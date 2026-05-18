TASK_NAME: TASK_1051_step5_c4_rollout_fidelity
SANDBOX_MODE: bypass

BACKGROUND:
C4 MET-WM-001 (alternative_rollout_fidelity) is required as evidence for the FRCG-WM claim that
counterfactual rollout prediction matches actual outcomes. This metric was BLOCKED in STEP 4
because the function did not exist in metrics.py.

Key source files:
- src/frcgw/evaluation/metrics.py (add new function)
- src/frcgw/evaluation/eval_runner.py (METRIC_FUNCTIONS dict, add new entry)
- scripts/10_run_lr_real_eval.py (_build_metrics_with_blocked_markers or equivalent; replace C4 BLOCKED marker with actual call)
- src/frcgw/text_env/counterfactual_rollout.py (CounterfactualRecord, has counterfactual_progress_delta field)

Current state in scripts/10_run_lr_real_eval.py: there is a BLOCKED marker for C4. Read the file
to find the exact location and replace it with the actual call.

GOAL:
Implement alternative_rollout_fidelity() in metrics.py, wire it into eval_runner.py and
scripts/10_run_lr_real_eval.py, and write 6 tests.

FILES_ALLOWED:
- src/frcgw/evaluation/metrics.py
- src/frcgw/evaluation/eval_runner.py
- scripts/10_run_lr_real_eval.py (BLOCKED marker replacement ONLY — do not rewrite the file)
- tests/test_step5_rollout_fidelity.py

FILES_FORBIDDEN:
- outputs/**
- data/**
- paper_context_ref/**
- src/frcgw/schemas/**
- .claude/**
- scripts/run_codex_task.ps1

REQUIRED_IMPLEMENTATION:
1. In src/frcgw/evaluation/metrics.py, add:

```python
def alternative_rollout_fidelity(episodes: list) -> dict:
    """MET-WM-001: counterfactual top-1 predicted_progress_delta vs actual progress_delta.

    paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md MET-WM-001 SSoT.

    Step-level fidelity = 1.0 - min(1.0, abs(predicted_top1_delta - actual_delta))
    Episode mean, then overall mean.
    Counterfactual-free steps are skipped.
    All-empty episodes give count_blocked increment.

    Returns: dict with keys:
      mean_fidelity: float | None
      count_episodes_with_counterfactuals: int
      count_blocked: int  (episodes with no counterfactuals)
      status: "OK" | "BLOCKED_no_counterfactuals"
    """
```

SAFETY CONSTRAINTS (MUST FOLLOW):
- counterfactual absent → return {"mean_fidelity": None, ..., "status": "BLOCKED_no_counterfactuals"}
- NEVER return 0.0 as mean_fidelity when there are no counterfactuals
- Do NOT read "oracle_best_action" from agent observation — read is_oracle_best from counterfactual record as eval label only
- Do NOT expose oracle_best_action, true_control_grammar, or any FORBIDDEN_AGENT_KEYS to inference input

CRITICAL WARNING (from T2 claim-metric-alignment audit):
- `predicted_top1_delta` (the "predicted" side of fidelity) must be the MODEL'S OWN rollout prediction
  output, NOT the oracle counterfactual_progress_delta read from the dataset.
- If both sides come from the same counterfactual record, the metric collapses to trivially 1.0
  (no discriminability). This would be a fake metric.
- If the model does NOT have a separate rollout prediction head (check eval_runner's _real_eval_step_records
  for a "predicted_progress_delta" field): return status="BLOCKED_no_model_rollout_prediction"
  and mean_fidelity=None rather than faking the computation.
- The "actual_delta" side = step's progress_delta from training_labels (ground truth, eval label)
- The "predicted" side = model's forward-pass rollout head output for that counterfactual
  (must be separately logged in eval traces; check if it exists first)

Input structure: episodes is a list of dicts (from eval_runner scored_episodes). Each episode
has a "steps" list. Each step may have a "counterfactuals" list (CounterfactualRecord-like dicts
with keys: is_oracle_best, counterfactual_progress_delta). The step also has "progress_delta".
If counterfactuals is absent or empty, skip the step.

2. In src/frcgw/evaluation/eval_runner.py:
- Add "alternative_rollout_fidelity": alternative_rollout_fidelity to METRIC_FUNCTIONS dict
- Add the import at the top

3. In scripts/10_run_lr_real_eval.py:
- Find the BLOCKED marker for C4/rollout_fidelity and replace with actual call
- Read the file to understand exact location before editing (do not guess)
- Only change the C4 marker block, nothing else

4. In tests/test_step5_rollout_fidelity.py, write 6 tests:
   - test_blocked_when_no_counterfactuals(): empty counterfactuals → status "BLOCKED_no_counterfactuals", mean_fidelity is None (not 0.0)
   - test_computes_from_progress_delta(): synthetic episode with known predicted_top1_delta=0.5, actual=0.4 → fidelity = 1.0 - 0.1 = 0.9
   - test_wrapper_status_reflects_blocked(): when all episodes blocked, wrapper output has explicit status
   - test_no_oracle_leakage(): metric function signature does not accept oracle_best_action as parameter
   - test_eval_runner_wired(): METRIC_FUNCTIONS["alternative_rollout_fidelity"] is not None
   - test_non_null_on_synthetic(): synthetic episode with valid counterfactuals → non-None result

REQUIRED_TESTS:
pytest tests/test_step5_rollout_fidelity.py tests/test_step4_counterfactual_no_leakage.py -q
Expected: 6 + 4 = 10 passed, no failures

ACCEPTANCE_CRITERIA:
- 6 new tests pass
- 4 STEP 4 counterfactual leakage regression tests still pass
- alternative_rollout_fidelity in METRIC_FUNCTIONS
- BLOCKED_no_counterfactuals status when no counterfactuals (not bare 0.0)
- No oracle_best_action or FORBIDDEN_AGENT_KEYS in function signature or local variable usage as model input

COMMIT_MESSAGE:
feat(step5/task2): C4 MET-WM-001 alternative_rollout_fidelity + eval_runner wire

STOP_CONDITION:
Stop if: (1) cannot locate BLOCKED marker in scripts/10_run_lr_real_eval.py,
(2) counterfactual_progress_delta field not present in data structure (report as BLOCKED),
(3) any FORBIDDEN_AGENT_KEYS would need to be read as model input to implement this
