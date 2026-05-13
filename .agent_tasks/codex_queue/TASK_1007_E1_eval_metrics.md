TASK_NAME: TASK_1007_E1_eval_metrics

BACKGROUND:
FRCG-WM P3 evaluation phase. `src/frcgw/evaluation/__init__.py` currently has `__all__ = []`
with "implementation deferred to P3/P6". The models/planning/training stack is complete
(P3 implementation gate passed, pytest 174 green). Now we need the evaluation layer.

This task implements two modules:
1. `src/frcgw/evaluation/metrics.py` — 10 metric functions
2. `src/frcgw/evaluation/compute_budget.py` — ComputeBudgetLog dataclass

Source MDs:
- paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md (metrics §5, compute §7)
- paper_context_ref/15_TDD_TECHNICAL_DESIGN_DOCUMENT_v1.md §15 lines 974~1042

Key schema:
- `src/frcgw/schemas/step_schema.py`: EvaluationLabels, TrainingLabels, PublicObservation
- EvaluationLabels has: true_wrong_hypothesis, h_exec_id, correct_hypothesis_id,
  evidence_timestamp, hypothesis_update_timestamp, recovery_timestamp, ood_type
- TrainingLabels has: true_failed_action, progress_delta, true_regime,
  true_control_grammar, etc.

GOAL:
Implement `src/frcgw/evaluation/metrics.py` with 10 metric functions and
`src/frcgw/evaluation/compute_budget.py` with ComputeBudgetLog. Write unit tests.

FILES_ALLOWED:
src/frcgw/evaluation/__init__.py
src/frcgw/evaluation/metrics.py
src/frcgw/evaluation/compute_budget.py
tests/test_metrics.py
tests/test_compute_budget.py

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

REQUIRED_IMPLEMENTATION:

### src/frcgw/evaluation/compute_budget.py

```python
"""frcgw.evaluation.compute_budget -- ComputeBudgetLog dataclass.
Source MD: paper_context_ref/15_TDD_TECHNICAL_DESIGN_DOCUMENT_v1.md §15 lines 1032~1042
"""
from dataclasses import dataclass

@dataclass(frozen=True)
class ComputeBudgetLog:
    planning_calls: int         # number of planning invocations
    rollout_steps: int          # total rollout steps across planning calls
    candidate_actions_scored: int  # hypotheses × actions scored
    top_k_alternatives: int     # alternatives evaluated per planning call
    wall_clock_seconds: float

    def total_compute_units(self) -> int:
        return self.planning_calls + self.rollout_steps + self.candidate_actions_scored
```

### src/frcgw/evaluation/metrics.py

Module docstring must cite:
  paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md §5 lines 151~179
  paper_context_ref/15_TDD_TECHNICAL_DESIGN_DOCUMENT_v1.md §15 lines 976~991

Implement these 10 functions. Each takes lists of per-episode data (dicts or dataclasses)
and returns a float scalar (or dict for precision/recall). Use only public data or
EvaluationLabels for ground truth. Never read FORBIDDEN_AGENT_KEYS from agent observation.

FORBIDDEN_AGENT_KEYS = {
    "true_regime", "true_control_grammar", "true_change_point",
    "true_reveal_vs_shift", "true_wrong_hypothesis", "counterfactual_action_effects",
    "oracle_regime_action", "oracle_grammar_action", "oracle_best_action",
    "split_id", "ood_type", "template_id", "seed", "policy_id", "audit_metadata",
}

1. task_success_rate(episodes: list[dict]) -> float
   episodes[i]["success"]: bool
   Returns: #success / len(episodes)

2. normalized_return(episodes: list[dict], task_min: float = 0.0, task_max: float = 1.0) -> float
   episodes[i]["total_return"]: float
   Returns: mean((r - task_min) / (task_max - task_min + 1e-8)) clamped to [0,1]

3. wrong_control_grammar_persistence(episodes: list[dict]) -> float
   Uses EvaluationLabels fields: evidence_timestamp, hypothesis_update_timestamp
   episodes[i]["eval_labels"]: dict with above keys (may be None → skip)
   Persistence = hypothesis_update_timestamp - evidence_timestamp per episode
   Returns: mean over episodes where both are not None and persistence >= 0

4. failed_action_repetition_rate(episodes: list[dict]) -> float
   episodes[i]["steps"]: list[dict] each with "failed": bool, "action_type": str, "action_params": dict
   Repetition: consecutive steps where failed=True AND same (action_type, action_params)
   Returns: #repetitions / max(1, #failure_opportunities)
   failure_opportunity = any step where failed=True

5. recovery_delay(episodes: list[dict]) -> float
   episodes[i]["eval_labels"]["evidence_timestamp"]: int | None
   episodes[i]["eval_labels"]["recovery_timestamp"]: int | None
   recovery_delay = recovery_timestamp - evidence_timestamp
   Returns: mean over episodes where both not None and delay >= 0

