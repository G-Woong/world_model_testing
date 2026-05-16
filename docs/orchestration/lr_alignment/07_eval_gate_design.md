---
file_id: EVAL-GATE-DESIGN-R3
title: Evaluation Gate Design — Phase 7 산출물
phase: 7 (Evaluation Gate Design)
run: 3
date: 2026-05-16
status: GATE_DESIGN_DOCUMENT
language: ko
type: gate_design_not_evaluation
---

# 07_eval_gate_design.md

**Phase**: 7 — Evaluation Gate Design  
**Run**: 3  
**Date**: 2026-05-16  
**Type**: 평가 gate 설계 문서. 평가 실행 아님. Run 3에서는 평가를 실행하지 않는다.

---

## Section 1. Purpose

### 1.1 이 문서의 역할

- Run 4 LR scorer 구현 + Run 5 baseline/ablation 확장 이후 P3 재학습/재평가를 정당화하기 위한 gate 계약 확정
- **success rate 단독 통과 금지**: mechanism metric 필수
- `P3_EVAL.passed`의 supersede 상황을 공식 반영하고 새 gate target 정의

### 1.2 이 문서에서 하지 않는 것

- P3 재학습 실행
- P3_EVAL 재실행
- baseline/ablation 코드 추가
- `paper_context_ref/` 수정
- 기존 `src/frcgw/` 파일 수정
- `outputs/phase_gates/` 수정/삭제
- 수치 threshold 임의 확정 (sensitivity analysis 대상)
- C1~C6 ALIVE/DEAD 확정

핵심 원칙: **약화가 아니라 정렬**. Gate 설계는 C1/C3/C5 primary survival axis를 우선 검증한다.

---

## Section 2. P3_EVAL Invalidity Reminder

`outputs/phase_gates/P3_EVAL.passed`는 **superseded evidence**다.

**`P3_EVAL.BLOCKED_planning_calls_zero.md`가 supersede한 근거**:

| Issue | 내용 | 출처 |
|---|---|---|
| `planning_calls=0` | 전 5 seed에서 planning gate가 한 번도 발동하지 않음 | P3_EVAL.BLOCKED_planning_calls_zero.md |
| `rollout_steps=0` | rollout 실행 자체가 없음 → C4 NOT_TESTED | feasibility_20260516_R1.md |
| FRCG-FULL = no_control_grammar (Δ=0) | mechanism delta가 0 → C1/C3 BLOCKED 또는 FAIL | ablation_results.json; war_room_R1_synthesis.md |
| h_exec trace 없음 | `selected_hypothesis_id` 미기록 → MET-PERSIST-001 불가 | reviewer2_20260516_R1.md Attack 2 |

**금지 사항**:
- `P3_EVAL.passed`를 논문 claim 근거로 사용 금지
- fake/manual metric을 위 issue를 덮는 방식으로 사용 금지
- 단순 재실행 (`scripts/03_eval_text_smoke.py` + `scripts/08_run_core_ablations.py`)은 LR scorer 구현 없이 금지

**새 gate target**: `outputs/phase_gates/P3_LR_EVAL.passed` (Phase 11에서만 생성 가능)

---

## Section 3. Gate Hierarchy (Gate 0~6)

7개 gate는 순서대로 통과해야 한다. 앞선 gate 실패 시 다음 gate 평가 금지.

---

### Gate 0 — Sanity / No Leakage

**목적**: 기본 안전성 확인. 어떤 metric도 이 gate 통과 없이는 신뢰 불가.

| 조건 | PASS 기준 | FAIL 기준 | BLOCKED 기준 |
|---|---|---|---|
| No hidden label leakage | `assert_agent_observation_safe()` 전 episode 통과 | 한 건이라도 `HiddenLabelLeakageError` 또는 `CounterfactualLeakageError` | leakage audit 미실행 |
| Forbidden field mirror sync | `test_forbidden_field_mirror_sync.py` green | 이 테스트 실패 | 테스트 파일 없음 |
| Deterministic replay | 동일 seed로 재실행 시 동일 metric | 재실행 결과 불일치 | replay 검증 미실행 |
| No fake metric | 모든 숫자가 실제 artifact에서 읽힘 | manual/placeholder metric 발견 | — |

