TASK_NAME: step2_real_eval_runner
SANDBOX_MODE: bypass
BACKGROUND:
  Run 6의 P3_LR_EVAL.passed sentinel은 real eval 결과가 아니라 preflight smoke 집계다.
  scripts/09_run_lr_eval.py:147에 "preflight_from_smoke" 명시. 실제 test_id.jsonl은
  경로 검증만 했고 episode 순회 및 agent.act() 호출이 없었다.

  Contract MD: docs/orchestration/lr_alignment/18_real_eval_runner_contract.md

  기존 eval_runner.py::EvaluationRunner.run()이 episode loop + leakage assert를 완비하고
  있으므로 이를 재사용한다. 단, _without_none() 함수는 None을 0.0으로 변환하므로
  BLOCKED metric에 사용 금지 — 자체 _build_metrics_with_blocked_markers()를 구현한다.

  T2 experiment-design-expander 주요 발견:
  - eval_runner.py:322 _without_none이 None→0.0 변환: BLOCKED metric에 사용 금지
  - Tests 6/7/8: guard 직접 발화 테스트 (path를 직접 열어 RuntimeError 확인)
  - random_init_ok=false는 advisory (run 중단 X), hard_checks_all_pass=false 설정

  T2 feasibility 확인:
  - TextFRCGModel ~2.5M params, CPU-only, 10MB RAM
  - smoke run (3 episodes): ~5초 예상
  - 전체 run (33): ~5-10분 예상

GOAL:
  다음 4개 파일을 생성한다 (기존 파일 수정 금지):
  1. scripts/10_run_lr_real_eval.py (~280 lines)
  2. configs/lr_eval_real.yaml (~70 lines)
  3. tests/test_lr_real_eval_runner.py (~340 lines)

  기준: tests/test_lr_real_eval_runner.py 14개 모두 green.
  smoke run (--max-episodes 3) 성공, exit 0.
  manifest.forbidden_source_assertion == "none_read".
  metrics.fake_metric_count == 0.
  모든 BLOCKED metric의 value is None (JSON null).

FILES_ALLOWED:
  - scripts/10_run_lr_real_eval.py
  - configs/lr_eval_real.yaml
  - tests/test_lr_real_eval_runner.py

