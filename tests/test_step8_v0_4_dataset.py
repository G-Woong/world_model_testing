from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_script(name: str, relative_path: str) -> Any:
    path = REPO_ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


audit_module = _load_script("step8_v04_coverage_audit", "scripts/audit_step8_dataset_coverage.py")
generator_module = _load_script("step8_v04_generator", "scripts/generate_v0_4_dataset.py")


def _step(effect_type: str, true_wrong_hypothesis: bool | None = False) -> dict[str, Any]:
    return {
        "step_id": "ep0_step_000",
        "episode_id": "ep0",
        "step_index": 0,
        "public_observation": {
            "instruction": "Find the result.",
            "history_public": [],
            "candidate_actions_public": [
                {"action_id": "wait", "action_type": "wait", "action_params": {}}
            ],
        },
        "observed_effect_public": {"effect_type": effect_type},
        "evaluation_labels": {"true_wrong_hypothesis": true_wrong_hypothesis},
    }


def _episode(
    effect_type: str,
    true_wrong_hypothesis: bool | None = False,
    episode_id: str = "ep0",
) -> dict[str, Any]:
    step = _step(effect_type, true_wrong_hypothesis)
    step["episode_id"] = episode_id
    return {"episode_id": episode_id, "steps": [step]}


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(record) + "\n" for record in records),
        encoding="utf-8",
    )


def test_coverage_audit_detects_missing_ood(tmp_path: Path) -> None:
    data_root = tmp_path / "dataset"
    _write_jsonl(
        data_root / "test_ood.jsonl",
        [
            _episode("state_change", False, "ep0"),
            _episode("delayed_effect", True, "ep1"),
        ],
    )

    report = audit_module.audit_dataset_coverage(data_root)

    assert report["ood_coverage_gate_pass"] is False
    assert report["ood_coverage_gate_status"].startswith("OOD_COVERAGE_GATE_FAIL_")
    assert "blocker_removed" in report["ood_coverage_gate_status"]


def test_leakage_audit_clean(tmp_path: Path) -> None:
    data_root = tmp_path / "dataset"
    _write_jsonl(data_root / "test_ood.jsonl", [_episode("blocker_removed", False)])

    report = audit_module.audit_dataset_coverage(
        data_root,
        gates={
            "blocker_removed_min": 1,
            "delayed_effect_min": 0,
            "true_wrong_both_classes": False,
        },
    )

    assert report["leakage_count"] == 0


def test_manifest_schema_fields() -> None:
    manifest = {
        "schema_version": "schema-06-v0.4",
        "total_episodes": 5000,
        "split_counts": {"train": 3500, "valid": 500, "test_id": 500, "test_ood": 500},
        "ood_effect_type_counts": {"blocker_removed": 50, "delayed_effect": 50},
        "coverage_gate_status": {"status": "OOD_COVERAGE_GATE_PASS", "pass": True},
        "sha256": {"train": "a", "valid": "b", "test_id": "c", "test_ood": "d"},
        "generator_version": "p3-text-v0.4",
        "seed": 84322,
        "timestamp": "2026-05-18T00:00:00+00:00",
    }

    assert generator_module.validate_manifest_schema(manifest) == []
