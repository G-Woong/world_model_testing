from __future__ import annotations

from frcgw.evaluation import metrics


def test_no_regime_shift_f1_function() -> None:
    assert not hasattr(metrics, "regime_shift_f1")
    assert not hasattr(metrics, "compute_regime_shift_f1")


def test_ood_shift_f1_exists() -> None:
    assert hasattr(metrics, "ood_shift_f1")
