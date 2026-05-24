"""R4 falsification gate smoke runner.

Loads a frozen R3 checkpoint, runs evaluate_residuals on all splits,
computes STAGE2 metrics, and writes artifacts.

Source: docs/idea/02_FALSIFICATION_THEORY.md §B-C,
        reports/R3_SMOKE_CLOSURE_REPORT.md §H.3 (R4 PASS thresholds).

Usage:
    python scripts/fglc/r4_falsification.py \
        --config configs/fglc/r4_falsification_pickcube.yaml \
        --r3-checkpoint outputs/r4_falsification/pickcube/r3_model.pt \
        --calibration-split test_id \
        --alpha 0.05 \
        --seed 42 \
        --descriptor pickcube_r4_falsification \
        --output-root outputs/r4_falsification/pickcube
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import torch
import yaml


_R4_PASS_THRESHOLDS = {
    "beta_t_auroc": 0.85,      # AUROC ≥ 0.85 on friction OR gain (R3 closure §H.3)
    "beta_t_fpr_id": 0.05,     # FPR ≤ 0.05 + 2σ tolerance
    "auroc_gain_over_nll": 0.20,  # β_t AUROC - raw NLL AUROC ≥ +0.20
}


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="R4 falsification gate smoke run.")
    p.add_argument("--config", required=True, type=Path)
    p.add_argument("--r3-checkpoint", required=True, type=Path)
    p.add_argument("--calibration-split", default="test_id")
    p.add_argument("--alpha", default=0.05, type=float)
    p.add_argument("--seed", default=42, type=int)
    p.add_argument("--descriptor", required=True)
    p.add_argument("--output-root", required=True, type=Path)
    p.add_argument("--phase", default="R4")
    return p


def main(argv: list[str] | None = None) -> int:
    ns = _parser().parse_args(argv)
    start_wall = time.perf_counter()

    config_path: Path = ns.config
    ckpt_path: Path = ns.r3_checkpoint
    cal_split: str = ns.calibration_split
    alpha: float = ns.alpha
    seed: int = ns.seed
    descriptor: str = ns.descriptor
    output_root: Path = ns.output_root

    if not config_path.exists():
        print(f"ERROR: config not found: {config_path}", file=sys.stderr)
        return 2
    if not ckpt_path.exists():
        print(f"ERROR: R3 checkpoint not found: {ckpt_path}", file=sys.stderr)
        return 2

    config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    config["seed"] = seed
    fals_cfg = config.get("falsification", {})
    sigma_floor = float(fals_cfg.get("sigma_floor", 1e-3))
    use_signed_bias = bool(fals_cfg.get("use_signed_bias", False))

    torch.manual_seed(seed)
    np.random.seed(seed)

    device_str = str(config.get("device", "cpu"))
    if device_str == "cuda" and not torch.cuda.is_available():
        device_str = "cpu"
    config["device"] = device_str

    if device_str == "cuda":
        torch.cuda.reset_peak_memory_stats()

    from fglc.data.dataloader import make_dataloaders
    from fglc.evaluation.falsification_metrics import compute_r4_metrics
    from fglc.evaluation.metrics import Evaluator
    from fglc.schemas.visibility import assert_no_forbidden_fields
    from fglc.training import TrainerConfig, TrainerR3

    # Build trainer (no training)
    trainer_cfg_dict = config["trainer"]
    trainer_config = TrainerConfig(
        batch_size=int(trainer_cfg_dict["batch_size"]),
        train_horizon=int(trainer_cfg_dict["train_horizon"]),
        epochs=0,
        learning_rate=float(trainer_cfg_dict["learning_rate"]),
        optimizer=str(trainer_cfg_dict["optimizer"]),
        loss_weights=dict(trainer_cfg_dict.get("loss_weights", {})),
        device=device_str,
    )
    trainer = TrainerR3(config["model"], trainer_config, device=device_str)

    print(f"[r4] loading R3 checkpoint: {ckpt_path}")
    trainer.load_state(ckpt_path, freeze=True)

    dataloaders = make_dataloaders(config)

    # Forbidden field audit on first batch
    for split_name, dl in dataloaders.items():
        for batch in dl:
            assert_no_forbidden_fields(batch, context=f"R4 dataloader:{split_name}")
            break

    evaluator = Evaluator(trainer, output_dir=output_root / "iter_0")

    print("[r4] computing residuals for all splits ...")
    eval_data: dict[str, dict] = {}
    for split_name, dl in dataloaders.items():
        print(f"  split={split_name} ...")
        eval_data[split_name] = evaluator.evaluate_residuals(dl)

    if cal_split not in eval_data:
        print(f"ERROR: calibration split {cal_split!r} not in dataloaders", file=sys.stderr)
        return 2

    print(f"[r4] computing R4 metrics (alpha={alpha}, calibration_split={cal_split}, use_signed_bias={use_signed_bias}) ...")
    r4_metrics = compute_r4_metrics(
        eval_data,
        calibration_split=cal_split,
        alpha=alpha,
        use_signed_bias=use_signed_bias,
    )

    # Also include R3 NLL metrics
    r3_metrics = evaluator.evaluate(dataloaders)
    all_metrics: dict[str, float] = {**r3_metrics}
    all_metrics.update({k: float(v) for k, v in r4_metrics.items()})

    # Optional: directional bias scores
    if use_signed_bias:
        from fglc.falsification.residuals import directional_bias_score
        for split_name, sd in eval_data.items():
            bias = directional_bias_score(sd["rho_per_group"])
            all_metrics[f"directional_bias_mean_{split_name}"] = float(bias.mean().item())

    # VRAM
    vram_peak = (
        float(torch.cuda.max_memory_allocated() / (1024 ** 2))
        if device_str == "cuda"
        else 0.0
    )
    all_metrics["vram_peak_mib"] = vram_peak
    wall_minutes = (time.perf_counter() - start_wall) / 60.0

    # Write artifacts
    iter_dir = output_root / "iter_0"
    iter_dir.mkdir(parents=True, exist_ok=True)

    metrics_path = iter_dir / "metrics.json"
    metrics_path.write_text(json.dumps(all_metrics, indent=2, sort_keys=True), encoding="utf-8")

    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "phase": ns.phase,
        "config_path": str(config_path),
        "r3_checkpoint": str(ckpt_path),
        "calibration_split": cal_split,
        "alpha": alpha,
        "seed": seed,
        "descriptor": descriptor,
        "wall_clock_minutes": wall_minutes,
        "vram_peak_mib": vram_peak,
    }
    (iter_dir / "run_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )
    (iter_dir / "config.yaml").write_text(
        yaml.safe_dump(config, sort_keys=True), encoding="utf-8"
    )

    # Summary
    print("\n[r4] === R4 metric summary ===")
    for k in sorted(r4_metrics.keys()):
        print(f"  {k}: {r4_metrics[k]:.4f}")

    # Verdict
    auroc_friction = r4_metrics.get("beta_t_auroc_friction", float("nan"))
    auroc_gain = r4_metrics.get("beta_t_auroc_gain", float("nan"))
    fpr_id = r4_metrics.get("beta_t_fpr_id", float("nan"))
    raw_nll_auroc_friction = r4_metrics.get("raw_nll_auroc_friction", float("nan"))
    raw_nll_auroc_gain = r4_metrics.get("raw_nll_auroc_gain", float("nan"))

    threshold = _R4_PASS_THRESHOLDS
    pass_auroc = (
        (auroc_friction >= threshold["beta_t_auroc"]) or
        (auroc_gain >= threshold["beta_t_auroc"])
    )
    pass_fpr = fpr_id <= threshold["beta_t_fpr_id"] * 2
    pass_gain_friction = (
        (auroc_friction - raw_nll_auroc_friction) >= threshold["auroc_gain_over_nll"] or
        (auroc_gain - raw_nll_auroc_gain) >= threshold["auroc_gain_over_nll"]
    )

    if pass_auroc and pass_fpr and pass_gain_friction:
        verdict = "PASS"
    elif pass_auroc or (auroc_friction >= 0.7 or auroc_gain >= 0.7):
        verdict = "PARTIAL_PASS"
    else:
        verdict = "PATCH_REQUIRED"

    print(f"\n[r4] VERDICT: {verdict}")
    print(f"  pass_auroc={pass_auroc}  pass_fpr={pass_fpr}  pass_gain_vs_nll={pass_gain_friction}")
    print(f"  artifacts: {iter_dir}")

    all_metrics["r4_verdict"] = verdict
    metrics_path.write_text(json.dumps(all_metrics, indent=2, sort_keys=True), encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
