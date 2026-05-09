"""frcgw.training.train_text -- Smoke training loop for P3 tiny text model.

Source MD: paper_context_ref/11_MODEL_DATASET_SCALE_AND_TRAINING_BUDGET_v1.md tiny model
Source MD: paper_context_ref/08_LOSS_REWARD_TRAINING_OBJECTIVE.md
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import math
from pathlib import Path
from typing import Any

import torch
from torch.optim import Optimizer
from torch.utils.data import DataLoader
import yaml

from frcgw.data.text_dataset import build_dataloaders
from frcgw.models.text_frcg_model import TextFRCGModel
from frcgw.objectives.losses import LossDict, assert_no_objective_leakage, compute_total_loss
from frcgw.training.monitoring import PublicTraceLogger


@dataclass
class EpochResult:
    epoch: int
    n_steps: int
    mean_losses: dict[str, float]
    final_loss: float


@dataclass
class SmokeResult:
    config: dict
    n_epochs: int
    total_steps: int
    all_losses_finite: bool
    checkpoint_paths: list[str]
    manifest_path: str


def _get_action_type_from_batch(batch: dict) -> str:
    """Extract first action type from batch for world model."""
    public_inputs = batch.get("public_inputs", [])
    if not public_inputs:
        return "noop"
    candidate_actions = getattr(public_inputs[0], "candidate_actions_public", None) or []
    if not candidate_actions:
        return "noop"
    return str(getattr(candidate_actions[0], "action_type", "noop") or "noop")


def train_one_epoch(
    model: TextFRCGModel,
    dataloader: DataLoader,
    optimizer: Optimizer,
    weights: dict[str, float],
    logger: PublicTraceLogger,
    device: str = "cpu",
    epoch: int = 0,
    max_steps: int = 80,
    global_step: int = 0,
) -> tuple[EpochResult, int]:
    """Train model for one epoch.

    Source MD: paper_context_ref/11_MODEL_DATASET_SCALE_AND_TRAINING_BUDGET_v1.md
    """
    model.train()
    running: dict[str, float] = {}
    n_steps = 0
    final_loss = 0.0

    for batch in dataloader:
        if n_steps >= max_steps:
            break

        public_inputs = batch["public_inputs"]
        targets = batch["targets"]
        for pub_input in public_inputs:
            assert_no_objective_leakage(pub_input)

        model_out = model.forward(public_inputs)
        action_type = _get_action_type_from_batch(batch)
        world_out = model.world_model_heads.forward_given_action(
            model_out.shared_h,
            model_out.z_state,
            action_type,
            0,
        )
        loss_dict = compute_total_loss(
            model_out,
            world_out,
            F_t=None,
            targets=targets,
            weights=weights,
            public_input=public_inputs,
        )
        _assert_losses_finite(loss_dict)

        optimizer.zero_grad()
        loss_dict.l_total.backward()
        grad_norm = compute_grad_norm(model)
        if not math.isfinite(grad_norm):
            raise FloatingPointError(f"non-finite grad_norm at step {global_step}: {grad_norm}")
        optimizer.step()

        logger.log_step(global_step, epoch, loss_dict, grad_norm)
        for name, value in _loss_scalars(loss_dict).items():
            running[name] = running.get(name, 0.0) + value
        final_loss = float(loss_dict.l_total.detach().item())
        global_step += 1
        n_steps += 1

    mean_losses = {name: value / n_steps for name, value in running.items()} if n_steps else {}
    return EpochResult(epoch=epoch, n_steps=n_steps, mean_losses=mean_losses, final_loss=final_loss), global_step


def compute_grad_norm(model: TextFRCGModel) -> float:
    """Compute total gradient L2 norm."""
    total_norm = 0.0
    for p in model.parameters():
        if p.grad is not None:
            total_norm += p.grad.data.norm(2).item() ** 2
    return total_norm ** 0.5


def save_checkpoint(model, optimizer, epoch, step, cfg, output_dir):
    """Save checkpoint to {output_dir}/checkpoint_ep{epoch}.pt."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    path = output_path / f"checkpoint_ep{epoch}.pt"
    torch.save(
        {
            "epoch": epoch,
            "model_state_dict": model.state_dict(),
            "optimizer_state_dict": optimizer.state_dict(),
            "cfg": cfg,
            "step": step,
        },
        path,
    )
    return path


