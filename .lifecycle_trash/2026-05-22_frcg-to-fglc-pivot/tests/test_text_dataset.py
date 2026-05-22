"""Tests for the P2 text dataset loader and leakage-safe collator."""
from __future__ import annotations

from dataclasses import fields
from pathlib import Path

import pytest

torch = pytest.importorskip("torch")

from frcgw.data.text_dataset import BatchTargets, TextStepDataset, build_dataloaders, collate_fn
from frcgw.schemas.step_schema import PublicObservation
from frcgw.schemas.visibility import (
    FORBIDDEN_AGENT_FIELDS,
    HiddenLabelLeakageError,
    _collect_field_names,
)


DATA_ROOT = Path("data/frcgw_text/v0_1")
MANIFEST = DATA_ROOT / "manifest.json"
SPLITS = ("train", "valid", "test_id")


@pytest.fixture(scope="module")
def dataset_root() -> Path:
    if not MANIFEST.exists():
        pytest.skip(f"P2 text dataset not present: {DATA_ROOT}")
    missing = [split for split in SPLITS if not (DATA_ROOT / f"{split}.jsonl").exists()]
    if missing:
        pytest.skip(f"P2 text dataset missing split shards: {missing}")
    return DATA_ROOT


def _first_batch(dataset_root: Path, split: str = "train") -> dict:
    dataset = TextStepDataset(dataset_root / f"{split}.jsonl")
    return collate_fn([dataset[0]])


def test_collator_returns_only_public_input(dataset_root: Path):
    batch = _first_batch(dataset_root)
    assert isinstance(batch["public_inputs"], list)
    assert all(isinstance(item, PublicObservation) for item in batch["public_inputs"])
    for public_input in batch["public_inputs"]:
        assert not (_collect_field_names(public_input) & FORBIDDEN_AGENT_FIELDS)


def test_forbidden_fields_absent(dataset_root: Path):
    sample = TextStepDataset(dataset_root / "train.jsonl")[0]
    public_names = _collect_field_names(sample.public_input)
    public_names.update(vars(sample.public_input).keys())
    assert set(FORBIDDEN_AGENT_FIELDS).isdisjoint(public_names)


def test_targets_contain_all_labels(dataset_root: Path):
    batch = _first_batch(dataset_root)
    target = batch["targets"][0]
    for name in (
        "true_regime",
        "true_control_grammar",
        "true_action_effect_type",
        "true_wrong_hypothesis",
        "h_exec_id",
        "progress_delta",
    ):
        assert hasattr(target, name)


def test_counterfactual_not_in_batch(dataset_root: Path):
    batch = _first_batch(dataset_root)
    forbidden = {"counterfactual_id", "counterfactual_effect_type", "is_oracle_best"}
    for target in batch["targets"]:
        assert forbidden.isdisjoint({field.name for field in fields(target)})


def test_batch_shape_consistent(dataset_root: Path):
    for split in SPLITS:
        batch = _first_batch(dataset_root, split)
        assert batch["public_inputs"]
        assert batch["targets"]
        assert batch["step_ids"]
        assert len(batch["public_inputs"]) == len(batch["targets"]) == len(batch["step_ids"])
        assert isinstance(batch["public_inputs"][0], PublicObservation)
        assert isinstance(batch["targets"][0], BatchTargets)
        assert isinstance(batch["step_ids"][0], str)


def test_assert_fires_on_leakage():
    public_input = PublicObservation(
        instruction="click",
        dom_snapshot_public={"true_regime": "hidden"},
    )
    target = BatchTargets(
        true_regime="r",
        true_control_grammar="g",
        true_change_point="none",
        true_reveal_vs_shift="reveal",
        true_action_effect_type="success",
        true_failed_action=False,
        failure_reason=None,
        progress_delta=0.0,
        recovery_action_id=None,
        valid_hypothesis_switch=None,
        true_wrong_hypothesis=None,
        h_exec_id=None,
        correct_hypothesis_id=None,
    )
    with pytest.raises(HiddenLabelLeakageError):
        collate_fn([type("Sample", (), {"public_input": public_input, "targets": target, "step_id": "s"})()])


def test_dataset_length_nonzero(dataset_root: Path):
    for split in SPLITS:
        assert len(TextStepDataset(dataset_root / f"{split}.jsonl")) > 0


def test_step_sample_has_step_id(dataset_root: Path):
    sample = TextStepDataset(dataset_root / "train.jsonl")[0]
    assert isinstance(sample.step_id, str)
    assert sample.step_id


def test_build_dataloaders(dataset_root: Path):
    train_dl, valid_dl, test_dl = build_dataloaders(dataset_root / "manifest.json", batch_size=2)
    assert next(iter(train_dl))["public_inputs"]
    assert next(iter(valid_dl))["public_inputs"]
    assert next(iter(test_dl))["public_inputs"]
