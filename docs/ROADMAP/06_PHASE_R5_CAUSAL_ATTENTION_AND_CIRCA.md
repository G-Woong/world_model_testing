# Phase R5 — Causal Attention and CIRCA

## Goal
Implement intervention-policy attention α_t, randomized Bernoulli gate for τ_g estimation,
α-distillation from τ_g, and CIRCA training loop.
Gate: corrected NLL < uncorrected NLL on OOD conditions.

## Inputs
- Prior phase sentinel: outputs/phase_gates/R4.passed
- Code: src/fglc/attention/causal.py, src/fglc/correction/adapter.py

## Steps

1. Implement attention module
   ```python
   class InterventionPolicyAttention(nn.Module):
       # Input: [ρ_t, σ_t, a_t, h_t, value_signal]
       # Output: α_t ∈ Δ^K (sparse, group-level)
       # Options: softmax → entmax → top-k (staged)
   ```

2. Implement randomized Bernoulli gate (CIRCA-specific)
   ```python
   def sample_random_gate(pi, training=True):
       if training:
           m = torch.bernoulli(pi)  # straight-through estimator for gradients
       else:
           m = (alpha > 0.5).float()  # hard selection at inference
       return m
   ```

3. Estimate τ_g utility effects
   ```python
   # For each group g:
   # U(m=1) = -NLL(z_next | corrected_with_group_g) + λQ(...)
   # U(m=0) = -NLL(z_next | without_group_g) + λQ(...)
   # τ_g = E[U(m=1)] - E[U(m=0)]  (difference-in-means)
   ```

4. Implement α-distillation loss
   ```python
   L_align = ||α - Normalize(clamp(τ_g, min=0))||²
   ```

5. Stage 2 CIRCA training: freeze base WM, train β-gate + attention + correction adapter

## Gate Criteria (all must be true for R5.passed)

- [ ] Corrected NLL < uncorrected NLL on OOD-mass (> 0.1 nat improvement)
- [ ] τ_g > 0 for at least 1 group per OOD condition (p < 0.05, t-test, 100 episodes)
- [ ] Attention entropy < 1.0 nats (sparse attention active)
- [ ] ABL-no-attention baseline run: uniform α=1/K (comparison ready for R9)
- [ ] `pytest tests/test_fglc_circa.py` green

## Risk Register References
- R-1: Off-manifold intervention — monitor ||z̃_t - z_t|| < 3*δ_max
- R-6: Straight-through estimator instability for Bernoulli gate

## Commit Cadence
- commit 1: `feat(attn): R5 intervention-policy attention (softmax phase)`
- commit 2: `feat(attn): R5 CIRCA Bernoulli gate + τ_g estimation`
- commit 3: `feat(train): R5 Stage 2 CIRCA training loop`
- commit 4: `results(R5): corrected NLL < uncorrected NLL on OOD verified`

## Codex Delegation
Yes → Codex TASK_R5_CIRCA.md
