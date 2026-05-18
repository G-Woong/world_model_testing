TASK_NAME: step8_c3_diagnostics
TASK_NUMBER: 1087

Files changed:
- scripts/10_run_lr_real_eval.py
- scripts/audit_step8_c3_root_cause.py
- tests/test_step8_c3_trace_integrity.py
- .agent_tasks/codex_done/TASK_1087_step8_c3_diagnostics_RESULT.md

Tests run:
- .\.venv\Scripts\python.exe -m pytest tests/test_step8_c3_trace_integrity.py -q
- .\.venv\Scripts\python.exe -m pytest tests/test_lr_real_eval_runner.py tests/test_forbidden_field_mirror_sync.py -q

Pass/fail summary:
- PASS: tests/test_step8_c3_trace_integrity.py (3 passed)
- PASS: tests/test_lr_real_eval_runner.py tests/test_forbidden_field_mirror_sync.py (16 passed, 1 skipped)

Blockers:
- None.
