TASK_NAME: TASK_10E_r3_runner_repair_integration
SANDBOX_MODE: bypass

BACKGROUND:
FGLC Step 10E. pytest 179 passed.
완성된 모듈: Encoder, BeliefMemory, GroupedDynamics, RewardHead, ValueHead, TrainerR3, evaluate_model, SyntheticToyDataset, make_dataloaders.

이 TASK의 목적:
(1) src/fglc/runners/r3_runner.py — RepairRunner Protocol 구현 (R3SmokeRunner)
(2) scripts/fglc/r3_smoke.py — real smoke 진입점
(3) scripts/fglc/repair_loop.py — mock/real runner 분기 추가 (CD-4 동반)
(4) src/fglc/repair/orchestrator.py — iter_{N}/ 4종 artifact 생성 (CD-2 동반)
(5) tests/test_fglc_r3_runner_integration.py — 1-iter end-to-end 통합 테스트

핵심 규칙: RepairRunner Protocol (orchestrator.py:74-85) 시그니처를 정확히 구현한다.
"""
def __call__(
    self,
    *,
    phase: str,
    config_path: Path,
    split: str,
    seed: int,
    descriptor: str,
    patch: Mapping[str, Any] | None,
    iter_index: int,
) -> RunnerOutput:
"""

iter_{N}/ 4종 artifact (CD-2):
  loop_dir/iter_{N}/config.yaml    — 적용된 config (patch 반영)
  loop_dir/iter_{N}/metrics.json   — 해당 iteration 결과
  loop_dir/iter_{N}/compare.json   — compare_metrics 결과 (baseline iter에서는 {})
  loop_dir/iter_{N}/run_manifest.json — {iter_index, seed, descriptor, patch, timestamp}

CD-4: scripts/fglc/repair_loop.py:84의 gate_threshold id_nll 0.4 → 0.5.

GOAL:
1. src/fglc/runners/__init__.py 생성 (export: R3SmokeRunner)
2. src/fglc/runners/r3_runner.py 구현 — R3SmokeRunner:
   - __init__(self, base_config_path: Path, output_root: Path = Path("outputs/repair"))
   - __call__(...) -> RunnerOutput:
     (a) load config via yaml.safe_load(base_config_path)
     (b) apply patch (deep merge: patch keys override config top-level or nested keys)
     (c) seed 설정: torch.manual_seed(seed), numpy rng
     (d) make_dataloaders(config) → 4 split DataLoaders
     (e) device = config.get("device", "cpu"); fallback to "cpu" if cuda unavailable
     (f) torch.cuda.set_per_process_memory_fraction(0.85) if cuda
     (g) trainer = TrainerR3(config["model"], TrainerConfig(...), device)
     (h) trainer.train(train_loader, val_loader) → train metrics
     (i) metrics = evaluate_model(trainer, dataloaders, config["model"], trainer_config) → dict
     (j) iter_dir = output_root / loop_id_placeholder / f"iter_{iter_index}"  (dir 생성)
         단, R3SmokeRunner는 loop_id를 모른다 (orchestrator가 관리). 따라서:
         iter_artifact_dir를 __call__의 keyword 인자로 받거나,
         또는 output_root / f"tmp_iter_{iter_index}" 로 기록하고
         orchestrator에서 나중에 loop_dir/iter_{iter_index}/로 이동한다.
         — 권장: orchestrator가 iter_artifact_dir를 직접 생성하여 runner에게 전달 (§ 3번 참조)
     (k) metrics.json, config.yaml, run_manifest.json 저장
     (l) vram_peak_mib = torch.cuda.max_memory_allocated() / 1024**2 if cuda else 0.0
     (m) return RunnerOutput(metrics=metrics, wall_clock_minutes=..., vram_peak_mib=vram_peak_mib)
   - docstring: "Source: docs/idea/04_BASE_WORLD_MODEL.md, docs/ROADMAP/04_PHASE_R3_BASE_WORLD_MODEL.md"

