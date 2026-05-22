# 21_METRICS — 4-Axis Metric Suite

## Source
- main.md §22 (experimental metrics)
- deep-research-report.md §R-14 (4-axis metrics)

## Claim

FGLC evaluation requires 4 independent metric axes. Reporting only NLL or only return
is insufficient — the paper claims contributions in all 4 axes and each must be measured.

## Axis 1: Prediction Accuracy

| Metric | Description | Required baseline |
|---|---|---|
| one-step NLL | -log pθ(z_{t+1}|z_t,a_t,h_t) | All baselines |
| MS-NLL | Multi-step rollout NLL (H=5,10,20) | All baselines |
| Calibration ECE | Expected Calibration Error for σ predictions | Required for β_t χ² claim |
| Reliability diagram | Bin predictions by confidence; plot vs. accuracy | Visual σ calibration |

## Axis 2: Falsification Detection

| Metric | Description | Oracle labels needed |
|---|---|---|
| OOD detection AUROC | Using F_t scores; regime_id as oracle label | Yes (eval only) |
| Detection delay | Steps from true regime change to β_t > 0.5 | Yes |
| False alarm rate | β_t > 0.5 on ID data | No |
| Calibration coverage | β_t gate fires at rate ≤ claimed α on ID | No |
| β_t autocorrelation | AR(1) under true shift vs. ID noise | Partial (eval regime label) |

## Axis 3: Attribution / Causal Validity

| Metric | Description | Oracle needed |
|---|---|---|
| Necessity-Δ | L_without - L_with; should be > 0 | No |
| Sufficiency-Δ | |L_selected - L_full|; should be < ε | No |
| Random-Δ | L_random - L_selected; should be > 0 | No |
| Counterfactual-Δ | NLL change under counterfactual physical params | Yes (sim oracle) |
| Mask precision/recall | α activates correct group (vs. changed factor) | Yes (sim oracle) |
| τ_g significance | p-value for group utility ATE per OOD type (CIRCA) | No |

## Axis 4: Control Performance

| Metric | Description | Oracle needed |
|---|---|---|
| Return | Average episode return (undiscounted and discounted) | No |
| Success rate | Task completion rate per OOD condition | No |
| Recovery time | Steps from regime change to baseline return recovery | Yes (regime timestamp) |
| Planning calls per episode | Total β_t > 0.5 firings | No |
| Return per compute | Return / total correction+planning rollouts | No |
| Worst-case return | 5th percentile return under OOD-mixed | No |
| Wrong-hypothesis duration | Steps with wrong dynamics (oracle comparison) | Yes |

## Compute-Matched Experiment (Critical)

Per Attack 5 defense: give all baselines same compute budget as FGLC (same planning rollouts/ep).
If FGLC's return-per-compute advantage disappears → gain from extra compute, not correction.

## Metric Reporting Requirements

1. All metrics must be reported as mean ± std over ≥3 seeds
2. Statistical significance: p < 0.05 (paired t-test vs. TD-MPC2) required for main claims
3. Per-OOD-condition breakdown required (not just aggregate)
4. Oracle metrics require explicit labeling as "oracle evaluation"

## Connection Map
- Upstream: 19_BASELINES.md, 20_ABLATIONS.md
- Downstream: 26_CROSSCHECK_SUMMARY.md
- Implementation: src/fglc/evaluation/metrics.py (R4+ phases)
