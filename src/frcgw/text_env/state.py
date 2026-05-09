"""frcgw.text_env.state — Text-only symbolic state and episode/step records.

Source docs:
- paper_context_ref/04_TEXT_ONLY_SMOKE_TESTBED.md §6, §7, §8, §19
- paper_context_ref/06_DATA_SCHEMA_AND_LABELING.md §0.4 MVE, §4 visibility
- paper_context_ref/12_DATA_COLLECTION_METHODOLOGY_v1.md §8 text-only
"""
from __future__ import annotations

from dataclasses import dataclass, field

from frcgw.schemas.step_schema import (
    ActionRecord,
    CandidateAction,
    EvaluationLabels,
    PublicEffect,
    PublicObservation,
    StepAuditMetadata,
    TrainingLabels,
)


@dataclass
class TextState:
    """Full environment state for one step in a text-only episode.

    Public fields are safe to expose via build_public_observation().
    Hidden fields (_hidden_*) must NEVER appear in any PublicObservation
    or history_public item (visibility contract: 06_DATA_SCHEMA §4).
    """
    # --- public ---
    visible_text: str
    public_actions: list[CandidateAction]
    progress_public: float          # monotonically non-decreasing 0.0–1.0
    blocker_state_public: str | None  # coarse label, never a grammar token
    step_index: int

    # --- hidden (internal only) ---
    _hidden_regime: str
    _hidden_control_grammar: str
    _hidden_preconditions: dict     # action_id -> bool (precondition satisfied)
    _hidden_progress_score: float   # precise internal progress
    _hidden_blocker_id: str | None
    _hidden_event_type: str         # none|reveal|shift|failed|noisy|delayed|blocker_removed

    def public_field_names(self) -> set[str]:
        return {"visible_text", "public_actions", "progress_public",
                "blocker_state_public", "step_index"}


@dataclass
class TextEpisodeSpec:
    """Specification for one text-only episode, generated before collection.

    hidden_regime and hidden_control_grammar are stored here for the collector
    to initialise TextState. They must never flow into PublicObservation.
    """
    episode_id: str
    task_family: str
    public_instruction: str
    initial_state_template: str
    hidden_regime: str
    hidden_control_grammar: str
    event_schedule: list[dict] = field(default_factory=list)
    max_steps: int = 12
    seed: int = 0


@dataclass
class TextStepResult:
    """Outcome of one step in a text-only episode.

    All P1 label dataclasses are reused directly.
    counterfactuals is always [] in P2 (deferred to P3/P4).
    """
    action: ActionRecord
    pre_state: TextState
    post_state: TextState
    public_effect: PublicEffect
    training_labels: TrainingLabels
    evaluation_labels: EvaluationLabels
    audit_metadata: StepAuditMetadata
    done: bool
    counterfactuals: list = field(default_factory=list)  # always empty in P2
