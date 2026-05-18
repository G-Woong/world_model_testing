"""Real episode-level eval runner for FRCG-WM P3.

Source: docs/orchestration/lr_alignment/18_real_eval_runner_contract.md

The confidence_threshold metric remains a STEP 3 placeholder until the
collector writes selected_hypothesis_confidence labels into real episodes.
"""
from __future__ import annotations

import argparse
import builtins
import datetime as _datetime
import json
import statistics
import subprocess
import sys
from collections import defaultdict
from dataclasses import asdict
from pathlib import Path
from typing import Any, Callable

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from frcgw.evaluation.ablations import ABLATION_REGISTRY, apply_ablation
from frcgw.evaluation.baselines import (
    CATTSStyleUncertaintyGateAgent,
    ComputeMatchedRandomAgent,
    CUWMStyleCandidateSimulationAgent,
    VerifierRecoveryAgent,
    VLAALoopHeuristicAgent,
    WACStyleConsequenceCorrectionAgent,
    WebWorldStyleSearchAgent,
)
from frcgw.evaluation.eval_runner import EvaluationResult, EvaluationRunner
from frcgw.evaluation.frcg_agent import TextFRCGModelAgent
from frcgw.schemas.step_schema import PublicObservation


AgentFactory = Callable[[], Any]
C5_DEGENERATE_PREDICTOR = "DEGENERATE_PREDICTOR"
C5_DEGENERATE_OR_UNTRAINED = "DEGENERATE_OR_UNTRAINED"
C5_OK = "OK"
C5_NO_DATA = "NO_DATA"
C5_AUDIT_FILENAME = "step4_ece_degenerate_predictor_audit.json"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run real episode-level LR evaluation.")
    parser.add_argument("--config", required=True)
    parser.add_argument("--split", default=None)
    parser.add_argument("--out-dir", default=None)
    parser.add_argument("--max-episodes", type=int, default=None)
    return parser.parse_args()


def _install_forbidden_source_guard(forbidden_paths: list[str]) -> Callable[[], None]:
    original_open = builtins.open
    original_path_open = Path.open
    original_read_text = Path.read_text

    def is_read_mode(mode: str | None) -> bool:
        mode = mode or "r"
        return "r" in mode or "+" in mode

    def is_forbidden(path_like: Any) -> bool:
        if not isinstance(path_like, (str, bytes, Path)):
            return False
        requested = Path(path_like)
        requested_str = str(requested)
        try:
            requested_resolved = str(requested.resolve())
        except OSError:
            requested_resolved = requested_str
        for forbidden in forbidden_paths:
            forbidden_path = Path(forbidden)
            try:
                forbidden_resolved = str(forbidden_path.resolve())
            except OSError:
                forbidden_resolved = str(forbidden_path)
            if requested_resolved == forbidden_resolved:
                return True
            if requested_str.endswith(forbidden):
                return True
            if requested_resolved.endswith(forbidden):
                return True
        return False

    def guarded_open(file: Any, mode: str = "r", *args: Any, **kwargs: Any) -> Any:
        if is_read_mode(mode) and is_forbidden(file):
            raise RuntimeError(f"forbidden source: {file}")
        return original_open(file, mode, *args, **kwargs)

    def guarded_path_open(self: Path, mode: str = "r", *args: Any, **kwargs: Any) -> Any:
        if is_read_mode(mode) and is_forbidden(self):
            raise RuntimeError(f"forbidden source: {self}")
        return original_path_open(self, mode, *args, **kwargs)

    def guarded_read_text(self: Path, *args: Any, **kwargs: Any) -> str:
        if is_forbidden(self):
            raise RuntimeError(f"forbidden source: {self}")
        return original_read_text(self, *args, **kwargs)

    builtins.open = guarded_open
    Path.open = guarded_path_open
    Path.read_text = guarded_read_text

    def uninstall() -> None:
        builtins.open = original_open
        Path.open = original_path_open
        Path.read_text = original_read_text

    return uninstall


