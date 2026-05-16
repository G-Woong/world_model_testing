---
file_id: LR-IMPLEMENTATION-CONTRACT-R3
title: LR Implementation Contract — Phase 5 산출물
phase: 5 (LR Implementation Contract)
run: 3
date: 2026-05-16
status: CONTRACT_DOCUMENT
language: ko
type: contract_not_implementation
---

# 05_lr_implementation_contract.md

**Phase**: 5 — LR Implementation Contract  
**Run**: 3  
**Date**: 2026-05-16  
**Type**: 구현 계약 문서. 구현 파일이 아님. Run 3에서는 구현하지 않는다.

---

## Section 1. Purpose

이 문서는 **구현 계약서이며 구현 코드가 아니다**.

### 1.1 이 문서의 역할

- Run 4에서 구현할 `LikelihoodRatioFalsificationScorer`의 인터페이스 계약을 확정
- 14개 symbol의 타입 서명, 입출력 계약, 실패 모드, anti-leakage 요구사항을 정의
- `src/frcgw/falsification/lr_scorer_stub.py` (Phase 5 stub)의 직접 근거 문서

### 1.2 C1/C3/C5 생존 조건과의 관계

**이 계약이 확정되기 전에는 다음이 금지된다**:

- C3는 LR scorer 구현 전까지 `ALIVE_WITH_EVIDENCE` 또는 `ALIVE` 선언 금지
- C1은 h_exec trace 구현 전까지 `ALIVE_WITH_EVIDENCE` 선언 금지
- C5는 rewrite metric (MET-REWRITE-001) + ABL-017 구현 전까지 `ALIVE_WITH_EVIDENCE` 선언 금지

근거: `docs/orchestration/lr_alignment/03_concept_survivability_ledger.md §4` (Status Transition Rules 4~8)

### 1.3 이 문서에서 하지 않는 것

- 실제 LR 계산 로직 작성 (F_t 계산식, posterior update 알고리즘, likelihood scoring 구현)
- torch/numpy/pandas/sklearn 의존성 도입
- `paper_context_ref/` 수정
- 기존 `src/frcgw/` 파일 수정
- P3 재학습 또는 P3_EVAL 재실행
- baseline/ablation 코드 추가
- C1~C6 ALIVE/DEAD 확정
- Evidence Card final 판정

---

## Section 2. Contract Scope

### 2.1 In Scope (이 문서가 확정하는 범위)

- `EvidenceLikelihood` 인터페이스 계약
- `LikelihoodRatioFalsificationScorer` 인터페이스 계약
- `PosteriorUpdater` 인터페이스 계약
- `DecisionRelevanceGate` 인터페이스 계약
- `GrammarConditionedRewrite` 인터페이스 계약
- h_exec trace 로그 필드 명세 (`selected_hypothesis_id`)
- Anti-leakage contract (어떤 필드가 inference input에 들어가면 안 되는가)
- Diagnostic output 요구사항 (어떤 필드를 step log에 기록해야 하는가)
- 9개 dataclass 타입 정의

### 2.2 Out of Scope (이 문서가 포함하지 않는 것)

- 실제 계산 로직 (ell_t, F_t, posterior, gate, rewrite 알고리즘)
- training loop, loss function, optimizer 설정
- P3 재학습 지시
- baseline/ablation 구현 (`baselines.py`, `ablations.py`)
- `paper_context_ref/` 내용 수정
- final claim 판정 또는 Evidence Card 완성

---

## Section 3. Primary Survival Axis Mapping

C1/C3/C5는 primary survival axis다. 이 계약의 모든 component는 이 3개 claim과 직접 연결된다.

