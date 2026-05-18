"""Effect-type mappings cover v0_3 public effect strings."""
from __future__ import annotations

import pytest

from frcgw.objectives.losses import EFFECT_TYPE_VOCAB
from frcgw.planning.planner import _effect_type_id
from frcgw.text_env.counterfactual_rollout import _PUBLIC_EFFECT_TYPES


_PUBLIC_LIST = list(_PUBLIC_EFFECT_TYPES)


@pytest.mark.parametrize("effect_str", _PUBLIC_LIST)
def test_planner_mapping_covers_public_effect_types(effect_str: str) -> None:
    result = _effect_type_id(effect_str)
    assert 0 <= result <= 6, f"{effect_str} -> {result} out of model range [0,6]"


@pytest.mark.parametrize(
    "effect_str",
    ["state_change", "blocker_removed", "delayed_effect", "task_complete"],
)
def test_planner_mapping_not_in_short_circuit(effect_str: str) -> None:
    result = _effect_type_id(effect_str)
    assert result not in {0, 6}, (
        f"{effect_str} maps to {result} which is in short-circuit set {{0, 6}}"
    )


def test_no_state_change_maps_to_zero() -> None:
    assert _effect_type_id("no_state_change") == 0


@pytest.mark.parametrize("effect_str", _PUBLIC_LIST)
def test_vocab_and_planner_agree(effect_str: str) -> None:
    planner_id = _effect_type_id(effect_str)
    vocab_id = EFFECT_TYPE_VOCAB.get(effect_str)
    assert vocab_id is not None, f"{effect_str} missing from EFFECT_TYPE_VOCAB"
    assert planner_id == vocab_id, (
        f"Mismatch: planner={planner_id}, vocab={vocab_id} for '{effect_str}'"
    )


def test_max_vocab_id_within_model_range() -> None:
    max_id = max(EFFECT_TYPE_VOCAB.values())
    assert max_id <= 6, f"Max vocab ID {max_id} exceeds model n_effect_types-1=6"
