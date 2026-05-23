"""P1 gate test: LeakageAuditor detects forbidden and counterfactual fields.

Source docs:
- paper_context_ref/06_DATA_SCHEMA_AND_LABELING.md §14-15
- paper_context_ref/15_TDD_TECHNICAL_DESIGN_DOCUMENT_v1.md §10.5
"""
from __future__ import annotations

import pytest
from frcgw.data.leakage_auditor import LeakageAuditor, AuditReport
from frcgw.schemas.step_schema import PublicObservation


def test_clean_observation_passes():
    auditor = LeakageAuditor()
    obs = PublicObservation(instruction="navigate to settings")
    report = auditor.audit_agent_input(obs)
    assert report.passed, report


def test_clean_dict_passes():
    auditor = LeakageAuditor()
    report = auditor.audit_agent_input({"instruction": "submit", "dom": "<div>"})
    assert report.passed


def test_hidden_label_in_dict_fails():
    auditor = LeakageAuditor()
    report = auditor.audit_agent_input({"instruction": "click", "true_regime": "modal"})
    assert not report.passed
    assert "true_regime" in report.forbidden_found


def test_counterfactual_in_dict_fails():
    auditor = LeakageAuditor()
    report = auditor.audit_agent_input({"instruction": "click", "counterfactual_action_effects": []})
    assert not report.passed
    assert "counterfactual_action_effects" in report.counterfactual_found


def test_batch_with_split_id_fails():
    auditor = LeakageAuditor()
    report = auditor.audit_batch({"input": "text", "split_id": "train"})
    assert not report.passed
    assert "split_id" in report.forbidden_found


def test_batch_with_seed_fails():
    auditor = LeakageAuditor()
    report = auditor.audit_batch({"input": "x", "seed": 42})
    assert not report.passed


def test_assert_clean_raises_on_forbidden():
    auditor = LeakageAuditor()
    with pytest.raises(ValueError, match="forbidden fields"):
        auditor.assert_clean({"instruction": "x", "true_control_grammar": "g1"})


def test_assert_clean_passes_on_safe():
    auditor = LeakageAuditor()
    auditor.assert_clean({"instruction": "navigate", "dom": "<div>login</div>"})


def test_multiple_forbidden_fields_all_reported():
    auditor = LeakageAuditor()
    report = auditor.audit_agent_input({"true_regime": "r1", "split_id": "train", "seed": 42})
    assert not report.passed
    assert "true_regime" in report.forbidden_found
    assert "split_id" in report.forbidden_found
    assert "seed" in report.forbidden_found


def test_audit_report_source_field():
    auditor = LeakageAuditor()
    report = auditor.audit_agent_input({"x": 1}, source="test_source")
    assert report.source == "test_source"


def test_audit_report_is_dataclass():
    report = AuditReport(source="test", passed=True)
    assert report.passed
    assert report.forbidden_found == []
    assert report.counterfactual_found == []
