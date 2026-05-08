"""frcgw.gui_env — Synthetic Web/GUI browser-like environment and collector.

Source docs:
- paper_context_ref/05_SYNTHETIC_WEB_GUI_ENVIRONMENT.md
- paper_context_ref/12_DATA_COLLECTION_METHODOLOGY_v1.md
- paper_context_ref/15_TDD_TECHNICAL_DESIGN_DOCUMENT_v1.md §8

Hard constraints (placeholder; implementation deferred to P4):
- Production/private website scraping must not be the main data source (GUI-REQ-010).
- Hidden regime/control-grammar oracle labels must exist outside agent observation (GUI-REQ-004).
- Deterministic replay must be supported (GUI-REQ-008).
- gui_env depends on schemas, logging, utils — not on model internals (TDD §4).
"""
__all__: list[str] = []
