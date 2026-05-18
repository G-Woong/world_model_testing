TASK_NAME: step7_c3_mapping_fix
SANDBOX_MODE: bypass
BACKGROUND: |
  FRCG-WM STEP 7. Branch: memory-redesign-2026-05-16 @ f488776.

  C3 falsification F1이 planner.py의 `_effect_type_id` mapping이 v0_3 데이터의 실제
  effect_type 문자열과 불일치하는 code bug로 인해 0.0이었다. 모든 v0_3 문자열
  ("no_state_change", "state_change", "blocker_removed", "delayed_effect", "task_complete")이
  mapping.get(key, 0) fallback으로 0이 되어 falsification.py:64의 short-circuit {0, 6}이
  항상 발동, F_t = 0.0.

  Phase C T1 audit 결과 (주요 포인트):
  - mathematical-validity-critic: losses.py EFFECT_TYPE_VOCAB도 원자적으로 함께 업데이트 필수
    (losses.py에 v0_3 키 없으면 vocab diverge; task_complete 슬롯이 어긋남)
  - n_effect_types=7 (model 출력 indices 0-6). task_complete=7은 index OOB → task_complete=5로 수정.
  - lr_scorer.py:106의 no_effect_flag에 "no_state_change" 누락 (systematic scoring bias)
  - frcgw-data-leakage-auditor: PASS — PublicEffect fields are public-safe
  - _accessed_hidden assert는 dead no-op, 보존은 하지만 의존하지 않음

  SSoT for public effect_type strings: src/frcgw/text_env/counterfactual_rollout.py:18-26
  (_PUBLIC_EFFECT_TYPES = {"state_change", "no_state_change", "blocker_removed",
                            "delayed_effect", "task_complete"})

  Model constraint: n_effect_types=7 in text_frcg_model.py:92 → effect head indices 0-6.
  task_complete MUST map to an index in {1,2,3,4,5} (not 0, not 6, not >= 7).

GOAL: |
  1. planner.py `_effect_type_id` mapping을 v0_3 effect_type 문자열로 확장
  2. losses.py EFFECT_TYPE_VOCAB를 planner mapping과 동일 ID로 원자적 업데이트
  3. lr_scorer.py `from_public_step`:
     a. no_effect_flag에 "no_state_change" 추가
     b. precondition_status를 effect_type으로 derive (public-safe)
     c. progress_delta를 text_diff_public + dom_diff_public으로 derive (public-safe)
  4. 3개 신규 테스트 작성

FILES_ALLOWED:
  - src/frcgw/planning/planner.py
  - src/frcgw/objectives/losses.py
  - src/frcgw/falsification/lr_scorer.py
  - tests/test_step7_effect_type_mapping_alignment.py
  - tests/test_step7_lr_scorer_public_proxy.py
  - tests/test_step7_falsification_nondegenerate.py

FILES_FORBIDDEN:
  - src/frcgw/schemas/visibility.py
  - src/frcgw/schemas/step_schema.py
  - src/frcgw/planning/falsification.py
  - src/frcgw/text_env/counterfactual_rollout.py
  - src/frcgw/models/text_frcg_model.py
  - src/frcgw/models/world_model_heads.py
  - src/frcgw/training/train_text.py
  - data/
  - outputs/
  - paper_context_ref/
  - .claude/
  - scripts/run_codex_task.ps1
  - configs/train_text*.yaml

