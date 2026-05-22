"""frcgw.text_env.generator — Task family templates and episode spec generator.

Source docs:
- paper_context_ref/04_TEXT_ONLY_SMOKE_TESTBED.md §5, §8, §14, §19
- paper_context_ref/12_DATA_COLLECTION_METHODOLOGY_v1.md §8 text-only, §13 scale
- paper_context_ref/06_DATA_SCHEMA_AND_LABELING.md §0.4 MVE
"""
from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass, field, replace
from enum import Enum

from frcgw.schemas.step_schema import CandidateAction
from frcgw.text_env.grammar import ControlGrammar
from frcgw.text_env.state import TextEpisodeSpec, TextState


class TaskFamily(str, Enum):
    SEARCH_FORM         = "search_form"
    REQUIRED_DROPDOWN   = "required_dropdown"
    MODAL_BLOCKER       = "modal_blocker"
    PAGINATION_VS_INF   = "pagination_vs_infinite"
    NESTED_SCROLL       = "nested_scroll"
    LOADING_DELAYED     = "loading_delayed"
    PERMISSION_GATE     = "permission_gate"
    FILTER_ACCORDION    = "filter_accordion"


OOD_GRAMMAR_FAMILIES = [TaskFamily.FILTER_ACCORDION, TaskFamily.NESTED_SCROLL]
ID_GRAMMAR_FAMILIES = [
    family for family in TaskFamily if family not in OOD_GRAMMAR_FAMILIES
]

# v0_5 compatible switch pairs (P0 fix — must have non-empty action-set overlap).
# Source: TASK_COLLECTOR_V05_SWITCH Reviewer-2 FATAL-1 resolution.
# Only pairs where at least one shared action exists so that post-switch steps
# can produce genuine wrong-hypothesis failures (recognisable action + failed
# precondition) rather than vocabulary-mismatch no-ops.
# Key pair: search_form <-> required_dropdown share {type_query, submit_search}.
_V0_5_COMPATIBLE_AFTER: dict[str, str] = {
    TaskFamily.SEARCH_FORM:      TaskFamily.REQUIRED_DROPDOWN,
    TaskFamily.REQUIRED_DROPDOWN: TaskFamily.SEARCH_FORM,
}


# ---------------------------------------------------------------------------
# Per-family action sets (public labels only — no grammar tokens)
# ---------------------------------------------------------------------------

_FAMILY_ACTIONS: dict[str, list[CandidateAction]] = {
    TaskFamily.SEARCH_FORM: [
        CandidateAction("type_query", "type_query"),
        CandidateAction("submit_search", "submit_search"),
        CandidateAction("wait", "wait"),
    ],
    TaskFamily.REQUIRED_DROPDOWN: [
        CandidateAction("open_dropdown", "open_dropdown"),
        CandidateAction("select_category", "select_category"),
        CandidateAction("type_query", "type_query"),
        CandidateAction("submit_search", "submit_search"),
        CandidateAction("wait", "wait"),
    ],
    TaskFamily.MODAL_BLOCKER: [
        CandidateAction("close_modal", "close_modal"),
        CandidateAction("click_filter", "click_filter"),
        CandidateAction("wait", "wait"),
    ],
    TaskFamily.PAGINATION_VS_INF: [
        CandidateAction("load_more", "load_more"),
        CandidateAction("view_item", "view_item"),
        CandidateAction("scroll_page", "scroll_page"),
        CandidateAction("click_next_page", "click_next_page"),
        CandidateAction("wait", "wait"),
    ],
    TaskFamily.NESTED_SCROLL: [
        CandidateAction("scroll_container", "scroll_container"),
        CandidateAction("select_item", "select_item"),
        CandidateAction("scroll_page", "scroll_page"),
        CandidateAction("wait", "wait"),
    ],
    TaskFamily.LOADING_DELAYED: [
        CandidateAction("wait", "wait"),
        CandidateAction("click_result", "click_result"),
        CandidateAction("scroll_page", "scroll_page"),
    ],
    TaskFamily.PERMISSION_GATE: [
        CandidateAction("accept_permission", "accept_permission"),
        CandidateAction("click_share", "click_share"),
        CandidateAction("wait", "wait"),
    ],
    TaskFamily.FILTER_ACCORDION: [
        CandidateAction("expand_section", "expand_section"),
        CandidateAction("click_price_filter", "click_price_filter"),
        CandidateAction("wait", "wait"),
    ],
}

