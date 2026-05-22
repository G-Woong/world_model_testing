# Cluster 1+3 Mathematical Validity Report

**Date**: 2026-05-22
**Agent**: mathematical-validity-critic (T1 deep mode)
**Clusters**: Cluster 1 (Problem Formulation: M-0, R-0, R-18) + Cluster 3 (Falsification Theory: M-7, M-8, R-6, R-7)

## Cluster 1 - Problem Formulation

**C1-Math verdict: CONDITIONAL**

Key issues:
1. Diagonal Gaussian `pθ(z_{t+1}|z_t,a_t,h_t) = N(μ_t, diag(σ_t²))` is internally consistent with per-group standardization `ρ_t^k = (z_{t+1}^k - μ_t^k) / σ_t^k`. No circularity.

2. **Attention-causality conflation risk**: main.md §4.3 labels the group interaction block as "dynamics interaction layer, NOT causal attention." The causal/correction attention is a separate module. The Cluster 1 claim description fuses these two, creating definitional ambiguity.

3. The claim "only that subspace receives sparse residual correction" is architecturally correct but identifiability of the *causally responsible* subspace is NOT guaranteed by diagonal-Gaussian prior alone. Requires value-aware utility alignment or randomized intervention training losses.

## Cluster 3 - Falsification Theory

**C1-Math verdict: CONDITIONAL**

Key issues:
1. **χ² claim is valid under stated assumptions.** Given `pθ = N(μ_t^k, diag((σ_t^k)^2))`, each element of `ρ_t^k` is i.i.d. `N(0,1)` under H0. Therefore `F_t^k ~ χ²_d` under H0. Mathematically valid, contingent on calibration.

2. **CRITICAL: σ collapse escape hatch.** The χ² calibration argument collapses entirely if σ is poorly calibrated (inflated). The paper must show that `L_sigma` prevents σ inflation. Without this, the χ² claim is an assumption, not a property.

3. **Gate distinguishability issue.** `β_t = sigmoid(MLP(...))` is mathematically distinguishable from a hard threshold ONLY if: (a) empirical quantile calibration is applied post-training on held-out ID data, OR (b) χ² CDF is used with calibrated σ. The paper must demonstrate conformal coverage at level α.

4. Equations 1-6 are internally consistent. `L_nll` is the correct heteroscedastic Gaussian NLL.

## Overall Assessment

**Main mathematical risks (HIGH to LOW)**:
- R1 (HIGH): σ calibration is load-bearing for entire χ²/conformal argument
- R2 (MEDIUM): Gate distinguishability from learnable threshold requires explicit coverage demonstration
- R3 (LOW): Attention-causality conflation in Cluster 1 labeling

**Required fixes**:
1. Add σ calibration check (reliability diagram / ECE for predictive variance) as required ablation
2. Replace "calibrated gate, not hard threshold" with: "threshold = empirical α-quantile of F_t on held-out ID trajectories, giving finite-sample coverage at level α"
3. In Cluster 1, split "causalized attention selects subspace" into: (a) mismatch score locates group, (b) sparse correction gate applies residual
