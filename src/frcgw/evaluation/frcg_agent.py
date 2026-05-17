"""frcgw.evaluation.frcg_agent -- TextFRCGModelAgent: FRCG full model as evaluation agent.

Source MDs:
- paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md text_frcg_plan interface
- paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md 짠7 FRCG-FULL comparison
"""
from __future__ import annotations

import math
from dataclasses import replace  # used for always_plan gate_mode override
from pathlib import Path

import torch
import torch.nn.functional as F

from frcgw.evaluation.baselines import BaselineAgent, _noop_action
from frcgw.evaluation.compute_budget import ComputeBudgetLog
from frcgw.models.text_frcg_model import TextFRCGModel
from frcgw.planning.decision_gate import GateConfig
from frcgw.planning.planner import PlannerState, text_frcg_plan
from frcgw.schemas.step_schema import CandidateAction, PublicObservation


def _sigmoid(x: float) -> float:
    """Numerically stable sigmoid with +/-50 clamp."""
    x = max(-50.0, min(50.0, x))
    return 1.0 / (1.0 + math.exp(-x))


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

        self.gate_config = gate_config or GateConfig(tau_f=0.5)
        # Threshold for grammar uncertainty: if max P(grammar) < 0.4, predict wrong hypothesis.
        # For default n_grammars=8, uniform gives max=0.125 (always predicts wrong).
        # A trained model concentrating on 1 grammar gives max≈1.0 (predicts correct).
        self._confidence_threshold: float = 0.4
        # _confidence_threshold kept for ABL-022/ABL-023 subclass compatibility
        # predicted_wrong now uses F_t > tau_f (paper contract: MET-FALS-001/002)
        self._planner_state = PlannerState()
        self._step_idx = 0
        self._last_F_t: float = 0.0
        self._last_predicted_wrong: bool = False
        self._last_wrong_prob: float = 0.5
        self._last_tau_f: float = self.gate_config.tau_f
        self._last_selected_hypothesis_id: str | None = None
        self._last_selected_hypothesis_confidence: float | None = None

    def reset(self) -> None:
        self._planner_state = PlannerState()
        self._step_idx = 0
        self._last_F_t = 0.0
        self._last_predicted_wrong = False
        self._last_wrong_prob = 0.5
        self._last_tau_f = self.gate_config.tau_f
        self._last_selected_hypothesis_id = None
        self._last_selected_hypothesis_confidence = None

    def act(
        self,
        obs: PublicObservation,
        eval_labels: dict | None = None,  # never used; accepted for API compatibility
    ) -> tuple[CandidateAction, ComputeBudgetLog]:
        candidates = list(obs.candidate_actions_public)
        if not candidates:
            candidates = [_noop_action()]

        self.model.eval()
        # For always_plan: bypass the early F_t <= tau_f check by setting tau_f=-inf
        plan_gate_config = self.gate_config
        if self.gate_config.gate_mode == "always_plan":
            plan_gate_config = replace(self.gate_config, tau_f=float("-inf"))

        with torch.no_grad():
            # Forward pass to get posterior for falsification signal
            model_out = self.model.forward(obs)
            # Retained for ABL-022/ABL-023 compatibility; full-model trace uses F_t below.
            grammar_probs = F.softmax(model_out.z_grammar_logits, dim=-1)
            best_grammar_idx = int(grammar_probs.argmax().item())
            max_grammar_prob = float(grammar_probs.max().item())
            self._last_selected_hypothesis_id = f"grammar_{best_grammar_idx}"
            self._last_selected_hypothesis_confidence = max_grammar_prob

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
        self._step_idx += 1

        planned = plan_meta.planned
        # When not planning: model forward = 1 unit; when planning: forward + k rollouts
        compute_log = ComputeBudgetLog(
            planning_calls=1 if planned else 0,
            rollout_steps=3 if planned else 0,
            candidate_actions_scored=len(candidates) if planned else 1,
            top_k_alternatives=3 if planned else 0,
            wall_clock_seconds=0.0,
        )
        return action, compute_log

    @property
    def last_predicted_wrong(self) -> bool:
        return self._last_predicted_wrong

    @property
    def last_wrong_prob(self) -> float:
        """P(wrong hypothesis) = sigmoid(F_t - tau_f) from the LR falsification score."""
        return self._last_wrong_prob

    @property
    def last_F_t(self) -> float:
        return self._last_F_t

    @property
    def last_tau_f(self) -> float:
        return self._last_tau_f
