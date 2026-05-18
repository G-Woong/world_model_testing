"""STEP 10 scaffold directory existence test.

Source: TASK_1110_step10_scaffold
Gate: O-CURRENT prerequisite
"""
import pathlib

import pytest

REQUIRED_DIRS = [
    "docs/orchestration/risk_hunt",
    "docs/orchestration/risk_hunt/literature",
    "docs/orchestration/risk_hunt/datasets",
    "docs/orchestration/risk_hunt/architecture",
    "docs/orchestration/risk_hunt/losses",
    "docs/orchestration/risk_hunt/evaluation",
    "docs/orchestration/risk_hunt/codex_tasks",
    "docs/orchestration/risk_hunt/loop_reports",
    "outputs/risk_hunt",
    "outputs/risk_hunt/audits",
    "outputs/risk_hunt/experiments",
    "outputs/risk_hunt/dataset_feasibility",
]

REPO_ROOT = pathlib.Path(__file__).parent.parent


@pytest.mark.parametrize("rel_path", REQUIRED_DIRS)
def test_risk_hunt_dir_exists(rel_path: str) -> None:
    assert (REPO_ROOT / rel_path).is_dir(), f"Missing directory: {rel_path}"
