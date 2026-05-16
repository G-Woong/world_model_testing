# Run 4-POST 완료 보고

**날짜**: 2026-05-16  
**대상 산출물**: Run 4 (Phase 8/9 — Option B LR Alignment)  
**검증자**: Claude Code (read-only, no code changes)  
**브랜치**: memory-redesign-2026-05-16  
**최신 커밋**: 1f62d87 (merge: accept codex-work TASK_1024 GUI env data integrity scaffold)

---

## 생성 파일

- `docs/orchestration/lr_alignment/09_run4_post_verification_report.md` (이 파일)

코드 수정: **0건**. Phase gate sentinel 생성: **0건**.

---

## 핵심 요약

- **LR core verification**: PASS — 14 symbol (9 dataclass + 5 component) 존재, F_t = max_alt - exec 구조 확인, BCE/sigmoid 키워드 main path 부재, degenerate/leakage guard 코드 흐름 확인, torch/numpy import 0개
- **h_exec trace verification**: PASS (with caveat) — ActionRecord 4 optional field 존재, collector L284-287에서 getattr populate 확인, OraclePolicy stale trace risk 식별 (Run 4.6 후속 조치 대상)
- **EvidenceFeatures public-only**: PASS — from_public_step이 step.observed_effect_public만 접근, training_labels/evaluation_labels/counterfactuals/audit_metadata 미접근 코드 확인
- **test status**: 20 passed, 3 skipped (Group B), 0 failed
- **smoke artifact status**: p3_lr_smoke PASS, p4_gui_lr_smoke PASS (manifest 부재 기록)
- **Run 5 readiness**: ablation 12개 / baseline 9개 / config 12 entry 확인, Run 5 변경 대상 파일 목록 작성 완료
- **claim strategy**: C1/C3/C5 primary axis 유지, C2 high-risk 유지, C4/C6 supporting 유지. ALIVE/DEAD 확정 0건

---

## Run 4 구현 검증 요약

| Area | Result | Evidence |
|---|---|---|
| LR core (14 symbols) | PASS | lr_scorer.py §4/§5: 9 dataclass + 5 component class 전체 존재 확인 |
| F_t = max_alt - exec | PASS | lr_scorer.py L412-416: `best_alt = max(alt_likelihoods, key=…); F_t = loglik_alt_best - loglik_exec` |
| BCE keyword main-path | PASS | test_bce_not_main_path 통과; "sigmoid/binary_cross/bce/binary_classifier" 소스 미등장 (분류 표 참조) |
| degenerate/edge-case guard | PASS | h_exec missing → L380-391, alt empty → L399-410, all-equal → L421-424 |
| leakage guard | PASS | _check_metadata_for_leakage() L31-51; counterfactual → CounterfactualLeakageError, true_*/FORBIDDEN → HiddenLabelLeakageError |
| torch/numpy import 0 | PASS | test_no_torch_numpy_dependency_in_stub AST 검사 통과 |
| h_exec trace | PASS | step_schema.py L45-48: 4 optional field 존재; collector.py L284-287: getattr populate |
| anti-leakage (from_public_step) | PASS | lr_scorer.py L100-111: 허용 접근만 사용; 금지 접근 0건 (코드 분석 확인) |
| tests | PASS | 20 passed, 3 skipped (Group B — Run 5 dependency), 0 failed |
| smoke (p3_lr_smoke) | PASS | planning_calls=1, f_t_variance=1.26, null_rate=0.0, leakage=0 |
| GUI smoke (p4_gui_lr_smoke) | PASS | hidden_leakage_count=0, f_t_variance=0.5, gui_lr_integration_status=PASS; manifest 부재는 DEFERRED |
| phase gate sentinels | PASS | P3_LR_EVAL.passed ABSENT, P4_*.passed ABSENT; 기존 P1/P1.5/P2/P3/P3_EVAL 보존 |

---

## 항목 1 — LR Core 상세 검증

### 1.1 14 symbol 존재 확인

**9 dataclass** (`src/frcgw/falsification/lr_scorer.py` §4):
1. `EvidenceFeatures` (L69)
2. `HypothesisTrace` (L127)
3. `HypothesisCandidate` (L144)
4. `LikelihoodScore` (L160)
5. `FalsificationResult` (L174)
6. `PosteriorState` (L195)
7. `PosteriorUpdateResult` (L210)
8. `GateDecision` (L223)
9. `RewriteDecision` (L242)

**5 component class** (`lr_scorer.py` §5):
1. `EvidenceLikelihood` (L275)
2. `LikelihoodRatioFalsificationScorer` (L349)
3. `PosteriorUpdater` (L443)
4. `DecisionRelevanceGate` (L524)
5. `GrammarConditionedRewrite` (L589)

