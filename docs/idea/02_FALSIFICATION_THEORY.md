# 02_FALSIFICATION_THEORY

## Source
- main.md §5 (mismatch), §6 (falsification gate)
- deep-research-report.md §Calibration·conformal·risk control, §CUSUM·SPRT·BOCPD

## Claim

Predictive mismatch can be **standardized** relative to the model's own uncertainty to produce
a calibration-valid falsification score. When this score exceeds the ID distribution's empirical
quantile threshold, the current dynamics hypothesis is falsified. The gate β_t is a calibrated
sigmoid MLP — mathematically distinguishable from a hard threshold because its threshold is
set to the empirical α-quantile of F_t scores on held-out ID trajectories, giving finite-sample
coverage at level α.

## Mathematical Formalization

```
Per-group standardized mismatch:
  ρ_t^k = (z_{t+1}^k - μ_t^k) / σ_t^k  ∈ R^d

Group falsification score:
  F_t^k = ||ρ_t^k||₂²

Under H0 (correct model, calibrated σ): F_t^k ~ χ²_d  [since each ρ_t^k_i ~ N(0,1)]

Total score: F_t = Σ_k F_t^k ~ χ²_{K*d} under H0

Falsification gate (calibrated):
  β_t = sigmoid(MLP([F_1^k,...,F_K^k, F_t, h_t]))
  
  Calibration: threshold set to empirical (1-α)-quantile of {F_t} on held-out ID data
  → finite-sample false alarm rate ≤ α

Calibration loss (prevents σ collapse escape):
  L_cal = E[log σ_t]²  or clamp: σ_min ≤ σ_t ≤ σ_max
  
  Combined NLL:
  L_nll = Σ_t Σ_k [0.5*(z_{t+1}^k - μ_t^k)²/(σ_t^k)² + log σ_t^k]
```

## CRITICAL LOAD-BEARING ASSUMPTION: σ Calibration

The χ² detection guarantee **collapses** if σ_t is poorly calibrated:
- Inflated σ → every mismatch appears "within uncertainty" → detection AUROC → 0.5
- NLL loss alone does NOT guarantee well-calibrated σ in deep networks

**Required evidence**: reliability diagram / ECE for predictive variance on ID and OOD.
This is a required ablation (see 20_ABLATIONS.md: no-conformal-calibration).

## Comparison: Conformal vs CUSUM/SPRT/BOCPD

| Method | Coverage guarantee | Action-relevance | Sequential power |
|---|---|---|---|
| FGLC conformal gate | Finite-sample, marginal | Via value-aware loss | Via β_t MLP |
| CUSUM (Page 1954) | CUSUM optimality | None | Strong |
| SPRT (Wald 1945) | Probability ratio | None | Strong |
| BOCPD (Adams & MacKay 2007) | Bayesian | None | Strong |

FGLC advantage over CUSUM/SPRT/BOCPD: directly integrates action/value relevance.
Baselines CUSUM/SPRT/BOCPD should outperform FGLC on detection-only metrics
(detection delay, false alarm rate) if FGLC's gate is miscalibrated.
This is an expected and honest result — FGLC trades detection optimality for action-relevance.

## Connection Map
- Upstream: M-6 (dynamics prior), R-7 (CUSUM/SPRT/BOCPD baseline)
- Downstream: M-9 (attention uses β_t), M-10 (correction gated by β_t), R-6 (conformal)
- Critical: must have σ-calibration evidence before claiming detection performance

## Checkpoints

- C1 Math validity: **CONDITIONAL** — χ² claim valid under stated assumptions. Key risk:
  σ calibration is load-bearing. Without variance calibration, the χ² distribution argument
  fails and the gate becomes indistinguishable from a learnable threshold.
  Distinguishability fix: threshold = empirical (1-α)-quantile of ID scores (explicit coverage).
  agent_report: see mathematical-validity-critic result 2026-05-22
- C2 Novelty: PENDING
- C3 Reviewer attack: PENDING
- C4 Feasibility: PASS — Calibration set can be collected from 1k ID trajectories.
  ECE computation is O(n) post-training. Feasible in R4 phase.
- C5 Claim-metric: CONDITIONAL — Must show detection AUROC + ECE + false-alarm rate.
  If σ miscalibrated, claim collapses. Required metric: variance calibration reliability plot.
- C6 Impl risk: PENDING
- C7 Experiment design: Required ablation: no-conformal-calibration (hard threshold).
  Without this, "calibrated gate" claim is not validated.
- C8 Failure interp: Main failure: σ collapse. If σ inflates, gate detects nothing.
  Mitigation: L_cal + σ clamp + ablation showing ECE degrades without it.
- C9 Related work (≥2 sources): PENDING — need Adams & MacKay BOCPD, Angelopoulos CRC.
- C10 Context routing: Source = main.md §5-6. Downstream: 06_CAUSAL_ATTENTION.md,
  13_ALGORITHM_CIRCA.md, 21_METRICS.md §detection axis.

## Open Questions
- Is empirical quantile calibration sufficient or is full conformal coverage (CRC) needed?
- How does detection delay compare to CUSUM under different shift magnitudes?
- Can we prove that a well-calibrated gate has strictly lower planning cost than always-correct?
