"""RSSM (Recurrent State-Space Model) core for the RG-4F world model.

Dreamer 계열 표준 구조를 그대로 따른다:
    - deterministic recurrent state h_t = GRU(h_{t-1}, [z_{t-1}, action_emb_{t-1}])
    - prior         p(z_t | h_t)        ~ Normal(μ_p(h_t), σ_p(h_t))
    - posterior     q(z_t | h_t, e_t)   ~ Normal(μ_q(h_t,e_t), σ_q(h_t,e_t))
    - features = concat(h_t, z_t)는 모든 prediction head의 공통 입력

본 모듈은 forward만 구현한다. training step / optimizer는 Session 9.

PART0 §1 mechanism-novelty 원칙을 따른다:
    - 본 backbone은 RSSM/Dreamer-style "표준"이다 (architecture novelty 아님).
    - regime/falsification/action-relevance/compute-reallocation은 backbone이 아니라
      head + loss + planner(Session 11+) 위에 얹힌다.
    - 모든 baseline/ablation은 본 backbone을 동일 capacity로 공유한다.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

import torch
from torch import Tensor, nn
from torch.nn import functional as F

from .config import RSSMConfig


# =============================================================================
# 1. RSSMState: 한 시점의 (h, z, prior, posterior) 묶음
# =============================================================================


@dataclass
class RSSMState:
    """RSSM의 한 timestep latent state.

    Attributes
    ----------
    h     : Tensor[..., deter_dim]    deterministic recurrent state
    z     : Tensor[..., stoch_dim]    sampled stochastic latent (posterior 또는 prior)
    prior_mean / prior_std         : prior distribution parameter
    post_mean  / post_std          : posterior distribution parameter (posterior step에서만 채워짐)
    """

    h: Tensor
    z: Tensor
    prior_mean: Tensor
    prior_std: Tensor
    post_mean: Optional[Tensor] = None
    post_std: Optional[Tensor] = None

    def detach(self) -> "RSSMState":
        return RSSMState(
            h=self.h.detach(),
            z=self.z.detach(),
            prior_mean=self.prior_mean.detach(),
            prior_std=self.prior_std.detach(),
            post_mean=None if self.post_mean is None else self.post_mean.detach(),
            post_std=None if self.post_std is None else self.post_std.detach(),
        )


# =============================================================================
# 2. Transition / Representation MLP
# =============================================================================


class TransitionPrior(nn.Module):
    """h_t -> Normal(μ_p, σ_p) over z_t. (= prior p(z_t | h_t))"""

    def __init__(self, deter_dim: int, stoch_dim: int, hidden_dim: int, min_std: float) -> None:
        super().__init__()
        self.min_std = float(min_std)
        self.net = nn.Sequential(
            nn.Linear(deter_dim, hidden_dim),
            nn.ELU(),
            nn.Linear(hidden_dim, 2 * stoch_dim),
        )
        self.stoch_dim = stoch_dim

    def forward(self, h: Tensor) -> Tuple[Tensor, Tensor]:
        """return (mean, std). shapes: h (..., deter_dim) → mean/std (..., stoch_dim)."""
        out = self.net(h)
        mean, std_pre = out.split(self.stoch_dim, dim=-1)
        std = F.softplus(std_pre) + self.min_std
        return mean, std


class RepresentationPosterior(nn.Module):
    """[h_t, e_t] -> Normal(μ_q, σ_q) over z_t. (= posterior q(z_t | h_t, e_t))"""

    def __init__(
        self,
        deter_dim: int,
        feature_dim: int,
        stoch_dim: int,
        hidden_dim: int,
        min_std: float,
    ) -> None:
        super().__init__()
        self.min_std = float(min_std)
        self.net = nn.Sequential(
            nn.Linear(deter_dim + feature_dim, hidden_dim),
            nn.ELU(),
            nn.Linear(hidden_dim, 2 * stoch_dim),
        )
        self.stoch_dim = stoch_dim

    def forward(self, h: Tensor, e: Tensor) -> Tuple[Tensor, Tensor]:
        """return (mean, std). h (..., D), e (..., F) → mean/std (..., stoch_dim)."""
        out = self.net(torch.cat([h, e], dim=-1))
        mean, std_pre = out.split(self.stoch_dim, dim=-1)
        std = F.softplus(std_pre) + self.min_std
        return mean, std


# =============================================================================
# 3. Recurrent core (GRUCell)
# =============================================================================


class RSSMCore(nn.Module):
    """RSSM의 deterministic recurrent core h_t = GRU(h_{t-1}, [z_{t-1}, a_{t-1}])."""

    def __init__(self, deter_dim: int, stoch_dim: int, action_emb_dim: int, hidden_dim: int) -> None:
        super().__init__()
        self.deter_dim = deter_dim
        # GRU 입력: stochastic latent + (optional) action embedding을 hidden_dim으로 일단 매핑
        in_dim = stoch_dim + action_emb_dim
        self.input_proj = nn.Sequential(
            nn.Linear(in_dim, hidden_dim),
            nn.ELU(),
        )
        self.cell = nn.GRUCell(hidden_dim, deter_dim)

    def forward(self, h_prev: Tensor, z_prev: Tensor, action_emb: Tensor) -> Tensor:
        """deterministic step.

        Shapes
        ------
        h_prev    : (B, deter_dim)
        z_prev    : (B, stoch_dim)
        action_emb: (B, action_emb_dim)   (action_emb_dim=0인 경우 0-dim tensor 허용)
        out h_t   : (B, deter_dim)
        """
        if action_emb.shape[-1] == 0:
            x = self.input_proj(z_prev)
        else:
            x = self.input_proj(torch.cat([z_prev, action_emb], dim=-1))
        return self.cell(x, h_prev)


# =============================================================================
# 4. RSSM (top-level: posterior step / prior step / sequence rollout)
# =============================================================================


class RSSM(nn.Module):
    """top-level RSSM. forward가 한 step 단위 (posterior_step / prior_step)이며,
    sequence rollout은 ``observe_sequence`` / ``imagine_sequence`` 메서드가 처리한다.

    NOTE
    ----
    - ``observe_sequence``는 학습용 (feature_t = encoder(o_t)를 매 step posterior에 넣음).
    - ``imagine_sequence``는 planner용 stub. Session 7에서는 interface만 정의한다 (구현은
      Session 11에서 horizon 조절, alternative regime hypothesis 등을 추가한다).
    """

    def __init__(self, cfg: RSSMConfig, feature_dim: int, action_emb_dim: int) -> None:
        super().__init__()
        self.cfg = cfg
        self.action_emb_dim = int(action_emb_dim) if cfg.gru_input_action else 0

        self.core = RSSMCore(
            deter_dim=cfg.deter_dim,
            stoch_dim=cfg.stoch_dim,
            action_emb_dim=self.action_emb_dim,
            hidden_dim=cfg.hidden_dim,
        )
        self.prior = TransitionPrior(
            deter_dim=cfg.deter_dim,
            stoch_dim=cfg.stoch_dim,
            hidden_dim=cfg.hidden_dim,
            min_std=cfg.min_std,
        )
        self.posterior = RepresentationPosterior(
            deter_dim=cfg.deter_dim,
            feature_dim=feature_dim,
            stoch_dim=cfg.stoch_dim,
            hidden_dim=cfg.hidden_dim,
            min_std=cfg.min_std,
        )

    # ---------------------------------------------------------------------
    # initial state
    # ---------------------------------------------------------------------
    def initial_state(self, batch_size: int, device: torch.device | str) -> RSSMState:
        device = torch.device(device)
        h = torch.zeros(batch_size, self.cfg.deter_dim, device=device)
        z = torch.zeros(batch_size, self.cfg.stoch_dim, device=device)
        zero_mean = torch.zeros(batch_size, self.cfg.stoch_dim, device=device)
        unit_std = torch.ones(batch_size, self.cfg.stoch_dim, device=device)
        return RSSMState(h=h, z=z, prior_mean=zero_mean, prior_std=unit_std)

    # ---------------------------------------------------------------------
    # posterior step (학습 시 정상 step)
    # ---------------------------------------------------------------------
    def posterior_step(
        self,
        prev_state: RSSMState,
        prev_action_emb: Tensor,
        feature_t: Tensor,
    ) -> RSSMState:
        """observation을 사용해 posterior로 z_t를 sampling하는 한 step.

        Shapes
        ------
        prev_state.h, prev_state.z : (B, deter_dim), (B, stoch_dim)
        prev_action_emb            : (B, action_emb_dim)  (gru_input_action=False면 (B,0))
        feature_t                  : (B, feature_dim)     encoder(o_t)
        out                        : RSSMState (h_t, z_t, prior, posterior)
        """
        h_t = self.core(prev_state.h, prev_state.z, prev_action_emb)
        prior_mean, prior_std = self.prior(h_t)
        post_mean, post_std = self.posterior(h_t, feature_t)
        z_t = _reparametrize(post_mean, post_std)
        return RSSMState(
            h=h_t, z=z_t,
            prior_mean=prior_mean, prior_std=prior_std,
            post_mean=post_mean, post_std=post_std,
        )

    # ---------------------------------------------------------------------
    # prior step (imagine; planner-side rollout에서 사용)
    # ---------------------------------------------------------------------
    def prior_step(
        self,
        prev_state: RSSMState,
        prev_action_emb: Tensor,
    ) -> RSSMState:
        """observation을 사용하지 않고 prior로만 z_t를 sampling하는 한 step.

        Session 7에서는 interface만 둔다. 실제 alternative regime conditioning은
        Session 11에서 추가된다 (예: regime embedding을 prev_action_emb 옆에 concat).
        """
        h_t = self.core(prev_state.h, prev_state.z, prev_action_emb)
        prior_mean, prior_std = self.prior(h_t)
        z_t = _reparametrize(prior_mean, prior_std)
        return RSSMState(
            h=h_t, z=z_t,
            prior_mean=prior_mean, prior_std=prior_std,
            post_mean=None, post_std=None,
        )

    # ---------------------------------------------------------------------
    # sequence: observe (training)
    # ---------------------------------------------------------------------
    def observe_sequence(
        self,
        features: Tensor,                  # (B, T, feature_dim)  encoder(o_{1..T})
        action_embeds: Tensor,             # (B, T, action_emb_dim)  prev action emb (a_{0..T-1})
        initial_state: Optional[RSSMState] = None,
    ) -> Dict[str, Tensor]:
        """학습용 BPTT step. T step을 순차적으로 posterior_step으로 처리한다.

        Returns
        -------
        dict with keys:
            "h"          : (B, T, deter_dim)
            "z"          : (B, T, stoch_dim)
            "prior_mean" : (B, T, stoch_dim)
            "prior_std"  : (B, T, stoch_dim)
            "post_mean"  : (B, T, stoch_dim)
            "post_std"   : (B, T, stoch_dim)
        """
        B, T, _ = features.shape
        if initial_state is None:
            initial_state = self.initial_state(B, features.device)
        # action_embeds[i, t]는 a_{t-1} (이전 step에서 수행한 action)을 임베딩한 것이다.
        # 호출자가 align을 보장한다 (Session 8 loader가 책임짐).
        prev_state = initial_state
        h_list, z_list = [], []
        pm_list, ps_list = [], []
        qm_list, qs_list = [], []
        for t in range(T):
            new_state = self.posterior_step(
                prev_state=prev_state,
                prev_action_emb=action_embeds[:, t],
                feature_t=features[:, t],
            )
            h_list.append(new_state.h)
            z_list.append(new_state.z)
            pm_list.append(new_state.prior_mean)
            ps_list.append(new_state.prior_std)
            qm_list.append(new_state.post_mean)
            qs_list.append(new_state.post_std)
            prev_state = new_state
        return {
            "h": torch.stack(h_list, dim=1),
            "z": torch.stack(z_list, dim=1),
            "prior_mean": torch.stack(pm_list, dim=1),
            "prior_std":  torch.stack(ps_list, dim=1),
            "post_mean":  torch.stack(qm_list, dim=1),
            "post_std":   torch.stack(qs_list, dim=1),
        }

    # ---------------------------------------------------------------------
    # sequence: imagine (planner stub; Session 11에서 확장)
    # ---------------------------------------------------------------------
    def imagine_sequence(
        self,
        action_embeds: Tensor,             # (B, H, action_emb_dim) action sequence to imagine
        initial_state: RSSMState,
    ) -> Dict[str, Tensor]:
        """horizon H에 걸친 prior-only rollout. planner용 stub.

        주의 — Session 7 contract:
          * 본 API는 *interface 정의*다. alternative regime hypothesis 분기,
            current-vs-alternative rollout 비교, action relevance 계산은 Session 11에서
            확장한다 (예: 별도 regime conditioning embedding을 받는 인자 추가).
          * 본 메서드는 reward / done / state 등 head 평가는 하지 않는다 (밖에서
            ``RSSMWorldModel.predict_heads``를 호출).
        """
        B, H, _ = action_embeds.shape
        prev_state = initial_state
        h_list, z_list = [], []
        for t in range(H):
            new_state = self.prior_step(
                prev_state=prev_state,
                prev_action_emb=action_embeds[:, t],
            )
            h_list.append(new_state.h)
            z_list.append(new_state.z)
            prev_state = new_state
        return {
            "h": torch.stack(h_list, dim=1),
            "z": torch.stack(z_list, dim=1),
        }


# =============================================================================
# 5. helpers
# =============================================================================


def _reparametrize(mean: Tensor, std: Tensor) -> Tensor:
    """Gaussian reparameterization trick. eval 시 호출자가 detach 또는 mean 사용."""
    eps = torch.randn_like(mean)
    return mean + eps * std


__all__ = [
    "RSSMState",
    "TransitionPrior",
    "RepresentationPosterior",
    "RSSMCore",
    "RSSM",
]
