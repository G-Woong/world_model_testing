# Phase R3 — Base World Model

## Goal
Implement and train Stage 1: encoder + grouped latent + GRU belief + dynamics + reward/value.
Gate: ID one-step NLL converged; OOD NLL measurably higher than ID (problem existence).

## Inputs
- Prior phase sentinel: outputs/phase_gates/R2.passed
- Code: src/fglc/models/ (encoder.py, dynamics.py, belief.py)
- Data: data/fglc/ ID split

## Architecture (from docs/idea/04_BASE_WORLD_MODEL.md)

```python
K=6, d=32, h_dim=256  # hyperparameters

class FGLCBaseWorldModel(nn.Module):
    encoder    # MLP D_x→256→256→K*d, LayerNorm, SiLU
    group_transformer  # 2-layer, d_model=32~64, heads=4 (DYNAMICS layer)
    dynamics   # per-group MLP → μ_t^k, logσ_t^k
    belief     # GRU(hidden=256, input=K*d+D_a+1)
    reward_head    # MLP flatten(z)+a+h → scalar
    value_head     # MLP flatten(z)+h → scalar
```

## Steps

1. Implement `src/fglc/models/encoder.py`
2. Implement `src/fglc/models/dynamics.py` (group MLP + interaction transformer)
3. Implement `src/fglc/models/belief.py` (GRU)
4. Implement training loop `src/fglc/training/train_base_wm.py` (Stage 1 loss)
5. Run Stage 1 training (3 tasks × ID data): ~6h on A100
6. Evaluate: ID NLL convergence + OOD NLL gap measurement

## Gate Criteria (all must be true for R3.passed)

- [ ] ID one-step NLL < 0.1 nat at convergence (PickCube reference)
- [ ] OOD-mass NLL > ID NLL by > 0.2 nat (OOD challenge exists)
- [ ] OOD-friction NLL > ID NLL by > 0.1 nat
- [ ] GRU belief h_t dimensionality = 256 (matches spec)
- [ ] `pytest tests/test_fglc_base_wm.py` green (architecture shapes, forward pass)
- [ ] Run manifest saved (config, seed, dataset hash, final NLL)

## Risk Register References
- R-7: MPPI determinism — not relevant here
- R-8: Value-Q convergence — value head may be slow to converge; use bootstrapped target
- R-9: Planner-WM coupling — not applicable (Stage 1 is model-only)

## Commit Cadence
- commit 1: `feat(model): R3 encoder + grouped latent + GRU belief`
- commit 2: `feat(model): R3 group interaction transformer + per-group dynamics`
- commit 3: `feat(train): R3 Stage 1 training loop + loss`
- commit 4: `results(R3): base WM ID convergence + OOD NLL gap verified`

## Codex Delegation
Yes — multi-file model implementation → Codex TASK_R3_BASE_WM.md
