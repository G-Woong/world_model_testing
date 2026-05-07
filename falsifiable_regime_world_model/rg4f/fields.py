"""Invisible noise field 동역학.

본 모듈은 PART1 §3.5(reveal vs shift), RG4F_Environment_Plan §7(invisible field),
PART2 §3.10(control-drift)의 환경 측면을 구현한다.

핵심 원칙 (PART0 §3 §10 위반 금지):
- 한 field는 최대 ``config.field_coupling_max_dims`` (=2)개의 state dim에만 영향.
- 5개 state vector를 동시에 흔드는 field는 절대 만들지 않는다.
- field source는 직접 관측되지 않는다 (env가 obs에 노출하지 않음).
- field mean drift(small cumulative)와 event-triggered shift(abrupt)는 분리되어
  처리되며, info에 분리된 라벨(reveal_event vs shift_event)로 노출된다.
"""
from __future__ import annotations

import math
from typing import Dict, List, Tuple

import numpy as np

from .config import RG4FConfig
from .types import (
    FieldFamily,
    FieldInfoEntry,
    Position,
    StateDim,
)


# =============================================================================
# field effect 계산
# =============================================================================

def _falloff(dist: float, radius: float) -> float:
    """source ~ point 거리에 따른 영향 강도. radius 안에서는 [0, 1] 선형 감쇠.

    radius 밖이면 0. 단순한 선형 falloff은 충분히 식별성을 제공하면서도
    edge 효과가 단순(=hidden state로 추론 가능).
    """
    if dist >= radius:
        return 0.0
    return float(max(0.0, 1.0 - dist / radius))


def evaluate_field_effects(
    fields: List[FieldInfoEntry],
    agent_position: Position,
    rng: np.random.Generator,
) -> Dict[int, float]:
    """현재 step에서 모든 field가 agent state에 미친 effect를 합산.

    Returns
    -------
    effect : Dict[state_dim_index, additive_delta]
        예: {StateDim.NOISE: +0.012, StateDim.VISION: -0.005}.
        각 state dim에 들어갈 ``Δx`` 합산값.
    """
    aggregate: Dict[int, float] = {}
    for f in fields:
        dist = _euclidean(agent_position, f.source_position)
        intensity = _falloff(dist, f.radius)
        if intensity <= 0.0:
            f.last_effect = {}
            continue
        # ε_{j,t} ~ N(mu_j, sigma_j). intensity로 스케일.
        sample = float(rng.normal(f.mu, max(f.sigma, 1e-6)))
        per_field_effect: Dict[int, float] = {}
        for sdim in f.coupled_states:
            delta = intensity * sample
            per_field_effect[int(sdim)] = delta
            aggregate[int(sdim)] = aggregate.get(int(sdim), 0.0) + delta
        f.last_effect = per_field_effect
    return aggregate


def _euclidean(a: Position, b: Position) -> float:
    dr = a.row - b.row
    dc = a.col - b.col
    return math.sqrt(dr * dr + dc * dc)


# =============================================================================
# field mean dynamics
# =============================================================================

def apply_small_drift(
    fields: List[FieldInfoEntry],
    config: RG4FConfig,
    rng: np.random.Generator,
) -> bool:
    """매 step 적용되는 small cumulative drift. μ_{j,t+1} = μ_{j,t} + N(0, σ_η^2).

    Returns
    -------
    applied : bool
        실제로 drift가 한 번이라도 적용됐는지 (디버그용).
    """
    sigma = config.field_mu_drift_sigma
    if sigma <= 0.0 or not fields:
        return False
    for f in fields:
        f.mu = float(f.mu + rng.normal(0.0, sigma))
    return True


def apply_event_shift(
    fields: List[FieldInfoEntry],
    config: RG4FConfig,
    rng: np.random.Generator,
    event_kind: str,
) -> Tuple[bool, List[int]]:
    """특정 event 발생 시 일정 확률로 field mean에 abrupt shift를 가한다.

    Parameters
    ----------
    event_kind : str
        ``"room_entry"``, ``"checkpoint"``, ``"stele_activation"`` 중 하나.
        config에서 정의된 확률을 따라 shift 결정.

    Returns
    -------
    (any_shifted, shifted_field_indices)
    """
    if not config.enable_event_triggered_shift or not fields:
        return False, []

    prob_map = {
        "room_entry": config.shift_prob_per_room_entry,
        "checkpoint": config.shift_prob_per_checkpoint,
        "stele_activation": config.shift_prob_per_stele_activation,
    }
    if event_kind not in prob_map:
        # 정의되지 않은 event는 shift를 트리거하지 않는다 (silent ignore 대신 False 반환)
        return False, []
    p = prob_map[event_kind]
    shifted: List[int] = []
    for idx, f in enumerate(fields):
        if rng.random() < p:
            sign = 1.0 if rng.random() < 0.5 else -1.0
            f.mu = float(f.mu + sign * config.event_shift_delta)
            shifted.append(idx)
    return (len(shifted) > 0), shifted


# =============================================================================
# 디버그/로깅 헬퍼
# =============================================================================

def summarize_fields_for_info(fields: List[FieldInfoEntry]) -> List[Dict[str, object]]:
    """info["field_info"]에 들어갈 ground-truth 요약."""
    out: List[Dict[str, object]] = []
    for f in fields:
        out.append({
            "family": int(f.family),
            "source_row": int(f.source_position.row),
            "source_col": int(f.source_position.col),
            "radius": float(f.radius),
            "mu": float(f.mu),
            "sigma": float(f.sigma),
            "coupled_states": tuple(int(s) for s in f.coupled_states),
            "last_effect": {int(k): float(v) for k, v in f.last_effect.items()},
        })
    return out


# 외부에 노출할 StateDim enum (편의)
__all__ = [
    "evaluate_field_effects",
    "apply_small_drift",
    "apply_event_shift",
    "summarize_fields_for_info",
    "StateDim",
]