**Required inputs**: eval run artifact (`outputs/runs/p3_lr_eval/`), leakage audit log  
**Related claims**: C1~C6 전체 (leakage 발생 시 모든 claim BLOCKED)

---

### Gate 1 — Mechanism Activation

**목적**: LR scorer와 h_exec trace가 실제로 동작함을 확인.  
P3_EVAL.BLOCKED의 root cause (planning_calls=0)가 해소됐는지 확인.

| 조건 | PASS 기준 | FAIL 기준 | BLOCKED 기준 |
|---|---|---|---|
| `planning_calls > 0` | ≥ 10% episodes에서 G_t=True | planning_calls=0 across all episodes | G_t 측정 코드 없음 |
| `F_t non-degenerate` | F_t variance > 0, not constant | F_t = 0 all episodes | F_t log field 없음 |
| `h_exec populated` | `selected_hypothesis_id` 기록됨 (모든 step) | `selected_hypothesis_id` null/empty | trace log 없음 |
| `H_alt non-empty` | alt_candidates 비어 있지 않은 episodes 존재 | 모든 episodes에서 A_t^H empty | proposer 미구현 |
| `G_t fires in falsifying episodes only` | high-F_t episode에서 G_t=True, low-F_t episode에서 G_t=False 비율 확인 | G_t fires regardless of F_t | gate_reason log 없음 |

**Hard Fail 조건**: `planning_calls == 0` → **FAIL Gate 1 + FAIL all downstream gates**  
**Required inputs**: `outputs/runs/p3_lr_eval/metrics.json` (planning_calls 필드)  
**Related claims**: C1 (h_exec), C3 (F_t), C6 (G_t)

---

### Gate 2 — C1 Persistence (Primary Survival Axis)

**목적**: wrong-grammar hypothesis가 falsifying evidence 이후에도 지속됨을 측정.  
FRCG-FULL이 BASE-001/005보다 높은 persistence 감지 능력을 보임.

| 조건 | PASS 기준 | FAIL 기준 | BLOCKED 기준 |
|---|---|---|---|
| MET-PERSIST-001 계산됨 | `wrong_control_grammar_persistence` 값이 artifact에 존재 | 값 없음 (h_exec trace 미구현) | h_exec trace not populated |
| MET-BELIEF-001 계산됨 | `belief_update_delay` 값이 artifact에 존재 | 값 없음 | — |
| MET-FAIL-002 계산됨 | `failure_repetition_rate` 값이 artifact에 존재 | 값 없음 | — |
| FRCG-FULL vs BASE-001 비교 | FRCG-FULL < BASE-001 (lower persistence = better recovery) | FRCG-FULL ≥ BASE-001 (no improvement) | BASE-001 미실행 |
| ABL-002 vs FRCG-FULL delta | FRCG-FULL < ABL-002 (no-control-grammar) | Δ ≈ 0 (mechanism not contributing) | ABL-002 미실행 |

**Hard Fail 조건**: h_exec trace 없음 → **BLOCKED (FAIL 아님)**, Gate 2 이후 C1 평가 불가  
**Required inputs**: MET-PERSIST-001/BELIEF-001/FAIL-002 from `outputs/runs/p3_lr_eval/`  
**Related claims**: C1 (primary survival axis)  
**Related baselines**: BASE-001, BASE-005

---

### Gate 3 — C3 LR Falsification (Primary Survival Axis)

**목적**: LR scorer가 BCE/uncertainty와 다른 mechanism을 실행함을 확인.  
ABL-022/023과의 비교에서 LR gate의 우위를 검증.

