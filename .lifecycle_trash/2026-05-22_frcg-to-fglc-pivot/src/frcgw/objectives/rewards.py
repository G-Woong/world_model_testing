"""frcgw.objectives.rewards -- Training-pathway reward components for P3.

Source MD: paper_context_ref/08_LOSS_REWARD_TRAINING_OBJECTIVE.md R-001, R-003, R-004, R-008
"""
from __future__ import annotations

import torch
from torch import Tensor


def R_progress(progress_delta: float | Tensor) -> float | Tensor:
    if isinstance(progress_delta, Tensor):
        return torch.clamp(progress_delta, 0.0, 1.0)
    return max(0.0, min(float(progress_delta), 1.0))


def R_failed_action_penalty(failed_action: bool | Tensor) -> float | Tensor:
    if isinstance(failed_action, Tensor):
        return failed_action.to(dtype=torch.float32) * -0.3
    return -0.3 if failed_action else 0.0


def R_repeated_failure_penalty(n_consecutive_failures: int) -> float:
    return -0.1 * int(n_consecutive_failures)


def R_compute_cost(n_alt_candidates: int, H: int, beta: float = 0.1) -> float:
    return float(beta) * int(n_alt_candidates) * int(H)
