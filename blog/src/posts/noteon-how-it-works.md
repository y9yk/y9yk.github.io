---
title: "NoteOn의 아키텍쳐: 강의 영상과 노트를 영상 ID 하나로 묶기"
date: "2026-11-27T09:30:00+09:00"
description: "강의를 깊게 공부하는 도구 NoteOn의 설계를 정리한다. 영상 ID 중심의 데이터 구조, 저장소의 코드 구성, 강의 화면 와이어프레임과 디자인 원칙, 노트를 만드는 큐레이션 과정이다."
topic: "제품 개발"
---

<blockquote>
<p><strong>TL;DR</strong><br/>
NoteOn은 모든 데이터를 YouTube 영상 ID 하나에 묶는다. 코드는 라우트(<code>app/</code>), 화면 조각(<code>components/</code>), 데이터 계층(<code>lib/</code>), 저장소(Supabase)로 나뉘고, 개발과 운영이 같은 카탈로그 로더를 거친다. 강의 화면은 "영상을 놓치지 않고 노트를 읽는다"는 한 가지 목표로 설계했다. 노트는 자동 생성이 아니라 검사와 원본 대조를 거친 편집의 결과다.</p>
</blockquote>

깊게 공부하는 데 필요한 건 두 가지였다. 어려운 대목의 근거를 곁에 두는 것, 그리고 내 생각의 흔적을 남기는 것이다. 이 글은 그 두 가지를 구조, 코드, 화면으로 어떻게 옮겼는지에 대한 기록이다.

## 데이터는 무엇을 기준으로 묶을까요?

가장 먼저 정한 것은 "무엇을 기준으로 자료를 이을까"였다. 답은 YouTube 영상 ID 열한 자다. 자막도, 핵심 구간도, 노트도, 메모와 학습 기록도 모두 이 ID에 매단다. 기준이 하나뿐이라, 어느 한 조각을 고쳐도 나머지가 같은 영상을 가리킨다.

<figure>
<a href="/blog/media/noteon-how-it-works/hub.png"><img alt="가운데 영상 ID 상자에서 한국어 자막, 핵심 구간, 강의 노트, 메모와 내 학습으로 이어지는 구조도" height="400" src="/blog/media/noteon-how-it-works/hub.png" width="960"/></a>
<figcaption>모든 데이터는 영상 ID 하나에 매달린다.</figcaption>
</figure>

테이블도 이 기준을 따른다.<sup><a href="#ref-1">[1]</a></sup>

| 테이블 | 담는 것 | 기준 키 |
|---|---|---|
| `courses` | 과목, 순서, 분야 | 과목 ID |
| `lectures` | 강의 메타데이터, 노트, 구간 | **YouTube 영상 ID** |
| `study_entries` | 북마크, 좋아한 강의, 시청 기록 | 사용자 + 영상 ID |
| `lecture_annotations` | 문장 메모, 공개 여부 | 사용자 + 영상 ID + 문장 범위 |

개인 기록이 담긴 테이블은 모두 Supabase의 행 수준 보안(RLS)을 켰다. 내 메모와 북마크는 나만 읽고 쓸 수 있다.

오류는 두 곳에서 거른다. 예를 들어 영상보다 긴 발췌 끝 시각은 DB 제약과 편집 초안 검사 양쪽에서 막힌다. 한쪽만 믿지 않는다.<sup><a href="#ref-1">[1]</a></sup>

## NoteOn의 코드 구성

저장소는 Next.js App Router 구조를 따른다. 역할에 따라 네 층으로 나뉜다.

<figure>
<a href="/blog/media/noteon-how-it-works/architecture.png"><img alt="app 라우트(홈, topics, lectures, study)에서 components(explorer, player, korean-captions, lecture-notes), lib(catalog.ts, study.ts, telemetry), 저장소(개발용 스냅샷 data/catalog.json, Supabase Postgres)로 내려가는 구성도. 아래에서 큐레이션 플러그인이 migrations로 노트를 반영한다" height="520" src="/blog/media/noteon-how-it-works/architecture.png" width="960"/></a>
<figcaption>코드 구성. 저장소 디렉터리를 기준으로 다시 그렸다.</figcaption>
</figure>

