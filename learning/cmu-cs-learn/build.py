"""Build the dependency-free CMU CS Learn study guide from catalog.json."""
import argparse
from html import escape
import json
import re
from pathlib import Path
import shutil
from urllib.parse import urlsplit

BASE = Path(__file__).resolve().parent


def e(value):
    return escape(str(value), quote=True)


def link(label, url, klass=''):
    return f'<a class="{e(klass)}" href="{e(url)}">{e(label)} <span aria-hidden="true">↗</span></a>'


def route_html(route, by_id):
    parts = ''.join(
        f'<li><a href="#course-{e(i)}" data-route-course>'
        f'<span>{e(i)}</span> {e(by_id[i]["ko"])}'
        f'{" <small>예정</small>" if by_id[i]["status"] == "planned" else ""}</a></li>'
        for i in route['steps']
    )
    return (f'<article class="route"><p class="eyebrow">{e(route["label"])}</p>'
            f'<h3>{e(route["title"])}</h3><p>{e(route["description"])}</p>'
            f'<ol>{parts}</ol><p class="route-goal"><strong>남길 결과물</strong> {e(route["goal"])}</p></article>')


def step_html(c, key, number, label, content):
    sid = f'step-{e(c["id"])}-{key}'
    return (f'<section id="{sid}" class="step" tabindex="-1" aria-labelledby="{sid}-title">'
            f'<div class="step-head"><span class="step-number" aria-hidden="true">{number:02}</span>'
            f'<h4 id="{sid}-title">{label}</h4><button class="mark requires-js" type="button" '
            f'data-step-key="{key}" aria-label="{label} 완료 여부" aria-pressed="false">완료 표시</button></div>'
            f'<div class="step-body">{content}</div></section>')



def read_lessons():
    videos = json.loads((BASE / 'video-index.json').read_text(encoding='utf-8'))
    valid = {(course, row['id']) for course, rows in videos.items() for row in rows}
    notes = {}
    for path in sorted((BASE / 'lesson-notes').glob('*.json')):
        for row in json.loads(path.read_text(encoding='utf-8')):
            key = row['course'], row['video']
            if key not in valid or key in notes or not row['summary'].strip() or not row['basis'].strip():
                raise ValueError(f'Invalid or duplicate lesson note: {path.name}, {key}')
            for item in row['evidence'] + row['references']:
                if urlsplit(item['url']).scheme != 'https' or not urlsplit(item['url']).hostname:
                    raise ValueError(f'Invalid lesson source: {path.name}, {item["url"]}')
            for point in row['highlights']:
                if 'at' in point and (type(point['at']) is not int or point['at'] < 0):
                    raise ValueError(f'Invalid lesson timestamp: {path.name}, {key}')
            notes[key] = row
    return videos, notes


def video_note(c, video, index, note):
    vid, title = video['id'], video['title'].split(' | ', 1)[-1]
    name = f'lesson-{e(vid)}'
    label = f'<h5 id="{name}">{e(title)}</h5>'
    if note:
        highlights = []
        for point in note['highlights']:
            time = ''
            if 'at' in point:
                at = point['at']
                time = (f'<button class="timestamp requires-js" data-timestamp="{at}" type="button" '
                        f'aria-label="{at // 60}분 {at % 60}초에서 재생">{at // 60}:{at % 60:02d}</button> ')
            highlights.append(f'<li>{time}{e(point["text"])}</li>')
        def source_block(label, rows):
            if not rows:
                return ''
            links = ''.join(f'<li>{link(r["label"], r["url"])}</li>' for r in rows)
            return f'<div><h6>{label}</h6><ul>{links}</ul></div>'
        body = (f'<p class="note-basis">{e(note["basis"])}</p><h6>요약</h6><p>{e(note["summary"])}</p>'
                f'<h6>핵심 포인트</h6><ul>{"".join(highlights)}</ul>'
                f'<div class="note-sources">{source_block("근거", note["evidence"])}{source_block("참고자료", note["references"])}</div>')
    else:
        body = '<p class="note-basis">출처 확인 대기</p><p>이 영상은 공식 공개 목록에 있지만 개별 요약은 아직 확인되지 않았습니다.</p>'
    fallback = link('YouTube 원본', f'https://www.youtube.com/watch?v={vid}')
    return f'<section class="video-note" data-video-notes="{e(vid)}" aria-labelledby="{name}">{label}{body}<p class="video-source">재생 문제 발생 시 {fallback}</p></section>'


