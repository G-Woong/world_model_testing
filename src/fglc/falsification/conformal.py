"""Conformal calibration for R4 falsification gate threshold.

Source: docs/idea/02_FALSIFICATION_THEORY.md §C5 (conformal threshold),
        reports/R3_SMOKE_CLOSURE_REPORT.md §H.2-2.

Key contract: threshold τ is ALWAYS fit on ID calibration data only.
Passing OOD scores to fit_threshold() violates the conformal guarantee.
"""

from __future__ import annotations

import torch
from torch import Tensor


def fit_threshold(scores_id: Tensor, alpha: float = 0.05) -> float:
    """Fit conformal threshold τ = (1−α)-quantile of ID falsification scores.

    Args:
        scores_id: 1-D tensor of F_total scores on in-distribution calibration data
        alpha: target false-positive rate (e.g., 0.05 → τ at 95th percentile)

    Returns:
        tau: scalar threshold (float)
    """
    if scores_id.dim() != 1 or len(scores_id) == 0:
        raise ValueError("scores_id must be a non-empty 1-D tensor")
    return float(torch.quantile(scores_id.float(), 1.0 - alpha).item())


def fit_per_group_thresholds(F_per_group_id: Tensor, alpha: float = 0.05) -> Tensor:
    """Fit per-group conformal thresholds τ_k.

    Args:
        F_per_group_id: shape (..., K) — group scores on ID calibration data
        alpha: target FPR per group

    Returns:
        tau_per_k: shape (K,)
    """
    flat = F_per_group_id.reshape(-1, F_per_group_id.shape[-1]).float()  # (N, K)
    return torch.quantile(flat, 1.0 - alpha, dim=0)                       # (K,)


def ece(rho_id: Tensor, n_bins: int = 10) -> float:
    """Expected Calibration Error for diagonal Gaussian on ID data.

    Under a well-calibrated model, standardized residuals ρ ~ N(0, I).
    ECE measures deviation between observed empirical CDF and N(0,1) CDF.

    Source: docs/idea/02_FALSIFICATION_THEORY.md §C8 (M7 σ floor + ECE).

    Args:
        rho_id: shape (N, ...) — standardized residuals, flattened to 1-D internally
        n_bins: number of quantile bins

    Returns:
        ece_value: float ∈ [0, 1]
    """
    flat = rho_id.reshape(-1).float()
    n = len(flat)
    if n == 0:
        return float("nan")

    # Expected quantiles under N(0,1)
    probs = torch.linspace(1.0 / (2 * n_bins), 1.0 - 1.0 / (2 * n_bins), n_bins)
    import math
    expected_q = torch.tensor(
        [_ndtri(float(p)) for p in probs], dtype=torch.float32
    )

    # Observed quantiles
    observed_q = torch.quantile(flat, probs)

    # ECE = mean abs deviation of empirical CDF from N(0,1) CDF at bin boundaries
    bin_edges = torch.linspace(
        float(torch.min(flat).item()),
        float(torch.max(flat).item()),
        n_bins + 1,
    )
    ece_val = 0.0
    for i in range(n_bins):
        mask = (flat >= bin_edges[i]) & (flat < bin_edges[i + 1])
        empirical_frac = float(mask.float().mean().item())
        lo = float(bin_edges[i].item())
        hi = float(bin_edges[i + 1].item())
        expected_frac = _ndtr(hi) - _ndtr(lo)
        ece_val += abs(empirical_frac - expected_frac)
    return ece_val / n_bins


def coverage(F_total: Tensor, tau: float) -> float:
    """Fraction of steps where F_total ≤ τ (empirical coverage).

    Should be ≈ (1−α) on ID calibration data.

    Args:
        F_total: 1-D tensor of total falsification scores
        tau: conformal threshold

    Returns:
        coverage_fraction: float ∈ [0, 1]
    """
    return float((F_total <= tau).float().mean().item())


# Minimal N(0,1) CDF/quantile helpers (no scipy dependency)
def _ndtr(x: float) -> float:
    import math
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _ndtri(p: float) -> float:
    """Rational approximation of the probit function (Abramowitz & Stegun)."""
    import math
    if p <= 0.0:
        return -8.0
    if p >= 1.0:
        return 8.0
    if p < 0.5:
        return -_ndtri(1.0 - p)
    t = math.sqrt(-2.0 * math.log(1.0 - p))
    c0, c1, c2 = 2.515517, 0.802853, 0.010328
    d1, d2, d3 = 1.432788, 0.189269, 0.001308
    return t - (c0 + c1 * t + c2 * t * t) / (1.0 + d1 * t + d2 * t * t + d3 * t ** 3)
