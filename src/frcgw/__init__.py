"""frcgw — Falsification-guided control-grammar world model for Web/GUI agents.

Source docs:
- paper_context_ref/00_CONTEXT_INDEX.md
- paper_context_ref/13_CLAUDE_CODE_EXECUTION_ROADMAP_v1.md
- paper_context_ref/14_TRD_TECHNICAL_REQUIREMENTS_DOCUMENT_v1.md
- paper_context_ref/15_TDD_TECHNICAL_DESIGN_DOCUMENT_v1.md
- paper_context_ref/FINAL_RESEARCH_BLUEPRINT.md

Hard constraints (placeholder; concrete implementation deferred to P1+):
- Hidden labels are never inference inputs (CLAUDE.md Absolute Data Rules).
- Generic GUI WM novelty framing is forbidden (CLAUDE.md Core Thesis).
- Implementation order: docs/scaffold → schema → text-only → GUI → VLM.
- P0 exports nothing. __all__ is intentionally empty.
"""
__all__: list[str] = []
