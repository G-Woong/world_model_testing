TASK_NAME: TASK_1055_step5_c5_degenerate
TASK_NUMBER: 1060

Files changed:
- scripts/10_run_lr_real_eval.py
- tests/test_step5_calibration.py
- .agent_tasks/codex_done/TASK_1060_TASK_1055_RESULT.md

Tests run:
- .\.venv\Scripts\python.exe -m pytest tests/test_step5_calibration.py -q

Pass/fail summary:
- PASS: 5 passed

Blockers:
- None

Notes:
- C5 audit filename remains step4_ece_degenerate_predictor_audit.json.
- outputs/audits/step4_ece_degenerate_predictor_audit.json was not overwritten.
