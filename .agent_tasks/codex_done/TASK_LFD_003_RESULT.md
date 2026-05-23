# TASK_LFD_003 — RESULT

**Status**: COMPLETE  
**Implemented by**: Claude (Codex fallback)  
**Date**: 2026-05-19  
**Checkpoint**: PHASE 5 (Checkpoint-5 precondition)

## Changes

### src/frcgw/models/falsification_head.py (new)
- `LFDOutput` dataclass: wrong_prob_learned, run_length_posterior, cusum_stat_t
- `FalsificationDetectorHead(h_dim, z_state_dim, max_run_length, effect_input_dim)`:
  - input: h_t + z_state + effect_residual (via effect_encoder) + F_t_deterministic
  - GRUCell for head_h_next carry-over
  - Outputs: sigmoid(wrong_logit), softmax(run_length_logits), cusum_head
  - `_bocpd_run_length_update()`: hazard-weighted soft BOCPD shift
- {0,6} bypass: head receives h_t DIRECTLY (not filtered by falsification.py shortcircuit)
  - falsification_score() preserved unchanged as input feature

### src/frcgw/models/text_frcg_model.py
- `TextFRCGModel.__init__(use_lfd_head=False)`: optional FalsificationDetectorHead
- `ModelOutput.lfd_output: LFDOutput | None = None`
- `forward(effect_scalar, F_t_deterministic, head_h0, return_lfd=False)`: LFD integration
- Default use_lfd_head=False (backward compat)

## Tests
- `tests/test_lfd_head.py`: 10 passed
- `tests/test_bocpd_recursion.py`: 3 passed

## Acceptance Criteria
- ✅ wrong_prob_learned in [0, 1] (sigmoid)
- ✅ run_length_posterior sums to 1 (softmax)
- ✅ Gradient flows to wrong_prob_head and run_length_head
- ✅ wrong_prob changes non-trivially across 5 sequential mismatch steps
- ✅ falsification_score() in planning/falsification.py UNCHANGED
- ✅ Model without LFD head returns lfd_output=None
