"""Run 4 — LR scorer contract tests.

Source MD: docs/orchestration/lr_alignment/06_unit_test_plan.md §4
Phase: 8/9 (Run 4 implementation)
Run: 4 — Priority 1 tests converted to real assertions.

Group A — Stub Import and Signature Tests (C3 stub contract)
Group C — LR Falsification Tests (C3 LR vs BCE/uncertainty)
"""
import ast
import importlib
import inspect
import sys

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_evidence(
    effect_type="no_effect",
    no_effect_flag=True,
    precondition_status="unknown",
    progress_delta=0.0,
    noisy_observation_flag=False,
    delayed_effect_flag=False,
):
    from frcgw.falsification.lr_scorer import EvidenceFeatures
    return EvidenceFeatures(
        effect_type=effect_type,
        dom_diff_summary="",
        accessibility_diff_summary="",
        visual_diff_score=0.0,
        precondition_status=precondition_status,
        no_effect_flag=no_effect_flag,
        delayed_effect_flag=delayed_effect_flag,
        noisy_observation_flag=noisy_observation_flag,
        progress_delta=progress_delta,
        failure_reason=None,
    )


def _make_candidate(hypothesis_id, metadata=None):
    from frcgw.falsification.lr_scorer import HypothesisCandidate
    return HypothesisCandidate(
        hypothesis_id=hypothesis_id,
        regime_id="r1",
        control_grammar_id="g1",
        prior_logprob=-0.5,
        metadata=metadata or {},
    )


def _make_trace(hypothesis_id, confidence=0.7, is_oracle_label=False):
    from frcgw.falsification.lr_scorer import HypothesisTrace
    return HypothesisTrace(
        selected_hypothesis_id=hypothesis_id,
        hypothesis_type="predicted",
        confidence=confidence,
        source="test",
        is_oracle_label=is_oracle_label,
    )


# ---------------------------------------------------------------------------
# Group A — Stub Import and Signature Tests
# Connected claim: C3 (falsification mechanism)
# ---------------------------------------------------------------------------


def test_stub_imports():
    """lr_scorer.py가 14개 symbol 모두 torch/numpy 없이 import 가능한지 확인한다.

    C3 연결: LR scorer 구현 경계 계약.
    Run 4: 실제 import 정상 동작 검증.
    """
    from frcgw.falsification.lr_scorer import (  # noqa: F401
        EvidenceFeatures,
        FalsificationResult,
        GateDecision,
        GrammarConditionedRewrite,
        HypothesisCandidate,
        HypothesisTrace,
        LikelihoodRatioFalsificationScorer,
        LikelihoodScore,
        PosteriorState,
        PosteriorUpdateResult,
        PosteriorUpdater,
        RewriteDecision,
        DecisionRelevanceGate,
        EvidenceLikelihood,
    )
    # All 14 symbols importable without torch/numpy/pandas/sklearn
    assert EvidenceFeatures is not None
    assert LikelihoodRatioFalsificationScorer is not None


