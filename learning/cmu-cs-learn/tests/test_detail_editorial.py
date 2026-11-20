import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from detail_editorial import read_editorial, render_editorial

VIDEO = {'id': 'KQUtNJEzUxU'}
RECORD = {'youtube_url':'https://www.youtube.com/watch?v=KQUtNJEzUxU'}

class DetailEditorialTests(unittest.TestCase):
    def test_video_segment_link_only_for_same_video_verified_bounds(self):
        guide={'why':'근거', 'what':['개념'], 'evidence':[
            {'kind':'official-chapter','title':'챕터','url':RECORD['youtube_url']+'&t=2692s','body':'설명'},
            {'kind':'official-chapter','title':'다른 영상','url':'https://www.youtube.com/watch?v=abcdefghijk&t=2692s','body':'설명'}]}
        html=render_editorial(VIDEO,RECORD,brief={'clips':[{'start':2692}]},guide=guide)
        self.assertEqual(html.count('학습실에서 구간 보기'),1)
        self.assertIn('#video-KQUtNJEzUxU-clip-2692',html)
    def test_unverified_video_labels_missing_explanation(self):
        html=render_editorial(VIDEO, RECORD)
        self.assertIn('아직 확인되지 않았습니다', html)
        self.assertIn(RECORD['youtube_url'], html)
        self.assertNotIn('이 강의를 볼 이유', html)

    def test_signed_explanations_and_sources_are_escaped_and_visible(self):
        guide={'why':'Why <example>', 'what':['Concept <sample>'], 'evidence':[
            {'kind':'원논문', 'title':'§4.3', 'url':'https://example.com/paper#page=6', 'body':'Known basis'}]}
        with tempfile.TemporaryDirectory() as folder:
            base=Path(folder)
            p=base/'editorial-guides.json'
            p.write_text(json.dumps({VIDEO['id']:guide}),encoding='utf-8')
            loaded=read_editorial(base, [VIDEO['id']])
            html=render_editorial(VIDEO, RECORD, guide=loaded[VIDEO['id']])
            self.assertIn('Why &lt;example&gt;',html)
            self.assertIn('Concept &lt;sample&gt;',html)
            self.assertIn('paper#page=6',html)
            self.assertIn('Known basis',html)
            guide['evidence'][0]['url']='javascript:alert(1)'
            p.write_text(json.dumps({VIDEO['id']:guide}),encoding='utf-8')
            with self.assertRaises(ValueError): read_editorial(base,[VIDEO['id']])
