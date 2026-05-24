# Agent H — Experiment Design Chair (Synthesis) — PushCube Dataset

**상태**: PENDING — Agent A~G 보고서 모두 완료 후 populate  
**Phase**: R2 data pipeline → R3 진입 전  
**트리거**: Stage 4 Agent H (plans/fglc-step-vectorized-iverson.md §G.8)  
**담당**: area-chair-synthesis-agent (필수, deep mode)  
**입력**: Agent A~G 7개 보고서  

---

## Reviewer 관점 종합 검증 (예정)

| 질문 | 판정 | 근거 |
|---|---|---|
| threshold를 낮춰 통과시킨 것처럼 보이는가? | PENDING | delta_min=0.01 유지 확인 필요 |
| PickCube mass FAIL 명시했는가? | PENDING | negative result 공시 확인 |
| 두 task 조합 정당성 방어 가능한가? | PENDING | Agent E I1~I7 검토 |
| H1~H15 gate 모두 PASS인가? | PENDING | Agent A~D 집계 |

## 집계 결과 (Stage 4 완료 후)

| Agent | 판정 |
|---|---|
| A (data-quality) | PENDING |
| B (split-leakage) | PENDING |
| C (ood-severity) | PENDING |
| D (dynamics-forensics) | PENDING |
| E (novelty-relevance) | PENDING |
| F (training-readiness) | PENDING |
| G (resource-budget) | PENDING |

## Negative Result 공시 의무 확인

PickCube mass OOD FAIL (gap=0.004, contact_rate=0.0%):
- 이 결과는 논문 Section 4에 반드시 명시.
- "PickCube+random policy에서 mass shift가 dynamics에 미치는 영향이 없음"을 투명하게 기록.
- PushCube로 task 변경한 이유를 방법론 섹션에 설명.
- **숨김 없음** — 이 보고서에서 기록으로 확인됨.

## 최종 판정

**PENDING** — Stage 4 Agent A~G 완료 후 채워질 것.

최종 판정 기준:
- ANALYSIS_PASS: Agent A~G 모두 PASS/CONDITIONAL_PASS, negative result 공시 확인
- PATCH_REQUIRED: 일부 FAIL → repair loop → 재수집
- BLOCKED: contact_rate < 5% (PushCube도 부적합) → task 재고 → 사용자 escalation
