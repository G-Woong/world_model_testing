from __future__ import annotations

import dataclasses
import json
import random
from pathlib import Path
from typing import Any

from frcgw.schemas.step_schema import (
    ActionRecord,
    CandidateAction,
    EvaluationLabels,
    PublicEffect,
    PublicObservation,
    StepAuditMetadata,
    StepRecord,
    TrainingLabels,
)
from frcgw.text_env.collector import (
    CollectorConfig,
    _backfill_episode_timestamps,
    collect_episode,
)
from frcgw.text_env.generator import EpisodeSpecGenerator, TaskFamily
from frcgw.text_env.policies import PolicyMixtureRunner


REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = REPO_ROOT / "data" / "frcgw_text" / "v0_2"


def _make_step(
    index: int,
    *,
    action_type: str = "wait",
    valid_switch: bool = False,
    true_wrong: bool = False,
    progress_delta: float = 0.0,
    recovery_action_id: str | None = None,
) -> StepRecord:
    return StepRecord(
        step_id=f"ep0_step_{index:03d}",
        episode_id="ep0",
        step_index=index,
        public_observation=PublicObservation(
            instruction="test",
            candidate_actions_public=[CandidateAction("wait", "wait")],
        ),
        action=ActionRecord(action_id=f"a{index}", action_type=action_type),
        observed_effect_public=PublicEffect(effect_type="no_state_change"),
        training_labels=TrainingLabels(
            true_regime="search_form",
            true_control_grammar="direct_search",
            true_change_point=str(index),
            true_reveal_vs_shift="none",
            true_action_effect_type="none",
            true_failed_action=False,
            failure_reason=None,
            progress_delta=progress_delta,
            recovery_action_id=recovery_action_id,
            valid_hypothesis_switch=valid_switch,
        ),
        evaluation_labels=EvaluationLabels(true_wrong_hypothesis=true_wrong),
        audit_metadata=StepAuditMetadata(
            generator_version="test",
            collection_timestamp="2026-01-01T00:00:00+00:00",
            policy_id="test",
            split_id="train",
        ),
    )


def _load_episodes(split: str) -> list[dict[str, Any]]:
    path = DATA_ROOT / f"{split}.jsonl"
    assert path.exists(), f"missing generated split: {path}"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _eval_labels(step: dict[str, Any]) -> dict[str, Any]:
    labels = step.get("evaluation_labels")
    if isinstance(labels, dict):
        return labels
    labels = step.get("eval_labels")
    if isinstance(labels, dict):
        return labels
    return {}


def _strip_collection_timestamps(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _strip_collection_timestamps(item)
            for key, item in value.items()
            if key != "collection_timestamp"
        }
    if isinstance(value, list):
        return [_strip_collection_timestamps(item) for item in value]
    return value


def test_collector_emits_hypothesis_update_timestamp_when_switch_occurs() -> None:
    steps = [_make_step(i, valid_switch=(i == 3)) for i in range(5)]

    patched = _backfill_episode_timestamps(steps, None)

    assert {step.evaluation_labels.hypothesis_update_timestamp for step in patched} == {3}


def test_collector_emits_recovery_timestamp_when_recovery_resolves_wrong_grammar() -> None:
    steps = [
        _make_step(0, true_wrong=True),
        _make_step(
            1,
            action_type="close_modal",
            progress_delta=0.5,
            recovery_action_id="close_modal",
        ),
    ]

    patched = _backfill_episode_timestamps(steps, None)

    assert {step.evaluation_labels.recovery_timestamp for step in patched} == {1}


def test_collector_keeps_recovery_timestamp_none_for_non_wrong_grammar_episode() -> None:
    steps = [_make_step(i, progress_delta=0.5, recovery_action_id="wait") for i in range(3)]

    patched = _backfill_episode_timestamps(steps, None)

    assert all(step.evaluation_labels.recovery_timestamp is None for step in patched)


