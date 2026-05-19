TASK_NAME: TASK_LFD_003_bocpd_run_length_head

BACKGROUND:
The FalsificationDetectorHead is the core learned component of LFD.
It takes persistent h_t (from TASK_LFD_002) + current step features as input
and produces:
- `wrong_prob_learned`: P(wrong hypothesis | history up to step t)
- `run_length_posterior`: P(R_t = r) for r in {1, ..., max_run_length}
- `cusum_stat_t`: CUSUM-style accumulated score (soft, not hard threshold)

The head uses Bayesian Online Change Point Detection (BOCPD) concepts:
Adams & MacKay (2007). Bayesian Online Changepoint Detection. arXiv:0710.3742.

CRITICAL ARCHITECTURAL DECISION (M2 from preflight checkpoint-0):
falsification.py:66-67 has a short-circuit that returns zero for effect_type {0,6}:
  `if evidence.observed_effect_type in {0, 6}: return zeros`
This short-circuit was designed for the deterministic log-likelihood score.
The BOCPD head MUST bypass this short-circuit:
- The head receives h_t (accumulated history) and step features BEFORE filtering
- The head does NOT call falsification_score() — it is a parallel path
- falsification_score() remains intact as the deterministic baseline input feature
  for the head (not the gate). Its output is used as one input feature to the head.
Design: FalsificationDetectorHead input = [h_t, z_state, current_effect_residual, F_t_deterministic]
where F_t_deterministic is the existing falsification_score() output (may be zero for {0,6}).

This design:
1. Preserves falsification_score() (no deletion, no modification)
2. Feeds F_t_deterministic as a feature to the head (so the head can LEARN when {0,6} is informative)
3. Gives the head full access to h_t without the {0,6} filter
4. Avoids the 65%+ dead input problem from the CRITICAL-2 risk

GOAL:
1. Implement FalsificationDetectorHead as a new module.
2. Add forward() interface that takes h_t + z_state + effect_residual + F_t_deterministic.
3. Outputs: wrong_prob_learned, run_length_posterior, cusum_stat_t.
4. Integrate into TextFRCGModel (optional pass, disabled by default).
5. Tests for BOCPD recursion, gradient flow, non-constant output.

FILES_ALLOWED:
- src/frcgw/models/falsification_head.py  (new file)
- src/frcgw/models/text_frcg_model.py
- src/frcgw/models/encoders.py  (read-only, no change expected)
- tests/test_lfd_head.py  (new file)
- tests/test_bocpd_recursion.py  (new file)

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
- src/frcgw/planning/falsification.py  (DO NOT MODIFY — preserve deterministic path)
- src/frcgw/objectives/losses.py  (loss changes in TASK_LFD_005)
- src/frcgw/data/

