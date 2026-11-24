---
title: "Claude Code와 Codex를 여러 개 켜두면, 그다음엔 뭘 써야 할까요?"
date: "2026-11-05T04:40:00+00:00"
description: "동시에 맡긴 작업이 어디서 끊기는지에 따라 Herdr, Conductor, cmux, ccmux를 비교한다."
topic: "개발 도구"
source: "https://y9yk.bearblog.dev/beyond-claude-code-codex-agent-workspaces/"
---

Claude Code에 수정 하나를 맡기고 Codex에는 다른 브랜치를 봐 달라고 했다. 일을 조금 더 얹다 보니 돌아가는 작업은 셋, 검토할 브랜치는 두 개가 됐다. 그중 하나가 실행 권한을 묻고 있는데, 어느 터미널인지부터 찾아야 한다.

이때 막힌 건 코드가 아니다. 이미 맡긴 일이 어디까지 갔는지, 어느 화면으로 돌아가야 하는지 놓친 것이다. 이 불편을 Herdr, Conductor, cmux, ccmux는 각기 다른 곳에서 풀어낸다. 2026년 11월 5일 기준 공식 문서를 바탕으로, 각각을 어떤 작업에 써볼 만한지 살펴봤다. 속도나 성능을 직접 재지는 않았다.

## 작업은 어디서 자꾸 끊길까요?

<table>
<thead>
<tr>
<th>자주 겪는 일</th>
<th>먼저 볼 도구</th>
<th>처음 해볼 일</th>
</tr>
</thead>
<tbody>
<tr>
<td>터미널을 계속 살려 두고, 에이전트에게 검토를 넘기고 싶다</td>
<td>Herdr</td>
<td>검토 에이전트를 띄워 보고서를 받아 본다</td>
</tr>
<tr>
<td>서로 독립적인 수정마다 브랜치와 검토 공간이 필요하다</td>
<td>Conductor</td>
<td>이슈 하나를 작업공간 생성부터 테스트, PR까지 끝내 본다</td>
</tr>
<tr>
<td>터미널, 알림, 브라우저를 오가다 맥락을 놓친다</td>
<td>cmux</td>
<td>에이전트 터미널 옆에서 웹 변경 하나를 확인한다</td>
</tr>
<tr>
<td>tmux는 편한데 대기 중인 세션을 찾는 일이 번거롭다</td>
<td>ccmux</td>
<td>입력을 기다리는 에이전트를 찾아 답해 본다</td>
</tr>
</tbody>
</table>

표에서 하나를 고르기 전에, 기능 이름만으로는 쓰임이 잘 드러나지 않는다는 점을 짚고 가자. Herdr와 ccmux에도 worktree 기능이 있고, cmux에도 자동화 인터페이스가 있다. 같은 기능이 있어도 터미널을 살려 두려는 사람과 작업마다 브랜치를 나누려는 사람이 처음 써볼 기능은 다를 수 있다.<sup><a href="#ref-1">[1]</a></sup><sup><a href="#ref-2">[2]</a></sup><sup><a href="#ref-3">[3]</a></sup><sup><a href="#ref-4">[4]</a></sup>

## Herdr를 닫으면, 돌아가던 작업은 어떻게 될까요?

Herdr에서는 앱 창을 닫아도 터미널을 관리하는 별도 서버인 herdr-core가 살아 있으면 작업이 계속 돈다. 여러 에이전트를 오래 띄워 두는 경우라면, 그중 하나에게 검토도 넘겨볼 수 있다. <code>hc</code> CLI로 보조 에이전트를 시작하고 메시지를 주고받으며, SSH로 연결할 수 있는 다른 컴퓨터의 작업도 같은 화면에서 본다.<sup><a href="#ref-5">[5]</a></sup>

가이드에는 기존 에이전트를 탭에서 띄운 뒤 <code>~/.config/herdr-app/AGENTS.md</code>를 읽게 하는 예가 나온다. 거기서 화면 배치를 바꾸거나 타이머, 에이전트 보드를 만들어 달라고 할 수 있다. 아래는 그렇게 꾸민 화면이다.<sup><a href="#ref-1">[1]</a></sup>

<figure class="post-figure">
<img alt="프로젝트에서 제공하는 Herdr Board 예시. Claude Code와 Codex 터미널 위에 에이전트 상태 카드가 있다." src="/blog/media/beyond-claude-code-codex-agent-workspaces/b3cbe49de5fcfa93.png"/>
<figcaption>Herdr Board의 사용자 지정 예시</figcaption>
</figure>

