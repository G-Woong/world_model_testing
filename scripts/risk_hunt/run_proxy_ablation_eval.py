"""Run STEP 10 no_state_change proxy ON/OFF ablation eval."""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from dataclasses import fields
from pathlib import Path
from typing import Any, Callable

import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from frcgw.planning.decision_gate import GateConfig


AgentFactory = Callable[[], Any]
DEFAULT_CONFIG = REPO_ROOT / "configs" / "lr_eval_step10_proxy_ablation.yaml"


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run proxy ON/OFF real-eval comparison for STEP 10."
    )
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--out-dir", default=None)
    parser.add_argument("--max-episodes", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def _load_config(path: Path) -> dict[str, Any]:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    return loaded if isinstance(loaded, dict) else {}


def _load_lr_real_module() -> Any:
    module_path = REPO_ROOT / "scripts" / "10_run_lr_real_eval.py"
    spec = importlib.util.spec_from_file_location("step10_lr_real_eval", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load real eval runner: {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _split_names(config: dict[str, Any]) -> list[str]:
    splits = config.get("splits")
    if isinstance(splits, list) and splits:
        return [str(split) for split in splits]
    return [str(config.get("split", "test_id"))]


def _dataset_path_for_split(config: dict[str, Any], split: str) -> str:
    dataset_path = Path(str(config.get("dataset_path") or config["dataset_root"]))
    if dataset_path.suffix == ".jsonl":
        return dataset_path.as_posix()
    return (dataset_path / f"{split}.jsonl").as_posix()


def _gate_config_from_spec(agent_spec: dict[str, Any]) -> GateConfig | None:
    raw_gate_config = agent_spec.get("gate_config")
    if raw_gate_config is None:
        return None
    if not isinstance(raw_gate_config, dict):
        raise TypeError(f"gate_config for {agent_spec.get('id')} must be a mapping")
    valid_fields = {field.name for field in fields(GateConfig)}
    unknown = sorted(set(raw_gate_config) - valid_fields)
    if unknown:
        raise ValueError(f"unknown GateConfig fields for {agent_spec.get('id')}: {unknown}")
    return GateConfig(**raw_gate_config)


def _build_proxy_dispatch_table(config: dict[str, Any], lr_real: Any) -> dict[str, AgentFactory]:
    dispatch: dict[str, AgentFactory] = {}
    for agent_spec in config.get("agents", []):
        agent_id = str(agent_spec["id"])
        class_name = str(agent_spec["class"])
        if class_name != "TextFRCGModelAgent":
            single_config = dict(config)
            single_config["agents"] = [agent_spec]
            dispatch[agent_id] = lr_real._build_agent_dispatch_table(single_config)[agent_id]
            continue

        def factory(spec: dict[str, Any] = agent_spec) -> Any:
            agent = lr_real.TextFRCGModelAgent(
                ckpt_path=spec.get("ckpt_path"),
                gate_config=_gate_config_from_spec(spec),
            )
            ablation_id = spec.get("ablation")
            if ablation_id:
                if ablation_id not in lr_real.ABLATION_REGISTRY:
                    raise KeyError(f"Unknown ablation for {spec['id']}: {ablation_id}")
                agent = lr_real.apply_ablation(agent, lr_real.ABLATION_REGISTRY[ablation_id])
            return agent

        dispatch[agent_id] = factory
    return dispatch


def _run_one_split(
    lr_real: Any,
    config: dict[str, Any],
    out_dir: Path,
    max_episodes: int | None,
) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "_eval_config.yaml").write_text(
        yaml.safe_dump(config, sort_keys=False),
        encoding="utf-8",
    )

    dispatch_table = _build_proxy_dispatch_table(config, lr_real)
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
    run_dataset_path = lr_real._limited_jsonl_path(dataset_path, max_episodes, out_dir)

    all_results = []
    for seed in seeds:
        for agent_id, factory in dispatch_table.items():
            agent = lr_real._TracingAgent(factory())
            agent.reset()
            result = runner.run(agent, run_dataset_path, split, seed)
            lr_real._attach_trace_records(result, run_dataset_path, agent.records)
            all_results.append((agent_id, seed, result))
            lr_real._write_per_step_jsonl(result, agent_id, seed, split, out_dir)
            lr_real._write_per_episode_jsonl(result, agent_id, seed, split, out_dir)

    metrics_payload = lr_real._build_metrics_with_blocked_markers(
        all_results,
        config,
        dataset_audit,
    )
    lr_real._write_ece_degenerate_predictor_audit(
        dict(metrics_payload.get("C5_calibration_audit") or {}),
        audit_dir=out_dir,
    )
    manifest = lr_real._write_manifest(
        config,
        out_dir,
        metrics_payload,
        "none_read",
        dataset_audit,
    )
    metrics_path = out_dir / "metrics.json"
    metrics_path.write_text(json.dumps(metrics_payload, indent=2), encoding="utf-8")
    return {
        "split": split,
        "metrics_path": metrics_path.as_posix(),
        "manifest_path": (out_dir / "manifest.json").as_posix(),
        "manifest": manifest,
        "metrics": metrics_payload,
    }


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    config_path = Path(args.config)
    config = _load_config(config_path)
    out_root = Path(args.out_dir or config.get("output_root") or config.get("out_dir"))

    plan = [
        {
            "agent_id": str(agent["id"]),
            "use_no_state_change_proxy": _gate_config_from_spec(agent).use_no_state_change_proxy
            if agent.get("gate_config") is not None
            else True,
        }
        for agent in config.get("agents", [])
    ]
    if args.dry_run:
        print(json.dumps({"config": str(config_path), "dispatch": plan}, indent=2))
        return 0

    lr_real = _load_lr_real_module()
    summaries = []
    for split in _split_names(config):
        split_config = dict(config)
        split_config["split"] = split
        split_config["dataset_path"] = _dataset_path_for_split(config, split)
        split_config["out_dir"] = (out_root / split).as_posix()
        max_episodes = args.max_episodes if args.max_episodes is not None else config.get("max_episodes")
        summaries.append(_run_one_split(lr_real, split_config, out_root / split, max_episodes))

    out_root.mkdir(parents=True, exist_ok=True)
    summary_path = out_root / "proxy_ablation_summary.json"
    summary_path.write_text(json.dumps({"splits": summaries}, indent=2), encoding="utf-8")
    print(f"OK: {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
