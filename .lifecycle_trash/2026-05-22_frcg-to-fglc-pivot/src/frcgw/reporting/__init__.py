"""frcgw.reporting — Markdown/CSV/figure report generation from run logs.

Source docs:
- paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md
- paper_context_ref/15_TDD_TECHNICAL_DESIGN_DOCUMENT_v1.md §16
- paper_context_ref/FINAL_RESEARCH_BLUEPRINT.md

Hard constraints (placeholder; implementation deferred to P8):
- Report generator must read only from run log and metric artifacts (TDD §16.3).
- Report generation fails if metric artifact, run manifest, or baseline artifact is missing.
- Negative and non-effect ablation results must not be hidden (REPORT-REQ-002).
- reporting depends on evaluation outputs — raw fake numbers are forbidden (TDD §4).
"""
__all__: list[str] = []
