# P3 Codex Task Decomposition

P3 tiny FRCG text model 구현을 위한 7개 Codex sub-task 헤더 목록.
각 TASK 파일은 `.agent_tasks/codex_queue/` 에 작성된다.

## Task List

| TASK ID | 파일 | 의존성 | 상태 |
|---|---|---|---|
| C1_text_dataset_loader | src/frcgw/data/text_dataset.py + tests/test_text_dataset.py | P2 schema/data | PENDING |
| C2_encoders | src/frcgw/models/encoders.py + latent_heads.py + test | C1 | PENDING |
| C3_world_model_and_model | src/frcgw/models/world_model_heads.py + text_frcg_model.py + test | C2 | PENDING |
| C4_objectives | src/frcgw/objectives/losses.py + rewards.py + tests/test_losses.py | C3 | PENDING |
| C5_falsification_alt_proposer | src/frcgw/planning/falsification.py + alternative_proposer.py + test | C3 | PENDING |
| C6_gate_rewrite_planner | planning/decision_gate.py + rewrite.py + planner.py + tests | C5 | PENDING |
| C7_train_smoke | training/train_text.py + monitoring.py + configs + scripts + test | C1..C6 | PENDING |

---

## TASK C1: text_dataset_loader

```
TASK_NAME: C1_text_dataset_loader
BACKGROUND: P2 phase generated 200 episodes / 1002 steps in data/frcgw_text/v0_1/{train,valid,test_id}.jsonl.
  StepRecord schema is in src/frcgw/schemas/step_schema.py.
  Forbidden inference fields are defined in src/frcgw/schemas/visibility.py::FORBIDDEN_AGENT_FIELDS.
  assert_agent_observation_safe() must be called on every public_input before it leaves the collator.
GOAL: Implement a PyTorch Dataset + collator that loads StepRecord JSONL shards and returns
  two distinct objects per batch: (1) public_input (PublicObservation only) and (2) targets
  (TrainingLabels + EvaluationLabels in a separate dataclass). CounterfactualRecord must NEVER appear
  in public_input. Leakage assert must fire on every batch.
FILES_ALLOWED:
  - src/frcgw/data/text_dataset.py
  - tests/test_text_dataset.py
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
REQUIRED_IMPLEMENTATION:
  - class StepBatch(dataclass): public_input: PublicObservation, targets: BatchTargets
  - class BatchTargets(dataclass): all TrainingLabels + EvaluationLabels fields (no CounterfactualRecord, no AuditMetadata)
  - class TextStepDataset(Dataset): loads JSONL from shard path, returns StepBatch
  - def collate_fn(batch: list[StepBatch]) -> CollatedBatch: pads and stacks; calls assert_agent_observation_safe on every public_input
  - def build_dataloaders(manifest_path, batch_size, seed) -> (train_dl, valid_dl, test_dl)
  - Source MD docstring: "Source MD: paper_context_ref/06_DATA_SCHEMA_AND_LABELING.md"
REQUIRED_TESTS:
  - test_collator_returns_only_public_input: public_input has NO forbidden fields
  - test_forbidden_fields_absent: 15 forbidden fields not in batch.public_input keys
  - test_targets_contain_all_labels: BatchTargets has true_regime, true_control_grammar, true_action_effect_type, true_wrong_hypothesis etc.
  - test_counterfactual_not_in_batch: CounterfactualRecord fields absent from public_input
  - test_batch_shape_consistent: shapes match across train/valid/test splits
  - test_assert_fires_on_leakage: assert_agent_observation_safe raises if forbidden field injected
ACCEPTANCE_CRITERIA:
  - pytest tests/test_text_dataset.py -q: ALL PASS
  - assert_agent_observation_safe called in collator
  - Source MD docstring present
  - RESULT.md written to .agent_tasks/codex_done/
COMMIT_MESSAGE: feat(p3-c1): text dataset loader with leakage-safe collator
STOP_CONDITION: STOP if any forbidden field appears in public_input; STOP if CounterfactualRecord fields in batch.
```

---

## TASK C2: encoders

