# T3 Implementation Risk Report — compare/ledger Step 6

> **Task**: `TASK_2026_05_23_FGLC_REPAIR_COMPARE_LEDGER.md`
> **Date**: 2026-05-23
> **Agent**: implementation-risk-critic

## Verdict: LOW_RISK (조건부 PASS)

BLOCKED 판정 사유 없음. 현재 스펙 상태에서 Codex 위임 가능.

---

## Risk Items

### RISK-1: SSoT 간 결정 로직 표현 불일치

- **Severity**: MEDIUM
- **Description**: `docs/EXPERIMENT_REPAIR_LOOP_PLAN.md §D.4`는 `|primary_delta| >= epsilon_accept` (절대값 표기)로 기술하는 반면, `docs/EXPERIMENT_LEDGER_SCHEMA.md §결정 규칙`은 direction 기반 `improvement` (부호 보정 후 비교)로 기술한다. 두 표현은 올바른 구현에서 동치지만, Codex가 §D.4를 직접 참조하면 "LOWER_BETTER metric의 negative delta에 절대값만 취해서 비교하는" 단순 구현을 작성할 수 있다. secondary delta의 direction 보정(`secondary improvement도 direction별로 부호 보정`)에 대한 test는 TASK 스펙에 명시적으로 포함되지 않아 Codex가 secondary delta를 raw delta 그대로 비교하는 구현을 낼 수 있다. 또한 test (3) `test_compare_lower_better_reject_secondary_regression`에서 secondary metric의 direction이 `metric_directions`에 명확히 지정되어야 한다.
- **Mitigation in TASK spec**: TASK 파일이 LEDGER_SCHEMA 방식을 "verbatim"으로 지정, test (4)가 HIGHER_BETTER direction을 커버. 단, secondary direction 보정에 대한 명시적 test 부재.

### RISK-2: REQUIRED_KEYS 19개 SSoT 일치 여부

- **Severity**: LOW
- **Description**: TASK 파일의 REQUIRED_KEYS 19개 목록과 `docs/EXPERIMENT_LEDGER_SCHEMA.md §필수 키 목록`의 내용이 완전히 일치한다. schema JSON 예시에는 REQUIRED_KEYS에 없는 추가 optional 필드들(`gate_threshold`, `result_reason`, 등)이 있으나 validate_ledger_line()의 검사 대상이 아니어서 안전하다.
- **Mitigation in TASK spec**: test (1) `test_required_keys_count_and_content`가 19개 수 + SSoT 목록과 1:1 비교를 명시. ACCEPTED.

### RISK-3: metric_directions 키 누락 시 ValueError 보장

- **Severity**: LOW
- **Description**: TASK 스펙에 `metric_directions[failed_metric] 누락 → ValueError` 명시. 그러나 secondary metric에 대해 `metric_directions[secondary_key]`가 누락된 경우의 처리가 명세에 없다. Codex가 silent skip하거나 KeyError를 던질 수 있다.
- **Mitigation in TASK spec**: 명시적 처리 없음. 실제 사용에서 드문 케이스이며 caller 책임 영역.

### RISK-4: secondary metric None일 때 silent skip이 schema 위반인지 여부

- **Severity**: LOW
- **Description**: TASK 스펙은 "secondary 중 한쪽이 None인 metric은 secondary delta 평가에서 skip (silent skip; 단, 그 키의 deltas 값은 None으로 기록)"으로 명시한다. `docs/EXPERIMENT_LEDGER_SCHEMA.md` JSON 예시도 `null` 케이스를 정상 상태로 보여준다. schema 위반 아님.
- **Mitigation in TASK spec**: test (7) `test_compare_skips_secondary_with_none`이 직접 검증. ACCEPTED.

### RISK-5: append_ledger_line() filelock timeout 후 raise 보장

- **Severity**: MEDIUM
- **Description**: TASK 스펙이 `with FileLock(str(lock_path), timeout=lock_timeout):` 명시. `filelock 3.25.2`는 timeout 초과 시 `filelock.Timeout` 예외 자동 raise. 그러나 Codex가 `try/except Exception: pass` 패턴으로 swallow하는 구현을 낼 가능성이 있다. timeout 발생 시 raise 여부를 test하지 않는다.
- **Mitigation in TASK spec**: 구조적으로 filelock의 기본 동작이 안전하나, ACCEPTANCE_CRITERIA에 "filelock Timeout은 반드시 호출자에게 전파" 문장 추가 시 완전해진다.

### RISK-6: compute_config_hash dict 처리 시 sort_keys=True 누락 위험

