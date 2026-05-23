"""Checkpoint 0: dependency import probe for Step 11 ManiSkill pipeline.

Source: docs/STEP11_PLAN.md §E Checkpoint 0, §I.2
Skipped automatically if mani-skill is not installed (CI safety).
"""

from __future__ import annotations

import importlib
import pytest


_MANISKILL_AVAILABLE = importlib.util.find_spec("mani_skill") is not None
_SAPIEN_AVAILABLE = importlib.util.find_spec("sapien") is not None
_H5PY_AVAILABLE = importlib.util.find_spec("h5py") is not None

skip_no_maniskill = pytest.mark.skipif(
    not _MANISKILL_AVAILABLE, reason="mani-skill not installed"
)
skip_no_sapien = pytest.mark.skipif(
    not _SAPIEN_AVAILABLE, reason="sapien not installed"
)
skip_no_h5py = pytest.mark.skipif(
    not _H5PY_AVAILABLE, reason="h5py not installed"
)


def test_h5py_importable():
    """h5py must be importable and meet minimum version."""
    import h5py  # noqa: PLC0415
    major, minor, _ = (int(x) for x in h5py.__version__.split(".")[:3])
    assert (major, minor) >= (3, 9), f"h5py >= 3.9 required, got {h5py.__version__}"


def test_gymnasium_importable():
    """gymnasium 1.2.3 must be importable."""
    import gymnasium as gym  # noqa: PLC0415
    assert gym.__version__ == "1.2.3", f"gymnasium pin mismatch: {gym.__version__}"


def test_hydra_importable():
    """hydra-core must be importable."""
    import hydra  # noqa: PLC0415
    major, minor, _ = (int(x) for x in hydra.__version__.split(".")[:3])
    assert (major, minor) >= (1, 3), f"hydra >= 1.3 required, got {hydra.__version__}"


def test_omegaconf_importable():
    """omegaconf must be importable."""
    import omegaconf  # noqa: PLC0415
    major, minor, _ = (int(x) for x in omegaconf.__version__.split(".")[:3])
    assert (major, minor) >= (2, 3), f"omegaconf >= 2.3 required, got {omegaconf.__version__}"


@skip_no_maniskill
def test_maniskill_version():
    """mani-skill >= 3.0.0 must be installed."""
    import mani_skill  # noqa: PLC0415
    version_str = mani_skill.__version__
    major = int(version_str.split(".")[0])
    assert major >= 3, f"mani-skill >= 3.x required, got {version_str}"


@skip_no_sapien
def test_sapien_version():
    """sapien >= 3.0.0 must be installed."""
    import sapien  # noqa: PLC0415
    version_str = sapien.__version__
    major = int(version_str.split(".")[0])
    assert major >= 3, f"sapien >= 3.x required, got {version_str}"


@skip_no_maniskill
def test_pickcube_task_registers():
    """PickCube-v1 must be registered in gymnasium after mani_skill.envs import."""
    import warnings
    warnings.filterwarnings("ignore")
    import gymnasium as gym  # noqa: PLC0415
    import mani_skill.envs  # noqa: F401, PLC0415

    all_ids = gym.registry.keys()
    assert "PickCube-v1" in all_ids, "PickCube-v1 not in gymnasium registry"


@skip_no_maniskill
def test_pickcube_state_dict_reset():
    """PickCube-v1 must reset with state_dict obs_mode and return dict obs."""
    import warnings
    warnings.filterwarnings("ignore")
    import gymnasium as gym  # noqa: PLC0415
    import mani_skill.envs  # noqa: F401, PLC0415

    env = gym.make("PickCube-v1", obs_mode="state_dict")
    try:
        obs, info = env.reset(seed=42)
        assert isinstance(obs, dict), f"Expected dict obs, got {type(obs)}"
        assert "agent" in obs, f"Expected 'agent' key, got {list(obs.keys())}"
        assert "extra" in obs, f"Expected 'extra' key, got {list(obs.keys())}"
    finally:
        env.close()


@skip_no_maniskill
def test_pickcube_dx_da():
    """PickCube-v1 must have D_x=42 and D_a=8."""
    import warnings
    warnings.filterwarnings("ignore")
    import gymnasium as gym  # noqa: PLC0415
    import mani_skill.envs  # noqa: F401, PLC0415
    import numpy as np

    def flat(d):
        if isinstance(d, dict):
            return np.concatenate([flat(v) for k, v in sorted(d.items())])
        v = d.cpu().numpy() if hasattr(d, "cpu") else np.array(d)
        return v.flatten().astype(np.float32)

    env = gym.make("PickCube-v1", obs_mode="state_dict")
    try:
        obs, _ = env.reset(seed=42)
        D_x = flat(obs).shape[0]
        D_a = env.action_space.shape[0]
        assert D_x == 42, f"Expected D_x=42, got {D_x}"
        assert D_a == 8, f"Expected D_a=8, got {D_a}"
    finally:
        env.close()


