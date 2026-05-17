TASK_NAME: C6_gate_rewrite_planner

BACKGROUND:
P3 decision gate, rewrite module, and closed-loop planner.
Source: paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md §G_hybrid, §RW-02, §RW-06, §12

Decision Gate G_hybrid:
  should_plan = (F_t > τ_f AND ΔV_t > τ_v AND P_switch > τ_a AND ΔV_t - C_plan > 0)
  Where:
  - F_t: falsification score from falsification.py
  - ΔV_t: expected value improvement = max(V(h_alt)) - V(h_exec)
    V(h) ≈ progress_pred from world_model_heads.forward_given_action
  - P_switch: action selection probability change = P(selected action changes with h*)
  - C_plan: planning compute cost = beta * len(alt_candidates) * H
  
  CRITICAL: uncertainty (posterior_entropy) alone MUST NEVER open the hybrid gate.
  Test for this: high entropy + F_t=0 → should_plan=False.

  Gate ablation modes (for Step 7 eval, not executed in P3):
  - "hybrid": the 4-condition gate above (default)
  - "falsification_only": should_plan = F_t > τ_f
  - "uncertainty_only": should_plan = posterior_entropy > τ_u
  - "always_plan": should_plan = True
  - "never_plan": should_plan = False

Rewrite (RW-02 + RW-06 fallback):
  rewrite_action(intent_emb, h_star, candidates, model):
    grammar_emb = model.grammar_embed(h_star.combined_id)  # (1, 32)
    intent_emb from instruction text (or action summary)
    For each candidate in candidates:
      score = rewrite_head(cat([intent_emb, cand_emb, grammar_emb]))
    top = candidates[argmax(scores)]
    return top

  Rewrite head: simple MLP in TextFRCGModel — for P3, use a stub that always returns
  the first candidate ranked by (action_type similarity to h_star grammar's expected action).
  
  RW-06 fallback conditions:
  - validate_rewrite returns False if:
    a) selected action not in candidates list
    b) rewrite_confidence < τ_r (config threshold)
  - On fallback: return base_action (first candidate or original action)

  IMPORTANT: oracle_grammar_action is NEVER used at inference time.
  At training time it's used only as a supervision target for L_intent_action_mapping (in losses.py).

