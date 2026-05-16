# Run 4 완료 보고

**Date**: 2026-05-16  
**Phase**: 8/9 (LR Core + h_exec Smoke)  
**Branch**: memory-redesign-2026-05-16

---

## 생성/수정 파일

**생성 (4개 필수 + 3개 조건부)**:
- `src/frcgw/falsification/__init__.py` — package 등록 (import path 문제 해소)
- `src/frcgw/falsification/lr_scorer.py` — 14 symbol 실제 구현 (Phase 8)
- `src/frcgw/gui_env/lr_integration.py` — GUI-LR smoke adapter (4C)
- `outputs/runs/p3_lr_smoke/metrics.json` — direct synthetic smoke artifact
- `outputs/runs/p3_lr_smoke/manifest.json` — run manifest
- `outputs/runs/p4_gui_lr_smoke/metrics.json` — GUI smoke artifact
- `docs/orchestration/lr_alignment/08_run4_implementation_report.md` — 본 보고서

**수정 (5개)**:
- `tests/test_lr_scorer_stub.py` — Priority 1 11개 테스트 실 assertion 전환
- `tests/test_h_exec_trace_stub.py` — Priority 1 5개 테스트 실 assertion 전환 (4개 skip 유지)
- `src/frcgw/schemas/step_schema.py` — ActionRecord 4 optional field 추가
- `src/frcgw/text_env/policies.py` — hypothesis tracking hook 추가
- `src/frcgw/text_env/collector.py` — ActionRecord.selected_hypothesis_id populate

**불변 (수정 금지 확인)**:
- `src/frcgw/schemas/visibility.py` ✓ 무변경
- `src/frcgw/planning/falsification.py` ✓ 무변경
- `paper_context_ref/` 전체 ✓ 무변경
- `outputs/phase_gates/` 전체 ✓ 무변경 (P3_LR_EVAL.passed 미생성)
- `src/frcgw/evaluation/ablations.py` / `baselines.py` ✓ 무변경

---

## 핵심 요약

- **LR core status**: PASS — 14 symbol 구현, standard library only, torch/numpy/pandas/sklearn 0개
- **h_exec trace status**: PASS — ActionRecord 4 optional field 추가, policies.py hook, collector.py populate
- **EvidenceFeatures anti-leakage status**: PASS — from_public_step hidden 필드 미접근, metadata leakage guard 작동
- **Unit test status**: PASS — Priority 1 16개 real assertion PASS (11개 + 5개), 3개 skip 유지
- **Text-only smoke status**: PASS — planning_calls=1 > 0, F_t_variance=1.26 > 0, leakage=0
- **GUI integration status**: PASS — gui_env/lr_integration.py, smoke hidden_leakage=0
- **Primary survival axis impact**: C1/C3/C5 mechanism code 존재 확인됨

---

## Run 4A 요약

### lr_scorer.py

- 14 symbol (9 dataclass + 5 component class) 표준 라이브러리만으로 구현
- `EvidenceFeatures.from_public_step(step)` classmethod 추가 — public 필드만 접근
- `_check_metadata_for_leakage()` — metadata key에 FORBIDDEN_AGENT_FIELDS / true_*/oracle_* prefix → HiddenLabelLeakageError or CounterfactualLeakageError raise

### F_t implementation

```
F_t = max_{h_alt in alt_likelihoods} [ell(h_alt) - ell(h_exec)]
```

- EvidenceLikelihood: deterministic scoring (+1.0 effect_type match, +0.5 no_effect_flag, +0.5 precondition, +0.5 progress direction sign, *0.5 noisy)
- Edge cases: h_exec missing → degenerate, alt empty → degenerate, all equal → degenerate

### BCE main path exclusion

- lr_scorer.py 소스 전체에 "sigmoid", "binary_cross", "bce", "binary_classifier" 키워드 0개 확인
- `test_bce_not_main_path` PASS

### Priority tests

- `tests/test_lr_scorer_stub.py`: 11개 → 전부 PASS
- `tests/test_h_exec_trace_stub.py`: 5개 → 전부 PASS, 4개 skip 유지
- `tests/test_forbidden_field_mirror_sync.py`: green 유지

---

## Run 4B 요약

### selected_hypothesis_id 위치

```python
# src/frcgw/schemas/step_schema.py — ActionRecord
selected_hypothesis_id: str | None = None
selected_hypothesis_type: str | None = None
selected_hypothesis_confidence: float | None = None
selected_hypothesis_source: str | None = None
```

### EvaluationLabels.h_exec_id 재사용 여부

- **재사용 안 함** — EvaluationLabels.h_exec_id는 무변경 (oracle-aligned, EVALUATION_ONLY bucket)
- ActionRecord.selected_hypothesis_id는 policy가 스스로 기록하는 predicted trace

### public-only EvidenceFeatures

- `from_public_step`: step.observed_effect_public (effect_type, dom_diff_public, text_diff_public)만 접근
- training_labels / evaluation_labels / counterfactuals / audit_metadata 미접근
- progress_delta=0.0, failure_reason=None (hidden → 0/None default)

### planning_calls, F_t variance, smoke artifact

