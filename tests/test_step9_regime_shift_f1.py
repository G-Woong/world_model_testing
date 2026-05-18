from __future__ import annotations

from frcgw.evaluation.metrics import regime_shift_f1


def _episode(
    regimes: list[str | None],
    predicted_wrong: bool = False,
) -> dict:
    return {
        "steps": [
            {
                "eval_labels": {"true_regime": regime} if regime is not None else {},
                "predicted_wrong": predicted_wrong,
            }
            for regime in regimes
        ]
    }


def test_regime_shift_f1_empty_episodes() -> None:
    result = regime_shift_f1([])

    assert result["precision"] == 0.0
    assert result["recall"] == 0.0
    assert result["f1"] == 0.0


def test_regime_shift_f1_no_true_regime() -> None:
    result = regime_shift_f1([_episode([None, None], predicted_wrong=True)])

    assert result["precision"] == 0.0
    assert result["recall"] == 0.0
    assert result["f1"] == 0.0
    assert result["skipped_no_regime_data"] == 1.0


def test_regime_shift_f1_no_shift_no_detection() -> None:
    result = regime_shift_f1([_episode(["r0", "r0"], predicted_wrong=False)])

    assert result["false_positives"] == 0.0
    assert result["false_negatives"] == 0.0
    assert result["f1"] == 0.0


def test_regime_shift_f1_shift_detected() -> None:
    result = regime_shift_f1([_episode(["r0", "r1"], predicted_wrong=True)])

    assert result["true_positives"] == 1.0
    assert result["precision"] == 1.0
    assert result["recall"] == 1.0
    assert result["f1"] == 1.0


def test_regime_shift_f1_shift_missed() -> None:
    result = regime_shift_f1([_episode(["r0", "r1"], predicted_wrong=False)])

    assert result["false_negatives"] == 1.0
    assert result["recall"] == 0.0
    assert result["f1"] == 0.0


def test_regime_shift_f1_false_alarm() -> None:
    result = regime_shift_f1([_episode(["r0", "r0"], predicted_wrong=True)])

    assert result["false_positives"] == 1.0
    assert result["precision"] == 0.0
    assert result["f1"] == 0.0
