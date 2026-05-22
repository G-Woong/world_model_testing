"""Tests for text-only environment: state transitions, grammar engine, leakage."""
from __future__ import annotations

import random

import pytest

from frcgw.text_env.generator import (
    EpisodeSpecGenerator,
    TaskFamily,
    build_initial_state,
)
from frcgw.text_env.grammar import ControlGrammar, GrammarEngine
from frcgw.text_env.state import TextEpisodeSpec, TextState
from frcgw.schemas.step_schema import PublicObservation
from frcgw.schemas.visibility import FORBIDDEN_AGENT_FIELDS, assert_agent_observation_safe
from frcgw.text_env.collector import build_public_observation


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_spec(family: str = TaskFamily.MODAL_BLOCKER, seed: int = 1) -> TextEpisodeSpec:
    gen = EpisodeSpecGenerator(seed=seed)
    return gen.generate(family=family)


def _engine(grammar: str) -> GrammarEngine:
    return GrammarEngine(grammar)


# ---------------------------------------------------------------------------
# TextState: hidden field absence in PublicObservation
# ---------------------------------------------------------------------------

class TestHiddenFieldAbsence:
    def test_build_public_observation_has_no_forbidden_fields(self):
        spec = _make_spec(TaskFamily.SEARCH_FORM)
        state = build_initial_state(spec)
        obs = build_public_observation(state, spec.public_instruction, [])
        # assert_agent_observation_safe raises if any forbidden field present
        assert_agent_observation_safe(obs)

    def test_visible_text_not_in_forbidden_set(self):
        # visible_text is not a forbidden field name — just its content must be safe
        spec = _make_spec(TaskFamily.MODAL_BLOCKER)
        state = build_initial_state(spec)
        obs = build_public_observation(state, spec.public_instruction, [])
        field_names = set(obs.__dataclass_fields__.keys())
        assert field_names.isdisjoint(FORBIDDEN_AGENT_FIELDS)

    def test_candidate_actions_have_no_grammar_token_names(self):
        for family in TaskFamily:
            spec = _make_spec(family)
            state = build_initial_state(spec)
            for ca in state.public_actions:
                # action_type must not embed grammar enum values
                for grammar_val in ControlGrammar:
                    assert grammar_val.value not in ca.action_type, (
                        f"Grammar token {grammar_val.value!r} in action_type {ca.action_type!r}"
                    )


# ---------------------------------------------------------------------------
# State transition determinism
# ---------------------------------------------------------------------------

class TestStateTransitionDeterminism:
    def test_same_seed_same_spec(self):
        gen1 = EpisodeSpecGenerator(seed=42)
        gen2 = EpisodeSpecGenerator(seed=42)
        spec1 = gen1.generate(family=TaskFamily.SEARCH_FORM)
        spec2 = gen2.generate(family=TaskFamily.SEARCH_FORM)
        assert spec1.episode_id == spec2.episode_id
        assert spec1.hidden_control_grammar == spec2.hidden_control_grammar
        assert spec1.public_instruction == spec2.public_instruction

    def test_initial_state_deterministic(self):
        spec = _make_spec(TaskFamily.NESTED_SCROLL, seed=7)
        s1 = build_initial_state(spec)
        s2 = build_initial_state(spec)
        assert s1.visible_text == s2.visible_text
        assert s1._hidden_control_grammar == s2._hidden_control_grammar

    def test_different_seed_different_episode_id(self):
        gen = EpisodeSpecGenerator(seed=1)
        spec_a = gen.generate(family=TaskFamily.SEARCH_FORM)
        spec_b = gen.generate(family=TaskFamily.SEARCH_FORM)
        assert spec_a.episode_id != spec_b.episode_id


# ---------------------------------------------------------------------------
# GrammarEngine: wrong_grammar_failure 4-condition rule (CONST-04-001~04-006)
# ---------------------------------------------------------------------------

