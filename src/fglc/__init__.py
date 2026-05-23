"""
FGLC — Falsification-Guided Latent Correction for Robotics World Models.

Source: docs/idea/00_OVERVIEW.md
Architecture: docs/main/main.md

Key components (to be implemented in R1..R8):
    fglc.models.encoder       — grouped latent encoder (K=6, d=32)
    fglc.models.dynamics      — base dynamics prior pθ(z'|z,a,h)
    fglc.models.belief        — GRU belief memory h_t
    fglc.detectors.mismatch   — standardized mismatch ρ_t
    fglc.detectors.gate       — falsification gate β_t
    fglc.attention.causal     — causal attention α_t (sparse, value-aware)
    fglc.correction.adapter   — sparse residual correction δ_t
    fglc.planning.mppi        — MPPI/CEM latent planner
    fglc.evaluation.metrics   — 4-axis metrics (prediction/detection/attribution/control)
    fglc.schemas.visibility   — FORBIDDEN_AGENT_FIELDS runtime enforcement
"""

__version__ = "0.1.0"
