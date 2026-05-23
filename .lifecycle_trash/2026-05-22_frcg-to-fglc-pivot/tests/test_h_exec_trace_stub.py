"""Run 5.5 — h_exec trace contract tests.

Source MD: docs/orchestration/lr_alignment/06_unit_test_plan.md §4
Phase: 8/9 (Run 4/5.5 implementation)
Run: 5.5 — Group B 3 skips converted to real assertions (preflight gate).

Group B — h_exec Trace Contract Tests (C1 h_exec trace) — Run 5.5
Group G — Anti-Leakage Tests (all leakage safety) — Run 4A Priority 1
"""
import subprocess
import sys
from random import Random

import pytest


# ---------------------------------------------------------------------------
# Group B — h_exec Trace Contract Tests
# Connected claim: C1 (wrong-grammar persistence), C3 (falsification)
# Converted: Run 5.5 preflight (ActionRecord fields populated in collector L284-287)
# ---------------------------------------------------------------------------


def test_h_exec_trace_has_selected_hypothesis_id():
    """step log에서 selected_hypothesis_id가 실제로 populate됨을 검증한다.

    C1 연결: selected_hypothesis_id가 step log에 populate되어야 MET-PERSIST-001 계산 가능.
    Run 5.5: 실제 collect_episode로 toy episode 수집 후 ActionRecord.selected_hypothesis_id 검증.
    근거: reviewer2_20260516_R1.md Attack 2 REF-PROBLEM-012.
    """
    from frcgw.text_env.collector import CollectorConfig, collect_episode
    from frcgw.text_env.generator import EpisodeSpecGenerator
    from frcgw.text_env.policies import PolicyMixtureRunner

    spec = EpisodeSpecGenerator(seed=0).generate()
    runner = PolicyMixtureRunner(rng=Random(0))
    config = CollectorConfig()
    episode = collect_episode(spec, runner, Random(0), config)

    assert len(episode.steps) > 0, "Episode must have at least one step"
    for step in episode.steps:
        assert step.action.selected_hypothesis_id is not None, (
            f"selected_hypothesis_id must be populated at step {step.step_index}"
        )
        assert isinstance(step.action.selected_hypothesis_id, str), (
            "selected_hypothesis_id must be str"
        )
        assert step.action.selected_hypothesis_id != "", (
            "selected_hypothesis_id must not be empty string"
        )


def test_h_exec_is_predicted_trace_not_oracle_label():
    """HypothesisTrace.is_oracle_label이 기본값 False임을 확인한다.

    C1/C3 연결: h_exec는 model/agent 예측 trace. oracle label이 아님.
    Run 5.5: HypothesisTrace 직접 fixture 구성으로 검증 (ActionRecord is_oracle_label 필드 없음).
    Anti-leakage: EvaluationLabels.h_exec_id는 eval-only namespace — predicted trace와 분리.
    근거: step_schema.py HypothesisTrace L140 default=False.
    """
    from frcgw.falsification.lr_scorer import HypothesisTrace
    from frcgw.schemas.step_schema import EvaluationLabels

    # HypothesisTrace.is_oracle_label defaults to False
    trace = HypothesisTrace(
        selected_hypothesis_id="oracle_best_action_proxy",
        hypothesis_type="predicted",
        confidence=1.0,
        source="oracle_policy",
    )
    assert trace.is_oracle_label is False, (
        "HypothesisTrace.is_oracle_label must be False — predicted trace, not oracle label"
    )

    # Explicit False also accepted
    trace2 = HypothesisTrace(
        selected_hypothesis_id="wrong_grammar_proxy",
        hypothesis_type="predicted",
        confidence=0.7,
        source="wrong_grammar_policy",
        is_oracle_label=False,
    )
    assert trace2.is_oracle_label is False

    # EvaluationLabels.h_exec_id is eval-only (None in text env collector)
    # — separate namespace from predicted trace
    eval_labels = EvaluationLabels(h_exec_id=None)
    assert eval_labels.h_exec_id is None, (
        "EvaluationLabels.h_exec_id is None in text env — distinct from predicted trace namespace"
    )
    # selected_hypothesis_id is policy-space, not oracle-aligned h_exec_id
    assert trace.selected_hypothesis_id != eval_labels.h_exec_id or eval_labels.h_exec_id is None


