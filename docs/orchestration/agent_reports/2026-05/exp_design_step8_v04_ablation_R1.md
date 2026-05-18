# experiment-design-expander Report: STEP 8 v0_4 + ABL-015 + Ablation Coverage

**report_id**: exp_design_step8_v04_ablation_R1
**date**: 2026-05-18
**trigger**: T2 (실험설계 변경 전)
**verdict**: INCOMPLETE_CRITICAL

---

## Critical Findings

### CRITICAL 1: ABL-015 Naming Error in 35_step8_handoff.md

`35_step8_handoff.md` line 43-46 incorrectly names STEP 8-E as "no_falsification_training_hard (l_falsification=0.0)".

**SSoT (10_EVALUATION_BASELINE_ABLATION.md §8):**
- ABL-015 = no L_control_grammar = `l_control_grammar=0.0`
- ABL-016 = no L_falsification = `l_falsification=0.0` (STEP 5 checkpoint serves as this control)

**Correct specification for Codex Task 5:**
- `l_control_grammar=0.0` (NOT l_falsification)
- All other objective weights identical to Stage B (l_falsification=1.0, l_regime=1.0, etc.)

Note: TASK_1082_step8_abl015_faithful.md (Codex Task 5) already correctly specifies `l_control_grammar=0.0`. The TASK file is correct. The handoff document has a naming error but does not propagate to the task.

### CRITICAL 2: v0_4 OOD Grammar Family Structural Gap

v0_3 OOD grammar families: `filter_accordion`, `nested_scroll`. These families structurally CANNOT produce `blocker_removed` or `delayed_effect` effect types.

**Correct grammar family → effect_type mapping:**
- `blocker_removed` is produced by `modal_blocker`-style families
- `delayed_effect` is produced by `loading_delayed`/`pagination_vs_infinite`-style families
- `filter_accordion` and `nested_scroll` produce `state_change`, `no_state_change`, `reveal`-like effects

**Required change for Codex Task 2 (generate_v0_4_dataset.py):**
- Either expand OOD grammar families to include families that structurally produce missing effect types
- OR implement explicit stratified OOD sampling with effect_type forcing at the generator level
- Policy mixture adjustment alone CANNOT fix this

### HIGH: Missing ABL-025 (random-alternative) and ABL-026 (no-rollout) Runners

CLAUDE.md requires all named ablation families to have at least one runner. Neither ABL-025 nor ABL-026 appear in STEP 7 or STEP 8 inference-time harness.

**Recommendation**: Add ABL-025 and ABL-026 to STEP 8 inference-time ablation harness (run_step8_full_eval_report.py). Both are inference-time modifications, no retraining required.

---

## ABL-015 Definition Clarification

| ABL ID | Name | Training param | STEP 8 status |
|---|---|---|---|
| ABL-015 | no L_control_grammar | `l_control_grammar=0.0` | PLANNED (Task 5) — naming error in handoff but task file correct |
| ABL-016 | no L_falsification | `l_falsification=0.0` | IMPLEMENTED (STEP 5 checkpoint = this control) |

## Ablation Coverage Table (14 CRITICAL families)

| ABL ID | Family | STEP 8 Coverage | Status |
|---|---|---|---|
| ABL-002 | no-control-grammar (inference) | STEP 7 harness on v0_4 ckpt | PLANNED |
| ABL-003 | merged regime-control grammar | DEFERRED STEP 9 | DEFERRED |
| ABL-006 | collapsed latent | STEP 7 harness | PLANNED |
| ABL-011 | no-action-effect-log | STEP 7 harness | PLANNED |
| ABL-015 | no L_control_grammar (training) | Task 5 retrain | PLANNED |
| ABL-016 | no L_falsification (training) | STEP 5 ckpt | IMPLEMENTED |
| ABL-017 | no L_intent_action_mapping | STEP 7 harness | PLANNED |
| ABL-022 | no falsification gate | STEP 7 harness | PLANNED |
| ABL-023 | uncertainty instead | STEP 7 harness | PLANNED |
| ABL-024 | no alternative hypothesis | STEP 7 harness | PLANNED |
| ABL-033 | no decision-relevance gate | STEP 7 harness | PLANNED |
| ABL-034 | always-plan | STEP 7 harness | PLANNED |
| ABL-035 | no action rewrite | STEP 7 harness | PLANNED |
| ABL-040 | leakage sanity probe | isolated positive control | PLANNED |

## CLAIM-EVAL-002 (factorization) Risk

ABL-003 deferred → CLAIM-EVAL-002 cannot reach PRELIMINARY+ in STEP 8. Evidence card must mark CLAIM-EVAL-002 as BLOCKED_PENDING_ABL003.

## Summary

| Issue | Priority | Fix Required Before |
|---|---|---|
| ABL-015 naming error in handoff | CRITICAL (doc only) | Codex Task 5 execution |
| v0_4 OOD structural gap | CRITICAL | Codex Task 2 authoring |
| ABL-025/026 missing runners | HIGH | STEP 8 eval harness (Task 4) |
| CLAIM-EVAL-002 no ABL-003 coverage | HIGH | Evidence card explicit mention |
