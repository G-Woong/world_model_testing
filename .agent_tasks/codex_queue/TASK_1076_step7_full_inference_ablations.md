TASK_NAME: step7_full_inference_ablations
SANDBOX_MODE: bypass
BACKGROUND: |
  FRCG-WM STEP 7. Branch: memory-redesign-2026-05-16.

  STEP 6에서 14 CRITICAL ablation이 ABLATION_REGISTRY에 등록됐다. STEP 7에서
  inference-time ablation 11개를 full eval harness로 실행한다.

  11 inference-time ablations:
  - ABL-006 (collapsed_latent)
  - ABL-011 (no_rollout)
  - ABL-017 (random_alternative)
  - ABL-022 (classifier_variant_a, LR 변형)
  - ABL-023 (uncertainty_instead_of_falsification)
  - ABL-024 (no_alternative_hypothesis)
  - ABL-033 (no_rewrite)
  - ABL-034 (no_progress_reward)
  - ABL-035 (no_compute_gate_soft)
  - ABL-036 (no_compute_gate)
  - ABL-040 (positive_control_oracle_leakage — 격리 필수)

  NOT executed in STEP 7 (faithful retrain needed):
  - ABL-001 (no_control_grammar_training)
  - ABL-003 (merged_regime_control_grammar_training)
  - ABL-015 (no_falsification_training_hard)

  ABL-040은 positive control (oracle leakage 감지용). FAIL이 정상이므로
  별도 "positive_control_results" 그룹에 격리.

GOAL: |
  1. scripts/run_step7_full_inference_ablations.py 신규 작성
  2. configs/ablation_core.yaml에 STEP 7 execution 메타데이터 추가 (기존 entries 변경 금지)
  3. tests/test_step7_full_ablation_dispatch.py 신규 작성
  4. docs/orchestration/lr_alignment/33_step7_ablation_execution_results.md 신규 작성

FILES_ALLOWED:
  - scripts/run_step7_full_inference_ablations.py
  - configs/ablation_core.yaml
  - tests/test_step7_full_ablation_dispatch.py
  - docs/orchestration/lr_alignment/33_step7_ablation_execution_results.md

FILES_FORBIDDEN:
  - outputs/
  - data/
  - src/frcgw/evaluation/ablations.py
  - src/frcgw/schemas/visibility.py
  - paper_context_ref/
  - .claude/
  - scripts/run_codex_task.ps1
  - configs/train_text*.yaml

