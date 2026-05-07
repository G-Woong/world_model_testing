"""RG-4F 환경의 설정 dataclass.

PART0 §3 금지사항: "config 없이 hard-coded 수치 박기 금지". 모든 environment-level
수치(공간 크기, drift 강도, target band 폭, reward weight 등)는 ``RG4FConfig``를
통해서만 흘러야 한다. 코드 내부에 magic number를 두는 것은 금지.

Session 2 단계에서는 yaml 파싱은 구현하지 않고 (Session 3 책임) dataclass default를
임시 값으로 둔다. ``configs/dataset_default.yaml``이 작성되면 ``from_dict`` /
``from_yaml`` 헬퍼만 추가하면 된다.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class RG4FConfig:
    """RG-4F 환경의 모든 수치를 한 곳에 모은 single source of truth.

    필드를 추가할 때는 반드시:
    1) ``__post_init__`` validation을 갱신한다.
    2) 의미를 docstring에 적는다.
    3) Session 3에서 yaml에 매핑될 수 있도록 primitive (int/float/list/tuple)로 둔다.
    """

    # =========================================================================
    # 1. seeding / determinism
    # =========================================================================
    seed: int = 42

    # =========================================================================
    # 2. 공간 구조 (RG4F_Environment_Plan §2.1)
    # =========================================================================
    hall_size: int = 9                  # 중앙홀 정사각 한 변 (interior)
    room_size: int = 8                  # 4방 정사각 한 변 (interior)
    corridor_length: int = 3            # hall ↔ room 연결 복도 길이
    return_to_hall_after_task: bool = True   # 한 task 완료 시 중앙홀로 자동 복귀

    # =========================================================================
    # 3. 부분관측 (RG4F_Environment_Plan §3)
    # =========================================================================
    # 메인 세팅: 5x5. ablation 시 3x3 또는 7x7로 변경.
    local_obs_size: int = 5
    # 허용되는 ablation 값. config 검증 시 local_obs_size가 이 집합 안인지 확인.
    local_obs_ablation_values: Tuple[int, ...] = (3, 5, 7)
    # vision level → cue mask. cue가 가려지기 시작하는 vision threshold.
    cue_visibility_threshold: float = -0.30

    # =========================================================================
    # 4. episode 길이 / 종료 조건
    # =========================================================================
    episode_max_steps: int = 600

    # =========================================================================
    # 5. 5개 상태값 동역학 (PART3 §3.17, RG4F_Environment_Plan §4)
    # =========================================================================
    # 상태값 자체의 [-1, 1] clipping 한계
    state_clip_min: float = -1.0
    state_clip_max: float = +1.0
    # 상태 조절 action 한 번이 만드는 변화량
    state_adjust_delta: float = 0.05
    # default target band (interaction altar / zero-mobility gate / noise-zero stele 공통 폭)
    target_band_width: float = 0.02
    # Task A의 τ_i 샘플링 범위
    task_a_target_range: Tuple[float, float] = (-0.20, 0.20)
    # τ_i sampling 격자 (U_{0.01})
    target_grid_step: float = 0.01

    # mobility cooldown 함수: cd(m) = max(1, ceil(kappa_m / (1 + alpha_m * m)))
    mobility_cooldown_kappa: float = 2.0
    mobility_cooldown_alpha: float = 1.5
    # 조각 운반 시 추가 cooldown (carry-induced burdened mobility)
    carry_cooldown_extra: int = 1

    # =========================================================================
    # 6. control-drift (PART2 §3.10, RG4F_Environment_Plan §5)
    # =========================================================================
    # 메인 환경에서 활성화되는 remap mode 후보. episode-level로 sampling.
    drift_strength_small_cumulative: float = 0.02
    drift_abrupt_remap_modes: Tuple[str, ...] = (
        "identity", "cw", "lr", "ud", "rev",
    )
    # episode 시작 시 initial control mode가 IDENTITY일 확률 (그렇지 않으면 위 후보 중 sampling)
    initial_identity_prob: float = 0.50
    # 약한 stochastic miscontrol p_slip
    miscontrol_p_low: float = 0.05
    miscontrol_p_high: float = 0.30
    # 주기적 slip period (adaptation/correction hard case ablation에서 활성)
    periodic_slip_period: int = 4
    enable_periodic_slip: bool = False
    # control-drift 자체의 small cumulative drift (d_t)
    enable_control_drift_cumulative: bool = True
    control_drift_step_min: float = -0.01
    control_drift_step_max: float = +0.03

    # =========================================================================
    # 7. event-triggered shift 확률 (RG4F_Environment_Plan §9)
    # =========================================================================
    enable_event_triggered_shift: bool = True
    shift_prob_per_room_entry: float = 0.20
    shift_prob_per_checkpoint: float = 0.40
    shift_prob_per_stele_activation: float = 0.30
    # event-triggered shift 시 field mean에 더해지는 점프 크기 ±delta
    event_shift_delta: float = 0.15
    # control mode이 shift될 때 mode를 다시 sampling

    # =========================================================================
    # 8. invisible noise field (RG4F_Environment_Plan §7)
    # =========================================================================
    enable_invisible_fields: bool = True
    # episode당 field 개수 (random sampling 범위)
    num_fields_min: int = 1
    num_fields_max: int = 2
    # sparse coupling 한도 (한 field가 영향을 줄 수 있는 state dim 수)
    field_coupling_max_dims: int = 2
    # field source 영향 반경 (cell 단위)
    field_radius_min: float = 3.0
    field_radius_max: float = 6.0
    # field 초기 mu / sigma
    field_mu_init_abs_max: float = 0.10
    field_sigma_init: float = 0.05
    # field mean small drift 표준편차 (매 tick 적용)
    field_mu_drift_sigma: float = 0.005

    # =========================================================================
    # 9. reward decomposition (PART2 §3.12)
    # =========================================================================
    # 각 component는 info에 분리되어 노출된다. agent/planner는 합산값과 분해값
    # 모두에 access 가능.
    step_cost: float = 1.0
    latency_cost_weight: float = 0.5
    failure_cost_weight: float = 5.0
    reset_cost_weight: float = 20.0
    task_reward: float = 50.0          # 한 task 완료 시
    completion_reward: float = 200.0   # 4 task 모두 완료 시
    # reward 합산 시 step_cost weight (보통 1로 두고 step_cost 자체로 조절)
    lambda_step: float = 1.0
    lambda_latency: float = 1.0
    lambda_failure: float = 1.0
    lambda_reset: float = 1.0

    # =========================================================================
    # 10. Task별 동작 파라미터
    # =========================================================================
    # Task A: 4개 piece의 weight set (heavy → light)
    task_a_piece_weights: Tuple[float, ...] = (0.80, 0.60, 0.40, 0.20)
    # Task A piece pickup 시 i, n에 한 번 적용되는 persistent shift 범위
    task_a_pickup_di_range: Tuple[float, float] = (-0.10, +0.10)
    task_a_pickup_dn_range: Tuple[float, float] = (-0.03, +0.03)

    # Task B: stele 4개 중 vision-positive 개수
    task_b_num_steles: int = 4
    task_b_num_positive: int = 2
    # stele ON 시 v, m, d에 적용되는 persistent shift 범위
    task_b_dv_range: Tuple[float, float] = (-0.10, +0.10)
    task_b_dm_range: Tuple[float, float] = (-0.10, +0.10)
    task_b_dd_range: Tuple[float, float] = (-0.03, +0.03)
    # zero-mobility gate band ([-α, +α])
    task_b_mobility_gate_half_width: float = 0.02
    # door open을 위한 vision 안정 조건 (마지막 N tick 동안 |Δv|=0)
    task_b_vision_stable_ticks: int = 2

    # Task C: 활성 stele 수 후보 / initial control-drift bin
    task_c_num_steles_choices: Tuple[int, ...] = (2, 3, 4)
    task_c_initial_d_bins: Tuple[float, ...] = (-0.70, -0.35, 0.00, +0.35, +0.70)
    # stele 활성 조건 noise band
    task_c_noise_zero_half_width: float = 0.02
    # 방향별 noise increment 범위 (per-direction noise step)
    task_c_dn_range: Tuple[float, float] = (-0.10, +0.10)

    # Task D: tile 영역 크기 / 누적 drift / final altar / fail reset
    task_d_num_tiles: int = 4
    task_d_tile_di_range: Tuple[float, float] = (-0.10, +0.10)
    task_d_tile_dn_range: Tuple[float, float] = (-0.05, +0.05)
    task_d_tile_dv_range: Tuple[float, float] = (-0.03, +0.03)
    task_d_altar_half_width: float = 0.02
    fail_reset_threshold: int = 3      # interaction fail 누적 시 forced reset

    # =========================================================================
    # 11. observation 채널 ON/OFF (config 노출)
    # =========================================================================
    enable_cue_channel: bool = True
    enable_event_token_in_obs: bool = True

    # =========================================================================
    # 12. split-aware room-task permutation (Session 3 추가)
    # =========================================================================
    # Dataset generator가 episode마다 강제 주입하는 4-tuple permutation.
    # - None이면 기존 random shuffle.
    # - tuple of 4 ints이면 (north_task_id, south_task_id, east_task_id, west_task_id)
    #   순서로 RoomID.NORTH/SOUTH/EAST/WEST에 강제 배정.
    # 이 필드는 yaml에는 포함되지 않으며 (yaml은 train/OOD pool 정책만 정의),
    # generator가 dataclasses.replace 또는 직접 setter로 episode마다 갱신한다.
    forced_permutation: Optional[Tuple[int, int, int, int]] = None

    # =========================================================================
    # __post_init__ : 모든 invariant를 강하게 검증한다.
    # =========================================================================
    def __post_init__(self) -> None:
        # local_obs_size: 홀수, 양수, ablation 집합 멤버
        if self.local_obs_size <= 0 or self.local_obs_size % 2 == 0:
            raise ValueError(
                f"local_obs_size must be a positive odd integer, got {self.local_obs_size}"
            )
        if self.local_obs_size not in self.local_obs_ablation_values:
            raise ValueError(
                f"local_obs_size={self.local_obs_size} must be in "
                f"local_obs_ablation_values={self.local_obs_ablation_values}"
            )
        # 메인 세팅 default 검증: ablation set은 (3, 5, 7)을 반드시 포함
        for required in (3, 5, 7):
            if required not in self.local_obs_ablation_values:
                raise ValueError(
                    f"local_obs_ablation_values must contain {required}; got "
                    f"{self.local_obs_ablation_values}"
                )

        # 공간 크기 sanity
        if self.hall_size < 3 or self.hall_size % 2 == 0:
            raise ValueError(
                f"hall_size must be odd and >=3 (so it has a unique center cell); "
                f"got {self.hall_size}"
            )
        if self.room_size < 3:
            raise ValueError(f"room_size must be >=3, got {self.room_size}")
        if self.corridor_length < 1:
            raise ValueError(f"corridor_length must be >=1, got {self.corridor_length}")

        # episode_max_steps
        if self.episode_max_steps <= 0:
            raise ValueError(
                f"episode_max_steps must be positive, got {self.episode_max_steps}"
            )

        # field coupling sparse 조건 (PART0 §3 금지사항 §10).
        if self.field_coupling_max_dims > 2:
            raise ValueError(
                f"field_coupling_max_dims must be <=2 (sparse coupling), "
                f"got {self.field_coupling_max_dims}"
            )
        if self.num_fields_min < 0 or self.num_fields_max < self.num_fields_min:
            raise ValueError(
                f"num_fields_min/max invalid: "
                f"({self.num_fields_min}, {self.num_fields_max})"
            )
        if self.field_radius_min <= 0 or self.field_radius_max < self.field_radius_min:
            raise ValueError(
                f"field_radius_min/max invalid: "
                f"({self.field_radius_min}, {self.field_radius_max})"
            )

        # control-drift modes
        allowed_modes = {"identity", "cw", "lr", "ud", "rev"}
        for m in self.drift_abrupt_remap_modes:
            if m not in allowed_modes:
                raise ValueError(
                    f"drift_abrupt_remap_modes contains invalid mode {m!r}; "
                    f"allowed: {sorted(allowed_modes)}"
                )

        if not (0.0 <= self.miscontrol_p_low <= self.miscontrol_p_high <= 1.0):
            raise ValueError(
                f"miscontrol_p_low={self.miscontrol_p_low} / p_high={self.miscontrol_p_high} "
                f"must satisfy 0 <= low <= high <= 1"
            )

        # state adjust
        if self.state_adjust_delta <= 0:
            raise ValueError(
                f"state_adjust_delta must be positive, got {self.state_adjust_delta}"
            )
        if self.state_clip_max <= self.state_clip_min:
            raise ValueError(
                f"state_clip_min/max invalid: ({self.state_clip_min}, {self.state_clip_max})"
            )

        # target band
        if self.target_band_width <= 0:
            raise ValueError(
                f"target_band_width must be positive, got {self.target_band_width}"
            )
        lo, hi = self.task_a_target_range
        if hi <= lo:
            raise ValueError(f"task_a_target_range invalid: ({lo}, {hi})")

        # Task B vision-positive count
        if not (0 < self.task_b_num_positive < self.task_b_num_steles):
            raise ValueError(
                f"task_b_num_positive ({self.task_b_num_positive}) must be in "
                f"(0, task_b_num_steles={self.task_b_num_steles})"
            )

        # fail reset
        if self.fail_reset_threshold <= 0:
            raise ValueError(
                f"fail_reset_threshold must be positive, got {self.fail_reset_threshold}"
            )

        # mobility cooldown sanity
        if self.mobility_cooldown_kappa <= 0:
            raise ValueError(
                f"mobility_cooldown_kappa must be positive, got {self.mobility_cooldown_kappa}"
            )
        if self.mobility_cooldown_alpha <= 0:
            raise ValueError(
                f"mobility_cooldown_alpha must be positive, got {self.mobility_cooldown_alpha}"
            )

        # forced_permutation 검증 (Session 3 split-aware permutation)
        # - None이거나 길이 4 + 0..3의 정확히 한 번씩 등장하는 sequence
        if self.forced_permutation is not None:
            if isinstance(self.forced_permutation, list):
                self.forced_permutation = tuple(self.forced_permutation)
            if len(self.forced_permutation) != 4:
                raise ValueError(
                    f"forced_permutation must have length 4, got {self.forced_permutation}"
                )
            if sorted(self.forced_permutation) != [0, 1, 2, 3]:
                raise ValueError(
                    f"forced_permutation must be a permutation of (0,1,2,3); "
                    f"got {self.forced_permutation}"
                )

    # =========================================================================
    # serialization 헬퍼 (Session 3에서 yaml 로딩 시 사용)
    # =========================================================================
    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "RG4FConfig":
        """dict (yaml 파싱 결과)에서 RG4FConfig를 생성한다.

        - 알려지지 않은 key는 ValueError로 거부한다 (오타로 인한 silent ignore 방지).
        - tuple로 정의된 필드는 list로 들어와도 자동 tuple 변환.
        """
        known = {f.name for f in cls.__dataclass_fields__.values()}
        unknown = set(payload.keys()) - known
        if unknown:
            raise ValueError(f"unknown config keys: {sorted(unknown)}")
        kwargs: Dict[str, Any] = {}
        for name, value in payload.items():
            target_type = cls.__dataclass_fields__[name].type
            # tuple 필드 자동 변환 (yaml은 list로 파싱됨)
            if isinstance(value, list):
                kwargs[name] = tuple(value)
            else:
                kwargs[name] = value
        return cls(**kwargs)


__all__ = ["RG4FConfig"]
