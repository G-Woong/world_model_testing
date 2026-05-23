# Codex Worktree Sync & Sub-Agent Setup Plan

> **Mode**: PLAN ONLY. 본 문서가 사용자 승인을 받기 전에는 어떤 파일도 수정하지 않는다.
> **Source of truth**: Claude Code worktree (`C:\Users\computer\Desktop\ICLR_WM_claude-code`, branch `memory-redesign-2026-05-16`, HEAD `58ad48d`).
> **Sub-agent sandbox**: Codex worktree (`C:\Users\computer\Desktop\ICLR_WM_codex`, branch `codex-work`, HEAD `befd173`).

---

## Context

이번 변경의 목적:

1. **현재 상태**: Codex worktree(`ICLR_WM_codex`)가 Claude HEAD보다 **9 commit 뒤처져 있고**, 그 9 commit 안에 **FRCG-WM → FGLC 대전환(R0 pivot, 526개 파일 삭제, `src/frcgw/` → `src/fglc/` 리네임, `paper_context_ref/` 전체 제거)**이 포함되어 있다. Codex가 현재 상태에서 작업을 수행하면 **이미 사라진 패키지명·디렉토리**에 대한 코드를 만들게 된다 → 모든 결과물이 stale.
2. **Codex 환경의 부재**: Codex worktree에는 `AGENTS.md`, `.codex/config.toml`, `rules/` 같은 sub-agent 제약 문서가 **하나도 없다**. Codex의 실제 행동은 100% `scripts/run_codex_task.ps1`이 `.agent_tasks/codex_prompt_template.md`를 stdin으로 흘려넣는 흐름으로만 결정된다. 그러나 그 template 자체가 stale("FRCG-WM repo" 문장, `paper_context_ref/` forbidden path, fglc 미언급).
3. **목적**: Codex worktree를 Claude 기준 HEAD로 안전하게 동기화하고, Codex의 sub-agent 행동을 제약하는 환경(AGENTS.md + 갱신된 prompt template)을 정리하며, 결과물을 Claude Code가 review·accept/reject할 수 있는 workflow를 회복한다.

본 PLAN은 그 sync · 보호 · 검증 절차를 한 묶음으로 설계한다.

---

## 1. Observed Current State

### 1.1 Worktrees
| Path | Branch | HEAD | Status |
|---|---|---|---|
| `C:\Users\computer\Desktop\ICLR_WM_claude-code` | `memory-redesign-2026-05-16` | `58ad48d chore(turn): auto-commit 2026-05-23T03:35:52Z` | **dirty** (2 files), `[ahead 213]` vs `origin` |
| `C:\Users\computer\Desktop\ICLR_WM_codex` | `codex-work` | `befd173 chore(cleanup): purge GUI code + screenshot_ref + dated reports` | **clean** |

`.worktrees/codex-work` 경로(`CLAUDE.local.md`의 코멘트 힌트)는 **존재하지 않는다** — Codex worktree의 실제 경로는 `C:\Users\computer\Desktop\ICLR_WM_codex` (sibling directory).

### 1.2 Divergence (Claude `58ad48d` vs Codex `befd173`)
- **Merge-base = `befd173`** (Codex HEAD 자체) → linear ancestor → **fast-forward 가능**.
- **Claude가 앞선 9 commit**: `58ad48d` ← `740a9d0` ← `ca92ff4`(R0.passed pivot 완료) ← `8174ab1` ← `73087a4`(**frcgw→fglc 리네임**) ← `cae2c8d` ← `e53169c` ← `c41663b`(**526개 파일 삭제**) ← `e0decac` ← `befd173`.
- **Codex가 앞선 commit: 0**.

### 1.3 Claude worktree dirty files
- `M .self_evolving_memory/hooks/hook_execution_log.md`
- `D outputs/lifecycle/.gitkeep`
- 둘 다 sync와 무관한 운영 흔적 — sync 결정과 분리해서 다룬다.

### 1.4 Codex worktree untracked/uncommitted
- `git status --short`, `git diff --stat`, `git diff --cached --stat` 모두 비어 있음 → **로컬 변경 0**. 안전.

### 1.5 Untracked/존재 파일 (Codex worktree 관점)
- `.env` (gitignored, secret) — sync와 무관, 절대 손대지 않는다.
- `.lifecycle_trash/`, `.pytest_cache/`, `.self_evolving_memory/`, `.venv/` — 모두 ignored.
- `src/frcgw/` (tracked, sync 후 사라짐), `paper_context_ref/` (tracked, sync 후 사라짐).
- `.agent_tasks/codex_queue/` 안에 **200+개 TASK 파일** (FRCG-WM 시대) — sync 후에도 디렉토리 자체는 untracked 영역이므로 사라지지 않지만, 내용이 stale.
- `.agent_tasks/codex_done/` 안에 `TASK_LFD_001/002/003/004/007_RESULT.md` 5개 — Codex가 만든 진짜 산출물, **보존 대상**.
- `.agent_tasks/archive/2026-05/` — 사용 흔적 있음, 보존 대상.

---

## 2. `.agent_tasks/` Audit

### 2.1 Claude worktree `.agent_tasks/` (현재 구조)
```text
.agent_tasks/
  codex_prompt_template.md   (1113 B, FRCG-WM 표기, 갱신 필요)
  archive/                   (.gitkeep만)
  codex_archive/p3_impl/     (빈 placeholder, 사용 흔적 없음)
  codex_done/                (.gitkeep만 — RESULT.md는 Codex worktree에만 있음)
  codex_logs/                (240+ 파일, ~9 MB; gitignored)
```

### 2.2 Codex worktree `.agent_tasks/` (현재 구조)
```text
.agent_tasks/
  codex_prompt_template.md   (1113 B, 동일 stale 버전)
  archive/                   (2026-05/ 하위 디렉토리 사용 중)
  codex_queue/               (200+ TASK 파일, 대부분 FRCG-WM 시대 stale)
  codex_done/                (LFD RESULT 5개 보존 대상)
  (codex_logs/ 없음 — gitignored 정책상 정상)
  (codex_archive/ 없음 — Claude쪽만 보유)
```

