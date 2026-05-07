"""WM prediction head 모음 + RSSMWorldModel(top-level).

본 모듈은 다음을 정의한다:
    1) 각 head의 forward (PART2/PART3에서 정의된 supervision target에 대응)
    2) ``RSSMWorldModel``: encoder + RSSM + heads + (optional) decoder를 묶는 top-level

forward output dict의 key contract는 ``forward()`` docstring에 명시되어 있다. 이
contract는 Session 9의 training step과 Session 11의 planner가 그대로 의존하는
**계약(API)** 이다 — 임의로 key명을 바꾸면 안 된다.
"""
from __future__ import annotations

from typing import Dict, Optional

import torch
from torch import Tensor, nn

from .config import HeadsConfig, ObservationConfig, RegimeConfig, RSSMConfig, WMConfig
from .modules import (
    ActionEmbedding,
    ObservationDecoder,
    ObservationEncoder,
    concat_features,
    make_mlp,
)
from .rssm import RSSM, RSSMState


# =============================================================================
# 1. small generic heads
# =============================================================================


class ScalarHead(nn.Module):
    """features -> 1-D scalar 예측 (예: reward)."""

    def __init__(self, in_dim: int, hidden_dim: int) -> None:
        super().__init__()
        self.net = make_mlp(in_dim, (hidden_dim, hidden_dim), 1, activation="elu")

    def forward(self, features: Tensor) -> Tensor:
        # (B, T, F) → (B, T, 1) → squeeze → (B, T)
        return self.net(features).squeeze(-1)


class BinaryLogitHead(nn.Module):
    """features -> 1-D logit (BCE-with-logits에 직접 넣을 수 있음)."""

    def __init__(self, in_dim: int, hidden_dim: int) -> None:
        super().__init__()
        self.net = make_mlp(in_dim, (hidden_dim, hidden_dim), 1, activation="elu")

    def forward(self, features: Tensor) -> Tensor:
        return self.net(features).squeeze(-1)


class CategoricalLogitHead(nn.Module):
    """features -> num_classes logits (CE에 직접 넣을 수 있음)."""

    def __init__(self, in_dim: int, hidden_dim: int, num_classes: int) -> None:
        super().__init__()
        self.net = make_mlp(in_dim, (hidden_dim, hidden_dim), num_classes, activation="elu")

    def forward(self, features: Tensor) -> Tensor:
        return self.net(features)   # (B, T, num_classes)


class RegressionHead(nn.Module):
    """features -> out_dim regression (예: 5-D true_state)."""

    def __init__(self, in_dim: int, hidden_dim: int, out_dim: int) -> None:
        super().__init__()
        self.net = make_mlp(in_dim, (hidden_dim, hidden_dim), out_dim, activation="elu")

    def forward(self, features: Tensor) -> Tensor:
        return self.net(features)   # (B, T, out_dim)


# =============================================================================
# 2. heads container
# =============================================================================


