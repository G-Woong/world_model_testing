# STEP 9 Current State Audit

date: 2026-05-18
branch: memory-redesign-2026-05-16 @ c5b96ab
gate: O-39 (prerequisite for STEP 1)
status: COMPLETE

---

## 1. Purpose

Phase 1 read-only 탐색 결과(F-1 ~ F-7)를 코드 라인 단위 증거와 함께 공식화.
추가 STEP 0 verification 4개 포함.

---

## 2. Code Evidence: C3 0.0 4중 죽음

### F-1a. tau_f=0.5 과보수

- 파일: `src/frcgw/evaluation/frcg_agent.py:74`
- 코드: `self.gate_config = gate_config or GateConfig(tau_f=0.5)`
- GateConfig 기본값: `decision_gate.py:14` → `tau_f: float = 0.0`
- agent가 기본값을 **override하여 0.5로 설정**
- 실측 `mean_wrong_prob = 0.0996` (STEP 8 metrics)
- `sigmoid(F_t - 0.5) = 0.0996` → `F_t = sigmoid_inv(0.0996) + 0.5 ≈ -2.2 + 0.5 = -1.7`
- `F_t > 0.5` 조건은 이 F_t 분포에서 거의 불가능
- **결론**: 설계 의도(기본값 0.0)와 agent 초기화(0.5)가 불일치 → C3 gate 영원히 통과 불가

### F-1b. eval evidence 0/0/False 하드코딩

- 파일: `src/frcgw/planning/planner.py:116`
- 코드: `evidence = FalsificationEvidence(_effect_type_id(effect_text), 0.0, False)`
- `observed_progress_delta=0.0`, `observed_failed_action=False` 고정
- train path (`train_text.py:107-124`)은 `targets["true_action_effect_type"]`, `targets["progress_delta"]`, `targets["true_failed_action"]` 사용
- eval path는 항상 zero evidence → falsification_score가 가능한 최소값 획득
- **결론**: train과 eval evidence 공급이 비대칭. eval에서 F_t가 suppressed.

### F-1c. PlannerState.update() 호출자 0개

- 파일: `src/frcgw/planning/planner.py:35-38`
- `PlannerState.update(step_idx, hypothesis_id)` 메서드 존재하나 호출자 없음
- `src/` repo-wide grep 결과: `planner_state.update` 매칭 0개
- `h_exec_id = planner_state.get_current(step_idx)` → 항상 `_current_by_step.get(step_idx, 0)` → 항상 0 반환
- `alt_hypotheses`의 `combined_id`와 `h_exec_id=0` 비교: `best_alt_id == h_exec_id`가 빈번 → `P_switch=0.0` → gate 차단
- **결론**: planning 루프에서 h_exec 상태가 절대 업데이트되지 않음 → degenerate planning

### F-1d. lr_scorer가 text evaluation path에서 dead code

- `src/frcgw/falsification/lr_scorer.py` 존재하나 `frcg_agent.py`는 import하지 않음
- `frcg_agent.py`는 `text_frcg_plan` 만 import
- `lr_scorer.py`는 `gui_env/lr_integration.py`에서만 사용
- eval trace에서 `lr_scorer_F_t == last_F_t` (동일값) → lr_scorer 실질적 미사용 증거
- **결론**: lr_scorer 설계 의도(정밀한 falsification evidence)가 text eval path에 미연결

---

## 3. Code Evidence: C4 task_success Ceiling

- 파일: `src/frcgw/evaluation/eval_runner.py:128-130`
```python
total_progress += float(targets.get("progress_delta") or 0.0)
total_return  += float(targets.get("progress_delta") or 0.0)
success = success or total_progress > 0.0
```
- `targets`는 JSONL의 `training_labels` dict에서 로드
- `grammar.py:40-125` effect_map 분석:
  - 모든 8개 grammar의 모든 action에 양수 `progress_delta` 할당 (0.2~0.7)
  - 예: `direct_search.type_query = 0.4`, `required_dropdown.open_dropdown = 0.2`
  - `task_complete` action만이 아니라 **모든 intermediate action**에도 progress_delta > 0