### 2.3 역할 (현재 실제 사용 패턴 기준)
| 경로 | 실제 역할 | 변경 권고 |
|---|---|---|
| `codex_prompt_template.md` | `run_codex_task.ps1 Invoke-Dispatch`가 stdin으로 흘리는 표준 프롬프트 | **갱신 필요** (FRCG-WM → FGLC 문구, forbidden path 재정렬) |
| `codex_logs/` (Claude only) | `RUN_<ts>_TASK_<N>.{jsonl,err.log,summary.json,_lastmsg.txt}` 실행 로그 | 유지. ignored이지만 디렉토리는 보존 |
| `codex_done/` (Claude only currently empty) | 하네스 contract상 `prepare-merge` 후 RESULT.md가 들어와야 할 곳 | 유지. Codex쪽 RESULT를 sync 후 옮길지 결정 필요 |
| `codex_queue/` (Claude는 없음, Codex는 있음) | 하네스가 `assign`/`dispatch` 모드에서 의존 (`$QUEUE_DIR = .agent_tasks/codex_queue`) | **Claude쪽에도 빈 디렉토리 + `.gitkeep` 추가가 필요** (`/run_codex_task.ps1 init`이 만들도록 위임 가능) |
| `archive/` (양쪽 다 있음) | Codex쪽은 실제 사용중(`2026-05/`), Claude는 비어 있음 | 역할 정의 필요: 일반 archive vs Codex 전용 |
| `codex_archive/p3_impl/` (Claude only) | 사용 흔적 없음 (orphan) | 역할 정의 또는 제거 결정 필요 (사용자 승인 후) |

### 2.4 발견된 inconsistency
1. **`codex_queue/` 부재 (Claude worktree)** — 하네스가 의존하지만 Claude 쪽에는 없음. `dispatch`/`assign` 모드 직접 호출 시 path resolve 실패 가능.
2. **`codex_done/` 양쪽 desync** — Codex가 LFD 결과 5건을 만들었지만 `prepare-merge` 단계가 실행되지 않아 Claude쪽 `codex_done/`은 빈 상태.
3. **Template 표기 drift** — 양쪽 worktree의 `codex_prompt_template.md`는 동일 1113 B (tracked)이지만 둘 다 "FRCG-WM repo" / `paper_context_ref/` 참조. Pivot 미반영.
4. **`codex_orchestration_rules.md` 패키지명 drift** — 본 파일은 `src/fglc/`라고 명시하지만 mirror 위치가 `src/frcgw/`로 남은 곳 있음 (확인 필요, 단 본 PLAN의 sync 범위 밖).
5. **`.claude/` 전체가 `.gitignore`됨 (line 107)** → `.claude/lib/codex_sync_constants.ps1`, `.claude/rules/codex_orchestration_rules.md` 등 하네스가 의존하는 파일들이 **tracked가 아니다**. 즉 Codex worktree에는 `.claude/` 자체가 없다(확인 완료). 이는 Codex가 직접 hooks·rules를 읽을 수 없음을 의미 — 의도된 격리.
6. **CLAUDE.md ↔ codex_orchestration_rules.md 패키지 표기 불일치** — CLAUDE.md는 `src/fglc/`, codex rules는 일부 위치에서 `src/frcgw/schemas/` 잔존. 본 PLAN scope 밖이지만 후속 PR로 분리 권고.

### 2.5 재사용 결정
- **유지**: `codex_prompt_template.md` 위치, `codex_logs/`, `codex_done/`, `archive/`, `codex_archive/` 폴더 구조 (역할만 명확화).
- **새로 만들지 않음**: 새 디렉토리, 새 docs 구조 일체 금지. 기존 폴더 안에 timestamp 기반 파일만 추가.
- **단 한 가지 신설 검토**: Claude worktree에 `.agent_tasks/codex_queue/.gitkeep`만 추가하여 하네스 의존성 회복 (또는 `run_codex_task.ps1 init` 1회 실행으로 위임).

---

## 3. Sync Risk Assessment

### 3.1 Risk level: **MEDIUM**
이유: linear fast-forward로 git 자체는 안전하지만, sync 후 **사용자가 인지하지 못한 거대 변경** (526 file deletion, package rename, paper_context_ref 전체 삭제)이 Codex worktree에 적용된다. Codex가 만들었던 200+ TASK 파일과 5개 RESULT.md는 untracked 영역에 있어 git fast-forward로는 사라지지 않지만, **그것들이 참조하는 코드/문서가 모두 사라진다** → 향후 dispatch 시 무효 동작 가능.

### 3.2 Codex-only 변경
- 없음 (git diff = 0, untracked 변경만 있음).
- 단 `.agent_tasks/codex_queue/`, `.agent_tasks/codex_done/`, `.agent_tasks/archive/` 안의 파일들은 **gitignored이므로 fast-forward에 영향받지 않음** — 자동 보존.

### 3.3 Claude-only 변경 (Codex로 들어갈 9 commit 요약)
- `R0.passed` sentinel 추가, FRCG-WM → FGLC pivot 완료.
- `src/frcgw/` → `src/fglc/` 패키지 리네임.
- 526개 tracked 파일 삭제 (대부분 paper_context_ref, FRCG-WM 시대 산출물).
- `docs/idea/` 27개 재작성, `docs/ROADMAP/` 21개 추가.
- settings.local.json 한국어 + EN→KR 번역.

### 3.4 Data/log/secret 위험
- Codex worktree의 `.env` 파일: gitignored → fast-forward로 건드리지 않음. **안전**.
- Codex worktree의 `.venv/`, `.pytest_cache/`, `.lifecycle_trash/`: gitignored → 보존.
- `.agent_tasks/codex_logs/`: ignored → 보존.
- `outputs/`, `data/`, `secrets/`: ignored (with `!` exceptions for whitelisted markers) → 보존.

