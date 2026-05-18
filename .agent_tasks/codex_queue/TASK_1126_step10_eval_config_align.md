TASK_NAME: TASK_1126_step10_eval_config_align
SANDBOX_MODE: bypass
BACKGROUND:
configs/lr_eval_real_v0_4_long.yaml (main eval config)에 regime_shift_f1 metric이 누락되어 있다.
configs/lr_eval_step9_c3_recovery.yaml에는 있다.
두 config의 metric 목록을 일치시켜야 한다.
또한 threshold_free_c3_auroc와 fair_ppc를 main eval config에 추가해야 한다.

GOAL:
1. configs/lr_eval_real_v0_4_long.yaml metrics 목록에 추가:
   - regime_shift_f1
   - threshold_free_c3_auroc (TASK_1123 구현 후 추가)
   - fair_ppc (TASK_1125 구현 후 추가)
2. configs/lr_eval_step9_c3_recovery.yaml에도 threshold_free_c3_auroc, fair_ppc 추가
3. 두 config 파일의 metrics 목록이 일치하는지 검증

FILES_ALLOWED:
configs/lr_eval_real_v0_4_long.yaml
configs/lr_eval_step9_c3_recovery.yaml

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
src/frcgw/evaluation/

REQUIRED_IMPLEMENTATION:
1. configs/lr_eval_real_v0_4_long.yaml metrics 섹션 변경:
   Before:
   ```yaml
   metrics:
     - task_success_rate
     - falsification_precision_recall
     - ood_shift_f1
     - progress_per_compute
     - false_planning_call_rate
   ```
   After:
   ```yaml
   metrics:
     - task_success_rate
     - falsification_precision_recall
     - ood_shift_f1
     - regime_shift_f1
     - threshold_free_c3_auroc
     - progress_per_compute
     - fair_ppc
     - false_planning_call_rate
   ```

2. configs/lr_eval_step9_c3_recovery.yaml metrics 섹션에 threshold_free_c3_auroc, fair_ppc 추가
   (regime_shift_f1은 이미 있음)

REQUIRED_TESTS:
N/A (yaml-only change, no code)

ACCEPTANCE_CRITERIA:
- lr_eval_real_v0_4_long.yaml metrics 목록에 regime_shift_f1, threshold_free_c3_auroc, fair_ppc 존재
- lr_eval_step9_c3_recovery.yaml에 threshold_free_c3_auroc, fair_ppc 존재
- 두 config metrics 목록이 일치

COMMIT_MESSAGE:
feat(step10): align eval configs — add regime_shift_f1, threshold_free_c3_auroc, fair_ppc to main config

STOP_CONDITION:
다른 yaml config 수정 시 abort.
Codex must not modify src/ or paper_context_ref/ files.
Codex must not modify claim wording or metric definitions in documentation.
