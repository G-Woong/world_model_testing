TASK_NAME: TASK_1009_E3_eval_runner

BACKGROUND:
FRCG-WM P3 evaluation phase.
- TASK_1007 (metrics + compute_budget) ✓
- TASK_1008 (baselines) ✓

Now implement:
1. `src/frcgw/evaluation/eval_runner.py` — EvaluationRunner class
2. `configs/eval_text.yaml` — populate all null values
3. `scripts/03_eval_text_smoke.py` — replace NotImplementedError with real runner call

Source MDs:
- paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md §7 CM-001~CM-012 (compute-match)
- paper_context_ref/11_MODEL_DATASET_SCALE_AND_TRAINING_BUDGET_v1.md (seeds, episode counts)
- paper_context_ref/15_TDD_TECHNICAL_DESIGN_DOCUMENT_v1.md §15 lines 1044~1058
- paper_context_ref/13_CLAUDE_CODE_EXECUTION_ROADMAP_v1.md §10

Data:
- data/frcgw_text/v0_1/manifest.json has 200 episodes: train 132 / valid 35 / test_id 33
- Episode JSONL shards in data/frcgw_text/v0_1/
- TextStepDataset in src/frcgw/data/text_dataset.py for loading
- BatchTargets has the label fields (training-only — NOT inference input)

GOAL:
Implement EvaluationRunner that runs a model/agent on a text dataset split,
computes all 10 metrics, and writes results to outputs/runs/p3_eval/.
Also update configs/eval_text.yaml and scripts/03_eval_text_smoke.py.

FILES_ALLOWED:
src/frcgw/evaluation/eval_runner.py
src/frcgw/evaluation/__init__.py
configs/eval_text.yaml
scripts/03_eval_text_smoke.py
tests/test_eval_runner.py

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

REQUIRED_IMPLEMENTATION:

### configs/eval_text.yaml

Replace all null values with:
```yaml
version: 1
phase: CC-P3
source_docs:
  - paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md
  - paper_context_ref/11_MODEL_DATASET_SCALE_AND_TRAINING_BUDGET_v1.md
  - paper_context_ref/13_CLAUDE_CODE_EXECUTION_ROADMAP_v1.md
  - paper_context_ref/14_TRD_TECHNICAL_REQUIREMENTS_DOCUMENT_v1.md
  - paper_context_ref/15_TDD_TECHNICAL_DESIGN_DOCUMENT_v1.md

seeds: [0, 1, 2, 3, 4]
model_ckpt: null        # runner will create a fresh tiny model if null
split: text_id          # primary split; text_ood_grammar and text_noisy also supported
splits:
  - text_id
  - text_ood_grammar
  - text_noisy
metrics:
  - task_success_rate
  - normalized_return
  - wrong_control_grammar_persistence
  - failed_action_repetition_rate
  - recovery_delay
  - falsification_precision_recall
  - falsification_calibration
  - progress_per_compute
  - false_planning_call_rate
  - action_switch_delay
baselines:
  - FrozenBaseAgent
  - ReactiveAgent
  - RetryAfterFailureAgent
  - VerifierOnlyAgent
  - NextStateWMOnlyAgent
  - AlwaysPlanAgent
  - UncertaintyGatedAgent
  - RandomAlternativePlannerAgent
compute_budget:
  planning_calls_cap: 5       # CM-001: same cap for FRCG, uncertainty-gated, always-plan, verifier-only
  rollout_steps_cap: 10       # CM-002: same cap for FRCG, next-state-WM-only
  max_candidates_per_call: 4  # CM-006 proxy
report_path: outputs/runs/p3_eval/
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
notes: "CC-P3 eval config. Thresholds from 04.md:500~510 are reference only, not hard gates."
```

### src/frcgw/evaluation/eval_runner.py

Module docstring citing:
  paper_context_ref/15_TDD_TECHNICAL_DESIGN_DOCUMENT_v1.md §15 lines 1044~1058
  paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md §7

```python
class EvaluationResult:
    agent_id: str
    split: str
    seed: int
    metrics: dict[str, float | dict]   # metric_name -> value
    compute_log: ComputeBudgetLog       # aggregated across all episodes
    n_episodes: int
    report_path: str | None

class EvaluationRunner:
    def __init__(self, config: dict) -> None:
        # Load config fields: seeds, splits, metrics, compute_budget, report_path
        # Validate forbidden_fields are not in config["metrics"]
        ...

    def run(
        self,
        agent: "BaselineAgent | Any",   # BaselineAgent or FRCG model wrapper
        dataset_path: str | Path,        # path to JSONL shard
        split: str,
        seed: int,
    ) -> EvaluationResult:
        # 1. Set random seed
        # 2. Load episodes from dataset_path JSONL
        # 3. For each episode:
        #    a. Build PublicObservation from episode steps
        #    b. assert_no_hidden_labels_in_input on agent observation
        #    c. Call agent.act(obs) → (action, compute_log_step)
        #    d. Collect episode-level episode_result dict
        # 4. Compute all 10 metrics from collected episodes
        # 5. Aggregate ComputeBudgetLog across all episodes
        # 6. Return EvaluationResult
        ...

    def run_all_baselines(
        self,
        baseline_agents: list["BaselineAgent"],
        dataset_path: str | Path,
        split: str,
    ) -> list[EvaluationResult]:
        results = []
        for seed in self._seeds:
            for agent in baseline_agents:
                agent.reset()
                results.append(self.run(agent, dataset_path, split, seed))
        return results

    def write_report(self, results: list[EvaluationResult], output_dir: str | Path) -> str:
        # Write metrics.json + summary.txt to output_dir/
        # Return path to metrics.json
        # NEVER write placeholder numbers — only values from EvaluationResult.metrics
        ...
```

