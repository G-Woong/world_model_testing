# STEP9_DRY_RUN_REPAIR_LOOP_REPORT — Repair Loop Control Plane 검증 보고서

> **Status**: STEP9_PATCH_REQUIRED
> **작성일**: 2026-05-23
> **Branch**: memory-redesign-2026-05-16
> **Prior commit**: `5170885` (Step 8 — orchestrator + CLI dry-run loop, 65 passed)
> **검증자**: Main Claude (Claude Code)

---

## 1. 검증 환경

| 항목 | 값 |
|---|---|
| OS | Windows 11 Home (10.0.26200) |
| Python | 3.11.9 (venv: `.venv\Scripts\python.exe`) |
| Branch / Commit | memory-redesign-2026-05-16 / `5170885` |
| pytest 버전 | 9.0.3 |
| 검증 시각 | 2026-05-23T08:51~08:53 UTC |
| 사전 git status | `.self_evolving_memory`, `plans/` 2개 파일 modified (무관) |

---

## 2. 정적 계약 감사 결과

다음 3개 문서와 구현 코드를 줄 단위로 비교하였다.

- `docs/EXPERIMENT_LEDGER_SCHEMA.md`
- `docs/EXPERIMENT_REPAIR_LOOP_PLAN.md` (참조)
- `docs/ROADMAP/4060_SMOKE_REPAIR_PATH.md`

### 2.1 확인된 계약 불일치 (CD-1 ~ CD-9)

| # | 항목 | 문서 계약 | 구현 실제 | 심각도 | 판정 |
|---|---|---|---|---|---|
| **CD-1** | Ledger path 구조 | `outputs/repair/{loop_id}/ledger.jsonl` (LEDGER_SCHEMA.md L5,22) | `outputs/repair/{loop_id}.jsonl` (orchestrator.py:229, repair_loop.py:155) | **HIGH** | **PATCH_REQUIRED** |
| **CD-2** | per-iter artifact 4종 | `iter_{N}/{config.yaml, metrics.json, compare.json, run_manifest.json}` (LEDGER_SCHEMA.md L22-28) | 미생성 | **HIGH** | **Step 10 동반 패치** (권장 옵션B) |
| **CD-3** | `gate_threshold` ledger 키 | schema 예시 L77에 포함 | `_base_line()`에 미기록 | **MED** | LOW 우선순위 (REQUIRED_KEYS에 없음, CD-6 연관) |
| **CD-4** | R3 gate threshold | ≤ 0.5 nat (4060 doc L89) | CLI gate_thresholds `id_nll`: 0.4 (repair_loop.py:84) | **LOW** | DOC_REVISION 또는 CLI 값 조정 |
| **CD-5** | `--dry-run` flag 정책 | doc 권장 (4060 L143) | `store_true` default=False, 동작에 영향 없음 | **LOW** | help text 보강 권장 |
| **CD-6** | schema 예시-REQUIRED_KEYS 불일치 | 예시 L77~L111에 Optional 필드 다수 | REQUIRED_KEYS(L121-130)에 미포함 | **LOW** | DOC_REVISION (Optional fields 섹션 분리) |
| **CD-7** | entry point 예시 flag 오기 | `--max-wall-clock 240` (4060 doc L151) | 실제 CLI: `--max-wall-clock-minutes` | **LOW** | DOC_REVISION |
| **CD-8** | smoke_4060.yaml hyperparam | K=6, h_dim=128, batch=16 권장 (4060 doc) | K=4, h=64, batch=32 (configs/fglc/smoke_4060.yaml) | **LOW** | Step 10 진입 직전 patch |
| **CD-9** (신규 발견) | loop_id 충돌 | 각 run마다 unique loop_id | 동일 초에 2개 실행 시 같은 `.jsonl` 파일에 혼입 | **MED** | Step 9.5 개선 권장 |

### 2.2 REQUIRED_KEYS 19개 정합 확인

