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
  self.assertEqual(html.count("data-mark-watch"),8)
  self.assertIn('0 / 21개 영상',html)
  self.assertIn('아래 과목을 펼쳐 공식 강의 링크와 노트를 볼 수 있습니다.',html)
  self.assertIn('<noscript><span id="step-11-768-watch"></span><span id="step-11-768-practice"></span>',html)
  self.assertIn('핵심 개념과 예시',html)
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
  self.assertEqual(len(premieres),1)
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
  for removed in ('data-step-key=', 'data-study-tab="study"', '<textarea', '이해 확인', '남길 결과물', '세 단계 체크리스트', '0/3 단계', '스스로 실행해 볼 작업', '다음 추적 연습'):
   self.assertNotIn(removed,self.html)
 def test_briefing_fallbacks_are_available_for_every_video_and_do_not_fake_clip_bounds(self):
  self.assertEqual(len(set(re.findall(r'data-video-brief="([^"]+)"',self.html))),21)
  self.assertIn('학습 브리핑',self.html)
  self.assertNotIn('<iframe',self.html)
  for removed in ('data-step-key=', 'data-study-tab="study"', '<textarea', '이해 확인', '남길 결과물', '세 단계 체크리스트', '0/3 단계', '스스로 실행해 볼 작업', '다음 추적 연습'):
   self.assertNotIn(removed,self.html)
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
  self.assertEqual(len(briefs),6)
  self.assertEqual(sum(len(x['clips']) for x in briefs.values()),56)
  self.assertEqual(len(re.findall(r'data-clip-start="\d+" data-clip-end="\d+"',self.html)),56)
  self.assertEqual(self.html.count('class="more-clips"'),5)
 def test_briefing_terms_and_clip_context_are_indexed(self):
  from html import unescape
  attrs=re.search(r'data-feed-video="KQUtNJEzUxU"[^>]+data-feed-keywords="([^"]+)"',self.html)
  self.assertIsNotNone(attrs)
  for term in ('컴바이너','Combiner','로컬 합계'):
   self.assertIn(term,unescape(attrs.group(1)))
  self.assertIn('data-clip-keywords="Shuffle와 Combiner',self.html)
 def test_watch_workspace_has_discrete_learning_tabs(self):
  for key, label in [('notes','강의 노트'),('clips','핵심 구간'),('sources','출처')]:
   self.assertEqual(self.html.count(f'data-study-tab="{key}"'),8)
   self.assertEqual(self.html.count(f'data-study-panel="{key}"'),8)
   self.assertIn(label,self.html)
  self.assertEqual(self.html.count('data-video-sources='),21)
  self.assertNotIn('<iframe',self.html)
  for removed in ('data-step-key=', 'data-study-tab="study"', '<textarea', '이해 확인', '남길 결과물', '세 단계 체크리스트', '0/3 단계', '스스로 실행해 볼 작업', '다음 추적 연습'):
   self.assertNotIn(removed,self.html)

 def test_course_discovery_and_verified_additional_readings(self):
  self.assertIn('id="course-discovery"',self.html)
  self.assertIn('전체 과목 보기',self.html)
  self.assertIn('4449.pdf#page=2',self.html)
  self.assertIn('4449.pdf#page=6',self.html)
  self.assertIn('rdd-programming-guide.html#rdd-operations',self.html)

 def test_video_feed_exposes_provenance_and_watch_page_prioritizes_player(self):
  h=self.html
  self.assertGreater(h.index('id="topics"'),h.index('data-feed-shelf'))
  self.assertEqual(h.count('data-preview-frames="https://i.ytimg.com/vi/'),21)
  self.assertIn('data-poster="https://i.ytimg.com/vi/KQUtNJEzUxU/hqdefault.jpg"',h)
  self.assertIn('https://i.ytimg.com/vi/KQUtNJEzUxU/hq1.jpg',h)
  lead=re.search(r'<div class="feed-shelf leading-shelf".+?</div>\s*</div>',h,re.S).group()
  self.assertEqual(lead.count('data-feed-video='),8)
  self.assertEqual(set(re.findall(r'data-feed-video="([^"]+)"',lead)[:2]),{'KQUtNJEzUxU','w05Mk2tjl_U'})
  self.assertGreaterEqual(len(set(re.findall(r'data-feed-course="([^"]+)"',lead))),6)
  self.assertIn('공식 확인 구간',h)
  self.assertEqual(h.count('class="watch-detail"'),8)
  self.assertEqual(h.count('class="watch-rail"'),8)
  self.assertNotIn('class="secondary-queue"',h)
  detail=h[h.index('class="watch-detail"'):]
  self.assertLess(detail.index('data-player'),detail.index('data-watch-title'))
  self.assertLess(detail.index('data-watch-title'),detail.index('data-study-tab'))
  self.assertLess(detail.index('data-study-tab'),detail.index('class="watch-rail"'))

 def test_browse_hero_has_measured_content_hierarchy(self):
  h=self.html
  self.assertIn('class="feed-intro-copy"',h)
  self.assertIn('class="feed-context-link"',h)
  self.assertRegex(h,r'class="feed-context-link"><a href="#library"')
  self.assertNotIn('class="feed-signals"',h)
  self.assertEqual(h.count('class="feed-context"'),21)

 def test_home_discovery_follows_reference_section_order(self):
  h=self.html
  blocks=('featured-title','for-you','topics','fresh','source-types','detail-topics')
  offsets=[h.index(f'id="{name}"') for name in blocks]
  self.assertEqual(offsets,sorted(offsets))
  self.assertRegex(h,r'id="recommend-query"[^>]+maxlength="500"')
  self.assertNotIn('type="file"',h)
  self.assertIn('id="discovery-results"',h)

 def test_home_facets_and_recent_shelf_use_real_distinct_video_ids(self):
  h=self.html
  starter=re.search(r'class="feed-shelf leading-shelf".+?</div>\s*</div>',h,re.S).group()
  fresh=re.search(r'id="fresh"[^>]*>.*?</section>',h,re.S).group()
  first=re.findall(r'data-feed-video="([^"]+)"',starter)
  recent=re.findall(r'data-feed-video="([^"]+)"',fresh)
  self.assertEqual(len(first),8)
  self.assertEqual(len(recent),8)
  self.assertFalse(set(first) & set(recent))
  data=json.loads(re.search(r'id="recommend-data">(.+?)</script>',h).group(1))
  self.assertEqual(set(data['videos']),set(re.findall(r'data-feed-video="([^"]+)"',h)))
  for kind in ('topic','source','tag'):
   pills=re.findall(rf'data-discovery-kind="{kind}"[^>]+data-discovery-ids="([^"]+)"[^>]+>[^<]+<span>(\d+)</span>',h)
   self.assertTrue(pills)
   for ids,count in pills:
    self.assertEqual(len(set(ids.split())),int(count))
    self.assertTrue(set(ids.split())<=data['videos'].keys())
  self.assertIn('추천 보기',h)
  self.assertNotIn('<iframe',h)

 def test_watch_poster_has_verified_hd_and_a_low_resolution_fallback(self):
  self.assertIn('data-poster-hd="https://i.ytimg.com/vi/KQUtNJEzUxU/maxresdefault.jpg"',self.html)
  self.assertIn('data-poster="https://i.ytimg.com/vi/KQUtNJEzUxU/hqdefault.jpg"',self.html)
  self.assertNotRegex(self.html,r'<img[^>]+src="[^"]+/maxresdefault\.jpg"')
  self.assertEqual(self.html.count('class="watch-byline"'),8)
