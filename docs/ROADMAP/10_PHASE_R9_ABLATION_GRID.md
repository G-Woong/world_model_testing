# Phase R9 — Ablation Grid

## Goal
Run all 11 ablation families from docs/idea/20_ABLATIONS.md. Report per-OOD-condition results.

## Ablation Execution Order (priority)

1. ABL-01 (no-correction) — validates problem existence
2. ABL-08 (K=1 collapsed latent) — validates decomposition necessity
3. ABL-02 (no-attention, uniform α) — validates selection contribution
4. ABL-10 (no-conformal-calibration) — validates calibration contribution
5. ABL-03 (no-falsification-gate) — validates β_t compute savings
6. ABL-05 (no-value) — validates value-aware loss
7. ABL-04 (random-mask) — validates non-randomness
8-11. ABL-06, ABL-07, ABL-09, ABL-11 — secondary

## Stop Conditions

- ABL-01 ≈ FGLC: STOP — problem existence fails
- ABL-02 ≈ FGLC: STOP — attention adds nothing above uniform
- ABL-08 ≈ FGLC: STOP — K=1 sufficient; no group decomposition needed

## Gate Criteria
- [ ] All 11 ablations run (3 seeds, 5 OOD conditions, 100 eval episodes each)
- [ ] ABL-01 < FGLC on OOD return (p < 0.05) — problem existence
- [ ] ABL-02 < FGLC on return/recovery (effect size > 0.3σ)
- [ ] Results table complete for paper
