"""Render public, independently written source notes for a lecture."""
from html import escape
import json
import re
from urllib.parse import parse_qs, urldefrag, urlsplit

KINDS = {'lecture-slides': '강의 슬라이드', 'official-chapter': '공식 영상 구간',
         'primary-paper': '원논문', 'course-schedule': '공식 강의 일정',
         'course-page': '공식 과목 자료', 'official-docs': '공식 기술 문서',
         'official-code': '공개 참고 코드'}

def e(value):
    return escape(str(value), quote=True)


def safe_url(value):
    if not isinstance(value, str) or not value.strip() or any(ord(c) < 32 for c in value):
        return False
    try:
        p = urlsplit(value)
        return p.scheme == 'https' and bool(p.hostname) and p.username is None and p.password is None
    except ValueError:
        return False


def read_editorial(base, known_video_ids):
    """Load vetted educational commentary, rejecting accidental bad ids or links."""
    path = base / 'editorial-guides.json'
    if not path.exists():
        return {}
    raw = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(raw, dict) or set(raw) - set(known_video_ids):
        raise ValueError('Editorial guides require official video IDs')
    for vid, guide in raw.items():
        if not isinstance(guide, dict) or not _nonempty(guide.get('why')):
            raise ValueError(f'Missing editorial reason for {vid}')
        what = guide.get('what')
        if not isinstance(what, list) or not what or not all(_nonempty(x) for x in what):
            raise ValueError(f'Missing editorial explanation for {vid}')
        evidence = guide.get('evidence')
        if not isinstance(evidence, list) or not evidence:
            raise ValueError(f'Missing editorial evidence for {vid}')
        for row in evidence:
            if (not isinstance(row, dict) or not all(_nonempty(row.get(k)) for k in ('kind','title','body'))
                or not safe_url(row.get('url'))):
                raise ValueError(f'Invalid evidence citation for {vid}')
    return raw


def _nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def _source_link(label, url):
    return f'<a href="{e(url)}" target="_blank" rel="noopener noreferrer">{e(label)} ↗</a>'


def bounded_link(row, vid, starts):
    if row['kind'] != 'official-chapter' or not re.fullmatch(r'[A-Za-z0-9_-]{11}', vid):
        return ''
    url = urlsplit(row['url'])
    query = parse_qs(url.query)
    t = query.get('t', [''])[0]
    if url.hostname != 'www.youtube.com' or url.path != '/watch' or query.get('v') != [vid]:
        return ''
    if not re.fullmatch(r'\d{1,8}s?', t) or int(t.rstrip('s')) not in starts:
        return ''
    return f' <a class="editorial-clip" href="#video-{e(vid)}-clip-{int(t.rstrip("s"))}">학습실에서 구간 보기</a>'


def fallback_evidence(note, brief):
    entries = []
    for rows, kind, description in (
        (note.get('evidence', ()), '강의 근거', '이 강의 노트를 작성할 때 참고한 자료입니다.'),
        (note.get('references', ()), '심화 자료', '노트에서 다룬 개념을 더 자세히 볼 때 참고하세요.'),
        (brief.get('sources', ()), '브리핑 출처', '강의 브리핑의 범위를 확인하는 데 사용한 자료입니다.'),
    ):
        for row in rows:
            if safe_url(row.get('url')):
                entries.append(dict(kind=kind,title=row.get('label','자료'),url=row['url'],body=description))
    used = set()
    distinct = []
    for row in entries:
        ref=urldefrag(row['url']).url
        if ref not in used:
            distinct.append(row)
            used.add(ref)
    return distinct


def render_editorial(video, record, note=None, brief=None, guide=None):
    """Unhidden selected-video overview/evidence; original text, never a transcript."""
    note, brief, guide = note or {}, brief or {}, guide or {}
    vid = video['id']
    why = guide.get('why')
    if not why and note:
        why = note.get('highlights', [{}])[0].get('text') if note.get('highlights') else None
    what = guide.get('what', [note['summary']] if note.get('summary') else [])
    basis = guide.get('basis') or note.get('basis') or brief.get('basis')
    evidence = guide.get('evidence') or fallback_evidence(note, brief)
    starts = {item['start'] for item in brief.get('clips', ())}
    lead = f'<h3>이 강의를 볼 이유</h3><p>{e(why)}</p>' if why else ''
    scope = (f'<h3>무엇을 다루나요?</h3>{"".join(f"<p>{e(p)}</p>" for p in what)}'
             if what else '<h3>공식 강의 소개</h3><p>이 영상의 개별 해설은 아직 확인되지 않았습니다.</p>')
    basis_text = f'<p class="editorial-basis">{e(basis)}</p>' if basis else ''
    cards = ''.join(
        f'<article class="editorial-source"><p class="editorial-citation"><strong>{e(KINDS.get(row["kind"], row["kind"]))}</strong>'
        f'{_source_link(row["title"],row["url"])}{bounded_link(row,vid,starts)}</p><p>{e(row["body"])}</p></article>'
        for row in evidence)
    if not cards:
        fallback = record.get('youtube_url') or f'https://www.youtube.com/watch?v={vid}'
        if safe_url(fallback):
            cards = ('<article class="editorial-source"><p class="editorial-citation"><strong>공식 영상</strong>'
                     f'{_source_link("CMU YouTube 원본",fallback)}</p><p>영상 설명과 제공되는 자막을 확인할 수 있습니다.</p></article>')
    return (f'<div class="video-editorial" data-video-editorial="{e(vid)}">'
            f'<section class="editorial-overview" aria-label="강의 개요">{lead}{scope}{basis_text}</section>'
            f'<section class="editorial-evidence" aria-label="이 강의를 뒷받침하는 자료">'
            f'<h3>근거 자료</h3>{cards}</section></div>')
