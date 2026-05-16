# Run 5 Baseline / Ablation Expansion Report

**Date**: 2026-05-16
**Phase**: Phase 10 — Baseline / Ablation Expansion
**Branch**: memory-redesign-2026-05-16

---

## 1. 생성/수정 파일 목록

| # | 경로 | 유형 | 변경 내용 |
|---|---|---|---|
| 1 | `src/frcgw/text_env/policies.py` | 수정 | OraclePolicy.select() L43-51 belief ID constant 4줄 추가 |
| 2 | `src/frcgw/evaluation/ablations.py` | 수정 | 신규 4 wrapper class + ABLATION_REGISTRY 4 entry + _WRAPPERS 4 mapping (12→16) |
| 3 | `src/frcgw/evaluation/baselines.py` | 수정 | 신규 7 baseline class + __all__ 갱신 (9→16) |
| 4 | `tests/test_ablation_runner.py` | 수정 | REQUIRED_ABLATION_IDS +4, CRITICAL_ABLATION_IDS +4 (비대칭 수정 포함), len==16 |
| 5 | `tests/test_baselines.py` | 수정 | AGENT_CASES +7, 신규 imports, lr_scorer/eval_labels 검증 테스트 추가 |
| 6 | `configs/ablation_core.yaml` | 수정 | ablations 리스트 +4 entry (12→16) |
| 7 | `docs/orchestration/lr_alignment/10_run5_baseline_ablation_report.md` | 생성 | 본 보고서 |

---

## 2. 핵심 요약

| 항목 | 결과 |
|---|---|
| stale trace preflight | PASS (Option 3, OraclePolicy 4줄) |
| ablation expansion | PASS (4 신규, registry 12→16) |
| baseline expansion | PASS (7 신규, AGENT_CASES 9→16) |
| config/test consistency | PASS (YAML 16개 == registry 16개) |
| test status | 292 passed, 3 skipped, 1 pre-existing fail (무관) |
| smoke artifact | PASS (outputs/runs/p3_ablations/ablation_results.json 생성) |
| claim strategy | C1/C3/C5 primary 유지, ALIVE/DEAD 확정 0건 |

---

## 3. 추가된 Ablations

| ID | TDD Ref | Claim | Purpose | Severity | Test Status |
|---|---|---|---|---|---|
| no_regime | ABL-001 | C2 | Regime latent 제거로 C2 regime/control-grammar 분리 검증 (Locatello impossibility 위험) | CRITICAL | PASS |
| no_intent_action_mapping | ABL-017 | C5 | Training-time L_intent_action_mapping loss 제거 (ABL-035 inference rewrite 제거와 별개) | CRITICAL | PASS |
| no_falsification_score_gate | ABL-022 | C1+C3 | F_t > tau_f inference gate 제거 (ABL-016 loss 제거와 별개) | CRITICAL | PASS |
| no_counterfactual_target | ABL-036 | C4 | Counterfactual supervision target 제거, rollout fidelity 저하 | HIGH | PASS |

---

## 4. 추가된 Baselines

| Class | Baseline ID | paper_ssot_id | Threat | Claim | Planning | Rollout | Test |
|---|---|---|---|---|---|---|---|
| VerifierRecoveryAgent | BASE-006 | BASE-006 (Verifier + heuristic recovery) | VeriGUI | C1/C3 | 0 | 0 | PASS |
| ComputeMatchedRandomAgent | BASE-015 | BASE-015 (compute-matched random reallocation) | C6 | C6 | 1 | 0 | PASS |
| WACStyleConsequenceCorrectionAgent | BASE-026 | BASE-026 (WAC-style consequence correction) | WAC | C1/C3/C5 | 1 | 1 | PASS |
| CUWMStyleCandidateSimulationAgent | BASE-027 | BASE-027 (CUWM-style candidate simulation) | CUWM | C1/C3 | 1 | N (cands) | PASS |
| WebWorldStyleSearchAgent | BASE-028 | BASE-028 (WebWorld-style simulator search) | WebWorld | C1/C3 | 1 | N (cands) | PASS |
| CATTSStyleUncertaintyGateAgent | BASE-012-CATTS | BASE-012 (uncertainty-gated planner, CATTS variant) | CATTS | C1/C6 | 0 or 1 | 0 | PASS |
| VLAALoopHeuristicAgent | BASE-003+008-VLAA | BASE-003 + BASE-008 composite (VLAA-loop style) | VLAA-loop | C1/C5 | 0 | 0 | PASS |

