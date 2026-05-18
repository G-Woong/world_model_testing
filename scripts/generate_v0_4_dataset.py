"""Generate the Step 8 v0.4 text dataset.

The generator reuses the v0.3 text environment generator and collector. The
v0.4 OOD split adds explicit effect-type strata because the held-out grammar
families do not naturally produce blocker_removed or delayed_effect effects.
"""
from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import math
import random
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from frcgw.data.leakage_auditor import LeakageAuditor
from frcgw.schemas.episode_schema import EpisodeRecord
from frcgw.schemas.step_schema import PublicEffect
from frcgw.text_env.collector import CollectorConfig, collect_episode
from frcgw.text_env.counterfactual_rollout import _simulate_action as _base_simulate_action
from frcgw.text_env.generator import EpisodeSpecGenerator
from frcgw.text_env.policies import PolicyMixtureRunner


GENERATOR_VERSION = "p3-text-v0.4"
SPLITS = ("train", "valid", "test_id", "test_ood")
REQUIRED_MANIFEST_FIELDS = frozenset(
    {
        "schema_version",
        "total_episodes",
        "split_counts",
        "ood_effect_type_counts",
        "coverage_gate_status",
        "sha256",
        "generator_version",
        "seed",
        "timestamp",
    }
)
PUBLIC_EFFECT_TYPES = frozenset(
    {
        "state_change",
        "no_state_change",
        "blocker_removed",
        "delayed_effect",
        "task_complete",
    }
)


