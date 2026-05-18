TASK_NAME: TASK_1111_step10_current_state_audit
SANDBOX_MODE: bypass
BACKGROUND:
STEP 10 STEP 0에서 Current State Truth Table(00_current_state_truth_table.md)이 작성되었다.
이 table의 핵심 항목들을 자동으로 검증하는 read-only audit script가 필요하다.
script는 코드/데이터/checkpoint를 직접 읽고 JSON 결과를 출력한다.

GOAL:
1. scripts/risk_hunt/audit_current_state.py 작성 — read-only audit script
2. 출력: outputs/risk_hunt/audits/current_state_audit_<ts>.json

FILES_ALLOWED:
scripts/risk_hunt/
outputs/risk_hunt/audits/
tests/test_step10_current_state_audit.py

FILES_FORBIDDEN:
.claude/
CLAUDE.md
.mcp.json
.venv/
data/
outputs/phase_gates/
outputs/checkpoints/
outputs/runs/
secrets/
.env
scripts/run_codex_task.ps1
paper_context_ref/
src/frcgw/schemas/visibility.py
src/frcgw/schemas/step_schema.py
src/frcgw/evaluation/
src/frcgw/planning/
src/frcgw/falsification/

REQUIRED_IMPLEMENTATION:
1. scripts/risk_hunt/ 디렉터리 생성 (없으면)
2. scripts/risk_hunt/audit_current_state.py:
   - read-only: 아래 항목을 파일 읽기로만 검사, 수정 없음
   - 검사 항목:
     a. sentinel_list: outputs/phase_gates/ 의 *.passed 파일 목록
     b. checkpoint_inventory: outputs/checkpoints/ 디렉터리 목록 + 각각의 checkpoint_best.pt 존재 여부
     c. pretrain_v0_4_long_manifest: outputs/checkpoints/pretrain_v0_4_long/manifest.json 존재 여부
     d. abl001_checkpoint: outputs/checkpoints/pretrain_v0_4_abl001/checkpoint_best.pt 존재 여부
     e. abl003_checkpoint: outputs/checkpoints/pretrain_v0_4_abl003/checkpoint_best.pt 존재 여부
     f. v0_4_manifest: data/frcgw_text/v0_4/manifest.json 읽기 + split_counts 확인
     g. lr_eval_real_v0_4_long_metrics: configs/lr_eval_real_v0_4_long.yaml 읽기 + metrics 목록에 regime_shift_f1 있는지 확인
     h. lr_eval_step9_recovery_metrics: configs/lr_eval_step9_c3_recovery.yaml 읽기 + metrics 목록에 regime_shift_f1 있는지 확인
     i. tau_f_value: src/frcgw/evaluation/frcg_agent.py 읽기 + GateConfig(tau_f=X) 값 grep
     j. no_state_change_proxy_present: src/frcgw/planning/planner.py 읽기 + "no_state_change" 키워드 존재 여부
     k. planner_state_update_called: src/frcgw/planning/planner.py 읽기 + "planner_state.update" 호출 존재 여부
     l. lr_scorer_in_frcg_agent: src/frcgw/evaluation/frcg_agent.py 읽기 + "lr_scorer" import 여부
     m. abl040_forced_F_t: src/frcgw/evaluation/ablations.py 읽기 + "_last_F_t = 10.0" 라인 존재 여부
     n. codex_queue_stale: .agent_tasks/codex_queue/ 에 TASK_1098~TASK_1109 파일 존재 여부
     o. leakage_count: 항상 0 (audit는 leakage check 스크립트를 실행하지 않음, 값은 last_known=0으로 기록)
     p. fake_metric_count: 항상 0 (last_known=0)

   - 출력 형식 (JSON):
     {
       "audit_timestamp": "<ISO timestamp>",
       "sentinel_list": [...],
       "pretrain_v0_4_long_manifest_exists": bool,
       "abl001_checkpoint_exists": bool,
       "abl003_checkpoint_exists": bool,
       "v0_4_total_episodes": int,
       "lr_eval_long_has_regime_shift_f1": bool,
       "lr_eval_recovery_has_regime_shift_f1": bool,
       "tau_f_in_frcg_agent": str,
       "no_state_change_proxy_present": bool,
       "planner_state_update_called": bool,
       "lr_scorer_in_frcg_agent": bool,
       "abl040_forced_F_t_present": bool,
       "codex_queue_stale_task_count": int,
       "last_known_leakage_count": 0,
       "last_known_fake_metric_count": 0
     }

   - 파일명: outputs/risk_hunt/audits/current_state_audit_{YYYYMMDD_HHMMSS}.json

3. tests/test_step10_current_state_audit.py:
   ```python
   """Smoke test for audit_current_state.py."""
   import json
   import subprocess
   import pathlib
   import pytest

   REPO_ROOT = pathlib.Path(__file__).parent.parent

   def test_audit_script_runs():
       result = subprocess.run(
           ["python", "scripts/risk_hunt/audit_current_state.py", "--dry-run"],
           cwd=REPO_ROOT,
           capture_output=True,
           text=True,
           timeout=30,
       )
       assert result.returncode == 0, result.stderr

   def test_audit_json_schema():
       """If any audit JSON exists, validate its schema."""
       audits = list((REPO_ROOT / "outputs/risk_hunt/audits").glob("current_state_audit_*.json"))
       if not audits:
           pytest.skip("No audit JSON yet")
       with open(audits[-1]) as f:
           data = json.load(f)
       required_keys = [
           "audit_timestamp", "sentinel_list", "pretrain_v0_4_long_manifest_exists",
           "abl001_checkpoint_exists", "abl003_checkpoint_exists",
           "last_known_leakage_count", "last_known_fake_metric_count",
       ]
       for k in required_keys:
           assert k in data, f"Missing key: {k}"
       assert data["last_known_leakage_count"] == 0
       assert data["last_known_fake_metric_count"] == 0
   ```

REQUIRED_TESTS:
tests/test_step10_current_state_audit.py → pytest -q → 2 passed (or 1 passed + 1 skipped if no JSON yet)

ACCEPTANCE_CRITERIA:
- scripts/risk_hunt/audit_current_state.py 존재
- python scripts/risk_hunt/audit_current_state.py 실행 시 outputs/risk_hunt/audits/current_state_audit_<ts>.json 생성
- JSON에 16개 필드 모두 존재
- last_known_leakage_count == 0
- last_known_fake_metric_count == 0
- test_step10_current_state_audit.py PASS

COMMIT_MESSAGE:
feat(step10): audit_current_state.py + current state audit JSON + test

STOP_CONDITION:
forbidden path 수정 시 즉시 abort.
audit script가 실제 파일을 수정하거나 삭제하면 즉시 abort.
