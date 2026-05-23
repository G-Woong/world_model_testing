TASK_NAME: fglc_repair_compare_ledger

BACKGROUND: |
  docs/EXPERIMENT_REPAIR_LOOP_PLAN.md §D.4 + docs/EXPERIMENT_LEDGER_SCHEMA.md는
  closed-loop repair harness의 결정 규칙(accept/reject/inconclusive)과
  ledger schema(JSON Lines, REQUIRED_KEYS 19개)를 정형화했다.
  이 TASK는 그 명세를 두 개의 Python 모듈로 구현한다.
  Step 5의 src/fglc/repair/taxonomy.py 위에 얹히는 두 번째 모듈 군이다.

GOAL: |
  Create:
    src/fglc/repair/compare.py
      - compare_metrics() pure function
      - MetricDirection Enum (LOWER_BETTER / HIGHER_BETTER)
      - 반환 dict는 ledger line subset (result / result_reason / deltas / epsilon_*)
    src/fglc/repair/ledger.py
      - REQUIRED_KEYS = (19개, SSoT verbatim)
      - compute_config_hash() (sha256, "sha256:<hex>" 형식)
      - build_run_id() / build_loop_id() helpers
      - validate_ledger_line() + LedgerSchemaError
      - append_ledger_line() with filelock 3.25.2
    tests/test_fglc_repair_compare.py  (>=7 test groups)
    tests/test_fglc_repair_ledger.py   (>=8 test groups, uses tmp_path)

  Touch nothing else. Do not modify src/fglc/repair/taxonomy.py or __init__.py.
  Do not write any files under outputs/, data/, configs/.

FILES_ALLOWED:
  - src/fglc/repair/compare.py
  - src/fglc/repair/ledger.py
  - tests/test_fglc_repair_compare.py
  - tests/test_fglc_repair_ledger.py
  - .agent_tasks/codex_done/TASK_2026_05_23_FGLC_REPAIR_COMPARE_LEDGER_RESULT.md
  - .agent_tasks/codex_done/TASK_2029_fglc_repair_compare_ledger_RESULT.md

FILES_FORBIDDEN:
  - src/fglc/repair/__init__.py
  - src/fglc/repair/taxonomy.py
  - src/fglc/schemas/
  - .claude/
  - CLAUDE.md
  - docs/
  - scripts/
  - configs/
  - outputs/
  - data/
  - "** (all other files not listed in FILES_ALLOWED)"

