# P1_5_PLUGIN_SKILL_AGENT_HOOK_PIPELINE_PLAN.md

---

## 0. Context

이 변경의 동기는 다음과 같다.

1. P0 scaffold(2025-... `290eb43`)와 P1 schema/visibility(`b5e4777`)가 이미 끝났고, working tree는 clean, 53개 pytest 전부 통과한다. 다음 단계는 P2 (text-only data generator)이지만, P2 이후의 모든 phase(데이터 생성, 학습, 평가)는 schema/leakage/baseline/ablation invariant를 위반할 위험이 P1의 schema 작업보다 훨씬 높다.
2. 현재 harness는 4개 hook(`session_start_context.ps1`, `pre_tool_guard.ps1`, `post_edit_audit.ps1`, `stop_summary_guard.ps1`) + 1개 command(`read-paper-context`) + 1개 MCP(Context7) 수준이다. 이 정도로는 P2 이후 phase-gate, leakage, baseline drift, fake-result, plugin/MCP 위험을 자동으로 막을 수 없다.
3. CLAUDE.md "Implementation Policy" + `13_..._ROADMAP_v1.md` §16 quality gates + `14_TRD_..._v1.md` SYS-REQ-009/010/011은 폐루프 검증(`config → test → leakage → coverage → baseline/ablation → report`)을 요구한다. 현재 harness는 PreToolUse 차단/PostToolUse 경고는 있지만, phase-gate 강제, baseline 누락 감지, subagent 분리, 외부 plugin audit가 모두 빠져 있다.

목표 결과(요약):
- P1.5-A: project-local skill 7개, subagent 7개, hook 4개 추가, command 2개 추가, settings hook registration 갱신.
- P1.5-B: 외부 plugin/MCP는 **이번 단계에서 0건 설치**. 모든 외부 후보는 audit-only(superpowers) 또는 reject(github MCP, skill-creator, code-review, code-simplifier, claude-md-management) 또는 install-later(Playwright MCP at P4).
- `paper_context_ref/` 원본은 절대 수정하지 않는다.
- pytest는 P1과 동일하게 전부 통과한다(새 hook이 false-positive를 만들지 않는다).
- P2를 시작하기 전에 6개 폐루프 pipeline이 활성화되어, P2~P6 phase 모두 동일한 검증 계약을 받는다.

---

## 1. Current Harness Diagnosis

### 1.1 git/working tree state (관측값)
- branch: `feat/p1-schema-visibility`, working tree clean.
- recent commits: `b5e4777` chore(p1) finalize, `3b9773b` feat(p1) implement, `e739715`/`31cf778` hooks fix, `290eb43` P0 scaffold.
- `paper_context_ref/` 18개 MD 모두 존재, 마지막 수정은 P0 시점.

### 1.2 Claude harness state (관측값)
- `claude --version` = `2.1.133`.
- `claude mcp list` → `context7: HTTP, ✓ Connected`. 기타 MCP 없음.
- `.claude/settings.json`: `model=opusplan`, `showClearContextOnPlanAccept=true`, hooks={PreToolUse[Bash|Edit|Write|NotebookEdit], PostToolUse[Edit|Write|NotebookEdit], Stop}. 모두 forward-slash path.
- `.claude/settings.local.json`: `enableAllProjectMcpServers=true`, `enabledMcpjsonServers=["context7"]`, allow에 `Skill(update-config)`, `Bash(python *)`, `Bash(claude --version)`, `Bash(claude mcp *)`, 두 개 Test-Path.
- `.claude/hooks/`: 4개 ps1 (위 4개). PowerShell 5.1, NonInteractive, JSON stdin → stdout warning/exit-1 block.
- `.claude/commands/`: `read-paper-context.md` (router용 slash command).
- `.claude/rules/`: `research_context_rules.md`.
- `.claude/agents/`: **존재하지 않음**.
- `.claude/skills/`: **존재하지 않음**.
- `.mcp.json`: project-scope에 context7 HTTP만.
- 사용 가능한 built-in skill: `/init`, `/review`, `/security-review`, `/simplify`, `/loop`, `/schedule`, `/claude-api`, `/update-config`, `/keybindings-help`, `/fewer-permission-prompts`, project-skill `/read-paper-context`.

### 1.3 Test/scaffold state (관측값)
- `src/frcgw/` 11개 sub-package, 4개 schema 모듈(`visibility.py`, `episode_schema.py`, `step_schema.py`, `validation.py`) + `data/leakage_auditor.py`.
- `tests/`: 9개 (P0 4개 + P1 4개 + `__init__`). `pytest -q` 결과 53 passed.
- `scripts/`: 10개 placeholder (00~09).
- `configs/`: 7개 yaml skeleton.
- `plans/`: `P0_REPO_SCAFFOLD_PLAN.md` 1개.

### 1.4 진단 결론
- **P0/P1 완료, working tree clean, 외부 plugin 0개, MCP 1개(Context7), hooks 4개 모두 정상.**
- harness는 *기본 안전망*은 갖췄지만 *phase-gate 강제, subagent 책임 분리, baseline drift 감지, plugin audit, targeted test 자동화*가 모두 결여됨. P2 이후 위험이 가파르게 올라가므로 P1.5에서 harness를 한 단계 끌어올린다.

### 1.5 P1.5에서 손대지 않을 것
- `paper_context_ref/` 18개 MD 원본.
- 기존 4개 hook의 동작(추가는 하되 기존 로직 변경 없음).
- Context7 MCP 연결.
- `.claude/settings.local.json`의 기존 permission allow list (필요 시 add-only).

---

## 2. Official Docs / Marketplace / GitHub Research

다음을 직접 검증했다(WebFetch + 공식 docs).

| Source | Verified Fact |
|---|---|
| `code.claude.com/docs/en/plugins` | Plugin manifest = `.claude-plugin/plugin.json`. 디렉토리 root에 `skills/`, `commands/`, `agents/`, `hooks/`, `.mcp.json`, `.lsp.json`, `monitors/`, `bin/`, `settings.json` 가능. Plugin은 자체 hook + MCP + monitor를 동봉할 수 있어 **trust surface가 넓다**. 표준 install: `/plugin marketplace add <repo>` → `/plugin install <plugin>@<marketplace>`. 로컬 테스트: `claude --plugin-dir ./path`. |
| `github.com/anthropics/skills` | 공식 Anthropic skills 카테고리 = Creative & Design, Development & Technical, Enterprise & Communication, Document Skills(docx/pdf/pptx/xlsx). **`skill-creator`, `code-review`, `claude-md-management`라는 이름의 official plugin은 존재하지 않는다.** Custom skill = `<folder>/SKILL.md` (frontmatter `name`, `description`)로 직접 작성하는 것이 canonical. |
| `github.com/obra/superpowers-marketplace` | 실재. 940⭐. 4개 plugin 동봉: Superpowers(core, 20+ skills), Elements of Style, Developing-for-Claude-Code, Private Journal MCP. SessionStart context injection 메커니즘 동봉. install: `/plugin marketplace add obra/superpowers-marketplace`. |
| `github.com/github/github-mcp-server` | 공식 GitHub Inc. 제공. v1.0.3 (2026-04-24). Windows 권장 설치 = Docker `ghcr.io/github/github-mcp-server`. **`GITHUB_PERSONAL_ACCESS_TOKEN` env var 필수**, gh CLI passthrough 미지원. README도 PAT 노출 위험을 명시. |
| `github.com/microsoft/playwright-mcp` | 공식 Microsoft 제공. v0.0.75 (2026-05-07). 32.2k⭐. install: `claude mcp add playwright npx @playwright/mcp@latest`. README 인용: "Playwright MCP is **not** a security boundary." |
| `mcp.context7.com/mcp` | 이미 `.mcp.json`에 HTTP 등록, `claude mcp list` 에서 ✓ Connected. 별도 plugin 불필요. |
| Built-in skill `/review`, `/security-review`, `/simplify`, `/init` | 현재 세션 available skills 목록에 확인됨. 별도 plugin 설치 없이 즉시 호출 가능. |

