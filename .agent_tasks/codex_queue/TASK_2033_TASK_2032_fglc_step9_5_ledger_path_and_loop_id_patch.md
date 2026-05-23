TASK_NAME: TASK_2032_fglc_step9_5_ledger_path_and_loop_id_patch

BACKGROUND:
  Step 9 정적 감사 및 dry-run에서 발견된 2개 계약 불일치 패치.

  CD-1: orchestrator.py:229와 repair_loop.py:155-157이 docs/EXPERIMENT_LEDGER_SCHEMA.md
        L5,22의 계약(outputs/repair/{loop_id}/ledger.jsonl)과 다르게 flat 경로
        (outputs/repair/{loop_id}.jsonl)를 사용함.
        - 현재 orchestrator.py:229: ledger_path = cfg.output_root / f"{loop_id}.jsonl"
        - 현재 repair_loop.py:155-157: cfg.output_root / f"{final.ledger_line['loop_id']}.jsonl"
        - 현재 test_orchestrator.py:73: output_root.glob("*.jsonl")

  CD-9: build_loop_id()가 초 단위 정밀도(loop_YYYY-MM-DDTHH-MM-SS)로 loop_id를 생성하여
        동일 초에 2 run 실행 시 같은 ledger 파일에 line 혼입.
        - 현재 ledger.py:80-83:
            def build_loop_id(now=None):
                if now is None:
                    now = datetime.now(timezone.utc).replace(microsecond=0)
                return f"loop_{now.strftime('%Y-%m-%dT%H-%M-%S')}"
        - 현재 test_ledger.py:136-137:
            assert re.match(r"^loop_\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}$", loop_id)
            assert loop_id == "loop_2026-05-23T15-00-00"

  관련 report: docs/STEP9_PATCH_PLAN.md §1, §2.

GOAL:
  CD-1: ledger_path를 outputs/repair/{loop_id}/ledger.jsonl 계층 구조로 수정.
  CD-9: loop_id에 uuid4 4-hex suffix 추가 (loop_YYYY-MM-DDTHH-MM-SS-{4hex}).
        collision 위험 제거.

FILES_ALLOWED:
  src/fglc/repair/orchestrator.py
  src/fglc/repair/ledger.py
  scripts/fglc/repair_loop.py
  tests/test_fglc_repair_orchestrator.py
  tests/test_fglc_repair_loop_cli.py
  tests/test_fglc_repair_ledger.py

FILES_FORBIDDEN:
  .claude/
  CLAUDE.md
  CLAUDE.local.md
  .mcp.json
  .venv/
  data/
  outputs/
  secrets/
  .env*
  scripts/run_codex_task.ps1
  docs/idea/
  docs/ROADMAP/
  docs/EXPERIMENT_LEDGER_SCHEMA.md
  src/fglc/schemas/
  src/fglc/repair/taxonomy.py
  src/fglc/repair/compare.py
  src/fglc/repair/diagnose.py
  src/fglc/repair/candidates.py
  src/fglc/repair/ranker.py
  configs/fglc/smoke_4060.yaml

