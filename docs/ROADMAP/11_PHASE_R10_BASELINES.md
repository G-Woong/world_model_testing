# Phase R10 — Baselines

## Goal
Train and evaluate all required baselines (19_BASELINES.md). Critical: compute-matched baseline.

## Baselines Priority

### High Priority (paper main claim)
1. TD-MPC2 (reference baseline) — use published code if available; else re-implement
2. BASE-COMP-04 (compute-matched random realloc) — critical for Attack 5 defense
3. BASE-ABL-01 (no-correction) — already in R9
4. BASE-ORACLE-01..04 (oracle upper bounds) — feasible in ManiSkill sim

### Medium Priority (related work comparison)
5. HiP-RSSM — need to implement or find public code
6. DreamerV3 — use published JAX code adapted for ManiSkill
7. BASE-ABL-03 (CUSUM verifier-only)
8. BASE-ABL-04 (SPRT verifier-only)

### Lower Priority (if budget allows)
9. PLSM, ReDRAW, AdaWM

## Gate Criteria
- [ ] TD-MPC2 baseline evaluated on all OOD conditions
- [ ] Compute-matched baseline (BASE-COMP-04) run — same planning rollouts as FGLC
- [ ] Oracle baselines run (mass/friction) — provide upper bound reference
- [ ] Results table complete: FGLC vs. TD-MPC2 vs. HiP-RSSM vs. compute-matched

## Risk Register
- R-3: HiP-RSSM requires RSSM base; may need custom ManiSkill adaptation
- R-4: DreamerV3 JAX→PyTorch port for ManiSkill may be complex
