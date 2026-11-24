'use strict';

// Shared header: same scrolled state as the portfolio (assets/site.js).
const header = document.querySelector('.site-header');
if (header) {
  const update = () => header.classList.toggle('is-scrolled', window.scrollY > 20);
  window.addEventListener('scroll', update, { passive: true });
  update();
}

// Comments: giscus loads only after an explicit click, never under DNT or GPC.
const container = document.querySelector('[data-discussion]');
const button = container?.querySelector('[data-open]');
const status = container?.querySelector('[data-status]');
if (container && button && status) {
  const privacy = navigator.globalPrivacyControl === true || ['1', 'yes'].includes(navigator.doNotTrack);
  if (privacy) {
    status.textContent = '브라우저의 개인정보 보호 설정(DNT/GPC)을 존중해 댓글 위젯을 불러오지 않아요.';
  } else {
    button.hidden = false;
    button.addEventListener('click', () => {
      button.disabled = true;
      status.textContent = '댓글을 불러오는 중입니다.';
      const script = document.createElement('script');
      script.src = 'https://giscus.app/client.js';
      script.async = true;
      script.crossOrigin = 'anonymous';
      const { repo, repoId, category, categoryId } = container.dataset;
      Object.assign(script.dataset, {
        repo, repoId, category, categoryId,
        mapping: 'pathname', strict: '1', reactionsEnabled: '0', emitMetadata: '0',
        inputPosition: 'top', lang: 'ko', theme: 'light', loading: 'lazy',
      });
      script.addEventListener('error', () => {
        script.remove();
        button.disabled = false;
        status.textContent = '댓글을 불러오지 못했어요. 다시 시도해 주세요.';
      });
      script.addEventListener('load', () => {
        button.hidden = true;
        status.textContent = 'GitHub 계정으로 로그인하면 댓글을 쓸 수 있어요.';
      });
      container.append(script);
    });
  }
}
