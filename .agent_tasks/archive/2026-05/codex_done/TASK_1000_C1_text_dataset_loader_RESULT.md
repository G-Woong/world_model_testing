TASK_NAME: C1_text_dataset_loader
TASK_NUMBER: 1000

Files changed:
- src/frcgw/data/text_dataset.py
- src/frcgw/data/__init__.py
- tests/test_text_dataset.py
- .agent_tasks/codex_done/TASK_1000_C1_text_dataset_loader_RESULT.md

Tests run:
- .\.venv\Scripts\python.exe -m pytest tests/test_text_dataset.py -q

Pass/fail summary:
- PASS: 1 test passed.
- SKIP: 8 tests skipped because data/frcgw_text/v0_1/ is not present in this checkout.
- FAIL: 0 failures, 0 errors.

Blockers:
- The real P2 dataset directory data/frcgw_text/v0_1/ is absent, so dataset-backed tests skip gracefully as required.
