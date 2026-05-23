import warnings
warnings.filterwarnings("ignore")
import gymnasium as gym
import mani_skill.envs
import numpy as np
import sapien.physx

env = gym.make("PickCube-v1", obs_mode="state_dict")
obs, _ = env.reset(seed=42)
inner = env.unwrapped
scene = inner.scene

# Check all entities and their physx materials
print("=== All scene entity materials ===")
if hasattr(scene, "entities"):
    for e in scene.entities:
        name = getattr(e, "name", "?")
        comps = getattr(e, "components", [])
        for c in comps:
            cname = type(c).__name__
            if "physx" in cname.lower():
                shapes = c.get_collision_shapes() if hasattr(c, "get_collision_shapes") else []
                for sh in shapes:
                    if hasattr(sh, "physical_material"):
                        mat = sh.physical_material
                        print(f"  [{name}|{cname}] st={mat.static_friction:.3f} dyn={mat.dynamic_friction:.3f} res={mat.restitution:.3f}")

# Check panda agent links
print("\n=== Panda agent links friction ===")
agent = inner.agent
robot = agent.robot if hasattr(agent, "robot") else None
if robot is not None:
    links = robot.links if hasattr(robot, "links") else []
    print(f"n_links: {len(links)}")
    for link in links:
        name = getattr(link, "name", "?")
        entity = link._objs[0] if hasattr(link, "_objs") else None
        if entity:
            for c in entity.components:
                if "physx" in type(c).__name__.lower():
                    shapes = c.get_collision_shapes() if hasattr(c, "get_collision_shapes") else []
                    for sh in shapes:
                        if hasattr(sh, "physical_material"):
                            mat = sh.physical_material
                            print(f"  [{name}] st={mat.static_friction:.3f} dyn={mat.dynamic_friction:.3f}")

# Also check joints for damping
print("\n=== Panda joints (damping) ===")
if robot is not None:
    joints = robot.active_joints if hasattr(robot, "active_joints") else []
    for j in joints:
        jname = getattr(j, "name", "?")
        damp = j.damping if hasattr(j, "damping") else "N/A"
        fric = j.friction if hasattr(j, "friction") else "N/A"
        print(f"  [{jname}] damping={damp} friction={fric}")

env.close()
