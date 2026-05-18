# Experiment Design Audit — STEP 5 (T2, compact mode)

**Date**: 2026-05-18
**Branch**: memory-redesign-2026-05-16 @ bea9b9c
**Auditor**: experiment-design-expander (T2 pre-STEP5)
**Mode**: compact

---

## Critical Ablation Status (14 CRITICAL per §8 SSoT)

| ABL | Key | Status | Note |
|---|---|---|---|
| ABL-002 | no_control_grammar | IMPLEMENTED | REGISTRY + WRAPPERS |
| ABL-003 | merged_regime_control_grammar | IMPLEMENTED | |
| ABL-006 | collapsed_latent | IMPLEMENTED | |
| ABL-011 | no_action_effect_log | MISSING | yaml-only → T6 wiring |
| ABL-015 | no_control_grammar_loss | MISSING | yaml-only → T6 wiring |
| ABL-016 | no_falsification | IMPLEMENTED | |
| ABL-017 | no_intent_action_mapping | IMPLEMENTED | |
| ABL-022 | no_falsification_score_gate | IMPLEMENTED | |
| ABL-023 | uncertainty_instead_of_falsification | IMPLEMENTED | |
| ABL-024 | no_alternative_hypothesis | IMPLEMENTED | |
| ABL-033 | no_compute_gate | IMPLEMENTED | |
| ABL-034 | always_plan_no_gate | IMPLEMENTED | |
| ABL-035 | no_rewrite | IMPLEMENTED | |
| ABL-040 | leakage_sanity_probe | MISSING | yaml-only → T6 wiring |

**11 IMPLEMENTED, 3 MISSING** (ABL-011, ABL-015, ABL-040) — tracked in Codex Task 6 (TASK_1054).

## CRITICAL ABLATION COVERAGE GAPS

1. `ABL-011 no_action_effect_log` — yaml-only; no Python class; no registry entry
2. `ABL-015 no_control_grammar_loss` — yaml-only; no Python class; no registry entry
3. `ABL-040 leakage_sanity_probe` — yaml-only; no Python class; no registry entry

## Implementation Notes for Codex Task 6

### ABL-011
Target field: `history_public[*].effect_summary` (PublicHistoryItem) — NOT a top-level `action_effect_log`.
Zero/None out `effect_summary` on a COPY of obs (do not mutate original).

### ABL-015
Proxy for training-time L_control_grammar=0.0. Inference proxy = random candidate selection.
Document clearly as a proxy; training cannot be replayed in P3 text-only smoke mode.

### ABL-040
Use `eval_labels: dict | None` parameter of `act()` for injection. NOT PublicObservation.
Structurally isolated from production leakage (leakage_auditor checks PublicObservation only).
Gate with `assert ablation_id == "leakage_sanity_probe"` to prevent accidental production use.

## Direct Threat Baselines
BASE-026/027/028: CONTRACT-ONLY for STEP 5 (T8 reviewer-response doc). No code implementation gap.

## Verdict: INCOMPLETE_CRITICAL (pre-implementation)
All 3 gaps are tracked in TASK_1054. No removal of existing CRITICAL ablations detected. Not escalated.