```
TASK_NAME: C2_encoders
BACKGROUND: P3 tiny model uses hash-based vocab (vocab_size=4096, embed_dim=64).
  TextStateEncoder: instruction + dom_snapshot_public text → 2-layer Transformer(d=128, heads=4, ff=256) → CLS pool.
  HistoryEncoder: per-step (action_type, effect_type, flags) features → GRU(hidden=128, 1 layer).
  LatentPosterior: shared MLP → 4 head linears (z_state=32, z_regime=4, z_control_grammar=8, z_change_point=7).
  AuxHeads: precondition(BCE), failure_risk(BCE).
  All from paper_context_ref/07_LATENT_ARCHITECTURE_DESIGN.md §MOD-07-003, 007, 010-017.
GOAL: Implement encoders.py (TextStateEncoder, HistoryEncoder) and latent_heads.py (LatentPosterior, AuxHeads).
  Each class docstring must cite source MD. No hidden fields as input. deterministic given seed.
FILES_ALLOWED:
  - src/frcgw/models/encoders.py
  - src/frcgw/models/latent_heads.py
  - tests/test_text_frcg_model.py
FILES_FORBIDDEN: [same standard list as C1]
REQUIRED_IMPLEMENTATION:
  - TextStateEncoder(vocab_size, embed_dim, d_model, nhead, num_layers, max_seq_len)
  - HistoryEncoder(action_vocab_size, effect_vocab_size, hidden_dim)
  - LatentPosterior(input_dim, z_state_dim, n_regimes, n_grammars, n_change_types): returns LatentSample dataclass
  - AuxHeads(input_dim): precondition_head, failure_risk_head
  - LatentSample dataclass: z_state, z_regime_logits, z_grammar_logits, z_change_logits, posterior_entropy
  - Source MD docstring: "Source MD: paper_context_ref/07_LATENT_ARCHITECTURE_DESIGN.md"
REQUIRED_TESTS:
  - test_text_state_encoder_shape: output (B, d_model)
  - test_history_encoder_shape: output (B, hidden_dim)
  - test_latent_posterior_keys: LatentSample has all required fields
  - test_deterministic_given_seed: same input → same output
  - test_no_hidden_fields_required: forward takes only public_input fields
ACCEPTANCE_CRITERIA:
  - pytest tests/test_text_frcg_model.py -q (subset): ALL PASS
  - Source MD docstring present in each class
  - RESULT.md written
COMMIT_MESSAGE: feat(p3-c2): TextStateEncoder + HistoryEncoder + LatentPosterior
STOP_CONDITION: STOP if any hidden label field required as model input.
```

---

## TASK C3: world_model_and_model

```
TASK_NAME: C3_world_model_and_model
BACKGROUND: WorldModelHeads takes [h_t || z || action_emb] and predicts:
  effect_type_logits (7-class), progress_delta (scalar), failed_action (BCE).
  These predictions are used both for loss computation AND for falsification likelihood.
  TextFRCGModel is the top-level wrapper integrating all encoders + latent + world model heads.
  Source: paper_context_ref/07_LATENT_ARCHITECTURE_DESIGN.md §MOD-07-018, 021.
GOAL: Implement world_model_heads.py and text_frcg_model.py. TextFRCGModel.forward(public_input)
  returns a ModelOutput dataclass with all head outputs. No hidden field as input.
FILES_ALLOWED:
  - src/frcgw/models/world_model_heads.py
  - src/frcgw/models/text_frcg_model.py
  - tests/test_text_frcg_model.py
FILES_FORBIDDEN: [same standard list]
REQUIRED_IMPLEMENTATION:
  - WorldModelHeads(d_model, n_actions, n_effect_types): effect_head, progress_head, failure_head
  - WorldModelHeads.rollout_step(h_t, z, action_emb, hypothesis_emb, H=1) -> RolloutResult
  - TextFRCGModel(model_cfg): integrates TextStateEncoder, HistoryEncoder, LatentPosterior, AuxHeads, WorldModelHeads, RewriteHead (stub for C6)
  - ModelOutput dataclass: z_state, z_regime_logits, z_grammar_logits, z_change_logits, effect_logits, progress_pred, failed_score, posterior_entropy, aux_precondition, aux_failure_risk
  - TextFRCGModel.forward(public_input: PublicObservation) -> ModelOutput
  - Source MD docstring in each class
REQUIRED_TESTS:
  - test_model_output_keys: ModelOutput has all required keys
  - test_effect_logits_shape: (B, n_effect_types)
  - test_progress_pred_shape: (B, 1) or scalar
  - test_forward_no_hidden_fields: forward does NOT require forbidden fields
  - test_deterministic_seed: same batch → same output
ACCEPTANCE_CRITERIA:
  - pytest tests/test_text_frcg_model.py -q: ALL PASS
  - Source MD docstring present
  - RESULT.md written
COMMIT_MESSAGE: feat(p3-c3): WorldModelHeads + TextFRCGModel forward
STOP_CONDITION: STOP if hidden fields required in forward. STOP if any head shape mismatch.
```

