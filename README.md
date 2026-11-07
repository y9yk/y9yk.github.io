# Yong Ki Lee — public homepage

The public profile, short project summaries, research links, and Site pulse dashboard for [y9yk.github.io](https://y9yk.github.io/).

```sh
make serve
```

Open http://127.0.0.1:8000. Use `make serve PORT=8001` for another port. Stop with Ctrl+C. After editing content, run `make build` and refresh. Python 3.11+ and Node 18+ are required for checks; no package install is needed.

## Content boundaries

This repository contains only approved public profile information and brief project summaries. Detailed working materials live outside this repository. They must not be copied here, hidden in JSON fields, uploaded as assets, or committed to Git history. Project/talk detail routes are not generated. Tests reject detail fields and private document/image links in public content.

- `content/profile.json`: approved public content.
- `scripts/build.py` and `src/`: public page generation.
- `assets/`: local fonts, icons, and D3 dashboard.
- `services/analytics/`: anonymous aggregate collector.
- `guides/analytics.md`: metric definitions and collector operations.
- `DESIGN.md`: typography and interaction rules.

## Publication state

Projects are a selected subset of the career timeline and appear on the homepage only. Detail pages remain excluded. Stats, its public API, and new browser collection are paused pending a research-backed design review; existing aggregates remain on the collector volume. Empty For fun content is hidden.

Run `make check` before committing. GitHub Actions verifies, builds, and publishes `dist/` after main-branch pushes.