REQUIRED_IMPLEMENTATION: |
  ## 1. configs/ablation_core.yaml — STEP 7 메타데이터 추가

  기존 ablation entries 아래에 다음 섹션을 추가 (기존 항목 절대 변경 금지):

  ```yaml
  # STEP 7 execution metadata (2026-05-18)
  step7_execution:
    planned_date: "2026-05-18"
    inference_time_ablations:
      - ABL-006
      - ABL-011
      - ABL-017
      - ABL-022
      - ABL-023
      - ABL-024
      - ABL-033
      - ABL-034
      - ABL-035
      - ABL-036
    positive_control_isolated:
      - ABL-040
    deferred_to_step8_faithful_retrain:
      - ABL-001
      - ABL-003
      - ABL-015
    note: "ABL-001/003/015 are training-time ablations. STEP 7 only runs inference-time ablations."
  ```

  ## 2. scripts/run_step7_full_inference_ablations.py

  다음 interface를 구현한다:
  ```
  python scripts/run_step7_full_inference_ablations.py \
    --config configs/lr_eval_real_v0_3_step7_full.yaml \
    --checkpoint outputs/checkpoints/pretrain_v0_3_falsification/checkpoint_best.pt \
    --out-dir outputs/runs/p3_lr_real_eval_step7_ablations
  ```

  기능:
  - 11개 inference-time ablation agent를 순차 실행 (각 ablation agent ID로 eval_runner 호출)
  - ABL-040은 `positive_control_results` 서브디렉토리에 격리
  - 각 ablation 결과를 `out-dir/<abl_id>/results.json`에 저장
  - 실행 완료 후 `out-dir/step7_ablation_manifest.json` 생성:
    ```json
    {
      "step": "step7",
      "executed_ablations": ["ABL-006", "ABL-011", ...],
      "positive_control_isolated": ["ABL-040"],
      "deferred_ablations": ["ABL-001", "ABL-003", "ABL-015"],
      "deferred_reason": "training-time ablations require faithful retrain (STEP 8)",
      "fake_metric_count": 0,
      "checkpoint": "...",
      "config": "..."
    }
    ```
  - --dry-run 플래그: 실행 시뮬레이션만 (ablation agent ID 목록 출력, 실제 eval 미수행)

  구현 시 주의:
  - ABL-001/003/015는 실행하지 않고 deferred_ablations에만 기록
  - ABL-040 결과가 "positive_control_results" 외부에 섞이지 않도록 격리
  - outputs/ 내 기존 STEP 5/6 eval 결과 절대 덮어쓰기 금지
  - 실제 eval이 없어도 (--dry-run) manifest는 생성

  ## 3. docs/orchestration/lr_alignment/33_step7_ablation_execution_results.md

  ```markdown
  # STEP 7 — Full Inference Ablation Execution Results

  date: 2026-05-18
  status: PLANNED (results pending eval execution)

  ## Executed Ablations (11 inference-time)

  | ID | Description | Expected Collapse | Result |
  |---|---|---|---|
  | ABL-006 | collapsed latent | falsification_precision_recall_f1 ↓ | PENDING |
  | ABL-011 | no rollout | alternative_rollout_fidelity ↓ | PENDING |
  | ABL-017 | random alternative | task_success_rate ↓ | PENDING |
  | ABL-022 | classifier variant A | falsification_precision_recall_f1 change | PENDING |
  | ABL-023 | uncertainty instead of falsification | false_planning_call_rate ↑ | PENDING |
  | ABL-024 | no alternative hypothesis | task_success_rate ↓ | PENDING |
  | ABL-033 | no rewrite | task_success_rate ↓ | PENDING |
  | ABL-034 | no progress/reward | progress_per_compute ↓ | PENDING |
  | ABL-035 | no compute gate (soft) | false_planning_call_rate ↑ | PENDING |
  | ABL-036 | no compute gate | false_planning_call_rate ↑ | PENDING |

  ## Positive Control (isolated)

  | ID | Description | Expected Result |
  |---|---|---|
  | ABL-040 | oracle leakage positive control | PASS (leakage detected) = F1 artificially high |

  ABL-040 FAIL = leakage working correctly (intended).

  ## Deferred to STEP 8 (faithful retrain required)

  | ID | Description | Reason |
  |---|---|---|
  | ABL-001 | no control grammar training | requires training-time l_grammar=0 |
  | ABL-003 | merged regime control grammar training | requires re-training with merged head |
  | ABL-015 | no falsification training hard | requires training-time l_falsification=0 (different from ABL-016) |

  These are training-proxy ablations only in STEP 7. STEP 8 faithful retrain is required
  for paper reporting. Do NOT report these as faithful ablation results.
  ```