| 조건 | PASS 기준 | FAIL 기준 | BLOCKED 기준 |
|---|---|---|---|
| MET-FALS-001 (falsification_precision) 계산됨 | artifact에 값 존재 | 값 없음 | F_t log field 없음 |
| MET-FALS-002 (falsification_recall) 계산됨 | artifact에 값 존재 | 값 없음 | — |
| MET-CAL-001 (falsification calibration) 계산됨 | artifact에 값 존재 | 값 없음 | — |
| LR vs ABL-022 (no falsification score gate) | FRCG-FULL > ABL-022 on primary metric | Δ ≈ 0 (falsification gate 불필요) | ABL-022 미구현 |
| LR vs ABL-023 (uncertainty instead) | FRCG-FULL > ABL-023 (high-conf wrong grammar case) | Δ ≈ 0 (uncertainty gate와 동일) | ABL-023 미실행 |
| VerifierOnly behavior difference | FRCG-FULL ≠ BASE-005 (verifier-only) 동작 | 동일 동작 | BASE-005 미구현 |

**Hard Fail 조건**:
- `F_t constant or all-zero` → **FAIL Gate 3**
- LR == BCE (ABL-022 비교에서 Δ = 0) → C3 DEAD_COLLAPSED 조건  
- LR == uncertainty gate (ABL-023 비교에서 Δ = 0) → C3 핵심 distinction 붕괴

**Required inputs**: ABL-022/ABL-023 결과, MET-FALS-001/002/CAL-001  
**Related claims**: C3 (primary survival axis)  
**Related baselines**: BASE-005, BASE-006, BASE-012

---

### Gate 4 — C5 Rewrite (Primary Survival Axis)

**목적**: grammar-conditioned rewrite가 generic correction과 다름을 확인.  
ABL-017/035와 비교, WAC-style (BASE-026) 대비 distinction.

| 조건 | PASS 기준 | FAIL 기준 | BLOCKED 기준 |
|---|---|---|---|
| MET-REWRITE-001 (rewrite_success_rate) 계산됨 | artifact에 값 존재 | 값 없음 | GrammarConditionedRewrite 미구현 |
| MET-SWITCH-001 (action switch delay) 계산됨 | artifact에 값 존재 | 값 없음 | — |
| FRCG-FULL vs ABL-017 (no L_intent_action_mapping) | FRCG-FULL > ABL-017 (training-level grammar conditioning 효과) | Δ ≈ 0 (grammar conditioning 학습 없음) | ABL-017 미구현 |
| FRCG-FULL vs ABL-035 (no-action-rewrite) | FRCG-FULL > ABL-035 (rewrite 자체의 효과) | Δ ≈ 0 (rewrite 불필요) | ABL-035 미실행 |
| WAC-style distinction (BASE-026) | FRCG-FULL ≠ BASE-026 (grammar conditioning ≠ generic correction) | Δ ≈ 0 (구분 불가) | BASE-026 미구현 |

**Hard Fail 조건**: rewrite ablation (ABL-035) 비교에서 Δ = 0 → C5 DEAD_COLLAPSED 조건  
**Required inputs**: MET-REWRITE-001/SWITCH-001, ABL-017/035 결과, BASE-026 결과  
**Related claims**: C5 (primary survival axis)  
**Related baselines**: BASE-003, BASE-004, BASE-026

---

### Gate 5 — Supporting C4/C6

**목적**: alternative grammar rollout (C4)과 compute gate (C6) 지원 claim 검증.

#### Gate 5a — C4 Alternative Grammar Rollout

| 조건 | PASS 기준 | FAIL 기준 | BLOCKED 기준 |
|---|---|---|---|
| MET-WM-001 (rollout_fidelity) 계산됨 | artifact에 값 존재 | 값 없음 | rollout_steps=0 |
| MET-ALT-001 (alternative_adoption_rate) 계산됨 | artifact에 값 존재 | 값 없음 | — |
| `rollout_steps > 0` | 일부 episodes에서 rollout 실행됨 | rollout_steps=0 모든 episodes | rollout 미구현 |
| BASE-028 (WebWorld-style) 대비 | grammar-conditioned rollout fidelity > grammar-agnostic | Δ ≈ 0 | BASE-028 미구현 |

