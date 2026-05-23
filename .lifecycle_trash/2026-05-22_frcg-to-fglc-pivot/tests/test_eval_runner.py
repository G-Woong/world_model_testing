from __future__ import annotations

import json
from pathlib import Path

import pytest

from frcgw.evaluation.baselines import FrozenBaseAgent, ReactiveAgent
from frcgw.evaluation.compute_budget import ComputeBudgetLog
from frcgw.evaluation.eval_runner import EvaluationResult, EvaluationRunner


METRICS = [
    "task_success_rate",
    "normalized_return",
    "wrong_control_grammar_persistence",
    "failed_action_repetition_rate",
    "recovery_delay",
    "falsification_precision_recall",
    "falsification_calibration",
    "progress_per_compute",
    "false_planning_call_rate",
    "action_switch_delay",
]


def _config() -> dict:
    return {
        "seeds": [0, 1],
        "splits": ["text_id"],
        "metrics": METRICS,
        "compute_budget": {
            "planning_calls_cap": 5,
            "rollout_steps_cap": 10,
            "max_candidates_per_call": 4,
        },
        "report_path": "unused",
        "forbidden_fields": [
            "true_regime",
            "true_control_grammar",
            "true_change_point",
            "true_reveal_vs_shift",
            "true_wrong_hypothesis",
            "counterfactual_action_effects",
            "oracle_regime_action",
            "oracle_grammar_action",
            "split_id",
            "ood_type",
            "template_id",
            "seed",
            "policy_id",
        ],
    }


def _episode(episode_index: int) -> dict:
    steps = []
    for step_index in range(3):
        steps.append(
            {
                "step_index": step_index,
                "public_input": {
                    "instruction": "click button",
                    "history_public": [],
                    "candidate_actions_public": [
                        {"action_id": "a1", "action_type": "click", "action_params": {}}
                    ],
                },
                "eval_labels": {
                    "true_wrong_hypothesis": False,
                    "evidence_timestamp": None,
                    "hypothesis_update_timestamp": None,
                    "recovery_timestamp": None,
                },
                "targets": {
                    "progress_delta": 0.1,
                    "true_failed_action": False,
                    "failure_reason": None,
                    "true_regime": "r0",
                    "true_control_grammar": "g0",
                    "true_change_point": "none",
                    "true_reveal_vs_shift": "none",
                    "true_action_effect_type": "click_effect",
                    "recovery_action_id": None,
                    "valid_hypothesis_switch": None,
                },
                "predicted_wrong": False,
                "wrong_prob": 0.1,
                "rewrite_timestamp": None,
                "planning_events": [],
            }
        )
    return {"episode_id": f"ep_{episode_index}", "steps": steps}


@pytest.fixture()
def synthetic_jsonl(tmp_path: Path) -> Path:
    path = tmp_path / "synthetic.jsonl"
    path.write_text(
        "\n".join(json.dumps(_episode(index)) for index in range(2)) + "\n",
        encoding="utf-8",
    )
    return path


def test_evaluation_runner_loads_config_without_error() -> None:
    runner = EvaluationRunner(_config())

    assert runner is not None


def test_run_with_frozen_base_agent_returns_evaluation_result(synthetic_jsonl: Path) -> None:
    result = EvaluationRunner(_config()).run(FrozenBaseAgent(), synthetic_jsonl, "text_id", 0)

    assert isinstance(result, EvaluationResult)
    assert result.agent_id == "BASE-001"
    assert result.n_episodes == 2
    assert isinstance(result.compute_log, ComputeBudgetLog)


def test_evaluation_result_metrics_include_all_metric_names(synthetic_jsonl: Path) -> None:
    result = EvaluationRunner(_config()).run(FrozenBaseAgent(), synthetic_jsonl, "text_id", 0)

    assert set(METRICS).issubset(result.metrics)


def test_forbidden_observation_key_raises_assertion(tmp_path: Path) -> None:
    episode = _episode(0)
    episode["steps"][0]["public_input"]["true_regime"] = "hidden"
    path = tmp_path / "leaky.jsonl"
    path.write_text(json.dumps(episode) + "\n", encoding="utf-8")

    with pytest.raises(AssertionError):
        EvaluationRunner(_config()).run(FrozenBaseAgent(), path, "text_id", 0)


def test_write_report_creates_metrics_json(synthetic_jsonl: Path, tmp_path: Path) -> None:
    runner = EvaluationRunner(_config())
    result = runner.run(FrozenBaseAgent(), synthetic_jsonl, "text_id", 0)

    report_path = Path(runner.write_report([result], tmp_path))

    assert report_path.exists()
    assert report_path.name == "metrics.json"


def test_metrics_json_contains_no_placeholder_none_for_numeric_metrics(
    synthetic_jsonl: Path, tmp_path: Path
) -> None:
    runner = EvaluationRunner(_config())
    result = runner.run(FrozenBaseAgent(), synthetic_jsonl, "text_id", 0)
    report_path = Path(runner.write_report([result], tmp_path))

    payload = json.loads(report_path.read_text(encoding="utf-8"))
    metrics = payload["results"][0]["metrics"]
    for value in metrics.values():
        if isinstance(value, dict):
            assert all(isinstance(child, float) for child in value.values())
        else:
            assert isinstance(value, float)
        assert value is not None


def test_run_all_baselines_returns_list_of_evaluation_results(synthetic_jsonl: Path) -> None:
    results = EvaluationRunner(_config()).run_all_baselines(
        [FrozenBaseAgent(), ReactiveAgent()],
        synthetic_jsonl,
        "text_id",
    )

    assert len(results) == 4
    assert all(isinstance(result, EvaluationResult) for result in results)