### 2.1 검증 한계 (정직한 표기)
- superpowers의 hook/MCP 권한 세부는 marketplace README 만으로는 fully audit 불가. P1.5-A에서 audit pipeline을 만들어 *나중에* 정밀 검토할 것.
- GitHub MCP의 fine-grained scope, OAuth 모드는 README에 일부만 노출. user-scope 전용 설치도 PAT가 OS env에 살아 있어야 한다는 사실은 변하지 않음 → 본 프로젝트 정책상 reject.

---

## 3. Plugin and MCP Recommendation Matrix

| name | category | official status | source | install command (검증된 경우) | bundled | net | file write | secret | win risk | FRCG benefit | conflict | Decision | Reason |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| superpowers | marketplace plugin | community-marketplace | obra/superpowers-marketplace, 940⭐ | `/plugin marketplace add obra/superpowers-marketplace` then `/plugin install superpowers@superpowers-marketplace` | 20+ skills, SessionStart hook, Private Journal MCP | yes | yes | unknown | unknown | 디버깅/테스트 skill 일부 유용 가능 | 자체 SessionStart 동봉 → 우리 `pre_tool_guard`의 daily-sentinel 메커니즘과 의미적으로 겹침 | **AUDIT_ONLY** | hooks/MCP audit 전 install 금지 |
| code-review (third-party plugin) | plugin | community/unverified | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | built-in `/review`와 중복 | **REJECT** | 이름 동일 plugin 검증 실패. built-in /review 사용 |
| code-simplifier (third-party plugin) | plugin | community/unverified | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | built-in `/simplify`와 중복 | **REJECT** | 검증 실패. built-in /simplify 사용 |
| github MCP | MCP server | official (GitHub Inc.) | github/github-mcp-server v1.0.3 | (지금 실행 안 함) Docker 또는 npm | github API | yes | no | **PAT 필수** | gh CLI passthrough 미지원 | PR/issue 자동화 | PAT 노출 위험 (사용자 정책 위배) | **REJECT** | gh CLI(이미 사용 가능)로 100% 대체 |
| skill-creator | plugin | unverified | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | 우리 frcgw-skill-scaffold custom command가 더 안전 | **REJECT** | 공식 skills repo에 부재 |
| claude-md-management | plugin | does-not-exist | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | built-in `/init` + 우리 frcgw-paper-framing skill로 충분 | **REJECT** | 존재 미확인 |
| Context7 MCP | MCP server (HTTP) | official-vendor (Upstash) | mcp.context7.com | already in `.mcp.json` | docs MCP | yes | no | none | none | 라이브러리 문서 lookup | none | **KEEP AS-IS** | 이미 ✓ Connected |
| Playwright MCP | MCP server | official-vendor (Microsoft) | microsoft/playwright-mcp v0.0.75 | `claude mcp add playwright npx @playwright/mcp@latest` (P4 시) | browser automation | yes (브라우저 launch) | yes (trace) | none | "not a security boundary" 자체 경고 | P4 synthetic GUI MVE에 필수 | none (P4 까지는 미설치) | **INSTALL_LATER (P4)** | P1~P3에서는 불필요 |

### 3.1 Built-in slash command 정책 (확정)
- `/review`, `/security-review`, `/simplify`, `/init`, `/read-paper-context`, `/loop`, `/schedule`, `/update-config`, `/fewer-permission-prompts`, `/claude-api`, `/keybindings-help`는 즉시 사용 가능.
- 본 P1.5-A는 `/review`, `/simplify`, `/init`를 **wrap**하는 FRCG guard skill을 만들고, 직접 호출은 wrap을 통과한 후에만 허용.

### 3.2 결론
- **P1.5에서 외부 plugin/MCP install 0건.** 모든 외부 후보는 audit-only(superpowers) / install-later(Playwright @ P4) / reject(나머지).
- 모든 효과는 project-local `.claude/` 자산으로 달성한다.

---

## 4. Project-Local Skill Architecture

경로: 모두 `.claude/skills/<name>/SKILL.md` (project-local, version-controlled).

skill frontmatter 표준:
```yaml
---
name: <kebab-case>
description: <one-line, model-invocable description>
---
```

> Note: built-in `/skill` 호출 형식은 `Skill(name=<frcgw-...>)`로 가능. project-local skill은 plugin namespace 없이 단명(short-name)으로 호출됨.

### 4.1 `.claude/skills/frcgw-phase-gate/SKILL.md`
- **purpose**: P0~P8 phase 시작/종료 시 Read/Phase/Changed/Tests/Gate/Blockers 강제. PASS 전 다음 phase 금지.
- **when to use**: 사용자가 "P2 시작", "P3 끝났다", "phase X 진행" 같은 발화를 할 때, 또는 `frcgw-phase-check` command 호출 시.
- **source MDs**: `13_..._ROADMAP_v1.md` §5 phase overview + §16 gates, `14_..._TRD_v1.md` §10 acceptance, `00_CONTEXT_INDEX.md` §5 phase router.
- **forbidden actions**: gate 미통과 상태에서 다음 phase 코드/데이터/학습 작업 시작; phase artifact를 짜증나게 한 채로 status PASS 마크.
- **required checklist**:
  1. 어떤 MD 읽었는가
  2. 현재 phase + 직전 gate status
  3. 변경/생성된 파일 목록
  4. 실행한 pytest + 새로 추가된 테스트
  5. baseline/ablation must-not-disappear 위반 여부
  6. Blockers 또는 `none`
- **required output format**: `Read:` / `Phase:` / `Changed/Created:` / `Tests/Gates:` / `Blockers:` (CLAUDE.md 응답 정책과 일치).
- **connected subagents**: `frcgw-test-runner`, `frcgw-experiment-evaluator`.
- **connected hooks**: `phase_gate_guard.ps1`, `user_prompt_phase_router.ps1`.
- **phase relevance**: ALL.
- **pass/fail gate**: gate 통과 못 하면 응답 끝에 `BLOCKED` + 이유 명시.

### 4.2 `.claude/skills/frcgw-data-safety/SKILL.md`
- **purpose**: schema, dataloader, collator, batch input, action-effect log, counterfactual shard 작업 시 hidden label / counterfactual / audit metadata가 inference input에 들어가지 않도록 보장.
- **when to use**: `src/frcgw/schemas/`, `src/frcgw/data/`, `src/frcgw/text_env/collector.py`, `src/frcgw/gui_env/collector.py`, `src/frcgw/logging/`에 변경이 일어날 때.
- **source MDs**: `06_DATA_SCHEMA_AND_LABELING.md` §0.3 naming contract / §4 visibility / §0.4 MVE subset / §14 audit, `12_DATA_COLLECTION_METHODOLOGY_v1.md`.
- **forbidden actions**: forbidden field 목록(`true_regime`, `true_control_grammar`, `true_change_point`, `true_reveal_vs_shift`, `true_wrong_hypothesis`, `counterfactual_*`, `oracle_*`, `split_id`, `ood_type`, `template_id`, `seed`, `policy_id`, `audit_metadata`)을 agent observation/dataloader input/model input/prompt에 통과시키는 것.
- **required checklist**:
  1. 변경 파일이 visibility bucket을 명시했는가 (`AGENT_OBSERVATION` / `TRAINING_SUPERVISION` / `EVALUATION_ONLY` / `COUNTERFACTUAL_ONLY` / `AUDIT_METADATA`)
  2. `build_agent_observation()` 또는 동치 함수가 forbidden field를 strip 하는가
  3. counterfactual shard가 별도 file/struct에 격리됐는가
  4. `tests/test_visibility_contract.py` + `tests/test_counterfactual_exclusion.py` + `tests/test_leakage_auditor.py` 실행됐는가
  5. P1 통과 testcase가 그대로 통과하는가
