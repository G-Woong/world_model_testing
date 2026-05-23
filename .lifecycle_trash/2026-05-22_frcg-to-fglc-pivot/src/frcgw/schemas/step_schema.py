"""frcgw.schemas.step_schema — StepRecord and related dataclasses.

Source docs:
- paper_context_ref/06_DATA_SCHEMA_AND_LABELING.md §0.4, §5-§12
- paper_context_ref/15_TDD_TECHNICAL_DESIGN_DOCUMENT_v1.md §5.3-5.7
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class PublicHistoryItem:
    step_index: int
    action_summary: str
    effect_summary: str | None = None


@dataclass
class CandidateAction:
    action_id: str
    action_type: str
    action_params: dict = field(default_factory=dict)


@dataclass
class PublicObservation:
    """Agent-visible observation. Must not contain any FORBIDDEN_AGENT_FIELDS (TDD §5.4)."""
    instruction: str
    dom_snapshot_public: dict | None = None
    accessibility_tree_public: dict | None = None
    history_public: list[PublicHistoryItem] = field(default_factory=list)
    candidate_actions_public: list[CandidateAction] = field(default_factory=list)


@dataclass
class ActionRecord:
    action_id: str
    action_type: str
    action_params: dict = field(default_factory=dict)
    rewritten: bool = False
    # Run 4B — predicted hypothesis trace (NOT oracle label).
    # is_oracle_label=False always. Separate from EvaluationLabels.h_exec_id (oracle-aligned).
    selected_hypothesis_id: str | None = None
    selected_hypothesis_type: str | None = None
    selected_hypothesis_confidence: float | None = None
    selected_hypothesis_source: str | None = None


@dataclass
class PublicEffect:
    effect_type: str
    dom_diff_public: dict | None = None
    text_diff_public: str | None = None


@dataclass
class TrainingLabels:
    """Supervision labels. TRAINING_SUPERVISION bucket only. Never inference input."""
    true_regime: str
    true_control_grammar: str
    true_change_point: str
    true_reveal_vs_shift: str
    true_action_effect_type: str
    true_failed_action: bool
    failure_reason: str | None
    progress_delta: float
    recovery_action_id: str | None = None
    valid_hypothesis_switch: bool | None = None


@dataclass
class EvaluationLabels:
    """Evaluation-only labels. EVALUATION_ONLY bucket."""
    true_wrong_hypothesis: bool | None = None
    h_exec_id: str | None = None
    correct_hypothesis_id: str | None = None
    evidence_timestamp: int | None = None
    hypothesis_update_timestamp: int | None = None
    recovery_timestamp: int | None = None
    ood_type: str | None = None
    true_regime: str | None = None
    regime_switch_t: int | None = None          # v0_5 switch timing (EVALUATION_ONLY, FORBIDDEN_AGENT_FIELDS)
    # LFD detector output fields (TASK_LFD_006) — written during eval, never inference input
    detector_wrong_prob_learned: float | None = None   # LFD wrong_prob_learned at this step
    detector_cusum_stat: float | None = None           # CUSUM statistic at this step
    detector_run_length_posterior: list | None = None  # BOCPD run-length posterior vector
    detection_delay_gt: int | None = None              # alarm_step - switch_step (FORBIDDEN_AGENT_FIELDS)


@dataclass
class CounterfactualRecord:
    """Counterfactual label. COUNTERFACTUAL_ONLY bucket.

    Never returned by dataloader collator as inference input (TDD §5.7).
    """
    counterfactual_id: str
    source_step_id: str
    candidate_action: CandidateAction
    hypothesis_id: str
    counterfactual_effect_type: str
    counterfactual_progress_delta: float
    counterfactual_failure_risk: float
    is_oracle_best: bool


@dataclass
class StepAuditMetadata:
    """Audit metadata. AUDIT_METADATA bucket only. Never inference input."""
    generator_version: str
    collection_timestamp: str
    policy_id: str
    split_id: str
    template_id: str | None = None
    seed: int | None = None
    leakage_check_flags: dict = field(default_factory=dict)


@dataclass
class StepRecord:
    step_id: str
    episode_id: str
    step_index: int
    public_observation: PublicObservation
    action: ActionRecord
    observed_effect_public: PublicEffect
    training_labels: TrainingLabels
    evaluation_labels: EvaluationLabels
    counterfactuals: list[CounterfactualRecord] = field(default_factory=list)
    audit_metadata: StepAuditMetadata | None = None