보드를 띄웠다면 작은 수정 하나를 맡기고, 구현이 끝났을 때 별도 검토 에이전트에게 브랜치나 diff를 넘겨 보자. 검토 결과가 다시 돌아오는 과정까지 봐야, 이 화면이 상태를 한눈에 보여 주는 데서 그치는지 실제 인계까지 편하게 해주는지 알 수 있다.

이렇게 화면과 동작을 꾸미기 시작하면 관리할 설정도 늘어난다. 특히 Herdr의 모드는 별도 샌드박스 없이 실행되는 코드라서, 외부 모드는 내용을 확인한 뒤 추가하는 편이 좋다.<sup><a href="#ref-16">[16]</a></sup> 네이티브 앱의 상세 상태도 실행 중인 프로그램이 OSC 7501로 알려줄 때 표시된다. 또 창을 닫아도 작업을 이어갈 수 있다는 말은 호스트가 계속 동작한다는 전제다. 노트북이 잠든 뒤에도 실행해야 한다면 호스트부터 따로 정해야 한다. 네이티브 앱의 상태 표시는 프로그램이 OSC 7501로 상태를 알려줄 때 동작한다. 임의의 CLI를 띄운다고 상세 상태까지 따라오는 건 아니다. 앱 창을 닫는 것과 실행 중인 컴퓨터가 잠드는 것도 다르다. 후자까지 피하려면 작업을 계속 돌릴 호스트가 필요하다.<sup><a href="#ref-5">[5]</a></sup>

이름이 비슷한 <strong>Herdr TUI</strong>는 자체 서버가 있는 별도 앱이다. 네이티브 앱과 에이전트를 공유하지 않는다. TUI 문서의 화면 감지와 통합 기능은 herdr-core의 상태 보고 방식과 구분해서 봐야 한다.<sup><a href="#ref-6">[6]</a></sup><sup><a href="#ref-7">[7]</a></sup>

## Conductor에서는 수정 두 개를 어디에 둘까요?

반대로 에이전트 둘에게 각각 배포할 수 있는 수정 두 건을 맡겼다면, 어디서 작업을 확인하느냐보다 각 변경을 어떻게 따로 끝내느냐가 중요해진다. Conductor는 로컬 작업마다 Git worktree를 만들어 별도 체크아웃과 브랜치를 주고, 대화와 명령 실행, 검토를 그 작업공간에 묶는다. 공식 가이드도 저장소를 가져오는 데서 시작해 diff를 보고, 테스트하고, PR을 여는 순서로 이어진다.<sup><a href="#ref-2">[2]</a></sup><sup><a href="#ref-8">[8]</a></sup>

두 작업의 완료 기준을 각각 적고 결과도 따로 검토해 보면 이 구조의 쓰임이 드러난다. 다만 두 변경이 같은 인터페이스나 파일에 닿는다면, 각자의 작업공간에서 끝났다는 것만으로 조율이 끝나지는 않는다. 두 결과를 합칠 때 동작을 다시 확인해야 한다.

작업을 나누기 전에 새 체크아웃에서 테스트가 도는지도 봐야 한다. Git이 추적하지 않는 설정이나 의존성, 데이터베이스, 생성 파일은 별도로 준비해야 할 수 있다. 이때 파일이 나뉘어 있어도 로컬 명령은 여전히 사용자 권한으로 실행된다.<sup><a href="#ref-2">[2]</a></sup>

작업을 노트북이 닫힌 뒤에도 계속해야 한다면, Conductor의 Cloud 작업공간은 Linux 샌드박스에서 실행되고 조직과 공유할 수 있다. 그만큼 로컬 환경과의 호환성, 팀에서 접근할 수 있는 범위를 확인해야 한다.<sup><a href="#ref-9">[9]</a></sup> 문서 기준으로 지원되는 유료 요금제와 GitHub 저장소가 필요하고, 세션 입출력은 Conductor 서버에 저장된다. 에이전트 구독이나 API 키도 별도여서, 비용을 볼 때는 앱 요금, 모델 사용량, 호스팅 실행 비용을 나누어 보는 편이 좋다. 문서 기준으로 지원되는 유료 요금제와 GitHub 저장소가 필요하고, 클라우드 세션 입출력은 Conductor 서버에 저장된다. 에이전트 구독이나 API 키도 별도로 준비한다. 앱 요금, 모델 사용량, 호스팅 실행 비용을 각각 봐야 비용이 보인다.<sup><a href="#ref-10">[10]</a></sup>

## cmux에서는 확인할 화면을 터미널 옆에 둡니다

cmux는 libghostty 기반 macOS 터미널이다. 사이드바에서 브랜치나 포트를 확인하고, 입력이나 확인이 필요한 창은 알림 링으로 찾는다. 내장 브라우저와 CLI·소켓 API가 있어서 터미널에서 작업한 웹 변경을 같은 공간에서 확인할 수 있다.<sup><a href="#ref-3">[3]</a></sup>

