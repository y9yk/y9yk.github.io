---
title: "에이전트가 주문을 조회했다. 그런데 고객 문의도 끝난 걸까요?"
date: "2026-11-05T05:06:00+00:00"
description: "반품 문의와 도서 대출 연장 사례를 따라가며, 상담 절차에 어떤 조건을 적고 어떻게 완료 여부를 시험할지 살펴본다."
topic: "에이전트 운영"
source: "https://y9yk.bearblog.dev/sop-agent-workflows-reliability/"
---

“주문한 물건이 아직 안 왔어요.”

상담원이라면 먼저 주문번호를 묻고, 배송 상태를 확인한 뒤 고객에게 다음에 무엇을 하면 되는지 알려 줄 것이다. 조회가 안 되거나 판단이 필요한 경우에는 담당자가 이어받는다. 그런데 이 순서가 상담원들 머릿속에만 있고, 문서로 남은 건 몇 년 치 상담 기록뿐이라면 AI에게는 무엇부터 알려 줘야 할까?

채널톡은 그 상담 기록에서 반복되는 응대 방식을 찾아 AI 상담 에이전트 ALF의 설정 초안으로 만들었다. 배송 문의 한 건을 따라가 보면 어떤 절차를 적어야 하는지 보인다. 그 절차가 실제로 도움이 됐는지는, 뒤에서 도서관 대출 연장 실험을 보며 따로 살펴보자.<sup><a href="#ref-1">[1]</a></sup>

## ALF가 하는 일부터 한번 봅시다

채널톡은 고객이 채팅창으로 문의하면 상담팀이 공용 작업공간에서 답하는 고객지원 서비스다. 그 안에서 ALF는 회사가 등록한 자료를 보고 답하거나, 주문 조회처럼 미리 연결해 둔 작업(Task)을 실행한다.<sup><a href="#ref-2">[2]</a></sup><sup><a href="#ref-3">[3]</a></sup>

아래 공식 영상에서는 상담 화면과 ALF v2가 문의를 처리하는 모습을 볼 수 있다. 화면 구성은 촬영 이후 달라졌을 수 있다.

채널톡 공식 ALF v2 소개와 제품 데모. <a href="https://www.youtube.com/watch?v=V7f6lgNuF0E">유튜브에서 보기</a> · <a href="https://channel.io/kr/blog/articles/ai-chatbot-cs-a0113e03">공식 소개</a>

배송 문의를 ALF에 맡긴다고 하면, 회사가 정해 줄 것은 세 가지다. 주문번호부터 물으라는 지시는 <strong>규칙</strong>에, 배송 상태별로 어떻게 안내할지는 <strong>지식</strong>에 넣는다. 조회 자체는 주문 시스템에 연결된 <strong>작업</strong>이 맡는다. 상담 기록을 분석하면 바로 이 세 설정의 초안을 만들 수 있다.<sup><a href="#ref-1">[1]</a></sup><sup><a href="#ref-3">[3]</a></sup>

## 상담 기록이 어떻게 업무 절차가 될까요?

문제는 기록마다 표현이 다르다는 것이다. 채널톡은 분석 에이전트에 SOP를 주고, 스크립트로 뽑은 실제 상담 표본을 모델이 읽게 했다. 여기서 찾아낸 응대 패턴을 고객지원 절차로 정리한 뒤, ALF 설정 초안을 만들어 사람이 검토하는 흐름이다.<sup><a href="#ref-1">[1]</a></sup>

<figure class="post-figure">
<a aria-label="상담 처리 흐름도 크게 보기" href="https://images-production-944c.up.railway.app/images/9f8b450a0af5657781604d0c5181b7876605550af1a430f60f5c871b1940957e.png"><img alt="상담 수집, 주제 묶기, 표본에서 응대 패턴 추출, 상담 절차 작성, ALF 설정 초안, 사람의 검토 순으로 이어지는 흐름도." src="https://images-production-944c.up.railway.app/images/9f8b450a0af5657781604d0c5181b7876605550af1a430f60f5c871b1940957e.png"/></a>
<figcaption>상담 기록에서 ALF 설정까지</figcaption>
</figure>