def test_missing_h_exec_blocks_persistence_metric():
    """selected_hypothesis_id が空文字列のとき LR scorer degenerate=True + F_t=0.0 を返すこと,
    および compute_wrong_grammar_persistence_v1 がBLOCKEDを返すことを確認する。

    C1 연결: h_exec trace 없이는 persistence metric 계산 불가.
    Run 5.5: LikelihoodRatioFalsificationScorer L380-390 degenerate path 검증.
    근거: P3_EVAL.BLOCKED_planning_calls_zero.md, MET-PERSIST-001 구현.
    """
    from frcgw.evaluation.metrics import compute_wrong_grammar_persistence_v1
    from frcgw.falsification.lr_scorer import (
        HypothesisCandidate,
        HypothesisTrace,
        LikelihoodRatioFalsificationScorer,
        LikelihoodScore,
    )

    # 1. LR scorer returns degenerate=True when selected_hypothesis_id is empty
    trace = HypothesisTrace(
        selected_hypothesis_id="",  # empty string is falsy — triggers degenerate path
        hypothesis_type="predicted",
        confidence=0.0,
        source="test",
        is_oracle_label=False,
    )
    scorer = LikelihoodRatioFalsificationScorer()
    result = scorer.score(
        h_exec_trace=trace,
        exec_likelihood=LikelihoodScore(hypothesis_id="", loglik=-1.0),
        alt_likelihoods=[LikelihoodScore(hypothesis_id="alt1", loglik=-0.5)],
        alt_candidates=[HypothesisCandidate(
            hypothesis_id="alt1",
            regime_id="r1",
            control_grammar_id="g1",
            prior_logprob=-0.5,
        )],
    )
    assert result.degenerate is True, (
        "LR scorer must return degenerate=True when h_exec_id is empty/missing"
    )
    assert result.F_t == 0.0, (
        "LR scorer must return F_t=0.0 when degenerate"
    )

    # 2. MET-PERSIST-001 returns BLOCKED when episodes lack eval labels
    episodes_without_eval_labels = [{}]  # dict with no evaluation_labels attribute
    persistence = compute_wrong_grammar_persistence_v1(episodes_without_eval_labels)
    assert persistence["status"] == "BLOCKED", (
        "compute_wrong_grammar_persistence_v1 must return BLOCKED when eval labels missing"
    )
    assert persistence["count_blocked"] == 1
    assert persistence["mean_persistence"] is None


# ---------------------------------------------------------------------------
# Group G — Anti-Leakage Tests (Priority 1, Run 4A)
# Connected claim: all (C1~C6)
# ---------------------------------------------------------------------------


def test_selected_hypothesis_not_in_forbidden_agent_fields():
    """selected_hypothesis_id가 FORBIDDEN_AGENT_FIELDS에 포함되지 않음을 확인한다.

    Anti-leakage: selected_hypothesis_id는 model 선택 필드 — forbidden 목록에 없음.
    Run 4A: visibility.py::FORBIDDEN_AGENT_FIELDS에 selected_hypothesis_id 부재 검증.
    근거: paper_context_ref/06_DATA_SCHEMA_AND_LABELING.md §4.
    """
    from frcgw.schemas.visibility import FORBIDDEN_AGENT_FIELDS

    assert "selected_hypothesis_id" not in FORBIDDEN_AGENT_FIELDS, (
        "selected_hypothesis_id must NOT be in FORBIDDEN_AGENT_FIELDS — it is a predicted trace, not oracle label"
    )
    # Also verify related predicted-trace fields are not forbidden
    for field_name in (
        "selected_hypothesis_type",
        "selected_hypothesis_confidence",
        "selected_hypothesis_source",
    ):
        assert field_name not in FORBIDDEN_AGENT_FIELDS, (
            f"{field_name} must not be in FORBIDDEN_AGENT_FIELDS"
        )


def test_true_control_grammar_not_in_inference_input():
    """EvidenceFeatures 인스턴스에 true_control_grammar 필드가 없음을 확인하고,
    HypothesisCandidate.metadata에 true_control_grammar가 있으면
    EvidenceLikelihood가 HiddenLabelLeakageError를 raise하는지 검증한다.

    Anti-leakage: true_control_grammar는 FORBIDDEN_AGENT_FIELDS 중 하나.
    Run 4A: 두 가지 경로 모두 검증.
    근거: src/frcgw/schemas/visibility.py::FORBIDDEN_AGENT_FIELDS.
    """
    from frcgw.falsification.lr_scorer import EvidenceFeatures, EvidenceLikelihood, HypothesisCandidate
    from frcgw.schemas.visibility import HiddenLabelLeakageError

    # EvidenceFeatures must have no true_control_grammar field
    ef = EvidenceFeatures(
        effect_type="test",
        dom_diff_summary="",
        accessibility_diff_summary="",
        visual_diff_score=0.0,
        precondition_status="unknown",
        no_effect_flag=False,
        delayed_effect_flag=False,
        noisy_observation_flag=False,
        progress_delta=0.0,
        failure_reason=None,
    )
    assert not hasattr(ef, "true_control_grammar"), (
        "EvidenceFeatures must not have true_control_grammar attribute"
    )

    # EvidenceLikelihood must raise HiddenLabelLeakageError if metadata contains true_control_grammar
    h_with_leakage = HypothesisCandidate(
        hypothesis_id="h_leak",
        regime_id="r1",
        control_grammar_id="g1",
        prior_logprob=0.0,
        metadata={"true_control_grammar": "direct_search"},  # FORBIDDEN
    )
    with pytest.raises(HiddenLabelLeakageError):
        EvidenceLikelihood().score(ef, h_with_leakage, None, None)


