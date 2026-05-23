from __future__ import annotations

from frcgw.planning.decision_gate import GateConfig, GateInput, decide


def test_hybrid_all_conditions_met() -> None:
    gi = GateInput(F_t=1.0, delta_V=1.0, P_switch=0.9, C_plan=0.1)
    cfg = GateConfig(tau_f=0.0, tau_v=0.0, tau_a=0.5)
    assert decide(gi, cfg).should_plan is True


def test_hybrid_missing_one_condition() -> None:
    cfg = GateConfig(tau_f=0.5, tau_v=0.5, tau_a=0.5)
    cases = [
        GateInput(F_t=0.5, delta_V=1.0, P_switch=0.9, C_plan=0.1),
        GateInput(F_t=1.0, delta_V=0.5, P_switch=0.9, C_plan=0.1),
        GateInput(F_t=1.0, delta_V=1.0, P_switch=0.5, C_plan=0.1),
        GateInput(F_t=1.0, delta_V=0.2, P_switch=0.9, C_plan=0.2),
    ]
    for gi in cases:
        assert decide(gi, cfg).should_plan is False


def test_uncertainty_alone_does_not_open_hybrid_gate() -> None:
    gi = GateInput(F_t=0.0, delta_V=0.0, P_switch=0.0, C_plan=0.0, posterior_entropy=100.0)
    cfg = GateConfig(gate_mode="hybrid")
    assert decide(gi, cfg).should_plan is False


def test_always_plan_mode() -> None:
    gi = GateInput(F_t=0.0, delta_V=0.0, P_switch=0.0, C_plan=0.0)
    cfg = GateConfig(gate_mode="always_plan")
    assert decide(gi, cfg).should_plan is True


def test_never_plan_mode() -> None:
    gi = GateInput(F_t=1.0, delta_V=1.0, P_switch=1.0, C_plan=0.0)
    cfg = GateConfig(gate_mode="never_plan")
    assert decide(gi, cfg).should_plan is False


def test_uncertainty_only_mode() -> None:
    cfg = GateConfig(gate_mode="uncertainty_only", tau_u=2.0)
    assert decide(GateInput(0.0, 0.0, 0.0, 0.0, posterior_entropy=3.0), cfg).should_plan is True
    assert decide(GateInput(0.0, 0.0, 0.0, 0.0, posterior_entropy=1.0), cfg).should_plan is False


def test_cost_exceeds_benefit() -> None:
    gi = GateInput(F_t=1.0, delta_V=0.2, P_switch=0.9, C_plan=0.5)
    assert decide(gi, GateConfig()).should_plan is False