def lesson_html(c, video_rows, notes):
    if not video_rows or any(not re.fullmatch(r'[A-Za-z0-9_-]{11}', row['id']) for row in video_rows):
        raise ValueError(f'Missing or invalid official videos: {c["id"]}')
    playlist = c['playlist']
    first = video_rows[0]
    options = ''.join(f'<option value="{e(v["id"])}" data-video-option="{e(v["id"])}" data-title="{e(v["title"].split(" | ", 1)[-1])}" data-availability="{e(v.get("availability", "unknown"))}" data-cc="{e(v.get("english_cc", "not-confirmed"))}">{i+1:02} · {e(v["title"].split(" | ", 1)[-1])}</option>' for i, v in enumerate(video_rows))
    covered = sum((c['id'], v['id']) in notes for v in video_rows)
    articles = ''.join(video_note(c, row, i, notes.get((c['id'], row['id']))) for i, row in enumerate(video_rows))
    cid = e(c['id'])
    note_summary = f'학습 노트 {covered}/{len(video_rows)}편'
    return f"""
      <div class="lesson-control requires-js"><label for="videos-{cid}">강의 영상 선택</label>
      <select id="videos-{cid}" data-video-select>{options}</select></div>
      <div class="lesson-layout">
        <div>
          <div class="player" data-player>
            <div class="player-placeholder"><p class="player-title" data-video-title>{e(first['title'].split(' | ', 1)[-1])}</p>
            <p>버튼을 누를 때만 YouTube 플레이어에 연결합니다.</p>
            <button class="play requires-js" type="button" data-play="{e(playlist)}"><span aria-hidden="true">▶</span> 영상 열기</button></div>
          </div>
          <p class="caption-help"><strong data-cc-status></strong> 자막이 있는 영상은 기본으로 영어 자막을 요청합니다. 플레이어의 CC 버튼과 설정에서 끄거나 언어를 선택하세요. 자막 언어와 제공 여부는 영상마다 다릅니다.</p>
          <p class="play-fallback">{link('CMU 공식 재생목록', f'https://www.youtube.com/playlist?list={playlist}')} · 영상 시청 후 직접 완료를 표시하세요.</p>
        </div>
        <div class="lesson-notes">
          <p class="eyebrow">VIDEO NOTES · {note_summary}</p>
          {articles}
        </div>
      </div>"""


def workspace_html(c, official, videos, notes):
    fallback = ''.join(f'<li>{link(r["label"], r["url"])}</li>' for r in c['resources'])
    resources = f'<details class="sources"><summary>출처 및 보충 자료</summary><ul>{fallback}<li>{link("CMU 공식 CS Learn", official)}</li></ul></details>'
    prep = f'<p class="prepare"><strong>이 과목을 보기 전에</strong> {e(c["prepare"])}</p>'
    if c['status'] == 'planned':
        return f'{prep}<p class="not-yet">CS Learn에서 공개되면 강의와 학습 체크리스트를 이용할 수 있습니다.</p>{resources}'
    playlist = c.get('playlist', '')
    if not re.fullmatch(r'PL[A-Za-z0-9_-]{8,60}', playlist):
        raise ValueError(f'Invalid official playlist: {c["id"]}')
    watch = lesson_html(c, videos.get(c['id'], []), notes)
    practice = f'<p>{e(c["practice"])}</p>'
    reflect = f"""
      <p>배운 개념 1개, 아직 설명하기 어려운 질문 1개, 다음에 해볼 실험 1개를 적어보세요.</p>
      <label class="note requires-js" for="note-{e(c["id"])}">나의 복습 노트</label>
      <textarea class="requires-js" id="note-{e(c["id"])}" maxlength="2000" rows="3" placeholder="배운 점 · 질문 · 다음 실험"></textarea>"""
    return prep + step_html(c, 'watch', 1, '공식 강의 보기', watch) + step_html(c, 'practice', 2, '미니 실습', practice) + step_html(c, 'reflect', 3, '복습 노트', reflect) + resources