### 3.5 Recommended sync method: **`git -C <codex> fetch` + `git -C <codex> merge --ff-only <claude_head>`**
근거:
- 두 worktree가 동일 `.git` 저장소를 공유 (Codex worktree gitdir → `.git/worktrees/ICLR_WM_codex`) → `fetch` 불필요할 수도 있으나, 명시적으로 refs 정합성 보장 차원에서 1회 시도.
- Claude HEAD가 Codex의 strict ancestor descendant → `--ff-only`가 절대 fail하지 않음. fail하면 가정 위반이므로 그 자체로 BLOCKER.
- Reset/rebase/cherry-pick 불필요 — fast-forward가 최소 침습.

### 3.6 Rejected sync methods
| 방식 | 거부 사유 |
|---|---|
| `git reset --hard <claude_head>` | destructive 명령, untracked 보존되긴 하지만 tracked 변경(0개)이 있을 경우 silent loss. 굳이 쓸 이유 없음 |
| `git rebase <claude_head>` | linear ancestor라 rebase는 noop. 의미 없음 |
| `git merge` (non-ff) | merge commit이 codex-work에 생기면 branch history가 더러워짐. ff-only가 더 깨끗 |
| Codex worktree 재생성 (`git worktree remove` → `add`) | 200+ TASK queue, LFD RESULT, archive/2026-05 모두 untracked → 재생성 시 ALL LOST. 백업 없이 절대 금지 |
| `git clean -fdx` | secrets, .venv 다 날아감. 절대 금지 |

---

## 4. Backup / Rollback Plan

Sync 직전 다음을 Claude worktree의 `.agent_tasks/codex_archive/` 하위에 기록한다 (timestamp prefix = sync 실행 순간의 `yyyyMMdd_HHmmss`).

### 4.1 저장 대상 (모두 Claude worktree의 `.agent_tasks/codex_archive/` 안)
```text
.agent_tasks/codex_archive/<ts>_pre_sync_status.txt
    → "git -C <codex> status --short" + "git -C <codex> status -sb" 결과

.agent_tasks/codex_archive/<ts>_pre_sync_diff.patch
    → "git -C <codex> diff HEAD"   (현재 비어 있을 예정 — 검증용 zero-byte 가능)

.agent_tasks/codex_archive/<ts>_codex_head.txt
    → "git -C <codex> rev-parse HEAD" + "git -C <codex> log -1 --format=fuller"

.agent_tasks/codex_archive/<ts>_codex_branch.txt
    → "git -C <codex> branch --show-current" + "git -C <codex> branch -vv"

.agent_tasks/codex_archive/<ts>_untracked_files.txt
    → "git -C <codex> ls-files --others --exclude-standard"

.agent_tasks/codex_archive/<ts>_codex_queue_inventory.txt
    → "ls -1" of .agent_tasks/codex_queue/ in codex worktree (filenames only, 200+ lines expected)

.agent_tasks/codex_archive/<ts>_codex_done_inventory.txt
    → "ls -1" of .agent_tasks/codex_done/ in codex worktree (LFD RESULT files)

.agent_tasks/codex_archive/<ts>_sync_plan.md
    → 본 PLAN의 결정사항 + 실행 명령 그대로 기록 (실행 후 결과 추가)
```

### 4.2 Rollback procedure
fast-forward는 ref 이동일 뿐이므로 rollback이 매우 단순하다.
```powershell
# 1. Codex worktree로 작업 디렉토리 이동 없이, -C 옵션으로:
git -C C:\Users\computer\Desktop\ICLR_WM_codex reset --hard <PRE_SYNC_CODEX_HEAD>

# 2. PRE_SYNC_CODEX_HEAD 값은 <ts>_codex_head.txt 첫 줄에서 복원
# 3. untracked 파일들(codex_queue/, codex_done/, archive/, .env, .venv, …)은 fast-forward로 건드려지지 않으므로 별도 복원 불필요
# 4. inventory 파일과 실제 ls 결과를 cross-check
```

리스크: rollback 후에도 Codex worktree에 fast-forward로 들어온 9 commit이 reflog에 남아 있어 GC 전까지 안전. 30일 이내 rollback 가능.

---

## 5. Codex Environment Audit

| 항목 | 현재 상태 |
|---|---|
| `AGENTS.md` (Codex worktree root) | **없음** |
| `.codex/` 디렉토리 | **없음** |
| `.codex/config.toml` | **없음** |
| repo-local `config.toml` (Codex가 읽는다고 확정되지 않음) | **없음** |
| repo-root `rules/` 디렉토리 | **없음** |
| Codex가 실제로 읽는 config | **CLI flags + stdin prompt (codex_prompt_template.md) + TASK 파일** 외 다른 소스 없음. `@openai/codex` 바이너리가 user-global `~/.codex/`를 자동 로드하는지 여부는 UNKNOWN — 본 repo에는 그런 흔적 없음. |
| Codex 실행 스크립트 | `scripts/run_codex_task.ps1` (779 lines, 6 modes: init/assign/dispatch/verify/prepare-merge/run) |
| Codex task/handoff 템플릿 | `.agent_tasks/codex_prompt_template.md` (22줄, stale) |
| Codex가 읽어야 할 최소 문서 | TASK 파일 본문 + `codex_prompt_template.md` 본문이 stdin으로 합쳐져서 전달됨 |
| Forbidden path 정의 위치 (총 4곳, 수동 동기화) | (1) `.claude/lib/codex_sync_constants.ps1` `$FORBIDDEN_PATTERNS` (canonical) <br> (2) `scripts/run_codex_task.ps1` (consumer) <br> (3) `.claude/rules/codex_orchestration_rules.md` (mirror) <br> (4) `.agent_tasks/codex_prompt_template.md` 본문 (hard-coded copy) |
| Codex 결과 저장 위치 | Codex worktree의 `.agent_tasks/codex_done/TASK_<N>_<NAME>_RESULT.md` (Codex 자신이 작성) → `prepare-merge` 시 Claude worktree로 이동 |
| Codex 로그 위치 | Claude worktree의 `.agent_tasks/codex_logs/RUN_<ts>_TASK_<N>.{jsonl,err.log,summary.json,_lastmsg.txt}` |
| Codex가 수정 금지 path | template line 10-11에 `.claude/, CLAUDE.md, .mcp.json, .venv/, data/, outputs/, secrets/, .env*, paper_context_ref/, scripts/run_codex_task.ps1` 명시. 단 **`paper_context_ref/`는 pivot 후 존재하지 않음** → forbidden 표현이 무의미해짐, 갱신 필요 |
| 검증 테스트 명령 | TASK 파일의 `REQUIRED_TESTS:` 헤더에 명시 |
| **UNKNOWN** | (a) Codex CLI(`@openai/codex`)가 user-global config를 자동 로드하는지 여부<br>(b) 현 시점에서 Codex가 `AGENTS.md`라는 이름을 인식하는지(공식 CLI 문서 미확인) — 만든다 해도 자동 로드 보장 없음<br>(c) `.codex/config.toml` 표준 위치/스키마 — 실제로 검증된 바 없음 |
| **BLOCKED** | 없음 |

