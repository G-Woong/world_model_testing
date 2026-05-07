"""rollout_runner: 한 episode를 RG4FEnv 위에서 closed-loop으로 돌린다.

호출자(Session 11-13 evaluation script)는 다음 호출을 한다:
    res = run_episode(env, planner, adapter, ..., trace=PlannerTrace(...))

본 함수는:
1. env.reset(seed) → 초기 obs/info
2. adapter.update_belief(prev=None, obs, prev_action=None) → BeliefState
3. for t in range(max_steps):
   a. planner.select_action(env_obs, belief, planner_state) → PlannerDecision
   b. env.step(action) → (next_obs, reward, terminated, truncated, info)
   c. trace에 step_summary 기록 (head_pred / info_summary 모두 metric용)
   d. adapter.update_belief(prev=belief, next_obs, prev_action=action) → new belief
   e. terminated/truncated이면 break

oracle leakage 방지: planner.select_action에는 env_obs와 belief만 넘기고 info는 안 넘긴다.
info는 trace 기록용으로만 사용.
"""
from __future__ import annotations

import time
from dataclasses import asdict
from typing import Any, Dict, Optional

import numpy as np
import torch

from ..planner import (
    BasePlanner,
    BeliefState,
    ComputeAccountant,
    PlannerState,
    PlannerTrace,
    StepTrace,
    WorldModelAdapter,
)
from ..planner.config import PlannerConfig
from ..planner.scoring import _sigmoid
from ..rg4f.env import RG4FEnv


# =============================================================================
# helpers
# =============================================================================


def _summarize_head(head: Dict[str, "torch.Tensor"]) -> Dict[str, Any]:
    """planner trace 기록용 head 예측 요약 (numpy/python primitive)."""
    out: Dict[str, Any] = {}
    if "state_pred" in head:
        out["state_pred"] = head["state_pred"].detach().cpu().numpy().reshape(-1).tolist()
    if "reward_pred" in head:
        out["reward_pred"] = float(head["reward_pred"].item())
    if "done_logit" in head:
        out["done_prob"] = float(_sigmoid(float(head["done_logit"].item())))
    if "regime_logits" in head:
        rl = head["regime_logits"].detach().cpu().numpy().reshape(-1)
        out["regime_argmax"] = int(np.argmax(rl))
        out["regime_probs"] = (np.exp(rl - rl.max()) / np.exp(rl - rl.max()).sum()).tolist()
    if "change_point_logit" in head:
        out["cp_prob"] = float(_sigmoid(float(head["change_point_logit"].item())))
    if "reveal_logit" in head:
        out["reveal_prob"] = float(_sigmoid(float(head["reveal_logit"].item())))
    if "shift_logit" in head:
        out["shift_prob"] = float(_sigmoid(float(head["shift_logit"].item())))
    if "raw_eff_mismatch_logit" in head:
        out["mismatch_prob"] = float(_sigmoid(float(head["raw_eff_mismatch_logit"].item())))
    return out


def _summarize_info(info: Dict[str, Any]) -> Dict[str, Any]:
    """trace 기록용 env info 요약 (ground-truth 포함; metric 계산용)."""
    return {
        "true_state": dict(info.get("true_state") or {}),
        "true_regime": dict(info.get("true_regime") or {}),
        "change_point": bool(info.get("change_point", False)),
        "reveal_event": bool(info.get("reveal_event", False)),
        "shift_event": bool(info.get("shift_event", False)),
        "task_id": int(info.get("task_id", -1)),
        "room_id": int(info.get("room_id", -1)),
        "completed_tasks": int(info.get("completed_tasks", 0)),
        "fail_count": int(info.get("failure_count", 0)),
        "wrong_interaction_count": int(info.get("wrong_interaction_count", 0)),
        "raw_action": int(info.get("raw_action", -1)),
        "effective_action": int(info.get("effective_action", -1)),
    }


# =============================================================================
# main: run_episode
# =============================================================================


