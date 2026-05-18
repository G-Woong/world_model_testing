from __future__ import annotations

import inspect

import pytest

from frcgw.evaluation.eval_runner import EvaluationRunner, METRIC_FUNCTIONS
from frcgw.evaluation.metrics import alternative_rollout_fidelity


def _episode_with_rollout_prediction(
    *,
    predicted_top1_delta: float = 0.5,
    actual_delta: float = 0.4,
) -> dict:
    return {
        "steps": [
            {
                "progress_delta": actual_delta,
                "predicted_top1_delta": predicted_top1_delta,
                "counterfactuals": [
                    {
                        "counterfactual_progress_delta": 1.0,
                        "is_oracle_best": True,
                    }
                ],
            }
        ]
    }


def test_blocked_when_no_counterfactuals() -> None:
    result = alternative_rollout_fidelity([{"steps": [{"progress_delta": 0.4}]}])

    assert result["status"] == "BLOCKED_no_counterfactuals"
    assert result["mean_fidelity"] is None
    assert result["mean_fidelity"] != 0.0
    assert result["count_blocked"] == 1


def test_computes_from_progress_delta() -> None:
    result = alternative_rollout_fidelity([_episode_with_rollout_prediction()])

    assert result["status"] == "OK"
    assert result["mean_fidelity"] == pytest.approx(0.9)


def test_wrapper_status_reflects_blocked() -> None:
    runner = EvaluationRunner({"metrics": ["alternative_rollout_fidelity"]})

    metrics = runner._compute_metrics([{"steps": [{"counterfactuals": []}]}], [])
    result = metrics["alternative_rollout_fidelity"]

    assert isinstance(result, dict)
    assert result["status"] == "BLOCKED_no_counterfactuals"
    assert result["mean_fidelity"] is None


def test_no_oracle_leakage() -> None:
    signature = inspect.signature(alternative_rollout_fidelity)

    assert "oracle_best_action" not in signature.parameters


def test_eval_runner_wired() -> None:
    assert METRIC_FUNCTIONS["alternative_rollout_fidelity"] is alternative_rollout_fidelity


def test_non_null_on_synthetic() -> None:
    result = alternative_rollout_fidelity([_episode_with_rollout_prediction()])

    assert result["status"] == "OK"
    assert result["mean_fidelity"] is not None