1. **`app/` 라우트.** 홈(`/`), 주제(`/topics/[topic]`), 강의(`/lectures/[id]`), 내 학습(`/study`)이 전부다. 강의 페이지의 `[id]`가 곧 영상 ID다.
2. **`components/` 화면 조각.** 탐색(`explorer`, `lecture-feed`), 재생(`player`, `korean-captions`, `lecture-timeline`), 읽기(`lecture-notes`, `note-popover`)로 묶인다.
3. **`lib/` 데이터 계층.** 화면은 DB를 직접 부르지 않고 이 층을 거친다. 핵심은 카탈로그 로더 `catalog.ts`다.
4. **저장소.** 운영은 Supabase Postgres, 개발은 저장소에 포함된 스냅샷 `data/catalog.json`이다.

### 개발과 운영이 같은 로더를 거친다

운영에서는 서버가 Supabase의 공개 키로 과목과 강의를 읽는다. 개발 환경에서 연결 설정이 비어 있으면 스냅샷을 읽는다.

중요한 점은 **어느 쪽이든 같은 로더 함수**를 거쳐 보충 노트와 공식 챕터가 붙는다는 것이다. 그래서 개발 화면에서 본 모습과 운영 화면이 어긋나지 않는다. 노트를 고친 뒤 운영 DB에 올리기 전에, 로컬에서 같은 모습으로 먼저 확인할 수 있다.<sup><a href="#ref-1">[1]</a></sup>

## 화면은 어떻게 설계했을까요?

강의 화면의 목표는 하나다. **노트를 읽는 동안에도 영상이 곁에 있어야 한다.** 근거를 곁에 둔다는 동기를 화면으로 옮기면 이렇게 된다.

<figure>
<a href="/blog/media/noteon-how-it-works/wireframe.png"><img alt="강의 화면 와이어프레임 두 장. 왼쪽 첫 화면은 YouTube 플레이어와 한국어 자막 오버레이, 오른쪽 핵심 구간 목록, 아래 한 문장 요지. 오른쪽은 아래로 내렸을 때로, 작은 플레이어와 목차가 왼쪽에 고정되고 오른쪽에 장 제목과 재생 시각, 노트 본문, 선택한 문장 위의 메모 쓰기 버튼, 이 구간 정리 박스가 있다" height="560" src="/blog/media/noteon-how-it-works/wireframe.png" width="960"/></a>
<figcaption>강의 화면 와이어프레임. 왼쪽은 첫 화면, 오른쪽은 노트를 읽으려 내렸을 때다.</figcaption>
</figure>

설계에서 정한 규칙은 다음과 같다.<sup><a href="#ref-2">[2]</a></sup>

- **첫 화면은 영상과 구간.** 플레이어 위에 한국어 자막이 겹치고, 오른쪽 핵심 구간을 누르면 그 시점으로 이동한다.
- **내리면 영상이 작아질 뿐 사라지지 않는다.** 작은 플레이어와 목차가 왼쪽에 고정되고, 지금 읽는 장의 번호가 강조된다.
- **노트의 각 장은 재생 시각을 가진다.** 장 제목 옆 시각을 누르면 그 범위가 재생된다. 글과 영상이 서로를 가리킨다.
- **흔적은 문장 단위로 남긴다.** 문장을 선택하면 '메모 쓰기' 버튼이 뜨고, 메모는 기본 비공개다.
- **좁은 화면에서는** 목차가 펼침 메뉴로 바뀐다.

### 디자인 원칙

화면 전체에는 다섯 가지 원칙을 적용했다.<sup><a href="#ref-2">[2]</a></sup>

1. **콘텐츠가 먼저다.** 색은 썸네일, 노트, 그림이 낸다. 인터페이스는 회색 계열에 주황색 강조 하나만 쓴다.
2. **강조색은 아껴 쓴다.** 주황은 주요 동작, 현재 상태, 데이터 표시에만 쓴다.
3. **그림자보다 가는 선.** 구분은 선과 옅은 면으로 한다. 그림자는 떠 있는 것(작은 플레이어, 메모 창)에만 준다.
4. **장식용 라벨을 달지 않는다.** 제목이 이미 무엇인지 말하면 아이콘이나 꼬리표를 덧붙이지 않는다.
5. **한국어로 읽기 편하게.** 단어 단위 줄바꿈, 넉넉한 행간, 한 줄 약 46rem 폭을 지킨다.

공부 도구라서 오래 읽어도 피곤하지 않은 화면이 중요했다. 다섯 원칙 모두 "읽는 데 방해하지 않기"로 모인다.

