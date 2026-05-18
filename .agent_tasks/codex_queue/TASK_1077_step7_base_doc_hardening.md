TASK_NAME: step7_base_doc_hardening
SANDBOX_MODE: bypass
BACKGROUND: |
  FRCG-WM STEP 7. Branch: memory-redesign-2026-05-16.

  BASE-026 (WAC-style), BASE-027 (CUWM-style), BASE-028 (WebWorld-style)은
  현재 heuristic proxy로 구현됐다. 논문에서 이를 "faithful WAC/CUWM/WebWorld"로
  오인하거나 reviewer가 공격할 수 있다.

  현재 상태:
  - BASE-028: approximation_level = "heuristic next-state proxy; full WebWorld reconstruction infeasible" (이미 존재)
  - BASE-026: approximation_level 없음 (추가 필요)
  - BASE-027: approximation_level 없음 (추가 필요)

  STEP 7 목표: BASE-026/027에 approximation_level class attr 추가로 3개 통일.
  Faithful upgrade는 STEP 8.

GOAL: |
  1. baselines.py BASE-026/027에 approximation_level 클래스 attr 추가
  2. tests/test_step7_direct_threat_approximation_declared.py 신규 작성
  3. docs/orchestration/lr_alignment/34_step7_direct_threat_baseline_status.md 신규 작성

FILES_ALLOWED:
  - src/frcgw/evaluation/baselines.py
  - tests/test_step7_direct_threat_approximation_declared.py
  - docs/orchestration/lr_alignment/34_step7_direct_threat_baseline_status.md

FILES_FORBIDDEN:
  - src/frcgw/schemas/visibility.py
  - src/frcgw/schemas/step_schema.py
  - data/
  - outputs/
  - paper_context_ref/
  - .claude/
  - scripts/run_codex_task.ps1
  - configs/train_text*.yaml

REQUIRED_IMPLEMENTATION: |
  ## 1. src/frcgw/evaluation/baselines.py

  WACStyleConsequenceCorrectionAgent 클래스에 approximation_level 추가:

  ```python
  class WACStyleConsequenceCorrectionAgent(BaselineAgent):
      """BASE-026: WAC-style consequence correction (WAC direct-threat defense).

      Public consequence heuristic-based correction. No grammar posterior.
      """
      baseline_id = "BASE-026"
      paper_ssot_id = "BASE-026 (WAC-style consequence correction)"
      approximation_level = (
          "heuristic last-effect-fail proxy; "
          "full WAC consequence-correction model (grammar posterior + consequence prediction) "
          "deferred to STEP 8"
      )
      # ... rest of class unchanged ...
  ```

  CUWMStyleCandidateSimulationAgent 클래스에 approximation_level 추가:

  ```python
  class CUWMStyleCandidateSimulationAgent(BaselineAgent):
      """BASE-027: CUWM-style candidate simulation (CUWM direct-threat defense).

      Compares frozen-base candidates via public heuristic. No grammar posterior.
      """
      baseline_id = "BASE-027"
      paper_ssot_id = "BASE-027 (CUWM-style candidate simulation)"
      approximation_level = (
          "heuristic longest-action-id proxy; "
          "full CUWM candidate-simulation (world model rollout per candidate) "
          "deferred to STEP 8"
      )
      # ... rest of class unchanged ...
  ```

  BASE-028의 기존 approximation_level은 변경하지 않는다.
  기존 act() 메서드들도 변경하지 않는다.

  ## 2. docs/orchestration/lr_alignment/34_step7_direct_threat_baseline_status.md

  ```markdown
  # STEP 7 — Direct-Threat Baseline Status

  date: 2026-05-18
  status: DOCUMENTATION_HARDENING_ONLY

  ## Summary

  BASE-026 (WAC), BASE-027 (CUWM), BASE-028 (WebWorld)은 STEP 7에서
  heuristic proxy로 구현되어 있다. STEP 7에서는 approximation_level 선언을
  통일하고, paper wording forbidden list를 강화한다.

  ## Approximation Level Declarations

  | Baseline | approximation_level | Faithful upgrade |
  |---|---|---|
  | BASE-026 (WAC) | heuristic last-effect-fail proxy; full WAC deferred | STEP 8 |
  | BASE-027 (CUWM) | heuristic longest-action-id proxy; full CUWM deferred | STEP 8 |
  | BASE-028 (WebWorld) | heuristic next-state proxy; full WebWorld infeasible | STEP 8/9 |

  ## Paper Wording — FORBIDDEN (reviewer attack vectors)

  ❌ "defeats WAC"
  ❌ "outperforms CUWM"
  ❌ "superior to WebWorld"
  ❌ "compared to WAC baseline" (without approximation_level qualifier)
  ❌ "our method vs WAC" (implies faithful WAC comparison)

  ## Paper Wording — ALLOWED

  ✅ "compared against heuristic proxy baselines (approximation_level=heuristic)"
  ✅ "BASE-026: WAC-style heuristic proxy (faithful WAC deferred to STEP 8)"
  ✅ "BASE-027: CUWM-style heuristic proxy (faithful CUWM deferred to STEP 8)"
  ✅ "direct-threat baselines: heuristic approximations only; faithful implementations in STEP 8"

  ## STEP 8 Roadmap

  - BASE-026 faithful: grammar posterior + consequence model (WAC §3.2)
  - BASE-027 faithful: candidate simulation with world model rollout (CUWM §4)
  - BASE-028 faithful: full simulator search (most complex, may require STEP 9)
  ```