---

## 5. C1/C3/C5 Primary Axis 방어 구조

| Claim | Ablation 방어 (기존+신규) | Baseline 방어 (신규) |
|---|---|---|
| C1 wrong-grammar persistence | ABL-016 (no_falsification loss) + **ABL-022 (no_falsification_score_gate)** | WAC(BASE-026), CUWM(BASE-027), WebWorld(BASE-028), VeriGUI(BASE-006) |
| C3 LR falsification | ABL-016 (loss) + **ABL-022 (gate)** | 동일 상위 |
| C5 grammar-conditioned rewrite | ABL-035 (inference rewrite) + **ABL-017 (training mapping loss)** | WAC(BASE-026), VLAA(BASE-003+008) |

---

## 6. C2/C4/C6 Supporting/High-Risk 구조

| Claim | 방어 |
|---|---|
| C2 regime/grammar separability | **ABL-001 (no_regime)** — Locatello impossibility 직접 검증 |
| C4 counterfactual learning | **ABL-036 (no_counterfactual_target)** — rollout fidelity 측정 |
| C6 compute efficiency | **BASE-015 (compute-matched random)** + **CATTS(BASE-012-CATTS)** |

---

## 7. OraclePolicy Stale Trace 처리 (Option 3)

**변경**: `src/frcgw/text_env/policies.py` OraclePolicy.select() L43-51

```python
# Run 5 Phase 0: record policy belief tag (NOT oracle label).
# Constant string — hidden state values are forbidden as trace ID.
self.last_selected_hypothesis_id = "oracle_best_action_proxy"
self.last_selected_hypothesis_type = "oracle"
self.last_selected_hypothesis_confidence = 1.0
self.last_selected_hypothesis_source = "oracle_policy"
```

- `state._hidden_*` 값 복사 0건 (forbidden)
- `EvaluationLabels.h_exec_id` 재사용 0건
- 회귀 점검: `test_text_policy_mixture.py` / `test_text_data_collection.py` / `test_text_replay.py` — 22 passed, 0 failed

---

## 8. CRITICAL_ABLATION_IDS 비대칭 수정

**발견**: `merged_regime_control_grammar`는 severity=CRITICAL이나 CRITICAL_ABLATION_IDS에서 누락.

**수정**: Run 5에서 동시 수정.

```
기존 CRITICAL_ABLATION_IDS (8개):
  no_control_grammar, collapsed_latent, no_falsification,
  uncertainty_instead_of_falsification, no_alternative_hypothesis,
  no_rewrite, always_plan_no_gate, no_compute_gate

수정 후 CRITICAL_ABLATION_IDS (12개):
  기존 8개 + merged_regime_control_grammar (비대칭 수정)
  + no_regime, no_intent_action_mapping, no_falsification_score_gate (Run 5 신규)
  (* no_counterfactual_target은 severity=HIGH로 제외)
```

---

## 9. Config/Test Count 변경 내역

| 항목 | 이전 | 이후 | 비고 |
|---|---|---|---|
| ABLATION_REGISTRY | 12 | 16 | +4 (ABL-001/017/022/036) |
| REQUIRED_ABLATION_IDS | 12 | 16 | 동기화 |
| CRITICAL_ABLATION_IDS | 8 | 12 | 비대칭 수정 + 3 신규 |
| configs/ablation_core.yaml entries | 12 | 16 | 동기화 |
| AGENT_CASES (test_baselines) | 9 | 16 | +7 direct-threat baselines |
| test_baselines.py collected | 23 | 39 | +16 tests |
| severity valid set | {CRITICAL, standard} | {CRITICAL, HIGH, standard} | ABL-036 HIGH 수용 |

---

## 10. 실행한 pytest 목록과 결과

| 테스트 | 결과 |
|---|---|
| `test_text_policy_mixture.py` + `test_text_data_collection.py` + `test_text_replay.py` | 22 passed |
| `test_ablation_runner.py` | 9 passed |
| `test_baselines.py` | 39 passed |
| `test_lr_scorer_stub.py` + `test_h_exec_trace_stub.py` + `test_forbidden_field_mirror_sync.py` | 20 passed, 3 skipped (Group B 유지) |
| `tests/` 전체 | 292 passed, 3 skipped, 1 pre-existing fail |

