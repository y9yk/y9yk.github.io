"""Normalize the verified CS Learn catalog into a video-first discovery feed."""
import json
import re
import unicodedata
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from urllib.parse import urldefrag, urlsplit

SOURCE_SNAPSHOT = json.loads(Path(__file__).with_name('feed-source-snapshot.json').read_text(encoding='utf-8'))
SOURCE_TYPES = {
    'official-video': 'CMU 공식 영상',
    'official-chapter': '공식 영상 챕터',
    'course-page': '과목 안내·일정',
    'lecture-notes': '강의 슬라이드·노트',
    'academic-paper': '학술 논문',
    'official-docs': '공식 문서·예제',
    'other-reference': '기타 참고자료',
}
CHANNEL_ID = 'cmu-cs-learn'
CHANNEL = {'id': CHANNEL_ID, 'label': 'CS Learn at Carnegie Mellon',
           'url': 'https://www.youtube.com/@CMULearn'}

# Editorial discovery vocabulary from published lecture titles/CS Learn chapter
# descriptions. Course tags stay separate so the UI need not imply that a
# course-wide topic was actually covered in any particular recording.
VIDEO_TAGS = {
    'WqBTJeFJ-FA': ('과목 안내', '대규모 데이터'),
    'TJ6qYAaGRZ8': ('대규모 데이터', '확장성', '머신러닝'),
    'KQUtNJEzUxU': ('MapReduce', 'Spark', 'Polars', '셔플', '분산 처리'),
    'xd7fZ5QpezY': ('MapReduce', 'Spark', 'Polars', '분산 처리', '워크플로'),
    'w05Mk2tjl_U': ('AI 에이전트', '도구 호출', 'LLM'),
    'oPSMMckx3eY': ('Python', '프로그래밍 기초', '자료형', '변수'),
    '0nmhvgc5XOI': ('자료 표현', '이진수', '문자 인코딩'),
    'vh3oVBcWG0A': ('Python', '함수', '프로그래밍 기초'),
    '3TmIRW4N3zo': ('머신러닝', 'ML 시스템'),
    'nbBCi6SZ8hE': ('머신러닝', 'ML 시스템', '시스템 설계'),
    'f-uQBacLc2E': ('딥러닝', '프로그래밍 추상화', 'ML 시스템'),
    'N7V5hsQeGVM': ('소프트웨어 설계', '의존성', '트레이드오프'),
    '2Sgd3efXKGg': ('객체지향', '인터페이스', '캡슐화'),
    'P_33xayi9J8': ('객체지향', 'UML', '요구사항'),
    '1DvaPZ_4sh0': ('소프트웨어 설계', '품질 속성', '트레이드오프'),
    'Y4Q2V6MI1oA': ('시스템 설계', '컨텍스트 다이어그램', '요구사항'),
    'XTRyyqbo4cw': ('시스템 설계', '요구사항', '품질 속성', '트레이드오프'),
    'CV-H1MynwNg': ('품질 관리', '품질 보증', '트레이드오프'),
    'c-fD7vM0Qj8': ('품질 관리', '지표', '관찰 가능성'),
    'f8jUgfO-Aik': ('품질 관리', 'CI/CD', '테스트'),
    'vFJCgzuEkmY': ('ML 시스템', '모델 평가', '위험'),
}


# Official YouTube thumbnails verified as distinct decoded images for the
# current editorial snapshot. New IDs should not assume alternates exist.
VERIFIED_PREVIEWS = {
    'WqBTJeFJ-FA', 'TJ6qYAaGRZ8', 'KQUtNJEzUxU', 'xd7fZ5QpezY',
    'w05Mk2tjl_U', 'oPSMMckx3eY', '0nmhvgc5XOI', 'vh3oVBcWG0A',
    '3TmIRW4N3zo', 'nbBCi6SZ8hE', 'f-uQBacLc2E', 'N7V5hsQeGVM',
    '2Sgd3efXKGg', 'P_33xayi9J8', '1DvaPZ_4sh0', 'Y4Q2V6MI1oA',
    'XTRyyqbo4cw', 'CV-H1MynwNg', 'c-fD7vM0Qj8', 'f8jUgfO-Aik',
    'vFJCgzuEkmY',
}


