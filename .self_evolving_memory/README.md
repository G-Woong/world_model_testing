# .self_evolving_memory/

Claude Code 지속 기억 저장소. Phase 1 skeleton (2026-05-17).

## 구조

| 경로 | 역할 |
|---|---|
| `index.yaml` | machine-readable master pointer |
| `errors/error_memory.yaml` | 오류 패턴 YAML 기록 |
| `errors/recurring_errors.md` | 반복 오류 목록 |
| `errors/resolved_errors.md` | 해결된 오류 목록 |
| `decisions/decision_memory.yaml` | 설계 결정 기록 |
| `directions/active_direction.md` | 현재 focus + 열린 blocker |
| `directions/parking_lot.md` | 미래 turn 이월 항목 |
| `patterns/successful_patterns.md` | 성공 패턴 |
| `patterns/anti_patterns.md` | 금지 패턴 |
| `hooks/hook_execution_log.md` | hook 실행 로그 (Phase E부터 자동 기록) |
| `run_summaries/` | turn별 요약 (Phase E hook 연결 후 자동 생성) |

## 정책

- **Phase 1** (현재): hook 없음, 수동 업데이트
- **Phase E**: `stop_lifecycle_automation.ps1` 추가 후 자동 업데이트 (별도 사용자 승인 필요)
- `run_summaries/`는 hook 연결 전까지 `.gitkeep`만 존재
- `.self_evolving_memory/**`는 lifecycle_audit_v2.py에서 **PROTECTED** 분류됨 (자동 이동/삭제 금지)

## 진입점

사람이 읽는 경우: `directions/active_direction.md` 부터 시작.
자동화 도구가 읽는 경우: `index.yaml` 부터 시작.
