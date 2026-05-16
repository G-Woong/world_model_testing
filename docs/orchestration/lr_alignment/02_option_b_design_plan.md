---
file_id: OPTION-B-DESIGN-PLAN
title: Option B LR Design Plan — Phase 2 산출물
phase: 2 (Option B LR Design Plan)
run: 1
date: 2026-05-16
status: DESIGN_DOCUMENT
language: ko
type: design_not_implementation
---

# 02_option_b_design_plan.md

**Phase**: 2 — Option B LR Design Plan  
**Run**: 1  
**Date**: 2026-05-16  
**Type**: 설계 문서. 구현 파일이 아님. Run 1에서는 구현하지 않는다.

---

## Section 1. Purpose

이 파일은 **구현 파일이 아니다**.

역할:
- `LikelihoodRatioFalsificationScorer`의 이론/설계 계약을 full detail로 작성
- Phase 5 (LR Implementation Contract)와 Phase 8 (Text-only LR Smoke Implementation)의 선행 설계
- paper_context_ref 수정 없이, 현재 docs 기반으로 Option B 설계 정렬

이 파일에서 하지 않는 것:
- 코드 작성
- 테스트 작성
- `paper_context_ref/` 수정
- `LikelihoodRatioFalsificationScorer` 구현 선언
- C1~C6 ALIVE/DEAD 판정

---

## Section 2. Component Overview

Option B main path는 5개 component로 구성된다.

| 번호 | Component | 역할 | Inference-Safe? |
|---|---|---|---|
| 1 | `EvidenceLikelihood` (`ell_t`) | 각 hypothesis의 evidence 설명력 계산 | YES — observed public evidence만 사용 |
| 2 | `LikelihoodRatioFalsificationScorer` (`F_t`) | alternative vs executed hypothesis의 LR로 falsification score 계산 | YES — predicted trace only |
| 3 | `PosteriorUpdater` (`b_t`) | regime/grammar posterior를 evidence history로 학습 근사 | YES — observed history만 사용 |
| 4 | `DecisionRelevanceGate` (`G_t`) | 4-way conjunction gate: falsification + value gain + action switch + cost-benefit | YES — predicted values only |
| 5 | `GrammarConditionedRewrite` (`Rewrite`) | 선택된 hypothesis 아래 intent/action 재작성 | YES — executed action만 output |

5개 component의 pipeline:
```
e_t (observed) → EvidenceLikelihood
                → LikelihoodRatioFalsificationScorer (F_t)
                → PosteriorUpdater (b_t) ←→ History (H_t)
                → DecisionRelevanceGate (G_t)
                → [G_t=1] GrammarConditionedRewrite (a_exec)
```

---

## Section 3. Symbol Table

| Symbol | Meaning | Inference-safe? | Required Log Field | Connected Claim |
|---|---|---|---|---|
| `h_exec` | 직전 action 생성에 실제로 사용된 hypothesis (predicted trace, NOT oracle label) | YES (predicted only) | `selected_hypothesis_id` | C1/C3 |
| `H_alt` / `A_t^H` | alternative regime/control-grammar hypothesis set (NOT alternative action set) | YES (predicted only) | `alternative_hypothesis_ids` | C3/C4 |
| `e_t` | action-effect evidence: observed effect type + DOM diff + accessibility diff + visual diff + precondition status + no-effect flag + delayed-effect flag + noisy-observation flag + progress delta + failure reason | YES (public observed) | `evidence_summary` | C3 |
| `ell_t(h)` | `log p_theta(e_t \| H_{t-1}, a_{t-1}, h)` — hypothesis h의 evidence 설명력 | YES (predicted) | `loglik_exec`, `loglik_alt_best` | C3 |
| `F_t` | `max_{h_alt ∈ A_t^H} [ell_t(h_alt) − ell_t(h_exec)]` — LR falsification score | YES (predicted) | `F_t` | C3/C6 |
| `b_t(z^r,z^g)` | `q_phi(z^r, z^g \| H_t)` — learned approximation (NOT exact Bayesian posterior) | YES (predicted) | `posterior_before`, `posterior_after` | C2/C3 |
| `ΔV_t` | `max_{h_alt,a} V(a,h_alt) − max_a V(a,h_exec)` — alternative hypothesis value gain | YES (predicted) | `decision_relevance_delta` | C4/C6 |
| `G_t` | `I[F_t > τ_f ∧ ΔV_t > τ_v ∧ P_switch > τ_a ∧ ΔV_t − C_plan > 0]` — decision gate | YES (predicted) | `gate_reason` | C6 |
| `a_exec` | `Rewrite(intent=i_t, base_action=a_base, selected_hypothesis=h*)` — 최종 실행 action | YES (executed only) | `rewrite_triggered`, `rewrite_confidence` | C5 |

