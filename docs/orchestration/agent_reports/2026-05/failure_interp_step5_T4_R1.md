# Failure Interpretation — STEP 5 (T4, deep mode)

**Date**: 2026-05-18
**Agent**: failure-interpretation-critic (T4)
**Overall**: WEAKENED (not INVALIDATED)
**Negative result disclosure**: YES

---

## Key Failures Identified

### FAIL-018: C5 calibration degenerate (triggered)
- Trained model output: unique_wrong_prob_count=2, mean_F_t=0.0
- Root cause: l_falsification=0.0 in training → falsification head received no gradient → collapsed to constant
- Claim impact: WEAKENS. Loss 1.96→0.0081 proves objective was fit, but objective had no falsification component.

### FAIL-010: No-falsification ablation indistinguishable from main method (triggered)
- All agents (FRCG-LR, ABL-017/022/023, all baselines) produce C3_falsification_F1=0.0
- Root cause: Current checkpoint is functionally the no-falsification ablation (l_falsification=0.0)
- Claim impact: REQUIRES_MODIFICATION. CLAIM-EVAL-003 cannot be advanced until l_falsification > 0 training.

### FAIL-001: Ceiling effect (triggered)
- task_success_rate=1.0 for ALL agents; C1_persistence=2.5 and C3_recovery_delay=2.5 identical across all
- Root cause: 5-episode smoke split trivially solvable + untrained falsification
- Claim impact: WEAKENS. No mechanism differentiation observable.

### FAIL-017: C4 eval harness gap (triggered)
- C4_rollout_fidelity=BLOCKED_no_model_rollout_prediction
- Root cause: Eval runner doesn't trace model's forward-pass rollout prediction output
- Claim impact: REQUIRES_MODIFICATION. CLAIM-EVAL-004 zero supporting evidence.

### FAIL-024: Discriminative power zero (triggered)
- F_t_planner=0.0 on ALL 37 steps; 44 BLOCKED metrics
- Root cause: 5 smoke episodes + untrained falsification
- Claim impact: WEAKENS. No claim about effect magnitude from this run.

---

## Critical Finding

**The STEP 5 checkpoint (trained with l_falsification=0.0) is functionally the no-falsification ablation (ABL-010), not the proposed FRCG-LR model.** This must be disclosed and the checkpoint must be relabelled.

## Claim Status Summary

| Claim | Status | Reason |
|---|---|---|
| CLAIM-EVAL-001 (C1 persistence) | WEAKENED | Ceiling effect, identical across agents |
| CLAIM-EVAL-003 (C3 falsification) | BLOCKED_EVIDENCE_INSUFFICIENT | l_falsification=0.0 → untrained head |
| CLAIM-EVAL-004 (C4 rollout fidelity) | UNSUPPORTED | BLOCKED_no_model_rollout_prediction |
| C5 calibration | DEFERRED | Structural fix done; calibration requires trained model |
| C6 progress_per_compute | PRELIMINARY | FRCG-LR=0.254 vs others, but not attributable to falsification |

## Required STEP 6 Actions (CRITICAL)

1. **Retrain with l_falsification > 0** — Current checkpoint relabelled as ABL-010 data
2. **Register current run as ABL-010** (no-falsification baseline) — Preserves negative result
3. **Fix eval harness** to log rollout prediction output for C4
4. **C3 status**: PRELIMINARY → BLOCKED_EVIDENCE_INSUFFICIENT until retraining
