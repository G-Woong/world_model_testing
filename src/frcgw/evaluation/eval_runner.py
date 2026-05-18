"""Evaluation runner for text-only P3 evaluation.

Sources:
- paper_context_ref/15_TDD_TECHNICAL_DESIGN_DOCUMENT_v1.md lines 1044-1058
- paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md section 7
"""

from __future__ import annotations

import json
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from frcgw.evaluation.compute_budget import ComputeBudgetLog
from frcgw.evaluation.metrics import (
    action_switch_delay,
    alternative_rollout_fidelity,
    assert_no_hidden_labels_in_input,
    failed_action_repetition_rate,
    false_planning_call_rate,
    falsification_calibration,
    falsification_precision_recall,
    normalized_return,
    progress_per_compute,
    recovery_delay,
    task_success_rate,
    wrong_control_grammar_persistence,
)
from frcgw.schemas.step_schema import CandidateAction, PublicHistoryItem, PublicObservation


METRIC_FUNCTIONS = {
    "task_success_rate": task_success_rate,
    "normalized_return": normalized_return,
    "wrong_control_grammar_persistence": wrong_control_grammar_persistence,
    "failed_action_repetition_rate": failed_action_repetition_rate,
    "recovery_delay": recovery_delay,
    "falsification_precision_recall": falsification_precision_recall,
    "falsification_calibration": falsification_calibration,
    "progress_per_compute": progress_per_compute,
    "false_planning_call_rate": false_planning_call_rate,
    "action_switch_delay": action_switch_delay,
    "alternative_rollout_fidelity": alternative_rollout_fidelity,
}


@dataclass
class EvaluationResult:
    agent_id: str
    split: str
    seed: int
    metrics: dict[str, float | dict]
    compute_log: ComputeBudgetLog
    n_episodes: int
    report_path: str | None