→ **PASS** (test_stub_imports + test_required_dataclasses_exist + test_required_component_classes_exist 통과)

### 1.2 F_t = max_alt[ell_alt - ell_exec] 구조 확인

`lr_scorer.py` L412-416:
```python
best_alt = max(alt_likelihoods, key=lambda s: s.loglik)
loglik_exec = exec_likelihood.loglik
loglik_alt_best = best_alt.loglik
F_t = loglik_alt_best - loglik_exec
```
→ **PASS** — C3 primary claim의 수식과 일치

### 1.3 BCE keyword main-path 재검증

소스 파일: `lr_scorer.py` 전체 (lowercase 스캔)

| Keyword | 등장 라인 | 분류 |
|---|---|---|
| sigmoid | 없음 | — |
| binary_cross | 없음 | — |
| bce | 없음 | — |
| binary_classifier | 없음 | — |

ablation 관련 언급은 다음과 같이 main-path 로직이 아닌 docstring/주석에만 등장:
- L8 (module docstring): `"Classifier-variant losses are ABL-022/023 ablation only."` → 주석, lowercase에 "bce" 없음
- L283 (EvidenceLikelihood docstring): `"Ablation variants (ABL-022/023) are separate."` → 주석, lowercase에 "bce" 없음
- L357-358 (LikelihoodRatioFalsificationScorer docstring): `"Ablation-022/023 comparison variants are separate files"` → 주석, lowercase에 "bce" 없음

**판정: PASS** — BCE 키워드 main path 0건. test_bce_not_main_path 통과 확인.

### 1.4 Edge-case / degenerate guard 코드 흐름

| 케이스 | 위치 | 결과 |
|---|---|---|
| h_exec_id 빈 문자열/None | L379-391 | `degenerate=True, F_t=0.0, reason="h_exec_id_missing"` |
| alt_likelihoods 빈 리스트 | L399-410 | `degenerate=True, F_t=0.0, reason="alt_likelihoods_empty"` |
| all-equal loglik (F_t==0.0) | L421-424 | `degenerate=True, reason="all_loglik_equal"` |
| best_alt == h_exec_id | L427-429 | `degenerate=True, reason contains "best_alt_equals_h_exec"` |
| exec_likelihood.hypothesis_id mismatch | L393-397 | `ValueError` raise |

→ **PASS** — 전체 edge-case 처리 코드 확인

### 1.5 torch/numpy/pandas/sklearn import 0개

AST-level 검사 (`test_no_torch_numpy_dependency_in_stub`): **PASS**
- `lr_scorer.py` imports: `math`, `dataclasses`, `typing`, `frcgw.schemas.visibility` (내부 모듈)
- 외부 numeric 라이브러리 import **0개**

---

## 항목 2 — h_exec Trace 상세 검증

### 2.1 ActionRecord 4 optional field (step_schema.py L45-48)

```python
# step_schema.py L43-48
selected_hypothesis_id: str | None = None
selected_hypothesis_type: str | None = None
selected_hypothesis_confidence: float | None = None
selected_hypothesis_source: str | None = None
```
→ **PASS** — 4 field 존재, is_oracle_label 없음 (HypothesisTrace와 구분됨)

### 2.2 EvaluationLabels.h_exec_id 무변경 확인

`step_schema.py` L77:
```python
h_exec_id: str | None = None
```
- EVALUATION_ONLY bucket에 위치 (`EvaluationLabels` dataclass 내)
- predicted trace 재사용 0건 확인 (ActionRecord.selected_hypothesis_id와 분리된 별도 dataclass)
→ **PASS**

### 2.3 collector.py populate source 확인

`collector.py` L282-287:
```python
selected_hypothesis_id=getattr(policy, "last_selected_hypothesis_id", None),
selected_hypothesis_type=getattr(policy, "last_selected_hypothesis_type", None),
selected_hypothesis_confidence=getattr(policy, "last_selected_hypothesis_confidence", None),
selected_hypothesis_source=getattr(policy, "last_selected_hypothesis_source", None),
```
- `TrainingLabels` / `EvaluationLabels` / `CounterfactualRecord`에서 가져오는 코드: **0건**
→ **PASS** — 예측 trace (policy belief)에서만 populate

### 2.4 Policy별 trace source 표

