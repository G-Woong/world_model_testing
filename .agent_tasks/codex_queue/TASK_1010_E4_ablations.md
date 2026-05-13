TASK_NAME: TASK_1010_E4_ablations

BACKGROUND:
FRCG-WM P3 evaluation phase.
- TASK_1007 (metrics + compute_budget) ✓
- TASK_1008 (baselines) ✓
- TASK_1009 (eval_runner + config + script) ✓

Now implement:
1. `src/frcgw/evaluation/ablations.py` — 12 ablation configurations + masking interface
2. `configs/ablation_core.yaml` — populate with ablation definitions + expected_collapse
3. `scripts/08_run_core_ablations.py` — replace NotImplementedError

Source MDs:
- paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md §8 ABL-001~042 (esp. CRITICAL ones)
- paper_context_ref/15_TDD_TECHNICAL_DESIGN_DOCUMENT_v1.md §15 lines 1011~1029

12 required ablation IDs (from configs/ablation_core.yaml):
  no_control_grammar, merged_regime_control_grammar, collapsed_latent,
  no_falsification, uncertainty_instead_of_falsification, no_alternative_hypothesis,
  random_alternative, no_rollout, no_rewrite, always_plan_no_gate,
  no_progress_reward, no_compute_penalty

For text-only P3 evaluation, "ablating" is done by config-driven masking on the
EvaluationRunner or baseline agents — NOT by re-training (model checkpoint is frozen).
Ablations simulate the effect of removing a component by overriding agent behavior.

GOAL:
Implement ablations.py with AblationConfig dataclass + ablation_registry dict +
apply_ablation() function. Populate ablation_core.yaml. Implement ablation runner script.

FILES_ALLOWED:
src/frcgw/evaluation/ablations.py
src/frcgw/evaluation/__init__.py
configs/ablation_core.yaml
scripts/08_run_core_ablations.py
tests/test_ablation_runner.py

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

REQUIRED_IMPLEMENTATION:

### src/frcgw/evaluation/ablations.py

Module docstring citing:
  paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md §8 ABL-001~042
  paper_context_ref/15_TDD_TECHNICAL_DESIGN_DOCUMENT_v1.md §15 lines 1011~1029

```python
from dataclasses import dataclass
from typing import Any

@dataclass
class AblationConfig:
    ablation_id: str               # e.g. "no_control_grammar"
    tdd_ref: str                   # e.g. "ABL-002"
    severity: str                  # "CRITICAL" or "standard"
    description: str
    expected_collapse: dict[str, str]
    # e.g. {"wrong_control_grammar_persistence": "increase",
    #        "task_success_rate_ood_grammar": "decrease"}
    masking: dict[str, Any]
    # Masking rules used by apply_ablation() to override agent behavior:
    # e.g. {"disable_grammar_head": True} or {"randomize_alternative": True}
```

ABLATION_REGISTRY: dict[str, AblationConfig] — all 12 ablations

```python
def apply_ablation(
    agent: Any,
    ablation_config: AblationConfig,
) -> Any:
    """Return a wrapped agent that behaves as per the ablation masking rules.

    For P3 text-only evaluation, masking is simulated via agent wrapper classes
    (not weight zeroing). Each ablation replaces specific decisions with
    ablated behavior:
      - no_control_grammar: agent ignores grammar scoring, uses uniform random action
      - no_falsification: agent never triggers planning on falsification signal
      - no_alternative_hypothesis: agent always uses first/current hypothesis
      - no_rollout: agent skips rollout, uses 0 rollout_steps
      - no_rewrite: agent returns original action without rewriting
      - always_plan_no_gate: agent always plans (no decision gate)
      - no_compute_gate: same as always_plan_no_gate but labels differently
      - no_progress_reward: agent does not use progress signal for scoring
      - uncertainty_instead_of_falsification: uses uncertainty score instead of F_t
      - random_alternative: picks random alternative hypothesis
      - merged_regime_control_grammar: treats regime and grammar as identical
      - collapsed_latent: uses zero-ed latent state representation

    Implementation: return a subclass/wrapper of BaselineAgent (from baselines.py)
    that overrides act() to simulate the ablation. The wrapper stores ablation_id.
    """
    ...
```

