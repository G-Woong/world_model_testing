"""Tests for repair metric artifact keys and diagnose fire rules.

Source: docs/STEP11_PLAN.md §I.2 TASK D6
Verifies:
  - OOD_TOO_HARD fire rule triggers when ood_id_nll_diff > 2.0
  - EVAL_NOISE_HIGH fire rule triggers when eval_ci95_over_effect_size > 1.0
  - OOD_TOO_HARD candidates exist in CANDIDATE_TABLE
  - EVAL_NOISE_HIGH candidates exist in CANDIDATE_TABLE
  - STAGE1_CANONICAL_METRIC_KEYS contains id_nll, ood_mass_nll, ood_friction_nll, ood_id_nll_diff
"""

from __future__ import annotations

import pytest


class TestCanonicalMetricKeys:
    def test_stage1_has_id_nll(self):
        from fglc.evaluation.metrics import STAGE1_CANONICAL_METRIC_KEYS
        assert "id_nll" in STAGE1_CANONICAL_METRIC_KEYS

    def test_stage1_has_ood_mass_nll(self):
        from fglc.evaluation.metrics import STAGE1_CANONICAL_METRIC_KEYS
        assert "ood_mass_nll" in STAGE1_CANONICAL_METRIC_KEYS

    def test_stage1_has_ood_friction_nll(self):
        from fglc.evaluation.metrics import STAGE1_CANONICAL_METRIC_KEYS
        assert "ood_friction_nll" in STAGE1_CANONICAL_METRIC_KEYS

    def test_stage1_has_ood_id_nll_diff(self):
        from fglc.evaluation.metrics import STAGE1_CANONICAL_METRIC_KEYS
        assert "ood_id_nll_diff" in STAGE1_CANONICAL_METRIC_KEYS


class TestOODTooHardFireRule:
    def test_fires_when_gap_exceeds_2(self):
        from fglc.repair.diagnose import diagnose
        from fglc.repair.taxonomy import FailureCauseId

        metrics = {"ood_id_nll_diff": 2.5, "id_nll": 0.3, "stagnant_epochs": 0}
        causes = diagnose(metrics, "R2")
        assert FailureCauseId.OOD_TOO_HARD in causes

    def test_does_not_fire_below_threshold(self):
        from fglc.repair.diagnose import diagnose
        from fglc.repair.taxonomy import FailureCauseId

        metrics = {"ood_id_nll_diff": 1.5, "id_nll": 0.3, "stagnant_epochs": 0}
        causes = diagnose(metrics, "R2")
        assert FailureCauseId.OOD_TOO_HARD not in causes

    def test_fires_at_exactly_2_dot_1(self):
        from fglc.repair.diagnose import diagnose
        from fglc.repair.taxonomy import FailureCauseId

        metrics = {"ood_id_nll_diff": 2.1, "id_nll": 0.3, "stagnant_epochs": 0}
        causes = diagnose(metrics, "R2")
        assert FailureCauseId.OOD_TOO_HARD in causes

    def test_no_diff_key_no_fire(self):
        from fglc.repair.diagnose import diagnose
        from fglc.repair.taxonomy import FailureCauseId

        metrics = {"id_nll": 0.3, "stagnant_epochs": 0}
        causes = diagnose(metrics, "R2")
        assert FailureCauseId.OOD_TOO_HARD not in causes


class TestEvalNoiseHighFireRule:
    def test_fires_when_ci_exceeds_effect_size(self):
        from fglc.repair.diagnose import diagnose
        from fglc.repair.taxonomy import FailureCauseId

        metrics = {"eval_ci95_over_effect_size": 1.5, "id_nll": 0.3, "stagnant_epochs": 0}
        causes = diagnose(metrics, "R3")
        assert FailureCauseId.EVAL_NOISE_HIGH in causes

    def test_does_not_fire_below_threshold(self):
        from fglc.repair.diagnose import diagnose
        from fglc.repair.taxonomy import FailureCauseId

        metrics = {"eval_ci95_over_effect_size": 0.5, "id_nll": 0.3, "stagnant_epochs": 0}
        causes = diagnose(metrics, "R3")
        assert FailureCauseId.EVAL_NOISE_HIGH not in causes

    def test_no_key_no_fire(self):
        from fglc.repair.diagnose import diagnose
        from fglc.repair.taxonomy import FailureCauseId

        metrics = {"id_nll": 0.3, "stagnant_epochs": 0}
        causes = diagnose(metrics, "R3")
        assert FailureCauseId.EVAL_NOISE_HIGH not in causes


class TestCandidatesForNewCauses:
    def test_ood_too_hard_candidates_exist(self):
        from fglc.repair.candidates import CANDIDATE_TABLE
        from fglc.repair.taxonomy import FailureCauseId

        assert FailureCauseId.OOD_TOO_HARD in CANDIDATE_TABLE
        cands = CANDIDATE_TABLE[FailureCauseId.OOD_TOO_HARD]
        assert len(cands) >= 2

    def test_eval_noise_high_candidates_exist(self):
        from fglc.repair.candidates import CANDIDATE_TABLE
        from fglc.repair.taxonomy import FailureCauseId

        assert FailureCauseId.EVAL_NOISE_HIGH in CANDIDATE_TABLE
        cands = CANDIDATE_TABLE[FailureCauseId.EVAL_NOISE_HIGH]
        assert len(cands) >= 2

    def test_ood_too_hard_applicable_r2(self):
        from fglc.repair.candidates import candidates_for
        from fglc.repair.taxonomy import FailureCauseId

        cands = candidates_for([FailureCauseId.OOD_TOO_HARD], "R2")
        assert len(cands) >= 1

    def test_eval_noise_high_applicable_r3(self):
        from fglc.repair.candidates import candidates_for
        from fglc.repair.taxonomy import FailureCauseId

        cands = candidates_for([FailureCauseId.EVAL_NOISE_HIGH], "R3")
        assert len(cands) >= 1