**Hard Fail 조건**: rollout_steps=0 → C4 BLOCKED (NOT_TESTED)

#### Gate 5b — C6 Decision-Relevant Compute Gate

| 조건 | PASS 기준 | FAIL 기준 | BLOCKED 기준 |
|---|---|---|---|
| MET-COMP-003 (compute_normalized_return) 계산됨 | artifact에 값 존재 | 값 없음 | planning_calls=0 |
| `false_planning_call_rate` 계산됨 | artifact에 값 존재 | 값 없음 | G_t log 없음 |
| BASE-015 (ComputeMatchedRandom) 대비 | FRCG-FULL > BASE-015 on compute-normalized return | Δ ≈ 0 | BASE-015 미구현 |
| CATTS-equivalent 대비 | high-conf wrong grammar: G_t fires, CATTS-style uncertainty gate ≠ G_t | CATTS-style과 동일 동작 | CATTS-equivalent baseline 미구현 |
| uncertainty gate와 구분 | high-conf wrong grammar episode에서 G_t=True, uncertainty gate=False 케이스 존재 | 케이스 없음 (둘이 동일) | ABL-023 미실행 |

**Hard Fail 조건**: `planning_calls == 0` → C6 BLOCKED (G_t never fires)  
**Related claims**: C6 (supporting efficiency claim)  
**Related baselines**: BASE-010, BASE-012, BASE-015, CATTS-equivalent, VLAA-loop-heuristic

---

### Gate 6 — Claim Survivability Update

**목적**: Evidence Card 갱신 artifact가 존재함을 확인. ALIVE/DEAD 최종 판정은 Phase 12.

| 조건 | PASS 기준 | FAIL 기준 | BLOCKED 기준 |
|---|---|---|---|
| Evidence Card 갱신 artifact path 존재 | Gate 2~5 결과가 C1~C6 Evidence Card `experiment_evidence` 필드에 기재됨 | artifact path 없음 | Gate 0~5 중 하나라도 BLOCKED |
| 갱신된 `03_concept_survivability_ledger.md` 존재 | Phase 11에서 update됨 | 미업데이트 | — |
| ALIVE/DEAD 최종 판정 = Phase 12만 허용 | Phase 12에서만 final verdict | Phase 11 이전에 final verdict 선언 | — |

**Related claims**: C1~C6 전체  
**최종 판정 출처**: `docs/orchestration/lr_alignment/12_survivability_decision_report.md` (Phase 12)

---

## Section 4. CC-P3-G1/G3/G4 Redefinition

기존 CC-P3-G1/G3/G4를 새 gate target에 맞게 재정의한다.

---

### CC-P3-G1-LR — Mechanism Activation Gate

**역할**: LR scorer와 h_exec trace가 text-only smoke에서 동작함.

| 항목 | 내용 |
|---|---|
| Required inputs | `outputs/runs/p3_lr_smoke/metrics.json` (planning_calls, F_t stats, h_exec populated 필드) |
| Required metrics | planning_calls, F_t (mean/std/degenerate_rate), `selected_hypothesis_id` 기록 여부 |
| PASS | planning_calls > 0 (≥ 10% episodes) ∧ F_t variance > 0 ∧ h_exec populated |
| FAIL | planning_calls = 0 또는 F_t constant |
| BLOCKED | G_t 측정 코드 없음 또는 h_exec trace 코드 없음 |
| Related claims | C1 (h_exec trace), C3 (F_t non-degenerate), C6 (G_t fires) |

---

### CC-P3-G3-LR — Persistence/Recovery Delta Gate

**역할**: LR scorer가 wrong-grammar hypothesis 감지에서 baselines 대비 우위를 보임.

