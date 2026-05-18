# Claim-Metric Alignment Audit — STEP 5 (T2, compact mode)

**Date**: 2026-05-18
**Branch**: memory-redesign-2026-05-16 @ bea9b9c
**Auditor**: claim-metric-alignment-auditor (T2 pre-STEP5)
**Mode**: compact

---

## Alignment Table

| Claim | Metric | Status |
|---|---|---|
| C4 rollout fidelity | MET-WM-001 alternative_rollout_fidelity | PARTIALLY_ALIGNED (function absent) |
| C1 wrong-grammar persistence | MET-PERSIST-001 compute_wrong_grammar_persistence_v1 | MISALIGNED (namespace: grammar_{idx} vs enum name) |
| C3 LR falsification divergence | F_t mean_abs_diff (audit-only) | ALIGNED ("preliminary" wording OK) |
| C5 calibration non-degenerate | falsification ECE / _compute_c5_status | MISALIGNED (AND logic fails unique=2 case) |

## Misaligned Items

### C1 namespace
- **Issue**: frcg_agent emits `"grammar_0"`, `"grammar_1"` etc.; compute_wrong_grammar_persistence_v1 expects `"direct_search"` etc.
- **Fix**: Static 8-entry dict `_GRAMMAR_IDX_TO_NAME` in frcg_agent.py (Codex Task 3)
- **Verification**: test_step5_namespace_alignment.py

### C5 AND logic
- **Issue**: `variance < 1e-6 and unique_count < 2 and mean_wp == 0.0 and f_t_constant_zero` — AND + strict less-than
- **Random-init case**: variance=0.012, unique=2, mean=0.034 → all fail AND → incorrectly OK
- **Fix**: OR logic with `unique_count <= 2` (Codex Task 5)
- **Verification**: test_step5_calibration.py

## CRITICAL WARNING for C4 (Codex Task 2)

`predicted_top1_delta` MUST be the model's own rollout forward-pass prediction output, NOT the oracle `counterfactual_progress_delta` from the dataset. If both sides use the same record field, the metric collapses to trivially 1.0 (no discriminability). If the model lacks a separate rollout prediction head, return `status="BLOCKED_no_model_rollout_prediction"`.

MET-WM-001 SSoT requires `predicted_rollout` trace in eval runner. Verify this exists before implementing.

## C3 Wording (Permitted/Forbidden)

- **Permitted**: "C3 F_t divergence is preliminary; active planner path unchanged pending STEP 6 full wiring."
- **Forbidden**: "C3 resolved", "FRCG-LR achieves lower falsification divergence", any quantitative positive finding

## Verdict: PARTIALLY_ALIGNED

Two MISALIGNED items have concrete resolutions. One WARNING for C4 implementation risk.
No escalation required — all gaps have defined Codex task resolutions.

## ABL-011/015/040 Dispatch Test
Registry wiring (T6) is appropriate gate. No additional metric-level gap for these ablations.
