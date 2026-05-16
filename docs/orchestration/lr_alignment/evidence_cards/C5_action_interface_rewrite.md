# Evidence Card C5: Action-Interface Rewrite

## claim_id
C5

## current_status_before_run6
CONDITIONAL — ABL-017 (no_intent_action_mapping) registered, rewrite ablation ABL-035 registered. No direct rewrite mechanism in text env.

## run6_metric_evidence
Source: `outputs/runs/p3_lr_eval/metrics.json` → C5

| Metric | Value | Source |
|---|---|---|
| MET-REWRITE-001 rewrite_success_rate_proxy | 0.50 | 1 - failed_action_repetition_rate FRCG-FULL |
| action_switch_delay | 0.0 | p3_ablations FRCG-FULL avg |
| no_intent_action_mapping_delta_failed_rep | -0.41 | FRCG-FULL minus ABL-017 |

Note: delta is negative (ABL-017 has lower failed_rep than FRCG-FULL in pilot) — this is a counter-direction finding. Investigation needed.

## baseline_evidence
| Comparison | FRCG-FULL failed_rep | Comparison | Delta |
|---|---|---|---|
| vs ABL-017 (no_intent_mapping) | 0.500 | 0.089 | +0.411 (FRCG-FULL worse!) |
| vs BASE-026 WAC | N/A | N/A | not in ablation_results |

## ablation_evidence
ABL-017 (no_intent_action_mapping): failed_action_repetition_rate=0.089 vs FRCG-FULL=0.500. In smoke run, removing intent-action mapping REDUCES failure repetition — opposite of expected direction. This is a negative / unexpected result.

ABL-035 (no_rewrite): expected_collapse: failed_repetition_rate increase. Not yet differentiated in pilot.

## counter_evidence
**CRITICAL**: ABL-017 shows OPPOSITE direction from expected — removing intent-action mapping reduces failure repetition in pilot. This is a potential claim-refuting result.
- action_switch_delay=0.0 for both FRCG-FULL and ablations (no differentiation in proxy).
- No BASE-026 WAC comparison.
- rewrite_success_rate=0.50 is a proxy (inverse of failed_rep), not a direct rewrite measurement.

## blocker
- ABL-017 unexpected direction (reduces failure rate instead of increasing it) — must investigate before claiming C5
- No WAC BASE-026 comparison
- No direct rewrite mechanism implemented in text env

## decision
CONDITIONAL_ALIVE

## rationale
Rewrite infrastructure exists (ActionRecord.rewritten field, ABL-035 config). But ABL-017 shows unexpected direction in pilot. This is an honest counter-evidence finding that must be reported. The claim cannot be ALIVE_WITH_EVIDENCE until the unexpected ABL-017 direction is explained.

Pilot scope only — unexpected result may be due to proxy metric limitations (smoke run with synthetic data, not real grammar failures).

## next_required_work
- Investigate ABL-017 unexpected direction (is failed_rep proxy reliable?)
- Implement direct rewrite measurement (not proxy)
- Compare vs BASE-026 WAC
- Run ABL-035 (no_rewrite) with real grammar failure episodes

## allowed_claim_wording
"FRCG-WM includes an action-interface rewrite mechanism. Pilot evaluation shows mixed results for ABL-017 (intent-action mapping removal) — further investigation is ongoing."

## forbidden_claim_wording
- "Removing intent-action mapping increases failure repetition (ABL-017)" — pilot shows opposite
- "Rewrite mechanism reduces failure repetition vs WAC baseline" — no WAC comparison
