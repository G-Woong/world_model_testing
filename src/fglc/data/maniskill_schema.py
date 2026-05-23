"""ManiSkill state-only transition and episode schemas for FGLC Step 11.

Source: docs/STEP11_PLAN.md §C Data Contract Schemas
Confirmed D_x=42 (PickCube-v1 state_dict), D_a=8 (Panda EEF) via probe 2026-05-23.

Inference dict (model input):
  - state, action, reward, done
  - FORBIDDEN fields (CLAUDE.md §양보할 수 없는 데이터 규칙) stripped before this point

Eval-only dict (evaluation metadata, NEVER model input):
  - regime_id, ood_type, true_mass, true_friction (joint_friction_value), etc.
"""

from __future__ import annotations

from typing import Any


class InferenceTransition:
    """Minimal model-input transition. No forbidden fields allowed."""
    __slots__ = ("state", "action", "reward", "done")

    def __init__(
        self,
        state: list[float],
        action: list[float],
        reward: float,
        done: bool,
    ) -> None:
        self.state = state      # float32 vector, length D_x
        self.action = action    # float32 vector, length D_a
        self.reward = reward    # scalar
        self.done = done        # bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "state": self.state,
            "action": self.action,
            "reward": self.reward,
            "done": self.done,
        }


class EvalOnlyTransition:
    """Evaluation-only metadata. Must NEVER be fed to model inference.

    Corresponds to FORBIDDEN_AGENT_FIELDS in visibility.py.
    """
    __slots__ = (
        "regime_id",
        "ood_type",
        "true_mass",
        "true_friction",
        "true_latency",
        "true_noise_sigma",
        "true_action_gain",
        "episode_id",
        "step_idx",
        "split",
        "task_id",
        "seed",
        "template_id",
        "success",
    )

    def __init__(
        self,
        regime_id: int,
        ood_type: str,
        true_mass: float,
        true_friction: float,
        true_latency: int,
        true_noise_sigma: float,
        true_action_gain: float,
        episode_id: int,
        step_idx: int,
        split: str,
        task_id: str,
        seed: int,
        template_id: str,
        success: bool,
    ) -> None:
        self.regime_id = regime_id
        self.ood_type = ood_type
        self.true_mass = true_mass
        self.true_friction = true_friction
        self.true_latency = true_latency
        self.true_noise_sigma = true_noise_sigma
        self.true_action_gain = true_action_gain
        self.episode_id = episode_id
        self.step_idx = step_idx
        self.split = split
        self.task_id = task_id
        self.seed = seed
        self.template_id = template_id
        self.success = success

    def to_dict(self) -> dict[str, Any]:
        return {k: getattr(self, k) for k in self.__slots__}


# Regime IDs (frozen, matches split_config)
REGIME_ID: dict[str, int] = {
    "train_id": 0,
    "val_id": 1,
    "test_id": 2,
    "ood_mass_low": 10,
    "ood_friction_low": 20,
    "ood_latency": 30,
}

# OOD params per split (for PickCube-v1, 2026-05-23 probe confirmed APIs)
OOD_PARAMS: dict[str, dict[str, Any]] = {
    "train_id": {"object_mass": 0.064, "joint_friction": 0.0},
    "val_id": {"object_mass": 0.064, "joint_friction": 0.0},
    "test_id": {"object_mass": 0.064, "joint_friction": 0.0},
    "ood_mass_low": {"object_mass": 1.5, "joint_friction": 0.0},
    "ood_friction_low": {"object_mass": 0.064, "joint_friction": 5.0},
}

# Default ID physical params (PickCube-v1 probe 2026-05-23)
ID_MASS_DEFAULT: float = 0.064      # kg, SAPIEN default cube mass
ID_JOINT_FRICTION_DEFAULT: float = 0.0  # dry friction coefficient (default=0)
