"""Audit Step 3 dataset label coverage.

This script is intentionally standalone so it can run before the FRCG-WM
package imports are available.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable


TARGET_FIELDS = (
    "hypothesis_update_timestamp",
    "recovery_timestamp",
    "ood_type",
    "selected_hypothesis_confidence",
    "true_wrong_hypothesis",
)
SPLIT_CHOICES = ("train", "valid", "test_id", "test_ood", "all")
SPLIT_ORDER = {split: index for index, split in enumerate(SPLIT_CHOICES)}


def _jsonl_files(data_root: Path, split_filter: str) -> list[Path]:
    if not data_root.exists():
        print(f"WARNING: data root does not exist: {data_root}", file=sys.stderr)
        return []
    if not data_root.is_dir():
        print(f"WARNING: data root is not a directory: {data_root}", file=sys.stderr)
        return []

    paths = sorted(data_root.rglob("*.jsonl"))
    if split_filter == "all":
        return paths
    return [path for path in paths if path.stem == split_filter]


def _split_sort_key(split: str) -> tuple[int, str]:
    return (SPLIT_ORDER.get(split, len(SPLIT_ORDER)), split)


def _iter_jsonl_records(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            record = json.loads(stripped)
            if not isinstance(record, dict):
                raise ValueError(f"{path}:{line_number} must contain a JSON object")
            yield record


def _iter_steps(record: dict[str, Any]) -> Iterable[tuple[dict[str, Any], str | None]]:
    episode_id = _string_or_none(record.get("episode_id"))
    steps = record.get("steps")
    if isinstance(steps, list):
        for step in steps:
            if isinstance(step, dict):
                yield step, _string_or_none(step.get("episode_id")) or episode_id
        return
    yield record, episode_id


def _string_or_none(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _labels(step: dict[str, Any]) -> dict[str, Any]:
    labels = step.get("eval_labels")
    if isinstance(labels, dict):
        return labels
    labels = step.get("evaluation_labels")
    if isinstance(labels, dict):
        return labels
    return {}


def _action(step: dict[str, Any]) -> dict[str, Any]:
    action = step.get("action")
    if isinstance(action, dict):
        return action
    return {}


def _field_value(step: dict[str, Any], field: str) -> Any:
    if field == "selected_hypothesis_confidence":
        return _action(step).get(field)
    return _labels(step).get(field)


def audit_coverage(data_root: Path, split_filter: str = "all") -> dict[str, Any]:
    """Return coverage counts for Step 3 label fields."""
    field_present = {field: 0 for field in TARGET_FIELDS}
    episode_ids: set[str] = set()
    total_steps = 0
    files = _jsonl_files(data_root, split_filter)

    for path in files:
        for record in _iter_jsonl_records(path):
            for step, episode_id in _iter_steps(record):
                total_steps += 1
                if episode_id is not None:
                    episode_ids.add(episode_id)
                for field in TARGET_FIELDS:
                    if _field_value(step, field) is not None:
                        field_present[field] += 1

    field_coverage = {}
    for field, present in field_present.items():
        field_coverage[field] = {
            "present": present,
            "total": total_steps,
            "ratio": present / total_steps if total_steps else 0.0,
        }

    splits_found = sorted({path.stem for path in files}, key=_split_sort_key)
    return {
        "data_root": str(data_root),
        "total_steps": total_steps,
        "total_episodes": len(episode_ids),
        "splits_found": splits_found,
        "field_coverage": field_coverage,
    }


def _print_summary(report: dict[str, Any]) -> None:
    print(f"Dataset coverage audit: {report['data_root']}")
    print(f"Splits found: {', '.join(report['splits_found']) or '<none>'}")
    print(f"Total episodes: {report['total_episodes']}")
    print(f"Total steps: {report['total_steps']}")
    print("Field coverage:")
    for field in TARGET_FIELDS:
        coverage = report["field_coverage"][field]
        print(
            f"  - {field}: {coverage['present']}/{coverage['total']} "
            f"({coverage['ratio']:.3f})"
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit Step 3 dataset label coverage.")
    parser.add_argument("--data-root", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--split", choices=SPLIT_CHOICES, default="all")
    args = parser.parse_args(argv)

    report = audit_coverage(args.data_root, args.split)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _print_summary(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
