TASK_NAME: step7_c2_c5_metrics
SANDBOX_MODE: bypass
BACKGROUND: |
  FRCG-WM STEP 7. Branch: memory-redesign-2026-05-16.

  C2 claim (regime_shift_f1)은 true_regime을 EvaluationLabels로 surface해야 측정 가능하지만
  visibility contract change가 필요해 STEP 8 이관. STEP 7에서는 OOD shift proxy로
  ood_shift_f1을 도입한다.

  Phase C T1 claim-metric-alignment-auditor 결과:
  - C2는 MET-OOD-003에 대응. ood_shift_f1은 "MET-OOD-003 STEP 7 proxy"로 등록.
  - ood_type은 FORBIDDEN_AGENT_FIELDS에 포함 → eval 단계에서 split label로만 사용.
  - regime_shift_f1 이름을 metrics.py에 도입하면 안 됨 (paper claim 보호).
  - MET-LATENT-001은 STEP 7 내 구현 불가 — STEP 8 이관 문서화 필요.

  C5: falsification_calibration (ECE)은 이미 metrics.py:151에 구현. STEP 7에서는
  C3 fix 후 wrong_prob unique_count > 2일 때만 ECE 계산. 구현 자체보다 calibration
  retest 판단 문서 작성이 목적.

GOAL: |
  1. metrics.py에 ood_shift_f1 함수 추가 (NOT regime_shift_f1)
  2. eval_runner.py METRIC_FUNCTIONS에 ood_shift_f1 dispatch 추가 (1줄)
  3. C2/C5 결정 문서 작성
  4. 테스트 2개 작성