- **required output**: visibility audit table + 위 5개 항목의 각 ✓/✗.
- **connected subagents**: `frcgw-data-leakage-auditor` (Read/Grep만, Write 금지).
- **connected hooks**: `schema_leakage_guard.ps1`, 기존 `post_edit_audit.ps1`(스키마 파일 시 LEAKAGE RISK 메시지).
- **phase relevance**: P1, P2, P4, P6.
- **pass/fail gate**: forbidden field가 obs/input path에 1개라도 섞이면 즉시 STOP, dataset shard 무효 선언.

### 4.3 `.claude/skills/frcgw-test-quality/SKILL.md`
- **purpose**: pytest targeted/full 실행, failure summary, fix loop, full gate test 수행.
- **when to use**: 코드/스크립트/스키마 변경 직후, phase gate 직전, 또는 사용자가 "tests" 언급 시.
- **source MDs**: `14_..._TRD_v1.md` §10 acceptance criteria, `13_..._ROADMAP_v1.md` §16 gates.
- **forbidden actions**: 실패한 테스트를 무시하고 다음 작업 진행; `--ignore`로 광범위하게 skip; failure 원인을 "intermittent"라고 단정.
- **required checklist**:
  1. 어떤 파일이 변경됐고 어떤 testcase가 영향받는가 (target mapping)
  2. targeted pytest 결과
  3. 실패 시: 원인 분석 1줄 + 수정 계획 + 다시 실행
  4. phase gate 직전이면 full pytest 실행
  5. 결과를 `outputs/test_reports/<UTC-timestamp>.txt`에 저장
- **required output**: target test list + result summary + (실패 시) fix plan.
- **connected subagents**: `frcgw-test-runner` (Bash 허용, Write/Edit 금지).
- **connected hooks**: `post_edit_targeted_tests.ps1` (자동 실행 아님 — 권고 메시지만).
- **phase relevance**: ALL.
- **pass/fail gate**: full pytest red 상태에서는 phase gate PASS 불가.

### 4.4 `.claude/skills/frcgw-experiment-design/SKILL.md`
- **purpose**: P3/P5/P6 실험 설계에서 `claim → metric → baseline → ablation → split → pass/fail → failure interpretation`을 1:1로 고정.
- **when to use**: P2~P6 실험 config 작성, eval runner 수정, ablation runner 수정, paper claim drafting 시.
- **source MDs**: `10_EVALUATION_BASELINE_ABLATION.md` §5 claim-to-evidence, §6 metric, §7 baseline, §8 ablation, §11 compute-matched, §13 reviewer attack, §14 failure interpretation.
- **forbidden actions**: success rate만 보고; baseline 누락(특히 verifier-only / next-state-WM-only / uncertainty-gated / always-plan / no-control-grammar / no-falsification / random alternative); compute mismatch; cherry-pick.
- **required checklist**: claim ID 명시 → 필요한 metric/baseline/ablation/split이 config/runner에 모두 존재 → compute log 활성 → failure interpretation 섹션 plan에 포함.
- **required output**: claim-evidence table (해당 phase 한정).
- **connected subagents**: `frcgw-experiment-evaluator` (Read/Grep, Bash 제한).
- **connected hooks**: `baseline_ablation_guard.ps1`.
- **phase relevance**: P3, P5, P6.
- **pass/fail gate**: must-not-disappear baseline/ablation 1개라도 누락 시 STOP.

### 4.5 `.claude/skills/frcgw-code-review/SKILL.md`
- **purpose**: built-in `/review`, `/simplify` 결과를 FRCG-WM scientific contract 관점에서 재해석하는 wrapper. simplification이 baseline/ablation/visibility/term을 망가뜨리지 않도록 감시.
- **when to use**: 사용자가 "code review", "simplify", "리뷰" 언급 시 또는 PR 생성 직전.
- **source MDs**: CLAUDE.md (Implementation/Response Policy), `.claude/rules/research_context_rules.md` (terms must-preserve, baselines must-not-disappear).
- **forbidden actions**: built-in `/simplify`의 자동 edit 결과를 검토 없이 그대로 수용; baseline 이름/ablation 이름/term(`control grammar`, `regime`, `current hypothesis`, `falsification evidence` 등) 변경; visibility bucket을 단순화 명목으로 평탄화.
- **required checklist**:
  1. built-in `/review` 또는 `/simplify` 호출 결과 캡처
  2. diff에서 baseline/ablation/term 변경 여부 grep
  3. visibility bucket 변경 여부 확인
  4. 변경이 anti-pattern이면 reject 사유 + 대안 제시
- **required output**: review summary + accept/reject diffs + 사유.
- **connected subagents**: `frcgw-code-reviewer`.
- **connected hooks**: 없음 (skill-driven).
- **phase relevance**: ALL.
- **pass/fail gate**: term/baseline/ablation drift 감지 시 reject 권고.

### 4.6 `.claude/skills/frcgw-plugin-audit/SKILL.md`
- **purpose**: 외부 plugin/MCP 설치 *전*에 source/permission/hook/MCP/script/network/secret/Windows risk를 audit.
- **when to use**: `/plugin install ...`, `/plugin marketplace add ...`, `claude mcp add ...` 같은 발화 또는 명령 시도 시 (즉, **install 직전**).
- **source MDs**: 본 plan §2~§3, `code.claude.com/docs/en/plugins`.
- **forbidden actions**: blind install; project-scope에 PAT/token 등록; project-scope에 `enableAllProjectMcpServers=true` 추가 (이미 있음 — 확장만 금지); hook을 동봉한 plugin을 audit 없이 활성화.
- **required checklist** (10 items):
  1. plugin/MCP의 official 여부 (vendor or marketplace)
  2. source repo URL + 마지막 commit 일자 + ⭐ 수
  3. issue tracker에서 Windows compatibility / hook 충돌 / 보안 항목 검색
  4. plugin manifest(`.claude-plugin/plugin.json`)와 동봉 디렉토리 구조 확인 (skills/agents/hooks/.mcp.json/.lsp.json/monitors/bin/settings.json 중 무엇이 있는가)
  5. 동봉 hook이 우리 PreToolUse/PostToolUse/Stop matcher와 충돌 가능성 평가
  6. 동봉 MCP의 network endpoint, auth 모드, secret 요구
  7. file write 범위
  8. install scope 권장(user vs project) — PAT/token이 필요하면 무조건 user scope
  9. uninstall 절차(rollback path)
  10. 위 9개를 통과한 경우에만 install-later candidate로 PROMOTE
- **required output**: `plans/PLUGIN_AUDIT_REPORT.md`에 항목 추가.
- **connected subagents**: `frcgw-plugin-security-auditor`.
- **phase relevance**: ALL (특히 P1.5-B, P4 Playwright).
- **pass/fail gate**: 위 10개 중 unknown/red 1개라도 있으면 install 보류.

