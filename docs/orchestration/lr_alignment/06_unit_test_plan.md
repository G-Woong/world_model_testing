---
file_id: UNIT-TEST-PLAN-R3
title: Unit Test Plan — Phase 6 산출물
phase: 6 (Unit Test Plan)
run: 3
date: 2026-05-16
status: TEST_PLAN_DOCUMENT
language: ko
type: test_plan_not_implementation
---

# 06_unit_test_plan.md

**Phase**: 6 — Unit Test Plan  
**Run**: 3  
**Date**: 2026-05-16  
**Type**: 테스트 계획 문서. 실제 assertion 로직 없음. Run 3에서는 구현하지 않는다.

---

## Section 1. Purpose

이 문서는 **실제 테스트 구현이 아니다**.

역할:
- Run 4 unit test 구현 전에 test 계약을 고정
- C1/C3/C5 primary survival axis를 검증하는 test group을 우선 정의
- C2/C4/C6 supporting/high-risk claim의 검증을 별도 분리
- test stub 파일 (함수 이름 + docstring만)의 근거 문서

이 문서에서 절대 하지 않는 것:
- 실제 assertion 로직 작성 (fixture/data load/assert 금지)
- `tests/test_ablation_runner.py` count 수정
- `paper_context_ref/` 수정
- 기존 `src/frcgw/` 파일 수정
- P3 재학습 또는 P3_EVAL 재실행
- C1~C6 ALIVE/DEAD 확정

핵심 원칙: **약화가 아니라 정렬**. C1/C3/C5 primary survival axis는 이 테스트 계획의 최우선 검증 대상이다.

---

## Section 2. Test Scope

각 test group은 아래 4단계 Run에 걸쳐 구현된다.

| Run | 단계 | 허용 작업 |
|---|---|---|
| **Run 3** | stub only | 함수 이름 + docstring. `pytest.skip` 또는 `pass` 만 |
| **Run 4** | real unit | 실제 assertion 구현. Group A/B/C/F/G Priority 1 우선 |
| **Run 5** | baseline + ablation | ABL-017/022/036 추가 후 Group C/E/F 확장. test_ablation_runner.py count 동반 업데이트 |
| **Run 6** | eval + gate | full eval 후 Group D/E/F/G 완성. Evidence Card 갱신 artifact 검증 |

---

## Section 3. Required Test Groups (A~G)

---

### Group A — Stub Import and Signature Tests

**Purpose**: `lr_scorer_stub.py`의 14개 symbol이 올바르게 정의되어 import 가능함을 확인.  
**Connected claim**: C3 (falsification mechanism) — stub 계약  
**Future run**: Run 4 (실제 import 검증)

| 테스트 함수 | 검증 내용 | 연결 symbol |
|---|---|---|
| `test_stub_imports` | torch/numpy 없이 import 가능 | 전체 모듈 |
| `test_required_dataclasses_exist` | 9개 dataclass 모두 존재 | 9개 dataclass |
| `test_required_component_classes_exist` | 5개 component class 모두 존재 | 5개 class |
| `test_methods_raise_not_implemented` | score/update/decide/rewrite → NotImplementedError | 5개 method |
| `test_no_torch_numpy_dependency_in_stub` | AST에 외부 ML 라이브러리 import 없음 | 모듈 import 목록 |

---

### Group B — h_exec Trace Contract Tests

**Purpose**: `selected_hypothesis_id` 필드가 step log에 올바르게 populate됨을 확인.  
C1 (wrong-grammar persistence)의 blocker 해소 조건 검증.  
**Connected claim**: C1 (primary survival axis)  
**Future run**: Run 4 Priority 1

| 테스트 함수 | 검증 내용 | 연결 blocker |
|---|---|---|
| `test_h_exec_trace_has_selected_hypothesis_id` | HypothesisTrace에 selected_hypothesis_id 필드 존재 | C1 BLOCKED: h_exec trace 미구현 |
| `test_h_exec_is_predicted_trace_not_oracle_label` | is_oracle_label=False 항상 | Anti-leakage: oracle label 혼동 금지 |
| `test_missing_h_exec_blocks_persistence_metric` | h_exec 없으면 F_t=0 + BLOCKER | P3_EVAL.BLOCKED_planning_calls_zero 재현 방지 |

---

### Group C — LR Falsification Tests

**Purpose**: F_t = max_alt[ell(h_alt) - ell(h_exec)] 계약 검증.  
BCE가 main path가 아님을 확인. uncertainty gate와 구분.  
**Connected claim**: C3 (primary survival axis)  
**Future run**: Run 4 Priority 1 (기본 케이스), Run 6 (ABL-022/023 비교)

