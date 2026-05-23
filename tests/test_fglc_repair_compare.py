import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from fglc.repair.compare import MetricDirection, compare_metrics


def test_compare_lower_better_accept():
    result = compare_metrics(
        {"id_nll_1step": 0.42, "ood_mass_nll_1step": 0.51},
        {"id_nll_1step": 0.28, "ood_mass_nll_1step": 0.55},
        "id_nll_1step",
        {
            "id_nll_1step": MetricDirection.LOWER_BETTER,
            "ood_mass_nll_1step": MetricDirection.LOWER_BETTER,
        },
    )

    assert result["result"] == "accept"
    assert result["deltas"]["id_nll_1step"] == pytest.approx(-0.14)


def test_compare_lower_better_reject_no_improvement():
    result = compare_metrics(
        {"id_nll_1step": 0.42},
        {"id_nll_1step": 0.42},
        "id_nll_1step",
        {"id_nll_1step": "lower_better"},
    )

    assert result["result"] == "reject"


def test_compare_lower_better_reject_secondary_regression():
    result = compare_metrics(
        {"id_nll_1step": 0.42, "detection_auroc": 0.75},
        {"id_nll_1step": 0.34, "detection_auroc": 0.60},
        "id_nll_1step",
        {
            "id_nll_1step": "lower_better",
            "detection_auroc": "higher_better",
        },
    )

    assert result["result"] == "reject"
    assert result["deltas"]["detection_auroc"] == pytest.approx(-0.15)


def test_compare_higher_better_accept():
    result = compare_metrics(
        {"detection_auroc": 0.71, "id_nll_1step": 0.42},
        {"detection_auroc": 0.79, "id_nll_1step": 0.43},
        "detection_auroc",
        {
            "detection_auroc": "higher_better",
            "id_nll_1step": "lower_better",
        },
    )

    assert result["result"] == "accept"
    assert result["failed_metric_direction"] == "higher_better"


def test_compare_inconclusive_small_improvement():
    result = compare_metrics(
        {"id_nll_1step": 0.42},
        {"id_nll_1step": 0.39},
        "id_nll_1step",
        {"id_nll_1step": "lower_better"},
    )

    assert result["result"] == "inconclusive"


def test_compare_raises_on_missing_failed_metric():
    with pytest.raises(ValueError):
        compare_metrics(
            {"id_nll_1step": 0.42},
            {"id_nll_1step": 0.39},
            "ood_mass_nll_1step",
            {"ood_mass_nll_1step": "lower_better"},
        )


def test_compare_skips_secondary_with_none():
    result = compare_metrics(
        {"id_nll_1step": 0.42, "ood_friction_nll_1step": None},
        {"id_nll_1step": 0.28, "ood_friction_nll_1step": 0.50},
        "id_nll_1step",
        {
            "id_nll_1step": "lower_better",
            "ood_friction_nll_1step": "lower_better",
        },
    )

    assert result["result"] == "accept"
    assert result["deltas"]["ood_friction_nll_1step"] is None


def test_compare_returns_all_expected_keys():
    result = compare_metrics(
        {"id_nll_1step": 0.42},
        {"id_nll_1step": 0.39},
        "id_nll_1step",
        {"id_nll_1step": "lower_better"},
    )

    assert set(result) == {
        "result",
        "result_reason",
        "deltas",
        "epsilon_accept",
        "epsilon_reject",
        "epsilon_secondary",
        "failed_metric_direction",
    }
