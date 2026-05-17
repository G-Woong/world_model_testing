TASK_NAME: TASK_1039_step4_counterfactual_rollout
SANDBOX_MODE: bypass

BACKGROUND: |
  FRCG-WM STEP 4 — B1 blocker.
  collector.py:391 `counterfactuals=[]` 하드코딩으로 C4 metric을 위한 데이터가 전혀 없다.
  (C4_rollout_fidelity metric 함수는 STEP 5로 이관; 이 Task는 데이터 생성만 unblock)

  `CounterfactualRecord` (step_schema.py:86-98)가 이미 정의되어 있다:
    - counterfactual_id: str
    - source_step_id: str
    - candidate_action: CandidateAction
    - hypothesis_id: str
    - counterfactual_effect_type: str  (enum: state_change/no_state_change/blocker_removed/delayed_effect/task_complete)
    - counterfactual_progress_delta: float
    - counterfactual_failure_risk: float
    - is_oracle_best: bool

  `GrammarEngine.apply(hidden_preconditions, action_id)` 가 engine.py에 존재한다.
  `validation.py:40-48 _COUNTERFACTUAL_BATCH_FIELDS` 로 leakage guard 존재.
  `visibility.py FORBIDDEN_AGENT_FIELDS` 는 수정 불가.

  현재 episode collection loop (collector.py:340-410):
  - pre_state, action_record, engine이 step_index loop 내에 존재함
  - L391: `counterfactuals=[]`
  - 후보 action 목록: `obs.candidate_actions_public` (공개 안전)

  반드시 지켜야 할 불변식:
  1. generate_counterfactuals()는 GrammarEngine 내부 state를 mutate해서는 안 된다 (deep copy 사용)
  2. CounterfactualRecord는 hidden label (true_wrong_hypothesis 등)을 포함하지 않는다
  3. is_oracle_best는 최대 1개만 True (정확히 1개, counterfactuals 비어있으면 없음)
  4. top_k = min(top_k, len(non_selected_candidates))
  5. rng seeded → deterministic

GOAL: |
  1. src/frcgw/text_env/counterfactual_rollout.py 신규 생성
     - generate_counterfactuals() 함수 구현
     - GrammarEngine deep copy + apply() 호출
     - top_k 제한, rng determinism, is_oracle_best 계산 포함
  2. collector.py L391 1-line patch:
     counterfactuals=[] → counterfactuals=generate_counterfactuals(...)
  3. tests/test_step4_counterfactual_rollout.py (9개 테스트)
  4. tests/test_step4_counterfactual_no_leakage.py (4개 테스트)

FILES_ALLOWED: |
  src/frcgw/text_env/counterfactual_rollout.py
  src/frcgw/text_env/collector.py
  tests/test_step4_counterfactual_rollout.py
  tests/test_step4_counterfactual_no_leakage.py

FILES_FORBIDDEN: |
  src/frcgw/schemas/visibility.py
  src/frcgw/schemas/validation.py
  src/frcgw/schemas/step_schema.py
  paper_context_ref/
  data/
  src/frcgw/evaluation/frcg_agent.py
  scripts/10_run_lr_real_eval.py
  src/frcgw/evaluation/metrics.py
  .claude/settings.json
  scripts/run_codex_task.ps1
  configs/
  outputs/