# Grammar assigned to each task family (hidden, for generator use only)
_FAMILY_GRAMMAR: dict[str, str] = {
    TaskFamily.SEARCH_FORM:       ControlGrammar.DIRECT_SEARCH,
    TaskFamily.REQUIRED_DROPDOWN: ControlGrammar.REQUIRED_DROPDOWN_THEN_SEARCH,
    TaskFamily.MODAL_BLOCKER:     ControlGrammar.MODAL_CONFIRM_THEN_ACTION,
    TaskFamily.PAGINATION_VS_INF: ControlGrammar.PAGINATION_OR_INFINITE_SCROLL,
    TaskFamily.NESTED_SCROLL:     ControlGrammar.CONTAINER_SCROLL_THEN_SELECT,
    TaskFamily.LOADING_DELAYED:   ControlGrammar.WAIT_UNTIL_ENABLED_THEN_CLICK,
    TaskFamily.PERMISSION_GATE:   ControlGrammar.PERMISSION_ACCEPT_THEN_ACTION,
    TaskFamily.FILTER_ACCORDION:  ControlGrammar.FILTER_OPEN_THEN_SELECT,
}

# Instruction paraphrases (≥3 per family, no grammar tokens in text)
_INSTRUCTIONS: dict[str, list[str]] = {
    TaskFamily.SEARCH_FORM: [
        "Find a wireless mouse.",
        "Search for wireless mice in the catalogue.",
        "Look up wireless mouse products.",
    ],
    TaskFamily.REQUIRED_DROPDOWN: [
        "Search by category.",
        "Filter results using the category selector.",
        "Select a category and run the search.",
    ],
    TaskFamily.MODAL_BLOCKER: [
        "Open the filter panel.",
        "Access the filtering options.",
        "Bring up the filter interface.",
    ],
    TaskFamily.PAGINATION_VS_INF: [
        "Show me more results.",
        "Load additional items in the list.",
        "Reveal more entries below.",
    ],
    TaskFamily.NESTED_SCROLL: [
        "View more comments.",
        "Read the remaining comments in the panel.",
        "Scroll through all comments.",
    ],
    TaskFamily.LOADING_DELAYED: [
        "Open the first result.",
        "Click the top search result.",
        "Select the first item in the result list.",
    ],
    TaskFamily.PERMISSION_GATE: [
        "Share this document.",
        "Send this document to a collaborator.",
        "Enable sharing for this file.",
    ],
    TaskFamily.FILTER_ACCORDION: [
        "Set a price filter.",
        "Apply a price range to the results.",
        "Filter items by price.",
    ],
}

# Initial visible_text paraphrases (≥3 per family, no grammar tokens)
_INITIAL_STATES: dict[str, list[str]] = {
    TaskFamily.SEARCH_FORM: [
        "Search bar visible. Submit button is greyed out.",
        "A text input field is available. The search button appears inactive.",
        "Input box ready. Search cannot be submitted yet.",
    ],
    TaskFamily.REQUIRED_DROPDOWN: [
        "Search bar and a collapsed category selector are visible.",
        "A text field and a closed category menu are displayed.",
        "Search input available. A category chooser sits beside it, currently closed.",
    ],
    TaskFamily.MODAL_BLOCKER: [
        "Filter button is visible. A notice overlay is active on the screen.",
        "The filter option is available, but a dialog is covering the interface.",
        "A consent pop-up is displayed in front of the main content.",
    ],
    TaskFamily.PAGINATION_VS_INF: [
        "Result list is displayed. Footer reads 'scroll for more'.",
        "Items are listed below. At the bottom, a navigation control is shown.",
        "A list of results is visible. More items can be revealed.",
    ],
    TaskFamily.NESTED_SCROLL: [
        "Comments panel is inside a scrollable container.",
        "A scrollable area contains the comment thread.",
        "The comments section is embedded in a contained region.",
    ],
    TaskFamily.LOADING_DELAYED: [
        "Search results are loading. Items are not yet interactive.",
        "Content is being fetched. The result list appears greyed.",
        "Page is loading. Results will appear shortly.",
    ],
    TaskFamily.PERMISSION_GATE: [
        "Share button is visible. An access prompt is active.",
        "Sharing option is present. A permission dialog is displayed.",
        "The share control is available, but an authorisation step is required.",
    ],
    TaskFamily.FILTER_ACCORDION: [
        "Filter section header is collapsed.",
        "Price filter is not currently visible.",
        "A collapsed section contains the price settings.",
    ],
}

