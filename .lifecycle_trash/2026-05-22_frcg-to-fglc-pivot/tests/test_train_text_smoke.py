"""Tests for P3 smoke training loop.

Source MD: paper_context_ref/11_MODEL_DATASET_SCALE_AND_TRAINING_BUDGET_v1.md
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

torch = pytest.importorskip("torch")

from frcgw.objectives.losses import LossDict, assert_no_objective_leakage
from frcgw.schemas.step_schema import CandidateAction, PublicObservation
from frcgw.schemas.visibility import HiddenLabelLeakageError
from frcgw.training.monitoring import PublicTraceLogger
from frcgw.training.train_text import run_smoke_train


LOSS_NAMES = {
    "l_action_effect",
    "l_progress",
    "l_regime",
    "l_control_grammar",
    "l_falsification",
    "l_intent_action_mapping",
    "l_change_point",
    "l_reveal_shift",
    "l_failed_action",
    "l_temporal_consistency",
}


@pytest.fixture(scope="module")
def smoke_output_dir(tmp_path_factory):
    """Run smoke train once, return output dir."""
    data_root = Path("data/frcgw_text/v0_1")
    if not (data_root / "manifest.json").exists():
        pytest.skip("P2 dataset not present")

    out = tmp_path_factory.mktemp("smoke_out")
    train_cfg = tmp_path_factory.mktemp("smoke_cfg") / "train_text.yaml"
    train_cfg.write_text(
        Path("configs/train_text.yaml")
        .read_text(encoding="utf-8")
        .replace("batch_size: 8", "batch_size: 4")
        .replace("max_steps: 80", "max_steps: 10")
        .replace("max_epochs: 2", "max_epochs: 1"),
        encoding="utf-8",
    )
    result = run_smoke_train(
        train_cfg_path=train_cfg,
        model_cfg_path=Path("configs/model_text.yaml"),
        output_dir=out,
    )
    return out, result


def test_smoke_train_completes(smoke_output_dir) -> None:
    out, result = smoke_output_dir
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["n_steps"] >= 1
    assert result.total_steps >= 1
    assert result.all_losses_finite is True


def test_loss_finite_throughout(smoke_output_dir) -> None:
    out, _ = smoke_output_dir
    for entry in _log_entries(out):
        for value in entry["losses"].values():
            assert isinstance(value, (int, float))
            assert math.isfinite(value)


def test_per_loss_curve_logged(smoke_output_dir) -> None:
    out, _ = smoke_output_dir
    for entry in _log_entries(out):
        assert LOSS_NAMES <= set(entry["losses"])


def test_grad_norm_logged(smoke_output_dir) -> None:
    out, _ = smoke_output_dir
    for entry in _log_entries(out):
        assert isinstance(entry["grad_norm"], (int, float))
        assert math.isfinite(entry["grad_norm"])


def test_checkpoint_written(smoke_output_dir) -> None:
    out, _ = smoke_output_dir
    assert (out / "checkpoint_ep0.pt").exists()


def test_manifest_written(smoke_output_dir) -> None:
    out, _ = smoke_output_dir
    manifest_path = out / "manifest.json"
    assert manifest_path.exists()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert {"seed", "n_steps", "n_epochs"} <= set(manifest)


def test_no_hidden_fields_in_batch() -> None:
    clean = [
        PublicObservation(
            instruction="search",
            candidate_actions_public=[CandidateAction("a0", "click", {})],
        )
    ]
    for public_input in clean:
        assert_no_objective_leakage(public_input)

    contaminated = PublicObservation(instruction="search", dom_snapshot_public={"true_regime": "search_form"})
    with pytest.raises(HiddenLabelLeakageError):
        assert_no_objective_leakage(contaminated)


def test_public_trace_logger(tmp_path) -> None:
    logger = PublicTraceLogger(tmp_path)
    try:
        for step in range(3):
            logger.log_step(step, 0, _mock_loss_dict(float(step + 1)), grad_norm=0.5)
    finally:
        logger.close()

    lines = (tmp_path / "training_log.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 3
    for line in lines:
        entry = json.loads(line)
        assert {"step", "epoch", "losses", "grad_norm"} <= set(entry)


def _log_entries(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in (path / "training_log.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _mock_loss_dict(value: float) -> LossDict:
    tensor = torch.tensor(value)
    return LossDict(
        l_action_effect=tensor,
        l_progress=tensor,
        l_regime=tensor,
        l_control_grammar=tensor,
        l_falsification=tensor,
        l_intent_action_mapping=tensor,
        l_change_point=tensor,
        l_reveal_shift=tensor,
        l_failed_action=tensor,
        l_temporal_consistency=tensor,
        l_seq_falsification=tensor,
        l_run_length_posterior=tensor,
        l_total=tensor,
        weights={},
    )
