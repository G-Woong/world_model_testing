# 22_step5_handoff.md — STEP 5 Handoff Document

작성일: 2026-05-17
선행: STEP 4 `P3_STEP4_EVIDENCE_INTEGRITY.passed` (예정)
branch: `memory-redesign-2026-05-16`

---

## §1. Purpose

이 문서는 STEP 4 완료 후 STEP 5에서 수행해야 할 작업을 이관한다.
STEP 4에서 `IMPLEMENTABLE_CORE` 판정을 받아 구현된 항목(B0~B5)과
STEP 5로 이관된 항목들의 공식 추적 기록이다.

---

## §2. STEP 4 완료 항목 (STEP 5에서 의존 가능)

| 항목 | 설명 | 결과 |
|---|---|---|
| B0 evidence_timestamp semantic fix | `_backfill_episode_timestamps`에 first-wrong-step 기반 evidence_ts 추가 | DONE |
| B0a namespace audit | correct_hypothesis_id vs selected_hypothesis_id → BLOCKED reason 명시 | BLOCKED → STEP 5 |
| B1 counterfactual rollout | `counterfactual_rollout.py` 신규; collector.py L391 패치 | DONE |
| B2 LR comparison report | `audit_step4_lr_comparison.py` compare-only | DONE |
| B3 valid_trained_eval disclosure | manifest에 valid_trained_eval field 추가 | DONE |
| B4 trace writer fix | selected_hypothesis_id/confidence per_step에 emit | DONE |
| B5 ECE degeneracy flag | C5_calibration_status field 추가; degenerate 탐지 | DONE |
| B6 v0_3 dataset | B0+B1 반영한 신규 dataset 생성 | DONE |
| B7 smoke eval | v0_3 test_id + test_ood smoke | DONE |

---

## §3. STEP 5 Task 목록

### §3.1 C4 MET-WM-001 — CRITICAL (T2 claim-metric-alignment 지시사항)

**Task**: `metrics.py`에 `alternative_rollout_fidelity()` (MET-WM-001) 함수 신규 작성
- `CounterfactualRecord.counterfactual_progress_delta`를 소비
- counterfactual rollout fidelity = 예측된 progress_delta vs 실제 outcome 비교
- paper §10 CLAIM-EVAL-004 SSoT 참조
- **Files**: `src/frcgw/evaluation/metrics.py`, `tests/test_step5_rollout_fidelity.py`
- **Priority**: CRITICAL (FC-04 주요 증거; gate 없이는 FC-04 claim 불가)

### §3.2 C2 Regime Split Metric

**Task**: `metrics.py`에 `regime_shift_f1()` (MET-REG-001) 함수 신규 작성
- `eval_runner.py`에 OOD-vs-ID aggregator 추가
- **Files**: `src/frcgw/evaluation/metrics.py`, `src/frcgw/evaluation/eval_runner.py`

### §3.3 LR Scorer Full Active Path 교체

**Task**: B2 comparison report 결과에 따라 full wiring 결정
- `mean_abs_diff < 0.01` → full wiring OK (STEP 5 Task로 진행)
- `mean_abs_diff >= 0.5` → reconcile before any C3 claim
- **Files**: `src/frcgw/evaluation/frcg_agent.py`, `src/frcgw/falsification/lr_scorer.py`

### §3.4 Pre-training Checkpoint

**Task**: `configs/train_text_v0_3.yaml` + short pretraining 실행
- `scripts/07_train.py` — `outputs/checkpoints/pretrain_v0_3/`
- valid_trained_eval=True로 전환; random-init smoke에서 실제 eval로 전환
- **Priority**: HIGH (C1/C3/C5 metric 신뢰도 전제조건)

### §3.5 Calibration Training

**Task**: temperature scaling 또는 isotonic regression
- `src/frcgw/evaluation/calibration.py` 신규
- C5_calibration_status → "OK" (DEGENERATE 해소)

### §3.6 Namespace Alignment — B0a BLOCKED 해소

**Task**: `selected_hypothesis_id` (policy string) ↔ `correct_hypothesis_id` (grammar name) mapping
- mapping table 또는 unified namespace 설계
- compute_wrong_grammar_persistence_v1() BLOCKED 상태 해소
- **Priority**: HIGH (C1 metric 완전 가동을 위한 전제조건)

### §3.7 degenerate_f_t_count Counter Bug Fix

**Task**: `src/frcgw/evaluation/eval_runner.py`의 per-episode `degenerate_f_t_count` rollup 카운터 로직 수정
- 현재: 100% F_t=0.0임에도 degenerate_f_t_count=0 반환
- 수정: F_t==0.0 step 카운트 로직 확인 및 수정

### §3.8 ABL-011/015/040 Ablation 실행 (T2 지시사항)

**Task**: STEP 5에서 `configs/ablation_core.yaml`에 등록된 3개 CRITICAL ablation 실행
- ABL-011 (no-action-effect-log): CLAIM-EVAL-003 falsification claim 검증
- ABL-015 (no L_control_grammar loss): CLAIM-EVAL-001/002 검증
- ABL-040 (leakage sanity probe): synthetic validity foundation 검증
- **Priority**: CRITICAL (reviewer attack defense 필수)

### §3.9 BASE-026/027/028 Direct Threat Baseline 고도화