**주의 사항**:
- `h_exec`는 predicted trace이지 oracle label이 아님. `true_control_grammar`, `true_regime` (FORBIDDEN_AGENT_FIELDS)과 혼동 금지
- `A_t^H`는 alternative **hypothesis** set이지 alternative **action** set이 아님
- `b_t(z^r,z^g)`는 exact Bayesian posterior가 아님. learned approximation

---

## Section 4. Input/Output Contract

각 component의 입력/출력/실패 모드를 명세한다. 구현 상세는 Phase 5에서 확정된다.

### 4.1 EvidenceLikelihood

**역할**: `ell_t(h) = log p_theta(e_t | H_{t-1}, a_{t-1}, h)`

**Inputs**:
- `e_t`: action-effect evidence (public observed fields only)
  - effect_type, dom_diff_summary, accessibility_diff, visual_diff_score, precondition_status
  - no_effect_flag, delayed_effect_flag, noisy_observation_flag, progress_delta, failure_reason
- `H_{t-1}`: history encoder output (episode step 0 ~ t-1의 인코딩)
- `a_{t-1}`: 직전 action representation
- `h`: 평가 대상 hypothesis (h_exec 또는 h_alt ∈ A_t^H)

**Outputs**:
- `loglik: float` — log p_theta(e_t | H_{t-1}, a_{t-1}, h)

**Failure Modes**:
- `e_t`에 FORBIDDEN_AGENT_FIELDS 포함 시: LEAKAGE ERROR — 즉시 중단
- `h`가 `true_control_grammar` 등 oracle label일 때: FORBIDDEN — 구현 금지
- log 0 또는 -inf: numerical underflow → log-sum-exp 사용 권고

**Inference-safety**: `e_t`는 public observed evidence만. hidden labels (true_wrong_hypothesis, oracle_regime_action 등) 포함 금지.

---

### 4.2 LikelihoodRatioFalsificationScorer

**역할**: `F_t = max_{h_alt ∈ A_t^H} [ell_t(h_alt) − ell_t(h_exec)]`

**Inputs**:
- `ell_t(h_exec)`: EvidenceLikelihood output for h_exec
- `{ell_t(h_alt) for h_alt ∈ A_t^H}`: EvidenceLikelihood outputs for all alternatives
- `A_t^H`: alternative hypothesis set (proposer output)

**Outputs**:
- `F_t: float` — LR falsification score
- `best_alt: h` — argmax alternative hypothesis

**Failure Modes**:
- `A_t^H` empty: F_t = 0 (no alternative → no falsification). 로그 기록 필수
- `h_exec` missing: F_t = UNDEFINED → fallback to F_t = 0 + 경고 로그
- 모든 ell_t가 동일 (all equal): F_t = 0 → 로그 기록
- F_t 항상 0: degenerate case (Section 9 참조)
- F_t 항상 매우 높음: degenerate case (Section 9 참조)

**주의**: BCE version (`BCEBinaryFalsificationScorer`)은 이 component를 대체하지 않는다. BCE는 main falsification method가 아니다. ABL-022/023 ablation path에서만 사용된다.

---

### 4.3 PosteriorUpdater

**역할**: `b_t(z^r, z^g) = q_phi(z^r, z^g | H_t)`

**Inputs**:
- `H_t`: history up to step t (action-effect evidence sequence)
- `phi`: learned parameters (history encoder + posterior head)

**Outputs**:
- `b_t`: distribution over (regime, grammar) latent pairs
- `z^r_t`: regime latent sample/mode
- `z^g_t`: grammar latent sample/mode

**Failure Modes**:
- posterior가 단일 (z^r, z^g)에 collapse: KNOWN RISK (Locatello impossibility 관련). ABL-001 + crossed split episodes로 진단
- posterior가 evidence와 무관하게 변하지 않음: degenerate case (Section 9 참조)
- hidden label이 `H_t`에 포함: LEAKAGE ERROR → 즉시 중단

**Inference-safety**: `H_t`에는 공개 observation만 포함. `true_regime`, `true_control_grammar` 입력 금지.

