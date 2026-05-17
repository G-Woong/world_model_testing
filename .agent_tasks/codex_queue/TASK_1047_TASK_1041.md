TASK_NAME: TASK_1041_step4_disclosure_trace_ece
SANDBOX_MODE: bypass

BACKGROUND: |
  FRCG-WM STEP 4 — B3 + B4 + B5 blockers.

  **B3 valid_trained_eval disclosure** (scripts/10_run_lr_real_eval.py L518-544):
  - 현재: manifest에 valid_trained_eval field 없음
  - 현재: `random_init_ok = ckpt_paths_all_provided` (naming 반대)
  - 수정: `valid_trained_eval = ckpt_paths_all_provided` 추가 (disclosure only)
  - 정의: valid_trained_eval=True iff all TextFRCGModelAgent specs have ckpt_path
  - Disclosure rule: valid_trained_eval=False → metric 인용 불가, smoke-only

  **B4 per_step trace writer fix** (scripts/10_run_lr_real_eval.py):
  - 현재: _TracingAgent.act()가 selected_hypothesis_id/confidence를 trace에 포함하지 않음
  - 현재: _write_per_step_jsonl이 selected_hypothesis_id=None, confidence=None 하드코딩
  - 수정:
    1. frcg_agent.py의 TextFRCGModelAgent.act()에 _last_selected_hypothesis_id,
       _last_selected_hypothesis_confidence 추가 (model argmax grammar)
    2. _TracingAgent.act()가 이를 getattr으로 읽어 trace dict에 포함
    3. _attach_trace_records/_write_per_step_jsonl이 이를 per_step row에 emit

  TextFRCGModelAgent에서 _last_selected_hypothesis_id를 derivate:
    model forward → z_grammar_logits → softmax → argmax → f"grammar_{idx}"
    confidence = float(grammar_probs.max())

  **B5 ECE degeneracy flag** (scripts/10_run_lr_real_eval.py):
  - 현재: ECE=0.025가 degenerate predictor (F_t=0.0 constant) artifact임
  - 수정: metrics dict에 C5_calibration_status field 추가
    - "DEGENERATE_PREDICTOR" if variance(wrong_prob) < 1e-6 AND unique_wrong_prob < 2 AND mean(F_t) == 0.0
    - "OK" otherwise
  - 추가: metrics.json에도 C5_calibration_status 포함 (manifest에만 두지 않음)
  - audit JSON: outputs/audits/step4_ece_degenerate_predictor_audit.json

  T2 claim-metric alignment auditor 지시사항 (2026-05-17):
  - valid_trained_eval 정의식: valid_trained_eval = ckpt_paths_all_provided (Boolean)
  - hard_checks_all_pass 조건 변경 없음 (기존 logic 유지)
  - C5_calibration_status는 metrics.json AND manifest에 포함

GOAL: |
  1. src/frcgw/evaluation/frcg_agent.py 수정:
     - act() 내부에 _last_selected_hypothesis_id, _last_selected_hypothesis_confidence 추가
     - reset() 에도 초기화

  2. scripts/10_run_lr_real_eval.py 수정:
     B3: _write_manifest()에 valid_trained_eval field 추가
     B4: _TracingAgent.act()에서 selected_hypothesis_id/confidence 읽어 trace dict 포함
         _attach_trace_records()에서 selected_hypothesis_id/confidence 읽기
         _write_per_step_jsonl()에서 선택한 값 emit (하드코딩 None 제거)
     B5: _build_metrics_with_blocked_markers() 또는 main()에서
         per_step wrong_prob variance 분석 → C5_calibration_status 결정
         outputs/audits/step4_ece_degenerate_predictor_audit.json 작성

  3. tests/test_step4_valid_trained_eval.py (B3, 5개 테스트)
  4. tests/test_step4_trace_writer.py (B4, 3개 테스트)
  5. tests/test_step4_ece_artifact.py (B5, 4개 테스트)

FILES_ALLOWED: |
  src/frcgw/evaluation/frcg_agent.py
  scripts/10_run_lr_real_eval.py
  scripts/audit_step4_ece_artifact.py
  tests/test_step4_valid_trained_eval.py
  tests/test_step4_trace_writer.py
  tests/test_step4_ece_artifact.py

FILES_FORBIDDEN: |
  src/frcgw/text_env/collector.py
  src/frcgw/evaluation/metrics.py
  src/frcgw/schemas/visibility.py
  paper_context_ref/
  data/
  .claude/settings.json
  scripts/run_codex_task.ps1
  configs/
  outputs/

