TASK_NAME: TASK_1011_E5_eval_report

BACKGROUND:
FRCG-WM P3 evaluation phase.
- TASK_1007 (metrics + compute_budget) ✓
- TASK_1008 (baselines) ✓
- TASK_1009 (eval_runner + config + eval smoke script) ✓
- TASK_1010 (ablations + ablation_core.yaml + ablation runner) ✓

Now implement:
1. `src/frcgw/evaluation/reporter.py` — EvalReporter class that reads artifacts
   from outputs/runs/ and writes plans/P3_EVAL_GATE_REPORT.md
2. `tests/test_reporter.py` — unit tests

Source MDs:
- paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md §9 reporting
- paper_context_ref/14_TRD_TECHNICAL_REQUIREMENTS_DOCUMENT_v1.md SYS-REQ-009 (no fake numbers)
- paper_context_ref/13_CLAUDE_CODE_EXECUTION_ROADMAP_v1.md §10 CC-P3

GOAL:
Implement EvalReporter that reads metrics.json + ablation_results.json from outputs/runs/,
summarizes CC-P3-G1~G4 gate checks, and writes plans/P3_EVAL_GATE_REPORT.md.
FAKE NUMBERS ARE FORBIDDEN — reporter must only report values from artifact files.

FILES_ALLOWED:
src/frcgw/evaluation/reporter.py
src/frcgw/evaluation/__init__.py
tests/test_reporter.py

FILES_FORBIDDEN:
paper_context_ref/
.claude/
.mcp.json
.venv/
data/
outputs/
secrets/
.env
scripts/run_codex_task.ps1
src/frcgw/gui_env/
src/frcgw/logging/
src/frcgw/models/
src/frcgw/objectives/
src/frcgw/planning/
src/frcgw/training/
src/frcgw/schemas/
src/frcgw/data/
src/frcgw/text_env/
src/frcgw/evaluation/metrics.py
src/frcgw/evaluation/compute_budget.py
src/frcgw/evaluation/baselines.py
src/frcgw/evaluation/eval_runner.py
src/frcgw/evaluation/ablations.py

REQUIRED_IMPLEMENTATION:

### src/frcgw/evaluation/reporter.py

Module docstring citing:
  paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md §9
  paper_context_ref/14_TRD_TECHNICAL_REQUIREMENTS_DOCUMENT_v1.md SYS-REQ-009
  paper_context_ref/13_CLAUDE_CODE_EXECUTION_ROADMAP_v1.md §10

```python
class GateCheckResult:
    gate_id: str           # e.g. "CC-P3-G1"
    description: str
    passed: bool | None    # None if not enough data
    evidence: str          # human-readable evidence string from artifacts

class EvalReporter:
    """Reads eval artifacts and writes P3_EVAL_GATE_REPORT.md.

    SYS-REQ-009: NEVER write placeholder or manually typed numbers.
    All numbers must be read from metrics.json / ablation_results.json artifacts.
    If artifacts are absent, write "DATA_MISSING" for that value — never 0.0 as proxy.
    """

    def __init__(
        self,
        eval_results_dir: str | Path,       # outputs/runs/p3_eval/
        ablation_results_dir: str | Path,    # outputs/runs/p3_ablations/
        report_output_path: str | Path,      # plans/P3_EVAL_GATE_REPORT.md
    ) -> None: ...

    def load_eval_results(self) -> list[dict]:
        """Load metrics.json. Raise FileNotFoundError if missing."""
        ...

    def load_ablation_results(self) -> list[dict]:
        """Load ablation_results.json. Raise FileNotFoundError if missing."""
        ...

    def check_gate_g1(self, eval_results: list[dict]) -> GateCheckResult:
        """CC-P3-G1: mean(recovery_delay) FRCG < VerifierOnly on text_id, 5 seeds.
        For P3 text baseline: compare VerifierOnlyAgent vs FrozenBaseAgent
        (FRCG full model not available in text-only phase; compare available agents).
        If VerifierOnlyAgent and FrozenBaseAgent results exist: check relationship.
        Returns passed=None if required data missing.
        """
        ...

    def check_gate_g2(self, eval_results: list[dict]) -> GateCheckResult:
        """CC-P3-G2: mean(progress_per_compute) VerifierOnly > UncertaintyGated on text_id.
        Check if VerifierOnlyAgent > UncertaintyGatedAgent for progress_per_compute.
        Returns passed=None if required data missing.
        """
        ...

    def check_gate_g3(self, ablation_results: list[dict]) -> GateCheckResult:
        """CC-P3-G3: persistence(no_control_grammar) > persistence(FrozenBase) on text_ood_grammar.
        Checks no_control_grammar ablation has higher wrong_control_grammar_persistence.
        Returns passed=None if required data missing.
        """
        ...

    def check_gate_g4(self, ablation_results: list[dict]) -> GateCheckResult:
        """CC-P3-G4: no_falsification shows lower falsification_precision_recall_f1
        AND higher false_planning_call_rate vs FrozenBase.
        Returns passed=None if required data missing.
        """
        ...

    def write_report(self) -> str:
        """Load artifacts, run gate checks, write plans/P3_EVAL_GATE_REPORT.md.
        Returns path to written report.

        Report format (must cite actual artifact paths):
          # P3 Evaluation Gate Report
          Generated: <timestamp>
          Eval artifacts: <eval_results_dir>/metrics.json
          Ablation artifacts: <ablation_results_dir>/ablation_results.json

          ## Gate Results
          | Gate | Status | Evidence |
          ...

          ## Metric Summary
          (tables from loaded artifacts, no manually typed numbers)

          ## Ablation Summary
          ...

          ## Compute Budget
          ...

          ## Failure Cases
          ...
        """
        ...
```