| Claim | Position | Contract Component | Required Stub Symbol | Required Future Evidence | Current Run 3 Output |
|---|---|---|---|---|---|
| **C1** wrong-grammar persistence | primary survival axis | h_exec trace | `HypothesisTrace` / `selected_hypothesis_id` 필드 | MET-PERSIST-001: Run 6 artifact | contract only (Run 3) |
| **C3** LR falsification mechanism | primary survival axis | `LikelihoodRatioFalsificationScorer` | `LikelihoodRatioFalsificationScorer.score()` | ABL-022/ABL-023 비교: Run 6 | contract + stub (Run 3) |
| **C5** grammar-conditioned rewrite | primary survival axis | `GrammarConditionedRewrite` | `GrammarConditionedRewrite.rewrite()` | MET-REWRITE-001 + ABL-017: Run 5/6 | contract only (Run 3) |

**추가 claim 위치**:

| Claim | Position | Contract Component |
|---|---|---|
| **C2** regime/grammar separation | high-risk architecture hypothesis | `PosteriorUpdater` (b_t factorization) |
| **C4** alternative grammar rollout | supporting mechanism claim | `DecisionRelevanceGate` (ΔV_t 계산) |
| **C6** decision-relevant compute gate | supporting efficiency claim | `DecisionRelevanceGate` (G_t 4-way conjunction) |

---

## Section 4. Data Structures and Types (9개 dataclass)

아래 9개 dataclass는 `src/frcgw/falsification/lr_scorer_stub.py`에 정의되며,  
`from __future__ import annotations`, `dataclasses`, `typing` import만 사용한다.  
torch/numpy/pandas/sklearn import 금지.

---

### 4.1 EvidenceFeatures

**역할**: 공개 관측에서 추출된 action-effect evidence.  
**소스**: `paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md §6.2`

| 필드 | 타입 | 내용 |
|---|---|---|
| `effect_type` | `str` | observed effect 유형 (no-effect, partial, full, delayed, noisy 등) |
| `dom_diff_summary` | `str` | DOM 변화 요약 (공개 관측값) |
| `accessibility_diff_summary` | `str` | accessibility tree 변화 요약 (공개 관측값) |
| `visual_diff_score` | `float` | 시각적 변화 점수 (0.0~1.0) |
| `precondition_status` | `str` | 사전조건 충족 여부 |
| `no_effect_flag` | `bool` | action 후 효과 없음 플래그 |
| `delayed_effect_flag` | `bool` | 지연 효과 플래그 |
| `noisy_observation_flag` | `bool` | noisy 관측 플래그 |
| `progress_delta` | `float` | task 진행도 변화 |
| `failure_reason` | `Optional[str]` | 실패 이유 (없으면 None) |

**Anti-leakage**: 이 dataclass의 모든 필드는 public observed evidence만 포함한다.  
`true_control_grammar`, `true_regime`, `oracle_*`, `counterfactual_action_effects` 포함 금지.

---

### 4.2 HypothesisTrace

**역할**: 직전 action 생성에 실제로 사용된 hypothesis의 predicted trace.  
**소스**: `paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md §5 Symbol Table line 123`

| 필드 | 타입 | 내용 |
|---|---|---|
| `selected_hypothesis_id` | `str` | 실행에 사용된 h_exec의 ID (model/agent 선택) |
| `hypothesis_type` | `str` | regime 또는 control_grammar 구분 |
| `confidence` | `float` | hypothesis 선택 confidence |
| `source` | `str` | 이 trace의 생성 출처 (model output path) |
| `is_oracle_label` | `bool` | 항상 `False`. oracle label 금지. |

**Anti-leakage**: `selected_hypothesis_id`는 model/agent 예측. `true_control_grammar`, `true_regime`과 혼동 금지.  
`is_oracle_label`은 항상 `False`여야 한다.

---

### 4.3 HypothesisCandidate

**역할**: A_t^H (alternative hypothesis set)의 후보 hypothesis.  
**소스**: `paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md §8 PROP-01..10`

