"""frcgw.text_env.collector — TextCollector: episode collection loop.

Source docs:
- paper_context_ref/04_TEXT_ONLY_SMOKE_TESTBED.md §8, §19
- paper_context_ref/06_DATA_SCHEMA_AND_LABELING.md §4 visibility, §7 extraction
- paper_context_ref/12_DATA_COLLECTION_METHODOLOGY_v1.md §8 text-only, §10 failure/recovery
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import datetime, timezone

from frcgw.schemas.episode_schema import AuditMetadata, EpisodeRecord
from frcgw.schemas.step_schema import (
    ActionRecord,
    CandidateAction,
    EvaluationLabels,
    PublicEffect,
    PublicHistoryItem,
    PublicObservation,
    StepAuditMetadata,
    StepRecord,
    TrainingLabels,
)
from frcgw.schemas.validation import (
    SchemaValidationError,
    validate_episode_schema,
    validate_step_schema,
    validate_visibility_contract,
)
from frcgw.schemas.visibility import (
    HiddenLabelLeakageError,
    assert_agent_observation_safe,
)
from frcgw.text_env.generator import build_initial_state
from frcgw.text_env.grammar import GrammarEngine
from frcgw.text_env.policies import PolicyMixtureRunner
from frcgw.text_env.state import TextEpisodeSpec, TextState


@dataclass
class CollectorConfig:
    dataset_version: str = "0.1"
    schema_version: str = "schema-06-v0.1"
    generator_version: str = "p2-text-v0.1"
    split_id: str = "train"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_public_observation(
    state: TextState,
    instruction: str,
    history: list[PublicHistoryItem],
) -> PublicObservation:
    """Build a sanitized PublicObservation from TextState.

    visible_text is embedded in instruction via [STATE] prefix (TDD §5.4).
    Hidden fields are NEVER copied here; assert_agent_observation_safe() enforces
    the visibility contract (06_DATA_SCHEMA §4).
    """
    obs = PublicObservation(
        instruction=instruction,
        dom_snapshot_public=None,
        accessibility_tree_public=None,
        screenshot_ref=None,
        history_public=list(history),
        candidate_actions_public=list(state.public_actions),
    )
    assert_agent_observation_safe(obs)
    return obs


def _format_instruction(spec: TextEpisodeSpec, state: TextState) -> str:
    return (
        f"[INSTRUCTION] {spec.public_instruction}\n"
        f"[STATE] {state.visible_text}"
    )


def _pick_scheduled_event(event_schedule: list[dict], step_index: int) -> dict | None:
    for ev in event_schedule:
        if ev.get("step") == step_index:
            return ev
    return None


def _apply_scheduled_event(state: TextState, event: dict) -> TextState:
    """Apply a reveal/shift/delay/noise event to the hidden state.

    Only _hidden_event_type and, for reveal, visible_text are modified.
    Grammar tokens are NEVER written into visible_text.
    """
    etype = event.get("type", "none")
    import copy as _copy
    new_state = _copy.copy(state)

    if etype == "reveal":
        new_state._hidden_event_type = "reveal"
        detail = event.get("detail", "")
        # Append generic reveal hint to visible_text (no grammar token)
        new_state.visible_text = state.visible_text + " [Additional information is now visible.]"
        new_state.blocker_state_public = None

    elif etype == "shift":
        new_state._hidden_event_type = "shift"

    elif etype == "delay":
        new_state._hidden_event_type = "delayed"

    elif etype == "noise":
        new_state._hidden_event_type = "noisy"

    else:
        new_state._hidden_event_type = "none"

    return new_state


def _compute_public_effect(
    pre_state: TextState,
    post_state: TextState,
    action_id: str,
    raw_effect_type: str,
) -> PublicEffect:
    """Compute a public-safe effect summary.

    No grammar token, regime name, or hidden field value is written
    into effect_type, dom_diff_public, or text_diff_public.
    """
    # Map internal effect types to public-safe labels
    _public_labels = {
        "task_complete":    "task_complete",
        "state_change":     "state_change",
        "no_state_change":  "no_state_change",
        "blocker_removed":  "blocker_removed",
        "delayed_effect":   "delayed_effect",
    }
    safe_effect = _public_labels.get(raw_effect_type, "no_state_change")

    text_diff = None
    if pre_state.visible_text != post_state.visible_text:
        text_diff = "state_text_updated"

    return PublicEffect(
        effect_type=safe_effect,
        dom_diff_public=None,
        text_diff_public=text_diff,
    )


def _build_training_labels(
    pre_state: TextState,
    post_state: TextState,
    action_id: str,
    engine: GrammarEngine,
    scheduled_event: dict | None,
    progress_delta: float,
    prev_effects: list[str] | None = None,
) -> TrainingLabels:
    event_type = engine.label_event_type(
        pre_state._hidden_preconditions,
        post_state._hidden_preconditions,
        scheduled_event,
    )
    if scheduled_event and scheduled_event.get("type") == "delay":
        event_type = "delayed"
    elif scheduled_event and scheduled_event.get("type") == "noise":
        event_type = "noisy"

    failed = not engine.precondition_satisfied(
        pre_state._hidden_preconditions, action_id
    )
    failure_reason = engine.label_failure_reason(
        pre_state._hidden_preconditions, action_id
    )
    recovery_action = engine.label_recovery_action(pre_state._hidden_preconditions)

    reveal_vs_shift = "none"
    if scheduled_event:
        stype = scheduled_event.get("type", "none")
        if stype in ("reveal", "shift"):
            reveal_vs_shift = stype

    # Detect hypothesis switch: this step succeeds after ≥2 consecutive prior failures
    hypothesis_switch = False
    if not failed and progress_delta > 0 and prev_effects:
        recent_fails = sum(1 for e in prev_effects[-3:] if e == "no_state_change")
        if recent_fails >= 2:
            hypothesis_switch = True

    return TrainingLabels(
        true_regime=pre_state._hidden_regime,
        true_control_grammar=pre_state._hidden_control_grammar,
        true_change_point=str(pre_state.step_index),
        true_reveal_vs_shift=reveal_vs_shift,
        true_action_effect_type=event_type,
        true_failed_action=failed,
        failure_reason=failure_reason,
        progress_delta=progress_delta,
        recovery_action_id=recovery_action,
        valid_hypothesis_switch=hypothesis_switch,
    )


def _build_evaluation_labels(
    pre_state: TextState,
    action_id: str,
    engine: GrammarEngine,
    policy_id: str,
    event_type: str,
) -> EvaluationLabels:
    is_wrong = engine.is_wrong_grammar_failure(
        pre_state._hidden_preconditions, action_id, event_type
    )
    return EvaluationLabels(
        true_wrong_hypothesis=is_wrong,
        h_exec_id=None,
        correct_hypothesis_id=pre_state._hidden_control_grammar,
        evidence_timestamp=pre_state.step_index,
        hypothesis_update_timestamp=None,
        recovery_timestamp=None,
        ood_type=None,
    )


def _update_visible_text(
    state: TextState,
    action_id: str,
    raw_effect_type: str,
    post_flags: dict,
) -> str:
    """Produce updated visible_text that never contains hidden grammar tokens."""
    if raw_effect_type == "task_complete":
        return "Task completed successfully."
    if raw_effect_type == "blocker_removed":
        return state.visible_text.replace("overlay_active", "").replace(
            "permission_required", "").strip() + " Blocker has been resolved."
    if raw_effect_type == "state_change":
        return state.visible_text + " (Interface updated.)"
    if raw_effect_type == "delayed_effect":
        return state.visible_text + " (Change pending.)"
    return state.visible_text  # no_state_change


def collect_episode(
    spec: TextEpisodeSpec,
    runner: PolicyMixtureRunner,
    rng: random.Random,
    config: CollectorConfig,
) -> EpisodeRecord:
    """Collect one full episode as an EpisodeRecord.

    Visibility contract is enforced per-step via assert_agent_observation_safe().
    Hidden fields are only ever written to TrainingLabels/EvaluationLabels/
    StepAuditMetadata, never to PublicObservation or history_public.
    """
    engine = GrammarEngine(spec.hidden_control_grammar)
    state = build_initial_state(spec)
    history: list[PublicHistoryItem] = []
    steps: list[StepRecord] = []

    for step_index in range(spec.max_steps):
        state.step_index = step_index

        # 1. Build sanitized public observation
        instruction = _format_instruction(spec, state)
        obs = build_public_observation(state, instruction, history)

        # 2. Pick policy and select action (policy may read state._hidden_* internally;
        #    result is only an action_type string — no hidden token written to obs)
        policy = runner.sample_policy(spec)
        action_type = policy.select(obs, history, state, engine, rng)
        action_record = ActionRecord(
            action_id=f"act_{spec.episode_id}_{step_index:03d}",
            action_type=action_type,
            action_params={},
            rewritten=False,
        )

        # 3. Apply grammar engine to hidden state
        scheduled_event = _pick_scheduled_event(spec.event_schedule, step_index)
        new_flags, progress_delta, raw_effect_type = engine.apply(
            state._hidden_preconditions, action_type
        )

        # 4. Build post_state (hidden fields updated; public fields derived safely)
        import copy as _copy
        post_state = _copy.copy(state)
        post_state._hidden_preconditions = new_flags
        post_state._hidden_progress_score = (
            state._hidden_progress_score + progress_delta
        )
        post_state.progress_public = min(1.0, post_state._hidden_progress_score)

        if raw_effect_type == "task_complete":
            new_flags["task_complete"] = True
            post_state._hidden_preconditions = new_flags

        new_visible = _update_visible_text(state, action_type, raw_effect_type, new_flags)
        post_state.visible_text = new_visible

        if scheduled_event is not None:
            post_state = _apply_scheduled_event(post_state, scheduled_event)

        event_type = post_state._hidden_event_type

        # 5. Compute public effect (safe labels only)
        public_effect = _compute_public_effect(state, post_state, action_type, raw_effect_type)

        # 6. Build training/eval labels from hidden state — never from obs
        prev_effects = [h.effect_summary for h in history]
        training_labels = _build_training_labels(
            state, post_state, action_type, engine, scheduled_event,
            progress_delta, prev_effects,
        )
        evaluation_labels = _build_evaluation_labels(
            state, action_type, engine, policy.policy_id, event_type
        )

        # 7. Build audit metadata (never agent input)
        audit = StepAuditMetadata(
            generator_version=config.generator_version,
            collection_timestamp=_now_iso(),
            policy_id=policy.policy_id,
            split_id=config.split_id,
            template_id=spec.task_family,
            seed=spec.seed,
        )

        step = StepRecord(
            step_id=f"{spec.episode_id}_step_{step_index:03d}",
            episode_id=spec.episode_id,
            step_index=step_index,
            public_observation=obs,
            action=action_record,
            observed_effect_public=public_effect,
            training_labels=training_labels,
            evaluation_labels=evaluation_labels,
            counterfactuals=[],
            audit_metadata=audit,
        )

        # 8. Validate per-step schema + visibility
        step_result = validate_step_schema(step)
        if not step_result.passed:
            raise SchemaValidationError(step_result.errors)

        steps.append(step)
        history.append(PublicHistoryItem(
            step_index=step_index,
            action_summary=action_type,
            effect_summary=public_effect.effect_type,
        ))

        state = post_state

        if engine.is_terminal(state._hidden_preconditions):
            break

    final_success = engine.is_success(state._hidden_preconditions)

    episode = EpisodeRecord(
        episode_id=spec.episode_id,
        dataset_version=config.dataset_version,
        schema_version=config.schema_version,
        generator_version=config.generator_version,
        split_id=config.split_id,
        task_family=spec.task_family,
        public_instruction=spec.public_instruction,
        steps=steps,
        final_success=final_success,
        total_progress=state.progress_public,
        audit_metadata=AuditMetadata(
            generator_version=config.generator_version,
            collection_timestamp=_now_iso(),
            schema_version=config.schema_version,
            split_id=config.split_id,
            template_id=spec.task_family,
            seed=spec.seed,
            policy_mixture=runner.policy_mixture_snapshot(),
        ),
    )

    ep_result = validate_episode_schema(episode)
    if not ep_result.passed:
        raise SchemaValidationError(ep_result.errors)

    vis_result = validate_visibility_contract(episode)
    if not vis_result.passed:
        raise HiddenLabelLeakageError(str(vis_result.errors))

    return episode
