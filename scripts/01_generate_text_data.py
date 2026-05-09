"""scripts/01_generate_text_data.py — P2 text-only data generation driver.

Source docs:
- paper_context_ref/13_CLAUDE_CODE_EXECUTION_ROADMAP_v1.md §8 (CC-P2)
- paper_context_ref/12_DATA_COLLECTION_METHODOLOGY_v1.md §8, §13, §16
- paper_context_ref/15_TDD_TECHNICAL_DESIGN_DOCUMENT_v1.md §18
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import shutil
import sys
from pathlib import Path

import yaml

# Ensure src/ is importable
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from frcgw.data.coverage_auditor import CoverageAuditor, CoverageThresholds
from frcgw.data.leakage_auditor import LeakageAuditor
from frcgw.data.shard_exporter import ShardExporter
from frcgw.text_env.collector import CollectorConfig, collect_episode
from frcgw.text_env.generator import EpisodeSpecGenerator, TaskFamily
from frcgw.text_env.policies import PolicyMixtureRunner
from frcgw.text_env.replay import ReplayValidator


def _split_id_from_hash(episode_id: str, train: float, valid: float) -> str:
    h = int(hashlib.md5(episode_id.encode()).hexdigest(), 16) % 100
    if h < int(train * 100):
        return "train"
    if h < int((train + valid) * 100):
        return "valid"
    return "test_id"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="P2 text-only data generator.")
    parser.add_argument("--config", required=True, help="Path to YAML config file.")
    parser.add_argument("--num-episodes", type=int, default=None,
                        help="Override num_episodes from config.")
    parser.add_argument("--out-dir", type=str, default=None,
                        help="Override output_dir from config.")
    args = parser.parse_args(argv)

    with open(args.config, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    num_episodes: int = args.num_episodes or cfg["num_episodes"]
    out_dir = Path(args.out_dir or cfg["output_dir"])
    seed: int = cfg["seed"]
    max_steps: int = cfg["max_steps"]
    dataset_version: str = cfg["dataset_version"]
    schema_version: str = cfg["schema_version"]
    generator_version: str = cfg["generator_version"]
    mixture_cfg: dict = cfg["policy_mixture"]
    cov_thresholds_cfg: dict = cfg["coverage_thresholds"]
    splits_cfg: dict = cfg["splits"]

    print(f"[P2] Generating {num_episodes} episodes → {out_dir}")
    print(f"[P2] seed={seed}, max_steps={max_steps}")

    # Setup
    exporter = ShardExporter(out_dir, dataset_version, schema_version)
    gen = EpisodeSpecGenerator(seed=seed, max_steps=max_steps)
    rng = random.Random(seed)
    runner = PolicyMixtureRunner(mixture=mixture_cfg, rng=random.Random(seed))
    thresholds = CoverageThresholds(**cov_thresholds_cfg)
    coverage_auditor = CoverageAuditor(thresholds)
    leakage_auditor = LeakageAuditor()

    episodes = []
    failed_count = 0

    # Generate episodes round-robin over task families to ensure coverage
    families = list(TaskFamily)
    n_per_family = max(1, num_episodes // len(families))

    for i in range(num_episodes):
        family = families[i % len(families)]
        try:
            spec = gen.generate(family=family)
            # Assign split deterministically
            split_id = _split_id_from_hash(spec.episode_id,
                                           splits_cfg["train"],
                                           splits_cfg["valid"])
            config = CollectorConfig(
                dataset_version=dataset_version,
                schema_version=schema_version,
                generator_version=generator_version,
                split_id=split_id,
            )
            ep = collect_episode(spec, runner, random.Random(spec.seed), config)
            exporter.write_episode(split_id, ep)
            episodes.append(ep)

            if (i + 1) % 50 == 0:
                print(f"[P2]   {i+1}/{num_episodes} episodes collected")

        except Exception as e:
            print(f"[P2] ERROR episode {i}: {e}", file=sys.stderr)
            failed_count += 1
            if failed_count > num_episodes // 10:
                print("[P2] Too many failures — aborting.", file=sys.stderr)
                return 1

    print(f"[P2] Collection complete: {len(episodes)} episodes, {failed_count} failures")

    # Coverage audit
    print("[P2] Running coverage audit...")
    cov_report = coverage_auditor.audit(episodes)
    print(f"[P2] Coverage ratios: {json.dumps(cov_report.ratios, indent=2)}")
    if not cov_report.gate_pass:
        print(f"[P2] COVERAGE GATE FAIL: {cov_report.failures}", file=sys.stderr)

    # Leakage audit on all public observations
    print("[P2] Running leakage audit...")
    all_obs = [s.public_observation for ep in episodes for s in ep.steps]
    leak_report = leakage_auditor.audit_agent_input(all_obs, source="full_dataset")
    if not leak_report.passed:
        print(f"[P2] LEAKAGE GATE FAIL: forbidden={leak_report.forbidden_found} "
              f"counterfactual={leak_report.counterfactual_found}", file=sys.stderr)

    # Write manifest and audit reports
    exporter.write_manifest(cov_report, leak_report)

    # Copy config to metadata
    meta_dir = out_dir / "metadata"
    meta_dir.mkdir(exist_ok=True)
    shutil.copy(args.config, meta_dir / "generator_config.yaml")
    (meta_dir / "version_hash.txt").write_text(
        f"{generator_version}\n{dataset_version}\n{schema_version}\n",
        encoding="utf-8",
    )

    # Replay validation (sample 5 episodes)
    print("[P2] Running replay validation (sample 5)...")
    validator = ReplayValidator()
    sample_specs_seen: list = []
    gen2 = EpisodeSpecGenerator(seed=seed, max_steps=max_steps)
    for i in range(min(5, num_episodes)):
        sample_spec = gen2.generate(family=families[i % len(families)])
        sample_specs_seen.append(sample_spec)

    replay_results = validator.validate_batch(sample_specs_seen, CollectorConfig(
        dataset_version=dataset_version,
        schema_version=schema_version,
        generator_version=generator_version,
        split_id="train",
    ), mixture=mixture_cfg)
    replay_pass = all(replay_results.values())
    replay_failed = [k for k, v in replay_results.items() if not v]

    replay_report = {"pass": replay_pass, "failed_ids": replay_failed,
                     "total_checked": len(replay_results)}
    (out_dir / "audits" / "replay_report.json").write_text(
        json.dumps(replay_report, indent=2), encoding="utf-8"
    )
    print(f"[P2] Replay: {'PASS' if replay_pass else 'FAIL'} ({len(replay_results)} checked)")

    # Summary
    gate_pass = cov_report.gate_pass and leak_report.passed and replay_pass
    print(f"\n[P2] === GATE STATUS ===")
    print(f"  Coverage: {'PASS' if cov_report.gate_pass else 'FAIL'}")
    print(f"  Leakage:  {'PASS' if leak_report.passed else 'FAIL'}")
    print(f"  Replay:   {'PASS' if replay_pass else 'FAIL'}")
    print(f"  OVERALL:  {'PASS' if gate_pass else 'FAIL'}")
    print(f"  Output:   {out_dir}")

    return 0 if gate_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
