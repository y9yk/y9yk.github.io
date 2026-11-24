import copy
import importlib.util
import json
from html.parser import HTMLParser
from pathlib import Path
import subprocess
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
class Document(HTMLParser):
    def __init__(self,text):super().__init__();self.ids=[];self.links=[];self.feed(text)
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if 'id' in attrs:self.ids.append(attrs['id'])
        if tag=='a':self.links.append(attrs.get('href',''))

class PublishedRoutesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run([sys.executable, str(ROOT/'scripts/build.py')], check=True, cwd=ROOT)

    def test_build_omits_private_and_retired_routes(self):
        output=ROOT/'dist'
        self.assertTrue((output/'projects/index.html').is_file())
        self.assertEqual({p.name for p in (output/'projects').iterdir()},{'index.html'})
        for route in ('learning', 'cmu-cs-learn', 'talks', 'demos', 'stats', 'for-fun'):
            self.assertFalse((output/route).exists(), route)
        for file in output.rglob('*.html'):
            doc=Document(file.read_text())
            for url in doc.links:
                self.assertFalse(url.startswith('talks/'))
                self.assertNotRegex(url,r'projects/[^?#/]+/')
                if url.startswith('#'):self.assertIn(url[1:],doc.ids)

    def test_astro_blog_builds_native_routes_for_published_posts(self):
        output = ROOT/'dist/blog'
        listing = (output/'index.html').read_text()
        self.assertNotIn('<iframe', listing)
        links = Document(listing).links
        posts = sorted((ROOT/'blog/src/posts').glob('*.md'))
        self.assertTrue(posts)
        for post in posts:
            with self.subTest(slug=post.stem):
                self.assertIn(f'/blog/{post.stem}/', links)
                article = (output/post.stem/'index.html').read_text()
                self.assertIn('<article', article)
                self.assertIn('discussion-heading', Document(article).ids)
                self.assertIn('/blog/', Document(article).links)

    def test_blog_shares_the_portfolio_header_and_stylesheet(self):
        partial=(ROOT/'src/header.html').read_text().strip()
        expected=partial.replace('{{prefix}}','/').replace('{{fun_link}}','').replace('<a href="/blog/">Blog</a>','<a href="/blog/" aria-current="page">Blog</a>')
        for page in (ROOT/'dist/blog').rglob('index.html'):
            with self.subTest(page=str(page.relative_to(ROOT))):
                text=page.read_text()
                self.assertIn(expected,text)
                self.assertIn('lang="ko"',text)
        css=''.join(p.read_text() for p in (ROOT/'dist/blog/_astro').glob('*.css'))
        self.assertIn('--site-header-height',css)
        self.assertIn('Inter',css)

    def test_blog_pages_keep_a_strict_policy_without_inline_code(self):
        for page in (ROOT/'dist/blog').rglob('index.html'):
            with self.subTest(page=str(page.relative_to(ROOT))):
                text=page.read_text()
                self.assertIn("default-src 'none'",text)
                self.assertNotRegex(text,r'<script(?![^>]*\ssrc=)[^>]*>')
                self.assertNotIn('<style',text)
                self.assertNotIn(' style="',text)

    def test_migrated_posts_are_complete_and_self_hosted(self):
        for post in (ROOT/'blog/src/posts').glob('*.md'):
            with self.subTest(slug=post.stem):
                text=post.read_text()
                self.assertNotIn('excerpt: true',text)
                self.assertNotIn('<style',text)
                self.assertNotRegex(text,r'<img[^>]*src="(?!/blog/media/)')
                for src in __import__('re').findall(r'src="/blog/(media/[^"]+)"',text):
                    self.assertTrue((ROOT/'blog/public'/src).is_file(),src)

    def test_blog_home_has_hero_latest_and_archive_with_thumbnails(self):
        listing=(ROOT/'dist/blog/index.html').read_text()
        ids=Document(listing).ids
        for section in ('blog-title','latest-title','all-title'):self.assertIn(section,ids)
        posts=list((ROOT/'blog/src/posts').glob('*.md'))
        self.assertEqual(listing.count('class="post-cover"'),len(posts))
        rss=(ROOT/'dist/blog/rss.xml').read_text()
        for post in posts:self.assertIn(f'https://yongkilee.com/blog/{post.stem}/',rss)

    def test_articles_offer_contents_and_neighbour_navigation(self):
        for post in (ROOT/'blog/src/posts').glob('*.md'):
            with self.subTest(slug=post.stem):
                article=(ROOT/'dist/blog'/post.stem/'index.html').read_text()
                if post.read_text().count('\n## ')>1:self.assertIn('data-toc',article)
                self.assertIn('class="post-pager"',article)

    def test_discussion_widget_waits_for_consent_and_honours_privacy_signals(self):
        script=(ROOT/'blog/public/blog.js').read_text()
        self.assertIn('globalPrivacyControl',script)
        self.assertIn('doNotTrack',script)
        self.assertIn("addEventListener('click'",script)
        self.assertLess(script.index('if (privacy)'),script.index("createElement('script')"))


class PublicBuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads((ROOT/'content/profile.json').read_text())
        spec=importlib.util.spec_from_file_location('build',ROOT/'scripts/build.py');cls.build=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.build)
    def test_only_public_summary_fields_are_accepted(self):
        self.build.validate(self.data)
        for field in ['sections','images','pipeline','evidence','code_artifact']:
            data=copy.deepcopy(self.data);data['projects'][0][field]=[]
            with self.subTest(field=field),self.assertRaises(ValueError):self.build.render(data)
    def test_private_source_links_are_rejected(self):
        data=copy.deepcopy(self.data);data['projects'][0]['summary']='https://docs.google.com/private'
        with self.assertRaises(ValueError):self.build.render(data)
    def test_content_escaping_and_link_schemes(self):
        data=copy.deepcopy(self.data);data['name']='<script>alert(1)</script>'
        self.assertNotIn('<script>alert',self.build.render(data))
        data=copy.deepcopy(self.data);data['links'][0]['url']='javascript:alert(1)'
        with self.assertRaises(ValueError):self.build.render(data)
    def test_research_and_outlined_project_action(self):
        html=self.build.render(self.data)
        self.assertIn('https://s-space.snu.ac.kr/handle/10371/11693',html)
        button=self.build.action('#projects','Projects')
        self.assertIn('button button-outline',button)
        self.assertIn('action-icon',button);self.assertNotIn('↗',html)
    def test_statistics_and_empty_fun_are_not_exposed(self):
        text=self.build.render(self.data)
        for forbidden in ['Site pulse','stats/','analytics.js','for-fun/']:
            self.assertNotIn(forbidden,text)
        self.assertIn('href="projects/"',text)
        self.assertNotIn('id="projects"',text)
        self.assertIn('<h1>Projects</h1>',self.build.render_projects(self.data))
        self.assertNotIn('Selected projects',text)
    def test_footer_company_marks_and_conversation_talk_link(self):
        text=self.build.render(self.data)
        footer=text.split('<footer>')[1].split('</footer>')[0]
        self.assertNotIn('<a ',footer)
        self.assertEqual(text.count('class="company-avatar"'),5)
        self.assertNotIn('<span>SK</span>',text)
        self.assertNotIn('<span>빌</span>',text)
        self.assertIn('company-logo',text)
        self.assertIn('상담 검색 서비스 (Customer conversation insights)',text)
        self.assertIn('SK AI Summit 2024 · Talk &amp; recording',self.build.render_projects(self.data))
        for filename in ['skt.png','lg.jpg','hyundai.png','tmax.png']:
            self.assertTrue((ROOT/'assets/companies'/filename).is_file())

    def test_current_skt_project_order_and_widget_evidence(self):
        ids=[p['id'] for p in self.data['projects'] if p['career_id']=='skt-current']
        self.assertEqual(ids,['marketing-ax-workspace','polaris-studio','smartbee','counseling-search'])
        text=self.build.render_projects(self.data)
        self.assertIn('https://www.youtube.com/watch?v=B1QARo421XA',text)
        self.assertIn('embeddable widget',text)

    def test_project_briefs_and_approved_talk_material(self):
        import hashlib
        text=self.build.render(self.data)
        for name in ['Polaris Studio','Marketing AX Workspace','My role','Challenge','Approach']:
            self.assertIn(name,self.build.render_projects(self.data))
        self.assertNotIn('Official session',text)
        self.assertIn('https://www.youtube.com/watch?v=256PfFzVDtw',text)
        self.assertIn('assets/talks/seoultech-2021.pdf',text)
        self.assertEqual(hashlib.sha256((ROOT/'assets/talks/seoultech-2021.pdf').read_bytes()).hexdigest(),'95c2cc201942a741c4a8ad92566fba11eafef9511521433d83c7b8438017a0c1')
        self.assertEqual({str(p.relative_to(ROOT)) for p in (ROOT/'assets/talks').iterdir()},self.build.TALK_ASSETS)
        data=copy.deepcopy(self.data);data['projects'][0]['brief']['internal_notes']='private'
        with self.assertRaises(ValueError):self.build.render(data)

    def test_home_keeps_career_summaries_and_projects_moves_to_index(self):
        home=self.build.render(self.data)
        listing=self.build.render_projects(self.data)
        self.assertNotIn('class="project-grid"',home)
        self.assertEqual(home.count('class="career-project"'),8)
        self.assertEqual(listing.count('class="project"'),8)
        self.assertIn('href="projects/#project-smartbee"',home)
        self.assertIn('href="blog/">Blog</a>',home)

    def test_home_contact_links_do_not_repeat_blog_navigation(self):
        home=self.build.render(self.data)
        social=home.split('<div class="social-links">')[1].split('</div>')[0]
        self.assertNotIn('Blog',social)
        self.assertIn('href="blog/">Blog</a>',home)

    def test_home_recent_projects_are_latest_first(self):
        home=self.build.render(self.data)
        links=[u for u in Document(home).links if u.startswith('projects/#project-')]
        self.assertEqual(links[:4],['projects/#project-marketing-ax-workspace','projects/#project-polaris-studio','projects/#project-smartbee','projects/#project-counseling-search'])

    def test_home_and_project_index_share_one_header_component(self):
        home=self.build.render(self.data).split('<header')[1].split('</header>')[0]
        listing=self.build.render_projects(self.data).split('<header')[1].split('</header>')[0]
        self.assertEqual(home,listing.replace('../',''))

    def test_project_previews_are_public_media_and_do_not_open_details(self):
        listing=self.build.render_projects(self.data)
        self.assertEqual(listing.count('class="project-list-preview"'),2)
        for path in ['assets/projects/review-widget.png']:
            self.assertTrue((ROOT/path).is_file())
            self.assertIn('../'+path,listing)
        self.assertNotIn('Read project',listing)
        for name in ['counseling-screen.png','smartbee-widget.png','aias-screen.png','targeting-screen.png']:
            self.assertNotIn(name,listing)
            self.assertFalse((ROOT/'assets/projects'/name).exists())
        self.assertNotIn('polaris-2.png',listing)
        self.assertNotIn('marketing-1.png',listing)
        self.assertNotIn('smartbee-widget-guide.jpg',listing)
        self.assertNotIn('sk-ai-summit-2024-video.jpg',listing)
        self.assertNotIn('notion',listing.lower())
        for link in Document(listing).links:
            self.assertNotRegex(link,r'(?:projects/)?(?:smartbee|reviewro|polaris-studio|marketing-ax-workspace)/')
        self.assertEqual({p.name for p in (ROOT/'assets/projects').iterdir()},{'review-widget.png','reviewro-app.png','SOURCES.md'})

    def test_confirmed_collaborators_are_sorted_and_exclude_the_owner(self):
        projects={p['id']:p for p in self.data['projects']}
        self.assertEqual(projects['reviewro']['collaborators'],['한송원','황윤교'])
        self.assertEqual(projects['aias']['collaborators'],['유근국'])
        self.assertEqual(projects['targeting']['collaborators'],['박인범'])
        for id in ['counseling-search','smartbee','polaris-studio','marketing-ax-workspace']:
            names=projects[id]['collaborators']
            self.assertEqual(names,sorted(set(names)))
            self.assertIn('유성현',names)
            self.assertNotIn('이용기',names)
        self.assertEqual(self.build.render_projects(self.data).count('class="project-collaborators"'),8)
        listing=self.build.render_projects(self.data)
        self.assertEqual(listing.count('SK Telecom colleagues'),6)
        self.assertNotIn('<p>Collaborators</p>',listing)

    def test_public_project_summaries_keep_the_approved_names(self):
        html=self.build.render(self.data)
        self.assertIn('빌리뷰',html);self.assertNotIn('BeReview',html)
        self.assertNotIn('CQRS with NestJS',html)
        self.assertEqual(len(self.data['projects']),8)

if __name__=='__main__':unittest.main()
