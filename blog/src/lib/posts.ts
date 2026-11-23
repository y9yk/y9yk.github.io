import type { MarkdownInstance } from 'astro';

type Metadata = {
  title: string;
  date: string;
  description: string;
  source: string;
  topic: string;
  excerpt?: boolean;
};

const files = import.meta.glob<MarkdownInstance<Metadata>>('../posts/*.md', { eager: true });
export const posts = Object.entries(files).map(([path, entry]) => {
  const slug = path.split('/').pop()!.replace(/\.md$/, '');
  return { slug, href: `/blog/${slug}/`, entry, ...entry.frontmatter };
}).sort((a, b) => Date.parse(b.date) - Date.parse(a.date));

export const dateLabel = (value: string) => new Intl.DateTimeFormat('ko-KR', {
  year: 'numeric', month: 'long', day: 'numeric', timeZone: 'Asia/Seoul'
}).format(new Date(value));
