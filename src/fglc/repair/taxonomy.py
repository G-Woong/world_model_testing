"""Failure cause taxonomy for the closed-loop repair harness.

Source: docs/idea/FGLC_FAILURE_TAXONOMY.md (single source of truth).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class FailureCauseId(str, Enum):
    """Canonical failure cause ids used by repair diagnostics."""

    DATA_TOO_SMALL = "DATA_TOO_SMALL"
    DATA_BAD_SPLIT = "DATA_BAD_SPLIT"
    OOD_TOO_HARD = "OOD_TOO_HARD"
    OOD_TOO_EASY = "OOD_TOO_EASY"
    MODEL_UNDERCAPACITY = "MODEL_UNDERCAPACITY"
    MODEL_OVERCAPACITY = "MODEL_OVERCAPACITY"
    LATENT_GROUP_TOO_SMALL = "LATENT_GROUP_TOO_SMALL"
    LATENT_DIM_TOO_SMALL = "LATENT_DIM_TOO_SMALL"
    HORIZON_TOO_SHORT = "HORIZON_TOO_SHORT"
    HORIZON_TOO_LONG = "HORIZON_TOO_LONG"
    LOSS_IMBALANCE = "LOSS_IMBALANCE"
    SIGMA_CALIBRATION_FAILURE = "SIGMA_CALIBRATION_FAILURE"
    BETA_GATE_COLLAPSE = "BETA_GATE_COLLAPSE"
    ATTENTION_COLLAPSE = "ATTENTION_COLLAPSE"
    CORRECTION_TOO_WEAK = "CORRECTION_TOO_WEAK"
    CORRECTION_TOO_LARGE = "CORRECTION_TOO_LARGE"
    PLANNER_BUDGET_TOO_LOW = "PLANNER_BUDGET_TOO_LOW"
    EVAL_NOISE_HIGH = "EVAL_NOISE_HIGH"
    BASELINE_MISMATCH = "BASELINE_MISMATCH"
    IMPLEMENTATION_BUG_SUSPECTED = "IMPLEMENTATION_BUG_SUSPECTED"
    # R4 new causes (2026-05-24)
    CONFORMAL_QUANTILE_MISMATCH = "CONFORMAL_QUANTILE_MISMATCH"
    BETA_GATE_DIRECTION_BLIND = "BETA_GATE_DIRECTION_BLIND"
    EASY_LOOKING_OOD_MISSED = "EASY_LOOKING_OOD_MISSED"


@dataclass(frozen=True)
class FailureCauseMeta:
    cause_id: FailureCauseId
    meaning: str
    source_md_refs: tuple[str, ...]
    applicable_phases: tuple[str, ...]
    detection_summary: str


CAUSE_METADATA: dict[FailureCauseId, FailureCauseMeta] = {
    FailureCauseId.DATA_TOO_SMALL: FailureCauseMeta(
        cause_id=FailureCauseId.DATA_TOO_SMALL,
        meaning="episode count is too small, causing high NLL variance.",
        source_md_refs=("docs/idea/18_DATA_BENCHMARKS.md",),
        applicable_phases=("R2",),
        detection_summary="NLL_std / NLL_mean > 0.3 at epoch-end eval.",
    ),
    FailureCauseId.DATA_BAD_SPLIT: FailureCauseMeta(
        cause_id=FailureCauseId.DATA_BAD_SPLIT,
        meaning="ID/OOD overlap or OOD distribution is effectively identical to ID.",
        source_md_refs=("docs/ROADMAP/03_PHASE_R2_DATA_PIPELINE.md",),
        applicable_phases=("R2",),
        detection_summary="abs(OOD_NLL - ID_NLL) < 0.05 nat on 1-step same-task eval.",
    ),
    FailureCauseId.OOD_TOO_HARD: FailureCauseMeta(
        cause_id=FailureCauseId.OOD_TOO_HARD,
        meaning="OOD shift is too extreme for model interpretation.",
        source_md_refs=("docs/idea/18_DATA_BENCHMARKS.md",),
        applicable_phases=("R2",),
        detection_summary="OOD_NLL - ID_NLL > 2.0 nat.",
    ),
    FailureCauseId.OOD_TOO_EASY: FailureCauseMeta(
        cause_id=FailureCauseId.OOD_TOO_EASY,
        meaning="OOD shift is nearly identical to ID and lacks meaningful shift.",
        source_md_refs=("docs/idea/12_TRAINING_STAGES.md",),
        applicable_phases=("R2",),
        detection_summary="OOD_NLL - ID_NLL < 0.05 nat.",
    ),
    FailureCauseId.MODEL_UNDERCAPACITY: FailureCauseMeta(
        cause_id=FailureCauseId.MODEL_UNDERCAPACITY,
        meaning="model capacity is insufficient and train loss is stagnant.",
        source_md_refs=("docs/idea/23_FAILURE_MODES.md",),
        applicable_phases=("R3",),
        detection_summary="train_NLL is approximately val_NLL, or train_NLL > 0.5 nat for at least 10 epochs.",
    ),
    FailureCauseId.MODEL_OVERCAPACITY: FailureCauseMeta(
        cause_id=FailureCauseId.MODEL_OVERCAPACITY,
        meaning="model is overfitting, with train and validation performance diverging.",
        source_md_refs=("docs/idea/23_FAILURE_MODES.md",),
        applicable_phases=("R3",),
        detection_summary="val_NLL - train_NLL > 0.3 nat.",
    ),
    FailureCauseId.LATENT_GROUP_TOO_SMALL: FailureCauseMeta(
        cause_id=FailureCauseId.LATENT_GROUP_TOO_SMALL,
        meaning="K is too small to represent diverse motion types.",
        source_md_refs=("docs/idea/03_LATENT_DECOMPOSITION.md",),
        applicable_phases=("R3",),
        detection_summary="median inter-group cosine similarity > 0.85.",
    ),
    FailureCauseId.LATENT_DIM_TOO_SMALL: FailureCauseMeta(
        cause_id=FailureCauseId.LATENT_DIM_TOO_SMALL,
        meaning="per-group latent dimension is too small and reconstruction error exceeds the upper bound.",
        source_md_refs=("docs/idea/03_LATENT_DECOMPOSITION.md",),
        applicable_phases=("R3",),
        detection_summary="reconstruction_mse > baseline_reconstruction_mse * 1.5.",
    ),
    FailureCauseId.HORIZON_TOO_SHORT: FailureCauseMeta(
        cause_id=FailureCauseId.HORIZON_TOO_SHORT,
        meaning="training horizon is too short to capture cumulative OOD error signal.",
        source_md_refs=("docs/idea/04_BASE_WORLD_MODEL.md",),
        applicable_phases=("R3",),
        detection_summary="k-step NLL is flat over k=1..T, with slope < 0.01 nat/step.",
    ),
    FailureCauseId.HORIZON_TOO_LONG: FailureCauseMeta(
        cause_id=FailureCauseId.HORIZON_TOO_LONG,
        meaning="training horizon is too long and cumulative error explodes.",
        source_md_refs=("docs/idea/04_BASE_WORLD_MODEL.md",),
        applicable_phases=("R3",),
        detection_summary="k-step NLL increases exponentially, doubling at some k.",
    ),
    FailureCauseId.LOSS_IMBALANCE: FailureCauseMeta(
        cause_id=FailureCauseId.LOSS_IMBALANCE,
        meaning="objective weights are biased so one objective suppresses the others.",
        source_md_refs=("docs/idea/10_LOSS_DESIGN.md",),
        applicable_phases=("R3",),
        detection_summary="one loss component is > 80% of total loss, or logs diverge.",
    ),
    FailureCauseId.SIGMA_CALIBRATION_FAILURE: FailureCauseMeta(
        cause_id=FailureCauseId.SIGMA_CALIBRATION_FAILURE,
        meaning="predicted uncertainty is over- or under-estimated by at least a factor of two relative to experience.",
        source_md_refs=(
            "docs/idea/23_FAILURE_MODES.md",
            "docs/ROADMAP/05_PHASE_R4_FALSIFICATION_GATE.md",
        ),
        applicable_phases=("R4",),
        detection_summary="ECE > 0.2 using 10-bin calibration error.",
    ),
    FailureCauseId.BETA_GATE_COLLAPSE: FailureCauseMeta(
        cause_id=FailureCauseId.BETA_GATE_COLLAPSE,
        meaning="falsification gate beta_t is almost always 0 or almost always 1.",
        source_md_refs=("docs/idea/23_FAILURE_MODES.md",),
        applicable_phases=("R4",),
        detection_summary="mean(beta_t) < 0.05 or mean(beta_t) > 0.95.",
    ),
    FailureCauseId.ATTENTION_COLLAPSE: FailureCauseMeta(
        cause_id=FailureCauseId.ATTENTION_COLLAPSE,
        meaning="causal attention concentrates on one group or becomes uniform, weakening sparse correction.",
        source_md_refs=(
            "docs/idea/23_FAILURE_MODES.md",
            "docs/idea/06_CAUSAL_ATTENTION.md",
        ),
        applicable_phases=("R5",),
        detection_summary="entropy(alpha_t) < 0.1 or entropy(alpha_t) > 0.95 * log(K).",
    ),
    FailureCauseId.CORRECTION_TOO_WEAK: FailureCauseMeta(
        cause_id=FailureCauseId.CORRECTION_TOO_WEAK,
        meaning="correction magnitude is near zero and has no effect on dynamics.",
        source_md_refs=(
            "docs/idea/23_FAILURE_MODES.md",
            "docs/idea/07_CORRECTION_MECHANISM.md",
        ),
        applicable_phases=("R6",),
        detection_summary="mean(||delta||) < 0.01.",
    ),
    FailureCauseId.CORRECTION_TOO_LARGE: FailureCauseMeta(
        cause_id=FailureCauseId.CORRECTION_TOO_LARGE,
        meaning="correction often hits delta_max bounds, making correction excessive.",
        source_md_refs=(
            "docs/idea/23_FAILURE_MODES.md",
            "docs/idea/07_CORRECTION_MECHANISM.md",
        ),
        applicable_phases=("R6",),
        detection_summary="fraction of steps with ||delta|| >= 0.9 * delta_max is > 30%.",
    ),
    FailureCauseId.PLANNER_BUDGET_TOO_LOW: FailureCauseMeta(
        cause_id=FailureCauseId.PLANNER_BUDGET_TOO_LOW,
        meaning="rollout count is too low and return estimates have high variance.",
        source_md_refs=("docs/idea/11_PLANNING_THEORY.md",),
        applicable_phases=("R7",),
        detection_summary="return_std > return_mean * 0.5 over 3 seeds.",
    ),
    FailureCauseId.EVAL_NOISE_HIGH: FailureCauseMeta(
        cause_id=FailureCauseId.EVAL_NOISE_HIGH,
        meaning="seed variance is too high to compare meaningfully against the effect size.",
        source_md_refs=("docs/idea/21_METRICS.md",),
        applicable_phases=("R3", "R4", "R5", "R7", "R9", "R10"),
        detection_summary="95% CI is greater than the effect size for each metric delta.",
    ),
    FailureCauseId.BASELINE_MISMATCH: FailureCauseMeta(
        cause_id=FailureCauseId.BASELINE_MISMATCH,
        meaning="baseline code does not match the baseline specification.",
        source_md_refs=("docs/idea/19_BASELINES.md",),
        applicable_phases=("R9", "R10"),
        detection_summary="baseline NLL is abnormally low or high on ID, with deviation > 2 sigma from expected.",
    ),
    FailureCauseId.IMPLEMENTATION_BUG_SUSPECTED: FailureCauseMeta(
        cause_id=FailureCauseId.IMPLEMENTATION_BUG_SUSPECTED,
        meaning="anomalous behavior does not match any of the other 19 causes.",
        source_md_refs=(),
        applicable_phases=("R3", "R4", "R5", "R6", "R7"),
        detection_summary="catch-all state requiring blocker report and manual evaluation.",
    ),
}


DETECTION_THRESHOLDS: dict[FailureCauseId, dict[str, float | None]] = {
    FailureCauseId.DATA_TOO_SMALL: {"nll_std_over_mean_max": 0.3},
    FailureCauseId.DATA_BAD_SPLIT: {"ood_id_nll_abs_diff_min": 0.05},
    FailureCauseId.OOD_TOO_HARD: {"ood_id_nll_diff_max": 2.0},
    FailureCauseId.OOD_TOO_EASY: {"ood_id_nll_diff_min": 0.05},
    FailureCauseId.MODEL_UNDERCAPACITY: {
        "train_nll_stagnant_min": 0.5,
        "stagnant_epochs_min": 10.0,
    },
    FailureCauseId.MODEL_OVERCAPACITY: {"val_train_nll_gap_max": 0.3},
    FailureCauseId.LATENT_GROUP_TOO_SMALL: {"inter_group_cosine_median_max": 0.85},
    FailureCauseId.LATENT_DIM_TOO_SMALL: {"reconstruction_mse_over_baseline_max": 1.5},
    FailureCauseId.HORIZON_TOO_SHORT: {"kstep_nll_slope_min": 0.01},
    FailureCauseId.HORIZON_TOO_LONG: {"kstep_nll_doubling_factor": 2.0},
    FailureCauseId.LOSS_IMBALANCE: {"loss_component_fraction_max": 0.8},
    FailureCauseId.SIGMA_CALIBRATION_FAILURE: {"ece_max": 0.2, "n_bins": 10.0},
    FailureCauseId.BETA_GATE_COLLAPSE: {
        "beta_mean_min": 0.05,
        "beta_mean_max": 0.95,
    },
    FailureCauseId.ATTENTION_COLLAPSE: {
        "attention_entropy_min": 0.1,
        "attention_entropy_log_k_fraction_max": 0.95,
    },
    FailureCauseId.CORRECTION_TOO_WEAK: {"correction_norm_mean_min": 0.01},
    FailureCauseId.CORRECTION_TOO_LARGE: {
        "correction_norm_over_max_threshold": 0.9,
        "correction_bound_hit_fraction_max": 0.3,
    },
    FailureCauseId.PLANNER_BUDGET_TOO_LOW: {"return_std_over_mean_max": 0.5},
    FailureCauseId.EVAL_NOISE_HIGH: {"ci95_over_effect_size_max": 1.0},
    FailureCauseId.BASELINE_MISMATCH: {"baseline_nll_expected_sigma_max": 2.0},
    FailureCauseId.IMPLEMENTATION_BUG_SUSPECTED: {},
}


CAUSE_METADATA.update(
    {
        FailureCauseId.CONFORMAL_QUANTILE_MISMATCH: FailureCauseMeta(
            cause_id=FailureCauseId.CONFORMAL_QUANTILE_MISMATCH,
            meaning="empirical FPR on ID calibration deviates significantly from α.",
            source_md_refs=("docs/idea/02_FALSIFICATION_THEORY.md",),
            applicable_phases=("R4",),
            detection_summary="beta_t_fpr_id not in [alpha/2, 2*alpha].",
        ),
        FailureCauseId.BETA_GATE_DIRECTION_BLIND: FailureCauseMeta(
            cause_id=FailureCauseId.BETA_GATE_DIRECTION_BLIND,
            meaning="β_t AUROC is below raw NLL AUROC, indicating gate is worse than baseline.",
            source_md_refs=("docs/idea/02_FALSIFICATION_THEORY.md",),
            applicable_phases=("R4",),
            detection_summary="beta_t_auroc_* < raw_nll_auroc_* by > 0.05.",
        ),
        FailureCauseId.EASY_LOOKING_OOD_MISSED: FailureCauseMeta(
            cause_id=FailureCauseId.EASY_LOOKING_OOD_MISSED,
            meaning="magnitude-reducing OOD (gain=0.7, friction=5.0) yields lower F_total than ID.",
            source_md_refs=(
                "reports/R3_SMOKE_CLOSURE_REPORT.md",
                "docs/FUTURE_OOD_DATA_EXPANSION_INSIGHTS.md",
            ),
            applicable_phases=("R4",),
            detection_summary="mean(F_total_ood) < mean(F_total_id) for friction or gain axis.",
        ),
    }
)

DETECTION_THRESHOLDS.update(
    {
        FailureCauseId.CONFORMAL_QUANTILE_MISMATCH: {
            "fpr_id_lo": None,  # dynamic: alpha/2
            "fpr_id_hi": None,  # dynamic: 2*alpha
        },
        FailureCauseId.BETA_GATE_DIRECTION_BLIND: {
            "beta_auroc_below_nll_auroc_margin": 0.05,
        },
        FailureCauseId.EASY_LOOKING_OOD_MISSED: {
            "ood_f_mean_below_id_f_mean": 0.0,
        },
    }
)


def applicable_phases_for(phase: str) -> frozenset[FailureCauseId]:
    """Return set of cause-ids that are diagnostically active in the given phase."""

    return frozenset(
        cause_id
        for cause_id, metadata in CAUSE_METADATA.items()
        if phase in metadata.applicable_phases
    )
