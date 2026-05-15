"""Leakage audit helpers for GUI agent observations."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from frcgw.schemas.visibility import FORBIDDEN_AGENT_FIELDS, _collect_field_names


FORBIDDEN_GUI_AGENT_FIELDS: frozenset[str] = FORBIDDEN_AGENT_FIELDS | frozenset({
    "true_grammar",
    "gold_element_id",
    "oracle_target",
    "true_label",
    "counterfactual_action",
})


@dataclass(frozen=True)
class GUILeakageAuditResult:
    passed: bool
    violations: list[str] = field(default_factory=list)


class GUILeakageError(RuntimeError):
    """Raised when GUI agent-observable data contains forbidden fields."""

    def __init__(self, violations: list[str]) -> None:
        self.violations = violations
        super().__init__(f"forbidden GUI agent observation fields: {violations}")


def audit_gui_observation(obs: dict[str, Any]) -> GUILeakageAuditResult:
    """Audit an agent observation dictionary and raise on hidden-label leakage."""
    field_names = _collect_field_names(obs)
    violations = sorted(field_names & FORBIDDEN_GUI_AGENT_FIELDS)
    result = GUILeakageAuditResult(passed=not violations, violations=violations)
    if violations:
        raise GUILeakageError(violations)
    return result
