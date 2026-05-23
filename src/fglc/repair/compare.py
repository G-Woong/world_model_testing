"""Metric comparison rules for closed-loop repair decisions.

Source: docs/EXPERIMENT_LEDGER_SCHEMA.md section decision rules +
docs/EXPERIMENT_REPAIR_LOOP_PLAN.md section D.4
"""

from enum import Enum
from typing import Any


class MetricDirection(str, Enum):
    LOWER_BETTER = "lower_better"
    HIGHER_BETTER = "higher_better"


def _coerce_direction(direction: str | MetricDirection) -> MetricDirection:
    try:
        return MetricDirection(direction)
    except ValueError as exc:
        raise ValueError(f"invalid metric direction: {direction!r}") from exc


def _improvement(delta: float, direction: MetricDirection) -> float:
    if direction is MetricDirection.LOWER_BETTER:
        return -delta
    return delta


def compare_metrics(
    metrics_before: dict[str, float | None],
    metrics_after: dict[str, float | None],
    failed_metric: str,
    metric_directions: dict[str, str | MetricDirection],
    *,
    epsilon_accept: float = 0.05,
    epsilon_reject: float = 0.0,
    epsilon_secondary: float = 0.10,
) -> dict[str, Any]:
    if failed_metric not in metrics_before or failed_metric not in metrics_after:
        raise ValueError("failed_metric must be present in metrics_before and metrics_after")
    if failed_metric not in metric_directions:
        raise ValueError("metric_directions must include failed_metric")

    before_primary = metrics_before[failed_metric]
    after_primary = metrics_after[failed_metric]
    if before_primary is None or after_primary is None:
        raise ValueError("primary metric must be measured")

    failed_direction = _coerce_direction(metric_directions[failed_metric])

    deltas: dict[str, float | None] = {}
    secondary_improvements: dict[str, float] = {}
    for metric, after_value in metrics_after.items():
        before_value = metrics_before.get(metric)
        if before_value is None or after_value is None:
            deltas[metric] = None
            continue

        delta = after_value - before_value
        deltas[metric] = delta
        if metric != failed_metric:
            if metric not in metric_directions:
                raise ValueError(f"metric_directions missing measured secondary metric: {metric}")
            direction = _coerce_direction(metric_directions[metric])
            secondary_improvements[metric] = _improvement(delta, direction)

    primary_delta = deltas[failed_metric]
    assert primary_delta is not None
    primary_improvement = _improvement(primary_delta, failed_direction)
    worst_secondary = min(secondary_improvements.values(), default=None)

    if (
        primary_improvement >= epsilon_accept
        and all(value > -epsilon_secondary for value in secondary_improvements.values())
    ):
        result = "accept"
        result_reason = (
            f"Primary {failed_metric} improvement {primary_improvement:.6g} "
            f"met epsilon_accept {epsilon_accept:.6g} with no secondary regression."
        )
    elif primary_improvement <= epsilon_reject:
        result = "reject"
        result_reason = (
            f"Primary {failed_metric} improvement {primary_improvement:.6g} "
            f"was at or below epsilon_reject {epsilon_reject:.6g}."
        )
    elif worst_secondary is not None and worst_secondary <= -epsilon_secondary:
        result = "reject"
        result_reason = (
            f"A secondary metric regressed by {-worst_secondary:.6g}, "
            f"meeting epsilon_secondary {epsilon_secondary:.6g}."
        )
    else:
        result = "inconclusive"
        result_reason = (
            f"Primary {failed_metric} improvement {primary_improvement:.6g} "
            f"did not meet accept or reject thresholds."
        )

    return {
        "result": result,
        "result_reason": result_reason,
        "deltas": deltas,
        "epsilon_accept": epsilon_accept,
        "epsilon_reject": epsilon_reject,
        "epsilon_secondary": epsilon_secondary,
        "failed_metric_direction": failed_direction.value,
    }