‘배송이 아직 안 왔어요’라는 문의를 그림에 넣어 보자. 아래는 흐름을 설명하기 위한 예시다.

<ol>
<li>기존 상담에서 ‘배송 확인해 주세요’, ‘주문이 아직 안 왔어요’ 같은 대화를 찾는다.</li>
<li>배송 상태를 묻는 문의로 묶는다. 주문 취소는 별도 주제다.</li>
<li>상담원이 주문번호를 묻고, 배송 상태를 확인하고, 다음 조치를 안내한 패턴을 실제 대화에서 찾아낸다.</li>
<li>그 패턴으로 절차를 쓴다. 번호를 받아 조회하고, 확인된 상태를 회사 안내 기준에 따라 설명한다. 조회에 실패하거나 판단이 필요하면 상담원에게 넘긴다.</li>
<li>ALF 설정 초안을 만든다. 어떤 문의에 적용할지는 규칙에, 승인된 배송 안내는 지식에, 조회 API와 입력값은 작업에 넣는다.</li>
<li>팀에서 정책과 API 연결을 확인한다. 주문번호가 빠졌거나 조회에 실패하는 경우도 시험하고 초안을 다듬는다.</li>
</ol>

<blockquote>
<p><strong>고객</strong> “물건이 아직 안 왔어요.”<br/>
<strong>ALF</strong> “주문번호를 알려 주시겠어요?”<br/>
<strong>고객</strong> “ORD-123이요.”<br/>
<strong>조회에 성공한 ALF</strong> “현재 배송 상태는 [조회한 상태]입니다. [회사 기준에 따른 다음 조치]를 안내해 드릴게요.”</p>
</blockquote>

이 대화에서 대괄호 안은 조회한 값과 회사가 승인한 안내로 채운다. 순서가 정해져 있으면, 정보가 없을 때 임의로 배송일을 답하는 대신 무엇을 확인하고 언제 넘겨야 하는지가 드러난다.

## 도구 호출이 성공하면 업무도 끝난 걸까요?

배송 조회에 성공해도 고객에게 다음 조치를 알려 주지 않으면 문의가 남는다. 도서관 대출 연장도 비슷하다. 연장 API가 성공했더라도, 먼저 연장할 수 있는 책인지 확인했는지, 올바른 카드 번호를 썼는지, 결과를 이용자에게 알려 줬는지까지 봐야 한다.

2026년 3월 Strands는 이 일을 에이전트에게 맡기고, 간단한 지시와 상세한 표준 업무 절차(SOP)를 비교했다. 6개 시나리오를 방식별로 각각 100번 실행하고 절차 준수, 도구 사용, 말투를 평가했다.<sup><a href="#ref-4">[4]</a></sup>

<table>
<thead>
<tr>
<th>방식</th>
<th>보고된 통과율</th>
<th>평균 입력 토큰</th>
</tr>
</thead>
<tbody>
<tr>
<td>간단한 지시</td>
<td>82.5%</td>
<td>2,329</td>
</tr>
<tr>
<td>상세한 SOP</td>
<td>99.8%</td>
<td>9,879</td>
</tr>
<tr>
<td>실행 전후를 검사하는 훅과 게이트웨이 정책</td>
<td>100.0%</td>
<td>3,346</td>
</tr>
<tr>
<td>그래프 기반 워크플로</td>
<td>80.8%</td>
<td>3,116</td>
</tr>
</tbody>
</table>

상세 절차를 주자 통과율은 82.5%에서 99.8%로 올랐고, 평균 입력 토큰도 2,329에서 9,879로 늘었다. 그 아래의 100.0%도 눈에 띄는데, 이 구성은 훅과 게이트웨이 정책을 함께 썼다. 여섯 가지 상황을 반복한 결과이므로, 표에서 훅만의 효과를 떼어 보거나 운영 중 들어올 모든 요청에 같은 결과를 기대하기는 어렵다.<sup><a href="#ref-4">[4]</a></sup><sup><a href="#ref-5">[5]</a></sup>

