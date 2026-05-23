# Step 9.5 — CD-1 + CD-9 Patch + Doc Revision PLAN (2026-05-23)

> **Status**: PLAN ONLY. ExitPlanMode 승인 후 execute 단계에서 Codex TASK enqueue → run → verify → accept/abort → Main Claude doc 수정 → 임시 파일 삭제 → 7 시나리오 재검증.
> **Branch**: memory-redesign-2026-05-16
> **Prior commit**: `5170885` (Step 8 merge — 65 passed)
> **Prior phase**: Step 9 STEP9_PATCH_REQUIRED 판정 (`docs/STEP9_DRY_RUN_REPAIR_LOOP_REPORT.md` §8)
> **현재 task**: Step 9 검증에서 발견한 CD-1(ledger path) + CD-9(loop_id collision)를 Codex로 패치하고, CD-6/CD-7 doc 수정과 step9_validate.py 정리를 Main Claude가 동반 처리.

---

## Context — 왜 이 패치가 필요한가

Step 9 검증에서 9개 계약 불일치(CD-1~CD-9)가 식별되었고, 단독 사유 **CD-1(ledger_path가 `{loop_id}/ledger.jsonl` 디렉터리가 아닌 `{loop_id}.jsonl` flat 파일)** 때문에 STEP9_PATCH_REQUIRED 판정이 났다. Step 10(R3 base WM smoke real run) 진입을 차단하는 사유이므로 본 Step 9.5에서 해소해야 한다.

또한 Step 9 dry-run에서 신규 발견된 **CD-9(loop_id 초 단위 정밀도로 동시 실행 시 collision)** 도 함께 처리하면 Step 10 real run에서 동시 run 안정성을 미리 확보할 수 있다. STEP9_PATCH_PLAN.md §1에서 CD-1과 CD-9 패치를 동반하도록 이미 권장되어 있다.

CD-6(LEDGER_SCHEMA.md Optional Fields 섹션) + CD-7(`--max-wall-clock` typo)은 doc 수정만 필요하므로 Codex 위임 없이 Main Claude가 직접 처리한다. step9_validate.py 임시 파일은 untracked 상태로 남아 있어 git 영향은 없으나 정리한다.

CD-2(per-iter artifact 4종), CD-3(gate_threshold field), CD-4(id_nll gate 0.4→0.5), CD-5(--dry-run help text), CD-8(smoke_4060.yaml hyperparam)는 본 Step 9.5에서 제외한다(이전 결정 — CD-2/CD-8은 Step 10 real run에서 자연스럽게 동반 패치, CD-3/CD-4/CD-5는 LOW 우선순위).

---

## A. Step 9.5 목적

1. **CD-1 패치**: `src/fglc/repair/orchestrator.py:229-230`와 `scripts/fglc/repair_loop.py:155-157`의 ledger_path를 `outputs/repair/{loop_id}/ledger.jsonl` 디렉터리 구조로 변경. 연관 테스트 수정.
2. **CD-9 패치**: `src/fglc/repair/ledger.py::build_loop_id()`에 `uuid.uuid4().hex[:4]` suffix 추가 (`loop_YYYY-MM-DDTHH-MM-SS-{4hex}`). collision 위험 제거.
3. **CD-6 doc 수정 (Main Claude)**: `docs/EXPERIMENT_LEDGER_SCHEMA.md`에 "Optional Fields" 섹션 추가. REQUIRED_KEYS 외 예시 필드(`oom_fallbacks_applied`, `candidate_*`, `epsilon_*`, `early_stop_*`, `result_reason`, `notes`, `gate_threshold`)를 분리.
4. **CD-7 doc 수정 (Main Claude)**: `docs/ROADMAP/4060_SMOKE_REPAIR_PATH.md` L151 `--max-wall-clock 240` → `--max-wall-clock-minutes 240` typo 수정.
5. **임시 파일 정리**: `step9_validate.py` 삭제 (필요 시 user-mode 권한으로 재시도).
6. **재검증**: 회귀 테스트 65+ passed 유지, Step 9 D.1 dry-run 7 시나리오 전체 재실행, 디렉터리 구조 검증, ledger 19 REQUIRED_KEYS 통과.
7. **판정**: STEP9.5_PASS / STEP9.5_PATCH_FAILED. PASS 시 Step 10 진입 허가.

