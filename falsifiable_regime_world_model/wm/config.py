"""WM (World Model) config dataclasses.

본 모듈은 ``configs/wm_*.yaml``을 1:1 매핑하는 strongly-typed config 객체를 제공한다.
어떤 hard-coded magic number도 두지 않는다 (PART0 §3 §4).

설계 원칙:
- 모든 모델 모듈(``modules.py``, ``rssm.py``, ``heads.py``, ``losses.py``)은 본
  config dataclass만 받아 동작한다.
- file I/O / dataset path는 본 모듈에 두지 않는다 (yaml 로드만).
- training loop / optimizer / scheduler는 정의하지 않는다 (Session 9).
- planner / evaluator interface는 정의하지 않는다 (Session 11+).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Tuple

try:
    import yaml  # 표준 PyYAML; requirements.txt에 포함됨.
except Exception as exc:  # pragma: no cover - PyYAML은 항상 있어야 함
    raise RuntimeError(
        "PyYAML이 필요합니다. requirements.txt의 PyYAML==6.0.3을 설치하세요."
    ) from exc


# =============================================================================
# 1. 하위 dataclass: yaml의 각 섹션과 1:1 매핑
# =============================================================================


@dataclass
class ObservationConfig:
    """관측 schema. dataset 측 schema(``rg4f.dataset_io``)와 정확히 일치해야 한다.

    절대 변경 금지(이미 디스크에 저장된 dataset의 shape이 결정되어 있음).
    """

    local_grid_size: int = 5
    local_grid_channels: int = 10
    scalar_dim: int = 14
    event_vocab: int = 13      # types.EventToken 0..12
    action_vocab: int = 16     # types.Action 0..15


@dataclass
class EncoderConfig:
    """observation encoder config (CNN + scalar MLP + event/action embedding)."""

    cnn_channels: Tuple[int, ...] = (32, 64)
    cnn_kernel: int = 3
    cnn_padding: int = 1
    scalar_hidden: int = 128
    event_embed_dim: int = 16
    action_embed_dim: int = 16
    feature_dim: int = 256     # encoder 출력 e_t 차원 (RSSM posterior 입력)


@dataclass
class RSSMConfig:
    """deterministic h + stochastic z (Dreamer-style)."""

    deter_dim: int = 256       # h_t 차원
    stoch_dim: int = 64        # z_t 차원
    hidden_dim: int = 256      # MLP 내부 hidden
    num_rssm_layers: int = 1
    min_std: float = 0.1       # softplus(std) + min_std (numerical stability)
    gru_input_action: bool = True   # h_t = GRU(h_{t-1}, [z_{t-1}, action_emb_{t-1}])


@dataclass
class HeadsConfig:
    """prediction head ON/OFF + 공통 hidden_dim."""

    hidden_dim: int = 256
    obs_recon_local: bool = True
    obs_recon_scalar: bool = True
    reward: bool = True
    done: bool = True
    state: bool = True
    regime: bool = True
    change_point: bool = True
    reveal: bool = True
    shift: bool = True
    raw_eff_mismatch: bool = True
    action_relevance_proxy: bool = False  # 기본 off; planner용 actual action relevance는 Session 13


@dataclass
class RegimeConfig:
    """regime classification head 구체 schema."""

    num_control_modes: int = 5      # types.ControlMode {IDENTITY, CW, LR, UD, REV}
    multi_factor: bool = False      # 현재 single factor (control_mode)만 supervised


@dataclass
class LossConfig:
    """loss component weight + KL balancing + change-point imbalance 대응."""

    lambda_obs_local: float = 1.0
    lambda_obs_scalar: float = 1.0
    lambda_reward: float = 1.0
    lambda_done: float = 1.0
    lambda_state: float = 1.0
    lambda_regime: float = 1.0
    lambda_change_point: float = 5.0
    lambda_reveal: float = 1.0
    lambda_shift: float = 5.0
    lambda_mismatch: float = 0.5
    beta_kl: float = 1.0
    free_nats: float = 1.0
    kl_balance: float = 0.8
    cp_use_focal: bool = False
    cp_focal_gamma: float = 2.0
    cp_pos_weight: float = 50.0
    shift_pos_weight: float = 50.0
    reveal_pos_weight: float = 1.0


@dataclass
class TrainerConfig:
    """training loop는 Session 9가 만든다. 본 dataclass는 미리 schema만 잡는다."""

    chunk_len: int = 64
    batch_size: int = 8
    device: str = "cuda"
    precision: str = "fp32"     # fp32 | bf16 | fp16
    grad_clip: float = 100.0


@dataclass
class MetaConfig:
    name: str = "wm_debug"
    scale: str = "debug"          # debug | medium | large
    paper_main: bool = False
    description: str = ""


# =============================================================================
# 2. variant: 학습 ablation에서 head/loss를 끄는 단순 dict
# =============================================================================
# planner / fixed-k / always-plan / uncertainty gate / event-only는 학습 variant
# 가 아니다. 동일 checkpoint 위에서 evaluation 시점에 swap된다.

VariantSpec = Dict[str, bool]   # {"regime": bool, "change_point": bool, "reveal": bool, "shift": bool, "state": bool}

DEFAULT_VARIANTS: Dict[str, VariantSpec] = {
    "full_model":      {"regime": True,  "change_point": True,  "reveal": True,  "shift": True,  "state": True},
    "no_regime":       {"regime": False, "change_point": True,  "reveal": True,  "shift": True,  "state": True},
    "no_change_point": {"regime": True,  "change_point": False, "reveal": True,  "shift": True,  "state": True},
    "no_reveal":       {"regime": True,  "change_point": True,  "reveal": False, "shift": True,  "state": True},
    "no_state_aux":    {"regime": True,  "change_point": True,  "reveal": True,  "shift": True,  "state": False},
}


# =============================================================================
# 3. top-level config
# =============================================================================


@dataclass
class WMConfig:
    """world model config의 top-level. ``WMConfig.from_yaml(path)``로 생성."""

    meta: MetaConfig = field(default_factory=MetaConfig)
    observation: ObservationConfig = field(default_factory=ObservationConfig)
    encoder: EncoderConfig = field(default_factory=EncoderConfig)
    rssm: RSSMConfig = field(default_factory=RSSMConfig)
    heads: HeadsConfig = field(default_factory=HeadsConfig)
    regime: RegimeConfig = field(default_factory=RegimeConfig)
    loss: LossConfig = field(default_factory=LossConfig)
    trainer: TrainerConfig = field(default_factory=TrainerConfig)
    variants: Dict[str, VariantSpec] = field(default_factory=lambda: dict(DEFAULT_VARIANTS))

    # ---------------------------------------------------------------------
    # convenience: feature_dim = deter + stoch (모든 head의 공통 입력 차원)
    # ---------------------------------------------------------------------
    @property
    def feature_dim(self) -> int:
        """모든 head가 공유하는 feature 차원: ``concat(h_t, z_t)``의 size."""
        return int(self.rssm.deter_dim + self.rssm.stoch_dim)

    @property
    def encoder_action_input_dim(self) -> int:
        """RSSM GRU 입력의 action 부분 차원. gru_input_action=False면 0."""
        return int(self.encoder.action_embed_dim) if self.rssm.gru_input_action else 0

    # ---------------------------------------------------------------------
    # variant 적용
    # ---------------------------------------------------------------------
    def apply_variant(self, variant_name: str) -> "WMConfig":
        """variant를 head/loss ON/OFF에 적용한 새 WMConfig를 반환 (immutable 권장).

        Notes
        -----
        ``regime=False``는 regime head 학습/예측 모두 끈다. 단, RSSM backbone
        capacity는 동일하게 유지된다 (PART0 §1.4 same-capacity 원칙).
        """
        if variant_name not in self.variants:
            raise KeyError(
                f"unknown variant '{variant_name}'. available: {sorted(self.variants.keys())}"
            )
        spec = self.variants[variant_name]
        new_heads = HeadsConfig(**self.heads.__dict__)
        new_loss = LossConfig(**self.loss.__dict__)
        # head ON/OFF (state/regime/change_point/reveal/shift만 variant 대상)
        if not spec.get("state", True):
            new_heads.state = False
            new_loss.lambda_state = 0.0
        if not spec.get("regime", True):
            new_heads.regime = False
            new_loss.lambda_regime = 0.0
        if not spec.get("change_point", True):
            new_heads.change_point = False
            new_loss.lambda_change_point = 0.0
        if not spec.get("reveal", True):
            new_heads.reveal = False
            new_loss.lambda_reveal = 0.0
        if not spec.get("shift", True):
            new_heads.shift = False
            new_loss.lambda_shift = 0.0
        return WMConfig(
            meta=MetaConfig(**{**self.meta.__dict__, "name": f"{self.meta.name}__{variant_name}"}),
            observation=ObservationConfig(**self.observation.__dict__),
            encoder=EncoderConfig(**self.encoder.__dict__),
            rssm=RSSMConfig(**self.rssm.__dict__),
            heads=new_heads,
            regime=RegimeConfig(**self.regime.__dict__),
            loss=new_loss,
            trainer=TrainerConfig(**self.trainer.__dict__),
            variants=dict(self.variants),
        )

    # ---------------------------------------------------------------------
    # YAML 로드
    # ---------------------------------------------------------------------
    @classmethod
    def from_yaml(cls, path: str | Path) -> "WMConfig":
        """``configs/wm_*.yaml`` 1개를 읽어 typed WMConfig를 반환한다."""
        p = Path(path)
        if not p.is_file():
            raise FileNotFoundError(f"config yaml not found: {p}")
        with p.open("r", encoding="utf-8") as fp:
            data = yaml.safe_load(fp) or {}
        if not isinstance(data, Mapping):
            raise ValueError(f"yaml root must be a mapping; got {type(data).__name__}")
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "WMConfig":
        """dict로부터 WMConfig를 만든다 (yaml 로드 후 분기 또는 테스트용)."""
        meta = _build_section(MetaConfig, data.get("meta") or {})
        observation = _build_section(ObservationConfig, data.get("observation") or {})
        encoder = _build_section(EncoderConfig, data.get("encoder") or {}, _coerce_cnn_channels)
        rssm = _build_section(RSSMConfig, data.get("rssm") or {})
        heads = _build_section(HeadsConfig, data.get("heads") or {})
        regime = _build_section(RegimeConfig, data.get("regime") or {})
        loss = _build_section(LossConfig, data.get("loss") or {})
        trainer = _build_section(TrainerConfig, data.get("trainer") or {})
        variants_raw = data.get("variants") or DEFAULT_VARIANTS
        variants = {
            str(k): {str(kk): bool(vv) for kk, vv in (v or {}).items()}
            for k, v in variants_raw.items()
        }
        return cls(
            meta=meta,
            observation=observation,
            encoder=encoder,
            rssm=rssm,
            heads=heads,
            regime=regime,
            loss=loss,
            trainer=trainer,
            variants=variants,
        )


# =============================================================================
# 4. 내부 헬퍼
# =============================================================================


def _build_section(cls_obj, raw: Mapping[str, Any], coerce_fn=None):
    """yaml의 한 섹션 dict을 dataclass로 변환한다.

    - dataclass에 정의된 field만 받아들이며, unknown key는 ``ValueError``로 거부한다.
      이는 오타로 인한 silent override를 막기 위함이다.
    - ``coerce_fn``은 일부 필드의 타입 변환(예: list→tuple)을 위한 hook.
    """
    field_names = set(cls_obj.__dataclass_fields__.keys())
    raw = dict(raw)
    if coerce_fn is not None:
        raw = coerce_fn(raw)
    unknown = set(raw.keys()) - field_names
    if unknown:
        raise ValueError(
            f"unknown keys for {cls_obj.__name__}: {sorted(unknown)}. "
            f"allowed: {sorted(field_names)}"
        )
    return cls_obj(**raw)


def _coerce_cnn_channels(raw: Dict[str, Any]) -> Dict[str, Any]:
    """``cnn_channels``가 list로 들어오면 tuple로 강제 변환한다."""
    if "cnn_channels" in raw and isinstance(raw["cnn_channels"], list):
        raw["cnn_channels"] = tuple(int(x) for x in raw["cnn_channels"])
    return raw


__all__ = [
    "ObservationConfig",
    "EncoderConfig",
    "RSSMConfig",
    "HeadsConfig",
    "RegimeConfig",
    "LossConfig",
    "TrainerConfig",
    "MetaConfig",
    "VariantSpec",
    "DEFAULT_VARIANTS",
    "WMConfig",
]
