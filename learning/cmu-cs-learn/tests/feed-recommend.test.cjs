const test = require('node:test');
const assert = require('node:assert/strict');
const {rank, videoId} = require('../assets/feed-recommend.js');
const model = {
  feed_ids: ['oPSMMckx3eY', 'KQUtNJEzUxU'],
  videos: {
    oPSMMckx3eY: {short_title:'Programming Basics', search_terms:['Python','프로그래밍 기초'], availability:'available'},
    KQUtNJEzUxU: {short_title:'Map-Reduce and Spark', search_terms:['MapReduce','분산 처리','Spark','셔플'], availability:'available'},
  }
};

test('Korean natural-language and English aliases rank the same verified lesson', () => {
  assert.equal(rank(model, '파이썬으로 시작하고 싶어요').video_ids[0], 'oPSMMckx3eY');
  assert.equal(rank(model, 'I want to learn Python').video_ids[0], 'oPSMMckx3eY');
  const result = rank(model, '스파크랑 맵리듀스 강의');
  assert.deepEqual(result.video_ids, ['KQUtNJEzUxU']);
  assert.match(result.reasons.KQUtNJEzUxU, /스파크|맵리듀스/);
});

test('exact local URL match beats lexical cues, unknown URLs and blank differ', () => {
  const result = rank(model, '파이썬 https://youtu.be/KQUtNJEzUxU?t=60');
  assert.deepEqual(result.matched_links, ['KQUtNJEzUxU']);
  assert.deepEqual(result.video_ids, ['KQUtNJEzUxU', 'oPSMMckx3eY']);
  assert.equal(result.reasons.KQUtNJEzUxU, '입력한 YouTube 링크와 일치');
  for (const query of ['오페라', 'https://www.youtube.com/watch?v=abcdefghijk', 'https://youtube.com.evil.test/watch?v=KQUtNJEzUxU']) {
    assert.deepEqual(rank(model, query).video_ids, []);
  }
  assert.deepEqual(rank(model, '').video_ids, model.feed_ids);
  assert.deepEqual(rank(model, '').matched_video_ids, []);
});

test('parser accepts only exact supported public hosts and no non-http URLs', () => {
  assert.equal(videoId('https://m.youtube.com/watch?v=KQUtNJEzUxU'), 'KQUtNJEzUxU');
  assert.equal(videoId('https://www.youtube-nocookie.com/embed/KQUtNJEzUxU'), 'KQUtNJEzUxU');
  assert.equal(videoId('https://www.youtube.com/shorts/KQUtNJEzUxU'), 'KQUtNJEzUxU');
  assert.equal(videoId('https://www.youtube.com@evil.test/watch?v=KQUtNJEzUxU'), null);
  assert.equal(videoId('javascript:alert("https://youtu.be/KQUtNJEzUxU")'), null);
});
