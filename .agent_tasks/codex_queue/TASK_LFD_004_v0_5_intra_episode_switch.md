TASK_NAME: TASK_LFD_004_v0_5_intra_episode_switch

BACKGROUND:
FRCG-WM text environment currently generates single-regime episodes:
generator.py:266 sets `hidden_regime=family` for the entire episode.
TextEpisodeSpec.hidden_regime is a single string (state.py:62).
BatchTargets.true_regime is a single string per step (text_dataset.py:25).

The Learned Falsification Detector (LFD) requires a v0_5 dataset where
intra-episode regime switches occur: after step `regime_switch_step`, the
control grammar changes to a new value while the same actions produce
different effects (same-action / different-effect pattern).

This task implements the v0_5 generator and collector extension while
preserving full v0_4 backward compatibility.

CRITICAL cascade mapping (from M3 of preflight checkpoint-0):
- TextEpisodeSpec gains: `regime_switch_step: int | None`, `hidden_regime_after: str | None`
- TextState gains: `_hidden_switch_occurred: bool`
- TextStepCollector / collector loop: emit `regime_switch_step` only to
  `evaluation_labels` (never to PublicObservation or training_labels)
- BatchTargets gains: `regime_switch_step: int | None` (eval-only, None for v0_4)
- `L_regime` in losses.py: receives `true_regime` per step — switch steps get
  the POST-switch regime as training label (this is TRAINING_SUPERVISION, safe)

SAFETY GATE (M4 from preflight):
`regime_switch_step` is a ground-truth label equivalent to `true_change_point`.
It MUST be added to `FORBIDDEN_AGENT_FIELDS` in `src/frcgw/schemas/visibility.py`
BEFORE this task executes (requires explicit user approval per CLAUDE.md §Invariant
Preservation). This task's STOP_CONDITION enforces that the sync test is green.

GOAL:
1. Extend TextEpisodeSpec and TextState to support per-episode regime switch.
2. Extend EpisodeSpecGenerator to emit v0_5 episodes with intra-episode switch.
3. Extend collector to record regime_switch_step in EvaluationLabels (EVALUATION_ONLY).
4. Extend BatchTargets with regime_switch_step (eval-only, None for v0_4).
5. Add dataset audit script to verify switch rate and leakage.
6. Preserve v0_4 full backward compatibility (all existing tests must pass).

FILES_ALLOWED:
- src/frcgw/text_env/state.py
- src/frcgw/text_env/generator.py
- src/frcgw/text_env/collector.py
- src/frcgw/data/text_dataset.py
- src/frcgw/schemas/step_schema.py
- scripts/risk_hunt/generate_v0_5_dataset.py  (new file)
- tests/test_v0_5_generator.py  (new file)
- tests/test_v0_5_collector.py  (new file)

FILES_FORBIDDEN:
- .claude/
- CLAUDE.md
- .mcp.json
- .venv/
- data/
- outputs/
- secrets/
- .env*
- scripts/run_codex_task.ps1
- paper_context_ref/
- src/frcgw/schemas/visibility.py
- src/frcgw/objectives/losses.py
- src/frcgw/models/

REQUIRED_IMPLEMENTATION:
1. TextEpisodeSpec (state.py):
   - Add `regime_switch_step: int | None = None`
   - Add `hidden_regime_after: str | None = None`
   - v0_4 default: both None

2. TextState (state.py):
   - Add `_hidden_switch_occurred: bool = False`

3. EpisodeSpecGenerator (generator.py):
   - Add method `generate_v0_5(family: str | None, rng: random.Random | None) -> TextEpisodeSpec`
   - Switch step sampled from U[2, max_steps-2] for non-trivial switch
   - `hidden_regime_after` chosen as a different family grammar (not same as pre-switch)
   - v0_4 `generate()` unchanged
   - Add `OOD_GRAMMAR_FAMILIES` split: switch episodes preferentially use ID families
     pre-switch → OOD family grammar post-switch to simulate grammar shift