| Policy | last_selected_hypothesis_id | type | confidence | source |
|---|---|---|---|---|
| WrongGrammarPolicy (L62-65) | `wrong_{final}` | wrong_grammar | 0.5 | wrong_grammar_policy |
| RetryPolicy (L76-79) | retry_same_grammar | retry | 0.3 | retry_policy |
| RecoveryPolicy phase1 (L104-107) | wrong_grammar_recovery_phase1 | wrong_grammar | 0.5 | recovery_policy_phase1 |
| RecoveryPolicy phase2 (L111-114) | recovery_grammar_phase2 | recovery | 0.7 | recovery_policy_phase2 |
| RandomConstrainedPolicy (L124-127) | random_alt | random | 0.1 | random_constrained_policy |
| **OraclePolicy (L43-47)** | **미설정 (None 반환)** | — | — | — |

### 2.5 OraclePolicy stale trace risk 격리 검증

**`_POLICY_INSTANCES` 구조** (`policies.py` L143-149):
```python
_POLICY_INSTANCES: dict[str, Policy] = {
    "oracle":             OraclePolicy(),
    "wrong_grammar":      WrongGrammarPolicy(),
    "retry":              RetryPolicy(),
    "recovery":           RecoveryPolicy(),
    "random_constrained": RandomConstrainedPolicy(),
}
```

**위험 분석** (read-only, 실행 없이 코드 흐름만):

1. **인스턴스 재사용 위험**: `_POLICY_INSTANCES`는 module-level dict로, 동일 인스턴스가 모든 에피소드에서 재사용됨. `PolicyMixtureRunner.sample_policy()`가 인스턴스를 reset하지 않음.

2. **OraclePolicy-specific 위험**:
   - `OraclePolicy.select()` (L43-47)는 `last_selected_hypothesis_id` 등 4개 field를 **설정하지 않음**
   - `Policy` base class에서 `last_selected_hypothesis_id: str | None = None` (L22)는 **class-level attribute** 선언
   - `getattr(oracle_instance, "last_selected_hypothesis_id", None)`은 인스턴스 속성이 없으면 class-level `None` 반환
   - **결과**: OraclePolicy 에피소드 스텝의 `ActionRecord.selected_hypothesis_id = None` (항상)

3. **교차 에피소드 오염 가능성**:
   - 각 policy 타입은 별도 인스턴스 (`_POLICY_INSTANCES`에서 분리됨) → 다른 policy 인스턴스의 `last_*` 오염 없음
   - WrongGrammarPolicy의 `last_*`가 OraclePolicy 인스턴스에 전파되는 경로: **없음** (별개 인스턴스)
   - **단, 같은 policy 타입 내 에피소드 간**: WrongGrammarPolicy는 매 `select()` 호출 시 `last_*`를 덮어쓰므로, 다음 에피소드에서 이전 값이 읽히는 창구가 없음 (select → getattr 순서 보장)

4. **잠재 위험 (실현 조건)**:
   - 미래에 `sample_policy()`가 `select()` 없이 `last_*`를 읽는 코드가 추가될 경우
   - `RecoveryPolicy` 내부에서 `OraclePolicy()`를 새 인스턴스로 생성 후 `select()` 호출 — 이 로컬 인스턴스의 `last_*`는 RecoveryPolicy가 덮어쓰므로 문제 없음

**판정**: 현재 코드에서 실제 오염 경로는 없음. 단, OraclePolicy가 항상 `selected_hypothesis_id=None`을 생성한다는 점은 C1 persistence metric 계산 시 oracle trajectory에 대한 trace 미기록 문제로 이어짐. **Run 4.6 후속 조치 후보로 등록**.

### 2.6 selected_hypothesis_id ∉ FORBIDDEN_AGENT_FIELDS

`visibility.py` FORBIDDEN_AGENT_FIELDS (14개):
```
true_regime, true_control_grammar, true_change_point, true_reveal_vs_shift,
true_wrong_hypothesis, counterfactual_action_effects, oracle_regime_action,
oracle_grammar_action, oracle_best_action, split_id, ood_type, template_id,
seed, policy_id, audit_metadata
```

`selected_hypothesis_id`, `selected_hypothesis_type`, `selected_hypothesis_confidence`, `selected_hypothesis_source` → **전체 FORBIDDEN_AGENT_FIELDS에 없음** ✓

→ **PASS** (`test_selected_hypothesis_not_in_forbidden_agent_fields` 통과)

---

## 항목 3 — EvidenceFeatures public-only 상세 검증

### 3.1 허용/금지 접근 분류

`lr_scorer.py` `EvidenceFeatures.from_public_step()` (L89-123):

**허용 접근** (실제 코드에서 사용됨):
- `step.observed_effect_public` → `eff = step.observed_effect_public` (L100)
- `eff.effect_type` (L101)
- `eff.dom_diff_public` (L102)
- `eff.text_diff_public` (L103)

