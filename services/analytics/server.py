"""Anonymous browser-session aggregates. Python standard library only."""
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import secrets
import sys
import sqlite3
import threading
import time
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

KST = timezone(timedelta(hours=9))
MAX_BODY = 2048
FIELDS = {'event_id', 'session_id', 'path', 'device', 'referrer'}
PUBLIC_SECTION = "CASE WHEN path LIKE '/projects/%' THEN '/projects/' WHEN path LIKE '/talks/%' THEN '/talks/' WHEN path IN ('/', '/stats/', '/for-fun/') THEN path ELSE '/other/' END"


def now():
    return datetime.now(KST)


class Store:
    def __init__(self, directory):
        directory.mkdir(parents=True, exist_ok=True)
        self.path = directory / 'analytics.sqlite3'
        key_file = directory / '.session-key'
        try:
            with key_file.open('xb') as file:
                os.chmod(key_file, 0o600)
                file.write(secrets.token_bytes(32))
        except FileExistsError:
            pass
        self.key = key_file.read_bytes()
        with self.connect() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS events (
                    event_hash TEXT PRIMARY KEY, day TEXT NOT NULL, hour INTEGER NOT NULL,
                    session_hash TEXT NOT NULL, path TEXT NOT NULL,
                    device TEXT NOT NULL, referrer TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS event_day ON events(day);
            ''')
            db.execute('INSERT OR IGNORE INTO metadata VALUES (?,?)', ('started_at', now().isoformat()))

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA journal_mode=WAL')
        try:
            with db:
                yield db
        finally:
            db.close()

    def purge(self):
        with self.connect() as db:
            db.execute('DELETE FROM events WHERE day < ?', ((now().date() - timedelta(days=90)).isoformat(),))

    def digest(self, value):
        return hmac.new(self.key, value.encode(), hashlib.sha256).hexdigest()

    def record(self, event):
        if not isinstance(event, dict) or set(event) != FIELDS or not all(isinstance(v, str) for v in event.values()):
            raise ValueError('Invalid event fields')
        for field in ['event_id', 'session_id']:
            if not re.fullmatch(r'[A-Za-z0-9_-]{12,80}', event[field]):
                raise ValueError('Invalid identifier')
        if len(event['path']) > 160 or not re.fullmatch(r'/(?:[a-z0-9-]+/)*', event['path']):
            raise ValueError('Invalid page path')
        if event['device'] not in {'desktop', 'mobile', 'tablet'}:
            raise ValueError('Invalid device')
        if event['referrer'] and (len(event['referrer']) > 100 or not re.fullmatch(r'[a-z0-9.-]+', event['referrer'])):
            raise ValueError('Expected referrer hostname only')
        instant = now()
        day = instant.date().isoformat()
        session = self.digest(day + ':' + event['session_id'])
        with self.connect() as db:
            cursor = db.execute('INSERT OR IGNORE INTO events VALUES (?,?,?,?,?,?,?)',
                (self.digest(event['event_id']), day, instant.hour, session, event['path'], event['device'], event['referrer']))
            db.execute('DELETE FROM events WHERE day < ?', ((instant.date() - timedelta(days=90)).isoformat(),))
            return cursor.rowcount == 1

    def stats(self, days):
        if days not in {7, 30}:
            raise ValueError('Supported ranges: 7 or 30 days')
        instant = now()
        today = instant.date()
        first = today - timedelta(days=days - 1)
        with self.connect() as db:
            started = db.execute('SELECT value FROM metadata WHERE key=?', ('started_at',)).fetchone()[0]
            rows = db.execute('SELECT day, COUNT(*) AS pageviews, COUNT(DISTINCT session_hash) AS sessions FROM events WHERE day>=? GROUP BY day', (first.isoformat(),)).fetchall()
            indexed = {row['day']: dict(row) for row in rows}
            daily = []
            for offset in range(days):
                day = (first + timedelta(days=offset)).isoformat()
                measured = day >= started[:10]
                daily.append(indexed.get(day, {'day': day, 'pageviews': 0 if measured else None, 'sessions': 0 if measured else None}))
            today_totals = indexed.get(today.isoformat(), {'day': today.isoformat(), 'pageviews': 0, 'sessions': 0})
            hours = {row['hour']: row['count'] for row in db.execute('SELECT hour, COUNT(*) AS count FROM events WHERE day=? GROUP BY hour', (today.isoformat(),))}
            def distribution(column, key):
                # Column names are internal constants, never request values.
                query = f'SELECT {column} AS label, COUNT(*) AS count FROM events WHERE day>=? GROUP BY {column} ORDER BY count DESC, label LIMIT 12'
                return [{key: row['label'], 'count': row['count']} for row in db.execute(query, (first.isoformat(),))]
            return {'source': 'anonymous-first-party', 'timezone': 'Asia/Seoul',
                    'collection_started_at': started, 'updated_at': instant.isoformat(),
                    'retention_days': 90, 'today': today_totals, 'daily': daily,
                    'range': {'days': days, 'pageviews': sum(row['pageviews'] or 0 for row in daily),
                              'sessions': sum(row['sessions'] or 0 for row in daily),
                              'pages': db.execute(f'SELECT COUNT(DISTINCT ({PUBLIC_SECTION})) FROM events WHERE day>=?', (first.isoformat(),)).fetchone()[0]},
                    'hourly': [{'hour': hour, 'pageviews': (hours.get(hour, 0) if hour <= instant.hour and (started[:10] < today.isoformat() or hour >= datetime.fromisoformat(started).hour) else None)} for hour in range(24)],
                    'pages': distribution(PUBLIC_SECTION, 'path'), 'devices': distribution('device', 'name'),
                    'referrers': distribution('referrer', 'name')}


class Handler(BaseHTTPRequestHandler):
    store = None
    allowed_origin = os.environ.get('SITE_ORIGIN', 'https://y9yk.github.io')
    public_stats_enabled = os.environ.get('PUBLIC_STATS_ENABLED', 'false').lower() == 'true'
    collection_enabled = os.environ.get('COLLECTION_ENABLED', 'false').lower() == 'true'
    limits = {}
    limits_lock = threading.Lock()

    def log_message(self, *_args):
        # Do not persist IP addresses, user agents, or arbitrary request paths.
        return

    def setup(self):
        super().setup()
        self.connection.settimeout(10)

    def respond(self, status, payload=None, origin=None):
        body = json.dumps(payload, separators=(',', ':')).encode() if payload is not None else b''
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        if origin:
            self.send_header('Access-Control-Allow-Origin', origin)
            self.send_header('Vary', 'Origin')
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == '/health':
            self.respond(200, {'ok': True})
        elif parsed.path == '/api/stats':
            if not self.public_stats_enabled:
                self.respond(404, {'error': 'Not found'})
                return
            query = parse_qs(parsed.query)
            try:
                days = int(query.get('days', ['30'])[0])
                self.respond(200, self.store.stats(days), '*')
            except ValueError:
                self.respond(400, {'error': 'Use days=7 or days=30'}, '*')
            except sqlite3.Error:
                self.respond(503, {'error': 'Statistics storage unavailable'}, '*')
        else:
            self.respond(404, {'error': 'Not found'})

    def do_OPTIONS(self):
        if self.headers.get('Origin') != self.allowed_origin or self.path != '/api/events':
            self.respond(403, {'error': 'Origin rejected'})
            return
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', self.allowed_origin)
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Access-Control-Max-Age', '600')
        self.send_header('Content-Length', '0')
        self.end_headers()

    def do_POST(self):
        if not self.collection_enabled:
            self.respond(404, {'error': 'Collection paused'})
            return
        if self.path != '/api/events':
            self.respond(404, {'error': 'Not found'})
            return
        if self.headers.get('Origin') != self.allowed_origin:
            self.respond(403, {'error': 'Origin rejected'})
            return
        # Short-lived keyed rate buckets; raw IP addresses are never saved.
        bucket = self.store.digest(self.client_address[0] + ':' + str(int(time.time() // 60)))
        with self.limits_lock:
            if len(self.limits) > 5000:
                self.limits.clear()
            self.limits[bucket] = self.limits.get(bucket, 0) + 1
            exceeded = self.limits[bucket] > 120
        if exceeded:
            self.respond(429, {'error': 'Rate limited'}, self.allowed_origin)
            return
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if size < 1 or size > MAX_BODY:
                raise ValueError('Invalid body size')
            event = json.loads(self.rfile.read(size))
            self.store.record(event)
        except (ValueError, UnicodeDecodeError):
            self.respond(400, {'error': 'Invalid event'}, self.allowed_origin)
            return
        except sqlite3.Error:
            self.respond(503, {'error': 'Statistics storage unavailable'}, self.allowed_origin)
            return
        self.respond(204, origin=self.allowed_origin)


class AnalyticsHTTPServer(ThreadingHTTPServer):
    def handle_error(self, request, client_address):
        # Retain the error category without the default peer-address log.
        error = sys.exception()
        print(f'Analytics request failed: {type(error).__name__}', flush=True)


def main():
    Handler.store = Store(Path(os.environ.get('ANALYTICS_DATA_DIR', '/data')))
    def maintenance():
        while True:
            try:
                Handler.store.purge()
            except sqlite3.Error:
                print('Analytics retention maintenance will retry.', flush=True)
            time.sleep(3600)
    threading.Thread(target=maintenance, daemon=True).start()
    port = int(os.environ.get('PORT', '8080'))
    print(f'Aggregate analytics listening on port {port}', flush=True)
    AnalyticsHTTPServer(('0.0.0.0', port), Handler).serve_forever()


if __name__ == '__main__':
    main()
