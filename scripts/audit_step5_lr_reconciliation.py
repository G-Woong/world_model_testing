"""audit_step5_lr_reconciliation - Compare trained planner F_t vs LR scorer F_t.

COMPARE-ONLY: Does not modify the active F_t path.
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
for import_root in (REPO_ROOT, SRC_ROOT):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from scripts import audit_step4_lr_comparison as step4_audit  # noqa: E402


DEFAULT_DATASET = "data/frcgw_text/v0_3/test_id.jsonl"
DEFAULT_CKPT_PATH = "outputs/checkpoints/pretrain_v0_3/checkpoint.pt"
DEFAULT_OUT = "outputs/audits/step5_lr_reconciliation.json"
STEP4_COMPARISON_PATH = "outputs/audits/step4_lr_comparison.json"


def _timestamp() -> str:
    return datetime.now(UTC).isoformat()


def _base_report(
    status: str,
    dataset_path: Path,
    ckpt_path: Path,
    *,
    n_episodes: int = 0,
    n_steps: int = 0,
    interpretation: str | None = None,
) -> dict[str, Any]:
    return {
        "status": status,
        "dataset": str(dataset_path),
        "ckpt_path": str(ckpt_path),
        "mean_abs_diff_trained": None,
        "degenerate_planner_rate_trained": None,
        "degenerate_lr_rate_trained": None,
        "interpretation": interpretation,
        "C3_claim_status": "PRELIMINARY"
        if interpretation == "DIVERGENCE_PERSISTS"
        else None,
        "step4_comparison_path": STEP4_COMPARISON_PATH,
        "n_episodes": n_episodes,
        "n_steps": n_steps,
        "timestamp": _timestamp(),
        "steps": [],
    }


def _write_report(report: dict[str, Any], out_path: Path) -> dict[str, Any]:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    return report


def _load_trained_agent(ckpt_path: Path) -> Any:
    from frcgw.evaluation.frcg_agent import TextFRCGModelAgent

    return TextFRCGModelAgent(ckpt_path=ckpt_path)


def _load_lr_components() -> tuple[dict[str, Any] | None, str | None]:
    return step4_audit._load_lr_components()


def _step_record_from_raw(
    step: dict[str, Any],
    episode_id: str,
    fallback_step_index: int,
) -> Any:
    return step4_audit._step_record_from_raw(step, episode_id, fallback_step_index)


def _lr_scorer_f_t(
    step_record: Any,
    lr_components: dict[str, Any] | None,
    lr_import_error: str | None,
) -> tuple[float, bool, str | None]:
    return step4_audit._lr_scorer_f_t(step_record, lr_components, lr_import_error)


def _planner_f_t_from_agent(agent: Any, obs: Any) -> float:
    agent.act(obs)
    return float(getattr(agent, "last_F_t", 0.0))


def _interpret(
    mean_abs_diff: float,
    degenerate_planner_rate: float,
    degenerate_lr_rate: float,
) -> str:
    if (
        mean_abs_diff < 0.1
        and degenerate_planner_rate < 0.1
        and degenerate_lr_rate < 0.1
    ):
        return "CONVERGED_AFTER_TRAINING"
    return "DIVERGENCE_PERSISTS"


def run_reconciliation(
    dataset_path: Path,
    ckpt_path: Path,
    out_path: Path,
    max_episodes: int,
) -> dict[str, Any]:
    if not dataset_path.exists():
        return _write_report(
            _base_report(
                "DATASET_NOT_FOUND",
                dataset_path,
                ckpt_path,
                interpretation="DATASET_NOT_FOUND",
            ),
            out_path,
        )

    if not ckpt_path.exists():
        return _write_report(
            _base_report(
                "CKPT_NOT_FOUND",
                dataset_path,
                ckpt_path,
                interpretation="CKPT_NOT_FOUND",
            ),
            out_path,
        )

    lr_components, lr_import_error = _load_lr_components()
    if lr_components is None:
        report = _base_report(
            "LR_SCORER_IMPORT_FAILED",
            dataset_path,
            ckpt_path,
            interpretation="BLOCKED_LR_SCORER_IMPORT_FAILED",
        )
        report["lr_scorer_error"] = lr_import_error
        return _write_report(report, out_path)

    episodes = step4_audit._load_episodes(dataset_path, max_episodes)
    agent = _load_trained_agent(ckpt_path)
    results: list[dict[str, Any]] = []

    for episode in episodes:
        if hasattr(agent, "reset"):
            agent.reset()
        episode_id = str(episode.get("episode_id", ""))
        for fallback_idx, raw_step in enumerate(episode.get("steps", [])):
            if not isinstance(raw_step, dict):
                continue
            step_record = _step_record_from_raw(raw_step, episode_id, fallback_idx)
            f_t_planner = _planner_f_t_from_agent(agent, step_record.public_observation)
            f_t_lr, lr_ok, lr_error = _lr_scorer_f_t(
                step_record,
                lr_components,
                lr_import_error,
            )
            row = {
                "episode_id": episode_id,
                "step_index": step_record.step_index,
                "F_t_planner": f_t_planner,
                "F_t_lr_scorer": f_t_lr,
                "abs_diff": abs(f_t_planner - f_t_lr),
                "degenerate_planner": f_t_planner == 0.0,
                "degenerate_lr": f_t_lr == 0.0,
                "lr_scorer_ok": lr_ok,
            }
            if lr_error:
                row["lr_error"] = lr_error
            results.append(row)

    if results:
        mean_abs_diff = sum(row["abs_diff"] for row in results) / len(results)
        degenerate_planner_rate = sum(
            1 for row in results if row["degenerate_planner"]
        ) / len(results)
        degenerate_lr_rate = sum(1 for row in results if row["degenerate_lr"]) / len(results)
    else:
        mean_abs_diff = 0.0
        degenerate_planner_rate = 1.0
        degenerate_lr_rate = 1.0

    interpretation = _interpret(
        mean_abs_diff,
        degenerate_planner_rate,
        degenerate_lr_rate,
    )
    report = _base_report(
        "OK",
        dataset_path,
        ckpt_path,
        n_episodes=len(episodes),
        n_steps=len(results),
        interpretation=interpretation,
    )
    report.update(
        {
            "mean_abs_diff_trained": mean_abs_diff,
            "degenerate_planner_rate_trained": degenerate_planner_rate,
            "degenerate_lr_rate_trained": degenerate_lr_rate,
            "C3_claim_status": "PRELIMINARY"
            if interpretation == "DIVERGENCE_PERSISTS"
            else "SUPPORTED",
            "steps": results,
        }
    )
    return _write_report(report, out_path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default=DEFAULT_DATASET)
    parser.add_argument("--ckpt-path", default=DEFAULT_CKPT_PATH)
    parser.add_argument("--out", default=DEFAULT_OUT)
    parser.add_argument("--max-episodes", type=int, default=5)
    args = parser.parse_args(argv)

    report = run_reconciliation(
        dataset_path=Path(args.dataset),
        ckpt_path=Path(args.ckpt_path),
        out_path=Path(args.out),
        max_episodes=args.max_episodes,
    )
    print(f"LR reconciliation report: {args.out}")
    print(f"  status: {report['status']}")
    print(f"  interpretation: {report['interpretation']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