def course_html(c, track, official, videos, notes):
    key = ' '.join([c['id'], c['id'].replace('-', ''), c['title'], c['ko'], c['faculty'], c['level'],
                    track, c['summary'], c['prepare'], ' '.join(c['tags']), ' '.join(row['title'] for row in videos.get(c['id'], []))])
    status = 'YouTube 공개' if c['status'] == 'available' else '2027년 1월 예정'
    tags = ''.join(f'<li>{e(t)}</li>' for t in c['tags'])
    cid = f'course-{e(c["id"])}'
    progress = '<span class="row-progress requires-js" data-course-progress>0/3 단계</span>' if c['status'] == 'available' else ''
    start = '학습 열기' if c['status'] == 'available' else '과목 미리보기'
    contents = workspace_html(c, official, videos, notes)
    return f"""
    <article id="{cid}" class="course" tabindex="-1" aria-labelledby="{cid}-title"
      data-course data-id="{e(c['id'])}" data-title="{e(c['ko'])}" data-track="{e(c['track'])}" data-status="{e(c['status'])}" data-keywords="{e(key)}">
      <details class="workspace" data-workspace>
        <summary class="course-row">
          <div class="row-code"><span class="course-id">{e(c['id'])}</span><span class="badge {e(c['status'])}">{status}</span></div>
          <div class="row-title"><h3 id="{cid}-title">{e(c['ko'])}</h3><p class="en" lang="en">{e(c['title'])}</p></div>
          <div class="row-cta">{progress}<span>{start} <span aria-hidden="true" class="chevron">⌄</span></span></div>
        </summary>
        <div class="workspace-body">
          <p class="byline">{e(c['faculty'])}</p><p class="summary">{e(c['summary'])}</p>
          <ul class="tags" aria-label="주제"><li class="level">{e(c['level'])}</li>{tags}</ul>
          {contents}
        </div>
      </details>
    </article>"""

def document(data, videos, notes):
    courses = data['courses']
    tracks = data['tracks']
    by_id = {c['id']: c for c in courses}
    routes = ''.join(route_html(r, by_id) for r in data['routes'])
    cards = ''.join(course_html(c, tracks[c['track']], data['source'], videos, notes) for c in courses)
    track_opts = ''.join(f'<option value="{e(k)}">{e(v)}</option>' for k, v in tracks.items())
    available = sum(c['status']=='available' for c in courses)
    planned = sum(c['status']=='planned' for c in courses)
    updated = e(data['checked'])
    featured = by_id[data['routes'][0]['steps'][0]]
    official = link('CMU 공식 강의 목록', data['source'], 'official')
    announcement = link('CMU 출시 공지', data['announcement'])
    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="카네기멜론 CS Learn 공개 강의를 찾아보고 AI 에이전트, ML 시스템, 소프트웨어 설계, 컴퓨팅 기초를 공부하는 한국어 길잡이.">
  <meta name="theme-color" content="#ffffff">
  <meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self'; style-src 'self'; frame-src https://www.youtube-nocookie.com; connect-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'">
  <title>CMU CS Learn · 한국어 독학 가이드</title>
  <link rel="canonical" href="https://yongkilee.com/learning/cmu-cs-learn/">
  <link rel="stylesheet" href="./style.css?v=2">
  <script defer src="./study.js?v=3"></script>
