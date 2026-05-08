"""frcgw.data — Split management, shard export, leakage audit, coverage audit, dataset loader.

Source docs:
- paper_context_ref/06_DATA_SCHEMA_AND_LABELING.md
- paper_context_ref/12_DATA_COLLECTION_METHODOLOGY_v1.md
- paper_context_ref/15_TDD_TECHNICAL_DESIGN_DOCUMENT_v1.md §10

Hard constraints:
- Dataset shard must not be fed to training loader before leakage audit passes (DATA-REQ-009).
- Collator must log all input batch field names and reject forbidden fields (TDD §10.5).
- Counterfactuals are only returned when config explicitly requests them as training targets,
  never as inference input (TDD §10.5).
- data depends on schemas, logging, utils — not on model-specific code except collator (TDD §4).
"""
from .leakage_auditor import LeakageAuditor, AuditReport

__all__ = ["LeakageAuditor", "AuditReport"]