---

### 4.4 DecisionRelevanceGate

**역할**:
```
ΔV_t = max_{h_alt∈A_t^H, a∈A} V(a,h_alt) − max_{a∈A} V(a,h_exec)

G_t = I[
    F_t > τ_f
    ∧ ΔV_t > τ_v
    ∧ P(action_switch | A_t^H, H_t) > τ_a
    ∧ ΔV_t − C_plan > 0
]
```

**Inputs**:
- `F_t`: LikelihoodRatioFalsificationScorer output
- `ΔV_t`: value gain from best alternative hypothesis (WM-based rollout)
- `P_switch`: action switch probability under alternative hypotheses
- `C_plan`: planning compute cost (β * rollout_steps)
- `τ_f, τ_v, τ_a`: threshold parameters (Phase 7에서 calibration 명세)

**Outputs**:
- `G_t: bool` — planning compute 사용 여부
- `gate_reason: str` — 어떤 조건이 위반되었는지 기록 (로깅 필수)
- `adopted_hypothesis_id: str` — G_t=1일 때 선택된 hypothesis

**Failure Modes**:
- G_t 항상 0 (never fires): τ_f, τ_v, τ_a가 너무 높거나 F_t가 너무 낮음 → degenerate
- G_t 항상 1 (always fires): threshold가 너무 낮거나 F_t가 항상 높음 → degenerate
- `ΔV_t − C_plan < 0` 항상 성립: planning 비용이 항상 이득을 초과 → threshold calibration 필요

**주의**: G_t는 `uncertainty > threshold` 단일 조건이 아님. 4개 조건의 conjunction.

---

### 4.5 GrammarConditionedRewrite

**역할**:
```
h* = argmax_{h ∈ {h_exec} ∪ A_t^H} max_a V(a,h)
a* = argmax_a V(a, h*)
a_exec = Rewrite(intent=i_t, base_action=a_base, selected_hypothesis=h*)
```

**Inputs**:
- `intent i_t`: high-level task intent (public)
- `base_action a_base`: 현재 selected action before rewrite
- `selected_hypothesis h*`: G_t gate 이후 채택된 hypothesis

**Outputs**:
- `a_exec`: 최종 실행 action (rewritten under h*)
- `rewrite_confidence: float`
- `fallback_used: bool`

**Failure Modes**:
- `rewrite_confidence < τ_r`: fallback rule 발동 → `base_action` 사용 또는 verifier-only safe fallback
- `precondition_check(a_exec) == INVALID`: fallback 발동
- Rewrite가 항상 no-op: C5 mechanism missing → ABL-035 상태와 동일
- Rewrite가 항상 base_action을 override: 과적합 위험

**Inference-safety**: `selected_hypothesis h*`는 predicted trace. `oracle_grammar_action`, `oracle_best_action` 입력 금지.

---

## Section 5. Main Path vs Ablation Path

### Main Path (Option B)

**`LikelihoodRatioFalsificationScorer`가 main falsification method다.**

Pipeline:
```
e_t → ell_t(h_exec), {ell_t(h_alt)}
→ F_t = max_{h_alt} [ell_t(h_alt) - ell_t(h_exec)]
→ G_t = I[F_t > τ_f ∧ ΔV_t > τ_v ∧ P_switch > τ_a ∧ ΔV_t - C_plan > 0]
→ [G_t=1] h* selection → Rewrite(intent, base, h*)
```

### Auxiliary / Ablation Path

아래 components는 main path를 대체하지 않는다. ablation 또는 baseline 비교 역할만 담당한다.

| Component | 역할 | Baseline/Ablation ID |
|---|---|---|
| `BCEBinaryFalsificationScorer` | binary classification 기반 falsification (L-MAIN-005 현 구현). BCE는 main falsification method가 아니다. | ABL-022 (no falsification score gate), ABL-023 (uncertainty instead of falsification) |
| `FailedActionFlagVerifier` | action failure binary flag만으로 falsification 판단. | BASE-005/006 (verifier-only) |
| `UncertaintyGate` | 모델 불확실도 > threshold 조건만으로 planning 트리거 | BASE-012 (UncertaintyGatedAgent) |
| `VerifierOnlyRecovery` | verification failure → corrective action (no posterior update) | BASE-005, BASE-006 |

**필수 명시 문구**:
- "BCE는 main falsification method가 아니다."
- "Run 1에서는 구현하지 않는다."
- "hidden labels are not inference inputs."
- "h_exec is predicted trace, not oracle label."

