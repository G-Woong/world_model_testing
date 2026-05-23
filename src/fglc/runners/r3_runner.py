"""R3 smoke runner for the repair loop.

Source: docs/idea/04_BASE_WORLD_MODEL.md, docs/ROADMAP/04_PHASE_R3_BASE_WORLD_MODEL.md
"""

from __future__ import annotations

import copy
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import torch
import yaml

from fglc.data.dataloader import make_dataloaders
from fglc.evaluation.metrics import evaluate_model
from fglc.repair.orchestrator import RunnerOutput
from fglc.training import TrainerConfig, TrainerR3


def _apply_patch(config: dict, patch: Mapping[str, Any] | None) -> dict:
    if patch is None:
        return config
    result = copy.deepcopy(config)
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _apply_patch(result[key], value)
        else:
            result[key] = value
    return result


def _trainer_config(config: dict, device: str) -> TrainerConfig:
    trainer = config["trainer"]
    return TrainerConfig(
        batch_size=int(trainer["batch_size"]),
        train_horizon=int(trainer["train_horizon"]),
        epochs=int(trainer["epochs"]),
        learning_rate=float(trainer["learning_rate"]),
        optimizer=str(trainer["optimizer"]),
        loss_weights=dict(trainer.get("loss_weights", {})),
        device=device,
    )


class R3SmokeRunner:
    """Run a real R3 smoke train/eval pass for repair-loop integration."""

    def __init__(
        self,
        base_config_path: Path,
        output_root: Path = Path("outputs/repair"),
    ) -> None:
        self.base_config_path = Path(base_config_path)
        self.output_root = Path(output_root)

    def __call__(
        self,
        *,
        phase: str,
        config_path: Path,
        split: str,
        seed: int,
        descriptor: str,
        patch: Mapping[str, Any] | None,
        iter_index: int,
    ) -> RunnerOutput:
        del phase, config_path, split
        start = time.perf_counter()
        loaded = yaml.safe_load(self.base_config_path.read_text(encoding="utf-8"))
        config = _apply_patch(dict(loaded or {}), patch)
        config["seed"] = seed

        torch.manual_seed(seed)
        np.random.seed(seed)
        np.random.default_rng(seed)

        device = str(config.get("device", "cpu"))
        if device == "cuda" and not torch.cuda.is_available():
            device = "cpu"
        config["device"] = device
        if device == "cuda":
            torch.cuda.set_per_process_memory_fraction(0.85)
            torch.cuda.reset_peak_memory_stats()

        dataloaders = make_dataloaders(config)
        trainer_config = _trainer_config(config, device)
        trainer = TrainerR3(config["model"], trainer_config, device=device)
        train_metrics = trainer.train(dataloaders["train_id"], dataloaders["val_id"])

        iter_artifact_dir = self.output_root / f"iter_{iter_index}"
        iter_artifact_dir.mkdir(parents=True, exist_ok=True)
        metrics = evaluate_model(
            trainer,
            dataloaders,
            config["model"],
            trainer_config,
            output_dir=iter_artifact_dir,
        )
        metrics.update(
            {
                "train_wall_clock_minutes": float(train_metrics["wall_clock_minutes"]),
                "train_vram_peak_mib": float(train_metrics["vram_peak_mib"]),
            }
        )

        (iter_artifact_dir / "config.yaml").write_text(
            yaml.safe_dump(config, sort_keys=True),
            encoding="utf-8",
        )
        (iter_artifact_dir / "metrics.json").write_text(
            json.dumps(metrics, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        (iter_artifact_dir / "run_manifest.json").write_text(
            json.dumps(
                {
                    "iter_index": iter_index,
                    "seed": seed,
                    "descriptor": descriptor,
                    "patch": patch,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )

        wall_clock_minutes = (time.perf_counter() - start) / 60.0
        vram_peak_mib = (
            float(torch.cuda.max_memory_allocated() / (1024**2))
            if device == "cuda"
            else 0.0
        )
        return RunnerOutput(
            metrics=dict(metrics),
            wall_clock_minutes=wall_clock_minutes,
            vram_peak_mib=vram_peak_mib,
        )