### 4.7 `.claude/skills/frcgw-paper-framing/SKILL.md`
- **purpose**: abstract/intro/related work/limitation 작성 시 generic Web/GUI world model claim으로 흐르는 것을 방지.
- **when to use**: paper-main draft, claim wording, related work 작성 시.
- **source MDs**: `00_MASTER_REFERENCE.md`, `01_RELATED_WORK_THREAT_MAP.md` (WebWorld/CUWM/WAC/VeriGUI), `02_PROBLEM_NOVELTY_FALSIFICATION.md`, `10_EVALUATION_BASELINE_ABLATION.md` §13 reviewer defense, `FINAL_RESEARCH_BLUEPRINT.md`.
- **forbidden actions**: "generic Web/GUI world model" novelty 주장; success rate만으로 mechanism claim; direct threat(WebWorld/CUWM/WAC/VeriGUI)을 무시; unresolved Unknown을 final claim으로 승격.
- **required checklist**: claim → 대응 metric → 대응 baseline/ablation → 대응 split → reviewer attack 대응.
- **required output**: claim sheet + threat map.
- **connected subagents**: `frcgw-related-work-scout`.
- **phase relevance**: P7, P8.
- **pass/fail gate**: claim 1개라도 supporting metric/baseline/ablation 부재 시 reject.

---

## 5. Project-Local Subagent Architecture

경로: 모두 `.claude/agents/<name>.md` (project-local). frontmatter 표준:
```yaml
---
name: <name>
description: <when to use, model-invocable>
tools: <comma-separated allow list, 또는 inherit>
model: sonnet | haiku | opus | inherit
---
```

원칙:
- **implementation은 main agent만**, subagent는 검증/리뷰/테스트/분석 중심.
- subagent 간 책임 분리 명확히. Read/Grep만으로 충분한 작업에 Bash/Edit/Write 금지.

### 5.1 `frcgw-context-router`
- **description**: "Use when the user mentions a phase or task type and the right paper_context_ref bundle is unclear. Routes to the minimum required MD bundle."
- **model**: haiku (저비용 routing).
- **allowed tools**: Read, Glob, Grep.
- **disallowed**: Bash, Edit, Write, NotebookEdit, WebFetch, WebSearch.
- **source MDs**: `00_CONTEXT_INDEX.md` §4 task router + §5 phase router.
- **task type**: read-only routing.
- **invocation example**: "I'm starting P3 text-only model and planner — what should I read first?"
- **output format**: `Read first:` `Then read:` `Do not assume:`.
- **fail condition**: 권장 MD 목록이 task와 무관하면 main agent가 reject.
- **when not to invoke**: task가 명확히 1개 MD에 묶일 때.

### 5.2 `frcgw-data-leakage-auditor`
- **description**: "Use when schema/dataloader/collector/logger files change. Audits for hidden-label, counterfactual, audit-metadata leakage into inference input."
- **model**: sonnet.
- **allowed tools**: Read, Glob, Grep.
- **disallowed**: Bash, Edit, Write, NotebookEdit, WebFetch, WebSearch.
- **source MDs**: `06_DATA_SCHEMA_AND_LABELING.md` §0.3, §4, §14, §15.
- **task type**: code-pattern audit (forbidden field 검색, build_agent_observation 호출 그래프, counterfactual shard isolation).
- **invocation example**: "Audit `src/frcgw/schemas/*.py` and `src/frcgw/data/leakage_auditor.py` against forbidden-field list."
- **output format**: forbidden-field hit table + visibility bucket coverage.
- **fail condition**: 1건이라도 hit이면 BLOCK.
- **when not to invoke**: 파일이 `tests/` 또는 `paper_context_ref/`일 때.

### 5.3 `frcgw-test-runner`
- **description**: "Use when targeted or full pytest must run. Reports failures and proposed fix path."
- **model**: sonnet.
- **allowed tools**: Bash (`pytest`만), Read, Glob, Grep.
- **disallowed**: Edit, Write, NotebookEdit, WebFetch, WebSearch, `git push|reset|clean` 류.
- **source MDs**: `14_..._TRD_v1.md` §10 acceptance.
- **task type**: 실행 + summary. 코드 수정은 main agent로 핸드오프.
- **invocation example**: "Run targeted tests for changes to `src/frcgw/schemas/visibility.py`."
- **output format**: changed files → target test list → result → fix plan(있다면).
- **fail condition**: 같은 testcase가 2회 연속 fail하면 root-cause를 명시하고 main agent에 위임.
- **when not to invoke**: phase gate 진단 외 routine query.

### 5.4 `frcgw-code-reviewer`
- **description**: "Use after Edit/Write to non-trivial code (planner, model, eval, schema). Reviews for FRCG-WM contract drift."
- **model**: sonnet.
- **allowed tools**: Read, Glob, Grep.
- **disallowed**: Bash, Edit, Write, NotebookEdit.
- **source MDs**: CLAUDE.md, `.claude/rules/research_context_rules.md`, `03_CORE_CONCEPT_TAXONOMY.md`(terms must-preserve), `10_..._BASELINE_ABLATION.md`(baselines must-not-disappear).
- **task type**: read-only review. Term drift, baseline 누락, ablation 누락, visibility bucket 평탄화 감지.
- **invocation example**: "Review the diff in `src/frcgw/planning/falsification.py` for term/baseline drift."
- **output format**: accept/reject diffs + 사유.
- **fail condition**: term이 silently rename됐거나 baseline이 사라졌으면 reject.
- **when not to invoke**: docs-only diff (paper_context_ref는 별도 흐름).

### 5.5 `frcgw-experiment-evaluator`
- **description**: "Use when interpreting eval/ablation outputs and deciding phase gate pass/fail."
- **model**: sonnet.
- **allowed tools**: Read, Glob, Grep, Bash(`pytest`만).
- **disallowed**: Edit, Write, NotebookEdit, WebFetch, WebSearch.
- **source MDs**: `10_..._BASELINE_ABLATION.md` §5, §6, §11, §14.
- **task type**: 결과 해석. compute-matched 비교 의무 검증, no-control-grammar/no-falsification ablation 감도 검증, success-rate-only 결과 거부.
- **output format**: claim-by-claim PASS/FAIL/INSUFFICIENT-EVIDENCE.
- **fail condition**: required baseline/ablation 결과 부재 또는 compute log 부재.

### 5.6 `frcgw-related-work-scout`
- **description**: "Use during paper framing to verify direct threats (WebWorld, CUWM, WAC, VeriGUI) are addressed."
- **model**: sonnet.
- **allowed tools**: Read, Glob, Grep, WebFetch, WebSearch.
- **disallowed**: Bash, Edit, Write, NotebookEdit.
- **source MDs**: `01_RELATED_WORK_THREAT_MAP.md`, `FINAL_RESEARCH_BLUEPRINT.md`, `10_..._BASELINE_ABLATION.md` §13.
- **task type**: web-search-augmented threat map 갱신.
- **output format**: threat-claim defense table.