REQUIRED_IMPLEMENTATION: |
  ### counterfactual_rollout.py (신규)

  ```python
  """frcgw.text_env.counterfactual_rollout — Counterfactual rollout generator.

  Source: paper_context_ref/06_DATA_SCHEMA_AND_LABELING.md §4 CounterfactualRecord
          paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md §8 ABL-008 rollout
  """
  from __future__ import annotations

  import copy
  import random

  from frcgw.schemas.step_schema import CandidateAction, CounterfactualRecord
  from frcgw.text_env.grammar import GrammarEngine
  from frcgw.text_env.state import TextState


  def generate_counterfactuals(
      pre_state: TextState,
      actual_action_id: str,
      candidates: list[CandidateAction],
      engine: GrammarEngine,
      top_k: int = 3,
      rng: random.Random | None = None,
  ) -> list[CounterfactualRecord]:
      """For each non-selected candidate (up to top_k), simulate effect under current grammar.

      Never mutates pre_state or engine state.
      CounterfactualRecord fields are all public-safe (no hidden labels).
      Source: paper_context_ref/06_DATA_SCHEMA_AND_LABELING.md §4
      """
      if rng is None:
          rng = random.Random(0)

      non_selected = [c for c in candidates if c.action_id != actual_action_id]
      if not non_selected:
          return []

      chosen = non_selected[:top_k]  # already ordered by candidate list

      records: list[CounterfactualRecord] = []
      best_delta = float("-inf")
      best_idx = -1

      source_step_id = getattr(pre_state, "step_id", str(pre_state.step_index))

      for i, candidate in enumerate(chosen):
          # Deep copy preconditions to avoid mutation of hidden state
          preconditions_copy = copy.deepcopy(pre_state._hidden_preconditions)
          effect_type, progress_delta = _simulate_action(
              preconditions_copy, candidate.action_id, engine
          )
          failure_risk = _estimate_failure_risk(
              preconditions_copy, candidate.action_id, engine, effect_type
          )
          if progress_delta > best_delta:
              best_delta = progress_delta
              best_idx = i
          records.append(
              CounterfactualRecord(
                  counterfactual_id=f"{source_step_id}_cf_{i}",
                  source_step_id=source_step_id,
                  candidate_action=candidate,
                  hypothesis_id="counterfactual_simulation",
                  counterfactual_effect_type=effect_type,
                  counterfactual_progress_delta=float(progress_delta),
                  counterfactual_failure_risk=float(failure_risk),
                  is_oracle_best=False,  # will be set below
              )
          )

      # Set exactly 1 is_oracle_best if non-empty
      if records and best_idx >= 0:
          records[best_idx] = CounterfactualRecord(
              counterfactual_id=records[best_idx].counterfactual_id,
              source_step_id=records[best_idx].source_step_id,
              candidate_action=records[best_idx].candidate_action,
              hypothesis_id=records[best_idx].hypothesis_id,
              counterfactual_effect_type=records[best_idx].counterfactual_effect_type,
              counterfactual_progress_delta=records[best_idx].counterfactual_progress_delta,
              counterfactual_failure_risk=records[best_idx].counterfactual_failure_risk,
              is_oracle_best=True,
          )
      return records


  def _simulate_action(
      preconditions: dict,
      action_id: str,
      engine: GrammarEngine,
  ) -> tuple[str, float]:
      """Apply action to (copied) preconditions; return (effect_type, progress_delta).

      Uses engine._rules for the current grammar only.
      """
      rules = engine._rules
      effect_map = rules.get("effect_map", {})
      action_type = action_id.split(":")[-1] if ":" in action_id else action_id
      if action_type in effect_map:
          prog_delta, eff_type, sets_key = effect_map[action_type]
          if sets_key:
              preconditions[sets_key] = True
          return eff_type, float(prog_delta)
      return "no_state_change", 0.0


  def _estimate_failure_risk(
      preconditions: dict,
      action_id: str,
      engine: GrammarEngine,
      effect_type: str,
  ) -> float:
      """Proxy failure risk: 1.0 if engine says wrong grammar failure, else 0.0."""
      action_type = action_id.split(":")[-1] if ":" in action_id else action_id
      try:
          is_wrong = engine.is_wrong_grammar_failure(preconditions, action_type, effect_type)
      except Exception:
          return 0.5
      return 1.0 if is_wrong else 0.0
  ```

  ### collector.py patch (L391 only)

  Change:
  ```python
  counterfactuals=[],
  ```
  To:
  ```python
  counterfactuals=_build_counterfactuals(pre_state, action_record.action_type, list(obs.candidate_actions_public), engine, rng),
  ```

  Add helper at module level (after imports, before collect_episode):
  ```python
  def _build_counterfactuals(
      pre_state: TextState,
      actual_action_type: str,
      candidates: list[CandidateAction],
      engine: GrammarEngine,
      rng: random.Random,
  ) -> list[CounterfactualRecord]:
      from frcgw.text_env.counterfactual_rollout import generate_counterfactuals
      # action_id in candidates matches action_type for text env
      actual_id = actual_action_type
      return generate_counterfactuals(
          pre_state=pre_state,
          actual_action_id=actual_id,
          candidates=candidates,
          engine=engine,
          top_k=3,
          rng=rng,
      )
  ```

  Import CounterfactualRecord is already in step_schema imports at top of collector.py.

