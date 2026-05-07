"""Task A/B/C/D의 state machine.

PART3 §3.18, RG4F_Environment_Plan §6 정의를 환경 코드 수준에서 구현한다.

각 Task는 다음 interface를 만족한다:
    - reset(rng)               : 진행 상태 초기화
    - on_enter_room(...)        : 방 진입 시 일회성 effect (예: Task C의 initial_d)
    - step(...)                 : 매 env.step에서 호출되는 진행 갱신 (tile 통과 등)
    - interact(...)             : E action 처리 (pickup/drop/stele toggle/altar)
    - is_completed()
    - get_target_band(...)
    - get_local_cues(...)
    - get_debug_info()

각 method는 다음 형식의 ``TaskStepResult``를 반환한다.
    event_token   : EventToken (이번 호출에서 발생한 가장 의미 있는 event 하나)
    outcome       : str ("none"/"success"/"fail"/"pickup"/"drop"/"toggle"/"complete")
    state_deltas  : Dict[int, float]   (state vector에 더해질 deterministic delta)
    reveal_event  : bool               (hidden state가 새로 드러난 event)
    shift_event   : bool               (regime/parameter가 변한 event)
    forced_reset  : bool               (Task D의 fail-3 forced reset 등)
    debug         : Dict[str, object]
env가 ``state_deltas``를 적용하고, ``reveal_event``/``shift_event``를 info에 노출한다.
이 분리는 PART0 §3 §8 ("reveal과 shift를 한 라벨로 합치는 것 금지")을 강제한다.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np

from .config import RG4FConfig
from .types import (
    AgentState,
    EventToken,
    Position,
    StateDim,
    TargetBandInfo,
    TaskID,
    TaskInstance,
)


# =============================================================================
# Task step의 표준 반환 구조체
# =============================================================================

@dataclass
class TaskStepResult:
    event_token: EventToken = EventToken.NONE
    outcome: str = "none"
    state_deltas: Dict[int, float] = field(default_factory=dict)
    reveal_event: bool = False
    shift_event: bool = False
    forced_reset: bool = False
    debug: Dict[str, object] = field(default_factory=dict)


def _empty() -> TaskStepResult:
    return TaskStepResult()


# =============================================================================
# Base class
# =============================================================================

class BaseTask:
    """Task A/B/C/D 공통 base. env는 이 interface만 의존한다."""

    task_id: TaskID

    def __init__(self, instance: TaskInstance, config: RG4FConfig) -> None:
        self.instance = instance
        self.config = config
        self._completed: bool = False
        self._failure_count: int = 0
        # 방 첫 진입 여부 (on_enter_room이 두 번 호출되는 것을 방지)
        self._has_entered_room: bool = False

    # ---- reset ----
    def reset(self, rng: np.random.Generator) -> None:  # noqa: ARG002 (rng는 subclass에서 사용)
        self._completed = False
        self._failure_count = 0
        self._has_entered_room = False

    # ---- env hooks ----
    def on_enter_room(
        self,
        agent_state: AgentState,
        rng: np.random.Generator,
    ) -> TaskStepResult:
        # 기본은 noop. subclass가 override (특히 Task C).
        del agent_state, rng
        if self._has_entered_room:
            return _empty()
        self._has_entered_room = True
        return TaskStepResult(event_token=EventToken.ROOM_ENTRY, outcome="entered")

    def step(
        self,
        agent_state: AgentState,
        prev_position: Position,
        rng: np.random.Generator,
    ) -> TaskStepResult:
        del agent_state, prev_position, rng
        return _empty()

    def interact(
        self,
        agent_state: AgentState,
        rng: np.random.Generator,
    ) -> TaskStepResult:
        del agent_state, rng
        return _empty()

    # ---- inspectors ----
    def is_completed(self) -> bool:
        return self._completed

    def get_target_band(self, agent_state: AgentState) -> TargetBandInfo:  # noqa: ARG002
        return TargetBandInfo(active=False)

    def get_local_cues(self) -> List[Tuple[Position, str, float]]:
        """returns list of (cell_position, cue_type, strength). strength ∈ [0, 1].

        observation.py가 cue layer를 만들 때 이 목록을 사용한다.
        """
        return []

    def get_debug_info(self) -> Dict[str, object]:
        return {
            "task_id": int(self.task_id),
            "room_id": int(self.instance.room_id),
            "completed": self._completed,
            "failure_count": self._failure_count,
        }


# =============================================================================
# Task A: weight-order pieces + final altar interaction
# =============================================================================

class TaskA(BaseTask):
    task_id = TaskID.TASK_A

    def reset(self, rng: np.random.Generator) -> None:
        super().reset(rng)
        # piece sequence 진행도. 정답 = piece_weight 내림차순으로 픽업.
        self._used_pieces: List[int] = []
        # carry 가능 여부: Session 2 단순화 → 픽업 직후 carrying=weight, 다음 piece를 픽업하면
        # 이전 piece는 자동 drop (delivered).
        self._weights = [
            self.instance.parameters[f"piece_weight_{j}"]
            for j in range(len(self.instance.object_positions["pieces"]))
        ]
        # 정답 ordering = weight 내림차순으로 정렬한 piece index
        self._correct_order = sorted(
            range(len(self._weights)),
            key=lambda j: -self._weights[j],
        )
        # pickup 시 적용될 i, n shift는 episode-sample (deterministic per piece)
        self._pickup_di = [
            float(rng.uniform(*self.config.task_a_pickup_di_range))
            for _ in self._weights
        ]
        self._pickup_dn = [
            float(rng.uniform(*self.config.task_a_pickup_dn_range))
            for _ in self._weights
        ]

    def _piece_index_at(self, position: Position) -> Optional[int]:
        for j, p in enumerate(self.instance.object_positions["pieces"]):
            if p == position and j not in self._used_pieces:
                return j
        return None

    def _altar_at(self, position: Position) -> bool:
        return position in self.instance.object_positions["altar"]

    def interact(
        self,
        agent_state: AgentState,
        rng: np.random.Generator,
    ) -> TaskStepResult:
        del rng
        pos = agent_state.position
        piece_idx = self._piece_index_at(pos)
        result = TaskStepResult()

        # piece pickup
        if piece_idx is not None:
            expected_idx = self._correct_order[len(self._used_pieces)]
            if piece_idx == expected_idx:
                self._used_pieces.append(piece_idx)
                # mobility carry penalty (deterministic state-level): Δm = -w_j
                # interaction / noise persistent shift (pre-sampled)
                result.event_token = EventToken.CARRY_PICKUP
                result.outcome = "pickup"
                result.state_deltas = {
                    int(StateDim.MOBILITY): -self._weights[piece_idx],
                    int(StateDim.INTERACTION): self._pickup_di[piece_idx],
                    int(StateDim.NOISE): self._pickup_dn[piece_idx],
                }
                result.reveal_event = True   # piece가 사용됨 = hidden state 갱신
                result.debug = {
                    "task_a_picked_piece_idx": int(piece_idx),
                    "task_a_carrying_weight": float(self._weights[piece_idx]),
                    "task_a_progress": len(self._used_pieces),
                }
            else:
                self._failure_count += 1
                result.event_token = EventToken.INTERACTION_FAIL
                result.outcome = "fail"
                result.debug = {
                    "task_a_wrong_piece_idx": int(piece_idx),
                    "task_a_expected_idx": int(expected_idx),
                }
            return result

        # altar interaction (모든 piece가 올바른 순서로 사용된 뒤에만 의미)
        if self._altar_at(pos):
            if len(self._used_pieces) < len(self._weights):
                self._failure_count += 1
                result.event_token = EventToken.INTERACTION_FAIL
                result.outcome = "fail"
                result.debug = {"task_a_altar_too_early": True}
                return result
            tau_i = self.instance.parameters["tau_i"]
            i_t = agent_state.state_vec[int(StateDim.INTERACTION)]
            half = self.config.target_band_width
            if abs(i_t - tau_i) <= half:
                self._completed = True
                result.event_token = EventToken.TASK_COMPLETE
                result.outcome = "complete"
                result.debug = {"task_a_tau_i": float(tau_i), "task_a_i_t": float(i_t)}
            else:
                self._failure_count += 1
                result.event_token = EventToken.INTERACTION_FAIL
                result.outcome = "fail"
                result.debug = {
                    "task_a_tau_i": float(tau_i),
                    "task_a_i_t": float(i_t),
                    "task_a_band_miss": float(abs(i_t - tau_i)),
                }
            return result

        # piece도 altar도 아닌 cell에서 E
        return _empty()

    def get_target_band(self, agent_state: AgentState) -> TargetBandInfo:
        # 모든 piece를 들고 altar 앞에 도달한 시점에서만 active
        if (
            len(self._used_pieces) >= len(self._weights)
            and self._altar_at(agent_state.position)
        ):
            tau_i = self.instance.parameters["tau_i"]
            return TargetBandInfo(
                active=True,
                state_dim=StateDim.INTERACTION,
                center=float(tau_i),
                half_width=float(self.config.target_band_width),
                kind="match_to_band",
            )
        return TargetBandInfo(active=False)

    def get_local_cues(self) -> List[Tuple[Position, str, float]]:
        cues: List[Tuple[Position, str, float]] = []
        for j, p in enumerate(self.instance.object_positions["pieces"]):
            if j in self._used_pieces:
                continue
            # weight를 약하게 hint하는 cue strength = weight (정확 수치 노출은 X, weak hint)
            cues.append((p, "piece_weight", float(self._weights[j])))
        for p in self.instance.object_positions["altar"]:
            cues.append((p, "altar_band", 0.5))
        return cues

    def get_debug_info(self) -> Dict[str, object]:
        info = super().get_debug_info()
        info.update({
            "task_a_used_pieces": list(self._used_pieces),
            "task_a_correct_order": list(self._correct_order),
            "task_a_tau_i": float(self.instance.parameters.get("tau_i", 0.0)),
            "task_a_progress": len(self._used_pieces),
        })
        return info


# =============================================================================
# Task B: vision-positive stele + zero-mobility gate
# =============================================================================

class TaskB(BaseTask):
    task_id = TaskID.TASK_B

    def reset(self, rng: np.random.Generator) -> None:
        super().reset(rng)
        n = len(self.instance.object_positions["steles"])
        self._stele_on: List[bool] = [False] * n
        # vision history (마지막 N tick의 v 값). N = task_b_vision_stable_ticks.
        self._vision_history: List[float] = []

    def _stele_index_at(self, position: Position) -> Optional[int]:
        for k_, p in enumerate(self.instance.object_positions["steles"]):
            if p == position:
                return k_
        return None

    def _door_at(self, position: Position) -> bool:
        return position in self.instance.object_positions["door"]

    def step(
        self,
        agent_state: AgentState,
        prev_position: Position,
        rng: np.random.Generator,
    ) -> TaskStepResult:
        del prev_position, rng
        v = agent_state.state_vec[int(StateDim.VISION)]
        self._vision_history.append(float(v))
        if len(self._vision_history) > self.config.task_b_vision_stable_ticks + 1:
            self._vision_history.pop(0)
        return _empty()

    def interact(
        self,
        agent_state: AgentState,
        rng: np.random.Generator,
    ) -> TaskStepResult:
        del rng
        pos = agent_state.position
        result = TaskStepResult()

        sidx = self._stele_index_at(pos)
        if sidx is not None:
            # toggle
            new_state = not self._stele_on[sidx]
            self._stele_on[sidx] = new_state
            result.event_token = EventToken.STELE_TOGGLE
            result.outcome = "toggle"
            # 켜는 순간 persistent shift, 끄는 순간은 영향 없음 (RG4F_Environment_Plan §6.2)
            if new_state:
                dv = self.instance.parameters[f"stele_dv_{sidx}"]
                dm = self.instance.parameters[f"stele_dm_{sidx}"]
                dd = self.instance.parameters[f"stele_dd_{sidx}"]
                result.state_deltas = {
                    int(StateDim.VISION): float(dv),
                    int(StateDim.MOBILITY): float(dm),
                    int(StateDim.CONTROL_DRIFT): float(dd),
                }
                result.reveal_event = True   # stele 정체가 드러남 (vision-positive 여부)
            result.debug = {
                "task_b_stele_idx": int(sidx),
                "task_b_stele_now_on": bool(new_state),
                "task_b_steles_state": list(self._stele_on),
            }
            return result

        if self._door_at(pos):
            # 정답 stele set: 정확히 vision-positive 들만 ON, non-positive는 OFF
            n = len(self._stele_on)
            positive_truth = [
                bool(self.instance.parameters[f"stele_positive_{k_}"]) for k_ in range(n)
            ]
            stele_correct = all(
                self._stele_on[k_] == positive_truth[k_] for k_ in range(n)
            )
            m_t = agent_state.state_vec[int(StateDim.MOBILITY)]
            m_in_band = abs(m_t) <= self.config.task_b_mobility_gate_half_width
            # vision 안정 조건: 마지막 N+1개 v값에서 N개의 Δv 모두 0
            need = self.config.task_b_vision_stable_ticks
            v_stable = (
                len(self._vision_history) >= need + 1
                and all(
                    abs(self._vision_history[i + 1] - self._vision_history[i]) < 1e-9
                    for i in range(-(need + 1), -1)
                )
            )
            if stele_correct and m_in_band and v_stable:
                self._completed = True
                result.event_token = EventToken.TASK_COMPLETE
                result.outcome = "complete"
                result.debug = {"task_b_door_open": True}
            else:
                self._failure_count += 1
                result.event_token = EventToken.INTERACTION_FAIL
                result.outcome = "fail"
                result.debug = {
                    "task_b_door_fail": True,
                    "task_b_stele_correct": stele_correct,
                    "task_b_m_in_band": m_in_band,
                    "task_b_v_stable": v_stable,
                }
            return result

        return _empty()

    def get_target_band(self, agent_state: AgentState) -> TargetBandInfo:
        if self._door_at(agent_state.position):
            return TargetBandInfo(
                active=True,
                state_dim=StateDim.MOBILITY,
                center=0.0,
                half_width=float(self.config.task_b_mobility_gate_half_width),
                kind="match_to_band",
            )
        return TargetBandInfo(active=False)

    def get_local_cues(self) -> List[Tuple[Position, str, float]]:
        cues: List[Tuple[Position, str, float]] = []
        n = len(self.instance.object_positions["steles"])
        for k_, p in enumerate(self.instance.object_positions["steles"]):
            label = float(self.instance.parameters[f"stele_positive_{k_}"])
            cues.append((p, "stele_vis_positive_hint", label))
        for p in self.instance.object_positions["door"]:
            cues.append((p, "door_zero_mobility_hint", 0.5))
        del n
        return cues

    def get_debug_info(self) -> Dict[str, object]:
        info = super().get_debug_info()
        info.update({
            "task_b_stele_on": list(self._stele_on),
            "task_b_vision_history": list(self._vision_history),
        })
        return info


# =============================================================================
# Task C: noise-zero multi-stele + control-drift tracking
# =============================================================================

class TaskC(BaseTask):
    task_id = TaskID.TASK_C

    def reset(self, rng: np.random.Generator) -> None:
        super().reset(rng)
        self._activated: List[bool] = [
            False
        ] * len(self.instance.object_positions["steles"])

    def on_enter_room(
        self,
        agent_state: AgentState,
        rng: np.random.Generator,
    ) -> TaskStepResult:
        del rng
        if self._has_entered_room:
            return _empty()
        self._has_entered_room = True
        # initial control-drift bin을 강제 set. 이건 regime shift event다.
        target_d = self.instance.parameters["initial_d"]
        current_d = agent_state.state_vec[int(StateDim.CONTROL_DRIFT)]
        result = TaskStepResult(
            event_token=EventToken.ROOM_ENTRY,
            outcome="entered",
            state_deltas={int(StateDim.CONTROL_DRIFT): float(target_d - current_d)},
            shift_event=True,
            debug={"task_c_initial_d": float(target_d)},
        )
        return result

    def step(
        self,
        agent_state: AgentState,
        prev_position: Position,
        rng: np.random.Generator,
    ) -> TaskStepResult:
        del rng
        # 이동 방향에 따라 noise increment Δn_dir 적용. prev_position → agent_state.position.
        dr = agent_state.position.row - prev_position.row
        dc = agent_state.position.col - prev_position.col
        result = TaskStepResult()
        if (dr, dc) == (-1, 0):
            label = "W"
        elif (dr, dc) == (0, -1):
            label = "A"
        elif (dr, dc) == (+1, 0):
            label = "S"
        elif (dr, dc) == (0, +1):
            label = "D"
        else:
            label = ""
        if label:
            dn = float(self.instance.parameters[f"dn_{label}"])
            result.state_deltas = {int(StateDim.NOISE): dn}
            result.reveal_event = True
            result.debug = {"task_c_movement_dn": dn, "task_c_dir": label}
        return result

    def _stele_index_at(self, position: Position) -> Optional[int]:
        for k_, p in enumerate(self.instance.object_positions["steles"]):
            if p == position and not self._activated[k_]:
                return k_
        return None

    def interact(
        self,
        agent_state: AgentState,
        rng: np.random.Generator,
    ) -> TaskStepResult:
        del rng
        sidx = self._stele_index_at(agent_state.position)
        if sidx is None:
            return _empty()
        n_t = agent_state.state_vec[int(StateDim.NOISE)]
        in_band = abs(n_t) <= self.config.task_c_noise_zero_half_width
        result = TaskStepResult(debug={
            "task_c_stele_idx": int(sidx),
            "task_c_n_t": float(n_t),
            "task_c_in_band": in_band,
        })
        if in_band:
            self._activated[sidx] = True
            if all(self._activated):
                self._completed = True
                result.event_token = EventToken.TASK_COMPLETE
                result.outcome = "complete"
            else:
                result.event_token = EventToken.STELE_TOGGLE
                result.outcome = "toggle"
        else:
            self._failure_count += 1
            result.event_token = EventToken.INTERACTION_FAIL
            result.outcome = "fail"
        return result

    def get_target_band(self, agent_state: AgentState) -> TargetBandInfo:
        if self._stele_index_at(agent_state.position) is not None:
            return TargetBandInfo(
                active=True,
                state_dim=StateDim.NOISE,
                center=0.0,
                half_width=float(self.config.task_c_noise_zero_half_width),
                kind="match_to_band",
            )
        return TargetBandInfo(active=False)

    def get_local_cues(self) -> List[Tuple[Position, str, float]]:
        return [
            (p, "stele_noise_zero_hint", 0.5)
            for p in self.instance.object_positions["steles"]
        ]

    def get_debug_info(self) -> Dict[str, object]:
        info = super().get_debug_info()
        info.update({
            "task_c_activated": list(self._activated),
            "task_c_initial_d": float(self.instance.parameters.get("initial_d", 0.0)),
        })
        return info


# =============================================================================
# Task D: tile-induced interaction drift + final zero-altar (3-fail forced reset)
# =============================================================================

class TaskD(BaseTask):
    task_id = TaskID.TASK_D

    def reset(self, rng: np.random.Generator) -> None:
        super().reset(rng)
        n_tiles = len(self.instance.object_positions["tiles"])
        self._tile_visited: List[bool] = [False] * n_tiles
        self._wrong_interaction: int = 0

    def _tile_index_at(self, position: Position) -> Optional[int]:
        for k_, p in enumerate(self.instance.object_positions["tiles"]):
            if p == position and not self._tile_visited[k_]:
                return k_
        return None

    def step(
        self,
        agent_state: AgentState,
        prev_position: Position,
        rng: np.random.Generator,
    ) -> TaskStepResult:
        del prev_position, rng
        tidx = self._tile_index_at(agent_state.position)
        if tidx is None:
            return _empty()
        # tile 첫 통과: persistent (Δi, Δn, Δv) shift
        self._tile_visited[tidx] = True
        di = float(self.instance.parameters[f"tile_di_{tidx}"])
        dn = float(self.instance.parameters[f"tile_dn_{tidx}"])
        dv = float(self.instance.parameters[f"tile_dv_{tidx}"])
        return TaskStepResult(
            event_token=EventToken.TILE_FIRST_TOUCH,
            outcome="reveal",
            state_deltas={
                int(StateDim.INTERACTION): di,
                int(StateDim.NOISE): dn,
                int(StateDim.VISION): dv,
            },
            reveal_event=True,
            debug={
                "task_d_tile_idx": int(tidx),
                "task_d_tile_di": di,
                "task_d_tile_dn": dn,
                "task_d_tile_dv": dv,
            },
        )

    def _altar_at(self, position: Position) -> bool:
        return position in self.instance.object_positions["altar"]

    def interact(
        self,
        agent_state: AgentState,
        rng: np.random.Generator,
    ) -> TaskStepResult:
        del rng
        if not self._altar_at(agent_state.position):
            return _empty()
        i_t = agent_state.state_vec[int(StateDim.INTERACTION)]
        half = self.config.task_d_altar_half_width
        result = TaskStepResult(debug={"task_d_i_t": float(i_t)})
        if abs(i_t) <= half:
            self._completed = True
            result.event_token = EventToken.TASK_COMPLETE
            result.outcome = "complete"
            return result
        self._wrong_interaction += 1
        self._failure_count += 1
        if self._wrong_interaction >= self.config.fail_reset_threshold:
            result.event_token = EventToken.FORCED_RESET
            result.outcome = "fail"
            result.forced_reset = True
            # forced reset 후 wrong-counter 초기화 (PART3 §3.18.4 의 강제복귀 의미)
            self._wrong_interaction = 0
        else:
            result.event_token = EventToken.INTERACTION_FAIL
            result.outcome = "fail"
        return result

    def get_target_band(self, agent_state: AgentState) -> TargetBandInfo:
        if self._altar_at(agent_state.position):
            return TargetBandInfo(
                active=True,
                state_dim=StateDim.INTERACTION,
                center=0.0,
                half_width=float(self.config.task_d_altar_half_width),
                kind="match_to_band",
            )
        return TargetBandInfo(active=False)

    def get_local_cues(self) -> List[Tuple[Position, str, float]]:
        cues: List[Tuple[Position, str, float]] = []
        for k_, p in enumerate(self.instance.object_positions["tiles"]):
            di = self.instance.parameters[f"tile_di_{k_}"]
            cues.append((p, "tile_drift_dir", float(di)))
        for p in self.instance.object_positions["altar"]:
            cues.append((p, "altar_zero_band", 0.5))
        return cues

    def get_debug_info(self) -> Dict[str, object]:
        info = super().get_debug_info()
        info.update({
            "task_d_tile_visited": list(self._tile_visited),
            "task_d_wrong_interaction_count": int(self._wrong_interaction),
        })
        return info


# =============================================================================
# Factory
# =============================================================================

_TASK_CLASS = {
    TaskID.TASK_A: TaskA,
    TaskID.TASK_B: TaskB,
    TaskID.TASK_C: TaskC,
    TaskID.TASK_D: TaskD,
}


def build_task(instance: TaskInstance, config: RG4FConfig) -> BaseTask:
    cls = _TASK_CLASS[instance.task_id]
    return cls(instance=instance, config=config)


__all__ = [
    "TaskStepResult",
    "BaseTask",
    "TaskA",
    "TaskB",
    "TaskC",
    "TaskD",
    "build_task",
]
