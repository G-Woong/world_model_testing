"""Episode trajectory → numpy array dict 직렬화 헬퍼.

Session 3에서 ``scripts/generate_dataset.py``가 환경을 굴려 모은 step-단위 transition
list를 디스크 친화적인 numeric array dict로 변환한다.

설계 원칙:
- 학습에 필요한 주요 supervision 신호는 모두 numeric array로 저장한다.
- string/list-of-dict 같은 비정형 metadata는 별도 ``episode_meta`` dict로 분리하여
  npz 본체와 분리해 ``episode_meta.json``에 저장한다.
- info dict 전체를 그대로 pickle/object array로 dump하지 않는다.
- ``next_observations_*``는 (T, ...) shape으로 저장한다 (마지막 timestep은 final obs).

PART0 §3 §11과 정합: model/planner/agent latent (z_t, q_t(r))는 절대 저장하지 않는다.
ground-truth (true_state/true_regime/change_point/reveal/shift)만 저장한다.
"""
from __future__ import annotations

from typing import Any, Dict, List

import numpy as np


# =============================================================================
# 인코딩 상수: reveal_or_shift / target_band kind 등 string을 정수로 인코딩
# =============================================================================

REVEAL_SHIFT_NONE: int = 0
REVEAL_SHIFT_REVEAL: int = 1
REVEAL_SHIFT_SHIFT: int = 2

REVEAL_SHIFT_TO_INT: Dict[str, int] = {
    "none": REVEAL_SHIFT_NONE,
    "reveal": REVEAL_SHIFT_REVEAL,
    "shift": REVEAL_SHIFT_SHIFT,
}

# target_band.kind string → int. 없으면 -1.
TARGET_BAND_KIND_TO_INT: Dict[str, int] = {
    "none": 0,
    "match_to_band": 1,
    "maximize": 2,
    "threshold": 3,
    "derivative_zero": 4,
}


# =============================================================================
# 한 step의 transition을 받는 데이터 클래스 대신 dict 사용
# (외부 generator가 채워준다)
# =============================================================================

