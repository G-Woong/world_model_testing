"""Source: docs/EXPERIMENT_REPAIR_LOOP_PLAN.md D.3."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from fglc.repair.taxonomy import FailureCauseId


@dataclass(frozen=True)
class RepairCandidate:
    id: str
    cause_id: FailureCauseId
    patch: Mapping[str, Any]
    cost_minutes: int
    risk: float
    expected_signal: float
    description: str
    applicable_phases: tuple[str, ...]


CANDIDATE_TABLE: dict[FailureCauseId, tuple[RepairCandidate, ...]] = {
    FailureCauseId.MODEL_UNDERCAPACITY: (
        RepairCandidate(
            id="MODEL_UNDERCAPACITY_h_dim_256",
            cause_id=FailureCauseId.MODEL_UNDERCAPACITY,
            patch={"hidden_dim": 256},
            cost_minutes=15,
            risk=0.1,
            expected_signal=0.6,
            description="Increase hidden_dim 128 to 256.",
            applicable_phases=("R3",),
        ),
    ),
    FailureCauseId.DATA_TOO_SMALL: (
        RepairCandidate(
            id="DATA_TOO_SMALL_episode_x2",
            cause_id=FailureCauseId.DATA_TOO_SMALL,
            patch={"num_episodes": 200},
            cost_minutes=30,
            risk=0.1,
            expected_signal=0.5,
            description="Double episode count.",
            applicable_phases=("R2", "R3"),
        ),
    ),
    FailureCauseId.HORIZON_TOO_SHORT: (
        RepairCandidate(
            id="HORIZON_TOO_SHORT_horizon_16",
            cause_id=FailureCauseId.HORIZON_TOO_SHORT,
            patch={"horizon": 16},
            cost_minutes=20,
            risk=0.2,
            expected_signal=0.4,
            description="Extend training horizon 8 to 16.",
            applicable_phases=("R3",),
        ),
    ),
    FailureCauseId.LOSS_IMBALANCE: (
        RepairCandidate(
            id="LOSS_IMBALANCE_weights_rebalance",
            cause_id=FailureCauseId.LOSS_IMBALANCE,
            patch={"loss_weights": {"nll": 1.0, "kl": 0.1}},
            cost_minutes=10,
            risk=0.2,
            expected_signal=0.4,
            description="Rebalance loss component weights.",
            applicable_phases=("R3",),
        ),
        RepairCandidate(
            id="LOSS_IMBALANCE_corrected_loss_weight_down",
            cause_id=FailureCauseId.LOSS_IMBALANCE,
            patch={"corrected_loss_weight": 0.5},
            cost_minutes=5,
            risk=0.1,
            expected_signal=0.5,
            description="Reduce corrected_loss_weight.",
            applicable_phases=("R3",),
        ),
    ),
    FailureCauseId.SIGMA_CALIBRATION_FAILURE: (
        RepairCandidate(
            id="SIGMA_CALIBRATION_FAILURE_add_l_cal",
            cause_id=FailureCauseId.SIGMA_CALIBRATION_FAILURE,
            patch={"calibration_loss_weight": 0.1},
            cost_minutes=10,
            risk=0.1,
            expected_signal=0.7,
            description="Add L_cal calibration penalty.",
            applicable_phases=("R4",),
        ),
    ),
    FailureCauseId.BETA_GATE_COLLAPSE: (
        RepairCandidate(
            id="BETA_GATE_COLLAPSE_reparam",
            cause_id=FailureCauseId.BETA_GATE_COLLAPSE,
            patch={"beta_reparameterize": True},
            cost_minutes=15,
            risk=0.2,
            expected_signal=0.5,
            description="Reparameterize beta gate to avoid collapse.",
            applicable_phases=("R4",),
        ),
        RepairCandidate(
            id="BETA_GATE_COLLAPSE_prior_scale_reset",
            cause_id=FailureCauseId.BETA_GATE_COLLAPSE,
            patch={"beta_prior_scale": 1.0},
            cost_minutes=10,
            risk=0.2,
            expected_signal=0.4,
            description="Reset beta prior scale.",
            applicable_phases=("R4",),
        ),
    ),
    FailureCauseId.OOD_TOO_EASY: (
        RepairCandidate(
            id="OOD_TOO_EASY_shift_strength_2x",
            cause_id=FailureCauseId.OOD_TOO_EASY,
            patch={"ood_shift_scale": 2.0},
            cost_minutes=20,
            risk=0.2,
            expected_signal=0.5,
            description="Double OOD shift magnitude.",
            applicable_phases=("R2",),
        ),
    ),
    FailureCauseId.DATA_BAD_SPLIT: (
        RepairCandidate(
            id="DATA_BAD_SPLIT_regenerate",
            cause_id=FailureCauseId.DATA_BAD_SPLIT,
            patch={"regenerate_split": True},
            cost_minutes=30,
            risk=0.3,
            expected_signal=0.6,
            description="Regenerate ID/OOD split.",
            applicable_phases=("R2",),
        ),
    ),
    FailureCauseId.CORRECTION_TOO_LARGE: (
        RepairCandidate(
            id="CORRECTION_TOO_LARGE_delta_max_01",
            cause_id=FailureCauseId.CORRECTION_TOO_LARGE,
            patch={"delta_max": 0.1},
            cost_minutes=5,
            risk=0.1,
            expected_signal=0.7,
            description="Reduce delta_max 0.25 to 0.1.",
            applicable_phases=("R6",),
        ),
        RepairCandidate(
            id="CORRECTION_TOO_LARGE_base_wm_freeze",
            cause_id=FailureCauseId.CORRECTION_TOO_LARGE,
            patch={"freeze_base_wm": True},
            cost_minutes=15,
            risk=0.3,
            expected_signal=0.5,
            description="Freeze base WM during correction training.",
            applicable_phases=("R6",),
        ),
        RepairCandidate(
            id="CORRECTION_TOO_LARGE_delta_max_reduce",
            cause_id=FailureCauseId.CORRECTION_TOO_LARGE,
            patch={"delta_max": 0.05},
            cost_minutes=5,
            risk=0.1,
            expected_signal=0.7,
            description="Reduce delta_max to 0.05.",
            applicable_phases=("R6",),
        ),
        RepairCandidate(
            id="CORRECTION_TOO_LARGE_l_corr_size_up",
            cause_id=FailureCauseId.CORRECTION_TOO_LARGE,
            patch={"l_corr_size_weight": 0.1},
            cost_minutes=5,
            risk=0.1,
            expected_signal=0.5,
            description="Increase L_corr_size penalty weight.",
            applicable_phases=("R6",),
        ),
    ),
    FailureCauseId.ATTENTION_COLLAPSE: (
        RepairCandidate(
            id="ATTENTION_COLLAPSE_entmax",
            cause_id=FailureCauseId.ATTENTION_COLLAPSE,
            patch={"attention_type": "entmax"},
            cost_minutes=10,
            risk=0.2,
            expected_signal=0.6,
            description="Switch to entmax/sparsemax attention.",
            applicable_phases=("R5", "R6"),
        ),
        RepairCandidate(
            id="ATTENTION_COLLAPSE_entmax_alpha_15",
            cause_id=FailureCauseId.ATTENTION_COLLAPSE,
            patch={"entmax_alpha": 1.5},
            cost_minutes=5,
            risk=0.1,
            expected_signal=0.6,
            description="Set entmax alpha=1.5 for sparse attention.",
            applicable_phases=("R5",),
        ),
        RepairCandidate(
            id="ATTENTION_COLLAPSE_topk_mask_k2",
            cause_id=FailureCauseId.ATTENTION_COLLAPSE,
            patch={"topk_mask_k": 2},
            cost_minutes=5,
            risk=0.1,
            expected_signal=0.5,
            description="Apply top-k mask with k=2.",
            applicable_phases=("R5",),
        ),
        RepairCandidate(
            id="ATTENTION_COLLAPSE_sparsity_penalty",
            cause_id=FailureCauseId.ATTENTION_COLLAPSE,
            patch={"attention_sparsity_penalty": 0.01},
            cost_minutes=5,
            risk=0.1,
            expected_signal=0.4,
            description="Add sparsity penalty to attention.",
            applicable_phases=("R5",),
        ),
    ),
    FailureCauseId.CORRECTION_TOO_WEAK: (
        RepairCandidate(
            id="CORRECTION_TOO_WEAK_delta_head_init_scale",
            cause_id=FailureCauseId.CORRECTION_TOO_WEAK,
            patch={"delta_head_init_scale": 0.1},
            cost_minutes=5,
            risk=0.1,
            expected_signal=0.6,
            description="Increase delta head init scale.",
            applicable_phases=("R6",),
        ),
        RepairCandidate(
            id="CORRECTION_TOO_WEAK_corrected_loss_weight_up",
            cause_id=FailureCauseId.CORRECTION_TOO_WEAK,
            patch={"corrected_loss_weight": 2.0},
            cost_minutes=5,
            risk=0.1,
            expected_signal=0.5,
            description="Increase corrected loss weight.",
            applicable_phases=("R6",),
        ),
    ),
    FailureCauseId.PLANNER_BUDGET_TOO_LOW: (
        RepairCandidate(
            id="PLANNER_BUDGET_TOO_LOW_n_candidate_up",
            cause_id=FailureCauseId.PLANNER_BUDGET_TOO_LOW,
            patch={"n_candidates": 512},
            cost_minutes=10,
            risk=0.1,
            expected_signal=0.6,
            description="Increase planner rollout count.",
            applicable_phases=("R7",),
        ),
        RepairCandidate(
            id="PLANNER_BUDGET_TOO_LOW_value_head_retrain",
            cause_id=FailureCauseId.PLANNER_BUDGET_TOO_LOW,
            patch={"retrain_value_head": True},
            cost_minutes=20,
            risk=0.3,
            expected_signal=0.5,
            description="Retrain reward/value head.",
            applicable_phases=("R7",),
        ),
    ),
    FailureCauseId.HORIZON_TOO_LONG: (
        RepairCandidate(
            id="HORIZON_TOO_LONG_horizon_3",
            cause_id=FailureCauseId.HORIZON_TOO_LONG,
            patch={"planning_horizon": 3},
            cost_minutes=5,
            risk=0.1,
            expected_signal=0.5,
            description="Reduce planning horizon 5 to 3.",
            applicable_phases=("R7",),
        ),
    ),
    FailureCauseId.IMPLEMENTATION_BUG_SUSPECTED: (
        RepairCandidate(
            id="IMPLEMENTATION_BUG_SUSPECTED_manual_blocker",
            cause_id=FailureCauseId.IMPLEMENTATION_BUG_SUSPECTED,
            patch={"action": "manual_blocker_report"},
            cost_minutes=1,
            risk=0.0,
            expected_signal=0.0,
            description="Escalate to user; no automated patch.",
            applicable_phases=("R3", "R4", "R5", "R6", "R7"),
        ),
    ),
}


def candidates_for(causes: Sequence[FailureCauseId], phase: str) -> list[RepairCandidate]:
    result: list[RepairCandidate] = []
    seen: set[FailureCauseId] = set()
    for cause_id in causes:
        if cause_id in seen:
            continue
        seen.add(cause_id)
        for candidate in CANDIDATE_TABLE.get(cause_id, ()):
            if phase in candidate.applicable_phases:
                result.append(candidate)
    return result