| 필드 | 타입 | 내용 |
|---|---|---|
| `hypothesis_id` | `str` | 후보 hypothesis ID |
| `regime_id` | `str` | 연관 regime ID |
| `control_grammar_id` | `str` | 연관 control grammar ID |
| `prior_logprob` | `float` | 사전 확률 (log scale) |
| `metadata` | `Dict[str, Any]` | 추가 메타데이터 (기본값: `{}`) |

**주의**: A_t^H는 alternative **hypothesis** set이지 alternative **action** set이 아니다.

---

### 4.4 LikelihoodScore

**역할**: 단일 hypothesis에 대한 EvidenceLikelihood 출력.  
**소스**: `paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md §6.2 line 152`

수식: `ell_t(h) = log p_theta(e_t | H_{t-1}, a_{t-1}, h)`

| 필드 | 타입 | 내용 |
|---|---|---|
| `hypothesis_id` | `str` | 평가된 hypothesis ID |
| `loglik` | `float` | `ell_t(h)` 값 |
| `diagnostics` | `Dict[str, Any]` | 진단 정보 (기본값: `{}`) |

---

### 4.5 FalsificationResult

**역할**: LikelihoodRatioFalsificationScorer의 출력.  
**소스**: `paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md §6.3 line 171`

수식: `F_t = max_{h_alt ∈ A_t^H} [ell_t(h_alt) − ell_t(h_exec)]`

| 필드 | 타입 | 내용 |
|---|---|---|
| `h_exec_id` | `str` | 실행에 사용된 hypothesis ID |
| `best_h_alt_id` | `Optional[str]` | argmax alternative hypothesis ID (없으면 None) |
| `loglik_exec` | `float` | `ell_t(h_exec)` 값 |
| `loglik_alt_best` | `float` | `max_{h_alt} ell_t(h_alt)` 값 |
| `F_t` | `float` | LR falsification score |
| `margin` | `float` | `F_t - tau_f` (threshold margin) |
| `degenerate` | `bool` | degenerate case 여부 (all equal, empty alt 등) |
| `calibration_features` | `Dict[str, Any]` | calibration 진단 (기본값: `{}`) |

---

### 4.6 PosteriorState

**역할**: 현재 step의 regime/grammar posterior 상태.  
**소스**: `paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md §6.1 line 142`

수식: `b_t(z^r, z^g) = q_phi(z^r, z^g | H_t)` — learned approximation (NOT exact Bayesian)

| 필드 | 타입 | 내용 |
|---|---|---|
| `posterior_by_hypothesis` | `Dict[str, float]` | hypothesis ID → posterior probability |
| `entropy` | `float` | posterior entropy |
| `top_hypothesis_id` | `str` | argmax hypothesis ID |

---

### 4.7 PosteriorUpdateResult

**역할**: PosteriorUpdater 단계의 결과.  
**소스**: `docs/orchestration/lr_alignment/02_option_b_design_plan.md §4.3`

| 필드 | 타입 | 내용 |
|---|---|---|
| `posterior_before` | `PosteriorState` | 업데이트 전 posterior |
| `posterior_after` | `PosteriorState` | 업데이트 후 posterior |
| `posterior_shift` | `float` | KL 또는 L2 기반 변화량 |
| `adopted_hypothesis_id` | `str` | G_t=1일 때 채택된 hypothesis ID |
| `switch_recommended` | `bool` | hypothesis 전환 권고 여부 |

---

### 4.8 GateDecision

**역할**: DecisionRelevanceGate의 출력.  
**소스**: `paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md §6.5 lines 200-209`

수식:
```
G_t = I[F_t > τ_f ∧ ΔV_t > τ_v ∧ P(action_switch) > τ_a ∧ ΔV_t − C_plan > 0]
```

| 필드 | 타입 | 내용 |
|---|---|---|
| `G_t` | `bool` | planning compute 허용 여부 |
| `planning_allowed` | `bool` | `G_t`와 동일 (명시적 alias) |
| `decision_relevance_delta` | `float` | ΔV_t 값 |
| `action_switch_probability` | `float` | P(action_switch \| A_t^H, H_t) |
| `compute_cost` | `float` | C_plan (β × rollout_steps) |
| `gate_reason` | `str` | 어떤 조건이 위반/충족됐는지 기록 |

