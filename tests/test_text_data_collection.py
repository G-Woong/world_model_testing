"""Tests for episode/step schema validation, JSONL roundtrip, manifest, audit reports."""
from __future__ import annotations

import dataclasses
import json
import random
import tempfile
from pathlib import Path

import pytest

from frcgw.data.coverage_auditor import CoverageAuditor, CoverageThresholds
from frcgw.data.leakage_auditor import LeakageAuditor
from frcgw.data.shard_exporter import ShardExporter
from frcgw.schemas.validation import (
    validate_episode_schema,
    validate_visibility_contract,
)
from frcgw.text_env.collector import CollectorConfig, collect_episode
from frcgw.text_env.generator import EpisodeSpecGenerator, TaskFamily
from frcgw.text_env.policies import PolicyMixtureRunner
from frcgw.text_env.replay import ReplayValidator


def _make_episode(family: str = TaskFamily.MODAL_BLOCKER, seed: int = 1):
    gen = EpisodeSpecGenerator(seed=seed)
    spec = gen.generate(family=family)
    config = CollectorConfig(split_id="train")
    runner = PolicyMixtureRunner(rng=random.Random(seed))
    return collect_episode(spec, runner, random.Random(spec.seed), config), spec


class TestSchemaValidation:
    def test_episode_passes_validate_episode_schema(self):
        ep, _ = _make_episode()
        result = validate_episode_schema(ep)
        assert result.passed, result.errors

    def test_episode_passes_validate_visibility_contract(self):
        ep, _ = _make_episode()
        result = validate_visibility_contract(ep)
        assert result.passed, result.errors

    def test_counterfactuals_are_empty_list(self):
        ep, _ = _make_episode()
        for step in ep.steps:
            assert step.counterfactuals == [], (
                f"P2 must leave counterfactuals empty; got {step.counterfactuals}"
            )

    def test_all_steps_have_required_fields(self):
        ep, _ = _make_episode()
        for step in ep.steps:
            assert step.step_id
            assert step.episode_id
            assert step.public_observation is not None
            assert step.training_labels is not None
            assert step.evaluation_labels is not None
            assert step.audit_metadata is not None


class TestJSONLRoundtrip:
    def test_episode_serializes_and_restores_fields(self):
        ep, _ = _make_episode(TaskFamily.SEARCH_FORM, seed=5)
        raw = dataclasses.asdict(ep)
        restored_str = json.dumps(raw, ensure_ascii=False)
        restored = json.loads(restored_str)
        assert restored["episode_id"] == ep.episode_id
        assert restored["task_family"] == ep.task_family
        assert len(restored["steps"]) == len(ep.steps)

    def test_shard_exporter_writes_jsonl_line(self):
        ep, _ = _make_episode(seed=9)
        with tempfile.TemporaryDirectory() as tmpdir:
            exporter = ShardExporter(
                output_dir=Path(tmpdir),
                dataset_version="0.1",
                schema_version="schema-06-v0.1",
            )
            exporter.write_episode("train", ep)
            shard = Path(tmpdir) / "train.jsonl"
            assert shard.exists()
            lines = shard.read_text(encoding="utf-8").strip().splitlines()
            assert len(lines) == 1
            loaded = json.loads(lines[0])
            assert loaded["episode_id"] == ep.episode_id


class TestManifestAndAuditReports:
    def test_write_manifest_creates_files(self):
        ep, _ = _make_episode(seed=13)
        with tempfile.TemporaryDirectory() as tmpdir:
            exporter = ShardExporter(
                output_dir=Path(tmpdir),
                dataset_version="0.1",
                schema_version="schema-06-v0.1",
            )
            exporter.write_episode("train", ep)

            auditor = CoverageAuditor()
            cov_report = auditor.audit([ep])

            leak_auditor = LeakageAuditor()
            from frcgw.data.leakage_auditor import AuditReport
            leak_report = leak_auditor.audit_agent_input(
                [s.public_observation for s in ep.steps], source="test_batch"
            )
            exporter.write_manifest(cov_report, leak_report)

            assert (Path(tmpdir) / "manifest.json").exists()
            assert (Path(tmpdir) / "audits" / "coverage_report.json").exists()
            assert (Path(tmpdir) / "audits" / "leakage_report.json").exists()

    def test_manifest_contains_split_counts(self):
        ep, _ = _make_episode(seed=17)
        with tempfile.TemporaryDirectory() as tmpdir:
            exporter = ShardExporter(
                output_dir=Path(tmpdir),
                dataset_version="0.1",
                schema_version="schema-06-v0.1",
            )
            exporter.write_episode("train", ep)
            exporter.write_episode("valid", ep)

            auditor = CoverageAuditor()
            cov_report = auditor.audit([ep])
            from frcgw.data.leakage_auditor import LeakageAuditor
            leak_auditor = LeakageAuditor()
            leak_report = leak_auditor.audit_agent_input(
                [s.public_observation for s in ep.steps], source="test_batch"
            )
            exporter.write_manifest(cov_report, leak_report)

            manifest = json.loads(
                (Path(tmpdir) / "manifest.json").read_text(encoding="utf-8")
            )
            assert manifest["splits"]["train"] == 1
            assert manifest["splits"]["valid"] == 1
            assert manifest["total_episodes"] == 2
