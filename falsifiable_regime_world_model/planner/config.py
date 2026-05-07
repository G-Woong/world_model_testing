"""Planner / evaluation config dataclasses (Session 11-13).

본 모듈은 ``configs/planner_eval_*.yaml``을 strongly-typed config 객체로 매핑한다.

설계 원칙
---------
- planner / baseline / FRC-WM가 사용하는 모든 hyperparameter는 본 dataclass를 통과해야 한다.
  코드 내부 magic number 금지 (PART0 §3 §4).
- 모든 planner는 동일한 ``PlannerConfig`` (compute budget / horizon / num_rollouts 등)을
  공유하여 fair comparison이 가능해야 한다 (§7 평가 설계 공정성).
- ``BaselinePlannerConfig``와 ``FRCPlannerConfig``는 PlannerConfig를 *공유*한 위에 각자
  추가적인 hyperparameter만 더한다.
- threshold tuning은 valid에서 결정한 값을 yaml에 박아둔다. test/OOD에서 다시 튜닝하면
  leakage이므로 코드/yaml 어디에서도 금지.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Tuple

try:
    import yaml
except Exception as exc:  # pragma: no cover
    raise RuntimeError("PyYAML이 필요합니다. requirements.txt 확인.") from exc


# =============================================================================
# 1. PlannerConfig — 모든 planner가 공유하는 compute budget / horizon
# =============================================================================


@dataclass
class PlannerConfig:
    """모든 planner가 공유하는 compute / rollout / horizon 설정.

    PART2 §3.9: ``compute reallocation``은 *amount*가 아니라 *target*이 본질이다.
    그러나 fair comparison을 위해 같은 budget 안에서 비교할 수 있어야 한다.
    """

    # rollout 기본값
    horizon: int = 10                             # 한 candidate action sequence의 길이
    num_rollouts_per_candidate: int = 1           # candidate별 sampling 횟수 (stochastic z)
    candidate_action_count: int = 8               # 평가할 candidate action sequence 수
    action_sequence_length: int = 1               # planning 후 실행할 first action 만 사용 (=1)

    # planning 빈도 / 횟수 제한
    max_planning_calls_per_episode: int = 1000    # 매 step planning이 가능한 환경에서도 안전 상한
    replan_interval: int = 1                      # fixed-k baseline 등에서 사용

    # compute budget (rollout step 단위. 1 step = 1 candidate가 1 step 미래로 imagine)
    compute_budget_total: int = 100000            # episode 전체 누적 한도
    compute_budget_per_step: int = 0              # 0이면 unlimited per step

    # alternative hypothesis rollout 관련
    enable_alternative_rollout: bool = False       # baseline은 false. FRC가 true로 override.
    num_alternative_samples: int = 4               # alternative latent sampling 수
    alt_latent_perturb_std: float = 0.5            # stochastic z perturbation strength
    alt_regime_topk: int = 2                       # regime logit top-k 후보 (1=current, 2부터 alt)

    # action space
    action_subset: Optional[List[int]] = None      # None이면 16 전체. baseline scenarios에서 subset 가능.
    use_action_mask: bool = True                   # env가 제공하는 action_mask로 invalid action 제외

    # device
    device: str = "auto"                            # auto | cuda | cpu

    # 결정성
    seed_offset: int = 0

    # planner-internal sampling 결정성. None이면 system random 사용.
    sampling_seed: Optional[int] = None

    def __post_init__(self) -> None:
        if self.horizon <= 0:
            raise ValueError(f"horizon must be positive, got {self.horizon}")
        if self.candidate_action_count <= 0:
            raise ValueError(f"candidate_action_count must be positive, got {self.candidate_action_count}")
        if self.num_rollouts_per_candidate <= 0:
            raise ValueError(
                f"num_rollouts_per_candidate must be positive, got {self.num_rollouts_per_candidate}"
            )
        if self.action_sequence_length <= 0:
            raise ValueError("action_sequence_length must be >= 1")
        if self.max_planning_calls_per_episode < 0:
            raise ValueError("max_planning_calls_per_episode must be >= 0")
        if self.compute_budget_total < 0:
            raise ValueError("compute_budget_total must be >= 0")
        if self.alt_regime_topk < 2:
            raise ValueError(
                "alt_regime_topk must be >= 2 (current + at least one alternative)"
            )


# =============================================================================
# 2. Baseline-specific configs
# =============================================================================


@dataclass
class BaselinePlannerConfig:
    """6 baseline (reactive / fixed-k / always-plan / uncertainty-gate /
    adaptive-lookahead / event-only) 의 추가 hyperparameter."""

    # fixed-k
    fixed_k_period: int = 5                        # 매 k step마다 planning

    # uncertainty gate
    uncertainty_signal: str = "regime_entropy"     # regime_entropy | reward_var | latent_var | done_uncertainty
    uncertainty_threshold: float = 1.0
    uncertainty_fallback: str = "reward_var"       # head 비활성 시 fallback

    # adaptive lookahead
    adaptive_low_horizon: int = 3
    adaptive_high_horizon: int = 15
    adaptive_low_rollouts: int = 4
    adaptive_high_rollouts: int = 16
    adaptive_threshold: float = 0.5                # uncertainty/risk threshold

    # event-only / novelty gate
    event_signals: Tuple[str, ...] = ("reveal_prob", "mismatch_prob")
    event_threshold: float = 0.5
    novelty_signal_window: int = 5                 # 최근 N step prediction error moving average


# =============================================================================
# 3. FRC-WM (Ours) config
# =============================================================================


@dataclass
class FRCPlannerConfig:
    """FRC-WM planner 추가 hyperparameter (PART2 §3.7~§3.14).

    threshold (tau_F / tau_Delta)는 ``valid`` split에서 결정한 값을 yaml에 박아두며
    test/OOD에서 다시 튜닝하면 leakage. 본 dataclass는 그 값을 단순히 보관한다.
    """

    # falsification score
    falsification_threshold: float = 0.30          # tau_F (sigmoid scale 0~1)
    cp_logit_threshold: float = 1.26                # diagnostic-derived (Session 10 best F1 logit)
    mismatch_logit_threshold: float = -0.30         # diagnostic-derived
    reveal_logit_threshold: float = -0.77           # diagnostic-derived
    falsification_window: int = 5                   # 최근 W step likelihood 평균
    falsification_weights: Tuple[float, ...] = (
        0.30,   # change_risk
        0.20,   # mismatch_risk
        0.15,   # reveal (stripped if reveal-only — usually low weight)
        0.20,   # regime_uncertainty (entropy)
        0.15,   # current_vs_alt disagreement
    )

    # action relevance
    relevance_threshold: float = 0.10              # tau_Delta on value gap (normalized)
    relevance_use_action_flip: bool = True
    relevance_value_gap_norm: float = 1.0          # gap을 [0,1]로 정규화하는 scale

    # compute reallocation
    base_horizon: int = 5                           # low falsification 시 horizon
    extreme_horizon: int = 15                        # high falsification 시 horizon
    base_rollouts: int = 4
    extreme_rollouts: int = 16
    extreme_falsification: float = 0.70             # 위 horizon으로 jump하는 falsification level

    # decision modes
    enable_correct_mode: bool = True
    enable_avoid_mode: bool = True
    enable_delay_mode: bool = True
    enable_explore_mode: bool = True
    delay_action: int = 15                          # Action.WAIT
    correction_state_dim_priority: Tuple[int, ...] = (4, 2, 1)   # control_drift, interaction, mobility

    # safety
    avoid_risk_threshold: float = 0.85              # falsification 매우 높을 때 avoid mode 강제

    # head ON 표 (model variant 별 사용 가능 head 자동 비활성)
    use_change_point: bool = True                   # no_change_point variant이면 자동 false
    use_regime_head: bool = True                    # no_regime variant이면 자동 false


# =============================================================================
# 4. PlannerSpec / SplitSpec / PlannerEvalRunSpec — yaml 매핑
# =============================================================================


@dataclass
class PlannerSpec:
    """yaml의 한 planner entry. ``kind``는 planner 종류를 결정한다."""
    name: str
    kind: str   # reactive | fixed_k | always_plan | uncertainty_gate | adaptive_lookahead | event_only | ours_frc
    planner: PlannerConfig = field(default_factory=PlannerConfig)
    baseline: BaselinePlannerConfig = field(default_factory=BaselinePlannerConfig)
    frc: FRCPlannerConfig = field(default_factory=FRCPlannerConfig)
    description: str = ""


@dataclass
class SplitSpec:
    """split별 평가 spec.

    ``split``은 RG4F generator가 만든 split 이름을 그대로 사용한다.
    평가 시점에는 해당 split의 dataset을 *읽지 않고* RG4FEnv를 직접 reset(seed)으로
    구동한다. 단 ``split_policy``를 통해 RG4FConfig를 split별로 변형할 수 있다.
    """
    name: str
    num_episodes: int = 5
    seeds: List[int] = field(default_factory=lambda: [0])
    seed_base: int = 1_000_000             # split별로 다른 seed range를 보장
    # split_policy_overrides는 RG4FConfig override dict.
    # ex) ood_param_shift: {drift_strength_multiplier: 2.0, shift_probability_multiplier: 2.0}
    config_overrides: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelSpec:
    """평가에 사용할 world model checkpoint."""
    name: str                                  # full | no_regime | no_change_point | ...
    checkpoint: str                            # 파일 경로 (step_00030000.pt or last.pt)
    wm_config: str                              # 학습 시 사용한 wm yaml 경로
    variant: str = "full_model"                # WMConfig.apply_variant에 들어가는 이름


@dataclass
class PlannerEvalRunSpec:
    """yaml 한 줄에 들어가는 (model, planner, split, seed) cross-product."""
    debug: bool = False
    out_dir: str = "outputs/planner_eval_main"
    max_steps_per_episode: int = 600
    save_traces: bool = True
    save_per_step_logs: bool = False
    skip_existing: bool = False


@dataclass
class PlannerEvalConfig:
    """top-level evaluation config (yaml 매핑).

    yaml schema (예시):
        meta: { name: ..., description: ... }
        run:
          debug: false
          out_dir: outputs/planner_eval_main
          max_steps_per_episode: 600
        models:
          - { name: full, checkpoint: ..., wm_config: ..., variant: full_model }
        planners:
          - { name: reactive, kind: reactive, planner: {...}, baseline: {...} }
        splits:
          - { name: test_id, num_episodes: 50, seeds: [0,1,2] }
    """
    meta_name: str = "planner_eval"
    description: str = ""
    run: PlannerEvalRunSpec = field(default_factory=PlannerEvalRunSpec)
    models: List[ModelSpec] = field(default_factory=list)
    planners: List[PlannerSpec] = field(default_factory=list)
    splits: List[SplitSpec] = field(default_factory=list)
    # env config 기본값 (yaml에서 override 가능)
    base_env_config: Optional[str] = None    # configs/dataset_default.yaml의 environment 섹션 fallback

    # ---------------------------------------------------------------------
    # YAML 로드
    # ---------------------------------------------------------------------
    @classmethod
    def from_yaml(cls, path: str | Path) -> "PlannerEvalConfig":
        p = Path(path)
        if not p.is_file():
            raise FileNotFoundError(f"planner eval config not found: {p}")
        with p.open("r", encoding="utf-8") as fp:
            data = yaml.safe_load(fp) or {}
        if not isinstance(data, Mapping):
            raise ValueError(f"yaml root must be a mapping; got {type(data).__name__}")
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "PlannerEvalConfig":
        meta = data.get("meta") or {}
        run_raw = data.get("run") or {}
        models_raw = data.get("models") or []
        planners_raw = data.get("planners") or []
        splits_raw = data.get("splits") or []

        run = _build_dataclass(PlannerEvalRunSpec, run_raw)
        models = [_build_dataclass(ModelSpec, m) for m in models_raw]
        planners = [_build_planner_spec(p) for p in planners_raw]
        splits = [_build_split_spec(s) for s in splits_raw]
        return cls(
            meta_name=str(meta.get("name", "planner_eval")),
            description=str(meta.get("description", "")),
            run=run,
            models=models,
            planners=planners,
            splits=splits,
            base_env_config=data.get("base_env_config"),
        )


# =============================================================================
# 5. 내부 헬퍼: dataclass builder + planner spec dispatch
# =============================================================================


def _build_dataclass(cls_obj, raw: Mapping[str, Any]):
    """unknown key를 거부하는 안전한 dataclass builder."""
    field_names = set(cls_obj.__dataclass_fields__.keys())
    raw = dict(raw)
    unknown = set(raw.keys()) - field_names
    if unknown:
        raise ValueError(
            f"unknown keys for {cls_obj.__name__}: {sorted(unknown)}. "
            f"allowed: {sorted(field_names)}"
        )
    # tuple type 자동 변환
    kwargs: Dict[str, Any] = {}
    for k, v in raw.items():
        kwargs[k] = tuple(v) if isinstance(v, list) and _expects_tuple(cls_obj, k) else v
    return cls_obj(**kwargs)


def _expects_tuple(cls_obj, name: str) -> bool:
    annotation = str(cls_obj.__dataclass_fields__[name].type)
    return "Tuple" in annotation or "tuple" in annotation


def _build_planner_spec(raw: Mapping[str, Any]) -> PlannerSpec:
    raw = dict(raw)
    planner_cfg = _build_dataclass(PlannerConfig, raw.pop("planner", {}) or {})
    baseline_cfg = _build_dataclass(BaselinePlannerConfig, raw.pop("baseline", {}) or {})
    frc_cfg = _build_dataclass(FRCPlannerConfig, raw.pop("frc", {}) or {})
    return PlannerSpec(
        name=str(raw["name"]),
        kind=str(raw["kind"]),
        planner=planner_cfg,
        baseline=baseline_cfg,
        frc=frc_cfg,
        description=str(raw.get("description", "")),
    )


def _build_split_spec(raw: Mapping[str, Any]) -> SplitSpec:
    raw = dict(raw)
    seeds = raw.get("seeds") or [0]
    if not isinstance(seeds, list):
        raise ValueError(f"split.seeds must be list; got {seeds!r}")
    return SplitSpec(
        name=str(raw["name"]),
        num_episodes=int(raw.get("num_episodes", 5)),
        seeds=[int(s) for s in seeds],
        seed_base=int(raw.get("seed_base", 1_000_000)),
        config_overrides=dict(raw.get("config_overrides", {})),
    )


__all__ = [
    "PlannerConfig",
    "BaselinePlannerConfig",
    "FRCPlannerConfig",
    "PlannerSpec",
    "SplitSpec",
    "ModelSpec",
    "PlannerEvalRunSpec",
    "PlannerEvalConfig",
]
