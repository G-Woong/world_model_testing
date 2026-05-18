TASK_NAME: TASK_1129_step10_n5_multiseed
SANDBOX_MODE: bypass
BACKGROUND:
현재 FRCG-LR C3 F1 baseline은 seed=42 단일 학습 결과이며 std=0.000 (deterministic eval).
STEP 10 Loop-02 (RH-STAT-01)는 5개 독립 학습 seed로 true across-seed variance를 확보한다.
std(F1) > 0.01이면 CI 작성 가능; std ≈ 0이면 architecture invariance로 명시 보고한다.
이 task는 5-seed 학습 launcher script와 multi-seed eval config를 준비한다.
실제 학습은 script가 생성된 후 별도 실행 단계에서 Claude가 직접 수행한다.

GOAL:
1. scripts/risk_hunt/run_multiseed_training.py 작성
   - 5개 seed (42, 123, 456, 789, 999)로 pretrain_v0_4_long stage B 학습
   - 각 seed별 checkpoint 저장: outputs/checkpoints/pretrain_v0_4_seed{N}/
2. configs/lr_eval_step10_multiseed.yaml 작성
   - 5개 checkpoint × 3 agents (FRCG-LR-seed{N}, ABL-036, leakage_sanity_probe)
   - split: test_id, seeds=[0]
3. tests/test_step10_multiseed.py 작성

FILES_ALLOWED:
scripts/risk_hunt/run_multiseed_training.py
configs/lr_eval_step10_multiseed.yaml
tests/test_step10_multiseed.py

FILES_FORBIDDEN:
.claude/
CLAUDE.md
.mcp.json
.venv/
data/
outputs/
secrets/
.env
scripts/run_codex_task.ps1
paper_context_ref/
src/frcgw/schemas/visibility.py
src/frcgw/schemas/step_schema.py
src/frcgw/
configs/train_text_v0_4_abl001.yaml
configs/train_text_v0_4_abl003.yaml

REQUIRED_IMPLEMENTATION:
1. scripts/risk_hunt/run_multiseed_training.py:
   ```python
   """5-seed multiseed training launcher for STEP 10 Loop-02 (RH-STAT-01).
   
   Runs 5 independent pretrain_v0_4_long stage B reruns with different seeds.
   Checkpoint output: outputs/checkpoints/pretrain_v0_4_seed{N}/checkpoint_best.pt
   Source MD: paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md RH-STAT-01
   """
   import argparse
   import subprocess
   import sys
   import pathlib

   REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
   SEEDS = [42, 123, 456, 789, 999]
   BASE_CONFIG = "configs/train_text_v0_4_long.yaml"

   def run_seed(seed: int, dry_run: bool = False) -> bool:
       ckpt_dir = f"outputs/checkpoints/pretrain_v0_4_seed{seed}"
       cmd = [
           sys.executable, "scripts/02_train_text_smoke.py",
           "--config", BASE_CONFIG,
           "--seed", str(seed),
           "--checkpoint-dir", ckpt_dir,
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
   ```

2. configs/lr_eval_step10_multiseed.yaml:
   ```yaml
   version: step10_multiseed
   dataset_root: data/frcgw_text/v0_4
   dataset_path: data/frcgw_text/v0_4
   model_config: configs/model_text.yaml
   max_episodes: null
   compute_budget:
     planning_calls_cap: 5
     rollout_steps_cap: 10
   agents:
     - id: FRCG-LR-seed42
       class: TextFRCGModelAgent
       ckpt_path: outputs/checkpoints/pretrain_v0_4_seed42/checkpoint_best.pt
     - id: FRCG-LR-seed123
       class: TextFRCGModelAgent
       ckpt_path: outputs/checkpoints/pretrain_v0_4_seed123/checkpoint_best.pt
     - id: FRCG-LR-seed456
       class: TextFRCGModelAgent
       ckpt_path: outputs/checkpoints/pretrain_v0_4_seed456/checkpoint_best.pt
     - id: FRCG-LR-seed789
       class: TextFRCGModelAgent
       ckpt_path: outputs/checkpoints/pretrain_v0_4_seed789/checkpoint_best.pt
     - id: FRCG-LR-seed999
       class: TextFRCGModelAgent
       ckpt_path: outputs/checkpoints/pretrain_v0_4_seed999/checkpoint_best.pt
   metrics:
     - falsification_precision_recall
     - threshold_free_c3_auroc
     - regime_shift_f1
     - progress_per_compute
     - fair_ppc
   splits:
     - test_id
   seeds: [0]
   output_root: outputs/risk_hunt/experiments/loop02_multiseed
   ```

3. tests/test_step10_multiseed.py:
   - test_multiseed_script_exists(): scripts/risk_hunt/run_multiseed_training.py 존재
   - test_multiseed_eval_config_exists(): configs/lr_eval_step10_multiseed.yaml 존재
   - test_multiseed_eval_config_has_5_seeds(): agents 5개 포함
   - test_multiseed_script_dry_run(tmp_path): --dry-run 플래그로 subprocess 없이 실행 가능

REQUIRED_TESTS:
tests/test_step10_multiseed.py → pytest -q → 4 passed
tests/test_forbidden_field_mirror_sync.py → GREEN

ACCEPTANCE_CRITERIA:
- scripts/risk_hunt/run_multiseed_training.py 존재, SEEDS=[42,123,456,789,999] 포함
- configs/lr_eval_step10_multiseed.yaml 존재, 5개 agent entry 포함
- --dry-run 실행 시 오류 없음
- 4 tests pass
- no forbidden path 수정

COMMIT_MESSAGE:
feat(step10): 5-seed multiseed training launcher + eval config (Loop-02 RH-STAT-01)

STOP_CONDITION:
forbidden path 수정 시 즉시 abort.
실제 학습 자동 실행 금지 — launcher script만 생성, 실행은 Claude가 별도 수행.
Codex must not modify claim wording or paper_context_ref/ files.
If task ambiguity arises, emit BLOCKED in RESULT.md.
