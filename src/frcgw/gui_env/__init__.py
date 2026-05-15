"""Synthetic Web/GUI environment data contracts."""
from __future__ import annotations

from .event_schema import GUIEpisodeRecord, GUIObservation
from .leakage_audit import GUILeakageError, audit_gui_observation
from .replay_validator import GUIReplayValidator
from .task_spec import GUITaskSpec, MVE_TASK_SPECS

__all__ = [
    "GUITaskSpec",
    "MVE_TASK_SPECS",
    "GUIObservation",
    "GUIEpisodeRecord",
    "GUIReplayValidator",
    "audit_gui_observation",
    "GUILeakageError",
]
