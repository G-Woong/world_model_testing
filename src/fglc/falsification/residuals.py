"""Standardized residual computation for R4 falsification gate.

Source: docs/idea/02_FALSIFICATION_THEORY.md §B (standardized mismatch ρ_t^k).
"""

from __future__ import annotations

import torch
from torch import Tensor


def standardized_residual(
    z_next: Tensor,
    mu: Tensor,
    log_sigma: Tensor,
    sigma_floor: float = 1e-3,
) -> Tensor:
    """Compute element-wise standardized residual ρ_t^k = (z_{t+1}^k − μ_t^k) / σ_t^k.

    Args:
        z_next, mu, log_sigma: shape (B, T, K, d)
        sigma_floor: minimum σ clamp to prevent division by near-zero

    Returns:
        rho: shape (B, T, K, d)
    """
    sigma = torch.exp(log_sigma).clamp_min(sigma_floor)
    return (z_next - mu) / sigma


def group_falsification_scores(rho: Tensor) -> Tensor:
    """Compute per-group chi-squared-like score F_t^k = ||ρ_t^k||₂².

    Args:
        rho: shape (B, T, K, d) or (N, K, d)

    Returns:
        F_per_group: shape (B, T, K) or (N, K)
    """
    return (rho ** 2).sum(dim=-1)


def total_falsification_score(F_per_group: Tensor) -> Tensor:
    """Sum group scores: F_t = Σ_k F_t^k.

    Args:
        F_per_group: shape (B, T, K) or (N, K)

    Returns:
        F_total: shape (B, T) or (N,)
    """
    return F_per_group.sum(dim=-1)


def signed_residual_mean(rho: Tensor) -> Tensor:
    """Per-group mean across latent dim d (M3 directional feature).

    Captures systematic signed bias (e.g., gain=0.7 → transitions smaller → ρ < 0).

    Args:
        rho: shape (B, T, K, d)

    Returns:
        signed_mean: shape (B, T, K)
    """
    return rho.mean(dim=-1)


def directional_bias_score(rho: Tensor, eps: float = 1e-6) -> Tensor:
    """Aggregate signed bias across groups: Σ_k |E[ρ_k]| / √(Var[ρ_k] + ε).

    Higher values indicate consistent directional drift (e.g., easy-looking OOD).

    Args:
        rho: shape (B, T, K, d)

    Returns:
        score: shape (B, T)
    """
    mean_k = rho.mean(dim=-1)                              # (B, T, K)
    var_k = rho.var(dim=-1, unbiased=False).clamp_min(eps) # (B, T, K)
    return (mean_k.abs() / var_k.sqrt()).sum(dim=-1)       # (B, T)
