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


# ---------------------------------------------------------------------------
# Sequential detection metrics (TASK_LFD_001/007)
# ---------------------------------------------------------------------------

def detection_delay(switch_step: int, alarm_step: int | None) -> int | None:
    """Steps from regime switch to first alarm. None if no alarm fired."""
    if alarm_step is None:
        return None
    return max(0, alarm_step - switch_step)


def false_alarm_rate_per_step(
    alarm_steps: list[int],
    stable_steps: list[int],
) -> float:
    """FAR = alarms on stable (pre-switch) steps / total stable steps."""
    if not stable_steps:
        return 0.0
    stable_set = set(stable_steps)
    alarms_on_stable = sum(1 for s in alarm_steps if s in stable_set)
    return alarms_on_stable / len(stable_steps)


def run_length_posterior_ece(
    run_length_probs: list[list[float]],
    true_run_lengths: list[int],
    n_bins: int = 10,
) -> float:
    """ECE for run-length posterior calibration.

    Treats run-length as a discrete classification over n_bins buckets.
    Lower is better (well-calibrated = 0.0).
    """
    if not run_length_probs or not true_run_lengths:
        return 0.0

    examples: list[tuple[float, float]] = []
    for probs, true_rl in zip(run_length_probs, true_run_lengths):
        if not probs:
            continue
        max_rl = len(probs)
        # Confidence = probability mass at the true run length (clamped)
        idx = min(true_rl, max_rl - 1)
        conf = float(probs[idx])
        examples.append((conf, 1.0))

    if not examples:
        return 0.0

    total = len(examples)
    ece = 0.0
    for b in range(n_bins):
        lo, hi = b / n_bins, (b + 1) / n_bins
        bucket = [(c, a) for c, a in examples if lo <= c < hi]
        if not bucket:
            continue
        mean_conf = sum(c for c, _ in bucket) / len(bucket)
        mean_acc = sum(a for _, a in bucket) / len(bucket)
        ece += (len(bucket) / total) * abs(mean_conf - mean_acc)
    return ece


def regime_shift_f1_sequential(
    predicted_switch_steps: list[int | None],
    true_switch_steps: list[int | None],
    tolerance: int = 2,
) -> dict[str, float]:
    """F1/precision/recall for regime switch detection with tolerance window.

    Args:
        predicted_switch_steps: Per-episode first alarm step (None = no alarm).
        true_switch_steps: Per-episode true switch step (None = no switch).
        tolerance: Allowed step slack around true switch step.
    """
    tp = fp = fn = 0
    for pred, true in zip(predicted_switch_steps, true_switch_steps):
        has_switch = true is not None
        detected = pred is not None
        if has_switch and detected:
            if abs(pred - true) <= tolerance:
                tp += 1
            else:
                fp += 1
                fn += 1
        elif not has_switch and detected:
            fp += 1
        elif has_switch and not detected:
            fn += 1

    prec_denom = tp + fp
    rec_denom = tp + fn
    precision = tp / prec_denom if prec_denom else 0.0
    recall = tp / rec_denom if rec_denom else 0.0
    f1_denom = precision + recall
    f1 = 2 * precision * recall / f1_denom if f1_denom else 0.0
    return {"f1": f1, "precision": precision, "recall": recall}


def split_episodes_by_grammar_ood(
    episodes: list[dict],
) -> tuple[list[dict], list[dict]]:
    """Split episodes into ID (in-distribution) and OOD (grammar shift) subsets.

    OOD grammar families: filter_accordion, nested_scroll (per generator.py).
    This implements the SPLIT-003 equivalent for Reviewer-2 FATAL-1 and FATAL-3 defense.

    Episodes are labeled by task_family field. Families not in OOD_GRAMMAR_FAMILIES
    are treated as ID.
    """
    OOD_FAMILIES = {"filter_accordion", "nested_scroll"}
    id_episodes, ood_episodes = [], []
    for ep in episodes:
        family = str(_field(ep, "task_family", "") or "").lower()
        if family in OOD_FAMILIES:
            ood_episodes.append(ep)
        else:
            id_episodes.append(ep)
    return id_episodes, ood_episodes


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


def _roc_auc_numpy(y_true: list[int], y_score: list[float]) -> float:
    """Compute ROC-AUC without sklearn using numpy trapezoid integration."""
    import numpy as np

    yt = np.array(y_true, dtype=float)
    ys = np.array(y_score, dtype=float)
    thresholds = np.sort(np.unique(ys))[::-1]
    tpr_list = [0.0]
    fpr_list = [0.0]
    pos = yt.sum()
    neg = len(yt) - pos
    if pos == 0 or neg == 0:
        return 0.0
    for t in thresholds:
        pred = (ys >= t).astype(float)
        tp = ((pred == 1) & (yt == 1)).sum()
        fp = ((pred == 1) & (yt == 0)).sum()
        tpr_list.append(float(tp / pos))
        fpr_list.append(float(fp / neg))
    tpr_list.append(1.0)
    fpr_list.append(1.0)
    return float(np.trapezoid(tpr_list, fpr_list))


