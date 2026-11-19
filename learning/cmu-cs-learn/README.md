# CMU CS Learn · 한국어 독학 가이드

카네기멜론에서 공개하는 컴퓨터과학 강의를 관심 분야와 학습 목표에 맞춰 찾는 비공식 인덱스입니다. 2026-11-19에 [CMU 공식 강의 목록](https://www.cs.cmu.edu/learn/)을 확인했습니다. YouTube 공개 과목 8개와 2027년 1월 공개 예정 과목 5개를 구분했습니다. 영상을 무료로 보는 것과 정규 수강·인증은 별개이며, 자가 학습 교재와 AI 튜터는 공식 안내상 이후 공개 예정입니다.

**[학습실 바로가기](https://yongkilee.com/learning/cmu-cs-learn/)**

## 추천 학습 경로

| 목표 | 추천 순서 | 남길 결과물 |
| --- | --- | --- |
| AI 에이전트를 만들고 운영하기 | 11-768 AI Agents → 17-645 ML in Production → 15-442 ML Systems | 읽기 전용 에이전트의 평가 케이스, 운영 지표, 서빙 지연 비교 |
| 백엔드 설계·테크 리드 | 17-214 Software Construction → 17-635 Software Architectures → 17-643 Quality Management | 아키텍처 결정 기록 하나와 릴리스 체크리스트 |
| 컴퓨터과학·ML 기초 새로 시작 | 15-110 Computing → 15-259 Probability → 07-280 AI and ML I → 10-605 Large Datasets | 기초 Python 연습 후 작은 데이터로 기준 모델과 검증 결과 재현 |

위 순서와 실습 아이디어는 독학용 제안입니다. 공식 선수 조건은 각 강의계획서를 참고하세요. 아직 공개 전인 과목은 연습만 먼저 하거나 공개 후 이어갈 수 있습니다.

## 과목 색인

### YouTube 공개 · 8개

- **11-768** AI Agents · [강의진 과목 사이트](https://www.cmu-agents.com/)
- **17-645** Machine Learning in Production · [강의진 과목·교재](https://mlip-cmu.github.io/)
- **15-442** Machine Learning Systems · [강의진 과목 사이트](https://mlsyscourse.org/)
- **17-635** Software Architectures · [CMU 공개 강의 목록](https://www.cs.cmu.edu/learn/)
- **17-214** Principles of Software Construction · [강의진 봄 학기 보충 자료](https://cmu-17-214.github.io/s2026/)
- **17-643** Quality Management · [CMU 공개 강의 목록](https://www.cs.cmu.edu/learn/)
- **10-605** Machine Learning with Large Datasets · [강의진 과목 사이트](https://10605.github.io/)
- **15-110** Principles of Computing · [CMU 강의계획서](https://www.cs.cmu.edu/~15110/syllabus.html)

### 2027년 1월 공개 예정 · 5개

- **15-259** Probability and Computing
- **11-777** Multimodal Machine Learning · [가을 학기 보충 자료](https://multicomp.cs.cmu.edu/mmml-course/fall2026/)
- **07-280** AI and Machine Learning I
- **17-619** Product Management Essentials
- **17-627** Requirements for Embedded Systems

## 학습실 사용

홈페이지 저장소 루트에서 `make serve`를 실행한 뒤 `http://127.0.0.1:8000/learning/cmu-cs-learn/`을 여세요. 한국어·영어 과목명, 과목 코드, 교수와 주제로 검색하고, 주제·공개 여부·학습 상태를 함께 거를 수 있습니다.

- **영상 탐색:** 썸네일과 제목에서 바로 강의로 들어가세요. 상단 검색과 주제 필터가 과목명, 영상 제목, 한국어 요약을 검색합니다. 영상 링크는 같은 사이트 안에서 특정 강의로 이어집니다.
- **이어서 학습:** 마지막으로 연 공개 과목에서 체크하지 않은 다음 단계(공식 강의, 미니 실습, 복습 노트)를 엽니다.
- **페이지 안에서 강의 보기:** 8개 공개 과목에서 공식 재생목록에 포함된 개별 영상과 노트를 고릅니다. 플레이어는 버튼을 누를 때만 개인 정보 보호 강화 모드로 불러옵니다. 영어 자막이 제공되는 영상에는 재생 시 표시를 요청하며, 제공 여부와 언어는 각 영상의 CC 및 설정을 따릅니다. 한국어 자막이나 자동 번역은 보장하지 않습니다.
- **영상별 학습 노트:** 요약·핵심 포인트·근거·참고자료를 구분하고, 시각은 공식 게시자가 제공한 챕터 등 확인된 것만 연결합니다. 표기된 작성 근거를 참고하세요. 자막이나 전체 강의 발화를 복제하지 않습니다.
- **진도와 노트:** 강의 시청은 자동으로 기록하지 않습니다. 독학 체크리스트에 직접 표시하며, 진행과 복습 노트는 같은 브라우저에만 저장합니다. 예전 진도는 같은 도메인과 브라우저에서 이어지지만 서로 다른 도메인 간 브라우저 저장소는 공유되지 않습니다.

### 학습실 디자인 참고

- [HackerTube AI](https://hackertube.ai/): 흰 배경과 상단 검색, 영상 중심 그리드, 상세 화면의 플레이어 아래 요약 및 오른쪽 연결 강의 구조를 참고했습니다. 썸네일과 길이는 공식 CMU YouTube 영상에서 확인했으며, 외부 플레이어는 선택 후에만 로드됩니다.

- [CLASS101](https://blog.class101.net/press_250421/): 첫 화면에서 직전 과목으로 복귀.
- [Open edX](https://edx.readthedocs.io/projects/open-edx-learner-guide/en/stable/SFD_start_course.html): 과목 목차와 다시 시작할 위치를 나란히 제공.
- [Coursera](https://www.coursera.support/s/article/learner-000002219?language=en_US): 목표별 학습 경로와 진도를 분리.
- [Moodle](https://docs.moodle.org/503/en/course/report/progress/index): 활동별 수동 완료 표시.

단일 홈페이지 Pages 빌드가 이 모듈의 결과를 `dist/learning/cmu-cs-learn/`에 넣습니다. 이전 공개 주소들은 새 주소를 가리킵니다.

## 목록 유지보수

`catalog.json`이 기본 데이터입니다. 공식 목록에서 공개 상태와 링크를 확인한 다음 이 파일을 수정하고 홈페이지 루트에서 `make build`로 게시용 파일을 다시 생성하세요. 링크가 강의진의 정규 학기 자료라면 CS Learn 영상과 구분해 표시합니다. 공식 재생목록 영상 ID·제목·자막 확인 상태는 `video-index.json`, 독립적으로 작성한 요약과 출처는 `lesson-notes/*.json`에 저장합니다. 영상 ID는 등록된 공식 영상과 매칭해야 하고, 확인하지 않은 발화나 타임스탬프는 쓰지 않습니다. 글과 미니 실습은 별도 작성했으며 영상·슬라이드·자막을 복제하지 않습니다.

```sh
make check
make build
```
