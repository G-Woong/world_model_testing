"""ABL-001 faithful retrain launcher for STEP 10 Loop-03.

Runs: python scripts/02_train_text_smoke.py --config configs/train_text_v0_4_abl001.yaml
Then: runs eval with lr_eval_step10_abl001.yaml
"""
import pathlib
import subprocess
import sys


REPO_ROOT = pathlib.Path(__file__).parent.parent.parent


def run_retrain():
    cmd = [
        sys.executable,
        "scripts/02_train_text_smoke.py",
        "--config",
        "configs/train_text_v0_4_abl001.yaml",
    ]
    result = subprocess.run(cmd, cwd=REPO_ROOT)
    return result.returncode == 0


def run_eval():
    cmd = [
        sys.executable,
        "scripts/10_run_lr_real_eval.py",
        "--config",
        "configs/lr_eval_step10_abl001.yaml",
    ]
    result = subprocess.run(cmd, cwd=REPO_ROOT)
    return result.returncode == 0


if __name__ == "__main__":
    if not run_retrain():
        print("RETRAIN FAILED")
        sys.exit(1)
    if not run_eval():
        print("EVAL FAILED")
        sys.exit(1)
    print("ABL-001 retrain + eval complete")