| 테스트 함수 | 검증 내용 | Required ablation/baseline |
|---|---|---|
| `test_lr_score_positive_when_alt_explains_evidence_better` | alt > exec → F_t > 0 | ABL-022 비교 (Run 6) |
| `test_lr_score_zero_or_negative_when_exec_explains_evidence_better` | exec > alt → F_t ≤ 0 | ABL-022 비교 (Run 6) |
| `test_all_equal_likelihoods_sets_degenerate_flag` | all equal → degenerate=True | degenerate case 처리 |
| `test_empty_alternatives_blocks_falsification` | empty H_alt → F_t=0, degenerate=True | degenerate case 처리 |
| `test_bce_not_main_path` | BCE ≠ LR main score() pathway | ABL-022/ABL-023 분리 |
| `test_uncertainty_gate_not_equivalent_to_lr_gate` | G_t 4-way ≠ uncertainty > threshold | ABL-023 (uncertainty instead), BASE-012 비교 |

---

### Group D — Posterior Update Tests

**Purpose**: `PosteriorUpdater`의 b_t 계산 계약 검증.  
posterior collapse, over-switching, leakage 없는 update 확인.  
**Connected claim**: C3/C2 (C2 = high-risk architecture hypothesis)  
**Future run**: Run 4 (기본 케이스), Run 6 (ABL-001/crossed split 비교)

| 테스트 함수 (Run 4에서 작성) | 검증 내용 | Connected claim |
|---|---|---|
| `test_posterior_shifts_when_strong_evidence` | strong evidence → posterior 변화 | C3 |
| `test_posterior_stable_when_no_effect_evidence` | no_effect_flag=True → 작은 변화 | C3 |
| `test_posterior_no_oracle_label_in_update` | H_t에 FORBIDDEN_AGENT_FIELDS 없음 | Anti-leakage |
| `test_posterior_collapse_detected_and_logged` | 단일 collapse → 경고 로그 | C2 KNOWN RISK |
| `test_over_switching_triggers_leakage_probe` | no_effect이지만 큰 변화 → ABL-040 트리거 | Anti-leakage |

---

### Group E — Decision Relevance Gate Tests

**Purpose**: G_t 4-way conjunction 계약 검증. G_t never fires / always fires 감지.  
**Connected claim**: C6 (supporting efficiency claim)  
**Future run**: Run 6 (full eval 후, BASE-015 / CATTS-equivalent 비교 포함)

| 테스트 함수 (Run 6에서 작성) | 검증 내용 | Required baseline |
|---|---|---|
| `test_gate_fires_when_all_conditions_met` | 4개 조건 충족 → G_t=True | ABL-034 경계 |
| `test_gate_blocked_when_f_t_below_threshold` | F_t < τ_f → G_t=False | BASE-012 비교 |
| `test_gate_different_from_uncertainty_gate` | high-conf wrong grammar case: G_t=True, uncertainty gate=False | CATTS-equivalent |
| `test_planning_calls_not_zero_in_smoke` | G_t fires ≥ 10% episodes | P3_EVAL.BLOCKED 해소 |
| `test_false_planning_call_rate_below_threshold` | 불필요한 planning call 비율 < threshold | MET-COMP-003 |

---

### Group F — Rewrite Tests

**Purpose**: `GrammarConditionedRewrite` 계약 검증. h*가 oracle이 아님. fallback 작동.  
**Connected claim**: C5 (primary survival axis)  
**Future run**: Run 4 (기본 케이스), Run 6 (ABL-017/035/BASE-026 비교)

| 테스트 함수 (Run 4에서 작성, Run 6 확장) | 검증 내용 | Required ablation |
|---|---|---|
| `test_rewrite_uses_predicted_hypothesis_not_oracle` | selected_hypothesis.is_oracle_label=False | Anti-leakage |
| `test_fallback_triggered_when_low_confidence` | rewrite_confidence < τ_r → fallback=True | C5 fallback rule |
| `test_no_op_rewrite_not_always` | a_exec == a_base 항상이면 C5 mechanism 누락 | ABL-035 경계 |
| `test_rewrite_distinct_from_wac_style` | WAC-style rewrite와 다른 action 생성 | BASE-026 비교 |
| `test_abl_017_ablation_reduces_rewrite_quality` | ABL-017 (no_L_intent_action_mapping) → rewrite 품질 저하 | ABL-017 (Run 5) |

---

### Group G — Anti-Leakage Tests

