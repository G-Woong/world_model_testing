"""frcgw.training.monitoring -- Per-step loss and gradient norm logger.

Source MD: paper_context_ref/07_LATENT_ARCHITECTURE_DESIGN.md MOD-07-027
Source MD: paper_context_ref/11_MODEL_DATASET_SCALE_AND_TRAINING_BUDGET_v1.md tiny model
"""
from __future__ import annotations

from dataclasses import fields
from datetime import datetime, timezone
import json
from pathlib import Path

from frcgw.objectives.losses import LossDict


class PublicTraceLogger:
    """Append-only JSONL logger for public training traces."""

    def __init__(self, output_dir: str | Path) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.path = self.output_dir / "training_log.jsonl"
        self._fh = self.path.open("a", encoding="utf-8")

    def log_step(self, step: int, epoch: int, loss_dict: LossDict, grad_norm: float) -> None:
        losses: dict[str, float] = {}
        for field in fields(loss_dict):
            if field.name == "weights":
                continue
            value = getattr(loss_dict, field.name)
            if hasattr(value, "detach"):
                value = value.detach().item()
            losses[field.name] = float(value)

        record = {
            "step": int(step),
            "epoch": int(epoch),
            "losses": losses,
            "grad_norm": float(grad_norm),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._fh.write(json.dumps(record, sort_keys=True) + "\n")
        self._fh.flush()

    def close(self) -> None:
        self._fh.close()
