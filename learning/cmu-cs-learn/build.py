"""Build the dependency-free CMU CS Learn study guide from catalog.json."""
import argparse
from html import escape
import json
import re
from pathlib import Path
import shutil
from urllib.parse import urlsplit

from feed_model import build_feed_model
from detail_editorial import read_editorial, render_editorial

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
            f'<ol>{parts}</ol></article>')


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




def validate_clip(clip, duration_s):
    start, end = clip.get('start'), clip.get('end')
    if type(start) is not int or type(end) is not int or type(duration_s) is not int or not 0 <= start < end <= duration_s:
        raise ValueError(f'Clip needs verified start/end within published duration: {start!r}–{end!r}')
    evidence = clip.get('evidence', {})
    source = urlsplit(evidence.get('url', ''))
    if source.scheme != 'https' or not source.hostname or not evidence.get('label', '').strip():
        raise ValueError('Clip needs a verifiable HTTPS source and label')
    if reading := clip.get('reading'):
        reading_url = urlsplit(reading.get('url',''))
        if reading_url.scheme != 'https' or not reading_url.hostname or not reading.get('label','').strip():
            raise ValueError('Clip reading needs a valid HTTPS link and label')
    if not clip.get('title', '').strip() or not clip.get('context', '').strip():
        raise ValueError('Clip needs a title and contextual explanation')


def read_briefings(videos):
    known = {(course, row['id']): row for course, rows in videos.items() for row in rows}
    briefs = {}
    for path in sorted((BASE / 'lesson-briefings').glob('*.json')):
        for row in json.loads(path.read_text(encoding='utf-8')):
            key = row['course'], row['video']
            if key not in known or key in briefs or not row['briefing'].strip():
                raise ValueError(f'Invalid or duplicate briefing: {path.name}, {key}')
            for clip in row.get('clips', []):
                validate_clip(clip, known[key].get('duration_s'))
            briefs[key] = row
    return briefs


def timecode(seconds):
    hours, remainder = divmod(seconds, 3600)
    minutes, second = divmod(remainder, 60)
    return f'{hours}:{minutes:02}:{second:02}' if hours else f'{minutes}:{second:02}'


def clip_keywords(segment):
    return ' '.join([segment['title'], segment['context'], *segment.get('keywords', [])])


def briefing_html(c, video, note, brief, lesson_number, *, clips_only=False):
    vid = e(video['id'])
    basis = (brief or {}).get('basis') or ('출처가 확인된 기존 노트 요약' if note else '공식 영상 목록')
    text = brief['briefing'] if brief else note['summary'] if note else '공식 과목 소개 영상입니다. 아직 별도 기술 요약은 없습니다.'
    core_highlights = {point.get('at') for point in (note or {}).get('highlights', [])}
    segments = (brief or {}).get('clips', [])
    priority = [item for item in segments if item['start'] in core_highlights]
    primary = (priority + [item for item in segments if item not in priority])[:3]
    core_ranges = {(item['start'],item['end']) for item in primary}
    def clip_row(segment):
        start, end = segment['start'], segment['end']
        evidence = segment['evidence']
        title = e(segment['title'])
        label = f'{timecode(start)}–{timecode(end)}'
        reading = segment.get('reading')
        reading_link = f'<p>{link("함께 읽기: "+reading["label"], reading["url"], "clip-reading")}</p>' if reading else ''
        return (f'<li id="video-{vid}-clip-{start}"><button type="button" class="clip-button requires-js" data-clip-start="{start}" data-clip-end="{end}" '
                f'data-clip-title="{title}" data-clip-keywords="{e(clip_keywords(segment))}" data-clip-label="{label}" aria-pressed="false" '
                f'aria-label="{title} · {timecode(start)}에서 {timecode(end)}까지 재생">'
                f'<span aria-hidden="true">▶</span> {label}</button>'
                f'<div><strong>{title}</strong><p>{e(segment["context"])}</p>'
                f'{link(evidence["label"], evidence["url"], "clip-evidence")}{reading_link}</div></li>')
    if segments:
        core_rows = ''.join(clip_row(item) for item in segments if (item['start'],item['end']) in core_ranges)
        rest = [item for item in segments if (item['start'],item['end']) not in core_ranges]
        extras_list = (f'<details class="more-clips"><summary>나머지 구간 {len(rest)}개 보기</summary>'
                       f'<ul class="clip-list">{"".join(clip_row(item) for item in rest)}</ul></details>' if rest else '')
        clip_section = f'<h4>핵심 구간만 보기 <small>총 {len(segments)}개</small></h4><p class="clip-method">시작과 끝은 공식 게시자의 챕터 또는 영상 길이 기준입니다. 발화나 자막을 직접 검증한 구간은 아닙니다.</p><ul class="clip-list">{core_rows}</ul>{extras_list}'
    else:
        clip_section = '<p class="brief-empty">시작·종료가 확인된 학습 구간은 아직 없습니다. 전체 영상은 아래에서 열 수 있습니다.</p>'
    concepts = ''.join(f'<dt>{e(x["term"])}</dt><dd>{e(x["explanation"])}</dd>' for x in (brief or {}).get('concepts', []))
    extras = f'<details class="brief-extra"><summary>핵심 개념과 예시</summary><dl>{concepts}</dl></details>' if concepts else ''
    if clips_only:
        return f'<section class="quick-brief" data-video-brief="{vid}" aria-label="검증 구간 {lesson_number}">{clip_section}</section>'
    return (f'<section class="quick-brief" data-video-overview="{vid}" data-summary-fallback="{str(not brief and bool(note)).lower()}" aria-label="학습 브리핑 {lesson_number}">'
            f'<h3>학습 브리핑</h3><p class="brief-basis">{e(basis)}</p><p class="brief-text">{e(text)}</p>{extras}</section>')


