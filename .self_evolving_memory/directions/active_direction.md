# Active Direction

Last updated: 2026-05-17
Branch: `memory-redesign-2026-05-16`

## Current Focus

**Lifecycle Automation v2 — Phase 4 Safe Apply** (활성화 완료: 2026-05-17)

### Lifecycle 운영 정책

| 트리거 | 스코프 | Apply 범위 | 상태 |
|---|---|---|---|
| 일반 턴 종료 (stop hook) | changed-scope | AUTO_SAFE_TEMP + AUTO_SAFE_CACHE | **자동 활성** |
| 명시적 "턴별정리" | repo-scope | AUTO_SAFE_TEMP + AUTO_SAFE_CACHE | 수동 커맨드 |
| ARCHIVE_READY | — | preview only | 별도 승인 필요 |
| MANUAL_ONLY / UNKNOWN | — | preview only | 절대 자동 금지 |
| PROTECTED | — | 불가 | 절대 금지 |

### 자동 Apply 허용 클래스
- `AUTO_SAFE_CACHE`: `__pycache__/`, `.pytest_cache/`, `.pyc` 등 (gitignored)
- `AUTO_SAFE_TEMP`: 임시 audit 결과 파일 등 (gitignored)

### 자동 Apply 금지 클래스
- `PROTECTED`: 논문 핵심 파일, 증거 카드, evidence, phase gate
- `ARCHIVE_READY`: 이전 보고서 (별도 승인 후 git mv)
- `MANUAL_ONLY`: 코드, 설정, 문서
- `UNKNOWN`: 미분류 파일

### Protected Core 목록 (절대 건드리지 않음)
- `outputs/runs/p3_lr_eval/metrics.json`
- `evidence_cards/C*.md`
- `claim_status.json`, `ablation_results.json`
- `outputs/phase_gates/**`
- `paper_context_ref/**`, `src/frcgw/**`, `data/**`

### 사용자 역할
- `.lifecycle_trash/` 디렉토리: 주기적으로 검토 후 비우거나 restore
- ARCHIVE_READY 이동: 별도 승인 라운드에서 처리
- MANUAL_ONLY / UNKNOWN: 직접 판단 후 명시적 명령으로만 처리

## Open Blockers

### B-1: C3 LR Claim Falsification (HIGH PRIORITY — P3 gate)

- **Issue**: `planning_rate=0.0` — P3 eval에서 planning calls zero
- **Gate sentinel**: `outputs/phase_gates/P3_EVAL.BLOCKED_planning_calls_zero.md`
- **Claim**: C3은 wrong-control-grammar falsification이 recovery 향상을 유발함을 주장
- **Required before P4 (research)**: falsification signal 확인 또는 claim 수정
- **Status**: Lifecycle Phase 4 완료; C3 remediation은 다음 우선순위

## Completed (Lifecycle Track)

- [x] Phase 1: `lifecycle_audit_v2.py` dry-run 분류 엔진
- [x] Phase 2: stop hook dry-run 연결 (`stop_lifecycle_automation.ps1`)
- [x] Phase 3: `lifecycle_trash_v2.py` + `lifecycle_restore_v2.ps1` + `lifecycle_memory_promote.py`
- [x] Phase 4: safe apply 활성화 — `--allow-dirty` 추가, hook dry-run → apply 전환, 53 tests pass

## Next After This Turn

1. C3 falsification blocker 해소 (P3 gate 재평가)
2. ARCHIVE_READY 8건 이동 — 별도 승인 라운드
3. Lifecycle Phase G: ARCHIVE_READY auto git mv 정책 수립
