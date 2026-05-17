TASK_NAME: STEP3_coverage_audit

BACKGROUND:
STEP 2 real eval runner (scripts/10_run_lr_real_eval.py) has 66 BLOCKED markers
because 6 metrics cannot be computed. The root cause is that the v0.1 dataset
(data/frcgw_text/v0_1/) is missing key evaluation label fields:
- hypothesis_update_timestamp (0/1002 present)
- recovery_timestamp (0/1002 present)
- selected_hypothesis_confidence (0/1002 present)
- ood_type (absent, test_ood.jsonl doesn't exist)

STEP 3 will regenerate the dataset as v0.2 with these fields populated.
Task 1 (this task) creates a coverage audit script that measures field coverage
BEFORE (v0.1) and AFTER (v0.2) dataset regeneration.

Key source files:
- data/frcgw_text/v0_1/ -- existing dataset structure
- src/frcgw/schemas/step_schema.py -- EvaluationLabels, ActionRecord schema
- docs/orchestration/lr_alignment/19_step3_dataset_backfill_plan.md -- plan

Scientific contract: paper_context_ref/06_DATA_SCHEMA_AND_LABELING.md (read-only reference).

GOAL:
Create scripts/audit_step3_dataset_coverage.py with:
1. CLI: --data-root PATH --out PATH.json [--split {train,valid,test_id,test_ood,all}]
2. Reads all .jsonl files under data-root
3. For each of these fields, counts how many steps have a non-null value:
   - eval_labels.hypothesis_update_timestamp
   - eval_labels.recovery_timestamp
   - eval_labels.ood_type
   - action.selected_hypothesis_confidence
   - eval_labels.true_wrong_hypothesis
4. Outputs a JSON report with structure:
   {
     "data_root": "...",
     "total_steps": N,
     "total_episodes": M,
     "splits_found": ["train", "valid", "test_id"],
     "field_coverage": {
       "hypothesis_update_timestamp": {"present": K, "total": N, "ratio": K/N},
       "recovery_timestamp": {...},
       "ood_type": {...},
       "selected_hypothesis_confidence": {...},
       "true_wrong_hypothesis": {...}
     }
   }
5. Prints a human-readable summary to stdout

Also create tests/test_step3_dataset_coverage_audit.py with 5 tests:
1. test_audit_reports_zero_for_missing_hypothesis_update_timestamp
2. test_audit_reports_zero_for_missing_recovery_timestamp
3. test_audit_reports_zero_for_missing_selected_hypothesis_confidence
4. test_audit_reports_correct_coverage_for_populated_synthetic
5. test_audit_emits_json_with_expected_keys

FILES_ALLOWED:
- scripts/audit_step3_dataset_coverage.py
- tests/test_step3_dataset_coverage_audit.py

FILES_FORBIDDEN:
- .claude/
- CLAUDE.md
- .mcp.json
- .venv/
- data/frcgw_text/v0_1/
- data/frcgw_text/v0_2/
- outputs/
- secrets/
- .env*
- scripts/run_codex_task.ps1
- paper_context_ref/
- src/frcgw/schemas/visibility.py
- src/frcgw/evaluation/eval_runner.py
- src/frcgw/evaluation/metrics.py
- src/frcgw/evaluation/baselines.py
- src/frcgw/evaluation/frcg_agent.py
- src/frcgw/text_env/collector.py
- scripts/09_run_lr_eval.py
- scripts/10_run_lr_real_eval.py
- configs/lr_eval_core.yaml
- configs/lr_eval_real.yaml
- .gitignore
- .self_evolving_memory/hooks/hook_execution_log.md
- docs/orchestration/AGENT_TEAMS_ROLLOUT_PLAN.md
- docs/orchestration/session_reports/2026-05/2026-05-17_precompact_handoff.md
- plans/PHASE_PROGRESS.md

REQUIRED_IMPLEMENTATION:
1. scripts/audit_step3_dataset_coverage.py:
   - `main()` function with argparse: --data-root (required), --out (required), --split (optional, default "all")
   - `audit_coverage(data_root: Path, split_filter: str) -> dict` function
   - Reads .jsonl files; each line is a StepRecord serialized as JSON
   - Handles missing keys gracefully (treat as null)
   - Uses sys.path manipulation to import from src/ if needed (but prefer stdlib + json only)
   - Does NOT import frcgw modules (standalone script for portability)
   - `if __name__ == "__main__": sys.exit(main())`
   
2. tests/test_step3_dataset_coverage_audit.py:
   - Uses `tmp_path` fixture to create synthetic .jsonl files
   - Synthetic data: create minimal step records with the 5 target fields
   - Test 4 (correct coverage for populated synthetic): create 10 steps, 5 with hypothesis_update_timestamp=0, verify ratio=0.5
   - Test 5: verify output JSON has keys: data_root, total_steps, total_episodes, field_coverage

REQUIRED_TESTS:
- tests/test_step3_dataset_coverage_audit.py (5 tests)
- All 5 tests must PASS

ACCEPTANCE_CRITERIA:
1. pytest tests/test_step3_dataset_coverage_audit.py -q → 5 passed, 0 failed
2. CLI invocation with --data-root data/frcgw_text/v0_1 --out /tmp/test_before.json exits 0
   (even if v0_1 is missing; script should handle missing dir gracefully with warning)
3. Output JSON has all required keys
4. Script does NOT import any frcgw.* modules (standalone; uses json stdlib only)
5. No modification to any FILES_FORBIDDEN path

COMMIT_MESSAGE:
feat(step3/task1): add coverage audit script for dataset label fields

STOP_CONDITION:
Stop if any test in tests/test_step3_dataset_coverage_audit.py fails after 2 fix attempts.
Stop if the script requires importing frcgw modules (it should be standalone).
Stop if any FILES_FORBIDDEN path is modified.