| 항목 | 내용 |
|---|---|
| Required inputs | `outputs/runs/p3_lr_eval/ablation_results.json` (FRCG-FULL vs ABL-002/BASE-001/005) |
| Required metrics | MET-PERSIST-001, MET-FAIL-002, MET-FALS-001/002 |
| PASS | FRCG-FULL < BASE-001 on MET-PERSIST-001 ∧ FRCG-FULL < ABL-002 on MET-PERSIST-001 |
| FAIL | FRCG-FULL ≥ BASE-001 (no persistence reduction) |
| BLOCKED | h_exec trace 없음 (MET-PERSIST-001 계산 불가) |
| Related claims | C1 (primary), C3 (supporting) |

---

### CC-P3-G4-LR — Ablation/Baseline Distinction Gate

**역할**: LR scorer가 ablation/baseline 경쟁자와 mechanism 수준에서 구별됨.

| 항목 | 내용 |
|---|---|
| Required inputs | `outputs/runs/p3_lr_eval/ablation_results.json` (FRCG-FULL vs ABL-022/023/017/035 vs BASE-026/027/028) |
| Required metrics | MET-FALS-001/002/CAL-001, MET-REWRITE-001, MET-COMP-003 |
| PASS | FRCG-FULL > ABL-022 ∧ FRCG-FULL > ABL-023 (high-conf wrong grammar) ∧ FRCG-FULL > BASE-026 |
| FAIL | ABL-023 ≈ FRCG-FULL (uncertainty gate와 동일) 또는 ABL-022 ≈ FRCG-FULL (falsification gate 불필요) |
| BLOCKED | ABL-022 미구현 또는 BASE-026 미구현 |
| Related claims | C3 (primary), C5 (primary), C6 (supporting) |

---

## Section 5. Required Metrics (14개)

각 metric은 artifact에서 실제로 계산된 값이어야 한다. 추정치/수동 입력 금지.

| Metric ID | 계산 내용 | Connected Claim | Required Log Fields | Missing이면 BLOCKED 되는 claim |
|---|---|---|---|---|
| MET-PERSIST-001 | `wrong_control_grammar_persistence` — wrong hypothesis 유지 기간 | C1 (primary) | `selected_hypothesis_id`, `true_wrong_hypothesis` (audit only) | C1 |
| MET-BELIEF-001 | `belief_update_delay` — hypothesis 전환까지 걸리는 step 수 | C1 | `posterior_shift`, `switch_recommended` | C1 |
| MET-FAIL-002 | `failure_repetition_rate` — 동일 실패 반복 비율 | C1 | `failure_reason` | C1 |
| MET-FALS-001 | `falsification_precision` — F_t > τ일 때 실제 wrong hypothesis 비율 | C3 (primary) | `F_t`, `true_wrong_hypothesis` (audit) | C3 |
| MET-FALS-002 | `falsification_recall` — actual wrong hypothesis에서 F_t > τ 비율 | C3 (primary) | `F_t`, `true_wrong_hypothesis` (audit) | C3 |
| MET-CAL-001 | `falsification_calibration` — F_t calibration (ECE 등) | C3 | `F_t`, `calibration_features` | C3 |
| MET-REWRITE-001 | `rewrite_success_rate` — rewrite 후 task 성공 비율 | C5 (primary) | `rewrite_triggered`, `rewrite_confidence`, `fallback_used` | C5 |
| MET-SWITCH-001 | `action_switch_delay` — wrong hypothesis 감지 후 rewrite까지 step 수 | C5 | `rewrite_triggered`, `F_t` | C5 |
| MET-WM-001 | `rollout_fidelity` — 예측 rollout vs 실제 outcome 일치도 | C4 (supporting) | `rollout_steps`, `predicted_rollout` | C4 |
| MET-ALT-001 | `alternative_adoption_rate` — G_t=1 후 alternative hypothesis 채택 비율 | C4 (supporting) | `adopted_hypothesis_id`, `alternative_hypothesis_ids` | C4 |
| MET-COMP-003 | `compute_normalized_return` — compute 단위당 성능 | C6 (supporting) | `planning_calls`, `rollout_steps`, `episode_reward` | C6 |
| `false_planning_call_rate` | G_t=True이지만 hypothesis switch 불필요한 비율 | C6 | `gate_reason`, `switch_recommended` | C6 |
| `planning_calls` | episode 내 G_t=True 총 횟수 | C1/C3/C6 | `gate_reason` | 전체 Gate 1 FAIL |
| `rollout_steps` | episode 내 rollout 실행 step 수 | C4 | `rollout_steps` | C4 BLOCKED |

