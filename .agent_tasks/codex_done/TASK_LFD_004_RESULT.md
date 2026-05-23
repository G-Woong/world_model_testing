# TASK_LFD_004 — RESULT

**Status**: COMPLETE  
**Implemented by**: Claude (Codex fallback — Codex produced empty output x2)  
**Date**: 2026-05-19  
**Checkpoint**: PHASE 2 (Checkpoint-2)

## Changes

### src/frcgw/text_env/state.py
- `TextEpisodeSpec`에 필드 추가:
  - `regime_switch_step: int | None = None` — switch가 발생하는 step 인덱스
  - `hidden_regime_after: str | None = None` — switch 후 regime (eval-only)
- v0_4 default: 둘 다 None (backward compat)

### src/frcgw/schemas/step_schema.py
- `EvaluationLabels`에 필드 추가:
  - `regime_switch_t: int | None = None` — EVALUATION_ONLY + FORBIDDEN_AGENT_FIELDS

### src/frcgw/text_env/generator.py
- `EpisodeSpecGenerator.generate_v0_5()` 메서드 추가
  - switch_step: U[2, max_steps-2] 샘플
  - hidden_regime_after: 다른 TaskFamily 선택
  - ood_type="regime_switch" 설정
- `generate_v0_5_batch(n)` 편의 메서드 추가
- `generate()` 기존 동작 완전 보존

### src/frcgw/text_env/collector.py
- `_backfill_v0_5_switch_labels(steps, regime_switch_step)` 함수 추가
  - regime_switch_step이 None이 아닌 경우 모든 step의 evaluation_labels.regime_switch_t 설정
  - TrainingLabels, PublicObservation에는 절대 기록하지 않음
- `collect_episode()`에 v0_5 post-pass 호출 추가

### src/frcgw/data/text_dataset.py
- `BatchTargets`에 `regime_switch_step: int | None = None` 필드 추가
- `_step_to_sample()`에서 `evaluation_labels.regime_switch_t`로부터 읽음 (eval-only)

## Tests
- `tests/test_v0_5_generator.py`: 6 passed
- `tests/test_v0_5_collector.py`: 5 passed
- `tests/test_forbidden_field_mirror_sync.py`: 3 passed (regime_switch_t in FORBIDDEN_AGENT_FIELDS)

## Acceptance Criteria
- ✅ regime_switch_step in [2, max_steps-2] (v0_5 episodes)
- ✅ hidden_regime != hidden_regime_after
- ✅ v0_4 generate(): regime_switch_step=None (backward compat)
- ✅ regime_switch_t EvaluationLabels에만 존재 (TrainingLabels/PublicObservation에 없음)
- ✅ BatchTargets.regime_switch_step은 evaluation_labels에서 읽음
- ✅ test_forbidden_field_mirror_sync: 3 passed (regime_switch_t 적용됨)
- ✅ pre-existing 실패 3개 (ablation_registry, fake_result_marker, counterfactuals_empty_list)는 내 변경과 무관 (stash 후 동일하게 실패 확인)
