"""Top-level entry: planner evaluation across (model × planner × split × seed).

사용 예:
    # debug smoke (Cursor-runnable)
    .\.venv\Scripts\python.exe scripts\evaluate_planners.py \
        --config configs\planner_eval_debug.yaml \
        --out-dir outputs\planner_eval_debug \
        --max-episodes 2

    # main (사용자가 PowerShell에서 직접 실행)
    .\.venv\Scripts\python.exe scripts\evaluate_planners.py \
        --config configs\planner_eval_main.yaml \
        --out-dir outputs\planner_eval_main

본 스크립트는:
- yaml을 PlannerEvalConfig로 로드
- PlannerEvalRunner.run() 호출
- 콘솔에 진행 요약 출력
- 결과 csv/jsonl/trace 저장 위치 출력
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from falsifiable_regime_world_model.planner import PlannerEvalConfig   # noqa: E402
from falsifiable_regime_world_model.eval import PlannerEvalRunner      # noqa: E402


def parse_args():
    p = argparse.ArgumentParser(
        description="Planner evaluation runner (Session 11-13)."
    )
    p.add_argument("--config", required=True, type=str, help="planner_eval_*.yaml")
    p.add_argument("--out-dir", required=True, type=str, help="결과 저장 디렉토리")
    p.add_argument("--max-episodes", type=int, default=None,
                   help="split별 num_episodes를 이 값으로 cap (smoke test용).")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    cfg = PlannerEvalConfig.from_yaml(args.config)
    print("=" * 78)
    print(f"[planner_eval] meta.name = {cfg.meta_name}")
    print(f"[planner_eval] config    = {args.config}")
    print(f"[planner_eval] out_dir   = {args.out_dir}")
    print(f"[planner_eval] models    = {[m.name for m in cfg.models]}")
    print(f"[planner_eval] planners  = {[p.name for p in cfg.planners]}")
    print(f"[planner_eval] splits    = {[s.name for s in cfg.splits]}")
    if args.max_episodes is not None:
        print(f"[planner_eval] max_episodes override = {args.max_episodes}")
    print("=" * 78)

    runner = PlannerEvalRunner(
        cfg, out_dir=args.out_dir,
        max_episodes_override=args.max_episodes,
    )
    t0 = time.time()
    res = runner.run()
    elapsed = time.time() - t0

    print("\n" + "=" * 78)
    print(f"[planner_eval] DONE in {elapsed:.1f}s")
    print(f"[planner_eval] n_episodes = {res['n_episodes']}")
    print(f"[planner_eval] outputs    = {res['out_dir']}")
    print("=" * 78)
    print("\nGenerated files:")
    out_dir = Path(args.out_dir)
    for fname in (
        "raw_episodes.jsonl",
        "metrics_by_episode.csv",
        "metrics_by_planner.csv",
        "metrics_by_split.csv",
        "aggregate_summary.csv",
        "config_resolved.yaml",
    ):
        p = out_dir / fname
        if p.exists():
            print(f"  - {p}")
    if (out_dir / "planner_traces").exists():
        print(f"  - {out_dir / 'planner_traces'}/  (per-episode jsonl)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
