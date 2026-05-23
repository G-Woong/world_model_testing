"""ManiSkill state-only episode collection script for FGLC Step 11.

Source: docs/STEP11_PLAN.md §J TASK D4

Usage:
  python scripts/fglc/collect_maniskill.py --split train_id --n-episodes 50
  python scripts/fglc/collect_maniskill.py --split ood_mass_low --ood-mass 1.5 --n-episodes 10
  python scripts/fglc/collect_maniskill.py --split ood_friction_low --ood-friction 5.0 --n-episodes 10
  python scripts/fglc/collect_maniskill.py --split train_id --n-episodes 5 --no-save  # probe
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime


def _parse_seed_pool(s: str) -> list[int]:
    parts = s.split(",")
    seeds = []
    for p in parts:
        p = p.strip()
        if "-" in p:
            a, b = p.split("-")
            seeds.extend(range(int(a), int(b) + 1))
        else:
            seeds.append(int(p))
    return seeds


SPLIT_DEFAULTS = {
    "train_id": {
        "n_episodes": 50,
        "seed_pool": list(range(42, 92)),
        "regime_id": 0,
        "ood_type": "id",
        "ood_params": {},
        "output": "data/fglc/PickCube-v1/raw/train_id.h5",
    },
    "val_id": {
        "n_episodes": 10,
        "seed_pool": list(range(200, 210)),
        "regime_id": 1,
        "ood_type": "id",
        "ood_params": {},
        "output": "data/fglc/PickCube-v1/raw/val_id.h5",
    },
    "test_id": {
        "n_episodes": 10,
        "seed_pool": list(range(300, 310)),
        "regime_id": 2,
        "ood_type": "id",
        "ood_params": {},
        "output": "data/fglc/PickCube-v1/raw/test_id.h5",
    },
    "ood_mass_low": {
        "n_episodes": 10,
        "seed_pool": list(range(500, 510)),
        "regime_id": 10,
        "ood_type": "ood_mass",
        "ood_params": {"object_mass": 1.5},
        "output": "data/fglc/PickCube-v1/raw/ood_mass_low.h5",
    },
    "ood_friction_low": {
        "n_episodes": 10,
        "seed_pool": list(range(600, 610)),
        "regime_id": 20,
        "ood_type": "ood_friction",
        "ood_params": {"joint_friction": 5.0},
        "output": "data/fglc/PickCube-v1/raw/ood_friction_low.h5",
    },
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect ManiSkill state-only episodes")
    parser.add_argument("--task", default="PickCube-v1")
    parser.add_argument("--split", default="train_id", choices=list(SPLIT_DEFAULTS.keys()))
    parser.add_argument("--n-episodes", type=int, default=None)
    parser.add_argument("--seed-pool", type=str, default=None,
                        help="comma-separated or range: 42,43 or 42-91")
    parser.add_argument("--ood-mass", type=float, default=None, help="object_mass override")
    parser.add_argument("--ood-friction", type=float, default=None, help="joint_friction override")
    parser.add_argument("--output", type=str, default=None, help="HDF5 output path")
    parser.add_argument("--no-save", action="store_true", help="probe mode: collect but don't save")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--max-wall-minutes", type=float, default=20.0)
    args = parser.parse_args()

    defaults = SPLIT_DEFAULTS[args.split].copy()
    n_episodes = args.n_episodes or defaults["n_episodes"]
    seed_pool = _parse_seed_pool(args.seed_pool) if args.seed_pool else defaults["seed_pool"]
    ood_params = defaults["ood_params"].copy()
    if args.ood_mass is not None:
        ood_params["object_mass"] = args.ood_mass
    if args.ood_friction is not None:
        ood_params["joint_friction"] = args.ood_friction
    output = args.output or defaults["output"]

    from fglc.data.collector import CollectionConfig, collect_episodes, save_episodes_h5

    config = CollectionConfig(
        task=args.task,
        split=args.split,
        n_episodes=n_episodes,
        seed_pool=seed_pool,
        ood_params=ood_params,
        regime_id=defaults["regime_id"],
        ood_type=defaults["ood_type"],
        wall_clock_limit_seconds=args.max_wall_minutes * 60.0,
    )

    print(f"[collect_maniskill] split={args.split} n_episodes={n_episodes} ood_params={ood_params}")
    episodes, eval_metas, stats = collect_episodes(config, verbose=args.verbose)

    summary = {
        "split": args.split,
        "n_accepted": stats.n_accepted,
        "n_rejected": stats.n_rejected,
        "rejection_counts": stats.rejection_counts,
        "total_transitions": stats.total_transitions,
        "wall_clock_seconds": round(stats.wall_clock_seconds, 2),
        "output": output if not args.no_save else "NOT_SAVED",
        "timestamp": datetime.utcnow().isoformat(),
    }

    if args.no_save:
        print(json.dumps(summary, indent=2))
        return

    if stats.n_accepted == 0:
        print("ERROR: 0 episodes accepted. Check collector logic and OOD params.")
        sys.exit(1)

    save_episodes_h5(episodes, eval_metas, output)
    print(json.dumps(summary, indent=2))
    print(f"[collect_maniskill] Saved to {output}")


if __name__ == "__main__":
    main()
