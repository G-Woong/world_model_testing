"""ABL-001 faithful retrain launcher for STEP 10 Loop-03.

Runs: python scripts/02_train_text_smoke.py --config configs/train_text_v0_4_abl001.yaml
       --output-dir outputs/runs/p3_train_v0_4_abl001
Promotes the last checkpoint_ep*.pt to outputs/checkpoints/abl001_no_regime/checkpoint_best.pt
Then: runs eval with lr_eval_step10_abl001.yaml
"""
import pathlib
import shutil
import subprocess
import sys


REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
TRAIN_OUTPUT_DIR = REPO_ROOT / "outputs" / "runs" / "p3_train_v0_4_abl001"
PROMOTE_DIR = REPO_ROOT / "outputs" / "checkpoints" / "abl001_no_regime"


def run_retrain():
    TRAIN_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable,
        "scripts/02_train_text_smoke.py",
        "--config",
        "configs/train_text_v0_4_abl001.yaml",
        "--output-dir",
        str(TRAIN_OUTPUT_DIR.relative_to(REPO_ROOT).as_posix()),
    ]
    result = subprocess.run(cmd, cwd=REPO_ROOT)
    return result.returncode == 0


def promote_checkpoint() -> bool:
    ckpts = sorted(TRAIN_OUTPUT_DIR.glob("checkpoint_ep*.pt"))
    if not ckpts:
        print(f"NO checkpoint produced in {TRAIN_OUTPUT_DIR}")
        return False
    PROMOTE_DIR.mkdir(parents=True, exist_ok=True)
    target = PROMOTE_DIR / "checkpoint_best.pt"
    shutil.copy2(ckpts[-1], target)
    print(f"Promoted {ckpts[-1].name} -> {target}")
    return True


def run_eval():
    cmd = [
        sys.executable,
        "scripts/10_run_lr_real_eval.py",
        "--config",
        "configs/lr_eval_step10_abl001.yaml",
        "--out-dir",
        "outputs/risk_hunt/experiments/loop03_abl001_retrain",
    ]
    result = subprocess.run(cmd, cwd=REPO_ROOT)
    return result.returncode == 0


if __name__ == "__main__":
    if not run_retrain():
        print("RETRAIN FAILED")
        sys.exit(1)
    if not promote_checkpoint():
        print("PROMOTE FAILED")
        sys.exit(1)
    if not run_eval():
        print("EVAL FAILED")
        sys.exit(1)
    print("ABL-001 retrain + eval complete")
