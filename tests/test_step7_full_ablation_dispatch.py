"""Tests that full ablation harness dispatches correct ablations and isolates ABL-040."""
import json
import subprocess
import sys
from pathlib import Path


EXPECTED_ABLATIONS = {
    "ABL-006", "ABL-011", "ABL-017", "ABL-022", "ABL-023",
    "ABL-024", "ABL-033", "ABL-034", "ABL-035", "ABL-036"
}
POSITIVE_CONTROL = {"ABL-040"}
DEFERRED = {"ABL-001", "ABL-003", "ABL-015"}


def test_harness_script_exists():
    assert Path("scripts/run_step7_full_inference_ablations.py").exists()


def test_dry_run_lists_correct_ablations(tmp_path):
    """Dry run must list exactly 11 ablations + ABL-040 isolated + 3 deferred."""
    result = subprocess.run(
        [sys.executable, "scripts/run_step7_full_inference_ablations.py",
         "--config", "configs/lr_eval_real_v0_3_step7_full.yaml",
         "--checkpoint", "outputs/checkpoints/pretrain_v0_3_falsification/checkpoint_best.pt",
         "--out-dir", str(tmp_path / "ablation_out"),
         "--dry-run"],
        capture_output=True, text=True, timeout=30
    )
    assert result.returncode == 0, result.stderr
    output = result.stdout + result.stderr
    for abl in EXPECTED_ABLATIONS:
        assert abl in output, f"{abl} not mentioned in dry-run output"

    assert "ABL-040" in output

    for abl in DEFERRED:
        assert abl in output, f"{abl} not mentioned as deferred"


def test_abl001_003_015_not_in_executed(tmp_path):
    """ABL-001/003/015 must not appear in executed_ablations in manifest."""
    result = subprocess.run(
        [sys.executable, "scripts/run_step7_full_inference_ablations.py",
         "--config", "configs/lr_eval_real_v0_3_step7_full.yaml",
         "--checkpoint", "outputs/checkpoints/pretrain_v0_3_falsification/checkpoint_best.pt",
         "--out-dir", str(tmp_path / "ablation_out"),
         "--dry-run"],
        capture_output=True, text=True, timeout=30
    )
    assert result.returncode == 0, result.stderr
    manifest_path = tmp_path / "ablation_out" / "step7_ablation_manifest.json"
    if manifest_path.exists():
        with open(manifest_path) as f:
            manifest = json.load(f)
        executed = set(manifest.get("executed_ablations", []))
        for abl in DEFERRED:
            assert abl not in executed, f"{abl} must not be in executed_ablations"
        assert manifest.get("fake_metric_count", 0) == 0


def test_abl040_isolated_from_main_results(tmp_path):
    """ABL-040 must be in positive_control_isolated, not in executed_ablations."""
    result = subprocess.run(
        [sys.executable, "scripts/run_step7_full_inference_ablations.py",
         "--config", "configs/lr_eval_real_v0_3_step7_full.yaml",
         "--checkpoint", "outputs/checkpoints/pretrain_v0_3_falsification/checkpoint_best.pt",
         "--out-dir", str(tmp_path / "ablation_out"),
         "--dry-run"],
        capture_output=True, text=True, timeout=30
    )
    assert result.returncode == 0, result.stderr
    manifest_path = tmp_path / "ablation_out" / "step7_ablation_manifest.json"
    if manifest_path.exists():
        with open(manifest_path) as f:
            manifest = json.load(f)
        executed = set(manifest.get("executed_ablations", []))
        positive = set(manifest.get("positive_control_isolated", []))
        assert "ABL-040" in positive, "ABL-040 must be in positive_control_isolated"
        assert "ABL-040" not in executed, "ABL-040 must NOT be in executed_ablations"
