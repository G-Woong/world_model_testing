> **DEPRECATED for active implementation (2026-05-22).**
>
> The synthetic Web/GUI environment SSoT below is **preserved for paper framing, related-work threat-map, and BASE-026/027/028 direct-threat baselines**. It must **not** be referenced from runtime code paths.
>
> Code modules removed: `src/frcgw/gui_env/*`, `tests/test_gui_env_*`, `scripts/04|06|07_*.py`, `configs/data_collection_gui_mve.yaml`, `outputs/runs/p4_gui_lr_smoke/`.
>
> Scientific contract preserved: nothing in this MD is deleted. BASE-026/027/028 remain in `10_EVALUATION_BASELINE_ABLATION.md`.
>
> Replacement runtime: TBD (next-generation environment — deferred).

---

# 05_SYNTHETIC_WEB_GUI_ENVIRONMENT.md

---
file_id: STEP-05
title: Synthetic Web/GUI Controlled Environment for FRCG-WM
version: v1.0
status: claude_code_ready_environment_contract_not_final_dataset_schema
language: ko
quality_target:
  content_level: 10/10
  research_idea_maturity: 10/10
  claude_code_context_fit: 10/10
  implementation_experiment_specificity: 10/10
depends_on:
  - 00_MASTER_REFERENCE.md
  - 01_RELATED_WORK_THREAT_MAP.md
  - 02_PROBLEM_NOVELTY_FALSIFICATION.md
  - 03_CORE_CONCEPT_TAXONOMY.md
  - 04_TEXT_ONLY_SMOKE_TESTBED.md
purpose:
  - Design a controlled synthetic Web/GUI environment for testing wrong-control-grammar hypothesis persistence.
  - Provide ground-truth hidden regime/control grammar/change-point/reveal-vs-shift labels without leaking them to the agent.
  - Bridge text-only smoke tests to DOM/screenshot/action-effect-log based Web/GUI experiments.
forbidden:
  - Do not finalize dataset schema; leave exact schema to Step 06.
  - Do not finalize model architecture; leave architecture to Step 07.
  - Do not finalize loss/reward training objective; leave objective to Step 08.
  - Do not finalize evaluation table; leave evaluation to Step 10.
next_files:
  - 06_DATA_SCHEMA_AND_LABELING.md
  - 07_LATENT_ARCHITECTURE_DESIGN.md
  - 08_LOSS_REWARD_TRAINING_OBJECTIVE.md
  - 09_PLANNING_THEORY_ALGORITHM.md
  - 10_EVALUATION_BASELINE_ABLATION.md
---

## 1. File Purpose

이 파일은 최종 dataset schema가 아니다. 이 파일은 model architecture 설계서도 아니며, loss/reward objective나 final evaluation table도 아니다. 이 파일의 유일한 목적은 Step 04의 text-only smoke test에서 정의한 mechanism을 실제 browser-like Web/GUI 환경으로 확장할 수 있도록, **controlled synthetic Web/GUI environment**의 설계 계약을 만드는 것이다.

이 환경의 핵심 가치는 realism 자체가 아니라 **causal control**이다. WebArena, VisualWebArena, OSWorld, WorkArena 같은 benchmark는 realism과 외부 타당성에 강하지만, `hidden_regime`, `hidden_control_grammar`, `true_change_point`, `reveal-vs-shift`, `counterfactual alternative effect`를 ground-truth로 제공하지 않는다. 따라서 이 환경은 실제 benchmark를 대체하는 것이 아니라, 논문 핵심 mechanism인 `wrong-control-grammar hypothesis persistence → action-effect evidence → falsification → alternative grammar rollout → action-interface rewrite`를 계량하기 위한 실험 실험실이다.

가장 중요한 금지선은 다음이다.

```text
hidden labels are never provided to the agent as observation.
hidden labels are used only for training supervision, logging, evaluation, and counterfactual analysis.
counterfactual alternative effect table is never exposed to the agent.
```

---


## 1.1 대헌법: Step 05 환경 설계의 절대 규율

이 파일을 읽는 Claude Code는 다음 원칙을 어떤 구현/리팩터링/후속 문서 작성에서도 위반하면 안 된다.

| 헌법 ID | 절대 규율 | 위반 시 붕괴하는 것 | Claude Code 행동 지침 |
|---|---|---|---|
| CONST-05-001 | `hidden_regime`, `hidden_control_grammar`, `true_change_point`, `reveal_vs_shift_label`, `counterfactual_effect_table`은 agent observation에 절대 포함하지 않는다. | 전체 실험의 leakage validity | observation builder를 작성할 때 반드시 denylist assertion 추가 |
| CONST-05-002 | synthetic environment의 목적은 “realism 흉내”가 아니라 “mechanism 계량 가능성”이다. | 환경 positioning | WebArena/OSWorld를 대체한다고 쓰지 말고 causal lab으로 설명 |
| CONST-05-003 | control grammar는 `intent mapping + precondition + expected effect schema`의 결합으로만 인정한다. | control grammar novelty | 단순 `button_disabled`나 `modal_active`를 grammar라고 부르지 말 것 |
| CONST-05-004 | 같은 user intent가 서로 다른 executable action/macro로 바뀌는 pair를 반드시 포함한다. | grammar-vs-state 분리 | every grammar family에 same-intent/different-action example 요구 |
| CONST-05-005 | no-effect는 항상 wrong grammar가 아니다. | falsification metric | benign no-change, noisy observation, delayed effect, loading을 별도 event로 생성 |
| CONST-05-006 | counterfactual label은 synthetic supervision/evaluation 전용이다. | real-world extension claim | real benchmark에서 counterfactual을 안다고 주장 금지 |
| CONST-05-007 | task family, UI template, regime, grammar는 1:1 대응되면 안 된다. | anti-toy validity | balanced cross-product generator와 leakage probes 요구 |
| CONST-05-008 | DOM-only, screenshot-only, action-log-only shortcut을 모두 audit한다. | modality claim | Step 10에 modality ablation 전달 |
| CONST-05-009 | environment trace는 후속 loss/planning/evaluation이 필요한 모든 timestamp를 남겨야 한다. | metric 재현성 | pre/post state hash, action id, hypothesis id, effect id, progress timestamp 기록 |
| CONST-05-010 | 이 파일은 schema 최종본이 아니다. | Step 06 침범 | field name은 design contract로 쓰되 final dtype/serialization은 Step 06에서 확정 |

---

## 1.2 Claude Code Context Routing

Claude Code는 Step 05 관련 작업을 할 때 아래 routing을 따른다. 모든 작업에서 `Must Read First`를 우선 읽고, 필요한 경우 `Then Read`를 확장한다.

| User Intent / Task | Must Read First | Then Read | Use This File Sections | Do Not Assume |
|---|---|---|---|---|
| synthetic Web/GUI 환경 전체 구조 파악 | `05_SYNTHETIC_WEB_GUI_ENVIRONMENT.md` | `04`, `06`, `10` | §4~§6, §14, §16 | dataset schema가 확정됐다고 가정 금지 |
| hidden label / leakage 관련 수정 | `05` §6, §16 | `06_DATA_SCHEMA_AND_LABELING.md` | OBS, GL, STRESS | hidden label을 debugging 편의로 DOM에 넣지 말 것 |
| Playwright/BrowserGym 스타일 구현 설계 | `05` §5, §11, §14 | `06`, `09` | ENV-COMP, ACT, GEN | tool API를 논문 action schema와 동일시 금지 |
| OOD split 추가/수정 | `05` §13 | `10_EVALUATION_BASELINE_ABLATION.md` | SPLIT table | OOD가 진짜 held-out factor인지 검증 없이 추가 금지 |
| grammar library 수정 | `05` §9 | `03`, `04`, `07`, `09` | GRAM, PAIR | grammar를 precondition 하나로 축소 금지 |
| action-effect logger 구현 | `05` §5, §11, §15 | `06`, `08`, `09` | ENV-COMP-014, ACT, trace example | observed effect를 너무 명시적인 hidden reason string으로 만들지 말 것 |
| counterfactual generator 구현 | `05` §12 | `06`, `09`, `10` | CF table | counterfactual table을 agent input에 노출 금지 |
| Step 06 schema 작성 | `05` 전체 | `04`, `07`, `08`, `10` | OBS, ACT, CF, SPLIT, GEN | Step 05의 field 이름을 그대로 final dtype으로 확정 금지 |
| Step 10 evaluation 작성 | `05` §13, §16, §17, §18 | `10`, `01`, `02` | OOD, guardrail, stress, limitation | synthetic success를 real benchmark success로 일반화 금지 |

---

## 1.3 Citation-Grade Source Anchor Ledger

아래 anchor는 Step 05의 설계 방향을 뒷받침하거나 위협하는 외부 기준이다. 이 표는 “최종 related work”가 아니라 환경 설계자가 반드시 참고해야 하는 citation-grade routing table이다.

| Anchor ID | Source / Tool / Paper | Stable Link | Verified Fact Used In This File | How It Constrains Step 05 | Threat / Use |
|---|---|---|---|---|---|
| SRC-05-001 | MiniWoB++ | https://miniwob.farama.org/ | 100개 이상 웹 상호작용 환경, Gymnasium API, Selenium WebDriver 기반 Python interface | synthetic browser task API와 small controlled task benchmark의 선례 | useful anchor |
| SRC-05-002 | WebArena | https://arxiv.org/abs/2307.13854 | realistic self-hostable web environment, four common web domains, functional correctness 중심 평가 | synthetic env는 realism이 아니라 hidden grammar labels의 causal lab으로 positioning해야 함 | realism benchmark / threat |
| SRC-05-003 | VisualWebArena | https://aclanthology.org/2024.acl-long.50/ | realistic visually grounded web tasks for multimodal agents | screenshot/bbox/visual perturbation을 Step 05에 포함해야 함 | visual benchmark / threat |
| SRC-05-004 | OSWorld | https://arxiv.org/abs/2404.07972 | real computer environment의 369개 open-ended tasks | Step 05는 real computer-use external validity를 증명하지 못함 | auxiliary validation anchor |
| SRC-05-005 | WorkArena | https://servicenow.github.io/WorkArena/ | ServiceNow 기반 enterprise web tasks, BrowserGym ecosystem과 연결 | ticket/dashboard/settings/admin-table task family에 근거 제공 | enterprise benchmark anchor |
| SRC-05-006 | BrowserGym | https://github.com/servicenow/browsergym | web agent benchmark 구현/평가를 위한 open/extensible framework | reset/step/action/observation API 설계 참고 | implementation anchor |
| SRC-05-007 | Playwright Trace Viewer | https://playwright.dev/docs/trace-viewer | action별 DOM snapshot, before/after 상태, timing inspection 제공 | action-effect logger와 pre/post trace 설계 참고 | logging anchor |
| SRC-05-008 | Playwright ARIA snapshots | https://playwright.dev/docs/aria-snapshots | accessibility tree의 YAML snapshot 저장/비교 가능 | a11y exporter와 sanitizer 설계 참고 | observation anchor |
| SRC-05-009 | WebWorld | https://arxiv.org/abs/2602.14721 | 1M+ open-web interaction으로 학습한 large-scale web world model, long-horizon simulation | generic web world model claim은 위협받음; Step 05는 hidden grammar causal labels로 차별화해야 함 | direct threat |
| SRC-05-010 | WAC | https://arxiv.org/abs/2602.15384 | consequence simulation + feedback-driven action correction | action correction/rollout claim은 WAC와 직접 비교 필요 | direct threat |
| SRC-05-011 | CUWM | https://arxiv.org/abs/2602.17365 | candidate action에 따른 next UI state prediction, frozen agent test-time search | frozen-agent + world-model search claim은 위협받음 | direct threat |
| SRC-05-012 | VeriGUI | https://arxiv.org/abs/2604.05477 | action-effect verification and self-correction, failure loops/recovery 개선 | Step 05는 verification-only가 아니라 hypothesis persistence/rewrite metric을 제공해야 함 | direct threat |

