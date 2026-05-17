# experiment_design_step4_T2_R1.md

**Agent**: experiment-design-expander
**Trigger**: T2 (실험설계 변경 전)
**Date**: 2026-05-17
**Scope**: STEP 4 B0~B5 블로커 + 37-test 계획 감사

## Verdict: INCOMPLETE_CRITICAL

## Critical Findings

### ABL-011/015/040 미등록 (CRITICAL)

`configs/ablation_core.yaml`에 다음 3개 CRITICAL ablation이 미등록:
- **ABL-011** (no-action-effect-log): CLAIM-EVAL-003 falsification novelty claim의 핵심 증거 경로
- **ABL-015** (no L_control_grammar loss): CLAIM-EVAL-001/002와 직결; ABL-017과 별개 항목
- **ABL-040** (leakage sanity probe): synthetic validity 전체의 foundation

→ **RESOLVED (2026-05-17)**: Main Claude가 ablation_core.yaml에 3개 항목 추가 완료.

### BASE-026/027/028 이관 경로 미기록

21_step4_execution_plan.md에 direct threat baseline(BASE-026 WAC, BASE-027 CUWM, BASE-028 WebWorld) 언급 없음. 이관 경로 문서화 필요.

### 기타 WARN 항목

- B3(valid_trained_eval)과 BASE-015(compute-matched) 혼동 위험: 의미론적으로 다른 레이어
- test_step4_counterfactual_no_leakage.py에 `FORBIDDEN_AGENT_FIELDS unchanged` assertion 추가 권장
- audit_step4_lr_comparison.py의 lr_scorer import side-effect 처리 조건 acceptance criteria 명시 필요

## Test Coverage Check

| Blocker | Test File | Count | Status |
|---|---|---|---|
| B0 | test_step4_evidence_timestamp.py | 8 | 1:1 |
| B1 | test_step4_counterfactual_rollout.py + no_leakage.py | 9+4 | 1:1 |
| B2 | test_step4_lr_comparison.py | 4 | 1:1 |
| B3 | test_step4_valid_trained_eval.py | 5 | 1:1 |
| B4 | test_step4_trace_writer.py | 3 | 1:1 |
| B5 | test_step4_ece_artifact.py | 4 | 1:1 |
| Total | — | 37 | MATCH |

## PASS Conditions (minimum to clear INCOMPLETE_CRITICAL)

1. ~~ablation_core.yaml에 ABL-011/015/040 추가~~ → DONE
2. 21_step4_execution_plan.md에 BASE-026/027/028 STEP 5 이관 명시 → PENDING
