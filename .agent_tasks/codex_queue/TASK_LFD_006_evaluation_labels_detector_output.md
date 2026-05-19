TASK_NAME: TASK_LFD_006_evaluation_labels_detector_output

BACKGROUND:
LFD evaluation requires comparing detector outputs to ground-truth evaluation
labels. The current EvaluationLabels (step_schema.py:74-84) does not have
fields for detector outputs or regime switch timing.

This task extends EvaluationLabels with eval-only fields and ensures the
output contract is safe (no public_obs exposure, no visibility.py violation).

SAFETY GATE (M5 from preflight checkpoint-0):
`detection_delay_gt` derives directly from `regime_switch_step` (oracle timing).
It MUST be added to `FORBIDDEN_AGENT_FIELDS` in `src/frcgw/schemas/visibility.py`
BEFORE this task executes. This requires explicit user approval per CLAUDE.md.

visibility.py IS FORBIDDEN in this task's FILES_ALLOWED.
If visibility.py update is needed, STOP and report to Claude (Main Claude will
request user approval separately). Do NOT modify visibility.py in this task.

GOAL:
1. Extend EvaluationLabels with detector output fields (EVALUATION_ONLY bucket).
2. Ensure all new fields are structurally isolated from PublicObservation.
3. Update StepRecord to pass through new fields.
4. Verify leakage tests pass.

FILES_ALLOWED:
- src/frcgw/schemas/step_schema.py
- tests/test_eval_labels_contract.py  (new file)

FILES_FORBIDDEN:
- .claude/
- CLAUDE.md
- .mcp.json
- .venv/
- data/
- outputs/
- secrets/
- .env*
- scripts/run_codex_task.ps1
- paper_context_ref/
- src/frcgw/schemas/visibility.py   ← EXPLICITLY FORBIDDEN — user approval required
- src/frcgw/models/
- src/frcgw/objectives/
- src/frcgw/planning/
- src/frcgw/data/
- src/frcgw/evaluation/

REQUIRED_IMPLEMENTATION:
1. EvaluationLabels extension (step_schema.py):

   @dataclass
   class EvaluationLabels:
     """Evaluation-only labels. EVALUATION_ONLY bucket.
     Never in PublicObservation, PublicHistoryItem, or any inference input.
     """
     # Existing fields (preserve all):
     true_wrong_hypothesis: bool | None = None
     h_exec_id: str | None = None
     correct_hypothesis_id: str | None = None
     evidence_timestamp: int | None = None
     hypothesis_update_timestamp: int | None = None
     recovery_timestamp: int | None = None
     ood_type: str | None = None
     true_regime: str | None = None
     
     # New detector output fields (EVALUATION_ONLY):
     regime_switch_t: int | None = None      # step index of switch (eval-only)
     detection_delay_gt: int | None = None   # alarm_step - regime_switch_t (eval-only)
     detector_wrong_prob_learned: float | None = None   # model output snapshot
     detector_cusum_stat: float | None = None           # CUSUM stat snapshot
     detector_run_length_posterior: list[float] | None = None  # full distribution

   NOTE: `regime_switch_t` and `detection_delay_gt` are eval-only ground truth.
   They should already be in FORBIDDEN_AGENT_FIELDS before this task runs.
   If they are not, do NOT add them here — STOP and report.

2. Tests (tests/test_eval_labels_contract.py):
   - `test_eval_labels_no_forbidden_fields_in_public_obs`
   - `test_regime_switch_t_not_in_public_observation`
   - `test_detection_delay_gt_not_in_public_observation`
   - `test_eval_labels_all_new_fields_optional`
   - `test_step_record_preserves_eval_labels_type`

REQUIRED_TESTS:
- tests/test_visibility_contract.py: must remain GREEN
- tests/test_leakage_auditor.py: must remain GREEN
- tests/test_forbidden_field_mirror_sync.py: must remain GREEN (3 passed)
- tests/test_eval_labels_contract.py: all new tests pass

ACCEPTANCE_CRITERIA:
- EvaluationLabels has all 5 new optional fields
- No new field appears in PublicObservation or PublicHistoryItem
- All three visibility/leakage tests remain GREEN
- No modification to visibility.py (FORBIDDEN in this task)
- If `regime_switch_t` is not in FORBIDDEN_AGENT_FIELDS: STOP, do not add it here

COMMIT_MESSAGE:
feat(schema): EvaluationLabels detector output fields (eval-only)

Adds regime_switch_t, detection_delay_gt, detector_wrong_prob_learned,
detector_cusum_stat, detector_run_length_posterior as EVALUATION_ONLY fields.
All fields optional; no inference path exposure. visibility.py unchanged.

STOP_CONDITION:
STOP if:
1. visibility.py is touched (FORBIDDEN — requires separate user approval)
2. `regime_switch_t` is not already in FORBIDDEN_AGENT_FIELDS when task runs
3. Any new field appears in PublicObservation, history_public, or any inference input
4. tests/test_visibility_contract.py fails
5. tests/test_forbidden_field_mirror_sync.py fails

Dependencies: TASK_LFD_004 (regime_switch_t defined in dataset), TASK_LFD_003 (detector outputs)
Pre-condition: visibility.py must have regime_switch_t + detection_delay_gt in FORBIDDEN_AGENT_FIELDS
               (user approval gate — not this task's responsibility)
Checkpoint mapping: PHASE 6 (Checkpoint-6)
Required agent review: frcgw-data-leakage-auditor (mandatory post-merge)
