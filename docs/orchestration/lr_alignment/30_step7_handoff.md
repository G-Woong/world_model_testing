# STEP 7 Handoff Document

**Date**: 2026-05-18  
**From**: STEP 6 completion  
**Status**: DRAFT — items to address in STEP 7

---

## 1. LR Scorer Active Path Swap

**Deferred from STEP 6**: `frcg_agent.py` currently uses `text_frcg_plan()` which calls
`planner.py:falsification_score()` for inference F_t. The LR scorer (`lr_scorer.py`) is a
separate rule-based component that computes F_t differently.

**Condition for swap**: `active_path_swap_decision == "READY_FOR_SWAP"` from
`outputs/audits/step6_lr_reconciliation.json`. Currently: `PERSIST_DUAL_TRACE`.

**Action**: After long-horizon training in STEP 7, re-run reconciliation audit. If `READY_FOR_SWAP`,
update `frcg_agent.py` to use `lr_scorer` path for inference.

---

## 2. C2 regime_shift_f1 Metric

**Deferred from STEP 6**: `EvaluationLabels` in `step_schema.py` has `ood_type` but not `regime`.
`true_regime` is in `TrainingLabels` (TRAINING_SUPERVISION bucket, hidden at inference — leakage risk).

**Action**: Review visibility contract change needed to surface regime label for evaluation.
Consult `paper_context_ref/06_DATA_SCHEMA_AND_LABELING.md §4` before any change.
Run leakage auditor after any visibility change.

---

## 3. C5 Calibration Training

**Deferred from STEP 6**: `wrong_probs` in v0_3 test_id episodes are constant (degenerate predictor).
Training l_falsification=1.0 in STEP 6 did not fix calibration (F_t still structural zero at inference).

**Action**: After C3 is unblocked (non-zero F_t at inference), implement temperature scaling or
isotonic regression calibration. Only start when `C5_calibration_status != DEGENERATE_PREDICTOR`.

---

## 4. BASE-026 (WAC) Faithful Upgrade

**Deferred from STEP 6**: `WACStyleConsequenceCorrectionAgent` is a stub (DOC_ONLY).

**Action**: Implement grammar posterior + consequence model per WAC paper. Must not use
forbidden_source_assertion violation. Requires faithful implementation before any comparison claim.

---

## 5. BASE-027 (CUWM) and BASE-028 (WebWorld) Faithful Upgrade

**Deferred from STEP 6**: Both agents are stubs.

**Action**: STEP 7 (CUWM) and STEP 8 (WebWorld). Implement before any direct-threat comparison claims.
Forbidden wording until then: "defeats", "outperforms", "proven superior".

---

## 6. Long-Horizon Training

**Deferred from STEP 6**: Stage 2 ran 498 steps (6 epochs) on v0_3 (limited data).

**Action**: 
- Option A: Collect DATA-T1 dataset (2000~10000 episodes) with observable effects
- Option B: Extend training to epochs ≥ 10 with v0_3 data augmentation
- Goal: test_id smoke episodes should show non-trivial effect_type distribution
  to unblock F_t > 0 at inference (effect_type ≠ 0 guard in falsification.py:64)

---

## 7. Full 14 Critical Ablation Faithful Execution

**Deferred from STEP 6**: ABL-001, ABL-003, ABL-015 are training-proxy only.

**Action**: Faithful retrain with:
- ABL-001 (no_regime): model without regime latent dimension
- ABL-003 (merged_regime_control_grammar): merged representation
- ABL-015 (no_control_grammar_loss): without L_control_grammar

---

## 8. Statistical Reliability

**Deferred from STEP 6**: All STEP 6 results from single seed (seed=42).

**Action**: Run n=5 seeds. Report mean ± std for all C1-C5 claims.

---

## 9. h_exec_id Emission Policy

**Deferred from STEP 6**: Training uses h_exec_id=0 for all examples (deterministic, not per-example
from actual grammar prediction). 

**Action**: Decide whether to use model's own grammar prediction (z_grammar_logits argmax) as
h_exec_id during training, or keep deterministic baseline.

---

## 10. Compute-Matched Comparison

**Deferred from STEP 6**: BASE-015 (ComputeMatchedRandomAgent) comparison not compute-matched.

**Action**: Ensure BASE-015 and FRCG-LR use identical compute budget in comparison.

---

## 11. schema_leakage_guard Hook Drift

**Deferred from STEP 6**: `.claude/hooks/schema_leakage_guard.ps1` forbiddenTokens has partial
drift from `visibility.py::FORBIDDEN_AGENT_FIELDS` (+4 counterfactual, −audit_metadata).

**Note**: `test_forbidden_field_mirror_sync.py` is GREEN (tests the code-level contract, not the hook).
The hook drift is a defense-in-depth issue, not a contract violation.

**Action**: Review R2 lock policy before modifying hook. If safe to update, sync
`$forbiddenTokens` with `FORBIDDEN_AGENT_FIELDS` in STEP 7.

---

## 12. Paper Table Readiness

**Deferred from STEP 6**: P7 phase gate condition not met yet.

**Conditions for P7 entry**:
- C1 persistence_v1: PRELIMINARY or better (needs non-zero F_t at inference)
- C3 falsification_f1: PRELIMINARY or better (needs non-degenerate F_t)
- C4 rollout_fidelity: READY_FOR_REPORT (currently 0.824 — needs validation)
- Statistical reliability: n=5 seeds
- Long-horizon training completed
- At least 2 direct-threat baselines faithfully implemented

---

## C2/C5 STEP 7 Blocking Summary

| Metric | STEP 6 Status | STEP 7 Action |
|--------|--------------|---------------|
| C1 persistence_v1 | BLOCKED (no evidence_timestamp in eval) | Fix eval_labels in dataset or v0_4 |
| C2 regime_shift_f1 | BLOCKED (regime label not in eval_labels) | Visibility contract review |
| C3 falsification_f1 | BLOCKED (degenerate F_t, effect_type=0) | Long-horizon data with diverse effects |
| C4 rollout_fidelity | 0.824 OK (PRELIMINARY) | Validate on OOD + n=5 seeds |
| C5 calibration | DEGENERATE_PREDICTOR | Fix C3 first |
