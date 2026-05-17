Task: C5_falsification_alt_proposer

Files changed:
- src/frcgw/planning/falsification.py
- src/frcgw/planning/alternative_proposer.py
- src/frcgw/planning/__init__.py
- tests/test_falsification.py
- .agent_tasks/codex_done/TASK_1004_C5_falsification_alt_proposer_RESULT.md

Tests run:
- .\.venv\Scripts\python.exe -m pytest tests/test_falsification.py -q
- .\.venv\Scripts\python.exe -m pytest tests/ -q

Pass/fail summary:
- Targeted falsification tests: PASS, 9 passed.
- Full test suite: PASS, with existing skips and one PyTorch nested tensor warning.

Blockers:
- None.