---

## 1.4 Implementation-Ready Environment Contract

이 섹션은 코드 구현을 강제하는 최종 스펙은 아니지만, Claude Code가 Step 05를 실제 repository에 옮길 때 반드시 지켜야 하는 최소 구현 계약이다.

### 1.4.1 Recommended Repository Layout

```text
frcg_webgui_env/
  env/
    browser_env.py              # reset/step/close API
    observation_builder.py      # agent-safe observation extraction
    action_executor.py          # click/type/select/scroll/wait/drag primitives
    trace_logger.py             # pre/post DOM, screenshot, a11y, effect log
    counterfactual.py           # hidden counterfactual effect generator
  generator/
    task_generator.py           # task family, subgoal graph, instruction sampling
    template_generator.py       # UI template/page flow generation
    regime_engine.py            # hidden regime schedule
    grammar_engine.py           # control grammar, preconditions, expected effects
    event_engine.py             # reveal/shift/change-point/noisy/delayed events
    perturbation_engine.py      # layout/text/DOM/timing perturbations
  webapp/
    package.json
    src/templates/...           # synthetic React/Vite page templates
  schemas/
    env_trace.schema.json       # Step 06에서 최종화
    observation.schema.json     # agent-safe schema
  tests/
    test_no_hidden_label_in_observation.py
    test_counterfactual_not_in_agent_obs.py
    test_task_regime_balance.py
    test_same_intent_different_action_pairs.py
    test_no_effect_not_always_wrong_grammar.py
```

### 1.4.2 Minimal Python API Contract

```python
class FRCGSyntheticWebGUIEnv:
    def reset(self, seed: int, split_id: str, task_family: str | None = None) -> dict:
        """Return agent-safe initial observation. Hidden labels stay internal."""
        ...

    def step(self, action: dict) -> tuple[dict, float, bool, dict]:
        """Execute action and return agent-safe observation, reward, done, public info."""
        ...

    def export_trace(self) -> dict:
        """Return full trace containing hidden labels for training/evaluation only."""
        ...

    def export_agent_observation(self) -> dict:
        """Return sanitized observation with no hidden labels and no counterfactual table."""
        ...
```

### 1.4.3 Mandatory Runtime Assertions

```python
FORBIDDEN_AGENT_KEYS = {
    "hidden_regime",
    "hidden_control_grammar",
    "true_change_point",
    "reveal_vs_shift_label",
    "counterfactual_effect_table",
    "oracle_best_action",
    "true_progress_delta",
}

def assert_agent_safe_observation(obs: dict):
    flat_keys = flatten_keys(obs)
    leaked = FORBIDDEN_AGENT_KEYS.intersection(flat_keys)
    assert not leaked, f"Hidden/eval-only fields leaked into agent observation: {leaked}"
```

### 1.4.4 Minimum Viable Experiment Scope

| MVE ID | Minimum Implementation Unit | Required Count | Why Required | Blocks Step 06/10 If Missing |
|---|---:|---:|---|---|
| MVE-05-001 | task families | ≥ 5 for first smoke Web/GUI version, ≥ 12 for full design | avoid single-domain toy | yes |
| MVE-05-002 | control grammar families | ≥ 8 first, ≥ 20 full | core mechanism coverage | yes |
| MVE-05-003 | same-intent/different-action pairs | ≥ 8 first, ≥ 12 full | grammar operational proof | yes |
| MVE-05-004 | OOD split types | ≥ 3 first, ≥ 10 full | generalization | yes |
| MVE-05-005 | anti-leakage tests | all critical tests | experiment validity | yes |
| MVE-05-006 | counterfactual generator | at least top-k candidate action effects | rollout fidelity | yes |
| MVE-05-007 | trace exporter | pre/post obs + hidden labels + effect evidence | metric computation | yes |

---

## 1.5 Environment-to-Claim Contract

| Claim ID | Claim | Environment Requirement | Metric Enabled | Baseline/Ablation Enabled | Failure If Missing |
|---|---|---|---|---|---|
| CLAIM-ENV-001 | wrong-control-grammar persistence is measurable | hidden grammar + executed hypothesis trace + falsifying evidence timestamp | persistence time | no-control-grammar | core problem metric impossible |
| CLAIM-ENV-002 | grammar differs from action failure | same visible action failure with different grammar causes | failed repetition + cause taxonomy | verifier-only | collapses into action failure |
| CLAIM-ENV-003 | grammar differs from visual grounding | same layout/visible target but different executable macro | OOD grammar shift | DOM/screenshot ablation | collapses into grounding failure |
| CLAIM-ENV-004 | falsification differs from verification | evidence must update hypothesis and rewrite action | evidence-to-update delay | verifier-only / no-falsification | VeriGUI threat wins |
| CLAIM-ENV-005 | alternative rollout matters | counterfactual alternative effects and top-k alternatives | rollout fidelity | no-alt / random-alt / oracle-alt | tree/search threat wins |
| CLAIM-ENV-006 | compute gate matters | planning calls/rollout steps logged | progress per compute | always-plan / uncertainty-gate | compute benefit unproven |
| CLAIM-ENV-007 | synthetic is not toy | held-out template/regime/grammar/OOD splits | ID-OOD drop | leakage probes | reviewer rejects environment |

---

## 2. Imported References
| Imported ID | Source File | Type | Meaning | Why It Matters | Priority |
| --- | --- | --- | --- | --- | --- |
| REF-CORE-001 | 00_MASTER_REFERENCE.md | core thesis | wrong-control-grammar hypothesis persistence | 환경이 직접 계량해야 하는 핵심 failure mode | CRITICAL |
| REF-CORE-002 | 00_MASTER_REFERENCE.md | core thesis | latent regime/control-grammar world model | hidden regime과 hidden grammar를 분리해 생성해야 함 | CRITICAL |
| REF-CORE-003 | 00_MASTER_REFERENCE.md | core thesis | action-effect evidence 기반 falsification | 실제 browser action 전후 증거 로그가 필요 | CRITICAL |
| REF-CORE-004 | 00_MASTER_REFERENCE.md | core thesis | current-vs-alternative hypothesis rollout | counterfactual alternative effect가 필요 | CRITICAL |
| REF-CORE-005 | 00_MASTER_REFERENCE.md | core thesis | intent-to-action rewrite | rewritten action이 실제 DOM progress를 만드는지 검증 | CRITICAL |
| REF-CORE-006 | 00_MASTER_REFERENCE.md | core thesis | decision-relevant compute reallocation | 항상 planning과 uncertainty gate를 구분해야 함 | CRITICAL |
| REF-CORE-007 | 00_MASTER_REFERENCE.md | core thesis | Frozen Base VLM/LLM + reliability module | base agent observation과 proposed module label을 분리 | HIGH |
| REF-CORE-008 | 00_MASTER_REFERENCE.md | core thesis | text-only smoke test | Step 04를 Web/GUI flow로 확장 | HIGH |
| REF-CORE-009 | 00_MASTER_REFERENCE.md | core thesis | synthetic Web/GUI controlled environment | Step 05의 직접 대상 | CRITICAL |
| REF-CORE-010 | 00_MASTER_REFERENCE.md | core thesis | real benchmark auxiliary validation | WebArena/OSWorld류는 보조 realism anchor | HIGH |
| REF-CORE-014 | 00_MASTER_REFERENCE.md | metric thesis | wrong-hypothesis persistence metric | ground-truth label이 있어야 계산 가능 | CRITICAL |
| REF-CORE-015 | 00_MASTER_REFERENCE.md | event thesis | reveal-vs-shift split | event engine과 change-point scheduler 필요 | CRITICAL |
| REF-PROBLEM-001 | 00_MASTER_REFERENCE.md | problem | 반복 실패는 단순 action failure가 아닐 수 있음 | action failure와 grammar persistence를 분리하는 episode 필요 | CRITICAL |
| REF-PROBLEM-002 | 00_MASTER_REFERENCE.md | problem | visual grounding failure와 분리 필요 | grounding 성공 조건에서도 grammar failure가 발생해야 함 | HIGH |
| REF-PROBLEM-003 | 00_MASTER_REFERENCE.md | problem | planning failure와 분리 필요 | subgoal은 맞고 executable mapping만 틀린 case 필요 | CRITICAL |
| REF-PROBLEM-004 | 00_MASTER_REFERENCE.md | problem | verification failure와 분리 필요 | verification 후 posterior/rewrite까지 이어져야 함 | CRITICAL |
| REF-CONCEPT-001 | 00_MASTER_REFERENCE.md | concept | state | hidden state engine의 기본 단위 | CRITICAL |
| REF-CONCEPT-002 | 00_MASTER_REFERENCE.md | concept | regime | interaction mode label 생성 대상 | CRITICAL |
| REF-CONCEPT-003 | 00_MASTER_REFERENCE.md | concept | control grammar | intent-to-action/precondition/effect schema 생성 대상 | CRITICAL |
| REF-CONCEPT-004 | 00_MASTER_REFERENCE.md | concept | change-point | change schedule의 ground truth label | HIGH |
| REF-CONCEPT-005 | 00_MASTER_REFERENCE.md | concept | reveal | 관측 확장 event로 생성 | HIGH |
| REF-CONCEPT-006 | 00_MASTER_REFERENCE.md | concept | shift | regime/grammar update event로 생성 | HIGH |
| REF-CONCEPT-007 | 00_MASTER_REFERENCE.md | concept | current hypothesis | 직전 action 생성 가설을 trace에 기록 | CRITICAL |
| REF-CONCEPT-008 | 00_MASTER_REFERENCE.md | concept | alternative hypothesis | top-k grammar 후보와 counterfactual 비교 | CRITICAL |
| REF-CONCEPT-009 | 00_MASTER_REFERENCE.md | concept | falsification evidence | DOM diff/visual diff/no-effect/validation error로 구성 | CRITICAL |
| REF-CONCEPT-010 | 00_MASTER_REFERENCE.md | concept | action-interface rewrite | retry가 아니라 action macro 변환으로 구현 | HIGH |
| REF-CONCEPT-011 | 00_MASTER_REFERENCE.md | concept | decision-relevant compute | action choice 변화 가능성 기반 gate | HIGH |
| REF-LATENT-001 | 00_MASTER_REFERENCE.md | latent seed | z_state | hidden_state label과 weak proxy 제공 | MEDIUM |
| REF-LATENT-002 | 00_MASTER_REFERENCE.md | latent seed | z_regime | hidden_regime supervision 후보 | CRITICAL |
| REF-LATENT-003 | 00_MASTER_REFERENCE.md | latent seed | z_control_grammar | hidden_control_grammar supervision 후보 | CRITICAL |
| REF-LATENT-004 | 00_MASTER_REFERENCE.md | latent seed | z_change_point | event_type/change_point supervision 후보 | HIGH |
| REF-DATA-001 | 00_MASTER_REFERENCE.md | data seed | DOM tree | agent observation과 logging의 중심 | CRITICAL |
| REF-DATA-002 | 00_MASTER_REFERENCE.md | data seed | screenshot feature | visual grounding 보조 및 VisualWebArena threat 대응 | HIGH |
| REF-DATA-003 | 00_MASTER_REFERENCE.md | data seed | structured action-effect log | falsification과 metric 계산의 핵심 | CRITICAL |
| REF-DATA-004 | 00_MASTER_REFERENCE.md | data seed | hidden regime label | training/evaluation only; agent input 금지 | CRITICAL |
| REF-DATA-005 | 00_MASTER_REFERENCE.md | data seed | hidden control grammar label | training/evaluation only; leakage 방지 필요 | CRITICAL |
| REF-DATA-006 | 00_MASTER_REFERENCE.md | data seed | alternative action effect table | rollout fidelity supervision 및 평가에 필요 | CRITICAL |
| PAPER-001 | 01_RELATED_WORK_THREAT_MAP.md | direct threat | WebWorld | open-web world model threat; generic WM claim 폐기 압력 | CRITICAL |
| PAPER-002 | 01_RELATED_WORK_THREAT_MAP.md | direct threat | WAC | consequence simulation/action correction threat | CRITICAL |
| PAPER-003 | 01_RELATED_WORK_THREAT_MAP.md | direct threat | CUWM | frozen agent + WM test-time search threat | CRITICAL |
| PAPER-004 | 01_RELATED_WORK_THREAT_MAP.md | direct threat | VeriGUI | action-effect verification/recovery threat | CRITICAL |
| PAPER-005 | 01_RELATED_WORK_THREAT_MAP.md | benchmark | WebArena | realistic self-hosted web benchmark anchor | HIGH |
| PAPER-006 | 01_RELATED_WORK_THREAT_MAP.md | benchmark | VisualWebArena | visual grounding realism anchor | HIGH |
| PAPER-007 | 01_RELATED_WORK_THREAT_MAP.md | benchmark | OSWorld | real computer-use benchmark anchor | HIGH |
| PAPER-008 | 01_RELATED_WORK_THREAT_MAP.md | benchmark | WorkArena/BrowserGym | enterprise web + gym framework anchor | HIGH |
| ATTACK-010 | 01_RELATED_WORK_THREAT_MAP.md | reviewer attack | control grammar는 용어 재포장 | 환경에서 동일 intent/different executable action pair로 방어 | CRITICAL |
| ATTACK-011 | 01_RELATED_WORK_THREAT_MAP.md | reviewer attack | synthetic benchmark는 toy | anti-leakage/OOD/realism guardrail 필요 | CRITICAL |
| ATTACK-012 | 01_RELATED_WORK_THREAT_MAP.md | reviewer attack | hidden labels are unrealistic | label은 mechanism 검증용이며 agent input 금지 설계 필요 | HIGH |
| MCX-001 | 02_PROBLEM_NOVELTY_FALSIFICATION.md | counterexample | pagination vs infinite scroll | same intent가 서로 다른 executable action을 요구 | CRITICAL |
| MCX-002 | 02_PROBLEM_NOVELTY_FALSIFICATION.md | counterexample | modal-blocked direct click | overlay state와 blocker grammar 구현 필요 | CRITICAL |
| MCX-003 | 02_PROBLEM_NOVELTY_FALSIFICATION.md | counterexample | form-invalid disabled submit | precondition/effect schema 필요 | CRITICAL |
| MCX-004 | 02_PROBLEM_NOVELTY_FALSIFICATION.md | counterexample | loading/stale DOM timing | delay/noisy effect와 falsification 분리 필요 | HIGH |
| MCX-005 | 02_PROBLEM_NOVELTY_FALSIFICATION.md | counterexample | responsive menu hidden navigation | layout perturbation과 grammar shift 연결 | HIGH |
| METRIC-001 | 02_PROBLEM_NOVELTY_FALSIFICATION.md | metric | wrong-control-grammar persistence time | 환경 trace에서 반드시 계산 | CRITICAL |
| METRIC-002 | 02_PROBLEM_NOVELTY_FALSIFICATION.md | metric | failed-action repetition rate | 반복 실패 측정 | CRITICAL |
| METRIC-003 | 02_PROBLEM_NOVELTY_FALSIFICATION.md | metric | action-interface switch delay | rewrite delay 측정 | HIGH |
| METRIC-004 | 02_PROBLEM_NOVELTY_FALSIFICATION.md | metric | recovery delay | VeriGUI와 구분되는 recovery 성능 측정 | HIGH |
| METRIC-005 | 02_PROBLEM_NOVELTY_FALSIFICATION.md | metric | alternative rollout fidelity | counterfactual label 필요 | CRITICAL |
| CONCEPT-003 | 03_CORE_CONCEPT_TAXONOMY.md | taxonomy | regime/control grammar 분리 | 환경 엔진을 둘로 나누는 근거 | CRITICAL |
| REVEAL-SHIFT-001 | 03_CORE_CONCEPT_TAXONOMY.md | taxonomy | reveal은 state belief update | state transition과 분리 label 필요 | HIGH |
| REVEAL-SHIFT-002 | 03_CORE_CONCEPT_TAXONOMY.md | taxonomy | shift는 regime/grammar update | change-point scheduler 필요 | HIGH |
| HYPOTHESIS-004 | 03_CORE_CONCEPT_TAXONOMY.md | taxonomy | falsification score는 likelihood ratio proxy | evidence likelihood를 trace에 계산 가능하게 해야 함 | CRITICAL |
| ACTION-INTERFACE-004 | 03_CORE_CONCEPT_TAXONOMY.md | taxonomy | rewritten action은 executable macro | Playwright action sequence와 연결 필요 | HIGH |
| TEXT-SCHEMA-001 | 04_TEXT_ONLY_SMOKE_TESTBED.md | text schema | episode_id/task_family/instruction | Web/GUI episode schema로 확장 | HIGH |
| TEXT-SCHEMA-010 | 04_TEXT_ONLY_SMOKE_TESTBED.md | text schema | current_hypothesis/alternative_hypotheses | 환경 trace의 hypothesis fields로 확장 | CRITICAL |
| TEXT-TEST-001 | 04_TEXT_ONLY_SMOKE_TESTBED.md | test case | modal blocked smoke test | 실제 overlay/covered-by DOM state로 구현 | CRITICAL |
| TEXT-TEST-002 | 04_TEXT_ONLY_SMOKE_TESTBED.md | test case | required option add-to-cart | select option + disabled button 구현 | CRITICAL |
| TEXT-LIMITATION-001 | 04_TEXT_ONLY_SMOKE_TESTBED.md | limitation | visual grounding 불가 | Step 05에서 screenshot/bbox 제공 필요 | HIGH |
| TEXT-GATE-001 | 04_TEXT_ONLY_SMOKE_TESTBED.md | gate | no-grammar ablation 하락 | 환경이 grammar label을 충분히 다양하게 제공해야 함 | CRITICAL |

