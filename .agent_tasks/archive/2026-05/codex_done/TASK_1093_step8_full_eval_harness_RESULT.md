TASK_NAME: step8_full_eval_harness
TASK_NUMBER: 1093

Files changed:
- scripts/run_step8_full_eval_report.py
- src/frcgw/evaluation/ablations.py
- tests/test_step8_full_eval_report.py
- .agent_tasks/codex_done/TASK_1093_step8_full_eval_harness_RESULT.md

Tests run:
- .\.venv\Scripts\python.exe -m pytest tests/test_step8_full_eval_report.py -q
- $env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest tests/test_step8_full_eval_report.py tests/test_step8_faithful_ablations.py tests/test_forbidden_field_mirror_sync.py -q

Pass/fail summary:
- tests/test_step8_full_eval_report.py: PASS (3 passed)
- Combined required run: PASS (7 passed, 1 skipped)

Blockers:
- None.

Notes:
- The existing required regression pair needs PYTHONPATH=src in this worktree; without it, test collection fails before executing code because frcgw is not importable from the default path.