def video_title(v):
    return v['title'].split(' | ', 1)[-1]


def duration(v):
    if v.get('availability') == 'premiere':
        return '공개 확인'
    seconds = v.get('duration_s')
    if type(seconds) is not int or seconds <= 0:
        return ''
    return timecode(seconds)


def thumbnail(v, c, eager=False, record=None):
    vid = v['id']
    if not re.fullmatch(r'[A-Za-z0-9_-]{11}', vid):
        raise ValueError(f'Invalid official video: {vid}')
    poster=(record or {}).get('poster_url') or f'https://i.ytimg.com/vi/{vid}/mqdefault.jpg'
    img = (f'<img src="{e(poster)}" alt="" width="320" height="180" '
           f'loading="{"eager" if eager else "lazy"}" decoding="async" referrerpolicy="no-referrer">'
           if v.get('thumbnail') else '')
    badge = f'<span class="time-badge">{duration(v)}</span>' if duration(v) else ''
    return f'<span class="video-thumb"><span class="thumb-fallback" aria-hidden="true">{e(c["id"])}</span>{img}{badge}</span>'


def quick_action(kind, symbol, label, vid=''):
    return (f'<button type="button" class="requires-js" data-video-action="{kind}" data-action-video="{e(vid)}" '
            f'aria-pressed="false" aria-label="{label}" title="{label}"><span aria-hidden="true">{symbol}</span></button>')


def video_card(c, v, note, brief, record, eager=False):
    vid = e(v['id'])
    context = record.get('reason') or (note['summary'] if note else '공식 과목 소개 영상')
    metrics = record['signals']
    signals = []
    if metrics['clips']:
        signals.append(f'공식 확인 구간 {metrics["clips"]}개')
    if metrics['sources']:
        signals.append(f'출처 {metrics["sources"]}개')
    if not signals and metrics["notes"]:
        signals.append("한국어 노트")
    summary_line = " · ".join([*signals, context])
    metadata = brief or {}
    concepts = [' '.join((x['term'], x['explanation'])) for x in metadata.get('concepts', [])]
    clips = [clip_keywords(x) for x in metadata.get('clips', [])]
    searchable = ' '.join([video_title(v), c['title'], c['ko'], c['faculty'], *c['tags'], *record['tags'], context,
                           metadata.get('briefing', ''), *concepts, *clips])
    return f"""<article class="feed-card" data-feed-video="{vid}" data-feed-course="{e(c['id'])}" data-feed-keywords="{e(searchable)}" data-preview-frames="{e(" ".join(record.get("preview_thumbnails", [])))}">
      <a class="video-card-link" href="#video-{vid}">
        {thumbnail(v, c, eager, record)}
        <h3>{e(video_title(v))}</h3>
      </a>
      <div class="feed-actions">{quick_action("save","◷","나중에 보기",vid)}{quick_action("watched","✓","시청 완료",vid)}</div>
      <p class="feed-meta">{e(c['faculty'])} · {e(c['id'])}</p>
      <p class="feed-context">{e(summary_line)}</p>
      <p class="recommend-reason" hidden></p>
    </article>"""