## 3. Search Expansion Ledger

| Search ID | Query | Source/Paper/Tool/Concept | Key Finding | How It Informs Environment | Risk/Threat | Follow-up |
| --- | --- | --- | --- | --- | --- | --- |
| SEARCH-05-001 | MiniWoB++ web interaction benchmark | MiniWoB++ / Farama docs, GitHub | 100개 이상 웹 상호작용 환경, Gymnasium API, Selenium WebDriver 인터페이스 제공 | 작은 synthetic browser task 설계의 기본 anchor | 과도하게 단순하면 toy 공격 | Step 05는 MiniWoB보다 hidden grammar/change labels를 더 강하게 설계 |
| SEARCH-05-002 | WebArena autonomous web agents benchmark | WebArena paper/site/GitHub | self-hosted realistic web environment; natural language command to web interaction | 현실성 보조 anchor. 다만 hidden grammar label 없음 | realism benchmark만으로 mechanism 계량 어려움 | Step 10 보조 평가에 연결 |
| SEARCH-05-003 | VisualWebArena multimodal web agents | VisualWebArena ACL 2024/arXiv/GitHub | visually grounded realistic web tasks를 평가 | screenshot/bbox 관측 설계 필요성 제공 | text-only 성공의 한계 강조 | visual perturbation split 필요 |
| SEARCH-05-004 | OSWorld computer use benchmark | OSWorld site/arXiv | 369개 real-world computer tasks와 execution-based evaluation | real computer-use realism anchor | synthetic label 없음 | 보조 external validity로만 사용 |
| SEARCH-05-005 | WorkArena enterprise web agents | WorkArena PMLR/site/GitHub | ServiceNow 기반 knowledge-work web tasks와 BrowserGym 제안 | enterprise flow/task family 설계 anchor | remote hosted benchmark라 hidden causal labels 없음 | task family에 ticket/settings/dashboard 반영 |
| SEARCH-05-006 | BrowserGym web agent benchmark environment | BrowserGym docs/GitHub/arXiv | Chromium 기반 gym-like web automation, MiniWoB/WebArena/WorkArena 통합 | 환경 API 설계와 observation/action space 표준화 anchor | 기존 benchmark만 쓰면 grammar labels 부족 | wrapper/API 설계 참고 |
| SEARCH-05-007 | Playwright trace viewer DOM snapshots | Playwright Trace Viewer docs | 각 action 전/중/후 DOM snapshots, screenshots, network/console/timing trace 제공 | action-effect logger와 trace exporter 설계 anchor | trace 자체가 agent input으로 새면 leakage | logging-only channel로 분리 |
| SEARCH-05-008 | Playwright aria snapshots accessibility tree | Playwright aria snapshots docs | accessibility tree를 YAML snapshot으로 저장/비교 가능 | accessibility tree exporter 설계 anchor | aria label에 hidden grammar가 새는 위험 | hidden class/text 금지 |
| SEARCH-05-009 | Playwright locators role name | Playwright locator docs | role/name 기반 robust locator 권장 | executable action grounding, bbox/role 기록에 유용 | agent에게 role만 주면 너무 쉬울 수 있음 | DOM/screenshot/a11y ablation 필요 |
| SEARCH-05-010 | Playwright MCP browser snapshot click type drag | Playwright MCP docs | browser_snapshot, click, type, fill_form, drag 등 action primitive 제공 | action executor primitive 후보 | MCP tool schema를 그대로 논문 action space로 착각 금지 | Step 06/09에서 abstract action schema로 변환 |
| SEARCH-05-011 | WebWorld large-scale world model web agent training | WebWorld arXiv 2602.14721 | 1M+ open-web interactions, long-horizon simulation 30+ steps, multi-format input 지원 | direct threat: generic web world model claim 폐기 | 우리 환경은 학습 규모가 아니라 hidden grammar causal label이 핵심 | related work/Step10에서 강하게 방어 |
| SEARCH-05-012 | WAC world model action correction web agents | WAC arXiv 2602.15384 | world model consequence simulation + judge 기반 action correction | direct threat: simulation/correction overlap | 우리 환경은 correction보다 grammar falsification metric 생성 | baseline으로 설계 필요 |
| SEARCH-05-013 | CUWM computer use world model | CUWM arXiv 2602.17365 | candidate action에 따른 next UI state prediction, frozen agent test-time action search | direct threat: frozen agent + WM search overlap | 우리 환경은 next screenshot보다 regime/grammar persistence label 중심 | Step 10 baseline으로 연결 |
| SEARCH-05-014 | VeriGUI action-effect verification GUI agents | VeriGUI/VeriWeb sources | long-chain GUI/Web task verifiability와 recovery/verification 강조 | verification-only baseline threat | evidence→hypothesis→rewrite 경로로 차별화 | Step 10에 verifier baseline |
| SEARCH-05-015 | DOM diff browser automation | Playwright trace/docs + testing practice | action 전후 DOM snapshot 비교 가능 | DOM diff/observed effect 설계 anchor | DOM diff만으로 visual overlay를 못 잡을 수 있음 | visual diff와 covered_by도 기록 |
| SEARCH-05-016 | web agent robustness perturbation benchmark | web agent robustness/perturbation literature anchor | layout shift, execution disruption, altered semantics 등이 web agent failure를 유발 | OOD perturbation split 필요 | robustness failure와 grammar persistence 혼동 위험 | Split을 claim별로 분리 |
| SEARCH-05-017 | synthetic UI generation agents | procedural UI generation concept | template/element/layout를 seed로 생성 가능 | procedural UI template generator 설계 anchor | template shortcut/seed leakage 위험 | randomization + held-out template |
| SEARCH-05-018 | counterfactual action effects environment | simulator/counterfactual environment concept | 실제 Web에서는 counterfactual unknown이나 synthetic에서는 oracle table 생성 가능 | alternative rollout fidelity supervision에 필요 | agent input leak 위험 극대 | strict hidden channel |
| SEARCH-05-019 | accessibility tree GUI agent observation | WebArena/BrowserGym/Playwright a11y tree practice | web agents가 DOM/HTML/a11y tree/screenshot을 관측으로 사용 | multi-modal observation design | hidden label이 aria attribute로 새는 위험 | a11y sanitization |
| SEARCH-05-020 | browser automation benchmark reinforcement learning | MiniWoB++ + BrowserGym | Gym-style reset/step/observation/reward/action 인터페이스가 적합 | environment API 구조 참고 | RL benchmark로만 보이면 논문 핵심 약화 | mechanism labels 강조 |
| SEARCH-05-021 | procedural web UI generation benchmark | UNVERIFIED_ANCHOR | procedural task/UI generation은 개념적으로 필요하나 특정 표준 benchmark는 불확실 | UI generator 설계의 필요성을 정리 | 검증된 paper로 단정 금지 | Step 06 구현 시 자체 generator spec 필요 |
| SEARCH-05-022 | browser action effect logging | Playwright tracing + DOM snapshot docs | action, screenshot, DOM, network timeline을 기록 가능 | action-effect logger 설계에 직접 적용 | trace overhead/비동기 noise | trace sampling/summary 필요 |
| SEARCH-05-023 | GUI agent DOM screenshot accessibility tree representation | VisualWebArena/BrowserGym/CUWM | screenshot+a11y/DOM+candidate action 기반 관측이 일반적 | 관측 space 분리 설계 | visual claim을 과장할 위험 | screenshot은 관측/ablation으로 제한 |
| SEARCH-05-024 | layout shift modal loading web agent failure | robustness benchmark anchor | layout shift, modal, loading, execution disruption이 흔한 failure source | stress/OOD split으로 반영 | perturbation 자체와 grammar shift 혼동 | label rule 필요 |
| SEARCH-05-025 | WebArena environment design self-hosted websites | WebArena paper/site | four popular website categories와 reproducible evaluation | realistic task flow 설계 anchor | hidden causal labels 없음 | mechanism lab로 synthetic 필요 |

