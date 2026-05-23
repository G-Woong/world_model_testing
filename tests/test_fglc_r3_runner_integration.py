import inspect
import json
import sys
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from fglc.repair.ledger import REQUIRED_KEYS
from fglc.repair.orchestrator import RepairLoopConfig, RunnerOutput, run_repair_loop
from fglc.runners import R3SmokeRunner
from scripts.fglc import repair_loop


def _small_config() -> dict:
    return {
        "phase": "R3",
        "seed": 42,
        "device": "cpu",
        "dataset": {
            "type": "synthetic_toy",
            "D_x": 8,
            "D_a": 4,
            "episode_len": 16,
            "n_episode_train": 8,
            "n_episode_val": 4,
            "n_episode_ood_mass": 4,
            "n_episode_ood_friction": 4,
            "ood_mass_scale": 2.0,
            "ood_friction_scale": 0.5,
            "sigma": 0.1,
        },
        "model": {
            "D_x": 8,
            "D_a": 4,
            "K": 2,
            "d": 8,
            "h_dim": 16,
            "encoder_hidden": 16,
            "dynamics_hidden": 16,
        },
        "trainer": {
            "batch_size": 4,
            "train_horizon": 8,
            "epochs": 1,
            "learning_rate": 3.0e-4,
            "optimizer": "adam",
            "loss_weights": {
                "lambda_reward": 1.0,
                "lambda_value": 1.0,
                "lambda_calibration": 0.0,
            },
        },
    }


def _tmp_config_path(tmp_path: Path) -> Path:
    path = tmp_path / "smoke.yaml"
    path.write_text(yaml.safe_dump(_small_config()), encoding="utf-8")
    return path


def _loop_cfg(tmp_path: Path, config_path: Path) -> RepairLoopConfig:
    return RepairLoopConfig(
        phase="R3",
        config_path=config_path,
        split="val",
        seed=0,
        descriptor="integration",
        max_iter=1,
        max_wall_clock_minutes=240.0,
        max_consecutive_inconclusive=2,
        dry_run=False,
        output_root=tmp_path / "repair",
        metric_directions={
            "id_nll": "lower_better",
            "ood_auroc": "higher_better",
            "stagnant_epochs": "lower_better",
        },
        gate_thresholds={"id_nll": 0.0},
        failed_metric="id_nll",
    )


def test_r3runner_protocol_signature():
    signature = inspect.signature(R3SmokeRunner.__call__)
    assert list(signature.parameters) == [
        "self",
        "phase",
        "config_path",
        "split",
        "seed",
        "descriptor",
        "patch",
        "iter_index",
    ]


def test_r3runner_one_call_cpu(tmp_path: Path):
    config_path = _tmp_config_path(tmp_path)
    runner = R3SmokeRunner(config_path, output_root=tmp_path / "runner")

    out = runner(
        phase="R3",
        config_path=config_path,
        split="val",
        seed=0,
        descriptor="one_call",
        patch=None,
        iter_index=0,
    )

    assert isinstance(out, RunnerOutput)
    assert "id_nll" in out.metrics
    assert out.wall_clock_minutes > 0.0
    assert (tmp_path / "runner" / "iter_0" / "metrics.json").exists()
    assert (tmp_path / "runner" / "iter_0" / "config.yaml").exists()


def test_repair_loop_one_iter_end_to_end(tmp_path: Path):
    config_path = _tmp_config_path(tmp_path)
    cfg = _loop_cfg(tmp_path, config_path)
    runner = R3SmokeRunner(config_path, output_root=tmp_path / "runner")

    results = run_repair_loop(cfg, runner=runner, git_sha_fn=lambda: "abc123")

    assert results
    ledger_path = next(cfg.output_root.glob("*/ledger.jsonl"))
    assert ledger_path.exists()
    records = [json.loads(line) for line in ledger_path.read_text(encoding="utf-8").splitlines()]
    assert len(records) == 1
    assert all(key in records[0] for key in REQUIRED_KEYS)


def test_ledger_required_keys_19(tmp_path: Path):
    config_path = _tmp_config_path(tmp_path)
    cfg = _loop_cfg(tmp_path, config_path)
    runner = R3SmokeRunner(config_path, output_root=tmp_path / "runner")

    run_repair_loop(cfg, runner=runner, git_sha_fn=lambda: "abc123")

    ledger_path = next(cfg.output_root.glob("*/ledger.jsonl"))
    record = json.loads(ledger_path.read_text(encoding="utf-8").splitlines()[0])
    assert len(REQUIRED_KEYS) == 19
    assert all(key in record for key in REQUIRED_KEYS)


def test_iter0_artifacts(tmp_path: Path):
    config_path = _tmp_config_path(tmp_path)
    cfg = _loop_cfg(tmp_path, config_path)
    runner = R3SmokeRunner(config_path, output_root=tmp_path / "runner")

    run_repair_loop(cfg, runner=runner, git_sha_fn=lambda: "abc123")

    loop_dir = next(cfg.output_root.glob("loop_*"))
    assert (loop_dir / "iter_0").is_dir()
    assert (loop_dir / "iter_0" / "compare.json").exists()
    assert (loop_dir / "iter_0" / "run_manifest.json").exists()


def test_mock_regression(tmp_path: Path):
    config_path = tmp_path / "smoke.yaml"
    config_path.write_text("phase: R3\n", encoding="utf-8")
    argv = [
        "--phase",
        "R3",
        "--config",
        str(config_path),
        "--descriptor",
        "mock",
        "--dry-run",
        "--mock-scenario",
        "improve",
        "--output-root",
        str(tmp_path / "out"),
    ]

    assert repair_loop.main(argv) == 0