def write_manifest(n_steps, n_epochs, seed, cfg, final_losses, output_dir):
    """Write manifest.json to output_dir."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    path = output_path / "manifest.json"
    manifest = {
        "seed": seed,
        "n_steps": n_steps,
        "n_epochs": n_epochs,
        "config": cfg,
        "final_losses": final_losses,
    }
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return path


def run_smoke_train(
    train_cfg_path: str | Path,
    model_cfg_path: str | Path,
    output_dir: str | Path = "outputs/runs/p3_smoke",
) -> SmokeResult:
    """Run smoke training from config files."""
    train_cfg = _load_yaml(train_cfg_path)
    model_cfg = _load_yaml(model_cfg_path)
    cfg = {"train": train_cfg, "model": model_cfg}

    seed = int(train_cfg.get("seed", model_cfg.get("seed", 42)))
    torch.manual_seed(seed)

    device = "cpu"
    model = TextFRCGModel(model_cfg).to(device)
    train_loader, valid_loader, test_loader = build_dataloaders(
        _manifest_path(train_cfg),
        batch_size=int(train_cfg.get("batch_size", 8)),
        seed=seed,
        num_workers=0,
    )
    split = str(train_cfg.get("split", "train"))
    dataloader = {"train": train_loader, "valid": valid_loader, "test_id": test_loader}.get(split, train_loader)

    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=float(train_cfg.get("lr", 1.0e-3)),
        weight_decay=float(train_cfg.get("weight_decay", 1.0e-4)),
    )
    weights = dict(train_cfg.get("objective_weights") or {})
    max_epochs = int(train_cfg.get("max_epochs", 2))
    max_steps = int(train_cfg.get("max_steps", 80))

    checkpoint_paths: list[str] = []
    final_losses: dict[str, float] = {}
    global_step = 0
    completed_epochs = 0
    logger = PublicTraceLogger(output_dir)
    try:
        for epoch in range(max_epochs):
            remaining = max_steps - global_step
            if remaining <= 0:
                break
            epoch_result, global_step = train_one_epoch(
                model=model,
                dataloader=dataloader,
                optimizer=optimizer,
                weights=weights,
                logger=logger,
                device=device,
                epoch=epoch,
                max_steps=remaining,
                global_step=global_step,
            )
            completed_epochs += 1
            final_losses = epoch_result.mean_losses
            checkpoint_paths.append(str(save_checkpoint(model, optimizer, epoch, global_step, cfg, output_dir)))
            manifest_path = write_manifest(global_step, completed_epochs, seed, cfg, final_losses, output_dir)
            if epoch_result.n_steps == 0:
                break
    finally:
        logger.close()

    manifest_path = write_manifest(global_step, completed_epochs, seed, cfg, final_losses, output_dir)
    return SmokeResult(
        config=cfg,
        n_epochs=completed_epochs,
        total_steps=global_step,
        all_losses_finite=True,
        checkpoint_paths=checkpoint_paths,
        manifest_path=str(manifest_path),
    )


def _load_yaml(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _manifest_path(train_cfg: dict[str, Any]) -> Path:
    if train_cfg.get("manifest_path"):
        return Path(train_cfg["manifest_path"])
    data_config = train_cfg.get("data_config")
    if data_config:
        data_cfg = _load_yaml(data_config)
        if data_cfg.get("output_dir"):
            return Path(data_cfg["output_dir"]) / "manifest.json"
    return Path("data/frcgw_text/v0_1/manifest.json")


def _loss_scalars(loss_dict: LossDict) -> dict[str, float]:
    return {
        name: float(value.detach().item())
        for name, value in loss_dict.__dict__.items()
        if name != "weights" and hasattr(value, "detach")
    }


def _assert_losses_finite(loss_dict: LossDict) -> None:
    for name, value in _loss_scalars(loss_dict).items():
        if not math.isfinite(value):
            raise FloatingPointError(f"non-finite loss {name}: {value}")
