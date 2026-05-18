TASK_NAME: step7_c4_expanded_validation
SANDBOX_MODE: bypass
BACKGROUND: |
  FRCG-WM STEP 7. Branch: memory-redesign-2026-05-16.

  STEP 6에서 C4 (task_success_rate_id_split) = 0.824가 처음 측정됐다 (n=1 seed, 10 episodes).
  STEP 7에서 n=5 seeds + full splits (test_id 34 ep, test_ood 50 ep) × 3 agents로 확장 검증.

  목적:
  - C4 0.824가 smoke artifact인지 아니면 실제 signal인지 판별
  - ABL-024 (no-alternative-hypothesis), ABL-036 (no-compute-gate)과 비교
  - C4 status: READY_FOR_REPORT 조건 — mean > 0.7 AND std < 0.15 AND ABL-024/036 < FRCG-LR by 0.05+

GOAL: |
  1. configs/lr_eval_real_v0_3_step7_full.yaml 신규 작성
  2. scripts/audit_step7_c4_expanded_validation.py 신규 작성
  3. tests/test_step7_c4_expanded_aggregator.py 신규 작성
  4. docs/orchestration/lr_alignment/32_step7_c4_validation_design.md 신규 작성

FILES_ALLOWED:
  - configs/lr_eval_real_v0_3_step7_full.yaml
  - scripts/audit_step7_c4_expanded_validation.py
  - tests/test_step7_c4_expanded_aggregator.py
  - docs/orchestration/lr_alignment/32_step7_c4_validation_design.md

FILES_FORBIDDEN:
  - outputs/
  - data/
  - src/frcgw/schemas/visibility.py
  - src/frcgw/schemas/step_schema.py
  - paper_context_ref/
  - .claude/
  - scripts/run_codex_task.ps1
  - configs/train_text*.yaml
  - configs/lr_eval_real_v0_3_step*.yaml (STEP 5/6 configs는 보존)

REQUIRED_IMPLEMENTATION: |
  ## 1. configs/lr_eval_real_v0_3_step7_full.yaml

  ```yaml
  # STEP 7 expanded C4 validation config
  # Source: STEP 7 plan N5 C4 Expanded Gate
  version: step7_full
  dataset_root: data/frcgw_text/v0_3
  checkpoint_path: outputs/checkpoints/pretrain_v0_3_falsification/checkpoint_best.pt
  model_config: configs/model_text.yaml
  max_episodes: null  # full split
  compute_budget:
    planning_calls_cap: 5
    rollout_steps_cap: 10
  agents:
    - id: FRCG-LR
      type: frcg_lr
      checkpoint: outputs/checkpoints/pretrain_v0_3_falsification/checkpoint_best.pt
    - id: ABL-024
      type: no_alternative_hypothesis
      checkpoint: outputs/checkpoints/pretrain_v0_3_falsification/checkpoint_best.pt
    - id: ABL-036
      type: no_compute_gate
      checkpoint: outputs/checkpoints/pretrain_v0_3_falsification/checkpoint_best.pt
  metrics:
    - task_success_rate
    - falsification_precision_recall
    - ood_shift_f1
    - progress_per_compute
    - false_planning_call_rate
  splits:
    - test_id
    - test_ood
  seeds: [0, 1, 2, 3, 4]
  output_root: outputs/runs/p3_lr_real_eval_step7_full
  ```

  ## 2. scripts/audit_step7_c4_expanded_validation.py

  다음 interface를 구현한다:
  ```
  python scripts/audit_step7_c4_expanded_validation.py \
    --config configs/lr_eval_real_v0_3_step7_full.yaml \
    --seeds 0 1 2 3 4 \
    --splits test_id test_ood \
    --agents FRCG-LR ABL-024 ABL-036 \
    --out outputs/audits/step7_c4_expanded_validation.json
  ```

  기능:
  - 각 (seed, split, agent) 조합의 결과 디렉토리에서 metrics JSON 읽기
  - task_success_rate에 대해 mean, std 계산
  - C4 status 판정:
    - READY_FOR_REPORT: FRCG-LR mean > 0.7 AND std < 0.15 AND (FRCG-LR mean - ABL-024 mean > 0.05) AND (FRCG-LR mean - ABL-036 mean > 0.05)
    - PRELIMINARY: FRCG-LR mean > 0.5 but 위 조건 일부 미충족
    - DOWNSHIFT: FRCG-LR mean <= 0.5 (STEP 6 0.824 smoke artifact 확정)
    - INCOMPLETE: 결과 파일 없음
  - fake_metric_count: 0 검증 (결과 파일에서 fake_metric 필드 확인)
  - JSON 출력 스키마:
    ```json
    {
      "step": "step7",
      "config": "configs/lr_eval_real_v0_3_step7_full.yaml",
      "seeds": [0, 1, 2, 3, 4],
      "splits": ["test_id", "test_ood"],
      "agents": ["FRCG-LR", "ABL-024", "ABL-036"],
      "results": {
        "test_id": {
          "FRCG-LR": {"mean_task_success_rate": 0.0, "std_task_success_rate": 0.0, "n_seeds": 0, "raw": []},
          "ABL-024": {"mean_task_success_rate": 0.0, "std_task_success_rate": 0.0, "n_seeds": 0, "raw": []},
          "ABL-036": {"mean_task_success_rate": 0.0, "std_task_success_rate": 0.0, "n_seeds": 0, "raw": []}
        },
        "test_ood": { "..." : "..." }
      },
      "c4_status": "INCOMPLETE",
      "c4_status_reason": "...",
      "fake_metric_count": 0,
      "comparison_delta": {
        "FRCG-LR_vs_ABL-024_test_id": null,
        "FRCG-LR_vs_ABL-036_test_id": null
      }
    }
    ```
  - --incomplete-ok 플래그: 결과 파일 없어도 INCOMPLETE로만 기록 (error 아님)

  구현 시 주의:
  - outputs/ 경로는 읽기만 (write는 --out 경로만)
  - data/ 경로는 접근하지 않음
  - 모든 숫자는 실제 파일에서 읽음 (하드코딩 금지)
  - 결과 파일 없으면 해당 셀을 null로 기록

  ## 3. docs/orchestration/lr_alignment/32_step7_c4_validation_design.md

  ```markdown
  # STEP 7 — C4 Expanded Validation Design

  date: 2026-05-18
  n_seeds: 5
  splits: test_id (34 ep), test_ood (50 ep)
  agents: FRCG-LR, ABL-024 (no-alt-hyp), ABL-036 (no-compute-gate)

  ## C4 Status Criteria

  - READY_FOR_REPORT: mean > 0.7 AND std < 0.15 AND FRCG-LR > ABL-024 by 0.05+ AND FRCG-LR > ABL-036 by 0.05+
  - PRELIMINARY: mean > 0.5 but criteria partially unmet
  - DOWNSHIFT: mean <= 0.5 (STEP 6 0.824 was smoke artifact)
  - INCOMPLETE: results not yet available

  ## Checkpoint

  STEP 6 falsification checkpoint: outputs/checkpoints/pretrain_v0_3_falsification/checkpoint_best.pt
  SHA256[:16]: 1910C13F7708CE10 (immutable)

  ## Output

  outputs/audits/step7_c4_expanded_validation.json
  (STEP 6 audit files must NOT be overwritten)
  ```

