from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import pytest
import yaml

SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from frcgw.evaluation.compute_budget import ComputeBudgetLog
from frcgw.evaluation.eval_runner import EvaluationRunner
from frcgw.evaluation.frcg_agent import TextFRCGModelAgent


def _load_runner_module() -> Any:
    path = Path("scripts/10_run_lr_real_eval.py")
    spec = importlib.util.spec_from_file_location("lr_real_eval_runner", path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


lr_real = _load_runner_module()
_build_agent_dispatch_table = lr_real._build_agent_dispatch_table
_install_forbidden_source_guard = lr_real._install_forbidden_source_guard
_write_per_step_jsonl = lr_real._write_per_step_jsonl
_build_metrics_with_blocked_markers = lr_real._build_metrics_with_blocked_markers
_write_manifest = lr_real._write_manifest
_TracingAgent = lr_real._TracingAgent
_attach_trace_records = lr_real._attach_trace_records


REQUIRED_AGENT_IDS = [
    "FRCG-LR",
    "ABL-017",
    "ABL-022",
    "ABL-023",
    "BASE-006",
    "BASE-012-CATTS",
    "BASE-015",
    "BASE-026",
    "BASE-027",
    "BASE-028",
    "BASE-003+008-VLAA",
]


def _step(step_index: int, *, recovery_ts: int | None = None) -> dict[str, Any]:
    return {
        "step_index": step_index,
        "public_input": {
            "instruction": "test",
            "history_public": [],
            "candidate_actions_public": [
                {"action_id": "a1", "action_type": "click", "action_params": {}}
            ],
        },
        "eval_labels": {
            "true_wrong_hypothesis": step_index == 0,
            "evidence_timestamp": 0,
            "hypothesis_update_timestamp": None,
            "recovery_timestamp": recovery_ts,
        },
        "targets": {
            "progress_delta": 0.0,
            "true_failed_action": False,
            "true_action_effect_type": "unknown",
        },
        "predicted_wrong": False,
        "wrong_prob": 0.1,
        "planning_events": [],
    }


def _synthetic_episode(
    with_recovery_ts: bool = True,
    with_confidence: bool = True,
) -> dict[str, Any]:
    steps = [_step(index, recovery_ts=1 if with_recovery_ts else None) for index in range(3)]
    if not with_recovery_ts:
        for step in steps:
            step["eval_labels"].pop("recovery_timestamp", None)
    if with_confidence:
        for step in steps:
            step["action"] = {"selected_hypothesis_confidence": 0.5}
    return {"episode_id": "ep0", "steps": steps}


def _write_minimal_jsonl(
    tmp_path: Path,
    *,
    n_episodes: int = 1,
    n_steps: int = 3,
    recovery_ts: int | None = None,
) -> Path:
    path = tmp_path / "episodes.jsonl"
    episodes = []
    for episode_index in range(n_episodes):
        episodes.append(
            {
                "episode_id": f"ep{episode_index}",
                "steps": [_step(index, recovery_ts=recovery_ts) for index in range(n_steps)],
            }
        )
    path.write_text("\n".join(json.dumps(episode) for episode in episodes) + "\n", encoding="utf-8")
    return path


class StubAgent:
    baseline_id = "STUB"
    call_count = 0
    last_predicted_wrong = False
    last_wrong_prob = 0.5

    def act(self, obs: Any, eval_labels: dict | None = None) -> tuple[Any, ComputeBudgetLog]:
        del obs, eval_labels
        self.call_count += 1
        from frcgw.evaluation.baselines import _noop_action

        return _noop_action(), ComputeBudgetLog(0, 0, 0, 0, 0.0)

    def reset(self) -> None:
        self.call_count = 0


def test_loads_config_without_error(tmp_path: Path) -> None:
    del tmp_path
    cfg = yaml.safe_load(Path("configs/lr_eval_real.yaml").read_text(encoding="utf-8"))
    assert cfg["run_mode"] == "real_episode_eval"
    assert "agents" in cfg


def test_dispatch_table_contains_all_required_agent_ids() -> None:
    cfg = yaml.safe_load(Path("configs/lr_eval_real.yaml").read_text(encoding="utf-8"))
    table = _build_agent_dispatch_table(cfg)
    for agent_id in REQUIRED_AGENT_IDS:
        assert agent_id in table, f"Missing agent: {agent_id}"


def test_frcg_full_and_frcg_lr_alias_resolve_to_same_class() -> None:
    cfg = yaml.safe_load(Path("configs/lr_eval_real.yaml").read_text(encoding="utf-8"))
    table = _build_agent_dispatch_table(cfg)
    agent = table["FRCG-LR"]()
    assert isinstance(agent, TextFRCGModelAgent)
    assert agent.baseline_id == "FRCG-FULL"


def test_runner_calls_agent_act_at_least_once(tmp_path: Path) -> None:
    dataset = _write_minimal_jsonl(tmp_path, n_episodes=1, n_steps=3)
    runner = EvaluationRunner({"metrics": ["task_success_rate"]})
    agent = StubAgent()
    runner.run(agent, dataset, "test_id", seed=0)
    assert agent.call_count >= 1


def test_runner_passes_public_observation_only(tmp_path: Path) -> None:
    episode = {
        "episode_id": "ep0",
        "steps": [
            {
                "step_index": 0,
                "public_input": {
                    "instruction": "test",
                    "true_wrong_hypothesis": True,
                    "candidate_actions_public": [],
                },
                "eval_labels": {},
                "targets": {},
            }
        ],
    }
    jsonl_path = tmp_path / "bad.jsonl"
    jsonl_path.write_text(json.dumps(episode) + "\n", encoding="utf-8")
    runner = EvaluationRunner({"metrics": ["task_success_rate"]})
    with pytest.raises(AssertionError):
        runner.run(StubAgent(), jsonl_path, "test_id", seed=0)


def test_runner_does_not_read_p3_lr_smoke(tmp_path: Path) -> None:
    forbidden = [str(tmp_path / "fake_smoke_metrics.json")]
    uninstall = _install_forbidden_source_guard(forbidden)
    try:
        with pytest.raises(RuntimeError, match="forbidden source"):
            open(forbidden[0])
    finally:
        uninstall()


def test_runner_does_not_read_p3_ablations(tmp_path: Path) -> None:
    forbidden = [str(tmp_path / "fake_ablation_results.json")]
    uninstall = _install_forbidden_source_guard(forbidden)
    try:
        with pytest.raises(RuntimeError, match="forbidden source"):
            Path(forbidden[0]).read_text(encoding="utf-8")
    finally:
        uninstall()


def test_runner_does_not_read_p3_lr_eval_metrics(tmp_path: Path) -> None:
    forbidden = [str(tmp_path / "fake_lr_eval_metrics.json")]
    uninstall = _install_forbidden_source_guard(forbidden)
    try:
        (tmp_path / "fake_lr_eval_metrics.json").write_text("{}", encoding="utf-8")
        with pytest.raises(RuntimeError, match="forbidden source"):
            with open(forbidden[0]) as handle:
                _ = handle.read()
    finally:
        uninstall()


def test_predicted_wrong_equals_agent_last_predicted_wrong(tmp_path: Path) -> None:
    dataset = _write_minimal_jsonl(tmp_path, n_episodes=1, n_steps=2)

    class RecordingAgent:
        baseline_id = "REC"
        last_wrong_prob = 0.9
        last_F_t = 0.0
        last_predicted_wrong = True

        def act(self, obs: Any, eval_labels: dict | None = None) -> tuple[Any, ComputeBudgetLog]:
            del obs, eval_labels
            from frcgw.evaluation.baselines import _noop_action

            return _noop_action(), ComputeBudgetLog(0, 0, 0, 0, 0.0)

        def reset(self) -> None:
            pass

    runner = EvaluationRunner({"metrics": ["task_success_rate"]})
    agent = _TracingAgent(RecordingAgent())
    result = runner.run(agent, dataset, "test_id", seed=0)
    _attach_trace_records(result, dataset, agent.records)
    out_dir = tmp_path / "out"
    _write_per_step_jsonl(result, "REC", 0, "test_id", out_dir)
    lines = (out_dir / "per_step" / "REC_seed0.jsonl").read_text(encoding="utf-8").splitlines()
    for line in lines:
        assert json.loads(line)["predicted_wrong"] is True


def test_predicted_wrong_threshold_documented_in_contract() -> None:
    contract_path = Path("docs/orchestration/lr_alignment/18_real_eval_runner_contract.md")
    if contract_path.exists():
        text = contract_path.read_text(encoding="utf-8")
    else:
        text = Path("scripts/10_run_lr_real_eval.py").read_text(encoding="utf-8")
    assert "confidence_threshold" in text
    assert "placeholder" in text.lower()
    assert "STEP 3" in text


def test_missing_recovery_timestamp_marks_C3_blocked(tmp_path: Path) -> None:
    dataset = _write_minimal_jsonl(tmp_path, n_episodes=2, n_steps=3, recovery_ts=None)
    runner = EvaluationRunner({"metrics": ["recovery_delay"]})
    result = runner.run(StubAgent(), dataset, "test_id", seed=0)
    dataset_audit = {
        "recovery_timestamp_coverage": 0,
        "hypothesis_update_timestamp_coverage": 0,
        "selected_hypothesis_confidence_coverage": 0,
        "counterfactual_coverage": 0,
        "ood_split_exists": False,
        "total_episodes_sampled": 2,
    }
    metrics = _build_metrics_with_blocked_markers([("STUB", 0, result)], {}, dataset_audit)
    stub_metrics = metrics["agents"]["STUB"]
    assert stub_metrics.get("C3_recovery_delay", {}).get("status", "").startswith("BLOCKED")
    assert stub_metrics.get("C3_recovery_delay", {}).get("value") is None


def test_missing_confidence_marks_C5_calibration_blocked_not_fake(tmp_path: Path) -> None:
    dataset = _write_minimal_jsonl(tmp_path, n_episodes=2, n_steps=3)
    runner = EvaluationRunner({"metrics": ["falsification_calibration"]})
    result = runner.run(StubAgent(), dataset, "test_id", seed=0)
    dataset_audit = {
        "recovery_timestamp_coverage": 0,
        "hypothesis_update_timestamp_coverage": 0,
        "selected_hypothesis_confidence_coverage": 0,
        "counterfactual_coverage": 0,
        "ood_split_exists": False,
        "total_episodes_sampled": 2,
    }
    metrics = _build_metrics_with_blocked_markers([("STUB", 0, result)], {}, dataset_audit)
    c5 = metrics["agents"]["STUB"].get("C5_calibration_ece", {})
    assert c5.get("status", "").startswith("BLOCKED"), f"Expected BLOCKED, got: {c5}"
    assert c5.get("value") is None, f"Expected null value, got: {c5.get('value')}"
    assert metrics["fake_metric_count"] == 0


def test_manifest_records_source_artifacts_used(tmp_path: Path) -> None:
    dataset = _write_minimal_jsonl(tmp_path, n_episodes=1, n_steps=2)
    config = {
        "dataset_path": str(dataset),
        "split": "test_id",
        "seeds": [0],
        "agents": [{"id": "BASE-015", "class": "ComputeMatchedRandomAgent"}],
        "metrics": ["task_success_rate"],
        "forbidden_sources": [],
    }
    dispatch = _build_agent_dispatch_table(config)
    runner = EvaluationRunner({"metrics": ["task_success_rate"]})
    results = [(agent_id, 0, runner.run(factory(), str(dataset), "test_id", 0)) for agent_id, factory in dispatch.items()]
    dataset_audit = {
        "recovery_timestamp_coverage": 0,
        "hypothesis_update_timestamp_coverage": 0,
        "selected_hypothesis_confidence_coverage": 0,
        "counterfactual_coverage": 0,
        "ood_split_exists": False,
        "total_episodes_sampled": 1,
    }
    metrics = _build_metrics_with_blocked_markers(results, config, dataset_audit)
    manifest = _write_manifest(config, tmp_path, metrics, "none_read", dataset_audit, write=False)
    assert manifest["source_artifacts_used"] == [config["dataset_path"]]
    assert "p3_lr_smoke" not in str(manifest["source_artifacts_used"])


def test_manifest_forbidden_source_artifacts_assertion_is_none_read(tmp_path: Path) -> None:
    config = {
        "dataset_path": "data/frcgw_text/v0_1/test_id.jsonl",
        "split": "test_id",
        "seeds": [0],
        "agents": [],
        "metrics": [],
        "forbidden_sources": [
            "outputs/runs/p3_lr_smoke/metrics.json",
            "outputs/runs/p3_ablations/ablation_results.json",
            "outputs/runs/p3_lr_eval/metrics.json",
        ],
    }
    dataset_audit = {
        "recovery_timestamp_coverage": 0,
        "hypothesis_update_timestamp_coverage": 0,
        "selected_hypothesis_confidence_coverage": 0,
        "counterfactual_coverage": 0,
        "ood_split_exists": False,
        "total_episodes_sampled": 0,
    }
    metrics = {
        "agents": {},
        "fake_metric_count": 0,
        "blocked_metric_count": 0,
        "hard_checks_all_pass": True,
    }
    manifest = _write_manifest(config, tmp_path, metrics, "none_read", dataset_audit, write=False)
    assert manifest["forbidden_source_assertion"] == "none_read"
    assert len(manifest["forbidden_source_artifacts"]) == 3
