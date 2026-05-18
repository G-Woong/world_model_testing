from __future__ import annotations

from frcgw.evaluation import metrics


def test_regime_shift_f1_function_exists() -> None:
    # STEP 9: regime_shift_f1 added (was blocked until true_regime in EvaluationLabels).
    assert hasattr(metrics, "regime_shift_f1"), "regime_shift_f1 must exist in STEP 9+"


def test_ood_shift_f1_exists() -> None:
    assert hasattr(metrics, "ood_shift_f1")
