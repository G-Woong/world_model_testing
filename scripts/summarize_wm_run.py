"""Summarize a WM training run directory.

train_log.jsonl + valid_log.jsonl을 읽고, 최신 metric / best metric / loss curve를
markdown 요약 파일로 만든다. 학습 중에 / 학습 종료 후 모두 호출 가능하다.

사용:
    python scripts\\summarize_wm_run.py --run-dir outputs/wm_runs/<run_name>
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.is_file():
        return []
    out: List[Dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except Exception:    # noqa: BLE001
            continue
    return out


def _last(records: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    return records[-1] if records else None


def _best_min(records: List[Dict[str, Any]], key: str) -> Optional[Dict[str, Any]]:
    best = None
    for r in records:
        v = r.get(key)
        if v is None:
            continue
        if best is None or float(v) < float(best.get(key)):
            best = r
    return best


def _best_max(records: List[Dict[str, Any]], key: str) -> Optional[Dict[str, Any]]:
    best = None
    for r in records:
        v = r.get(key)
        if v is None:
            continue
        if best is None or float(v) > float(best.get(key)):
            best = r
    return best


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=str, required=True)
    args = parser.parse_args()

    run_dir = Path(args.run_dir)
    if not run_dir.is_dir():
        print(f"[summary] run_dir not found: {run_dir}")
        return 1

    train_log = _read_jsonl(run_dir / "train_log.jsonl")
    valid_log = _read_jsonl(run_dir / "valid_log.jsonl")

    last_train = _last(train_log)
    last_valid = _last(valid_log)
    best_uniform = _best_min(valid_log, "valid_uniform/loss/total")
    best_event_cp_f1 = _best_max(valid_log, "valid_event/change_point/f1")

    md_lines: List[str] = []
    md_lines.append(f"# Run summary: `{run_dir.name}`\n")
    md_lines.append(f"- run_dir: `{run_dir}`")
    md_lines.append(f"- train_log entries: {len(train_log)}")
    md_lines.append(f"- valid_log entries: {len(valid_log)}\n")

    if last_train is not None:
        md_lines.append("## Last train step")
        md_lines.append(f"- step: {last_train.get('global_step')}")
        md_lines.append(f"- stage: {last_train.get('stage')}")
        md_lines.append(f"- lr: {last_train.get('lr')}")
        md_lines.append(f"- precision: {last_train.get('precision')}")
        loss = last_train.get("loss") or {}
        md_lines.append(f"- loss.total: {loss.get('total')}")
        md_lines.append(f"- loss.change_point: {loss.get('change_point')}")
        md_lines.append(f"- loss.kl: {loss.get('kl')}")
        md_lines.append(f"- grad_norm: {last_train.get('grad_norm')}")
        md_lines.append(f"- step_time: {last_train.get('step_time_sec')}\n")

    if last_valid is not None:
        md_lines.append("## Last valid")
        md_lines.append(f"- step: {last_valid.get('global_step')}")
        for k in (
            "valid_uniform/loss/total",
            "valid_event/loss/total",
            "valid_uniform/reward/mse",
            "valid_uniform/state/mse",
            "valid_uniform/regime/accuracy",
            "valid_event/change_point/f1",
            "valid_event/change_point/precision",
            "valid_event/change_point/recall",
            "valid_event/shift/f1",
            "valid_event/reveal/f1",
            "valid_event/raw_eff_mismatch/f1",
        ):
            if k in last_valid:
                md_lines.append(f"- {k}: {last_valid[k]}")
        md_lines.append("")

    if best_uniform is not None:
        md_lines.append("## Best valid_uniform/loss/total")
        md_lines.append(f"- step: {best_uniform.get('global_step')}")
        md_lines.append(f"- value: {best_uniform.get('valid_uniform/loss/total')}\n")

    if best_event_cp_f1 is not None:
        md_lines.append("## Best valid_event/change_point/f1")
        md_lines.append(f"- step: {best_event_cp_f1.get('global_step')}")
        md_lines.append(f"- value: {best_event_cp_f1.get('valid_event/change_point/f1')}\n")

    # Train-valid gap (가장 최근)
    if last_train and last_valid:
        train_total = (last_train.get("loss") or {}).get("total")
        valid_uniform_total = last_valid.get("valid_uniform/loss/total")
        if train_total is not None and valid_uniform_total is not None:
            gap = float(valid_uniform_total) - float(train_total)
            md_lines.append("## Train-valid gap (latest)")
            md_lines.append(f"- valid_uniform/total - train/total = {gap:.4f}\n")

    out_path = run_dir / "run_summary.md"
    out_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    print(f"[summary] wrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
