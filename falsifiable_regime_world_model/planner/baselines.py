"""Baseline planners (PART3 §3.22).

본 모듈은 6 baseline을 모두 구현한다. 모든 baseline은:
- 동일한 ``WorldModelAdapter`` checkpoint 위에서 작동한다 (PART0 §1.4 same-backbone).
- 동일한 ``PlannerConfig`` compute budget 안에서 비교된다 (PART3 §3.25.6 compute frontier).
- 사용 불가한 head는 N/A로 fallback한다 (no_regime이면 regime entropy 사용 금지 등).

Baselines:
1. ReactivePlanner            — 매 step head-greedy 1-step lookahead.
2. FixedKPlanner              — k step마다 horizon planning.
3. AlwaysPlanPlanner          — 매 step planning.
4. UncertaintyGatePlanner     — uncertainty가 threshold 초과 시 planning.
5. AdaptiveLookaheadPlanner   — uncertainty/risk에 따라 horizon 조절.
6. EventOnlyPlanner           — reveal/mismatch event detect 시 planning.

oracle leakage 방지: 모든 baseline은 belief.head_outputs와 action_mask만 사용한다.
"""
from __future__ import annotations

import abc
from dataclasses import dataclass
from typing import Any, Dict, Optional, Sequence

import numpy as np

from .action_space import (
    ActionSpaceSpec,
    enumerate_action_candidates,
    sample_action_sequences,
    candidates_to_tensor,
)
from .config import BaselinePlannerConfig, PlannerConfig
from .interface import BeliefState, ComputeAccountant, PlannerDecision, PlannerState, RolloutPrediction
from .policies import select_reactive_action
from .scoring import _entropy_from_logits, _sigmoid
from .world_model_adapter import WorldModelAdapter


# =============================================================================
# 1. BasePlanner abstract class
# =============================================================================


class BasePlanner(abc.ABC):
    """모든 planner의 공통 interface.

    ``select_action(env_obs, info, planner_state)``이 이 한 step의 결정을 만든다.
    info는 metric 계산을 위해 trace에 기록되는 ground-truth가 들어 있지만 planner는
    ``info``를 input으로 사용하지 않는다 (oracle leakage 방지).
    """

    name: str = "base"

    def __init__(
        self,
        *,
        adapter: WorldModelAdapter,
        config: PlannerConfig,
        baseline_config: Optional[BaselinePlannerConfig] = None,
        action_space: Optional[ActionSpaceSpec] = None,
        rng: Optional[np.random.Generator] = None,
    ) -> None:
        self.adapter = adapter
        self.config = config
        self.baseline = baseline_config or BaselinePlannerConfig()
        self.action_space = action_space or ActionSpaceSpec(
            action_subset=config.action_subset,
            use_action_mask=config.use_action_mask,
        )
        self.rng = rng or np.random.default_rng(config.sampling_seed)

    # ------------------------------------------------------------------
    # planner interface — override
    # ------------------------------------------------------------------
    @abc.abstractmethod
    def select_action(
        self,
        *,
        env_obs: Dict[str, np.ndarray],
        belief: BeliefState,
        planner_state: PlannerState,
    ) -> PlannerDecision:
        ...

    # ------------------------------------------------------------------
    # 공통 helpers
    # ------------------------------------------------------------------
    def _do_planning(
        self,
        *,
        belief: BeliefState,
        action_mask: Optional[np.ndarray],
        horizon: int,
        candidate_count: int,
        n_samples: int,
        accountant: ComputeAccountant,
    ) -> tuple[Optional[RolloutPrediction], int]:
        """planning 한 번 (current hypothesis only).

        Returns
        -------
        (rollout, picked_action) — budget이 부족하면 (None, fallback action).
        """
        # candidate generation: 첫 step 다양화 + horizon > 1이면 random tail
        if horizon > 1 and candidate_count > self.action_space.action_vocab:
            candidates = sample_action_sequences(
                self.action_space,
                n_candidates=candidate_count,
                horizon=horizon,
                rng=self.rng,
                action_mask=action_mask,
            )
        else:
            candidates = enumerate_action_candidates(
                self.action_space, horizon=horizon, action_mask=action_mask,
            )
            # candidate_count보다 많으면 truncate
            if len(candidates) > candidate_count:
                candidates = candidates[:candidate_count]
        if not candidates:
            return None, self.action_space.wait_action
        arr = candidates_to_tensor(candidates, n_samples=n_samples)
        expected_steps = arr.shape[0] * horizon
        if not accountant.can_plan(expected_rollout_steps=expected_steps):
            # budget 부족 → fallback action
            fallback = int(candidates[0].actions[0])
            return None, fallback
        rollout = self.adapter.imagine_from_belief(
            belief, arr,
            horizon=horizon,
            n_samples=n_samples,
            n_candidates=len(candidates),
        )
        accountant.record_planning(
            rollout_steps=expected_steps, n_rollouts=len(candidates) * n_samples,
        )
        scores = self.adapter.score_rollout(rollout).detach().cpu().numpy()
        if not np.isfinite(scores).any():
            best = 0
        else:
            best = int(np.argmax(scores))
        action = int(candidates[best].actions[0])
        return rollout, action


