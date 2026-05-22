# 18_DATA_BENCHMARKS

## Source
- main.md §2 (input data), §15 (data split), §16 (modality progression)
- deep-research-report.md §실험 설계와 벤치마크 (R-13)

## Claim

ManiSkill state-only data with controlled physical parameter variation provides the
primary benchmark. regime_id and env_state (true physical parameters) are EVALUATION-ONLY
fields — never enter training loss or inference input.

## Data Schema

```python
transition_t = {
    # INFERENCE INPUT (allowed)
    "state":   x_t,         # shape: [D_x] — robot proprio + object + goal
    "action":  a_t,         # shape: [D_a] — delta EEF + gripper
    "reward":  r_t,         # scalar
    "done":    d_t,         # scalar

    # EVALUATION-ONLY (forbidden in inference input)
    "regime_id":    g_t,    # physical regime label
    "true_mass":    m_t,    # actual object mass
    "true_friction": f_t,   # actual friction
    "true_latency":  l_t,   # actual action delay
    "true_noise":    n_t,   # actual obs noise σ
    "true_action_gain": ag_t, # actual action gain

    # ORACLE BASELINE (explicitly labeled; forbidden in standard agent)
    "oracle_action": oa_t,  # optimal action given true physical params
    "split_id": sid_t,      # OOD split membership
}
```

## OOD Split Design

```
Train-ID:    mass=1.0, friction=1.0, latency=0, noise=0.0, action_gain=1.0
Valid-ID:    same distribution
Test-ID:     same distribution, unseen seeds

OOD-mass:    mass ∈ {0.5, 1.5, 2.0}
OOD-friction: friction ∈ {0.3, 0.7, 1.5}
OOD-latency:  delay ∈ {3, 5, 8} steps
OOD-noise:   obs_noise σ ∈ {0.05, 0.1, 0.2}
OOD-action-gain: gain ∈ {0.7, 0.85, 1.3}
OOD-mixed:   mass × friction × latency combined
```

## Datasets

| Dataset | Role | Modality | OOD axes |
|---|---|---|---|
| ManiSkill PickCube/PushCube/LiftCube | Primary: controlled experiments | state_dict | mass/friction/latency/noise/gain |
| robosuite/robomimic | HDF5 pipeline validation | states+actions | camera dropout, observation corruption |
| DROID (Khazatsky 2024) | Real robot validation Phase 2 | language+proprio+3-RGB | collector split, scene shift |
| BridgeData V2 (Walke 2023) | Real robot generalization | image+goal-image | institution/object split |

## Data Rules (Normative)

- regime_id: EVALUATION ONLY — never in training loss, never in model input
- env_state (mass/friction/latency/noise/gain): EVALUATION ONLY
- oracle_action: ORACLE BASELINE ONLY — explicitly labeled experiment
- split_id: SPLIT TRACKING ONLY — never in model input

**Rationale**: FGLC claims to identify regime shifts WITHOUT oracle regime labels.
If regime_id enters training, the claim "no regime label required" is violated.

## Connection Map
- Upstream: docs/main/main.md §2, §15
- Downstream: all training/eval scripts; 21_METRICS.md (eval uses split_id)
- Fragile file: this document IS the normative SSoT for data rules

## Checkpoints

- C1 Math validity: N/A (data schema design)
- C2 Novelty: N/A
- C3 Reviewer attack: MEDIUM — "You use regime_id at evaluation — isn't that leakage?"
  Defense: regime_id used ONLY for evaluation stratification (which OOD split?), never as
  model input or training signal. Analogous to using test set labels for computing accuracy.
- C4 Feasibility: CONDITIONAL — DROID/BridgeData download requires large storage (~100GB+).
  Phase 1 (state-only ManiSkill): fully feasible. Phase 2: requires DROID access.
- C5 Claim-metric: OOD detection AUROC computed using regime_id as ground truth label.
  Prediction/planning metrics computed per OOD split.
- C6 Impl risk: MEDIUM — ManiSkill OOD variation requires environment parameter API.
- C7 Experiment design: Must verify OOD challenge exists: OOD NLL >> ID NLL at Stage 1.
- C8 Failure interp: If OOD splits don't produce measurable dynamics shift: dataset design fails.
- C9 Related work: ManiSkill v3 (arXiv 2410.00425); DROID arXiv 2403.12945 — PENDING ≥2 sources
- C10 Context routing: Source = main.md §2,15. THIS FILE IS FRAGILE (normative data SSoT).
