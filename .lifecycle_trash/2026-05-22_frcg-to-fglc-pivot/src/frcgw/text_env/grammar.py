"""frcgw.text_env.grammar — Control grammar engine for text-only episodes.

Source docs:
- paper_context_ref/03_CORE_CONCEPT_TAXONOMY.md §3, §6, §11 reveal/shift
- paper_context_ref/04_TEXT_ONLY_SMOKE_TESTBED.md §5, §9, §19
- paper_context_ref/12_DATA_COLLECTION_METHODOLOGY_v1.md §7 buckets, §10 failure/recovery
"""
from __future__ import annotations

import copy
from enum import Enum


class ControlGrammar(str, Enum):
    DIRECT_SEARCH                 = "direct_search"
    REQUIRED_DROPDOWN_THEN_SEARCH = "required_dropdown_then_search"
    MODAL_CONFIRM_THEN_ACTION     = "modal_confirm_then_action"
    CONTAINER_SCROLL_THEN_SELECT  = "container_scroll_then_select"
    WAIT_UNTIL_ENABLED_THEN_CLICK = "wait_until_enabled_then_click"
    PERMISSION_ACCEPT_THEN_ACTION = "permission_accept_then_action"
    FILTER_OPEN_THEN_SELECT       = "filter_open_then_select"
    PAGINATION_OR_INFINITE_SCROLL = "pagination_or_infinite_scroll"


# ---------------------------------------------------------------------------
# Grammar rule tables
# Each grammar defines:
#   prereq_actions : ordered list of actions that must execute first
#   final_action   : the action that completes the task
#   precondition   : dict[action_id -> prerequisite state key that must be True]
#   effect_map     : dict[action_id -> (progress_delta, effect_type, sets_state_key)]
# ---------------------------------------------------------------------------

_GRAMMAR_RULES: dict[str, dict] = {
    ControlGrammar.DIRECT_SEARCH: {
        "prereq_actions": ["type_query"],
        "final_action": "submit_search",
        "preconditions": {
            "submit_search": "query_typed",
        },
        "effect_map": {
            "type_query": (0.4, "state_change", "query_typed"),
            "submit_search": (0.6, "task_complete", None),
        },
    },
    ControlGrammar.REQUIRED_DROPDOWN_THEN_SEARCH: {
        "prereq_actions": ["open_dropdown", "select_category", "type_query"],
        "final_action": "submit_search",
        "preconditions": {
            "select_category": "dropdown_open",
            "type_query": "category_selected",
            "submit_search": "query_typed",
        },
        "effect_map": {
            "open_dropdown": (0.2, "state_change", "dropdown_open"),
            "select_category": (0.2, "state_change", "category_selected"),
            "type_query": (0.2, "state_change", "query_typed"),
            "submit_search": (0.4, "task_complete", None),
        },
    },
    ControlGrammar.MODAL_CONFIRM_THEN_ACTION: {
        "prereq_actions": ["close_modal"],
        "final_action": "click_filter",
        "preconditions": {
            "click_filter": "modal_closed",
        },
        "effect_map": {
            "close_modal": (0.4, "blocker_removed", "modal_closed"),
            "click_filter": (0.6, "task_complete", None),
        },
    },
    ControlGrammar.CONTAINER_SCROLL_THEN_SELECT: {
        "prereq_actions": ["scroll_container"],
        "final_action": "select_item",
        "preconditions": {
            "select_item": "container_scrolled",
        },
        "effect_map": {
            "scroll_container": (0.5, "state_change", "container_scrolled"),
            "select_item": (0.5, "task_complete", None),
        },
    },
    ControlGrammar.WAIT_UNTIL_ENABLED_THEN_CLICK: {
        "prereq_actions": ["wait"],
        "final_action": "click_result",
        "preconditions": {
            "click_result": "button_enabled",
        },
        "effect_map": {
            "wait": (0.3, "delayed_effect", "button_enabled"),
            "click_result": (0.7, "task_complete", None),
        },
    },
    ControlGrammar.PERMISSION_ACCEPT_THEN_ACTION: {
        "prereq_actions": ["accept_permission"],
        "final_action": "click_share",
        "preconditions": {
            "click_share": "permission_accepted",
        },
        "effect_map": {
            "accept_permission": (0.4, "blocker_removed", "permission_accepted"),
            "click_share": (0.6, "task_complete", None),
        },
    },
    ControlGrammar.FILTER_OPEN_THEN_SELECT: {
        "prereq_actions": ["expand_section"],
        "final_action": "click_price_filter",
        "preconditions": {
            "click_price_filter": "section_expanded",
        },
        "effect_map": {
            "expand_section": (0.4, "state_change", "section_expanded"),
            "click_price_filter": (0.6, "task_complete", None),
        },
    },
    ControlGrammar.PAGINATION_OR_INFINITE_SCROLL: {
        "prereq_actions": ["load_more"],
        "final_action": "view_item",
        "preconditions": {
            "view_item": "more_loaded",
        },
        "effect_map": {
            "load_more": (0.5, "state_change", "more_loaded"),
            "view_item": (0.5, "task_complete", None),
        },
    },
}


