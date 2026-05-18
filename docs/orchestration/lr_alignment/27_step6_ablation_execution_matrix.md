# STEP 6 Ablation Execution Matrix

**Date**: 2026-05-18  
**Source**: `paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md §8` (ABL-001..042 SSoT)

---

## 14 Critical Ablations — Classification Table

| ABL id | ablation_core.yaml id | type | dispatch_ready | STEP 6 executable | requires_faithful_retrain |
|--------|----------------------|------|---------------|-------------------|--------------------------|
| ABL-001 | no_regime | training-proxy | YES | YES (proxy only) | YES (STEP 7) |
| ABL-003 | merged_regime_control_grammar | training-proxy | YES | YES (proxy only) | YES (STEP 7) |
| ABL-006 | collapsed_latent | inference-time | YES | YES (direct) | NO |
| ABL-011 | no_action_effect_log | inference-time | YES | YES (direct) | NO |
| ABL-015 | no_control_grammar_loss | training-proxy | YES | YES (proxy only) | YES (STEP 7) |
| ABL-016 | no_falsification | training-time control | YES (STEP 5 ckpt) | YES (control registered) | N/A |
| ABL-017 | no_intent_action_mapping | inference-time | YES | YES (direct) | NO |
| ABL-022 | no_falsification_score_gate | inference-time | YES | YES (direct) | NO |
| ABL-023 | uncertainty_instead_of_falsification | inference-time | YES | YES (direct) | NO |
| ABL-024 | no_alternative_hypothesis | inference-time | YES | YES (direct) | NO |
| ABL-033 | no_compute_gate | inference-time | YES | YES (direct) | NO |
| ABL-034 | always_plan_no_gate | inference-time | YES | YES (direct) | NO |
| ABL-035 | no_rewrite | inference-time | YES | YES (direct) | NO |
| ABL-036 | no_counterfactual_target | inference-time | YES | YES (direct) | NO |
| ABL-040 | leakage_sanity_probe | positive-control | YES | YES (direct) | NO |

**Type definitions**:
- **inference-time**: ablation applies at inference via masking/behavior change; works on any checkpoint
- **training-proxy**: ablation simulates training condition by proxy (random/passthrough); not faithful retrain
- **training-time control**: ABL-016 STEP 5 checkpoint IS the faithful run (l_falsification=0.0)
- **positive-control**: ABL-040 injects oracle label to confirm metric discriminability; NOT a performance ablation

---

## STEP 6 Directly Executable Ablations (using falsification-enabled checkpoint)

The following 11 ablations can be run immediately using `outputs/checkpoints/pretrain_v0_3_falsification/checkpoint_best.pt`:

ABL-006, ABL-011, ABL-017, ABL-022, ABL-023, ABL-024, ABL-033, ABL-034, ABL-035, ABL-036, ABL-040

---

## STEP 7 — Faithful Retrain Required (3 training-proxy)

| ABL id | name | reason |
|--------|------|--------|
| ABL-001 | no_regime | removes regime latent in training; proxy behavior is random |
| ABL-003 | merged_regime_control_grammar | merges representation in training; proxy behavior is concat |
| ABL-015 | no_control_grammar_loss | removes L_control_grammar in training; proxy is passthrough |

---

## ABL-016 Control Status

STEP 5 checkpoint serves as ABL-016 training-time control.  
Registration document: `docs/orchestration/lr_alignment/29_step6_abl016_control_registration.md`  
Checkpoint: `outputs/checkpoints/pretrain_v0_3/checkpoint_best.pt`  
Training l_falsification: 0.0  
Control eval run: `outputs/runs/p3_lr_real_eval_step5_trained_smoke/` (IMMUTABLE)

---

## ABL-040 Isolation Note

**ABL-040 (leakage_sanity_probe) is a POSITIVE CONTROL — it must NOT be mixed with performance ablations.**

- Purpose: inject `true_control_grammar` into inference input → metric should INCREASE (confirms discriminability)
- Interpretation: ABL-040 result that shows increased task_success_rate confirms the metric is discriminative
- Never average ABL-040 results with performance ablations in C1-C5 tables
- A result where ABL-040 does NOT increase metrics is a BLOCKER (metric is non-discriminative)

---

## Direct-Threat Baseline Notes (DOC_ONLY for STEP 6)

| Baseline | Class | STEP 6 Status |
|----------|-------|---------------|
| BASE-026 (WAC) | WACStyleConsequenceCorrectionAgent | STUB_ONLY — faithful upgrade in STEP 7 |
| BASE-027 (CUWM) | CUWMStyleCandidateSimulationAgent | STUB_ONLY — faithful upgrade in STEP 7/8 |
| BASE-028 (WebWorld) | WebWorldStyleSearchAgent | STUB_ONLY — faithful upgrade in STEP 8 |

**Forbidden wording**: never use "defeats", "outperforms", "proven superior" against direct-threat stubs  
(BASE-026/027/028) without faithful implementation. STEP 6 direct-threat results are labeled "STUB_ONLY"  
and must not appear in paper claims.

---

## Execution Plan for STEP 6 Smoke Eval

Run the following 9 inference-time ablations (+ FRCG-LR control) on 10 episodes of test_id:

```powershell
python scripts/10_run_lr_real_eval.py `
  --config configs/lr_eval_real_v0_3_falsification.yaml `
  --split test_id `
  --max-episodes 10 `
  --out-dir outputs/runs/p3_lr_real_eval_step6_falsification_test_id_smoke
```

This config includes agents: FRCG-LR, ABL-017, ABL-022, ABL-023, BASE-006, BASE-012-CATTS,
BASE-015, BASE-026 (STUB), BASE-027 (STUB), BASE-028 (STUB), BASE-003+008-VLAA.

Additional ablations (ABL-006, ABL-011, ABL-024, ABL-033, ABL-034, ABL-035, ABL-036, ABL-040)
can be added to the eval config as needed.
