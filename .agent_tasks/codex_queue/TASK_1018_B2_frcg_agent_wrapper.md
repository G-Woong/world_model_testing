TASK_NAME: TASK_1018_B2_frcg_agent_wrapper

BACKGROUND:
FRCG-WM P3 evaluation phase. P3 EVAL FAIL blocker B2.

TASK_1017 (B1) is already merged. After B1 fix:
  - recovery_delay and persistence metrics now compute from step sequences
  - BUT for gates G1/G2: we need "FRCG-FULL" agent results to compare vs VerifierOnly
    and UncertaintyGated
  - Gates G3/G4 compare no_control_grammar/no_falsification ablations vs FRCG-FULL

Currently src/frcgw/evaluation/baselines.py has only heuristic baseline agents.
The TextFRCGModel (src/frcgw/models/text_frcg_model.py) is NOT wrapped as an agent.

Key interfaces already implemented:
- TextFRCGModel.forward(obs: PublicObservation) → ModelOutput (models/text_frcg_model.py)
- text_frcg_plan(obs, step_idx, candidates, model, planner_state, cfg) → (CandidateAction, PlanMetadata)
  (planning/planner.py)
- PlannerState, GateConfig, GateInput, GateOutput (planning/planner.py, decision_gate.py)
- FalsificationEvidence, falsification_score (planning/falsification.py)
- BaselineAgent.act(obs) → (CandidateAction, ComputeBudgetLog) (evaluation/baselines.py)
- ComputeBudgetLog (evaluation/compute_budget.py)

eval_runner.py after TASK_1017 now supports:
  - agent.last_predicted_wrong property for per-step predicted_wrong

GateConfig defaults: tau_f=0.0 (opens on ANY falsification signal).
For evaluation, use tau_f=0.5 to require meaningful falsification before planning.

Source MDs:
- paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md (text_frcg_plan interface)
- paper_context_ref/07_LATENT_ARCHITECTURE_DESIGN.md (model output)
- paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md §7 BASE-001 (FRCG-FULL spec)

GOAL:
Implement src/frcgw/evaluation/frcg_agent.py with TextFRCGModelAgent.
Write tests/test_frcg_agent.py.
Update src/frcgw/evaluation/__init__.py to export TextFRCGModelAgent.

FILES_ALLOWED:
src/frcgw/evaluation/frcg_agent.py
src/frcgw/evaluation/__init__.py
tests/test_frcg_agent.py

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
src/frcgw/evaluation/reporter.py

REQUIRED_IMPLEMENTATION:

### src/frcgw/evaluation/frcg_agent.py

Module docstring citing:
  paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md text_frcg_plan
  paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md §7