---

## 6. Proposed Codex Environment Changes

### 6.1 변경 결정 원칙
- **Codex가 실제로 읽는다는 증거가 없는 파일은 만들지 않는다.** 노이즈 회피.
- Codex의 행동 제약은 (a) `codex_prompt_template.md`의 명시적 지시 (b) `TASK 파일`의 헤더 (c) 하네스(`run_codex_task.ps1`)가 강제하는 검증 (forbidden path 차단, 종료코드 40) 이 3축에 의존한다. 본 PLAN은 이 3축만 다듬는다.
- **`AGENTS.md`는 "보조 문서"로만 생성한다** — 자동 로드 보장이 없으므로 그것을 강제 의존하는 구조는 만들지 않는다. 단 사람(Claude Code 본인)이 직접 TASK 작성 시 reference로 쓰고, 가능하면 template 본문에 "If `AGENTS.md` exists, read it before edits" 한 줄을 추가하여 stdin 흐름으로 강제한다.

### 6.2 변경 목록

| 파일 | 변경 유형 | 변경 내용 요약 |
|---|---|---|
| `.agent_tasks/codex_prompt_template.md` (Claude + Codex 양쪽 tracked, 동일 파일) | **갱신** | (a) "FRCG-WM repo" → "FGLC repo (Falsification-Guided Latent Correction)" <br> (b) forbidden path 목록에서 `paper_context_ref/` 제거 (pivot으로 존재하지 않음), `.claude/lib/`·`.claude/rules/` 명시(.claude/는 이미 있음), `src/fglc/schemas/` 추가 (codex_sync_constants.ps1과 일치) <br> (c) "After committing, write" vs "Before committing, write" wording drift 해소 — `run_codex_task.ps1` line 246-247과 일치시켜 **"After committing"** 채택? 또는 RESULT.md를 commit에 포함시키도록 **"Before committing"** 유지? → 사용자 확인 필요. PLAN 단계 결정: 현 on-disk 버전("Before committing")이 RESULT.md를 commit에 포함시키는 더 엄격한 contract이므로 유지하되, init-embedded template도 같이 맞춰서 drift를 0으로 만든다. <br> (d) "If `AGENTS.md` exists at repo root, read it as Codex sub-agent constitution" 한 줄 추가 <br> (e) report 형식(아래 §7) 명시 |
| Codex worktree root `AGENTS.md` | **신규 생성** | §6.3 참조. Claude 전용 `.claude/`, `CLAUDE.md`를 Codex 환경에 복사하지 않고, Codex가 자체적으로 따라야 할 헌법 수준의 제약만 짧게 기술 (1-2 페이지). |
| `scripts/run_codex_task.ps1` init-embedded template (lines 230-251) | **갱신** | 위 (a)~(d)와 동일 내용으로 동기화 (drift 0). |
| `.claude/lib/codex_sync_constants.ps1` `$FORBIDDEN_PATTERNS` | **검토** | `^paper_context_ref/`를 제거할지 (pivot으로 디렉토리 자체 없음) 또는 안전망으로 유지할지. PLAN 권고: **유지** (방어적). 변경하지 않음. |
| `.claude/rules/codex_orchestration_rules.md` | **별도 PR로 분리** | 패키지명 drift (`src/fglc/` vs 일부 `src/frcgw/schemas/`) 정리. 본 PLAN scope 밖. |
| `.gitignore` | **소폭 보강** | (a) `AGENTS.md`는 tracked 권장 (negation 불필요, 기본 tracked) <br> (b) `.codex/` 디렉토리는 만들지 않으므로 추가 ignore 불필요 <br> (c) `.agent_tasks/codex_queue/`는 untracked 데이터 디렉토리 — 현재 ignore 정책에 명시되지 않음 → 명시적 `.gitignore` 라인 추가 권고 (단, `!.agent_tasks/codex_queue/.gitkeep` 예외로 디렉토리 자체는 git에 남게 함). 결정 필요. |
| 추가 신규 파일 | **없음** | 새 docs/, rules/, .codex/ 일체 만들지 않는다. |