REQUIRED_TESTS: |
  tests/test_step4_counterfactual_rollout.py — 9개:

  1. test_counterfactuals_non_empty_when_alt_candidates_exist
     - episode with 3 candidates; actual_action != all others → len(result) >= 1

  2. test_counterfactuals_empty_when_no_alternatives
     - single candidate == actual_action → result == []

  3. test_top_k_limit_respected
     - 5 candidates, top_k=2 → len(result) <= 2

  4. test_counterfactual_rollout_is_deterministic_for_seed
     - same rng seed → same records

  5. test_counterfactual_engine_state_unchanged_after_rollout
     - deep copy engine; call generate_counterfactuals; compare engine._rules before/after

  6. test_is_oracle_best_exactly_one_true_when_non_empty
     - len(records) > 0 → exactly 1 record with is_oracle_best=True

  7. test_counterfactual_effect_type_is_public_safe_enum
     - effect_type in {"state_change","no_state_change","blocker_removed","delayed_effect","task_complete"}

  8. test_counterfactual_failure_risk_in_unit_interval
     - 0.0 <= failure_risk <= 1.0 for all records

  9. test_v0_2_data_not_overwritten
     - check that data/frcgw_text/v0_2/ mtime is unchanged after running generator
     - (mock or use pathlib stat to confirm no writes to v0_2 path)

  tests/test_step4_counterfactual_no_leakage.py — 4개:

  1. test_counterfactual_does_not_appear_in_public_observation
     - CounterfactualRecord fields not present in PublicObservation asdict output

  2. test_counterfactual_does_not_appear_in_candidate_actions
     - CandidateAction does not include counterfactual fields

  3. test_counterfactual_does_not_appear_in_history_public
     - PublicHistoryItem does not include counterfactual fields

  4. test_validate_counterfactual_exclusion_still_passes_on_v0_3
     - validate_counterfactual_exclusion(step.public_observation) passes
     - (use a synthetic step with populated counterfactuals list)

ACCEPTANCE_CRITERIA: |
  - pytest tests/test_step4_counterfactual_rollout.py -q → 9/9 PASSED
  - pytest tests/test_step4_counterfactual_no_leakage.py -q → 4/4 PASSED
  - pytest tests/test_forbidden_field_mirror_sync.py -q → PASSED (회귀)
  - pytest tests/test_step3_no_label_leakage.py -q → PASSED (회귀)
  - data/frcgw_text/v0_1/ 및 data/frcgw_text/v0_2/ 파일 mtime 불변
  - visibility.py, validation.py, step_schema.py 미수정
  - collector.py 변경은 L391 1-line patch + _build_counterfactuals helper 추가만

COMMIT_MESSAGE: |
  feat(step4/task2): counterfactual rollout generator + collector patch

  B1 blocker: adds counterfactual_rollout.py with generate_counterfactuals()
  and patches collector.py L391 from counterfactuals=[] to actual rollout.
  Data-level unblock for C4 metric (metric function deferred to STEP 5).
  Public-safe: no hidden labels, engine state not mutated.

  13 new tests: 9 rollout + 4 leakage guards.

STOP_CONDITION: |
  13 tests green, FILES_FORBIDDEN 미수정, v0_1/v0_2 mtime 불변.
  visibility/leakage 회귀 FAIL 시 즉시 중단.
