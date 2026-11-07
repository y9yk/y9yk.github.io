const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const source = fs.readFileSync(path.join(__dirname, '../assets/analytics.js'), 'utf8');
function track(overrides = {}) {
  const sent = [];
  const stored = new Map();
  const navigator = { doNotTrack: '0', globalPrivacyControl: false, sendBeacon: (url, body) => { sent.push({ url, body }); return true; }, ...overrides.navigator };
  vm.runInNewContext(source, {
    document: { currentScript: { dataset: { endpoint: 'https://analytics.example', host: 'y9yk.github.io' } }, referrer: 'https://search.example/private?q=secret' },
    location: { hostname: overrides.host || 'y9yk.github.io', pathname: '/projects/review-analytics/', search: '?email=private@example.com' },
    navigator, innerWidth: 390, URL, Blob, crypto: { randomUUID: () => 'anonymous-random-0001' },
    sessionStorage: { getItem: (key) => stored.get(key), setItem: (key, value) => stored.set(key, value) },
    fetch: () => Promise.resolve(),
  });
  return { sent, stored };
}
test('tracking sends only the page path and referrer hostname', async () => {
  const result = track();
  assert.equal(result.sent.length, 1);
  const body = JSON.parse(await result.sent[0].body.text());
  assert.equal(body.path, '/projects/review-analytics/');
  assert.equal(body.referrer, 'search.example');
  assert.equal(body.device, 'mobile');
  assert.equal(Object.keys(body).length, 5);
  assert.doesNotMatch(JSON.stringify(body), /private|secret|email/);
});
test('DNT, GPC, and local previews do not collect events or session storage', () => {
  for (const config of [{ navigator: { doNotTrack: '1' } }, { navigator: { globalPrivacyControl: true } }, { host: '127.0.0.1' }]) {
    const result = track(config);
    assert.equal(result.sent.length, 0);
    assert.equal(result.stored.size, 0);
  }
});
