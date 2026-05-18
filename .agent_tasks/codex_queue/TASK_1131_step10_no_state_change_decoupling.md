TASK_NAME: TASK_1131_step10_no_state_change_decoupling
SANDBOX_MODE: bypass
BACKGROUND:
STEP 9에서 C3 F1=0.0→0.539를 달성한 핵심 fix 중 하나는 planner.py:120-126의
no_state_change→effect_type=3 proxy이다.
RH-CORE-01은 이 proxy가 없을 때 F1이 0.0으로 회귀할 수 있음을 지적한다.
Loop-01 (RH-CORE-01) 검증을 위해 proxy OFF eval config를 생성하고 eval 결과를 비교해야 한다.
이 task는 proxy ON/OFF 비교를 위한 eval config + eval runner 수정이다 (proxy 제거는 하지 않음).

GOAL:
1. configs/lr_eval_step10_proxy_ablation.yaml 생성
   - proxy OFF 모드를 지원하는 eval config
2. src/frcgw/planning/planner.py에 --no-proxy flag 지원 추가 (GateConfig optional)
3. scripts/risk_hunt/run_proxy_ablation_eval.py 작성 (proxy ON vs OFF 비교 eval)
4. tests/test_step10_proxy_ablation.py 작성

FILES_ALLOWED:
configs/lr_eval_step10_proxy_ablation.yaml
src/frcgw/planning/planner.py
scripts/risk_hunt/run_proxy_ablation_eval.py
tests/test_step10_proxy_ablation.py

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
src/frcgw/evaluation/frcg_agent.py
src/frcgw/evaluation/ablations.py
src/frcgw/planning/falsification.py

REQUIRED_IMPLEMENTATION:
1. src/frcgw/planning/planner.py 수정:
   - text_frcg_plan() 시그니처에 `use_no_state_change_proxy: bool = True` 파라미터 추가
   - line 122 게이팅:
     `if use_no_state_change_proxy: _obs_effect_type_id = 3 if _effect_key == "no_state_change" else _effect_type_id(effect_text)`
     `else: _obs_effect_type_id = _effect_type_id(effect_text)` (proxy 없음, no special-case)
   - line 124 게이팅 (반드시 함께 처리):
     `if use_no_state_change_proxy: _observed_failed = any(kw in _effect_key for kw in _failed_keywords) or _effect_key == "no_state_change"`
     `else: _observed_failed = any(kw in _effect_key for kw in _failed_keywords)` (no_state_change 특수처리 없음)
   - default=True → 기존 동작 유지 (regression 없음)
   - 두 줄(122, 124) 모두 게이팅하지 않으면 proxy=OFF 결과가 부분적 proxy임 (Fix-B 요구사항)

2. GateConfig에 `use_no_state_change_proxy: bool = True` 필드 추가
   - src/frcgw/planning/decision_gate.py 수정
   - frcg_agent.py는 GateConfig를 그대로 전달 → 변경 불필요

3. configs/lr_eval_step10_proxy_ablation.yaml:
   ```yaml
   version: step10_proxy_ablation
   dataset_root: data/frcgw_text/v0_4
   dataset_path: data/frcgw_text/v0_4
   checkpoint_path: outputs/checkpoints/pretrain_v0_4_long/checkpoint_best.pt
   model_config: configs/model_text.yaml
   max_episodes: null
   compute_budget:
     planning_calls_cap: 5
     rollout_steps_cap: 10
   agents:
     - id: FRCG-LR-proxy-on
       class: TextFRCGModelAgent
       ckpt_path: outputs/checkpoints/pretrain_v0_4_long/checkpoint_best.pt
     - id: FRCG-LR-proxy-off
       class: TextFRCGModelAgent
       gate_config:
         use_no_state_change_proxy: false
       ckpt_path: outputs/checkpoints/pretrain_v0_4_long/checkpoint_best.pt
   metrics:
     - falsification_precision_recall
     - threshold_free_c3_auroc
     - progress_per_compute
   splits:
     - test_id
   seeds: [0]
   output_root: outputs/risk_hunt/experiments/loop01_proxy_ablation
   ```

4. tests/test_step10_proxy_ablation.py:
   - test_proxy_flag_default_true(): GateConfig() default use_no_state_change_proxy=True
   - test_proxy_flag_false_changes_effect_type(): with proxy=False, no_state_change → type=0 (not 3)
   - test_text_frcg_plan_with_proxy_on(): smoke call, no error
   - test_text_frcg_plan_with_proxy_off(): smoke call, no error

REQUIRED_TESTS:
tests/test_step10_proxy_ablation.py → pytest -q → 4 passed
tests/test_forbidden_field_mirror_sync.py → GREEN
기존 tests/test_step9_regime_shift_f1.py → GREEN (no regression — proxy=True is default)

ACCEPTANCE_CRITERIA:
- GateConfig has use_no_state_change_proxy field (default=True)
- text_frcg_plan() accepts use_no_state_change_proxy parameter
- proxy OFF path: _obs_effect_type_id = _effect_type_id(effect_text) without special-casing no_state_change
- eval config exists with proxy-off agent
- 4 tests pass
- no regression in existing tests

COMMIT_MESSAGE:
feat(step10): proxy ablation flag in GateConfig + eval config (Loop-01 RH-CORE-01 verification)

STOP_CONDITION:
forbidden path 수정 시 즉시 abort.
planner.py에서 proxy=True (default) 경로 변경 시 abort (regression risk).
falsification.py 수정 시 abort.
Codex must not modify claim wording or paper_context_ref/ files.
If task ambiguity arises, emit BLOCKED in RESULT.md, do not guess.
