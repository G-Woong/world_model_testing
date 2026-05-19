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
    CounterfactualRecord,
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

# v0_5: TaskFamily -> ControlGrammar string mapping.
# Mirrors generator._FAMILY_GRAMMAR; kept local to avoid circular import.
# Source: paper_context_ref/12_DATA_COLLECTION_METHODOLOGY.md §8 v0_5 switch.
_V0_5_FAMILY_TO_GRAMMAR: dict[str, str] = {
    "search_form":           "direct_search",
    "required_dropdown":     "required_dropdown_then_search",
    "modal_blocker":         "modal_confirm_then_action",
    "nested_scroll":         "container_scroll_then_select",
    "loading_delayed":       "wait_until_enabled_then_click",
    "permission_gate":       "permission_accept_then_action",
    "filter_accordion":      "filter_open_then_select",
    "pagination_vs_infinite": "pagination_or_infinite_scroll",
}


@dataclass
class CollectorConfig:
    dataset_version: str = "0.1"
    schema_version: str = "schema-06-v0.1"
    generator_version: str = "p2-text-v0.1"
    split_id: str = "train"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _build_counterfactuals(
    pre_state: TextState,
    actual_action_type: str,
    candidates: list[CandidateAction],
    engine: GrammarEngine,
    rng: random.Random,
) -> list[CounterfactualRecord]:
    from frcgw.text_env.counterfactual_rollout import generate_counterfactuals

    return generate_counterfactuals(
        pre_state=pre_state,
        actual_action_id=actual_action_type,
        candidates=candidates,
        engine=engine,
        top_k=3,
        rng=rng,
    )


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
    is_post_v0_5_switch: bool = False,
    active_engine: GrammarEngine | None = None,
) -> EvaluationLabels:
    """Build EvaluationLabels for one step.

    Post-switch (is_post_v0_5_switch=True) uses active_engine
    (the new grammar) to evaluate is_wrong_grammar_failure. This produces
    genuine wrong-hypothesis labels: the action is recognisable in the new
    grammar but fails its precondition — exactly the wrong-hypothesis
    persistence pattern defined in paper §CONST-04-001.

    P1 fix (TASK_COLLECTOR_V05_SWITCH): replaced unconditional is_wrong=True
    override with active_engine.is_wrong_grammar_failure(), so only steps
    where the action is in the new grammar's action space AND the precondition
    fails count as wrong-hypothesis. Vocabulary-mismatch steps (action not in
    new grammar) do NOT count — they are no_state_change with is_wrong=False.
    This label stays in EvaluationLabels and never enters PublicObservation.
    """
    if is_post_v0_5_switch and active_engine is not None:
        # Use new grammar to check: is this action recognisable but precondition-blocked?
        is_wrong = active_engine.is_wrong_grammar_failure(
            pre_state._hidden_preconditions, action_id, event_type
        )
    else:
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
        true_regime=pre_state._hidden_regime,
    )


def _backfill_v0_5_switch_labels(
    steps: list[StepRecord],
    regime_switch_step: int | None,
) -> list[StepRecord]:
    """Backfill regime_switch_t into all step EvaluationLabels for v0_5 episodes.

    regime_switch_t records WHEN the switch happened (eval-only, FORBIDDEN_AGENT_FIELDS).
    It is set on EVERY step of a switch episode (not just post-switch steps) so
    metrics can compute detection_delay = alarm_step - regime_switch_t.
    MUST NOT appear in TrainingLabels or PublicObservation.
    """
    if regime_switch_step is None:
        return steps

    import dataclasses

    patched = []
    for step in steps:
        new_eval = dataclasses.replace(step.evaluation_labels, regime_switch_t=regime_switch_step)
        patched.append(dataclasses.replace(step, evaluation_labels=new_eval))
    return patched


