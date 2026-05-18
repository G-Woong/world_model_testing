TASK_NAME: step6_ablation_execution_matrix

BACKGROUND:
STEP 6 requires documenting which of the 14 critical ablations can be executed immediately
(inference-time, using the falsification-enabled checkpoint) vs which require faithful retraining
(training-proxy). Currently 19 ablation wrappers exist in ablations.py.

ABL-016 (no_falsification) is now formally registered as the STEP 5 control (see Task 2).

GOAL:
Create the ablation execution matrix document and tests verifying its integrity.

FILES_ALLOWED:
- docs/orchestration/lr_alignment/27_step6_ablation_execution_matrix.md (new file)
- tests/test_step6_ablation_execution_matrix.py (new file)

FILES_FORBIDDEN:
- outputs/**
- data/**
- paper_context_ref/**
- src/frcgw/schemas/visibility.py
- .claude/**
- scripts/run_codex_task.ps1
- configs/ablation_core.yaml (Task 2 owns this; read-only for Task 5)
- configs/lr_eval_real_v0_3.yaml

REQUIRED_IMPLEMENTATION:

### docs/orchestration/lr_alignment/27_step6_ablation_execution_matrix.md

Create this document with:

Title: STEP 6 Ablation Execution Matrix
Date: 2026-05-18
Source: paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md §8 (ABL-001..042 SSoT)

## 14 Critical Ablations Table

| ABL id | name (ablation_core.yaml id) | type | dispatch_ready | STEP 6 feasible | requires_faithful_retrain |
|--------|------------------------------|------|----------------|-----------------|--------------------------|
| ABL-001 | no_regime | training-proxy | YES | YES (proxy only) | YES (STEP 7) |
| ABL-003 | merged_regime_control_grammar | training-proxy | YES | YES (proxy only) | YES (STEP 7) |
| ABL-006 | collapsed_latent | inference-time | YES | YES (direct) | NO |
| ABL-011 | no_action_effect_log | inference-time | YES | YES (direct) | NO |
| ABL-015 | no_control_grammar_loss | training-proxy | YES | YES (proxy only) | YES (STEP 7) |
| ABL-016 | no_falsification | training-time control | YES (STEP 5 ckpt) | YES (control registered) | N/A (STEP 5 is the faithful run) |
| ABL-017 | no_intent_action_mapping | inference-time | YES | YES (direct) | NO |
| ABL-022 | no_falsification_score_gate | inference-time | YES | YES (direct) | NO |
| ABL-023 | uncertainty_instead_of_falsification | inference-time | YES | YES (direct) | NO |
| ABL-024 | no_alternative_hypothesis | inference-time | YES | YES (direct) | NO |
| ABL-033 | no_compute_gate | inference-time | YES | YES (direct) | NO |
| ABL-034 | always_plan_no_gate | inference-time | YES | YES (direct) | NO |
| ABL-035 | no_rewrite | inference-time | YES | YES (direct) | NO |
| ABL-036 | no_counterfactual_target | inference-time | YES | YES (direct) | NO |
| ABL-040 | leakage_sanity_probe | positive-control | YES | YES (direct) | NO |

Notes:
- Type "inference-time": ablation applies masking/behavior change at inference; works on any checkpoint
- Type "training-proxy": ablation simulates training condition by proxy (random/passthrough); not faithful retrain
- Type "training-time control": ABL-016 STEP 5 checkpoint IS the faithful run (l_falsification=0.0)
- Type "positive-control": ABL-040 is oracle injection (should increase metrics); confirms discriminability

## STEP 6 Executable Ablations (9 direct, using falsification-enabled checkpoint)
ABL-006, ABL-011, ABL-017, ABL-022, ABL-023, ABL-024, ABL-033, ABL-034, ABL-035, ABL-036, ABL-040
(= 11 inference-time/positive-control ablations)

## STEP 7 Faithful Retrain Required (3 training-proxy)
ABL-001, ABL-003, ABL-015 (training-proxy; faithful retraining in STEP 7)

## ABL-016 Control Status (already registered)
STEP 5 checkpoint serves as ABL-016 training-time control.
Registered in: docs/orchestration/lr_alignment/29_step6_abl016_control_registration.md
Checkpoint: outputs/checkpoints/pretrain_v0_3/checkpoint_best.pt

## ABL-040 Isolation Note
ABL-040 (leakage_sanity_probe) injects oracle label into inference. It is a POSITIVE CONTROL
(metrics should increase). Its result must be interpreted separately from performance ablations.
Never average ABL-040 results with other ablations in C1-C5 tables.

## Direct-Threat Baseline Notes (DOC_ONLY for STEP 6)
BASE-026 (WAC), BASE-027 (CUWM), BASE-028 (WebWorld): Current implementations are stubs.
Faithful upgrade deferred to STEP 7. STEP 6 results for these agents are labeled "STUB_ONLY".
Forbidden wording: never use "defeats", "outperforms", "proven superior" against direct threats
without faithful implementation.

REQUIRED_TESTS:

### tests/test_step6_ablation_execution_matrix.py

1. test_14_critical_ablations_registered(): import ABLATION_REGISTRY from ablations.py, verify all 14 critical ABL ids are registered as wrapper entries. List to check: no_control_grammar, merged_regime_control_grammar, collapsed_latent, no_falsification, no_intent_action_mapping, no_falsification_score_gate, uncertainty_instead_of_falsification, no_alternative_hypothesis, no_compute_gate, always_plan_no_gate, no_rewrite, no_counterfactual_target, no_action_effect_log, no_control_grammar_loss.

2. test_training_vs_inference_type_classification(): verify that the 9 directly-executable ablations (ABL-006/011/017/022/023/024/033/034/035) are all present in ABLATION_REGISTRY. This tests dispatch_ready=YES. The "type" classification is doc-only.

3. test_abl040_is_positive_control_isolated(): import LeakageSanityProbeAblation, verify its description contains "leakage" or "oracle" or "sanity" (confirming positive-control nature), AND verify it is NOT in the same wrapper dict entry as performance ablations (it is an isolated wrapper).

4. test_abl016_control_evidence_ref_consistent(): import ABLATION_REGISTRY, assert ABLATION_REGISTRY["no_falsification"].control_evidence_ref is not None (confirms Task 2 was completed first).

5. test_matrix_file_exists(): verify docs/orchestration/lr_alignment/27_step6_ablation_execution_matrix.md exists and is non-empty.

ACCEPTANCE_CRITERIA:
- 5 tests PASS
- Matrix document contains all 14 critical ABL entries
- ABL-040 is explicitly labeled as positive-control, not performance ablation
- ABL-016 control evidence is noted as STEP 5 checkpoint (cross-reference to Task 2)
- direct-threat stubs (BASE-026/027/028) are DOC_ONLY labeled
- test_abl016_control_evidence_ref_consistent must PASS (depends on Task 2 completion)

COMMIT_MESSAGE:
feat(step6/task5): ablation execution matrix doc + 14 critical ABL classification tests

STOP_CONDITION:
Stop if: (1) any FORBIDDEN file is modified; (2) ABL-040 results are presented as performance evidence (positive-control isolation violated); (3) direct-threat baseline stubs are labeled as "faithful" or "defeated".
