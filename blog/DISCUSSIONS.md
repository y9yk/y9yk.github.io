# 댓글과 공감 연결

1. 공개 저장소의 Settings → General → Features에서 Discussions를 켜고, 해당 저장소에 [giscus GitHub App](https://github.com/apps/giscus)을 설치한다.
2. [giscus 설정](https://giscus.app/ko)에서 저장소와 카테고리를 선택한다. 글별 대화만 모으려면 Announcements 유형의 전용 카테고리를 쓴다.
3. 설정 페이지의 `data-repo`, `data-repo-id`, `data-category`, `data-category-id` 값을 각각 아래 이름으로 Astro 빌드 환경에 전달한다. 로컬에서는 프로젝트 루트의 `.env.local`을 쓸 수 있다. GitHub Actions에서는 빌드 단계의 환경 변수로 전달한다.

```dotenv
PUBLIC_GISCUS_REPO=
PUBLIC_GISCUS_REPO_ID=
PUBLIC_GISCUS_CATEGORY=
PUBLIC_GISCUS_CATEGORY_ID=
```

다시 빌드한 뒤 글 하단의 **댓글과 공감 열기**를 누른다. 방문자가 GitHub로 로그인한 후 처음 댓글이나 반응을 남기면 해당 글의 Discussion이 생성된다. 대화는 글 경로에 연결되므로 운영 중에는 글의 slug를 유지한다. 기존 Bear Blog 공감 수는 두 서비스에서 별개로 집계된다.

브라우저에 DNT 또는 GPC가 켜져 있으면 GitHub 링크가 제공된다. 그 외에는 방문자가 버튼을 눌러야 외부 댓글 위젯을 불러온다.
