"""Audit Step 8 v0.4 dataset coverage and public-observation leakage."""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from frcgw.data.leakage_auditor import LeakageAuditor


SPLITS = ("train", "valid", "test_id", "test_ood")
DEFAULT_OOD_GATES = {
    "blocker_removed_min": 30,
    "delayed_effect_min": 30,
    "true_wrong_both_classes": True,
}


def _iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    if not path.exists():
        return
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            record = json.loads(stripped)
            if not isinstance(record, dict):
                raise ValueError(f"{path}:{line_number} must contain a JSON object")
            yield record


def _iter_steps(episode_or_step: dict[str, Any]) -> Iterable[dict[str, Any]]:
    steps = episode_or_step.get("steps")
    if isinstance(steps, list):
        for step in steps:
            if isinstance(step, dict):
                yield step
        return
    yield episode_or_step


def _labels(step: dict[str, Any]) -> dict[str, Any]:
    labels = step.get("evaluation_labels")
    if isinstance(labels, dict):
        return labels
    labels = step.get("eval_labels")
    if isinstance(labels, dict):
        return labels
    return {}


def _effect_type(step: dict[str, Any]) -> str:
    effect = step.get("observed_effect_public")
    if isinstance(effect, dict) and effect.get("effect_type") is not None:
        return str(effect["effect_type"])
    if step.get("effect_type") is not None:
        return str(step["effect_type"])
    training_labels = step.get("training_labels")
    if isinstance(training_labels, dict) and training_labels.get("true_action_effect_type") is not None:
        return str(training_labels["true_action_effect_type"])
    return "missing"


def _agent_observation(step: dict[str, Any]) -> dict[str, Any] | None:
    obs = step.get("agent_observation")
    if isinstance(obs, dict):
        return obs
    obs = step.get("public_observation")
    if isinstance(obs, dict):
        return obs
    return None


def _true_wrong_key(value: Any) -> str:
    if value is True:
        return "true"
    if value is False:
        return "false"
    return "none"


def _split_report(
    data_root: Path,
    split: str,
    leakage_auditor: LeakageAuditor,
) -> tuple[dict[str, Any], int]:
    effect_counts: Counter[str] = Counter()
    true_wrong_counts: Counter[str] = Counter({"true": 0, "false": 0, "none": 0})
    leakage_count = 0
    total = 0

    for episode in _iter_jsonl(data_root / f"{split}.jsonl"):
        total += 1
        for step in _iter_steps(episode):
            effect_counts[_effect_type(step)] += 1
            true_wrong_counts[_true_wrong_key(_labels(step).get("true_wrong_hypothesis"))] += 1
            obs = _agent_observation(step)
            if obs is not None:
                report = leakage_auditor.audit_agent_input(obs, source=f"{split}:{total}")
                if not report.passed:
                    leakage_count += 1

    return (
        {
            "total": total,
            "effect_types": dict(sorted(effect_counts.items())),
            "true_wrong_counts": {
                "true": true_wrong_counts["true"],
                "false": true_wrong_counts["false"],
                "none": true_wrong_counts["none"],
            },
            "coverage_gate_pass": None,
        },
        leakage_count,
    )


def _ood_gate_status(
    test_ood: dict[str, Any],
    gates: dict[str, Any] | None = None,
) -> tuple[bool, str, list[str]]:
    gates = dict(DEFAULT_OOD_GATES if gates is None else gates)
    effect_types = test_ood.get("effect_types", {})
    true_wrong = test_ood.get("true_wrong_counts", {})
    failures: list[str] = []

    blocker_count = int(effect_types.get("blocker_removed", 0))
    blocker_min = int(gates.get("blocker_removed_min", 30))
    if blocker_count < blocker_min:
        failures.append(f"blocker_removed_lt_{blocker_min}")

    delayed_count = int(effect_types.get("delayed_effect", 0))
    delayed_min = int(gates.get("delayed_effect_min", 30))
    if delayed_count < delayed_min:
        failures.append(f"delayed_effect_lt_{delayed_min}")

    if gates.get("true_wrong_both_classes", True):
        if int(true_wrong.get("true", 0)) <= 0 or int(true_wrong.get("false", 0)) <= 0:
            failures.append("missing_true_wrong_class")

    if failures:
        return False, "OOD_COVERAGE_GATE_FAIL_" + "_".join(failures), failures
    return True, "OOD_COVERAGE_GATE_PASS", []


def audit_dataset_coverage(
    data_root: Path,
    gates: dict[str, Any] | None = None,
) -> dict[str, Any]:
    leakage_auditor = LeakageAuditor()
    split_reports: dict[str, dict[str, Any]] = {}
    leakage_count = 0

    for split in SPLITS:
        report, split_leakage_count = _split_report(data_root, split, leakage_auditor)
        split_reports[split] = report
        leakage_count += split_leakage_count

    ood_pass, ood_status, ood_failures = _ood_gate_status(split_reports["test_ood"], gates)
    split_reports["test_ood"]["coverage_gate_pass"] = ood_pass
    for split in ("train", "valid", "test_id"):
        split_reports[split]["coverage_gate_pass"] = True

    overall_pass = ood_pass and leakage_count == 0
    result: dict[str, Any] = {
        "data_root": str(data_root),
        "splits": split_reports,
        "leakage_count": leakage_count,
        "coverage_gate_overall": ood_status if leakage_count == 0 else "OOD_COVERAGE_GATE_FAIL_leakage",
        "ood_coverage_gate_pass": ood_pass,
        "ood_coverage_gate_status": ood_status,
        "ood_coverage_gate_failures": ood_failures,
        "overall_pass": overall_pass,
    }
    result.update(split_reports)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit Step 8 v0.4 dataset coverage.")
    parser.add_argument("--data-root", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)

    report = audit_dataset_coverage(args.data_root)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(report["coverage_gate_overall"])
    return 0 if report["overall_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
