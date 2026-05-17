TASK_1044 / TASK_1038 RESULT

Files changed:
- src/frcgw/text_env/collector.py
- tests/test_step4_evidence_timestamp.py
- .agent_tasks/codex_done/TASK_1044_TASK_1038_RESULT.md

Tests run:
- .\.venv\Scripts\python.exe -m pytest tests/test_step4_evidence_timestamp.py -q
  - FAIL: collection failed with ModuleNotFoundError: No module named 'frcgw' because the venv does not have the src package installed and PYTHONPATH was not set.
- $env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest tests/test_step4_evidence_timestamp.py -q
  - PASS: 8 passed.
- $env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest tests/test_forbidden_field_mirror_sync.py -q
  - PASS: 2 passed, 1 skipped.
- $env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest tests/test_forbidden_field_mirror_sync.py tests/test_step3_dataset_backfill.py -q
  - FAIL: 6 dataset-backed tests failed because data/frcgw_text/v0_2 train/test_id JSONL files and manifest.json are absent; the remaining tests in that command passed or skipped.

Pass/fail summary:
- Required Step 4 evidence timestamp tests passed: 8/8.
- _backfill_episode_timestamps now backfills evidence_timestamp to the first episode step whose true_wrong_hypothesis is True, or None when no such step exists.
- No data/frcgw_text/v0_1 or data/frcgw_text/v0_2 files were modified; those directories are absent in this worktree.

Blockers:
- tests/test_step3_dataset_backfill.py cannot fully pass in this worktree without the missing generated data/frcgw_text/v0_2 dataset files. data/ is forbidden for this task, so no dataset generation or repair was attempted.
