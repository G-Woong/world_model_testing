"""Backfill true_regime from training_labels into evaluation_labels for v0_4 dataset."""
from __future__ import annotations

import json
from pathlib import Path


def backfill(dataset_root: str) -> dict:
    root = Path(dataset_root)
    stats = {}
    for split_file in ["train.jsonl", "valid.jsonl", "test_id.jsonl", "test_ood.jsonl"]:
        path = root / split_file
        if not path.exists():
            continue
        lines = path.read_text(encoding="utf-8-sig").strip().split("\n")
        updated = 0
        already_set = 0
        output_lines = []
        for line in lines:
            if not line.strip():
                continue
            episode = json.loads(line)
            for step in episode.get("steps", []):
                training_labels = step.get("training_labels", {}) or {}
                evaluation_labels = step.get("evaluation_labels") or {}
                if evaluation_labels.get("true_regime") is not None:
                    already_set += 1
                else:
                    true_regime = training_labels.get("true_regime")
                    if true_regime is not None:
                        if step.get("evaluation_labels") is None:
                            step["evaluation_labels"] = {}
                        step["evaluation_labels"]["true_regime"] = true_regime
                        updated += 1
            output_lines.append(json.dumps(episode, ensure_ascii=False))
        path.write_text("\n".join(output_lines) + "\n", encoding="utf-8")
        stats[split_file] = {"updated": updated, "already_set": already_set}
    return stats


if __name__ == "__main__":
    import sys

    root = sys.argv[1] if len(sys.argv) > 1 else "data/frcgw_text/v0_4"
    stats = backfill(root)
    print(json.dumps(stats, indent=2))