# =============================================================================
# 2. ReactivePlanner
# =============================================================================


class ReactivePlanner(BasePlanner):
    """매 step head-greedy 1-step lookahead.

    PART3 §3.22.1: planning이 거의 없는 기준점. compute는 (n_valid_actions × 1) step만 사용.
    """

    name = "reactive"

    def select_action(self, *, env_obs, belief, planner_state):
        accountant = planner_state.accountant
        action_mask = env_obs.get("action_mask")
        # 1-step lookahead
        candidates = enumerate_action_candidates(
            self.action_space, horizon=1, action_mask=action_mask,
        )
        n_steps = len(candidates) * 1
        if not accountant.can_plan(expected_rollout_steps=n_steps):
            # 매우 strict한 budget이면 random valid action
            valid = self.action_space.available_actions(action_mask)
            return PlannerDecision(
                action=int(self.rng.choice(valid)) if valid else self.action_space.wait_action,
                decision_mode="reactive",
                used_planning=False,
                planning_calls=0,
                rollout_steps=0,
                candidate_count=0,
                horizon=0,
                decision_reason={"fallback": "budget_exhausted"},
            )
        action = select_reactive_action(
            adapter=self.adapter,
            belief=belief,
            action_space=self.action_space,
            action_mask=action_mask,
            horizon=1,
            rng=self.rng,
        )
        accountant.record_planning(
            rollout_steps=n_steps, n_rollouts=len(candidates),
        )
        return PlannerDecision(
            action=int(action),
            decision_mode="reactive",
            used_planning=True,    # head-greedy도 imagine 1 step 호출이라 planning 사용으로 기록
            planning_calls=1,
            rollout_steps=n_steps,
            candidate_count=len(candidates),
            horizon=1,
            decision_reason={"strategy": "head_greedy_1step"},
        )


# =============================================================================
# 3. FixedKPlanner
# =============================================================================


class FixedKPlanner(BasePlanner):
    """매 k step마다 planning. cp/reveal/mismatch는 보지 않는다."""

    name = "fixed_k"

    def select_action(self, *, env_obs, belief, planner_state):
        accountant = planner_state.accountant
        action_mask = env_obs.get("action_mask")
        k = max(1, int(self.baseline.fixed_k_period))
        do_plan = (belief.step_index % k == 0)

        if not do_plan:
            # reactive fallback
            action = select_reactive_action(
                adapter=self.adapter, belief=belief,
                action_space=self.action_space, action_mask=action_mask,
                horizon=1, rng=self.rng,
            )
            n_valid = len(self.action_space.available_actions(action_mask))
            accountant.record_planning(rollout_steps=n_valid, n_rollouts=n_valid)
            return PlannerDecision(
                action=int(action),
                decision_mode="reactive",
                used_planning=False,
                planning_calls=0,
                rollout_steps=n_valid,
                candidate_count=n_valid,
                horizon=1,
                decision_reason={"fixed_k_period": k, "step_mod_k": belief.step_index % k},
            )

        rollout, action = self._do_planning(
            belief=belief, action_mask=action_mask,
            horizon=self.config.horizon,
            candidate_count=self.config.candidate_action_count,
            n_samples=self.config.num_rollouts_per_candidate,
            accountant=accountant,
        )
        return PlannerDecision(
            action=int(action),
            decision_mode="plan_current" if rollout is not None else "reactive",
            used_planning=rollout is not None,
            planning_calls=1 if rollout is not None else 0,
            rollout_steps=accountant._step_rollout_steps,
            candidate_count=self.config.candidate_action_count,
            horizon=self.config.horizon if rollout is not None else 0,
            decision_reason={"fixed_k_period": k, "do_plan": True},
        )


# =============================================================================
# 4. AlwaysPlanPlanner
# =============================================================================


class AlwaysPlanPlanner(BasePlanner):
    """매 step planning. compute frontier에서 손해를 봐야 하는 baseline."""

    name = "always_plan"

    def select_action(self, *, env_obs, belief, planner_state):
        accountant = planner_state.accountant
        action_mask = env_obs.get("action_mask")
        rollout, action = self._do_planning(
            belief=belief, action_mask=action_mask,
            horizon=self.config.horizon,
            candidate_count=self.config.candidate_action_count,
            n_samples=self.config.num_rollouts_per_candidate,
            accountant=accountant,
        )
        return PlannerDecision(
            action=int(action),
            decision_mode="plan_current" if rollout is not None else "reactive",
            used_planning=rollout is not None,
            planning_calls=1 if rollout is not None else 0,
            rollout_steps=accountant._step_rollout_steps,
            candidate_count=self.config.candidate_action_count,
            horizon=self.config.horizon if rollout is not None else 0,
            decision_reason={"always_plan": True},
        )


