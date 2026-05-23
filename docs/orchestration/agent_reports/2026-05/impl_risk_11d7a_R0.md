# implementation-risk-critic 보고서 — TASK_11D7A_COLLECTOR_PATCH

**검토 대상**: `.agent_tasks/codex_queue/TASK_11D7A_COLLECTOR_PATCH.md`
**검토일**: 2026-05-23
**검토자**: implementation-risk-critic (T3, compact mode)
**트리거**: Step 11-D7 Codex 패치 A 실행 전 T3 사전 점검
**총평**: CONDITIONAL_PASS

---

## Gatekeeper 5조건 (Codex 실행 전)

```
verify_exit_0:          N/A (Codex 실행 전 사전 검토)
diff_review_clean:      N/A
forbidden_paths_clean:  CONDITIONAL (§1 참조)
result_md_exists:       N/A
required_tests_passed:  CONDITIONAL (§2 참조)
```

---

## §1 — Scope 위반 위험 [CONDITIONAL_PASS]

- 허용 파일 8개 경계 명확. `src/fglc/schemas/`가 `FILES_FORBIDDEN`에 명시됨.
- `collector.py`는 현재 `visibility.py`를 직접 import하지 않으므로 quarantine 저장이 forbidden 파일 수정을 유발하지 않음.
- **주의**: friction 4 필드를 `build_quality_report()`에 추가하는 방식은 반드시 **방식 B** (build_split.py main()에서 dict에 직접 추가)여야 함. `manifest.py::build_quality_report()` 시그니처 변경은 REQUIRED_IMPLEMENTATION에 의해 금지됨.

---

## §2 — 테스트 커버리지 현실성 [CONDITIONAL_PASS]

- `test_all_nine_reject_reasons_in_enum` 삭제 (-1) + 신규 3개 추가 (+3) = net +2개 in `test_fglc_no_garbage_data.py`
- `test_fglc_split_integrity.py`에 신규 3개 추가 = net +3개
- 총 순증 +5개 ≥ 5 요건 충족.
- 기존 nine-test와 enum 10개 추가가 동시에 존재하면 red. 단일 커밋에서 처리되는지 확인 필요.

---

## §3 — Scope Creep 위험 [CONDITIONAL_PASS]

| 위험 | 심각도 | 설명 |
|---|---|---|
| HDF5 append 모드 | MED | quarantine 저장 시 `h5py.File(path, "w")` 사용 확인. STOP_CONDITION에 append 금지 명시됨 |
| diagnose.py 로직 변경 | LOW | `CANONICAL_METRIC_KEYS`에 키 1개 추가만. `_fire_eval_noise_high()` 내부 수정 금지 |
| seen_state_hashes module-level | MED | set은 caller가 생성/관리. validate_episode() 내부에서 module-level mutable set 금지 |

---

## §4 — validate_episode() 하위호환성 [PASS]

`seen_state_hashes: set[str] | None = None` 기본값으로 기존 호출부 모두 호환. 파괴 없음.

---

## §5 — build_split.py hash audit helper 분리 [HIGH RISK → CONDITIONAL_PASS]

**핵심 위험 항목.** 현재 TASK GOAL (4)에 "helper 분리 권장"으로 명시됨.

`main()` 내부 인라인 시 `test_fglc_split_integrity.py`에서 직접 import 불가 → 테스트 작성 방법 없음 또는 subprocess 우회 방식으로 degradation.

**필수 조치**: TASK 파일 GOAL (4)에 다음 추가:
> "hash audit 로직을 `build_split.py` 내 모듈 레벨 함수 `audit_trajectory_hashes(split_episodes: dict[str, list[dict]]) -> dict`로 반드시 분리한다. `main()` 내부 인라인 금지."

---

## 종합 위험 표

| 항목 | 심각도 | 판정 |
|---|---|---|
| forbidden_paths | LOW | CONDITIONAL |
| build_quality_report 시그니처 불변 | MED | CONDITIONAL (방식 B 명시 필요) |
| test count 기준 검증 | LOW | CONDITIONAL (collect-only 확인 권고) |
| nine→ten enum 교체 순서 | LOW | CONDITIONAL |
| hash_audit helper 분리 | HIGH | CONDITIONAL (TASK 파일 보강 필수) |
| quarantine append 모드 금지 | MED | CONDITIONAL |
| validate_episode 하위호환 | — | PASS |
| diagnose.py 키만 추가 | LOW | PASS |

---

## 수용 전 필수 확인 사항 (Codex 결과 review 시)

1. `build_split.py`에 `audit_trajectory_hashes()` 또는 동등한 **모듈 레벨 helper**가 존재하고, `test_fglc_split_integrity.py`가 해당 helper를 직접 import해서 intra/inter 테스트를 수행하는지 확인.
2. friction 4 필드가 `manifest.py::build_quality_report()` 시그니처 변경 없이 `build_split.py main()` 내에서 dict에 직접 추가되었는지 확인.
3. `h5py.File(quarantine_path, "w")` (append 아님) 확인.
4. `CANONICAL_METRIC_KEYS`에 `"eval_ci95_over_effect_size"` 1개만 추가, `_fire_eval_noise_high()` 내부 수정 없음 확인.

---

## Codex 실행 전 권고 조치 (메인 세션)

TASK 파일 GOAL (4) 마지막에 helper 분리 필수 문장 추가 후 Codex 실행.
