TASK_NAME: TASK_1041_step4_disclosure_trace_ece
TASK_NUMBER: 1048

Files changed:
- src/frcgw/evaluation/frcg_agent.py
- scripts/10_run_lr_real_eval.py
- tests/test_step4_valid_trained_eval.py
- tests/test_step4_trace_writer.py
- tests/test_step4_ece_artifact.py
- .agent_tasks/codex_done/TASK_1048_TASK_1041_RESULT.md

Implementation summary:
- Added TextFRCGModelAgent selected-hypothesis trace state, reset clearing, and grammar argmax/confidence capture during act().
- Added valid_trained_eval disclosure to manifest and preserved existing hard_checks_all_pass logic.
- Propagated selected_hypothesis_id and selected_hypothesis_confidence through _TracingAgent, _attach_trace_records, and per-step JSONL writing.
- Added C5_calibration_status and C5_calibration_audit to metrics payload, blocks C5 ECE when the predictor is degenerate, and writes the Step 4 ECE audit JSON during runner execution.

Tests run:
- .venv\Scripts\python.exe -m pytest tests/test_step4_valid_trained_eval.py -q -> PASSED, 5 passed
- .venv\Scripts\python.exe -m pytest tests/test_step4_trace_writer.py -q -> PASSED, 3 passed
- .venv\Scripts\python.exe -m pytest tests/test_step4_ece_artifact.py -q -> PASSED, 4 passed
- .venv\Scripts\python.exe -m pytest tests/test_lr_real_eval_runner.py -q -> PASSED, 14 passed
- $env:PYTHONPATH='src'; .venv\Scripts\python.exe -m pytest tests/test_frcg_agent.py -q -> PASSED, 11 passed, 1 torch warning

Pass/fail summary:
- Required tests: PASS, 26/26.
- Additional frcg_agent regression: PASS after setting PYTHONPATH=src. An initial extra collection attempt without PYTHONPATH failed with ModuleNotFoundError for frcgw; no code failure.

Blockers:
- None.
