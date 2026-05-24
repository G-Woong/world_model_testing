"""ManiSkill state-only episode collector for FGLC Step 11.

Source: docs/STEP11_PLAN.md §F TASK D4
Collects episodes from ManiSkill PickCube-v1 with optional OOD params.
Per-episode validation via validators.py runs inline before storage.

OOD APIs confirmed via probe 2026-05-23:
  Mass: env.unwrapped.cube.set_mass(value)
  Friction: art.joints[i].set_friction(value)  (joint dry friction)
"""

from __future__ import annotations

import time
import warnings
from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass
class CollectionConfig:
    task: str = "PickCube-v1"
    split: str = "train_id"
    n_episodes: int = 50
    seed_pool: list[int] = field(default_factory=lambda: list(range(42, 92)))
    max_episode_steps: int = 200
    ood_params: dict[str, Any] = field(default_factory=dict)
    regime_id: int = 0
    ood_type: str = "id"
    min_episode_len: int = 10
    max_retry: int = 3
    wall_clock_limit_seconds: float = 1200.0  # 20 min


@dataclass
class CollectionStats:
    n_accepted: int = 0
    n_rejected: int = 0
    rejection_counts: dict[str, int] = field(default_factory=dict)
    total_transitions: int = 0
    wall_clock_seconds: float = 0.0


def _flat_obs(obs: dict) -> np.ndarray:
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


def _scalar(x) -> float:
    if hasattr(x, "item"):
        return x.item()
    return float(x)


def _apply_ood(env, ood_params: dict[str, Any], task: str = "PickCube-v1") -> None:
    """Apply OOD physical parameters after env.reset().

    Mass API differs by task: PickCube uses inner.cube, PushCube uses inner.obj.
    Falls back to actor name search when neither attribute exists.
    """
    inner = env.unwrapped
    if "object_mass" in ood_params:
        mass_val = float(ood_params["object_mass"])
        if hasattr(inner, "cube"):
            inner.cube.set_mass(mass_val)
        elif hasattr(inner, "obj"):
            inner.obj.set_mass(mass_val)
        else:
            for actor in inner.scene.get_all_actors():
                if any(kw in actor.name.lower() for kw in ("cube", "box", "obj")):
                    actor.set_mass(mass_val)
                    break
    if "joint_friction" in ood_params and ood_params["joint_friction"] > 0.0:
        robot = inner.agent.robot
        art = robot._objs[0]
        for j in art.joints:
            if hasattr(j, "set_friction"):
                j.set_friction(float(ood_params["joint_friction"]))