FILES_FORBIDDEN:
  - .claude/**
  - CLAUDE.md
  - .mcp.json
  - .venv/**
  - data/**
  - outputs/**
  - secrets/**
  - .env*
  - scripts/run_codex_task.ps1
  - paper_context_ref/**
  - src/frcgw/evaluation/eval_runner.py
  - src/frcgw/evaluation/metrics.py
  - src/frcgw/evaluation/baselines.py
  - src/frcgw/evaluation/ablations.py
  - src/frcgw/evaluation/frcg_agent.py
  - src/frcgw/falsification/lr_scorer.py
  - scripts/09_run_lr_eval.py
  - configs/lr_eval_core.yaml
  - .gitignore
  - .self_evolving_memory/hooks/hook_execution_log.md
  - docs/orchestration/AGENT_TEAMS_ROLLOUT_PLAN.md
  - docs/orchestration/session_reports/2026-05/2026-05-17_precompact_handoff.md
  - plans/PHASE_PROGRESS.md

REQUIRED_IMPLEMENTATION:

  ## A. configs/lr_eval_real.yaml

  ```yaml
  # Real episode-level eval config
  # Source: docs/orchestration/lr_alignment/18_real_eval_runner_contract.md
  run_mode: real_episode_eval
  dataset_path: data/frcgw_text/v0_1/test_id.jsonl
  split: test_id
  seeds: [0, 1, 2]
  out_dir: outputs/runs/p3_lr_real_eval

  agents:
    # FRCG-LR is alias for FRCG-FULL (same class: TextFRCGModelAgent)
    - id: FRCG-LR
      alias: FRCG-FULL
      class: TextFRCGModelAgent
      ckpt_path: null  # null = random init; random_init_ok=false in manifest
    - id: ABL-017
      class: TextFRCGModelAgent
      ablation: no_intent_action_mapping
      ckpt_path: null
    - id: ABL-022
      class: TextFRCGModelAgent
      ablation: no_falsification_score_gate
      ckpt_path: null
    - id: ABL-023
      class: TextFRCGModelAgent
      ablation: uncertainty_instead_of_falsification
      ckpt_path: null
    - id: BASE-006
      class: VerifierRecoveryAgent
    - id: BASE-012-CATTS
      class: CATTSStyleUncertaintyGateAgent
    - id: BASE-015
      class: ComputeMatchedRandomAgent
    - id: BASE-026
      class: WACStyleConsequenceCorrectionAgent
    - id: BASE-027
      class: CUWMStyleCandidateSimulationAgent
    - id: BASE-028
      class: WebWorldStyleSearchAgent
    - id: BASE-003+008-VLAA
      class: VLAALoopHeuristicAgent

  metrics:
    - task_success_rate
    - normalized_return
    - falsification_precision_recall
    - falsification_calibration
    - progress_per_compute
    - false_planning_call_rate
    - failed_action_repetition_rate
    - wrong_control_grammar_persistence
    - recovery_delay
    - action_switch_delay

  compute_budget:
    planning_calls_cap: 10
    rollout_steps_cap: 30
    max_candidates_per_call: 8

  forbidden_sources:
    - outputs/runs/p3_lr_smoke/metrics.json
    - outputs/runs/p3_ablations/ablation_results.json
    - outputs/runs/p3_lr_eval/metrics.json
  ```

  ## B. scripts/10_run_lr_real_eval.py

  ### 구조
  ```python
  """Real episode-level eval runner for FRCG-WM P3.
  Source: docs/orchestration/lr_alignment/18_real_eval_runner_contract.md
  """
  import argparse, builtins, datetime, json, subprocess, sys
  from pathlib import Path
  from typing import Any

  import yaml

  from frcgw.evaluation.ablations import ABLATION_REGISTRY, apply_ablation
  from frcgw.evaluation.baselines import (
      CATTSStyleUncertaintyGateAgent, ComputeMatchedRandomAgent,
      CUWMStyleCandidateSimulationAgent, VerifierRecoveryAgent,
      VLAALoopHeuristicAgent, WACStyleConsequenceCorrectionAgent,
      WebWorldStyleSearchAgent,
  )
  from frcgw.evaluation.eval_runner import EvaluationRunner
  from frcgw.evaluation.frcg_agent import TextFRCGModelAgent
  ```

  ### _install_forbidden_source_guard(forbidden_paths: list[str]) → callable

  `builtins.open`, `Path.open`, `Path.read_text` 3개를 monkeypatch.
  forbidden_paths 중 하나와 path가 match되면 `RuntimeError("forbidden source: {path}")` 발생.
  반환값은 uninstall 함수(lambda).

  Path matching: `str(Path(requested_path).resolve()) == str(Path(fp).resolve())` OR
  `str(Path(requested_path)).endswith(fp)` for relative path matching.

  매우 중요: `builtins.open`은 파일 경로 뿐 아니라 정수(fd), socket 등도 받는다.
  non-string 인자는 원래 함수로 즉시 pass-through.

  ### _build_agent_dispatch_table(config: dict) → dict[str, callable]

  agents 목록을 순회하여 agent_id → factory lambda 반환.
  ablation 있으면 apply_ablation 적용.
  FRCG-LR alias: agent_id="FRCG-LR"이면 base class TextFRCGModelAgent, baseline_id="FRCG-FULL" 유지.

  ### _preflight_dry_obs_check(dispatch_table: dict) → None

  각 agent에 dummy PublicObservation 1회 act() 호출.
  PublicObservation 생성: instruction="preflight", 나머지 empty.
  이미 assert_no_hidden_labels_in_input이 eval_runner에 있으나,
  여기서는 agent가 forbidden field를 observation에서 읽으려 하는지 확인 목적.

  ### _write_per_step_jsonl(...)
  ### _write_per_episode_jsonl(...)

  per_step 필드 (§6 스키마 참조):
    run_id, agent_id, agent_type, episode_id, step_id, step_index, split,
    action_id, action_type, selected_hypothesis_id (null), selected_hypothesis_confidence (null),
    f_t (agent.last_F_t if hasattr else null), tau_f (null),
    predicted_wrong, wrong_prob,
    planning_calls, rollout_steps, observed_effect_type ("unknown" default),
    true_wrong_hypothesis_available, leakage_guard_passed (True), error (null)

  per_episode 필드 (§7 스키마 참조):
    run_id, agent_id, episode_id, split,
    num_steps, planning_calls_total, rollout_steps_total,
    falsification_tp, falsification_fp, falsification_fn,
    degenerate_f_t_count (0 placeholder), h_exec_null_count (0 placeholder),
    blocked_metrics ([]), errors ([])

  ### _build_metrics_with_blocked_markers(all_results, config, dataset_audit) → dict

  **중요**: _without_none() 사용 절대 금지.

  BLOCKED 판단 기준 (dataset_audit dict에서 읽음):
  - hypothesis_update_timestamp_coverage == 0: C1_persistence → BLOCKED_no_hypothesis_update_timestamp
  - recovery_timestamp_coverage == 0: C3_recovery_delay → BLOCKED_no_recovery_timestamp
  - selected_hypothesis_confidence_coverage == 0: C5_calibration_ece → BLOCKED_no_confidence_label
  - counterfactual_coverage == 0: CF metrics → BLOCKED_no_counterfactual_samples
  - ood_split_exists == False: C2 regime-split → BLOCKED_no_ood_split

  모든 metric은 {"value": float_or_null, "status": "OK" or "BLOCKED_<reason>"} wrapper로 반환.
  `null`은 Python None → JSON null.

  ### _audit_dataset(dataset_path: str) → dict

  test_id.jsonl를 샘플링(최대 100 episodes)하여:
  - hypothesis_update_timestamp_coverage: steps 중 not None 비율
  - recovery_timestamp_coverage: 동일
  - selected_hypothesis_confidence_coverage: steps 중 not None 비율
  - counterfactual_coverage: steps 중 counterfactual list 비어있지 않은 비율
  - ood_split_exists: Path("data/frcgw_text/v0_1/test_ood.jsonl").exists()
  - total_episodes_sampled: int

  ### _write_manifest(...)

  §9 스키마 기반.
  random_init_ok: config에 ckpt_path 있는 TextFRCGModelAgent 수 == 0이면 False.
  git_sha: subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()
  hard_checks_all_pass: fake_metric_count==0 AND forbidden_source_assertion=="none_read"
    AND (random_init_ok OR ckpt_paths_all_provided).
    random_init_ok==False이면 hard_checks_all_pass=False지만 run은 계속.

  ### main()

  ```python
  def main():
      args = _parse_args()
      config = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
      # override from CLI
      if args.split:
          config["split"] = args.split
      if args.out_dir:
          config["out_dir"] = args.out_dir
      max_episodes = args.max_episodes  # None means all

      forbidden_paths = config.get("forbidden_sources", [])
      uninstall_guard = _install_forbidden_source_guard(forbidden_paths)
      forbidden_source_assertion = "none_read"

      try:
          dispatch_table = _build_agent_dispatch_table(config)
          _preflight_dry_obs_check(dispatch_table)

          dataset_path = config["dataset_path"]
          split = config.get("split", "test_id")
          seeds = config.get("seeds", [0])
          out_dir = Path(config.get("out_dir", "outputs/runs/p3_lr_real_eval"))
          out_dir.mkdir(parents=True, exist_ok=True)

          runner_config = {
              "seeds": seeds,
              "split": split,
              "metrics": config.get("metrics", []),
              "compute_budget": config.get("compute_budget", {}),
          }
          runner = EvaluationRunner(runner_config)

          all_results = []
          dataset_audit = _audit_dataset(dataset_path)

          for seed in seeds:
              for agent_id, factory in dispatch_table.items():
                  agent = factory()
                  agent.reset()
                  result = runner.run(
                      agent,
                      dataset_path if max_episodes is None else dataset_path,
                      split,
                      seed,
                  )
                  # If max_episodes, we need to limit - handle in loader wrapper
                  all_results.append((agent_id, seed, result))
                  _write_per_step_jsonl(result, agent_id, seed, split, out_dir)
                  _write_per_episode_jsonl(result, agent_id, seed, split, out_dir)

      except RuntimeError as exc:
          if "forbidden source" in str(exc):
              forbidden_source_assertion = "VIOLATION"
              print(f"FORBIDDEN SOURCE VIOLATION: {exc}", file=sys.stderr)
              sys.exit(1)
          raise
      finally:
          uninstall_guard()

      metrics_payload = _build_metrics_with_blocked_markers(
          all_results, config, dataset_audit
      )
      _write_manifest(config, out_dir, metrics_payload, forbidden_source_assertion, dataset_audit)
      (out_dir / "metrics.json").write_text(
          json.dumps(metrics_payload, indent=2), encoding="utf-8"
      )
      print(f"OK: {out_dir / 'metrics.json'}")
  ```

  ### --max-episodes 지원

  argparse에 --max-episodes INT 인자 추가.
  EvaluationRunner.run()은 dataset을 통째로 로드하므로,
  max_episodes가 지정된 경우 JSONL에서 상위 max_episodes 라인만 임시 파일에 써서
  그 경로를 runner.run()에 전달. (tmpfile: tempfile.NamedTemporaryFile, text mode)

  ## C. tests/test_lr_real_eval_runner.py

  다음 14개 테스트를 구현한다.
  pytest 표준. 각 테스트는 독립적으로 실행 가능해야 한다.

  ### Fixture: _synthetic_episode(with_recovery_ts=True, with_confidence=True)

  test_eval_runner.py의 _episode() helper를 참고하여 JSONL 형식 episode를 생성.
  with_recovery_ts=False: eval_labels에서 recovery_timestamp 제거 (None 대신 키 자체 없음).
  with_confidence=False: step에서 selected_hypothesis_confidence 제거.
  tmpdir에 .jsonl 형태로 저장 후 경로 반환.

  ### Test 1: test_loads_config_without_error
  ```python
  def test_loads_config_without_error(tmp_path):
      # configs/lr_eval_real.yaml가 로드 가능한지 확인
      import yaml
      cfg = yaml.safe_load(Path("configs/lr_eval_real.yaml").read_text(encoding="utf-8"))
      assert cfg["run_mode"] == "real_episode_eval"
      assert "agents" in cfg
  ```

  ### Test 2: test_dispatch_table_contains_all_required_agent_ids
  ```python
  REQUIRED_AGENT_IDS = [
      "FRCG-LR", "ABL-017", "ABL-022", "ABL-023",
      "BASE-006", "BASE-012-CATTS", "BASE-015",
      "BASE-026", "BASE-027", "BASE-028", "BASE-003+008-VLAA",
  ]
  def test_dispatch_table_contains_all_required_agent_ids():
      import yaml
      cfg = yaml.safe_load(Path("configs/lr_eval_real.yaml").read_text(encoding="utf-8"))
      table = _build_agent_dispatch_table(cfg)
      for aid in REQUIRED_AGENT_IDS:
          assert aid in table, f"Missing agent: {aid}"
  ```

  ### Test 3: test_frcg_full_and_frcg_lr_alias_resolve_to_same_class
  ```python
  def test_frcg_full_and_frcg_lr_alias_resolve_to_same_class():
      import yaml
      cfg = yaml.safe_load(Path("configs/lr_eval_real.yaml").read_text(encoding="utf-8"))
      table = _build_agent_dispatch_table(cfg)
      agent = table["FRCG-LR"]()
      assert isinstance(agent, TextFRCGModelAgent)
      assert agent.baseline_id == "FRCG-FULL"
  ```

  ### Test 4: test_runner_calls_agent_act_at_least_once
  stub agent 구현 (call counter 보유).
  ```python
  class StubAgent:
      baseline_id = "STUB"
      call_count = 0
      last_predicted_wrong = False
      last_wrong_prob = 0.5
      def act(self, obs, eval_labels=None):
          self.call_count += 1
          from frcgw.evaluation.baselines import _noop_action
          from frcgw.evaluation.compute_budget import ComputeBudgetLog
          return _noop_action(), ComputeBudgetLog(0,0,0,0,0.0)
      def reset(self): self.call_count = 0

  def test_runner_calls_agent_act_at_least_once(tmp_path):
      # 1 episode, 3 steps JSONL 생성
      dataset = _write_minimal_jsonl(tmp_path, n_episodes=1, n_steps=3)
      runner = EvaluationRunner({"metrics": ["task_success_rate"]})
      agent = StubAgent()
      runner.run(agent, dataset, "test_id", seed=0)
      assert agent.call_count >= 1
  ```

  ### Test 5: test_runner_passes_public_observation_only
  forbidden field가 public_observation에 있으면 assert_no_hidden_labels_in_input이 AssertionError 발생.
  ```python
  def test_runner_passes_public_observation_only(tmp_path):
      # step에 forbidden field를 public_observation에 주입
      episode = {
          "episode_id": "ep0",
          "steps": [{
              "step_index": 0,
              "public_input": {
                  "instruction": "test",
                  "true_wrong_hypothesis": True,  # FORBIDDEN KEY
                  "candidate_actions_public": [],
              },
              "eval_labels": {},
              "targets": {}
          }]
      }
      jsonl_path = tmp_path / "bad.jsonl"
      jsonl_path.write_text(json.dumps(episode) + "\n", encoding="utf-8")
      runner = EvaluationRunner({"metrics": ["task_success_rate"]})
      agent = StubAgent()
      with pytest.raises(AssertionError):
          runner.run(agent, jsonl_path, "test_id", seed=0)
  ```

  ### Test 6: test_runner_does_not_read_p3_lr_smoke
  ```python
  def test_runner_does_not_read_p3_lr_smoke(tmp_path):
      forbidden = [str(tmp_path / "fake_smoke_metrics.json")]
      # guard 설치 후 직접 해당 경로 open 시도 → RuntimeError
      uninstall = _install_forbidden_source_guard(forbidden)
      try:
          with pytest.raises(RuntimeError, match="forbidden source"):
              open(forbidden[0])
      finally:
          uninstall()
  ```

  ### Test 7: test_runner_does_not_read_p3_ablations
  ```python
  def test_runner_does_not_read_p3_ablations(tmp_path):
      forbidden = [str(tmp_path / "fake_ablation_results.json")]
      uninstall = _install_forbidden_source_guard(forbidden)
      try:
          with pytest.raises(RuntimeError, match="forbidden source"):
              Path(forbidden[0]).read_text(encoding="utf-8")
      finally:
          uninstall()
  ```

  ### Test 8: test_runner_does_not_read_p3_lr_eval_metrics
  ```python
  def test_runner_does_not_read_p3_lr_eval_metrics(tmp_path):
      forbidden = [str(tmp_path / "fake_lr_eval_metrics.json")]
      uninstall = _install_forbidden_source_guard(forbidden)
      try:
          (tmp_path / "fake_lr_eval_metrics.json").write_text("{}", encoding="utf-8")
          with pytest.raises(RuntimeError, match="forbidden source"):
              with open(forbidden[0]) as f:
                  _ = f.read()
      finally:
          uninstall()
  ```

  ### Test 9: test_predicted_wrong_equals_agent_last_predicted_wrong
  ```python
  class CyclingStubAgent:
      baseline_id = "CYCLING"
      last_wrong_prob = 0.9
      _cycle = [True, False, True]
      _idx = 0
      @property
      def last_predicted_wrong(self):
          v = self._cycle[self._idx % 3]; self._idx += 1; return v
      def act(self, obs, eval_labels=None):
          from frcgw.evaluation.baselines import _noop_action
          from frcgw.evaluation.compute_budget import ComputeBudgetLog
          return _noop_action(), ComputeBudgetLog(0,0,0,0,0.0)
      def reset(self): self._idx = 0

  def test_predicted_wrong_equals_agent_last_predicted_wrong(tmp_path):
      # 3-step episode → per_step records の predicted_wrong matches agent's property
      # (tests the runner wiring, not the per-step writer which is in 10_run_lr_real_eval.py)
      # Use eval_runner directly to verify predicted_wrong is read from agent.last_predicted_wrong
      dataset = _write_minimal_jsonl(tmp_path, n_episodes=1, n_steps=3)
      runner = EvaluationRunner({"metrics": ["task_success_rate"]})
      agent = CyclingStubAgent()
      result = runner.run(agent, dataset, "test_id", seed=0)
      steps = result.metrics  # EvaluationResult.metrics doesn't have per_step; check differently
      # Instead: call runner.run, capture per-step via a stub that records predicted_wrong
      # Assert that at least one step had predicted_wrong=True (from cycle)
      # Since eval_runner records from agent.last_predicted_wrong, verify the result was non-trivial
      assert result.n_episodes == 1
  ```
  注: EvaluationRunner.run()이 step_results에 predicted_wrong를 기록하지만
  EvaluationResult에는 노출되지 않는다. 이 테스트는 runner가 agent.last_predicted_wrong를
  읽는다는 것 확인을 위해 monkeypatch로 step_results를 캡처하거나,
  per_step JSONL writer를 통해 검증하는 방식으로 구현.
  가장 단순한 방법: 10_run_lr_real_eval.py의 _write_per_step_jsonl을 직접 호출하여
  기록된 predicted_wrong 값이 agent.last_predicted_wrong와 일치하는지 확인.

  구체적 구현:
  ```python
  def test_predicted_wrong_equals_agent_last_predicted_wrong(tmp_path):
      dataset = _write_minimal_jsonl(tmp_path, n_episodes=1, n_steps=2)
      runner = EvaluationRunner({"metrics": ["task_success_rate"]})
      class RecordingAgent:
          baseline_id = "REC"
          last_wrong_prob = 0.9
          last_F_t = 0.0
          last_predicted_wrong = True  # fixed True
          def act(self, obs, eval_labels=None):
              from frcgw.evaluation.baselines import _noop_action
              from frcgw.evaluation.compute_budget import ComputeBudgetLog
              return _noop_action(), ComputeBudgetLog(0,0,0,0,0.0)
          def reset(self): pass
      agent = RecordingAgent()
      result = runner.run(agent, dataset, "test_id", seed=0)
      # eval_runner reads agent.last_predicted_wrong → step_result["predicted_wrong"]
      # We can verify by directly inspecting that _write_per_step_jsonl produces correct output
      out_dir = tmp_path / "out"
      out_dir.mkdir()
      _write_per_step_jsonl(result, "REC", 0, "test_id", out_dir)
      lines = (out_dir / "per_step" / "REC_seed0.jsonl").read_text().splitlines()
      for line in lines:
          record = json.loads(line)
          assert record["predicted_wrong"] is True
  ```

  ### Test 10: test_predicted_wrong_threshold_documented_in_contract
  ```python
  def test_predicted_wrong_threshold_documented_in_contract():
      contract_path = Path("docs/orchestration/lr_alignment/18_real_eval_runner_contract.md")
      text = contract_path.read_text(encoding="utf-8")
      assert "confidence_threshold" in text
      assert "placeholder" in text.lower()
      assert "STEP 3" in text
  ```

  ### Test 11: test_missing_recovery_timestamp_marks_C3_blocked
  ```python
  def test_missing_recovery_timestamp_marks_C3_blocked(tmp_path):
      # synthetic dataset with no recovery_timestamp in any eval_label
      dataset = _write_minimal_jsonl(tmp_path, n_episodes=2, n_steps=3, recovery_ts=None)
      runner = EvaluationRunner({"metrics": ["recovery_delay"]})
      agent = StubAgent()
      result = runner.run(agent, dataset, "test_id", seed=0)
      # Now call _build_metrics_with_blocked_markers directly
      dataset_audit = {"recovery_timestamp_coverage": 0, "hypothesis_update_timestamp_coverage": 0,
                       "selected_hypothesis_confidence_coverage": 0, "counterfactual_coverage": 0,
                       "ood_split_exists": False, "total_episodes_sampled": 2}
      all_results = [("STUB", 0, result)]
      metrics = _build_metrics_with_blocked_markers(all_results, {}, dataset_audit)
      stub_metrics = metrics["agents"]["STUB"]
      # C3_recovery_delay should be BLOCKED
      assert stub_metrics.get("C3_recovery_delay", {}).get("status", "").startswith("BLOCKED")
      assert stub_metrics.get("C3_recovery_delay", {}).get("value") is None
  ```

  ### Test 12: test_missing_confidence_marks_C5_calibration_blocked_not_fake
  ```python
  def test_missing_confidence_marks_C5_calibration_blocked_not_fake(tmp_path):
      dataset = _write_minimal_jsonl(tmp_path, n_episodes=2, n_steps=3)
      runner = EvaluationRunner({"metrics": ["falsification_calibration"]})
      agent = StubAgent()
      result = runner.run(agent, dataset, "test_id", seed=0)
      dataset_audit = {"recovery_timestamp_coverage": 0, "hypothesis_update_timestamp_coverage": 0,
                       "selected_hypothesis_confidence_coverage": 0, "counterfactual_coverage": 0,
                       "ood_split_exists": False, "total_episodes_sampled": 2}
      all_results = [("STUB", 0, result)]
      metrics = _build_metrics_with_blocked_markers(all_results, {}, dataset_audit)
      # Check C5 calibration ECE is BLOCKED
      stub_m = metrics["agents"]["STUB"]
      c5 = stub_m.get("C5_calibration_ece", {})
      assert c5.get("status", "").startswith("BLOCKED"), f"Expected BLOCKED, got: {c5}"
      assert c5.get("value") is None, f"Expected null value, got: {c5.get('value')}"
      # Check fake_metric_count == 0
      assert metrics["fake_metric_count"] == 0
  ```

  ### Test 13: test_manifest_records_source_artifacts_used
  ```python
  def test_manifest_records_source_artifacts_used(tmp_path):
      dataset = _write_minimal_jsonl(tmp_path, n_episodes=1, n_steps=2)
      config = {
          "dataset_path": str(dataset),
          "split": "test_id",
          "seeds": [0],
          "agents": [{"id": "BASE-015", "class": "ComputeMatchedRandomAgent"}],
          "metrics": ["task_success_rate"],
          "forbidden_sources": [],
      }
      # Run minimal main-style flow
      dispatch = _build_agent_dispatch_table(config)
      runner = EvaluationRunner({"metrics": ["task_success_rate"]})
      results = [(aid, 0, runner.run(f(), str(dataset), "test_id", 0))
                 for aid, f in dispatch.items()]
      dataset_audit = {"recovery_timestamp_coverage": 0, "hypothesis_update_timestamp_coverage": 0,
                       "selected_hypothesis_confidence_coverage": 0, "counterfactual_coverage": 0,
                       "ood_split_exists": False, "total_episodes_sampled": 1}
      metrics = _build_metrics_with_blocked_markers(results, config, dataset_audit)
      manifest = _write_manifest(config, tmp_path, metrics, "none_read", dataset_audit, write=False)
      assert manifest["source_artifacts_used"] == [config["dataset_path"]]
      assert "p3_lr_smoke" not in str(manifest["source_artifacts_used"])
  ```
  _write_manifest에 write=False 옵션 추가 (manifest dict 반환만, 파일 미기록).

  ### Test 14: test_manifest_forbidden_source_artifacts_assertion_is_none_read
  ```python
  def test_manifest_forbidden_source_artifacts_assertion_is_none_read(tmp_path):
      config = {
          "dataset_path": "data/frcgw_text/v0_1/test_id.jsonl",
          "split": "test_id",
          "seeds": [0],
          "agents": [],
          "metrics": [],
          "forbidden_sources": [
              "outputs/runs/p3_lr_smoke/metrics.json",
              "outputs/runs/p3_ablations/ablation_results.json",
              "outputs/runs/p3_lr_eval/metrics.json",
          ],
      }
      dataset_audit = {"recovery_timestamp_coverage": 0, "hypothesis_update_timestamp_coverage": 0,
                       "selected_hypothesis_confidence_coverage": 0, "counterfactual_coverage": 0,
                       "ood_split_exists": False, "total_episodes_sampled": 0}
      metrics = {"agents": {}, "fake_metric_count": 0, "blocked_metric_count": 0,
                 "hard_checks_all_pass": True}
      manifest = _write_manifest(config, tmp_path, metrics, "none_read", dataset_audit, write=False)
      assert manifest["forbidden_source_assertion"] == "none_read"
      assert len(manifest["forbidden_source_artifacts"]) == 3
  ```

REQUIRED_TESTS:
  tests/test_lr_real_eval_runner.py の 14개 테스트 모두 green.
  pytest tests/test_lr_real_eval_runner.py -q

ACCEPTANCE_CRITERIA:
  1. pytest tests/test_lr_real_eval_runner.py -q → 14 passed, 0 failed
  2. python scripts/10_run_lr_real_eval.py --config configs/lr_eval_real.yaml --split test_id --max-episodes 3 --out-dir outputs/runs/p3_lr_real_eval_smoke
     exit code 0
  3. outputs/runs/p3_lr_real_eval_smoke/manifest.json 존재
     manifest["forbidden_source_assertion"] == "none_read"
     manifest["source_artifacts_used"] == ["data/frcgw_text/v0_1/test_id.jsonl"]
  4. outputs/runs/p3_lr_real_eval_smoke/metrics.json["fake_metric_count"] == 0
  5. BLOCKED metric 무결성:
     모든 BLOCKED status를 가진 metric의 "value"가 JSON null (Python None)
  6. outputs/runs/p3_lr_real_eval_smoke/per_step/ 에 .jsonl 파일 존재, line count > 0
  7. outputs/runs/p3_lr_real_eval_smoke/per_episode/ 에 .jsonl 파일 존재, line count > 0
  8. FILES_FORBIDDEN에 열거된 경로 미수정 (git diff --cached --name-only 확인)

COMMIT_MESSAGE: "feat(eval): add real episode-level eval runner (P3_LR_REAL_EVAL contract)"

STOP_CONDITION:
  다음 중 하나라도 발생하면 즉시 중단하고 RESULT.md에 BLOCKED 표시:
  - FILES_FORBIDDEN 경로 수정 시도
  - 14 테스트 중 하나라도 red
  - fake_metric_count > 0
  - forbidden_source_assertion != "none_read"
  - BLOCKED metric에 null이 아닌 numeric value 기록
  - _without_none() 호출이 BLOCKED metric에 적용되는 경우

RELATED_AGENT_REPORT_IDS:
  - T2-experiment-design-expander: docs/orchestration/agent_reports/2026-05/experiment_design_step2_real_eval_runner_T2.md (TBD after PHASE E T3)
  - T2-feasibility-auditor: docs/orchestration/agent_reports/2026-05/feasibility_step2_real_eval_runner_T2.md (TBD)
  - T3-impl-risk (필수 before merge): docs/orchestration/agent_reports/2026-05/impl_risk_step2_real_eval_runner_R1.md (TBD)
