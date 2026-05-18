from __future__ import annotations

import pytest

from frcgw.evaluation.eval_runner import METRIC_FUNCTIONS
from frcgw.evaluation.metrics import fair_ppc


def test_fair_ppc_returns_schema() -> None:
    result = fair_ppc(
        [
            {
                "total_progress": 2.0,
                "compute_logs": [
                    {
                        "wall_clock_seconds": 1.0,
                        "planning_calls": 1,
                        "rollout_steps": 2,
                        "candidate_actions_scored": 3,
                    }
                ],
            }
        ]
    )

    assert set(result) == {
        "ppc_wall_clock",
        "ppc_self_report",
        "total_wall_clock_seconds",
        "total_self_report_units",
        "total_progress",
    }


def test_fair_ppc_self_report_when_no_wall_clock() -> None:
    result = fair_ppc(
        [
            {
                "total_progress": 6.0,
                "compute_logs": [
                    {
                        "wall_clock_seconds": 0.0,
                        "planning_calls": 1,
                        "rollout_steps": 2,
                        "candidate_actions_scored": 3,
                    }
                ],
            }
        ]
    )

    assert result["ppc_wall_clock"] == 0.0
    assert result["ppc_self_report"] == pytest.approx(1.0)


def test_fair_ppc_positive_wall_clock() -> None:
    result = fair_ppc(
        [
            {
                "total_progress": 2.0,
                "compute_logs": [
                    {
                        "wall_clock_seconds": 1.0,
                        "planning_calls": 1,
                        "rollout_steps": 0,
                        "candidate_actions_scored": 1,
                    }
                ],
            }
        ]
    )

    assert result["ppc_wall_clock"] > 0.0
    assert result["ppc_wall_clock"] == pytest.approx(2.0)


def test_fair_ppc_in_metric_functions() -> None:
    assert METRIC_FUNCTIONS["fair_ppc"] is fair_ppc
