"""frcgw.training — Training loops, checkpoints, and training monitor.

Source docs:
- paper_context_ref/08_LOSS_REWARD_TRAINING_OBJECTIVE.md
- paper_context_ref/11_MODEL_DATASET_SCALE_AND_TRAINING_BUDGET_v1.md
- paper_context_ref/15_TDD_TECHNICAL_DESIGN_DOCUMENT_v1.md §14

Hard constraints (placeholder; implementation deferred to P3/P5):
- Training must not start before leakage audit passes (TDD §14.2, NFR-REL-002).
- Hidden labels may only be used as training targets, never as model inputs (TRAIN-REQ-010).
- Every run must write a RunManifest with config_hash, seed, and status (TDD §20).
- Kill conditions: hidden field in batch, NaN loss, leakage report missing (TDD §14.3).
- Training does not start with 7B/72B VLM (SYS-REQ-001, phase gate).
"""
__all__: list[str] = []