**주의**: G_t는 uncertainty > threshold 단일 조건이 아님. 4개 조건의 conjunction.

---

### 4.9 RewriteDecision

**역할**: GrammarConditionedRewrite의 출력.  
**소스**: `paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md §6.6`

수식: `a_exec = Rewrite(intent=i_t, base_action=a_base, selected_hypothesis=h*)`

| 필드 | 타입 | 내용 |
|---|---|---|
| `intent_id` | `str` | high-level task intent ID |
| `base_action_id` | `str` | rewrite 전 base action ID |
| `selected_hypothesis_id` | `str` | h* ID (predicted trace, NOT oracle) |
| `executable_action_id` | `str` | rewrite 후 최종 실행 action ID |
| `rewrite_triggered` | `bool` | rewrite 발동 여부 |
| `rewrite_confidence` | `float` | rewrite confidence score |
| `fallback_used` | `bool` | fallback rule 발동 여부 (confidence < τ_r) |
| `rewrite_reason` | `str` | rewrite 또는 fallback 이유 |

---

## Section 5. Component Contracts (5개)

---

### 5.1 EvidenceLikelihood

**수식**: `ell_t(h) = log p_theta(e_t | H_{t-1}, a_{t-1}, h)`  
**소스**: `paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md §6.2 line 152`

**Input**:
- `evidence: EvidenceFeatures` — public observed evidence
- `hypothesis: HypothesisCandidate` — 평가 대상 hypothesis (h_exec 또는 h_alt)
- `history_encoding: Any` — H_{t-1} history encoder output (observed history only)
- `prev_action: Any` — 직전 action representation

**Output**:
- `LikelihoodScore` — `loglik` (ell_t(h)) + `diagnostics`

**Failure Modes**:
- `no_effect_flag=True`: evidence 신호 없음 → loglik 신뢰도 하락. `degenerate=True` 표시
- `delayed_effect_flag=True`: 지연 effect → 즉각 falsification 불가. 경고 로그
- `noisy_observation_flag=True`: noisy observation → loglik variance 증가. 경고 로그
- `ambiguous_evidence`: 여러 hypothesis가 동등하게 설명 → F_t ≈ 0
- `e_t`에 `FORBIDDEN_AGENT_FIELDS` 포함: **LEAKAGE ERROR — 즉시 중단**
- `h`가 oracle label (`is_oracle_label=True`): **FORBIDDEN — 구현 금지**

**Anti-leakage**: `e_t`는 public observed evidence만. `H_{t-1}`에 hidden label 포함 금지.

---

### 5.2 LikelihoodRatioFalsificationScorer

**수식**: `F_t = max_{h_alt ∈ A_t^H} [ell_t(h_alt) − ell_t(h_exec)]`  
**소스**: `paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md §6.3 line 171`

**주요 명시**: **BCE는 main path가 아니다. BCE is comparison/ablation only.**  
`BCEBinaryFalsificationScorer`는 ABL-022 / ABL-023 ablation path에서만 사용된다.

**Input**:
- `h_exec_trace: HypothesisTrace` — 실행된 hypothesis의 predicted trace
- `exec_likelihood: LikelihoodScore` — `ell_t(h_exec)`
- `alt_likelihoods: List[LikelihoodScore]` — 모든 h_alt의 `ell_t(h_alt)` 목록
- `alt_candidates: List[HypothesisCandidate]` — A_t^H 구성 hypothesis 목록

**Output**:
- `FalsificationResult` — F_t, best_h_alt_id, loglik_exec, loglik_alt_best, degenerate

