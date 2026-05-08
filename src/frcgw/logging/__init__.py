"""frcgw.logging — Action-effect logging, counterfactual simulation, replay, manifest.

Source docs:
- paper_context_ref/06_DATA_SCHEMA_AND_LABELING.md
- paper_context_ref/12_DATA_COLLECTION_METHODOLOGY_v1.md
- paper_context_ref/15_TDD_TECHNICAL_DESIGN_DOCUMENT_v1.md §9

Hard constraints (placeholder; implementation deferred to P2/P4):
- CounterfactualRecord is never returned by the dataloader input collator (TDD §5.7).
- Every run must produce a RunManifest with config, seed, and status (TDD §20).
- logging depends on schemas, utils — not on training (TDD §4).
"""
__all__: list[str] = []
