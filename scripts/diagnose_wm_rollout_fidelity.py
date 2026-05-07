"""Session 10 — rollout fidelity + change-point detection delay.

frozen checkpoint를 로드하여 valid chunk에서 H-step prior-only rollout을 수행하고,
실제 미래 관측/상태/reward와 비교한다. 추가로 change-point detection delay (predicted
peak vs ground-truth tick)도 같은 forward에서 산출한다.

방식:
    1. valid_uniform loader (chunk_len=128, batch=8)에서 batch를 받는다.
    2. warmup_len(=32) tick까지 posterior로 belief 형성.
    3. t = warmup..chunk_len-1 동안 prior_step만으로 rollout (action은 실제 chunk의 action).
    4. 매 H={1,5,10,20,50}에서 state/reward 예측 vs 실제 값 비교.
    5. event-window vs uniform 분리: warmup 이후 chunk가 cp/reveal/shift/mismatch 양성을
       포함하는지 여부로 chunk를 분류.
    6. change-point delay: cp probability sequence (sigmoid(logit))의 argmax tick과
       ground-truth cp tick의 거리 측정.

학습/optimizer/backward 코드 없음. ``torch.no_grad`` only.
"""
from __future__ import annotations

import argparse
import sys
import time
from collections import defaultdict
from contextlib import nullcontext
from pathlib import Path
from typing import Dict, List, Optional, Tuple

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
    build_chunk_dataset,
    build_source_indices,
    collate_chunks,
    load_checkpoint,
    make_uniform_event_window_config,
    pick_precision,
    collect_env_report,
)
from falsifiable_regime_world_model.wm.diagnostics import write_csv   # noqa: E402


_RUN_SPEC = (
    ("wm_medium_full_v1", "full_model"),
    ("wm_medium_no_regime_v1", "no_regime"),
    ("wm_medium_no_change_point_v1", "no_change_point"),
)


def _autocast(device: torch.device, precision: str):
    if device.type != "cuda" or precision == "fp32":
        return nullcontext()
    if precision == "bf16":
        return torch.amp.autocast("cuda", dtype=torch.bfloat16)
    if precision == "fp16":
        return torch.amp.autocast("cuda", dtype=torch.float16)
    return nullcontext()


def _build_loader(yaml_path: str, *, chunk_len: int, batch_size: int, eval_kind: str = "uniform") -> DataLoader:
    cfg = WMDataConfig.from_yaml(yaml_path)
    cfg.train.chunk_len = chunk_len
    cfg.valid.chunk_len = chunk_len
    if eval_kind == "uniform":
        cfg = make_uniform_event_window_config(cfg)
    sources = build_source_indices(cfg)
    ds = build_chunk_dataset(cfg, "valid", epoch=0, sources=sources)
    return DataLoader(ds, batch_size=batch_size, num_workers=0, collate_fn=collate_chunks)


