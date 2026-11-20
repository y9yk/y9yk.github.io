import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from feed_model import CHANNEL_ID, build_feed_model  # noqa: E402


class FeedModelTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = json.loads((ROOT / 'catalog.json').read_text())
        cls.video_index = json.loads((ROOT / 'video-index.json').read_text())
        cls.model = build_feed_model(cls.catalog, cls.video_index)

    def test_metadata_preserved_without_invented_metrics(self):
        for course_id, group in self.video_index.items():
            for src in group:
                row = self.model['videos'][src['id']]
                self.assertEqual(row['course_id'], course_id)
                for key in ('duration_s', 'english_cc', 'availability', 'thumbnail'):
                    self.assertEqual(row[key], src.get(key))
                self.assertFalse({'views', 'likes', 'score', 'interest', 'comment_count'} & row.keys())

    def test_all_video_ids_ranked_once_and_channels_and_topics_resolve(self):
        self.assertCountEqual(self.model['feed_ids'], self.model['videos'])
        self.assertEqual(self.model['channels'][CHANNEL_ID]['video_ids'], self.model['feed_ids'])
        seen_later = False
        for vid in self.model['feed_ids']:
            row = self.model['videos'][vid]
            if row['availability'] != 'available':
                seen_later = True
            elif seen_later:
                self.fail('an available video was ranked after unverified/premiere videos')
            self.assertIn(vid, self.model['courses'][row['course_id']]['video_ids'])
            for topic in row['topic_ids']:
                self.assertIn(vid, self.model['topics'][topic]['video_ids'])

    def test_related_video_ranking_and_reasons(self):
        row = self.model['videos']['KQUtNJEzUxU']
        self.assertEqual(row['related_ids'][0], 'xd7fZ5QpezY')
        self.assertEqual(row['related_reasons']['xd7fZ5QpezY'], '같은 과목의 다음 영상')
        self.assertIn('MapReduce', row['tags'])
        for video in self.model['videos'].values():
            self.assertNotIn(video['id'], video['related_ids'])
            self.assertLessEqual(len(video['related_ids']), 6)
            self.assertCountEqual(video['related_ids'], video['related_reasons'])
            for related in video['related_ids']:
                self.assertEqual(self.model['videos'][related]['availability'], 'available')

    def test_underlying_notes_clips_and_distinct_documents_counted(self):
        key = ('10-605', 'KQUtNJEzUxU')
        a = {'url': 'https://example.test/paper.pdf'}
        b = {'url': 'https://example.test/paper.pdf#page=2'}
        c = {'url': 'https://example.test/docs'}
        note = {key: {'summary': '요약', 'evidence': [a], 'references': [b]}}
        brief = {key: {'clips': [{'evidence': {'url': 'https://youtube.com/watch?v=KQUtNJEzUxU&t=4'},
                                 'reading': c}]}}
        row = build_feed_model(self.catalog, self.video_index, note, brief)['videos'][key[1]]
        self.assertEqual(row['signals'], {'notes': True, 'clips': 1, 'sources': 2})
        self.assertEqual(row['reason'], '요약')

    def test_verified_poster_and_alternates_and_unknown_fallback(self):
        row = self.model['videos']['KQUtNJEzUxU']
        base = 'https://i.ytimg.com/vi/KQUtNJEzUxU/'
        self.assertEqual(row['poster_url'], base + 'hqdefault.jpg')
        self.assertEqual(row['preview_thumbnails'], [base + f'hq{i}.jpg' for i in range(1, 4)])
        video = {'id': 'unknown0000', 'title': 'Lecture 4', 'thumbnail': True}
        candidate = build_feed_model(self.catalog, {'10-605': [video]})['videos'][video['id']]
        self.assertIsNotNone(candidate['poster_url'])
        self.assertEqual(candidate['preview_thumbnails'], [])
        video['thumbnail'] = False
        self.assertIsNone(build_feed_model(self.catalog, {'10-605': [video]})['videos'][video['id']]['poster_url'])

    def test_best_supported_lessons_beat_trailer_and_preserve_diversity(self):
        key = ('10-605', 'KQUtNJEzUxU')
        notes = {key: {'summary': '요약', 'references': [{'url': 'https://example.test/paper'}]}}
        briefs = {key: {'clips': [{'start': 1700, 'end': 1944}]}}
        model = build_feed_model(self.catalog, self.video_index, notes, briefs)
        first = model['feed_ids'][:8]
        self.assertIn(key[1], first)
        self.assertNotIn('WqBTJeFJ-FA', first)
        ready_courses = {c for c, rows in self.video_index.items()
                         if any(v['availability'] == 'available' for v in rows)}
        self.assertEqual({model['videos'][vid]['course_id'] for vid in first}, ready_courses)

    def test_facets_join_unique_real_video_ids(self):
        for key in ('topics', 'tag_facets', 'source_types'):
            for facet in self.model[key].values():
                self.assertEqual(facet['video_count'], len(set(facet['video_ids'])))
                for vid in facet['video_ids']:
                    self.assertIn(vid, self.model['videos'])
        self.assertEqual(sum(x['video_count'] for x in self.model['topics'].values()), len(self.model['videos']))
        self.assertGreaterEqual(len(self.model['tag_facets']), 20)
        self.assertEqual(self.model['source_types']['official-chapter']['video_count'], 20)
        self.assertNotIn('WqBTJeFJ-FA', self.model['source_types']['official-chapter']['video_ids'])

    def test_fresh_uses_official_publish_timestamp_and_no_premieres_or_trailers(self):
        from datetime import datetime
        fresh = self.model['shelves']['fresh']
        self.assertGreaterEqual(len(fresh['video_ids']), 12)
        rows = [self.model['videos'][vid] for vid in fresh['video_ids']]
        dates = [datetime.fromisoformat(row['published_at']) for row in rows]
        self.assertEqual(dates, sorted(dates, reverse=True))
        self.assertTrue(all(row['kind'] == 'lesson' and row['availability'] == 'available' for row in rows))
        self.assertEqual(self.model['videos']['w05Mk2tjl_U']['duration_s'], 3161)
        self.assertIsNone(self.model['videos']['w05Mk2tjl_U']['published_date'])

    def test_provenance_keeps_citations_readable_and_scoped(self):
        key = ('10-605', 'KQUtNJEzUxU')
        evidence = [
            {'label':'공식 일정', 'url':'https://10605.github.io/schedule.html'},
            {'label':'강의 슬라이드', 'url':'https://example.test/slides'},
            {'label':'원 논문', 'url':'https://example.test/paper'},
            {'label':'Spark 공식 문서', 'url':'https://spark.apache.org/docs/'},
        ]
        model = build_feed_model(self.catalog, self.video_index, {key:{'evidence':evidence}})
        types = {ref['type']:ref for ref in model['videos'][key[1]]['source_refs']}
        for type_id in ('official-video', 'official-chapter', 'course-page', 'lecture-notes', 'academic-paper', 'official-docs'):
            self.assertIn(type_id, types)
        self.assertEqual(types['academic-paper']['scope'], 'lesson')
        self.assertIn(key[1], model['source_types']['academic-paper']['video_ids'])
