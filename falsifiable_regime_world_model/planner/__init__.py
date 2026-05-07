"""falsifiable_regime_world_model.planner — Session 11-13 산출물.

학습된 RSSM world model 위에 얹히는 "wrong-hypothesis-aware" planner 모듈.

PART2 §3.7~§3.14의 알고리즘:
    - falsification score (likelihood ratio + change-point posterior)
    - action relevance (value gap / action flip)
    - compute reallocation (current → alternative regime rollout)
    - decision modes (reactive / plan_current / plan_alternative / correct / avoid / delay / explore)

주요 공개 API
-------------
- ``WorldModelAdapter``     : 학습된 RSSM checkpoint를 planner가 부를 수 있도록 감싸는 adapter
- ``BasePlanner``           : 모든 planner의 공통 abstract interface
- ``PlannerConfig``         : planner 공통 hyperparameter
- ``PlannerEvalConfig``     : evaluation 시 사용하는 yaml 매핑 dataclass
- ``PlannerTrace``/``StepTrace`` : per-step decision trace 저장용
- ``RolloutPrediction``     : imagine() 결과 묶음
- ``CandidateActionSequence``, ``ActionSpaceSpec`` : action sampling 인터페이스
- ``ReactivePlanner``, ``FixedKPlanner``, ``AlwaysPlanPlanner``,
  ``UncertaintyGatePlanner``, ``AdaptiveLookaheadPlanner``, ``EventOnlyPlanner``,
  ``FRCWMPlanner`` : 6 baseline + ours

본 모듈은 dataset npz를 직접 읽지 않는다. 평가 시점에는 RG4FEnv를 직접 reset/step한다.
oracle/metadata leakage 방지: WorldModelAdapter는 obs dict (local_grid + scalar +
event_token + action_mask)만 받고 info의 ground-truth는 절대 input으로 사용하지 않는다.
"""
from .action_space import (
    ActionSpaceSpec,
    CandidateActionSequence,
    enumerate_action_candidates,
    sample_action_sequences,
)
from .baselines import (
    AdaptiveLookaheadPlanner,
    AlwaysPlanPlanner,
    BasePlanner,
    EventOnlyPlanner,
    FixedKPlanner,
    ReactivePlanner,
    UncertaintyGatePlanner,
)
from .config import (
    BaselinePlannerConfig,
    FRCPlannerConfig,
    PlannerConfig,
    PlannerEvalConfig,
    PlannerEvalRunSpec,
    PlannerSpec,
    SplitSpec,
)
from .frc_planner import FRCWMPlanner
from .interface import (
    BeliefState,
    ComputeAccountant,
    PlannerDecision,
    PlannerState,
    RolloutPrediction,
)
from .scoring import (
    ActionRelevanceResult,
    AlternativeRollouts,
    FalsificationContext,
    FalsificationResult,
    compute_action_relevance,
    compute_alternative_disagreement,
    compute_falsification_score,
)
from .trace import PlannerTrace, StepTrace
from .world_model_adapter import WorldModelAdapter

__all__ = [
    # adapter
    "WorldModelAdapter",
    # state / decision
    "BeliefState",
    "PlannerState",
    "PlannerDecision",
    "RolloutPrediction",
    "ComputeAccountant",
    # action space
    "ActionSpaceSpec",
    "CandidateActionSequence",
    "enumerate_action_candidates",
    "sample_action_sequences",
    # config
    "PlannerConfig",
    "BaselinePlannerConfig",
    "FRCPlannerConfig",
    "PlannerEvalConfig",
    "PlannerEvalRunSpec",
    "PlannerSpec",
    "SplitSpec",
    # scoring
    "FalsificationContext",
    "FalsificationResult",
    "ActionRelevanceResult",
    "AlternativeRollouts",
    "compute_falsification_score",
    "compute_action_relevance",
    "compute_alternative_disagreement",
    # trace
    "PlannerTrace",
    "StepTrace",
    # planners
    "BasePlanner",
    "ReactivePlanner",
    "FixedKPlanner",
    "AlwaysPlanPlanner",
    "UncertaintyGatePlanner",
    "AdaptiveLookaheadPlanner",
    "EventOnlyPlanner",
    "FRCWMPlanner",
]
