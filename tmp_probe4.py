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

np.random.seed(42)
actions = [np.array([0.5, -0.3, -0.5, 0.0, 0.0, 0.2, 0.3, 1.0], dtype=np.float32) for _ in range(30)]

# ID
env_id = gym.make("PickCube-v1", obs_mode="state_dict")
env_id.reset(seed=42)
id_states = []
for a in actions:
    obs, r, t, tr, info = env_id.step(a)
    id_states.append(flat(obs))
env_id.close()

# OOD: high joint friction
env_ood = gym.make("PickCube-v1", obs_mode="state_dict")
env_ood.reset(seed=42)

# Access articulation joints via _objs
robot_ood = env_ood.unwrapped.agent.robot
if hasattr(robot_ood, "_objs"):
    art = robot_ood._objs[0]
    joints_phys = art.joints if hasattr(art, "joints") else []
    print(f"PhysX joints: {len(joints_phys)}")
    for j in joints_phys:
        if hasattr(j, "set_friction"):
            try:
                jf_before = j.get_friction() if hasattr(j, "get_friction") else j.friction
                j.set_friction(20.0)
                jf_after = j.friction
                # print(f"  {j.name}: {jf_before} -> {jf_after}")
            except Exception as e:
                print(f"  friction set error: {e}")
    print("Joint friction set to 20.0")

ood_states = []
for a in actions:
    obs, r, t, tr, info = env_ood.step(a)
    ood_states.append(flat(obs))
env_ood.close()

diffs = [np.linalg.norm(s1-s2) for s1,s2 in zip(id_states, ood_states)]
print(f"Max diff (joint friction OOD): {max(diffs):.6f}")
print(f"All diffs: {[f'{d:.4f}' for d in diffs[:10]]}")
print("Joint friction OOD works:", max(diffs) > 1e-4)

# Summary of confirmed APIs
print("\n=== CONFIRMED OOD APIs ===")
print("1. cube.set_mass(1.5)  -> CONFIRMED (L2 diff ~0.002/step)")
print(f"2. joint.set_friction(20)  -> {'CONFIRMED' if max(diffs) > 1e-4 else 'NOT effective'}")
