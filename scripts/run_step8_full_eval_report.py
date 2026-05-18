"""Aggregate STEP 8 per-seed evaluation outputs into a full report.

This harness does not execute training or evaluation. It reads existing
``metrics.json`` files and writes aggregate JSON and Markdown summaries.
"""
from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


SUMMARY_METRICS = (
    "task_success_rate",
    "falsification_precision",
    "falsification_recall",
    "ood_shift_f1",
    "progress_per_compute",
    "false_planning_call_rate",
)

POSITIVE_CONTROL_IDS = {"ABL-040", "leakage_sanity_probe"}

INPUT_DIR_CONFIG_KEYS = (
    "step8_ablation_out_dir",
    "ablation_out_dir",
    "eval_input_dir",
    "input_dir",
    "source_dir",
)

METRIC_PATHS: dict[str, tuple[tuple[str, ...], ...]] = {
    "task_success_rate": (
        ("task_success_rate",),
    ),
    "falsification_precision": (
        ("falsification_precision",),
        ("C3_falsification_precision",),
        ("falsification_precision_recall", "precision"),
    ),
    "falsification_recall": (
        ("falsification_recall",),
        ("C3_falsification_recall",),
        ("falsification_precision_recall", "recall"),
    ),
    "ood_shift_f1": (
        ("ood_shift_f1", "f1"),
        ("ood_shift_f1",),
        ("C2_ood_shift_f1",),
        ("ood_shift", "f1"),
    ),
    "progress_per_compute": (
        ("progress_per_compute",),
        ("C6_progress_per_compute",),
    ),
    "false_planning_call_rate": (
        ("false_planning_call_rate",),
    ),
}


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Aggregate STEP 8 per-seed eval outputs into summary.json."
    )
    parser.add_argument("--config", required=True, help="YAML config used for metadata/input hints.")
    parser.add_argument("--agents", nargs="+", required=True, help="Agent IDs to aggregate.")
    parser.add_argument("--out-dir", required=True, help="Directory for summary.json and summary_human.md.")
    parser.add_argument("--seeds", nargs="+", type=int, required=True, help="Seed IDs to aggregate.")
    parser.add_argument("--splits", nargs="+", required=True, help="Split names to aggregate.")
    return parser.parse_args(argv)


def _load_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing config: {path}")
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    return loaded if isinstance(loaded, dict) else {}


def _resolve_path(path_value: str | Path, *, config_path: Path | None = None) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path
    if config_path is not None:
        config_relative = config_path.parent / path
        if config_relative.exists():
            return config_relative
    return REPO_ROOT / path


def _repo_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _input_roots(config: dict[str, Any], config_path: Path, out_dir: Path) -> list[Path]:
    roots: list[Path] = []
    for key in INPUT_DIR_CONFIG_KEYS:
        value = config.get(key)
        if value:
            roots.append(_resolve_path(str(value), config_path=config_path))

    roots.extend(
        [
            out_dir.parent / "p3_lr_real_eval_step8_ablations",
            out_dir,
            REPO_ROOT / "outputs" / "runs" / "p3_lr_real_eval_step8_ablations",
        ]
    )

    unique_roots: list[Path] = []
    seen: set[str] = set()
    for root in roots:
        key = str(root.resolve()) if root.exists() else str(root)
        if key not in seen:
            seen.add(key)
            unique_roots.append(root)
    return unique_roots


def _metrics_path_candidates(root: Path, agent_id: str, seed: int, split: str) -> list[Path]:
    return [
        root / f"{agent_id}_seed{seed}_{split}" / "metrics.json",
        root / agent_id / f"seed{seed}_{split}" / "metrics.json",
        root / agent_id / split / f"seed{seed}" / "metrics.json",
        root / agent_id / split / "metrics.json",
        root / "positive_control_results" / agent_id / split / "metrics.json",
    ]


def _find_metrics_path(
    roots: list[Path],
    agent_id: str,
    seed: int,
    split: str,
) -> Path | None:
    for root in roots:
        for candidate in _metrics_path_candidates(root, agent_id, seed, split):
            if candidate.exists():
                return candidate
    return None


