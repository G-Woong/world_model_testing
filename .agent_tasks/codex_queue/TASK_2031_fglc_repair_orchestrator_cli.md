TASK_NAME: fglc_repair_orchestrator_cli

BACKGROUND: |
  docs/EXPERIMENT_REPAIR_LOOP_PLAN.md §G Step 8 = closed-loop repair harness의
  연결판(control plane). Step 5(taxonomy) + Step 6(compare, ledger) +
  Step 7(diagnose, candidates, ranker)을 하나의 dry-run loop로 묶는다.
  실제 학습/평가 실행은 Step 9 이후. Step 8은 mock metric으로 흐름 제어만 검증.

  기존 모듈 인터페이스 (수정 절대 금지):
  - ledger.py: REQUIRED_KEYS(19개), validate_ledger_line(), compute_config_hash(),
    build_loop_id(), build_run_id(), append_ledger_line(). 디렉터리 자동 생성 안 함.
  - compare.py: compare_metrics() → dict (dataclass 아님), MetricDirection enum.
  - diagnose.py: diagnose(metrics, phase) -> list[FailureCauseId]
  - candidates.py: candidates_for(causes, phase) -> list[RepairCandidate]
  - ranker.py: rank(candidates) -> list[RankedCandidate]
  - taxonomy.py: FailureCauseId, CAUSE_METADATA, DETECTION_THRESHOLDS,
    applicable_phases_for

GOAL: |
  Create dry-run orchestrator + CLI:

  src/fglc/repair/orchestrator.py
    - Dataclasses (frozen where appropriate):
        RepairLoopConfig(phase, config_path, split, seed, descriptor, max_iter,
          max_wall_clock_minutes, max_consecutive_inconclusive, dry_run, output_root,
          metric_directions, gate_thresholds, failed_metric)
        RepairLoopState(loop_id, iter=0, metrics_before={}, metrics_after={},
          consecutive_inconclusive=0, total_wall_clock_minutes=0.0,
          stop_condition_hit=None)
        RepairIterationResult(ledger_line, diagnosed_causes, ranked_candidates,
          chosen_candidate, compare_result, stop_condition_hit, next_action)
        RunnerOutput(metrics, wall_clock_minutes, vram_peak_mib,
          hook_blocked=False, hook_reason=None)
    - Protocol: RepairRunner.__call__(*, phase, config_path, split, seed, descriptor,
        patch, iter_index) -> RunnerOutput
    - run_repair_loop(cfg, *, runner, now=None, git_sha_fn=None) -> list[RepairIterationResult]
    - git_sha() -> str  (subprocess + fallback "unknown")

  scripts/fglc/repair_loop.py
    - build_mock_runner(scenario, *, failed_metric) — 7 scenarios
    - main(argv: list[str] | None = None) -> int (exit 0/1/2)

  configs/fglc/smoke_4060.yaml   (dummy — yaml parse 안 함, hash 용)
  outputs/repair/.gitkeep        (empty marker)
  tests/test_fglc_repair_orchestrator.py  (>=8 tests, 5 stop conditions all covered)
  tests/test_fglc_repair_loop_cli.py      (>=4 tests)
  src/fglc/repair/__init__.py    (orchestrator 4 API 추가만)
  .gitignore                     (!outputs/repair/.gitkeep 한 줄 추가만)

  Touch nothing else. 기존 6개 모듈 파일(taxonomy/compare/ledger/diagnose/
  candidates/ranker) 1바이트도 수정 금지.

FILES_ALLOWED:
  - src/fglc/repair/orchestrator.py
  - scripts/fglc/repair_loop.py
  - configs/fglc/smoke_4060.yaml
  - outputs/repair/.gitkeep
  - tests/test_fglc_repair_orchestrator.py
  - tests/test_fglc_repair_loop_cli.py
  - src/fglc/repair/__init__.py
  - .gitignore
  - .agent_tasks/codex_done/TASK_2026_05_23_fglc_repair_orchestrator_cli_RESULT.md

FILES_FORBIDDEN:
  - src/fglc/repair/taxonomy.py
  - src/fglc/repair/compare.py
  - src/fglc/repair/ledger.py
  - src/fglc/repair/diagnose.py
  - src/fglc/repair/candidates.py
  - src/fglc/repair/ranker.py
  - src/fglc/schemas/
  - .claude/
  - CLAUDE.md
  - docs/
  - scripts/run_codex_task.ps1
  - outputs/phase_gates/
  - outputs/repair/  (제외: .gitkeep만 허용)
  - any R*.passed / P*.passed sentinel

