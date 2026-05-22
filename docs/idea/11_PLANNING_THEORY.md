# 11_PLANNING_THEORY

## Source
- main.md §14 (planning structure), §20.2-20.3 (rollout loop)
- deep-research-report.md §Robust control·DRO (R-8), §Inference decision flow (R-17)

## Claim

The planner uses MPPI/CEM over corrected latent rollouts. The correction mask α_t, δ_t
obtained from the current timestep is extrapolated for H_corr=3~5 future steps
(short-horizon hold) because physical regime shifts persist across steps.
Compute savings come from using the base planner when β_t < threshold.

## Mathematical Formalization

```
Planner input:
  Current z_t, h_t; candidate action sequences A = [a_t,...,a_{t+H-1}]

Uncorrected rollout (for timesteps where β_τ is predicted low):
  ẑ_{τ+1} = fθ(ẑ_τ, a_τ, h_τ)
  r̂_τ = Rθ(ẑ_τ, a_τ)

Corrected rollout (for first H_corr=3~5 steps when β_t triggered):
  Use current (α_t, δ_t) correction mask (short-horizon hold)
  z̃_{τ+1} = fθ(z̃_τ, a_τ, h_τ) + β_τ · α_t · δ_τ    [α_t held constant for H_corr steps]
  
Total trajectory score:
  J(A) = Σ_{τ=t}^{t+H-1} γ^{τ-t} r̂_τ + γ^H V̂(ẑ_{t+H})
  
MPPI update:
  weights_i ∝ exp(J(A_i) / temperature)
  a_t* = Σ_i weights_i · a_t^i

Compute-gated planning:
  if β_t < threshold: use base planner (no correction)
  if β_t ≥ threshold: use corrected planner

Decision-relevant compute: planning calls only when action/value changes justify cost
```

## Robust MPC (CIRCA variant)

Deep-research-report §R-17 proposes robust MPC under corrected latent:
1. Calibrated falsification gate → go/no-go for correction
2. Top-k group selection by α
3. Effect re-evaluation (interventional utility check)
4. Value-improvement check
5. If improvement expected: robust MPC under corrected z̃

## Connection Map
- Upstream: M-6 (dynamics), M-8 (β_t gate), M-9 (α_t), M-11 (δ_t)
- Downstream: M-12 (return/recovery validation uses planner output)
- Algorithm: R-8 (robust MPC), R-15 (causal graph), R-17 (inference flow)

## Checkpoints

- C1 Math validity: PASS — MPPI/CEM is standard. Short-horizon hold is a heuristic
  (justified by persistence of regime shifts). Value consistency loss validated.
- C2 Novelty: CONDITIONAL — MPPI/CEM over corrected latents is the combination.
  Not novel as individual components; novel as integrated system.
- C3 Reviewer attack: Attack 5 (4-axis metrics tautological). Compute-matched baseline required.
  See reviewer2_attack_fglc_R1.md §Attack 5.
- C4 Feasibility: PASS — MPPI with 512 rollouts, H=10, A100: ~50ms per step. Feasible.
- C5 Claim-metric: Return + recovery time + planning calls per episode + worst-case return.
  ALL must be measured; compute-matched experiment required.
- C6 Impl risk: MEDIUM — integration of correction into MPPI rollout loop needs careful impl.
- C7 Experiment design: Required: compute-matched baseline. Both FGLC and baseline given
  same total planning rollouts per episode.
- C8 Failure interp: If compute-matched baseline matches FGLC: gain is from extra planning compute.
  This would mean correction improves prediction but not planning efficiency.
- C9 Related work: MPPI (Williams et al. 2017), CEM — PENDING ≥2 sources
- C10 Context routing: Source = main.md §14. Downstream: 12_TRAINING_STAGES.md, 13_ALGORITHM_CIRCA.md
