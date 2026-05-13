TASK_NAME: TASK_1008_E2_baselines

BACKGROUND:
FRCG-WM P3 evaluation phase. TASK_1007 (eval metrics) is complete.
Now implement `src/frcgw/evaluation/baselines.py` — 9 baseline agent classes.

Baselines that must NOT disappear (codex_orchestration_rules.md §baselines):
BASE-001 FrozenBaseAgent, BASE-002 ReactiveAgent, BASE-003 RetryAfterFailureAgent,
BASE-005 VerifierOnlyAgent (CC-P3-G1 comparison), BASE-009 NextStateWMOnlyAgent,
BASE-010 AlwaysPlanAgent, BASE-012 UncertaintyGatedAgent (CC-P3-G2 comparison),
BASE-014 RandomAlternativePlannerAgent, BASE-016/017 Oracle agents (upper bounds).

Each agent must:
1. Implement `act(obs: PublicObservation, compute_log: ComputeBudgetLog | None) -> tuple[CandidateAction, ComputeBudgetLog]`
2. NEVER read FORBIDDEN_AGENT_KEYS from obs (see STOP_CONDITION)
3. Return a ComputeBudgetLog reflecting actual compute used

Source MDs:
- paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md §7 BASE-001~028
- paper_context_ref/15_TDD_TECHNICAL_DESIGN_DOCUMENT_v1.md §15 lines 993~1009

Key imports:
- from frcgw.schemas.step_schema import PublicObservation, CandidateAction
- from frcgw.evaluation.compute_budget import ComputeBudgetLog

GOAL:
Implement `src/frcgw/evaluation/baselines.py` with 9 baseline agent classes.
Write `tests/test_baselines.py`.

FILES_ALLOWED:
src/frcgw/evaluation/baselines.py
src/frcgw/evaluation/__init__.py
tests/test_baselines.py

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

REQUIRED_IMPLEMENTATION:

### src/frcgw/evaluation/baselines.py

Module docstring citing:
  paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md §7 BASE-001~028
  paper_context_ref/15_TDD_TECHNICAL_DESIGN_DOCUMENT_v1.md §15 lines 993~1009

FORBIDDEN_AGENT_KEYS = {
    "true_regime", "true_control_grammar", "true_change_point",
    "true_reveal_vs_shift", "true_wrong_hypothesis", "counterfactual_action_effects",
    "oracle_regime_action", "oracle_grammar_action", "oracle_best_action",
    "split_id", "ood_type", "template_id", "seed", "policy_id", "audit_metadata",
}

Abstract base:
```python
class BaselineAgent(ABC):
    baseline_id: str  # e.g. "BASE-001"

    @abstractmethod
    def act(
        self,
        obs: PublicObservation,
        eval_labels: dict | None = None,   # may be provided for oracle agents ONLY
    ) -> tuple[CandidateAction, ComputeBudgetLog]:
        ...

    def reset(self) -> None:
        """Reset any per-episode state."""
        pass
```

Implement 9 agents:

1. FrozenBaseAgent (BASE-001)
   - No planning, no rollout, no history use beyond instruction
   - Just pick obs.candidate_actions_public[0] or a "noop" CandidateAction
   - compute_log: planning_calls=0, rollout_steps=0, candidate_actions_scored=1,
     top_k_alternatives=0, wall_clock_seconds=0.0

2. ReactiveAgent (BASE-002)
   - Pick first candidate action (greedy), no state tracking
   - Same compute as FrozenBaseAgent

3. RetryAfterFailureAgent (BASE-003)
   - Track last action type in per-episode state (self._last_action_type)
   - If last action failed (tracked via history_public last item's effect_summary
     containing "fail"), try next candidate; else pick first candidate
   - compute_log: planning_calls=0, rollout_steps=0, candidate_actions_scored=2,
     top_k_alternatives=0, wall_clock_seconds=0.0
   - Implements reset() to clear self._last_action_type

4. VerifierOnlyAgent (BASE-005)
   - Simulates a "verifier": scores all candidate actions by a heuristic
     (length of action_id string as proxy, or uniform random with fixed seed)
   - planning_calls=1, rollout_steps=0 (no world model rollout),
     candidate_actions_scored=len(obs.candidate_actions_public),
     top_k_alternatives=0
   - Pick the top-scored candidate action
   - NOTE: This is the CC-P3-G1 comparison target. Its budget is compute-matched
     to FRCG on planning_calls but uses 0 rollout_steps.

