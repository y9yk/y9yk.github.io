"""Normalize the verified CS Learn catalog into a video-first discovery feed."""
import re
import unicodedata
from collections import defaultdict
from urllib.parse import urldefrag

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


def _source_count(note, brief):
    # Count distinct documents cited for this lesson. A PDF page anchor and its
    # unanchored URL count once. Clip timestamp evidence is not another source.
    candidates = [*note.get('evidence', ()), *note.get('references', ()),
                  *brief.get('sources', ()), *brief.get('references', ()),
                  *(clip.get('reading') for clip in brief.get('clips', ()))]
    return len({urldefrag(item['url']).url for item in candidates
                if isinstance(item, dict) and item.get('url')})


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


def build_feed_model(catalog, video_index, notes=None, briefs=None):
    """Build keyed topics/channels/courses/videos, plus editorial feed_ids.

    notes and briefs are optional dicts keyed by (course_id, video_id), as
    returned by the existing content loaders. No engagement data are generated.
    """
    notes, briefs = notes or {}, briefs or {}
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
            image_base = 'https://i.ytimg.com/vi/' + vid + '/'
            poster = image_base + 'hqdefault.jpg' if source.get('thumbnail') else None
            videos[vid] = dict(
                id=vid, title=title, short_title=short_title, lesson_number=lesson_number,
                kind='trailer' if is_trailer else 'lesson', poster_url=poster,
                preview_thumbnails=[image_base + name + '.jpg' for name in ('hq1','hq2','hq3')]
                if poster and vid in VERIFIED_PREVIEWS else [],
                course_id=key, channel_id=CHANNEL_ID, topic_ids=[topic],
                tags=list(VIDEO_TAGS.get(vid, ())), course_tags=list(course.get('tags', ())),
                position=position, youtube_url='https://www.youtube.com/watch?v=' + vid,
                duration_s=source.get('duration_s'), availability=availability,
                english_cc=source.get('english_cc'), thumbnail=source.get('thumbnail', False),
                signals={'notes': bool(note), 'clips': len(brief.get('clips', ())),
                         'sources': _source_count(note, brief)},
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
    channel = {**CHANNEL, 'course_ids': list(courses), 'video_ids': feed_ids.copy()}
    return {'topics': topics, 'channels': {CHANNEL_ID: channel}, 'courses': courses,
            'videos': videos, 'feed_ids': feed_ids}
