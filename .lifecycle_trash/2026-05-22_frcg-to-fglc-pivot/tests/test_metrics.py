from __future__ import annotations

import math

import pytest

from frcgw.evaluation.compute_budget import ComputeBudgetLog
from frcgw.evaluation.metrics import (
    action_switch_delay,
    assert_no_hidden_labels_in_input,
    failed_action_repetition_rate,
    false_planning_call_rate,
    falsification_calibration,
    falsification_precision_recall,
    normalized_return,
    progress_per_compute,
    recovery_delay,
    task_success_rate,
    wrong_control_grammar_persistence,
)


def test_task_success_rate() -> None:
    assert task_success_rate([]) == 0.0
    assert task_success_rate([{"success": False}, {"success": False}, {"success": False}]) == 0.0
    assert task_success_rate([{"success": True}, {"success": True}, {"success": True}]) == 1.0
    assert task_success_rate([{"success": True}, {"success": False}, {"success": True}]) == pytest.approx(
        2 / 3
    )


def test_normalized_return_clamps_to_unit_interval() -> None:
    episodes = [{"total_return": -10.0}, {"total_return": 5.0}, {"total_return": 20.0}]

    assert normalized_return([]) == 0.0
    assert normalized_return(episodes, task_min=0.0, task_max=10.0) == pytest.approx(0.5)


def test_wrong_control_grammar_persistence_skips_none_and_averages_valid_pairs() -> None:
    episodes = [
        {"eval_labels": {"evidence_timestamp": 2, "hypothesis_update_timestamp": 7}},
        {"eval_labels": {"evidence_timestamp": None, "hypothesis_update_timestamp": 9}},
        {"eval_labels": None},
        {"eval_labels": {"evidence_timestamp": 4, "hypothesis_update_timestamp": 3}},
        {"eval_labels": {"evidence_timestamp": 10, "hypothesis_update_timestamp": 16}},
    ]

    assert wrong_control_grammar_persistence([]) == 0.0
    assert wrong_control_grammar_persistence(episodes) == pytest.approx(5.5)


def test_failed_action_repetition_rate_counts_consecutive_same_action_failures() -> None:
    episodes = [
        {
            "steps": [
                {"failed": True, "action_type": "click", "action_params": {"id": "a"}},
                {"failed": True, "action_type": "click", "action_params": {"id": "a"}},
                {"failed": True, "action_type": "type", "action_params": {"text": "x"}},
                {"failed": False, "action_type": "type", "action_params": {"text": "x"}},
                {"failed": True, "action_type": "type", "action_params": {"text": "x"}},
                {"failed": True, "action_type": "type", "action_params": {"text": "x"}},
            ]
        }
    ]

    assert failed_action_repetition_rate([]) == 0.0
    assert failed_action_repetition_rate(episodes) == pytest.approx(2 / 5)


def test_recovery_delay_mean_of_non_none_non_negative_pairs() -> None:
    episodes = [
        {"eval_labels": {"evidence_timestamp": 3, "recovery_timestamp": 8}},
        {"eval_labels": {"evidence_timestamp": 5, "recovery_timestamp": None}},
        {"eval_labels": {"evidence_timestamp": 10, "recovery_timestamp": 9}},
        {"eval_labels": {"evidence_timestamp": 1, "recovery_timestamp": 7}},
    ]

    assert recovery_delay([]) == 0.0
    assert recovery_delay(episodes) == pytest.approx(5.5)


def test_falsification_precision_recall_counts_tp_fp_fn_and_empty_case() -> None:
    episodes = [
        {
            "steps": [
                {"predicted_wrong": True, "eval_labels": {"true_wrong_hypothesis": True}},
                {"predicted_wrong": True, "eval_labels": {"true_wrong_hypothesis": False}},
                {"predicted_wrong": False, "eval_labels": {"true_wrong_hypothesis": True}},
                {"predicted_wrong": False, "eval_labels": {"true_wrong_hypothesis": False}},
                {"predicted_wrong": True, "eval_labels": {"true_wrong_hypothesis": None}},
            ]
        }
    ]

    result = falsification_precision_recall(episodes)
    assert result == {"precision": 0.5, "recall": 0.5, "f1": 0.5}
    assert falsification_precision_recall([]) == {"precision": 0.0, "recall": 0.0, "f1": 0.0}


def test_falsification_calibration_returns_unit_interval_float() -> None:
    episodes = [
        {
            "steps": [
                {"wrong_prob": 0.9, "eval_labels": {"true_wrong_hypothesis": True}},
                {"wrong_prob": 0.2, "eval_labels": {"true_wrong_hypothesis": False}},
                {"wrong_prob": 0.7, "eval_labels": {"true_wrong_hypothesis": None}},
            ]
        }
    ]

    result = falsification_calibration(episodes, n_bins=10)
    assert isinstance(result, float)
    assert 0.0 <= result <= 1.0
    assert math.isclose(falsification_calibration([]), 0.0)


def test_progress_per_compute_uses_total_progress_over_total_compute_units() -> None:
    episodes = [{"total_progress": 6.0}, {"total_progress": 4.0}]
    compute_logs = [
        ComputeBudgetLog(1, 2, 3, 4, 0.1),
        ComputeBudgetLog(2, 3, 4, 5, 0.2),
    ]

    assert progress_per_compute([], []) == 0.0
    assert progress_per_compute(episodes, compute_logs) == pytest.approx(10 / 15)


def test_false_planning_call_rate_ratio() -> None:
    episodes = [
        {
            "planning_events": [
                {"action_changed": False, "progress_changed": False},
                {"action_changed": True, "progress_changed": False},
                {"action_changed": False, "progress_changed": True},
                {"action_changed": False, "progress_changed": False},
            ]
        }
    ]

    assert false_planning_call_rate([]) == 0.0
    assert false_planning_call_rate(episodes) == pytest.approx(0.5)


def test_action_switch_delay_mean_of_valid_pairs() -> None:
    episodes = [
        {"eval_labels": {"evidence_timestamp": 2}, "rewrite_timestamp": 5},
        {"eval_labels": {"evidence_timestamp": None}, "rewrite_timestamp": 7},
        {"eval_labels": {"evidence_timestamp": 10}, "rewrite_timestamp": 9},
        {"eval_labels": {"evidence_timestamp": 1}, "rewrite_timestamp": 6},
    ]

    assert action_switch_delay([]) == 0.0
    assert action_switch_delay(episodes) == pytest.approx(4.0)


def test_assert_no_hidden_labels_in_input_raises_for_forbidden_keys() -> None:
    for obs in ({"true_regime": "A"}, {"oracle_best_action": "click"}, {"audit_metadata": {}}):
        with pytest.raises(AssertionError):
            assert_no_hidden_labels_in_input(obs)

    assert_no_hidden_labels_in_input({"public_text": "visible", "reward": 1.0})
