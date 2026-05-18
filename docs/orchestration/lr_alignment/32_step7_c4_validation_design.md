# STEP 7 C4 Expanded Validation Design

date: 2026-05-18
n_seeds: 5
splits: test_id (34 ep), test_ood (50 ep)
agents: FRCG-LR, ABL-024 (no-alt-hyp), ABL-036 (no-compute-gate)

## C4 Status Criteria

- READY_FOR_REPORT: mean > 0.7 AND std < 0.15 AND FRCG-LR > ABL-024 by 0.05+ AND FRCG-LR > ABL-036 by 0.05+
- PRELIMINARY: mean > 0.5 but criteria partially unmet
- DOWNSHIFT: mean <= 0.5 (STEP 6 0.824 was smoke artifact)
- INCOMPLETE: results not yet available

## Checkpoint

STEP 6 falsification checkpoint: outputs/checkpoints/pretrain_v0_3_falsification/checkpoint_best.pt
SHA256[:16]: 1910C13F7708CE10 (immutable)

## Output

outputs/audits/step7_c4_expanded_validation.json
(STEP 6 audit files must NOT be overwritten)
