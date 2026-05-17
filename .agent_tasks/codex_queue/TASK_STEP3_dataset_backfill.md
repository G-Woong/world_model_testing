TASK_NAME: STEP3_dataset_backfill
SANDBOX_MODE: bypass

BACKGROUND:
STEP 2 real eval runner has 66 BLOCKED markers. Root causes:
1. collector.py L220-226: hypothesis_update_timestamp, recovery_timestamp, ood_type all hardcoded None
2. data/frcgw_text/v0_1/: selected_hypothesis_confidence not emitted (schema predates v0_1)
3. test_ood.jsonl: absent, no OOD spec generator path

This task (Task 2 of 3):
- Patches collector.py to backfill hypothesis_update_timestamp and recovery_timestamp
  using an episode-level post-pass (after all steps collected)
- Adds ood_type field to TextEpisodeSpec
- Adds OOD spec generation path (held-out grammar families: filter_accordion, nested_scroll)
- Creates configs/dataset_v0_2.yaml
- Regenerates dataset as data/frcgw_text/v0_2/ with all 4 splits
- Creates 20 tests (12 backfill + 5 leakage + 3 OOD)

Key design docs:
- docs/orchestration/lr_alignment/19_step3_dataset_backfill_plan.md §5 (backfill design)
- src/frcgw/schemas/step_schema.py (EvaluationLabels, TrainingLabels, ActionRecord)
- src/frcgw/text_env/state.py (TextEpisodeSpec)
- src/frcgw/text_env/collector.py (collect_episode function)
- src/frcgw/text_env/generator.py (EpisodeSpecGenerator, TaskFamily)
- configs/data_collection_text.yaml (v0_1 config reference)

GOAL:
1. Add `ood_type: str | None = None` field to TextEpisodeSpec in state.py
2. Add `_backfill_episode_timestamps(steps, ood_type)` function to collector.py
3. Call this function in collect_episode() BEFORE validate_visibility_contract()
   (after the step loop, before EpisodeRecord construction)
4. Add OOD spec generation to EpisodeSpecGenerator (generate_ood() method)
5. Create configs/dataset_v0_2.yaml
6. Regenerate dataset: run scripts/01_generate_text_data.py with v0_2 config
   - Creates data/frcgw_text/v0_2/{train,valid,test_id}.jsonl
   - Creates data/frcgw_text/v0_2/test_ood.jsonl separately
   - Creates data/frcgw_text/v0_2/manifest.json
   - Creates data/frcgw_text/v0_2/audits/ directory
7. Create 20 tests across 3 test files

FILES_ALLOWED:
- src/frcgw/text_env/collector.py
- src/frcgw/text_env/state.py
- src/frcgw/text_env/generator.py
- scripts/01_generate_text_data.py
- configs/dataset_v0_2.yaml
- data/frcgw_text/v0_2/
- tests/test_step3_dataset_backfill.py
- tests/test_step3_no_label_leakage.py
- tests/test_step3_ood_split.py

FILES_FORBIDDEN:
- data/frcgw_text/v0_1/
- .claude/
- CLAUDE.md
- .mcp.json
- .venv/
- outputs/
- secrets/
- .env*
- scripts/run_codex_task.ps1
- paper_context_ref/
- src/frcgw/schemas/visibility.py
- src/frcgw/schemas/step_schema.py
- src/frcgw/evaluation/eval_runner.py
- src/frcgw/evaluation/metrics.py
- src/frcgw/evaluation/baselines.py
- src/frcgw/evaluation/frcg_agent.py
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

### 1. src/frcgw/text_env/state.py

Add field to TextEpisodeSpec dataclass:
```python
ood_type: str | None = None  # None for id split, "grammar_shift" for ood split
```

### 2. src/frcgw/text_env/collector.py

Add function BEFORE collect_episode():
```python
def _backfill_episode_timestamps(
    steps: list[StepRecord],
    ood_type: str | None,
) -> list[StepRecord]:
    """Episode-level post-pass: backfill hypothesis_update_timestamp, recovery_timestamp, ood_type.
    
    Source: docs/orchestration/lr_alignment/19_step3_dataset_backfill_plan.md §5.1
    """
    import dataclasses

    # hypothesis_update_timestamp: first step where valid_hypothesis_switch=True
    hyp_update_ts = None
    for i, step in enumerate(steps):
        if step.training_labels.valid_hypothesis_switch:
            hyp_update_ts = i
            break

    # recovery_timestamp: first step where action_type == recovery_action_id
    # AND progress_delta > 0 AND prior step had true_wrong_hypothesis=True
    recovery_ts = None
    for i, step in enumerate(steps):
        if i == 0:
            continue
        prior_wrong = steps[i - 1].evaluation_labels.true_wrong_hypothesis
        tl = step.training_labels
        if (
            prior_wrong
            and step.action.action_type == tl.recovery_action_id
            and tl.progress_delta > 0
        ):
            recovery_ts = i
            break

    patched = []
    for step in steps:
        new_eval = dataclasses.replace(
            step.evaluation_labels,
            hypothesis_update_timestamp=hyp_update_ts,
            recovery_timestamp=recovery_ts,
            ood_type=ood_type,
        )
        patched.append(dataclasses.replace(step, evaluation_labels=new_eval))
    return patched
```

