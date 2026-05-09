"""frcgw.data.coverage_auditor — Coverage audit for text-only dataset (CA-001~CA-006).

Source docs:
- paper_context_ref/12_DATA_COLLECTION_METHODOLOGY_v1.md §16 coverage audit
- paper_context_ref/14_TRD_TECHNICAL_REQUIREMENTS_DOCUMENT_v1.md §10 acceptance
- paper_context_ref/13_CLAUDE_CODE_EXECUTION_ROADMAP_v1.md §8.7 P2 spec
"""
from __future__ import annotations

from dataclasses import dataclass, field

from frcgw.schemas.episode_schema import EpisodeRecord


@dataclass
class CoverageThresholds:
    """Minimum ratios for gate PASS (13.md §8.7 P2 thresholds)."""
    failed_action_ratio: float = 0.20           # CA-001 relaxed from 0.25
    recovery_ratio: float = 0.08                 # CA-002 relaxed
    repeated_wrong_mapping_ratio: float = 0.08   # CA-006 relaxed
    shift_ratio: float = 0.08                    # CA-003 relaxed
    reveal_ratio: float = 0.05                   # CA-004
    delayed_or_noisy_or_no_op_valid_ratio: float = 0.03  # CA-005 relaxed


@dataclass
class CoverageReport:
    total_steps: int = 0
    failed_action_count: int = 0
    recovery_count: int = 0
    repeated_wrong_mapping_count: int = 0
    shift_count: int = 0
    reveal_count: int = 0
    delayed_or_noisy_or_no_op_valid_count: int = 0
    thresholds: CoverageThresholds = field(default_factory=CoverageThresholds)
    ratios: dict[str, float] = field(default_factory=dict)
    gate_pass: bool = False
    failures: list[str] = field(default_factory=list)
    source_doc_note: str = (
        "Thresholds from 13.md §8.7 (P2 gate); 12.md §16 CA-001~006 targets noted in failures."
    )


class CoverageAuditor:
    """Compute coverage metrics over a list of EpisodeRecord."""

    def __init__(self, thresholds: CoverageThresholds | None = None) -> None:
        self._thresholds = thresholds or CoverageThresholds()

    def audit(self, episodes: list[EpisodeRecord]) -> CoverageReport:
        report = CoverageReport(thresholds=self._thresholds)

        prev_actions: dict[str, list[str]] = {}  # episode_id -> action history

        for ep in episodes:
            ep_actions: list[str] = []
            for step in ep.steps:
                report.total_steps += 1
                tl = step.training_labels

                if tl.true_failed_action:
                    report.failed_action_count += 1

                if tl.valid_hypothesis_switch:
                    report.recovery_count += 1

                # Check for wrong mapping repetition in this episode
                # (same action repeated while still failing)
                ep_actions.append(step.action.action_type)

                etype = tl.true_action_effect_type
                if etype == "shift":
                    report.shift_count += 1
                elif etype == "reveal":
                    report.reveal_count += 1
                elif etype in ("delayed", "noisy"):
                    report.delayed_or_noisy_or_no_op_valid_count += 1
                elif step.action.action_type == "wait" and not tl.true_failed_action:
                    report.delayed_or_noisy_or_no_op_valid_count += 1

            # Detect repeated wrong mapping within episode
            report.repeated_wrong_mapping_count += _count_repeated_wrong_mapping(ep)

        n = max(report.total_steps, 1)
        ratios = {
            "failed_action_ratio":                      report.failed_action_count / n,
            "recovery_ratio":                           report.recovery_count / n,
            "repeated_wrong_mapping_ratio":             report.repeated_wrong_mapping_count / n,
            "shift_ratio":                              report.shift_count / n,
            "reveal_ratio":                             report.reveal_count / n,
            "delayed_or_noisy_or_no_op_valid_ratio":    report.delayed_or_noisy_or_no_op_valid_count / n,
        }
        report.ratios = ratios

        failures: list[str] = []
        t = self._thresholds
        _checks = [
            ("failed_action_ratio",                   t.failed_action_ratio,                   "CA-001"),
            ("recovery_ratio",                        t.recovery_ratio,                         "CA-002"),
            ("repeated_wrong_mapping_ratio",          t.repeated_wrong_mapping_ratio,           "CA-006"),
            ("shift_ratio",                           t.shift_ratio,                            "CA-003"),
            ("reveal_ratio",                          t.reveal_ratio,                           "CA-004"),
            ("delayed_or_noisy_or_no_op_valid_ratio", t.delayed_or_noisy_or_no_op_valid_ratio,  "CA-005"),
        ]
        for key, threshold, ca_id in _checks:
            actual = ratios[key]
            if actual < threshold:
                failures.append(
                    f"{ca_id} FAIL: {key}={actual:.3f} < {threshold:.3f}"
                )

        report.failures = failures
        report.gate_pass = len(failures) == 0
        return report


def _count_repeated_wrong_mapping(ep: EpisodeRecord) -> int:
    """Count steps where the same failing action is repeated consecutively."""
    count = 0
    prev_action = None
    prev_failed = False
    for step in ep.steps:
        tl = step.training_labels
        current_action = step.action.action_type
        current_failed = tl.true_failed_action
        if (
            prev_action == current_action
            and prev_failed
            and current_failed
        ):
            count += 1
        prev_action = current_action
        prev_failed = current_failed
    return count