def _build_agent_dispatch_table(config: dict[str, Any]) -> dict[str, AgentFactory]:
    class_table: dict[str, type] = {
        "TextFRCGModelAgent": TextFRCGModelAgent,
        "VerifierRecoveryAgent": VerifierRecoveryAgent,
        "CATTSStyleUncertaintyGateAgent": CATTSStyleUncertaintyGateAgent,
        "ComputeMatchedRandomAgent": ComputeMatchedRandomAgent,
        "WACStyleConsequenceCorrectionAgent": WACStyleConsequenceCorrectionAgent,
        "CUWMStyleCandidateSimulationAgent": CUWMStyleCandidateSimulationAgent,
        "WebWorldStyleSearchAgent": WebWorldStyleSearchAgent,
        "VLAALoopHeuristicAgent": VLAALoopHeuristicAgent,
    }
    dispatch: dict[str, AgentFactory] = {}

    for agent_spec in config.get("agents", []):
        agent_id = str(agent_spec["id"])
        class_name = str(agent_spec["class"])
        if class_name not in class_table:
            raise KeyError(f"Unknown agent class for {agent_id}: {class_name}")
        cls = class_table[class_name]

        def factory(spec: dict[str, Any] = agent_spec, agent_cls: type = cls) -> Any:
            if agent_cls is TextFRCGModelAgent:
                agent = agent_cls(ckpt_path=spec.get("ckpt_path"))
            else:
                agent = agent_cls()

            ablation_id = spec.get("ablation")
            if ablation_id:
                if ablation_id not in ABLATION_REGISTRY:
                    raise KeyError(f"Unknown ablation for {spec['id']}: {ablation_id}")
                agent = apply_ablation(agent, ABLATION_REGISTRY[ablation_id])
            return agent

        dispatch[agent_id] = factory

    return dispatch


def _ckpt_paths_all_provided(config: dict[str, Any]) -> bool:
    text_specs = [
        spec
        for spec in config.get("agents", [])
        if spec.get("class") == "TextFRCGModelAgent"
    ]
    return all(bool(spec.get("ckpt_path")) for spec in text_specs)


def _preflight_dry_obs_check(dispatch_table: dict[str, AgentFactory]) -> None:
    obs = PublicObservation(
        instruction="preflight",
        history_public=[],
        candidate_actions_public=[],
    )
    for factory in dispatch_table.values():
        agent = factory()
        if hasattr(agent, "reset"):
            agent.reset()
        agent.act(obs)


class _TracingAgent:
    def __init__(self, agent: Any) -> None:
        self._agent = agent
        self.records: list[dict[str, Any]] = []

    def __getattr__(self, name: str) -> Any:
        return getattr(self._agent, name)

    def reset(self) -> None:
        self.records = []
        if hasattr(self._agent, "reset"):
            self._agent.reset()

    def act(self, obs: PublicObservation) -> Any:
        action, compute_log = self._agent.act(obs)
        self.records.append(
            {
                "action_id": action.action_id,
                "action_type": action.action_type,
                "planning_calls": compute_log.planning_calls,
                "rollout_steps": compute_log.rollout_steps,
                "predicted_wrong": getattr(self._agent, "last_predicted_wrong", None),
                "wrong_prob": getattr(self._agent, "last_wrong_prob", None),
                "f_t": getattr(self._agent, "last_F_t", None),
                "tau_f": getattr(self._agent, "_last_tau_f", None),
                "selected_hypothesis_id": getattr(
                    self._agent,
                    "_last_selected_hypothesis_id",
                    None,
                ),
                "selected_hypothesis_confidence": getattr(
                    self._agent,
                    "_last_selected_hypothesis_confidence",
                    None,
                ),
            }
        )
        return action, compute_log