REQUIRED_TESTS: |
  ## tests/test_step7_full_ablation_dispatch.py

  ```python
  """Tests that full ablation harness dispatches correct ablations and isolates ABL-040."""
  import json
  import subprocess
  import sys
  from pathlib import Path


  EXPECTED_ABLATIONS = {
      "ABL-006", "ABL-011", "ABL-017", "ABL-022", "ABL-023",
      "ABL-024", "ABL-033", "ABL-034", "ABL-035", "ABL-036"
  }
  POSITIVE_CONTROL = {"ABL-040"}
  DEFERRED = {"ABL-001", "ABL-003", "ABL-015"}


  def test_harness_script_exists():
      assert Path("scripts/run_step7_full_inference_ablations.py").exists()


  def test_dry_run_lists_correct_ablations(tmp_path):
      """Dry run must list exactly 11 ablations + ABL-040 isolated + 3 deferred."""
      result = subprocess.run(
          [sys.executable, "scripts/run_step7_full_inference_ablations.py",
           "--config", "configs/lr_eval_real_v0_3_step7_full.yaml",
           "--checkpoint", "outputs/checkpoints/pretrain_v0_3_falsification/checkpoint_best.pt",
           "--out-dir", str(tmp_path / "ablation_out"),
           "--dry-run"],
          capture_output=True, text=True, timeout=30
      )
      # Check that output mentions the 11 ablations
      output = result.stdout + result.stderr
      for abl in EXPECTED_ABLATIONS:
          assert abl in output, f"{abl} not mentioned in dry-run output"

      # ABL-040 must be flagged as isolated
      assert "ABL-040" in output

      # Deferred ablations must be mentioned as deferred
      for abl in DEFERRED:
          assert abl in output, f"{abl} not mentioned as deferred"


  def test_abl001_003_015_not_in_executed(tmp_path):
      """ABL-001/003/015 must not appear in executed_ablations in manifest."""
      result = subprocess.run(
          [sys.executable, "scripts/run_step7_full_inference_ablations.py",
           "--config", "configs/lr_eval_real_v0_3_step7_full.yaml",
           "--checkpoint", "outputs/checkpoints/pretrain_v0_3_falsification/checkpoint_best.pt",
           "--out-dir", str(tmp_path / "ablation_out"),
           "--dry-run"],
          capture_output=True, text=True, timeout=30
      )
      manifest_path = tmp_path / "ablation_out" / "step7_ablation_manifest.json"
      if manifest_path.exists():
          with open(manifest_path) as f:
              manifest = json.load(f)
          executed = set(manifest.get("executed_ablations", []))
          for abl in DEFERRED:
              assert abl not in executed, f"{abl} must not be in executed_ablations"
          assert manifest.get("fake_metric_count", 0) == 0


  def test_abl040_isolated_from_main_results(tmp_path):
      """ABL-040 must be in positive_control_isolated, not in executed_ablations."""
      result = subprocess.run(
          [sys.executable, "scripts/run_step7_full_inference_ablations.py",
           "--config", "configs/lr_eval_real_v0_3_step7_full.yaml",
           "--checkpoint", "outputs/checkpoints/pretrain_v0_3_falsification/checkpoint_best.pt",
           "--out-dir", str(tmp_path / "ablation_out"),
           "--dry-run"],
          capture_output=True, text=True, timeout=30
      )
      manifest_path = tmp_path / "ablation_out" / "step7_ablation_manifest.json"
      if manifest_path.exists():
          with open(manifest_path) as f:
              manifest = json.load(f)
          executed = set(manifest.get("executed_ablations", []))
          positive = set(manifest.get("positive_control_isolated", []))
          assert "ABL-040" in positive, "ABL-040 must be in positive_control_isolated"
          assert "ABL-040" not in executed, "ABL-040 must NOT be in executed_ablations"
  ```

ACCEPTANCE_CRITERIA: |
  1. pytest tests/test_step7_full_ablation_dispatch.py -q → ALL GREEN (or skipped if configs absent)
  2. scripts/run_step7_full_inference_ablations.py 존재
  3. configs/ablation_core.yaml에 step7_execution 섹션 추가, 기존 항목 불변
  4. docs/orchestration/lr_alignment/33_step7_ablation_execution_results.md 존재
  5. ABL-040이 positive_control_isolated에 격리됨 (executed_ablations 미포함)
  6. ABL-001/003/015이 executed_ablations에 없고 deferred_ablations에만 기록
  7. git diff src/frcgw/evaluation/ablations.py → empty (registry 변경 없음)
  8. git diff outputs/ → empty (Codex는 outputs/ 쓰기 금지)

COMMIT_MESSAGE: "feat(step7/task5): full 11 inference-time ablation harness + ABL-040 isolation + STEP 8 deferred list"

STOP_CONDITION: |
  STOP if:
  - ABL-001, ABL-003, or ABL-015 appears in executed_ablations
  - ABL-040 is not isolated in positive_control_isolated
  - outputs/ directory was written (Codex must not execute eval)
  - src/frcgw/evaluation/ablations.py was modified (registry must stay unchanged)
  - Existing ablation_core.yaml entries were modified or removed
