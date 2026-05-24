"""Unit tests for src/fglc/falsification/residuals.py.

Verifies shape, finiteness, sigma_floor, and score additivity.
"""

from __future__ import annotations

import torch
import pytest

from fglc.falsification.residuals import (
    directional_bias_score,
    group_falsification_scores,
    signed_residual_mean,
    standardized_residual,
    total_falsification_score,
)


B, T, K, d = 4, 8, 6, 32


@pytest.fixture()
def rho_sample():
    torch.manual_seed(0)
    z_next = torch.randn(B, T, K, d)
    mu = torch.randn(B, T, K, d)
    log_sigma = torch.zeros(B, T, K, d)  # σ=1
    return standardized_residual(z_next, mu, log_sigma)


def test_standardized_residual_shape(rho_sample):
    assert rho_sample.shape == (B, T, K, d)


def test_standardized_residual_finite(rho_sample):
    assert torch.isfinite(rho_sample).all(), "rho contains NaN or Inf"


def test_sigma_floor_applied():
    z_next = torch.ones(2, 4, 3, 8)
    mu = torch.zeros(2, 4, 3, 8)
    log_sigma = torch.full((2, 4, 3, 8), -100.0)  # σ ~ 0
    rho = standardized_residual(z_next, mu, log_sigma, sigma_floor=1e-3)
    assert torch.isfinite(rho).all(), "sigma_floor should prevent inf/nan"
    # With sigma_floor=1e-3, max rho magnitude should be 1/1e-3 = 1000
    assert float(rho.abs().max()) <= 1001.0


def test_group_score_sum_equals_total(rho_sample):
    F_k = group_falsification_scores(rho_sample)        # (B, T, K)
    F_tot_from_sum = F_k.sum(dim=-1)                    # (B, T)
    F_tot = total_falsification_score(F_k)               # (B, T)
    assert torch.allclose(F_tot_from_sum, F_tot), "total_falsification_score must equal Σ_k F^k"


def test_group_scores_nonnegative(rho_sample):
    F_k = group_falsification_scores(rho_sample)
    assert (F_k >= 0).all(), "group scores must be non-negative (||ρ||²)"


def test_signed_residual_mean_shape(rho_sample):
    sr = signed_residual_mean(rho_sample)
    assert sr.shape == (B, T, K)


def test_directional_bias_score_shape(rho_sample):
    dbs = directional_bias_score(rho_sample)
    assert dbs.shape == (B, T)


def test_directional_bias_score_positive(rho_sample):
    dbs = directional_bias_score(rho_sample)
    assert (dbs >= 0).all(), "directional bias score must be non-negative"
