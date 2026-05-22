# Reviewer-2 Attack Report — FGLC

**Date**: 2026-05-22
**Agent**: reviewer-2-attack-agent (T5 deep mode)
**Verdict**: ATTACK_MANAGEABLE — 5 MAJOR attacks, all defensible with specific experiments

## Attack 1 — "Causal" Attention Is Correlation Dressed in Causal Vocabulary (MAJOR)

**ATTACK**: α_t = CausalAttention(...) naming is not justified. Jain & Wallace (2019) showed alternative attention distributions can produce identical predictions. No surgical intervention criterion is defined.

**DEFENSE**: Reframe α_t as learned intervention policy. Add CIRCA-style randomized Bernoulli gate: m_t^k ~ Bernoulli(α_t^k). Estimate τ_g = E[U|do(m^k=1)] - E[U|do(m^k=0)]. Add alignment loss ||α - Normalize(τ_+)||². Replace "causal" with "intervention-policy attention."

**VERIFICATION**: Jain-Wallace manipulation test (alternative α' with identical corrections). t-test on utility change under do(m^k=1), 500 OOD episodes, p < 0.05 per group.

## Attack 2 — This Is ReDRAW / Residual Adaptation With Extra Notation (MAJOR)

**ATTACK**: μ̃_t^k = μ_t^k + β_t α_t^k δ_t^k is a gated residual adapter. ReDRAW already does frozen base + shift detection + residual correction. What distinguishes FGLC from "K-head residual adapter with uncertainty gate"?

**DEFENSE**: L_nec + L_suf losses force value-relevance, not just prediction-error minimization. Run BASE-ReDRAW: same capacity, no α selection, uniform residual. FGLC should outperform on control metrics but not necessarily prediction metrics.

**VERIFICATION**: ABL-no-attention (uniform α=1/K). FGLC > uniform-α on return/recovery, effect size > 0.3σ, p < 0.05.

## Attack 3 — K=6 Grouping Is Arbitrary (MAJOR)

**ATTACK**: K=6 chosen for convenience. Locatello et al. (2019): unsupervised disentanglement is fundamentally unidentifiable without auxiliary signals. Group labels are post-hoc researcher assignments.

**DEFENSE**: Functional not semantic claim (explicitly stated in main.md). Verify cross-seed consistency: same OOD type activates same group index across seeds. K sensitivity sweep (K=3,6,12).

**VERIFICATION**: 5-seed Spearman correlation of per-OOD attention vectors > 0.7. K=3 vs K=6 within 5% performance gap.

## Attack 4 — Falsification Gate ≡ Anomaly Detection (MAJOR)

**ATTACK**: β_t = sigmoid(MLP([F_t, h_t])) is calibrated anomaly detector. No operational distinction from falsification. Fires equally on sensor noise, adversarial perturbation, true dynamics shift.

**DEFENSE**: h_t (GRU belief memory) provides temporal context. True regime shifts produce temporally consistent high β (persistent dynamics), sensor anomalies produce isolated spikes. β_t autocorrelation test.

**VERIFICATION**: β_t recall/FPR under true OOD vs. matched-magnitude observation noise. Recall > 0.8, FPR < 0.2. AR(1) > 0.6 under regime shift, < 0.1 under ID noise.

## Attack 5 — Four-Axis Metrics Are Not Jointly Falsifiable (MAJOR)

**ATTACK**: Return, recovery time, wrong-hypothesis duration, return-per-compute are not independent. Near-tautological given the correction mechanism. Compute denominator undefined.

**DEFENSE**: Oracle-grounded wrong-hypothesis duration (measured from true regime change timestamp). Compute-matched experiment: give baseline same additional planning rollouts FGLC uses.

**VERIFICATION**: Compute-matched random reallocation baseline (required by CLAUDE.md §Baselines). If return-per-compute advantage disappears under compute matching, gain is from extra compute.

## Summary

```yaml
rejection_risk: MED
verdict: ATTACK_MANAGEABLE
unresolvable_weakness: "Causal" naming will attract sustained skepticism even if ablations pass. 
  Must either rename to "intervention-policy attention" or run τ_g randomized intervention experiment.
highest_priority_experiment: Compute-matched baseline (Attack 5) — already required by project contract.
```
