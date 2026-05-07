"""Session 10 — held-out (test_id / OOD) prediction diagnostics + claim verdict.

frozen checkpoint를 로드하여 dataset의 ``test_id`` / ``ood_*`` split들에 대해 no_grad
forward를 1회 수행하고, common-core metric (state MSE, reward MSE, reveal F1, shift F1,
raw_eff_mismatch F1, cp F1 + PR-AUC)을 산출한다.

PART0 §3 정합:
    - 본 결과는 *held-out diagnostic* — paper에서는 generalization 분석 자료로만 인용.
    - hyperparameter / checkpoint 선택에 사용 금지.
    - 본 스크립트는 학습/optimizer/backward 0회.

분석 split:
    test_id, ood_room_perm, ood_factor_recomb, ood_param_shift,
    ood_obs_shift, ood_field_placement

dataset roots (각 split이 모두 존재):
    data/rg4f_random_2000
    data/rg4f_success_curriculum_v5_2000

본 스크립트는 ``SourceIndex``를 우회한다 (``SourceIndex``는 ALLOWED_TRAIN_SPLITS만 캐시).
대신 ``rg4f.dataset_io.load_index`` / ``load_episode``를 직접 호출 + 학습 dataset의
chunk 처리(``data._slice_episode`` / ``sampling.compute_sample_weight``)를 그대로 재사용.
"""
from __future__ import annotations

import argparse
import sys
import time
from collections import defaultdict
from contextlib import nullcontext
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
import torch
from torch.utils.data import DataLoader, IterableDataset

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from falsifiable_regime_world_model.rg4f.dataset_io import (   # noqa: E402
    EpisodeBundle,
    IndexEntry,
    load_episode,
    load_index,
    load_manifest,
)
from falsifiable_regime_world_model.wm import (   # noqa: E402
    RSSMWorldModel,
    WMConfig,
    WMDataConfig,
    collate_chunks,
    load_checkpoint,
    pick_precision,
    collect_env_report,
)
from falsifiable_regime_world_model.wm.data import (   # noqa: E402
    EpisodeChunk,
    _slice_episode,
)
from falsifiable_regime_world_model.wm.data_config import EventWindowConfig, SampleWeightConfig, TargetConfig   # noqa: E402
from falsifiable_regime_world_model.wm.sampling import EventWindowSampler, compute_sample_weight, extract_event_index   # noqa: E402
from falsifiable_regime_world_model.wm.diagnostics import pr_auc, write_csv   # noqa: E402


_RUN_SPEC = (
    ("wm_medium_full_v1", "full_model"),
    ("wm_medium_no_regime_v1", "no_regime"),
    ("wm_medium_no_change_point_v1", "no_change_point"),
)

_DATASETS = (
    ("random_2000", "data/rg4f_random_2000"),
    ("success_v5_2000", "data/rg4f_success_curriculum_v5_2000"),
)

_SPLITS_TO_EVAL = (
    "test_id",
    "ood_room_perm",
    "ood_factor_recomb",
    "ood_param_shift",
    "ood_obs_shift",
    "ood_field_placement",
)


def _autocast(device: torch.device, precision: str):
    if device.type != "cuda" or precision == "fp32":
        return nullcontext()
    if precision == "bf16":
        return torch.amp.autocast("cuda", dtype=torch.bfloat16)
    if precision == "fp16":
        return torch.amp.autocast("cuda", dtype=torch.float16)
    return nullcontext()


# =============================================================================
# 1. Held-out chunk dataset (test_id / OOD)
# =============================================================================


