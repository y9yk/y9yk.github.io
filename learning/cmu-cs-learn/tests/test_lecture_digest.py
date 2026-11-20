import json
from pathlib import Path
import tempfile
import unittest

from detail_editorial import read_digests, render_editorial
from feed_model import build_feed_model

VID = 'KQUtNJEzUxU'
YOUTUBE = 'https://www.youtube.com/watch?v=' + VID
VIDEO = {'id': VID, 'title': 'Lecture 2', 'duration_s': 100}
RECORD = {'youtube_url': YOUTUBE}
BRIEF = {'clips': [{'start': 12, 'end': 40}]}
ENTRY = {
    'source_kind': 'official-materials', 'takeaway': '비용을 구분하세요 <태그>',
    'summary': ['작업을 쪼갭니다.', '데이터 이동을 줄입니다.'],
    'concepts': [{'term': '셔플', 'meaning': '키에 따라 데이터를 옮깁니다.'}],
    'topics': ['대용량 컴퓨팅'], 'tags': ['교육예제 전용태그'],
    'sections': [{'start': 12, 'title': '설명', 'summary': '같은 키를 모읍니다.'}],
    'sources': [{'label': '공식 구간', 'url': YOUTUBE}],
}


class LectureDigestTests(unittest.TestCase):
    def load(self, entry):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            (base / 'lecture-digests.json').write_text(json.dumps({VID: entry}), encoding='utf-8')
            return read_digests(base, {'10-605': [VIDEO]}, {('10-605', VID): BRIEF})

    def test_digest_visible_and_honest_with_playable_window(self):
        row = self.load(ENTRY)[VID]
        html = render_editorial(VIDEO, RECORD, brief=BRIEF, digest=row)
        for text in ('영상 없이 읽는 강의', '비용을 구분하세요 &lt;태그&gt;', '셔플',
                     '대용량 컴퓨팅', '자막 미대조', '#video-KQUtNJEzUxU-clip-12', '0:12–0:40'):
            self.assertIn(text, html)

    def test_rejects_unverified_section_start_and_malformed_source(self):
        entry = dict(ENTRY, sections=[dict(ENTRY['sections'][0], start=13)])
        with self.assertRaises(ValueError):
            self.load(entry)
        with self.assertRaises(ValueError):
            self.load(dict(ENTRY, sources=[{'label': '자료', 'url': 'javascript:alert(1)'}]))

    def test_digest_tags_and_keywords_feed_existing_indexes(self):
        data = {'tracks': {'systems':'시스템'}, 'courses': [
            {'id':'10-605', 'title':'Large datasets', 'ko':'데이터', 'track':'systems'}
        ]}
        model = build_feed_model(data, {'10-605':[VIDEO]}, digests={VID: ENTRY})
        self.assertIn('교육예제 전용태그', model['videos'][VID]['tags'])
        self.assertIn('셔플', model['videos'][VID]['search_terms'])
        self.assertIn('대용량 컴퓨팅', model['videos'][VID]['search_terms'])

    def test_all_four_reviewed_digests_reach_generated_site(self):
        import build
        videos, notes = build.read_lessons()
        briefs = build.read_briefings(videos)
        data = json.loads((build.BASE / 'catalog.json').read_text(encoding='utf-8'))
        html = build.document(data, videos, notes, briefs)
        self.assertEqual(html.count('공식 스크립트 주요 구간과 대조</span>'), 4)
        for part in ('설거짓거리와 빵 부스러기', '토스트에 관한 작은 문서 모음',
                     '과도한 메일 삭제 사례', 'Bigram'):
            self.assertIn(part, html)
