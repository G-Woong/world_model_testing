TASK_NAME: TASK_LFD_002_history_encoder_persistent_ht

BACKGROUND:
HistoryEncoder.forward (encoders.py:109) currently discards GRU hidden state:
  `gru_out, _ = self.gru(step_features)`  (line 142)
Returns a single Tensor of shape [batch, hidden_dim].

The FalsificationDetectorHead (PHASE 5) requires persistent episode-level
hidden state (h_t) to accumulate evidence across steps. This requires:
1. HistoryEncoder.forward to optionally accept h0 and return h_t_next
2. TextFRCGModel.forward to thread h_t through sequential episode steps
3. Training loop to handle both stateless (v0_4) and stateful (v0_5 LFD) paths

CRITICAL interface change (M1 from preflight checkpoint-0):
Changing HistoryEncoder.forward return type from Tensor to (Tensor, Tensor)
would break ALL callers. Instead, use a backward-compatible design:
- Add parameter `return_hidden: bool = False`
- If False (default): return Tensor as before (v0_4 compat)
- If True: return tuple(Tensor, Tensor) (new stateful path)
- h0: Tensor | None = None (if None, uses zeros like GRU default)

ALL CALLERS must be audited and updated where stateful path is needed:
- TextFRCGModel.forward (text_frcg_model.py:97-116): add optional h0, h_t_next
- Training loop (train_text.py): no h_t needed per-batch (stateless OK for P3)
- Rollout harness (planning/planner.py): episode-level h_t carry-over
- Any test that calls history_encoder.forward directly

GOAL:
1. Add `h0: Tensor | None = None` and `return_hidden: bool = False` to HistoryEncoder.forward.
2. Return `(out_tensor, h_t_next)` when `return_hidden=True`.
3. Update TextFRCGModel to optionally thread h_t.
4. Verify backward compat: all existing callers receive same output as before.
5. Add test for stateful vs stateless divergence.

FILES_ALLOWED:
- src/frcgw/models/encoders.py
- src/frcgw/models/text_frcg_model.py
- src/frcgw/planning/planner.py
- tests/test_persistent_ht.py  (new file)
- tests/test_encoder_backward_compat.py  (new file)

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
- src/frcgw/objectives/losses.py
- src/frcgw/data/
- src/frcgw/training/

REQUIRED_IMPLEMENTATION:
1. encoders.py — HistoryEncoder.forward signature:
   ```python
   def forward(
     self,
     history_list: list[list[PublicHistoryItem]],
     h0: Tensor | None = None,
     return_hidden: bool = False,
   ) -> Tensor | tuple[Tensor, Tensor]:
   ```
   - When h0 is None: GRU initializes to zeros (same as before)
   - When return_hidden=False: return out (same signature as v0_4)
   - When return_hidden=True: return (out, h_t_next) where h_t_next is
     the final GRU hidden state of shape [1, batch, hidden_dim]
   - gru call: `gru_out, h_t_next = self.gru(step_features, h0)`

2. text_frcg_model.py — TextFRCGModel:
   - Add optional `h_t: Tensor | None = None` parameter to forward()
   - When h_t is not None: pass to history_encoder with return_hidden=True
   - ModelOutput gains: `h_t_next: Tensor | None = None`
   - Default: h_t=None (backward compat, stateless path unchanged)

3. planning/planner.py:
   - `run_planning_step` signature: add `episode_h_t: Tensor | None = None`
   - Returns updated h_t_next if model supports it
   - Default: None (stateless, v0_4 behavior unchanged)

4. New test: tests/test_persistent_ht.py:
   - `test_h_t_carry_over_changes_output`: call forward twice with carry-over
     h_t, assert output differs from zero-init call on same input
   - `test_h_t_episode_reset_to_none`: after episode end, h_t reset to None
     produces same output as fresh episode with same inputs
   - `test_h_t_shape_correct`: h_t_next has shape [1, batch, hidden_dim]
   - `test_h_t_nonzero_after_nonempty_history`

5. New test: tests/test_encoder_backward_compat.py:
   - `test_forward_default_return_tensor_not_tuple`: return_hidden=False → Tensor
   - `test_forward_return_hidden_true_is_tuple`: return_hidden=True → tuple
   - `test_forward_h0_none_same_as_default`: no h0 produces same as default call

REQUIRED_TESTS:
All tests in test_persistent_ht.py and test_encoder_backward_compat.py.
All existing tests that import or use HistoryEncoder must still pass.
tests/test_forbidden_field_mirror_sync.py must remain GREEN.

ACCEPTANCE_CRITERIA:
- `return_hidden=False` path: identical output to pre-change forward() call
- `return_hidden=True` path: returns tuple (Tensor, Tensor)
- h_t carry-over produces different output from zero-init (test_h_t_carry_over_changes_output)
- h_t reset to None reproduces fresh-episode output (test_h_t_episode_reset)
- No existing test broken
- ModelOutput.h_t_next is None when called without h_t

COMMIT_MESSAGE:
feat(arch): HistoryEncoder persistent h_t with backward-compatible return_hidden flag

Adds h0/return_hidden params to HistoryEncoder.forward, threads h_t through
TextFRCGModel and planner, backward compat preserved via default params.

STOP_CONDITION:
STOP if:
1. HistoryEncoder.forward return type changes unconditionally (breaks callers)
2. Training loop broken by new signature
3. h_t shape incorrect ([1, batch, hidden_dim] required for GRU)
4. Any modification to paper_context_ref/ or visibility.py
5. Existing encoder tests fail

Dependencies: none (standalone arch change)
Checkpoint mapping: PHASE 4 (Checkpoint-4)
Required agent review: implementation-risk-critic (T3 trigger)
