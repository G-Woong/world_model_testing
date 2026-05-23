# T3 Implementation Risk Audit — FGLC Repair Step 8

**보고서 경로**: `docs/orchestration/agent_reports/2026-05/impl_risk_fglc_repair_orchestrator_cli_R1.md`
**감사 기준**: Gatekeeper 5조건 (codex_orchestration_rules.md) + G1~G5 사전 위험 점검
**감사 대상**: fglc_repair_orchestrator_cli (계획 단계 — Codex 미실행)
**참조**: `plans/fglc-phase-eager-wilkes.md` Step 8 Plan, Step 5~7 산출물 6개 모듈
**Verdict**: **CONDITIONAL PASS**

---

## G1: Scope 위반 위험 — PASS (조건부)

- taxonomy/compare/ledger/diagnose/candidates/ranker 모두 import만으로 연결 가능. 로직 변경 불필요.
- `--no-dry-run`: argparse `store_true`로 `--dry-run`만 등록 시 `--no-dry-run` 자동 미제공. 위험 낮음.
- ManiSkill/torch: 6개 모듈이 stdlib + filelock만 사용. import 유입 경로 없음.

**강화 권고**: STOP_CONDITION에 "기존 6개 모듈 파일 1바이트도 수정 금지" 명시.

---

## G2: 인터페이스 충돌 위험 — PASS

- `metrics_after={}`, `deltas={}` 빈 dict: `validate_ledger_line()`이 키 존재만 검사. 통과 확인.
- `chosen=None sentinel {"id": None, "patch": None, "reason": "no_candidate"}`: 키 존재 충족. 통과.
- `stop_condition_hit=None`: 코드 `if stop_condition is not None and ...` 명시적 허용. 통과.

**WARN**: baseline hook_blocked 시 `result="inconclusive"` (not "reject") 혼란 가능.
TASK에 명시 권고: "baseline hook_blocked: result='inconclusive', stop='hook_blocked'"

---

## G3: 테스트 커버리지 위험 — WARN

- hook_blocked / target_reached / consecutive_inconclusive / max_iter: 4개 커버.
- **wall_clock: 미커버** — 5개 stop condition 중 1개 누락.
- git_sha monkeypatch: 계획에 명시되나 ACCEPTANCE_CRITERIA에 미포함.

---

## G4: Stop Condition 우선순위 위험 — WARN

- 우선순위 순차 평가로 race condition 없음.
- **HIGH 위험**: `state.metrics_before`가 baseline.metrics로 초기화되지 않으면
  target_reached 평가 시 KeyError 발생 가능.

---

## G5: Ledger Dir 생성 위험 — FAIL → MUST FIX

- `ledger.py::append_ledger_line()`이 디렉터리 자동 생성 안 함.
- orchestrator의 `mkdir(parents=True, exist_ok=True)` 필수.
- **현재 테스트 계획에서 `tmp_path` (pytest 생성 디렉터리) 사용 시 mkdir 누락 버그 탐지 불가.**
- `tmp_path / "repair_subdir"` (존재하지 않는 서브디렉터리) 사용 의무화 필요.

---

## 필수 강화 4개 (TASK 명세 반영 필수)

### [HIGH-1] Ledger Dir 생성 테스트 강화
```
모든 orchestrator 테스트에서 output_root=tmp_path / "repair_subdir"
(존재하지 않는 서브디렉터리) 사용 의무화.
orchestrator가 mkdir(parents=True, exist_ok=True)를 ledger 첫 쓰기 전에
호출하지 않으면 FileNotFoundError → 테스트 실패로 탐지.
```

### [HIGH-2] metrics_before 초기화 명시
```
state.metrics_before must be initialized to baseline.metrics (not {}) 
immediately after baseline runner call, before the main for-loop.
target_reached check at iter start uses state.metrics_before[cfg.failed_metric].
Missing key MUST NOT cause unhandled KeyError.
```

### [MED-3] wall_clock stop condition 테스트 추가
```
5개 stop condition (hook_blocked, target_reached, wall_clock,
consecutive_inconclusive, max_iter) 모두 최소 1개 테스트에서 발견되어야 함.
wall_clock 테스트: max_wall_clock_minutes=0.001, mock runner wall_clock_minutes=1.0
→ 첫 retest 후 stop="wall_clock".
```

### [MED-4] git_sha monkeypatch 의무화
```
모든 orchestrator 테스트는 git_sha_fn=lambda: "abc123" (또는 동등한 monkeypatch)
주입을 통해 실제 subprocess.run 호출을 차단해야 함.
```

---

## Gatekeeper 사전 점검 요약

| Gate | 사전 판정 | 비고 |
|---|---|---|
| G1 verify exit 0 | PENDING | Codex 미실행 |
| G2 diff review clean | PENDING | TASK FILES_ALLOWED 9개 명확 |
| G3 forbidden paths clean | PENDING | FILES_FORBIDDEN 충분히 명확 |
| G4 RESULT.md 존재 | PENDING | Codex 미실행 |
| G5 REQUIRED_TESTS PASS | PENDING | 강화 4개 반영 후 재확인 |

**Verdict: CONDITIONAL PASS — 위 4개 강화 반영 후 Codex 실행 가능.**