class EvaluationRunner:
    def __init__(self, config: dict) -> None:
        self._config = dict(config)
        self._seeds = list(config.get("seeds") or [0])
        self._splits = list(config.get("splits") or [config.get("split", "text_id")])
        self._metrics = list(config.get("metrics") or METRIC_FUNCTIONS)
        self._compute_budget = dict(config.get("compute_budget") or {})
        self._report_path = config.get("report_path")
        forbidden_fields = set(config.get("forbidden_fields") or [])

        forbidden_metrics = forbidden_fields.intersection(self._metrics)
        if forbidden_metrics:
            raise ValueError(f"Forbidden fields configured as metrics: {sorted(forbidden_metrics)}")

        unknown_metrics = sorted(set(self._metrics).difference(METRIC_FUNCTIONS))
        if unknown_metrics:
            raise ValueError(f"Unknown metrics: {unknown_metrics}")

    def run(
        self,
        agent: Any,
        dataset_path: str | Path,
        split: str,
        seed: int,
    ) -> EvaluationResult:
        random.seed(seed)
        episodes = _load_jsonl(dataset_path)
        scored_episodes: list[dict[str, Any]] = []
        episode_compute_logs: list[ComputeBudgetLog] = []

        for episode in episodes:
            step_results: list[dict[str, Any]] = []
            episode_eval_labels: dict[str, Any] = {}
            episode_planning_events: list[dict[str, Any]] = []
            total_progress = 0.0
            total_return = 0.0
            success = False
            episode_compute_log = _empty_compute_log()

            for step in episode.get("steps", []):
                # Actual JSONL keys: public_observation, evaluation_labels, training_labels
                public_obs = dict(step.get("public_observation") or step.get("public_input") or {})
                assert_no_hidden_labels_in_input(
                    public_obs,
                    context=f"{episode.get('episode_id', '<unknown>')}:{step.get('step_index', 0)}",
                )
                obs = _build_public_observation(public_obs)
                action, compute_log = agent.act(obs)
                episode_compute_log = _add_compute_logs(episode_compute_log, compute_log)
                if hasattr(agent, "last_predicted_wrong"):
                    predicted_wrong_val = bool(agent.last_predicted_wrong)
                else:
                    predicted_wrong_val = bool(step.get("predicted_wrong", False))
                if hasattr(agent, "last_wrong_prob"):
                    wrong_prob_val = float(agent.last_wrong_prob)
                else:
                    wrong_prob_val = float(step.get("wrong_prob") or 0.0)
                f_t_val = _safe_float_or_none(getattr(agent, "last_F_t", None))
                predicted_progress_delta_val = getattr(agent, "last_predicted_progress_delta", None)

                eval_labels = dict(step.get("evaluation_labels") or step.get("eval_labels") or {})
                targets = dict(step.get("training_labels") or step.get("targets") or {})
                if not episode_eval_labels:
                    episode_eval_labels = eval_labels
                total_progress += float(targets.get("progress_delta") or 0.0)
                total_return += float(targets.get("progress_delta") or 0.0)
                success = success or total_progress > 0.0

                planning_events = list(step.get("planning_events") or [])
                episode_planning_events.extend(planning_events)
                step_results.append(
                    {
                        "step_index": step.get("step_index", len(step_results)),
                        "action_id": action.action_id,
                        "action_type": action.action_type,
                        "action_params": action.action_params,
                        "failed": bool(targets.get("true_failed_action", False)),
                        "eval_labels": eval_labels,
                        "predicted_wrong": predicted_wrong_val,
                        "wrong_prob": wrong_prob_val,
                        "f_t": f_t_val,
                        "progress_delta": float(targets.get("progress_delta") or 0.0),
                        "predicted_progress_delta": predicted_progress_delta_val,
                        "counterfactuals": list(
                            step.get("counterfactuals") or step.get("counterfactual") or []
                        ),
                        "planning_events": planning_events,
                    }
                )

            episode_ts = _compute_episode_timestamps(step_results)
            episode_eval_labels.update(episode_ts)
            scored_episodes.append(
                {
                    "episode_id": episode.get("episode_id"),
                    "success": success,
                    "total_return": total_return,
                    "total_progress": total_progress,
                    "eval_labels": episode_eval_labels,
                    "rewrite_timestamp": _first_present(episode.get("steps", []), "rewrite_timestamp"),
                    "planning_events": episode_planning_events,
                    "degenerate_f_t_count": _count_degenerate_f_t_steps(step_results),
                    "steps": step_results,
                }
            )
            episode_compute_logs.append(episode_compute_log)

        metrics = self._compute_metrics(scored_episodes, episode_compute_logs)
        aggregate_compute_log = _sum_compute_logs(episode_compute_logs)
        return EvaluationResult(
            agent_id=str(getattr(agent, "baseline_id", agent.__class__.__name__)),
            split=split,
            seed=seed,
            metrics=metrics,
            compute_log=aggregate_compute_log,
            n_episodes=len(scored_episodes),
            report_path=None,
        )

    def run_all_baselines(
        self,
        baseline_agents: list[Any],
        dataset_path: str | Path,
        split: str,
    ) -> list[EvaluationResult]:
        results = []
        for seed in self._seeds:
            for agent in baseline_agents:
                agent.reset()
                results.append(self.run(agent, dataset_path, split, seed))
        return results

    def write_report(self, results: list[EvaluationResult], output_dir: str | Path) -> str:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        metrics_path = output_path / "metrics.json"
        serializable_results = [_result_to_dict(result, str(metrics_path)) for result in results]
        metrics_path.write_text(
            json.dumps({"results": serializable_results}, indent=2, sort_keys=True),
            encoding="utf-8",
        )

        summary_lines = [
            "FRCG-WM P3 evaluation summary",
            f"n_results: {len(results)}",
        ]
        for result in results:
            summary_lines.append(
                f"{result.agent_id} seed={result.seed} split={result.split} n={result.n_episodes}"
            )
        (output_path / "summary.txt").write_text("\n".join(summary_lines) + "\n", encoding="utf-8")
        return str(metrics_path)

    def _compute_metrics(
        self,
        episodes: list[dict[str, Any]],
        compute_logs: list[ComputeBudgetLog],
    ) -> dict[str, float | dict]:
        values: dict[str, float | dict] = {}
        for metric_name in self._metrics:
            if metric_name == "progress_per_compute":
                value = progress_per_compute(episodes, compute_logs)
            else:
                value = METRIC_FUNCTIONS[metric_name](episodes)
            values[metric_name] = _without_none(value)
        return values


def _load_jsonl(dataset_path: str | Path) -> list[dict[str, Any]]:
    path = Path(dataset_path)
    episodes = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            episodes.append(json.loads(line))
    return episodes


