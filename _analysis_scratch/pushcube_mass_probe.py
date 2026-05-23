"""PushCube-v1 mass OOD probe script.
One-time analysis in _analysis_scratch/. Do NOT commit.
Goal: measure state_delta_norm gap (train_id vs ood_mass_low, mass=1.5)
      with n=50 episodes + KS test.
"""
import gymnasium as gym
import mani_skill.envs
import numpy as np
from scipy import stats
import warnings
warnings.filterwarnings("ignore")


def collect_probe(task, n_episodes, mass=None, seeds=None, verbose=False):
    if seeds is None:
        seeds = list(range(42, 42 + n_episodes))

    env = gym.make(task, obs_mode="state", render_mode=None)
    all_delta_norms = []
    all_rewards = []

    for i, seed in enumerate(seeds[:n_episodes]):
        obs, _ = env.reset(seed=seed)

        # Apply mass OOD (PushCube-v1 uses inner.obj, not inner.cube)
        if mass is not None:
            inner = env.unwrapped
            if hasattr(inner, "obj"):
                inner.obj.set_mass(float(mass))
            elif hasattr(inner, "cube"):
                inner.cube.set_mass(float(mass))
            else:
                # Try actor search
                for actor in inner.scene.get_all_actors():
                    if "cube" in actor.name.lower() or "box" in actor.name.lower():
                        actor.set_mass(float(mass))
                        break

        states = []
        ep_rewards = []
        for step in range(50):
            action = env.action_space.sample()
            obs, rew, done, trunc, _ = env.step(action)
            if hasattr(obs, "cpu"):
                states.append(obs.cpu().numpy().flatten())
            else:
                states.append(np.array(obs).flatten())
            ep_rewards.append(float(rew))
            if done or trunc:
                break

        if len(states) >= 2:
            st = np.stack(states)
            delta = np.abs(st[1:] - st[:-1])
            delta_norm = np.linalg.norm(delta.mean(axis=0))
            all_delta_norms.append(delta_norm)
        all_rewards.extend(ep_rewards)

        if verbose and (i + 1) % 10 == 0:
            print(f"  ep {i+1}/{n_episodes}")

    env.close()

    return {
        "state_delta_norm_mean": float(np.mean(all_delta_norms)),
        "state_delta_norm_std": float(np.std(all_delta_norms)),
        "all_delta_norms": all_delta_norms,
        "reward_mean": float(np.mean(all_rewards)),
        "reward_max": float(np.max(all_rewards)),
        "n_episodes": len(all_delta_norms),
    }


if __name__ == "__main__":
    print("=== PushCube-v1 mass OOD probe (n=50 each) ===")
    print("Collecting train_id (50 ep)...")
    train = collect_probe("PushCube-v1", n_episodes=50,
                          seeds=list(range(42, 92)), verbose=True)
    print(f"train_id: mean={train['state_delta_norm_mean']:.6f} std={train['state_delta_norm_std']:.6f}")

    print("\nCollecting ood_mass_low (mass=1.5, 50 ep)...")
    mass_ood = collect_probe("PushCube-v1", n_episodes=50, mass=1.5,
                             seeds=list(range(500, 550)), verbose=True)
    print(f"ood_mass_low: mean={mass_ood['state_delta_norm_mean']:.6f} std={mass_ood['state_delta_norm_std']:.6f}")

    # Gap and KS test
    gap = abs(mass_ood["state_delta_norm_mean"] - train["state_delta_norm_mean"])
    gap_signed = mass_ood["state_delta_norm_mean"] - train["state_delta_norm_mean"]
    ks_stat, ks_p = stats.ks_2samp(
        train["all_delta_norms"], mass_ood["all_delta_norms"]
    )
    t_stat, t_p = stats.ttest_ind(
        train["all_delta_norms"], mass_ood["all_delta_norms"]
    )

    print(f"\n=== RESULT ===")
    print(f"gap (abs): {gap:.6f} (threshold=0.01 -> {'PASS' if gap >= 0.01 else 'FAIL'})")
    print(f"gap (signed): {gap_signed:+.6f}")
    print(f"KS test: stat={ks_stat:.4f}, p={ks_p:.4e} -> {'significant' if ks_p < 0.05 else 'NOT significant'}")
    print(f"t-test:  stat={t_stat:.4f}, p={t_p:.4e} -> {'significant' if t_p < 0.05 else 'NOT significant'}")
    print(f"reward: train={train['reward_mean']:.4f}/{train['reward_max']:.4f} "
          f"mass={mass_ood['reward_mean']:.4f}/{mass_ood['reward_max']:.4f}")

    # Final judgment
    print(f"\n=== FINAL JUDGMENT ===")
    if gap >= 0.01 and ks_p < 0.05:
        print("PASS: gap >= 0.01 AND KS p < 0.05 -> mass OOD severity CONFIRMED in PushCube-v1")
    elif gap >= 0.01 and ks_p >= 0.05:
        print("BORDERLINE: gap >= 0.01 but KS p >= 0.05 -> statistically uncertain")
    elif gap < 0.01:
        print("FAIL: gap < 0.01 -> mass OOD not detectable in PushCube-v1 either")
        print("  -> Fall back to E.7+E.2 (friction-only R3)")
