"""Smoke test for audit_current_state.py."""
from __future__ import annotations

import json
import pathlib
import subprocess

import pytest

REPO_ROOT = pathlib.Path(__file__).parent.parent


def test_audit_script_runs() -> None:
    result = subprocess.run(
        ["python", "scripts/risk_hunt/audit_current_state.py", "--dry-run"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr


def test_audit_json_schema() -> None:
    result = subprocess.run(
        ["python", "scripts/risk_hunt/audit_current_state.py", "--dry-run"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    required_keys = [
        "audit_timestamp",
        "sentinel_list",
        "pretrain_v0_4_long_manifest_exists",
        "abl001_checkpoint_exists",
        "abl003_checkpoint_exists",
        "last_known_leakage_count",
        "last_known_fake_metric_count",
    ]
    for k in required_keys:
        assert k in data, f"Missing key: {k}"
    assert data["last_known_leakage_count"] == 0
    assert data["last_known_fake_metric_count"] == 0


def test_existing_audit_json_schema() -> None:
    """If any audit JSON exists, validate its schema."""
    audits = list((REPO_ROOT / "outputs" / "risk_hunt" / "audits").glob("current_state_audit_*.json"))
    if not audits:
        pytest.skip("No audit JSON yet — run audit_current_state.py to generate")
    with open(sorted(audits)[-1]) as f:
        data = json.load(f)
    assert data["last_known_leakage_count"] == 0
    assert data["last_known_fake_metric_count"] == 0
