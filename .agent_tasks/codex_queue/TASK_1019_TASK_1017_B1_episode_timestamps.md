TASK_NAME: TASK_1017_B1_episode_timestamps

BACKGROUND:
FRCG-WM P3 evaluation phase. P3 EVAL FAIL blocker B1:

`outputs/runs/p3_eval/metrics.json` shows:
  - `recovery_delay` = 0.0 for ALL agents
  - `wrong_control_grammar_persistence` = 0.0 for ALL agents
  - `falsification_precision_recall` f1 = 0.0 for ALL heuristic baselines

Root cause: `src/frcgw/evaluation/eval_runner.py` uses episode_eval_labels =
first step's evaluation_labels only. The collector always sets
`hypothesis_update_timestamp=None` and `recovery_timestamp=None` in
EvaluationLabels (collector.py line 224-225), so metrics always return 0.0.

Data inspection confirms:
  - 165 steps in test_id.jsonl: evidence_timestamp = step_index (non-null)
  - hypothesis_update_timestamp: 0 non-null  ← needs to be COMPUTED
  - recovery_timestamp: 0 non-null           ← needs to be COMPUTED
  - true_wrong_hypothesis: 50 True, 115 False, 0 null ← sequence IS present
  - 113 of 165 episodes (train+test_id) have True→False transitions ← usable

Fix strategy (NO data regeneration needed):
  After processing all steps in run(), compute episode-level timestamps from the
  step sequence of true_wrong_hypothesis and progress_delta:
  - evidence_timestamp  = first step_index where true_wrong_hypothesis = True
  - hypothesis_update_timestamp = first step_index where true_wrong_hypothesis
    transitions from True → False (after being True)
  - recovery_timestamp = first step_index where progress_delta > 0
    AND a prior step had true_wrong_hypothesis = True

  Also: heuristic baseline agents don't set predicted_wrong per step.
  Support `predicted_wrong` from agent.last_predicted_wrong if available.

Source MDs:
- paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md §5 metric defs (lines 151~179)
- paper_context_ref/15_TDD_TECHNICAL_DESIGN_DOCUMENT_v1.md §15 lines 1044~1058

GOAL:
Fix `src/frcgw/evaluation/eval_runner.py`:
1. Store progress_delta per step in step_results
2. Compute episode-level timestamps from step sequence
3. Support agent.last_predicted_wrong for predicted_wrong field
Write `tests/test_eval_runner_timestamps.py` to verify the fix.

FILES_ALLOWED:
src/frcgw/evaluation/eval_runner.py
tests/test_eval_runner_timestamps.py

FILES_FORBIDDEN:
paper_context_ref/
.claude/
.mcp.json
.venv/
data/
outputs/
secrets/
.env
scripts/run_codex_task.ps1
src/frcgw/gui_env/
src/frcgw/logging/
src/frcgw/models/
src/frcgw/objectives/
src/frcgw/planning/
src/frcgw/training/
src/frcgw/schemas/
src/frcgw/data/
src/frcgw/text_env/
src/frcgw/evaluation/metrics.py
src/frcgw/evaluation/compute_budget.py
src/frcgw/evaluation/baselines.py
src/frcgw/evaluation/ablations.py
src/frcgw/evaluation/reporter.py
configs/
scripts/03_eval_text_smoke.py
scripts/08_run_core_ablations.py

REQUIRED_IMPLEMENTATION:

### src/frcgw/evaluation/eval_runner.py — targeted changes only

Change 1: In the step loop, store progress_delta in step_results dict.
Add "progress_delta" key to the step_results.append({...}) call:
  "progress_delta": float(targets.get("progress_delta") or 0.0),

Change 2: After the step loop (still inside the episode loop), compute episode
timestamps using this helper function:

```python
def _compute_episode_timestamps(step_results: list[dict]) -> dict:
    """Compute episode-level eval timestamps from step sequence.

    evidence_timestamp: first step where true_wrong_hypothesis=True
    hypothesis_update_timestamp: first step where true_wrong_hypothesis
        transitions True→False after evidence_timestamp
    recovery_timestamp: first step where progress_delta > 0 after evidence_timestamp
    """
    evidence_ts = None
    hypothesis_update_ts = None
    recovery_ts = None
    was_wrong = False

    for sr in step_results:
        idx = sr.get("step_index", 0)
        el = sr.get("eval_labels", {}) or {}
        tw = el.get("true_wrong_hypothesis")
        pd = float(sr.get("progress_delta", 0.0))

        if tw is True:
            if evidence_ts is None:
                evidence_ts = idx
            was_wrong = True

        if was_wrong and tw is False and hypothesis_update_ts is None:
            hypothesis_update_ts = idx

        if was_wrong and pd > 0 and recovery_ts is None:
            recovery_ts = idx

    return {
        "evidence_timestamp": evidence_ts,
        "hypothesis_update_timestamp": hypothesis_update_ts,
        "recovery_timestamp": recovery_ts,
    }
```

