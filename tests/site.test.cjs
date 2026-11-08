const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

function renderImage(complete = false, naturalWidth = 0) {
  let onError;
  const image = { hidden: false, complete, naturalWidth, addEventListener(name, callback) { onError = callback; } };
  const document = { querySelectorAll: () => [image], querySelector: () => null };
  vm.runInNewContext(fs.readFileSync(path.join(__dirname, '../assets/site.js'), 'utf8'), { document });
  return { image, fail: () => onError() };
}

test('missing remote images are hidden while text labels remain in the document', () => {
  const page = renderImage();
  assert.equal(page.image.hidden, false);
  page.fail();
  assert.equal(page.image.hidden, true);
});

test('previously failed images are handled when the script loads', () => {
  assert.equal(renderImage(true, 0).image.hidden, true);
  assert.equal(renderImage(true, 24).image.hidden, false);
});

test('the sticky header adds scroll treatment without changing the shared component', () => {
  const state = new Map(); let onScroll;
  const header = { classList: { toggle: (name, active) => state.set(name, active) } };
  const document = { querySelectorAll: () => [], querySelector: () => header };
  const window = { scrollY: 0, addEventListener: (name, handler) => { onScroll = handler; } };
  vm.runInNewContext(fs.readFileSync(path.join(__dirname, '../assets/site.js'), 'utf8'), { document, window });
  assert.equal(state.get('is-scrolled'), false);
  window.scrollY = 100; onScroll(); assert.equal(state.get('is-scrolled'), true);
  window.scrollY = 0; onScroll(); assert.equal(state.get('is-scrolled'), false);
});


test('failed company logos hide their whole avatar without a placeholder', () => {
  let onError;
  const avatar = { hidden: false };
  const image = { hidden: false, complete: false, naturalWidth: 0,
    closest: () => avatar,
    addEventListener: (name, callback) => { onError = callback; } };
  const document = { querySelectorAll: () => [image], querySelector: () => null };
  vm.runInNewContext(fs.readFileSync(path.join(__dirname, '../assets/site.js'), 'utf8'), { document });
  onError();
  assert.equal(image.hidden, true);
  assert.equal(avatar.hidden, true);
});
