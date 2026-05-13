TASK_NAME: C5_falsification_alt_proposer

BACKGROUND:
P3 falsification scorer (FALS-02) and alternative hypothesis proposer (PROP-03).
Source: paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md §FALS-02, §PROP-03

FALS-02 Falsification Score:
  F_t = max_{h_alt ∈ A_t^H} [ ell_t(h_alt) - ell_t(h_exec) ]

  ell_t(h) = log p_theta(e_t | H_{t-1}, a_{t-1}, h)
           = log Cat(true_action_effect_type | effect_logits(h, a, H))  [main term]
             + λ_p * log N(progress_delta | progress_pred(h), σ²)       [progress term]
             + λ_f * log p(failed_action | failure_score(h))             [failure term]

  Implementation details:
  - ell_t(h) = log_softmax(effect_logits(h))[observed_effect_idx]
               + λ_p * (-0.5 * (progress_pred(h) - progress_delta)^2)
               + λ_f * (log(failure_score(h)) if failed else log(1-failure_score(h)))
  - F_t = max(ell_alts) - ell_exec    # scalar tensor per step

  h_exec identification:
  - At TRAINING TIME: use targets.h_exec_id if available, otherwise use default hypothesis (0)
  - At INFERENCE TIME: tracked from history (planner.py in C6 handles this)
  - h_exec_id is a hypothesis index (int in [0, n_hypotheses-1] = [0, 63])
    The mapping: h_exec_id = regime_id * n_grammars + grammar_id

  no_op_valid handling:
  - When true_action_effect_type is "no_op_valid" (maps to 6) or "none" (maps to 0):
    the action was valid but had no observable effect → this is NOT evidence of wrong grammar
    → IMPORTANT: falsification score should NOT be driven up for these steps
  - Implementation: when evidence.observed_effect_type in {0, 6} (no_change or no_op_valid):
    return F_t = 0.0 (uninformative evidence)

PROP-03 Alternative Proposer:
  score(h_alt) = α_b * log_posterior(h_alt) + α_l * ell_t(h_alt)
  A_t^H = top_k(score, k=3)

  Hypothesis space: Cartesian product regime × grammar = 8 × 8 = 64 candidates
  HypothesisId: regime_id (0..7) + grammar_id (0..7) → combined_id = regime_id * 8 + grammar_id

  Mode variants:
  - "hybrid": score = α_b * log_prior + α_l * ell_t  [default]
  - "posterior_only": score = z_regime_logits + z_grammar_logits for each hypothesis
  - "random": score = torch.randn(64)
  - "oracle": only used with EvaluationLabels.correct_hypothesis_id (NEVER at inference)

EXISTING MODULES (DO NOT MODIFY):
  - src/frcgw/models/text_frcg_model.py: TextFRCGModel, ModelOutput
  - src/frcgw/models/world_model_heads.py: WorldModelHeads, RolloutResult
  - src/frcgw/models/latent_heads.py: LatentSample
  - src/frcgw/objectives/losses.py: EFFECT_TYPE_VOCAB

GOAL:
Implement src/frcgw/planning/falsification.py and src/frcgw/planning/alternative_proposer.py.
Write tests/test_falsification.py.

FILES_ALLOWED:
  - src/frcgw/planning/falsification.py
  - src/frcgw/planning/alternative_proposer.py
  - src/frcgw/planning/__init__.py
  - tests/test_falsification.py

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

REQUIRED_IMPLEMENTATION:

src/frcgw/planning/falsification.py:
```python
"""frcgw.planning.falsification -- Falsification scorer F_t (FALS-02).

Source MD: paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md §FALS-02
"""
```
Required:

@dataclass class FalsificationEvidence:
  observed_effect_type: int    # encoded effect type index (0-6)
  observed_progress_delta: float
  observed_failed_action: bool

def log_likelihood(
    rollout_result: RolloutResult,
    evidence: FalsificationEvidence,
    lambda_p: float = 0.5,
    lambda_f: float = 0.5,
) -> Tensor:
  """Compute ell_t(h) = log p(e_t | h).

  Source MD: paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md §FALS-02
  """
  - log_p_eff = log_softmax(rollout_result.effect_logits, dim=-1)[..., evidence.observed_effect_type]
  - log_p_prog = -0.5 * (rollout_result.progress_pred - evidence.observed_progress_delta)**2
  - If observed_failed_action is True:
      log_p_fail = torch.log(rollout_result.failed_score.clamp_min(1e-8))
    Else:
      log_p_fail = torch.log((1.0 - rollout_result.failed_score).clamp_min(1e-8))
  - Return log_p_eff + lambda_p * log_p_prog + lambda_f * log_p_fail

def falsification_score(
    model: TextFRCGModel,
    shared_h: Tensor,
    z_state: Tensor,
    action_type: str,
    h_exec_id: int,
    alt_hypothesis_ids: list[int],
    evidence: FalsificationEvidence,
    lambda_p: float = 0.5,
    lambda_f: float = 0.5,
) -> Tensor:
  """Compute F_t = max(ell_alts) - ell_exec.

  Source MD: paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md §FALS-02
  """
  - If evidence.observed_effect_type in {0, 6}:  # no_change or no_op_valid
      return torch.zeros((), dtype=shared_h.dtype, device=shared_h.device)
  - exec_rollout = model.world_model_heads.forward_given_action(shared_h, z_state, action_type, h_exec_id)
  - ell_exec = log_likelihood(exec_rollout, evidence, lambda_p, lambda_f)
  - ell_alts = [
      log_likelihood(model.world_model_heads.forward_given_action(shared_h, z_state, action_type, hid),
                     evidence, lambda_p, lambda_f)
      for hid in alt_hypothesis_ids
    ]
  - If no alts: return torch.zeros_like(ell_exec)
  - ell_max_alt = torch.stack(ell_alts).max()
  - return ell_max_alt - ell_exec  # F_t: scalar tensor

