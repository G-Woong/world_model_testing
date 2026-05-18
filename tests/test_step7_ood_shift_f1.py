"""Tests for ood_shift_f1 metric as the MET-OOD-003 STEP 7 proxy."""

from frcgw.evaluation.metrics import ood_shift_f1


def _episode(ood_type, predicted_wrongs):
    """Helper: create episode dict with given ood_type and step predictions."""
    steps = [{"predicted_wrong": pw, "eval_labels": None} for pw in predicted_wrongs]
    return {
        "eval_labels": {"ood_type": ood_type},
        "steps": steps,
        "success": False,
    }


def test_ood_shift_f1_perfect_detection():
    """Perfect detector: shift detected for all OOD, not for ID."""
    episodes = [
        _episode("OOD_grammar", [True]),
        _episode("OOD_grammar", [True]),
        _episode("ID", [False, False]),
        _episode("ID", [False]),
    ]
    result = ood_shift_f1(episodes)
    assert result["f1"] == 1.0
    assert result["true_positives"] == 2
    assert result["true_negatives"] == 2
    assert result["false_positives"] == 0
    assert result["false_negatives"] == 0


def test_ood_shift_f1_no_detection():
    """No detection: shift never detected means recall=0 and f1=0."""
    episodes = [
        _episode("OOD_grammar", [False]),
        _episode("OOD_grammar", [False]),
    ]
    result = ood_shift_f1(episodes)
    assert result["f1"] == 0.0
    assert result["false_negatives"] == 2


def test_ood_shift_f1_all_false_positives():
    """Shift detected for all ID episodes means precision=0 and f1=0."""
    episodes = [
        _episode("ID", [True]),
        _episode("ID", [True]),
    ]
    result = ood_shift_f1(episodes)
    assert result["f1"] == 0.0
    assert result["false_positives"] == 2


def test_ood_shift_f1_no_ood_type():
    """Episodes without eval_labels.ood_type are skipped."""
    episodes = [{"eval_labels": None, "steps": [{"predicted_wrong": True}]}]
    result = ood_shift_f1(episodes)
    assert result["f1"] == 0.0
    assert result["true_positives"] == 0


def test_ood_shift_f1_name_not_regime_shift():
    """Verify that both ood_shift_f1 and regime_shift_f1 are in METRIC_FUNCTIONS (STEP 9+)."""
    from frcgw.evaluation.eval_runner import METRIC_FUNCTIONS

    # STEP 9: regime_shift_f1 added as faithful C2 metric alongside ood_shift_f1 proxy.
    assert "ood_shift_f1" in METRIC_FUNCTIONS
    assert "regime_shift_f1" in METRIC_FUNCTIONS


def test_ood_shift_f1_dispatched_in_runner():
    """ood_shift_f1 must be registered in METRIC_FUNCTIONS."""
    from frcgw.evaluation.eval_runner import METRIC_FUNCTIONS

    assert "ood_shift_f1" in METRIC_FUNCTIONS
