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

- Blog opens /blog/ under the same shared header. Its iframe points only to https://y9yk.bearblog.dev/blog/; the route CSP allows that frame origin and keeps the outer navigation on this site. Browser verification is authoritative: the CLI returned a different 404 response, while the normal browser returned 200 with ALLOWALL.

- Projects representatives must be actual service interfaces, never video thumbnails or architecture slides. Omit the preview when no publishable service screen exists. Video thumbnails remain valid only within Talks.

- Projects display newest-first: Marketing AX, Polaris, SmartBee, conversation search, REVIEWRO, review analytics, AIAS, targeting. Exactly six service previews are selected; Polaris and Marketing AX are text-only.

- Blog uses one viewport-height frame without an outer footer/min-height overflow. Its right scrollbar rail is clipped by a wrapper; native inner scrolling remains enabled for long posts.
