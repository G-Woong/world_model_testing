"""Partial observation 변환.

PART3 §3.16, RG4F_Environment_Plan §3 사양:
- ``o_t = (o_t^{local}, o_t^{scalar}, e_t)``
- ``local_obs_size`` 메인 5x5, ablation {3, 5, 7}.
- 전체 맵, hidden field source 위치, 정확한 regime label은 obs에 절대 노출되지 않는다.
- 5x5 안에서 cue 가시성 보장 원칙(§3.3): cue가 vision level에 따라 가려질 수 있으나
  적정 vision일 때는 보인다.

본 모듈은 hidden state(invisible field 위치, 정확한 task parameter, change-point 등)는
obs에 포함하지 않으며, 그 정보는 ``env.step``의 info에만 노출된다.
"""
from __future__ import annotations

from typing import Dict, List, Tuple

import numpy as np

from .config import RG4FConfig
from .map_generator import GridLayout
from .tasks import BaseTask
from .types import (
    AgentState,
    CellType,
    EventToken,
    LOCAL_CHANNELS,
    Position,
    RoomID,
    StateDim,
    TaskID,
    TASK_ROOM_IDS,
)


# 채널 이름 → index lookup
_CHANNEL_INDEX: Dict[str, int] = {name: i for i, name in enumerate(LOCAL_CHANNELS)}


def num_channels() -> int:
    return len(LOCAL_CHANNELS)


def scalar_dim(num_task_rooms: int = 4) -> int:
    """scalar vector의 길이.

    구성: 5(state) + 1(room_id_normalized) + 1(completed_count) + 1(fail_count)
        + 1(step_norm) + 1(carrying_weight)
        + num_task_rooms (각 방 task 완료 여부, room-task permutation은 episode 별이므로
          obs에는 "어느 task가 어느 방인지"가 아니라 "task별 완료 여부"만 노출하여
          task 위치 암기를 막는다)
    """
    return 5 + 1 + 1 + 1 + 1 + 1 + 4   # 4 = TaskID enum 크기


# =============================================================================
# local grid 변환
# =============================================================================

def _build_object_overlay(
    layout: GridLayout,
    tasks_by_room: Dict[RoomID, BaseTask],
) -> Dict[Tuple[int, int], Dict[str, float]]:
    """object/cue 정보를 cell coord → channel value dict로 변환.

    변환된 overlay는 어느 cell이 어떤 task object/cue인지를 채널별 강도로 기록한다.
    """
    overlay: Dict[Tuple[int, int], Dict[str, float]] = {}

    def _set(p: Position, channel: str, val: float) -> None:
        key = (p.row, p.col)
        if key not in overlay:
            overlay[key] = {}
        # 채널이 이미 있으면 max 결합 (덮어쓰기보다 안전)
        overlay[key][channel] = max(overlay[key].get(channel, 0.0), val)

    for room_id, task in tasks_by_room.items():
        del room_id
        # task object positions를 task 종류별로 기록.
        if task.task_id == TaskID.TASK_A:
            for p in task.instance.object_positions.get("pieces", []):
                _set(p, "task_object", 1.0)
            for p in task.instance.object_positions.get("altar", []):
                _set(p, "altar", 1.0)
        elif task.task_id == TaskID.TASK_B:
            for p in task.instance.object_positions.get("steles", []):
                _set(p, "stele", 1.0)
                _set(p, "task_object", 1.0)
            for p in task.instance.object_positions.get("door", []):
                _set(p, "task_object", 1.0)
        elif task.task_id == TaskID.TASK_C:
            for p in task.instance.object_positions.get("steles", []):
                _set(p, "stele", 1.0)
                _set(p, "task_object", 1.0)
        elif task.task_id == TaskID.TASK_D:
            for p in task.instance.object_positions.get("tiles", []):
                _set(p, "task_object", 1.0)
            for p in task.instance.object_positions.get("altar", []):
                _set(p, "altar", 1.0)
        # cue layer (vision-level mask는 build_local_grid에서 적용)
        for cue_pos, cue_label, strength in task.get_local_cues():
            del cue_label   # cue 종류별 분리는 향후 확장. 현재는 단일 cue 채널.
            _set(cue_pos, "cue", min(1.0, max(0.0, abs(float(strength)))))
    return overlay


