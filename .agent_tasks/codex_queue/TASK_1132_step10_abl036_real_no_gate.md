TASK_NAME: TASK_1132_step10_abl036_real_no_gate
SANDBOX_MODE: bypass
BACKGROUND:
현재 ABL-036 (NoCounterfactualTargetAblationAgent)은 heuristic bypass로 구현되어 있어
FRCG model forward를 거치지 않는다. 이 때문에 denominator가 FRCG-LR보다 훨씬 작아
self-reported ppc가 14.9× advantage를 부풀린다.
Loop-06 (RH-EVAL-02)은 fair compute 조건에서 C6 advantage를 재검증한다.
RealNoGateAblation은 FRCG model forward를 거치되 F_t gate를 항상 통과(always_plan=True)시켜
planning_calls를 항상 소비하는 faithful no-gate baseline이다.

GOAL:
1. src/frcgw/evaluation/ablations.py에 RealNoGateAblation 추가:
   - always_plan = True (no F_t gate), FRCG model forward 거침
   - planning_calls += 1 per step
   - ablation_id = "real_no_gate"
   - TextFRCGModelAgent를 wrapping하여 gate_mode="always_plan" override로 구현
2. src/frcgw/evaluation/eval_runner.py에 "real_no_gate" ablation 등록
3. configs/lr_eval_step10_fair_compute.yaml 작성:
   - agents: FRCG-LR, RealNoGateAblation, NoComputeGateAblation (기존 heuristic)
   - metrics: fair_ppc, progress_per_compute
4. tests/test_step10_fair_compute.py 작성

FILES_ALLOWED:
src/frcgw/evaluation/ablations.py
src/frcgw/evaluation/eval_runner.py
configs/lr_eval_step10_fair_compute.yaml
tests/test_step10_fair_compute.py

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
src/frcgw/evaluation/frcg_agent.py
src/frcgw/evaluation/metrics.py
src/frcgw/evaluation/baselines.py

REQUIRED_IMPLEMENTATION:
1. src/frcgw/evaluation/ablations.py에 RealNoGateAblation 추가:
   - TextFRCGModelAgent를 내부에 wrapping (AblatedAgent 상속)
   - act() 내부에서 agent._gate_cfg = GateConfig(gate_mode="always_plan") 를 임시 override
   - 또는 agent.cfg = replace(agent.cfg, gate_mode="always_plan") 패턴 사용
   - planning_calls=1 per step 보장
   - ablation_id = "real_no_gate"
   - 구현 시 TextFRCGModelAgent import 필요

   ```python
   class RealNoGateAblation(AblatedAgent):
       """ABL-036b: Always-plan with full FRCG model forward (faithful no-gate baseline).
   
       Unlike heuristic NoComputeGateAblation, this uses the FRCG model forward pass
       with gate_mode=always_plan. Provides fair wall-clock denominator for C6 claim.
       ablation_id = "real_no_gate"
       Source MD: paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md C6 fair_ppc
       """
   
       def act(
           self,
           obs: PublicObservation,
           eval_labels: dict | None = None,
       ) -> tuple[CandidateAction, ComputeBudgetLog]:
           from frcgw.planning.decision_gate import GateConfig
           from dataclasses import replace as dc_replace
           orig_cfg = getattr(self._agent, "gate_config", None) or GateConfig()
           always_plan_cfg = dc_replace(orig_cfg, gate_mode="always_plan")
           # Temporarily override gate_config for this step
           old_cfg = getattr(self._agent, "gate_config", None)
           try:
               self._agent.gate_config = always_plan_cfg
               action, log = self._agent.act(obs, eval_labels=eval_labels)
           finally:
               self._agent.gate_config = old_cfg
           return action, ComputeBudgetLog(
               planning_calls=1,
               rollout_steps=log.rollout_steps,
               candidate_actions_scored=log.candidate_actions_scored,
               top_k_alternatives=log.top_k_alternatives,
               wall_clock_seconds=log.wall_clock_seconds,
           )
   ```

2. src/frcgw/evaluation/eval_runner.py:
   - AGENT_CLASSES dict (또는 agent 등록 메커니즘)에 "RealNoGateAblation" 추가
   - eval_runner가 YAML config에서 class="RealNoGateAblation" 를 읽어 인스턴스화할 수 있어야 함

3. configs/lr_eval_step10_fair_compute.yaml:
   ```yaml
   version: step10_fair_compute
   dataset_root: data/frcgw_text/v0_4
   dataset_path: data/frcgw_text/v0_4
   model_config: configs/model_text.yaml
   max_episodes: null
   compute_budget:
     planning_calls_cap: 5
     rollout_steps_cap: 10
   agents:
     - id: FRCG-LR
       class: TextFRCGModelAgent
       ckpt_path: outputs/checkpoints/pretrain_v0_4_long/checkpoint_best.pt
     - id: ABL-036b-real-no-gate
       class: RealNoGateAblation
       ckpt_path: outputs/checkpoints/pretrain_v0_4_long/checkpoint_best.pt
     - id: ABL-036-heuristic
       class: NoComputeGateAblation
       ckpt_path: outputs/checkpoints/pretrain_v0_4_long/checkpoint_best.pt
   metrics:
     - fair_ppc
     - progress_per_compute
     - falsification_precision_recall
   splits:
     - test_id
   seeds: [0]
   output_root: outputs/risk_hunt/experiments/loop06_fair_compute
   ```

4. tests/test_step10_fair_compute.py:
   - test_real_no_gate_ablation_class_exists(): RealNoGateAblation importable from ablations.py
   - test_real_no_gate_ablation_id(): RealNoGateAblation.ablation_id == "real_no_gate" (AblationConfig 통해)
   - test_fair_compute_eval_config_exists(): configs/lr_eval_step10_fair_compute.yaml 존재
   - test_fair_compute_config_has_fair_ppc(): fair_ppc in metrics list

REQUIRED_TESTS:
tests/test_step10_fair_compute.py → pytest -q → 4 passed
tests/test_step9_regime_shift_f1.py → GREEN (regression — ablations.py 추가이므로 기존 ablation 영향 없음)
tests/test_forbidden_field_mirror_sync.py → GREEN

ACCEPTANCE_CRITERIA:
- RealNoGateAblation class defined in ablations.py with ablation_id="real_no_gate"
- eval_runner recognizes "RealNoGateAblation" class string
- configs/lr_eval_step10_fair_compute.yaml exists with fair_ppc metric
- 4 tests pass
- no forbidden path modified

COMMIT_MESSAGE:
feat(step10): RealNoGateAblation (faithful ABL-036b) + fair compute eval config (Loop-06 RH-EVAL-02)

STOP_CONDITION:
forbidden path 수정 시 즉시 abort.
visibility.py 수정 시 즉시 abort.
hidden label 사용 금지.
기존 ablation class 수정 금지 (추가만 허용).
Codex must not modify claim wording or paper_context_ref/ files.
If task ambiguity arises, emit BLOCKED in RESULT.md.