def test_required_dataclasses_exist():
    """9개 dataclass 인스턴스 생성 + 필드 타입 검증.

    C3 연결: 14개 symbol의 signature 계약.
    Run 4: 실제 인스턴스 생성 + 필드 타입 검증.
    """
    from frcgw.falsification.lr_scorer import (
        EvidenceFeatures,
        FalsificationResult,
        GateDecision,
        HypothesisCandidate,
        HypothesisTrace,
        LikelihoodScore,
        PosteriorState,
        PosteriorUpdateResult,
        RewriteDecision,
    )

    ef = EvidenceFeatures(
        effect_type="test_effect",
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
    assert isinstance(ef.effect_type, str)
    assert isinstance(ef.visual_diff_score, float)
    assert ef.failure_reason is None

    ht = HypothesisTrace(
        selected_hypothesis_id="h1",
        hypothesis_type="wrong",
        confidence=0.5,
        source="test",
    )
    assert isinstance(ht.selected_hypothesis_id, str)
    assert ht.is_oracle_label is False  # default must be False

    hc = HypothesisCandidate(
        hypothesis_id="h_alt",
        regime_id="r1",
        control_grammar_id="g1",
        prior_logprob=-0.5,
    )
    assert isinstance(hc.metadata, dict)

    ls = LikelihoodScore(hypothesis_id="h1", loglik=1.5)
    assert isinstance(ls.loglik, float)
    assert isinstance(ls.diagnostics, dict)

    fr = FalsificationResult(
        h_exec_id="h_exec",
        best_h_alt_id="h_alt",
        loglik_exec=0.0,
        loglik_alt_best=1.5,
        F_t=1.5,
        margin=0.0,
        degenerate=False,
    )
    assert isinstance(fr.F_t, float)
    assert isinstance(fr.degenerate, bool)

    ps = PosteriorState(
        posterior_by_hypothesis={"h1": 0.6, "h2": 0.4},
        entropy=0.67,
        top_hypothesis_id="h1",
    )
    assert isinstance(ps.posterior_by_hypothesis, dict)

    pur = PosteriorUpdateResult(
        posterior_before=ps,
        posterior_after=ps,
        posterior_shift=0.1,
        adopted_hypothesis_id="h1",
        switch_recommended=False,
    )
    assert isinstance(pur.switch_recommended, bool)

    gd = GateDecision(
        G_t=True,
        planning_allowed=True,
        decision_relevance_delta=0.5,
        action_switch_probability=0.8,
        compute_cost=0.1,
        gate_reason="PASS_ALL_4",
    )
    assert isinstance(gd.G_t, bool)

    rd = RewriteDecision(
        intent_id="i1",
        base_action_id="click",
        selected_hypothesis_id="h1",
        executable_action_id="click__rewritten_by__h1",
        rewrite_triggered=True,
        rewrite_confidence=0.8,
        fallback_used=False,
        rewrite_reason="applied",
    )
    assert isinstance(rd.rewrite_triggered, bool)


def test_required_component_classes_exist():
    """5개 component class 인스턴스 생성 + method 존재 검증.

    C3 연결: LR scorer I/O contract 계약.
    Run 4: 인스턴스 생성 + method signature 검증.
    """
    from frcgw.falsification.lr_scorer import (
        DecisionRelevanceGate,
        EvidenceLikelihood,
        GrammarConditionedRewrite,
        LikelihoodRatioFalsificationScorer,
        PosteriorUpdater,
    )

    el = EvidenceLikelihood()
    assert hasattr(el, "score") and callable(el.score)

    lrf = LikelihoodRatioFalsificationScorer()
    assert hasattr(lrf, "score") and callable(lrf.score)

    pu = PosteriorUpdater()
    assert hasattr(pu, "update") and callable(pu.update)

    drg = DecisionRelevanceGate()
    assert hasattr(drg, "decide") and callable(drg.decide)

    gcr = GrammarConditionedRewrite()
    assert hasattr(gcr, "rewrite") and callable(gcr.rewrite)


def test_methods_raise_not_implemented():
    """stub은 NotImplementedError를 유지하고, lr_scorer는 실제 결과를 반환하는지 검증.

    C3 연결: stub 경계 계약 vs 실제 구현 경계.
    Run 4: stub NotImplementedError + lr_scorer 실 결과 둘 다 검증.
    """
    # Stub still raises NotImplementedError
    from frcgw.falsification.lr_scorer_stub import (
        EvidenceLikelihood as StubEL,
        LikelihoodRatioFalsificationScorer as StubLRF,
        PosteriorUpdater as StubPU,
        DecisionRelevanceGate as StubDRG,
        GrammarConditionedRewrite as StubGCR,
    )
    with pytest.raises(NotImplementedError):
        StubEL().score(None, None, None, None)
    with pytest.raises(NotImplementedError):
        StubLRF().score(None, None, None, None)
    with pytest.raises(NotImplementedError):
        StubPU().update(None, None, None, None)
    with pytest.raises(NotImplementedError):
        StubDRG().decide(None, None, None, None, None, None, None, None)
    with pytest.raises(NotImplementedError):
        StubGCR().rewrite(None, None, None, None)

    # lr_scorer returns real results (no NotImplementedError)
    from frcgw.falsification.lr_scorer import EvidenceLikelihood, LikelihoodScore
    evidence = _make_evidence()
    h = _make_candidate("h1", metadata={})
    result = EvidenceLikelihood().score(evidence, h, None, None)
    assert isinstance(result, LikelihoodScore)
    assert isinstance(result.loglik, float)


def test_no_torch_numpy_dependency_in_stub():
    """stub과 lr_scorer 둘 다 AST에 torch/numpy/pandas/sklearn import가 없음을 검증.

    C3 연결: stub 순수성 계약 + lr_scorer 구현 경계.
    Run 4: AST-level import 검사.
    """
    import pathlib

    root = pathlib.Path(__file__).parent.parent / "src" / "frcgw" / "falsification"
    forbidden_modules = {"torch", "numpy", "pandas", "sklearn"}

    for fname in ("lr_scorer_stub.py", "lr_scorer.py"):
        fpath = root / fname
        assert fpath.exists(), f"Expected file not found: {fpath}"
        tree = ast.parse(fpath.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.Import):
                    names = [alias.name.split(".")[0] for alias in node.names]
                else:
                    names = [node.module.split(".")[0]] if node.module else []
                for name in names:
                    assert name not in forbidden_modules, (
                        f"{fname} imports forbidden module '{name}'"
                    )


# ---------------------------------------------------------------------------
# Group C — LR Falsification Tests
# Connected claim: C3 (falsification mechanism)
# ---------------------------------------------------------------------------


def test_lr_score_positive_when_alt_explains_evidence_better():
    """h_alt가 h_exec보다 evidence를 더 잘 설명할 때 F_t > 0인지 확인한다.

    C3 연결: F_t = max_alt[ell(h_alt) - ell(h_exec)] > 0 조건.
    Run 4: EvidenceLikelihood + LikelihoodRatioFalsificationScorer 실 검증.
    """
    from frcgw.falsification.lr_scorer import (
        EvidenceLikelihood,
        LikelihoodRatioFalsificationScorer,
    )

    # Evidence: no_effect occurred
    evidence = _make_evidence(effect_type="no_effect", no_effect_flag=True)

    # h_exec expects a positive action effect — mismatches evidence
    h_exec_candidate = _make_candidate(
        "h_exec",
        metadata={"expected_effect_type": "positive_action", "expected_no_effect_flag": False},
    )
    # h_alt expects no_effect — matches evidence
    h_alt_candidate = _make_candidate(
        "h_alt",
        metadata={"expected_effect_type": "no_effect", "expected_no_effect_flag": True},
    )

    el = EvidenceLikelihood()
    exec_ls = el.score(evidence, h_exec_candidate, None, None)
    alt_ls = el.score(evidence, h_alt_candidate, None, None)

    h_exec_trace = _make_trace("h_exec")

    result = LikelihoodRatioFalsificationScorer().score(
        h_exec_trace=h_exec_trace,
        exec_likelihood=exec_ls,
        alt_likelihoods=[alt_ls],
        alt_candidates=[h_alt_candidate],
    )

    assert result.F_t > 0, f"Expected F_t > 0 when alt explains evidence better, got {result.F_t}"
    assert not result.degenerate
    assert result.best_h_alt_id == "h_alt"


def test_lr_score_zero_or_negative_when_exec_explains_evidence_better():
    """h_exec가 h_alt보다 evidence를 더 잘 설명할 때 F_t <= 0인지 확인한다.

    C3 연결: LR score의 방향성 계약.
    Run 4: ell_exec > ell_alt_best 케이스.
    """
    from frcgw.falsification.lr_scorer import (
        EvidenceLikelihood,
        LikelihoodRatioFalsificationScorer,
    )

    # Evidence: positive_action occurred
    evidence = _make_evidence(effect_type="positive_action", no_effect_flag=False)

    # h_exec matches evidence well
    h_exec_candidate = _make_candidate(
        "h_exec",
        metadata={"expected_effect_type": "positive_action", "expected_no_effect_flag": False},
    )
    # h_alt expects no_effect — doesn't match
    h_alt_candidate = _make_candidate(
        "h_alt",
        metadata={"expected_effect_type": "no_effect", "expected_no_effect_flag": True},
    )

    el = EvidenceLikelihood()
    exec_ls = el.score(evidence, h_exec_candidate, None, None)
    alt_ls = el.score(evidence, h_alt_candidate, None, None)

    h_exec_trace = _make_trace("h_exec")

    result = LikelihoodRatioFalsificationScorer().score(
        h_exec_trace=h_exec_trace,
        exec_likelihood=exec_ls,
        alt_likelihoods=[alt_ls],
        alt_candidates=[h_alt_candidate],
    )

    assert result.F_t <= 0, f"Expected F_t <= 0 when exec explains evidence better, got {result.F_t}"


def test_all_equal_likelihoods_sets_degenerate_flag():
    """모든 hypothesis의 loglik이 동일할 때 FalsificationResult.degenerate=True인지 확인한다.

    C3 연결: degenerate case — F_t=0 all-equal 케이스.
    Run 4: 모든 ell_t 동일 케이스에서 degenerate flag 검증.
    """
    from frcgw.falsification.lr_scorer import (
        LikelihoodRatioFalsificationScorer,
        LikelihoodScore,
    )

    # Both get identical loglik (no matching metadata → score=0 for both)
    exec_ls = LikelihoodScore(hypothesis_id="h_exec", loglik=0.0)
    alt_ls = LikelihoodScore(hypothesis_id="h_alt", loglik=0.0)

    h_exec_trace = _make_trace("h_exec")

    result = LikelihoodRatioFalsificationScorer().score(
        h_exec_trace=h_exec_trace,
        exec_likelihood=exec_ls,
        alt_likelihoods=[alt_ls],
        alt_candidates=[_make_candidate("h_alt")],
    )

    assert result.degenerate is True, "Expected degenerate=True when all likelihoods equal"
    assert result.F_t == 0.0


def test_empty_alternatives_blocks_falsification():
    """A_t^H가 비어 있을 때 F_t=0이고 degenerate=True인지 확인한다.

    C3 연결: alt_candidates=[] 케이스 처리 계약.
    Run 4: empty alt_candidates 케이스 검증.
    """
    from frcgw.falsification.lr_scorer import (
        LikelihoodRatioFalsificationScorer,
        LikelihoodScore,
    )

    exec_ls = LikelihoodScore(hypothesis_id="h_exec", loglik=1.0)
    h_exec_trace = _make_trace("h_exec")

    result = LikelihoodRatioFalsificationScorer().score(
        h_exec_trace=h_exec_trace,
        exec_likelihood=exec_ls,
        alt_likelihoods=[],
        alt_candidates=[],
    )

    assert result.degenerate is True, "Expected degenerate=True for empty alternatives"
    assert result.F_t == 0.0


def test_bce_not_main_path():
    """lr_scorer.py 소스에 BCE/sigmoid/binary_cross 키워드가 없는지 확인한다.

    C3 연결: BCE는 ABL-022/ABL-023 ablation path. main path = LR scorer.
    Run 4: inspect.getsource으로 BCE/sigmoid/binary_cross 부재 검증.
    """
    import pathlib

    fpath = (
        pathlib.Path(__file__).parent.parent
        / "src"
        / "frcgw"
        / "falsification"
        / "lr_scorer.py"
    )
    source = fpath.read_text(encoding="utf-8").lower()

    forbidden_keywords = ("sigmoid", "binary_cross", "bce", "binary_classifier")
    for kw in forbidden_keywords:
        assert kw not in source, (
            f"Forbidden keyword '{kw}' found in lr_scorer.py — BCE must remain ablation-only"
        )


def test_uncertainty_gate_not_equivalent_to_lr_gate():
    """DecisionRelevanceGate의 G_t 4-way conjunction이 단순 uncertainty > threshold와
    다른 결과를 낼 수 있는 케이스가 존재하는지 확인한다.

    C6 연결: G_t != uncertainty gate — 4-way conjunction 차이.
    C3 연결: LR falsification이 compute gate 결정에 기여함.
    Run 4: high F_t + low delta_v → G_t=False지만 uncertainty gate=True 케이스.
    """
    from frcgw.falsification.lr_scorer import (
        DecisionRelevanceGate,
        FalsificationResult,
        GateDecision,
        PosteriorState,
        PosteriorUpdateResult,
    )

    # Case: strong falsification (F_t=3.0 > tau_f=1.0) but value gain insufficient (delta_v < tau_v)
    falsification_result = FalsificationResult(
        h_exec_id="h_exec",
        best_h_alt_id="h_alt",
        loglik_exec=0.0,
        loglik_alt_best=3.0,
        F_t=3.0,
        margin=0.0,
        degenerate=False,
    )

    ps_before = PosteriorState(
        posterior_by_hypothesis={"h_exec": 0.9, "h_alt": 0.1},
        entropy=0.3,
        top_hypothesis_id="h_exec",
    )
    ps_after = PosteriorState(
        posterior_by_hypothesis={"h_exec": 0.4, "h_alt": 0.6},
        entropy=0.67,
        top_hypothesis_id="h_alt",
    )
    posterior_update = PosteriorUpdateResult(
        posterior_before=ps_before,
        posterior_after=ps_after,
        posterior_shift=0.5,
        adopted_hypothesis_id="h_alt",
        switch_recommended=True,
    )

    gate = DecisionRelevanceGate()
    decision = gate.decide(
        falsification_result=falsification_result,
        posterior_update=posterior_update,
        value_gain_delta=0.01,      # << tau_v: insufficient value gain
        action_switch_probability=0.9,
        compute_cost=0.05,
        tau_f=1.0,   # F_t=3.0 > tau_f ✓
        tau_v=0.1,   # delta_v=0.01 < tau_v ✗ → G_t=False
        tau_a=0.5,   # P_switch=0.9 > tau_a ✓
    )

    # G_t = False because delta_v < tau_v
    assert decision.G_t is False, f"Expected G_t=False (delta_v<tau_v), got gate_reason={decision.gate_reason}"

    # A naive uncertainty gate would fire here (high switch probability = high uncertainty signal)
    # Simulating: uncertainty > threshold → True
    uncertainty_score = posterior_update.posterior_shift  # 0.5 as proxy
    uncertainty_threshold = 0.3
    naive_uncertainty_gate = uncertainty_score > uncertainty_threshold

    assert naive_uncertainty_gate is True, "Uncertainty gate should fire in this case"
    assert decision.G_t != naive_uncertainty_gate, (
        "G_t and uncertainty gate must differ in this case — 4-way conjunction vs single condition"
    )