# Event schedules per family (type: reveal|shift|delay|noise)
# step -1 means no event
_EVENT_SCHEDULES: dict[str, list[dict]] = {
    TaskFamily.SEARCH_FORM:       [{"step": 2, "type": "reveal", "detail": "dropdown_appears"}],
    TaskFamily.REQUIRED_DROPDOWN: [{"step": 2, "type": "shift", "detail": "grammar_to_direct_search"}],
    TaskFamily.MODAL_BLOCKER:     [{"step": 1, "type": "shift", "detail": "ui_mode_change"}],
    TaskFamily.PAGINATION_VS_INF: [{"step": 1, "type": "shift", "detail": "pagination_mode_switch"}],
    TaskFamily.NESTED_SCROLL:     [{"step": 1, "type": "shift", "detail": "scroll_layout_change"}],
    TaskFamily.LOADING_DELAYED:   [{"step": 1, "type": "delay", "detail": "button_enables_after_wait"}],
    TaskFamily.PERMISSION_GATE:   [{"step": 1, "type": "reveal", "detail": "permission_text_shown"}],
    TaskFamily.FILTER_ACCORDION:  [{"step": 2, "type": "reveal", "detail": "filter_options_shown"}],
}


@dataclass
class TaskFamilyTemplate:
    family: str
    grammar: str
    instructions: list[str]
    initial_states: list[str]
    actions: list[CandidateAction]
    event_schedules: list[dict]


def _build_templates() -> dict[str, TaskFamilyTemplate]:
    return {
        family: TaskFamilyTemplate(
            family=family,
            grammar=_FAMILY_GRAMMAR[family],
            instructions=_INSTRUCTIONS[family],
            initial_states=_INITIAL_STATES[family],
            actions=_FAMILY_ACTIONS[family],
            event_schedules=_EVENT_SCHEDULES[family],
        )
        for family in TaskFamily
    }


TASK_FAMILY_TEMPLATES: dict[str, TaskFamilyTemplate] = _build_templates()