REQUIRED_TESTS: |
  ## tests/test_step7_c4_expanded_aggregator.py

  ```python
  """Tests for audit_step7_c4_expanded_validation.py aggregator logic."""
  import json
  import subprocess
  import sys
  from pathlib import Path


  def test_aggregator_imports():
      """Script must be importable without error."""
      import importlib.util
      spec = importlib.util.spec_from_file_location(
          "audit_step7_c4",
          Path("scripts/audit_step7_c4_expanded_validation.py")
      )
      assert spec is not None, "Script not found"


  def test_aggregator_schema_keys():
      """Output JSON must have required schema keys."""
      required_keys = {
          "step", "config", "seeds", "splits", "agents",
          "results", "c4_status", "c4_status_reason",
          "fake_metric_count", "comparison_delta"
      }
      # Run with --incomplete-ok to allow missing results
      result = subprocess.run(
          [sys.executable, "scripts/audit_step7_c4_expanded_validation.py",
           "--config", "configs/lr_eval_real_v0_3_step7_full.yaml",
           "--seeds", "0", "1",
           "--splits", "test_id",
           "--agents", "FRCG-LR",
           "--out", "outputs/audits/test_step7_c4_schema_check.json",
           "--incomplete-ok"],
          capture_output=True, text=True, timeout=30
      )
      # Should exit 0 or produce output file (INCOMPLETE is valid)
      output_path = Path("outputs/audits/test_step7_c4_schema_check.json")
      if output_path.exists():
          with open(output_path) as f:
              data = json.load(f)
          assert required_keys.issubset(data.keys()), f"Missing keys: {required_keys - data.keys()}"
          assert data["fake_metric_count"] == 0


  def test_c4_status_incomplete_when_no_results(tmp_path):
      """When no result files exist, c4_status must be INCOMPLETE."""
      import importlib.util, types
      # Load the module
      spec = importlib.util.spec_from_file_location(
          "audit_step7_c4",
          Path("scripts/audit_step7_c4_expanded_validation.py")
      )
      if spec is None:
          return  # Script not found yet, skip
      module = importlib.util.module_from_spec(spec)
      try:
          spec.loader.exec_module(module)
      except Exception:
          return  # Module has side effects on import, skip structural test

      # If the module has a determine_c4_status function, test it directly
      if hasattr(module, "determine_c4_status"):
          status = module.determine_c4_status(
              frcg_lr_means=[], abl024_means=[], abl036_means=[]
          )
          assert status["c4_status"] == "INCOMPLETE"
  ```

ACCEPTANCE_CRITERIA: |
  1. pytest tests/test_step7_c4_expanded_aggregator.py -q → ALL GREEN (or skipped if result files absent)
  2. configs/lr_eval_real_v0_3_step7_full.yaml 존재
  3. scripts/audit_step7_c4_expanded_validation.py 존재
  4. docs/orchestration/lr_alignment/32_step7_c4_validation_design.md 존재
  5. git diff outputs/ → empty (aggregator는 read-only, --out 경로만 write)
  6. STEP 6 audit JSON 불변 (outputs/audits/step6_*.json 미수정)
  7. configs/lr_eval_real_v0_3_step{5,6}*.yaml 미수정

COMMIT_MESSAGE: "feat(step7/task4): C4 expanded validation harness (5 seeds, full splits, 3 agents)"

STOP_CONDITION: |
  STOP if:
  - outputs/audits/step6_*.json was modified
  - outputs/runs/p3_lr_real_eval_step{5,6}_* was modified
  - configs/lr_eval_real_v0_3_step5*.yaml or step6*.yaml was modified
  - Any hardcoded numeric metric values appear in scripts (all must come from files)
  - data/ directories were accessed or modified
