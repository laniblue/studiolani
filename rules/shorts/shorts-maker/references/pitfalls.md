# 실제로 겪은 함정과 해결법

문제가 생겼을 때 먼저 이 목록을 확인한다. 모두 실제 제작 중에 나온 문제다.

## 환경
- **Homebrew `node@22`는 keg-only다.** 설치 후 `node: command not found`가 나오면 `export PATH="/opt/homebrew/opt/node@22/bin:$PATH"`를 쓰고, `~/.zprofile`에 한 줄 추가해 두면 다음부터 편하다. 모든 Bash 호출에서 이 export를 먼저 실행한다.
- **FFmpeg 7.1+(9.x 포함)는 `-filter_complex_script`가 없다.** 대신 `-/filter_complex <파일>`을 쓴다. `autocut.py`는 둘 다 시도한다.
- **Homebrew FFmpeg에 `drawtext`가 없을 수 있다.** 글자가 들어간 이미지는 FFmpeg 대신 HyperFrames 스냅샷으로 만든다.
- macOS 렌더는 `PRODUCER_BROWSER_GPU_MODE=hardware`로 한다. 소프트웨어 모드는 느리고, 브라우저 세션이 아예 안 뜰 수 있다("Browser session never ran").

## 전사 · 컷
- **Whisper는 문장 마지막 단어의 끝 시간을 다음 무음까지 늘린다.** 컷 지점은 Whisper 타임스탬프가 아니라 FFmpeg 무음 구간과 10ms RMS로 정한다.
- **속삭이는 대사는 -35 dB 무음 판정에 걸린다.** 실제로 "oh my gosh"가 그렇게 잘렸다. `autocut.py`는 150ms 평균 에너지가 바닥 잡음보다 7 dB 높으면 말소리로 보고, 그 부분은 자르지 않는다. 판정 기준을 "순간 최댓값"으로 하면 잡음에 걸리고, "계속 큼"으로 하면 속삭임을 놓친다.
- **재전사 비교는 같은 엔진끼리 한다.** 원본도 같은 `hyperframes transcribe`로 다시 전사해서 diff를 낸다. 엔진이 다르면 받아쓰기 차이가 누락처럼 보인다.
- Whisper가 실행마다 다르게 받아쓰는 부분(예: "let- let me" → "let me")은 누락이 아니다. 그 시점에 컷이 있을 때만 누락을 의심한다.
- **말더듬, 반복, 끊긴 문장이 개그인 콩트가 있다.** "마지막 테이크만 남기기"는 진짜 재촬영일 때만 적용하고, 판단이 애매하면 사용자에게 묻는다.

## 영상 · 레이아웃
- **원본에 박힌 자막·제목이 있는지 먼저 본다.** 화면을 1.5fps로 캡처해 한 장에 이어 붙이면(contact sheet) 바로 보인다. 영어 자막 띠는 `scaffold.py --lift`로 헤더 아래로 밀어 숨기고, 박힌 제목 카드와 우리 자막이 겹치지 않게 위치를 정한다.
- 박힌 자막은 번역의 1순위 원문이다. Whisper가 숫자나 이름을 틀려도 박힌 자막이 정답을 알려 준다.
- **소스 영상의 키프레임 간격이 넓으면 렌더할 때 화면이 멈춘다.** 항상 `-g 30 -keyint_min 30`으로 다시 인코딩한 `a-roll.mp4`를 쓴다. `scaffold.py`가 이 작업을 한다.
- 같은 영상 파일을 `<video>` 두 개에 쓰면 `duplicate_media_discovery_risk` 경고가 난다. 블러 배경은 별도의 작은 파일로 만든다.
- 일부러 화면 밖으로 넘치게 둔 요소(확대·크롭한 영상, 구름)에는 `data-layout-allow-overflow`를 붙인다.

## 편집 · 효과음
- 박힌 글자를 `boxblur`로 지우면 색 덩어리(빨간 카드 → 분홍 사각형)가 남는다. `delogo`로 주변 색을 채우고, 약한 블러로 줄무늬를 지운다(`blur_regions.py` 기본값).
- 효과음은 화면 비트에 맞추되, 대사 위에 얹히면 목소리를 덮는다. 렌더 후 `sfx_check.py`로 확인하고, 해당 이벤트만 볼륨을 낮춘다.
- 합성 효과음은 생성 방식에 따라 레벨이 -50 dB부터 0 dB까지 제각각이다. 피크 정규화(2-pass) 없이 쓰면 우시가 거의 안 들린다.
- 확대는 타임드 `<video>`가 아니라 감싸는 `#zoom` div에 건다. 미디어 요소 크기를 애니메이션하면 lint 오류가 난다.
- 유튜브 페이지는 Trusted Types 정책 때문에 `innerHTML` 대입이 막혀 있다. 프레임 시트를 표시할 때는 `removeChild`와 `appendChild`를 쓴다.

## 자막
- 자막 타이밍은 단어 시작점을 기준으로 잡는다. 컷과 자막 경계가 0.3초 안에 있으면 컷 프레임에 맞춘다(`qa.py --fix`).
- 외곽선 두께의 절반이 글자 바깥으로 나간다. 안전 영역 검사는 외곽선까지 포함해서 한다. 안전선은 title-safe x 108–972이고, 오른쪽은 인스타 버튼 줄을 피해 950까지만 쓴다.
- 줄바꿈 때문에 한 글자만 따로 떨어지면(예: "너 / 유당불내증…") 자막 상자를 넓히거나 문구를 다듬는다. `<br>`은 쓰지 않는다.

## HyperFrames · 스튜디오
- 서브 컴포지션은 `<template>` 안에 style·마크업·script를 모두 넣는다. `<head>`의 style은 버려진다.
- 서브 컴포지션 루트는 `#root`로 스타일한다. 클래스로 스타일하면 lint 오류가 난다.
- CSS `transform`과 GSAP scale/rotation을 같은 요소에 같이 쓰면 충돌한다. 회전 같은 값도 GSAP `fromTo` 안에 넣는다.
- 같은 요소에 `fromTo`를 여러 번 걸면 첫 번째를 뺀 나머지에 `immediateRender: false`를 준다. 아니면 `to`를 두 번 쓴다.
- **스튜디오(preview)는 파일에 `data-hf-id`를 덧붙이며 다시 쓴다.** 편집 전에는 파일을 새로 읽고, 정규식 치환은 이 속성이 붙어 있어도 맞도록 짠다.
- 미리보기 API(`/api/projects/<name>/preview`)는 캐시가 남는다. 측정할 때는 `?_t=<숫자>`를 붙인다.
- 2MB가 넘는 폰트는 번들에 인라인되지 않는다는 안내가 뜬다. 로컬 렌더에는 문제없다.
- 렌더 명령: `npx hyperframes render --quality high --output final-video.mp4` (high = delivery 품질).