class HeldOutChunkDataset(IterableDataset):
    """test_id / OOD split episodes에서 uniform chunk를 yield.

    학습용 ``RG4FChunkIterableDataset``과 의미는 같지만, ``SourceIndex.entries(split)``의
    ALLOWED_TRAIN_SPLITS guard를 우회하기 위해 직접 ``load_index`` / ``load_episode``를
    호출한다.

    중요:
        - sample_weight는 boost OFF (모든 valid tick = 1.0).
        - event_window는 OFF (uniform sampling).
        - 본 dataset은 hyperparameter selection에 절대 사용되지 않는다 (스크립트가 호출하는
          상위 레벨에서 분석 결과만 csv로 dump).
    """

    def __init__(
        self,
        root: Path,
        split: str,
        *,
        chunk_len: int,
        n_episodes: int,
        chunks_per_episode: int,
        seed: int,
    ) -> None:
        super().__init__()
        self.root = Path(root)
        self.split = split
        self.chunk_len = int(chunk_len)
        self.chunks_per_episode = int(chunks_per_episode)
        self.seed = int(seed)
        # split index 직접 로드
        split_dir = self.root / split
        if not split_dir.is_dir():
            self._entries: List[IndexEntry] = []
            return
        all_entries = load_index(split_dir)
        # 결정성: seed + split name으로 sub-sample
        rng = np.random.default_rng(self.seed)
        if len(all_entries) > n_episodes:
            idxs = rng.choice(len(all_entries), size=n_episodes, replace=False)
            self._entries = [all_entries[int(i)] for i in idxs]
        else:
            self._entries = list(all_entries)
        # uniform-only event window
        self._event_window = EventWindowConfig(
            enabled=False, change_point_prob=0, shift_prob=0, reveal_prob=0,
            success_prob=0, uniform_prob=1.0,
        )
        self._sample_weight_cfg = SampleWeightConfig(
            enabled=True, base_weight=1.0, boost_radius=0,
            change_point_boost=1.0, shift_boost=1.0, reveal_boost=1.0,
            success_boost=1.0, raw_eff_mismatch_boost=1.0, weight_cap=1.0,
        )
        self._target_cfg = TargetConfig(obs_recon_mode="next_step")
        self._sampler = EventWindowSampler(self._event_window)

    def __iter__(self):
        rng = np.random.default_rng(self.seed * 100003 + 7)
        for ep_idx, entry in enumerate(self._entries):
            try:
                bundle: EpisodeBundle = load_episode(self.root, entry, load_meta=False, mmap=False)
            except Exception:   # noqa: BLE001
                continue
            arrays = bundle.arrays
            ev_index = extract_event_index(arrays)
            T = ev_index.episode_length
            for _ in range(self.chunks_per_episode):
                chunk_start, sampler_type = self._sampler.sample_chunk_start(
                    ev_index, self.chunk_len, rng,
                )
                valid_len = max(1, min(self.chunk_len, T - chunk_start))
                sliced = _slice_episode(arrays, chunk_start, self.chunk_len, valid_len, self._target_cfg)
                sample_weight = compute_sample_weight(
                    arrays=arrays, chunk_start=chunk_start, chunk_len=self.chunk_len,
                    valid_len=valid_len, cfg=self._sample_weight_cfg,
                    raw_eff_mismatch_subsample_max=64, rng=rng,
                )
                yield EpisodeChunk(
                    arrays=sliced, valid_len=valid_len, sample_weight=sample_weight,
                    source_id=0, source_name=self.root.name, split=self.split,
                    episode_id=str(entry.episode_id), chunk_start=chunk_start,
                    sampler_type=sampler_type,
                )


# =============================================================================
# 2. metrics extraction (logits/targets accumulator)
# =============================================================================


