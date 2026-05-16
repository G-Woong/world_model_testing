# Evidence Card C6: Decision-Relevant Compute Gate

## claim_id
C6

## current_status_before_run6
CONDITIONAL — ComputeBudgetLog implemented, progress_per_compute metric exists. BASE-015 not in ablation_results.

## run6_metric_evidence
Source: `outputs/runs/p3_lr_eval/metrics.json` → C6

| Metric | Value | Source |
|---|---|---|
| MET-COMP-003 progress_per_compute | 0.229 | p3_ablations FRCG-FULL avg |
| false_planning_call_rate | 0.0 | p3_ablations FRCG-FULL avg |
| planning_calls | 1 | p3_lr_smoke |
| compute_matched_delta_ppc | null | BASE-015 not in ablation_results |

## baseline_evidence
| Comparison | FRCG-FULL ppc | Comparison | Delta |
|---|---|---|---|
| vs BASE-015 compute_matched_random | 0.229 | N/A | null (not in ablation_results) |
| vs always_plan_no_gate (ABL-034) | 0.229 | 0.114 | +0.115 (FRCG-FULL better) |

ABL-034 (always_plan_no_gate): progress_per_compute=0.114 vs FRCG-FULL=0.229 — gate doubles efficiency in pilot.

## ablation_evidence
- ABL-034 (always_plan_no_gate): ppc=0.114 vs FRCG-FULL=0.229 → delta=+0.115. Gate improves compute efficiency by ~2x in pilot.
- ABL-033 (no_compute_gate): false_planning_call_rate=0.0 for both (proxy insufficient).
- BASE-015 (compute_matched_random): not in ablation_results → delta_ppc=null.

## counter_evidence
- false_planning_call_rate=0.0 for FRCG-FULL in pilot — all planning calls resulted in action/progress change. But this may be a proxy artifact (planning_events count = 0 in most steps).
- BASE-015 compute_matched_random comparison absent — CATTS-equivalent comparison not possible.
- planning_calls=1 (from smoke, 5 records) — insufficient for statistical claims.

## blocker
- BASE-015 not in current ablation_results → compute_matched_delta is null
- Small sample (1 planning call across 5 smoke records) → no statistical power

## decision
CONDITIONAL_ALIVE

## rationale
ABL-034 shows gate improves ppc by ~2x in pilot (0.229 vs 0.114). false_planning_call_rate=0.0 is consistent with gate working. However, BASE-015 comparison is absent and sample size is insufficient. Cannot reach ALIVE_WITH_EVIDENCE.

## next_required_work
- Add BASE-015 (compute_matched_random) to ablation evaluation
- Increase evaluation sample size
- Implement real planning_events logging (not proxy)
- Compare vs BASE-012-CATTS for compute efficiency

## allowed_claim_wording
"The decision-relevance gate (G_t) shows ~2x improvement in progress-per-compute over always-plan baseline (ABL-034) in pilot evaluation. Full comparison against compute-matched baselines is planned."

## forbidden_claim_wording
- "FRCG-WM achieves better compute efficiency than CATTS" — comparison absent
- "false_planning_call_rate=0 proves gate efficiency" — proxy artifact likely
