# Phase R2 — Data Pipeline

## Goal
ManiSkill state-only dataset with ID and OOD splits, replay loader, data validation tests.

## Inputs
- Prior phase sentinel: outputs/phase_gates/R1.passed
- Code: src/fglc/data/maniskill.py

## Steps

1. **ManiSkill environment setup + rollout collection**
   ```python
   # Tasks: PickCube, PushCube, LiftCube
   # Policy: random agent (for initial) + human demo replay
   # State observation: state_dict (robot_qpos + object_pose + goal)
   ```

2. **OOD parameter variation**
   ```python
   # For each OOD axis, collect separate dataset split:
   OOD_CONFIGS = {
       "ood_mass":     [{"object_mass": v} for v in [0.5, 1.5, 2.0]],
       "ood_friction": [{"friction": v} for v in [0.3, 0.7, 1.5]],
       "ood_latency":  [{"action_delay": v} for v in [3, 5, 8]],  # steps
       "ood_noise":    [{"obs_noise_sigma": v} for v in [0.05, 0.1, 0.2]],
       "ood_gain":     [{"action_gain": v} for v in [0.7, 0.85, 1.3]],
       "ood_mixed":    [{"object_mass": 1.5, "friction": 0.7, "action_delay": 3}],
   }
   ```

3. **Data schema enforcement**
   Each transition stored as HDF5 with FORBIDDEN fields in separate eval-only split.
   Forbidden fields NEVER in model input tensor construction.

4. **Replay loader + data validation**
   `src/fglc/data/maniskill.py`: DataLoader returning (state, action, next_state, reward, done)
   Validation: `tests/test_fglc_data_pipeline.py`

5. **Verify OOD challenge exists**
   CRITICAL GATE: base WM NLL on OOD must be measurably higher than ID NLL.
   If OOD_NLL ≈ ID_NLL → dataset design failure → stop.

## Deliverables
- data: `data/fglc/` (ID + 6 OOD splits per task)
- code: `src/fglc/data/maniskill.py`
- tests: `tests/test_fglc_data_pipeline.py`

## Gate Criteria (all must be true for R2.passed)

- [ ] 3 tasks × 7 splits (ID + 6 OOD) collected, each with ≥1000 episodes
- [ ] FORBIDDEN fields isolated in eval-only partition
- [ ] Replay loader returns correct tensor shapes
- [ ] `pytest tests/test_fglc_data_pipeline.py` green
- [ ] OOD challenge verification: ID NLL measured (gate for Stage 1 comparison)

## Risk Register References
- R-2: ManiSkill API drift (object mass/friction parameter names may change)
- R-4: Computational cost — 3 tasks × 7 splits × 1000 episodes × T=16 may take ~8h

## Commit Cadence
- commit 1: `feat(data): R2 ManiSkill state-only ID split loader`
- commit 2: `feat(data): R2 OOD splits (mass/friction/latency/noise/gain/mixed)`
- commit 3: `test(data): R2 data pipeline validation green`

## Codex Delegation
Yes — data loader + validation (multi-file) → Codex TASK_R2_DATA_PIPELINE.md
