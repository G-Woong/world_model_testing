"""frcgw.text_env.replay — Deterministic replay validator.

Source docs:
- paper_context_ref/04_TEXT_ONLY_SMOKE_TESTBED.md §19
- paper_context_ref/12_DATA_COLLECTION_METHODOLOGY_v1.md §8 text-only
- paper_context_ref/14_TRD_TECHNICAL_REQUIREMENTS_DOCUMENT_v1.md §6
"""
from __future__ import annotations

import dataclasses
import json
import random
from dataclasses import asdict

from frcgw.schemas.episode_schema import EpisodeRecord
from frcgw.schemas.validation import ReplayValidationError
from frcgw.text_env.collector import CollectorConfig, collect_episode
from frcgw.text_env.policies import PolicyMixtureRunner
from frcgw.text_env.state import TextEpisodeSpec


def _episode_to_stable_json(episode: EpisodeRecord) -> str:
    """Serialize EpisodeRecord to a stable JSON string for comparison."""
    def _default(obj):
        if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
            return dataclasses.asdict(obj)
        raise TypeError(f"Not serializable: {type(obj)}")

    raw = dataclasses.asdict(episode)
    # Remove non-deterministic timestamps before comparison
    _strip_timestamps(raw)
    return json.dumps(raw, sort_keys=True)


def _strip_timestamps(d):
    """Recursively remove collection_timestamp keys for determinism check."""
    if isinstance(d, dict):
        d.pop("collection_timestamp", None)
        for v in d.values():
            _strip_timestamps(v)
    elif isinstance(d, list):
        for item in d:
            _strip_timestamps(item)


class ReplayValidator:
    """Validates that episode collection is deterministic given the same seed."""

    def validate(
        self,
        spec: TextEpisodeSpec,
        config: CollectorConfig,
        mixture: dict[str, float] | None = None,
    ) -> bool:
        """Re-collect the episode twice from the same seed and compare.

        Returns True if byte-identical (modulo timestamps), raises
        ReplayValidationError with a diff summary if not.
        """
        ep1 = self._collect(spec, config, mixture)
        ep2 = self._collect(spec, config, mixture)

        j1 = _episode_to_stable_json(ep1)
        j2 = _episode_to_stable_json(ep2)

        if j1 != j2:
            raise ReplayValidationError(
                f"Episode {spec.episode_id} is non-deterministic: "
                f"first_len={len(j1)} second_len={len(j2)}"
            )
        return True

    def validate_batch(
        self,
        specs: list[TextEpisodeSpec],
        config: CollectorConfig,
        mixture: dict[str, float] | None = None,
    ) -> dict[str, bool]:
        """Validate a list of specs; returns {episode_id: passed}."""
        results = {}
        for spec in specs:
            try:
                self.validate(spec, config, mixture)
                results[spec.episode_id] = True
            except ReplayValidationError:
                results[spec.episode_id] = False
        return results

    def _collect(
        self,
        spec: TextEpisodeSpec,
        config: CollectorConfig,
        mixture: dict[str, float] | None,
    ) -> EpisodeRecord:
        rng = random.Random(spec.seed)
        runner = PolicyMixtureRunner(mixture=mixture, rng=random.Random(spec.seed))
        return collect_episode(spec, runner, rng, config)