REQUIRED_IMPLEMENTATION: |
  ## 1. planner.py `_effect_type_id` (lines ~55-67)

  현재:
  ```python
  def _effect_type_id(effect_summary: str | None) -> int:
      key = (effect_summary or "none").strip().lower()
      mapping = {
          "none": 0,
          "no_change": 0,
          "reveal": 1,
          "shift": 2,
          "failed": 3,
          "delayed": 4,
          "noisy": 5,
          "no_op_valid": 6,
      }
      return mapping.get(key, 0)
  ```

  업데이트 후:
  ```python
  def _effect_type_id(effect_summary: str | None) -> int:
      key = (effect_summary or "none").strip().lower()
      # Legacy keys preserved for backward compat with training-proxy ABL data.
      # v0_3 / _PUBLIC_EFFECT_TYPES keys added below.
      # SSoT for public strings: counterfactual_rollout.py::_PUBLIC_EFFECT_TYPES
      # n_effect_types=7 (indices 0-6); task_complete=5 avoids index OOB and {0,6} short-circuit.
      mapping = {
          "none": 0,
          "no_change": 0,
          "no_op_valid": 6,
          # v0_3 public effect_type strings
          "no_state_change": 0,
          "state_change": 1,
          "blocker_removed": 2,
          "delayed_effect": 4,
          "task_complete": 5,
      }
      return mapping.get(key, 0)
  ```

  중요: no_state_change=0은 short-circuit 대상(의도적). state_change=1/blocker_removed=2/delayed_effect=4/task_complete=5 모두 {0,6} 밖.

  ## 2. losses.py EFFECT_TYPE_VOCAB (lines ~44-53)

  현재:
  ```python
  EFFECT_TYPE_VOCAB: dict[str, int] = {
      "none": 0,
      "no_change": 0,
      "reveal": 1,
      "shift": 2,
      "failed": 3,
      "delayed": 4,
      "noisy": 5,
      "no_op_valid": 6,
  }
  ```

  업데이트 후:
  ```python
  # SSoT alignment: planner.py::_effect_type_id, _PUBLIC_EFFECT_TYPES in counterfactual_rollout.py.
  # n_effect_types=7 (indices 0-6). All v0_3 strings map within this range.
  EFFECT_TYPE_VOCAB: dict[str, int] = {
      # legacy (preserved for backward compat)
      "none": 0,
      "no_change": 0,
      "reveal": 1,
      "shift": 2,
      "failed": 3,
      "delayed": 4,
      "noisy": 5,
      "no_op_valid": 6,
      # v0_3 / _PUBLIC_EFFECT_TYPES strings (must match planner.py::_effect_type_id)
      "no_state_change": 0,
      "state_change": 1,
      "blocker_removed": 2,
      "delayed_effect": 4,
      "task_complete": 5,
  }
  ```

  ## 3. lr_scorer.py `from_public_step` (lines ~89-123)

  변경 사항:
  a) no_effect_flag: "no_state_change" 추가
  b) precondition_status: effect_type으로 derive
  c) progress_delta: len(text_diff_public) + len(dom_diff_public) normalize로 derive
  d) 기존 anti-leakage assert 보존
  e) training_labels / evaluation_labels / counterfactuals / audit_metadata 절대 접근 금지

  ```python
  @classmethod
  def from_public_step(cls, step: "StepRecord") -> "EvidenceFeatures":
      """Build EvidenceFeatures from public-only fields of a StepRecord.

      Allowed: step.public_observation, step.action, step.observed_effect_public.
      Forbidden: step.training_labels, step.evaluation_labels,
                 step.counterfactuals, step.audit_metadata — never accessed below.
      """
      _accessed_hidden = False
      assert not _accessed_hidden, "Hidden fields must not be accessed in from_public_step"

      eff = step.observed_effect_public
      effect_type: str = eff.effect_type

      dom_diff_summary: str = _summarize_dom_diff(eff.dom_diff_public)
      text_diff: str = eff.text_diff_public or ""

      # visual_diff_score: no visual field in current public schema
      visual_diff_score: float = 0.0

      # precondition_status: derive from public effect_type (shortcut_risk WARN, not BLOCK)
      if effect_type in ("blocker_removed", "task_complete"):
          precondition_status: str = "satisfied"
      elif effect_type == "no_state_change":
          precondition_status = "unmet"
      else:
          precondition_status = "unknown"

      # no_effect_flag: include v0_3 no-effect string
      no_effect_flag: bool = effect_type in (
          "no_effect", "no_change", "noop", "no_state_change"
      )
      delayed_effect_flag: bool = effect_type == "delayed_effect"
      noisy_observation_flag: bool = False  # no public noisy marker in schema

      # progress_delta: public-safe proxy from observable text/dom diff
      # training_labels.progress_delta is hidden — use heuristic proxy instead
      text_len = len(text_diff) if text_diff else 0
      dom_items = len(eff.dom_diff_public) if isinstance(eff.dom_diff_public, dict) else 0
      raw_proxy = float(text_len + dom_items)
      # Normalize: clamp to [0, 1] with soft cap at 100 chars/items total
      progress_delta: float = min(1.0, raw_proxy / 100.0)

      failure_reason: str | None = None  # training_labels.failure_reason is hidden

      return cls(
          effect_type=effect_type,
          dom_diff_summary=dom_diff_summary,
          accessibility_diff_summary=text_diff,
          visual_diff_score=visual_diff_score,
          precondition_status=precondition_status,
          no_effect_flag=no_effect_flag,
          delayed_effect_flag=delayed_effect_flag,
          noisy_observation_flag=noisy_observation_flag,
          progress_delta=progress_delta,
          failure_reason=failure_reason,
      )
  ```

