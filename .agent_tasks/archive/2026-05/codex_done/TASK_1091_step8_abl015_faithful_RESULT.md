# TASK 1091 Result: step8_abl015_faithful

## Files Changed
- `configs/train_text_v0_4_abl015.yaml`
- `scripts/run_step8_faithful_ablations.py`
- `tests/test_step8_faithful_ablations.py`
- `.agent_tasks/codex_done/TASK_1091_step8_abl015_faithful_RESULT.md`

## Tests Run
- `.venv\Scripts\python.exe -m pytest tests/test_step8_faithful_ablations.py`
- `.venv\Scripts\python.exe scripts/run_step8_faithful_ablations.py`

## Pass/Fail Summary
- PASS: `tests/test_step8_faithful_ablations.py` (`2 passed`)
- PASS: ABL-015 validator script confirmed config isolation and printed training entrypoint.

## Training Entry
- Command: `python scripts/02_train_text_smoke.py --config configs/train_text_v0_4_abl015.yaml --model-config configs/model_text.yaml --output-dir outputs/runs/p3_train_v0_4_abl015`
- Expected checkpoint: `outputs/checkpoints/abl015_no_control_grammar_loss/checkpoint_best.pt`

## Blockers
- None.
