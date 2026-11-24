import type { APIRoute } from 'astro';
import { posts } from '../lib/posts';
import { siteName } from '../lib/site';

const xml = (value: string) => value.replace(/[<>&'"]/g, c => ({ '<': '&lt;', '>': '&gt;', '&': '&amp;', "'": '&apos;', '"': '&quot;' })[c]!);

export const GET: APIRoute = ({ site }) => {
  const home = new URL('/blog/', site);
  const items = posts.map(post => {
    const link = new URL(post.href, site).href;
    return `<item><title>${xml(post.title)}</title><link>${link}</link><guid>${link}</guid><pubDate>${new Date(post.date).toUTCString()}</pubDate><category>${xml(post.topic)}</category><description>${xml(post.description)}</description></item>`;
  }).join('');
  const body = `<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>${xml(siteName)} · Blog</title><link>${home.href}</link><description>데이터 중심 서비스를 만들며 만난 문제와 AI를 쓰며 달라진 일을 기록합니다.</description><language>ko</language>${items}</channel></rss>`;
  return new Response(body, { headers: { 'Content-Type': 'application/rss+xml; charset=utf-8' } });
};