REQUIRED_IMPLEMENTATION: |
  Step 1: Read docs/EXPERIMENT_REPAIR_LOOP_PLAN.md §G Step 8 (dry-run loop 흐름).
  Step 2: Read src/fglc/repair/{taxonomy,compare,ledger,diagnose,candidates,ranker}.py
          for verbatim function signatures. Do NOT modify these files.

  Step 3: Implement src/fglc/repair/orchestrator.py per the following spec:

  3a. Dataclasses + Protocol (verbatim):
      @dataclass(frozen=True)
      class RepairLoopConfig:
          phase: str
          config_path: Path
          split: str
          seed: int
          descriptor: str
          max_iter: int
          max_wall_clock_minutes: float
          max_consecutive_inconclusive: int
          dry_run: bool
          output_root: Path
          metric_directions: Mapping[str, str]
          gate_thresholds: Mapping[str, float]
          failed_metric: str

      @dataclass
      class RepairLoopState:
          loop_id: str
          iter: int = 0
          metrics_before: dict = field(default_factory=dict)
          metrics_after: dict = field(default_factory=dict)
          consecutive_inconclusive: int = 0
          total_wall_clock_minutes: float = 0.0
          stop_condition_hit: str | None = None

      @dataclass(frozen=True)
      class RepairIterationResult:
          ledger_line: dict
          diagnosed_causes: tuple
          ranked_candidates: tuple
          chosen_candidate: Any
          compare_result: dict | None
          stop_condition_hit: str | None
          next_action: str

      @dataclass(frozen=True)
      class RunnerOutput:
          metrics: dict
          wall_clock_minutes: float
          vram_peak_mib: float
          hook_blocked: bool = False
          hook_reason: str | None = None

      class RepairRunner(Protocol):
          def __call__(self, *, phase, config_path, split, seed, descriptor,
                       patch, iter_index) -> RunnerOutput: ...

  3b. git_sha() helper:
      def git_sha() -> str:
          try:
              r = subprocess.run(["git","rev-parse","HEAD"],
                                 capture_output=True, text=True, check=True, timeout=5.0)
              return r.stdout.strip() or "unknown"
          except (subprocess.CalledProcessError, FileNotFoundError,
                  subprocess.TimeoutExpired):
              return "unknown"

  3c. _hash_config(path: Path) -> str:
      if path.exists():
          return compute_config_hash(path)          # Path branch -> read_bytes
      return compute_config_hash(f"<missing:{path.as_posix()}>")  # str fallback

  3d. run_repair_loop(cfg, *, runner, now=None, git_sha_fn=None) -> list:

      CRITICAL: output_root.mkdir(parents=True, exist_ok=True) MUST be called
      BEFORE any ledger write. This is the orchestrator's responsibility —
      ledger.py does NOT create directories.

      loop_id = build_loop_id(now() if now else None)
      config_hash = _hash_config(cfg.config_path)
      ledger_path = cfg.output_root / f"{loop_id}.jsonl"
      cfg.output_root.mkdir(parents=True, exist_ok=True)   # <-- REQUIRED HERE

      sha = git_sha_fn() if git_sha_fn else git_sha()

      # Step 1: baseline run (iter_index=0)
      baseline = runner(phase=cfg.phase, config_path=cfg.config_path,
                        split=cfg.split, seed=cfg.seed, descriptor=cfg.descriptor,
                        patch=None, iter_index=0)

      if baseline.hook_blocked:
          line = _build_baseline_hook_blocked_ledger(loop_id, cfg, config_hash,
                                                     sha, baseline)
          append_ledger_line(ledger_path, line)
          return [RepairIterationResult(ledger_line=line, ...)]

      # CRITICAL: state.metrics_before MUST be initialized to baseline.metrics
      # before the main for-loop. NOT {}. This is required for target_reached check.
      state = RepairLoopState(loop_id=loop_id)
      state_metrics_before = dict(baseline.metrics)  # mutable copy
      total_wall_clock = baseline.wall_clock_minutes
      consecutive_inconclusive = 0
      results = []

      for iter_index in range(1, cfg.max_iter + 1):
          # (1) target_reached check FIRST (uses metrics_before from previous iter)
          # Use .get() with None to avoid KeyError on missing failed_metric key
          cur_val = state_metrics_before.get(cfg.failed_metric)
          if cur_val is not None and _gate_passed(cur_val, cfg):
              line = _build_accept_target_reached_ledger(...)
              append_ledger_line(ledger_path, line)
              results.append(RepairIterationResult(..., stop_condition_hit="target_reached"))
              return results

          # (2) diagnose -> candidates -> rank
          causes = diagnose(state_metrics_before, cfg.phase)
          cands = candidates_for(causes, cfg.phase)

          # (3) chosen=None path: empty or IMPLEMENTATION_BUG_SUSPECTED-only
          if not cands or _is_sentinel_only(cands):
              line = _build_no_candidate_ledger(...)
              append_ledger_line(ledger_path, line)
              results.append(RepairIterationResult(..., stop_condition_hit="hook_blocked",
                                                   next_action="escalate_to_user"))
              return results

          ranked = rank(cands)
          chosen = ranked[0].candidate

          # (4) retest with patch
          out = runner(patch=chosen.patch, iter_index=iter_index, ...)
          if out.hook_blocked:
              line = _build_hook_blocked_mid_ledger(...)
              append_ledger_line(ledger_path, line)
              results.append(RepairIterationResult(..., stop_condition_hit="hook_blocked"))
              return results

          total_wall_clock += out.wall_clock_minutes
          metrics_after = dict(out.metrics)

          # (5) compare
          cmp = compare_metrics(state_metrics_before, metrics_after,
                                cfg.failed_metric, cfg.metric_directions)

          # (6) stop condition evaluation (priority order):
          # hook_blocked (already handled above)
          # target_reached (checked at next iter start)
          # wall_clock
          # consecutive_inconclusive
          # max_iter

          # Update consecutive_inconclusive for current iter
          if cmp["result"] == "inconclusive":
              consecutive_inconclusive += 1
          else:
              consecutive_inconclusive = 0

          stop = None
          if total_wall_clock >= cfg.max_wall_clock_minutes:
              stop = "wall_clock"
          elif consecutive_inconclusive >= cfg.max_consecutive_inconclusive:
              stop = "consecutive_inconclusive"
          elif iter_index == cfg.max_iter:
              stop = "max_iter"

          # (7) build and write ledger line
          run_id = build_run_id(cfg.phase, cfg.descriptor, cfg.seed,
                                {"split": cfg.split, "iter": iter_index})
          line = {
              "loop_id": loop_id,
              "iter": iter_index,
              "run_id": run_id,
              "git_sha": sha,
              "config_hash": config_hash,
              "config_path": str(cfg.config_path),
              "phase": cfg.phase,
              "split": cfg.split,
              "metrics_before": dict(state_metrics_before),
              "metrics_after": metrics_after,
              "deltas": cmp["deltas"],
              "failed_metric": cfg.failed_metric,
              "diagnosed_cause": [{"cause_id": c.value,
                                   "rationale": f"diagnose@{cfg.phase}"}
                                  for c in causes],
              "candidate_chosen": {
                  "id": chosen.id,
                  "patch": dict(chosen.patch),
                  "cost_minutes": chosen.cost_minutes,
                  "risk": chosen.risk,
                  "expected_signal": chosen.expected_signal,
                  "rank": 1,
              },
              "result": cmp["result"],
              "stop_condition_hit": stop,
              "next_action": _next_action(cmp["result"], stop),
              "wall_clock_minutes": out.wall_clock_minutes,
              "vram_peak_mib": out.vram_peak_mib,
          }
          append_ledger_line(ledger_path, line)

          result = RepairIterationResult(
              ledger_line=line,
              diagnosed_causes=tuple(causes),
              ranked_candidates=tuple(ranked),
              chosen_candidate=chosen,
              compare_result=cmp,
              stop_condition_hit=stop,
              next_action=line["next_action"],
          )
          results.append(result)

          # (8) state update
          if cmp["result"] == "accept":
              state_metrics_before = metrics_after

          if stop:
              return results

      return results

  3e. _next_action(result, stop) mapping:
      accept (no stop) -> "continue_or_next_phase"
      reject (no stop) -> "try_next_candidate"
      inconclusive (no stop) -> "increase_signal_or_eval"
      hook_blocked -> "escalate_to_user"
      target_reached -> "stop_target_reached"
      wall_clock -> "stop_wall_clock"
      consecutive_inconclusive -> "stop_consecutive_inconclusive"
      max_iter -> "stop_max_iter"

  3f. _gate_passed(value, cfg) for target_reached:
      direction = cfg.metric_directions.get(cfg.failed_metric, "lower_better")
      threshold = cfg.gate_thresholds.get(cfg.failed_metric)
      if threshold is None: return False
      if "lower" in direction: return value <= threshold
      return value >= threshold

  3g. _is_sentinel_only(cands):
      return (len(cands) == 1 and
              cands[0].cause_id == FailureCauseId.IMPLEMENTATION_BUG_SUSPECTED)

  Step 4: Implement scripts/fglc/repair_loop.py:

  4a. 13 CLI arguments:
      --phase         str, required, choices=[R2,R3,R4,R5,R6,R7]
      --config        Path, required
      --split         str, default="val", choices=[val,test,id,ood]
      --seed          int, default=0
      --descriptor    str, required
      --failed-metric str, default=None (auto from phase via _default_failed_metric)
      --max-iter      int, default=3
      --max-wall-clock-minutes float, default=60.0
      --max-consecutive-inconclusive int, default=2
      --output-root   Path, default="outputs/repair"
      --dry-run       store_true (default behavior — DO NOT add --no-dry-run)
      --mock-scenario str, default="improve",
                      choices=[improve,reject,inconclusive,target_reached,
                               max_iter,hook_blocked,no_candidate]

  4b. _default_failed_metric(phase):
      return {"R2": "ood_auroc", "R3": "id_nll", "R4": "ood_auroc",
              "R5": "attention_entropy", "R6": "corrected_nll_gain",
              "R7": "planner_return_gain"}[phase]

  4c. build_mock_runner(scenario, *, failed_metric) -> RepairRunner:
      Returns a callable matching RepairRunner Protocol. patch arg is ignored.
      Scenarios (R3 default, failed_metric="id_nll" LOWER_BETTER):

      improve:        iter0 id_nll=0.80 ood_auroc=0.70
                      iter1+ id_nll=0.70 ood_auroc=0.75 (accept: delta=0.10>=eps)
      reject:         iter0 id_nll=0.80 ood_auroc=0.70
                      iter1+ id_nll=0.82 ood_auroc=0.68 (reject: delta=-0.02<=0)
      inconclusive:   iter0 id_nll=0.80 ood_auroc=0.70
                      iterN id_nll=0.80-(N*0.01) ood_auroc=0.70 (small → inconclusive)
      target_reached: iter0 id_nll=0.30 ood_auroc=0.90 (gate=0.4 → target_reached at iter1 start)
      max_iter:       all iters id_nll=0.80 ood_auroc=0.70 (reject every time)
      hook_blocked:   iter0 (baseline): RunnerOutput(metrics={}, wall_clock_minutes=0.0,
                      vram_peak_mib=0.0, hook_blocked=True, hook_reason="test_hook")
      no_candidate:   all iters id_nll=0.45 ood_auroc=0.90 (no DETECTION_THRESHOLDS
                      fire → diagnose=[IMPLEMENTATION_BUG_SUSPECTED] → sentinel only)
                      wall_clock_minutes=0.1, vram_peak_mib=100.0 per iter

      All scenarios provide wall_clock_minutes=0.1, vram_peak_mib=100.0 unless overridden.
      Store scenario metrics in closure constants dict — do NOT use random numbers.

  4d. main(argv=None) -> int:
      try:
          ns = _parser().parse_args(argv)
      except SystemExit as e:
          return int(e.code) if isinstance(e.code, int) else 2
      try:
          cfg = _build_config(ns)
          runner = build_mock_runner(ns.mock_scenario, failed_metric=cfg.failed_metric)
          results = run_repair_loop(cfg, runner=runner)
          final = results[-1]
          print(json.dumps({
              "loop_id": final.ledger_line["loop_id"],
              "final_result": final.ledger_line["result"],
              "stop_condition_hit": final.ledger_line["stop_condition_hit"],
              "ledger_path": str(cfg.output_root / f"{final.ledger_line['loop_id']}.jsonl"),
              "next_action": final.ledger_line["next_action"],
          }))
          return 0
      except ValueError as e:
          print(f"ERROR config: {e}", file=sys.stderr); return 2
      except Exception as e:
          print(f"ERROR internal: {e}", file=sys.stderr); return 1

  Step 5: configs/fglc/smoke_4060.yaml (minimal, NOT parsed by orchestrator):
      phase: R3
      seed: 0
      K: 4
      d: 32
      h: 64
      batch_size: 32

  Step 6: outputs/repair/.gitkeep — create empty file.

  Step 7: .gitignore — add ONLY this one line at end of file (preserve existing content):
      !outputs/repair/.gitkeep

  Step 8: src/fglc/repair/__init__.py — add ONLY these imports (no other changes):
      from fglc.repair.orchestrator import (
          run_repair_loop,
          RepairLoopConfig,
          RepairLoopState,
          RepairIterationResult,
      )
      Update __all__ to include these 4 names.
      Do NOT remove or change existing imports (taxonomy exports etc).

  Step 9: Import policy for orchestrator.py and repair_loop.py:
      ONLY: stdlib (subprocess, datetime, json, sys, pathlib, dataclasses, typing) +
            fglc.repair.{taxonomy,compare,candidates,ranker,diagnose,ledger}
      NO external deps beyond filelock (already in ledger.py).
      NO torch, NO maniskill, NO numpy import.