REQUIRED_IMPLEMENTATION: |
  ### A. frcg_agent.py TextFRCGModelAgent 수정

  `__init__`에 추가:
  ```python
  self._last_selected_hypothesis_id: str | None = None
  self._last_selected_hypothesis_confidence: float | None = None
  ```

  `reset()`에 추가:
  ```python
  self._last_selected_hypothesis_id = None
  self._last_selected_hypothesis_confidence = None
  ```

  `act()` 내부, model forward 직후:
  ```python
  with torch.no_grad():
      model_out = self.model.forward(obs)
      grammar_probs = F.softmax(model_out.z_grammar_logits, dim=-1)
      best_grammar_idx = int(grammar_probs.argmax().item())
      self._last_selected_hypothesis_id = f"grammar_{best_grammar_idx}"
      self._last_selected_hypothesis_confidence = float(grammar_probs.max().item())
      # existing code continues...
      max_grammar_prob = float(grammar_probs.max().item())
      action, plan_meta = text_frcg_plan(...)
  ```

  ### B. _TracingAgent.act() 수정 (10_run_lr_real_eval.py L178-192)

  ```python
  def act(self, obs: PublicObservation) -> Any:
      action, compute_log = self._agent.act(obs)
      self.records.append(
          {
              "action_id": action.action_id,
              "action_type": action.action_type,
              "planning_calls": compute_log.planning_calls,
              "rollout_steps": compute_log.rollout_steps,
              "predicted_wrong": getattr(self._agent, "last_predicted_wrong", None),
              "wrong_prob": getattr(self._agent, "last_wrong_prob", None),
              "f_t": getattr(self._agent, "last_F_t", None),
              "tau_f": getattr(self._agent, "_last_tau_f", None),
              "selected_hypothesis_id": getattr(self._agent, "_last_selected_hypothesis_id", None),
              "selected_hypothesis_confidence": getattr(self._agent, "_last_selected_hypothesis_confidence", None),
          }
      )
      return action, compute_log
  ```

  ### C. _attach_trace_records() 수정 (L231-235 영역)

  trace dict에서 selected_hypothesis_id, selected_hypothesis_confidence를 읽어
  per_step dict에 추가:
  ```python
  per_step.append({
      ...existing fields...,
      "selected_hypothesis_id": trace.get("selected_hypothesis_id"),
      "selected_hypothesis_confidence": trace.get("selected_hypothesis_confidence"),
  })
  ```

  ### D. _write_per_step_jsonl() 수정 (L293-316 영역)

  `selected_hypothesis_id: None` → `record.get("selected_hypothesis_id")`
  `selected_hypothesis_confidence: None` → `record.get("selected_hypothesis_confidence")`

  ### E. _write_manifest() 수정 (L518-551 영역)

  ```python
  ckpt_paths_all_provided = all(bool(spec.get("ckpt_path")) for spec in text_specs)
  valid_trained_eval = ckpt_paths_all_provided  # True iff all ckpts provided
  # keep random_init_ok as-is for backward compat (it equals ckpt_paths_all_provided, confusingly named)
  hard_checks_all_pass = (
      metrics_payload.get("fake_metric_count") == 0
      and forbidden_source_assertion == "none_read"
      and (random_init_ok or ckpt_paths_all_provided)
  )  # hard_checks_all_pass logic unchanged
  manifest = {
      ...existing fields...,
      "valid_trained_eval": valid_trained_eval,  # NEW disclosure field
  }
  ```

  ### F. C5_calibration_status computation

  In main() or a helper, after all_results are collected:
  ```python
  all_wrong_probs = [
      rec["wrong_prob"]
      for agent_id, _, result in all_results
      for rec in getattr(result, "_real_eval_step_records", [])
      if rec.get("wrong_prob") is not None
  ]
  if all_wrong_probs:
      import statistics
      variance = statistics.pvariance(all_wrong_probs)
      unique_count = len(set(all_wrong_probs))
      mean_wp = sum(all_wrong_probs) / len(all_wrong_probs)
      if variance < 1e-6 and unique_count < 2 and mean_wp == 0.0:
          c5_status = "DEGENERATE_PREDICTOR"
      else:
          c5_status = "OK"
  else:
      c5_status = "NO_DATA"
  metrics_payload["C5_calibration_status"] = c5_status
  ```

  Write audit file:
  ```python
  ece_audit = {
      "n_steps": len(all_wrong_probs),
      "variance_wrong_prob": variance if all_wrong_probs else None,
      "unique_wrong_prob_count": unique_count if all_wrong_probs else None,
      "mean_wrong_prob": mean_wp if all_wrong_probs else None,
      "C5_calibration_status": c5_status,
  }
  (out_dir / ".." / ".." / "audits" / "step4_ece_degenerate_predictor_audit.json").write_text(
      json.dumps(ece_audit, indent=2), encoding="utf-8"
  )
  # OR write to outputs/audits/ directly via Path
  ```

