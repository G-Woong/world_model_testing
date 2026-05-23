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

env = gym.make("PickCube-v1", obs_mode="state_dict")
obs, _ = env.reset(seed=42)
inner = env.unwrapped
agent = inner.agent
robot = agent.robot

# Check robot joints
print("=== Robot active joints ===")
joints = robot.active_joints if hasattr(robot, "active_joints") else []
for j in joints:
    jname = getattr(j, "name", "?")
    # SAPIEN 3 joint API
    attrs = [a for a in dir(j) if "damp" in a.lower() or "fric" in a.lower()]
    damp = getattr(j, "damping", "N/A")
    fric = getattr(j, "friction", "N/A")
    print(f"  [{jname}] damping={damp} friction={fric}")

print("\n=== Checking PhysxArticulation ===")
if hasattr(robot, "_objs"):
    for obj in robot._objs:
        joints_obj = obj.joints if hasattr(obj, "joints") else []
        print(f"n_joints: {len(joints_obj)}")
        for j in joints_obj[:3]:
            print(f"  joint: {getattr(j, 'name', '?')}, attrs: {[a for a in dir(j) if 'damp' in a.lower() or 'fric' in a.lower() or 'stiff' in a.lower()]}")
        break

env.close()

print("\n=== Testing joint damping OOD ===")
# Mass OOD is confirmed. Let's see if joint damping affects things.
np.random.seed(42)
actions = [np.array([0.3, -0.2, -0.4, 0.0, 0.0, 0.1, 0.2, 1.0], dtype=np.float32) for _ in range(30)]

env_id = gym.make("PickCube-v1", obs_mode="state_dict")
env_id.reset(seed=42)
id_states = []
for a in actions:
    obs, r, t, tr, info = env_id.step(a)
    id_states.append(flat(obs))
env_id.close()

# OOD: increase joint damping (simulates "friction" in joints)
env_ood = gym.make("PickCube-v1", obs_mode="state_dict")
env_ood.reset(seed=42)
robot_ood = env_ood.unwrapped.agent.robot
joints_ood = robot_ood.active_joints
print(f"Trying to set damping on {len(joints_ood)} joints")
for j in joints_ood:
    try:
        d_orig = j.damping
        j.damping = d_orig * 3.0  # 3x damping
        print(f"  {j.name}: damping {d_orig} -> {j.damping}")
    except Exception as e:
        print(f"  {j.name}: set damping failed: {e}")
        break

ood_states = []
for a in actions:
    obs, r, t, tr, info = env_ood.step(a)
    ood_states.append(flat(obs))
env_ood.close()

diffs = [np.linalg.norm(s1-s2) for s1,s2 in zip(id_states, ood_states)]
print(f"Max diff (damping OOD): {max(diffs):.6f}")
print("Damping OOD works:", max(diffs) > 1e-4)