src/frcgw/planning/alternative_proposer.py:
```python
"""frcgw.planning.alternative_proposer -- Alternative hypothesis proposer (PROP-03).

Source MD: paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md §PROP-03
"""
```
Required:

@dataclass class HypothesisId:
  regime_id: int    # 0..n_regimes-1
  grammar_id: int   # 0..n_grammars-1
  combined_id: int  # regime_id * n_grammars + grammar_id

def enumerate_hypotheses(n_regimes: int = 8, n_grammars: int = 8) -> list[HypothesisId]:
  """Return all n_regimes * n_grammars hypothesis candidates."""
  - Return [HypothesisId(r, g, r*n_grammars+g) for r in range(n_regimes) for g in range(n_grammars)]

def log_prior(latent_sample: LatentSample, hypothesis: HypothesisId) -> Tensor:
  """log p(h) ≈ log_softmax(z_regime)[regime_id] + log_softmax(z_grammar)[grammar_id]."""
  - Using latent_sample.z_regime_logits and z_grammar_logits

def propose(
    latent_sample: LatentSample,
    model: TextFRCGModel | None,
    shared_h: Tensor | None,
    z_state: Tensor | None,
    action_type: str | None,
    evidence: FalsificationEvidence | None,
    k: int = 3,
    mode: str = "hybrid",
    n_regimes: int = 8,
    n_grammars: int = 8,
    alpha_b: float = 1.0,
    alpha_l: float = 1.0,
    oracle_hypothesis_id: int | None = None,
) -> list[HypothesisId]:
  """Propose top-k alternative hypotheses.

  Source MD: paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md §PROP-03
  """
  hypotheses = enumerate_hypotheses(n_regimes, n_grammars)
  if mode == "hybrid":
      - score(h) = alpha_b * log_prior(latent_sample, h) + alpha_l * ell_t(h)
      - ell_t requires model, shared_h, z_state, action_type, evidence
      - If any of these is None, fall back to "posterior_only"
  elif mode == "posterior_only":
      - score(h) = log_prior(latent_sample, h)
  elif mode == "random":
      - score(h) = random scalar (torch.randn)
  elif mode == "oracle":
      - Returns [h for h in hypotheses if h.combined_id == oracle_hypothesis_id] * k
        (oracle mode: always propose the correct hypothesis; NEVER called at inference)
  - Return top_k(hypotheses, scores, k)

REQUIRED_TESTS:

tests/test_falsification.py:
Required test cases:

1. test_falsification_positive_when_alt_better:
   - Create two hypothesis rollout results where alt has better log_likelihood than exec
   - Confirm F_t > 0

2. test_falsification_negative_when_exec_correct:
   - Create situation where exec_rollout explains evidence better (high effect prob at correct class)
   - Confirm F_t <= 0

3. test_no_op_valid_not_driven_up:
   - evidence.observed_effect_type = 6 (no_op_valid) OR = 0 (no_change)
   - F_t = falsification_score(... evidence with type=0 ...) 
   - assert F_t == 0.0

4. test_falsification_scalar:
   - F_t from falsification_score is a 0-dim tensor (scalar)
   - assert F_t.ndim == 0 or F_t.shape == () or F_t.numel() == 1

5. test_propose_returns_k_hypotheses:
   - propose(latent_sample, ..., k=3, mode="posterior_only") returns 3 HypothesisIds
   - All have valid regime_id ∈ [0,7] and grammar_id ∈ [0,7]

6. test_modes_differ:
   - propose(mode="random", ...) with different seeds → different results
   - propose(mode="posterior_only") → deterministic

7. test_enumerate_hypotheses:
   - enumerate_hypotheses(8, 8) returns 64 items
   - combined_ids are unique
   - combined_id == regime_id * 8 + grammar_id

8. test_log_likelihood_finite:
   - log_likelihood(rollout, evidence) returns finite scalar

9. test_no_evidence_empty_alts:
   - falsification_score(..., alt_hypothesis_ids=[]) returns 0.0

ACCEPTANCE_CRITERIA:
  - pytest tests/test_falsification.py -q: ALL PASS (9 tests)
  - pytest tests/ -q: ALL PASS (134 existing + 9 new = 143 total)
  - F_t is 0.0 for no_change/no_op_valid evidence (CRITICAL: prevents false falsification)
  - falsification_score does NOT require hidden labels as input
  - propose() "oracle" mode only usable if oracle_hypothesis_id is provided (NEVER called at inference)
  - Source MD docstring present in both files
  - RESULT.md written to .agent_tasks/codex_done/TASK_C5_falsification_alt_proposer_RESULT.md

COMMIT_MESSAGE: feat(p3-c5): falsification scorer (FALS-02) + alternative proposer (PROP-03)

STOP_CONDITION:
  - STOP if oracle_hypothesis_id (or oracle_grammar_action) is used at inference time
    (propose() is called at inference in mode="hybrid" or "posterior_only" only)
  - STOP if F_t uses EvaluationLabels.h_exec_id as inference input
    (h_exec_id should only be used in training to look up the correct hypothesis)
  - STOP if test_no_op_valid_not_driven_up fails
  - STOP if modifying any file outside FILES_ALLOWED
