# Phase R13 — Necessity/Sufficiency Deep Evaluation

## Goal
Evaluate attribution quality using sim ground-truth factor oracle.
Report mask precision/recall for each OOD type vs. known changed physical parameter.

## Steps

1. For each OOD condition, measure which group has highest α_t (mean over 100 episodes)
2. Compare with ground-truth changed factor:
   - OOD-mass → expect z^context or z^action_gain group activated
   - OOD-friction → expect z^contact or z^object group activated
   - OOD-latency → expect z^action_gain group activated
3. Compute precision/recall of top-1 group selection vs. ground-truth factor

## Gate Criteria
- [ ] Mask precision of top-1 group > 0.5 on at least 2 OOD conditions
- [ ] Cross-seed consistency: Spearman ρ > 0.7 across 5 seeds (per OOD type)
- [ ] τ_g significance confirmed: p < 0.05 for the top activated group

## Risk Register
- Q3 (24_OPEN_QUESTIONS): Latent group assignments may not correspond to expected physical factors
  If precision < 0.5: groups don't cleanly correspond to single physical parameters (multi-factor groups)
