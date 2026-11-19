'use strict';

const STEPS=['watch','practice','reflect'];
const LABELS={watch:'공식 강의 보기',practice:'미니 실습',reflect:'복습 노트'};
const OLD_KEY='cmu-cs-study:completed:v1';
const STUDY_KEY='cmu-cs-study:workspace:v2';

function normalize(input) {
  return String(input ?? '').normalize('NFKC').toLowerCase().replace(/[‐‑‒–—−-]/g,' ').replace(/\s+/g,' ').trim();
}

function matches(course,{q='',track='all',status='all',progress='all',seen=new Set(),started=new Set()}={}) {
  const done=seen.has(course.id);
  if (track!=='all' && course.track!==track) return false;
  if (status!=='all' && course.status!==status) return false;
  if ((progress==='done' && !done) || (progress==='open' && done) ||
      (progress==='started' && (!started.has(course.id) || done))) return false;
  return normalize(q).split(' ').filter(Boolean).every(word=>normalize(course.keywords).includes(word));
}

function videoIdFromHash(hash) {
  return /^#video-([A-Za-z0-9_-]{11})$/.exec(hash)?.[1]??null;
}

function videoEmbedUrl(vid, at=0) {
  if(!/^[A-Za-z0-9_-]{11}$/.test(vid)) return null;
  const q=new URLSearchParams({playsinline:'1',cc_load_policy:'1',cc_lang_pref:'en',hl:'ko'});
  if(Number.isInteger(at) && at>0) q.set('start',String(at));
  return `https://www.youtube-nocookie.com/embed/${vid}?${q}`;
}

function loadStudy(legacy, raw, courses) {
  const available=new Set(courses.filter(c=>c.status==='available').map(c=>c.id));
  const steps=Object.create(null), notes=Object.create(null), videos=Object.create(null);
  const legacyDone=new Set(Array.isArray(legacy)?legacy:[]);
  for (const id of available) {
    const src=raw?.steps?.[id];
    if (Array.isArray(src)) steps[id]=STEPS.filter(s=>src.includes(s));
    else if(legacyDone.has(id)) steps[id]=[...STEPS];
    const note=raw?.notes?.[id];
    if(typeof note==='string') notes[id]=note.slice(0,2000);
    if(/^[A-Za-z0-9_-]{11}$/.test(raw?.videos?.[id]??'')) videos[id]=raw.videos[id];
  }
  return {steps,notes,videos,last:available.has(raw?.last)?raw.last:null};
}

function courseCount(state, course) {
  return course.status==='available'?(state.steps[course.id]?.length??0):0;
}

function toggleStep(state, course, step) {
  if (course.status!=='available' || !STEPS.includes(step)) return false;
  const values=new Set(state.steps[course.id]??[]);
  if(values.has(step)) values.delete(step); else values.add(step);
  state.steps[course.id]=STEPS.filter(s=>values.has(s));
  state.last=course.id;
  return true;
}

function nextAction(courses,state) {
  const active=courses.filter(c=>c.status==='available' && courseCount(state,c)<STEPS.length);
  const last=active.find(c=>c.id===state.last);
  const course=last??active[0];
  if(!course) return null;
  return {id:course.id,step:STEPS.find(s=>!state.steps[course.id]?.includes(s)),resume:Boolean(last)};
}

if (typeof module!=='undefined') module.exports={matches,normalize,loadStudy,toggleStep,nextAction,courseCount,videoEmbedUrl,videoIdFromHash};