def _evaluate_split(
    model: RSSMWorldModel,
    *,
    root: Path,
    split: str,
    chunk_len: int,
    batch_size: int,
    n_episodes: int,
    chunks_per_episode: int,
    seed: int,
    device: torch.device,
    precision: str,
    has_regime: bool,
    has_cp: bool,
) -> Dict[str, float]:
    ds = HeldOutChunkDataset(
        root=root, split=split, chunk_len=chunk_len,
        n_episodes=n_episodes, chunks_per_episode=chunks_per_episode, seed=seed,
    )
    if not ds._entries:   # noqa: SLF001
        return {"n_chunks": 0, "n_episodes": 0, "skipped": 1.0}
    loader = DataLoader(ds, batch_size=batch_size, num_workers=0, collate_fn=collate_chunks)

    state_se = []
    reward_se = []
    regime_correct = 0
    regime_total = 0
    n_chunks = 0
    cp_logit = []
    cp_target = []
    rv_logit = []
    rv_target = []
    sh_logit = []
    sh_target = []
    mm_logit = []
    mm_target = []

    model.eval()
    with torch.no_grad():
        for batch in loader:
            inputs = {k: v.to(device, non_blocking=True) for k, v in batch["inputs"].items()}
            targets = {k: v.to(device, non_blocking=True) for k, v in batch["targets"].items()}
            mask = batch["valid_mask"].to(device, non_blocking=True)
            with _autocast(device, precision):
                out = model(inputs)
            mask_b = (mask > 0)
            n_chunks += inputs["local_grid"].shape[0]

            # state MSE
            if "state_pred" in out:
                err = ((out["state_pred"].float() - targets["true_state"]) ** 2).mean(dim=-1)
                state_se.append((err[mask_b]).detach().cpu().numpy())

            # reward MSE
            if "reward_pred" in out:
                err = (out["reward_pred"].float() - targets["reward"]) ** 2
                reward_se.append((err[mask_b]).detach().cpu().numpy())

            # regime accuracy
            if has_regime and "regime_logits" in out:
                pred = torch.argmax(out["regime_logits"], dim=-1)
                ok = (pred == targets["true_regime_control_mode"])
                regime_correct += int((ok & mask_b).sum().item())
                regime_total += int(mask_b.sum().item())

            # binary heads
            for head_name, logit_key, target_key, store_l, store_t in (
                ("change_point", "change_point_logit", "change_point", cp_logit, cp_target),
                ("reveal", "reveal_logit", "reveal_event", rv_logit, rv_target),
                ("shift", "shift_logit", "shift_event", sh_logit, sh_target),
                ("mismatch", "raw_eff_mismatch_logit", "raw_eff_mismatch", mm_logit, mm_target),
            ):
                if logit_key in out:
                    l = out[logit_key].float().detach().cpu().numpy().reshape(-1)
                    t = targets[target_key].detach().cpu().numpy().reshape(-1)
                    m = mask.detach().cpu().numpy().reshape(-1).astype(bool)
                    store_l.append(l[m])
                    store_t.append(t[m])

    out_dict: Dict[str, float] = {"n_chunks": float(n_chunks), "n_episodes": float(len(ds._entries))}   # noqa: SLF001

    if state_se:
        arr = np.concatenate(state_se)
        out_dict["state_mse"] = float(arr.mean()) if arr.size else float("nan")
    if reward_se:
        arr = np.concatenate(reward_se)
        out_dict["reward_mse"] = float(arr.mean()) if arr.size else float("nan")
    if has_regime and regime_total > 0:
        out_dict["regime_accuracy"] = regime_correct / regime_total

    def _binary_summary(name: str, logits: List[np.ndarray], targets_list: List[np.ndarray]) -> None:
        if not logits:
            return
        l = np.concatenate(logits)
        t = np.concatenate(targets_list)
        if l.size == 0:
            return
        ap = pr_auc(l, t, mask=None)
        out_dict[f"{name}_n_pos"] = ap["n_positive"]
        out_dict[f"{name}_pr_auc"] = ap["pr_auc"]
        out_dict[f"{name}_best_f1"] = ap["best_f1"]
        out_dict[f"{name}_best_th_logit"] = ap["best_threshold_logit"]
        out_dict[f"{name}_separation"] = ap["separation"]
        # f1 at threshold 0
        pred = (l > 0)
        tgt = (t > 0.5)
        tp = int((pred & tgt).sum())
        fp = int((pred & ~tgt).sum())
        fn = int((~pred & tgt).sum())
        eps = 1e-9
        precision = tp / max(eps, tp + fp)
        recall = tp / max(eps, tp + fn)
        f1 = 2 * precision * recall / max(eps, precision + recall)
        out_dict[f"{name}_f1_at_zero"] = float(f1)

    if has_cp:
        _binary_summary("cp", cp_logit, cp_target)
    _binary_summary("reveal", rv_logit, rv_target)
    _binary_summary("shift", sh_logit, sh_target)
    _binary_summary("mismatch", mm_logit, mm_target)

    return out_dict