---

## TASK C4: objectives

```
TASK_NAME: C4_objectives
BACKGROUND: 6 main losses + 4 aux losses from paper_context_ref/08_LOSS_REWARD_TRAINING_OBJECTIVE.md.
  Targets come from BatchTargets (TrainingLabels + EvaluationLabels). public_input must NOT be used
  as loss target. L_intent_action_mapping must be masked to 0 when recovery_action_id is None.
  L_falsification uses true_wrong_hypothesis from EvaluationLabels (target side only).
  Rewards R-001, R-003, R-004, R-008 are training-pathway tensors.
GOAL: Implement losses.py and rewards.py. compute_total_loss(model_output, targets, weights) must
  be differentiable. assert_no_objective_leakage(public_input) must be called at batch start.
FILES_ALLOWED:
  - src/frcgw/objectives/losses.py
  - src/frcgw/objectives/rewards.py
  - tests/test_losses.py
FILES_FORBIDDEN: [same standard list]
REQUIRED_IMPLEMENTATION:
  - assert_no_objective_leakage(public_input): raises if forbidden field in public_input
  - L_action_effect(effect_logits, targets) -> Tensor
  - L_progress(progress_pred, targets) -> Tensor
  - L_regime(regime_logits, targets) -> Tensor
  - L_control_grammar(grammar_logits, targets) -> Tensor
  - L_falsification(F_t, targets) -> Tensor [BCE(sigmoid(F_t), true_wrong_hypothesis)]
  - L_intent_action_mapping(rewrite_logits, targets) -> Tensor [masked]
  - L_change_point, L_reveal_shift, L_failed_action, L_temporal_consistency aux losses
  - compute_total_loss(model_output, targets, weights: dict) -> LossDict
  - R_progress, R_failed_action_penalty, R_repeated_failure_penalty, R_compute_cost in rewards.py
  - Source MD docstring: "Source MD: paper_context_ref/08_LOSS_REWARD_TRAINING_OBJECTIVE.md"
REQUIRED_TESTS:
  - test_each_loss_nonneg_finite: all losses >= 0 and finite
  - test_total_loss_has_grad: L_total.backward() does not error, grad on all params
  - test_recovery_mask: L_intent_action_mapping = 0 when recovery_action_id is None
  - test_no_op_valid_not_false_positive: no_op_valid step → true_wrong_hypothesis=False
  - test_weight_config_applied: halving a weight → L_total changes proportionally
  - test_assert_fires_on_leakage: assert_no_objective_leakage raises on forbidden field
ACCEPTANCE_CRITERIA:
  - pytest tests/test_losses.py -q: ALL PASS
  - Source MD docstring present
  - RESULT.md written
COMMIT_MESSAGE: feat(p3-c4): 6-main+4-aux losses and training-pathway rewards
STOP_CONDITION: STOP if any forbidden field used as loss target from public_input.
```

---

## TASK C5: falsification_alt_proposer

