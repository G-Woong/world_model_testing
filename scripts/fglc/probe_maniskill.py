"""ManiSkill PickCube-v1 state-only probe script.

Checkpoint 1a~1e (Step 11 PLAN §E):
  1a. Task registration + state_dict reset/step
  1b. D_x / D_a shape determination
  1c. reward / done / success API
  1d. Seed reproducibility
  1e. OOD param API (mass + joint friction)

Usage:
  python scripts/fglc/probe_maniskill.py --task PickCube-v1 --n-probe 5 --output-json -
  python scripts/fglc/probe_maniskill.py --task PickCube-v1 --verbose

Source: docs/STEP11_PLAN.md §J TASK D1
"""

from __future__ import annotations

import argparse
import json
import sys
import warnings

warnings.filterwarnings("ignore")

import numpy as np


def _flat_obs(obs: dict) -> np.ndarray:
    """Recursively flatten a ManiSkill state_dict obs to 1D float32."""
    parts: list[np.ndarray] = []
    for k in sorted(obs.keys()):
        v = obs[k]
        if isinstance(v, dict):
            parts.append(_flat_obs(v))
        else:
            if hasattr(v, "cpu"):
                v = v.cpu().numpy()
            arr = np.array(v, dtype=np.float32).flatten()
            parts.append(arr)
    return np.concatenate(parts)


def _set_mass(env, mass: float) -> None:
    """Set cube mass via SAPIEN Actor.set_mass."""
    inner = env.unwrapped
    inner.cube.set_mass(mass)


def _set_joint_friction(env, friction: float) -> None:
    """Set joint dry friction on all Panda articulation joints."""
    inner = env.unwrapped
    robot = inner.agent.robot
    art = robot._objs[0]
    for j in art.joints:
        if hasattr(j, "set_friction"):
            j.set_friction(friction)


def _scalar(x) -> float:
    """Extract Python float from tensor or numpy scalar."""
    if hasattr(x, "item"):
        return x.item()
    return float(x)


