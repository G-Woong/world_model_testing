TASK_NAME: C7_train_smoke

BACKGROUND:
P3 smoke training loop, monitoring, config population, and CLI entrypoint.
Source: paper_context_ref/11_MODEL_DATASET_SCALE_AND_TRAINING_BUDGET_v1.md §tiny model

Smoke train constraints:
  - CPU only (no CUDA required)
  - ≤ 2 epochs, ≤ 80 steps total
  - batch_size = 8
  - Complete in ≤ 5 minutes on CPU
  - All per-step losses must be finite (not nan/inf)

Data source:
  - data/frcgw_text/v0_1/manifest.json (200 episodes, train/valid/test_id splits)
  - Use build_dataloaders() from src/frcgw/data/text_dataset.py

Model:
  - TextFRCGModel with default config (from text_frcg_model.py get_default_cfg())
  - Adam optimizer, lr=1e-3, weight_decay=1e-4

Loss function:
  - compute_total_loss() from src/frcgw/objectives/losses.py
  - For smoke train, F_t=None (falsification disabled; losses.py already handles this gracefully)
  - world_model_output from model.world_model_heads.forward_given_action(shared_h, z_state, action_type, 0)
    where action_type is taken from batch candidate_actions_public[0].action_type (or "noop" if empty)
  - public_input is public_inputs list from batch (for leakage check)

Monitoring:
  - Log per-loss scalars + grad_norm per step to a JSONL file
  - Each line: {"step": N, "epoch": E, "losses": {...}, "grad_norm": ..., "timestamp": "..."}
  - PublicTraceLogger class writes to {output_dir}/training_log.jsonl

Checkpoint:
  - Save after each epoch: {output_dir}/checkpoint_ep{N}.pt
    Contents: {"epoch": N, "model_state_dict": ..., "optimizer_state_dict": ..., "cfg": ..., "step": N}
  - Manifest after each epoch: {output_dir}/manifest.json
    Contents: {"seed": ..., "n_steps": ..., "n_epochs": ..., "config": ..., "final_losses": {...}}

Output directory: outputs/runs/p3_smoke/ (created if not exists, NOT committed to git)

Configs to POPULATE (currently have null values):

configs/model_text.yaml — populate these fields:
  version: 1
  phase: CC-P3
  seed: 42
  vocab_size: 4096
  embed_dim: 64
  d_model: 128
  nhead: 4
  num_layers: 2
  dim_feedforward: 256
  dropout: 0.1
  max_seq_len: 128
  hidden_dim: 128
  z_state_dim: 32
  n_regimes: 8
  n_grammars: 8
  n_change_types: 12
  n_reveal_shift: 3
  n_effect_types: 7
  n_hypotheses: 64
  action_embed_dim: 64
  hypothesis_embed_dim: 32
  model_version: "p3-tiny-v0.1"
  compute_budget: "smoke"
  ablation: null
  notes: "P3 tiny text model. ~460k params."
  (keep existing forbidden_fields list unchanged)

