---
title: "다음 개발을 시작하기 전에, 무엇을 책임질지 적어 보자"
date: "2026-11-16T06:39:00+00:00"
description: "로그 요약 도구를 만든다고 가정하고, 실험을 계속할 조건과 출시 뒤 맡을 일을 한 장에 적어 본다."
topic: "제품 개발"
source: "https://y9yk.bearblog.dev/one-page-memo-before-the-next-build/"
---

<blockquote>
<p><strong>이 글을 쓰게 된 배경</strong><br/>
GeekNews에서 소개된 Zach Chmael의 글 <a href="https://zchmael.substack.com/p/i-can-build-almost-anything-now-whats">‘I Can Build Almost Anything Now. What’s Worth Building?’</a>이 좋아서, 핵심 질문을 한국어로 소개하고 개발자의 상황에 적용해 보았다. 다섯 가지 질문은 원문을 간추려 옮겼고, 로그 요약 도구는 이해를 돕기 위해 별도로 구성한 가상의 예시다. 원문 전체를 번역한 글은 아니다. <a href="https://news.hada.io/topic?id=37237">GeekNews 소개 보기</a></p>
</blockquote>

에러 로그를 모아 아침마다 요약해 주는 작은 도구를 만들었다고 해 보자. 시제품을 본 동료가 매일 스탠드업 회의 전에 받아볼 수 있느냐고 묻는다. 이제 기능 구현 외에 결정할 일이 생긴다. 요약이 오지 않거나 내용이 틀렸을 때 누가 알아차리고 처리할 것인가?

실제 제품 사례가 아닌 가상의 상황이지만, Zach Chmael의 글 'I Can Build Almost Anything Now. What's Worth Building?'을 읽는 출발점으로 삼기 좋다. GeekNews를 통해 접한 이 글에서 저자는 무언가를 만드는 즐거움과 그것을 계속 운영할 책임을 구분한다. 다음 개발을 시작하기 전에 짧은 메모를 써 보자는 제안이다.<sup><a href="#ref-1">[1]</a></sup>

## 편집기를 열기 전에 적어 볼 다섯 가지

저자의 질문을 다음과 같이 간추릴 수 있다.<sup><a href="#ref-1">[1]</a></sup>

<ul>
<li><strong>목적:</strong> 이 프로젝트를 통해 무엇을 얻고 싶은가?</li>
<li><strong>불확실성:</strong> 어떤 질문의 답을 알게 되면 다음 행동이 달라지는가?</li>
<li><strong>실험:</strong> 시간과 비용의 한도를 정하고, 그 질문에 답할 작은 시도를 할 수 있는가?</li>
<li><strong>지속 조건:</strong> 어떤 결과가 나오면 더 해 볼 가치가 있는가?</li>
<li><strong>운영 책임:</strong> 사람들이 사용하기 시작하면 어떤 일을 계속 맡을 것인가? 그 시간을 확보하려면 무엇을 줄일 것인가?</li>
</ul>

개발자에게는 마지막 질문이 특히 유용하다. 구현할 기능은 바로 작업을 시작할 만큼 자세히 설명하면서도, 완성한 뒤 누가 돌볼지는 비워 두기 쉽기 때문이다.

할 일이 쌓이기 전에 메모를 쓰면, 앞으로 그 일을 맡을 사람이 감당할 범위를 먼저 정할 수 있다.

## 로그 요약 도구라면 이렇게 적어 볼 수 있다

앞서 떠올린 도구에 다섯 가지 질문을 적용해 보자. 다음은 실제로 진행한 실험의 결과가 아니라, 메모를 채워 보는 가상의 예시다.

<figure>
<a href="https://images-production-944c.up.railway.app/images/be45ab1f2446fc9bc6f3a665b0596fd7f7776df431fcdea4c4b68e3f7ed26646.png"><img alt="개발 전 메모 작성 예시: 로그 요약 도구의 목적, 불확실성, 실험, 지속 조건, 운영 책임" height="1536" src="https://images-production-944c.up.railway.app/images/be45ab1f2446fc9bc6f3a665b0596fd7f7776df431fcdea4c4b68e3f7ed26646.png" width="1536"/></a>
<figcaption>Zach Chmael의 질문을 응용해 직접 작성한 가상의 로그 요약 도구 메모.</figcaption>
</figure>

<strong>목적.</strong> 아침 근무를 시작하는 개발자가 조사할 오류를 고르도록 돕는다. 이번 시도에서는 사람이 검토할 요약을 만든다. 장애 알림이나 탐지 체계를 대체하는 용도는 아니다.

<strong>불확실성.</strong> 요약이 무엇을 조사할지 정하는 데 도움이 될까? 아니면 읽어야 할 문서만 하나 더 생길까? 그럴듯한 요약을 생성하는 데 성공해도 이 질문은 남는다.

<strong>실험.</strong> 사용 승인을 받고 민감한 정보를 제거한 로그 표본으로 오후 한 번 동안 요약을 만든다. 동료 한 명에게 원본 로그와 함께 검토해 달라고 부탁한다. 요약의 각 항목에는 근거가 된 로그를 연결한다. 실행 전에 비용 상한을 정하고, 운영 환경의 인증 정보와 개인정보는 표본에서 제외한다.

<strong>지속 조건.</strong> 동료가 요약을 활용해 조사할 항목을 골랐고 다시 받아보고 싶다고 하면 다음 시도를 검토한다. 놓친 오류와 오해를 부른 요약도 함께 기록한다. 다시 요청했다는 반응은 긍정적인 신호지만, 장애를 안정적으로 찾아낸다는 증거까지 되지는 않는다.

<strong>운영 책임.</strong> 매일 자동으로 보내기 전에 실행 실패를 처리할 사람, 접근 권한을 점검할 사람, 요약 지침이 바뀔 때 검토할 사람을 정한다. 언제 도구를 중단할지도 정하고, 이 일을 맡을 시간을 배정한다. 아무도 시간을 낼 수 없다면 수동 도구로 남겨 둔다.

이렇게 적으면 무엇부터 만들지도 달라진다. 보기 좋은 대시보드는 나중에 만들어도 된다. 원본 로그로 돌아가는 링크는 검토자가 결과를 판단하는 데 필요하므로 먼저 준비해야 한다.

이 순서는 우리가 고른 불확실성에서 나온다. 답해야 할 질문이 '정해진 지연 시간 안에 로그 조회를 끝낼 수 있는가'였다면 첫 실험도 달라졌을 것이다.

## 실험 결과에 따라 계획도 바뀌어야 한다

Paul Graham은 'How to Get Startup Ideas'에서 그럴듯한 잠재 고객 설명이 실제 수요의 부재를 가릴 수 있다고 지적한다. 자신도 미술관을 위한 소프트웨어를 만들면서 수요를 가정했고, 나중에야 그 가정이 틀렸음을 알게 됐다고 회고한다.<sup><a href="#ref-2">[2]</a></sup>

사내 도구에서도 비슷한 착각을 할 수 있다. 동료들이 '로그를 읽기 어렵다'는 데 동의했다고 해서 매일 AI 요약을 보내 달라고 요청한 것은 아니다.

앞선 예시에서 검토자가 요약은 읽지 않고 원본 로그 링크만 반복해서 열었다고 해 보자. 다음 단계는 더 나은 저장 쿼리나 오류를 묶어서 보여 주는 페이지일 수 있다. 쓸 만한 필요를 발견하면서도, 요약 기능은 빼는 편이 낫다는 결론에 도달할 수 있다.

그래서 지속 조건에는 더 만들 이유뿐 아니라 범위를 줄이거나, 잠시 멈추거나, 접근을 바꿀 조건도 적는 편이 좋다. 그렇지 않으면 어떤 반응이 나와도 기능을 하나 더 만들 이유로 해석하기 쉽다.

## 서비스가 되지 않아도 끝낼 수 있다

Chmael은 새로운 것을 배우거나 만드는 재미를 느끼는 것만으로도 프로젝트를 할 이유가 충분하다고 말한다.<sup><a href="#ref-1">[1]</a></sup> 나도 이 의견에 공감한다. 꼭 고객을 모으거나 서비스로 운영하지 않더라도, 만드는 과정에서 배우고 즐거움을 얻었다면 의미 있는 프로젝트라고 생각한다.

로그 요약 도구도 검색과 요약이 어떻게 맞물리는지 배웠다면 그 자체로 끝낼 수 있다. 코드를 남기고, 잘되지 않은 점을 기록하고, 거기서 멈춰도 된다. 매일 제공하는 일은 별도로 결정할 책임이다.

다음 개발을 시작하기 전에 다섯 줄을 채워 보자. 내일 할 일을 바꿀 수 있을 만큼 구체적이면 좋다. '아이디어를 검증한다'보다 '개발자 한 명에게 요약을 보여 주고 무엇을 조사하는지 살펴본다'고 적으면 어디서 시작할지 정하기 쉽다.

## 참고 자료

<ol>
<li><a id="ref-1"></a>Zach Chmael. <a href="https://zchmael.substack.com/p/i-can-build-almost-anything-now-whats">I Can Build Almost Anything Now. What's Worth Building?</a>. 2026년 11월 8일. 'The note I'd write before the next build', 'Would I want to do the work if this succeeds?', 'I still want to make unnecessary things' 절. <a href="https://news.hada.io/topic?id=37237">GeekNews 소개</a>를 통해 발견했다.</li>
<li><a id="ref-2"></a>Paul Graham. <a href="https://paulgraham.com/startupideas.html">How to Get Startup Ideas</a>. 2012년 11월. 'Problems', 'Well' 절.</li>
</ol>
