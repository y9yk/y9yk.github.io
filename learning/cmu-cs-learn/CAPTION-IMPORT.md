# 편집자용 자막 가져오기 (게시 금지)

이 도구는 편집자가 권한을 가진 자막을 **로컬에서** 시간순 검토하는 용도입니다.
가져온 JSON에는 자막 본문이 있으므로 저장소, `dist/`, 공개 문서, 커밋에 넣지 않습니다.
정적 사이트 빌드·CI·브라우저 기능에서 이 도구를 호출하지 않습니다. 자막 접근과 자막 재게시 허락은 별개입니다.

저장소 루트에서 다음처럼 실행합니다. 출력 디렉터리는 Git 밖에 두고 본인만 접근할 수 있게 준비합니다.

```sh
mkdir -p -m 700 "$HOME/cmu-caption-review"
python3 scripts/import_cmu_captions.py \
  --video-id KQUtNJEzUxU --language en --track manual \
  --input "$HOME/cmu-caption-review/authorized.en.vtt" \
  --output "$HOME/cmu-caption-review/KQUtNJEzUxU.en.json"
```

- 입력은 UTF-8 WebVTT 또는 SRT (8 MiB 이하), 영상은 `video-index.json`에 등록된 YouTube ID만 지원합니다. 로컬 입력의 영상·언어·트랙 일치는 편집자 진술이며 도구가 별도 확인하지 않습니다.
- YouTube 자동 자막에는 `--track auto`를 지정합니다. 시간이 겹치는 큐의 이전 끝과 다음 시작에 같은 어절이 있으면 반복 표시로 보고 제거합니다. 겹치지 않는 반복은 유지합니다. 자동 트랙의 인라인 시각이 있으면 이를 사용하며, 없으면 원래 큐 시작 시각을 사용합니다. 화자별 정렬이나 음성 검증은 하지 않습니다.
- JSON은 영상 ID·언어·트랙, 원본 SHA-256·입력 형식·가져온 시각·수집 방법, 밀리초 단위 큐를 담습니다. 로컬 파일의 경로는 기록하지 않고 기존 파일은 덮어쓰지 않습니다.

## 선택: 공개 트랙 직접 가져오기

[yt-dlp 공식 배포판](https://github.com/yt-dlp/yt-dlp#installation)이 이미 설치된 환경에만 해당합니다.
플랫폼 및 권리자의 허가 범위에서 공개 접근이 가능한 경우, `--input` 대신 `--fetch`를 명시합니다.

```sh
python3 scripts/import_cmu_captions.py \
  --video-id KQUtNJEzUxU --language en --track manual --fetch \
  --output "$HOME/cmu-caption-review/KQUtNJEzUxU.en.fetched.json"
```

정확히 지정한 한 영상·한 언어·한 트랙만 요청합니다. 미디어 파일은 내려받지 않습니다.
자막은 임시 디렉터리를 이용해 처리하고, 종료 시 정리합니다. 쿠키·계정·외부 토큰·지역 제한 우회와 설정·플러그인·외부 런타임 구성 요소 다운로드를 사용하지 않습니다.
로그인·봇 확인·접근 제한·요청 제한이 표시되면 재시도 없이 중단합니다. 자막이 없거나 타임아웃(최대 60초)이 발생하면 가져오지 않습니다. 그 경우 이미 권한을 가진 로컬 파일을 이용하거나 공식 플레이어에서 확인하세요. 트랙이 확인되지 않은 경우 다른 언어 또는 자동 번역으로 대체하지 않습니다.

검증: `python3 -m unittest discover -s tests -p test_import_cmu_captions.py`.
