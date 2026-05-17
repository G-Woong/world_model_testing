# 17_step1_5_lifecycle_cleanup_design.md — STEP 1.5: Lifecycle/Cleanup 정책 설계

**작성일**: 2026-05-17  
**Phase**: CC-P3  
**근거**: `docs/orchestration/14_REPORT_LIFECYCLE_POLICY.md`,  
`docs/orchestration/02_CLEANUP_CANDIDATES.md`,  
`scripts/audit_stale_reports.py`  
**범위**: Read-only 분석 + 신규 layer 설계. 원본 파일 변경 0. 정책 본문 수정 0.

---

## §1. 핵심 결론 요약

| Q | 답 | 근거 |
|---|---|---|
| cleanup atomic PR 필요한가? | **YES (implicit)** | `14_REPORT_LIFECYCLE_POLICY.md §3 C5`, §6: "Move-Item PR → 별도 라운드" |
| 정기 실행인가? | **Milestone-driven** | phase-gate sentinel 추가 후 routine. cron 아님 |
| copy-only staging 가능한가? | **YES — 신규 layer** | 기존 정책에 없음. 이 문서에서 설계 |
| 이미 archive로 이동된 파일? | **NO** | `docs/orchestration/archive/` 및 `plans/archive/` = `.gitkeep`만 |
| human review 강제 mechanism? | **YES (다층)** | script `--apply` 차단 + 정책 §6/§7 + CONFIRM gate + git mv 전용 |

---

## §2. 기존 정책 분석 (`14_REPORT_LIFECYCLE_POLICY.md`)

### §2.1 정책 핵심 원칙

- **delete 금지, archive-first** (§4)
- **archive 경로**: `plans/archive/YYYY-MM/`, `docs/orchestration/archive/YYYY-MM/`
- **`git mv` 전용** — 단순 copy/delete 금지
- **dry-run → human 승인 → 별도 라운드**에서만 실행

### §2.2 Archive 5조건 (§3) — 모두 충족 필수

| ID | 조건 |
|---|---|
| C1 | 내용이 active SSoT에 흡수됨 |
| C2 | blocker/decision이 후속 session report 또는 decision log에 이관됨 |
| C3 | data manifest 또는 phase gate sentinel에 결과가 반영됨 |
| C4 | 미해결 leakage/schema/baseline/evaluation 결정 없음 |
| C5 | 본 정책 §3 archive 사유 한 줄이 archive 이동 PR에 명시됨 |

### §2.3 Dry-Run Pipeline (§6)

```
[dry-run audit_stale_reports.py]
    ↓ stdout JSON/text only, 파일 변경 0
[human review (§3 5조건 수동 검증)]
    ↓ 별도 라운드 명시
[git mv 기반 archive PR (atomic)]
    ↓ archive/YYYY-MM/ 이동 (delete 금지)
[일정 기간 후 manual delete (별도 결정)]
```

### §2.4 Hard Prohibitions (§7)

기존 정책이 금지하는 것:
- `rm`, `Remove-Item`, `git rm`, `rmdir` 사용 금지
- `paper_context_ref/`, `outputs/phase_gates/`, `src/`, `tests/` 자동 후보 포함 금지
- `plans/PHASE_PROGRESS.md` archive/delete 절대 금지 (pre_compact hook active)
- 사용자 승인 없는 파일 이동 금지

---

## §3. `scripts/audit_stale_reports.py` 분석

### §3.1 `--apply` 차단 (read-only 강제)

```python
# audit_stale_reports.py:243-249 (approximate)
if args.apply:
    print("[ERROR] --apply is not implemented. This script is dry-run only.", file=sys.stderr)
    print("[ERROR] Use git mv manually after reviewing the dry-run output.", file=sys.stderr)
    sys.exit(2)
```

`--apply` 호출 시 **stderr 출력 + exit 2**. 어떤 move/copy/delete 코드 경로도 없음.

### §3.2 Script 동작

