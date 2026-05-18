TASK_NAME: step6_c4_rollout_harness_c1_dispatch

BACKGROUND:
Two metric dispatch gaps found in STEP 5:

B4 (C4 gap): alternative_rollout_fidelity() is defined and working, but the eval harness
(scripts/10_run_lr_real_eval.py) never calls world_model_heads.rollout_step() per counterfactual
candidate to get model_predicted_progress_delta. Without this, C4 metric always returns
BLOCKED_no_model_rollout_prediction even when a trained checkpoint is loaded.

B5 (C1 gap): compute_wrong_grammar_persistence_v1() is defined in metrics.py but NOT dispatched
in eval_runner.py's METRIC_FUNCTIONS dict. The STEP 5 eval used legacy "wrong_control_grammar_persistence"
(label-only). The new v1 function uses selected_hypothesis_id tracking.

GOAL:
1. Add model rollout prediction call in the TracingAgent wrapper in scripts/10_run_lr_real_eval.py.
2. Add model_predicted_progress_delta optional field to CounterfactualRecord schema.
3. Register compute_wrong_grammar_persistence_v1 in eval_runner.py METRIC_FUNCTIONS.
4. Write tests verifying both fixes.

FILES_ALLOWED:
- src/frcgw/evaluation/eval_runner.py (METRIC_FUNCTIONS dict: add 1 line only)
- src/frcgw/evaluation/metrics.py (alternative_rollout_fidelity: add model_predicted fallback priority block ONLY; no other changes)
- scripts/10_run_lr_real_eval.py (TracingAgent wrapper: add model rollout call)
- src/frcgw/text_env/counterfactual_rollout.py (CounterfactualRecord: add optional field)
- tests/test_step6_model_rollout_prediction.py (new file)
- tests/test_step6_c1_persistence_v1_dispatch.py (new file)

