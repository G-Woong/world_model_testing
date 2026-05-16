# Evidence Card C1: Wrong-Control-Grammar Persistence

## claim_id
C1

## current_status_before_run6
CONDITIONAL — h_exec trace fields added (Run 4B), but MET-PERSIST-001 unimplemented and Group B tests skipped.

## run6_metric_evidence
Source: `outputs/runs/p3_lr_eval/metrics.json` → C1

| Metric | Value | Source |
|---|---|---|
| planning_calls | 1 | p3_lr_smoke/metrics.json |
| h_exec_null_rate | 0.0 | p3_lr_smoke/metrics.json |
| MET-PERSIST-001 status | BLOCKED_no_eval_labels | preflight |
| repeated_invalid_mapping_rate | 0.5 | p3_ablations/ablation_results.json FRCG-FULL |
| recovery_delay | 2.545 | p3_ablations/ablation_results.json FRCG-FULL |

## baseline_evidence
| Baseline | Metric | FRCG-FULL | Baseline | Delta |
|---|---|---|---|---|
| ABL-022 no_falsification_score_gate | recovery_delay | 2.545 | 2.545 | 0.0 (proxy only) |
| BASE-006 verifier_recovery | N/A | N/A | N/A | not in ablation_results |
| VLAA-loop BASE-003+008 | N/A | N/A | N/A | not in ablation_results |

## ablation_evidence
- ABL-022 (no_falsification_score_gate): same wrong_grammar_persistence as FRCG-FULL (1.909 each) — expected differentiation requires full eval with eval_labels.
- MET-PERSIST-001 function implemented (`compute_wrong_grammar_persistence_v1`) — returns BLOCKED when evidence_timestamp/correct_hypothesis_id absent.

## counter_evidence
- MET-PERSIST-001 BLOCKED: cannot compute actual persistence without eval_labels.evidence_timestamp + eval_labels.correct_hypothesis_id in text env episodes.
- ABL-022 vs FRCG-FULL persistence not differentiated at this scope (same proxy trajectory).
- Reviewer 2 Attack 2 (REF-PROBLEM-012): h_exec trace = policy-space constant string, not model-predicted. Insufficient for strong C1 claim.

## blocker
- eval_labels.evidence_timestamp not populated in text env collector → MET-PERSIST-001 always BLOCKED
- No BASE-006/VLAA comparison baseline data
- h_exec_id not oracle-aligned (None in collector) → persistence vs "correct hypothesis switch" unmeasurable

## decision
CONDITIONAL_ALIVE

## rationale
h_exec trace is populated (null_rate=0.0), MET-PERSIST-001 function exists and correctly returns BLOCKED when labels missing. Planning_calls=1>0 confirms the mechanism is engaged. Cannot reach ALIVE_WITH_EVIDENCE without eval_labels.evidence_timestamp and oracle-aligned correct_hypothesis_id in trajectory data.

## next_required_work
- Populate EvaluationLabels.evidence_timestamp in text env collector (or P4/P5 GUI env)
- Populate EvaluationLabels.correct_hypothesis_id
- Run MET-PERSIST-001 with eval-labeled episodes
- Compare FRCG-FULL vs ABL-022 + BASE-006 + VLAA-loop on persistence metric

## allowed_claim_wording
"We introduce a wrong-control-grammar persistence metric (MET-PERSIST-001) and provide infrastructure to measure it when evaluation labels are available. Pilot results show h_exec traces are non-null and planning is engaged."

## forbidden_claim_wording
- "We show reduced wrong-grammar persistence compared to baselines" — not measurable at this scope
- "MET-PERSIST-001 confirms C1 holds" — function returns BLOCKED, no evidence yet
