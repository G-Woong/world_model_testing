"""Episode-level metrics + aggregation helpers (Session 11-13).

PART3 §3.25 metric을 구현한다.

metric 분류:
- task: success_rate, return, episode_length, completion_rate per task A/B/C/D
- compute: planning_calls, imagined_rollouts, rollout_steps, compute_normalized_return,
            return_per_1k_imagined_steps
- regime tracking (사용 가능 시): wrong_hypothesis_persistence, recovery_delay_after_change
- decision: action_flip_rate, action_relevance_precision, false_planning_call_rate
- OOD: degradation ratio (split별 separately)

ground truth (true_regime, change_point, ...)은 PlannerTrace의 info_summary에 저장되어
있고, 이 metric은 그 ground truth를 후처리로만 사용한다 (planner는 보지 않음).
"""
from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np


# =============================================================================
# 1. EpisodeResult — 한 episode의 raw 결과
# =============================================================================


@dataclass
class EpisodeResult:
    episode_id: str
    split: str
    model_name: str
    planner_name: str
    seed: int
    episode_index: int

    # outcome
    episode_return: float = 0.0
    episode_length: int = 0
    success: bool = False             # 4 task all completed
    completed_tasks: int = 0
    task_completed: Tuple[bool, bool, bool, bool] = (False, False, False, False)
    fail_count: int = 0

    # compute
    planning_calls: int = 0
    imagined_rollouts: int = 0
    rollout_steps: int = 0

    # decision
    decision_mode_counts: Dict[str, int] = field(default_factory=dict)
    action_flip_count: int = 0     # FRC가 alternative로 flip한 횟수
    correct_mode_count: int = 0
    avoid_mode_count: int = 0

    # regime tracking (post-hoc; ground truth 사용; planner input 아님)
    wrong_hypothesis_persistence: int = 0
    recovery_delay_after_change: float = float("nan")   # NaN if no change observed
    change_point_count: int = 0

    # FRC 전용 (baselines은 0)
    mean_falsification_score: float = 0.0
    mean_action_relevance: float = 0.0
    false_planning_call_rate: float = 0.0    # planning했지만 reward 개선 없음 비율
    action_relevance_precision: float = float("nan")   # 후처리

    # extras
    extras: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# 2. compute_episode_metrics — PlannerTrace + episode info → EpisodeResult
# =============================================================================


