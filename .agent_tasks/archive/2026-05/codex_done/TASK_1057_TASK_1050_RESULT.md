TASK_NAME: TASK_1050_step5_pretraining_config
TASK_NUMBER: 1057

Files changed:
- configs/train_text_v0_3.yaml
- configs/train_text_v0_3_stage2.yaml
- src/frcgw/training/monitoring.py
- tests/test_step5_pretraining_checkpoint.py
- .agent_tasks/codex_done/TASK_1057_TASK_1050_RESULT.md

Tests run:
- .\.venv\Scripts\python.exe -m pytest tests\test_step5_pretraining_checkpoint.py -q
- .\.venv\Scripts\python.exe -m pytest tests\test_step5_pretraining_checkpoint.py --collect-only -q
- $env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -c "import frcgw.training.train_text; print('train_text import ok')"

Pass/fail summary:
- PASS: targeted STEP 5 test run produced 5 passing tests.
- PASS: collect-only check reported exactly 5 tests.
- PASS: train_text import check succeeded with src on PYTHONPATH.

Blockers:
- None.
