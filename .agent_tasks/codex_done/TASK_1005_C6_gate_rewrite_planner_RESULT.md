TASK_NAME: C6_gate_rewrite_planner
TASK_NUMBER: 1005

Files changed:
- src/frcgw/planning/decision_gate.py
- src/frcgw/planning/rewrite.py
- src/frcgw/planning/planner.py
- src/frcgw/planning/__init__.py
- tests/test_decision_gate.py
- tests/test_rewrite.py
- .agent_tasks/codex_done/TASK_1005_C6_gate_rewrite_planner_RESULT.md

Tests run:
- .\.venv\Scripts\python.exe -m pytest tests/test_decision_gate.py -q
- .\.venv\Scripts\python.exe -m pytest tests/test_rewrite.py -q
- .\.venv\Scripts\python.exe -m pytest tests/ -q

Pass/fail summary:
- PASS: tests/test_decision_gate.py - 7 passed
- PASS: tests/test_rewrite.py - 8 passed
- PASS: tests/ full suite passed with existing skips and one warning
- PASS: test_uncertainty_alone_does_not_open_hybrid_gate
- PASS: test_planner_assert_fires_on_leakage

Blockers:
- None.
