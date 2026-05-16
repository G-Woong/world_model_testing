"""Core P3 ablation definitions and masking wrappers.

Source docs:
- paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md section 8 ABL-001~042
- paper_context_ref/15_TDD_TECHNICAL_DESIGN_DOCUMENT_v1.md section 15 lines 1011~1029
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any

from frcgw.evaluation.baselines import BaselineAgent
from frcgw.evaluation.compute_budget import ComputeBudgetLog
from frcgw.schemas.step_schema import CandidateAction, PublicObservation


@dataclass
class AblationConfig:
    ablation_id: str
    tdd_ref: str
    severity: str
    description: str
    expected_collapse: dict[str, str]
    masking: dict[str, Any]


def _budget(
    *,
    planning_calls: int,
    rollout_steps: int,
    candidate_actions_scored: int,
    top_k_alternatives: int = 0,
) -> ComputeBudgetLog:
    return ComputeBudgetLog(
        planning_calls=planning_calls,
        rollout_steps=rollout_steps,
        candidate_actions_scored=candidate_actions_scored,
        top_k_alternatives=top_k_alternatives,
        wall_clock_seconds=0.0,
    )


def _noop_action() -> CandidateAction:
    return CandidateAction("noop", "noop", {})


def _first_candidate(obs: PublicObservation) -> CandidateAction:
    if obs.candidate_actions_public:
        return obs.candidate_actions_public[0]
    return _noop_action()


def _best_public_candidate(obs: PublicObservation) -> CandidateAction:
    if not obs.candidate_actions_public:
        return _noop_action()
    return max(obs.candidate_actions_public, key=lambda action: len(action.action_id))


def _random_public_candidate(obs: PublicObservation, *, salt: str = "") -> CandidateAction:
    if not obs.candidate_actions_public:
        return _noop_action()
    seed = f"{salt}|{obs.instruction}|{len(obs.history_public)}|{len(obs.candidate_actions_public)}"
    rng = random.Random(seed)
    return rng.choice(obs.candidate_actions_public)


class AblatedAgent(BaselineAgent):
    """Base wrapper for config-driven ablations over a frozen public-policy agent."""

    def __init__(self, agent: Any, config: AblationConfig) -> None:
        self._agent = agent
        self._config = config
        self.ablation_id = config.ablation_id
        self.baseline_id = f"{getattr(agent, 'baseline_id', agent.__class__.__name__)}:{self.ablation_id}"

    def reset(self) -> None:
        if hasattr(self._agent, "reset"):
            self._agent.reset()


class NoControlGrammarAblation(AblatedAgent):
    def act(
        self,
        obs: PublicObservation,
        eval_labels: dict | None = None,
    ) -> tuple[CandidateAction, ComputeBudgetLog]:
        return _random_public_candidate(obs, salt=self.ablation_id), _budget(
            planning_calls=0,
            rollout_steps=0,
            candidate_actions_scored=len(obs.candidate_actions_public),
        )


class MergedRegimeControlGrammarAblation(AblatedAgent):
    def act(
        self,
        obs: PublicObservation,
        eval_labels: dict | None = None,
    ) -> tuple[CandidateAction, ComputeBudgetLog]:
        return _first_candidate(obs), _budget(
            planning_calls=0,
            rollout_steps=0,
            candidate_actions_scored=1 if obs.candidate_actions_public else 0,
        )


class CollapsedLatentAblation(AblatedAgent):
    def act(
        self,
        obs: PublicObservation,
        eval_labels: dict | None = None,
    ) -> tuple[CandidateAction, ComputeBudgetLog]:
        return _first_candidate(obs), _budget(
            planning_calls=0,
            rollout_steps=0,
            candidate_actions_scored=1 if obs.candidate_actions_public else 0,
        )


class NoFalsificationAblation(AblatedAgent):
    def act(
        self,
        obs: PublicObservation,
        eval_labels: dict | None = None,
    ) -> tuple[CandidateAction, ComputeBudgetLog]:
        action, log = self._agent.act(obs)
        return action, ComputeBudgetLog(
            planning_calls=0,
            rollout_steps=0,
            candidate_actions_scored=log.candidate_actions_scored,
            top_k_alternatives=0,
            wall_clock_seconds=log.wall_clock_seconds,
        )


class UncertaintyInsteadOfFalsificationAblation(AblatedAgent):
    def act(
        self,
        obs: PublicObservation,
        eval_labels: dict | None = None,
    ) -> tuple[CandidateAction, ComputeBudgetLog]:
        should_plan = len(obs.history_public) % 3 == 0
        if should_plan:
            return _best_public_candidate(obs), _budget(
                planning_calls=1,
                rollout_steps=0,
                candidate_actions_scored=len(obs.candidate_actions_public),
            )
        return _first_candidate(obs), _budget(
            planning_calls=0,
            rollout_steps=0,
            candidate_actions_scored=1 if obs.candidate_actions_public else 0,
        )


class NoAlternativeHypothesisAblation(AblatedAgent):
    def act(
        self,
        obs: PublicObservation,
        eval_labels: dict | None = None,
    ) -> tuple[CandidateAction, ComputeBudgetLog]:
        return _first_candidate(obs), _budget(
            planning_calls=1,
            rollout_steps=0,
            candidate_actions_scored=1 if obs.candidate_actions_public else 0,
            top_k_alternatives=0,
        )


class RandomAlternativeAblation(AblatedAgent):
    def act(
        self,
        obs: PublicObservation,
        eval_labels: dict | None = None,
    ) -> tuple[CandidateAction, ComputeBudgetLog]:
        return _random_public_candidate(obs, salt=self.ablation_id), _budget(
            planning_calls=1,
            rollout_steps=0,
            candidate_actions_scored=len(obs.candidate_actions_public),
            top_k_alternatives=1 if obs.candidate_actions_public else 0,
        )


class NoRolloutAblation(AblatedAgent):
    def act(
        self,
        obs: PublicObservation,
        eval_labels: dict | None = None,
    ) -> tuple[CandidateAction, ComputeBudgetLog]:
        return _best_public_candidate(obs), _budget(
            planning_calls=1,
            rollout_steps=0,
            candidate_actions_scored=len(obs.candidate_actions_public),
        )


class NoRewriteAblation(AblatedAgent):
    def act(
        self,
        obs: PublicObservation,
        eval_labels: dict | None = None,
    ) -> tuple[CandidateAction, ComputeBudgetLog]:
        action, log = self._agent.act(obs)
        return action, log


class AlwaysPlanNoGateAblation(AblatedAgent):
    def act(
        self,
        obs: PublicObservation,
        eval_labels: dict | None = None,
    ) -> tuple[CandidateAction, ComputeBudgetLog]:
        return _best_public_candidate(obs), _budget(
            planning_calls=1,
            rollout_steps=0,
            candidate_actions_scored=len(obs.candidate_actions_public),
        )


class NoProgressRewardAblation(AblatedAgent):
    def act(
        self,
        obs: PublicObservation,
        eval_labels: dict | None = None,
    ) -> tuple[CandidateAction, ComputeBudgetLog]:
        return _random_public_candidate(obs, salt=self.ablation_id), _budget(
            planning_calls=1,
            rollout_steps=len(obs.candidate_actions_public),
            candidate_actions_scored=len(obs.candidate_actions_public),
        )


class NoComputeGateAblation(AblatedAgent):
    def act(
        self,
        obs: PublicObservation,
        eval_labels: dict | None = None,
    ) -> tuple[CandidateAction, ComputeBudgetLog]:
        rollout_steps = int(self._config.masking.get("rollout_steps", 10))
        return _best_public_candidate(obs), _budget(
            planning_calls=1,
            rollout_steps=rollout_steps,
            candidate_actions_scored=len(obs.candidate_actions_public),
        )


class NoRegimeAblationAgent(AblatedAgent):
    """ABL-001: Remove regime latent to test C2 regime/control-grammar separability.

    Locatello impossibility risk: without separate regime latent,
    regime and grammar representations may collapse.
    """

    def act(
        self,
        obs: PublicObservation,
        eval_labels: dict | None = None,
    ) -> tuple[CandidateAction, ComputeBudgetLog]:
        return _first_candidate(obs), _budget(
            planning_calls=0,
            rollout_steps=0,
            candidate_actions_scored=1 if obs.candidate_actions_public else 0,
        )


class NoIntentActionMappingAblationAgent(AblatedAgent):
    """ABL-017: Remove training-time intent-to-action mapping loss.

    Distinct from ABL-035 (no_rewrite): ABL-035 removes the inference-time
    rewrite module; ABL-017 removes the training-time L_intent_action_mapping loss.
    At inference, manifests as random candidate selection.
    """

    def act(
        self,
        obs: PublicObservation,
        eval_labels: dict | None = None,
    ) -> tuple[CandidateAction, ComputeBudgetLog]:
        return _random_public_candidate(obs, salt=self.ablation_id), _budget(
            planning_calls=0,
            rollout_steps=0,
            candidate_actions_scored=len(obs.candidate_actions_public),
        )


class NoFalsificationScoreGateAblationAgent(AblatedAgent):
    """ABL-022: Remove F_t > tau_f inference gate.

    Distinct from ABL-016 (no_falsification): ABL-016 removes the training-time
    falsification loss; ABL-022 removes the inference-time score gate.
    Without the gate, the agent always attempts to plan.
    """

    def act(
        self,
        obs: PublicObservation,
        eval_labels: dict | None = None,
    ) -> tuple[CandidateAction, ComputeBudgetLog]:
        return _first_candidate(obs), _budget(
            planning_calls=1,
            rollout_steps=0,
            candidate_actions_scored=1 if obs.candidate_actions_public else 0,
        )


class NoCounterfactualTargetAblationAgent(AblatedAgent):
    """ABL-036: Remove counterfactual supervision target.

    Without counterfactual targets, alternative rollout fidelity degrades;
    the agent still plans but picks randomly among candidates.
    """

    def act(
        self,
        obs: PublicObservation,
        eval_labels: dict | None = None,
    ) -> tuple[CandidateAction, ComputeBudgetLog]:
        return _random_public_candidate(obs, salt=self.ablation_id), _budget(
            planning_calls=1,
            rollout_steps=0,
            candidate_actions_scored=len(obs.candidate_actions_public),
        )


ABLATION_REGISTRY: dict[str, AblationConfig] = {
    "no_control_grammar": AblationConfig(
        ablation_id="no_control_grammar",
        tdd_ref="ABL-002",
        severity="CRITICAL",
        description="Remove control-grammar head; agent uses uniform random action selection",
        expected_collapse={
            "wrong_control_grammar_persistence": "increase",
            "task_success_rate_text_ood_grammar": "decrease",
        },
        masking={"disable_grammar_head": True, "uniform_random_action": True},
    ),
    "merged_regime_control_grammar": AblationConfig(
        ablation_id="merged_regime_control_grammar",
        tdd_ref="ABL-003",
        severity="CRITICAL",
        description="Merge regime and grammar representations",
        expected_collapse={"task_success_rate_text_ood_grammar": "decrease"},
        masking={"merge_regime_and_grammar": True},
    ),
    "collapsed_latent": AblationConfig(
        ablation_id="collapsed_latent",
        tdd_ref="ABL-006",
        severity="CRITICAL",
        description="Use zero/uniform latent representation",
        expected_collapse={"falsification_precision_recall_f1": "decrease"},
        masking={"zero_latent_state": True},
    ),
    "no_falsification": AblationConfig(
        ablation_id="no_falsification",
        tdd_ref="ABL-016",
        severity="CRITICAL",
        description="Remove falsification scoring; agent never detects wrong hypothesis",
        expected_collapse={
            "falsification_precision_recall_f1": "decrease",
            "false_planning_call_rate": "increase",
        },
        masking={"disable_falsification": True},
    ),
    "uncertainty_instead_of_falsification": AblationConfig(
        ablation_id="uncertainty_instead_of_falsification",
        tdd_ref="ABL-023",
        severity="CRITICAL",
        description="Replace falsification with uncertainty threshold",
        expected_collapse={"false_planning_call_rate": "increase"},
        masking={"use_uncertainty_gate": True},
    ),
    "no_alternative_hypothesis": AblationConfig(
        ablation_id="no_alternative_hypothesis",
        tdd_ref="ABL-024",
        severity="CRITICAL",
        description="No alternative hypothesis proposal; always uses current grammar",
        expected_collapse={"recovery_delay": "increase", "task_success_rate": "decrease"},
        masking={"disable_alternative_proposal": True},
    ),
    "random_alternative": AblationConfig(
        ablation_id="random_alternative",
        tdd_ref="ABL-025",
        severity="standard",
        description="Pick random alternative hypothesis instead of proposed",
        expected_collapse={"recovery_delay": "increase"},
        masking={"randomize_alternative": True},
    ),
    "no_rollout": AblationConfig(
        ablation_id="no_rollout",
        tdd_ref="ABL-026",
        severity="standard",
        description="Skip rollout; use 0 rollout steps in planning",
        expected_collapse={"task_success_rate": "decrease"},
        masking={"rollout_steps": 0},
    ),
    "no_rewrite": AblationConfig(
        ablation_id="no_rewrite",
        tdd_ref="ABL-035",
        severity="CRITICAL",
        description="Skip action-interface rewrite",
        expected_collapse={
            "failed_action_repetition_rate": "increase",
            "action_switch_delay": "increase",
        },
        masking={"disable_rewrite": True},
    ),
    "always_plan_no_gate": AblationConfig(
        ablation_id="always_plan_no_gate",
        tdd_ref="ABL-034",
        severity="CRITICAL",
        description="Always plan; no decision gate",
        expected_collapse={
            "progress_per_compute": "decrease",
            "false_planning_call_rate": "increase",
        },
        masking={"always_plan": True},
    ),
    "no_progress_reward": AblationConfig(
        ablation_id="no_progress_reward",
        tdd_ref="ABL-019",
        severity="standard",
        description="Remove progress signal from scoring",
        expected_collapse={"progress_per_compute": "decrease"},
        masking={"disable_progress_reward": True},
    ),
    "no_compute_gate": AblationConfig(
        ablation_id="no_compute_gate",
        tdd_ref="ABL-033",
        severity="CRITICAL",
        description="No compute gate; always allocate full budget",
        expected_collapse={
            "false_planning_call_rate": "increase",
            "progress_per_compute": "decrease",
        },
        masking={"disable_compute_gate": True, "rollout_steps": 10},
    ),
    "no_regime": AblationConfig(
        ablation_id="no_regime",
        tdd_ref="ABL-001",
        severity="CRITICAL",
        description="Remove regime latent dimension to test C2 regime/control-grammar separation. Locatello impossibility risk.",
        expected_collapse={"regime_shift_f1": "decrease", "recovery_delay": "increase"},
        masking={"regime_latent": "zeroed"},
    ),
    "no_intent_action_mapping": AblationConfig(
        ablation_id="no_intent_action_mapping",
        tdd_ref="ABL-017",
        severity="CRITICAL",
        description="Remove training-time L_intent_action_mapping loss (C5). ABL-035 removes inference rewrite; this removes training-time mapping loss.",
        expected_collapse={"rewrite_success_rate": "decrease", "failed_repetition_rate": "increase"},
        masking={"disable_intent_action_mapping_loss": True},
    ),
    "no_falsification_score_gate": AblationConfig(
        ablation_id="no_falsification_score_gate",
        tdd_ref="ABL-022",
        severity="CRITICAL",
        description="Remove F_t > tau_f inference gate (C1+C3). ABL-016 removes falsification loss; this removes inference gate.",
        expected_collapse={"falsification_precision_recall_f1": "decrease", "wrong_control_grammar_persistence": "increase"},
        masking={"disable_falsification_gate": True},
    ),
    "no_counterfactual_target": AblationConfig(
        ablation_id="no_counterfactual_target",
        tdd_ref="ABL-036",
        severity="HIGH",
        description="Remove counterfactual supervision target; alternative rollout fidelity degraded (C4).",
        expected_collapse={"rollout_fidelity": "decrease", "alternative_adoption_rate": "decrease"},
        masking={"disable_counterfactual_target": True},
    ),
}


_WRAPPERS: dict[str, type[AblatedAgent]] = {
    "no_control_grammar": NoControlGrammarAblation,
    "merged_regime_control_grammar": MergedRegimeControlGrammarAblation,
    "collapsed_latent": CollapsedLatentAblation,
    "no_falsification": NoFalsificationAblation,
    "uncertainty_instead_of_falsification": UncertaintyInsteadOfFalsificationAblation,
    "no_alternative_hypothesis": NoAlternativeHypothesisAblation,
    "random_alternative": RandomAlternativeAblation,
    "no_rollout": NoRolloutAblation,
    "no_rewrite": NoRewriteAblation,
    "always_plan_no_gate": AlwaysPlanNoGateAblation,
    "no_progress_reward": NoProgressRewardAblation,
    "no_compute_gate": NoComputeGateAblation,
    "no_regime": NoRegimeAblationAgent,
    "no_intent_action_mapping": NoIntentActionMappingAblationAgent,
    "no_falsification_score_gate": NoFalsificationScoreGateAblationAgent,
    "no_counterfactual_target": NoCounterfactualTargetAblationAgent,
}


def apply_ablation(
    agent: Any,
    ablation_config: AblationConfig,
) -> Any:
    """Return a wrapped agent that behaves as per the ablation masking rules.

    For P3 text-only evaluation, masking is simulated via agent wrapper classes
    rather than weight zeroing. Each wrapper overrides public action selection
    and compute accounting without reading hidden/evaluation-only observation
    fields.
    """
    wrapper_cls = _WRAPPERS.get(ablation_config.ablation_id)
    if wrapper_cls is None:
        raise KeyError(f"Unknown ablation_id: {ablation_config.ablation_id}")
    return wrapper_cls(agent, ablation_config)


__all__ = [
    "ABLATION_REGISTRY",
    "AblationConfig",
    "AblatedAgent",
    "apply_ablation",
]