### 5.7 `frcgw-plugin-security-auditor`
- **description**: "Use before any plugin/MCP install. Audits source, permissions, hooks, MCP, scripts, network, secret risk, Windows compatibility."
- **model**: sonnet.
- **allowed tools**: Read, Glob, Grep, WebFetch, WebSearch, Bash(`claude mcp list`, `git log`만).
- **disallowed**: Edit, Write, NotebookEdit (config는 main agent만), Bash 광범위 명령.
- **source MDs**: 본 plan §2, `code.claude.com/docs/en/plugins`.
- **task type**: 10-item audit checklist 실행 → `plans/PLUGIN_AUDIT_REPORT.md` 항목 *초안* 작성을 main agent에 핸드오프.
- **output format**: 10-item table + verdict (`install-now` / `install-later` / `audit-only` / `reject`) + 사유.
- **fail condition**: 1개 이상 unknown/red면 verdict=reject 또는 audit-only.

---

## 6. Hook Upgrade Architecture

원칙(이미 검증됨):
- Windows path는 forward slash `./.claude/hooks/...`.
- heavy full pytest는 Edit마다 자동 실행 금지.
- targeted test는 권고만 (강제 실행 X).
- phase gate에서만 full pytest 명시 실행.
- warning(exit 0 + msg)과 blocking(exit 1) 분리.
- `paper_context_ref/` 수정은 강하게 경고 또는 차단.
- forbidden-field leakage 명백한 패턴은 차단.
- baseline/ablation 제거 패턴은 경고.

### 기존 4개 hook은 변경하지 않는다. 아래는 추가 후보.

### 6.1 `.claude/hooks/user_prompt_phase_router.ps1`  (event=`UserPromptSubmit`)
- **matcher**: `*` (모든 prompt에 light-weight scan).
- **purpose**: prompt에 "P[0-8]", "phase X", "data generator", "ablation", "baseline", "leakage" 같은 키워드가 있으면 1줄 hint 출력 (해당 MD 경로 안내).
- **block/warn**: warn only.
- **target**: stdin JSON `prompt` 필드 정규식 스캔.
- **false positive risk**: 낮음. 단순 hint.
- **win path**: `./.claude/hooks/user_prompt_phase_router.ps1`.

### 6.2 `.claude/hooks/phase_gate_guard.ps1`  (event=`PreToolUse`, matcher=`Bash`)
- **purpose**: `pytest -q` 외의 *대규모 실행*(예: `python scripts/02_train_text_smoke.py`, `python scripts/06_train_vlm_mve.py`, `python scripts/04_generate_gui_mve_data.py`)이 trigger되면 **이전 phase gate 통과 sentinel** 존재 여부 확인.
- sentinel 위치: `outputs/phase_gates/<phase>.passed` (manual touch 또는 frcgw-phase-check command가 생성).
- sentinel 부재 → exit 1, 메시지 출력.
- **block/warn**: BLOCK.
- **false positive risk**: 사용자가 sentinel 없이 의도적으로 실행하려는 경우 → uninstall 절차 명시(`/frcgw-phase-check --override` 권장).

### 6.3 `.claude/hooks/schema_leakage_guard.ps1`  (event=`PreToolUse`, matcher=`Edit|Write`)
- **purpose**: edit 대상이 `src/frcgw/schemas/*` / `src/frcgw/data/*` / `src/frcgw/text_env/collector.py` / `src/frcgw/gui_env/collector.py`이고 `new_string`에 forbidden field 토큰(`true_regime`, `true_control_grammar`, `counterfactual_action_effects`, `oracle_*`, `true_change_point`, `true_reveal_vs_shift`, `split_id`, `ood_type`, `template_id`, `seed`)이 *agent observation 컨텍스트로* 들어가는 패턴이 보이면 BLOCK.
- 단순 등장은 경고, 다음 패턴은 BLOCK: `obs[...] = ... true_regime ...`, `agent_input.update({'true_*': ...})`, `dataloader return ... oracle_*`.
- **block/warn**: 강한 정규식 매칭 시 BLOCK, 약한 매칭 시 WARN.
- **false positive risk**: 중간 — schemas 파일 안에서 forbidden field 정의 자체는 OK. 따라서 `bucket=AGENT_OBSERVATION` 또는 `build_agent_observation` 함수 이내 발생만 BLOCK.

### 6.4 `.claude/hooks/post_edit_targeted_tests.ps1`  (event=`PostToolUse`, matcher=`Edit|Write|NotebookEdit`)
- **purpose**: 어떤 testcase가 영향받는지 권고만 출력. **자동 실행 안 함.**
- mapping:
  - `src/frcgw/schemas/*.py` → `tests/test_visibility_contract.py tests/test_episode_schema.py tests/test_counterfactual_exclusion.py`
  - `src/frcgw/data/leakage_auditor.py` → `tests/test_leakage_auditor.py`
  - `src/frcgw/text_env/*.py` → P2 도착 시 `tests/test_text_env*.py`
  - `src/frcgw/planning/*.py` → P3 도착 시 `tests/test_falsification.py tests/test_decision_gate.py`
  - `src/frcgw/evaluation/*.py` → P3+ `tests/test_metrics.py tests/test_eval_runner.py`
  - `configs/*.yaml` → `tests/test_config_validation.py` (있다면)
- **block/warn**: warn only (recommend command).
- **false positive risk**: 매우 낮음.

### 6.5 `.claude/hooks/baseline_ablation_guard.ps1`  (event=`PreToolUse`, matcher=`Edit|Write`)
- **purpose**: edit 대상이 `src/frcgw/evaluation/baselines.py` 또는 `ablations.py` 또는 `configs/ablation_*.yaml`이고 `new_string`에 known baseline/ablation 이름(`verifier-only`, `next-state-WM-only`, `uncertainty-gated`, `always-plan`, `random alternative`, `frozen base`, `no-control-grammar`, `no-falsification`, `no-alternative-hypothesis`, `no-rollout`, `no-rewrite`, `no-progress`, `no-compute-gate`, `merged regime-control grammar`, `collapsed latent`)이 **삭제**되는 패턴이면 WARN(BLOCK 아님 — 정상적 rename일 수 있음).
- **block/warn**: WARN with explicit list of suspected removals.
- **false positive risk**: 중간 — rename일 수 있으므로 차단은 하지 않는다.

### 6.6 `.claude/hooks/subagent_stop_audit.ps1`  (event=`SubagentStop`)
- **purpose**: subagent 가 종료될 때 (1) 어떤 subagent였는지 (2) Edit/Write 결과가 있었는지 (3) data-leakage-auditor/code-reviewer/test-runner는 Edit/Write가 0건이어야 함을 검증.
- 위반 시 stdout에 강한 경고. (Stop 이벤트는 block 불가 — diagnostic only.)
- **false positive risk**: 낮음.

### 6.7 `.claude/hooks/pre_compact_phase_handoff.ps1`  (event=`PreCompact`)
- **purpose**: context compaction 직전, 현재 phase, 직전 gate status, blocker 목록을 `plans/PHASE_PROGRESS.md`에 append하여 다음 turn으로 핸드오프.
- **block/warn**: non-blocking.
- **false positive risk**: 낮음. write가 있으므로 atomic append + UTC timestamp.

### 6.8 settings.json 등록 계획 (P1.5-A에서 변경)

기존 PreToolUse/PostToolUse/Stop은 그대로. 다음 추가:

```jsonc
{
  // 기존 키 유지 + 아래 events 추가
  "hooks": {
    "PreToolUse": [
      { "matcher": "Bash|Edit|Write|NotebookEdit",
        "hooks": [{ "type":"command",
                    "command":"powershell -NonInteractive -NoProfile -ExecutionPolicy Bypass -File ./.claude/hooks/pre_tool_guard.ps1" }] },
      { "matcher": "Bash",
        "hooks": [{ "type":"command",
                    "command":"powershell -NonInteractive -NoProfile -ExecutionPolicy Bypass -File ./.claude/hooks/phase_gate_guard.ps1" }] },
      { "matcher": "Edit|Write",
        "hooks": [{ "type":"command",
                    "command":"powershell -NonInteractive -NoProfile -ExecutionPolicy Bypass -File ./.claude/hooks/schema_leakage_guard.ps1" }] },
      { "matcher": "Edit|Write",
        "hooks": [{ "type":"command",
                    "command":"powershell -NonInteractive -NoProfile -ExecutionPolicy Bypass -File ./.claude/hooks/baseline_ablation_guard.ps1" }] }
    ],
    "PostToolUse": [
      { "matcher": "Edit|Write|NotebookEdit",
        "hooks": [{ "type":"command",
                    "command":"powershell -NonInteractive -NoProfile -ExecutionPolicy Bypass -File ./.claude/hooks/post_edit_audit.ps1" }] },
      { "matcher": "Edit|Write|NotebookEdit",
        "hooks": [{ "type":"command",
                    "command":"powershell -NonInteractive -NoProfile -ExecutionPolicy Bypass -File ./.claude/hooks/post_edit_targeted_tests.ps1" }] }
    ],
    "UserPromptSubmit": [
      { "hooks": [{ "type":"command",
                    "command":"powershell -NonInteractive -NoProfile -ExecutionPolicy Bypass -File ./.claude/hooks/user_prompt_phase_router.ps1" }] }
    ],
    "SubagentStop": [
      { "hooks": [{ "type":"command",
                    "command":"powershell -NonInteractive -NoProfile -ExecutionPolicy Bypass -File ./.claude/hooks/subagent_stop_audit.ps1" }] }
    ],
    "PreCompact": [
      { "hooks": [{ "type":"command",
                    "command":"powershell -NonInteractive -NoProfile -ExecutionPolicy Bypass -File ./.claude/hooks/pre_compact_phase_handoff.ps1" }] }
    ],
    "Stop": [
      { "hooks": [{ "type":"command",
                    "command":"powershell -NonInteractive -NoProfile -ExecutionPolicy Bypass -File ./.claude/hooks/stop_summary_guard.ps1" }] }
    ]
  }
}
```

---

## 7. Closed-Loop Pipelines

각 pipeline은 (skill | subagent | hook | output) 4-tuple로 구성된다.

### Pipeline A — FRCG-PHASE-GATE-LOOP
- skill: `.claude/skills/frcgw-phase-gate/SKILL.md`
- subagent: `frcgw-experiment-evaluator` (PASS/FAIL 판정), `frcgw-test-runner` (gate test)
- hook: `phase_gate_guard.ps1`, `user_prompt_phase_router.ps1`, `pre_compact_phase_handoff.ps1`
- command: `.claude/commands/frcgw-phase-check.md`
- output: `plans/PHASE_PROGRESS.md`, sentinel `outputs/phase_gates/<phase>.passed`
- 역할: 모든 phase 시작/종료에 응답 형식 강제. PASS sentinel 없으면 main scripts/ 실행 차단.

### Pipeline B — FRCG-DATA-SAFETY-LOOP
- skill: `.claude/skills/frcgw-data-safety/SKILL.md`
- subagent: `frcgw-data-leakage-auditor`
- hook: `schema_leakage_guard.ps1`, 기존 `post_edit_audit.ps1` (LEAKAGE RISK 메시지)
- tests: `tests/test_visibility_contract.py`, `tests/test_counterfactual_exclusion.py`, `tests/test_leakage_auditor.py`, `tests/test_episode_schema.py`
- output: pytest report + audit summary
- 역할: schema/dataloader/collector 변경 시 forbidden field가 inference path에 들어가지 않도록 다중 방어.

### Pipeline C — FRCG-TEST-QUALITY-LOOP
- skill: `.claude/skills/frcgw-test-quality/SKILL.md`
- subagent: `frcgw-test-runner`
- hook: `post_edit_targeted_tests.ps1` (권고)
- output: `outputs/test_reports/<UTC>.txt`
- 역할: targeted test 권고 + phase gate full test + fix loop.

### Pipeline D — FRCG-CODE-REVIEW-LOOP
- skill: `.claude/skills/frcgw-code-review/SKILL.md` (built-in `/review`, `/simplify` wrap)
- subagent: `frcgw-code-reviewer`
- output: `outputs/review_reports/<UTC>.md`
- 역할: term drift, baseline 누락, simplification artifact 감지.

### Pipeline E — FRCG-EXPERIMENT-EVIDENCE-LOOP
- skill: `.claude/skills/frcgw-experiment-design/SKILL.md`
- subagent: `frcgw-experiment-evaluator`
- hook: `baseline_ablation_guard.ps1`
- output: `outputs/eval_reports/<UTC>/claim_evidence.json`
- 역할: P3/P5/P6 핵심. claim → metric → baseline → ablation → split → pass/fail 1:1.

### Pipeline F — FRCG-PLUGIN-AUDIT-LOOP
- skill: `.claude/skills/frcgw-plugin-audit/SKILL.md`
- subagent: `frcgw-plugin-security-auditor`
- output: `plans/PLUGIN_AUDIT_REPORT.md`
- 역할: 외부 plugin/MCP install 전 10-item audit. P1.5-B 시작 게이트.

---

## 8. File Creation / Modification Plan

| Path | Purpose | Source Docs | Test/Gate Relevance | Create Now? |
|---|---|---|---|---|
| `.claude/skills/frcgw-phase-gate/SKILL.md` | Pipeline A skill | 13§5/§16, 14§10, 00§5 | gate hook | YES (P1.5-A) |
| `.claude/skills/frcgw-data-safety/SKILL.md` | Pipeline B skill | 06§4/§14, 12 | leakage tests | YES |
| `.claude/skills/frcgw-test-quality/SKILL.md` | Pipeline C skill | 14§10 | pytest | YES |
| `.claude/skills/frcgw-experiment-design/SKILL.md` | Pipeline E skill | 10§5~§14 | eval gate | YES |
| `.claude/skills/frcgw-code-review/SKILL.md` | Pipeline D skill (wraps `/review`/`/simplify`) | CLAUDE.md, 03 terms, 10 baselines | review | YES |
| `.claude/skills/frcgw-plugin-audit/SKILL.md` | Pipeline F skill | this plan §2~§3 | install gate | YES |
| `.claude/skills/frcgw-paper-framing/SKILL.md` | claim drift 방지 | 00,01,02,10,FINAL | paper framing | YES (활용은 P7~) |
| `.claude/agents/frcgw-context-router.md` | MD routing | 00§4/§5 | — | YES |
| `.claude/agents/frcgw-data-leakage-auditor.md` | leakage audit (read-only) | 06 | leakage tests | YES |
| `.claude/agents/frcgw-test-runner.md` | pytest runner (Bash 제한) | 14§10 | pytest | YES |
| `.claude/agents/frcgw-code-reviewer.md` | term/baseline drift | CLAUDE.md, 03, 10 | review | YES |
| `.claude/agents/frcgw-experiment-evaluator.md` | gate verdict | 10§5/§11/§14 | eval gate | YES |
| `.claude/agents/frcgw-related-work-scout.md` | threat map (web 가능) | 01, FINAL | paper | YES (활용은 P7~) |
| `.claude/agents/frcgw-plugin-security-auditor.md` | install pre-audit | this plan §2~§3 | install gate | YES |
| `.claude/hooks/user_prompt_phase_router.ps1` | UserPromptSubmit hint | 00§5 | — | YES |
| `.claude/hooks/phase_gate_guard.ps1` | PreToolUse Bash gate | 13§5 | sentinel | YES |
| `.claude/hooks/schema_leakage_guard.ps1` | PreToolUse Edit/Write leakage | 06§4 | leakage | YES |
| `.claude/hooks/post_edit_targeted_tests.ps1` | PostToolUse test recommend | 14§10 | pytest | YES |
| `.claude/hooks/baseline_ablation_guard.ps1` | PreToolUse Edit/Write baseline drop | 10§7/§8 | baseline | YES |
| `.claude/hooks/subagent_stop_audit.ps1` | SubagentStop diagnostic | this plan §5 | subagent rules | YES |
| `.claude/hooks/pre_compact_phase_handoff.ps1` | PreCompact handoff | 13§5 | handoff | YES |
| `.claude/commands/frcgw-phase-check.md` | sentinel manage + status | 13§16 | gate | YES |
| `.claude/commands/frcgw-plugin-audit.md` | wraps Pipeline F | this plan §6 | install gate | YES |
| `.claude/settings.json` | hook registration 확장 | this plan §6.8 | runtime | YES (additive) |
| `plans/P1_5_PLUGIN_SKILL_AGENT_HOOK_PIPELINE_PLAN.md` | THIS PLAN | — | — | YES (현재 작성중) |
| `plans/PLUGIN_AUDIT_REPORT.md` | Pipeline F 산출물 | this plan §3 | install gate | CREATE EMPTY (initial entries: superpowers AUDIT_ONLY, github MCP REJECT, Playwright INSTALL_LATER@P4) |
| `plans/PHASE_PROGRESS.md` | phase 진행 ledger | 13§5 | gate | CREATE EMPTY (P0=PASS, P1=PASS, P1.5=IN_PROGRESS) |
| `outputs/phase_gates/.gitkeep` | sentinel 디렉토리 | — | gate | YES |
| `outputs/test_reports/.gitkeep` | test report 디렉토리 | — | test | YES |
| `outputs/review_reports/.gitkeep` | review report 디렉토리 | — | review | YES |
| `outputs/eval_reports/.gitkeep` | eval report 디렉토리 | — | eval | YES (디렉토리만) |

