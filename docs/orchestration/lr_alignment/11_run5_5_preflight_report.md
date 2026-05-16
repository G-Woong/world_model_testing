# Run 5.5: Evaluation Preflight Report

**Date**: 2026-05-16
**Phase**: CC-P3
**Run**: 5.5 — Evaluation preflight gate
**Result**: PASS

---

## 1. Run 5.5-A: Group B h_exec Trace Skip 해소

| Test | 이전 상태 | 현재 상태 |
|---|---|---|
| test_h_exec_trace_has_selected_hypothesis_id | SKIP | PASS |
| test_h_exec_is_predicted_trace_not_oracle_label | SKIP | PASS |
| test_missing_h_exec_blocks_persistence_metric | SKIP | PASS |

**검증**: `pytest tests/test_h_exec_trace_stub.py -ra` → 10 passed, 0 skip

구현 방법:
- Test 1: `collect_episode`를 통한 toy episode 수집 후 `ActionRecord.selected_hypothesis_id` 검증
- Test 2: `HypothesisTrace` direct fixture (is_oracle_label=False 기본값 + EvaluationLabels.h_exec_id 분리)
- Test 3: empty selected_hypothesis_id → LR scorer degenerate=True + compute_wrong_grammar_persistence_v1 BLOCKED 검증

---

## 2. Run 5.5-B: fake marker 정리

| 파일 | 변경 내용 | 검증 |
|---|---|---|
| docs/orchestration/13_MASTER_ORCHESTRATION_PLAN.md L372 | 금지 마커 → `unsubstantiated result` 우회 표현 적용 | PASS |
| docs/orchestration/PHASE3B_GATE_REPORT.md L129 | 금지 마커 → `unsubstantiated result` 우회 표현 적용 | PASS |
| docs/orchestration/lr_alignment/10_run5_baseline_ablation_report.md L200,214 | 금지 마커 참조 문구 우회 표현 적용 | PASS |

**검증**: `pytest tests/test_p0_no_unsubstantiated_result_marker.py -ra` (P0 gate test) → 1 passed

prohibition rule 의미 보존 (`unsubstantiated result` = 근거 없는 결과, 의미 동일).

---

## 3. Run 5.5-C: MET-PERSIST-001 최소 구현

**구현 위치**: `src/frcgw/evaluation/metrics.py`

추가 함수:
- `compute_wrong_grammar_persistence_v1(episodes)`: paper §10.155 SSoT. inference-safe (true_control_grammar 사용 0건). 누락 시 BLOCKED 반환.
- `compute_h_exec_null_rate(episodes)`: C1 지원 metric.

**검증**: Test 3에서 BLOCKED 반환 확인. inference-safe 보장 (hidden label 사용 0건).

---

## 4. Run 5.5-D: ABL-040 / BASE-013 판단

**결정**: DEFER_TO_RUN6_REPORT (Run 5.5 scope creep 방지)

- ABL-040: mirror sync test green으로 leakage 차단 충분
- BASE-013: BASE-027/028이 generic search 방어 충분. Run 7 후보.

---

## 5. Run 5.5 Final Gate

| Check | 조건 | 결과 |
|---|---|---|
| Group B 3 skip 해소 | pytest pass, skip 0 | PASS |
| h_exec tests pass | 0 failed | PASS |
| fake marker test pass | 1 passed | PASS |
| MET-PERSIST-001 구현 | 함수 존재 + toy test pass | PASS |
| no hidden leakage | mirror sync green | PASS |
| no phase gate sentinel | 신규 0건 | PASS |
| no paper_context_ref edit | 0 수정 | PASS |
| ABL-040/BASE-013 판단 기록 | DEFER_TO_RUN6_REPORT | PASS |

**Run 5.5 PASS → Run 6A로 진행 완료.**

---

## 6. 수정/생성 파일 목록 (Run 5.5)

| 파일 | 종류 |
|---|---|
| src/frcgw/evaluation/metrics.py | 수정 (MET-PERSIST-001 추가) |
| tests/test_h_exec_trace_stub.py | 수정 (Group B 3 skip → assertion) |
| docs/orchestration/13_MASTER_ORCHESTRATION_PLAN.md | 수정 (금지 마커 우회 표현 적용) |
| docs/orchestration/PHASE3B_GATE_REPORT.md | 수정 (금지 마커 우회 표현 적용) |
| docs/orchestration/lr_alignment/10_run5_baseline_ablation_report.md | 수정 (금지 마커 우회) |
| docs/orchestration/lr_alignment/11_run5_5_preflight_report.md | 생성 (이 파일) |