def _read_config(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        cfg = yaml.safe_load(handle)
    if not isinstance(cfg, dict):
        raise ValueError(f"config must be a YAML mapping: {path}")
    return cfg


def _scaled_split_counts(configured: dict[str, int], target: int) -> dict[str, int]:
    if target <= 0:
        raise ValueError("--target-episodes must be positive")

    base_total = sum(int(configured.get(split, 0)) for split in SPLITS)
    if target == base_total:
        return {split: int(configured.get(split, 0)) for split in SPLITS}

    raw = {
        split: target * (int(configured.get(split, 0)) / base_total)
        for split in SPLITS
    }
    counts = {split: int(math.floor(value)) for split, value in raw.items()}
    remainder = target - sum(counts.values())
    by_fraction = sorted(SPLITS, key=lambda split: (raw[split] - counts[split], -SPLITS.index(split)), reverse=True)
    for split in by_fraction[:remainder]:
        counts[split] += 1

    if target >= len(SPLITS):
        for split in SPLITS:
            if counts[split] > 0:
                continue
            donor = max(SPLITS, key=lambda candidate: counts[candidate])
            if counts[donor] <= 1:
                break
            counts[donor] -= 1
            counts[split] = 1

    return counts


def _single_policy(policy_id: str) -> dict[str, float]:
    return {
        "oracle": 1.0 if policy_id == "oracle" else 0.0,
        "wrong_grammar": 1.0 if policy_id == "wrong_grammar" else 0.0,
        "retry": 1.0 if policy_id == "retry" else 0.0,
        "recovery": 1.0 if policy_id == "recovery" else 0.0,
        "random_constrained": 1.0 if policy_id == "random_constrained" else 0.0,
    }


def _simulate_action(
    preconditions: dict[str, Any],
    action_id: str,
    engine: Any,
    forced_effect_type: str | None = None,
) -> tuple[str, float]:
    """Return public-safe effect simulation, optionally forcing an OOD stratum."""
    if forced_effect_type is not None:
        if forced_effect_type not in PUBLIC_EFFECT_TYPES:
            raise ValueError(f"unsupported forced effect type: {forced_effect_type}")
        forced_delta = 0.4 if forced_effect_type == "blocker_removed" else 0.3
        return forced_effect_type, forced_delta
    return _base_simulate_action(preconditions, action_id, engine)


def _collect_episode(
    generator: EpisodeSpecGenerator,
    family: str,
    split: str,
    cfg: dict[str, Any],
    mixture: dict[str, float],
    force_policy: str | None = None,
    forced_effect_type: str | None = None,
) -> EpisodeRecord:
    spec = generator.generate(family=family)
    if split == "test_ood":
        spec = dataclasses.replace(spec, ood_type="grammar_shift")

    collector_config = CollectorConfig(
        dataset_version=str(cfg["dataset_version"]),
        schema_version=str(cfg["schema_version"]),
        generator_version=str(cfg.get("generator_version", GENERATOR_VERSION)),
        split_id=split,
    )
    runner_mixture = _single_policy(force_policy) if force_policy else mixture
    runner = PolicyMixtureRunner(mixture=runner_mixture, rng=random.Random(spec.seed))
    episode = collect_episode(spec, runner, random.Random(spec.seed), collector_config)
    if forced_effect_type is not None:
        episode = _force_episode_effect_type(episode, forced_effect_type)
    return episode


def _force_episode_effect_type(episode: EpisodeRecord, forced_effect_type: str) -> EpisodeRecord:
    """Patch one OOD episode with an artificial public effect stratum.

    The hidden task family/control grammar labels remain the OOD family emitted
    by EpisodeSpecGenerator. Evaluation labels use no_matching_grammar because
    the forced public effect has no matching held-out grammar explanation.
    """
    if not episode.steps:
        return episode

    forced_effect_type, forced_delta = _simulate_action(
        {}, "", None, forced_effect_type=forced_effect_type
    )
    style_source = (
        "modal_blocker_style"
        if forced_effect_type == "blocker_removed"
        else "loading_delayed_style"
    )

    patched_steps = []
    source_step_index = episode.steps[0].step_index
    for index, step in enumerate(episode.steps):
        eval_labels = dataclasses.replace(
            step.evaluation_labels,
            correct_hypothesis_id="no_matching_grammar",
        )
        audit_metadata = step.audit_metadata
        if audit_metadata is not None:
            flags = dict(audit_metadata.leakage_check_flags)
            flags.update(
                {
                    "effect_type_stratified_episode": True,
                    "forced_effect_type": forced_effect_type,
                    "stratification_source": style_source,
                }
            )
            audit_metadata = dataclasses.replace(audit_metadata, leakage_check_flags=flags)

        public_observation = step.public_observation
        if index > 0:
            patched_history = []
            for item in public_observation.history_public:
                if item.step_index == source_step_index:
                    patched_history.append(
                        dataclasses.replace(item, effect_summary=forced_effect_type)
                    )
                else:
                    patched_history.append(item)
            public_observation = dataclasses.replace(
                public_observation,
                history_public=patched_history,
            )

        if index == 0:
            observed = PublicEffect(
                effect_type=forced_effect_type,
                dom_diff_public=None,
                text_diff_public="state_text_updated",
            )
            training_labels = dataclasses.replace(
                step.training_labels,
                true_action_effect_type=forced_effect_type,
                true_failed_action=False,
                failure_reason=None,
                progress_delta=max(float(step.training_labels.progress_delta), forced_delta),
            )
            patched_steps.append(
                dataclasses.replace(
                    step,
                    public_observation=public_observation,
                    observed_effect_public=observed,
                    training_labels=training_labels,
                    evaluation_labels=eval_labels,
                    audit_metadata=audit_metadata,
                )
            )
            continue

        patched_steps.append(
            dataclasses.replace(
                step,
                public_observation=public_observation,
                evaluation_labels=eval_labels,
                audit_metadata=audit_metadata,
            )
        )

    episode_audit = episode.audit_metadata
    if episode_audit is not None:
        flags = dict(episode_audit.leakage_check_flags)
        flags.update(
            {
                "effect_type_stratified_episode": True,
                "forced_effect_type": forced_effect_type,
                "stratification_source": style_source,
            }
        )
        episode_audit = dataclasses.replace(episode_audit, leakage_check_flags=flags)

    return dataclasses.replace(episode, steps=patched_steps, audit_metadata=episode_audit)


def _forced_ood_quotas(
    target_count: int,
    gates: dict[str, Any],
    strata: dict[str, float],
) -> dict[str, int]:
    if target_count <= 0:
        return {"blocker_removed": 0, "delayed_effect": 0}

    if target_count >= int(gates["blocker_removed_min"]) + int(gates["delayed_effect_min"]):
        return {
            "blocker_removed": max(
                int(gates["blocker_removed_min"]),
                int(round(target_count * float(strata.get("blocker_removed", 0.10)))),
            ),
            "delayed_effect": max(
                int(gates["delayed_effect_min"]),
                int(round(target_count * float(strata.get("delayed_effect", 0.10)))),
            ),
        }

    if target_count == 1:
        return {"blocker_removed": 1, "delayed_effect": 0}
    return {"blocker_removed": target_count // 2, "delayed_effect": target_count - target_count // 2}


def _generate_standard_split(
    split: str,
    count: int,
    families: list[str],
    generator: EpisodeSpecGenerator,
    cfg: dict[str, Any],
    mixture: dict[str, float],
) -> list[EpisodeRecord]:
    episodes: list[EpisodeRecord] = []
    for index in range(count):
        family = families[index % len(families)]
        episodes.append(_collect_episode(generator, family, split, cfg, mixture))
    return episodes


def _generate_ood_split(
    count: int,
    families: list[str],
    generator: EpisodeSpecGenerator,
    cfg: dict[str, Any],
    mixture: dict[str, float],
) -> tuple[list[EpisodeRecord], dict[str, Any]]:
    gates = dict(cfg["ood_coverage_gates"])
    strata = dict(cfg["ood_effect_type_strata"])
    quotas = _forced_ood_quotas(count, gates, strata)
    forced_total = min(count, sum(quotas.values()))
    normal_target = max(0, count - forced_total)
    max_attempts = max(1, 10 * max(count, 1))
    attempts = 0
    episodes: list[EpisodeRecord] = []

    for index in range(normal_target):
        attempts += 1
        if attempts > max_attempts:
            break
        family = families[index % len(families)]
        force_policy = "oracle" if index == 0 else "wrong_grammar" if index == 1 else None
        episodes.append(
            _collect_episode(
                generator,
                family,
                "test_ood",
                cfg,
                mixture,
                force_policy=force_policy,
            )
        )

    forced_index = 0
    for forced_effect_type, quota in quotas.items():
        for _ in range(quota):
            if len(episodes) >= count or attempts >= max_attempts:
                break
            attempts += 1
            family = families[forced_index % len(families)]
            forced_index += 1
            episodes.append(
                _collect_episode(
                    generator,
                    family,
                    "test_ood",
                    cfg,
                    mixture,
                    force_policy="oracle",
                    forced_effect_type=forced_effect_type,
                )
            )

    status = _coverage_gate_status(episodes, gates)
    if not status["pass"]:
        status = dict(status)
        status["warning"] = "OOD_COVERAGE_GATE_PARTIAL"
        status["attempts"] = attempts
        status["max_attempts"] = max_attempts
    return episodes, status


def _effect_type_counts(episodes: list[EpisodeRecord]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for episode in episodes:
        for step in episode.steps:
            counts[step.observed_effect_public.effect_type] += 1
    return counts


def _true_wrong_counts(episodes: list[EpisodeRecord]) -> Counter[str]:
    counts: Counter[str] = Counter({"true": 0, "false": 0, "none": 0})
    for episode in episodes:
        for step in episode.steps:
            value = step.evaluation_labels.true_wrong_hypothesis
            if value is True:
                counts["true"] += 1
            elif value is False:
                counts["false"] += 1
            else:
                counts["none"] += 1
    return counts


def _coverage_gate_status(
    episodes: list[EpisodeRecord],
    gates: dict[str, Any],
) -> dict[str, Any]:
    effects = _effect_type_counts(episodes)
    true_wrong = _true_wrong_counts(episodes)
    failures: list[str] = []

    blocker_min = int(gates["blocker_removed_min"])
    delayed_min = int(gates["delayed_effect_min"])
    if effects["blocker_removed"] < blocker_min:
        failures.append(f"blocker_removed_lt_{blocker_min}")
    if effects["delayed_effect"] < delayed_min:
        failures.append(f"delayed_effect_lt_{delayed_min}")
    if gates.get("true_wrong_both_classes", True):
        if true_wrong["true"] <= 0 or true_wrong["false"] <= 0:
            failures.append("missing_true_wrong_class")

    return {
        "pass": not failures,
        "status": "OOD_COVERAGE_GATE_PASS"
        if not failures
        else "OOD_COVERAGE_GATE_FAIL_" + "_".join(failures),
        "failures": failures,
        "effect_types": dict(sorted(effects.items())),
        "true_wrong_counts": {
            "true": true_wrong["true"],
            "false": true_wrong["false"],
            "none": true_wrong["none"],
        },
    }


def _audit_public_observations(episodes_by_split: dict[str, list[EpisodeRecord]]) -> None:
    observations = [
        step.public_observation
        for episodes in episodes_by_split.values()
        for episode in episodes
        for step in episode.steps
    ]
    report = LeakageAuditor().audit_agent_input(observations, source="v0_4_generated_public_observations")
    if not report.passed:
        raise RuntimeError(
            "Leakage audit failed before manifest write: "
            f"forbidden={report.forbidden_found} counterfactual={report.counterfactual_found}"
        )


def _write_jsonl(out_root: Path, split: str, episodes: list[EpisodeRecord]) -> Path:
    path = out_root / f"{split}.jsonl"
    with path.open("w", encoding="utf-8") as handle:
        for episode in episodes:
            handle.write(json.dumps(dataclasses.asdict(episode), ensure_ascii=False) + "\n")
    return path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_manifest(
    cfg: dict[str, Any],
    split_counts: dict[str, int],
    split_paths: dict[str, Path],
    episodes_by_split: dict[str, list[EpisodeRecord]],
    coverage_gate_status: dict[str, Any],
    seed: int,
) -> dict[str, Any]:
    test_ood_effects = _effect_type_counts(episodes_by_split.get("test_ood", []))
    manifest = {
        "schema_version": cfg["schema_version"],
        "dataset_version": cfg["dataset_version"],
        "total_episodes": sum(len(episodes) for episodes in episodes_by_split.values()),
        "target_episodes": sum(split_counts.values()),
        "split_counts": {split: len(episodes_by_split.get(split, [])) for split in SPLITS},
        "configured_split_counts": split_counts,
        "split_files": {split: f"{split}.jsonl" for split in SPLITS},
        "ood_effect_type_counts": dict(sorted(test_ood_effects.items())),
        "coverage_gate_status": coverage_gate_status,
        "sha256": {split: _sha256(path) for split, path in split_paths.items()},
        "generator_version": str(cfg.get("generator_version", GENERATOR_VERSION)),
        "seed": seed,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    missing = validate_manifest_schema(manifest)
    if missing:
        raise ValueError(f"manifest missing required fields: {missing}")
    return manifest


def validate_manifest_schema(manifest: dict[str, Any]) -> list[str]:
    return sorted(REQUIRED_MANIFEST_FIELDS - set(manifest))


def generate_dataset(
    cfg: dict[str, Any],
    out_root: Path,
    target_episodes: int | None = None,
    seed: int | None = None,
) -> dict[str, Any]:
    seed = int(seed if seed is not None else cfg["seed"])
    target = int(target_episodes if target_episodes is not None else cfg["target_episodes"])
    split_counts = _scaled_split_counts(cfg["splits"], target)
    mixture = dict(cfg["policy_mixture"])
    id_families = [str(family) for family in cfg["id_grammar_families"]]
    ood_families = [str(family) for family in cfg["ood_grammar_families"]]
    generator = EpisodeSpecGenerator(seed=seed, max_steps=int(cfg["max_steps"]))

    episodes_by_split: dict[str, list[EpisodeRecord]] = {}
    for split in ("train", "valid", "test_id"):
        episodes_by_split[split] = _generate_standard_split(
            split,
            split_counts[split],
            id_families,
            generator,
            cfg,
            mixture,
        )

    ood_episodes, coverage_gate_status = _generate_ood_split(
        split_counts["test_ood"],
        ood_families,
        generator,
        cfg,
        mixture,
    )
    episodes_by_split["test_ood"] = ood_episodes

    _audit_public_observations(episodes_by_split)

    out_root.mkdir(parents=True, exist_ok=True)
    split_paths = {
        split: _write_jsonl(out_root, split, episodes_by_split.get(split, []))
        for split in SPLITS
    }
    manifest = build_manifest(
        cfg,
        split_counts,
        split_paths,
        episodes_by_split,
        coverage_gate_status,
        seed,
    )
    (out_root / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate Step 8 v0.4 text dataset.")
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--out-root", type=Path, default=None)
    parser.add_argument("--target-episodes", type=int, default=None)
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args(argv)

    cfg = _read_config(args.config)
    out_root = args.out_root or Path(str(cfg["output_dir"]))
    manifest = generate_dataset(
        cfg,
        out_root,
        target_episodes=args.target_episodes,
        seed=args.seed,
    )
    print(
        json.dumps(
            {
                "out_root": str(out_root),
                "total_episodes": manifest["total_episodes"],
                "coverage_gate_status": manifest["coverage_gate_status"]["status"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