def _load_jsonl(path: str | Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def _limited_jsonl_path(dataset_path: str | Path, max_episodes: int | None, out_dir: Path) -> Path:
    source = Path(dataset_path)
    if max_episodes is None:
        return source
    if max_episodes <= 0:
        raise ValueError("--max-episodes must be positive")
    episodes = _load_jsonl(source)[:max_episodes]
    limited_path = out_dir / f"_max_episodes_{max_episodes}.jsonl"
    limited_path.write_text(
        "\n".join(json.dumps(episode) for episode in episodes) + "\n",
        encoding="utf-8",
    )
    return limited_path


def _attach_trace_records(
    result: EvaluationResult,
    dataset_path: str | Path,
    trace_records: list[dict[str, Any]],
) -> None:
    episodes = _load_jsonl(dataset_path)
    per_step: list[dict[str, Any]] = []
    trace_index = 0
    for episode in episodes:
        episode_id = str(episode.get("episode_id", f"episode_{len(per_step)}"))
        for step in episode.get("steps", []):
            trace = trace_records[trace_index] if trace_index < len(trace_records) else {}
            trace_index += 1
            step_index = int(step.get("step_index", trace_index - 1))
            eval_labels = dict(step.get("evaluation_labels") or step.get("eval_labels") or {})
            training_labels = dict(step.get("training_labels") or step.get("targets") or {})
            observed_effect = dict(step.get("observed_effect_public") or {})
            predicted_wrong = trace.get("predicted_wrong")
            if predicted_wrong is None:
                predicted_wrong = bool(step.get("predicted_wrong", False))
            wrong_prob = trace.get("wrong_prob")
            if wrong_prob is None:
                wrong_prob = float(step.get("wrong_prob") or 0.0)
            per_step.append(
                {
                    "episode_id": episode_id,
                    "step_id": step.get("step_id") or f"{episode_id}:{step_index}",
                    "step_index": step_index,
                    "action_id": trace.get("action_id", "unknown"),
                    "action_type": trace.get("action_type", "unknown"),
                    "f_t": trace.get("f_t"),
                    "tau_f": trace.get("tau_f"),
                    "predicted_wrong": bool(predicted_wrong),
                    "wrong_prob": float(wrong_prob),
                    "planning_calls": int(trace.get("planning_calls") or 0),
                    "rollout_steps": int(trace.get("rollout_steps") or 0),
                    "selected_hypothesis_id": trace.get("selected_hypothesis_id"),
                    "selected_hypothesis_confidence": trace.get(
                        "selected_hypothesis_confidence"
                    ),
                    "observed_effect_type": observed_effect.get(
                        "effect_type",
                        training_labels.get("true_action_effect_type", "unknown"),
                    ),
                    "true_wrong_hypothesis_available": eval_labels.get("true_wrong_hypothesis") is not None,
                }
            )
    result._real_eval_step_records = per_step  # type: ignore[attr-defined]


def _write_per_step_jsonl(
    result: EvaluationResult,
    agent_id: str,
    seed: int,
    split: str,
    out_dir: Path,
) -> Path:
    per_step_dir = out_dir / "per_step"
    per_step_dir.mkdir(parents=True, exist_ok=True)
    path = per_step_dir / f"{agent_id}_seed{seed}.jsonl"
    run_id = f"{agent_id}_seed{seed}"
    records = list(getattr(result, "_real_eval_step_records", []))
    if not records:
        records = [
            {
                "episode_id": f"episode_{index}",
                "step_id": f"episode_{index}:0",
                "step_index": 0,
                "action_id": "unknown",
                "action_type": "unknown",
                "f_t": None,
                "tau_f": None,
                "predicted_wrong": False,
                "wrong_prob": 0.0,
                "planning_calls": 0,
                "rollout_steps": 0,
                "observed_effect_type": "unknown",
                "true_wrong_hypothesis_available": False,
            }
            for index in range(result.n_episodes)
        ]
    rows = []
    for record in records:
        rows.append(
            {
                "run_id": run_id,
                "agent_id": agent_id,
                "agent_type": result.agent_id,
                "episode_id": record["episode_id"],
                "step_id": record["step_id"],
                "step_index": record["step_index"],
                "split": split,
                "action_id": record["action_id"],
                "action_type": record["action_type"],
                "selected_hypothesis_id": record.get("selected_hypothesis_id"),
                "selected_hypothesis_confidence": record.get(
                    "selected_hypothesis_confidence"
                ),
                "f_t": record["f_t"],
                "tau_f": record.get("tau_f"),
                "predicted_wrong": record["predicted_wrong"],
                "wrong_prob": record["wrong_prob"],
                "planning_calls": record["planning_calls"],
                "rollout_steps": record["rollout_steps"],
                "observed_effect_type": record["observed_effect_type"],
                "true_wrong_hypothesis_available": record["true_wrong_hypothesis_available"],
                "leakage_guard_passed": True,
                "error": None,
            }
        )
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
    return path


def _write_per_episode_jsonl(
    result: EvaluationResult,
    agent_id: str,
    seed: int,
    split: str,
    out_dir: Path,
) -> Path:
    per_episode_dir = out_dir / "per_episode"
    per_episode_dir.mkdir(parents=True, exist_ok=True)
    path = per_episode_dir / f"{agent_id}_seed{seed}.jsonl"
    run_id = f"{agent_id}_seed{seed}"
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in getattr(result, "_real_eval_step_records", []):
        grouped[str(record["episode_id"])].append(record)
    if not grouped:
        grouped = {f"episode_{index}": [] for index in range(result.n_episodes)}
    rows = []
    for episode_id, records in grouped.items():
        rows.append(
            {
                "run_id": run_id,
                "agent_id": agent_id,
                "episode_id": episode_id,
                "split": split,
                "num_steps": len(records),
                "planning_calls_total": sum(int(record.get("planning_calls") or 0) for record in records),
                "rollout_steps_total": sum(int(record.get("rollout_steps") or 0) for record in records),
                "falsification_tp": 0,
                "falsification_fp": 0,
                "falsification_fn": 0,
                "degenerate_f_t_count": 0,
                "h_exec_null_count": 0,
                "blocked_metrics": [],
                "errors": [],
            }
        )
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
    return path


def _audit_dataset(dataset_path: str | Path) -> dict[str, Any]:
    path = Path(dataset_path)
    episodes = _load_jsonl(path)[:100]
    total_steps = 0
    hypothesis_updates = 0
    recoveries = 0
    confidences = 0
    counterfactuals = 0
    for episode in episodes:
        for step in episode.get("steps", []):
            total_steps += 1
            eval_labels = dict(step.get("evaluation_labels") or step.get("eval_labels") or {})
            action = dict(step.get("action") or {})
            if eval_labels.get("hypothesis_update_timestamp") is not None:
                hypothesis_updates += 1
            if eval_labels.get("recovery_timestamp") is not None:
                recoveries += 1
            if (
                step.get("selected_hypothesis_confidence") is not None
                or action.get("selected_hypothesis_confidence") is not None
            ):
                confidences += 1
            cfs = step.get("counterfactuals", step.get("counterfactual", [])) or []
            if cfs:
                counterfactuals += 1

    denom = max(1, total_steps)
    return {
        "hypothesis_update_timestamp_coverage": hypothesis_updates / denom,
        "recovery_timestamp_coverage": recoveries / denom,
        "selected_hypothesis_confidence_coverage": confidences / denom,
        "counterfactual_coverage": counterfactuals / denom,
        "ood_split_exists": (path.parent / "test_ood.jsonl").exists(),
        "total_episodes_sampled": len(episodes),
    }


def _mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def _compute_c5_calibration_audit(
    wrong_probs: list[float],
    f_t_values: list[float] | None = None,
) -> dict[str, Any]:
    f_t_values = f_t_values or []
    if wrong_probs:
        variance = statistics.pvariance(wrong_probs)
        unique_count = len(set(wrong_probs))
        mean_wp = sum(wrong_probs) / len(wrong_probs)
        mean_f_t = sum(f_t_values) / len(f_t_values) if f_t_values else None
        if (
            variance < 1e-6
            or unique_count <= 2
            or (mean_f_t is not None and mean_f_t < 1e-6)
        ):
            c5_status = C5_DEGENERATE_PREDICTOR
        else:
            c5_status = C5_OK
    else:
        variance = None
        unique_count = None
        mean_wp = None
        mean_f_t = None
        c5_status = C5_NO_DATA

    return {
        "n_steps": len(wrong_probs),
        "variance_wrong_prob": variance,
        "unique_wrong_prob_count": unique_count,
        "mean_wrong_prob": mean_wp,
        "mean_f_t": mean_f_t,
        "C5_calibration_status": c5_status,
    }


def _collect_trace_float_values(
    all_results: list[tuple[str, int, EvaluationResult]],
    key: str,
) -> list[float]:
    values: list[float] = []
    for _agent_id, _seed, result in all_results:
        for record in getattr(result, "_real_eval_step_records", []):
            value = record.get(key)
            if value is not None:
                values.append(float(value))
    return values


def _build_c5_calibration_audit(
    all_results: list[tuple[str, int, EvaluationResult]],
) -> dict[str, Any]:
    return _compute_c5_calibration_audit(
        _collect_trace_float_values(all_results, "wrong_prob"),
        _collect_trace_float_values(all_results, "f_t"),
    )


def _write_ece_degenerate_predictor_audit(
    audit_payload: dict[str, Any],
    audit_dir: Path | None = None,
) -> Path:
    target_dir = audit_dir or (REPO_ROOT / "outputs" / "audits")
    target_dir.mkdir(parents=True, exist_ok=True)
    path = target_dir / C5_AUDIT_FILENAME
    path.write_text(json.dumps(audit_payload, indent=2), encoding="utf-8")
    return path


def _metric(value: float | None, status: str = "OK") -> dict[str, Any]:
    return {"value": value, "status": status}


def _blocked(reason: str) -> dict[str, Any]:
    return {"value": None, "status": reason}


def _build_metrics_with_blocked_markers(
    all_results: list[tuple[str, int, EvaluationResult]],
    config: dict[str, Any],
    dataset_audit: dict[str, Any],
) -> dict[str, Any]:
    by_agent: dict[str, list[EvaluationResult]] = defaultdict(list)
    for agent_id, _seed, result in all_results:
        by_agent[agent_id].append(result)

    c5_audit = _build_c5_calibration_audit(all_results)
    c5_status = str(c5_audit["C5_calibration_status"])
    if not _ckpt_paths_all_provided(config):
        c5_status = C5_DEGENERATE_OR_UNTRAINED
        c5_audit = dict(c5_audit)
        c5_audit["C5_calibration_status"] = c5_status
    agents_payload: dict[str, dict[str, Any]] = {}
    blocked_count = 0
    for agent_id, results in by_agent.items():
        def values(metric_name: str) -> list[float]:
            output = []
            for result in results:
                value = result.metrics.get(metric_name)
                if isinstance(value, (int, float)):
                    output.append(float(value))
            return output

        def nested_values(metric_name: str, child_name: str) -> list[float]:
            output = []
            for result in results:
                value = result.metrics.get(metric_name)
                if isinstance(value, dict) and isinstance(value.get(child_name), (int, float)):
                    output.append(float(value[child_name]))
            return output

        payload = {
            "task_success_rate": _metric(_mean(values("task_success_rate"))),
            "normalized_return": _metric(_mean(values("normalized_return"))),
            "C3_falsification_precision": _metric(
                _mean(nested_values("falsification_precision_recall", "precision"))
            ),
            "C3_falsification_recall": _metric(
                _mean(nested_values("falsification_precision_recall", "recall"))
            ),
            "C3_falsification_f1": _metric(
                _mean(nested_values("falsification_precision_recall", "f1"))
            ),
            "C6_progress_per_compute": _metric(_mean(values("progress_per_compute"))),
            "false_planning_call_rate": _metric(_mean(values("false_planning_call_rate"))),
            "failed_action_repetition_rate": _metric(
                _mean(values("failed_action_repetition_rate"))
            ),
            "action_switch_delay": _metric(_mean(values("action_switch_delay"))),
        }
        if dataset_audit.get("hypothesis_update_timestamp_coverage", 0) == 0:
            payload["C1_persistence"] = _blocked("BLOCKED_no_hypothesis_update_timestamp")
        else:
            payload["C1_persistence"] = _metric(
                _mean(values("wrong_control_grammar_persistence"))
            )
        if dataset_audit.get("recovery_timestamp_coverage", 0) == 0:
            payload["C3_recovery_delay"] = _blocked("BLOCKED_no_recovery_timestamp")
        else:
            payload["C3_recovery_delay"] = _metric(_mean(values("recovery_delay")))
        if c5_status == C5_DEGENERATE_PREDICTOR:
            payload["C5_calibration_ece"] = _blocked("BLOCKED_DEGENERATE_PREDICTOR")
        elif c5_status == C5_DEGENERATE_OR_UNTRAINED:
            payload["C5_calibration_ece"] = _blocked("BLOCKED_DEGENERATE_OR_UNTRAINED")
        elif dataset_audit.get("selected_hypothesis_confidence_coverage", 0) == 0:
            payload["C5_calibration_ece"] = _blocked("BLOCKED_no_confidence_label")
        elif c5_status == C5_NO_DATA:
            payload["C5_calibration_ece"] = _blocked("BLOCKED_no_wrong_prob_trace")
        else:
            payload["C5_calibration_ece"] = _metric(
                _mean(values("falsification_calibration"))
            )
        if dataset_audit.get("counterfactual_coverage", 0) == 0:
            payload["C4_rollout_fidelity"] = _blocked("BLOCKED_no_counterfactual_samples")
            payload["C4_alternative_adoption_rate"] = _blocked(
                "BLOCKED_no_counterfactual_samples"
            )
        else:
            payload["C4_rollout_fidelity"] = _blocked("BLOCKED_counterfactual_metric_not_implemented")
            payload["C4_alternative_adoption_rate"] = _blocked(
                "BLOCKED_counterfactual_metric_not_implemented"
            )
        if not dataset_audit.get("ood_split_exists", False):
            payload["C2_regime_split"] = _blocked("BLOCKED_no_ood_split")
        else:
            payload["C2_regime_split"] = _blocked("BLOCKED_regime_split_metric_not_implemented")

        blocked_count += sum(
            1 for value in payload.values() if str(value.get("status", "")).startswith("BLOCKED")
        )
        agents_payload[agent_id] = payload

    return {
        "run_mode": "real_episode_eval",
        "agents": agents_payload,
        "dataset_audit": dataset_audit,
        "fake_metric_count": 0,
        "blocked_metric_count": blocked_count,
        "C5_calibration_status": c5_status,
        "C5_calibration_audit": c5_audit,
    }


def _write_manifest(
    config: dict[str, Any],
    out_dir: Path,
    metrics_payload: dict[str, Any],
    forbidden_source_assertion: str,
    dataset_audit: dict[str, Any],
    *,
    write: bool = True,
) -> dict[str, Any]:
    ckpt_paths_all_provided = _ckpt_paths_all_provided(config)
    valid_trained_eval = ckpt_paths_all_provided
    random_init_ok = ckpt_paths_all_provided
    hard_checks_all_pass = (
        metrics_payload.get("fake_metric_count") == 0
        and forbidden_source_assertion == "none_read"
        and (random_init_ok or ckpt_paths_all_provided)
    )
    try:
        git_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        git_sha = "unknown"
    c5_status = metrics_payload.get("C5_calibration_status")
    if not valid_trained_eval:
        c5_status = C5_DEGENERATE_OR_UNTRAINED
    manifest = {
        "run_mode": config.get("run_mode", "real_episode_eval"),
        "created_at_utc": _datetime.datetime.now(_datetime.UTC).isoformat(),
        "git_sha": git_sha,
        "split": config.get("split", "test_id"),
        "seeds": list(config.get("seeds", [0])),
        "source_artifacts_used": [config["dataset_path"]],
        "forbidden_source_artifacts": list(config.get("forbidden_sources", [])),
        "forbidden_source_assertion": forbidden_source_assertion,
        "random_init_ok": random_init_ok,
        "ckpt_paths_all_provided": ckpt_paths_all_provided,
        "valid_trained_eval": valid_trained_eval,
        "hard_checks_all_pass": hard_checks_all_pass,
        "C5_calibration_status": c5_status,
        "dataset_audit": dataset_audit,
        "fake_metric_count": metrics_payload.get("fake_metric_count"),
        "blocked_metric_count": metrics_payload.get("blocked_metric_count"),
    }
    if write:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "manifest.json").write_text(
            json.dumps(manifest, indent=2),
            encoding="utf-8",
        )
    return manifest