**비목적 (이 Step에서 안 함)**:
- CD-2 per-iter artifact 4종 생성 → Step 10 R3 runner 작성 시 동반 구현
- CD-3 gate_threshold ledger field → LEDGER_SCHEMA.md REQUIRED_KEYS 자체 정합 필요, defer
- CD-4 id_nll gate 0.4→0.5 → Step 10 R3 실측 후 재조정
- CD-5 --dry-run help text → Step 10에서 real-run mode 분리 시 동시 처리
- CD-8 smoke_4060.yaml K/h_dim/batch 권장값 → Step 10 진입 직전
- R3 encoder/dynamics/heads 구현 → Step 10 별도 plan
- 실제 ManiSkill 학습 실행
- phase gate sentinel 생성

---

## B. CD-1 패치 명세 (Codex TASK_2032 위임)

### B.1 변경 위치 1: `src/fglc/repair/orchestrator.py:229-230`

**현재**:
```python
ledger_path = cfg.output_root / f"{loop_id}.jsonl"
cfg.output_root.mkdir(parents=True, exist_ok=True)
```

**변경 후**:
```python
loop_dir = cfg.output_root / loop_id
loop_dir.mkdir(parents=True, exist_ok=True)
ledger_path = loop_dir / "ledger.jsonl"
```

### B.2 변경 위치 2: `scripts/fglc/repair_loop.py:155-157`

**현재**:
```python
"ledger_path": str(
    cfg.output_root / f"{final.ledger_line['loop_id']}.jsonl"
),
```

**변경 후**:
```python
"ledger_path": str(
    cfg.output_root / final.ledger_line["loop_id"] / "ledger.jsonl"
),
```

### B.3 변경 위치 3: `tests/test_fglc_repair_orchestrator.py:72-74`

**현재** (`_records()` helper):
```python
def _records(output_root):
    ledger_path = next(output_root.glob("*.jsonl"))
    return [json.loads(line) for line in ledger_path.read_text(encoding="utf-8").splitlines()]
```

**변경 후** (recursive glob으로 디렉터리 구조 대응):
```python
def _records(output_root):
    ledger_path = next(output_root.glob("*/ledger.jsonl"))
    return [json.loads(line) for line in ledger_path.read_text(encoding="utf-8").splitlines()]
```

### B.4 `tests/test_fglc_repair_loop_cli.py` 영향

`test_cli_smoke_improve()` L43은 `Path(payload["ledger_path"]).exists()`로 stdout payload만 확인하므로 CLI 측 패치(B.2)가 적용되면 자동 통과. 추가 수정 불필요.

---

## C. CD-9 패치 명세 (Codex TASK_2032 위임, 동일 task)

### C.1 변경 위치: `src/fglc/repair/ledger.py::build_loop_id()`

**현재** (추정 — `STEP9_PATCH_PLAN.md` §2에서 명시):
```python
def build_loop_id(now=None):
    if now is None:
        now = datetime.now(timezone.utc).replace(microsecond=0)
    return f"loop_{now.strftime('%Y-%m-%dT%H-%M-%S')}"
```

**변경 후**:
```python
import uuid

def build_loop_id(now=None):
    if now is None:
        now = datetime.now(timezone.utc).replace(microsecond=0)
    suffix = uuid.uuid4().hex[:4]
    return f"loop_{now.strftime('%Y-%m-%dT%H-%M-%S')}-{suffix}"
```

### C.2 연관 테스트: `tests/test_fglc_repair_ledger.py`

`build_loop_id()` 형식 검증 테스트가 존재하면 새로운 `loop_YYYY-MM-DDTHH-MM-SS-{4hex}` regex 패턴으로 업데이트. Codex가 파일 내용을 확인 후 수정.

---

## D. Codex TASK_2032 명세

### D.1 TASK 파일 경로

`.agent_tasks/codex_queue/TASK_2032_fglc_step9_5_ledger_path_and_loop_id_patch.md`

### D.2 10개 필수 헤더 + 1개 선택 헤더

