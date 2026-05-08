"""frcgw.schemas.validation — Schema validation functions and error types.

Source docs:
- paper_context_ref/06_DATA_SCHEMA_AND_LABELING.md §7, §14, §15
- paper_context_ref/14_TRD_TECHNICAL_REQUIREMENTS_DOCUMENT_v1.md §6.2
- paper_context_ref/15_TDD_TECHNICAL_DESIGN_DOCUMENT_v1.md §6.2, §6.3
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .visibility import (
    FORBIDDEN_AGENT_FIELDS,
    HiddenLabelLeakageError,
    CounterfactualLeakageError,
    assert_agent_observation_safe,
    _collect_field_names,
)
from .step_schema import StepRecord
from .episode_schema import EpisodeRecord


class SchemaValidationError(RuntimeError):
    """Raised when required schema fields are missing or invalid."""


class ReplayValidationError(RuntimeError):
    """Raised when deterministic replay validation fails."""


class CoverageValidationError(RuntimeError):
    """Raised when coverage thresholds are not met."""


class SplitIntegrityError(RuntimeError):
    """Raised when split leakage or split integrity violation is detected."""


_COUNTERFACTUAL_BATCH_FIELDS: frozenset[str] = frozenset({
    "counterfactual_action_effects",
    "counterfactuals",
    "counterfactual_id",
    "counterfactual_effect_type",
    "counterfactual_progress_delta",
    "counterfactual_failure_risk",
    "is_oracle_best",
})


@dataclass
class ValidationResult:
    passed: bool
    errors: list[str] = field(default_factory=list)


def validate_step_schema(step: StepRecord) -> ValidationResult:
    errors: list[str] = []
    if not step.step_id:
        errors.append("step_id is required")
    if not step.episode_id:
        errors.append("episode_id is required")
    if step.step_index < 0:
        errors.append("step_index must be >= 0")
    if step.public_observation is None:
        errors.append("public_observation is required")
    if step.training_labels is None:
        errors.append("training_labels is required")
    if step.evaluation_labels is None:
        errors.append("evaluation_labels is required")
    if step.public_observation is not None:
        try:
            assert_agent_observation_safe(step.public_observation)
        except (HiddenLabelLeakageError, CounterfactualLeakageError) as e:
            errors.append(str(e))
    return ValidationResult(passed=len(errors) == 0, errors=errors)


def validate_episode_schema(episode: EpisodeRecord) -> ValidationResult:
    errors: list[str] = []
    if not episode.episode_id:
        errors.append("episode_id is required")
    if not episode.dataset_version:
        errors.append("dataset_version is required")
    if not episode.schema_version:
        errors.append("schema_version is required")
    if not episode.split_id:
        errors.append("split_id is required")
    if not episode.public_instruction:
        errors.append("public_instruction is required")
    for i, step in enumerate(episode.steps):
        step_result = validate_step_schema(step)
        if not step_result.passed:
            errors.extend([f"step[{i}]: {e}" for e in step_result.errors])
    return ValidationResult(passed=len(errors) == 0, errors=errors)


def validate_visibility_contract(episode: EpisodeRecord) -> ValidationResult:
    """Verify that no step's public_observation contains forbidden fields."""
    errors: list[str] = []
    for i, step in enumerate(episode.steps):
        try:
            assert_agent_observation_safe(step.public_observation)
        except (HiddenLabelLeakageError, CounterfactualLeakageError) as e:
            errors.append(f"step[{i}] visibility violation: {e}")
    return ValidationResult(passed=len(errors) == 0, errors=errors)


def validate_counterfactual_exclusion(batch: Any) -> ValidationResult:
    """Verify that a dataloader batch contains no counterfactual fields."""
    errors: list[str] = []
    if batch is None:
        return ValidationResult(passed=True)
    all_names = _collect_field_names(batch)
    if isinstance(batch, dict):
        all_names.update(batch.keys())
    found = all_names & _COUNTERFACTUAL_BATCH_FIELDS
    if found:
        errors.append(f"counterfactual fields in batch: {sorted(found)}")
    return ValidationResult(passed=len(errors) == 0, errors=errors)
