# Phase R6 — Correction Module

## Goal
Implement per-group correction MLP δ_t^k with tanh bounding and necessity/sufficiency losses.
Gate: L_nec (necessity) and L_suf (sufficiency) tests pass at required thresholds.

## Inputs
- Prior phase sentinel: outputs/phase_gates/R5.passed

## Steps

1. Implement correction adapter (src/fglc/correction/adapter.py)
   ```python
   class CorrectionAdapter(nn.Module):
       def forward(self, z_k, rho_k, a, h):
           raw = MLP(concat(z_k, rho_k, a, h))  # → d
           delta_k = delta_max * torch.tanh(raw)
           return delta_k  # bounded correction
   
   def corrected_dynamics(mu, beta, alpha, delta, groups):
       # mu_tilde_k = mu_k + beta * alpha_k * delta_k
       return mu + beta.unsqueeze(-1) * alpha.unsqueeze(-1) * delta
   ```

2. Add correction-size penalty L_corr_size
3. Add temporal consistency loss L_temporal (α_t ≈ α_{t+1})
4. Implement necessity/sufficiency/random-contrast losses
5. Measure per-group correction size across OOD types

## Gate Criteria

- [ ] Necessity test: L_without - L_with > 0.05 nat on OOD-mass (correction selected groups are needed)
- [ ] Sufficiency test: |L_selected - L_full| < 0.1 nat (selected groups sufficient)
- [ ] Random contrast: L_random - L_selected > 0.05 nat (better than random)
- [ ] Correction size ||δ_t^k|| < δ_max = 0.25 (no overflow)
- [ ] `pytest tests/test_fglc_correction.py` green

## Risk Register References
- R-1: Correction module captures base WM training. Monitor L_corr_size during Stage 2.
  STOP if correction size exceeds 2× base WM prediction variance.

## Commit Cadence
- commit 1: `feat(correction): R6 per-group correction adapter + tanh bounding`
- commit 2: `feat(loss): R6 necessity/sufficiency/contrast losses`
- commit 3: `results(R6): necessity+sufficiency thresholds verified`

## Codex Delegation
Yes → Codex TASK_R6_CORRECTION.md
