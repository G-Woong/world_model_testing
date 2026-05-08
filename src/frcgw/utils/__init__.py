"""frcgw.utils — Seed setting, config loading, hashing, and I/O helpers.

Source docs:
- paper_context_ref/15_TDD_TECHNICAL_DESIGN_DOCUMENT_v1.md §4

Hard constraints (placeholder; implementation deferred to P1):
- utils depends on nothing (TDD §4 package layering; no scientific logic here).
- Every generation/training/eval run must call seed setter and config loader from utils.
"""
__all__: list[str] = []
