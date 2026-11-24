import type { MarkdownInstance } from 'astro';

type Metadata = {
  title: string;
  date: string;
  description: string;
  topic: string;
  source?: string;
  cover?: string;
  coverAlt?: string;
};

const files = import.meta.glob<MarkdownInstance<Metadata>>('../posts/*.md', { eager: true });

const firstImage = (markdown: string) =>
  markdown.match(/<img[^>]*\ssrc="([^"]+)"/)?.[1] ?? markdown.match(/!\[[^\]]*\]\(([^)\s]+)/)?.[1];

// Korean prose reads at roughly 500 characters per minute.
const minutes = (markdown: string) => {
  const text = markdown.replace(/<[^>]+>/g, ' ').replace(/[#>*_`|\-\[\]()]/g, ' ').replace(/\s+/g, '');
  return Math.max(1, Math.round(text.length / 500));
};

export const posts = Object.entries(files).map(([path, entry]) => {
  const slug = path.split('/').pop()!.replace(/\.md$/, '');
  const raw = entry.rawContent();
  return {
    slug,
    href: `/blog/${slug}/`,
    entry,
    ...entry.frontmatter,
    cover: entry.frontmatter.cover ?? firstImage(raw),
    readingMinutes: minutes(raw),
  };
}).sort((a, b) => Date.parse(b.date) - Date.parse(a.date));

export type Post = (typeof posts)[number];

export const topics = [...new Set(posts.map(post => post.topic))];

export const dateLabel = (value: string) => new Intl.DateTimeFormat('ko-KR', {
  year: 'numeric', month: 'long', day: 'numeric', timeZone: 'Asia/Seoul'
}).format(new Date(value));
