# P2_TEXT_ONLY_DATA_PLAN.md

Status: READY_FOR_SONNET
Phase: P2 — text-only data generator
Author of plan: Opus Plan Mode (2026-05-08)
Executor: Sonnet implementation mode

---

## 0. Context

이 계획서는 FRCG-WM phase P2(text-only data generator) 구현을 위한 최종 실행
지침이다. P0(scaffold)·P1(schema/visibility)·P1.5(plugin/skill/agent/hook
harness)는 모두 완료된 상태(`pytest -q = 53 passed`, P1 commit `b5e4777`)이며,
P2의 목표는 **GUI/VLM 단계로 넘어가기 전에 falsification-guided planning의
mechanism viability를 symbolic text-only 환경에서 검증할 수 있는 dataset
generator**를 만드는 것이다.

P2는 단순 trajectory 생성기가 아니다. 다음 4개 mechanism을 수치로 측정 가능하게
만드는 trajectory를 leakage 없이 충분히 생성해야 한다.

1. wrong-control-grammar hypothesis persistence
2. action-effect evidence 기반 falsification (단순 failed-action flag와 구분)
3. alternative grammar adoption (alternative action search와 구분)
4. action-interface rewrite (policy correction과 구분)

본 계획서는 P1.5 harness(7 skill / 7 subagent / 11 hook / 3 command)가 P2 작업
폐루프에서 어떻게 사용되어야 하는지를 명시한다. Sonnet 실행 모드는 이 plan을
순서대로 따른다.

---

## 1. Read Context

### 1.1 Required source MDs (반드시 먼저 읽는다)

```
CLAUDE.md
.claude/rules/research_context_rules.md
paper_context_ref/00_CONTEXT_INDEX.md  (§5 phase router)
paper_context_ref/04_TEXT_ONLY_SMOKE_TESTBED.md  (§5–§14, §19)
paper_context_ref/03_CORE_CONCEPT_TAXONOMY.md  (§3 대헌법, §6 정의표, §11 reveal/shift)
paper_context_ref/06_DATA_SCHEMA_AND_LABELING.md  (§0.3, §0.4 MVE, §4 visibility, §7 extraction, §14 export, §15 leakage)
paper_context_ref/12_DATA_COLLECTION_METHODOLOGY_v1.md  (§7 buckets, §8 text-only, §10 failure/recovery, §13 scale, §16 coverage, §19 pseudocode)
paper_context_ref/13_CLAUDE_CODE_EXECUTION_ROADMAP_v1.md  (§8 P2 spec)
paper_context_ref/14_TRD_TECHNICAL_REQUIREMENTS_DOCUMENT_v1.md  (§6 data, §10 acceptance)
paper_context_ref/15_TDD_TECHNICAL_DESIGN_DOCUMENT_v1.md  (§5 schema, §6 validation)
```

### 1.2 P1.5 harness files (P2 작업 시작 전 동작 확인)

```
.claude/skills/frcgw-phase-gate/SKILL.md
.claude/skills/frcgw-data-safety/SKILL.md
.claude/skills/frcgw-test-quality/SKILL.md
.claude/skills/frcgw-experiment-design/SKILL.md
.claude/agents/frcgw-data-leakage-auditor.md
.claude/agents/frcgw-test-runner.md
.claude/agents/frcgw-code-reviewer.md
.claude/hooks/schema_leakage_guard.ps1
.claude/hooks/post_edit_targeted_tests.ps1
.claude/hooks/phase_gate_guard.ps1
.claude/hooks/user_prompt_phase_router.ps1
.claude/commands/frcgw-phase-check.md
plans/PHASE_PROGRESS.md
plans/PLUGIN_AUDIT_REPORT.md
plans/P1_5_PLUGIN_SKILL_AGENT_HOOK_PIPELINE_PLAN.md
```

---

## 2. Current Repository Inspection

### 2.1 Inspection commands (Sonnet은 P2 시작 시 모두 실행)

```powershell
git status --short
git log --oneline -8
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -c "import frcgw, frcgw.schemas, frcgw.text_env"
Test-Path outputs\phase_gates\P1.passed
Test-Path outputs\phase_gates\P1.5.passed
Get-ChildItem -Path src\frcgw\text_env
```

### 2.2 Verified state at plan time (2026-05-08)

| Check | Result |
|---|---|
| git working tree | clean for tracked files; P1.5 untracked artifacts present (skills/agents/hooks/commands/plans) |
| recent commit | `b5e4777 chore(p1): finalize schema and visibility guards` |
| pytest | 53 passed |
| paper_context_ref/ | unchanged — must remain so |
| `.claude/settings.json` | JSON valid |
| `.claude/skills/` | 7 skills present |
| `.claude/agents/` | 7 subagents present |
| `.claude/hooks/` | 11 hooks present (P1 baseline + P1.5 added) |
| `.claude/commands/` | 3 commands present |
| `src/frcgw/schemas/visibility.py` | present, `FORBIDDEN_AGENT_FIELDS` = 15 items, `assert_agent_observation_safe()` present |
| `src/frcgw/schemas/episode_schema.py` | present, `EpisodeRecord` + `AuditMetadata` |
| `src/frcgw/schemas/step_schema.py` | present (PublicObservation/PublicHistoryItem/CandidateAction/ActionRecord/PublicEffect/TrainingLabels/EvaluationLabels/CounterfactualRecord/StepAuditMetadata/StepRecord) |
| `src/frcgw/schemas/validation.py` | present (validate_step_schema, validate_episode_schema, validate_visibility_contract, validate_counterfactual_exclusion + 4 error types) |
| `src/frcgw/data/leakage_auditor.py` | present (`LeakageAuditor.audit_agent_input/audit_batch/assert_clean`) |
| `src/frcgw/text_env/` | exists with `__init__.py` only — empty for P2 |
| `tests/` | 8 test files (P0+P1 baseline, P2 placeholders absent) |
| outputs/phase_gates/P1.passed | **ABSENT** — must be created during P1.5→P2 handoff |
| outputs/phase_gates/P1.5.passed | **ABSENT** — must be created during P1.5→P2 handoff |
| `plans/PHASE_PROGRESS.md` | shows P1.5 IN_PROGRESS, P2 PENDING |

### 2.3 Pre-P2 blockers to clear (Sonnet 1단계)

P2 main script (`scripts/01_generate_text_data.py`) 실행은 hook
`phase_gate_guard.ps1` 규칙상 `outputs/phase_gates/P1.passed` sentinel을 요구한다.
또한 P1.5 가 PHASE_PROGRESS.md 에 IN_PROGRESS로 남아 있으므로 status flip
이 필요하다.

순서:

1. `/frcgw-phase-check` 실행하여 P1.5 gate 검토.
2. P1.5 PASS 확인 후 `outputs/phase_gates/P1.passed`, `outputs/phase_gates/P1.5.passed`
   sentinel 생성. (frcgw-phase-check command 또는 명시적 main agent `New-Item -Path
   outputs/phase_gates/P1.passed -ItemType File`).
3. `plans/PHASE_PROGRESS.md` P1.5 → PASS, P2 → IN_PROGRESS 업데이트.
4. 그 후에만 `scripts/01_generate_text_data.py` 실행 시도.

