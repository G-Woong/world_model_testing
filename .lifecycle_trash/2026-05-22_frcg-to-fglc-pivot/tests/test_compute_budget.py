from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from frcgw.evaluation.compute_budget import ComputeBudgetLog


def test_compute_budget_log_instantiation_typical_values() -> None:
    log = ComputeBudgetLog(
        planning_calls=2,
        rollout_steps=12,
        candidate_actions_scored=40,
        top_k_alternatives=5,
        wall_clock_seconds=1.25,
    )

    assert log.planning_calls == 2
    assert log.rollout_steps == 12
    assert log.candidate_actions_scored == 40
    assert log.top_k_alternatives == 5
    assert isinstance(log.wall_clock_seconds, float)
    assert log.wall_clock_seconds >= 0.0


def test_compute_budget_log_is_frozen() -> None:
    log = ComputeBudgetLog(1, 2, 3, 4, 0.5)

    with pytest.raises(FrozenInstanceError):
        log.planning_calls = 99  # type: ignore[misc]


def test_total_compute_units() -> None:
    log = ComputeBudgetLog(
        planning_calls=3,
        rollout_steps=7,
        candidate_actions_scored=11,
        top_k_alternatives=2,
        wall_clock_seconds=0.75,
    )

    assert log.total_compute_units() == 21