```python
"""frcgw.evaluation.frcg_agent — TextFRCGModelAgent: FRCG full model as evaluation agent.

Source MDs:
- paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md text_frcg_plan interface
- paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md §7 FRCG-FULL comparison
"""
from __future__ import annotations

import torch
from pathlib import Path
from typing import Any

from frcgw.evaluation.baselines import BaselineAgent, _noop_action
from frcgw.evaluation.compute_budget import ComputeBudgetLog
from frcgw.models.text_frcg_model import TextFRCGModel
from frcgw.planning.decision_gate import GateConfig
from frcgw.planning.planner import PlannerState, text_frcg_plan
from frcgw.schemas.step_schema import CandidateAction, PublicObservation


class TextFRCGModelAgent(BaselineAgent):
    """FRCG full model wrapped as a BaselineAgent for evaluation.

    Uses text_frcg_plan() for closed-loop planning. Exposes:
    - last_predicted_wrong: bool  (F_t > tau_f from most recent act())
    - last_F_t: float             (falsification score from most recent act())

    NEVER reads FORBIDDEN_AGENT_KEYS from observation.
    eval_labels arg in act() is accepted but IGNORED (oracle not used).

    Source MD: paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md text_frcg_plan
    """

    baseline_id = "FRCG-FULL"

    def __init__(
        self,
        model: TextFRCGModel | None = None,
        ckpt_path: str | Path | None = None,
        gate_config: GateConfig | None = None,
        device: str = "cpu",
    ) -> None:
        if model is None:
            model = TextFRCGModel()
        self.model = model.to(device)
        self.device = device

        if ckpt_path is not None:
            ckpt = torch.load(ckpt_path, map_location=device)
            state_dict = ckpt.get("model_state_dict", ckpt)
            self.model.load_state_dict(state_dict)

        # tau_f=0.5: require meaningful falsification signal to trigger planning
        self.gate_config = gate_config or GateConfig(tau_f=0.5)
        self._planner_state = PlannerState()
        self._step_idx = 0
        self._last_F_t: float = 0.0
        self._last_predicted_wrong: bool = False

    def reset(self) -> None:
        self._planner_state = PlannerState()
        self._step_idx = 0
        self._last_F_t = 0.0
        self._last_predicted_wrong = False

    def act(
        self,
        obs: PublicObservation,
        eval_labels: dict | None = None,   # accepted but never used
    ) -> tuple[CandidateAction, ComputeBudgetLog]:
        candidates = list(obs.candidate_actions_public)
        if not candidates:
            candidates = [_noop_action()]

        self.model.eval()
        with torch.no_grad():
            action, plan_meta = text_frcg_plan(
                obs,
                self._step_idx,
                candidates,
                self.model,
                self._planner_state,
                self.gate_config,
            )

        self._last_F_t = plan_meta.F_t
        self._last_predicted_wrong = plan_meta.F_t > self.gate_config.tau_f
        self._step_idx += 1

        planned = plan_meta.planned
        compute_log = ComputeBudgetLog(
            planning_calls=1 if planned else 0,
            rollout_steps=3 if planned else 0,  # k=3 alternatives scored
            candidate_actions_scored=len(candidates),
            top_k_alternatives=3 if planned else 0,
            wall_clock_seconds=0.0,
        )
        return action, compute_log

    @property
    def last_predicted_wrong(self) -> bool:
        return self._last_predicted_wrong

    @property
    def last_F_t(self) -> float:
        return self._last_F_t
```

### src/frcgw/evaluation/__init__.py

Add TextFRCGModelAgent to imports and __all__:
```python
from frcgw.evaluation.frcg_agent import TextFRCGModelAgent
```
Add "TextFRCGModelAgent" to __all__.

REQUIRED_TESTS:

### tests/test_frcg_agent.py

Use TextFRCGModel() (default random init, no checkpoint required).

Tests:
1. TextFRCGModelAgent() constructs without error (no ckpt required)
2. agent.act(obs) returns (CandidateAction, ComputeBudgetLog)
3. agent.act(obs) with empty candidate_actions_public → returns noop action
4. agent.act(obs) with 2 candidates → returns one of them (CandidateAction)
5. ComputeBudgetLog.planning_calls is 0 or 1 (never negative, never > 1 per step)
6. agent.reset() resets _step_idx to 0 and _last_F_t to 0.0
7. agent.last_predicted_wrong is bool
8. agent.last_F_t is float
9. eval_labels arg in act() is accepted and does NOT affect action selection
   (call with eval_labels={"oracle_best_action": "click"} → no error, no change)
10. baseline_id == "FRCG-FULL"
11. FORBIDDEN_AGENT_KEYS: verify agent does NOT read any forbidden key from obs
    (construct obs with a forbidden-named field manually and verify no AttributeError)
12. gate_config can be overridden: GateConfig(gate_mode="never_plan") → planning_calls=0 always
13. GateConfig(gate_mode="always_plan") → planning_calls=1 for every act()

ACCEPTANCE_CRITERIA:
1. pytest tests/test_frcg_agent.py -q → all pass, 0 failures
2. TextFRCGModelAgent is exported from src/frcgw/evaluation/__init__.py
3. baseline_id = "FRCG-FULL" exactly (string match for eval reporter)
4. act() never passes eval_labels to model.forward() or text_frcg_plan()
5. last_predicted_wrong = F_t > gate_config.tau_f (consistent with gate threshold)
6. reset() fully clears per-episode state (_step_idx, _planner_state, _last_F_t)
7. No import of forbidden fields from schemas in frcg_agent.py

COMMIT_MESSAGE:
feat(p3-eval-b2): TextFRCGModelAgent wrapper for FRCG-FULL evaluation

STOP_CONDITION:
Stop if eval_labels or any oracle_* field is passed to model.forward() or
text_frcg_plan() — that is hidden label leakage.
Stop if act() reads any FORBIDDEN_AGENT_KEY from obs (these are not attributes of
PublicObservation, so any AttributeError on .true_regime etc would be caught).
Stop if last_predicted_wrong is not computed from F_t (must be F_t > tau_f).