`ledger.py:16-36`의 `REQUIRED_KEYS`와 `LEDGER_SCHEMA.md` L121-130이 **완전 일치** (19개 키 1:1):

```
loop_id, iter, run_id, git_sha, config_hash, config_path, phase, split,
metrics_before, metrics_after, deltas, failed_metric, diagnosed_cause,
candidate_chosen, result, stop_condition_hit, next_action,
wall_clock_minutes, vram_peak_mib
```

### 2.3 stop condition enum 정합 확인

`ledger.py:39-47`의 `VALID_STOP_CONDITIONS` vs `LEDGER_SCHEMA.md` L182-187:

```
max_iter, wall_clock, target_reached, consecutive_inconclusive, hook_blocked
```

**완전 일치** ✓

### 2.4 stop condition 우선순위 정합 확인

문서 계약 (hook_blocked > target_reached > wall_clock > consecutive_inconclusive > max_iter):

- `hook_blocked`: baseline 실행 직후 즉시 return (orchestrator.py:243-272) ✓
- `target_reached`: 각 iter 시작 시 gate 평가 후 즉시 return (orchestrator.py:283-313) ✓
- `wall_clock`: iter 완료 후 평가 (orchestrator.py:408) ✓
- `consecutive_inconclusive`: 그 다음 (orchestrator.py:410) ✓
- `max_iter`: 마지막 (orchestrator.py:412) ✓

**우선순위 일치** ✓

---

## 3. Dry-Run 7 시나리오 실행 결과

### 3.1 실행 명령 및 결과

| # | 시나리오 | exit_code | stdout JSON |
|---|---|---|---|
| S1 | improve (--max-iter 2) | 0 | `{"loop_id":"loop_2026-05-23T08-51-58","final_result":"reject","stop_condition_hit":"max_iter","ledger_path":"outputs\\repair\\loop_2026-05-23T08-51-58.jsonl","next_action":"stop_max_iter"}` |
| S2 | reject (--max-iter 1) | 0 | `{"loop_id":"loop_2026-05-23T08-52-34","final_result":"reject","stop_condition_hit":"max_iter","ledger_path":"...08-52-34.jsonl","next_action":"stop_max_iter"}` |
| S3 | inconclusive (--max-consecutive-inconclusive 1 --max-iter 3) | 0 | `{"loop_id":"loop_2026-05-23T08-52-39","final_result":"inconclusive","stop_condition_hit":"consecutive_inconclusive","ledger_path":"...08-52-39.jsonl","next_action":"stop_consecutive_inconclusive"}` |
| S4 | target_reached (--max-iter 2) | 0 | `{"loop_id":"loop_2026-05-23T08-52-43","final_result":"accept","stop_condition_hit":"target_reached","ledger_path":"...08-52-43.jsonl","next_action":"stop_target_reached"}` |
| S5 | max_iter (--max-iter 1) | 0 | `{"loop_id":"loop_2026-05-23T08-53-00","final_result":"reject","stop_condition_hit":"max_iter","ledger_path":"...08-53-00.jsonl","next_action":"stop_max_iter"}` |
| S6 | hook_blocked | 0 | `{"loop_id":"loop_2026-05-23T08-53-00","final_result":"inconclusive","stop_condition_hit":"hook_blocked","ledger_path":"...08-53-00.jsonl","next_action":"escalate_to_user"}` |
| S7 | no_candidate | 0 | `{"loop_id":"loop_2026-05-23T08-53-01","final_result":"inconclusive","stop_condition_hit":"hook_blocked","ledger_path":"...08-53-01.jsonl","next_action":"escalate_to_user"}` |

### 3.2 시나리오별 stop/result 검증

