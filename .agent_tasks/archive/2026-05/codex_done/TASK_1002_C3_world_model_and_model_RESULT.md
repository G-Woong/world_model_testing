TASK_NAME: C3_world_model_and_model
TASK_NUMBER: 1002

Files changed:
- src/frcgw/models/world_model_heads.py
- src/frcgw/models/text_frcg_model.py
- src/frcgw/models/__init__.py
- tests/test_text_frcg_model.py
- .agent_tasks/codex_done/TASK_1002_C3_world_model_and_model_RESULT.md

Tests run:
- .\.venv\Scripts\python -m pytest tests/test_text_frcg_model.py -q
- .\.venv\Scripts\python -m pytest tests/ -q

Pass/fail summary:
- PASS: tests/test_text_frcg_model.py passed all 16 tests.
- PASS: tests/ passed with existing skips and one PyTorch nested tensor warning.

Blockers:
- None.