@torch.no_grad()
def _rollout_chunk_batch(
    model: RSSMWorldModel,
    batch: Dict,
    *,
    device: torch.device,
    precision: str,
    warmup_len: int,
    horizons: Tuple[int, ...],
) -> Dict[str, np.ndarray]:
    """단일 batch에 대해 (warmup posterior) → (rollout prior) 후 H-step 비교 결과를 반환.

    Returns
    -------
    dict with per-H mse 누적용 numpy 1D arrays:
        state_mse_h{H}: (B,)  per-batch element MSE at step warmup-1+H
        reward_mse_h{H}: (B,)
        regime_acc_h{H}: (B,) — 이 batch에서 valid sample만 평균
        is_event_chunk: (B,) bool — chunk 안에 cp 또는 shift 또는 reveal 양성이 1개 이상 있는지
        cp_in_chunk: (B,) bool
        # cp delay diagnostics
        cp_delay_signed: (n_cp_chunks,) — predicted_peak_tick - true_cp_tick (없으면 NaN/empty)
    """
    inputs = {k: v.to(device, non_blocking=True) for k, v in batch["inputs"].items()}
    targets = {k: v.to(device, non_blocking=True) for k, v in batch["targets"].items()}
    valid_mask = batch["valid_mask"].to(device, non_blocking=True)

    B, T = inputs["local_grid"].shape[:2]
    assert warmup_len < T, f"warmup_len {warmup_len} must be < chunk_len {T}"
    max_H = max(horizons)
    assert warmup_len + max_H <= T, f"warmup_len({warmup_len}) + max_H({max_H}) > chunk_len({T})"

    # ---- Step 1: warmup posterior on [0..warmup_len) ----
    warmup_inputs = {
        "local_grid": inputs["local_grid"][:, :warmup_len],
        "scalar": inputs["scalar"][:, :warmup_len],
        "event_token": inputs["event_token"][:, :warmup_len],
        "action_raw": inputs["action_raw"][:, :warmup_len],
        "action_prev_raw": inputs["action_prev_raw"][:, :warmup_len],
    }
    with _autocast(device, precision):
        warm_out = model(warmup_inputs)
    # last warmup posterior state
    h_init = warm_out["h"][:, -1]
    z_init = warm_out["z"][:, -1]
    from falsifiable_regime_world_model.wm.rssm import RSSMState
    init_state = RSSMState(
        h=h_init, z=z_init,
        prior_mean=warm_out["prior_mean"][:, -1],
        prior_std=warm_out["prior_std"][:, -1],
        post_mean=warm_out["post_mean"][:, -1],
        post_std=warm_out["post_std"][:, -1],
    )

    # ---- Step 2: imagine rollout from warmup_len for max_H ticks ----
    # action_seq for imagine: action_raw[warmup_len-1 .. warmup_len-1+max_H-1] aligned as prev_action
    # imagine 내부에서 action을 prev_action으로 사용. RSSM.imagine_sequence는 action_embeds[i]를
    # 'i번째 step의 prev action'으로 사용 (즉 t=warmup에서 t-1=warmup-1의 action).
    prev_actions = inputs["action_raw"][:, warmup_len - 1: warmup_len - 1 + max_H]   # (B, max_H)
    with _autocast(device, precision):
        roll = model.imagine(prev_actions, init_state)

    # roll heads: state_pred (B, max_H, 5), reward_pred (B, max_H), regime_logits (B, max_H, R) optional, change_point_logit etc.
    state_pred = roll.get("state_pred")
    reward_pred = roll.get("reward_pred")
    regime_logits = roll.get("regime_logits")
    cp_logit = roll.get("change_point_logit")

    # ground truth at the same indices
    state_gt = targets["true_state"][:, warmup_len: warmup_len + max_H]   # (B, max_H, 5)
    reward_gt = targets["reward"][:, warmup_len: warmup_len + max_H]
    regime_gt = targets["true_regime_control_mode"][:, warmup_len: warmup_len + max_H]
    cp_gt = targets["change_point"][:, warmup_len: warmup_len + max_H]
    shift_gt = targets["shift_event"][:, warmup_len: warmup_len + max_H]
    reveal_gt = targets["reveal_event"][:, warmup_len: warmup_len + max_H]
    mismatch_gt = targets["raw_eff_mismatch"][:, warmup_len: warmup_len + max_H]

    out: Dict[str, np.ndarray] = {}
    # per-H scalar metrics
    for H in horizons:
        idx = H - 1   # 0-based: H=1 → idx 0
        if state_pred is not None:
            err = ((state_pred[:, idx].float() - state_gt[:, idx]) ** 2).mean(dim=-1)
            out[f"state_mse_h{H}"] = err.detach().cpu().numpy()
        if reward_pred is not None:
            err = (reward_pred[:, idx].float() - reward_gt[:, idx]) ** 2
            out[f"reward_mse_h{H}"] = err.detach().cpu().numpy()
        if regime_logits is not None:
            pred = torch.argmax(regime_logits[:, idx], dim=-1)
            ok = (pred == regime_gt[:, idx]).float()
            out[f"regime_acc_h{H}"] = ok.detach().cpu().numpy()

    # event/uniform chunk classification (within [warmup_len, warmup_len+max_H))
    cp_chunk_has = (cp_gt > 0.5).any(dim=-1).detach().cpu().numpy()
    shift_chunk_has = (shift_gt > 0.5).any(dim=-1).detach().cpu().numpy()
    reveal_chunk_has = (reveal_gt > 0.5).any(dim=-1).detach().cpu().numpy()
    mismatch_chunk_has = (mismatch_gt > 0.5).any(dim=-1).detach().cpu().numpy()
    out["cp_in_chunk"] = cp_chunk_has.astype(np.float32)
    out["shift_in_chunk"] = shift_chunk_has.astype(np.float32)
    out["reveal_in_chunk"] = reveal_chunk_has.astype(np.float32)
    out["mismatch_in_chunk"] = mismatch_chunk_has.astype(np.float32)
    is_event = cp_chunk_has | shift_chunk_has | reveal_chunk_has | mismatch_chunk_has
    out["is_event_chunk"] = is_event.astype(np.float32)

    # ---- change-point detection delay (cp_logit이 있는 경우) ----
    if cp_logit is not None:
        # cp_logit: (B, max_H). cp_gt: (B, max_H).
        cp_logit_np = cp_logit.float().detach().cpu().numpy()
        cp_gt_np = cp_gt.detach().cpu().numpy()
        delays: List[float] = []
        hits1 = []
        hits3 = []
        hits5 = []
        hits10 = []
        for b in range(B):
            true_idx = np.where(cp_gt_np[b] > 0.5)[0]
            if true_idx.size == 0:
                continue
            true_t = int(true_idx[0])    # 첫 cp 위치를 사용
            pred_peak = int(np.argmax(cp_logit_np[b]))
            d = pred_peak - true_t
            delays.append(d)
            hits1.append(int(abs(d) <= 1))
            hits3.append(int(abs(d) <= 3))
            hits5.append(int(abs(d) <= 5))
            hits10.append(int(abs(d) <= 10))
        out["cp_delays"] = np.array(delays, dtype=np.float32)
        out["cp_hit1"] = np.array(hits1, dtype=np.float32)
        out["cp_hit3"] = np.array(hits3, dtype=np.float32)
        out["cp_hit5"] = np.array(hits5, dtype=np.float32)
        out["cp_hit10"] = np.array(hits10, dtype=np.float32)
    return out