### 6.3 `AGENTS.md` (Codex worktree root, ~80-120 lines) — 설계
포함 요소:
1. **Role**: "당신은 Claude Code의 sub-agent다. 독립 오케스트레이터가 아니다."
2. **Worktree 경계**: 작업은 `C:\Users\computer\Desktop\ICLR_WM_codex` 내부에서만. main worktree 직접 수정 금지.
3. **Task scope**: 주어진 TASK 파일의 `FILES_ALLOWED:` 외 파일 수정 금지.
4. **Forbidden actions**: destructive git (`reset --hard`, `clean -fdx`, `push --force`), branch 변경, merge to main, secret/env 접근, dependency 무단 install, 네트워크 호출.
5. **Required analysis**: 코드 수정 전 `FILES_ALLOWED` 전체를 읽고 호출 관계 매핑.
6. **Required tests**: TASK의 `REQUIRED_TESTS:` 항목 실행, 모두 green일 때만 commit.
7. **Reporting contract**: §7의 report format 강제.
8. **BLOCKED/UNKNOWN policy**: 불확실하면 commit하지 말고 `STOP_CONDITION` 매칭 + RESULT.md에 BLOCKED 명시.
9. **Sub-agent 한계**: scope 확장·기능 추가·"개선" 시도 금지. 시니어 엔지니어 테스트 통과 여부 점검.
10. **Source-of-truth 참조 금지**: `.claude/`는 Codex worktree에 존재하지 않는다 — 거기 있는 hook/skill/rule을 끌어오려 하지 말 것. 필요한 모든 컨텍스트는 stdin prompt + TASK 파일에 명시되어 전달된다.

이 문서는 Codex가 자동 로드한다는 보장은 없다. 그러나 (a) template이 "If AGENTS.md exists, read it before edits"를 명시하면 Codex가 첫 단계에서 `cat AGENTS.md`를 호출하고, (b) Claude Code(본인)가 TASK 파일 작성 시 reference로 쓰며, (c) 향후 Codex CLI가 `AGENTS.md` 자동 로드를 지원하게 되면 그대로 활성화된다.

### 6.4 변경하지 않을 항목
- `.claude/` 전체 (Codex worktree에 복사 금지)
- `CLAUDE.md` 전체
- `CLAUDE.local.md`
- `src/`, `tests/`, `docs/idea/`, `docs/ROADMAP/` 본문
- `.env`, `outputs/`, `data/`, `secrets/`, `.venv/`
- Codex worktree의 `.agent_tasks/codex_queue/` 200+ TASK 파일 — **보존**, 단 사용자가 "이것들은 이제 stale이니 archive로 옮겨라"라고 명시할 때만 §13 단계에서 별도 처리
- Codex worktree의 `.agent_tasks/codex_done/` LFD RESULT 5건 — **보존**
- Codex worktree의 `.agent_tasks/archive/2026-05/` — **보존**

---

## 7. Codex Task Template Plan

### 7.1 현재 template 평가
- ✅ Worktree 경계 명시
- ✅ Forbidden path 일부 명시
- ❌ "FRCG-WM" 문구 stale
- ❌ `paper_context_ref/` forbidden 무의미 (디렉토리 없음)
- ❌ context files 섹션 부재 (TASK 파일에만 의존)
- ❌ Required analysis before edit 미강제
- ❌ Claude review checklist 부재
- ❌ Report format이 산문으로만 적혀 있어 일관성 약함
- ❌ `AGENTS.md` 참조 부재
- ❌ `SANDBOX_MODE` TASK 헤더 언급 없음 (하네스는 인식)

### 7.2 보강 후 구조 (목표 ~40-50 lines, 현재 22줄에서 ~2배)
```text
You are the implementation agent for the FGLC repo at
C:\Users\computer\Desktop\ICLR_WM_codex (worktree branch: codex-work).
You are a sub-agent of Claude Code; you are not an independent orchestrator.

# Step 0 — read constitution
- If `AGENTS.md` exists at repo root, read it in full BEFORE any edit.

# Step 1 — read your task
Task spec: {{TASK_FILE}}
Task name: {{TASK_NAME}}
Task number: {{TASK_NUMBER}}

Required headers in the TASK file:
TASK_NAME / BACKGROUND / GOAL / FILES_ALLOWED / FILES_FORBIDDEN /
REQUIRED_IMPLEMENTATION / REQUIRED_TESTS / ACCEPTANCE_CRITERIA /
COMMIT_MESSAGE / STOP_CONDITION   (+ optional SANDBOX_MODE: default|bypass)

# Step 2 — hard constraints
- Work only inside C:\Users\computer\Desktop\ICLR_WM_codex.
- Do not modify outside `FILES_ALLOWED`.
- Never modify: .claude/, CLAUDE.md, CLAUDE.local.md, .mcp.json, .venv/,
  data/, outputs/, secrets/, .env*, src/fglc/schemas/, scripts/run_codex_task.ps1.
- Use the existing Python venv at .venv. Use `python -m pip`, not bare pip.
- Run the targeted tests listed in REQUIRED_TESTS.
- Do not push. Do not amend. Do not rebase. Do not branch.
- Never run destructive git: reset --hard, clean -fdx, checkout -- *, branch -D.

# Step 3 — required analysis (before edits)
- Read every file in FILES_ALLOWED at least once.
- Map the call graph for the function(s) you will change.
- If the task spec is ambiguous, STOP and write a BLOCKED RESULT.md.

# Step 4 — report contract
Before committing, write to:
.agent_tasks/codex_done/TASK_{{TASK_NUMBER}}_{{TASK_NAME}}_RESULT.md
with EXACTLY these sections:

  # Codex Task Report — TASK_{{TASK_NUMBER}} {{TASK_NAME}}
  ## Summary
  ## Files Changed
  ## Commands Run
  ## Tests Run (pass/fail)
  ## Evidence (log paths, metric values)
  ## Risks / Open Questions
  ## Patch Review Notes for Claude Code
  ## Accept/Reject Recommendation

# Step 5 — commit
git add ALL changed files including RESULT.md.
git commit -m "<COMMIT_MESSAGE verbatim from task file>".
Working tree must be clean after commit.

# Step 6 — stop
Stop after the commit. Do not continue to additional work.
Do not start the next task. Do not "clean up" unrelated files.
```

### 7.3 양쪽 worktree 동기화
이 갱신은 양쪽 worktree의 `.agent_tasks/codex_prompt_template.md`에 모두 반영되어야 하지만, **fast-forward sync로 Claude → Codex로 전파된다**. 즉 절차는:
1. Claude worktree에서 template 수정 + commit
2. Codex worktree에서 `git merge --ff-only` (이미 §3.5에서 계획됨)
이로써 drift 0 보장.

