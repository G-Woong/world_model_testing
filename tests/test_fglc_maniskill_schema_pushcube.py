"""Schema and split-defaults tests for PushCube-v1 support.

Tests run without mani-skill installed (pure Python, no env execution).
Source: plans/fglc-step-vectorized-iverson.md §K TASK Q6 REQUIRED_TESTS [T2]
"""

from __future__ import annotations


def test_task_ood_params_has_pushcube():
    """TASK_OOD_PARAMS must include PushCube-v1 with ood_mass_low."""
    from fglc.data.maniskill_schema import TASK_OOD_PARAMS

    assert "PushCube-v1" in TASK_OOD_PARAMS, "PushCube-v1 missing from TASK_OOD_PARAMS"
    assert "ood_mass_low" in TASK_OOD_PARAMS["PushCube-v1"]
    assert TASK_OOD_PARAMS["PushCube-v1"]["ood_mass_low"]["object_mass"] == 1.5


def test_pickcube_ood_params_backward_compat():
    """OOD_PARAMS alias must equal TASK_OOD_PARAMS['PickCube-v1']."""
    from fglc.data.maniskill_schema import OOD_PARAMS, TASK_OOD_PARAMS

    assert OOD_PARAMS is TASK_OOD_PARAMS["PickCube-v1"], (
        "OOD_PARAMS alias broken: must be TASK_OOD_PARAMS['PickCube-v1']"
    )


def test_task_split_defaults_pushcube():
    """TASK_SPLIT_DEFAULTS must include PushCube-v1 with all 5 splits."""
    from scripts.fglc.collect_maniskill import TASK_SPLIT_DEFAULTS, SPLIT_DEFAULTS

    assert "PushCube-v1" in TASK_SPLIT_DEFAULTS, "PushCube-v1 missing from TASK_SPLIT_DEFAULTS"
    pc = TASK_SPLIT_DEFAULTS["PushCube-v1"]
    for split in ("train_id", "val_id", "test_id", "ood_mass_low", "ood_friction_low"):
        assert split in pc, f"PushCube split '{split}' missing"
        assert "PushCube-v1" in pc[split]["output"], (
            f"PushCube split '{split}' output path must contain 'PushCube-v1'"
        )
    # PickCube backward compat
    assert SPLIT_DEFAULTS is TASK_SPLIT_DEFAULTS["PickCube-v1"], (
        "SPLIT_DEFAULTS alias broken: must be TASK_SPLIT_DEFAULTS['PickCube-v1']"
    )


def test_pushcube_pickcube_seed_disjoint():
    """PushCube and PickCube seed pools must be completely disjoint."""
    from scripts.fglc.collect_maniskill import TASK_SPLIT_DEFAULTS

    pc_seeds: set[int] = set()
    for v in TASK_SPLIT_DEFAULTS["PickCube-v1"].values():
        pc_seeds.update(v["seed_pool"])

    push_seeds: set[int] = set()
    for v in TASK_SPLIT_DEFAULTS["PushCube-v1"].values():
        push_seeds.update(v["seed_pool"])

    overlap = pc_seeds & push_seeds
    assert not overlap, f"PickCube and PushCube seed pools overlap: {sorted(overlap)[:10]}"
