TASK_NAME: C4_objectives

BACKGROUND:
P3 loss functions and training-pathway rewards.
Source: paper_context_ref/08_LOSS_REWARD_TRAINING_OBJECTIVE.md §L-MAIN-001..006, §L-AUX-001..005, §R-001..008

The loss module receives:
  - model_output: ModelOutput (from text_frcg_model.py) — posterior outputs only
  - world_model_output: RolloutResult (from world_model_heads.py) — effect/progress/failure predictions
  - F_t: Tensor (scalar per step) — falsification score (computed by falsification.py in C5)
  - targets: BatchTargets (from text_dataset.py) — supervision labels, NOT inference input
  - weights: dict[str, float] — loss weight config

Label vocabulary (from P2 dataset, confirmed):
  - true_regime: 8 classes (search_form, required_dropdown, modal_blocker, nested_scroll,
                             permission_gate, filter_accordion, pagination_vs_infinite, loading_delayed)
  - true_control_grammar: 8 classes (direct_search, required_dropdown_then_search, etc.)
  - true_change_point: int step index 0-11 (12 classes, stored as str in JSONL → parse to int)
  - true_reveal_vs_shift: 3 classes (none, reveal, shift)
  - true_action_effect_type: 7-class forward-compatible taxonomy
    current P2 data uses subset: none→0, reveal→1, shift→2, delayed→3
    taxonomy: none/no_change=0, reveal=1, shift=2, failed=3, delayed=4, noisy=5, no_op_valid=6
  - true_failed_action: bool
  - progress_delta: float
  - recovery_action_id: str or None (mask loss if None)
  - true_wrong_hypothesis: bool or None (from EvaluationLabels)

IMPORTANT about F_t:
  In C4, the L_falsification loss function TAKES F_t as an already-computed input tensor
  (it does NOT compute it internally). F_t will be provided by the falsification.py module
  in C5. For C4 implementation, design the signature to accept F_t: Tensor | None.
  When F_t is None, L_falsification = 0.0 (masked).

LABEL ENCODING STRATEGY:
  Build a static vocabulary mapping in losses.py:
  - REGIME_VOCAB: dict[str, int] (8 entries)
  - GRAMMAR_VOCAB: dict[str, int] (8 entries)
  - CHANGE_POINT_VOCAB: lambda x: int(x)  (parse int from str/int)
  - REVEAL_SHIFT_VOCAB: dict[str, int] = {"none": 0, "reveal": 1, "shift": 2}
  - EFFECT_TYPE_VOCAB: dict[str, int] = {"none": 0, "no_change": 0, "reveal": 1, "shift": 2,
                                          "failed": 3, "delayed": 4, "noisy": 5, "no_op_valid": 6}
  Note: "none" and "no_change" both map to 0 (equivalent in P2 data).

assert_no_objective_leakage(public_input):
  - Must call assert_agent_observation_safe(public_input) from frcgw.schemas.visibility
  - Called at the start of compute_total_loss() on the public_input (if provided)
  - Also: check that targets is NOT passed as public_input

EXISTING MODULES (already implemented, DO NOT modify):
  - src/frcgw/models/text_frcg_model.py: TextFRCGModel, ModelOutput
  - src/frcgw/models/world_model_heads.py: WorldModelHeads, RolloutResult
  - src/frcgw/models/latent_heads.py: LatentPosterior, LatentSample
  - src/frcgw/data/text_dataset.py: BatchTargets, StepSample

GOAL:
Implement src/frcgw/objectives/losses.py and src/frcgw/objectives/rewards.py.
Write tests/test_losses.py. All losses must be non-negative and finite.
L_total must have gradients on all trainable model parameters.

FILES_ALLOWED:
  - src/frcgw/objectives/losses.py
  - src/frcgw/objectives/rewards.py
  - src/frcgw/objectives/__init__.py
  - tests/test_losses.py

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

REQUIRED_IMPLEMENTATION:

src/frcgw/objectives/losses.py:
```python
"""frcgw.objectives.losses -- 6 main + 4 aux losses for P3 text model.

Source MD: paper_context_ref/08_LOSS_REWARD_TRAINING_OBJECTIVE.md §L-MAIN-001..006, §L-AUX-001..005
"""
```
Required:
1. Vocabulary dicts:
   REGIME_VOCAB: dict[str, int]   (8 classes)
   GRAMMAR_VOCAB: dict[str, int]  (8 classes)
   REVEAL_SHIFT_VOCAB: dict[str, int]  (3 classes: none=0, reveal=1, shift=2)
   EFFECT_TYPE_VOCAB: dict[str, int]  (7 classes: none/no_change=0, reveal=1, shift=2,
                                        failed=3, delayed=4, noisy=5, no_op_valid=6)

2. assert_no_objective_leakage(public_input):
   - Calls assert_agent_observation_safe from frcgw.schemas.visibility
   - Raises HiddenLabelLeakageError if forbidden field detected

3. @dataclass class LossDict:
   - l_action_effect: Tensor
   - l_progress: Tensor
   - l_regime: Tensor
   - l_control_grammar: Tensor
   - l_falsification: Tensor
   - l_intent_action_mapping: Tensor
   - l_change_point: Tensor
   - l_reveal_shift: Tensor
   - l_failed_action: Tensor
   - l_temporal_consistency: Tensor
   - l_total: Tensor
   - weights: dict[str, float]

4. Individual loss functions (each takes list[BatchTargets] and relevant predictions):
   - L_action_effect(effect_logits: Tensor, targets: list[BatchTargets]) -> Tensor
     CE(effect_logits, encode(true_action_effect_type, EFFECT_TYPE_VOCAB))
   - L_progress(progress_pred: Tensor, targets: list[BatchTargets]) -> Tensor
     MSE(progress_pred, progress_delta tensor)
   - L_regime(regime_logits: Tensor, targets: list[BatchTargets]) -> Tensor
     CE(regime_logits, encode(true_regime, REGIME_VOCAB))
   - L_control_grammar(grammar_logits: Tensor, targets: list[BatchTargets]) -> Tensor
     CE(grammar_logits, encode(true_control_grammar, GRAMMAR_VOCAB))
   - L_falsification(F_t: Tensor | None, targets: list[BatchTargets]) -> Tensor
     BCE(sigmoid(F_t), encode_bool(true_wrong_hypothesis))
     Returns 0.0 tensor if F_t is None OR if true_wrong_hypothesis is all None
   - L_intent_action_mapping(rewrite_logits: Tensor | None, targets: list[BatchTargets]) -> Tensor
     Returns 0.0 tensor if rewrite_logits is None or if all recovery_action_id are None
     (P3 stub: always returns 0.0 since rewrite head not yet integrated into loss)
   - L_change_point(change_logits: Tensor, targets: list[BatchTargets]) -> Tensor
     CE(change_logits, int(true_change_point))
   - L_reveal_shift(reveal_logits: Tensor, targets: list[BatchTargets]) -> Tensor
     CE(reveal_logits, encode(true_reveal_vs_shift, REVEAL_SHIFT_VOCAB))
   - L_failed_action(failed_score: Tensor, targets: list[BatchTargets]) -> Tensor
     BCE(failed_score, encode_bool(true_failed_action))
   - L_temporal_consistency(posterior_entropy: Tensor) -> Tensor
     Returns 0.0 tensor (placeholder; requires sequential batches — implement in P4)

5. compute_total_loss(
       model_output: ModelOutput,
       world_model_output: RolloutResult | None,
       F_t: Tensor | None,
       targets: list[BatchTargets],
       weights: dict[str, float] | None = None,
       public_input: list[PublicObservation] | None = None,
   ) -> LossDict:
   - If public_input is provided, calls assert_no_objective_leakage on each item
   - Computes all 10 losses
   - l_total = sum(w_k * L_k for k, w_k in weights.items())
   - Default weights: {l_action_effect:1.0, l_progress:0.5, l_regime:1.0, l_control_grammar:1.0,
                       l_falsification:1.0, l_intent_action_mapping:0.5, l_change_point:0.3,
                       l_reveal_shift:0.3, l_failed_action:0.3, l_temporal_consistency:0.1}
   - Returns LossDict