# =============================================================================
# 5. UncertaintyGatePlanner
# =============================================================================


def _uncertainty_signal(
    belief: BeliefState,
    *,
    signal: str,
    fallback: str,
    has_regime: bool,
    has_change_point: bool,
) -> tuple[float, str]:
    """현재 belief에서 single-step uncertainty signal 계산.

    PART2 §3.7: cp head 직접 사용은 별도 variant로 분리하라는 가이드대로,
    기본은 ``regime_entropy`` 또는 ``reward_var``. cp는 event-only baseline이 사용.
    """
    head = belief.head_outputs
    used = signal
    if signal == "regime_entropy" and has_regime and "regime_logits" in head:
        r = head["regime_logits"].detach().cpu().numpy().reshape(-1)
        ent = _entropy_from_logits(r)
        max_ent = float(np.log(max(2, r.size)))
        return float(ent / max_ent if max_ent > 0 else 0.0), used
    if signal == "reward_var" and "reward_pred" in head:
        # single-step variance proxy: |reward_pred| (단일 sample이라 분산 추정 불가; 절대값 fallback)
        return float(abs(float(head["reward_pred"].item()))), used
    if signal == "latent_var":
        # post_std의 mean
        if belief.post_std is not None:
            return float(belief.post_std.mean().item()), used
        return float(belief.prior_std.mean().item()), used
    if signal == "done_uncertainty" and "done_logit" in head:
        d = float(head["done_logit"].item())
        # entropy of bernoulli
        p = _sigmoid(d)
        if p <= 0 or p >= 1:
            return 0.0, used
        return float(-(p * np.log(p) + (1 - p) * np.log(1 - p)) / np.log(2)), used
    # fallback
    if fallback == "reward_var" and "reward_pred" in head:
        return float(abs(float(head["reward_pred"].item()))), f"{signal}->{fallback}"
    if belief.post_std is not None:
        return float(belief.post_std.mean().item()), f"{signal}->latent_var"
    return float(belief.prior_std.mean().item()), f"{signal}->prior_std"


class UncertaintyGatePlanner(BasePlanner):
    """uncertainty가 threshold 초과 시 planning. PART3 §3.22.4."""

    name = "uncertainty_gate"

    def select_action(self, *, env_obs, belief, planner_state):
        accountant = planner_state.accountant
        action_mask = env_obs.get("action_mask")
        unc, used_signal = _uncertainty_signal(
            belief,
            signal=self.baseline.uncertainty_signal,
            fallback=self.baseline.uncertainty_fallback,
            has_regime=self.adapter.has_regime_head,
            has_change_point=self.adapter.has_change_point_head,
        )
        do_plan = unc >= float(self.baseline.uncertainty_threshold)

        if not do_plan:
            action = select_reactive_action(
                adapter=self.adapter, belief=belief,
                action_space=self.action_space, action_mask=action_mask,
                horizon=1, rng=self.rng,
            )
            n_valid = len(self.action_space.available_actions(action_mask))
            accountant.record_planning(rollout_steps=n_valid, n_rollouts=n_valid)
            return PlannerDecision(
                action=int(action),
                decision_mode="reactive",
                used_planning=False,
                planning_calls=0,
                rollout_steps=n_valid,
                candidate_count=n_valid,
                horizon=1,
                decision_reason={
                    "uncertainty": float(unc), "threshold": float(self.baseline.uncertainty_threshold),
                    "signal": used_signal, "do_plan": False,
                },
            )

        rollout, action = self._do_planning(
            belief=belief, action_mask=action_mask,
            horizon=self.config.horizon,
            candidate_count=self.config.candidate_action_count,
            n_samples=self.config.num_rollouts_per_candidate,
            accountant=accountant,
        )
        return PlannerDecision(
            action=int(action),
            decision_mode="plan_current" if rollout is not None else "reactive",
            used_planning=rollout is not None,
            planning_calls=1 if rollout is not None else 0,
            rollout_steps=accountant._step_rollout_steps,
            candidate_count=self.config.candidate_action_count,
            horizon=self.config.horizon if rollout is not None else 0,
            decision_reason={
                "uncertainty": float(unc), "threshold": float(self.baseline.uncertainty_threshold),
                "signal": used_signal, "do_plan": True,
            },
        )


# =============================================================================
# 6. AdaptiveLookaheadPlanner
# =============================================================================