## 4. Environment Scope and Anti-Toy Positioning

| Scope ID | Question | Decision | Reason | Risk | Later Step |
| --- | --- | --- | --- | --- | --- |
| SCOPE-05-001 | 왜 synthetic controlled environment가 필요한가? | wrong grammar persistence를 ground-truth로 계량하려면 hidden regime/grammar/change labels와 counterfactual effects가 필요하다. | real benchmarks는 realism은 강하지만 labels가 부족하다. | toy로 보이면 novelty가 약화된다. | Step 06/10 |
| SCOPE-05-002 | 왜 WebArena/OSWorld만으로 부족한가? | 그들은 task success와 execution trace는 제공하지만 hidden control grammar와 alternative effect oracle은 제공하지 않는다. | 핵심 metric이 success rate가 아니라 persistence/rewrite/rollout fidelity이기 때문이다. | realism 부족 공격이 남는다. | Step 10 보조 실험 |
| SCOPE-05-003 | text-only와 무엇이 다른가? | DOM, screenshot, accessibility tree, bbox, overlay, async state, browser action logging을 포함한다. | symbolic action이 실제 UI action으로 내려가는지 검증한다. | 복잡도가 급증한다. | Step 06 |
| SCOPE-05-004 | 무엇을 검증하는가? | grammar shift 조건에서 repeated failed action이 줄고 alternative grammar rewrite가 progress를 만드는지 검증한다. | 논문 메커니즘 검증의 메인 환경이다. | 환경 shortcut이 있으면 metric이 무의미해진다. | Step 10 |
| SCOPE-05-005 | 검증하지 못하는 것은? | open-world 웹 다양성, 실제 계정/세션, third-party latency, 보안 제약, 실사용 instruction ambiguity는 완전히 검증하지 못한다. | controlled lab이기 때문이다. | 과장하면 reviewer 공격을 받는다. | Step 18/10 |
| SCOPE-05-006 | toy shortcut 방지 방법은? | task-family/regime 균형, held-out template, paraphrase, decoy, layout randomization, seed separation을 둔다. | label leakage와 template memorization 방지. | 불충분하면 synthetic toy 공격. | Step 16 |
| SCOPE-05-007 | label leakage 방지 방법은? | hidden labels는 DOM class/text/aria/data-*에 절대 넣지 않고 trace-only metadata로 저장한다. | agent가 label을 직접 읽으면 실험 붕괴. | 디버그 편의로 새기 쉬움. | Step 06 |
| SCOPE-05-008 | DOM 역할은? | element hierarchy, role, enabled/visible/clickable, form state, DOM diff를 제공한다. | action grounding과 effect logging의 중심. | DOM만으로 너무 쉽게 풀릴 수 있음. | Step 10 ablation |
| SCOPE-05-009 | screenshot 역할은? | visual overlap, overlay, layout shift, bbox alignment, visual diff를 제공한다. | VisualWebArena/OSWorld threat 대응. | screenshot 없이도 풀리면 visual claim 약화. | Step 10 modality ablation |
| SCOPE-05-010 | action-effect log 역할은? | executed action, expected effect, observed diff, failure evidence, progress delta를 기록한다. | falsification score와 persistence metric의 원천. | evidence가 너무 명시적이면 shortcut. | Step 06 |
| SCOPE-05-011 | browser timing/asynchrony 포함 수준은? | loading, delayed validation, stale DOM, optimistic rollback을 controlled stochastic schedule로 포함한다. | 실제 GUI 실패와 연결. | falsification과 noise가 혼동될 수 있다. | Step 08/10 |
| SCOPE-05-012 | 환경에서 실패하면 무엇을 폐기해야 하는가? | no-grammar/no-falsification/no-alt-rollout ablation이 무너지지 않으면 core mechanism claim을 폐기하거나 축소한다. | 환경은 viability gate이기도 하다. | 나쁜 결과를 숨기면 설계 전체가 취약해진다. | FINAL/Step10 |

## 5. Environment Architecture Overview

```text
Procedural Task Generator
  → Instruction / Subgoal Graph Generator
  → UI Template Generator
  → Hidden State Engine
  → Hidden Regime Engine
  → Control Grammar Engine
  → Browser Renderer / DOM Generator / Accessibility Exporter
  → Agent-Safe Observation Filter
  → Agent Action Executor
  → Action Precondition Checker
  → Action Effect Executor
  → Reveal/Shift Event Engine
  → Change-Point Scheduler
  → Perturbation Engine
  → Action-Effect Logger
  → Counterfactual Alternative Effect Generator
  → Progress / Reward Tracker
  → Success Checker
  → Trace Exporter
  → Seed / Version Manager
```

이 구조에서 `Hidden State / Regime / Grammar`는 환경 내부의 ground-truth channel이다. agent observation channel에는 sanitized DOM, accessibility tree, screenshot, visible/enabled/clickable 상태, previous action/effect 요약만 제공된다. hidden labels와 counterfactual table은 Step 06의 schema에서 metadata-only field로 고정되어야 한다.

| Component ID | Component | Input | Output | Role | Connected Claim | Risk If Missing |
| --- | --- | --- | --- | --- | --- | --- |
| ENV-COMP-001 | procedural task generator | seed, split config, task family prior | instruction, subgoal graph, task metadata | 다양한 task와 subgoal을 생성 | REF-CORE-001/009 | task-regime 1:1 shortcut 발생 |
| ENV-COMP-002 | UI template generator | task metadata, template pool, perturbation config | React/Vite page templates | realistic page/view 구성 | REF-DATA-001/002 | toy page만 생성됨 |
| ENV-COMP-003 | DOM generator | template, hidden state | DOM tree, roles, attributes | browser-like structural observation 생성 | REF-DATA-001 | hidden label leakage |
| ENV-COMP-004 | visual/screenshot renderer | DOM/CSS/layout | screenshot, bbox, visual diff base | visual grounding/overlay evidence 제공 | REF-DATA-002 | visual claim 부재 |
| ENV-COMP-005 | accessibility tree exporter | rendered page | a11y tree snapshot | agent observation 및 robust locator anchor | PAPER-008 | aria leakage |
| ENV-COMP-006 | hidden state engine | task state, action effect | updated hidden_state | progress, validation, modal, loading 상태 관리 | REF-CONCEPT-001 | state/regime 혼동 |
| ENV-COMP-007 | hidden regime engine | state/context/schedule | hidden_regime | interaction mode label 생성 | REF-CONCEPT-002 | mode label 불명확 |
| ENV-COMP-008 | control grammar engine | intent, regime, state | valid executable mapping/preconditions/effect schema | 핵심 grammar label 생성 | REF-CONCEPT-003 | grammar가 precondition으로 축소 |
| ENV-COMP-009 | action precondition checker | action, DOM, hidden_state, grammar | valid/invalid/reason | failed action 원인 분리 | REF-CONCEPT-003 | invalid 이유가 불명확 |
| ENV-COMP-010 | action effect executor | valid action, hidden_state | post_state, DOM update, visual update | actual transition 수행 | REF-CORE-003 | effect evidence 없음 |
| ENV-COMP-011 | reveal/shift event engine | action/effect/schedule | event_type, reveal_shift_label | reveal vs shift ground truth 생성 | REF-CORE-015 | event taxonomy 붕괴 |
| ENV-COMP-012 | change-point scheduler | episode step, stochastic events | change events | timed/user-triggered change 생성 | REF-CONCEPT-004 | change label 없음 |
| ENV-COMP-013 | perturbation engine | split config, UI template | layout/text/DOM/timing perturbation | OOD/generalization 검증 | REF-CORE-010 | ID overfit |
| ENV-COMP-014 | action-effect logger | pre/post DOM, screenshot, action, hidden labels | structured trace | falsification/eval 계산 원천 | REF-DATA-003 | metric 계산 불가 |
| ENV-COMP-015 | counterfactual alternative effect generator | state, candidate actions, grammar hypotheses | oracle alternative effect table | rollout fidelity supervision/eval | REF-DATA-006 | alternative rollout 검증 불가 |
| ENV-COMP-016 | progress tracker | subgoal graph, state | progress_score, progress_delta | reward/normalized return 계산 | REF-REWARD-001 | success만 남아 dense 분석 불가 |
| ENV-COMP-017 | reward calculator | progress, failures, compute | reward components | training/eval reward 산출 | REF-REWARD-* | reward hacking |
| ENV-COMP-018 | success checker | task-specific verifier | done/success | execution-based success 판정 | PAPER-005/007 | subjective success |
| ENV-COMP-019 | trace exporter | episode traces, labels | jsonl/parquet/artifacts | Step 06 dataset로 연결 | TEXT-SCHEMA-* | 재현성 부족 |
| ENV-COMP-020 | seed/version manager | global seed, split id, template version | deterministic episode ids | reproducibility/split leakage 방지 | QG-05 | seed leakage |
| ENV-COMP-021 | agent observation filter | full environment state | agent-safe observation | hidden labels 제거 | REF-RISK label leakage | leakage 실험 붕괴 |
| ENV-COMP-022 | browser wrapper | Playwright/Chromium process | reset/step/close API | BrowserGym-style interface 제공 | PAPER-008 | 실행 불안정 |

## 6. Observation Space Design

명시 규칙:

```text
hidden_regime, hidden_control_grammar, true_change_point, reveal_vs_shift_label, alternative_action_effect_table은 agent input으로 절대 제공하지 않는다.
이들은 training supervision, logging, evaluation, counterfactual analysis에만 사용한다.
```

