"""Evaluation metrics for FRCG-WM.

Sources:
- paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md lines 151-179
- paper_context_ref/15_TDD_TECHNICAL_DESIGN_DOCUMENT_v1.md lines 976-991
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from frcgw.evaluation.compute_budget import ComputeBudgetLog

FORBIDDEN_AGENT_KEYS = {
    "true_regime",
    "true_control_grammar",
    "true_change_point",
    "true_reveal_vs_shift",
    "true_wrong_hypothesis",
    "counterfactual_action_effects",
    "oracle_regime_action",
    "oracle_grammar_action",
    "oracle_best_action",
    "split_id",
    "ood_type",
    "template_id",
    "seed",
    "policy_id",
    "audit_metadata",
}


def _field(obj: Any, key: str, default: Any = None) -> Any:
    if obj is None:
        return default
    if isinstance(obj, Mapping):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def assert_no_hidden_labels_in_input(obs_dict: dict, context: str = "") -> None:
    """Raise AssertionError if any FORBIDDEN_AGENT_KEY is in obs_dict."""
    forbidden = sorted(FORBIDDEN_AGENT_KEYS.intersection(obs_dict))
    if forbidden:
        suffix = f" in {context}" if context else ""
        raise AssertionError(f"Forbidden agent observation keys{suffix}: {forbidden}")


# C2 proxy: ood_shift_f1 uses eval_labels.ood_type as split label.
def ood_shift_f1(episodes: list[dict]) -> dict[str, float]:
    """OOD shift detection F1 for the MET-OOD-003 STEP 8 proxy.

    Uses EvaluationLabels.ood_type as a split-time label, not inference input.
    Agent prediction uses any step with predicted_wrong=True as the shift signal.
    This is a proxy; the true regime-shift metric is deferred to STEP 9.
    """
    true_positives = 0
    false_positives = 0
    false_negatives = 0
    true_negatives = 0

    for episode in episodes:
        labels = _field(episode, "eval_labels")
        ood_type = _field(labels, "ood_type")
        if ood_type is None:
            continue

        is_ood_shift = str(ood_type).startswith("OOD")
        shift_detected = False
        for step in _field(episode, "steps", []) or []:
            if bool(_field(step, "predicted_wrong", False)):
                shift_detected = True
                break

        if shift_detected and is_ood_shift:
            true_positives += 1
        elif shift_detected and not is_ood_shift:
            false_positives += 1
        elif not shift_detected and is_ood_shift:
            false_negatives += 1
        else:
            true_negatives += 1

    precision_denom = true_positives + false_positives
    recall_denom = true_positives + false_negatives
    precision = true_positives / precision_denom if precision_denom else 0.0
    recall = true_positives / recall_denom if recall_denom else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "true_positives": true_positives,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "true_negatives": true_negatives,
    }


def regime_shift_f1(episodes: list[dict]) -> dict[str, float]:
    """Compute regime-shift detection F1 using true_regime from EvaluationLabels.

    true_regime is EVALUATION_ONLY and must never be used as inference input.
    A shift is any episode where true_regime changes across steps.
    """
    true_positives = 0
    false_positives = 0
    false_negatives = 0
    skipped = 0

    for episode in episodes:
        steps = _field(episode, "steps", []) or []
        regimes = []
        detected = False
        has_regime_data = False

        for step in steps:
            labels = _field(step, "eval_labels", {}) or {}
            true_regime = _field(labels, "true_regime")
            if true_regime is None:
                labels = _field(step, "evaluation_labels", {}) or {}
                true_regime = _field(labels, "true_regime")
            if true_regime is not None:
                has_regime_data = True
                regimes.append(true_regime)
            if bool(_field(step, "predicted_wrong", False)):
                detected = True

        if not has_regime_data:
            skipped += 1
            continue

        is_shift = len(set(regimes)) > 1

        if is_shift and detected:
            true_positives += 1
        elif not is_shift and detected:
            false_positives += 1
        elif is_shift and not detected:
            false_negatives += 1

    precision_denom = true_positives + false_positives
    recall_denom = true_positives + false_negatives
    precision = true_positives / precision_denom if precision_denom > 0 else 0.0
    recall = true_positives / recall_denom if recall_denom > 0 else 0.0
    f1_denom = precision + recall
    f1 = 2 * precision * recall / f1_denom if f1_denom > 0 else 0.0

    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "true_positives": float(true_positives),
        "false_positives": float(false_positives),
        "false_negatives": float(false_negatives),
        "skipped_no_regime_data": float(skipped),
    }


def task_success_rate(episodes: list[dict]) -> float:
    if not episodes:
        return 0.0
    return sum(1 for episode in episodes if bool(_field(episode, "success", False))) / len(episodes)


def normalized_return(
    episodes: list[dict],
    task_min: float = 0.0,
    task_max: float = 1.0,
) -> float:
    if not episodes:
        return 0.0
    denom = task_max - task_min + 1e-8
    values = []
    for episode in episodes:
        total_return = float(_field(episode, "total_return", 0.0))
        normalized = (total_return - task_min) / denom
        values.append(min(1.0, max(0.0, normalized)))
    return _mean(values)


def wrong_control_grammar_persistence(episodes: list[dict]) -> float:
    values = []
    for episode in episodes:
        labels = _field(episode, "eval_labels")
        evidence_timestamp = _field(labels, "evidence_timestamp")
        update_timestamp = _field(labels, "hypothesis_update_timestamp")
        if evidence_timestamp is None or update_timestamp is None:
            continue
        persistence = update_timestamp - evidence_timestamp
        if persistence >= 0:
            values.append(float(persistence))
    return _mean(values)


def failed_action_repetition_rate(episodes: list[dict]) -> float:
    repetitions = 0
    failure_opportunities = 0
    for episode in episodes:
        previous_failed_action: tuple[Any, Any] | None = None
        for step in _field(episode, "steps", []) or []:
            failed = bool(_field(step, "failed", False))
            if not failed:
                previous_failed_action = None
                continue
            failure_opportunities += 1
            action = (_field(step, "action_type"), _field(step, "action_params", {}))
            if previous_failed_action == action:
                repetitions += 1
            previous_failed_action = action
    return repetitions / max(1, failure_opportunities)


def recovery_delay(episodes: list[dict]) -> float:
    values = []
    for episode in episodes:
        labels = _field(episode, "eval_labels")
        evidence_timestamp = _field(labels, "evidence_timestamp")
        recovery_timestamp = _field(labels, "recovery_timestamp")
        if evidence_timestamp is None or recovery_timestamp is None:
            continue
        delay = recovery_timestamp - evidence_timestamp
        if delay >= 0:
            values.append(float(delay))
    return _mean(values)


def falsification_precision_recall(episodes: list[dict]) -> dict[str, float]:
    true_positives = 0
    false_positives = 0
    false_negatives = 0
    for episode in episodes:
        for step in _field(episode, "steps", []) or []:
            labels = _field(step, "eval_labels")
            true_wrong = _field(labels, "true_wrong_hypothesis")
            if true_wrong is None:
                continue
            predicted_wrong = bool(_field(step, "predicted_wrong", False))
            true_wrong = bool(true_wrong)
            if predicted_wrong and true_wrong:
                true_positives += 1
            elif predicted_wrong and not true_wrong:
                false_positives += 1
            elif not predicted_wrong and true_wrong:
                false_negatives += 1

    precision_denom = true_positives + false_positives
    recall_denom = true_positives + false_negatives
    precision = true_positives / precision_denom if precision_denom else 0.0
    recall = true_positives / recall_denom if recall_denom else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"precision": precision, "recall": recall, "f1": f1}


def falsification_calibration(episodes: list[dict], n_bins: int = 10) -> float:
    if n_bins <= 0:
        raise ValueError("n_bins must be positive")

    examples: list[tuple[float, float]] = []
    for episode in episodes:
        for step in _field(episode, "steps", []) or []:
            labels = _field(step, "eval_labels")
            true_wrong = _field(labels, "true_wrong_hypothesis")
            if true_wrong is None:
                continue
            wrong_prob = min(1.0, max(0.0, float(_field(step, "wrong_prob", 0.0))))
            examples.append((wrong_prob, 1.0 if bool(true_wrong) else 0.0))

    if not examples:
        return 0.0

    total = len(examples)
    ece = 0.0
    for bin_index in range(n_bins):
        lower = bin_index / n_bins
        upper = (bin_index + 1) / n_bins
        if bin_index == n_bins - 1:
            bin_examples = [(conf, acc) for conf, acc in examples if lower <= conf <= upper]
        else:
            bin_examples = [(conf, acc) for conf, acc in examples if lower <= conf < upper]
        if not bin_examples:
            continue
        mean_confidence = sum(conf for conf, _ in bin_examples) / len(bin_examples)
        mean_accuracy = sum(acc for _, acc in bin_examples) / len(bin_examples)
        ece += (len(bin_examples) / total) * abs(mean_confidence - mean_accuracy)
    return ece


def progress_per_compute(episodes: list[dict], compute_logs: list[ComputeBudgetLog]) -> float:
    total_progress = sum(float(_field(episode, "total_progress", 0.0)) for episode in episodes)
    total_compute = sum(log.total_compute_units() for log in compute_logs)
    return total_progress / max(1, total_compute)


def false_planning_call_rate(episodes: list[dict]) -> float:
    false_calls = 0
    total_calls = 0
    for episode in episodes:
        for event in _field(episode, "planning_events", []) or []:
            total_calls += 1
            if not bool(_field(event, "action_changed", False)) and not bool(
                _field(event, "progress_changed", False)
            ):
                false_calls += 1
    return false_calls / max(1, total_calls)


def action_switch_delay(episodes: list[dict]) -> float:
    values = []
    for episode in episodes:
        labels = _field(episode, "eval_labels")
        evidence_timestamp = _field(labels, "evidence_timestamp")
        rewrite_timestamp = _field(episode, "rewrite_timestamp")
        if evidence_timestamp is None or rewrite_timestamp is None:
            continue
        delay = rewrite_timestamp - evidence_timestamp
        if delay >= 0:
            values.append(float(delay))
    return _mean(values)


def _float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _counterfactuals_for_step(step: Any) -> list[Any]:
    counterfactuals = _field(step, "counterfactuals")
    if counterfactuals is None:
        counterfactuals = _field(step, "counterfactual")
    if counterfactuals is None:
        return []
    if isinstance(counterfactuals, Mapping):
        return [counterfactuals]
    return list(counterfactuals)


def _actual_progress_delta_for_step(step: Any) -> float | None:
    direct = _float_or_none(_field(step, "progress_delta"))
    if direct is not None:
        return direct

    for container_name in ("training_labels", "targets"):
        container = _field(step, container_name)
        value = _float_or_none(_field(container, "progress_delta"))
        if value is not None:
            return value
    return None


def _predicted_top1_delta_for_step(step: Any, counterfactuals: list[Any]) -> float | None:
    for key in (
        "predicted_top1_delta",
        "predicted_progress_delta",
        "model_predicted_progress_delta",
        "rollout_predicted_progress_delta",
    ):
        value = _float_or_none(_field(step, key))
        if value is not None:
            return value

    predicted_deltas: list[float] = []
    for counterfactual in counterfactuals:
        for key in (
            "predicted_progress_delta",
            "model_predicted_progress_delta",
            "rollout_predicted_progress_delta",
        ):
            value = _float_or_none(_field(counterfactual, key))
            if value is not None:
                predicted_deltas.append(value)
                break
    if not predicted_deltas:
        return None
    return max(predicted_deltas)


def alternative_rollout_fidelity(episodes: list) -> dict:
    """MET-WM-001: counterfactual top-1 predicted delta vs actual progress delta.

    paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md MET-WM-001 SSoT.

    Step-level fidelity = 1.0 - min(1.0, abs(predicted_top1_delta - actual_delta)).
    Episode mean, then overall mean. Counterfactual-free steps are skipped.
    All-empty episodes increment count_blocked.

    Returns:
        dict with keys:
          mean_fidelity: float | None
          count_episodes_with_counterfactuals: int
          count_blocked: int
          status: "OK" | "BLOCKED_no_counterfactuals" |
              "BLOCKED_no_model_rollout_prediction"
    """
    episode_means: list[float] = []
    count_episodes_with_counterfactuals = 0
    count_blocked = 0
    saw_model_rollout_prediction = False

    for episode in episodes:
        step_fidelities: list[float] = []
        episode_has_counterfactuals = False

        for step in _field(episode, "steps", []) or []:
            counterfactuals = _counterfactuals_for_step(step)
            if not counterfactuals:
                continue

            episode_has_counterfactuals = True
            predicted_delta = _predicted_top1_delta_for_step(step, counterfactuals)
            if predicted_delta is None:
                continue
            saw_model_rollout_prediction = True

            actual_delta = _actual_progress_delta_for_step(step)
            if actual_delta is None:
                continue

            step_fidelities.append(1.0 - min(1.0, abs(predicted_delta - actual_delta)))

        if episode_has_counterfactuals:
            count_episodes_with_counterfactuals += 1
        else:
            count_blocked += 1

        if step_fidelities:
            episode_means.append(_mean(step_fidelities))

    if not episode_means:
        status = (
            "BLOCKED_no_model_rollout_prediction"
            if count_episodes_with_counterfactuals > 0 and not saw_model_rollout_prediction
            else "BLOCKED_no_counterfactuals"
        )
        return {
            "mean_fidelity": None,
            "count_episodes_with_counterfactuals": count_episodes_with_counterfactuals,
            "count_blocked": count_blocked,
            "status": status,
        }

    return {
        "mean_fidelity": _mean(episode_means),
        "count_episodes_with_counterfactuals": count_episodes_with_counterfactuals,
        "count_blocked": count_blocked,
        "status": "OK",
    }


def compute_wrong_grammar_persistence_v1(episodes: list) -> dict:
    """MET-PERSIST-001: first_falsifying_evidence_t 이후 correct grammar switch까지 step 수.

    paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md:155 SSoT.

    inference-safe input: action.selected_hypothesis_id, step_index
    eval-only label: evaluation_labels.evidence_timestamp, evaluation_labels.correct_hypothesis_id

    Returns:
        dict with keys: mean_persistence, median, count_blocked, count_episodes, status
        count_blocked: evidence_timestamp/correct_hypothesis_id 누락 에피소드 수
        status: "OK" or "BLOCKED"
    """
    persistence_values = []
    blocked = 0
    for episode in episodes:
        eval_labels = getattr(episode, "evaluation_labels", None) if not isinstance(episode, dict) else None
        evidence_t = getattr(eval_labels, "evidence_timestamp", None) if eval_labels is not None else None
        correct_id = getattr(eval_labels, "correct_hypothesis_id", None) if eval_labels is not None else None
        if evidence_t is None or correct_id is None:
            blocked += 1
            continue

        steps = getattr(episode, "steps", []) or []
        switch_step = None
        for step in steps:
            step_idx = getattr(step, "step_index", None)
            if step_idx is None or step_idx < evidence_t:
                continue
            predicted = getattr(getattr(step, "action", None), "selected_hypothesis_id", None)
            if predicted == correct_id:
                switch_step = step_idx
                break

        if switch_step is None:
            persistence_values.append(max(0, len(steps) - evidence_t))
        else:
            persistence_values.append(max(0, switch_step - evidence_t))

    if not persistence_values:
        return {
            "mean_persistence": None,
            "median": None,
            "count_blocked": blocked,
            "count_episodes": len(episodes),
            "status": "BLOCKED",
        }
    sorted_vals = sorted(persistence_values)
    return {
        "mean_persistence": sum(persistence_values) / len(persistence_values),
        "median": sorted_vals[len(sorted_vals) // 2],
        "count_blocked": blocked,
        "count_episodes": len(episodes),
        "status": "OK",
    }


def compute_h_exec_null_rate(episodes: list) -> float | None:
    """C1 supporting metric: 전체 step 중 selected_hypothesis_id=None 비율.

    inference-safe input: action.selected_hypothesis_id only.
    """
    total = 0
    null_count = 0
    for episode in episodes:
        steps = getattr(episode, "steps", []) or []
        for step in steps:
            total += 1
            predicted = getattr(getattr(step, "action", None), "selected_hypothesis_id", None)
            if predicted is None:
                null_count += 1
    return null_count / total if total > 0 else None
