# STEP9.5 Patch Result Report

> **Branch**: memory-redesign-2026-05-16
> **Date**: 2026-05-23
> **Status**: ✅ STEP9.5_PASS — Step 10 진입 허가

---

## 1. 목적

Step 9 dry-run에서 발견된 계약 불일치를 해소하는 최소 패치:
- **CD-1**: ledger_path flat 구조 → `{loop_id}/ledger.jsonl` 디렉터리 구조
- **CD-9**: `build_loop_id()` uuid 4-hex suffix 추가 (collision 방지)
- **CD-6**: `EXPERIMENT_LEDGER_SCHEMA.md` Optional Fields 섹션 추가
- **CD-7**: `4060_SMOKE_REPAIR_PATH.md:L151` typo 수정

---

## 2. Codex TASK 결과

| 항목 | 결과 |
|---|---|
| TASK 번호 | TASK_2034 (from TASK_2032 파일) |
| verify exit code | 0 |
| Codex commit | `be39f7e fix(repair): correct ledger path...` |
| RESULT.md | `.agent_tasks/codex_done/TASK_2034_..._RESULT.md` |
| 변경 파일 | 5개 (모두 FILES_ALLOWED 범위) |

---

## 3. 6-Gatekeeper 결과

| # | 조건 | 결과 |
|---|---|---|
| 1 | verify mode exit 0 | ✅ PASS |
| 2 | git diff --cached 수동 review | ✅ PASS — 5파일 모두 명세 일치 |
| 3 | FILES_FORBIDDEN 미수정 | ✅ PASS — harness "Forbidden paths: clean" |
| 4 | RESULT.md 존재 | ✅ PASS — TASK_2034_..._RESULT.md 확인 |
| 5 | REQUIRED_TESTS 통과 | ✅ PASS — 65 passed |
| 6 | T3 implementation-risk-critic PASS | ✅ PASS — ACCEPT_READY |

**→ accept commit 실행: `e243455`**

---

## 4. 코드 변경 상세

### CD-1 패치 (ledger_path 디렉터리 구조)

**orchestrator.py L229-231** (before → after):
```python
# before
ledger_path = cfg.output_root / f"{loop_id}.jsonl"
cfg.output_root.mkdir(parents=True, exist_ok=True)

# after
loop_dir = cfg.output_root / loop_id
loop_dir.mkdir(parents=True, exist_ok=True)
ledger_path = loop_dir / "ledger.jsonl"
```

**repair_loop.py L155-157** (before → after):
```python
# before
cfg.output_root / f"{final.ledger_line['loop_id']}.jsonl"

# after
cfg.output_root / final.ledger_line["loop_id"] / "ledger.jsonl"
```

**test_fglc_repair_orchestrator.py L73** (before → after):
```python
# before
ledger_path = next(output_root.glob("*.jsonl"))

# after
ledger_path = next(output_root.glob("*/ledger.jsonl"))
```

### CD-9 패치 (uuid 4-hex suffix)

**ledger.py** (before → after):
```python
# before
def build_loop_id(now: datetime | None = None) -> str:
    if now is None:
        now = datetime.now(timezone.utc).replace(microsecond=0)
    return f"loop_{now.strftime('%Y-%m-%dT%H-%M-%S')}"

# after
import uuid  # 추가
def build_loop_id(now: datetime | None = None) -> str:
    if now is None:
        now = datetime.now(timezone.utc).replace(microsecond=0)
    suffix = uuid.uuid4().hex[:4]
    return f"loop_{now.strftime('%Y-%m-%dT%H-%M-%S')}-{suffix}"
```

**test_fglc_repair_ledger.py** (before → after):
```python
# before
assert re.match(r"^loop_\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}$", loop_id)
assert loop_id == "loop_2026-05-23T15-00-00"

# after
assert re.match(r"^loop_\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}-[0-9a-f]{4}$", loop_id)
assert loop_id.startswith("loop_2026-05-23T15-00-00-")
assert len(loop_id) == len("loop_2026-05-23T15-00-00-") + 4
```

---

## 5. 회귀 테스트 결과

```
tests\test_fglc_repair_taxonomy.py      ........ (8)
tests\test_fglc_repair_compare.py       ........ (8)
tests\test_fglc_repair_ledger.py        ............. (13)
tests\test_fglc_repair_diagnose.py      ......... (9)
tests\test_fglc_repair_candidates.py    ....... (7)
tests\test_fglc_repair_ranker.py        ........ (8)
tests\test_fglc_repair_orchestrator.py  ........ (8)
tests\test_fglc_repair_loop_cli.py      .... (4)

============================= 65 passed in 0.28s ==============================
```

기준 65+ PASS ✅

---

## 6. 7 시나리오 dry-run 재실행 결과

| Scenario | Exit | Result | PathExists | FormatOK | UuidOK | LoopID |
|---|---|---|---|---|---|---|
| improve | 0 | reject | ✅ | ✅ | ✅ | loop_2026-05-23T09-29-55-**3eef** |
| reject | 0 | reject | ✅ | ✅ | ✅ | loop_2026-05-23T09-29-55-**d057** |
| inconclusive | 0 | inconclusive | ✅ | ✅ | ✅ | loop_2026-05-23T09-29-56-d7cb |
| target_reached | 0 | accept | ✅ | ✅ | ✅ | loop_2026-05-23T09-29-56-7ab6 |
| max_iter | 0 | reject | ✅ | ✅ | ✅ | loop_2026-05-23T09-29-56-d6fb |
| hook_blocked | 0 | inconclusive | ✅ | ✅ | ✅ | loop_2026-05-23T09-29-56-ad5e |
| no_candidate | 0 | inconclusive | ✅ | ✅ | ✅ | loop_2026-05-23T09-29-57-5a5d |