**금지 접근 여부 (grep 결과)**:
- `step.training_labels` → **0건** ✓
- `step.evaluation_labels` → **0건** ✓
- `step.counterfactuals` → **0건** ✓
- `step.audit_metadata` → **0건** ✓

→ **PASS** — 금지 접근 완전 부재

### 3.2 progress_delta / failure_reason 처리

```python
# L109-110
progress_delta: float = 0.0   # training_labels.progress_delta is hidden
failure_reason: Optional[str] = None  # training_labels.failure_reason is hidden
```
- `TrainingLabels.progress_delta` 미사용 → 0.0 default ✓
- `TrainingLabels.failure_reason` 미사용 → None default ✓

→ **PASS**

### 3.3 metadata leakage guard 코드 흐름

`_check_metadata_for_leakage()` (L31-51):
1. `counterfactual_action_effects` key → `CounterfactualLeakageError` raise (우선순위 1)
2. `FORBIDDEN_AGENT_FIELDS` 포함 key → `HiddenLabelLeakageError` raise
3. `true_` / `oracle_` prefix key → `HiddenLabelLeakageError` raise
4. `EvidenceLikelihood.score()` (L303)에서 모든 hypothesis score 시 호출

→ **PASS** (test_true_control_grammar_not_in_inference_input, test_true_regime_not_in_inference_input, test_counterfactual_table_not_in_inference_input 통과)

---

## 항목 4 — Test Status

### 실행 결과

```
pytest -q tests/test_lr_scorer_stub.py tests/test_h_exec_trace_stub.py tests/test_forbidden_field_mirror_sync.py -ra
```

**결과**: `...........sss.........` `[100%]`
- **20 passed**, **3 skipped**, **0 failed**

### 테스트 목록 및 분류

**test_lr_scorer_stub.py** (11개 통과):
- `test_stub_imports` — Group A
- `test_required_dataclasses_exist` — Group A
- `test_required_component_classes_exist` — Group A
- `test_methods_raise_not_implemented` — Group A
- `test_no_torch_numpy_dependency_in_stub` — Group A
- `test_lr_score_positive_when_alt_explains_evidence_better` — Group C
- `test_lr_score_zero_or_negative_when_exec_explains_evidence_better` — Group C
- `test_all_equal_likelihoods_sets_degenerate_flag` — Group C
- `test_empty_alternatives_blocks_falsification` — Group C
- `test_bce_not_main_path` — Group C
- `test_uncertainty_gate_not_equivalent_to_lr_gate` — Group C

**test_h_exec_trace_stub.py** (3 skip + 7 pass):

*Group B (3 skip):*
| Test Name | Skip 메시지 | 정당성 판단 |
|---|---|---|
| `test_h_exec_trace_has_selected_hypothesis_id` | "Run 4B: implement after ActionRecord.selected_hypothesis_id populated in collector." | **조건부 정당**: `ActionRecord.selected_hypothesis_id` 필드는 이미 존재하고 collector에서 populate됨. 단, "step log에서 실제로 기록됨을 검증"하는 integration 테스트는 step-level log I/O와 persistence metric과의 연결(MET-PERSIST-001)이 필요 — Run 5 dependency 맞음 |
| `test_h_exec_is_predicted_trace_not_oracle_label` | "Run 4B: implement after collector populates is_oracle_label=False invariant." | **조건부 정당**: HypothesisTrace.is_oracle_label=False는 이미 default False. 단, 실제 collector populate 코드의 invariant 강제 검증은 별도 통합 테스트 필요 — Run 5 dependency |
| `test_missing_h_exec_blocks_persistence_metric` | "Run 4B: integrate with actual step log and persistence metric." | **정당**: LR scorer의 degenerate 처리는 구현됨(항목 1.4). 단, 실제 step log와 MET-PERSIST-001 계산기와의 연결은 미구현 — Run 5 dependency 맞음 |

**Group B skip 전환 여부**: Run 4-POST 범위에서 전환 불가. Run 4.6 후속 조치 후보로 기록.

*Group G (7 pass):*
- `test_selected_hypothesis_not_in_forbidden_agent_fields`
- `test_true_control_grammar_not_in_inference_input`
- `test_true_regime_not_in_inference_input`
- `test_counterfactual_table_not_in_inference_input`
- `test_future_evidence_not_available_to_scorer`
- `test_forbidden_field_mirror_sync_still_green`

→ **mirror sync test PASS** ✓

---

## 항목 5 — Smoke Artifact 검증

### p3_lr_smoke/metrics.json

```json
{
  "smoke_type": "direct_synthetic",
  "num_records": 5,
  "planning_calls": 1,
  "f_t_min": -1.5,
  "f_t_max": 1.5,
  "f_t_variance": 1.26,
  "selected_hypothesis_id_null_rate": 0.0,
  "hidden_leakage_count": 0,
  "degenerate_count": 1
}
```

