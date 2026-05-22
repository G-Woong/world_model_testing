"""Counterfactual rollout generation for text environment steps.

Source:
- paper_context_ref/06_DATA_SCHEMA_AND_LABELING.md section 4 CounterfactualRecord
- paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md section 8 ABL-008 rollout
"""
from __future__ import annotations

import copy
import random
from dataclasses import replace

from frcgw.schemas.step_schema import CandidateAction, CounterfactualRecord
from frcgw.text_env.grammar import GrammarEngine
from frcgw.text_env.state import TextState


_PUBLIC_EFFECT_TYPES = frozenset(
    {
        "state_change",
        "no_state_change",
        "blocker_removed",
        "delayed_effect",
        "task_complete",
    }
)


def generate_counterfactuals(
    pre_state: TextState,
    actual_action_id: str,
    candidates: list[CandidateAction],
    engine: GrammarEngine,
    top_k: int = 3,
    rng: random.Random | None = None,
) -> list[CounterfactualRecord]:
    """Simulate non-selected candidate effects under the current grammar.

    The rollout uses a deep copy of the pre-step hidden preconditions and never
    mutates ``pre_state`` or ``engine``. Returned records contain only
    CounterfactualRecord fields intended for counterfactual-only storage.
    """
    if rng is None:
        rng = random.Random(0)

    del rng  # Candidate ordering is already deterministic.

    if top_k <= 0:
        return []

    non_selected = [c for c in candidates if c.action_id != actual_action_id]
    if not non_selected:
        return []

    chosen = non_selected[: min(top_k, len(non_selected))]
    source_step_id = getattr(pre_state, "step_id", str(pre_state.step_index))

    records: list[CounterfactualRecord] = []
    best_delta = float("-inf")
    best_idx = -1

    for i, candidate in enumerate(chosen):
        preconditions_copy = copy.deepcopy(pre_state._hidden_preconditions)
        effect_type, progress_delta = _simulate_action(
            preconditions_copy, candidate.action_id, engine
        )
        failure_risk = _estimate_failure_risk(
            preconditions_copy, candidate.action_id, engine, effect_type
        )

        if progress_delta > best_delta:
            best_delta = progress_delta
            best_idx = i

        records.append(
            CounterfactualRecord(
                counterfactual_id=f"{source_step_id}_cf_{i}",
                source_step_id=source_step_id,
                candidate_action=candidate,
                hypothesis_id="counterfactual_simulation",
                counterfactual_effect_type=effect_type,
                counterfactual_progress_delta=float(progress_delta),
                counterfactual_failure_risk=float(failure_risk),
                is_oracle_best=False,
            )
        )

    if records and best_idx >= 0:
        records[best_idx] = replace(records[best_idx], is_oracle_best=True)

    return records


def _simulate_action(
    preconditions: dict,
    action_id: str,
    engine: GrammarEngine,
) -> tuple[str, float]:
    """Apply an action to copied preconditions and return public-safe effects."""
    _new_flags, progress_delta, effect_type = engine.apply(preconditions, action_id)
    if effect_type not in _PUBLIC_EFFECT_TYPES:
        effect_type = "no_state_change"
    return effect_type, float(progress_delta)


def _estimate_failure_risk(
    preconditions: dict,
    action_id: str,
    engine: GrammarEngine,
    effect_type: str,
) -> float:
    """Return a bounded proxy for wrong-grammar failure risk."""
    try:
        is_wrong = engine.is_wrong_grammar_failure(preconditions, action_id, effect_type)
    except Exception:
        return 0.5
    return 1.0 if is_wrong else 0.0
