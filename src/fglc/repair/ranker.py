"""Source: docs/EXPERIMENT_REPAIR_LOOP_PLAN.md D.1 step6 + H + plan A.6 (lexicographic + normalized)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from fglc.repair.candidates import RepairCandidate


@dataclass(frozen=True)
class RankedCandidate:
    candidate: RepairCandidate
    rank: int
    score: float


def rank(candidates: Sequence[RepairCandidate]) -> list[RankedCandidate]:
    for candidate in candidates:
        if candidate.cost_minutes <= 0:
            raise ValueError(f"cost_minutes must be > 0: {candidate.id}")
        if not (0.0 <= candidate.risk <= 1.0):
            raise ValueError(f"risk must be in [0,1]: {candidate.id}")
        if not (0.0 <= candidate.expected_signal <= 1.0):
            raise ValueError(f"expected_signal must be in [0,1]: {candidate.id}")

    sorted_ = sorted(
        candidates,
        key=lambda candidate: (
            candidate.cost_minutes,
            candidate.risk,
            -candidate.expected_signal,
            candidate.id,
        ),
    )
    n = len(sorted_)
    denom = max(1, n - 1)
    return [
        RankedCandidate(
            candidate=candidate,
            rank=i + 1,
            score=((n - (i + 1)) / denom if n > 1 else 1.0),
        )
        for i, candidate in enumerate(sorted_)
    ]
