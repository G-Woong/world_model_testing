"""CLI entrypoint for the P3 text smoke training loop."""
from __future__ import annotations

import argparse
import tempfile
from dataclasses import asdict
import json
from pathlib import Path

import yaml

from frcgw.training.train_text import run_smoke_train


def main() -> int:
    parser = argparse.ArgumentParser(description="Run P3 tiny text smoke training.")
    parser.add_argument("--config", default="configs/train_text.yaml")
    parser.add_argument("--model-config", default="configs/model_text.yaml")
    parser.add_argument("--output-dir", default="outputs/runs/p3_smoke")
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Override train_cfg.seed (multiseed launcher support).",
    )
    parser.add_argument(
        "--checkpoint-dir",
        default=None,
        help="Alias for --output-dir when launcher wants to align with eval ckpt_path.",
    )
    args = parser.parse_args()

    output_dir = args.checkpoint_dir or args.output_dir
    config_path = args.config

    if args.seed is not None:
        with Path(args.config).open("r", encoding="utf-8") as f:
            train_cfg = yaml.safe_load(f) or {}
        train_cfg["seed"] = int(args.seed)
        tmp = tempfile.NamedTemporaryFile(
            "w",
            delete=False,
            suffix=".yaml",
            encoding="utf-8",
        )
        try:
            yaml.safe_dump(train_cfg, tmp)
        finally:
            tmp.close()
        config_path = tmp.name

    result = run_smoke_train(
        train_cfg_path=config_path,
        model_cfg_path=args.model_config,
        output_dir=output_dir,
    )
    print(json.dumps(asdict(result), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
