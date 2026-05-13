"""frcgw.evaluation.frcg_agent -- TextFRCGModelAgent: FRCG full model as evaluation agent.

Source MDs:
- paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md text_frcg_plan interface
- paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md 짠7 FRCG-FULL comparison
"""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import torch

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

        # tau_f=0.5 requires a meaningful falsification signal to trigger planning.
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
        eval_labels: dict | None = None,
    ) -> tuple[CandidateAction, ComputeBudgetLog]:
        candidates = list(obs.candidate_actions_public)
        if not candidates:
            candidates = [_noop_action()]

        self.model.eval()
        plan_gate_config = self.gate_config
        if self.gate_config.gate_mode == "always_plan":
            plan_gate_config = replace(self.gate_config, tau_f=float("-inf"))

        with torch.no_grad():
            action, plan_meta = text_frcg_plan(
                obs,
                self._step_idx,
                candidates,
                self.model,
                self._planner_state,
                plan_gate_config,
            )

        self._last_F_t = float(plan_meta.F_t)
        self._last_predicted_wrong = self._last_F_t > self.gate_config.tau_f
        self._step_idx += 1

        planned = plan_meta.planned
        compute_log = ComputeBudgetLog(
            planning_calls=1 if planned else 0,
            rollout_steps=3 if planned else 0,
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
