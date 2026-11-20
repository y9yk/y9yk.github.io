'use strict';

const LEGACY_STUDY_KEY='cmu-cs-study:workspace:v2';
const VIEWING_KEY='cmu-cs-study:viewing:v3';

function legacyStepCourse(hash) {
  return /^#step-(\d{2}-\d{3})-(?:watch|practice|reflect)$/.exec(hash)?.[1]??null;
}

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

function clipRoute(hash) {
  const match=/^#video-([A-Za-z0-9_-]{11})-clip-(0|[1-9]\d{0,8})$/.exec(hash);
  return match?{id:match[1],start:match[2]}:null;
}

function matchingClip(clips,query) {
  const terms=normalize(query).split(' ').filter(Boolean);
  if(!terms.length) return undefined;
  return clips.find(clip=>terms.every(term=>normalize(clip.keywords).includes(term)));
}

function topView(hash) {
  if(videoIdFromHash(hash) || clipRoute(hash)) return 'watch';
  if(hash==='#study-next') return 'learn';
  if(hash==='#library' || hash==='#paths' || /^#(?:course|step)-/.test(hash)) return 'catalog';
  return 'browse';
}

function videoEmbedUrl(vid, at=0, end=null) {
  if(!/^[A-Za-z0-9_-]{11}$/.test(vid)) return null;
  const q=new URLSearchParams({playsinline:'1',cc_load_policy:'1',cc_lang_pref:'en',hl:'ko'});
  if(end!==null) {
    if(!Number.isSafeInteger(at) || !Number.isSafeInteger(end) || at<0 || end<=at) return null;
    q.set('start',String(at));q.set('end',String(end));q.set('autoplay','1');
  } else if(Number.isSafeInteger(at) && at>0) q.set('start',String(at));
  return `https://www.youtube-nocookie.com/embed/${vid}?${q}`;
}

function loadStudy(raw, legacy, courses) {
  const available=courses.filter(c=>c.status==='available');
  const last=(raw??legacy)?.last;
  const watched=Object.create(null), videos=Object.create(null);
  for(const c of available) {
    const vid=(raw??legacy)?.videos?.[c.id];
    if(c.videoIds.includes(vid)) videos[c.id]=vid;
    for(const id of c.videoIds) if(raw?.watched?.[id]===true) watched[id]=true;
  }
  return {watched,videos,last:available.some(c=>c.id===last)?last:null};
}

function courseCount(state, course) {
  return course.videoIds.filter(id=>state.watched[id]).length;
}

function toggleWatched(state, course, video) {
  if(course.status!=='available' || !course.videoIds.includes(video)) return false;
  if(state.watched[video]) delete state.watched[video];
  else state.watched[video]=true;
  state.last=course.id;
  state.videos[course.id]=video;
  return true;
}

function nextAction(courses,state) {
  const active=courses.filter(c=>c.status==='available' && courseCount(state,c)<c.videoIds.length);
  const last=active.find(c=>c.id===state.last);
  const course=last??active[0];
  if(!course) return null;
  const selected=state.videos[course.id];
  const video=selected&&!state.watched[selected]?selected:course.videoIds.find(id=>!state.watched[id]);
  return {id:course.id,video,resume:Boolean(last)};
}

if (typeof module!=='undefined') module.exports={matches,normalize,loadStudy,toggleWatched,nextAction,courseCount,videoEmbedUrl,videoIdFromHash,clipRoute,matchingClip,topView,legacyStepCourse};

if (typeof document!=='undefined') {
  const get=id=>document.getElementById(id);
  const form=get('filters'), fields=form.elements;
  const cards=[...document.querySelectorAll('[data-course]')];
  const courses=cards.map(card=>({
    ...card.dataset, videoIds:[...card.querySelectorAll('[data-video-option]')].map(o=>o.value)
  }));
  const courseData=new Map(courses.map(c=>[c.id,c]));
  const byId=new Map(cards.map(card=>[card.dataset.id,card]));
  const videoCards=[...document.querySelectorAll('[data-feed-video]')];
  const topics=[...document.querySelectorAll('[data-topic]')];
  const videoPicker=new Map();
  const clipPanels=new Map([...document.querySelectorAll('[data-video-brief]')].map(panel=>[
    panel.dataset.videoBrief,[...panel.querySelectorAll('[data-clip-start]')].map(button=>({
      start:button.dataset.clipStart,keywords:button.dataset.clipKeywords,button
    }))
  ]));
  let active=null;
  let lastFeedLink=null;
  function read(key) {
    try {return JSON.parse(localStorage.getItem(key));} catch {return null;}
  }
  const state=loadStudy(read(VIEWING_KEY),read(LEGACY_STUDY_KEY),courses);
  const released=courses.filter(c=>c.status==='available');
  const totalVideos=released.reduce((sum,c)=>sum+c.videoIds.length,0);
  function save() {
    try {localStorage.setItem(VIEWING_KEY,JSON.stringify(state));}
    catch {get('storage-note').hidden=false;}
  }

  function render() {
    const seen=new Set(released.filter(c=>courseCount(state,c)===c.videoIds.length).map(c=>c.id));
    const started=new Set(released.filter(c=>courseCount(state,c)>0 || state.videos[c.id]).map(c=>c.id));
    const filters={q:fields.q.value,track:fields.track.value,status:fields.status.value,progress:fields.progress.value,seen,started};
    let visible=0;
    for(const card of cards) {
      const c=courseData.get(card.dataset.id);
      const show=matches(c,filters);
      card.hidden=!show && active?.card!==card;
      if(show) visible++;
      if(c.status!=='available') continue;
      const count=courseCount(state,c);
      card.querySelector('[data-course-progress]').textContent=count?`${count}/${c.videoIds.length}개 시청`:'';
      const watchMark=card.querySelector('[data-mark-watch]');
      const watched=Boolean(state.watched[card.querySelector('[data-video-select]').value]);
      watchMark.setAttribute('aria-pressed',String(watched));
      watchMark.textContent=watched?'이 영상 시청 완료 ✓':'이 영상 시청 완료 표시';
    }
    let videoCount=0;
    for(const video of videoCards) {
      const course=byId.get(video.dataset.feedCourse).dataset;
      video.hidden=!matches({...course,keywords:video.dataset.feedKeywords+' '+course.id+' '+course.id.replace('-','')},filters);
      const vid=video.dataset.feedVideo;
      const clip=video.hidden?undefined:matchingClip(clipPanels.get(vid)??[],filters.q);
      video.querySelector('.video-card-link').hash=clip?`#video-${vid}-clip-${clip.start}`:`#video-${vid}`;
      if(!video.hidden) videoCount++;
    }
    document.querySelectorAll('[data-feed-shelf]').forEach(shelf=>{
      shelf.hidden=!shelf.querySelector('[data-feed-video]:not([hidden])');
    });
    topics.forEach(chip=>chip.setAttribute('aria-pressed',String(chip.dataset.topic===fields.track.value)));
    get('feed-empty').hidden=videoCount>0;
    get('course-discovery').hidden=Boolean(normalize(filters.q)) || filters.track!=='all';
    get('feed-results').textContent=`강의 영상 ${videoCount}개`;
    get('video-query').value=fields.q.value;
    get('result-count').textContent=`${visible}개 과목`;
    get('empty').hidden=visible>0;
    const count=released.reduce((sum,c)=>sum+courseCount(state,c),0);
    get('study-progress').textContent=`${count} / ${totalVideos}개 영상`;
    get('study-meter').value=count;
    get('study-count').textContent=`전체 강의를 시청 완료한 과목 ${seen.size} / ${released.length}`;
    const action=nextAction(courses,state), target=get('next-cta');
    if(!action) {
      get('next-label').textContent='공개 과목 완료';
      get('next-title').textContent='공개된 모든 과목을 마쳤어요.';
      get('next-step').textContent='강의 노트를 다시 읽거나 공개 예정 과목을 확인해 보세요.';
      target.href='#library';target.textContent='과목 라이브러리 보기';
    } else {
      const c=byId.get(action.id).dataset;
      get('next-label').textContent=action.resume?'이어서 학습':'추천 시작 과목';
      get('next-title').textContent=c.title;
      get('next-step').textContent=`${c.id} · ${byId.get(c.id).querySelector(`[data-video-option="${action.video}"]`).dataset.title}`;
      target.href=`#video-${action.video}`;
      target.textContent=action.resume?'이어서 공부하기 →':'공부 시작하기 →';
    }
  }

  function showView(view) {
    document.documentElement.dataset.topView=view;
    document.querySelectorAll('[data-top-view]').forEach(link=>{
      if(link.dataset.topView===view) link.setAttribute('aria-current','page');
      else link.removeAttribute('aria-current');
    });
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
    const route=clipRoute(hash);
    const videoId=route?.id??videoIdFromHash(hash);
    const legacyId=legacyStepCourse(hash);
    const target=get(videoId?`video-${videoId}`:legacyId?`course-${legacyId}`:hash.slice(1));
    if(videoId && target) {
      const card=target.closest('[data-course]');
      const controls=videoPicker.get(card);
      if(!controls) return;
      if(active?.card!==card) closeWatch();
      card.querySelector('[data-workspace]').open=true;
      active={card,controls};
      card.classList.add('watch-current');
      document.documentElement.classList.add('watch-mode');
      showView('watch');
      controls.choose(videoId);
      controls.tab(route?'clips':'notes');
      render();
      // Deep links reveal verified clips but never start playback.
      const clip=route&&clipPanels.get(videoId)?.find(entry=>entry.start===route.start)?.button;
      if(clip) {
        const disclosure=clip.closest('details.more-clips');
        if(disclosure) disclosure.open=true;
        clip.focus({preventScroll:true});
        clip.scrollIntoView({block:'center'});
      } else {
        card.querySelector('[data-watch-title]').focus({preventScroll:true});
        window.scrollTo({top:0,behavior:'instant'});
      }
      return;
    }
    closeWatch();
    const view=topView(hash);
    showView(view==='watch'?'browse':view);
    if(!target || !target.closest('[data-course]')) {
      if(hash==='#videos' && lastFeedLink && !lastFeedLink.closest('[hidden]')) lastFeedLink.focus({preventScroll:true});
      if(hash==='#paths') target?.scrollIntoView({block:'start'});
      else if(['#library','#study-next'].includes(hash)) window.scrollTo({top:0,behavior:'instant'});
      return;
    }
    const card=target.closest('[data-course]');
    form.reset();
    card.querySelector('[data-workspace]').open=true;
    render();
    target.focus({preventScroll:true});
    target.scrollIntoView({block:'start'});
  }

  function go(hash) {
    if(location.hash!==hash) history.pushState(null,'',hash);
    selectTarget(hash);
  }

  for(const card of cards) {
    const c=courseData.get(card.dataset.id);
    if(c.status!=='available') continue;
    const select=card.querySelector('select[data-video-select]');
    card.querySelector('[data-mark-watch]').addEventListener('click',()=>{
      if(toggleWatched(state,c,select.value)) {save();render();}
    });
    const playerBox=card.querySelector('[data-player]');
    const placeholder=playerBox.firstElementChild.cloneNode(true);
    const notes=[...card.querySelectorAll('[data-video-notes]')];
    const extraVideoSections=[...card.querySelectorAll('[data-video-overview],[data-video-sources]')];
    const tabs=[...card.querySelectorAll('[data-study-tab]')];
    function chooseTab(key, focus=false) {
      tabs.forEach(tab=>{
        const selected=tab.dataset.studyTab===key;
        tab.setAttribute('aria-selected',String(selected));
        tab.tabIndex=selected?0:-1;
        get(tab.getAttribute('aria-controls')).hidden=!selected;
        if(selected && focus) tab.focus();
      });
    }
    tabs.forEach((tab,i)=>{
      tab.addEventListener('click',()=>chooseTab(tab.dataset.studyTab));
      tab.addEventListener('keydown',event=>{
        const motion={ArrowLeft:-1,ArrowRight:1}[event.key];
        const next=motion?tabs[(i+motion+tabs.length)%tabs.length]:event.key==='Home'?tabs[0]:event.key==='End'?tabs.at(-1):null;
        if(next){event.preventDefault();chooseTab(next.dataset.studyTab,true);}
      });
    });
    chooseTab('notes');
    const briefings=[...card.querySelectorAll('[data-video-brief]')];
    const clipButtons=[...card.querySelectorAll('[data-clip-start]')];
    const clipStatus=card.querySelector('[data-active-clip]');
    const fullVideo=card.querySelector('[data-full-video]');
    function renderClip(button=null) {
      clipButtons.forEach(b=>b.setAttribute('aria-pressed',String(button===b)));
      clipStatus.hidden=fullVideo.hidden=!button;
      clipStatus.textContent=button?`재생 요청 · ${button.dataset.clipTitle} · ${button.dataset.clipLabel}`:'';
    }
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
      extraVideoSections.forEach(n=>{n.hidden=(n.dataset.videoOverview??n.dataset.videoSources)!==select.value;});
      briefings.forEach(n=>{n.hidden=n.dataset.videoBrief!==select.value;});
      const caption=card.querySelector('[data-cc-status]');
      caption.textContent = option.dataset.availability==='premiere'
        ? '확인 당시 첫 공개 대기 · 자막 미확인'
        : option.dataset.cc==='confirmed' ? '영어 CC 확인' : '자막 제공 여부 미확인';
    }
    function loadVideo(at=0, moveFocus=false, end=null, clipButton=null) {
      const url=videoEmbedUrl(select.value,at,end);
      if(!url) return;
      let player=playerBox.querySelector('iframe');
      const isNew=!player;
      if(isNew) player=document.createElement('iframe');
      player.title=`${select.selectedOptions[0].dataset.title} · CMU 공식 영상`;
      player.allow=(end===null?'':'autoplay; ')+'encrypted-media; picture-in-picture; fullscreen';
      player.referrerPolicy='strict-origin-when-cross-origin';
      player.allowFullscreen=true;
      player.src=url;
      if(isNew) playerBox.replaceChildren(player);
      renderClip(clipButton);
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
    videoPicker.set(card,{choose,tab:chooseTab,stop:()=>{
      if(playerBox.querySelector('iframe')) {
        playerBox.replaceChildren(placeholder.cloneNode(true));
        renderClip();renderVideo();
      }
    }});
    select.addEventListener('change',()=>active?.card===card?go('#video-'+select.value):choose(select.value));
    playerBox.addEventListener('click',event=>{if(event.target.closest('button[data-play]')) loadVideo(0,true);});
    card.querySelectorAll('[data-timestamp]').forEach(button=>button.addEventListener('click',()=>loadVideo(Number(button.dataset.timestamp),true)));
    clipButtons.forEach(button=>button.addEventListener('click',()=>{
      const panel=button.closest('[data-video-brief]');
      if(panel.dataset.videoBrief!==select.value) return;
      loadVideo(Number(button.dataset.clipStart),true,Number(button.dataset.clipEnd),button);
      playerBox.scrollIntoView({block:'start'});
    }));
    fullVideo.addEventListener('click',()=>loadVideo(0,true));
  }
  function reset(){form.reset();render();}
  function runHeaderSearch(scroll) {
    fields.q.value=get('video-query').value;
    if(document.documentElement.dataset.topView!=='browse') go('#videos');
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
    if(videoIdFromHash(hash)){evt.preventDefault();go(hash);}
  });
  function handleVideoLink(evt) {
    if(evt.ctrlKey || evt.metaKey || evt.shiftKey || evt.altKey || evt.button!==0) return;
    evt.preventDefault();
    if(evt.currentTarget.matches('.video-card-link')) lastFeedLink=evt.currentTarget;
    go(evt.currentTarget.hash);
  }
  document.querySelectorAll('.video-card-link,[data-queue-video]').forEach(link=>link.addEventListener('click',handleVideoLink));
  document.querySelectorAll('a[data-route-course]').forEach(link=>link.addEventListener('click',evt=>{
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