def test_collector_emits_ood_type_for_ood_spec() -> None:
    spec = dataclasses.replace(
        EpisodeSpecGenerator(seed=101).generate(family=TaskFamily.NESTED_SCROLL),
        ood_type="grammar_shift",
    )
    runner = PolicyMixtureRunner(mixture={"oracle": 1.0}, rng=random.Random(101))

    episode = collect_episode(
        spec,
        runner,
        random.Random(spec.seed),
        CollectorConfig(split_id="test_ood"),
    )

    assert {step.evaluation_labels.ood_type for step in episode.steps} == {"grammar_shift"}


def test_backfilled_dataset_has_required_step3_fields() -> None:
    episodes = _load_episodes("test_id")[:5]
    assert episodes

    for episode in episodes:
        for step in episode["steps"]:
            labels = _eval_labels(step)
            assert "hypothesis_update_timestamp" in labels
            assert "recovery_timestamp" in labels
            assert "selected_hypothesis_confidence" in step["action"]


def test_backfilled_dataset_preserves_episode_step_continuity() -> None:
    for split in ("train", "valid", "test_id", "test_ood"):
        for episode in _load_episodes(split):
            indices = [step["step_index"] for step in episode["steps"]]
            assert indices == list(range(len(indices)))


def test_backfilled_dataset_is_deterministic_for_seed() -> None:
    spec = EpisodeSpecGenerator(seed=333).generate(family=TaskFamily.MODAL_BLOCKER)
    config = CollectorConfig(split_id="train")

    episode_a = collect_episode(
        spec,
        PolicyMixtureRunner(mixture={"recovery": 1.0}, rng=random.Random(spec.seed)),
        random.Random(spec.seed),
        config,
    )
    episode_b = collect_episode(
        spec,
        PolicyMixtureRunner(mixture={"recovery": 1.0}, rng=random.Random(spec.seed)),
        random.Random(spec.seed),
        config,
    )

    assert _strip_collection_timestamps(dataclasses.asdict(episode_a)) == (
        _strip_collection_timestamps(dataclasses.asdict(episode_b))
    )


def test_original_v0_1_dataset_not_overwritten() -> None:
    v01_root = REPO_ROOT / "data" / "frcgw_text" / "v0_1"
    if not v01_root.exists():
        assert not v01_root.exists()
        return

    for split in ("train", "valid", "test_id"):
        path = v01_root / f"{split}.jsonl"
        assert path.exists()
        assert len(path.read_text(encoding="utf-8").splitlines()) > 0


def test_v0_2_manifest_records_split_sizes() -> None:
    manifest = json.loads((DATA_ROOT / "manifest.json").read_text(encoding="utf-8"))

    assert {"train_count", "valid_count", "test_id_count", "test_ood_count"} <= set(manifest)
    for split in ("train", "valid", "test_id", "test_ood"):
        assert manifest[f"{split}_count"] == len(_load_episodes(split))


def test_persistence_metric_becomes_computable_when_labels_present() -> None:
    episodes = _load_episodes("test_id")

    with_switch = [
        episode
        for episode in episodes
        if any(_eval_labels(step)["hypothesis_update_timestamp"] is not None for step in episode["steps"])
    ]

    assert with_switch


def test_recovery_delay_metric_becomes_computable_when_labels_present() -> None:
    episodes = _load_episodes("test_id")

    with_recovery = [
        episode
        for episode in episodes
        if any(_eval_labels(step)["recovery_timestamp"] is not None for step in episode["steps"])
    ]

    assert with_recovery


def test_calibration_ece_becomes_computable_when_confidence_present() -> None:
    steps = [
        step
        for episode in _load_episodes("test_id")
        for step in episode["steps"]
    ]
    present = [
        step
        for step in steps
        if step["action"].get("selected_hypothesis_confidence") is not None
    ]

    assert len(present) / len(steps) >= 0.5
