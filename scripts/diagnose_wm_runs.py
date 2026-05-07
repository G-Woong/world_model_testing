"""Session 10 — log-based run summary + reward long-tail diagnostics.

본 스크립트는 *frozen log + checkpoint 메타*만 읽고 학습/optimizer/backward를 일절
실행하지 않는다. checkpoint 자체는 inventory에만 사용되고 forward/backward로 평가하지
않는다 (그건 ``diagnose_wm_thresholds.py`` / ``diagnose_wm_rollout_fidelity.py``).

생성:
    outputs/wm_diagnostics/session10/
        checkpoint_inventory.csv
        run_summary_table.csv
        final_valid_table.csv
        best_valid_table.csv
        common_core_metrics.csv
        reward_diagnostics_log.csv     (train_log 기반 reward MSE long-tail proxy)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from falsifiable_regime_world_model.wm.diagnostics import (   # noqa: E402
    inventory_checkpoints,
    read_jsonl,
    summarize_run,
    write_csv,
)


# 표준 3 run + variant 매핑
_RUN_SPEC = (
    ("wm_medium_full_v1", "full_model"),
    ("wm_medium_no_regime_v1", "no_regime"),
    ("wm_medium_no_change_point_v1", "no_change_point"),
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Session 10 log-level diagnostics.")
    parser.add_argument("--runs-root", type=str, default="outputs/wm_runs")
    parser.add_argument("--out-dir", type=str, default="outputs/wm_diagnostics/session10")
    args = parser.parse_args()

    runs_root = Path(args.runs_root)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    summaries = []
    inv_rows = []
    final_rows = []
    best_rows = []
    common_rows = []
    reward_rows = []

    for run_name, variant in _RUN_SPEC:
        rdir = runs_root / run_name
        if not rdir.is_dir():
            print(f"[skip] {run_name}: run dir not found")
            continue
        # ---- summary ----
        rsum = summarize_run(rdir, variant=variant)
        summaries.append(rsum)
        row = rsum.to_row()
        # csv 친화적으로 nan는 빈 칸으로
        common_rows.append({
            "run_name": rsum.run_name,
            "variant": rsum.variant,
            "final_step": rsum.final_step,
            "final_stage": rsum.final_stage,
            # common-core only
            "valid_uniform_total": rsum.final_valid_uniform_total,
            "valid_event_total": rsum.final_valid_event_total,
            "reward_mse_uniform": rsum.reward_mse_uniform,
            "state_mse_uniform": rsum.state_mse_uniform,
            "reveal_f1_event": rsum.reveal_f1_event,
            "shift_f1_event": rsum.shift_f1_event,
            "raw_eff_mismatch_f1_event": rsum.raw_eff_mismatch_f1_event,
        })
        # ---- inventory ----
        ck = inventory_checkpoints(rdir, variant=variant)
        inv_rows.append({
            "run_name": ck.run_name,
            "variant": ck.variant,
            "last_pt": ck.last_pt,
            "step_30000_pt": ck.step_30000_pt,
            "step_29000_pt": ck.step_29000_pt,
            "best_valid_uniform_pt": ck.best_valid_uniform_pt,
            "best_valid_event_cp_f1_pt": ck.best_valid_event_cp_f1_pt,
            "primary_path": ck.primary_path,
            "alias_missing_notes": ck.alias_missing_notes,
        })

        # ---- final valid ----
        valid_log = read_jsonl(rdir / "valid_log.jsonl")
        if valid_log:
            r = valid_log[-1]
            final_rows.append({
                "run_name": run_name, "variant": variant, "step": r.get("global_step"),
                "valid_uniform/loss/total": r.get("valid_uniform/loss/total"),
                "valid_event/loss/total": r.get("valid_event/loss/total"),
                "valid_uniform/reward/mse": r.get("valid_uniform/reward/mse"),
                "valid_uniform/state/mse": r.get("valid_uniform/state/mse"),
                "valid_uniform/regime/accuracy": r.get("valid_uniform/regime/accuracy"),
                "valid_event/change_point/f1": r.get("valid_event/change_point/f1"),
                "valid_event/change_point/precision": r.get("valid_event/change_point/precision"),
                "valid_event/change_point/recall": r.get("valid_event/change_point/recall"),
                "valid_event/change_point/positives": r.get("valid_event/change_point/positives"),
                "valid_event/reveal/f1": r.get("valid_event/reveal/f1"),
                "valid_event/shift/f1": r.get("valid_event/shift/f1"),
                "valid_event/raw_eff_mismatch/f1": r.get("valid_event/raw_eff_mismatch/f1"),
                "valid_uniform/success_done/f1": r.get("valid_uniform/success_done/f1"),
                "valid_uniform/terminal/f1": r.get("valid_uniform/terminal/f1"),
                "valid_uniform/truncated/rate": r.get("valid_uniform/truncated/rate"),
            })

        # ---- best valid (per metric, log 기반) ----
        if valid_log:
            best_rows.append({
                "run_name": run_name, "variant": variant,
                "best_valid_uniform_total": rsum.best_valid_uniform_total,
                "best_valid_uniform_step": rsum.best_valid_uniform_step,
                "best_valid_event_change_point_f1": rsum.best_valid_event_change_point_f1,
                "best_valid_event_change_point_step": rsum.best_valid_event_change_point_step,
            })

        # ---- reward long-tail proxy from train_log ----
        train_log = read_jsonl(rdir / "train_log.jsonl")
        if train_log:
            losses = [r.get("loss", {}).get("reward", 0.0) for r in train_log if "loss" in r]
            sw_max = [r.get("sample_weight", {}).get("max", 0.0) for r in train_log]
            grad_norms = [r.get("grad_norm", 0.0) for r in train_log]
            n = len(losses)
            if n:
                import numpy as np
                arr = np.array(losses, dtype=np.float64)
                # spike: > 5x median
                med = float(np.median(arr))
                spike_thr = max(med * 5.0, 5.0)
                spike_idx = np.where(arr > spike_thr)[0]
                top5_idx = np.argsort(-arr)[:5]
                reward_rows.append({
                    "run_name": run_name, "variant": variant,
                    "n_logged_steps": n,
                    "loss_reward_mean": float(arr.mean()),
                    "loss_reward_median": med,
                    "loss_reward_p90": float(np.percentile(arr, 90)),
                    "loss_reward_p99": float(np.percentile(arr, 99)),
                    "loss_reward_max": float(arr.max()),
                    "n_spikes_gt_5x_median": int(spike_idx.size),
                    "top5_spike_steps": ";".join(str(train_log[int(i)].get("global_step")) for i in top5_idx),
                    "top5_spike_values": ";".join(f"{arr[i]:.2f}" for i in top5_idx),
                    "sw_max_max": float(np.max(sw_max)) if sw_max else 0.0,
                    "grad_norm_max": float(np.max(grad_norms)) if grad_norms else 0.0,
                    "grad_norm_p99": float(np.percentile(grad_norms, 99)) if grad_norms else 0.0,
                })

    # ---- run summary table ----
    write_csv(out_dir / "run_summary_table.csv", [s.to_row() for s in summaries])
    write_csv(out_dir / "checkpoint_inventory.csv", inv_rows)
    write_csv(out_dir / "final_valid_table.csv", final_rows)
    write_csv(out_dir / "best_valid_table.csv", best_rows)
    write_csv(out_dir / "common_core_metrics.csv", common_rows)
    write_csv(out_dir / "reward_diagnostics_log.csv", reward_rows)

    # 콘솔 요약
    print("=== Session 10 -- log-based diagnostics ===")
    print(f"out_dir: {out_dir}")
    print()
    print("checkpoint inventory:")
    for r in inv_rows:
        print(f"  - {r['run_name']:<32s} variant={r['variant']:<18s} primary={r['primary_path']}")
        if r['alias_missing_notes']:
            print(f"      WARN: {r['alias_missing_notes']}")
    print()
    print("final valid (last record):")
    for r in final_rows:
        print(f"  - {r['run_name']:<32s} step={r['step']} "
              f"uni_tot={r['valid_uniform/loss/total']:.3f}  "
              f"evt_tot={r['valid_event/loss/total']:.3f}  "
              f"cp_f1={(r['valid_event/change_point/f1'] or 0):.3f}  "
              f"reveal_f1={(r['valid_event/reveal/f1'] or 0):.3f}  "
              f"mismatch_f1={(r['valid_event/raw_eff_mismatch/f1'] or 0):.3f}")
    print()
    print("reward long-tail (train_log 기반):")
    for r in reward_rows:
        print(f"  - {r['run_name']:<32s} mean={r['loss_reward_mean']:.2f} "
              f"p99={r['loss_reward_p99']:.2f} max={r['loss_reward_max']:.2f} "
              f"n_spikes>5xmed={r['n_spikes_gt_5x_median']}  "
              f"grad_p99={r['grad_norm_p99']:.1f}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