text_frcg_plan() — closed-loop step (§12 pseudocode):
  1. assert_agent_observation_safe(public_obs)  ← MANDATORY
  2. model.forward(public_obs) → model_out
  3. evidence = extract_evidence(public_obs) → FalsificationEvidence
     (from last history item's action/effect summary text)
  4. h_exec_id = tracker.get_current(step_idx)  ← from PlannerState tracker, NOT from EvaluationLabels
  5. F_t = falsification_score(model, shared_h, z_state, action_type, h_exec_id, [], evidence)
     (no alts yet — just compute F_t for gate decision)
  6. If F_t <= τ_f: return base_action, PlanMetadata(planned=False, reason="low_F_t")
  7. alt_hypotheses = propose(latent_sample, mode="posterior_only", k=3)
     (Use posterior_only for P3 — hybrid requires evidence-based ell which needs action_type)
  8. alt_ids = [h.combined_id for h in alt_hypotheses]
  9. Compute V(h_exec) and V(h_alts) using world_model_heads.rollout_step for H=1
     - Get a "base action" from candidates (first candidate's action_type)
     - V(h) = rollout.progress_pred for each hypothesis
  10. ΔV_t = max(V(h_alts)) - V(h_exec)
  11. P_switch = 1.0 if argmax(V(h_alts)) != h_exec_id else 0.0  (simplified P3 version)
  12. C_plan = cfg.C_plan_beta * len(alt_hypotheses) * 1  (H=1)
  13. gate_input = GateInput(F_t, ΔV_t, P_switch, C_plan, model_out.posterior_entropy.item())
  14. gate_out = gate.decide(gate_input, cfg)
  15. If not gate_out.should_plan: return base_action, PlanMetadata(planned=False, reason=gate_out.reason)
  16. h_star = alt_hypotheses[argmax(V(h_alts))]
  17. rewrite_result = rewrite_action(instruction, h_star, candidates, model)
  18. valid, reason = validate_rewrite(rewrite_result, public_obs, τ_r=cfg.τ_r)
  19. If valid: return rewrite_result, PlanMetadata(planned=True, h_star=h_star)
      Else: return base_action, PlanMetadata(planned=False, reason=f"rewrite_invalid:{reason}")

PlannerState tracker:
  - Simple dict: {step_idx: hypothesis_id}
  - get_current(step_idx) → h_exec_id (defaults to 0 if not tracked)
  - update(step_idx, hypothesis_id) → update tracking

EXISTING MODULES (DO NOT MODIFY):
  - src/frcgw/planning/falsification.py: FalsificationEvidence, falsification_score, log_likelihood
  - src/frcgw/planning/alternative_proposer.py: HypothesisId, propose, enumerate_hypotheses
  - src/frcgw/models/text_frcg_model.py: TextFRCGModel, ModelOutput
  - src/frcgw/schemas/visibility.py: assert_agent_observation_safe

GOAL:
Implement decision_gate.py, rewrite.py, planner.py.
Write tests/test_decision_gate.py and tests/test_rewrite.py.
Do NOT modify falsification.py or alternative_proposer.py.

FILES_ALLOWED:
  - src/frcgw/planning/decision_gate.py
  - src/frcgw/planning/rewrite.py
  - src/frcgw/planning/planner.py
  - src/frcgw/planning/__init__.py
  - tests/test_decision_gate.py
  - tests/test_rewrite.py

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
  - src/frcgw/planning/falsification.py
  - src/frcgw/planning/alternative_proposer.py

REQUIRED_IMPLEMENTATION:

src/frcgw/planning/decision_gate.py:
```python
"""frcgw.planning.decision_gate -- G_hybrid 4-condition decision gate.

Source MD: paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md §G_hybrid
"""
```
Required:

@dataclass class GateConfig:
  gate_mode: str = "hybrid"   # hybrid, falsification_only, uncertainty_only, always_plan, never_plan
  tau_f: float = 0.0           # falsification threshold
  tau_v: float = 0.0           # value improvement threshold
  tau_a: float = 0.5           # action switch probability threshold
  tau_u: float = 2.0           # uncertainty threshold (for uncertainty_only mode)
  C_plan_beta: float = 0.1
  tau_r: float = 0.5           # rewrite confidence threshold

@dataclass class GateInput:
  F_t: float
  delta_V: float
  P_switch: float
  C_plan: float
  posterior_entropy: float = 0.0

@dataclass class GateOutput:
  should_plan: bool
  reason: str
  components: dict  # {"F_t": ..., "delta_V": ..., "P_switch": ..., "C_plan": ...}

def decide(gi: GateInput, cfg: GateConfig | None = None) -> GateOutput:
  """Evaluate gate condition based on cfg.gate_mode."""
  - hybrid: should_plan = (gi.F_t > cfg.tau_f AND gi.delta_V > cfg.tau_v
                           AND gi.P_switch > cfg.tau_a AND gi.delta_V - gi.C_plan > 0)
  - falsification_only: should_plan = gi.F_t > cfg.tau_f
  - uncertainty_only: should_plan = gi.posterior_entropy > cfg.tau_u
  - always_plan: should_plan = True
  - never_plan: should_plan = False
  - Returns GateOutput with reason string ("all_conditions_met", "low_F_t", "low_delta_V",
    "low_P_switch", "cost_exceeds_benefit", "always_plan", "never_plan", "uncertainty_only")

src/frcgw/planning/rewrite.py:
```python
"""frcgw.planning.rewrite -- Grammar-conditioned action rewrite (RW-02 + RW-06).

Source MD: paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md §RW-02, §RW-06
"""
```
Required:

def rewrite_action(
    instruction: str,
    h_star: HypothesisId,
    candidates: list[CandidateAction],
    model: TextFRCGModel,
) -> tuple[CandidateAction | None, float]:
  """Return (best_candidate, confidence) based on grammar-conditioned ranking.

  Source MD: paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md §RW-02
  """
  - If no candidates: return None, 0.0
  - grammar_emb = model.grammar_embed(h_star.combined_id)  # (1, 32)
  - For each candidate: score = action_similarity(candidate.action_type, grammar_emb, model)
    Simple implementation: hash-based action embedding dot grammar_embedding
  - top_candidate = candidates[argmax(scores)]
  - confidence = softmax(scores)[argmax] if len>1 else 1.0
  - return top_candidate, confidence.item()

def validate_rewrite(
    candidate: CandidateAction | None,
    public_obs: PublicObservation,
    confidence: float,
    tau_r: float = 0.5,
) -> tuple[bool, str]:
  """Validate rewrite output (RW-06 fallback check).

  Source MD: paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md §RW-06
  """
  - If candidate is None: return False, "no_candidate"
  - candidate_ids = {c.action_id for c in public_obs.candidate_actions_public}
  - If candidate.action_id not in candidate_ids: return False, "not_in_candidates"
  - If confidence < tau_r: return False, "low_confidence"
  - return True, "ok"

src/frcgw/planning/planner.py:
```python
"""frcgw.planning.planner -- text_frcg_plan closed-loop step function.

Source MD: paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md §12
"""
```
Required:

@dataclass class PlanMetadata:
  planned: bool
  reason: str
  h_star: HypothesisId | None = None
  F_t: float = 0.0
  delta_V: float = 0.0

class PlannerState:
  """Tracks h_exec per step index. NOT backed by EvaluationLabels at inference."""
  def get_current(self, step_idx: int) -> int:  # returns hypothesis combined_id
  def update(self, step_idx: int, hypothesis_id: int) -> None

def text_frcg_plan(
    public_obs: PublicObservation,
    step_idx: int,
    candidates: list[CandidateAction],
    model: TextFRCGModel,
    planner_state: PlannerState,
    cfg: GateConfig | None = None,
) -> tuple[CandidateAction, PlanMetadata]:
  """Closed-loop planning step.

  Source MD: paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md §12
  """
  - Step 1: assert_agent_observation_safe(public_obs)  ← MANDATORY
  - Step 2: base_action = candidates[0] if candidates else CandidateAction("noop", "noop", {})
  - Step 3: model.forward(public_obs) → model_out
  - Step 4: extract last history item's effect_type for evidence
    effect_text = last_history_item.effect_summary or "none"
    observed_effect_type = map to int via simple rule:
      "none"|"no_change" → 0, "reveal" → 1, "shift" → 2, "failed" → 3,
      "delayed" → 4, "noisy" → 5, "no_op_valid" → 6, default → 0
    evidence = FalsificationEvidence(observed_effect_type, 0.0, False)
  - Step 5: h_exec_id = planner_state.get_current(step_idx)
  - Step 6: F_t_tensor = falsification_score(model, model_out.shared_h, model_out.z_state,
                                              base_action.action_type, h_exec_id, [], evidence)
  - Step 7: cfg = cfg or GateConfig()
  - If F_t <= cfg.tau_f:
      return base_action, PlanMetadata(planned=False, reason="low_F_t", F_t=F_t_tensor.item())
  - Step 8: alt_hypotheses = propose(LatentSample from model_out, model=None, mode="posterior_only", k=3)
    Note: Need to reconstruct LatentSample from model_out — create helper or pass fields directly
  - Step 9: Compute ΔV for each hypothesis
    - V(h) = rollout.progress_pred.item() from model.world_model_heads.rollout_step(...)
    - For each alt_h and h_exec, use base_action.action_type and H=1
  - Step 10-12: Compute gate input and decide
  - Step 13-19: Rewrite if gate opens, else return base_action

  Helper for LatentSample from ModelOutput:
    from frcgw.models.latent_heads import LatentSample
    latent_sample = LatentSample(
        z_state=model_out.z_state,
        z_regime_logits=model_out.z_regime_logits,
        z_grammar_logits=model_out.z_grammar_logits,
        z_change_logits=model_out.z_change_logits,
        z_reveal_shift_logits=model_out.z_reveal_shift_logits,
        shared_h=model_out.shared_h,
        posterior_entropy=model_out.posterior_entropy,
        aux_precondition=model_out.aux_precondition,
        aux_failure_risk=model_out.aux_failure_risk,
    )

REQUIRED_TESTS:

tests/test_decision_gate.py:

1. test_hybrid_all_conditions_met:
   - GateInput(F_t=1.0, delta_V=1.0, P_switch=0.9, C_plan=0.1)
   - cfg with tau_f=0.0, tau_v=0.0, tau_a=0.5
   - assert gate.decide(gi, cfg).should_plan == True

2. test_hybrid_missing_one_condition:
   - Test 4 cases, each with one condition failing:
     a) F_t <= tau_f
     b) delta_V <= tau_v
     c) P_switch <= tau_a
     d) delta_V - C_plan <= 0
   - For each: assert should_plan == False

