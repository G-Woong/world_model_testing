"""R4 falsification gate: β_t continuous/boolean + CUSUM + AUROC.

Source: docs/idea/02_FALSIFICATION_THEORY.md §B-C,
        reports/R3_SMOKE_CLOSURE_REPORT.md §H.2-3 (M4 sequential aggregation).

R4 uses conformal-only β_t (no MLP). MLP β_t training is deferred to R5+
to respect Stage 2 freeze policy (docs/idea/12_TRAINING_STAGES.md).
"""

from __future__ import annotations

import torch
from torch import Tensor


def beta_t_continuous(F_total: Tensor, tau: float) -> Tensor:
    """Soft falsification gate: β_t = sigmoid((F_t − τ) / s), s = τ/4.

    Args:
        F_total: shape (B, T) or (N,) — total falsification score
        tau: conformal threshold

    Returns:
        beta: same shape as F_total, values in (0, 1)
    """
    s = max(tau / 4.0, 1e-6)
    return torch.sigmoid((F_total - tau) / s)


def beta_t_boolean(F_total: Tensor, tau: float) -> Tensor:
    """Hard falsification gate: β_t = 1 if F_t > τ, else 0.

    Args:
        F_total: shape (B, T) or (N,)
        tau: conformal threshold

    Returns:
        beta: float tensor with values in {0.0, 1.0}
    """
    return (F_total > tau).float()


def cusum_score(F_t_seq: Tensor, tau: float, window: int = 8) -> Tensor:
    """CUSUM-like sequential aggregation: S_t = max(0, S_{t-1} + (F_t − τ)).

    Captures sustained falsification events over time (M4 sequential aggregation).

    Source: reports/R3_SMOKE_CLOSURE_REPORT.md §H.2-3.

    Args:
        F_t_seq: shape (B, T) — sequence of total falsification scores
        tau: conformal threshold (excess = F_t - tau)
        window: not currently used (CUSUM is unbounded by default); kept for API

    Returns:
        S: shape (B, T) — non-negative CUSUM accumulator
    """
    del window  # unbounded CUSUM; window-bounded variant deferred to R5
    B, T = F_t_seq.shape
    excess = F_t_seq - tau                         # (B, T)
    S = torch.zeros_like(excess)
    S[:, 0] = excess[:, 0].clamp_min(0.0)
    for t in range(1, T):
        S[:, t] = (S[:, t - 1] + excess[:, t]).clamp_min(0.0)
    return S


def auroc_from_scores(
    scores_id: Tensor,
    scores_ood: Tensor,
) -> float:
    """Compute AUROC for OOD detection without sklearn.

    Convention: higher score = more likely OOD.
    ID = label 0, OOD = label 1.

    Args:
        scores_id:  1-D tensor of falsification scores on ID data
        scores_ood: 1-D tensor of falsification scores on OOD data

    Returns:
        auroc: float ∈ [0, 1]
    """
    n_id = len(scores_id)
    n_ood = len(scores_ood)
    if n_id == 0 or n_ood == 0:
        return float("nan")

    # Mann-Whitney U statistic: P(score_ood > score_id)
    # Equivalent to AUROC via the Wilcoxon rank-sum interpretation.
    all_scores = torch.cat([scores_id.float(), scores_ood.float()])
    labels = torch.cat([
        torch.zeros(n_id, dtype=torch.float32),
        torch.ones(n_ood, dtype=torch.float32),
    ])
    order = torch.argsort(all_scores)
    sorted_labels = labels[order]

    # AUROC = (sum of ranks of OOD among all - n_ood*(n_ood+1)/2) / (n_id * n_ood)
    ranks = torch.arange(1, len(all_scores) + 1, dtype=torch.float32)
    rank_sum_ood = float((ranks * sorted_labels).sum().item())
    auroc = (rank_sum_ood - n_ood * (n_ood + 1) / 2.0) / (n_id * n_ood)
    return float(auroc)
