from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from frcgw.evaluation.baselines import FrozenBaseAgent
from frcgw.evaluation.compute_budget import ComputeBudgetLog
from frcgw.evaluation.eval_runner import (
    EvaluationRunner,
    _compute_episode_timestamps,
)
from frcgw.schemas.step_schema import CandidateAction, PublicObservation


def _config(metrics: list[str] | None = None) -> dict[str, Any]:
    return {
        "seeds": [0],
        "splits": ["text_id"],
        "metrics": metrics
        or [
            "recovery_delay",
            "wrong_control_grammar_persistence",
            "falsification_precision_recall",
        ],
        "compute_budget": {},
        "report_path": "unused",
        "forbidden_fields": [],
    }


def _step(
    step_index: int,
    true_wrong_hypothesis: bool,
    progress_delta: float,
    *,
    predicted_wrong: bool = False,
) -> dict[str, Any]:
    return {
        "step_index": step_index,
        "public_observation": {
            "instruction": "test",
            "history_public": [],
            "candidate_actions_public": [
                {"action_id": "a1", "action_type": "click", "action_params": {}}
            ],
        },
        "evaluation_labels": {
            "true_wrong_hypothesis": true_wrong_hypothesis,
            "evidence_timestamp": step_index if true_wrong_hypothesis else None,
            "hypothesis_update_timestamp": None,
            "recovery_timestamp": None,
            "ood_type": None,
        },
        "training_labels": {
            "progress_delta": progress_delta,
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
        "predicted_wrong": predicted_wrong,
    }


def _timestamp_steps() -> list[dict[str, Any]]:
    return [
        _step(0, False, 0.0),
        _step(1, True, 0.0),
        _step(2, True, 0.0),
        _step(3, False, 0.0),
        _step(4, False, 0.5),
    ]


def _write_episode_jsonl(tmp_path: Path, steps: list[dict[str, Any]]) -> Path:
    path = tmp_path / "episode.jsonl"
    path.write_text(json.dumps({"episode_id": "ep0", "steps": steps}) + "\n", encoding="utf-8")
    return path


def _step_results(steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    results = []
    for step in steps:
        results.append(
            {
                "step_index": step["step_index"],
                "eval_labels": step["evaluation_labels"],
                "progress_delta": step["training_labels"]["progress_delta"],
            }
        )
    return results


def test_compute_episode_timestamps_from_true_false_progress_sequence() -> None:
    timestamps = _compute_episode_timestamps(_step_results(_timestamp_steps()))

    assert timestamps == {
        "evidence_timestamp": 1,
        "hypothesis_update_timestamp": 3,
        "recovery_timestamp": 4,
    }


def test_compute_episode_timestamps_all_false_returns_none() -> None:
    steps = [_step(index, False, 0.0) for index in range(3)]

    timestamps = _compute_episode_timestamps(_step_results(steps))

    assert timestamps == {
        "evidence_timestamp": None,
        "hypothesis_update_timestamp": None,
        "recovery_timestamp": None,
    }


def test_compute_episode_timestamps_true_without_false_keeps_update_none() -> None:
    steps = [
        _step(0, False, 0.0),
        _step(1, False, 0.0),
        _step(2, True, 0.0),
        _step(3, True, 0.25),
    ]

    timestamps = _compute_episode_timestamps(_step_results(steps))

    assert timestamps == {
        "evidence_timestamp": 2,
        "hypothesis_update_timestamp": None,
        "recovery_timestamp": 3,
    }


def test_run_uses_computed_timestamps_for_recovery_delay(tmp_path: Path) -> None:
    jsonl_path = _write_episode_jsonl(tmp_path, _timestamp_steps())

    result = EvaluationRunner(_config()).run(FrozenBaseAgent(), jsonl_path, "text_id", seed=0)

    assert result.metrics["recovery_delay"] > 0.0
    assert result.metrics["recovery_delay"] == 3.0


def test_run_uses_computed_timestamps_for_wrong_control_grammar_persistence(
    tmp_path: Path,
) -> None:
    jsonl_path = _write_episode_jsonl(tmp_path, _timestamp_steps())

    result = EvaluationRunner(_config()).run(FrozenBaseAgent(), jsonl_path, "text_id", seed=0)

    assert result.metrics["wrong_control_grammar_persistence"] > 0.0
    assert result.metrics["wrong_control_grammar_persistence"] == 2.0


class LastPredictedWrongAgent:
    baseline_id = "TEST-LAST-PREDICTED"
    last_predicted_wrong = True

    def act(self, obs: PublicObservation) -> tuple[CandidateAction, ComputeBudgetLog]:
        return obs.candidate_actions_public[0], ComputeBudgetLog(0, 0, 1, 0, 0.0)


class NoLastPredictedWrongAgent:
    baseline_id = "TEST-FALLBACK"

    def act(self, obs: PublicObservation) -> tuple[CandidateAction, ComputeBudgetLog]:
        return obs.candidate_actions_public[0], ComputeBudgetLog(0, 0, 1, 0, 0.0)


def test_run_uses_agent_last_predicted_wrong_when_available(tmp_path: Path) -> None:
    jsonl_path = _write_episode_jsonl(tmp_path, _timestamp_steps())

    result = EvaluationRunner(_config()).run(
        LastPredictedWrongAgent(),
        jsonl_path,
        "text_id",
        seed=0,
    )

    assert result.metrics["falsification_precision_recall"] == {
        "precision": 0.4,
        "recall": 1.0,
        "f1": 0.5714285714285715,
    }


def test_run_without_agent_last_predicted_wrong_falls_back_to_jsonl(
    tmp_path: Path,
) -> None:
    steps = _timestamp_steps()
    steps[1]["predicted_wrong"] = True
    jsonl_path = _write_episode_jsonl(tmp_path, steps)

    result = EvaluationRunner(_config()).run(
        NoLastPredictedWrongAgent(),
        jsonl_path,
        "text_id",
        seed=0,
    )

    assert result.metrics["falsification_precision_recall"] == {
        "precision": 1.0,
        "recall": 0.5,
        "f1": 0.6666666666666666,
    }