class EpisodeSpecGenerator:
    """Generates TextEpisodeSpec instances deterministically from a seed.

    Each call to generate() produces a unique episode_id based on
    a running counter seeded by the base seed.
    """

    def __init__(self, seed: int = 0, max_steps: int = 12) -> None:
        self._base_seed = seed
        self._max_steps = max_steps
        self._counter = 0
        self._rng = random.Random(seed)

    def generate(self, family: str | None = None, rng: random.Random | None = None) -> TextEpisodeSpec:
        if rng is None:
            rng = random.Random(self._base_seed + self._counter)
        self._counter += 1

        if family is None:
            family = rng.choice(ID_GRAMMAR_FAMILIES)

        return self._generate_spec(family, rng)

    def _generate_spec(self, family: str, rng: random.Random) -> TextEpisodeSpec:
        template = TASK_FAMILY_TEMPLATES[family]
        instruction = rng.choice(template.instructions)
        initial_state_text = rng.choice(template.initial_states)

        ep_seed = self._base_seed + self._counter
        episode_id = _make_episode_id(family, ep_seed)

        return TextEpisodeSpec(
            episode_id=episode_id,
            task_family=family,
            public_instruction=instruction,
            initial_state_template=initial_state_text,
            hidden_regime=family,            # regime == family in P2
            hidden_control_grammar=template.grammar,
            event_schedule=list(template.event_schedules),
            max_steps=self._max_steps,
            seed=ep_seed,
        )

    def generate_v0_5(
        self,
        family: str | None = None,
        rng: random.Random | None = None,
    ) -> TextEpisodeSpec:
        """Generate a v0_5 episode with an intra-episode regime switch.

        After regime_switch_step, the hidden control grammar changes to a
        different family grammar (same-action / different-effect pattern).
        regime_switch_t is written to EvaluationLabels by the collector —
        it is FORBIDDEN_AGENT_FIELDS and must never enter PublicObservation.
        """
        if rng is None:
            rng = random.Random(self._base_seed + self._counter)
        self._counter += 1

        if family is None:
            family = rng.choice(ID_GRAMMAR_FAMILIES)

        spec = self._generate_spec(family, rng)

        # Sample switch step in [2, max_steps-2] to ensure non-trivial switch
        switch_step = rng.randint(2, max(2, spec.max_steps - 2))

        # Pick compatible after-family (action-set overlap → genuine wrong-hypothesis
        # failures post-switch, not vocabulary-mismatch no-ops).
        # Falls back to any other family only if no compatible pair is defined.
        family_after = _V0_5_COMPATIBLE_AFTER.get(family)
        if family_after is None:
            other_families = [f for f in TaskFamily if f != family]
            family_after = rng.choice(other_families)

        return TextEpisodeSpec(
            episode_id=spec.episode_id + "_v0_5",
            task_family=spec.task_family,
            public_instruction=spec.public_instruction,
            initial_state_template=spec.initial_state_template,
            hidden_regime=spec.hidden_regime,
            hidden_control_grammar=spec.hidden_control_grammar,
            event_schedule=spec.event_schedule,
            max_steps=spec.max_steps,
            seed=spec.seed,
            ood_type="regime_switch",
            regime_switch_step=switch_step,
            hidden_regime_after=family_after,
        )

    def generate_batch(
        self, n: int, family: str | None = None
    ) -> list[TextEpisodeSpec]:
        rng = random.Random(self._base_seed)
        return [self.generate(family=family, rng=rng) for _ in range(n)]

    def generate_v0_5_batch(
        self, n: int, family: str | None = None
    ) -> list[TextEpisodeSpec]:
        """Generate n v0_5 episodes with intra-episode regime switches."""
        rng = random.Random(self._base_seed)
        return [self.generate_v0_5(family=family, rng=rng) for _ in range(n)]

    def generate_ood(self, n: int, ood_type: str = "grammar_shift") -> list[TextEpisodeSpec]:
        """Generate OOD episode specs using held-out grammar families."""
        specs = []
        for _ in range(n):
            family = self._rng.choice(OOD_GRAMMAR_FAMILIES)
            spec = self.generate(family=family, rng=self._rng)
            specs.append(replace(spec, ood_type=ood_type))
        return specs


def build_initial_state(spec: TextEpisodeSpec) -> TextState:
    """Construct the initial TextState from a TextEpisodeSpec."""
    template = TASK_FAMILY_TEMPLATES[spec.task_family]
    return TextState(
        visible_text=spec.initial_state_template,
        public_actions=list(template.actions),
        progress_public=0.0,
        blocker_state_public=_initial_blocker_label(spec.task_family),
        step_index=0,
        _hidden_regime=spec.hidden_regime,
        _hidden_control_grammar=spec.hidden_control_grammar,
        _hidden_preconditions={},
        _hidden_progress_score=0.0,
        _hidden_blocker_id=_initial_blocker_id(spec.task_family),
        _hidden_event_type="none",
    )


def _initial_blocker_label(family: str) -> str | None:
    _blockers = {
        TaskFamily.MODAL_BLOCKER: "overlay_active",
        TaskFamily.LOADING_DELAYED: "loading",
        TaskFamily.PERMISSION_GATE: "permission_required",
    }
    return _blockers.get(family)


def _initial_blocker_id(family: str) -> str | None:
    _ids = {
        TaskFamily.MODAL_BLOCKER: "modal_001",
        TaskFamily.LOADING_DELAYED: "loader_001",
        TaskFamily.PERMISSION_GATE: "perm_001",
    }
    return _ids.get(family)


def _make_episode_id(family: str, seed: int) -> str:
    h = hashlib.md5(f"{family}:{seed}".encode()).hexdigest()[:8]
    return f"ep_{family}_{h}"
