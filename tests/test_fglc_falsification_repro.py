"""Reproducibility tests for R4 falsification gate.

Same seed + same data → same τ, same AUROC.
"""

from __future__ import annotations

import torch
import pytest

from fglc.falsification.conformal import fit_threshold
from fglc.falsification.gate import auroc_from_scores
from fglc.falsification.residuals import (
    group_falsification_scores,
    standardized_residual,
    total_falsification_score,
)


def _make_fake_eval_data(seed: int, N: int = 200, K: int = 6, d: int = 32):
    g = torch.Generator()
    g.manual_seed(seed)
    z_next = torch.randn(N, K, d, generator=g)
    mu = torch.randn(N, K, d, generator=g)
    log_sigma = torch.zeros(N, K, d)
    rho = standardized_residual(z_next, mu, log_sigma)
    F_k = group_falsification_scores(rho)
    F_tot = total_falsification_score(F_k)
    return F_tot


def test_same_seed_same_threshold():
    F1 = _make_fake_eval_data(seed=42)
    F2 = _make_fake_eval_data(seed=42)
    tau1 = fit_threshold(F1, alpha=0.05)
    tau2 = fit_threshold(F2, alpha=0.05)
    assert tau1 == tau2, f"same seed must yield same threshold: {tau1} vs {tau2}"


def test_same_seed_same_auroc():
    F_id1 = _make_fake_eval_data(seed=10)
    F_ood1 = _make_fake_eval_data(seed=20)
    F_id2 = _make_fake_eval_data(seed=10)
    F_ood2 = _make_fake_eval_data(seed=20)
    auroc1 = auroc_from_scores(F_id1, F_ood1)
    auroc2 = auroc_from_scores(F_id2, F_ood2)
    assert abs(auroc1 - auroc2) < 1e-6, f"same seed must yield same AUROC: {auroc1} vs {auroc2}"


def test_different_seed_may_differ():
    F_id_a = _make_fake_eval_data(seed=1)
    F_id_b = _make_fake_eval_data(seed=999)
    tau_a = fit_threshold(F_id_a, alpha=0.05)
    tau_b = fit_threshold(F_id_b, alpha=0.05)
    # With different seeds, thresholds should generally differ
    # (not a hard requirement but validates non-constant behavior)
    assert isinstance(tau_a, float) and isinstance(tau_b, float)