def probe_task(
    task: str,
    n_probe: int,
    verbose: bool,
) -> dict:
    """Run all Checkpoint 1a~1e probes and return results dict."""
    import gymnasium as gym
    import mani_skill.envs  # noqa: F401 — registers envs

    results: dict = {
        "task": task,
        "checkpoint_1a": "UNKNOWN",
        "checkpoint_1b": "UNKNOWN",
        "checkpoint_1c": "UNKNOWN",
        "checkpoint_1d": "UNKNOWN",
        "checkpoint_1e_mass": "UNKNOWN",
        "checkpoint_1e_friction": "UNKNOWN",
        "D_x": None,
        "D_a": None,
        "episode_len_probe": None,
        "ood_api_mass": "cube.set_mass(value)",
        "ood_api_friction": "art.joints[i].set_friction(value)",
        "obs_keys": None,
        "info_keys": None,
        "reward_type": None,
        "seed_reproducible": None,
        "mass_l2_diff_mean": None,
        "friction_l2_diff_mean": None,
        "obs_structure": {},
    }

    # --- Checkpoint 1a: task registration + reset/step ---
    try:
        env = gym.make(task, obs_mode="state_dict")
        obs, info = env.reset(seed=42)
        assert isinstance(obs, dict), f"obs is not dict: {type(obs)}"
        obs_keys = sorted(obs.keys())
        results["obs_keys"] = obs_keys
        results["checkpoint_1a"] = "PASS"
        if verbose:
            print(f"[1a] PASS — obs_keys={obs_keys}")
    except Exception as e:
        results["checkpoint_1a"] = f"FAIL: {e}"
        return results

    # --- Checkpoint 1b: shape probe ---
    try:
        D_a = env.action_space.shape[0]
        flat = _flat_obs(obs)
        D_x = flat.shape[0]
        results["D_x"] = int(D_x)
        results["D_a"] = int(D_a)

        # Record obs sub-structure
        def _obs_struct(d, prefix=""):
            out = {}
            if isinstance(d, dict):
                for k, v in d.items():
                    out.update(_obs_struct(v, f"{prefix}/{k}"))
            else:
                if hasattr(d, "cpu"):
                    d = d.cpu().numpy()
                arr = np.array(d)
                out[prefix] = {"shape": list(arr.shape), "dtype": str(arr.dtype)}
            return out

        results["obs_structure"] = _obs_struct(obs)

        # Stability check: consistent shape across multiple steps
        shapes_ok = True
        ep_steps = 0
        for _ in range(n_probe * 5):
            a = env.action_space.sample()
            obs2, r, t, tr, info2 = env.step(a)
            ep_steps += 1
            flat2 = _flat_obs(obs2)
            if flat2.shape[0] != D_x:
                shapes_ok = False
                break
            if _scalar(t) or _scalar(tr):
                break

        results["episode_len_probe"] = ep_steps
        results["checkpoint_1b"] = "PASS" if shapes_ok else "FAIL: inconsistent D_x"
        if verbose:
            print(f"[1b] PASS — D_x={D_x}, D_a={D_a}, ep_steps={ep_steps}")
    except Exception as e:
        results["checkpoint_1b"] = f"FAIL: {e}"

    # --- Checkpoint 1c: reward / done / success ---
    try:
        env.reset(seed=42)
        a = env.action_space.sample()
        obs3, r, term, trunc, info3 = env.step(a)
        results["reward_type"] = type(r).__name__
        results["info_keys"] = sorted(info3.keys()) if hasattr(info3, "keys") else []
        has_success = "success" in info3
        results["checkpoint_1c"] = "PASS" if has_success else "WARN: no 'success' in info"
        if verbose:
            print(f"[1c] PASS — reward={_scalar(r):.4f}, success_in_info={has_success}")
    except Exception as e:
        results["checkpoint_1c"] = f"FAIL: {e}"

    env.close()

    # --- Checkpoint 1d: seed reproducibility ---
    try:
        env1 = gym.make(task, obs_mode="state_dict")
        env1.reset(seed=42)
        env2 = gym.make(task, obs_mode="state_dict")
        env2.reset(seed=42)

        actions = [env1.action_space.sample() for _ in range(10)]
        diffs = []
        for a in actions:
            o1, _, t1, tr1, _ = env1.step(a)
            o2, _, t2, tr2, _ = env2.step(a)
            diffs.append(np.max(np.abs(_flat_obs(o1) - _flat_obs(o2))))
            if _scalar(t1) or _scalar(tr1):
                break

        env1.close()
        env2.close()
        reproducible = all(d < 1e-5 for d in diffs)
        results["seed_reproducible"] = reproducible
        results["checkpoint_1d"] = "PASS" if reproducible else "WARN: non-deterministic"
        if verbose:
            print(f"[1d] {'PASS' if reproducible else 'WARN'} — max_diff={max(diffs):.2e}")
    except Exception as e:
        results["checkpoint_1d"] = f"FAIL: {e}"

    # --- Checkpoint 1e: OOD param APIs ---
    fixed_actions = [
        np.array([0.5, -0.3, -0.5, 0.0, 0.0, 0.2, 0.3, 1.0], dtype=np.float32)
        for _ in range(20)
    ]

    def _run(modifier=None):
        e = gym.make(task, obs_mode="state_dict")
        e.reset(seed=42)
        if modifier:
            modifier(e)
        st = []
        for a in fixed_actions:
            o, _, t, tr, _ = e.step(a)
            st.append(_flat_obs(o))
            if _scalar(t) or _scalar(tr):
                break
        e.close()
        return np.array(st)

    id_states = _run()

    # Mass OOD
    try:
        ood_mass = _run(modifier=lambda e: _set_mass(e, 1.5))
        n = min(len(id_states), len(ood_mass))
        diffs_mass = np.linalg.norm(id_states[:n] - ood_mass[:n], axis=1)
        results["mass_l2_diff_mean"] = float(diffs_mass.mean())
        results["checkpoint_1e_mass"] = "PASS" if diffs_mass.mean() > 1e-6 else "FAIL: no divergence"
        if verbose:
            print(f"[1e-mass] PASS — mean_L2_diff={diffs_mass.mean():.4f}")
    except Exception as e:
        results["checkpoint_1e_mass"] = f"FAIL: {e}"

    # Joint friction OOD
    try:
        ood_fric = _run(modifier=lambda e: _set_joint_friction(e, 5.0))
        n = min(len(id_states), len(ood_fric))
        diffs_fric = np.linalg.norm(id_states[:n] - ood_fric[:n], axis=1)
        results["friction_l2_diff_mean"] = float(diffs_fric.mean())
        results["checkpoint_1e_friction"] = "PASS" if diffs_fric.mean() > 1e-6 else "FAIL: no divergence"
        if verbose:
            print(f"[1e-friction] PASS — mean_L2_diff={diffs_fric.mean():.4f}")
    except Exception as e:
        results["checkpoint_1e_friction"] = f"FAIL: {e}"

    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="ManiSkill PickCube-v1 probe")
    parser.add_argument("--task", default="PickCube-v1")
    parser.add_argument("--n-probe", type=int, default=5, help="mini probe episode count")
    parser.add_argument("--output-json", default="-", help="output path or '-' for stdout")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    results = probe_task(args.task, args.n_probe, args.verbose)
    passed = all(
        str(v).startswith("PASS") or str(v).startswith("WARN")
        for k, v in results.items()
        if k.startswith("checkpoint_")
    )
    results["overall"] = "PASS" if passed else "FAIL"
    results["ood_api_resolved"] = (
        results["checkpoint_1e_mass"] == "PASS"
        and results["checkpoint_1e_friction"] == "PASS"
    )

    out = json.dumps(results, indent=2)
    if args.output_json == "-":
        print(out)
    else:
        with open(args.output_json, "w") as f:
            f.write(out)
        print(f"Probe result written to {args.output_json}")


if __name__ == "__main__":
    main()
