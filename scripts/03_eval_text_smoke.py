"""scripts/03_eval_text_smoke.py -- CC-P3 text-only evaluation entrypoint.

Source docs:
- paper_context_ref/13_CLAUDE_CODE_EXECUTION_ROADMAP_v1.md section 9 (CC-P3)
- paper_context_ref/15_TDD_TECHNICAL_DESIGN_DOCUMENT_v1.md section 18
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate text-only FRCG model.")
    parser.add_argument("--config", required=True)
    parser.add_argument("--split", default=None)
    parser.add_argument("--output-dir", default=None)
    args = parser.parse_args()

    import yaml

    from frcgw.evaluation.baselines import (
        AlwaysPlanAgent,
        FrozenBaseAgent,
        NextStateWMOnlyAgent,
        RandomAlternativePlannerAgent,
        ReactiveAgent,
        RetryAfterFailureAgent,
        UncertaintyGatedAgent,
        VerifierOnlyAgent,
    )
    from frcgw.evaluation.eval_runner import EvaluationRunner

    config = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    if args.split:
        config["split"] = args.split
    if args.output_dir:
        config["report_path"] = args.output_dir

    runner = EvaluationRunner(config)

    manifest_path = Path("data/frcgw_text/v0_1/manifest.json")
    if not manifest_path.exists():
        print(f"[SKIP] manifest not found: {manifest_path}")
        return 0

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    split = config.get("split", "text_id")
    shard_path = _find_shard(manifest, split)
    if shard_path is None:
        print(f"[SKIP] no shard for split={split}")
        return 0

    agents = [
        FrozenBaseAgent(),
        ReactiveAgent(),
        RetryAfterFailureAgent(),
        VerifierOnlyAgent(),
        NextStateWMOnlyAgent(),
        AlwaysPlanAgent(),
        UncertaintyGatedAgent(),
        RandomAlternativePlannerAgent(),
    ]
    results = runner.run_all_baselines(agents, shard_path, split)
    report_dir = Path(config.get("report_path", "outputs/runs/p3_eval"))
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = runner.write_report(results, report_dir)
    print(f"[OK] eval report written: {report_path}")
    return 0


def _find_shard(manifest: dict, split: str) -> str | None:
    for shard in manifest.get("shards", []):
        if shard.get("split") == split:
            return shard.get("path")
    return None


if __name__ == "__main__":
    raise SystemExit(main())
