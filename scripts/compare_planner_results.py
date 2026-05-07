"""Compare planner_eval outputs across (model × planner × split).

input  : <out_dir>/raw_episodes.jsonl + metrics_by_*.csv
output : <summary_dir>/planner_comparison_table.csv
        <summary_dir>/model_ablation_planner_table.csv
        <summary_dir>/ood_breakdown_table.csv
        <summary_dir>/compute_normalized_table.csv

사용 예:
    .\.venv\Scripts\python.exe scripts\compare_planner_results.py \
        --input outputs\planner_eval_main \
        --out-dir outputs\planner_eval_main_summary
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True, type=str, help="planner_eval out_dir")
    p.add_argument("--out-dir", required=True, type=str, help="summary dir")
    return p.parse_args()


def _read_csv(path: Path) -> List[Dict[str, Any]]:
    if not path.is_file():
        return []
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8", newline="") as fp:
        reader = csv.DictReader(fp)
        for row in reader:
            rows.append(row)
    return rows


def _write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    keys: List[str] = []
    seen = set()
    for r in rows:
        for k in r.keys():
            if k not in seen:
                seen.add(k)
                keys.append(k)
    with path.open("w", encoding="utf-8", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=keys, extrasaction="ignore")
        writer.writeheader()
        for r in rows:
            writer.writerow(r)


def _f(v: Any) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def main() -> int:
    args = parse_args()
    in_dir = Path(args.input)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    by_planner = _read_csv(in_dir / "metrics_by_planner.csv")
    by_split = _read_csv(in_dir / "metrics_by_split.csv")

    if not by_planner and not by_split:
        print(f"[compare] no metrics csv found in {in_dir}", file=sys.stderr)
        return 1

    # 1) planner_comparison_table: planner × model 단순 비교 (split aggregated)
    pc_rows = []
    for r in by_planner:
        pc_rows.append({
            "planner": r.get("planner"),
            "model": r.get("model"),
            "n_episodes": r.get("n_episodes"),
            "return_mean": _f(r.get("return_mean")),
            "return_ci_lo": _f(r.get("return_ci_lo")),
            "return_ci_hi": _f(r.get("return_ci_hi")),
            "success_rate": _f(r.get("success_rate")),
            "completed_mean": _f(r.get("completed_mean")),
            "planning_calls_mean": _f(r.get("planning_calls_mean")),
            "rollout_steps_mean": _f(r.get("rollout_steps_mean")),
            "compute_normalized_return": _f(r.get("compute_normalized_return")),
            "wrong_hypothesis_persistence_mean": _f(r.get("wrong_hypothesis_persistence_mean")),
            "recovery_delay_after_change_mean": _f(r.get("recovery_delay_after_change_mean")),
            "false_planning_call_rate": _f(r.get("false_planning_call_rate")),
            "mean_falsification_score": _f(r.get("mean_falsification_score")),
        })
    _write_csv(out_dir / "planner_comparison_table.csv", pc_rows)

    # 2) model_ablation_planner_table: 동일 planner를 model variant 간 비교
    by_pm: Dict[str, Dict[str, Dict[str, Any]]] = defaultdict(dict)
    for r in by_planner:
        by_pm[r.get("planner")][r.get("model")] = r
    map_rows = []
    for planner, by_model in by_pm.items():
        for model_name in ("full", "no_regime", "no_change_point"):
            r = by_model.get(model_name) or {}
            map_rows.append({
                "planner": planner,
                "model": model_name,
                "n_episodes": r.get("n_episodes"),
                "return_mean": _f(r.get("return_mean")),
                "success_rate": _f(r.get("success_rate")),
                "compute_normalized_return": _f(r.get("compute_normalized_return")),
                "wrong_hypothesis_persistence_mean": _f(r.get("wrong_hypothesis_persistence_mean")),
                "recovery_delay_after_change_mean": _f(r.get("recovery_delay_after_change_mean")),
            })
    _write_csv(out_dir / "model_ablation_planner_table.csv", map_rows)

    # 3) ood_breakdown_table: split별 separately
    ood_rows = []
    for r in by_split:
        ood_rows.append({
            "split": r.get("split"),
            "planner": r.get("planner"),
            "model": r.get("model"),
            "n_episodes": r.get("n_episodes"),
            "return_mean": _f(r.get("return_mean")),
            "return_ci_lo": _f(r.get("return_ci_lo")),
            "return_ci_hi": _f(r.get("return_ci_hi")),
            "success_rate": _f(r.get("success_rate")),
            "completed_mean": _f(r.get("completed_mean")),
            "planning_calls_mean": _f(r.get("planning_calls_mean")),
            "rollout_steps_mean": _f(r.get("rollout_steps_mean")),
            "compute_normalized_return": _f(r.get("compute_normalized_return")),
            "wrong_hypothesis_persistence_mean": _f(r.get("wrong_hypothesis_persistence_mean")),
            "recovery_delay_after_change_mean": _f(r.get("recovery_delay_after_change_mean")),
        })
    _write_csv(out_dir / "ood_breakdown_table.csv", ood_rows)

    # 4) compute_normalized_table: planner × model의 (return, compute, normalized) trio
    cn_rows = []
    for r in by_planner:
        plan_calls = _f(r.get("planning_calls_mean"))
        roll_steps = _f(r.get("rollout_steps_mean"))
        ret = _f(r.get("return_mean"))
        cn_rows.append({
            "planner": r.get("planner"),
            "model": r.get("model"),
            "return_mean": ret,
            "planning_calls_mean": plan_calls,
            "rollout_steps_mean": roll_steps,
            "return_per_planning_call": ret / max(1.0, plan_calls),
            "return_per_1k_rollout_steps": ret * 1000.0 / max(1.0, roll_steps),
            "success_per_1k_rollout_steps": _f(r.get("success_per_1k_imagined_steps")),
            "compute_normalized_return": _f(r.get("compute_normalized_return")),
        })
    _write_csv(out_dir / "compute_normalized_table.csv", cn_rows)

    # 5) figures dir placeholder
    (out_dir / "figures").mkdir(parents=True, exist_ok=True)

    # 6) summary.md placeholder (사용자가 채울 수 있는 골격)
    summary_md = out_dir / "summary.md"
    summary_md.write_text(
        f"""# Planner Comparison Summary

input directory: `{in_dir}`

## Tables
- `planner_comparison_table.csv` — planner × model aggregate
- `model_ablation_planner_table.csv` — same planner across model variants
- `ood_breakdown_table.csv` — per-(planner, model, split)
- `compute_normalized_table.csv` — return / compute frontier

## Suggested follow-up
- per-OOD success_rate plot (planner별)
- compute-normalized return scatter (planning_calls vs return)
- wrong_hypothesis_persistence vs success_rate scatter

본 파일은 `scripts/summarize_planner_eval.py`로 자동 갱신할 수 있다.
""",
        encoding="utf-8",
    )

    print(f"[compare] wrote summary tables to {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
