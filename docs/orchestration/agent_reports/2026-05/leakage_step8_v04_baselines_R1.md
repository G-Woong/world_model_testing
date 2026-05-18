# frcgw-data-leakage-auditor Report: STEP 8 v0_4 + BASE-026/027 Faithful

**report_id**: leakage_step8_v04_baselines_R1
**date**: 2026-05-18
**trigger**: T2 (데이터/스키마 변경 전)
**verdict**: PASS (current code) / WARN (prospective Codex tasks)

---

## Summary

Current v0_3 codebase: PASS. No hidden labels in agent_observation path. All concerns are prospective — dependent on how Codex implements v0_4 generator and faithful baselines.

## v0_4 Generator Leakage Risk

### WARN 1: OOD grammar family selection transparency
OOD coverage enforcement (force blocker_removed ≥ 30, delayed_effect ≥ 30) must operate at task-family selection level before any agent observation is built. The `effect_summary` in `history_public` IS permitted to contain "blocker_removed", "delayed_effect" — these are in `_PUBLIC_EFFECT_TYPES` and are agent-observable behavioral signals. This is correct.

**Safeguard**: Generator must not encode grammar tokens in `visible_text`, `initial_state_template`, or `event.detail` strings.

### WARN 2: `oracle_best_action` and `audit_metadata` missing from v0_3 forbidden_fields config
`oracle_best_action` and `audit_metadata` are in `FORBIDDEN_AGENT_FIELDS` (visibility.py) but absent from `dataset_v0_3.yaml` forbidden_fields list. v0_4 config must add these.

### Safeguards for Codex Task 2
1. Call `assert_agent_observation_safe(obs)` per step as in collector.py
2. OOD selection at task-family level, not effect-label injection
3. `configs/dataset_v0_4.yaml` forbidden_fields must include `oracle_best_action` and `audit_metadata`
4. Manifest must record `leakage_audit_passed: true`

## WACFaithfulCandidate Leakage Surface

### BLOCK condition if implemented naively

**FORBIDDEN inputs to act():**
| Field | Risk | Guidance |
|---|---|---|
| `true_control_grammar` | HIGH-BLOCK | Grammar posterior must come from public history, not oracle label |
| `true_regime` | HIGH-BLOCK | Must not condition on true regime |
| `true_wrong_hypothesis` | HIGH-BLOCK | Use effect_summary=="no_state_change" as failure signal instead |
| `oracle_grammar_action` | HIGH-BLOCK | Recovery must come from posterior, not oracle |
| `correct_hypothesis_id` | MEDIUM | eval_labels argument must be ignored entirely |
| `counterfactual_progress_delta` | MEDIUM | Must not use for consequence correction selection |

### Safeguards for Codex Task 6 (WACFaithfulCandidate)
1. `eval_labels` argument must be entirely ignored: `assert eval_labels is None or not (FORBIDDEN_AGENT_KEYS & eval_labels.keys())`
2. Grammar posterior derived from `obs.history_public` sequence only
3. Must NOT import `TrainingLabels` or `EvaluationLabels` from `step_schema`
4. `FORBIDDEN_AGENT_KEYS` check at method entry

## CUWMFaithfulCandidate Leakage Surface

### WARN — implicit oracle risk

**FORBIDDEN inputs:**
| Field | Risk | Guidance |
|---|---|---|
| `true_control_grammar` | HIGH-BLOCK | Must not seed rollout GrammarEngine |
| `oracle_best_action` | HIGH-BLOCK | Progress scoring must come from model, not oracle |
| `counterfactual_progress_delta` | HIGH-BLOCK | Must not use stored counterfactual delta as rollout score |
| `true_regime` | MEDIUM | Must not condition rollout |

### Safeguards for Codex Task 6 (CUWMFaithfulCandidate)
1. Must NOT call `GrammarEngine(grammar=eval_labels["true_control_grammar"])`
2. K candidates from `obs.candidate_actions_public` only
3. Predicted progress = proxy from public effect history (count of state_change + task_complete)
4. `eval_labels` entirely ignored

## Schema Changes Deferred to STEP 9
- `true_regime` to EvaluationLabels EVALUATION_ONLY bucket (for true regime_shift_f1)
- `ood_effect_type` subtype field (if OOD distinction beyond coarse ood_type needed)
- Do NOT modify step_schema.py or visibility.py in STEP 8