3. src/fglc/repair/orchestrator.py 수정 — iter_{N}/ artifact 생성 (CD-2):
   - run_repair_loop 내부에서 runner 호출 직후 iter_dir = loop_dir / f"iter_{iter_index}"를 생성
   - iter_dir에 compare.json 저장 (compare_metrics 결과를 json으로 dump)
   - iter_dir에 run_manifest.json 저장: {iter_index, loop_id, phase, seed, descriptor, patch (str), timestamp}
   - baseline run(iter_index=0)에서도 iter_dir = loop_dir / "iter_0" 생성
     baseline의 compare.json = {} (비교 없음), run_manifest.json = {iter_index: 0, ...}
   - NOTE: config.yaml 및 metrics.json 저장은 R3SmokeRunner가 담당 (runner 측)
     orchestrator는 runner가 저장한 경로를 알 수 없으므로
     orchestrator 측에서는 compare.json + run_manifest.json만 작성한다
   - RepairRunner Protocol 시그니처를 변경하지 마라 (iter_artifact_dir 전달 방식은 runner가 output_root 기반으로 계산)
   
   실용적인 iter_artifact_dir 전달 방법:
   orchestrator가 runner를 호출하기 전에 iter_dir을 먼저 만들어두고
   runner가 output_root와 iter_index를 조합하여 스스로 계산하거나,
   RepairRunner Protocol에 선택적 keyword를 추가하는 것은 금지 (Protocol 변경 금지).
   따라서: runner가 __init__에서 output_root를 알고, iter_index를 통해 계산하는 것이 올바름.
   단, loop_id는 runner가 알 수 없으므로 "tmp" prefix나 orchestrator에서 사후 처리한다.
   
   최단 경로: orchestrator가 iter_dir 경로를 runner에게 알리지 않아도 됨.
   orchestrator가 runner 호출 후 metrics_after dict에서 metrics.json artifact 경로를 별도 저장하는 것도 불필요.
   핵심은 iter_dir/compare.json + iter_dir/run_manifest.json만 orchestrator가 작성하면 됨.
   iter_dir/config.yaml은 runner가 자체적으로 저장 (patch 반영 config).
   iter_dir/metrics.json은 TrainerR3.train() / evaluate_model()이 저장.

4. scripts/fglc/repair_loop.py 수정:
   - CD-4: gate_threshold id_nll 0.4 → 0.5 (L84 또는 해당 라인)
   - `--use-real-runner` flag 추가:
     parser.add_argument("--use-real-runner", action="store_true")
     main()에서 ns.use_real_runner가 True이면 R3SmokeRunner를 사용하고
     False (기존 --dry-run / mock) 이면 build_mock_runner 사용
   - 기존 dry-run + mock 시나리오 동작 보존 필수

5. scripts/fglc/r3_smoke.py 신규 작성:
   - argparse: --phase (default R3), --config (required), --split, --seed, --descriptor (required),
     --max-iter (default 3), --max-wall-clock-minutes (default 240.0), --output-root (default outputs/repair),
     --failed-metric (default None, auto-detect from phase)
   - R3SmokeRunner를 직접 빌드 (dry-run 없음, 실제 학습 실행)
   - RepairLoopConfig 구성 후 run_repair_loop 호출
   - 결과 출력: loop_id, final result, metrics_before, metrics_after 요약

6. tests/test_fglc_r3_runner_integration.py 작성:
   - test_r3runner_protocol_signature: R3SmokeRunner가 RepairRunner Protocol을 만족하는지 확인
     (isinstance 또는 signature check)
   - test_r3runner_one_call_cpu: device='cpu'로 R3SmokeRunner.__call__ 1회 실행
     → RunnerOutput 반환, metrics에 id_nll 포함, wall_clock_minutes > 0
   - test_repair_loop_one_iter_end_to_end: run_repair_loop with R3SmokeRunner, max_iter=1, device='cpu'
     → results 반환, ledger.jsonl 파일 생성, REQUIRED_KEYS 19개 확인
   - test_ledger_required_keys_19: 위 결과의 ledger 1줄에서 REQUIRED_KEYS 19개 모두 존재
   - test_iter0_artifacts: loop_dir/iter_0/ 존재, compare.json + run_manifest.json 생성
   - test_mock_regression: --dry-run --mock-scenario improve 동작 무변 (mock runner 회귀)
     repair_loop main(['--phase', 'R3', '--config', str(tmp_path/'smoke.yaml'), '--descriptor', 'mock', '--dry-run', '--mock-scenario', 'improve']) → 0 반환

   pytest fixtures:
   - tmp_config_path: smoke_4060.yaml을 tmp_path에 복사 (tests/fixtures/ 활용)
   - device='cpu' 강제 (config["device"] = "cpu")

FILES_ALLOWED:
src/fglc/runners/__init__.py
src/fglc/runners/r3_runner.py
src/fglc/repair/orchestrator.py
scripts/fglc/repair_loop.py
scripts/fglc/r3_smoke.py
tests/test_fglc_r3_runner_integration.py

FILES_FORBIDDEN:
src/fglc/schemas/
src/fglc/repair/taxonomy.py
src/fglc/repair/diagnose.py
src/fglc/repair/candidates.py
src/fglc/repair/ranker.py
src/fglc/repair/compare.py
src/fglc/repair/ledger.py
src/fglc/models/
src/fglc/training/
src/fglc/evaluation/
src/fglc/data/
src/fglc/__init__.py
docs/idea/
docs/ROADMAP/
scripts/run_codex_task.ps1
.claude/
CLAUDE.md
.mcp.json
.env
configs/

