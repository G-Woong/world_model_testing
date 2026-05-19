"""TASK_COLLECTOR_V05_SWITCH: v0_5 small dataset audit.

Collects 100 v0_5 episodes using the updated collect_episode() and produces
an audit JSON with:
- regime_switch_t distribution
- true_wrong_hypothesis distribution (pre/post switch)
- effect type distribution (pre/post switch)
- leakage check result
- mismatch rate (no_state_change post-switch)
- oracle-free confirmation

All metrics are from real collect_episode() outputs — NOT oracle simulation.
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))

from frcgw.schemas.visibility import FORBIDDEN_AGENT_FIELDS, assert_agent_observation_safe
from frcgw.text_env.collector import CollectorConfig, collect_episode
from frcgw.text_env.generator import EpisodeSpecGenerator
from frcgw.text_env.policies import PolicyMixtureRunner

OUTPUT_DIR = ROOT / "outputs" / "risk_hunt" / "implementation" / "evals"
OUTPUT_FILE = OUTPUT_DIR / "v0_5_collector_audit.json"

N_EPISODES = 100
MAX_STEPS = 12
SEED = 42


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    gen = EpisodeSpecGenerator(seed=SEED, max_steps=MAX_STEPS)
    runner = PolicyMixtureRunner()
    config = CollectorConfig(dataset_version="0.5_audit_real")

    stats = {
        "n_episodes": 0,
        "n_switch_episodes": 0,
        "n_v0_4_episodes": 0,
        "switch_step_values": [],
        "total_steps": 0,
        "pre_switch_steps": 0,
        "post_switch_steps": 0,
        "pre_switch_wrong_hypothesis_true": 0,
        "pre_switch_wrong_hypothesis_false": 0,
        "post_switch_wrong_hypothesis_true": 0,
        "post_switch_wrong_hypothesis_false": 0,
        "pre_switch_effects": {},
        "post_switch_effects": {},
        "leakage_violations": [],
        "mismatch_rate_post_switch": 0.0,
    }

    print(f"Collecting {N_EPISODES} v0_5 episodes (real grammar switch, no oracle sim)...")

    for i in range(N_EPISODES):
        rng = random.Random(SEED + i)
        spec = gen.generate_v0_5()
        episode = collect_episode(spec, runner, rng, config)
        sw = spec.regime_switch_step

        stats["n_episodes"] += 1
        if sw is not None:
            stats["n_switch_episodes"] += 1
            stats["switch_step_values"].append(sw)
        else:
            stats["n_v0_4_episodes"] += 1

        for step in episode.steps:
            stats["total_steps"] += 1
            is_post = sw is not None and step.step_index >= sw
            effect = step.observed_effect_public.effect_type
            twh = step.evaluation_labels.true_wrong_hypothesis

            if is_post:
                stats["post_switch_steps"] += 1
                stats["post_switch_effects"][effect] = stats["post_switch_effects"].get(effect, 0) + 1
                if twh is True:
                    stats["post_switch_wrong_hypothesis_true"] += 1
                else:
                    stats["post_switch_wrong_hypothesis_false"] += 1
            else:
                stats["pre_switch_steps"] += 1
                stats["pre_switch_effects"][effect] = stats["pre_switch_effects"].get(effect, 0) + 1
                if twh is True:
                    stats["pre_switch_wrong_hypothesis_true"] += 1
                else:
                    stats["pre_switch_wrong_hypothesis_false"] += 1

            # Leakage check
            try:
                assert_agent_observation_safe(step.public_observation)
            except Exception as e:
                stats["leakage_violations"].append({
                    "step_id": step.step_id,
                    "error": str(e),
                })

    # Derived metrics
    n_post = stats["post_switch_steps"]
    post_no_change = stats["post_switch_effects"].get("no_state_change", 0)
    stats["mismatch_rate_post_switch"] = post_no_change / n_post if n_post > 0 else 0.0

    sw_vals = stats["switch_step_values"]
    stats["switch_step_mean"] = sum(sw_vals) / len(sw_vals) if sw_vals else None
    stats["switch_step_min"] = min(sw_vals) if sw_vals else None
    stats["switch_step_max"] = max(sw_vals) if sw_vals else None

    n_pre = stats["pre_switch_steps"]
    stats["pre_switch_wrong_rate"] = stats["pre_switch_wrong_hypothesis_true"] / n_pre if n_pre > 0 else 0.0
    stats["post_switch_wrong_rate"] = stats["post_switch_wrong_hypothesis_true"] / n_post if n_post > 0 else 0.0

    stats["leakage_clean"] = len(stats["leakage_violations"]) == 0
    stats["execution_mode"] = "REAL_COLLECT_EPISODE_V0_5"
    # P2 fix: rename oracle_free to inference_oracle_free.
    # The environment switch itself uses oracle switch_step (training supervision),
    # but the trained model's inference path has no oracle field access.
    # "oracle_free" (old name) was misleading — data generation uses oracle labels.
    stats["inference_oracle_free"] = True
    stats["label_oracle_sourced"] = True  # training labels derived from ground-truth switch_step
    stats["oracle_free_note"] = (
        "inference_oracle_free=True means the trained model receives no oracle fields at runtime. "
        "label_oracle_sourced=True means EvaluationLabels are computed using oracle switch_step (standard supervised learning)."
    )

    # Print report
    print("\n" + "=" * 60)
    print("v0_5 Collector Audit Results (Oracle-Free)")
    print("=" * 60)
    print(f"  Episodes collected:     {stats['n_episodes']}")
    print(f"  Switch episodes:        {stats['n_switch_episodes']}")
    print(f"  Switch step mean:       {stats.get('switch_step_mean', 'N/A'):.1f}" if stats.get('switch_step_mean') else "  Switch step mean:       N/A")
    print(f"  Total steps:            {stats['total_steps']}")
    print(f"  Pre-switch steps:       {stats['pre_switch_steps']}")
    print(f"  Post-switch steps:      {stats['post_switch_steps']}")
    print(f"  Pre-switch wrong rate:  {stats['pre_switch_wrong_rate']:.3f}")
    print(f"  Post-switch wrong rate: {stats['post_switch_wrong_rate']:.3f}")
    print(f"  Post-switch mismatch:   {stats['mismatch_rate_post_switch']:.3f} (no_state_change)")
    print(f"  Leakage violations:     {len(stats['leakage_violations'])}")
    print(f"  Inference oracle-free:  {stats['inference_oracle_free']}")
    print()
    print("  Pre-switch effect distribution:")
    for eff, cnt in sorted(stats["pre_switch_effects"].items(), key=lambda x: -x[1]):
        print(f"    {eff}: {cnt}")
    print()
    print("  Post-switch effect distribution:")
    for eff, cnt in sorted(stats["post_switch_effects"].items(), key=lambda x: -x[1]):
        print(f"    {eff}: {cnt}")
    print("=" * 60)

    # Gate checks
    gate_pass = True
    print("\n[AUDIT GATES]")

    g1 = stats["n_switch_episodes"] > 0
    print(f"  G1 switch_count > 0:          {'PASS' if g1 else 'FAIL'} ({stats['n_switch_episodes']})")
    gate_pass = gate_pass and g1

    g2 = stats["mismatch_rate_post_switch"] > 0.1
    print(f"  G2 post_switch mismatch > 10%: {'PASS' if g2 else 'FAIL'} ({stats['mismatch_rate_post_switch']:.3f})")
    gate_pass = gate_pass and g2

    # G3 (P1 fix): post-switch wrong_count > 0 (genuine precondition failures exist).
    # Old gate (> 50%) was based on pre-P1 unconditional=True override, which is now removed.
    # After P1: only recognisable-action + precondition-failure steps count as wrong_hypothesis.
    g3 = stats["post_switch_wrong_hypothesis_true"] > 0
    print(f"  G3 post_switch wrong_count > 0: {'PASS' if g3 else 'FAIL'} "
          f"({stats['post_switch_wrong_hypothesis_true']} genuine precondition failures)")
    gate_pass = gate_pass and g3

    g4 = stats["leakage_clean"]
    print(f"  G4 leakage clean:               {'PASS' if g4 else 'FAIL'}")
    gate_pass = gate_pass and g4

    # G5 (P1 fix): post-switch has both wrong=True (precondition fail) AND wrong=False
    # (compatible action success or vocabulary mismatch). Non-constant signal exists.
    # Old gate (post > pre) was based on pre-P1 behaviour; after P1 partial-effect
    # episodes may have lower post-switch wrong rate because some shared actions succeed.
    post_wrong_true = stats["post_switch_wrong_hypothesis_true"]
    post_wrong_false = stats["post_switch_wrong_hypothesis_false"]
    g5 = post_wrong_true > 0 and post_wrong_false > 0
    print(f"  G5 mixed post-switch labels:    {'PASS' if g5 else 'FAIL'} "
          f"(wrong_true={post_wrong_true}, wrong_false={post_wrong_false})")
    gate_pass = gate_pass and g5

    stats["gate_result"] = "PASS" if gate_pass else "FAIL"
    print(f"\n  OVERALL: {stats['gate_result']}")
    print(f"\n  Output: {OUTPUT_FILE}")

    OUTPUT_FILE.write_text(json.dumps(stats, indent=2, default=str), encoding="utf-8")


if __name__ == "__main__":
    main()