def main() -> int:
    parser = argparse.ArgumentParser(description="Session 10 held-out OOD diagnostics.")
    parser.add_argument("--runs-root", type=str, default="outputs/wm_runs")
    parser.add_argument("--out-dir", type=str, default="outputs/wm_diagnostics/session10")
    parser.add_argument("--n-episodes", type=int, default=10, help="per (dataset, split) episodes 수")
    parser.add_argument("--chunks-per-episode", type=int, default=4)
    parser.add_argument("--chunk-len", type=int, default=128)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--device", type=str, default="auto")
    args = parser.parse_args()

    runs_root = Path(args.runs_root)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    env = collect_env_report()
    device = torch.device("cuda" if (args.device in ("auto", "cuda") and env.gpu.available) else "cpu")
    print(f"[ood] device={device}  n_ep={args.n_episodes} chunks/ep={args.chunks_per_episode}")
    print("[ood] *** held-out diagnostic ONLY -- not used for hyperparameter selection ***")

    rows: List[Dict] = []

    for run_name, variant in _RUN_SPEC:
        rdir = runs_root / run_name
        ckpt_path = rdir / "checkpoints" / "step_00030000.pt"
        if not ckpt_path.is_file():
            ckpt_path = rdir / "checkpoints" / "last.pt"
        if not ckpt_path.is_file():
            print(f"[ood] {run_name}: no ckpt; skip")
            continue
        print(f"\n[ood] === {run_name} ({variant}) ===  ckpt={ckpt_path.name}")
        state = load_checkpoint(ckpt_path, map_location=device)
        wm_cfg = WMConfig.from_yaml(_REPO_ROOT / "configs" / "wm_medium.yaml").apply_variant(variant)
        train_cfg_dict = state.get("train_config", {})
        precision = str(train_cfg_dict.get("precision", "bf16"))
        if precision == "auto":
            precision = pick_precision(env.gpu, "auto")

        model = RSSMWorldModel(wm_cfg).to(device)
        model.load_state_dict(state["model"])

        has_regime = wm_cfg.heads.regime
        has_cp = wm_cfg.heads.change_point

        for ds_name, ds_root in _DATASETS:
            for split in _SPLITS_TO_EVAL:
                t0 = time.time()
                metrics = _evaluate_split(
                    model, root=Path(ds_root), split=split,
                    chunk_len=args.chunk_len, batch_size=args.batch_size,
                    n_episodes=args.n_episodes, chunks_per_episode=args.chunks_per_episode,
                    seed=42, device=device, precision=precision,
                    has_regime=has_regime, has_cp=has_cp,
                )
                elapsed = time.time() - t0
                row = {
                    "run_name": run_name, "variant": variant,
                    "dataset": ds_name, "split": split,
                    "elapsed_sec": elapsed,
                    **metrics,
                }
                rows.append(row)
                if metrics.get("skipped", 0) > 0.5:
                    print(f"   [{ds_name:<16s} {split:<22s}] (split not present, skip)")
                    continue
                print(f"   [{ds_name:<16s} {split:<22s}] "
                      f"n_ep={int(metrics['n_episodes'])} n_ck={int(metrics['n_chunks'])}  "
                      f"state={metrics.get('state_mse', float('nan')):.3f}  "
                      f"reward={metrics.get('reward_mse', float('nan')):.1f}  "
                      f"reg_acc={metrics.get('regime_accuracy', float('nan')):.3f}  "
                      f"cp_f1@0={metrics.get('cp_f1_at_zero', float('nan')):.3f} (best={metrics.get('cp_best_f1', float('nan')):.3f})  "
                      f"rev_f1@0={metrics.get('reveal_f1_at_zero', float('nan')):.3f}  "
                      f"sh_f1@0={metrics.get('shift_f1_at_zero', float('nan')):.3f}  "
                      f"mm_f1@0={metrics.get('mismatch_f1_at_zero', float('nan')):.3f}  "
                      f"elapsed={elapsed:.1f}s")

        del model
        if device.type == "cuda":
            torch.cuda.empty_cache()

    write_csv(out_dir / "heldout_prediction_diagnostics.csv", rows)
    print(f"\n[ood] wrote {out_dir/'heldout_prediction_diagnostics.csv'} ({len(rows)} rows)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
