# failure_interp_step4_smoke_R1.md

**Agent**: failure-interpretation-critic
**Trigger**: T4 (결과 해석 전)
**Date**: 2026-05-17
**Note**: 이 agent는 OLD `p3_lr_real_eval_smoke` (STEP 3, v0_1)를 일부 참조했음.
          STEP 4 smoke = `p3_lr_real_eval_step4_smoke` (v0_3). 아래 corrections 반영.

## Claim Status (수정 포함)

| Claim | Status | Notes |
|---|---|---|
| C1 persistence | BLOCKED (STEP 4) | v0_3 hypothesis_update_timestamp_coverage=0% (backfill 미적용) |
| C3 falsification f1 | WEAKENED | f1=0.412 is constant-predictor artifact (FRCG-LR predicts "wrong" always) |
| C4 rollout fidelity | BLOCKED | C4_rollout_fidelity metric 함수 absent |
| C5 calibration | BLOCKED in STEP 4 | selected_hypothesis_confidence_coverage=0% in v0_3 |
| C6 compute gate | NOTE | tau_f=0.5 ✓ in STEP 4 (agent corrected per_step 확인) |

## STEP 5 Critical Blockers (from this audit)

**B1 (CRITICAL)**: v0_3 dataset hypothesis_update_timestamp/recovery_timestamp backfill 미적용 → C1/C3_recovery_delay BLOCKED

**B2 (TRACKED NEGATIVE)**: ABL-017 inversion (rewrite module increases failed repetition in untrained state) — consistent STEP 3 + STEP 4

**B3 (DATA GAP)**: v0_3 selected_hypothesis_confidence_coverage=0% → C5 ECE not evaluable on v0_3

## Corrections to agent analysis

- `tau_f=null` → **INCORRECT**: STEP 4 smoke shows `tau_f=0.5` (correct from B4 wire-up)
- `source=v0_1` → **INCORRECT**: STEP 4 smoke source is `data/frcgw_text/v0_3/test_id.jsonl`
- `counterfactual_coverage=0.0` → **INCORRECT for STEP 4**: v0_3 smoke shows counterfactual_coverage > 0% (v0_3 has counterfactuals)
- `blocked_metric_count=66` → **INCORRECT**: STEP 4 smoke shows 33 (11 agents × 3 BLOCKED)

Agent analyzed OLD `p3_lr_real_eval_smoke` (STEP 3, v0_1) — not the STEP 4 result.
