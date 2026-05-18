"""Compute divergence_rate = action_changed_by_rollout mean over all steps.

Usage:
    python scripts/risk_hunt/compute_foresight_causal.py --result-dir outputs/risk_hunt/experiments/

Source MD: paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md Claim-C foresight causal
"""
from __future__ import annotations

import argparse
import json
import pathlib
from typing import Any


def _episodes_from_payload(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        return [episode for episode in data if isinstance(episode, dict)]
    if isinstance(data, dict):
        episodes = data.get("episodes", [])
        if isinstance(episodes, list):
            return [episode for episode in episodes if isinstance(episode, dict)]
    return []


def compute(result_dir: str) -> dict[str, float | int]:
    total_steps = 0
    changed_steps = 0
    for json_file in pathlib.Path(result_dir).rglob("episode_results*.json"):
        data = json.loads(json_file.read_text(encoding="utf-8"))
        for episode in _episodes_from_payload(data):
            for step in episode.get("steps", []):
                if not isinstance(step, dict):
                    continue
                total_steps += 1
                if step.get("action_changed_by_rollout", False):
                    changed_steps += 1
    divergence_rate = changed_steps / total_steps if total_steps > 0 else 0.0
    return {
        "divergence_rate": divergence_rate,
        "changed_steps": changed_steps,
        "total_steps": total_steps,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result-dir", required=True)
    args = parser.parse_args()
    result = compute(args.result_dir)
    print(
        f"divergence_rate={result['divergence_rate']:.4f} "
        f"({result['changed_steps']}/{result['total_steps']} steps changed by rollout)"
    )


if __name__ == "__main__":
    main()