<figure class="post-figure">
<img alt="공식 cmux 문서의 스크린샷. 확인이 필요한 터미널 창 둘레에 파란 알림 링이 표시돼 있다." src="/blog/media/beyond-claude-code-codex-agent-workspaces/d2b37220de199fc3.png"/>
<figcaption>cmux 알림 링</figcaption>
</figure>

기존 에이전트를 띄우고, 작은 UI 수정 하나를 맡겨 보자. 수정 중인 앱을 옆 브라우저에 열어 놓으면 알림이 왔을 때 무엇을 확인해야 하는지 찾기가 쉬워지는지 볼 수 있다.

이렇게 터미널 옆에 확인할 화면을 두는 게 목적이라면, 작업공간을 다시 열었을 때 어디까지 돌아오는지도 알아둘 만하다. 시작 가이드 기준으로 macOS 14 이상이 필요하며, cmux는 배치와 작업 맥락을 복원한다. 지원 에이전트는 통합 기능이 네이티브 세션 ID를 기록해 뒀을 때 대화를 이어갈 수 있다. 그 사이 실행 중이던 임의의 프로세스까지 저장해 이어주는 기능은 아니다.<sup><a href="#ref-11">[11]</a></sup><sup><a href="#ref-12">[12]</a></sup>

## tmux를 잘 쓰고 있다면, 세션 찾기만 바꿔볼까요?

ccmux는 기존 tmux 세션 위에서 돌아간다. 세션 선택기에서 작업 중, 입력 대기, 완료 상태를 보고 바로 그 창으로 이동할 수 있다. 문서에 나온 시작 순서는 <code>brew install ccmux</code>, <code>ccmux setup</code>, 그리고 평소처럼 에이전트와 함께 ccmux를 실행하는 것이다.<sup><a href="#ref-4">[4]</a></sup><sup><a href="#ref-13">[13]</a></sup>

<figure class="post-figure">
<img alt="프로젝트별 에이전트 세션과 대기, 작업 중, 완료, 유휴 상태를 보여 주는 ccmux 공식 README 화면." src="/blog/media/beyond-claude-code-codex-agent-workspaces/f59776a1afd6edc8.png"/>
<figcaption>ccmux 세션 선택기</figcaption>
</figure>

<code>setup</code>은 지원 에이전트의 통합 기능을 설치한다. 훅 없이도 기본 감지는 되지만, 같은 프로젝트에서 여러 세션을 돌릴 때는 훅이 어느 세션이 어느 창에 속하는지 더 잘 맞춰 준다.<sup><a href="#ref-14">[14]</a></sup>

기존 tmux 환경을 유지하는 만큼 필요한 버전도 함께 본다. 팝업은 tmux 3.2 이상, worktree 기능은 Git 2.31 이상이 필요하다. 에이전트마다 지원 범위도 다르다. 가령 문서에 나온 대화 분기 기능의 전용 명령은 현재 Claude Code에만 있다.<sup><a href="#ref-4">[4]</a></sup><sup><a href="#ref-15">[15]</a></sup>

## 그래서 하나를 써본다면, 뭘 기록해 둘까요?

같은 저장소에서 평소 자꾸 끊기는 작업 하나를 골라 보자. 도구를 붙이기 전후로 다음을 보면, 창이 늘어난 것 말고도 달라진 게 있는지 판단하기 쉽다.

<ul>
<li>새 작업공간을 만든 뒤 테스트가 처음 돌아가기까지 얼마나 걸렸나?</li>
<li>입력을 기다리는 에이전트를 직접 찾아야 했던 건 몇 번인가?</li>
<li>변경을 받아들이기 전에 무엇이 왜 바뀌었는지 확인할 수 있었나?</li>
<li>작업 두 개가 끝난 뒤 다시 맞춰야 했던 건 무엇인가?</li>
<li>완료까지 모델 사용량과 사람의 검토 시간이 얼마나 들었나?</li>
</ul>

이 질문들은 도구를 직접 비교할 때 쓸 기준이다. 가령 별도 체크아웃 덕분에 작업 중 충돌이 줄었더라도, 두 변경이 공통 인터페이스에서 만난다면 통합할 때 다시 확인할 일이 생긴다. 이런 작업에서는 에이전트를 하나 더 띄우기 전에 작업 순서와 인터페이스 규칙을 정하는 편이 더 도움이 될 수 있다.

한 에이전트와 지금 터미널로 작업부터 테스트, 검토까지 편하게 끝낼 수 있다면, 그 흐름을 기준으로 삼아도 된다. 권한 요청을 놓치는지, 검토할 브랜치를 찾느라 시간을 쓰는지처럼 어디에서 자꾸 멈추는지부터 보면 새 도구를 붙일 이유도 구체적이 된다.

