"""Minimal GUI MVE task specifications."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class GUITaskType(str, Enum):
    CLICK = "CLICK"
    FILL = "FILL"
    NAVIGATE = "NAVIGATE"
    DRAG = "DRAG"


@dataclass(frozen=True)
class GUITaskSpec:
    """Task-level GUI metadata."""

    task_id: str
    task_type: GUITaskType
    description: str
    target_url: str
    expected_grammar: str
    difficulty: int
    regime: str

    def __post_init__(self) -> None:
        if not 1 <= self.difficulty <= 5:
            raise ValueError(f"difficulty must be in [1, 5], got {self.difficulty}")


MVE_TASK_SPECS: list[GUITaskSpec] = [
    GUITaskSpec(
        task_id="gui_mve_click_login",
        task_type=GUITaskType.CLICK,
        description="Click the login button from the account menu.",
        target_url="https://mve.local/account",
        expected_grammar="menu_open_then_click_primary",
        difficulty=1,
        regime="direct_click",
    ),
    GUITaskSpec(
        task_id="gui_mve_fill_search",
        task_type=GUITaskType.FILL,
        description="Enter a product query into the search field.",
        target_url="https://mve.local/search",
        expected_grammar="focus_input_type_submit",
        difficulty=1,
        regime="simple_form",
    ),
    GUITaskSpec(
        task_id="gui_mve_navigate_settings",
        task_type=GUITaskType.NAVIGATE,
        description="Navigate from the dashboard to settings.",
        target_url="https://mve.local/dashboard",
        expected_grammar="sidebar_select_destination",
        difficulty=2,
        regime="navigation",
    ),
    GUITaskSpec(
        task_id="gui_mve_drag_priority",
        task_type=GUITaskType.DRAG,
        description="Drag the priority card to the top of the list.",
        target_url="https://mve.local/tasks",
        expected_grammar="drag_reorder_list",
        difficulty=3,
        regime="reorder",
    ),
    GUITaskSpec(
        task_id="gui_mve_click_modal_confirm",
        task_type=GUITaskType.CLICK,
        description="Confirm the modal dialog action.",
        target_url="https://mve.local/modal",
        expected_grammar="modal_confirm",
        difficulty=2,
        regime="modal_gate",
    ),
    GUITaskSpec(
        task_id="gui_mve_fill_profile",
        task_type=GUITaskType.FILL,
        description="Fill the display name field in the profile form.",
        target_url="https://mve.local/profile",
        expected_grammar="form_field_update",
        difficulty=2,
        regime="profile_form",
    ),
    GUITaskSpec(
        task_id="gui_mve_navigate_breadcrumb",
        task_type=GUITaskType.NAVIGATE,
        description="Use the breadcrumb to return to the project page.",
        target_url="https://mve.local/project/settings",
        expected_grammar="breadcrumb_backtrack",
        difficulty=3,
        regime="hierarchical_nav",
    ),
    GUITaskSpec(
        task_id="gui_mve_drag_slider",
        task_type=GUITaskType.DRAG,
        description="Drag the volume slider to the requested level.",
        target_url="https://mve.local/preferences",
        expected_grammar="continuous_control_adjustment",
        difficulty=4,
        regime="range_control",
    ),
    GUITaskSpec(
        task_id="gui_mve_click_filter",
        task_type=GUITaskType.CLICK,
        description="Apply the active-only filter in a results toolbar.",
        target_url="https://mve.local/results",
        expected_grammar="toolbar_filter_toggle",
        difficulty=2,
        regime="filter_toggle",
    ),
    GUITaskSpec(
        task_id="gui_mve_fill_checkout_zip",
        task_type=GUITaskType.FILL,
        description="Enter the ZIP code during checkout.",
        target_url="https://mve.local/checkout",
        expected_grammar="checkout_address_field",
        difficulty=3,
        regime="multi_step_form",
    ),
]
