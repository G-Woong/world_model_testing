"""FRCG-WM calibration utilities. C5 ECE (MET-CAL-001).

Source MD: paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md MET-CAL-001
Source MD: paper_context_ref/08_LOSS_REWARD_TRAINING_OBJECTIVE.md C5 calibration
"""

from __future__ import annotations

MIN_UNIQUE_WRONG_PROB = 3
BLOCKED_DEGENERATE_PREDICTOR = "BLOCKED_DEGENERATE_PREDICTOR"
BLOCKED_C3_STATUSES = {"BLOCKED", "PIVOT_REQUIRED"}


def temperature_scale_probs(probs: list[float], temperature: float) -> list[float]:
    """Apply temperature scaling to predicted probabilities.

    temperature > 1 softens; < 1 sharpens.
    """
    if temperature <= 0:
        raise ValueError("temperature must be positive")
    if not probs:
        return []
    if any(prob < 0.0 or prob > 1.0 for prob in probs):
        raise ValueError("probs must be in [0, 1]")

    exponent = 1.0 / temperature
    scaled_weights = [prob**exponent for prob in probs]
    total = sum(scaled_weights)
    if total <= 0.0:
        raise ValueError("at least one probability must be positive")
    return [weight / total for weight in scaled_weights]


def compute_ece_if_valid(
    wrong_probs: list[float],
    true_wrong: list[bool],
    n_bins: int = 10,
) -> dict:
    """Compute ECE with BLOCKED_DEGENERATE_PREDICTOR guard.

    Returns dict with keys: status, ece, unique_count, n_bins, message.
    status: 'BLOCKED_DEGENERATE_PREDICTOR' | 'OK' | 'INSUFFICIENT_DATA'
    """
    if n_bins <= 0:
        raise ValueError("n_bins must be positive")
    if len(wrong_probs) != len(true_wrong):
        raise ValueError("wrong_probs and true_wrong must have the same length")
    if any(prob < 0.0 or prob > 1.0 for prob in wrong_probs):
        raise ValueError("wrong_probs must be in [0, 1]")

    unique_count = len(set(wrong_probs))
    if unique_count <= 2:
        return {
            "status": BLOCKED_DEGENERATE_PREDICTOR,
            "ece": None,
            "unique_count": unique_count,
            "n_bins": n_bins,
            "message": (
                f"unique wrong_prob values={unique_count}; "
                f"minimum required={MIN_UNIQUE_WRONG_PROB}"
            ),
        }

    if len(wrong_probs) < 10:
        return {
            "status": "INSUFFICIENT_DATA",
            "ece": None,
            "unique_count": unique_count,
            "n_bins": n_bins,
            "message": "minimum required examples=10",
        }

    examples = [
        (float(wrong_prob), 1.0 if bool(actual_wrong) else 0.0)
        for wrong_prob, actual_wrong in zip(wrong_probs, true_wrong, strict=True)
    ]
    total = len(examples)
    ece = 0.0
    for bin_index in range(n_bins):
        lower = bin_index / n_bins
        upper = (bin_index + 1) / n_bins
        if bin_index == n_bins - 1:
            bin_examples = [
                (pred, actual) for pred, actual in examples if lower <= pred <= upper
            ]
        else:
            bin_examples = [
                (pred, actual) for pred, actual in examples if lower <= pred < upper
            ]
        if not bin_examples:
            continue
        mean_pred = sum(pred for pred, _ in bin_examples) / len(bin_examples)
        mean_actual = sum(actual for _, actual in bin_examples) / len(bin_examples)
        ece += (len(bin_examples) / total) * abs(mean_pred - mean_actual)

    return {
        "status": "OK",
        "ece": float(ece),
        "unique_count": unique_count,
        "n_bins": n_bins,
        "message": "",
    }


def check_c3_nondegenerate(c3_status: str) -> bool:
    """Return True only if C3 is non-degenerate (i.e., ECE computation is permitted).

    C3 status must be READY_CANDIDATE or PRELIMINARY_PLUS to unlock C5 ECE.
    """
    return c3_status not in BLOCKED_C3_STATUSES