3. test_uncertainty_alone_does_not_open_hybrid_gate:
   - GateInput(F_t=0.0, delta_V=0.0, P_switch=0.0, C_plan=0.0, posterior_entropy=100.0)
   - cfg.gate_mode = "hybrid"
   - assert gate.decide(gi, cfg).should_plan == False  ← CRITICAL test

4. test_always_plan_mode:
   - GateInput with all zeros
   - cfg.gate_mode = "always_plan"
   - assert should_plan == True

5. test_never_plan_mode:
   - Any GateInput
   - cfg.gate_mode = "never_plan"
   - assert should_plan == False

6. test_uncertainty_only_mode:
   - GateInput(posterior_entropy=3.0)
   - cfg.gate_mode = "uncertainty_only", tau_u=2.0
   - assert should_plan == True
   - GateInput(posterior_entropy=1.0) → should_plan == False

7. test_cost_exceeds_benefit:
   - GateInput(F_t=1.0, delta_V=0.2, P_switch=0.9, C_plan=0.5)
   - delta_V(0.2) - C_plan(0.5) = -0.3 < 0 → should_plan == False

tests/test_rewrite.py:

1. test_rewrite_action_returns_candidate:
   - model = TextFRCGModel()
   - pub = PublicObservation(instruction="submit form", ...)
   - cands = [CandidateAction("a1", "click", {}), CandidateAction("a2", "submit", {})]
   - h_star = HypothesisId(0, 0, 0)
   - cand, conf = rewrite_action("submit form", h_star, cands, model)
   - assert cand in cands
   - assert 0.0 <= conf <= 1.0