### 7.4 `run_codex_task.ps1` init-embedded template
PowerShell 스크립트 line 230-251에 같은 내용의 fallback template이 hard-coded되어 있다. 본 sync 시 같은 commit에 함께 갱신 (drift 방지).

---

## 8. Test Task Plan

### 8.1 Task ID: `TASK_2026_05_23_SYNC_PROBE`
- 위치: `.agent_tasks/codex_queue/TASK_2026_05_23_SYNC_PROBE.md` (Codex worktree)
- 목적: sync + AGENTS.md + 갱신된 template의 contract 통과 여부를 **부작용 없이** 검증.

### 8.2 설계
- **Objective**: Codex가 (a) `AGENTS.md`를 읽고, (b) FILES_ALLOWED 외 파일에 손대지 않으며, (c) 지정된 report 형식으로 RESULT.md를 남기고, (d) 1개의 짧은 산문 파일을 생성·commit하고, (e) STOP 조건을 지키는지 검증.
- **No-op 범위**: 실제 연구 코드/모델/데이터/학습/평가 어디에도 영향 없음. 새 파일 1개만 생성.

### 8.3 TASK 파일 헤더 (요약)
```yaml
TASK_NAME: sync_probe
BACKGROUND: |
  Validate that post-sync Codex sub-agent honors the new AGENTS.md +
  updated codex_prompt_template.md contracts.
GOAL: |
  Create exactly one new file:
  .agent_tasks/codex_done/TASK_2026_05_23_SYNC_PROBE_HANDOFF.md
  containing the sync probe result. Touch nothing else.
FILES_ALLOWED:
  - .agent_tasks/codex_done/TASK_2026_05_23_SYNC_PROBE_HANDOFF.md
  - .agent_tasks/codex_done/TASK_2026_05_23_SYNC_PROBE_RESULT.md
FILES_FORBIDDEN:
  - "**" (everything else)
REQUIRED_IMPLEMENTATION: |
  1. Read AGENTS.md in full.
  2. Read this TASK file in full.
  3. Run `git -C . rev-parse HEAD` and `git -C . status --short`.
  4. Create HANDOFF.md with sections:
     - HEAD SHA
     - Branch
     - AGENTS.md byte size
     - Template byte size
     - "Sync probe OK" line if all checks pass.
  5. No code changes elsewhere.
REQUIRED_TESTS:
  - pwsh: "git -C . status --short"   # must be empty after commit
  - pwsh: "Test-Path .agent_tasks/codex_done/TASK_2026_05_23_SYNC_PROBE_HANDOFF.md"
  - pwsh: "Test-Path .agent_tasks/codex_done/TASK_2026_05_23_SYNC_PROBE_RESULT.md"
ACCEPTANCE_CRITERIA: |
  - Exactly 2 files added (HANDOFF.md + RESULT.md).
  - 0 files modified outside FILES_ALLOWED.
  - RESULT.md follows the 8-section format from updated template.
  - Working tree clean after commit.
COMMIT_MESSAGE: |
  test(codex-sub-agent): sync probe — verify AGENTS.md + template contract
STOP_CONDITION: |
  Stop immediately after the single commit. Do not attempt cleanup,
  scope expansion, or additional file creation.
SANDBOX_MODE: default
```

### 8.4 Allowed/Forbidden 명시
- Allowed: `.agent_tasks/codex_done/TASK_2026_05_23_SYNC_PROBE_HANDOFF.md`, `.agent_tasks/codex_done/TASK_2026_05_23_SYNC_PROBE_RESULT.md`
- Forbidden: 그 외 모든 파일.

### 8.5 Expected report location
- `C:\Users\computer\Desktop\ICLR_WM_codex\.agent_tasks\codex_done\TASK_2026_05_23_SYNC_PROBE_RESULT.md`
- `prepare-merge` 후 Claude worktree의 동일 경로로 이동.

### 8.6 Accept criteria (Claude Code 본인이 review)
- ✅ 정확히 2개 파일 add.
- ✅ FILES_FORBIDDEN 영역 침범 0.
- ✅ RESULT.md가 8섹션 모두 채워짐.
- ✅ HEAD SHA가 Claude HEAD (`58ad48d` 또는 그 이후)와 일치.
- ✅ `git -C <codex> status --short`가 commit 후 빈 결과.
- ✅ 하네스 종료 코드 0.
- ✅ T3 implementation-risk-critic agent report PASS (선택 — sync probe는 trivial하므로 사용자 결정).

### 8.7 Reject 시 처리
- `.agent_tasks/codex_archive/<ts>_sync_probe_rejected/` 디렉토리에 patch + report 이동.
- Codex worktree에서 `git -C <codex> reset --hard HEAD~1`로 revert (해당 1개 commit만).

---

## 9. Claude Review Protocol

### 9.1 Review steps (Codex가 sync probe completion 통보 후)
1. `.agent_tasks/codex_logs/RUN_<ts>_TASK_<N>.summary.json` 종료 코드 확인 (=0).
2. `.agent_tasks/codex_done/TASK_<N>_<NAME>_RESULT.md` 본문 확인 — 8섹션 모두 있는가.
3. `git -C <codex> diff HEAD~1 HEAD --stat` — 파일 수, 라인 수.
4. `git -C <codex> diff HEAD~1 HEAD --name-only` — FILES_ALLOWED 범위 일치 여부.
5. Forbidden path 침범 여부 (`run_codex_task.ps1`의 verify mode가 자동 검사 — 종료 코드 40이면 즉시 abort).
6. Test 결과 RESULT.md에 명시 — 모두 green?
7. unrelated 변경 ("그 김에" 개선)이 끼었는가 → diff 직접 검토.
8. T3 implementation-risk-critic agent 호출 (sync probe trivial이므로 사용자 옵션).
9. Accept / Reject 판단.
10. Accept: `prepare-merge` 모드 호출 → Claude worktree의 `codex_done/`로 RESULT.md 이동, fast-forward merge.
11. Reject: `git -C <codex> merge --abort`(만약 merge 진행중) 또는 `git -C <codex> reset --hard HEAD~1`, archive로 이동, blocker 보고.