class WMHeads(nn.Module):
    """모든 head를 하나의 nn.Module로 묶고 forward에서 dict를 반환한다.

    head ON/OFF는 ``HeadsConfig``로 제어된다. OFF인 head는 nn.Module을 만들지 않으며,
    forward output dict에도 해당 key가 없다 (Session 9에서 graceful skip).
    """

    def __init__(
        self,
        feature_dim: int,
        heads_cfg: HeadsConfig,
        regime_cfg: RegimeConfig,
        obs_cfg: ObservationConfig,
    ) -> None:
        super().__init__()
        self.heads_cfg = heads_cfg
        self.regime_cfg = regime_cfg

        H = heads_cfg.hidden_dim
        # observation reconstruction head (decoder)
        self.obs_decoder: Optional[ObservationDecoder] = (
            ObservationDecoder(feature_dim=feature_dim, obs_cfg=obs_cfg, hidden_dim=H)
            if (heads_cfg.obs_recon_local or heads_cfg.obs_recon_scalar)
            else None
        )
        self.reward_head = ScalarHead(feature_dim, H) if heads_cfg.reward else None
        self.done_head = BinaryLogitHead(feature_dim, H) if heads_cfg.done else None
        self.state_head = (
            RegressionHead(feature_dim, H, out_dim=5) if heads_cfg.state else None
        )
        self.regime_head = (
            CategoricalLogitHead(feature_dim, H, num_classes=regime_cfg.num_control_modes)
            if heads_cfg.regime
            else None
        )
        self.change_point_head = BinaryLogitHead(feature_dim, H) if heads_cfg.change_point else None
        self.reveal_head = BinaryLogitHead(feature_dim, H) if heads_cfg.reveal else None
        self.shift_head = BinaryLogitHead(feature_dim, H) if heads_cfg.shift else None
        self.mismatch_head = BinaryLogitHead(feature_dim, H) if heads_cfg.raw_eff_mismatch else None
        # action_relevance_proxy: 단순 scalar regression (실제 action relevance는 Session 13).
        self.action_rel_proxy_head = (
            ScalarHead(feature_dim, H) if heads_cfg.action_relevance_proxy else None
        )

    def forward(self, features: Tensor) -> Dict[str, Tensor]:
        """모든 ON head를 한 번에 호출한다.

        Output dict key contract (이 키들은 Session 9 training step / Session 11 planner와
        반드시 일치해야 한다):
            "obs_local_pred"        : (B, T, H, W, C)   if obs_recon_local
            "obs_scalar_pred"       : (B, T, S)         if obs_recon_scalar
            "reward_pred"           : (B, T)            if reward
            "done_logit"            : (B, T)            if done
            "state_pred"            : (B, T, 5)         if state
            "regime_logits"         : (B, T, R)         if regime
            "change_point_logit"    : (B, T)            if change_point
            "reveal_logit"          : (B, T)            if reveal
            "shift_logit"           : (B, T)            if shift
            "raw_eff_mismatch_logit": (B, T)            if raw_eff_mismatch
            "action_rel_proxy_pred" : (B, T)            if action_relevance_proxy
        """
        out: Dict[str, Tensor] = {}
        if self.obs_decoder is not None:
            local_pred, scalar_pred = self.obs_decoder(features)
            if self.heads_cfg.obs_recon_local:
                out["obs_local_pred"] = local_pred
            if self.heads_cfg.obs_recon_scalar:
                out["obs_scalar_pred"] = scalar_pred
        if self.reward_head is not None:
            out["reward_pred"] = self.reward_head(features)
        if self.done_head is not None:
            out["done_logit"] = self.done_head(features)
        if self.state_head is not None:
            out["state_pred"] = self.state_head(features)
        if self.regime_head is not None:
            out["regime_logits"] = self.regime_head(features)
        if self.change_point_head is not None:
            out["change_point_logit"] = self.change_point_head(features)
        if self.reveal_head is not None:
            out["reveal_logit"] = self.reveal_head(features)
        if self.shift_head is not None:
            out["shift_logit"] = self.shift_head(features)
        if self.mismatch_head is not None:
            out["raw_eff_mismatch_logit"] = self.mismatch_head(features)
        if self.action_rel_proxy_head is not None:
            out["action_rel_proxy_pred"] = self.action_rel_proxy_head(features)
        return out


# =============================================================================
# 3. RSSMWorldModel: encoder + RSSM + heads
# =============================================================================


