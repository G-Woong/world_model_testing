TASK_NAME: step8_base026027_faithful
SANDBOX_MODE: bypass

BACKGROUND:
FRCG-WM STEP 8. BASE-026 (WAC-style) and BASE-027 (CUWM-style) currently use heuristic proxies with approximation_level="heuristic". STEP 8 upgrades them to faithful candidates. Leakage audit (leakage_step8_v04_baselines_R1) confirmed: both classes must NEVER access true_control_grammar, true_regime, oracle_grammar_action, oracle_best_action, or any FORBIDDEN_AGENT_FIELD through the eval_labels argument or any inference path. BASE-028 (WebWorld) stays heuristic (STEP 9).

GOAL:
1. Add WACFaithfulCandidate and CUWMFaithfulCandidate classes to src/frcgw/evaluation/baselines.py.
2. Create scripts/audit_step8_direct_threat_baselines.py.
3. Create tests/test_step8_direct_threat_baselines.py.
4. Create docs/orchestration/lr_alignment/39_step8_direct_baseline_faithfulness.md.

FILES_ALLOWED:
- src/frcgw/evaluation/baselines.py (Edit: add two new classes)
- tests/test_step8_direct_threat_baselines.py (NEW)
- docs/orchestration/lr_alignment/39_step8_direct_baseline_faithfulness.md (NEW)
- scripts/audit_step8_direct_threat_baselines.py (NEW)
- .agent_tasks/codex_done/TASK_1083_step8_base026027_faithful_RESULT.md

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
WACFaithfulCandidate class (baselines.py):
- Inherits from BaselineAgent
- Class attribute: approximation_level: str = "partial"  # honest — WAC full grammar posterior requires trained discriminative model
- Class attribute: baseline_id: str = "BASE-026-faithful"
- act(self, obs: PublicObservation, eval_labels: dict | None = None) -> CandidateAction:
  - FIRST LINE: assert eval_labels is None or not (FORBIDDEN_AGENT_KEYS & set(eval_labels or {})), f"Hidden label leak: {FORBIDDEN_AGENT_KEYS & set(eval_labels or {})}"
  - Grammar posterior estimation from history_public:
    - Count "no_state_change" events per action_type in history (failure signal)
    - Each candidate grammar hypothesis = the action families visible in candidate_actions_public
    - Grammar posterior: P(grammar=g | history) proportional to (1 - no_state_change_rate(g))
  - Consequence correction: select the candidate action with highest posterior-weighted success probability
  - If history empty or all actions have same posterior: fall back to first candidate
  - MUST NOT import TrainingLabels, EvaluationLabels, or StepAuditMetadata from step_schema
  - MUST NOT call GrammarEngine from text_env.grammar with any true grammar value
  - docstring must cite: "WAC §3.2 grammar posterior + consequence correction. approximation_level=partial: full WAC requires trained discriminative model. Heuristic: beta-Binomial counting from public history."

CUWMFaithfulCandidate class (baselines.py):
- Inherits from BaselineAgent
- Class attribute: approximation_level: str = "partial"  # honest — full CUWM requires trained world model rollout
- Class attribute: baseline_id: str = "BASE-027-faithful"
- act(self, obs: PublicObservation, eval_labels: dict | None = None) -> CandidateAction:
  - FIRST LINE: assert eval_labels is None or not (FORBIDDEN_AGENT_KEYS & set(eval_labels or {})), f"Hidden label leak: {FORBIDDEN_AGENT_KEYS & set(eval_labels or {})}"
  - K-candidate simulation (K = min(len(candidates), 5)):
    - For each candidate action in obs.candidate_actions_public[:K]:
      - Simulate 1-step rollout: estimate effect_type from action_type heuristic (e.g., "close_modal" → likely "blocker_removed"; "wait" → likely "delayed_effect"; else "state_change")
      - Score = {task_complete: 2.0, blocker_removed: 1.5, state_change: 1.0, delayed_effect: 0.5, no_state_change: 0.0}[simulated_effect]
      - Add bonus for actions not previously tried (from history_public)
    - Select candidate with highest score
  - MUST NOT read counterfactual_progress_delta or counterfactual_failure_risk from eval_labels
  - MUST NOT import GrammarEngine with any true grammar value
  - docstring: "CUWM §4 K-candidate simulation + task progress prediction. approximation_level=partial: full CUWM requires trained world model rollout. Heuristic: action_type→effect_type rule table."

Forbidden wording (ZERO occurrences in any file, comment, string, docstring, log):
- "defeats WAC"
- "outperforms CUWM"
- "superior to WebWorld"

scripts/audit_step8_direct_threat_baselines.py:
- Args: --eval-root (path to eval runs dir), --out (output JSON path)
- Reads metrics from: {eval_root}/{agent_id}_*/{split}_metrics.json
- For agent_ids: FRCG-LR, BASE-026-faithful, BASE-027-faithful, BASE-026-heuristic, BASE-027-heuristic, BASE-028-heuristic
- For each baseline: record approximation_level, task_success_rate mean, wrong_grammar_persistence mean, forbidden_wording_count (scan the baseline agent class source for forbidden strings)
- forbidden_wording_count must be 0 for gate PASS
- Output JSON: {baseline_id: {approximation_level, metrics, forbidden_wording_count, gate_pass}}

tests/test_step8_direct_threat_baselines.py:
- test_wac_faithful_no_eval_labels: call WACFaithfulCandidate().act(mock_obs, eval_labels={"true_control_grammar": "direct_search"}) → expect AssertionError (leakage guard triggers)
- test_cuwm_faithful_no_hidden_labels: call CUWMFaithfulCandidate().act(mock_obs, eval_labels={"oracle_best_action": "some_action"}) → expect AssertionError
- test_approximation_level_honest: verify both classes have approximation_level field with value in {"partial", "faithful_candidate", "heuristic"}
- test_forbidden_wording_absent: scan baselines.py source for "defeats WAC", "outperforms CUWM", "superior to WebWorld" → assert count=0
- All 4 tests must pass

REQUIRED_TESTS:
- tests/test_step8_direct_threat_baselines.py: all 4 tests green
- existing: python -m pytest tests/test_forbidden_field_mirror_sync.py tests/test_leakage_auditor.py -q (must stay green)

ACCEPTANCE_CRITERIA:
1. WACFaithfulCandidate and CUWMFaithfulCandidate exist in baselines.py with correct structure
2. Both classes have FORBIDDEN_AGENT_KEYS assertion as first line of act()
3. approximation_level="partial" with honest docstring
4. Forbidden wording count=0 in source
5. All 4 tests green + leakage tests stay green
6. doc 39 exists with faithfulness verification criteria and reviewer wording guard

COMMIT_MESSAGE:
feat(step8/task6): WACFaithfulCandidate + CUWMFaithfulCandidate (partial faithful)

STOP_CONDITION:
Stop if: implementing the faithful classes requires reading true_control_grammar or any FORBIDDEN field — in that case they remain approximation_level="partial" with explicit honest description. This is expected and acceptable.

RELATED_AGENT_REPORT_IDS: leakage_step8_v04_baselines_R1, claim_metric_step8_alignment_R1
