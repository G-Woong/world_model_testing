"""CLI entrypoint for the P3 text smoke training loop."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import json

from frcgw.training.train_text import run_smoke_train


def main() -> int:
    parser = argparse.ArgumentParser(description="Run P3 tiny text smoke training.")
    parser.add_argument("--config", default="configs/train_text.yaml")
    parser.add_argument("--model-config", default="configs/model_text.yaml")
    parser.add_argument("--output-dir", default="outputs/runs/p3_smoke")
    args = parser.parse_args()

    result = run_smoke_train(
        train_cfg_path=args.config,
        model_cfg_path=args.model_config,
        output_dir=args.output_dir,
    )
    print(json.dumps(asdict(result), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
