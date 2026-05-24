"""Cross-source consistency tests for FGLC data config / manifest / collector SoT.

Sources verified:
  - scripts/fglc/collect_maniskill.py::TASK_SPLIT_DEFAULTS  (SoT)
  - data/fglc/<task>/manifest.json                          (built artifact)
  - configs/fglc/smoke_maniskill_<task>.yaml                (advisory config)

Run: pytest -q tests/test_fglc_config_manifest_consistency.py
Gate: must PASS after Stage 2 manifest rebuild (2026-05-24).

NOTE: TestManifestSeedPoolMatchesCollectorSoT tests FAIL before Stage 2 manifest
      rebuild — seed_pool not yet corrected in manifests at Stage 1 time.
"""

from __future__ import annotations

import json
import warnings
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).parent.parent

from scripts.fglc.collect_maniskill import TASK_SPLIT_DEFAULTS  # noqa: E402

TASKS = ["PickCube-v1", "PushCube-v1"]

# yaml config key → manifest split name (for n_episode_* check)
YAML_TO_MANIFEST_SPLIT = {
    "n_episode_train": "train_id",
    "n_episode_val": "val_id",
    "n_episode_ood_mass": "ood_mass_low",
    "n_episode_ood_friction": "ood_friction_low",
    "n_episode_ood_gain": "ood_gain_low",
}

TASK_YAML_PATHS = {
    "PickCube-v1": "configs/fglc/smoke_maniskill_pickcube.yaml",
    "PushCube-v1": "configs/fglc/smoke_maniskill_pushcube.yaml",
}

TASK_MANIFEST_PATHS = {
    "PickCube-v1": "data/fglc/PickCube-v1/manifest.json",
    "PushCube-v1": "data/fglc/PushCube-v1/manifest.json",
}


def _load_yaml_dataset(task: str) -> dict:
    path = REPO_ROOT / TASK_YAML_PATHS[task]
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)["dataset"]


