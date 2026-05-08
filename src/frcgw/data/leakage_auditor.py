"""frcgw.data.leakage_auditor — Leakage audit for dataset batches and agent inputs.

Source docs:
- paper_context_ref/06_DATA_SCHEMA_AND_LABELING.md §14, §15
- paper_context_ref/14_TRD_TECHNICAL_REQUIREMENTS_DOCUMENT_v1.md §6.6
- paper_context_ref/15_TDD_TECHNICAL_DESIGN_DOCUMENT_v1.md §10.5
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..schemas.visibility import FORBIDDEN_AGENT_FIELDS, _collect_field_names


_COUNTERFACTUAL_FIELDS: frozenset[str] = frozenset({
    "counterfactual_action_effects",
    "counterfactuals",
    "counterfactual_id",
    "counterfactual_effect_type",
    "counterfactual_progress_delta",
    "counterfactual_failure_risk",
    "is_oracle_best",
})


@dataclass
class AuditReport:
    source: str
    passed: bool
    forbidden_found: list[str] = field(default_factory=list)
    counterfactual_found: list[str] = field(default_factory=list)


class LeakageAuditor:
    """Audits agent inputs and dataset batches for hidden label or counterfactual leakage.

    Source: paper_context_ref/06_DATA_SCHEMA_AND_LABELING.md §14-15
    Fail-closed: ambiguous inputs are treated as failures (TDD-PRINCIPLE-009).
    """

    def audit_agent_input(self, obj: Any, source: str = "unknown") -> AuditReport:
        """Scan obj for forbidden hidden label or counterfactual fields."""
        all_names = _collect_field_names(obj)
        if isinstance(obj, dict):
            all_names.update(obj.keys())
        forbidden = sorted(all_names & FORBIDDEN_AGENT_FIELDS)
        counterfactual = sorted(all_names & _COUNTERFACTUAL_FIELDS)
        return AuditReport(
            source=source,
            passed=len(forbidden) == 0 and len(counterfactual) == 0,
            forbidden_found=forbidden,
            counterfactual_found=counterfactual,
        )

    def audit_batch(self, batch: dict, source: str = "dataloader") -> AuditReport:
        """Audit a dataloader batch dict for forbidden fields."""
        return self.audit_agent_input(batch, source=source)

    def assert_clean(self, obj: Any, source: str = "unknown") -> None:
        """Raise ValueError if audit fails."""
        report = self.audit_agent_input(obj, source=source)
        if not report.passed:
            msgs: list[str] = []
            if report.forbidden_found:
                msgs.append(f"forbidden fields: {report.forbidden_found}")
            if report.counterfactual_found:
                msgs.append(f"counterfactual fields: {report.counterfactual_found}")
            raise ValueError(f"[LeakageAuditor] {source} failed: {'; '.join(msgs)}")
