TASK_NAME: step8_c2c5_integrity
SANDBOX_MODE: bypass

BACKGROUND:
FRCG-WM STEP 8. C2 metric: ood_shift_f1 proxy ONLY (no true regime_shift_f1 — requires visibility contract change deferred to STEP 9). C5 metric: ECE (MET-CAL-001) is BLOCKED_DEGENERATE_PREDICTOR until C3 non-degenerate; progress_per_compute is computable. Agent audit (claim_metric_step8_alignment_R1) found: calibration.py NEW must implement BLOCKED_DEGENERATE_PREDICTOR guard programmatically, NOT just by convention.

GOAL:
1. Edit src/frcgw/evaluation/metrics.py: add explicit comment confirming ood_shift_f1 proxy is STEP 8 limit + note that true regime_shift_f1 function is NOT implemented.
2. Create src/frcgw/evaluation/calibration.py: temperature scaling utility with BLOCKED_DEGENERATE_PREDICTOR guard.
3. Create tests/test_step8_regime_shift_f1.py: verify true regime_shift_f1 function does NOT exist in metrics.py.
4. Create tests/test_step8_calibration.py: verify BLOCKED_DEGENERATE_PREDICTOR guard fires correctly.

FILES_ALLOWED:
- src/frcgw/evaluation/metrics.py (Edit: add comment only — no functional change)
- src/frcgw/evaluation/calibration.py (NEW)
- tests/test_step8_regime_shift_f1.py (NEW)
- tests/test_step8_calibration.py (NEW)
- .agent_tasks/codex_done/TASK_1084_step8_c2c5_integrity_RESULT.md

FILES_FORBIDDEN:
- src/frcgw/schemas/visibility.py
- src/frcgw/schemas/step_schema.py
- src/frcgw/evaluation/eval_runner.py (no functional change needed)
- outputs/**
- data/**
- paper_context_ref/**
- .claude/**
- scripts/run_codex_task.ps1
- *.pt

REQUIRED_IMPLEMENTATION:
src/frcgw/evaluation/metrics.py (Edit — comment addition only):
- Near the ood_shift_f1 function definition, add a docstring note (or comment above function):
  "# C2 proxy: ood_shift_f1 uses eval_labels.ood_type as split label.
  # true regime_shift_f1 (MET-OOD-003 faithful) requires true_regime in EvaluationLabels.
  # This is deferred to STEP 9 (R2 lock review required for visibility contract change).
  # DO NOT add a regime_shift_f1 function here in STEP 8."
- NO functional changes to any metric function

src/frcgw/evaluation/calibration.py (NEW):
"""FRCG-WM calibration utilities. C5 ECE (MET-CAL-001).

Source MD: paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md MET-CAL-001
Source MD: paper_context_ref/08_LOSS_REWARD_TRAINING_OBJECTIVE.md C5 calibration
"""
- Constants:
  MIN_UNIQUE_WRONG_PROB = 3  # minimum unique wrong_prob values for ECE to be valid
  BLOCKED_DEGENERATE_PREDICTOR = "BLOCKED_DEGENERATE_PREDICTOR"  # matches eval_runner constant

- Function temperature_scale_probs(probs: list[float], temperature: float) -> list[float]:
  "Apply temperature scaling to predicted probabilities. temperature > 1 softens; < 1 sharpens."
  - Input validation: all probs in [0, 1]; temperature > 0
  - Apply: scaled = [p^(1/T) / sum(q^(1/T) for q in probs) for each p]
  - Return scaled probs

- Function compute_ece_if_valid(
      wrong_probs: list[float],
      true_wrong: list[bool],
      n_bins: int = 10,
  ) -> dict:
  "Compute ECE with BLOCKED_DEGENERATE_PREDICTOR guard.
  
  Returns dict with keys: status, ece, unique_count, n_bins, message.
  status: 'BLOCKED_DEGENERATE_PREDICTOR' | 'OK' | 'INSUFFICIENT_DATA'
  "
  - FIRST: check unique_count = len(set(wrong_probs))
  - If unique_count <= 2: return {status: BLOCKED_DEGENERATE_PREDICTOR, ece: None, unique_count: unique_count, message: f"unique wrong_prob values={unique_count}; minimum required={MIN_UNIQUE_WRONG_PROB}"}
  - If len(wrong_probs) < 10: return {status: "INSUFFICIENT_DATA", ...}
  - Else: compute binned ECE (standard implementation: bin by predicted prob, compute |mean_pred - mean_actual| per bin, weighted average)
  - Return {status: "OK", ece: float, unique_count: unique_count, n_bins: n_bins}
  
- Function check_c3_nondegenerate(c3_status: str) -> bool:
  "Return True only if C3 is non-degenerate (i.e., ECE computation is permitted).
  C3 status must be READY_CANDIDATE or PRELIMINARY_PLUS to unlock C5 ECE.
  "
  BLOCKED_C3_STATUSES = {"BLOCKED", "PIVOT_REQUIRED"}
  return c3_status not in BLOCKED_C3_STATUSES

tests/test_step8_regime_shift_f1.py:
- test_no_regime_shift_f1_function: import metrics; assert NOT hasattr(metrics, "regime_shift_f1") and NOT hasattr(metrics, "compute_regime_shift_f1")
- test_ood_shift_f1_exists: assert hasattr(metrics, "ood_shift_f1") or function is importable
- Both tests must pass

tests/test_step8_calibration.py:
- test_blocked_degenerate_predictor_guard: compute_ece_if_valid([0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5], [True]*10) → status == BLOCKED_DEGENERATE_PREDICTOR (only 1 unique value)
- test_ece_ok_with_diverse_probs: compute_ece_if_valid([0.1, 0.3, 0.5, 0.7, 0.9, 0.2, 0.4, 0.6, 0.8, 0.15], [False, False, True, True, True, False, False, True, True, False]) → status == "OK", ece is float
- test_c3_gate_blocks_degenerate: check_c3_nondegenerate("BLOCKED") == False; check_c3_nondegenerate("READY_CANDIDATE") == True
- test_temperature_scale: temperature_scale_probs([0.3, 0.7], 2.0) → probabilities are floats summing to 1.0
- All 4 tests must pass

REQUIRED_TESTS:
- tests/test_step8_regime_shift_f1.py: both tests green
- tests/test_step8_calibration.py: all 4 tests green
- existing: python -m pytest tests/test_visibility_contract.py tests/test_forbidden_field_mirror_sync.py -q (must stay green)

ACCEPTANCE_CRITERIA:
1. metrics.py has comment confirming no true regime_shift_f1 function exists
2. calibration.py exists with BLOCKED_DEGENERATE_PREDICTOR guard as programmatic check (not just convention)
3. test_no_regime_shift_f1_function passes: metrics module has no regime_shift_f1 function
4. All 4 calibration tests green
5. No schema changes (visibility.py, step_schema.py untouched)

COMMIT_MESSAGE:
feat(step8/task7): C2 proxy guard comment + C5 calibration with degenerate predictor gate

STOP_CONDITION:
Stop if: implementing ECE requires reading true_wrong_hypothesis from agent_observation at inference time (LEAKAGE — BLOCKED). ECE may only use wrong_probs from model output and true_wrong from eval_labels (post-hoc).

RELATED_AGENT_REPORT_IDS: claim_metric_step8_alignment_R1, leakage_step8_v04_baselines_R1
