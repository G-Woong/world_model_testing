"""Test: FORBIDDEN_AGENT_FIELDS in src/fglc/schemas/visibility.py is synchronized
with the CLAUDE.md canonical list and schema_leakage_guard.ps1 hook tokens.

Source: CLAUDE.md §양보할 수 없는 데이터 규칙
SSoT:   src/fglc/schemas/visibility.py::FORBIDDEN_AGENT_FIELDS
Mirror: .claude/hooks/schema_leakage_guard.ps1 $forbiddenTokens

Run:    pytest -q tests/test_fglc_forbidden_field_sync.py
Gate:   must stay GREEN — guards the forbidden field contract across all R-phases.
"""

from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Canonical field set — source of truth is CLAUDE.md §양보할 수 없는 데이터 규칙.
# If this list changes here, update CLAUDE.md + visibility.py + schema_leakage_guard.ps1.
# ---------------------------------------------------------------------------
CLAUDE_MD_REQUIRED_FIELDS: frozenset[str] = frozenset({
    "regime_id",
    "true_mass",
    "true_friction",
    "true_latency",
    "true_noise_sigma",
    "true_action_gain",
    "oracle_action",
    "counterfactual_reward",
    "split_id",
    "ood_type",
    "seed",
    "template_id",
})

REPO_ROOT = Path(__file__).parent.parent
HOOK_PATH = REPO_ROOT / ".claude" / "hooks" / "schema_leakage_guard.ps1"


# ---------------------------------------------------------------------------
# Group 1: visibility.py module well-formedness
# ---------------------------------------------------------------------------

class TestFglcVisibilityModule:

    def test_import_forbidden_agent_fields(self):
        from fglc.schemas.visibility import FORBIDDEN_AGENT_FIELDS  # noqa: F401

    def test_is_frozenset(self):
        from fglc.schemas.visibility import FORBIDDEN_AGENT_FIELDS
        assert isinstance(FORBIDDEN_AGENT_FIELDS, frozenset)

    def test_nonempty(self):
        from fglc.schemas.visibility import FORBIDDEN_AGENT_FIELDS
        assert len(FORBIDDEN_AGENT_FIELDS) >= len(CLAUDE_MD_REQUIRED_FIELDS)

    def test_no_empty_strings(self):
        from fglc.schemas.visibility import FORBIDDEN_AGENT_FIELDS
        assert "" not in FORBIDDEN_AGENT_FIELDS

    def test_assert_no_forbidden_fields_clean(self):
        from fglc.schemas.visibility import assert_no_forbidden_fields
        # safe dict — no forbidden fields
        assert_no_forbidden_fields({"obs": [1, 2, 3], "action": 0})

    def test_assert_no_forbidden_fields_raises(self):
        from fglc.schemas.visibility import assert_no_forbidden_fields
        with pytest.raises(ValueError, match="regime_id"):
            assert_no_forbidden_fields({"regime_id": 1, "obs": [1, 2, 3]})


# ---------------------------------------------------------------------------
# Group 2: CLAUDE.md canonical fields ⊆ FORBIDDEN_AGENT_FIELDS
# ---------------------------------------------------------------------------

class TestFglcClaudeMdSync:

    @pytest.mark.parametrize("field", sorted(CLAUDE_MD_REQUIRED_FIELDS))
    def test_required_field_present(self, field):
        from fglc.schemas.visibility import FORBIDDEN_AGENT_FIELDS
        assert field in FORBIDDEN_AGENT_FIELDS, (
            f"'{field}' is missing from FORBIDDEN_AGENT_FIELDS. "
            f"Required by CLAUDE.md §양보할 수 없는 데이터 규칙. "
            f"Add it to src/fglc/schemas/visibility.py."
        )


# ---------------------------------------------------------------------------
# Group 3: schema_leakage_guard.ps1 hook token mirror
# ---------------------------------------------------------------------------

class TestFglcHookMirror:
    """Verify the hook's $forbiddenTokens contains every required field."""

    @pytest.fixture(autouse=True)
    def skip_if_no_hook(self):
        if not HOOK_PATH.exists():
            pytest.skip("schema_leakage_guard.ps1 not found (only present in Claude worktree)")

    def test_hook_references_fglc_package(self):
        content = HOOK_PATH.read_text(encoding="utf-8")
        assert "src[/\\\\]fglc[/\\\\]" in content or "src/fglc/" in content, (
            "schema_leakage_guard.ps1 must watch src/fglc/ paths, not src/frcgw/."
        )

    def test_hook_does_not_reference_frcgw(self):
        content = HOOK_PATH.read_text(encoding="utf-8")
        assert "src/frcgw" not in content and "src[/\\\\]frcgw" not in content, (
            "schema_leakage_guard.ps1 still references src/frcgw/ — update to src/fglc/."
        )

    @pytest.mark.parametrize("field", sorted(CLAUDE_MD_REQUIRED_FIELDS))
    def test_hook_token_present(self, field):
        content = HOOK_PATH.read_text(encoding="utf-8")
        assert field in content, (
            f"'{field}' is missing from schema_leakage_guard.ps1 $forbiddenTokens. "
            f"Hook mirror must stay in sync with visibility.py::FORBIDDEN_AGENT_FIELDS."
        )
