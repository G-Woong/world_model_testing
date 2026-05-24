"""Unit tests for src/fglc/falsification/conformal.py.

Verifies threshold fitting, coverage, and ECE.
"""

from __future__ import annotations

import math

import torch
import pytest

from fglc.falsification.conformal import coverage, ece, fit_per_group_thresholds, fit_threshold


def test_fit_threshold_returns_scalar():
    scores = torch.randn(200).abs()
    tau = fit_threshold(scores, alpha=0.05)
    assert isinstance(tau, float)
    assert math.isfinite(tau)


def test_fit_threshold_quantile_property():
    """On ID data, fraction of F_total ≤ τ should be ≈ 1-alpha."""
    torch.manual_seed(42)
    scores_id = torch.randn(1000).abs() ** 2  # chi-squared-like
    alpha = 0.05
    tau = fit_threshold(scores_id, alpha=alpha)
    emp_cov = coverage(scores_id, tau)
    # Allow ±0.03 tolerance around (1-alpha)=0.95
    assert abs(emp_cov - (1.0 - alpha)) < 0.03, (
        f"expected coverage ≈ {1-alpha:.2f}, got {emp_cov:.4f}"
    )


def test_fit_threshold_empty_raises():
    with pytest.raises(ValueError):
        fit_threshold(torch.tensor([]), alpha=0.05)


def test_fit_threshold_1d_required():
    with pytest.raises(ValueError):
        fit_threshold(torch.randn(10, 5), alpha=0.05)


def test_fit_per_group_thresholds_shape():
    K = 6
    F_per_group = torch.randn(200, 8, K).abs() ** 2
    tau_k = fit_per_group_thresholds(F_per_group, alpha=0.05)
    assert tau_k.shape == (K,)


def test_coverage_id_data():
    torch.manual_seed(0)
    scores = torch.rand(500)
    tau = 0.9
    cov = coverage(scores, tau)
    # scores ∈ [0,1] uniform → coverage(τ=0.9) ≈ 0.9
    assert abs(cov - 0.9) < 0.05


def test_ece_calibrated_model():
    """Well-calibrated model (z_next ~ N(μ, σ²)) should yield ECE ≈ 0."""
    torch.manual_seed(1)
    # Simulate perfectly calibrated residuals ρ ~ N(0,1)
    rho_id = torch.randn(5000, 6, 32)
    ece_val = ece(rho_id, n_bins=10)
    assert math.isfinite(ece_val)
    assert ece_val < 0.10, f"ECE for N(0,1) residuals should be small, got {ece_val:.4f}"
