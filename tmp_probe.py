import warnings
warnings.filterwarnings("ignore")
import gymnasium as gym
import mani_skill.envs
import numpy as np
import sapien.physx

def to_np(d):
    if isinstance(d, dict):
        return {k: to_np(v) for k, v in d.items()}
    v = d.cpu().numpy() if hasattr(d, "cpu") else np.array(d)
    return v

def flat(d):
    if isinstance(d, dict):
        return np.concatenate([flat(v) for k, v in sorted(d.items())])
    v = d.cpu().numpy() if hasattr(d, "cpu") else np.array(d)
    return v.flatten().astype(np.float32)

env = gym.make("PickCube-v1", obs_mode="state_dict")
obs, _ = env.reset(seed=42)
inner = env.unwrapped
obs_np = to_np(obs)

print("=== Initial State ===")
print("tcp_pose:", obs_np["extra"]["tcp_pose"])
print("obj_pose:", obs_np["extra"]["obj_pose"])
print("tcp_to_obj:", obs_np["extra"]["tcp_to_obj_pos"])

# Check ground material
scene = inner.scene
if hasattr(scene, "entities"):
    for e in scene.entities:
        name = getattr(e, "name", "?")
        comps = getattr(e, "components", [])
        for c in comps:
            if "physx" in type(c).__name__.lower() and "static" in type(c).__name__.lower():
                shapes = c.get_collision_shapes() if hasattr(c, "get_collision_shapes") else []
                for sh in shapes:
                    if hasattr(sh, "physical_material"):
                        mat = sh.physical_material
                        print(f"Ground entity '{name}' static_friction={mat.static_friction:.3f} dyn={mat.dynamic_friction:.3f}")

# Test: Use a long sequence where robot moves near cube
# Move TCP toward object first, then interact
print("\n=== Friction vs Mass OOD test ===")

# Use a "teleport to cube + grasp" approach via scripted actions
# Check what max_episode_steps is
print("max_episode_steps:", inner.max_episode_steps if hasattr(inner, "max_episode_steps") else "unknown")

# Test with extreme friction difference
def get_cube_mat(env):
    cube = env.unwrapped.cube
    entity = cube._objs[0]
    for c in entity.components:
        if "physx" in type(c).__name__.lower():
            return c.get_collision_shapes()[0].physical_material
    return None

# Long random episode - check if friction ever matters
np.random.seed(42)
actions = [env.action_space.sample() for _ in range(50)]

env.close()

# ID
env_id = gym.make("PickCube-v1", obs_mode="state_dict")
env_id.reset(seed=42)
id_states = []
for a in actions:
    obs, r, t, tr, info = env_id.step(a)
    id_states.append(flat(obs))
    if t.item() or tr.item():
        break
env_id.close()

# OOD friction=1.5
env_ood = gym.make("PickCube-v1", obs_mode="state_dict")
env_ood.reset(seed=42)
mat = get_cube_mat(env_ood)
mat.set_static_friction(1.5)
mat.set_dynamic_friction(1.5)
print(f"OOD cube friction: static={mat.static_friction:.3f} dyn={mat.dynamic_friction:.3f}")
ood_states = []
for a in actions[:len(id_states)]:
    obs, r, t, tr, info = env_ood.step(a)
    ood_states.append(flat(obs))
    if t.item() or tr.item():
        break
env_ood.close()

diffs = [np.linalg.norm(s1 - s2) for s1, s2 in zip(id_states, ood_states)]
max_diff = max(diffs)
print(f"Max state L2 diff (friction OOD): {max_diff:.6f}")
print("Friction OOD effective:", max_diff > 1e-4)