In collect_episode(), BEFORE building EpisodeRecord (after the step loop, after all steps are collected):
```python
# Post-pass: backfill episode-level timestamps
ood_type = getattr(spec, 'ood_type', None)
steps = _backfill_episode_timestamps(steps, ood_type)
```

### 3. src/frcgw/text_env/generator.py

Add `generate_ood()` method to EpisodeSpecGenerator:
```python
OOD_GRAMMAR_FAMILIES = [TaskFamily.FILTER_ACCORDION, TaskFamily.NESTED_SCROLL]

def generate_ood(self, n: int, ood_type: str = "grammar_shift") -> list[TextEpisodeSpec]:
    """Generate OOD episode specs using held-out grammar families."""
    specs = []
    for i in range(n):
        family = self._rng.choice(OOD_GRAMMAR_FAMILIES)
        spec = self._generate_spec(family)
        # spec is a TextEpisodeSpec; we need to set ood_type
        import dataclasses
        spec = dataclasses.replace(spec, ood_type=ood_type)
        specs.append(spec)
    return specs
```

ID split families (train/valid/test_id) must EXCLUDE OOD_GRAMMAR_FAMILIES:
- Modify generate() to filter out OOD families when generating ID splits

### 4. configs/dataset_v0_2.yaml

```yaml
# v0.2 dataset config with OOD split and backfilled labels
# Source: docs/orchestration/lr_alignment/19_step3_dataset_backfill_plan.md §10

version: 2
phase: P3
dataset_version: "0.2"
schema_version: "schema-06-v0.2"
generator_version: "p3-text-v0.2"
num_episodes: 200
num_ood_episodes: 50
max_steps: 12
seed: 73211
output_dir: "data/frcgw_text/v0_2"

id_grammar_families:
  - search_form
  - required_dropdown
  - modal_blocker
  - pagination_vs_infinite
  - loading_delayed
  - permission_gate

ood_grammar_families:
  - filter_accordion
  - nested_scroll

policy_mixture:
  oracle: 0.20
  wrong_grammar: 0.25
  retry: 0.25
  recovery: 0.20
  random_constrained: 0.10

coverage_thresholds:
  failed_action_ratio: 0.20
  recovery_ratio: 0.08
  repeated_wrong_mapping_ratio: 0.08
  shift_ratio: 0.08
  reveal_ratio: 0.05
  delayed_or_noisy_or_no_op_valid_ratio: 0.03

splits:
  train: 0.70
  valid: 0.15
  test_id: 0.15

forbidden_fields:
  - true_regime
  - true_control_grammar
  - true_change_point
  - true_reveal_vs_shift
  - true_wrong_hypothesis
  - counterfactual_action_effects
  - oracle_regime_action
  - oracle_grammar_action
  - split_id
  - ood_type
  - template_id
  - seed
  - policy_id

notes: "v0.2: backfilled hypothesis_update_timestamp, recovery_timestamp, ood_type; OOD split added."
```

### 5. scripts/01_generate_text_data.py

If the config has `ood_grammar_families` and `num_ood_episodes`:
- Restrict ID episode generation to id_grammar_families only
- After ID split generation, call gen.generate_ood(num_ood_episodes)
- Collect OOD episodes and export to test_ood.jsonl separately
- Otherwise preserve backward compatibility with v0_1 config

### 6. Dataset regeneration

After implementing the above, run:
```
python scripts/01_generate_text_data.py --config configs/dataset_v0_2.yaml
```
to generate data/frcgw_text/v0_2/.

REQUIRED_TESTS:

### tests/test_step3_dataset_backfill.py (12 tests)

1. test_collector_emits_hypothesis_update_timestamp_when_switch_occurs
   - Synthesize episode with valid_hypothesis_switch=True at step 3
   - Assert all steps have hypothesis_update_timestamp=3

2. test_collector_emits_recovery_timestamp_when_recovery_resolves_wrong_grammar
   - Step 0: true_wrong_hypothesis=True, recovery_action_id="close_modal"
   - Step 1: action_type="close_modal", progress_delta=0.5
   - Assert recovery_timestamp=1

3. test_collector_keeps_recovery_timestamp_none_for_non_wrong_grammar_episode
   - Episode with no true_wrong_hypothesis=True steps
   - Assert all steps have recovery_timestamp=None

4. test_collector_emits_ood_type_for_ood_spec
   - Create spec with ood_type="grammar_shift"
   - Run collect_episode
   - Assert all steps have ood_type="grammar_shift"