REQUIRED_TESTS: |
  Run command (use python -m pytest, NOT pytest.exe which is broken):
  .venv\Scripts\python.exe -m pytest -q tests\test_fglc_repair_orchestrator.py tests\test_fglc_repair_loop_cli.py

  Test file 1: tests/test_fglc_repair_orchestrator.py (>=8 tests)

  CRITICAL TEST REQUIREMENT: ALL orchestrator tests MUST use
  output_root=tmp_path / "repair_subdir"  (a non-existent subdirectory)
  NOT tmp_path directly. This verifies mkdir(parents=True, exist_ok=True)
  is called before ledger write.

  CRITICAL TEST REQUIREMENT: ALL orchestrator tests MUST pass
  git_sha_fn=lambda: "abc123" to run_repair_loop() to prevent real subprocess calls.

  Required tests:
  1. test_improve_scenario:
     runner=improve_mock, max_iter=2, output_root=tmp_path/"repair_subdir"
     Assert: results[-1].ledger_line["result"]=="accept"
     Assert: (tmp_path/"repair_subdir").exists()  [mkdir verification]
     Assert: ledger file has 2 lines
     Assert: all lines pass validate_ledger_line()
     Assert: all 19 REQUIRED_KEYS present in each line

  2. test_reject_scenario:
     runner=reject_mock, max_iter=1
     Assert: results[0].ledger_line["result"]=="reject"

  3. test_inconclusive_then_consecutive_stop:
     runner=inconclusive_mock, max_consecutive_inconclusive=2, max_iter=5
     Assert: results[-1].stop_condition_hit=="consecutive_inconclusive"
     Assert: results[-1].ledger_line["result"]=="inconclusive"

  4. test_target_reached_at_iter_start:
     Inject metrics_before with id_nll=0.30 by using target_reached mock runner.
     gate_thresholds={"id_nll": 0.40}, metric_directions={"id_nll": "lower_better"}
     Assert: results[0].stop_condition_hit=="target_reached"
     Assert: results[0].ledger_line["result"]=="accept"
     Assert: results[0].ledger_line["next_action"]=="stop_target_reached"

  5. test_max_iter:
     runner=max_iter_mock (all reject), max_iter=2
     Assert: results[-1].stop_condition_hit=="max_iter"
     Assert: len(results)==2

  6. test_hook_blocked_baseline:
     runner returns hook_blocked=True on iter_index=0
     Assert: len(results)==1
     Assert: results[0].ledger_line["iter"]==0
     Assert: results[0].ledger_line["result"]=="inconclusive"
     Assert: results[0].ledger_line["stop_condition_hit"]=="hook_blocked"
     Assert: results[0].ledger_line["candidate_chosen"]["id"] is None
     Assert: validate_ledger_line(results[0].ledger_line) passes

  7. test_no_candidate_sentinel_only:
     runner=no_candidate_mock (all metrics fine, no threshold fires)
     Assert: results[0].chosen_candidate is None
     Assert: results[0].ledger_line["result"]=="inconclusive"
     Assert: results[0].ledger_line["stop_condition_hit"]=="hook_blocked"
     Assert: results[0].ledger_line["next_action"]=="escalate_to_user"
     Assert: validate_ledger_line(results[0].ledger_line) passes

  8. test_wall_clock_stop:  [REQUIRED — covers 5th stop condition]
     max_wall_clock_minutes=0.001, runner returns wall_clock_minutes=1.0 per iter
     max_iter=5
     Assert: results[-1].stop_condition_hit=="wall_clock"
     Assert: validate_ledger_line(results[-1].ledger_line) passes

  Test file 2: tests/test_fglc_repair_loop_cli.py (>=4 tests)

  1. test_cli_smoke_improve:
     argv=["--phase","R3","--config",str(tmp_yaml),"--descriptor","smoke",
           "--mock-scenario","improve","--max-iter","2",
           "--output-root",str(tmp_path/"out")]
     Assert: main(argv)==0
     Assert: ledger file exists under tmp_path/"out"/...
     Assert: json.loads(stdout) has keys: loop_id, final_result, stop_condition_hit,
             ledger_path, next_action

  2. test_cli_invalid_phase:
     argv=["--phase","BAD","--config","x.yaml","--descriptor","d"]
     Assert: main(argv)==2

  3. test_cli_invalid_failed_metric:
     argv=["--phase","R3","--config","x.yaml","--descriptor","d",
           "--failed-metric","garbage_metric_xyz"]
     Assert: main(argv)==2  [_build_config raises ValueError; unknown metric for phase]

  4. test_cli_internal_exception:
     monkeypatch run_repair_loop to raise RuntimeError("test error")
     Assert: main(argv)==1

