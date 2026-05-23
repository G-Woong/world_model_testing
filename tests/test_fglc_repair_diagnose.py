from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from fglc.repair.diagnose import CANONICAL_METRIC_KEYS, diagnose
from fglc.repair.taxonomy import FailureCauseId


def test_empty_metrics_with_R3_falls_back_to_bug_suspected():
    assert diagnose({}, "R3") == [FailureCauseId.IMPLEMENTATION_BUG_SUSPECTED]


def test_id_nll_high_fires_undercapacity():
    result = diagnose({"id_nll": 0.7, "stagnant_epochs": 12, "train_nll": 0.7}, "R3")
    assert FailureCauseId.MODEL_UNDERCAPACITY in result


def test_id_nll_below_threshold_does_not_fire():
    result = diagnose({"id_nll": 0.4, "stagnant_epochs": 12}, "R3")
    assert FailureCauseId.MODEL_UNDERCAPACITY not in result


def test_phase_filter_drops_R6_causes_in_R3():
    result = diagnose({"correction_norm_mean": 0.005}, "R3")
    assert FailureCauseId.CORRECTION_TOO_WEAK not in result


def test_dedup_unique_causes():
    result = diagnose({"corrected_nll_gain": 0.05, "planner_return_gain": -0.1}, "R7")
    assert result.count(FailureCauseId.CORRECTION_TOO_LARGE) <= 1


def test_attention_collapse_fires_low_entropy():
    result = diagnose({"attention_entropy": 0.05, "log_k": 2.0}, "R5")
    assert FailureCauseId.ATTENTION_COLLAPSE in result


def test_corrected_gain_positive_fires_correction_too_large():
    result = diagnose({"corrected_nll_gain": 0.05}, "R6")
    assert FailureCauseId.CORRECTION_TOO_LARGE in result


def test_invalid_phase_raises():
    with pytest.raises(ValueError):
        diagnose({"id_nll": 0.7}, "R99")


def test_canonical_metric_keys_nonempty():
    assert len(CANONICAL_METRIC_KEYS) >= 10
    assert all(isinstance(key, str) for key in CANONICAL_METRIC_KEYS)