def run_episode(
    *,
    env: RG4FEnv,
    planner: BasePlanner,
    adapter: WorldModelAdapter,
    planner_config: PlannerConfig,
    trace: PlannerTrace,
    seed: int,
    max_steps: int = 600,
) -> Dict[str, Any]:
    """한 episode 평가.

    Returns
    -------
    summary dict (PlannerTrace.summary에 들어감 + metric 계산에 사용).
    """
    accountant = ComputeAccountant(
        budget_total=int(planner_config.compute_budget_total),
        budget_per_step=int(planner_config.compute_budget_per_step),
        max_planning_calls=int(planner_config.max_planning_calls_per_episode),
    )
    planner_state = PlannerState(
        belief=None,
        accountant=accountant,
        falsification_window=getattr(planner, "frc", None).falsification_window
        if hasattr(planner, "frc") else 5,
    )

    obs, info = env.reset(seed=seed)
    belief = adapter.update_belief(prev_belief=None, obs=obs, prev_action=None, step_index=0)
    planner_state.belief = belief

    cumulative_reward = 0.0
    completed_tasks = 0
    fail_count = 0
    last_action_taken = None
    task_completed_per_step: list[bool] = [False, False, False, False]

    t0 = time.time()
    for t in range(max_steps):
        accountant.begin_step()
        # planner decision (oracle 차단: info를 넘기지 않는다)
        decision = planner.select_action(
            env_obs=obs, belief=belief, planner_state=planner_state,
        )
        # env step
        next_obs, reward, terminated, truncated, info = env.step(int(decision.action))
        cumulative_reward += float(reward)
        completed_tasks = max(completed_tasks, int(info.get("completed_tasks", completed_tasks)))
        fail_count = int(info.get("failure_count", fail_count))
        # task별 완료 추적
        for i in range(4):
            # info에는 episode-cumulative만 노출되므로, completed_tasks 카운트로 추정 (which task는 trace head에서)
            pass

        # trace 기록
        head_summary = _summarize_head(belief.head_outputs)
        info_summary = _summarize_info(info)
        step_trace = StepTrace(
            step=int(t),
            action=int(decision.action),
            decision_mode=str(decision.decision_mode),
            used_planning=bool(decision.used_planning),
            planning_calls=int(decision.planning_calls),
            rollout_steps=int(decision.rollout_steps),
            candidate_count=int(decision.candidate_count),
            horizon=int(decision.horizon),
            reward=float(reward),
            cumulative_reward=float(cumulative_reward),
            terminated=bool(terminated),
            truncated=bool(truncated),
            falsification_score=float(planner_state.last_falsification_score),
            action_relevance=float(planner_state.last_action_relevance),
            head_pred_summary=head_summary,
            info_summary=info_summary,
            decision_reason=dict(decision.decision_reason),
        )
        trace.steps.append(step_trace)

        # belief update with the new obs
        belief = adapter.update_belief(
            prev_belief=belief, obs=next_obs, prev_action=int(decision.action),
            step_index=t + 1,
        )
        planner_state.belief = belief
        planner_state.push_history(
            obs=next_obs, action=int(decision.action),
            head_pred=None,
            pred_error=0.0,
        )
        last_action_taken = int(decision.action)

        obs = next_obs
        if terminated or truncated:
            break

    elapsed = time.time() - t0

    # task별 completion 후처리: trace의 마지막 step에서 info의 task_completed 정보를
    # 추정 (env가 task별 flag를 노출하지 않으므로 sum=4이면 모든 task 완료로 간주).
    final_completed = int(completed_tasks)
    all_done = bool(final_completed >= 4)
    # task별 완료 여부는 obs.scalar의 마지막 4개 (per-task done flag)로 추정
    # (rg4f.observation.build_scalar 참조: 마지막 4 entry = task A/B/C/D done)
    last_scalar = np.asarray(obs.get("scalar", np.zeros(14, dtype=np.float32)), dtype=np.float32)
    if last_scalar.size >= 4:
        task_done = [bool(last_scalar[-4 + i] >= 0.5) for i in range(4)]
    else:
        task_done = [False] * 4

    summary = {
        "episode_return": float(cumulative_reward),
        "episode_length": int(len(trace.steps)),
        "completed_tasks": int(final_completed),
        "all_tasks_completed": all_done,
        "task_completed": task_done,
        "fail_count": int(fail_count),
        "planning_calls": int(accountant.total_planning_calls),
        "imagined_rollouts": int(accountant.total_imagined_rollouts),
        "rollout_steps": int(accountant.total_rollout_steps),
        "wallclock_seconds": float(elapsed),
        "last_action_taken": last_action_taken,
        "seed": int(seed),
    }
    trace.summary = summary
    return summary


__all__ = ["run_episode"]
