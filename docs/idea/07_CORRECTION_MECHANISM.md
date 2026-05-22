# 07_CORRECTION_MECHANISM

## Source
- main.md §8 (correction location), §9 (correction module)
- deep-research-report.md §SCM/do-intervention/mediator (R-1)

## Claim

Correction is applied to the **transition prediction** (μ_t), not to z_t directly.
This is the "transition adapter" pattern: base WM provides H0 prediction; correction module
provides conditional residual. The final corrected prediction is:
μ̃_t^k = μ_t^k + β_t · α_t^k · δ_t^k

This is NOT post-hoc latent space editing — it is a **conditional residual** applied during
inference when falsification is detected, gated by β_t, selected by α_t.

## Mathematical Formalization

```
Three correction location options:
  (a) Current latent:    z̃_t = z_t + α_t ⊙ δ_t     [corrects state estimate]
  (b) Next prediction:   μ̃_t = μ_t + α_t ⊙ δ_t     [corrects dynamics prediction]
  (c) Transition adapter: μ̃_t = fθ(z_t,a_t,h_t) + α_t ⊙ gψ(z_t,ρ_t,a_t,h_t)

RECOMMENDED: option (c) transition adapter

Correction module per group k:
  δ_t^k = Gψ^k(z_t^k, ρ_t^k, a_t, h_t)
         = δ_max · tanh(MLP([z_t^k, ρ_t^k, a_t, h_t]))
  
  MLP: Linear(d_z+d_rho+d_a+d_h → 128) → SiLU → LayerNorm → Linear(128→128) → SiLU → Linear(128→d)

Final corrected prediction:
  μ̃_t^k = μ_t^k + β_t · α_t^k · δ_t^k
  
  β_t:    falsification gate   (whether to correct at all)
  α_t^k:  group selection      (which groups to correct)
  δ_t^k:  correction vector    (how much to correct per group)

Bounding:
  tanh ensures ||δ_t^k|| ≤ δ_max (prevents correction module from dominating base WM)
  δ_max = 0.1 ~ 0.5 latent std (initial: 0.25)

Correction size penalty:
  L_corr_size = Σ_k ||α_t^k · δ_t^k||₂²
  (prevents correction from absorbing all base WM prediction errors)
```

## Why Transition Adapter > Direct z_t Edit

Option (a) edits current state belief — unstable if encoder z_t is already well-calibrated.
Option (b) edits only next prediction — misses persistent regime context accumulated in h_t.
Option (c) as full transition adapter: base WM is preserved as H0 reference; correction module
captures conditional residual. Analogous to adapter layers in NLP fine-tuning.

## Connection Map
- Upstream: M-8 (β_t gate), M-9 (α_t attention), M-6 (μ_t base prediction)
- Downstream: M-12 (value relevance validates δ), M-13..M-15 (nec/suf/contrast)
- Algorithm: R-1 (SCM: δ is the intervention on mediating gate), R-9 (CIRCA correction path)

## Checkpoints

- C1 Math validity: PASS — tanh bounding + β_t · α_t^k · δ_t^k formulation is well-defined.
  The correction-size penalty is a valid regularizer. No mathematical inconsistency.
- C2 Novelty: CONDITIONAL — ReDRAW comparison critical (see Attack 2 from reviewer-2).
  Distinction: L_nec + L_suf + value-aware selection vs. uniform residual adapter.
- C3 Reviewer attack: MEDIUM — Attack 2: "this is ReDRAW." Defense requires running
  BASE-ReDRAW baseline and showing FGLC > uniform-α ablation on control metrics.
- C4 Feasibility: PASS — per-group MLP correction is lightweight (~50k params per group).
- C5 Claim-metric: Correction validated by: ABL-no-attention, ABL-no-correction,
  necessity (L_without - L_with > margin), sufficiency (L_selected ≈ L_full).
- C6 Impl risk: LOW — Standard MLP architecture; tanh bounding well-understood.
- C7 Experiment design: Required ablations: no-correction (base WM only), no-attention
  (uniform α), no-falsification-gate (always-correct).
- C8 Failure interp: Failure mode 1: correction too strong → base WM doesn't learn.
  Mitigation: L_corr_size + δ_max clamp + staged training (freeze base in Stage 2).
- C9 Related work: ReDRAW (residual WM), AdaWM — PENDING ≥2 sources
- C10 Context routing: Source = main.md §8-9. Downstream: 09_NECESSITY_SUFFICIENCY.md,
  10_LOSS_DESIGN.md, 11_PLANNING_THEORY.md
