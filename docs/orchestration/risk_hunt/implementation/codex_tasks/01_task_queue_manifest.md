# PHASE 1 — Codex Task Queue Manifest

**Date**: 2026-05-19  
**Status**: COMPLETE — 8 task files created

---

## Task Queue

| Task ID | 파일명 | 실행 순서 | 의존성 | Checkpoint |
|---|---|---|---|---|
| TASK_LFD_004 | `TASK_LFD_004_v0_5_intra_episode_switch.md` | 1 | visibility.py 사전 수정 (사용자 승인) | Checkpoint-2 |
| TASK_LFD_001 | `TASK_LFD_001_cusum_sprt_baseline.md` | 2 | TASK_LFD_004 | Checkpoint-3 |
| TASK_LFD_007 | `TASK_LFD_007_sequential_detection_metrics.md` | 3 | TASK_LFD_001, TASK_LFD_004 | Checkpoint-3 |
| TASK_LFD_002 | `TASK_LFD_002_history_encoder_persistent_ht.md` | 4 | 없음 (독립) | Checkpoint-4 |
| TASK_LFD_003 | `TASK_LFD_003_bocpd_run_length_head.md` | 5 | TASK_LFD_002 | Checkpoint-5 |
| TASK_LFD_005 | `TASK_LFD_005_temporal_consistency_and_seq_loss.md` | 6 | TASK_LFD_003, TASK_LFD_007 | Checkpoint-5 |
| TASK_LFD_006 | `TASK_LFD_006_evaluation_labels_detector_output.md` | 7 | TASK_LFD_004, TASK_LFD_003 + visibility.py 사전 수정 | Checkpoint-6 |
| TASK_LFD_008 | `TASK_LFD_008_robotics_ood_eval_harness.md` | 8 | TASK_LFD_003, TASK_LFD_001 | Checkpoint-8 |

---

## 공통 FILES_FORBIDDEN (모든 task 적용)

```
.claude/
CLAUDE.md
.mcp.json
.venv/
data/
outputs/
secrets/
.env*
scripts/run_codex_task.ps1
paper_context_ref/
src/frcgw/schemas/visibility.py  (PHASE 6 TASK에서도 FORBIDDEN)
```

---

## 사용자 승인 게이트 (코드 실행 전 필수)

### Gate-A (TASK_LFD_004 실행 전)
`visibility.py::FORBIDDEN_AGENT_FIELDS`에 추가 필요:
```python
"regime_switch_t",
```
Mirror: `.claude/hooks/schema_leakage_guard.ps1 $forbiddenTokens`  
테스트: `pytest -q tests/test_forbidden_field_mirror_sync.py` → 통과 확인

### Gate-B (TASK_LFD_006 실행 전)
`visibility.py::FORBIDDEN_AGENT_FIELDS`에 추가 필요:
```python
"detection_delay_gt",
```
Mirror: 동일  
테스트: `pytest -q tests/test_forbidden_field_mirror_sync.py tests/test_visibility_contract.py tests/test_leakage_auditor.py`

---

## M1-M7 수정사항 반영 확인

| # | 수정사항 | 반영 TASK | 위치 |
|---|---|---|---|
| M1 | HistoryEncoder callers FILES_ALLOWED 포함 | TASK_LFD_002 | FILES_ALLOWED + BACKGROUND |
| M2 | {0,6} short-circuit 처리 결정 | TASK_LFD_003 | BACKGROUND (parallel path 결정) |
| M3 | BatchTargets + L_regime cascade 매핑 | TASK_LFD_004 | BACKGROUND + REQUIRED_IMPLEMENTATION |
| M4 | regime_switch_t 사용자 승인 게이트 | TASK_LFD_004 | STOP_CONDITION |
| M5 | detection_delay_gt 사용자 승인 게이트 | TASK_LFD_006 | STOP_CONDITION + FILES_FORBIDDEN |
| M6 | 컴포넌트별 unit test 명시 | LFD_001-003 | REQUIRED_TESTS (각 task) |
| M7 | grammar-template OOD split 설계 | TASK_LFD_001 | REQUIRED_IMPLEMENTATION §3 |

---

## Checkpoint-1 통과 조건 평가

| 조건 | 상태 |
|---|---|
| 8 task 파일 schema 완비 | ✅ (10-field schema 완비) |
| visibility.py 관련 task(LFD_006) 별도 safety gate 명시 | ✅ (FILES_FORBIDDEN + STOP_CONDITION) |
| Dependency graph 합의 | ✅ (위 순서표) |
| M1-M7 수정사항 반영 | ✅ (위 확인표) |

**Checkpoint-1 판정**: `PASS`

---

## 다음 단계 (PHASE 2)

사용자 승인 후 절차:
1. **Gate-A 승인** → visibility.py에 `regime_switch_t` 추가 + sync test GREEN
2. `scripts/run_codex_task.ps1 -Mode run -TaskName LFD_004 -TaskFile .agent_tasks/codex_queue/TASK_LFD_004_v0_5_intra_episode_switch.md -BypassSandbox`
3. Codex 결과 verify + T3 critic audit + accept