그럼 실제 상담에서는 무엇을 성공으로 셀까? Anthropic이 소개한 Gradient Labs는 금융 고객지원에서 **사람 개입 없이 처음부터 끝까지 해결한 비율이 80–90%**라고 보고했다. Claude가 지식 그래프 기반 시스템에서 요청을 해석하고 절차의 다음 단계와 도구를 고르는 방식이다. 여기서 세는 건 위 표의 평가 통과율과 다른 값이다. 가령 고객이 계정 변경을 요청했다면 답변에 그치지 않고 변경까지 끝나야 해결로 볼 수 있다. 공개 사례에는 전체 평가 데이터, 관찰 기간, SOP를 뺀 대조 결과가 나와 있지 않다.<sup><a href="#ref-6">[6]</a></sup>

## 그럼 문서에는 뭐라고 써야 할까요?

배송 조회와 대출 연장에서 공통으로 빠지기 쉬웠던 일은 숙련된 담당자에게는 당연한 사전 확인과 마무리였다. 그런 판단을 다른 사람이나 에이전트가 반복해서 쓸 수 있게 적어 둔 것이 SOP, 즉 표준 업무 절차(standard operating procedure)다.<sup><a href="#ref-7">[7]</a></sup>

<ul>
<li>어떤 요청에 이 절차를 적용하나? 적용하면 안 되는 경우는?</li>
<li>시작 전에 필요한 정보는 무엇이고, 어느 출처를 기준으로 삼나?</li>
<li>어떤 도구를 어느 순서로 쓰고, 어떤 결과에서 다음 단계가 갈리나?</li>
<li>언제 멈추고, 실패하거나 사람 판단이 필요하면 어디로 넘기나?</li>
<li>일을 끝냈다는 걸 무엇으로 확인하고 어떤 근거를 남기나?</li>
</ul>

이 질문에 대한 답을 Strands는 개요, 매개변수, 순서가 있는 단계, MUST나 SHOULD로 표시한 제약을 담은 Markdown 문서로 정리한다. 에이전트가 절차를 찾도록 스킬이나 MCP로 제공하거나 직접 연결할 수 있다. 단계 전환을 워크플로 엔진에 맡길지, 조건에 맞지 않는 실행을 도구 정책에서 막을지는 그다음에 정할 문제다.<sup><a href="#ref-8">[8]</a></sup>

## 문서에서 한 줄만 꺼내 봅시다

도서관 예시는 ‘연장 가능 여부를 확인한다’에서 더 나아간다. 어떤 도구로 책 상태를 확인하는지 적고, 도서관 카드 번호는 고객 메시지에 쓰인 값 대신 사용자 정보 도구에서 가져오게 했다. ‘어떤 책을 빌렸나요?’와 ‘이 책을 연장해 주세요’도 다른 요청으로 다룬다.<sup><a href="#ref-9">[9]</a></sup>

<figure class="post-figure">
<img alt="대출 연장 전에 도서 상태를 조회하고 사용자 정보 도구에서 카드 번호를 가져오도록 명시한 Strands 절차 일부." src="https://images-production-944c.up.railway.app/images/0c3335c6470b42d8ef1a86610649ff651170913f1e519aad5b1d294b8ba03ccf.png"/>
<figcaption>대출 연장 전 필수 확인 항목</figcaption>
</figure>

같은 문장도 어디에 넣느냐에 따라 효력이 달라진다. 샘플 구현은 SOP를 시스템 프롬프트에 넣기 때문에 MUST라고 써도 모델이 그 내용을 해석해 따라야 한다. 별도의 훅 구성에서는 실행 전후를 검사하고, 게이트웨이 정책으로 연장 기간을 제한한다. 호출이 그 경로를 거치면 조건을 어긴 실행을 게이트웨이에서 막을 수 있다. 이 차이를 기준으로 절차를 어디에 둘지 나눠 보자.<sup><a href="#ref-5">[5]</a></sup><sup><a href="#ref-10">[10]</a></sup>

