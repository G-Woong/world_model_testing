# STEP9_PATCH_PLAN — Step 9.5 패치 명세

> **Status**: PATCH_REQUIRED (CD-1 필수, CD-3/CD-4/CD-5/CD-9 권장, CD-2/CD-7/CD-8 deferred)
> **작성일**: 2026-05-23
> **근거**: `docs/STEP9_DRY_RUN_REPAIR_LOOP_REPORT.md` §8 판정

---

## 1. CD-1 패치 명세 (필수 — Step 10 진입 차단 해제)

### 문제

`orchestrator.py:229`:
```python
ledger_path = cfg.output_root / f"{loop_id}.jsonl"
```
→ `outputs/repair/loop_YYYY-MM-DDTHH-MM-SS.jsonl` (flat 파일)

`repair_loop.py:155-157` (stdout JSON 생성):
```python
"ledger_path": str(cfg.output_root / f"{final.ledger_line['loop_id']}.jsonl"),
```
→ 동일 flat 경로

### 목표 상태 (문서 계약)

```
outputs/repair/{loop_id}/
  ledger.jsonl
```

### 변경 명세

**파일 1: `src/fglc/repair/orchestrator.py`**

변경 위치: `run_repair_loop()` 함수 내 (L229-230)

```python
# 현재
ledger_path = cfg.output_root / f"{loop_id}.jsonl"
cfg.output_root.mkdir(parents=True, exist_ok=True)

# 변경 후
loop_dir = cfg.output_root / loop_id
loop_dir.mkdir(parents=True, exist_ok=True)
ledger_path = loop_dir / "ledger.jsonl"
```

**파일 2: `scripts/fglc/repair_loop.py`**

변경 위치: `main()` 함수 내 stdout JSON (L155-157)

```python
# 현재
"ledger_path": str(cfg.output_root / f"{final.ledger_line['loop_id']}.jsonl"),

# 변경 후
"ledger_path": str(cfg.output_root / final.ledger_line["loop_id"] / "ledger.jsonl"),
```

**파일 3: `tests/test_fglc_repair_orchestrator.py`**

테스트에서 ledger 파일을 `tmp_path / "repair_subdir" / f"{loop_id}.jsonl"` 패턴으로 찾는 부분이 있으면, `tmp_path / "repair_subdir" / loop_id / "ledger.jsonl"` 패턴으로 수정 필요.

실제 코드를 확인하여 glob 패턴 또는 직접 경로 참조를 모두 수정.

### Acceptance Criteria (재검증 명령)

```powershell
# 1. 회귀 테스트 65 passed 유지
.\.venv\Scripts\python.exe -m pytest -q tests\test_fglc_repair_orchestrator.py tests\test_fglc_repair_loop_cli.py

# 2. dry-run 실행 후 디렉터리 구조 확인
.\.venv\Scripts\python.exe scripts\fglc\repair_loop.py --phase R3 --config configs\fglc\smoke_4060.yaml --descriptor smoke --mock-scenario improve --max-iter 1 --output-root outputs\repair
Get-ChildItem outputs\repair -Recurse | Format-Table Name, FullName
# 기대:
#   outputs\repair\loop_YYYY-MM-DDTHH-MM-SS\
#     ledger.jsonl

# 3. stdout ledger_path가 디렉터리 구조를 반영하는지 확인
#    기대: "ledger_path": "outputs\\repair\\loop_...\ledger.jsonl"
```

### Codex TASK 명세 초안

```
TASK_NAME: TASK_2032_fglc_step9_ledger_path_patch
BACKGROUND:
  Step 9 정적 감사에서 CD-1 발견: orchestrator.py:229와 repair_loop.py:155-157이
  docs/EXPERIMENT_LEDGER_SCHEMA.md L5,22의 계약(outputs/repair/{loop_id}/ledger.jsonl)과
  다르게 flat 경로(outputs/repair/{loop_id}.jsonl)를 사용함.

GOAL:
  ledger_path를 outputs/repair/{loop_id}/ledger.jsonl 계층 구조로 수정한다.

FILES_ALLOWED:
  src/fglc/repair/orchestrator.py
  scripts/fglc/repair_loop.py
  tests/test_fglc_repair_orchestrator.py
  tests/test_fglc_repair_loop_cli.py

FILES_FORBIDDEN:
  .claude/
  CLAUDE.md
  docs/idea/
  src/fglc/schemas/
  scripts/run_codex_task.ps1

REQUIRED_IMPLEMENTATION:
  1. orchestrator.py run_repair_loop() 내
     - loop_dir = cfg.output_root / loop_id
     - loop_dir.mkdir(parents=True, exist_ok=True)
     - ledger_path = loop_dir / "ledger.jsonl"
  2. repair_loop.py main() stdout JSON 내
     - ledger_path = cfg.output_root / loop_id / "ledger.jsonl"

REQUIRED_TESTS:
  - test_fglc_repair_orchestrator.py 전체 (8 tests) pass
  - test_fglc_repair_loop_cli.py 전체 (4 tests) pass
  - dry-run 실행 후 outputs/repair/{loop_id}/ledger.jsonl 파일 존재 확인

ACCEPTANCE_CRITERIA:
  1. 65 passed 유지
  2. dry-run 실행 후 outputs/repair/{loop_id}/ledger.jsonl 경로로 파일 생성
  3. stdout JSON ledger_path 키가 새 경로 반영
  4. 금지 경로 미수정

COMMIT_MESSAGE:
  fix(repair): correct ledger path to {loop_id}/ledger.jsonl hierarchy (CD-1)

STOP_CONDITION:
  65 passed 미달 또는 금지 경로 수정 발견 시 abort
```

### 6-Gatekeeper 체크포인트

