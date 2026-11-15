# 핑크 토끼 30초 숏폼 콘티 — "찡그린 토끼의 선물"

> 레퍼런스: `ref/bunny-front.png` (캐릭터), `ref/stage-A_stream-forest.png` (무대 A)
> 화면 비율 9:16 / 컷당 3~5초 / 총 9컷 / 약 32초

## 이야기 한 줄
늘 찡그리고 다니는 토끼가 개울에서 반짝이는 조약돌을 주워, 마을 친구 집 앞에 몰래 두고 숨는다. 친구가 기뻐하는 걸 보고 처음으로 살짝 웃는다.
(마지막에 찡그린 얼굴이 풀리는 게 포인트. 캐릭터 성격이 생김)

---

## 0단계. 고정 문구 (모든 프롬프트 앞에 그대로 붙이기)

**CHARACTER**
```
a small chibi pink bunny character, flat solid pink body, thick black outline,
long upright ears with a small notch between them, angry furrowed eyebrows,
tiny dot eyes, small "w"-shaped mouth, one round white patch on the belly,
short stubby arms and legs, no clothes
```

**STYLE**
```
cute flat 2D cartoon illustration, thick clean black outlines, soft pastel colors,
no gradients on the character, storybook background, consistent character design
```

**NEGATIVE** (지원되는 모델에서만)
```
realistic, 3d render, fur texture, extra limbs, different face, clothes, text, watermark
```

> ⚠️ 배 무늬가 프레임마다 흔들렸으니 "one round white patch on the belly"는 절대 빼지 말 것.

---

## 1단계. 캐릭터 시트 (이미지 모델, 레퍼런스: bunny-front.png)
```
[CHARACTER] character turnaround sheet on plain white background:
front view, side view, back view, sitting, smiling face, surprised face.
[STYLE]
```
→ 잘 나온 걸 `ref/bunny-sheet.png`로 저장. 이후 모든 생성에 레퍼런스로 넣기.

## 2단계. 무대 이미지 (배경만, 캐릭터 없음)
- **무대 A — 개울 숲 (낮)**: 기존 `stage-A_stream-forest.png` 그대로 사용
- **무대 B — 마을 친구 집 앞 (낮)**
  ```
  a cozy small cottage with a blue roof and a round wooden door, flower pots,
  dirt path, green hills behind, same art style as reference, no characters. [STYLE]
  ```
  (레퍼런스: 무대 A → 그림체 맞추기 용)
- **무대 B' — 같은 집 앞 (노을)**: 무대 B를 레퍼런스로 "same scene at sunset, warm orange sky"

---

## 3단계. 컷 리스트

| # | 시간 | 무대 | 샷 | 장면 (이미지 프롬프트 요지) | 움직임 (영상 프롬프트) |
|---|---|---|---|---|---|
| 1 | 0–4s | A | 와이드 | 토끼가 개울을 첨벙첨벙 건너는 중 (기존 영상 그대로 재사용 가능) | bunny walks through shallow stream, small water ripples, static camera |
| 2 | 4–7s | A | 클로즈업 | 물속에서 반짝이는 하트 모양 조약돌, 토끼 발 끝 | stone sparkles, gentle water flow, slow push-in |
| 3 | 7–11s | A | 미디엄 | 토끼가 조약돌을 두 손으로 들고 찡그린 얼굴로 바라봄 | bunny lifts stone, tilts head, stone glints |
| 4 | 11–14s | B | 와이드 | 마을 집 앞 길을 토끼가 조약돌 안고 걸어옴 | bunny walks toward the house, static camera |
| 5 | 14–17s | B | 미디엄 | 문 앞 계단에 조약돌을 살짝 내려놓음 | bunny gently places stone on doorstep, looks around |
| 6 | 17–21s | B | 와이드 | 화분 뒤에 숨어 귀만 쏙 나와 있음 | bunny hides behind flower pot, ears twitch |
| 7 | 21–25s | B | 미디엄 | 문 열리고 친구(흰 병아리)가 조약돌 발견, 깡충 | door opens, small chick finds stone and hops happily |
| 8 | 25–29s | B | 클로즈업 | 화분 뒤 토끼 얼굴 — 눈썹이 풀리며 살짝 미소 | eyebrows relax, small shy smile, blush appears |
| 9 | 29–32s | B' | 와이드 | 노을 길을 혼자 걸어가는 토끼 뒷모습 (루프용: 1번 컷과 비슷한 방향) | bunny walks away down the path, sunset, slow pull-back |

> 친구 캐릭터(흰 병아리)도 1단계처럼 시트 1장 만들어서 레퍼런스로 넣을 것.
> 8번 컷이 감정 포인트 → 시작 프레임(찡그림) + 끝 프레임(미소) 두 장 지정하는 방식이 가장 안정적.

---

## 4단계. 생성 규칙 (일관성 체크리스트)
- [ ] 장면 이미지는 **항상 캐릭터 시트 + 해당 무대 이미지** 두 장을 레퍼런스로 넣는다
- [ ] 이미지 단계에서 귀 노치 / 찡그린 눈썹 / 배 흰 동그라미 / 핑크 단색 4개 확인. 하나라도 틀리면 버린다
- [ ] 컷당 3~4장 뽑고 1장 고르기
- [ ] 영상은 반드시 image-to-video, 3~5초, 움직임 한 가지만
- [ ] 카메라는 고정 또는 아주 느린 push-in/pull-back만
- [ ] 와이드 → 클로즈업 → 와이드 순서로 섞기 (와이드에서 작은 오류는 안 보임)
- [ ] 마지막에 업스케일 (1080×1920)

## 5단계. 편집
- 컷 사이 하드컷, 8번 컷 앞에만 0.3초 정적
- 잔잔한 어쿠스틱/오르골 음악, 7번 컷에 효과음(뿅)
- 자막 최소: 8번 컷에 "..." 정도
