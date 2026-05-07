"""falsifiable_regime_world_model.eval — Session 11-13 산출물.

학습된 RSSM checkpoint + planner를 RG4FEnv 위에서 closed-loop rollout으로 평가한다.

주요 객체
---------
- ``EpisodeResult``      : 한 episode의 결과 (return, success, compute, trace)
- ``PlannerEvalRunner``  : (model × planner × split × seed) cross-product 실행
- ``run_episode``        : 한 episode 단위 rollout 헬퍼
- ``compute_metrics``    : raw episodes → metric dict
- ``aggregate_results``  : metric dict → confidence interval / per-split / per-planner
"""
from .metrics import (
    EpisodeResult,
    aggregate_by_planner,
    aggregate_by_split,
    bootstrap_ci,
    compute_episode_metrics,
)
from .planner_eval import PlannerEvalRunner
from .rollout_runner import run_episode

__all__ = [
    "EpisodeResult",
    "compute_episode_metrics",
    "aggregate_by_planner",
    "aggregate_by_split",
    "bootstrap_ci",
    "run_episode",
    "PlannerEvalRunner",
]