- **Severity**: LOW
- **Description**: TASK 스펙이 `json.dumps(config, sort_keys=True, ensure_ascii=False)` 명시. test (8) `test_compute_config_hash_dict_order_invariant`가 `{a:1,b:2}`와 `{b:2,a:1}` hash 동일성을 검증하여 누락 시 즉시 실패.
- **Mitigation in TASK spec**: 스펙 명시 + test 커버. ACCEPTED.

### RISK-7: build_loop_id timezone awareness (UTC) 보장

- **Severity**: LOW
- **Description**: TASK 스펙이 `datetime.now(timezone.utc)` 명시. Codex가 naive datetime을 쓸 가능성 낮음.
- **Mitigation in TASK spec**: 스펙 명시됨. ACCEPTED.

### RISK-8: .lock 파일이 tmp_path 안에서만 생성되는지 (worktree 더럽힘 방지)

- **Severity**: MEDIUM
- **Description**: lock_path는 `ledger_path.with_suffix(...)`으로 ledger 파일과 동일 디렉터리에 생성. test가 `tmp_path/ledger.jsonl`을 사용하므로 lock은 `tmp_path/ledger.jsonl.lock`으로 worktree 더럽힘 없음. 구조적으로 안전.
- **Mitigation in TASK spec**: tmp_path 사용이 ACCEPTANCE_CRITERIA에 강제됨. ACCEPTED.

### RISK-9: FILES_ALLOWED에 RESULT.md 경로 두 개 기재 (불일치)

- **Severity**: LOW
- **Description**: TASK 파일 FILES_ALLOWED에 RESULT.md 경로가 두 개: `TASK_2026_05_23_FGLC_REPAIR_COMPARE_LEDGER_RESULT.md`와 `TASK_2029_fglc_repair_compare_ledger_RESULT.md`. TASK_NAME은 `fglc_repair_compare_ledger`이므로 두 번째 경로의 `TASK_2029_` prefix는 harness 자동 번호 부여 패턴 대비용. Main Claude가 accept 시 두 경로 모두 확인해야 한다.
- **Mitigation in TASK spec**: Main Claude가 G4 gate에서 두 경로 중 하나 존재 확인으로 처리.

### RISK-10: validate_ledger_line() stop_condition_hit=None 허용 여부 모호 표현

- **Severity**: LOW
- **Description**: TASK 스펙 line 104: `stop_condition_hit이 None 또는 {"max_iter","wall_clock","target_reached","consecutive_inconclusive","hook_blocked"} 외 → LedgerSchemaError`로 읽히면 None도 LedgerSchemaError가 되어야 하지만, test (6) `test_validate_allows_none_stop_condition`은 `stop_condition_hit=None → 통과`로 명시한다. 의도: None은 허용, 열거형 외 non-None 값만 LedgerSchemaError.
- **Mitigation in TASK spec**: test (6)이 명시적 grounding 역할. test 통과가 올바른 구현을 강제. ACCEPTED.

### RISK-11: __init__.py compare/ledger re-export 없음 (의도된 설계)

- **Severity**: LOW
- **Description**: `__init__.py`가 FILES_FORBIDDEN에 포함되어 있어 Codex가 수정 불가. Step 8 orchestrator 도입 시 일괄 처리 예정.
- **Mitigation in TASK spec**: STOP_CONDITION에 명시됨. ACCEPTED.

### RISK-12: filelock 패키지 import 가능 여부

- **Severity**: LOW
- **Description**: requirements.txt에 filelock 3.25.2 핀 확인 필요하나 TASK 스펙이 "already pinned"으로 기술. smoke import 실패 시 모든 test 즉시 실패로 조기 감지.
- **Mitigation in TASK spec**: test 자가 검증. ACCEPTED.

---

## Summary

TASK 스펙 전체 구조는 건전하다. REQUIRED_KEYS 19개가 SSoT(`docs/EXPERIMENT_LEDGER_SCHEMA.md §필수 키 목록`)와 완전히 일치하며, test 13개가 핵심 계약 대부분을 커버한다.

주요 주의사항 세 가지:
1. `validate_ledger_line()` 스펙 텍스트에서 `stop_condition_hit=None` 허용 여부 표현 모호 — test (6)이 grounding 역할로 구현 강제
2. secondary metric의 direction 보정에 대한 명시적 test 부재 — test (3)이 간접 커버하나 direction이 명시되지 않음
3. RESULT.md 경로 두 개 기재 불일치 — Main Claude가 accept 시 두 경로 모두 확인 필요

치명적(CRITICAL) 위험 없음. Codex 위임 가능.