- **Input**: repo 파일 트리 탐색
- **Output**: stdout JSON 또는 텍스트 (후보 목록)
- **Side effects**: 0 (파일 변경 없음)
- **JSON mode**: `--json` 플래그로 machine-readable 출력

### §3.3 현재 Category enum (추정)

기존 script의 분류:  
`PLAN / GATE_REPORT / PROGRESS / SESSION / DECISION / RESULT / HANDOFF / OTHER`

---

## §4. 기존 정책 vs 사용자 제안 Reconciliation

### §4.1 기존 정책 "review" 단계

기존 §6 dry-run pipeline에서 "human review"는:
- audit script stdout 결과를 읽음
- 정책 §3 5조건을 수동으로 검증
- **물리적 복사본 없음** — 텍스트 기반 판단

### §4.2 사용자 제안 ("필요한 파일과 필요없는 파일을 분리")

사용자 인텐트:
> "바로 삭제·이동이 아니라 필요한 파일과 필요없는 파일을 분리시키는 정책.  
> 사용자가 근거를 보고 직접 삭제/이동을 결정."

이 인텐트는 기존 정책의 dry-run 분류 단계와 **부분 일치**하지만:
- 기존: stdout 텍스트만 출력
- 사용자 제안: **물리적 복사본을 `outputs/cleanup_audit/<ts>/`에 분리 staging**

→ **충돌 아님. 기존 dry-run 단계와 archive PR 단계 사이에 끼어드는 optional review layer.**

### §4.3 두 모델 비교

| 차이 | 기존 정책 | 신규 layer (사용자 제안) |
|---|---|---|
| dry-run 출력 형태 | stdout JSON/text | + filesystem manifest + 복사본 |
| 검토 단계의 물리적 형태 | 없음 | `outputs/cleanup_audit/<ts>/` 디렉터리 |
| archive 실행 방식 | `git mv` (history 보존) | 동일 (변경 없음) |
| delete 시점 | archive 후 수동만 | 동일 |
| 추가 리스크 | — | 디스크 사용량 (복사본), staging dir 자체가 미래 cruft 가능 |

---

## §5. 신규 Layer 설계 — Copy-Only Review Staging

### §5.1 동작 모델

```
[dry-run audit_stale_reports.py --json]
    ↓ stdout JSON 출력 (파일 변경 0)
    ↓ → outputs/cleanup_audit/<YYYYMMDD_HHMMSS>/candidate_manifest.json 저장
    ↓ → outputs/cleanup_audit/<YYYYMMDD_HHMMSS>/candidate_manifest.md (사람 가독 표)
[optional: copy-only staging]
    ↓ 안전한 카테고리(SUPERSEDED_REPORT 등)의 후보만 복사
    ↓ outputs/cleanup_audit/<ts>/review_copies/<sanitized_path>/ 에 복사
    ↓ sha256(original) + sha256(copy) 기록
    ↓ 원본 변경 0, 원본 이동 0, 원본 삭제 0
[user reviews 복사본 + 근거 manifest]
    ↓ 각 후보에 KEEP / ARCHIVE_LATER / DELETE_LATER 라벨 부여
[기존 정책 §6의 archive PR 라운드 진입 (또는 KEEP 시 staging 폐기)]
    ↓ git mv 기반 atomic PR
```

### §5.2 Copy-Only Staging 안전 규칙

1. 원본 파일 **이동/삭제/overwrite 0건**
2. 복사본에 sha256 기록 (원본 hash + 복사본 hash 동일 확인)
3. 후보 수 상한: **20 파일** 또는 누적 **1 MB** 초과 시 manifest만 생성 (copy DEFER)
4. `paper_context_ref/`, `src/frcgw/`, `tests/`, `outputs/phase_gates/` → **자동 제외**
5. `plans/PHASE_PROGRESS.md` → **자동 제외** (pre_compact hook active)
6. `.claude/`, `CLAUDE.md`, `.mcp.json` → **자동 제외**

### §5.3 Staging 디렉터리 구조

