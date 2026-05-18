TASK_NAME: TASK_1097_step9_abl001_003_configs
SANDBOX_MODE: bypass

BACKGROUND:
FRCG-WM P3 STEP 9 STEP 4 Faithful Retrain Queue.
ABL-001 (no_regime) and ABL-003 (merged_regime_control_grammar) faithful retrains are needed
to establish claim-level ablation evidence for C2 (regime separation).

Reference:
- ABL-001 (ABL-001): no_regime faithful retrain — removes regime latent dimension
- ABL-003 (ABL-003): merged_regime_control_grammar — merges regime+grammar heads
- SSoT: paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md §8 ABL-001, ABL-003
- Config format reference: configs/train_text_v0_4_abl015.yaml (ABL-015 faithful retrain)

Existing Stage B config: configs/train_text_v0_4_long_stage2.yaml
ABL-015 (no control grammar): configs/train_text_v0_4_abl015.yaml

GOAL:
1. Create configs/train_text_v0_4_abl001.yaml — no_regime faithful retrain (l_regime=0.0)
2. Create configs/train_text_v0_4_abl003.yaml — merged_regime_control_grammar (shared z_regime+z_grammar dimension)

For ABL-003: Check if model architecture supports merged mode.
If a "merge_regime_and_grammar" flag exists in TextFRCGModel or model config → use it.
If not → use config flag only (training script may need to be checked but do NOT modify model code without explicit guidance).

FILES_ALLOWED:
- configs/train_text_v0_4_abl001.yaml
- configs/train_text_v0_4_abl003.yaml

FILES_FORBIDDEN:
- src/frcgw/schemas/visibility.py
- CLAUDE.md
- .claude/
- .mcp.json
- paper_context_ref/
- scripts/run_codex_task.ps1
- outputs/
- data/
- .venv/
- secrets/
- src/ (DO NOT modify any source files)

REQUIRED_IMPLEMENTATION:

### configs/train_text_v0_4_abl001.yaml

Based on configs/train_text_v0_4_abl015.yaml with the following changes:
- phase: CC-P3-STEP9-ABL001
- ablation: "ABL-001"
- objective_weights: set l_regime: 0.0 (remove regime loss)
- warm_start_checkpoint: "outputs/checkpoints/pretrain_v0_4_long_stageA/checkpoint_best.pt" (same as ABL-015)
- checkpoint_dir: "outputs/checkpoints/abl001_no_regime"
- manifest_dir: "outputs/runs/p3_train_v0_4_abl001"
- notes: "ABL-001: no L_regime faithful retrain. SSoT: 10_EVALUATION_BASELINE_ABLATION.md §8 ABL-001. l_regime=0.0, all other weights identical to Stage B. Expected collapse: regime_shift_f1 decrease."

All forbidden_fields should be identical to ABL-015 config.

### configs/train_text_v0_4_abl003.yaml

Based on configs/train_text_v0_4_abl015.yaml with the following changes:
- phase: CC-P3-STEP9-ABL003
- ablation: "ABL-003"
- objective_weights: keep same as Stage B (l_regime=1.0, l_control_grammar=1.0) — merged training uses both losses but shared representation
- warm_start_checkpoint: "outputs/checkpoints/pretrain_v0_4_long_stageA/checkpoint_best.pt"
- checkpoint_dir: "outputs/checkpoints/abl003_merged_regime_grammar"
- manifest_dir: "outputs/runs/p3_train_v0_4_abl003"
- Add flag: merge_regime_and_grammar: true (for model config if supported)
- notes: "ABL-003: merged_regime_control_grammar faithful retrain. SSoT: 10_EVALUATION_BASELINE_ABLATION.md §8 ABL-003. Shared regime+grammar latent. Expected collapse: C2 regime_shift_f1 decrease AND C3 falsification_f1 decrease."

REQUIRED_TESTS:
- No new tests required for config-only changes.
- Verify that both YAML files are valid YAML (parseable).
- Verify that the files have all required keys: version, phase, seed, batch_size, max_steps, objective_weights, checkpoint_dir, ablation.

ACCEPTANCE_CRITERIA:
1. configs/train_text_v0_4_abl001.yaml exists and is valid YAML
2. configs/train_text_v0_4_abl003.yaml exists and is valid YAML
3. ABL-001: l_regime: 0.0 in objective_weights
4. ABL-003: merge_regime_and_grammar: true flag present
5. Both configs reference Stage A checkpoint as warm_start
6. Both configs have forbidden_fields list
7. NO source code files modified (src/ entirely forbidden)

COMMIT_MESSAGE:
feat(step9): ABL-001 no_regime + ABL-003 merged_regime_grammar faithful retrain configs (STEP 9 STEP 4)

STOP_CONDITION:
Stop if:
- Any src/ file modification attempted
- Paper context files modified
- .claude/ modified
- outputs/ or data/ modified
