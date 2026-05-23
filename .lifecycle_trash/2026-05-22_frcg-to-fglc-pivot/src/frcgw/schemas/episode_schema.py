"""frcgw.schemas.episode_schema — EpisodeRecord and AuditMetadata.

Source docs:
- paper_context_ref/06_DATA_SCHEMA_AND_LABELING.md §0.4, §6
- paper_context_ref/15_TDD_TECHNICAL_DESIGN_DOCUMENT_v1.md §5.2
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .step_schema import StepRecord


@dataclass
class AuditMetadata:
    """Episode-level audit metadata. AUDIT_METADATA bucket only. Never inference input."""
    generator_version: str
    collection_timestamp: str
    schema_version: str
    split_id: str
    template_id: str | None = None
    seed: int | None = None
    policy_mixture: dict = field(default_factory=dict)
    leakage_check_flags: dict = field(default_factory=dict)


@dataclass
class EpisodeRecord:
    """Full episode record including hidden labels, counterfactuals, and audit metadata.

    task_family, split_id, template_id, seed must not be fed to model input (TDD §5.2).
    """
    episode_id: str
    dataset_version: str
    schema_version: str
    generator_version: str
    split_id: str
    task_family: str
    public_instruction: str
    steps: list[StepRecord]
    final_success: bool
    total_progress: float
    audit_metadata: AuditMetadata | None = None