**현재 상태** (STEP 4 smoke에서 확인됨):
- BASE-026 (`WACStyleConsequenceCorrectionAgent`): heuristic-based **구현 완료** — public consequence 기반, no grammar posterior
- BASE-027 (`CUWMStyleCandidateSimulationAgent`): heuristic-based **구현 완료** — frozen-base candidate comparison, no grammar posterior
- BASE-028 (`WebWorldStyleSearchAgent`): heuristic-based **구현 완료** — next-state heuristic + action search

이들은 paper §7의 direct threat baselines의 **heuristic approximation**이며 실제 WAC/CUWM/WebWorld와 구조적으로 유사하나 grammar posterior를 사용하지 않는 단순화 버전이다.

**Task** (STEP 5): 
- 3개 baseline이 smoke eval에 이미 포함됨 (metrics.json에 BASE-026/027/028 기록)
- 논문 비교를 위해 공개된 WAC/CUWM/WebWorld 알고리즘에 더 충실한 구현으로 고도화 또는 현재 구현이 충분한지 reviewer response 문서화
- **Priority**: MEDIUM (기본 구현 존재, 고도화 우선순위 결정 필요)

### §3.10 h_exec_id Emission Decision

**Task**: `h_exec_id` (hypothesis execution ID) — agent-derived vs generator gap 결정
- 현재: 모든 step에서 None
- STEP 5 설계: 정책 결정 후 emit 또는 계속 None

---

## §4. STEP 5 실행 순서 (권장)

```
1. §3.4 Pre-training checkpoint (모든 metric 신뢰도의 전제조건)
2. §3.6 Namespace alignment (C1 v1 metric unblock)
3. §3.1 C4 MET-WM-001 metric 함수 (FC-04 critical path)
4. §3.3 LR scorer full wiring (B2 comparison 결과 기반 결정)
5. §3.5 Calibration training (C5 DEGENERATE 해소)
6. §3.7 degenerate_f_t_count counter bug fix
7. §3.2 C2 regime split metric
8. §3.8 ABL-011/015/040 ablation 실행
9. §3.9 BASE-026/027/028 baseline 구현
10. §3.10 h_exec_id decision
```

---

## §5. Evidence Card Update Rules

STEP 4 완료 후 evidence card에서:

- C1 `wrong_grammar_persistence`: STEP 3 값(3.0)은 evidence_timestamp 의미 오류 기반 → 폐기
  STEP 4 v0_3 값이 새 기준점; valid_trained_eval=False이므로 "random-init smoke"로만 표기
- C3 F1=0.0: "random-init artifact, STEP 5 pretraining으로 해소 예정"으로 표기
- C4: "counterfactual data generated (v0_3); MET-WM-001 metric deferred to STEP 5"
- C5: ECE=0.025 → "DEGENERATE_PREDICTOR artifact; calibration training in STEP 5"

---

## §6. Cross-references

- `docs/orchestration/lr_alignment/21_step4_execution_plan.md` — STEP 4 계획
- `paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md §7,§8` — baseline/ablation SSoT
- `docs/orchestration/agent_reports/2026-05/claim_metric_alignment_step4_T2_R1.md` — T2 claim audit
- `docs/orchestration/agent_reports/2026-05/experiment_design_step4_T2_R1.md` — T2 experiment audit

---

## §7. STEP 5 Execution Status (2026-05-18 append)

**시작일**: 2026-05-18
**Verdict**: IMPLEMENTABLE_CORE (confidence 0.78)
**실행 계획**: `docs/orchestration/lr_alignment/23_step5_execution_plan.md`

### 진행 상태

| Task | Status | Notes |
|---|---|---|
| T1 Pretraining checkpoint (Codex Task 1) | PENDING | v0_3 config + monitoring.py + tests |
| T2 C4 MET-WM-001 metric (Codex Task 2) | PENDING | alternative_rollout_fidelity() |
| T3 C1 namespace mapping (Codex Task 3) | PENDING | _GRAMMAR_IDX_TO_NAME dict |
| T4 LR reconciliation (Codex Task 4) | PENDING | audit script + degenerate counter fix |
| T5 C5 DEGENERATE 임계 강화 (Codex Task 5) | PENDING | unique<=2 condition |
| T6 ABL-011/015/040 registry (Codex Task 6) | PENDING | ablations.py wiring |
| T7 Trained smoke eval | PENDING | test_id + test_ood (5 ep each) |
| T8 BASE-026/027/028 reviewer doc | PENDING | 24_step5_direct_threat_baseline_report.md |
| T9 STEP 6 handoff doc | PENDING | 25_step6_handoff.md |
| T10 Red-team review (Codex Task 7) | PENDING | read-only review |

### Pre-existing Dirty Files (STEP 5 commit 미포함)
- `.gitignore` (M)
- `.self_evolving_memory/hooks/hook_execution_log.md` (M)
- `docs/orchestration/AGENT_TEAMS_ROLLOUT_PLAN.md` (M)
- `docs/orchestration/session_reports/2026-05/2026-05-17_precompact_handoff.md` (M)
- `plans/PHASE_PROGRESS.md` (M)
- `docs/orchestration/session_reports/2026-05/2026-05-18_precompact_handoff.md` (?? untracked)

### Blockers
- None at STEP 5 start. Training NaN/Inf 시 TRAIN_BLOCKED 상태로 전환.

### Target Sentinel
`outputs/phase_gates/P3_STEP5_TRAINED_EVIDENCE_READY.passed`
