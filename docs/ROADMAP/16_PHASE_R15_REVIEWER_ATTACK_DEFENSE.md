# Phase R15 — Reviewer-Attack Defense

## Goal
Pre-emptively address all 5 MAJOR reviewer-2 attacks (reviewer2_attack_fglc_R1.md).

## Required Defenses

1. **Attack 1 (causal naming)**: Either add CIRCA τ_g experiment result or rename
   to "intervention-policy attention" throughout paper. See 06_CAUSAL_ATTENTION.md.

2. **Attack 2 (ReDRAW similarity)**: Show BASE-ReDRAW baseline result; cite return improvement
   from ABL-02 (no-attention) < FGLC as distinct evidence.

3. **Attack 3 (K=6 arbitrary)**: Show cross-seed Spearman > 0.7 result + K={3,6,12} sweep
   in supplementary. Cite Locatello limitation explicitly.

4. **Attack 4 (anomaly detection)**: Show β_t autocorrelation AR(1) > 0.5 under OOD,
   < 0.1 under ID noise. Report recall/FPR discrimination table.

5. **Attack 5 (compute-matched)**: Show BASE-COMP-04 result in main table.
   If FGLC > compute-matched: "FGLC achieves better return with more targeted correction."
   If FGLC ≈ compute-matched: reduce claim to "correction is more efficient than random reallocation."

## Supplementary Appendix Requirements
- K sensitivity sweep (K=3,6,12)
- Cross-seed attention consistency (5-seed Spearman per OOD type)
- β_t temporal correlation analysis
- τ_g significance per group per OOD type
- Full ablation table with standard deviations

## Gate Criteria
- [ ] All 5 attacks addressed in paper text or supplementary
- [ ] Supplementary appendix complete
- [ ] fglc-related-work-scout run on final related work section