<table>
<thead>
<tr>
<th>방식</th>
<th>절차를 어디에 두나</th>
<th>써볼 만한 상황</th>
<th>살펴볼 점</th>
</tr>
</thead>
<tbody>
<tr>
<td>에이전트에 SOP 제공</td>
<td>자연어 단계와 제약</td>
<td>기존 에이전트에게 반복 업무를 맡길 때</td>
<td>모델이 단계를 건너뛰거나 다르게 해석할 수 있다</td>
</tr>
<tr>
<td>절차를 워크플로 로직으로 변환</td>
<td>구조화한 분기와 연동</td>
<td>정해진 경로로 동작을 제어해야 할 때</td>
<td>예외와 분기를 계속 관리해야 한다</td>
</tr>
<tr>
<td>SOP에 실행 시점 검사 추가</td>
<td>절차와 도구·출력 검사</td>
<td>특정 규칙을 실행 전에 확인해야 할 때</td>
<td>검사 범위와 상태 처리를 구현해야 한다</td>
</tr>
</tbody>
</table>

Strands 샘플에는 첫째와 셋째 방식이 나온다. 둘째 방식은 Decagon 사례에서 볼 수 있다. 업무팀이 자연어로 절차를 적으면 구조화된 워크플로로 변환하고, 엔지니어가 연동과 실행 제약을 관리한다. 공급사가 공개한 설계 설명이다. 어느 방식이든 절차가 다루지 않는 요청을 만났을 때의 동작도 정해야 한다.<sup><a href="#ref-5">[5]</a></sup><sup><a href="#ref-11">[11]</a></sup>

## 자주 하는 일 하나에 써보면 어떨까요?

어떤 도구를 붙이기 전에, 평소 맡기는 일 하나의 절차를 적어 봐도 좋다. 가령 코딩 에이전트에게 기존 저장소의 버그 수정을 맡긴다면, ‘수정하고 검증해 주세요’를 아래처럼 풀어 쓸 수 있다.

<div class="highlight"><pre><span></span>범위: 기존 저장소에서 요청받은 버그 수정

1. 저장소 안내와 보고된 동작을 읽는다.
2. 문제를 재현하고, 막히면 이유를 기록한다.
3. 관련 코드와 관찰 가능한 완료 조건을 찾는다.
4. 원인을 해결하는 최소 변경을 한다.
5. 관련 검사를 실행하고 실제 결과를 남긴다.
6. 최종 diff를 요청 내용과 대조한다.
7. 변경 사항과 근거, 남은 한계를 보고한다.

멈추는 조건
- 동작을 결정하는 요구사항이 빠졌으면 물어본다.
- 외부 쓰기 결과가 불확실하면 다시 시도하기 전에 상태를 확인한다.
- 검사가 실패하면 실패를 보고한다. 검증됐다고 쓰지 않는다.

완료 근거
- 검토한 diff 또는 커밋 식별자
- 해당 코드 상태에 연결된 검사 결과
- 확인하지 못한 부분
</pre></div>

여기서 ‘검증한다’만 다시 들여다보자. 어떤 검사를 돌리고, 어느 코드 상태에서 통과했는지 남겨야 다음 사람이 같은 결과를 확인할 수 있다. 저장소마다 답이 다르니 이 부분을 구체적으로 채워야 한다. AWS는 Amazon 팀들이 코드 리뷰, 문서, 장애 대응, 모니터링 등에 수천 개의 Agent SOP를 쓴다고 보고했다. 어떤 일에 적용하는지는 공개했지만, 업무별 정확도는 제시하지 않았다.<sup><a href="#ref-12">[12]</a></sup>

## 절차를 써 뒀다면, 반품 요청을 어떻게 시험할까요?

채널톡의 2026년 6월 글에서는 주문 조회나 반품 작업을 시험하기 위해 그래프의 경로에서 시나리오를 뽑고 LLM에 고객 역할을 맡겼다. 에이전트가 API를 호출하는 단계에는 예상 결과를 넣어 줬다. 이렇게 하면 실제 반품을 접수하지 않고도 같은 상황을 여러 번 재현할 수 있다.<sup><a href="#ref-13">[13]</a></sup>

처음엔 예상한 마지막 단계에 도달하면 된다고 봤다. 그런데 에이전트가 엉뚱한 답을 하고도 그 단계에 도착할 수 있었다. 그래서 대화가 고객 의도를 해결했는지 따로 평가하고, 실패한 대화에서 수정안을 제안하는 에이전트를 붙였다. 글에서는 해결이 나아졌다고 설명하지만 전후 수치는 공개하지 않았다. 당시 이 개선 과정은 개념 검증(PoC) 단계였고, 제안된 변경은 사람이 검토한 뒤 적용했다.<sup><a href="#ref-13">[13]</a></sup>