def _key(value):
    return unicodedata.normalize('NFKC', value).strip().casefold()


def _source_count(note, brief, editorial=None):
    # Count distinct documents cited for this lesson. A PDF page anchor and its
    # unanchored URL count once. Clip timestamp evidence is not another source.
    candidates = [*note.get('evidence', ()), *note.get('references', ()),
                  *brief.get('sources', ()), *brief.get('references', ()),
                  *(clip.get('reading') for clip in brief.get('clips', ())),
                  *(row for row in (editorial or {}).get('evidence', ()) if row['kind'] != 'official-chapter')]
    return len({urldefrag(item['url']).url for item in candidates
                if isinstance(item, dict) and item.get('url')})


def _source_type(item):
    if item.get('type') in SOURCE_TYPES:
        return item['type']
    url = urlsplit(item['url'])
    host = url.hostname or ''
    label = item.get('label', '')
    if host in {'www.youtube.com', 'youtube.com', 'youtu.be'}:
        return 'official-chapter' if '챕터' in label else 'official-video'
    if '논문' in label or host in {'arxiv.org', 'doi.org', 'proceedings.neurips.cc'}:
        return 'academic-paper'
    if any(word in label for word in ('슬라이드', '강의 자료', '강의진 자료')):
        return 'lecture-notes'
    if any(word in label for word in ('예제 코드', '공식 문서', '교재', '가이드')) or host in {
        'spark.apache.org', 'docs.pola.rs',
    }:
        return 'official-docs'
    if any(word in label for word in ('과목', '일정', '강의계획서', '강의진 공식 사이트')):
        return 'course-page'
    return 'other-reference'


def _video_sources(video_url, chapter, note, brief, course, editorial=None):
    sources = []
    seen = set()

    def add(item, scope):
        if not isinstance(item, dict) or not item.get('url') or not item.get('label'):
            return
        source_type = _source_type(item)
        key = (source_type, item['url'])
        if key not in seen:
            seen.add(key)
            sources.append({'type': source_type, 'label': item['label'],
                            'url': item['url'], 'scope': scope})

    add({'type': 'official-video', 'label': 'CS Learn 공식 영상', 'url': video_url}, 'video')
    if chapter:
        add({'type': 'official-chapter', 'label': '공식 게시자 챕터·영상 설명',
             'url': video_url}, 'video')
    for fields in (note.get('evidence', ()), note.get('references', ()),
                   brief.get('sources', ()), brief.get('references', ())):
        for item in fields:
            add(item, 'lesson')
    for clip in brief.get('clips', ()):
        add(clip.get('reading'), 'lesson')
    editorial_types = {'official-chapter':'official-chapter', 'lecture-slides':'lecture-notes',
                       'primary-paper':'academic-paper', 'official-docs':'official-docs',
                       'official-code':'official-docs', 'course-schedule':'course-page',
                       'course-page':'course-page'}
    for row in (editorial or {}).get('evidence', ()):
        add({'type':editorial_types.get(row['kind'],'other-reference'),
             'label':row['title'],'url':row['url']}, 'video' if row['kind']=='official-chapter' else 'lesson')
    for item in course.get('resources', ()):
        # Alternate course recordings are not lesson-specific unless already
        # linked by the note. Stable course sources are separately scoped.
        source_type = _source_type(item)
        if source_type != 'official-video':
            add(item, 'course')
    return sources


def _indexed_facets(videos, feed_ids, facet):
    result = {}
    for vid in feed_ids:
        for key in dict.fromkeys(facet(videos[vid])):
            result.setdefault(key, []).append(vid)
    return result


