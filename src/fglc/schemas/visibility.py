"""
FGLC visibility contract — runtime forbidden field enforcement.

Source: docs/idea/18_DATA_BENCHMARKS.md §Data Rules
SSoT:   CLAUDE.md §양보할 수 없는 데이터 규칙

FORBIDDEN_AGENT_FIELDS must never appear in:
  - agent observation inputs
  - model forward() inputs
  - dataloader __getitem__ returns (inference path)
  - training loss computation inputs

Sync obligations:
  - .claude/hooks/schema_leakage_guard.ps1  $forbiddenTokens  (hook mirror)
  - tests/test_fglc_forbidden_field_sync.py                   (sync-test)
"""

FORBIDDEN_AGENT_FIELDS: frozenset[str] = frozenset({
    "regime_id",           # ground-truth physical regime label
    "true_mass",           # true object mass
    "true_friction",       # true friction coefficient
    "true_latency",        # true action delay
    "true_noise_sigma",    # true observation noise σ
    "true_action_gain",    # true action gain factor
    "oracle_action",       # oracle-optimal action (upper-bound baseline only)
    "counterfactual_reward",  # reward under counterfactual physical params
    "split_id",            # OOD split membership
    "ood_type",            # OOD axis identifier (mass / friction / latency / noise / gain)
    "seed",                # data generation seed
    "template_id",         # task template ID
})


def assert_no_forbidden_fields(d: dict, context: str = "") -> None:
    """Raise ValueError if any forbidden field appears in dict keys (shallow check).

    Args:
        d: dict to check (e.g. agent observation dict, batch dict)
        context: human-readable label for error messages

    Raises:
        ValueError: if any key in d is in FORBIDDEN_AGENT_FIELDS
    """
    violations = FORBIDDEN_AGENT_FIELDS & d.keys()
    if violations:
        prefix = f"[{context}] " if context else ""
        raise ValueError(
            f"{prefix}Forbidden fields detected in input: {sorted(violations)}. "
            f"These must not enter inference or training loss paths. "
            f"SSoT: src/fglc/schemas/visibility.py::FORBIDDEN_AGENT_FIELDS"
        )
