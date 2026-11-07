import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class AnalyticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('analytics_server', ROOT / 'services/analytics/server.py')
        cls.server = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.server)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = self.server.Store(Path(self.temp.name))

    def event(self, **overrides):
        return {'event_id': 'event-00000001', 'session_id': 'session-00000001', 'path': '/', 'device': 'desktop', 'referrer': '', **overrides}

    def test_duplicate_events_do_not_inflate_counts(self):
        self.assertTrue(self.store.record(self.event()))
        self.assertFalse(self.store.record(self.event()))
        stats = self.store.stats(7)
        self.assertEqual(stats['today']['pageviews'], 1)
        self.assertEqual(stats['today']['sessions'], 1)
        self.store.record(self.event(event_id='event-00000002', path='/projects/'))
        stats = self.store.stats(7)
        self.assertEqual(stats['today']['pageviews'], 2)
        self.assertEqual(stats['today']['sessions'], 1)

    def test_public_stats_are_aggregate_only_and_fill_precollection_with_null(self):
        self.store.record(self.event(referrer='example.com'))
        result = self.store.stats(7)
        encoded = str(result)
        for private in ['session-00000001', 'event-00000001', 'session_hash', 'ip_address', 'user_agent']:
            self.assertNotIn(private, encoded)
        self.assertEqual(len(result['daily']), 7)
        self.assertIsNone(result['daily'][0]['pageviews'])
        self.assertEqual(result['pages'][0]['path'], '/')
        self.assertEqual(result['referrers'][0]['name'], 'example.com')

    def test_untrusted_fields_and_paths_are_rejected(self):
        for values in [{'path': '/?email=private@example.com'}, {'path': '/../../secret'},
                       {'referrer': 'https://example.com/private'}, {'device': '<script>'},
                       {'session_id': 'x'}, {'event_id': ''}]:
            with self.subTest(values=values), self.assertRaises(ValueError):
                self.store.record(self.event(**values))

    def test_unknown_collection_fields_are_rejected(self):
        with self.assertRaises(ValueError):
            self.store.record(self.event(email='someone@example.com'))

    def test_sqlite_survives_store_restart(self):
        self.store.record(self.event())
        restarted = self.server.Store(Path(self.temp.name))
        self.assertEqual(restarted.stats(7)['today']['pageviews'], 1)


if __name__ == '__main__':
    unittest.main()

class AnalyticsHTTPTests(unittest.TestCase):
    def test_origin_validation_and_public_aggregate_readback(self):
        import json
        import threading
        from urllib.request import Request, urlopen
        from urllib.error import HTTPError
        spec = importlib.util.spec_from_file_location('http_analytics', ROOT / 'services/analytics/server.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as directory:
            handler = type('TestHandler', (module.Handler,), {'store': module.Store(Path(directory)), 'limits': {}})
            server = module.ThreadingHTTPServer(('127.0.0.1', 0), handler)
            worker = threading.Thread(target=server.serve_forever, daemon=True)
            worker.start()
            base = f'http://127.0.0.1:{server.server_port}'
            event = json.dumps({'event_id':'http-event-000001','session_id':'http-session-000001','path':'/stats/','device':'desktop','referrer':''}).encode()
            try:
                bad = Request(base+'/api/events',data=event,headers={'Origin':'https://unapproved.example'},method='POST')
                with self.assertRaises(HTTPError) as error:
                    urlopen(bad,timeout=5)
                self.assertEqual(error.exception.code,403)
                error.exception.close()
                valid = Request(base+'/api/events',data=event,headers={'Origin':'https://y9yk.github.io'},method='POST')
                with urlopen(valid,timeout=5) as response:
                    self.assertEqual(response.status,204)
                with urlopen(base+'/api/stats?days=7',timeout=5) as response:
                    self.assertEqual(response.headers['Access-Control-Allow-Origin'],'*')
                    self.assertEqual(json.load(response)['today']['pageviews'],1)
                with self.assertRaises(HTTPError) as error:
                    urlopen(base+'/.session-key',timeout=5)
                self.assertEqual(error.exception.code,404)
                error.exception.close()
            finally:
                server.shutdown();server.server_close();worker.join(timeout=5)

class RetentionTests(unittest.TestCase):
    def test_old_events_are_removed_by_maintenance(self):
        from unittest.mock import patch
        spec = importlib.util.spec_from_file_location('retention_analytics', ROOT / 'services/analytics/server.py')
        module = importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as directory:
            store = module.Store(Path(directory))
            old = module.now() - module.timedelta(days=91)
            with patch.object(module, 'now', return_value=old):
                store.record({'event_id':'old-event-000001','session_id':'old-session-000001','path':'/','device':'desktop','referrer':''})
            store.purge()
            with store.connect() as db:
                self.assertEqual(db.execute('SELECT COUNT(*) FROM events').fetchone()[0],0)

class PublicPathPrivacyTests(unittest.TestCase):
    def test_detail_paths_are_grouped_before_public_readback(self):
        spec=importlib.util.spec_from_file_location('public_analytics',ROOT/'services/analytics/server.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as directory:
            store=module.Store(Path(directory))
            for i,path in enumerate(['/projects/private-a/','/projects/private-b/']):
                store.record({'event_id':f'privacy-event-{i:04}','session_id':'privacy-session-0001','path':path,'device':'desktop','referrer':''})
            stats=store.stats(7)
            self.assertEqual(stats['pages'],[{'path':'/projects/','count':2}])
            self.assertEqual(stats['range']['pages'],1)
            self.assertNotIn('private-a',str(stats))
