"""5-seed multiseed training launcher for STEP 10 Loop-02 (RH-STAT-01).

Runs 5 independent pretrain_v0_4_long stage B reruns with different seeds.
Checkpoint output: outputs/checkpoints/pretrain_v0_4_seed{N}/checkpoint_best.pt
Source MD: paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md RH-STAT-01
"""
import argparse
import pathlib
import subprocess
import sys

REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
SEEDS = [42, 123, 456, 789, 999]
BASE_CONFIG = "configs/train_text_v0_4_long.yaml"


def run_seed(seed: int, dry_run: bool = False) -> bool:
    ckpt_dir = f"outputs/checkpoints/pretrain_v0_4_seed{seed}"
    cmd = [
        sys.executable,
        "scripts/02_train_text_smoke.py",
        "--config",
        BASE_CONFIG,
        "--seed",
        str(seed),
        "--checkpoint-dir",
        ckpt_dir,
    ]
    print(f"[multiseed] seed={seed} ckpt_dir={ckpt_dir}")
    if dry_run:
        print(f"  DRY RUN: {' '.join(cmd)}")
        return True
    result = subprocess.run(cmd, cwd=REPO_ROOT)
    return result.returncode == 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--seeds", nargs="+", type=int, default=SEEDS)
    args = parser.parse_args()
    failed = []
    for seed in args.seeds:
        ok = run_seed(seed, dry_run=args.dry_run)
        if not ok:
            failed.append(seed)
            print(f"SEED {seed} FAILED")
    if failed:
        print(f"FAILED seeds: {failed}")
        sys.exit(1)
    print(f"All seeds complete: {args.seeds}")