5. test_backfilled_dataset_has_required_step3_fields
   - Load data/frcgw_text/v0_2/test_id.jsonl (at least 5 rows)
   - Assert each row has keys: eval_labels.hypothesis_update_timestamp,
     eval_labels.recovery_timestamp, action.selected_hypothesis_confidence
   - (None is allowed; key must exist)

6. test_backfilled_dataset_preserves_episode_step_continuity
   - Load v0_2 dataset
   - For each episode, verify step_index is sequential 0,1,2,...

7. test_backfilled_dataset_is_deterministic_for_seed
   - Run collect_episode twice with same spec and seed
   - Assert resulting steps are identical

8. test_original_v0_1_dataset_not_overwritten
   - Assert data/frcgw_text/v0_1/train.jsonl still exists
   - Assert its line count has not changed

9. test_v0_2_manifest_records_split_sizes
   - Load data/frcgw_text/v0_2/manifest.json
   - Assert has keys: train_count, valid_count, test_id_count, test_ood_count

10. test_persistence_metric_becomes_computable_when_labels_present
    - Load v0_2 test_id.jsonl
    - Find episodes where hypothesis_update_timestamp is not None
    - Assert at least 1 such episode exists (hypothesis switch happened)

11. test_recovery_delay_metric_becomes_computable_when_labels_present
    - Load v0_2 test_id.jsonl
    - Find episodes where recovery_timestamp is not None
    - Assert at least 1 such episode exists

12. test_calibration_ece_becomes_computable_when_confidence_present
    - Load v0_2 test_id.jsonl
    - Find steps where action.selected_hypothesis_confidence is not None
    - Assert at least 50% of steps have non-null confidence

### tests/test_step3_no_label_leakage.py (5 tests)

13. test_public_input_does_not_contain_eval_labels
    - Run collect_episode on a spec
    - For each step, assert public_observation dict has no eval_labels keys

14. test_public_input_does_not_contain_ood_type
    - Create OOD spec (ood_type="grammar_shift")
    - Run collect_episode
    - Assert "ood_type" not in str(step.public_observation.instruction)
    - Assert "grammar_shift" not in any public field

15. test_candidate_actions_do_not_contain_oracle_labels
    - For each step, assert candidate_actions_public items have no hidden fields

16. test_eval_labels_not_passed_to_non_oracle_agent
    - Create a random constrained policy
    - Run collect_episode
    - Assert policy.last_selected_hypothesis_id is None for random policy
    
17. test_visibility_forbidden_fields_still_mirror_hook
    - Import FORBIDDEN_AGENT_FIELDS from frcgw.schemas.visibility
    - Assert "ood_type" IS in FORBIDDEN_AGENT_FIELDS (it's in inference_forbidden set)
    - This is a sync check

### tests/test_step3_ood_split.py (3 tests)

18. test_test_ood_jsonl_created_with_distinct_grammar_families
    - Load data/frcgw_text/v0_2/test_ood.jsonl
    - Extract task_family field from each episode
    - Assert all families ARE in {"filter_accordion", "nested_scroll"} (OOD only)
    - Assert NONE of these ID families appear: {"search_form", "required_dropdown",
      "modal_blocker", "pagination_vs_infinite", "loading_delayed", "permission_gate"}
    - This is a BIDIRECTIONAL check: OOD ⊆ ood_set AND OOD ∩ id_set = ∅

19. test_ood_type_present_in_all_ood_episodes
    - Load test_ood.jsonl
    - For each step, assert eval_labels.ood_type == "grammar_shift"

20. test_ood_split_does_not_duplicate_test_id_exactly
    - Load test_id.jsonl and test_ood.jsonl
    - Assert no episode_id appears in both

ACCEPTANCE_CRITERIA:
1. pytest tests/test_step3_dataset_backfill.py tests/test_step3_no_label_leakage.py tests/test_step3_ood_split.py -q → 20 passed, 0 failed
2. data/frcgw_text/v0_2/ directory exists with: train.jsonl, valid.jsonl, test_id.jsonl, test_ood.jsonl, manifest.json
3. data/frcgw_text/v0_1/ directory is UNMODIFIED (line counts identical)
4. In v0_2 dataset: hypothesis_update_timestamp non-null in ≥ 5% of episodes (some episodes have no switch)
5. In v0_2 dataset: selected_hypothesis_confidence non-null in ≥ 50% of steps
6. ood_type == "grammar_shift" for all test_ood episodes
7. validate_visibility_contract passes for all v0_2 episodes (no leakage)
8. pytest tests/test_forbidden_field_mirror_sync.py -q → still green

COMMIT_MESSAGE:
feat(step3/task2): backfill v0.2 dataset labels + OOD split generator

STOP_CONDITION:
CRITICAL STOP: If data/frcgw_text/v0_1/ is modified in any way, immediately abort.
Stop if validate_visibility_contract() raises HiddenLabelLeakageError for any v0_2 episode.
Stop if test_step3_no_label_leakage.py tests fail after 2 fix attempts.
Stop if any FILES_FORBIDDEN path is modified.
