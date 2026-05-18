# STEP 6 ABL-016 Control Registration

**Date**: 2026-05-18  
**Status**: REGISTERED  
**Branch**: memory-redesign-2026-05-16

---

## Section 1: What ABL-016 Is

STEP 5 checkpoint = deliberate training-time no-falsification control condition.

- **Training config**: `configs/train_text_v0_3.yaml` (l_falsification=0.0)
- **Control checkpoint**: `outputs/checkpoints/pretrain_v0_3/checkpoint_best.pt`
- **Control eval run**: `outputs/runs/p3_lr_real_eval_step5_trained_smoke/` (preserved, IMMUTABLE)
- **SSoT reference**: `paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md §8` (ABL-016 / no_falsification)

The STEP 5 checkpoint is NOT a failure of FRCG-LR. It is the deliberate control condition for ABL-016 (no_falsification), where the training-time falsification loss weight was set to 0.0 to test what happens when the falsification head receives no gradient signal during training.

## Section 2: Naming Correction

Prior session documents (including `25_step6_handoff.md`) referenced "ABL-010". **This is incorrect.**

SSoT (`paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md §8`) and `src/frcgw/evaluation/ablations.py` consistently define:
- `tdd_ref="ABL-016"` / `ablation_id="no_falsification"` = training-time L_falsification removal
- ABL-010 does not exist in the current SSoT registry

All references to "ABL-010" for the STEP 5 checkpoint/training condition should be read as ABL-016.

## Section 3: Experimental Comparison (STEP 6)

| Condition | Training l_falsification | Checkpoint | Status |
|-----------|--------------------------|------------|--------|
| ABL-016 (control) | 0.0 | `outputs/checkpoints/pretrain_v0_3/checkpoint_best.pt` | REGISTERED (STEP 5) |
| Experimental (STEP 6) | 1.0 | `outputs/checkpoints/pretrain_v0_3_falsification/checkpoint_best.pt` | IN PROGRESS |

**Comparison metrics**: C3 (falsification F1), C4 (rollout fidelity), C1 (persistence_v1)  
**Audit output**: `outputs/audits/step6_lr_reconciliation.json` (4-way: ABL-016 × {planner, lr_scorer} × FALSIFICATION_ENABLED × {planner, lr_scorer})

## Section 4: Immutability Guarantee

The following artifacts are **IMMUTABLE** and must never be modified or deleted:
- `outputs/checkpoints/pretrain_v0_3/**` (4 files: checkpoint_best.pt, checkpoint_ep0.pt, checkpoint_ep1.pt, manifest.json)
- `outputs/runs/p3_lr_real_eval_step5_*` (all STEP 5 eval outputs)
- `outputs/audits/step5_lr_reconciliation.json`
- `outputs/audits/step4_*.json`

## Section 5: Claim Wording Policy

Maximum claim wording for STEP 6 results: **PRELIMINARY**

Forbidden wording (never use in STEP 6 or STEP 7 without long-horizon evidence):
- "resolved", "proven", "defeats", "outperforms", "superior to"

The fact that C3 F1 increases after enabling l_falsification=1.0 training is a necessary but insufficient condition for C3 claim. Statistical reliability (seed variance n=5) and long-horizon training (DATA-T1 2000+ episodes) are required for "READY_FOR_REPORT".

## Section 6: Code Registration

- `src/frcgw/evaluation/ablations.py`: `AblationConfig.control_evidence_ref` field added
- `configs/ablation_core.yaml`: ABL-016 entry annotated with control_checkpoint_ref, training_l_falsification, step6_experimental_group_ckpt
- Tests: `tests/test_step6_abl016_control_registration.py`