REQUIRED_TESTS: |
  ## tests/test_step7_direct_threat_approximation_declared.py

  ```python
  """Tests that BASE-026, BASE-027, BASE-028 all declare approximation_level."""
  import pytest
  from frcgw.evaluation.baselines import (
      WACStyleConsequenceCorrectionAgent,
      CUWMStyleCandidateSimulationAgent,
      WebWorldStyleSearchAgent,
  )


  @pytest.mark.parametrize("cls,expected_id", [
      (WACStyleConsequenceCorrectionAgent, "BASE-026"),
      (CUWMStyleCandidateSimulationAgent, "BASE-027"),
      (WebWorldStyleSearchAgent, "BASE-028"),
  ])
  def test_approximation_level_declared(cls, expected_id):
      """All three direct-threat baselines must declare approximation_level."""
      assert hasattr(cls, "approximation_level"), (
          f"{expected_id} ({cls.__name__}) missing 'approximation_level' class attr"
      )
      level = cls.approximation_level
      assert isinstance(level, str) and len(level) > 0, (
          f"{expected_id} approximation_level must be a non-empty string"
      )
      assert "heuristic" in level.lower() or "proxy" in level.lower() or "infeasible" in level.lower(), (
          f"{expected_id} approximation_level must mention 'heuristic', 'proxy', or 'infeasible': {level}"
      )


  def test_base026_approximation_level_mentions_wac():
      level = WACStyleConsequenceCorrectionAgent.approximation_level
      assert "WAC" in level or "consequence" in level.lower()


  def test_base027_approximation_level_mentions_cuwm():
      level = CUWMStyleCandidateSimulationAgent.approximation_level
      assert "CUWM" in level or "candidate" in level.lower()


  def test_base028_approximation_level_exists_unchanged():
      """BASE-028 approximation_level must still exist (was already there)."""
      assert hasattr(WebWorldStyleSearchAgent, "approximation_level")
      level = WebWorldStyleSearchAgent.approximation_level
      assert "heuristic" in level.lower() or "proxy" in level.lower()


  def test_paper_ssot_ids_present():
      """All three must have paper_ssot_id for registry tracking."""
      for cls in [WACStyleConsequenceCorrectionAgent, CUWMStyleCandidateSimulationAgent, WebWorldStyleSearchAgent]:
          assert hasattr(cls, "paper_ssot_id"), f"{cls.__name__} missing paper_ssot_id"
  ```

ACCEPTANCE_CRITERIA: |
  1. pytest tests/test_step7_direct_threat_approximation_declared.py -q → ALL GREEN
  2. WACStyleConsequenceCorrectionAgent.approximation_level 존재 및 "WAC" 언급
  3. CUWMStyleCandidateSimulationAgent.approximation_level 존재 및 "CUWM" 언급
  4. WebWorldStyleSearchAgent.approximation_level 불변 (기존 string 유지)
  5. 3개 baseline의 act() 메서드 미수정
  6. docs/orchestration/lr_alignment/34_step7_direct_threat_baseline_status.md 존재
  7. git diff src/frcgw/schemas/ → empty
  8. "defeats WAC" / "outperforms CUWM" / "superior to WebWorld" 문자열이 코드에 없음

COMMIT_MESSAGE: "feat(step7/task6): add approximation_level to BASE-026/027 + forbidden wording doc"

STOP_CONDITION: |
  STOP if:
  - BaselineAgent act() methods were modified (only approximation_level attr needed)
  - BASE-028 approximation_level was changed from its existing value
  - src/frcgw/schemas/visibility.py was modified
  - Any "faithful" WAC/CUWM implementation was attempted (scope violation)
  - Paper claim wording of the form "defeats WAC" was added to any source file
