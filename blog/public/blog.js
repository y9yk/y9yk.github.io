'use strict';

// Shared header: same scrolled state as the portfolio (assets/site.js).
const header = document.querySelector('.site-header');
if (header) {
  const update = () => header.classList.toggle('is-scrolled', window.scrollY > 20);
  window.addEventListener('scroll', update, { passive: true });
  update();
}

// Table of contents: collapsed by default on narrow screens, current section highlighted.
const toc = document.querySelector('[data-toc]');
if (toc) {
  const wide = window.matchMedia('(min-width: 1040px)');
  const sync = () => { toc.open = wide.matches; };
  sync();
  wide.addEventListener('change', sync);

  const links = new Map([...toc.querySelectorAll('a[href^="#"]')].map(link => [decodeURIComponent(link.hash.slice(1)), link]));
  const headings = [...links.keys()].map(id => document.getElementById(id)).filter(Boolean);
  const mark = id => {
    for (const [key, link] of links) {
      if (key === id) link.setAttribute('aria-current', 'true');
      else link.removeAttribute('aria-current');
    }
  };
  const locate = () => {
    const offset = (header?.offsetHeight ?? 0) + 32;
    let current = headings[0];
    for (const heading of headings) if (heading.getBoundingClientRect().top - offset <= 0) current = heading;
    if (current) mark(current.id);
  };
  let pending = false;
  window.addEventListener('scroll', () => {
    if (pending) return;
    pending = true;
    requestAnimationFrame(() => { pending = false; locate(); });
  }, { passive: true });
  locate();
  toc.addEventListener('click', event => {
    if (event.target.closest('a') && !wide.matches) toc.open = false;
  });
}

// Likes and comments: giscus loads only after an explicit click, never under DNT or GPC.
const container = document.querySelector('[data-discussion]');
const button = container?.querySelector('[data-open]');
const status = container?.querySelector('[data-status]');
if (container && button && status) {
  const privacy = navigator.globalPrivacyControl === true || ['1', 'yes'].includes(navigator.doNotTrack);
  if (privacy) {
    status.textContent = '브라우저의 개인정보 보호 설정(DNT/GPC)을 존중해 외부 위젯을 불러오지 않아요. GitHub Discussions에서 좋아요와 댓글을 남길 수 있어요.';
  } else {
    button.hidden = false;
    button.addEventListener('click', () => {
      button.disabled = true;
      status.textContent = '좋아요와 댓글을 불러오는 중입니다.';
      const script = document.createElement('script');
      script.src = 'https://giscus.app/client.js';
      script.async = true;
      script.crossOrigin = 'anonymous';
      const { repo, repoId, category, categoryId } = container.dataset;
      Object.assign(script.dataset, {
        repo, repoId, category, categoryId,
        mapping: 'pathname', strict: '1', reactionsEnabled: '1', emitMetadata: '0',
        inputPosition: 'top', lang: 'ko', theme: 'light', loading: 'lazy',
      });
      script.addEventListener('error', () => {
        script.remove();
        button.disabled = false;
        status.textContent = '불러오지 못했어요. 다시 시도하거나 GitHub Discussions에서 열어 주세요.';
      });
      script.addEventListener('load', () => {
        button.hidden = true;
        status.textContent = '위쪽 반응에서 👍를 누르면 좋아요가 남고, 아래에 댓글을 쓸 수 있어요.';
      });
      container.append(script);
    });
  }
}