REQUIRED_TESTS: |
  tests/test_step4_valid_trained_eval.py — 5개:

  1. test_valid_trained_eval_false_without_ckpt
     - config with TextFRCGModelAgent ckpt_path=None → valid_trained_eval=False in manifest

  2. test_valid_trained_eval_true_with_all_ckpts
     - config with TextFRCGModelAgent ckpt_path="some/path.ckpt" → valid_trained_eval=True

  3. test_metrics_contains_valid_trained_eval
     - after _write_manifest, manifest dict contains "valid_trained_eval" key

  4. test_hard_checks_requires_valid_trained_eval
     - valid_trained_eval=False → hard_checks_all_pass=False (verify disclosure semantics)

  5. test_manifest_disclosure_fields_present
     - manifest contains: valid_trained_eval, random_init_ok, ckpt_paths_all_provided, hard_checks_all_pass

  tests/test_step4_trace_writer.py — 3개:

  1. test_per_step_records_selected_hypothesis_id_when_agent_emits
     - create mock agent with _last_selected_hypothesis_id = "grammar_3"
     - _TracingAgent wraps it; after act(), records[0]["selected_hypothesis_id"] == "grammar_3"

  2. test_per_step_records_selected_hypothesis_confidence
     - mock agent with _last_selected_hypothesis_confidence = 0.75
     - records[0]["selected_hypothesis_confidence"] == 0.75

  3. test_per_step_null_when_agent_does_not_emit
     - mock agent WITHOUT _last_selected_hypothesis_id attribute
     - records[0]["selected_hypothesis_id"] is None (graceful getattr)

  tests/test_step4_ece_artifact.py — 4개:

  1. test_c5_status_degenerate_when_wrong_prob_constant
     - all_wrong_probs = [0.0] * 50 → C5_calibration_status == "DEGENERATE_PREDICTOR"

  2. test_c5_status_ok_when_wrong_prob_distributed
     - all_wrong_probs = [0.1, 0.9, 0.5, 0.3, 0.7] → C5_calibration_status == "OK"

  3. test_ece_artifact_audit_json_written
     - run C5 logic with mocked results; outputs/audits/step4_ece_degenerate_predictor_audit.json exists
     - JSON contains "C5_calibration_status", "variance_wrong_prob" keys

  4. test_c5_claim_blocked_when_degenerate
     - When C5_calibration_status == "DEGENERATE_PREDICTOR", metrics.json must NOT report ECE
       as valid calibration evidence (verify: a warning message or status field indicates this)

ACCEPTANCE_CRITERIA: |
  - pytest tests/test_step4_valid_trained_eval.py -q → 5/5 PASSED
  - pytest tests/test_step4_trace_writer.py -q → 3/3 PASSED
  - pytest tests/test_step4_ece_artifact.py -q → 4/4 PASSED
  - pytest tests/test_lr_real_eval_runner.py -q → 14/14 PASSED (회귀)
  - frcg_agent.py 수정 후 _last_selected_hypothesis_id property 존재 확인
  - per_step jsonl row에 selected_hypothesis_id 필드 존재 (None 허용)
  - C5_calibration_status가 metrics dict에 포함됨 (metrics.json에 기록)
  - outputs/audits/step4_ece_degenerate_predictor_audit.json 존재 (smoke run 후)
  - valid_trained_eval field가 manifest에 존재

COMMIT_MESSAGE: |
  feat(step4/task4): valid_trained_eval disclosure + trace writer fix + ECE degeneracy flag

  B3: adds valid_trained_eval=ckpt_paths_all_provided to manifest for disclosure.
  B4: _TracingAgent reads _last_selected_hypothesis_id/confidence from agent;
      frcg_agent.py emits grammar argmax as hypothesis ID.
      _write_per_step_jsonl no longer hardcodes None.
  B5: C5_calibration_status computed from wrong_prob variance/uniqueness;
      DEGENERATE_PREDICTOR when F_t=0.0 constant (random-init artifact).

  12 new tests: 5 (B3) + 3 (B4) + 4 (B5). 14 regression green.

STOP_CONDITION: |
  12 tests green, 14 regression green. FILES_FORBIDDEN 미수정.
  metrics.py 미수정. C5_calibration_status가 metrics dict에 있는지 확인.
  If frcg_agent.py modification breaks existing tests, revert and report BLOCKED.

RELATED_AGENT_REPORT_IDS: |
  docs/orchestration/agent_reports/2026-05/claim_metric_alignment_step4_T2_R1.md
  docs/orchestration/agent_reports/2026-05/experiment_design_step4_T2_R1.md