def collect_episodes(
    config: CollectionConfig,
    verbose: bool = False,
    quarantine_dir: str | None = None,
) -> tuple[list[dict[str, np.ndarray]], list[dict[str, Any]], CollectionStats]:
    """Collect n_episodes from ManiSkill with per-episode validation.

    Returns:
        episodes: list of inference dicts {state, action, reward, done} per episode
        eval_metas: list of eval-only metadata dicts, parallel to episodes
        stats: collection statistics
    """
    warnings.filterwarnings("ignore")

    import gymnasium as gym
    import mani_skill.envs  # noqa: F401

    from fglc.data.validators import validate_episode

    stats = CollectionStats()
    episodes: list[dict[str, np.ndarray]] = []
    eval_metas: list[dict[str, Any]] = []
    seen_state_hashes: set[str] = set()

    seed_iter = iter(config.seed_pool)
    accepted = 0
    t_start = time.time()

    while accepted < config.n_episodes:
        elapsed = time.time() - t_start
        if elapsed > config.wall_clock_limit_seconds:
            if verbose:
                print(f"  Wall-clock limit reached ({elapsed:.0f}s), stopping.")
            break

        try:
            seed = next(seed_iter)
        except StopIteration:
            if verbose:
                print("  Seed pool exhausted, stopping.")
            break

        retry = 0
        while retry < config.max_retry:
            env = gym.make(config.task, obs_mode="state_dict")
            obs, _ = env.reset(seed=seed)
            if config.ood_params:
                _apply_ood(env, config.ood_params, task=config.task)

            states: list[np.ndarray] = []
            actions: list[np.ndarray] = []
            rewards: list[float] = []
            dones: list[bool] = []
            success = False

            for _step in range(config.max_episode_steps):
                a = env.action_space.sample()
                gain = float(config.ood_params.get("action_gain", 1.0))
                if gain != 1.0:
                    a = np.clip(a * gain,
                                env.action_space.low,
                                env.action_space.high).astype(np.float32)
                obs_next, r, term, trunc, info = env.step(a)
                states.append(_flat_obs(obs))
                actions.append(np.array(a, dtype=np.float32))
                rewards.append(_scalar(r))
                done_val = bool(_scalar(term)) or bool(_scalar(trunc))
                dones.append(done_val)
                if "success" in info:
                    success = bool(_scalar(info["success"])) or success
                obs = obs_next
                if done_val:
                    break

            # Force timeout termination so no_done_signal validator doesn't reject
            # when collector's max_episode_steps fires before env's native limit.
            if dones and not dones[-1]:
                dones[-1] = True

            env.close()

            s_arr = np.array(states, dtype=np.float32)
            a_arr = np.array(actions, dtype=np.float32)
            r_arr = np.array(rewards, dtype=np.float32)
            d_arr = np.array(dones, dtype=bool)

            reject_reason = validate_episode(
                s_arr,
                a_arr,
                r_arr,
                d_arr,
                min_episode_len=config.min_episode_len,
                seen_state_hashes=seen_state_hashes,
            )

            if reject_reason is None:
                episodes.append({"state": s_arr, "action": a_arr, "reward": r_arr, "done": d_arr})
                eval_metas.append({
                    "regime_id": config.regime_id,
                    "ood_type": config.ood_type,
                    "true_mass": float(config.ood_params.get("object_mass", 0.064)),
                    "true_friction": float(config.ood_params.get("joint_friction", 0.0)),
                    "true_latency": int(config.ood_params.get("action_delay_steps", 0)),
                    "true_noise_sigma": float(config.ood_params.get("noise_sigma", 0.0)),
                    "true_action_gain": float(config.ood_params.get("action_gain", 1.0)),
                    "episode_id": accepted,
                    "step_idx": -1,
                    "split": config.split,
                    "task_id": config.task,
                    "seed": seed,
                    "template_id": "default",
                    "success": success,
                    "episode_len": len(states),
                })
                stats.n_accepted += 1
                stats.total_transitions += len(states)
                accepted += 1
                if verbose:
                    print(f"  [{config.split}] ep {accepted}/{config.n_episodes} "
                          f"seed={seed} len={len(states)} success={success}")
                break
            else:
                stats.n_rejected += 1
                reason_key = reject_reason.value
                stats.rejection_counts[reason_key] = (
                    stats.rejection_counts.get(reason_key, 0) + 1
                )
                if verbose:
                    print(f"  [{config.split}] REJECT seed={seed} reason={reason_key}")
                if quarantine_dir is not None:
                    _quarantine_rejected_episode(
                        quarantine_dir=quarantine_dir,
                        split=config.split,
                        seed=seed,
                        reason=reason_key,
                        states=s_arr,
                        actions=a_arr,
                        rewards=r_arr,
                        dones=d_arr,
                    )
                retry += 1

    stats.wall_clock_seconds = time.time() - t_start
    return episodes, eval_metas, stats


def _quarantine_rejected_episode(
    quarantine_dir: str,
    split: str,
    seed: int,
    reason: str,
    states: np.ndarray,
    actions: np.ndarray,
    rewards: np.ndarray,
    dones: np.ndarray,
) -> None:
    """Best-effort rejected-episode dump; failures must not stop collection."""
    import os

    import h5py

    try:
        split_dir = os.path.join(quarantine_dir, split)
        os.makedirs(split_dir, exist_ok=True)
        h5_path = os.path.join(split_dir, f"{seed}_{reason}.h5")
        with h5py.File(h5_path, "w") as f:
            f.create_dataset("state", data=states, compression="gzip", compression_opts=4)
            f.create_dataset("action", data=actions, compression="gzip", compression_opts=4)
            f.create_dataset("reward", data=rewards, compression="gzip", compression_opts=4)
            f.create_dataset("done", data=dones, compression="gzip", compression_opts=4)
    except Exception as exc:
        print(
            f"WARNING: failed to quarantine rejected episode split={split} "
            f"seed={seed} reason={reason}: {exc}"
        )


def save_episodes_h5(
    episodes: list[dict[str, np.ndarray]],
    eval_metas: list[dict[str, Any]],
    h5_path: str,
) -> None:
    """Write episodes to HDF5. inference fields in /episodes/, eval-only in /eval_only/."""
    import h5py

    import os
    os.makedirs(os.path.dirname(h5_path) or ".", exist_ok=True)

    with h5py.File(h5_path, "w") as f:
        ep_group = f.create_group("episodes")
        eval_group = f.create_group("eval_only")

        for i, (ep, meta) in enumerate(zip(episodes, eval_metas)):
            eg = ep_group.create_group(str(i))
            eg.create_dataset("state", data=ep["state"], compression="gzip", compression_opts=4)
            eg.create_dataset("action", data=ep["action"], compression="gzip", compression_opts=4)
            eg.create_dataset("reward", data=ep["reward"], compression="gzip", compression_opts=4)
            eg.create_dataset("done", data=ep["done"], compression="gzip", compression_opts=4)

            evg = eval_group.create_group(str(i))
            for k, v in meta.items():
                if k in ("state", "action", "reward", "done"):
                    continue
                evg.attrs[k] = v
