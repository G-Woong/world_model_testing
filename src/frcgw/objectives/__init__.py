"""frcgw.objectives — Losses, rewards, and loss weight scheduling.

Source docs:
- paper_context_ref/08_LOSS_REWARD_TRAINING_OBJECTIVE.md
- paper_context_ref/15_TDD_TECHNICAL_DESIGN_DOCUMENT_v1.md §12

Hard constraints (placeholder; implementation deferred to P3):
- Reward must be connected to the training/planning path, not metric-only (TRAIN-REQ-008).
- Valid switch reward applies only when all 4 conditions are satisfied (TRAIN-REQ-007).
- objectives depends on models, schemas — not on data generation (TDD §4).
"""
__all__: list[str] = []