```
TASK_NAME: C5_falsification_alt_proposer
BACKGROUND: Falsification score F_t = max_{h_alt}[ell(h_alt) - ell(h_exec)] where
  ell_t(h) = log p(effect | h, a, H) + λ_p*log p(progress | h) + λ_f*log p(failure | h).
  h_exec comes from EvaluationLabels.h_exec_id (target side). At inference: from history tracker.
  Alternative proposer (PROP-03): score(h_alt) = α_b*log_posterior(h_alt) + α_l*ell(h_alt), top_k=3.
  Hypothesis space: Cartesian product of regime × grammar (max 32 candidates).
  Source: paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md §FALS-02, PROP-03.
GOAL: Implement falsification.py and alternative_proposer.py. F_t must be scalar per step.
  When alt explains evidence better → F_t > 0. When h_exec correct → F_t ≤ 0.
  no_op_valid evidence must NOT drive F_t up.
FILES_ALLOWED:
  - src/frcgw/planning/falsification.py
  - src/frcgw/planning/alternative_proposer.py
  - tests/test_falsification.py
FILES_FORBIDDEN: [same standard list]
REQUIRED_IMPLEMENTATION:
  - log_likelihood(model, history_enc, action_emb, hypothesis_emb, evidence) -> Tensor (scalar)
  - falsification_score(model, history_enc, action_emb, h_exec, alt_hypotheses, evidence) -> Tensor
  - enumerate_hypotheses(n_regimes, n_grammars) -> list[HypothesisId]
  - propose(posterior: LatentSample, evidence, k=3, mode="hybrid") -> list[HypothesisId]
  - Hypothesis modes: "hybrid", "posterior_only", "random", "oracle" (for Step 7)
  - HypothesisId dataclass: regime_id, grammar_id (integers)
  - Source MD: "Source MD: paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md"
REQUIRED_TESTS:
  - test_falsification_positive_when_alt_better: F_t > 0 when alt grammar explains effect better
  - test_falsification_negative_when_exec_correct: F_t < 0 when h_exec correct
  - test_no_op_valid_not_driven_up: no_op_valid evidence → F_t not positively biased
  - test_falsification_scalar: shape is () or (1,) per step
  - test_propose_returns_k_hypotheses: propose(k=3) returns 3 HypothesisIds
  - test_modes_differ: hybrid vs random → different results (stochastic seed test)
ACCEPTANCE_CRITERIA:
  - pytest tests/test_falsification.py -q: ALL PASS
  - Source MD docstring present
  - RESULT.md written
COMMIT_MESSAGE: feat(p3-c5): falsification scorer (FALS-02) + alternative proposer (PROP-03)
STOP_CONDITION: STOP if F_t uses hidden labels. STOP if EvaluationLabels fields appear in inference path.
```

---

## TASK C6: gate_rewrite_planner

```
TASK_NAME: C6_gate_rewrite_planner
BACKGROUND: Decision gate G_hybrid: should_plan = (F_t > τ_f AND ΔV_t > τ_v AND P_switch > τ_a
  AND ΔV_t - C_plan > 0). Uncertainty alone must NEVER open the hybrid gate.
  Rewrite (RW-02): grammar-conditioned ranking head. oracle_grammar_action is NOT used at inference.
  RW-06 fallback: if rewrite_confidence < τ_r or action not in candidates → return base_action.
  Planner: text_frcg_plan(state, history, candidates, model) implements 09_PLANNING_THEORY §12 pseudocode.
  Source: paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md §G_hybrid, RW-02, RW-06, §12.
GOAL: Implement decision_gate.py, rewrite.py, planner.py with tests.
  Gate ablation modes: hybrid, falsification_only, uncertainty_only, always_plan, never_plan.
FILES_ALLOWED:
  - src/frcgw/planning/decision_gate.py
  - src/frcgw/planning/rewrite.py
  - src/frcgw/planning/planner.py
  - tests/test_decision_gate.py
  - tests/test_rewrite.py
FILES_FORBIDDEN: [same standard list]
REQUIRED_IMPLEMENTATION:
  - GateInput dataclass: F_t, ΔV_t, P_switch, C_plan, posterior_entropy
  - GateOutput dataclass: should_plan, best_hypothesis, reason, components
  - decide(gi: GateInput, cfg) -> GateOutput with mode switch
  - rewrite_action(intent_emb, h_star, candidates, model) -> ActionRecord
  - validate_rewrite(a, public_obs, conf, τ_r) -> (bool, str)
  - text_frcg_plan(public_obs, history, candidates, model, cfg) -> (ActionRecord, PlanMetadata)
  - assert_agent_observation_safe(public_obs) called in text_frcg_plan
  - Source MD: "Source MD: paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md"
REQUIRED_TESTS:
  - test_hybrid_gate_all_conditions_required: missing any 1 of 4 → should_plan=False
  - test_uncertainty_alone_does_not_open_hybrid_gate: high entropy, low F_t → False
  - test_c_plan_exceeds_dv: C_plan > ΔV_t → should_plan=False
  - test_ablation_modes: always_plan=True, never_plan=False, uncertainty_only=entropy>τ_u
  - test_rewrite_grammar_changes_ranking: different h_star grammar → different top action
  - test_rewrite_invalid_not_in_candidates: action not in candidates → invalid
  - test_rewrite_low_confidence_fallback: conf < τ_r → (False, "low_confidence")
  - test_planner_no_hidden_fields: text_frcg_plan does not require forbidden fields
  - test_h_exec_tracking: h_exec_id from history, not from EvaluationLabels at inference
ACCEPTANCE_CRITERIA:
  - pytest tests/test_decision_gate.py tests/test_rewrite.py -q: ALL PASS
  - Source MD docstring present
  - RESULT.md written
COMMIT_MESSAGE: feat(p3-c6): decision gate (G_hybrid) + rewrite (RW-02/06) + planner
STOP_CONDITION: STOP if oracle_grammar_action used at inference. STOP if hidden fields in planner input.
```