def _backfill_episode_timestamps(
    steps: list[StepRecord],
    ood_type: str | None,
) -> list[StepRecord]:
    """Episode-level post-pass for Step 3 evaluation-only labels.

    Source: docs/orchestration/lr_alignment/19_step3_dataset_backfill_plan.md 짠5.1
    """
    import dataclasses

    evidence_ts = next(
        (
            i
            for i, step in enumerate(steps)
            if step.evaluation_labels.true_wrong_hypothesis
        ),
        None,
    )

    hyp_update_ts = None
    for i, step in enumerate(steps):
        if step.training_labels.valid_hypothesis_switch:
            hyp_update_ts = i
            break

    recovery_ts = None
    for i, step in enumerate(steps):
        if i == 0:
            continue
        prior_wrong = steps[i - 1].evaluation_labels.true_wrong_hypothesis
        tl = step.training_labels
        if (
            prior_wrong
            and step.action.action_type == tl.recovery_action_id
            and tl.progress_delta > 0
        ):
            recovery_ts = i
            break

    patched = []
    for step in steps:
        new_eval = dataclasses.replace(
            step.evaluation_labels,
            evidence_timestamp=evidence_ts,
            hypothesis_update_timestamp=hyp_update_ts,
            recovery_timestamp=recovery_ts,
            ood_type=ood_type,
        )
        patched.append(dataclasses.replace(step, evaluation_labels=new_eval))
    return patched


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

    v0_5 intra-episode switch (TASK_COLLECTOR_V05_SWITCH):
    When spec.regime_switch_step is set, the active GrammarEngine is replaced
    with the engine for spec.hidden_regime_after at that step. The agent
    continues to select actions under the original grammar (PolicyMixtureRunner
    does not observe the switch), so post-switch actions produce no_state_change
    in the new engine — this is the genuine action-outcome mismatch signal that
    the Learned Falsification Detector (LFD) is trained to detect.
    true_wrong_hypothesis=True is written to EvaluationLabels ONLY (never
    PublicObservation or training visible fields).
    """
    engine = GrammarEngine(spec.hidden_control_grammar)
    # v0_5: active_engine switches at regime_switch_step; engine (original) kept
    # for label resolution and policy context.
    active_engine = engine
    v0_5_switch_step: int | None = getattr(spec, "regime_switch_step", None)
    v0_5_after_family: str | None = getattr(spec, "hidden_regime_after", None)
    _v0_5_switched = False  # tracks whether switch has been applied

    state = build_initial_state(spec)
    history: list[PublicHistoryItem] = []
    steps: list[StepRecord] = []

    for step_index in range(spec.max_steps):
        # v0_5: apply grammar switch at the designated step (oracle-free transition)
        if (
            v0_5_switch_step is not None
            and step_index == v0_5_switch_step
            and v0_5_after_family is not None
            and not _v0_5_switched
        ):
            # TaskFamily is a str,Enum — use .value to get "modal_blocker" etc.
            after_family_str = (
                v0_5_after_family.value
                if hasattr(v0_5_after_family, "value")
                else str(v0_5_after_family)
            )
            after_grammar = _V0_5_FAMILY_TO_GRAMMAR.get(after_family_str)
            if after_grammar is not None:
                try:
                    active_engine = GrammarEngine(after_grammar)
                    _v0_5_switched = True
                except ValueError:
                    pass  # unknown grammar — keep original engine
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
            # Run 4B: populate predicted hypothesis trace from policy belief.
            # NOT oracle label — EvaluationLabels.h_exec_id is separate and unchanged.
            selected_hypothesis_id=getattr(policy, "last_selected_hypothesis_id", None),
            selected_hypothesis_type=getattr(policy, "last_selected_hypothesis_type", None),
            selected_hypothesis_confidence=getattr(policy, "last_selected_hypothesis_confidence", None),
            selected_hypothesis_source=getattr(policy, "last_selected_hypothesis_source", None),
        )

        # 3. Apply grammar engine to hidden state
        # v0_5: use active_engine (may be the switched grammar post-switch) so
        # that post-switch actions produce no_state_change in the new grammar.
        # The original engine is still used for policy selection (step 2 above)
        # and terminal check (end of loop) to preserve agent's wrong hypothesis.
        scheduled_event = _pick_scheduled_event(spec.event_schedule, step_index)
        new_flags, progress_delta, raw_effect_type = active_engine.apply(
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
        # Training labels use active_engine to correctly reflect post-switch effects.
        training_labels = _build_training_labels(
            state, post_state, action_type, active_engine, scheduled_event,
            progress_delta, prev_effects,
        )
        # v0_5: pass active_engine so post-switch uses new grammar's is_wrong_grammar_failure.
        # P1 fix: unconditional is_wrong=True override removed; genuine wrong-hypothesis
        # requires action to be recognisable in new grammar AND precondition to fail.
        evaluation_labels = _build_evaluation_labels(
            state, action_type, engine, policy.policy_id, event_type,
            is_post_v0_5_switch=_v0_5_switched,
            active_engine=active_engine if _v0_5_switched else None,
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
            counterfactuals=_build_counterfactuals(
                state,
                action_record.action_type,
                list(obs.candidate_actions_public),
                active_engine,
                rng,
            ),
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

    # Post-pass: backfill episode-level timestamps.
    ood_type = getattr(spec, "ood_type", None)
    steps = _backfill_episode_timestamps(steps, ood_type)

    # Post-pass: backfill v0_5 regime_switch_t (eval-only, FORBIDDEN_AGENT_FIELDS).
    # regime_switch_t never enters PublicObservation; it goes only to EvaluationLabels.
    regime_switch_step = getattr(spec, "regime_switch_step", None)
    steps = _backfill_v0_5_switch_labels(steps, regime_switch_step)

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