---

## Section 6. Required Baseline/Ablation Comparisons

모든 비교는 artifact path가 존재해야 한다. 비교 없이는 gate PASS 불가.

### 6.1 Required Baselines

| Baseline ID | 연결 claim | 필요 이유 | 없으면 BLOCKED |
|---|---|---|---|
| BASE-001 (FrozenBaseLLM) | C1 | persistence 비교 기준 | Gate 2 (C1) BLOCKED |
| BASE-005 (VerifierOnlyAgent) | C3 | verifier-only vs LR mechanism 구분 | Gate 3 (C3) BLOCKED |
| BASE-006 (VerifierHeuristicRecovery) | C3 | heuristic recovery vs LR 구분 | Gate 3 (C3) 부분 BLOCKED |
| BASE-012 (UncertaintyGatedAgent) | C6 | uncertainty gate vs G_t 4-way 구분 | Gate 5b (C6) BLOCKED |
| BASE-015 (ComputeMatchedRandom) | C6 | compute-matched baseline | Gate 5b (C6) BLOCKED |
| BASE-026 (WAC-style) | C5 | grammar-conditioned rewrite vs WAC 구분 | Gate 4 (C5) BLOCKED |
| BASE-027 (CUWM-style) | C3/C4 | CUWM (THREAT-06) 방어 | Gate 3/5a 부분 BLOCKED |
| BASE-028 (WebWorld-style) | C4 | WebWorld (THREAT-04) 방어. grammar-agnostic rollout 비교 | Gate 5a (C4) BLOCKED |
| CATTS-equivalent | C6 | CATTS (THREAT-01) 방어. uncertainty compute gate 비교 | Gate 5b (C6) BLOCKED |
| VLAA-loop-heuristic | C1/C3 | VLAA-GUI (THREAT-02) 방어 | Gate 2/3 부분 BLOCKED |

### 6.2 Required Ablations

| Ablation ID | 연결 claim | 필요 이유 | 없으면 BLOCKED |
|---|---|---|---|
| ABL-001 (no_regime) | C2 | regime 요인 독립 기여 검증 | C2 검증 BLOCKED |
| ABL-002 (no-control-grammar) | C1 | FRCG-FULL vs no-grammar Δ | Gate 2 (C1) BLOCKED |
| ABL-016 (no L_falsification) | C3 | falsification loss 자체의 기여 | Gate 3 (C3) 참조 |
| ABL-017 (no L_intent_action_mapping) | C5 | grammar conditioning training 기여 | Gate 4 (C5) BLOCKED |
| ABL-022 (no falsification score gate) | C3/C1 | F_t gate 없을 때 성능 | Gate 3 (C3) BLOCKED |
| ABL-023 (uncertainty instead of falsification) | C3/C6 | uncertainty gate vs LR gate 구분 | Gate 3/5b BLOCKED |
| ABL-024 (no-alternative-hypothesis) | C4 | A_t^H 없을 때 성능 | Gate 5a (C4) 참조 |
| ABL-026 (no-rollout) | C4 | rollout 자체의 기여 | Gate 5a (C4) 참조 |
| ABL-033 (no decision-relevance gate) | C6 | G_t gate 없을 때 성능 | Gate 5b (C6) 참조 |
| ABL-034 (always-plan) | C6 | always-plan vs selective-plan | Gate 5b (C6) 참조 |
| ABL-035 (no-action-rewrite) | C5 | rewrite 자체의 기여 | Gate 4 (C5) BLOCKED |
| ABL-036 (no_counterfactual_target) | C4 | counterfactual target 기여 | Gate 5a (C4) 참조 |
| ABL-040 (leakage probe) | all | posterior spurious update 감시 | Gate 0 참조 |

