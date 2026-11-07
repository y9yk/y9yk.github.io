/* Anonymous tab sessions; no query strings, full referrers, or user identifiers. */
'use strict';
(() => {
  const script = document.currentScript;
  const endpoint = script?.dataset.endpoint;
  if (!endpoint || location.hostname !== script.dataset.host || navigator.doNotTrack === '1' || navigator.globalPrivacyControl) return;
  let session;
  try {
    session = sessionStorage.getItem('y9yk_visit_session');
    if (!session) { session = crypto.randomUUID(); sessionStorage.setItem('y9yk_visit_session', session); }
  } catch {
    session = crypto.randomUUID();
  }
  let referrer = '';
  try { const host = new URL(document.referrer).hostname; if (host !== location.hostname) referrer = host.toLowerCase(); } catch { /* Direct navigation has no referrer URL. */ }
  let path = location.pathname.replace(/index\.html$/, '');
  if (!path.endsWith('/')) path += '/';
  const event = { event_id: crypto.randomUUID(), session_id: session, path,
    device: innerWidth <= 600 ? 'mobile' : innerWidth <= 1024 ? 'tablet' : 'desktop', referrer };
  const body = JSON.stringify(event);
  if (!navigator.sendBeacon(endpoint + '/api/events', new Blob([body], { type: 'text/plain' }))) {
    fetch(endpoint + '/api/events', { method: 'POST', body, credentials: 'omit', keepalive: true, headers: { 'Content-Type': 'text/plain' } }).catch(() => {});
  }
})();
