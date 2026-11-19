'use strict';
function normalize(input) {
  return String(input ?? '').normalize('NFKC').toLowerCase().replace(/[‐‑‒–—−-]/g,' ').replace(/\s+/g,' ').trim();
}
function matches(course,{q='',track='all',status='all',progress='all',seen=new Set()}={}) {
  const done=seen.has(course.id);
  if (track!=='all' && course.track!==track) return false;
  if (status!=='all' && course.status!==status) return false;
  if ((progress==='done' && !done) || (progress==='open' && done)) return false;
  const hay=normalize(course.keywords);
  return normalize(q).split(' ').filter(Boolean).every(word=>hay.includes(word));
}
if (typeof module!=='undefined') module.exports={matches,normalize};
if (typeof document!=='undefined') {
  const key='cmu-cs-study:completed:v1';
  const form=document.querySelector('#filters');
  const fields=form.elements;
  const cards=[...document.querySelectorAll('[data-course]')];
  const validIds=new Set(cards.map(card=>card.dataset.id));
  let seen=new Set();
  try {
    const saved=JSON.parse(localStorage.getItem(key) || '[]');
    if (Array.isArray(saved)) seen=new Set(saved.filter(id=>validIds.has(id)));
  } catch {}
  function render() {
    let count=0;
    for (const card of cards) {
      const show=matches(card.dataset,{q:fields.q.value,track:fields.track.value,status:fields.status.value,progress:fields.progress.value,seen});
      card.hidden=!show;
      if (show) count++;
      const mark=card.querySelector('button[data-mark]');
      mark.setAttribute('aria-pressed',String(seen.has(card.dataset.id)));
      mark.textContent=seen.has(card.dataset.id)?'✓ 완료':'완료로 표시';
    }
    document.querySelector('#result-count').textContent=`${count}개 과목 · 완료 ${seen.size}/${cards.length}`;
    document.querySelector('#empty').hidden=count>0;
  }
  for (const card of cards) {
    card.querySelector('button[data-mark]').addEventListener('click',()=>{
      if (seen.has(card.dataset.id)) seen.delete(card.dataset.id);
      else seen.add(card.dataset.id);
      try {localStorage.setItem(key,JSON.stringify([...seen]));}
      catch {document.querySelector('#storage-note').hidden=false;}
      render();
      if(card.hidden) fields.progress.focus();
    });
  }
  function reset() {form.reset();render();}
  form.addEventListener('submit',evt=>{evt.preventDefault();render();});
  form.addEventListener('input',render);
  form.addEventListener('change',render);
  document.querySelectorAll('[data-reset]').forEach(button=>button.addEventListener('click',()=>{reset();fields.q.focus();}));
  document.querySelectorAll('a[data-route-course]').forEach(link=> {
    link.addEventListener('click',()=>{
      reset();
      document.getElementById(link.hash.slice(1))?.focus({preventScroll:true});
    });
  });
  document.documentElement.classList.add('is-enhanced');
  render();
}