```
TASK_NAME: TASK_2032_fglc_step9_5_ledger_path_and_loop_id_patch

BACKGROUND:
  Step 9 정적 감사 및 dry-run에서 발견된 2개 계약 불일치 패치.
  CD-1: orchestrator.py:229와 repair_loop.py:155-157이 docs/EXPERIMENT_LEDGER_SCHEMA.md
        L5,22의 계약(outputs/repair/{loop_id}/ledger.jsonl)과 다르게 flat 경로
        (outputs/repair/{loop_id}.jsonl)를 사용함.
  CD-9: build_loop_id()가 초 단위 정밀도로 loop_id를 생성하여 동일 초에 2 run 실행 시
        같은 파일에 ledger line 혼입. STEP9_DRY_RUN_REPAIR_LOOP_REPORT.md §5에서 실측 확인.
  관련 report: docs/STEP9_PATCH_PLAN.md §1, §2.

GOAL:
  CD-1: ledger_path를 outputs/repair/{loop_id}/ledger.jsonl 계층 구조로 수정.
  CD-9: loop_id에 uuid4 4-hex suffix 추가 (loop_YYYY-MM-DDTHH-MM-SS-{4hex}).

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
  src/fglc/schemas/
  src/fglc/repair/taxonomy.py
  src/fglc/repair/compare.py
  src/fglc/repair/diagnose.py
  src/fglc/repair/candidates.py
  src/fglc/repair/ranker.py
  configs/fglc/smoke_4060.yaml

REQUIRED_IMPLEMENTATION:
  1. src/fglc/repair/orchestrator.py run_repair_loop() 내 (L229-230):
     - 현재: ledger_path = cfg.output_root / f"{loop_id}.jsonl"; cfg.output_root.mkdir(...)
     - 변경: loop_dir = cfg.output_root / loop_id; loop_dir.mkdir(parents=True, exist_ok=True);
             ledger_path = loop_dir / "ledger.jsonl"
  2. scripts/fglc/repair_loop.py main() stdout JSON (L155-157):
     - 현재: cfg.output_root / f"{final.ledger_line['loop_id']}.jsonl"
     - 변경: cfg.output_root / final.ledger_line["loop_id"] / "ledger.jsonl"
  3. src/fglc/repair/ledger.py build_loop_id():
     - 변경: uuid.uuid4().hex[:4] suffix 추가 → "loop_YYYY-MM-DDTHH-MM-SS-{4hex}"
     - import uuid 추가 필요
  4. tests/test_fglc_repair_orchestrator.py _records() (L72-74):
     - 변경: output_root.glob("*.jsonl") → output_root.glob("*/ledger.jsonl")
  5. tests/test_fglc_repair_ledger.py:
     - build_loop_id 형식 검증 테스트가 있으면 새 regex 패턴 (suffix 4-hex)으로 업데이트
     - 없으면 추가 (build_loop_id가 hex suffix 포함 형식 반환 확인)

REQUIRED_TESTS:
  - tests/test_fglc_repair_orchestrator.py 전체 (8 tests) PASS
  - tests/test_fglc_repair_loop_cli.py 전체 (4 tests) PASS
  - tests/test_fglc_repair_ledger.py 전체 PASS
  - tests/test_fglc_repair_*.py 전체 회귀 65+ passed 유지

ACCEPTANCE_CRITERIA:
  1. 회귀 테스트 65+ passed 유지 (CD-9 신규 테스트 추가 시 66+)
  2. orchestrator.py 변경이 정확히 B.1 명세대로 적용
  3. repair_loop.py 변경이 정확히 B.2 명세대로 적용
  4. ledger.py build_loop_id가 C.1 명세대로 uuid 4-hex suffix 포함
  5. 금지 경로(FILES_FORBIDDEN) 미수정
  6. RESULT.md 파일 생성 (.agent_tasks/codex_done/TASK_2032_fglc_step9_5_ledger_path_and_loop_id_patch_RESULT.md)
  7. 변경된 파일 5~6개만 staged (orchestrator.py + ledger.py + repair_loop.py + test_orchestrator + test_ledger + 선택적으로 test_loop_cli)

COMMIT_MESSAGE:
  fix(repair): correct ledger path to {loop_id}/ledger.jsonl + add uuid suffix to loop_id (CD-1, CD-9)

STOP_CONDITION:
  - 65 passed 미달
  - 금지 경로 수정 발견
  - build_loop_id 변경이 외부 호출자(orchestrator)와 incompatible
  - timeout 30분 초과

RELATED_AGENT_REPORT_IDS:
  (T3 implementation-risk-critic report는 verify 후 docs/orchestration/agent_reports/2026-05/impl_risk_TASK_2032_R1.md 경로로 생성 예정)
```

