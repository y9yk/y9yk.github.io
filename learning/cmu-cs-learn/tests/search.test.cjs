const {test}=require('node:test');
const assert=require('node:assert/strict');
const {matches,normalize}=require('../assets/study.js');
const c={keywords:'11-768 AI Agents 인공지능 에이전트 평가 모델',track:'agents',status:'available',id:'11-768'};
test('교과목 번호 표기 차이를 허용한다',()=>assert.equal(matches(c,{q:'１１ ７６８',track:'all'}),true));
test('한국어·영어 검색어를 함께 찾는다',()=>assert.equal(matches(c,{q:'agents 평가',track:'all'}),true));
test('검색어는 모두 존재해야 한다',()=>assert.equal(matches(c,{q:'agents 멀티모달',track:'all'}),false));
test('주제와 공개 상태를 동시에 필터한다',()=>{
 assert.equal(matches(c,{q:'',track:'agents',status:'available'}),true);
 assert.equal(matches(c,{q:'',track:'software',status:'available'}),false);
 assert.equal(matches(c,{q:'',track:'agents',status:'planned'}),false);
});
test('완료 과목을 실제 저장 상태로 거른다',()=>{
 assert.equal(matches(c,{q:'agents',track:'all',progress:'done',seen:new Set(['11-768'])}),true);
 assert.equal(matches(c,{q:'agents',track:'all',progress:'done',seen:new Set()}),false);
 assert.equal(matches(c,{q:'agents',track:'all',progress:'open',seen:new Set(['11-768'])}),false);
});
test('한글 조합 및 하이픈을 정규화한다',()=>assert.equal(normalize('한글–A   B'),'한글 a b'));
const {loadStudy,toggleWatched,nextAction,legacyStepCourse}=require('../assets/study.js');
const x='w05Mk2tjl_U', y='KQUtNJEzUxU', z='0nmhvgc5XOI';
const available={id:'11-768',status:'available',videoIds:[x,y]}, planned={id:'11-777',status:'planned',videoIds:[]};
const courses=[available,planned,{id:'17-645',status:'available',videoIds:[z]}];
test('기존 기록은 수정하지 않고 마지막 선택 영상만 이어본다',()=>{
 const legacy={last:available.id,steps:{[available.id]:['watch','practice']},notes:{[available.id]:'개인 노트'},videos:{[available.id]:y}};
 const snapshot=structuredClone(legacy);
 const s=loadStudy(null,legacy,courses);
 assert.deepEqual(legacy,snapshot);
 assert.deepEqual(Object.keys(s.watched),[]);
 assert.deepEqual(nextAction(courses,s),{id:available.id,video:y,resume:true});
});
test('개별 영상의 수동 시청 표시만 복원하고 독립적으로 해제한다',()=>{
 const s=loadStudy(null,null,courses);
 assert.equal(toggleWatched(s,available,x),true);
 assert.equal(toggleWatched(s,available,z),false);
 assert.equal(toggleWatched(s,planned,x),false);
 const restored=loadStudy(JSON.parse(JSON.stringify(s)),null,courses);
 assert.equal(restored.watched[x],true);
 assert.equal(restored.watched[y],undefined);
 assert.equal(toggleWatched(restored,available,x),true);
 assert.equal(restored.watched[x],undefined);
});
test('마지막 과목의 다음 미시청 강의를 우선하고 완료 후 다른 과목을 고른다',()=>{
 const s=loadStudy({last:available.id,videos:{[available.id]:x},watched:{[x]:true,invalid:true}},null,courses);
 assert.deepEqual(nextAction(courses,s),{id:available.id,video:y,resume:true});
 toggleWatched(s,available,y);
 assert.deepEqual(nextAction(courses,s),{id:'17-645',video:z,resume:false});
 toggleWatched(s,courses[2],z);
 assert.equal(nextAction(courses,s),null);
});
test('이전 3단계 해시는 모두 동일 과목 보기로 이어진다',()=>{
 for(const name of ['watch','practice','reflect']) assert.equal(legacyStepCourse('#step-11-768-'+name),'11-768');
 assert.equal(legacyStepCourse('#step-11-768-invalid'),null);
});
const {videoEmbedUrl}=require('../assets/study.js');
test('개별 영상은 올바른 ID와 공식 CC 파라미터만 허용한다',()=>{
 const url=new URL(videoEmbedUrl('w05Mk2tjl_U',42));
 assert.equal(url.hostname,'www.youtube-nocookie.com');
 assert.equal(url.pathname,'/embed/w05Mk2tjl_U');
 assert.equal(url.searchParams.get('cc_load_policy'),'1');
 assert.equal(url.searchParams.get('start'),'42');
 assert.equal(videoEmbedUrl('../escaped'),null);
 assert.equal(new URL(videoEmbedUrl('w05Mk2tjl_U',-1)).searchParams.has('start'),false);
});
const {videoIdFromHash}=require('../assets/study.js');
test('영상 위치의 링크만 정확한 ID로 파싱하고 과목 주소를 보존한다',()=>{
 assert.equal(videoIdFromHash('#video-w05Mk2tjl_U'),'w05Mk2tjl_U');
 assert.equal(videoIdFromHash('#course-11-768'),null);
 assert.equal(videoIdFromHash('#video-../outside'),null);
});
test('공식 플레이어 구간을 시작과 종료 모두로 제한한다',()=>{
 const bounded=new URL(videoEmbedUrl('0nmhvgc5XOI',0,300));
 assert.equal(bounded.searchParams.get('start'),'0');
 assert.equal(bounded.searchParams.get('end'),'300');
 assert.equal(bounded.searchParams.get('autoplay'),'1');
 assert.equal(videoEmbedUrl('0nmhvgc5XOI',300,300),null);
 assert.equal(videoEmbedUrl('0nmhvgc5XOI',300,280),null);
 assert.equal(videoEmbedUrl('0nmhvgc5XOI',-1,280),null);
 assert.equal(new URL(videoEmbedUrl('0nmhvgc5XOI',300)).searchParams.has('end'),false);
});
const {clipRoute,matchingClip}=require('../assets/study.js');
test('영문과 한글 학습 용어는 정확한 구간 링크를 찾는다',()=>{
 const clips=[{start:'2692',keywords:'Shuffle Combiner 셔플 컴바이너 로컬 집계'}];
 assert.equal(matchingClip(clips,'combiner')?.start,'2692');
 assert.equal(matchingClip(clips,'컴바이너')?.start,'2692');
 assert.equal(matchingClip(clips,'map reduce'),undefined);
 assert.deepEqual(clipRoute('#video-KQUtNJEzUxU-clip-2692'),{id:'KQUtNJEzUxU',start:'2692'});
 assert.equal(clipRoute('#video-KQUtNJEzUxU-clip-../a'),null);
});
const {topView}=require('../assets/study.js');
test('탐색·과목·내 학습을 별도의 화면으로 분리하고 기존 링크를 유지한다',()=>{
 assert.equal(topView(''),'browse');
 assert.equal(topView('#videos'),'browse');
 assert.equal(topView('#library'),'catalog');
 assert.equal(topView('#paths'),'catalog');
 assert.equal(topView('#step-11-768-practice'),'catalog');
 assert.equal(topView('#study-next'),'learn');
 assert.equal(topView('#video-KQUtNJEzUxU-clip-2692'),'watch');
});
test('나중에 볼 목록은 검증된 공식 영상만 저장하고 기존 시청 완료는 유지한다',()=>{
 const {toggleSaved}=require('../assets/study.js');
 const s=loadStudy({watched:{[x]:true},saved:{[y]:true,invalid:true}},null,courses);
 assert.deepEqual(Object.keys(s.saved),[y]);
 assert.equal(toggleSaved(s,available,z),false);
 assert.equal(toggleSaved(s,available,x),true);
 assert.equal(s.watched[x],true);
 assert.equal(toggleSaved(s,available,y),true);
 assert.deepEqual(Object.keys(s.saved),[x]);
});
