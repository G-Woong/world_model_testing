# Evidence Card C3: Falsification via Likelihood Ratio Score

## claim_id
C3

## current_status_before_run6
CONDITIONAL — LR scorer implemented (Run 4), ABL-022/023 ablations registered (Run 5). No eval label data for full metrics.

## run6_metric_evidence
Source: `outputs/runs/p3_lr_eval/metrics.json` → C3

| Metric | Value | Source |
|---|---|---|
| MET-FALS-001 falsification_precision | 0.338 | ablation_results.json FRCG-FULL avg |
| MET-FALS-002 falsification_recall | 0.500 | ablation_results.json FRCG-FULL avg |
| falsification_f1 | 0.403 | ablation_results.json FRCG-FULL avg |
| MET-CAL-001 calibration_ece | 0.244 | ablation_results.json FRCG-FULL avg |
| F_t_variance | 1.26 | p3_lr_smoke/metrics.json |
| F_t_degenerate_rate | 0.20 | p3_lr_smoke/metrics.json |
| FRCG-FULL fals_f1 | 0.403 | ablation_results.json |
| ABL-022 fals_f1 | 0.000 | ablation_results.json |
| ABL-023 fals_f1 | 0.000 | ablation_results.json |
| LR_vs_gate_removal_delta_f1 | +0.403 | computed |
| LR_vs_uncertainty_delta_f1 | +0.403 | computed |

## baseline_evidence
| Comparison | FRCG-FULL f1 | Comparison f1 | Delta |
|---|---|---|---|
| vs ABL-022 (no_falsification_score_gate) | 0.403 | 0.000 | +0.403 |
| vs ABL-023 (uncertainty_instead_of_falsification) | 0.403 | 0.000 | +0.403 |
| vs BASE-006 VerifierRecovery | 0.403 | N/A (not in results) | N/A |
| vs BASE-012-CATTS | 0.403 | N/A (not in results) | N/A |

## ablation_evidence
- ABL-022 (F_t gate removal): f1=0.0 vs FRCG-FULL f1=0.403 → removing gate collapses detection
- ABL-023 (uncertainty instead of LR): f1=0.0 → uncertainty threshold alone insufficient
- Main path: LR log-likelihood ratio only. BCE/sigmoid variants are ABL variants. Confirmed by lr_scorer.py docstring.

## counter_evidence
- Proxy metrics: `predicted_wrong` field not in real step records; falsification_precision_recall uses a proxy. Reviewer 2 can attack "precision/recall not from real model."
- calibration_ece=0.244 is non-trivial (baseline is 0.5 for uniform calibration) but meaningful calibration requires real model scores, not proxy.
- F_t_degenerate_rate=0.20 means 20% of smoke records are degenerate — needs investigation.
- BASE-006, BASE-012-CATTS comparison absent.

## blocker
- No BASE-006 / BASE-012-CATTS comparison data
- `predicted_wrong` proxy in falsification metrics is not from real model inference
- F_t from smoke run (5 synthetic records), not from real evaluation

## decision
CONDITIONAL_ALIVE

## rationale
Strong structural evidence: LR scorer produces non-degenerate F_t (variance=1.26), ABL-022 and ABL-023 both collapse to f1=0.0 vs FRCG-FULL f1=0.403 (delta=0.403 each). Main path is BCE-free (confirmed by code review). Precision/recall/calibration metrics exist. Cannot reach ALIVE_WITH_EVIDENCE without real model inference + BASE-006/CATTS comparison.

## next_required_work
- Run BASE-006 VerifierRecovery and BASE-012-CATTS agents in ablation evaluation
- Implement real `predicted_wrong` from LR scorer output (not proxy)
- Increase smoke records from 5 to statistically meaningful N
- Investigate 20% degenerate rate

## allowed_claim_wording
"We show that the LR falsification score (F_t) achieves non-zero detection performance (f1=0.40 in pilot) while removing the gate (ABL-022) or substituting uncertainty (ABL-023) collapses detection to zero. Full evaluation against BASE-006 and BASE-012-CATTS is planned."

## forbidden_claim_wording
- "LR scorer outperforms verifier-only and CATTS baselines" — comparison data absent
- "F_t achieves 50% recall in real evaluation" — smoke results only
- "Calibration is well-behaved" — 0.244 ECE from proxy, not real model
