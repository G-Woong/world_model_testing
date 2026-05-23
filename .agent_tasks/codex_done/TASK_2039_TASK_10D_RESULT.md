# Codex Task Report ??TASK_2039 TASK_10D
## Summary
BLOCKED. The task requires `evaluate_model` to return and persist metric keys that are not present in the current `src/fglc/repair/diagnose.py::CANONICAL_METRIC_KEYS`, while also requiring that returned metric keys be a subset of `CANONICAL_METRIC_KEYS` and forbidding edits outside `FILES_ALLOWED`.
## Files Changed
- `.agent_tasks/codex_done/TASK_2039_TASK_10D_RESULT.md`
## Commands Run
- `Get-Content -Raw AGENTS.md`
- `Get-Content -Raw .agent_tasks/codex_queue/TASK_2039_TASK_10D.md`
- `Get-ChildItem -Force src\\fglc\\training, src\\fglc\\evaluation, tests -ErrorAction SilentlyContinue | Select-Object FullName,Length,Mode`
- Read all `FILES_ALLOWED` paths; all were missing.
- `rg -n "class Encoder|class BeliefMemory|class GroupedDynamics|class RewardHead|class ValueHead|CANONICAL_METRIC_KEYS|SyntheticToyDataset|make_dataloaders" src tests`
- `git status --short`
- Read relevant existing files: `src/fglc/models/encoder.py`, `src/fglc/models/belief.py`, `src/fglc/models/dynamics.py`, `src/fglc/models/heads.py`, `src/fglc/data/state_only_dataset.py`, `src/fglc/data/dataloader.py`, `src/fglc/repair/diagnose.py`, `tests/test_fglc_base_wm.py`
## Tests Run (pass/fail)
- Not run. Implementation was blocked before edits because the task acceptance criteria are contradictory under the allowed file set.
## Evidence (log paths, metric values)
- Current `CANONICAL_METRIC_KEYS` contains `id_nll`, `train_nll`, `val_train_nll_gap`, `stagnant_epochs`, `kstep_nll_slope`, and `ood_id_nll_diff`.
- Current `CANONICAL_METRIC_KEYS` does not contain required output keys `val_nll`, `ood_mass_nll`, `ood_friction_nll`, `epoch`, `wall_clock_minutes`, or `vram_peak_mib`.
- `src/fglc/repair/diagnose.py`, where `CANONICAL_METRIC_KEYS` is defined, is not in `FILES_ALLOWED`.
## Risks / Open Questions
- To unblock, Claude Code should either add the required Stage 1 metric names to `CANONICAL_METRIC_KEYS` in an upstream task, or relax TASK_10D acceptance criterion 4 so operational artifact keys such as `epoch`, `wall_clock_minutes`, and `vram_peak_mib` are allowed outside `CANONICAL_METRIC_KEYS`.
## Patch Review Notes for Claude Code
- No implementation files were changed.
- Call graph mapped before stopping: planned trainer would call `Encoder.forward`, `BeliefMemory.forward`, `GroupedDynamics.forward`, `RewardHead.forward`, and `ValueHead.forward`; evaluator would call the trainer NLL evaluation helpers and compare keys against `CANONICAL_METRIC_KEYS`.
- Existing tests covering touched model APIs include `tests/test_fglc_base_wm.py`; required new trainer smoke tests could not be authored coherently without resolving the metric-key contract.
## Accept/Reject Recommendation
Reject/BLOCKED until the canonical metric key contract is made consistent with the required `metrics.json` schema or `src/fglc/repair/diagnose.py` is added to `FILES_ALLOWED`.
