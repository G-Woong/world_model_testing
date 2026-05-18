TASK_NAME: TASK_1055_step5_c5_degenerate
SANDBOX_MODE: bypass

BACKGROUND:
STEP 4 found that C5 calibration status incorrectly returned "OK" for random-init model outputs.
The bug is in scripts/10_run_lr_real_eval.py function _compute_c5_calibration_audit() at line ~435:

Current (buggy):
  if variance < 1e-6 and unique_count < 2 and mean_wp == 0.0 and f_t_constant_zero:
      c5_status = C5_DEGENERATE_PREDICTOR

Bug: uses strict AND + `unique_count < 2` (strict less-than).
Random-init case: variance=0.012, unique=2, mean=0.034 — ALL fail the AND conditions → C5_OK (wrong!)

Fix: change to OR logic with corrected unique threshold.
Also need: if valid_trained_eval=False (ckpt=null in config), force DEGENERATE_OR_UNTRAINED status.

GOAL:
1. Fix _compute_c5_calibration_audit() in scripts/10_run_lr_real_eval.py
2. Add DEGENERATE_OR_UNTRAINED status to the manifest when ckpt_path=None
3. Write tests/test_step5_calibration.py (5 tests)

FILES_ALLOWED:
- scripts/10_run_lr_real_eval.py (_compute_c5_calibration_audit change + valid_trained_eval status)
- tests/test_step5_calibration.py

FILES_FORBIDDEN:
- outputs/**
- data/**
- paper_context_ref/**
- src/frcgw/evaluation/metrics.py (active metric function — status flag only; do not change the metric itself)
- src/frcgw/schemas/**
- .claude/**
- scripts/run_codex_task.ps1
- outputs/audits/step4_ece_degenerate_predictor_audit.json (DO NOT OVERWRITE)

REQUIRED_IMPLEMENTATION:

1. In _compute_c5_calibration_audit() at line ~435, change:
   FROM:
     if variance < 1e-6 and unique_count < 2 and mean_wp == 0.0 and f_t_constant_zero:
   TO:
     if (variance < 1e-6) or (unique_count <= 2) or (mean_f_t is not None and mean_f_t < 1e-6):

   Also add a new status constant at the top of the file:
   C5_DEGENERATE_OR_UNTRAINED = "DEGENERATE_OR_UNTRAINED"

2. Add valid_trained_eval gate: in the manifest-writing section, if valid_trained_eval is False
   (i.e., ckpt_path is null for FRCG-LR agent), force c5_status = C5_DEGENERATE_OR_UNTRAINED
   before the payload assignment for C5_calibration_ece.
   Find the manifest-writing section by searching for "valid_trained_eval" in the file.

3. Read the existing C5_DEGENERATE_PREDICTOR constant definition and _build_c5_calibration_audit
   call site to understand the full flow before changing.

4. The C5_AUDIT_FILENAME should remain "step4_ece_degenerate_predictor_audit.json"
   for backward compatibility. STEP 5 runs write to new directories; do not change the filename.

5. tests/test_step5_calibration.py (5 tests):
   - test_unique_2_marked_degenerate(): _compute_c5_calibration_audit with unique_count=2
     (e.g., wrong_probs=[0.034, 0.034, 0.034, ...]) → C5_calibration_status == "DEGENERATE_PREDICTOR"
   - test_random_init_degenerate_or_untrained(): simulate valid_trained_eval=False with random-init
     probs (variance=0.012, unique=2) → status is DEGENERATE_OR_UNTRAINED or DEGENERATE_PREDICTOR
   - test_ok_condition(): _compute_c5_calibration_audit with variance=0.1, unique=8, mean=0.3, f_t mean=0.4
     → C5_calibration_status == "OK"
   - test_abl017_counter_evidence_preserved(): after fix, ABL-017 ablation's C5 status is still
     reported separately (not forcibly DEGENERATE; ABL-017 may have different wrong_probs distribution)
   - test_claim_block_on_degenerate(): when c5_status is DEGENERATE_PREDICTOR, the C5_calibration_ece
     payload key has "status" starting with "BLOCKED" (per existing _blocked() logic)

REQUIRED_TESTS:
pytest tests/test_step5_calibration.py -q
Expected: 5 passed

ACCEPTANCE_CRITERIA:
- 5 tests pass
- unique_count <= 2 (inclusive) triggers DEGENERATE_PREDICTOR
- valid_trained_eval=False triggers DEGENERATE_OR_UNTRAINED
- step4_ece_degenerate_predictor_audit.json is NOT overwritten
- C5_DEGENERATE_OR_UNTRAINED constant added
- OR logic replaces AND logic for DEGENERATE detection

COMMIT_MESSAGE:
feat(step5/task5): C5 DEGENERATE threshold hardening OR logic + DEGENERATE_OR_UNTRAINED

STOP_CONDITION:
Stop if: (1) cannot locate _compute_c5_calibration_audit in the file,
(2) valid_trained_eval field not in manifest path (report BLOCKED — do not guess)
