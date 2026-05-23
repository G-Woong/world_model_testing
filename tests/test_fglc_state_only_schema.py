"""Tests for ManiSkill state-only schema: FORBIDDEN field isolation.

Source: docs/STEP11_PLAN.md §G Checkpoint 1 (schema gate), §I.2
Verifies inference dict has no FORBIDDEN_AGENT_FIELDS, eval-only dict has all.
"""

from __future__ import annotations

import pytest

from fglc.data.maniskill_schema import (
    EvalOnlyTransition,
    InferenceTransition,
    OOD_PARAMS,
    REGIME_ID,
)
from fglc.schemas.visibility import FORBIDDEN_AGENT_FIELDS


def _make_inference(**overrides) -> dict:
    defaults = {"state": [0.0] * 42, "action": [0.0] * 8, "reward": 0.0, "done": False}
    defaults.update(overrides)
    return InferenceTransition(**defaults).to_dict()


def _make_eval_only(**overrides) -> dict:
    defaults = {
        "regime_id": 0,
        "ood_type": "id",
        "true_mass": 0.064,
        "true_friction": 0.0,
        "true_latency": 0,
        "true_noise_sigma": 0.0,
        "true_action_gain": 1.0,
        "episode_id": 0,
        "step_idx": 0,
        "split": "train_id",
        "task_id": "PickCube-v1",
        "seed": 42,
        "template_id": "default",
        "success": False,
    }
    defaults.update(overrides)
    return EvalOnlyTransition(**defaults).to_dict()


class TestInferenceTransitionForbiddenFieldsFree:
    def test_no_regime_id(self):
        d = _make_inference()
        assert "regime_id" not in d

    def test_no_true_mass(self):
        d = _make_inference()
        assert "true_mass" not in d

    def test_no_true_friction(self):
        d = _make_inference()
        assert "true_friction" not in d

    def test_no_split_id(self):
        d = _make_inference()
        assert "split_id" not in d

    def test_no_ood_type(self):
        d = _make_inference()
        assert "ood_type" not in d

    def test_no_oracle_action(self):
        d = _make_inference()
        assert "oracle_action" not in d

    def test_no_seed(self):
        d = _make_inference()
        assert "seed" not in d

    def test_all_forbidden_fields_absent(self):
        """All 12 FORBIDDEN_AGENT_FIELDS must be absent from inference dict."""
        d = _make_inference()
        present = FORBIDDEN_AGENT_FIELDS & set(d.keys())
        assert not present, f"Forbidden fields in inference dict: {present}"

    def test_required_fields_present(self):
        d = _make_inference()
        assert set(d.keys()) == {"state", "action", "reward", "done"}

    def test_state_dim(self):
        d = _make_inference()
        assert len(d["state"]) == 42

    def test_action_dim(self):
        d = _make_inference()
        assert len(d["action"]) == 8


class TestEvalOnlyTransitionHasForbiddenFields:
    def test_has_regime_id(self):
        d = _make_eval_only()
        assert "regime_id" in d

    def test_has_true_mass(self):
        d = _make_eval_only()
        assert "true_mass" in d

    def test_has_true_friction(self):
        d = _make_eval_only()
        assert "true_friction" in d

    def test_has_seed(self):
        d = _make_eval_only()
        assert "seed" in d

    def test_has_ood_type(self):
        d = _make_eval_only()
        assert "ood_type" in d

    def test_regime_id_values_match_split(self):
        for split, rid in REGIME_ID.items():
            d = _make_eval_only(split=split, regime_id=rid)
            assert d["regime_id"] == rid


class TestOODParamsSchema:
    def test_id_splits_have_default_mass(self):
        for split in ("train_id", "val_id", "test_id"):
            assert OOD_PARAMS[split]["object_mass"] == pytest.approx(0.064, abs=1e-4)

    def test_ood_mass_low_has_elevated_mass(self):
        assert OOD_PARAMS["ood_mass_low"]["object_mass"] > 0.064

    def test_ood_friction_low_has_elevated_friction(self):
        assert OOD_PARAMS["ood_friction_low"]["joint_friction"] > 0.0

    def test_id_splits_have_zero_friction(self):
        for split in ("train_id", "val_id", "test_id"):
            assert OOD_PARAMS[split]["joint_friction"] == 0.0