CD-1 패치 accept 전 반드시 확인:
1. verify mode exit 0 ✓
2. git diff --cached 수동 review ✓
3. 금지 경로 미수정 ✓
4. RESULT.md 존재 ✓
5. REQUIRED_TESTS 통과 ✓
6. T3 (implementation-risk-critic) agent report PASS ✓

---

## 2. CD-9 개선 명세 (권장 — Step 9.5 동반)

### 문제

`build_loop_id()`가 초 단위 정밀도로 생성되어 동일 초에 2개 run 실행 시 같은 파일에 혼입.

### 목표 상태

loop_id에 랜덤 suffix(4자리 hex) 추가:
```
loop_YYYY-MM-DDTHH-MM-SS-{uuid4_short}
```

변경 파일: `src/fglc/repair/ledger.py` `build_loop_id()` 함수.

### Acceptance Criteria

```python
import uuid
def build_loop_id(now=None):
    if now is None:
        now = datetime.now(timezone.utc).replace(microsecond=0)
    suffix = uuid.uuid4().hex[:4]
    return f"loop_{now.strftime('%Y-%m-%dT%H-%M-%S')}-{suffix}"
```

`test_fglc_repair_ledger.py` 에서 `build_loop_id()` 형식 검증 테스트 업데이트 필요.

---

## 3. CD-3 패치 명세 (LOW 우선순위)

### 문제

`orchestrator.py`의 `_base_line()`이 `gate_threshold` 필드를 기록하지 않음.
`LEDGER_SCHEMA.md` 예시 L77에는 포함되어 있으나 REQUIRED_KEYS에는 없음.

### 목표 상태

`_base_line()`에 `gate_threshold` 추가 (Optional field):
```python
"gate_threshold": cfg.gate_thresholds.get(cfg.failed_metric),
```

단, `LEDGER_SCHEMA.md`의 REQUIRED_KEYS에 추가 여부는 CD-6(schema 예시-REQUIRED_KEYS 불일치) 해결 후 결정.

---

## 4. CD-4 처리 (DOC_REVISION)

### 문제

`4060_SMOKE_REPAIR_PATH.md` L89: R3 gate ≤ 0.5 nat
`repair_loop.py:84`: `"id_nll": 0.4` (더 엄격한 기준)

### 권장 처리

옵션 A (권장): `repair_loop.py` 값을 0.5로 맞추고 주석 추가:
```python
"id_nll": 0.5,  # 4060_SMOKE_REPAIR_PATH.md R3 gate threshold
```

옵션 B: doc을 0.4로 수정.

Step 10 R3 실측 후 조정 예정이므로 Step 9.5에서 옵션 A로 진행.

---

## 5. CD-5 처리 (help text 보강)

`repair_loop.py`의 `--dry-run` argparse에 help 추가:
```python
parser.add_argument(
    "--dry-run", action="store_true",
    help="(Step 8 control plane only) mock runner always used; this flag is reserved for future real-run mode."
)
```

---

## 6. CD-6 ~ CD-8 처리 (DOC_REVISION 또는 Deferred)

| # | 항목 | 처리 |
|---|---|---|
| CD-6 | schema 예시 Optional 필드 | `LEDGER_SCHEMA.md`에 "## Optional Fields" 섹션 추가 |
| CD-7 | `--max-wall-clock 240` 오기 | `4060_SMOKE_REPAIR_PATH.md` L151 수정 → `--max-wall-clock-minutes 240` |
| CD-8 | smoke_4060.yaml hyperparam | Step 10 진입 직전 K=6, h_dim=128, batch=16으로 수정 |

CD-6, CD-7은 docs 파일 수정이므로 별도 Codex TASK 불필요 (Main Claude 직접 처리 가능).

---

## 7. 재검증 명령 (Step 9.5 완료 후)

```powershell
# 회귀 테스트 전체
.\.venv\Scripts\python.exe -m pytest tests\test_fglc_repair_taxonomy.py tests\test_fglc_repair_compare.py tests\test_fglc_repair_ledger.py tests\test_fglc_repair_diagnose.py tests\test_fglc_repair_candidates.py tests\test_fglc_repair_ranker.py tests\test_fglc_repair_orchestrator.py tests\test_fglc_repair_loop_cli.py
# 기대: 65+ passed (CD-9 테스트 추가 시 66+)

# dry-run 7 시나리오 재실행 (Step 9 D.1 동일 명령)
# CD-1 패치 확인: 디렉터리 구조 생성 여부
Get-ChildItem outputs\repair -Recurse | Format-Table Name, FullName

# git hygiene 재확인
git status --short
```

---

## 8. Step 10 진입 허용 조건

- [ ] CD-1 패치 완료 (orchestrator.py + repair_loop.py + 연관 테스트)
- [ ] 회귀 테스트 ≥ 65 passed
- [ ] dry-run 재실행에서 `{loop_id}/ledger.jsonl` 구조 확인
- [ ] Step 9.5 RESULT.md 존재
- [ ] T3 agent report PASS

---

## 9. 큰 그림 요약

```
Step 9.5:
  CD-1 (필수): orchestrator.py + repair_loop.py ledger path 구조 수정
  CD-9 (권장): loop_id에 uuid suffix 추가
  CD-3 (LOW): gate_threshold optional field 추가
  CD-4 (LOW): id_nll gate 0.4→0.5 (4060 doc 정합)
  CD-5 (LOW): --dry-run help text 보강
  CD-6, CD-7 (DOC): docs 파일 직접 수정

Step 10:
  CD-2: R3 real runner 구현 시 iter_{N}/ artifact 4종 동반 생성
  CD-8: smoke_4060.yaml 권장값(K=6, h_dim=128, batch=16) 업데이트
```