class TestWrongGrammarFailure4Condition:
    """is_wrong_grammar_failure must be True iff all 4 conditions are met."""

    def _flags_empty(self) -> dict:
        return {}

    def test_wrong_grammar_when_precondition_unmet(self):
        engine = _engine(ControlGrammar.MODAL_CONFIRM_THEN_ACTION)
        flags = self._flags_empty()
        # click_filter requires modal_closed; without it, should be wrong_grammar
        assert engine.is_wrong_grammar_failure(flags, "click_filter", "none") is True

    def test_not_wrong_grammar_when_precondition_met(self):
        engine = _engine(ControlGrammar.MODAL_CONFIRM_THEN_ACTION)
        flags = {"modal_closed": True}
        assert engine.is_wrong_grammar_failure(flags, "click_filter", "none") is False

    def test_not_wrong_grammar_when_event_delayed(self):
        engine = _engine(ControlGrammar.MODAL_CONFIRM_THEN_ACTION)
        flags = self._flags_empty()
        # delayed events must NOT be classified as wrong_grammar (REVISION-03-011)
        assert engine.is_wrong_grammar_failure(flags, "click_filter", "delayed") is False

    def test_not_wrong_grammar_when_event_noisy(self):
        engine = _engine(ControlGrammar.MODAL_CONFIRM_THEN_ACTION)
        flags = self._flags_empty()
        assert engine.is_wrong_grammar_failure(flags, "click_filter", "noisy") is False

    def test_not_wrong_grammar_unknown_action(self):
        engine = _engine(ControlGrammar.DIRECT_SEARCH)
        flags = self._flags_empty()
        assert engine.is_wrong_grammar_failure(flags, "nonexistent_action", "none") is False


# ---------------------------------------------------------------------------
# GrammarEngine: delayed / no_op_valid not classified as wrong grammar
# ---------------------------------------------------------------------------

class TestDelayedAndNoOpValid:
    def test_delayed_event_not_wrong_grammar(self):
        engine = _engine(ControlGrammar.WAIT_UNTIL_ENABLED_THEN_CLICK)
        flags = {}
        # wait action with delayed event — should NOT be wrong grammar
        result = engine.is_wrong_grammar_failure(flags, "click_result", "delayed")
        assert result is False

    def test_no_op_wait_not_wrong_grammar(self):
        engine = _engine(ControlGrammar.WAIT_UNTIL_ENABLED_THEN_CLICK)
        flags = {}
        # wait itself has no precondition — precondition_satisfied returns True
        assert engine.precondition_satisfied(flags, "wait") is True
        assert engine.is_wrong_grammar_failure(flags, "wait", "none") is False


# ---------------------------------------------------------------------------
# GrammarEngine: apply produces correct transitions
# ---------------------------------------------------------------------------

class TestGrammarEngineApply:
    def test_apply_without_precondition_returns_no_change(self):
        engine = _engine(ControlGrammar.DIRECT_SEARCH)
        flags = {}
        new_flags, delta, effect = engine.apply(flags, "submit_search")
        assert effect == "no_state_change"
        assert delta == 0.0
        assert "query_typed" not in new_flags

    def test_apply_with_precondition_succeeds(self):
        engine = _engine(ControlGrammar.DIRECT_SEARCH)
        flags = {"query_typed": True}
        new_flags, delta, effect = engine.apply(flags, "submit_search")
        assert effect == "task_complete"
        assert delta > 0.0

    def test_is_success_after_task_complete(self):
        engine = _engine(ControlGrammar.DIRECT_SEARCH)
        flags = {"query_typed": True}
        new_flags, _, _ = engine.apply(flags, "submit_search")
        new_flags["task_complete"] = True
        assert engine.is_success(new_flags) is True


# ---------------------------------------------------------------------------
# Generator: paraphrase coverage (≥3 per family)
# ---------------------------------------------------------------------------

class TestGeneratorParaphraseCoverage:
    def test_each_family_has_at_least_3_instructions(self):
        from frcgw.text_env.generator import _INSTRUCTIONS
        for family in TaskFamily:
            assert len(_INSTRUCTIONS[family]) >= 3, (
                f"{family} has fewer than 3 instruction paraphrases"
            )

    def test_each_family_has_at_least_3_initial_states(self):
        from frcgw.text_env.generator import _INITIAL_STATES
        for family in TaskFamily:
            assert len(_INITIAL_STATES[family]) >= 3, (
                f"{family} has fewer than 3 initial state paraphrases"
            )
