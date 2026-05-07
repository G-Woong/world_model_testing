"""RG4FEnv 메인 클래스.

PART0 / PART1 / PART2 / PART3 / RG4F_Environment_Plan / SESSION1_HANDOFF의
모든 환경 측면을 한 곳에 모은 reset/step/observe 컨트랙트.

핵심 책임:
1. seed-deterministic reset/step.
2. control-drift remap + 약한 stochastic miscontrol + (옵션) 주기적 slip.
3. mobility cooldown / latency (control-drift와 분리된 채널!).
4. invisible field의 sparse coupling effect + small drift + event-triggered shift.
5. Task A/B/C/D state machine 호출.
6. reward decomposition (PART2 §3.12). ``λ_plan C^plan``은 환경이 채우지 않는다.
7. info/debug에 ``true_state`` / ``true_regime`` / ``change_point`` /
   ``reveal_event`` / ``shift_event`` / ``target_band`` / ``field_info`` 노출.
8. dataset 저장, 모델, planner 코드는 ABSOLUTELY 포함하지 않는다.
"""
from __future__ import annotations

import math
from copy import deepcopy
from dataclasses import asdict
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from .config import RG4FConfig
from .fields import (
    apply_event_shift,
    apply_small_drift,
    evaluate_field_effects,
    summarize_fields_for_info,
)
from .map_generator import EpisodeLayout, GridLayout, build_episode
from .observation import build_observation
from .tasks import BaseTask, build_task
from .types import (
    ACTION_TO_DIRECTION,
    Action,
    AgentState,
    CellType,
    ControlMode,
    DIR_DELTA,
    Direction,
    EventToken,
    FieldFamily,
    MOVE_ACTIONS,
    MobilityMode,
    Position,
    RegimeState,
    RoomID,
    STATE_ADJUST_TABLE,
    StateDim,
    StepDebug,
    TASK_ROOM_IDS,
    TargetBandInfo,
    TaskID,
)


# =============================================================================
# Control-drift remap 테이블 / 인접 action
# =============================================================================

# Action → Action mapping per ControlMode (4-방향 grid 한정)
_CONTROL_REMAP: Dict[ControlMode, Dict[Action, Action]] = {
    ControlMode.IDENTITY: {Action.W: Action.W, Action.A: Action.A, Action.S: Action.S, Action.D: Action.D},
    ControlMode.CW:       {Action.W: Action.D, Action.D: Action.S, Action.S: Action.A, Action.A: Action.W},
    ControlMode.LR:       {Action.W: Action.W, Action.S: Action.S, Action.A: Action.D, Action.D: Action.A},
    ControlMode.UD:       {Action.W: Action.S, Action.S: Action.W, Action.A: Action.A, Action.D: Action.D},
    ControlMode.REV:      {Action.W: Action.S, Action.S: Action.W, Action.A: Action.D, Action.D: Action.A},
}


# 90° 인접 방향 (stochastic miscontrol slip 후보)
_NEIGHBOR_ACTIONS: Dict[Action, Tuple[Action, Action]] = {
    Action.W: (Action.A, Action.D),
    Action.S: (Action.A, Action.D),
    Action.A: (Action.W, Action.S),
    Action.D: (Action.W, Action.S),
}


_STR_TO_CONTROL_MODE: Dict[str, ControlMode] = {
    "identity": ControlMode.IDENTITY,
    "cw": ControlMode.CW,
    "lr": ControlMode.LR,
    "ud": ControlMode.UD,
    "rev": ControlMode.REV,
}


# =============================================================================
# RG4FEnv
# =============================================================================

