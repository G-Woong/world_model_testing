"""P1 gate test: visibility contract — forbidden fields raise in agent observation.

Source docs:
- paper_context_ref/06_DATA_SCHEMA_AND_LABELING.md §7, §14
- paper_context_ref/15_TDD_TECHNICAL_DESIGN_DOCUMENT_v1.md §6.1, §6.4
"""
from __future__ import annotations

import pytest
from frcgw.schemas.visibility import (
    assert_agent_observation_safe,
    HiddenLabelLeakageError,
    CounterfactualLeakageError,
    get_forbidden_agent_fields,
)
from frcgw.schemas.step_schema import PublicObservation


def _safe_obs() -> PublicObservation:
    return PublicObservation(instruction="click the login button")


def test_clean_observation_passes():
    assert_agent_observation_safe(_safe_obs())


def test_clean_dict_passes():
    assert_agent_observation_safe({"instruction": "submit form", "dom_snapshot_public": {}})


def test_true_control_grammar_in_dict_raises():
    with pytest.raises(HiddenLabelLeakageError):
        assert_agent_observation_safe({"instruction": "click", "true_control_grammar": "modal"})


def test_counterfactual_action_effects_raises_counterfactual_error():
    with pytest.raises(CounterfactualLeakageError):
        assert_agent_observation_safe({"instruction": "click", "counterfactual_action_effects": []})


def test_split_id_in_dict_raises():
    with pytest.raises(HiddenLabelLeakageError):
        assert_agent_observation_safe({"instruction": "fill form", "split_id": "train"})


def test_template_id_in_dict_raises():
    with pytest.raises(HiddenLabelLeakageError):
        assert_agent_observation_safe({"instruction": "submit", "template_id": "t42"})


def test_seed_in_dict_raises():
    with pytest.raises(HiddenLabelLeakageError):
        assert_agent_observation_safe({"instruction": "navigate", "seed": 42})


def test_true_regime_in_dict_raises():
    with pytest.raises(HiddenLabelLeakageError):
        assert_agent_observation_safe({"instruction": "click", "true_regime": "modal"})


def test_true_wrong_hypothesis_raises():
    with pytest.raises(HiddenLabelLeakageError):
        assert_agent_observation_safe({"instruction": "x", "true_wrong_hypothesis": True})


def test_oracle_best_action_raises():
    with pytest.raises(HiddenLabelLeakageError):
        assert_agent_observation_safe({"instruction": "click", "oracle_best_action": "submit"})


def test_oracle_regime_action_raises():
    with pytest.raises(HiddenLabelLeakageError):
        assert_agent_observation_safe({"instruction": "x", "oracle_regime_action": "r1"})


def test_oracle_grammar_action_raises():
    with pytest.raises(HiddenLabelLeakageError):
        assert_agent_observation_safe({"instruction": "x", "oracle_grammar_action": "g1"})


def test_policy_id_raises():
    with pytest.raises(HiddenLabelLeakageError):
        assert_agent_observation_safe({"instruction": "x", "policy_id": "oracle"})


def test_audit_metadata_raises():
    with pytest.raises(HiddenLabelLeakageError):
        assert_agent_observation_safe({"instruction": "x", "audit_metadata": {}})


def test_nested_forbidden_field_raises():
    with pytest.raises(HiddenLabelLeakageError):
        assert_agent_observation_safe({"instruction": "x", "sub": {"true_control_grammar": "g1"}})


def test_public_observation_dataclass_passes():
    obs = PublicObservation(
        instruction="navigate to settings",
        dom_snapshot_public={"root": "div"},
    )
    assert_agent_observation_safe(obs)


def test_get_forbidden_agent_fields_contains_all_required():
    fields = get_forbidden_agent_fields()
    required = {
        "true_regime", "true_control_grammar", "true_change_point",
        "true_reveal_vs_shift", "true_wrong_hypothesis",
        "counterfactual_action_effects",
        "oracle_regime_action", "oracle_grammar_action", "oracle_best_action",
        "split_id", "ood_type", "template_id", "seed", "policy_id", "audit_metadata",
    }
    assert required <= set(fields)
