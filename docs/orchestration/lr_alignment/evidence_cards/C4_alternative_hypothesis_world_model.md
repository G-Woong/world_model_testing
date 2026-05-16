# Evidence Card C4: Alternative Hypothesis World Model / Rollout

## claim_id
C4

## current_status_before_run6
BLOCKED — rollout integration not implemented at text env scope. MET-WM-001 and MET-ALT-001 have no data.

## run6_metric_evidence
Source: `outputs/runs/p3_lr_eval/metrics.json` → C4

| Metric | Value |
|---|---|
| MET-WM-001 rollout_fidelity | BLOCKED_no_rollout_log |
| MET-ALT-001 alternative_adoption_rate | BLOCKED_no_rollout_log |
| rollout_steps | 0 |

ABL-036 (no_counterfactual_target) registered in ABLATION_REGISTRY with expected_collapse: rollout_fidelity decrease, alternative_adoption_rate decrease. No differentiation in pilot (same proxy metrics).

## baseline_evidence
No baseline comparison available. BASE-027 (CUWM candidate simulation) and BASE-028 (WebWorld search) not in current ablation_results.

## ablation_evidence
ABL-036 (no_counterfactual_target): identical proxy metrics to FRCG-FULL in smoke run. No differentiation possible without rollout implementation.

## counter_evidence
- Rollout = 0 steps in all current experiments → C4 claim entirely unsupported.
- No world model fidelity data of any kind.
- CUWM and WebWorld threats not addressed by any current result.

## blocker
- Rollout integration not implemented (Phase 5+ scope)
- MET-WM-001 and MET-ALT-001 not measurable without rollout
- ABL-036 shows no differentiation without rollout

## decision
BLOCKED

## rationale
Zero rollout steps means world model / alternative hypothesis claim has no empirical support. MET-WM-001 and MET-ALT-001 both BLOCKED. This is a Phase 5+ deliverable.

## next_required_work
- Implement rollout step logging in eval runner
- Implement MET-WM-001 (rollout fidelity metric)
- Implement MET-ALT-001 (alternative adoption rate)
- Compare vs BASE-027 (CUWM) and BASE-028 (WebWorld)
- Run ABL-036 with rollout enabled

## allowed_claim_wording
"FRCG-WM includes an alternative hypothesis world model component. Quantitative evaluation (MET-WM-001, MET-ALT-001) is planned for Phase 5 with rollout integration."

## forbidden_claim_wording
- "The world model improves alternative hypothesis selection" — no rollout data
- "ABL-036 confirms world model contribution" — no differentiation observed
