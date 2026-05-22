# 09_NECESSITY_SUFFICIENCY

## Source
- main.md §11 (necessity/sufficiency validation)
- deep-research-report.md §SCM/do-intervention (R-1), §Shapley/ASV (R-3)

## Claim

Attention-guided correction can be partially validated via necessity, sufficiency, and
random-mask contrast losses. These do NOT prove causal identifiability but constitute
**intervention-level validation**: the selected mask (a) is necessary for performance,
(b) alone is sufficient for near-full-correction performance, (c) outperforms random selection.

## Mathematical Formalization

```
Let:
  L_with    = prediction/value loss after selected correction (top-k by α)
  L_without = prediction/value loss with selected correction removed
  L_full    = prediction/value loss with all groups corrected
  L_random  = prediction/value loss with random k groups corrected
  m_selected = top-k groups by α_t (correction mask)

Necessity:
  L_nec = max(0, margin - (L_without - L_with))
  Goal: L_without > L_with  →  removing selected groups hurts
  
Sufficiency:
  L_suf = |L_selected - L_full|
  Goal: L_selected ≈ L_full  →  selected groups alone capture most benefit

Random contrast:
  L_rand = max(0, margin - (L_random - L_selected))
  Goal: L_selected < L_random  →  better than random group selection

Training schedule:
  Stage 1: base WM only (no nec/suf)
  Stage 2: add L_nec + L_suf + L_rand
  (necessity/sufficiency losses require base WM to be reasonably trained first)
```

**Limitation**: L_nec validates that selected groups ARE needed (if removed, performance drops).
L_suf validates that selected groups ARE sufficient. But this does NOT prove that α_t has
identified the *causally correct* group — only that the intervention is effective.
True causal identification requires ground-truth factor access (available in sim via sim's
physical parameter assignments) or randomized τ_g estimation (CIRCA).

## Connection Map
- Upstream: M-9 (α_t selection), M-10 (correction δ_t), M-12 (value relevance)
- Downstream: M-16 (total loss includes L_nec+L_suf+L_rand)
- Algorithm: R-1 (SCM necessity is ~τ_g > 0), R-3 (Shapley sufficiency interpretation)
- Metrics: 21_METRICS.md §attribution axis

## Checkpoints

- C1 Math validity: PASS — L_nec, L_suf, L_rand are well-defined hinge/absolute losses.
  Margin term is a hyperparameter, not a learnable threshold.
- C2 Novelty: CONDITIONAL — Necessity/sufficiency testing for attention has been proposed.
  Novel aspect: applying it as training losses (not just eval tests) in a WM context.
- C3 Reviewer attack: MEDIUM — "Necessity/sufficiency doesn't prove causal attribution."
  Defense (documented): This is intervention-level validation, not causal proof. Ground-truth
  sim provides causal oracle for additional validation (mask precision/recall vs. changed factor).
- C4 Feasibility: PASS — All three losses are standard differentiable operations.
- C5 Claim-metric: Necessity-Δ, Sufficiency-Δ, Random-Δ in 21_METRICS.md §attribution axis.
  Also: sim ground-truth mask precision/recall (OOD mass activated z^1 group primarily?).
- C6 Impl risk: LOW
- C7 Experiment design: Required: quantify each metric. Show that selected mask achieves
  Necessity-Δ > 0.2 and Sufficiency-Δ < 0.1 under OOD conditions.
- C8 Failure interp: If L_without ≈ L_with (necessity fails): selection is redundant.
  If L_selected << L_full (sufficiency fails): selected groups insufficient, k is too small.
- C9 Related work: Jain & Wallace removal-based evaluation; Shapley (Frye 2020 ASV) — PENDING
- C10 Context routing: Source = main.md §11. Downstream: 10_LOSS_DESIGN.md, 21_METRICS.md
