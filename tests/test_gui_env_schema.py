"""Tests for GUI environment task and event schemas."""
from __future__ import annotations

from dataclasses import fields

from frcgw.gui_env.event_schema import GUIEpisodeRecord, GUIEventType, GUIObservation
from frcgw.gui_env.task_spec import MVE_TASK_SPECS


def test_task_spec_fields_present():
    assert len(MVE_TASK_SPECS) >= 10
    task_ids = [spec.task_id for spec in MVE_TASK_SPECS]
    assert len(task_ids) == len(set(task_ids))
    assert all(spec.description for spec in MVE_TASK_SPECS)
    assert all(1 <= spec.difficulty <= 5 for spec in MVE_TASK_SPECS)


def test_hidden_fields_not_in_observation():
    observation_fields = {field.name for field in fields(GUIObservation)}
    assert "true_grammar" not in observation_fields
    assert "true_regime" not in observation_fields
    assert "split_id" not in observation_fields


def test_episode_record_has_audit_only_fields():
    episode_fields = {field.name for field in fields(GUIEpisodeRecord)}
    assert "true_grammar" in episode_fields
    assert "true_regime" in episode_fields
    assert "split_id" in episode_fields


def test_gui_event_types_cover_all():
    event_types = {event.value for event in GUIEventType}
    assert {"CLICK", "FILL", "NAVIGATE", "DRAG"} <= event_types
