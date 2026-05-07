"""중앙홀 + 4방 + 복도 layout 생성과 episode-level 정적 sampling.

본 모듈은 한 episode가 시작되는 시점에 한 번만 호출되어 다음을 결정한다.
1. grid layout (CellType array, traversable mask)
2. room_id lookup (각 cell이 어느 영역인지)
3. agent의 시작 위치 (중앙홀 중심)
4. room-task permutation (4! 중 하나 sampling)
5. 각 방 안 object placement (task 종류별로 결정)
6. invisible field source placement (sparse coupling 조건 준수)

PART0 §3 §11 금지: "task A/B/C/D를 room 위치에 고정하는 구현 금지". 따라서
permutation은 매 episode마다 sampling되며, 방의 task는 ``permutation`` dict에
의해 결정된다. 어떠한 hard-coded "north → Task A" 매핑도 금지한다.

Session 2 단계에서는 split-aware permutation까지 구현하지 않는다. Session 3에서
``configs/dataset_default.yaml``과 함께 train/OOD permutation 분리가 추가된다.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

import numpy as np

from .config import RG4FConfig
from .types import (
    FIELD_COUPLED_STATES,
    CellType,
    FieldFamily,
    FieldInfoEntry,
    Position,
    RoomID,
    TASK_ROOM_IDS,
    TaskID,
    TaskInstance,
)


# =============================================================================
# Layout dataclass — 정적 grid 정보의 캐리어
# =============================================================================

@dataclass
class GridLayout:
    """한 episode의 정적 grid 정보. step 동안 절대 변하지 않는다."""

    full_h: int
    full_w: int
    cells: np.ndarray            # (H, W) of CellType (int)
    room_id_grid: np.ndarray     # (H, W) of RoomID (int). wall은 OUTSIDE.
    traversable: np.ndarray      # (H, W) bool
    # 각 영역(room/hall)의 interior bbox: (top, left, bot, right) inclusive
    room_bounds: Dict[RoomID, Tuple[int, int, int, int]]
    # corridor cells (RoomID.CORRIDOR로 분류된 cell들)
    corridor_cells: List[Position]
    # 방 입구 door cell (room별)
    door_positions: Dict[RoomID, Position]
    # agent 시작 위치 (중앙홀 중심)
    start_position: Position

    def in_bounds(self, p: Position) -> bool:
        return 0 <= p.row < self.full_h and 0 <= p.col < self.full_w

    def is_traversable(self, p: Position) -> bool:
        if not self.in_bounds(p):
            return False
        return bool(self.traversable[p.row, p.col])

    def room_of(self, p: Position) -> RoomID:
        if not self.in_bounds(p):
            return RoomID.OUTSIDE
        return RoomID(int(self.room_id_grid[p.row, p.col]))


@dataclass
class EpisodeLayout:
    """layout + permutation + task_instances + invisible fields.

    이 객체는 ``RG4FEnv`` 안에서 reset 시 한 번 만들어지고, step에서 읽기만 한다.
    """

    layout: GridLayout
    # room → task (RoomID.NORTH/SOUTH/EAST/WEST 만 key로 사용)
    permutation: Dict[RoomID, TaskID]
    # 각 4방 task의 인스턴스 (task별 object placement / parameter 포함)
    task_instances: Dict[TaskID, TaskInstance]
    # invisible field source 정의 (env.step에서 mean drift / event shift 갱신)
    invisible_fields: List[FieldInfoEntry]
    # 디버그: episode 생성 정보 요약
    meta: Dict[str, object] = field(default_factory=dict)


# =============================================================================
# 1. grid layout 생성
# =============================================================================

@dataclass
class _AxisAnchors:
    """row 또는 col 한 축의 영역 경계 (inclusive index).

    cross 토폴로지에서 row와 col은 동일한 split 패턴을 가진다.
    """

    rs: int       # room_size
    cs: int       # corridor_length
    hs: int       # hall_size
    full: int     # 전체 길이

    @property
    def near_room_top(self) -> int:
        # 가까운 쪽 방의 시작 (north 또는 west)
        return 1

    @property
    def near_room_bot(self) -> int:
        return self.rs                                         # inclusive

    @property
    def wall_near_corr(self) -> int:
        return self.rs + 1

    @property
    def near_corr_top(self) -> int:
        return self.rs + 2

    @property
    def near_corr_bot(self) -> int:
        return self.rs + 1 + self.cs                            # inclusive

    @property
    def wall_hall_near(self) -> int:
        return self.rs + 2 + self.cs

    @property
    def hall_top(self) -> int:
        return self.rs + 3 + self.cs

    @property
    def hall_bot(self) -> int:
        return self.rs + 2 + self.cs + self.hs                  # inclusive

    @property
    def wall_hall_far(self) -> int:
        return self.rs + 3 + self.cs + self.hs

    @property
    def far_corr_top(self) -> int:
        return self.rs + 4 + self.cs + self.hs

    @property
    def far_corr_bot(self) -> int:
        return self.rs + 3 + 2 * self.cs + self.hs              # inclusive

    @property
    def wall_far_corr(self) -> int:
        return self.rs + 4 + 2 * self.cs + self.hs

    @property
    def far_room_top(self) -> int:
        return self.rs + 5 + 2 * self.cs + self.hs

    @property
    def far_room_bot(self) -> int:
        return 2 * self.rs + 4 + 2 * self.cs + self.hs          # inclusive


def _make_anchors(config: RG4FConfig) -> _AxisAnchors:
    rs, cs, hs = config.room_size, config.corridor_length, config.hall_size
    # 한 축 layout: outer_wall(1) + room(rs) + wall(1) + corridor(cs) + wall(1)
    #            + hall(hs) + wall(1) + corridor(cs) + wall(1) + room(rs) + outer_wall(1)
    # 합계: 6 + 2*rs + 2*cs + hs
    full = 6 + 2 * rs + 2 * cs + hs
    return _AxisAnchors(rs=rs, cs=cs, hs=hs, full=full)


def generate_layout(config: RG4FConfig, rng: np.random.Generator) -> GridLayout:
    """static grid layout을 생성한다. RNG는 미래 확장(벽 변형 등)을 위해 받는다.

    현재 구현은 deterministic layout (정사각 cross 토폴로지). procedural maze는
    만들지 않는다 (Session 2 범위 외).
    """
    del rng  # 현재 deterministic layout

    A = _make_anchors(config)
    full = A.full

    cells = np.full((full, full), CellType.WALL, dtype=np.int8)
    room_id_grid = np.full((full, full), RoomID.OUTSIDE, dtype=np.int8)

    hall_top, hall_bot = A.hall_top, A.hall_bot
    hall_left, hall_right = A.hall_top, A.hall_bot   # 정사각 → row와 동일
    hall_size = config.hall_size
    rs = config.room_size

    # ---- hall interior ----
    cells[hall_top:hall_bot + 1, hall_left:hall_right + 1] = CellType.FLOOR
    room_id_grid[hall_top:hall_bot + 1, hall_left:hall_right + 1] = RoomID.CENTRAL_HALL

    # ---- 4방 interior ----
    # north/south room: cols는 hall과 left-aligned (hall_left ~ hall_left + rs - 1)
    # west/east room: rows는 hall과 left-aligned (hall_top ~ hall_top + rs - 1)
    room_col_left_ns = hall_left
    room_col_right_ns = hall_left + rs - 1
    room_row_top_we = hall_top
    room_row_bot_we = hall_top + rs - 1

    room_bounds: Dict[RoomID, Tuple[int, int, int, int]] = {}

    def _fill_room(rid: RoomID, top: int, bot: int, left: int, right: int) -> None:
        cells[top:bot + 1, left:right + 1] = CellType.FLOOR
        room_id_grid[top:bot + 1, left:right + 1] = rid
        room_bounds[rid] = (top, left, bot, right)

    _fill_room(
        RoomID.NORTH,
        A.near_room_top, A.near_room_bot,
        room_col_left_ns, room_col_right_ns,
    )
    _fill_room(
        RoomID.SOUTH,
        A.far_room_top, A.far_room_bot,
        room_col_left_ns, room_col_right_ns,
    )
    _fill_room(
        RoomID.WEST,
        room_row_top_we, room_row_bot_we,
        A.near_room_top, A.near_room_bot,
    )
    _fill_room(
        RoomID.EAST,
        room_row_top_we, room_row_bot_we,
        A.far_room_top, A.far_room_bot,
    )
    room_bounds[RoomID.CENTRAL_HALL] = (hall_top, hall_left, hall_bot, hall_right)

    # ---- corridor 4개 ---- (1-cell wide)
    corridor_cells: List[Position] = []
    door_positions: Dict[RoomID, Position] = {}

    hall_center_col = hall_left + hall_size // 2
    hall_center_row = hall_top + hall_size // 2

    def _fill_corridor_segment(cells_list: List[Position]) -> None:
        for p in cells_list:
            cells[p.row, p.col] = CellType.CORRIDOR
            room_id_grid[p.row, p.col] = RoomID.CORRIDOR
            corridor_cells.append(p)

    def _set_door(p: Position) -> None:
        cells[p.row, p.col] = CellType.DOOR
        room_id_grid[p.row, p.col] = RoomID.CORRIDOR

    # north corridor (rows near_corr_top..near_corr_bot, col = hall_center_col)
    north_segment = [Position(r, hall_center_col)
                     for r in range(A.near_corr_top, A.near_corr_bot + 1)]
    _fill_corridor_segment(north_segment)
    _set_door(Position(A.wall_hall_near, hall_center_col))   # hall ↔ corridor
    _set_door(Position(A.wall_near_corr, hall_center_col))   # corridor ↔ north room
    door_positions[RoomID.NORTH] = Position(A.wall_near_corr, hall_center_col)

    # south corridor
    south_segment = [Position(r, hall_center_col)
                     for r in range(A.far_corr_top, A.far_corr_bot + 1)]
    _fill_corridor_segment(south_segment)
    _set_door(Position(A.wall_hall_far, hall_center_col))
    _set_door(Position(A.wall_far_corr, hall_center_col))
    door_positions[RoomID.SOUTH] = Position(A.wall_far_corr, hall_center_col)

    # west corridor (row = hall_center_row, cols near_corr_top..near_corr_bot)
    west_segment = [Position(hall_center_row, c)
                    for c in range(A.near_corr_top, A.near_corr_bot + 1)]
    _fill_corridor_segment(west_segment)
    _set_door(Position(hall_center_row, A.wall_hall_near))
    _set_door(Position(hall_center_row, A.wall_near_corr))
    door_positions[RoomID.WEST] = Position(hall_center_row, A.wall_near_corr)

    # east corridor (row = hall_center_row, cols far_corr_top..far_corr_bot)
    east_segment = [Position(hall_center_row, c)
                    for c in range(A.far_corr_top, A.far_corr_bot + 1)]
    _fill_corridor_segment(east_segment)
    _set_door(Position(hall_center_row, A.wall_hall_far))
    _set_door(Position(hall_center_row, A.wall_far_corr))
    door_positions[RoomID.EAST] = Position(hall_center_row, A.wall_far_corr)

    # ---- traversable mask ----
    traversable = np.isin(cells, [CellType.FLOOR, CellType.CORRIDOR, CellType.DOOR])

    start_position = Position(hall_center_row, hall_center_col)

    return GridLayout(
        full_h=full,
        full_w=full,
        cells=cells,
        room_id_grid=room_id_grid,
        traversable=traversable,
        room_bounds=room_bounds,
        corridor_cells=corridor_cells,
        door_positions=door_positions,
        start_position=start_position,
    )


# =============================================================================
# 2. room-task permutation
# =============================================================================

def sample_room_task_permutation(
    rng: np.random.Generator,
    forced: "Tuple[int, int, int, int] | None" = None,
) -> Dict[RoomID, TaskID]:
    """4! permutation 중 하나를 sampling 또는 강제 주입.

    Parameters
    ----------
    rng : np.random.Generator
        forced=None일 때 random shuffle에 사용.
    forced : tuple[int, int, int, int] | None
        Session 3 split-aware permutation을 위해 generator가 주입하는 강제 매핑.
        ``forced[i]``는 ``TASK_ROOM_IDS[i]`` (NORTH/SOUTH/EAST/WEST 순)에 배정될
        ``TaskID`` 정수값. 0..3의 정확한 permutation이어야 한다.
        None이면 단순 random shuffle (Session 2 호환).
    """
    if forced is not None:
        if sorted(forced) != [0, 1, 2, 3]:
            raise ValueError(
                f"forced permutation must be a permutation of (0,1,2,3); got {forced}"
            )
        return {room: TaskID(int(forced[i])) for i, room in enumerate(TASK_ROOM_IDS)}

    tasks = list(TaskID)
    rng.shuffle(tasks)
    return {room: tasks[i] for i, room in enumerate(TASK_ROOM_IDS)}


# =============================================================================
# 3. 방 object placement (task별 정적 layout 결정)
# =============================================================================

def _interior_cells(layout: GridLayout, room_id: RoomID) -> List[Position]:
    """주어진 방의 interior FLOOR cell 목록을 반환한다 (door 제외)."""
    top, left, bot, right = layout.room_bounds[room_id]
    cells = []
    for r in range(top, bot + 1):
        for c in range(left, right + 1):
            if layout.cells[r, c] == CellType.FLOOR:
                cells.append(Position(r, c))
    return cells


def _sample_distinct_positions(
    rng: np.random.Generator,
    candidates: List[Position],
    k: int,
) -> List[Position]:
    """후보에서 k개의 서로 다른 위치를 샘플링."""
    if k > len(candidates):
        raise ValueError(
            f"requested {k} distinct positions but only {len(candidates)} candidates available"
        )
    indices = rng.choice(len(candidates), size=k, replace=False)
    return [candidates[int(i)] for i in indices]


def build_task_instance(
    config: RG4FConfig,
    layout: GridLayout,
    rng: np.random.Generator,
    task_id: TaskID,
    room_id: RoomID,
) -> TaskInstance:
    """task 종류에 맞는 object placement와 episode-sampled parameter를 만든다.

    object_positions의 key는 task별로 정의된 string label.
    parameters의 key 역시 task별로 정의된 의미.
    """
    candidates = _interior_cells(layout, room_id)
    inst = TaskInstance(task_id=task_id, room_id=room_id)

    if task_id == TaskID.TASK_A:
        positions = _sample_distinct_positions(rng, candidates, k=5)
        inst.object_positions["pieces"] = positions[:4]
        inst.object_positions["altar"] = positions[4:]
        # τ_i: U_{target_grid_step}[task_a_target_range], 격자 위 sample
        lo, hi = config.task_a_target_range
        steps = int(round((hi - lo) / config.target_grid_step))
        idx = int(rng.integers(0, steps + 1))
        tau_i = lo + idx * config.target_grid_step
        inst.parameters["tau_i"] = float(tau_i)
        # 어느 piece가 어떤 weight인지를 random shuffle. 정답 ordering은 weight 내림차순.
        weights = list(config.task_a_piece_weights)
        order_perm = rng.permutation(len(weights))
        for j, perm_idx in enumerate(order_perm):
            inst.parameters[f"piece_weight_{j}"] = float(weights[int(perm_idx)])

    elif task_id == TaskID.TASK_B:
        n_steles = config.task_b_num_steles
        positions = _sample_distinct_positions(rng, candidates, k=n_steles + 1)
        inst.object_positions["steles"] = positions[:n_steles]
        inst.object_positions["door"] = positions[n_steles:]
        # vision-positive label: 정확히 num_positive 개를 random selection
        labels = np.zeros(n_steles, dtype=bool)
        positive_idx = rng.choice(n_steles, size=config.task_b_num_positive, replace=False)
        labels[positive_idx] = True
        for k_, val in enumerate(labels):
            inst.parameters[f"stele_positive_{k_}"] = float(val)
        # stele ON 시 적용될 Δv_k 등을 미리 sampling (vision-positive 여부와 부호 일치)
        for k_ in range(n_steles):
            sign = +1 if labels[k_] else -1
            mag = float(rng.uniform(0.0, abs(config.task_b_dv_range[1])))
            inst.parameters[f"stele_dv_{k_}"] = sign * mag
            inst.parameters[f"stele_dm_{k_}"] = float(
                rng.uniform(*config.task_b_dm_range)
            )
            inst.parameters[f"stele_dd_{k_}"] = float(
                rng.uniform(*config.task_b_dd_range)
            )

    elif task_id == TaskID.TASK_C:
        n_steles = int(rng.choice(config.task_c_num_steles_choices))
        positions = _sample_distinct_positions(rng, candidates, k=n_steles)
        inst.object_positions["steles"] = positions
        # 방 진입 시 initial control-drift bin
        d0 = float(rng.choice(config.task_c_initial_d_bins))
        inst.parameters["initial_d"] = d0
        # 방향별 noise increment Δn_W/A/S/D
        for dir_label in ("W", "A", "S", "D"):
            inst.parameters[f"dn_{dir_label}"] = float(
                rng.uniform(*config.task_c_dn_range)
            )

    elif task_id == TaskID.TASK_D:
        n_tiles = config.task_d_num_tiles
        positions = _sample_distinct_positions(rng, candidates, k=n_tiles + 1)
        inst.object_positions["tiles"] = positions[:n_tiles]
        inst.object_positions["altar"] = positions[n_tiles:]
        # tile별 첫 통과 시 적용될 (Δi, Δn, Δv) 미리 sampling
        for k_ in range(n_tiles):
            inst.parameters[f"tile_di_{k_}"] = float(
                rng.uniform(*config.task_d_tile_di_range)
            )
            inst.parameters[f"tile_dn_{k_}"] = float(
                rng.uniform(*config.task_d_tile_dn_range)
            )
            inst.parameters[f"tile_dv_{k_}"] = float(
                rng.uniform(*config.task_d_tile_dv_range)
            )

    else:
        raise ValueError(f"unknown task_id: {task_id}")

    return inst


# =============================================================================
# 4. invisible field placement
# =============================================================================

def sample_invisible_fields(
    config: RG4FConfig,
    layout: GridLayout,
    rng: np.random.Generator,
) -> List[FieldInfoEntry]:
    """sparse coupling을 보장하면서 invisible field source를 sampling한다.

    field source는 grid 어디든 가능하다. agent에게 직접 보이지 않으므로
    wall cell이어도 무관하다 (effect는 distance 기반).
    """
    if not config.enable_invisible_fields:
        return []

    n = int(rng.integers(config.num_fields_min, config.num_fields_max + 1))
    fields: List[FieldInfoEntry] = []
    families = list(FieldFamily)
    for _ in range(n):
        family = FieldFamily(int(rng.choice(families)))
        coupled = FIELD_COUPLED_STATES[family]
        # PART0 §3 §10: sparse coupling 강제
        if len(coupled) > config.field_coupling_max_dims:
            raise ValueError(
                f"FIELD_COUPLED_STATES[{family}] has {len(coupled)} dims; "
                f"violates field_coupling_max_dims={config.field_coupling_max_dims}"
            )
        # source는 grid 안 random cell
        src_row = int(rng.integers(0, layout.full_h))
        src_col = int(rng.integers(0, layout.full_w))
        radius = float(rng.uniform(config.field_radius_min, config.field_radius_max))
        mu = float(rng.uniform(-config.field_mu_init_abs_max, config.field_mu_init_abs_max))
        fields.append(
            FieldInfoEntry(
                family=family,
                source_position=Position(src_row, src_col),
                radius=radius,
                mu=mu,
                sigma=config.field_sigma_init,
                coupled_states=tuple(coupled),
                last_effect={},
            )
        )
    return fields


# =============================================================================
# 5. 한 episode 분량의 모든 정적 정보 build
# =============================================================================

def build_episode(
    config: RG4FConfig,
    rng: np.random.Generator,
) -> EpisodeLayout:
    """한 episode를 위한 layout / permutation / task instances / fields 구축.

    ``config.forced_permutation``이 None이 아니면 그 값을 강제로 사용한다 (Session 3
    split-aware permutation). None이면 random shuffle (Session 2 호환).
    """
    layout = generate_layout(config, rng)
    permutation = sample_room_task_permutation(rng, forced=config.forced_permutation)
    task_instances: Dict[TaskID, TaskInstance] = {}
    for room_id, task_id in permutation.items():
        inst = build_task_instance(config, layout, rng, task_id, room_id)
        task_instances[task_id] = inst
    invisible_fields = sample_invisible_fields(config, layout, rng)

    meta: Dict[str, object] = {
        "permutation": {int(k): int(v) for k, v in permutation.items()},
        "num_invisible_fields": len(invisible_fields),
    }
    return EpisodeLayout(
        layout=layout,
        permutation=permutation,
        task_instances=task_instances,
        invisible_fields=invisible_fields,
        meta=meta,
    )


__all__ = [
    "GridLayout",
    "EpisodeLayout",
    "generate_layout",
    "sample_room_task_permutation",
    "build_task_instance",
    "sample_invisible_fields",
    "build_episode",
]
