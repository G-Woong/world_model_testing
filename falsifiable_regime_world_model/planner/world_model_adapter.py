"""WorldModelAdapter — 학습된 RSSM checkpoint를 planner가 부를 수 있도록 감싸는 adapter.

PART2 §3.14의 알고리즘 단계를 1:1로 노출한다.
    - load_from_checkpoint   : 학습 checkpoint 로드 (model + variant + device)
    - encode_observation     : env obs (numpy dict) → encoder feature tensor
    - update_belief          : posterior_step 한 번 (belief update)
    - imagine_from_belief    : current hypothesis prior rollout (alternative_mode=False)
    - imagine_alternative    : alternative hypothesis rollout (latent perturbation 또는
                               regime top-k 기반; oracle 사용 금지)
    - score_rollout          : RolloutPrediction → candidate value (discounted return)
    - get_head_outputs       : 단일 belief에서 head 평가 (planner 의사결정용)

Notes
-----
- 본 모듈은 oracle/metadata leakage 방지를 위해 obs dict의 ``local_grid``/``scalar``/
  ``event_token`` 키만 사용한다. info의 ``true_state``/``true_regime`` 등은 절대 input
  으로 사용하지 않는다.
- 모든 forward는 torch.no_grad. 학습 graph는 만들지 않는다.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import torch
from torch import Tensor

from ..wm.checkpointing import load_checkpoint as _load_ckpt
from ..wm.config import WMConfig
from ..wm.heads import RSSMWorldModel
from ..wm.modules import concat_features
from ..wm.rssm import RSSMState

from .interface import BeliefState, RolloutPrediction


# =============================================================================
# 1. helpers — obs dict → tensor
# =============================================================================


def _obs_to_tensors(
    obs: Dict[str, np.ndarray],
    *,
    device: torch.device,
    add_time_dim: bool = True,
) -> Dict[str, Tensor]:
    """env obs (numpy dict) → encoder가 받을 tensor dict.

    Notes
    -----
    - ``local_grid`` (H, W, C) → (1, 1, H, W, C) float32
    - ``scalar``     (S,)      → (1, 1, S)       float32
    - ``event_token``  scalar  → (1, 1)          long
    - ``action_raw`` (optional, scalar) → (1, 1) long
    - oracle key는 절대 transform되지 않는다 (planner도 이 함수만 호출).
    """
    local = torch.from_numpy(np.asarray(obs["local_grid"], dtype=np.float32))
    scalar = torch.from_numpy(np.asarray(obs["scalar"], dtype=np.float32))
    event = torch.tensor(int(obs["event_token"]), dtype=torch.long)
    if add_time_dim:
        local = local.unsqueeze(0).unsqueeze(0)        # (1, 1, H, W, C)
        scalar = scalar.unsqueeze(0).unsqueeze(0)      # (1, 1, S)
        event = event.reshape(1, 1)                    # (1, 1)
    return {
        "local_grid": local.to(device),
        "scalar": scalar.to(device),
        "event_token": event.to(device),
    }


def _resolve_device(device: str) -> torch.device:
    if device == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    return torch.device(device)


# =============================================================================
# 2. WorldModelAdapter
# =============================================================================


class WorldModelAdapter:
    """학습된 RSSM world model의 planner-side 리모컨.

    1 인스턴스 = 1 checkpoint. variant ablation은 별도 adapter를 만든다.
    """

    def __init__(
        self,
        model: RSSMWorldModel,
        wm_config: WMConfig,
        *,
        device: torch.device,
        checkpoint_path: Optional[Path] = None,
        variant: str = "full_model",
    ) -> None:
        self.model = model
        self.wm_config = wm_config
        self.device = device
        self.checkpoint_path = checkpoint_path
        self.variant = variant
        # head ON 표 (planner 측 fallback 결정에 사용)
        self.has_regime_head = wm_config.heads.regime
        self.has_change_point_head = wm_config.heads.change_point
        self.has_reveal_head = wm_config.heads.reveal
        self.has_shift_head = wm_config.heads.shift
        self.has_mismatch_head = wm_config.heads.raw_eff_mismatch
        self.has_state_head = wm_config.heads.state
        self.has_reward_head = wm_config.heads.reward
        self.has_done_head = wm_config.heads.done
        self.regime_num_classes = wm_config.regime.num_control_modes
        self.action_emb_dim = wm_config.encoder_action_input_dim

    # ---------------------------------------------------------------------
    # constructor: checkpoint 로드
    # ---------------------------------------------------------------------
    @classmethod
    def load_from_checkpoint(
        cls,
        checkpoint_path: str | Path,
        *,
        wm_config_path: str | Path,
        variant: str = "full_model",
        device: str = "auto",
    ) -> "WorldModelAdapter":
        """Session 9 ManagedCheckpointer 형식의 .pt 파일을 로드한다.

        Parameters
        ----------
        checkpoint_path : .pt 파일 경로 (예: outputs/wm_runs/.../step_00030000.pt)
        wm_config_path  : 학습 시 사용한 wm yaml (예: configs/wm_medium.yaml)
        variant         : full_model | no_regime | no_change_point | ...
        device          : auto | cuda | cpu
        """
        dev = _resolve_device(device)
        ckpt_path = Path(checkpoint_path)
        wm_path = Path(wm_config_path)
        if not ckpt_path.is_file():
            raise FileNotFoundError(f"checkpoint not found: {ckpt_path}")
        if not wm_path.is_file():
            raise FileNotFoundError(f"wm yaml not found: {wm_path}")
        wm_cfg = WMConfig.from_yaml(wm_path).apply_variant(variant)
        state = _load_ckpt(ckpt_path, map_location=dev)
        model = RSSMWorldModel(wm_cfg).to(dev)
        # state_dict 로드 (체크포인트 variant와 일치하지 않으면 missing/unexpected key가 발생)
        missing, unexpected = model.load_state_dict(state["model"], strict=False)
        if unexpected:
            raise RuntimeError(
                f"unexpected keys when loading checkpoint {ckpt_path.name} into variant "
                f"'{variant}': {unexpected[:5]}{'...' if len(unexpected) > 5 else ''}"
            )
        # missing keys는 head 비활성화에 따라 자연 발생할 수 있음 (예: variant=no_regime이면
        # regime head module이 없음). 단, ckpt에 있던 head를 이쪽에서 안 만들면 lost.
        # → variant가 ckpt 학습 variant와 일치해야 한다.
        if missing:
            # 헤드 끔으로 인해 missing이 발생할 수 있으나, backbone 핵심 (encoder/RSSM)에서
            # missing이 발생하면 critical.
            critical = [k for k in missing if not _is_head_key(k)]
            if critical:
                raise RuntimeError(
                    f"missing critical keys for variant '{variant}' from {ckpt_path.name}: "
                    f"{critical[:5]}{'...' if len(critical) > 5 else ''}"
                )
        model.eval()
        return cls(
            model=model,
            wm_config=wm_cfg,
            device=dev,
            checkpoint_path=ckpt_path,
            variant=variant,
        )

    # ---------------------------------------------------------------------
    # 1) encode observation
    # ---------------------------------------------------------------------
    @torch.no_grad()
    def encode_observation(self, obs: Dict[str, np.ndarray]) -> Tensor:
        """단일 obs (numpy) → encoder feature (1, 1, F).

        oracle leakage 방지: obs dict에서 ``local_grid``, ``scalar``, ``event_token``만 사용.
        """
        tensors = _obs_to_tensors(obs, device=self.device, add_time_dim=True)
        feat = self.model.encoder(
            tensors["local_grid"], tensors["scalar"], tensors["event_token"],
        )
        return feat   # (1, 1, F)

    # ---------------------------------------------------------------------
    # 2) update belief (posterior step 한 번)
    # ---------------------------------------------------------------------
    @torch.no_grad()
    def update_belief(
        self,
        prev_belief: Optional[BeliefState],
        obs: Dict[str, np.ndarray],
        prev_action: Optional[int] = None,
        *,
        step_index: int = 0,
    ) -> BeliefState:
        """env obs를 받아 posterior_step → 새 BeliefState 반환.

        Parameters
        ----------
        prev_belief : 직전 step의 BeliefState. 첫 step에서 None이면 zero-state로 초기화.
        obs         : env obs dict (numpy).
        prev_action : 직전 step에서 환경에 보낸 raw action. 첫 step은 None (=0 padding).
        step_index  : 현재 env step (0-based).
        """
        # initial state
        if prev_belief is None:
            init = self.model.initial_state(batch_size=1, device=self.device)
            prev_h, prev_z = init.h, init.z
            prev_pm, prev_ps = init.prior_mean, init.prior_std
        else:
            prev_h = prev_belief.h
            prev_z = prev_belief.z
            prev_pm = prev_belief.prior_mean
            prev_ps = prev_belief.prior_std

        # encoder feature
        tensors = _obs_to_tensors(obs, device=self.device, add_time_dim=True)
        feat = self.model.encoder(
            tensors["local_grid"], tensors["scalar"], tensors["event_token"],
        )   # (1, 1, F)
        feat_t = feat[:, 0]   # (1, F)

        # action embedding (prev action; 첫 step은 0)
        a = int(prev_action) if prev_action is not None else 0
        action_t = torch.tensor([[a]], dtype=torch.long, device=self.device)   # (1, 1)
        prev_action_emb = self.model.action_emb(action_t)[:, 0]   # (1, E)
        if not self.wm_config.rssm.gru_input_action:
            prev_action_emb = prev_action_emb[:, :0]   # zero-dim slice

        # RSSM posterior_step
        prev_state = RSSMState(
            h=prev_h, z=prev_z,
            prior_mean=prev_pm, prior_std=prev_ps,
            post_mean=None, post_std=None,
        )
        new_state = self.model.rssm.posterior_step(
            prev_state=prev_state,
            prev_action_emb=prev_action_emb,
            feature_t=feat_t,
        )

        # head outputs at this belief (single timestep)
        head_out = self._predict_heads_single(new_state.h, new_state.z)

        return BeliefState(
            h=new_state.h,
            z=new_state.z,
            prior_mean=new_state.prior_mean,
            prior_std=new_state.prior_std,
            post_mean=new_state.post_mean,
            post_std=new_state.post_std,
            head_outputs=head_out,
            last_action=a,
            step_index=int(step_index),
        )

    # ---------------------------------------------------------------------
    # 3) get_head_outputs at a single belief (no time dim)
    # ---------------------------------------------------------------------
    @torch.no_grad()
    def get_head_outputs(self, belief: BeliefState) -> Dict[str, Tensor]:
        """belief 한 step의 head 예측 dict.

        Returns
        -------
        dict — keys: state_pred (1,5), reward_pred (1,), done_logit (1,),
                     regime_logits (1,R) | None, change_point_logit (1,) | None,
                     reveal_logit (1,) | None, shift_logit (1,) | None,
                     raw_eff_mismatch_logit (1,) | None.
        """
        return self._predict_heads_single(belief.h, belief.z)

    @torch.no_grad()
    def _predict_heads_single(self, h: Tensor, z: Tensor) -> Dict[str, Tensor]:
        """h, z가 (1, D) shape이라고 가정하고 (1, 1, D)로 늘려 head 평가 후 squeeze."""
        h_in = h.unsqueeze(1) if h.dim() == 2 else h     # (1, 1, deter)
        z_in = z.unsqueeze(1) if z.dim() == 2 else z     # (1, 1, stoch)
        out = self.model.predict_heads(h_in, z_in)
        squeezed: Dict[str, Tensor] = {}
        for k, v in out.items():
            # (1, 1, ...) → (1, ...)
            squeezed[k] = v[:, 0] if v.dim() >= 2 else v
        return squeezed

    # ---------------------------------------------------------------------
    # 4) imagine — current hypothesis rollout
    # ---------------------------------------------------------------------
    @torch.no_grad()
    def imagine_from_belief(
        self,
        belief: BeliefState,
        action_sequences: np.ndarray,
        *,
        horizon: Optional[int] = None,
        n_samples: int = 1,
        n_candidates: Optional[int] = None,
    ) -> RolloutPrediction:
        """current belief에서 prior-only rollout. PART2 §3.14.7 step 7.

        Parameters
        ----------
        belief           : 현재 belief.
        action_sequences : (C*S, H) np.ndarray of int. C candidate × S sample.
                           (S>1이면 같은 candidate를 여러 번 stochastic하게 굴린다.)
        horizon          : H. None이면 array shape에서 추론.
        n_samples        : S
        n_candidates     : C. None이면 array shape에서 추론.

        Returns
        -------
        RolloutPrediction (모든 head output은 (C*S, H, ...) shape)
        """
        if action_sequences.ndim != 2:
            raise ValueError(f"action_sequences must be 2D (CS, H); got {action_sequences.shape}")
        CS, H = action_sequences.shape
        if horizon is None:
            horizon = H
        if n_candidates is None:
            n_candidates = CS // max(1, n_samples)
        if n_candidates * n_samples != CS:
            raise ValueError(
                f"n_candidates({n_candidates}) * n_samples({n_samples}) != CS({CS})"
            )

        # belief을 (CS, ...)로 broadcast
        h0 = belief.h.expand(CS, -1).contiguous()
        z0 = belief.z.expand(CS, -1).contiguous()
        pm0 = belief.prior_mean.expand(CS, -1).contiguous()
        ps0 = belief.prior_std.expand(CS, -1).contiguous()
        init = RSSMState(h=h0, z=z0, prior_mean=pm0, prior_std=ps0)

        # action sequence (CS, H) → tensor
        a_seq = torch.from_numpy(np.asarray(action_sequences, dtype=np.int64)).to(self.device)

        # imagine — model.imagine 호출
        out = self.model.imagine(a_seq, init)

        rollout = RolloutPrediction(
            candidate_actions=a_seq.reshape(n_candidates, n_samples, horizon)[:, 0],   # (C, H)
            h=out["h"], z=out["z"],
            state_pred=out.get("state_pred"),
            reward_pred=out.get("reward_pred"),
            done_logit=out.get("done_logit"),
            regime_logits=out.get("regime_logits"),
            change_point_logit=out.get("change_point_logit"),
            reveal_logit=out.get("reveal_logit"),
            shift_logit=out.get("shift_logit"),
            mismatch_logit=out.get("raw_eff_mismatch_logit"),
            n_samples=int(n_samples),
            n_candidates=int(n_candidates),
            horizon=int(horizon),
            rollout_steps=int(CS * horizon),
        )
        return rollout

    # ---------------------------------------------------------------------
    # 5) imagine_alternative — alternative hypothesis rollout
    # ---------------------------------------------------------------------
    @torch.no_grad()
    def imagine_alternative(
        self,
        belief: BeliefState,
        action_sequences: np.ndarray,
        *,
        horizon: Optional[int] = None,
        n_samples: int = 4,
        n_candidates: Optional[int] = None,
        latent_perturb_std: float = 0.5,
        regime_topk_index: Optional[int] = None,
    ) -> RolloutPrediction:
        """alternative regime hypothesis 가정 하의 rollout.

        oracle 금지: true_regime을 input으로 직접 사용하지 않는다. 다음 두 메커니즘 중
        하나(또는 둘 다)로 alternative를 모의한다.

        1) **stochastic z perturbation** (always): initial z를 ``latent_perturb_std`` 배의
           Gaussian noise로 흔들어 alternative latent posterior에서 sampling한 것처럼 굴린다.
        2) **regime top-k seed bias** (optional): ``regime_topk_index``가 주어지면, 그
           regime을 더 supportive하게 보이게 하는 latent 방향으로 초기 z를 push한다.
           구체적으로는 prior_mean을 동일하게 두고 std를 약간 키워 더 넓은 sampling을 유도.
           (regime embedding을 직접 주입하는 정식 conditioning은 학습된 모델이 이를 받지
           않으므로 사용 불가; 본 구현은 "model이 스스로 의심하는 대안" 원칙을 지킨다.)

        Returns
        -------
        RolloutPrediction with same schema as ``imagine_from_belief``.
        """
        if action_sequences.ndim != 2:
            raise ValueError(f"action_sequences must be 2D (CS, H); got {action_sequences.shape}")
        CS, H = action_sequences.shape
        if horizon is None:
            horizon = H
        if n_candidates is None:
            n_candidates = CS // max(1, n_samples)

        # initial state broadcast + perturbation
        h0 = belief.h.expand(CS, -1).contiguous()
        z_mean = belief.z.expand(CS, -1).contiguous()
        # Gaussian noise (CS, stoch_dim) — broadcast가 같은 noise를 만들지 않도록 새로 생성
        noise = torch.randn(z_mean.shape, device=self.device, dtype=z_mean.dtype)
        z0 = z_mean + noise * float(latent_perturb_std)
        pm0 = belief.prior_mean.expand(CS, -1).contiguous()
        ps0 = belief.prior_std.expand(CS, -1).contiguous()
        # regime_topk_index가 주어졌으나 모델에 regime conditioning이 없는 경우 prior_std를
        # 약간 키워 alternative trajectory diversity를 유도.
        if regime_topk_index is not None:
            ps0 = ps0 * (1.0 + 0.5 * float(regime_topk_index))
        init = RSSMState(h=h0, z=z0, prior_mean=pm0, prior_std=ps0)

        a_seq = torch.from_numpy(np.asarray(action_sequences, dtype=np.int64)).to(self.device)
        out = self.model.imagine(a_seq, init)
        return RolloutPrediction(
            candidate_actions=a_seq.reshape(n_candidates, n_samples, horizon)[:, 0],
            h=out["h"], z=out["z"],
            state_pred=out.get("state_pred"),
            reward_pred=out.get("reward_pred"),
            done_logit=out.get("done_logit"),
            regime_logits=out.get("regime_logits"),
            change_point_logit=out.get("change_point_logit"),
            reveal_logit=out.get("reveal_logit"),
            shift_logit=out.get("shift_logit"),
            mismatch_logit=out.get("raw_eff_mismatch_logit"),
            n_samples=int(n_samples),
            n_candidates=int(n_candidates),
            horizon=int(horizon),
            rollout_steps=int(CS * horizon),
        )

    # ---------------------------------------------------------------------
    # 6) score_rollout
    # ---------------------------------------------------------------------
    @torch.no_grad()
    def score_rollout(
        self,
        rollout: RolloutPrediction,
        *,
        gamma: float = 0.99,
        risk_weight: float = 0.0,
    ) -> Tensor:
        """RolloutPrediction → (n_candidates,) 점수.

        기본은 discounted reward sum. ``risk_weight > 0``이면 mismatch/cp 위험을 차감.
        """
        value = rollout.candidate_value(gamma=gamma)
        if risk_weight <= 0.0:
            return value
        # risk = mean over horizon × samples of mismatch + cp probability
        risk = torch.zeros_like(value)
        if rollout.mismatch_logit is not None:
            m = torch.sigmoid(rollout.mismatch_logit)
            risk = risk + m.reshape(rollout.n_candidates, rollout.n_samples, rollout.horizon).mean(dim=(1, 2))
        if rollout.change_point_logit is not None:
            c = torch.sigmoid(rollout.change_point_logit)
            risk = risk + c.reshape(rollout.n_candidates, rollout.n_samples, rollout.horizon).mean(dim=(1, 2))
        return value - float(risk_weight) * risk


# =============================================================================
# 3. helpers
# =============================================================================


def _is_head_key(key: str) -> bool:
    """state_dict key가 head module에 속하는지 (variant ablation으로 missing 가능)."""
    head_prefixes = (
        "heads.reward_head.",
        "heads.done_head.",
        "heads.state_head.",
        "heads.regime_head.",
        "heads.change_point_head.",
        "heads.reveal_head.",
        "heads.shift_head.",
        "heads.mismatch_head.",
        "heads.action_rel_proxy_head.",
        "heads.obs_decoder.",
    )
    return any(key.startswith(p) for p in head_prefixes)


__all__ = ["WorldModelAdapter"]
