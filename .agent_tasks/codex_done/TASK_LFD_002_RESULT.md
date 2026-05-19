# TASK_LFD_002 — RESULT

**Status**: COMPLETE  
**Implemented by**: Claude (Codex fallback — Codex produced empty output x2)  
**Date**: 2026-05-19  
**Checkpoint**: PHASE 4 (Checkpoint-4)

## Changes

### src/frcgw/models/encoders.py
- `HistoryEncoder.forward` 서명 변경: `h0: Tensor | None = None`, `return_hidden: bool = False` 파라미터 추가
- `return_hidden=False` (default): 기존과 동일한 `Tensor` 반환 (v0_4 backward compat)
- `return_hidden=True`: `(Tensor, h_t_next)` 튜플 반환
- `gru_out, h_t_next = self.gru(step_features, h0)` — h0 전달 지원

### src/frcgw/models/text_frcg_model.py
- `ModelOutput`에 `h_t_next: Tensor | None = None` 필드 추가
- `TextFRCGModel.forward(h_t: Tensor | None = None)` 파라미터 추가
- h_t 전달 시 `return_hidden=True`로 history_encoder 호출 → `h_t_next` ModelOutput에 반환
- Default: h_t=None (기존 동작 완전 보존)

## Tests
- `tests/test_persistent_ht.py`: 4 passed (carry-over, reset, shape, nonzero)
- `tests/test_encoder_backward_compat.py`: 5 passed (tuple, Tensor, h0=None 동등성, ModelOutput)

## Acceptance Criteria
- ✅ return_hidden=False path: 기존 Tensor 반환 (backward compat)
- ✅ return_hidden=True path: tuple(Tensor, Tensor) 반환
- ✅ h_t carry-over로 다른 출력 생성 (test_h_t_carry_over_changes_output)
- ✅ h_t reset=None → fresh episode 재현 (test_h_t_episode_reset_to_none)
- ✅ No existing test broken
- ✅ test_forbidden_field_mirror_sync: 3 passed