---

## TASK C7: train_smoke

```
TASK_NAME: C7_train_smoke
BACKGROUND: Smoke training: ≤2 epochs, batch=8, ≤80 steps on CPU. All 7 test files must pass.
  configs/model_text.yaml and configs/train_text.yaml are P0 stubs (null values) that C7 populates.
  scripts/02_train_text_smoke.py is the CLI entrypoint.
  monitoring.py logs per-loss curve and grad-norm per step.
  Checkpoint + manifest written to outputs/runs/p3_smoke/ (NOT committed to git).
  Source: paper_context_ref/11_MODEL_DATASET_SCALE_AND_TRAINING_BUDGET_v1.md §tiny model.
GOAL: Implement train_text.py, monitoring.py, populate configs, create CLI script, write smoke test.
  Smoke train must complete in ≤5 min on CPU with finite loss throughout.
FILES_ALLOWED:
  - src/frcgw/training/train_text.py
  - src/frcgw/training/monitoring.py
  - configs/model_text.yaml
  - configs/train_text.yaml
  - scripts/02_train_text_smoke.py
  - tests/test_train_text_smoke.py
FILES_FORBIDDEN: [same standard list]
REQUIRED_IMPLEMENTATION:
  - train_one_epoch(model, dataloader, optimizer, loss_fn, monitoring, device) -> EpochResult
  - run_smoke_train(cfg_path, model_cfg_path, output_dir) -> SmokeResult
  - PublicTraceLogger: logs per-loss scalars + grad-norm per step to JSONL
  - Checkpoint: saves model state_dict + config + manifest.json after each epoch
  - configs/model_text.yaml: populate (vocab_size=4096, embed_dim=64, d_model=128, nhead=4, num_layers=2, hidden_dim=128, z_state_dim=32, n_regimes=4, n_grammars=8, n_change_types=7, n_effect_types=7)
  - configs/train_text.yaml: populate (seed=42, batch_size=8, max_steps=80, max_epochs=2, lr=1e-3, weight_decay=1e-4, loss_weights={...}, gate_thresholds={τ_f:0.0, τ_v:0.0, τ_a:0.5}, C_plan_beta=0.1)
  - 02_train_text_smoke.py: CLI with --config, --model-config, --output-dir args
  - Source MD: "Source MD: paper_context_ref/11_MODEL_DATASET_SCALE_AND_TRAINING_BUDGET_v1.md"
REQUIRED_TESTS:
  - test_smoke_train_completes: ≤2 epoch ≤80 step run completes without error
  - test_loss_finite_throughout: all per-step losses are finite (not nan/inf)
  - test_per_loss_curve_logged: monitoring JSONL contains all 10 loss names
  - test_grad_norm_logged: grad_norm key in monitoring log
  - test_checkpoint_written: outputs/runs/p3_smoke/checkpoint_ep0.pt exists
  - test_manifest_written: manifest.json with seed, config, n_steps fields
  - test_no_hidden_fields_in_batch: assert_no_objective_leakage passes on every batch
ACCEPTANCE_CRITERIA:
  - pytest tests/test_train_text_smoke.py -q: ALL PASS
  - Smoke train runs end-to-end without nan loss
  - checkpoint + manifest in outputs/runs/p3_smoke/
  - Source MD docstring present
  - RESULT.md written
COMMIT_MESSAGE: feat(p3-c7): smoke train loop + monitoring + config population
STOP_CONDITION: STOP if nan/inf loss persists >3 consecutive steps. STOP if hidden fields in any batch.
```
