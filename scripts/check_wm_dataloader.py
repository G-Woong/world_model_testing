"""Smoke / safety check for the WM dataloader (no training).

본 스크립트는 다음을 검증한다:
    1) ``WMDataConfig.from_yaml(args.data_config)`` 로드.
    2) train / valid loader 생성 (``num_workers=0`` 단일 process).
    3) batch ``args.num_batches``개 sampling.
    4) 각 batch의 input/target dict 구조 / shape / dtype을 출력.
    5) sample_weight 통계 + event-window sampler type 분포 출력.
    6) 모든 forbidden key가 batch["inputs"]에 들어 있지 않은지 검증.
    7) split이 train/valid만 사용되는지 검증.
    8) (옵션) RSSMWorldModel.forward를 1회 실행하여 shape이 일치하는지 확인 (학습 X, backward X).
    9) (옵션) ``--inject-bad-split test_id``로 forbidden split을 강제 주입했을 때 ValueError가
       발생하는지 확인 (negative test).

PART0 §3 정합:
    - dataset_loader가 학습용 split만 yield 한다는 사실을 unit-level로 검증.
    - test_id / OOD를 inject 하면 즉시 raise.
    - collector_metadata 등 forbidden key가 inputs에 들어가지 않음을 hard 검사.
    - optimizer.step / loss.backward 없음 (smoke 한정 forward 1회만 허용).
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Mapping

import torch
from torch.utils.data import DataLoader

# project root를 path에 추가 (rg4f / wm 패키지 import 가능하도록)
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from falsifiable_regime_world_model.wm import (  # noqa: E402
    ALLOWED_TRAIN_SPLITS,
    FORBIDDEN_INPUT_KEYS,
    FORBIDDEN_TRAIN_SPLITS,
    RSSMWorldModel,
    WMConfig,
    WMDataConfig,
    build_chunk_dataset,
    build_source_indices,
    collate_chunks,
)


# =============================================================================
# 1. dataloader 만들기
# =============================================================================


def make_dataloader(
    cfg: WMDataConfig,
    split: str,
    *,
    epoch: int = 0,
):
    if split not in ALLOWED_TRAIN_SPLITS:
        raise ValueError(
            f"Split leakage detected: test_id/OOD splits must not be used "
            f"for training loaders. Got: {split!r}."
        )
    sources = build_source_indices(cfg)
    ds = build_chunk_dataset(cfg, split, epoch=epoch, sources=sources)
    split_cfg = cfg.train if split == "train" else cfg.valid
    return DataLoader(
        ds,
        batch_size=split_cfg.batch_size,
        num_workers=int(split_cfg.num_workers),
        collate_fn=collate_chunks,
        drop_last=split_cfg.drop_last,
    )


# =============================================================================
# 2. batch 검사 (assertion + 출력)
# =============================================================================


def inspect_batch(batch: Mapping[str, Any], expected_split: str) -> Dict[str, Any]:
    """batch dict 1개에 대해 구조/shape/dtype/forbidden key 검사 후 통계 dict 반환.

    raise on first violation.
    """
    # --- 구조 ---
    for top_key in ("inputs", "targets", "sample_weight", "valid_mask", "meta"):
        assert top_key in batch, f"missing top-level key: {top_key}"
    inputs = batch["inputs"]
    targets = batch["targets"]
    meta = batch["meta"]

    # --- forbidden key가 inputs에 있는지 ---
    leaked = [k for k in inputs.keys() if k in FORBIDDEN_INPUT_KEYS]
    assert not leaked, f"FORBIDDEN INPUT KEY LEAK: {leaked}"

    # --- split guard ---
    seen_splits = set(meta["split"])
    bad_splits = seen_splits & set(FORBIDDEN_TRAIN_SPLITS)
    assert not bad_splits, f"BAD SPLITS in batch meta: {sorted(bad_splits)}"
    if expected_split not in seen_splits:
        # (보통은 단일 split만 들어와야 함)
        raise AssertionError(
            f"batch meta.split does not contain expected split {expected_split!r}; "
            f"got {sorted(seen_splits)}"
        )

    # --- shape / dtype ---
    B, T = inputs["local_grid"].shape[:2]
    assert inputs["local_grid"].shape == (B, T, 5, 5, 10), inputs["local_grid"].shape
    assert inputs["scalar"].shape == (B, T, 14), inputs["scalar"].shape
    assert inputs["event_token"].shape == (B, T)
    assert inputs["action_raw"].shape == (B, T)
    assert inputs["action_prev_raw"].shape == (B, T)
    assert inputs["local_grid"].dtype == torch.float32
    assert inputs["scalar"].dtype == torch.float32
    assert inputs["event_token"].dtype == torch.long
    assert inputs["action_raw"].dtype == torch.long
    assert inputs["action_prev_raw"].dtype == torch.long

    # action_prev_raw[t=0] must be 0 (right-shift)
    assert torch.all(inputs["action_prev_raw"][:, 0] == 0), \
        "action_prev_raw[:, 0] should be 0 after right-shift"

    # targets contract
    assert targets["true_state"].shape == (B, T, 5)
    assert targets["true_regime_control_mode"].dtype == torch.long
    for k in ("change_point", "reveal_event", "shift_event", "raw_eff_mismatch", "done", "reward"):
        assert targets[k].shape == (B, T), f"targets[{k}].shape = {targets[k].shape}"
        assert targets[k].dtype == torch.float32, f"targets[{k}].dtype = {targets[k].dtype}"

    # raw_eff_mismatch == (action_raw != action_effective) 검증은 chunk_arrays에 actions_effective가
    # 있으면 collate에서 이미 만들어 줌. 여기서는 raw_eff_mismatch가 0/1 binary float인지만 확인.
    mm = targets["raw_eff_mismatch"]
    assert torch.all((mm == 0.0) | (mm == 1.0)), \
        "raw_eff_mismatch should be binary float in {0,1}"

    # sample_weight / valid_mask
    sw = batch["sample_weight"]
    vm = batch["valid_mask"]
    assert sw.shape == (B, T) and sw.dtype == torch.float32
    assert vm.shape == (B, T) and vm.dtype == torch.float32

    # padding 위치 sample_weight=0
    invalid = (vm == 0.0)
    assert torch.all(sw[invalid] == 0.0), "sample_weight at padding tick must be 0"

    # change-point가 있는 batch에서 sample_weight boost 적용 여부
    cp = targets["change_point"]
    boost_check = "no_change_point_in_batch"
    if torch.any(cp > 0):
        # change_point가 1인 위치의 sw가 base_weight(1.0)보다 큰 게 적어도 일부는 있어야 함.
        # (cp_boost=5.0, weight_cap=10.0 default일 때 sw는 5.0이 되어야 함)
        sw_at_cp = sw[cp > 0]
        # sample_weight_boost가 enabled면 평균이 1.0보다 커야 함.
        if torch.mean(sw_at_cp) > 1.01:
            boost_check = f"PASS mean_sw_at_cp={float(torch.mean(sw_at_cp)):.2f}"
        else:
            boost_check = f"WEAK mean_sw_at_cp={float(torch.mean(sw_at_cp)):.2f}"

    # source 분포
    src_counts = Counter(meta["source_name"])
    sampler_types = Counter(meta["sampler_type"])
    return {
        "B": B, "T": T,
        "split": list(seen_splits),
        "source_dist": dict(src_counts),
        "sampler_types": dict(sampler_types),
        "sample_weight": {
            "min": float(sw.min().item()),
            "mean": float(sw.mean().item()),
            "max": float(sw.max().item()),
        },
        "valid_mask_mean": float(vm.mean().item()),
        "events": {
            "change_point": int(cp.sum().item()),
            "reveal": int(targets["reveal_event"].sum().item()),
            "shift": int(targets["shift_event"].sum().item()),
            "done": int(targets["done"].sum().item()),
            "raw_eff_mismatch": int(mm.sum().item()),
        },
        "boost_check": boost_check,
    }


# =============================================================================
# 3. (옵션) RSSMWorldModel forward 1회
# =============================================================================


def smoke_forward_with_model(
    batch: Mapping[str, Any],
    wm_cfg: WMConfig,
    device: torch.device,
) -> Dict[str, Any]:
    model = RSSMWorldModel(wm_cfg).to(device).eval()
    inputs = {k: v.to(device) for k, v in batch["inputs"].items()}
    with torch.no_grad():
        out = model(inputs)
    return {
        "forward_keys": sorted(out.keys()),
        "h_shape": tuple(out["h"].shape),
        "z_shape": tuple(out["z"].shape),
        "reward_pred_shape": tuple(out["reward_pred"].shape) if "reward_pred" in out else None,
    }


# =============================================================================
# 4. main
# =============================================================================


def main() -> int:
    parser = argparse.ArgumentParser(description="WM dataloader smoke / safety check.")
    parser.add_argument("--data-config", type=str, required=True, help="configs/wm_data_stage*.yaml")
    parser.add_argument("--wm-config", type=str, default=None,
                        help="(optional) configs/wm_*.yaml to run a forward smoke")
    parser.add_argument("--num-batches", type=int, default=2, help="batch 수 (train + valid 각각)")
    parser.add_argument("--device", type=str, default="cpu", help="cpu | cuda — forward smoke용")
    parser.add_argument(
        "--inject-bad-split", type=str, default=None,
        help="negative test: 강제로 forbidden split을 inject하여 ValueError 발생을 확인",
    )
    parser.add_argument(
        "--expect-fail", action="store_true",
        help="--inject-bad-split와 함께 사용. ValueError가 나야 PASS, 안 나면 FAIL.",
    )
    args = parser.parse_args()

    # --- (negative) bad split injection ---
    if args.inject_bad_split:
        # Path 1: WMDataConfig는 splits를 직접 받지 않지만, validate(extra_split_names=...)
        # 또는 build_chunk_dataset(split=...)으로 inject 가능. 두 가지 모두 시도한다.
        cfg = WMDataConfig.from_yaml(args.data_config)
        try:
            cfg.validate(extra_split_names=[args.inject_bad_split])
            try:
                build_chunk_dataset(cfg, split=args.inject_bad_split)
                print(f"[NEG] FAIL: build_chunk_dataset accepted bad split={args.inject_bad_split}")
                return 1
            except ValueError as e:
                print(f"[NEG] PASS: build_chunk_dataset raised ValueError as expected.")
                print(f"        message: {e}")
                return 0
        except ValueError as e:
            print(f"[NEG] PASS: WMDataConfig.validate raised ValueError as expected.")
            print(f"        message: {e}")
            return 0

    # --- positive path ---
    cfg = WMDataConfig.from_yaml(args.data_config)
    print(f"[data] config={args.data_config}  name={cfg.name}")
    print(f"[data] sources:")
    for s in cfg.sources:
        print(f"        - {s.name:<20s} root={s.root}  "
              f"train_w={s.train_weight}  valid_w={s.valid_weight}")
    print(f"[data] train.chunk_len={cfg.train.chunk_len}  batch_size={cfg.train.batch_size}  "
          f"chunks_per_epoch={cfg.train.chunks_per_epoch}")
    print(f"[data] valid.chunk_len={cfg.valid.chunk_len}  batch_size={cfg.valid.batch_size}  "
          f"chunks_per_epoch={cfg.valid.chunks_per_epoch}")

    overall_ok = True
    for split in ("train", "valid"):
        print(f"\n========== split={split} ==========")
        loader = make_dataloader(cfg, split)
        it = iter(loader)
        agg_src = Counter()
        agg_sampler = Counter()
        for b_idx in range(args.num_batches):
            try:
                batch = next(it)
            except StopIteration:
                print(f"[{split}] StopIteration before reaching {args.num_batches} batches.")
                break
            stats = inspect_batch(batch, expected_split=split)
            print(f"[{split}] batch {b_idx}: B={stats['B']} T={stats['T']}  "
                  f"src={stats['source_dist']}  events={stats['events']}  "
                  f"sw={stats['sample_weight']}  vm_mean={stats['valid_mask_mean']:.3f}  "
                  f"boost={stats['boost_check']}")
            print(f"[{split}]   sampler_types={stats['sampler_types']}")
            agg_src.update(stats["source_dist"])
            agg_sampler.update(stats["sampler_types"])
            if "WEAK" in stats["boost_check"]:
                # 단일 batch에서 cp가 chunk-끝에 위치해 boost 영역이 valid_len 밖으로 나가는 경우가
                # 있을 수 있음 → 경고만 출력하고 FAIL 처리하지 않는다.
                print(f"[{split}]   (warn) sample_weight boost가 약하게 적용된 batch 발견.")

        # source 비율 vs config weight 비교
        weights = cfg.normalized_weights(split)
        weight_map = {s.name: w for s, w in zip(cfg.sources, weights)}
        total = sum(agg_src.values())
        if total > 0:
            print(f"[{split}] source 분포 (총 {total} chunks):")
            for name, w in weight_map.items():
                actual = agg_src.get(name, 0) / total
                print(f"   - {name:<20s} expected={w:.2f}  actual={actual:.2f}")
        print(f"[{split}] sampler-type 분포 (총 {sum(agg_sampler.values())} chunks):")
        for k, v in sorted(agg_sampler.items()):
            print(f"   - {k:<28s} {v}")

    # --- (옵션) model forward smoke ---
    if args.wm_config:
        print("\n========== model forward smoke ==========")
        wm_cfg = WMConfig.from_yaml(args.wm_config)
        device = torch.device(args.device if (args.device == "cpu" or torch.cuda.is_available()) else "cpu")
        loader = make_dataloader(cfg, "train")
        batch = next(iter(loader))
        info = smoke_forward_with_model(batch, wm_cfg, device)
        print(f"[fwd] device={device}")
        print(f"[fwd] forward_keys={info['forward_keys']}")
        print(f"[fwd] h_shape={info['h_shape']}  z_shape={info['z_shape']}  "
              f"reward_pred_shape={info['reward_pred_shape']}")

    print(f"\n[wm-data] {'PASS' if overall_ok else 'FAIL'}: dataloader smoke complete.")
    return 0 if overall_ok else 1


if __name__ == "__main__":
    sys.exit(main())
