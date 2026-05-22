# 14_ALGORITHM_ASAP — Asymmetric Shapley Attention Planning

## Source
- deep-research-report.md §ASAP (R-10), §Shapley·removal-based·ASV (R-3)

## Priority: 3

## Claim

ASAP uses top-k attention as a fast proposal engine, then validates corrections using
Monte Carlo interventional Asymmetric Shapley Values (ASV). ASV respects causal order
among latent groups (e.g., context → dynamics → reward). Computationally expensive
but provides the strongest formal guarantee for interaction effects.

## Mathematical Formalization

```
Interventional value function:
  v(S) = E[-NLL(S) + λQ(S)]   where S = set of corrected groups

Asymmetric Shapley Value:
  φ_i^ASV = ordered-Shapley(v)  [respects causal ordering of groups]
  (non-permitted orderings excluded from coalition averaging)

ASAP Training:
  1. Train world model and planner/value head
  2. Gate-net proposes top-k latent groups via attention
  3. On top-k only: Monte-Carlo estimate of interventional ASV using v(S)
  4. Distill normalized ASV into attention α
  5. Use conformal gate on mismatch before correction

ASAP Inference:
  1. Trigger on calibrated mismatch
  2. Recompute small-budget ASV on top-k groups
  3. Correct only groups with positive ASV and sufficient effect size

Complexity: O(2^k · n_mc) where k = top-k selection, n_mc = MC samples
  Practical: k=2~3, n_mc=20 → O(4~8 × 20) = 80~160 forward passes per step
  → Suitable for planning time-scale, not real-time policy
```

## When ASAP Wins (vs. CIRCA)

ASAP captures interaction effects: "groups 2 AND 4 together cause shift, not individually."
CIRCA estimates marginal τ_g per group (may miss interactions).
Expected superiority: shift conditions where multiple groups co-shift
(e.g., OOD-mixed: mass + friction + action-gain simultaneously).

## Connection Map
- Upstream: R-3 (Shapley/ASV), M-9 (attention α), R-6 (conformal gate)
- Algorithm peers: 13_ALGORITHM_CIRCA.md, 15_ALGORITHM_I3G.md, 16_ALGORITHM_IVI.md
- Downstream: 17_ALGORITHM_COMPARISON.md

## Checkpoints

- C1 Math validity: CONDITIONAL — ASV with causal order requires known causal graph.
  Causal order among latent groups (z^1=proprioception → z^2=object → z^3=contact) is
  an assumption, not derived. Wrong ordering gives wrong ASV. Risk: if causal order is
  ambiguous, ASV reduces to standard Shapley.
- C2 Novelty: CONDITIONAL — Interventional Shapley in RL/WM context is relatively new.
- C3 Reviewer attack: HIGH — "Too expensive for real deployment." Defense: ASAP is a
  research comparison for understanding interaction effects; CIRCA is the deployable algorithm.
- C4 Feasibility: CONDITIONAL — k=2, n_mc=20: feasible at planning time. k=4, n_mc=50: 
  ~250 forward passes per step; too slow for fast manipulation (>30Hz). Batch eval only.
- C5 Claim-metric: ASV values provide group importance scores per OOD condition.
  Compare with CIRCA τ_g: do they agree? Discrepancy = interaction effects present.
- C6 Impl risk: MEDIUM — MC Shapley estimation + gradient propagation through ASV.
- C7 Experiment design: Side-by-side comparison: CIRCA vs. ASAP on OOD-mixed conditions.
  Hypothesis: ASAP > CIRCA specifically under multi-factor OOD.
- C8 Failure interp: If ASAP ≈ CIRCA across all conditions: interactions are weak; Shapley
  overhead not justified. Reduce ASAP role to ablation only.
- C9 Related work: Frye et al. (2020) ASV; Shapley+RL — PENDING ≥2 sources
- C10 Context routing: Source = deep-research-report.md §ASAP. Downstream: 17_ALGORITHM_COMPARISON.md
