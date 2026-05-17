TASK_NAME: STEP3_lr_wireup
SANDBOX_MODE: bypass

BACKGROUND:
STEP 2 real eval runner has BLOCKED metrics for falsification_precision_recall and
falsification_calibration. Two root causes:

RC-5: frcg_agent.py L95-96:
  self._last_wrong_prob = 1.0 - max_grammar_prob
  self._last_predicted_wrong = max_grammar_prob < self._confidence_threshold
  
  This uses a confidence PROXY (1 - max P(grammar)). The correct logic is:
  predicted_wrong = (F_t > tau_f)
  where F_t is already computed by text_frcg_plan() and available as plan_meta.F_t

RC-6: scripts/10_run_lr_real_eval.py L304:
  "tau_f": None  # hardcoded

Task 3 (this task) fixes both with minimal surgical changes:
1. frcg_agent.py: predicted_wrong = F_t > tau_f; wrong_prob = sigmoid(F_t - tau_f)
2. 10_run_lr_real_eval.py: tau_f lifted from agent._last_tau_f
3. configs/lr_eval_real_v0_2.yaml: new config pointing to v0_2 dataset
4. 6 new tests + regression validation

Key source files:
- src/frcgw/evaluation/frcg_agent.py (TextFRCGModelAgent.act(), lines 73-119)
- scripts/10_run_lr_real_eval.py (_attach_trace_records, lines ~295-316)
- src/frcgw/planning/planner.py (text_frcg_plan -> plan_meta.F_t)
- src/frcgw/planning/decision_gate.py (GateConfig.tau_f)
- docs/orchestration/lr_alignment/19_step3_dataset_backfill_plan.md §7 (LR wire-up design)

GOAL:
1. Patch frcg_agent.py act() so predicted_wrong uses F_t > tau_f (not max_grammar_prob proxy)
2. Propagate tau_f into _last_tau_f attribute for tracing
3. Patch 10_run_lr_real_eval.py _attach_trace_records to lift tau_f
4. Create configs/lr_eval_real_v0_2.yaml pointing to v0_2 dataset
5. Create tests/test_step3_lr_trace_contract.py (6 new tests)
6. Verify existing tests/test_lr_real_eval_runner.py (14 tests) still pass

FILES_ALLOWED:
- src/frcgw/evaluation/frcg_agent.py
- scripts/10_run_lr_real_eval.py
- configs/lr_eval_real_v0_2.yaml
- tests/test_step3_lr_trace_contract.py
- tests/test_lr_real_eval_runner.py

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
- src/frcgw/schemas/step_schema.py
- src/frcgw/evaluation/eval_runner.py
- src/frcgw/evaluation/metrics.py
- src/frcgw/evaluation/baselines.py
- src/frcgw/text_env/collector.py
- src/frcgw/text_env/state.py
- src/frcgw/text_env/generator.py
- scripts/09_run_lr_eval.py
- configs/lr_eval_core.yaml
- configs/lr_eval_real.yaml
- configs/dataset_v0_2.yaml
- .gitignore
- .self_evolving_memory/hooks/hook_execution_log.md
- docs/orchestration/AGENT_TEAMS_ROLLOUT_PLAN.md
- docs/orchestration/session_reports/2026-05/2026-05-17_precompact_handoff.md
- plans/PHASE_PROGRESS.md

REQUIRED_IMPLEMENTATION:

### 1. src/frcgw/evaluation/frcg_agent.py

Add module-level helper function (before the class definition):
```python
import math

def _sigmoid(x: float) -> float:
    """Numerically stable sigmoid with ±50 clamp."""
    x = max(-50.0, min(50.0, x))
    return 1.0 / (1.0 + math.exp(-x))
```

In __init__, add new attribute after `_last_wrong_prob`:
```python
self._last_tau_f: float = self.gate_config.tau_f
```

In reset(), add:
```python
self._last_tau_f = self.gate_config.tau_f
```

In act(), replace lines 95-107 (the wrong_prob/predicted_wrong + F_t setting):

