"""Generate a markdown summary of planner_eval results.

input  : <summary_dir> (compare_planner_results.py output) or <out_dir> (raw)
output : <summary.md> (markdown 표 + 핵심 통찰)

사용 예:
    .\.venv\Scripts\python.exe scripts\summarize_planner_eval.py \
        --input outputs\planner_eval_main_summary \
        --out docs\PLANNER_EVAL_SUMMARY.md
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Any, Dict, List

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True, type=str,
                   help="planner_eval_*_summary 디렉토리 (compare_planner_results.py output)")
    p.add_argument("--out", required=True, type=str, help="출력 markdown 파일")
    return p.parse_args()


def _read_csv(path: Path) -> List[Dict[str, Any]]:
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8", newline="") as fp:
        return list(csv.DictReader(fp))


def _format_table(rows: List[Dict[str, Any]], cols: List[str]) -> str:
    if not rows:
        return "_(no rows)_\n"
    lines = ["| " + " | ".join(cols) + " |"]
    lines.append("|" + "|".join(["---"] * len(cols)) + "|")
    for r in rows:
        cells = []
        for c in cols:
            v = r.get(c, "")
            try:
                f = float(v)
                if abs(f) >= 1000 or (abs(f) > 0 and abs(f) < 0.001):
                    cells.append(f"{f:.3e}")
                else:
                    cells.append(f"{f:.3f}")
            except (TypeError, ValueError):
                cells.append(str(v))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    in_dir = Path(args.input)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    pc = _read_csv(in_dir / "planner_comparison_table.csv")
    map_t = _read_csv(in_dir / "model_ablation_planner_table.csv")
    ood = _read_csv(in_dir / "ood_breakdown_table.csv")
    cn = _read_csv(in_dir / "compute_normalized_table.csv")

    md = []
    md.append("# Planner Evaluation Summary")
    md.append("")
    md.append(f"input: `{in_dir}`")
    md.append("")

    md.append("## 1. Planner × Model 요약")
    md.append("")
    md.append(_format_table(pc, [
        "planner", "model", "n_episodes",
        "return_mean", "success_rate", "completed_mean",
        "planning_calls_mean", "rollout_steps_mean",
        "compute_normalized_return", "wrong_hypothesis_persistence_mean",
        "recovery_delay_after_change_mean", "false_planning_call_rate",
    ]))

    md.append("\n## 2. Model Ablation × Planner")
    md.append("")
    md.append(_format_table(map_t, [
        "planner", "model", "n_episodes",
        "return_mean", "success_rate",
        "compute_normalized_return",
        "wrong_hypothesis_persistence_mean",
        "recovery_delay_after_change_mean",
    ]))

    md.append("\n## 3. OOD breakdown")
    md.append("")
    md.append(_format_table(ood, [
        "split", "planner", "model", "n_episodes",
        "return_mean", "return_ci_lo", "return_ci_hi",
        "success_rate", "compute_normalized_return",
    ]))

    md.append("\n## 4. Compute frontier")
    md.append("")
    md.append(_format_table(cn, [
        "planner", "model", "return_mean", "planning_calls_mean",
        "rollout_steps_mean", "return_per_1k_rollout_steps",
        "compute_normalized_return",
    ]))

    md.append("\n## 5. 해석 가이드")
    md.append("")
    md.append("- 같은 planner를 model variant 간 비교: `full > no_regime` (특히 control-drift OOD에서)")
    md.append("- Ours(`ours_frc`) vs `always_plan`: compute_normalized_return에서 우위해야 함")
    md.append("- Ours vs `fixed_k`/`uncertainty_gate`/`adaptive_lookahead`: WHPT 감소 + recovery delay 감소")
    md.append("- `event_only` vs Ours: small drift OOD에서 Ours가 더 나아야 함")
    md.append("- 결과가 안 좋으면 paper-main 주장을 약화하거나 ablation으로 위치 조정 필요 (정직하게)")
    md.append("")

    out_path.write_text("\n".join(md), encoding="utf-8")
    print(f"[summary] wrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
