"""Action space utilities for planner.

RG-4F의 raw action vocab은 16 (W/A/S/D + E + V±/M±/I±/N±/D± + WAIT)이다.
planner는 이 vocab 안에서 candidate action sequence를 sampling하여 imagine한다.

본 모듈은:
- ``ActionSpaceSpec``: action subset / mask 처리 / sampling 정책 dataclass.
- ``CandidateActionSequence``: 한 candidate (sequence + diagnostic).
- ``enumerate_action_candidates``: 첫 step의 모든 valid action을 candidate로 (horizon=1
  exhaustive). 작은 horizon에서는 가장 단순하고 실용적이다.
- ``sample_action_sequences``: stochastic sampling으로 candidate 생성. horizon > 1일 때
  사용. mask를 step마다 update할 수는 없으므로 첫 step에만 mask를 적용 (env rollout이
  아니라 imagine이므로 정확하지는 않지만 candidate diversity는 유지).

설계 메모
---------
- planner는 raw action만 다룬다. control-drift remap은 env가 적용한다.
  (PART2 §3.10: control-drift는 env-side action semantics regime이며, planner는 raw
  action 후보만 평가한다. effective action mismatch는 mismatch_logit으로 검출.)
- planning compute accountant 측 비용은 (n_candidates × n_samples × horizon) step.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Sequence, Tuple

import numpy as np


# =============================================================================
# 1. ActionSpaceSpec
# =============================================================================


@dataclass
class ActionSpaceSpec:
    """planner가 사용할 action subset 및 sampling 정책."""

    action_vocab: int = 16
    action_subset: Optional[Sequence[int]] = None     # None이면 전체. 실험적으로 subset 가능.
    use_action_mask: bool = True                       # env가 제공하는 action_mask를 따른다
    # WAIT action index (PART3 §3.11.5: adaptation/correction에서 wait이 cost-sensitive)
    wait_action: int = 15
    # interact action index (Action.E)
    interact_action: int = 4
    # state-adjust action range (V_PLUS=5 ~ D_MINUS=14)
    state_adjust_actions: Tuple[int, ...] = tuple(range(5, 15))
    # move action range
    move_actions: Tuple[int, ...] = (0, 1, 2, 3)

    def available_actions(
        self,
        action_mask: Optional[np.ndarray] = None,
    ) -> List[int]:
        """현재 step에서 valid한 action index 리스트.

        Parameters
        ----------
        action_mask : (16,) float array — env obs에서 받은 mask. 1.0인 index만 valid.

        Notes
        -----
        - subset이 지정되면 mask와 교집합.
        - mask가 None이면 subset 또는 전체 vocab.
        """
        if self.action_subset is not None:
            base = list(self.action_subset)
        else:
            base = list(range(self.action_vocab))
        if self.use_action_mask and action_mask is not None:
            base = [a for a in base if float(action_mask[a]) > 0.5]
        if not base:
            # 모든 mask가 0이면 fallback: WAIT만 허용
            base = [self.wait_action]
        return base


# =============================================================================
# 2. CandidateActionSequence
# =============================================================================


@dataclass
class CandidateActionSequence:
    """한 candidate. ``actions``는 horizon 길이 sequence.

    Attributes
    ----------
    actions    : (H,) np.ndarray of int (raw action index)
    source     : 후보 생성 출처 ("first_action_grid" | "random" | ...)
    weight     : 사용자 priority (optional). FRC에서 action_relevance 가중치로 활용 가능.
    """

    actions: np.ndarray
    source: str = "random"
    weight: float = 1.0

    @property
    def horizon(self) -> int:
        return int(self.actions.shape[0])


# =============================================================================
# 3. candidate generators
# =============================================================================


def enumerate_action_candidates(
    spec: ActionSpaceSpec,
    *,
    horizon: int,
    action_mask: Optional[np.ndarray] = None,
    repeat_first_action: bool = True,
) -> List[CandidateActionSequence]:
    """첫 step의 모든 valid action 각각을 candidate로 만든다.

    Parameters
    ----------
    repeat_first_action : True이면 candidate의 모든 step에 same first action을 채워
        horizon만큼 반복한다. False면 첫 step만 다양화하고 나머지는 WAIT 채움.

    Returns
    -------
    candidates : list[CandidateActionSequence] (len = |valid_actions|)
    """
    if horizon <= 0:
        raise ValueError(f"horizon must be positive, got {horizon}")
    valid = spec.available_actions(action_mask)
    out: List[CandidateActionSequence] = []
    for a in valid:
        seq = np.full((horizon,), a if repeat_first_action else spec.wait_action, dtype=np.int64)
        seq[0] = a
        out.append(CandidateActionSequence(actions=seq, source="first_action_grid"))
    return out


def sample_action_sequences(
    spec: ActionSpaceSpec,
    *,
    n_candidates: int,
    horizon: int,
    rng: np.random.Generator,
    action_mask: Optional[np.ndarray] = None,
    bias_first_action: Optional[Sequence[int]] = None,
) -> List[CandidateActionSequence]:
    """random sampling으로 candidate 생성.

    Parameters
    ----------
    bias_first_action : 지정되면 첫 step은 이 set 안에서만 sampling한다 (FRC가
        action relevance 기반으로 sub-pool을 만들 때 사용).

    Returns
    -------
    candidates : list of length n_candidates.
    """
    if horizon <= 0:
        raise ValueError(f"horizon must be positive, got {horizon}")
    if n_candidates <= 0:
        raise ValueError(f"n_candidates must be positive, got {n_candidates}")
    valid_first = spec.available_actions(action_mask)
    valid_all = (
        list(spec.action_subset) if spec.action_subset is not None
        else list(range(spec.action_vocab))
    )
    if not valid_all:
        valid_all = [spec.wait_action]
    out: List[CandidateActionSequence] = []
    bias_pool = (
        [a for a in (bias_first_action or []) if a in valid_first] or valid_first
    )
    for _ in range(n_candidates):
        seq = np.empty((horizon,), dtype=np.int64)
        seq[0] = int(rng.choice(bias_pool))
        if horizon > 1:
            # 나머지 step은 valid_all 안에서 random (action_mask는 t>0에서 알 수 없음)
            seq[1:] = rng.choice(valid_all, size=horizon - 1)
        out.append(CandidateActionSequence(actions=seq, source="random"))
    return out


def candidates_to_tensor(
    candidates: Sequence[CandidateActionSequence],
    *,
    n_samples: int,
) -> np.ndarray:
    """C candidate × S sample을 단일 (C*S, H) np.array로 묶는다.

    Returns
    -------
    arr : (C*S, H) int64
    """
    if not candidates:
        raise ValueError("empty candidates")
    H = candidates[0].horizon
    C = len(candidates)
    arr = np.empty((C * n_samples, H), dtype=np.int64)
    for c, cand in enumerate(candidates):
        for s in range(n_samples):
            arr[c * n_samples + s, :] = cand.actions
    return arr


__all__ = [
    "ActionSpaceSpec",
    "CandidateActionSequence",
    "enumerate_action_candidates",
    "sample_action_sequences",
    "candidates_to_tensor",
]