def _load_metrics_payload(path: Path) -> dict[str, Any]:
    loaded = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError(f"metrics.json must contain a JSON object: {path}")
    return loaded


def _agent_metrics_payload(payload: dict[str, Any], agent_id: str) -> dict[str, Any]:
    agents_payload = payload.get("agents")
    if isinstance(agents_payload, Mapping):
        if isinstance(agents_payload.get(agent_id), dict):
            return dict(agents_payload[agent_id])
        if len(agents_payload) == 1:
            only_payload = next(iter(agents_payload.values()))
            if isinstance(only_payload, dict):
                return dict(only_payload)

    results = payload.get("results")
    if isinstance(results, list):
        fallback: dict[str, Any] | None = None
        for result in results:
            if not isinstance(result, Mapping):
                continue
            metrics = result.get("metrics")
            if isinstance(metrics, dict):
                if fallback is None:
                    fallback = dict(metrics)
                if str(result.get("agent_id")) == agent_id:
                    return dict(metrics)
        if fallback is not None and len(results) == 1:
            return fallback

    return payload


def _numeric_value(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        number = float(value)
        if math.isfinite(number):
            return number
        return None
    if isinstance(value, Mapping):
        child = value.get("value")
        if isinstance(child, bool):
            return None
        if isinstance(child, (int, float)) and math.isfinite(float(child)):
            return float(child)
    return None


def _lookup_metric(metrics_payload: dict[str, Any], path: tuple[str, ...]) -> float | None:
    current: Any = metrics_payload
    for key in path:
        if not isinstance(current, Mapping) or key not in current:
            return None
        current = current[key]
    return _numeric_value(current)


def _extract_metrics(payload: dict[str, Any], agent_id: str) -> dict[str, float]:
    metrics_payload = _agent_metrics_payload(payload, agent_id)
    extracted: dict[str, float] = {}
    for metric_name, paths in METRIC_PATHS.items():
        for path in paths:
            value = _lookup_metric(metrics_payload, path)
            if value is not None:
                extracted[metric_name] = value
                break
    return extracted


def _mean(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def _std(values: list[float]) -> float | None:
    if not values:
        return None
    if len(values) == 1:
        return 0.0
    mean_value = sum(values) / len(values)
    variance = sum((value - mean_value) ** 2 for value in values) / (len(values) - 1)
    return math.sqrt(variance)


def _summarize_values(records: list[dict[str, Any]]) -> tuple[dict[str, float | None], dict[str, float | None]]:
    values_by_metric: dict[str, list[float]] = {metric: [] for metric in SUMMARY_METRICS}
    for record in records:
        metrics = record.get("metrics")
        if not isinstance(metrics, Mapping):
            continue
        for metric in SUMMARY_METRICS:
            value = metrics.get(metric)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                values_by_metric[metric].append(float(value))
    return (
        {metric: _mean(values) for metric, values in values_by_metric.items()},
        {metric: _std(values) for metric, values in values_by_metric.items()},
    )


def _summarize_agent(
    *,
    agent_id: str,
    roots: list[Path],
    seeds: list[int],
    splits: list[str],
) -> dict[str, Any]:
    all_records: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []
    split_payloads: dict[str, dict[str, Any]] = {}

    for split in splits:
        split_records: list[dict[str, Any]] = []
        split_missing: list[dict[str, Any]] = []
        for seed in seeds:
            metrics_path = _find_metrics_path(roots, agent_id, seed, split)
            if metrics_path is None:
                missing_record = {
                    "seed": seed,
                    "split": split,
                    "reason": "missing_metrics_json",
                }
                missing.append(missing_record)
                split_missing.append(missing_record)
                continue

            try:
                payload = _load_metrics_payload(metrics_path)
                metrics = _extract_metrics(payload, agent_id)
            except (OSError, ValueError, json.JSONDecodeError) as exc:
                missing_record = {
                    "seed": seed,
                    "split": split,
                    "path": _repo_relative(metrics_path),
                    "reason": f"unreadable_metrics_json:{exc.__class__.__name__}",
                }
                missing.append(missing_record)
                split_missing.append(missing_record)
                continue

            record = {
                "seed": seed,
                "split": split,
                "path": _repo_relative(metrics_path),
                "metrics": metrics,
            }
            all_records.append(record)
            split_records.append(record)

        split_mean, split_std = _summarize_values(split_records)
        split_payloads[split] = {
            "mean": split_mean,
            "std": split_std,
            "n_seeds": len({record["seed"] for record in split_records}),
            "n_expected": len(seeds),
            "count_missing": len(split_missing),
            "missing": split_missing,
        }

    mean_payload, std_payload = _summarize_values(all_records)
    return {
        "mean": mean_payload,
        "std": std_payload,
        "n_seeds": len(seeds),
        "n_observed": len(all_records),
        "n_expected": len(seeds) * len(splits),
        "count_missing": len(missing),
        "missing": missing,
        "splits": split_payloads,
    }


def _current_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "unknown"


def build_summary(
    *,
    config_path: Path,
    config: dict[str, Any],
    agents: list[str],
    out_dir: Path,
    seeds: list[int],
    splits: list[str],
) -> dict[str, Any]:
    roots = _input_roots(config, config_path, out_dir)
    summary: dict[str, Any] = {
        "agents": {},
        "positive_control": {},
        "metadata": {
            "config": _repo_relative(config_path),
            "config_content": config,
            "timestamp": datetime.now(UTC).isoformat(),
            "commit": _current_commit(),
            "seeds": seeds,
            "splits": splits,
            "input_roots": [_repo_relative(root) for root in roots],
            "summary_metrics": list(SUMMARY_METRICS),
        },
    }

    for agent_id in agents:
        agent_summary = _summarize_agent(
            agent_id=agent_id,
            roots=roots,
            seeds=seeds,
            splits=splits,
        )
        if agent_id in POSITIVE_CONTROL_IDS:
            summary["positive_control"][agent_id] = agent_summary
        else:
            summary["agents"][agent_id] = agent_summary
    return summary


def _format_float(value: Any) -> str:
    if value is None:
        return "NA"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return f"{float(value):.6g}"
    return str(value)


def _human_table(summary: dict[str, Any]) -> str:
    rows = [
        "# STEP 8 Full Evaluation Summary",
        "",
        f"commit: {summary['metadata'].get('commit', 'unknown')}",
        f"timestamp: {summary['metadata'].get('timestamp', 'unknown')}",
        "",
        "| group | agent | n_observed | count_missing | task_success_rate | falsification_precision | falsification_recall | ood_shift_f1 | progress_per_compute | false_planning_call_rate |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]

    def append_group(group_name: str, agents: Mapping[str, Any]) -> None:
        for agent_id, payload in agents.items():
            mean_payload = payload.get("mean", {})
            std_payload = payload.get("std", {})
            metric_cells = []
            for metric in SUMMARY_METRICS:
                mean_value = _format_float(mean_payload.get(metric))
                std_value = _format_float(std_payload.get(metric))
                metric_cells.append(f"{mean_value} +/- {std_value}")
            rows.append(
                "| "
                + " | ".join(
                    [
                        group_name,
                        str(agent_id),
                        str(payload.get("n_observed", 0)),
                        str(payload.get("count_missing", 0)),
                        *metric_cells,
                    ]
                )
                + " |"
            )

    append_group("agents", summary.get("agents", {}))
    append_group("positive_control", summary.get("positive_control", {}))
    rows.append("")
    return "\n".join(rows)


def write_summary(summary: dict[str, Any], out_dir: Path) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    summary_path = out_dir / "summary.json"
    human_path = out_dir / "summary_human.md"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    human_path.write_text(_human_table(summary), encoding="utf-8")
    return summary_path, human_path


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    config_path = _resolve_path(args.config)
    out_dir = _resolve_path(args.out_dir)
    config = _load_config(config_path)
    summary = build_summary(
        config_path=config_path,
        config=config,
        agents=[str(agent) for agent in args.agents],
        out_dir=out_dir,
        seeds=list(args.seeds),
        splits=[str(split) for split in args.splits],
    )
    summary_path, human_path = write_summary(summary, out_dir)
    print(f"Wrote {summary_path}")
    print(f"Wrote {human_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
