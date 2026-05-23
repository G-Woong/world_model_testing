from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from fglc.repair.candidates import RepairCandidate
from fglc.repair.ranker import rank
from fglc.repair.taxonomy import FailureCauseId


def make_candidate(
    id: str,
    cost: int,
    risk: float,
    signal: float,
    cause_id: FailureCauseId | None = None,
) -> RepairCandidate:
    return RepairCandidate(
        id=id,
        cause_id=cause_id or FailureCauseId.MODEL_UNDERCAPACITY,
        patch={"hidden_dim": 256},
        cost_minutes=cost,
        risk=risk,
        expected_signal=signal,
        description="test",
        applicable_phases=("R3",),
    )


def test_sorted_by_cost_then_risk_then_signal_desc_then_id():
    c1 = make_candidate("c1", cost=5, risk=0.1, signal=0.6)
    c2 = make_candidate("c2", cost=10, risk=0.1, signal=0.6)
    c3 = make_candidate("c3", cost=5, risk=0.2, signal=0.6)
    result = rank([c2, c3, c1])
    assert result[0].candidate.id == "c1"
    assert result[1].candidate.id == "c3"
    assert result[2].candidate.id == "c2"


def test_score_in_unit_interval():
    candidates = [
        make_candidate(f"c{i}", cost=i + 1, risk=0.1, signal=0.5)
        for i in range(5)
    ]
    result = rank(candidates)
    assert all(0.0 <= ranked.score <= 1.0 for ranked in result)


def test_empty_returns_empty():
    assert rank([]) == []


def test_single_candidate_score_is_one():
    candidate = make_candidate("c1", cost=5, risk=0.1, signal=0.5)
    result = rank([candidate])
    assert len(result) == 1
    assert result[0].rank == 1
    assert result[0].score == 1.0


def test_invalid_cost_raises():
    candidate = make_candidate("bad", cost=0, risk=0.1, signal=0.5)
    with pytest.raises(ValueError):
        rank([candidate])


def test_invalid_risk_raises():
    candidate = make_candidate("bad", cost=5, risk=1.5, signal=0.5)
    with pytest.raises(ValueError):
        rank([candidate])


def test_tie_breaker_by_id():
    c1 = make_candidate("aaa", cost=5, risk=0.1, signal=0.5)
    c2 = make_candidate("bbb", cost=5, risk=0.1, signal=0.5)
    result = rank([c2, c1])
    assert result[0].candidate.id == "aaa"


def test_round_trip_diagnose_candidates_rank():
    from fglc.repair.candidates import candidates_for
    from fglc.repair.diagnose import diagnose

    metrics = {"id_nll": 0.7, "stagnant_epochs": 12, "train_nll": 0.7}
    causes = diagnose(metrics, "R3")
    assert len(causes) >= 1
    candidates = candidates_for(causes, "R3")
    assert len(candidates) >= 1
    result = rank(candidates)
    assert len(result) >= 1
    assert result[0].rank == 1
    assert re.match(r"^[A-Z_]+_[a-z0-9_]{2,40}$", result[0].candidate.id)
