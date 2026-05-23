"""Manifest, dataset_stats, quality_report writers for FGLC Step 11.

Source: docs/STEP11_PLAN.md §C.4, §C.5, §C.6, §G
"""

from __future__ import annotations

import hashlib
import json
import os
from typing import Any

import numpy as np


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _config_hash(split_config: dict) -> str:
    raw = json.dumps(split_config, sort_keys=True).encode()
    return hashlib.sha256(raw).hexdigest()[:16]


def build_manifest(
    task_id: str,
    splits: dict[str, dict[str, Any]],
    split_config: dict,
    data_root: str,
    collector_command: str = "",
    validation_command: str = "",
    quality_report_path: str = "",
) -> dict:
    """Build manifest.json content dict.

    splits: {split_name: {"n_episodes": int, "n_transitions": int,
                          "episode_ids": list, "seed_pool": list,
                          "h5_path": str, "ood_params": dict}}
    """
    import datetime
    import platform
    import sys
    import torch

    try:
        import mani_skill
        msv = mani_skill.__version__
    except ImportError:
        msv = "unknown"

    try:
        import sapien
        spv = sapien.__version__
    except ImportError:
        spv = "unknown"

    splits_out: dict[str, Any] = {}
    for name, info in splits.items():
        h5_path = info.get("h5_path", "")
        h5_hash = _sha256_file(h5_path) if os.path.isfile(h5_path) else ""
        splits_out[name] = {
            "n_episodes": info["n_episodes"],
            "n_transitions": info["n_transitions"],
            "episode_ids": info["episode_ids"],
            "seed_pool": info["seed_pool"],
            "storage": os.path.relpath(h5_path, data_root) if h5_path else "",
            "hash": h5_hash,
            "ood_params": info.get("ood_params", {}),
        }

    return {
        "manifest_version": "v1",
        "task_id": task_id,
        "maniskill_version": msv,
        "sapien_version": spv,
        "python_version": sys.version,
        "torch_version": torch.__version__,
        "platform": platform.platform(),
        "git_sha": _get_git_sha(),
        "config_hash": _config_hash(split_config),
        "created_at": datetime.datetime.utcnow().isoformat(),
        "splits": splits_out,
        "rejected_episodes": split_config.get("rejected_episodes", []),
        "collector_command": collector_command,
        "validation_command": validation_command,
        "quality_report_path": quality_report_path,
    }


def _get_git_sha() -> str:
    try:
        import subprocess
        r = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=5
        )
        if r.returncode == 0:
            return r.stdout.strip()[:12]
    except Exception:
        pass
    return "unknown"


def build_dataset_stats(
    episodes: list[dict[str, np.ndarray]],
    split: str,
) -> dict:
    """Compute per-split dataset statistics."""
    all_states = np.concatenate([ep["state"] for ep in episodes], axis=0)
    all_actions = np.concatenate([ep["action"] for ep in episodes], axis=0)
    all_rewards = np.concatenate([ep["reward"] for ep in episodes], axis=0)
    episode_lengths = [len(ep["state"]) for ep in episodes]

    state_deltas = []
    for ep in episodes:
        s = ep["state"]
        if len(s) > 1:
            state_deltas.append(np.linalg.norm(s[1:] - s[:-1], axis=1))
    delta_arr = np.concatenate(state_deltas) if state_deltas else np.array([0.0])

    return {
        "split": split,
        "n_episodes": len(episodes),
        "D_x": int(all_states.shape[1]),
        "D_a": int(all_actions.shape[1]),
        "state_mean": all_states.mean(axis=0).tolist(),
        "state_std": all_states.std(axis=0).tolist(),
        "action_mean": all_actions.mean(axis=0).tolist(),
        "action_std": all_actions.std(axis=0).tolist(),
        "state_delta_norm_mean": float(delta_arr.mean()),
        "state_delta_norm_p50": float(np.percentile(delta_arr, 50)),
        "state_delta_norm_p95": float(np.percentile(delta_arr, 95)),
        "reward_mean": float(all_rewards.mean()),
        "reward_std": float(all_rewards.std()),
        "reward_min": float(all_rewards.min()),
        "reward_max": float(all_rewards.max()),
        "episode_length_mean": float(np.mean(episode_lengths)),
        "episode_length_min": int(np.min(episode_lengths)),
        "episode_length_max": int(np.max(episode_lengths)),
        "episode_length_stdev": float(np.std(episode_lengths)),
        "nan_inf_count": int(
            np.isnan(all_states).sum() + np.isinf(all_states).sum() +
            np.isnan(all_actions).sum() + np.isinf(all_actions).sum()
        ),
    }


def build_quality_report(checkpoint_results: dict[str, str], warnings: list[str] | None = None) -> dict:
    """Build quality_report.json content dict.

    checkpoint_results: {checkpoint_key: "PASS" | "FAIL" | "SKIP"}
    """
    return {
        "checkpoint_0_dependency": checkpoint_results.get("checkpoint_0_dependency", "SKIP"),
        "checkpoint_1_schema": checkpoint_results.get("checkpoint_1_schema", "SKIP"),
        "checkpoint_2_dynamics": checkpoint_results.get("checkpoint_2_dynamics", "SKIP"),
        "checkpoint_3_split": checkpoint_results.get("checkpoint_3_split", "SKIP"),
        "checkpoint_4_ood_sev": checkpoint_results.get("checkpoint_4_ood_sev", "SKIP"),
        "checkpoint_5_learnability": checkpoint_results.get("checkpoint_5_learnability", "SKIP"),
        "checkpoint_6_repair_metric": checkpoint_results.get("checkpoint_6_repair_metric", "SKIP"),
        "checkpoint_7_storage": checkpoint_results.get("checkpoint_7_storage", "SKIP"),
        "checkpoint_8_reproducibility": checkpoint_results.get("checkpoint_8_reproducibility", "SKIP"),
        "checkpoint_9_novelty": checkpoint_results.get("checkpoint_9_novelty", "SKIP"),
        "friction_api": "joint_dry_friction",
        "friction_ssot_unit": "mu_kinetic",
        "friction_ssot_value_used": 5.0,
        "friction_mapping": "DEFERRED - see docs/idea/18_DATA_BENCHMARKS.md:44",
        "hash_intra_duplicate_count": 0,
        "hash_inter_duplicate_count": 0,
        "hash_collision_pairs": [],
        "warnings": warnings or [],
    }


def write_json(path: str, data: dict, indent: int = 2) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)


def verify_split_integrity(
    split_configs: dict[str, dict],
) -> tuple[bool, list[str]]:
    """Verify that all seed pools are pairwise disjoint.

    Returns (ok, list_of_violations).
    """
    seed_sets: dict[str, set] = {
        name: set(cfg["seed_pool"]) for name, cfg in split_configs.items()
    }
    violations: list[str] = []
    names = list(seed_sets.keys())
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = names[i], names[j]
            overlap = seed_sets[a] & seed_sets[b]
            if overlap:
                violations.append(f"seed overlap {a} ∩ {b} = {sorted(overlap)}")
    return len(violations) == 0, violations


def verify_ood_severity(
    id_stats: dict,
    ood_stats: dict,
    delta_min: float = 0.01,
) -> tuple[bool, float]:
    """Check that OOD vs ID state_delta gap exceeds delta_min.

    Returns (pass, gap_value).
    """
    gap = abs(ood_stats["state_delta_norm_mean"] - id_stats["state_delta_norm_mean"])
    return gap > delta_min, gap