def _relationship(current, candidate):
    shared = {_key(t) for t in current['tags']} & {_key(t) for t in candidate['tags']}
    same_course = current['course_id'] == candidate['course_id']
    same_topic = bool(set(current['topic_ids']) & set(candidate['topic_ids']))
    if not (same_course or shared or same_topic):
        return None
    next_lesson = same_course and candidate['position'] == current['position'] + 1
    # Deductive, editorial order only: no claim about popularity or viewers.
    order = (not next_lesson, not same_course, -len(shared), not same_topic,
             candidate['kind'] == 'trailer',
             abs(current['position'] - candidate['position']) if same_course else 0)
    reason = ('같은 과목의 다음 영상' if next_lesson else '같은 과목의 영상' if same_course
              else '공통 태그: ' + ', '.join(t for t in current['tags'] if _key(t) in shared)
              if shared else '같은 주제의 영상')
    return order, reason


def build_feed_model(catalog, video_index, notes=None, briefs=None, editorials=None):
    """Build keyed topics/channels/courses/videos, plus editorial feed_ids.

    notes and briefs are optional dicts keyed by (course_id, video_id), as
    returned by the existing content loaders. No engagement data are generated.
    """
    notes, briefs, editorials = notes or {}, briefs or {}, editorials or {}
    courses = {}
    videos = {}
    topics = {key: {'id': key, 'label': label, 'course_ids': [], 'video_ids': []}
              for key, label in catalog['tracks'].items()}
    priority = {'available': 0, 'premiere': 1}
    groups = defaultdict(list)
    for course in catalog['courses']:
        key = course['id']
        topic = course['track']
        if key in courses:
            raise ValueError(f'duplicate course: {key}')
        courses[key] = {'id': key, 'title': course['title'], 'label': course['ko'],
                        'channel_id': CHANNEL_ID, 'topic_ids': [topic],
                        'tags': list(course.get('tags', ())),
                        'faculty': course.get('faculty'), 'playlist': course.get('playlist'),
                        'status': course.get('status'), 'video_ids': []}
        topics[topic]['course_ids'].append(key)
        for position, source in enumerate(video_index.get(key, ()), start=1):
            vid = source['id']
            if vid in videos:
                raise ValueError(f'duplicate video: {vid}')
            note, brief = notes.get((key, vid), {}), briefs.get((key, vid), {})
            availability = source.get('availability')
            title = source['title']
            short_title = re.split(r'\s+\|\s+', title)[-1]
            lecture_match = re.match(r'Lecture (\d+)\b', short_title, re.I)
            lesson_number = int(lecture_match[1]) if lecture_match else None
            is_trailer = title.casefold().startswith('welcome to ')
            pinned = SOURCE_SNAPSHOT['videos'].get(vid, {})
            published_at = pinned.get('published_at') if availability == 'available' else None
            video_url = 'https://www.youtube.com/watch?v=' + vid
            lecture_tags = list(VIDEO_TAGS.get(vid, ()))
            search_terms = list(dict.fromkeys([
                short_title, key, course['title'], course['ko'], catalog['tracks'][topic],
                *lecture_tags, *course.get('tags', ()), *([course['faculty']] if course.get('faculty') else ()),
            ]))
            editorial = editorials.get(vid, {})
            source_refs = _video_sources(video_url, pinned.get('published_chapters'), note, brief, course, editorial)
            image_base = 'https://i.ytimg.com/vi/' + vid + '/'
            poster = image_base + 'hqdefault.jpg' if source.get('thumbnail') else None
            videos[vid] = dict(
                id=vid, title=title, short_title=short_title, lesson_number=lesson_number,
                kind='trailer' if is_trailer else 'lesson', poster_url=poster,
                preview_thumbnails=[image_base + name + '.jpg' for name in ('hq1','hq2','hq3')]
                if poster and vid in VERIFIED_PREVIEWS else [],
                course_id=key, channel_id=CHANNEL_ID, topic_ids=[topic],
                tags=lecture_tags, course_tags=list(course.get('tags', ())), search_terms=search_terms,
                source_refs=source_refs, position=position, youtube_url=video_url,
                published_at=published_at, published_date=published_at[:10] if published_at else None,
                duration_s=source.get('duration_s'), availability=availability,
                english_cc=source.get('english_cc'), thumbnail=source.get('thumbnail', False),
                signals={'notes': bool(note), 'clips': len(brief.get('clips', ())),
                         'sources': _source_count(note, brief, editorial)},
                reason=note.get('summary') or None,
            )
            topics[topic]['video_ids'].append(vid)
            courses[key]['video_ids'].append(vid)
            groups[priority.get(availability, 2) * 2 + int(is_trailer), key].append(vid)
    unknown = set(video_index) - set(courses)
    if unknown:
        raise ValueError(f'unknown courses in video index: {sorted(unknown)}')

    def support_order(vid):
        row = videos[vid]['signals']
        # Only completeness of available study material drives this preference,
        # not its raw volume (e.g. 40 chapters are not intrinsically better).
        return (not bool(row['clips'] and row['sources']), not row['notes'],
                not bool(row['clips']), not bool(row['sources']))

    # Within each availability/type tier, interleave courses to preserve
    # diversity. Place the best-supported video of each course first.
    feed_ids = []
    for rank in range(6):
        rows = [sorted(groups[rank, key], key=support_order) for key in courses]
        for pos in range(max(map(len, rows), default=0)):
            batch = [row[pos] for row in rows if pos < len(row)]
            feed_ids.extend(sorted(batch, key=support_order))
    feed_order = {vid: pos for pos, vid in enumerate(feed_ids)}
    for video in videos.values():
        related = []
        for candidate in videos.values():
            if candidate['id'] == video['id'] or candidate['availability'] != 'available':
                continue
            match = _relationship(video, candidate)
            if match:
                related.append((match[0], feed_order[candidate['id']], candidate['id'], match[1]))
        ordered = sorted(related)[:6]
        video['related_ids'] = [row[2] for row in ordered]
        video['related_reasons'] = {row[2]: row[3] for row in ordered}
    for row in topics.values():
        row['video_count'] = len(row['video_ids'])
    tags = _indexed_facets(videos, feed_ids, lambda v: v['tags'])
    source_ids = _indexed_facets(videos, feed_ids, lambda v: (r['type'] for r in v['source_refs']))
    tag_facets = {tag: {'id': tag, 'label': tag, 'video_ids': ids, 'video_count': len(ids)}
                  for tag, ids in sorted(tags.items(), key=lambda pair: (-len(pair[1]), _key(pair[0])))}
    source_types = {key: {'id': key, 'label': label, 'video_ids': source_ids.get(key, []),
                         'video_count': len(source_ids.get(key, ()))}
                    for key, label in SOURCE_TYPES.items()}
    dated = [vid for vid in feed_ids if videos[vid]['published_at'] and videos[vid]['kind'] == 'lesson']
    fresh = sorted(dated, key=lambda vid: datetime.fromisoformat(videos[vid]['published_at']),
                   reverse=True)
    channel = {**CHANNEL, 'course_ids': list(courses), 'video_ids': feed_ids.copy(),
               'video_count': len(feed_ids)}
    shelves = {
        'fresh': {'label': '최근 공개', 'video_ids': fresh,
                  'basis': 'YouTube 공식 공개 시각순 · 확인된 재생 가능 강의만',
                  'checked': SOURCE_SNAPSHOT['checked']},
        'featured': {'label': '추천 강의', 'video_ids': feed_ids[:8],
                     'basis': '과목 다양성과 검증된 학습자료 기준으로 편집'},
    }
    return {'topics': topics, 'tag_facets': tag_facets, 'source_types': source_types,
            'channels': {CHANNEL_ID: channel}, 'courses': courses, 'videos': videos,
            'feed_ids': feed_ids, 'shelves': shelves}