</head>
<body>
  <a class="skip" href="#library">과목 목록으로 건너뛰기</a>
  <header class="mast">
    <div class="shell topbar">
      <a href="./" class="brand" aria-label="CS Learn 독학 가이드 홈"><span class="brand-icon" aria-hidden="true">⌘</span> CS Learn <span class="brand-note">독학 가이드</span></a>
      <nav aria-label="페이지"><a href="#study-next">내 학습</a><a href="#library">과목 검색</a><a href="#paths">학습 경로</a></nav>
    </div>
    <div class="shell hero">
      <div class="hero-copy">
        <p class="eyebrow"><span class="signal"></span> Carnegie Mellon University · 비공식 학습 가이드</p>
        <h1>CMU 컴퓨터과학 <span>학습실</span></h1>
        <p>개별 강의 영상과 검증된 요약을 나란히 보고, 실습과 복습까지 이어가세요.</p>
      </div>
    </div>
  </header>
  <main class="shell">
    <section id="study-next" class="study-grid" aria-label="내 학습">
      <article class="next-sheet">
        <p class="eyebrow" id="next-label">추천 시작 과목</p>
        <h2 id="next-title">{e(featured['ko'])}</h2>
        <p id="next-step">{e(featured['id'])} · 다음: 공식 강의 보기</p>
        <a class="cta" id="next-cta" href="#course-{e(featured['id'])}">공부 시작하기 →</a>
      </article>
      <aside class="progress-sheet" aria-label="내 학습 진도">
        <p class="eyebrow">MY PROGRESS</p>
        <h2 id="study-progress">0 / {available*3}단계</h2>
        <progress id="study-meter" value="0" max="{available*3}" aria-label="완료한 독학 단계"></progress>
        <p id="study-count">완료한 공개 과목 0 / {available}</p>
        <p id="storage-note" hidden>현재 브라우저에서 저장할 수 없어 새로고침하면 진도가 초기화됩니다.</p>
        <p class="local-note">진도와 노트는 이 브라우저에만 남습니다.</p>
      </aside>
    </section>
    <section id="library" aria-labelledby="library-title">
      <div class="section-title"><p class="eyebrow">01 / CATALOG</p><h2 id="library-title">과목 라이브러리</h2><p>공개 {available}개 · 공개 예정 {planned}개. 검색하거나 과목을 열어 바로 공부하세요.</p></div>
      <form id="filters" class="requires-js" role="search" aria-label="과목 검색 및 필터">
        <label class="search">과목 검색<input type="search" name="q" placeholder="예: 11-768, 서빙, software" autocomplete="off"></label>
        <label>주제<select name="track"><option value="all">전체</option>{track_opts}</select></label>
        <label>공개 상태<select name="status"><option value="all">전체</option><option value="available">YouTube 공개</option><option value="planned">공개 예정</option></select></label>
        <label>학습 상태<select name="progress"><option value="all">전체</option><option value="started">학습 중</option><option value="open">미완료</option><option value="done">완료</option></select></label>
        <button class="clear" type="button" data-reset>초기화</button>
      </form>
      <p id="result-count" aria-live="polite">{len(courses)}개 과목</p>
      <p class="storage">세 단계 체크리스트는 독학용입니다. CMU 공식 커리큘럼이나 수료 기준이 아닙니다.</p>
      <noscript><p>이 환경에서는 검색, 내장 플레이어, 진도 저장이 꺼져 있습니다. 아래 과목을 펼쳐 강의 링크와 실습을 볼 수 있습니다.</p></noscript>
      <div class="empty" id="empty" hidden><h3>검색 결과가 없어요</h3><p>키워드를 줄이거나 필터를 초기화해 보세요.</p><button class="clear" type="button" data-reset>검색·필터 초기화</button></div>
      <div class="courses">{cards}</div>
    </section>
    <section id="paths" aria-labelledby="paths-title">
      <div class="section-title"><p class="eyebrow">02 / ROADMAP</p><h2 id="paths-title">목표별 학습 경로</h2><p>독학용 추천 순서이며 공식 선수과목이 아닙니다.</p></div>
      <div class="routes">{routes}</div>
    </section>
  </main>
  <footer><div class="shell footer-inner">
    <div><strong>CMU CS Learn · 한국어 독학 가이드</strong><p>CMU와 별개인 비공식 정리입니다. 소개·준비·실습은 독학용 제안이며 강의 영상·슬라이드·자막은 재배포하지 않습니다. CMU의 자가 학습 교재와 AI 튜터는 공식 안내상 별도 공개 예정입니다. 공식 목록 확인: <time datetime="{updated}">{updated}</time>.</p></div>
    <div class="foot-links">{official}{announcement}<a href="#library">과목 목록 ↑</a></div>
  </div></footer>
</body>
</html>
"""


def build(output):
    data = json.loads((BASE / 'catalog.json').read_text(encoding='utf-8'))
    videos, notes = read_lessons()
    html = document(data, videos, notes)
    output.mkdir(parents=True, exist_ok=True)
    (output / 'index.html').write_text(html, encoding='utf-8')
    for asset in ('study.js', 'style.css'):
        shutil.copyfile(BASE / 'assets' / asset, output / asset)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=BASE / 'dist')
    args = parser.parse_args()
    build(args.output)


if __name__ == '__main__':
    main()