| 항목 | 값 |
|---|---|
| smoke_type | direct_synthetic |
| num_records | 5 |
| planning_calls | 1 |
| f_t_min | -1.5 |
| f_t_max | 1.5 |
| f_t_variance | 1.26 |
| selected_hypothesis_id_null_rate | 0.0 |
| hidden_leakage_count | 0 |
| degenerate_count | 1 |

Pass criteria: planning_calls > 0 ✓, f_t_variance > 0 ✓, leakage = 0 ✓

---

## Run 4C 요약

### GUI integration

- `src/frcgw/gui_env/lr_integration.py` 생성
- `gui_lr_smoke(obs)` — GUIObservation → EvidenceFeatures → LR score 1회
- `_assert_gui_obs_safe()` — FORBIDDEN_GUI_AGENT_FIELDS 점검
- `evidence_from_gui_obs()` — effect_description → effect_type 파생 (hidden label 미접근)

GUI smoke 결과 (`outputs/runs/p4_gui_lr_smoke/metrics.json`):
| 항목 | 값 |
|---|---|
| num_records | 3 |
| hidden_leakage_count | 0 |
| f_t_variance | 0.5 |
| gui_lr_integration_status | PASS |

DEFERRED 없음 — 기존 GUIObservation 공개 필드 구조가 충분히 명확함.

---

## C1/C3/C5 생존 경로 업데이트

| Claim | Run 4 Contribution | Still Missing | Future Run |
|---|---|---|---|
| C1 (wrong-grammar persistence) | selected_hypothesis_id이 ActionRecord에 존재, policy에서 populate됨 → MET-PERSIST-001 계산 가능 경로 확보 | text_env 실제 training + h_exec vs h_true 비교 metric | Run 5 |
| C3 (LR falsification) | LikelihoodRatioFalsificationScorer 구현, F_t > 0 케이스 smoke 확인, PosteriorUpdater + DecisionRelevanceGate 작동 | compute-matched baseline(ABL-022/023) 비교, full ablation | Run 5/6 |
| C5 (compute gate) | DecisionRelevanceGate 4-way conjunction 구현, uncertainty gate ≠ G_t 테스트 확인 | Full eval에서 G_t=True episode rate vs BASE-012 비교 | Run 6 |

---

## C2/C4/C6 상태

| Claim | Position | Run 4 Handling | Future Evidence |
|---|---|---|---|
| C2 (latent disentanglement) | high-risk architecture hypothesis | lr_scorer.py와 충돌 없음. latent 구조 미구현 | Run 5 (frozen VLM phase) |
| C4 (hypothesis switch) | supporting mechanism | PosteriorUpdater.switch_recommended 구현됨, smoke에서 작동 확인 | Run 5 text_env full run |
| C6 (compute efficiency) | supporting efficiency | G_t ≠ uncertainty gate 단위 테스트 PASS | Run 6 compute-matched eval |

---

## 검증 체크리스트

| Check | 결과 | 상세 |
|---|---|---|
| A. File Scope | PASS | paper_context_ref/outputs/phase_gates/visibility.py/ablations.py/baselines.py 0개 변경. 허용 범위 파일만 수정 |
| B. LR Core | PASS | py_compile OK. 14 symbol grep 확인. "sigmoid"/"binary_cross"/"bce"/"binary_classifier" 0개. torch/numpy/pandas/sklearn import 0개 |
| C. h_exec Trace | PASS | ActionRecord 4 optional field 추가. EvaluationLabels.h_exec_id 무변경. selected_hypothesis_id ∉ FORBIDDEN_AGENT_FIELDS |
| D. Anti-Leakage | PASS | from_public_step: training_labels/evaluation_labels/counterfactuals/audit_metadata 미접근. metadata 내 true_*/oracle_*/forbidden key → raise |
| E. Unit Tests | PASS | pytest -q target tests: 37 passed, 3 skipped. test_forbidden_field_mirror_sync.py green |
| F. Text-only Smoke | PASS | outputs/runs/p3_lr_smoke/metrics.json 존재. planning_calls=1>0. f_t_variance=1.26>0. leakage=0. P3_LR_EVAL.passed 미생성 |
| G. GUI Integration | PASS | outputs/runs/p4_gui_lr_smoke/metrics.json 존재. hidden_leakage=0. 위상 게이트 sentinel 없음 |
| H. Claim Strategy | PASS | C1/C3/C5 primary axis 유지. C2/C4/C6 supporting/high-risk 유지. ALIVE/DEAD 0건 |
| I. Forbidden Actions | PASS | paper_context_ref 수정 0/phase gate 생성 0/P3 retraining 0/baseline·ablation 추가 0/Codex 호출 0/fake metric 0 |
| J. Final Gate | PASS | A~G + H + I 전부 PASS |

---

## 다음 Run에서 해야 할 일

- text_env full episode 수집 (selected_hypothesis_id populate 검증)
- MET-PERSIST-001 metric 계산 구현 (h_exec_id populate 확인)
- ABL-022/023 (log-ratio ablation 비교 variant) 구현
- P3 gate 재평가 — planning_calls > 0 경로 확보됨, full retrain 조건 검토
- test_h_exec_trace_has_selected_hypothesis_id (Group B 4개 skip → 실 assertion 전환)

Run 5 시작은 **별도 사용자 트리거 필요**. 자동 진행 금지.