**Purpose**: 모든 leakage 안전성 계약 검증. hidden label이 inference input에 들어가지 않음.  
**Connected claim**: 전체 (C1~C6 공통)  
**Future run**: Run 4 Priority 1, Run 6 (full audit)

| 테스트 함수 | 검증 내용 | 연결 필드 |
|---|---|---|
| `test_selected_hypothesis_not_in_forbidden_agent_fields` | selected_hypothesis_id ∉ FORBIDDEN_AGENT_FIELDS | visibility.py |
| `test_true_control_grammar_not_in_inference_input` | true_control_grammar ∉ EvidenceFeatures | FORBIDDEN_AGENT_FIELDS |
| `test_true_regime_not_in_inference_input` | true_regime ∉ EvidenceFeatures | FORBIDDEN_AGENT_FIELDS |
| `test_counterfactual_table_not_in_inference_input` | counterfactual_action_effects ∉ input | CounterfactualLeakageError |
| `test_future_evidence_not_available_to_scorer` | e_t = 현재 step evidence만 | anti-leakage boundary |
| `test_forbidden_field_mirror_sync_still_green` | test_forbidden_field_mirror_sync.py green 유지 | visibility.py sync |

---

## Section 4. Test Stub File Contract

### 4.1 `tests/test_lr_scorer_stub.py`

**파일 규칙**:
- pytest 함수 이름만 생성 (Section 3 Group A/C 일부)
- 내부는 `pytest.skip("Run 3 stub only; implement assertions in Run 4.")` 또는 `pass`
- 실제 assertion 없음
- fixture/data load 없음
- repository state 변경 없음 (src/tests/outputs 수정 없음)
- hidden label 접근 없음

**필수 함수 (11개)**:
1. `test_stub_imports` — Group A
2. `test_required_dataclasses_exist` — Group A
3. `test_required_component_classes_exist` — Group A
4. `test_methods_raise_not_implemented` — Group A
5. `test_no_torch_numpy_dependency_in_stub` — Group A
6. `test_lr_score_positive_when_alt_explains_evidence_better` — Group C
7. `test_lr_score_zero_or_negative_when_exec_explains_evidence_better` — Group C
8. `test_all_equal_likelihoods_sets_degenerate_flag` — Group C
9. `test_empty_alternatives_blocks_falsification` — Group C
10. `test_bce_not_main_path` — Group C
11. `test_uncertainty_gate_not_equivalent_to_lr_gate` — Group C/E

### 4.2 `tests/test_h_exec_trace_stub.py`

**파일 규칙**: 동일 (위 4.1 규칙 적용)

**필수 함수 (9개)**:
1. `test_h_exec_trace_has_selected_hypothesis_id` — Group B
2. `test_h_exec_is_predicted_trace_not_oracle_label` — Group B
3. `test_missing_h_exec_blocks_persistence_metric` — Group B
4. `test_selected_hypothesis_not_in_forbidden_agent_fields` — Group G
5. `test_true_control_grammar_not_in_inference_input` — Group G
6. `test_true_regime_not_in_inference_input` — Group G
7. `test_counterfactual_table_not_in_inference_input` — Group G
8. `test_future_evidence_not_available_to_scorer` — Group G
9. `test_forbidden_field_mirror_sync_still_green` — Group G

---

## Section 5. Claim Mapping (A~G × claim × role × run)

| Group | Test 파일 | Connected Claim | Survival Role | Run 3 Status | Future Run |
|---|---|---|---|---|---|
| **A** Stub Signature | test_lr_scorer_stub.py | C3 | primary survival axis — contract | stub (skip) | Run 4 |
| **B** h_exec Trace | test_h_exec_trace_stub.py | **C1** | primary survival axis — blocker 해소 | stub (skip) | Run 4 Priority 1 |
| **C** LR Falsification | test_lr_scorer_stub.py | **C3** | primary survival axis — mechanism | stub (skip) | Run 4 Priority 1, Run 6 ABL-022/023 |
| **D** Posterior Update | (Run 4 작성) | C3/C2 | primary (C3) + high-risk (C2) | 미작성 | Run 4, Run 6 |
| **E** Decision Relevance Gate | (Run 6 작성) | C6 | supporting efficiency | 미작성 | Run 6 |
| **F** Rewrite | (Run 4 시작) | **C5** | primary survival axis — mechanism | 미작성 | Run 4, Run 5 ABL-017, Run 6 |
| **G** Anti-Leakage | test_h_exec_trace_stub.py | C1~C6 전체 | leakage safety | stub (skip) | Run 4 Priority 1 |

---

## Section 6. `tests/test_ablation_runner.py` Count Warning

