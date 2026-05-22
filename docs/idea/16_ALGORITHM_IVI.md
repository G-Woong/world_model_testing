# 16_ALGORITHM_IVI — Influence-Validated Interventions

## Source
- deep-research-report.md §IVI (R-12), §Influence functions (R-2)

## Priority: 4

## Claim

IVI uses influence functions as a fast first-pass ranker, then validates top-k candidates
via randomized knockout. The most computationally efficient algorithm, but weakest on large
dynamics shifts where local linear influence assumptions break down.

## Mathematical Formalization

```
Local influence score:
  I_g ≈ |∂U/∂z^(g)|   [gradient of utility w.r.t. group g]
  
  Full Hessian-based: I_g ≈ |∂²U/∂z^(g)∂θ · H_θ^{-1} · ∂L/∂θ|
  (approximated via HVP: Hessian-vector product)

Combined score:
  score_g = ω₁ I_g + ω₂ ΔÛ_g^{knockout}
  where ΔÛ_g = U(z with group g corrected) - U(z uncorrected)

IVI Training:
  1. Train world model + value-aware loss
  2. Compute local influence scores for latent groups
  3. Run randomized knockouts on top-k groups only
  4. Distill combined scores into sparse attention
  5. Use calibrated sequential gate before applying correction

Complexity: O(BT · C_wm + n_mc · k) where n_mc << ASAP's 2^k
  ~2-3× overhead above base WM; most practical for deployment
```

## When IVI Wins (vs. CIRCA)

IVI is fastest. For small dynamics shifts (5-10% mass change), local linear influence
captures most of the effect accurately. Expected best performance: real-time deployment,
low-budget compute, small perturbations.

Expected weakness: Large shift (2× mass change) where local approximation breaks.

## Connection Map
- Upstream: R-2 (influence functions), M-9 (α), M-11 (correction δ)
- Algorithm peers: 13_ALGORITHM_CIRCA.md, 14_ALGORITHM_ASAP.md, 15_ALGORITHM_I3G.md
- Downstream: 17_ALGORITHM_COMPARISON.md

## Checkpoints

- C1 Math validity: CONDITIONAL — Hessian approximation valid locally; breaks for large shifts.
  Influence-as-ranker (1st pass) is still valid even if full influence is imprecise.
- C2 Novelty: LOW — Influence functions for neural networks well-established (Koh & Liang 2017).
  Novel aspect: applying to group-level latent ranking in WM context.
- C3 Reviewer attack: MEDIUM — "Local method can't handle large regime shifts."
  Acknowledged limitation. IVI is a lightweight baseline, not the primary algorithm.
- C4 Feasibility: PASS — HVP computation is standard in PyTorch. Most efficient of 4 algorithms.
- C5 Claim-metric: IVI should match CIRCA on small shifts (OOD-noise, small OOD-friction).
  IVI should underperform CIRCA on large shifts (2× mass, OOD-mixed).
- C6 Impl risk: LOW — HVP via torch.autograd.functional.vjp.
- C7 Experiment design: Compare IVI vs. CIRCA across shift magnitudes. Hypothesis: IVI ≈ CIRCA
  for small shifts, IVI < CIRCA for large shifts. This validates the "use IVI for efficiency"
  recommendation.
- C8 Failure interp: If IVI ≈ CIRCA across all conditions: CIRCA's randomized interventions
  add no value. This would suggest influence-based ranking is sufficient.
- C9 Related work: Koh & Liang (2017) influence functions arXiv 1703.04730 — PENDING ≥2 sources
- C10 Context routing: Source = deep-research-report.md §IVI. Downstream: 17_ALGORITHM_COMPARISON.md