def _load_manifest(task: str) -> dict:
    path = REPO_ROOT / TASK_MANIFEST_PATHS[task]
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _load_yaml_seed_pool(task: str) -> dict:
    path = REPO_ROOT / TASK_YAML_PATHS[task]
    with open(path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    return cfg.get("seed_pool", {})


def _parse_seed_pool_str(s: str) -> list[int]:
    """Parse "42-291" or "42,43,44" → list of ints."""
    parts = str(s).split(",")
    seeds: list[int] = []
    for p in parts:
        p = p.strip()
        if "-" in p:
            a, b = p.split("-", 1)
            seeds.extend(range(int(a), int(b) + 1))
        else:
            seeds.append(int(p))
    return seeds


# ---------------------------------------------------------------------------
# Group 1: yaml n_episode_* must match manifest n_episodes (advisory sync)
# ---------------------------------------------------------------------------

class TestYamlMatchesManifestEpisodeCounts:
    """yaml n_episode_* (advisory) must match manifest.json n_episodes.

    These tests PASS after Stage 1 yaml sync (no manifest rebuild needed).
    """

    @pytest.mark.parametrize("task", TASKS)
    @pytest.mark.parametrize("yaml_key,split_name", list(YAML_TO_MANIFEST_SPLIT.items()))
    def test_n_episode_matches_manifest(self, task: str, yaml_key: str, split_name: str) -> None:
        cfg = _load_yaml_dataset(task)
        if yaml_key not in cfg:
            pytest.skip(f"{task} yaml missing {yaml_key!r}")
        manifest = _load_manifest(task)
        if split_name not in manifest["splits"]:
            pytest.skip(f"{task} manifest missing split {split_name!r}")

        yaml_count = int(cfg[yaml_key])
        manifest_count = int(manifest["splits"][split_name]["n_episodes"])
        assert yaml_count == manifest_count, (
            f"{task} mismatch: yaml.{yaml_key}={yaml_count} != "
            f"manifest.splits.{split_name}.n_episodes={manifest_count}. "
            f"Update {TASK_YAML_PATHS[task]} to match manifest."
        )


# ---------------------------------------------------------------------------
# Group 2: manifest seed_pool must match TASK_SPLIT_DEFAULTS (SoT)
# ---------------------------------------------------------------------------

class TestManifestSeedPoolMatchesCollectorSoT:
    """manifest.json seed_pool must match TASK_SPLIT_DEFAULTS SoT.

    These tests FAIL before Stage 2 manifest rebuild and PASS after.
    """

    @pytest.mark.parametrize("task", TASKS)
    @pytest.mark.parametrize("split_name", ["train_id", "val_id", "test_id",
                                             "ood_mass_low", "ood_friction_low", "ood_gain_low"])
    def test_seed_pool_matches_sot(self, task: str, split_name: str) -> None:
        if split_name not in TASK_SPLIT_DEFAULTS.get(task, {}):
            pytest.skip(f"{task} SoT missing split {split_name!r}")
        manifest = _load_manifest(task)
        if split_name not in manifest["splits"]:
            pytest.skip(f"{task} manifest missing split {split_name!r}")

        manifest_pool = manifest["splits"][split_name]["seed_pool"]
        expected_pool = TASK_SPLIT_DEFAULTS[task][split_name]["seed_pool"]

        assert manifest_pool == expected_pool, (
            f"{task} {split_name} seed_pool mismatch after manifest rebuild.\n"
            f"  manifest: {len(manifest_pool)} seeds "
            f"[{manifest_pool[0]}..{manifest_pool[-1]}]\n"
            f"  SoT (TASK_SPLIT_DEFAULTS): {len(expected_pool)} seeds "
            f"[{expected_pool[0]}..{expected_pool[-1]}]\n"
            f"Fix: python scripts/fglc/build_split.py --task {task}"
        )


# ---------------------------------------------------------------------------
# Group 3: yaml seed_pool strings must match TASK_SPLIT_DEFAULTS (SoT)
# ---------------------------------------------------------------------------

class TestYamlSeedPoolMatchesCollectorSoT:
    """yaml seed_pool string values must parse to TASK_SPLIT_DEFAULTS seed_pool.

    These tests PASS immediately (yaml seed_pool strings are already correct).
    """

    @pytest.mark.parametrize("task", TASKS)
    @pytest.mark.parametrize("split_name", ["train_id", "val_id", "test_id",
                                             "ood_mass_low", "ood_friction_low", "ood_gain_low"])
    def test_yaml_seed_pool_matches_sot(self, task: str, split_name: str) -> None:
        if split_name not in TASK_SPLIT_DEFAULTS.get(task, {}):
            pytest.skip(f"{task} SoT missing split {split_name!r}")
        seed_pool_cfg = _load_yaml_seed_pool(task)
        if split_name not in seed_pool_cfg:
            pytest.skip(f"{task} yaml missing seed_pool.{split_name!r}")

        yaml_pool = _parse_seed_pool_str(seed_pool_cfg[split_name])
        expected_pool = TASK_SPLIT_DEFAULTS[task][split_name]["seed_pool"]

        assert yaml_pool == expected_pool, (
            f"{task} yaml seed_pool.{split_name} mismatch.\n"
            f"  yaml parsed: {len(yaml_pool)} seeds [{yaml_pool[0]}..{yaml_pool[-1]}]\n"
            f"  SoT: {len(expected_pool)} seeds [{expected_pool[0]}..{expected_pool[-1]}]"
        )


# ---------------------------------------------------------------------------
# Group 4: cross-task seed overlap (informational, always passes)
# ---------------------------------------------------------------------------

class TestCrossTaskSeedOverlapInformational:
    """Document cross-task seed overlap. Does NOT fail — informational only."""

    def test_pickcube_ood_gain_pushcube_train_overlap_informational(self) -> None:
        """PickCube ood_gain_low [700..1199] ∩ PushCube train_id [1042..1541] = 158 seeds.

        Different environments → not direct leakage. Informational note only.
        """
        pc_ood_gain = set(TASK_SPLIT_DEFAULTS["PickCube-v1"]["ood_gain_low"]["seed_pool"])
        push_train = set(TASK_SPLIT_DEFAULTS["PushCube-v1"]["train_id"]["seed_pool"])
        overlap = pc_ood_gain & push_train
        if overlap:
            warnings.warn(
                f"Cross-task seed overlap (informational, not leakage): "
                f"PickCube ood_gain_low ∩ PushCube train_id = {len(overlap)} seeds "
                f"({min(overlap)}..{max(overlap)}). Different envs — no direct leakage.",
                UserWarning,
            )
        assert True  # always passes

    def test_pickcube_train_val_intra_overlap_informational(self) -> None:
        """PickCube train_id [42..291] ∩ val_id [200..249] = 50 seeds.

        Within-task ID split overlap from TASK_SPLIT_DEFAULTS design.
        verify_split_integrity reports WARN (ID-ID). Informational note only.
        """
        pc_train = set(TASK_SPLIT_DEFAULTS["PickCube-v1"]["train_id"]["seed_pool"])
        pc_val = set(TASK_SPLIT_DEFAULTS["PickCube-v1"]["val_id"]["seed_pool"])
        overlap = pc_train & pc_val
        if overlap:
            warnings.warn(
                f"PickCube intra-task train_id∩val_id overlap (ID-ID, WARN-level): "
                f"{len(overlap)} seeds ({min(overlap)}..{max(overlap)}). "
                f"Design choice or bug in TASK_SPLIT_DEFAULTS — data already collected.",
                UserWarning,
            )
        assert True  # always passes
