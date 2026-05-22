# 10_LOSS_DESIGN

## Source
- main.md §12 (total loss), §13 (training stages)

## Claim

The full FGLC training objective has 10 terms. These must be introduced **staged**:
Stage 1 uses only L_base+L_reward+L_value+L_calibration; Stage 2 adds correction terms.
End-to-end training from scratch with all 10 terms simultaneously will fail.

## Mathematical Formalization

```
L_total =
    L_base_dynamics          [base WM: NLL of one-step prediction]
  + λ1 L_reward              [reward head accuracy]
  + λ2 L_value               [value head TD consistency]
  + λ3 L_calibration         [σ regularization: prevent collapse]
  + λ4 L_corrected_dynamics  [corrected rollout NLL improvement]
  + λ5 L_sparse_attention    [entropy penalty on α_t]
  + λ6 L_correction_size     [L2 penalty on α_t^k · δ_t^k]
  + λ7 L_temporal_consistency [α_t ≈ α_{t+1} under persistent regime]
  + λ8 L_necessity           [max(0, margin - (L_without - L_with))]
  + λ9 L_sufficiency         [|L_selected - L_full|]
  + λ10 L_random_contrast    [max(0, margin - (L_random - L_selected))]

Initial λ values:
  λ1=1.0, λ2=1.0, λ3=0.1 (sigma reg)
  λ4=1.0 (Stage 2+)
  λ5=0.01 (sparsity), λ6=0.1 (size), λ7=0.05 (temporal)
  λ8=0.1 (necessity), λ9=0.1 (sufficiency), λ10=0.1 (contrast)

Stage-wise enable:
  Stage 1: L_base + λ1 L_reward + λ2 L_value + λ3 L_calibration
  Stage 2: + λ4 L_corrected_dynamics + λ5..λ10 correction terms
  Stage 3: planner integration (MPPI/CEM)
```

**Why staged?**
- If base dynamics and correction train simultaneously, correction module "steals" gradients
- Base WM must first establish a stable H0 hypothesis; correction then acts as H1
- Analogy: base = frozen prior; correction = posterior update

## Connection Map
- Upstream: M-6 (base dynamics), M-8 (β_t for correction), M-9 (α_t), M-12..M-15
- Downstream: M-17 (training stages), M-23 (hyperparameter spec)
- All previous modules feed into L_total

## Checkpoints

- C1 Math validity: PASS — All 10 loss terms are well-defined differentiable functions.
  λ values are hyperparameters; staged enabling is a training schedule decision.
- C2 Novelty: NOT CLAIMED for individual terms. Novel aspect: integration of
  calibration + correction + necessity/sufficiency + value-aware in single objective.
- C3 Reviewer attack: MEDIUM — "10-term loss requires careful tuning; unrobust to λ."
  Defense: staged training isolates terms; ablation suite tests each λ_i → 0.
- C4 Feasibility: PASS — all terms are standard ops; no exotic numerical issues expected.
- C5 Claim-metric: Required: λ sensitivity sweep (at least λ6, λ7, λ8 critical).
- C6 Impl risk: LOW — gradient flow through all terms is standard.
- C7 Experiment design: Must show Stage 1 alone fails on OOD (validates staged training necessity).
- C8 Failure interp: If Stage 2 doesn't improve over Stage 1 on OOD: correction module adds nothing.
  This would force reduction to "calibrated detection" claim without correction improvement.
- C9 Related work: N/A — this is a design decision, not a novelty claim.
- C10 Context routing: Source = main.md §12-13. Downstream: 12_TRAINING_STAGES.md, 13_ALGORITHM_CIRCA.md
