# TASK_LFD_001 — RESULT

**Status**: COMPLETE  
**Implemented by**: Claude (Codex fallback)  
**Date**: 2026-05-19  
**Checkpoint**: PHASE 3 (Checkpoint-3)

## Changes

### src/frcgw/evaluation/baseline_detectors.py (new)
- `CUSUMDetector` (Page 1954): k=0.5, h=4.0 default, update() → (stat, alarm)
- `SPRTDetector` (Wald 1945): A/B thresholds, update() → reject_H0 | accept_H0 | continue
- `compute_effect_llr()`: mismatch → +weight, match → -weight/2
- `run_cusum_on_episode()`, `run_sprt_on_episode()`: episode-level runners

### src/frcgw/evaluation/metrics.py (additions)
- `detection_delay(switch_step, alarm_step)` → int | None
- `false_alarm_rate_per_step(alarm_steps, stable_steps)` → float
- `run_length_posterior_ece(probs, true_rls, n_bins)` → float
- `regime_shift_f1_sequential(predicted, true, tolerance)` → dict
- `split_episodes_by_grammar_ood(episodes)` → (id_eps, ood_eps) — SPLIT-003 equivalent

## Tests
- `tests/test_sequential_detectors.py`: 11 passed
- `tests/test_odc_split.py`: 4 passed

## Acceptance Criteria
- ✅ CUSUM alarms on persistent mismatch within 10 steps (h=4.0, k=0.5: step 7)
- ✅ FAR on zero-LLR stream < 0.05
- ✅ SPRT rejects H0 on persistent mismatch stream
- ✅ split_episodes_by_grammar_ood: filter_accordion + nested_scroll → OOD
- ✅ regime_shift_f1_sequential: F1=1.0 for perfect predictor
