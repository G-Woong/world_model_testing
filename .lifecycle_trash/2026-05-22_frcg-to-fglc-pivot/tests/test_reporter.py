from __future__ import annotations

import json
from pathlib import Path

import pytest

from frcgw.evaluation.reporter import EvalReporter


def _metrics_results() -> list[dict]:
    return [
        {
            "agent_id": "VerifierOnlyAgent",
            "split": "text_id",
            "seed": 0,
            "metrics": {
                "recovery_delay": 2.5,
                "progress_per_compute": 0.15,
                "task_success_rate": 0.6,
                "normalized_return": 0.5,
                "wrong_control_grammar_persistence": 3.0,
                "failed_action_repetition_rate": 0.2,
                "falsification_precision_recall": {"precision": 0.7, "recall": 0.6, "f1": 0.65},
                "falsification_calibration": 0.1,
                "false_planning_call_rate": 0.3,
                "action_switch_delay": 2.0,
            },
            "n_episodes": 33,
        },
        {
            "agent_id": "UncertaintyGatedAgent",
            "split": "text_id",
            "seed": 0,
            "metrics": {
                "recovery_delay": 3.5,
                "progress_per_compute": 0.08,
                "task_success_rate": 0.5,
                "normalized_return": 0.4,
                "wrong_control_grammar_persistence": 4.0,
                "failed_action_repetition_rate": 0.3,
                "falsification_precision_recall": {"precision": 0.5, "recall": 0.4, "f1": 0.44},
                "falsification_calibration": 0.2,
                "false_planning_call_rate": 0.5,
                "action_switch_delay": 3.0,
            },
            "n_episodes": 33,
        },
        {
            "agent_id": "FrozenBaseAgent",
            "split": "text_id",
            "seed": 0,
            "metrics": {
                "recovery_delay": 4.0,
                "progress_per_compute": 0.05,
                "task_success_rate": 0.3,
                "normalized_return": 0.3,
                "wrong_control_grammar_persistence": 5.0,
                "failed_action_repetition_rate": 0.4,
                "falsification_precision_recall": {"precision": 0.0, "recall": 0.0, "f1": 0.0},
                "falsification_calibration": 0.4,
                "false_planning_call_rate": 0.0,
                "action_switch_delay": 5.0,
            },
            "n_episodes": 33,
        },
    ]


def _ablation_results() -> list[dict]:
    return [
        {
            "ablation_id": "no_control_grammar",
            "seed": 0,
            "split": "text_ood_grammar",
            "metrics": {"wrong_control_grammar_persistence": 6.0, "task_success_rate": 0.2},
        },
        {
            "ablation_id": "no_falsification",
            "seed": 0,
            "split": "text_ood_grammar",
            "metrics": {
                "falsification_precision_recall": {"f1": 0.0},
                "false_planning_call_rate": 0.8,
            },
        },
    ]


@pytest.fixture()
def reporter_with_artifacts(tmp_path: Path) -> EvalReporter:
    eval_dir = tmp_path / "outputs" / "runs" / "p3_eval"
    ablation_dir = tmp_path / "outputs" / "runs" / "p3_ablations"
    eval_dir.mkdir(parents=True)
    ablation_dir.mkdir(parents=True)
    (eval_dir / "metrics.json").write_text(json.dumps(_metrics_results()), encoding="utf-8")
    (ablation_dir / "ablation_results.json").write_text(
        json.dumps(_ablation_results()), encoding="utf-8"
    )
    return EvalReporter(eval_dir, ablation_dir, tmp_path / "plans" / "P3_EVAL_GATE_REPORT.md")


def test_eval_reporter_loads_both_artifact_files(reporter_with_artifacts: EvalReporter) -> None:
    assert reporter_with_artifacts.load_eval_results() == _metrics_results()
    assert reporter_with_artifacts.load_ablation_results() == _ablation_results()


def test_check_gate_g1_passes_when_verifier_recovers_faster(
    reporter_with_artifacts: EvalReporter,
) -> None:
    result = reporter_with_artifacts.check_gate_g1(reporter_with_artifacts.load_eval_results())

    assert result.passed is True


def test_check_gate_g2_passes_when_verifier_progress_per_compute_is_higher(
    reporter_with_artifacts: EvalReporter,
) -> None:
    result = reporter_with_artifacts.check_gate_g2(reporter_with_artifacts.load_eval_results())

    assert result.passed is True


def test_check_gate_g3_passes_when_no_control_grammar_persistence_is_higher(
    reporter_with_artifacts: EvalReporter,
) -> None:
    result = reporter_with_artifacts.check_gate_g3(reporter_with_artifacts.load_ablation_results())

    assert result.passed is True


def test_check_gate_g4_passes_when_no_falsification_collapses(
    reporter_with_artifacts: EvalReporter,
) -> None:
    result = reporter_with_artifacts.check_gate_g4(reporter_with_artifacts.load_ablation_results())

    assert result.passed is True


def test_write_report_creates_markdown_without_missing_markers_when_data_present(
    reporter_with_artifacts: EvalReporter,
) -> None:
    report_path = Path(reporter_with_artifacts.write_report())
    report = report_path.read_text(encoding="utf-8")

    assert report_path.exists()
    assert "## Gate Results" in report
    assert all(gate in report for gate in ["CC-P3-G1", "CC-P3-G2", "CC-P3-G3", "CC-P3-G4"])
    assert "DATA_MISSING" not in report
    assert "None" not in report


def test_eval_reporter_raises_file_not_found_when_artifact_files_missing(tmp_path: Path) -> None:
    reporter = EvalReporter(
        tmp_path / "missing_eval",
        tmp_path / "missing_ablation",
        tmp_path / "plans" / "P3_EVAL_GATE_REPORT.md",
    )

    with pytest.raises(FileNotFoundError):
        reporter.load_eval_results()
    with pytest.raises(FileNotFoundError):
        reporter.load_ablation_results()
    with pytest.raises(FileNotFoundError):
        reporter.write_report()


def test_gate_check_result_passed_is_none_when_required_agent_missing(
    reporter_with_artifacts: EvalReporter,
) -> None:
    eval_results = [
        row for row in reporter_with_artifacts.load_eval_results()
        if row["agent_id"] != "VerifierOnlyAgent"
    ]

    result = reporter_with_artifacts.check_gate_g1(eval_results)

    assert result.passed is None
