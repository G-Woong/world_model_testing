"""scripts/08_run_core_ablations.py -- CC-P3 core ablation runner entrypoint.

Source docs:
- paper_context_ref/13_CLAUDE_CODE_EXECUTION_ROADMAP_v1.md section 12
- paper_context_ref/15_TDD_TECHNICAL_DESIGN_DOCUMENT_v1.md section 18
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


def main() -> int:
    parser = argparse.ArgumentParser(description="Run core ablations for FRCG model.")
    parser.add_argument("--config", required=True)
    parser.add_argument("--split", default=None)
    args = parser.parse_args()

    import yaml

    from frcgw.evaluation.ablations import ABLATION_REGISTRY, apply_ablation
    from frcgw.evaluation.baselines import FrozenBaseAgent
    from frcgw.evaluation.eval_runner import EvaluationRunner

    config = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    if args.split:
        config["split"] = args.split

    manifest_path = Path("data/frcgw_text/v0_1/manifest.json")
    if not manifest_path.exists():
        print(f"[SKIP] manifest not found: {manifest_path}")
        return 0

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    split = config.get("split", "text_ood_grammar")
    shard_path = _find_shard(manifest, split)
    if shard_path is None:
        print(f"[SKIP] no shard for split={split}")
        return 0

    runner = EvaluationRunner(config)
    report_dir = Path(config.get("report_path", "outputs/runs/p3_ablations"))
    report_dir.mkdir(parents=True, exist_ok=True)

    all_results = []
    base_agent = FrozenBaseAgent()
    for ablation_id, abl_config in ABLATION_REGISTRY.items():
        ablated_agent = apply_ablation(base_agent, abl_config)
        for seed in config.get("seeds", [0]):
            if hasattr(ablated_agent, "reset"):
                ablated_agent.reset()
            result = runner.run(ablated_agent, shard_path, split, seed)
            result_dict = {
                "ablation_id": ablation_id,
                "seed": seed,
                "split": split,
                "metrics": result.metrics,
            }
            all_results.append(result_dict)

    out_path = report_dir / "ablation_results.json"
    out_path.write_text(json.dumps(all_results, indent=2), encoding="utf-8")
    print(f"[OK] ablation results written: {out_path}")
    return 0


def _find_shard(manifest: dict, split: str) -> str | None:
    # Manifest format: {"splits": {"train": N, "valid": N, "test_id": N}}
    # Ablation config uses "text_ood_grammar" which maps to "test_id" fallback
    _ALIAS = {"text_id": "test_id", "text_ood_grammar": "test_id", "text_noisy": "test_id"}
    splits_dict = manifest.get("splits", {})
    for candidate in [split, _ALIAS.get(split, split)]:
        if candidate in splits_dict:
            p = Path("data/frcgw_text/v0_1") / f"{candidate}.jsonl"
            if p.exists():
                return str(p)
    return None


if __name__ == "__main__":
    raise SystemExit(main())