def discovery_pills(rows, facet):
    return ''.join(
        f'<button type="button" data-discovery-kind="{e(facet)}" data-discovery-key="{e(key)}" '
        f'data-discovery-label="{e(row["label"])}" data-discovery-ids="{e(" ".join(row["video_ids"]))}" aria-pressed="false">'
        f'{e(row["label"])} <span>{len(row["video_ids"])}</span></button>'
        for key,row in rows.items() if row['video_ids'])


def feed_html(courses, videos, notes, briefs, model):
    by_id = {c['id']:c for c in courses}
    lookup = {v['id']:(by_id[cid],v) for cid,rows in videos.items() for v in rows}
    records = model['videos']
    ordered = model['feed_ids']
    shelves = model.get('shelves', {})
    leads = shelves.get('featured',{}).get('video_ids',ordered[:8])[:8]
    fresh = shelves.get('fresh', {})
    fresh_ids = [vid for vid in fresh.get('video_ids',[]) if vid not in leads][:8]
    rest = [vid for vid in ordered if vid not in leads and vid not in fresh_ids]
    fresh_label = fresh.get('label', '새 공개 강의')
    fresh_basis = fresh.get('basis', '') + ' · 위 추천에 없는 영상'
    def cards(ids, eager=False):
        rows = []
        for i,vid in enumerate(ids):
            c,v=lookup[vid]
            key=(c['id'],vid)
            rows.append(video_card(c,v,notes.get(key),briefs.get(key),records[vid],eager and i<4))
        return ''.join(rows)
    course_links=''.join(f'<a href="#course-{e(c["id"])}"><small>{e(c["id"])}</small><strong>{e(c["ko"])}</strong><span>{len(videos[c["id"]])}개 강의</span></a>'
                         for c in courses if videos.get(c['id']))
    topic_chips=discovery_pills(model['topics'],'topic')
    source_pills=discovery_pills(model.get('source_types',{}),'source')
    tag_pills=discovery_pills(dict(list(model.get('tag_facets',{}).items())[:20]),'tag')
    return f"""<div class="feed-shelf leading-shelf" data-feed-shelf aria-labelledby="featured-title">
       <h2 class="visually-hidden" id="featured-title">추천 강의</h2>
       <div class="video-grid">{cards(leads,True)}</div>
     </div>
     <section class="discovery-section recommendation-box requires-js" id="for-you" aria-labelledby="for-you-title">
       <h2 id="for-you-title">나에게 맞는 강의 찾기</h2>
       <form id="recommend-form">
         <label class="visually-hidden" for="recommend-query">관심사 또는 CMU YouTube 링크</label>
         <input id="recommend-query" type="text" placeholder="예: 파이썬 입문, 분산 처리, 또는 CMU YouTube 링크" maxlength="500" required autocomplete="off" aria-describedby="recommend-help">
         <button type="submit">추천 보기</button>
       </form>
       <p id="recommend-help">관심사를 한국어·영어로 적거나 목록에 있는 CMU YouTube 링크를 넣어보세요. 입력은 브라우저에서만 처리합니다.</p>
     </section>
     <section class="discovery-section requires-js" id="topics" aria-labelledby="topic-title">
       <h2 id="topic-title">관심 주제로 고르기</h2>
       <div class="discovery-pills" aria-label="관심 주제">{topic_chips}</div>
     </section>
     <section class="feed-shelf discovery-section recent-shelf" id="fresh" data-feed-shelf aria-labelledby="fresh-title">
       <div class="heading-with-count"><h2 id="fresh-title">{e(fresh_label)}</h2><span>{len(fresh_ids)}개 영상</span></div>
       <p>{e(fresh_basis)}</p><div class="video-grid">{cards(fresh_ids)}</div>
     </section>
     <section class="discovery-section requires-js" id="source-types" aria-labelledby="source-types-title">
       <h2 id="source-types-title">근거 자료별 탐색</h2>
       <p>강의와 함께 확인할 수 있는 원본 자료로 고르세요.</p>
       <div class="discovery-pills" aria-label="근거 자료 유형">{source_pills}</div>
     </section>
     <section class="discovery-section requires-js" id="detail-topics" aria-labelledby="detail-topics-title">
       <h2 id="detail-topics-title">세부 주제별 탐색</h2>
       <div class="discovery-pills detail-topic-pills" aria-label="세부 주제">{tag_pills}</div>
     </section>
     <section class="feed-shelf discovery-section archive-shelf" data-feed-shelf aria-labelledby="archive-title">
       <div class="heading-with-count"><h2 id="archive-title">나머지 강의</h2><span>{len(rest)}개 영상</span></div>
       <div class="video-grid">{cards(rest)}</div>
     </section>
     <section class="catalog-shelf" id="course-discovery">
       <div><h2>과목 둘러보기</h2><a href="#library">전체 과목 보기 →</a></div>
       <nav aria-label="공개 과목">{course_links}</nav>
     </section>"""


