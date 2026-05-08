"""frcgw.text_env — Symbolic text-only environment and trajectory collector.

Source docs:
- paper_context_ref/04_TEXT_ONLY_SMOKE_TESTBED.md
- paper_context_ref/12_DATA_COLLECTION_METHODOLOGY_v1.md
- paper_context_ref/15_TDD_TECHNICAL_DESIGN_DOCUMENT_v1.md §7

Hard constraints (placeholder; implementation deferred to P2):
- Hidden control grammar must not appear in visible_text (TEXT-REQ-002).
- text_env depends on schemas, data, logging — not on VLM or model training (TDD §4).
- Text-only results must never be claimed as Web/GUI evidence (TEXT-REQ-006).
- Minimum 8 task families required (TEXT-REQ-001).
"""
__all__: list[str] = []
