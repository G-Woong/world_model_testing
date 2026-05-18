TASK_NAME: step8_abl015_faithful
SANDBOX_MODE: bypass

BACKGROUND:
FRCG-WM STEP 8. ABL-015 (per §8 SSoT of 10_EVALUATION_BASELINE_ABLATION.md) = no L_control_grammar = l_control_grammar=0.0. NOTE: The step8 handoff doc (35_step8_handoff.md) contains a naming error calling this "no_falsification_training_hard" — that is WRONG. The §8 SSoT definition takes precedence. This task implements the CORRECT ABL-015: l_control_grammar=0.0 retrain, identical to Stage B otherwise. ABL-015 tests whether training the control-grammar head is necessary for the core FRCG-WM claims (C1 persistence + C2 factorization).

GOAL:
1. Create configs/train_text_v0_4_abl015.yaml: Stage B config with ONLY l_control_grammar: 0.0 changed.
2. Create scripts/run_step8_faithful_ablations.py: orchestrates ABL-015 training entry (script writes training command + checkpoint path to RESULT.md; Claude executes).
3. Create tests/test_step8_faithful_ablations.py: verify config diff isolation.

FILES_ALLOWED:
- configs/train_text_v0_4_abl015.yaml (NEW)
- scripts/run_step8_faithful_ablations.py (NEW)
- tests/test_step8_faithful_ablations.py (NEW)
- .agent_tasks/codex_done/TASK_1082_step8_abl015_faithful_RESULT.md

FILES_FORBIDDEN:
- configs/train_text_v0_4_long_stage2.yaml (read-only; must compare against it but not edit)
- src/frcgw/schemas/visibility.py
- outputs/**
- data/**
- paper_context_ref/**
- .claude/**
- scripts/run_codex_task.ps1
- *.pt

REQUIRED_IMPLEMENTATION:
configs/train_text_v0_4_abl015.yaml:
- ALL fields IDENTICAL to configs/train_text_v0_4_long_stage2.yaml EXCEPT:
  - objective_weights.l_control_grammar: 0.0 (instead of 1.0)
  - phase: "CC-P3-STEP8-ABL015"
  - manifest_dir: "outputs/runs/p3_train_v0_4_abl015"
  - checkpoint_dir: "outputs/checkpoints/abl015_no_control_grammar_loss"
  - ablation: "ABL-015"
  - notes: "ABL-015: no L_control_grammar faithful retrain. SSoT: 10_EVALUATION_BASELINE_ABLATION.md §8 ABL-015. l_control_grammar=0.0, all other weights identical to Stage B."
- MUST include comment: "# ABL-015 per §8 SSoT = no_control_grammar_loss. DO NOT confuse with ABL-016 (no_falsification)."

scripts/run_step8_faithful_ablations.py:
- Validates that configs/train_text_v0_4_abl015.yaml exists and has l_control_grammar=0.0
- Validates that configs/train_text_v0_4_long_stage2.yaml exists and has l_control_grammar=1.0 (to verify the diff is exactly 1 field)
- Prints the training command to run ABL-015:
  "python scripts/02_train_text_smoke.py --config configs/train_text_v0_4_abl015.yaml --model-config configs/model_text.yaml --output-dir outputs/runs/p3_train_v0_4_abl015"
- Prints expected checkpoint path: "outputs/checkpoints/abl015_no_control_grammar_loss/checkpoint_best.pt"
- Returns exit code 0 on validation success, 1 on config mismatch
- ABL-001/003 are explicitly NOT included in this script; they must appear in a comment: "# ABL-001/003 faithful retrain: STEP 9 queue. Not implemented here."

tests/test_step8_faithful_ablations.py:
- test_abl015_config_diff_isolation: load both configs, assert ONLY l_control_grammar differs between abl015 and stage2 configs (no other key may differ except phase/manifest_dir/checkpoint_dir/ablation/notes)
- test_abl015_ablation_field_set: verify config has ablation="ABL-015"
- All 2 tests must pass. No real checkpoint or execution required.

REQUIRED_TESTS:
- tests/test_step8_faithful_ablations.py: all 2 tests green

ACCEPTANCE_CRITERIA:
1. configs/train_text_v0_4_abl015.yaml differs from Stage B config ONLY in l_control_grammar (confirmed by test)
2. Script validates config diff isolation and prints training command
3. ABL-001/003 explicitly noted as STEP 9 in comment
4. Both tests green

COMMIT_MESSAGE:
feat(step8/task5): ABL-015 faithful retrain config (l_control_grammar=0.0)

STOP_CONDITION:
Stop if configs/train_text_v0_4_long_stage2.yaml does not exist (prerequisite from TASK_1080 not met). Report as blocker.

RELATED_AGENT_REPORT_IDS: exp_design_step8_v04_ablation_R1
