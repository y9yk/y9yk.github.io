# 블로그

Node.js 24 환경에서 저장소 루트의 `make serve`를 실행하면 포트폴리오와 블로그를 함께 볼 수 있다. 블로그만 편집할 때는 이 폴더에서 `npm ci` 후 `npm run dev`를 실행하고 터미널 주소의 `/blog/`를 연다. 이 경우 헤더 로고처럼 포트폴리오의 `/assets/` 파일은 보이지 않는다.

## 글 추가

공개할 글은 `src/posts/<slug>.md`에 추가한다. 글의 slug는 주소(`/blog/<slug>/`)이자 댓글 스레드의 식별자이므로 발행한 뒤에는 바꾸지 않는다.

```yaml
---
title: "글 제목"
date: "2026-11-24T09:00:00+09:00"   # 시간대 포함 ISO 문자열
description: "목록과 검색 결과에 쓰는 한두 문장 요약"
topic: "에이전트 운영"
cover: "/blog/media/<slug>/cover.png"   # 선택. 없으면 본문 첫 이미지
source: "https://y9yk.bearblog.dev/<slug>/"   # 선택. Bear Blog에서 옮긴 글만
---
```

- 본문의 `##` 제목이 목차가 된다. 두 개 이상일 때 목차가 표시된다.
- 이미지는 `public/media/<slug>/`에 두고 `/blog/media/<slug>/파일명`으로 참조한다. 외부 이미지 주소와 `<style>`, `style=""`은 콘텐츠 보안 정책 때문에 쓰지 않는다. 테스트가 이를 확인한다.
- 가장 최근 글이 블로그 홈의 “최신 글”이 된다.

디자인 규칙은 루트의 [DESIGN.md](../DESIGN.md#blog-blog)를 따른다. 루트의 `make build`가 블로그를 빌드해 최종 Pages 산출물의 `dist/blog/`에 포함한다. 좋아요와 댓글은 [giscus 설정](DISCUSSIONS.md)을 따른다.
