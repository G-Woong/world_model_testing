"""frcgw.planning — Falsification scoring, alternative proposer, rollout, decision gate, rewrite.

Source docs:
- paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md
- paper_context_ref/15_TDD_TECHNICAL_DESIGN_DOCUMENT_v1.md §13

Hard constraints (placeholder; implementation deferred to P3):
- Falsification must not be reduced to a simple failure flag (PLAN-REQ-003).
- Uncertainty-gated baseline must be kept as a separate baseline, not collapsed
  into the falsification-guided planner (PLAN-REQ-007).
- planning depends on models/objectives outputs — hidden labels must never be
  used as inference input here (TDD §4).
- Gate rule: F_t > tau_f AND delta_V_t > tau_v AND P(action_switch) > tau_a (TDD §13.4).
"""
from frcgw.planning.alternative_proposer import HypothesisId, enumerate_hypotheses, log_prior, propose
from frcgw.planning.falsification import FalsificationEvidence, falsification_score, log_likelihood

__all__ = [
    "FalsificationEvidence",
    "HypothesisId",
    "enumerate_hypotheses",
    "falsification_score",
    "log_likelihood",
    "log_prior",
    "propose",
]
