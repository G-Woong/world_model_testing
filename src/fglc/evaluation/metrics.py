"""Stage 1 evaluator and metrics.json artifact writer."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from torch.utils.data import DataLoader

from fglc.training import TrainerConfig, TrainerR3


STAGE1_CANONICAL_METRIC_KEYS: frozenset[str] = frozenset(
    {
        "id_nll",
        "train_nll",
        "val_nll",
        "val_train_nll_gap",
        "stagnant_epochs",
        "kstep_nll_slope",
        "ood_mass_nll",
        "ood_friction_nll",
        "ood_id_nll_diff",
    }
)
ARTIFACT_KEYS: frozenset[str] = frozenset(
    {"epoch", "wall_clock_minutes", "vram_peak_mib"}
)


class Evaluator:
    """Evaluate a trained R3 trainer and persist Stage 1 metrics."""

    def __init__(
        self,
        trainer: TrainerR3,
        output_dir: Path | str = Path("outputs") / "repair" / "metrics_tmp",
    ) -> None:
        self.trainer = trainer
        self.output_dir = Path(output_dir)

    def evaluate(self, dataloaders: dict[str, DataLoader]) -> dict[str, float | int]:
        train_nll = self.trainer.evaluate_nll(dataloaders["train_id"])
        id_nll = self.trainer.evaluate_nll(dataloaders["val_id"])
        ood_mass_nll = self.trainer.evaluate_nll(dataloaders["ood_mass"])
        ood_friction_nll = self.trainer.evaluate_nll(dataloaders["ood_friction"])
        ood_mean = (ood_mass_nll + ood_friction_nll) / 2.0

        metrics: dict[str, float | int] = {
            "id_nll": float(id_nll),
            "train_nll": float(train_nll),
            "val_nll": float(id_nll),
            "val_train_nll_gap": float(id_nll - train_nll),
            "stagnant_epochs": int(self.trainer.stagnant_epochs),
            "kstep_nll_slope": float(
                self.trainer.evaluate_kstep_nll_slope(dataloaders["val_id"])
            ),
            "ood_mass_nll": float(ood_mass_nll),
            "ood_friction_nll": float(ood_friction_nll),
            "ood_id_nll_diff": float(ood_mean - id_nll),
            "epoch": int(self.trainer.epoch),
            "wall_clock_minutes": float(self.trainer.wall_clock_minutes),
            "vram_peak_mib": float(self.trainer.vram_peak_mib),
        }

        self.output_dir.mkdir(parents=True, exist_ok=True)
        metrics_path = self.output_dir / "metrics.json"
        metrics_path.write_text(json.dumps(metrics, indent=2, sort_keys=True), encoding="utf-8")
        return metrics


def evaluate_model(
    trainer: TrainerR3,
    dataloaders: dict[str, DataLoader],
    model_config: dict[str, Any],
    trainer_config: TrainerConfig,
    output_dir: Path | str = Path("outputs") / "repair" / "metrics_tmp",
) -> dict[str, float | int]:
    del model_config, trainer_config
    return Evaluator(trainer, output_dir=output_dir).evaluate(dataloaders)