**Failure Modes**:
- `h_exec missing` (`selected_hypothesis_id` 빈값): F_t = UNDEFINED → fallback F_t=0 + **BLOCKER 경고**
- `H_alt empty` (alt_candidates 빈 리스트): F_t = 0, degenerate=True. 로그 기록 필수
- `all loglik equal`: F_t = 0, degenerate=True → 모델 underfit 의심
- `F_t always zero`: **CRITICAL** — P3_EVAL BLOCKED 재현 조건. 학습 step 연장 필요
- `F_t always high`: threshold calibration 필요. ABL-034 (always-plan) 경계
- `best alt = h_exec`: 이론적 불일치 → 경고 로그
- `degenerate likelihood scale`: log-sum-exp 사용 확인 필요

---

### 5.3 PosteriorUpdater

**수식**: `b_t(z^r, z^g) = q_phi(z^r, z^g | H_t)` — **exact Bayesian posterior 아님, learned approximation**  
**소스**: `paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md §6.1 line 142`

**Input**:
- `prior_state: PosteriorState` — 이전 step의 b_{t-1}
- `evidence: EvidenceFeatures` — 현재 step의 e_t (public observed)
- `falsification_result: FalsificationResult` — F_t 결과
- `history_encoding: Any` — H_t 인코딩 (public observation history)

**Output**:
- `PosteriorUpdateResult` — posterior_before, posterior_after, posterior_shift, switch_recommended

**Failure Modes**:
- `posterior collapse`: 단일 hypothesis에 집중 → Locatello impossibility 관련 (C2 KNOWN RISK)
- `over-switching`: evidence 없이 (no_effect_flag=True) hypothesis 전환 → leakage probe (ABL-040)
- `under-switching`: F_t 높지만 posterior 고정 → threshold calibration 필요
- `switch without evidence`: spurious update → 즉각 leakage audit 트리거
- `no switch despite strong evidence`: G_t 판단에 영향

**Anti-leakage**: `H_t`에 `true_regime`, `true_control_grammar` 포함 금지.

---

### 5.4 DecisionRelevanceGate

**수식**:
```
ΔV_t = max_{h_alt∈A_t^H, a∈A} V(a, h_alt) − max_{a∈A} V(a, h_exec)
G_t = I[F_t > τ_f ∧ ΔV_t > τ_v ∧ P(switch|A_t^H, H_t) > τ_a ∧ ΔV_t − C_plan > 0]
```
**소스**: `paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md §6.5 lines 200-209`

**주요 명시**: G_t는 **uncertainty > threshold 단일 조건이 아님**. 4개 조건의 conjunction.

**Input**:
- `falsification_result: FalsificationResult` — F_t
- `posterior_update: PosteriorUpdateResult` — 최신 posterior
- `value_gain_delta: float` — ΔV_t (WM-based rollout 결과)
- `action_switch_probability: float` — P(switch | A_t^H, H_t)
- `compute_cost: float` — C_plan (β × rollout_steps)
- `tau_f, tau_v, tau_a: float` — threshold 파라미터 (Phase 7에서 calibration 정책 명세)

**Output**:
- `GateDecision` — G_t, planning_allowed, decision_relevance_delta, gate_reason

**Failure Modes**:
- `G_t always 0` (never fires): threshold 너무 높거나 F_t 항상 낮음 → planning_calls=0 재현 (**CRITICAL**)
- `G_t always 1` (always fires): threshold 너무 낮음 → ABL-034 (always-plan) 경계
- `ΔV_t − C_plan < 0` 항상: planning 비용이 항상 이득 초과 → threshold calibration 필요
- `uncertainty-gate collapse`: G_t가 uncertainty gate (BASE-012)와 동일 동작 → C6 핵심 distinction 붕괴
- `false planning call`: G_t=1이지만 hypothesis switch 불필요 (false positive)

---

### 5.5 GrammarConditionedRewrite

**수식**: `a_exec = Rewrite(intent=i_t, base_action=a_base, selected_hypothesis=h*)`  
**소스**: `paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md §6.6`

