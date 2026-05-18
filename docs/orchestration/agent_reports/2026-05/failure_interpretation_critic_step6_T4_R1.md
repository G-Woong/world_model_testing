# T4 Agent Report: Failure Interpretation Critic — STEP 6 Results

**Date**: 2026-05-18  
**Phase**: STEP 6 post-execution (Phase H)  
**Trigger**: T4 (results interpretation before claim finalization)  
**Verdict**: MODIFIED — C3 ceiling must be BLOCKED, C4 needs source validation

---

## Finding 1 — C3_f1=0.0: Evidence unavailability, NOT model failure (WARN)

The structural evidence is unambiguous. `falsification.py:64-65` short-circuits F_t=0.0 when
`observed_effect_type in {0,6}` ("none"/"no_op_valid"). ALL 69 evaluated steps across both
checkpoints show `f_t: 0.0` with `degenerate_rate=1.0`.

Critical diagnostic: LR scorer `falsification_lr_scorer.mean_f_t: 1.5` with `degenerate_rate=0.0`
for BOTH checkpoints, confirming the model's internal representation is non-degenerate. The issue
is that v0_3 test_id episodes don't contain steps with observable effects (effect_type ∉ {0,6}).

The fact that C3_f1=0.0 for ALL agents (FRCG-LR, ABL-017, ABL-022, ABL-023, all baselines)
uniformly confirms this is a dataset/trigger structural gap, not a model-specific failure.

The `l_falsification` training loss being non-zero (0.6531/0.6409) confirms the loss surface is
non-flat — the model DID learn something. But the eval split provides no trigger paths.

**Claim impact**: C3 cannot be evaluated on v0_3 test_id. Scope to "pending eval on episodes with observable effect types."

## Finding 2 — C4 rollout fidelity 0.824: Genuine model computation, but preliminary (WARN)

The 0.824 value comes from `step["predicted_progress_delta"]` = `agent.last_predicted_progress_delta`
= max of model rollout predictions across top-3 candidates. This IS live model inference
(model.world_model_heads.rollout_step() called per candidate in _TracingAgent.act()).

The T4 agent initially raised concern about `rollout_steps=0` — this is the PLANNER's compute
budget, not the TracingAgent's model prediction call. They are separate code paths.

However, caveat: the 0.824 compares max(rollout_pred over candidates) vs actual_progress_delta.
This is a valid metric but PRELIMINARY:
- Needs OOD split validation
- Needs n=5 seeds
- Source of comparison: predicted = model's top-1 progress prediction; actual = dataset progress_delta

**Claim impact**: C4=0.824 is reportable as "PRELIMINARY" with explicit caveats.

## Finding 3 — C3 ceiling: Must be BLOCKED (BLOCK)

Zero positive evidence of falsification detection. Reporting "PRELIMINARY" would overstate.

Correct wording: "C3 falsification detection F1 is structurally untestable on v0_3 test_id due
to degenerate effect-type coverage. C3 measurement is BLOCKED pending evaluation on episodes
with non-zero observable effects (effect_type ∉ {0,6})."

## Finding 4 — l_falsification non-zero training vs zero inference (WARN)

Training l_falsification is non-zero. LR scorer F_t is non-zero (mean=1.5). Inference planner
F_t=0 is due to effect_type guard, not training failure. Must be disclosed as eval coverage gap,
not model failure.

## Finding 5 — Conditions for C3 upgrade from BLOCKED

1. **Effect-type coverage**: >20% of eval steps with effect_type ∉ {0,6}
2. **Non-zero F_t at inference**: At least subset of steps with F_t > 0
3. **Differential from ABL-016**: delta_falsification_vs_abl016.planner > 0

## Negative Result Disclosure: PASS

All negative results are present and accurately recorded:
- C3_f1=0.0 across all agents (status OK, not hidden)
- c3_claim_readiness: BLOCKED (correctly set)
- C5: DEGENERATE_PREDICTOR (full audit: n_steps=2277, unique_wrong_prob_count=2)
- fake_metric_count: 0 ✓
- No metric fabricated

## Summary

| Claim | Status | Action |
|-------|--------|--------|
| C3 ceiling | BLOCK | Change from PRELIMINARY to BLOCKED |
| C4 0.824 | WARN/PRELIMINARY | Document as preliminary, source-traced |
| l_falsification training non-zero | PRESERVES | Evidence of non-flat loss surface only |
| C1 persistence 2.43 | PRESERVES | Same range as STEP 5, stable |
| Negative result disclosure | PASS | All negatives recorded |

**overall_claim_status: MODIFIED** — C3 wording must change to BLOCKED.
No INVALIDATED condition. Core persistence claim C1 unaffected.
