"""Stage 1 evaluator and metrics.json artifact writer."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import torch
from torch import Tensor
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
        "ood_gain_nll",   # action_gain OOD axis (2026-05-24)
        "ood_id_nll_diff",
    }
)
ARTIFACT_KEYS: frozenset[str] = frozenset(
    {"epoch", "wall_clock_minutes", "vram_peak_mib"}
)

STAGE2_CANONICAL_METRIC_KEYS: frozenset[str] = frozenset(
    {
        "beta_t_auroc_friction",
        "beta_t_auroc_gain",
        "beta_t_fpr_id",
        "beta_t_tpr_friction",
        "beta_t_tpr_gain",
        "conformal_threshold",
        "residual_ece",
        "raw_nll_auroc_friction",
        "raw_nll_auroc_gain",
    }
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
        ood_gain_nll = (
            self.trainer.evaluate_nll(dataloaders["ood_gain"])
            if "ood_gain" in dataloaders
            else float("nan")
        )
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
            "ood_gain_nll": float(ood_gain_nll),  # action_gain OOD axis (2026-05-24)
            "ood_id_nll_diff": float(ood_mean - id_nll),
            "epoch": int(self.trainer.epoch),
            "wall_clock_minutes": float(self.trainer.wall_clock_minutes),
            "vram_peak_mib": float(self.trainer.vram_peak_mib),
        }

        self.output_dir.mkdir(parents=True, exist_ok=True)
        metrics_path = self.output_dir / "metrics.json"
        metrics_path.write_text(json.dumps(metrics, indent=2, sort_keys=True), encoding="utf-8")
        return metrics


    @torch.no_grad()
    def evaluate_residuals(self, dataloader: DataLoader) -> dict[str, Tensor]:
        """Accumulate per-step standardized residuals for R4 falsification gate.

        Source: docs/idea/02_FALSIFICATION_THEORY.md §B-C,
                reports/R3_SMOKE_CLOSURE_REPORT.md §H.

        Returns:
            rho_per_group: (N_steps, K, d)   standardized residuals
            F_per_group:   (N_steps, K)      group falsification scores ||ρ_k||₂²
            F_total:       (N_steps,)        total score Σ_k F_k
            raw_nll_step:  (N_steps,)        per-step Gaussian NLL (mean over K,d)
        """
        from fglc.falsification.residuals import (
            group_falsification_scores,
            standardized_residual,
            total_falsification_score,
        )

        trainer = self.trainer
        trainer.modules.eval()

        all_rho: list[Tensor] = []
        all_F_k: list[Tensor] = []
        all_F_total: list[Tensor] = []
        all_nll: list[Tensor] = []

        for batch in dataloader:
            state = batch["state"].to(trainer.device)
            action = batch["action"].to(trainer.device)
            reward = batch["reward"].to(trainer.device)

            z = trainer.encoder(state)
            h = trainer.belief(z, action, reward)
            mu, log_sigma = trainer.dynamics(z, action, h)

            # Temporal alignment: t vs t+1
            z_next = z[:, 1:].detach()     # (B, T-1, K, d)
            mu_t = mu[:, :-1]               # (B, T-1, K, d)
            ls_t = log_sigma[:, :-1]        # (B, T-1, K, d)

            rho = standardized_residual(z_next, mu_t, ls_t)   # (B, T-1, K, d)
            F_k = group_falsification_scores(rho)               # (B, T-1, K)
            F_tot = total_falsification_score(F_k)              # (B, T-1)

            # Per-step Gaussian NLL (mean over latent dims)
            var = torch.exp(2.0 * ls_t)
            nll_elem = 0.5 * (math.log(2 * math.pi) + 2.0 * ls_t + (z_next - mu_t).pow(2) / var)
            nll_step = nll_elem.mean(dim=(-2, -1))              # (B, T-1)

            B, T1 = rho.shape[:2]
            all_rho.append(rho.reshape(B * T1, *rho.shape[2:]).cpu())
            all_F_k.append(F_k.reshape(B * T1, F_k.shape[-1]).cpu())
            all_F_total.append(F_tot.reshape(B * T1).cpu())
            all_nll.append(nll_step.reshape(B * T1).cpu())

        # Directional bias score — captures systematic signed drift (M3, easy-looking OOD)
        # Source: reports/R3_SMOKE_CLOSURE_REPORT.md §H.2-1
        from fglc.falsification.residuals import directional_bias_score

        all_dbs = [directional_bias_score(rho_chunk) for rho_chunk in all_rho]

        return {
            "rho_per_group": torch.cat(all_rho, dim=0),
            "F_per_group": torch.cat(all_F_k, dim=0),
            "F_total": torch.cat(all_F_total, dim=0),
            "raw_nll_step": torch.cat(all_nll, dim=0),
            "directional_bias_step": torch.cat(all_dbs, dim=0),  # (N_steps,)
        }


def evaluate_model(
    trainer: TrainerR3,
    dataloaders: dict[str, DataLoader],
    model_config: dict[str, Any],
    trainer_config: TrainerConfig,
    output_dir: Path | str = Path("outputs") / "repair" / "metrics_tmp",
) -> dict[str, float | int]:
    del model_config, trainer_config
    return Evaluator(trainer, output_dir=output_dir).evaluate(dataloaders)
