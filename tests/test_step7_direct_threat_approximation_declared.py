"""Tests that BASE-026, BASE-027, BASE-028 all declare approximation_level."""

import pytest

from frcgw.evaluation.baselines import (
    CUWMStyleCandidateSimulationAgent,
    WACStyleConsequenceCorrectionAgent,
    WebWorldStyleSearchAgent,
)


@pytest.mark.parametrize(
    "cls,expected_id",
    [
        (WACStyleConsequenceCorrectionAgent, "BASE-026"),
        (CUWMStyleCandidateSimulationAgent, "BASE-027"),
        (WebWorldStyleSearchAgent, "BASE-028"),
    ],
)
def test_approximation_level_declared(cls, expected_id):
    """All three direct-threat baselines must declare approximation_level."""
    assert hasattr(cls, "approximation_level"), (
        f"{expected_id} ({cls.__name__}) missing 'approximation_level' class attr"
    )
    level = cls.approximation_level
    assert isinstance(level, str) and len(level) > 0, (
        f"{expected_id} approximation_level must be a non-empty string"
    )
    assert (
        "heuristic" in level.lower()
        or "proxy" in level.lower()
        or "infeasible" in level.lower()
    ), (
        f"{expected_id} approximation_level must mention 'heuristic', "
        f"'proxy', or 'infeasible': {level}"
    )


def test_base026_approximation_level_mentions_wac():
    level = WACStyleConsequenceCorrectionAgent.approximation_level
    assert "WAC" in level or "consequence" in level.lower()


def test_base027_approximation_level_mentions_cuwm():
    level = CUWMStyleCandidateSimulationAgent.approximation_level
    assert "CUWM" in level or "candidate" in level.lower()


def test_base028_approximation_level_exists_unchanged():
    """BASE-028 approximation_level must still exist (was already there)."""
    assert hasattr(WebWorldStyleSearchAgent, "approximation_level")
    level = WebWorldStyleSearchAgent.approximation_level
    assert "heuristic" in level.lower() or "proxy" in level.lower()


def test_paper_ssot_ids_present():
    """All three must have paper_ssot_id for registry tracking."""
    for cls in [
        WACStyleConsequenceCorrectionAgent,
        CUWMStyleCandidateSimulationAgent,
        WebWorldStyleSearchAgent,
    ]:
        assert hasattr(cls, "paper_ssot_id"), f"{cls.__name__} missing paper_ssot_id"