6. falsification_precision_recall(episodes: list[dict]) -> dict[str, float]
   episodes[i]["steps"]: list[dict] with:
     "predicted_wrong": bool  (model's falsification prediction)
     "eval_labels": dict with "true_wrong_hypothesis": bool | None
   Only count steps where true_wrong_hypothesis is not None.
   TP = predicted_wrong=True AND true_wrong_hypothesis=True
   FP = predicted_wrong=True AND true_wrong_hypothesis=False
   FN = predicted_wrong=False AND true_wrong_hypothesis=True
   Returns: {"precision": float, "recall": float, "f1": float}
   Use 0.0 for empty cases with no warnings.

7. falsification_calibration(episodes: list[dict], n_bins: int = 10) -> float
   episodes[i]["steps"]: list[dict] with:
     "wrong_prob": float  (model's P(wrong hypothesis))
     "eval_labels": dict with "true_wrong_hypothesis": bool | None
   Only steps where true_wrong_hypothesis is not None.
   ECE = sum_b (|B_b| / N) * |mean_confidence_b - mean_accuracy_b|
   Returns ECE float. If fewer than n_bins steps, still compute with available data.

8. progress_per_compute(episodes: list[dict], compute_logs: list[ComputeBudgetLog]) -> float
   episodes[i]["total_progress"]: float  (sum of progress_delta across steps)
   compute_logs[i].total_compute_units()
   Returns: sum(progress) / max(1, sum(compute_units))

9. false_planning_call_rate(episodes: list[dict]) -> float
   episodes[i]["planning_events"]: list[dict] each with:
     "action_changed": bool
     "progress_changed": bool
   false_call = not action_changed AND not progress_changed
   Returns: #false_calls / max(1, #total_planning_calls)

10. action_switch_delay(episodes: list[dict]) -> float
    episodes[i]["eval_labels"]["evidence_timestamp"]: int | None
    episodes[i]["rewrite_timestamp"]: int | None
    delay = rewrite_timestamp - evidence_timestamp
    Returns: mean over episodes where both not None and delay >= 0

Also add:
def assert_no_hidden_labels_in_input(obs_dict: dict, context: str = "") -> None:
    """Raise AssertionError if any FORBIDDEN_AGENT_KEY is in obs_dict."""
    ...
```

### src/frcgw/evaluation/__init__.py

Update to export:
```python
from frcgw.evaluation.compute_budget import ComputeBudgetLog
from frcgw.evaluation.metrics import (
    task_success_rate, normalized_return, wrong_control_grammar_persistence,
    failed_action_repetition_rate, recovery_delay, falsification_precision_recall,
    falsification_calibration, progress_per_compute, false_planning_call_rate,
    action_switch_delay, assert_no_hidden_labels_in_input,
)
__all__ = [
    "ComputeBudgetLog",
    "task_success_rate", "normalized_return", "wrong_control_grammar_persistence",
    "failed_action_repetition_rate", "recovery_delay", "falsification_precision_recall",
    "falsification_calibration", "progress_per_compute", "false_planning_call_rate",
    "action_switch_delay", "assert_no_hidden_labels_in_input",
]
```

REQUIRED_TESTS:

### tests/test_metrics.py

Test each of the 10 metric functions with minimal synthetic episode dicts.
Requirements:
- task_success_rate: 0/3=0.0, 3/3=1.0, 2/3≈0.667
- normalized_return: verify [0,1] clamping
- wrong_control_grammar_persistence: skip None labels, mean of valid ones
- failed_action_repetition_rate: consecutive same-action failures count correctly
- recovery_delay: mean of non-None pairs
- falsification_precision_recall: exact TP/FP/FN counts, verify precision=recall=0 for empty
- falsification_calibration: smoke test returns float in [0,1]
- progress_per_compute: sum(progress)/sum(compute_units) formula
- false_planning_call_rate: correct ratio
- action_switch_delay: mean of valid pairs
- assert_no_hidden_labels_in_input: raises AssertionError on forbidden key, passes clean dict

### tests/test_compute_budget.py

- ComputeBudgetLog instantiation with typical values
- frozen dataclass: cannot mutate
- total_compute_units(): planning_calls + rollout_steps + candidate_actions_scored
- wall_clock_seconds: float, not negative check (manual)

ACCEPTANCE_CRITERIA:
1. pytest tests/test_metrics.py tests/test_compute_budget.py -q → all pass, 0 failures
2. No import of forbidden fields from frcgw.schemas.step_schema in metrics.py
   (TrainingLabels fields are used only when passed as explicit eval_labels dicts,
    never as direct imports driving inference)
3. assert_no_hidden_labels_in_input raises AssertionError on at least:
   {"true_regime": "A"}, {"oracle_best_action": "click"}, {"audit_metadata": {}}
4. All 10 metric functions handle empty input lists without raising (return 0.0 or empty dict)
5. ComputeBudgetLog is frozen=True (immutable)
6. __init__.py __all__ populated (not empty list)

COMMIT_MESSAGE:
feat(p3-eval-e1): evaluation metrics + compute budget log

STOP_CONDITION:
Stop if any test imports or uses TrainingLabels/EvaluationLabels as model inference inputs.
Stop if any metric function reads "true_regime", "true_control_grammar",
"oracle_*", "split_id", "seed", "policy_id" from an agent observation dict
(these may only appear in eval_labels sub-dicts explicitly passed for scoring).
Stop if assert_no_hidden_labels_in_input is missing.
