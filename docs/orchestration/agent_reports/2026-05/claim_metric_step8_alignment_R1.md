# claim-metric-alignment-auditor Report: STEP 8 C1-C5 Alignment

**report_id**: claim_metric_step8_alignment_R1
**date**: 2026-05-18
**trigger**: T1+T2
**verdict**: PARTIALLY_ALIGNED

---

## C1-C5 Alignment Table

| Claim | Metric | Leakage-safe | Computable | Status |
|---|---|---|---|---|
| C1 wrong-grammar persistence | `compute_wrong_grammar_persistence_v1` | CONDITIONAL — uses `true_wrong_hypothesis` post-hoc (evaluation-only, not agent input) | PARTIAL — blocked without `correct_hypothesis_id` in eval_labels | WARN |
| C2 factorization + OOD | `ood_shift_f1` PROXY only | YES | YES | PROXY_ONLY (FC-02 cannot be validated in STEP 8) |
| C3 falsification F1 | `falsification_precision_recall`, F_t from lr_scorer | SAFE (lr_scorer uses public path only) | PARTIAL — degenerate risk | WARN |
| C4 alternative rollout + rewrite | `alternative_rollout_fidelity`, `recovery_delay` | YES | PARTIAL — blocked without model rollout prediction | WARN |
| C5 ECE + progress_per_compute | ECE: BLOCKED_DEGENERATE; `progress_per_compute`: computable | YES | PARTIAL | PARTIAL |

## Critical Findings

### CRITICAL: C1 requires `correct_hypothesis_id` in v0_4 evaluation_labels
`compute_wrong_grammar_persistence_v1` reads `eval_labels.correct_hypothesis_id`. If v0_4 generator does NOT emit this field, all C1 episodes report status=BLOCKED. Must be added to Codex Task 2 (v0_4 generator) acceptance criteria.

### FC-02 (C2) is BLOCK_SOFT in STEP 8
The architectural claim (factorization contributes to OOD generalization) requires:
- True metric: `regime_shift_f1` (needs `true_regime` in EvaluationLabels → STEP 9 R2 lock)
- Faithful ablations: ABL-001 (no_regime) + ABL-003 (merged regime-grammar) → STEP 9

STEP 8 can only produce ood_shift_f1 PROXY evidence. Wording must be "PRELIMINARY_PROXY" not "PRELIMINARY".

### C3 F_t is leakage-safe via lr_scorer path
`from_public_step()` uses only public observations. `_check_metadata_for_leakage()` runtime guard prevents hidden labels in hypothesis metadata. SAFE path confirmed.

### ABL-040 injection may be inert
`LeakageSanityProbeAblation` sets `self._agent._last_selected_hypothesis_id` AFTER `act()`. If `eval_runner.py` does not read this field for metric computation, the positive control produces identical results to base FRCG-LR. Add test to verify injection propagates to metric output.

### C5 ECE gating
`calibration.py` (NEW, Codex Task 7) must implement `BLOCKED_DEGENERATE_PREDICTOR` guard: if `unique_count(wrong_prob) ≤ 2`, return status=BLOCKED_DEGENERATE_PREDICTOR, do NOT compute ECE.

## BASE-026/027 Metric Comparison Scope
Must compare beyond `task_success_rate`:
1. `wrong_control_grammar_persistence` — mechanism differentiation
2. `recovery_delay` (MET-REC-001) — speed of hypothesis update
3. `falsification_precision_recall` — LR vs heuristic signal quality
4. `progress_per_compute` — compute efficiency

## Action Items for Codex Tasks

| Task | Action | Priority |
|---|---|---|
| Task 2 (v0_4 generator) | Add `correct_hypothesis_id` to evaluation_labels; verify in Gate O3 | CRITICAL |
| Task 4 (eval harness) | Verify ABL-040 injection propagates to metric output; add test | HIGH |
| Task 7 (C2/C5) | `calibration.py` must have BLOCKED_DEGENERATE_PREDICTOR guard programmatically | HIGH |
| Task 6 (baselines) | Include persistence + recovery_delay + falsification metrics in BASE-026/027 comparison | HIGH |
| All artifacts | FC-02 wording must be PRELIMINARY_PROXY, never PRELIMINARY | MEDIUM |
