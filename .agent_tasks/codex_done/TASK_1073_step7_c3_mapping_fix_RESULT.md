TASK_NAME: step7_c3_mapping_fix
TASK_NUMBER: 1073

Files changed:
- src/frcgw/planning/planner.py
- src/frcgw/objectives/losses.py
- src/frcgw/falsification/lr_scorer.py
- tests/test_step7_effect_type_mapping_alignment.py
- tests/test_step7_lr_scorer_public_proxy.py
- tests/test_step7_falsification_nondegenerate.py
- .agent_tasks/codex_done/TASK_1073_step7_c3_mapping_fix_RESULT.md

Tests run:
- .\.venv\Scripts\python.exe -m pytest tests/test_step7_effect_type_mapping_alignment.py -q
  - Failed once at collection because the checkout was not installed and PYTHONPATH was not set.
- $env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest tests/test_step7_effect_type_mapping_alignment.py -q
  - PASS: 16 passed
- $env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest tests/test_step7_lr_scorer_public_proxy.py -q
  - PASS: 8 passed
- $env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest tests/test_step7_falsification_nondegenerate.py -q
  - PASS: 5 passed
- $env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest tests/test_forbidden_field_mirror_sync.py -q
  - PASS: 2 passed, 1 skipped
- $env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest tests/test_visibility_contract.py -q
  - PASS: 17 passed

Acceptance checks:
- git diff -- src/frcgw/schemas/ -> empty
- git diff -- scripts/run_codex_task.ps1 -> empty
- git diff -- src/frcgw/planning/falsification.py -> empty
- git diff -- src/frcgw/text_env/counterfactual_rollout.py -> empty
- EFFECT_TYPE_VOCAB max ID <= 6 verified by test_max_vocab_id_within_model_range.
- Non-trivial v0_3 effect types map outside {0, 6} verified by test_planner_mapping_not_in_short_circuit.

Blockers:
- None.
