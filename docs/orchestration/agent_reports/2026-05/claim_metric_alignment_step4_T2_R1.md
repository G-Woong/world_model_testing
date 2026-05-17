# claim_metric_alignment_step4_T2_R1.md

**Agent**: claim-metric-alignment-auditor
**Trigger**: T2 (실험설계 변경 전)
**Date**: 2026-05-17
**Scope**: C1/C3/C4/C5 metric wording vs paper §10 SSoT

## Verdict: PARTIALLY_ALIGNED

## Alignment Table

| Claim | Metric | Status | Notes |
|---|---|---|---|
| FC-01 (C1 persistence) | MET-PERSIST-001 | PARTIALLY_ALIGNED | B0a namespace mismatch(correct_hypothesis_id vs selected_hypothesis_id) → compute_wrong_grammar_persistence_v1 BLOCKED. v0 metric (wrong_control_grammar_persistence) unblocked by B0 |
| FC-03 (C3 falsification) | MET-FALS-001/002 | ALIGNED | PR/F1 함수 정합; ECE artifact disclosure 처리 올바름 |
| FC-04 (C4 rollout fidelity) | MET-WM-001 | MISALIGNED | metric 함수 metrics.py에 absent; B1은 데이터만 생성; STEP 5 이관 명시 필요 |
| FC-05 (C5 ECE) | MET-CAL-001 | PARTIALLY_ALIGNED | falsification_calibration() override 없음(GOOD); C5_calibration_status를 metrics.json에도 포함해야 함 |

## Misaligned Items

### FC-04 MET-WM-001 absent (CRITICAL)

metrics.py에 MET-WM-001(alternative_rollout_fidelity) 함수가 없음. B1은 데이터만 unblock.
22_step5_handoff.md에 "C4_rollout_fidelity / MET-WM-001" STEP 5 첫 task로 등록 필수.

→ **PENDING**: 22_step5_handoff.md 작성 시(PHASE G) 반영

### valid_trained_eval 정의식

`valid_trained_eval` 정의: `valid_trained_eval = ckpt_paths_all_provided`
TASK_1041 spec에 명시됨.

### C5_calibration_status 배치

C5_calibration_status → metrics.json AND manifest 둘 다에 기록.
TASK_1041 spec에 명시됨.

## Required Main Claude Actions

1. **즉시**: 22_step5_handoff.md 작성 시 FC-04/MET-WM-001을 STEP 5 Task #1로 등록
2. **즉시**: C1 namespace mismatch (B0a) BLOCKED reason을 22_step5_handoff.md에 "namespace mapping" task로 등록
3. **TASK_1041**: valid_trained_eval = ckpt_paths_all_provided 정의 명시 ✓
4. **TASK_1041**: C5_calibration_status를 metrics.json에 포함 ✓