2. test_rewrite_different_grammar_changes_ranking:
   - Use two different h_star grammars (grammar_id=0 vs grammar_id=7)
   - Run rewrite_action with each
   - (Soft assertion: at least one of the two should select different top candidate for some inputs)
   - If both select same: assert confidence values differ

3. test_rewrite_invalid_not_in_candidates:
   - validate_rewrite(CandidateAction("X", "X", {}), public_obs_with_empty_candidates, 0.9)
   - assert valid==False and reason=="not_in_candidates"

4. test_rewrite_low_confidence_fallback:
   - validate_rewrite(valid_candidate, public_obs, confidence=0.1, tau_r=0.5)
   - assert valid==False and reason=="low_confidence"

5. test_validate_rewrite_valid:
   - candidate is in public_obs.candidate_actions_public, confidence > tau_r
   - assert valid==True, reason=="ok"

6. test_planner_no_hidden_fields:
   - pub = PublicObservation(instruction="search", history_public=[])
   - model = TextFRCGModel()
   - planner_state = PlannerState()
   - cands = [CandidateAction("a1", "search", {})]
   - action, meta = text_frcg_plan(pub, 0, cands, model, planner_state)
   - assert isinstance(action, CandidateAction)
   - assert isinstance(meta, PlanMetadata)
   - (No forbidden field access in forward path)

7. test_planner_assert_fires_on_leakage:
   - pub = PublicObservation(instruction="x", dom_snapshot_public={"true_regime": "y"})
   - text_frcg_plan(pub, ...) should raise HiddenLabelLeakageError

8. test_h_exec_tracking:
   - planner_state = PlannerState()
   - planner_state.update(0, 5)
   - assert planner_state.get_current(0) == 5
   - assert planner_state.get_current(99) == 0  # default

ACCEPTANCE_CRITERIA:
  - pytest tests/test_decision_gate.py -q: ALL PASS (7 tests)
  - pytest tests/test_rewrite.py -q: ALL PASS (8 tests)
  - pytest tests/ -q: ALL PASS (143 existing + 15 new = 158 total, 0 regression)
  - test_uncertainty_alone_does_not_open_hybrid_gate: PASS (CRITICAL)
  - test_planner_assert_fires_on_leakage: PASS (CRITICAL)
  - text_frcg_plan: does not use EvaluationLabels or oracle fields at inference
  - Source MD docstring present in all 3 new files
  - RESULT.md written to .agent_tasks/codex_done/TASK_C6_gate_rewrite_planner_RESULT.md

COMMIT_MESSAGE: feat(p3-c6): decision gate (G_hybrid) + rewrite (RW-02/06) + planner

STOP_CONDITION:
  - STOP if oracle_grammar_action used in planner inference path
  - STOP if EvaluationLabels fields accessed in text_frcg_plan
  - STOP if test_uncertainty_alone_does_not_open_hybrid_gate fails
  - STOP if text_frcg_plan does not call assert_agent_observation_safe
  - STOP if modifying falsification.py or alternative_proposer.py