**주요 명시**: h*는 **predicted trace**이지 oracle label이 아니다.  
`rewrite_confidence < τ_r`이면 fallback rule 발동.

**Input**:
- `intent_id: str` — high-level task intent (public)
- `base_action_id: str` — 현재 selected action (rewrite 전)
- `selected_hypothesis: HypothesisTrace` — G_t gate 이후 채택된 h* (predicted trace)
- `rewrite_confidence_threshold: float` — τ_r threshold

**Output**:
- `RewriteDecision` — executable_action_id, rewrite_triggered, rewrite_confidence, fallback_used

**Failure Modes**:
- `no-op rewrite`: a_exec == a_base 항상 → C5 mechanism missing (ABL-035 상태와 동일)
- `harmful rewrite`: precondition_check(a_exec) == INVALID → fallback 발동
- `unnecessary rewrite`: G_t=0임에도 rewrite 발동 → scope 위반
- `fallback never used`: rewrite_confidence 항상 ≥ τ_r → τ_r calibration 필요
- `fallback always used`: rewrite_confidence 항상 < τ_r → Rewrite 학습 실패 의심

**Anti-leakage**: `selected_hypothesis.is_oracle_label` = False 필수.  
`oracle_grammar_action`, `oracle_best_action` 입력 금지.

---

## Section 6. Anti-Leakage Contract

### 6.1 inference input 절대 금지 필드 (FORBIDDEN_AGENT_FIELDS + 확장)

아래 필드는 `EvidenceFeatures`, `HypothesisTrace`, `HypothesisCandidate`,  
`LikelihoodScore`, `FalsificationResult`, `PosteriorState`, `GateDecision`, `RewriteDecision`  
어디에도 포함되면 안 된다.

```
FORBIDDEN FROM INFERENCE INPUT:
- true_regime                  (FORBIDDEN_AGENT_FIELDS)
- true_control_grammar         (FORBIDDEN_AGENT_FIELDS)
- true_change_point            (FORBIDDEN_AGENT_FIELDS)
- true_reveal_vs_shift         (FORBIDDEN_AGENT_FIELDS)
- true_wrong_hypothesis        (FORBIDDEN_AGENT_FIELDS)
- counterfactual_action_effects (FORBIDDEN_AGENT_FIELDS)
- oracle_regime_action         (FORBIDDEN_AGENT_FIELDS)
- oracle_grammar_action        (FORBIDDEN_AGENT_FIELDS)
- oracle_best_action           (FORBIDDEN_AGENT_FIELDS)
- hidden_state_flags (모든 hidden_ 접두어 필드)
- counterfactual table 전체
- oracle labels 전체
- split_id, ood_type, template_id, seed, policy_id (split/audit metadata)
- 미래 step의 evidence (future evidence leakage)
```

근거: `src/frcgw/schemas/visibility.py::FORBIDDEN_AGENT_FIELDS` (15개 필드)  
SSoT: `paper_context_ref/06_DATA_SCHEMA_AND_LABELING.md §4`

### 6.2 명시적 계약

- **h_exec = predicted trace**: `HypothesisTrace.selected_hypothesis_id`는 model/agent 선택. oracle label이 아님
- **selected_hypothesis_id = model/agent 선택**: step log에서 기록하는 필드. `true_control_grammar`과 혼동 금지
- **EvidenceFeatures = public observation에서만 생성**: DOM diff, accessibility diff, visual diff, precondition status 등 공개 관측값만 포함
- **hidden labels = training/eval target 또는 audit 용도만**: `true_control_grammar` 등은 training loss target 또는 audit 메타데이터로만 사용
- **미래 evidence 접근 금지**: e_t는 현재 step의 observed evidence만

### 6.3 Leakage Detection 우선 처리 경로