Define wrapper classes for each of the 12 ablations as inner classes or top-level.
These wrappers subclass the most appropriate BaselineAgent and override act() to
enforce the ablation. They all must:
- Have .ablation_id attribute = ablation_config.ablation_id
- Return (CandidateAction, ComputeBudgetLog) from act()
- NEVER read FORBIDDEN_AGENT_KEYS from obs

### configs/ablation_core.yaml

Replace P0 skeleton with:
```yaml
version: 1
phase: CC-P3
source_docs:
  - paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md
  - paper_context_ref/13_CLAUDE_CODE_EXECUTION_ROADMAP_v1.md
  - paper_context_ref/14_TRD_TECHNICAL_REQUIREMENTS_DOCUMENT_v1.md
  - paper_context_ref/15_TDD_TECHNICAL_DESIGN_DOCUMENT_v1.md

seeds: [0, 1, 2, 3, 4]
split: text_ood_grammar    # primary split for ablation testing (OOD tests grammar sensitivity)
splits:
  - text_id
  - text_ood_grammar
  - text_noisy
report_path: outputs/runs/p3_ablations/
compute_budget:
  planning_calls_cap: 5
  rollout_steps_cap: 10
ablations:
  - id: no_control_grammar
    tdd_ref: ABL-002
    severity: CRITICAL
    description: "Remove control-grammar head; agent uses uniform random action selection"
    expected_collapse:
      wrong_control_grammar_persistence: increase
      task_success_rate_text_ood_grammar: decrease
  - id: merged_regime_control_grammar
    tdd_ref: ABL-003
    severity: CRITICAL
    description: "Merge regime and grammar representations"
    expected_collapse:
      task_success_rate_text_ood_grammar: decrease
  - id: collapsed_latent
    tdd_ref: ABL-006
    severity: CRITICAL
    description: "Use zero/uniform latent representation"
    expected_collapse:
      falsification_precision_recall_f1: decrease
  - id: no_falsification
    tdd_ref: ABL-016
    severity: CRITICAL
    description: "Remove falsification scoring; agent never detects wrong hypothesis"
    expected_collapse:
      falsification_precision_recall_f1: decrease
      false_planning_call_rate: increase
  - id: uncertainty_instead_of_falsification
    tdd_ref: ABL-023
    severity: CRITICAL
    description: "Replace falsification with uncertainty threshold"
    expected_collapse:
      false_planning_call_rate: increase
  - id: no_alternative_hypothesis
    tdd_ref: ABL-024
    severity: CRITICAL
    description: "No alternative hypothesis proposal; always uses current grammar"
    expected_collapse:
      recovery_delay: increase
      task_success_rate: decrease
  - id: random_alternative
    tdd_ref: ABL-025
    severity: standard
    description: "Pick random alternative hypothesis instead of proposed"
    expected_collapse:
      recovery_delay: increase
  - id: no_rollout
    tdd_ref: ABL-026
    severity: standard
    description: "Skip rollout; use 0 rollout steps in planning"
    expected_collapse:
      task_success_rate: decrease
  - id: no_rewrite
    tdd_ref: ABL-035
    severity: CRITICAL
    description: "Skip action-interface rewrite"
    expected_collapse:
      failed_action_repetition_rate: increase
      action_switch_delay: increase
  - id: always_plan_no_gate
    tdd_ref: ABL-034
    severity: CRITICAL
    description: "Always plan; no decision gate"
    expected_collapse:
      progress_per_compute: decrease
      false_planning_call_rate: increase
  - id: no_progress_reward
    tdd_ref: ABL-019
    severity: standard
    description: "Remove progress signal from scoring"
    expected_collapse:
      progress_per_compute: decrease
  - id: no_compute_gate
    tdd_ref: ABL-033
    severity: CRITICAL
    description: "No compute gate; always allocate full budget"
    expected_collapse:
      false_planning_call_rate: increase
      progress_per_compute: decrease
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
notes: "CC-P3 ablation config. CRITICAL ablations must show expected_collapse; else claim blocked."
```

### scripts/08_run_core_ablations.py

