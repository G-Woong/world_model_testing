# T1 Agent Report: Claim-Metric Alignment Auditor — STEP 6 C3 LR Reconciliation

**Date**: 2026-05-18  
**Phase**: STEP 6 pre-implementation (Phase C)  
**Trigger**: T1 (planner alt-emission fix design review)  
**Verdict**: PARTIALLY_ALIGNED

---

## Findings

### Finding 1 — propose() with model=None: **WARN**
`planner.py:125-134` calls `propose(latent_sample, model=None, ..., mode="posterior_only", k=3)`.
In `posterior_only` mode, `propose()` returns top-k hypotheses ranked by `log_prior` only — NOT evidence-blind stub, but evidence-blind. It ignores actual action-effect evidence. The fix using propose() results as alt_hypotheses is valid (returns real HypothesisId objects with valid combined_id), but uses prior-ranked alts, not likelihood-ranked alts. This weakens the theoretical justification and should be documented explicitly.

### Finding 2 — F_t non-zero after fix: **WARN**
After the fix, `falsification_score()` will have non-empty `alt_hypothesis_ids`. However, `falsification.py:64-65` short-circuits and returns `torch.zeros` when `evidence.observed_effect_type in {0, 6}` (effect types "none/no_change" and "no_op_valid"). Since `_effect_type_id` maps default "none" effect to 0, F_t remains structurally 0 for steps without observable effect changes. The fix removes one zero source (empty alt list) but does not remove the evidence-type zero gate.

### Finding 3 — "PRELIMINARY" max safe level: **PASS**
Yes, "PRELIMINARY" is the correct ceiling for C3 at STEP 6. "READY_FOR_REPORT" is blocked without:
(a) confirmed non-zero F_t on real evaluation episodes, (b) label coverage data, (c) non-degenerate F_t propagated to `predicted_wrong` decisions.

### Finding 4 — metric-planner disconnect on predicted_wrong: **BLOCK (for C3 metric)**
`metrics.py:124-148` reads `step["eval_labels"]["true_wrong_hypothesis"]` as ground truth and
`step["predicted_wrong"]` as agent prediction. In `eval_runner.py:109-113`, `predicted_wrong` is
sourced from `agent.last_predicted_wrong` — but `text_frcg_plan` does NOT set `last_predicted_wrong`
on any agent wrapper. Therefore `falsification_precision_recall` computes against constant-False
`predicted_wrong` for any TextFRCGModelAgent. The C3 metric is a **null metric** for the current agent.

This is a **substantive alignment gap** independent of the §B2 fix. Must be resolved in Codex Task 1.

**Required fix**: Agent wrapper must threshold F_t into `predicted_wrong` (e.g., `self.last_predicted_wrong = (F_t > tau_f)` in `frcg_agent.py` or the planner's `plan()` output).

### Finding 5 — New gaps from planner fix: **WARN**
No new untracked metric gap from the fix itself. But `posterior_only` vs `hybrid` mode choice is not documented against any claim. Add documentation to Codex Task 2 (ABL-016 registration).

---

## Summary

| # | Item | Verdict |
|---|---|---|
| 1 | propose() model=None behavior | WARN |
| 2 | F_t non-zero after fix | WARN |
| 3 | "PRELIMINARY" max level | PASS |
| 4 | predicted_wrong null metric gap | BLOCK (for C3 metric) |
| 5 | New gaps from fix | WARN |

**Overall: PARTIALLY_ALIGNED — BLOCK for "READY_FOR_REPORT", WARN for PRELIMINARY**

## Required Codex Task 1 Additions
1. **(Critical)** Add F_t-to-predicted_wrong threshold in agent wrapper:
   - `frcg_agent.py` must set `self.last_predicted_wrong = (F_t > tau_f)` after computing F_t in `act()`
   - OR planner return `planned=True/False` must be mirrored to `last_predicted_wrong`
2. Planner fix (B2) to move propose() before falsification_score() is necessary but not sufficient
3. Document: `propose()` uses `posterior_only` mode (evidence-blind) — C3 evidence is still preliminary
