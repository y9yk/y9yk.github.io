import { defineConfig } from 'astro/config';

export default defineConfig({
  site: 'https://yongkilee.com',
  base: '/blog',
  trailingSlash: 'always',
  // Keep CSS and JS in files so the strict Content-Security-Policy needs no inline allowances.
  build: { inlineStylesheets: 'never' },
});