def compute_episode_metrics(
    *,
    trace_steps: Sequence[Dict[str, Any]],
    trace_summary: Dict[str, Any],
    episode_id: str,
    split: str,
    model_name: str,
    planner_name: str,
    seed: int,
    episode_index: int,
) -> EpisodeResult:
    """PlannerTrace의 step list + summary로부터 EpisodeResult 계산.

    trace_steps는 StepTrace를 dict로 직렬화한 list (rollout_runner가 채움).
    """
    if not trace_steps:
        return EpisodeResult(
            episode_id=episode_id, split=split, model_name=model_name,
            planner_name=planner_name, seed=seed, episode_index=episode_index,
        )
    steps = list(trace_steps)
    final = trace_summary or {}

    # 기본 outcome
    episode_return = float(steps[-1].get("cumulative_reward", 0.0))
    episode_length = int(len(steps))
    completed_tasks = int(final.get("completed_tasks", 0))
    success = bool(final.get("all_tasks_completed", completed_tasks >= 4))
    task_completed = tuple(bool(x) for x in final.get("task_completed", [False] * 4))[:4]
    if len(task_completed) < 4:
        task_completed = task_completed + tuple([False] * (4 - len(task_completed)))
    fail_count = int(final.get("fail_count", 0))

    # compute
    planning_calls = int(sum(int(s.get("planning_calls", 0)) for s in steps))
    rollout_steps = int(sum(int(s.get("rollout_steps", 0)) for s in steps))
    imagined_rollouts = int(final.get("imagined_rollouts", 0))

    # decision mode 분포
    mode_counts: Dict[str, int] = defaultdict(int)
    for s in steps:
        mode_counts[str(s.get("decision_mode", "reactive"))] += 1
    correct_count = int(mode_counts.get("correct", 0))
    avoid_count = int(mode_counts.get("avoid", 0))

    # action flip count = decision_reason의 action_flip=True
    action_flip_count = int(sum(
        1 for s in steps
        if bool(s.get("decision_reason", {}).get("action_flip", False))
    ))

    # FRC scores
    mean_fal = float(np.mean([float(s.get("falsification_score", 0.0)) for s in steps])) if steps else 0.0
    mean_rel = float(np.mean([float(s.get("action_relevance", 0.0)) for s in steps])) if steps else 0.0

    # wrong_hypothesis_persistence: 모델이 추정한 best regime vs ground truth가 mismatch한
    # 누적 step 수 (planner는 ground truth를 안 보지만 metric은 본다).
    whp = 0
    cp_count = 0
    recovery_delays: List[int] = []
    last_change_step: Optional[int] = None
    last_recovery_step: Optional[int] = None
    last_observed_pred_regime: Optional[int] = None
    for s in steps:
        info = s.get("info_summary") or {}
        pred = s.get("head_pred_summary") or {}
        true_regime_dict = info.get("true_regime") or {}
        true_regime = int(true_regime_dict.get("control_mode", -1))
        # head 추정 regime argmax
        regime_argmax = pred.get("regime_argmax")
        if regime_argmax is not None and true_regime >= 0:
            ra = int(regime_argmax)
            if ra != true_regime:
                whp += 1
            last_observed_pred_regime = ra
        # ground truth change point (info의 change_point)
        if bool(info.get("change_point", False)):
            cp_count += 1
            last_change_step = int(s.get("step", 0))
            last_recovery_step = None
        # recovery: change 후 step에서 모델이 새 regime을 맞히기 시작하면 recovery 시점
        if last_change_step is not None and last_recovery_step is None:
            if regime_argmax is not None and true_regime >= 0 and int(regime_argmax) == true_regime:
                last_recovery_step = int(s.get("step", 0))
                recovery_delays.append(last_recovery_step - last_change_step)
                last_change_step = None    # 다음 change까지 대기

    recovery = float(np.mean(recovery_delays)) if recovery_delays else float("nan")

    # false planning call rate: planning한 step 중 reward delta가 0/음수인 비율
    plan_steps = [s for s in steps if int(s.get("planning_calls", 0)) > 0]
    false_calls = 0
    for i, s in enumerate(steps):
        if int(s.get("planning_calls", 0)) > 0:
            r = float(s.get("reward", 0.0))
            if r <= 0:
                false_calls += 1
    false_planning_rate = float(false_calls / max(1, len(plan_steps))) if plan_steps else 0.0

    return EpisodeResult(
        episode_id=episode_id, split=split,
        model_name=model_name, planner_name=planner_name,
        seed=seed, episode_index=episode_index,
        episode_return=episode_return,
        episode_length=episode_length,
        success=success,
        completed_tasks=completed_tasks,
        task_completed=task_completed,
        fail_count=fail_count,
        planning_calls=planning_calls,
        imagined_rollouts=imagined_rollouts,
        rollout_steps=rollout_steps,
        decision_mode_counts=dict(mode_counts),
        action_flip_count=action_flip_count,
        correct_mode_count=correct_count,
        avoid_mode_count=avoid_count,
        wrong_hypothesis_persistence=int(whp),
        recovery_delay_after_change=recovery,
        change_point_count=cp_count,
        mean_falsification_score=mean_fal,
        mean_action_relevance=mean_rel,
        false_planning_call_rate=false_planning_rate,
    )


# =============================================================================
# 3. aggregate helpers
# =============================================================================


def _safe_mean(xs: Sequence[float]) -> float:
    xs = [float(x) for x in xs if x is not None and not (isinstance(x, float) and math.isnan(x))]
    return float(np.mean(xs)) if xs else 0.0


def _safe_std(xs: Sequence[float]) -> float:
    xs = [float(x) for x in xs if x is not None and not (isinstance(x, float) and math.isnan(x))]
    return float(np.std(xs)) if xs else 0.0


def bootstrap_ci(values: Sequence[float], *, n_boot: int = 1000, alpha: float = 0.05, rng: Optional[np.random.Generator] = None) -> Tuple[float, float, float]:
    """간단 bootstrap (mean, lo, hi). values가 비면 (0, 0, 0)."""
    arr = np.asarray([float(v) for v in values if v is not None], dtype=np.float64)
    if arr.size == 0:
        return 0.0, 0.0, 0.0
    rng = rng or np.random.default_rng(0)
    means = []
    for _ in range(n_boot):
        sample = rng.choice(arr, size=arr.size, replace=True)
        means.append(float(sample.mean()))
    means = np.asarray(means, dtype=np.float64)
    lo = float(np.percentile(means, 100.0 * alpha / 2))
    hi = float(np.percentile(means, 100.0 * (1 - alpha / 2)))
    return float(arr.mean()), lo, hi