## ‘끝났습니다’라는 말 뒤에 뭘 볼까요?

마지막 단계에 갔는지와 실제로 일을 잘 끝냈는지는 SOP-Bench v2에서도 따로 센다. 실행 가능한 도구와 사람이 검증한 정답을 써서 12개 업무 분야의 2,000개 넘는 과제를 평가했는데, 절차와 모델·에이전트 조합에 따라 결과가 크게 달랐다. 이때 끝까지 실행한 비율, 완료한 것 중 정답 비율, 전체 과제 성공률을 구분한다. 그럴듯하지만 불필요한 도구를 하나 더 넣었을 때 시험 절차의 성공률이 떨어진 사례도 있었다.<sup><a href="#ref-14">[14]</a></sup><sup><a href="#ref-7">[7]</a></sup>

직접 평가한다면 네 가지를 따로 기록해 보자.

<ol>
<li><strong>결과</strong> 요청한 상태가 실제로 올바르게 바뀌었나?</li>
<li><strong>절차</strong> 사전 확인과 필요한 인계를 했나?</li>
<li><strong>실행 범위</strong> 요청받지 않은 동작을 하지 않았나?</li>
<li><strong>비용</strong> 지연, 모델 사용량, 재시도, 사람 검토가 얼마나 들었나?</li>
</ol>

네 가지를 살피려면 정상 요청 외에도 입력이 빠졌을 때, 값이 잘못됐을 때, 도구가 실패했을 때를 넣어 본다. 애초에 절차를 시작하면 안 되는 요청도 있어야 어디서 멈추는지 볼 수 있다. 같은 사례를 반복하되 처음 보는 사례는 별도로 남겨 둔다. Strands의 평가 SOP는 이 일을 계획, 시험 데이터 생성, 실행, 결과 보고 순으로 정리한다.<sup><a href="#ref-15">[15]</a></sup>

처음의 배송 문의로 돌아가 보자. 조회에는 성공했는데 해결로 세지 않은 대화가 있다면, 그 대화부터 열어 보면 된다. 조회 결과를 설명하지 않았는지, 상담원에게 넘겨야 할 때 혼자 답했는지 살피면 절차에 무엇을 더 적어야 할지가 보인다.

## 참고 자료

