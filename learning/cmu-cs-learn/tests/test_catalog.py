import json
import unittest
from pathlib import Path
import re
import sys
import subprocess
import tempfile
ROOT=Path(__file__).resolve().parents[1]
EXPECTED={'10-605','15-110','17-214','15-442','17-635','17-643','11-768','17-645','15-259','11-777','17-619','07-280','17-627'}
class CatalogTest(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  with tempfile.TemporaryDirectory() as directory:
   out=Path(directory)
   subprocess.run([sys.executable,'build.py','--output',directory],cwd=ROOT,check=True)
   cls.html=(out/'index.html').read_text(encoding='utf-8')
   cls.served_assets={f:(out/f).read_bytes() for f in ('style.css','study.js')}
 def setUp(self): self.data=json.loads((ROOT/'catalog.json').read_text())
 def test_official_inventory(self):
  items=self.data['courses']
  self.assertEqual({i['id'] for i in items},EXPECTED)
  self.assertEqual(len(items),len(EXPECTED))
  self.assertEqual(sum(i['status']=='available' for i in items),8)
  self.assertEqual(sum(i['status']=='planned' for i in items),5)
 def test_routes_resolve(self):
  ids={i['id'] for i in self.data['courses']}
  for route in self.data['routes']:
   self.assertTrue(route['steps'])
   self.assertEqual(len(set(route['steps'])),len(route['steps']))
   self.assertTrue(set(route['steps'])<=ids)
 def test_all_cards_and_source_assets_are_emitted(self):
  html=self.html
  self.assertEqual(set(re.findall(r'<article id="(course-\d\d-\d{3})"',html)),{f'course-{i}' for i in EXPECTED})
  for name,asset in self.served_assets.items():
   self.assertEqual(asset,(ROOT/'assets'/name).read_bytes())
 def test_metadata_labels_and_links(self):
  for c in self.data['courses']:
   self.assertTrue(c['summary'] and c['practice'] and c['prepare'])
   self.assertTrue(all(r['url'].startswith('https://') for r in c['resources']))
   self.assertEqual(c['status']=='planned',c['release']=='2027-01')
 def test_study_room_is_available_without_invented_content(self):
  html=self.html
  self.assertIn('id="study-next"',html)
  self.assertIn('id="study-progress"',html)
  self.assertEqual(html.count('data-workspace'),13)
  self.assertEqual(html.count('data-step-key="watch"'),8)
  self.assertIn('공식 커리큘럼이나 수료 기준이 아닙니다',html)
  self.assertNotIn('<iframe',html) # third-party player must be opt-in
  self.assertIn('data-play=',html)
 def test_eight_official_playlists_and_no_upcoming_embeds(self):
  expected={'10-605':'PLOz411Ejgqdw','15-110':'PLB27aM0tkAQs','17-214':'PLBDTyW_Uan_k','15-442':'PLSH_5v_OOfP8','17-635':'PLBXWgYnejeLU','17-643':'PLBAcFaUDLxMA','11-768':'PLf0BEPn2BGr0','17-645':'PLDOc_XHH9ABE'}
  self.assertEqual({c['id']:c['playlist'] for c in self.data['courses'] if 'playlist' in c},expected)
  html=self.html
  self.assertEqual(set(re.findall(r'data-play="([^"]+)"',html)),set(expected.values()))
  self.assertIn('frame-src https://www.youtube-nocookie.com',html)
  self.assertNotIn('src="https://www.youtube-nocookie.com',html)
 def test_individual_official_video_inventory_is_rendered_without_preloading(self):
  video_index=json.loads((ROOT/'video-index.json').read_text())
  all_videos={x['id'] for xs in video_index.values() for x in xs}
  self.assertEqual(len(all_videos),21)
  html=self.html
  self.assertEqual(set(re.findall(r'data-video-option="([^"]+)"',html)),all_videos)
  self.assertEqual(set(re.findall(r'data-video-notes="([^"]+)"',html)),all_videos)
  self.assertIn('플레이어의 CC 버튼',html)
  self.assertNotIn('<iframe',html)
 def test_notes_are_exact_video_matches_and_show_documented_basis(self):
  import build
  videos,notes=build.read_lessons()
  html=self.html
  self.assertGreaterEqual(len(notes),20)
  for (course,video),note in notes.items():
   self.assertTrue(any(row['id']==video for row in videos[course]))
   self.assertTrue(note['evidence'] and note['references'])
   self.assertIn(f'data-video-notes="{video}"',html)
  captions=[v for rows in videos.values() for v in rows if v['english_cc']=='confirmed']
  premieres=[v for rows in videos.values() for v in rows if v['availability']=='premiere']
  self.assertEqual(len(captions),19)
  self.assertEqual(len(premieres),2)
 def test_feed_links_all_video_cards_to_details_and_has_one_queue_per_course(self):
  from html.parser import HTMLParser
  class Inventory(HTMLParser):
   def __init__(self,text):
    super().__init__(); self.feed_ids=[]; self.anchors=[]; self.queues=0; self.feed(text)
   def handle_starttag(self,tag,attrs):
    a=dict(attrs)
    if 'data-feed-video' in a: self.feed_ids.append(a['data-feed-video'])
    if 'data-video-notes' in a: self.anchors.append(a.get('id'))
    if 'data-course-queue' in a: self.queues+=1
  parsed=Inventory(self.html)
  self.assertEqual(len(set(parsed.feed_ids)),21)
  self.assertEqual({f'video-{v}' for v in parsed.feed_ids},set(parsed.anchors))
  self.assertEqual(parsed.queues,8)
  self.assertIn('id="header-search"',self.html)
  self.assertNotIn('<iframe',self.html)
 def test_briefing_fallbacks_are_available_for_every_video_and_do_not_fake_clip_bounds(self):
  self.assertEqual(len(set(re.findall(r'data-video-brief="([^"]+)"',self.html))),21)
  self.assertIn('학습 브리핑',self.html)
  self.assertNotIn('<iframe',self.html)
 def test_invalid_clips_are_rejected(self):
  import build
  row={'title':'Example','context':'context','evidence':{'label':'verified','url':'https://www.youtube.com/watch?v=oPSMMckx3eY'},'start':30,'end':80}
  build.validate_clip(row,100)
  for bad in [{**row,'start':81},{**row,'end':110},{**row,'end':'80'},{**row,'evidence':{'label':'unverified','url':'javascript:alert(1)'}}]:
   with self.assertRaises(ValueError): build.validate_clip(bad,100)
 def test_curated_clip_keys_counts_and_core_limit(self):
  import build
  videos,_=build.read_lessons()
  briefs=build.read_briefings(videos)
  self.assertEqual(len(briefs),5)
  self.assertEqual(sum(len(x['clips']) for x in briefs.values()),49)
  self.assertEqual(len(re.findall(r'data-clip-start="\d+" data-clip-end="\d+"',self.html)),49)
  self.assertEqual(self.html.count('class="more-clips"'),3)
