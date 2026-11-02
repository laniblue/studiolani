---
name: shorts-autofix-checks
description: 오피스 쇼츠 컷 편집은 검사 항목을 스스로 고쳐서 통과한 결과로 나와야 함 — 경고만 띄우면 안 됨
metadata:
  node_type: memory
  type: feedback
  originSessionId: ec69c552-ae5a-4604-a276-7ab20a6af6b8
  modified: 2026-10-23T00:53:08.581Z
---

오피스 쇼츠는 컷 편집 체크리스트(첫 음절·문장 끝·반복·호흡·입 모양 튐)를 애초에 다 충족한 상태로 나와야 한다. 검사해서 경고만 띄우는 건 안 된다.

**Why:** 대표님 2026-10-23 "애초에 이 모든걸 충족하게 작업이 나와야함. 떡상영상 분석해서 된다매". 경고 5개 뜬 화면 보고 화냄.

**How to apply:** 새 검사 항목을 넣을 땐 자동으로 고치는 로직도 같이 넣는다(scripts/cutcheck.py polish + make-shorts.py 자동 다시 자르기 최대 2번). 정말 사람 눈이 필요한 것만 남기고, 남기면 이유를 같이 보여 준다. [[shorts-confirmed-workflow]]
