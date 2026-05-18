TASK_NAME: step8_v04_dataset
SANDBOX_MODE: bypass

BACKGROUND:
FRCG-WM STEP 8. v0_3 dataset (200 episodes) has OOD gap: test_ood has blocker_removed=0, delayed_effect=0 (only 3 of 5 effect types covered). v0_4 must fix this and scale to 5000 episodes for long-horizon training.

CRITICAL (from experiment-design-expander audit): v0_3 OOD grammar families (filter_accordion, nested_scroll) CANNOT structurally produce blocker_removed or delayed_effect effect types. These effect types are produced by MODAL_BLOCKER and LOADING_DELAYED families respectively, which are in the ID split. Therefore: policy_mixture adjustment alone CANNOT fix the OOD coverage gap. The v0_4 generator MUST implement explicit stratified OOD sampling with effect_type forcing.

CRITICAL (from claim-metric-alignment-auditor): C1 metric (compute_wrong_grammar_persistence_v1) requires eval_labels.correct_hypothesis_id. If v0_4 generator does NOT emit this field, all C1 episodes report status=BLOCKED. Must be added to evaluation_labels generation.

CRITICAL (from frcgw-data-leakage-auditor): oracle_best_action and audit_metadata are in FORBIDDEN_AGENT_FIELDS (visibility.py) but absent from dataset_v0_3.yaml forbidden_fields list. v0_4 config must add these.

GOAL:
1. Create configs/dataset_v0_4.yaml specifying 5000 episodes (train=3500/valid=500/test_id=500/test_ood=500), OOD coverage gates, schema_version "schema-06-v0.4".
2. Create scripts/generate_v0_4_dataset.py that generates the dataset to data/frcgw_text/v0_4/ with manifest.json.
3. Create scripts/audit_step8_dataset_coverage.py that reads data/frcgw_text/v0_4/ and writes outputs/audits/step8_v0_4_dataset_coverage.json with coverage gates.
4. Create tests/test_step8_v0_4_dataset.py with ≥3 passing tests.

FILES_ALLOWED:
- configs/dataset_v0_4.yaml (NEW)
- scripts/generate_v0_4_dataset.py (NEW)
- scripts/audit_step8_dataset_coverage.py (NEW)
- tests/test_step8_v0_4_dataset.py (NEW)
- .agent_tasks/codex_done/TASK_1079_step8_v04_dataset_RESULT.md

