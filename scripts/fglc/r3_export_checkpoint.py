"""Minimal R3 training run to produce a checkpoint for R4 falsification gate.

Runs 5 epochs on R3 base world model and saves state_dict to --output path.
Does NOT modify R3 closure artifacts (outputs/repair/<task>_r3_*/iter_0/).

Source: docs/idea/12_TRAINING_STAGES.md Stage 2 (R4 freeze policy).
        reports/R3_SMOKE_CLOSURE_REPORT.md §H (R4 entry audit).

Usage:
    python scripts/fglc/r3_export_checkpoint.py \
        --config configs/fglc/r4_falsification_pickcube.yaml \
        --seed 42 \
        --output outputs/r4_falsification/pickcube/r3_model.pt
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import torch
import yaml


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Export R3 checkpoint for R4 frozen reuse.")
    p.add_argument("--config", required=True, type=Path)
    p.add_argument("--seed", default=42, type=int)
    p.add_argument("--output", required=True, type=Path)
    return p


def main(argv: list[str] | None = None) -> int:
    ns = _parser().parse_args(argv)
    config_path: Path = ns.config
    seed: int = ns.seed
    output_path: Path = ns.output

    if not config_path.exists():
        print(f"ERROR: config not found: {config_path}", file=sys.stderr)
        return 2

    config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    config["seed"] = seed

    torch.manual_seed(seed)
    np.random.seed(seed)

    device_str = str(config.get("device", "cpu"))
    if device_str == "cuda" and not torch.cuda.is_available():
        device_str = "cpu"
    config["device"] = device_str

    from fglc.data.dataloader import make_dataloaders
    from fglc.training import TrainerConfig, TrainerR3

    dataloaders = make_dataloaders(config)

    trainer_cfg_dict = config["trainer"]
    trainer_config = TrainerConfig(
        batch_size=int(trainer_cfg_dict["batch_size"]),
        train_horizon=int(trainer_cfg_dict["train_horizon"]),
        epochs=int(trainer_cfg_dict["epochs"]),
        learning_rate=float(trainer_cfg_dict["learning_rate"]),
        optimizer=str(trainer_cfg_dict["optimizer"]),
        loss_weights=dict(trainer_cfg_dict.get("loss_weights", {})),
        device=device_str,
    )

    trainer = TrainerR3(config["model"], trainer_config, device=device_str)
    print(f"[r3_export] training {trainer_config.epochs} epochs on {device_str} ...")
    train_metrics = trainer.train(dataloaders["train_id"], dataloaders["val_id"])

    output_path.parent.mkdir(parents=True, exist_ok=True)
    trainer.save_state(output_path)

    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "config_path": str(config_path),
        "seed": seed,
        "epochs": trainer_config.epochs,
        "train_nll": float(train_metrics["train_nll"]),
        "val_nll": float(train_metrics["val_nll"]),
        "vram_peak_mib": float(train_metrics["vram_peak_mib"]),
        "output_path": str(output_path),
    }
    manifest_path = output_path.with_suffix(".manifest.json")
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    print(f"[r3_export] checkpoint saved: {output_path}")
    print(f"[r3_export] train_nll={train_metrics['train_nll']:.4f}  val_nll={train_metrics['val_nll']:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
