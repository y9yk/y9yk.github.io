# 블로그

Node.js 24 환경에서 저장소 루트의 `make serve`를 실행하면 포트폴리오와 블로그를 함께 볼 수 있다. 블로그만 편집할 때는 이 폴더에서 `npm ci` 후 `npm run dev`를 실행하고 터미널 주소의 `/blog/`를 연다.

공개할 글은 `src/posts/<slug>.md`에 추가한다. 프런트매터에는 title, date(시간대 포함 ISO 문자열), description, topic을 넣는다. 기존 Bear Blog 글에는 source를, 요약에는 excerpt: true와 source를 추가한다. 대표 글은 `src/pages/index.astro`에서 선택한다. 글의 slug는 댓글 스레드의 식별자로도 쓰인다.

루트의 `make build`가 블로그를 빌드해 최종 Pages 산출물의 `dist/blog/`에 포함한다. 댓글과 공감은 이 저장소의 [giscus 설정](DISCUSSIONS.md)을 따른다.