5. NextStateWMOnlyAgent (BASE-009)
   - Simulates a generic next-state world model: for each candidate action, predict
     a "next state score" (uniform random with episode-seeded rng), pick highest
   - planning_calls=1, rollout_steps=len(obs.candidate_actions_public),
     candidate_actions_scored=len(obs.candidate_actions_public),
     top_k_alternatives=0

6. AlwaysPlanAgent (BASE-010)
   - Always plans regardless of falsification signal
   - Same heuristic scoring as VerifierOnlyAgent but called every step
   - planning_calls=1 per step, rollout_steps=0,
     candidate_actions_scored=len(obs.candidate_actions_public)

7. UncertaintyGatedAgent (BASE-012)
   - Plans only when uncertainty > threshold (simulated via
     len(obs.history_public) % 3 == 0 as a deterministic proxy)
   - When not planning: pick first candidate (0 planning budget)
   - When planning: same as VerifierOnlyAgent scoring
   - NOTE: This is the CC-P3-G2 comparison target

8. RandomAlternativePlannerAgent (BASE-014)
   - Like AlwaysPlanAgent but picks action uniformly at random from candidates
   - planning_calls=1, rollout_steps=0

9. OracleAgent (BASE-016/017 combined)
   - Accepts eval_labels dict in act()
   - If eval_labels is None → falls back to FrozenBaseAgent behavior
   - If eval_labels has "correct_hypothesis_id": uses it to pick action (last candidate
     if hypothesis id is truthy, else first)
   - planning_calls=0, rollout_steps=0
   - Used ONLY as upper bound visualization, NOT in compute-matched comparisons

Helper: `def _noop_action() -> CandidateAction` returning CandidateAction("noop","noop",{})

Update `src/frcgw/evaluation/__init__.py` to export all baseline classes.

REQUIRED_TESTS:

### tests/test_baselines.py

For each of the 9 agents:
- Construct a minimal PublicObservation with 2 candidate_actions_public
- Call agent.act(obs) → verify returns (CandidateAction, ComputeBudgetLog)
- Verify ComputeBudgetLog has correct planning_calls and rollout_steps per spec
- Verify act() does NOT raise even with empty candidate_actions_public

Additional:
- RetryAfterFailureAgent.reset() clears state between episodes
- OracleAgent with eval_labels=None does not crash
- OracleAgent with eval_labels={"correct_hypothesis_id": "h1"} returns valid action
- assert that none of FORBIDDEN_AGENT_KEYS appear in any agent's attribute names
  (sanity check: agents don't store forbidden labels as instance vars)
- Verify FrozenBaseAgent produces planning_calls=0 ComputeBudgetLog

ACCEPTANCE_CRITERIA:
1. pytest tests/test_baselines.py -q → all pass, 0 failures
2. All 9 classes present in baselines.py with correct baseline_id strings
3. No agent reads FORBIDDEN_AGENT_KEYS from a PublicObservation attribute
   (PublicObservation fields: instruction, dom_snapshot_public,
    accessibility_tree_public, screenshot_ref, history_public,
    candidate_actions_public — all safe)
4. Every act() returns (CandidateAction, ComputeBudgetLog) — type contract enforced
5. OracleAgent only uses eval_labels when explicitly passed; never baked into
   the agent's internal state from obs
6. __init__.py exports all 9 classes

COMMIT_MESSAGE:
feat(p3-eval-e2): baseline agent implementations (BASE-001,002,003,005,009,010,012,014,016/017)

STOP_CONDITION:
Stop if any agent reads attributes named "true_*", "oracle_*", "counterfactual_*",
"split_id", "ood_type", "template_id", "seed", "policy_id", "audit_metadata"
from obs (PublicObservation) — these are forbidden at inference time.
Stop if eval_labels is used as inference input in any agent other than OracleAgent.
Stop if any agent imports from frcgw.models, frcgw.planning, frcgw.training
(baselines are standalone heuristics in P3 text-only evaluation).