4. Collector (collector.py — create if absent):
   - `collect_episode_v0_5(spec: TextEpisodeSpec) -> list[TextStepResult]`
   - Pre-switch steps: standard collection
   - Post-switch steps: same action type maps to `different_effect_type` (type 3 for pre-type 0, etc.)
   - Write `regime_switch_step` to `EvaluationLabels.regime_switch_step` (EVALUATION_ONLY)
   - MUST NOT write `regime_switch_step` to `TrainingLabels` or `PublicObservation`

5. BatchTargets (text_dataset.py):
   - Add `regime_switch_step: int | None = None`
   - Collator reads from `step.evaluation_labels.regime_switch_step` (eval-only field)
   - Audit asserts `regime_switch_step` never appears in `public_input` fields

6. scripts/risk_hunt/generate_v0_5_dataset.py:
   - CLI: `--n-episodes`, `--switch-rate`, `--seed`, `--out-dir`
   - Outputs: JSONL shard + audit JSON
   - Audit JSON must include: `regime_switch_episode_count`, `action_outcome_inversion_count`,
     `hidden_label_leakage_count`, `v0_4_episode_count`, `v0_5_episode_count`

REQUIRED_TESTS:
- tests/test_v0_5_generator.py:
  - `test_generate_v0_5_switch_step_in_range`: regime_switch_step in [2, max_steps-2]
  - `test_generate_v0_5_regime_changes`: hidden_regime != hidden_regime_after
  - `test_generate_v0_4_backward_compat`: v0_4 generate() produces None regime_switch_step
  - `test_v0_5_batch_targets_regime_switch_not_in_public_obs`: leakage guard
  - `test_regime_switch_episode_count_nonzero`: audit JSON check

- tests/test_v0_5_collector.py:
  - `test_post_switch_effect_differs_from_pre_switch`: same action → different effect
  - `test_evaluation_labels_has_regime_switch_step`: non-None after switch step
  - `test_training_labels_no_regime_switch_step`: no such field in TrainingLabels
  - `test_public_obs_no_regime_switch_step`: leakage check on PublicObservation fields
  - `test_v0_4_episode_no_switch`: v0_4 episodes unaffected

- tests/test_forbidden_field_mirror_sync.py must remain GREEN (3 passed)

ACCEPTANCE_CRITERIA:
- All listed tests pass
- audit JSON: `regime_switch_episode_count > 0` for a 100-episode v0_5 batch
- audit JSON: `action_outcome_inversion_count > 0` (same action, different effect)
- audit JSON: `hidden_label_leakage_count == 0`
- v0_4 generate() backward compat: all existing generator/collector tests pass
- `regime_switch_step` appears ONLY in evaluation_labels, never in public_obs or training_labels
- `test_forbidden_field_mirror_sync.py` GREEN (requires visibility.py pre-edit by user)

COMMIT_MESSAGE:
feat(data): v0_5 intra-episode regime switch generator and collector

Adds TextEpisodeSpec.regime_switch_step/hidden_regime_after, per-step
switch collection, BatchTargets.regime_switch_step (eval-only), and
audit script. v0_4 backward compat preserved. All sync tests green.

STOP_CONDITION:
STOP if:
1. `regime_switch_step` appears in `public_input`, `PublicObservation`, or `TrainingLabels`
2. `test_forbidden_field_mirror_sync.py` fails (regime_switch_step must be in FORBIDDEN_AGENT_FIELDS
   before this task runs — if not, STOP and report "visibility.py not updated yet")
3. v0_4 existing collector/generator tests fail
4. Any modification to paper_context_ref/, .claude/, or visibility.py
5. RESULT.md is not written on success

Dependencies: visibility.py must have `regime_switch_step` in FORBIDDEN_AGENT_FIELDS (user approval gate)
Checkpoint mapping: PHASE 2 (Checkpoint-2)
Required agent review: frcgw-data-leakage-auditor after merge
