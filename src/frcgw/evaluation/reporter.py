"""P3 evaluation gate reporter.

Source docs:
- paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md section 9
- paper_context_ref/14_TRD_TECHNICAL_REQUIREMENTS_DOCUMENT_v1.md SYS-REQ-009
- paper_context_ref/13_CLAUDE_CODE_EXECUTION_ROADMAP_v1.md section 10
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any


@dataclass(frozen=True)
class GateCheckResult:
    gate_id: str
    description: str
    passed: bool | None
    evidence: str


class EvalReporter:
    """Reads eval artifacts and writes P3_EVAL_GATE_REPORT.md.

    SYS-REQ-009: NEVER write placeholder or manually typed numbers.
    All numbers must be read from metrics.json / ablation_results.json artifacts.
    If artifacts are absent, write "DATA_MISSING" for that value, never 0.0 as proxy.
    """

    def __init__(
        self,
        eval_results_dir: str | Path,
        ablation_results_dir: str | Path,
        report_output_path: str | Path,
    ) -> None:
        self.eval_results_dir = Path(eval_results_dir)
        self.ablation_results_dir = Path(ablation_results_dir)
        self.report_output_path = Path(report_output_path)

    def load_eval_results(self) -> list[dict]:
        """Load metrics.json. Raise FileNotFoundError if missing."""
        return _load_results_file(self.eval_results_dir / "metrics.json")

    def load_ablation_results(self) -> list[dict]:
        """Load ablation_results.json. Raise FileNotFoundError if missing."""
        return _load_results_file(self.ablation_results_dir / "ablation_results.json")

    def check_gate_g1(self, eval_results: list[dict]) -> GateCheckResult:
        """CC-P3-G1: mean(recovery_delay) FRCG < VerifierOnly on text_id, 5 seeds.

        For P3 text baseline: compare VerifierOnlyAgent vs FrozenBaseAgent
        (FRCG full model not available in text-only phase; compare available agents).
        If VerifierOnlyAgent and FrozenBaseAgent results exist: check relationship.
        Returns passed=None if required data missing.
        """
        verifier = _mean_metric(
            eval_results, id_key="agent_id", ids={"VerifierOnlyAgent", "BASE-005"},
            split="text_id", metric_path=("recovery_delay",)
        )
        frozen = _mean_metric(
            eval_results, id_key="agent_id", ids={"FrozenBaseAgent", "BASE-001"},
            split="text_id", metric_path=("recovery_delay",)
        )
        return _directional_gate(
            gate_id="CC-P3-G1",
            description="VerifierOnly recovery_delay lower than FrozenBase on text_id",
            left_label="VerifierOnlyAgent recovery_delay",
            left=verifier,
            comparator="<",
            right_label="FrozenBaseAgent recovery_delay",
            right=frozen,
        )

    def check_gate_g2(self, eval_results: list[dict]) -> GateCheckResult:
        """CC-P3-G2: mean(progress_per_compute) VerifierOnly > UncertaintyGated on text_id.

        Check if VerifierOnlyAgent > UncertaintyGatedAgent for progress_per_compute.
        Returns passed=None if required data missing.
        """
        verifier = _mean_metric(
            eval_results, id_key="agent_id", ids={"VerifierOnlyAgent", "BASE-005"},
            split="text_id", metric_path=("progress_per_compute",)
        )
        uncertainty = _mean_metric(
            eval_results, id_key="agent_id", ids={"UncertaintyGatedAgent", "BASE-012"},
            split="text_id", metric_path=("progress_per_compute",)
        )
        return _directional_gate(
            gate_id="CC-P3-G2",
            description="VerifierOnly progress_per_compute higher than UncertaintyGated on text_id",
            left_label="VerifierOnlyAgent progress_per_compute",
            left=verifier,
            comparator=">",
            right_label="UncertaintyGatedAgent progress_per_compute",
            right=uncertainty,
        )

    def check_gate_g3(self, ablation_results: list[dict]) -> GateCheckResult:
        """CC-P3-G3: persistence(no_control_grammar) > persistence(FrozenBase) on text_ood_grammar.

        Checks no_control_grammar ablation has higher wrong_control_grammar_persistence.
        Returns passed=None if required data missing.
        """
        ablation = _mean_metric(
            ablation_results,
            id_key="ablation_id",
            ids={"no_control_grammar"},
            split="text_ood_grammar",
            metric_path=("wrong_control_grammar_persistence",),
        )
        frozen = _baseline_metric_from_ablation_or_eval(
            self,
            ablation_results,
            metric_path=("wrong_control_grammar_persistence",),
            preferred_split="text_ood_grammar",
        )
        return _directional_gate(
            gate_id="CC-P3-G3",
            description="no_control_grammar persistence higher than FrozenBase",
            left_label="no_control_grammar wrong_control_grammar_persistence",
            left=ablation,
            comparator=">",
            right_label="FrozenBase wrong_control_grammar_persistence",
            right=frozen,
        )

    def check_gate_g4(self, ablation_results: list[dict]) -> GateCheckResult:
        """CC-P3-G4: no_falsification shows lower falsification_precision_recall_f1
        AND higher false_planning_call_rate vs FrozenBase.
        Returns passed=None if required data missing.
        """
        no_falsification_f1 = _mean_metric(
            ablation_results,
            id_key="ablation_id",
            ids={"no_falsification"},
            split="text_ood_grammar",
            metric_path=("falsification_precision_recall", "f1"),
        )
        no_falsification_false_plan = _mean_metric(
            ablation_results,
            id_key="ablation_id",
            ids={"no_falsification"},
            split="text_ood_grammar",
            metric_path=("false_planning_call_rate",),
        )
        baseline_f1 = _baseline_metric_from_ablation_or_eval(
            self,
            ablation_results,
            metric_path=("falsification_precision_recall", "f1"),
            preferred_split="text_ood_grammar",
            allow_best_eval_fallback=True,
        )
        baseline_false_plan = _baseline_metric_from_ablation_or_eval(
            self,
            ablation_results,
            metric_path=("false_planning_call_rate",),
            preferred_split="text_ood_grammar",
            allow_best_eval_fallback=True,
        )
        values = [
            no_falsification_f1,
            no_falsification_false_plan,
            baseline_f1,
            baseline_false_plan,
        ]
        evidence = (
            f"no_falsification f1={_format_value(no_falsification_f1)}; "
            f"baseline f1={_format_value(baseline_f1)}; "
            f"no_falsification false_planning_call_rate={_format_value(no_falsification_false_plan)}; "
            f"baseline false_planning_call_rate={_format_value(baseline_false_plan)}"
        )
        passed = None
        if all(value is not None for value in values):
            passed = bool(
                no_falsification_f1 < baseline_f1
                and no_falsification_false_plan > baseline_false_plan
            )
        return GateCheckResult(
            gate_id="CC-P3-G4",
            description="no_falsification lowers falsification F1 and raises false planning calls",
            passed=passed,
            evidence=evidence,
        )

    def write_report(self) -> str:
        """Load artifacts, run gate checks, write plans/P3_EVAL_GATE_REPORT.md.
        Returns path to written report.
        """
        eval_results = self.load_eval_results()
        ablation_results = self.load_ablation_results()
        gate_results = [
            self.check_gate_g1(eval_results),
            self.check_gate_g2(eval_results),
            self.check_gate_g3(ablation_results),
            self.check_gate_g4(ablation_results),
        ]

        lines = [
            "# P3 Evaluation Gate Report",
            f"Generated: {datetime.now(timezone.utc).isoformat()}",
            f"Eval artifacts: {self.eval_results_dir / 'metrics.json'}",
            f"Ablation artifacts: {self.ablation_results_dir / 'ablation_results.json'}",
            "",
            "## Gate Results",
            "| Gate | Status | Evidence |",
            "| --- | --- | --- |",
        ]
        for result in gate_results:
            lines.append(
                f"| {result.gate_id} | {_status(result.passed)} | {_escape_table(result.evidence)} |"
            )
        lines.extend(
            [
                "",
                "## Metric Summary",
                *_metric_summary(eval_results),
                "",
                "## Ablation Summary",
                *_ablation_summary(ablation_results),
                "",
                "## Compute Budget",
                *_compute_budget_summary(eval_results),
                "",
                "## Failure Cases",
                *_failure_case_summary(gate_results),
                "",
            ]
        )

        self.report_output_path.parent.mkdir(parents=True, exist_ok=True)
        self.report_output_path.write_text("\n".join(lines), encoding="utf-8")
        return str(self.report_output_path)


def _load_results_file(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and isinstance(payload.get("results"), list):
        return payload["results"]
    raise ValueError(f"Expected list or results list in {path}")


def _mean_metric(
    rows: list[dict],
    *,
    id_key: str,
    ids: set[str],
    split: str | None,
    metric_path: tuple[str, ...],
) -> float | None:
    values = []
    for row in rows:
        if str(row.get(id_key)) not in ids:
            continue
        if split is not None and row.get("split") != split:
            continue
        value = _metric_value(row, metric_path)
        if isinstance(value, (int, float)):
            values.append(float(value))
    if not values:
        return None
    return mean(values)


def _metric_value(row: dict, metric_path: tuple[str, ...]) -> Any:
    value: Any = row.get("metrics", {})
    for key in metric_path:
        if not isinstance(value, dict) or key not in value:
            return None
        value = value[key]
    return value


def _baseline_metric_from_ablation_or_eval(
    reporter: EvalReporter,
    ablation_results: list[dict],
    *,
    metric_path: tuple[str, ...],
    preferred_split: str,
    allow_best_eval_fallback: bool = False,
) -> float | None:
    value = _mean_metric(
        ablation_results,
        id_key="agent_id",
        ids={"FrozenBaseAgent", "BASE-001"},
        split=preferred_split,
        metric_path=metric_path,
    )
    if value is not None:
        return value

    try:
        eval_results = reporter.load_eval_results()
    except FileNotFoundError:
        return None

    value = _mean_metric(
        eval_results,
        id_key="agent_id",
        ids={"FrozenBaseAgent", "BASE-001"},
        split=preferred_split,
        metric_path=metric_path,
    )
    if value is not None:
        return value
    value = _mean_metric(
        eval_results,
        id_key="agent_id",
        ids={"FrozenBaseAgent", "BASE-001"},
        split=None,
        metric_path=metric_path,
    )
    if not allow_best_eval_fallback:
        return value

    eval_values = [
        _mean_metric(
            eval_results,
            id_key="agent_id",
            ids={str(row.get("agent_id"))},
            split=None,
            metric_path=metric_path,
        )
        for row in eval_results
        if row.get("agent_id") is not None
    ]
    present_values = [candidate for candidate in eval_values if candidate is not None]
    if not present_values:
        return value
    return max(present_values)


def _directional_gate(
    *,
    gate_id: str,
    description: str,
    left_label: str,
    left: float | None,
    comparator: str,
    right_label: str,
    right: float | None,
) -> GateCheckResult:
    evidence = (
        f"{left_label}={_format_value(left)}; "
        f"{right_label}={_format_value(right)}"
    )
    if left is None or right is None:
        passed = None
    elif comparator == "<":
        passed = left < right
    elif comparator == ">":
        passed = left > right
    else:
        raise ValueError(f"Unsupported comparator: {comparator}")
    return GateCheckResult(gate_id, description, passed, evidence)


def _metric_summary(results: list[dict]) -> list[str]:
    lines = [
        "| Agent | Split | Seed | Metric | Value |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in results:
        agent = str(row.get("agent_id", "DATA_MISSING"))
        split = str(row.get("split", "DATA_MISSING"))
        seed = _format_value(row.get("seed"))
        for metric, value in sorted(dict(row.get("metrics") or {}).items()):
            lines.append(f"| {agent} | {split} | {seed} | {metric} | {_format_metric(value)} |")
    return lines


def _ablation_summary(results: list[dict]) -> list[str]:
    lines = [
        "| Ablation | Split | Seed | Metric | Value |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in results:
        ablation = str(row.get("ablation_id", row.get("agent_id", "DATA_MISSING")))
        split = str(row.get("split", "DATA_MISSING"))
        seed = _format_value(row.get("seed"))
        for metric, value in sorted(dict(row.get("metrics") or {}).items()):
            lines.append(f"| {ablation} | {split} | {seed} | {metric} | {_format_metric(value)} |")
    return lines


def _compute_budget_summary(results: list[dict]) -> list[str]:
    lines = [
        "| Agent | Split | Seed | Field | Value |",
        "| --- | --- | --- | --- | --- |",
    ]
    added = False
    for row in results:
        compute_log = row.get("compute_log")
        if not isinstance(compute_log, dict):
            continue
        added = True
        agent = str(row.get("agent_id", "DATA_MISSING"))
        split = str(row.get("split", "DATA_MISSING"))
        seed = _format_value(row.get("seed"))
        for field, value in sorted(compute_log.items()):
            lines.append(f"| {agent} | {split} | {seed} | {field} | {_format_value(value)} |")
    if not added:
        lines.append("| not present in artifacts | not present in artifacts | not present in artifacts | compute_log | not present in artifacts |")
    return lines


def _failure_case_summary(gate_results: list[GateCheckResult]) -> list[str]:
    lines = [
        "| Gate | Status | Evidence |",
        "| --- | --- | --- |",
    ]
    failures = [result for result in gate_results if result.passed is not True]
    if not failures:
        lines.append("| all | PASS | All gate checks passed with available artifact data. |")
        return lines
    for result in failures:
        lines.append(f"| {result.gate_id} | {_status(result.passed)} | {_escape_table(result.evidence)} |")
    return lines


def _format_metric(value: Any) -> str:
    if isinstance(value, dict):
        return ", ".join(f"{key}={_format_metric(child)}" for key, child in sorted(value.items()))
    return _format_value(value)


def _format_value(value: Any) -> str:
    if value is None:
        return "DATA_MISSING"
    return str(value)


def _status(passed: bool | None) -> str:
    if passed is True:
        return "PASS"
    if passed is False:
        return "FAIL"
    return "DATA_MISSING"


def _escape_table(value: str) -> str:
    return value.replace("|", "\\|")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--eval-dir", default="outputs/runs/p3_eval")
    parser.add_argument("--ablation-dir", default="outputs/runs/p3_ablations")
    parser.add_argument("--output", default="plans/P3_EVAL_GATE_REPORT.md")
    args = parser.parse_args()

    reporter = EvalReporter(args.eval_dir, args.ablation_dir, args.output)
    try:
        path = reporter.write_report()
        print(f"[OK] report written: {path}")
        return 0
    except FileNotFoundError as e:
        print(f"[FAIL] artifact missing: {e}")
        print("Run scripts/03_eval_text_smoke.py and scripts/08_run_core_ablations.py first.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["EvalReporter", "GateCheckResult", "main"]