<ol>
<li><a id="ref-1"></a>Pete, Channel Talk. <a href="https://tech.channel.io/kr/articles/tech-sop-generation-agent-5e13175f">상담 데이터 분석을 통해 메뉴얼 추출하기</a>. 2026년 4월 23일. 분석 에이전트 절차, 생성한 상담 SOP, ALF 설정 초안.</li>
<li><a id="ref-2"></a>Channel Talk. <a href="https://docs.channel.io/help/en/articles/Getting-started-fed198ac">Getting started</a>. 채팅과 상담 작업공간. 2026년 11월 5일 확인.</li>
<li><a id="ref-3"></a>Channel Talk. <a href="https://channel.io/kr/blog/articles/ai-chatbot-cs-a0113e03">AI 챗봇이란?</a>. 2026년 2월 5일. ALF 지식과 작업, 공식 ALF v2 영상.</li>
<li><a id="ref-4"></a>Clare Liguori. <a href="https://strandsagents.com/blog/steering-accuracy-beats-prompts-workflows/">How Steering Hooks Achieved 100% Agent Accuracy Where Prompts and Workflows Failed</a>. 2026년 3월 18일. 평가 결과, 여섯 가지 시나리오, 토큰 표.</li>
<li><a id="ref-5"></a>Strands Agents. <a href="https://github.com/strands-agents/samples/blob/3c9ebca88ad8906ca77147753d951c5e2a7123bd/python/05-technical-use-cases/steering/library-book-renewal-agent/README.md">Library Book Renewal Agent README</a>. 에이전트 구성, 평가기, 게이트웨이 정책 차이. 고정 리비전.</li>
<li><a id="ref-6"></a>Anthropic. <a href="https://claude.com/customers/gradient-labs">Gradient Labs transforms financial services customer support with Claude</a>. SOP 실행과 보고된 전체 해결률. 공급사가 공개한 사례.</li>
<li><a id="ref-7"></a>Rohith Nama and Subhrangshu Nandi. <a href="https://www.amazon.science/blog/sop-bench-a-new-benchmark-for-evaluating-ai-agents-on-real-business-procedures">SOP-Bench: A new benchmark for evaluating AI agents on real business procedures</a>. 2026년 8월 21일. SOP 정의, 절차별 차이, 도구 추가 실험.</li>
<li><a id="ref-8"></a>Strands Agents. <a href="https://github.com/strands-agents/agent-sop/blob/0b9014f4af467a06291886a0b316aef8c316dedb/README.md">Agent SOP format</a>. 개요, 매개변수, 제약, 배포. 2026년 11월 5일 확인.</li>
<li><a id="ref-9"></a>Strands Agents. <a href="https://github.com/strands-agents/samples/blob/3c9ebca88ad8906ca77147753d951c5e2a7123bd/python/05-technical-use-cases/steering/library-book-renewal-agent/src/library_agent_demo/agents/library_book_renewal.sop.md">Library book renewal SOP</a>. 적용 범위, 1–2단계, 확인 요건.</li>
<li><a id="ref-10"></a>Strands Agents. <a href="https://github.com/strands-agents/samples/blob/3c9ebca88ad8906ca77147753d951c5e2a7123bd/python/05-technical-use-cases/steering/library-book-renewal-agent/src/library_agent_demo/agents/sop_agent.py">SOP agent implementation</a>. SOP 내용을 시스템 프롬프트에 넣는 구현.</li>
<li><a id="ref-11"></a>Decagon. <a href="https://decagon.ai/blog/from-sops-to-agent-operating-procedures">Agent Operating Procedures: From Manual SOPs to Automated AI Logic</a>. 2025년 11월 26일. 자연어 절차를 워크플로로 변환하는 방식과 담당 범위.</li>
<li><a id="ref-12"></a>James Hood and Nicholas Clegg. <a href="https://aws.amazon.com/blogs/opensource/introducing-strands-agent-sops-natural-language-workflows-for-ai-agents/">Introducing Strands Agent SOPs</a>. 2025년 11월 20일. Amazon 내부 도입과 활용 사례.</li>
<li><a id="ref-13"></a>Mango, Channel Talk. <a href="https://tech.channel.io/kr/articles/tech-self-evolving-ai-workflow-23a19040">팀장님이 QA 100번 시키길래 만들었습니다.</a>. 2026년 6월 11일. 그래프 시나리오, 모의 사용자, API 모의 응답, 의도 평가, 사람 검토를 거친 개념 검증.</li>
<li><a id="ref-14"></a>Subhrangshu Nandi et al. <a href="https://arxiv.org/html/2506.08119v2">SOP-Bench: Complex Industrial SOPs for Evaluating LLM Agents, v2</a>. 2026년 2월 23일. 4.1절 평가 지표, 5절 결과와 구성 요소별 실험.</li>
<li><a id="ref-15"></a>Strands Agents. <a href="https://strandsagents.com/docs/user-guide/evals-sdk/eval-sop/">Evaluate with AI</a>. 평가의 네 단계. 2026년 11월 5일 확인.</li>
</ol>

### 이미지 출처

<ul>
<li><strong>상담 기록에서 ALF 설정까지</strong> · Pete의 2026년 4월 글을 바탕으로 작성한 흐름도.<sup><a href="#ref-1">[1]</a></sup></li>
<li><strong>대출 연장 전 필수 확인 항목</strong> · 원문 일부를 발췌해 형식을 정리했다(Apache-2.0). <a href="https://github.com/strands-agents/samples/blob/3c9ebca88ad8906ca77147753d951c5e2a7123bd/python/05-technical-use-cases/steering/library-book-renewal-agent/src/library_agent_demo/agents/library_book_renewal.sop.md">출처</a> · <a href="https://github.com/strands-agents/samples/blob/3c9ebca88ad8906ca77147753d951c5e2a7123bd/LICENSE">라이선스</a></li>
</ul>
