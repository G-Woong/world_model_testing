"""Verify that falsification_calibration is registered and handles degenerate inputs."""

from frcgw.evaluation.eval_runner import METRIC_FUNCTIONS
from frcgw.evaluation.metrics import falsification_calibration


def test_c5_falsification_calibration_registered():
    """C5 ECE must be registered in METRIC_FUNCTIONS."""
    assert "falsification_calibration" in METRIC_FUNCTIONS


def test_c5_calibration_degenerate_returns_zero_for_empty():
    """Empty episodes produce 0.0 ECE, not an error."""
    result = falsification_calibration([])
    assert result == 0.0


def test_c5_calibration_degenerate_constant_predictor():
    """Constant predictor calibration is well-defined."""
    episodes = [
        {
            "steps": [
                {
                    "eval_labels": {"true_wrong_hypothesis": True},
                    "predicted_wrong": True,
                    "wrong_prob": 0.9,
                },
                {
                    "eval_labels": {"true_wrong_hypothesis": False},
                    "predicted_wrong": False,
                    "wrong_prob": 0.9,
                },
            ]
        }
    ]
    result = falsification_calibration(episodes)
    assert isinstance(result, float)
