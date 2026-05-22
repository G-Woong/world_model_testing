# Phase R1 — Infrastructure Setup

## Goal
Install ManiSkill/SAPIEN/h5py/entmax, verify CUDA, create src/fglc/ skeleton.

## Inputs
- Prior phase sentinel: outputs/phase_gates/R0.passed
- Code stub: src/fglc/__init__.py

## Steps

1. **Python environment setup**
   ```powershell
   # Install base deps
   pip install -e ".[maniskill,rl,causal]"
   # Verify ManiSkill
   python -c "import mani_skill; print(mani_skill.__version__)"
   # Verify entmax
   python -c "from entmax import sparsemax, entmax15; print('entmax OK')"
   # Verify CUDA
   python -c "import torch; print(torch.cuda.is_available())"
   ```

2. **Create src/fglc/ package skeleton**
   ```
   src/fglc/
   ├── __init__.py (done)
   ├── py.typed (done)
   ├── schemas/
   │   ├── __init__.py
   │   └── visibility.py  ← FORBIDDEN_AGENT_FIELDS
   ├── models/
   │   ├── encoder.py     ← MLP encoder, grouped latent
   │   ├── dynamics.py    ← base dynamics prior pθ
   │   └── belief.py      ← GRU belief memory
   ├── detectors/
   │   ├── mismatch.py    ← standardized mismatch ρ_t
   │   └── gate.py        ← falsification gate β_t
   ├── attention/
   │   └── causal.py      ← intervention-policy attention α_t
   ├── correction/
   │   └── adapter.py     ← sparse residual correction δ_t
   ├── planning/
   │   └── mppi.py        ← MPPI/CEM latent planner
   ├── evaluation/
   │   ├── metrics.py     ← 4-axis metric suite
   │   └── calibration.py ← ECE, reliability diagram
   └── data/
       └── maniskill.py   ← ManiSkill data loader
   ```

3. **Create visibility.py (FRAGILE file)**
   Defines FORBIDDEN_AGENT_FIELDS: regime_id, true_mass, true_friction, etc.
   Mirror of docs/idea/18_DATA_BENCHMARKS.md §Data Rules.

4. **Verify package import**
   ```powershell
   python -c "import fglc; from fglc.schemas.visibility import FORBIDDEN_AGENT_FIELDS; print(len(FORBIDDEN_AGENT_FIELDS), 'forbidden fields')"
   ```

5. **Create visibility sync test**
   tests/test_fglc_forbidden_field_sync.py

## Deliverables
- code: `src/fglc/` (12 modules)
- tests: `tests/test_fglc_forbidden_field_sync.py`
- doc updates: none

## Gate Criteria (all must be true for R1.passed)

- [ ] `pip install -e ".[maniskill]"` succeeds
- [ ] `python -c "import fglc.schemas.visibility"` succeeds
- [ ] `pytest tests/test_fglc_forbidden_field_sync.py` green
- [ ] `python -m pyflakes src/fglc/` → 0 errors
- [ ] ManiSkill env instantiation test passes (smoke test)

## Risk Register References
- R-2 (ROADMAP/19): ManiSkill API drift
- R-3 (ROADMAP/19): SAPIEN version compatibility

## Commit Cadence
- commit 1: `feat(fglc): R1 src/fglc skeleton + visibility.py`
- commit 2: `test(fglc): R1 forbidden field sync test green`

## Codex Delegation
Yes — skeleton creation (3+ files) → Codex TASK file at `.agent_tasks/codex_queue/TASK_R1_FGLC_SKELETON.md`
