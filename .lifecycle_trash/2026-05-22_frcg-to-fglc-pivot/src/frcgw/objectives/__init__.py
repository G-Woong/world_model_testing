"""frcgw.objectives -- Losses, rewards, and loss weight scheduling.

Source docs:
- paper_context_ref/08_LOSS_REWARD_TRAINING_OBJECTIVE.md
- paper_context_ref/15_TDD_TECHNICAL_DESIGN_DOCUMENT_v1.md section 12
"""
from frcgw.objectives.losses import (
    DEFAULT_WEIGHTS,
    EFFECT_TYPE_VOCAB,
    GRAMMAR_VOCAB,
    REGIME_VOCAB,
    REVEAL_SHIFT_VOCAB,
    LossDict,
    compute_total_loss,
)
from frcgw.objectives.rewards import (
    R_compute_cost,
    R_failed_action_penalty,
    R_progress,
    R_repeated_failure_penalty,
)

__all__ = [
    "DEFAULT_WEIGHTS",
    "EFFECT_TYPE_VOCAB",
    "GRAMMAR_VOCAB",
    "REGIME_VOCAB",
    "REVEAL_SHIFT_VOCAB",
    "LossDict",
    "compute_total_loss",
    "R_compute_cost",
    "R_failed_action_penalty",
    "R_progress",
    "R_repeated_failure_penalty",
]