### D.3 실행 명령

```powershell
.\scripts\run_codex_task.ps1 `
  -Mode run `
  -TaskName TASK_2032_fglc_step9_5_ledger_path_and_loop_id_patch `
  -TaskFile .agent_tasks\codex_queue\TASK_2032_fglc_step9_5_ledger_path_and_loop_id_patch.md `
  -BypassSandbox
```

### D.4 6-Gatekeeper 체크포인트

Codex 결과 accept 전 반드시 6개 조건 모두 충족:

1. ✅ verify mode exit 0
2. ✅ `git diff --cached` 수동 review — 의도된 변경만
3. ✅ FILES_FORBIDDEN 미수정 확인 (`git diff --cached --name-only` 점검)
4. ✅ `.agent_tasks/codex_done/TASK_2032_..._RESULT.md` 존재
5. ✅ REQUIRED_TESTS 통과 재확인 (`pytest -q tests/test_fglc_repair_*.py`)
6. ✅ T3 implementation-risk-critic agent report PASS

하나라도 실패 시 → `git merge --abort` → STEP9.5_PATCH_FAILED.

---

## E. Main Claude 직접 처리 (Codex 위임 없음)

### E.1 CD-6 doc 수정: `docs/EXPERIMENT_LEDGER_SCHEMA.md`

REQUIRED_KEYS(19개) 외에 schema 예시에 등장하는 필드들을 "## Optional Fields" 섹션으로 분리한다.

**예상 위치**: REQUIRED_KEYS 정의 직후 또는 schema 예시 직후에 신규 섹션 삽입.

**섹션 내용 골격**:
```markdown
## Optional Fields

REQUIRED_KEYS에 포함되지 않지만 schema 예시에 등장하는 필드들. 구현체가 기록할 수 있으나
필수는 아니며, validate_ledger_line()은 누락을 허용한다.

| 필드 | 설명 | 출처 |
|---|---|---|
| `gate_threshold` | 현재 phase의 gate threshold 값 (e.g., id_nll ≤ 0.5) | diagnose 추적성 |
| `candidate_cost_minutes` | candidate_chosen.cost_minutes의 flat alias | 예시 호환 |
| `candidate_risk` | candidate_chosen.risk의 flat alias | 동 |
| `candidate_expected_signal` | candidate_chosen.expected_signal의 flat alias | 동 |
| `candidate_rank_score` | ranker.rank() 결과의 점수 | 분석 보조 |
| `oom_fallbacks_applied` | OOM 복구 fallback 적용 횟수 | Step 10+ runner 메타 |
| `epsilon_accept`, `epsilon_reject`, `epsilon_secondary` | compare.py 임계값 echo | 재현성 |
| `early_stop_*` | 조기 종료 메타 | Step 10+ trainer |
| `result_reason` | result 결정의 사유 텍스트 | 분석 보조 |
| `notes` | 자유 텍스트 메모 | 분석 보조 |
```

정확한 필드 목록은 LEDGER_SCHEMA.md 현재 schema 예시 read 후 확정.

### E.2 CD-7 doc 수정: `docs/ROADMAP/4060_SMOKE_REPAIR_PATH.md:L151`

**현재** (추정):
```
... --max-wall-clock 240 ...
```

**변경 후**:
```
... --max-wall-clock-minutes 240 ...
```

Edit 도구로 한 줄 정확히 수정.

### E.3 임시 파일 정리: `step9_validate.py`

```powershell
Remove-Item step9_validate.py -ErrorAction SilentlyContinue
```

