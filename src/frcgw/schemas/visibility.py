"""frcgw.schemas.visibility — VisibilityBucket enum and leakage guard.

Source docs:
- paper_context_ref/06_DATA_SCHEMA_AND_LABELING.md §0.3, §7, §14
- paper_context_ref/15_TDD_TECHNICAL_DESIGN_DOCUMENT_v1.md §5.1, §5.4, §6.1
"""
from __future__ import annotations

from enum import Enum
from typing import Any


class VisibilityBucket(str, Enum):
    """Visibility classification for FRCG-WM data fields.

    Only AGENT_OBSERVATION is allowed in inference input (TDD §5.1).
    """
    AGENT_OBSERVATION = "AGENT_OBSERVATION"
    TRAINING_SUPERVISION = "TRAINING_SUPERVISION"
    EVALUATION_ONLY = "EVALUATION_ONLY"
    COUNTERFACTUAL_ONLY = "COUNTERFACTUAL_ONLY"
    AUDIT_METADATA = "AUDIT_METADATA"


FORBIDDEN_AGENT_FIELDS: frozenset[str] = frozenset({
    "true_regime",
    "true_control_grammar",
    "true_change_point",
    "true_reveal_vs_shift",
    "true_wrong_hypothesis",
    "counterfactual_action_effects",
    "oracle_regime_action",
    "oracle_grammar_action",
    "oracle_best_action",
    "split_id",
    "ood_type",
    "template_id",
    "seed",
    "policy_id",
    "audit_metadata",
    "regime_switch_t",   # v0_5 intra-episode switch timing — eval-only label, never inference input
})


class HiddenLabelLeakageError(RuntimeError):
    """Raised when a hidden label field appears in agent-observable input."""


class CounterfactualLeakageError(RuntimeError):
    """Raised when a counterfactual field appears in agent-observable input."""


def get_forbidden_agent_fields() -> frozenset[str]:
    """Return the set of field names forbidden in agent observation."""
    return FORBIDDEN_AGENT_FIELDS


def _collect_field_names(obj: Any) -> set[str]:
    """Recursively collect all field/key names from dicts, dataclasses, and lists."""
    names: set[str] = set()
    if isinstance(obj, dict):
        for k, v in obj.items():
            names.add(str(k))
            names.update(_collect_field_names(v))
    elif isinstance(obj, (list, tuple)):
        for item in obj:
            names.update(_collect_field_names(item))
    elif hasattr(obj, "__dataclass_fields__"):
        for field_name in obj.__dataclass_fields__:
            names.add(field_name)
            names.update(_collect_field_names(getattr(obj, field_name, None)))
    return names


def assert_agent_observation_safe(obj: Any) -> None:
    """Raise if forbidden fields are present anywhere in obj.

    Raises CounterfactualLeakageError for counterfactual_action_effects.
    Raises HiddenLabelLeakageError for any other forbidden field.
    """
    all_names = _collect_field_names(obj)
    violations = all_names & FORBIDDEN_AGENT_FIELDS
    if "counterfactual_action_effects" in violations:
        raise CounterfactualLeakageError(
            "counterfactual field in agent observation: counterfactual_action_effects"
        )
    if violations:
        raise HiddenLabelLeakageError(
            f"forbidden hidden label fields in agent observation: {sorted(violations)}"
        )


def strip_to_agent_observation(step: Any) -> Any:
    """Return only public_observation from a StepRecord; assert it is safe."""
    obs = step.public_observation
    assert_agent_observation_safe(obs)
    return obs
