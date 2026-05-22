# Phase R14 — 논문 구성 및 초안 작성

## 목표
실제 실험 아티팩트에서 모든 논문 섹션 초안 작성 (자리 표시자 숫자 없음).

## 섹션 구조

1. **초록** — 25_PAPER_TITLE_CONTRIBUTIONS.md 기반 (X%와 Y×를 R7+R10 결과로 채움)
2. **서론** — 잘못된 dynamics 가설 지속; 4개 하위 문제
3. **관련 연구** — TD-MPC2, DreamerV3, HiP-RSSM, PLSM, ReDRAW, AdaWM, conformal-RL
   차별화 표는 22_NOVELTY_AND_THREATS.md 참조
4. **방법** — 3개 섹션: (a) 기본 WM, (b) falsification gate, (c) CIRCA 알고리즘
5. **실험** — 4축 지표; 4가지 알고리즘 비교; ablation 표; baseline 표
6. **토론** — 실패 모드, 열린 질문, 한계 (24_OPEN_QUESTIONS.md)
7. **결론** — 25_PAPER_TITLE_CONTRIBUTIONS.md의 5가지 기여 사항

## 불변 조건

- 어떤 섹션에도 자리 표시자 숫자 없음
- 모든 그림은 출력 아티팩트에서 생성됨 (수동으로 그린 그림 없음)
- 본문의 모든 주장은 지표 표에 해당 행이 있어야 함

## Agent Team 트리거
관련 연구 및 주장 섹션 초안 작성 전 T5 필요 (reviewer-2-attack-agent).
이미 완료됨: reviewer2_attack_fglc_R1.md — 논문 본문에 방어 통합.

## Gate 기준
- [ ] 7개 섹션 모두 초안 작성됨
- [ ] 주요 본문에 X% 자리 표시자 없음 (모두 실험에서 채워짐)
- [ ] 관련 연구 섹션에서 T5 agent team 리뷰 완료됨
- [ ] 최종 관련 연구 섹션에서 fglc-related-work-scout 실행됨