권한 거부 시 PASS 보고서에 "untracked, no git impact"로 명기. 강제 삭제 시도하지 않음.

---

## F. 재검증 절차

### F.1 회귀 테스트 (Codex accept 직후)

```powershell
.\.venv\Scripts\python.exe -m pytest -q `
  tests\test_fglc_repair_taxonomy.py `
  tests\test_fglc_repair_compare.py `
  tests\test_fglc_repair_ledger.py `
  tests\test_fglc_repair_diagnose.py `
  tests\test_fglc_repair_candidates.py `
  tests\test_fglc_repair_ranker.py `
  tests\test_fglc_repair_orchestrator.py `
  tests\test_fglc_repair_loop_cli.py
```

**기대**: 65+ passed (CD-9 신규 테스트 추가 시 66+).

### F.2 dry-run 7 시나리오 재실행 (Step 9 D.1 동일 명령)

```powershell
# (1) improve
.\.venv\Scripts\python.exe scripts\fglc\repair_loop.py --phase R3 --config configs\fglc\smoke_4060.yaml --descriptor smoke --mock-scenario improve --max-iter 2 --output-root outputs\repair

# (2) reject
.\.venv\Scripts\python.exe scripts\fglc\repair_loop.py --phase R3 --config configs\fglc\smoke_4060.yaml --descriptor smoke --mock-scenario reject --max-iter 1 --output-root outputs\repair

# (3) inconclusive
.\.venv\Scripts\python.exe scripts\fglc\repair_loop.py --phase R3 --config configs\fglc\smoke_4060.yaml --descriptor smoke --mock-scenario inconclusive --max-consecutive-inconclusive 1 --max-iter 3 --output-root outputs\repair

# (4) target_reached
.\.venv\Scripts\python.exe scripts\fglc\repair_loop.py --phase R3 --config configs\fglc\smoke_4060.yaml --descriptor smoke --mock-scenario target_reached --max-iter 2 --output-root outputs\repair

# (5) max_iter
.\.venv\Scripts\python.exe scripts\fglc\repair_loop.py --phase R3 --config configs\fglc\smoke_4060.yaml --descriptor smoke --mock-scenario max_iter --max-iter 1 --output-root outputs\repair

# (6) hook_blocked
.\.venv\Scripts\python.exe scripts\fglc\repair_loop.py --phase R3 --config configs\fglc\smoke_4060.yaml --descriptor smoke --mock-scenario hook_blocked --output-root outputs\repair

# (7) no_candidate
.\.venv\Scripts\python.exe scripts\fglc\repair_loop.py --phase R3 --config configs\fglc\smoke_4060.yaml --descriptor smoke --mock-scenario no_candidate --output-root outputs\repair
```

**각 명령 직후 검증**:
- exit code == 0
- stdout JSON parse 가능 + 5 key 존재
- payload["ledger_path"] 파일 존재
- payload["ledger_path"]가 `outputs/repair/loop_YYYY-MM-DDTHH-MM-SS-{4hex}/ledger.jsonl` 형식 (CD-1 + CD-9 확인)

### F.3 디렉터리 구조 확인

```powershell
Get-ChildItem outputs\repair -Recurse | Select-Object FullName, Length
```

**기대 구조**:
```
outputs/repair/
  .gitkeep
  loop_2026-05-23T<HHMMSS>-{abcd}/
    ledger.jsonl
  loop_2026-05-23T<HHMMSS>-{efgh}/
    ledger.jsonl
  ...
```

7개 시나리오 → 7개 loop 디렉터리 (CD-9로 인해 동일 초 collision 없음).

### F.4 Ledger REQUIRED_KEYS 검증

기존 step9_validate.py를 디렉터리 구조 대응으로 재작성하거나 inline Python으로:

```powershell
.\.venv\Scripts\python.exe -c "
import json
from pathlib import Path
from fglc.repair.ledger import REQUIRED_KEYS, validate_ledger_line, VALID_RESULTS, VALID_STOP_CONDITIONS

errors = 0
for ledger in Path('outputs/repair').glob('*/ledger.jsonl'):
    for i, line in enumerate(ledger.read_text(encoding='utf-8').splitlines()):
        if not line.strip(): continue
        d = json.loads(line)
        try:
            validate_ledger_line(d)
            assert d['result'] in VALID_RESULTS
            assert d['stop_condition_hit'] in VALID_STOP_CONDITIONS or d['stop_condition_hit'] is None
            print(f'PASS {ledger.parent.name} line {i}')
        except Exception as e:
            print(f'FAIL {ledger.parent.name} line {i}: {e}')
            errors += 1
print(f'Total errors: {errors}')
"
```

**기대**: errors == 0.

### F.5 git hygiene

```powershell
git status --short
```

**기대**: tracked 변경 없음 (Codex commit이 ff-merge 후) + plan/문서 파일만 변경 (Main Claude doc 수정분).

---

## G. PASS / FAIL 판정 기준

### G.1 STEP9.5_PASS 조건 (모두 충족)

- [ ] Codex TASK_2032 verify exit 0
- [ ] 6-Gatekeeper 6개 모두 ✅
- [ ] 회귀 테스트 65+ passed
- [ ] dry-run 7 시나리오 모두 exit 0, stdout JSON 유효
- [ ] payload["ledger_path"]가 `{loop_id}/ledger.jsonl` 형식 (CD-1)
- [ ] loop_id에 4-hex suffix 포함 (CD-9)
- [ ] 7개 시나리오 → 7개 독립 loop 디렉터리 (collision 없음)
- [ ] LEDGER_SCHEMA.md Optional Fields 섹션 추가됨 (CD-6)
- [ ] 4060_SMOKE_REPAIR_PATH.md L151 typo 수정됨 (CD-7)
- [ ] git hygiene 통과

### G.2 STEP9.5_PATCH_FAILED 조건

다음 중 하나 이상:
- Codex verify exit ≠ 0
- 6-Gatekeeper 중 1개라도 ❌
- 회귀 테스트 fail
- 7 시나리오 중 1개라도 실패
- ledger_path가 여전히 flat 구조
- loop_id collision 재발

FAILED 시 → `git merge --abort` → Step 10 진입 BLOCKED → 추가 patch round 또는 사용자 보고.

---

## H. Step 10 진입 허용 조건 (Step 9.5 완료 후)

- [x] Step 9 STEP9_DRY_RUN_REPAIR_LOOP_REPORT.md 존재 (Step 9에서 작성됨)
- [ ] Step 9.5 CD-1 패치 완료 + 회귀 65+ passed
- [ ] Step 9.5 CD-9 패치 완료 + collision 해소 확인
- [ ] CD-6/CD-7 doc 수정 완료
- [ ] 7 시나리오 재실행에서 `{loop_id}/ledger.jsonl` 구조 + uuid suffix 확인
- [ ] T3 agent report PASS
- [ ] Step 9.5 RESULT.md 작성

위 7개 모두 충족 시 Step 10 R3 base WM smoke 진입 허가.

---

## I. 절대 하지 말 것 (이 Step의 비-범위)

- 실제 ManiSkill 학습 실행 금지
- R3 encoder/dynamics/world model heads 구현 금지
- `src/fglc/model/` 또는 `src/fglc/dynamics/` 신규 모듈 생성 금지
- phase gate sentinel 생성 금지 (`outputs/phase_gates/R*.passed`)
- `outputs/phase_gates/` 수정 금지
- dry-run artifact (`outputs/repair/loop_*/ledger.jsonl`) git commit 금지
- CD-2 per-iter artifact 4종 추가 금지 (Step 10에서)
- CD-3 gate_threshold ledger field 추가 금지 (LEDGER_SCHEMA REQUIRED_KEYS 정합 후)
- CD-4 id_nll gate 변경 금지 (Step 10 실측 후)
- CD-5 --dry-run help text 변경 금지 (Step 10에서)
- CD-8 smoke_4060.yaml 수정 금지 (Step 10 진입 직전)
- `src/fglc/schemas/` 수정 금지 (불변)
- `src/fglc/repair/{taxonomy,compare,diagnose,candidates,ranker}.py` 수정 금지
- `configs/fglc/smoke_4060.yaml` 수정 금지
- `.gitignore` 수정 금지
- Codex TASK_2032 외의 추가 Codex TASK 생성 금지

