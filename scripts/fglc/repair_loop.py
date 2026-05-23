"""CLI for the dry-run repair loop."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from fglc.repair.diagnose import CANONICAL_METRIC_KEYS
from fglc.repair.orchestrator import RepairLoopConfig, RunnerOutput, run_repair_loop


METRIC_DIRECTIONS = {
    "id_nll": "lower_better",
    "ood_auroc": "higher_better",
    "attention_entropy": "lower_better",
    "corrected_nll_gain": "higher_better",
    "planner_return_gain": "higher_better",
    "stagnant_epochs": "lower_better",
    "train_nll": "lower_better",
}


def _default_failed_metric(phase: str) -> str:
    return {
        "R2": "ood_auroc",
        "R3": "id_nll",
        "R4": "ood_auroc",
        "R5": "attention_entropy",
        "R6": "corrected_nll_gain",
        "R7": "planner_return_gain",
    }[phase]


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", required=True, choices=["R2", "R3", "R4", "R5", "R6", "R7"])
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--split", default="val", choices=["val", "test", "id", "ood"])
    parser.add_argument("--seed", default=0, type=int)
    parser.add_argument("--descriptor", required=True)
    parser.add_argument("--failed-metric", default=None)
    parser.add_argument("--max-iter", default=3, type=int)
    parser.add_argument("--max-wall-clock-minutes", default=60.0, type=float)
    parser.add_argument("--max-consecutive-inconclusive", default=2, type=int)
    parser.add_argument("--output-root", default=Path("outputs/repair"), type=Path)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--mock-scenario",
        default="improve",
        choices=[
            "improve",
            "reject",
            "inconclusive",
            "target_reached",
            "max_iter",
            "hook_blocked",
            "no_candidate",
        ],
    )
    return parser


def _build_config(ns) -> RepairLoopConfig:
    failed_metric = ns.failed_metric or _default_failed_metric(ns.phase)
    if failed_metric not in CANONICAL_METRIC_KEYS:
        raise ValueError(f"unknown metric for phase {ns.phase}: {failed_metric}")
    if failed_metric not in METRIC_DIRECTIONS:
        raise ValueError(f"unknown metric direction for phase {ns.phase}: {failed_metric}")
    return RepairLoopConfig(
        phase=ns.phase,
        config_path=ns.config,
        split=ns.split,
        seed=ns.seed,
        descriptor=ns.descriptor,
        max_iter=ns.max_iter,
        max_wall_clock_minutes=ns.max_wall_clock_minutes,
        max_consecutive_inconclusive=ns.max_consecutive_inconclusive,
        dry_run=ns.dry_run,
        output_root=ns.output_root,
        metric_directions=METRIC_DIRECTIONS,
        gate_thresholds={
            "id_nll": 0.4,
            "ood_auroc": 0.8,
            "attention_entropy": 0.1,
            "corrected_nll_gain": 0.1,
            "planner_return_gain": 0.1,
        },
        failed_metric=failed_metric,
    )


def build_mock_runner(scenario, *, failed_metric):
    del failed_metric

    def _metrics(iter_index: int) -> dict:
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

    def _runner(*, phase, config_path, split, seed, descriptor, patch, iter_index):
        del phase, config_path, split, seed, descriptor, patch
        if scenario == "hook_blocked" and iter_index == 0:
            return RunnerOutput(
                metrics={},
                wall_clock_minutes=0.0,
                vram_peak_mib=0.0,
                hook_blocked=True,
                hook_reason="test_hook",
            )
        return RunnerOutput(
            metrics=_metrics(iter_index),
            wall_clock_minutes=0.1,
            vram_peak_mib=100.0,
        )

    return _runner


def main(argv: list[str] | None = None) -> int:
    try:
        ns = _parser().parse_args(argv)
    except SystemExit as e:
        return int(e.code) if isinstance(e.code, int) else 2
    try:
        cfg = _build_config(ns)
        runner = build_mock_runner(ns.mock_scenario, failed_metric=cfg.failed_metric)
        results = run_repair_loop(cfg, runner=runner)
        final = results[-1]
        print(
            json.dumps(
                {
                    "loop_id": final.ledger_line["loop_id"],
                    "final_result": final.ledger_line["result"],
                    "stop_condition_hit": final.ledger_line["stop_condition_hit"],
                    "ledger_path": str(
                        cfg.output_root / final.ledger_line["loop_id"] / "ledger.jsonl"
                    ),
                    "next_action": final.ledger_line["next_action"],
                }
            )
        )
        return 0
    except ValueError as e:
        print(f"ERROR config: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"ERROR internal: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
