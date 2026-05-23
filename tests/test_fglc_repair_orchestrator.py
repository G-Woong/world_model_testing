import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from fglc.repair.ledger import REQUIRED_KEYS, validate_ledger_line
from fglc.repair.orchestrator import RepairLoopConfig, RunnerOutput, run_repair_loop


def _cfg(tmp_path, **overrides):
    values = {
        "phase": "R3",
        "config_path": tmp_path / "missing.yaml",
        "split": "val",
        "seed": 0,
        "descriptor": "smoke",
        "max_iter": 2,
        "max_wall_clock_minutes": 60.0,
        "max_consecutive_inconclusive": 2,
        "dry_run": True,
        "output_root": tmp_path / "repair_subdir",
        "metric_directions": {
            "id_nll": "lower_better",
            "ood_auroc": "higher_better",
            "stagnant_epochs": "lower_better",
        },
        "gate_thresholds": {"id_nll": 0.0},
        "failed_metric": "id_nll",
    }
    values.update(overrides)
    return RepairLoopConfig(**values)


def _runner(scenario, wall_clock=0.1):
    def _metrics(iter_index):
        if scenario == "target_reached":
            return {"id_nll": 0.30, "ood_auroc": 0.90, "stagnant_epochs": 12.0}
        if scenario == "no_candidate":
            return {"id_nll": 0.45, "ood_auroc": 0.90}
        if scenario == "reject":
            if iter_index == 0:
                return {"id_nll": 0.80, "ood_auroc": 0.70, "stagnant_epochs": 12.0}
            return {"id_nll": 0.82, "ood_auroc": 0.68, "stagnant_epochs": 12.0}
        if scenario == "inconclusive":
            if iter_index == 0:
                return {"id_nll": 0.80, "ood_auroc": 0.70, "stagnant_epochs": 12.0}
            return {
                "id_nll": 0.80 - (iter_index * 0.01),
                "ood_auroc": 0.70,
                "stagnant_epochs": 12.0,
            }
        if scenario == "max_iter":
            return {"id_nll": 0.80, "ood_auroc": 0.70, "stagnant_epochs": 12.0}
        if iter_index == 0:
            return {"id_nll": 0.80, "ood_auroc": 0.70, "stagnant_epochs": 12.0}
        return {"id_nll": 0.70, "ood_auroc": 0.75, "stagnant_epochs": 12.0}

    def run(*, phase, config_path, split, seed, descriptor, patch, iter_index):
        del phase, config_path, split, seed, descriptor, patch
        if scenario == "hook_blocked" and iter_index == 0:
            return RunnerOutput({}, 0.0, 0.0, hook_blocked=True, hook_reason="test_hook")
        return RunnerOutput(_metrics(iter_index), wall_clock, 100.0)

    return run


def _records(output_root):
    ledger_path = next(output_root.glob("*/ledger.jsonl"))
    return [json.loads(line) for line in ledger_path.read_text(encoding="utf-8").splitlines()]


def _assert_valid(line):
    validate_ledger_line(line)
    assert all(key in line for key in REQUIRED_KEYS)


def test_improve_scenario(tmp_path):
    cfg = _cfg(tmp_path, gate_thresholds={"id_nll": 0.70})
    results = run_repair_loop(cfg, runner=_runner("improve"), git_sha_fn=lambda: "abc123")

    assert results[-1].ledger_line["result"] == "accept"
    assert (tmp_path / "repair_subdir").exists()
    records = _records(tmp_path / "repair_subdir")
    assert len(records) == 2
    for line in records:
        _assert_valid(line)


def test_reject_scenario(tmp_path):
    cfg = _cfg(tmp_path, max_iter=1)
    results = run_repair_loop(cfg, runner=_runner("reject"), git_sha_fn=lambda: "abc123")

    assert results[0].ledger_line["result"] == "reject"


def test_inconclusive_then_consecutive_stop(tmp_path):
    cfg = _cfg(tmp_path, max_consecutive_inconclusive=2, max_iter=5)
    results = run_repair_loop(cfg, runner=_runner("inconclusive"), git_sha_fn=lambda: "abc123")

    assert results[-1].stop_condition_hit == "consecutive_inconclusive"
    assert results[-1].ledger_line["result"] == "inconclusive"


def test_target_reached_at_iter_start(tmp_path):
    cfg = _cfg(
        tmp_path,
        gate_thresholds={"id_nll": 0.40},
        metric_directions={
            "id_nll": "lower_better",
            "ood_auroc": "higher_better",
            "stagnant_epochs": "lower_better",
        },
    )
    results = run_repair_loop(
        cfg,
        runner=_runner("target_reached"),
        git_sha_fn=lambda: "abc123",
    )

    assert results[0].stop_condition_hit == "target_reached"
    assert results[0].ledger_line["result"] == "accept"
    assert results[0].ledger_line["next_action"] == "stop_target_reached"


def test_max_iter(tmp_path):
    cfg = _cfg(tmp_path, max_iter=2)
    results = run_repair_loop(cfg, runner=_runner("max_iter"), git_sha_fn=lambda: "abc123")

    assert results[-1].stop_condition_hit == "max_iter"
    assert len(results) == 2


def test_hook_blocked_baseline(tmp_path):
    cfg = _cfg(tmp_path)
    results = run_repair_loop(cfg, runner=_runner("hook_blocked"), git_sha_fn=lambda: "abc123")

    assert len(results) == 1
    assert results[0].ledger_line["iter"] == 0
    assert results[0].ledger_line["result"] == "inconclusive"
    assert results[0].ledger_line["stop_condition_hit"] == "hook_blocked"
    assert results[0].ledger_line["candidate_chosen"]["id"] is None
    validate_ledger_line(results[0].ledger_line)


def test_no_candidate_sentinel_only(tmp_path):
    cfg = _cfg(tmp_path)
    results = run_repair_loop(cfg, runner=_runner("no_candidate"), git_sha_fn=lambda: "abc123")

    assert results[0].chosen_candidate is None
    assert results[0].ledger_line["result"] == "inconclusive"
    assert results[0].ledger_line["stop_condition_hit"] == "hook_blocked"
    assert results[0].ledger_line["next_action"] == "escalate_to_user"
    validate_ledger_line(results[0].ledger_line)


def test_wall_clock_stop(tmp_path):
    cfg = _cfg(tmp_path, max_wall_clock_minutes=0.001, max_iter=5)
    results = run_repair_loop(
        cfg,
        runner=_runner("improve", wall_clock=1.0),
        git_sha_fn=lambda: "abc123",
    )

    assert results[-1].stop_condition_hit == "wall_clock"
    validate_ledger_line(results[-1].ledger_line)
