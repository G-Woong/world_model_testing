TASK_NAME: TASK_1127_step10_abl001_retrain
SANDBOX_MODE: bypass
BACKGROUND:
ABL-001 (l_regime=0.0) faithful retrain이 STEP 10 Loop-03에서 필요하다.
train config는 configs/train_text_v0_4_abl001.yaml로 이미 준비되어 있다.
ABL-001은 regime latent 학습 없을 때 C2 regime_shift_f1이 collapse하는지 검증하기 위해 필요하다.
이 task는 retrain 실행 스크립트와 checkpoint 출력, eval 설정을 준비한다.

GOAL:
1. scripts/risk_hunt/run_abl001_retrain.py 작성 — ABL-001 retrain wrapper script
2. configs/lr_eval_step10_abl001.yaml 생성 — ABL-001 checkpoint eval config
3. tests/test_step10_abl001_retrain.py 작성 — config/script 존재 및 schema 확인

FILES_ALLOWED:
scripts/risk_hunt/run_abl001_retrain.py
configs/lr_eval_step10_abl001.yaml
tests/test_step10_abl001_retrain.py

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
configs/train_text_v0_4_abl001.yaml
src/frcgw/

REQUIRED_IMPLEMENTATION:
1. scripts/risk_hunt/run_abl001_retrain.py:
   ```python
   """ABL-001 faithful retrain launcher for STEP 10 Loop-03.
   
   Runs: python scripts/02_train_text_smoke.py --config configs/train_text_v0_4_abl001.yaml
   Then: runs eval with lr_eval_step10_abl001.yaml
   """
   import subprocess, sys, pathlib
   
   REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
   
   def run_retrain():
       cmd = [sys.executable, "scripts/02_train_text_smoke.py",
              "--config", "configs/train_text_v0_4_abl001.yaml"]
       result = subprocess.run(cmd, cwd=REPO_ROOT)
       return result.returncode == 0
   
   def run_eval():
       cmd = [sys.executable, "scripts/10_run_lr_real_eval.py",
              "--config", "configs/lr_eval_step10_abl001.yaml"]
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
   ```

2. configs/lr_eval_step10_abl001.yaml:
   ```yaml
   version: step10_abl001
   dataset_root: data/frcgw_text/v0_4
   dataset_path: data/frcgw_text/v0_4
   checkpoint_path: outputs/checkpoints/pretrain_v0_4_abl001/checkpoint_best.pt
   model_config: configs/model_text.yaml
   max_episodes: null
   compute_budget:
     planning_calls_cap: 5
     rollout_steps_cap: 10
   agents:
     - id: ABL-001-no-regime
       class: TextFRCGModelAgent
       ckpt_path: outputs/checkpoints/pretrain_v0_4_abl001/checkpoint_best.pt
     - id: FRCG-LR-reference
       class: TextFRCGModelAgent
       ckpt_path: outputs/checkpoints/pretrain_v0_4_long/checkpoint_best.pt
   metrics:
     - falsification_precision_recall
     - threshold_free_c3_auroc
     - regime_shift_f1
     - progress_per_compute
   splits:
     - test_id
     - test_ood
   seeds: [0]
   output_root: outputs/risk_hunt/experiments/loop03_abl001_retrain
   ```

3. tests/test_step10_abl001_retrain.py:
   - test_abl001_train_config_exists(): configs/train_text_v0_4_abl001.yaml exists
   - test_abl001_eval_config_exists(): configs/lr_eval_step10_abl001.yaml exists
   - test_abl001_retrain_script_exists(): scripts/risk_hunt/run_abl001_retrain.py exists
   - test_abl001_eval_config_has_regime_metric(): regime_shift_f1 in eval config

REQUIRED_TESTS:
tests/test_step10_abl001_retrain.py → pytest -q → 4 passed

ACCEPTANCE_CRITERIA:
- scripts/risk_hunt/run_abl001_retrain.py exists
- configs/lr_eval_step10_abl001.yaml exists with regime_shift_f1 metric
- checkpoint_path points to ABL-001 output location
- 4 tests pass

COMMIT_MESSAGE:
feat(step10): ABL-001 retrain launcher + eval config (Loop-03 RH-FAI-01)

STOP_CONDITION:
forbidden path 수정 시 즉시 abort.
configs/train_text_v0_4_abl001.yaml 수정 시 abort (이미 준비된 config).
Codex must not modify claim wording or paper_context_ref/ files.
Codex must not trigger actual training — script should exist but not auto-run.
If task ambiguity arises, emit BLOCKED in RESULT.md.