### 6.1 현재 상태

`tests/test_ablation_runner.py:63` (또는 해당 count assertion line)은 현재 ablation 개수를 고정하고 있다.

**Run 3에서는 이 파일을 수정하지 않는다.**

### 6.2 Run 5에서의 필수 동반 업데이트

Run 5 (Phase 10)에서 ablation registry에 다음 항목을 추가할 때:
- ABL-017 (no_L_intent_action_mapping) 추가
- ABL-022 (no falsification score gate) standalone 등록
- ABL-036 (no_counterfactual_target) 추가
- 기타 MISSING ablation 추가

→ `tests/test_ablation_runner.py`의 count assertion을 **반드시 동반 업데이트**해야 한다.  
ablation 추가 commit과 count 업데이트 commit은 **동일 commit**이어야 한다.

### 6.3 ABL-022 standalone 등록 주의사항

현재 ABL-023 (uncertainty instead)은 `ablations.py`에 구현되어 있으나,  
ABL-022 (no falsification score gate)는 standalone으로 등록되어 있지 않다.  
Run 5에서 ABL-022를 추가할 때 count assertion 업데이트를 빠뜨리면 CI가 깨진다.

---

## Section 7. Handoff to Run 4

Run 4 (Phase 8/9)에서 구현할 테스트 우선순위:

### Priority 1 (반드시 Run 4에서)

1. **Group B**: h_exec trace 검증
   - `test_h_exec_trace_has_selected_hypothesis_id`: step log에서 실제 field 기록 확인
   - `test_h_exec_is_predicted_trace_not_oracle_label`: is_oracle_label=False 강제 확인
   - `test_missing_h_exec_blocks_persistence_metric`: h_exec 없을 때 F_t fallback 확인

2. **Group C**: LR falsification 기본 케이스
   - `test_lr_score_positive_when_alt_explains_evidence_better`: mock ell_t로 F_t > 0 검증
   - `test_lr_score_zero_or_negative_when_exec_explains_evidence_better`: F_t ≤ 0 검증
   - `test_all_equal_likelihoods_sets_degenerate_flag`: degenerate=True 검증
   - `test_empty_alternatives_blocks_falsification`: empty alt → F_t=0 검증
   - `test_bce_not_main_path`: BCE pathway 분리 확인

3. **Group G**: Anti-leakage 기본 케이스
   - `test_true_control_grammar_not_in_inference_input`
   - `test_true_regime_not_in_inference_input`
   - `test_counterfactual_table_not_in_inference_input`

### Priority 2 (Run 4/5에서)

4. **Group D**: Posterior update 기본 케이스
   - strong evidence → posterior shift 확인
   - no_effect → 작은 변화 확인

5. **Group F**: Rewrite 기본 케이스
   - `test_rewrite_uses_predicted_hypothesis_not_oracle`
   - `test_fallback_triggered_when_low_confidence`
   - `test_no_op_rewrite_not_always`

### Priority 3 (Run 5/6에서)

6. **Group C/E**: ABL-022/023/017 추가 후 비교 테스트
7. **Group E**: G_t gate 전체 검증 (BASE-015 / CATTS-equivalent 포함)
8. **Group F**: ABL-017 + BASE-026 비교 포함 확장

---

## Section 8. Phase 6 Verdict

**`TEST_PLAN_READY_FOR_EVAL_GATE`**

근거:
1. Test Group A~G 모두 정의 (Section 3)
2. 각 Group에 purpose / required future tests / connected claim / future run 명시
3. Test stub 파일 계약 확정 (Section 4): 11+9=20개 함수
4. `test_ablation_runner.py` count 경고 명시 (Section 6)
5. Run 4 구현 우선순위 명시 (Section 7)
6. C1/C3/C5 primary survival axis 우선 검증 경로 확정

**주의**: "TEST_PLAN_READY_FOR_EVAL_GATE"는 Phase 7 (Eval Gate Design)으로 진행 준비가 됐다는 의미다.  
"테스트 구현 완료"가 아니다. Run 3에서는 stub만 작성한다.

---

*생성일: 2026-05-16 / Run 3 / Phase 6 산출물*  
*근거: `docs/orchestration/lr_alignment/00_OPTION_B_PHASE_ROADMAP.md` Section 4 Phase 6, Section 5 Run 3*  
*수정 금지: `paper_context_ref/` 전체, 기존 `tests/` 파일 (test_ablation_runner.py 포함)*  
*C1~C6 ALIVE/DEAD 최종 판정 금지: Phase 11 Evidence Card 완성 이후에만 허용*
