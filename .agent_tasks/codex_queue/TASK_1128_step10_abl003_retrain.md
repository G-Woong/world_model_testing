TASK_NAME: TASK_1128_step10_abl003_retrain
SANDBOX_MODE: bypass
BACKGROUND:
ABL-003 (merged regime+grammar) faithful retrain이 STEP 10 Loop-03에서 필요하다.
train config는 configs/train_text_v0_4_abl003.yaml로 이미 준비되어 있다.
ABL-003은 regime + grammar latent를 단일 head로 합쳤을 때 C2 + C3 모두 collapse하는지 검증한다.
이 task는 TASK_1127과 동일한 패턴으로 ABL-003용 retrain 스크립트와 eval config를 준비한다.

GOAL:
1. scripts/risk_hunt/run_abl003_retrain.py 작성
2. configs/lr_eval_step10_abl003.yaml 생성
3. tests/test_step10_abl003_retrain.py 작성

FILES_ALLOWED:
scripts/risk_hunt/run_abl003_retrain.py
configs/lr_eval_step10_abl003.yaml
tests/test_step10_abl003_retrain.py

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
configs/train_text_v0_4_abl003.yaml
src/frcgw/

REQUIRED_IMPLEMENTATION:
1. scripts/risk_hunt/run_abl003_retrain.py (identical pattern to run_abl001_retrain.py but for abl003)
2. configs/lr_eval_step10_abl003.yaml:
   - checkpoint_path: outputs/checkpoints/pretrain_v0_4_abl003/checkpoint_best.pt
   - agents: ABL-003-merged + FRCG-LR-reference
   - metrics: falsification_precision_recall, threshold_free_c3_auroc, regime_shift_f1, progress_per_compute
   - output_root: outputs/risk_hunt/experiments/loop03_abl003_retrain

3. tests/test_step10_abl003_retrain.py (same pattern as test_step10_abl001_retrain.py)

REQUIRED_TESTS:
tests/test_step10_abl003_retrain.py → pytest -q → 4 passed

ACCEPTANCE_CRITERIA:
- scripts/risk_hunt/run_abl003_retrain.py exists
- configs/lr_eval_step10_abl003.yaml exists with C2/C3 metrics
- 4 tests pass

COMMIT_MESSAGE:
feat(step10): ABL-003 retrain launcher + eval config (Loop-03 RH-FAI-01)

STOP_CONDITION:
forbidden path 수정 시 즉시 abort.
configs/train_text_v0_4_abl003.yaml 수정 시 abort.
Codex must not modify claim wording or paper_context_ref/ files.
If task ambiguity arises, emit BLOCKED in RESULT.md.