configs/train_text.yaml — populate these fields:
  version: 1
  phase: CC-P3
  seed: 42
  batch_size: 8
  max_steps: 80
  max_epochs: 2
  lr: 0.001
  weight_decay: 0.0001
  model_config: "configs/model_text.yaml"
  data_config: "configs/data_collection_text.yaml"
  split: "train"
  objective_weights:
    l_action_effect: 1.0
    l_progress: 0.5
    l_regime: 1.0
    l_control_grammar: 1.0
    l_falsification: 0.0
    l_intent_action_mapping: 0.0
    l_change_point: 0.3
    l_reveal_shift: 0.3
    l_failed_action: 0.3
    l_temporal_consistency: 0.0
  optimizer: "adam"
  manifest_dir: "outputs/runs/p3_smoke"
  gate_thresholds:
    tau_f: 0.0
    tau_v: 0.0
    tau_a: 0.5
    tau_u: 2.0
    C_plan_beta: 0.1
    tau_r: 0.5
  compute_budget: "smoke: max_epochs=2, max_steps=80, batch_size=8"
  ablation: null
  notes: "P3 smoke train config."
  (keep existing forbidden_fields list unchanged, keep version: null at end only if there's no conflict)

Note: configs/ files currently have "version: null" at top AND bottom. Remove the duplicate.

EXISTING MODULES (DO NOT MODIFY):
  - src/frcgw/models/text_frcg_model.py: TextFRCGModel, ModelOutput
  - src/frcgw/models/world_model_heads.py: WorldModelHeads, RolloutResult
  - src/frcgw/objectives/losses.py: compute_total_loss, LossDict, EFFECT_TYPE_VOCAB
  - src/frcgw/objectives/rewards.py: reward functions
  - src/frcgw/data/text_dataset.py: build_dataloaders, BatchTargets
  - src/frcgw/planning/decision_gate.py: GateConfig, GateInput, GateOutput, decide
  - src/frcgw/planning/planner.py: text_frcg_plan, PlannerState, PlanMetadata
  - src/frcgw/schemas/visibility.py: assert_agent_observation_safe

GOAL:
Implement train_text.py, monitoring.py, populate configs, create CLI script, write smoke test.

FILES_ALLOWED:
  - src/frcgw/training/train_text.py
  - src/frcgw/training/monitoring.py
  - src/frcgw/training/__init__.py
  - configs/model_text.yaml
  - configs/train_text.yaml
  - scripts/02_train_text_smoke.py
  - tests/test_train_text_smoke.py

FILES_FORBIDDEN:
  - .claude/
  - CLAUDE.md
  - .mcp.json
  - .venv/
  - data/
  - outputs/
  - secrets/
  - scripts/run_codex_task.ps1
  - paper_context_ref/
  - src/frcgw/schemas/
  - src/frcgw/text_env/
  - src/frcgw/data/
  - src/frcgw/models/
  - src/frcgw/objectives/
  - src/frcgw/planning/

REQUIRED_IMPLEMENTATION:

src/frcgw/training/monitoring.py:
```python
"""frcgw.training.monitoring -- Per-step loss and gradient norm logger.

Source MD: paper_context_ref/07_LATENT_ARCHITECTURE_DESIGN.md §MOD-07-027
Source MD: paper_context_ref/11_MODEL_DATASET_SCALE_AND_TRAINING_BUDGET_v1.md §tiny model
"""
```
Required:
- class PublicTraceLogger:
  - __init__(self, output_dir: str | Path)
  - Creates {output_dir}/training_log.jsonl if not exists
  - def log_step(self, step: int, epoch: int, loss_dict: LossDict, grad_norm: float) -> None:
    Appends JSON line: {step, epoch, losses: {name: value for each loss}, grad_norm, timestamp}
  - def close(self) -> None

src/frcgw/training/train_text.py:
```python
"""frcgw.training.train_text -- Smoke training loop for P3 tiny text model.

Source MD: paper_context_ref/11_MODEL_DATASET_SCALE_AND_TRAINING_BUDGET_v1.md §tiny model
Source MD: paper_context_ref/08_LOSS_REWARD_TRAINING_OBJECTIVE.md
"""
```
Required:

@dataclass class EpochResult:
  epoch: int
  n_steps: int
  mean_losses: dict[str, float]
  final_loss: float

@dataclass class SmokeResult:
  config: dict
  n_epochs: int
  total_steps: int
  all_losses_finite: bool
  checkpoint_paths: list[str]
  manifest_path: str

def _get_action_type_from_batch(batch: dict) -> str:
  """Extract first action type from batch for world model."""
  - Try first candidate action type from public_inputs[0].candidate_actions_public
  - Return "noop" if none available

def train_one_epoch(
    model: TextFRCGModel,
    dataloader: DataLoader,
    optimizer: Optimizer,
    weights: dict[str, float],
    logger: PublicTraceLogger,
    device: str = "cpu",
    epoch: int = 0,
    max_steps: int = 80,
    global_step: int = 0,
) -> tuple[EpochResult, int]:
  """Train model for one epoch.
  
  Source MD: paper_context_ref/11_MODEL_DATASET_SCALE_AND_TRAINING_BUDGET_v1.md
  """
  - Loop over batches until max_steps reached
  - For each batch:
    1. Call assert_no_objective_leakage(pub_input) for each item (from losses.py)
    2. model.forward(public_inputs) → model_out
    3. action_type = _get_action_type_from_batch(batch)
    4. world_out = model.world_model_heads.forward_given_action(
           model_out.shared_h, model_out.z_state, action_type, 0)
    5. loss_dict = compute_total_loss(model_out, world_out, F_t=None, targets=targets, weights=weights)
    6. optimizer.zero_grad()
    7. loss_dict.l_total.backward()
    8. grad_norm = compute_grad_norm(model)
    9. optimizer.step()
    10. logger.log_step(global_step, epoch, loss_dict, grad_norm)
    11. global_step += 1
  - Return EpochResult, updated global_step

def compute_grad_norm(model: TextFRCGModel) -> float:
  """Compute total gradient L2 norm."""
  total_norm = 0.0
  for p in model.parameters():
      if p.grad is not None:
          total_norm += p.grad.data.norm(2).item() ** 2
  return total_norm ** 0.5

def save_checkpoint(model, optimizer, epoch, step, cfg, output_dir):
  """Save checkpoint to {output_dir}/checkpoint_ep{epoch}.pt."""

def write_manifest(n_steps, n_epochs, seed, cfg, final_losses, output_dir):
  """Write manifest.json to output_dir."""

def run_smoke_train(
    train_cfg_path: str | Path,
    model_cfg_path: str | Path,
    output_dir: str | Path = "outputs/runs/p3_smoke",
) -> SmokeResult:
  """Run smoke training from config files."""
  - Load YAML configs (PyYAML)
  - Build model from model_cfg
  - Build dataloaders from manifest_path derived from train_cfg
  - Run training for max_epochs or until max_steps
  - Save checkpoint and manifest after each epoch
  - Return SmokeResult

scripts/02_train_text_smoke.py:
  CLI with argparse:
  - --config: path to train_text.yaml (default: configs/train_text.yaml)
  - --model-config: path to model_text.yaml (default: configs/model_text.yaml)
  - --output-dir: output directory (default: outputs/runs/p3_smoke)
  - Calls run_smoke_train() and prints final SmokeResult summary

REQUIRED_TESTS:

tests/test_train_text_smoke.py:
```python
"""Tests for P3 smoke training loop.

Source MD: paper_context_ref/11_MODEL_DATASET_SCALE_AND_TRAINING_BUDGET_v1.md
"""
```
Note: Use pytest.importorskip("torch") at top.
The data-backed tests should use data/frcgw_text/v0_1/ with a pytest fixture that skips if absent.

Required tests:

1. test_smoke_train_completes (data-backed):
   - Run run_smoke_train with max_epochs=1, max_steps=10, batch_size=4
   - Assert completes without exception
   - Assert result.total_steps >= 1
   - Assert result.all_losses_finite == True

2. test_loss_finite_throughout (data-backed):
   - Check all losses in per-step log are finite
   - Read training_log.jsonl and assert all "losses" values are finite numbers

3. test_per_loss_curve_logged (data-backed):
   - Read training_log.jsonl
   - Assert each entry contains all 10 loss names:
     l_action_effect, l_progress, l_regime, l_control_grammar, l_falsification,
     l_intent_action_mapping, l_change_point, l_reveal_shift, l_failed_action,
     l_temporal_consistency

4. test_grad_norm_logged (data-backed):
   - Each entry in training_log.jsonl has "grad_norm" key with numeric value

5. test_checkpoint_written (data-backed):
   - After smoke train, checkpoint_ep0.pt exists in output_dir

6. test_manifest_written (data-backed):
   - manifest.json exists in output_dir
   - Contains "seed", "n_steps", "n_epochs" keys

7. test_no_hidden_fields_in_batch (synthetic):
   - Use a mock batch dict with PublicObservation inputs
   - Call assert_no_objective_leakage on each public_input
   - Assert no error for clean public_inputs
   - Assert HiddenLabelLeakageError for contaminated ones

8. test_public_trace_logger (synthetic):
   - Create a PublicTraceLogger in a tmp_path
   - Log 3 steps with mock LossDict values
   - Assert 3 lines in training_log.jsonl
   - Assert each line has "step", "epoch", "losses", "grad_norm" keys

Helper fixture for data-backed tests:
```python
@pytest.fixture(scope="module")
def smoke_output_dir(tmp_path_factory):
    """Run smoke train once, return output dir."""
    data_root = Path("data/frcgw_text/v0_1")
    if not (data_root / "manifest.json").exists():
        pytest.skip("P2 dataset not present")
    
    out = tmp_path_factory.mktemp("smoke_out")
    run_smoke_train(
        train_cfg_path=Path("configs/train_text.yaml"),
        model_cfg_path=Path("configs/model_text.yaml"),
        output_dir=out,
    )
    return out
```
Note: Override max_steps=10 and max_epochs=1 for speed. You can pass these as kwargs to run_smoke_train or via a test-specific mini config dict.

ACCEPTANCE_CRITERIA:
  - pytest tests/test_train_text_smoke.py -q: ALL PASS (8 tests, 0 failures)
  - pytest tests/ -q: ALL PASS (158 existing + 8 new = 166 total, 0 regression)
  - configs/model_text.yaml populated (no null values for key fields)
  - configs/train_text.yaml populated (no null values for key fields)
  - All per-step losses finite (assert throughout training loop)
  - assert_no_objective_leakage called for each batch public_input
  - Source MD docstring in monitoring.py and train_text.py
  - RESULT.md written to .agent_tasks/codex_done/TASK_C7_train_smoke_RESULT.md

COMMIT_MESSAGE: feat(p3-c7): smoke train loop + monitoring + config population

STOP_CONDITION:
  - STOP if loss is nan or inf at any training step
  - STOP if smoke train crashes due to shape mismatch in any forward pass
  - STOP if forbidden fields appear in any batch during training
  - STOP if test_smoke_train_completes fails (even on 10 steps)
  - STOP if modifying any file outside FILES_ALLOWED