---

## J. 사전 점검 체크리스트 (execute 단계 진입 직전)

```
[ ] 1. plan 파일 ExitPlanMode 승인
[ ] 2. git status --short → 현재 plan 파일 + STEP9_*.md만 modified/untracked, 나머지 clean
[ ] 3. .venv\Scripts\python.exe 동작 확인
[ ] 4. .agent_tasks/codex_queue/ 비어 있음 확인 (이전 TASK 정리됨)
[ ] 5. .agent_tasks/codex_done/ 에 TASK_2032 기존 RESULT 없음 확인
[ ] 6. outputs/repair/ stale ledger 정리 (선택, .gitkeep만 남김)
       단, .gitkeep 절대 삭제 금지
```

---

## K. 실행 단계 절차 (execute 단계 시)

```
[ ] K.1  Codex TASK 파일 작성
         .agent_tasks/codex_queue/TASK_2032_fglc_step9_5_ledger_path_and_loop_id_patch.md

[ ] K.2  Codex 호출
         .\scripts\run_codex_task.ps1 -Mode run `
           -TaskName TASK_2032_fglc_step9_5_ledger_path_and_loop_id_patch `
           -TaskFile <path> -BypassSandbox

[ ] K.3  verify exit 0 확인

[ ] K.4  6-Gatekeeper 점검:
         - git diff --cached --name-only (변경 파일 ≤ 6개)
         - git diff --cached --stat (라인 변경량 합리적)
         - 금지 경로 미포함 확인
         - RESULT.md 존재 확인
         - pytest -q tests\test_fglc_repair_*.py → 65+ passed
         - T3 implementation-risk-critic agent 호출 → report PASS 확인

[ ] K.5  6개 중 1개라도 FAIL → git merge --abort → STEP9.5_PATCH_FAILED 보고
         모두 PASS → accept commit 자동 완료 (ff-merge)

[ ] K.6  Main Claude doc 수정:
         (a) docs/EXPERIMENT_LEDGER_SCHEMA.md → ## Optional Fields 섹션 추가 (CD-6)
         (b) docs/ROADMAP/4060_SMOKE_REPAIR_PATH.md L151 → --max-wall-clock-minutes typo 수정 (CD-7)

[ ] K.7  step9_validate.py 정리
         Remove-Item step9_validate.py -ErrorAction SilentlyContinue
         (권한 거부 시 skip + 보고서에 명기)

[ ] K.8  7 시나리오 dry-run 재실행 (F.2)
         각 명령 직후:
         - exit code 0 확인
         - stdout JSON parse
         - payload["ledger_path"] 형식 검증 ({loop_id}/ledger.jsonl)
         - loop_id에 4-hex suffix 존재 확인

[ ] K.9  Get-ChildItem outputs\repair -Recurse | Format-Table Name, FullName
         디렉터리 구조 시각 확인 (CD-1 해소 증거)

[ ] K.10 Ledger REQUIRED_KEYS inline 검증 (F.4)
         errors == 0 확인

[ ] K.11 git hygiene:
         git status --short
         tracked 변경 = doc 2개 파일만 (CD-6, CD-7), Codex commit은 이미 merged

[ ] K.12 판정 결정:
         - 모두 PASS → STEP9.5_PASS → Step 10 진입 허가
         - 1개라도 FAIL → STEP9.5_PATCH_FAILED → 사용자 보고 + 다음 라운드

[ ] K.13 산출 문서 작성:
         docs/STEP9_5_PATCH_RESULT_REPORT.md
         - Codex TASK_2032 verify 결과
         - 6-Gatekeeper 6개 결과
         - 회귀 65+ passed 증거
         - 7 시나리오 재실행 결과 표
         - 디렉터리 구조 출력
         - ledger REQUIRED_KEYS 검증 결과
         - doc 수정 diff (CD-6, CD-7)
         - 판정: STEP9.5_PASS 또는 FAILED
         - Step 10 진입 권고

[ ] K.14 사용자에게 결과 보고 + Step 10 plan 요청 대기
```

---

## L. BLOCKER 시나리오 + 대응

