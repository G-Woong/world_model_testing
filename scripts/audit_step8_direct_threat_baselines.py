"""Audit STEP 8 direct-threat baseline metrics and source wording."""
from __future__ import annotations

import argparse
import inspect
import json
import sys
from pathlib import Path
from statistics import mean
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from frcgw.evaluation.baselines import (  # noqa: E402
    CUWMFaithfulCandidate,
    CUWMStyleCandidateSimulationAgent,
    WACFaithfulCandidate,
    WACStyleConsequenceCorrectionAgent,
    WebWorldStyleSearchAgent,
)


AGENT_IDS = (
    "FRCG-LR",
    "BASE-026-faithful",
    "BASE-027-faithful",
    "BASE-026-heuristic",
    "BASE-027-heuristic",
    "BASE-028-heuristic",
)

BASELINE_CLASSES = {
    "BASE-026-faithful": WACFaithfulCandidate,
    "BASE-027-faithful": CUWMFaithfulCandidate,
    "BASE-026-heuristic": WACStyleConsequenceCorrectionAgent,
    "BASE-027-heuristic": CUWMStyleCandidateSimulationAgent,
    "BASE-028-heuristic": WebWorldStyleSearchAgent,
}


def _guarded_phrases() -> tuple[str, str, str]:
    return (
        "defeats " + "WAC",
        "outperforms " + "CUWM",
        "superior to " + "WebWorld",
    )


def _metric_files(eval_root: Path, agent_id: str) -> list[Path]:
    files = set(eval_root.glob(f"{agent_id}_*/*_metrics.json"))
    exact_dir = eval_root / agent_id
    if exact_dir.exists():
        files.update(exact_dir.glob("*_metrics.json"))
    return sorted(files)


def _numeric_values(value: Any) -> list[float]:
    if isinstance(value, bool):
        return []
    if isinstance(value, (int, float)):
        return [float(value)]
    if isinstance(value, list):
        values: list[float] = []
        for item in value:
            values.extend(_numeric_values(item))
        return values
    if isinstance(value, dict):
        for key in ("mean", "value", "rate"):
            if key in value:
                values = _numeric_values(value[key])
                if values:
                    return values
    return []


def _metric_values(payload: dict[str, Any], metric_name: str) -> list[float]:
    roots = [payload]
    if isinstance(payload.get("metrics"), dict):
        roots.insert(0, payload["metrics"])

    aliases = [metric_name]
    if metric_name == "wrong_grammar_persistence":
        aliases.append("wrong_control_grammar_persistence")

    for root in roots:
        for alias in aliases:
            if alias in root:
                return _numeric_values(root[alias])
    return []


def _metric_mean(eval_root: Path, agent_id: str, metric_name: str) -> float | None:
    values: list[float] = []
    for path in _metric_files(eval_root, agent_id):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            values.extend(_metric_values(payload, metric_name))
    return mean(values) if values else None


def _approximation_level(agent_id: str) -> str:
    cls = BASELINE_CLASSES.get(agent_id)
    if cls is None:
        return "trained"
    return str(getattr(cls, "approximation_level", "unspecified"))


def _forbidden_wording_count(agent_id: str) -> int:
    cls = BASELINE_CLASSES.get(agent_id)
    if cls is None:
        return 0
    source = inspect.getsource(cls)
    return sum(source.count(phrase) for phrase in _guarded_phrases())


def audit_direct_threat_baselines(eval_root: Path) -> dict[str, dict[str, Any]]:
    report: dict[str, dict[str, Any]] = {}
    for agent_id in AGENT_IDS:
        wording_count = _forbidden_wording_count(agent_id)
        task_success = _metric_mean(
            eval_root,
            agent_id,
            "task_success_rate",
        )
        wrong_grammar = _metric_mean(
            eval_root,
            agent_id,
            "wrong_grammar_persistence",
        )
        report[agent_id] = {
            "approximation_level": _approximation_level(agent_id),
            "metrics": {
                "task_success_rate": task_success,
                "task_success_rate_mean": task_success,
                "wrong_grammar_persistence": wrong_grammar,
                "wrong_grammar_persistence_mean": wrong_grammar,
                "metric_file_count": len(_metric_files(eval_root, agent_id)),
            },
            "forbidden_wording_count": wording_count,
            "gate_pass": wording_count == 0,
        }
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit STEP 8 direct-threat baselines.")
    parser.add_argument("--eval-root", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)

    report = audit_direct_threat_baselines(args.eval_root)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0 if all(item["gate_pass"] for item in report.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
