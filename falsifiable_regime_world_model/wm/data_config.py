"""WM dataloader config dataclasses.

본 모듈은 ``configs/wm_data_stage*.yaml``을 1:1 매핑하는 strongly-typed config 객체
를 제공한다. ``WMDataConfig`` 1개가 ``DataLoader`` 생성에 필요한 모든 결정을 담는다.

설계 원칙 (Session 8):
- 학습에는 ``train`` / ``valid`` split만 허용. test_id / ood_* split이 들어오면 yaml
  로드 시점에서 즉시 ``ValueError``를 던진다 (PART0 §3 §6 split-leak 방지).
- 모든 데이터 source는 ``data/<root>/<split>/{index.jsonl, episodes/*.npz}`` 구조여야
  한다. Session 3 generator가 만든 schema와 동일.
- collector_metadata / privilege metadata 등은 본 config에서 다루지 않는다 (loader가
  npz의 numeric array만 읽고, episode_meta.json의 collector_metadata는 무시).
- 본 모듈은 Tensor를 다루지 않는다. PyTorch import 0회.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, List, Mapping, Optional, Sequence, Tuple

try:
    import yaml
except Exception as exc:  # pragma: no cover
    raise RuntimeError(
        "PyYAML이 필요합니다. requirements.txt의 PyYAML==6.0.3을 설치하세요."
    ) from exc


# =============================================================================
# 1. 학습 허용 split 정책 (PART0 §3 §6)
# =============================================================================

# 학습용 loader가 yield 가능한 split. 추가 시 신중히.
ALLOWED_TRAIN_SPLITS: Tuple[str, ...] = ("train", "valid")

# 학습 input으로 절대 사용 금지 split (test 또는 OOD).
FORBIDDEN_TRAIN_SPLITS: Tuple[str, ...] = (
    "test_id",
    "ood_room_perm",
    "ood_factor_recomb",
    "ood_param_shift",
    "ood_obs_shift",
    "ood_field_placement",
)

# 학습 batch input/target에 들어가면 안 되는 metadata key (oracle leak 방지). 본 dataloader는
# npz의 numeric array만 읽으므로 자연스럽게 차단되지만, collate 단계에서 hard guard를 둔다.
FORBIDDEN_INPUT_KEYS: Tuple[str, ...] = (
    "collector_metadata",
    "collector_mode",
    "task_order_str",
    "task_order_planned",
    "task_attempt_ticks",
    "task_timeout",
    "task_retry_count",
    "task_budgets",
    "privilege_level",
    "b_use_label_oracle",
    "target_band_center",
    "target_band_half_width",
    "target_band_kind",
    "target_band_state_dim",
    "target_band_active",
    "tau_i",
    "stele_positive_k",
    "piece_weight_j",
    "forced_permutation",
    "permutation",
    "permutation_id",
    "field_info_static",
    "field_info_mu",
    "field_info_sigma",
    # ground-truth (target은 가능, input은 금지)
    "true_regime",
    "true_regime_control_mode",
    "true_regime_mobility_mode",
    "true_regime_miscontrol_p",
    "true_regime_periodic_slip",
    "change_point",
    "reveal_event",
    "shift_event",
    "reveal_or_shift",
    "true_state",
)


# =============================================================================
# 2. 하위 dataclass
# =============================================================================


@dataclass
class DatasetSourceConfig:
    """단일 dataset root 설정 (예: random_2000 또는 success_curriculum_v5_2000)."""

    name: str                      # 인간 친화적 이름 (예: "random_2000"). dataset_id로도 사용.
    root: str                      # data/<root>. manifest.json이 있어야 함.
    train_weight: float = 1.0      # train split mixture weight (loader가 normalize)
    valid_weight: float = 1.0      # valid split mixture weight

    def root_path(self) -> Path:
        return Path(self.root)


@dataclass
class EventWindowConfig:
    """event-window chunk sampling 설정.

    학습 loader가 매 chunk를 샘플링할 때 사용:
      1. type을 ``[change_point, shift, reveal, success(=done), uniform]`` 중 확률적 선택.
      2. 해당 event index가 episode 안에 존재하면 그 주변 ±radius에서 chunk_start 결정.
      3. 없으면 uniform fallback.

    weight는 정규화되어 categorical로 사용된다 (합 1.0이 아니어도 됨).
    """

    enabled: bool = True
    window_radius: int = 16
    change_point_prob: float = 0.25
    shift_prob: float = 0.20
    reveal_prob: float = 0.15
    success_prob: float = 0.10        # done==1 또는 task_completion 주변
    uniform_prob: float = 0.30        # 위 4개에 fallback이 발생해도 uniform과 합산
    raw_eff_mismatch_subsample_max: int = 64  # mismatch event는 너무 많으므로 max N개만 사용


@dataclass
class SampleWeightConfig:
    """tick-level sample_weight boost 정책 (loss 계산용).

    base_weight    : valid tick의 기본 weight. padding tick은 0.0으로 강제.
    *_boost        : 해당 event 주변 ±boost_radius tick에 곱해질 multiplier.
    cap            : 최종 weight cap (오버플로 방지).
    """

    enabled: bool = True
    base_weight: float = 1.0
    boost_radius: int = 8
    change_point_boost: float = 5.0
    shift_boost: float = 5.0
    reveal_boost: float = 2.0
    success_boost: float = 2.0
    raw_eff_mismatch_boost: float = 1.5
    weight_cap: float = 10.0


@dataclass
class SplitConfig:
    """train / valid split별 chunk dataloader 설정."""

    chunk_len: int = 64
    batch_size: int = 8
    chunks_per_epoch: int = 4096      # 한 epoch에서 yield할 chunk 수 (IterableDataset의 길이)
    seed: int = 42
    num_workers: int = 0              # PyTorch DataLoader num_workers. Windows는 0 권장
    drop_last: bool = False
    shuffle_episodes: bool = True


@dataclass
class TargetConfig:
    """obs reconstruction target을 어떻게 정의할지 결정.

    next_step (DreamerV3 표준): obs_target = next_observations_*
    same_step:                  obs_target = observations_* (auto-encoding)
    """

    obs_recon_mode: str = "next_step"  # "next_step" | "same_step"


# =============================================================================
# 3. top-level config
# =============================================================================


@dataclass
class WMDataConfig:
    """top-level dataloader config. ``WMDataConfig.from_yaml(path)``로 생성."""

    name: str = "wm_data_stage1"
    description: str = ""
    sources: List[DatasetSourceConfig] = field(default_factory=list)
    train: SplitConfig = field(default_factory=SplitConfig)
    valid: SplitConfig = field(default_factory=lambda: SplitConfig(chunks_per_epoch=512))
    event_window: EventWindowConfig = field(default_factory=EventWindowConfig)
    sample_weight: SampleWeightConfig = field(default_factory=SampleWeightConfig)
    target: TargetConfig = field(default_factory=TargetConfig)

    # ---------------------------------------------------------------------
    # validation
    # ---------------------------------------------------------------------
    def validate(self, *, extra_split_names: Sequence[str] = ()) -> None:
        """학습 loader 사용 직전에 호출. forbidden split이 들어왔는지 확인.

        ``extra_split_names``: 외부 코드가 명시적으로 추가하려고 시도한 split. (negative
        test에서 inject_bad_split을 받을 때 사용.)
        """
        for split in extra_split_names:
            if split in FORBIDDEN_TRAIN_SPLITS:
                raise ValueError(
                    f"Split leakage detected: test_id/OOD splits must not be used "
                    f"for training loaders. Got: {split!r}. "
                    f"Allowed: {ALLOWED_TRAIN_SPLITS}"
                )
            if split not in ALLOWED_TRAIN_SPLITS:
                raise ValueError(
                    f"Unknown split {split!r}. Allowed: {ALLOWED_TRAIN_SPLITS}"
                )
        # source 검증
        if not self.sources:
            raise ValueError("WMDataConfig.sources가 비어 있습니다.")
        seen_names: set[str] = set()
        for src in self.sources:
            if src.name in seen_names:
                raise ValueError(f"중복 source name: {src.name!r}")
            seen_names.add(src.name)
            if not src.root_path().is_dir():
                # smoke 단계에서는 실재 dir이 없을 수도 있지만, 실제 학습에서는 필요.
                # 본 메서드는 strict하게 검증한다.
                raise FileNotFoundError(
                    f"source {src.name!r}의 root가 존재하지 않습니다: {src.root_path()}"
                )
            manifest = src.root_path() / "manifest.json"
            if not manifest.is_file():
                raise FileNotFoundError(
                    f"source {src.name!r}의 manifest.json이 없습니다: {manifest}"
                )
        # target mode
        if self.target.obs_recon_mode not in ("next_step", "same_step"):
            raise ValueError(
                f"target.obs_recon_mode must be 'next_step' or 'same_step'; "
                f"got {self.target.obs_recon_mode!r}"
            )

    # ---------------------------------------------------------------------
    # mixture weight 정규화
    # ---------------------------------------------------------------------
    def normalized_weights(self, split: str) -> List[float]:
        """source별 weight를 split-conditional로 normalize 해 반환."""
        if split not in ALLOWED_TRAIN_SPLITS:
            raise ValueError(
                f"Split leakage detected: test_id/OOD splits must not be used "
                f"for training loaders. Got: {split!r}."
            )
        attr = "train_weight" if split == "train" else "valid_weight"
        raw = [max(0.0, float(getattr(s, attr))) for s in self.sources]
        total = sum(raw)
        if total <= 0.0:
            raise ValueError(
                f"split={split!r}에서 모든 source의 weight가 0입니다. "
                f"적어도 하나는 양수여야 합니다."
            )
        return [w / total for w in raw]

    # ---------------------------------------------------------------------
    # YAML 로드
    # ---------------------------------------------------------------------
    @classmethod
    def from_yaml(cls, path: str | Path) -> "WMDataConfig":
        p = Path(path)
        if not p.is_file():
            raise FileNotFoundError(f"data config yaml not found: {p}")
        with p.open("r", encoding="utf-8") as fp:
            data = yaml.safe_load(fp) or {}
        if not isinstance(data, Mapping):
            raise ValueError(f"yaml root must be a mapping; got {type(data).__name__}")
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "WMDataConfig":
        sources_raw = data.get("sources") or []
        if not isinstance(sources_raw, list) or not sources_raw:
            raise ValueError("yaml 'sources' 항목이 비어 있거나 list가 아닙니다.")
        sources = [
            _build_section(DatasetSourceConfig, item) for item in sources_raw
        ]
        # split section
        train = _build_section(SplitConfig, data.get("train") or {})
        valid_raw = data.get("valid") or {}
        # valid는 train의 chunk_len/batch_size를 명시하지 않은 경우 train에서 상속 (편의)
        if "chunk_len" not in valid_raw:
            valid_raw = {**valid_raw, "chunk_len": train.chunk_len}
        if "batch_size" not in valid_raw:
            valid_raw = {**valid_raw, "batch_size": train.batch_size}
        valid = _build_section(SplitConfig, valid_raw)
        event_window = _build_section(EventWindowConfig, data.get("event_window") or {})
        sample_weight = _build_section(SampleWeightConfig, data.get("sample_weight") or {})
        target = _build_section(TargetConfig, data.get("target") or {})
        cfg = cls(
            name=str(data.get("name", "wm_data")),
            description=str(data.get("description", "")),
            sources=sources,
            train=train,
            valid=valid,
            event_window=event_window,
            sample_weight=sample_weight,
            target=target,
        )
        # forbidden split이 들어왔는지 하드 가드
        forbidden_in_yaml = set(data.get("splits", [])) & set(FORBIDDEN_TRAIN_SPLITS)
        if forbidden_in_yaml:
            raise ValueError(
                f"Split leakage detected: test_id/OOD splits must not be used "
                f"for training loaders. Got: {sorted(forbidden_in_yaml)}"
            )
        return cfg


# =============================================================================
# 4. 내부 헬퍼
# =============================================================================


def _build_section(cls_obj, raw: Mapping[str, Any]):
    """unknown key를 거부하는 dataclass 빌더."""
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
    "ALLOWED_TRAIN_SPLITS",
    "FORBIDDEN_TRAIN_SPLITS",
    "FORBIDDEN_INPUT_KEYS",
    "DatasetSourceConfig",
    "EventWindowConfig",
    "SampleWeightConfig",
    "SplitConfig",
    "TargetConfig",
    "WMDataConfig",
]
