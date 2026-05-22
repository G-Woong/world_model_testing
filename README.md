# FGLC

**FGLC: Falsification-Guided Latent Correction for Robotics World Models.**

This is not a generic robotics world model.
The target is falsification-guided latent correction:
standardized predictive mismatch → dynamics hypothesis falsification
→ causal attention over grouped latent subspace → sparse residual correction
→ necessity/sufficiency validation → robust MPC planning.

---

## Core Equations

```
pθ(z_{t+1}|z_t,a_t,h_t) = N(μ_t, Σ_t)
ρ_t = Σ_t^{-1/2}(z_{t+1} − μ_t)          [standardized mismatch]
β_t = FalsificationGate(ρ_t, h_t)          [calibrated β gate]
α_t = CausalAttention(ρ_t, z_t, a_t, ∇Q)  [sparse, value-aware]
μ̃_t^k = μ_t^k + β_t α_t^k δ_t^k         [grouped latent correction]
```

## Status

- R0: ✅ Contract reset complete (FRCG-WM → FGLC pivot)
- R1..R16: Pending (see `docs/ROADMAP/00_ROADMAP_OVERVIEW.md`)

## Package

```python
import fglc  # src/fglc/ (stub — full implementation in R1+)
```

## Documentation

- Architecture: `docs/main/main.md`
- Methodology survey: `docs/main/deep-research-report.md`
- Idea units (44 atomic): `docs/idea/00_OVERVIEW.md`
- Roadmap (R0..R16): `docs/ROADMAP/00_ROADMAP_OVERVIEW.md`

## Algorithms

| Algorithm | Priority | Key mechanism |
|---|---|---|
| CIRCA | 1 | Randomized Bernoulli gate + conformal + α-distill + robust MPC |
| I3G | 2 | iVAE + ICP/anchor + SPCI gate + sparse group gates |
| ASAP | 3 | Top-k proposal + MC interventional ASV + α-distill |
| IVI | 4 | Influence-rank + randomized knockout + sparse α-distill |

## Benchmarks

ManiSkill PickCube/PushCube/LiftCube (state-only → RGB-D)
OOD axes: mass × {0.5,1,2} / friction × {0.5,1,2} / latency / noise / action-gain
Transfer: robosuite, DROID, BridgeData V2
