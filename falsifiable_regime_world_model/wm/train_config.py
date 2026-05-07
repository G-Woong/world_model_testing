"""WM training config (Session 9).

본 모듈은 ``configs/wm_train_*.yaml``을 strongly-typed dataclass로 매핑한다.

설계 원칙:
    - hard-coded 수치 박지 않는다 (PART0 §3 §4).
    - hyperparameter는 모두 ``WMTrainConfig``를 통과해야 한다.
    - training script (train_world_model.py)는 본 dataclass만 받아 동작한다.
    - planner / evaluator / OOD 관련 키는 절대 두지 않는다.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence

try:
    import yaml
except Exception as exc:   # pragma: no cover
    raise RuntimeError("PyYAML이 필요합니다.") from exc


# =============================================================================
# 1. sub configs
# =============================================================================


@dataclass
class StageScheduleEntry:
    """단일 stage entry. ``end_fraction``: 전체 max_steps의 누적 비율.

    예시:
        StageScheduleEntry(name="stage1", data_config="configs/wm_data_stage1.yaml", end_fraction=0.30)
        → global_step / max_steps <= 0.30 동안 stage1을 사용.
    """
    name: str
    data_config: str
    end_fraction: float


@dataclass
class OptimizerConfig:
    name: str = "adamw"
    lr: float = 3.0e-4
    weight_decay: float = 1.0e-4
    betas: List[float] = field(default_factory=lambda: [0.9, 0.999])
    eps: float = 1.0e-8


@dataclass
class SchedulerConfig:
    name: str = "warmup_cosine"     # warmup_cosine | warmup_linear | constant
    warmup_steps: int = 1000
    min_lr_factor: float = 0.1      # min_lr = optimizer.lr * min_lr_factor


@dataclass
class CheckpointConfig:
    save_every_steps: int = 1000
    keep_last_n: int = 3
    keep_best_n: int = 3
    best_metric_keys: List[str] = field(default_factory=lambda: [
        "valid_uniform/total_loss",
        "valid_event/change_point/f1",
    ])
    # best_metric의 방향: "min" (loss) | "max" (f1)
    best_metric_modes: List[str] = field(default_factory=lambda: ["min", "max"])


@dataclass
class EvalConfig:
    eval_every_steps: int = 1000
    valid_event_data_config: str = "configs/wm_data_stage2.yaml"      # event-window sampling on
    valid_uniform_data_config: str = "configs/wm_data_stage2.yaml"    # event-window off (loader에서 force)
    valid_event_max_batches: int = 64
    valid_uniform_max_batches: int = 64
    cp_threshold: float = 0.5    # change_point/shift/reveal/mismatch logit threshold


@dataclass
class StabilityConfig:
    """NaN/Inf / OOM / overweight 방어 옵션."""
    grad_clip: float = 100.0
    nan_action: str = "stop"           # stop | skip
    overweight_warn_ratio: float = 0.5  # loss_change_point / total_loss > 0.5 이면 WARN
    overweight_warn_consecutive: int = 50
    early_stop_patience_evals: int = 0  # 0이면 비활성


# =============================================================================
# 2. top-level
# =============================================================================


@dataclass
class WMTrainConfig:
    name: str = "wm_train"
    description: str = ""
    wm_config: str = "configs/wm_debug.yaml"   # WMConfig yaml path
    variant: str = "full_model"
    output_root: str = "outputs/wm_runs"
    seed: int = 1234

    # batch / chunk / precision
    chunk_len: int = 64
    batch_size: int = 8
    grad_accum_steps: int = 1
    precision: str = "auto"                    # auto | bf16 | fp16 | fp32
    device: str = "auto"                       # auto | cuda | cpu
    num_workers: int = 0

    # training horizon
    max_steps: int = 100
    log_every_steps: int = 10

    # done target 의미 분리 (PART0/SESSION9 §2)
    done_target_mode: str = "success_done"     # success_done | terminal

    # sub configs
    optimizer: OptimizerConfig = field(default_factory=OptimizerConfig)
    scheduler: SchedulerConfig = field(default_factory=SchedulerConfig)
    checkpoint: CheckpointConfig = field(default_factory=CheckpointConfig)
    eval: EvalConfig = field(default_factory=EvalConfig)
    stability: StabilityConfig = field(default_factory=StabilityConfig)

    # stage schedule
    stage_schedule: List[StageScheduleEntry] = field(default_factory=list)

    # ---------------------------------------------------------------------
    # validation
    # ---------------------------------------------------------------------
    def validate(self) -> None:
        if self.precision not in ("auto", "bf16", "fp16", "fp32"):
            raise ValueError(f"unknown precision: {self.precision!r}")
        if self.device not in ("auto", "cuda", "cpu"):
            raise ValueError(f"unknown device: {self.device!r}")
        if self.done_target_mode not in ("success_done", "terminal"):
            raise ValueError(f"unknown done_target_mode: {self.done_target_mode!r}")
        if self.batch_size <= 0 or self.chunk_len <= 0 or self.grad_accum_steps <= 0:
            raise ValueError("batch_size/chunk_len/grad_accum_steps must be > 0")
        if self.max_steps <= 0:
            raise ValueError("max_steps must be > 0")
        if not self.stage_schedule:
            raise ValueError("stage_schedule must contain at least one entry")
        last = 0.0
        for e in self.stage_schedule:
            if not (0.0 < e.end_fraction <= 1.0):
                raise ValueError(f"stage {e.name}: end_fraction must be in (0,1].")
            if e.end_fraction < last:
                raise ValueError(f"stage {e.name}: end_fraction must be monotonic.")
            last = e.end_fraction
            if not Path(e.data_config).is_file():
                raise FileNotFoundError(f"stage {e.name}: data_config not found: {e.data_config}")
        # last의 end_fraction 이 1.0 미만이면 자동으로 1.0으로 확장
        if self.stage_schedule[-1].end_fraction < 1.0:
            self.stage_schedule[-1].end_fraction = 1.0
        # eval data configs
        for p in (self.eval.valid_event_data_config, self.eval.valid_uniform_data_config):
            if not Path(p).is_file():
                raise FileNotFoundError(f"eval data_config not found: {p}")
        # wm_config
        if not Path(self.wm_config).is_file():
            raise FileNotFoundError(f"wm_config not found: {self.wm_config}")

    @property
    def effective_batch_size(self) -> int:
        return int(self.batch_size * self.grad_accum_steps)

    # ---------------------------------------------------------------------
    # stage lookup
    # ---------------------------------------------------------------------
    def stage_for_step(self, global_step: int) -> StageScheduleEntry:
        """global_step을 받아 현재 사용해야 할 stage entry를 반환한다."""
        frac = float(global_step) / max(1, self.max_steps)
        for e in self.stage_schedule:
            if frac < e.end_fraction:
                return e
        return self.stage_schedule[-1]

    # ---------------------------------------------------------------------
    # YAML I/O
    # ---------------------------------------------------------------------
    @classmethod
    def from_yaml(cls, path: str | Path) -> "WMTrainConfig":
        p = Path(path)
        if not p.is_file():
            raise FileNotFoundError(f"train config yaml not found: {p}")
        with p.open("r", encoding="utf-8") as fp:
            data = yaml.safe_load(fp) or {}
        if not isinstance(data, Mapping):
            raise ValueError(f"yaml root must be a mapping; got {type(data).__name__}")
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "WMTrainConfig":
        sub_optimizer = _build(OptimizerConfig, data.get("optimizer") or {})
        sub_scheduler = _build(SchedulerConfig, data.get("scheduler") or {})
        sub_checkpoint = _build(CheckpointConfig, data.get("checkpoint") or {})
        sub_eval = _build(EvalConfig, data.get("eval") or {})
        sub_stability = _build(StabilityConfig, data.get("stability") or {})
        stage_raw = data.get("stage_schedule") or []
        if not isinstance(stage_raw, list) or not stage_raw:
            raise ValueError("'stage_schedule' must be a non-empty list of entries.")
        stage_schedule = [_build(StageScheduleEntry, item) for item in stage_raw]

        # top-level fields
        top_fields = {
            k: data[k] for k in (
                "name", "description", "wm_config", "variant", "output_root", "seed",
                "chunk_len", "batch_size", "grad_accum_steps", "precision", "device",
                "num_workers", "max_steps", "log_every_steps", "done_target_mode",
            ) if k in data
        }
        return cls(
            **top_fields,
            optimizer=sub_optimizer,
            scheduler=sub_scheduler,
            checkpoint=sub_checkpoint,
            eval=sub_eval,
            stability=sub_stability,
            stage_schedule=stage_schedule,
        )

    def to_dict(self) -> Dict[str, Any]:
        from dataclasses import asdict
        return asdict(self)


def _build(cls_obj, raw: Mapping[str, Any]):
    field_names = set(cls_obj.__dataclass_fields__.keys())
    raw = dict(raw)
    unknown = set(raw.keys()) - field_names
    if unknown:
        raise ValueError(
            f"unknown keys for {cls_obj.__name__}: {sorted(unknown)}. "
            f"allowed: {sorted(field_names)}"
        )
    return cls_obj(**raw)


__all__ = [
    "StageScheduleEntry",
    "OptimizerConfig",
    "SchedulerConfig",
    "CheckpointConfig",
    "EvalConfig",
    "StabilityConfig",
    "WMTrainConfig",
]
