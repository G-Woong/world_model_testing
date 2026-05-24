"""Source: docs/EXPERIMENT_REPAIR_LOOP_PLAN.md D.2 + src/fglc/repair/taxonomy.py."""

from __future__ import annotations

from collections.abc import Mapping

from fglc.repair.taxonomy import FailureCauseId, applicable_phases_for


CANONICAL_METRIC_KEYS: frozenset[str] = frozenset(
    {
        "id_nll",
        "ood_auroc",
        "corrected_nll_gain",
        "attention_entropy",
        "correction_norm_mean",
        "planner_return_gain",
        "val_train_nll_gap",
        "ood_id_nll_diff",
        "beta_mean",
        "ece",
        "stagnant_epochs",
        "log_k",
        "kstep_nll_slope",
        "train_nll",
        # R3 smoke keys (added for Step 10D / CD-3 standardisation)
        "val_nll",
        "ood_mass_nll",
        "ood_friction_nll",
        "eval_ci95_over_effect_size",
        # R4 falsification gate keys (2026-05-24)
        "beta_t_auroc_friction",
        "beta_t_auroc_gain",
        "beta_t_fpr_id",
        "beta_t_tpr_friction",
        "beta_t_tpr_gain",
        "conformal_threshold",
        "residual_ece",
        "raw_nll_auroc_friction",
        "raw_nll_auroc_gain",
    }
)

# Operational artifact keys — allowed in metrics.json alongside CANONICAL_METRIC_KEYS
# but not used by diagnose/ranker logic.
ARTIFACT_KEYS: frozenset[str] = frozenset({"epoch", "wall_clock_minutes", "vram_peak_mib"})


def _fire_id_nll(metrics: Mapping[str, float]) -> list[FailureCauseId]:
    if metrics.get("id_nll") is None or metrics.get("stagnant_epochs") is None:
        return []
    if metrics["id_nll"] > 0.5 and metrics["stagnant_epochs"] >= 10:
        return [
            FailureCauseId.MODEL_UNDERCAPACITY,
            FailureCauseId.DATA_TOO_SMALL,
            FailureCauseId.HORIZON_TOO_SHORT,
            FailureCauseId.LOSS_IMBALANCE,
        ]
    return []


def _fire_ood_auroc(metrics: Mapping[str, float]) -> list[FailureCauseId]:
    if metrics.get("ood_auroc") is None:
        return []
    if metrics["ood_auroc"] < 0.7:
        return [
            FailureCauseId.SIGMA_CALIBRATION_FAILURE,
            FailureCauseId.BETA_GATE_COLLAPSE,
            FailureCauseId.OOD_TOO_EASY,
            FailureCauseId.DATA_BAD_SPLIT,
        ]
    return []


def _fire_corrected_gain(metrics: Mapping[str, float]) -> list[FailureCauseId]:
    if metrics.get("corrected_nll_gain") is None:
        return []
    if metrics["corrected_nll_gain"] > 0:
        return [
            FailureCauseId.CORRECTION_TOO_LARGE,
            FailureCauseId.ATTENTION_COLLAPSE,
            FailureCauseId.LOSS_IMBALANCE,
        ]
    return []


def _fire_attention(metrics: Mapping[str, float]) -> list[FailureCauseId]:
    entropy = metrics.get("attention_entropy")
    if entropy is None:
        return []
    if entropy < 0.1:
        return [FailureCauseId.ATTENTION_COLLAPSE]
    log_k = metrics.get("log_k")
    if log_k is not None and entropy > 0.95 * log_k:
        return [FailureCauseId.ATTENTION_COLLAPSE]
    return []


def _fire_correction_weak(metrics: Mapping[str, float]) -> list[FailureCauseId]:
    if metrics.get("correction_norm_mean") is None:
        return []
    if metrics["correction_norm_mean"] < 0.01:
        return [
            FailureCauseId.CORRECTION_TOO_WEAK,
            FailureCauseId.BETA_GATE_COLLAPSE,
        ]
    return []


def _fire_correction_large(metrics: Mapping[str, float]) -> list[FailureCauseId]:
    if metrics.get("correction_norm_mean") is None:
        return []
    if metrics["correction_norm_mean"] > 0.9:
        return [FailureCauseId.CORRECTION_TOO_LARGE]
    return []


def _fire_ood_too_hard(metrics: Mapping[str, float]) -> list[FailureCauseId]:
    diff = metrics.get("ood_id_nll_diff")
    if diff is None:
        return []
    # OOD_TOO_HARD: gap > 2.0 nat (taxonomy threshold)
    if diff > 2.0:
        return [FailureCauseId.OOD_TOO_HARD]
    return []


def _fire_eval_noise_high(metrics: Mapping[str, float]) -> list[FailureCauseId]:
    ci = metrics.get("eval_ci95_over_effect_size")
    if ci is None:
        return []
    if ci > 1.0:
        return [FailureCauseId.EVAL_NOISE_HIGH]
    return []


def _fire_planner(metrics: Mapping[str, float]) -> list[FailureCauseId]:
    if metrics.get("planner_return_gain") is None:
        return []
    if metrics["planner_return_gain"] <= 0:
        return [
            FailureCauseId.PLANNER_BUDGET_TOO_LOW,
            FailureCauseId.HORIZON_TOO_LONG,
            FailureCauseId.IMPLEMENTATION_BUG_SUSPECTED,
        ]
    return []


def diagnose(metrics: Mapping[str, float], phase: str) -> list[FailureCauseId]:
    applicable = applicable_phases_for(phase)
    if not applicable:
        raise ValueError(f"invalid phase: {phase!r}")

    causes: list[FailureCauseId] = []
    for fire_fn in [
        _fire_id_nll,
        _fire_ood_auroc,
        _fire_corrected_gain,
        _fire_attention,
        _fire_correction_weak,
        _fire_correction_large,
        _fire_ood_too_hard,
        _fire_eval_noise_high,
        _fire_planner,
    ]:
        for cause_id in fire_fn(metrics):
            if cause_id in applicable and cause_id not in causes:
                causes.append(cause_id)

    if not causes and FailureCauseId.IMPLEMENTATION_BUG_SUSPECTED in applicable:
        return [FailureCauseId.IMPLEMENTATION_BUG_SUSPECTED]
    return causes
