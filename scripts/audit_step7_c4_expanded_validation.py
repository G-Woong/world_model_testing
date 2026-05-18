"""Aggregate STEP 7 C4 expanded validation metrics.

This script is intentionally read-only with respect to evaluation runs. It
looks for per-(seed, split, agent) metrics.json files under the STEP 7
``output_root`` and writes one audit JSON to ``--out``.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = "configs/lr_eval_real_v0_3_step7_full.yaml"
DEFAULT_OUT = "outputs/audits/step7_c4_expanded_validation.json"
DEFAULT_OUTPUT_ROOT = "outputs/runs/p3_lr_real_eval_step7_full"

READY_MEAN_THRESHOLD = 0.7
READY_STD_THRESHOLD = 0.15
ABLATION_DELTA_THRESHOLD = 0.05
PRELIMINARY_MEAN_THRESHOLD = 0.5

_FORBIDDEN_OUT_NAMES = {
    "step4_lr_comparison.json",
    "step5_lr_reconciliation.json",
    "step6_lr_reconciliation.json",
}


def _repo_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _load_config(config_path: Path) -> dict[str, Any]:
    if not config_path.exists():
        return {}
    text = config_path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore

        loaded = yaml.safe_load(text)
        return loaded if isinstance(loaded, dict) else {}
    except Exception:
        config: dict[str, Any] = {}
        for line in text.splitlines():
            clean = line.split("#", 1)[0].strip()
            if not clean or ":" not in clean:
                continue
            key, value = clean.split(":", 1)
            value = value.strip()
            if key and value:
                config[key.strip()] = value
        return config


def _mean(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def _std(values: list[float]) -> float | None:
    if not values:
        return None
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / len(values)
    return math.sqrt(variance)


def _numeric(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, dict):
        return _numeric(value.get("value"))
    return None


def _count_key(payload: Any, key_name: str) -> int:
    if isinstance(payload, dict):
        total = 0
        for key, value in payload.items():
            if key == key_name:
                total += 1
            total += _count_key(value, key_name)
        return total
    if isinstance(payload, list):
        return sum(_count_key(item, key_name) for item in payload)
    return 0


def _extract_task_success_rate(payload: dict[str, Any], agent: str) -> float | None:
    if isinstance(payload.get("agents"), dict):
        agent_payload = payload["agents"].get(agent)
        if isinstance(agent_payload, dict):
            direct = _numeric(agent_payload.get("task_success_rate"))
            if direct is not None:
                return direct

    if isinstance(payload.get("metrics"), dict):
        direct = _numeric(payload["metrics"].get("task_success_rate"))
        if direct is not None:
            return direct

    return _numeric(payload.get("task_success_rate"))


def _safe_json_load(path: Path) -> dict[str, Any] | None:
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return loaded if isinstance(loaded, dict) else None


def _path_matches(path: Path, split: str, agent: str, seed: int) -> bool:
    normalized = path.as_posix().lower()
    agent_token = agent.lower()
    seed_tokens = (f"seed{seed}", f"seed_{seed}", f"seed={seed}")
    return (
        split.lower() in normalized
        and agent_token in normalized
        and any(token in normalized for token in seed_tokens)
    )


def _candidate_metric_paths(output_root: Path, split: str, agent: str, seed: int) -> list[Path]:
    agent_dir = agent.replace("/", "_")
    exact = [
        output_root / split / agent_dir / f"seed_{seed}" / "metrics.json",
        output_root / split / agent_dir / f"seed{seed}" / "metrics.json",
        output_root / split / f"{agent_dir}_seed_{seed}" / "metrics.json",
        output_root / split / f"{agent_dir}_seed{seed}" / "metrics.json",
        output_root / agent_dir / split / f"seed_{seed}" / "metrics.json",
        output_root / agent_dir / split / f"seed{seed}" / "metrics.json",
        output_root / f"seed_{seed}" / split / agent_dir / "metrics.json",
        output_root / f"seed{seed}" / split / agent_dir / "metrics.json",
        output_root / split / f"seed_{seed}" / agent_dir / "metrics.json",
        output_root / split / f"seed{seed}" / agent_dir / "metrics.json",
        output_root / f"{split}_{agent_dir}_seed_{seed}" / "metrics.json",
        output_root / f"{split}_{agent_dir}_seed{seed}" / "metrics.json",
    ]
    seen: set[Path] = set()
    candidates: list[Path] = []
    for path in exact:
        if path not in seen:
            seen.add(path)
            candidates.append(path)

    if output_root.exists():
        for path in output_root.rglob("metrics.json"):
            if path not in seen and _path_matches(path, split, agent_dir, seed):
                seen.add(path)
                candidates.append(path)
    return candidates


def _read_metric_for_combo(
    output_root: Path,
    split: str,
    agent: str,
    seed: int,
) -> tuple[float | None, Path | None, int]:
    fake_metric_count = 0
    for path in _candidate_metric_paths(output_root, split, agent, seed):
        if not path.exists():
            continue
        payload = _safe_json_load(path)
        if payload is None:
            continue
        fake_metric_count += _count_key(payload, "fake_metric")
        value = _extract_task_success_rate(payload, agent)
        if value is not None:
            return value, path, fake_metric_count
    return None, None, fake_metric_count


def _aggregate_agent(
    output_root: Path,
    split: str,
    agent: str,
    seeds: list[int],
) -> tuple[dict[str, Any], int, int]:
    raw: list[dict[str, Any]] = []
    fake_metric_count = 0
    missing = 0
    values: list[float] = []

    for seed in seeds:
        value, path, fake_count = _read_metric_for_combo(output_root, split, agent, seed)
        fake_metric_count += fake_count
        if value is None or path is None:
            missing += 1
            continue
        values.append(value)
        raw.append(
            {
                "seed": seed,
                "task_success_rate": value,
                "metrics_path": _repo_relative(path),
            }
        )

    return (
        {
            "mean_task_success_rate": _mean(values),
            "std_task_success_rate": _std(values),
            "n_seeds": len(values),
            "raw": raw,
        },
        missing,
        fake_metric_count,
    )


def _delta(a: float | None, b: float | None) -> float | None:
    if a is None or b is None:
        return None
    return a - b


def determine_c4_status(
    frcg_lr_means: list[float],
    abl024_means: list[float],
    abl036_means: list[float],
    *,
    incomplete: bool = False,
) -> dict[str, Any]:
    """Return STEP 7 C4 status for FRCG-LR vs required ablations."""
    if incomplete or not frcg_lr_means:
        return {
            "c4_status": "INCOMPLETE",
            "c4_status_reason": "Missing STEP 7 C4 result files.",
        }

    frcg_mean = _mean(frcg_lr_means)
    frcg_std = _std(frcg_lr_means)
    abl024_mean = _mean(abl024_means)
    abl036_mean = _mean(abl036_means)

    if frcg_mean is None or frcg_std is None or abl024_mean is None or abl036_mean is None:
        return {
            "c4_status": "INCOMPLETE",
            "c4_status_reason": "Missing FRCG-LR or ablation means for C4 comparison.",
        }

    delta_024 = frcg_mean - abl024_mean
    delta_036 = frcg_mean - abl036_mean

    if frcg_mean <= PRELIMINARY_MEAN_THRESHOLD:
        return {
            "c4_status": "DOWNSHIFT",
            "c4_status_reason": (
                "FRCG-LR mean_task_success_rate did not exceed the preliminary threshold."
            ),
        }

    ready = (
        frcg_mean > READY_MEAN_THRESHOLD
        and frcg_std < READY_STD_THRESHOLD
        and delta_024 > ABLATION_DELTA_THRESHOLD
        and delta_036 > ABLATION_DELTA_THRESHOLD
    )
    if ready:
        return {
            "c4_status": "READY_FOR_REPORT",
            "c4_status_reason": (
                "FRCG-LR mean/std and ablation deltas satisfy STEP 7 C4 criteria."
            ),
        }

    return {
        "c4_status": "PRELIMINARY",
        "c4_status_reason": "FRCG-LR mean > 0.5 but one or more C4 criteria are unmet.",
    }


def build_audit(
    config: str,
    seeds: list[int],
    splits: list[str],
    agents: list[str],
) -> dict[str, Any]:
    config_path = (REPO_ROOT / config).resolve() if not Path(config).is_absolute() else Path(config)
    config_payload = _load_config(config_path)
    output_root = Path(str(config_payload.get("output_root", DEFAULT_OUTPUT_ROOT)))
    if not output_root.is_absolute():
        output_root = REPO_ROOT / output_root

    results: dict[str, dict[str, Any]] = {}
    fake_metric_count = 0
    missing_count = 0
    expected_count = len(seeds) * len(splits) * len(agents)

    for split in splits:
        results[split] = {}
        for agent in agents:
            aggregate, missing, fake_count = _aggregate_agent(output_root, split, agent, seeds)
            results[split][agent] = aggregate
            missing_count += missing
            fake_metric_count += fake_count

    focus_split = "test_id" if "test_id" in results else splits[0]
    focus_results = results.get(focus_split, {})
    frcg_raw = [
        float(row["task_success_rate"])
        for row in focus_results.get("FRCG-LR", {}).get("raw", [])
    ]
    abl024_raw = [
        float(row["task_success_rate"])
        for row in focus_results.get("ABL-024", {}).get("raw", [])
    ]
    abl036_raw = [
        float(row["task_success_rate"])
        for row in focus_results.get("ABL-036", {}).get("raw", [])
    ]

    status = determine_c4_status(
        frcg_lr_means=frcg_raw,
        abl024_means=abl024_raw,
        abl036_means=abl036_raw,
        incomplete=missing_count > 0,
    )
    if status["c4_status"] == "INCOMPLETE":
        status["c4_status_reason"] = (
            f"Missing {missing_count} of {expected_count} expected STEP 7 C4 metric files."
        )

    comparison_delta: dict[str, float | None] = {}
    for split in splits:
        split_results = results.get(split, {})
        frcg_mean = split_results.get("FRCG-LR", {}).get("mean_task_success_rate")
        for ablation in ("ABL-024", "ABL-036"):
            ablation_mean = split_results.get(ablation, {}).get("mean_task_success_rate")
            comparison_delta[f"FRCG-LR_vs_{ablation}_{split}"] = _delta(frcg_mean, ablation_mean)

    return {
        "step": "step7",
        "config": config,
        "seeds": seeds,
        "splits": splits,
        "agents": agents,
        "results": results,
        "c4_status": status["c4_status"],
        "c4_status_reason": status["c4_status_reason"],
        "fake_metric_count": fake_metric_count,
        "comparison_delta": comparison_delta,
    }


def _write_audit(audit: dict[str, Any], out_path: Path) -> None:
    if out_path.name in _FORBIDDEN_OUT_NAMES:
        raise ValueError(f"Refusing to overwrite protected audit file: {out_path}")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(audit, indent=2, sort_keys=True), encoding="utf-8")


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Aggregate STEP 7 C4 expanded validation results.")
    parser.add_argument("--config", default=DEFAULT_CONFIG)
    parser.add_argument("--seeds", nargs="+", type=int, default=[0, 1, 2, 3, 4])
    parser.add_argument("--splits", nargs="+", default=["test_id", "test_ood"])
    parser.add_argument("--agents", nargs="+", default=["FRCG-LR", "ABL-024", "ABL-036"])
    parser.add_argument("--out", default=DEFAULT_OUT)
    parser.add_argument(
        "--incomplete-ok",
        action="store_true",
        help="Write INCOMPLETE audits without returning a non-zero exit code.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    audit = build_audit(
        config=args.config,
        seeds=list(args.seeds),
        splits=list(args.splits),
        agents=list(args.agents),
    )
    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = REPO_ROOT / out_path
    _write_audit(audit, out_path)
    print(f"STEP 7 C4 audit: {_repo_relative(out_path)}")
    print(f"  c4_status: {audit['c4_status']}")
    print(f"  fake_metric_count: {audit['fake_metric_count']}")
    if audit["c4_status"] == "INCOMPLETE" and not args.incomplete_ok:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
