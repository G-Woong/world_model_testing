# Codex Task Report ??TASK_2041 TASK_10D
## Summary
Implemented Stage 1 R3 training and evaluation support. Added TrainerR3 with Encoder, BeliefMemory, GroupedDynamics, RewardHead, and ValueHead wiring; Gaussian 1-step NLL, reward MSE, value MSE with undiscounted Monte Carlo returns; CPU/CUDA device handling; per-epoch train/validation tracking; evaluator metrics; and metrics.json artifact writing.

## Files Changed
- src/fglc/training/__init__.py
- src/fglc/training/trainer_r3.py
- src/fglc/evaluation/__init__.py
- src/fglc/evaluation/metrics.py
- tests/test_fglc_trainer_r3_smoke.py
- .agent_tasks/codex_done/TASK_2041_TASK_10D_RESULT.md

## Commands Run
- Get-Content -Raw AGENTS.md
- Get-Content -Raw .agent_tasks\codex_queue\TASK_2041_TASK_10D.md
- Read allowed files and confirmed they were missing before creation.
- rg "CANONICAL_METRIC_KEYS|ARTIFACT_KEYS" src/fglc tests
- rg "class (Encoder|BeliefMemory|GroupedDynamics|RewardHead|ValueHead)|def forward|SyntheticToyDataset|make_dataloaders" src/fglc/models src/fglc/data tests
- Get-Content -Raw src/fglc/models/encoder.py
- Get-Content -Raw src/fglc/models/belief.py
- Get-Content -Raw src/fglc/models/dynamics.py
- Get-Content -Raw src/fglc/models/heads.py
- Get-Content -Raw src/fglc/data/dataloader.py
- Get-Content -Raw src/fglc/data/state_only_dataset.py
- Get-Content -Raw src/fglc/repair/diagnose.py
- Get-Content -Raw tests/test_fglc_dataset_state_only.py
- Get-Content -Raw configs/fglc/smoke_4060.yaml
- Get-Content -Raw pyproject.toml
- .\.venv\Scripts\python.exe -m pytest -q tests/test_fglc_trainer_r3_smoke.py
- .\.venv\Scripts\python.exe -m pytest -q tests/test_fglc_forbidden_field_sync.py
- $env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest -q tests/test_fglc_trainer_r3_smoke.py
- $env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest -q tests/test_fglc_forbidden_field_sync.py
- $env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest -q --ignore=tests/test_lifecycle_phase2_hooks.py
- git status --short

## Tests Run (pass/fail)
- PASS: $env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest -q tests/test_fglc_trainer_r3_smoke.py (6 passed)
- PASS: $env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest -q tests/test_fglc_forbidden_field_sync.py (18 passed, 14 skipped)
- PASS: $env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest -q --ignore=tests/test_lifecycle_phase2_hooks.py (all non-lifecycle tests passed, 14 skipped)
- FAIL then rerun with PYTHONPATH: .\.venv\Scripts\python.exe -m pytest -q tests/test_fglc_trainer_r3_smoke.py failed during collection because fglc was not importable without PYTHONPATH=src.
- FAIL then rerun with PYTHONPATH: .\.venv\Scripts\python.exe -m pytest -q tests/test_fglc_forbidden_field_sync.py failed during collection/import because fglc was not importable without PYTHONPATH=src.

## Evidence (log paths, metric values)
- Trainer smoke test writes metrics.json under pytest tmp_path and validates required keys.
- Observed train criterion in smoke: final train_nll <= initial_train_nll * 1.05.
- CUDA unavailable path reports vram_peak_mib = 0.0 on CPU.
- No persistent external log files were created.

## Risks / Open Questions
- Existing src/fglc/repair/diagnose.py does not currently include val_nll in CANONICAL_METRIC_KEYS, while TASK_10D STOP_CONDITION explicitly defines val_nll as canonical. Because diagnose.py is outside FILES_ALLOWED, this task implements a local Stage 1 canonical set in src/fglc/evaluation/metrics.py and does not modify repair code.
- The kstep_nll_slope smoke implementation computes fixed-offset latent NLL for k in {1,2,4,8}; it is sufficient for the Stage 1 artifact and tests but is not a recursive rollout evaluator.

## Patch Review Notes for Claude Code
- Call graph: TrainerR3.train -> _run_train_epoch -> _compute_losses; TrainerR3.train -> evaluate_nll -> _compute_losses; Evaluator.evaluate -> trainer.evaluate_nll and trainer.evaluate_kstep_nll_slope -> _evaluate_kstep_nll.
- The trainer consumes batches with only state/action/reward/done and never introduces forbidden fields.
- Calibration loss is intentionally not implemented, matching lambda_calibration=0.0 smoke scope.
- metrics.json contains exactly Stage 1 scientific keys plus artifact keys.

## Accept/Reject Recommendation
Accept. The scoped implementation and smoke tests pass, mandatory forbidden-field sync remains green, and the broader non-lifecycle suite passes with PYTHONPATH=src.