- **결론**: agent가 첫 valid action을 취하면 `total_progress > 0` 즉시 발동 → success=True
- `episode.get("final_success", False)`가 이미 `collector.py:448`에서 올바르게 기록됨
- 1줄 fix: `success = bool(episode.get("final_success", False))`

---

## 4. Code Evidence: C6 ppc 정직성 문제

- `eval_runner.py` progress numerator: `episode["total_progress"]` = dataset의 `training_labels.progress_delta` 합계 → **agent-invariant**
- denominator: `planning_calls + rollout_steps + candidate_actions_scored` = agent self-report
- ABL-036(no_compute_gate): `candidate_actions_scored ≈ 6~11` self-report
- 1st-candidate ablations: `=1` self-report
- **14.7× gap은 self-report 차이만으로 설명 가능**
- compute-matched fair comparison 없이는 C6를 claim evidence로 사용 불가

---

## 5. Code Evidence: ABL-040 2중 차단

- 1차 차단: `eval_runner.py:111` `action, compute_log = agent.act(obs)` — eval_labels 미전달
- `LeakageSanityProbeAblation.act()` (ablations.py:409): `eval_labels is not None and "true_control_grammar" in eval_labels` → 진입 자체 불가
- 2차 차단: 설령 진입해도 `self._agent._last_selected_hypothesis_id = injected_id` write만 → F_t/predicted_wrong/wrong_prob 경로와 미연결
- ablations.py:389-417 확인: F_t forcing 없음
- **결론**: ABL-040은 FRCG-LR과 동일 코드 경로 실행 중

---

## 6. STEP 0 추가 Verification

### 6-1. validate_visibility_contract 호출 범위

- `validation.py:98-106`:
```python
def validate_visibility_contract(episode: EpisodeRecord) -> ValidationResult:
    for i, step in enumerate(episode.steps):
        assert_agent_observation_safe(step.public_observation)
```
- `step.public_observation`만 검사 — EvaluationLabels, TrainingLabels, CounterfactualRecord 미검사
- **결론**: EvaluationLabels에 `true_regime` 추가해도 visibility contract 위반 없음

### 6-2. test_visibility_contract.py EvaluationLabels 범위

- `test_visibility_contract.py:56-58`:
```python
def test_true_regime_in_dict_raises():
    assert_agent_observation_safe({"instruction": "click", "true_regime": "modal"})
```
- 이 테스트는 `true_regime`이 **PublicObservation dict**에 있을 때 raise하는 것을 검증
- EvaluationLabels는 별도 container → 이 테스트와 충돌 없음
- R2 lock 조건: `FORBIDDEN_AGENT_FIELDS` 및 `schema_leakage_guard` token list 무변경 → 충족
- **결론**: `step_schema.py::EvaluationLabels`에 `true_regime: str | None = None` 추가는 R2 lock 통과

### 6-3. world_model_heads.forward_given_action 초기화

- `world_model_heads.py:66-80`:
  - `effect_head = nn.Linear(input_dim, n_effect_types)` — PyTorch 기본 Xavier uniform init
  - `progress_head = nn.Sequential(Linear, ReLU, Linear)` — 동일
  - `failure_head = nn.Linear(input_dim, 1)` — 동일
- 초기화 pathology 없음; 학습 후 weight 정상
- **결론**: F_t variance 비정상의 원인이 아님

### 6-4. grammar.py progress_delta 분포

- `grammar.py:34-127` 전체 8개 grammar effect_map 분석:
  - DIRECT_SEARCH: type_query=0.4, submit_search=0.6
  - REQUIRED_DROPDOWN: open_dropdown=0.2, select_category=0.2, type_query=0.2, submit_search=0.4
  - MODAL_CONFIRM: close_modal=0.4, click_filter=0.6
  - (기타 5개 동일 패턴)
