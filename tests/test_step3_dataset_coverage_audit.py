from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

import pytest


def _load_audit_module() -> Any:
    path = Path(__file__).resolve().parents[1] / "scripts/audit_step3_dataset_coverage.py"
    spec = importlib.util.spec_from_file_location("step3_coverage_audit", path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


audit_module = _load_audit_module()


def _step(
    index: int,
    *,
    episode_id: str = "ep0",
    hypothesis_update_timestamp: int | None = None,
    recovery_timestamp: int | None = None,
    ood_type: str | None = None,
    selected_hypothesis_confidence: float | None = None,
    true_wrong_hypothesis: bool | None = None,
) -> dict[str, Any]:
    return {
        "step_id": f"{episode_id}_step_{index}",
        "episode_id": episode_id,
        "step_index": index,
        "eval_labels": {
            "hypothesis_update_timestamp": hypothesis_update_timestamp,
            "recovery_timestamp": recovery_timestamp,
            "ood_type": ood_type,
            "true_wrong_hypothesis": true_wrong_hypothesis,
        },
        "action": {"selected_hypothesis_confidence": selected_hypothesis_confidence},
    }


def _write_jsonl(data_root: Path, split: str, records: list[dict[str, Any]]) -> Path:
    data_root.mkdir(parents=True, exist_ok=True)
    path = data_root / f"{split}.jsonl"
    text = "\n".join(json.dumps(record) for record in records) + "\n"
    path.write_text(text, encoding="utf-8")
    return path


def test_audit_reports_zero_for_missing_hypothesis_update_timestamp(tmp_path: Path) -> None:
    data_root = tmp_path / "dataset"
    _write_jsonl(data_root, "train", [_step(0), _step(1)])

    report = audit_module.audit_coverage(data_root, "all")

    coverage = report["field_coverage"]["hypothesis_update_timestamp"]
    assert coverage["present"] == 0
    assert coverage["total"] == 2
    assert coverage["ratio"] == 0.0


def test_audit_reports_zero_for_missing_recovery_timestamp(tmp_path: Path) -> None:
    data_root = tmp_path / "dataset"
    _write_jsonl(data_root, "train", [_step(0), _step(1)])

    report = audit_module.audit_coverage(data_root, "all")

    coverage = report["field_coverage"]["recovery_timestamp"]
    assert coverage["present"] == 0
    assert coverage["total"] == 2
    assert coverage["ratio"] == 0.0


def test_audit_reports_zero_for_missing_selected_hypothesis_confidence(tmp_path: Path) -> None:
    data_root = tmp_path / "dataset"
    steps = [_step(0), _step(1)]
    for step in steps:
        step["action"].pop("selected_hypothesis_confidence")
    _write_jsonl(data_root, "train", steps)

    report = audit_module.audit_coverage(data_root, "all")

    coverage = report["field_coverage"]["selected_hypothesis_confidence"]
    assert coverage["present"] == 0
    assert coverage["total"] == 2
    assert coverage["ratio"] == 0.0


def test_audit_reports_correct_coverage_for_populated_synthetic(tmp_path: Path) -> None:
    data_root = tmp_path / "dataset"
    steps = [
        _step(
            index,
            episode_id=f"ep{index // 5}",
            hypothesis_update_timestamp=0 if index < 5 else None,
        )
        for index in range(10)
    ]
    _write_jsonl(data_root, "train", steps)

    report = audit_module.audit_coverage(data_root, "all")

    coverage = report["field_coverage"]["hypothesis_update_timestamp"]
    assert coverage["present"] == 5
    assert coverage["total"] == 10
    assert coverage["ratio"] == pytest.approx(0.5)
    assert report["total_episodes"] == 2


def test_audit_emits_json_with_expected_keys(tmp_path: Path) -> None:
    data_root = tmp_path / "dataset"
    out_path = tmp_path / "coverage.json"
    _write_jsonl(data_root, "valid", [_step(0, true_wrong_hypothesis=False)])

    exit_code = audit_module.main(
        ["--data-root", str(data_root), "--out", str(out_path), "--split", "valid"]
    )

    assert exit_code == 0
    report = json.loads(out_path.read_text(encoding="utf-8"))
    assert {"data_root", "total_steps", "total_episodes", "field_coverage"} <= set(report)