Pass criteria:
- `planning_calls=1 > 0` ✓
- `f_t_variance=1.26 > 0` ✓
- `selected_hypothesis_id_null_rate=0.0 < 1` ✓
- `hidden_leakage_count=0` ✓
- `degenerate_count=1` (기록됨, 정상)

### p3_lr_smoke/manifest.json

- `"P3_LR_EVAL.passed NOT generated"` 문구 존재 ✓
- `git_sha`: `"1f62d87d70e8b8031852a9d258905e0294e08b90"` ✓
- `smoke_type`: `"direct_synthetic"` ✓

### p4_gui_lr_smoke/metrics.json

```json
{
  "smoke_type": "gui_env_synthetic",
  "num_records": 3,
  "hidden_leakage_count": 0,
  "f_t_values": [1.5, 0.0, 0.0],
  "f_t_variance": 0.5,
  "degenerate_count": 2,
  "phase_gate_created": false,
  "gui_lr_integration_status": "PASS"
}
```

Pass criteria:
- `hidden_leakage_count=0` ✓
- `f_t_variance=0.5 > 0` ✓
- `phase_gate_created=false` ✓
- `gui_lr_integration_status=PASS` ✓

`p4_gui_lr_smoke/manifest.json`: **부재** → Run 4.6 후속 조치로 기록 (Run 4-POST에서 생성 금지)

### Phase gate sentinel 상태

현재 `outputs/phase_gates/` 내용:
```
.gitkeep
P1.passed
P1.5.passed
P2.passed
P3.passed
P3_EVAL.passed
P3_EVAL.BLOCKED_planning_calls_zero.md
```

- `P3_LR_EVAL.passed` → **ABSENT** ✓
- `P4_LR_EVAL.passed` → **ABSENT** ✓
- `P4.passed` → **ABSENT** ✓
- 기존 sentinel 전체 보존 ✓

> **중요**: `outputs/runs/p3_lr_smoke/`의 `smoke_type="direct_synthetic"`는 mechanism smoke임.  
> **direct_synthetic smoke ≠ empirical paper evidence**.  
> P3 phase gate 통과 조건인 full evaluation (compute-matched baseline 비교, ABL-022/023 비교, MET-FALSIF-001~004 실측)과 무관하며, 논문 claim의 empirical evidence로 사용 불가.

---

## 항목 6 — Run 5 Readiness

### 현재 상태

**ABLATION_REGISTRY** (12개):
| ID | TDD Ref | Severity |
|---|---|---|
| no_control_grammar | ABL-002 | CRITICAL |
| merged_regime_control_grammar | ABL-003 | CRITICAL |
| collapsed_latent | ABL-006 | CRITICAL |
| no_falsification | ABL-016 | CRITICAL |
| uncertainty_instead_of_falsification | ABL-023 | CRITICAL |
| no_alternative_hypothesis | ABL-024 | CRITICAL |
| random_alternative | ABL-025 | standard |
| no_rollout | ABL-026 | standard |
| no_rewrite | ABL-035 | CRITICAL |
| always_plan_no_gate | ABL-034 | CRITICAL |
| no_progress_reward | ABL-019 | standard |
| no_compute_gate | ABL-033 | CRITICAL |

**Baseline 목록** (9개):
| Class | Baseline ID |
|---|---|
| FrozenBaseAgent | BASE-001 |
| ReactiveAgent | BASE-002 |
| RetryAfterFailureAgent | BASE-003 |
| VerifierOnlyAgent | BASE-005 |
| NextStateWMOnlyAgent | BASE-009 |
| AlwaysPlanAgent | BASE-010 |
| UncertaintyGatedAgent | BASE-012 |
| RandomAlternativePlannerAgent | BASE-014 |
| OracleAgent | BASE-016/017 |

**configs/ablation_core.yaml**: 12 entry ✓ (ABL-002/003/006/016/023/024/025/026/035/034/019/033)

**hard count assertion**: `tests/test_ablation_runner.py` L63-65:
```python
assert set(ABLATION_REGISTRY) == REQUIRED_ABLATION_IDS
assert len(ABLATION_REGISTRY) == 12
```

### Run 5 추가 후보 (구현 금지, 목록만)

**Ablation 추가 후보**:
- `ABL-017`: `no_L_intent_action_mapping` — intent→action mapping 제거
- `ABL-022`: `no_falsification_score_gate` — falsification score threshold gate 제거
- `ABL-036`: `no_counterfactual_target` — counterfactual target 제거
- `ABL-040` (필요 시): 추가 rewrite ablation variant