Replace NotImplementedError with:
```python
def main() -> int:
    parser = argparse.ArgumentParser(description="Run core ablations for FRCG model.")
    parser.add_argument("--config", required=True)
    parser.add_argument("--split", default=None)
    args = parser.parse_args()

    import yaml, json
    from pathlib import Path
    from frcgw.evaluation.eval_runner import EvaluationRunner
    from frcgw.evaluation.ablations import ABLATION_REGISTRY, apply_ablation
    from frcgw.evaluation.baselines import FrozenBaseAgent

    config = yaml.safe_load(Path(args.config).read_text())
    if args.split:
        config["split"] = args.split

    manifest_path = Path("data/frcgw_text/v0_1/manifest.json")
    if not manifest_path.exists():
        print(f"[SKIP] manifest not found: {manifest_path}")
        return 0

    manifest = json.loads(manifest_path.read_text())
    split = config.get("split", "text_ood_grammar")
    shard_path = _find_shard(manifest, split)
    if shard_path is None:
        print(f"[SKIP] no shard for split={split}")
        return 0

    runner = EvaluationRunner(config)
    report_dir = Path(config.get("report_path", "outputs/runs/p3_ablations"))
    report_dir.mkdir(parents=True, exist_ok=True)

    all_results = []
    base_agent = FrozenBaseAgent()
    for ablation_id, abl_config in ABLATION_REGISTRY.items():
        ablated_agent = apply_ablation(base_agent, abl_config)
        for seed in config.get("seeds", [0]):
            ablated_agent.reset() if hasattr(ablated_agent, 'reset') else None
            result = runner.run(ablated_agent, shard_path, split, seed)
            result_dict = {
                "ablation_id": ablation_id,
                "seed": seed,
                "split": split,
                "metrics": result.metrics,
            }
            all_results.append(result_dict)

    import json as json_mod
    out_path = report_dir / "ablation_results.json"
    out_path.write_text(json_mod.dumps(all_results, indent=2))
    print(f"[OK] ablation results written: {out_path}")
    return 0

def _find_shard(manifest: dict, split: str) -> str | None:
    for shard in manifest.get("shards", []):
        if shard.get("split") == split:
            return shard.get("path")
    return None
```

REQUIRED_TESTS:

### tests/test_ablation_runner.py

1. ABLATION_REGISTRY has all 12 ablation IDs
2. Each AblationConfig has ablation_id, tdd_ref, severity, expected_collapse, masking
3. CRITICAL ablations: no_control_grammar, collapsed_latent, no_falsification,
   uncertainty_instead_of_falsification, no_alternative_hypothesis, no_rewrite,
   always_plan_no_gate, no_compute_gate — all have severity="CRITICAL"
4. apply_ablation(FrozenBaseAgent(), config) returns an object with act() method
5. Ablated agent act() returns (CandidateAction, ComputeBudgetLog)
6. Ablated agent does not read FORBIDDEN_AGENT_KEYS from obs
7. expected_collapse directions are valid strings: "increase" or "decrease"
8. scripts/08_run_core_ablations.py --config configs/ablation_core.yaml runs without
   NotImplementedError (may skip if data absent)

ACCEPTANCE_CRITERIA:
1. pytest tests/test_ablation_runner.py -q → all pass, 0 failures
2. ABLATION_REGISTRY contains exactly 12 entries matching ablation_core.yaml
3. All CRITICAL ablations are marked severity="CRITICAL"
4. apply_ablation() returns valid agent with act() and ablation_id attribute
5. configs/ablation_core.yaml has no null values (seeds, split, ablations all populated)
6. scripts/08_run_core_ablations.py no longer raises NotImplementedError

COMMIT_MESSAGE:
feat(p3-eval-e4): ablation configs + masking wrappers + ablation runner script

STOP_CONDITION:
Stop if any ablation wrapper reads FORBIDDEN_AGENT_KEYS from obs.
Stop if expected_collapse direction is anything other than "increase" or "decrease".
Stop if any CRITICAL ablation is missing from ABLATION_REGISTRY.
Stop if configs/ablation_core.yaml still has null values for seeds or ablations list.
