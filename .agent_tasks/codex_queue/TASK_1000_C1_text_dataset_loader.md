TASK_NAME: C1_text_dataset_loader

BACKGROUND:
P2 phase generated 200 episodes in data/frcgw_text/v0_1/{train,valid,test_id}.jsonl.
Each JSONL line is one EpisodeRecord (episode_id, dataset_version, schema_version, generator_version,
split_id, task_family, public_instruction, steps: list[StepRecord], final_success, total_progress,
audit_metadata). Each StepRecord contains:
  - public_observation: PublicObservation (instruction, dom_snapshot_public, accessibility_tree_public,
    screenshot_ref, history_public: list[PublicHistoryItem], candidate_actions_public: list[CandidateAction])
  - action: ActionRecord
  - observed_effect_public: PublicEffect
  - training_labels: TrainingLabels (true_regime, true_control_grammar, true_change_point,
    true_reveal_vs_shift, true_action_effect_type, true_failed_action, failure_reason,
    progress_delta, recovery_action_id, valid_hypothesis_switch)
  - evaluation_labels: EvaluationLabels (true_wrong_hypothesis, h_exec_id, correct_hypothesis_id,
    evidence_timestamp, hypothesis_update_timestamp, recovery_timestamp, ood_type)
  - counterfactuals: list[CounterfactualRecord]  <- MUST NOT appear in public_input ever
  - audit_metadata: StepAuditMetadata  <- MUST NOT appear in public_input ever

FORBIDDEN inference fields (from src/frcgw/schemas/visibility.py::FORBIDDEN_AGENT_FIELDS):
  true_regime, true_control_grammar, true_change_point, true_reveal_vs_shift,
  true_wrong_hypothesis, counterfactual_action_effects, oracle_regime_action,
  oracle_grammar_action, oracle_best_action, split_id, ood_type, template_id, seed,
  policy_id, audit_metadata

assert_agent_observation_safe() is in src/frcgw/schemas/visibility.py and MUST be called on every
public_input before it leaves the collator.

The JSONL structure as confirmed: each line JSON has "steps" as a list of step-level dicts.
The history_public in the JSONL may be serialized as string ("") or as list — handle both.
The candidate_actions_public similarly may be serialized as string ("  ") or list — handle both.

GOAL:
Implement a PyTorch Dataset + collator that:
1. Loads StepRecord objects from JSONL shards (flattening episode→step)
2. Returns batches with two strictly separate objects:
   - public_input: PublicObservation only (no hidden fields, no counterfactuals, no audit metadata)
   - targets: BatchTargets dataclass (all TrainingLabels + EvaluationLabels fields, no CounterfactualRecord)
3. Calls assert_agent_observation_safe() on every public_input in the collator
4. Provides build_dataloaders() to create train/valid/test DataLoaders from manifest.json

FILES_ALLOWED:
  - src/frcgw/data/text_dataset.py
  - tests/test_text_dataset.py
  - src/frcgw/data/__init__.py

FILES_FORBIDDEN:
  - .claude/
  - CLAUDE.md
  - .mcp.json
  - .venv/
  - data/
  - outputs/
  - secrets/
  - scripts/run_codex_task.ps1
  - paper_context_ref/
  - src/frcgw/schemas/
  - src/frcgw/text_env/

REQUIRED_IMPLEMENTATION:

File: src/frcgw/data/text_dataset.py

```python
"""frcgw.data.text_dataset — P2 JSONL loader, collator, and DataLoader builder.

Source MD: paper_context_ref/06_DATA_SCHEMA_AND_LABELING.md
Source MD: paper_context_ref/15_TDD_TECHNICAL_DESIGN_DOCUMENT_v1.md §17
"""
```

Required classes/functions:

1. BatchTargets (dataclass):
   - Fields from TrainingLabels: true_regime: str, true_control_grammar: str,
     true_change_point: str, true_reveal_vs_shift: str, true_action_effect_type: str,
     true_failed_action: bool, failure_reason: str | None, progress_delta: float,
     recovery_action_id: str | None, valid_hypothesis_switch: bool | None
   - Fields from EvaluationLabels: true_wrong_hypothesis: bool | None, h_exec_id: str | None,
     correct_hypothesis_id: str | None
   - NOTE: CounterfactualRecord fields MUST NOT appear here

2. StepSample (dataclass):
   - public_input: PublicObservation
   - targets: BatchTargets
   - step_id: str (for debugging)

3. TextStepDataset(torch.utils.data.Dataset):
   - __init__(jsonl_path: str | Path)
   - Loads all episodes from JSONL (one episode per line)
   - Flattens to individual steps → list of StepSample
   - Handles both serialized string and list forms of history_public and candidate_actions_public
   - __len__(), __getitem__(idx) -> StepSample

4. collate_fn(batch: list[StepSample]) -> dict:
   - Returns {"public_inputs": list[PublicObservation], "targets": list[BatchTargets], "step_ids": list[str]}
   - MUST call assert_agent_observation_safe(pub_obs) for each public_input
   - If assertion fails, raises with clear error message

5. build_dataloaders(manifest_path: str | Path, batch_size: int = 8, seed: int = 42,
                      num_workers: int = 0) -> tuple[DataLoader, DataLoader, DataLoader]:
   - Reads manifest.json to find shard paths (train.jsonl, valid.jsonl, test_id.jsonl)
   - Returns (train_dl, valid_dl, test_dl)
   - train DataLoader shuffles, valid/test do not

REQUIRED_TESTS:

File: tests/test_text_dataset.py

Tests must use data/frcgw_text/v0_1/ as the test data source (the real P2 dataset).
Use pytest.importorskip or skip gracefully if JSONL not present.

Required test cases:

1. test_collator_returns_only_public_input:
   - Load 1 batch from train split
   - Assert: batch["public_inputs"] is list of PublicObservation
   - Assert: none of FORBIDDEN_AGENT_FIELDS appear in public_input (field names)
   - Use _collect_field_names from visibility.py

2. test_forbidden_fields_absent:
   - For a random sample, check all 15 forbidden field names are NOT in public_input's
     attribute names or dict keys

3. test_targets_contain_all_labels:
   - Load 1 batch, check BatchTargets has true_regime, true_control_grammar,
     true_action_effect_type, true_wrong_hypothesis, h_exec_id, progress_delta

4. test_counterfactual_not_in_batch:
   - Assert: "counterfactual_id", "counterfactual_effect_type", "is_oracle_best" NOT in
     any BatchTargets field names

5. test_batch_shape_consistent:
   - Load 1 batch from each split (train, valid, test_id)
   - Assert: all batches are non-empty lists with consistent structure

6. test_assert_fires_on_leakage:
   - Manually inject a forbidden field into a PublicObservation object
   - Assert: collate_fn raises HiddenLabelLeakageError or similar

7. test_dataset_length_nonzero:
   - train set len > 0, valid set len > 0, test_id set len > 0

8. test_step_sample_has_step_id:
   - Each StepSample.step_id is a non-empty string

ACCEPTANCE_CRITERIA:
  - pytest tests/test_text_dataset.py -q: ALL PASS (0 failures, 0 errors)
  - assert_agent_observation_safe() called in collate_fn (verify by reading code)
  - "Source MD: paper_context_ref/06_DATA_SCHEMA_AND_LABELING.md" in module docstring
  - RESULT.md written to .agent_tasks/codex_done/TASK_C1_text_dataset_loader_RESULT.md
  - No modifications to forbidden paths

COMMIT_MESSAGE: feat(p3-c1): text dataset loader with leakage-safe collator

STOP_CONDITION:
  - STOP immediately if any FORBIDDEN_AGENT_FIELD appears in public_input at any point
  - STOP if CounterfactualRecord fields appear in BatchTargets
  - STOP if audit_metadata fields appear in public_input
  - STOP if tests cannot be made to pass within the allowed files
