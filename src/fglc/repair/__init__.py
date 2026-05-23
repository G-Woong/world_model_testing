"""Repair harness taxonomy package.

Source: docs/EXPERIMENT_REPAIR_LOOP_PLAN.md Section F.2.
"""

from fglc.repair.taxonomy import (
    CAUSE_METADATA,
    DETECTION_THRESHOLDS,
    FailureCauseId,
    applicable_phases_for,
)
from fglc.repair.orchestrator import (
    RepairIterationResult,
    RepairLoopConfig,
    RepairLoopState,
    run_repair_loop,
)

__all__ = [
    "CAUSE_METADATA",
    "DETECTION_THRESHOLDS",
    "FailureCauseId",
    "RepairIterationResult",
    "RepairLoopConfig",
    "RepairLoopState",
    "applicable_phases_for",
    "run_repair_loop",
]