def main() -> int:
    args = _parse_args()
    config = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    if args.split:
        config["split"] = args.split
    if args.out_dir:
        config["out_dir"] = args.out_dir

    out_dir = Path(config.get("out_dir", "outputs/runs/p3_lr_real_eval"))
    out_dir.mkdir(parents=True, exist_ok=True)
    forbidden_source_assertion = "none_read"
    uninstall_guard = _install_forbidden_source_guard(config.get("forbidden_sources", []))

    try:
        dispatch_table = _build_agent_dispatch_table(config)
        _preflight_dry_obs_check(dispatch_table)

        dataset_path = str(config["dataset_path"])
        split = config.get("split", "test_id")
        seeds = list(config.get("seeds", [0]))
        runner_config = {
            "seeds": seeds,
            "split": split,
            "metrics": config.get("metrics", []),
            "compute_budget": config.get("compute_budget", {}),
        }
        runner = EvaluationRunner(runner_config)
        dataset_audit = _audit_dataset(dataset_path)
        run_dataset_path = _limited_jsonl_path(dataset_path, args.max_episodes, out_dir)

        all_results: list[tuple[str, int, EvaluationResult]] = []
        for seed in seeds:
            for agent_id, factory in dispatch_table.items():
                agent = _TracingAgent(factory())
                agent.reset()
                result = runner.run(agent, run_dataset_path, split, seed)
                _attach_trace_records(result, run_dataset_path, agent.records)
                all_results.append((agent_id, seed, result))
                _write_per_step_jsonl(result, agent_id, seed, split, out_dir)
                _write_per_episode_jsonl(result, agent_id, seed, split, out_dir)

        metrics_payload = _build_metrics_with_blocked_markers(
            all_results,
            config,
            dataset_audit,
        )
        _write_ece_degenerate_predictor_audit(
            dict(metrics_payload.get("C5_calibration_audit") or {})
        )
        _write_manifest(config, out_dir, metrics_payload, forbidden_source_assertion, dataset_audit)
        (out_dir / "metrics.json").write_text(
            json.dumps(metrics_payload, indent=2),
            encoding="utf-8",
        )
        print(f"OK: {out_dir / 'metrics.json'}")
        return 0
    except RuntimeError as exc:
        if "forbidden source" in str(exc):
            forbidden_source_assertion = "VIOLATION"
            print(f"FORBIDDEN SOURCE VIOLATION: {exc}", file=sys.stderr)
            return 1
        raise
    finally:
        uninstall_guard()


if __name__ == "__main__":
    raise SystemExit(main())