> **주의**: ABL-023 `bce_classifier_variant`는 현재 registry에서 `uncertainty_instead_of_falsification`가 ABL-023 ref를 사용 중. Run 5에서 `bce_classifier_variant`를 별도 entry로 추가 시 tdd_ref 충돌 회피 방안 사전 설계 필요.

**Baseline 추가 후보**:
- `BASE-015`: compute-matched random reallocation
- `BASE-026`: WAC-style (direct-threat baseline)
- `BASE-027`: CUWM-style (direct-threat baseline)
- `BASE-028`: WebWorld-style (direct-threat baseline)
- CATTS-equivalent
- VLAA-loop-heuristic

### Run 5에서 동시 변경 필요한 파일 목록

| 파일 | 변경 이유 |
|---|---|
| `src/frcgw/evaluation/ablations.py` | registry entry + wrapper class 추가 |
| `src/frcgw/evaluation/baselines.py` | agent class 추가 (BASE-015/026/027/028 등) |
| `tests/test_ablation_runner.py` | `REQUIRED_ABLATION_IDS` 확장 + `len(ABLATION_REGISTRY)` count 갱신 (L63-65) |
| `tests/test_baselines.py` | `AGENT_CASES` expected set 확장 |
| `configs/ablation_core.yaml` | ablation entry 추가 |
| 신규 baseline별 source MD reference | `paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md §7` BASE-026/027/028 인용 |

---

## 항목 7 — Claim Strategy

**원칙**: ALIVE/DEAD 확정 금지. Run 4-POST에서 코드 존재만 확인.

### Claim Strategy 표

| Claim | Run 4-POST 입장 | 아직 부족한 evidence |
|---|---|---|
| **C1** (wrong-grammar persistence) | h_exec trace path 코드 존재 (ActionRecord 4 field + collector populate). C1 primary axis **유지**. | Group B 3 skip 해소, MET-PERSIST-001 구현, persistence_duration 실측, ablation 비교 |
| **C2** (latent disentanglement) | high-risk architecture hypothesis 유지. LR scorer는 latent space를 사용하지 않는 deterministic scorer — C2와 직접 충돌 없음. | ABL-001 collapsed_latent 실 효과 측정, crossed-split 검증, MET-LATENT-001 |
| **C3** (LR falsification) | LR scorer core 14 symbol 구현 완료, F_t 계산 smoke 통과. C3 primary axis **유지**. | ABL-022/023 비교 실험, BASE-005/009/012 비교, MET-FALSIF-001~004 실측, full eval |
| **C4** (hypothesis switch) | supporting. `PosteriorUpdater.switch_recommended` 코드 존재, smoke에서 F_t variance 확인. | rollout_steps 실험, MET-WM-001, MET-ALT-001, BASE-028 WebWorld-style 비교 |
| **C5** (compute gate) | 4-way `DecisionRelevanceGate` 코드 존재, G_t ≠ uncertainty gate 단위 테스트 PASS. C5 primary axis **유지**. | full eval에서 G_t=True rate vs BASE-012, ABL-017 비교, false_planning_call_rate 실측, MET-REWRITE-001 |
| **C6** (compute efficiency) | supporting. G_t ≠ uncertainty gate 케이스 증명 (test_uncertainty_gate_not_equivalent_to_lr_gate PASS). | compute-matched eval, CATTS-equivalent baseline, false_planning_call_rate 실측, progress_per_compute 실측 |

**C1/C3/C5**: primary survival axis — 코드 경로 확인됨, full experiment 대기 중  
**C2**: high-risk — architecture hypothesis, crossed-split 검증 전까지 불확정  
**C4/C6**: supporting — 보조 메커니즘, primary claim 의존적

---

## 검증 체크리스트