REQUIRED_IMPLEMENTATION:
1. src/frcgw/models/falsification_head.py (new):

   """FalsificationDetectorHead — Learned sequential falsification detector.
   
   Source MD: paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md FALS-03
   Architecture: BOCPD run-length posterior + effect residual + persistent h_t
   Reference: Adams & MacKay (2007). Bayesian Online Changepoint Detection.
   """
   
   @dataclass
   class LFDOutput:
     wrong_prob_learned: Tensor      # [batch] sigmoid output
     run_length_posterior: Tensor    # [batch, max_run_length] softmax
     cusum_stat_t: Tensor            # [batch] scalar CUSUM accumulator
   
   class FalsificationDetectorHead(nn.Module):
     def __init__(
       self,
       h_dim: int = 128,
       z_state_dim: int = 32,
       max_run_length: int = 20,
       effect_input_dim: int = 16,
     ):
       super().__init__()
       # Inputs: h_t (h_dim) + z_state (z_state_dim) + effect_residual (effect_input_dim) + F_t_scalar (1)
       input_dim = h_dim + z_state_dim + effect_input_dim + 1
       self.input_proj = nn.Linear(input_dim, h_dim)
       self.gru_cell = nn.GRUCell(h_dim, h_dim)
       self.wrong_prob_head = nn.Linear(h_dim, 1)    # → sigmoid → wrong_prob
       self.run_length_head = nn.Linear(h_dim, max_run_length)  # → softmax
       self.cusum_head = nn.Linear(h_dim, 1)         # → scalar
       self.max_run_length = max_run_length
     
     def forward(
       self,
       h_t: Tensor,                 # [batch, h_dim] from HistoryEncoder
       z_state: Tensor,             # [batch, z_state_dim] from LatentPosterior
       effect_residual: Tensor,     # [batch, effect_input_dim] current step effect
       F_t_deterministic: Tensor,   # [batch] from falsification_score() — may be 0
       head_h0: Tensor | None = None,  # [batch, h_dim] head's own recurrent state
     ) -> tuple[LFDOutput, Tensor]:
       """Returns (LFDOutput, head_h_next)."""
       ...
     
     def _bocpd_run_length_update(
       self, prior_logits: Tensor, new_evidence_score: Tensor
     ) -> Tensor:
       """Approximate BOCPD run-length posterior update.
       
       Soft version: prior run-length logits shifted by hazard + new evidence score.
       """
       ...

2. TextFRCGModel integration:
   - Add optional `falsification_head: FalsificationDetectorHead | None = None`
   - `ModelOutput` gains: `lfd_output: LFDOutput | None = None`
   - `forward()` with `h_t`, `head_h0`, `return_lfd=False` params
   - Default: return_lfd=False (backward compat)

REQUIRED_TESTS:
- tests/test_lfd_head.py:
  - `test_wrong_prob_range`: wrong_prob_learned in [0, 1]
  - `test_run_length_posterior_sums_to_one`: sum(run_length_posterior, dim=-1) ≈ 1
  - `test_run_length_posterior_nonuniform`: not all equal after evidence
  - `test_cusum_stat_nonzero_after_mismatch`: cusum_stat_t > 0 after mismatch evidence
  - `test_gradient_flows_to_wrong_prob_head`: loss.backward() succeeds, grad non-zero
  - `test_gradient_flows_to_run_length_head`
  - `test_head_h_next_shape_correct`
  - `test_wrong_prob_changes_across_steps_with_mismatch`: non-constant over 5 steps

- tests/test_bocpd_recursion.py:
  - `test_run_length_posterior_reset_on_change_point`: high evidence → posterior shifts to short run
  - `test_run_length_posterior_grows_on_stable`: stable signal → posterior shifts to long run
  - `test_bocpd_update_preserves_normalization`

ACCEPTANCE_CRITERIA:
- wrong_prob_learned in [0, 1] (sigmoid output)
- run_length_posterior sums to 1 (softmax)
- Gradient flows to all head outputs
- wrong_prob changes non-trivially across 5 sequential mismatch steps
- falsification_score() in planning/falsification.py UNCHANGED (verify no diff)
- All listed tests pass

COMMIT_MESSAGE:
feat(model): FalsificationDetectorHead with BOCPD run-length posterior

Adds learned falsification head with wrong_prob_learned, run_length_posterior,
cusum_stat_t. Bypasses {0,6} short-circuit via parallel h_t input path.
deterministic falsification_score() preserved as input feature.

STOP_CONDITION:
STOP if:
1. TASK_LFD_002 not complete (h_t carry-over required)
2. falsification.py is modified (DELETE FORBIDDEN — it's a preserved baseline feature)
3. wrong_prob_learned is constant across inputs (no learning signal)
4. run_length_posterior does not sum to 1
5. Any modification to paper_context_ref/ or visibility.py

Dependencies: TASK_LFD_002 (persistent h_t)
Checkpoint mapping: PHASE 5 (Checkpoint-5)
Required agent review: implementation-risk-critic (T3), mathematical-validity-critic
