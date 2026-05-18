TASK_NAME: step6_ft_wiring_planner_configs

BACKGROUND:
STEP 5 produced a trained checkpoint (loss 1.96→0.0081) but with l_falsification=0.0 in the
training config. That checkpoint is now registered as ABL-016 (no_falsification control).

STEP 6 goal: enable L_falsification in training + fix inference-time F_t (always=0 bug).

Two blockers identified by T1 audit (docs/orchestration/agent_reports/2026-05/):
B1: train_text.py:91-98 passes F_t=None hardcoded → L_falsification gradient never flows.
B2: planner.py:110-118 passes alt_hypotheses=[] → falsification_score() always returns 0 at inference.

Additionally T1 agent found:
- falsification_score() returns scalar but L_falsification expects [B] tensor → must loop+stack.
- true_action_effect_type is a string in BatchTargets; FalsificationEvidence expects int → needs EFFECT_TYPE_VOCAB mapping.

GOAL:
1. Fix train_text.py to compute F_t per-example (loop+stack to [B]) and pass to compute_total_loss.
2. Fix planner.py to call propose() BEFORE falsification_score(), passing alt IDs from propose() results.
3. Create training configs for falsification-enabled Stage 1 + Stage 2.
4. Create eval config pointing to falsification-enabled checkpoint.
5. Write tests verifying the fixes.

FILES_ALLOWED:
- src/frcgw/training/train_text.py
- src/frcgw/planning/planner.py
- configs/train_text_v0_3_falsification.yaml
- configs/train_text_v0_3_falsification_stage2.yaml
- configs/lr_eval_real_v0_3_falsification.yaml
- tests/test_step6_l_falsification_training_config.py
- tests/test_step6_planner_alt_hypothesis_emission.py

