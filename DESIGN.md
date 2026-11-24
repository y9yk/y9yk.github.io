# Public design

- White background, locally hosted Inter, charcoal text, blue/teal accents.
- Typography: page titles 34–48px; section headings 25–26px; entry headings 19–20px; body 16px; secondary descriptions 14–15px; metadata and chart labels at least 12px. Body line height 1.8; readable text width around 68–72 characters.
- Sticky header: category navigation, quiet initial state, stable height across routes and scroll states; rule/shadow after scrolling. Respect reduced motion.
- Context actions use outlined buttons and small SVG icons rather than text-arrow glyphs. Keyboard focus stays visible.
- Home shows career-linked project summaries only. Projects opens a separate single-column summary index. Detailed articles stay in the private local review site. Missing company logos show no placeholder. Header: Home, Projects, Talks, Blog.
- Combined Research & Education retains public thesis/publication links. Talks contain only public titles and official external resources.
- Stats and data collection remain paused. No dashboard links or screens are published.
- Responsive charts use real container dimensions so labels remain readable. No horizontal page overflow at 360/390px.
- Detailed drafts and original working images remain outside the public source. Build/schema tests enforce this boundary.

- Home contact links exclude Blog, which lives in the shared header. Recent SK Telecom career projects render newest-first; canonical project chronology is retained in content data.

- Blog opens the Astro editorial index at /blog/. Each public post has its own static page with a reading layout and optional discussion.

## Blog (/blog/)

The blog is the same site, not a separate brand. It imports `assets/style.css` (Inter, color tokens, buttons, footer) and renders `src/header.html` unchanged, with Blog marked `aria-current`. Blog-only components live in `blog/src/styles/blog.css` and use only the shared tokens (`--ink`, `--muted`, `--line`, `--blue`, `--soft`).

- Language: post content and blog UI are Korean (`lang="ko"`, `word-break: keep-all`). The shared header stays English.
- Footer: name and RSS only; the shared header already links to the profile.
- Width: same 960px page and 36/24/20px gutters as the portfolio. No horizontal overflow at 360/390px.
- Home: hero (the one-line intro as a 22px heading, no “블로그” title) → one list of every post, newest first, with no section headings or featured card. Rows show date · reading time, title, summary, and a cover thumbnail on the right; summaries hide below 700px and thumbnails turn square.
- Covers: the post’s `cover` front matter or its first image. Cropped to 16:10 from the top, 1px `--line` border, 8px radius. Without an image, a plain soft tile. Never a stock or generated picture.
- Article: back link → meta line (date, reading time) → 40px title (32/28px on smaller screens) → muted lede. Body text 17px/1.85 (16px on phones) uses the full page content width. Tables scroll inside their own box. Figures center with a muted 13px caption.
- No table of contents, no likes, and no topic/category labels.
- Hover on post cards and previous/next cards underlines the title only; no color change.
- Comments: a bordered “댓글” panel after the body with one outlined “댓글 열기” button, using giscus (GitHub Discussions) with reactions off. It loads only after a click and never under DNT/GPC. No separate Discussions link.
- Previous/next: two outlined cards (title + two-line summary) after the article.
- Security: strict CSP with no inline script or style; client code lives in `blog/public/blog.js`. Post images are self-hosted under `blog/public/media/<slug>/`.

- Projects representatives must be actual service interfaces, never video thumbnails or architecture slides. Omit the preview when no publishable service screen exists. Video thumbnails remain valid only within Talks.

- Projects display newest-first: Marketing AX, Polaris, SmartBee, conversation search, REVIEWRO, review analytics, AIAS, targeting. Exactly six service previews are selected; Polaris and Marketing AX are text-only.