- **모든 action에 0.2~0.7 양수 progress_delta** → task_complete만이 아님
- `collector.py:448` `final_success = engine.is_success(state._hidden_preconditions)` → 진짜 task completion 기반
- **결론**: training_labels.progress_delta를 success 지표로 쓰면 모든 agent가 첫 valid action에서 성공

---

## 7. 살아있음 vs 죽어있음 증거 분리

### 살아있음 (claim 가능)
| Item | Value | Source |
|---|---|---|
| v0_4 episodes | 5000 | STEP 8 |
| leakage_count | 0 | STEP 8 |
| planner_F_t_variance | 0.6840 (n=2645 test_id) | STEP 8 metrics |
| falsification_planner.variance | 0.7879 (n=53) | STEP 8 metrics |
| F_t 자체 | non-degenerate | F_t variance > 0 확인 |
| L_falsification | 0.635 (Stage B) | STEP 8 training |
| gradient path | active | training loss non-degenerate |
| fake_metric_count | 0 | STEP 8 audit |
| hard_checks_all_pass | true | STEP 8 audit |

### 죽어있음 (claim 금지)
| Item | Root Cause | Priority |
|---|---|---|
| C3 fp/recall/f1 = 0.0 (13 agents, 2 splits) | F-1a+b+c+d 동시 | CRITICAL |
| C5 ECE = null (BLOCKED_DEGENERATE_PREDICTOR) | C3 죽음에 종속 | BLOCKED |
| C4 rollout_fidelity = null | eval_labels 미전달 | HIGH |
| C4 alternative_adoption_rate = null | eval_labels 미전달 | HIGH |
| C2 regime_split = null | true_regime 누락 | HIGH |
| task_success 0.994/0.998 ceiling | progress_delta 버그 | HIGH |
| false_planning_call_rate = 0.0 (모든 agent) | tau_f=0.5 차단 | CRITICAL |
| ABL-040 FRCG-LR과 bit-identical | 2중 차단 | CRITICAL |
| predicted_wrong=True: 0개 (n=2645) | tau_f=0.5 차단 | CRITICAL |

---

## 8. STEP 8 누락 Artifact 목록

| Artifact | Status | 영향 |
|---|---|---|
| `outputs/checkpoints/pretrain_v0_4_long/manifest.json` | MISSING | training metadata 인용 불가 |
| ABL-015 faithful retrain checkpoint | MISSING | eval 실행 안 됨 |
| step8_c4_expanded_validation.json | INCOMPLETE (30/30 missing) | C4 n=5 seeds 데이터 0개 |
| step8_direct_threat_baseline_audit.json | metric_file_count=0, all metrics null | BASE-026/027 eval 미실행 |
| BASE-028 faithful | skip (STEP 9) | heuristic만 존재 |
| true_regime in v0_4 EvaluationLabels | MISSING | C2 regime_shift_f1 BLOCKED |

---

## 9. Fix Priority Matrix

| Fix | 파일 | 줄 수 | 효과 |
|---|---|---|---|
| tau_f: 0.5→0.0 | frcg_agent.py:74 | 1 | predicted_wrong gate 개방 |
| predicted_wrong: F_t→wrong_prob | frcg_agent.py:141 | 1 | sigmoid 공간 일관화 |
| evidence progress_delta proxy | planner.py:116 | 5 | F_t 더 정확한 근거 |
| planner_state.update | planner.py:145+ | 3 | h_exec_id 동적 갱신 |
| success fix | eval_runner.py:130 | 1 | C4 ceiling 제거 |
| ABL-040 eval_labels 전달 | eval_runner.py:111 + ablations.py | 10+3 | positive control 활성화 |
| true_regime in EvaluationLabels | step_schema.py + collector.py + metrics.py | ~25 | C2 활성화 |

---

## 10. Gate O-39 Status

**PASS** — Phase 1 발견 F-1~F-7이 코드 라인 단위로 증명되었고, STEP 0 추가 4개 항목 모두 검증 완료.

**다음**: doc 40 (C3 root cause classification) 작성 → Gate O-40 → STEP 2 fix 진행.
