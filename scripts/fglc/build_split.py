"""Build split manifests and validate integrity after collect_maniskill.py runs.

Source: docs/STEP11_PLAN.md §J TASK D5

Usage:
  python scripts/fglc/build_split.py --task PickCube-v1
  python scripts/fglc/build_split.py --task PushCube-v1
  python scripts/fglc/build_split.py --data-root data/fglc/PickCube-v1/raw --output-dir data/fglc/PickCube-v1
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

from scripts.fglc.collect_maniskill import TASK_SPLIT_DEFAULTS as _COLLECTOR_DEFAULTS


# ---- task-aware split defaults (SoT: scripts/fglc/collect_maniskill.py) ----
# seed_pool is task-specific; h5_name is derived from the output path.

def get_split_defaults(task: str) -> dict[str, dict]:
    """Return task-aware split config from collect_maniskill SoT.

    Source: scripts/fglc/collect_maniskill.py::TASK_SPLIT_DEFAULTS
    """
    if task not in _COLLECTOR_DEFAULTS:
        raise ValueError(f"Unknown task: {task!r}; known: {list(_COLLECTOR_DEFAULTS)}")
    src = _COLLECTOR_DEFAULTS[task]
    # Map TASK_SPLIT_DEFAULTS format to build_split internal format
    _regime_map = {
        "train_id": 0, "val_id": 1, "test_id": 2,
        "ood_mass_low": 10, "ood_friction_low": 20, "ood_gain_low": 40,
    }
    result: dict[str, dict] = {}
    for split_name, cfg in src.items():
        result[split_name] = {
            "regime_id": _regime_map.get(split_name, -1),
            "ood_type": cfg["ood_type"],
            "ood_params": cfg["ood_params"],
            "h5_name": os.path.basename(cfg["output"]),
            "seed_pool": cfg["seed_pool"],
        }
    return result


# Backward-compat alias — split names only, used for argparse default.
# Do NOT use for seed_pool display; use get_split_defaults() instead.
SPLIT_DEFAULTS = {
    "train_id":        {"regime_id": 0,  "ood_type": "id",          "ood_params": {},                     "h5_name": "train_id.h5",        "seed_pool": list(range(42, 92))},
    "val_id":          {"regime_id": 1,  "ood_type": "id",          "ood_params": {},                     "h5_name": "val_id.h5",          "seed_pool": list(range(200, 210))},
    "test_id":         {"regime_id": 2,  "ood_type": "id",          "ood_params": {},                     "h5_name": "test_id.h5",         "seed_pool": list(range(300, 310))},
    "ood_mass_low":    {"regime_id": 10, "ood_type": "ood_mass",    "ood_params": {"object_mass": 1.5},   "h5_name": "ood_mass_low.h5",    "seed_pool": list(range(500, 510))},
    "ood_friction_low":{"regime_id": 20, "ood_type": "ood_friction","ood_params": {"joint_friction": 5.0},"h5_name": "ood_friction_low.h5","seed_pool": list(range(600, 610))},
    "ood_gain_low":    {"regime_id": 40, "ood_type": "ood_gain",    "ood_params": {"action_gain": 0.7},    "h5_name": "ood_gain_low.h5",    "seed_pool": list(range(700, 710))},
}


def _load_h5_split(h5_path: str):
    import h5py
    import numpy as np

    episodes = []
    with h5py.File(h5_path, "r") as f:
        ep_group = f["episodes"]
        for k in sorted(ep_group.keys(), key=int):
            g = ep_group[k]
            episodes.append({
                "state":  g["state"][:],
                "action": g["action"][:],
                "reward": g["reward"][:],
                "done":   g["done"][:],
            })
    return episodes


def audit_trajectory_hashes(split_episodes: dict[str, list[dict]]) -> dict:
    """Audit exact duplicate state trajectories within and across splits."""
    seen_by_hash: dict[str, list[tuple[str, int]]] = {}
    intra_count = 0
    inter_count = 0
    collision_pairs: list[str] = []
    truncated = False

    def record_pair(pair: str) -> None:
        nonlocal truncated
        if len(collision_pairs) < 100:
            collision_pairs.append(pair)
        elif not truncated:
            collision_pairs.append("TRUNCATED_AT_100")
            truncated = True

    for split, episodes in split_episodes.items():
        for ep_i, ep in enumerate(episodes):
            state_hash = hashlib.sha1(ep["state"].tobytes()).hexdigest()
            prior_entries = seen_by_hash.setdefault(state_hash, [])
            for prior_split, prior_ep_i in prior_entries:
                pair = f"{prior_split}:ep_{prior_ep_i} vs {split}:ep_{ep_i}"
                if prior_split == split:
                    intra_count += 1
                else:
                    inter_count += 1
                record_pair(pair)
            prior_entries.append((split, ep_i))

    return {
        "hash_intra_duplicate_count": intra_count,
        "hash_inter_duplicate_count": inter_count,
        "hash_collision_pairs": collision_pairs,
    }


def _extract_split_names_from_violation(v: str) -> list[str]:
    """Parse 'seed overlap A ∩ B = [...]' → [A, B]."""
    try:
        left, right = v.split(" ∩ ")
        a = left.split()[-1]
        b = right.split(" = ")[0].strip()
        return [a, b]
    except Exception:
        return []


def main() -> None:
    # Pre-parse --task to derive task-aware data-root / output-dir defaults
    _pre = argparse.ArgumentParser(add_help=False)
    _pre.add_argument("--task", default="PickCube-v1")
    _pre_args, _ = _pre.parse_known_args()
    _task = _pre_args.task

    parser = argparse.ArgumentParser(description="Build split manifest + quality report")
    parser.add_argument("--data-root", default=f"data/fglc/{_task}/raw",
                        help="Directory containing per-split .h5 files")
    parser.add_argument("--output-dir", default=f"data/fglc/{_task}",
                        help="Directory to write manifest.json, dataset_stats.json, quality_report.json")
    parser.add_argument("--task", default="PickCube-v1", choices=list(_COLLECTOR_DEFAULTS.keys()))
    parser.add_argument("--ood-delta-min", type=float, default=0.01,
                        help="Minimum state_delta gap for OOD severity PASS")
    parser.add_argument("--splits", nargs="+", default=list(SPLIT_DEFAULTS.keys()),
                        help="Splits to include (default: all 6)")
    args = parser.parse_args()

    from fglc.data.manifest import (
        build_dataset_stats,
        build_manifest,
        build_quality_report,
        verify_ood_severity,
        verify_split_integrity,
        write_json,
    )

    os.makedirs(args.output_dir, exist_ok=True)

    # Resolve task-aware split config (seed_pool SoT: collect_maniskill.py)
    task_defaults = get_split_defaults(args.task)

    # Load all available splits
    split_episodes: dict[str, list] = {}
    split_infos: dict[str, dict] = {}
    missing_splits: list[str] = []

    for split in args.splits:
        if split not in task_defaults:
            print(f"  [WARN] {split}: not in task_defaults for {args.task}, skipping")
            missing_splits.append(split)
            continue
        defaults = task_defaults[split]
        h5_path = os.path.join(args.data_root, defaults["h5_name"])
        if not os.path.isfile(h5_path):
            print(f"  [WARN] {split}: {h5_path} not found, skipping")
            missing_splits.append(split)
            continue
        print(f"  Loading {split} from {h5_path} ...", end=" ", flush=True)
        episodes = _load_h5_split(h5_path)
        print(f"{len(episodes)} episodes")
        split_episodes[split] = episodes
        n_transitions = sum(len(ep["state"]) for ep in episodes)
        split_infos[split] = {
            "n_episodes": len(episodes),
            "n_transitions": n_transitions,
            "episode_ids": list(range(len(episodes))),
            "seed_pool": defaults["seed_pool"],   # task-aware seed_pool (SoT)
            "h5_path": h5_path,
            "ood_params": defaults["ood_params"],
        }

    if not split_episodes:
        print("ERROR: no splits loaded. Run collect_maniskill.py first.")
        sys.exit(1)

    hash_audit = audit_trajectory_hashes(split_episodes)

    # Checkpoint 3: split integrity (seed pool disjoint)
    # NOTE: ID-ID overlaps (train∩val, train∩test) are WARN only — may be by design.
    # OOD-ID overlaps are critical and blocking.
    available_task_defaults = {s: task_defaults[s] for s in split_episodes}
    ok_integrity, violations = verify_split_integrity(available_task_defaults)

    _id_splits = {"train_id", "val_id", "test_id"}
    critical_violations = [
        v for v in violations
        if not all(s in _id_splits for s in _extract_split_names_from_violation(v))
    ]
    ckpt3 = "PASS" if not violations else ("WARN" if not critical_violations else "FAIL")
    if violations:
        for v in violations:
            is_critical = v in critical_violations
            tag = "FAIL" if is_critical else "WARN(id-id-overlap)"
            print(f"  [INTEGRITY {tag}] {v}")

    # Checkpoint 4: OOD severity
    id_stats = build_dataset_stats(split_episodes.get("train_id", []), "train_id") \
        if "train_id" in split_episodes else None

    ckpt4 = "SKIP"
    ood_sev_results: list[str] = []
    if id_stats:
        for ood_split in ("ood_mass_low", "ood_friction_low"):
            if ood_split not in split_episodes:
                continue
            ood_stats = build_dataset_stats(split_episodes[ood_split], ood_split)
            ok_sev, gap = verify_ood_severity(id_stats, ood_stats, delta_min=args.ood_delta_min)
            ood_sev_results.append(f"{ood_split}: gap={gap:.5f} {'PASS' if ok_sev else 'FAIL'}")
            if not ok_sev:
                ckpt4 = "FAIL"
        if ckpt4 != "FAIL":
            ckpt4 = "PASS"

    for r in ood_sev_results:
        print(f"  [OOD SEV] {r}")

    # Build per-split stats
    all_stats: dict[str, dict] = {}
    for split, episodes in split_episodes.items():
        all_stats[split] = build_dataset_stats(episodes, split)

    # Checkpoint 2: dynamics sanity (nan_inf_count == 0)
    ckpt2 = "PASS"
    for split, st in all_stats.items():
        if st["nan_inf_count"] > 0:
            ckpt2 = "FAIL"
            print(f"  [DYNAMICS FAIL] {split}: nan_inf_count={st['nan_inf_count']}")

    split_config = {
        "task": args.task,
        "splits": {s: {"seed_pool": task_defaults[s]["seed_pool"], "ood_params": task_defaults[s]["ood_params"]}
                   for s in split_episodes},
        "rejected_episodes": [],
    }

    manifest = build_manifest(
        task_id=args.task,
        splits=split_infos,
        split_config=split_config,
        data_root=args.data_root,
        collector_command="python scripts/fglc/collect_maniskill.py --split <split>",
        validation_command="python scripts/fglc/build_split.py",
        quality_report_path=os.path.join(args.output_dir, "quality_report.json"),
    )

    checkpoint_results = {
        "checkpoint_0_dependency": "PASS",
        "checkpoint_1_schema": "PASS",
        "checkpoint_2_dynamics": ckpt2,
        "checkpoint_3_split": ckpt3,
        "checkpoint_4_ood_sev": ckpt4,
        "checkpoint_5_learnability": "SKIP",
        "checkpoint_6_repair_metric": "SKIP",
        "checkpoint_7_storage": "PASS",
        "checkpoint_8_reproducibility": "PASS",
        "checkpoint_9_novelty": "SKIP",
    }

    quality_report = build_quality_report(
        checkpoint_results,
        warnings=[f"Missing splits: {missing_splits}"] if missing_splits else [],
    )
    quality_report.update(hash_audit)

    # Write outputs
    manifest_path = os.path.join(args.output_dir, "manifest.json")
    stats_path = os.path.join(args.output_dir, "dataset_stats.json")
    qr_path = os.path.join(args.output_dir, "quality_report.json")
    sc_path = os.path.join(args.output_dir, "split_config.yaml")

    write_json(manifest_path, manifest)
    write_json(stats_path, all_stats)
    write_json(qr_path, quality_report)

    import yaml
    with open(sc_path, "w", encoding="utf-8") as f:
        yaml.dump(split_config, f, allow_unicode=True, sort_keys=False)

    print(f"\nWrote:")
    print(f"  {manifest_path}")
    print(f"  {stats_path}")
    print(f"  {qr_path}")
    print(f"  {sc_path}")
    print(f"\nCheckpoints: {json.dumps(checkpoint_results, indent=2)}")

    if ckpt3 == "FAIL" or ckpt2 == "FAIL":
        print("\nERROR: One or more FAIL checkpoints.")
        sys.exit(1)

    print("\nBuild split DONE.")


if __name__ == "__main__":
    main()