class GrammarEngine:
    """Deterministic control grammar evaluator.

    Reads _hidden_* fields from TextState; outputs are used to build
    TrainingLabels and EvaluationLabels. Results must NEVER flow into
    PublicObservation (06_DATA_SCHEMA §4).
    """

    def __init__(self, grammar: str) -> None:
        if grammar not in _GRAMMAR_RULES:
            raise ValueError(f"Unknown grammar: {grammar!r}")
        self._grammar = grammar
        self._rules = _GRAMMAR_RULES[grammar]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def precondition_satisfied(self, hidden_state_flags: dict, action_id: str) -> bool:
        required_key = self._rules["preconditions"].get(action_id)
        if required_key is None:
            return True  # no precondition for this action
        return bool(hidden_state_flags.get(required_key, False))

    def expected_effect(self, action_id: str) -> str:
        entry = self._rules["effect_map"].get(action_id)
        if entry is None:
            return "no_effect"
        return entry[1]

    def apply(self, hidden_state_flags: dict, action_id: str) -> tuple[dict, float, str]:
        """Apply action to hidden state.

        Returns (new_hidden_state_flags, progress_delta, effect_type).
        If precondition not satisfied, returns no_state_change + 0.0 delta.
        """
        new_flags = copy.copy(hidden_state_flags)
        if not self.precondition_satisfied(hidden_state_flags, action_id):
            return new_flags, 0.0, "no_state_change"

        entry = self._rules["effect_map"].get(action_id)
        if entry is None:
            return new_flags, 0.0, "no_state_change"

        progress_delta, effect_type, sets_key = entry
        if sets_key is not None:
            new_flags[sets_key] = True
        return new_flags, progress_delta, effect_type

    def label_failure_reason(self, hidden_state_flags: dict, action_id: str) -> str | None:
        if not self.precondition_satisfied(hidden_state_flags, action_id):
            required_key = self._rules["preconditions"].get(action_id)
            return f"precondition_not_met:{required_key}"
        return None

    def label_recovery_action(self, hidden_state_flags: dict) -> str | None:
        """Return the next prerequisite action that should be taken.

        An action is 'done' when the state key it sets is present in flags.
        If all prereq actions are done, return the final action.
        """
        for action_id in self._rules["prereq_actions"]:
            entry = self._rules["effect_map"].get(action_id)
            if entry is None:
                continue
            _, _, sets_key = entry
            # If this prereq sets a state key and it's not yet set, do it
            if sets_key is not None and not hidden_state_flags.get(sets_key, False):
                return action_id
        return self._rules["final_action"]

    def is_wrong_grammar_failure(
        self,
        hidden_state_flags: dict,
        action_id: str,
        event_type: str,
    ) -> bool:
        """True iff all 4 conditions from CONST-04-001~04-006 are met.

        Conditions:
        1. action_id is recognisable (in the grammar action space).
        2. precondition_satisfied == False.
        3. expected_effect != observed ("no_state_change" mismatch).
        4. event_type is not delayed or noisy (REVISION-03-011, BOUNDARY-03-017).
        """
        all_actions = set(self._rules["effect_map"].keys())
        if action_id not in all_actions:
            return False
        if self.precondition_satisfied(hidden_state_flags, action_id):
            return False
        if event_type in ("delayed", "noisy"):
            return False
        return True

    def label_event_type(
        self,
        prev_flags: dict,
        post_flags: dict,
        scheduled: dict | None,
    ) -> str:
        """Classify the event type for this step transition."""
        if scheduled is not None:
            stype = scheduled.get("type", "none")
            if stype in ("reveal", "shift", "delay", "noise"):
                if stype == "delay":
                    return "delayed"
                if stype == "noise":
                    return "noisy"
                return stype  # "reveal" | "shift"
        if prev_flags != post_flags:
            return "none"  # normal state change
        return "none"

    def is_terminal(self, hidden_state_flags: dict) -> bool:
        final = self._rules["final_action"]
        entry = self._rules["effect_map"].get(final)
        if entry is None:
            return False
        _, _, sets_key = entry
        # terminal when task_complete effect has been applied (sets_key is None
        # for terminal action) or the final action was successful
        final_prereq = self._rules["preconditions"].get(final)
        if final_prereq is not None and not hidden_state_flags.get(final_prereq, False):
            return False
        return hidden_state_flags.get("task_complete", False)

    def is_success(self, hidden_state_flags: dict) -> bool:
        return hidden_state_flags.get("task_complete", False)