`outputs/phase_gates/`, `outputs/test_reports/`, `outputs/review_reports/`,
`outputs/eval_reports/` 디렉터리 부재 시 사전 생성.

---

## 3. P2 Scope

### 3.1 In-scope (P2가 반드시 만든다)

- text-only symbolic environment (no DOM, no screenshot, no browser).
- hidden control grammar engine (intent→action mapping + precondition + expected effect).
- public text observation with hidden grammar/regime separated.
- 8 task family minimum (search form, modal blocker, required dropdown, pagination
  vs infinite scroll, nested scroll, loading/delayed enable, permission gate,
  filter accordion).
- policy mixture (Oracle, WrongGrammar, Retry, Recovery, RandomConstrained).
- trajectory collector reusing P1 schema (`StepRecord`, `EpisodeRecord`,
  `PublicObservation`, `TrainingLabels`, `EvaluationLabels`, `StepAuditMetadata`,
  `AuditMetadata`).
- JSONL shard exporter and manifest writer (`data/frcgw_text/v0_1/`).
- coverage auditor (CA-001~CA-006 of `12.md §16`).
- leakage auditor reuse (`LeakageAuditor.assert_clean` + lexical scan over
  `public_state_text`).
- deterministic replay validator.
- 5 new test files (see §11).
- one driver script (`scripts/01_generate_text_data.py`) and one config
  (`configs/data_collection_text.yaml`).
- small dry-run dataset (100~500 episodes / 1k~5k transitions) only — no
  20k–100k full collection until P2 gate passes review.

### 3.2 Out-of-scope (P2가 절대 만들지 않는다)

- VLM model code, frozen-VLM adapter.
- synthetic GUI environment, browser executor, DOM/screenshot/a11y artifacts.
- model architecture, latent heads, world model heads.
- losses, rewards (beyond label fields), training loop.
- planner, falsification scorer, alternative proposer, decision gate, rewrite head.
- evaluation runner, metrics module beyond coverage audit.
- counterfactual_action_effects generation (deferred to P3/P4 — P2 leaves
  `StepRecord.counterfactuals` empty list).
- paper-main 7B/QLoRA training.
- modifications to `paper_context_ref/*.md`.
- modifications to P1 schema files (`src/frcgw/schemas/*`,
  `src/frcgw/data/leakage_auditor.py`) unless audited as backwards-compatible
  additions.
- deletion or rename of must-not-disappear baseline/ablation hooks (none touched).
- pushing to remote branches.
- deleting any P1.5 hook, skill, agent, or command.
- producing fake metric values or success-rate claims.

### 3.3 Files to create / modify

Create:

```
src/frcgw/text_env/__init__.py          (extend existing)
src/frcgw/text_env/state.py
src/frcgw/text_env/grammar.py
src/frcgw/text_env/generator.py
src/frcgw/text_env/policies.py
src/frcgw/text_env/collector.py
src/frcgw/text_env/replay.py
src/frcgw/data/coverage_auditor.py
src/frcgw/data/shard_exporter.py
scripts/01_generate_text_data.py
configs/data_collection_text.yaml
tests/test_text_env.py
tests/test_text_data_collection.py
tests/test_text_policy_mixture.py
tests/test_text_public_leakage.py
tests/test_text_replay.py
plans/P2_GATE_REPORT.md                  (final phase gate report)
outputs/phase_gates/P1.passed             (pre-P2 sentinel)
outputs/phase_gates/P1.5.passed           (pre-P2 sentinel)
outputs/phase_gates/P2.passed             (post-P2 sentinel after gate PASS)
data/frcgw_text/v0_1/manifest.json        (only after dry-run)
data/frcgw_text/v0_1/train.jsonl
data/frcgw_text/v0_1/valid.jsonl
data/frcgw_text/v0_1/test_id.jsonl
data/frcgw_text/v0_1/audits/coverage_report.json
data/frcgw_text/v0_1/audits/leakage_report.json
```

Modify:

```
plans/PHASE_PROGRESS.md   (P1.5 → PASS, P2 progression)
src/frcgw/text_env/__init__.py  (re-export public API only — never hidden labels)
src/frcgw/data/__init__.py  (export coverage_auditor / shard_exporter symbols if missing)
```

Do NOT modify (audited):

```
paper_context_ref/**
src/frcgw/schemas/visibility.py
src/frcgw/schemas/episode_schema.py
src/frcgw/schemas/step_schema.py
src/frcgw/schemas/validation.py
src/frcgw/data/leakage_auditor.py
.claude/{skills,agents,hooks,commands}/**  (unless bug fix needed; flagged separately)
tests/test_visibility_contract.py
tests/test_episode_schema.py
tests/test_counterfactual_exclusion.py
tests/test_leakage_auditor.py
tests/test_p0_*.py
```

---

## 4. Skill / Subagent / Hook Usage Plan

P2의 핵심은 **P1.5 harness를 실제로 사용해서 폐루프(implement → audit →
test → review → gate)를 돌리는 것**이다. 모든 skill/subagent/hook 호출은
응답에 명시한다.

### 4.1 Skills

| Skill | When | Why | Pass condition |
|---|---|---|---|
| `frcgw-phase-gate` | (a) P2 시작 응답, (b) Step 4·6·8·10 완료 시점, (c) P2 종료 응답 | Read/Phase/Changed/Tests/Gates/Blockers 형식을 강제하고 sentinel 정책 적용 | 모든 응답이 6-section 형식을 갖고 sentinel이 sentinel 정책을 따른다 |
| `frcgw-data-safety` | text_env/state.py · grammar.py · generator.py · collector.py · shard_exporter.py 작성/수정 직후 | hidden grammar / regime / counterfactual / audit metadata 가 PublicObservation에 들어가지 않는지 확인 | forbidden fields가 어떤 식으로도 obs path에 들어가지 않음, counterfactual list 비어 있거나 별도 격리, public 텍스트에 hidden grammar token 없음 |
| `frcgw-test-quality` | 매 모듈 추가 후, 그리고 P2 final gate 직전 | targeted pytest 권고 후 필요시 full suite 실행, 결과를 `outputs/test_reports/<UTC>.txt`에 저장 | targeted tests pass, 종료 직전 `pytest -q` 전체 PASS |
| `frcgw-experiment-design` | task family / policy mixture / coverage threshold 결정 시점 (Step 8·9) | P3 mechanism test에 필요한 trajectory 분포(failed/recovery/repeated wrong mapping/shift/delayed/no-op valid)가 충족되는지 점검, must-not-disappear baseline 호출 흐름이 깨지지 않았는지 검증 | claim-to-evidence 표가 P2 기준으로 작성되고 must-not-disappear 항목 어떤 것도 P2 변경에서 제거되지 않음 |

명시적으로 사용하지 않는 skill: `frcgw-paper-framing` (P7/P8용), `frcgw-code-review`
(commit 직전 활용 — §4.4 참조), `frcgw-plugin-audit` (P2는 외부 plugin 설치
없음).

### 4.2 Subagents

