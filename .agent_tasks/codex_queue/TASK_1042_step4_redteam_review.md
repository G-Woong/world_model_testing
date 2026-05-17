TASK_NAME: TASK_1042_step4_redteam_review
SANDBOX_MODE: bypass

BACKGROUND: |
  FRCG-WM STEP 4 — Task 5 Red-team Review.
  Task 1-4(TASK_1038~1041) 완료 후 STEP 4 전체 diff를 종합 검토한다.
  이 task는 **read-only** — 어떤 파일도 수정하지 않는다.
  RESULT.md에 검토 결과만 기록한다.

GOAL: |
  다음 7개 위험 항목을 검토하고 PASS/WARN/FAIL 판정:

  1. HIDDEN_LABEL_LEAKAGE
     - counterfactual_rollout.py: is_oracle_best 결정에 true_wrong_hypothesis 사용 여부
     - collector.py _build_counterfactuals: hidden_preconditions가 public_observation에 노출되는지
     - frcg_agent.py: _last_selected_hypothesis_id 값이 true_control_grammar token 포함 여부

  2. FAKE_COUNTERFACTUAL
     - counterfactual_effect_type이 GrammarEngine.apply() 실제 호출 결과에서 오는지 확인
     - progress_delta가 hard-coded 값이 아닌 effect_map에서 파생되는지 확인

  3. RANDOM_INIT_MISUSE
     - valid_trained_eval=False인 경우 metric 값이 "claim evidence"로 표기되지 않는지 확인
     - ECE=0.025가 C5_calibration_status="DEGENERATE_PREDICTOR"로 표시되는지 확인

  4. C5_MISUSE
     - C5_calibration_status가 falsification_calibration() 반환값을 override하는지 확인 (override 금지)
     - C5_calibration_status는 metadata-only로만 사용되는지 확인

  5. OLD_ARTIFACT_OVERWRITE
     - data/frcgw_text/v0_1/, data/frcgw_text/v0_2/ 파일이 변경됐는지 확인
     - outputs/runs/p3_lr_real_eval_smoke/ 기존 artifact가 변경됐는지 확인

  6. CLAIM_OVERSTATEMENT
     - C4_rollout_fidelity metric 함수가 STEP 4에서 구현됐다면 FAIL
     - "C4 resolved" 또는 "rollout fidelity proven" 표현이 결과에 포함됐는지 확인

  7. EXISTENCE_ONLY_TESTS
     - test_step4_*.py 테스트들이 실제 assert를 포함하는지 확인
     - "assert True" 또는 빈 pass 테스트가 없는지 확인

FILES_ALLOWED: |
  (read-only)
  src/frcgw/text_env/counterfactual_rollout.py
  src/frcgw/text_env/collector.py
  src/frcgw/evaluation/frcg_agent.py
  scripts/10_run_lr_real_eval.py
  scripts/audit_step4_lr_comparison.py
  scripts/audit_step4_ece_artifact.py
  tests/test_step4_evidence_timestamp.py
  tests/test_step4_counterfactual_rollout.py
  tests/test_step4_counterfactual_no_leakage.py
  tests/test_step4_lr_comparison.py
  tests/test_step4_valid_trained_eval.py
  tests/test_step4_trace_writer.py
  tests/test_step4_ece_artifact.py

FILES_FORBIDDEN: |
  (ANY write operation to any file)

REQUIRED_IMPLEMENTATION: |
  RESULT.md에 다음 형식으로 작성:

  # STEP 4 Red-team Review Result
  ## Verdict: [PASS | WARN | FAIL]
  ## Items:
  | Item | Status | Notes |
  |---|---|---|
  | HIDDEN_LABEL_LEAKAGE | [PASS|WARN|FAIL] | ... |
  | FAKE_COUNTERFACTUAL | [PASS|WARN|FAIL] | ... |
  | RANDOM_INIT_MISUSE | [PASS|WARN|FAIL] | ... |
  | C5_MISUSE | [PASS|WARN|FAIL] | ... |
  | OLD_ARTIFACT_OVERWRITE | [PASS|WARN|FAIL] | ... |
  | CLAIM_OVERSTATEMENT | [PASS|WARN|FAIL] | ... |
  | EXISTENCE_ONLY_TESTS | [PASS|WARN|FAIL] | ... |
  ## Blockers:
  [list any FAIL items with specific line references]

REQUIRED_TESTS: |
  N/A (read-only review)

ACCEPTANCE_CRITERIA: |
  - RESULT.md 존재 및 7개 항목 판정 포함
  - 어떤 파일도 수정하지 않음 (FILES_ALLOWED = read-only)
  - HIDDEN_LABEL_LEAKAGE: PASS (counterfactual에 hidden label 없음)
  - FAKE_COUNTERFACTUAL: PASS (effect_map에서 파생)
  - OLD_ARTIFACT_OVERWRITE: PASS (v0_1/v0_2 미수정)
  - CLAIM_OVERSTATEMENT: PASS (C4_rollout_fidelity metric 함수 구현 없음)

COMMIT_MESSAGE: |
  review(step4/task5): STEP 4 red-team review complete

  Read-only review of Task 1-4 diff. RESULT.md records 7-item verdict.
  No code modified.

STOP_CONDITION: |
  RESULT.md 작성 완료. FAIL 항목 발견 시 즉시 BLOCKED 이유 기록 + Main Claude에 이관.