CURRENT (lines 95-107):
```python
            self._last_wrong_prob = 1.0 - max_grammar_prob
            self._last_predicted_wrong = max_grammar_prob < self._confidence_threshold

            action, plan_meta = text_frcg_plan(
                obs,
                self._step_idx,
                candidates,
                self.model,
                self._planner_state,
                plan_gate_config,
            )

        self._last_F_t = float(plan_meta.F_t)
```

AFTER (move F_t assignment before predicted_wrong, use F_t > tau_f):
```python
            action, plan_meta = text_frcg_plan(
                obs,
                self._step_idx,
                candidates,
                self.model,
                self._planner_state,
                plan_gate_config,
            )

        self._last_F_t = float(plan_meta.F_t)
        tau_f = float(self.gate_config.tau_f)
        self._last_tau_f = tau_f
        self._last_predicted_wrong = self._last_F_t > tau_f
        self._last_wrong_prob = _sigmoid(self._last_F_t - tau_f)
```

IMPORTANT: The `_confidence_threshold` attribute and `max_grammar_prob` computation 
MUST be kept in the base class for now, but MUST NOT be used for predicted_wrong in 
TextFRCGModelAgent. Do NOT remove _confidence_threshold. Reason: ABL-023 
(uncertainty_instead_of_falsification) and ABL-022 (no_falsification_score_gate) 
may be subclasses or use this attribute for their distinct uncertainty proxy.
If these are subclasses, their act() overrides must continue to work after this refactor.
Do NOT change their behavior.

After the patch, add a marker comment:
    # _confidence_threshold kept for ABL-022/ABL-023 subclass compatibility
    # predicted_wrong now uses F_t > tau_f (paper contract: MET-FALS-001/002)

Add property:
```python
@property
def last_tau_f(self) -> float:
    return self._last_tau_f
```

### 2. scripts/10_run_lr_real_eval.py

In _TracingAgent.act() (the wrapper that calls self._agent.act() and records trace):
Find where the trace dict is built/updated and add:
```python
trace["tau_f"] = getattr(self._agent, "_last_tau_f", None)
```

In _attach_trace_records() (around line 304 where "tau_f": None is hardcoded):
Change:
```python
"tau_f": None,
```
To:
```python
"tau_f": trace.get("tau_f"),
```

### 3. configs/lr_eval_real_v0_2.yaml

```yaml
# Real episode-level eval config for v0.2 dataset
# Source: docs/orchestration/lr_alignment/19_step3_dataset_backfill_plan.md
run_mode: real_episode_eval
dataset_path: data/frcgw_text/v0_2/test_id.jsonl
split: test_id
seeds: [0, 1, 2]
out_dir: outputs/runs/p3_lr_real_eval_v0_2

agents:
  - id: FRCG-LR
    alias: FRCG-FULL
    class: TextFRCGModelAgent
    ckpt_path: null
  - id: ABL-017
    class: TextFRCGModelAgent
    ablation: no_intent_action_mapping
    ckpt_path: null
  - id: ABL-022
    class: TextFRCGModelAgent
    ablation: no_falsification_score_gate
    ckpt_path: null
  - id: ABL-023
    class: TextFRCGModelAgent
    ablation: uncertainty_instead_of_falsification
    ckpt_path: null
  - id: BASE-006
    class: VerifierRecoveryAgent
  - id: BASE-012-CATTS
    class: CATTSStyleUncertaintyGateAgent
  - id: BASE-015
    class: ComputeMatchedRandomAgent
  - id: BASE-026
    class: WACStyleConsequenceCorrectionAgent
  - id: BASE-027
    class: CUWMStyleCandidateSimulationAgent
  - id: BASE-028
    class: WebWorldStyleSearchAgent
  - id: BASE-003+008-VLAA
    class: VLAALoopHeuristicAgent

metrics:
  - task_success_rate
  - normalized_return
  - falsification_precision_recall
  - falsification_calibration
  - progress_per_compute
  - false_planning_call_rate
  - failed_action_repetition_rate
  - wrong_control_grammar_persistence
  - recovery_delay
  - action_switch_delay

compute_budget:
  planning_calls_cap: 10
  rollout_steps_cap: 30
  max_candidates_per_call: 8

forbidden_sources:
  - outputs/runs/p3_lr_smoke/metrics.json
  - outputs/runs/p3_ablations/ablation_results.json
  - outputs/runs/p3_lr_eval/metrics.json
  - outputs/runs/p3_lr_real_eval/metrics.json
```

