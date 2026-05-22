# 13_ALGORITHM_CIRCA — Causal Intervention Randomized Conformal Attention

## Source
- deep-research-report.md §CIRCA (R-9), §이론 점검을 통과하는 알고리즘 골격

## Priority: 1 (primary FGLC algorithm)

## Claim

CIRCA is the primary FGLC algorithm. It combines:
1. **Randomized Bernoulli gate** for average treatment effect (τ_g) estimation
2. **Conformal falsification gate** for calibrated detection
3. **α-distillation** aligning attention with positive τ_g effects
4. **Robust MPC** for action selection under corrected latent

This is the algorithm that most directly addresses all 5 Reviewer-2 attacks:
- Attack 1: τ_g estimation provides intervention-validated attention
- Attack 2: value-aware distillation separates CIRCA from pure residual adapters
- Attack 4: conformal gate separates CIRCA from anomaly detection

## Mathematical Formalization

```
CIRCA Total Loss:
  L_CIRCA = L_wm
           + β · L_conf          [conformal calibration]
           + γ · ||α - Norm(τ̂_+)||²  [attention-τ_g alignment]
           + ρ · ||m||₁          [sparsity on gate]
           - ξ · ΔQ_robust       [value improvement]

where:
  τ̂_g = E[U_t | do(m^(g)=1)] - E[U_t | do(m^(g)=0)]   [average treatment effect]
  U_t = -NLL(z_{t+1} | z̃_t) + λQ(z̃_t, a_t)            [utility: prediction + value]
  Norm(τ̂_+)_g = max(0, τ̂_g) / Σ_k max(0, τ̂_k)

Training Algorithm:
  1. Learn base world model pθ and value head Qψ on ID trajectories
  2. Partition latent z into G groups; gate-net outputs π = σ(a(z, h))
  3. Sample randomized gate: m ~ Bernoulli(π); compute intervened z̃ = z + m ⊙ δ
  4. Compute factual/intervened utility U = -NLL + λQ
  5. Estimate group effects τ̂_g from randomized interventions (IPW or difference-in-means)
  6. Update gate-net so attention α aligns with positive τ̂_g; enforce sparsity
  7. Fit conformal/CRC calibration set on residual scores s_t on held-out ID data

Inference:
  1. If s_t ≤ calibrated threshold: use base planner (no correction)
  2. Else select top-k groups by α_t
  3. Optimize δ only on selected groups
  4. Choose action by robust MPC under corrected latent z + m⊙δ

Complexity: O(BT(C_wm + G) + k·H·C_plan)
  B = batch size, T = horizon, G = groups, k = top-k, H = planning horizon
```

## Key Properties

| Property | CIRCA | Standard residual | Random gate |
|---|---|---|---|
| Intervention validity | τ_g (ATE) | None | By construction |
| Detection calibration | Conformal (finite-sample) | None | None |
| Action relevance | -ξΔQ_robust | None | None |
| Attention alignment | τ_g-distill | N/A | N/A |

## Connection Map
- Upstream: R-1 (SCM gate), R-6 (conformal), R-8 (robust MPC), M-9 (α), M-8 (β)
- Algorithm peers: 14_ALGORITHM_ASAP.md, 15_ALGORITHM_I3G.md, 16_ALGORITHM_IVI.md
- Downstream: 17_ALGORITHM_COMPARISON.md, 11_PLANNING_THEORY.md

## Checkpoints

- C1 Math validity: CONDITIONAL — ATE estimation via IPW/difference-in-means valid under
  positivity + ignorability. Positivity: α_t^k ∈ (0,1) required during training (not hard 0/1).
  Ignorability: m_t^k ~ Bernoulli(π) randomizes conditioning on z_t,h_t context.
  Risk: if Bernoulli sampling disrupts latent manifold, τ_g estimates may be off-manifold.
- C2 Novelty: CONDITIONAL — CIRCA as combination is NOT present in prior literature per
  deep-research-report.md §실무적으로 "현재 공개 문헌에서 정면으로 동일한 형태로 정리된 예는 드뭅니다."
  However, each component exists. Novelty claim: the specific combination in WM context.
- C3 Reviewer attack: MEDIUM (managed) — τ_g randomization addresses Attack 1.
  Off-manifold intervention risk (Attack 1 failure mode): low-rank correction constraint mitigates.
- C4 Feasibility: CONDITIONAL — τ_g estimation adds ~20% training overhead per main report.
  IPW estimator is simple; DR estimator more complex. Phase 1: difference-in-means sufficient.
- C5 Claim-metric: τ_g significance (t-test p<0.05 per group, 500 OOD episodes).
  Conformal coverage rate at level α on held-out ID (must match claimed α).
- C6 Impl risk: MEDIUM — Bernoulli sampling during training needs gradient flow via
  straight-through estimator or Gumbel-softmax.
- C7 Experiment design: CIRCA vs. I3G vs. ASAP vs. IVI on same benchmark. All algorithms
  must share identical base WM (Stage 1 weights).
- C8 Failure interp: If τ_g ≈ 0 for all groups: correction has no interventional utility.
  Implication: the world model dynamics are already accurate enough for planning under shift.
- C9 Related work: Bernoulli gate intervention theory, CRC (Angelopoulos 2022) — PENDING ≥2 sources
- C10 Context routing: Source = deep-research-report.md §CIRCA. Downstream: 17_ALGORITHM_COMPARISON.md
