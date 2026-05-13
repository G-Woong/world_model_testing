from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml

from frcgw.evaluation.ablations import ABLATION_REGISTRY, AblationConfig, apply_ablation
from frcgw.evaluation.baselines import FORBIDDEN_AGENT_KEYS, FrozenBaseAgent
from frcgw.evaluation.compute_budget import ComputeBudgetLog
from frcgw.schemas.step_schema import CandidateAction, PublicObservation


REQUIRED_ABLATION_IDS = {
    "no_control_grammar",
    "merged_regime_control_grammar",
    "collapsed_latent",
    "no_falsification",
    "uncertainty_instead_of_falsification",
    "no_alternative_hypothesis",
    "random_alternative",
    "no_rollout",
    "no_rewrite",
    "always_plan_no_gate",
    "no_progress_reward",
    "no_compute_gate",
}

CRITICAL_ABLATION_IDS = {
    "no_control_grammar",
    "collapsed_latent",
    "no_falsification",
    "uncertainty_instead_of_falsification",
    "no_alternative_hypothesis",
    "no_rewrite",
    "always_plan_no_gate",
    "no_compute_gate",
}


class GuardedObservation(PublicObservation):
    def __getattribute__(self, name: str):
        if name in FORBIDDEN_AGENT_KEYS:
            raise AssertionError(f"forbidden key read: {name}")
        return super().__getattribute__(name)


def _obs() -> PublicObservation:
    return GuardedObservation(
        instruction="click the visible submit button",
        dom_snapshot_public={"visible": True},
        accessibility_tree_public={"role": "root"},
        screenshot_ref="screen-1",
        history_public=[],
        candidate_actions_public=[
            CandidateAction("a", "click", {"target": "left"}),
            CandidateAction("longer-action-id", "click", {"target": "right"}),
        ],
    )


def test_ablation_registry_has_all_12_ids() -> None:
    assert set(ABLATION_REGISTRY) == REQUIRED_ABLATION_IDS
    assert len(ABLATION_REGISTRY) == 12


def test_ablation_config_fields_are_populated() -> None:
    for ablation_id, config in ABLATION_REGISTRY.items():
        assert isinstance(config, AblationConfig)
        assert config.ablation_id == ablation_id
        assert config.tdd_ref.startswith("ABL-")
        assert config.severity in {"CRITICAL", "standard"}
        assert config.description
        assert config.expected_collapse
        assert config.masking


def test_critical_ablation_severities() -> None:
    for ablation_id in CRITICAL_ABLATION_IDS:
        assert ABLATION_REGISTRY[ablation_id].severity == "CRITICAL"


def test_expected_collapse_directions_are_valid() -> None:
    for config in ABLATION_REGISTRY.values():
        assert set(config.expected_collapse.values()).issubset({"increase", "decrease"})


def test_apply_ablation_returns_agent_with_act_and_ablation_id() -> None:
    for ablation_id, config in ABLATION_REGISTRY.items():
        agent = apply_ablation(FrozenBaseAgent(), config)

        assert hasattr(agent, "act")
        assert agent.ablation_id == ablation_id


def test_ablated_agent_act_returns_action_and_compute_budget() -> None:
    for config in ABLATION_REGISTRY.values():
        agent = apply_ablation(FrozenBaseAgent(), config)

        action, log = agent.act(_obs())

        assert isinstance(action, CandidateAction)
        assert isinstance(log, ComputeBudgetLog)


def test_ablated_agent_does_not_read_forbidden_observation_keys() -> None:
    for config in ABLATION_REGISTRY.values():
        agent = apply_ablation(FrozenBaseAgent(), config)

        agent.act(_obs())

        assert FORBIDDEN_AGENT_KEYS.isdisjoint(vars(agent))


def test_ablation_core_yaml_matches_registry_and_has_no_null_core_values() -> None:
    config = yaml.safe_load(Path("configs/ablation_core.yaml").read_text(encoding="utf-8"))
    yaml_ids = {entry["id"] for entry in config["ablations"]}

    assert config["seeds"]
    assert config["split"]
    assert config["ablations"]
    assert yaml_ids == set(ABLATION_REGISTRY)
    assert all(entry["expected_collapse"] for entry in config["ablations"])


def test_ablation_runner_script_runs_without_not_implemented_error() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/08_run_core_ablations.py",
            "--config",
            "configs/ablation_core.yaml",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "NotImplementedError" not in result.stderr
