"""audit_step6_lr_reconciliation - 4-way comparison: ABL-016 vs FALSIFICATION_ENABLED × planner vs lr_scorer F_t.

COMPARE-ONLY: Does not modify any active F_t path.
Output: outputs/audits/step6_lr_reconciliation.json

Source: docs/orchestration/lr_alignment/26_step6_execution_plan.md §D.3
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
for _import_root in (REPO_ROOT, SRC_ROOT):
    if str(_import_root) not in sys.path:
        sys.path.insert(0, str(_import_root))

from scripts import audit_step4_lr_comparison as step4_audit  # noqa: E402
from scripts import audit_step5_lr_reconciliation as step5_audit  # noqa: E402

DEFAULT_ABL016_CKPT = "outputs/checkpoints/pretrain_v0_3/checkpoint_best.pt"
DEFAULT_FALSIFICATION_CKPT = "outputs/checkpoints/pretrain_v0_3_falsification/checkpoint_best.pt"
DEFAULT_DATASET = "data/frcgw_text/v0_3/test_id.jsonl"
DEFAULT_OUT = "outputs/audits/step6_lr_reconciliation.json"

# Immutable STEP 4/5 audit paths — must never be overwritten
_FORBIDDEN_OUT_PATHS = {
    "outputs/audits/step4_lr_comparison.json",
    "outputs/audits/step5_lr_reconciliation.json",
}
_DEGENERATE_THRESHOLD = 1e-6


def _timestamp() -> str:
    return datetime.now(UTC).isoformat()


def _f_t_stats(f_t_values: list[float]) -> dict[str, float | None]:
    if not f_t_values:
        return {"mean_f_t": None, "variance": None, "degenerate_rate": None}
    n = len(f_t_values)
    mean = sum(f_t_values) / n
    variance = sum((x - mean) ** 2 for x in f_t_values) / n
    degenerate_rate = sum(1 for x in f_t_values if abs(x) < _DEGENERATE_THRESHOLD) / n
    return {"mean_f_t": mean, "variance": variance, "degenerate_rate": degenerate_rate}


def _mean_abs_diff(a: list[float], b: list[float]) -> float | None:
    paired = [(x, y) for x, y in zip(a, b)]
    if not paired:
        return None
    return sum(abs(x - y) for x, y in paired) / len(paired)


def _delta(a_mean: float | None, b_mean: float | None) -> float | None:
    if a_mean is None or b_mean is None:
        return None
    return b_mean - a_mean


def _swap_decision(
    falsification_planner_stats: dict,
    falsification_lr_stats: dict,
    diff_falsification: float | None,
) -> str:
    if diff_falsification is None:
        return "INCONCLUSIVE"
    fp_degen = falsification_planner_stats.get("degenerate_rate")
    fl_degen = falsification_lr_stats.get("degenerate_rate")
    if fp_degen is None or fl_degen is None:
        return "INCONCLUSIVE"
    if (
        diff_falsification < 0.1
        and fp_degen < 0.1
        and fl_degen < 0.1
    ):
        return "READY_FOR_SWAP"
    return "PERSIST_DUAL_TRACE"


def _c3_claim_readiness(
    blocked_reasons: list[str],
    falsification_planner_stats: dict,
    falsification_lr_stats: dict,
) -> str:
    if blocked_reasons:
        return "BLOCKED"
    fp_degen = falsification_planner_stats.get("degenerate_rate")
    fp_mean = falsification_planner_stats.get("mean_f_t")
    if fp_degen is None or fp_mean is None:
        return "BLOCKED"
    if fp_degen >= 1.0:
        return "BLOCKED"
    # PRELIMINARY is the max for STEP 6; READY_FOR_REPORT reserved for STEP 7
    return "PRELIMINARY"


def _collect_f_t_values(
    episodes: list[dict[str, Any]],
    agent: Any,
    lr_components: dict[str, Any] | None,
    lr_import_error: str | None,
) -> tuple[list[float], list[float]]:
    """Return (planner_f_t_values, lr_scorer_f_t_values) for all steps."""
    planner_vals: list[float] = []
    lr_vals: list[float] = []

    for episode in episodes:
        if hasattr(agent, "reset"):
            agent.reset()
        episode_id = str(episode.get("episode_id", ""))
        for fallback_idx, raw_step in enumerate(episode.get("steps", [])):
            if not isinstance(raw_step, dict):
                continue
            step_record = step5_audit._step_record_from_raw(raw_step, episode_id, fallback_idx)

            # Planner F_t: uses agent.act() which internally calls text_frcg_plan()
            # LEAKAGE PREVENTION: only PublicObservation is passed to agent.act()
            f_t_planner = step5_audit._planner_f_t_from_agent(agent, step_record.public_observation)
            planner_vals.append(f_t_planner)

            # LR scorer F_t: rule-based, no forbidden fields
            f_t_lr, _lr_ok, _lr_err = step5_audit._lr_scorer_f_t(step_record, lr_components, lr_import_error)
            lr_vals.append(f_t_lr)

    return planner_vals, lr_vals


def run_reconciliation(
    abl016_ckpt_path: Path,
    falsification_ckpt_path: Path,
    dataset_path: Path,
    out_path: Path,
    max_episodes: int = 10,
) -> dict[str, Any]:
    # Safety: never overwrite STEP 4/5 audits
    out_str = str(out_path).replace("\\", "/")
    for forbidden in _FORBIDDEN_OUT_PATHS:
        if out_str.endswith(forbidden) or out_str == forbidden:
            raise ValueError(
                f"Output path {out_path!r} matches forbidden STEP 4/5 audit path: {forbidden}"
            )
    if "step6" not in str(out_path):
        raise ValueError(
            f"Output path must contain 'step6' to prevent accidental overwrite: {out_path}"
        )

    blocked_reasons: list[str] = []

    if not dataset_path.exists():
        blocked_reasons.append(f"DATASET_NOT_FOUND: {dataset_path}")
    if not abl016_ckpt_path.exists():
        blocked_reasons.append(f"CKPT_ABL016_NOT_FOUND: {abl016_ckpt_path}")
    if not falsification_ckpt_path.exists():
        blocked_reasons.append(f"CKPT_FALSIFICATION_NOT_FOUND: {falsification_ckpt_path}")

    base = {
        "timestamp": _timestamp(),
        "abl016_checkpoint": str(abl016_ckpt_path),
        "falsification_checkpoint": str(falsification_ckpt_path),
        "dataset": str(dataset_path),
        "n_episodes_evaluated": 0,
        "n_steps_evaluated": 0,
        "abl016_planner": {"mean_f_t": None, "variance": None, "degenerate_rate": None},
        "abl016_lr_scorer": {"mean_f_t": None, "variance": None, "degenerate_rate": None},
        "falsification_planner": {"mean_f_t": None, "variance": None, "degenerate_rate": None},
        "falsification_lr_scorer": {"mean_f_t": None, "variance": None, "degenerate_rate": None},
        "mean_abs_diff_planner_vs_lr_abl016": None,
        "mean_abs_diff_planner_vs_lr_falsification": None,
        "delta_falsification_vs_abl016": {"planner": None, "lr_scorer": None},
        "active_path_swap_decision": "INCONCLUSIVE",
        "c3_claim_readiness": "BLOCKED",
        "blocked_reasons": blocked_reasons,
        "step4_audit_path": "outputs/audits/step4_lr_comparison.json",
        "step5_audit_path": "outputs/audits/step5_lr_reconciliation.json",
    }

    if blocked_reasons:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(base, indent=2, sort_keys=True), encoding="utf-8")
        return base

    lr_components, lr_import_error = step5_audit._load_lr_components()
    if lr_components is None:
        blocked_reasons.append(f"LR_SCORER_IMPORT_FAILED: {lr_import_error}")
        base["blocked_reasons"] = blocked_reasons
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(base, indent=2, sort_keys=True), encoding="utf-8")
        return base

    episodes = step4_audit._load_episodes(dataset_path, max_episodes)

    # Load agents for each checkpoint
    abl016_agent = step5_audit._load_trained_agent(abl016_ckpt_path)
    falsification_agent = step5_audit._load_trained_agent(falsification_ckpt_path)

    # Collect F_t values for both checkpoints
    abl016_planner_vals, abl016_lr_vals = _collect_f_t_values(
        episodes, abl016_agent, lr_components, lr_import_error
    )
    falsification_planner_vals, falsification_lr_vals = _collect_f_t_values(
        episodes, falsification_agent, lr_components, lr_import_error
    )

    n_steps = len(abl016_planner_vals)

    abl016_planner_stats = _f_t_stats(abl016_planner_vals)
    abl016_lr_stats = _f_t_stats(abl016_lr_vals)
    falsification_planner_stats = _f_t_stats(falsification_planner_vals)
    falsification_lr_stats = _f_t_stats(falsification_lr_vals)

    diff_abl016 = _mean_abs_diff(abl016_planner_vals, abl016_lr_vals)
    diff_falsification = _mean_abs_diff(falsification_planner_vals, falsification_lr_vals)

    delta_planner = _delta(
        abl016_planner_stats.get("mean_f_t"),
        falsification_planner_stats.get("mean_f_t"),
    )
    delta_lr = _delta(
        abl016_lr_stats.get("mean_f_t"),
        falsification_lr_stats.get("mean_f_t"),
    )

    swap_decision = _swap_decision(falsification_planner_stats, falsification_lr_stats, diff_falsification)
    c3_readiness = _c3_claim_readiness(blocked_reasons, falsification_planner_stats, falsification_lr_stats)

    report = {
        **base,
        "n_episodes_evaluated": len(episodes),
        "n_steps_evaluated": n_steps,
        "abl016_planner": abl016_planner_stats,
        "abl016_lr_scorer": abl016_lr_stats,
        "falsification_planner": falsification_planner_stats,
        "falsification_lr_scorer": falsification_lr_stats,
        "mean_abs_diff_planner_vs_lr_abl016": diff_abl016,
        "mean_abs_diff_planner_vs_lr_falsification": diff_falsification,
        "delta_falsification_vs_abl016": {"planner": delta_planner, "lr_scorer": delta_lr},
        "active_path_swap_decision": swap_decision,
        "c3_claim_readiness": c3_readiness,
        "blocked_reasons": blocked_reasons,
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="STEP 6 LR reconciliation: 4-way ABL-016 vs FALSIFICATION_ENABLED comparison"
    )
    parser.add_argument("--abl016-checkpoint", default=DEFAULT_ABL016_CKPT)
    parser.add_argument("--falsification-checkpoint", default=DEFAULT_FALSIFICATION_CKPT)
    parser.add_argument("--dataset", default=DEFAULT_DATASET)
    parser.add_argument("--out", default=DEFAULT_OUT)
    parser.add_argument("--max-episodes", type=int, default=10)
    args = parser.parse_args(argv)

    report = run_reconciliation(
        abl016_ckpt_path=Path(args.abl016_checkpoint),
        falsification_ckpt_path=Path(args.falsification_checkpoint),
        dataset_path=Path(args.dataset),
        out_path=Path(args.out),
        max_episodes=args.max_episodes,
    )
    print(f"STEP 6 LR reconciliation: {args.out}")
    print(f"  c3_claim_readiness: {report['c3_claim_readiness']}")
    print(f"  active_path_swap_decision: {report['active_path_swap_decision']}")
    if report.get("blocked_reasons"):
        for reason in report["blocked_reasons"]:
            print(f"  BLOCKED: {reason}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
