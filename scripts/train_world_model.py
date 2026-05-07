"""WM training entrypoint (Session 9).

본 스크립트는 ``WMTrainConfig`` yaml을 받아 학습을 시작한다. 학습 루프 구현 자체는
``wm/trainer.py``의 ``Trainer`` 클래스에 있다.

Cursor는 본 스크립트를 *full training*으로 절대 직접 실행하지 않는다 (Session 9 §13).
대신 사용자가 PowerShell에서 직접 실행한다.

지원 CLI:
    --train-config        : configs/wm_train_*.yaml
    --run-name            : outputs/wm_runs/<run_name>
    --variant             : full_model | no_regime | no_change_point | ...
    --resume              : checkpoint path (optional)
    --max-steps           : (optional) yaml 값을 override
    --eval-every-steps    : (optional) yaml 값을 override
    --save-every-steps    : (optional) yaml 값을 override
    --device              : (optional) auto | cuda | cpu
    --precision           : (optional) auto | bf16 | fp16 | fp32
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from falsifiable_regime_world_model.wm import (   # noqa: E402
    Trainer,
    WMConfig,
    WMTrainConfig,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Train RG-4F world model (Session 9).")
    parser.add_argument("--train-config", type=str, required=True)
    parser.add_argument("--run-name", type=str, required=True)
    parser.add_argument("--variant", type=str, default=None,
                        help="full_model | no_regime | no_change_point | no_reveal | no_state_aux. "
                             "지정 시 yaml.variant를 override.")
    parser.add_argument("--resume", type=str, default=None)
    parser.add_argument("--max-steps", type=int, default=None)
    parser.add_argument("--eval-every-steps", type=int, default=None)
    parser.add_argument("--save-every-steps", type=int, default=None)
    parser.add_argument("--device", type=str, default=None)
    parser.add_argument("--precision", type=str, default=None)
    args = parser.parse_args()

    train_cfg = WMTrainConfig.from_yaml(args.train_config)
    if args.variant:
        train_cfg.variant = args.variant
    if args.max_steps is not None:
        train_cfg.max_steps = int(args.max_steps)
    if args.eval_every_steps is not None:
        train_cfg.eval.eval_every_steps = int(args.eval_every_steps)
    if args.save_every_steps is not None:
        train_cfg.checkpoint.save_every_steps = int(args.save_every_steps)
    if args.device is not None:
        train_cfg.device = args.device
    if args.precision is not None:
        train_cfg.precision = args.precision

    wm_cfg = WMConfig.from_yaml(train_cfg.wm_config)

    print(f"[train] run_name={args.run_name}")
    print(f"[train] train_config={args.train_config}  variant={train_cfg.variant}")
    print(f"[train] wm_config={train_cfg.wm_config}  max_steps={train_cfg.max_steps}")
    print(f"[train] batch={train_cfg.batch_size}  chunk={train_cfg.chunk_len}  "
          f"accum={train_cfg.grad_accum_steps}  precision={train_cfg.precision}")

    trainer = Trainer(
        train_cfg=train_cfg, wm_cfg=wm_cfg,
        run_name=args.run_name, resume_from=args.resume,
    )
    summary = trainer.run()
    print(f"\n[train] DONE. global_step={summary['global_step']}  "
          f"elapsed={summary['elapsed_sec']:.1f}s  run_dir={summary['run_dir']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
