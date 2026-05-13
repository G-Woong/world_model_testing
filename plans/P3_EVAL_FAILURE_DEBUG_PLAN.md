# P3 Evaluation Gate Failure Debug Plan

Generated: 2026-05-13
Branch: solo/p3-final-boss-cleared
Artifacts: outputs/runs/p3_eval/metrics.json, outputs/runs/p3_ablations/ablation_results.json
Gate Report: plans/P3_EVAL_GATE_REPORT.md

---

## Gate Results (from P3_EVAL_GATE_REPORT.md)

| Gate | Status | Root Cause |
|---|---|---|
| CC-P3-G1 | FAIL | recovery_delay=0.0 everywhere — data gap: recovery_timestamp=null |
| CC-P3-G2 | FAIL | No FRCG model agent; proxy comparison VerifierOnly vs UncertaintyGated shows wrong direction |
| CC-P3-G3 | FAIL | persistence=0.0 everywhere — data gap: hypothesis_update_timestamp=null |
| CC-P3-G4 | FAIL | f1=0.0 everywhere — no predicted_wrong from baseline agents; no FRCG model eval |

---

## Root Cause Analysis

### Blocker B1: Data Gap — Missing recovery/persistence timestamps

**Affected metrics**: `recovery_delay`, `wrong_control_grammar_persistence`

**Evidence**: `data/frcgw_text/v0_1/test_id.jsonl` — 165 steps checked:
- `evidence_timestamp`: 165 non-null ✓
- `recovery_timestamp`: 0 non-null ✗
- `hypothesis_update_timestamp`: 0 non-null ✗

**Cause**: P2 text data generator (`src/frcgw/text_env/`) created episodes where
`evaluation_labels.recovery_timestamp` and `evaluation_labels.hypothesis_update_timestamp`
are always null. These fields track the step index when an agent's hypothesis switches
(hypothesis_update) or when progress is recovered (recovery). The text environment
synthetic generator did not implement the hypothesis tracking logic.

**Impact**: CC-P3-G1 (recovery_delay) and CC-P3-G3 (persistence) gates cannot be
evaluated — both show 0.0 for all agents because the denominator metric has no data.

**Fix required**: Update `src/frcgw/text_env/` data generator to:
1. Track when `true_wrong_hypothesis` transitions from True → False (hypothesis_update_timestamp)
2. Track when `progress_delta > 0` first occurs after a wrong hypothesis step (recovery_timestamp)
3. Regenerate `data/frcgw_text/v0_1/` with these fields populated

### Blocker B2: Missing FRCG Model Agent Wrapper

**Affected gates**: CC-P3-G1, CC-P3-G2, CC-P3-G3, CC-P3-G4

**Evidence**: `src/frcgw/evaluation/baselines.py` only has heuristic baseline agents.
The `TextFRCGModel` (implemented in `src/frcgw/models/text_frcg_model.py`) is not
wrapped as an evaluation agent.

**Cause**: TASK_1007~1011 implemented metrics, baselines (heuristic), eval_runner,
ablations (heuristic wrappers), and reporter — but did not implement the FRCG model
agent wrapper that would run the actual neural model through the evaluator.

**Impact**:
- `predicted_wrong` per step = False everywhere → falsification_precision_recall f1 = 0.0
- G1/G2: compare FRCG vs VerifierOnly/UncertaintyGated → impossible without FRCG agent
- G3/G4: ablations compare against FRCG full model → impossible without FRCG agent

**Fix required**: Implement `src/frcgw/evaluation/frcg_agent.py` with:
```python
class TextFRCGModelAgent(BaselineAgent):
    baseline_id = "FRCG-FULL"
    def __init__(self, model: TextFRCGModel, checkpoint_path: str | None = None):
        self.model = model
        if checkpoint_path:
            self.model.load_state_dict(torch.load(checkpoint_path))
        self.falsification_scorer = ...  # use falsification.falsification_score
        self.planner = ...               # use planning.planner.plan_step

    def act(self, obs: PublicObservation, eval_labels: dict | None = None
           ) -> tuple[CandidateAction, ComputeBudgetLog]:
        # 1. model.forward(obs) → ModelOutput
        # 2. falsification_score → predicted_wrong, F_t
        # 3. decision_gate → plan or not
        # 4. if planning: propose alternatives, rollout, rewrite
        # 5. return (action, ComputeBudgetLog)
```

Also: run smoke train to generate a checkpoint at `outputs/runs/p3_train_smoke/`.

### Blocker B3: Missing text_ood_grammar Split

**Affected gate**: CC-P3-G3 (uses text_ood_grammar split)

**Evidence**: `data/frcgw_text/v0_1/manifest.json` only has:
`{"train": 132, "valid": 35, "test_id": 33}`

No `text_ood_grammar`, `text_noisy` splits exist.

**Cause**: P2 text data generator did not implement OOD splits.

**Impact**: CC-P3-G3 ablation comparison falls back to `test_id` via `_ALIAS`.
This is tolerable for now (proxy) but proper G3 requires OOD grammar episodes.

**Fix required** (lower priority than B1, B2):
- Extend P2 data generator to produce a `text_ood_grammar` shard (30+ episodes)
  where control grammar shifts mid-episode (test persistence sensitivity).

---

