TASK_NAME: TASK_LFD_001_cusum_sprt_baseline

BACKGROUND:
FRCG-WM requires statistical baselines for the falsification detection claim.
The Learned Falsification Detector (LFD) must demonstrate improvement over
classical sequential change-point detectors to justify its added complexity.

Two baselines are required:
1. CUSUM (Page 1954): cumulative sum of LLR for effect-type mismatch signal
2. SPRT-style LLR estimator (Wald 1945): sequential log-likelihood ratio

These are NOT threshold-proxy heuristics — they are principled statistical
baselines that must be fairly compared to LFD on the SAME v0_5 evaluation splits.

CRITICAL: To address Reviewer-2 FATAL Attack 1 (CUSUM sufficiency) and
FATAL Attack 3 (circularity), this task must include:
- Grammar-template-level OOD split design (M7 from preflight checkpoint-0)
  equivalent to SPLIT-003 (OOD grammar families unseen during any training)
- CUSUM must be tuned with SAME supervision budget as LFD (no unfair advantage)
- Stateless LFD ablation hook in ablations.py (for later use in PHASE 5)

v0_5 dataset required — this task runs AFTER TASK_LFD_004 completes.

GOAL:
1. Implement CUSUM detector for regime-switch detection on effect-type signal.
2. Implement SPRT-style LLR estimator for falsification scoring.
3. Add sequential detection metrics to metrics.py.
4. Add grammar-template-level OOD split definition in evaluation.
5. Export CUSUM/SPRT as ablation runners in ablations.py.

FILES_ALLOWED:
- src/frcgw/evaluation/metrics.py
- src/frcgw/evaluation/ablations.py
- src/frcgw/evaluation/baseline_detectors.py  (new file)
- tests/test_sequential_detectors.py  (new file)
- tests/test_odc_split.py  (new file)

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
- src/frcgw/objectives/losses.py
- src/frcgw/training/

REQUIRED_IMPLEMENTATION:
1. src/frcgw/evaluation/baseline_detectors.py (new):

   class CUSUMDetector:
     """CUSUM change-point detector (Page 1954) for effect-type mismatch.
     
     Source: E.S. Page (1954). Continuous Inspection Schemes. Biometrika.
     """
     def __init__(self, k: float = 0.5, h: float = 4.0):
       self.k = k  # reference value (allowance)
       self.h = h  # decision interval (threshold)
       self.S_pos: float = 0.0
       self.S_neg: float = 0.0
     
     def update(self, llr: float) -> tuple[float, bool]:
       """Update CUSUM statistic. Returns (S_t, alarm_raised)."""
       ...
     
     def reset(self):
       self.S_pos = 0.0; self.S_neg = 0.0

   class SPRTDetector:
     """SPRT-style log-likelihood ratio estimator (Wald 1945).
     
     Source: Wald, A. (1945). Sequential Tests of Statistical Hypotheses.
     """
     def __init__(self, A: float = 10.0, B: float = 0.1):
       self.A = A  # upper threshold (reject H0)
       self.B = B  # lower threshold (accept H0)
       self.llr: float = 0.0
     
     def update(self, llr_increment: float) -> str:
       """Returns 'continue' | 'reject_H0' | 'accept_H0'."""
       ...
     
     def reset(self):
       self.llr = 0.0

   def compute_effect_llr(
     observed_effect_type: int,
     expected_effect_type: int,
     mismatch_weight: float = 1.0,
   ) -> float:
     """Simple LLR: +mismatch_weight if mismatch, -mismatch_weight/2 if match."""
     ...

2. src/frcgw/evaluation/metrics.py additions:

   def detection_delay(
     switch_step: int,
     alarm_step: int | None,
   ) -> int | None:
     """Steps from switch to alarm. None if no alarm in episode."""
     ...

   def false_alarm_rate_per_step(
     alarm_steps: list[int],
     stable_steps: list[int],
   ) -> float:
     """FAR = alarms on stable steps / total stable steps."""
     ...

   def run_length_posterior_ece(
     run_length_probs: list[list[float]],
     true_run_lengths: list[int],
     n_bins: int = 10,
   ) -> float:
     """ECE for run-length posterior calibration."""
     ...

   def regime_shift_f1(
     predicted_switch_steps: list[int | None],
     true_switch_steps: list[int | None],
     tolerance: int = 2,
   ) -> dict[str, float]:
     """F1, precision, recall for regime switch detection with tolerance window."""
     ...

3. Grammar-template OOD split (metrics.py or ablations.py):
   - ID grammar families: SEARCH_FORM, REQUIRED_DROPDOWN, MODAL_BLOCKER,
     PAGINATION_VS_INF, LOADING_DELAYED, PERMISSION_GATE
   - OOD grammar families: FILTER_ACCORDION, NESTED_SCROLL (already in generator.py)
   - Function: `split_episodes_by_grammar_ood(episodes) -> (id_episodes, ood_episodes)`
   - This function is the SPLIT-003 equivalent for FATAL Attack 3 defense.

4. ablations.py:
   - Add `CUSUMBaselineRunner` and `SPRTBaselineRunner`
   - Each runner: runs detector over v0_5 eval episodes, returns per-episode
     `detection_delay`, `false_alarm_steps`, `alarm_steps`
   - Export: `run_cusum_baseline(episodes, k, h) -> dict[str, any]`
   - Export: `run_sprt_baseline(episodes, A, B) -> dict[str, any]`
   - Each runner reports threshold selection method in metadata

REQUIRED_TESTS:
- tests/test_sequential_detectors.py:
  - `test_cusum_detects_step_change`: inject step-change LLR stream, alarm within 3 steps
  - `test_cusum_stable_far_low`: no alarm on stable LLR stream (FAR < 0.05)
  - `test_sprt_rejects_H0_on_persistent_mismatch`
  - `test_sprt_accepts_H0_on_stable`
  - `test_compute_effect_llr_mismatch_positive`: LLR > 0 for mismatch
  - `test_detection_delay_correct`
  - `test_false_alarm_rate_per_step_zero_for_clean`
  - `test_run_length_posterior_ece_uniform_is_high`
  - `test_regime_shift_f1_perfect`

- tests/test_odc_split.py:
  - `test_odc_split_families_disjoint`: ID and OOD families do not overlap
  - `test_split_episodes_by_grammar_ood_correct_assignment`

ACCEPTANCE_CRITERIA:
- CUSUM detects injected step-change within 3 steps (h=4.0, k=0.5)
- FAR on stable stream (50 steps, no switch) < 0.05 per step
- SPRT correctly classifies 10-step mismatch stream as reject_H0
- All listed tests pass
- `split_episodes_by_grammar_ood` covers both ID and OOD families
- CUSUM/SPRT runner outputs include threshold metadata for fair comparison

COMMIT_MESSAGE:
feat(eval): CUSUM and SPRT baseline detectors + sequential detection metrics

Adds CUSUMDetector, SPRTDetector, detection_delay, false_alarm_rate_per_step,
run_length_posterior_ece, regime_shift_f1, and grammar-template OOD split.
Provides fair comparison floor for LFD (PHASE 5).

STOP_CONDITION:
STOP if:
1. v0_5 dataset not available (depends on TASK_LFD_004)
2. Any modification to paper_context_ref/, .claude/, or visibility.py
3. Thresholds are hand-tuned to beat a future LFD (unfair baseline)
4. `split_episodes_by_grammar_ood` uses inference-time forbidden fields to split

Dependencies: TASK_LFD_004 (v0_5 dataset must exist)
Checkpoint mapping: PHASE 3 (Checkpoint-3)
Required agent review: mathematical-validity-critic, experiment-design-expander
