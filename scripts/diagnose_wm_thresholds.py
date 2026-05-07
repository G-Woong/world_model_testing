"""Session 10 — threshold sweep + PR-AUC for binary heads.

frozen checkpoint를 로드하여 valid_event / valid_uniform에서 cp / reveal / shift /
raw_eff_mismatch / success_done / terminal head logits을 수집하고, threshold sweep과
PR-AUC를 계산한다.

학습/optimizer/backward 코드 없음. ``torch.no_grad`` only.

생성:
    outputs/wm_diagnostics/session10/threshold_sweep.csv
    outputs/wm_diagnostics/session10/threshold_sweep_summary.csv
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from contextlib import nullcontext
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import torch
from torch.utils.data import DataLoader

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from falsifiable_regime_world_model.wm import (   # noqa: E402
    RSSMWorldModel,
    WMConfig,
    WMDataConfig,
    WMTrainConfig,
    build_chunk_dataset,
    build_source_indices,
    collate_chunks,
    load_checkpoint,
    make_uniform_event_window_config,
    pick_precision,
    collect_env_report,
)
from falsifiable_regime_world_model.wm.diagnostics import (   # noqa: E402
    pr_auc,
    threshold_sweep,
    write_csv,
)


_RUN_SPEC = (
    ("wm_medium_full_v1", "full_model"),
    ("wm_medium_no_regime_v1", "no_regime"),
    ("wm_medium_no_change_point_v1", "no_change_point"),
)


# 평가할 binary head 목록. (logit_key, target_key, head_name, na_for_variant)
_BINARY_HEADS = (
    ("change_point_logit", "change_point", "change_point", ("no_change_point",)),
    ("reveal_logit", "reveal_event", "reveal", ()),
    ("shift_logit", "shift_event", "shift", ()),
    ("raw_eff_mismatch_logit", "raw_eff_mismatch", "raw_eff_mismatch", ()),
    ("done_logit", "success_done", "success_done", ()),
    ("done_logit", "terminal", "terminal", ()),
)


def _autocast(device: torch.device, precision: str):
    if device.type != "cuda" or precision == "fp32":
        return nullcontext()
    if precision == "bf16":
        return torch.amp.autocast("cuda", dtype=torch.bfloat16)
    if precision == "fp16":
        return torch.amp.autocast("cuda", dtype=torch.float16)
    return nullcontext()


def _build_loaders(
    data_cfg_path: str,
    *,
    chunk_len: int,
    batch_size: int,
    split: str,
    eval_kind: str,    # 'event' | 'uniform'
) -> DataLoader:
    cfg = WMDataConfig.from_yaml(data_cfg_path)
    cfg.train.chunk_len = chunk_len
    cfg.valid.chunk_len = chunk_len
    if eval_kind == "uniform":
        cfg = make_uniform_event_window_config(cfg)
    sources = build_source_indices(cfg)
    ds = build_chunk_dataset(cfg, split, epoch=0, sources=sources)
    return DataLoader(ds, batch_size=batch_size, num_workers=0, collate_fn=collate_chunks)


def _collect_logits(
    model: RSSMWorldModel,
    loader: DataLoader,
    device: torch.device,
    precision: str,
    *,
    max_batches: int,
) -> Dict[str, np.ndarray]:
    """frozen forward로 logit/target/mask을 누적해 numpy로 반환."""
    model.eval()
    bins: Dict[str, List[np.ndarray]] = {}
    n = 0
    with torch.no_grad():
        for batch in loader:
            if n >= max_batches:
                break
            n += 1
            inputs = {k: v.to(device, non_blocking=True) for k, v in batch["inputs"].items()}
            targets = {k: v.to(device, non_blocking=True) for k, v in batch["targets"].items()}
            mask = batch["valid_mask"].to(device, non_blocking=True)
            with _autocast(device, precision):
                out = model(inputs)
            for logit_key, target_key, head_name, _ in _BINARY_HEADS:
                if logit_key not in out:
                    continue
                if target_key not in targets:
                    continue
                logit = out[logit_key].float().detach().cpu().numpy().reshape(-1)
                target = targets[target_key].float().detach().cpu().numpy().reshape(-1)
                m = mask.detach().cpu().numpy().reshape(-1)
                bins.setdefault(head_name + "/logit", []).append(logit)
                bins.setdefault(head_name + "/target", []).append(target)
                bins.setdefault(head_name + "/mask", []).append(m)
    out_np: Dict[str, np.ndarray] = {}
    for k, v in bins.items():
        out_np[k] = np.concatenate(v, axis=0) if v else np.empty((0,), dtype=np.float32)
    return out_np


def main() -> int:
    parser = argparse.ArgumentParser(description="Session 10 threshold sweep + PR-AUC.")
    parser.add_argument("--runs-root", type=str, default="outputs/wm_runs")
    parser.add_argument("--out-dir", type=str, default="outputs/wm_diagnostics/session10")
    parser.add_argument("--max-batches", type=int, default=64,
                        help="batches per (eval_kind, run); valid_event/uniform 각 64.")
    parser.add_argument("--device", type=str, default="auto")
    args = parser.parse_args()

    runs_root = Path(args.runs_root)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    env = collect_env_report()
    device = torch.device("cuda" if (args.device in ("auto", "cuda") and env.gpu.available) else "cpu")
    print(f"[thr] device={device}")

    sweep_rows: List[Dict] = []
    summary_rows: List[Dict] = []

    for run_name, variant in _RUN_SPEC:
        rdir = runs_root / run_name
        ckpt_path = rdir / "checkpoints" / "step_00030000.pt"
        if not ckpt_path.is_file():
            ckpt_path = rdir / "checkpoints" / "last.pt"
        if not ckpt_path.is_file():
            print(f"[thr] {run_name}: no checkpoint found; skip")
            continue

        print(f"\n[thr] === {run_name} ({variant}) ===")
        print(f"      ckpt={ckpt_path}")
        state = load_checkpoint(ckpt_path, map_location=device)
        # WMConfig는 train_config의 wm_config path에서 로드 (apply_variant 후 저장된 것이 state['wm_config'])
        # 안전한 경로: WMConfig.from_yaml(configs/wm_medium.yaml) → apply_variant
        wm_cfg = WMConfig.from_yaml(_REPO_ROOT / "configs" / "wm_medium.yaml").apply_variant(variant)
        train_cfg_dict = state.get("train_config", {})
        chunk_len = int(train_cfg_dict.get("chunk_len", 128))
        batch_size = int(train_cfg_dict.get("batch_size", 8))
        precision = state.get("env_summary", {}).get("precision", "bf16") if False else "bf16"
        # precision은 학습 시 사용된 것을 정확히 재현하기 위해 train_config에서 가져온다.
        precision = str(train_cfg_dict.get("precision", "bf16"))
        if precision == "auto":
            precision = pick_precision(env.gpu, "auto")

        # model 로드
        model = RSSMWorldModel(wm_cfg).to(device)
        model.load_state_dict(state["model"])

        # 학습 시 사용한 valid event_data_config / uniform_data_config과 동일 yaml 사용
        eval_cfg = train_cfg_dict.get("eval", {})
        ve_yaml = eval_cfg.get("valid_event_data_config", "configs/wm_data_stage2.yaml")
        vu_yaml = eval_cfg.get("valid_uniform_data_config", "configs/wm_data_stage2.yaml")

        for eval_kind, yaml_path in (("event", ve_yaml), ("uniform", vu_yaml)):
            t0 = time.time()
            loader = _build_loaders(
                yaml_path, chunk_len=chunk_len, batch_size=batch_size,
                split="valid", eval_kind=eval_kind,
            )
            data = _collect_logits(model, loader, device, precision, max_batches=args.max_batches)
            elapsed = time.time() - t0
            print(f"   eval_kind={eval_kind:<7s} elapsed={elapsed:.1f}s  cached_keys={len(data)//3}")

            for logit_key, target_key, head_name, na_for in _BINARY_HEADS:
                if variant in na_for:
                    summary_rows.append({
                        "run_name": run_name, "variant": variant,
                        "eval_kind": eval_kind, "head": head_name,
                        "na_reason": "head removed in variant",
                    })
                    continue
                lk = head_name + "/logit"
                tk = head_name + "/target"
                mk = head_name + "/mask"
                if lk not in data or tk not in data:
                    summary_rows.append({
                        "run_name": run_name, "variant": variant,
                        "eval_kind": eval_kind, "head": head_name,
                        "na_reason": "missing logit or target in forward output",
                    })
                    continue
                logit = data[lk]
                target = data[tk]
                mask = data[mk]
                # threshold sweep
                rows = threshold_sweep(logit, target, mask)
                for r in rows:
                    sweep_rows.append({
                        "run_name": run_name, "variant": variant,
                        "eval_kind": eval_kind, "head": head_name, **r,
                    })
                # PR-AUC + best
                ap = pr_auc(logit, target, mask)
                # fixed threshold=0.0의 F1
                f1_at_zero = 0.0
                for r in rows:
                    if r["threshold_logit"] == 0:
                        f1_at_zero = r["f1"]
                        break
                summary_rows.append({
                    "run_name": run_name, "variant": variant,
                    "eval_kind": eval_kind, "head": head_name,
                    "n_total": ap["n_total"], "n_positive": ap["n_positive"],
                    "f1_at_zero": f1_at_zero,
                    "best_f1": ap["best_f1"],
                    "best_threshold_logit": ap["best_threshold_logit"],
                    "best_precision": ap["best_precision"],
                    "best_recall": ap["best_recall"],
                    "pr_auc": ap["pr_auc"],
                    "pos_logit_mean": ap["pos_logit_mean"],
                    "neg_logit_mean": ap["neg_logit_mean"],
                    "separation": ap["separation"],
                    "na_reason": "",
                })
                print(f"      [{head_name:<18s}] n_pos={ap['n_positive']:.0f}/{ap['n_total']:.0f}  "
                      f"f1@0={f1_at_zero:.3f}  best_f1={ap['best_f1']:.3f}@th={ap['best_threshold_logit']:.2f}  "
                      f"PR-AUC={ap['pr_auc']:.3f}  sep={ap['separation']:+.2f}")

        # cleanup
        del model
        if device.type == "cuda":
            torch.cuda.empty_cache()

    write_csv(out_dir / "threshold_sweep.csv", sweep_rows)
    write_csv(out_dir / "threshold_sweep_summary.csv", summary_rows)
    print(f"\n[thr] wrote {out_dir / 'threshold_sweep.csv'} ({len(sweep_rows)} rows)")
    print(f"[thr] wrote {out_dir / 'threshold_sweep_summary.csv'} ({len(summary_rows)} rows)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