## Metrics That DO Show Meaningful Variation (infrastructure works)

These metrics work correctly with the current data and heuristic baselines:

| Metric | Observation |
|---|---|
| `task_success_rate` | All baselines = 1.0 (all episodes complete — proxy for "any progress") |
| `normalized_return` | ~1.0 for all (same reason) |
| `failed_action_repetition_rate` | BASE-001=0.50, BASE-009=0.125, BASE-014=0.143, BASE-012=0.196 (variation ✓) |
| `progress_per_compute` | BASE-001=0.228, BASE-003=0.114, BASE-005=0.047, BASE-009=0.026, BASE-012=0.090 (variation ✓) |
| `falsification_calibration` | 0.303 for all baselines (uniform wrong_prob=0.0 → calibrated at bin 0) |

The eval runner, metric functions, ablation wrappers, and reporter are all working correctly.

---

## Required Fixes (Prioritized)

### Fix F1 (CRITICAL): Populate recovery/persistence timestamps in text data

Files:
- `src/frcgw/text_env/` episode generator (investigate which file creates `evaluation_labels`)
- `data/frcgw_text/v0_1/` regeneration after fix (manifest must pass leakage+coverage gates)

Logic:
```python
# Per episode, track step-level:
# hypothesis_update_timestamp: first step where true_wrong_hypothesis flips False
#   (after being True for at least 1 step)
# recovery_timestamp: first step where progress_delta > 0
#   AND prior steps had true_wrong_hypothesis=True
```

Test: `evidence_timestamp` and `hypothesis_update_timestamp` non-null for at least
30% of steps where `true_wrong_hypothesis=True` exists.

### Fix F2 (CRITICAL): Implement TextFRCGModelAgent + run smoke checkpoint

New file: `src/frcgw/evaluation/frcg_agent.py`
Checkpoint: run `scripts/01_train_text_smoke.py` (or equivalent) → `outputs/runs/p3_train_smoke/`

The agent must:
- Set `predicted_wrong: bool` per step (from falsification_score > threshold)
- Return meaningful `ComputeBudgetLog.planning_calls` (> 0 when planning triggered)
- NOT read FORBIDDEN_AGENT_KEYS from obs

Test gate: `pytest tests/test_frcg_agent.py`

### Fix F3 (LOWER): Add text_ood_grammar shard

After F1: extend data generator to produce an `ood_grammar` shard (30+ episodes)
where grammar changes mid-episode. This enables proper G3 comparison.

---

## Interpretation: Scientific Claims vs Infrastructure

The current FAIL is **infrastructure-driven**, not a claim-level failure:

| FAIL gate | Cause | Scientific implication |
|---|---|---|
| G1 | recovery_timestamp null + no FRCG agent | UNKNOWN — cannot evaluate |
| G2 | no FRCG agent | UNKNOWN — cannot evaluate |
| G3 | hypothesis_update_timestamp null + no FRCG agent | UNKNOWN — cannot evaluate |
| G4 | no predicted_wrong + no FRCG agent | UNKNOWN — cannot evaluate |

Per `paper_context_ref/13_CLAUDE_CODE_EXECUTION_ROADMAP_v1.md` §10, CC-P3 gates
require the FRCG model to be evaluated. The evaluation infrastructure is now complete
(TASK_1007~1011 done, 227 pytest green), but the model+data components were not
part of those tasks.

**This is NOT** the "claim-level" failures described in §9.2:
- G3 does NOT demonstrate "grammar claim weak" yet — the ablation effect cannot be measured
- G4 does NOT demonstrate "falsification claim weak" yet — the metric is unmeasurable

---

## P4 Status

**P4 BLOCKED** per plan §10:
> `outputs/phase_gates/P3_EVAL.passed` does not exist → P4 entry forbidden.

---

## Next Steps (for user approval)

1. **F1**: Fix text episode generator to populate recovery/persistence timestamps.
   Regenerate `data/frcgw_text/v0_1/` (100 → 200 episodes, same scale, new timestamps).
   Run `pytest -q` + leakage audit.

2. **F2**: Implement `src/frcgw/evaluation/frcg_agent.py` (TextFRCGModelAgent).
   Run `scripts/01_train_text_smoke.py` to generate checkpoint.
   Evaluate FRCG agent against VerifierOnly and UncertaintyGated.
   Re-run `scripts/03_eval_text_smoke.py` + `scripts/08_run_core_ablations.py`.

3. **F3** (lower priority): Add `text_ood_grammar` shard after F1.

4. Re-run reporter: `python -m frcgw.evaluation.reporter` → new `plans/P3_EVAL_GATE_REPORT.md`.

5. Re-evaluate gates G1~G4 with real FRCG model comparisons.
   If PASS → issue `outputs/phase_gates/P3_EVAL.passed` → proceed to P4.
   If FAIL on G3/G4 after FRCG model eval → scientific claim re-examination per §9.2.

---

## Blockers Summary

| ID | Blocker | Priority | Fix |
|---|---|---|---|
| B1 | recovery_timestamp + hypothesis_update_timestamp null in all text data | CRITICAL | Fix text generator + regenerate data |
| B2 | No FRCG model agent wrapper | CRITICAL | Implement TextFRCGModelAgent + checkpoint |
| B3 | No text_ood_grammar split | MODERATE | Extend data generator |