**CD-9 collision 해소 실증**: `improve`와 `reject`가 동일 초 `09-29-55`에 실행되었으나 suffix가 `3eef` vs `d057`으로 달라 독립 디렉터리 생성 확인.

---

## 7. 디렉터리 구조 확인 (K.9)

패치 후 새로 생성된 loop 디렉터리:
```
outputs/repair/
  .gitkeep
  loop_2026-05-23T09-29-55-3eef/ledger.jsonl  ← improve
  loop_2026-05-23T09-29-55-d057/ledger.jsonl  ← reject
  loop_2026-05-23T09-29-56-7ab6/ledger.jsonl  ← target_reached
  loop_2026-05-23T09-29-56-ad5e/ledger.jsonl  ← hook_blocked
  loop_2026-05-23T09-29-56-d6fb/ledger.jsonl  ← max_iter
  loop_2026-05-23T09-29-56-d7cb/ledger.jsonl  ← inconclusive
  loop_2026-05-23T09-29-57-5a5d/ledger.jsonl  ← no_candidate
  (구 flat files: loop_..T08-5*-.jsonl — Step 9 dry-run 잔재, untracked, git impact 없음)
```

7개 시나리오 → 7개 독립 loop 디렉터리. ✅

---

## 8. Ledger REQUIRED_KEYS 검증 (K.10)

```
PASS loop_2026-05-23T09-29-55-3eef line 0
PASS loop_2026-05-23T09-29-55-3eef line 1  (improve = 2-iter)
PASS loop_2026-05-23T09-29-55-d057 line 0
PASS loop_2026-05-23T09-29-56-7ab6 line 0
PASS loop_2026-05-23T09-29-56-ad5e line 0
PASS loop_2026-05-23T09-29-56-d6fb line 0
PASS loop_2026-05-23T09-29-56-d7cb line 0
PASS loop_2026-05-23T09-29-57-5a5d line 0

Total: 8 lines checked, 0 errors
```

errors == 0 ✅

---

## 9. Doc 수정 결과 (Main Claude 직접)

| 항목 | 파일 | 변경 | 커밋 |
|---|---|---|---|
| CD-6 | `docs/EXPERIMENT_LEDGER_SCHEMA.md` | loop_id 형식 설명 + Optional Fields 섹션(13개 필드) 추가 | `7218c6d` |
| CD-7 | `docs/ROADMAP/4060_SMOKE_REPAIR_PATH.md:L151` | `--max-wall-clock` → `--max-wall-clock-minutes` | `7218c6d` |

---

## 10. 임시 파일 정리 상태

| 파일 | 상태 |
|---|---|
| `step9_validate.py` | 삭제 권한 거부 — untracked, git impact 없음 |
| `_tmp_ledger_check.py` | 삭제 권한 거부 — untracked, git impact 없음 |

---

## 11. git hygiene (K.11)

tracked 변경: Step 9.5 이전 pre-existing 파일만 (hook_execution_log, session_reports, plans).
Step 9.5 커밋: `e243455` (Codex merge) + `7218c6d` (doc 수정).
출처: `git status --short` 확인.

---

## 12. STEP9.5_PASS 조건 체크리스트

- [x] Codex TASK_2034 verify exit 0
- [x] 6-Gatekeeper 6개 모두 ✅
- [x] 회귀 테스트 65 passed
- [x] dry-run 7 시나리오 모두 exit 0, stdout JSON 유효
- [x] payload["ledger_path"]가 `{loop_id}/ledger.jsonl` 형식 (CD-1)
- [x] loop_id에 4-hex suffix 포함 (CD-9)
- [x] 7개 시나리오 → 7개 독립 loop 디렉터리 (collision 없음)
- [x] LEDGER_SCHEMA.md Optional Fields 섹션 추가됨 (CD-6)
- [x] 4060_SMOKE_REPAIR_PATH.md L151 typo 수정됨 (CD-7)
- [x] git hygiene 통과

**→ STEP9.5_PASS** ✅

---

## 13. Step 10 진입 허용 조건

- [x] Step 9 `STEP9_DRY_RUN_REPAIR_LOOP_REPORT.md` 존재
- [x] Step 9.5 CD-1 패치 완료 + 회귀 65 passed
- [x] Step 9.5 CD-9 패치 완료 + collision 해소 확인
- [x] CD-6/CD-7 doc 수정 완료
- [x] 7 시나리오 재실행에서 `{loop_id}/ledger.jsonl` 구조 + uuid suffix 확인
- [x] T3 agent report PASS
- [x] Step 9.5 RESULT.md (이 파일)

**Step 10 R3 base WM smoke 진입 허가** ✅

---

## 14. 미처리 CD (defer 사유 확인)

| CD | 내용 | defer 사유 |
|---|---|---|
| CD-2 | per-iter artifact 4종 | Step 10 R3 runner 구현 시 동반 |
| CD-3 | gate_threshold ledger field | LEDGER_SCHEMA REQUIRED_KEYS 정합 후 결정 |
| CD-4 | id_nll gate 0.4→0.5 | Step 10 실측 후 재조정 |
| CD-5 | --dry-run help text | Step 10 real-run mode 분리 시 |
| CD-8 | smoke_4060.yaml K/h_dim/batch 권장값 | Step 10 진입 직전 |
