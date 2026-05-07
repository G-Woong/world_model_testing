"""WM loss component 정의 + total loss 조합 함수.

본 모듈은 *loss 함수* 만 제공한다. training step / optimizer.step()은 만들지 않는다
(Session 9). 본 모듈의 함수는 dict-in / dict-out 인터페이스를 따르며, key contract는
``heads.RSSMWorldModel.forward``의 output dict와 일치한다.

Loss decomposition (PART2 §3.12 reward decomposition + Dreamer KL + WM heads):

    L_total =
        λ_obs_local    * L_obs_local
      + λ_obs_scalar   * L_obs_scalar
      + λ_reward       * L_reward
      + λ_done         * L_done
      + λ_state        * L_state
      + λ_regime       * L_regime
      + λ_change_point * L_change_point
      + λ_reveal       * L_reveal
      + λ_shift        * L_shift
      + λ_mismatch     * L_mismatch
      + β_kl           * L_KL

change-point / shift binary head는 tick-level positive가 매우 희소하므로
``pos_weight``와 (옵션) ``focal loss``를 지원한다. 학습 sampler 단의 event-window
sampling은 Session 8에서 추가된다.

본 모듈은 ``forward output dict``와 ``target dict``의 key 이름이 다음과 같다고 가정한다:

forward (예측):
    obs_local_pred / obs_scalar_pred
    reward_pred
    done_logit
    state_pred
    regime_logits
    change_point_logit / reveal_logit / shift_logit
    raw_eff_mismatch_logit
    prior_mean / prior_std / post_mean / post_std

target (정답; Session 8 loader가 dataset npz에서 만들어 줌):
    obs_local_target / obs_scalar_target
    reward
    done                                    # (terminated || truncated) bool/float
    true_state                              # (B, T, 5)
    true_regime_control_mode                # (B, T) long
    change_point / reveal_event / shift_event   # (B, T) bool/float
    raw_eff_mismatch                         # (B, T) bool/float (= action_raw != action_effective)

추가:
    sample_weight (B, T) float 또는 None — event-window sampling weight 또는 padding mask.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Mapping, Optional

import torch
from torch import Tensor
from torch.nn import functional as F

from .config import LossConfig


# =============================================================================
# 1. dataclass: 모든 loss component를 분해해 보고/디버깅한다
# =============================================================================


@dataclass
class WMLossOutput:
    """compute_total_loss의 반환. 각 component는 scalar tensor (이미 평균/가중)."""

    total: Tensor
    components: Dict[str, Tensor] = field(default_factory=dict)
    # diagnostics: gradient에 들어가지 않는 부수 metric (예: KL raw, calibration metric).
    diagnostics: Dict[str, Tensor] = field(default_factory=dict)


# =============================================================================
# 2. 개별 loss 함수
# =============================================================================


def masked_mean(x: Tensor, mask: Optional[Tensor] = None) -> Tensor:
    """``x``의 평균. mask가 있으면 ``(x * mask).sum() / mask.sum().clamp_min(1.0)``."""
    if mask is None:
        return x.mean()
    return (x * mask).sum() / mask.sum().clamp_min(1.0)


def mse_loss(pred: Tensor, target: Tensor, mask: Optional[Tensor] = None) -> Tensor:
    """element-wise MSE. mask는 (B, T) 또는 broadcastable shape."""
    err = (pred - target) ** 2
    while err.dim() > (mask.dim() if mask is not None else err.dim()):
        err = err.mean(-1)
    return masked_mean(err, mask)


def bce_with_logits_loss(
    logit: Tensor,
    target: Tensor,
    *,
    pos_weight: float = 1.0,
    use_focal: bool = False,
    focal_gamma: float = 2.0,
    mask: Optional[Tensor] = None,
) -> Tensor:
    """binary cross-entropy with optional pos_weight + focal modulation.

    - logit, target: (B, T)
    - pos_weight: 양성 클래스 가중치. tick-level 희소 event(change_point/shift)에 사용.
    - use_focal: True이면 ``(1 - p_t)^γ * BCE``로 modulation (focal loss).
    """
    target = target.to(dtype=logit.dtype)
    pw = torch.tensor([float(pos_weight)], device=logit.device, dtype=logit.dtype)
    bce = F.binary_cross_entropy_with_logits(
        logit, target, pos_weight=pw, reduction="none",
    )
    if use_focal:
        # p_t = target * sigmoid(logit) + (1-target) * (1 - sigmoid(logit))
        prob = torch.sigmoid(logit)
        p_t = target * prob + (1.0 - target) * (1.0 - prob)
        bce = bce * (1.0 - p_t).clamp_min(1e-6).pow(focal_gamma)
    return masked_mean(bce, mask)


def categorical_ce_loss(
    logits: Tensor,
    target: Tensor,
    mask: Optional[Tensor] = None,
) -> Tensor:
    """multi-class cross-entropy.

    logits : (B, T, R)
    target : (B, T) long
    mask   : (B, T) float or None
    """
    B, T, R = logits.shape
    flat_logits = logits.reshape(B * T, R)
    flat_target = target.reshape(B * T).long()
    ce = F.cross_entropy(flat_logits, flat_target, reduction="none")  # (B*T,)
    ce = ce.reshape(B, T)
    return masked_mean(ce, mask)


def kl_divergence_diag_normal(
    p_mean: Tensor, p_std: Tensor, q_mean: Tensor, q_std: Tensor,
) -> Tensor:
    """KL(N(q_mean, q_std) || N(p_mean, p_std)) — 대각 가우시안.

    Dreamer-style: posterior=q, prior=p로 두고 KL(q || p)을 계산.
    Returns: same shape as q_mean (per-element).
    """
    # 표준 closed-form: KL = log(p/q) + (q^2 + (μq - μp)^2)/(2 p^2) - 0.5
    var_q = q_std.pow(2)
    var_p = p_std.pow(2)
    return (
        torch.log(p_std / q_std.clamp_min(1e-8))
        + (var_q + (q_mean - p_mean).pow(2)) / (2.0 * var_p.clamp_min(1e-8))
        - 0.5
    )


def kl_loss_dreamer(
    prior_mean: Tensor, prior_std: Tensor,
    post_mean: Tensor, post_std: Tensor,
    *,
    free_nats: float = 1.0,
    kl_balance: float = 0.8,
    mask: Optional[Tensor] = None,
) -> Tensor:
    """Dreamer-style KL with free nats + KL balancing.

    KL balancing (DreamerV2/V3): prior와 posterior 양쪽의 gradient 비율을 비대칭으로 두어
    posterior(q)가 prior에 더 빨리 끌려가는 collapse를 막는다.

    Total KL =
        kl_balance * KL(stop_grad(q) || p) + (1 - kl_balance) * KL(q || stop_grad(p))

    free_nats: KL을 free_nats 이하로 떨어뜨리지 않도록 element-wise clamp.
    """
    q_mean_sg = post_mean.detach()
    q_std_sg = post_std.detach()
    p_mean_sg = prior_mean.detach()
    p_std_sg = prior_std.detach()
    # forward direction(prior 측 gradient)
    kl_prior_side = kl_divergence_diag_normal(prior_mean, prior_std, q_mean_sg, q_std_sg)
    # representation direction(posterior 측 gradient)
    kl_post_side = kl_divergence_diag_normal(p_mean_sg, p_std_sg, post_mean, post_std)
    # element-wise free nats clamp on per-step KL sum-over-dim
    kl_prior_step = kl_prior_side.sum(dim=-1).clamp_min(free_nats)
    kl_post_step = kl_post_side.sum(dim=-1).clamp_min(free_nats)
    # KL balancing 결합
    kl_per_step = kl_balance * kl_prior_step + (1.0 - kl_balance) * kl_post_step
    return masked_mean(kl_per_step, mask)


# =============================================================================
# 3. total loss 조합
# =============================================================================


def compute_total_loss(
    forward_out: Mapping[str, Tensor],
    target: Mapping[str, Tensor],
    cfg: LossConfig,
    *,
    sample_weight: Optional[Tensor] = None,
) -> WMLossOutput:
    """모든 ON head의 loss를 계산하고 가중합한다.

    Parameters
    ----------
    forward_out : RSSMWorldModel.forward의 output dict
    target      : Session 8 loader가 만든 target dict
    cfg         : LossConfig
    sample_weight : (B, T) float, optional. event-window sampling 또는 padding mask.

    Returns
    -------
    WMLossOutput. total은 학습 backprop에 그대로 사용. components는 logging용 분해 항목.

    Notes
    -----
    - head가 forward_out에 없으면 해당 component는 0으로 처리하고 compute에서 skip.
    - target에 누락된 key가 있으면 해당 component는 자동 skip하고 diagnostics에 기록.
    """
    components: Dict[str, Tensor] = {}
    diagnostics: Dict[str, Tensor] = {}
    device = _pick_device(forward_out)

    def _scalar(v: float) -> Tensor:
        return torch.tensor(float(v), device=device)

    total = torch.zeros((), device=device)

    # -------- observation reconstruction --------
    if "obs_local_pred" in forward_out and "obs_local_target" in target:
        loss = mse_loss(forward_out["obs_local_pred"], target["obs_local_target"], sample_weight)
        components["obs_local"] = loss
        total = total + cfg.lambda_obs_local * loss

    if "obs_scalar_pred" in forward_out and "obs_scalar_target" in target:
        loss = mse_loss(forward_out["obs_scalar_pred"], target["obs_scalar_target"], sample_weight)
        components["obs_scalar"] = loss
        total = total + cfg.lambda_obs_scalar * loss

    # -------- reward / done --------
    if "reward_pred" in forward_out and "reward" in target:
        loss = mse_loss(forward_out["reward_pred"], target["reward"], sample_weight)
        components["reward"] = loss
        total = total + cfg.lambda_reward * loss

    if "done_logit" in forward_out and "done" in target:
        # NOTE: target["done"]은 trainer._prepare_targets에서 done_target_mode에 따라
        # success_done(default) 또는 terminal로 미리 dispatch되어 들어온다 (Session 9 PATCH).
        # 본 함수는 target["done"]을 그대로 신뢰한다 — silent fallback 없음.
        loss = bce_with_logits_loss(
            forward_out["done_logit"], target["done"], mask=sample_weight,
        )
        components["done"] = loss
        total = total + cfg.lambda_done * loss

    # -------- state vector regression --------
    if "state_pred" in forward_out and "true_state" in target:
        loss = mse_loss(forward_out["state_pred"], target["true_state"], sample_weight)
        components["state"] = loss
        total = total + cfg.lambda_state * loss

    # -------- regime (control_mode 5-class CE) --------
    if "regime_logits" in forward_out and "true_regime_control_mode" in target:
        loss = categorical_ce_loss(
            forward_out["regime_logits"], target["true_regime_control_mode"], sample_weight,
        )
        components["regime"] = loss
        total = total + cfg.lambda_regime * loss

    # -------- change-point (희소 event; pos_weight + (optional) focal) --------
    if "change_point_logit" in forward_out and "change_point" in target:
        loss = bce_with_logits_loss(
            forward_out["change_point_logit"],
            target["change_point"],
            pos_weight=cfg.cp_pos_weight,
            use_focal=cfg.cp_use_focal,
            focal_gamma=cfg.cp_focal_gamma,
            mask=sample_weight,
        )
        components["change_point"] = loss
        total = total + cfg.lambda_change_point * loss

    # -------- reveal (event-rich; 별도 weighting 없음) --------
    if "reveal_logit" in forward_out and "reveal_event" in target:
        loss = bce_with_logits_loss(
            forward_out["reveal_logit"],
            target["reveal_event"],
            pos_weight=cfg.reveal_pos_weight,
            mask=sample_weight,
        )
        components["reveal"] = loss
        total = total + cfg.lambda_reveal * loss

    # -------- shift (희소 event; pos_weight) --------
    if "shift_logit" in forward_out and "shift_event" in target:
        loss = bce_with_logits_loss(
            forward_out["shift_logit"],
            target["shift_event"],
            pos_weight=cfg.shift_pos_weight,
            use_focal=cfg.cp_use_focal,
            focal_gamma=cfg.cp_focal_gamma,
            mask=sample_weight,
        )
        components["shift"] = loss
        total = total + cfg.lambda_shift * loss

    # -------- raw/effective mismatch (control-drift auxiliary) --------
    if "raw_eff_mismatch_logit" in forward_out and "raw_eff_mismatch" in target:
        loss = bce_with_logits_loss(
            forward_out["raw_eff_mismatch_logit"],
            target["raw_eff_mismatch"],
            mask=sample_weight,
        )
        components["mismatch"] = loss
        total = total + cfg.lambda_mismatch * loss

    # -------- KL (Dreamer-style; free nats + balancing) --------
    if all(k in forward_out for k in ("prior_mean", "prior_std", "post_mean", "post_std")):
        kl = kl_loss_dreamer(
            prior_mean=forward_out["prior_mean"],
            prior_std=forward_out["prior_std"],
            post_mean=forward_out["post_mean"],
            post_std=forward_out["post_std"],
            free_nats=cfg.free_nats,
            kl_balance=cfg.kl_balance,
            mask=sample_weight,
        )
        components["kl"] = kl
        total = total + cfg.beta_kl * kl
        # diagnostics: raw KL (free-nats 미적용) for monitoring
        with torch.no_grad():
            raw_kl = kl_divergence_diag_normal(
                forward_out["prior_mean"], forward_out["prior_std"],
                forward_out["post_mean"], forward_out["post_std"],
            ).sum(dim=-1)
            diagnostics["kl_raw_mean"] = masked_mean(raw_kl, sample_weight)

    return WMLossOutput(total=total, components=components, diagnostics=diagnostics)


# =============================================================================
# 4. helpers
# =============================================================================


def _pick_device(d: Mapping[str, Tensor]) -> torch.device:
    for v in d.values():
        if isinstance(v, Tensor):
            return v.device
    return torch.device("cpu")


__all__ = [
    "WMLossOutput",
    "masked_mean",
    "mse_loss",
    "bce_with_logits_loss",
    "categorical_ce_loss",
    "kl_divergence_diag_normal",
    "kl_loss_dreamer",
    "compute_total_loss",
]
