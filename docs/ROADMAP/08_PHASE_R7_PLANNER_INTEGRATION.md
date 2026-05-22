# Phase R7 — Planner Integration

## Goal
Integrate MPPI/CEM with corrected dynamics rollout.
Gate: closed-loop FGLC > TD-MPC2 return on ≥2 OOD conditions (p < 0.05).

## Inputs
- Prior phase sentinel: outputs/phase_gates/R6.passed

## Steps

1. Implement MPPI planner (src/fglc/planning/mppi.py)
   - Base rollout: use uncorrected dynamics when β_t < threshold
   - Corrected rollout: use corrected μ̃_t for first H_corr=3~5 steps

2. Implement closed-loop evaluation loop
   ```python
   for episode in eval_episodes:
       for t in range(max_steps):
           z_t, h_t = encode_and_update_belief(obs)
           rho, F_k, F_total = compute_mismatch(z_t, ...)
           beta = gate(rho, h_t)
           if beta > threshold:
               alpha = attention(rho, z_t, a, h_t)
               delta = correction(z_t, rho, a, h_t)
           action = mppi.plan(z_t, h_t, beta, alpha, delta)
           obs, reward, done = env.step(action)
   ```

3. Compute-matched experiment
   - Give TD-MPC2 same additional planning rollouts FGLC uses for correction
   - This is BASE-COMP-04 baseline (critical for Attack 5 defense)

## Gate Criteria

- [ ] FGLC return > TD-MPC2 return on ≥2 OOD conditions (p < 0.05)
- [ ] FGLC return > no-correction baseline on ≥2 OOD conditions
- [ ] Compute-matched baseline results available (BASE-COMP-04)
- [ ] Recovery time measurement implemented (requires regime_id timestamp)
- [ ] `pytest tests/test_fglc_planner.py` green

## Risk Register References
- R-5: MPPI determinism — seed control required for reproducibility
- R-7: MPPI correction integration complexity

## Commit Cadence
- commit 1: `feat(plan): R7 MPPI/CEM latent planner (uncorrected)`
- commit 2: `feat(plan): R7 corrected rollout with H_corr short-horizon hold`
- commit 3: `results(R7): closed-loop FGLC > TD-MPC2 on OOD verified`

## Codex Delegation
Yes → Codex TASK_R7_PLANNER.md
