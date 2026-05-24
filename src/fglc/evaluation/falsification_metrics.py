"""R4 falsification gate metric aggregator.

Source: docs/idea/02_FALSIFICATION_THEORY.md §B-C,
        reports/R3_SMOKE_CLOSURE_REPORT.md §H.3 (PASS gate thresholds).

Computes STAGE2_CANONICAL_METRIC_KEYS from per-split residual tensors.
Contract: conformal threshold τ is ALWAYS fit on calibration_split only.
"""

from __future__ import annotations

from typing import Mapping

import torch
from torch import Tensor

from fglc.evaluation.metrics import STAGE2_CANONICAL_METRIC_KEYS
from fglc.falsification.conformal import coverage, ece, fit_threshold
from fglc.falsification.gate import auroc_from_scores, beta_t_boolean


def compute_r4_metrics(
    eval_data: Mapping[str, Mapping[str, Tensor]],
    calibration_split: str = "test_id",
    alpha: float = 0.05,
    use_signed_bias: bool = False,
) -> dict[str, float]:
    """Compute all STAGE2_CANONICAL_METRIC_KEYS from per-split residual dicts.

    Args:
        eval_data: split_name → {rho_per_group, F_per_group, F_total, raw_nll_step}
                   Keys must include calibration_split, "ood_friction", "ood_gain".
                   "ood_mass" is optional.
        calibration_split: split used to fit τ and FPR (must be ID data).
        alpha: conformal FPR target (default 0.05).
        use_signed_bias: if True, use directional_bias_step instead of F_total for AUROC.
            Recommended for easy-looking OOD (magnitude-reducing physics shifts).
            Source: reports/R3_SMOKE_CLOSURE_REPORT.md §H.2-1.

    Returns:
        metrics dict matching STAGE2_CANONICAL_METRIC_KEYS.
    """
    if calibration_split not in eval_data:
        raise ValueError(
            f"calibration_split {calibration_split!r} not found in eval_data keys: "
            f"{sorted(eval_data.keys())}"
        )

    cal = eval_data[calibration_split]
    F_id: Tensor = cal["F_total"]
    rho_id: Tensor = cal["rho_per_group"]
    nll_id: Tensor = cal["raw_nll_step"]

    # Optional: use directional bias score as detection score (repair: EASY_LOOKING_OOD_MISSED)
    if use_signed_bias and "directional_bias_step" in cal:
        detection_id = cal["directional_bias_step"]
    else:
        detection_id = F_id

    # 1. Fit conformal threshold from ID calibration data only
    # Threshold is always on F_total (conformal guarantee is for F_total)
    tau = fit_threshold(F_id, alpha=alpha)

    # 2. ECE on ID calibration data
    residual_ece_val = ece(rho_id, n_bins=10)

    # 3. FPR on calibration split (should be ≈ α)
    fpr_id = 1.0 - coverage(F_id, tau)

    # 4. Per-OOD-axis AUROC and TPR
    friction_metrics = _axis_metrics(
        eval_data, "ood_friction", tau, detection_id, nll_id, F_id_for_tpr=F_id,
        use_signed_bias=use_signed_bias,
    )
    gain_metrics = _axis_metrics(
        eval_data, "ood_gain", tau, detection_id, nll_id, F_id_for_tpr=F_id,
        use_signed_bias=use_signed_bias,
    )

    result: dict[str, float] = {
        "conformal_threshold": float(tau),
        "residual_ece": float(residual_ece_val),
        "beta_t_fpr_id": float(fpr_id),
        "beta_t_auroc_friction": friction_metrics["auroc"],
        "beta_t_tpr_friction": friction_metrics["tpr"],
        "raw_nll_auroc_friction": friction_metrics["raw_nll_auroc"],
        "beta_t_auroc_gain": gain_metrics["auroc"],
        "beta_t_tpr_gain": gain_metrics["tpr"],
        "raw_nll_auroc_gain": gain_metrics["raw_nll_auroc"],
    }

    assert STAGE2_CANONICAL_METRIC_KEYS <= result.keys(), (
        f"Missing R4 metric keys: {STAGE2_CANONICAL_METRIC_KEYS - result.keys()}"
    )
    return result


def _axis_metrics(
    eval_data: Mapping[str, Mapping[str, Tensor]],
    ood_split: str,
    tau: float,
    detection_id: Tensor,
    nll_id: Tensor,
    F_id_for_tpr: Tensor | None = None,
    use_signed_bias: bool = False,
) -> dict[str, float]:
    """Compute AUROC, TPR, raw_nll_auroc for one OOD axis.

    When use_signed_bias=True, uses directional_bias_step for AUROC
    (detection_id should already be directional_bias_step from caller).
    """
    if ood_split not in eval_data:
        return {"auroc": float("nan"), "tpr": float("nan"), "raw_nll_auroc": float("nan")}

    ood = eval_data[ood_split]
    F_ood: Tensor = ood["F_total"]
    nll_ood: Tensor = ood["raw_nll_step"]

    from fglc.falsification.gate import auroc_from_scores, beta_t_boolean

    # Detection score for AUROC
    if use_signed_bias and "directional_bias_step" in ood:
        detection_ood = ood["directional_bias_step"]
    else:
        detection_ood = F_ood

    # β_t AUROC using selected detection score
    auroc = auroc_from_scores(detection_id, detection_ood)

    # TPR at conformal threshold — always uses F_total (conformal coverage)
    f_id_tpr = F_id_for_tpr if F_id_for_tpr is not None else detection_id
    tau_for_tpr = tau  # conformal threshold was fit on F_total
    beta_ood = beta_t_boolean(F_ood, tau_for_tpr)
    tpr = float(beta_ood.mean().item())

    # raw NLL AUROC (baseline)
    raw_nll_auroc = auroc_from_scores(nll_id, nll_ood)

    return {"auroc": float(auroc), "tpr": float(tpr), "raw_nll_auroc": float(raw_nll_auroc)}
