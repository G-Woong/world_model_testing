"""RG-4F dataset generator (Session 3).

train / valid / test_id / 5개 OOD split의 episode dataset을 디스크에 저장한다.

핵심 책임:
1) yaml config 로드 + CLI argparse override.
2) split-aware room-task permutation pool 분리 (train/OOD disjoint).
3) split별 RG4FConfig 변형 (param_shift / factor_recomb / field_placement / obs_shift).
4) random_uniform / random_biased behavior policy로 environment를 굴려 transition 수집.
5) episode npz + index.jsonl + episode_meta.json + 전체 manifest.json 저장.

PART0 §3 §6 / SESSION1_HANDOFF §6 / SESSION2_HANDOFF §9 정합:
- world model / RSSM / planner / agent 코드 절대 포함하지 않는다.
- 학습 loop, optimizer, training run 일절 없음.
- DreamerV3 / SOTA backbone import 없음.
- 본 script는 "환경을 굴려 transition을 모은다" 그 이상의 일을 하지 않는다.

PART0 §3 §4: 모든 수치는 yaml 또는 CLI 옵션으로만 흐른다 (magic number 금지).

사용법
------
    python scripts/generate_dataset.py --config configs/dataset_default.yaml
    python scripts/generate_dataset.py --config configs/dataset_default.yaml --dry-run
    python scripts/generate_dataset.py --config configs/dataset_default.yaml \\
        --num-train 2 --num-valid 1 --num-test 1 --num-ood-per-type 1 --overwrite
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import itertools
import json
import shutil
import sys
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import yaml

# 프로젝트 루트를 sys.path에 추가 (script가 단독 실행될 때 falsifiable_regime_world_model
# 패키지를 찾을 수 있도록)
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from collections import deque

from falsifiable_regime_world_model.rg4f import (
    Action,
    RG4FConfig,
    RG4FEnv,
    StateDim,
)
from falsifiable_regime_world_model.rg4f.serialization import EpisodeBuffer
from falsifiable_regime_world_model.rg4f.types import (
    ACTION_TO_DIRECTION,
    DIR_DELTA,
    TASK_ROOM_IDS,
    Position,
    RoomID,
    StateDim,
    TaskID,
)

try:
    from tqdm import tqdm

    _HAS_TQDM = True
except ImportError:
    _HAS_TQDM = False


# =============================================================================
# 1. friendly yaml key → RG4FConfig 정확한 필드명 변환
# =============================================================================

# yaml의 environment 섹션에는 RG4FConfig 정확한 필드명이 아닌 friendly key가 섞여 있다.
# (사용자 요구사항). RG4FConfig.from_dict는 unknown key를 거부하므로 generator가 변환한다.
_FRIENDLY_KEY_REMOVED: Tuple[str, ...] = (
    # RG4FConfig에 매핑되지 않는 metadata-only / generator-level 키
    "field_coupling_type",
    "task_permutation_mode",
)


def _yaml_env_to_rg4f_kwargs(env_section: Dict[str, Any]) -> Dict[str, Any]:
    """yaml의 environment 섹션을 RG4FConfig 정확한 필드명으로 변환한 dict로 만든다.

    변환 규칙:
        drift_strength               → field_mu_drift_sigma
        shift_probability            → shift_prob_per_room_entry / per_checkpoint /
                                       per_stele_activation 모두에 동일 값 적용
        stochastic_miscontrol_prob   → miscontrol_p_low
        field_coupling_type          → metadata only (제거)
        task_permutation_mode        → generator-level 정책 (제거)

    그 외 키는 RG4FConfig 필드명과 일치한다고 가정하고 그대로 전달한다.
    """
    out: Dict[str, Any] = {}
    for k, v in env_section.items():
        if k in _FRIENDLY_KEY_REMOVED:
            continue
        if k == "drift_strength":
            out["field_mu_drift_sigma"] = float(v)
        elif k == "shift_probability":
            out["shift_prob_per_room_entry"] = float(v)
            out["shift_prob_per_checkpoint"] = float(v)
            out["shift_prob_per_stele_activation"] = float(v)
        elif k == "stochastic_miscontrol_prob":
            out["miscontrol_p_low"] = float(v)
        else:
            out[k] = v
    return out


# =============================================================================
# 2. split-aware permutation pool 분리
# =============================================================================


def _all_24_permutations() -> List[Tuple[int, int, int, int]]:
    """4! = 24개 permutation을 lexicographic 순서로 enumerate."""
    return [tuple(p) for p in itertools.permutations((0, 1, 2, 3))]


def _build_permutation_pools(
    rng: np.random.Generator,
    train_fraction: float,
    ood_use_disjoint: bool,
) -> Tuple[List[Tuple[int, int, int, int]], List[Tuple[int, int, int, int]]]:
    """24개 permutation을 train_pool / ood_pool로 disjoint하게 분리한다.

    rng로 24개를 한 번 shuffle한 뒤 앞 K개 = train, 나머지 = ood.
    (master seed에 의해 deterministic하므로 같은 yaml + 같은 seed → 같은 분리.)

    Returns
    -------
    (train_pool, ood_pool)
        - train_pool: train/valid/test_id가 공통으로 사용
        - ood_pool: ood_room_perm 전용. ood_use_disjoint=False면 train_pool과 동일.
    """
    perms = _all_24_permutations()
    if not (0.0 < train_fraction < 1.0):
        raise ValueError(
            f"train_fraction_of_24_permutations must be in (0,1); got {train_fraction}"
        )
    rng_shuffled = list(perms)
    rng.shuffle(rng_shuffled)
    K = max(
        1, min(len(rng_shuffled) - 1, int(round(len(rng_shuffled) * train_fraction)))
    )
    train_pool = rng_shuffled[:K]
    ood_pool = rng_shuffled[K:] if ood_use_disjoint else list(rng_shuffled)
    if ood_use_disjoint and not ood_pool:
        raise ValueError(
            "ood_pool is empty; reduce train_fraction_of_24_permutations or disable disjoint."
        )
    return train_pool, ood_pool


# =============================================================================
# 3. behavior policy
# =============================================================================

_STATE_ADJUST_ACTIONS: Tuple[Action, ...] = (
    Action.V_PLUS,
    Action.V_MINUS,
    Action.M_PLUS,
    Action.M_MINUS,
    Action.I_PLUS,
    Action.I_MINUS,
    Action.N_PLUS,
    Action.N_MINUS,
    Action.D_PLUS,
    Action.D_MINUS,
)
_MOVE_ACTION_LIST: Tuple[Action, ...] = (Action.W, Action.A, Action.S, Action.D)


def _build_action_probs(policy: str, num_actions: int = 16) -> np.ndarray:
    """behavior policy 이름에 따라 정적 action 확률 분포를 만든다.

    - random_uniform : 모든 action 균일.
    - random_biased  : movement 55% / E 15% / state adjust 30% / WAIT 0%.
                       movement 4개 / state adjust 10개에 균등 분배.

    task_probe는 정적 분포가 아니라 ``_TaskProbePolicy``가 동적으로 결정한다.
    단, task_probe 안에서 epsilon-fallback으로 random_biased 분포를 재사용하므로
    본 함수는 task_probe 호출 시에도 random_biased로 변환되어 호출된다.
    """
    if policy == "task_probe":
        # task_probe는 정적 분포가 아님. fallback용으로 random_biased를 반환.
        policy = "random_biased"
    p = np.zeros(num_actions, dtype=np.float64)
    if policy == "random_uniform":
        p[:] = 1.0 / num_actions
    elif policy == "random_biased":
        move_total = 0.55
        e_total = 0.15
        adj_total = 0.30
        for a in _MOVE_ACTION_LIST:
            p[int(a)] = move_total / 4.0
        p[int(Action.E)] = e_total
        for a in _STATE_ADJUST_ACTIONS:
            p[int(a)] = adj_total / float(len(_STATE_ADJUST_ACTIONS))
        # WAIT은 0% (data collection은 WAIT보다 의미 있는 action 위주)
    else:
        raise ValueError(
            f"Unknown behavior_policy: {policy!r}. "
            f"Allowed: random_uniform | random_biased | task_probe"
        )
    p = p / p.sum()
    return p


def _sample_action(rng: np.random.Generator, probs: np.ndarray) -> int:
    """확률 분포에서 하나의 action index를 샘플링."""
    return int(rng.choice(len(probs), p=probs))


# =============================================================================
# 3.5 task_probe policy: scripted data collection (NOT an evaluation agent)
# =============================================================================
#
# WARNING: task_probe is a SCRIPTED data-collection policy used to enrich
# transition coverage of A/B/C/D events for world-model pretraining. It is
# explicitly NOT:
#   * an evaluation agent (do not report task_probe success as agent metric)
#   * an FRC-WM planner
#   * an uncertainty/adaptive baseline
#
# Behavior summary (per env.step):
#   1) epsilon prob: pure random_biased fallback (다양성 유지).
#   2) target room 결정: 가장 적게 방문한 task room, 또는 stuck/resample 시 변경.
#   3) target room 안: 방의 task object들 (pieces/steles/altars/tiles/door) 중
#      가장 가까운 cell로 greedy move; 인접/같은 칸이면 E 확률 상승.
#   4) target room 밖: 해당 방의 door로 greedy move.
#   5) state-adjust prob: 위 결정 대신 state-adjust action 한 개 sampling.
#   6) stuck (최근 stuck_window tick 동안 위치 다양성 < 3): target_room resample.
#
# Oracle 사용 금지:
#   - true_state, true_regime, target_band center/half_width 같은 hidden ground
#     truth는 절대 직접 보지 않는다.
#   - 사용 가능한 정보는 grid layout (정적), agent.position, agent.current_room,
#     episode permutation (room→task), task object positions (room layout의 일부)
#     로 한정된다.

_TASK_OBJECT_LABELS: Tuple[str, ...] = (
    "pieces",
    "steles",
    "altar",
    "altars",
    "door",
    "doors",
    "tiles",
)


class _RandomBehaviorPolicy:
    """random_uniform / random_biased를 wrapping한 stateless policy."""

    name: str = "random"

    def __init__(self, action_probs: np.ndarray) -> None:
        self._probs = action_probs

    def reset(
        self,
        env: "RG4FEnv",
        episode_seed: int,
        rng: np.random.Generator,
    ) -> None:
        del env, episode_seed, rng

    def select(
        self,
        env: "RG4FEnv",
        rng: np.random.Generator,
        step: int,
    ) -> int:
        del env, step
        return int(rng.choice(len(self._probs), p=self._probs))


class _TaskProbePolicy:
    """방 탐색 + object 접근 + E + state-adjust를 균형있게 섞는 데이터 수집 policy."""

    name: str = "task_probe"

    def __init__(
        self,
        epsilon: float,
        interact_prob_near_object: float,
        state_adjust_prob: float,
        stuck_window: int,
        room_resample_prob: float,
        prefer_unvisited_rooms: bool,
        fallback_probs: np.ndarray,
    ) -> None:
        self.epsilon = float(epsilon)
        self.interact_prob_near_object = float(interact_prob_near_object)
        self.state_adjust_prob = float(state_adjust_prob)
        self.stuck_window = int(stuck_window)
        self.room_resample_prob = float(room_resample_prob)
        self.prefer_unvisited_rooms = bool(prefer_unvisited_rooms)
        self._fallback_probs = fallback_probs
        # episode-level 상태 (reset에서 채움)
        self._target_room: Optional[RoomID] = None
        self._room_visit_count: Dict[RoomID, int] = {}
        self._recent_positions: deque = deque(maxlen=self.stuck_window)
        self._last_resample_step: int = -(10**9)

    def reset(
        self,
        env: "RG4FEnv",
        episode_seed: int,
        rng: np.random.Generator,
    ) -> None:
        del env, episode_seed, rng
        self._target_room = None
        self._room_visit_count = {r: 0 for r in TASK_ROOM_IDS}
        self._recent_positions = deque(maxlen=self.stuck_window)
        self._last_resample_step = -(10**9)

    def _sample_state_adjust(self, rng: np.random.Generator) -> int:
        idx = int(rng.integers(0, len(_STATE_ADJUST_ACTIONS)))
        return int(_STATE_ADJUST_ACTIONS[idx])

    def _greedy_move_toward(
        self,
        layout,
        cur_pos: Position,
        target_pos: Position,
        rng: np.random.Generator,
    ) -> int:
        """현재 위치에서 target 방향으로 한 칸 이동하는 movement action을 선택.

        traversable 칸을 우선 시도. 모두 막히면 random movement로 fallback.
        control-drift remap은 고려하지 않는다 (env가 effective action을 따로 기록).
        """
        dr = int(target_pos.row - cur_pos.row)
        dc = int(target_pos.col - cur_pos.col)
        candidates: List[Action] = []
        # 더 큰 차이 방향을 먼저 시도 → 빠른 거리 감소
        if abs(dr) >= abs(dc):
            if dr < 0:
                candidates.append(Action.W)
            elif dr > 0:
                candidates.append(Action.S)
            if dc < 0:
                candidates.append(Action.A)
            elif dc > 0:
                candidates.append(Action.D)
        else:
            if dc < 0:
                candidates.append(Action.A)
            elif dc > 0:
                candidates.append(Action.D)
            if dr < 0:
                candidates.append(Action.W)
            elif dr > 0:
                candidates.append(Action.S)
        # traversable 후보를 우선 반환
        for a in candidates:
            direction = ACTION_TO_DIRECTION[a]
            drow, dcol = DIR_DELTA[direction]
            nxt = cur_pos.shifted(drow, dcol)
            if layout.is_traversable(nxt):
                return int(a)
        # 모두 막힘 → 4방향 중 traversable한 칸을 random 선택
        movable: List[int] = []
        for a in _MOVE_ACTION_LIST:
            direction = ACTION_TO_DIRECTION[a]
            drow, dcol = DIR_DELTA[direction]
            nxt = cur_pos.shifted(drow, dcol)
            if layout.is_traversable(nxt):
                movable.append(int(a))
        if movable:
            return int(movable[int(rng.integers(0, len(movable)))])
        return int(_MOVE_ACTION_LIST[int(rng.integers(0, len(_MOVE_ACTION_LIST)))])

    def _collect_object_positions(self, episode, task_id: TaskID) -> List[Position]:
        inst = episode.task_instances.get(task_id)
        if inst is None:
            return []
        out: List[Position] = []
        for label in _TASK_OBJECT_LABELS:
            for p in inst.object_positions.get(label, []):
                out.append(p)
        return out

    def _select_target_room(
        self,
        rng: np.random.Generator,
    ) -> RoomID:
        # visit count 기준 정렬 (적게 방문한 것 우선); tie는 random
        rooms = list(TASK_ROOM_IDS)
        if self.prefer_unvisited_rooms:
            unvisited = [r for r in rooms if self._room_visit_count[r] == 0]
            if unvisited:
                return unvisited[int(rng.integers(0, len(unvisited)))]
        # 가장 적은 visit_count를 가진 방들 중 random 선택
        min_count = min(self._room_visit_count[r] for r in rooms)
        candidates = [r for r in rooms if self._room_visit_count[r] == min_count]
        return candidates[int(rng.integers(0, len(candidates)))]

    def select(
        self,
        env: "RG4FEnv",
        rng: np.random.Generator,
        step: int,
    ) -> int:
        # epsilon fallback (다양성 + 비결정성 보장)
        if rng.random() < self.epsilon:
            return int(rng.choice(len(self._fallback_probs), p=self._fallback_probs))

        episode = (
            env._episode
        )  # noqa: SLF001 (generator는 env 동결 상태에서 직접 접근 허용)
        agent = env._agent  # noqa: SLF001
        if episode is None or agent is None:
            return int(rng.choice(len(self._fallback_probs), p=self._fallback_probs))
        layout = episode.layout
        cur_pos: Position = agent.position
        cur_room: RoomID = agent.current_room

        # 방문 카운트 업데이트
        if cur_room in self._room_visit_count:
            self._room_visit_count[cur_room] += 1

        # stuck 감지: 최근 stuck_window tick 동안 위치 다양성 < 3
        self._recent_positions.append(cur_pos.as_tuple())
        is_stuck = (
            len(self._recent_positions) >= self.stuck_window
            and len(set(self._recent_positions)) < 3
            and (step - self._last_resample_step) > self.stuck_window // 2
        )

        # target room 결정/갱신
        need_resample = (
            self._target_room is None
            or is_stuck
            or rng.random() < self.room_resample_prob
        )
        if need_resample:
            self._target_room = self._select_target_room(rng)
            self._last_resample_step = step

        # state-adjust 비율 유지 (target/위치와 무관하게 일정 비율로 sampling)
        if rng.random() < self.state_adjust_prob:
            return self._sample_state_adjust(rng)

        # 현재 방이 target room인가?
        if cur_room == self._target_room and cur_room in episode.permutation:
            task_id = episode.permutation[cur_room]
            objects = self._collect_object_positions(episode, task_id)
            if objects:
                # 가장 가까운 object 선택 (Manhattan distance)
                target = min(
                    objects,
                    key=lambda p: abs(p.row - cur_pos.row) + abs(p.col - cur_pos.col),
                )
                dist = abs(target.row - cur_pos.row) + abs(target.col - cur_pos.col)
                # 같은 칸 또는 인접 칸이면 interact 우선
                if dist <= 1:
                    if rng.random() < self.interact_prob_near_object:
                        return int(Action.E)
                # 더 가까이 이동
                return self._greedy_move_toward(layout, cur_pos, target, rng)
            # object가 없는 task_id (이론상 발생 안 함) — fallback
            return int(rng.choice(len(self._fallback_probs), p=self._fallback_probs))

        # 방 밖 (corridor / central_hall / 다른 task room): target room의 door로 이동
        door = (
            layout.door_positions.get(self._target_room) if self._target_room else None
        )
        if door is not None:
            return self._greedy_move_toward(layout, cur_pos, door, rng)
        # door 정보가 없으면 fallback
        return int(rng.choice(len(self._fallback_probs), p=self._fallback_probs))


# =============================================================================
# 3.6 task_success_curriculum policy: scripted success trajectory collector
# =============================================================================
#
# WARNING: task_success_curriculum is a SCRIPTED data-collection policy used to
# enrich success / near-success / value / action-relevance supervision for
# world-model training. It is explicitly NOT:
#   * an evaluation agent (results MUST NOT be reported as agent metric)
#   * an FRC-WM planner / RSSM rollout
#   * an uncertainty / adaptive baseline
#   * a "best path" oracle that bypasses learning
#
# Privilege level (configurable via yaml `task_success_curriculum.privilege_level`):
#   * non_oracle : task object positions만 사용. policy가 task progression /
#                  state value를 보지 않음. → A/B/C 성공률 매우 낮음.
#   * weak_oracle (DEFAULT): episode parameters의 정답 ordering (Task A weight,
#                  Task B vision-positive labels) + target_band center +
#                  current state value (i_t/m_t/n_t)를 plus/minus 방향 결정에
#                  사용. → A/B/C/D 성공률 0.40~0.60 가능.
#   * strong_oracle : 추가로 control_mode (true_regime) 직접 보정. 본 코드에서는
#                     구현하지 않음 (학습 데이터에 regime ID를 노출하면 평가가 무너짐).
#
# Mode (config의 mode_weights로 episode마다 sampling):
#   task_success_A/B/C/D : 한 task에 집중하여 완료 시도
#   task_success_all      : 4 task를 순차적으로 완료 시도 (all_done_rate 기여)
#   random_biased_fallback: 의도적 실패/방황 데이터 유지

_TASK_TO_ROOM_ID_KEYS = (RoomID.NORTH, RoomID.SOUTH, RoomID.EAST, RoomID.WEST)


class _TaskSuccessCurriculumPolicy:
    """Task-specific scripted probe로 success/near-success trajectory 생성.

    weak_oracle 기본: episode parameters의 task-specific privileged info
    (정답 ordering, vision-positive labels, target_band center)와 current
    state value (i_t/m_t/n_t)를 plus/minus 방향 결정에 사용.

    이는 평가 agent가 아니다. 본 dataset은 학습 단계에서 trajectory enrichment용으로만
    사용되며, evaluation은 반드시 별도 환경에서 수행해야 한다.
    """

    name: str = "task_success_curriculum"

    # v5 mode set (단일 fixed order 강제 금지)
    _ALL_MODES: Tuple[str, ...] = (
        "all_task_random_order",
        "all_task_easy_first",
        "all_task_hard_first",
        "all_task_balanced_cycle",
        "per_task_probe_A",
        "per_task_probe_B",
        "per_task_probe_C",
        "per_task_probe_D",
        "random_biased_fallback",
    )

    def __init__(
        self,
        epsilon: float,
        state_sweep_prob: float,
        interact_prob_near_object: float,
        stuck_window: int,
        room_resample_prob: float,
        failure_exploration_prob: float,
        privilege_level: str,
        mode_weights: Dict[str, float],
        task_budgets: Dict[str, int],
        max_retry_per_task: int,
        a_altar_sweep_step: float,
        a_altar_sweep_max_E_per_value: int,
        b_use_label_oracle: bool,
        fallback_probs: np.ndarray,
    ) -> None:
        self.epsilon = float(epsilon)
        self.state_sweep_prob = float(state_sweep_prob)
        self.interact_prob_near_object = float(interact_prob_near_object)
        self.stuck_window = int(stuck_window)
        self.room_resample_prob = float(room_resample_prob)
        self.failure_exploration_prob = float(failure_exploration_prob)
        self.privilege_level = str(privilege_level)
        self._fallback_probs = fallback_probs
        # task별 budget (yaml 또는 default)
        self.task_budgets: Dict[int, int] = {
            0: int(task_budgets.get("A", 420)),
            1: int(task_budgets.get("B", 480)),
            2: int(task_budgets.get("C", 360)),
            3: int(task_budgets.get("D", 200)),
        }
        self.max_retry_per_task = int(max_retry_per_task)
        self.a_altar_sweep_step = float(a_altar_sweep_step)
        self.a_altar_sweep_max_E_per_value = int(a_altar_sweep_max_E_per_value)
        self.b_use_label_oracle = bool(b_use_label_oracle)

        # mode_weights normalize
        modes = list(self._ALL_MODES)
        weights = np.array(
            [float(mode_weights.get(m, 0.0)) for m in modes], dtype=np.float64
        )
        total = float(weights.sum())
        if total <= 0:
            weights = np.ones_like(weights) / len(weights)
        else:
            weights = weights / total
        self._mode_names = modes
        self._mode_weights = weights

        # episode-level 상태
        self._mode: str = "all_task_random_order"
        self._task_order: List[int] = []  # 이번 episode의 task 시도 순서 (4-tuple)
        self._task_order_str: str = ""  # 메타데이터 기록용 ("ABCD" / "DBCA" 등)
        self._task_attempt_ticks: Dict[int, int] = {0: 0, 1: 0, 2: 0, 3: 0}
        self._task_timeout: Dict[int, int] = {0: 0, 1: 0, 2: 0, 3: 0}
        self._task_retry_count: Dict[int, int] = {0: 0, 1: 0, 2: 0, 3: 0}
        self._task_giveup: Dict[int, bool] = {}
        self._target_task: Optional[int] = None
        # Task A altar sweep 상태 (target_band center 직접 사용 금지 → sweep)
        # i_t를 -0.20 → -0.19 → ... → +0.20 grid로 sweep하며 각 grid에서 E 시도.
        self._a_altar_sweep_target_idx: int = 0  # 현재 sweep 중인 grid index
        self._a_altar_e_count_at_value: int = 0
        # Task B label oracle 미사용 시: stele toggle 후 dv 관찰
        self._b_initial_v: Optional[float] = None
        self._b_last_toggled: Optional[int] = None
        self._b_observed_positive: List[Optional[bool]] = [None, None, None, None]
        self._b_re_toggle_pending: List[bool] = [False, False, False, False]
        # balanced_cycle: round-robin 순환용 cursor
        self._cycle_cursor: int = 0
        self._cycle_room_steps_per_task: int = (
            60  # task당 round 60 tick (총 240 tick × ~6 round = 1440)
        )
        self._recent_positions: deque = deque(maxlen=self.stuck_window)

    def reset(
        self,
        env: "RG4FEnv",
        episode_seed: int,
        rng: np.random.Generator,
    ) -> None:
        del env, episode_seed
        # mode를 episode마다 sampling
        idx = int(rng.choice(len(self._mode_names), p=self._mode_weights))
        self._mode = str(self._mode_names[idx])
        # failure_exploration_prob 추가 적용
        if (
            self._mode != "random_biased_fallback"
            and rng.random() < self.failure_exploration_prob
        ):
            self._mode = "random_biased_fallback"

        # task_order 결정 (mode에 따라)
        if self._mode == "all_task_random_order":
            order = [0, 1, 2, 3]
            rng.shuffle(order)
            self._task_order = list(order)
        elif self._mode == "all_task_easy_first":
            self._task_order = [3, 2, 1, 0]  # D → C → B → A
        elif self._mode == "all_task_hard_first":
            self._task_order = [0, 2, 1, 3]  # A → C → B → D (v4 default)
        elif self._mode == "all_task_balanced_cycle":
            # cycle 모드는 어느 task가 first인지 episode마다 random rotation
            base = [0, 1, 2, 3]
            rng.shuffle(base)
            self._task_order = list(base)
        elif self._mode == "per_task_probe_A":
            self._task_order = [0]
        elif self._mode == "per_task_probe_B":
            self._task_order = [1]
        elif self._mode == "per_task_probe_C":
            self._task_order = [2]
        elif self._mode == "per_task_probe_D":
            self._task_order = [3]
        else:  # random_biased_fallback
            self._task_order = []
        self._task_order_str = "".join("ABCD"[t] for t in self._task_order) or "RND"

        # 진행 트래킹 초기화
        self._task_attempt_ticks = {0: 0, 1: 0, 2: 0, 3: 0}
        self._task_timeout = {0: 0, 1: 0, 2: 0, 3: 0}
        self._task_retry_count = {0: 0, 1: 0, 2: 0, 3: 0}
        self._target_task = self._task_order[0] if self._task_order else None
        self._task_giveup = {0: False, 1: False, 2: False, 3: False}
        self._recent_positions = deque(maxlen=self.stuck_window)
        self._a_altar_sweep_target_idx = 0
        self._a_altar_e_count_at_value = 0
        self._b_initial_v = None
        self._b_last_toggled = None
        self._b_observed_positive = [None, None, None, None]
        self._b_re_toggle_pending = [False, False, False, False]
        self._cycle_cursor = 0

    def get_collector_metadata(self) -> Dict[str, Any]:
        """episode_meta에 기록할 collector mode + task_order + budget usage."""
        return {
            "collector_mode": self._mode,
            "task_order_planned": list(self._task_order),
            "task_order_str": self._task_order_str,
            "task_attempt_ticks": {
                "A": int(self._task_attempt_ticks[0]),
                "B": int(self._task_attempt_ticks[1]),
                "C": int(self._task_attempt_ticks[2]),
                "D": int(self._task_attempt_ticks[3]),
            },
            "task_timeout": {
                "A": int(self._task_timeout[0]),
                "B": int(self._task_timeout[1]),
                "C": int(self._task_timeout[2]),
                "D": int(self._task_timeout[3]),
            },
            "task_retry_count": {
                "A": int(self._task_retry_count[0]),
                "B": int(self._task_retry_count[1]),
                "C": int(self._task_retry_count[2]),
                "D": int(self._task_retry_count[3]),
            },
            "task_budgets": {
                "A": int(self.task_budgets[0]),
                "B": int(self.task_budgets[1]),
                "C": int(self.task_budgets[2]),
                "D": int(self.task_budgets[3]),
            },
            "privilege_level": self.privilege_level,
            "b_use_label_oracle": bool(self.b_use_label_oracle),
        }

    # ---- helpers ----

    def _sample_state_adjust(self, rng: np.random.Generator) -> int:
        idx = int(rng.integers(0, len(_STATE_ADJUST_ACTIONS)))
        return int(_STATE_ADJUST_ACTIONS[idx])

    def _greedy_move_toward(
        self,
        layout,
        cur_pos: Position,
        target_pos: Position,
        rng: np.random.Generator,
    ) -> int:
        dr = int(target_pos.row - cur_pos.row)
        dc = int(target_pos.col - cur_pos.col)
        candidates: List[Action] = []
        if abs(dr) >= abs(dc):
            if dr < 0:
                candidates.append(Action.W)
            elif dr > 0:
                candidates.append(Action.S)
            if dc < 0:
                candidates.append(Action.A)
            elif dc > 0:
                candidates.append(Action.D)
        else:
            if dc < 0:
                candidates.append(Action.A)
            elif dc > 0:
                candidates.append(Action.D)
            if dr < 0:
                candidates.append(Action.W)
            elif dr > 0:
                candidates.append(Action.S)
        for a in candidates:
            direction = ACTION_TO_DIRECTION[a]
            drow, dcol = DIR_DELTA[direction]
            nxt = cur_pos.shifted(drow, dcol)
            if layout.is_traversable(nxt):
                return int(a)
        movable: List[int] = []
        for a in _MOVE_ACTION_LIST:
            direction = ACTION_TO_DIRECTION[a]
            drow, dcol = DIR_DELTA[direction]
            nxt = cur_pos.shifted(drow, dcol)
            if layout.is_traversable(nxt):
                movable.append(int(a))
        if movable:
            return int(movable[int(rng.integers(0, len(movable)))])
        return int(_MOVE_ACTION_LIST[int(rng.integers(0, len(_MOVE_ACTION_LIST)))])

    def _find_room_for_task(self, episode, task_id: int) -> Optional[RoomID]:
        for room, tid in episode.permutation.items():
            if int(tid) == int(task_id):
                return room
        return None

    def _select_target_task(
        self,
        env: "RG4FEnv",
        step: int,
        rng: np.random.Generator,
    ) -> Optional[int]:
        """현재 mode + episode progress + task_order에 따라 target task 선택.

        v5: 단일 fixed difficulty_order를 강제하지 않는다.
        - all_task_*: episode 시작 시 sampling된 self._task_order를 그대로 따른다.
        - per_task_probe_X: 단일 task만.
        - all_task_balanced_cycle: round-robin으로 task room을 _cycle_room_steps_per_task tick씩 순환.
        - random_biased_fallback: None 반환 → caller가 random fallback.
        """
        if self._mode == "random_biased_fallback":
            return None
        if not self._task_order:
            return None
        tasks_done = {
            int(tid): bool(env._tasks_by_id[tid].is_completed())  # noqa: SLF001
            for tid in env._tasks_by_id  # noqa: SLF001
        }

        # balanced_cycle: 시간 기반 round-robin
        if self._mode == "all_task_balanced_cycle":
            cycle_idx = (step // max(1, self._cycle_room_steps_per_task)) % len(
                self._task_order
            )
            tid = int(self._task_order[cycle_idx])
            if not tasks_done.get(tid, False) and not self._task_giveup[tid]:
                return tid
            # 이번 cycle slot의 task가 완료/포기 → 다음 미완료 task로 fallback
            for tid2 in self._task_order:
                if (
                    not tasks_done.get(int(tid2), False)
                    and not self._task_giveup[int(tid2)]
                ):
                    return int(tid2)
            return None

        # 일반 순서 모드 (random_order / easy_first / hard_first / per_task_probe_*)
        # task_order 순서대로 미완료/안 포기한 task 선택
        for tid in self._task_order:
            tid = int(tid)
            if not tasks_done.get(tid, False) and not self._task_giveup[tid]:
                return tid

        # 모두 완료/포기 → 남은 시간에 retry 가능한 task 찾기
        for tid in self._task_order:
            tid = int(tid)
            if (
                not tasks_done.get(tid, False)
                and self._task_retry_count[tid] < self.max_retry_per_task
            ):
                # giveup 해제 + retry
                self._task_giveup[tid] = False
                self._task_retry_count[tid] += 1
                self._task_attempt_ticks[tid] = 0
                return tid
        return None

    # ---- task-specific probes (weak_oracle) ----

    def _task_a_action(
        self,
        env: "RG4FEnv",
        rng: np.random.Generator,
    ) -> int:
        """v5 Task A: weight ordering은 cue layer로 노출되므로 사용 가능 (weak hint).
        단 altar τ_i (target_band center)는 oracle이므로 직접 사용 금지.
        대신 systematic sweep (i를 -0.20 ~ +0.20 grid로 한 칸씩 이동하며 매번 E 시도).
        """
        agent = env._agent  # noqa: SLF001
        episode = env._episode  # noqa: SLF001
        layout = episode.layout
        task = env._tasks_by_id[TaskID.TASK_A]  # noqa: SLF001
        inst = task.instance
        n_pieces = len(inst.object_positions["pieces"])
        # piece weight (cue layer로 weak hint이라 환경이 의도적으로 노출함 — 사용 가능)
        weights = [float(inst.parameters[f"piece_weight_{j}"]) for j in range(n_pieces)]
        correct_order = sorted(range(n_pieces), key=lambda j: -weights[j])
        progress = list(task._used_pieces)  # noqa: SLF001
        m_t = float(agent.state_vec[int(StateDim.MOBILITY)])

        # mobility recovery (현재 m 값을 보고 결정 — scalar obs는 합법적 정보)
        # m < -0.50: 거의 강제 (cd 매우 큼). m < -0.30: 강한 권장.
        if m_t < -0.80:
            return int(Action.M_PLUS)
        if len(progress) < n_pieces:
            if m_t < -0.50 and rng.random() < 0.90:
                return int(Action.M_PLUS)
            if m_t < -0.30 and rng.random() < 0.70:
                return int(Action.M_PLUS)
        else:
            # altar phase: cooldown 부담을 줄이기 위해 -0.10까지 회복
            if m_t < -0.10:
                return int(Action.M_PLUS)

        if len(progress) < n_pieces:
            next_idx = correct_order[len(progress)]
            target = inst.object_positions["pieces"][next_idx]
            if agent.position == target:
                return int(Action.E)
            return self._greedy_move_toward(layout, agent.position, target, rng)

        # 모든 piece 픽업: altar로 이동 + i_t를 systematic sweep으로 시도.
        # τ_i (target_band center)는 직접 사용 금지. -0.20 ~ +0.20 grid를 0.01 step으로 sweep.
        altar_positions = inst.object_positions["altar"]
        target = altar_positions[0]
        if agent.position != target:
            return self._greedy_move_toward(layout, agent.position, target, rng)

        # altar 위: systematic sweep
        # i_t를 sweep grid의 현재 target_value로 이동 → E 시도 → 다음 grid로
        # grid: -0.20 + idx * 0.01 (idx=0..40). 현재 idx에서 i를 맞추기까지는 I_PLUS/I_MINUS.
        i_t = float(agent.state_vec[int(StateDim.INTERACTION)])
        # current sweep target value
        sweep_lo, sweep_hi = -0.20, 0.20
        n_grid = int(round((sweep_hi - sweep_lo) / self.a_altar_sweep_step)) + 1
        if self._a_altar_sweep_target_idx >= n_grid:
            self._a_altar_sweep_target_idx = 0
            self._a_altar_e_count_at_value = 0
        target_i = sweep_lo + self._a_altar_sweep_target_idx * self.a_altar_sweep_step
        diff = target_i - i_t
        # 충분히 가까우면 (state_adjust_delta 절반 이내) E 시도
        delta = float(env.config.state_adjust_delta)
        if abs(diff) <= delta * 0.6:
            self._a_altar_e_count_at_value += 1
            # max E try 후 다음 grid로 이동 (band miss는 fail counter만 증가; 환경은 종료 안 함)
            if self._a_altar_e_count_at_value >= self.a_altar_sweep_max_E_per_value:
                self._a_altar_sweep_target_idx += 1
                self._a_altar_e_count_at_value = 0
            return int(Action.E)
        # 아직 거리 있음: I_PLUS / I_MINUS로 한 step
        return int(Action.I_PLUS) if diff > 0 else int(Action.I_MINUS)

    def _task_b_action(
        self,
        env: "RG4FEnv",
        rng: np.random.Generator,
    ) -> int:
        """v5 Task B: vision-positive label oracle 사용 금지 (b_use_label_oracle=false 기본).
        대안: 모든 stele를 한 번 toggle ON → v 변화 관찰 → 잘못된 (Δv < 0) stele를 다시 toggle OFF.
        이 방식은 환경의 자연스러운 추론 (stele toggle 후 v 변화는 obs로 노출됨)에 기반.
        """
        agent = env._agent  # noqa: SLF001
        episode = env._episode  # noqa: SLF001
        layout = episode.layout
        task = env._tasks_by_id[TaskID.TASK_B]  # noqa: SLF001
        inst = task.instance
        n = len(inst.object_positions["steles"])
        on_states = list(task._stele_on)  # noqa: SLF001
        v_t = float(agent.state_vec[int(StateDim.VISION)])

        # initial v 기록 (첫 호출 시)
        if self._b_initial_v is None:
            self._b_initial_v = v_t

        # 마지막 toggle 후 dv 관찰
        if self._b_last_toggled is not None:
            k_prev = int(self._b_last_toggled)
            # toggle 직후 ON 상태에서 v가 증가 / 감소했는지 평가
            # initial_v 대비 누적 변화 + 직전 step 비교 (간단히 last_v 추적)
            # 본 구현은 단순: 마지막 toggle 후 v가 initial보다 높아졌는지로 추정
            if self._b_observed_positive[k_prev] is None:
                # 약한 추정: v가 initial보다 +0.01 이상 → positive로 분류
                # (v_history는 task가 매 step push하므로 dv 누적 신호)
                self._b_observed_positive[k_prev] = bool(v_t - self._b_initial_v > 0.01)
                # 음의 변화면 retoggle pending
                if not self._b_observed_positive[k_prev] and on_states[k_prev]:
                    self._b_re_toggle_pending[k_prev] = True
            self._b_last_toggled = None

        if self.b_use_label_oracle:
            # weak_oracle 옵션: 정답 label 사용 (debug 모드)
            positive = [bool(inst.parameters[f"stele_positive_{k}"]) for k in range(n)]
            mismatch_idx = [k for k in range(n) if positive[k] != on_states[k]]
            if mismatch_idx:
                target_k = min(
                    mismatch_idx,
                    key=lambda k: abs(
                        inst.object_positions["steles"][k].row - agent.position.row
                    )
                    + abs(inst.object_positions["steles"][k].col - agent.position.col),
                )
                target = inst.object_positions["steles"][target_k]
                if agent.position == target:
                    self._b_last_toggled = target_k
                    return int(Action.E)
                return self._greedy_move_toward(layout, agent.position, target, rng)
        else:
            # NON-ORACLE: toggle-then-observe
            # phase 1: 아직 toggle 안 한 stele 또는 retoggle pending인 stele
            untoggled = [k for k in range(n) if self._b_observed_positive[k] is None]
            retoggle = [k for k in range(n) if self._b_re_toggle_pending[k]]
            target_k: Optional[int] = None
            if untoggled:
                # 가장 가까운 untoggled
                target_k = min(
                    untoggled,
                    key=lambda k: abs(
                        inst.object_positions["steles"][k].row - agent.position.row
                    )
                    + abs(inst.object_positions["steles"][k].col - agent.position.col),
                )
            elif retoggle:
                target_k = min(
                    retoggle,
                    key=lambda k: abs(
                        inst.object_positions["steles"][k].row - agent.position.row
                    )
                    + abs(inst.object_positions["steles"][k].col - agent.position.col),
                )
                # retoggle pending 처리: 도달 후 toggle하면 OFF 됨
            if target_k is not None:
                target = inst.object_positions["steles"][target_k]
                if agent.position == target:
                    self._b_last_toggled = target_k
                    if self._b_re_toggle_pending[target_k]:
                        self._b_re_toggle_pending[target_k] = False
                    return int(Action.E)
                return self._greedy_move_toward(layout, agent.position, target, rng)

        # 모든 stele toggle 처리 완료 → door로 이동 + mobility/vision_stable 처리
        door = inst.object_positions["door"][0]
        if agent.position != door:
            return self._greedy_move_toward(layout, agent.position, door, rng)
        # door 위: mobility band (gate=0.02)는 obs (m_t) 기반, oracle 아님
        m_t = float(agent.state_vec[int(StateDim.MOBILITY)])
        gate = float(env.config.task_b_mobility_gate_half_width)
        if abs(m_t) > gate * 0.9:
            return int(Action.M_PLUS) if m_t < 0 else int(Action.M_MINUS)
        # vision stable: task의 vision_history (env가 매 step 누적; obs와 동등)
        v_history = list(task._vision_history)  # noqa: SLF001
        need = int(env.config.task_b_vision_stable_ticks)
        v_stable = len(v_history) >= need + 1 and all(
            abs(v_history[i + 1] - v_history[i]) < 1e-9 for i in range(-(need + 1), -1)
        )
        if not v_stable:
            return int(Action.WAIT)
        return int(Action.E)

    def _task_c_action(
        self,
        env: "RG4FEnv",
        rng: np.random.Generator,
    ) -> int:
        agent = env._agent  # noqa: SLF001
        episode = env._episode  # noqa: SLF001
        layout = episode.layout
        task = env._tasks_by_id[TaskID.TASK_C]  # noqa: SLF001
        inst = task.instance
        n = len(inst.object_positions["steles"])
        unactivated = [k for k in range(n) if not task._activated[k]]  # noqa: SLF001
        if not unactivated:
            return int(Action.WAIT)  # 이미 완료
        # 가장 가까운 미활성 stele
        target_k = min(
            unactivated,
            key=lambda k: abs(
                inst.object_positions["steles"][k].row - agent.position.row
            )
            + abs(inst.object_positions["steles"][k].col - agent.position.col),
        )
        target = inst.object_positions["steles"][target_k]
        n_t = float(agent.state_vec[int(StateDim.NOISE)])
        n_band = float(env.config.task_c_noise_zero_half_width)

        if agent.position == target:
            # stele 위: noise band 안이면 E, 아니면 sweep
            if abs(n_t) <= n_band * 0.9:
                return int(Action.E)
            return int(Action.N_MINUS) if n_t > 0 else int(Action.N_PLUS)
        # stele까지 이동. dist <=1이면 noise sweep을 우선 (도착 직전 안정화)
        dist = abs(target.row - agent.position.row) + abs(
            target.col - agent.position.col
        )
        if dist <= 1 and abs(n_t) > n_band * 0.9:
            return int(Action.N_MINUS) if n_t > 0 else int(Action.N_PLUS)
        return self._greedy_move_toward(layout, agent.position, target, rng)

    def _task_d_action(
        self,
        env: "RG4FEnv",
        rng: np.random.Generator,
    ) -> int:
        agent = env._agent  # noqa: SLF001
        episode = env._episode  # noqa: SLF001
        layout = episode.layout
        task = env._tasks_by_id[TaskID.TASK_D]  # noqa: SLF001
        inst = task.instance
        # tile은 굳이 다 거치지 않고 altar 직진. drift 누적이 적을수록 i_t≈0 매치 쉬움.
        altar = inst.object_positions["altar"][0]
        if agent.position != altar:
            return self._greedy_move_toward(layout, agent.position, altar, rng)
        i_t = float(agent.state_vec[int(StateDim.INTERACTION)])
        i_band = float(env.config.task_d_altar_half_width)
        if abs(i_t) <= i_band * 0.9:
            return int(Action.E)
        return int(Action.I_MINUS) if i_t > 0 else int(Action.I_PLUS)
        # 주의: forced_reset 시 wrong_counter는 env에서 초기화되므로 retry 가능

    def select(
        self,
        env: "RG4FEnv",
        rng: np.random.Generator,
        step: int,
    ) -> int:
        # epsilon fallback
        if rng.random() < self.epsilon:
            return int(rng.choice(len(self._fallback_probs), p=self._fallback_probs))
        # mode = random_biased_fallback이면 항상 fallback
        if self._mode == "random_biased_fallback":
            return int(rng.choice(len(self._fallback_probs), p=self._fallback_probs))

        episode = env._episode  # noqa: SLF001
        agent = env._agent  # noqa: SLF001
        if episode is None or agent is None:
            return int(rng.choice(len(self._fallback_probs), p=self._fallback_probs))

        # target task 결정
        target_task = self._select_target_task(env, step, rng)
        if target_task is None:
            # 모든 task 완료 또는 mode가 mistarget — random fallback
            return int(rng.choice(len(self._fallback_probs), p=self._fallback_probs))

        # task room으로 이동/probe
        target_room = self._find_room_for_task(episode, int(target_task))
        if target_room is None:
            return int(rng.choice(len(self._fallback_probs), p=self._fallback_probs))
        cur_room = agent.current_room

        # task attempt 시간 추적 (yaml task_budgets 사용; v5는 task별 별도 budget)
        if cur_room == target_room:
            self._task_attempt_ticks[target_task] += 1
            budget = int(self.task_budgets.get(int(target_task), 250))
            if self._task_attempt_ticks[target_task] >= budget:
                # timeout 기록 + giveup
                self._task_timeout[target_task] += 1
                self._task_giveup[target_task] = True
                # 다음 step에서 다른 task 선택 (또는 retry trigger via _select_target_task)
                return int(
                    rng.choice(len(self._fallback_probs), p=self._fallback_probs)
                )

        # 방 밖이면 door로 이동
        if cur_room != target_room:
            door = episode.layout.door_positions.get(target_room)
            if door is not None:
                return self._greedy_move_toward(
                    episode.layout, agent.position, door, rng
                )
            return int(rng.choice(len(self._fallback_probs), p=self._fallback_probs))

        # 방 안: task-specific probe
        try:
            if target_task == 0:
                return self._task_a_action(env, rng)
            if target_task == 1:
                return self._task_b_action(env, rng)
            if target_task == 2:
                return self._task_c_action(env, rng)
            if target_task == 3:
                return self._task_d_action(env, rng)
        except Exception:
            return int(rng.choice(len(self._fallback_probs), p=self._fallback_probs))
        return int(rng.choice(len(self._fallback_probs), p=self._fallback_probs))


def _make_policy(
    behavior_policy: str,
    yaml_cfg: Dict[str, Any],
):
    """behavior_policy 이름에 따라 policy 객체를 반환한다.

    Parameters
    ----------
    behavior_policy : str
        "random_uniform" | "random_biased" | "task_probe" | "task_success_curriculum"
    yaml_cfg : Dict
        전체 yaml config (task_probe / task_success_curriculum의 hyperparameter용).
    """
    if behavior_policy in ("random_uniform", "random_biased"):
        probs = _build_action_probs(behavior_policy)
        return _RandomBehaviorPolicy(probs)
    if behavior_policy == "task_probe":
        tp_cfg = (yaml_cfg.get("generation") or {}).get("task_probe") or {}
        fallback_probs = _build_action_probs("random_biased")
        return _TaskProbePolicy(
            epsilon=float(tp_cfg.get("epsilon", 0.15)),
            interact_prob_near_object=float(
                tp_cfg.get("interact_prob_near_object", 0.70)
            ),
            state_adjust_prob=float(tp_cfg.get("state_adjust_prob", 0.25)),
            stuck_window=int(tp_cfg.get("stuck_window", 20)),
            room_resample_prob=float(tp_cfg.get("room_resample_prob", 0.05)),
            prefer_unvisited_rooms=bool(tp_cfg.get("prefer_unvisited_rooms", True)),
            fallback_probs=fallback_probs,
        )
    if behavior_policy == "task_success_curriculum":
        sc_cfg = (yaml_cfg.get("generation") or {}).get("task_success_curriculum") or {}
        fallback_probs = _build_action_probs("random_biased")
        return _TaskSuccessCurriculumPolicy(
            epsilon=float(sc_cfg.get("epsilon", 0.10)),
            state_sweep_prob=float(sc_cfg.get("state_sweep_prob", 0.30)),
            interact_prob_near_object=float(
                sc_cfg.get("interact_prob_near_object", 0.80)
            ),
            stuck_window=int(sc_cfg.get("stuck_window", 25)),
            room_resample_prob=float(sc_cfg.get("room_resample_prob", 0.05)),
            failure_exploration_prob=float(
                sc_cfg.get("failure_exploration_prob", 0.05)
            ),
            privilege_level=str(sc_cfg.get("privilege_level", "weak_oracle")),
            mode_weights=dict(sc_cfg.get("mode_weights") or {}),
            task_budgets=dict(
                sc_cfg.get("task_budgets") or {"A": 420, "B": 480, "C": 360, "D": 200}
            ),
            max_retry_per_task=int(sc_cfg.get("max_retry_per_task", 1)),
            a_altar_sweep_step=float(sc_cfg.get("a_altar_sweep_step", 0.01)),
            a_altar_sweep_max_E_per_value=int(
                sc_cfg.get("a_altar_sweep_max_E_per_value", 1)
            ),
            b_use_label_oracle=bool(sc_cfg.get("b_use_label_oracle", False)),
            fallback_probs=fallback_probs,
        )
    raise ValueError(
        f"Unknown behavior_policy: {behavior_policy!r}. "
        f"Allowed: random_uniform | random_biased | task_probe | task_success_curriculum"
    )


# =============================================================================
# 4. split별 RG4FConfig 변형
# =============================================================================


def _apply_obs_channel_permutation(
    obs: Dict[str, np.ndarray],
    channel_perm: np.ndarray,
) -> Dict[str, np.ndarray]:
    """local_grid의 channel 순서를 permutation으로 섞는다 (ood_obs_shift 전용).

    의미는 그대로 유지되지만 모델이 보는 channel 위치가 달라진다 — 진짜 regime shift는
    아니므로 novelty detector가 false positive를 내야 하는 split을 만든다.
    """
    new_obs = dict(obs)
    grid = obs["local_grid"]
    new_obs["local_grid"] = grid[..., channel_perm]
    return new_obs


def _maybe_relocate_fields_to_room_centers(
    env: RG4FEnv,
    rng: np.random.Generator,
) -> None:
    """ood_field_placement 전용: invisible field source를 room interior 중심부로 재배치.

    env.reset() 직후, 환경의 _episode.invisible_fields 안의 source_position만 교체한다.
    coupling/family/radius/mu/sigma는 건드리지 않는다.
    """
    ep = env._episode  # noqa: SLF001 — 본 generator는 env 동결 상태로 직접 접근 허용
    if ep is None or not ep.invisible_fields:
        return
    layout = ep.layout
    candidates: List[Tuple[int, int]] = []
    from falsifiable_regime_world_model.rg4f.types import RoomID, TASK_ROOM_IDS

    for rid in TASK_ROOM_IDS:
        if rid not in layout.room_bounds:
            continue
        top, left, bot, right = layout.room_bounds[rid]
        cr = (top + bot) // 2
        cc = (left + right) // 2
        # 중심 셀 + 1셀 내 8-neighborhood 중 traversable 셀
        for dr in (-1, 0, +1):
            for dc in (-1, 0, +1):
                r, c = cr + dr, cc + dc
                if (
                    0 <= r < layout.full_h
                    and 0 <= c < layout.full_w
                    and bool(layout.traversable[r, c])
                ):
                    candidates.append((r, c))
    if not candidates:
        return
    from falsifiable_regime_world_model.rg4f.types import Position

    for f in ep.invisible_fields:
        idx = int(rng.integers(0, len(candidates)))
        r, c = candidates[idx]
        f.source_position = Position(r, c)


# =============================================================================
# 5. 한 episode 수집
# =============================================================================


def _run_one_episode(
    env: RG4FEnv,
    rng: np.random.Generator,
    policy: Any,
    max_steps: int,
    episode_seed: int,
    obs_channel_perm: Optional[np.ndarray] = None,
    relocate_fields_room_center: bool = False,
    field_family_pool: Optional[Sequence[int]] = None,
    family_filter_max_retries: int = 8,
) -> Tuple[Dict[str, np.ndarray], Dict[str, Any]]:
    """env를 한 episode 굴려 EpisodeBuffer를 채우고 finalize한다.

    Parameters
    ----------
    env : RG4FEnv
        외부에서 만든 환경. 본 함수가 reset부터 호출.
    rng : np.random.Generator
        action sampling용 rng. env 내부 rng와 분리되어 있어 같은 episode_seed로
        env reset해도 action sequence는 본 rng가 결정.
    policy : _RandomBehaviorPolicy | _TaskProbePolicy
        behavior policy 객체. ``policy.reset(env, episode_seed, rng)``과
        ``policy.select(env, rng, step)`` 인터페이스를 가진다.
    max_steps : int
        episode 최대 step 수 (env.config.episode_max_steps와 같거나 작아야 함).
    episode_seed : int
        env.reset(seed=episode_seed)으로 결정성 보장. family filter 재시도 시 본 rng로 갱신.
    obs_channel_perm : Optional[np.ndarray]
        ood_obs_shift 전용. None이 아니면 obs["local_grid"]의 채널 순서를 permute.
    relocate_fields_room_center : bool
        ood_field_placement 전용. True면 reset 직후 field source를 방 중심으로 이동.
    field_family_pool : Optional[Sequence[int]]
        ood_factor_recomb 전용. 주어지면 이 family에 들지 않는 invisible field를 제거.
        reset 후 fields가 모두 사라지면 ``family_filter_max_retries``번 reseed해서 재시도.
    """
    cur_seed = int(episode_seed)
    attempts = 0
    while True:
        obs, info = env.reset(seed=cur_seed)
        if field_family_pool is not None:
            empty = _filter_invisible_fields_by_family(env, field_family_pool)
            if empty and attempts < family_filter_max_retries:
                # 재시도: action rng로 새로운 env_seed 생성 (action 결정성과 분리)
                cur_seed = int(rng.integers(0, 2**31 - 1))
                attempts += 1
                continue
            # info의 field_info도 동기화 (제거된 field 반영)
            from falsifiable_regime_world_model.rg4f.fields import (
                summarize_fields_for_info,
            )

            info["field_info"] = summarize_fields_for_info(
                env._episode.invisible_fields
            )  # noqa: SLF001
            # P1: env._regime.active_field_families도 filter 후 fields와 동기화.
            # episode_meta.initial_regime이 실제 사용된 family pool과 일관되어야 한다.
            ep = env._episode  # noqa: SLF001
            if ep is not None:
                env._regime.active_field_families = tuple(  # noqa: SLF001
                    {f.family for f in ep.invisible_fields}
                )
                info["true_regime"]["active_field_families"] = [
                    int(f) for f in env._regime.active_field_families  # noqa: SLF001
                ]
        break

    if relocate_fields_room_center:
        _maybe_relocate_fields_to_room_centers(env, rng)
        # 방 중심으로 옮긴 source_position을 info에 동기화 (episode_meta에 그대로 저장됨)
        from falsifiable_regime_world_model.rg4f.fields import summarize_fields_for_info

        info["field_info"] = summarize_fields_for_info(
            env._episode.invisible_fields
        )  # noqa: SLF001

    if obs_channel_perm is not None:
        obs = _apply_obs_channel_permutation(obs, obs_channel_perm)

    buf = EpisodeBuffer()
    buf.set_initial(obs, info, episode_seed=episode_seed)

    # task_probe / random policy를 env 상태와 동기화
    policy.reset(env, episode_seed=episode_seed, rng=rng)

    for t in range(max_steps):
        action = policy.select(env, rng, step=t)
        next_obs, reward, terminated, truncated, info = env.step(action)
        if obs_channel_perm is not None:
            next_obs = _apply_obs_channel_permutation(next_obs, obs_channel_perm)
        # info에서 effective_action을 가져온다
        eff = int(info.get("effective_action", action))
        buf.append(
            action_raw=action,
            action_effective=eff,
            next_obs=next_obs,
            reward=float(reward),
            terminated=bool(terminated),
            truncated=bool(truncated),
            info=info,
        )
        if terminated or truncated:
            break

    arrays, meta = buf.finalize(save_debug_trace=True)
    return arrays, meta


# =============================================================================
# 6. split별 generation 정책
# =============================================================================


@dataclasses.dataclass
class SplitPlan:
    """한 split을 생성하기 위한 정책 결정 결과."""

    name: str
    num_episodes: int
    perm_pool: List[Tuple[int, int, int, int]]
    rg4f_kwargs_override: Dict[str, Any]
    field_family_pool: Optional[List[int]]  # None이면 모든 family 허용
    obs_channel_perm: Optional[np.ndarray]
    relocate_fields_room_center: bool
    is_ood: bool
    ood_type: Optional[str]


def _build_split_plans(
    splits: Sequence[str],
    yaml_cfg: Dict[str, Any],
    base_rg4f_kwargs: Dict[str, Any],
    base_rg4f: RG4FConfig,
    train_pool: List[Tuple[int, int, int, int]],
    ood_pool: List[Tuple[int, int, int, int]],
    counts: Dict[str, int],
    perm_master_rng: np.random.Generator,
) -> List[SplitPlan]:
    """각 split의 SplitPlan 객체를 만든다."""
    sp_policy = yaml_cfg.get("split_policy", {})
    factor_policy = sp_policy.get("factor_recomb", {})
    param_policy = sp_policy.get("param_shift", {})
    obs_policy = sp_policy.get("obs_shift", {})
    field_policy = sp_policy.get("field_placement", {})

    # train field families pool
    train_families = [
        int(x) for x in factor_policy.get("train_field_families", [0, 1, 2, 3])
    ]
    ood_families = [
        int(x) for x in factor_policy.get("ood_field_families", train_families)
    ]
    # P1 (Session 6 ENV_FIX_INSTRUCTIONS Issue 2): train_apply_family_filter=true면
    # train/valid/test_id에도 train_field_families를 강제 → ood_factor_recomb 가
    # train과 strict disjoint한 family pool에서 sampling됨이 보장된다.
    train_apply_family_filter = bool(
        factor_policy.get("train_apply_family_filter", False)
    )
    train_filter_pool: Optional[List[int]] = (
        train_families if train_apply_family_filter else None
    )

    # param shift multipliers
    drift_mult = float(param_policy.get("drift_strength_multiplier", 2.0))
    shift_mult = float(param_policy.get("shift_probability_multiplier", 2.0))

    # obs channel permutation: split별 고정된 permutation을 reproducibly 생성
    # (master rng의 sub-stream으로)
    visual_perm_enabled = bool(obs_policy.get("visual_channel_permutation", True))
    num_channels = int(
        base_rg4f.local_obs_size
    )  # used only for sanity; channels=10 hardcoded
    # local_grid C=10. types.LOCAL_CHANNELS 길이.
    from falsifiable_regime_world_model.rg4f.types import LOCAL_CHANNELS

    C = len(LOCAL_CHANNELS)
    if visual_perm_enabled:
        obs_perm = perm_master_rng.permutation(C)
        # identity가 우연히 나오면 한 번 더 shuffle (의미 없음 방지)
        if np.array_equal(obs_perm, np.arange(C)):
            obs_perm = perm_master_rng.permutation(C)
    else:
        obs_perm = np.arange(C)

    relocate_fields_for_field_split = bool(
        field_policy.get("placement_prior_shift", True)
    )

    plans: List[SplitPlan] = []
    for s in splits:
        n = counts.get(s, 0)
        if s in ("train", "valid", "test_id"):
            plans.append(
                SplitPlan(
                    name=s,
                    num_episodes=n,
                    perm_pool=list(train_pool),
                    rg4f_kwargs_override={},
                    # P1: train_apply_family_filter=true면 train_filter_pool을 적용,
                    # false면 None (기존 동작: 4 family 자유 노출).
                    field_family_pool=train_filter_pool,
                    obs_channel_perm=None,
                    relocate_fields_room_center=False,
                    is_ood=False,
                    ood_type=None,
                )
            )
        elif s == "ood_room_perm":
            plans.append(
                SplitPlan(
                    name=s,
                    num_episodes=n,
                    perm_pool=list(ood_pool),
                    rg4f_kwargs_override={},
                    field_family_pool=None,
                    obs_channel_perm=None,
                    relocate_fields_room_center=False,
                    is_ood=True,
                    ood_type="room_perm",
                )
            )
        elif s == "ood_factor_recomb":
            plans.append(
                SplitPlan(
                    name=s,
                    num_episodes=n,
                    perm_pool=list(train_pool),
                    rg4f_kwargs_override={},
                    field_family_pool=ood_families,
                    obs_channel_perm=None,
                    relocate_fields_room_center=False,
                    is_ood=True,
                    ood_type="factor_recomb",
                )
            )
        elif s == "ood_param_shift":
            override = {
                "field_mu_drift_sigma": float(base_rg4f.field_mu_drift_sigma)
                * drift_mult,
                "shift_prob_per_room_entry": min(
                    1.0, float(base_rg4f.shift_prob_per_room_entry) * shift_mult
                ),
                "shift_prob_per_checkpoint": min(
                    1.0, float(base_rg4f.shift_prob_per_checkpoint) * shift_mult
                ),
                "shift_prob_per_stele_activation": min(
                    1.0, float(base_rg4f.shift_prob_per_stele_activation) * shift_mult
                ),
                "field_radius_max": float(base_rg4f.field_radius_max) * drift_mult,
            }
            plans.append(
                SplitPlan(
                    name=s,
                    num_episodes=n,
                    perm_pool=list(train_pool),
                    rg4f_kwargs_override=override,
                    field_family_pool=None,
                    obs_channel_perm=None,
                    relocate_fields_room_center=False,
                    is_ood=True,
                    ood_type="param_shift",
                )
            )
        elif s == "ood_obs_shift":
            plans.append(
                SplitPlan(
                    name=s,
                    num_episodes=n,
                    perm_pool=list(train_pool),
                    rg4f_kwargs_override={},
                    field_family_pool=None,
                    obs_channel_perm=obs_perm,
                    relocate_fields_room_center=False,
                    is_ood=True,
                    ood_type="obs_shift",
                )
            )
        elif s == "ood_field_placement":
            plans.append(
                SplitPlan(
                    name=s,
                    num_episodes=n,
                    perm_pool=list(train_pool),
                    rg4f_kwargs_override={},
                    field_family_pool=None,
                    obs_channel_perm=None,
                    relocate_fields_room_center=relocate_fields_for_field_split,
                    is_ood=True,
                    ood_type="field_placement",
                )
            )
        else:
            raise ValueError(f"Unknown split name: {s!r}")
    return plans


# =============================================================================
# 7. 한 split의 모든 episode 생성
# =============================================================================


def _filter_invisible_fields_by_family(
    env: RG4FEnv,
    allowed_families: Sequence[int],
) -> bool:
    """env._episode.invisible_fields 중 allowed_families에 들지 않는 것을 제거한다.

    제거 후 fields가 모두 사라지면 True 반환 (caller에서 retry 결정).
    """
    ep = env._episode  # noqa: SLF001
    if ep is None:
        return False
    allowed = set(int(x) for x in allowed_families)
    ep.invisible_fields = [f for f in ep.invisible_fields if int(f.family) in allowed]
    return len(ep.invisible_fields) == 0


def _generate_split(
    plan: SplitPlan,
    base_rg4f_kwargs: Dict[str, Any],
    output_root: Path,
    master_seed: int,
    max_steps: int,
    behavior_policy: str,
    yaml_cfg: Dict[str, Any],
    save_debug_trace: bool,
    save_episode_metadata: bool,
    show_progress: bool,
    show_tqdm: bool,
) -> Dict[str, Any]:
    """한 split 폴더에 episode npz와 index.jsonl을 작성하고 통계를 반환한다."""
    split_dir = output_root / plan.name
    episodes_dir = split_dir / "episodes"
    episodes_dir.mkdir(parents=True, exist_ok=True)

    index_path = split_dir / "index.jsonl"
    index_lines: List[str] = []
    summary: Dict[str, Any] = {
        "split": plan.name,
        "num_episodes": plan.num_episodes,
        "is_ood": plan.is_ood,
        "ood_type": plan.ood_type,
        "rg4f_kwargs_override": plan.rg4f_kwargs_override,
        "field_family_pool": plan.field_family_pool,
        "obs_channel_perm_applied": plan.obs_channel_perm is not None,
        "obs_channel_perm": (
            plan.obs_channel_perm.tolist()
            if plan.obs_channel_perm is not None
            else None
        ),
        "relocate_fields_room_center": plan.relocate_fields_room_center,
        "perm_pool_size": len(plan.perm_pool),
        "perm_pool": [list(p) for p in plan.perm_pool],
        "behavior_policy": behavior_policy,
        "max_steps": max_steps,
        "episodes": [],  # 통계 (작은 정보만)
    }

    if plan.num_episodes <= 0:
        # 빈 split도 폴더와 index.jsonl(빈 파일)은 만든다 (downstream consistency)
        index_path.write_text("", encoding="utf-8")
        return summary

    # split-level 고정 RG4FConfig 만들기 (override 반영). forced_permutation은 episode마다 갱신.
    rg4f_kwargs = dict(base_rg4f_kwargs)
    rg4f_kwargs.update(plan.rg4f_kwargs_override)
    rg4f_kwargs["episode_max_steps"] = max_steps

    # split별 master rng — split name + master_seed 조합으로 결정성 보장.
    # Python ``hash()``는 PYTHONHASHSEED에 의존하므로 process 간 결정성이 깨진다.
    # 따라서 SHA1 기반 결정적 정수 변환을 사용한다.
    name_int = int.from_bytes(
        hashlib.sha1(plan.name.encode("utf-8")).digest()[:4],
        "big",
    )
    split_seed_root = (master_seed * 1_000_003 + name_int) & 0x7FFFFFFF
    split_rng = np.random.default_rng(split_seed_root)
    # task_probe 또는 random_* policy 객체. 각 episode 시작 시 reset() 호출.
    policy = _make_policy(behavior_policy, yaml_cfg)

    iterator: Iterable[int] = range(plan.num_episodes)
    if show_progress and show_tqdm and _HAS_TQDM:
        iterator = tqdm(iterator, desc=plan.name, total=plan.num_episodes, ncols=80)

    successful = 0
    for ep_idx in iterator:
        # 매 episode 결정성을 위해 split seed에서 episode seed 파생
        env_seed = int(split_rng.integers(0, 2**31 - 1))
        action_seed = int(split_rng.integers(0, 2**31 - 1))
        action_rng = np.random.default_rng(action_seed)

        # forced permutation 선택 (uniform over plan.perm_pool)
        forced = plan.perm_pool[int(split_rng.integers(0, len(plan.perm_pool)))]
        ep_kwargs = dict(rg4f_kwargs)
        ep_kwargs["forced_permutation"] = tuple(forced)
        try:
            ep_config = RG4FConfig.from_dict(ep_kwargs)
        except ValueError as exc:
            raise ValueError(
                f"Failed to build RG4FConfig for split={plan.name}: {exc}\n"
                f"kwargs={ep_kwargs}"
            ) from exc
        env = RG4FEnv(config=ep_config, seed=env_seed)

        # ood_factor_recomb의 family filter는 _run_one_episode 안에서 reset 직후 적용.
        # ood_field_placement의 relocate도 마찬가지. (이 두 후처리는 reset 직후만 의미 있음.)
        try:
            arrays, meta = _run_one_episode(
                env=env,
                rng=action_rng,
                policy=policy,
                max_steps=max_steps,
                episode_seed=env_seed,
                obs_channel_perm=plan.obs_channel_perm,
                relocate_fields_room_center=plan.relocate_fields_room_center,
                field_family_pool=plan.field_family_pool,
            )
        except Exception as exc:  # 한 episode 실패가 전체 split을 막지 않게
            print(
                f"[WARN] {plan.name} episode {ep_idx} failed: {exc!r}", file=sys.stderr
            )
            continue

        # episode metadata 보강
        meta["split"] = plan.name
        meta["is_ood"] = plan.is_ood
        meta["ood_type"] = plan.ood_type
        meta["permutation_id"] = int(_all_24_permutations().index(tuple(forced)))
        meta["forced_permutation"] = list(forced)
        meta["env_seed"] = env_seed
        meta["action_seed"] = action_seed
        meta["behavior_policy"] = behavior_policy
        # task_probe / task_success_curriculum은 정적 분포가 아니므로 action_probs는 fallback (random_biased) 분포
        if behavior_policy in ("random_uniform", "random_biased"):
            meta["action_probs"] = [
                float(x) for x in _build_action_probs(behavior_policy).tolist()
            ]
        else:
            meta["action_probs"] = (
                None  # task_probe / task_success_curriculum: state-dependent
            )
        # v5: task_success_curriculum의 collector metadata (mode + task_order + budget usage)
        if hasattr(policy, "get_collector_metadata"):
            try:
                meta["collector_metadata"] = policy.get_collector_metadata()
            except Exception:
                meta["collector_metadata"] = None
        meta["rg4f_kwargs_override"] = plan.rg4f_kwargs_override
        meta["field_family_pool"] = plan.field_family_pool
        meta["obs_channel_perm"] = (
            plan.obs_channel_perm.tolist()
            if plan.obs_channel_perm is not None
            else None
        )
        meta["relocate_fields_room_center"] = plan.relocate_fields_room_center
        if not save_debug_trace and "debug_trace" in meta:
            del meta["debug_trace"]

        # 파일 저장
        ep_name = f"{plan.name}_{ep_idx:06d}"
        npz_path = episodes_dir / f"{ep_name}.npz"
        np.savez_compressed(str(npz_path), **arrays)
        if save_episode_metadata:
            meta_path = episodes_dir / f"{ep_name}.meta.json"
            with meta_path.open("w", encoding="utf-8") as fp:
                json.dump(meta, fp, ensure_ascii=False, indent=2, default=_json_default)

        # index.jsonl 한 줄
        index_entry = {
            "episode_id": ep_name,
            "split": plan.name,
            "is_ood": plan.is_ood,
            "ood_type": plan.ood_type,
            "npz_path": str(npz_path.relative_to(output_root)).replace("\\", "/"),
            "meta_path": (
                str(
                    (episodes_dir / f"{ep_name}.meta.json").relative_to(output_root)
                ).replace("\\", "/")
                if save_episode_metadata
                else None
            ),
            "episode_length": int(meta["episode_length"]),
            "permutation_id": int(meta["permutation_id"]),
            "forced_permutation": list(forced),
            "env_seed": env_seed,
            "num_invisible_fields": int(meta["num_invisible_fields"]),
        }
        index_lines.append(json.dumps(index_entry, ensure_ascii=False))
        summary["episodes"].append(index_entry)
        successful += 1

        if show_progress and not (show_tqdm and _HAS_TQDM):
            # tqdm을 못 쓰는 경우 fallback print
            if (ep_idx + 1) % max(1, plan.num_episodes // 10) == 0:
                print(f"  [{plan.name}] {ep_idx + 1}/{plan.num_episodes}")

    index_path.write_text(
        "\n".join(index_lines) + ("\n" if index_lines else ""), encoding="utf-8"
    )
    summary["successful"] = successful
    return summary


def _json_default(obj: Any) -> Any:
    """json.dump default fallback. numpy scalar / array를 native python으로 변환."""
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return float(obj)
    if isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, tuple):
        return list(obj)
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


# =============================================================================
# 8. 메인 entry
# =============================================================================


def _load_yaml(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as fp:
        cfg = yaml.safe_load(fp)
    if not isinstance(cfg, dict):
        raise ValueError(f"Config root must be a dict; got {type(cfg).__name__}")
    return cfg


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="RG-4F dataset generator (Session 3)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--config", type=str, required=True, help="yaml config path")
    p.add_argument(
        "--output-root", type=str, default=None, help="override project.output_root"
    )
    p.add_argument("--seed", type=int, default=None, help="override generation.seed")
    p.add_argument(
        "--behavior-policy",
        type=str,
        default=None,
        help="override generation.behavior_policy. allowed: random_uniform | random_biased | task_probe",
    )
    p.add_argument("--num-train", type=int, default=None)
    p.add_argument("--num-valid", type=int, default=None)
    p.add_argument(
        "--num-test", type=int, default=None, help="num_test_id (in-distribution test)"
    )
    p.add_argument("--num-ood-per-type", type=int, default=None)
    p.add_argument(
        "--max-steps",
        type=int,
        default=None,
        help="override generation.episode_max_steps",
    )
    p.add_argument(
        "--overwrite", action="store_true", help="overwrite existing output dir"
    )
    p.add_argument(
        "--dry-run", action="store_true", help="check config and print plan; no IO"
    )
    p.add_argument(
        "--split",
        type=str,
        default=None,
        help="generate only the named split (e.g. train). default: all splits in yaml",
    )
    return p.parse_args()


def main() -> int:
    args = _parse_args()
    cfg_path = Path(args.config).resolve()
    if not cfg_path.is_file():
        print(f"[ERROR] config file not found: {cfg_path}", file=sys.stderr)
        return 2

    yaml_cfg = _load_yaml(cfg_path)

    project = yaml_cfg.get("project", {})
    generation = yaml_cfg.get("generation", {})
    metadata_cfg = yaml_cfg.get("metadata", {})
    splits_yaml = yaml_cfg.get("splits", [])
    if not splits_yaml:
        print("[ERROR] 'splits' must be a non-empty list", file=sys.stderr)
        return 2

    output_root = Path(
        args.output_root or project.get("output_root", "data/rg4f")
    ).resolve()
    overwrite = bool(args.overwrite or project.get("overwrite", False))
    save_format = str(project.get("save_format", "npz"))
    if save_format != "npz":
        print(
            f"[WARN] save_format={save_format!r} is not implemented; using npz.",
            file=sys.stderr,
        )

    master_seed = int(
        args.seed if args.seed is not None else generation.get("seed", 42)
    )
    num_train = int(
        args.num_train
        if args.num_train is not None
        else generation.get("num_train", 20)
    )
    num_valid = int(
        args.num_valid if args.num_valid is not None else generation.get("num_valid", 5)
    )
    num_test = int(
        args.num_test if args.num_test is not None else generation.get("num_test", 5)
    )
    num_ood = int(
        args.num_ood_per_type
        if args.num_ood_per_type is not None
        else generation.get("num_ood_per_type", 5)
    )
    max_steps = int(
        args.max_steps
        if args.max_steps is not None
        else generation.get("episode_max_steps", 200)
    )
    behavior_policy = str(
        args.behavior_policy
        if args.behavior_policy is not None
        else generation.get("behavior_policy", "random_biased")
    )
    if behavior_policy not in (
        "random_uniform",
        "random_biased",
        "task_probe",
        "task_success_curriculum",
    ):
        print(
            f"[ERROR] unknown behavior_policy={behavior_policy!r}. "
            f"allowed: random_uniform | random_biased | task_probe | task_success_curriculum",
            file=sys.stderr,
        )
        return 2
    show_tqdm = bool(generation.get("show_tqdm", True))
    save_manifest = bool(metadata_cfg.get("save_manifest", True))
    save_index = bool(metadata_cfg.get("save_index_jsonl", True))
    save_episode_meta = bool(metadata_cfg.get("save_episode_metadata", True))
    save_debug_trace = bool(metadata_cfg.get("save_debug_trace", True))

    counts: Dict[str, int] = {
        "train": num_train,
        "valid": num_valid,
        "test_id": num_test,
        "ood_room_perm": num_ood,
        "ood_factor_recomb": num_ood,
        "ood_param_shift": num_ood,
        "ood_obs_shift": num_ood,
        "ood_field_placement": num_ood,
    }

    # split filter
    if args.split is not None:
        if args.split not in splits_yaml:
            print(
                f"[ERROR] --split={args.split!r} not in yaml splits {splits_yaml}",
                file=sys.stderr,
            )
            return 2
        splits = [args.split]
    else:
        splits = list(splits_yaml)

    # environment yaml → RG4FConfig kwargs 변환
    env_section = yaml_cfg.get("environment", {})
    base_rg4f_kwargs = _yaml_env_to_rg4f_kwargs(env_section)
    # generation의 max_steps도 환경에 반영
    base_rg4f_kwargs["episode_max_steps"] = max_steps
    try:
        base_rg4f = RG4FConfig.from_dict(base_rg4f_kwargs)
    except ValueError as exc:
        print(f"[ERROR] Invalid environment config: {exc}", file=sys.stderr)
        return 2

    # split-aware permutation pool
    perm_root_seed = (master_seed * 65537) & 0x7FFFFFFF
    perm_master_rng = np.random.default_rng(perm_root_seed)
    sp_policy = yaml_cfg.get("split_policy", {})
    rp_policy = sp_policy.get("room_permutation", {})
    train_pool, ood_pool = _build_permutation_pools(
        rng=perm_master_rng,
        train_fraction=float(rp_policy.get("train_fraction_of_24_permutations", 0.5)),
        ood_use_disjoint=bool(rp_policy.get("ood_use_disjoint_permutations", True)),
    )

    # disjoint 검증 (체크리스트)
    train_set = set(train_pool)
    ood_set = set(ood_pool)
    overlap = train_set & ood_set
    if rp_policy.get("ood_use_disjoint_permutations", True) and overlap:
        print(
            f"[ERROR] train/ood permutation pools overlap: {overlap}", file=sys.stderr
        )
        return 2

    # plans 빌드
    # obs channel permutation은 master rng의 sub-stream으로 결정성
    obs_perm_rng = np.random.default_rng((master_seed * 31 + 7) & 0x7FFFFFFF)
    plans = _build_split_plans(
        splits=splits,
        yaml_cfg=yaml_cfg,
        base_rg4f_kwargs=base_rg4f_kwargs,
        base_rg4f=base_rg4f,
        train_pool=train_pool,
        ood_pool=ood_pool,
        counts=counts,
        perm_master_rng=obs_perm_rng,
    )

    # ---- dry-run ----
    if args.dry_run:
        print("=== Dry-run plan ===")
        print(f"config:      {cfg_path}")
        print(f"output_root: {output_root}")
        print(f"master_seed: {master_seed}")
        print(f"max_steps:   {max_steps}")
        print(f"behavior:    {behavior_policy}")
        print(
            f"train_pool ({len(train_pool)}): {train_pool[:6]}{' ...' if len(train_pool)>6 else ''}"
        )
        print(
            f"ood_pool   ({len(ood_pool)}):   {ood_pool[:6]}{' ...' if len(ood_pool)>6 else ''}"
        )
        print(f"disjoint check: train ∩ ood = {sorted(overlap)} (must be empty)")
        print(f"base RG4FConfig (resolved):")
        for f in dataclasses.fields(RG4FConfig):
            v = getattr(base_rg4f, f.name)
            print(f"  {f.name}: {v}")
        for plan in plans:
            print(
                f"\n[split={plan.name}] num={plan.num_episodes} is_ood={plan.is_ood} ood_type={plan.ood_type}"
            )
            print(f"  perm_pool_size: {len(plan.perm_pool)}")
            print(f"  rg4f_override: {plan.rg4f_kwargs_override}")
            print(f"  field_family_pool: {plan.field_family_pool}")
            print(
                f"  obs_channel_perm: {plan.obs_channel_perm.tolist() if plan.obs_channel_perm is not None else None}"
            )
            print(f"  relocate_fields_room_center: {plan.relocate_fields_room_center}")
        return 0

    # ---- 실제 IO ----
    if output_root.exists():
        if not overwrite:
            print(
                f"[ERROR] output_root {output_root} already exists. "
                f"Use --overwrite or set project.overwrite=true.",
                file=sys.stderr,
            )
            return 2
        # overwrite: 기존 split 폴더만 청소 (다른 user 파일은 안 건드림)
        for s in splits:
            tgt = output_root / s
            if tgt.exists():
                shutil.rmtree(tgt)
        for f_name in ("manifest.json",):
            f_path = output_root / f_name
            if f_path.exists():
                f_path.unlink()
    output_root.mkdir(parents=True, exist_ok=True)

    started = time.time()
    summaries: List[Dict[str, Any]] = []
    for plan in plans:
        print(f"=> generating split {plan.name} (n={plan.num_episodes})")
        s = _generate_split(
            plan=plan,
            base_rg4f_kwargs=base_rg4f_kwargs,
            output_root=output_root,
            master_seed=master_seed,
            max_steps=max_steps,
            behavior_policy=behavior_policy,
            yaml_cfg=yaml_cfg,
            save_debug_trace=save_debug_trace,
            save_episode_metadata=save_episode_meta,
            show_progress=True,
            show_tqdm=show_tqdm,
        )
        summaries.append(s)

    elapsed = time.time() - started

    # P1: factor_recomb 정책을 manifest에 명시적으로 기록 (Session 6 ENV_FIX Issue 2).
    factor_policy_yaml = (yaml_cfg.get("split_policy") or {}).get(
        "factor_recomb", {}
    ) or {}
    train_families_recorded = [
        int(x) for x in factor_policy_yaml.get("train_field_families", [0, 1, 2, 3])
    ]
    ood_families_recorded = [
        int(x)
        for x in factor_policy_yaml.get(
            "ood_field_families",
            train_families_recorded,
        )
    ]
    train_apply_filter_recorded = bool(
        factor_policy_yaml.get("train_apply_family_filter", False)
    )
    factor_recomb_disjoint = train_apply_filter_recorded and not (
        set(train_families_recorded) & set(ood_families_recorded)
    )

    # manifest.json
    if save_manifest:
        manifest = {
            "generator_version": "session3-v1",
            "config_path": str(cfg_path),
            "output_root": str(output_root),
            "master_seed": master_seed,
            "max_steps": max_steps,
            "behavior_policy": behavior_policy,
            "splits": list(splits),
            "counts": {k: counts.get(k, 0) for k in splits},
            "train_pool": [list(p) for p in train_pool],
            "ood_pool": [list(p) for p in ood_pool],
            "ood_room_perm_disjoint_from_train": bool(
                rp_policy.get("ood_use_disjoint_permutations", True)
            )
            and not overlap,
            "factor_recomb_policy": {
                "train_field_families": train_families_recorded,
                "ood_field_families": ood_families_recorded,
                "train_apply_family_filter": train_apply_filter_recorded,
                "disjoint": bool(factor_recomb_disjoint),
            },
            "task_probe_params": (
                (yaml_cfg.get("generation") or {}).get("task_probe")
                if behavior_policy == "task_probe"
                else None
            ),
            "task_success_curriculum_params": (
                (yaml_cfg.get("generation") or {}).get("task_success_curriculum")
                if behavior_policy == "task_success_curriculum"
                else None
            ),
            "rg4f_config": {
                f.name: getattr(base_rg4f, f.name)
                for f in dataclasses.fields(RG4FConfig)
            },
            "save_debug_trace": save_debug_trace,
            "save_index_jsonl": save_index,
            "save_episode_metadata": save_episode_meta,
            "split_summaries": [
                {
                    "split": s["split"],
                    "num_episodes": s["num_episodes"],
                    "successful": s.get("successful", 0),
                    "is_ood": s["is_ood"],
                    "ood_type": s["ood_type"],
                    "perm_pool_size": s["perm_pool_size"],
                    "rg4f_kwargs_override": s["rg4f_kwargs_override"],
                    "field_family_pool": s["field_family_pool"],
                    "obs_channel_perm": s.get("obs_channel_perm"),
                    "relocate_fields_room_center": s["relocate_fields_room_center"],
                }
                for s in summaries
            ],
            "elapsed_seconds": float(elapsed),
        }
        with (output_root / "manifest.json").open("w", encoding="utf-8") as fp:
            json.dump(manifest, fp, ensure_ascii=False, indent=2, default=_json_default)

    print(f"=== done in {elapsed:.2f}s. output: {output_root}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
