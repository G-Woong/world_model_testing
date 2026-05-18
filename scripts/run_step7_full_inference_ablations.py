"""Run STEP 7 inference-time ablations with ABL-040 isolated.

The default interface is:

python scripts/run_step7_full_inference_ablations.py \
  --config configs/lr_eval_real_v0_3_step7_full.yaml \
  --checkpoint outputs/checkpoints/pretrain_v0_3_falsification/checkpoint_best.pt \
  --out-dir outputs/runs/p3_lr_real_eval_step7_ablations

Use --dry-run to write only the STEP 7 manifest and print the dispatch plan.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


DEFERRED_ABLATIONS = ["ABL-001", "ABL-003", "ABL-015"]
DEFERRED_REASON = "training-time ablations require faithful retrain (STEP 8)"


@dataclass(frozen=True)
class Step7AblationSpec:
    abl_id: str
    registry_ablation: str
    description: str
    expected_collapse: str
    positive_control: bool = False


EXECUTED_ABLATIONS: tuple[Step7AblationSpec, ...] = (
    Step7AblationSpec(
        "ABL-006",
        "collapsed_latent",
        "collapsed latent",
        "falsification_precision_recall_f1 decrease",
    ),
    Step7AblationSpec(
        "ABL-011",
        "no_rollout",
        "no rollout",
        "alternative_rollout_fidelity decrease",
    ),
    Step7AblationSpec(
        "ABL-017",
        "random_alternative",
        "random alternative",
        "task_success_rate decrease",
    ),
    Step7AblationSpec(
        "ABL-022",
        "no_falsification_score_gate",
        "classifier variant A",
        "falsification_precision_recall_f1 change",
    ),
    Step7AblationSpec(
        "ABL-023",
        "uncertainty_instead_of_falsification",
        "uncertainty instead of falsification",
        "false_planning_call_rate increase",
    ),
    Step7AblationSpec(
        "ABL-024",
        "no_alternative_hypothesis",
        "no alternative hypothesis",
        "task_success_rate decrease",
    ),
    Step7AblationSpec(
        "ABL-033",
        "no_rewrite",
        "no rewrite",
        "task_success_rate decrease",
    ),
    Step7AblationSpec(
        "ABL-034",
        "no_progress_reward",
        "no progress/reward",
        "progress_per_compute decrease",
    ),
    Step7AblationSpec(
        "ABL-035",
        "always_plan_no_gate",
        "no compute gate (soft)",
        "false_planning_call_rate increase",
    ),
    Step7AblationSpec(
        "ABL-036",
        "no_compute_gate",
        "no compute gate",
        "false_planning_call_rate increase",
    ),
    Step7AblationSpec(
        "ABL-025",
        "random_alternative",
        "random alternative hypothesis selection",
        "falsification_precision decrease, recovery_delay increase",
    ),
    Step7AblationSpec(
        "ABL-026",
        "no_rollout",
        "no short rollout before rewrite",
        "alternative_rollout_fidelity decrease",
    ),
)

POSITIVE_CONTROL_ABLATIONS: tuple[Step7AblationSpec, ...] = (
    Step7AblationSpec(
        "ABL-040",
        "leakage_sanity_probe",
        "oracle leakage positive control",
        "task_success_rate artificially high",
        positive_control=True,
    ),
)

DEFAULT_METRICS = [
    "task_success_rate",
    "normalized_return",
    "falsification_precision_recall",
    "falsification_calibration",
    "progress_per_compute",
    "false_planning_call_rate",
    "failed_action_repetition_rate",
    "wrong_control_grammar_persistence",
    "wrong_grammar_persistence_v1",
    "recovery_delay",
    "action_switch_delay",
    "alternative_rollout_fidelity",
]

DEFAULT_FORBIDDEN_SOURCES = [
    "outputs/runs/p3_lr_smoke/metrics.json",
    "outputs/runs/p3_ablations/ablation_results.json",
    "outputs/runs/p3_lr_eval/metrics.json",
    "outputs/runs/p3_lr_real_eval/metrics.json",
    "outputs/runs/p3_lr_real_eval_smoke/metrics.json",
    "outputs/runs/p3_lr_real_eval_step4_smoke/metrics.json",
    "outputs/runs/p3_lr_real_eval_step5_trained_smoke/metrics.json",
]


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run STEP 7 full inference-time ablations."
    )
    parser.add_argument("--config", required=True)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--max-episodes",
        type=int,
        default=None,
        help="Optional debug cap passed to the underlying eval loop.",
    )
    return parser.parse_args(argv)


def _load_config(path: Path) -> dict[str, Any]:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    return loaded if isinstance(loaded, dict) else {}


def _repo_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _split_names(config: dict[str, Any]) -> list[str]:
    splits = config.get("splits")
    if isinstance(splits, list) and splits:
        return [str(split) for split in splits]
    return [str(config.get("split", "test_id"))]


def _dataset_path_for_split(config: dict[str, Any], split: str) -> str:
    if config.get("dataset_path"):
        dataset_path = Path(str(config["dataset_path"]))
        # If it's a directory, construct {dir}/{split}.jsonl
        if dataset_path.is_dir():
            return (dataset_path / f"{split}.jsonl").as_posix()
        # If it's already a specific JSONL file, use as-is (single-split config)
        if dataset_path.suffix == ".jsonl":
            return dataset_path.as_posix()
        # Fallback: treat as directory
        return (dataset_path / f"{split}.jsonl").as_posix()

    dataset_root = Path(str(config.get("dataset_root", "data/frcgw_text/v0_3")))
    return (dataset_root / f"{split}.jsonl").as_posix()


def _build_manifest(
    *,
    config_path: str,
    checkpoint: str,
    dry_run: bool,
) -> dict[str, Any]:
    return {
        "step": "step7",
        "executed_ablations": [spec.abl_id for spec in EXECUTED_ABLATIONS],
        "positive_control_isolated": [
            spec.abl_id for spec in POSITIVE_CONTROL_ABLATIONS
        ],
        "deferred_ablations": list(DEFERRED_ABLATIONS),
        "deferred_reason": DEFERRED_REASON,
        "fake_metric_count": 0,
        "checkpoint": checkpoint,
        "config": config_path,
        "dry_run": dry_run,
    }


def _validate_manifest(manifest: dict[str, Any]) -> None:
    executed = set(manifest.get("executed_ablations", []))
    positive = set(manifest.get("positive_control_isolated", []))
    deferred = set(manifest.get("deferred_ablations", []))

    if executed.intersection(deferred):
        overlap = sorted(executed.intersection(deferred))
        raise RuntimeError(f"Deferred ablations cannot be executed: {overlap}")
    if "ABL-040" not in positive:
        raise RuntimeError("ABL-040 must be isolated in positive_control_isolated")
    if "ABL-040" in executed:
        raise RuntimeError("ABL-040 must not be in executed_ablations")


def _write_manifest(out_dir: Path, manifest: dict[str, Any]) -> Path:
    _validate_manifest(manifest)
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = out_dir / "step7_ablation_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest_path


def _print_plan(manifest: dict[str, Any]) -> None:
    print("STEP 7 ablation dispatch plan")
    print("Executed performance ablations:")
    for spec in EXECUTED_ABLATIONS:
        print(
            f"  - {spec.abl_id}: {spec.description} "
            f"(registry={spec.registry_ablation})"
        )
    print("Positive control isolated:")
    for spec in POSITIVE_CONTROL_ABLATIONS:
        print(
            f"  - {spec.abl_id}: {spec.description} "
            f"(registry={spec.registry_ablation}, result_group=positive_control_results)"
        )
    print("Deferred to STEP 8 faithful retrain:")
    for abl_id in manifest["deferred_ablations"]:
        print(f"  - {abl_id}: deferred ({manifest['deferred_reason']})")


def _load_lr_real_module() -> Any:
    module_path = REPO_ROOT / "scripts" / "10_run_lr_real_eval.py"
    spec = importlib.util.spec_from_file_location("step7_lr_real_eval", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load real eval runner: {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _real_eval_config(
    base_config: dict[str, Any],
    spec: Step7AblationSpec,
    split: str,
    checkpoint: str,
    run_dir: Path,
) -> dict[str, Any]:
    return {
        "run_mode": "real_episode_eval",
        "dataset_path": _dataset_path_for_split(base_config, split),
        "split": split,
        "seeds": list(base_config.get("seeds") or [0]),
        "out_dir": run_dir.as_posix(),
        "agents": [
            {
                "id": spec.abl_id,
                "class": "TextFRCGModelAgent",
                "ablation": spec.registry_ablation,
                "ckpt_path": checkpoint,
            }
        ],
        "metrics": list(base_config.get("metrics") or DEFAULT_METRICS),
        "compute_budget": dict(base_config.get("compute_budget") or {}),
        "forbidden_sources": list(
            base_config.get("forbidden_sources") or DEFAULT_FORBIDDEN_SOURCES
        ),
    }


def _run_one_split(
    lr_real: Any,
    config: dict[str, Any],
    run_dir: Path,
    max_episodes: int | None,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "_eval_config.yaml").write_text(
        yaml.safe_dump(config, sort_keys=False),
        encoding="utf-8",
    )

    dispatch_table = lr_real._build_agent_dispatch_table(config)
    lr_real._preflight_dry_obs_check(dispatch_table)

    dataset_path = str(config["dataset_path"])
    split = str(config.get("split", "test_id"))
    seeds = list(config.get("seeds", [0]))
    runner_config = {
        "seeds": seeds,
        "split": split,
        "metrics": config.get("metrics", []),
        "compute_budget": config.get("compute_budget", {}),
    }
    runner = lr_real.EvaluationRunner(runner_config)
    dataset_audit = lr_real._audit_dataset(dataset_path)
    run_dataset_path = lr_real._limited_jsonl_path(dataset_path, max_episodes, run_dir)

    all_results = []
    for seed in seeds:
        for agent_id, factory in dispatch_table.items():
            agent = lr_real._TracingAgent(factory())
            agent.reset()
            result = runner.run(agent, run_dataset_path, split, seed)
            lr_real._attach_trace_records(result, run_dataset_path, agent.records)
            all_results.append((agent_id, seed, result))
            lr_real._write_per_step_jsonl(result, agent_id, seed, split, run_dir)
            lr_real._write_per_episode_jsonl(result, agent_id, seed, split, run_dir)

    metrics_payload = lr_real._build_metrics_with_blocked_markers(
        all_results,
        config,
        dataset_audit,
    )
    lr_real._write_ece_degenerate_predictor_audit(
        dict(metrics_payload.get("C5_calibration_audit") or {}),
        audit_dir=run_dir,
    )
    manifest = lr_real._write_manifest(
        config,
        run_dir,
        metrics_payload,
        "none_read",
        dataset_audit,
    )
    metrics_path = run_dir / "metrics.json"
    metrics_path.write_text(json.dumps(metrics_payload, indent=2), encoding="utf-8")

    return {
        "split": split,
        "metrics_path": _repo_relative(metrics_path),
        "manifest_path": _repo_relative(run_dir / "manifest.json"),
        "metrics": metrics_payload,
        "manifest": manifest,
    }


def _result_dir(out_dir: Path, spec: Step7AblationSpec) -> Path:
    if spec.positive_control:
        return out_dir / "positive_control_results" / spec.abl_id
    return out_dir / spec.abl_id


def _run_ablation(
    lr_real: Any,
    base_config: dict[str, Any],
    spec: Step7AblationSpec,
    checkpoint: str,
    out_dir: Path,
    max_episodes: int | None,
) -> dict[str, Any]:
    result_dir = _result_dir(out_dir, spec)
    split_payloads = []
    fake_metric_count = 0

    for split in _split_names(base_config):
        split_dir = result_dir / split
        eval_config = _real_eval_config(base_config, spec, split, checkpoint, split_dir)
        split_payload = _run_one_split(lr_real, eval_config, split_dir, max_episodes)
        split_payloads.append(split_payload)
        fake_metric_count += int(split_payload["metrics"].get("fake_metric_count", 0))

    result_payload = {
        "ablation_id": spec.abl_id,
        "registry_ablation": spec.registry_ablation,
        "description": spec.description,
        "expected_collapse": spec.expected_collapse,
        "positive_control": spec.positive_control,
        "fake_metric_count": fake_metric_count,
        "splits": split_payloads,
    }
    result_path = result_dir / "results.json"
    result_path.write_text(json.dumps(result_payload, indent=2), encoding="utf-8")
    return {
        "ablation_id": spec.abl_id,
        "result_path": _repo_relative(result_path),
        "fake_metric_count": fake_metric_count,
    }


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    config_path = Path(args.config)
    base_config = _load_config(config_path)
    out_dir = Path(args.out_dir)

    manifest = _build_manifest(
        config_path=args.config,
        checkpoint=args.checkpoint,
        dry_run=bool(args.dry_run),
    )
    manifest_path = _write_manifest(out_dir, manifest)
    _print_plan(manifest)
    print(f"Manifest written: {manifest_path}")

    if args.dry_run:
        print("Dry run only: no eval was executed.")
        return 0

    lr_real = _load_lr_real_module()
    results = []
    for spec in [*EXECUTED_ABLATIONS, *POSITIVE_CONTROL_ABLATIONS]:
        print(f"Running {spec.abl_id}: {spec.description}")
        results.append(
            _run_ablation(
                lr_real,
                base_config,
                spec,
                args.checkpoint,
                out_dir,
                args.max_episodes,
            )
        )

    manifest["dry_run"] = False
    manifest["result_files"] = results
    manifest["fake_metric_count"] = sum(int(item["fake_metric_count"]) for item in results)
    _write_manifest(out_dir, manifest)
    print(f"STEP 7 ablation run complete: {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
