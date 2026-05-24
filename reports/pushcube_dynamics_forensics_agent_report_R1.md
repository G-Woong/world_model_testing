# Agent D — Dynamics Forensics Report (PushCube-v1)

**상태**: PENDING — Stage 3 PushCube full collection 완료 후 populate  
**Phase**: R2 data pipeline → R3 진입 전  
**트리거**: Stage 4 Agent D (plans/fglc-step-vectorized-iverson.md §G.4)  
**담당**: failure-interpretation-critic  
**입력**: PushCube-v1 5 HDF5 + collector.py  

---

## 핵심 검사: contact_rate (H10)

**이것이 PushCube 채택의 핵심 근거.**  
PickCube random policy에서 contact_rate = 0.0% (tcp_dist=0.999m).  
PushCube에서 contact_rate > 30%여야 mass dynamics가 의미 있음.

| Split | contact_rate (tcp<5cm) | tcp_dist_mean | 판정 |
|---|---|---|---|
| train_id | PENDING | PENDING | — |
| ood_mass_low | PENDING | PENDING | — |
| ood_friction_low | PENDING | PENDING | — |

## Per-dim Cohen's d 상위 10 (mass-sensitive dims)

| Dim | Cohen's d (ID vs ood_mass_low) | 물리 해석 |
|---|---|---|
| PENDING | PENDING | PENDING |

## Action-response Correlation

| Split | action_norm_mean | state_delta_norm_mean | correlation |
|---|---|---|---|
| train_id | PENDING | PENDING | PENDING |
| ood_mass_low | PENDING | PENDING | PENDING |

## PickCube 대조

| Task | contact_rate | tcp_dist_mean | mass-sensitive dims |
|---|---|---|---|
| PickCube-v1 | 0.0% | 0.999m | 0 (dim24 artifact) |
| PushCube-v1 | PENDING | PENDING | PENDING |

## 판정

**PENDING** — Stage 3 완료 후 채워질 것.

최종 판정 기준 (H10):
- PASS: contact_rate > 30% AND mass-sensitive dims ≥ 3개 (\|d\| > 0.3)
- BLOCKED: contact_rate < 5% → PushCube도 부적합 → task 재고 → 사용자 escalation