def _build_public_observation(public_input: dict[str, Any]) -> PublicObservation:
    return PublicObservation(
        instruction=str(public_input.get("instruction", "")),
        dom_snapshot_public=public_input.get("dom_snapshot_public"),
        accessibility_tree_public=public_input.get("accessibility_tree_public"),
        screenshot_ref=public_input.get("screenshot_ref"),
        history_public=[
            PublicHistoryItem(
                step_index=int(item.get("step_index", 0)),
                action_summary=str(item.get("action_summary", "")),
                effect_summary=item.get("effect_summary"),
            )
            for item in public_input.get("history_public", [])
        ],
        candidate_actions_public=[
            CandidateAction(
                action_id=str(item.get("action_id", "")),
                action_type=str(item.get("action_type", "")),
                action_params=dict(item.get("action_params") or {}),
            )
            for item in public_input.get("candidate_actions_public", [])
        ],
    )


def _compute_episode_timestamps(step_results: list[dict]) -> dict:
    """Compute episode-level eval timestamps from step sequence.

    evidence_timestamp: first step where true_wrong_hypothesis=True
    hypothesis_update_timestamp: first step where true_wrong_hypothesis
        transitions True->False after evidence_timestamp
    recovery_timestamp: first step where progress_delta > 0 after evidence_timestamp
    """
    evidence_ts = None
    hypothesis_update_ts = None
    recovery_ts = None
    was_wrong = False

    for sr in step_results:
        idx = sr.get("step_index", 0)
        el = sr.get("eval_labels", {}) or {}
        tw = el.get("true_wrong_hypothesis")
        pd = float(sr.get("progress_delta", 0.0))

        if tw is True:
            if evidence_ts is None:
                evidence_ts = idx
            was_wrong = True

        if was_wrong and tw is False and hypothesis_update_ts is None:
            hypothesis_update_ts = idx

        if was_wrong and pd > 0 and recovery_ts is None:
            recovery_ts = idx

    return {
        "evidence_timestamp": evidence_ts,
        "hypothesis_update_timestamp": hypothesis_update_ts,
        "recovery_timestamp": recovery_ts,
    }


def _empty_compute_log() -> ComputeBudgetLog:
    return ComputeBudgetLog(0, 0, 0, 0, 0.0)


def _add_compute_logs(left: ComputeBudgetLog, right: ComputeBudgetLog) -> ComputeBudgetLog:
    return ComputeBudgetLog(
        planning_calls=left.planning_calls + right.planning_calls,
        rollout_steps=left.rollout_steps + right.rollout_steps,
        candidate_actions_scored=left.candidate_actions_scored + right.candidate_actions_scored,
        top_k_alternatives=left.top_k_alternatives + right.top_k_alternatives,
        wall_clock_seconds=left.wall_clock_seconds + right.wall_clock_seconds,
    )


def _sum_compute_logs(logs: list[ComputeBudgetLog]) -> ComputeBudgetLog:
    total = _empty_compute_log()
    for log in logs:
        total = _add_compute_logs(total, log)
    return total


def _first_present(steps: list[dict[str, Any]], key: str) -> Any:
    for step in steps:
        value = step.get(key)
        if value is not None:
            return value
    return None


def _safe_float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _step_f_t_value(step_result: dict[str, Any]) -> float | None:
    for key in ("f_t", "F_t", "last_F_t"):
        if key in step_result:
            return _safe_float_or_none(step_result.get(key))
    return None


def _count_degenerate_f_t_steps(step_results: list[dict[str, Any]]) -> int:
    return sum(
        1
        for step_result in step_results
        if _step_f_t_value(step_result) == 0.0
    )


def _without_none(value: Any) -> Any:
    if value is None:
        return 0.0
    if isinstance(value, dict):
        return {
            str(key): None if child is None else _without_none(child)
            for key, child in value.items()
        }
    if isinstance(value, (int, float)):
        return float(value)
    return value


def _result_to_dict(result: EvaluationResult, report_path: str) -> dict[str, Any]:
    data = asdict(result)
    data["compute_log"] = asdict(result.compute_log)
    data["report_path"] = report_path
    return data


__all__ = ["EvaluationResult", "EvaluationRunner", "_compute_episode_timestamps"]