REQUIRED_IMPLEMENTATION:
  1. src/fglc/repair/ledger.py — build_loop_id() 수정:
     - 파일 상단에 'import uuid' 추가 (기존 imports 직후)
     - build_loop_id() 함수 변경:
       현재:
         def build_loop_id(now: datetime | None = None) -> str:
             if now is None:
                 now = datetime.now(timezone.utc).replace(microsecond=0)
             return f"loop_{now.strftime('%Y-%m-%dT%H-%M-%S')}"
       변경 후:
         def build_loop_id(now: datetime | None = None) -> str:
             if now is None:
                 now = datetime.now(timezone.utc).replace(microsecond=0)
             suffix = uuid.uuid4().hex[:4]
             return f"loop_{now.strftime('%Y-%m-%dT%H-%M-%S')}-{suffix}"

  2. src/fglc/repair/orchestrator.py — run_repair_loop() 내 L229-230 수정:
     현재:
       ledger_path = cfg.output_root / f"{loop_id}.jsonl"
       cfg.output_root.mkdir(parents=True, exist_ok=True)
     변경 후:
       loop_dir = cfg.output_root / loop_id
       loop_dir.mkdir(parents=True, exist_ok=True)
       ledger_path = loop_dir / "ledger.jsonl"

  3. scripts/fglc/repair_loop.py — main() stdout JSON 내 L155-157 수정:
     현재:
       "ledger_path": str(
           cfg.output_root / f"{final.ledger_line['loop_id']}.jsonl"
       ),
     변경 후:
       "ledger_path": str(
           cfg.output_root / final.ledger_line["loop_id"] / "ledger.jsonl"
       ),

  4. tests/test_fglc_repair_orchestrator.py — _records() helper L72-74 수정:
     현재:
       def _records(output_root):
           ledger_path = next(output_root.glob("*.jsonl"))
           return [json.loads(line) for line in ledger_path.read_text(encoding="utf-8").splitlines()]
     변경 후:
       def _records(output_root):
           ledger_path = next(output_root.glob("*/ledger.jsonl"))
           return [json.loads(line) for line in ledger_path.read_text(encoding="utf-8").splitlines()]

  5. tests/test_fglc_repair_ledger.py — test_build_loop_id_format() 수정:
     현재 (L133-137):
       def test_build_loop_id_format():
           loop_id = build_loop_id(datetime(2026, 5, 23, 15, 0, 0, tzinfo=timezone.utc))

           assert re.match(r"^loop_\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}$", loop_id)
           assert loop_id == "loop_2026-05-23T15-00-00"
     변경 후:
       def test_build_loop_id_format():
           loop_id = build_loop_id(datetime(2026, 5, 23, 15, 0, 0, tzinfo=timezone.utc))

           assert re.match(r"^loop_\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}-[0-9a-f]{4}$", loop_id)
           assert loop_id.startswith("loop_2026-05-23T15-00-00-")
           assert len(loop_id) == len("loop_2026-05-23T15-00-00-") + 4

       (주의: 'assert loop_id == "loop_2026-05-23T15-00-00"' 라인을 위 3줄로 교체.
        uuid suffix는 매 호출마다 다르므로 exact match 불가.)

REQUIRED_TESTS:
  - tests/test_fglc_repair_ledger.py 전체 PASS (build_loop_id format 신규 regex 포함)
  - tests/test_fglc_repair_orchestrator.py 전체 PASS (8 tests)
  - tests/test_fglc_repair_loop_cli.py 전체 PASS (4 tests, ledger_path 존재 확인 포함)
  - tests/test_fglc_repair_*.py 전체 회귀 65+ passed 유지

ACCEPTANCE_CRITERIA:
  1. 회귀 테스트 65+ passed 유지 (CD-9 test 갱신 포함)
  2. orchestrator.py 변경이 정확히 REQUIRED_IMPLEMENTATION 2번 명세대로 적용
  3. repair_loop.py 변경이 정확히 REQUIRED_IMPLEMENTATION 3번 명세대로 적용
  4. ledger.py build_loop_id가 REQUIRED_IMPLEMENTATION 1번 명세대로 uuid 4-hex suffix 포함
  5. test_orchestrator.py _records() glob이 "*/ledger.jsonl"로 변경됨
  6. test_ledger.py test_build_loop_id_format이 새 regex + startswith + len 검증으로 변경됨
  7. 금지 경로(FILES_FORBIDDEN) 미수정
  8. RESULT.md 파일 생성:
     .agent_tasks/codex_done/TASK_2032_fglc_step9_5_ledger_path_and_loop_id_patch_RESULT.md

COMMIT_MESSAGE:
  fix(repair): correct ledger path to {loop_id}/ledger.jsonl + add uuid suffix to loop_id (CD-1, CD-9)

STOP_CONDITION:
  - 65 passed 미달
  - 금지 경로 수정 발견
  - build_loop_id 변경이 외부 호출자(orchestrator)와 incompatible
  - test_cli_smoke_improve의 Path(payload["ledger_path"]).exists() fail
  - timeout 30분 초과

RELATED_AGENT_REPORT_IDS:
  (T3 implementation-risk-critic report는 verify 후
  docs/orchestration/agent_reports/2026-05/impl_risk_TASK_2032_R1.md 경로로 생성 예정)
