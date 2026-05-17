TASK_NAME: C7_train_smoke
TASK_NUMBER: 1006

Files changed:
- configs/model_text.yaml
- configs/train_text.yaml
- scripts/02_train_text_smoke.py
- src/frcgw/training/__init__.py
- src/frcgw/training/monitoring.py
- src/frcgw/training/train_text.py
- tests/test_train_text_smoke.py
- .agent_tasks/codex_done/TASK_1006_C7_train_smoke_RESULT.md

Tests run:
- .venv\Scripts\python.exe -m pytest tests/test_train_text_smoke.py -q
- .venv\Scripts\python.exe -m pytest tests/ -q

Pass/fail summary:
- Targeted smoke tests: PASS, with 6 data-backed tests skipped because data/frcgw_text/v0_1/manifest.json is not present in this workspace; 2 synthetic tests passed.
- Full test suite: PASS, with dataset-dependent skips and one existing PyTorch nested tensor warning.

Blockers:
- Local P2 dataset directory data/frcgw_text/v0_1 is absent, so the data-backed smoke train tests could not execute in this workspace.