REQUIRED_IMPLEMENTATION: |
  1. Read docs/EXPERIMENT_LEDGER_SCHEMA.md (SSoT for ledger fields + accept rule).
  2. Read docs/EXPERIMENT_REPAIR_LOOP_PLAN.md §D.4 (accept/reject 결정 규칙 원본).
  3. Implement src/fglc/repair/compare.py:
     - module docstring citing "Source: docs/EXPERIMENT_LEDGER_SCHEMA.md §결정 규칙 + docs/EXPERIMENT_REPAIR_LOOP_PLAN.md §D.4"
     - class MetricDirection(str, Enum):
         LOWER_BETTER = "lower_better"
         HIGHER_BETTER = "higher_better"
     - def compare_metrics(
         metrics_before: dict[str, float | None],
         metrics_after: dict[str, float | None],
         failed_metric: str,
         metric_directions: dict[str, str | MetricDirection],
         *,
         epsilon_accept: float = 0.05,
         epsilon_reject: float = 0.0,
         epsilon_secondary: float = 0.10,
       ) -> dict
       반환 keys (정확히 7개):
         "result"                  : "accept" | "reject" | "inconclusive"
         "result_reason"           : str (사람이 읽을 1문장 근거)
         "deltas"                  : {k: float | None for k in metrics_after.keys()}
         "epsilon_accept"          : float (입력 그대로 echo)
         "epsilon_reject"          : float
         "epsilon_secondary"       : float
         "failed_metric_direction" : "lower_better" | "higher_better"
     - 결정 로직 (docs/EXPERIMENT_LEDGER_SCHEMA.md §결정 규칙 verbatim):
         primary_delta = after[failed_metric] - before[failed_metric]
         direction이 LOWER_BETTER이면 improvement = -primary_delta (낮을수록 좋음)
         direction이 HIGHER_BETTER이면 improvement = +primary_delta
         secondary deltas = {k: (after[k] - before[k]) for k in after if k != failed_metric and 둘 다 not None}
         accept :  improvement >= epsilon_accept AND 모든 secondary improvement > -epsilon_secondary
                   (secondary improvement도 direction별로 부호 보정)
         reject :  improvement <= epsilon_reject OR 어떤 secondary improvement <= -epsilon_secondary
         inconclusive : else
     - 에러 케이스:
         failed_metric이 metrics_before/metrics_after에 없음 → ValueError
         metric_directions[failed_metric] 누락 → ValueError
         before[failed_metric] 또는 after[failed_metric]이 None → ValueError("primary metric must be measured")
         secondary 중 한쪽이 None인 metric은 secondary delta 평가에서 skip (silent skip; 단, 그 키의 deltas 값은 None으로 기록)
  4. Implement src/fglc/repair/ledger.py:
     - module docstring citing "Source: docs/EXPERIMENT_LEDGER_SCHEMA.md (Ledger Line Schema + REQUIRED_KEYS)"
     - REQUIRED_KEYS: tuple[str, ...] = (
         "loop_id", "iter", "run_id", "git_sha", "config_hash",
         "config_path", "phase", "split",
         "metrics_before", "metrics_after", "deltas",
         "failed_metric", "diagnosed_cause",
         "candidate_chosen", "result",
         "stop_condition_hit", "next_action",
         "wall_clock_minutes", "vram_peak_mib",
       )   # 정확히 19개 — docs/EXPERIMENT_LEDGER_SCHEMA.md §필수 키 목록 verbatim
     - class LedgerSchemaError(ValueError): pass
     - def validate_ledger_line(line: dict) -> None:
         REQUIRED_KEYS 중 누락된 키 → LedgerSchemaError(f"missing keys: {sorted(missing)}")
         line["result"]가 {"accept","reject","inconclusive"} 외 → LedgerSchemaError
         line["stop_condition_hit"]이 None 또는
           {"max_iter","wall_clock","target_reached","consecutive_inconclusive","hook_blocked"} 외 → LedgerSchemaError
     - def compute_config_hash(config: dict | str | Path) -> str:
         dict → json.dumps(config, sort_keys=True, ensure_ascii=False).encode("utf-8") → sha256
         str → utf-8 인코딩 → sha256
         Path → read_bytes() → sha256
         반환: f"sha256:{hexdigest}"
     - def build_loop_id(now: datetime | None = None) -> str:
         now = now or datetime.now(timezone.utc).replace(microsecond=0)
         iso = now.strftime("%Y-%m-%dT%H-%M-%S")  # 콜론을 하이픈으로
         return f"loop_{iso}"
     - def build_run_id(phase: str, descriptor: str, seed: int, key_params: dict) -> str:
         params_sorted = "_".join(f"{k}{v}" for k, v in sorted(key_params.items()))
         return f"{phase}_{descriptor}_seed{seed}_{params_sorted}"
       (예: build_run_id("R3","smoke",42,{"K":6,"d":32,"h":128}) → "R3_smoke_seed42_K6_d32_h128")
     - def append_ledger_line(
         ledger_path: Path, line: dict, *, lock_timeout: float = 10.0
       ) -> None:
         validate_ledger_line(line)
         lock_path = ledger_path.with_suffix(ledger_path.suffix + ".lock")
         with FileLock(str(lock_path), timeout=lock_timeout):
             with ledger_path.open("a", encoding="utf-8") as f:
                 f.write(json.dumps(line, ensure_ascii=False, sort_keys=True))
                 f.write("\n")
                 f.flush()
                 os.fsync(f.fileno())
     - import 정책: stdlib(os, json, hashlib, datetime, pathlib, typing) + filelock만.
       taxonomy.py / __init__.py import 금지.
  5. Implement tests/test_fglc_repair_compare.py (>=7 test groups):
     - sys.path bootstrap (Step 5 pattern): insert REPO_ROOT/src
     (1) test_compare_lower_better_accept: NLL improves by 0.14 >= 0.05 → accept
     (2) test_compare_lower_better_reject_no_improvement: NLL improves by 0.0 <= 0.0 → reject
     (3) test_compare_lower_better_reject_secondary_regression: primary OK but secondary regresses 0.15 >= 0.10 → reject
     (4) test_compare_higher_better_accept: AUROC improves by 0.08 >= 0.05 → accept
     (5) test_compare_inconclusive_small_improvement: improvement 0.03 (< 0.05, > 0.0) → inconclusive
     (6) test_compare_raises_on_missing_failed_metric: failed_metric 키 부재 → ValueError
     (7) test_compare_skips_secondary_with_none: secondary metric 한쪽 None → silent skip, deltas[key]=None
     (8) test_compare_returns_all_expected_keys: 반환 dict가 7개 키 모두 포함
  6. Implement tests/test_fglc_repair_ledger.py (>=8 test groups, tmp_path 사용):
     - sys.path bootstrap (Step 5 pattern)
     (1) test_required_keys_count_and_content: REQUIRED_KEYS == 19개 + SSoT 리스트와 1:1
     (2) test_validate_passes_on_complete_line: 19키 모두 포함된 minimal line → 통과
     (3) test_validate_raises_on_missing_key: 한 키 제거 → LedgerSchemaError
     (4) test_validate_raises_on_invalid_result: result="maybe" → LedgerSchemaError
     (5) test_validate_raises_on_invalid_stop_condition: stop_condition_hit="forever" → LedgerSchemaError
     (6) test_validate_allows_none_stop_condition: stop_condition_hit=None → 통과
     (7) test_compute_config_hash_dict_deterministic: 동일 dict 두 번 hash → 동일 결과 + "sha256:" prefix
     (8) test_compute_config_hash_dict_order_invariant: {a:1,b:2}와 {b:2,a:1} hash → 동일
     (9) test_compute_config_hash_str_and_path: str/Path 입력 모두 동작
     (10) test_build_loop_id_format: regex "^loop_\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}$"
     (11) test_build_run_id_format: 위 예시 → "R3_smoke_seed42_K6_d32_h128"
     (12) test_append_ledger_line_round_trip: tmp_path/ledger.jsonl에 append → 다시 read → JSON parse → 원본 line dict와 동일
     (13) test_append_two_lines_yields_two_records: 두 번 append → 두 줄 + 두 line 모두 valid

