"""frcgw.data.text_dataset - P2 JSONL loader, collator, and DataLoader builder.

Source MD: paper_context_ref/06_DATA_SCHEMA_AND_LABELING.md
Source MD: paper_context_ref/15_TDD_TECHNICAL_DESIGN_DOCUMENT_v1.md section 17
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from torch.utils.data import DataLoader, Dataset

from frcgw.schemas.step_schema import (
    CandidateAction,
    PublicHistoryItem,
    PublicObservation,
)
from frcgw.schemas.visibility import assert_agent_observation_safe


@dataclass
class BatchTargets:
    true_regime: str
    true_control_grammar: str
    true_change_point: str
    true_reveal_vs_shift: str
    true_action_effect_type: str
    true_failed_action: bool
    failure_reason: str | None
    progress_delta: float
    recovery_action_id: str | None
    valid_hypothesis_switch: bool | None
    true_wrong_hypothesis: bool | None
    h_exec_id: str | None
    correct_hypothesis_id: str | None
    regime_switch_step: int | None = None   # v0_5 eval-only; None for v0_4


@dataclass
class StepSample:
    public_input: PublicObservation
    targets: BatchTargets
    step_id: str


class TextStepDataset(Dataset):
    """Load P2 episode JSONL and expose flattened step-level samples."""

    def __init__(self, jsonl_path: str | Path) -> None:
        self.jsonl_path = Path(jsonl_path)
        if not self.jsonl_path.exists():
            raise FileNotFoundError(f"JSONL shard not found: {self.jsonl_path}")
        self._samples = self._load_samples(self.jsonl_path)

    def __len__(self) -> int:
        return len(self._samples)

    def __getitem__(self, idx: int) -> StepSample:
        return self._samples[idx]

    @staticmethod
    def _load_samples(jsonl_path: Path) -> list[StepSample]:
        samples: list[StepSample] = []
        with jsonl_path.open("r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                episode = json.loads(line)
                episode_id = str(episode.get("episode_id", ""))
                for fallback_idx, step in enumerate(episode.get("steps", [])):
                    samples.append(_step_to_sample(step, episode_id, fallback_idx, line_no))
        return samples


def collate_fn(batch: list[StepSample]) -> dict[str, list[Any]]:
    public_inputs: list[PublicObservation] = []
    targets: list[BatchTargets] = []
    step_ids: list[str] = []

    for sample in batch:
        try:
            assert_agent_observation_safe(sample.public_input)
        except Exception as exc:
            raise type(exc)(
                f"public_input leakage for step_id={sample.step_id}: {exc}"
            ) from exc
        public_inputs.append(sample.public_input)
        targets.append(sample.targets)
        step_ids.append(sample.step_id)

    return {"public_inputs": public_inputs, "targets": targets, "step_ids": step_ids}


def build_dataloaders(
    manifest_path: str | Path,
    batch_size: int = 8,
    seed: int = 42,
    num_workers: int = 0,
) -> tuple[DataLoader, DataLoader, DataLoader]:
    manifest_path = Path(manifest_path)
    if not manifest_path.exists():
        raise FileNotFoundError(f"manifest not found: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    train_ds = TextStepDataset(_split_path(manifest_path, manifest, "train"))
    valid_ds = TextStepDataset(_split_path(manifest_path, manifest, "valid"))
    test_ds = TextStepDataset(_split_path(manifest_path, manifest, "test_id"))

    generator = None
    if seed is not None:
        import torch

        generator = torch.Generator()
        generator.manual_seed(seed)

    train_dl = DataLoader(
        train_ds,
        batch_size=batch_size,
        shuffle=True,
        collate_fn=collate_fn,
        num_workers=num_workers,
        generator=generator,
    )
    valid_dl = DataLoader(
        valid_ds,
        batch_size=batch_size,
        shuffle=False,
        collate_fn=collate_fn,
        num_workers=num_workers,
    )
    test_dl = DataLoader(
        test_ds,
        batch_size=batch_size,
        shuffle=False,
        collate_fn=collate_fn,
        num_workers=num_workers,
    )
    return train_dl, valid_dl, test_dl


def _step_to_sample(
    step: dict[str, Any],
    episode_id: str,
    fallback_idx: int,
    line_no: int,
) -> StepSample:
    try:
        public_observation = _public_observation_from_dict(step["public_observation"])
        training_labels = step["training_labels"]
        evaluation_labels = step["evaluation_labels"]
    except KeyError as exc:
        raise ValueError(f"missing required step field at line {line_no}: {exc}") from exc

    targets = BatchTargets(
        true_regime=training_labels["true_regime"],
        true_control_grammar=training_labels["true_control_grammar"],
        true_change_point=training_labels["true_change_point"],
        true_reveal_vs_shift=training_labels["true_reveal_vs_shift"],
        true_action_effect_type=training_labels["true_action_effect_type"],
        true_failed_action=training_labels["true_failed_action"],
        failure_reason=training_labels.get("failure_reason"),
        progress_delta=training_labels["progress_delta"],
        recovery_action_id=training_labels.get("recovery_action_id"),
        valid_hypothesis_switch=training_labels.get("valid_hypothesis_switch"),
        true_wrong_hypothesis=evaluation_labels.get("true_wrong_hypothesis"),
        h_exec_id=evaluation_labels.get("h_exec_id"),
        correct_hypothesis_id=evaluation_labels.get("correct_hypothesis_id"),
        regime_switch_step=evaluation_labels.get("regime_switch_t"),  # eval-only; never in public_input
    )
    step_id = step.get("step_id") or f"{episode_id}:step:{fallback_idx}"
    return StepSample(public_input=public_observation, targets=targets, step_id=str(step_id))


def _public_observation_from_dict(data: dict[str, Any]) -> PublicObservation:
    return PublicObservation(
        instruction=data["instruction"],
        dom_snapshot_public=data.get("dom_snapshot_public"),
        accessibility_tree_public=data.get("accessibility_tree_public"),
        history_public=[
            PublicHistoryItem(**item) for item in _coerce_public_list(data.get("history_public"))
        ],
        candidate_actions_public=[
            CandidateAction(**item)
            for item in _coerce_public_list(data.get("candidate_actions_public"))
        ],
    )


def _coerce_public_list(value: Any) -> list[dict[str, Any]]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return []
        parsed = json.loads(stripped)
        if isinstance(parsed, list):
            return parsed
    raise TypeError(f"expected list or serialized list string, got {type(value).__name__}")


def _split_path(manifest_path: Path, manifest: dict[str, Any], split: str) -> Path:
    for key in ("shards", "files", "split_files"):
        split_map = manifest.get(key)
        if isinstance(split_map, dict) and split in split_map:
            candidate = Path(split_map[split])
            return candidate if candidate.is_absolute() else manifest_path.parent / candidate
    return manifest_path.parent / f"{split}.jsonl"
