'use strict';

for (const image of document.querySelectorAll('img')) {
  const handleError = () => { image.hidden = true; };
  image.addEventListener('error', handleError);
  if (image.complete && image.naturalWidth === 0) handleError();
}

const header = document.querySelector('.site-header');
if (header) {
  const updateHeader = () => header.classList.toggle('is-scrolled', window.scrollY > 20);
  window.addEventListener('scroll', updateHeader, { passive: true });
  updateHeader();
}
