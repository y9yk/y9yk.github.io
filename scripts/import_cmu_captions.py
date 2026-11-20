#!/usr/bin/env python3
"""Import a single authorized caption track into private, external JSON."""
import argparse
from datetime import datetime, timezone
import hashlib
import html
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / 'learning' / 'cmu-cs-learn' / 'video-index.json'
MAX_BYTES = 8 * 1024 * 1024
TIMEOUT_S = 60
TIMECODE = r'(?:(?:\d{2,}):)?[0-5]\d:[0-5]\d[.,]\d{3}'
TIME_LINE = re.compile(rf'^({TIMECODE})[ \t]+-->[ \t]+({TIMECODE})(?:[ \t].*)?$')
INLINE = re.compile(rf'<({TIMECODE})>')
TAG = re.compile(r'<[^>\n]*>')
WORD = re.compile(r'\S+')
ACCESS_NOTICE = re.compile(
    r'not a bot|captcha|unusual traffic|sign[ -]in|login required|log in to'
    r'|too many requests|\b(?:403|429)\b|members.only|private video|age.restricted'
    r'|access denied|not available in your country', re.I,
)


def millis(value):
    hms, fractional = re.split(r'[.,]', value)
    seconds = 0
    for field in hms.split(':'):
        seconds = seconds * 60 + int(field)
    return seconds * 1000 + int(fractional)


def read_file(path):
    if not stat.S_ISREG(path.stat().st_mode):
        raise ValueError('caption input must be a regular file')
    with path.open('rb') as f:
        data = f.read(MAX_BYTES + 1)
    if not data or len(data) > MAX_BYTES:
        raise ValueError('caption input must contain between 1 byte and 8 MiB')
    return data


def words_with_time(text):
    words = []
    current = None
    for i, part in enumerate(INLINE.split(text)):
        if i % 2:
            current = millis(part)
        else:
            plain = html.unescape(TAG.sub('', part))
            words.extend((match.group(), current) for match in WORD.finditer(plain))
    return words


def carryover_size(prior, current):
    # Find the longest previous suffix that is a current prefix in linear
    # time. None cannot collide with a caption token.
    sequence = current + (None,) + prior[-len(current):]
    prefix = [0] * len(sequence)
    for i in range(1, len(sequence)):
        length = prefix[i - 1]
        while length and sequence[length] != sequence[i]:
            length = prefix[length - 1]
        prefix[i] = length + (sequence[length] == sequence[i])
    return prefix[-1]


def parse_cues(data, fmt, auto):
    text = data.decode('utf-8-sig').replace('\r\n', '\n').replace('\r', '\n')
    if fmt == 'vtt':
        header = text.split('\n', 1)[0]
        if not re.fullmatch(r'WEBVTT(?:[ \t].*)?', header):
            raise ValueError('invalid WEBVTT header')
    timed = []
    for block in re.split(r'\n[ \t]*\n', text.strip()):
        lines = block.strip().split('\n')
        if not lines or (fmt == 'vtt' and re.match(r'^(?:WEBVTT|NOTE|STYLE|REGION)(?:\s|$)', lines[0])):
            continue
        t = next((i for i, line in enumerate(lines[:2]) if '-->' in line), None)
        if t is None:
            raise ValueError('caption block without timestamp')
        match = TIME_LINE.fullmatch(lines[t].strip())
        if not match:
            raise ValueError('invalid cue timestamp')
        start, end = map(millis, match.groups())
        if start >= end:
            raise ValueError('cue timestamp end must follow start')
        words = words_with_time('\n'.join(lines[t+1:]))
        if words:
            timed.append((start, end, words))

    cues = []
    seen = set()
    previous = None
    for start, end, words in sorted(timed, key=lambda row: row[0]):
        tokens = tuple(word for word, _ in words)
        full = (start, end, tokens)
        if full in seen:
            continue
        seen.add(full)
        overlap = 0
        if auto and previous and start < previous[1]:
            # Only a shared suffix/prefix during overlap is treated as display
            # carryover. Non-overlapping repetitions remain separate cues.
            overlap = carryover_size(previous[0], tokens)
            if overlap == len(tokens):
                if cues and cues[-1]['text'] == ' '.join(tokens):
                    cues[-1]['end_ms'] = max(cues[-1]['end_ms'], end)
                previous = (tokens, max(previous[1], end))
                continue
        previous = (tokens, end)
        if overlap and cues and cues[-1]['start_ms'] < start < cues[-1]['end_ms']:
            # The next cue replaces the rolling window at its stated start.
            cues[-1]['end_ms'] = start
        text_start = words[overlap][1] if auto else None
        if text_start is not None and start <= text_start < end:
            start = text_start
        cues.append({'start_ms': start, 'end_ms': end, 'text': ' '.join(tokens[overlap:])})
    if not cues:
        raise ValueError('no usable caption cues found')
    return sorted(cues, key=lambda cue: cue['start_ms'])


