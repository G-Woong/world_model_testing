"""falsifiable_regime_world_model.wm — RSSM/Dreamer-style world model package.

Session 7 산출물. RG-4F 환경의 wrong-hypothesis-aware planning 메커니즘 검증을
위한 표준 RSSM/Dreamer-style backbone과 prediction head 구조를 제공한다.

핵심 원칙 (PART0 §1):
- 본 backbone은 architecture novelty가 아니라 mechanism novelty 검증을 위한
  controlled backbone이다. 모든 baseline / ablation은 동일 capacity로 공유한다.
- training loop / dataset loader / planner / evaluator는 본 패키지에 두지 않는다
  (Session 8/9/11+).
- 모든 module은 torch.nn.Module이며, file I/O / hard-coded path는 두지 않는다.

Public API
----------
- ``RSSMWorldModel``    : top-level model (encoder + RSSM + heads + decoder)
- ``WMConfig``          : strongly-typed config dataclass (yaml 매핑)
- ``WMLossOutput``      : compute_total_loss의 분해 결과
- ``compute_total_loss``: forward output + target → 가중합 loss
- ``RSSMState``         : RSSM의 한 timestep latent state (planner imagine API용)

Example
-------
```python
from falsifiable_regime_world_model.wm import (
    WMConfig, RSSMWorldModel, compute_total_loss,
)

cfg = WMConfig.from_yaml("configs/wm_debug.yaml")
model = RSSMWorldModel(cfg).eval()
batch = {  # synthetic shape sanity
    "local_grid":  torch.zeros(2, 16, 5, 5, 10),
    "scalar":      torch.zeros(2, 16, 14),
    "event_token": torch.zeros(2, 16, dtype=torch.long),
    "action_raw":  torch.zeros(2, 16, dtype=torch.long),
}
out = model(batch)   # forward output dict
```
"""
from .collate import collate_chunks
from .config import (
    DEFAULT_VARIANTS,
    EncoderConfig,
    HeadsConfig,
    LossConfig,
    MetaConfig,
    ObservationConfig,
    RegimeConfig,
    RSSMConfig,
    TrainerConfig,
    VariantSpec,
    WMConfig,
)
from .data import (
    EpisodeChunk,
    MixtureChunkIterableDataset,
    RG4FChunkIterableDataset,
    SourceIndex,
    build_chunk_dataset,
    build_source_indices,
)
from .data_config import (
    ALLOWED_TRAIN_SPLITS,
    FORBIDDEN_INPUT_KEYS,
    FORBIDDEN_TRAIN_SPLITS,
    DatasetSourceConfig,
    EventWindowConfig,
    SampleWeightConfig,
    SplitConfig,
    TargetConfig,
    WMDataConfig,
)
from .sampling import (
    EventIndex,
    EventWindowSampler,
    compute_sample_weight,
    extract_event_index,
)

# --- Session 9: training infrastructure ---
from .checkpointing import (
    ManagedCheckpointer,
    atomic_save,
    capture_rng_state,
    env_summary,
    load_checkpoint,
    model_state_dict_cpu,
    restore_rng_state,
)
from .env_check import (
    EnvReport,
    GPUStatus,
    collect_env_report,
    pick_precision,
    write_report,
)
from .metrics import (
    BinaryConfusion,
    CategoricalAccuracy,
    LossAggregator,
    RunningMean,
    ValidMetrics,
)
from .schedules import (
    build_lr_scheduler,
    constant_lambda,
    warmup_cosine_lambda,
    warmup_linear_lambda,
)
from .train_config import (
    CheckpointConfig,
    EvalConfig,
    OptimizerConfig,
    SchedulerConfig,
    StabilityConfig,
    StageScheduleEntry,
    WMTrainConfig,
)
from .trainer import (
    PrecisionContext,
    Trainer,
    assert_safe_data_config,
    assert_safe_inputs,
    build_train_loader,
    build_valid_loaders,
    make_precision_context,
    make_uniform_event_window_config,
    stages_from_config,
)
from .heads import (
    BinaryLogitHead,
    CategoricalLogitHead,
    RegressionHead,
    RSSMWorldModel,
    ScalarHead,
    WMHeads,
)
from .losses import (
    WMLossOutput,
    bce_with_logits_loss,
    categorical_ce_loss,
    compute_total_loss,
    kl_divergence_diag_normal,
    kl_loss_dreamer,
    masked_mean,
    mse_loss,
)
from .modules import (
    ActionEmbedding,
    ObservationDecoder,
    ObservationEncoder,
    concat_features,
    make_mlp,
)
from .rssm import (
    RSSM,
    RSSMCore,
    RSSMState,
    RepresentationPosterior,
    TransitionPrior,
)


__all__ = [
    # config (model)
    "WMConfig",
    "MetaConfig",
    "ObservationConfig",
    "EncoderConfig",
    "RSSMConfig",
    "HeadsConfig",
    "RegimeConfig",
    "LossConfig",
    "TrainerConfig",
    "VariantSpec",
    "DEFAULT_VARIANTS",
    # config (data)
    "WMDataConfig",
    "DatasetSourceConfig",
    "EventWindowConfig",
    "SampleWeightConfig",
    "SplitConfig",
    "TargetConfig",
    "ALLOWED_TRAIN_SPLITS",
    "FORBIDDEN_TRAIN_SPLITS",
    "FORBIDDEN_INPUT_KEYS",
    # data
    "EpisodeChunk",
    "SourceIndex",
    "RG4FChunkIterableDataset",
    "MixtureChunkIterableDataset",
    "build_chunk_dataset",
    "build_source_indices",
    # sampling
    "EventIndex",
    "EventWindowSampler",
    "compute_sample_weight",
    "extract_event_index",
    # collate
    "collate_chunks",
    # modules
    "ObservationEncoder",
    "ObservationDecoder",
    "ActionEmbedding",
    "make_mlp",
    "concat_features",
    # rssm
    "RSSM",
    "RSSMCore",
    "RSSMState",
    "TransitionPrior",
    "RepresentationPosterior",
    # heads
    "RSSMWorldModel",
    "WMHeads",
    "ScalarHead",
    "BinaryLogitHead",
    "CategoricalLogitHead",
    "RegressionHead",
    # losses
    "WMLossOutput",
    "compute_total_loss",
    "kl_loss_dreamer",
    "kl_divergence_diag_normal",
    "bce_with_logits_loss",
    "categorical_ce_loss",
    "mse_loss",
    "masked_mean",
    # training (Session 9)
    "WMTrainConfig",
    "OptimizerConfig",
    "SchedulerConfig",
    "CheckpointConfig",
    "EvalConfig",
    "StabilityConfig",
    "StageScheduleEntry",
    "Trainer",
    "PrecisionContext",
    "make_precision_context",
    "build_train_loader",
    "build_valid_loaders",
    "make_uniform_event_window_config",
    "stages_from_config",
    "assert_safe_data_config",
    "assert_safe_inputs",
    "ManagedCheckpointer",
    "atomic_save",
    "load_checkpoint",
    "capture_rng_state",
    "restore_rng_state",
    "env_summary",
    "model_state_dict_cpu",
    "EnvReport",
    "GPUStatus",
    "collect_env_report",
    "pick_precision",
    "write_report",
    "BinaryConfusion",
    "CategoricalAccuracy",
    "LossAggregator",
    "RunningMean",
    "ValidMetrics",
    "build_lr_scheduler",
    "warmup_cosine_lambda",
    "warmup_linear_lambda",
    "constant_lambda",
]
