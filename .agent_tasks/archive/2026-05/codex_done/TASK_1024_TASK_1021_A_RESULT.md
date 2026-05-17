TASK_NAME: TASK_1021_A_gui_env_data_integrity_scaffold

Files changed:
- src/frcgw/gui_env/__init__.py
- src/frcgw/gui_env/task_spec.py
- src/frcgw/gui_env/event_schema.py
- src/frcgw/gui_env/replay_validator.py
- src/frcgw/gui_env/leakage_audit.py
- tests/test_gui_env_schema.py
- tests/test_gui_env_leakage.py
- tests/test_gui_env_replay_determinism.py
- .agent_tasks/codex_done/TASK_1024_TASK_1021_A_RESULT.md

Tests run:
- $env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest tests/test_gui_env_schema.py tests/test_gui_env_leakage.py tests/test_gui_env_replay_determinism.py

Pass/fail summary:
- PASS: 12 passed in 0.07s.
- Initial collection without PYTHONPATH failed because the src-layout package was not installed into the venv; rerun used PYTHONPATH=src and passed.

Blockers:
- None.