Also add a CLI entry point:
```python
def main() -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--eval-dir", default="outputs/runs/p3_eval")
    parser.add_argument("--ablation-dir", default="outputs/runs/p3_ablations")
    parser.add_argument("--output", default="plans/P3_EVAL_GATE_REPORT.md")
    args = parser.parse_args()

    reporter = EvalReporter(args.eval_dir, args.ablation_dir, args.output)
    try:
        path = reporter.write_report()
        print(f"[OK] report written: {path}")
        return 0
    except FileNotFoundError as e:
        print(f"[FAIL] artifact missing: {e}")
        print("Run scripts/03_eval_text_smoke.py and scripts/08_run_core_ablations.py first.")
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
```

REQUIRED_TESTS:

### tests/test_reporter.py

Use tmp_path fixtures to create synthetic metrics.json and ablation_results.json.

Synthetic metrics.json (list of EvaluationResult dicts):
```json
[
  {"agent_id": "VerifierOnlyAgent", "split": "text_id", "seed": 0,
   "metrics": {"recovery_delay": 2.5, "progress_per_compute": 0.15,
               "task_success_rate": 0.6, "normalized_return": 0.5,
               "wrong_control_grammar_persistence": 3.0,
               "failed_action_repetition_rate": 0.2,
               "falsification_precision_recall": {"precision": 0.7, "recall": 0.6, "f1": 0.65},
               "falsification_calibration": 0.1,
               "false_planning_call_rate": 0.3, "action_switch_delay": 2.0},
   "n_episodes": 33},
  {"agent_id": "UncertaintyGatedAgent", "split": "text_id", "seed": 0,
   "metrics": {"recovery_delay": 3.5, "progress_per_compute": 0.08,
               "task_success_rate": 0.5, "normalized_return": 0.4,
               "wrong_control_grammar_persistence": 4.0,
               "failed_action_repetition_rate": 0.3,
               "falsification_precision_recall": {"precision": 0.5, "recall": 0.4, "f1": 0.44},
               "falsification_calibration": 0.2,
               "false_planning_call_rate": 0.5, "action_switch_delay": 3.0},
   "n_episodes": 33},
  {"agent_id": "FrozenBaseAgent", "split": "text_id", "seed": 0,
   "metrics": {"recovery_delay": 4.0, "progress_per_compute": 0.05,
               "task_success_rate": 0.3, "normalized_return": 0.3,
               "wrong_control_grammar_persistence": 5.0,
               "failed_action_repetition_rate": 0.4,
               "falsification_precision_recall": {"precision": 0.0, "recall": 0.0, "f1": 0.0},
               "falsification_calibration": 0.4,
               "false_planning_call_rate": 0.0, "action_switch_delay": 5.0},
   "n_episodes": 33}
]
```

Synthetic ablation_results.json:
```json
[
  {"ablation_id": "no_control_grammar", "seed": 0, "split": "text_ood_grammar",
   "metrics": {"wrong_control_grammar_persistence": 6.0, "task_success_rate": 0.2}},
  {"ablation_id": "no_falsification", "seed": 0, "split": "text_ood_grammar",
   "metrics": {"falsification_precision_recall": {"f1": 0.0},
               "false_planning_call_rate": 0.8}}
]
```

Tests:
1. EvalReporter loads both artifact files from tmp_path
2. check_gate_g1: VerifierOnly.recovery_delay < FrozenBase.recovery_delay → passed=True
3. check_gate_g2: VerifierOnly.progress_per_compute > UncertaintyGated → passed=True
4. check_gate_g3: no_control_grammar persistence > FrozenBase persistence → passed=True
5. check_gate_g4: no_falsification f1 lower + false_planning higher → passed=True
6. write_report() creates plans/P3_EVAL_GATE_REPORT.md (use tmp_path for output)
7. Report file contains no literal string "DATA_MISSING" when data present
8. Report file contains no literal Python "None" where numeric values expected
9. EvalReporter raises FileNotFoundError when artifact files missing
   (not silently returning 0.0)
10. GateCheckResult.passed = None when required agent not in results

ACCEPTANCE_CRITERIA:
1. pytest tests/test_reporter.py -q → all pass, 0 failures
2. reporter.py does not hardcode any numeric thresholds as PASS/FAIL cutoffs
   (gate check is directional: A > B or A < B, no ≥25% threshold enforcement)
3. write_report() always reads numbers from artifact files — never hardcodes
4. Missing artifact → FileNotFoundError (not silent 0.0 substitution)
5. Report markdown contains ## Gate Results table with all 4 gates (G1~G4)
6. GateCheckResult.passed = None if data missing (not False — they're different)

COMMIT_MESSAGE:
feat(p3-eval-e5): eval reporter + P3_EVAL_GATE_REPORT writer

STOP_CONDITION:
Stop if reporter.py hardcodes any numeric value (like 0.25, 0.15) as a gate threshold.
Stop if write_report() silently substitutes 0.0 for missing artifact values.
Stop if GateCheckResult.passed is set to False when data is simply absent
  (must be None to distinguish "data missing" from "gate failed").
Stop if plans/P3_EVAL_GATE_REPORT.md contains manually typed numbers.