FILES_ALLOWED:
  - src/frcgw/evaluation/metrics.py
  - src/frcgw/evaluation/eval_runner.py
  - tests/test_step7_ood_shift_f1.py
  - tests/test_step7_c5_calibration_stub.py
  - docs/orchestration/lr_alignment/31_step7_c2_metric_decision.md

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
  ## 1. src/frcgw/evaluation/metrics.py — ood_shift_f1 함수 추가

  기존 FORBIDDEN_AGENT_KEYS set 아래에 다음 함수를 추가한다.
  절대로 "regime_shift_f1" 이름을 사용하지 않는다.

  ```python
  def ood_shift_f1(episodes: list[dict]) -> dict[str, float]:
      """OOD shift detection F1 — MET-OOD-003 STEP 7 proxy.

      Uses EvaluationLabels.ood_type as split-time label (NOT inference input).
      Agent prediction: predicted_wrong or selected_hypothesis_id change as shift signal.

      NOTE: This is NOT regime_shift_f1. True regime_shift_f1 requires true_regime
      in EvaluationLabels (visibility contract change deferred to STEP 8).
      Paper claim wording must use "OOD shift detection F1 (proxy)" not "regime_shift_f1".
      """
      true_positives = 0
      false_positives = 0
      false_negatives = 0
      true_negatives = 0

      for episode in episodes:
          labels = _field(episode, "eval_labels")
          ood_type = _field(labels, "ood_type")
          if ood_type is None:
              continue
          # Binary: ID = no shift expected, OOD_* = shift expected
          is_ood_shift = str(ood_type).startswith("OOD")

          # Agent shift signal: predicted_wrong flag or hypothesis switch event
          # Use any step in episode where predicted_wrong is True as "shift detected"
          shift_detected = False
          for step in _field(episode, "steps", []) or []:
              if bool(_field(step, "predicted_wrong", False)):
                  shift_detected = True
                  break

          if shift_detected and is_ood_shift:
              true_positives += 1
          elif shift_detected and not is_ood_shift:
              false_positives += 1
          elif not shift_detected and is_ood_shift:
              false_negatives += 1
          else:
              true_negatives += 1

      precision_denom = true_positives + false_positives
      recall_denom = true_positives + false_negatives
      precision = true_positives / precision_denom if precision_denom else 0.0
      recall = true_positives / recall_denom if recall_denom else 0.0
      f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
      return {
          "precision": precision,
          "recall": recall,
          "f1": f1,
          "true_positives": true_positives,
          "false_positives": false_positives,
          "false_negatives": false_negatives,
          "true_negatives": true_negatives,
      }
  ```

  ## 2. src/frcgw/evaluation/eval_runner.py — METRIC_FUNCTIONS dispatch

  import 블록에 ood_shift_f1 추가:
  ```python
  from frcgw.evaluation.metrics import (
      ...existing imports...,
      ood_shift_f1,
  )
  ```

  METRIC_FUNCTIONS dict에 1줄 추가:
  ```python
  "ood_shift_f1": ood_shift_f1,
  ```

  기존 METRIC_FUNCTIONS 항목은 절대 변경하지 않는다.

  ## 3. docs/orchestration/lr_alignment/31_step7_c2_metric_decision.md

  ```markdown
  # STEP 7 — C2 Metric Decision: ood_shift_f1 vs regime_shift_f1

  date: 2026-05-18
  status: DOCUMENTED

  ## Decision

  C2 claim (regime/control grammar 분리가 OOD generalization에 기여)의 정식 metric은
  MET-OOD-003 (OOD control grammar shift performance)이다.

  정식 regime_shift_f1 계산을 위해서는 true_regime이 EvaluationLabels에
  노출되어야 하나, 현재 true_regime은 FORBIDDEN_AGENT_FIELDS에 포함되어
  visibility contract change 없이는 eval label로 surface 불가.
  이 변경은 STEP 8으로 이관한다.

  STEP 7에서는 ood_shift_f1 (MET-OOD-003 proxy)를 도입한다:
  - ood_type (EvaluationLabels, eval-time split label)을 binary shift/no-shift로 변환
  - agent predicted_wrong flag를 shift detection signal로 사용
  - 이는 PROXY이며 진짜 regime shift detection이 아님

  ## Paper Wording Rules

  FORBIDDEN:
  - "regime_shift_f1" (STEP 7 metric 이름으로 사용 금지)
  - "C2 resolved" / "C2 proven" (STEP 8 전 사용 금지)
  - "defeats regime shift problem" (empirical evidence 없이 사용 금지)

  ALLOWED:
  - "OOD shift detection F1 (proxy, STEP 7)"
  - "C2 preliminary proxy: ood_shift_f1"
  - "regime_shift_f1 deferred to STEP 8 (visibility contract change required)"

  ## C5 Calibration Retest Policy

  falsification_calibration (ECE)은 metrics.py:151에 구현 완료.
  STEP 7 trained eval 후 wrong_prob unique_count > 2일 때만 ECE 계산.
  unique_count <= 2이면 BLOCKED_DEGENERATE_PREDICTOR 상태 유지.

  ## MET-LATENT-001 Status

  MET-LATENT-001 (latent factorization quality metric)은 STEP 7에서 구현 불가.
  → STEP 8 이관. C2 ablation (ABL-001/002/003)도 STEP 8 faithful retrain queue.
  ```

