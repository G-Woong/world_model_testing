from __future__ import annotations

from pathlib import Path

import pytest

from frcgw.evaluation.baselines import CUWMFaithfulCandidate, WACFaithfulCandidate
from frcgw.schemas.step_schema import CandidateAction, PublicObservation


def _mock_obs() -> PublicObservation:
    return PublicObservation(
        instruction="finish the visible task",
        dom_snapshot_public={"visible": True},
        accessibility_tree_public={"role": "root"},
        history_public=[],
        candidate_actions_public=[
            CandidateAction("click-primary", "click", {"target": "primary"}),
            CandidateAction("wait-for-update", "wait", {}),
        ],
    )


def _guarded_phrases() -> tuple[str, str, str]:
    return (
        "defeats " + "WAC",
        "outperforms " + "CUWM",
        "superior to " + "WebWorld",
    )


def test_wac_faithful_no_eval_labels() -> None:
    with pytest.raises(AssertionError, match="Hidden label leak"):
        WACFaithfulCandidate().act(
            _mock_obs(),
            eval_labels={"true_control_grammar": "direct_search"},
        )


def test_cuwm_faithful_no_hidden_labels() -> None:
    with pytest.raises(AssertionError, match="Hidden label leak"):
        CUWMFaithfulCandidate().act(
            _mock_obs(),
            eval_labels={"oracle_best_action": "some_action"},
        )


def test_approximation_level_honest() -> None:
    allowed_levels = {"partial", "faithful_candidate", "heuristic"}

    assert WACFaithfulCandidate.approximation_level in allowed_levels
    assert CUWMFaithfulCandidate.approximation_level in allowed_levels


def test_forbidden_wording_absent() -> None:
    source = Path("src/frcgw/evaluation/baselines.py").read_text(encoding="utf-8")

    assert sum(source.count(phrase) for phrase in _guarded_phrases()) == 0