class EpisodeBuffer:
    """한 episode의 transition을 모으는 in-memory buffer.

    generator는 다음 순서로 buffer를 채운다:
        buf = EpisodeBuffer()
        obs0, info0 = env.reset()
        buf.set_initial(obs0, info0)
        for t in range(T):
            action = policy(obs_t)
            next_obs, reward, term, trunc, info = env.step(action)
            buf.append(action_raw=..., next_obs=next_obs, reward=..., terminated=...,
                        truncated=..., info=info)
            if term or trunc: break
        arrays, meta = buf.finalize(field_info_static)
        np.savez_compressed(path, **arrays)
        json.dump(meta, ...)
    """

    def __init__(self) -> None:
        # 관측 시퀀스: t=0..T-1 (현재 obs), t+1: next_obs
        self._obs_local: List[np.ndarray] = []
        self._obs_scalar: List[np.ndarray] = []
        self._obs_event: List[int] = []
        # 다음 관측 시퀀스 (length T)
        self._next_local: List[np.ndarray] = []
        self._next_scalar: List[np.ndarray] = []
        self._next_event: List[int] = []
        # actions / rewards / done / truncated
        self._actions_raw: List[int] = []
        self._actions_eff: List[int] = []
        self._rewards: List[float] = []
        self._terminateds: List[bool] = []
        self._truncateds: List[bool] = []
        # supervision: ground-truth (info에서 추출)
        self._true_state: List[np.ndarray] = []
        self._true_regime_control_mode: List[int] = []
        self._true_regime_mobility_mode: List[int] = []
        self._true_regime_miscontrol_p: List[float] = []
        self._true_regime_periodic_slip: List[bool] = []
        self._change_point: List[bool] = []
        self._reveal_event: List[bool] = []
        self._shift_event: List[bool] = []
        self._reveal_or_shift: List[int] = []
        # task / room / event
        self._task_id: List[int] = []
        self._room_id: List[int] = []
        self._event_token: List[int] = []
        # target band: active / state_dim / center / half_width / kind_int
        self._tband_active: List[bool] = []
        self._tband_state_dim: List[int] = []
        self._tband_center: List[float] = []
        self._tband_halfw: List[float] = []
        self._tband_kind: List[int] = []
        # field_info dynamic (mu / sigma / last_effect는 step마다 변함)
        # field 수는 episode 시작 시 결정되고 episode 동안 고정. shape (T, F).
        self._field_mu: List[List[float]] = []
        self._field_sigma: List[List[float]] = []
        # agent / counters / cost
        self._agent_pos: List[np.ndarray] = []
        self._completed: List[int] = []
        self._failures: List[int] = []
        self._tick_cost: List[float] = []
        self._latency_cost: List[float] = []
        self._failure_cost: List[float] = []
        self._reset_cost: List[float] = []
        self._task_reward: List[float] = []
        self._completion_reward: List[float] = []
        self._reset_flag: List[bool] = []
        # 디버그 trace (optional)
        self._debug_trace: List[Dict[str, Any]] = []

        # initial obs/info (reset 직후 한 번만 채워짐)
        self._initial_obs: Dict[str, np.ndarray] | None = None
        self._initial_info: Dict[str, Any] | None = None

        # episode-level metadata (reset 시 결정되는 정적 정보)
        self._episode_seed: int | None = None
        self._permutation: Dict[int, int] | None = None
        self._field_info_static: List[Dict[str, Any]] | None = None
        self._initial_regime: Dict[str, Any] | None = None

    # ---------------------------------------------------------------------
    # 채움 API
    # ---------------------------------------------------------------------
    def set_initial(
        self,
        obs: Dict[str, np.ndarray],
        info: Dict[str, Any],
        episode_seed: int,
    ) -> None:
        self._initial_obs = {k: np.asarray(v).copy() for k, v in obs.items()}
        self._initial_info = info
        self._episode_seed = int(episode_seed)
        # 정적 metadata 추출
        self._permutation = {int(k): int(v) for k, v in info.get("permutation", {}).items()}
        self._field_info_static = [
            {
                "family": int(f["family"]),
                "source_row": int(f["source_row"]),
                "source_col": int(f["source_col"]),
                "radius": float(f["radius"]),
                "sigma_init": float(f["sigma"]),
                "coupled_states": [int(s) for s in f["coupled_states"]],
            }
            for f in info.get("field_info", [])
        ]
        self._initial_regime = dict(info.get("true_regime", {}))

    def append(
        self,
        action_raw: int,
        action_effective: int,
        next_obs: Dict[str, np.ndarray],
        reward: float,
        terminated: bool,
        truncated: bool,
        info: Dict[str, Any],
    ) -> None:
        """한 step의 transition을 buffer에 추가한다."""
        if self._initial_obs is None:
            raise RuntimeError("EpisodeBuffer.set_initial() must be called before append().")

        # 이번 step의 obs는 직전 step의 next_obs (또는 t==0이면 initial obs)
        if not self._obs_local:
            cur_obs = self._initial_obs
        else:
            cur_obs = {
                "local_grid": self._next_local[-1],
                "scalar": self._next_scalar[-1],
                "event_token": np.int32(self._next_event[-1]),
            }
        self._obs_local.append(np.asarray(cur_obs["local_grid"], dtype=np.float32))
        self._obs_scalar.append(np.asarray(cur_obs["scalar"], dtype=np.float32))
        self._obs_event.append(int(cur_obs["event_token"]))

        self._next_local.append(np.asarray(next_obs["local_grid"], dtype=np.float32))
        self._next_scalar.append(np.asarray(next_obs["scalar"], dtype=np.float32))
        self._next_event.append(int(next_obs["event_token"]))

        self._actions_raw.append(int(action_raw))
        self._actions_eff.append(int(action_effective))
        self._rewards.append(float(reward))
        self._terminateds.append(bool(terminated))
        self._truncateds.append(bool(truncated))

        ts = info.get("true_state", {})
        self._true_state.append(np.asarray(
            [
                float(ts.get("vision", 0.0)),
                float(ts.get("mobility", 0.0)),
                float(ts.get("interaction", 0.0)),
                float(ts.get("noise", 0.0)),
                float(ts.get("control_drift", 0.0)),
            ],
            dtype=np.float32,
        ))
        tr = info.get("true_regime", {})
        self._true_regime_control_mode.append(int(tr.get("control_mode", 0)))
        self._true_regime_mobility_mode.append(int(tr.get("mobility_mode", 0)))
        self._true_regime_miscontrol_p.append(float(tr.get("miscontrol_p", 0.0)))
        self._true_regime_periodic_slip.append(bool(tr.get("periodic_slip_active", False)))

        self._change_point.append(bool(info.get("change_point", False)))
        self._reveal_event.append(bool(info.get("reveal_event", False)))
        self._shift_event.append(bool(info.get("shift_event", False)))
        self._reveal_or_shift.append(
            REVEAL_SHIFT_TO_INT.get(str(info.get("reveal_or_shift", "none")), REVEAL_SHIFT_NONE)
        )

        self._task_id.append(int(info.get("task_id", -1)))
        self._room_id.append(int(info.get("room_id", -1)))
        self._event_token.append(int(info.get("event_token", 0)))

        tb = info.get("target_band")
        if tb is None:
            self._tband_active.append(False)
            self._tband_state_dim.append(-1)
            self._tband_center.append(0.0)
            self._tband_halfw.append(0.0)
            self._tband_kind.append(0)
        else:
            self._tband_active.append(True)
            self._tband_state_dim.append(int(tb.get("state_dim", -1)))
            self._tband_center.append(float(tb.get("center", 0.0)))
            self._tband_halfw.append(float(tb.get("half_width", 0.0)))
            self._tband_kind.append(
                TARGET_BAND_KIND_TO_INT.get(str(tb.get("kind", "none")), 0)
            )

        # field dynamic (mu / sigma per field. coupled_states는 정적이므로 metadata로 분리)
        fields = info.get("field_info", []) or []
        self._field_mu.append([float(f.get("mu", 0.0)) for f in fields])
        self._field_sigma.append([float(f.get("sigma", 0.0)) for f in fields])

        ap = info.get("agent_position", (0, 0))
        self._agent_pos.append(np.asarray([int(ap[0]), int(ap[1])], dtype=np.int32))
        self._completed.append(int(info.get("completed_tasks", 0)))
        self._failures.append(int(info.get("failure_count", 0)))
        self._tick_cost.append(float(info.get("tick_cost", 0.0)))
        self._latency_cost.append(float(info.get("latency_cost", 0.0)))
        self._failure_cost.append(float(info.get("failure_cost", 0.0)))
        self._reset_cost.append(float(info.get("reset_cost", 0.0)))
        self._task_reward.append(float(info.get("task_reward", 0.0)))
        self._completion_reward.append(float(info.get("completion_reward", 0.0)))
        self._reset_flag.append(bool(info.get("reset_flag", False)))

        # debug trace는 dict 형태. dataset 저장 시 metadata로 옮긴다 (optional).
        if "debug" in info:
            self._debug_trace.append({
                k: v for k, v in info["debug"].items()
                # 너무 많은 데이터(extras)는 제외 — 핵심 step-level flag만 저장
                if k in (
                    "miscontrolled", "move_attempted", "move_succeeded",
                    "interaction_attempted", "interaction_outcome",
                    "cooldown_blocked", "field_drift_applied",
                    "field_event_shift_applied",
                )
            })

    # ---------------------------------------------------------------------
    # 마무리: 모은 transition을 numeric array dict + episode_meta dict로 변환
    # ---------------------------------------------------------------------
    def finalize(
        self,
        save_debug_trace: bool = True,
    ) -> "tuple[Dict[str, np.ndarray], Dict[str, Any]]":
        """모은 transition을 numpy array dict + episode_meta dict로 반환한다.

        Returns
        -------
        arrays : Dict[str, np.ndarray]
            np.savez_compressed에 그대로 넘길 수 있는 numeric arrays.
        episode_meta : Dict[str, Any]
            정적 metadata (permutation / field_info / regime / debug_trace 등).
            json.dump 가능.
        """
        T = len(self._actions_raw)
        if T == 0:
            raise ValueError("Cannot finalize empty episode buffer (T=0).")

        # field 수는 episode 동안 고정 (None이거나 일관)
        # 일부 step에서 빈 list일 수 있는 edge-case는 0으로 통일
        F = max((len(mu) for mu in self._field_mu), default=0)

        def _pad_to_f(rows: List[List[float]]) -> np.ndarray:
            arr = np.zeros((T, F), dtype=np.float32)
            for t, row in enumerate(rows):
                if len(row) > 0:
                    arr[t, : len(row)] = np.asarray(row, dtype=np.float32)
            return arr

        arrays: Dict[str, np.ndarray] = {
            # 관측 (current)
            "observations_local_grid": np.stack(self._obs_local, axis=0),
            "observations_scalar": np.stack(self._obs_scalar, axis=0),
            "observations_event_token": np.asarray(self._obs_event, dtype=np.int32),
            # 다음 관측
            "next_observations_local_grid": np.stack(self._next_local, axis=0),
            "next_observations_scalar": np.stack(self._next_scalar, axis=0),
            "next_observations_event_token": np.asarray(self._next_event, dtype=np.int32),
            # action / reward / termination
            "actions_raw": np.asarray(self._actions_raw, dtype=np.int32),
            "actions_effective": np.asarray(self._actions_eff, dtype=np.int32),
            "rewards": np.asarray(self._rewards, dtype=np.float32),
            "dones": np.asarray(self._terminateds, dtype=bool),
            "truncateds": np.asarray(self._truncateds, dtype=bool),
            # ground-truth supervision
            "true_state": np.stack(self._true_state, axis=0),
            "true_regime_control_mode": np.asarray(self._true_regime_control_mode, dtype=np.int32),
            "true_regime_mobility_mode": np.asarray(self._true_regime_mobility_mode, dtype=np.int32),
            "true_regime_miscontrol_p": np.asarray(self._true_regime_miscontrol_p, dtype=np.float32),
            "true_regime_periodic_slip": np.asarray(self._true_regime_periodic_slip, dtype=bool),
            "change_point": np.asarray(self._change_point, dtype=bool),
            "reveal_event": np.asarray(self._reveal_event, dtype=bool),
            "shift_event": np.asarray(self._shift_event, dtype=bool),
            "reveal_or_shift": np.asarray(self._reveal_or_shift, dtype=np.int32),
            # task / room / event
            "task_id": np.asarray(self._task_id, dtype=np.int32),
            "room_id": np.asarray(self._room_id, dtype=np.int32),
            "event_token": np.asarray(self._event_token, dtype=np.int32),
            # target band
            "target_band_active": np.asarray(self._tband_active, dtype=bool),
            "target_band_state_dim": np.asarray(self._tband_state_dim, dtype=np.int32),
            "target_band_center": np.asarray(self._tband_center, dtype=np.float32),
            "target_band_half_width": np.asarray(self._tband_halfw, dtype=np.float32),
            "target_band_kind": np.asarray(self._tband_kind, dtype=np.int32),
            # field dynamic
            "field_info_mu": _pad_to_f(self._field_mu),
            "field_info_sigma": _pad_to_f(self._field_sigma),
            # agent / counters / cost
            "agent_position": np.stack(self._agent_pos, axis=0),
            "completed_tasks": np.asarray(self._completed, dtype=np.int32),
            "failure_count": np.asarray(self._failures, dtype=np.int32),
            "tick_cost": np.asarray(self._tick_cost, dtype=np.float32),
            "latency_cost": np.asarray(self._latency_cost, dtype=np.float32),
            "failure_cost": np.asarray(self._failure_cost, dtype=np.float32),
            "reset_cost": np.asarray(self._reset_cost, dtype=np.float32),
            "task_reward": np.asarray(self._task_reward, dtype=np.float32),
            "completion_reward": np.asarray(self._completion_reward, dtype=np.float32),
            "reset_flag": np.asarray(self._reset_flag, dtype=bool),
        }

        # episode metadata: 정적/비정형 데이터
        meta: Dict[str, Any] = {
            "episode_length": T,
            "episode_seed": self._episode_seed,
            "permutation": self._permutation or {},
            "initial_regime": self._initial_regime or {},
            "num_invisible_fields": F,
            "field_info_static": self._field_info_static or [],
            "obs_local_shape": list(self._next_local[0].shape),
            "obs_scalar_dim": int(self._next_scalar[0].shape[0]),
        }
        if save_debug_trace and self._debug_trace:
            meta["debug_trace"] = self._debug_trace
        return arrays, meta


__all__ = [
    "EpisodeBuffer",
    "REVEAL_SHIFT_TO_INT",
    "REVEAL_SHIFT_NONE",
    "REVEAL_SHIFT_REVEAL",
    "REVEAL_SHIFT_SHIFT",
    "TARGET_BAND_KIND_TO_INT",
]