| Observation ID | Observation Item | Provided To Agent? | Used For Label? | Used For Logging? | Leakage Risk | Guardrail |
| --- | --- | --- | --- | --- | --- | --- |
| OBS-001 | DOM tree | YES | NO | YES | class/data attr에 hidden regime가 새는 위험 | hidden label 단어 금지, sanitizer |
| OBS-002 | accessibility tree | YES | NO | YES | aria-label에 grammar 정보 누출 | a11y text paraphrase/blacklist |
| OBS-003 | screenshot | YES | NO | YES | layout shortcut 가능 | layout randomization, visual decoy |
| OBS-004 | bounding boxes | YES | NO | YES | bbox 위치로 template memorization | coordinate jitter/responsive variants |
| OBS-005 | visible state | YES | YES | YES | visible만으로 regime shortcut | regime-balanced visible states |
| OBS-006 | enabled/clickable state | YES | YES | YES | disabled=wrong grammar shortcut | disabled 아닌 wrong grammar cases 포함 |
| OBS-007 | overlay/covered-by state | YES/PARTIAL | YES | YES | covered_by가 modal_blocked를 직접 노출 | agent에는 UI-grounded description만 제공 |
| OBS-008 | scrollability | YES | YES | YES | scrollable=true가 infinite_scroll shortcut | pagination+scrollable decoy 포함 |
| OBS-009 | form validation state | YES/PARTIAL | YES | YES | required field label shortcut | decoy required indicators |
| OBS-010 | loading/stale state | YES/PARTIAL | YES | YES | loading=no-effect shortcut | delayed valid effect와 noisy no-effect 분리 |
| OBS-011 | previous action | YES | NO | YES | history 길이 shortcut | history truncation variants |
| OBS-012 | observed effect | YES/PARTIAL | YES | YES | evidence가 너무 명시적일 위험 | raw diff + summarized evidence 분리 |
| OBS-013 | DOM diff | NO/PARTIAL | YES | YES | diff summary에 label 누출 | agent에는 raw/sanitized diff만 |
| OBS-014 | visual diff | NO/PARTIAL | YES | YES | threshold shortcut | noise calibration |
| OBS-015 | action-effect evidence | YES/PARTIAL | YES | YES | wrong grammar reason을 직접 말하면 누출 | three levels: raw, weak summary, label-only hidden |
| OBS-016 | hidden regime label | NO | YES | YES | agent input으로 새면 붕괴 | metadata-only |
| OBS-017 | hidden control grammar label | NO | YES | YES | 핵심 label 누출 | metadata-only |
| OBS-018 | true change-point label | NO | YES | YES | event classifier cheating | metadata-only |
| OBS-019 | reveal-vs-shift label | NO | YES | YES | label leakage | metadata-only |
| OBS-020 | progress label | NO/PARTIAL | YES | YES | reward hacking 가능 | agent에는 task natural feedback만 |
| OBS-021 | alternative action effect table | NO | YES | YES | counterfactual oracle 누출 | evaluation/training supervision only |
| OBS-022 | network/timing trace | NO/PARTIAL | YES | YES | timing feature shortcut | bucketization/noise |

## 7. Task Family Design

| Task ID | Task Family | User Instruction Type | UI Pages | Required Subgoals | Possible Regimes | Success Condition | Why Useful |
| --- | --- | --- | --- | --- | --- | --- | --- |
| TASK-001 | shopping search/filter | 조건에 맞는 상품을 찾아 필터 적용 | list, filter panel, detail | 검색어 입력→필터 열기→조건 적용→상품 선택 | pagination, infinite_scroll, hidden_filter, modal_blocked | 조건 만족 상품 선택 | 상업 웹의 대표 long-horizon flow |
| TASK-002 | product listing navigation | 다음 결과 페이지/목록 보기 | list page | 목록 이동→상품 확인 | pagination, infinite_scroll, replaced_vs_appended | 새 결과 카드 노출 | same intent/different action 검증 |
| TASK-003 | add-to-cart with required option | 옵션 선택 후 장바구니 담기 | detail page, mini cart | 옵션 선택→button enable→add | form_invalid, disabled_button, prerequisite_option | cart_count 증가 | precondition grammar 핵심 |
| TASK-004 | checkout form | 배송/결제 정보 제출 | cart, checkout form, confirmation | 필수 입력→검증→제출→확인 | form_invalid, delayed_validation, confirmation_flow | 주문 확인 상태 | form/confirmation shift |
| TASK-005 | account settings update | 설정값 변경 저장 | settings tabs, modal | 탭 이동→필드 수정→저장 | tabbed_navigation, modal_blocked, permission_required | 설정 반영 | enterprise UI flow |
| TASK-006 | dashboard filtering | 대시보드 테이블 필터링 | dashboard, table, filter drawer | 필터 열기→조건 설정→결과 확인 | hidden_filter, accordion_reveal, loading | 테이블 행 조건 만족 | data app realism |
| TASK-007 | knowledge base search | 문서 검색 후 정답 문서 열기 | search page, article | 검색→결과 탐색→문서 열기 | search_replaced, search_appended, infinite_scroll | 정답 문서 표시 | search effect schema 검증 |
| TASK-008 | ticket creation | 지원 티켓 생성 | ticket form, category modal | 카테고리 선택→내용 입력→submit | form_invalid, permission_required, confirmation_flow | ticket id 생성 | WorkArena 유사 업무 flow |
| TASK-009 | permission/confirmation workflow | 권한 요청 승인 후 진행 | permission page, modal | 권한 요청→승인→원래 action | permission_required, confirmation_flow, modal_blocked | target action 성공 | blocker removal grammar |
| TASK-010 | multi-step profile update | 프로필 여러 단계 수정 | wizard, settings page | 단계 이동→필드 수정→저장 | multi_step_wizard, validation, responsive_menu | profile updated | long-horizon composition |
| TASK-011 | calendar/event creation | 일정 생성 | calendar view, event modal | 날짜 선택→event form→save | modal_blocked, delayed_validation, confirmation | event visible | modal/form/timing 결합 |
| TASK-012 | document/file management | 파일 찾기/정렬/이동 | file list, folder tree | 폴더 열기→검색/정렬→이동 | tree_navigation, drag_drop, confirmation | 파일 위치 변경 | desktop/web hybrid task |
| TASK-013 | admin table sorting/filtering | 관리자 테이블에서 항목 수정 | admin table, edit modal | 정렬→행 선택→edit→save | tabbed_navigation, modal_blocked, loading | row value changed | enterprise table flow |
| TASK-014 | notification/preferences setup | 알림 선호 설정 | preferences, toggles | 섹션 열기→toggle→save | accordion_reveal, disabled_button, confirmation | preference saved | toggle/action effect ambiguity |
| TASK-015 | multi-page onboarding | 온보딩 단계 완료 | wizard pages | 다음→필수 선택→확인 | multi_step_wizard, prerequisite_option, delayed_validation | onboarding complete | long-horizon + grammar shift |

## 8. UI Template and Page Flow Library

| Template ID | Template | Pages/Views | Interactive Elements | Possible Perturbations | Relevant Regimes | Risk |
| --- | --- | --- | --- | --- | --- | --- |
| TPL-001 | product list page | list/search/filter/result cards | search input, filter button, cards, pagination/scroll container | layout shift, card order, text paraphrase | pagination, infinite_scroll, hidden_filter | task-family shortcut 위험 |
| TPL-002 | product detail page | detail/options/cart sidebar | option dropdowns, add button, quantity, modal | disabled state, option order, overlay | form_invalid, prerequisite_option, modal_blocked | disabled shortcut |
| TPL-003 | checkout form | cart/address/payment/confirm | inputs, selects, submit, validation messages | delayed validation, required fields | form_invalid, confirmation_flow | validation leakage |
| TPL-004 | settings page | tabs/sections/forms | tabs, toggles, save button, modal | responsive menu, hidden section | tabbed_navigation, responsive_menu | tab names shortcut |
| TPL-005 | dashboard table | table/filter drawer/charts | filter drawer, table rows, sort buttons | loading, column reorder | hidden_filter, loading | DOM-only shortcut |
| TPL-006 | search result page | search box/result list/detail | search input, result cards, sort, scroll | replaced/appended variants | search_replaced, search_appended | effect schema shortcut |
| TPL-007 | knowledge base page | category tree/article view | category tree, accordion, article link | accordion order, lazy loading | accordion_reveal, loading | reveal/shift ambiguity |
| TPL-008 | ticket form | category picker/form/submit | dropdown, modal, text area, submit | permission modal, confirmation | permission_required, confirmation_flow | category-regime shortcut |
| TPL-009 | calendar/event form | calendar grid/event modal | date cell, modal form, save | modal overlay, delayed validation | modal_blocked, delayed_validation | visual localization challenge |
| TPL-010 | file/document manager | folder tree/file list/context menu | tree nodes, drag/drop, menu, confirm | drag target changes, context modal | drag_drop, confirmation | complex action executor 필요 |
| TPL-011 | multi-step wizard | step pages/progress bar | next/back/required selections | step order randomization | multi_step_wizard, prerequisite_option | long-horizon 과소평가 |
| TPL-012 | modal/overlay flow | base page + overlay | overlay close, accept, reject, target behind overlay | z-index, transparent overlay | overlay_intercept, modal_blocked | covered_by logging 필요 |

## 9. Regime and Control Grammar Engine

`regime`은 UI의 interaction mode이고, `control grammar`는 동일 intent가 executable action 또는 macro로 번역되는 규칙이다. 이 섹션의 목표는 grammar를 단순 precondition label로 축소하지 않는 것이다. 각 grammar는 반드시 `intent mapping + preconditions + expected effect`를 가진다.

| Grammar ID | Regime | Control Grammar | Intent Mapping | Preconditions | Expected Effect | Wrong Hypothesis It Induces | Falsifying Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| GRAM-001 | pagination | next_results → click(next_button) | next_button visible/enabled | page_index += 1, cards replaced | infinite_scroll로 오해 | click next no target/disabled, scroll container available |
| GRAM-002 | infinite_scroll | next_results → scroll(container_down) | container scrollable, near bottom loads | cards appended | pagination으로 오해 | next button absent, scroll adds cards |
| GRAM-003 | modal_blocked | target_intent → close_modal → target_action | overlay active | overlay removed, target clickable | direct_click | click target no effect, covered_by overlay |
| GRAM-004 | form_invalid | submit_intent → fill_required → submit | required fields valid | validation cleared, submit accepted | direct_submit | validation error, disabled/invalid field |
| GRAM-005 | loading_stale_dom | target_click → wait_until_stable → click | loading false, element stable | click executes on stable node | immediate_click | element detached, spinner active |
| GRAM-006 | disabled_button | proceed → satisfy_enable_condition → click | button enabled condition met | button enabled then action effect | click_disabled | aria-disabled/disabled true, no effect |
| GRAM-007 | hidden_filter | apply_filter → open_filter_panel → set_filter | filter panel open | filter controls visible, result filtered | click hidden filter control | target absent until panel open |
| GRAM-008 | responsive_menu | navigate → open_hamburger → click_menu_item | small viewport/collapsed nav | menu item visible then route change | top_nav_click | top nav target hidden, hamburger visible |
| GRAM-009 | permission_required | perform_target → request/accept_permission → target | permission granted | permission state true, target succeeds | direct_target | permission prompt blocks effect |
| GRAM-010 | confirmation_flow | destructive/proceed → click target → confirm | confirm modal active after first click | confirmed state transition | single_click_done | confirm dialog appears, no final change |
| GRAM-011 | accordion_reveal | inspect_option → expand_section | section collapsed | new controls revealed | scroll/click hidden child | child absent until expand |
| GRAM-012 | scroll_container_vs_page | find_item → scroll(inner_container) | inner container scrollable | inner list position changes | page_scroll | page scroll no list change |
| GRAM-013 | search_replaced | search → type query → submit | query valid | results replaced | append expectation | old cards removed, new cards set |
| GRAM-014 | search_appended | load_more_results → scroll/click_more | load more available | new results appended | replace expectation | old cards remain plus new cards |
| GRAM-015 | prerequisite_option | add_to_cart → select_option → click_add | required option selected | cart_count += 1 | click_add_direct | option missing validation, add disabled |
| GRAM-016 | overlay_intercept | click_target → remove_or_accept_overlay → click_target | overlay intercepts pointer | target receives click after overlay removed | target_click_direct | click intercepted, z-index overlay |
| GRAM-017 | tabbed_navigation | edit_field → switch_tab → edit | target tab inactive | target fields visible in active tab | field_direct_edit | field absent in current tab |
| GRAM-018 | multi_step_wizard | complete_task → follow_step_order | current step valid | step_index increments | jump_to_final | future controls disabled/hidden |
| GRAM-019 | drag_drop_reorder | reorder → drag item to target slot | drag handle available | order changed | click_up_down | click no reorder, drag target active |
| GRAM-020 | delayed_validation | submit → wait_validation → fix_or_confirm | async validation completed | validation state appears then submit allowed | instant_submit | pending validation blocks progress |
| GRAM-021 | optimistic_rollback | save → wait_server_ack → retry/fix | server ack success | optimistic UI persists or rolls back | optimistic_success | state reverts after delay |