FILES_FORBIDDEN:
- data/frcgw_text/v0_1/**
- data/frcgw_text/v0_2/**
- data/frcgw_text/v0_3/**
- outputs/**
- src/frcgw/schemas/visibility.py
- src/frcgw/schemas/step_schema.py
- paper_context_ref/**
- .claude/**
- scripts/run_codex_task.ps1
- *.pt

REQUIRED_IMPLEMENTATION:
configs/dataset_v0_4.yaml:
- version: 4, phase: P3, dataset_version: "0.4", schema_version: "schema-06-v0.4"
- target_episodes: 5000 (train: 3500, valid: 500, test_id: 500, test_ood: 500)
- max_steps: 12, seed: 84322
- output_dir: "data/frcgw_text/v0_4"
- id_grammar_families: same 6 as v0_3 (search_form, required_dropdown, modal_blocker, pagination_vs_infinite, loading_delayed, permission_gate)
- ood_grammar_families: filter_accordion, nested_scroll
- policy_mixture: oracle 0.20, wrong_grammar 0.25, retry 0.25, recovery 0.20, random_constrained 0.10
- ood_coverage_gates: {blocker_removed_min: 30, delayed_effect_min: 30, true_wrong_both_classes: true}
- ood_effect_type_strata: {blocker_removed: 0.10, delayed_effect: 0.10}  # CRITICAL: explicit stratification since grammar families don't produce these by construction
- forbidden_fields: all 15 FORBIDDEN_AGENT_FIELDS from visibility.py including oracle_best_action and audit_metadata (these are MISSING from v0_3 config — must add them)
- counterfactual_rollout: {enabled: true, top_k: 3}
- generate_correct_hypothesis_id: true  # CRITICAL: must emit correct_hypothesis_id in evaluation_labels for C1 metric

scripts/generate_v0_4_dataset.py:
- Args: --config (yaml path), --out-root (output dir), --target-episodes (int), --seed (int)
- Based on v0_3 generator (src/frcgw/text_env/generator.py), must import and reuse it
- CRITICAL: OOD coverage enforcement requires EXPLICIT STRATIFIED SAMPLING because filter_accordion
  and nested_scroll grammar families CANNOT produce blocker_removed or delayed_effect effect types
  by construction. Implementation: for OOD split, generate 80% episodes normally + 20% with explicit
  effect_type forcing:
  - For blocker_removed-forced episodes: use MODAL_BLOCKER-style action sequence with modified
    _simulate_action to return "blocker_removed" from the public effect vocab. This is a generator-level
    simulation — the HIDDEN grammar remains filter_accordion/nested_scroll but the simulated effect
    for this episode is forced to blocker_removed. Document this as "effect_type_stratified_episode=true"
    in the episode's audit_metadata (NOT in agent_observation).
  - For delayed_effect-forced episodes: same approach but force "delayed_effect" effect type
  - Run stratified OOD generation in a loop until coverage gates are met OR max_attempts=10× target
  - If gates cannot be met after max_attempts: write partial data + log warning "OOD_COVERAGE_GATE_PARTIAL" to manifest.json
- CRITICAL: each episode's evaluation_labels must include correct_hypothesis_id (the hypothesis_id that
  corresponds to the actual grammar family of the episode). For ID episodes: correct grammar = episode grammar.
  For OOD effect-forced episodes: correct grammar = "no_matching_grammar" (since the effect forcing is artificial).
  Write as integer hypothesis index if available, else as grammar string.
- Write each split as JSONL to {out_root}/{split}.jsonl
- Write manifest.json with: schema_version, total_episodes, split_counts, ood_effect_type_counts, coverage_gate_status, sha256 of each split file, generator_version, seed, timestamp
- FORBIDDEN: never write true_regime/true_control_grammar/etc. to agent_observation fields
- Must call src/frcgw/data/leakage_auditor.py audit on generated data before writing manifest

scripts/audit_step8_dataset_coverage.py:
- Args: --data-root (path), --out (JSON path)
- Reads all 4 split JSONL files
- Counts per-split: total_episodes, effect_type distribution, true_wrong_hypothesis class balance
- Checks coverage gates: blocker_removed >= 30 in test_ood, delayed_effect >= 30 in test_ood, both true_wrong classes in test_ood
- Checks leakage: zero FORBIDDEN_AGENT_FIELDS in any agent_observation (import FORBIDDEN_AGENT_FIELDS from visibility.py)
- Writes: {split: {total, effect_types, true_wrong_counts, coverage_gate_pass}, leakage_count, coverage_gate_overall, ood_coverage_gate_pass}
- Coverage gate output keys: "OOD_COVERAGE_GATE_PASS" or "OOD_COVERAGE_GATE_FAIL_{reason}"

tests/test_step8_v0_4_dataset.py:
- test_coverage_audit_detects_missing_ood: create synthetic minimal test_ood without blocker_removed → audit must return OOD_COVERAGE_GATE_FAIL
- test_leakage_audit_clean: create synthetic episodes with only PublicObservation fields → leakage_count=0
- test_manifest_schema_fields: verify manifest.json structure has required keys
- All tests use mock/synthetic data, no real disk I/O required

REQUIRED_TESTS:
- tests/test_step8_v0_4_dataset.py: all 3 tests green
- existing: python -m pytest tests/test_forbidden_field_mirror_sync.py tests/test_leakage_auditor.py -q (must stay green)

ACCEPTANCE_CRITERIA:
1. configs/dataset_v0_4.yaml valid and loadable
2. generate_v0_4_dataset.py can be imported without error; dry-run with --target-episodes 5 passes
3. audit_step8_dataset_coverage.py correctly detects OOD coverage gate failure in tests
4. leakage_count=0 enforcement verified by test
5. All 3 new tests green
6. Pre-existing leakage tests stay green

COMMIT_MESSAGE:
feat(step8/task2): v0_4 dataset generator + coverage audit script

STOP_CONDITION:
Stop if: (a) generator requires reading FORBIDDEN_AGENT_FIELDS for OOD coverage enforcement (LEAKAGE — BLOCKED), (b) coverage gate cannot be logically met given grammar families.

RELATED_AGENT_REPORT_IDS: exp_design_step8_v04_ablation_R1, leakage_step8_v04_baselines_R1
