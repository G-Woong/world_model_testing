TASK_NAME: step8_longhorizon_configs
SANDBOX_MODE: bypass

BACKGROUND:
FRCG-WM STEP 8. v0_3 training (STEP 6) used max_steps=800, max_epochs=6. STEP 8 needs a two-stage training plan:
- Stage A (diagnostic): 500 steps, 3 epochs — enough to see F_t variance convergence or flag degenerate
- Stage B (long-horizon): 2000 steps, ≥10 epochs — paper-table candidate checkpoint
Both stages use v0_4 dataset and l_falsification=1.0. Monitoring must detect NaN/Inf and log F_t variance.

src/frcgw/training/monitoring.py already exists with PublicTraceLogger and check_losses_finite. It needs enhancement for F_t variance monitoring hook.

GOAL:
1. Create configs/train_text_v0_4_long.yaml (Stage A: 500 steps, 3 epochs, v0_4 data)
2. Create configs/train_text_v0_4_long_stage2.yaml (Stage B: 2000 steps, 10 epochs, v0_4 data)
3. Create configs/lr_eval_real_v0_4_long.yaml (eval config pointing to v0_4 data + Stage B checkpoint)
4. Edit src/frcgw/training/monitoring.py: add F_t variance monitoring hooks + NaN/Inf detection
5. Create tests/test_step8_long_horizon_training_config.py with ≥3 tests

FILES_ALLOWED:
- configs/train_text_v0_4_long.yaml (NEW)
- configs/train_text_v0_4_long_stage2.yaml (NEW)
- configs/lr_eval_real_v0_4_long.yaml (NEW)
- src/frcgw/training/monitoring.py (Edit)
- src/frcgw/training/train_text.py (Edit: gradient clipping ONLY — see below)
- tests/test_step8_long_horizon_training_config.py (NEW)
- .agent_tasks/codex_done/TASK_1080_step8_longhorizon_configs_RESULT.md