### 9.1 Regime Pair Comparison

| Regime Pair ID | Regime A | Regime B | Same Intent? | Different Executable Action? | Why This Tests Control Grammar |
| --- | --- | --- | --- | --- | --- |
| PAIR-001 | pagination | infinite_scroll | YES | YES | next_results intent가 click vs scroll로 갈린다 |
| PAIR-002 | direct_click | modal_blocked | YES | YES | target_click intent가 blocker removal macro를 요구한다 |
| PAIR-003 | direct_submit | form_invalid | YES | YES | submit intent가 fill_required macro를 요구한다 |
| PAIR-004 | immediate_click | loading_stale_dom | YES | YES | same click이 wait prerequisite를 요구한다 |
| PAIR-005 | top_nav | responsive_menu | YES | YES | navigate intent가 menu expansion을 요구한다 |
| PAIR-006 | visible_filter | hidden_filter | YES | YES | apply_filter intent가 panel open을 요구한다 |
| PAIR-007 | single_click_done | confirmation_flow | YES | YES | proceed intent가 confirm second action을 요구한다 |
| PAIR-008 | page_scroll | scroll_container_vs_page | YES | YES | find_more intent가 different scroll target을 요구한다 |
| PAIR-009 | search_replaced | search_appended | YES | YES | search/more intent의 expected effect schema가 다르다 |
| PAIR-010 | click_add_direct | prerequisite_option | YES | YES | add_to_cart intent가 option selection prerequisite를 요구한다 |
| PAIR-011 | field_direct_edit | tabbed_navigation | YES | YES | edit intent가 active tab switch를 요구한다 |
| PAIR-012 | instant_success | optimistic_rollback | YES | YES | save intent가 delayed confirmation/wait를 요구한다 |

## 10. Reveal-vs-Shift and Change-Point Engine

| Event ID | Event Type | Trigger | Hidden Update | Observable Evidence | Label Rule | Example |
| --- | --- | --- | --- | --- | --- | --- |
| EVT-001 | no-change | valid action but no UI/state change intended | none | DOM/visual unchanged, progress unchanged | no hidden update and no failure evidence | hover/focus ignored |
| EVT-002 | reveal | user expands hidden content | z_state observable subset increases | new controls appear, same regime/grammar | new visible nodes without grammar change | accordion open |
| EVT-003 | state transition | valid action changes task state | hidden_state progress changes | cart_count/result/filter changes | state variable update under same grammar | add item succeeds |
| EVT-004 | regime shift | UI interaction mode changes | hidden_regime changes | modal appears/disappears, loading starts | mode label changes | checkout opens confirmation modal |
| EVT-005 | control grammar shift | same intent now needs different executable action | hidden_control_grammar changes | button disabled until prerequisite | grammar id changes | option required after variant selection |
| EVT-006 | failed action | precondition violated or effect absent | failure flag true | no expected progress, error/no diff | invalid action under true grammar | click disabled submit |
| EVT-007 | delayed effect | effect occurs after wait | pending→resolved state | spinner then DOM update | effect delay within schedule | async validation |
| EVT-008 | noisy observation | observation differs without hidden change | observation noise only | minor visual/text jitter | hidden state/regime unchanged | ad/animation jitter |
| EVT-009 | blocker removed | overlay/modal/permission cleared | blocker state false | covered target becomes clickable | blocker removed label | cookie modal close |
| EVT-010 | validation state changed | form validity changes | validation flag update | error message/enabled button changes | validation label update | required field filled |

### 10.1 Change-Point Scheduling

| Schedule ID | Change Type | When It Occurs | Agent-Controllable? | Ground Truth Label | Risk |
| --- | --- | --- | --- | --- | --- |
| SCH-001 | agent-triggered reveal | after expand/filter/menu action | YES | reveal | 잘못 shift로 해석될 위험 |
| SCH-002 | agent-triggered regime shift | after click checkout/add requiring modal | YES | regime_shift | modal state leakage |
| SCH-003 | time-triggered loading resolve | after k wait/action ticks | PARTIAL | delayed_effect | wait shortcut |
| SCH-004 | hidden grammar shift after prerequisite | after option/login/permission state changes | YES | control_grammar_shift | precondition과 grammar 혼동 |
| SCH-005 | random overlay insertion | episode step sampled under split config | NO/PARTIAL | regime_shift | unfair stochasticity |
| SCH-006 | responsive layout switch | viewport sampled at reset or resize | NO | regime_shift | layout shortcut |
| SCH-007 | optimistic rollback | after save then delayed server response | NO/PARTIAL | delayed_effect/regime_shift | false falsification |
| SCH-008 | noisy observation interval | random visual jitter without state change | NO | noisy_observation | falsification false positive |

## 11. Action Space and Action Executor

| Action ID | Action Type | Arguments | Preconditions | Possible Effects | Failure Modes | Logged Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| ACT-001 | click | target_node_id/x,y | visible and pointer-receivable | route, open, submit, select | covered, disabled, stale target | pre/post DOM, covered_by, click result |
| ACT-002 | type | target_node_id,text | focusable input enabled | input value changes | target disabled, validation fail | input diff, validation |
| ACT-003 | select | select_node_id, option | select enabled, option exists | selected value changes | missing option, disabled | value diff |
| ACT-004 | scroll_page | delta | page scrollable | viewport moves, lazy content may load | no scroll, wrong container | scroll position, new nodes |
| ACT-005 | scroll_container | container_id, delta | container scrollable | inner list moves/loads | page scrolled instead | container scroll diff |
| ACT-006 | wait | duration/ticks | none | loading resolves, delayed effect appears | wasted compute | time, pending state diff |
| ACT-007 | close_modal | modal_id | modal active and closable | overlay removed | wrong modal, close absent | overlay state diff |
| ACT-008 | open_menu | menu_button_id | menu collapsed | menu items visible | wrong viewport, disabled | visible nodes |
| ACT-009 | submit_form | form_id | form valid and enabled | success/validation/errors | invalid form, delayed validation | validation/result state |
| ACT-010 | clear_input | input_id | input enabled | value empty | wrong field, disabled | input diff |
| ACT-011 | navigate_back | none | history exists | previous page | state loss, no history | url/page diff |
| ACT-012 | confirm | modal_id/button | confirmation active | confirmed transition | no modal, cancel needed | confirmation state |
| ACT-013 | cancel | modal_id/button | modal active | modal closed/no destructive action | wrong branch | modal state |
| ACT-014 | drag_drop | source_id,target_id | drag handle/target valid | order/location changes | drop rejected | order diff |
| ACT-015 | focus_blur | target_id | focusable element | validation or UI hint | no meaningful effect | focus/validation trace |

## 12. Counterfactual Alternative Effect Generator

이 논문 후보는 current-vs-alternative hypothesis rollout을 다루기 때문에, synthetic environment는 counterfactual action effect를 생성할 수 있어야 한다. 단, 이 table은 agent input이 아니다. 실제 Web/GUI에서는 counterfactual을 직접 알 수 없으므로, 이 table은 synthetic environment에서만 강한 supervision과 rollout fidelity 평가를 위해 사용한다.

```text
counterfactual table is hidden from the agent.
counterfactual table is used only for supervised signal, rollout fidelity evaluation, and oracle analysis.
```

| Counterfactual ID | Situation | Current Action Effect | Alternative Action Effect | Needed Label | Used By |
| --- | --- | --- | --- | --- | --- |
| CF-001 | modal covers filter button | click_filter → no_effect | close_modal → overlay_removed; click_filter next → filter_open | modal_blocked grammar | rollout fidelity/rewrite training |
| CF-002 | product requires size | click_add → validation_error | select_size → button_enabled; click_add → cart+1 | prerequisite_option | grammar selection |
| CF-003 | pagination absent but list scrollable | click_next → target_absent | scroll_container → cards_appended | infinite_scroll | current-vs-alt rollout |
| CF-004 | loading spinner active | click_result → stale_element | wait → loading_false; click_result → detail_open | loading_stale_dom | delay/falsification separation |
| CF-005 | collapsed filter panel | click_price_filter → target_absent | open_filter_panel → controls_visible | hidden_filter | reveal vs shift labeling |
| CF-006 | hamburger viewport | click_settings_topnav → target_absent | open_menu→click_settings → route_change | responsive_menu | layout OOD |
| CF-007 | permission prompt | click_download → blocked | accept_permission → permission_true; click_download succeeds | permission_required | blocker grammar |
| CF-008 | confirmation flow | click_delete → confirm_modal | confirm → item_deleted | confirmation_flow | single vs macro action |
| CF-009 | inner scroll list | scroll_page → no_new_rows | scroll_container → new_rows | scroll_container_vs_page | action argument grounding |
| CF-010 | search appends results | submit_search → cards_appended | clear_then_search → cards_replaced | search_appended | effect schema evaluation |
| CF-011 | tab inactive | type_field → target_absent | click_tab→type_field succeeds | tabbed_navigation | state vs grammar boundary |
| CF-012 | optimistic save rollback | click_save → temporary_success_then_revert | wait_ack_or_fix → stable_success | optimistic_rollback | delayed effect handling |

## 13. OOD Split Design

| Split ID | Split Name | What Changes | What Stays Fixed | Claim Tested | Failure Interpretation |
| --- | --- | --- | --- | --- | --- |
| SPLIT-001 | ID test | same task/template/regime family distribution | seed-disjoint episodes | basic mechanism fit | 낮으면 환경/모델 viability 실패 |
| SPLIT-002 | OOD-regime recombination | seen regimes appear in unseen order/combinations | individual regime definitions | composition generalization | sequence memorization |
| SPLIT-003 | OOD-control grammar shift | same visual layout but different precondition/effect grammar | task family/layout | grammar not visual shortcut | visual template shortcut 드러남 |
| SPLIT-004 | OOD-visual/layout perturbation | CSS, bbox, viewport, order changes | grammar/task semantics | visual robustness | bbox memorization |
| SPLIT-005 | OOD-DOM/text perturbation | tag nesting, text paraphrase, aria names | visual/grammar semantics | DOM/text shortcut 방지 | text shortcut |
| SPLIT-006 | OOD-task composition | seen subtasks in longer unseen workflows | regime library | long-horizon composition | short task overfit |
| SPLIT-007 | OOD-timing/asynchrony | delay, stale DOM, rollback probabilities | task/regime labels | noise vs falsification 분리 | false positive falsification |
| SPLIT-008 | OOD-reveal-vs-shift ambiguity | same observable expansion can be reveal or shift | surface UI form | event taxonomy validity | event label collapse |
| SPLIT-009 | OOD-unseen UI template | held-out page templates | grammar/task semantics | template generalization | template memorization |
| SPLIT-010 | OOD-long-horizon composition | more subgoals/change points | basic primitives | persistence/recovery over long horizon | planning compute failure |

## 14. Episode Generation Protocol

