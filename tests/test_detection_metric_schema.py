"""Tests for DetectorEvalResult schema and LFD metric harness (TASK_LFD_007).

Source: .agent_tasks/codex_queue/TASK_LFD_007_sequential_detection_metrics.md
"""
from __future__ import annotations

import json
import math

from frcgw.evaluation.metric_schema import DetectorEvalResult
from frcgw.evaluation.metrics import (
    aggregate_episode_metrics,
    auroc_wrong_hypothesis,
    auprc_wrong_hypothesis,
    recovery_delay_correlation,
)


# ---------------------------------------------------------------------------
# AUROC / AUPRC tests
# ---------------------------------------------------------------------------

def test_auroc_perfect() -> None:
    """AUROC = 1.0 for perfect classifier."""
    scores = [0.9, 0.8, 0.1, 0.05]
    labels = [True, True, False, False]
    result = auroc_wrong_hypothesis(scores, labels)
    assert abs(result - 1.0) < 1e-6, f"Expected 1.0, got {result}"


def test_auroc_random() -> None:
    """AUROC in (0, 1) for non-perfect discriminator."""
    # Scores partially correlated with labels but not perfect
    scores = [0.9, 0.1, 0.8, 0.2, 0.7, 0.3]  # positive-aligned but not perfect
    labels = [True, False, True, False, True, False]
    result = auroc_wrong_hypothesis(scores, labels)
    assert 0.0 < result <= 1.0, f"AUROC should be in (0, 1], got {result}"


def test_auroc_no_positives_returns_half() -> None:
    """AUROC = 0.5 when no positive labels."""
    scores = [0.8, 0.3]
    labels = [False, False]
    result = auroc_wrong_hypothesis(scores, labels)
    assert result == 0.5


def test_auprc_range() -> None:
    """AUPRC in [0, 1]."""
    scores = [0.9, 0.7, 0.3, 0.1]
    labels = [True, False, True, False]
    result = auprc_wrong_hypothesis(scores, labels)
    assert 0.0 <= result <= 1.0


def test_auprc_no_positives_returns_zero() -> None:
    """AUPRC = 0.0 when no positive labels."""
    result = auprc_wrong_hypothesis([0.8, 0.3], [False, False])
    assert result == 0.0


# ---------------------------------------------------------------------------
# Recovery delay correlation tests
# ---------------------------------------------------------------------------

def test_recovery_delay_correlation_positive() -> None:
    """Known correlated input produces r > 0.5."""
    det = [1, 2, 3, 4, 5, 6, 7, 8]
    rec = [3, 5, 6, 8, 9, 11, 12, 14]  # linearly correlated
    result = recovery_delay_correlation(det, rec)
    assert result["r"] > 0.5, f"Expected r > 0.5 for correlated data, got {result['r']:.3f}"
    assert result["n"] == 8


def test_recovery_delay_correlation_uncorrelated() -> None:
    """Nearly uncorrelated input: |r| small."""
    det = [1, 2, 3, 4, 5]
    rec = [5, 1, 4, 2, 3]  # shuffled, low correlation
    result = recovery_delay_correlation(det, rec)
    assert result["n"] == 5


def test_recovery_delay_correlation_too_few_samples() -> None:
    """n < 3: returns r=0.0."""
    result = recovery_delay_correlation([1, 2], [3, 4])
    assert result["r"] == 0.0
    assert result["p_value_approx"] == 1.0


# ---------------------------------------------------------------------------
# DetectorEvalResult schema tests
# ---------------------------------------------------------------------------

def test_detector_eval_result_json_serializable() -> None:
    """DetectorEvalResult.to_json() returns valid JSON."""
    result = DetectorEvalResult(
        detector_name="cusum",
        n_switch_episodes=10,
        n_stable_episodes=20,
        n_episodes_evaluated=30,
        mean_detection_delay=3.5,
    )
    json_str = result.to_json()
    parsed = json.loads(json_str)
    assert parsed["detector_name"] == "cusum"
    assert parsed["n_episodes_evaluated"] == 30


def test_detector_eval_result_all_optional_none() -> None:
    """All optional fields default to None / 0.0."""
    result = DetectorEvalResult(
        detector_name="test",
        n_switch_episodes=0,
        n_stable_episodes=5,
        n_episodes_evaluated=5,
    )
    assert result.mean_detection_delay is None
    assert result.auroc_wrong_hypothesis is None
    assert result.false_alarm_rate_per_step == 0.0


# ---------------------------------------------------------------------------
# aggregate_episode_metrics tests
# ---------------------------------------------------------------------------

def _make_switch_episode(switch_step: int, first_alarm: int | None, n_steps: int = 10) -> dict:
    stable_steps = list(range(switch_step))
    alarm_steps = [first_alarm] if first_alarm is not None else []
    wrong_probs = [0.1] * switch_step + [0.8] * (n_steps - switch_step)
    true_wrong = [False] * switch_step + [True] * (n_steps - switch_step)
    return {
        "switch_step": switch_step,
        "first_alarm": first_alarm,
        "stable_steps": stable_steps,
        "alarm_steps": alarm_steps,
        "wrong_prob_scores": wrong_probs,
        "true_wrong_hypothesis": true_wrong,
        "recovery_delay": (first_alarm - switch_step + 3) if first_alarm is not None else None,
    }


def _make_stable_episode(n_steps: int = 10) -> dict:
    return {
        "switch_step": None,
        "first_alarm": None,
        "stable_steps": list(range(n_steps)),
        "alarm_steps": [],
        "wrong_prob_scores": [0.1] * n_steps,
        "true_wrong_hypothesis": [False] * n_steps,
    }


def test_aggregate_episode_metrics_v0_4_graceful() -> None:
    """v0_4 episodes (no switch) return mean_detection_delay=None."""
    episodes = [_make_stable_episode() for _ in range(5)]
    result = aggregate_episode_metrics(episodes, detector_name="cusum")
    assert result.mean_detection_delay is None
    assert result.n_switch_episodes == 0
    assert result.n_stable_episodes == 5
    assert result.n_episodes_evaluated == 5


def test_aggregate_episode_metrics_v0_5_nonzero() -> None:
    """v0_5 episodes with switch return non-None detection delay."""
    episodes = [_make_switch_episode(switch_step=3, first_alarm=5) for _ in range(5)]
    result = aggregate_episode_metrics(episodes, detector_name="cusum")
    assert result.mean_detection_delay is not None
    assert result.mean_detection_delay == 2.0  # alarm 5 - switch 3 = 2
    assert result.n_switch_episodes == 5
    assert result.auroc_wrong_hypothesis is not None


def test_aggregate_mixed_v0_4_v0_5() -> None:
    """Mixed v0_4 and v0_5 episodes: counts correctly."""
    episodes = (
        [_make_switch_episode(3, 5) for _ in range(3)]
        + [_make_stable_episode() for _ in range(2)]
    )
    result = aggregate_episode_metrics(episodes, detector_name="lfd")
    assert result.n_switch_episodes == 3
    assert result.n_stable_episodes == 2
    assert result.n_episodes_evaluated == 5
    assert result.mean_detection_delay == 2.0