| Check | 항목 | 결과 |
|---|---|---|
| **A. File Scope** | 생성 파일 1개(이 보고서)만, 코드 수정 0건, 금지 파일 수정 0건 | **PASS** |
| **B. LR Core** | 14 symbol grep PASS, F_t 코드 흐름 확인, BCE/sigmoid/binary_cross/binary_classifier main-path 0건 (분류 표 작성), degenerate/leakage guard 확인, torch/numpy/pandas/sklearn import 0개 | **PASS** |
| **C. h_exec Trace** | ActionRecord 4 field PASS, h_exec_id 무변경, collector populate source 확인, policy 5개 trace source 표 작성, **OraclePolicy stale trace risk + `_POLICY_INSTANCES` 위험 보고서 명시**, `selected_hypothesis_id` ∉ FORBIDDEN_AGENT_FIELDS PASS | **PASS** |
| **D. Anti-Leakage** | `from_public_step` 허용 접근 목록 작성, training_labels/evaluation_labels/counterfactuals/audit_metadata 미접근 PASS, metadata leakage guard 코드 흐름 확인 | **PASS** |
| **E. Tests** | 20 passed, 3 skipped (Group B — Run 5 dependency, 정당성 판단 기록), 0 failed. mirror sync green | **PASS** |
| **F. Smoke** | p3_lr_smoke pass criteria 전체 확인, p4_gui_lr_smoke pass criteria 확인, manifest 부재 기록, `P3_LR_EVAL.passed`/`P4_*.passed` 부재 확인, direct_synthetic ≠ empirical evidence 명시 | **PASS** |
| **G. Run 5 Readiness** | ablation 12개 / baseline 9개 / config 12 entry 확인, Run 5 추가 후보 목록 작성, 동시 변경 필요 파일 목록 작성 | **PASS** |
| **H. Claim Strategy** | C1/C3/C5 primary axis 유지, C2 high-risk 유지, C4/C6 supporting 유지, ALIVE/DEAD 판정 0건 | **PASS** |
| **I. Forbidden Actions** | paper_context_ref 수정 0건, phase gate sentinel 생성 0건, P3 retraining 0건, baseline·ablation 구현 0건, registry 수정 0건, Codex 호출 0건, fake metric 0건, Run 5 지시문 0건, Group B skip 전환 시도 0건 | **PASS** |
| **J. Final Gate** | A~I 모두 PASS | **PASS** |

---

## 잠재 위험 (Run 4.6 후속 조치 후보)

### 1. OraclePolicy stale trace + `_POLICY_INSTANCES` module cache

- **위험 설명**: `_POLICY_INSTANCES["oracle"]`의 단일 OraclePolicy 인스턴스가 `select()` 내에서 `last_*` field를 설정하지 않음. 결과적으로 모든 oracle 스텝의 `ActionRecord.selected_hypothesis_id = None`. 에피소드 간 인스턴스 재사용 시 reset 없음.
- **현재 오염 경로**: 없음 (각 policy 타입이 별개 인스턴스, select→getattr 순서 보장)
- **미래 위험**: policy instance 공유 방식 변경 시 오염 가능
- **권장 조치**: OraclePolicy에 `last_selected_hypothesis_id = "oracle_best_action_proxy"` 설정 추가, 또는 `_POLICY_INSTANCES` 대신 per-episode 인스턴스 생성 고려
- **우선순위**: Medium (현재 기능 영향 없음, C1 oracle trajectory trace 추적 불가)

### 2. BCE keyword main-path 재검증 결과

- **결과**: PASS. lr_scorer.py 소스 전체 lowercase 스캔 → "sigmoid", "binary_cross", "bce", "binary_classifier" 0건
- **등장 라인 분류**: ABL-022/023 관련 언급은 3개 docstring/주석에만 존재, main-path 로직에 없음
- **위험 없음**: 현재 버전에서 완전히 안전

### 3. Group B 3 skip 즉시 전환 가능성 검토

- `ActionRecord.selected_hypothesis_id` populate는 이미 완료됨 (Run 4B)
- **즉시 전환이 막히는 이유**: skip 메시지가 참조하는 실질적 dependency는 "step log에서 실제 기록 검증 + MET-PERSIST-001 persistence metric 계산기와의 연결"로, 이는 Run 5에서 구현될 full pipeline 통합을 요구함
- **판정**: skip 조건 표현은 구식이나, skip 자체의 정당성은 유지됨. Run 5에서 전환 권장.

### 4. p4_gui_lr_smoke/manifest.json 부재

- `outputs/runs/p4_gui_lr_smoke/manifest.json` 파일 없음
- Run 4-POST에서 생성 금지 (scope 밖)
- **권장 조치**: Run 4.6에서 metrics.json 대비 manifest.json 생성 (run_id, git_sha, seed, smoke_type, lr_scorer_module, timestamp, pass_criteria, notes)

### 5. ABL-023 tdd_ref 중복 위험

- 현재 `uncertainty_instead_of_falsification` → `tdd_ref="ABL-023"` 등록됨
- Run 5 계획에 `bce_classifier_variant` → ABL-023 추가 예정
- tdd_ref가 registry의 unique key가 아니라 참조 필드이므로 기술적으로 중복 가능하나, 혼동 위험 존재
- **권장 조치**: Run 5 진입 전 `paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md §8`에서 ABL-023 정확한 scope 재확인 후 ablation_id 명세

---

## Skipped Tests

