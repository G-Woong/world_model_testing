"""DetectorEvalResult schema for sequential detection metric aggregation.

Source: .agent_tasks/codex_queue/TASK_LFD_007_sequential_detection_metrics.md
Used by: LFD evaluation harness, CUSUM/SPRT baseline comparison.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field


@dataclass
class DetectorEvalResult:
    """Aggregated evaluation result for one detector over a set of episodes."""
    detector_name: str
    n_switch_episodes: int               # v0_5 episodes with regime_switch_t
    n_stable_episodes: int               # v0_4 episodes or pre-switch steps
    n_episodes_evaluated: int

    # Detection delay metrics (None when no switch episodes exist)
    mean_detection_delay: float | None = None
    median_detection_delay: float | None = None
    p90_detection_delay: float | None = None

    false_alarm_rate_per_step: float = 0.0

    # Regime shift classification
    regime_shift_f1: float = 0.0
    regime_shift_precision: float = 0.0
    regime_shift_recall: float = 0.0

    # Wrong-hypothesis detection quality
    auroc_wrong_hypothesis: float | None = None
    auprc_wrong_hypothesis: float | None = None

    # Run-length posterior concentration (NOT standard ECE — sharpness score)
    # See metrics.run_length_posterior_concentration docstring for distinction.
    run_length_posterior_concentration: float | None = None

    # Causal link: detection delay → recovery delay (Pearson r)
    recovery_delay_pearson_r: float | None = None

    threshold_metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)