def queue_html(c, rows, model, lookup):
    def item(vid, reason=''):
        course,v=lookup[vid]
        hint=reason or f'{course["ko"]} · {course["id"]}'
        return (f'<a href="#video-{e(vid)}" class="queue-row" data-queue-video="{e(vid)}">{thumbnail(v,course,record=model["videos"][vid])}'
                f'<span><strong>{e(video_title(v))}</strong><small>{e(course["faculty"])}</small>'
                f'<small>{e(hint)}</small></span></a>')
    def related_for(row):
        record=model['videos'][row['id']]
        items=''.join(item(vid,record['related_reasons'][vid]) for vid in record['related_ids'][:6])
        empty='<p class="rail-empty">아직 연결할 관련 강의가 없습니다.</p>'
        return f'<div data-related-video="{e(row["id"])}">{items or empty}</div>'
    same=''.join(item(v['id']) for v in rows)
    recommended=''.join(related_for(v) for v in rows)
    return (f'<aside class="watch-rail" aria-label="이어 볼 강의"><div class="course-queue" data-course-queue>'
            f'<h3>관련 강의</h3>{recommended}<details class="watch-course"><summary>{e(c["ko"])} · 전체 {len(rows)}개</summary>{same}</details>'
            '</div></aside>')


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
    return f'<section class="video-note" id="video-{e(vid)}" data-video-notes="{e(vid)}" aria-labelledby="{name}">{label}{body}<p class="video-source">재생 문제 발생 시 {fallback}</p></section>'


def lesson_sources(c, video, note, official):
    vid = video['id']
    sections = []
    for title, rows in (('요약의 근거', (note or {}).get('evidence', [])),
                        ('추가 참고자료', (note or {}).get('references', [])),
                        ('공식 자료', [{'url':f'https://www.youtube.com/watch?v={vid}','label':'YouTube 공식 영상'}, {'url':official,'label':'CMU CS Learn'}])):
        if rows:
            links=''.join(f'<li>{link(r["label"],r["url"])}</li>' for r in rows)
            sections.append(f'<h4>{title}</h4><ul>{links}</ul>')
    basis = (note or {}).get('basis')
    context = f'<p>{e(basis)}</p>' if basis else '<p>이 영상의 별도 요약 근거는 아직 확인되지 않았습니다.</p>'
    return f'<div class="lesson-source-list" data-video-sources="{e(vid)}">{context}{"".join(sections)}</div>'