1. `assert_agent_observation_safe()` 호출: `src/frcgw/schemas/visibility.py`
2. `HiddenLabelLeakageError`: forbidden field가 inference input에 포함 시 즉시 raise
3. `CounterfactualLeakageError`: `counterfactual_action_effects` 포함 시 즉시 raise
4. 이 중 하나라도 발생하면 **즉시 중단 + blocker 보고**

---

## Section 7. Signature Stub Contract

`src/frcgw/falsification/lr_scorer_stub.py`에 들어갈 14개 symbol 목록:

### 7.1 Dataclass 9개

1. `EvidenceFeatures`
2. `HypothesisTrace`
3. `HypothesisCandidate`
4. `LikelihoodScore`
5. `FalsificationResult`
6. `PosteriorState`
7. `PosteriorUpdateResult`
8. `GateDecision`
9. `RewriteDecision`

### 7.2 Component Class 5개

10. `EvidenceLikelihood` — `score()` method
11. `LikelihoodRatioFalsificationScorer` — `score()` method
12. `PosteriorUpdater` — `update()` method
13. `DecisionRelevanceGate` — `decide()` method
14. `GrammarConditionedRewrite` — `rewrite()` method

### 7.3 Stub 규칙

- `from __future__ import annotations` 필수
- `dataclasses`, `typing` import만 허용
- torch/numpy/pandas/sklearn import 절대 금지
- dataclass decorator, field default, type hint, docstring 포함
- method body: `raise NotImplementedError("Run 3 signature stub only; implement in Run 4.")`
- 실제 계산 로직 없음
- repository state 변경 없음 (파일 생성만, 기존 파일 수정 없음)
- `__init__.py` 생성 없음

---

## Section 8. Handoff to Run 4

Run 4 (Phase 8)에서 구현할 항목:

1. **Priority 1**: `src/frcgw/falsification/lr_scorer.py` — 실제 EvidenceLikelihood + LikelihoodRatioFalsificationScorer 구현
2. **Priority 1**: `selected_hypothesis_id` step log populate — h_exec trace 활성화 (C1 blocker 해소)
3. **Priority 1**: text-only smoke에서 `planning_calls > 0` 확인 (P3_EVAL.BLOCKED 해소 조건)
4. **Priority 2**: `GrammarConditionedRewrite` 구현 (C5)
5. **Priority 2**: `PosteriorUpdater` 구현 (C2/C3)
6. **Priority 2**: `DecisionRelevanceGate` 구현 (C6)
7. **Priority 3**: MET-WM-001 / MET-ALT-001 구현 (C4)
8. C1/C3/C5 Evidence Card의 `code_evidence`, `test_evidence` 갱신

---

## Section 9. Phase 5 Verdict

**`LR_CONTRACT_READY_FOR_TEST_PLAN`**

근거:
1. 9개 dataclass 타입 계약 완성 (Section 4)
2. 5개 component I/O contract 완성 (Section 5)
3. Anti-leakage contract 명시 (Section 6)
4. 14개 stub symbol 목록 확정 (Section 7)
5. C1/C3/C5 primary survival axis 매핑 완성 (Section 3)
6. Run 4 handoff 우선순위 명시 (Section 8)
7. `lr_scorer_stub.py` 생성 완료 (torch/numpy 없음, NotImplementedError만)

**주의**: "LR_CONTRACT_READY_FOR_TEST_PLAN"은 Phase 6 (Unit Test Plan)으로 진행할 준비가 됐다는 의미다.  
"구현 준비 완료"가 아니다. Run 3에서는 구현하지 않는다.

---

*생성일: 2026-05-16 / Run 3 / Phase 5 산출물*  
*근거: `docs/orchestration/lr_alignment/00_OPTION_B_PHASE_ROADMAP.md` Section 4 Phase 5, Section 5 Run 3*  
*수정 금지: `paper_context_ref/` 전체 (Phase 4 계획 + 사용자 승인 후)*  
*C1~C6 ALIVE/DEAD 최종 판정 금지: Phase 11 Evidence Card 완성 이후에만 허용*