| Subagent | Trigger | Tools | Expected output | Fail action |
|---|---|---|---|---|
| `frcgw-data-leakage-auditor` | (a) PublicObservation 설계 후, (b) collector 작성 후, (c) shard_exporter 작성 후, (d) P2 구현 완료 시점 | Read, Glob, Grep | `Audit target / Forbidden field hits / Counterfactual isolation / Verdict (PASS/BLOCK) / Reason` | BLOCK 시 main agent가 leaked field가 들어간 path를 즉시 수정 → 재호출 |
| `frcgw-test-runner` | (a) 각 module group 추가 후, (b) P2 final gate 직전 | Bash (pytest only), Read, Glob, Grep | `Changed files / Target tests / Command run / Result / Failed (테스트명+원인 1줄) / Fix plan / Gate ready (YES/NO)` | 같은 testcase 2회 fail 시 main agent가 root cause 명시 후 fix |
| `frcgw-code-reviewer` | P2 구현 완료 후, commit 직전 | Read, Glob, Grep | `Term drift / Baseline drift / Ablation drift / Visibility change / Docstring / Verdict (ACCEPT/REJECT/WARN) / Reason` | REJECT 시 commit 금지, WARN은 main agent 판단 |
| `frcgw-context-router` | task fit 불확실 시 (예: P2 후반에 P3 reference가 필요할지 판단) | Read, Glob, Grep | required MD bundle list | 응답을 받아 필요한 MD만 읽음 |
| `frcgw-experiment-evaluator` | P2 dry-run coverage report 해석 시점 | Read, Glob, Grep, Bash (read-only) | gate PASS/FAIL 판단 + 부족 분포 지적 | FAIL 시 policy mixture 비율 조정 후 재생성 |

명시적으로 사용하지 않는 subagent: `frcgw-related-work-scout` (P7/P8용),
`frcgw-plugin-security-auditor` (P2 plugin 설치 없음).

### 4.3 Hooks (자동 동작 — 비활성화 금지)