| # | 시나리오 | 대응 |
|---|---|---|
| BL1 | Codex sandbox lock issue 재발 | -BypassSandbox 확인 + run_codex_task.ps1 exit code 10 디버깅 |
| BL2 | Codex가 FILES_FORBIDDEN 수정 시도 | exit code 40 → 자동 abort → 사용자 보고 |
| BL3 | Codex가 build_loop_id 변경했으나 외부 호출자 break | pytest fail → exit 40 → abort |
| BL4 | uuid import 누락으로 ImportError | Codex RESULT.md에서 빠진 import 식별 → 추가 round |
| BL5 | test_records glob 패턴 변경 후에도 test fail | _records() helper 외 다른 ledger 경로 참조 존재 가능 → 사용자 보고 |
| BL6 | T3 agent report FAIL | report 내용 검토 후 추가 round 또는 Step 9.6 plan |
| BL7 | dry-run 7 시나리오 중 일부 collision 재발 | uuid.uuid4().hex[:4] 충돌 가능성 (1/65536) → suffix 길이 6~8로 확장 검토 |
| BL8 | CD-6 doc 수정 시 LEDGER_SCHEMA.md 현재 구조와 충돌 | Read 후 적절한 삽입 위치 재결정 |

---

## M. 큰 그림 (Step 9 → Step 9.5 → Step 10)

```
Step 9 (완료):
  control plane 정적 + 동적 검증
  9개 계약 불일치 식별 (CD-1~CD-9)
  판정: STEP9_PATCH_REQUIRED (CD-1 단독 사유)
  산출: STEP9_DRY_RUN_REPAIR_LOOP_REPORT.md + STEP9_PATCH_PLAN.md

Step 9.5 (이 plan):
  Codex TASK_2032: CD-1 (ledger path) + CD-9 (uuid suffix) 패치
  Main Claude: CD-6 (Optional Fields), CD-7 (typo) doc 수정
  cleanup: step9_validate.py 삭제
  재검증: 회귀 65+ passed + 7 시나리오 dry-run + 디렉터리 구조 + ledger 검증
  산출: STEP9_5_PATCH_RESULT_REPORT.md
  판정: STEP9.5_PASS → Step 10 진입 허가

Step 10 (별도 plan):
  R3 base WM 구현 (encoder + dynamics + heads)
  ManiSkill state-only PickCube 데이터 로더
  real RunnerOutput 생성기 (mock 대체)
  CD-2 (iter_{N}/ artifact 4종) 동반 구현
  CD-3 (gate_threshold field) 동반 결정
  CD-4 (id_nll gate 0.4↔0.5) 실측 후 결정
  CD-5 (--dry-run help text) real-run mode 분리 시
  CD-8 (smoke_4060.yaml K=6, h_dim=128, batch=16) 업데이트
  4060 8GB VRAM 한계 확인
  dry-run 1 epoch smoke + real smoke
  R3 phase gate sentinel (R3.passed) 생성
```

이 Step 9.5는 Step 9(검증 완료)과 Step 10(R3 real run) 사이의 **계약 정합 패치 단계**이며, **Codex 단일 TASK + Main Claude doc 동반 수정**이 본질이다.

---

## N. 검증 (plan ↔ 사용자 의도 정합)

1. **CD-1 + CD-9 통합 패치** — 사용자 결정에 따라 단일 TASK_2032에 통합. B/C/D 절에 명시.
2. **CD-6 + CD-7 doc 수정 Main Claude 직접 처리** — E 절. Codex TASK와 분리.
3. **step9_validate.py 정리 포함** — E.3.
4. **회귀 + 7 시나리오 dry-run 재실행** — F.1 + F.2. 사용자 결정에 따라 전체 7 시나리오.
5. **6-Gatekeeper 명시** — D.4.
6. **Step 10 진입 조건 명시** — H 절.
7. **비-범위 명시** — I 절. CD-2/3/4/5/8 제외 사유 명확.
8. **BLOCKER 시나리오 대비** — L 절.
9. **plan ONLY** — execute 시 K 절 순서대로 진행, 본 plan 파일 외 어떤 파일도 본 plan에서 수정하지 않음.
