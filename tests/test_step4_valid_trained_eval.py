from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any


def _load_runner_module() -> Any:
    path = Path("scripts/10_run_lr_real_eval.py")
    spec = importlib.util.spec_from_file_location("lr_real_eval_runner_step4_b3", path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


lr_real = _load_runner_module()
_write_manifest = lr_real._write_manifest


def _dataset_audit() -> dict[str, Any]:
    return {
        "recovery_timestamp_coverage": 0,
        "hypothesis_update_timestamp_coverage": 0,
        "selected_hypothesis_confidence_coverage": 0,
        "counterfactual_coverage": 0,
        "ood_split_exists": False,
        "total_episodes_sampled": 0,
    }


def _metrics_payload() -> dict[str, Any]:
    return {
        "agents": {},
        "fake_metric_count": 0,
        "blocked_metric_count": 0,
        "C5_calibration_status": "NO_DATA",
    }


def _config(ckpt_path: str | None) -> dict[str, Any]:
    return {
        "dataset_path": "data/frcgw_text/v0_3/test_id.jsonl",
        "split": "test_id",
        "seeds": [0],
        "agents": [
            {
                "id": "FRCG-LR",
                "class": "TextFRCGModelAgent",
                "ckpt_path": ckpt_path,
            }
        ],
        "metrics": [],
        "forbidden_sources": [],
    }


def test_valid_trained_eval_false_without_ckpt(tmp_path: Path) -> None:
    manifest = _write_manifest(
        _config(None),
        tmp_path,
        _metrics_payload(),
        "none_read",
        _dataset_audit(),
        write=False,
    )

    assert manifest["valid_trained_eval"] is False


def test_valid_trained_eval_true_with_all_ckpts(tmp_path: Path) -> None:
    manifest = _write_manifest(
        _config("some/path.ckpt"),
        tmp_path,
        _metrics_payload(),
        "none_read",
        _dataset_audit(),
        write=False,
    )

    assert manifest["valid_trained_eval"] is True


def test_metrics_contains_valid_trained_eval(tmp_path: Path) -> None:
    manifest = _write_manifest(
        _config(None),
        tmp_path,
        _metrics_payload(),
        "none_read",
        _dataset_audit(),
        write=False,
    )

    assert "valid_trained_eval" in manifest


def test_hard_checks_requires_valid_trained_eval(tmp_path: Path) -> None:
    manifest = _write_manifest(
        _config(None),
        tmp_path,
        _metrics_payload(),
        "none_read",
        _dataset_audit(),
        write=False,
    )

    assert manifest["valid_trained_eval"] is False
    assert manifest["hard_checks_all_pass"] is False


def test_manifest_disclosure_fields_present(tmp_path: Path) -> None:
    manifest = _write_manifest(
        _config(None),
        tmp_path,
        _metrics_payload(),
        "none_read",
        _dataset_audit(),
        write=False,
    )

    for field in (
        "valid_trained_eval",
        "random_init_ok",
        "ckpt_paths_all_provided",
        "hard_checks_all_pass",
    ):
        assert field in manifest