def output_path(filename):
    path = Path(filename).expanduser()
    if os.path.lexists(path):
        raise ValueError('private output already exists')
    parent = path.parent.resolve(strict=True)
    if parent.is_relative_to(ROOT) or any((ancestor / '.git').is_file() or (ancestor / '.git' / 'HEAD').is_file()
                                               for ancestor in (parent, *parent.parents)):
        raise ValueError('private output must be outside this and any Git checkout')
    if not parent.is_dir() or path.suffix.lower() != '.json':
        raise ValueError('private output needs an existing external directory and a .json extension')
    return parent / path.name


def fetch_captions(video_id, url, language, track, output_dir):
    executable = shutil.which('yt-dlp')
    if not executable:
        raise ValueError('yt-dlp is not installed; install from its official source or supply --input')
    with TemporaryDirectory(prefix='cmu-captions-', dir=output_dir) as temporary:
        trusted = [executable, '--ignore-config', '--no-plugin-dirs']
        version = subprocess.run([*trusted, '--version'], cwd=temporary, capture_output=True,
                                 text=True, timeout=5, errors='replace', check=False)
        if version.returncode or not version.stdout.strip():
            raise ValueError('yt-dlp version check failed')
        option = '--write-auto-subs' if track == 'auto' else '--write-subs'
        command = [*trusted, '--no-cache-dir', '--skip-download', '--no-playlist',
                   '--no-remote-components', '--socket-timeout', '12',
                   '--retries', '0', '--fragment-retries', '0', '--extractor-retries', '0',
                   option, '--sub-langs', language, '--sub-format', 'vtt', '--output',
                   '%(id)s.%(ext)s', '--', url]
        proc = subprocess.run(command, cwd=temporary, capture_output=True, text=True,
                              timeout=TIMEOUT_S, errors='replace', check=False)
        if ACCESS_NOTICE.search(proc.stderr + '\n' + proc.stdout):
            raise ValueError('provider access or bot challenge; stopped without retry or bypass')
        if proc.returncode:
            raise ValueError('yt-dlp could not retrieve public captions in normal mode')
        result = Path(temporary) / f'{video_id}.{language}.vtt'
        if not result.is_file():
            raise ValueError('requested public caption language or track is unavailable')
        return read_file(result), version.stdout.strip().splitlines()[0]


def import_track(args):
    index = json.loads(INDEX.read_text(encoding='utf-8'))
    known = {row['id'] for rows in index.values() for row in rows}
    if not re.fullmatch(r'[A-Za-z0-9_-]{11}', args.video_id) or args.video_id not in known:
        raise ValueError('use a registered CMU video ID, not a URL or playlist')
    if not re.fullmatch(r'[a-zA-Z]{2,3}(?:-[A-Za-z0-9]{2,8})*', args.language):
        raise ValueError('supply one exact language code, for example en or en-US')
    out = output_path(args.output)
    track = args.track
    url = f'https://www.youtube.com/watch?v={args.video_id}'
    if args.fetch:
        track = track or 'manual'
        data, version = fetch_captions(args.video_id, url, args.language, track, out.parent)
        fmt = 'vtt'
        provenance = {'method': 'youtube-public-yt-dlp', 'tool_version': version,
                      'attribution': 'public track selected by exact video ID, language, and track type'}
    else:
        track = track or 'unknown'
        path = Path(args.input).expanduser()
        fmt = path.suffix.lower().lstrip('.')
        if fmt not in {'srt', 'vtt'}:
            raise ValueError('local input must be a UTF-8 .srt or .vtt file')
        data = read_file(path)
        provenance = {'method': 'authorized-local',
                      'attribution': 'video ID, language, and track type supplied by the editor'}
    cues = parse_cues(data, fmt, track == 'auto')
    result = {
        'schema_version': 1, 'video_id': args.video_id, 'language': args.language, 'track': track,
        'provenance': {**provenance, 'video_url': url, 'input_format': fmt,
                       'input_sha256': hashlib.sha256(data).hexdigest(),
                       'imported_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
                       'normalization': 'cue start/end and publisher inline timestamps; rolling carryover removed only for auto' },
        'cues': cues,
    }
    payload = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
    # No overwrite and no following a destination symlink even after validation.
    fd = os.open(out, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w', encoding='utf-8') as file:
        file.write(payload)
    return len(cues)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--video-id', required=True)
    parser.add_argument('--language', required=True)
    parser.add_argument('--track', choices=('manual', 'auto'))
    parser.add_argument('--output', required=True, help='new private JSON file outside every checkout')
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--input', help='authorized local UTF-8 .srt or .vtt')
    mode.add_argument('--fetch', action='store_true', help='opt into normal public-caption retrieval')
    try:
        count = import_track(parser.parse_args())
    except subprocess.TimeoutExpired:
        parser.exit(1, 'Caption import stopped: yt-dlp timed out without retry.\n')
    except (OSError, ValueError) as error:
        parser.exit(1, f'Caption import stopped: {error}\n')
    print(f'Imported {count} timestamped cues to private JSON.')


if __name__ == '__main__':
    main()
