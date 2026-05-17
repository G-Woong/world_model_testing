# impl_risk_TASK_1039_R1.md

**Agent**: implementation-risk-critic
**Task**: TASK_1039_step4_counterfactual_rollout (B1)
**Date**: 2026-05-17
**Mode**: T3 pre-audit

## Verdict: NEEDS_FIX (2 HIGH, 1 LOW, 1 consequent)

## Critical Fixes Required

### FIX-1 (HIGH): _simulate_action must call engine.apply()

**Risk**: 현재 TASK spec의 `_simulate_action`은 `engine._rules`에 직접 접근하고
`preconditions` dict를 in-place mutate한다. 이는:
1. 전제조건(precondition) 검사를 우회함 → 충족 불가능한 action이 progress_delta를 받음
2. `is_oracle_best`가 잘못된 값에 기반할 수 있음

**Fix**: `_simulate_action` body를 `engine.apply(preconditions_copy, action_id)` 호출로 교체.
`engine.apply()`는 내부에서 `copy.copy(hidden_state_flags)`를 사용해 새 dict를 반환하므로
원본 `preconditions_copy`는 변경되지 않음.

### FIX-2 (HIGH): source_step_id를 명시적 파라미터로 전달

**Risk**: `TextState`에 `step_id` 속성 없음. `getattr(pre_state, "step_id", str(step_index))`가
항상 fallback → `counterfactual_id`가 episode-non-qualified (`"3_cf_0"` 등).

**Fix**: `generate_counterfactuals()`에 `source_step_id: str` 파라미터 추가.
`_build_counterfactuals` helper에서 `f"{spec.episode_id}_step_{step_index:03d}"` 전달.

### FIX-3 (LOW): CounterfactualRecord import 추가

**Risk**: TASK spec이 "CounterfactualRecord는 이미 collector.py에 import됨"이라 했으나
실제로는 없음. `_build_counterfactuals` return type 사용 시 NameError.

**Fix**: `from frcgw.schemas.step_schema import (...)` 블록에 `CounterfactualRecord` 추가,
또는 type annotation 생략.

### FIX-4 (consequent): _estimate_failure_risk에 pre-apply preconditions 전달

FIX-1 적용 후 자동 해소: `engine.apply()`가 새 dict 반환하므로 원본 `preconditions_copy`
(pre-apply)를 `_estimate_failure_risk`에 안전하게 전달 가능.

## Post-Execution Verification

Codex 결과 검토 시:
1. `_simulate_action`에서 `engine._rules` 직접 접근 없는지 확인
2. `generate_counterfactuals` 시그니처에 `source_step_id` 파라미터 있는지 확인
3. `CounterfactualRecord` import 추가됐는지 확인
4. `test_counterfactual_engine_state_unchanged_after_rollout` 통과 여부 확인
5. `test_counterfactual_failure_risk_in_unit_interval` 통과 여부 확인