### 9.2 Accept method
- 하네스 `prepare-merge` 모드 사용 (이미 구현됨).
- Claude worktree에서 `scripts/run_codex_task.ps1 -Mode prepare-merge -TaskName sync_probe -TaskNumber 2026_05_23_SYNC_PROBE` 형식.
- 자동 git merge 수행 (fast-forward 또는 merge commit).

### 9.3 Reject / Archive method
- `.agent_tasks/codex_archive/<ts>_<task_id>_rejected/`에 아래 저장:
  - `RESULT.md` 사본
  - `diff.patch` (`git -C <codex> format-patch HEAD~1..HEAD`)
  - `reason.md` (왜 reject했는지)
- Codex worktree에서 해당 commit revert:
  - `git -C <codex> reset --hard <PRE_TASK_HEAD>` (만약 그 1개 commit만 있으면)
  - 그 commit이 다른 작업 위에 있다면 `git revert <SHA>` 또는 `git rebase --onto`.

### 9.4 절대 금지
- Codex 결과를 review 없이 main worktree에 반영.
- `prepare-merge` 결과를 origin에 자동 push (`scripts/run_codex_task.ps1`은 push 안 함, 안전).
- T3 audit 없이 4 file 이상 변경된 codex commit을 accept.

---

## 10. Execution Plan After Approval

> 본 plan을 사용자 승인 후에만 실행. PLAN 단계에서는 어떤 파일도 수정하지 않는다.

### 단계 (각 단계 → verify 형식)

1. **Pre-sync 백업** → verify: `.agent_tasks/codex_archive/<ts>_*` 8개 파일 모두 생성, `<ts>_codex_head.txt` 첫 줄에 `befd173` 표시.
2. **Codex worktree fast-forward** (`git -C <codex> merge --ff-only 58ad48d`) → verify: `git -C <codex> rev-parse HEAD` == Claude HEAD, `git -C <codex> status --short` 빈 결과, `src/` 안에 `fglc/`만 남고 `frcgw/` 사라짐, `paper_context_ref/` 사라짐 확인.
3. **template + AGENTS.md 갱신 (Claude worktree에서)** → verify:
   - `.agent_tasks/codex_prompt_template.md` 새 50줄 버전 적용
   - `scripts/run_codex_task.ps1` 230-251 라인 init-embedded template 동기 갱신
   - Codex worktree root에 `AGENTS.md` 신규 작성 — 단 이 파일은 Codex worktree 전용이므로 Claude worktree에 작성 후 Codex worktree로 sync할지(=tracked) 또는 Codex worktree에서만 따로 commit할지 결정 필요. **권고**: Claude worktree에서 작성하여 tracked로 만들고 fast-forward로 Codex worktree에 전파 (단일 source-of-truth).
   - 위 변경 commit (Claude worktree) — commit message: `feat(codex-sub-agent): refresh prompt template + AGENTS.md for FGLC pivot`
4. **Codex worktree 2차 fast-forward** → verify: Codex worktree에 새 template + AGENTS.md 반영됨. `cat <codex>/AGENTS.md`로 직접 확인.
5. **(선택) `.agent_tasks/codex_queue/` 정리** → verify: 200+ stale FRCG-WM TASK 파일을 `.agent_tasks/codex_archive/2026-05-23_pre_pivot_stale_queue/`로 일괄 이동 (`mv`, untracked → untracked). 사용자가 "이건 이제 stale이니까 archive해도 좋다"라고 명시 승인했을 때만 실행. **PLAN 기본값: 보류** (사용자 결정 §11).
6. **Sync probe TASK 작성 및 실행** → verify: Codex worktree의 `.agent_tasks/codex_queue/TASK_2026_05_23_SYNC_PROBE.md` 생성. `scripts/run_codex_task.ps1 -Mode run -TaskName sync_probe -TaskFile <path>` 실행. 종료 코드 0.
7. **Sync probe 결과 review** (§9.1) → verify: 8섹션 RESULT.md 존재, FILES_FORBIDDEN 침범 0, test 결과 green.
8. **prepare-merge로 RESULT.md를 Claude worktree로 이동** → verify: Claude worktree의 `.agent_tasks/codex_done/TASK_2026_05_23_SYNC_PROBE_RESULT.md` 존재.
9. **최종 감사 보고서 작성** → verify: `.agent_tasks/codex_archive/<ts>_sync_plan.md`에 실행 결과 (각 단계의 verify 결과, 발견된 이슈, post-sync 상태) 추가 기록.

---

## 11. Completion Criteria

다음이 **모두** 만족될 때만 본 작업을 "완료"로 선언한다.

| # | 기준 | 검증 방법 |
|---|---|---|
| C1 | Codex worktree HEAD == Claude HEAD (`58ad48d` 또는 sync 시점 Claude HEAD) | `git -C <codex> rev-parse HEAD` |
| C2 | Codex worktree `git status --short` 빈 결과 | 위 명령 |
| C3 | Codex worktree에 `src/frcgw/`, `paper_context_ref/` 없음 | `Test-Path` |
| C4 | Codex worktree에 `src/fglc/` 존재 | `Test-Path` |
| C5 | Codex worktree의 `.agent_tasks/codex_done/TASK_LFD_001~007_RESULT.md` 보존 | `Get-ChildItem` |
| C6 | Codex worktree의 `.agent_tasks/archive/2026-05/` 보존 | 위 |
| C7 | Codex worktree의 `.env` 보존 (사이즈·SHA 변동 없음) | `Get-FileHash` |
| C8 | `.agent_tasks/codex_archive/<ts>_pre_sync_*` 8개 백업 파일 모두 존재 | `Get-ChildItem` |
| C9 | `.agent_tasks/codex_prompt_template.md` 새 50줄 버전 + `AGENTS.md` Codex worktree에 존재 | 위 |
| C10 | Sync probe TASK가 종료 코드 0으로 완료 | 하네스 summary.json |
| C11 | Sync probe RESULT.md가 8섹션 완비 + FILES_FORBIDDEN 침범 0 | 수동 review |
| C12 | Claude worktree의 `.agent_tasks/codex_done/`에 sync probe RESULT.md 도착 | `Test-Path` |
| C13 | 어떤 단계에서도 사용자에게 보고된 BLOCKER가 없거나, 보고된 BLOCKER는 모두 사용자가 명시 승인 | 본 PLAN의 §12 항목 0 |

