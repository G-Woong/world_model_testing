"""Reactive (no-planning) policy primitives.

PART3 §3.22.1: Reactive policy는 world model planning을 거의 쓰지 않는 baseline.
FRC-WM도 "low falsification일 때 reactive로 동작"하므로 본 module의 ``ReactivePolicy``를
재사용한다.

설계 원칙
---------
- heuristic/keyword 기반 분기는 최대한 지양 (사용자 규칙). 단순히 head output을 이용한
  greedy reactive policy를 둔다.
- ``select_reactive_action`` 은 belief.head_outputs의 ``state_pred``/``regime_logits``를
  쓸 수 있을 때 가장 가능성 높은 next reward를 만들어내는 단일 action 후보를 score한다.
  단 horizon=1 imagine 한 번을 짧게 호출한다 (compute는 candidate × 1).
"""
from __future__ import annotations

from typing import Optional

import numpy as np

from .action_space import ActionSpaceSpec, enumerate_action_candidates, candidates_to_tensor
from .interface import BeliefState, RolloutPrediction
from .world_model_adapter import WorldModelAdapter


def select_reactive_action(
    *,
    adapter: WorldModelAdapter,
    belief: BeliefState,
    action_space: ActionSpaceSpec,
    action_mask: Optional[np.ndarray] = None,
    horizon: int = 1,
    rng: Optional[np.random.Generator] = None,
) -> int:
    """짧은 1-step lookahead로 reward를 maximize하는 raw action을 고른다.

    fallback: head가 없거나 action mask가 비면 random.
    """
    candidates = enumerate_action_candidates(
        action_space, horizon=horizon, action_mask=action_mask,
    )
    if not candidates:
        return action_space.wait_action
    arr = candidates_to_tensor(candidates, n_samples=1)
    rollout: RolloutPrediction = adapter.imagine_from_belief(
        belief, arr, horizon=horizon, n_samples=1, n_candidates=len(candidates),
    )
    val = rollout.candidate_value().detach().cpu().numpy()
    if not np.isfinite(val).any():
        if rng is not None:
            return int(rng.choice([c.actions[0] for c in candidates]))
        return int(candidates[0].actions[0])
    return int(candidates[int(np.argmax(val))].actions[0])


__all__ = ["select_reactive_action"]
