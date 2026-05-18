from __future__ import annotations

import pytest

from frcgw.evaluation.calibration import (
    BLOCKED_DEGENERATE_PREDICTOR,
    check_c3_nondegenerate,
    compute_ece_if_valid,
    temperature_scale_probs,
)


def test_blocked_degenerate_predictor_guard() -> None:
    result = compute_ece_if_valid([0.5] * 10, [True] * 10)

    assert result["status"] == BLOCKED_DEGENERATE_PREDICTOR
    assert result["ece"] is None
    assert result["unique_count"] == 1


def test_ece_ok_with_diverse_probs() -> None:
    result = compute_ece_if_valid(
        [0.1, 0.3, 0.5, 0.7, 0.9, 0.2, 0.4, 0.6, 0.8, 0.15],
        [False, False, True, True, True, False, False, True, True, False],
    )

    assert result["status"] == "OK"
    assert isinstance(result["ece"], float)


def test_c3_gate_blocks_degenerate() -> None:
    assert check_c3_nondegenerate("BLOCKED") is False
    assert check_c3_nondegenerate("READY_CANDIDATE") is True


def test_temperature_scale() -> None:
    scaled_probs = temperature_scale_probs([0.3, 0.7], 2.0)

    assert all(isinstance(prob, float) for prob in scaled_probs)
    assert sum(scaled_probs) == pytest.approx(1.0)
