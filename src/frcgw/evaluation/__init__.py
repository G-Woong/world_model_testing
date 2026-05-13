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
from frcgw.evaluation.compute_budget import ComputeBudgetLog
from frcgw.evaluation.ablations import ABLATION_REGISTRY, AblationConfig, apply_ablation
from frcgw.evaluation.eval_runner import EvaluationResult, EvaluationRunner
from frcgw.evaluation.baselines import (
    AlwaysPlanAgent,
    BaselineAgent,
    FORBIDDEN_AGENT_KEYS,
    FrozenBaseAgent,
    NextStateWMOnlyAgent,
    OracleAgent,
    RandomAlternativePlannerAgent,
    ReactiveAgent,
    RetryAfterFailureAgent,
    UncertaintyGatedAgent,
    VerifierOnlyAgent,
)
from frcgw.evaluation.metrics import (
    action_switch_delay,
    assert_no_hidden_labels_in_input,
    failed_action_repetition_rate,
    false_planning_call_rate,
    falsification_calibration,
    falsification_precision_recall,
    normalized_return,
    progress_per_compute,
    recovery_delay,
    task_success_rate,
    wrong_control_grammar_persistence,
)

__all__ = [
    "ComputeBudgetLog",
    "ABLATION_REGISTRY",
    "AblationConfig",
    "apply_ablation",
    "EvaluationResult",
    "EvaluationRunner",
    "FORBIDDEN_AGENT_KEYS",
    "BaselineAgent",
    "FrozenBaseAgent",
    "ReactiveAgent",
    "RetryAfterFailureAgent",
    "VerifierOnlyAgent",
    "NextStateWMOnlyAgent",
    "AlwaysPlanAgent",
    "UncertaintyGatedAgent",
    "RandomAlternativePlannerAgent",
    "OracleAgent",
    "task_success_rate",
    "normalized_return",
    "wrong_control_grammar_persistence",
    "failed_action_repetition_rate",
    "recovery_delay",
    "falsification_precision_recall",
    "falsification_calibration",
    "progress_per_compute",
    "false_planning_call_rate",
    "action_switch_delay",
    "assert_no_hidden_labels_in_input",
]
