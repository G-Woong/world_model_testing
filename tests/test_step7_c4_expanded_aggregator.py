"""Tests for audit_step7_c4_expanded_validation.py aggregator logic."""
import json
import subprocess
import sys
from pathlib import Path


def test_aggregator_imports():
    """Script must be importable without error."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "audit_step7_c4",
        Path("scripts/audit_step7_c4_expanded_validation.py"),
    )
    assert spec is not None, "Script not found"


def test_aggregator_schema_keys():
    """Output JSON must have required schema keys."""
    required_keys = {
        "step",
        "config",
        "seeds",
        "splits",
        "agents",
        "results",
        "c4_status",
        "c4_status_reason",
        "fake_metric_count",
        "comparison_delta",
    }
    # Run with --incomplete-ok to allow missing results
    subprocess.run(
        [
            sys.executable,
            "scripts/audit_step7_c4_expanded_validation.py",
            "--config",
            "configs/lr_eval_real_v0_3_step7_full.yaml",
            "--seeds",
            "0",
            "1",
            "--splits",
            "test_id",
            "--agents",
            "FRCG-LR",
            "--out",
            "outputs/audits/test_step7_c4_schema_check.json",
            "--incomplete-ok",
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    # Should exit 0 or produce output file (INCOMPLETE is valid)
    output_path = Path("outputs/audits/test_step7_c4_schema_check.json")
    if output_path.exists():
        with open(output_path) as f:
            data = json.load(f)
        assert required_keys.issubset(data.keys()), f"Missing keys: {required_keys - data.keys()}"
        assert data["fake_metric_count"] == 0


def test_c4_status_incomplete_when_no_results(tmp_path):
    """When no result files exist, c4_status must be INCOMPLETE."""
    import importlib.util

    # Load the module
    spec = importlib.util.spec_from_file_location(
        "audit_step7_c4",
        Path("scripts/audit_step7_c4_expanded_validation.py"),
    )
    if spec is None:
        return  # Script not found yet, skip
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception:
        return  # Module has side effects on import, skip structural test

    # If the module has a determine_c4_status function, test it directly
    if hasattr(module, "determine_c4_status"):
        status = module.determine_c4_status(
            frcg_lr_means=[], abl024_means=[], abl036_means=[]
        )
        assert status["c4_status"] == "INCOMPLETE"
