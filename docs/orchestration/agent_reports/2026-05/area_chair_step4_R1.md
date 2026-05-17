# area_chair_step4_R1.md

**Agent**: area-chair-synthesis-agent
**Trigger**: T4 (결과 해석 전)
**Date**: 2026-05-17
**Scope**: STEP 4 smoke eval (v0_3, 3 episodes, random-init)

## Final Verdict: MAJOR_REVISION → SENTINEL_WARN (조건부 발행)

## Claim 상태

| Claim | 상태 | 비고 |
|---|---|---|
| FC-01 (C1 persistence) | PARTIALLY_ACCEPTABLE | evidence_ts fixed; v1 BLOCKED by namespace; smoke-only |
| FC-03 (C3 falsification) | ACCEPTABLE (scope-limited) | PR/F1=0.0 random-init artifact; disclosure 올바름 |
| FC-04 (C4 rollout fidelity) | NOT_ACCEPTABLE (deferred) | MET-WM-001 absent; STEP 5 Task #1 |
| FC-05 (C5 calibration) | CONDITIONALLY_ACCEPTABLE | ECE disclosure 올바름; wording 주의 필요 |

## SENTINEL_WARN 발행 조건

| 조건 | 상태 |
|---|---|
| 82 tests green (pytest) | CONFIRMED (82 passed in 2.41s) |
| blocked_metric_count=33 = 11×3 intentional | CONFIRMED |
| BASE-026/027/028 stub status 문서화 | DONE (22_step5_handoff.md §3.9) |

## TOP 3 STEP 5 Priorities

1. Pre-training checkpoint (STEP 5 §3.4) — 모든 claim의 전제조건
2. MET-WM-001 alternative_rollout_fidelity() 구현 (§3.1) — FC-04 CRITICAL
3. Namespace alignment B0a 해소 (§3.6) — C1 v1 metric BLOCKED 해소

## 논문 Draft 허용 wording 수준

- FC-01: "random-init smoke baseline, 3-step episodes; v1 metric BLOCKED"
- FC-03: "constant-predictor artifact at random init; trained eval deferred to STEP 5"
- FC-04: "counterfactual data in v0_3; MET-WM-001 metric function deferred to STEP 5"
- FC-05: "ECE=0.025 is infrastructure reference artifact (valid_trained_eval=False)"