---

## Section 7. Threshold Policy

### 7.1 Run 3에서 수치 threshold 임의 확정 금지

Run 3에서는 τ_f, τ_v, τ_a, τ_r 등 수치 threshold를 임의로 확정하지 않는다.  
sensitivity analysis (Run 6)에서 실험적으로 calibration해야 한다.

### 7.2 Hard Fail 조건 (threshold 무관, 절대 기준)

다음 조건은 threshold에 무관하게 즉각 FAIL/BLOCKED 판정:

| 조건 | 판정 | 영향 범위 |
|---|---|---|
| `planning_calls == 0` | **FAIL** Gate 1 + FAIL all downstream | C1/C3/C6 모두 |
| `h_exec missing` (selected_hypothesis_id null/empty) | **BLOCKED** Gate 2 (C1/C3) | C1, C3 |
| `F_t constant or all-zero` | **FAIL** Gate 3 (C3) | C3 |
| `hidden label leakage` 발생 | **FAIL** Gate 0 + FAIL all | C1~C6 모두 |
| `fake/manual metric` 발견 | **FAIL** Gate 0 + FAIL all | C1~C6 모두 |
| `required baseline 없음` | **BLOCKED** (PASS 아님) | 해당 Gate |

### 7.3 Sensitivity Analysis 정책 (Run 6에서 확정)

- τ_f: {0.1, 0.3, 0.5, 1.0, 2.0} 후보 grid에서 Gate 1 통과 조건으로 calibration
- τ_v: ΔV_t 분포 기반 calibration
- τ_a: action switch probability 분포 기반 calibration
- threshold sensitivity report = `outputs/runs/p3_lr_eval/threshold_sensitivity.json` (Run 6)

---

## Section 8. Failure Interpretation Protocol

각 failure case에 대한 해석 프로토콜:

| Failure | 해석 | 우선 조치 |
|---|---|---|
| `planning_calls=0` | F_t 항상 < τ_f. 모델 학습 부족 또는 LR scorer 미동작. P3_EVAL.BLOCKED 재현. | 학습 step 연장 + F_t 분포 진단 |
| `h_exec missing` | `selected_hypothesis_id` log populate 코드 누락. C1 mechanism 전혀 미동작. | lr_scorer.py 구현 재확인. step log populate 코드 추가 |
| `LR == BCE` (ABL-022 Δ=0) | F_t LR gate가 BCE binary flag와 동일 동작. C3 핵심 distinction 붕괴. Option B의 근거 약화. | BCE vs LR 계산 경로 분리 검증. 학습 signal 재검토 |
| `LR == uncertainty gate` (ABL-023 Δ=0) | LR falsification과 uncertainty threshold가 동일 에피소드에서 발동. C3/C6 핵심 구분 붕괴. | high-confidence wrong grammar episode 구성 재검토. τ_f vs uncertainty threshold 비교 |
| `rewrite ablation no delta` (ABL-035 Δ=0) | Rewrite 자체가 성능에 기여하지 않음. C5 DEAD_COLLAPSED 조건. | GrammarConditionedRewrite 구현 재검토. grammar conditioning 학습 signal 확인 |
| `rollout fidelity no delta` (BASE-028 Δ=0) | grammar-conditioned rollout이 grammar-agnostic와 동일. C4 DEAD_COLLAPSED 조건. | ΔV_t 계산 재검토. alternative hypothesis 품질 확인 |
| `compute gate no advantage` (BASE-015 Δ=0) | compute-matched random reallocation과 성능 동일. C6 DEAD_COLLAPSED 조건. | gate threshold calibration 재검토. planning compute 비율 진단 |
| `hidden label leakage` | FORBIDDEN_AGENT_FIELDS가 inference input에 포함. 즉각 중단. | leakage audit 재실행. dataset shard 무효화. |
| `C2 latent probe fails` (MI ≈ 0) | regime/grammar separation이 이론적으로 불가. Locatello impossibility 발현. | ABL-001 + crossed split 결과와 함께 Phase 12에서 판정. primary claim 아니므로 즉각 종료 아님 |
| `success rate improves but mechanism metrics do not` | 성능 향상이 mechanism이 아닌 다른 요인 (학습 signal, data bias 등)에 기인. | mechanism metric 진단 우선. success rate만으로 claim 주장 금지. |

