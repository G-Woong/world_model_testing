"""GUI event and episode schemas for agent-observable data."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any

from frcgw.schemas.visibility import VisibilityBucket


class GUIEventType(str, Enum):
    CLICK = "CLICK"
    FILL = "FILL"
    NAVIGATE = "NAVIGATE"
    SCROLL = "SCROLL"
    HOVER = "HOVER"
    DRAG = "DRAG"


GUI_OBSERVATION_VISIBILITY: dict[str, VisibilityBucket] = {
    "observation_id": VisibilityBucket.AGENT_OBSERVATION,
    "timestamp": VisibilityBucket.AGENT_OBSERVATION,
    "url": VisibilityBucket.AGENT_OBSERVATION,
    "visible_text": VisibilityBucket.AGENT_OBSERVATION,
    "clickable_elements": VisibilityBucket.AGENT_OBSERVATION,
    "screenshot_hash": VisibilityBucket.AGENT_OBSERVATION,
    "action_taken": VisibilityBucket.AGENT_OBSERVATION,
    "effect_description": VisibilityBucket.AGENT_OBSERVATION,
}


@dataclass(frozen=True)
class GUIObservation:
    observation_id: str
    timestamp: float
    url: str
    visible_text: str
    clickable_elements: list[str]
    screenshot_hash: str
    action_taken: str
    effect_description: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GUIObservation":
        return cls(
            observation_id=str(data["observation_id"]),
            timestamp=float(data["timestamp"]),
            url=str(data["url"]),
            visible_text=str(data["visible_text"]),
            clickable_elements=list(data["clickable_elements"]),
            screenshot_hash=str(data["screenshot_hash"]),
            action_taken=str(data["action_taken"]),
            effect_description=str(data["effect_description"]),
        )


@dataclass(frozen=True)
class GUIEpisodeRecord:
    episode_id: str
    task_id: str
    observations: list[GUIObservation]
    true_grammar: str
    true_regime: str
    outcome: str
    split_id: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GUIEpisodeRecord":
        return cls(
            episode_id=str(data["episode_id"]),
            task_id=str(data["task_id"]),
            observations=[
                obs if isinstance(obs, GUIObservation) else GUIObservation.from_dict(obs)
                for obs in data["observations"]
            ],
            true_grammar=str(data["true_grammar"]),
            true_regime=str(data["true_regime"]),
            outcome=str(data["outcome"]),
            split_id=str(data["split_id"]),
        )
