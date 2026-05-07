"""RG-4F 환경의 모든 enum / dataclass / 타입 정의.

이 모듈은 RG-4F 환경 코드의 single source of truth 타입 시스템이다.
- 어떠한 로직(시뮬레이션, 샘플링, 변환)도 두지 않는다.
- 다른 모듈은 이 파일에서 import만 한다.
- dataset generator, world model, planner도 이 타입을 그대로 import한다.

세부 설계 근거:
- PART1 §3.3 (hidden state / hidden regime / change-point 분리)
- PART2 §3.10 (control-drift = 이산 remap + 약한 miscontrol + 주기 slip)
- RG4F_Environment_Plan §3.2 (관측 구조), §4 (5개 상태값), §6 (Task A/B/C/D)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Dict, List, Optional, Tuple


# =============================================================================
# 1. Action / EventToken / Direction enum
# =============================================================================

class Action(IntEnum):
    """RG-4F의 action 공간.

    이동 4 + 상호작용 1 + 5개 상태값 ±조절 10 + 대기 1 = 16개 action.

    PICKUP / DROP은 별도 action으로 두지 않고 ``E`` 한 개로 통합한다.
    어떤 동작이 발생하는지는 Task A의 진행 상태(carrying 여부)와 cell context로
    결정된다. 이 분기는 휴리스틱이 아니라 task FSM이 명시적으로 결정한다.
    """

    W = 0   # move up
    A = 1   # move left
    S = 2   # move down
    D = 3   # move right
    E = 4   # interact (context-dependent: pickup/drop/stele toggle/altar/door)
    V_PLUS = 5
    V_MINUS = 6
    M_PLUS = 7
    M_MINUS = 8
    I_PLUS = 9
    I_MINUS = 10
    N_PLUS = 11
    N_MINUS = 12
    D_PLUS = 13
    D_MINUS = 14
    WAIT = 15


# 이동 action 모음 (control-drift remap 대상)
MOVE_ACTIONS: Tuple[Action, ...] = (Action.W, Action.A, Action.S, Action.D)

# 상태 조절 action → (state_dim_index, sign)
STATE_ADJUST_TABLE: Dict[Action, Tuple[int, float]] = {
    Action.V_PLUS:  (0, +1.0),
    Action.V_MINUS: (0, -1.0),
    Action.M_PLUS:  (1, +1.0),
    Action.M_MINUS: (1, -1.0),
    Action.I_PLUS:  (2, +1.0),
    Action.I_MINUS: (2, -1.0),
    Action.N_PLUS:  (3, +1.0),
    Action.N_MINUS: (3, -1.0),
    Action.D_PLUS:  (4, +1.0),
    Action.D_MINUS: (4, -1.0),
}


class Direction(IntEnum):
    """4방향. (drow, dcol) 이동 벡터와 1:1 대응."""

    UP = 0
    LEFT = 1
    DOWN = 2
    RIGHT = 3


DIR_DELTA: Dict[Direction, Tuple[int, int]] = {
    Direction.UP:    (-1, 0),
    Direction.LEFT:  (0, -1),
    Direction.DOWN:  (+1, 0),
    Direction.RIGHT: (0, +1),
}

# Action(WASD) ↔ Direction 매핑
ACTION_TO_DIRECTION: Dict[Action, Direction] = {
    Action.W: Direction.UP,
    Action.A: Direction.LEFT,
    Action.S: Direction.DOWN,
    Action.D: Direction.RIGHT,
}
DIRECTION_TO_ACTION: Dict[Direction, Action] = {
    v: k for k, v in ACTION_TO_DIRECTION.items()
}


class EventToken(IntEnum):
    """env.step의 info에 기록되는 discrete event token.

    obs 안에서도 동일한 enum이 정수로 노출된다(단, obs는 1-hot이 아니라
    integer scalar 형태로 전달된다 — 모델 측에서 embedding 처리).
    """

    NONE = 0
    ROOM_ENTRY = 1
    ROOM_EXIT = 2
    INTERACTION_SUCCESS = 3
    INTERACTION_FAIL = 4
    CHECKPOINT = 5
    DOOR_OPEN = 6
    STELE_TOGGLE = 7
    TILE_FIRST_TOUCH = 8
    FORCED_RESET = 9
    CARRY_PICKUP = 10
    CARRY_DROP = 11
    TASK_COMPLETE = 12


class RoomID(IntEnum):
    """5개 영역 + 복도 식별자."""

    CENTRAL_HALL = 0
    NORTH = 1
    SOUTH = 2
    EAST = 3
    WEST = 4
    CORRIDOR = 5
    OUTSIDE = 6   # wall 등 어떤 영역도 아닌 경우 (디버깅용 sentinel)


# 4개 task 방. CENTRAL_HALL/CORRIDOR/OUTSIDE는 task 방이 아니다.
TASK_ROOM_IDS: Tuple[RoomID, ...] = (RoomID.NORTH, RoomID.SOUTH, RoomID.EAST, RoomID.WEST)


class TaskID(IntEnum):
    """Task A/B/C/D 식별자 (PART3 §3.18, RG4F_Environment_Plan §6)."""

    TASK_A = 0   # weight-order + interaction calibration (mobility, interaction)
    TASK_B = 1   # vision-positive stele + zero-mobility gate (vision, mobility)
    TASK_C = 2   # noise-zero multi-stele + control-drift tracking (noise, control-drift)
    TASK_D = 3   # tile-induced interaction drift + zero-i altar (interaction, noise)


class ControlMode(IntEnum):
    """control-drift regime. action remap 함수 Π_{r^ctrl}을 결정한다.

    PART2 §3.10.2의 정의를 그대로 따른다. 연속 각도 drift는 사용하지 않는다.
    """

    IDENTITY = 0
    CW = 1   # clockwise: W→D→S→A→W
    LR = 2   # left-right flip: A↔D
    UD = 3   # up-down flip: W↔S
    REV = 4  # reverse all


class MobilityMode(IntEnum):
    """mobility cooldown 함수 mode. 단순/주기적/burdened 등 확장을 위한 enum."""

    NORMAL = 0       # cooldown = base (m_t에 따라 가변)
    BURDENED = 1     # 조각 운반 중 추가 cooldown
    PERIODIC = 2     # 주기적 mobility spike (현재 메인 환경에서는 사용 안 함)


class FieldFamily(IntEnum):
    """invisible noise field family. RG4F_Environment_Plan §7.4.

    하나의 family는 정해진 1~2개의 상태 dimension에만 sparse coupling된다.
    """

    VISIBILITY = 0              # noise + vision
    FRICTION = 1                # noise + mobility
    INTERACTION_INTERFERENCE = 2  # noise + interaction
    CONTROL_INTERFERENCE = 3    # noise + control-drift


# state dimension index (state vector x_t = (v, m, i, n, d) ∈ [-1,1]^5)
class StateDim(IntEnum):
    VISION = 0
    MOBILITY = 1
    INTERACTION = 2
    NOISE = 3
    CONTROL_DRIFT = 4


# field family별 coupling 대상 state dim. sparse coupling 강제 (|·| ≤ 2).
FIELD_COUPLED_STATES: Dict[FieldFamily, Tuple[StateDim, ...]] = {
    FieldFamily.VISIBILITY: (StateDim.NOISE, StateDim.VISION),
    FieldFamily.FRICTION: (StateDim.NOISE, StateDim.MOBILITY),
    FieldFamily.INTERACTION_INTERFERENCE: (StateDim.NOISE, StateDim.INTERACTION),
    FieldFamily.CONTROL_INTERFERENCE: (StateDim.NOISE, StateDim.CONTROL_DRIFT),
}


# =============================================================================
# 2. cell type (map_generator가 사용하는 grid cell 분류)
# =============================================================================

class CellType(IntEnum):
    """grid 한 cell의 정적 속성. 동적 정보(object/agent)는 별도 layer로 둔다."""

    WALL = 0
    FLOOR = 1
    DOOR = 2          # corridor가 hall/room의 wall을 통과하는 위치
    CORRIDOR = 3      # corridor interior cell


# observation local grid의 channel 정의.
# 순서가 곧 channel index. 추가 시 끝에 append하여 backward compatibility 유지.
LOCAL_CHANNELS: Tuple[str, ...] = (
    "wall",                # 1.0 if cell is wall
    "floor",               # 1.0 if cell is plain floor
    "corridor",            # 1.0 if cell is corridor cell
    "door",                # 1.0 if cell is door
    "task_object",         # task별 object (piece/stele/altar/tile)
    "stele",               # task B/C의 stele 표지
    "altar",               # task A/D의 altar 표지
    "cue",                 # weak local cue (vision-level mask 적용 후)
    "agent",               # agent 위치
    "traversable",         # 이동 가능한 cell
)


# =============================================================================
# 3. dataclass: 환경 내부 상태 + info/debug 컨테이너
# =============================================================================

@dataclass(frozen=True)
class Position:
    """grid 위 정수 좌표. (row, col) 순서. frozen=True (해시 가능)."""

    row: int
    col: int

    def shifted(self, drow: int, dcol: int) -> "Position":
        return Position(self.row + drow, self.col + dcol)

    def as_tuple(self) -> Tuple[int, int]:
        return (self.row, self.col)


@dataclass
class AgentState:
    """agent의 현재 동적 상태. 일부는 obs에 직접 노출되고 일부는 hidden state다."""

    position: Position
    # 5차원 상태값 x_t = (v, m, i, n, d)
    state_vec: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0, 0.0, 0.0])
    # mobility cooldown: 다음 이동 가능 tick까지 남은 step 수 (>=0)
    move_cooldown: int = 0
    # carrying: Task A에서 들고 있는 piece의 weight (0이면 빈손).
    # (Task A 외 task에서는 0으로 유지)
    carrying_weight: float = 0.0
    carrying_piece_id: Optional[int] = None
    # 현재 위치 room id (관측에 노출)
    current_room: RoomID = RoomID.CENTRAL_HALL


@dataclass
class TaskInstance:
    """한 episode에서 하나의 방에 배정된 task의 정적 instantiation.

    실제 진행 상태(progress/completed_subgoals)는 ``TaskInstance.state``에 둔다.
    """

    task_id: TaskID
    room_id: RoomID
    # 방 안 object들의 고정 placement (cell coord 리스트).
    # task별 의미는 다르다. 예: task A → 4 piece 위치 + altar 위치.
    object_positions: Dict[str, List[Position]] = field(default_factory=dict)
    # task-level parameter (예: τ_i target band center, weight order ground truth).
    parameters: Dict[str, float] = field(default_factory=dict)
    # task별 진행 상태 (mutable). reset 시 비워진다.
    state: Dict[str, object] = field(default_factory=dict)


@dataclass
class FieldInfoEntry:
    """info["field_info"]에 들어가는 한 invisible field의 ground-truth 요약."""

    family: FieldFamily
    source_position: Position
    radius: float
    mu: float
    sigma: float
    coupled_states: Tuple[StateDim, ...]
    # 현재 step에서 agent에게 미친 effect (state dim별 sample). 디버그용.
    last_effect: Dict[int, float] = field(default_factory=dict)


@dataclass
class TargetBandInfo:
    """현재 활성 target band 정보. 없을 수도 있으므로 ``active=False``로 표현."""

    active: bool = False
    state_dim: Optional[StateDim] = None
    center: float = 0.0
    half_width: float = 0.0
    # band 종류: "match_to_band" | "maximize" | "threshold" | "derivative_zero"
    kind: str = "none"


@dataclass
class RegimeState:
    """현재 episode의 hidden regime ground truth.

    obs에 노출되지 않는다. info["true_regime"]에만 들어간다.
    factorized regime code (PART3 §3.23.7).
    """

    control_mode: ControlMode = ControlMode.IDENTITY
    mobility_mode: MobilityMode = MobilityMode.NORMAL
    miscontrol_p: float = 0.0
    periodic_slip_active: bool = False
    periodic_K: int = 4
    # 현재 상태에 영향을 미치는 invisible field family들의 union (디버그)
    active_field_families: Tuple[FieldFamily, ...] = ()


@dataclass
class StepDebug:
    """env.step의 info["debug"]에 들어가는 풍부한 디버그 trace.

    이 객체는 dataset generator / falsification metric / world-model supervision
    이 사용한다. obs에는 절대 노출되지 않는다.
    """

    raw_action: int = 0
    effective_action: int = 0
    miscontrolled: bool = False
    move_attempted: bool = False
    move_succeeded: bool = False
    moved_into_cell_type: int = 0
    interaction_attempted: bool = False
    interaction_outcome: str = "none"     # "none"/"success"/"fail"/"pickup"/"drop"
    state_adjust_dim: Optional[int] = None
    state_adjust_sign: float = 0.0
    cooldown_blocked: bool = False
    field_effect: Dict[int, float] = field(default_factory=dict)
    field_drift_applied: bool = False
    field_event_shift_applied: bool = False
    reveal_event: bool = False
    shift_event: bool = False
    change_point: bool = False
    extras: Dict[str, object] = field(default_factory=dict)


__all__ = [
    "Action",
    "MOVE_ACTIONS",
    "STATE_ADJUST_TABLE",
    "Direction",
    "DIR_DELTA",
    "ACTION_TO_DIRECTION",
    "DIRECTION_TO_ACTION",
    "EventToken",
    "RoomID",
    "TASK_ROOM_IDS",
    "TaskID",
    "ControlMode",
    "MobilityMode",
    "FieldFamily",
    "StateDim",
    "FIELD_COUPLED_STATES",
    "CellType",
    "LOCAL_CHANNELS",
    "Position",
    "AgentState",
    "TaskInstance",
    "FieldInfoEntry",
    "TargetBandInfo",
    "RegimeState",
    "StepDebug",
]