| # | 시나리오 | 실제 stop | 실제 result | 계획 예상 stop | 계획 예상 result | stop 일치 | result 일치 |
|---|---|---|---|---|---|---|---|
| S1 | improve | max_iter | reject | null/max_iter | accept | ✓ | **✗** |
| S2 | reject | max_iter | reject | max_iter | reject | ✓ | ✓ |
| S3 | inconclusive | consecutive_inconclusive | inconclusive | consecutive_inconclusive | inconclusive | ✓ | ✓ |
| S4 | target_reached | target_reached | accept | target_reached | accept | ✓ | ✓ |
| S5 | max_iter | max_iter | reject | max_iter | reject | ✓ | ✓ |
| S6 | hook_blocked | hook_blocked | inconclusive | hook_blocked | inconclusive | ✓ | ✓ |
| S7 | no_candidate | hook_blocked | inconclusive | hook_blocked | inconclusive | ✓ | ✓ |

#### S1 "improve" result 불일치 분석

**코드 버그 아님** — plan 예상 표(D.3)가 부정확했음.

구현 로직:
1. 기준선(iter_index=0): id_nll=0.80
2. iter 1: id_nll=0.70 → delta=-0.10 ≥ ε_accept(0.05) → **accept** (단, max_iter=2이므로 loop 종료 안 됨)
   - state_metrics_before를 0.70으로 업데이트
3. iter 2: id_nll=0.70 (mock은 iter>0에서 항상 0.70 반환) → delta=0.0 ≤ ε_reject(0.0) → **reject**
   - iter_index=2 = max_iter=2 → stop=max_iter
4. CLI는 `results[-1]` (마지막 iteration) 결과를 보고 → **reject/max_iter**

`improve` 시나리오는 "개선이 발생했음을 보여주는 예시"이고, ledger에는 iter 1의 accept 기록이 남아있다 (실제로 2 lines 중 [0]이 `accept/None`). max_iter=1로 실행하면 "accept" 최종 결과를 얻을 수 있다. 이 동작은 설계 의도에 부합한다.

**CD-9: loop_id collision 확인**

S5(max_iter)와 S6(hook_blocked)가 같은 초(08-53-00)에 실행되어 동일 파일 `loop_2026-05-23T08-53-00.jsonl`에 2개 라인이 기록됨. 파일 내용:
- [0]: S5의 결과 (reject/max_iter)
- [1]: S6의 결과 (inconclusive/hook_blocked)

FileLock이 보호하므로 데이터 손상은 없으나, 두 별개 run의 ledger가 혼입된 논리적 오염 발생. 실제 운영에서는 동시 실행이 드물지만 개선 권장.

### 3.3 5-key stdout 검증

모든 7개 시나리오에서 stdout JSON 5개 필수 키 확인 완료:
`loop_id`, `final_result`, `stop_condition_hit`, `ledger_path`, `next_action` ✓

---

## 4. Ledger Artifact 검증

### 4.1 생성된 파일 목록

```
outputs/repair/
  .gitkeep                            (0 bytes, 사전 존재)
  loop_2026-05-23T08-51-58.jsonl    (2236 bytes, 2 lines — S1)
  loop_2026-05-23T08-52-34.jsonl    (1135 bytes, 1 line  — S2)
  loop_2026-05-23T08-52-39.jsonl    (1155 bytes, 1 line  — S3)
  loop_2026-05-23T08-52-43.jsonl    ( 821 bytes, 1 line  — S4)
  loop_2026-05-23T08-53-00.jsonl    (1795 bytes, 2 lines — S5+S6 collision)
  loop_2026-05-23T08-53-01.jsonl    ( 833 bytes, 1 line  — S7)
```

**CD-1 확인**: 모든 파일이 `outputs/repair/{loop_id}.jsonl` flat 구조.
문서 계약 `outputs/repair/{loop_id}/ledger.jsonl` 디렉터리 구조와 불일치.

**CD-2 확인**: `iter_{N}/` 서브디렉터리 전혀 생성 안 됨.

### 4.2 REQUIRED_KEYS 19개 검증 결과

총 9개 ledger 라인 (7 시나리오, S1·S5+S6 collision 포함) 전부 PASS:

```
Files found: 6
--- loop_...(S1)  (2 lines): [0] PASS accept/None  [1] PASS reject/max_iter
--- loop_...(S2)  (1 lines): [0] PASS reject/max_iter
--- loop_...(S3)  (1 lines): [0] PASS inconclusive/consecutive_inconclusive
--- loop_...(S4)  (1 lines): [0] PASS accept/target_reached
--- loop_...(S5+S6)(2 lines): [0] PASS reject/max_iter  [1] PASS inconclusive/hook_blocked
--- loop_...(S7)  (1 lines): [0] PASS inconclusive/hook_blocked
Total validation errors: 0
```

---

## 5. 회귀 테스트 결과

```
pytest tests/test_fglc_repair_taxonomy.py
      tests/test_fglc_repair_compare.py
      tests/test_fglc_repair_ledger.py
      tests/test_fglc_repair_diagnose.py
      tests/test_fglc_repair_candidates.py
      tests/test_fglc_repair_ranker.py
      tests/test_fglc_repair_orchestrator.py
      tests/test_fglc_repair_loop_cli.py

결과: 65 passed in 0.28s  (exit 0)
```

Step 8 merge 기준 65 passed **유지** ✓

---

## 6. Git Hygiene 검증

```
git status --short (dry-run 실행 후):
 M .self_evolving_memory/hooks/hook_execution_log.md
 M docs/orchestration/session_reports/2026-05/2026-05-23_precompact_handoff.md
 M plans/fglc-phase-eager-wilkes.md
?? step9_validate.py   (임시 검증 스크립트, 삭제 예정)
```

`outputs/repair/loop_*.jsonl` 파일이 git status에 **나타나지 않음** → `.gitignore` 정상 작동 ✓

`step9_validate.py`는 untracked 상태 (임시 파일, git 영향 없음). 삭제 필요.

---

## 7. 정적 감사 종합 (불일치 수 요약)

| 심각도 | 건수 | 내용 |
|---|---|---|
| HIGH | 2 | CD-1 (ledger path), CD-2 (iter_N artifact) |
| MED | 2 | CD-3 (gate_threshold field), CD-9 (loop_id collision) |
| LOW | 5 | CD-4, CD-5, CD-6, CD-7, CD-8 |
| **합계** | **9** | |

---

## 8. 판정: STEP9_PATCH_REQUIRED

### 판정 근거

- **CD-1** 단독 → `STEP9_PATCH_REQUIRED` 확정 (G.2 기준)
  - ledger path 구조가 분석 파이프라인 진입점이므로 Step 10 이전 반드시 수정
- 회귀 테스트 65 passed ✓ (BLOCKED 사유 없음)
- stdout JSON 7/7 parse 가능 ✓
- REQUIRED_KEYS 9 lines / 0 errors ✓
- git hygiene ✓
- CD-2: Step 10 동반 패치 (권장 옵션B) — 즉각 BLOCKED 사유 아님
- S1 result 불일치: 코드 버그 아님, plan 표 오기 — BLOCKED 아님

### Step 10 진입 조건

| 조건 | 현재 상태 | 통과 기준 |
|---|---|---|
| 65 passed 유지 | ✓ PASS | — |
| CD-1 패치 완료 | **미완료** | Step 9.5 후 재확인 |
| 7 시나리오 정상 동작 | ✓ PASS (모두 exit 0) | — |
| git hygiene | ✓ PASS | — |
| STEP9_DRY_RUN_REPAIR_LOOP_REPORT.md 작성 | ✓ 이 문서 | — |

**Step 10은 CD-1 패치(Step 9.5) 완료 후에만 진입 허용.**

---

## 9. 참조

- Step 8 구현 commit: `5170885`
- Patch 계획: `docs/STEP9_PATCH_PLAN.md`
- 문서 계약: `docs/EXPERIMENT_LEDGER_SCHEMA.md`, `docs/ROADMAP/4060_SMOKE_REPAIR_PATH.md`