## 강의 한 편은 어떻게 노트가 될까요?

노트는 자동 생성물이 아니라 편집 결과물이다. 깊게 공부하려면 노트부터 믿을 수 있어야 하기 때문이다. 강의 한 편을 다룰 때 넘겨받는 것은 영상 ID, 한국어로 다시 쓴 노트, 그리고 각 설명과 재생 시각을 확인할 수 있는 원본 링크다.

<figure>
<a href="/blog/media/noteon-how-it-works/pipeline.png"><img alt="공식 영상에서 자료와 한국어 노트 초안을 거쳐 검사·원본 대조 뒤, 로컬 카탈로그와 조건부 변경 SQL로 나뉘어 Supabase에 반영되는 흐름도" height="320" src="/blog/media/noteon-how-it-works/pipeline.png" width="960"/></a>
<figcaption>강의 한 편이 노트가 되기까지. 저장소 운영 문서의 흐름을 바탕으로 다시 그렸다.</figcaption>
</figure>

과정은 대략 이렇다.<sup><a href="#ref-3">[3]</a></sup>

1. 공식 영상과 학기·회차를 확인하고, 강의 자료와 공식 챕터를 모은다.
2. 허용된 자막을 비공개로 검토하고, 출처를 단 한국어 노트 초안을 쓴다.
3. 형식 검사와 원본 대조를 거친다. 결과는 새 DB용 초기 시드와 기존 DB용 조건부 변경 SQL로 나눈다.
4. 개발 화면에서 확인한 뒤 Supabase에 반영하고, 운영 화면에서 다시 확인한다.

변경은 모두 `supabase/migrations`에 SQL 파일로 남는다. 어떤 강의의 노트가 언제 어떻게 바뀌었는지 저장소 기록으로 추적할 수 있다.

이 과정은 Codex 큐레이션 플러그인으로 반복할 수 있게 만들었다. 강의를 고르는 단계부터 노트 작성, 검사, 운영 DB 갱신까지 같은 순서로 따라간다. 덕분에 강의가 늘어도 품질 기준과 출처 표기가 흔들리지 않는다.<sup><a href="#ref-3">[3]</a></sup>

## 서버 관측

운영에서는 OpenTelemetry로 트레이스·메트릭·로그를 남긴다. 브라우저는 재생, 구간 이동, 메모 저장 같은 허용된 이용 이벤트만 보낸다. 계정 ID, 이메일, 메모 본문은 보내지 않고, DNT나 GPC가 켜진 브라우저는 아무것도 보내지 않는다.<sup><a href="#ref-4">[4]</a></sup>

## 지금까지 한 이야기를 정리해보자

- **데이터:** 기준은 영상 ID 하나다. 개인 기록은 RLS로 지킨다.
- **코드:** 라우트, 화면 조각, 데이터 계층, 저장소의 네 층이다. 개발과 운영이 같은 로더를 거친다.
- **화면:** 노트를 읽는 동안에도 영상이 곁에 있다. 글과 영상이 재생 시각으로 서로를 가리킨다.
- **노트:** 자동 생성이 아니라 검사와 대조를 거친 편집의 결과이고, 변경은 SQL로 남는다.

모두 같은 목표로 돌아간다. 좋은 강의를 흘려보내지 않고 깊게 공부하려면, 흩어진 자료를 한 기준으로 묶고 읽는 동안 근거가 곁에 있어야 한다.

## 참고 자료

<ol>
<li><a id="ref-1"></a>NoteOn 설계 문서. '읽는 곳과 쓰는 곳', '무엇을 어떤 단위로 저장하는가' 절. 저장소 <code>docs/architecture.md</code>, <code>lib/catalog.ts</code>, <code>supabase/migrations</code>에서 확인했다.</li>
<li><a id="ref-2"></a>NoteOn 디자인 시스템. 저장소 <code>DESIGN.md</code>의 'Principles', 'Components' 절과 설계 문서의 '강의를 보면서 노트를 읽는 화면' 절.</li>
<li><a id="ref-3"></a>NoteOn 운영 문서. '강의 수집과 큐레이션 운영'. 저장소 <code>docs/data-pipeline.md</code>와 큐레이션 플러그인.</li>
<li><a id="ref-4"></a>NoteOn 관측 문서. '서버 관측과 이용 기록'. 저장소 <code>docs/observability.md</code>.</li>
</ol>
