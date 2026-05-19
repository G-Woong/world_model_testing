Task: 1102 / 1097

Files changed:
- configs/train_text_v0_4_abl001.yaml
- configs/train_text_v0_4_abl003.yaml
- .agent_tasks/codex_done/TASK_1102_1097_RESULT.md

Tests run:
- `@' ... '@ | .\.venv\Scripts\python.exe -`
  - Parsed both YAML files with PyYAML.
  - Verified required keys: version, phase, seed, batch_size, max_steps, objective_weights, checkpoint_dir, ablation.
  - Verified both configs use the Stage A warm-start checkpoint.
  - Verified both configs include forbidden_fields.
  - Verified ABL-001 sets objective_weights.l_regime to 0.0.
  - Verified ABL-003 sets merge_regime_and_grammar to true.

Pass/fail summary:
- PASS: ABL-001 and ABL-003 YAML validation and required key checks passed.

Blockers:
- None.
