"""CLI entry point for real R3 smoke repair-loop runs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from fglc.repair.diagnose import CANONICAL_METRIC_KEYS
from fglc.repair.orchestrator import RepairLoopConfig, run_repair_loop
from fglc.runners import R3SmokeRunner
from scripts.fglc.repair_loop import METRIC_DIRECTIONS, _default_failed_metric


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", default="R3", choices=["R2", "R3", "R4", "R5", "R6", "R7"])
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--split", default="val", choices=["val", "test", "id", "ood"])
    parser.add_argument("--seed", default=0, type=int)
    parser.add_argument("--descriptor", required=True)
    parser.add_argument("--max-iter", default=3, type=int)
    parser.add_argument("--max-wall-clock-minutes", default=240.0, type=float)
    parser.add_argument("--output-root", default=Path("outputs/repair"), type=Path)
    parser.add_argument("--failed-metric", default=None)
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
        max_consecutive_inconclusive=2,
        dry_run=False,
        output_root=ns.output_root,
        metric_directions=METRIC_DIRECTIONS,
        gate_thresholds={
            "id_nll": 0.5,
            "ood_auroc": 0.8,
            "attention_entropy": 0.1,
            "corrected_nll_gain": 0.1,
            "planner_return_gain": 0.1,
        },
        failed_metric=failed_metric,
    )


def main(argv: list[str] | None = None) -> int:
    try:
        ns = _parser().parse_args(argv)
    except SystemExit as e:
        return int(e.code) if isinstance(e.code, int) else 2
    try:
        cfg = _build_config(ns)
        runner = R3SmokeRunner(ns.config, output_root=cfg.output_root)
        results = run_repair_loop(cfg, runner=runner)
        final = results[-1]
        print(
            json.dumps(
                {
                    "loop_id": final.ledger_line["loop_id"],
                    "final_result": final.ledger_line["result"],
                    "metrics_before": final.ledger_line["metrics_before"],
                    "metrics_after": final.ledger_line["metrics_after"],
                },
                sort_keys=True,
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
