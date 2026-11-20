/* Local-only interest and public YouTube URL matching. No requests or storage. */
(function (global) {
  'use strict';
  const aliases = [
    ['python', '파이썬'], ['spark', '스파크'], ['polars', '폴라스'],
    ['mapreduce', 'map reduce', '맵리듀스', '맵 리듀스'],
    ['shuffle', '셔플'], ['combiner', '컴바이너', '콤바이너'],
    ['distributed processing', '분산 처리', '분산처리'],
    ['ai agent', 'ai agents', '에이전트', 'agent'],
    ['tool use', '도구 호출', '툴 호출'],
    ['machine learning', '머신러닝', '기계 학습', 'ml'],
    ['ml systems', 'ml 시스템', '머신러닝 시스템'],
    ['software architecture', '소프트웨어 아키텍처', '아키텍처'],
    ['software design', '소프트웨어 설계'], ['object oriented', 'oop', '객체지향', '객체 지향'],
    ['quality management', '품질 관리'], ['quality attributes', '품질 속성'],
    ['observability', '관찰 가능성', '옵저버빌리티'],
    ['binary', '이진수', '이진법'], ['function', '함수'],
    ['types', '자료형', '타입'], ['deep learning', '딥러닝'],
    ['testing', '테스트', '테스팅'], ['ci cd', 'cicd'],
  ];

  function normalize(value) {
    return String(value || '').normalize('NFKC').toLowerCase()
      .replace(/[^\p{L}\p{N}]+/gu, ' ').trim().replace(/\s+/g, ' ');
  }

  function contains(text, phrase) {
    if (!phrase) return false;
    if (/^[\x00-\x7F]+$/.test(phrase)) return (' ' + text + ' ').includes(' ' + phrase + ' ');
    return text.includes(phrase);
  }

  function videoId(url) {
    try {
      const u = new URL(url);
      if (u.protocol !== 'https:' && u.protocol !== 'http:') return null;
      const host = u.hostname.toLowerCase();
      let id = null;
      if (host === 'youtu.be' && /^\/[\w-]+\/?$/.test(u.pathname)) id = u.pathname.split('/')[1];
      else if (['youtube.com', 'www.youtube.com', 'm.youtube.com',
        'youtube-nocookie.com', 'www.youtube-nocookie.com'].includes(host)) {
        if (u.pathname === '/watch') id = u.searchParams.get('v');
        else {
          const m = u.pathname.match(/^\/(?:shorts|embed|live)\/([\w-]+)\/?$/);
          if (m) id = m[1];
        }
      }
      return id && /^[A-Za-z0-9_-]{11}$/.test(id) ? id : null;
    } catch (_) { return null; }
  }

  function rank(model, query) {
    const corpus = model.videos || {};
    const ids = (model.feed_ids || Object.keys(corpus)).filter(id => Object.hasOwn(corpus, id));
    const input = String(query || '').trim();
    const urls = input.match(/https?:\/\/[^\s<>]+/gi) || [];
    const matched_links = [...new Set(urls.map(url => videoId(url.replace(/[),.!?;]+$/, '')))
      .filter(id => id && Object.hasOwn(corpus, id)))];
    const plain = normalize(input.replace(/https?:\/\/[^\s<>]+/gi, ' '));
    if (!input) return {video_ids: ids, matched_video_ids: [], matched_links, reasons: {}};
    const direct = new Set(matched_links);
    const stop = new Set(['i', 'want', 'to', 'learn', 'about', 'the', 'and', '강의', '추천',
      '관련', '공부', '보고', '싶어요', '찾아줘', '추천해주세요']);
    const themes = aliases.filter(group => group.some(value => contains(plain, value)));
    const tokens = plain.split(' ').filter(value => value.length > 1 && !stop.has(value));
    const scored = [];
    for (const [index, id] of ids.entries()) {
      const row = corpus[id];
      const title = normalize(row.short_title || row.title);
      const searchable = (row.search_terms || []).map(normalize);
      const terms = new Set();
      const linked = direct.has(id);
      let score = linked ? 10000 - matched_links.indexOf(id) : 0;
      if (plain && contains(title, plain)) {
        score += 16;
        terms.add(plain);
      }
      for (const group of themes) {
        const titleHit = group.find(term => contains(title, term));
        const tagHit = group.find(term => searchable.some(text => contains(text, term)));
        if (titleHit || tagHit) {
          score += titleHit ? 9 : 4;
          terms.add(group.find(term => contains(plain, term)) || titleHit || tagHit);
        }
      }
      for (const term of new Set(tokens)) {
        if (contains(title, term)) {
          score += 5;
          terms.add(term);
        } else if (searchable.some(text => contains(text, term))) {
          score += 2;
          terms.add(term);
        }
      }
      if (score) scored.push({id, index, score, unavailable: row.availability !== 'available',
        reason: linked ? '입력한 YouTube 링크와 일치' : '일치한 관심사: ' + [...terms].slice(0, 3).join(', ')});
    }
    scored.sort((a, b) => b.score - a.score || Number(a.unavailable) - Number(b.unavailable) || a.index - b.index);
    const matched_video_ids = scored.map(row => row.id);
    return {video_ids: matched_video_ids, matched_video_ids, matched_links,
      reasons: Object.fromEntries(scored.map(row => [row.id, row.reason]))};
  }

  const api = Object.freeze({rank, videoId});
  if (typeof module === 'object' && module.exports) module.exports = api;
  if (global) global.CmuFeedRecommend = api;
})(typeof globalThis === 'object' ? globalThis : this);