FILES_FORBIDDEN:
- src/frcgw/schemas/visibility.py
- src/frcgw/schemas/step_schema.py
- outputs/**
- data/**
- paper_context_ref/**
- .claude/**
- scripts/run_codex_task.ps1
- *.pt

REQUIRED_IMPLEMENTATION:
src/frcgw/training/train_text.py (Edit — gradient clipping ONLY):
- In train_one_epoch(), add ONE LINE between loss.backward() and optimizer.step():
  torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
- Add import: from torch import nn as _nn (or use torch.nn.utils directly)
- NO other changes to train_text.py
- This is REQUIRED: feasibility audit showed lr × 0.5 retry alone is insufficient if NaN
  originates from large logit magnitudes in falsification_score() forward pass.

configs/train_text_v0_4_long.yaml (Stage A):
- version: 1, phase: CC-P3-STEP8-STAGE-A, seed: 42
- batch_size: 8, max_steps: 1000, max_epochs: 3, lr: 0.001, weight_decay: 0.0001
  NOTE: 1000 steps (not 500) — feasibility audit finding: 500 steps = 1.1 epochs at v0_4 scale
  (3500 train episodes), insufficient for F_t variance convergence diagnosis. 1000 steps = 2.28 epochs.
  Wall-clock cost: +30-90 seconds (negligible).
- model_config: "configs/model_text.yaml"
- data_config: "configs/data_collection_text.yaml"
- dataset_version: "v0_4"
- dataset_root: "data/frcgw_text/v0_4"
- split: "train"
- objective_weights: same as v0_3_falsification_stage2 (l_falsification: 1.0, l_control_grammar: 1.0, etc.)
- manifest_dir: "outputs/runs/p3_train_v0_4_long_stageA"
- checkpoint_dir: "outputs/checkpoints/pretrain_v0_4_long_stageA"
- monitoring: {nan_check: true, f_t_variance_check: true, grad_norm_threshold: 100.0}
- gate_thresholds: same as v0_3_falsification_stage2
- forbidden_fields: same as v0_3 training config
- notes: "STEP 8 Stage A: diagnostic training (500 steps). NaN→lr×0.5 retry logic."

configs/train_text_v0_4_long_stage2.yaml (Stage B):
- version: 1, phase: CC-P3-STEP8-STAGE-B, seed: 42
- batch_size: 8, max_steps: 2000, max_epochs: 10, lr: 0.001, weight_decay: 0.0001
- dataset_version: "v0_4", dataset_root: "data/frcgw_text/v0_4"
- objective_weights: same as Stage A (l_falsification: 1.0, l_control_grammar: 1.0)
- manifest_dir: "outputs/runs/p3_train_v0_4_long_stageB"
- checkpoint_dir: "outputs/checkpoints/pretrain_v0_4_long"
- monitoring: {nan_check: true, f_t_variance_check: true, grad_norm_threshold: 100.0}
- warm_start_checkpoint: "outputs/checkpoints/pretrain_v0_4_long_stageA/checkpoint_best.pt"
  (optional — if exists, load; else train from scratch)
- notes: "STEP 8 Stage B: long-horizon training (2000 steps, 10 epochs). Paper-table candidate."

configs/lr_eval_real_v0_4_long.yaml:
- version: step8_full
- dataset_root: data/frcgw_text/v0_4
- checkpoint_path: outputs/checkpoints/pretrain_v0_4_long/checkpoint_best.pt
- model_config: configs/model_text.yaml
- max_episodes: null
- compute_budget: {planning_calls_cap: 5, rollout_steps_cap: 10}
- agents: same 3 as step7_full (FRCG-LR frcg_lr, ABL-024 no_alternative_hypothesis, ABL-036 no_compute_gate)
- metrics: task_success_rate, falsification_precision_recall, ood_shift_f1, progress_per_compute, false_planning_call_rate
- splits: [test_id, test_ood]
- seeds: [0, 1, 2, 3, 4]
- output_root: outputs/runs/p3_lr_real_eval_step8_full

src/frcgw/training/monitoring.py additions:
- Add class FtVarianceMonitor with method record_f_t(step: int, f_t: float) and property variance() → float
- Add function check_f_t_variance_nonzero(f_t_values: list[float], threshold: float = 1e-6) → bool
- Add function check_grad_norm(grad_norm: float, threshold: float = 100.0) → bool
- Add function build_nan_repair_lr(original_lr: float, attempt: int = 0) → float:
  returns original_lr * (0.5 ** (attempt + 1)); raises ValueError if attempt > 0 (max 1 retry)
- Preserve existing PublicTraceLogger.log_step() interface exactly

tests/test_step8_long_horizon_training_config.py:
- test_stage_a_config_schema: load configs/train_text_v0_4_long.yaml, verify required keys including max_steps == 1000
- test_stage_b_config_has_higher_budget: verify stage2 max_steps > stage_a max_steps AND max_epochs > stage_a max_epochs
- test_monitoring_nan_repair_lr: build_nan_repair_lr(0.001, attempt=0) == 0.0005; attempt=1 raises ValueError
- test_gradient_clipping_in_train_text: import train_text; read source; assert "clip_grad_norm_" appears in train_one_epoch function body

REQUIRED_TESTS:
- tests/test_step8_long_horizon_training_config.py: all 3 tests green
- existing: python -m pytest tests/ -q --ignore=tests/test_step8_c3_trace_integrity.py --ignore=tests/test_step8_v0_4_dataset.py (must stay green)

ACCEPTANCE_CRITERIA:
1. All 3 config YAML files are valid and loadable with yaml.safe_load
2. monitoring.py has FtVarianceMonitor, check_f_t_variance_nonzero, check_grad_norm, build_nan_repair_lr
3. All 3 new tests green
4. monitoring.py PublicTraceLogger interface unchanged

COMMIT_MESSAGE:
feat(step8/task3): long-horizon training configs + monitoring hooks

STOP_CONDITION:
Stop if: monitoring.py changes would break existing import chain for train_text.py.

RELATED_AGENT_REPORT_IDS: feasibility_step8_budget_R1, math_critic_step8_c3_gradient_R1
