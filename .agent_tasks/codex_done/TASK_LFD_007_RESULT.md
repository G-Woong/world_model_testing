# TASK_LFD_007 — RESULT

**Status**: COMPLETE  
**Implemented by**: Claude (Codex fallback)  
**Date**: 2026-05-19  
**Checkpoint**: PHASE 3 (Checkpoint-3)

## Changes

### src/frcgw/evaluation/metric_schema.py (new)
- `DetectorEvalResult` dataclass: 16 fields, JSON serializable
- n_switch/stable/total_episodes + detection delay (mean/median/p90) + FAR + F1 + AUROC/AUPRC + ECE + Pearson r

### src/frcgw/evaluation/metrics.py (additions)
- `auroc_wrong_hypothesis()`: trapezoidal rule, returns 0.5 for no positives
- `auprc_wrong_hypothesis()`: trapezoidal precision-recall, returns 0.0 for no positives
- `recovery_delay_correlation()`: Pearson r + p_value_approx
- `aggregate_episode_metrics()`: full harness over episode list → DetectorEvalResult

## Tests
- `tests/test_detection_metric_schema.py`: 13 passed

## v0_5 Small Eval (n=20, CUSUM baseline)
| Metric | Value |
|---|---|
| mean_detection_delay | 7.0 steps |
| false_alarm_rate | 0.0 |
| regime_shift_f1 | 0.0 |
| auroc | 1.0 (sim input) |

## Key Finding
CUSUM(h=4.0, k=0.5) in 10-step episodes: alarm after 8 post-switch steps.
switch_step ∈ [2, 8] → most episodes have < 8 post-switch steps → regime_shift_f1=0.
This is the baseline gap LFD must overcome via accumulated h_t evidence.
