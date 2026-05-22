"""frcgw.evaluation.compute_budget -- ComputeBudgetLog dataclass.

Source MD: paper_context_ref/15_TDD_TECHNICAL_DESIGN_DOCUMENT_v1.md lines 1032-1042
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ComputeBudgetLog:
    planning_calls: int
    rollout_steps: int
    candidate_actions_scored: int
    top_k_alternatives: int
    wall_clock_seconds: float

    def total_compute_units(self) -> int:
        return self.planning_calls + self.rollout_steps + self.candidate_actions_scored
