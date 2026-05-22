# 20_ABLATIONS — Must-Not-Disappear Ablation Families

## Source
- main.md §22.5 (ablation list), deep-research-report.md §실험 설계
- CLAUDE.md §Required ablation families

## This file IS the normative ablation SSoT. Do not maintain duplicates elsewhere.

## 11 Required Ablation Families

| ID | Family | Ablated component | Expected effect of ablation | Claim validated |
|---|---|---|---|---|
| ABL-01 | no-correction | Remove all δ_t^k (correction = 0) | OOD return degrades → base WM insufficient | Correction is needed |
| ABL-02 | no-attention | Replace α_t with uniform 1/K | Return and attribution degrade | Attention selection adds value |
| ABL-03 | no-falsification-gate | β_t = 1 always (always-correct) | OOD may improve slightly but compute inefficient | Gate provides compute savings |
| ABL-04 | random-mask | Random k groups, not attention-guided | Return < FGLC → attention is not random | Attention is non-trivially selective |
| ABL-05 | no-value | λ2 = λ_value = 0 | NLL improves, return degrades | Value-aware loss is necessary |
| ABL-06 | no-sparse | No sparsity penalty (softmax, λ5=0) | Attention spreads; attribution degrades | Sparsity enables group selection |
| ABL-07 | no-temporal-consistency | λ7 = 0 | Attention flickers across time | Temporal consistency stabilizes attribution |
| ABL-08 | collapsed-K=1-latent | K=1 (single group, no decomposition) | Cannot localize correction; similar to no-attention | K>1 grouping is necessary |
| ABL-09 | no-iVAE-prior | I3G without iVAE objective | Attribution precision degrades (I3G only) | iVAE identifiability needed (I3G) |
| ABL-10 | no-conformal-calibration | Hard threshold instead of empirical quantile | False alarm rate uncontrolled | Conformal calibration needed |
| ABL-11 | no-robust-MPC | Standard MPC (not robust) | Worst-case performance degrades | Robust planning under uncertainty needed |

## Ablation Outcome Rules

If ABL-02 (no-attention) ≈ FGLC: STOP. Claim "sparse attention adds above uniform selection" is invalid.
If ABL-01 (no-correction) ≈ FGLC on OOD: STOP. Problem existence fails — base WM sufficient under OOD.
If ABL-08 (K=1) ≈ FGLC: STOP. Group decomposition claim is invalid; reduce to gated residual claim.
If ABL-10 (hard threshold) ≈ FGLC: CONDITIONAL. Conformal calibration claim weakened; reduce to empirical.

## Ablation Execution Plan

```
Phase R9 (see docs/ROADMAP/10_PHASE_R9_ABLATION_GRID.md):
  - Run all 11 families on ManiSkill PickCube (primary task)
  - Run ABL-01, ABL-02, ABL-08 also on PushCube (cross-task generalization)
  - Each ablation: 3 seeds, 5 OOD conditions, 100 eval episodes per condition
  
Order of execution:
  1. ABL-01 (no-correction) — validates problem existence
  2. ABL-08 (K=1) — validates decomposition necessity
  3. ABL-02 (no-attention) — validates selection contribution
  4. ABL-10 (no-conformal) — validates calibration contribution
  5. ABL-03 (no-gate) — validates β_t gate compute savings
  6. ABL-05 (no-value) — validates value-aware loss
  7. ABL-04 (random-mask) — validates non-randomness of attention
  8. ABL-06, ABL-07, ABL-09, ABL-11 — secondary validations
```

## Connection Map
- This file is referenced by: CLAUDE.md, behavioral_coding_rules.md §5, baseline_ablation_guard.ps1
- Downstream: 21_METRICS.md, docs/ROADMAP/10_PHASE_R9_ABLATION_GRID.md
