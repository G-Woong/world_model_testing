TASK_NAME: TASK_LFD_007_sequential_detection_metrics

BACKGROUND:
FRCG-WM's LFD evaluation requires sequential detection metrics that are
independent of any proxy heuristic. These metrics quantify:
1. How quickly a detector finds regime switches (detection_delay)
2. How often it raises false alarms on stable segments (false_alarm_rate_per_step)
3. How well-calibrated the run-length posterior is (run_length_posterior_ECE)
4. End-to-end: whether earlier detection causally reduces recovery delay

TASK_LFD_001 adds the core metric functions. This task adds the evaluation
harness that applies them across a full v0_5 episode set, and the AUROC/AUPRC
computation for the binary wrong-hypothesis classifier.

This task runs AFTER TASK_LFD_001 and TASK_LFD_004.

Note: v0_4 episodes have regime_switch_step=None. All metrics gracefully
return None for v0_4 inputs and non-None for v0_5 switch inputs.

GOAL:
1. Add AUROC/AUPRC/F1 for binary wrong-hypothesis detection (proxy-free).
2. Add episode-level metric aggregation across v0_5 eval set.
3. Add recovery delay correlation metric (detection → recovery causal evidence).
4. Add metric output schema (JSON) for comparison with CUSUM/LFD.

FILES_ALLOWED:
- src/frcgw/evaluation/metrics.py
- src/frcgw/evaluation/metric_schema.py  (new file)
- tests/test_detection_metric_schema.py  (new file)

FILES_FORBIDDEN:
- .claude/
- CLAUDE.md
- .mcp.json
- .venv/
- data/
- outputs/
- secrets/
- .env*
- scripts/run_codex_task.ps1
- paper_context_ref/
- src/frcgw/schemas/visibility.py
- src/frcgw/models/
- src/frcgw/objectives/
- src/frcgw/training/

REQUIRED_IMPLEMENTATION:
1. src/frcgw/evaluation/metric_schema.py (new):

   @dataclass
   class DetectorEvalResult:
     detector_name: str
     n_switch_episodes: int
     n_stable_episodes: int
     mean_detection_delay: float | None
     median_detection_delay: float | None
     p90_detection_delay: float | None
     false_alarm_rate_per_step: float
     regime_shift_f1: float
     regime_shift_precision: float
     regime_shift_recall: float
     auroc_wrong_hypothesis: float | None
     auprc_wrong_hypothesis: float | None
     run_length_posterior_ece: float | None
     recovery_delay_pearson_r: float | None
     n_episodes_evaluated: int
     threshold_metadata: dict

2. src/frcgw/evaluation/metrics.py additions:

   def auroc_wrong_hypothesis(
     wrong_prob_scores: list[float],
     true_wrong_hypothesis: list[bool],
   ) -> float:
     """AUROC for binary wrong-hypothesis classifier.
     
     Input: model-predicted scores and eval-only ground truth.
     Both inputs are lists of per-step values across all episodes.
     Uses sklearn.metrics.roc_auc_score if sklearn available, else trapezoidal.
     """
     ...

   def auprc_wrong_hypothesis(
     wrong_prob_scores: list[float],
     true_wrong_hypothesis: list[bool],
   ) -> float:
     """AUPRC (area under precision-recall curve) for wrong-hypothesis detection."""
     ...

   def recovery_delay_correlation(
     detection_delays: list[int],
     recovery_delays: list[int],
   ) -> dict[str, float]:
     """Pearson r and p-value between detection delay and recovery delay.
     
     Per Reviewer-2 MAJOR-5 defense: must show r > 0.3 on OOD split to
     claim detection_delay is task-relevant.
     """
     ...

   def aggregate_episode_metrics(
     episodes: list[dict],
     detector_name: str,
     threshold_metadata: dict,
   ) -> DetectorEvalResult:
     """Aggregate per-episode metrics into DetectorEvalResult."""
     ...

REQUIRED_TESTS:
- tests/test_detection_metric_schema.py:
  - `test_auroc_perfect`: auroc=1.0 for perfect score
  - `test_auroc_random`: auroc ≈ 0.5 for random scores (tol=0.1)
  - `test_auprc_range`: auprc in [0, 1]
  - `test_recovery_delay_correlation_positive`: known correlated input → r > 0.5
  - `test_recovery_delay_correlation_uncorrelated`: random input → |r| < 0.3
  - `test_aggregate_episode_metrics_v0_4_graceful`: v0_4 episodes (no switch) return None delay
  - `test_aggregate_episode_metrics_v0_5_nonzero`: v0_5 episodes return non-None delay
  - `test_detector_eval_result_json_serializable`

ACCEPTANCE_CRITERIA:
- All listed tests pass
- `auroc_wrong_hypothesis` returns 1.0 for perfect classifier
- `aggregate_episode_metrics` correctly handles v0_4 None switch steps
- `DetectorEvalResult` is JSON-serializable (asdict output)
- No forbidden field appears in any metric input path

COMMIT_MESSAGE:
feat(eval): sequential detection metric schema and aggregation harness

Adds AUROC/AUPRC for wrong-hypothesis detection, recovery delay correlation,
DetectorEvalResult schema, and episode-level metric aggregation.

STOP_CONDITION:
STOP if:
1. TASK_LFD_001 not complete (metrics.py base functions must exist)
2. Any forbidden field (true_wrong_hypothesis etc.) used as model INPUT (not eval label)
3. auroc computation reads oracle labels at inference time
4. Any modification to paper_context_ref/ or visibility.py

Dependencies: TASK_LFD_001 (base metric functions), TASK_LFD_004 (v0_5 data)
Checkpoint mapping: PHASE 3 (Checkpoint-3)