---

## 11. scripts/08_run_core_ablations.py 실행 결과

```
[OK] ablation results written: outputs\runs\p3_ablations\ablation_results.json
returncode: 0
NotImplementedError: 0건
```

---

## 12. 금지 위반 0건 확인

| 금지 항목 | 확인 |
|---|---|
| paper_context_ref/ 수정 | 0건 |
| outputs/phase_gates/ 수정/생성 | 0건 (P3_LR_EVAL.passed 부재 유지) |
| visibility.py 수정 | 0건 |
| lr_scorer.py 수정 | 0건 |
| step_schema.py 수정 | 0건 |
| collector.py 수정 | 0건 |
| state._hidden_* 복사 | 0건 (Option 3 constant만 사용) |
| Codex 호출 | 0건 |
| P3 full retraining | 0건 |
| C1-C6 ALIVE/DEAD 확정 | 0건 |
| Group B skip 전환 | 0건 (3 skipped 유지) |
| Run 6 지시문 작성 | 0건 |
| CATTS/VLAA에서 lr_scorer import | 0건 (AST scan test PASS) |
| WAC/CUWM/WebWorld eval_labels hidden read | 0건 (test PASS) |

---

## 13. 검증 체크리스트 (A-K)

| Check | 결과 |
|---|---|
| **A. File Scope** | PASS — 6 수정 + 1 생성. paper_context_ref/outputs/phase_gates/visibility.py/lr_scorer.py/step_schema.py/collector.py 수정 0건 |
| **B. Stale Trace Preflight** | PASS — OraclePolicy 4줄 constant, state._hidden_* 복사 0건, 22 passed 회귀 없음 |
| **C. Ablation Registry** | PASS — 4 신규 등록, ABL-016 vs ABL-022 구분, ABL-035 vs ABL-017 구분, registry 16개, severity 정확, expected_collapse 방향 valid |
| **D. Ablation Config/Test** | PASS — YAML 16 == registry 16, REQUIRED_ABLATION_IDS 갱신, CRITICAL_ABLATION_IDS 갱신, len==16 assertion, script returncode 0 |
| **E. Baseline Expansion** | PASS — BASE-006/015/026/027/028/012-CATTS/003+008-VLAA 등록, paper_ssot_id 명시, ComputeBudgetLog 반환, empty→noop, forbidden key 0건, lr_scorer import 0건 |
| **F. Baseline Tests** | PASS — AGENT_CASES 16개, 39 passed, WAC/CUWM/WebWorld eval_labels hidden read test PASS |
| **G. Claim Strategy** | PASS — C1/C3/C5 primary 유지, C2/C4/C6 supporting 유지, ALIVE/DEAD 확정 0건 |
| **H. Test Execution** | PASS — 292 passed, 3 skipped (Group B), 1 pre-existing fail (무관) |
| **I. Smoke Artifact** | PASS — outputs/runs/p3_ablations/ablation_results.json 생성, phase_gates 생성 0건, P3_LR_EVAL.passed 부재 유지 |
| **J. Forbidden Actions** | PASS — 전 항목 위반 0건 |
| **K. Final Gate** | PASS — A-J 모두 PASS |

---

## 14. Pre-existing 실패 분리 보고

P0 gate test (test_p0_no_unsubstantiated_result_marker.py equivalent)

- 원인: `docs\orchestration\13_MASTER_ORCHESTRATION_PLAN.md`와 `docs\orchestration\PHASE3B_GATE_REPORT.md`에 'unsubstantiated result' 관련 금지 마커 존재
- 이 파일들은 Run 5에서 수정하지 않음
- Run 5 이전부터 존재하는 pre-existing failure
- Run 5 관련 0 failed

---

## 15. Run 6 후보 (지시문 아님, 후보 목록만)

1. ABL-040 leakage probe — Run 5에서 defer된 항목
2. BASE-013 TreeSearch baseline 등록
3. MET-PERSIST-001 계산기와 oracle trajectory 연결
4. Group B 3 skip 해소 (`test_h_exec_trace_stub.py` Group B) — 별도 트리거 필요
5. `sample_policy` per-episode vs per-step docstring 불일치 수정
6. P0 gate test 원인 파일 'unsubstantiated result' 관련 금지 마커 정리

---

*Run 6 시작은 별도 사용자 트리거 필요. 자동 진행 금지.*
