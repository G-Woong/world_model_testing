from __future__ import annotations

import inspect
import re
from types import SimpleNamespace

import pytest
import torch
from torch import nn

from frcgw.evaluation.frcg_agent import _GRAMMAR_IDX_TO_NAME, TextFRCGModelAgent
from frcgw.evaluation.metrics import compute_wrong_grammar_persistence_v1
from frcgw.models.text_frcg_model import ModelOutput
from frcgw.schemas.step_schema import CandidateAction, PublicObservation
from frcgw.text_env.grammar import ControlGrammar


def _obs() -> PublicObservation:
    return PublicObservation(
        instruction="click the right item",
        dom_snapshot_public={"visible": True},
        accessibility_tree_public={"role": "root"},
        screenshot_ref="screen-1",
        candidate_actions_public=[
            CandidateAction("a", "click", {"target": "left"}),
            CandidateAction("b", "click", {"target": "right"}),
        ],
    )


class _FixedGrammarModel(nn.Module):
    def __init__(self, best_idx: int, n_grammars: int = 8) -> None:
        super().__init__()
        self.best_idx = best_idx
        self.n_grammars = n_grammars

    def forward(self, _public_input: PublicObservation) -> ModelOutput:
        grammar_logits = torch.zeros(1, self.n_grammars)
        grammar_logits[0, self.best_idx] = 10.0
        return ModelOutput(
            z_state=torch.zeros(1, 32),
            z_regime_logits=torch.zeros(1, 8),
            z_grammar_logits=grammar_logits,
            z_change_logits=torch.zeros(1, 12),
            z_reveal_shift_logits=torch.zeros(1, 3),
            shared_h=torch.zeros(1, 128),
            posterior_entropy=torch.zeros(1),
            aux_precondition=torch.zeros(1),
            aux_failure_risk=torch.zeros(1),
        )


def test_mapping_covers_all_8_grammars() -> None:
    expected = [grammar.value for grammar in ControlGrammar]

    assert len(_GRAMMAR_IDX_TO_NAME) == 8
    assert _GRAMMAR_IDX_TO_NAME == expected


def test_emitted_id_in_grammar_enum() -> None:
    agent = TextFRCGModelAgent()

    agent.act(_obs())

    emitted_id = agent._last_selected_hypothesis_id
    assert emitted_id in {grammar.value for grammar in ControlGrammar}
    assert emitted_id is None or re.fullmatch(r"grammar_\d+", emitted_id) is None


def test_persistence_v1_computable_after_fix() -> None:
    correct_id = "required_dropdown_then_search"
    episode = SimpleNamespace(
        evaluation_labels=SimpleNamespace(
            evidence_timestamp=1,
            correct_hypothesis_id=correct_id,
        ),
        steps=[
            SimpleNamespace(
                step_index=0,
                action=SimpleNamespace(selected_hypothesis_id="direct_search"),
            ),
            SimpleNamespace(
                step_index=1,
                action=SimpleNamespace(selected_hypothesis_id=correct_id),
            ),
        ],
    )

    result = compute_wrong_grammar_persistence_v1([episode])

    assert result["status"] == "OK"
    assert result["count_blocked"] == 0
    assert result["count_episodes"] == 1
    assert result["mean_persistence"] == 0


def test_no_oracle_leakage() -> None:
    signature = inspect.signature(TextFRCGModelAgent.act)
    for forbidden_name in (
        "correct_hypothesis_id",
        "oracle_grammar_action",
        "true_control_grammar",
    ):
        assert forbidden_name not in signature.parameters

    obs = _obs()
    agent = TextFRCGModelAgent(model=_FixedGrammarModel(best_idx=0))
    action_without_labels, _log = agent.act(obs)
    agent.reset()
    action_with_labels, _log = agent.act(
        obs,
        eval_labels={
            "correct_hypothesis_id": "modal_confirm_then_action",
            "oracle_grammar_action": "hidden",
            "true_control_grammar": "pagination_or_infinite_scroll",
        },
    )

    assert action_with_labels == action_without_labels
    for forbidden_name in (
        "correct_hypothesis_id",
        "oracle_grammar_action",
        "true_control_grammar",
    ):
        with pytest.raises(TypeError):
            agent.act(obs, **{forbidden_name: "hidden"})  # type: ignore[arg-type]


def test_fallback_for_unknown_idx() -> None:
    agent = TextFRCGModelAgent(model=_FixedGrammarModel(best_idx=99, n_grammars=100))

    agent.act(_obs())

    assert agent._last_selected_hypothesis_id == "grammar_99"
    assert agent._last_selected_hypothesis_id.startswith("grammar_")


def test_regression_no_grammar_idx_in_output() -> None:
    for idx, expected_name in enumerate(_GRAMMAR_IDX_TO_NAME):
        agent = TextFRCGModelAgent(model=_FixedGrammarModel(best_idx=idx))

        agent.act(_obs())

        emitted_id = agent._last_selected_hypothesis_id
        assert emitted_id == expected_name
        assert emitted_id is None or re.fullmatch(r"grammar_\d+", emitted_id) is None
