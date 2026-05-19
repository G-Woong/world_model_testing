TASK_NAME: TASK_LFD_008_robotics_ood_eval_harness

BACKGROUND:
FRCG-WM's core claim is text-env validated. This task adds a passive OOD probe
for robotics datasets (Open X-Embodiment / DROID schema) as an appendix result.

SCOPE LIMIT: This is EVAL-ONLY. No training, no backward pass, no weight updates.
Main claims are NOT based on this result. It is an appendix "passive OOD probe"
showing the detector generalizes to a different domain's action-effect patterns.

This task runs AFTER the core LFD is trained and evaluated (PHASE 9).
No LFD training happens in this task.

GOAL:
1. Implement a schema adapter for robotics episode format (Open X / DROID).
2. Run CUSUM + LFD inference (eval-only) on adapted episodes.
3. Report anomaly score distribution for in-distribution vs OOD conditions.
4. Output: appendix table of anomaly/surprise score distributions.

FILES_ALLOWED:
- src/frcgw/evaluation/robotics_ood_adapter.py  (new file)
- scripts/risk_hunt/run_robotics_ood_probe.py   (new file)
- tests/test_robotics_ood_adapter.py            (new file)

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
- src/frcgw/models/
- src/frcgw/objectives/
- src/frcgw/training/
- src/frcgw/planning/

REQUIRED_IMPLEMENTATION:
1. src/frcgw/evaluation/robotics_ood_adapter.py:

   @dataclass
   class RoboticsStepObservation:
     """Schema adapter for Open X-Embodiment / DROID episode step."""
     step_index: int
     action_type_str: str         # discretized from continuous action
     effect_type_str: str         # discretized from delta-state
     failed_action: bool          # from termination flag or stuck detection
     progress_delta: float        # normalized task progress

   def adapt_robotics_episode(
     episode_dict: dict,
     schema: str = "open_x",     # "open_x" | "droid"
   ) -> list[RoboticsStepObservation]:
     """Map robotics episode format to FRCG-WM step observations.
     
     NO forbidden fields are created. No hidden regime labels.
     Only public action-effect observations are extracted.
     """
     ...

   def run_cusum_probe(
     observations: list[RoboticsStepObservation],
     k: float = 0.5,
     h: float = 4.0,
   ) -> dict[str, any]:
     """Run CUSUM over robotics episode. Returns alarm_steps and S_t trace."""
     ...

   def run_lfd_probe(
     observations: list[RoboticsStepObservation],
     model: any,  # trained FalsificationDetectorHead
   ) -> dict[str, any]:
     """Run LFD inference over robotics episode. No gradient, eval-only."""
     ...

2. scripts/risk_hunt/run_robotics_ood_probe.py:
   - CLI: `--robotics-data-path`, `--schema`, `--model-checkpoint`, `--out-dir`
   - Outputs: JSON with anomaly score distributions + appendix table

REQUIRED_TESTS:
- tests/test_robotics_ood_adapter.py:
  - `test_adapt_open_x_no_forbidden_fields`: no FORBIDDEN_AGENT_FIELDS in output
  - `test_adapt_produces_valid_observations`: all fields within expected ranges
  - `test_no_backward_pass_in_lfd_probe`: torch.no_grad() verified
  - `test_cusum_probe_returns_alarm_steps`
  - `test_schema_adapter_handles_missing_fields_gracefully`

ACCEPTANCE_CRITERIA:
- No backward pass in any probe function (eval-only)
- No forbidden field in RoboticsStepObservation
- Main claim paper sections do NOT cite robotics probe results
- All listed tests pass

COMMIT_MESSAGE:
feat(eval): robotics passive OOD probe adapter (appendix-only)

Adds schema adapter for Open X / DROID episodes, CUSUM + LFD eval-only
probe, and appendix report script. No training; no main claim dependency.

STOP_CONDITION:
STOP if:
1. Any backward() call exists in this code
2. Robotics probe results are cited in main claim sections
3. Hidden regime labels are derived from robotics data
4. TASK_LFD_003 + TASK_LFD_001 not complete (detectors needed)

Dependencies: TASK_LFD_003 (LFD model), TASK_LFD_001 (CUSUM baseline)
Checkpoint mapping: PHASE 8 (Checkpoint-8, appendix only)