def _pr_auc_numpy(y_true: list[int], y_score: list[float]) -> float:
    """Compute PR-AUC (average precision) without sklearn using numpy."""
    import numpy as np

    yt = np.array(y_true, dtype=float)
    ys = np.array(y_score, dtype=float)
    thresholds = np.sort(np.unique(ys))[::-1]
    precision_list = []
    recall_list = []
    pos = yt.sum()
    if pos == 0:
        return 0.0
    for t in thresholds:
        pred = (ys >= t).astype(float)
        tp = ((pred == 1) & (yt == 1)).sum()
        fp = ((pred == 1) & (yt == 0)).sum()
        fn = ((pred == 0) & (yt == 1)).sum()
        p = float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0
        r = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0
        precision_list.append(p)
        recall_list.append(r)
    if not recall_list:
        return 0.0
    # Sort by recall
    pairs = sorted(zip(recall_list, precision_list))
    recalls = [p[0] for p in pairs]
    precs = [p[1] for p in pairs]
    return float(np.trapezoid(precs, recalls))


def threshold_free_c3_auroc(episodes: list[dict]) -> dict[str, float]:
    """Threshold-free AUROC/AUPRC for C3 falsification detection.

    Uses wrong_prob (continuous) vs true_wrong_hypothesis (binary label).
    true_wrong_hypothesis is eval-only and never enters inference input.

    Source MD: paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md MET-FALS-003 (threshold-free)
    """
    y_true: list[int] = []
    y_score: list[float] = []
    for ep in episodes:
        for step in _field(ep, "steps", []) or []:
            label_dict = _field(step, "eval_labels", {}) or {}
            twh = _field(label_dict, "true_wrong_hypothesis")
            wp = _field(step, "wrong_prob")
            if twh is not None and wp is not None:
                y_true.append(int(bool(twh)))
                y_score.append(float(wp))
    n_pos = sum(y_true)
    n_total = len(y_true)
    if n_total < 2 or n_pos == 0 or n_pos == n_total:
        return {"auroc": 0.0, "auprc": 0.0, "n_positive": n_pos, "n_total": n_total}
    auroc = _roc_auc_numpy(y_true, y_score)
    auprc = _pr_auc_numpy(y_true, y_score)
    return {"auroc": auroc, "auprc": auprc, "n_positive": n_pos, "n_total": n_total}


def evidence_accumulation_quality(episodes: list[dict], window: int = 10) -> dict[str, float]:
    """Sliding window AUROC for evidence accumulation quality.

    Compares per-step AUROC (instantaneous) vs window-averaged wrong_prob AUROC.
    Measures whether accumulated evidence improves detection over instantaneous.

    Source MD: paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md MET-FALS-004 (accumulation)
    """
    y_true_inst: list[int] = []
    y_score_inst: list[float] = []
    y_true_accum: list[int] = []
    y_score_accum: list[float] = []
    for ep in episodes:
        wp_history: list[float] = []
        for step in _field(ep, "steps", []) or []:
            label_dict = _field(step, "eval_labels", {}) or {}
            twh = _field(label_dict, "true_wrong_hypothesis")
            wp = _field(step, "wrong_prob")
            if twh is None or wp is None:
                continue
            wp_val = float(wp)
            wp_history.append(wp_val)
            window_vals = wp_history[-window:]
            accum_wp = sum(window_vals) / len(window_vals)
            y_true_inst.append(int(bool(twh)))
            y_score_inst.append(wp_val)
            y_true_accum.append(int(bool(twh)))
            y_score_accum.append(accum_wp)

    def _safe_auc(yt: list[int], ys: list[float]) -> float:
        if len(yt) < 2 or sum(yt) == 0 or sum(yt) == len(yt):
            return 0.0
        return _roc_auc_numpy(yt, ys)

    return {
        "instantaneous_auroc": _safe_auc(y_true_inst, y_score_inst),
        "window_auroc": _safe_auc(y_true_accum, y_score_accum),
        "window_size": float(window),
        "n_steps": float(len(y_true_inst)),
    }


def fair_ppc(episodes: list[dict]) -> dict[str, float]:
    """Fair compute-matched progress per compute.

    Denominator = actual wall_clock_seconds (or self-report if wall_clock=0).
    Avoids self-report bias in planning_calls vs heuristic agents.

    Source MD: paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md MET-COMPUTE-001 (fair)
    """
    total_progress, total_wall_clock, total_self_report = 0.0, 0.0, 0.0
    for ep in episodes:
        total_progress += float(_field(ep, "total_progress", 0.0) or 0.0)
        compute_logs = _field(ep, "compute_logs")
        if compute_logs is None:
            compute_logs = [_field(ep, "compute_log", {}) or {}]
        for clog in compute_logs:
            total_wall_clock += float(_field(clog, "wall_clock_seconds", 0.0) or 0.0)
            total_self_report += (
                float(_field(clog, "planning_calls", 0.0) or 0.0)
                + float(_field(clog, "rollout_steps", 0.0) or 0.0)
                + float(_field(clog, "candidate_actions_scored", 0.0) or 0.0)
            )
    ppc_wall = total_progress / total_wall_clock if total_wall_clock > 0 else 0.0
    ppc_self = total_progress / total_self_report if total_self_report > 0 else 0.0
    return {
        "ppc_wall_clock": ppc_wall,
        "ppc_self_report": ppc_self,
        "total_wall_clock_seconds": total_wall_clock,
        "total_self_report_units": total_self_report,
        "total_progress": total_progress,
    }
