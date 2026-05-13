TASK_NAME: TASK_1009_E3_eval_runner
TASK_NUMBER: 1014

Files changed:
- src/frcgw/evaluation/eval_runner.py
- src/frcgw/evaluation/__init__.py
- configs/eval_text.yaml
- scripts/03_eval_text_smoke.py
- tests/test_eval_runner.py
- .agent_tasks/codex_done/TASK_1014_TASK_1009_E3_eval_runner_RESULT.md

Tests run:
- .\.venv\Scripts\python.exe -m pytest tests/test_eval_runner.py -q
- .\.venv\Scripts\python.exe scripts\03_eval_text_smoke.py --config configs\eval_text.yaml
- rg "null" configs\eval_text.yaml

Pass/fail summary:
- PASS: tests/test_eval_runner.py completed with 7 passed, 0 failed.
- PASS: smoke script completed without NotImplementedError and skipped because data/frcgw_text/v0_1/manifest.json is absent in this worktree.
- PASS: configs/eval_text.yaml contains only model_ckpt: null.

Blockers:
- None.