---

## Section 6. Claim Mapping

C1~C6 각각에 대해 필요 component, metric, ablation, 현재 Run 1 status를 매핑한다.

| Claim | Required Component | Required Later Metric | Required Later Ablation | Current Run 1 Status |
|---|---|---|---|---|
| **C1** (wrong-grammar persistence) | `h_exec` trace + persistence trace (`selected_hypothesis_id` 로그) | MET-PERSIST-001 (wrong_control_grammar_persistence) | ABL-002 (no-control-grammar), ABL-022 (no falsification score gate) | BLOCKED — h_exec trace 미구현, planning_calls=0 |
| **C2** (regime/grammar separation) | `b_t` factorization — `q_phi(z^r, z^g \| H_t)` + crossed split episodes | MET-LATENT-001 (latent_factorization_probe) | ABL-001 (no_regime), ABL-003 (merged regime-grammar), ABL-006 (collapsed latent) | BLOCKED — ABL-001 미구현, crossed split 부재, Locatello impossibility 미해소 |
| **C3** (falsification mechanism) | `ell_t` (EvidenceLikelihood) + `F_t` (LikelihoodRatioFalsificationScorer) | MET-FALS-001 (falsification_precision), MET-FALS-002 (falsification_recall), MET-CAL-001 | ABL-016 (no L_falsification), ABL-022 (no falsification score gate), ABL-023 (uncertainty instead) | DESIGNING — LR 설계 진행 중 (이 문서) |
| **C4** (alternative grammar rollout) | `A_t^H` (alternative hypothesis set) + `ΔV_t` (rollout-based value gain) | MET-WM-001 (rollout_fidelity), MET-ALT-001 (alternative_adoption_rate) | ABL-024 (no-alternative-hypothesis), ABL-026 (no-rollout), ABL-036 (no_counterfactual_target) | BLOCKED — MET-WM-001/ALT-001 미구현, rollout_steps=0 |
| **C5** (grammar-conditioned rewrite) | `GrammarConditionedRewrite` — `Rewrite(intent, base, h*)` | MET-REWRITE-001 (rewrite_success_rate) | ABL-017 (no_L_intent_action_mapping), ABL-035 (no-action-rewrite) | CONDITIONAL — 수식 명확, ABL-017 미구현 |
| **C6** (decision-relevant compute gate) | `G_t` (DecisionRelevanceGate) — 4-way conjunction | MET-COMP-003 (compute_normalized_return), MET-COMP-004 (compute_efficiency_gain) | ABL-023 (uncertainty instead), ABL-033 (no decision-relevance gate), ABL-034 (always-plan) | BLOCKED — CATTS threat 미등록, BASE-015 미구현 |

**주의**: "DESIGNING" 상태(C3)는 설계 진행 중이라는 뜻이지 구현 완료나 ALIVE 판정이 아니다.

---

## Section 7. Required Logs for Later Implementation

Phase 8 구현 시 반드시 기록해야 하는 16개 필드.

| 번호 | 필드명 | 유형 | 설명 |
|---|---|---|---|
| 1 | `selected_hypothesis_id` | str | 직전 action 생성에 사용된 h_exec의 ID (h_exec trace) |
| 2 | `alternative_hypothesis_ids` | List[str] | A_t^H 구성 hypothesis ID 목록 |
| 3 | `evidence_summary` | dict | e_t 구조 (effect_type, dom_diff, 등 10개 하위 필드) |
| 4 | `loglik_exec` | float | ell_t(h_exec) 값 |
| 5 | `loglik_alt_best` | float | max_{h_alt} ell_t(h_alt) 값 |
| 6 | `F_t` | float | LR falsification score |
| 7 | `posterior_before` | dict | 이전 step의 b_t(z^r, z^g) |
| 8 | `posterior_after` | dict | 현재 step의 b_t(z^r, z^g) |
| 9 | `adopted_hypothesis_id` | str | G_t=1일 때 h* ID; G_t=0이면 h_exec |
| 10 | `decision_relevance_delta` | float | ΔV_t 값 |
| 11 | `gate_reason` | str | G_t 판정 이유 (어떤 조건 위반/충족) |
| 12 | `rewrite_triggered` | bool | Rewrite 발동 여부 |
| 13 | `rewrite_confidence` | float | Rewrite confidence score |
| 14 | `fallback_used` | bool | fallback rule 발동 여부 |
| 15 | `planning_calls` | int | episode 내 G_t=1 횟수 (MET-COMP-003/004 계산용) |
| 16 | `rollout_steps` | int | 실제 rollout 실행 step 수 |

