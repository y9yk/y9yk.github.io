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
const {loadStudy,toggleStep,nextAction,courseCount}=require('../assets/study.js');
const available={id:'11-768',status:'available'}, planned={id:'11-777',status:'planned'};
const courses=[available,planned,{id:'17-645',status:'available'}];
test('기존 과목 완료 기록을 체크리스트에 보존한다',()=>{
 const state=loadStudy(['11-768','unknown'],null,courses);
 assert.equal(courseCount(state,available),3);
 assert.equal(state.last,null);
});
test('다시 열면 마지막 과목의 다음 미완료 활동으로 이어간다',()=>{
 const state=loadStudy([],null,courses);
 toggleStep(state,available,'watch');
 const restored=loadStudy([],JSON.parse(JSON.stringify(state)),courses);
 assert.deepEqual(nextAction(courses,restored),{id:'11-768',step:'practice',resume:true});
});
test('공개 예정 과목을 완료하거나 이어보기 대상으로 만들지 않는다',()=>{
 const state=loadStudy([], {last:'11-777',steps:{'11-777':['watch'],'unknown':['practice']}},courses);
 assert.equal(toggleStep(state,planned,'watch'),false);
 assert.equal(courseCount(state,planned),0);
 assert.deepEqual(nextAction(courses,state),{id:'11-768',step:'watch',resume:false});
});
test('완료한 과목은 다음 공개 과목을 추천하며 모두 완료하면 종료한다',()=>{
 const state=loadStudy(['11-768'],{last:'11-768'},courses);
 assert.deepEqual(nextAction(courses,state),{id:'17-645',step:'watch',resume:false});
 for(const k of ['watch','practice','reflect']) toggleStep(state,courses[2],k);
 assert.equal(nextAction(courses,state),null);
});
test('노트는 유효한 과목만 보존하고 브라우저 입력 길이를 지킨다',()=>{
 const restored=loadStudy([],JSON.parse(JSON.stringify({last:'11-768',steps:{'11-768':['practice','practice','bogus']},notes:{'11-768':'가'.repeat(2200),'11-777':'not available','unknown':'no'}})),courses);
 assert.equal(restored.notes['11-768'].length,2000);
 assert.deepEqual(Object.keys(restored.notes),['11-768']);
 assert.equal(courseCount(restored,available),1);
 assert.deepEqual(nextAction(courses,restored),{id:'11-768',step:'watch',resume:true});
});
test('도메인 내 학습 경로 변경 뒤에도 이전 단계·노트·선택 영상 데이터를 보존한다',()=>{
 const old={last:'11-768',steps:{'11-768':['watch']},notes:{'11-768':'개인 노트'},videos:{'11-768':'w05Mk2tjl_U'}};
 const st=loadStudy([],JSON.parse(JSON.stringify(old)),courses);
 assert.equal(st.notes['11-768'],'개인 노트');
 assert.equal(st.videos['11-768'],'w05Mk2tjl_U');
 assert.deepEqual(nextAction(courses,st),{id:'11-768',step:'practice',resume:true});
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