FILES_FORBIDDEN:
- outputs/**
- data/**
- paper_context_ref/**
- src/frcgw/schemas/visibility.py
- .claude/**
- scripts/run_codex_task.ps1
- src/frcgw/objectives/losses.py
- src/frcgw/falsification/lr_scorer.py
- configs/train_text.yaml
- configs/train_text_v0_3.yaml
- configs/train_text_v0_3_stage2.yaml
- configs/lr_eval_real_v0_3.yaml
- configs/lr_eval_real_v0_3_trained.yaml

REQUIRED_IMPLEMENTATION:

## 1. train_text.py — F_t wiring (per-example, stacked to [B])

In train_one_epoch(), after the existing model.forward() and world_model_heads.forward_given_action()
calls, add a block that computes F_t for every example in the batch:

```python
from frcgw.planning.falsification import FalsificationEvidence, falsification_score
from frcgw.objectives.losses import EFFECT_TYPE_VOCAB, GRAMMAR_VOCAB

# Compute per-example F_t tensor for L_falsification
# GRAMMAR_VOCAB keys: "direct","required_dropdown","modal_confirm","container_scroll",
#   "wait_until_enabled","permission_accept","filter_open","pagination"  (indices 0..7)
_GRAMMAR_N = max(GRAMMAR_VOCAB.values()) + 1  # = 8
_F_t_list = []
for t in targets:
    h_exec_id = 0  # training: use grammar index 0 as executing hypothesis
    alt_ids = [i for i in range(_GRAMMAR_N) if i != h_exec_id]  # deterministic enumeration
    effect_type_str = getattr(t, "true_action_effect_type", "none") or "none"
    effect_type_int = EFFECT_TYPE_VOCAB.get(effect_type_str, 0)
    evidence = FalsificationEvidence(
        observed_effect_type=effect_type_int,
        observed_progress_delta=float(getattr(t, "progress_delta", 0.0) or 0.0),
        observed_failed_action=bool(getattr(t, "true_failed_action", False)),
    )
    with torch.no_grad():
        # Detach shared_h and z_state for F_t computation — F_t gradient flows through the loss
        f_t_i = falsification_score(
            model,
            model_out.shared_h[:1] if model_out.shared_h.dim() > 1 else model_out.shared_h.unsqueeze(0),
            model_out.z_state[:1] if model_out.z_state.dim() > 1 else model_out.z_state.unsqueeze(0),
            action_type,
            h_exec_id,
            alt_ids,
            evidence,
        )
    _F_t_list.append(f_t_i.reshape(1))
F_t_batch = torch.cat(_F_t_list, dim=0)  # shape [B]
```

IMPORTANT: this per-example loop uses the first slice of shared_h/z_state as a proxy since
the current training loop uses a single batch forward pass. If model_out.shared_h is shape [1, D]
or [D] (due to batch collation), adjust accordingly. The key invariant: F_t_batch.shape[0] == len(targets).

Then replace the existing compute_total_loss call:
```python
# OLD:
# loss_dict = compute_total_loss(model_out, world_out, F_t=None, ...)
# NEW:
loss_dict = compute_total_loss(model_out, world_out, F_t=F_t_batch, targets=targets, weights=weights, public_input=public_inputs)
```

NOTE: Do NOT use torch.no_grad() around F_t_batch computation if l_falsification > 0 — the gradient
needs to flow. Remove the with torch.no_grad() wrapper shown above; it was illustrative only.
The actual implementation should compute F_t WITHOUT torch.no_grad() so that gradients flow through
the falsification head.

## 2. planner.py — move propose() before falsification_score()

Current order (lines 109-134):
  1. h_exec_id = planner_state.get_current(step_idx)
  2. F_t = falsification_score(..., alt_hypothesis_ids=[], ...)  ← always returns 0
  3. if F_t <= tau_f: early return
  4. latent_sample = ...
  5. alt_hypotheses = propose(...)

New order:
  1. h_exec_id = planner_state.get_current(step_idx)
  2. latent_sample = _latent_sample_from_output(model_out)
  3. alt_hypotheses = propose(latent_sample, model=None, ..., mode="posterior_only", k=3)
  4. alt_ids = [h.combined_id for h in alt_hypotheses if isinstance(h.combined_id, int)]
  5. F_t = falsification_score(..., alt_hypothesis_ids=alt_ids, ...)
  6. if F_t <= tau_f: early return (preserve early-exit logic)
  7. (rest of planning logic as before, alt_hypotheses already computed)

This ensures alt_ids is non-empty when propose() returns results. The posterior_only mode is
evidence-blind but provides structural non-zero F_t when model weights are trained. Document
this in a one-line comment: "# posterior_only: prior-ranked alts; evidence-blind by design at inference"

## 3. Training configs

### configs/train_text_v0_3_falsification.yaml
Copy train_text_v0_3.yaml with these changes:
- phase: CC-P3-STEP6
- objective_weights.l_falsification: 1.0
- max_steps: 300
- max_epochs: 3
- manifest_dir: "outputs/runs/p3_train_v0_3_falsification_stage1"
- notes: "STEP 6 Stage 1: falsification-enabled training. l_falsification=1.0. STEP 5 (ABL-016 control) used l_falsification=0.0."
Keep all other fields identical to train_text_v0_3.yaml (seed=42, batch_size=8, lr=0.001, etc.)

### configs/train_text_v0_3_falsification_stage2.yaml
- phase: CC-P3-STEP6
- objective_weights.l_falsification: 1.0
- max_steps: 800
- max_epochs: 6
- manifest_dir: "outputs/runs/p3_train_v0_3_falsification_stage2"
- notes: "STEP 6 Stage 2: falsification-enabled training stage 2. Conditional on Stage 1 PASS."

### configs/lr_eval_real_v0_3_falsification.yaml
Copy lr_eval_real_v0_3_trained.yaml (or lr_eval_real_v0_3.yaml) with these changes:
- For all FRCG-LR / FRCG-FULL agents: ckpt_path: "outputs/checkpoints/pretrain_v0_3_falsification/checkpoint_best.pt"
- out_dir: "outputs/runs/p3_lr_real_eval_step6_falsification_smoke"
- Add comment: "# STEP 6 eval: falsification-enabled checkpoint. Compare to STEP 5 ABL-016 control."

REQUIRED_TESTS:

### tests/test_step6_l_falsification_training_config.py

1. test_falsification_stage1_config_l_falsification_is_1(): load configs/train_text_v0_3_falsification.yaml, assert objective_weights["l_falsification"] == 1.0
2. test_falsification_stage2_config_l_falsification_is_1(): same for stage2 yaml
3. test_step5_abl016_configs_unchanged(): load configs/train_text_v0_3.yaml and configs/train_text_v0_3_stage2.yaml, assert objective_weights["l_falsification"] == 0.0 (ABL-016 control must remain unmodified)
4. test_falsification_eval_config_ckpt_path(): load configs/lr_eval_real_v0_3_falsification.yaml, assert all FRCG-type agent ckpt_paths contain "pretrain_v0_3_falsification"
5. test_falsification_eval_config_out_dir_not_step5(): load configs/lr_eval_real_v0_3_falsification.yaml, assert out_dir does NOT contain "step5" or "p3_lr_real_eval_step4" (safety: not overwriting old outputs)

### tests/test_step6_planner_alt_hypothesis_emission.py

6. test_planner_alt_hypotheses_non_empty_after_fix(): instantiate a minimal mock model, call text_frcg_plan(), assert F_t is NOT always 0.0 when propose() can return results (use mock propose to return 2 hypotheses).
7. test_planner_alt_hypotheses_ids_are_ints(): verify alt_ids list contains int values (not raw HypothesisId objects) before passing to falsification_score.
8. test_planner_early_exit_preserved(): when F_t <= tau_f, planner still returns early (PlanMetadata(planned=False)).

### tests/test_step6_ft_batch_shape.py (or add to above)

9. test_l_falsification_receives_batch_shaped_tensor(): mock training step with batch_size=4, assert L_falsification is called with F_t tensor of shape [4], not scalar.
10. test_effect_type_vocab_mapping_used(): verify FalsificationEvidence uses int effect_type (not string), using EFFECT_TYPE_VOCAB.

ACCEPTANCE_CRITERIA:
- tests/test_step6_l_falsification_training_config.py: 5 tests PASS
- tests/test_step6_planner_alt_hypothesis_emission.py + test_step6_ft_batch_shape.py: 5 tests PASS
- Mock training run (2 steps) shows l_falsification component non-zero for at least 1 batch when l_falsification=1.0 in config
- Inference: alt_hypotheses list is non-empty when model has loaded weights and propose() returns results
- losses.py DEFAULT_WEIGHTS unchanged (git diff src/frcgw/objectives/losses.py = empty)
- STEP 5 configs unchanged: git diff configs/train_text_v0_3.yaml = empty, git diff configs/train_text_v0_3_stage2.yaml = empty
- No changes to frcg_agent.py, eval_runner.py (scope boundary)

COMMIT_MESSAGE:
feat(step6/task1): F_t wiring fix + planner alt-hypothesis emission + falsification training configs

STOP_CONDITION:
Stop if: (1) any FORBIDDEN file is modified; (2) F_t computation introduces torch.no_grad() wrapper that blocks gradient flow; (3) STEP 5 config l_falsification values are changed from 0.0; (4) outputs/** are created or modified; (5) test assertions use magic float constants without documented source.

RELATED_AGENT_REPORT_IDS:
docs/orchestration/agent_reports/2026-05/mathematical_validity_critic_step6_T1_R1.md
docs/orchestration/agent_reports/2026-05/claim_metric_alignment_auditor_step6_T1_R1.md
