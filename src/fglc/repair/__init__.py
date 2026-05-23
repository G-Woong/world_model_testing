"""Repair harness taxonomy package.

Source: docs/EXPERIMENT_REPAIR_LOOP_PLAN.md Section F.2.
"""

from fglc.repair.taxonomy import (
    CAUSE_METADATA,
    DETECTION_THRESHOLDS,
    FailureCauseId,
    applicable_phases_for,
)

__all__ = [
    "CAUSE_METADATA",
    "DETECTION_THRESHOLDS",
    "FailureCauseId",
    "applicable_phases_for",
]
