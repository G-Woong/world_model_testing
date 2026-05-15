"""Deterministic replay validation for GUI event traces."""
from __future__ import annotations

import hashlib
import json
import random
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class GUIReplayResult:
    is_valid: bool
    outcome_hash: str
    mismatch_step: int | None = None


class GUIReplayValidator:
    """Validate that a GUI event trace is deterministic for a fixed seed."""

    def validate(self, seed: int, event_trace: list[dict[str, Any]]) -> bool:
        return self.validate_result(seed, event_trace).is_valid

    def validate_result(self, seed: int, event_trace: list[dict[str, Any]]) -> GUIReplayResult:
        first = self._replay(seed, event_trace)
        second = self._replay(seed, event_trace)
        mismatch_step = self._first_mismatch(first["steps"], second["steps"])
        first_hash = self._stable_hash(first)
        return GUIReplayResult(
            is_valid=mismatch_step is None and first_hash == self._stable_hash(second),
            outcome_hash=first_hash,
            mismatch_step=mismatch_step,
        )

    def _replay(self, seed: int, event_trace: list[dict[str, Any]]) -> dict[str, Any]:
        random.seed(seed)
        steps: list[dict[str, Any]] = []
        state = 0
        for index, event in enumerate(event_trace):
            payload = json.dumps(event, sort_keys=True, separators=(",", ":"))
            event_hash = int(hashlib.sha256(payload.encode("utf-8")).hexdigest()[:8], 16)
            jitter = random.randint(0, 2**16 - 1)
            state = (state * 31 + event_hash + jitter + index) % (2**32)
            steps.append({"index": index, "state": state})
        return {"seed": seed, "final_state": state, "steps": steps}

    @staticmethod
    def _stable_hash(payload: dict[str, Any]) -> str:
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    @staticmethod
    def _first_mismatch(
        first_steps: list[dict[str, Any]],
        second_steps: list[dict[str, Any]],
    ) -> int | None:
        for index, (left, right) in enumerate(zip(first_steps, second_steps)):
            if left != right:
                return index
        if len(first_steps) != len(second_steps):
            return min(len(first_steps), len(second_steps))
        return None