class RSSMWorldModel(nn.Module):
    """Top-level world model. ``forward(batch)``이 RSSM observation rollout을 수행하고
    모든 ON head를 한 번에 평가한다.

    Forward contract
    ----------------
    Input batch (모든 key는 (B, T, ...) tensor; ``T``는 chunk_len):
        "local_grid"   : float32 (B, T, H, W, C)
        "scalar"       : float32 (B, T, S)
        "event_token"  : long    (B, T)
        "action_raw"   : long    (B, T)        # a_{0..T-1} (env step에 들어간 raw action)
        # (선택) "action_prev_raw" : long (B, T)  # 명시적 a_{t-1}.
        #                                          미제공 시 action_raw를 한 step shift.

    Output dict (heads + RSSM):
        "h" : (B, T, deter_dim)
        "z" : (B, T, stoch_dim)
        "prior_mean", "prior_std" : (B, T, stoch_dim)
        "post_mean",  "post_std"  : (B, T, stoch_dim)
        + WMHeads.forward의 모든 key
    """

    def __init__(self, cfg: WMConfig) -> None:
        super().__init__()
        self.cfg = cfg
        self.encoder = ObservationEncoder(cfg.observation, cfg.encoder)
        self.action_emb = ActionEmbedding(
            action_vocab=cfg.observation.action_vocab,
            embed_dim=cfg.encoder.action_embed_dim,
        )
        self.rssm = RSSM(
            cfg.rssm,
            feature_dim=cfg.encoder.feature_dim,
            action_emb_dim=cfg.encoder.action_embed_dim,
        )
        self.heads = WMHeads(
            feature_dim=cfg.feature_dim,
            heads_cfg=cfg.heads,
            regime_cfg=cfg.regime,
            obs_cfg=cfg.observation,
        )

    # ---------------------------------------------------------------------
    # forward (학습용 BPTT)
    # ---------------------------------------------------------------------
    def forward(
        self,
        batch: Dict[str, Tensor],
        initial_state: Optional[RSSMState] = None,
    ) -> Dict[str, Tensor]:
        """모든 head를 한 번에 평가한다 (학습용 정상 BPTT).

        Notes
        -----
        - ``a_{t-1}``의 alignment는 호출자(Session 8 loader)가 책임진다. 본 메서드는
          batch에 ``action_prev_raw`` 키가 있으면 그것을, 없으면 ``action_raw``를
          한 timestep 우측 shift하여 t=0에 zero(=Action.W=0 슬롯이지만 별도 padding
          mask 없이 0으로 채움 — Session 9의 학습 loop에서 첫 step KL을 적절히
          처리한다)로 사용한다.
        """
        local_grid = batch["local_grid"]
        scalar = batch["scalar"]
        event_token = batch["event_token"]
        action_raw = batch["action_raw"]

        # encoder
        feat = self.encoder(local_grid, scalar, event_token)   # (B, T, F)
        # action embedding (prev step alignment)
        if "action_prev_raw" in batch:
            prev_action_raw = batch["action_prev_raw"]
        else:
            prev_action_raw = self._shift_right(action_raw)
        prev_action_emb = self.action_emb(prev_action_raw)      # (B, T, E)

        # RSSM rollout
        rssm_out = self.rssm.observe_sequence(
            features=feat,
            action_embeds=prev_action_emb,
            initial_state=initial_state,
        )

        # heads
        features = concat_features(rssm_out["h"], rssm_out["z"])  # (B, T, deter+stoch)
        head_out = self.heads(features)

        out: Dict[str, Tensor] = {}
        out.update(rssm_out)
        out.update(head_out)
        return out

    # ---------------------------------------------------------------------
    # head-only evaluation on given (h, z). Session 11의 planner가 사용.
    # ---------------------------------------------------------------------
    def predict_heads(self, h: Tensor, z: Tensor) -> Dict[str, Tensor]:
        """(h, z) sequence에 대해 head만 평가한다 (encoder/RSSM 호출 없이)."""
        features = concat_features(h, z)
        return self.heads(features)

    # ---------------------------------------------------------------------
    # imagine API stub: planner가 alternative-regime rollout을 만들 때 사용한다.
    # Session 7에서는 단순 prior-only rollout만 정의 (single hypothesis).
    # Session 11에서 alternative-regime conditioning을 추가한다.
    # ---------------------------------------------------------------------
    def imagine(
        self,
        action_sequence_raw: Tensor,    # (B, H) long
        initial_state: RSSMState,
    ) -> Dict[str, Tensor]:
        """initial belief에서 action sequence rollout 후 head 예측까지 반환.

        Returns
        -------
        {
          "h", "z" : (B, H, ...)          # RSSM rollout latent
          + heads (WMHeads.forward와 동일 key)
        }

        TODO (Session 11):
          - regime hypothesis embedding을 인자로 추가하여 alternative regime rollout을
            지원한다 (current vs alternative).
          - Q-value head 또는 value-of-computation 계산에 사용할 head 추가 여부를 결정.
        """
        action_emb = self.action_emb(action_sequence_raw)   # (B, H, E)
        rssm_out = self.rssm.imagine_sequence(action_emb, initial_state)
        features = concat_features(rssm_out["h"], rssm_out["z"])
        head_out = self.heads(features)
        out: Dict[str, Tensor] = {}
        out.update(rssm_out)
        out.update(head_out)
        return out

    # ---------------------------------------------------------------------
    # initial state proxy
    # ---------------------------------------------------------------------
    def initial_state(self, batch_size: int, device: torch.device | str) -> RSSMState:
        return self.rssm.initial_state(batch_size, device)

    # ---------------------------------------------------------------------
    # internal helper
    # ---------------------------------------------------------------------
    @staticmethod
    def _shift_right(action_raw: Tensor) -> Tensor:
        """(B, T) action_raw → (B, T) prev_action_raw.

        prev[:, 0] = 0 (=Action.W의 정수값; Session 9 학습에서 첫 step KL은 가중치 0
        또는 mask로 처리). prev[:, 1:] = action_raw[:, :-1].
        """
        B, T = action_raw.shape
        out = torch.zeros_like(action_raw)
        out[:, 1:] = action_raw[:, :-1]
        return out


__all__ = [
    "ScalarHead",
    "BinaryLogitHead",
    "CategoricalLogitHead",
    "RegressionHead",
    "WMHeads",
    "RSSMWorldModel",
]
