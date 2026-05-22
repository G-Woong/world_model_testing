# 05_BELIEF_MEMORY

## Source
- main.md §4.2 (belief memory h_t)
- deep-research-report.md §I3G algorithm (R-11), HiP-RSSM comparison

## Claim

A GRU-based belief memory h_t is necessary for detecting persistent dynamics shifts.
Without temporal context, β_t cannot distinguish a one-step noise spike (ID) from a
regime change that will persist for 10+ steps (OOD mass/friction/action-gain).

## Mathematical Formalization

```
h_t = GRU(h_{t-1}, [flatten(z_t), a_{t-1}, r_{t-1}])

Input dim: K*d + D_a + 1 = 192 + 7 + 1 = 200
Hidden dim: h_dim = 256
Output: h_t ∈ R^256

Used in:
  β_t = sigmoid(MLP([F_1,...,F_K, F_total, h_t]))   [falsification gate]
  α_t = SparseAttention(ρ_t, z_t, a_t, h_t, ∇Q)    [correction attention]
  δ_t^k = tanh(MLP([z_t^k, ρ_t^k, a_t, h_t]))       [correction module]
```

**Physical justification**: Hidden regime properties (mass, friction) cannot be inferred
from a single observation. Multiple observations are needed:
- Cup weight: push → feel → update belief
- Friction change: slide distance over multiple steps

h_t serves the same role as DreamerV3's RSSM deterministic state, but without requiring
full image reconstruction (decoder-free design).

## HiP-RSSM Comparison

HiP-RSSM (Achterhold et al. 2022) uses context-conditioned RSSM where latent parameters
encode different dynamical systems. The key difference:
- HiP-RSSM: parametric inference of which dynamics family applies
- FGLC: belief h_t accumulates evidence; β_t decides IF falsification occurred;
  α_t decides WHERE correction applies. No explicit parameter inference.

## Connection Map
- Upstream: M-4 (encoder), M-6 (dynamics produces μ_t,σ_t with h_t input)
- Downstream: M-8 (β_t gate), M-9 (α_t attention), M-11 (correction δ_t), R-11 (I3G context)
- Baselines: HiP-RSSM (parameter inference vs. belief accumulation comparison)

## Checkpoints

- C1 Math validity: PASS — GRU is standard; h_t dimensionality is tractable.
- C2 Novelty: NOT CLAIMED — GRU belief is standard. Novelty is in how h_t is used.
- C3 Reviewer attack: LOW — Well-established component. Main attack would be "RSSM stochastic
  component might be better" (defensible: decoder-free RSSM stochastic is more complex, deferred to R11).
- C4 Feasibility: PASS — 256-dim GRU, standard.
- C5 Claim-metric: C5-conditional — Must show β_t autocorrelation under regime shift > 0.6
  (Attack 4 from reviewer-2 defense). h_t provides this temporal context.
- C6 Impl risk: LOW
- C7 Experiment design: Ablation: belief-less β_t (use only ρ_t without h_t).
  Hypothesis: without h_t, false alarm rate on ID noise increases significantly.
- C8 Failure interp: If h_t doesn't help discriminate, it suggests regime shifts are
  detectable from single-step ρ_t alone (possible for large shifts). Not catastrophic.
- C9 Related work: HiP-RSSM arXiv 2206.14697 — PENDING ≥2 sources
- C10 Context routing: Source = main.md §4.2. Downstream: 02_FALSIFICATION_THEORY.md,
  06_CAUSAL_ATTENTION.md.