---

## Section 9. Handoff to Run 4/5/6

### Run 4 (Phase 8/9) — LR scorer 구현 + GUI env 연동

Run 4에서 해야 할 일:
1. `src/frcgw/falsification/lr_scorer.py` 구현 (실제 EvidenceLikelihood + LikelihoodRatioFalsificationScorer)
2. `selected_hypothesis_id` step log populate (h_exec trace 활성화)
3. text-only smoke: planning_calls > 0 달성 (`CC-P3-G1-LR` PASS 조건)
4. Group A/B/C/G 테스트 실제 assertion 구현

### Run 5 (Phase 10) — Baseline/Ablation 확장

Run 5에서 해야 할 일:
1. BASE-026 (WAC-style), BASE-027 (CUWM-style), BASE-028 (WebWorld-style) 구현
2. ABL-017 (no_L_intent_action_mapping), ABL-022 (standalone), ABL-036 추가
3. `tests/test_ablation_runner.py` count **반드시 동반 업데이트**
4. CATTS-equivalent baseline 구현
5. Group C/E/F 테스트 ablation 비교 assertion 추가

### Run 6 (Phase 11/12) — Full eval + Evidence Card 갱신

Run 6에서 해야 할 일:
1. Full eval 실행: Gate 0~6 순서대로 평가
2. leakage audit 실행: `assert_agent_observation_safe()` 전 episode
3. 14개 metric 모두 계산
4. C1~C6 Evidence Card `experiment_evidence`, `counter_evidence` 갱신
5. `outputs/phase_gates/P3_LR_EVAL.passed` sentinel 생성 (Gate 0~6 모두 PASS 시)
6. `12_survivability_decision_report.md` 작성 (C1~C6 final verdict)

---

## Section 10. Phase 7 Verdict

**`EVAL_GATE_READY_FOR_RUN4_IMPLEMENTATION`**

근거:
1. Gate 0~6 hierarchy 완성 (Section 3)
2. CC-P3-G1/G3/G4 재정의 완성 (Section 4)
3. 14개 Required Metrics 명세 완성 (Section 5)
4. 10개 Required Baselines + 13개 Required Ablations 명세 완성 (Section 6)
5. Hard fail 조건 6개 명시 (Section 7)
6. Failure interpretation protocol 10개 케이스 (Section 8)
7. Run 4/5/6 handoff 명시 (Section 9)

**주의**: "EVAL_GATE_READY_FOR_RUN4_IMPLEMENTATION"은 Run 4 구현으로 진행 준비가 됐다는 의미다.  
**"P3 재학습 준비 완료"라고 쓰지 않는다.**  
Run 4 구현 + Run 5 baseline/ablation 확장 이후에만 P3 재학습 가능.

---

*생성일: 2026-05-16 / Run 3 / Phase 7 산출물*  
*근거: `docs/orchestration/lr_alignment/00_OPTION_B_PHASE_ROADMAP.md` Section 4 Phase 7, Section 5 Run 3*  
*수정 금지: `paper_context_ref/` 전체, `outputs/phase_gates/` 전체*  
*C1~C6 ALIVE/DEAD 최종 판정 금지: Phase 11 Evidence Card 완성 이후에만 허용*  
*수치 threshold 임의 확정 금지: Run 6 sensitivity analysis에서 calibration*