def build_local_grid(
    config: RG4FConfig,
    layout: GridLayout,
    agent_state: AgentState,
    tasks_by_room: Dict[RoomID, BaseTask],
) -> np.ndarray:
    """주변 ``local_obs_size`` x ``local_obs_size`` x C window를 만든다.

    boundary는 wall로 padding된다 (transparent하게 환경의 외부도 wall로 인식되도록).
    vision level이 낮을수록 cue 채널이 부분적으로 마스킹된다.
    """
    n = config.local_obs_size
    half = n // 2
    C = num_channels()
    grid = np.zeros((n, n, C), dtype=np.float32)

    overlay = _build_object_overlay(layout, tasks_by_room)
    ar, ac = agent_state.position.row, agent_state.position.col

    # vision level → cue 가시성 확률.
    # vision threshold 이상이면 fully visible, 그 이하면 점차 hidden.
    v = agent_state.state_vec[int(StateDim.VISION)]
    cue_visible_strength = float(np.clip(
        (v - config.cue_visibility_threshold) /
        (1.0 - config.cue_visibility_threshold + 1e-6),
        0.0,
        1.0,
    ))

    for dr in range(-half, half + 1):
        for dc in range(-half, half + 1):
            r = ar + dr
            c = ac + dc
            ir = dr + half   # local row index
            ic = dc + half
            if not (0 <= r < layout.full_h and 0 <= c < layout.full_w):
                # 외부는 wall로 처리
                grid[ir, ic, _CHANNEL_INDEX["wall"]] = 1.0
                continue
            cell_type = int(layout.cells[r, c])
            if cell_type == int(CellType.WALL):
                grid[ir, ic, _CHANNEL_INDEX["wall"]] = 1.0
            elif cell_type == int(CellType.FLOOR):
                grid[ir, ic, _CHANNEL_INDEX["floor"]] = 1.0
            elif cell_type == int(CellType.CORRIDOR):
                grid[ir, ic, _CHANNEL_INDEX["corridor"]] = 1.0
            elif cell_type == int(CellType.DOOR):
                grid[ir, ic, _CHANNEL_INDEX["door"]] = 1.0
            grid[ir, ic, _CHANNEL_INDEX["traversable"]] = float(
                bool(layout.traversable[r, c])
            )
            ov = overlay.get((r, c))
            if ov is not None:
                for chan, val in ov.items():
                    if chan == "cue" and config.enable_cue_channel:
                        # cue는 vision level에 따라 마스킹
                        grid[ir, ic, _CHANNEL_INDEX[chan]] = float(val * cue_visible_strength)
                    elif chan in _CHANNEL_INDEX:
                        grid[ir, ic, _CHANNEL_INDEX[chan]] = float(val)

    # agent 자기 위치
    grid[half, half, _CHANNEL_INDEX["agent"]] = 1.0
    return grid


# =============================================================================
# scalar 변환
# =============================================================================

def build_scalar(
    config: RG4FConfig,
    agent_state: AgentState,
    tasks_by_room: Dict[RoomID, BaseTask],
    completed_count: int,
    fail_count: int,
    step: int,
) -> np.ndarray:
    """scalar 벡터 구성. RG4F_Environment_Plan §3.2 참조.

    구성: state(5) + room_norm(1) + completed(1) + fail(1) + step_norm(1)
         + carrying(1) + per-task completion(4)
    """
    out: List[float] = []
    out.extend(float(x) for x in agent_state.state_vec)
    out.append(float(int(agent_state.current_room)) / float(len(RoomID)))
    out.append(float(completed_count))
    out.append(float(fail_count))
    out.append(float(step) / float(config.episode_max_steps))
    out.append(float(agent_state.carrying_weight))
    # task 완료 여부는 task ID 별로 (room이 아니라 task identity 자체)
    task_done = {tid: 0.0 for tid in TaskID}  # noqa: F841 (placeholder)
    for room_id in TASK_ROOM_IDS:
        if room_id in tasks_by_room:
            t = tasks_by_room[room_id]
            task_done[t.task_id] = 1.0 if t.is_completed() else 0.0
    for tid in (TaskID.TASK_A, TaskID.TASK_B, TaskID.TASK_C, TaskID.TASK_D):
        out.append(task_done[tid])
    return np.asarray(out, dtype=np.float32)


# =============================================================================
# action mask
# =============================================================================

def build_action_mask(
    layout: GridLayout,
    agent_state: AgentState,
) -> np.ndarray:
    """현재 step에서 의미 있는 action 후보를 1.0으로 표시한 mask.

    이동 4 + E + 상태조절 10 + WAIT = 16개.
    mobility cooldown 중에는 이동 action이 0.0이지만, 환경은 그 action을 받아들여
    latency_cost를 부과하고 cooldown을 유지한다 (즉 mask는 hint일 뿐 hard constraint
    아님). agent 측은 mask를 보조 신호로 사용 가능.
    """
    from .types import Action, MOVE_ACTIONS, STATE_ADJUST_TABLE   # local import: 순환 참조 회피

    mask = np.zeros(16, dtype=np.float32)
    # 상태 조절은 항상 가능
    for a in STATE_ADJUST_TABLE:
        mask[int(a)] = 1.0
    mask[int(Action.WAIT)] = 1.0
    mask[int(Action.E)] = 1.0
    # 이동: cooldown이 끝나야 의미 있음
    can_move = agent_state.move_cooldown <= 0
    if can_move:
        for a in MOVE_ACTIONS:
            mask[int(a)] = 1.0
    del layout
    return mask


# =============================================================================
# 통합: dict observation 생성
# =============================================================================

def build_observation(
    config: RG4FConfig,
    layout: GridLayout,
    agent_state: AgentState,
    tasks_by_room: Dict[RoomID, BaseTask],
    completed_count: int,
    fail_count: int,
    step: int,
    last_event: EventToken,
) -> Dict[str, np.ndarray]:
    """env.reset / env.step에서 반환하는 obs dict.

    keys
    ----
    local_grid : float32 (n, n, C)
    scalar     : float32 (D,)
    event_token: int32 scalar
    action_mask: float32 (16,)
    """
    return {
        "local_grid": build_local_grid(config, layout, agent_state, tasks_by_room),
        "scalar": build_scalar(
            config, agent_state, tasks_by_room, completed_count, fail_count, step
        ),
        "event_token": np.int32(int(last_event)),
        "action_mask": build_action_mask(layout, agent_state),
    }


__all__ = [
    "num_channels",
    "scalar_dim",
    "build_local_grid",
    "build_scalar",
    "build_action_mask",
    "build_observation",
]