**우선순위**:
- `planning_calls` (15) + `selected_hypothesis_id` (1) + `F_t` (6): P3_EVAL BLOCKED의 직접 원인. Phase 8에서 반드시 최우선 구현.
- `loglik_exec`/`loglik_alt_best` (4,5): LR score 계산의 기본 재료.
- `gate_reason` (11): G_t 동작 디버깅에 필수.

---

## Section 8. Anti-Leakage Contract

아래 필드는 inference input에 절대 들어갈 수 없다.

```
FORBIDDEN FROM INFERENCE INPUT:
- true_control_grammar
- true_regime
- true_change_point
- true_reveal_vs_shift
- true_wrong_hypothesis
- counterfactual_action_effects
- oracle_regime_action
- oracle_grammar_action
- oracle_best_action
- hidden_state_flags (모든 hidden_ 접두어 필드)
- counterfactual table 전체
- oracle labels 전체
```

추가 계약:
- `h_exec`는 **predicted trace**이며 oracle label이 아님. step log의 `selected_hypothesis_id`에서 읽음.
- Evidence likelihood `ell_t(h)`는 **observed public evidence** (`e_t`)에서만 계산.
- hidden labels는 training/eval **target** 또는 **audit** 용도로만 사용 가능.
- `b_t(z^r, z^g)` 계산은 **public observation history** (`H_t`)만 사용.

근거: `paper_context_ref/06_DATA_SCHEMA_AND_LABELING.md §4` (33개 필드, 5개 카테고리)  
런타임 적용: `src/frcgw/schemas/visibility.py::FORBIDDEN_AGENT_FIELDS`  
싱크 테스트: `tests/test_forbidden_field_mirror_sync.py` (항상 green 유지)

---

## Section 9. Degenerate Cases

11개 degenerate case와 처리 방침.

| # | Case | 증상 | 처리 방침 |
|---|---|---|---|
| 1 | `H_alt empty` (A_t^H가 비어 있음) | F_t = 0. 항상 h_exec 유지. planning 불가 | 경고 로그. Proposer 모듈 진단. `alternative_hypothesis_ids` = [] 기록 |
| 2 | `h_exec missing` | F_t = UNDEFINED. selected_hypothesis_id 미기록 | F_t = 0으로 fallback + BLOCKER 경고. Phase 8에서 반드시 해결 |
| 3 | `all ell_t equal` (h_exec와 h_alt의 ell_t가 모두 같음) | F_t = 0 항상. evidence가 모든 hypothesis를 동등하게 설명함 | 모델 underfit 의심. 학습 진단 필요 |
| 4 | `F_t always zero` | planning_calls = 0. P3_EVAL BLOCKED 재현. FRCG-FULL = no_control_grammar | CRITICAL. 모델 weight 진단 + 학습 step 연장 필요. `P3_EVAL.BLOCKED_planning_calls_zero.md` 재현 조건 |
| 5 | `F_t always high` | planning_calls = episode steps. G_t 항상 1. always-plan ablation과 동일 | τ_f threshold calibration 필요. ABL-034 (always-plan) 경계로 진단 |
| 6 | `G_t never fires` | τ_f/τ_v/τ_a 너무 높거나 F_t/ΔV_t 항상 낮음 | threshold 낮추기 + 학습 진단. degenerate (4)와 구분: 여기서는 F_t > 0이지만 G_t = 0 |
| 7 | `G_t always fires` | threshold 너무 낮음. always-plan과 동일 | τ 상향 조정. ABL-034 baseline과 비교 |
| 8 | `Rewrite always no-op` | rewrite_triggered = True이지만 a_exec = a_base 항상 | ABL-035 (no-action-rewrite)와 동일 상태. Rewrite module 학습 실패 의심 |
| 9 | `Rewrite always overrides` | rewrite_confidence 무관하게 항상 base_action을 override | fallback rule 미작동. τ_r threshold 진단 필요 |
| 10 | `posterior never changes` | b_t(z^r, z^g)가 episode 전체에서 고정 | PosteriorUpdater 학습 실패. history encoding이 b_t에 영향 없음 |
| 11 | `posterior changes without evidence` | e_t = no_effect이지만 b_t가 큰 폭으로 변화 | spurious update. evidence가 실제로 포함된 건지 audit 필요. leakage probe (ABL-040) 트리거 |