Change 3: After collecting all step_results for an episode, compute timestamps and
update episode_eval_labels BEFORE appending to scored_episodes:

```python
episode_ts = _compute_episode_timestamps(step_results)
episode_eval_labels.update(episode_ts)
```

Note: episode_eval_labels is set to first step's eval_labels (existing logic).
update() adds/overwrites the 3 timestamp keys with computed values.

Change 4: Support agent.last_predicted_wrong in predicted_wrong field.
In the step loop, after action, compute_log = agent.act(obs):

```python
# Support FRCG agent's falsification signal; fallback to JSONL or False
if hasattr(agent, "last_predicted_wrong"):
    predicted_wrong_val = bool(agent.last_predicted_wrong)
else:
    predicted_wrong_val = bool(step.get("predicted_wrong", False))
```

Then use predicted_wrong_val in the step_results append instead of the current:
  "predicted_wrong": bool(step.get("predicted_wrong", False)),

NO OTHER CHANGES to eval_runner.py. Keep all existing logic intact.

REQUIRED_TESTS:

### tests/test_eval_runner_timestamps.py

Use a synthetic JSONL fixture (in tmp_path) with 1 episode, 5 steps:

Step sequence:
  0: true_wrong_hypothesis=False, progress_delta=0.0
  1: true_wrong_hypothesis=True,  progress_delta=0.0  ← evidence here (ts=1)
  2: true_wrong_hypothesis=True,  progress_delta=0.0
  3: true_wrong_hypothesis=False, progress_delta=0.0  ← hypothesis_update (ts=3)
  4: true_wrong_hypothesis=False, progress_delta=0.5  ← recovery (ts=4)

Expected timestamps:
  evidence_timestamp = 1
  hypothesis_update_timestamp = 3
  recovery_timestamp = 4

Fixture JSONL format (per step):
```json
{"step_index": 1, "public_observation": {"instruction": "test", "history_public": [],
  "candidate_actions_public": [{"action_id": "a1", "action_type": "click", "action_params": {}}]},
 "evaluation_labels": {"true_wrong_hypothesis": true, "evidence_timestamp": 1,
   "hypothesis_update_timestamp": null, "recovery_timestamp": null, "ood_type": null},
 "training_labels": {"progress_delta": 0.0, "true_failed_action": false,
   "failure_reason": null, "true_regime": "r0", "true_control_grammar": "g0",
   "true_change_point": "none", "true_reveal_vs_shift": "none",
   "true_action_effect_type": "click_effect", "recovery_action_id": null,
   "valid_hypothesis_switch": null}}
```

Tests:
1. _compute_episode_timestamps() with the 5-step sequence returns
   evidence_timestamp=1, hypothesis_update_timestamp=3, recovery_timestamp=4
2. _compute_episode_timestamps() with all-False sequence returns all None
3. _compute_episode_timestamps() with True at step 2, never False returns
   evidence_timestamp=2, hypothesis_update_timestamp=None, recovery_timestamp=<if pd>0>
4. EvaluationRunner.run(FrozenBaseAgent(), jsonl_path, "text_id", seed=0)
   returns EvaluationResult where result.metrics["recovery_delay"] > 0.0
   (because recovery_timestamp=4, evidence_timestamp=1, delay=3)
5. EvaluationRunner.run(FrozenBaseAgent(), jsonl_path, "text_id", seed=0)
   returns result.metrics["wrong_control_grammar_persistence"] > 0.0
   (hypothesis_update=3, evidence=1, persistence=2)
6. Agent with last_predicted_wrong=True → step_results[i]["predicted_wrong"]=True
   (create a mock agent class with last_predicted_wrong=True property)
7. Agent WITHOUT last_predicted_wrong → falls back to step.get("predicted_wrong", False)

ACCEPTANCE_CRITERIA:
1. pytest tests/test_eval_runner_timestamps.py -q → all pass
2. _compute_episode_timestamps is present in eval_runner.py (exported or module-level)
3. run() stores "progress_delta" in each step_results entry
4. run() calls _compute_episode_timestamps and updates episode_eval_labels
5. run() uses agent.last_predicted_wrong when available
6. No changes to other eval_runner.py methods (write_report, run_all_baselines, etc.)
7. Existing test_eval_runner.py still passes (no regressions)

COMMIT_MESSAGE:
fix(p3-eval-b1): compute episode timestamps from step sequence in eval_runner

STOP_CONDITION:
Stop if true_wrong_hypothesis is used as an inference input to agent.act().
Stop if _compute_episode_timestamps reads from agent's internal state
  (must only use already-collected step_results).
Stop if existing tests/test_eval_runner.py tests break.
