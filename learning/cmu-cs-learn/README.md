# CMU CS Learn · 한국어 독학 가이드

카네기멜론에서 공개하는 컴퓨터과학 강의를 관심 분야와 학습 목표에 맞춰 찾는 비공식 인덱스입니다. 2026-11-19에 [CMU 공식 강의 목록](https://www.cs.cmu.edu/learn/)을 확인했습니다. YouTube 공개 과목 8개와 2027년 1월 공개 예정 과목 5개를 구분했습니다. 영상을 무료로 보는 것과 정규 수강·인증은 별개이며, 자가 학습 교재와 AI 튜터는 공식 안내상 이후 공개 예정입니다.

**[학습실 바로가기](https://yongkilee.com/learning/cmu-cs-learn/)**

## 추천 학습 경로

| 목표 | 추천 시청 순서 |
| --- | --- |
| AI 에이전트와 운영 | 11-768 AI Agents → 17-645 ML in Production → 15-442 ML Systems |
| 백엔드와 테크 리드 | 17-214 Software Construction → 17-635 Software Architectures → 17-643 Quality Management |
| 컴퓨터과학과 ML 기초 | 15-110 Computing → 15-259 Probability → 07-280 AI and ML I → 10-605 Large Datasets |

위 순서는 강의를 살펴보는 데 도움이 되는 제안이며 공식 선수 조건은 각 강의계획서를 참고하세요.

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

- **탐색과 과목:** 탐색 홈은 추천 영상, 주제, 공개 과목을 보여줍니다. 카드의 노트·구간·출처 표시는 확인된 자료의 범위이며 커뮤니티 지표가 아닙니다. ‘나에게 맞는 강의’는 한국어·영어 관심사나 공식 CMU YouTube 링크를 브라우저에서만 맞춰 보며, 관심 주제·자료 유형·세부 태그로도 탐색할 수 있습니다. ‘최근 공개’는 공식 게시 시각이 확인된 영상에서 첫 추천 목록과 겹치지 않는 영상을 보여줍니다. 별도 과목 화면에서 전체 목록과 추천 학습 경로를 볼 수 있습니다. 상단 검색은 영상 제목, 요약, 개념, 확인된 구간을 찾으며, 구간에 해당하면 재생 버튼이 있는 위치로만 이동합니다. 자동으로 재생하지 않습니다.
- **내 학습:** 별도 화면에서 영상별 수동 시청 완료와 나중에 볼 목록을 관리하고 최근 과목의 영상을 이어서 볼 수 있습니다.
- **페이지 안에서 강의 보기:** 8개 공개 과목에서 공식 재생목록에 포함된 개별 영상과 노트를 고릅니다. 선택한 공식 썸네일을 먼저 표시하고, 플레이어는 재생 버튼을 누를 때만 개인 정보 보호 강화 모드로 불러옵니다. 탐색 카드에 마우스를 올리면 확인된 공식 대체 이미지가 표시됩니다. 영어 자막이 제공되는 영상에는 재생 시 표시를 요청하며, 제공 여부와 언어는 각 영상의 CC 및 설정을 따릅니다. 한국어 자막이나 자동 번역은 보장하지 않습니다.
- **강의 상세:** 플레이어를 유지하면서 `강의 노트`, `핵심 구간`, `출처`를 전환할 수 있습니다. 6개 강의에는 56개 확인된 구간과 개념 설명·풀이 예시가 있습니다. 강의 상세 위쪽에는 해당 영상을 볼 이유, 강의의 내용, 연결된 근거가 먼저 나옵니다. 4개 강의의 ‘영상 없이 읽는 강의’는 공개 스크립트 주요 구간과 강의 자료를 대조한 한국어 해설로, 핵심 결론·구간별 요지·키워드·주제·검색용 태그를 제공합니다. 핵심 구간 탭에서는 대표 3개를 먼저 보여줍니다. 경계는 게시자 제공 챕터 또는 확인된 영상 길이이며, 발화 단위의 타이밍은 아닙니다.
- **영상별 학습 노트:** 요약·핵심 포인트·근거·참고자료를 구분하고, 시각은 공식 게시자가 제공한 챕터 등 확인된 것만 연결합니다. 표기된 작성 근거를 참고하세요. 자막이나 전체 강의 발화를 복제하지 않습니다.
- **시청 기록:** 실제 재생 시간을 자동 추적하지 않습니다. 영상마다 직접 완료를 표시하며, 기록은 같은 브라우저에만 남습니다. 이전 체크리스트와 개인 메모는 삭제하지 않고 기존 브라우저 저장소에 남겨 두지만 화면에는 표시하지 않습니다.

### 학습실 디자인 참고

- [Readray(구 LilysAI)](https://readray.ai/ko): 영상과 학습 자료를 나란히 열고, 노트의 시각 표시에서 원본 구간으로 이동하는 방식.

- [HackerTube AI](https://hackertube.ai/): 흰 배경과 상단 검색, 영상 중심 그리드, 상세 화면의 플레이어 아래 요약 및 오른쪽 연결 강의 구조를 참고했습니다. 썸네일과 길이는 공식 CMU YouTube 영상에서 확인했으며, 외부 플레이어는 선택 후에만 로드됩니다.

- [CLASS101](https://blog.class101.net/press_250421/): 첫 화면에서 직전 과목으로 복귀.
- [Open edX](https://edx.readthedocs.io/projects/open-edx-learner-guide/en/stable/SFD_start_course.html): 과목 목차와 다시 시작할 위치를 나란히 제공.
- [Coursera](https://www.coursera.support/s/article/learner-000002219?language=en_US): 목표별 학습 경로와 진도를 분리.
- [Moodle](https://docs.moodle.org/503/en/course/report/progress/index): 활동별 수동 완료 표시.

단일 홈페이지 Pages 빌드가 이 모듈의 결과를 `dist/learning/cmu-cs-learn/`에 넣습니다. 이전 공개 주소들은 새 주소를 가리킵니다.

## 목록 유지보수

`catalog.json`이 기본 데이터입니다. 공식 목록에서 공개 상태와 링크를 확인한 다음 이 파일을 수정하고 홈페이지 루트에서 `make build`로 게시용 파일을 다시 생성하세요. 링크가 강의진의 정규 학기 자료라면 CS Learn 영상과 구분해 표시합니다. 추천 순서·주제·태그·과목·관련 강의 관계는 `feed_model.py`가 확인 가능한 근거에서 구성합니다. 공식 공개 시각·채널 검증 스냅샷은 `feed-source-snapshot.json`, 강의별 편집 설명과 검증된 직접 근거는 `editorial-guides.json`에 담았습니다. 공식 재생목록 영상 ID·제목·자막 확인 상태는 `video-index.json`, 독립적으로 작성한 요약과 출처는 `lesson-notes/*.json`, 검증된 시작·종료와 추가 학습 자료는 `lesson-briefings/*.json`에 저장합니다. 영상 ID는 등록된 공식 영상과 매칭해야 하고, 확인하지 않은 발화나 타임스탬프는 쓰지 않습니다. 자막 대조 요약은 `lecture-digests.json`에 출처와 함께 저장합니다. 선택적 [yt-dlp 또는 로컬 VTT/SRT 검토](CAPTION-IMPORT.md)는 게시 빌드와 분리됩니다. 한국어 설명과 개념 예시는 별도 작성했으며 영상·슬라이드·자막을 복제하지 않습니다.

```sh
make check
make build
```