REQUIRED_TESTS: |
  ## tests/test_step7_ood_shift_f1.py

  ```python
  """Tests for ood_shift_f1 metric — MET-OOD-003 STEP 7 proxy."""
  import pytest
  from frcgw.evaluation.metrics import ood_shift_f1


  def _episode(ood_type, predicted_wrongs):
      """Helper: create episode dict with given ood_type and step predictions."""
      steps = [{"predicted_wrong": pw, "eval_labels": None} for pw in predicted_wrongs]
      return {
          "eval_labels": {"ood_type": ood_type},
          "steps": steps,
          "success": False,
      }


  def test_ood_shift_f1_perfect_detection():
      """Perfect detector: shift detected for all OOD, not for ID."""
      episodes = [
          _episode("OOD_grammar", [True]),   # shift detected, OOD → TP
          _episode("OOD_grammar", [True]),   # shift detected, OOD → TP
          _episode("ID", [False, False]),     # no shift, ID → TN
          _episode("ID", [False]),            # no shift, ID → TN
      ]
      result = ood_shift_f1(episodes)
      assert result["f1"] == 1.0
      assert result["true_positives"] == 2
      assert result["true_negatives"] == 2
      assert result["false_positives"] == 0
      assert result["false_negatives"] == 0


  def test_ood_shift_f1_no_detection():
      """No detection: shift never detected → recall=0 → f1=0."""
      episodes = [
          _episode("OOD_grammar", [False]),  # no shift, OOD → FN
          _episode("OOD_grammar", [False]),  # no shift, OOD → FN
      ]
      result = ood_shift_f1(episodes)
      assert result["f1"] == 0.0
      assert result["false_negatives"] == 2


  def test_ood_shift_f1_all_false_positives():
      """Shift detected for all ID episodes → precision=0 → f1=0."""
      episodes = [
          _episode("ID", [True]),            # shift detected, ID → FP
          _episode("ID", [True]),            # shift detected, ID → FP
      ]
      result = ood_shift_f1(episodes)
      assert result["f1"] == 0.0
      assert result["false_positives"] == 2


  def test_ood_shift_f1_no_ood_type():
      """Episodes without eval_labels.ood_type are skipped."""
      episodes = [{"eval_labels": None, "steps": [{"predicted_wrong": True}]}]
      result = ood_shift_f1(episodes)
      assert result["f1"] == 0.0
      assert result["true_positives"] == 0


  def test_ood_shift_f1_name_not_regime_shift():
      """Verify that regime_shift_f1 is NOT in METRIC_FUNCTIONS."""
      from frcgw.evaluation.eval_runner import METRIC_FUNCTIONS
      assert "regime_shift_f1" not in METRIC_FUNCTIONS, (
          "regime_shift_f1 must NOT appear in METRIC_FUNCTIONS — use ood_shift_f1 only"
      )
      assert "ood_shift_f1" in METRIC_FUNCTIONS


  def test_ood_shift_f1_dispatched_in_runner():
      """ood_shift_f1 must be registered in METRIC_FUNCTIONS."""
      from frcgw.evaluation.eval_runner import METRIC_FUNCTIONS
      assert "ood_shift_f1" in METRIC_FUNCTIONS
  ```

  ## tests/test_step7_c5_calibration_stub.py

  ```python
  """Verify that falsification_calibration is registered and degenerate check is available."""
  from frcgw.evaluation.eval_runner import METRIC_FUNCTIONS
  from frcgw.evaluation.metrics import falsification_calibration


  def test_c5_falsification_calibration_registered():
      """C5 ECE must be registered in METRIC_FUNCTIONS."""
      assert "falsification_calibration" in METRIC_FUNCTIONS


  def test_c5_calibration_degenerate_returns_zero_for_empty():
      """Empty episodes → 0.0 ECE (not an error)."""
      result = falsification_calibration([])
      assert result == 0.0


  def test_c5_calibration_degenerate_constant_predictor():
      """Constant predictor (all same wrong_prob) → calibration is well-defined."""
      episodes = [
          {"steps": [
              {"eval_labels": {"true_wrong_hypothesis": True}, "predicted_wrong": True, "wrong_prob": 0.9},
              {"eval_labels": {"true_wrong_hypothesis": False}, "predicted_wrong": False, "wrong_prob": 0.9},
          ]}
      ]
      # Should not raise; result may be non-zero
      result = falsification_calibration(episodes)
      assert isinstance(result, float)
  ```

ACCEPTANCE_CRITERIA: |
  1. pytest tests/test_step7_ood_shift_f1.py -q → ALL GREEN
  2. pytest tests/test_step7_c5_calibration_stub.py -q → ALL GREEN
  3. "regime_shift_f1" が metrics.py に存在しない
  4. "ood_shift_f1" が METRIC_FUNCTIONS に登録されている
  5. docs/orchestration/lr_alignment/31_step7_c2_metric_decision.md 存在
  6. git diff src/frcgw/schemas/ → empty

COMMIT_MESSAGE: "feat(step7/task3): add ood_shift_f1 proxy metric (MET-OOD-003 STEP 7) + C2/C5 decision doc"

STOP_CONDITION: |
  STOP if:
  - "regime_shift_f1" function is added to metrics.py (paper claim protection)
  - ood_type is accessed as an inference input (must be eval-only label)
  - src/frcgw/schemas/visibility.py is modified
  - src/frcgw/schemas/step_schema.py is modified
  - Any test_forbidden_field_mirror_sync.py fails