class AdaptiveLookaheadPlanner(BasePlanner):
    """uncertainty/risk에 따라 horizon/rollout count를 조절. PART3 §3.22.7."""

    name = "adaptive_lookahead"

    def select_action(self, *, env_obs, belief, planner_state):
        accountant = planner_state.accountant
        action_mask = env_obs.get("action_mask")
        unc, used_signal = _uncertainty_signal(
            belief,
            signal=self.baseline.uncertainty_signal,
            fallback=self.baseline.uncertainty_fallback,
            has_regime=self.adapter.has_regime_head,
            has_change_point=self.adapter.has_change_point_head,
        )
        if unc >= float(self.baseline.adaptive_threshold):
            horizon = int(self.baseline.adaptive_high_horizon)
            n_cand = int(self.baseline.adaptive_high_rollouts)
        else:
            horizon = int(self.baseline.adaptive_low_horizon)
            n_cand = int(self.baseline.adaptive_low_rollouts)
        rollout, action = self._do_planning(
            belief=belief, action_mask=action_mask,
            horizon=horizon,
            candidate_count=n_cand,
            n_samples=self.config.num_rollouts_per_candidate,
            accountant=accountant,
        )
        return PlannerDecision(
            action=int(action),
            decision_mode="plan_current" if rollout is not None else "reactive",
            used_planning=rollout is not None,
            planning_calls=1 if rollout is not None else 0,
            rollout_steps=accountant._step_rollout_steps,
            candidate_count=n_cand,
            horizon=horizon if rollout is not None else 0,
            decision_reason={
                "uncertainty": float(unc), "threshold": float(self.baseline.adaptive_threshold),
                "signal": used_signal,
            },
        )


# =============================================================================
# 7. EventOnlyPlanner
# =============================================================================


class EventOnlyPlanner(BasePlanner):
    """reveal_logit / mismatch_logit / novelty score가 high일 때 planning.

    PART3 §3.22.6. cp / falsification / action relevance는 사용하지 않는다.
    """

    name = "event_only"

    def select_action(self, *, env_obs, belief, planner_state):
        accountant = planner_state.accountant
        action_mask = env_obs.get("action_mask")
        head = belief.head_outputs
        signals = []
        for s in self.baseline.event_signals:
            if s == "reveal_prob" and self.adapter.has_reveal_head and "reveal_logit" in head:
                signals.append(_sigmoid(float(head["reveal_logit"].item())))
            elif s == "mismatch_prob" and self.adapter.has_mismatch_head and "raw_eff_mismatch_logit" in head:
                signals.append(_sigmoid(float(head["raw_eff_mismatch_logit"].item())))
            elif s == "shift_prob" and self.adapter.has_shift_head and "shift_logit" in head:
                signals.append(_sigmoid(float(head["shift_logit"].item())))
            elif s == "novelty":
                # novelty = recent prediction error EMA (planner_state가 채움)
                signals.append(planner_state.history_pred_error[-1] if planner_state.history_pred_error else 0.0)
            else:
                signals.append(0.0)
        score = float(np.max(signals)) if signals else 0.0
        do_plan = score >= float(self.baseline.event_threshold)

        if not do_plan:
            action = select_reactive_action(
                adapter=self.adapter, belief=belief,
                action_space=self.action_space, action_mask=action_mask,
                horizon=1, rng=self.rng,
            )
            n_valid = len(self.action_space.available_actions(action_mask))
            accountant.record_planning(rollout_steps=n_valid, n_rollouts=n_valid)
            return PlannerDecision(
                action=int(action),
                decision_mode="reactive",
                used_planning=False,
                planning_calls=0,
                rollout_steps=n_valid,
                candidate_count=n_valid,
                horizon=1,
                decision_reason={
                    "event_score": float(score),
                    "threshold": float(self.baseline.event_threshold),
                    "signals": list(self.baseline.event_signals),
                    "do_plan": False,
                },
            )

        rollout, action = self._do_planning(
            belief=belief, action_mask=action_mask,
            horizon=self.config.horizon,
            candidate_count=self.config.candidate_action_count,
            n_samples=self.config.num_rollouts_per_candidate,
            accountant=accountant,
        )
        return PlannerDecision(
            action=int(action),
            decision_mode="plan_current" if rollout is not None else "reactive",
            used_planning=rollout is not None,
            planning_calls=1 if rollout is not None else 0,
            rollout_steps=accountant._step_rollout_steps,
            candidate_count=self.config.candidate_action_count,
            horizon=self.config.horizon if rollout is not None else 0,
            decision_reason={
                "event_score": float(score),
                "threshold": float(self.baseline.event_threshold),
                "do_plan": True,
            },
        )


__all__ = [
    "BasePlanner",
    "ReactivePlanner",
    "FixedKPlanner",
    "AlwaysPlanPlanner",
    "UncertaintyGatePlanner",
    "AdaptiveLookaheadPlanner",
    "EventOnlyPlanner",
]
