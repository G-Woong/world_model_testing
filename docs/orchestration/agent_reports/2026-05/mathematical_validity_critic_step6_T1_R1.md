# T1 Agent Report: Mathematical Validity Critic — STEP 6 F_t Wiring Design

**Date**: 2026-05-18  
**Phase**: STEP 6 pre-implementation (Phase C)  
**Trigger**: T1 (claim/design change before Codex Task 1)  
**Verdict**: NEEDS_REVISION

---

## Findings

### Finding 1 — F_t shape mismatch: **BLOCK**
`falsification_score()` returns a scalar 0-dim tensor (line 83: `return score.squeeze()`).
`L_falsification()` at line 112 calls `F_t.reshape(-1)`, producing a 1-element `[1]` tensor.
Then `scores.index_select(0, idx)` selects from that 1-element tensor using `idx` of length
`len(labeled)` (up to batch_size=8). When `len(labeled) > 1`, index_select silently repeats
element 0 for all indices — constant-valued gradient signal, not an error, but mathematically wrong.

**Required fix**: `falsification_score()` must be called per-example and results stacked to `[B]`,
OR the function must be vectorized to return `[B]`. Codex Task 1 must specify: loop over batch
examples, call `falsification_score()` per example, stack results into `[B]` tensor before passing
to `compute_total_loss`.

### Finding 2 — Grammar ID range: **PASS**
`WorldModelHeads._hypothesis_ids()` clamps to `[0, n_hypotheses-1]` (default n_hypotheses=64).
GRAMMAR_VOCAB has 8 entries (ids 0..7). Using `alt_hypothesis_ids = list(range(1, 8))` is safe.

### Finding 3 — TrainingLabels evidence use: **PASS**
`FalsificationEvidence` consuming `true_action_effect_type`, `progress_delta`, `true_failed_action`
from `BatchTargets` is internally consistent — same fields already used as supervision signals.
Not a leakage violation since BatchTargets are excluded from `public_input`.

### Finding 4 — Config weight redundancy: **PASS**
`DEFAULT_WEIGHTS["l_falsification"] = 1.0` already. Setting `objective_weights.l_falsification: 1.0`
in new falsification config is redundant but harmless. STEP 5 config correctly has `0.0`.

### Finding 5 — effect_type str-to-int conversion: **WARN**
`true_action_effect_type` is a string in `BatchTargets`, but `FalsificationEvidence.observed_effect_type`
expects `int`. Must convert via `EFFECT_TYPE_VOCAB[t.true_action_effect_type]` before constructing
`FalsificationEvidence`. Without this conversion, `log_likelihood()` will cause a `TypeError` at runtime.

---

## Summary

| # | Item | Verdict |
|---|---|---|
| 1 | F_t shape: scalar vs [B] | BLOCK |
| 2 | Grammar ID range / clamping | PASS |
| 3 | TrainingLabels as evidence | PASS |
| 4 | Config weight redundancy | PASS |
| 5 | effect_type str-to-int | WARN |

**Overall: NEEDS_REVISION**

## Required Codex Task 1 Additions
1. Loop over batch examples in `train_text.py`, call `falsification_score()` per example, stack to `[B]`
2. Add `EFFECT_TYPE_VOCAB[t.true_action_effect_type]` mapping in batch evidence construction
3. Add unit test asserting `L_falsification` receives `[B]`-shaped tensor when batch_size > 1 with mixed labeled/unlabeled examples
