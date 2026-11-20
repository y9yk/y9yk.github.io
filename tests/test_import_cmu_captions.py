"""Black-box checks using synthetic captions and a local downloader stand-in."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "import_cmu_captions.py"
VIDEO = "KQUtNJEzUxU"
ROLLING = """WEBVTT

00:00:01.000 --> 00:00:03.000 align:start
<c>we make keys</c>

00:00:02.000 --> 00:00:04.000
we make keys
<00:00:02.100><c>and aggregate</c>

00:00:03.100 --> 00:00:05.000
and aggregate

00:00:08.000 --> 00:00:09.000
and aggregate
"""


class CaptionImportTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.directory = Path(self.tmp.name)
        self.input = self.directory / "source.vtt"
        self.input.write_text(ROLLING, encoding="utf-8")
        self.output = self.directory / "private.json"

    def invoke(self, *args, env=None, output=None, video=VIDEO):
        return subprocess.run([sys.executable, str(SCRIPT), "--video-id", video,
                               "--language", "en", "--output", str(output or self.output), *args],
                              cwd=ROOT, text=True, capture_output=True, env=env, check=False)

    def test_vtt_removes_temporally_adjacent_rollover_not_later_repetition(self):
        result = self.invoke("--input", str(self.input), "--track", "auto")
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(self.output.read_text())
        self.assertEqual(data["cues"], [
            {"start_ms": 1000, "end_ms": 2000, "text": "we make keys"},
            {"start_ms": 2100, "end_ms": 5000, "text": "and aggregate"},
            {"start_ms": 8000, "end_ms": 9000, "text": "and aggregate"},
        ])
        self.assertEqual(data["video_id"], VIDEO)
        self.assertEqual(data["provenance"]["method"], "authorized-local")
        self.assertEqual(len(data["provenance"]["input_sha256"]), 64)
        self.assertNotIn(str(self.input), self.output.read_text())
        self.assertEqual(self.output.stat().st_mode & 0o777, 0o600)

    def test_srt_preserves_repeated_manual_words_without_overlap_heuristic(self):
        srt = self.directory / "source.srt"
        srt.write_text("1\n00:00:01,000 --> 00:00:03,000\n<i>one two</i>\n\n"
                       "2\n00:00:02,000 --> 00:00:04,000\ntwo &amp; three\n", encoding="utf-8")
        result = self.invoke("--input", str(srt), "--track", "manual")
        self.assertEqual(result.returncode, 0, result.stderr)
        rows = json.loads(self.output.read_text())["cues"]
        self.assertEqual([row["text"] for row in rows], ["one two", "two & three"])

    def test_refuses_output_inside_checkout_before_fetch(self):
        output = ROOT / "dist" / "unsafe-private-test.json"
        result = self.invoke("--input", str(self.input), output=output)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("outside", result.stderr)
        self.assertFalse(output.exists())

    def test_refuses_existing_output_even_if_symlink(self):
        self.output.symlink_to(self.input)
        result = self.invoke("--input", str(self.input))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("already exists", result.stderr)
        self.assertEqual(self.input.read_text(), ROLLING)

    def test_requires_known_video_id_and_rejects_url(self):
        for value in ("AABCDEFGHI", "https://youtu.be/" + VIDEO):
            result = self.invoke("--input", str(self.input), video=value)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("registered CMU video ID", result.stderr)

    def test_malformed_timestamp_is_an_error_not_partial_output(self):
        self.input.write_text("WEBVTT\n\n00:00:02.000 --> 00:00:01.000\nbackwards\n", encoding="utf-8")
        result = self.invoke("--input", str(self.input))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("timestamp", result.stderr)
        self.assertFalse(self.output.exists())

    def downloader(self, body):
        shim = self.directory / "yt-dlp"
        shim.write_text(f"#!{sys.executable}\n" + body, encoding="utf-8")
        shim.chmod(0o700)
        return {**os.environ, "PATH": str(self.directory) + os.pathsep + os.environ["PATH"]}

    def test_fetch_invokes_only_direct_subtitle_options_and_imports_exact_language(self):
        env = self.downloader("""
import pathlib, sys
argv = sys.argv[1:]
if '--version' in argv:
    print('test-double-1')
    raise SystemExit(0)
assert argv[-1] == 'https://www.youtube.com/watch?v=KQUtNJEzUxU', argv
assert argv[argv.index('--sub-langs') + 1] == 'en', argv
for option in ('--skip-download', '--no-playlist', '--write-subs', '--ignore-config', '--no-plugin-dirs'):
    assert option in argv, argv
assert '--write-auto-subs' not in argv, argv
pathlib.Path('KQUtNJEzUxU.en.vtt').write_text('WEBVTT\\n\\n00:01.000 --> 00:02.000\\nsynthetic\\n')
""")
        result = self.invoke("--fetch", env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(self.output.read_text())
        self.assertEqual(data["provenance"]["tool_version"], "test-double-1")
        self.assertEqual(data["provenance"]["method"], "youtube-public-yt-dlp")

    def test_bot_challenge_stops_without_output_even_if_caption_temp_exists(self):
        env = self.downloader("""
import pathlib, sys
if '--version' in sys.argv:
    print('test-double-1')
    raise SystemExit(0)
pathlib.Path('KQUtNJEzUxU.en.vtt').write_text('WEBVTT\\n\\n00:01.000 --> 00:02.000\\nsynthetic\\n')
print('Sign in to confirm you are not a bot', file=sys.stderr)
""")
        result = self.invoke("--fetch", env=env)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("challenge", result.stderr)
        self.assertFalse(self.output.exists())

    def test_rolling_duplicate_does_not_extend_a_discontiguous_suffix(self):
        self.input.write_text(
            "WEBVTT\n\n00:01.000 --> 00:04.000\nwe can aggregate\n\n"
            "00:03.000 --> 00:06.000\naggregate\n", encoding="utf-8")
        result = self.invoke("--input", str(self.input), "--track", "auto")
        self.assertEqual(result.returncode, 0, result.stderr)
        # The rolling cue holds only the suffix; it does not keep the whole
        # preceding line active through 6s.
        self.assertEqual(json.loads(self.output.read_text())["cues"], [
            {"start_ms": 1000, "end_ms": 4000, "text": "we can aggregate"},
        ])

    def test_adjacent_same_sentence_without_rolling_hint_is_preserved(self):
        self.input.write_text(
            "WEBVTT\n\n00:01.000 --> 00:02.000\nrepeat now\n\n"
            "00:02.000 --> 00:03.000\nrepeat now\n", encoding="utf-8")
        result = self.invoke("--input", str(self.input), "--track", "auto")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(json.loads(self.output.read_text())["cues"]), 2)