REQUIRED_IMPLEMENTATION:
patch 적용 방식 (deep merge):
  def _apply_patch(config: dict, patch: Mapping[str, Any] | None) -> dict:
      if patch is None:
          return config
      import copy
      result = copy.deepcopy(config)
      for key, value in patch.items():
          if isinstance(value, dict) and isinstance(result.get(key), dict):
              result[key] = _apply_patch(result[key], value)
          else:
              result[key] = value
      return result

iter_artifact_dir 저장 (R3SmokeRunner 측):
  runner가 output_root + descriptor + iter_index로 임시 경로 계산:
  iter_artifact_dir = output_root / f"_pending_{descriptor}_{iter_index}"
  metrics.json, config.yaml 저장
  run_manifest.json 저장 (iter_artifact_dir에)
  
  이후 orchestrator가 loop_dir를 알면 실제 경로로 이동할 수 있지만,
  smoke 단계에서는 임시 경로에 저장하고 end-to-end test에서 파일 존재 여부만 확인해도 된다.
  단순화: R3SmokeRunner가 iter_artifact_dir = output_root / f"iter_{iter_index}" 로 직접 저장.
  (loop_id는 모르지만 test에서 output_root 내 iter_{N}/ 존재 여부 확인)

orchestrator에서 CD-2 구현 (최소):
  baseline 호출 후:
    iter_dir = loop_dir / "iter_0"
    iter_dir.mkdir(parents=True, exist_ok=True)
    (iter_dir / "compare.json").write_text(json.dumps({}))
    (iter_dir / "run_manifest.json").write_text(json.dumps({
        "iter_index": 0, "loop_id": loop_id, "phase": cfg.phase,
        "seed": cfg.seed, "descriptor": cfg.descriptor, "patch": None,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }))
  
  각 iteration 후 compare_metrics 결과 저장:
    iter_dir = loop_dir / f"iter_{iter_index}"
    iter_dir.mkdir(parents=True, exist_ok=True)
    (iter_dir / "compare.json").write_text(json.dumps(cmp))
    (iter_dir / "run_manifest.json").write_text(json.dumps({
        "iter_index": iter_index, "loop_id": loop_id, "phase": cfg.phase,
        "seed": cfg.seed, "descriptor": cfg.descriptor,
        "patch": str(chosen.patch), "timestamp": datetime.now(timezone.utc).isoformat()
    }))

필요한 import 추가 (orchestrator.py 상단):
  import json
  from datetime import datetime, timezone  (이미 있을 수 있음)

REQUIRED_TESTS:
tests/test_fglc_r3_runner_integration.py 6개 PASS.
기존 179 tests 중 test_lifecycle_phase2_hooks.py 제외 회귀 없음.
(lifecycle hook 테스트는 worktree 구조상 .claude/ 부재로 실패하며 TASK 범위 외다.)

ACCEPTANCE_CRITERIA:
1. pytest tests/test_fglc_r3_runner_integration.py → 6 passed (device='cpu')
2. R3SmokeRunner.__call__ 1회 실행 후 RunnerOutput 반환, metrics에 id_nll 포함
3. run_repair_loop(max_iter=1, runner=R3SmokeRunner) → ledger.jsonl 1줄 생성
4. ledger 1줄에 REQUIRED_KEYS 19개 모두 존재 (src/fglc/repair/ledger.py::REQUIRED_KEYS)
5. loop_dir/iter_0/ 존재, compare.json 및 run_manifest.json 생성 (CD-2)
6. repair_loop.py:84 gate_threshold id_nll = 0.5 (CD-4, 0.4 → 0.5)
7. mock runner 회귀 없음 (--dry-run --mock-scenario improve 정상 동작)
8. RepairRunner Protocol 시그니처 충족 (orchestrator.py:74-85)
9. src/fglc/schemas/, src/fglc/repair/diagnose.py 미수정
10. 기존 179 tests (lifecycle 제외) 회귀 없음

COMMIT_MESSAGE:
feat(runners): add R3SmokeRunner + r3_smoke.py + iter artifacts (TASK_10E, CD-2, CD-4)

STOP_CONDITION:
- RepairRunner Protocol 시그니처 변경 시 즉시 중단 (orchestrator.py:74-85 형식 보존)
- src/fglc/schemas/ 또는 src/fglc/repair/diagnose.py 수정 시 즉시 중단
- configs/ 수정 시 즉시 중단
- 기존 179 tests (lifecycle 제외) 추가 실패 시 즉시 중단
- dry-run / mock 시나리오 회귀 발생 시 즉시 중단

RELATED_AGENT_REPORT_IDS: docs/STEP10A_AUDIT_REPORT.md
