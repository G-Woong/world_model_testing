TASK_NAME: TASK_1010_E4_ablations
TASK_NUMBER: 1015

Files changed:
- src/frcgw/evaluation/ablations.py
- src/frcgw/evaluation/__init__.py
- configs/ablation_core.yaml
- scripts/08_run_core_ablations.py
- tests/test_ablation_runner.py
- .agent_tasks/codex_done/TASK_1015_TASK_1010_E4_ablations_RESULT.md

Tests run:
- .\.venv\Scripts\python.exe -m pytest tests/test_ablation_runner.py -q
- git diff --check

Pass/fail summary:
- PASS: 9 targeted ablation tests passed.
- PASS: git diff whitespace check passed.

Blockers:
- None.
