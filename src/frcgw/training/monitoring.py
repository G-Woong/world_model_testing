"""frcgw.training.monitoring -- Per-step loss and gradient norm logger.

Source MD: paper_context_ref/07_LATENT_ARCHITECTURE_DESIGN.md MOD-07-027
Source MD: paper_context_ref/11_MODEL_DATASET_SCALE_AND_TRAINING_BUDGET_v1.md tiny model
"""
from __future__ import annotations

from dataclasses import dataclass, field, fields
from datetime import datetime, timezone
import json
import math
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


def check_losses_finite(losses: list[float]) -> bool:
    """Return True when every observed loss is finite."""
    return all(math.isfinite(float(loss)) for loss in losses)


def check_grad_norm(norm: float, threshold: float = 100.0) -> bool:
    """Return True when the gradient norm is finite and within threshold."""
    value = float(norm)
    return math.isfinite(value) and 0.0 <= value <= threshold


def check_f_t_variance(values: list[float], threshold: float = 1e-4) -> str:
    """Classify future F_t variance checks without depending on training F_t output."""
    if len(values) < 3:
        return "INSUFFICIENT_DATA"

    numeric_values = [float(value) for value in values]
    if not check_losses_finite(numeric_values):
        return "DEGENERATE_LOW_VARIANCE"

    mean = sum(numeric_values) / len(numeric_values)
    variance = sum((value - mean) ** 2 for value in numeric_values) / len(numeric_values)
    if variance < threshold:
        return "DEGENERATE_LOW_VARIANCE"
    return "OK"


@dataclass
class TrainingMonitorState:
    step: int
    loss: float
    grad_norm: float
    f_t_variance_status: str
    alerts: list[str] = field(default_factory=list)


def build_monitor_csv_row(state: TrainingMonitorState) -> dict:
    """Build a flat row suitable for CSV monitoring logs."""
    return {
        "step": int(state.step),
        "loss": float(state.loss),
        "grad_norm": float(state.grad_norm),
        "f_t_variance_status": state.f_t_variance_status,
        "alerts": ";".join(state.alerts),
    }