@skip_no_maniskill
def test_pickcube_seed_reproducibility():
    """Same seed must produce identical state trajectories."""
    import warnings
    warnings.filterwarnings("ignore")
    import gymnasium as gym  # noqa: PLC0415
    import mani_skill.envs  # noqa: F401, PLC0415
    import numpy as np

    def flat(d):
        if isinstance(d, dict):
            return np.concatenate([flat(v) for k, v in sorted(d.items())])
        v = d.cpu().numpy() if hasattr(d, "cpu") else np.array(d)
        return v.flatten().astype(np.float32)

    env1 = gym.make("PickCube-v1", obs_mode="state_dict")
    env2 = gym.make("PickCube-v1", obs_mode="state_dict")
    try:
        env1.reset(seed=99)
        env2.reset(seed=99)
        actions = [env1.action_space.sample() for _ in range(5)]
        for a in actions:
            o1, _, t1, tr1, _ = env1.step(a)
            o2, _, _, _, _ = env2.step(a)
            diff = np.max(np.abs(flat(o1) - flat(o2)))
            assert diff < 1e-5, f"Seed not reproducible: max_diff={diff}"
            if hasattr(t1, "item") and t1.item():
                break
    finally:
        env1.close()
        env2.close()


@skip_no_maniskill
def test_ood_mass_api():
    """cube.set_mass(1.5) must cause dynamics divergence from ID."""
    import warnings
    warnings.filterwarnings("ignore")
    import gymnasium as gym  # noqa: PLC0415
    import mani_skill.envs  # noqa: F401, PLC0415
    import numpy as np

    def flat(d):
        if isinstance(d, dict):
            return np.concatenate([flat(v) for k, v in sorted(d.items())])
        v = d.cpu().numpy() if hasattr(d, "cpu") else np.array(d)
        return v.flatten().astype(np.float32)

    fixed_action = np.array([0.5, -0.3, -0.5, 0.0, 0.0, 0.2, 0.3, 1.0], dtype=np.float32)
    n = 15

    env_id = gym.make("PickCube-v1", obs_mode="state_dict")
    env_id.reset(seed=42)
    id_states = [flat(env_id.step(fixed_action)[0]) for _ in range(n)]
    env_id.close()

    env_ood = gym.make("PickCube-v1", obs_mode="state_dict")
    env_ood.reset(seed=42)
    env_ood.unwrapped.cube.set_mass(1.5)
    ood_states = [flat(env_ood.step(fixed_action)[0]) for _ in range(n)]
    env_ood.close()

    diffs = [np.linalg.norm(s1 - s2) for s1, s2 in zip(id_states, ood_states)]
    assert max(diffs) > 1e-4, f"Mass OOD had no effect: max L2 diff={max(diffs):.2e}"


@skip_no_maniskill
def test_ood_joint_friction_api():
    """art.joints[i].set_friction(5.0) must cause dynamics divergence from ID."""
    import warnings
    warnings.filterwarnings("ignore")
    import gymnasium as gym  # noqa: PLC0415
    import mani_skill.envs  # noqa: F401, PLC0415
    import numpy as np

    def flat(d):
        if isinstance(d, dict):
            return np.concatenate([flat(v) for k, v in sorted(d.items())])
        v = d.cpu().numpy() if hasattr(d, "cpu") else np.array(d)
        return v.flatten().astype(np.float32)

    fixed_action = np.array([0.5, -0.3, -0.5, 0.0, 0.0, 0.2, 0.3, 1.0], dtype=np.float32)
    n = 15

    env_id = gym.make("PickCube-v1", obs_mode="state_dict")
    env_id.reset(seed=42)
    id_states = [flat(env_id.step(fixed_action)[0]) for _ in range(n)]
    env_id.close()

    env_ood = gym.make("PickCube-v1", obs_mode="state_dict")
    env_ood.reset(seed=42)
    robot = env_ood.unwrapped.agent.robot
    art = robot._objs[0]
    for j in art.joints:
        if hasattr(j, "set_friction"):
            j.set_friction(5.0)
    ood_states = [flat(env_ood.step(fixed_action)[0]) for _ in range(n)]
    env_ood.close()

    diffs = [np.linalg.norm(s1 - s2) for s1, s2 in zip(id_states, ood_states)]
    assert max(diffs) > 1e-3, f"Friction OOD had no effect: max L2 diff={max(diffs):.2e}"