if (typeof document!=='undefined') {
  const get=id=>document.getElementById(id);
  const form=get('filters'), fields=form.elements;
  const cards=[...document.querySelectorAll('[data-course]')];
  const courses=cards.map(c=>c.dataset);
  const byId=new Map(cards.map(card=>[card.dataset.id,card]));
  const videoCards=[...document.querySelectorAll('[data-feed-video]')];
  const topics=[...document.querySelectorAll('[data-topic]')];
  const videoPicker=new Map();
  let active=null;
  let lastFeedLink=null;
  function read(key) {
    try {return JSON.parse(localStorage.getItem(key));} catch {return null;}
  }
  const legacy=read(OLD_KEY);
  const state=loadStudy(legacy,read(STUDY_KEY),courses);
  const released=courses.filter(c=>c.status==='available');
  function save() {
    try {
      localStorage.setItem(STUDY_KEY,JSON.stringify(state));
      const future=(Array.isArray(legacy)?legacy:[]).filter(id=>byId.get(id)?.dataset.status==='planned');
      localStorage.setItem(OLD_KEY,JSON.stringify([...released.filter(c=>courseCount(state,c)===3).map(c=>c.id),...future]));
    } catch {get('storage-note').hidden=false;}
  }

  function render() {
    const seen=new Set(released.filter(c=>courseCount(state,c)===3).map(c=>c.id));
    const started=new Set(released.filter(c=>courseCount(state,c)>0 || state.last===c.id || state.notes[c.id]).map(c=>c.id));
    const filters={q:fields.q.value,track:fields.track.value,status:fields.status.value,progress:fields.progress.value,seen,started};
    let visible=0;
    for(const card of cards) {
      const c=card.dataset;
      const show=matches(c,filters);
      card.hidden=!show && active?.card!==card;
      if(show) visible++;
      if(c.status!=='available') continue;
      card.querySelector('[data-course-progress]').textContent=`${courseCount(state,c)}/3 단계`;
      const watchMark=card.querySelector('[data-mark-watch]');
      const watched=Boolean(state.steps[c.id]?.includes('watch'));
      watchMark.setAttribute('aria-pressed',String(watched));
      watchMark.textContent=watched?'시청 완료 ✓':'시청 완료 표시';
      card.querySelectorAll('button[data-step-key]').forEach(button=>{
        const done=Boolean(state.steps[c.id]?.includes(button.dataset.stepKey));
        button.setAttribute('aria-pressed',String(done));
        button.textContent=done?'완료 ✓':'완료 표시';
      });
    }
    let videoCount=0;
    for(const video of videoCards) {
      const course=byId.get(video.dataset.feedCourse).dataset;
      video.hidden=!matches({...course,keywords:video.dataset.feedKeywords+' '+course.id+' '+course.id.replace('-','')},filters);
      if(!video.hidden) videoCount++;
    }
    document.querySelectorAll('[data-feed-shelf]').forEach(shelf=>{
      shelf.hidden=!shelf.querySelector('[data-feed-video]:not([hidden])');
    });
    topics.forEach(chip=>chip.setAttribute('aria-pressed',String(chip.dataset.topic===fields.track.value)));
    get('feed-empty').hidden=videoCount>0;
    get('feed-results').textContent=`강의 영상 ${videoCount}개`;
    get('video-query').value=fields.q.value;
    get('result-count').textContent=`${visible}개 과목`;
    get('empty').hidden=visible>0;
    const count=released.reduce((sum,c)=>sum+courseCount(state,c),0);
    get('study-progress').textContent=`${count} / ${released.length*3}단계`;
    get('study-meter').value=count;
    get('study-count').textContent=`완료한 공개 과목 ${seen.size} / ${released.length}`;
    const action=nextAction(courses,state), target=get('next-cta');
    if(!action) {
      get('next-label').textContent='공개 과목 완료';
      get('next-title').textContent='공개된 모든 과목을 마쳤어요.';
      get('next-step').textContent='노트를 다시 열거나 공개 예정 과목을 확인해 보세요.';
      target.href='#library';target.textContent='과목 라이브러리 보기';
    } else {
      const c=byId.get(action.id).dataset;
      get('next-label').textContent=action.resume?'이어서 학습':'추천 시작 과목';
      get('next-title').textContent=c.title;
      get('next-step').textContent=`${c.id} · 다음: ${LABELS[action.step]}`;
      target.href=`#step-${action.id}-${action.step}`;
      target.textContent=action.resume?'이어서 공부하기 →':'공부 시작하기 →';
    }
  }

  function closeWatch() {
    if(!active) return;
    active.controls.stop();
    active.card.classList.remove('watch-current');
    active=null;
    document.documentElement.classList.remove('watch-mode');
    render();
  }

  function selectTarget(hash) {
    const videoId=videoIdFromHash(hash);
    const target=get(hash.slice(1));
    if(videoId && target) {
      const card=target.closest('[data-course]');
      const controls=videoPicker.get(card);
      if(!controls) return;
      if(active?.card!==card) closeWatch();
      card.querySelector('[data-workspace]').open=true;
      active={card,controls};
      card.classList.add('watch-current');
      document.documentElement.classList.add('watch-mode');
      controls.choose(videoId);
      render();
      card.querySelector('[data-watch-title]').focus({preventScroll:true});
      window.scrollTo({top:0,behavior:'instant'});
      return;
    }
    const focusedStep=target && active?.card.contains(target) && target.matches('.step');
    if(!focusedStep) closeWatch();
    if(!target || !target.closest('[data-course]')) {
      if(hash==='#videos' && lastFeedLink && !lastFeedLink.closest('[hidden]')) lastFeedLink.focus({preventScroll:true});
      return;
    }
    const card=target.closest('[data-course]');
    form.reset();
    card.querySelector('[data-workspace]').open=true;
    if(card.dataset.status==='available') {state.last=card.dataset.id;save();}
    render();
    target.focus({preventScroll:true});
    target.scrollIntoView({block:'start'});
  }

  function go(hash) {
    if(location.hash!==hash) history.pushState(null,'',hash);
    selectTarget(hash);
  }

  for(const card of cards) {
    const c=card.dataset, workspace=card.querySelector('[data-workspace]');
    if(c.status!=='available') continue;
    workspace.addEventListener('toggle',()=>{
      if(workspace.open) {state.last=c.id;save();render();}
    });
    card.querySelectorAll('button[data-step-key]').forEach(button=>button.addEventListener('click',()=>{
      if(toggleStep(state,c,button.dataset.stepKey)) {save();render();if(card.hidden)fields.progress.focus();}
    }));
    card.querySelector('[data-mark-watch]').addEventListener('click',()=>{
      if(toggleStep(state,c,'watch')) {save();render();}
    });
    const note=card.querySelector('textarea');
    note.value=state.notes[c.id]??'';
    note.addEventListener('input',()=>{
      if(note.value) state.notes[c.id]=note.value;else delete state.notes[c.id];
      state.last=c.id;save();render();
    });
    const select=card.querySelector('select[data-video-select]');
    const playerBox=card.querySelector('[data-player]');
    const placeholder=playerBox.firstElementChild.cloneNode(true);
    const notes=[...card.querySelectorAll('[data-video-notes]')];
    function renderVideo() {
      const option=select.selectedOptions[0];
      const frame=playerBox.querySelector('iframe');
      playerBox.querySelector('[data-video-title]')?.replaceChildren(option.dataset.title);
      card.querySelector('[data-watch-title]').textContent=option.dataset.title;
      card.querySelectorAll('[data-queue-video]').forEach(row=>{
        if(row.dataset.queueVideo===select.value) row.setAttribute('aria-current','true');
        else row.removeAttribute('aria-current');
      });
      if(frame) frame.title=`${option.dataset.title} · CMU 공식 영상`;
      notes.forEach(n=>{n.hidden=n.dataset.videoNotes!==select.value;});
      const caption=card.querySelector('[data-cc-status]');
      caption.textContent = option.dataset.availability==='premiere'
        ? '확인 당시 첫 공개 대기 · 자막 미확인'
        : option.dataset.cc==='confirmed' ? '영어 CC 확인' : '자막 제공 여부 미확인';
    }
    function loadVideo(at=0, moveFocus=false) {
      const url=videoEmbedUrl(select.value,at);
      if(!url) return;
      let player=playerBox.querySelector('iframe');
      const isNew=!player;
      if(isNew) player=document.createElement('iframe');
      player.title=`${select.selectedOptions[0].dataset.title} · CMU 공식 영상`;
      player.allow='encrypted-media; picture-in-picture; fullscreen';
      player.referrerPolicy='strict-origin-when-cross-origin';
      player.allowFullscreen=true;
      player.src=url;
      if(isNew) playerBox.replaceChildren(player);
      if(moveFocus) player.focus();
      state.last=c.id;state.videos[c.id]=select.value;save();render();
    }
    if([...select.options].some(o=>o.value===state.videos[c.id])) select.value=state.videos[c.id];
    renderVideo();
    function choose(id) {
      if(![...select.options].some(option=>option.value===id)) return;
      const frame=playerBox.querySelector('iframe');
      const changed=Boolean(frame && !frame.src.includes('/embed/'+id+'?'));
      select.value=id;
      state.last=c.id;state.videos[c.id]=id;save();
      renderVideo();
      if(changed) loadVideo();
      render();
    }
    videoPicker.set(card,{choose,stop:()=>{
      if(playerBox.querySelector('iframe')) {
        playerBox.replaceChildren(placeholder.cloneNode(true));
        renderVideo();
      }
    }});
    select.addEventListener('change',()=>active?.card===card?go('#video-'+select.value):choose(select.value));
    playerBox.addEventListener('click',event=>{if(event.target.closest('button[data-play]')) loadVideo(0,true);});
    card.querySelectorAll('[data-timestamp]').forEach(button=>button.addEventListener('click',()=>loadVideo(Number(button.dataset.timestamp),true)));
  }
  function reset(){form.reset();render();}
  function runHeaderSearch(scroll) {
    fields.q.value=get('video-query').value;
    if(active) {
      closeWatch();
      history.pushState(null,'','#videos');
    }
    render();
    if(scroll) get('videos').scrollIntoView({block:'start'});
  }
  get('header-search').addEventListener('submit',e=>{e.preventDefault();runHeaderSearch(true);});
  get('video-query').addEventListener('input',()=>runHeaderSearch(false));
  topics.forEach(chip=>chip.addEventListener('click',()=>{
    fields.track.value=chip.dataset.topic;
    fields.status.value='all';
    fields.progress.value='all';
    render();
  }));
  form.addEventListener('submit',evt=>{evt.preventDefault();render();});
  form.addEventListener('input',render);
  form.addEventListener('change',render);
  document.querySelectorAll('[data-reset]').forEach(button=>button.addEventListener('click',()=>{reset();fields.q.focus();}));
  get('next-cta').addEventListener('click',evt=>{
    const hash=evt.currentTarget.hash;
    if(hash.startsWith('#step-')){evt.preventDefault();go(hash);}
  });
  function handleVideoLink(evt) {
    if(evt.ctrlKey || evt.metaKey || evt.shiftKey || evt.altKey || evt.button!==0) return;
    evt.preventDefault();
    if(evt.currentTarget.matches('.video-card-link')) lastFeedLink=evt.currentTarget;
    go(evt.currentTarget.hash);
  }
  document.querySelectorAll('.video-card-link,[data-queue-video]').forEach(link=>link.addEventListener('click',handleVideoLink));
  document.querySelectorAll('a[data-route-course],a[data-watch-step]').forEach(link=>link.addEventListener('click',evt=>{
    evt.preventDefault();go(link.hash);
  }));
  get('back-to-feed').addEventListener('click',evt=>{
    evt.preventDefault();go('#videos');get('videos').scrollIntoView({block:'start'});
  });
  // A thumbnail is visual context, not required to select a lecture.
  document.querySelectorAll('.video-thumb img').forEach(img=>{
    function hideMissing(){img.hidden=true;}
    img.addEventListener('error',hideMissing,{once:true});
    if(img.complete && img.naturalWidth===0) hideMissing();
  });
  window.addEventListener('hashchange',()=>selectTarget(location.hash));
  document.documentElement.classList.add('is-enhanced');
  render();
  selectTarget(location.hash);
}