## 참고 자료

<ol>
<li><a id="ref-1"></a>Herdr. <a href="https://herdr.dev/guide/">Guide</a>. 시작하기, 검토 에이전트, worktree, 사용자 지정 예시.</li>
<li><a id="ref-2"></a>Conductor. <a href="https://www.conductor.build/docs/concepts/git-worktrees">Git worktrees</a>. 격리, 공유 상태, 무시된 파일, 설정 스크립트.</li>
<li><a id="ref-3"></a>cmux. <a href="https://cmux.com/">Product overview</a>. 기능, 브라우저, 자동화, 무료 터미널과 유료 선택 기능.</li>
<li><a id="ref-4"></a>ccmux. <a href="https://ccmux.dev/docs/">Overview</a>. 세션 선택기와 요구사항.</li>
<li><a id="ref-5"></a>Herdr. <a href="https://herdr.dev/core/">herdr-core</a>. 지속 터미널, 보조 에이전트 수명 주기, SSH, OSC 7501.</li>
<li><a id="ref-6"></a>Herdr. <a href="https://herdr.dev/">Product FAQ</a>. 네이티브 앱과 Herdr TUI의 차이.</li>
<li><a id="ref-7"></a>Herdr TUI. <a href="https://herdr.dev/tui/docs/agents/">Agents</a>. 상태 감지와 통합.</li>
<li><a id="ref-8"></a>Conductor. <a href="https://www.conductor.build/docs/first-workspace">Your first workspace</a>. 저장소 설정부터 PR까지.</li>
<li><a id="ref-9"></a>Conductor. <a href="https://www.conductor.build/docs/cloud">What is Conductor Cloud?</a>. 로컬 설정과 클라우드 실행 비교, 조직 공유.</li>
<li><a id="ref-10"></a>Conductor. <a href="https://www.conductor.build/docs/cloud/faq">Cloud FAQ</a>. 요금제, 자격증명, 저장 범위, 세션 데이터.</li>
<li><a id="ref-11"></a>cmux. <a href="https://cmux.com/docs/getting-started">Getting started</a>. macOS 요구사항과 설치.</li>
<li><a id="ref-12"></a>cmux. <a href="https://cmux.com/docs/session-restore">Session restore</a>. 복원 상태, 훅, 네이티브 세션 이어가기.</li>
<li><a id="ref-13"></a>ccmux. <a href="https://ccmux.dev/docs/getting-started/">Getting started</a>. 설치, 설정, 에이전트 실행.</li>
<li><a id="ref-14"></a>ccmux. <a href="https://ccmux.dev/docs/session-matching/">Session matching and hooks</a>. 통합 기능의 효과와 기본 감지.</li>
<li><a id="ref-15"></a>ccmux. <a href="https://ccmux.dev/docs/worktrees/">Worktrees</a>. worktree 요구사항과 에이전트별 제약.</li>
<li><a id="ref-16"></a>Herdr. <a href="https://github.com/herdrdev/herdr-app/blob/e77f112ac2ea136b84fe510efa42d41163bfd776/README.md">App README</a>. 업데이트, 개인정보, 신뢰 기반 모드.</li>
</ol>

### 이미지 출처

<ul>
<li><strong>Herdr Board 사용자 지정 예시</strong> · 프로젝트 제공 이미지, Apache-2.0, 변경 없음. <a href="https://github.com/herdrdev/herdr-layout-examples/blob/0ec967640bf854ffb839e9af06c1e0c328bc9815/board/preview.png">출처</a> · <a href="https://github.com/herdrdev/herdr-layout-examples/blob/0ec967640bf854ffb839e9af06c1e0c328bc9815/LICENSE">라이선스</a></li>
<li><strong>cmux 알림 링</strong> · cmux 공식 문서, © Manaflow, Inc., GPL-3.0-or-later, 변경 없음. <a href="https://github.com/manaflow-ai/cmux/blob/074abb874d7fa053161686a9bd1e4ec965501f83/docs/assets/notification-rings.png">출처</a> · <a href="https://github.com/manaflow-ai/cmux/blob/074abb874d7fa053161686a9bd1e4ec965501f83/LICENSE">라이선스</a></li>
<li><strong>ccmux 세션 선택기</strong> · ccmux 공식 README, © 2026 epilande, MIT, 변경 없음. <a href="https://github.com/epilande/ccmux/blob/d89acbb10403c5ec944ceee701e9c5aa6b358721/README.md">출처</a> · <a href="https://github.com/epilande/ccmux/blob/d89acbb10403c5ec944ceee701e9c5aa6b358721/LICENSE">라이선스</a></li>
</ul>
