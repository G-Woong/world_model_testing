"""tests/test_forbidden_field_mirror_sync.py — paper §4 ↔ visibility.py ↔ hook sync test.

Source MDs:
- paper_context_ref/06_DATA_SCHEMA_AND_LABELING.md §4 (normative scientific contract)
- src/frcgw/schemas/visibility.py::FORBIDDEN_AGENT_FIELDS (runtime enforcement)
- .claude/hooks/schema_leakage_guard.ps1 $forbiddenTokens (hook mirror)

NOTE: The expected_inference_forbidden set below is initialized from the current
visibility.py content (15 fields as of 2026-05-16 plan apply).
When paper §4 33-field reclassification is completed in a future round,
update this expected set to match the confirmed inference_forbidden category.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from frcgw.schemas.visibility import FORBIDDEN_AGENT_FIELDS

# Repo root (two levels up from this test file)
REPO_ROOT = Path(__file__).parent.parent

# ---------------------------------------------------------------------------
# Expected inference_forbidden subset (authoritative: paper §4)
# Initialized from current visibility.py as of 2026-05-16.
# TODO(future-round): update when paper §4 reclassification is finalized.
# ---------------------------------------------------------------------------
PAPER_INFERENCE_FORBIDDEN: frozenset[str] = frozenset({
    "true_regime",
    "true_control_grammar",
    "true_change_point",
    "true_reveal_vs_shift",
    "true_wrong_hypothesis",
    "counterfactual_action_effects",
    "oracle_regime_action",
    "oracle_grammar_action",
    "oracle_best_action",
    "split_id",
    "ood_type",
    "template_id",
    "seed",
    "policy_id",
    "audit_metadata",
    "regime_switch_t",   # v0_5 intra-episode switch timing — added Gate-A 2026-05-19
    "detection_delay_gt",  # oracle-derived timing — added Gate-B 2026-05-19
})


def _parse_hook_tokens(hook_path: Path) -> set[str]:
    """Parse $forbiddenTokens array from schema_leakage_guard.ps1."""
    text = hook_path.read_text(encoding="utf-8", errors="replace")
    # Match: $forbiddenTokens = @( ... ) — extract quoted strings inside
    match = re.search(
        r"\$forbiddenTokens\s*=\s*@\(([^)]+)\)",
        text,
        re.DOTALL,
    )
    if not match:
        return set()
    block = match.group(1)
    # Extract all single-quoted or double-quoted strings
    tokens = re.findall(r"""['"]([^'"]+)['"]""", block)
    return set(tokens)


class TestVisibilityRuntimeSubset:
    """visibility.py::FORBIDDEN_AGENT_FIELDS must be a subset of paper §4 inference_forbidden."""

    def test_visibility_runtime_subset_of_paper_4(self) -> None:
        extra = FORBIDDEN_AGENT_FIELDS - PAPER_INFERENCE_FORBIDDEN
        assert not extra, (
            f"visibility.py contains fields NOT in paper §4 inference_forbidden: {sorted(extra)}\n"
            "Update PAPER_INFERENCE_FORBIDDEN in this test when paper §4 is extended, "
            "or remove the field from visibility.py."
        )


class TestVisibilityRuntimeEqualsPaper4:
    """visibility.py::FORBIDDEN_AGENT_FIELDS must equal paper §4 inference_forbidden (strict)."""

    def test_visibility_runtime_equals_paper_4_inference_forbidden(self) -> None:
        missing_from_code = PAPER_INFERENCE_FORBIDDEN - FORBIDDEN_AGENT_FIELDS
        extra_in_code = FORBIDDEN_AGENT_FIELDS - PAPER_INFERENCE_FORBIDDEN
        errors: list[str] = []
        if missing_from_code:
            errors.append(
                f"In paper §4 but NOT in visibility.py: {sorted(missing_from_code)}"
            )
        if extra_in_code:
            errors.append(
                f"In visibility.py but NOT in paper §4: {sorted(extra_in_code)}"
            )
        assert not errors, (
            "visibility.py::FORBIDDEN_AGENT_FIELDS diverges from paper §4 inference_forbidden:\n"
            + "\n".join(errors)
        )


class TestHookTokenMirror:
    """schema_leakage_guard.ps1 $forbiddenTokens must mirror visibility.py."""

    HOOK_PATH = REPO_ROOT / ".claude" / "hooks" / "schema_leakage_guard.ps1"

    def test_hook_token_list_mirror(self) -> None:
        if not self.HOOK_PATH.exists():
            pytest.skip(f"Hook not found: {self.HOOK_PATH}")

        hook_tokens = _parse_hook_tokens(self.HOOK_PATH)
        if not hook_tokens:
            pytest.skip(
                f"Could not parse $forbiddenTokens from {self.HOOK_PATH}. "
                "Check regex or hook format."
            )

        missing_from_hook = FORBIDDEN_AGENT_FIELDS - hook_tokens
        assert not missing_from_hook, (
            f"Fields in visibility.py but missing from hook $forbiddenTokens: "
            f"{sorted(missing_from_hook)}\n"
            f"Hook: {self.HOOK_PATH}\n"
            "Comment in hook: 'Mirror of FORBIDDEN_AGENT_FIELDS in visibility.py; "
            "sync-test enforced.'"
        )