| Hook | Event | P2 effect | 의도된 결과 |
|---|---|---|---|
| `schema_leakage_guard.ps1` | PreToolUse Edit/Write | text_env/collector·generator·state, schemas/, data/, logging/ 영역에서 forbidden field token이 위험 컨텍스트(`build_agent_observation`, `__getitem__`, `collate_fn`, `forward(`)에 들어가면 BLOCK; 정의/주석 컨텍스트면 WARN | hidden label leakage를 조기에 차단 |
| `post_edit_targeted_tests.ps1` | PostToolUse Edit/Write | text_env/* 수정 후 `tests/test_text_env*.py` 실행을 권고; schemas/* 수정 후 P1 tests 권고 | 매 edit마다 full suite 자동실행 금지, targeted 권고 |
| `phase_gate_guard.ps1` | PreToolUse Bash | `scripts/01_generate_text_data.py` 호출 시 `outputs/phase_gates/P1.passed` 부재면 BLOCK | sentinel 부재 상태로 main script 실행 금지 |
| `user_prompt_phase_router.ps1` | UserPromptSubmit | "P3", "다음 phase", "model" 등 phase-jump 발화 시 P2 gate 확인 reminder | P2 미완 상태에서 P3 점프 차단 |
| `subagent_stop_audit.ps1` | SubagentStop | subagent 종료 시 결과 요약/audit | subagent 결과를 main agent context에 포함 |
| `pre_compact_phase_handoff.ps1` | PreCompact | compact 직전 phase status를 PHASE_PROGRESS.md에 append | context 압축 후 phase 진행 상황 보존 |
| `baseline_ablation_guard.ps1` | PreToolUse Edit/Write | must-not-disappear baseline/ablation 이름이 삭제되면 BLOCK | P2가 baseline list를 건드리지 않으므로 정상 silent |

P2 hook 운영 원칙:

- 매 edit마다 full pytest 자동 실행 금지 (post_edit_targeted_tests 권고만).
- final gate에서만 `pytest -q` 실행.
- false positive는 WARN 우선, hidden leakage 명백 패턴은 BLOCK.
- Windows path는 forward slash 또는 PowerShell 친화 escape.

### 4.4 Closed-loop sequence per module

각 P2 모듈(state/grammar/generator/policies/collector/exporter)에 대해 다음
6단계를 반복한다.

```
1. Edit/Write module file
   └─ schema_leakage_guard hook auto-runs (BLOCK/WARN/silent)
   └─ post_edit_targeted_tests hook auto-runs (recommendation)
2. Invoke frcgw-data-safety skill manually (if collector/exporter/state)
3. Invoke frcgw-data-leakage-auditor subagent
   └─ Verdict PASS or BLOCK
4. Invoke frcgw-test-runner subagent (targeted tests)
   └─ Result PASS or fix loop
5. Continue to next module
6. After all modules done:
   - frcgw-experiment-design skill (coverage adequacy)
   - frcgw-code-reviewer subagent (drift check)
   - frcgw-test-runner subagent (full pytest -q)
   - frcgw-phase-gate skill (final gate report)
```

---

## 5. Text-Only Environment Design

### 5.1 Module map

```
src/frcgw/text_env/
  __init__.py         (re-export public API only)
  state.py            TextState, TextEpisodeSpec, TextStepResult
  grammar.py          ControlGrammar enum, GrammarRule, GrammarEngine
  generator.py        TaskFamily enum, TaskFamilyTemplate, EpisodeSpecGenerator
  policies.py         Policy ABC + 5 concrete policies + PolicyMixtureRunner
  collector.py        TextCollector (orchestrates step loop)
  replay.py           ReplayValidator
```

`src/frcgw/data/` extensions:

```
src/frcgw/data/
  coverage_auditor.py CoverageAuditor, CoverageReport, CoverageThresholds
  shard_exporter.py   ShardExporter (JSONL serializer + manifest writer)
```

### 5.2 Source MD docstring rule

각 신규 module 첫 줄 docstring에 source MD를 적는다. `frcgw-code-reviewer`가
검사한다.

```python
"""frcgw.text_env.state — Text-only symbolic state and episode/step records.

Source docs:
- paper_context_ref/04_TEXT_ONLY_SMOKE_TESTBED.md §6, §7, §8, §19
- paper_context_ref/06_DATA_SCHEMA_AND_LABELING.md §0.4 MVE, §4 visibility
- paper_context_ref/12_DATA_COLLECTION_METHODOLOGY_v1.md §8 text-only
"""
```

### 5.3 TextState (state.py)

```python
@dataclass(frozen=False)
class TextState:
    # public — exposed via build_public_observation()
    visible_text: str                       # the only natural-language obs
    public_actions: list[CandidateAction]   # public candidate actions
    progress_public: float                  # 0.0~1.0 monotonic public hint
    blocker_state_public: str | None        # coarse public, never grammar token
    step_index: int

    # hidden — internal only; NEVER serialized to public_observation
    _hidden_regime: str                     # field name underscore-prefixed
    _hidden_control_grammar: str
    _hidden_preconditions: dict             # action_id -> bool
    _hidden_progress_score: float
    _hidden_blocker_id: str | None
    _hidden_event_type: str                 # one of: none/reveal/shift/failed/noisy/delayed/blocker_removed
```

규칙:

- `_hidden_*` prefix 필드는 dataclass 안에 두되, `build_public_observation()`은
  `_`로 시작하는 필드를 절대 노출하지 않는다.
- `visible_text`는 hidden grammar/regime token이 절대 들어가지 않는다.
  (lexical scan: `tests/test_text_public_leakage.py`에서 검증)
- public action label도 grammar 이름을 노출하지 않는다 (`click_filter_button` OK,
  `remove_blocker_before_target_action` 금지).

### 5.4 TextEpisodeSpec (state.py)

```python
@dataclass
class TextEpisodeSpec:
    episode_id: str
    task_family: str
    public_instruction: str
    initial_state_template: str
    hidden_regime: str
    hidden_control_grammar: str
    event_schedule: list[dict]   # [{step:int, type:reveal|shift|delay|noise, ...}]
    max_steps: int               # default 12 for text-only (much shorter than GUI)
    seed: int
```

### 5.5 TextStepResult (state.py)

```python
@dataclass
class TextStepResult:
    action: ActionRecord
    pre_state: TextState
    post_state: TextState
    public_effect: PublicEffect
    training_labels: TrainingLabels
    evaluation_labels: EvaluationLabels
    audit_metadata: StepAuditMetadata
    done: bool
```

`TrainingLabels`, `EvaluationLabels`, `StepAuditMetadata`는 P1 schema를 그대로
사용. `counterfactuals=[]` 빈 리스트로 둠 (P2는 counterfactual_action_effects를
생성하지 않음).

### 5.6 build_public_observation contract

`collector.py`의 helper:

```python
def build_public_observation(state: TextState, instruction: str,
                             history: list[PublicHistoryItem]) -> PublicObservation:
    obs = PublicObservation(
        instruction=instruction,
        dom_snapshot_public=None,
        accessibility_tree_public=None,
        screenshot_ref=None,
        history_public=history,
        candidate_actions_public=list(state.public_actions),
    )
    # mandatory leakage assert — uses P1 helper
    assert_agent_observation_safe(obs)
    return obs
```

`visible_text`는 PublicObservation 자체에 새 필드를 추가하지 않고
`history_public`의 이전 effect summary 또는 instruction prefix로 전달한다.

대안: PublicObservation은 P1에서 확정되었으므로 변경하지 않는다. 대신
text-only는 `instruction` 필드 안에 `[STATE] ...`을 prepend하는 단순 직렬화
를 사용한다 (TDD §5.4 호환).

```text
instruction = (
    f"[INSTRUCTION] {episode_spec.public_instruction}\n"
    f"[STATE] {state.visible_text}"
)
```

이렇게 하면 P1 schema를 건드리지 않고 text-only 정보를 전달할 수 있다.

---

## 6. Control Grammar Engine Plan

### 6.1 ControlGrammar enum (grammar.py)

P2에서는 8개 task family에 대응하는 8개 control grammar를 1차 구현한다.
필요시 STRESS-04-* 시나리오 확장은 P3에서 한다.

```python
class ControlGrammar(str, Enum):
    DIRECT_SEARCH                     = "direct_search"
    REQUIRED_DROPDOWN_THEN_SEARCH     = "required_dropdown_then_search"
    MODAL_CONFIRM_THEN_ACTION         = "modal_confirm_then_action"
    CONTAINER_SCROLL_THEN_SELECT      = "container_scroll_then_select"
    WAIT_UNTIL_ENABLED_THEN_CLICK     = "wait_until_enabled_then_click"
    PERMISSION_ACCEPT_THEN_ACTION     = "permission_accept_then_action"
    FILTER_OPEN_THEN_SELECT           = "filter_open_then_select"
    PAGINATION_OR_INFINITE_SCROLL     = "pagination_or_infinite_scroll"
```

### 6.2 GrammarEngine API (grammar.py)

```python
class GrammarEngine:
    def precondition_satisfied(self, state: TextState, action_id: str) -> bool: ...
    def expected_effect(self, state: TextState, action_id: str) -> str: ...
    def apply(self, state: TextState, action_id: str) -> TextState: ...
    def label_failure_reason(self, state: TextState, action_id: str) -> str | None: ...
    def label_recovery_action(self, state: TextState) -> str | None: ...
    def is_wrong_grammar_failure(self, state: TextState, action_id: str) -> bool: ...
    def label_event_type(self, prev: TextState, post: TextState,
                         scheduled: dict | None) -> str: ...
```

### 6.3 wrong-grammar failure 정의 (CONST-04-001~04-006 준수)

`is_wrong_grammar_failure(s, a)` 는 다음 모두 만족해야 True:

- `intent`는 맞다 (action_id가 instruction의 subgoal로 정렬됨).
- `precondition_satisfied(s, a) == False`.
- `expected_effect(s, a)` 와 `apply()` 후 observed effect mismatch.
- `event_type != delayed` and `event_type != noisy` (delay/noise는 wrong grammar로
  분류하지 않는다 — REVISION-03-011, BOUNDARY-03-017).

이 4-조건 규칙은 `tests/test_text_env.py`에서 단위 테스트로 고정한다.

### 6.4 reveal vs shift 정의

- `reveal`: `_hidden_state`의 일부가 `visible_text`로 노출되지만 grammar/regime
  은 그대로. (hidden_filter accordion expand 등)
- `shift`: regime/grammar가 바뀜. (pagination → infinite_scroll 등)

`event_schedule`에 `{step:k, type:"reveal"|"shift", ...}` 형태로 미리 결정하고,
collector가 step k 도달 시 trigger한다.

### 6.5 delayed/no-op valid 정의

- `delayed`: action이 effect를 t+Δ에 만든다 (Δ ∈ {1,2}). delay window 내에서는
  `failed_action=False`, `delayed_effect_flag=True`.
- `no_op_valid`: `wait` action이 valid한 step (loading 중). `failed_action=False`,
  `progress_delta=0`이지만 wrong grammar로 분류 금지.

`tests/test_text_env.py`에 별도 case로 검증한다.

---

## 7. Task Family Plan

P2는 다음 8개 task family를 구현한다 (`generator.py`의 `TaskFamilyTemplate`).

| Family | Public instruction | Public visible state | Hidden grammar | Common wrong action | Correct recovery | Expected failure pattern | Reveal/Shift/Delay 가능 | Leakage risk | Test case |
|---|---|---|---|---|---|---|---|---|---|
| `search_form` | "Find a wireless mouse." | "Search bar visible. Submit button greyed." | DIRECT_SEARCH or REQUIRED_DROPDOWN_THEN_SEARCH | submit immediately | type query → submit | submit no_state_change while disabled | reveal: dropdown appears | "category" word can leak grammar — paraphrase | TEST-04-003 |
| `required_dropdown` | "Search by category." | "Search bar + Category dropdown collapsed." | REQUIRED_DROPDOWN_THEN_SEARCH | type and submit | open_dropdown → select → submit | submit fails, dropdown still closed | shift to DIRECT_SEARCH after reveal | dropdown name might leak | TEST-04-006 |
| `modal_blocker` | "Open the filter panel." | "Filter button visible. Cookie modal active." | MODAL_CONFIRM_THEN_ACTION | click filter directly | close_modal → click_filter | click_filter no_state_change while modal_active | reveal: modal text | "modal" token must not appear in visible_text | TEST-04-002 |
| `pagination_vs_infinite` | "Show me more results." | "Result list. Footer text 'scroll for more' OR 'Next page'." | PAGINATION_OR_INFINITE_SCROLL | wrong of two | other of two | no new items appear | shift: switches between two between episodes | footer text could give grammar — randomize phrasing | TEST-04-001 |
| `nested_scroll` | "View more comments." | "Comments panel inside container." | CONTAINER_SCROLL_THEN_SELECT | scroll page | scroll container | page no_state_change | none | "container" token | TEST-04-009 |
| `loading_delayed` | "Open first result." | "Search results loading." | WAIT_UNTIL_ENABLED_THEN_CLICK | click immediately | wait → click | stale or delayed effect | delay event scheduled | "loading" label | TEST-04-004 |
| `permission_gate` | "Share this document." | "Share button visible. Permission prompt active." | PERMISSION_ACCEPT_THEN_ACTION | click share | accept → click share | share no_state_change | reveal: permission text | "permission" word | TEST-04-007 |
| `filter_accordion` | "Set price filter." | "Filter section header collapsed." | FILTER_OPEN_THEN_SELECT | click price filter directly | expand_section → click_price | price filter not visible | reveal | "accordion"/"expand" | TEST-04-013 |

각 family는 최소 3개 surface 변형(instruction paraphrase + visible_text
paraphrase)을 가져야 keyword shortcut을 줄일 수 있다. paraphrase
template은 generator config에서 관리.

---

## 8. Policy Mixture Plan

### 8.1 Policy classes (policies.py)

```python
class Policy(ABC):
    @abstractmethod
    def select(self, obs: PublicObservation, history: list[PublicHistoryItem]) -> str: ...

class OraclePolicy(Policy): ...
class WrongGrammarPolicy(Policy): ...
class RetryPolicy(Policy): ...
class RecoveryPolicy(Policy): ...
class RandomConstrainedPolicy(Policy): ...

class PolicyMixtureRunner:
    def __init__(self, mixture: dict[str, float], rng: random.Random): ...
    def sample_policy(self, episode_spec: TextEpisodeSpec) -> Policy: ...
    def coverage_oversample(self, current_coverage: dict, targets: dict) -> Policy | None: ...
```

### 8.2 Policy ratio table

| Policy | Initial ratio | Trajectory type produced | Expected labels | Leakage risk | Test |
|---|---:|---|---|---|---|
| `OraclePolicy` | 20% | success path; uses hidden grammar (allowed for collector behavior, not agent input) | normal progress | oracle behavior never written into PublicObservation | test_text_policy_mixture |
| `WrongGrammarPolicy` | 25% | scripted wrong-mapping repetition | failed_action=True, true_wrong_hypothesis=True, repeated_invalid_mapping_flag=True | none if scripts only consume hidden grammar internally | test_text_policy_mixture |
| `RetryPolicy` | 25% | base agent-like — retries previous action up to N | failed_action=True with low recovery | none | test_text_policy_mixture |
| `RecoveryPolicy` | 20% | first wrong then switch to correct grammar after evidence | true_valid_hypothesis_switch=True | none | test_text_policy_mixture |
| `RandomConstrainedPolicy` | 10% | random over public_actions | mixed | none | test_text_policy_mixture |

### 8.3 Coverage-driven oversampling

`PolicyMixtureRunner.coverage_oversample()`는 current_coverage가 targets의
80% 이하인 카테고리에 대해 해당 카테고리를 채우는 policy를 우선 선택한다.
oversampling 결정은 `audit_metadata.policy_id`와 `policy_mixture` log에 기록.

### 8.4 Policy implementation 규칙

- Oracle/WrongGrammar/Recovery policy는 `_hidden_*` 필드를 읽을 수 있지만
  생성된 trace의 `PublicObservation`/`history_public`에 hidden token을 절대
  쓰지 않는다.
- `policy_id`는 `StepAuditMetadata.policy_id`에만 기록되고 PublicObservation
  안에 들어가서는 안 된다 (`FORBIDDEN_AGENT_FIELDS`에 이미 포함).

---

## 9. Collector and Export Plan

### 9.1 Collector flow (collector.py)

```python
def collect_episode(spec: TextEpisodeSpec, runner: PolicyMixtureRunner,
                    rng: random.Random, config: CollectorConfig) -> EpisodeRecord:
    state = init_state_from_spec(spec)
    history: list[PublicHistoryItem] = []
    steps: list[StepRecord] = []

    for step_index in range(spec.max_steps):
        # 1. Build sanitized public observation
        instruction = format_instruction_with_state(spec, state)
        obs = build_public_observation(state, instruction, history)
        # P1 helper: raises HiddenLabelLeakageError if forbidden field present
        assert_agent_observation_safe(obs)

        # 2. Pick policy and select action
        policy = runner.sample_policy(spec)
        action_id = policy.select(obs, history)
        action_record = ActionRecord(
            action_id=f"act_{spec.episode_id}_{step_index:03d}",
            action_type=action_id,  # symbolic primitive
            action_params={},
            rewritten=False,
        )

        # 3. Apply grammar engine
        engine = GrammarEngine(state._hidden_control_grammar)
        scheduled_event = pick_scheduled_event(spec.event_schedule, step_index)
        post_state = engine.apply(state, action_id)
        if scheduled_event is not None:
            post_state = apply_scheduled_event(post_state, scheduled_event)

        # 4. Compute public effect (no hidden grammar tokens)
        public_effect = compute_public_effect(state, post_state, action_id)

        # 5. Build training/eval labels (post-step)
        training_labels = build_training_labels(state, post_state, action_id, engine,
                                                scheduled_event)
        evaluation_labels = build_evaluation_labels(state, post_state, action_id,
                                                    policy)

        # 6. Build audit metadata (never agent input)
        audit = StepAuditMetadata(
            generator_version=config.generator_version,
            collection_timestamp=now_iso(),
            policy_id=policy.policy_id,
            split_id=config.split_id,
            template_id=spec.task_family,
            seed=spec.seed,
        )

        step = StepRecord(
            step_id=f"{spec.episode_id}_step_{step_index:03d}",
            episode_id=spec.episode_id,
            step_index=step_index,
            public_observation=obs,
            action=action_record,
            observed_effect_public=public_effect,
            training_labels=training_labels,
            evaluation_labels=evaluation_labels,
            counterfactuals=[],     # P2 leaves empty
            audit_metadata=audit,
        )

        # 7. Validate per-step
        step_result = validate_step_schema(step)
        if not step_result.passed:
            raise SchemaValidationError(step_result.errors)

        steps.append(step)
        history.append(PublicHistoryItem(
            step_index=step_index,
            action_summary=action_id,
            effect_summary=public_effect.effect_type,
        ))

        state = post_state
        if engine.is_terminal(state):
            break

    episode = EpisodeRecord(
        episode_id=spec.episode_id,
        dataset_version=config.dataset_version,
        schema_version=config.schema_version,
        generator_version=config.generator_version,
        split_id=config.split_id,
        task_family=spec.task_family,
        public_instruction=spec.public_instruction,
        steps=steps,
        final_success=engine.is_success(state),
        total_progress=state.progress_public,
        audit_metadata=AuditMetadata(
            generator_version=config.generator_version,
            collection_timestamp=now_iso(),
            schema_version=config.schema_version,
            split_id=config.split_id,
            template_id=spec.task_family,
            seed=spec.seed,
            policy_mixture=runner.policy_mixture_snapshot(),
        ),
    )

    ep_result = validate_episode_schema(episode)
    if not ep_result.passed:
        raise SchemaValidationError(ep_result.errors)
    visibility_result = validate_visibility_contract(episode)
    if not visibility_result.passed:
        raise HiddenLabelLeakageError(visibility_result.errors)

    return episode
```

### 9.2 ShardExporter (data/shard_exporter.py)

```python
class ShardExporter:
    def __init__(self, output_dir: Path, dataset_version: str, schema_version: str): ...
    def write_episode(self, split_id: str, episode: EpisodeRecord) -> None:
        # serialize to JSONL line per episode (or per step — pick episode line)
        # apply LeakageAuditor.audit_agent_input on PublicObservation only
        # before writing
        ...
    def write_manifest(self, coverage_report: CoverageReport,
                       leakage_report: AuditReport) -> None: ...
```

### 9.3 CoverageAuditor (data/coverage_auditor.py)

`12.md §16` 의 CA-001~CA-006 중 P2-relevant를 구현:

| Threshold | Target | Source |
|---|---:|---|
| failed_action_ratio | ≥ 20% | user spec STEP 11; `12.md §16` CA-001 (≥25%) — relax to ≥20% per `13.md §8.7` |
| recovery_ratio | ≥ 8% | user spec STEP 11; CA-002 (≥10–20%) |
| repeated_wrong_mapping_ratio | ≥ 8% | user spec STEP 11; CA-006 (≥10–20%) |
| shift_ratio | ≥ 8% | user spec STEP 11; CA-003 (≥10–20%) |
| reveal_ratio | ≥ 5% | CA-004 |
| delayed_or_noisy_or_no_op_valid_ratio | ≥ 3% | user spec; CA-005 (≥5–10%) |

Pass condition은 user spec STEP 11 thresholds를 1차 기준으로 사용. Sonnet은 user
spec과 12.md §16의 차이를 `data/frcgw_text/v0_1/audits/coverage_report.json`에
명시한다.

### 9.4 Output layout

```text
data/
  frcgw_text/
    v0_1/
      manifest.json
      schema.json                  (optional: dump dataclass JSON schema)
      train.jsonl
      valid.jsonl
      test_id.jsonl
      audits/
        coverage_report.json
        leakage_report.json
        replay_report.json
      metadata/
        generator_config.yaml      (copy of configs/data_collection_text.yaml)
        version_hash.txt
```

train/valid/test_id 분할은 `SplitManager`(또는 collector inline)에서 episode_id
hash 기반으로 결정. P2는 OOD split을 만들지 않는다 (그것은 P3/P4).

### 9.5 Dry-run scale

P2 dry-run 만 실행:

| Metric | Target |
|---|---:|
| episodes | 100 ~ 500 |
| transitions (steps) | 1k ~ 5k |
| splits | train / valid / test_id |
| coverage thresholds | §9.3 |

20k–100k 대형 dataset은 P2 gate PASS 후 별도 승인 단계에서 결정 (P3 시작 시
별도 prompt로 사용자가 스케일업 승인).

---

## 10. Tests and Gates

### 10.1 New test files

| File | Tests inside |
|---|---|
| `tests/test_text_env.py` | state transition determinism, hidden field absence in PublicObservation, wrong_grammar_failure 4-condition rule, delayed effect not classified as wrong grammar, no_op_valid not classified as wrong grammar |
| `tests/test_text_data_collection.py` | EpisodeRecord/StepRecord pass `validate_episode_schema`, `validate_visibility_contract`, JSONL roundtrip preserves fields, manifest file written correctly, audit reports written |
| `tests/test_text_policy_mixture.py` | each policy produces expected label distribution on a fixed-seed mini-run, oversampling triggers when ratio < target |
| `tests/test_text_public_leakage.py` | (a) lexical scan of `visible_text` and `instruction` over hidden grammar tokens / regime tokens / counterfactual tokens — must be 0 hits; (b) `LeakageAuditor.assert_clean(obs)` passes; (c) `policy_id`/`split_id`/`template_id`/`seed` never in PublicObservation; (d) hidden grammar token never in any history_public.action_summary or effect_summary |
| `tests/test_text_replay.py` | same seed → byte-identical EpisodeRecord (after stable JSON dump), different seed → different episode_id sequence, replay validator detects deterministic mismatch when injected |

### 10.2 P2 Gate PASS conditions

모두 충족해야 P2 gate PASS sentinel `outputs/phase_gates/P2.passed` 생성 가능.

| ID | Condition |
|---|---|
| P2-G-01 | `pytest -q` ALL pass (P0+P1 baseline 53 + P2 신규 = ≥ 70 expected) |
| P2-G-02 | P1 tests still pass (no regression) |
| P2-G-03 | P2 신규 test 5종 모두 pass |
| P2-G-04 | dry-run dataset 100~500 episodes 생성 가능 |
| P2-G-05 | hidden grammar/regime token PublicObservation·history·effect_summary 누수 0건 (lexical scan) |
| P2-G-06 | `LeakageAuditor.audit_batch` PASS on each shard line |
| P2-G-07 | failed_action_ratio ≥ 20% |
| P2-G-08 | recovery_ratio ≥ 8% |
| P2-G-09 | repeated_wrong_mapping_ratio ≥ 8% |
| P2-G-10 | shift_ratio ≥ 8% |
| P2-G-11 | delayed/no_op_valid case 포함됨 (count ≥ 1 per family that supports it) |
| P2-G-12 | `paper_context_ref/` 수정 없음 |
| P2-G-13 | P2 범위 밖 파일(P1 schema, P1.5 harness) 수정 없음 (코드 리뷰가 확인) |
| P2-G-14 | `frcgw-data-leakage-auditor` subagent → Verdict PASS |
| P2-G-15 | `frcgw-test-runner` subagent → Result PASS, Gate ready YES |
| P2-G-16 | `frcgw-code-reviewer` subagent → Verdict ACCEPT (또는 WARN only) |
| P2-G-17 | `frcgw-experiment-design` skill → claim-to-evidence 표 작성됨, must-not-disappear baseline 누락 0 |

조건 미충족 시 sentinel 생성 금지. `BLOCKED: <reason>` 응답으로 종료.

### 10.3 Gate report

P2 gate report는 `plans/P2_GATE_REPORT.md`에 다음 형식으로 작성한다.

```markdown
# P2 Gate Report (date)

## Read
- (MD list)

## Phase
- P2 | gate status: PASS

## Changed/Created
- (file list)

## Tests/Gates
- pytest -q: N passed
- coverage report: failed=...% recovery=...% ...
- leakage report: 0 forbidden hits / 0 counterfactual hits
- replay report: (n) episodes byte-identical on re-collection

## Subagent verdicts
- frcgw-data-leakage-auditor: PASS
- frcgw-test-runner: PASS
- frcgw-code-reviewer: ACCEPT (or WARN: ...)

## Blockers
- none
```

---

## 11. Closed-Loop Validation Workflow

### 11.1 Per-module loop (each of state/grammar/generator/policies/collector/exporter/coverage_auditor/replay)

```
[1] Edit/Write file
    └─ schema_leakage_guard hook (auto)         → BLOCK | WARN | silent
    └─ post_edit_targeted_tests hook (auto)     → recommendation
[2] If module touches data path:
    └─ Invoke frcgw-data-safety skill
[3] Invoke frcgw-data-leakage-auditor subagent (Read/Glob/Grep on changed files)
    └─ Verdict PASS | BLOCK
    └─ If BLOCK: fix and goto [3]
[4] Invoke frcgw-test-runner subagent (targeted tests)
    └─ Result PASS | FAIL
    └─ If FAIL: fix and goto [4]; same test fails twice → escalate to root cause
[5] Continue to next module
```

### 11.2 P2 final loop (after all modules pass per-module loop)

```
[A] Run dry-run collection
    .\.venv\Scripts\python.exe scripts/01_generate_text_data.py --config configs/data_collection_text.yaml --num-episodes 200
[B] Inspect data/frcgw_text/v0_1/audits/coverage_report.json
    Invoke frcgw-experiment-evaluator subagent → PASS/FAIL on coverage
    If FAIL: adjust policy mixture, re-run [A]
[C] Inspect data/frcgw_text/v0_1/audits/leakage_report.json
    Invoke frcgw-data-leakage-auditor subagent on shards (Grep over JSONL)
    If BLOCK: fix path, re-run [A]
[D] Invoke frcgw-experiment-design skill (claim-to-evidence)
[E] Invoke frcgw-code-reviewer subagent (drift)
[F] Invoke frcgw-test-runner subagent (full pytest -q)
[G] Invoke frcgw-phase-gate skill (write Read/Phase/Changed/Tests/Gates/Blockers)
[H] If all P2-G-01~17 pass: New-Item outputs/phase_gates/P2.passed
[I] Update plans/PHASE_PROGRESS.md (P2 → PASS)
[J] Write plans/P2_GATE_REPORT.md
```

### 11.3 Failure handling matrix

| Failure | Action |
|---|---|
| Hidden token in visible_text | regenerate task family paraphrases; rerun lexical scan |
| Coverage threshold 미달 | policy mixture 비율 조정 또는 oversampling 활성화 |
| Replay non-deterministic | seed 사용 위치 점검; `random.Random(spec.seed)` 단일 인스턴스 enforce |
| pytest red 2x | 에러 root cause 명시 후 main agent fix |
| code-reviewer REJECT | term/baseline drift 수정 후 재검사 |
| sentinel 부재로 main script BLOCK | `/frcgw-phase-check`로 sentinel 정상화 |
| paper_context_ref/ 수정 감지 | 즉시 revert, BLOCKED 응답 |

---

## 12. Sonnet Execution Instructions

Sonnet 모드는 다음 순서로 실행한다. 각 단계 끝마다 frcgw-phase-gate skill
형식(Read/Phase/Changed/Tests/Gates/Blockers)으로 응답한다.

### Step S0 — Pre-P2 sentinel and harness sanity (≤ 1 commit)

```
1. /frcgw-phase-check                        (P1.5 gate review)
2. New-Item outputs/phase_gates/P1.passed    (after sentinel policy review)
3. New-Item outputs/phase_gates/P1.5.passed  (after sentinel policy review)
4. Update plans/PHASE_PROGRESS.md (P1.5 → PASS, P2 → IN_PROGRESS)
5. .\.venv\Scripts\python.exe -m pytest -q   (must remain 53 passed)
```

### Step S1 — TextState / TextEpisodeSpec / TextStepResult

```
1. Write src/frcgw/text_env/state.py per §5.3–5.5
2. Per-module loop (§11.1) until PASS
3. Add tests/test_text_env.py (state transition, hidden field absence)
```

### Step S2 — GrammarEngine

```
1. Write src/frcgw/text_env/grammar.py per §6
2. Per-module loop
3. Extend tests/test_text_env.py with wrong_grammar_failure 4-condition,
   delayed/no_op_valid handling
```

### Step S3 — TaskFamilyTemplate / EpisodeSpecGenerator

```
1. Write src/frcgw/text_env/generator.py per §7
2. Per-module loop
3. Add tests for paraphrase variants, deterministic seed→spec
```

### Step S4 — Policies / PolicyMixtureRunner

```
1. Write src/frcgw/text_env/policies.py per §8
2. Per-module loop
3. Add tests/test_text_policy_mixture.py
```

### Step S5 — TextCollector / build_public_observation

```
1. Write src/frcgw/text_env/collector.py per §9.1
2. Per-module loop with strong frcgw-data-safety + frcgw-data-leakage-auditor
3. Add tests/test_text_data_collection.py
4. Add tests/test_text_public_leakage.py (lexical scan)
```

### Step S6 — ShardExporter / CoverageAuditor / ReplayValidator

```
1. Write src/frcgw/data/shard_exporter.py
2. Write src/frcgw/data/coverage_auditor.py
3. Write src/frcgw/text_env/replay.py
4. Per-module loop
5. Add tests/test_text_replay.py
6. Extend tests/test_text_data_collection.py for JSONL roundtrip + manifest
```

### Step S7 — Driver script + config

```
1. Write configs/data_collection_text.yaml
   - dataset_version: "0.1"
   - schema_version: "schema-06-v0.1"
   - num_episodes: 200
   - max_steps: 12
   - policy_mixture: §8.2 ratios
   - coverage_thresholds: §9.3
   - splits: train=0.7, valid=0.15, test_id=0.15
   - output_dir: data/frcgw_text/v0_1
   - seed: 73211
2. Write scripts/01_generate_text_data.py
   - argparse: --config, --num-episodes (override), --out-dir (override)
   - call collect_episode loop, ShardExporter, CoverageAuditor, LeakageAuditor
   - exit non-zero on coverage/leakage failure
```

### Step S8 — Final P2 loop (§11.2 [A]–[J])

```
1. Run dry-run
2. coverage / leakage / replay reports
3. frcgw-experiment-design / frcgw-code-reviewer / frcgw-test-runner
4. frcgw-phase-gate skill: write final report
5. Create outputs/phase_gates/P2.passed if PASS
6. Write plans/P2_GATE_REPORT.md
7. Update plans/PHASE_PROGRESS.md (P2 → PASS)
```

### Step S9 — Commit (§13)

### General execution rules

- **Never modify** `paper_context_ref/`. Detect and revert if changed.
- **Never delete** P1 schema, P1.5 hooks/skills/agents/commands.
- **Never invoke** `pytest --ignore` broadly.
- **Never commit** without frcgw-code-reviewer ACCEPT/WARN verdict.
- **Never push** to remote without explicit user approval.
- **Always** run targeted pytest before full pytest.
- **Always** call `assert_agent_observation_safe(obs)` before exposing obs to a
  policy.
- **Always** include source MD reference in module docstring.
- **Always** keep module size below ~250 lines; split if larger (P0 scaffold rule).
- **Always** update `plans/PHASE_PROGRESS.md` when phase status changes.

---

## 13. Commit Policy

### 13.1 Pre-commit (S0 sentinel/harness)

선택. P1.5 marker commit이 필요하면:

```
git add .claude/skills .claude/agents .claude/hooks .claude/commands \
        .claude/settings.json .claude/settings.local.json \
        plans/P1_5_PLUGIN_SKILL_AGENT_HOOK_PIPELINE_PLAN.md \
        plans/PHASE_PROGRESS.md plans/PLUGIN_AUDIT_REPORT.md \
        outputs/phase_gates/P1.passed outputs/phase_gates/P1.5.passed
git commit -m "chore(p1.5): finalize harness, sentinels, and progress tracker"
```

### 13.2 P2 main commit (after gate PASS)

```
git add src/frcgw/text_env/ \
        src/frcgw/data/coverage_auditor.py src/frcgw/data/shard_exporter.py \
        scripts/01_generate_text_data.py \
        configs/data_collection_text.yaml \
        tests/test_text_env.py tests/test_text_data_collection.py \
        tests/test_text_policy_mixture.py tests/test_text_public_leakage.py \
        tests/test_text_replay.py \
        plans/P2_TEXT_ONLY_DATA_PLAN.md plans/P2_GATE_REPORT.md plans/PHASE_PROGRESS.md \
        outputs/phase_gates/P2.passed

git commit -m "feat(p2): implement text-only data generator and coverage gates"
```

### 13.3 Forbidden in commit

- `data/frcgw_text/v0_1/*.jsonl` — generated dataset (gitignore).
- `data/frcgw_text/v0_1/audits/*.json` — generated reports (gitignore unless
  small sample explicitly archived; default exclude).
- `outputs/test_reports/*.txt` — generated logs.
- `paper_context_ref/**` — must remain untouched.
- secrets / API tokens (none in P2 anyway).
- P3+ artifacts (not yet built).

`.gitignore`에 다음이 없다면 추가한다:

```
data/frcgw_text/v0_1/train.jsonl
data/frcgw_text/v0_1/valid.jsonl
data/frcgw_text/v0_1/test_id.jsonl
data/frcgw_text/v0_1/audits/
outputs/test_reports/
```

`outputs/phase_gates/*.passed` sentinel은 commit 한다 (작은 zero-byte 마커).

### 13.4 Push policy

P2 commit 후 push는 사용자 명시 승인 시에만. branch는 현재
`feat/p1-schema-visibility` → 새 branch `feat/p2-text-only-data` 권장
(사용자 결정).

---

## 14. Risks and Blockers

### 14.1 Risk register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| visible_text가 hidden grammar token을 누설 | HIGH | dataset invalid | lexical scan test + paraphrase library + frcgw-data-leakage-auditor 매 단계 호출 |
| policy_id/split_id/template_id/seed가 PublicObservation에 침입 | MEDIUM | dataset invalid | P1 `FORBIDDEN_AGENT_FIELDS` + `assert_agent_observation_safe` per step |
| coverage 미달 (특히 repeated_wrong_mapping, shift) | MEDIUM | gate fail | PolicyMixtureRunner.coverage_oversample + adversarial WrongGrammarPolicy 비율 조정 |
| replay non-determinism (random seed misuse) | MEDIUM | replay test fail | 단일 `random.Random(spec.seed)` 인스턴스 collector 안에 격리; 시간/uuid 사용 시 명시적 분리 |
| delayed/no_op_valid 케이스를 wrong_grammar로 오분류 | MEDIUM | mechanism metric distortion | 4-condition rule + 별도 unit test (TEST-04-017 spirit) |
| paper_context_ref/ 우발적 수정 | LOW | scientific contract drift | frcgw-code-reviewer + git diff 확인 + 즉시 revert |
| P1 schema 우발적 수정 | LOW | P1 regression | frcgw-code-reviewer drift check + tests/test_visibility_contract green |
| P1.5 hook 비활성화/삭제 우려 | LOW | 폐루프 깨짐 | hooks 변경 시 plan 외부 승인 요구 |
| dry-run dataset 사이즈 폭증 | LOW | 디스크 폭주 | 200 episodes 기본, max 500, 그 이상은 별도 승인 |
| frcgw-phase-gate sentinel 누락 | MEDIUM | hook BLOCK | S0에서 sentinel 사전 생성 |
| Windows path/encoding 이슈 | MEDIUM | json/yaml IO 실패 | UTF-8 encoding 명시 (`encoding="utf-8"`), forward slash path 사용 |

### 14.2 Stop conditions

다음 발생 시 즉시 멈추고 BLOCKED 응답:

- hidden label leakage detected (any subagent or hook).
- counterfactual leakage detected.
- replay validation failed.
- coverage audit failed without recovery path.
- pytest -q red after 2 consecutive fix attempts.
- paper_context_ref/ 수정 감지.
- must-not-disappear baseline/ablation list 변경 감지.
- frcgw-code-reviewer REJECT verdict.
- LLM fabricated metric values 감지.

---

## 15. Final Recommendation

### 15.1 Plan readiness verdict

```
READY_FOR_SONNET
```

근거:

- P0/P1/P1.5 artifact 모두 검증됨 (pytest 53 passed, P1 schema/leakage guard
  imports OK).
- P2 scope·design·테스트·gate 기준 수치화됨.
- P1.5 harness(7 skill / 7 subagent / 11 hook / 3 command) 사용 위치/이유/통과
  기준 명시됨.
- Sonnet 실행 단계 S0~S9 자족적으로 정의됨.
- commit·push policy, leakage·coverage·replay·gate report 양식 명시됨.
- paper_context_ref/ 수정 0건 보장.

### 15.2 Critical files Sonnet must touch first

```
plans/PHASE_PROGRESS.md            (S0 status update)
outputs/phase_gates/P1.passed       (S0 sentinel)
outputs/phase_gates/P1.5.passed     (S0 sentinel)
src/frcgw/text_env/state.py         (S1 first module)
```

### 15.3 Critical files Sonnet must NOT touch

```
paper_context_ref/**
src/frcgw/schemas/visibility.py
src/frcgw/schemas/episode_schema.py
src/frcgw/schemas/step_schema.py
src/frcgw/schemas/validation.py
src/frcgw/data/leakage_auditor.py
.claude/{skills,agents,hooks,commands}/**  (변경 시 사용자 승인 필요)
tests/test_visibility_contract.py
tests/test_episode_schema.py
tests/test_counterfactual_exclusion.py
tests/test_leakage_auditor.py
```

### 15.4 Open decisions for the user (optional, before S0)

1. branch 전략: `feat/p1-schema-visibility` 그대로 진행 vs. 새 branch
   `feat/p2-text-only-data` 분기.
2. dry-run episode 수: 기본 200 vs. 500.
3. P1.5 sentinel 생성을 `/frcgw-phase-check` 자동 vs. 명시적 main agent
   `New-Item`으로 진행할지.

위 결정이 필요 없으면 Sonnet은 default(현재 branch 유지, 200 episodes,
explicit New-Item)로 진행한다.

---

End of P2_TEXT_ONLY_DATA_PLAN.md