REQUIRED_TESTS: |
  .venv\Scripts\python.exe -m pytest -q tests\test_fglc_repair_compare.py tests\test_fglc_repair_ledger.py
  NOTE: .venv\Scripts\pytest.exe is broken in this venv (silent exit 1). Use python -m pytest only.

ACCEPTANCE_CRITERIA: |
  - Exactly 4 source files added (compare.py, ledger.py, 2 test files).
  - RESULT.md added (5th file).
  - 0 files modified outside FILES_ALLOWED.
  - .venv\Scripts\python.exe -m pytest -q tests\test_fglc_repair_compare.py tests\test_fglc_repair_ledger.py → all green.
  - No test writes files under outputs/, data/, configs/ (tmp_path enforced).
  - No import from src/fglc/schemas/ or src/fglc/repair/taxonomy.py.
  - No external deps beyond stdlib + filelock (already pinned).
  - Working tree clean after commit (git status --short returns empty).

COMMIT_MESSAGE: feat(repair): add compare/ledger modules (accept/reject decision + jsonl ledger)

STOP_CONDITION: |
  Stop immediately after the single commit. Do not implement diagnose.py /
  candidates.py / ranker.py / orchestrator.py — those are separate Steps.
  Do not modify docs/EXPERIMENT_LEDGER_SCHEMA.md (read-only SSoT).
  Do not modify src/fglc/repair/__init__.py or taxonomy.py (Step 5 산출물).
  Do not add new entries to src/fglc/repair/__init__.py — Step 8 orchestrator merge 시 일괄 처리.

SANDBOX_MODE: bypass

RELATED_AGENT_REPORT_IDS:
  - docs/orchestration/agent_reports/2026-05/impl_risk_fglc_repair_compare_ledger_R1.md