REQUIRED_TESTS:

### tests/test_step3_lr_trace_contract.py (6 tests)

1. test_predicted_wrong_equals_F_t_greater_than_tau_f
   - Create TextFRCGModelAgent with GateConfig(tau_f=0.5)
   - Mock plan_meta.F_t = 0.7 (> tau_f)
   - Call act() with stub obs
   - Assert agent.last_predicted_wrong == True
   - Assert agent.last_F_t == 0.7

2. test_predicted_wrong_false_when_F_t_below_tau_f
   - Mock plan_meta.F_t = 0.3 (< tau_f=0.5)
   - Assert agent.last_predicted_wrong == False

3. test_wrong_prob_equals_sigmoid_of_F_t_minus_tau_f
   - Mock F_t=0.5, tau_f=0.5 → sigmoid(0) = 0.5
   - Assert abs(agent.last_wrong_prob - 0.5) < 1e-6

4. test_per_step_records_non_null_tau_f
   - Create _TracingAgent wrapping a stub agent with _last_tau_f=0.5
   - Call act() and check trace["tau_f"] == 0.5

5. test_per_step_records_f_t_from_plan_meta
   - Verify that per-step record["f_t"] reflects plan_meta.F_t (not proxy)
   - Use _attach_trace_records with trace that has f_t from model forward

6. test_manifest_uses_v0_2_dataset_path
   - Load configs/lr_eval_real_v0_2.yaml
   - Assert dataset_path == "data/frcgw_text/v0_2/test_id.jsonl"

7. test_abl023_predicted_wrong_does_not_collapse_to_full_model
   - If ABL-023 (UncertaintyInsteadOfFalsificationAgent or equivalent) is a subclass 
     of TextFRCGModelAgent, verify that its predicted_wrong comes from a DIFFERENT 
     path than TextFRCGModelAgent (e.g., confidence-space proxy, NOT F_t > tau_f).
   - If ABL-023 is NOT a subclass (separate class), skip this test with a skip marker 
     and comment: "ABL-023 is independent; no regression risk."
   - This test prevents silent ablation collapse where ABL-023 becomes identical to FRCG-FULL.

### tests/test_lr_real_eval_runner.py (existing, 14 tests)
All 14 existing tests must pass without modification.
Key tests that must still pass:
- test_predicted_wrong_equals_agent_last_predicted_wrong
- test_build_agent_dispatch_table_has_required_ids
- test_tracing_agent_wraps_predicted_wrong

ACCEPTANCE_CRITERIA:
1. pytest tests/test_step3_lr_trace_contract.py -q → 6 passed, 0 failed
2. pytest tests/test_lr_real_eval_runner.py -q → 14 passed, 0 failed (regression)
3. In frcg_agent.py: predicted_wrong is computed as (F_t > tau_f), NOT from max_grammar_prob
4. In frcg_agent.py: wrong_prob is computed as sigmoid(F_t - tau_f), NOT as (1 - max_grammar_prob)
5. agent._last_tau_f is set to gate_config.tau_f on every act() call
6. In 10_run_lr_real_eval.py: tau_f in per_step trace is lifted from agent (not hardcoded None)
7. configs/lr_eval_real_v0_2.yaml exists and points to data/frcgw_text/v0_2/test_id.jsonl
8. No FILES_FORBIDDEN path modified

COMMIT_MESSAGE:
feat(step3/task3): wire predicted_wrong = F_t > tau_f; lift tau_f into per_step trace

STOP_CONDITION:
Stop if tests/test_lr_real_eval_runner.py has any regression failure (was 14 passing).
Stop if predicted_wrong still uses max_grammar_prob proxy after fix.
Stop if any FILES_FORBIDDEN path is modified.
Stop if _sigmoid clamp is missing (overflow risk at extreme F_t values).
