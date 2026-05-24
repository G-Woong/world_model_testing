"""Unit tests for src/fglc/falsification/gate.py.

Verifies β_t range, boolean threshold, CUSUM monotonicity, and AUROC correctness.
"""

from __future__ import annotations

import torch
import pytest

from fglc.falsification.gate import (
    auroc_from_scores,
    beta_t_boolean,
    beta_t_continuous,
    cusum_score,
)


def test_beta_t_continuous_in_unit_interval():
    F = torch.randn(4, 10).abs()
    tau = 1.0
    beta = beta_t_continuous(F, tau)
    assert beta.shape == F.shape
    assert (beta >= 0.0).all() and (beta <= 1.0).all()


def test_beta_t_boolean_threshold():
    F = torch.tensor([0.5, 1.0, 1.5, 2.0])
    tau = 1.0
    beta = beta_t_boolean(F, tau)
    expected = torch.tensor([0.0, 0.0, 1.0, 1.0])
    assert torch.equal(beta, expected), f"expected {expected}, got {beta}"


def test_beta_t_boolean_shape():
    F = torch.randn(3, 7).abs()
    tau = 0.5
    beta = beta_t_boolean(F, tau)
    assert beta.shape == (3, 7)


def test_beta_t_continuous_increases_with_F():
    tau = 1.0
    F_lo = torch.full((1,), 0.5)
    F_hi = torch.full((1,), 2.0)
    assert beta_t_continuous(F_lo, tau) < beta_t_continuous(F_hi, tau)


def test_cusum_nonnegative():
    F = torch.randn(2, 16)
    tau = 0.0
    S = cusum_score(F, tau)
    assert (S >= 0).all(), "CUSUM must be non-negative"


def test_cusum_shape():
    B, T = 3, 12
    F = torch.randn(B, T)
    S = cusum_score(F, tau=1.0)
    assert S.shape == (B, T)


def test_cusum_monotonic_under_drift():
    """Under sustained positive drift (F_t >> τ), CUSUM should be non-decreasing."""
    B, T = 1, 20
    F = torch.full((B, T), 5.0)  # always above tau
    tau = 1.0
    S = cusum_score(F, tau)
    diffs = S[:, 1:] - S[:, :-1]
    assert (diffs >= -1e-6).all(), "CUSUM should be non-decreasing under sustained drift"


def test_auroc_perfect_separator():
    id_scores = torch.zeros(100)
    ood_scores = torch.ones(100)
    auroc = auroc_from_scores(id_scores, ood_scores)
    assert abs(auroc - 1.0) < 1e-6, f"perfect separator should yield AUROC=1, got {auroc}"


def test_auroc_random_classifier():
    torch.manual_seed(5)
    id_scores = torch.randn(500)
    ood_scores = torch.randn(500)
    auroc = auroc_from_scores(id_scores, ood_scores)
    # Random classifier: AUROC ≈ 0.5 ± 0.05
    assert abs(auroc - 0.5) < 0.07, f"random classifier AUROC should be near 0.5, got {auroc}"


def test_auroc_empty_returns_nan():
    import math
    auroc = auroc_from_scores(torch.tensor([]), torch.ones(10))
    assert math.isnan(auroc)