---

## 12. BLOCKED / UNKNOWN

### 12.1 UNKNOWN (사용자 결정 필요)
- **U1**: 200+개 stale `.agent_tasks/codex_queue/` 파일을 (A) 그대로 보존 / (B) `.agent_tasks/codex_archive/2026-05-23_pre_pivot_stale_queue/`로 이관할지. PLAN 기본값: (A) 보존 (untracked, fast-forward에 영향 없음). 사용자가 명시 승인 시 (B) 실행.
- **U2**: `codex_prompt_template.md`의 "Before committing" vs "After committing" wording — RESULT.md를 commit에 포함하는 게 contract라면 "Before". 사용자 확인 권고. PLAN 기본값: **"Before committing"** 유지 (현 on-disk 동작 보존).
- **U3**: `AGENTS.md`를 Claude worktree에 tracked로 작성하여 fast-forward로 전파할지, Codex worktree에서만 별도 commit할지. PLAN 기본값: **tracked로 양쪽 공유** (single source-of-truth, drift 방지).
- **U4**: `@openai/codex` 바이너리가 `AGENTS.md`를 자동 로드하는지 미확인. PLAN은 자동 로드를 가정하지 않고, stdin template에 "If AGENTS.md exists, read it before edits"를 추가하여 explicit 강제.
- **U5**: `.claude/rules/codex_orchestration_rules.md`의 패키지명 drift (`src/fglc/` vs `src/frcgw/schemas/`) — 본 PLAN scope 밖, 별도 PR로 분리 권고. 사용자 우선순위 결정 필요.
- **U6**: T3 implementation-risk-critic agent를 sync probe accept 전에 호출할지. sync probe는 trivial(파일 1-2개 추가)이므로 PLAN 기본값: **생략 가능**, 단 사용자가 audit을 원하면 추가.
- **U7**: Claude worktree의 `.self_evolving_memory/hooks/hook_execution_log.md` 수정 및 `outputs/lifecycle/.gitkeep` 삭제 (Pre-existing dirty state)는 본 sync와 무관 — sync 전에 commit/stash할지 사용자 결정. PLAN 기본값: **이 PLAN 외부 이슈로 분리**.

### 12.2 BLOCKED
- 없음. 모든 단계가 기술적으로 실행 가능. (사용자 승인만 필요)

---

## 13. 산출물 위치 요약

```text
# Sync 백업 (Claude worktree)
.agent_tasks/codex_archive/<ts>_pre_sync_status.txt
.agent_tasks/codex_archive/<ts>_pre_sync_diff.patch
.agent_tasks/codex_archive/<ts>_codex_head.txt
.agent_tasks/codex_archive/<ts>_codex_branch.txt
.agent_tasks/codex_archive/<ts>_untracked_files.txt
.agent_tasks/codex_archive/<ts>_codex_queue_inventory.txt
.agent_tasks/codex_archive/<ts>_codex_done_inventory.txt
.agent_tasks/codex_archive/<ts>_sync_plan.md           # 본 PLAN 사본 + 실행 결과

# 갱신된 contract 파일 (양쪽 worktree에 fast-forward 전파)
.agent_tasks/codex_prompt_template.md                  # ~50줄 신버전
AGENTS.md                                              # Codex worktree root, ~80-120줄

# init-embedded template 동기화
scripts/run_codex_task.ps1 (lines 230-251)             # template drift 해소

# Sync probe 결과
.agent_tasks/codex_done/TASK_2026_05_23_SYNC_PROBE_RESULT.md   (Codex worktree → prepare-merge → Claude worktree)
.agent_tasks/codex_done/TASK_2026_05_23_SYNC_PROBE_HANDOFF.md  (위와 동일 경로)
.agent_tasks/codex_logs/RUN_<ts>_TASK_2026_05_23_SYNC_PROBE.{jsonl,err.log,summary.json,_lastmsg.txt}  (Claude worktree)

# 새로 만들지 않는 항목
.codex/                  # 미생성 — Codex CLI 자동 로드 보장 없음
rules/                   # 미생성 — Codex CLI가 자동 로드하지 않음, AGENTS.md로 대체
docs/codex_sub_agent/    # 미생성 — 기존 구조 재사용 원칙
```

---

## 14. 금지 (PLAN 실행 중 자체 강제)

- Codex worktree를 `git reset --hard` 또는 `git clean -fdx`로 다루기 — 절대 금지.
- Codex worktree의 `.env`, `.venv/`, `.lifecycle_trash/`, `.self_evolving_memory/` 접근 — 절대 금지.
- Codex worktree에 `.claude/`를 복사 — 절대 금지.
- Codex worktree에 CLAUDE.md를 복사 — 절대 금지.
- `.agent_tasks/codex_queue/` 200+ stale 파일을 사용자 승인 없이 삭제 — 절대 금지.
- 새 docs/, rules/, .codex/ 디렉토리 신설 — 본 PLAN scope에서는 금지.
- Sync probe 외 실제 코드/모델/데이터/평가 코드를 같은 commit에 묶기 — 금지.
- Codex 결과를 review 없이 main worktree에 자동 반영 — 금지.
- `origin`으로 push — 본 PLAN의 어떤 단계도 push를 포함하지 않음.

---

> **End of PLAN.**
> 사용자 승인을 받으면 본 PLAN의 §10 "Execution Plan After Approval" 단계를 순서대로 실행한다.
> 승인 전에는 본 plan 파일(`plans/md-task-claude-wondrous-unicorn.md`) 외 어떤 파일도 수정하지 않는다.
