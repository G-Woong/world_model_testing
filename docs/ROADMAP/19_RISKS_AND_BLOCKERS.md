# Risks and Blockers Register

## R-1 — Latent Surgery Off-Manifold
**Likelihood**: Medium | **Impact**: High
**Description**: Correction vectors push z̃_t outside the valid latent manifold.
**Detection**: ||z̃_t - nearest_train_latent|| >> σ_latent
**Mitigation**: Low-rank correction; bounded δ_max; monitor round-trip distance

## R-2 — ManiSkill API Drift
**Likelihood**: Low | **Impact**: Medium
**Description**: ManiSkill v3 API changes break data collection scripts.
**Mitigation**: Pin mani-skill version in pyproject.toml; test against pinned version

## R-3 — HiP-RSSM/DreamerV3 Porting Complexity
**Likelihood**: Medium | **Impact**: Medium
**Description**: Adapting HiP-RSSM (JAX) or DreamerV3 (JAX) to ManiSkill may require significant effort.
**Mitigation**: Find existing PyTorch forks; if unavailable, use simplified re-implementation for baseline

## R-4 — DROID Dataset Access
**Likelihood**: Medium | **Impact**: Low (Phase 2 only)
**Description**: DROID ~100GB; requires institutional access.
**Mitigation**: Phase 1 (state-only ManiSkill) is sufficient for paper main results; DROID is supplementary

## R-5 — σ Calibration Failure
**Likelihood**: Medium | **Impact**: Critical
**Description**: Base WM learns inflated σ; OOD detection AUROC → 0.5.
**Mitigation**: L_cal penalty; σ clamp; ECE check is R4 gate criterion; STOP if ECE > 0.2

## R-6 — Conformal Coverage Under Non-Exchangeable OOD
**Likelihood**: Medium | **Impact**: Medium
**Description**: Conformal guarantees assume exchangeability; OOD data may violate this.
**Mitigation**: Use empirical quantile calibration (not strict conformal) as primary; report both

## R-7 — MPPI Determinism
**Likelihood**: Low | **Impact**: Medium
**Description**: MPPI sampling introduces variance; results may not be reproducible.
**Mitigation**: Fixed seed for MPPI sampling; report mean ± std over 3 seeds

## R-8 — Value-Q Convergence Slow
**Likelihood**: Medium | **Impact**: Low
**Description**: Value/Q head may take many episodes to converge; bootstrapping unstable.
**Mitigation**: Use n=3 step TD target initially; reduce horizon if unstable

## R-9 — Planner-WM Coupling
**Likelihood**: Medium | **Impact**: Medium
**Description**: Planner gradients may interfere with correction module training.
**Mitigation**: Stage 3 (planner) only after Stage 2 (correction) converged; separate LR schedule

## R-10 — Entmax Stability
**Likelihood**: Low | **Impact**: Low
**Description**: entmax gradient may be numerically unstable for very small temperatures.
**Mitigation**: Clip logits before entmax; use temperature schedule starting from softmax

## R-11 — RGB-D Encoder Compute
**Likelihood**: High | **Impact**: Low (Phase 2 optional)
**Description**: ViT encoder + RGB-D may not fit in single A100 batch.
**Mitigation**: Reduce batch size; use smaller CNN; defer to R11 if budget exceeded

## R-12 — K=6 Cross-Seed Inconsistency
**Likelihood**: Medium | **Impact**: High
**Description**: Spearman correlation < 0.7 across seeds for per-OOD attention vectors.
**Mitigation**: Reduce K; add explicit group-separation loss; if unresolvable, reduce claim

## R-13 — Compute Budget Overrun
**Likelihood**: Medium | **Impact**: High
**Description**: 60+ eval runs (4 algorithms × 3 tasks × 5 OOD conditions) may exceed 8-week budget.
**Mitigation**: Run CIRCA+IVI first; add ASAP+I3G if budget allows; 3 tasks minimum

## R-14 — Real Robot Transfer (DROID/BridgeData) Fails
**Likelihood**: Medium | **Impact**: Low
**Description**: FGLC correction doesn't generalize to real robot sensor noise.
**Mitigation**: Report limitation honestly; sim results remain valid for core claim