REQUIRED_TESTS: |
  ## tests/test_step7_effect_type_mapping_alignment.py

  ```python
  """Tests that planner._effect_type_id and losses.EFFECT_TYPE_VOCAB
  are aligned and all _PUBLIC_EFFECT_TYPES strings are covered.
  """
  import pytest
  from frcgw.planning.planner import _effect_type_id
  from frcgw.objectives.losses import EFFECT_TYPE_VOCAB
  from frcgw.text_env.counterfactual_rollout import _PUBLIC_EFFECT_TYPES

  _PUBLIC_LIST = list(_PUBLIC_EFFECT_TYPES)

  @pytest.mark.parametrize("effect_str", _PUBLIC_LIST)
  def test_planner_mapping_covers_public_effect_types(effect_str):
      """Every _PUBLIC_EFFECT_TYPES string must map to a defined (non-fallback) ID."""
      # The mapping must explicitly cover the string (not just fallback to 0)
      # We verify by checking the result is deterministic and within [0, 6]
      result = _effect_type_id(effect_str)
      assert 0 <= result <= 6, f"{effect_str} -> {result} out of model range [0,6]"

  @pytest.mark.parametrize("effect_str", [
      "state_change", "blocker_removed", "delayed_effect", "task_complete"
  ])
  def test_planner_mapping_not_in_short_circuit(effect_str):
      """Non-trivial v0_3 effect types must NOT map to short-circuit set {0, 6}."""
      result = _effect_type_id(effect_str)
      assert result not in {0, 6}, (
          f"{effect_str} maps to {result} which is in short-circuit set {{0, 6}}"
      )

  def test_no_state_change_maps_to_zero():
      """no_state_change correctly maps to 0 (short-circuit is intentional)."""
      assert _effect_type_id("no_state_change") == 0

  @pytest.mark.parametrize("effect_str", _PUBLIC_LIST)
  def test_vocab_and_planner_agree(effect_str):
      """EFFECT_TYPE_VOCAB and _effect_type_id must agree on all public strings."""
      planner_id = _effect_type_id(effect_str)
      vocab_id = EFFECT_TYPE_VOCAB.get(effect_str, None)
      assert vocab_id is not None, f"{effect_str} missing from EFFECT_TYPE_VOCAB"
      assert planner_id == vocab_id, (
          f"Mismatch: planner={planner_id}, vocab={vocab_id} for '{effect_str}'"
      )

  def test_max_vocab_id_within_model_range():
      """Max EFFECT_TYPE_VOCAB value must be <= 6 (n_effect_types=7, indices 0-6)."""
      max_id = max(EFFECT_TYPE_VOCAB.values())
      assert max_id <= 6, f"Max vocab ID {max_id} exceeds model n_effect_types-1=6"
  ```

  ## tests/test_step7_lr_scorer_public_proxy.py

  ```python
  """Tests that from_public_step derives non-trivial values without hidden field access."""
  import pytest
  from unittest.mock import MagicMock
  from frcgw.falsification.lr_scorer import EvidenceFeatures


  def _make_public_effect(effect_type, text_diff=None, dom_diff=None):
      eff = MagicMock()
      eff.effect_type = effect_type
      eff.text_diff_public = text_diff
      eff.dom_diff_public = dom_diff
      return eff


  def _make_step(effect_type, text_diff=None, dom_diff=None):
      step = MagicMock()
      step.observed_effect_public = _make_public_effect(effect_type, text_diff, dom_diff)
      # Accessing training_labels/evaluation_labels/counterfactuals raises AttributeError
      # to simulate forbidden access — MagicMock returns new MagicMock by default,
      # so we don't need to set that up explicitly; the test verifies no leakage structurally.
      return step


  def test_progress_delta_nonzero_when_text_diff_present():
      """progress_delta must be > 0 when text_diff_public is non-empty."""
      step = _make_step("state_change", text_diff="some change occurred", dom_diff=None)
      features = EvidenceFeatures.from_public_step(step)
      assert features.progress_delta > 0.0, "Expected non-zero progress_delta with text_diff"


  def test_progress_delta_nonzero_when_dom_diff_present():
      """progress_delta must be > 0 when dom_diff_public has items."""
      step = _make_step("state_change", text_diff=None, dom_diff={"added": ["div#1"]})
      features = EvidenceFeatures.from_public_step(step)
      assert features.progress_delta > 0.0, "Expected non-zero progress_delta with dom_diff"


  def test_precondition_satisfied_for_blocker_removed():
      step = _make_step("blocker_removed", text_diff="Modal closed", dom_diff=None)
      features = EvidenceFeatures.from_public_step(step)
      assert features.precondition_status == "satisfied"


  def test_precondition_satisfied_for_task_complete():
      step = _make_step("task_complete", text_diff="Task done", dom_diff=None)
      features = EvidenceFeatures.from_public_step(step)
      assert features.precondition_status == "satisfied"


  def test_precondition_unmet_for_no_state_change():
      step = _make_step("no_state_change", text_diff=None, dom_diff=None)
      features = EvidenceFeatures.from_public_step(step)
      assert features.precondition_status == "unmet"


  def test_no_effect_flag_for_no_state_change():
      """no_state_change must be recognized as a no-effect event."""
      step = _make_step("no_state_change", text_diff=None, dom_diff=None)
      features = EvidenceFeatures.from_public_step(step)
      assert features.no_effect_flag is True


  def test_no_effect_flag_false_for_state_change():
      step = _make_step("state_change", text_diff="changed", dom_diff=None)
      features = EvidenceFeatures.from_public_step(step)
      assert features.no_effect_flag is False


  def test_no_training_labels_accessed():
      """Verify effect_type is taken from public field, not training_labels."""
      step = _make_step("state_change", text_diff="delta", dom_diff=None)
      # If from_public_step accessed step.training_labels, it would return a MagicMock,
      # but not raise — however we verify no forbidden key appears in output fields.
      features = EvidenceFeatures.from_public_step(step)
      # effect_type must come from observed_effect_public, not training_labels
      assert features.effect_type == "state_change"
      assert isinstance(features.progress_delta, float)
      assert isinstance(features.precondition_status, str)
  ```

  ## tests/test_step7_falsification_nondegenerate.py

  ```python
  """Tests that falsification_score returns non-zero values for non-trivial effect types.

  Uses an untrained model head fixture. The test only verifies that the short-circuit
  does NOT fire for v0_3 non-trivial effect types (i.e., output is not guaranteed-zero
  by code path alone).
  """
  import pytest
  import torch
  from unittest.mock import MagicMock
  from frcgw.planning.falsification import FalsificationEvidence, falsification_score


  def _make_rollout(n_effect_types=7):
      """Create a mock RolloutResult with random logits."""
      rollout = MagicMock()
      rollout.effect_logits = torch.randn(1, n_effect_types)
      rollout.progress_pred = torch.tensor([0.5])
      rollout.failed_score = torch.tensor([0.1])
      return rollout


  def _make_model(n_effect_types=7):
      model = MagicMock()
      model.world_model_heads.forward_given_action.side_effect = (
          lambda sh, zs, action, hid: _make_rollout(n_effect_types)
      )
      return model


  @pytest.mark.parametrize("effect_str,effect_id", [
      ("state_change", 1),
      ("blocker_removed", 2),
      ("delayed_effect", 4),
      ("task_complete", 5),
  ])
  def test_falsification_not_short_circuited_for_nontrivial_effects(effect_str, effect_id):
      """For non-trivial v0_3 effect types, falsification_score must not return zero
      due to short-circuit alone (result depends on model, not code path blocking)."""
      model = _make_model()
      shared_h = torch.zeros(1, 32)
      z_state = torch.zeros(1, 32)
      evidence = FalsificationEvidence(
          observed_effect_type=effect_id,
          observed_progress_delta=0.3,
          observed_failed_action=False,
      )
      result = falsification_score(
          model, shared_h, z_state, "click", h_exec_id=0,
          alt_hypothesis_ids=[1, 2], evidence=evidence
      )
      # The result should be a tensor (not zeros from short-circuit)
      # We can't assert non-zero because an untrained model might return zero by chance,
      # but we CAN assert the code path is not the short-circuit path.
      # Verification: model.world_model_heads.forward_given_action was called (not bypassed).
      assert model.world_model_heads.forward_given_action.called, (
          f"Short-circuit fired for {effect_str} (id={effect_id}): model was not called"
      )


  def test_falsification_short_circuits_for_no_state_change():
      """no_state_change (id=0) must trigger short-circuit → zero output, no model call."""
      model = _make_model()
      shared_h = torch.zeros(1, 32)
      z_state = torch.zeros(1, 32)
      evidence = FalsificationEvidence(
          observed_effect_type=0,
          observed_progress_delta=0.0,
          observed_failed_action=False,
      )
      result = falsification_score(
          model, shared_h, z_state, "click", h_exec_id=0,
          alt_hypothesis_ids=[1, 2], evidence=evidence
      )
      assert not model.world_model_heads.forward_given_action.called, (
          "Short-circuit should have prevented model call for no_state_change (id=0)"
      )
      assert result.item() == 0.0
  ```

