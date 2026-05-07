"""Planner interface: abstract base, belief state, decision, compute accountant.

본 모듈은 모든 baseline / FRC-WM가 공유하는 *interface 계층*만 정의한다. 구체 planner
구현은 ``baselines.py`` / ``frc_planner.py``에 둔다.

주요 객체
---------
- ``BeliefState``      : 현재 belief (RSSMState wrapper) + per-step head outputs.
- ``RolloutPrediction``: imagine 결과 묶음. score/explanation에 사용.
- ``PlannerDecision``  : planner가 한 step에 만든 결정 (action + reasoning + compute).
- ``PlannerState``     : episode 단위 mutable state (history buffer / accountant / trace).
- ``ComputeAccountant`` : compute budget 추적 + per-step / total 한도 enforcement.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np
import torch
from torch import Tensor


# =============================================================================
# 1. BeliefState — 현재 belief + per-step head outputs
# =============================================================================


@dataclass
class BeliefState:
    """planner 호출 시점의 belief 묶음.

    Attributes
    ----------
    h            : (1, deter_dim) tensor — RSSM deterministic state
    z            : (1, stoch_dim) tensor — last sampled stochastic latent (posterior)
    prior_mean   : (1, stoch_dim)
    prior_std    : (1, stoch_dim)
    post_mean    : (1, stoch_dim) | None
    post_std     : (1, stoch_dim) | None
    head_outputs : current step의 head 예측 dict
                  ("state_pred"/"reward_pred"/"regime_logits"/"change_point_logit"/
                   "reveal_logit"/"shift_logit"/"raw_eff_mismatch_logit"/"done_logit")
                  각 텐서는 (1, ...) shape.
    last_action  : 직전 env step에서 선택한 raw action (int). 첫 step은 None.
    step_index   : 현재 env step (0-based).
    """

    h: Tensor
    z: Tensor
    prior_mean: Tensor
    prior_std: Tensor
    post_mean: Optional[Tensor] = None
    post_std: Optional[Tensor] = None
    head_outputs: Dict[str, Tensor] = field(default_factory=dict)
    last_action: Optional[int] = None
    step_index: int = 0


# =============================================================================
# 2. RolloutPrediction — imagine 결과 묶음
# =============================================================================


@dataclass
class RolloutPrediction:
    """imagine_from_belief / imagine_alternative의 출력.

    여러 candidate × 여러 sample을 한 batch로 한 번에 굴린 결과를 담는다.

    Attributes
    ----------
    candidate_actions : (C, H) long — C candidate × H horizon raw action sequence
    h                 : (C*S, H, deter_dim) — RSSM deter rollout
    z                 : (C*S, H, stoch_dim) — RSSM stoch rollout
    state_pred        : (C*S, H, 5)
    reward_pred       : (C*S, H)
    done_logit        : (C*S, H)
    regime_logits     : (C*S, H, R) | None
    change_point_logit: (C*S, H) | None
    reveal_logit      : (C*S, H) | None
    shift_logit       : (C*S, H) | None
    mismatch_logit    : (C*S, H) | None
    n_samples         : S — candidate별 sampling 횟수 (stochastic z)
    n_candidates      : C
    horizon           : H
    rollout_steps     : C * S * H — compute accounting용
    """

    candidate_actions: Tensor
    h: Tensor
    z: Tensor
    state_pred: Optional[Tensor] = None
    reward_pred: Optional[Tensor] = None
    done_logit: Optional[Tensor] = None
    regime_logits: Optional[Tensor] = None
    change_point_logit: Optional[Tensor] = None
    reveal_logit: Optional[Tensor] = None
    shift_logit: Optional[Tensor] = None
    mismatch_logit: Optional[Tensor] = None
    n_samples: int = 1
    n_candidates: int = 1
    horizon: int = 1
    rollout_steps: int = 0

    def candidate_value(self, *, gamma: float = 0.99) -> Tensor:
        """각 candidate의 discounted reward sum (sample 평균).

        Returns
        -------
        (C,) tensor of expected return.
        """
        if self.reward_pred is None:
            return torch.zeros(self.n_candidates, device=self.h.device)
        # (C*S, H) → (C, S, H)
        r = self.reward_pred.reshape(self.n_candidates, self.n_samples, self.horizon)
        # done masking: done_logit > 0 이후의 reward는 비활성. 단순 sigmoid > 0.5 기준.
        if self.done_logit is not None:
            d = torch.sigmoid(
                self.done_logit.reshape(self.n_candidates, self.n_samples, self.horizon)
            )
            # cumulative survival probability (1 - done)
            survive = torch.cumprod(1.0 - d, dim=-1)
        else:
            survive = torch.ones_like(r)
        # discount factor (1, 1, H)
        discount = torch.tensor(
            [gamma ** t for t in range(self.horizon)],
            device=r.device, dtype=r.dtype,
        ).reshape(1, 1, -1)
        weighted = r * survive * discount
        # sample 평균 → candidate별 합 (over horizon)
        return weighted.mean(dim=1).sum(dim=-1)


# =============================================================================
# 3. PlannerDecision
# =============================================================================


@dataclass
class PlannerDecision:
    """한 env step에서 planner가 만든 결정.

    Attributes
    ----------
    action          : 선택된 raw action (int 0..15).
    decision_mode   : "reactive" | "plan_current" | "plan_alternative" | "correct" |
                     "avoid" | "delay" | "explore_for_information"
    used_planning   : 이번 step에서 planning을 호출했는가.
    planning_calls  : 이번 결정에 사용한 planning call 수 (보통 0 또는 1).
    rollout_steps   : 이번 결정에 사용한 imagined rollout step 수 (compute accounting).
    candidate_count : 평가한 candidate action 수.
    horizon         : 사용한 horizon.
    decision_reason : 사람이 읽을 수 있는 사유 dict (per-mode score / threshold 등).
    """

    action: int
    decision_mode: str = "reactive"
    used_planning: bool = False
    planning_calls: int = 0
    rollout_steps: int = 0
    candidate_count: int = 0
    horizon: int = 0
    decision_reason: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# 4. ComputeAccountant — budget 추적
# =============================================================================


class ComputeAccountant:
    """episode 동안 누적된 compute / planning_call 추적.

    PART3 §3.25: planning_calls / rollout_steps / compute-normalized return은
    paper-main metric이다. 본 클래스는 모든 planner가 공유하는 단일 회계 체계다.
    """

    def __init__(
        self,
        *,
        budget_total: int = 0,
        budget_per_step: int = 0,
        max_planning_calls: int = 0,
    ) -> None:
        self.budget_total = int(budget_total)
        self.budget_per_step = int(budget_per_step)
        self.max_planning_calls = int(max_planning_calls)
        # episode-level accumulators
        self.total_rollout_steps: int = 0
        self.total_planning_calls: int = 0
        self.total_imagined_rollouts: int = 0
        # step-level accumulator (reset between env steps)
        self._step_rollout_steps: int = 0
        self._step_planning_calls: int = 0

    # ---------------------------------------------------------------------
    # checks
    # ---------------------------------------------------------------------
    def can_plan(self, expected_rollout_steps: int = 0) -> bool:
        """budget이 충분한가?

        - max_planning_calls=0이면 unlimited.
        - budget_total=0이면 unlimited.
        """
        if self.max_planning_calls > 0 and self.total_planning_calls >= self.max_planning_calls:
            return False
        if self.budget_total > 0:
            if self.total_rollout_steps + expected_rollout_steps > self.budget_total:
                return False
        if self.budget_per_step > 0:
            if self._step_rollout_steps + expected_rollout_steps > self.budget_per_step:
                return False
        return True

    # ---------------------------------------------------------------------
    # accounting
    # ---------------------------------------------------------------------
    def record_planning(
        self,
        *,
        rollout_steps: int,
        n_rollouts: int = 1,
    ) -> None:
        self.total_rollout_steps += int(rollout_steps)
        self._step_rollout_steps += int(rollout_steps)
        self.total_imagined_rollouts += int(n_rollouts)
        self.total_planning_calls += 1
        self._step_planning_calls += 1

    def begin_step(self) -> None:
        self._step_rollout_steps = 0
        self._step_planning_calls = 0

    # ---------------------------------------------------------------------
    # snapshot
    # ---------------------------------------------------------------------
    def snapshot(self) -> Dict[str, int]:
        return {
            "total_rollout_steps": self.total_rollout_steps,
            "total_planning_calls": self.total_planning_calls,
            "total_imagined_rollouts": self.total_imagined_rollouts,
            "step_rollout_steps": self._step_rollout_steps,
            "step_planning_calls": self._step_planning_calls,
        }


# =============================================================================
# 5. PlannerState — episode 단위 mutable state
# =============================================================================


@dataclass
class PlannerState:
    """episode 동안 유지되는 planner 측 상태 묶음.

    Attributes
    ----------
    belief                : 가장 최근 BeliefState
    accountant            : ComputeAccountant
    history_obs           : 최근 W step의 observation history (window for falsification)
    history_actions       : 최근 W step의 action history
    history_head_pred     : 최근 W step의 head 예측 history (state/reward/regime)
    history_head_target   : 최근 W step의 실제 다음 obs와 비교한 prediction error
    falsification_window  : window 길이 W
    last_decision_mode    : 직전 step의 decision mode
    """

    belief: Optional[BeliefState] = None
    accountant: Optional[ComputeAccountant] = None
    history_obs: List[Dict[str, np.ndarray]] = field(default_factory=list)
    history_actions: List[int] = field(default_factory=list)
    history_head_pred: List[Dict[str, np.ndarray]] = field(default_factory=list)
    history_pred_error: List[float] = field(default_factory=list)
    falsification_window: int = 5
    last_decision_mode: str = "reactive"
    # per-step diagnostic (FRC가 채움; baseline은 0)
    last_falsification_score: float = 0.0
    last_action_relevance: float = 0.0

    def push_history(
        self,
        *,
        obs: Dict[str, np.ndarray],
        action: int,
        head_pred: Optional[Dict[str, np.ndarray]] = None,
        pred_error: float = 0.0,
    ) -> None:
        self.history_obs.append(obs)
        self.history_actions.append(action)
        if head_pred is not None:
            self.history_head_pred.append(head_pred)
        self.history_pred_error.append(float(pred_error))
        # window 유지
        W = self.falsification_window
        if len(self.history_obs) > W:
            self.history_obs = self.history_obs[-W:]
        if len(self.history_actions) > W:
            self.history_actions = self.history_actions[-W:]
        if len(self.history_head_pred) > W:
            self.history_head_pred = self.history_head_pred[-W:]
        if len(self.history_pred_error) > W:
            self.history_pred_error = self.history_pred_error[-W:]


__all__ = [
    "BeliefState",
    "RolloutPrediction",
    "PlannerDecision",
    "ComputeAccountant",
    "PlannerState",
]
