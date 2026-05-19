TASK_NAME: TASK_LFD_005_temporal_consistency_and_seq_loss

BACKGROUND:
losses.py has 5 placeholder `_zero()` returns:
- Line 120: L_falsification guard (F_t is None or no labeled steps)
- Line 132: L_intent_action_mapping — always returns zero
- Line 150: L_temporal_consistency — always returns zero
- Lines 170-172: compute_total_loss world_model_output=None branches

The FalsificationDetectorHead (TASK_LFD_003) requires new losses:
1. L_seq_falsification: cumulative BCE on wrong_prob_learned across sequence steps
2. L_run_length_posterior: BOCPD KL divergence loss (soft target)
3. L_temporal_consistency (line 150): actual implementation replacing _zero()

These losses ONLY apply to v0_5 data where LFDOutput is available.
For v0_4 (no LFDOutput), all new losses return _zero() gracefully.

IMPORTANT: L_intent_action_mapping (line 132) stays as _zero() — no action
rewrite supervision is available yet. Do NOT implement this.

GOAL:
1. Implement L_seq_falsification (cumulative BCE over sequence).
2. Implement L_run_length_posterior (BOCPD KL divergence target).
3. Replace L_temporal_consistency placeholder with actual implementation.
4. Integrate new losses into compute_total_loss with proper weight keys.
5. Proxy OFF path: ensure no proxy heuristic enters loss computation.

FILES_ALLOWED:
- src/frcgw/objectives/losses.py
- tests/test_lfd_losses.py  (new file)

FILES_FORBIDDEN:
- .claude/
- CLAUDE.md
- .mcp.json
- .venv/
- data/
- outputs/
- secrets/
- .env*
- scripts/run_codex_task.ps1
- paper_context_ref/
- src/frcgw/schemas/visibility.py
- src/frcgw/models/
- src/frcgw/planning/
- src/frcgw/data/

REQUIRED_IMPLEMENTATION:
1. losses.py additions:

   def L_seq_falsification(
     lfd_wrong_probs: Tensor | None,     # [batch, T] or None
     targets: list[BatchTargets],
   ) -> Tensor:
     """Cumulative BCE on wrong_prob_learned across sequence steps.
     
     Uses true_wrong_hypothesis from targets (TRAINING_SUPERVISION bucket).
     If lfd_wrong_probs is None or no labeled steps: return _zero().
     """
     ...

   def L_run_length_posterior(
     run_length_posterior: Tensor | None,   # [batch, max_run_length] or None
     targets: list[BatchTargets],
   ) -> Tensor:
     """KL divergence from BOCPD posterior to soft target distribution.
     
     Soft target: uniform over observed run-length +/- tolerance window.
     If run_length_posterior is None: return _zero().
     """
     ...

   def L_temporal_consistency(posterior_entropy: Tensor) -> Tensor:
     """Temporal consistency loss: penalize sudden entropy jumps.
     
     Replaces _zero() placeholder. Computes smoothed entropy regularization.
     If posterior_entropy is None or constant: return _zero() gracefully.
     """
     # Replace current: return _zero(posterior_entropy)
     # Implement: L = mean(relu(entropy[t] - entropy[t-1] - margin))
     # Applied per batch; graceful if single-step (returns zero)
     ...

2. compute_total_loss updates:
   - Add `lfd_output` parameter (from FalsificationDetectorHead output or None)
   - Add new keys to LossDict: 'l_seq_falsification', 'l_run_length_posterior'
   - DEFAULT_WEIGHTS additions: 'l_seq_falsification': 1.0, 'l_run_length_posterior': 0.5
   - Proxy OFF: if `cfg.use_no_state_change_proxy` is True, issue WARNING
     "proxy heuristic active during LFD training — use proxy_off config"
     Do NOT modify planner.py here; this is a warning only.

3. L_intent_action_mapping: LEAVE AS _zero() — do not implement

REQUIRED_TESTS:
- tests/test_lfd_losses.py:
  - `test_seq_falsification_backward_computable`: loss.backward() succeeds
  - `test_seq_falsification_none_lfd_returns_zero`
  - `test_seq_falsification_labeled_steps_only`
  - `test_run_length_kl_range`: L_run_length_posterior >= 0
  - `test_run_length_kl_none_returns_zero`
  - `test_temporal_consistency_penalizes_sudden_jump`: large entropy jump → positive loss
  - `test_temporal_consistency_stable_returns_low`: stable entropy → near-zero loss
  - `test_compute_total_loss_with_lfd_output_keys_present`
  - `test_compute_total_loss_without_lfd_output_backward_compat`

ACCEPTANCE_CRITERIA:
- L_seq_falsification backward()-computable
- L_run_length_posterior >= 0 (KL divergence)
- L_temporal_consistency: large entropy jump → positive loss, stable → ~0
- compute_total_loss with lfd_output=None: identical to pre-change behavior
- L_intent_action_mapping still returns _zero() (unchanged)
- All listed tests pass

COMMIT_MESSAGE:
feat(loss): L_seq_falsification, L_run_length_posterior, L_temporal_consistency

Replaces _zero() placeholders for seq falsification and temporal consistency.
L_intent_action_mapping intentionally remains _zero(). v0_4 backward compat.

STOP_CONDITION:
STOP if:
1. TASK_LFD_003 not complete (LFDOutput dataclass required)
2. L_intent_action_mapping is given a real implementation (leave as _zero)
3. proxy heuristic logic is imported or used in loss computation
4. L_run_length_posterior < 0 (invalid KL)
5. Any modification to paper_context_ref/ or visibility.py

Dependencies: TASK_LFD_003 (LFDOutput dataclass), TASK_LFD_007 (metrics exist)
Checkpoint mapping: PHASE 5 (Checkpoint-5)
