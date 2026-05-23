import warnings
warnings.filterwarnings("ignore")
import gymnasium as gym
import mani_skill.envs
import numpy as np

def flat(d):
    if isinstance(d, dict):
        return np.concatenate([flat(v) for k, v in sorted(d.items())])
    v = d.cpu().numpy() if hasattr(d, "cpu") else np.array(d)
    return v.flatten().astype(np.float32)

def run_episode(mass_scale=None, joint_friction=None, seed=42, n_steps=30):
    """Run episode with optional OOD params, return state trajectory."""
    actions = [np.array([0.5, -0.3, -0.5, 0.0, 0.0, 0.2, 0.3, 1.0], dtype=np.float32)
               for _ in range(n_steps)]
    env = gym.make("PickCube-v1", obs_mode="state_dict")
    env.reset(seed=seed)
    inner = env.unwrapped
    if mass_scale is not None:
        inner.cube.set_mass(mass_scale)
    if joint_friction is not None:
        robot = inner.agent.robot
        art = robot._objs[0]
        for j in art.joints:
            if hasattr(j, "set_friction"):
                j.set_friction(joint_friction)
    states = []
    for a in actions:
        obs, r, t, tr, info = env.step(a)
        states.append(flat(obs))
    env.close()
    return np.array(states)

# ID
id_states = run_episode()

tests = [
    ("mass=1.5", dict(mass_scale=1.5)),
    ("mass=0.5", dict(mass_scale=0.5)),
    ("jfric=2.0", dict(joint_friction=2.0)),
    ("jfric=5.0", dict(joint_friction=5.0)),
    ("jfric=10.0", dict(joint_friction=10.0)),
    ("jfric=20.0", dict(joint_friction=20.0)),
]

print("=== OOD Severity Comparison ===")
print(f"{'Config':<20} {'mean_L2_diff':<15} {'max_L2_diff':<15}")
for name, kwargs in tests:
    ood_states = run_episode(**kwargs)
    diffs = np.linalg.norm(id_states - ood_states, axis=1)
    print(f"{name:<20} {diffs.mean():.6f}       {diffs.max():.6f}")
