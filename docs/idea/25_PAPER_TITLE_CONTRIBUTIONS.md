# 25_PAPER_TITLE_CONTRIBUTIONS

## Source
- main.md §24 (title candidates), §마지막 핵심 정리

## Title Candidates

**Primary (recommended)**:
> Falsification-Guided Latent Correction for World Model Planning under Physical Distribution Shift

**Alternative A** (shorter):
> Action-Relevant Falsification in Latent World Models

**Alternative B** (emphasizing algorithms):
> CIRCA: Causal Intervention Randomized Conformal Attention for World Model Correction

**Decision**: Use primary title for submission. Alternative B if contribution is reduced to CIRCA only.

## 5 Contribution Bullets

1. **Falsification-guided correction framework**: A principled framework that detects when a
   latent world model's predictive distribution is statistically inconsistent with observation
   transitions (falsification event) and applies targeted sparse residual correction.

2. **Calibrated falsification gate**: A statistically calibrated gate β_t with finite-sample
   false alarm rate control, distinguishable from hard-threshold anomaly detection by
   empirical quantile calibration on held-out ID trajectories.

3. **Intervention-policy attention**: A group-level sparse attention mechanism α_t validated
   as an intervention policy (necessity/sufficiency losses + τ_g randomized intervention)
   rather than as a causal attributor, addressing the attention-as-explanation critique.

4. **Four-algorithm benchmark**: A systematic comparison of CIRCA, ASAP, I3G, and IVI
   covering different points in the intervention-validity / calibration / compute-efficiency
   space, providing guidance for practitioners on algorithm selection.

5. **Empirical evaluation**: Controlled physical dynamics shift benchmark (ManiSkill OOD axes:
   mass/friction/latency/noise/action-gain) with 4-axis metrics (prediction/detection/
   attribution/control) demonstrating FGLC outperforms TD-MPC2/DreamerV3/HiP-RSSM on
   OOD return and recovery time while maintaining compute efficiency.

## Abstract Draft (v0.1)

```
Latent world models degrade silently when physical dynamics shift — 
a phenomenon we call wrong-dynamics-hypothesis persistence. 
We introduce FGLC (Falsification-Guided Latent Correction), a framework 
that (1) detects dynamics hypothesis violations via calibrated standardized 
predictive mismatch, (2) identifies which grouped latent subspaces drive 
planning failures through an intervention-validated sparse attention 
mechanism, and (3) applies bounded residual correction to those subspaces.
We validate corrections via necessity, sufficiency, and counterfactual rollout 
losses, ensuring the sparse attention mask is an effective intervention policy 
rather than an attention visualization. We instantiate FGLC as four algorithms 
(CIRCA, ASAP, I3G, IVI) with different validity/calibration/compute tradeoffs 
and evaluate on ManiSkill manipulation tasks under controlled mass, friction, 
latency, noise, and action-gain shifts. FGLC achieves [X]% higher return and 
[Y]× faster recovery than TD-MPC2 under OOD conditions while maintaining 
comparable performance on ID tasks.
[Placeholder: X and Y require actual experimental results]
```

## Positioning vs. Direct Threats

| Threat | Our positioning |
|---|---|
| TD-MPC2 | We extend TD-MPC2 with falsification detection and targeted correction |
| DreamerV3 | Same OOD problem but decoder-free, no correction mechanism |
| HiP-RSSM | We detect and correct without explicit parameter inference |
| PLSM | PLSM improves action effects at training; FGLC corrects failures at inference |
| ReDRAW/AdaWM | FGLC adds causal attention + necessity/sufficiency validation |

## Connection Map
- Upstream: 22_NOVELTY_AND_THREATS.md, 17_ALGORITHM_COMPARISON.md
- Downstream: docs/ROADMAP/15_PHASE_R14_PAPER_FRAMING_AND_DRAFTING.md