FILES_FORBIDDEN:
- outputs/**
- data/**
- paper_context_ref/**
- src/frcgw/schemas/visibility.py
- .claude/**
- scripts/run_codex_task.ps1
- src/frcgw/models/world_model_heads.py (read-only; rollout_step API must not change)
- src/frcgw/evaluation/frcg_agent.py (read-only; act() signature must not change)
- src/frcgw/schemas/step_schema.py (CounterfactualRecord is in step_schema.py — use counterfactual_rollout.py's generate_counterfactuals instead)

WAIT: CHECK IF CounterfactualRecord IS IN step_schema.py OR counterfactual_rollout.py BEFORE EDITING.
The schema is in src/frcgw/schemas/step_schema.py. But the plan says to edit counterfactual_rollout.py.
Resolution: the model_predicted_progress_delta field should be added to step_schema.CounterfactualRecord
via src/frcgw/schemas/step_schema.py — but that file is NOT in FILES_ALLOWED. Instead:
  - Add model_predicted_progress_delta as a field on the dict record emitted by _TracingAgent.act()
    (in scripts/10_run_lr_real_eval.py), not in the dataclass schema.
  - The alternative_rollout_fidelity metric already reads from dicts by field name lookup.
  - This avoids schema file modification.

REQUIRED_IMPLEMENTATION:

## 1. eval_runner.py — add C1 v1 dispatch (1 line)

In the METRIC_FUNCTIONS dict, add after "wrong_control_grammar_persistence":
```python
"wrong_grammar_persistence_v1": compute_wrong_grammar_persistence_v1,
```

Also add the import: from frcgw.evaluation.metrics import compute_wrong_grammar_persistence_v1
(or ensure it's already imported at the top).

## 2. metrics.py — NO CHANGES NEEDED

The existing _predicted_top1_delta_for_step() function already includes "model_predicted_progress_delta"
as a fallback key (lines 255-256). So alternative_rollout_fidelity() will automatically read it
from step records if present. No change needed to metrics.py.

## 3. scripts/10_run_lr_real_eval.py — TracingAgent rollout prediction

In _TracingAgent.act(), after computing the action and compute_log, add model rollout prediction:

The TracingAgent wraps self._agent. It needs to call world_model_heads.rollout_step() for each
counterfactual candidate. However, the TracingAgent does not have direct access to model_out
within act(). The model rollout must be called using the agent's model if available.

Implementation approach:
- After `action, compute_log = self._agent.act(obs)`, check if `hasattr(self._agent, 'model')` and the model has `world_model_heads`.
- If yes AND valid_trained_eval (ckpt_path is not None in agent config):
  - call `model_out = self._agent.model.forward(obs)` (note: this was already called inside act(), so this is a second forward pass — acceptable for smoke eval with 10 episodes)
  - for each candidate in obs.candidate_actions_public[:3] (top 3 candidates):
    - hypothesis_id = i (enumerate candidates)
    - rollout = self._agent.model.world_model_heads.rollout_step(model_out.shared_h, model_out.z_state, candidate.action_type, hypothesis_id, H=1)
    - predicted_delta = float(rollout.progress_pred.squeeze().item())
  - record the per-candidate model_predicted_progress_delta in a list

Then add to self.records[-1] (the dict just appended):
```python
"model_rollout_predictions": [
    {"candidate_idx": i, "action_type": c.action_type, "model_predicted_progress_delta": delta}
    for i, (c, delta) in enumerate(zip(candidates_used, predicted_deltas))
]
```

Also add a top-level `"model_predicted_progress_delta"` field to the step record as the max
of the predicted deltas (for direct use by _predicted_top1_delta_for_step in metrics.py).

IMPORTANT: This additional forward pass must be inside torch.no_grad() to avoid memory issues.
IMPORTANT: If the agent's model is None or ckpt_path is None, set model_predicted_progress_delta=None
and model_rollout_predictions=[]. Do NOT raise an error.
IMPORTANT: model_predicted_progress_delta must NEVER flow into PublicObservation (obs).
It is only added to the tracing records after act() completes.

## 4. Leakage prevention (critical)
The model_predicted_progress_delta is the model's prediction, NOT oracle. It must only appear in:
  - self.records (tracing data, written to JSON after episode)
  - step["model_predicted_progress_delta"] (post-act trace field)
It must NEVER be added to PublicObservation, eval_labels, or any input to the next act() call.
Add a comment in the code: "# model prediction trace — never flows to obs (leakage prevention)"

REQUIRED_TESTS:

### tests/test_step6_model_rollout_prediction.py

1. test_c4_metric_reads_model_prediction(): create mock episode with steps having model_predicted_progress_delta > 0 and counterfactual records, call alternative_rollout_fidelity([episode]), assert status=="OK" and mean_fidelity is not None.
2. test_c4_metric_blocked_without_prediction(): create episode with counterfactuals but no model_predicted_progress_delta, assert status=="BLOCKED_no_model_rollout_prediction".
3. test_model_predicted_not_in_observation(): verify that after _TracingAgent.act(), the PublicObservation passed to next act() does NOT contain model_predicted_progress_delta (observation is immutable across calls).
4. test_rollout_prediction_none_when_no_ckpt(): mock agent without model, verify model_predicted_progress_delta=None in trace record (not 0.0, not error).
5. test_fake_zero_forbidden(): verify that when model has no weights loaded (random init), model_predicted_progress_delta is None (not 0.0 placeholder) OR explicitly documented as "random_init" status.

### tests/test_step6_c1_persistence_v1_dispatch.py

6. test_persistence_v1_in_metric_functions(): from frcgw.evaluation.eval_runner import METRIC_FUNCTIONS; assert "wrong_grammar_persistence_v1" in METRIC_FUNCTIONS
7. test_persistence_v1_callable(): assert callable(METRIC_FUNCTIONS["wrong_grammar_persistence_v1"])
8. test_persistence_v1_returns_dict(): call METRIC_FUNCTIONS["wrong_grammar_persistence_v1"]([]) returns dict with keys: mean_persistence, median, count_blocked, count_episodes, status

ACCEPTANCE_CRITERIA:
- 8 tests PASS
- eval_runner.py diff: exactly 1 line added to METRIC_FUNCTIONS dict (+ import if needed)
- metrics.py: NO changes (zero diff) — alternative_rollout_fidelity already handles model_predicted_progress_delta
- model_predicted_progress_delta never appears in PublicObservation fields
- No bare 0.0 for model_predicted_progress_delta when model is not loaded (must be None)
- STEP 5 eval trace files in outputs/ not modified

COMMIT_MESSAGE:
feat(step6/task4): C4 model rollout prediction harness + C1 persistence_v1 dispatch

STOP_CONDITION:
Stop if: (1) any FORBIDDEN file is modified; (2) model_predicted_progress_delta is added to PublicObservation; (3) world_model_heads.py rollout_step signature is changed; (4) metrics.py is modified beyond the 1-block fallback addition (and even that is not needed per analysis above); (5) fake 0.0 used instead of None for missing model.