ACCEPTANCE_CRITERIA: |
  - Exactly 9 files added/modified (7 new + 2 modified: __init__.py, .gitignore).
    Plus RESULT.md = 10th file.
  - 0 files modified outside FILES_ALLOWED.
  - 기존 6개 모듈(taxonomy/compare/ledger/diagnose/candidates/ranker) 1바이트도 수정 없음.
  - python -m pytest -q tests/test_fglc_repair_orchestrator.py
                              tests/test_fglc_repair_loop_cli.py
    → ALL green, total tests >= 12 (8 orchestrator + 4 CLI).
  - 모든 ledger line이 validate_ledger_line() 통과 (19 REQUIRED_KEYS 모두 존재).
  - 5개 stop_condition_hit 값 모두 최소 1개 테스트에서 발견됨:
    hook_blocked, target_reached, wall_clock, consecutive_inconclusive, max_iter.
  - chosen=None sentinel path (test 7) 가 테스트됨.
  - mkdir(parents=True, exist_ok=True) 검증: test_improve 등에서 비존재 서브디렉터리 사용.
  - No call to real training code. No actual ManiSkill / torch import.
  - `import sys; assert 'torch' not in sys.modules` equivalent — orchestrator.py
    and repair_loop.py MUST NOT import torch/maniskill/numpy.
  - --no-dry-run flag does NOT exist in argparse.
    Passing '--no-dry-run' via argv MUST trigger SystemExit(2) (argparse default).
  - No file writes outside cfg.output_root / tmp_path.
  - No new external deps added (no new packages beyond existing requirements.txt).
  - All orchestrator tests use git_sha_fn=lambda: "abc123" (no real subprocess).
  - All orchestrator tests use output_root=tmp_path/"repair_subdir" (non-existent subdir).

COMMIT_MESSAGE: feat(repair): add orchestrator + CLI dry-run loop (Step 8 control plane)

STOP_CONDITION: |
  Stop immediately after the single commit. One commit only.

  Do NOT implement R3 base WM training runner (Step 9+).
  Do NOT dispatch Codex sub-tasks from inside orchestrator (Step 9+).
  Do NOT add --no-dry-run CLI flag under any circumstances.
  Do NOT modify taxonomy/compare/ledger/diagnose/candidates/ranker logic — 1 byte.
  Do NOT modify docs/idea/ or docs/EXPERIMENT_REPAIR_LOOP_PLAN.md (read-only SSoT).
  Do NOT create R*.passed / P*.passed sentinels.
  Do NOT call subprocess for anything except `git rev-parse HEAD`.
  Do NOT write outside cfg.output_root (or tmp_path in tests).
  Do NOT import torch, maniskill, numpy, or any library not in existing requirements.txt.
  Do NOT add abstractions beyond what the 7 acceptance tests require.

SANDBOX_MODE: bypass

RELATED_AGENT_REPORT_IDS:
  - docs/orchestration/agent_reports/2026-05/impl_risk_fglc_repair_orchestrator_cli_R1.md