```
outputs/cleanup_audit/
└── 20260517_HHMMSS/
    ├── candidate_manifest.json      # machine-readable
    ├── candidate_manifest.md        # human-readable 표
    └── review_copies/               # (조건부, 안전 카테고리만)
        ├── plans__P0_REPO_SCAFFOLD_PLAN/
        │   ├── original.md          # 복사본
        │   └── sha256.txt           # original + copy hash
        └── ...
```

> **Note**: `outputs/cleanup_audit/`는 `.gitignore`에 추가 권고.  
> 단, 본 설계 문서는 `.gitignore` 수정을 직접 실행하지 않음 (별도 라운드).

---

## §6. Candidate Taxonomy (확장)

기존 script Category에 더해 본 설계에서 제안하는 분류:

| Category | 정의 | `deletion_allowed_now` | `move_allowed_now` |
|---|---|---|---|
| `SUPERSEDED_REPORT` | 후속 보고서로 대체된 보고서 (ex: 04_xxx → 08_run4_xxx) | **false** | false |
| `OLD_RUN_OUTPUT` | `outputs/runs/` 중 더 이상 source-of-truth 아닌 것 | **false** | false |
| `OBSOLETE_CLAIM_DOC` | 폐기된 claim version 문서 | **false** | false |
| `DUPLICATED_SESSION_REPORT` | 동일 날짜 중복 handoff MD | **false** | false |
| `CODEX_TASK_ARTIFACT` | `.agent_tasks/codex_done/*_RESULT.md` | **false** | false |
| `CLAUDE_TASK_ARTIFACT` | Claude 측 task report MD | **false** | false |
| `REPLACED_CONFIG` | 코드 변경 후 dead config/script | **false** | false |
| `TEMP_SMOKE_OUTPUT` | smoke 후 보존 불요 출력 | **false** | false |
| `KEEP_CORE` | 현재 C3 LR falsification 관련 core 파일 (보존) | N/A | N/A |
| `MANUAL_REVIEW_ONLY` | 자동 분류 불가, 사용자 판단 필수 | **false** | false |
| `DO_NOT_TOUCH` | `paper_context_ref/`, `src/frcgw/`, active sentinel | **false** | **false** |
| `PLAN_ACTIVE` | 현재 active plan MD (본 문서 등) | **false** | false |

**모든 category에 `deletion_allowed_now: false` 강제.**  
`move_allowed_now: false` — archive 이동도 human approval + 별도 PR 라운드 필요.

---

## §7. 옵션 비교 (Option A/B/C)

### Option A — 현재 정책 그대로 (dry-run only)

```
dry-run stdout → human reads text → archive PR
```

- 장점: 기존 정책 변경 없음
- 단점: 물리적 분리 없음, 사용자가 텍스트만으로 판단해야 함

### Option B — Copy-Only Staging (신규 layer) ← **추천**

```
dry-run stdout → manifest JSON 생성 → copy-only staging → human reviews 복사본 → archive PR
```

- 장점: 사용자가 복사본을 직접 열어 내용 확인 가능. 원본 안전.
- 단점: 디스크 사용량, staging dir 관리 필요
- 추천 이유: 사용자 인텐트와 가장 일치. 원본 위험 없음.

### Option C — Manifest + Tag (파일 내 tag 추가)

```
dry-run → manifest → 각 파일에 front-matter tag 추가 → human reviews
```

- 단점: 원본 파일 수정 (fragile file 포함 가능). §7 Hard Prohibitions 위반 위험.
- **비권장.**

---

## §8. Human Review Guide

### §8.1 각 후보 파일에 대해 결정할 것

사용자가 staging 디렉터리 또는 manifest를 검토 후 결정:

| 결정 | 의미 | 다음 조치 |
|---|---|---|
| `KEEP` | 현재 위치에 그대로 유지 | staging dir 내 해당 복사본만 삭제 가능 |
| `ARCHIVE_LATER` | archive 이동 대상 확인 | 별도 PR 라운드에서 `git mv` 실행 |
| `DELETE_LATER` | 삭제 대상 확인 (archive 후 일정 기간 뒤) | archive PR → 별도 결정 |
| `NEED_MORE_INFO` | 판단 보류 | 다음 세션에서 재검토 |