| Stage ID | Generation Stage | Input | Output | Randomized? | Controlled? | Risk |
| --- | --- | --- | --- | --- | --- | --- |
| GEN-001 | sample task family | split config, seed | task_family | YES | YES | task imbalance |
| GEN-002 | sample instruction | task family, paraphrase pool | natural language instruction | YES | YES | instruction shortcut |
| GEN-003 | sample subgoal graph | task template | subgoal DAG | YES | YES | too linear tasks |
| GEN-004 | sample UI template | task family, split | template id/pages | YES | YES | template leakage |
| GEN-005 | sample hidden regime | task/subgoal/state | regime schedule | YES | YES | task-regime 1:1 mapping |
| GEN-006 | sample control grammar | intent, regime | grammar id/schema | YES | YES | grammar leakage |
| GEN-007 | sample perturbation | split config | layout/text/timing perturbations | YES | YES | unbalanced OOD |
| GEN-008 | sample change-point schedule | regime/grammar config | event schedule | YES | YES | unfair stochasticity |
| GEN-009 | render DOM/screenshot | template,state,perturbation | DOM/a11y/screenshot/bbox | NO | YES | hidden labels in DOM |
| GEN-010 | execute agent action | action, pre-state | post-state/effect | NO | YES | non-deterministic action |
| GEN-011 | log action-effect | pre/post observations, labels | trace record | NO | YES | incomplete evidence |
| GEN-012 | compute progress/reward | subgoal graph, trace | progress_delta/reward | NO | YES | reward hacking |
| GEN-013 | export trace | episode metadata | jsonl/parquet/artifacts | NO | YES | schema drift |

## 15. Environment Trace Example

아래 예시는 Step 06의 final data schema가 아니다. 이 예시는 environment가 어떤 causal labels와 action-effect evidence를 생성해야 하는지 보여주는 illustrative trace다.

```json
{
  "episode_id": "webgui_ep_000742",
  "task_family": "add_to_cart_with_required_option",
  "instruction": "Add the blue medium hoodie to the cart.",
  "initial_page": "product_detail_page",
  "agent_observation": {
    "dom_summary": "Product detail page with color selector, size selector, Add to cart button, cart icon.",
    "screenshot_ref": "frames/webgui_ep_000742_t000.png",
    "visible_elements": ["Color: Blue", "Size dropdown", "Add to cart"]
  },
  "hidden_regime": "form_invalid",
  "hidden_control_grammar": "prerequisite_option_selection_before_add_to_cart",
  "current_hypothesis": {
    "regime": "direct_click",
    "control_grammar": "click_add_to_cart_directly"
  },
  "agent_wrong_action": {
    "type": "click",
    "target": "btn_add_cart"
  },
  "observed_failed_effect": {
    "cart_count_delta": 0,
    "dom_diff": ["validation_message_size_required_visible"],
    "visual_diff": "small validation message appears near size dropdown",
    "progress_delta": 0.0
  },
  "falsifying_evidence": "Expected cart_count += 1 under direct-click grammar, but observed validation error and no cart update.",
  "correct_alternative_hypothesis": {
    "regime": "form_invalid",
    "control_grammar": "select_required_option_then_click_add"
  },
  "recovery_action": [
    {"type": "select", "target": "size_dropdown", "value": "M"},
    {"type": "click", "target": "btn_add_cart"}
  ],
  "progress_update": {
    "cart_count_delta": 1,
    "subgoal_completed": true,
    "progress_delta": 0.35
  },
  "labels_generated": {
    "true_change_point": false,
    "event_type": "failed_action_then_valid_recovery",
    "wrong_control_grammar_persistence_steps": 1,
    "action_interface_switch_delay": 1,
    "reveal_vs_shift": "control_grammar_shift_required"
  }
}
```

이 예시에서 중요한 점은 agent가 `hidden_control_grammar`를 관측하지 않는다는 것이다. agent는 DOM/screenshot/action-effect evidence만 본다. hidden grammar는 metric, supervision, ablation, counterfactual analysis에만 사용된다.

## 16. Anti-Leakage and Shortcut Guardrails

| Guardrail ID | Leakage/Shortcut Risk | Detection Method | Guardrail | Later Validation |
| --- | --- | --- | --- | --- |
| GL-001 | hidden regime in DOM class names | grep/classifier probes | class/data attributes use neutral ids only | Step 06 leakage tests |
| GL-002 | hidden grammar in text labels | text probe accuracy | no label-like words in visible text/aria | Step 06 |
| GL-003 | template memorization | train/test template classifier | held-out template split and randomized layout | Step 10 |
| GL-004 | task-to-regime shortcut | mutual information test | balanced regimes per task family | Step 06 |
| GL-005 | layout-to-grammar shortcut | layout-only classifier | layout randomization and same-layout/different-grammar split | Step 10 |
| GL-006 | counterfactual table leakage | observation sanitizer test | counterfactual stored only in hidden trace | Step 06 |
| GL-007 | evidence too explicit | reason-string ablation | raw diff/weak summary levels; no “because grammar” string | Step 06 |
| GL-008 | no-effect always wrong grammar | conditional distribution test | include benign no-change/noisy/no-op cases | Step 10 |
| GL-009 | loading confused with falsification | delay-label calibration | separate delayed effect/noisy observation/event labels | Step 08 |
| GL-010 | visible disabled shortcut | disabled-only classifier | valid grammar with disabled and invalid grammar without disabled examples | Step 10 |
| GL-011 | aria leakage | a11y snapshot sanitizer | remove synthetic diagnostic names | Step 06 |
| GL-012 | button text shortcut | text paraphrasing probe | paraphrase and decoy button labels | Step 06 |
| GL-013 | seed leakage | episode id hash audit | split-independent seed namespaces | Step 06 |
| GL-014 | OOD not truly OOD | distance/metadata audit | explicit held-out dimensions | Step 10 |
| GL-015 | reward hidden-label leakage | reward decomposition audit | reward tied to progress/effect, not label prediction alone | Step 08 |
| GL-016 | visual modality unnecessary | DOM-only vs visual ablation | visual-specific tasks/overlays/layout ambiguity | Step 10 |
| GL-017 | modal/form dominance | regime distribution audit | minimum per-regime counts and entropy threshold | Step 06 |
| GL-018 | long horizon fake composition | subgoal dependency audit | non-commutative subgoal dependencies | Step 05/10 |
| GL-019 | oracle upper bound uninterpretable | oracle diagnostics | calibrate oracle grammar with same action space constraints | Step 10 |
| GL-020 | real benchmark label gap | external validation plan | treat real benchmarks as auxiliary, not proof of mechanism | FINAL/Step10 |
| GL-021 | DOM-only too easy | modality ablation | construct cases requiring visual overlay/bbox evidence | Step 10 |

## 17. Stress Test Ledger

| Stress ID | Attack | Why Dangerous | Detection Method | Required Guardrail | Later Step |
| --- | --- | --- | --- | --- | --- |
| STRESS-05-001 | hidden regime이 DOM class에 새는가? | agent가 label을 직접 읽으면 실험 붕괴 | DOM text/class probe | GL-001 | Step 06 |
| STRESS-05-002 | grammar label이 button text에 반영되는가? | text shortcut | text-only classifier | GL-002/012 | Step 06 |
| STRESS-05-003 | task family만 보고 regime을 맞추는가? | task-regime shortcut | MI/task-only probe | GL-004 | Step 06 |
| STRESS-05-004 | layout만 보고 grammar를 맞추는가? | layout shortcut | layout-only visual probe | GL-005 | Step 10 |
| STRESS-05-005 | template 반복이 심한가? | template memorization | template classifier | GL-003 | Step 10 |
| STRESS-05-006 | OOD split이 train과 너무 비슷한가? | generalization 허위 | split distance audit | GL-014 | Step 10 |
| STRESS-05-007 | screenshot 없어도 모든 task가 풀리는가? | visual claim 약화 | DOM-only ablation | GL-016/021 | Step 10 |
| STRESS-05-008 | DOM만으로 너무 쉽게 풀리는가? | visual/interaction 약화 | DOM-only high score check | GL-021 | Step 10 |
| STRESS-05-009 | action-effect evidence 없이 grammar를 맞추는가? | evidence mechanism 무의미 | no-history/evidence ablation | GL-004/005 | Step 10 |
| STRESS-05-010 | reward가 hidden label 맞추기로 새는가? | reward hacking | reward-feature audit | GL-015 | Step 08 |
| STRESS-05-011 | counterfactual effect table이 agent input에 새는가? | oracle leakage | observation schema audit | GL-006 | Step 06 |
| STRESS-05-012 | failed evidence가 너무 명시적인가? | 문장 shortcut | reason-string ablation | GL-007 | Step 06 |
| STRESS-05-013 | no-effect가 항상 wrong grammar인가? | false shortcut | no-effect distribution audit | GL-008 | Step 10 |
| STRESS-05-014 | loading/noise를 falsification으로 오판하는가? | false positive falsification | delayed/noisy stress split | GL-009 | Step 10 |
| STRESS-05-015 | modal/form/loading만 많지 않은가? | taxonomy coverage 부족 | regime entropy audit | GL-017 | Step 06 |
| STRESS-05-016 | long-horizon이 short task 조합뿐인가? | planning claim 약화 | subgoal dependency test | GL-018 | Step 10 |
| STRESS-05-017 | random seed가 split leakage를 만드는가? | 재현성/오염 | seed namespace audit | GL-013 | Step 06 |
| STRESS-05-018 | UI text distribution으로 split을 맞추는가? | text shortcut | language-model probe | GL-012 | Step 06 |
| STRESS-05-019 | oracle upper bound가 비정상인가? | 해석 불가 | oracle run sanity | GL-019 | Step 10 |
| STRESS-05-020 | real benchmark로 확장 시 label이 사라지는가? | external validity 약화 | aux eval plan | GL-020 | Step 10 |

## 18. What This Environment Cannot Prove

| Limitation ID | Limitation | Why It Matters | Must Be Handled In | Risk If Ignored |
| --- | --- | --- | --- | --- |
| LIMIT-05-001 | real website diversity | 실제 사이트의 디자인/상태/계정 흐름은 더 다양하다 | Step 10 auxiliary benchmark | synthetic 성공을 과장 |
| LIMIT-05-002 | true open-world UI distribution | procedural generator가 현실 분포를 완전히 포착하지 못한다 | FINAL/Step10 | generalization 과장 |
| LIMIT-05-003 | uncontrolled user accounts/session states | 로그인/권한/개인화 상태는 실제로 더 복잡하다 | Step 10 | permission grammar 과소평가 |
| LIMIT-05-004 | third-party latency/network variance | 외부 API/네트워크 지연은 통제된 delay와 다르다 | Step 05 stress/Step10 | timing robustness 과장 |
| LIMIT-05-005 | natural webpage visual complexity | 광고/팝업/반응형 CSS 복잡도가 제한된다 | Step 10 VisualWebArena | visual realism 부족 |
| LIMIT-05-006 | real browser security restrictions | CORS/다운로드/파일 권한 등 실제 제약 미반영 | Step 10 OSWorld | computer-use transfer 약화 |
| LIMIT-05-007 | real-world counterfactual unobservability | 실제 환경에서는 alternative effect oracle을 알 수 없다 | Step 09/10 | counterfactual supervision 과장 |
| LIMIT-05-008 | real user instruction ambiguity | 사용자 지시문은 더 모호하고 개인화된다 | Step 10 | instruction understanding claim 제한 |
| LIMIT-05-009 | large-scale benchmark comparability | custom synthetic 환경은 외부 leaderboard와 직접 비교 어려움 | Step 10 | benchmark acceptability 약화 |
| LIMIT-05-010 | long-term deployment reliability | 장기 세션, memory, user preference 변화 미검증 | FINAL | deployment claim 금지 |

## 19. Required Design Revisions From Environment Design

