"""frcgw.evaluation — Metrics, baselines, ablations, compute budget, eval runner.

Source docs:
- paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md
- paper_context_ref/11_MODEL_DATASET_SCALE_AND_TRAINING_BUDGET_v1.md
- paper_context_ref/15_TDD_TECHNICAL_DESIGN_DOCUMENT_v1.md §15

Hard constraints (placeholder; implementation deferred to P3/P6):
- Evaluation must compute mechanism metrics beyond success rate (EVAL-REQ-001).
- Must-not-disappear baselines: Frozen Base VLM/LLM, verifier-only,
  next-state-WM-only, uncertainty-gated planner, always-plan, random alternative (TRD §6.9).
- Must-not-disappear ablations: no-control-grammar, no-falsification,
  no-alternative-hypothesis, no-rollout, no-rewrite, no-compute-gate (TRD §6.9).
- evaluation depends on data, models, planning — training-only labels are never
  used as evaluation inputs (TDD §4).
- Fake numbers must never be output (EVAL-REQ-016).
"""
__all__: list[str] = []