### §8.2 Archive 5조건 수동 체크 (각 ARCHIVE_LATER 대상마다)

1. [ ] C1: 내용이 active SSoT에 흡수됨?
2. [ ] C2: blocker/decision이 후속 report에 이관됨?
3. [ ] C3: 결과가 phase gate 또는 manifest에 반영됨?
4. [ ] C4: 미해결 leakage/baseline/evaluation 결정 없음?
5. [ ] C5: archive 사유 한 줄 작성됨?

**5조건 중 하나라도 NO → ARCHIVE_LATER 불가 → KEEP 또는 NEED_MORE_INFO.**

### §8.3 절대 금지 행동

- `git rm <file>` 금지
- `Remove-Item <file>` 금지
- `rm <file>` 금지
- 복사본 staging 디렉터리의 파일을 원본 경로에 덮어쓰기 금지
- `paper_context_ref/`, `src/frcgw/`, `outputs/phase_gates/` 변경 금지
- `plans/PHASE_PROGRESS.md` 이동/삭제 금지

---

## §9. 현재 Cleanup 후보 카테고리 예시 (dry-run 결과 대기)

아래는 `02_CLEANUP_CANDIDATES.md` 및 기존 분석 기반 예비 분류:

### SUPERSEDED_REPORT 후보

| 파일 | 대체 파일 | 확인 필요 사항 |
|---|---|---|
| `docs/orchestration/lr_alignment/04_md_refactor_patch_plan.md` | 후속 보고서들 | 내용 흡수 여부 확인 |
| `docs/orchestration/lr_alignment/06_unit_test_plan.md` | 구현 완료 | test 파일 존재 확인 |

### KEEP_CORE (절대 보존)

| 파일 | 이유 |
|---|---|
| `docs/orchestration/lr_alignment/13_claim_survivability_decision_report.md` | C1~C6 최신 판정 |
| `docs/orchestration/lr_alignment/12_run6_lr_eval_report.md` | Run 6 reference |
| `outputs/runs/p3_lr_eval/metrics.json` | Run 6 preflight reference |
| `outputs/runs/p3_ablations/ablation_results.json` | Ablation reference |
| `evidence_cards/C{1..6}_*.md` | claim evidence SSoT |

### DO_NOT_TOUCH (자동 제외)

- `paper_context_ref/*.md` (16개)
- `src/frcgw/**/*.py`
- `tests/**/*.py`
- `outputs/phase_gates/*.passed`
- `plans/PHASE_PROGRESS.md`
- `.claude/settings.json`
- `scripts/run_codex_task.ps1`

---

## §10. 정책 본문 수정 권고 (별도 라운드에서만)

본 문서는 신규 layer를 "권고"로만 기술한다.  
`14_REPORT_LIFECYCLE_POLICY.md` 본문에 §10 추가는 **별도 라운드**에서만 실행:
- 사용자 명시적 승인 필요
- Fragile file 수정 규칙 적용
- 테스트 재실행 (smoke test of hook 동작)

---

## §11. STEP 1.5 PASS 선언

- [x] `14_REPORT_LIFECYCLE_POLICY.md` §3 5조건 및 §6 pipeline 분석 완료
- [x] `audit_stale_reports.py` `--apply` 차단 메커니즘 분석 완료
- [x] Q1 cleanup atomic PR: YES (implicit) 확인
- [x] Q2 periodic: milestone-driven 확인
- [x] Q3 copy-only staging 가능: YES (신규 layer, 기존 정책과 충돌 없음) 설계 완료
- [x] Option A/B/C 비교 + Option B 추천
- [x] Candidate taxonomy 12개 + `deletion_allowed_now=false` 강제
- [x] Human review instructions 완성
- [x] "필요한 파일과 필요없는 파일을 분리" 인텐트 부분 일치 + 신규 layer로 해소 명시
- [x] 원본 파일 변경 0
- [x] 정책 본문 수정 0 (별도 라운드 권고만)

**STEP 1.5: PASS**
