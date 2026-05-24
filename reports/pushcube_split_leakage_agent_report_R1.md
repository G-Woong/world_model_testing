# Agent B — Split Leakage Auditor Report (PushCube-v1)

**상태**: PENDING — Stage 3 PushCube full collection 완료 후 populate  
**Phase**: R2 data pipeline → R3 진입 전  
**트리거**: Stage 4 Agent B (plans/fglc-step-vectorized-iverson.md §G.2)  
**담당**: split-leakage-auditor  
**입력**: PushCube-v1 manifest.json seed pools + 5 HDF5 trajectory hashes  

---

## 검사 항목

| Gate | 기준 | 결과 | 판정 |
|---|---|---|---|
| seed overlap (H8) | 빈 집합 (PickCube 42-650과 비겹) | PENDING | — |
| intra-split hash duplicate (H7 intra) | 0 | PENDING | — |
| inter-split hash duplicate (H7 inter) | 0 | PENDING | — |
| regime contamination (H9) | regime_id 추론 input 부재 | PENDING | — |
| forbidden field (H9) | test_fglc_forbidden_field_sync.py green | PENDING | — |

## Seed Pool 교집합 분석

- PickCube-v1 seed pools: 42-650 (train/val/test/ood×2)
- PushCube-v1 계획 seed pools: 1042-1999 (disjoint)
- 교집합: **공집합 (설계상 보장)** — manifest.json 생성 후 재확인

## 판정

**PENDING** — Stage 3 완료 후 채워질 것.

최종 판정 기준:
- PASS: 모든 leakage 검사 0건
- FAIL: 어느 하나라도 > 0