**파일 수 합계 (P1.5-A에서 생성)**: 7 skill + 7 agent + 7 hook + 2 command + 1 settings 수정 + 1 plan(이 파일) + 2 ledger + 4 .gitkeep = **31개**.

**P1.5-A에서 절대 변경하지 않는 파일**:
- `paper_context_ref/*` 18개 MD
- `CLAUDE.md`
- `.claude/rules/research_context_rules.md`
- 기존 4개 hook (`session_start_context.ps1`, `pre_tool_guard.ps1`, `post_edit_audit.ps1`, `stop_summary_guard.ps1`)
- 기존 command `read-paper-context.md`
- `.mcp.json` (Context7 외 추가 금지)
- `.claude/settings.local.json` (allow list 추가는 사용자 동의 후)
- `src/frcgw/**`
- `tests/**`
- `configs/**`
- `scripts/**`

---

## 9. Install Policy: P1.5-A vs P1.5-B

### P1.5-A — Local harness first (이번 turn 직후 진행)
- 외부 plugin/MCP install **0건**.
- §8 표의 "Create Now? = YES" 31개 파일 생성/수정.
- `.claude/settings.json`에 hook 4개 event 추가 (UserPromptSubmit, SubagentStop, PreCompact + PreToolUse/PostToolUse 새 entry).
- pytest 53개 그대로 통과 확인.
- 새 hook이 false positive로 다른 작업을 막지 않는지 sanity check (간단한 Edit, Bash, UserPrompt 흐름 1회씩 시연).
- 산출물: `plans/PLUGIN_AUDIT_REPORT.md` 초기 entries 3건(superpowers AUDIT_ONLY, github MCP REJECT, Playwright INSTALL_LATER@P4), `plans/PHASE_PROGRESS.md` 초기화.
- 사용자 승인 게이트.

### P1.5-B — External plugin/MCP install (별도 turn, 사용자 승인 필요)
- 본 plan §3 매트릭스에 따라 **install-now 후보 0개**, install-later 후보 1개(Playwright @ P4 도달 시), audit-only 1개(superpowers).
- 즉 **P1.5-B는 사실상 비어 있다.** Playwright MCP는 P4 도달 후, Pipeline F를 한 번 더 돌려 verify 후 user-scope에서 설치.
- superpowers는 P1.5-B에서도 install하지 않는다. 그 결정은 향후 별도 audit 결과에 따라 갱신.
- token/secret은 절대 project 파일에 저장하지 않는다.

### 결론
- P1.5는 사실상 **P1.5-A 1단계만 실행** 한다. P1.5-B는 placeholder로만 존재하며 P4 도달 후 reopen.

---

## 10. Tests and Gates

### 10.1 P1.5-A 통과 기준
- 기존 pytest 53개 전부 PASS (P1 baseline 유지).
- 새 hook 7개 모두 syntax-valid PowerShell, `-NonInteractive -NoProfile` 형식.
- `.claude/settings.json`이 valid JSON.
- 새 hook이 trigger되는 다음 5개 sanity 시나리오 통과:
  1. `claude` 시작 시 → 기존 SessionStart 메시지 1회 (변화 없음).
  2. 일반 prompt 입력 → `user_prompt_phase_router.ps1` warning 0~1줄 (block 아님).
  3. `Edit src/frcgw/schemas/visibility.py` → 기존 PostToolUse + 새 `post_edit_targeted_tests.ps1` 권고만 출력.
  4. `Edit src/frcgw/evaluation/baselines.py`에 `verifier-only` 삭제 패턴을 *모의*로 시도 → `baseline_ablation_guard.ps1` WARN 출력 (BLOCK 아님).
  5. `Bash python scripts/02_train_text_smoke.py` 시도 → `phase_gate_guard.ps1`이 sentinel 부재 BLOCK.
- subagent 7개 frontmatter validate (`tools` 필드가 화이트리스트 형식).
- skill 7개 frontmatter validate.

### 10.2 P1.5-A 후 자동 추가될 gate (P2 이후 적용)
- P2 시작 → `frcgw-phase-gate` skill의 응답 형식 강제 (Read/Phase/Changed/Tests/Gate/Blockers).
- P2 데이터 생성 전 `frcgw-data-safety` + `frcgw-data-leakage-auditor` 통과.
- P2 끝 → `outputs/phase_gates/P2.passed` sentinel 생성. 그 전엔 P3 main script 실행 BLOCK.

### 10.3 새 hook이 도입할 수 있는 false positive 시나리오 및 완화
- `schema_leakage_guard.ps1`: 정의 파일 안에서 forbidden field 토큰 자체는 정상. → "AGENT_OBSERVATION 컨텍스트 / build_agent_observation 함수 / dataloader return 경로" 패턴만 BLOCK.
- `baseline_ablation_guard.ps1`: rename refactor가 일시적으로 baseline 이름을 삭제하는 것처럼 보일 수 있음. → BLOCK 아닌 WARN. 동시에 동일 diff에 새 이름이 *추가*된 경우 WARN 자체를 suppress.
- `phase_gate_guard.ps1`: 사용자가 의도적으로 우회해야 할 때 → command `/frcgw-phase-check --override <reason>`이 임시 sentinel 생성.

---

## 11. Sonnet Execution Instructions

(P1.5-A를 Opus가 직접 작성하는 turn 이후 Sonnet으로 위임할 경우 사용.)

