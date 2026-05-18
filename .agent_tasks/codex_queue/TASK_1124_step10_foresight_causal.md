TASK_NAME: TASK_1124_step10_foresight_causal
SANDBOX_MODE: bypass
BACKGROUND:
STEP 10 Loop-04 (RH-FORE-01)는 world model rollout이 policy action을 실제로 바꾸는지
인과적으로 검증한다. Claim-C: "foresight planning changes action choice in ≥10% of steps."
현재 frcg_agent.py act()는 rollout 결과를 반영한 action만 반환한다.
rollout이 없었더라면 선택했을 action(rollout_off_action)을 함께 계산하여
두 action이 다른 경우를 action_changed_by_rollout=True로 기록해야 한다.
이 divergence_rate = E[action_changed_by_rollout] 가 Claim-C 근거가 된다.

GOAL:
1. src/frcgw/evaluation/frcg_agent.py 수정:
   - act() 메서드에 rollout_off_action 계산 추가
   - action_changed_by_rollout: bool 을 step_result에 기록
   - public_observation만 사용, hidden label 미사용
2. src/frcgw/evaluation/eval_runner.py 수정:
   - step_results dict에 action_changed_by_rollout 필드 추가
3. scripts/risk_hunt/compute_foresight_causal.py 작성:
   - eval output JSON 디렉터리 → action_changed_by_rollout 집계 → divergence_rate 출력
4. tests/test_step10_foresight_causal.py 작성

FILES_ALLOWED:
src/frcgw/evaluation/frcg_agent.py
src/frcgw/evaluation/eval_runner.py
scripts/risk_hunt/compute_foresight_causal.py
tests/test_step10_foresight_causal.py

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
src/frcgw/evaluation/ablations.py
src/frcgw/evaluation/metrics.py
src/frcgw/evaluation/baselines.py

REQUIRED_IMPLEMENTATION:
1. src/frcgw/evaluation/frcg_agent.py 수정:
   act() 메서드 내부 (text_frcg_plan 호출 이후):
   a. rollout_off_action 계산:
      - GateConfig를 gate_mode="never_plan"으로 override한 cfg_off 생성
      - cfg_off를 사용해 text_frcg_plan() 호출 (동일 obs, 동일 planner_state)
      - 반환된 action을 rollout_off_action으로 저장
   b. action_changed_by_rollout = (chosen_action.action_id != rollout_off_action.action_id)
   c. act() 반환값에 action_changed_by_rollout 추가:
      - TextFRCGModelAgent에 self.last_action_changed_by_rollout: bool = False 속성 추가
      - act() 마지막에 self.last_action_changed_by_rollout = action_changed_by_rollout
   주의: rollout_off_action 계산 시 planner_state를 수정하면 안 됨
   주의: public_observation만 사용 — hidden label 절대 사용 금지

2. src/frcgw/evaluation/eval_runner.py 수정:
   - _run_episode() 내부 step loop에서 agent.act() 직후:
     step_result["action_changed_by_rollout"] = getattr(agent, "last_action_changed_by_rollout", False)
   - episode_result dict에도 "total_action_changes": sum(s.get("action_changed_by_rollout", False) for s in steps) 추가

3. scripts/risk_hunt/compute_foresight_causal.py:
   ```python
   """Compute divergence_rate = action_changed_by_rollout mean over all steps.
   
   Usage: python scripts/risk_hunt/compute_foresight_causal.py --result-dir outputs/risk_hunt/experiments/
   Source MD: paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md Claim-C foresight causal
   """
   import argparse, json, pathlib

   def compute(result_dir: str) -> dict:
       total_steps = 0
       changed_steps = 0
       for jf in pathlib.Path(result_dir).rglob("episode_results*.json"):
           data = json.loads(jf.read_text())
           episodes = data if isinstance(data, list) else data.get("episodes", [])
           for ep in episodes:
               for step in ep.get("steps", []):
                   total_steps += 1
                   if step.get("action_changed_by_rollout", False):
                       changed_steps += 1
       divergence_rate = changed_steps / total_steps if total_steps > 0 else 0.0
       return {"divergence_rate": divergence_rate, "changed_steps": changed_steps, "total_steps": total_steps}

   if __name__ == "__main__":
       parser = argparse.ArgumentParser()
       parser.add_argument("--result-dir", required=True)
       args = parser.parse_args()
       result = compute(args.result_dir)
       print(f"divergence_rate={result['divergence_rate']:.4f} "
             f"({result['changed_steps']}/{result['total_steps']} steps changed by rollout)")
   ```

4. tests/test_step10_foresight_causal.py:
   - test_foresight_causal_script_exists(): scripts/risk_hunt/compute_foresight_causal.py 존재
   - test_action_changed_attr_default(): TextFRCGModelAgent 인스턴스에 last_action_changed_by_rollout 속성 존재
   - test_eval_runner_records_field(): eval_runner._run_episode step_result에 action_changed_by_rollout 키 존재
   - test_compute_foresight_causal_empty_dir(tmp_path): empty dir → divergence_rate=0.0

REQUIRED_TESTS:
tests/test_step10_foresight_causal.py → pytest -q → 4 passed
tests/test_forbidden_field_mirror_sync.py → GREEN
tests/test_step9_regime_shift_f1.py → GREEN (regression — act() 변경으로 기존 동작 영향 없음 확인)

ACCEPTANCE_CRITERIA:
- TextFRCGModelAgent.last_action_changed_by_rollout 속성 존재 (default=False)
- act() 내부에서 rollout_off_action 계산 및 비교
- eval_runner step_result에 action_changed_by_rollout 키 기록
- compute_foresight_causal.py 존재하고 --result-dir 인수 처리
- 4 tests pass
- no hidden label leakage (public_observation only)

COMMIT_MESSAGE:
feat(step10): foresight causal divergence_rate logger (Loop-04 RH-FORE-01 Claim-C)

STOP_CONDITION:
forbidden path 수정 시 즉시 abort.
visibility.py 수정 시 즉시 abort.
hidden label 사용 시 즉시 abort (true_regime, true_control_grammar 등).
planner.py 수정 시 abort — frcg_agent.py만 수정.
Codex must not modify claim wording or paper_context_ref/ files.
If task ambiguity arises, emit BLOCKED in RESULT.md, do not guess.
