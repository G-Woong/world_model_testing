TASK_NAME: TASK_1125_step10_fair_ppc
SANDBOX_MODE: bypass
BACKGROUND:
현재 C6 ppc (progress_per_compute) denominator가 agent self-reported compute units이다.
FRCG-LR: planning_calls + rollout_steps + candidate_actions_scored
ABL-036: heuristic bypass (no model forward) → much smaller denominator
이 불균형이 14.9× advantage의 주요 원인일 수 있다.
Wall-clock 기반 denominator로 fair compute matching을 구현해야 한다.

GOAL:
1. src/frcgw/evaluation/metrics.py에 fair_ppc() 함수 추가 (wall-clock denominator)
2. eval_runner.py의 ComputeBudgetLog에 wall_clock_seconds 필드 활성화
3. frcg_agent.py의 act() 에서 wall_clock_seconds 기록 (time.perf_counter)
4. METRIC_FUNCTIONS에 fair_ppc 등록
5. tests/test_step10_fair_ppc.py 작성

FILES_ALLOWED:
src/frcgw/evaluation/metrics.py
src/frcgw/evaluation/eval_runner.py
src/frcgw/evaluation/frcg_agent.py
tests/test_step10_fair_ppc.py

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
src/frcgw/planning/
src/frcgw/falsification/
src/frcgw/evaluation/ablations.py

REQUIRED_IMPLEMENTATION:
1. frcg_agent.py: act() 메서드에서 wall-clock 기록:
   - import time 추가
   - _t_start = time.perf_counter() before text_frcg_plan()
   - wall_clock_seconds = time.perf_counter() - _t_start
   - ComputeBudgetLog(... wall_clock_seconds=wall_clock_seconds)

2. metrics.py: fair_ppc() 함수:
   ```python
   def fair_ppc(episodes: list[dict]) -> dict[str, float]:
       """Fair compute-matched progress per compute.
       
       Denominator = actual wall_clock_seconds (or self-report if wall_clock=0).
       Avoids self-report bias in planning_calls vs heuristic agents.
       
       Source MD: paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md MET-COMPUTE-001 (fair)
       """
       total_progress, total_wall_clock, total_self_report = 0.0, 0.0, 0.0
       for ep in episodes:
           total_progress += float(ep.get("total_progress", 0))
           for clog in ep.get("compute_logs", [ep.get("compute_log", {})]):
               total_wall_clock += float(clog.get("wall_clock_seconds", 0) or 0)
               total_self_report += (
                   float(clog.get("planning_calls", 0) or 0)
                   + float(clog.get("rollout_steps", 0) or 0)
                   + float(clog.get("candidate_actions_scored", 0) or 0)
               )
       ppc_wall = total_progress / total_wall_clock if total_wall_clock > 0 else 0.0
       ppc_self = total_progress / total_self_report if total_self_report > 0 else 0.0
       return {
           "ppc_wall_clock": ppc_wall,
           "ppc_self_report": ppc_self,
           "total_wall_clock_seconds": total_wall_clock,
           "total_self_report_units": total_self_report,
           "total_progress": total_progress,
       }
   ```

3. eval_runner.py: METRIC_FUNCTIONS에 fair_ppc 추가

4. tests/test_step10_fair_ppc.py:
   - test_fair_ppc_returns_schema(): schema check (keys present)
   - test_fair_ppc_self_report_when_no_wall_clock(): when wall_clock=0 → ppc_wall=0
   - test_fair_ppc_positive_wall_clock(): mock episode with wall_clock=1.0 → ppc_wall > 0
   - test_fair_ppc_in_metric_functions(): registered in METRIC_FUNCTIONS

REQUIRED_TESTS:
tests/test_step10_fair_ppc.py → pytest -q → 4 passed
tests/test_step9_regime_shift_f1.py → GREEN (regression)
tests/test_forbidden_field_mirror_sync.py → GREEN

ACCEPTANCE_CRITERIA:
- fair_ppc() defined in metrics.py with 5-key return dict
- wall_clock_seconds recorded in act() (at least 0.0 fallback)
- METRIC_FUNCTIONS["fair_ppc"] registered
- 4 tests pass
- no regression

COMMIT_MESSAGE:
feat(step10): fair_ppc wall-clock denominator + act() timing (Gate O-EVAL, Loop-06)

STOP_CONDITION:
forbidden path 수정 시 즉시 abort.
visibility.py 수정 시 즉시 abort.
Codex must not modify claim wording, metric definition, baseline list, or ablation list.
If task ambiguity arises, emit BLOCKED in RESULT.md, do not guess.