**가장 위험한 degenerate case**: (4) `F_t always zero` → P3_EVAL BLOCKED 재현. (11) `posterior changes without evidence` → leakage 의심 즉시 중단.

---

## Section 10. Handoff to Future Runs

### Run 2 (Phase 3/4): Evidence Card / MD Refactor에 넘길 항목

- Evidence Card schema 확정 (C1~C6 card stub): 6개 필수 필드 (source_evidence, code_evidence, test_evidence, experiment_evidence, counter_evidence, decision_rationale)
- C1~C6 각 card의 BLOCKED/DESIGNING/CONDITIONAL 이유 기록
- paper_context_ref 수정 대상 목록: `08_LOSS_REWARD_TRAINING_OBJECTIVE.md` (L-MAIN-005 BCE → LR 전환), `09_PLANNING_THEORY_ALGORITHM.md` (§7 F_t candidates 상태 업데이트), `FINAL_RESEARCH_BLUEPRINT.md` (C3 claim 명확화)

### Run 3 (Phase 5/6/7): Implementation Contract / Test Plan / Eval Gate

- Phase 5: 이 문서(Section 4)의 I/O contract를 module-level signature로 변환
- Phase 6: 각 component별 단위 테스트 목록 (stub)
- Phase 7: CC-P3-G1/G3/G4 재정의 + ABL-016/022/023/024 비교 조건 명세
- 인계 항목: Section 4의 failure mode 목록 → 각 failure mode에 대한 테스트 case 작성

### Run 4 (Phase 8/9): Text-only Smoke / GUI Integration

- Phase 8: `src/frcgw/falsification/lr_scorer.py` 실 구현. planning_calls > 0 달성.
- Phase 9: `src/frcgw/gui_env/`와 LR scorer 연동. GUI observation에서 `e_t` 추출 → `F_t` 계산.
- 우선순위: Section 7 필드 16개 중 (1) selected_hypothesis_id, (6) F_t, (15) planning_calls 먼저 구현

### Run 5 (Phase 10): Baseline/Ablation 확장

- BASE-026 (WAC-style), BASE-027 (CUWM-style), BASE-028 (WebWorld-style) 구현
- ABL-016/017/022/023/024/035/039 구현 + `tests/test_ablation_runner.py` count 동반 업데이트
- `BCEBinaryFalsificationScorer` → ABL-022/023 ablation으로 정식 등록

### Run 6 (Phase 11/12): Evaluation / Survivability Decision

- MET-PERSIST-001/WM-001/ALT-001/FALS-001/002/LATENT-001 계산
- C1~C6 Evidence Card 채우기
- LR vs BCE mechanism delta 통계 검증 (Option A vs Option B 최종 비교)

---

## Section 11. Run 1 Design Verdict

**`LR_DESIGN_READY_FOR_LEDGER`**

근거:
1. `ell_t`, `F_t`, `b_t`, `ΔV_t`, `G_t`, `Rewrite` 6개 핵심 수식이 `paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md §6.2~6.6`에 완전히 정의되어 있음
2. 5개 component의 I/O contract가 이 문서에 명세됨
3. Symbol table (9개), Required log fields (16개), Degenerate cases (11개) 완성
4. Anti-leakage contract 명시됨
5. Main path vs ablation path 구분 완성

**주의**: "LR_DESIGN_READY_FOR_LEDGER"는 설계 문서가 다음 단계(Run 3 Phase 5 Implementation Contract)에 넘겨질 준비가 됐다는 의미다. "구현 준비 완료"가 아니다. Run 1에서는 구현하지 않는다.

남은 설계 미결 항목 (Phase 5에서 확정):
- τ_f, τ_v, τ_a threshold calibration 방법
- `EvidenceLikelihood`의 구체적 architecture (transformer head vs MLP head)
- `PosteriorUpdater`의 KL regularization term
- Proposer module (A_t^H 생성 방법)

---

*생성일: 2026-05-16 / Run 1 / Phase 2 산출물*  
*근거: `docs/orchestration/lr_alignment/00_OPTION_B_PHASE_ROADMAP.md` Section 4 Phase 2, Section 5 Run 1*  
*수정 금지: `paper_context_ref/` 전체 (Phase 4 계획 + 사용자 승인 후)*