ACCEPTANCE_CRITERIA: |
  1. pytest tests/test_step7_effect_type_mapping_alignment.py -q → ALL GREEN
  2. pytest tests/test_step7_lr_scorer_public_proxy.py -q → ALL GREEN
  3. pytest tests/test_step7_falsification_nondegenerate.py -q → ALL GREEN
  4. git diff src/frcgw/schemas/ → empty (no schema file touched)
  5. git diff scripts/run_codex_task.ps1 → empty
  6. git diff src/frcgw/planning/falsification.py → empty (no short-circuit change in Task 1)
  7. git diff src/frcgw/text_env/counterfactual_rollout.py → empty
  8. max(EFFECT_TYPE_VOCAB.values()) <= 6 (verified by test_max_vocab_id_within_model_range)
  9. All v0_3 non-trivial effect types map outside {0, 6} in planner mapping
  10. lr_scorer.py training_labels / evaluation_labels / counterfactuals / audit_metadata 미접근

COMMIT_MESSAGE: "fix(step7/task1): align effect_type mapping with v0_3 _PUBLIC_EFFECT_TYPES + update EFFECT_TYPE_VOCAB + lr_scorer public proxy"

STOP_CONDITION: |
  STOP if:
  - Any test in tests/test_forbidden_field_mirror_sync.py fails
  - Any test in tests/test_visibility_contract.py fails
  - src/frcgw/schemas/visibility.py was modified
  - max(EFFECT_TYPE_VOCAB.values()) > 6
  - Any v0_3 non-trivial effect type (state_change, blocker_removed, delayed_effect, task_complete) maps to {0, 6}
  - Any training_labels / evaluation_labels field is accessed in from_public_step