Episode building from JSONL:
Each episode line in the JSONL has "steps" list. For each step:
  public_input = build PublicObservation from step["public_input"] (already stored)
  eval_labels = step.get("eval_labels") or {}  (for metric scoring, NOT agent obs)
  targets = step.get("targets") or {}          (training labels, NOT agent obs)

Agent receive only PublicObservation. eval_labels and targets are held separately for
metric computation after act() returns.

### scripts/03_eval_text_smoke.py

Replace NotImplementedError with:
```python
def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate text-only FRCG model.")
    parser.add_argument("--config", required=True)
    parser.add_argument("--split", default=None)
    parser.add_argument("--output-dir", default=None)
    args = parser.parse_args()

    import yaml
    from pathlib import Path
    from frcgw.evaluation.eval_runner import EvaluationRunner
    from frcgw.evaluation.baselines import (
        FrozenBaseAgent, ReactiveAgent, RetryAfterFailureAgent,
        VerifierOnlyAgent, NextStateWMOnlyAgent, AlwaysPlanAgent,
        UncertaintyGatedAgent, RandomAlternativePlannerAgent,
    )

    config = yaml.safe_load(Path(args.config).read_text())
    if args.split:
        config["split"] = args.split
    if args.output_dir:
        config["report_path"] = args.output_dir

    runner = EvaluationRunner(config)

    # Load dataset path from manifest
    manifest_path = Path("data/frcgw_text/v0_1/manifest.json")
    if not manifest_path.exists():
        print(f"[SKIP] manifest not found: {manifest_path}")
        return 0

    import json
    manifest = json.loads(manifest_path.read_text())
    split = config.get("split", "text_id")
    shard_path = _find_shard(manifest, split)
    if shard_path is None:
        print(f"[SKIP] no shard for split={split}")
        return 0

    agents = [
        FrozenBaseAgent(), ReactiveAgent(), RetryAfterFailureAgent(),
        VerifierOnlyAgent(), NextStateWMOnlyAgent(), AlwaysPlanAgent(),
        UncertaintyGatedAgent(), RandomAlternativePlannerAgent(),
    ]
    results = runner.run_all_baselines(agents, shard_path, split)
    report_dir = Path(config.get("report_path", "outputs/runs/p3_eval"))
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = runner.write_report(results, report_dir)
    print(f"[OK] eval report written: {report_path}")
    return 0

def _find_shard(manifest: dict, split: str) -> str | None:
    for shard in manifest.get("shards", []):
        if shard.get("split") == split:
            return shard.get("path")
    return None
```

REQUIRED_TESTS:

### tests/test_eval_runner.py

Use a minimal synthetic JSONL fixture (2 episodes, 3 steps each) created in tmp_path.

Tests:
1. EvaluationRunner loads config without error
2. run() with FrozenBaseAgent on synthetic JSONL returns EvaluationResult
3. EvaluationResult.metrics keys include all 10 metric names
4. assert_no_hidden_labels_in_input is called per episode step (verify forbidden key
   raises AssertionError when injected into observation)
5. write_report() creates metrics.json in output dir
6. metrics.json contains no placeholder None values for numeric metrics
   (all values are float or dict-of-float)
7. run_all_baselines() returns list of EvaluationResult

Synthetic JSONL format per episode:
```json
{"episode_id": "ep_0", "steps": [
  {"step_index": 0, "public_input": {"instruction": "click button",
    "history_public": [], "candidate_actions_public": [
      {"action_id": "a1", "action_type": "click", "action_params": {}}]},
   "eval_labels": {"true_wrong_hypothesis": false, "evidence_timestamp": null,
     "hypothesis_update_timestamp": null, "recovery_timestamp": null},
   "targets": {"progress_delta": 0.1, "true_failed_action": false,
     "failure_reason": null, "true_regime": "r0",
     "true_control_grammar": "g0", "true_change_point": "none",
     "true_reveal_vs_shift": "none", "true_action_effect_type": "click_effect",
     "recovery_action_id": null, "valid_hypothesis_switch": null},
   "predicted_wrong": false, "wrong_prob": 0.1, "rewrite_timestamp": null,
   "planning_events": []}
]}
```

ACCEPTANCE_CRITERIA:
1. pytest tests/test_eval_runner.py -q → all pass, 0 failures
2. EvaluationRunner.run() never passes forbidden fields to agent.act()
3. write_report() produces metrics.json with real computed values (not None)
4. scripts/03_eval_text_smoke.py --config configs/eval_text.yaml runs without
   NotImplementedError (may print [SKIP] if data not present — that's OK)
5. configs/eval_text.yaml has no null values except model_ckpt

COMMIT_MESSAGE:
feat(p3-eval-e3): eval runner + eval_text config + eval smoke script

STOP_CONDITION:
Stop if EvaluationRunner passes targets or eval_labels as part of agent.act() obs arg.
Stop if metrics.json contains Python None (use 0.0 for missing/empty metrics).
Stop if configs/eval_text.yaml still has null for seeds, splits, or metrics.
Stop if scripts/03_eval_text_smoke.py still raises NotImplementedError.
