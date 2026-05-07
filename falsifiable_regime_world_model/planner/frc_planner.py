"""FRC-WM planner (Ours): Falsification-driven Regime-Conditioned World Model.

PART2 §3.7~§3.14 알고리즘을 1:1 구현.

알고리즘 흐름:
    1. belief update (이미 outer evaluation runner가 호출했음)
    2. falsification score F_t (current hypothesis가 반증될 가능성)
    3. low falsification → reactive (1-step)
    4. medium → current rollout만 (top relevant candidates)
    5. high → alternative rollout 추가, horizon ↑, candidate count ↑
    6. extreme risk → avoid / delay / correct mode 선택
    7. 결정 mode + selected action 반환

핵심 보장:
- oracle 사용 금지: head outputs(regime_logits, change_point_logit, mismatch_logit, ...)
  만 사용하고 info의 ground truth는 절대 input으로 사용하지 않는다.
- variant ablation: no_regime이면 regime_uncertainty 자동 N/A. no_change_point면 cp_risk 자동 0.
- compute reallocation: planning을 안 하면 reactive call만 (low cost). 의심 시에만 alternative
  rollout을 추가 호출 → "amount"가 아니라 "target"이 reallocation됨.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import torch

from .action_space import (
    ActionSpaceSpec,
    enumerate_action_candidates,
    sample_action_sequences,
    candidates_to_tensor,
)
from .baselines import BasePlanner
from .config import BaselinePlannerConfig, FRCPlannerConfig, PlannerConfig
from .interface import BeliefState, PlannerDecision, PlannerState, RolloutPrediction
from .scoring import (
    FalsificationContext,
    FalsificationResult,
    _entropy_from_logits,
    _sigmoid,
    compute_action_relevance,
    compute_alternative_disagreement,
    compute_falsification_score,
)
from .world_model_adapter import WorldModelAdapter


# =============================================================================
# 1. FRCWMPlanner
# =============================================================================


class FRCWMPlanner(BasePlanner):
    """Falsification-Relevance-Compute reallocation planner."""

    name = "ours_frc"

    def __init__(
        self,
        *,
        adapter: WorldModelAdapter,
        config: PlannerConfig,
        frc_config: Optional[FRCPlannerConfig] = None,
        baseline_config: Optional[BaselinePlannerConfig] = None,
        action_space: Optional[ActionSpaceSpec] = None,
        rng: Optional[np.random.Generator] = None,
    ) -> None:
        super().__init__(
            adapter=adapter, config=config,
            baseline_config=baseline_config, action_space=action_space, rng=rng,
        )
        self.frc = frc_config or FRCPlannerConfig()
        # variant에 따라 head 사용 여부 자동 fallback
        if not self.adapter.has_change_point_head:
            self.frc.use_change_point = False
        if not self.adapter.has_regime_head:
            self.frc.use_regime_head = False
        # 자체 falsification context (planner_state.history와 별도로 관리)
        self.context = FalsificationContext(
            window_size=int(self.frc.falsification_window),
        )
        # FRC는 alternative rollout을 켠다 (planner config의 enable_alternative_rollout 무시)
        self.config.enable_alternative_rollout = True

    # ------------------------------------------------------------------
    # main
    # ------------------------------------------------------------------
    def select_action(self, *, env_obs, belief, planner_state):
        accountant = planner_state.accountant
        action_mask = env_obs.get("action_mask")

        # ---- 0) context push (recent evidence 누적) ----
        head = belief.head_outputs
        cp_prob = (
            _sigmoid(float(head["change_point_logit"].item()))
            if "change_point_logit" in head and self.frc.use_change_point else None
        )
        mismatch_prob = (
            _sigmoid(float(head["raw_eff_mismatch_logit"].item()))
            if "raw_eff_mismatch_logit" in head else None
        )
        regime_entropy = None
        if self.frc.use_regime_head and "regime_logits" in head:
            r = head["regime_logits"].detach().cpu().numpy().reshape(-1)
            ent = _entropy_from_logits(r)
            max_ent = float(np.log(max(2, r.size)))
            regime_entropy = float(ent / max_ent if max_ent > 0 else 0.0)
        pred_state = (
            head["state_pred"].detach().cpu().numpy().reshape(-1) if "state_pred" in head else None
        )
        # obs.scalar의 처음 5개는 5D 상태값 (rg4f.observation.build_scalar)
        obs_state = np.asarray(env_obs["scalar"], dtype=np.float32)[:5]
        self.context.push(
            pred_state=pred_state,
            obs_state=obs_state,
            cp_prob=cp_prob, mismatch_prob=mismatch_prob, regime_entropy=regime_entropy,
        )

        # ---- 1) preliminary falsification score (rollout disagreement 없이) ----
        prelim = compute_falsification_score(
            belief=belief, context=self.context,
            weights=self.frc.falsification_weights,
            cp_logit_threshold=self.frc.cp_logit_threshold,
            mismatch_logit_threshold=self.frc.mismatch_logit_threshold,
            use_change_point=self.frc.use_change_point,
            use_regime=self.frc.use_regime_head,
            rollout_disagreement=None,
        )

        # ---- 2) low falsification path: reactive ----
        if prelim.score < float(self.frc.falsification_threshold):
            # reactive 1-step
            from .policies import select_reactive_action
            action = select_reactive_action(
                adapter=self.adapter, belief=belief,
                action_space=self.action_space, action_mask=action_mask,
                horizon=1, rng=self.rng,
            )
            n_valid = len(self.action_space.available_actions(action_mask))
            accountant.record_planning(rollout_steps=n_valid, n_rollouts=n_valid)
            planner_state.last_falsification_score = prelim.score
            planner_state.last_action_relevance = 0.0
            planner_state.last_decision_mode = "reactive"
            return PlannerDecision(
                action=int(action),
                decision_mode="reactive",
                used_planning=False,
                planning_calls=0,
                rollout_steps=n_valid,
                candidate_count=n_valid,
                horizon=1,
                decision_reason={
                    "stage": "low_falsification",
                    "falsification_score": prelim.score,
                    "falsification_reason": prelim.reason,
                },
            )

        # ---- 3) compute reallocation: medium vs high vs extreme ----
        if prelim.score >= float(self.frc.avoid_risk_threshold):
            stage = "extreme"
            horizon = int(self.frc.extreme_horizon)
            n_cand = int(self.frc.extreme_rollouts)
        elif prelim.score >= float(self.frc.extreme_falsification):
            stage = "high"
            horizon = int(self.frc.extreme_horizon)
            n_cand = int(self.frc.extreme_rollouts)
        else:
            stage = "medium"
            horizon = int(self.frc.base_horizon)
            n_cand = int(self.frc.base_rollouts)

        # ---- 4) candidate generation: top relevant first action에 bias ----
        # bias = head action_rel_proxy가 있으면 그것을 따르고, 없으면 enumerate_action_candidates
        # (모든 valid action을 candidate로) 후 score로 선택.
        candidates = enumerate_action_candidates(
            self.action_space, horizon=horizon, action_mask=action_mask,
            repeat_first_action=True,
        )
        if len(candidates) > n_cand:
            candidates = candidates[:n_cand]
        # candidate가 부족하면 random sampling으로 보충
        if len(candidates) < n_cand and horizon > 1:
            extra = sample_action_sequences(
                self.action_space, n_candidates=n_cand - len(candidates),
                horizon=horizon, rng=self.rng, action_mask=action_mask,
            )
            candidates = list(candidates) + list(extra)

        n_samples = int(self.config.num_rollouts_per_candidate)
        arr = candidates_to_tensor(candidates, n_samples=n_samples)

        # ---- 5) current rollout ----
        steps_cur = arr.shape[0] * horizon
        if not accountant.can_plan(expected_rollout_steps=steps_cur):
            # budget 부족 → fallback to reactive
            from .policies import select_reactive_action
            action = select_reactive_action(
                adapter=self.adapter, belief=belief,
                action_space=self.action_space, action_mask=action_mask,
                horizon=1, rng=self.rng,
            )
            n_valid = len(self.action_space.available_actions(action_mask))
            accountant.record_planning(rollout_steps=n_valid, n_rollouts=n_valid)
            planner_state.last_falsification_score = prelim.score
            planner_state.last_action_relevance = 0.0
            planner_state.last_decision_mode = "delay"
            return PlannerDecision(
                action=int(action),
                decision_mode="delay",
                used_planning=False,
                planning_calls=0,
                rollout_steps=n_valid,
                candidate_count=n_valid,
                horizon=1,
                decision_reason={
                    "stage": stage, "falsification_score": prelim.score,
                    "fallback": "budget_exhausted",
                },
            )
        rollout_cur = self.adapter.imagine_from_belief(
            belief, arr, horizon=horizon, n_samples=n_samples,
            n_candidates=len(candidates),
        )
        accountant.record_planning(
            rollout_steps=steps_cur, n_rollouts=len(candidates) * n_samples,
        )

        # ---- 6) alternative rollout (high/extreme stage) ----
        rollout_alt: Optional[RolloutPrediction] = None
        used_alternative = False
        if stage in ("high", "extreme"):
            alt_samples = int(self.config.num_alternative_samples)
            steps_alt = arr.shape[0] * horizon
            if accountant.can_plan(expected_rollout_steps=steps_alt):
                rollout_alt = self.adapter.imagine_alternative(
                    belief, arr, horizon=horizon, n_samples=n_samples,
                    n_candidates=len(candidates),
                    latent_perturb_std=float(self.config.alt_latent_perturb_std),
                    regime_topk_index=1,    # 1 = first alternative
                )
                accountant.record_planning(
                    rollout_steps=steps_alt, n_rollouts=len(candidates) * n_samples,
                )
                used_alternative = True

        # ---- 7) action relevance + final score ----
        relevance = compute_action_relevance(
            rollout_current=rollout_cur,
            rollout_alternative=rollout_alt,
            relevance_value_gap_norm=float(self.frc.relevance_value_gap_norm),
            use_action_flip=bool(self.frc.relevance_use_action_flip),
        )

        # ---- 8) compute alternative disagreement (FRC update + 최종 falsification 보강) ----
        if rollout_alt is not None:
            disagreement_dict = compute_alternative_disagreement(
                current=rollout_cur, alternatives=[rollout_alt],
            )
            disagreement_score = float(disagreement_dict["predicted_reward_gap"])
            # 최종 falsification score 재계산 (rollout_disagreement 반영)
            final = compute_falsification_score(
                belief=belief, context=self.context,
                weights=self.frc.falsification_weights,
                cp_logit_threshold=self.frc.cp_logit_threshold,
                mismatch_logit_threshold=self.frc.mismatch_logit_threshold,
                use_change_point=self.frc.use_change_point,
                use_regime=self.frc.use_regime_head,
                rollout_disagreement=disagreement_score,
            )
        else:
            disagreement_dict = {
                "predicted_reward_gap": 0.0,
                "predicted_state_disagreement": 0.0,
                "predicted_regime_uncertainty": 0.0,
                "predicted_change_risk": 0.0,
            }
            final = prelim

        # ---- 9) decision mode 선택 ----
        # avoid: extreme risk + no flip benefit
        # correct: state pred가 target band에서 멀고 mismatch_risk 큼 → state-adjust action으로
        # delay: budget 거의 소진 + uncertainty 매우 높음 → wait
        # plan_alternative: alternative가 flip 만들었음
        # plan_current: planning 했지만 alternative 없음 또는 flip 없음
        # explore_for_information: high regime entropy + low value gap
        decision_mode = "plan_current"
        chosen_action = int(candidates[relevance.best_index].actions[0])

        if stage == "extreme" and self.frc.enable_avoid_mode:
            # avoid: 가장 안전한 action 선택 (best risk-adjusted)
            adj = relevance.value - relevance.risk
            safe_idx = int(np.argmax(adj))
            chosen_action = int(candidates[safe_idx].actions[0])
            decision_mode = "avoid"
        elif used_alternative and relevance.flip_from_argmax_current and self.frc.enable_correct_mode:
            decision_mode = "plan_alternative"
            chosen_action = int(candidates[relevance.best_index].actions[0])
            # correct mode: state-adjust action 우선 (correction_state_dim_priority)
            if (
                final.reason.get("mismatch_risk", 0.0) > 0.5
                and head.get("state_pred") is not None
            ):
                # 가장 큰 |state_pred| 차원에 대해 state-adjust action 선택
                state_dev = pred_state if pred_state is not None else np.zeros(5, dtype=np.float32)
                # correction_state_dim_priority: drift, interaction, mobility 우선
                dim_pri = list(self.frc.correction_state_dim_priority)
                # 가장 dev 큰 dim 중 priority 안의 것
                priorities = sorted(
                    dim_pri, key=lambda d: -abs(state_dev[d]) if d < state_dev.size else 0.0,
                )
                chosen_dim = priorities[0] if priorities else None
                if chosen_dim is not None and chosen_dim < state_dev.size:
                    sign = -1 if state_dev[chosen_dim] > 0 else 1
                    # action vocab: V_PLUS=5, V_MINUS=6, M_PLUS=7, M_MINUS=8, ...
                    base = 5 + 2 * int(chosen_dim)
                    correct_action = base if sign > 0 else base + 1
                    if action_mask is None or float(action_mask[correct_action]) > 0.5:
                        chosen_action = int(correct_action)
                        decision_mode = "correct"
        elif used_alternative and self.frc.enable_explore_mode and final.reason.get("regime_uncertainty", 0.0) > 0.7 and final.reason.get("rollout_disagreement", 0.0) < 0.1:
            decision_mode = "explore_for_information"
        elif self.frc.enable_delay_mode and not accountant.can_plan(expected_rollout_steps=1) and final.score > 0.5:
            decision_mode = "delay"
            chosen_action = int(self.frc.delay_action)

        planner_state.last_falsification_score = final.score
        planner_state.last_action_relevance = float(np.max(relevance.relevance)) if relevance.relevance.size else 0.0
        planner_state.last_decision_mode = decision_mode

        return PlannerDecision(
            action=int(chosen_action),
            decision_mode=decision_mode,
            used_planning=True,
            planning_calls=2 if used_alternative else 1,
            rollout_steps=accountant._step_rollout_steps,
            candidate_count=len(candidates),
            horizon=horizon,
            decision_reason={
                "stage": stage,
                "falsification_score": final.score,
                "falsification_reason": final.reason,
                "action_relevance_max": float(np.max(relevance.relevance)) if relevance.relevance.size else 0.0,
                "action_relevance_value_gap": float(relevance.value_gap),
                "action_flip": bool(relevance.flip_from_argmax_current),
                "used_alternative": used_alternative,
                "alt_disagreement": disagreement_dict,
                "best_index": int(relevance.best_index),
            },
        )


__all__ = ["FRCWMPlanner"]