| Revision ID | Environment Issue | Required Revision | Affected Later Step | Severity |
| --- | --- | --- | --- | --- |
| REV-05-001 | hidden label leakage 위험 | hidden labels를 agent observation과 완전히 분리하는 schema sanitizer 필요 | 06_DATA_SCHEMA_AND_LABELING.md | CRITICAL |
| REV-05-002 | counterfactual oracle 현실성 위험 | counterfactual table은 synthetic supervision/eval 전용으로 명시 | 06/09/10 | CRITICAL |
| REV-05-003 | DOM-only shortcut 위험 | screenshot/overlay/bbox가 필요한 task subset과 modality ablation 추가 | 10_EVALUATION_BASELINE_ABLATION.md | HIGH |
| REV-05-004 | no-effect shortcut 위험 | benign no-change/noisy/delayed effect를 별도 event로 포함 | 06/08/10 | HIGH |
| REV-05-005 | task-regime 1:1 shortcut | 모든 task family에 최소 2개 이상 regime variation 강제 | 06_DATA_SCHEMA_AND_LABELING.md | CRITICAL |
| REV-05-006 | grammar vs precondition collapse | grammar를 mapping+precondition+effect schema로 저장 | 06/07 | CRITICAL |
| REV-05-007 | toy template 공격 | held-out template/OOD-long-horizon split 필수 | 10_EVALUATION_BASELINE_ABLATION.md | HIGH |
| REV-05-008 | loading과 falsification 혼동 | delayed effect/noisy observation label과 falsification rule 분리 | 08/09 | HIGH |
| REV-05-009 | real benchmark label gap | real benchmark는 mechanism proof가 아니라 auxiliary external validity로 위치 지정 | 10/FINAL | MEDIUM |
| REV-05-010 | reward hacking 위험 | reward는 hidden label match가 아니라 progress/effect/recovery 조건에 연결 | 08_LOSS_REWARD_TRAINING_OBJECTIVE.md | CRITICAL |
| REV-05-011 | oracle upper bound 해석 위험 | oracle에도 동일 action space/observation constraint를 적용 | 10_EVALUATION_BASELINE_ABLATION.md | MEDIUM |

## 20. Handoff to Later Steps

| Handoff ID | Target Step | What Must Be Used | What Must Be Verified | What Must Not Be Assumed |
| --- | --- | --- | --- | --- |
| HANDOFF-05-001 | 06_DATA_SCHEMA_AND_LABELING.md | observation fields, hidden label rules, trace fields, anti-leakage guardrails | schema sanitizer, label provenance, split metadata | dataset schema가 이미 확정됐다고 가정 금지 |
| HANDOFF-05-002 | 07_LATENT_ARCHITECTURE_DESIGN.md | hidden_state/regime/control_grammar/change labels, observation space | which labels map to latent vs auxiliary heads | latent identifiability가 해결됐다고 가정 금지 |
| HANDOFF-05-003 | 08_LOSS_REWARD_TRAINING_OBJECTIVE.md | event labels, progress/reward components, counterfactual effects | reward hacking guardrails, loss-label mapping | reward/loss가 최종 검증됐다고 가정 금지 |
| HANDOFF-05-004 | 09_PLANNING_THEORY_ALGORITHM.md | current/alternative hypothesis fields, counterfactual effects, action executor | falsification likelihood ratio and decision relevance gate | algorithm novelty가 확정됐다고 가정 금지 |
| HANDOFF-05-005 | 10_EVALUATION_BASELINE_ABLATION.md | OOD splits, metrics, stress tests, baselines threat | compute-matched baselines and leakage probes | synthetic success가 real benchmark success라고 가정 금지 |

## 21. Updated Risk / Unknown Ledger

| Risk ID | Risk / Unknown | Triggered By | Why It Matters | Resolution Path | Can Be Final Claim? |
| --- | --- | --- | --- | --- | --- |
| RISK-05-001 | hidden regime/control grammar label leakage | DOM/a11y/text fields | agent가 labels를 읽으면 metric 무의미 | schema sanitizer + leakage probes | NO |
| RISK-05-002 | synthetic toy shortcut | template/task/regime shortcuts | reviewer가 toy benchmark로 공격 | OOD + randomization + stress tests | NO |
| RISK-05-003 | counterfactual table 현실성 | synthetic oracle only | real Web에서는 unavailable | synthetic-only supervision으로 제한 | NO |
| RISK-05-004 | DOM-only overfitting | DOM tree rich observation | visual contribution 약화 | modality ablation 및 visual-specific cases | NO |
| RISK-05-005 | visual-only shortcut | layout/bbox fixed | grammar를 visual pattern으로 외움 | layout randomization | NO |
| RISK-05-006 | no-effect shortcut | failed action evidence | no-effect=wrong grammar로 과적합 | benign no-change/noisy/delayed cases | NO |
| RISK-05-007 | loading/falsification confusion | async UI behavior | false falsification 증가 | delay/noise event labels | NO |
| RISK-05-008 | task-regime imbalance | generator prior | task family만 보고 regime 예측 | balanced sampling | NO |
| RISK-05-009 | grammar taxonomy arbitrariness | human-defined grammar ids | 말장난 공격 | same intent/different action pair로 operationalize | NO |
| RISK-05-010 | real benchmark transfer gap | custom synthetic env | external validity 부족 | WebArena/VisualWebArena/OSWorld auxiliary | NO |
| RISK-05-011 | long-horizon 부족 | short task templates | planning claim 약화 | OOD-long-horizon composition | NO |
| RISK-05-012 | reward hacking | switch/recovery reward | 무의미한 switching 유도 | progress-linked switch reward | NO |
| RISK-05-013 | oracle upper bound miscalibration | oracle grammar model | gap 해석 어려움 | same action constraints | NO |
| RISK-05-014 | trace overhead | Playwright-style logging | scale/latency 문제 | trace compression/sampling | NO |
| RISK-05-015 | environment nondeterminism | browser async effects | 재현성 저하 | seed/version manager | NO |

## 22. Quality Gate Result

| Gate ID | Gate | PASS/FAIL/PARTIAL | Evidence | If Not PASS, Blocker |
| --- | --- | --- | --- | --- |
| QG-05-01 | 00/01/02/03/04 refs imported | PASS | Imported References 60개 이상 포함 | - |
| QG-05-02 | search expansion 25개 이상 수행 | PASS | Search Ledger 25개 작성 | - |
| QG-05-03 | environment architecture component 20개 이상 정의 | PASS | 22개 component 작성 | - |
| QG-05-04 | observation space 20개 이상 정의 | PASS | 22개 observation item 작성 | - |
| QG-05-05 | task family 12개 이상 설계 | PASS | 15개 task family 작성 | - |
| QG-05-06 | UI template 10개 이상 설계 | PASS | 12개 template 작성 | - |
| QG-05-07 | regime/control grammar 20개 이상 설계 | PASS | 21개 grammar 작성 | - |
| QG-05-08 | reveal-vs-shift/change-point engine 설계 | PASS | 10개 event + 8개 schedule 작성 | - |
| QG-05-09 | action executor 15개 이상 설계 | PASS | 15개 action type 작성 | - |
| QG-05-10 | counterfactual alternative effect generator 설계 | PASS | 12개 counterfactual situation 작성 | - |
| QG-05-11 | OOD split 10개 이상 설계 | PASS | 10개 split 작성 | - |
| QG-05-12 | anti-leakage guardrail 20개 이상 작성 | PASS | 21개 guardrail 작성 | - |
| QG-05-13 | environment limitation 10개 이상 작성 | PASS | 10개 limitation 작성 | - |
| QG-05-14 | no final dataset schema/model/evaluation prematurely accepted | PASS | front matter와 각 섹션에서 Step 06/07/08/10으로 넘김 | - |


## 22.1 Claude Code Implementation Checklist

Claude Code가 이 파일을 기반으로 실제 환경 코드를 작성하거나 Step 06 schema를 생성할 때, 아래 항목을 모두 체크해야 한다.

| Checklist ID | Check | Pass Condition | Blocker If Fail |
|---|---|---|---|
| CC-05-001 | agent observation sanitizer | forbidden hidden/counterfactual keys에 대한 assertion 존재 | hidden label leakage |
| CC-05-002 | same-intent/different-action pair | 최소 12개 pair가 environment generator에서 생성 가능 | control grammar operational proof 부족 |
| CC-05-003 | no-effect taxonomy | no-change, failed action, delayed effect, noisy observation이 분리됨 | falsification false positive |
| CC-05-004 | counterfactual isolation | counterfactual table은 trace metadata에만 존재 | oracle leakage |
| CC-05-005 | OOD split reproducibility | split id, seed, held-out factor가 trace에 기록됨 | OOD 재현 불가 |
| CC-05-006 | action executor evidence | each step logs pre/post DOM hash, screenshot ref, a11y ref, effect type | metric 계산 불가 |
| CC-05-007 | visual-specific cases | screenshot/bbox 없이는 풀기 어려운 overlay/layout cases 존재 | visual modality claim 약화 |
| CC-05-008 | DOM-only cases | screenshot 없이도 풀 수 있는 structured state cases 존재 | modality confound |
| CC-05-009 | loading/delayed cases | wait action이 필요한 delayed effect cases 존재 | timing robustness 부재 |
| CC-05-010 | direct-threat baseline support | verifier-only, next-state-WM, always-plan, uncertainty-gate를 재현할 trace fields 존재 | Step 10 baseline 불가 |

## 22.2 File-Level Delta From v0.1

| Delta ID | Added / Strengthened | Why It Raises Quality |
|---|---|---|
| DELTA-05-001 | Claude Code Context Routing 추가 | 필요한 파일과 섹션을 확장적으로 읽을 수 있음 |
| DELTA-05-002 | Citation-grade source anchors 추가 | MiniWoB++, WebArena, VisualWebArena, OSWorld, WorkArena, BrowserGym, Playwright, WebWorld/WAC/CUWM/VeriGUI의 위치가 명확해짐 |
| DELTA-05-003 | Implementation-ready repository/API contract 추가 | 바로 코드화할 수 있는 최소 실행 구조를 제공 |
| DELTA-05-004 | Runtime assertion 예시 추가 | hidden label leakage를 코드 레벨에서 차단 |
| DELTA-05-005 | Minimum viable experiment scope 추가 | 구현 우선순위를 text-only 이후 Web/GUI MVE로 압축 가능 |
| DELTA-05-006 | Environment-to-claim contract 추가 | 환경 컴포넌트가 논문 claim/metric/baseline과 직접 연결됨 |
| DELTA-05-007 | Claude Code implementation checklist 추가 | 후속 구현/검토 시 누락을 자동 점검 가능 |

## 23. Final Statement of This File

```text
05_SYNTHETIC_WEB_GUI_ENVIRONMENT.md is an environment design file, not a final dataset schema or model method.

The synthetic Web/GUI environment is intended to validate:
- wrong-control-grammar hypothesis persistence를 hidden regime/control grammar ground truth로 계량할 수 있는가.
- action-effect evidence가 current hypothesis를 반증하고, alternative grammar rewrite가 실제 progress를 만드는가.
- always-plan, uncertainty-gate, verifier-only, next-state-WM-only와 구분되는 mechanism 평가가 가능한가.

The strongest anti-toy guardrails are:
- hidden labels and counterfactual effects are never exposed to the agent.
- task-family/regime/template/layout/text shortcuts are tested by leakage probes and OOD splits.
- no-effect, loading, noisy observation, benign no-change are separated from wrong grammar falsification.

The environment still cannot prove:
- real open-world website diversity and uncontrolled session/account state robustness.
- real-world counterfactual effects, because those are unobservable outside synthetic environment.
- final benchmark-level generalization without WebArena/VisualWebArena/OSWorld/WorkArena auxiliary validation.

The next required file is:
06_DATA_SCHEMA_AND_LABELING.md
```