| Test Name | Reason | Future Run | Blocking? |
|---|---|---|---|
| `test_h_exec_trace_has_selected_hypothesis_id` | ActionRecord field 존재하나 step log integration + MET-PERSIST-001 연결 미완 | Run 5 | No |
| `test_h_exec_is_predicted_trace_not_oracle_label` | collector populate is_oracle_label=False invariant 통합 검증 미완 | Run 5 | No |
| `test_missing_h_exec_blocks_persistence_metric` | degenerate 처리 구현됨; 실제 step log + persistence metric 계산기 연결 미완 | Run 5 | No |

Priority 1 skip: **0건** ✓

---

## Run 5 준비 요약

| Category | Current State | Needed in Run 5 | Files to Change Later |
|---|---|---|---|
| Ablations | 12 (ABL-002/003/006/016/019/023/024/025/026/033/034/035) | +ABL-017, +ABL-022, +ABL-036 (+ ABL-023 bce_classifier_variant 명세 확인) | `ablations.py`, `test_ablation_runner.py` L63-65 count 갱신, `configs/ablation_core.yaml` |
| Baselines | 9 (BASE-001/002/003/005/009/010/012/014/016/017) | +BASE-015, +BASE-026, +BASE-027, +BASE-028, +CATTS-equivalent, +VLAA-loop-heuristic | `baselines.py`, `test_baselines.py` AGENT_CASES |
| Tests | hard count==12 (`test_ablation_runner.py` L65) | count 갱신 + REQUIRED_ABLATION_IDS 확장 + AGENT_CASES 확장 | `test_ablation_runner.py` L15-28, 63-65 / `test_baselines.py` L22-32 |
| Config | 12 entry (ablation_core.yaml) | 신규 ablation entry 추가, forbidden_fields 미러 확인 | `configs/ablation_core.yaml` |
| Group B skips | 3 skip (Run 5 dependency) | `test_missing_h_exec_blocks_persistence_metric` 등 전환 — MET-PERSIST-001 구현 후 | `tests/test_h_exec_trace_stub.py` Group B |

---

## Claim Status Update

| Claim | Run 4-POST Interpretation | Still Missing | Future Run |
|---|---|---|---|
| C1 | h_exec trace path 코드 확인. selected_hypothesis_id populate 동작 확인 (smoke). Primary axis 유지. | Group B 3 skip 해소, MET-PERSIST-001 구현, full eval with persistence_duration, ablation 비교 | Run 5 |
| C2 | High-risk architecture hypothesis 유지. LR scorer와 충돌 없음 (별도 모듈). | ABL-001 (collapsed_latent) real effect, crossed-split, MET-LATENT-001 | Run 5-6 |
| C3 | LR scorer 14 symbol 존재, F_t 계산 smoke PASS. Primary axis 유지. | ABL-022/023 비교 실험, BASE-005/009/012 비교, MET-FALSIF-001~004 실측 | Run 5 |
| C4 | Supporting. PosteriorUpdater.switch_recommended 코드 존재. | rollout_steps 실험, MET-WM-001, MET-ALT-001, BASE-028 | Run 5-6 |
| C5 | 4-way DecisionRelevanceGate 코드 존재. G_t ≠ uncertainty gate 단위 테스트 PASS. Primary axis 유지. | G_t=True rate vs BASE-012, ABL-017 no_L_intent_action_mapping, MET-REWRITE-001, false_planning_call_rate | Run 5 |
| C6 | Supporting. G_t ≠ uncertainty gate 케이스 증명됨 (unit test level). | compute-matched eval, CATTS-equivalent 비교, false_planning_call_rate 실측, progress_per_compute 실측 | Run 5-6 |

---

## 다음 단계

Run 5에서 해야 할 작업 후보 (우선순위 순):

1. **baseline/ablation registry 확장**: BASE-026/027/028 (direct-threat), BASE-015 (compute-matched), ABL-017/022/036 신규 구현
2. **test count 갱신**: `test_ablation_runner.py` L63-65 hard count assertion 갱신, `test_baselines.py` AGENT_CASES 확장
3. **Group B skip 해소**: step log pipeline + MET-PERSIST-001 구현 후 skip 3개 assertion으로 전환
4. **p4_gui_lr_smoke manifest.json 생성**: Run 4.6 scope
5. **OraclePolicy trace 처리**: oracle trajectory의 hypothesis trace 기록 방식 결정 (Run 4.6 scope)
6. **P3 full evaluation**: compute-matched baseline 비교, ABL 비교, MET-FALSIF-001~004 실측 — P3_LR_EVAL.passed 조건 충족 목표

> **주의**: Run 5 지시문은 이 보고서에 포함하지 않음. Run 5 시작은 별도 사용자 트리거 필요.

---

*검증 완료. Run 4-POST PASS. 코드 수정 0건. Sentinel 생성 0건.*