def _aggregate(rows: List[Dict[str, np.ndarray]]) -> Dict[str, np.ndarray]:
    """rollout batches dict list → flat dict (concatenated)."""
    out: Dict[str, list] = defaultdict(list)
    for r in rows:
        for k, v in r.items():
            out[k].append(v)
    return {k: np.concatenate(v, axis=0) if v else np.empty((0,), dtype=np.float32) for k, v in out.items()}


def main() -> int:
    parser = argparse.ArgumentParser(description="Session 10 rollout fidelity + cp delay.")
    parser.add_argument("--runs-root", type=str, default="outputs/wm_runs")
    parser.add_argument("--out-dir", type=str, default="outputs/wm_diagnostics/session10")
    parser.add_argument("--max-batches", type=int, default=64)
    parser.add_argument("--warmup-len", type=int, default=32)
    parser.add_argument("--horizons", type=str, default="1,5,10,20,50")
    parser.add_argument("--chunk-len", type=int, default=128)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--device", type=str, default="auto")
    args = parser.parse_args()

    runs_root = Path(args.runs_root)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    horizons = tuple(int(x) for x in args.horizons.split(","))

    env = collect_env_report()
    device = torch.device("cuda" if (args.device in ("auto", "cuda") and env.gpu.available) else "cpu")
    print(f"[rollout] device={device}  warmup={args.warmup_len}  horizons={horizons}  chunk={args.chunk_len}")

    detail_rows: List[Dict] = []
    summary_rows: List[Dict] = []
    cp_delay_rows: List[Dict] = []

    for run_name, variant in _RUN_SPEC:
        rdir = runs_root / run_name
        ckpt_path = rdir / "checkpoints" / "step_00030000.pt"
        if not ckpt_path.is_file():
            ckpt_path = rdir / "checkpoints" / "last.pt"
        if not ckpt_path.is_file():
            print(f"[rollout] {run_name}: no ckpt; skip")
            continue

        print(f"\n[rollout] === {run_name} ({variant}) ===  ckpt={ckpt_path.name}")
        state = load_checkpoint(ckpt_path, map_location=device)
        wm_cfg = WMConfig.from_yaml(_REPO_ROOT / "configs" / "wm_medium.yaml").apply_variant(variant)
        train_cfg_dict = state.get("train_config", {})
        precision = str(train_cfg_dict.get("precision", "bf16"))
        if precision == "auto":
            precision = pick_precision(env.gpu, "auto")

        model = RSSMWorldModel(wm_cfg).to(device)
        model.load_state_dict(state["model"])
        model.eval()

        eval_cfg = train_cfg_dict.get("eval", {})
        ve_yaml = eval_cfg.get("valid_event_data_config", "configs/wm_data_stage2.yaml")
        vu_yaml = eval_cfg.get("valid_uniform_data_config", "configs/wm_data_stage2.yaml")

        for eval_kind, yaml_path in (("event", ve_yaml), ("uniform", vu_yaml)):
            t0 = time.time()
            loader = _build_loader(
                yaml_path, chunk_len=args.chunk_len, batch_size=args.batch_size, eval_kind=eval_kind,
            )
            batch_outs: List[Dict[str, np.ndarray]] = []
            n = 0
            for batch in loader:
                if n >= args.max_batches:
                    break
                n += 1
                out = _rollout_chunk_batch(
                    model, batch, device=device, precision=precision,
                    warmup_len=args.warmup_len, horizons=horizons,
                )
                batch_outs.append(out)
            elapsed = time.time() - t0
            agg = _aggregate(batch_outs)
            print(f"   [{eval_kind:<7s}] elapsed={elapsed:.1f}s  n_chunks={int(agg.get('is_event_chunk', np.array([])).size)}")

            # ---- 한 H에 대해 event/uniform/cp/non-cp 분리 metric ----
            n_chunks = int(agg.get("is_event_chunk", np.array([])).size)
            is_event = agg["is_event_chunk"].astype(bool) if "is_event_chunk" in agg else np.zeros(n_chunks, dtype=bool)
            cp_in = agg["cp_in_chunk"].astype(bool) if "cp_in_chunk" in agg else np.zeros(n_chunks, dtype=bool)

            for H in horizons:
                state_arr = agg.get(f"state_mse_h{H}")
                reward_arr = agg.get(f"reward_mse_h{H}")
                regime_arr = agg.get(f"regime_acc_h{H}")

                def _agg(values: Optional[np.ndarray], sel: Optional[np.ndarray] = None) -> Optional[float]:
                    if values is None or values.size == 0:
                        return None
                    if sel is not None:
                        if sel.sum() == 0:
                            return None
                        values = values[sel]
                    return float(values.mean())

                row_base = {
                    "run_name": run_name, "variant": variant, "eval_kind": eval_kind, "H": H,
                    "n_chunks": n_chunks,
                    "n_event_chunks": int(is_event.sum()),
                    "n_cp_chunks": int(cp_in.sum()),
                    "state_mse_all": _agg(state_arr),
                    "state_mse_event": _agg(state_arr, is_event),
                    "state_mse_non_event": _agg(state_arr, ~is_event),
                    "state_mse_cp_chunk": _agg(state_arr, cp_in),
                    "state_mse_non_cp_chunk": _agg(state_arr, ~cp_in),
                    "reward_mse_all": _agg(reward_arr),
                    "reward_mse_event": _agg(reward_arr, is_event),
                    "reward_mse_non_event": _agg(reward_arr, ~is_event),
                    "reward_mse_cp_chunk": _agg(reward_arr, cp_in),
                    "regime_acc_all": _agg(regime_arr),
                    "regime_acc_event": _agg(regime_arr, is_event),
                    "regime_acc_non_event": _agg(regime_arr, ~is_event),
                    "regime_acc_cp_chunk": _agg(regime_arr, cp_in),
                }
                detail_rows.append(row_base)

            # rollout_fidelity_summary: H별 핵심 metric 한 줄 요약
            for H in horizons:
                state_arr = agg.get(f"state_mse_h{H}")
                reward_arr = agg.get(f"reward_mse_h{H}")
                summary_rows.append({
                    "run_name": run_name, "variant": variant,
                    "eval_kind": eval_kind, "H": H,
                    "state_mse_mean": float(state_arr.mean()) if state_arr is not None and state_arr.size else None,
                    "state_mse_event_minus_uniform": (
                        float(state_arr[is_event].mean() - state_arr[~is_event].mean())
                        if state_arr is not None and is_event.sum() > 0 and (~is_event).sum() > 0
                        else None
                    ),
                    "reward_mse_mean": float(reward_arr.mean()) if reward_arr is not None and reward_arr.size else None,
                })

            # change-point delay 요약
            if "cp_delays" in agg and agg["cp_delays"].size > 0:
                d = agg["cp_delays"]
                cp_delay_rows.append({
                    "run_name": run_name, "variant": variant, "eval_kind": eval_kind,
                    "n_cp_chunks": int(d.size),
                    "delay_mean": float(d.mean()),
                    "delay_median": float(np.median(d)),
                    "delay_p10": float(np.percentile(d, 10)),
                    "delay_p90": float(np.percentile(d, 90)),
                    "delay_abs_mean": float(np.abs(d).mean()),
                    "hit_at_1": float(agg["cp_hit1"].mean()),
                    "hit_at_3": float(agg["cp_hit3"].mean()),
                    "hit_at_5": float(agg["cp_hit5"].mean()),
                    "hit_at_10": float(agg["cp_hit10"].mean()),
                })
                print(f"      cp delay: n_cp={d.size}  mean={d.mean():+.2f}  abs_mean={np.abs(d).mean():.2f}  "
                      f"hit@5={float(agg['cp_hit5'].mean()):.2f}  hit@10={float(agg['cp_hit10'].mean()):.2f}")

            # console summary per eval_kind
            for H in (1, 5, 10, 50):
                if H not in horizons:
                    continue
                sa = agg.get(f"state_mse_h{H}")
                ra = agg.get(f"reward_mse_h{H}")
                if sa is None or sa.size == 0:
                    continue
                evt_mse = sa[is_event].mean() if is_event.sum() else float("nan")
                non_mse = sa[~is_event].mean() if (~is_event).sum() else float("nan")
                print(f"      H={H:>2d}  state_mse all={sa.mean():.4f}  event={evt_mse:.4f}  non_event={non_mse:.4f}  "
                      f"reward_mse={ra.mean() if ra is not None else 0:.2f}")

        del model
        if device.type == "cuda":
            torch.cuda.empty_cache()

    write_csv(out_dir / "rollout_fidelity.csv", detail_rows)
    write_csv(out_dir / "rollout_fidelity_summary.csv", summary_rows)
    write_csv(out_dir / "change_point_delay.csv", cp_delay_rows)
    print(f"\n[rollout] wrote {out_dir/'rollout_fidelity.csv'} ({len(detail_rows)} rows)")
    print(f"[rollout] wrote {out_dir/'rollout_fidelity_summary.csv'} ({len(summary_rows)} rows)")
    print(f"[rollout] wrote {out_dir/'change_point_delay.csv'} ({len(cp_delay_rows)} rows)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
