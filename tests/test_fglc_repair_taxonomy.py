from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from fglc.repair import (
    CAUSE_METADATA,
    DETECTION_THRESHOLDS,
    FailureCauseId,
    applicable_phases_for,
)
from fglc.repair.taxonomy import FailureCauseMeta


CANONICAL_PHASES = {"R2", "R3", "R4", "R5", "R6", "R7", "R9", "R10"}


def test_enum_well_formedness() -> None:
    assert len(FailureCauseId) == 20
    assert all(isinstance(cause.value, str) for cause in FailureCauseId)
    assert all(cause.name == cause.value for cause in FailureCauseId)
    assert all(re.fullmatch(r"[A-Z][A-Z0-9_]*", cause.name) for cause in FailureCauseId)


def test_cause_metadata_complete_for_every_enum_member() -> None:
    assert set(CAUSE_METADATA) == set(FailureCauseId)
    assert all(isinstance(meta, FailureCauseMeta) for meta in CAUSE_METADATA.values())
    assert all(cause is meta.cause_id for cause, meta in CAUSE_METADATA.items())


def test_source_md_refs_exist_except_implementation_bug_suspected() -> None:
    for cause, meta in CAUSE_METADATA.items():
        if cause is FailureCauseId.IMPLEMENTATION_BUG_SUSPECTED:
            assert meta.source_md_refs == ()
            continue

        assert meta.source_md_refs
        for ref in meta.source_md_refs:
            path = REPO_ROOT / ref
            assert ref.startswith("docs/")
            assert path.exists(), ref


def test_applicable_phases_are_canonical_subset() -> None:
    for meta in CAUSE_METADATA.values():
        assert meta.applicable_phases
        assert set(meta.applicable_phases) <= CANONICAL_PHASES


def test_detection_threshold_values_are_numeric_or_none() -> None:
    assert set(DETECTION_THRESHOLDS) == set(FailureCauseId)
    for thresholds in DETECTION_THRESHOLDS.values():
        assert isinstance(thresholds, dict)
        for value in thresholds.values():
            assert value is None or isinstance(value, (int, float))
            assert not callable(value)
            assert not isinstance(value, str)


def test_applicable_phases_for_r3_sanity() -> None:
    assert applicable_phases_for("R3") == frozenset(
        {
            FailureCauseId.MODEL_UNDERCAPACITY,
            FailureCauseId.MODEL_OVERCAPACITY,
            FailureCauseId.LATENT_GROUP_TOO_SMALL,
            FailureCauseId.LATENT_DIM_TOO_SMALL,
            FailureCauseId.HORIZON_TOO_SHORT,
            FailureCauseId.HORIZON_TOO_LONG,
            FailureCauseId.LOSS_IMBALANCE,
            FailureCauseId.EVAL_NOISE_HIGH,
            FailureCauseId.IMPLEMENTATION_BUG_SUSPECTED,
        }
    )


def test_applicable_phases_for_r4_sanity() -> None:
    assert applicable_phases_for("R4") == frozenset(
        {
            FailureCauseId.SIGMA_CALIBRATION_FAILURE,
            FailureCauseId.BETA_GATE_COLLAPSE,
            FailureCauseId.EVAL_NOISE_HIGH,
            FailureCauseId.IMPLEMENTATION_BUG_SUSPECTED,
        }
    )


def test_applicable_phases_for_r6_sanity() -> None:
    assert applicable_phases_for("R6") == frozenset(
        {
            FailureCauseId.CORRECTION_TOO_WEAK,
            FailureCauseId.CORRECTION_TOO_LARGE,
            FailureCauseId.IMPLEMENTATION_BUG_SUSPECTED,
        }
    )
