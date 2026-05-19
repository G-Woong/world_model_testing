TASK_1039 result summary

Files changed:
- src/frcgw/text_env/counterfactual_rollout.py
- src/frcgw/text_env/collector.py
- tests/test_step4_counterfactual_rollout.py
- tests/test_step4_counterfactual_no_leakage.py
- .agent_tasks/codex_done/TASK_1045_TASK_1039_RESULT.md

Tests run:
- PYTHONPATH=src .venv/Scripts/python.exe -m pytest tests/test_step4_counterfactual_rollout.py -q
- PYTHONPATH=src .venv/Scripts/python.exe -m pytest tests/test_step4_counterfactual_no_leakage.py -q
- PYTHONPATH=src .venv/Scripts/python.exe -m pytest tests/test_forbidden_field_mirror_sync.py -q
- PYTHONPATH=src .venv/Scripts/python.exe -m pytest tests/test_step3_no_label_leakage.py -q

Pass/fail summary:
- Rollout tests: 9 passed.
- Counterfactual no-leakage tests: 4 passed.
- Forbidden field mirror guard: 2 passed, 1 skipped.
- Step 3 no-label-leakage guard: 5 passed.
- Initial direct pytest invocation without PYTHONPATH failed at import collection because frcgw was not on sys.path; rerun with PYTHONPATH=src passed.
- data/frcgw_text/v0_1 and data/frcgw_text/v0_2 were absent before/after checks; no data writes occurred.

Blockers:
- None.