class RG4FEnv:
    """RegimeGrid-4Room Factorized Tasks 환경.

    Gymnasium-like API (gymnasium 의존 없음. dict obs).
    """

    metadata: Dict[str, object] = {"render_modes": ["ascii"]}

    # =========================================================================
    # init
    # =========================================================================
    def __init__(self, config: RG4FConfig, seed: int = 42) -> None:
        self.config: RG4FConfig = config
        self._initial_seed: int = int(seed)
        self._rng: np.random.Generator = np.random.default_rng(self._initial_seed)

        # episode-level state (reset에서 채워짐)
        self._episode: Optional[EpisodeLayout] = None
        self._tasks_by_room: Dict[RoomID, BaseTask] = {}
        self._tasks_by_id: Dict[TaskID, BaseTask] = {}
        self._agent: Optional[AgentState] = None
        self._regime: RegimeState = RegimeState()
        self._step_count: int = 0
        self._completed_tasks: int = 0
        self._fail_count: int = 0
        self._wrong_interaction_count: int = 0
        self._last_event: EventToken = EventToken.NONE
        self._terminated: bool = False
        self._truncated: bool = False
        # change-point ground truth: regime이 이번 tick에 변화했는지
        self._change_point: bool = False
        # 마지막 reward decomposition (debug)
        self._last_reward_components: Dict[str, float] = {}

    # =========================================================================
    # reset
    # =========================================================================
    def reset(self, seed: Optional[int] = None) -> Tuple[Dict[str, np.ndarray], Dict[str, Any]]:
        """deterministic reset. ``seed=None``이면 ``__init__`` seed 재사용."""
        if seed is not None:
            self._initial_seed = int(seed)
        self._rng = np.random.default_rng(self._initial_seed)

        # episode layout / task instances / fields 생성
        self._episode = build_episode(self.config, self._rng)
        self._tasks_by_room = {}
        self._tasks_by_id = {}
        for room_id, task_id in self._episode.permutation.items():
            inst = self._episode.task_instances[task_id]
            t = build_task(inst, self.config)
            t.reset(self._rng)
            self._tasks_by_room[room_id] = t
            self._tasks_by_id[task_id] = t

        # agent
        self._agent = AgentState(
            position=self._episode.layout.start_position,
            state_vec=[0.0, 0.0, 0.0, 0.0, 0.0],
            move_cooldown=0,
            carrying_weight=0.0,
            carrying_piece_id=None,
            current_room=RoomID.CENTRAL_HALL,
        )

        # regime sampling
        self._regime = self._sample_initial_regime(self._rng)

        # episode counters
        self._step_count = 0
        self._completed_tasks = 0
        self._fail_count = 0
        self._wrong_interaction_count = 0
        self._last_event = EventToken.NONE
        self._terminated = False
        self._truncated = False
        self._change_point = True   # 첫 step은 regime 결정 시점이므로 change-point로 표기
        self._last_reward_components = {}

        obs = self._build_obs()
        info = self._build_info(StepDebug(), reset_flag=True)
        return obs, info

    def _sample_initial_regime(self, rng: np.random.Generator) -> RegimeState:
        # control mode: 절반 확률로 identity, 그 외에는 다른 mode 샘플링
        if rng.random() < self.config.initial_identity_prob:
            mode = ControlMode.IDENTITY
        else:
            modes = [_STR_TO_CONTROL_MODE[m] for m in self.config.drift_abrupt_remap_modes]
            mode = ControlMode(int(rng.choice(modes)))

        # 매 episode 한 번 sampling되는 base miscontrol p
        p_low = self.config.miscontrol_p_low
        p_high = self.config.miscontrol_p_high
        # 평소 슬립 확률 p_low; periodic slip이 켜졌을 때만 K마다 p_high로 점프 (step 함수에서 처리)
        active_field_families = []
        if self._episode is not None:
            active_field_families = list({f.family for f in self._episode.invisible_fields})
        return RegimeState(
            control_mode=mode,
            mobility_mode=MobilityMode.NORMAL,
            miscontrol_p=p_low,
            periodic_slip_active=False,
            periodic_K=self.config.periodic_slip_period,
            active_field_families=tuple(active_field_families),
        )

    # =========================================================================
    # step
    # =========================================================================
    def step(self, action: Any) -> Tuple[Dict[str, np.ndarray], float, bool, bool, Dict[str, Any]]:
        """raw action을 받아 한 tick을 진행. Gymnasium-like 5-tuple 반환."""
        if self._episode is None or self._agent is None:
            raise RuntimeError("RG4FEnv.step called before reset()")
        if self._terminated or self._truncated:
            raise RuntimeError(
                "RG4FEnv.step called after episode end. Call reset() before stepping again."
            )

        debug = StepDebug()
        # action 정규화
        try:
            raw_action = Action(int(action))
        except (ValueError, TypeError) as exc:
            raise ValueError(f"invalid action: {action!r}") from exc
        debug.raw_action = int(raw_action)

        # ---- 1. control-drift remap + miscontrol (이동 action에만 적용) ----
        # periodic slip: t mod K == 0이면 p_slip = p_high
        if (
            self.config.enable_periodic_slip
            and self._regime.periodic_K > 0
            and self._step_count % self._regime.periodic_K == 0
        ):
            self._regime.periodic_slip_active = True
            self._regime.miscontrol_p = self.config.miscontrol_p_high
        else:
            self._regime.periodic_slip_active = False
            self._regime.miscontrol_p = self.config.miscontrol_p_low

        effective_action = self._apply_control_drift(raw_action, debug)
        debug.effective_action = int(effective_action)

        # ---- 2. action 실행 ----
        prev_position = self._agent.position
        prev_room = self._agent.current_room

        # latency_cost / failure_cost / reset_cost 누적용
        latency_cost = 0.0
        failure_cost = 0.0
        reset_cost = 0.0

        # state-level deltas (env 단계에서만 더하는 누적)
        state_deltas: Dict[int, float] = {}
        forced_reset = False
        reveal_event = False
        shift_event = False
        event_token = EventToken.NONE

        if effective_action in MOVE_ACTIONS:
            debug.move_attempted = True
            if self._agent.move_cooldown > 0:
                # cooldown 중. 이동 실패. latency_cost 추가.
                debug.cooldown_blocked = True
                latency_cost += self.config.step_cost  # cooldown 동안 추가 latency 부과
            else:
                direction = ACTION_TO_DIRECTION[effective_action]
                drow, dcol = DIR_DELTA[direction]
                target = self._agent.position.shifted(drow, dcol)
                if self._episode.layout.is_traversable(target):
                    self._agent.position = target
                    debug.move_succeeded = True
                    debug.moved_into_cell_type = int(self._episode.layout.cells[target.row, target.col])
                    # cooldown 설정 (mobility에 의존; carry 시 추가)
                    cd = self._compute_movement_cooldown()
                    self._agent.move_cooldown = max(0, cd - 1)  # 이번 step이 1tick을 사용
                    # mobility latency cost: cooldown이 1보다 크면 추가 비용
                    if cd > 1:
                        latency_cost += float(cd - 1) * self.config.step_cost * 0.25
                else:
                    # 벽 충돌. 이동 실패. (control-drift miscontrol 때문일 수도 있음)
                    debug.move_succeeded = False
                    latency_cost += self.config.step_cost * 0.5

        elif effective_action == Action.E:
            debug.interaction_attempted = True
            # 현재 cell의 task에 interact 위임
            task = self._active_task()
            if task is not None:
                res = task.interact(self._agent, self._rng)
                event_token = res.event_token
                debug.interaction_outcome = res.outcome
                self._merge_state_deltas(state_deltas, res.state_deltas)
                reveal_event = reveal_event or res.reveal_event
                shift_event = shift_event or res.shift_event
                forced_reset = forced_reset or res.forced_reset
                if res.outcome == "fail":
                    self._fail_count += 1
                    failure_cost += self.config.failure_cost_weight
                if res.outcome == "pickup":
                    # carrying weight 갱신: pickup 직후 piece weight를 carrying에 반영
                    if "task_a_carrying_weight" in res.debug:
                        self._agent.carrying_weight = float(
                            res.debug["task_a_carrying_weight"]
                        )
                debug.extras.update(res.debug)
            # interaction이 task와 무관한 cell이면 outcome="none" (reward 영향 없음)

        elif effective_action in STATE_ADJUST_TABLE:
            sdim, sign = STATE_ADJUST_TABLE[effective_action]
            debug.state_adjust_dim = int(sdim)
            debug.state_adjust_sign = float(sign)
            delta = sign * self.config.state_adjust_delta
            self._merge_state_deltas(state_deltas, {sdim: delta})

        elif effective_action == Action.WAIT:
            pass   # noop. step_cost만 적용.

        # ---- 3. tile-induced step effects (Task D 등 — agent의 새 위치에서 발동) ----
        task = self._active_task()
        if task is not None:
            res = task.step(self._agent, prev_position, self._rng)
            if res.event_token != EventToken.NONE:
                event_token = res.event_token
            self._merge_state_deltas(state_deltas, res.state_deltas)
            reveal_event = reveal_event or res.reveal_event
            shift_event = shift_event or res.shift_event
            forced_reset = forced_reset or res.forced_reset
            debug.extras.update(res.debug)

        # ---- 4. 방 전환 & on_enter_room hook ----
        new_room = self._room_of_agent()
        if new_room != prev_room:
            self._agent.current_room = new_room
            if event_token == EventToken.NONE:
                event_token = EventToken.ROOM_ENTRY if new_room in TASK_ROOM_IDS else EventToken.ROOM_EXIT
            # 새 방의 task가 있으면 on_enter_room 호출
            if new_room in self._tasks_by_room:
                t2 = self._tasks_by_room[new_room]
                res = t2.on_enter_room(self._agent, self._rng)
                self._merge_state_deltas(state_deltas, res.state_deltas)
                shift_event = shift_event or res.shift_event
                debug.extras.update(res.debug)

            # event-triggered field shift 가능성 (방 진입 시)
            shifted, idx = apply_event_shift(
                self._episode.invisible_fields, self.config, self._rng, "room_entry"
            )
            if shifted:
                shift_event = True
                debug.field_event_shift_applied = True
                debug.extras["shifted_field_indices"] = idx

        # ---- 5. control-drift small cumulative + clip ----
        if self.config.enable_control_drift_cumulative:
            d_eps = float(self._rng.uniform(
                self.config.control_drift_step_min,
                self.config.control_drift_step_max,
            ))
            state_deltas[int(StateDim.CONTROL_DRIFT)] = state_deltas.get(
                int(StateDim.CONTROL_DRIFT), 0.0,
            ) + d_eps

        # ---- 6. invisible field effect (sparse coupling) ----
        if self.config.enable_invisible_fields and self._episode.invisible_fields:
            field_effect = evaluate_field_effects(
                self._episode.invisible_fields, self._agent.position, self._rng,
            )
            if field_effect:
                self._merge_state_deltas(state_deltas, field_effect)
                debug.field_effect = dict(field_effect)
            # field mean small drift는 매 tick 적용
            applied = apply_small_drift(self._episode.invisible_fields, self.config, self._rng)
            debug.field_drift_applied = applied

        # ---- 7. state vector update + clip ----
        self._apply_state_deltas(state_deltas)

        # ---- 8. forced reset (Task D 3-fail) ----
        if forced_reset:
            self._agent.position = self._episode.layout.start_position
            self._agent.current_room = RoomID.CENTRAL_HALL
            self._agent.move_cooldown = 0
            self._agent.carrying_weight = 0.0
            reset_cost += self.config.reset_cost_weight
            event_token = EventToken.FORCED_RESET

        # ---- 9. task 완료 카운트 ----
        completed_now = sum(1 for t in self._tasks_by_id.values() if t.is_completed())
        new_completion = completed_now > self._completed_tasks
        self._completed_tasks = completed_now

        # ---- 10. cooldown 감소 (cooldown은 step당 1씩) ----
        if self._agent.move_cooldown > 0:
            self._agent.move_cooldown -= 1

        # ---- 11. change_point: regime이 바뀌었는지 ----
        # mobility_mode/control_mode/active_field_family 등이 이번 step에서 변경되었는지
        # 본 환경에서 control_mode change는 event-triggered abrupt remap shift에서만 발생.
        change_point = shift_event   # shift_event = regime change
        self._change_point = change_point
        debug.change_point = change_point
        debug.reveal_event = reveal_event
        debug.shift_event = shift_event

        # ---- 12. reward 계산 ----
        step_cost = self.config.step_cost
        task_reward = 0.0
        completion_reward = 0.0
        if new_completion:
            task_reward += self.config.task_reward
        if self._completed_tasks >= len(TaskID) and not self._terminated:
            self._terminated = True
            completion_reward += self.config.completion_reward

        reward = (
            task_reward
            + completion_reward
            - self.config.lambda_step * step_cost
            - self.config.lambda_latency * latency_cost
            - self.config.lambda_failure * failure_cost
            - self.config.lambda_reset * reset_cost
        )
        self._last_reward_components = {
            "task_reward": float(task_reward),
            "completion_reward": float(completion_reward),
            "step_cost": float(step_cost),
            "latency_cost": float(latency_cost),
            "failure_cost": float(failure_cost),
            "reset_cost": float(reset_cost),
            "total": float(reward),
        }

        # ---- 13. termination / truncation ----
        self._step_count += 1
        if self._step_count >= self.config.episode_max_steps and not self._terminated:
            self._truncated = True

        # ---- 14. event_token 저장 + obs/info 빌드 ----
        self._last_event = event_token
        obs = self._build_obs()
        info = self._build_info(debug, reset_flag=False)

        return obs, float(reward), self._terminated, self._truncated, info

    # =========================================================================
    # observe (현재 obs를 다시 빌드. step과 reset 사이에 한 번 더 호출 가능)
    # =========================================================================
    def observe(self) -> Dict[str, np.ndarray]:
        if self._episode is None or self._agent is None:
            raise RuntimeError("RG4FEnv.observe called before reset()")
        return self._build_obs()

    # =========================================================================
    # render
    # =========================================================================
    def render_ascii(self) -> str:
        """ASCII 렌더링 (디버그용)."""
        if self._episode is None or self._agent is None:
            return "<env not reset>"
        layout = self._episode.layout
        rows: List[str] = []
        for r in range(layout.full_h):
            line: List[str] = []
            for c in range(layout.full_w):
                if (r, c) == self._agent.position.as_tuple():
                    ch = "@"
                else:
                    cell = int(layout.cells[r, c])
                    if cell == int(CellType.WALL):
                        ch = "#"
                    elif cell == int(CellType.FLOOR):
                        ch = "."
                    elif cell == int(CellType.CORRIDOR):
                        ch = "-"
                    elif cell == int(CellType.DOOR):
                        ch = "+"
                    else:
                        ch = "?"
                line.append(ch)
            rows.append("".join(line))
        return "\n".join(rows)

    # =========================================================================
    # debug snapshot (Session 4의 inspect_episode가 사용 가능)
    # =========================================================================
    def get_debug_state(self) -> Dict[str, Any]:
        if self._episode is None or self._agent is None:
            return {"reset": False}
        return {
            "reset": True,
            "step": self._step_count,
            "agent_position": self._agent.position.as_tuple(),
            "current_room": int(self._agent.current_room),
            "state_vec": list(self._agent.state_vec),
            "completed_tasks": self._completed_tasks,
            "fail_count": self._fail_count,
            "regime": asdict(self._regime),
            "permutation": {int(k): int(v) for k, v in self._episode.permutation.items()},
            "fields": summarize_fields_for_info(self._episode.invisible_fields),
            "task_debug": {
                int(t.task_id): t.get_debug_info() for t in self._tasks_by_id.values()
            },
        }

    # =========================================================================
    # ----- internals -----
    # =========================================================================
    def _apply_control_drift(self, raw_action: Action, debug: StepDebug) -> Action:
        """control-drift remap + 약한 stochastic miscontrol을 raw_action에 적용.

        이동 action이 아닌 경우 그대로 반환. mobility cooldown은 별도 처리이며 본 함수에서
        다루지 않는다 (PART2 §3.10.2: mobility와 control-drift는 분리된 채널).
        """
        if raw_action not in MOVE_ACTIONS:
            return raw_action
        # ① 이산 remap
        mapped = _CONTROL_REMAP[self._regime.control_mode][raw_action]
        # ② 약한 stochastic miscontrol
        if self._regime.miscontrol_p > 0.0 and self._rng.random() < self._regime.miscontrol_p:
            neighbors = _NEIGHBOR_ACTIONS[mapped]
            slipped = neighbors[int(self._rng.integers(0, len(neighbors)))]
            debug.miscontrolled = True
            return slipped
        return mapped

    def _compute_movement_cooldown(self) -> int:
        """현재 mobility(+carrying)에 따른 ticks_per_move."""
        m_t = self._agent.state_vec[int(StateDim.MOBILITY)]
        kappa = self.config.mobility_cooldown_kappa
        alpha = self.config.mobility_cooldown_alpha
        denom = max(0.05, 1.0 + alpha * m_t)
        cd = max(1, int(math.ceil(kappa / denom)))
        if self._agent.carrying_weight != 0.0:
            cd += self.config.carry_cooldown_extra
        return cd

    def _merge_state_deltas(
        self, accumulator: Dict[int, float], extra: Dict[int, float],
    ) -> None:
        for k, v in extra.items():
            accumulator[int(k)] = accumulator.get(int(k), 0.0) + float(v)

    def _apply_state_deltas(self, deltas: Dict[int, float]) -> None:
        if not deltas:
            return
        clip_lo = self.config.state_clip_min
        clip_hi = self.config.state_clip_max
        for sdim, dv in deltas.items():
            new_val = float(self._agent.state_vec[int(sdim)]) + float(dv)
            self._agent.state_vec[int(sdim)] = float(np.clip(new_val, clip_lo, clip_hi))

    def _room_of_agent(self) -> RoomID:
        assert self._episode is not None
        return self._episode.layout.room_of(self._agent.position)

    def _active_task(self) -> Optional[BaseTask]:
        if self._episode is None:
            return None
        room = self._agent.current_room
        if room not in self._tasks_by_room:
            return None
        return self._tasks_by_room[room]

    # =========================================================================
    # obs / info 빌더
    # =========================================================================
    def _build_obs(self) -> Dict[str, np.ndarray]:
        assert self._episode is not None and self._agent is not None
        return build_observation(
            config=self.config,
            layout=self._episode.layout,
            agent_state=self._agent,
            tasks_by_room=self._tasks_by_room,
            completed_count=self._completed_tasks,
            fail_count=self._fail_count,
            step=self._step_count,
            last_event=self._last_event,
        )

    def _current_target_band(self) -> TargetBandInfo:
        task = self._active_task()
        if task is None or self._agent is None:
            return TargetBandInfo(active=False)
        return task.get_target_band(self._agent)

    def _build_info(self, debug: StepDebug, reset_flag: bool) -> Dict[str, Any]:
        assert self._episode is not None and self._agent is not None
        # true_state: 5차원 상태값의 정확한 ground truth (obs에는 노출 안 됨)
        true_state = {
            "vision": float(self._agent.state_vec[int(StateDim.VISION)]),
            "mobility": float(self._agent.state_vec[int(StateDim.MOBILITY)]),
            "interaction": float(self._agent.state_vec[int(StateDim.INTERACTION)]),
            "noise": float(self._agent.state_vec[int(StateDim.NOISE)]),
            "control_drift": float(self._agent.state_vec[int(StateDim.CONTROL_DRIFT)]),
        }
        # true_regime: factorized regime ground truth
        true_regime = {
            "control_mode": int(self._regime.control_mode),
            "mobility_mode": int(self._regime.mobility_mode),
            "miscontrol_p": float(self._regime.miscontrol_p),
            "periodic_slip_active": bool(self._regime.periodic_slip_active),
            "active_field_families": [int(f) for f in self._regime.active_field_families],
        }
        # 현재 활성 task / room / target band
        current_room = self._agent.current_room
        active_task = self._active_task()
        if active_task is not None:
            task_id = int(active_task.task_id)
            task_debug = active_task.get_debug_info()
        else:
            task_id = -1
            task_debug = {}

        target_band_info = self._current_target_band()
        target_band_payload = None
        if target_band_info.active:
            target_band_payload = {
                "state_dim": int(target_band_info.state_dim) if target_band_info.state_dim is not None else -1,
                "center": float(target_band_info.center),
                "half_width": float(target_band_info.half_width),
                "kind": str(target_band_info.kind),
            }

        info: Dict[str, Any] = {
            "true_state": true_state,
            "true_regime": true_regime,
            "change_point": bool(self._change_point),
            "reveal_or_shift": (
                "shift" if debug.shift_event
                else ("reveal" if debug.reveal_event else "none")
            ),
            "reveal_event": bool(debug.reveal_event),
            "shift_event": bool(debug.shift_event),
            "task_id": task_id,
            "room_id": int(current_room),
            "event_token": int(self._last_event),
            "raw_action": int(debug.raw_action),
            "effective_action": int(debug.effective_action),
            "tick_cost": float(self.config.step_cost),
            "latency_cost": float(self._last_reward_components.get("latency_cost", 0.0)),
            "failure_count": int(self._fail_count),
            "reset_flag": bool(reset_flag),
            "target_band": target_band_payload,
            "field_info": summarize_fields_for_info(self._episode.invisible_fields),
            "local_obs_size": int(self.config.local_obs_size),
            "agent_position": self._agent.position.as_tuple(),
            "completed_tasks": int(self._completed_tasks),
            "wrong_interaction_count": int(self._wrong_interaction_count),
            "control_mode": int(self._regime.control_mode),
            "mobility_mode": int(self._regime.mobility_mode),
            "step_cost": float(self._last_reward_components.get("step_cost", self.config.step_cost)),
            "failure_cost": float(self._last_reward_components.get("failure_cost", 0.0)),
            "reset_cost": float(self._last_reward_components.get("reset_cost", 0.0)),
            "task_reward": float(self._last_reward_components.get("task_reward", 0.0)),
            "completion_reward": float(self._last_reward_components.get("completion_reward", 0.0)),
            "permutation": {int(k): int(v) for k, v in self._episode.permutation.items()},
            "task_debug": task_debug,
            # 풍부한 step-level 디버그 trace (dataset generator / falsification metric용)
            "debug": {
                "raw_action": int(debug.raw_action),
                "effective_action": int(debug.effective_action),
                "miscontrolled": bool(debug.miscontrolled),
                "move_attempted": bool(debug.move_attempted),
                "move_succeeded": bool(debug.move_succeeded),
                "moved_into_cell_type": int(debug.moved_into_cell_type),
                "interaction_attempted": bool(debug.interaction_attempted),
                "interaction_outcome": str(debug.interaction_outcome),
                "state_adjust_dim": (
                    int(debug.state_adjust_dim)
                    if debug.state_adjust_dim is not None else -1
                ),
                "state_adjust_sign": float(debug.state_adjust_sign),
                "cooldown_blocked": bool(debug.cooldown_blocked),
                "field_effect": {int(k): float(v) for k, v in debug.field_effect.items()},
                "field_drift_applied": bool(debug.field_drift_applied),
                "field_event_shift_applied": bool(debug.field_event_shift_applied),
                "reveal_event": bool(debug.reveal_event),
                "shift_event": bool(debug.shift_event),
                "change_point": bool(debug.change_point),
                "extras": dict(debug.extras),
            },
        }
        return info


__all__ = [
    "RG4FEnv",
]
