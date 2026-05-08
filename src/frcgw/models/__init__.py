"""frcgw.models — Encoders, latent heads, world model heads, text and VLM adapters.

Source docs:
- paper_context_ref/07_LATENT_ARCHITECTURE_DESIGN.md
- paper_context_ref/15_TDD_TECHNICAL_DESIGN_DOCUMENT_v1.md §11

Hard constraints (placeholder; implementation deferred to P3/P5):
- Default VLM adapter must freeze backbone parameters (MODEL-REQ-002, TDD §11.2).
- Full VLM fine-tuning is not allowed at initial stage (MODEL-REQ-003).
- models depends on schemas field names only — not on evaluator reports (TDD §4).
- 4-latent structure (z_state, z_regime, z_control_grammar, z_change_point) is a
  hypothesis to be validated by ablation, not a confirmed final design (TDD §11.3).
"""
__all__: list[str] = []
