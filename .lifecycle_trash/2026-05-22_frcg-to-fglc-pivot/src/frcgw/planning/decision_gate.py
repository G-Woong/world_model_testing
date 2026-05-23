"""frcgw.planning.decision_gate -- G_hybrid 4-condition decision gate.

Source MD: paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md G_hybrid
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class GateConfig:
    gate_mode: str = "hybrid"
    tau_f: float = 0.0
    tau_v: float = 0.0
    tau_a: float = 0.5
    tau_u: float = 2.0
    C_plan_beta: float = 0.1
    tau_r: float = 0.5
    use_no_state_change_proxy: bool = True


@dataclass
class GateInput:
    F_t: float
    delta_V: float
    P_switch: float
    C_plan: float
    posterior_entropy: float = 0.0


@dataclass
class GateOutput:
    should_plan: bool
    reason: str
    components: dict[str, Any]


def decide(gi: GateInput, cfg: GateConfig | None = None) -> GateOutput:
    """Evaluate gate condition based on cfg.gate_mode."""
    cfg = cfg or GateConfig()
    components = {
        "F_t": gi.F_t,
        "delta_V": gi.delta_V,
        "P_switch": gi.P_switch,
        "C_plan": gi.C_plan,
        "posterior_entropy": gi.posterior_entropy,
    }

    if cfg.gate_mode == "always_plan":
        return GateOutput(True, "always_plan", components)
    if cfg.gate_mode == "never_plan":
        return GateOutput(False, "never_plan", components)
    if cfg.gate_mode == "falsification_only":
        should_plan = gi.F_t > cfg.tau_f
        return GateOutput(should_plan, "all_conditions_met" if should_plan else "low_F_t", components)
    if cfg.gate_mode == "uncertainty_only":
        should_plan = gi.posterior_entropy > cfg.tau_u
        return GateOutput(should_plan, "uncertainty_only", components)
    if cfg.gate_mode != "hybrid":
        raise ValueError(f"unknown gate_mode: {cfg.gate_mode}")

    if gi.F_t <= cfg.tau_f:
        return GateOutput(False, "low_F_t", components)
    if gi.delta_V <= cfg.tau_v:
        return GateOutput(False, "low_delta_V", components)
    if gi.P_switch <= cfg.tau_a:
        return GateOutput(False, "low_P_switch", components)
    if gi.delta_V - gi.C_plan <= 0:
        return GateOutput(False, "cost_exceeds_benefit", components)
    return GateOutput(True, "all_conditions_met", components)
