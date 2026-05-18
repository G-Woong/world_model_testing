# Safety Drift Sub-Audit — STEP 6 (Task 7-aux)

**Date**: 2026-05-18  
**Status**: PASS — test green, drift noted for STEP 7 correction

---

## Findings

### test_forbidden_field_mirror_sync.py

**Result**: GREEN (31 tests PASS)

The sync test verifies that `src/frcgw/schemas/visibility.py::FORBIDDEN_AGENT_FIELDS` is consistent
with the codebase contract. All 31 tests pass.

### Hook Drift Analysis

The `.claude/hooks/schema_leakage_guard.ps1` `$forbiddenTokens` array has partial drift from
`FORBIDDEN_AGENT_FIELDS`:

- **Extra in hook** (not in FORBIDDEN_AGENT_FIELDS): 4 counterfactual-related tokens
- **Missing from hook** (in FORBIDDEN_AGENT_FIELDS): `audit_metadata`

The sync test tests the CODE-LEVEL contract (`visibility.py` mirrors), not the hook behavior.
The hook is a defense-in-depth layer (additional shell-level check). The drift does NOT create
a leakage vulnerability in the inference path — `assert_agent_observation_safe()` and
`FORBIDDEN_AGENT_FIELDS` are the authoritative runtime enforcement.

### Decision

- **STEP 6**: No hook modification (R2 lock + fragile file policy)
- **STEP 7**: Review R2 lock policy; if approved, sync `$forbiddenTokens` with FORBIDDEN_AGENT_FIELDS

### STEP 6 Scope

Per plan §B7: "이번 STEP 6 commit에서 hook 수정은 하지 않음. drift 발견 시 STEP 7 task로 이관."

This decision is confirmed. No `.claude/hooks/schema_leakage_guard.ps1` modification in STEP 6.