def aggregate_by_planner(
    results: Iterable[EpisodeResult],
) -> List[Dict[str, Any]]:
    """planner별 집계 (split/model 무시). main paper-table용."""
    grouped: Dict[Tuple[str, str], List[EpisodeResult]] = defaultdict(list)
    for r in results:
        grouped[(r.planner_name, r.model_name)].append(r)
    rows = []
    for (planner, model), group in grouped.items():
        rows.append(_aggregate_row(group, key={"planner": planner, "model": model}))
    return rows


def aggregate_by_split(
    results: Iterable[EpisodeResult],
) -> List[Dict[str, Any]]:
    """(planner, model, split)별 집계. OOD breakdown용."""
    grouped: Dict[Tuple[str, str, str], List[EpisodeResult]] = defaultdict(list)
    for r in results:
        grouped[(r.planner_name, r.model_name, r.split)].append(r)
    rows = []
    for (planner, model, split), group in grouped.items():
        rows.append(_aggregate_row(group, key={"planner": planner, "model": model, "split": split}))
    return rows


def _aggregate_row(group: List[EpisodeResult], *, key: Dict[str, Any]) -> Dict[str, Any]:
    n = len(group)
    if n == 0:
        return {**key, "n_episodes": 0}
    returns = [r.episode_return for r in group]
    rmean, rlo, rhi = bootstrap_ci(returns)
    success = [1.0 if r.success else 0.0 for r in group]
    smean, slo, shi = bootstrap_ci(success)
    plan_calls = [r.planning_calls for r in group]
    rollout_steps = [r.rollout_steps for r in group]
    norm = [
        r.episode_return / max(1.0, r.rollout_steps) for r in group
    ]
    nmean, nlo, nhi = bootstrap_ci(norm)
    return_per_1k = [
        r.episode_return * 1000.0 / max(1.0, r.rollout_steps) for r in group
    ]
    success_per_1k = [
        (1.0 if r.success else 0.0) * 1000.0 / max(1.0, r.rollout_steps) for r in group
    ]
    whp = [r.wrong_hypothesis_persistence for r in group]
    rec = [r.recovery_delay_after_change for r in group if not math.isnan(r.recovery_delay_after_change)]
    return {
        **key,
        "n_episodes": int(n),
        "return_mean": float(rmean),
        "return_ci_lo": float(rlo),
        "return_ci_hi": float(rhi),
        "return_std": _safe_std(returns),
        "success_rate": float(smean),
        "success_ci_lo": float(slo),
        "success_ci_hi": float(shi),
        "completed_mean": _safe_mean([r.completed_tasks for r in group]),
        "task_a_rate": _safe_mean([1.0 if r.task_completed[0] else 0.0 for r in group]),
        "task_b_rate": _safe_mean([1.0 if r.task_completed[1] else 0.0 for r in group]),
        "task_c_rate": _safe_mean([1.0 if r.task_completed[2] else 0.0 for r in group]),
        "task_d_rate": _safe_mean([1.0 if r.task_completed[3] else 0.0 for r in group]),
        "episode_length_mean": _safe_mean([r.episode_length for r in group]),
        "planning_calls_mean": _safe_mean(plan_calls),
        "imagined_rollouts_mean": _safe_mean([r.imagined_rollouts for r in group]),
        "rollout_steps_mean": _safe_mean(rollout_steps),
        "compute_normalized_return": float(nmean),
        "compute_norm_ci_lo": float(nlo),
        "compute_norm_ci_hi": float(nhi),
        "return_per_1k_imagined_steps": _safe_mean(return_per_1k),
        "success_per_1k_imagined_steps": _safe_mean(success_per_1k),
        "wrong_hypothesis_persistence_mean": _safe_mean(whp),
        "recovery_delay_after_change_mean": _safe_mean(rec),
        "action_flip_rate": _safe_mean([
            r.action_flip_count / max(1, r.episode_length) for r in group
        ]),
        "false_planning_call_rate": _safe_mean([r.false_planning_call_rate for r in group]),
        "mean_falsification_score": _safe_mean([r.mean_falsification_score for r in group]),
        "mean_action_relevance": _safe_mean([r.mean_action_relevance for r in group]),
    }


__all__ = [
    "EpisodeResult",
    "compute_episode_metrics",
    "bootstrap_ci",
    "aggregate_by_planner",
    "aggregate_by_split",
]