def test_true_regime_not_in_inference_input():
    """EvidenceFeatures 인스턴스에 true_regime 필드가 없음을 확인하고,
    HypothesisCandidate.metadata에 true_regime이 있으면
    EvidenceLikelihood가 HiddenLabelLeakageError를 raise하는지 검증한다.

    Anti-leakage: true_regime은 FORBIDDEN_AGENT_FIELDS 중 하나.
    Run 4A: 동일 패턴, true_regime.
    근거: src/frcgw/schemas/visibility.py::FORBIDDEN_AGENT_FIELDS.
    """
    from frcgw.falsification.lr_scorer import EvidenceFeatures, EvidenceLikelihood, HypothesisCandidate
    from frcgw.schemas.visibility import HiddenLabelLeakageError

    ef = EvidenceFeatures(
        effect_type="test",
        dom_diff_summary="",
        accessibility_diff_summary="",
        visual_diff_score=0.0,
        precondition_status="unknown",
        no_effect_flag=False,
        delayed_effect_flag=False,
        noisy_observation_flag=False,
        progress_delta=0.0,
        failure_reason=None,
    )
    assert not hasattr(ef, "true_regime"), (
        "EvidenceFeatures must not have true_regime attribute"
    )

    h_with_leakage = HypothesisCandidate(
        hypothesis_id="h_leak",
        regime_id="r1",
        control_grammar_id="g1",
        prior_logprob=0.0,
        metadata={"true_regime": "modal_mode"},  # FORBIDDEN
    )
    with pytest.raises(HiddenLabelLeakageError):
        EvidenceLikelihood().score(ef, h_with_leakage, None, None)


def test_counterfactual_table_not_in_inference_input():
    """EvidenceFeatures 인스턴스에 counterfactual_action_effects 필드가 없음을 확인하고,
    HypothesisCandidate.metadata에 counterfactual_action_effects가 있으면
    EvidenceLikelihood가 CounterfactualLeakageError를 raise하는지 검증한다.

    Anti-leakage: counterfactual_action_effects는 FORBIDDEN_AGENT_FIELDS.
    Run 4A: CounterfactualLeakageError raise 검증.
    근거: src/frcgw/schemas/visibility.py::CounterfactualLeakageError.
    """
    from frcgw.falsification.lr_scorer import EvidenceFeatures, EvidenceLikelihood, HypothesisCandidate
    from frcgw.schemas.visibility import CounterfactualLeakageError

    ef = EvidenceFeatures(
        effect_type="test",
        dom_diff_summary="",
        accessibility_diff_summary="",
        visual_diff_score=0.0,
        precondition_status="unknown",
        no_effect_flag=False,
        delayed_effect_flag=False,
        noisy_observation_flag=False,
        progress_delta=0.0,
        failure_reason=None,
    )
    assert not hasattr(ef, "counterfactual_action_effects"), (
        "EvidenceFeatures must not have counterfactual_action_effects attribute"
    )

    h_with_counterfactual = HypothesisCandidate(
        hypothesis_id="h_cf",
        regime_id="r1",
        control_grammar_id="g1",
        prior_logprob=0.0,
        metadata={"counterfactual_action_effects": {"click": "success"}},  # FORBIDDEN
    )
    with pytest.raises(CounterfactualLeakageError):
        EvidenceLikelihood().score(ef, h_with_counterfactual, None, None)


def test_future_evidence_not_available_to_scorer():
    """EvidenceFeatures にstep_index フィールドがなく、
    future evidence leakage が構造的に不可能なことを確認する。

    Anti-leakage: e_t는 현재 step의 observed evidence만 포함.
    EvidenceFeatures에 step_index 필드가 없으므로 future reference 구조적 불가.
    Run 4A: EvidenceFeatures 필드 목록에 step_index 없음 검증.
    근거: 05_lr_implementation_contract.md §4.
    """
    from frcgw.falsification.lr_scorer import EvidenceFeatures
    from dataclasses import fields

    field_names = {f.name for f in fields(EvidenceFeatures)}

    # step_index가 없으면 future evidence reference 구조적으로 불가
    assert "step_index" not in field_names, (
        "EvidenceFeatures must not have step_index — future evidence access must be structurally impossible"
    )
    # 다른 future-reference 가능 필드도 없어야 함
    for forbidden_future_field in ("future_effect", "next_effect", "future_evidence"):
        assert forbidden_future_field not in field_names, (
            f"EvidenceFeatures must not have {forbidden_future_field}"
        )


def test_forbidden_field_mirror_sync_still_green():
    """tests/test_forbidden_field_mirror_sync.py가 Run 4 이후에도 green 상태임을 확인한다.

    lr_scorer.py 및 step_schema.py 변경이 visibility.py::FORBIDDEN_AGENT_FIELDS를
    변경하지 않았음을 간접 확인한다.
    Run 4A: subprocess로 mirror sync test 실행.
    근거: src/frcgw/schemas/visibility.py (수정 금지, 사용자 승인 없이).
    """
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_forbidden_field_mirror_sync.py", "-q", "--tb=short"],
        capture_output=True,
        text=True,
        cwd=str(__import__("pathlib").Path(__file__).parent.parent),
    )
    assert result.returncode == 0, (
        f"test_forbidden_field_mirror_sync.py FAILED after Run 4 changes:\n"
        f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )
