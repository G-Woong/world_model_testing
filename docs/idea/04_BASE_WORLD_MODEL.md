# 04_BASE_WORLD_MODEL

## Source
- main.md §1 (base WM choice), §4 (encoder + belief + dynamics)
- deep-research-report.md §요약 (TD-MPC2 / Dreamer recommendation)

## Claim

TD-MPC2-style decoder-free latent world model is the recommended base, with RSSM-like
GRU belief memory added for partial observability. This is NOT a contribution claim —
it is the **foundation on top of which the novel FGLC modules operate**.

## Architecture

```
State encoder (MLP, state-only Phase 1):
  E: x_t ∈ R^{D_x} → z_t = [z_t^1,...,z_t^K] ∈ R^{K×d}
  x_norm = (x - mean_train) / std_train
  E = Linear(D_x→256) → SiLU → LayerNorm → Linear(256→256) → SiLU → Linear(256→K*d)
  Reshape: [K*d] → [K, d]

Belief memory (GRU):
  h_t = GRU(h_{t-1}, [flatten(z_t), a_{t-1}, r_{t-1}])
  h_dim = 256

Group interaction transformer:
  tokens = [z_t^1,...,z_t^K, action_token, belief_token]
  Z'_t = 2-layer Transformer (d_model=32~64, heads=4)
  NOTE: this is a DYNAMICS INTERACTION layer, NOT causal attention
  
Base dynamics prior (per-group MLP + group interaction):
  μ_t^k, logσ_t^k = GroupDynamicsMLP_k([Z'_t^k, a_embed, h_embed])
  pθ(z_{t+1}^k | z_t, a_t, h_t) = N(μ_t^k, diag((σ_t^k)²))

Reward/value heads:
  r̂_t = Rθ(flatten(z_t), a_t, h_t)
  Q̂_t = Qθ(flatten(z_t), a_t, h_t)
  V̂_t = Vθ(flatten(z_t), h_t)
```

**Why decoder-free (TD-MPC2-style)?**
- FGLC needs action-predictive latent, not image-reconstructive latent
- Decoder-free avoids pixel reconstruction overhead in Phase 1
- Latent planning (MPPI/CEM) operates directly in z-space

**Why add GRU belief (RSSM-like)?**
- Physical parameter shifts (mass/friction) are NOT visible in single observation
- h_t accumulates evidence of hidden regime over multiple timesteps
- Without h_t, β_t gate cannot distinguish persistent dynamics shift from transient noise

## Differentiation

| Approach | h_t memory | Decoder | Target |
|---|---|---|---|
| TD-MPC2 pure | None | None | Continuous control (reference) |
| DreamerV3 | RSSM | Decoder | Pixel reconstruction + planning |
| FGLC (ours) | GRU belief | None | Falsification-guided correction |

## Connection Map
- Upstream: M-3 (grouped latent), docs/main/main.md §1-4
- Downstream: M-7 (mismatch uses μ_t,σ_t), M-8 (gate uses h_t), M-9 (attention uses h_t)
- Baselines: TD-MPC2, DreamerV3 (direct comparisons in 19_BASELINES.md)

## Checkpoints

- C1 Math validity: PASS — Architecture is standard; no novel mathematical claims here.
  Conditional: group interaction transformer is labeled correctly as "dynamics layer" not "causal."
- C2 Novelty: NOT CLAIMED — Base WM is a standard building block. Novelty is in FGLC modules.
- C3 Reviewer attack: LOW — No novel claim; description matches published TD-MPC2/RSSM literature.
- C4 Feasibility: PASS — TD-MPC2 state-only on ManiSkill: ~2M params, A100 compatible.
  Stage 1 training ~2h per task; feasible in 8-week A100 budget.
- C5 Claim-metric: N/A for base WM itself. Stage 1 gate: ID one-step NLL ≤ 0.1 nat.
- C6 Impl risk: LOW — Standard MLP/GRU/Transformer architecture, well-tested.
- C7 Experiment design: Stage 1 training required before any correction module.
- C8 Failure interp: If base WM fails to learn ID dynamics (NLL doesn't decrease),
  all downstream claims are invalid. Gate: ID NLL convergence check required before R4.
- C9 Related work: TD-MPC2 (Hansen 2024, arXiv:2310.16828) — PENDING ≥2 sources
- C10 Context routing: Source = main.md §1-4. Consumers: 02_FALSIFICATION_THEORY.md,
  05_BELIEF_MEMORY.md, 12_TRAINING_STAGES.md