def learning_panel(cid, key, body):
    return (f'<section class="learning-panel" id="panel-{cid}-{key}" role="tabpanel" '
            f'aria-labelledby="tab-{cid}-{key}" data-study-panel="{key}">{body}</section>')


def learning_tabs(cid, panels):
    labels = [('notes','강의 노트'),('clips','핵심 구간'),('sources','출처')]
    buttons = ''.join(f'<button type="button" id="tab-{cid}-{key}" role="tab" data-study-tab="{key}" aria-selected="{str(key=="notes").lower()}" aria-controls="panel-{cid}-{key}" tabindex="{0 if key=="notes" else -1}">{label}</button>' for key,label in labels)
    return (f'<div class="learning-pane"><div class="learning-tabs requires-js" role="tablist" aria-label="강의 학습 자료">{buttons}</div>'
            f'{"".join(learning_panel(cid,key,panels[key]) for key,_ in labels)}</div>')


def lesson_html(c, video_rows, notes, model, lookup, editorials, briefs, official):
    if not video_rows or any(not re.fullmatch(r'[A-Za-z0-9_-]{11}', row['id']) for row in video_rows):
        raise ValueError(f'Missing or invalid official videos: {c["id"]}')
    playlist = c['playlist']
    first = video_rows[0]
    options = ''.join(f'<option value="{e(v["id"])}" data-video-option="{e(v["id"])}" data-title="{e(v["title"].split(" | ", 1)[-1])}" data-availability="{e(v.get("availability", "unknown"))}" data-cc="{e(v.get("english_cc", "not-confirmed"))}"  data-poster="{e(model["videos"][v["id"]].get("poster_url") or "")}" data-duration="{e(duration(v))}">{i+1:02} · {e(v["title"].split(" | ", 1)[-1])}</option>' for i, v in enumerate(video_rows))
    articles = ''.join(video_note(c, row, i, notes.get((c['id'], row['id']))) for i, row in enumerate(video_rows))
    cid = e(c['id'])
    overview = ''.join(briefing_html(c, v, notes.get((c['id'],v['id'])), briefs.get((c['id'],v['id'])), i+1) for i,v in enumerate(video_rows))
    clips = ''.join(briefing_html(c, v, notes.get((c['id'],v['id'])), briefs.get((c['id'],v['id'])), i+1, clips_only=True) for i,v in enumerate(video_rows))
    sources = ''.join(lesson_sources(c,v,notes.get((c['id'],v['id'])),official) for v in video_rows)
    def tags_for(v):
        record=model['videos'][v['id']]
        tags=(record['tags'] or record['course_tags'])[:4]
        buttons=''.join(f'<a href="#topics" data-search-tag="{e(t)}">{e(t)}</a>' for t in tags)
        return f'<div class="watch-tags" data-video-tags="{e(v["id"])}" aria-label="강의 태그">{buttons}</div>'
    watch_tags=''.join(tags_for(v) for v in video_rows)
    editor_html=''.join(render_editorial(v,model['videos'][v['id']],notes.get((c['id'],v['id'])),
                              briefs.get((c['id'],v['id'])),editorials.get(v['id'])) for v in video_rows)
    panels = learning_tabs(cid, {'notes':overview+f'<div class="lesson-notes">{articles}</div>',
      'clips':clips, 'sources':sources})
    return f"""
      <div class="lesson-control requires-js"><label for="videos-{cid}">강의 영상 선택</label>
      <select id="videos-{cid}" data-video-select>{options}</select></div>
      <div class="lesson-layout">
        <div class="watch-detail">
        <div class="lesson-screen">
          <div class="player" data-player>
            <div class="player-placeholder">
            <span class="player-poster">{thumbnail(first,c,True,model["videos"][first["id"]])}</span>
            <button class="play requires-js" type="button" data-play="{e(playlist)}" aria-label="전체 영상 재생"><span aria-hidden="true">▶</span><span class="visually-hidden" data-video-title>{e(video_title(first))}</span></button></div>
          </div>
          <p class="active-clip" data-active-clip aria-live="polite" hidden></p>
          <h2 class="watch-title" data-watch-title tabindex="-1">{e(video_title(first))}</h2>
          <p class="watch-line">{e(c["faculty"])} · {e(c["id"])} · {e(c["ko"])}<span data-watch-duration></span></p>
          <div class="watch-meta">
            <button class="mark-pill requires-js" data-mark-save type="button" aria-pressed="false">◷ 나중에 보기</button>
            <button class="mark-pill requires-js" data-mark-watch type="button" aria-pressed="false">이 영상 시청 완료</button>
            <a data-video-original href="https://www.youtube.com/watch?v={e(first['id'])}">YouTube에서 열기 ↗</a>
            <button type="button" class="full-video requires-js" data-full-video hidden>전체 영상으로 전환</button>
          </div>
          {watch_tags}
          <details class="caption-help"><summary><strong data-cc-status>자막과 공식 재생목록</strong></summary>
          <p>플레이어의 CC 버튼과 설정에서 자막을 선택하세요. 영상에 따라 언어와 제공 여부가 달라집니다. {link('공식 재생목록',f'https://www.youtube.com/playlist?list={playlist}')}</p></details>
        </div>
        {editor_html}
        {panels}
        </div>
        {queue_html(c,video_rows,model,lookup)}
      </div>
      """


