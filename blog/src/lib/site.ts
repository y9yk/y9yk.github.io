// The blog renders the portfolio's own header partial so both sites share one navigation component.
import partialSource from '../../../src/header.html?raw';
import profile from '../../../content/profile.json';

const partial = partialSource.trim();

export const siteName: string = profile.name;

export const siteHeader = partial
  .replaceAll('{{prefix}}', '/')
  .replace('{{fun_link}}', profile.for_fun?.length ? '<a href="/#for-fun">For fun</a>' : '')
  .replace('<a href="/blog/">Blog</a>', '<a href="/blog/" aria-current="page">Blog</a>');

export const policy = [
  "default-src 'none'",
  "script-src 'self' https://giscus.app",
  "style-src 'self' https://giscus.app",
  "font-src 'self'",
  "img-src 'self'",
  "frame-src https://giscus.app",
  "connect-src 'none'",
  "base-uri 'none'",
  "form-action 'none'",
].join('; ');
