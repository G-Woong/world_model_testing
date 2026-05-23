"""frcgw.data.shard_exporter — JSONL shard exporter and manifest writer.

Source docs:
- paper_context_ref/06_DATA_SCHEMA_AND_LABELING.md §14 export
- paper_context_ref/12_DATA_COLLECTION_METHODOLOGY_v1.md §13 scale
- paper_context_ref/14_TRD_TECHNICAL_REQUIREMENTS_DOCUMENT_v1.md §6 data
"""
from __future__ import annotations

import dataclasses
import json
from datetime import datetime, timezone
from pathlib import Path

from frcgw.data.coverage_auditor import CoverageReport
from frcgw.data.leakage_auditor import AuditReport, LeakageAuditor
from frcgw.schemas.episode_schema import EpisodeRecord


def _to_dict(obj) -> dict:
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return dataclasses.asdict(obj)
    raise TypeError(f"Cannot serialize {type(obj)}")


class ShardExporter:
    """Serialises EpisodeRecord objects to per-split JSONL files.

    Each line is one episode (all steps inline).
    LeakageAuditor.audit_agent_input() is called on each PublicObservation
    before the line is written.
    """

    def __init__(
        self,
        output_dir: Path,
        dataset_version: str,
        schema_version: str,
    ) -> None:
        self._out = Path(output_dir)
        self._dataset_version = dataset_version
        self._schema_version = schema_version
        self._leakage_auditor = LeakageAuditor()
        self._counts: dict[str, int] = {}
        self._out.mkdir(parents=True, exist_ok=True)
        (self._out / "audits").mkdir(exist_ok=True)
        (self._out / "metadata").mkdir(exist_ok=True)

    def write_episode(self, split_id: str, episode: EpisodeRecord) -> None:
        """Append one episode to the appropriate split JSONL file.

        Raises if any step's public_observation contains forbidden fields.
        """
        # Leakage check on every step's public obs
        for step in episode.steps:
            result = self._leakage_auditor.audit_agent_input(step.public_observation)
            if not result.passed:
                raise RuntimeError(
                    f"Leakage detected in episode {episode.episode_id} "
                    f"step {step.step_index}: forbidden={result.forbidden_found} "
                    f"counterfactual={result.counterfactual_found}"
                )

        shard_path = self._out / f"{split_id}.jsonl"
        with shard_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(_to_dict(episode), ensure_ascii=False) + "\n")

        self._counts[split_id] = self._counts.get(split_id, 0) + 1

    def write_manifest(
        self,
        coverage_report: CoverageReport,
        leakage_report: AuditReport,
    ) -> None:
        """Write manifest.json plus audit report files."""
        manifest = {
            "dataset_version": self._dataset_version,
            "schema_version": self._schema_version,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "splits": self._counts,
            "total_episodes": sum(self._counts.values()),
            "coverage_gate_pass": coverage_report.gate_pass,
            "leakage_gate_pass": leakage_report.passed,
        }
        manifest_path = self._out / "manifest.json"
        manifest_path.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
        )

        cov_path = self._out / "audits" / "coverage_report.json"
        cov_path.write_text(
            json.dumps(dataclasses.asdict(coverage_report), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        leak_path = self._out / "audits" / "leakage_report.json"
        leak_path.write_text(
            json.dumps(dataclasses.asdict(leakage_report), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