```text
Phase: P1.5-A (local harness)
Read: CLAUDE.md, paper_context_ref/00_CONTEXT_INDEX.md,
      paper_context_ref/13_CLAUDE_CODE_EXECUTION_ROADMAP_v1.md (sections 5, 16, 20, 21),
      paper_context_ref/14_TRD_TECHNICAL_REQUIREMENTS_DOCUMENT_v1.md (sections 6.1, 6.2, 10),
      paper_context_ref/06_DATA_SCHEMA_AND_LABELING.md (sections 0.3, 0.4, 4),
      paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md (sections 5, 6, 7, 8, 11, 13, 14),
      .claude/rules/research_context_rules.md,
      plans/P1_5_PLUGIN_SKILL_AGENT_HOOK_PIPELINE_PLAN.md (this plan).

Do:
1. Create the 7 skill files under .claude/skills/<name>/SKILL.md.
2. Create the 7 subagent files under .claude/agents/<name>.md.
3. Create the 7 new hook scripts under .claude/hooks/*.ps1 (PowerShell 5.1 NonInteractive, forward-slash paths).
4. Create the 2 commands under .claude/commands/.
5. Update .claude/settings.json hooks block exactly per §6.8 of the plan (additive, do not remove existing entries).
6. Create plans/PLUGIN_AUDIT_REPORT.md with the 3 initial entries (superpowers AUDIT_ONLY, github MCP REJECT, Playwright INSTALL_LATER@P4).
7. Create plans/PHASE_PROGRESS.md with P0=PASS, P1=PASS, P1.5=IN_PROGRESS.
8. Create empty outputs/{phase_gates,test_reports,review_reports,eval_reports}/.gitkeep .
9. Run `pytest -q` — must remain 53 passed.
10. Sanity-check the 5 hook scenarios in §10.1.
11. Reply in the required Read/Phase/Changed/Tests/Gates/Blockers format.

Do not:
- Install any external plugin or MCP server.
- Modify paper_context_ref/*.
- Modify CLAUDE.md or .claude/rules/research_context_rules.md.
- Modify the existing 4 hooks.
- Edit src/frcgw/, tests/, configs/, scripts/.
- Add tokens/PATs/secrets to any file.
- Set enableAllProjectMcpServers to anything new.
- Add MCP servers beyond Context7.

Forbidden assumptions:
- That superpowers, code-review, code-simplifier, skill-creator, claude-md-management, github MCP are usable in this phase.
- That hidden labels can be used as inference inputs.
- That phase order can be skipped.
- That success rate is sufficient evidence.

Stop conditions:
- pytest red after harness changes.
- A new hook breaks routine Edit/Bash/UserPrompt flows.
- Any forbidden-field leakage pattern hits in newly created skill/agent files.
```

---

## 12. Risks and Blockers

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| 새 hook이 false positive로 일반 작업을 차단 | M | M | §6 각 hook에 명시한 패턴 정밀화 + WARN/BLOCK 분리. §10.1 sanity 시나리오로 사전 검증. |
| schema_leakage_guard 정규식이 너무 엄격 | M | L–M | "context-aware" 매칭 (build_agent_observation, AGENT_OBSERVATION bucket 안에서만). 단순 등장은 WARN. |
| baseline_ablation_guard가 rename refactor를 막음 | L–M | M | BLOCK 아닌 WARN. diff에 이름 추가 동반 시 suppress. |
| settings.json 등록 실수로 hook이 trigger 안 됨 | L | H | §6.8 JSON 그대로 복사. JSON validate 자동 실행. |
| superpowers를 사용자가 임의로 install하여 SessionStart 충돌 | L | M | `frcgw-plugin-audit` skill + Pipeline F + `PLUGIN_AUDIT_REPORT.md` 정책. |
| GitHub PAT가 우연히 project 파일에 들어감 | L | H | 기존 `pre_tool_guard`의 PAT 패턴 차단 + `frcgw-plugin-audit` 강제. |
| Playwright MCP가 P4 도달 시 영원히 미설치된 채로 남음 | L | M | P4 phase gate에 install-later 항목 자동 reopen. |
| skill/agent 명세가 너무 복잡해 실제 호출이 안 됨 | M | M | description은 `when to use` + 1줄 trigger 키워드 중심으로. |
| Claude Code 2.1.133 이후 plugin manifest 스펙 변경 | L | M | local skill/agent/hook은 manifest 무관. plugin install이 0건이라 영향 0. |
| Windows path 처리 실수 | L | M | 기존 4 hook과 동일하게 forward-slash + `-File ./.claude/...`. |

### Open blockers
- **NONE**: P1 끝, working tree clean, MCP healthy, 사용자 결정 3건 모두 권장안 채택. P1.5-A 즉시 실행 가능.

---

## 13. Final Recommendation

### Recommendation
- **Proceed with P1.5-A only.** External plugin/MCP install 0건.
- 7 skill + 7 subagent + 7 hook + 2 command + settings.json hook block 확장 + 2 plan ledger + .gitkeep 4개 = **31개 파일** 추가/수정.
- `paper_context_ref/`, `CLAUDE.md`, `.claude/rules/`, 기존 4 hook, src/tests/configs/scripts는 모두 unchanged.
- 완료 즉시 P2 (text-only data generator) 시작 가능 — Pipeline A~F가 이후 모든 phase에 적용됨.

### Output Form

```text
Read:
- CLAUDE.md
- paper_context_ref/00_CONTEXT_INDEX.md
- paper_context_ref/06_DATA_SCHEMA_AND_LABELING.md (§0.3, §0.4, §4)
- paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md (§1~§7 부분)
- paper_context_ref/13_CLAUDE_CODE_EXECUTION_ROADMAP_v1.md (§4~§7 부분)
- paper_context_ref/14_TRD_TECHNICAL_REQUIREMENTS_DOCUMENT_v1.md (§3, §5, §6.1, §6.2)
- .claude/rules/research_context_rules.md
- .claude/settings.json + settings.local.json
- .claude/hooks/{session_start_context, pre_tool_guard, post_edit_audit, stop_summary_guard}.ps1
- .claude/commands/read-paper-context.md
- .mcp.json
- plans/P0_REPO_SCAFFOLD_PLAN.md (cross-check)
- code.claude.com/docs/en/plugins (verified)
- github.com/anthropics/skills (verified)
- github.com/obra/superpowers-marketplace (verified)
- github.com/github/github-mcp-server (verified)
- github.com/microsoft/playwright-mcp (verified)

Inspected:
- claude --version = 2.1.133
- claude mcp list (context7 ✓ Connected only)
- pytest -q = 53 passed
- git status clean, branch=feat/p1-schema-visibility

Researched:
- 8 plugin/MCP candidates verified vs official sources
- Built-in available skills mapped to 5 of the 6 user wishes
- Hook event surface (PreToolUse / PostToolUse / UserPromptSubmit / SubagentStop / PreCompact / Stop) confirmed

Plan Saved:
- plans/P1_5_PLUGIN_SKILL_AGENT_HOOK_PIPELINE_PLAN.md (this file)

Recommendation:
- install now: NONE
- install later: Playwright MCP @ P4 (microsoft/playwright-mcp v0.0.75)
- audit only:  superpowers (obra/superpowers-marketplace, 940⭐) — Pipeline F only
- reject:      github MCP (PAT in env required, no gh passthrough),
               code-review/code-simplifier/skill-creator/claude-md-management
               (none verified as marketplace plugins; built-ins cover all).

Gate:
- READY_FOR_SONNET (P1.5-A)

Blockers:
- none
```
