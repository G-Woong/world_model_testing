TASK_NAME: C4_objectives
TASK_NUMBER: 1003

Files changed:
- src/frcgw/objectives/losses.py
- src/frcgw/objectives/rewards.py
- src/frcgw/objectives/__init__.py
- tests/test_losses.py
- .agent_tasks/codex_done/TASK_1003_C4_objectives_RESULT.md

Tests run:
- .\.venv\Scripts\python.exe -m pytest tests/test_losses.py -q
- .\.venv\Scripts\python.exe -m pytest tests/ -q

Pass/fail summary:
- tests/test_losses.py: PASS, 8 passed
- tests/: PASS, full suite passed with existing skips and one PyTorch nested tensor warning

Blockers:
- None
