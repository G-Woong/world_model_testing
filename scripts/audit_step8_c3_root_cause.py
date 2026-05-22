"""Step 8 C3 root-cause audit for F_t trace degeneracy.

The audit consumes per-step eval traces when available. If no eval trace
directory is provided, it can run a lightweight public-observation-only pass
over the dataset with TextFRCGModelAgent.
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


DEFAULT_OUT = "outputs/audits/step8_c3_root_cause_audit.json"
SHORT_CIRCUIT_EFFECT_TYPES = frozenset({"none", "no_state_change"})


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def _trace_paths(eval_dir: Path) -> list[Path]:
    if eval_dir.is_file():
        return [eval_dir]
    per_step_dir = eval_dir / "per_step"
    candidates = list(per_step_dir.glob("*.jsonl")) if per_step_dir.exists() else []
    candidates.extend(path for path in eval_dir.glob("*.jsonl") if path not in candidates)
    return sorted(candidates)


def _records_from_eval_dir(eval_dir: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in _trace_paths(eval_dir):
        records.extend(_load_jsonl(path))
    return records


def _coerce_float(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _coerce_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if value is None:
        return None
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered == "true":
            return True
        if lowered == "false":
            return False
    return None


def _variance(values: list[float]) -> float:
    return statistics.pvariance(values) if values else 0.0


def _public_observation_from_raw(raw: dict[str, Any]) -> Any:
    from frcgw.schemas.step_schema import CandidateAction, PublicHistoryItem, PublicObservation

    history = [
        PublicHistoryItem(
            step_index=int(item.get("step_index", index)),
            action_summary=str(item.get("action_summary", "")),
            effect_summary=item.get("effect_summary"),
        )
        for index, item in enumerate(raw.get("history_public") or [])
        if isinstance(item, dict)
    ]
    candidates = [
        CandidateAction(
            action_id=str(item.get("action_id", f"candidate_{index}")),
            action_type=str(item.get("action_type", "noop")),
            action_params=dict(item.get("action_params") or {}),
        )
        for index, item in enumerate(raw.get("candidate_actions_public") or [])
        if isinstance(item, dict)
    ]
    return PublicObservation(
        instruction=str(raw.get("instruction", "")),
        dom_snapshot_public=raw.get("dom_snapshot_public"),
        accessibility_tree_public=raw.get("accessibility_tree_public"),
        history_public=history,
        candidate_actions_public=candidates,
    )


def _last_effect_type_from_obs(obs: Any) -> str:
    if not obs.history_public:
        return "none"
    return str(obs.history_public[-1].effect_summary or "none")


def _current_h_exec_id(agent: Any, step_idx: int) -> int:
    planner_state = getattr(agent, "_planner_state", None)
    get_current = getattr(planner_state, "get_current", None)
    if callable(get_current):
        return int(get_current(step_idx))
    return 0


def _records_from_direct_inference(
    dataset: Path,
    checkpoint: Path | None,
) -> list[dict[str, Any]]:
    from frcgw.evaluation.frcg_agent import TextFRCGModelAgent

    agent = TextFRCGModelAgent(ckpt_path=checkpoint if checkpoint else None)
    records: list[dict[str, Any]] = []
    for episode in _load_jsonl(dataset):
        episode_id = str(episode.get("episode_id", f"episode_{len(records)}"))
        for fallback_idx, step in enumerate(episode.get("steps") or []):
            if not isinstance(step, dict):
                continue
            public_raw = dict(step.get("public_observation") or step.get("public_input") or {})
            obs = _public_observation_from_raw(public_raw)
            step_idx = int(step.get("step_index", fallback_idx))
            h_exec_id = _current_h_exec_id(agent, step_idx)
            agent.act(obs)
            F_t = _coerce_float(getattr(agent, "last_F_t", 0.0))
            records.append(
                {
                    "episode_id": episode_id,
                    "step_index": step_idx,
                    "planner_F_t": F_t,
                    "lr_scorer_F_t": F_t,
                    "effect_type": _last_effect_type_from_obs(obs),
                    "predicted_wrong": getattr(agent, "last_predicted_wrong", None),
                    "wrong_prob": _coerce_float(getattr(agent, "last_wrong_prob", 0.0)),
                    "h_exec_id": h_exec_id,
                    "h_alt_best_id": None,
                    "degenerate_reason": None,
                }
            )
    return records


def _record_float(record: dict[str, Any], *keys: str) -> float:
    for key in keys:
        if key in record and record.get(key) is not None:
            return _coerce_float(record.get(key))
    return 0.0


def _record_effect_type(record: dict[str, Any]) -> str:
    value = record.get("effect_type")
    if value is None:
        value = record.get("observed_effect_type")
    return str(value or "none")


def _degenerate_reason(
    planner_variance: float,
    lr_scorer_variance: float,
    mapping_coverage: float,
    n_steps: int,
) -> str:
    both_zero = planner_variance < 1e-6 and lr_scorer_variance < 1e-6
    if n_steps == 0:
        return "model_untrained"
    if mapping_coverage < 0.05:
        return "zero_short_circuit"
    if both_zero and mapping_coverage >= 0.05:
        return "mapping_miss"
    if both_zero:
        return "both_traces_zero"
    return "non_degenerate"


def _c3_status(
    planner_variance: float,
    lr_scorer_variance: float,
    predicted_wrong_class_counts: dict[str, int],
    degenerate_reason: str,
) -> str:
    max_variance = max(planner_variance, lr_scorer_variance)
    both_classes_present = (
        predicted_wrong_class_counts["true_count"] > 0
        and predicted_wrong_class_counts["false_count"] > 0
    )
    one_class_present = (
        predicted_wrong_class_counts["true_count"] > 0
        or predicted_wrong_class_counts["false_count"] > 0
    )
    if degenerate_reason != "non_degenerate":
        return "BLOCKED"
    if max_variance > 0.01 and both_classes_present:
        return "READY_CANDIDATE"
    if max_variance > 1e-6 or one_class_present:
        return "PRELIMINARY_PLUS"
    return "BLOCKED"


def build_audit(records: list[dict[str, Any]], source: str) -> dict[str, Any]:
    planner_values = [
        _record_float(record, "planner_F_t", "F_t_planner", "f_t", "F_t")
        for record in records
    ]
    lr_scorer_values = [
        _record_float(record, "lr_scorer_F_t", "F_t_lr_scorer", "f_t", "F_t")
        for record in records
    ]
    planner_variance = _variance(planner_values)
    lr_scorer_variance = _variance(lr_scorer_values)

    bool_counts = Counter(
        value
        for value in (_coerce_bool(record.get("predicted_wrong")) for record in records)
        if value is not None
    )
    predicted_wrong_class_counts = {
        "true_count": int(bool_counts[True]),
        "false_count": int(bool_counts[False]),
    }

    effects = [_record_effect_type(record) for record in records]
    effect_type_distribution = dict(sorted(Counter(effects).items()))
    mapping_coverage = (
        sum(1 for effect in effects if effect not in SHORT_CIRCUIT_EFFECT_TYPES)
        / len(effects)
        if effects
        else 0.0
    )
    reason = _degenerate_reason(
        planner_variance,
        lr_scorer_variance,
        mapping_coverage,
        len(records),
    )
    c3_status = _c3_status(
        planner_variance,
        lr_scorer_variance,
        predicted_wrong_class_counts,
        reason,
    )

    return {
        "source": source,
        "n_steps": len(records),
        "planner_F_t_variance": planner_variance,
        "lr_scorer_F_t_variance": lr_scorer_variance,
        "predicted_wrong_class_counts": predicted_wrong_class_counts,
        "predicted_wrong_diversity": sum(
            1 for count in predicted_wrong_class_counts.values() if count > 0
        ),
        "effect_type_distribution": effect_type_distribution,
        "mapping_coverage": mapping_coverage,
        "degenerate_reason": reason,
        "c3_status": c3_status,
    }


def run_audit(
    dataset: Path,
    checkpoint: Path | None,
    eval_dir: Path | None,
    out: Path,
) -> dict[str, Any]:
    if eval_dir is not None:
        records = _records_from_eval_dir(eval_dir)
        source = str(eval_dir)
    else:
        records = _records_from_direct_inference(dataset, checkpoint)
        source = str(dataset)

    report = build_audit(records, source)
    report["dataset"] = str(dataset)
    report["checkpoint"] = None if checkpoint is None else str(checkpoint)
    report["eval_dir"] = None if eval_dir is None else str(eval_dir)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit Step 8 C3 F_t root cause.")
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--checkpoint", default=None)
    parser.add_argument("--eval-dir", default=None)
    parser.add_argument("--out", default=DEFAULT_OUT)
    args = parser.parse_args(argv)

    dataset = Path(args.dataset)
    checkpoint = Path(args.checkpoint) if args.checkpoint else None
    eval_dir = Path(args.eval_dir) if args.eval_dir else None
    out = Path(args.out)

    run_audit(dataset=dataset, checkpoint=checkpoint, eval_dir=eval_dir, out=out)
    print(f"Step 8 C3 audit written: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
