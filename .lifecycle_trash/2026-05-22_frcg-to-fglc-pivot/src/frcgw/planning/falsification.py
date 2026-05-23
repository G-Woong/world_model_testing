"""frcgw.planning.falsification -- Falsification scorer F_t (FALS-02).

Source MD: paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md FALS-02
"""
from __future__ import annotations

from dataclasses import dataclass

import torch
from torch import Tensor
import torch.nn.functional as F

from frcgw.models.text_frcg_model import TextFRCGModel
from frcgw.models.world_model_heads import RolloutResult


@dataclass(frozen=True)
class FalsificationEvidence:
    observed_effect_type: int
    observed_progress_delta: float
    observed_failed_action: bool


def log_likelihood(
    rollout_result: RolloutResult,
    evidence: FalsificationEvidence,
    lambda_p: float = 0.5,
    lambda_f: float = 0.5,
) -> Tensor:
    """Compute ell_t(h) = log p(e_t | h).

    Source MD: paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md FALS-02
    """
    log_p_eff = F.log_softmax(rollout_result.effect_logits, dim=-1)[..., evidence.observed_effect_type]
    progress_delta = torch.as_tensor(
        evidence.observed_progress_delta,
        dtype=rollout_result.progress_pred.dtype,
        device=rollout_result.progress_pred.device,
    )
    log_p_prog = -0.5 * (rollout_result.progress_pred - progress_delta).pow(2)
    if evidence.observed_failed_action:
        log_p_fail = torch.log(rollout_result.failed_score.clamp_min(1.0e-8))
    else:
        log_p_fail = torch.log((1.0 - rollout_result.failed_score).clamp_min(1.0e-8))
    ell = log_p_eff + lambda_p * log_p_prog + lambda_f * log_p_fail
    return ell.squeeze() if ell.numel() == 1 else ell


def falsification_score(
    model: TextFRCGModel,
    shared_h: Tensor,
    z_state: Tensor,
    action_type: str,
    h_exec_id: int,
    alt_hypothesis_ids: list[int],
    evidence: FalsificationEvidence,
    lambda_p: float = 0.5,
    lambda_f: float = 0.5,
) -> Tensor:
    """Compute F_t = max(ell_alts) - ell_exec.

    Source MD: paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md FALS-02
    """
    # 0=no_state_change (unintended no-change); 6=no_op_valid (deliberate no-op).
    # Falsifying on zero-effect evidence is ill-posed — short-circuit is intentional.
    if evidence.observed_effect_type in {0, 6}:
        return torch.zeros((), dtype=shared_h.dtype, device=shared_h.device)

    exec_rollout = model.world_model_heads.forward_given_action(shared_h, z_state, action_type, h_exec_id)
    ell_exec = log_likelihood(exec_rollout, evidence, lambda_p, lambda_f)
    if not alt_hypothesis_ids:
        return torch.zeros_like(ell_exec.squeeze() if ell_exec.numel() == 1 else ell_exec)

    ell_alts = [
        log_likelihood(
            model.world_model_heads.forward_given_action(shared_h, z_state, action_type, hid),
            evidence,
            lambda_p,
            lambda_f,
        )
        for hid in alt_hypothesis_ids
    ]
    ell_max_alt = torch.stack([ell.squeeze() if ell.numel() == 1 else ell for ell in ell_alts]).max()
    score = ell_max_alt - (ell_exec.squeeze() if ell_exec.numel() == 1 else ell_exec).max()
    return score.squeeze()