def workspace_html(c, official, videos, notes, model, lookup, editorials, briefs):
    fallback = ''.join(f'<li>{link(r["label"], r["url"])}</li>' for r in c['resources'])
    resources = f'<details class="sources"><summary>출처 및 보충 자료</summary><ul>{fallback}<li>{link("CMU 공식 CS Learn", official)}</li></ul></details>'
    prep = f'<p class="prepare"><strong>이 과목을 보기 전에</strong> {e(c["prepare"])}</p>'
    if c['status'] == 'planned':
        return f'{prep}<p class="not-yet">CS Learn에서 공개되면 공식 강의를 볼 수 있습니다.</p>{resources}'
    playlist = c.get('playlist', '')
    if not re.fullmatch(r'PL[A-Za-z0-9_-]{8,60}', playlist):
        raise ValueError(f'Invalid official playlist: {c["id"]}')
    watch = lesson_html(c, videos.get(c['id'], []), notes, model, lookup, editorials, briefs, official)
    return prep + f'<div class="official-watch">{watch}</div>' + resources


def course_html(c, track, official, videos, notes, model, lookup, editorials, briefs):
    key = ' '.join([c['id'], c['id'].replace('-', ''), c['title'], c['ko'], c['faculty'], c['level'],
                    track, c['summary'], c['prepare'], ' '.join(c['tags']), ' '.join(row['title'] for row in videos.get(c['id'], []))])
    status = 'YouTube 공개' if c['status'] == 'available' else '2027년 1월 예정'
    tags = ''.join(f'<li>{e(t)}</li>' for t in c['tags'])
    cid = f'course-{e(c["id"])}'
    progress = '<span class="row-progress requires-js" data-course-progress></span>' if c['status'] == 'available' else ''
    start = '학습 열기' if c['status'] == 'available' else '과목 미리보기'
    contents = workspace_html(c, official, videos, notes, model, lookup, editorials, briefs)
    legacy_anchors = ('<noscript>' + ''.join(f'<span id="step-{e(c['id'])}-{key}"></span>' for key in ('watch','practice','reflect')) + '</noscript>') if c['status'] == 'available' else ''
    return f"""
    <article id="{cid}" class="course" tabindex="-1" aria-labelledby="{cid}-title"
      data-course data-id="{e(c['id'])}" data-title="{e(c['ko'])}" data-track="{e(c['track'])}" data-status="{e(c['status'])}" data-keywords="{e(key)}">
      {legacy_anchors}<details class="workspace" data-workspace>
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

def document(data, videos, notes, briefs):
    courses = data['courses']
    tracks = data['tracks']
    by_id = {c['id']: c for c in courses}
    routes = ''.join(route_html(r, by_id) for r in data['routes'])
    editorials = read_editorial(BASE,{v["id"] for rows in videos.values() for v in rows})
    model = build_feed_model(data,videos,notes,briefs,editorials)
    lookup = {v['id']:(by_id[cid],v) for cid,rows in videos.items() for v in rows}
    cards = ''.join(course_html(c, tracks[c['track']], data['source'], videos, notes, model, lookup, editorials, briefs) for c in courses)
    track_opts = ''.join(f'<option value="{e(k)}">{e(v)}</option>' for k, v in tracks.items())
    available = sum(c['status']=='available' for c in courses)
    planned = sum(c['status']=='planned' for c in courses)
    updated = e(data['checked'])
    featured = by_id[data['routes'][0]['steps'][0]]
    official = link('CMU 공식 강의 목록', data['source'], 'official')
    announcement = link('CMU 출시 공지', data['announcement'])
    total_videos = sum(map(len, videos.values()))
    feed = feed_html(courses, videos, notes, briefs, model)
    ranking_records={vid:{k:row[k] for k in ('search_terms','short_title','title','availability')} for vid,row in model['videos'].items()}
    recommend_data = json.dumps({'videos':ranking_records,'feed_ids':model['feed_ids']},ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')
    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="카네기멜론 CS Learn 공개 강의를 찾아보고 AI 에이전트, ML 시스템, 소프트웨어 설계, 컴퓨팅 기초를 공부하는 한국어 길잡이.">
  <meta name="theme-color" content="#ffffff">
  <meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' https://i.ytimg.com; frame-src https://www.youtube-nocookie.com; connect-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'">
  <title>CMU CS Learn · 한국어 독학 가이드</title>
  <link rel="canonical" href="https://yongkilee.com/learning/cmu-cs-learn/">
  <link rel="stylesheet" href="./style.css?v=9">
  <link rel="stylesheet" href="./editorial.css?v=1">
  <script defer src="./feed-recommend.js?v=1"></script>
  <script defer src="./study.js?v=10"></script>
</head>
<body>
  <a class="skip" href="#videos">강의로 건너뛰기</a>
  <header class="mast">
    <div class="shell topbar">
      <a href="#videos" class="brand" aria-label="CMU 학습실 홈"><span>CMU</span><span class="brand-tag">Learn</span></a>
      <form id="header-search" class="top-search requires-js" role="search" aria-label="강의 영상 검색">
        <input type="search" id="video-query" placeholder="강의, 과목, 키워드 검색" aria-label="강의, 과목, 키워드 검색" autocomplete="off">
        <button type="submit" aria-label="검색"><svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5" fill="none" stroke="currentColor" stroke-width="2"/><path d="m16 16 4 4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg></button>
      </form>
      <nav aria-label="페이지"><a href="#topics" class="requires-js" data-top-view="browse">주제</a><a href="#library" data-top-view="catalog">과목</a><a href="#study-next" class="requires-js" data-top-view="learn">내 학습</a></nav>
    </div>
  </header>
  <main class="shell">
    <section id="videos" class="feed" aria-labelledby="feed-title">
      <div class="feed-intro">
        <h1 id="feed-title">다음에 어떤 강의를 볼까요?</h1>
        <p class="feed-intro-copy">카네기멜론의 공식 컴퓨터과학 강의 {total_videos}개를 한곳에 모았습니다.<br>한국어 노트, 핵심 구간, 원본 출처와 함께 관심 있는 강의부터 보세요.</p>
        <p class="feed-context-link"><a href="#library">공개 과목 전체 보기</a><span> · AI, 머신러닝, 소프트웨어 설계, 컴퓨팅 기초</span></p>
      </div>
      <p id="feed-results" class="visually-hidden" aria-live="polite"></p>
      <section id="discovery-results" class="discovery-section" aria-labelledby="discovery-results-title" hidden>
        <div class="heading-with-count"><div><h2 id="discovery-results-title" tabindex="-1">강의 결과</h2><p id="discovery-count"></p></div><button class="clear" id="clear-discovery" type="button">전체 보기</button></div>
        <p class="empty" id="feed-empty" hidden>해당 강의를 찾지 못했어요. 다른 관심사나 주제를 선택해 보세요.</p>
        <div class="video-grid" id="discovery-grid"></div>
      </section>
      <script type="application/json" id="recommend-data">{recommend_data}</script>
      {feed}
    </section>
    <p class="watch-back requires-js"><a href="#videos" id="back-to-feed">← 모든 강의</a></p>
    <section id="study-next" class="study-grid" aria-labelledby="study-heading">
      <div class="section-title study-heading"><h1 id="study-heading">내 학습</h1><p>최근에 연 강의를 이어 보세요. 시청 완료는 영상마다 직접 표시할 수 있습니다.</p></div>
      <article class="next-sheet">
        <p class="eyebrow" id="next-label">추천 시작 과목</p>
        <h2 id="next-title">{e(featured['ko'])}</h2>
        <p id="next-step">{e(featured['id'])} · 다음: 공식 강의 보기</p>
        <a class="cta" id="next-cta" href="#course-{e(featured['id'])}">공부 시작하기 →</a>
      </article>
      <aside class="progress-sheet" aria-label="내 학습 진도">
        <p class="eyebrow">MY PROGRESS</p>
        <h2 id="study-progress">0 / {total_videos}개 영상</h2>
        <progress id="study-meter" value="0" max="{total_videos}" aria-label="시청 완료한 영상"></progress>
        <p id="study-count">전체 강의를 시청 완료한 과목 0 / {available}</p>
        <p id="storage-note" hidden>현재 브라우저에서 저장할 수 없어 새로고침하면 진도가 초기화됩니다.</p>
        <p class="local-note">시청 기록은 이 브라우저에만 남습니다.</p>
      </aside>
      <section class="saved-shelf" aria-labelledby="saved-heading"><h2 id="saved-heading">나중에 보기</h2><p id="saved-empty">나중에 볼 강의를 저장하면 여기에 표시됩니다.</p><ul id="saved-videos"></ul></section>
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
      <noscript><p>이 환경에서는 검색, 내장 플레이어, 진도 저장이 꺼져 있습니다. 아래 과목을 펼쳐 공식 강의 링크와 노트를 볼 수 있습니다.</p></noscript>
      <div class="empty" id="empty" hidden><h3>검색 결과가 없어요</h3><p>키워드를 줄이거나 필터를 초기화해 보세요.</p><button class="clear" type="button" data-reset>검색·필터 초기화</button></div>
      <div class="courses">{cards}</div>
    </section>
    <section id="paths" aria-labelledby="paths-title">
      <div class="section-title"><p class="eyebrow">02 / ROADMAP</p><h2 id="paths-title">목표별 학습 경로</h2><p>독학용 추천 순서이며 공식 선수과목이 아닙니다.</p></div>
      <div class="routes">{routes}</div>
    </section>
  </main>
  <footer><div class="shell footer-inner">
    <div><strong>CMU CS Learn · 한국어 독학 가이드</strong><p>CMU와 별개인 비공식 정리입니다. 한국어 안내와 요약은 별도로 작성했으며 강의 영상·슬라이드·자막은 재배포하지 않습니다. CMU의 자가 학습 교재와 AI 튜터는 공식 안내상 별도 공개 예정입니다. 공식 목록 확인: <time datetime="{updated}">{updated}</time>.</p></div>
    <div class="foot-links">{official}{announcement}<a href="#library">과목 목록 ↑</a></div>
  </div></footer>
</body>
</html>
"""


def build(output):
    data = json.loads((BASE / 'catalog.json').read_text(encoding='utf-8'))
    videos, notes = read_lessons()
    html = document(data, videos, notes, read_briefings(videos))
    output.mkdir(parents=True, exist_ok=True)
    (output / 'index.html').write_text(html, encoding='utf-8')
    for asset in ('study.js','style.css','feed-recommend.js','editorial.css'):
        shutil.copyfile(BASE / 'assets' / asset, output / asset)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=BASE / 'dist')
    args = parser.parse_args()
    build(args.output)


if __name__ == '__main__':
    main()
