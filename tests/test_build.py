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
    def test_no_detail_routes_or_detail_links_are_published(self):
        subprocess.run([sys.executable,str(ROOT/'scripts/build.py')],check=True,cwd=ROOT,capture_output=True)
        output=ROOT/'dist'
        self.assertEqual(list((output/'projects').rglob('*.html')),[output/'projects/index.html'])
        self.assertFalse((output/'talks').exists());self.assertFalse((output/'demos').exists())
        for file in output.rglob('*.html'):
            doc=Document(file.read_text())
            for url in doc.links:
                self.assertNotIn('talks/',url)
                self.assertNotRegex(url,r'projects/[^?#/]+/')
                if url.startswith('#'):self.assertIn(url[1:],doc.ids)
    def test_research_and_outlined_project_action(self):
        html=self.build.render(self.data)
        self.assertIn('https://s-space.snu.ac.kr/handle/10371/11693',html)
        self.assertIn('button button-outline',html)
        self.assertIn('action-icon',html);self.assertNotIn('↗',html)
    def test_dashboard_omits_implementation_and_raw_table(self):
        text=(ROOT/'src/stats.html').read_text()+(ROOT/'assets/stats.js').read_text()
        for forbidden in ['SQLite','Daily data table','<table','Unmeasured','Reading paths']:
            self.assertNotIn(forbidden,text)
    def test_public_project_summaries_keep_the_approved_names(self):
        html=self.build.render(self.data)
        self.assertIn('빌리뷰',html);self.assertNotIn('BeReview',html)
        self.assertNotIn('CQRS with NestJS',html)
        self.assertEqual(len(self.data['projects']),5)

if __name__=='__main__':unittest.main()