src/frcgw/objectives/rewards.py:
```python
"""frcgw.objectives.rewards -- Training-pathway reward components for P3.

Source MD: paper_context_ref/08_LOSS_REWARD_TRAINING_OBJECTIVE.md §R-001, R-003, R-004, R-008
"""
```
Required:
- R_progress(progress_delta: float | Tensor) -> float | Tensor  [R-001: clip(progress_delta, 0, 1)]
- R_failed_action_penalty(failed_action: bool | Tensor) -> float | Tensor  [R-003: -0.3 if failed]
- R_repeated_failure_penalty(n_consecutive_failures: int) -> float  [R-004: -0.1 * n]
- R_compute_cost(n_alt_candidates: int, H: int, beta: float = 0.1) -> float  [R-008: beta*n*H]

REQUIRED_TESTS:

tests/test_losses.py:
```python
"""Tests for P3 loss functions and objective leakage guard.

Source MD: paper_context_ref/08_LOSS_REWARD_TRAINING_OBJECTIVE.md
"""
```
Required test cases (use pytest.importorskip("torch") at top):

1. test_each_loss_nonneg_finite:
   - Create synthetic model_output, world_model_output, targets, F_t
   - assert all individual losses >= 0 and not nan

2. test_total_loss_has_grad:
   - model = TextFRCGModel()
   - pub = PublicObservation(instruction="test", history_public=[])
   - out = model(pub)
   - world_out = model.world_model_heads.forward_given_action(out.shared_h, out.z_state, "click", 0)
   - F_t = torch.zeros(1, requires_grad=True)
   - loss_dict = compute_total_loss(out, world_out, F_t, [mock_target])
   - loss_dict.l_total.backward()
   - assert any(p.grad is not None for p in model.parameters() if p.requires_grad)

3. test_recovery_mask:
   - target with recovery_action_id=None -> L_intent_action_mapping == 0.0

4. test_no_op_valid_not_false_positive:
   - Create target with true_action_effect_type="no_op_valid" and true_wrong_hypothesis=False
   - L_falsification should NOT be driven high by this case (true_wrong_hypothesis=False means it's not wrong)

5. test_weight_config_applied:
   - Compute total loss with default weights
   - Halve one weight (e.g., l_regime: 0.5 -> 0.25)
   - Recompute — l_total should change

6. test_assert_fires_on_leakage:
   - Create PublicObservation with dom_snapshot_public={"true_regime": "x"}
   - compute_total_loss(..., public_input=[leaky_obs]) should raise HiddenLabelLeakageError

7. test_falsification_none_returns_zero:
   - compute_total_loss with F_t=None -> l_falsification == 0.0

8. test_rewards_basic:
   - R_progress(0.5) == 0.5
   - R_failed_action_penalty(True) == -0.3
   - R_repeated_failure_penalty(3) == -0.3
   - R_compute_cost(3, 1, 0.1) == 0.3

Helper: create a mock BatchTargets with all required fields (use a fixture or helper function):
```python
def make_target(**kwargs) -> BatchTargets:
    defaults = dict(
        true_regime="search_form",
        true_control_grammar="direct_search",
        true_change_point="0",
        true_reveal_vs_shift="none",
        true_action_effect_type="none",
        true_failed_action=False,
        failure_reason=None,
        progress_delta=0.0,
        recovery_action_id=None,
        valid_hypothesis_switch=None,
        true_wrong_hypothesis=False,
        h_exec_id=None,
        correct_hypothesis_id=None,
    )
    defaults.update(kwargs)
    return BatchTargets(**defaults)
```

ACCEPTANCE_CRITERIA:
  - pytest tests/test_losses.py -q: ALL PASS (8 tests, 0 failures)
  - pytest tests/ -q: ALL PASS (126 existing + 8 new = 134 total, 0 regression)
  - All individual losses non-negative and finite (test_each_loss_nonneg_finite)
  - L_total.backward() puts gradients on TextFRCGModel parameters
  - assert_no_objective_leakage raises on forbidden field
  - Source MD docstring in both files
  - RESULT.md written to .agent_tasks/codex_done/TASK_C4_objectives_RESULT.md

COMMIT_MESSAGE: feat(p3-c4): 6-main+4-aux losses and training-pathway rewards

STOP_CONDITION:
  - STOP if any forbidden field (true_regime, true_control_grammar, etc.) used as loss input from public_input
  - STOP if L_total is nan or inf for synthetic inputs
  - STOP if L_total.backward() raises error
  - STOP if modifying any file under src/frcgw/models/
