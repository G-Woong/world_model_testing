"""Risk register schema validation test.

Source: TASK_1112_step10_risk_register_validator
Gate: O-RISK prerequisite
"""
from __future__ import annotations

import json
import pathlib
import subprocess

import pytest

REPO_ROOT = pathlib.Path(__file__).parent.parent
REGISTER_PATH = REPO_ROOT / "docs" / "orchestration" / "risk_hunt" / "01_global_risk_register.md"


def test_register_file_exists() -> None:
    assert REGISTER_PATH.exists(), "01_global_risk_register.md not found"


def test_validator_runs() -> None:
    result = subprocess.run(
        ["python", "scripts/risk_hunt/validate_risk_register.py", "--dry-run"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["total_risks"] >= 50, f"Only {data['total_risks']} risks registered, need >= 50"
    assert data["schema_valid"], f"Schema invalid: {data.get('invalid_risks', [])[:5]}"


def test_gate_o_risk_pass() -> None:
    result = subprocess.run(
        ["python", "scripts/risk_hunt/validate_risk_register.py", "--dry-run"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["gate_o_risk_pass"], f"Gate O-RISK not passed: {data}"


def test_all_20_categories_present() -> None:
    result = subprocess.run(
        ["python", "scripts/risk_hunt/validate_risk_register.py", "--dry-run"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    expected_cats = {
        "CORE", "THR", "FORE", "PCG", "LAT", "REG", "DUP", "ENV", "OXE", "CF",
        "ARC", "LOSS", "LONG", "EVAL", "DTB", "FAI", "STAT", "REV", "NOV", "LEAK",
    }
    found_cats = set(data["category_counts"].keys())
    missing = expected_cats - found_cats
    assert not missing, f"Missing categories: {missing}"
