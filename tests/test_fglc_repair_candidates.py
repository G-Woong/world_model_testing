from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from fglc.repair.candidates import candidates_for
from fglc.repair.taxonomy import FailureCauseId


def test_candidates_for_undercapacity_R3_nonempty():
    result = candidates_for([FailureCauseId.MODEL_UNDERCAPACITY], "R3")
    assert len(result) >= 1


def test_candidate_field_types():
    result = candidates_for(
        [
            FailureCauseId.MODEL_UNDERCAPACITY,
            FailureCauseId.IMPLEMENTATION_BUG_SUSPECTED,
        ],
        "R3",
    )
    assert result
    for candidate in result:
        assert isinstance(candidate.cost_minutes, int) and candidate.cost_minutes > 0
        assert 0.0 <= candidate.risk <= 1.0
        assert 0.0 <= candidate.expected_signal <= 1.0
        assert isinstance(candidate.patch, dict)
        if candidate.cause_id != FailureCauseId.IMPLEMENTATION_BUG_SUSPECTED:
            assert candidate.patch
        assert re.match(r"^[A-Z_]+_[a-z0-9_]{2,40}$", candidate.id)


def test_candidate_cause_id_subset_of_input():
    causes = [
        FailureCauseId.MODEL_UNDERCAPACITY,
        FailureCauseId.SIGMA_CALIBRATION_FAILURE,
    ]
    result = candidates_for(causes, "R3")
    assert all(candidate.cause_id in causes for candidate in result)


def test_duplicate_cause_dedup():
    causes = [
        FailureCauseId.MODEL_UNDERCAPACITY,
        FailureCauseId.MODEL_UNDERCAPACITY,
    ]
    result1 = candidates_for(causes, "R3")
    result2 = candidates_for([FailureCauseId.MODEL_UNDERCAPACITY], "R3")
    assert result1 == result2


def test_phase_filter_drops_inapplicable():
    result = candidates_for([FailureCauseId.CORRECTION_TOO_WEAK], "R3")
    assert result == []


def test_implementation_bug_suspected_has_sentinel_patch():
    result = candidates_for([FailureCauseId.IMPLEMENTATION_BUG_SUSPECTED], "R3")
    assert len(result) >= 1
    assert result[0].patch == {"action": "manual_blocker_report"}


def test_candidates_for_all_d3_cause_groups():
    test_cases = [
        (FailureCauseId.MODEL_UNDERCAPACITY, "R3"),
        (FailureCauseId.SIGMA_CALIBRATION_FAILURE, "R4"),
        (FailureCauseId.ATTENTION_COLLAPSE, "R5"),
        (FailureCauseId.CORRECTION_TOO_WEAK, "R6"),
        (FailureCauseId.CORRECTION_TOO_LARGE, "R6"),
        (FailureCauseId.PLANNER_BUDGET_TOO_LOW, "R7"),
        (FailureCauseId.IMPLEMENTATION_BUG_SUSPECTED, "R3"),
    ]
    for cause, phase in test_cases:
        result = candidates_for([cause], phase)
        assert len(result) >= 1, f"No candidates for {cause} in phase {phase}"
