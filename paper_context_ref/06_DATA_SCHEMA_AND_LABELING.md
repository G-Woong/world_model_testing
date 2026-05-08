# 06_DATA_SCHEMA_AND_LABELING.md

---
file_id: STEP-06
title: Data Schema and Labeling Contract for FRCG-WM
version: v1.0
status: schema_contract_implementation_ready_context
depends_on:
  - 00_MASTER_REFERENCE.md
  - 01_RELATED_WORK_THREAT_MAP.md
  - 02_PROBLEM_NOVELTY_FALSIFICATION.md
  - 03_CORE_CONCEPT_TAXONOMY.md
  - 04_TEXT_ONLY_SMOKE_TESTBED.md
  - 05_SYNTHETIC_WEB_GUI_ENVIRONMENT.md
purpose:
  - Define the data schema, label generation rules, trace format, counterfactual records, split/versioning metadata, and leakage guardrails for FRCG-WM experiments.
  - Separate agent observations from hidden labels, training supervision, evaluation-only fields, counterfactual-only fields, and audit metadata.
  - Provide a data contract for later architecture, loss/reward, planning, and evaluation steps.
forbidden:
  - Do not finalize model architecture.
  - Do not finalize training objective.
  - Do not finalize evaluation results.
  - Do not provide hidden labels as agent observations.
next_files:
  - 07_LATENT_ARCHITECTURE_DESIGN.md
  - 08_LOSS_REWARD_TRAINING_OBJECTIVE.md
  - 09_PLANNING_THEORY_ALGORITHM.md
  - 10_EVALUATION_BASELINE_ABLATION.md
---

## 0. Claude Code Context Routing

이 파일은 Claude Code가 `FRCG-WM` 프로젝트에서 dataset/schema/labeling 관련 작업을 할 때 가장 먼저 읽어야 하는 계약 파일이다. 단, 이 파일만으로 model architecture, loss, planner, evaluation을 구현하면 안 된다. Claude Code는 아래 routing을 따라 필요한 context를 확장적으로 읽어야 한다.

| User Intent / Task | Must Read First | Then Read | Must Not Assume |
|---|---|---|---|
| agent observation builder 구현 | `06_DATA_SCHEMA_AND_LABELING.md` §4, §5, §7, §14 | `05_SYNTHETIC_WEB_GUI_ENVIRONMENT.md`, `07_LATENT_ARCHITECTURE_DESIGN.md` | hidden labels가 public observation에 포함되어도 된다고 가정 금지 |
| hidden label schema 수정 | `06_DATA_SCHEMA_AND_LABELING.md` §4, §5.9, §8 | `03_CORE_CONCEPT_TAXONOMY.md`, `05_SYNTHETIC_WEB_GUI_ENVIRONMENT.md` | `true_regime`과 `true_control_grammar`가 같은 의미라고 가정 금지 |
| action-effect logger 구현 | `06_DATA_SCHEMA_AND_LABELING.md` §9 | `05_SYNTHETIC_WEB_GUI_ENVIRONMENT.md`, `09_PLANNING_THEORY_ALGORITHM.md` | `no_effect`가 항상 wrong grammar를 뜻한다고 가정 금지 |
| counterfactual shard 구현 | `06_DATA_SCHEMA_AND_LABELING.md` §10 | `05_SYNTHETIC_WEB_GUI_ENVIRONMENT.md`, `09_PLANNING_THEORY_ALGORITHM.md` | counterfactual table을 agent input으로 제공 금지 |
| loss/objective 데이터 연결 | `06_DATA_SCHEMA_AND_LABELING.md` §8~§12 | `08_LOSS_REWARD_TRAINING_OBJECTIVE.md`, `07_LATENT_ARCHITECTURE_DESIGN.md` | label이 inference input으로도 쓰인다고 가정 금지 |
| evaluation metric 계산 | `06_DATA_SCHEMA_AND_LABELING.md` §12, §13, §14 | `10_EVALUATION_BASELINE_ABLATION.md` | success rate만으로 claim 검증 금지 |
| leakage audit 작성 | `06_DATA_SCHEMA_AND_LABELING.md` §4, §7, §14, §15 | `05_SYNTHETIC_WEB_GUI_ENVIRONMENT.md`, `10_EVALUATION_BASELINE_ABLATION.md` | sanitizer 없이 trace를 prompt에 넣지 말 것 |
| dataset card/appendix 작성 | `06_DATA_SCHEMA_AND_LABELING.md` §16, §19, §20 | `10_EVALUATION_BASELINE_ABLATION.md`, `FINAL_RESEARCH_BLUEPRINT.md` | synthetic counterfactual label을 real-world에도 있다고 주장 금지 |

---

## 0.1 10점 고도화 기준

이 파일은 다음 네 기준을 모두 만족해야 한다.

| Criterion | Required Level | Concrete Requirement |
|---|---:|---|
| 내용 수준 | 10/10 | hidden label, public observation, counterfactual, reward/progress, metric-support, audit metadata가 분리되어야 한다. |
| 논문 아이디어 고도화 | 10/10 | `wrong-control-grammar persistence`가 실제로 계산 가능한 field chain으로 연결되어야 한다. |
| Claude Code context 적합성 | 10/10 | 어떤 작업에서 어느 섹션을 읽어야 하는지 routing이 존재해야 한다. |
| 바로 구현 가능한 실험 명세 | 10/10 | `build_agent_observation`, `validate_no_leakage`, `metric field dependency`, `MVE schema subset`이 존재해야 한다. |

---

## 0.2 Citation-Grade Source Anchor Ledger

이 표는 schema와 logging 설계가 완전히 임의적인 것이 아님을 보이기 위한 source anchor다. 이 파일은 논문 Related Work가 아니므로, 최종 인용 문장은 `01_RELATED_WORK_THREAT_MAP.md`와 `FINAL_RESEARCH_BLUEPRINT.md`에서 다시 정제해야 한다.

| Anchor ID | Source / Tool / Paper | Stable URL | What It Supports | How It Is Used Here |
|---|---|---|---|---|
| SRC-SCHEMA-001 | BrowserGym Ecosystem for Web Agent Research | https://arxiv.org/abs/2412.05467 | web agent benchmark의 gym-like observation/action/evaluation 표준화 | agent observation/action trace schema의 외부 anchor |
| SRC-SCHEMA-002 | BrowserGym Documentation | https://browsergym.readthedocs.io/ | Chromium 기반 web task automation env | `reset/step/close`, environment wrapper 설계 참고 |
| SRC-SCHEMA-003 | RLDS: an Ecosystem to Generate, Share and Use Datasets in Reinforcement Learning | https://arxiv.org/abs/2111.02767 | episode/step 기반 sequential decision dataset 저장 | hierarchical dataset schema의 외부 anchor |
| SRC-SCHEMA-004 | Google Research RLDS blog | https://research.google/blog/rlds-an-ecosystem-to-generate-share-and-use-datasets-in-reinforcement-learning/ | RL trajectory recording/replay/manipulation | dataset-level/episode-level/step-level record 분리 참고 |
| SRC-SCHEMA-005 | Playwright | https://playwright.dev/ | Chromium/Firefox/WebKit 자동화와 testing/agent workflow 지원 | browser action executor 및 trace collection 구현 anchor |
| SRC-SCHEMA-006 | Playwright Trace Viewer | https://playwright.dev/docs/trace-viewer | action별 trace, screenshot, DOM/event timeline | action-effect logger와 screenshot/trace artifact 설계 참고 |
| SRC-SCHEMA-007 | Chrome DevTools Protocol DOMSnapshot | https://chromedevtools.github.io/devtools-protocol/tot/DOMSnapshot/ | DOM/layout/style snapshot capture | `dom_snapshot`, `layout`, `bbox` field 설계 참고 |
| SRC-SCHEMA-008 | Chrome DevTools Protocol Accessibility | https://chromedevtools.github.io/devtools-protocol/tot/Accessibility/ | full/partial accessibility tree retrieval | `accessibility_tree_sanitized` 설계 참고 |
| SRC-SCHEMA-009 | Chrome DevTools Accessibility Tree Reference | https://developer.chrome.com/docs/devtools/accessibility/reference | AX tree는 DOM 중 screen reader에 유용한 subset | DOM/AX mismatch audit 필요성 근거 |
| SRC-SCHEMA-010 | Datasheets for Datasets | https://arxiv.org/abs/1803.09010 | dataset motivation/composition/collection/uses/limitations 문서화 | dataset card/documentation 요구사항 anchor |
| SRC-SCHEMA-011 | D4RL | https://arxiv.org/abs/2004.07219 | offline RL dataset benchmark와 normalized evaluation | logged trajectory/evaluation split 참고 |

---

## 0.3 Global Field Naming Contract

아래 naming rule은 이후 code implementation에서 반드시 지켜야 한다.

| Prefix / Field Family | Meaning | Allowed Bucket | Forbidden Use |
|---|---|---|---|
| `public_*` | agent가 볼 수 있는 필드 | `AGENT_OBSERVATION` | hidden/eval-only 값을 포함 금지 |
| `true_*` | simulator ground-truth label | `TRAINING_SUPERVISION`, `EVALUATION_ONLY` | agent observation 금지 |
| `counterfactual_*` | 실행하지 않은 alternative action effect oracle | `COUNTERFACTUAL_ONLY` | prompt/input/dataloader public view 금지 |
| `oracle_*` | upper bound action/grammar/regime label | `EVALUATION_ONLY`, `COUNTERFACTUAL_ONLY` | training input으로 직접 주입 금지 |
| `audit_*` / `leakage_*` | 검증/재현성/누수검사 metadata | `AUDIT_METADATA` | agent observation 금지 |
| `*_sanitized` | public-safe sanitizer 통과 필드 | `AGENT_OBSERVATION` 가능 | sanitizer 미통과 raw field와 혼합 금지 |
| `*_raw` | raw trace artifact | `AUDIT_METADATA` 또는 storage-only | agent observation 금지 |

Implementation rule:

```text
Claude Code가 dataset loader를 만들 때는 반드시 두 개의 view를 분리해야 한다.
1. storage view: hidden/counterfactual/audit를 포함하는 full record
2. agent view: build_agent_observation()이 반환하는 sanitized public observation
```

---

## 0.4 Minimal Viable Experiment Schema Subset

초기 구현은 전체 schema를 한 번에 만들지 말고, 아래 MVE subset부터 구현한다.

| MVE Field | Required? | Why First |
|---|---:|---|
| `episode_id` | YES | trace grouping |
| `step_id` | YES | temporal metric |
| `public_instruction` | YES | base agent input |
| `dom_tree_sanitized` | YES | minimal structured observation |
| `previous_action_public` | YES_AFTER_STEP0 | action-effect history |
| `observed_effect_public` | YES_AFTER_STEP0 | falsification evidence public view |
| `true_regime` | YES_HIDDEN | regime supervision/eval |
| `true_control_grammar` | YES_HIDDEN | core grammar supervision/eval |
| `executed_hypothesis` | YES_EVAL | persistence metric |
| `true_wrong_hypothesis` | YES_LABEL | falsification target |
| `true_action_effect_type` | YES_LABEL | action-effect loss |
| `true_progress_delta` | YES_LABEL | progress/reward objective |
| `counterfactual_action_effects` | YES_COUNTERFACTUAL | rollout fidelity |
| `reward_components` | YES_LABEL | objective/eval |
| `leakage_check_flags` | YES_AUDIT | dataset validity |

MVE gate:

```text
위 필드 없이 07/08/09/10 단계 구현을 시작하면 안 된다.
```

---


## 1. File Purpose

이 파일은 model method가 아니라 **FRCG-WM 실험 전체의 data contract**다. 목적은 JSON을 예쁘게 만드는 것이 아니라, 이후 architecture, loss, reward, planning, evaluation이 같은 데이터 의미를 공유하도록 **observation, hidden label, training supervision, evaluation-only label, counterfactual-only label, audit metadata**를 분리하는 것이다.

핵심 규칙은 다음이다.

1. `true_regime`, `true_control_grammar`, `true_change_point`, `true_reveal_vs_shift`, `counterfactual_action_effects`는 agent observation에 절대 포함하지 않는다.
2. agent가 보는 public observation과 학습/평가/감사용 record는 같은 episode 안에 저장되더라도 추출 경로를 분리한다.
3. action-effect evidence는 falsification, metric, loss, reward를 모두 연결하는 중심 record다.
4. counterfactual label은 synthetic environment의 강점이지만 실제 Web/GUI에서는 직접 관측 불가능하므로, synthetic-only supervision이라는 한계를 명시한다.
5. schema가 흔들리면 `wrong-control-grammar persistence`, `alternative rollout fidelity`, `recovery delay`, `compute-matched return` 같은 핵심 metric이 전부 무효가 된다.

## 2. Imported References


| Imported ID | Source File | Type | Meaning | Why It Matters | Priority |
| --- | --- | --- | --- | --- | --- |
| REF-CORE-001 | 00_MASTER_REFERENCE.md | core thesis | wrong-control-grammar hypothesis persistence | persistence label과 metric 정의의 중심 | CRITICAL |
| REF-CORE-002 | 00_MASTER_REFERENCE.md | core thesis | latent regime/control-grammar world model | hidden label과 supervision 분리 필요 | CRITICAL |
| REF-CORE-003 | 00_MASTER_REFERENCE.md | core thesis | action-effect evidence 기반 falsification | per-step evidence schema 필요 | CRITICAL |
| REF-CORE-004 | 00_MASTER_REFERENCE.md | core thesis | current-vs-alternative hypothesis rollout | counterfactual record 필요 | CRITICAL |
| REF-CORE-005 | 00_MASTER_REFERENCE.md | core thesis | intent-to-action rewrite | rewritten action trace 필요 | CRITICAL |
| REF-CORE-006 | 00_MASTER_REFERENCE.md | core thesis | decision-relevant compute reallocation | compute field와 cost label 필요 | HIGH |
| REF-CORE-007 | 00_MASTER_REFERENCE.md | core thesis | Frozen Base VLM/LLM + proposed module | base input과 module label 분리 필요 | HIGH |
| REF-CORE-009 | 00_MASTER_REFERENCE.md | core thesis | synthetic Web/GUI controlled environment | hidden causal label 저장 필요 | CRITICAL |
| REF-PROBLEM-001 | 00_MASTER_REFERENCE.md | problem | 반복 실패는 단순 action failure가 아닐 수 있음 | failed action과 wrong grammar label 분리 | CRITICAL |
| REF-PROBLEM-002 | 00_MASTER_REFERENCE.md | problem | visual grounding과 grammar failure 분리 | bbox/screenshot과 hidden grammar 분리 | HIGH |
| REF-PROBLEM-003 | 00_MASTER_REFERENCE.md | problem | planning failure와 grammar mapping failure 분리 | intent/subgoal/action mapping record 필요 | CRITICAL |
| REF-PROBLEM-004 | 00_MASTER_REFERENCE.md | problem | verification failure와 falsification 분리 | verification outcome과 posterior update record 분리 | CRITICAL |
| REF-CONCEPT-001 | 00_MASTER_REFERENCE.md | concept | state | hidden_state schema 필요 | CRITICAL |
| REF-CONCEPT-002 | 00_MASTER_REFERENCE.md | concept | regime | true_regime label 필요 | CRITICAL |
| REF-CONCEPT-003 | 00_MASTER_REFERENCE.md | concept | control grammar | true_control_grammar label 필요 | CRITICAL |
| REF-CONCEPT-004 | 00_MASTER_REFERENCE.md | concept | change-point | true_change_point label 필요 | HIGH |
| REF-CONCEPT-005 | 00_MASTER_REFERENCE.md | concept | reveal | true_reveal_vs_shift label 필요 | HIGH |
| REF-CONCEPT-006 | 00_MASTER_REFERENCE.md | concept | shift | regime/grammar shift event label 필요 | HIGH |
| REF-CONCEPT-007 | 00_MASTER_REFERENCE.md | concept | current hypothesis | executed_hypothesis record 필요 | CRITICAL |
| REF-CONCEPT-008 | 00_MASTER_REFERENCE.md | concept | alternative hypothesis | top-k alternative record 필요 | CRITICAL |
| REF-CONCEPT-009 | 00_MASTER_REFERENCE.md | concept | falsification evidence | evidence strength field 필요 | CRITICAL |
| REF-CONCEPT-010 | 00_MASTER_REFERENCE.md | concept | action-interface rewrite | rewrite action field 필요 | HIGH |
| REF-CONCEPT-011 | 00_MASTER_REFERENCE.md | concept | decision-relevant compute | planning budget/call field 필요 | HIGH |
| REF-LATENT-001 | 00_MASTER_REFERENCE.md | latent seed | z_state | state supervision 후보 | HIGH |
| REF-LATENT-002 | 00_MASTER_REFERENCE.md | latent seed | z_regime | regime supervision 후보 | CRITICAL |
| REF-LATENT-003 | 00_MASTER_REFERENCE.md | latent seed | z_control_grammar | grammar supervision 후보 | CRITICAL |
| REF-LATENT-004 | 00_MASTER_REFERENCE.md | latent seed | z_change_point | change-point supervision 후보 | HIGH |
| REF-DATA-001 | 00_MASTER_REFERENCE.md | data seed | DOM tree | agent observation과 diff 계산 | CRITICAL |
| REF-DATA-002 | 00_MASTER_REFERENCE.md | data seed | screenshot feature | visual diff/bbox 검증 | HIGH |
| REF-DATA-003 | 00_MASTER_REFERENCE.md | data seed | structured action-effect log | falsification/metric 계산 원천 | CRITICAL |
| REF-DATA-004 | 00_MASTER_REFERENCE.md | data seed | hidden regime label | training/evaluation only | CRITICAL |
| REF-DATA-005 | 00_MASTER_REFERENCE.md | data seed | hidden control grammar label | training/evaluation only | CRITICAL |
| REF-DATA-006 | 00_MASTER_REFERENCE.md | data seed | alternative action effect table | counterfactual-only로 격리 | CRITICAL |
| PAPER-001 | 01_RELATED_WORK_THREAT_MAP.md | direct threat | WebWorld | generic web world model claim 방어 | HIGH |
| PAPER-002 | 01_RELATED_WORK_THREAT_MAP.md | direct threat | WAC | consequence simulation/action correction과 구분 | HIGH |
| PAPER-003 | 01_RELATED_WORK_THREAT_MAP.md | direct threat | CUWM | frozen agent + WM search와 구분 | HIGH |
| PAPER-004 | 01_RELATED_WORK_THREAT_MAP.md | direct threat | VeriGUI | verification/recovery와 falsification schema 구분 | CRITICAL |
| PAPER-005 | 01_RELATED_WORK_THREAT_MAP.md | benchmark | WebArena | realistic web benchmark anchor | MEDIUM |
| PAPER-006 | 01_RELATED_WORK_THREAT_MAP.md | benchmark | VisualWebArena | screenshot/visual observation 필요성 | MEDIUM |
| PAPER-007 | 01_RELATED_WORK_THREAT_MAP.md | benchmark | OSWorld | real computer-use 한계 명시 | MEDIUM |
| PAPER-008 | 01_RELATED_WORK_THREAT_MAP.md | benchmark | WorkArena/BrowserGym | standardized obs/action/trace anchor | HIGH |
| ATTACK-010 | 01_RELATED_WORK_THREAT_MAP.md | reviewer attack | control grammar는 용어 재포장 | label definition과 anti-leakage 필요 | CRITICAL |
| ATTACK-012 | 01_RELATED_WORK_THREAT_MAP.md | reviewer attack | hidden labels are unrealistic | synthetic-only vs real-world limitation 명시 | HIGH |
| CLAIM-001 | 02_PROBLEM_NOVELTY_FALSIFICATION.md | conditional claim | wrong grammar persistence may survive | metric-support fields 필요 | CRITICAL |
| CLAIM-002 | 02_PROBLEM_NOVELTY_FALSIFICATION.md | conditional claim | verification과 구분 가능해야 함 | verification/falsification field 분리 | CRITICAL |
| MCX-001 | 02_PROBLEM_NOVELTY_FALSIFICATION.md | counterexample | pagination vs infinite scroll | same intent different executable action schema | HIGH |
| MCX-002 | 02_PROBLEM_NOVELTY_FALSIFICATION.md | counterexample | modal-blocked direct click | covered_by/overlay field 필요 | HIGH |
| MCX-003 | 02_PROBLEM_NOVELTY_FALSIFICATION.md | counterexample | form-invalid disabled submit | validation/precondition field 필요 | HIGH |
| MCX-004 | 02_PROBLEM_NOVELTY_FALSIFICATION.md | counterexample | loading/stale DOM timing | delayed_effect/noisy flag 필요 | HIGH |
| METRIC-001 | 02_PROBLEM_NOVELTY_FALSIFICATION.md | metric | wrong-control-grammar persistence time | executed hypothesis와 true grammar 비교 필요 | CRITICAL |
| METRIC-002 | 02_PROBLEM_NOVELTY_FALSIFICATION.md | metric | failed-action repetition rate | action identity/failure reason field 필요 | HIGH |
| METRIC-003 | 02_PROBLEM_NOVELTY_FALSIFICATION.md | metric | action-interface switch delay | rewrite/switch timestamp 필요 | HIGH |
| METRIC-004 | 02_PROBLEM_NOVELTY_FALSIFICATION.md | metric | recovery delay | failure evidence와 progress recovery timestamp 필요 | HIGH |
| CONCEPT-003 | 03_CORE_CONCEPT_TAXONOMY.md | taxonomy | regime | mode label과 observation 분리 | CRITICAL |
| CONCEPT-004 | 03_CORE_CONCEPT_TAXONOMY.md | taxonomy | control grammar | intent mapping/precondition/effect schema로 저장 | CRITICAL |
| CONCEPT-012 | 03_CORE_CONCEPT_TAXONOMY.md | taxonomy | falsification | likelihood/evidence strength proxy 필요 | CRITICAL |
| CONCEPT-016 | 03_CORE_CONCEPT_TAXONOMY.md | taxonomy | wrong-control-grammar persistence | metric support record 필요 | CRITICAL |
| BOUNDARY-008 | 03_CORE_CONCEPT_TAXONOMY.md | boundary | click 후 no-effect | failed action vs falsification evidence 구분 | HIGH |
| SEPARATION-008 | 03_CORE_CONCEPT_TAXONOMY.md | separation | verification vs falsification | verification label과 hypothesis update label 분리 | CRITICAL |
| TEXT-SCHEMA-001 | 04_TEXT_ONLY_SMOKE_TESTBED.md | schema | episode_id/task_family/instruction | episode metadata 기본 | HIGH |
| TEXT-SCHEMA-010 | 04_TEXT_ONLY_SMOKE_TESTBED.md | schema | current/alternative hypotheses | hypothesis trace field로 확장 | CRITICAL |
| TEXT-TEST-001 | 04_TEXT_ONLY_SMOKE_TESTBED.md | test | modal blocked | covered_by와 failed evidence fields 필요 | HIGH |
| TEXT-GATE-001 | 04_TEXT_ONLY_SMOKE_TESTBED.md | gate | no-grammar ablation 하락 | grammar label과 ablation support 필요 | CRITICAL |
| TEXT-LIMITATION-001 | 04_TEXT_ONLY_SMOKE_TESTBED.md | limitation | visual grounding 불가 | screenshot/bbox fields 추가 | HIGH |
| ENV-COMP-003 | 05_SYNTHETIC_WEB_GUI_ENVIRONMENT.md | env component | DOM generator | DOM observation/diff schema 필요 | CRITICAL |
| ENV-COMP-004 | 05_SYNTHETIC_WEB_GUI_ENVIRONMENT.md | env component | screenshot renderer | screenshot_ref/visual_diff 필요 | HIGH |
| ENV-COMP-005 | 05_SYNTHETIC_WEB_GUI_ENVIRONMENT.md | env component | accessibility tree exporter | a11y schema 필요 | HIGH |
| ENV-COMP-014 | 05_SYNTHETIC_WEB_GUI_ENVIRONMENT.md | env component | action-effect logger | per-step evidence schema 중심 | CRITICAL |
| ENV-COMP-015 | 05_SYNTHETIC_WEB_GUI_ENVIRONMENT.md | env component | counterfactual generator | counterfactual-only record 필요 | CRITICAL |
| ENV-OBS-015 | 05_SYNTHETIC_WEB_GUI_ENVIRONMENT.md | observation | hidden regime label | agent input 금지 | CRITICAL |
| ENV-OBS-016 | 05_SYNTHETIC_WEB_GUI_ENVIRONMENT.md | observation | hidden control grammar label | agent input 금지 | CRITICAL |
| ENV-COUNTERFACTUAL-001 | 05_SYNTHETIC_WEB_GUI_ENVIRONMENT.md | counterfactual | current vs alternative effect | rollout fidelity supervision/eval | CRITICAL |
| ENV-OOD-001 | 05_SYNTHETIC_WEB_GUI_ENVIRONMENT.md | split | ID/OOD split design | split metadata와 held-out factor 필요 | HIGH |
| ENV-GUARDRAIL-001 | 05_SYNTHETIC_WEB_GUI_ENVIRONMENT.md | guardrail | hidden labels not in DOM class/text | leakage audit 필수 | CRITICAL |
| ENV-STRESS-001 | 05_SYNTHETIC_WEB_GUI_ENVIRONMENT.md | stress | label leakage/shortcut | audit flags와 tests 필요 | CRITICAL |


## 3. Search Expansion Ledger


| Search ID | Query | Source/Paper/Tool/Concept | Key Finding | How It Informs Schema/Labeling | Risk/Threat | Follow-up |
| --- | --- | --- | --- | --- | --- | --- |
| SEARCH-06-001 | web agent dataset schema trajectory | BrowserGym Ecosystem for Web Agent Research, 2024 | web agent 평가를 위한 unified gym-like observation/action space를 제안 | agent obs/action schema와 benchmark reproducibility 설계 참고 | fragmented benchmark 문제를 보여줌 | Step 10에서 BrowserGym-style eval 비교 |
| SEARCH-06-002 | RLDS reinforcement learning dataset schema episodes steps | Google Research RLDS, 2021 | sequential decision making dataset을 episode/step 단위로 저장·조작하는 ecosystem | episode-level/step-level hierarchy 설계 anchor | RLDS는 Web/GUI hidden label을 직접 제공하지 않음 | schema adapter 검토 |
| SEARCH-06-003 | D4RL datasets offline reinforcement learning benchmark format | D4RL, 2020 | offline RL benchmark와 static dataset 평가 protocol 제안 | logged trajectories와 offline evaluation field 참고 | web action-effect evidence와 다름 | normalized score 설계에 참고 |
| SEARCH-06-004 | datasheets for datasets machine learning | Datasheets for Datasets, Gebru et al. | motivation, composition, collection, intended use 등 dataset documentation 제안 | dataset card/documentation 요구사항 설계 | documentation만으로 leakage를 막지는 못함 | appendix dataset card로 확장 |
| SEARCH-06-005 | dataset card benchmark documentation | Model Cards / Dataset documentation practice | evaluation conditions와 intended use disclosure 강조 | intended/prohibited use, limitations 섹션 설계 | model card는 dataset schema가 아님 | dataset card로만 사용 |
| SEARCH-06-006 | Playwright trace viewer DOM snapshot screenshot | Playwright Trace Viewer | action별 trace, browser state, screenshot 기반 debugging 지원 | per-step trace artifact, screenshot_ref, action timeline 설계 | trace artifact가 agent input으로 새면 안 됨 | audit path sanitizer 필요 |
| SEARCH-06-007 | Playwright aria snapshots accessibility tree | Playwright ARIA snapshots | accessibility tree를 YAML-like snapshot으로 저장·비교 가능 | a11y_tree field 설계 참고 | ARIA label이 hidden grammar를 노출할 수 있음 | sanitize_a11y 필요 |
| SEARCH-06-008 | Chrome DevTools Protocol DOMSnapshot | CDP DOMSnapshot domain | full DOM tree/layout/computed style snapshot 반환 가능 | DOM tree/layout/bbox capture schema 참고 | style/class name leakage 가능 | sanitize_dom 필요 |
| SEARCH-06-009 | Chrome DevTools accessibility tree | Chrome DevTools accessibility pane | DOM node가 assistive tech에 어떻게 노출되는지 제공 | AX-tree와 DOM mismatch audit 필요 | accessibility labels shortcut 위험 | cross-modal consistency check |
| SEARCH-06-010 | VisualWebArena observation format screenshot DOM | VisualWebArena | visual information이 필요한 web task benchmark | screenshot_ref, bbox, visual_diff 필요성 | hidden label 없음 | 보조 eval anchor |
| SEARCH-06-011 | MiniWoB++ observation action format | MiniWoB++ | 100개 이상 browser interaction environment와 gym-style API | synthetic web action/action observation abstraction 참고 | modern Web/GUI realism 제한 | smoke/task abstraction 참고 |
| SEARCH-06-012 | OSWorld trajectory logging computer use benchmark | OSWorld | real computer-use tasks benchmark | realistic computer-use limitation 명시 | controlled labels 없음 | external validation만 |
| SEARCH-06-013 | counterfactual action effect labels reinforcement learning | counterfactual trajectories RL concept | unexecuted action의 effect label은 synthetic/causal env에서만 직접 가능 | counterfactual-only bucket 설계 | real web extension 불가 | synthetic-only limitation 명시 |
| SEARCH-06-014 | change point detection dataset labels | change-point sequence labeling | event boundary와 regime shift annotation이 필요 | true_change_point, event_type schema 설계 | label ambiguity | inter-logic validator 필요 |
| SEARCH-06-015 | regime shift labeling sequential data | regime-switching models | hidden mode/regime labels는 sequence supervision으로 사용 가능 | true_regime timeline 저장 | identifiability 위험 | Step 07에서 probe 필요 |
| SEARCH-06-016 | benchmark train test leakage prevention | ML benchmark leakage prevention | metadata/seed/template leakage가 benchmark를 무효화할 수 있음 | leakage audit ledger 설계 | 완전 자동 검출 어려움 | adversarial audit 필요 |
| SEARCH-06-017 | OOD split dataset design machine learning | distribution shift / OOD benchmark design | held-out factor를 명시해야 OOD claim 가능 | split metadata and held_out_factor fields | split이 너무 쉽거나 어려울 수 있음 | Step 10에서 difficulty calibration |
| SEARCH-06-018 | web UI action logging DOM diff | browser action logging concept | pre/post DOM diff와 visual diff가 action-effect evidence의 핵심 | dom_diff, visual_diff_score, effect_match_score 설계 | diff와 semantic progress 불일치 | progress validator 필요 |
| SEARCH-06-019 | browser agent observation action trace format | BrowserGym/AgentLab trace analysis | observation/action space 표준화와 experiment management 강조 | trace exporter와 reproducibility fields 설계 | framework-specific bias | general schema로 추상화 |
| SEARCH-06-020 | offline RL dataset schema transition tuple | offline RL trajectories | state/action/reward/next_state/done 기반 기본 transition 구조 | step record 최소 구조 참고 | hypothesis/evidence label 부족 | 확장 schema로 설계 |
| SEARCH-06-021 | synthetic benchmark leakage guardrails | synthetic benchmark shortcut risks | synthetic task에서 template/label shortcut 위험 | anti-leakage flags 설계 | 검출 누락 가능 | stress tests 추가 |
| SEARCH-06-022 | browser automation trace format screenshots network logs | Playwright traces / browser debugging | screenshots, DOM, network, console, timing log가 trace에 포함 가능 | network/timing/log artifact optional fields | over-logging privacy/size risk | artifact policy 필요 |
| SEARCH-06-023 | event detection sequence labeling schema | event detection labels | event type, onset/offset, confidence schema 필요 | event_id, event_start_step, event_end_step 설계 | event boundary 모호성 | label rule 명시 |
| SEARCH-06-024 | POMDP hidden state label dataset | POMDP benchmark hidden state | hidden state는 observation과 분리되어 supervision/eval로만 사용 | true_hidden_state visibility contract | hidden state leakage 위험 | agent_obs extraction assert |
| SEARCH-06-025 | causal environment action effect dataset | causal/action effect simulation | controlled simulator에서 action-effect causal labels 생성 가능 | action_effect_executor/counterfactual record 연결 | real-world causal label 없음 | synthetic vs real limitation |


## 4. Data Visibility Contract


| Visibility ID | Field | Bucket | Allowed In Agent Input? | Allowed In Training? | Allowed In Evaluation? | Leakage Risk | Guardrail |
| --- | --- | --- | --- | --- | --- | --- | --- |
| VIS-06-001 | public_instruction | AGENT_OBSERVATION/AUDIT_METADATA | YES | NO | YES | instruction이 split/regime shortcut을 포함할 수 있음 | paraphrase + forbidden token scan |
| VIS-06-002 | dom_tree_sanitized | AGENT_OBSERVATION | YES | NO | YES | class/id에 hidden label leakage | sanitize_dom removes regime/grammar names |
| VIS-06-003 | accessibility_tree_sanitized | AGENT_OBSERVATION | YES | NO | YES | aria-label에 grammar leakage | sanitize_a11y + audit |
| VIS-06-004 | screenshot_ref_public | AGENT_OBSERVATION | YES | NO | YES | filename에 split/regime 정보 leakage | opaque UUID filename |
| VIS-06-005 | bbox_public | AGENT_OBSERVATION | YES | NO | YES | target bbox가 oracle target처럼 작동 | all visible elements bbox 제공 |
| VIS-06-006 | visible_enabled_clickable_public | AGENT_OBSERVATION | YES | NO | YES | precondition shortcut 위험 | public UI affordance만 제공 |
| VIS-06-007 | previous_action_public | AGENT_OBSERVATION | YES | NO | YES | action id가 target semantics 노출 | public action normalization |
| VIS-06-008 | observed_effect_public | AGENT_OBSERVATION | YES | NO | YES | 너무 노골적 evidence leakage | coarse natural summary + structured public diff only |
| VIS-06-009 | true_hidden_state | TRAINING_SUPERVISION/EVALUATION_ONLY | NO | YES | YES | hidden state leakage | never in build_agent_observation |
| VIS-06-010 | true_regime | TRAINING_SUPERVISION/EVALUATION_ONLY | NO | YES | YES | 핵심 label leakage | storage-only, prompt assert |
| VIS-06-011 | true_control_grammar | TRAINING_SUPERVISION/EVALUATION_ONLY | NO | YES | YES | 핵심 label leakage | storage-only, prompt assert |
| VIS-06-012 | true_change_point | TRAINING_SUPERVISION/EVALUATION_ONLY | NO | YES | YES | future/event leakage | label record only |
| VIS-06-013 | true_event_type | TRAINING_SUPERVISION/EVALUATION_ONLY | NO | YES | YES | event class leakage | label record only |
| VIS-06-014 | true_reveal_vs_shift | TRAINING_SUPERVISION/EVALUATION_ONLY | NO | YES | YES | shift answer leakage | label record only |
| VIS-06-015 | true_action_precondition_satisfied | TRAINING_SUPERVISION | NO | YES | YES | precondition answer leakage | supervision only |
| VIS-06-016 | true_action_effect_type | TRAINING_SUPERVISION/EVALUATION_ONLY | NO | YES | YES | effect answer leakage | supervision/eval only |
| VIS-06-017 | true_failed_action | TRAINING_SUPERVISION/EVALUATION_ONLY | NO | YES | YES | failure shortcut | derived after action only; not input |
| VIS-06-018 | true_failure_reason | TRAINING_SUPERVISION/EVALUATION_ONLY | NO | YES | YES | grammar answer leakage | label-only; public reason coarse |
| VIS-06-019 | true_recovery_action | TRAINING_SUPERVISION/EVALUATION_ONLY | NO | YES | YES | oracle action leakage | not agent input |
| VIS-06-020 | true_progress_delta | TRAINING_SUPERVISION/EVALUATION_ONLY | NO | YES | YES | reward/progress leakage | post-step label only |
| VIS-06-021 | true_task_success | EVALUATION_ONLY | NO | NO | YES | success shortcut | episode terminal only |
| VIS-06-022 | true_wrong_hypothesis | TRAINING_SUPERVISION/EVALUATION_ONLY | NO | YES | YES | current hypothesis answer leakage | derived from executed hypothesis vs true grammar |
| VIS-06-023 | true_valid_hypothesis_switch | TRAINING_SUPERVISION/EVALUATION_ONLY | NO | YES | YES | switch reward leakage | post-hoc label |
| VIS-06-024 | true_invalid_hypothesis_switch | TRAINING_SUPERVISION/EVALUATION_ONLY | NO | YES | YES | switch answer leakage | post-hoc label |
| VIS-06-025 | current_hypothesis_model_record | AUDIT_METADATA/EVALUATION_ONLY | NO | NO | YES | agent rationale leakage in future step | stored after inference only |
| VIS-06-026 | alternative_hypotheses_model_record | AUDIT_METADATA/EVALUATION_ONLY | NO | NO | YES | top-k answer leakage | stored after proposal only |
| VIS-06-027 | counterfactual_action_effects | COUNTERFACTUAL_ONLY | NO | YES_WITH_RESTRICTION | YES | massive oracle leakage | never in obs; separate file shard |
| VIS-06-028 | counterfactual_progress_delta | COUNTERFACTUAL_ONLY | NO | YES_WITH_RESTRICTION | YES | oracle progress leakage | counterfactual-only shard |
| VIS-06-029 | counterfactual_failure_risk | COUNTERFACTUAL_ONLY | NO | YES_WITH_RESTRICTION | YES | oracle risk leakage | excluded from agent prompt |
| VIS-06-030 | counterfactual_best_alternative | COUNTERFACTUAL_ONLY/EVALUATION_ONLY | NO | YES_WITH_RESTRICTION | YES | best alt answer leakage | only for rollout fidelity/eval |
| VIS-06-031 | oracle_regime_action | COUNTERFACTUAL_ONLY/EVALUATION_ONLY | NO | NO | YES | oracle upper bound leakage | eval-only |
| VIS-06-032 | oracle_grammar_action | COUNTERFACTUAL_ONLY/EVALUATION_ONLY | NO | NO | YES | oracle grammar action leakage | eval-only |
| VIS-06-033 | reward_components | TRAINING_SUPERVISION/EVALUATION_ONLY | NO | YES | YES | reward answer in obs | post-step only |
| VIS-06-034 | compute_cost | TRAINING_SUPERVISION/EVALUATION_ONLY | NO | YES | YES | compute budget shortcut | logged separately |
| VIS-06-035 | template_id | AUDIT_METADATA | NO | NO | YES | template-regime shortcut | never agent input |
| VIS-06-036 | seed | AUDIT_METADATA | NO | NO | YES | split/episode shortcut | opaque and hidden |
| VIS-06-037 | split_id | AUDIT_METADATA | NO | NO | YES | train/test shortcut | never input |
| VIS-06-038 | ood_type | AUDIT_METADATA | NO | NO | YES | OOD answer leakage | never input |
| VIS-06-039 | regime_distribution_id | AUDIT_METADATA | NO | NO | YES | label distribution leakage | hidden metadata |
| VIS-06-040 | grammar_distribution_id | AUDIT_METADATA | NO | NO | YES | grammar distribution leakage | hidden metadata |
| VIS-06-041 | leakage_check_flags | AUDIT_METADATA | NO | NO | YES | could reveal risk labels | audit only |
| VIS-06-042 | generation_config_hash | AUDIT_METADATA | NO | NO | YES | seed/config shortcut | opaque hash |
| VIS-06-043 | browser_version | AUDIT_METADATA | NO | NO | YES | reproducibility only | audit only |
| VIS-06-044 | viewport_size | AGENT_OBSERVATION/AUDIT_METADATA | YES | NO | YES | layout regime shortcut 가능 | balanced across regimes |
| VIS-06-045 | artifact_paths | AUDIT_METADATA | NO | NO | YES | filename leakage | opaque UUID paths |


## 5. Hierarchical Dataset Schema


### 5.1 Dataset-Level Metadata


| Field | Type | Required? | Description | Example | Visibility Bucket |
| --- | --- | --- | --- | --- | --- |
| dataset_id | string | YES | 데이터셋 고유 ID | frcgwm_synth_v0_1 | AUDIT_METADATA |
| dataset_version | string | YES | 공개/실험 버전 | 0.1.0 | AUDIT_METADATA |
| schema_version | string | YES | schema contract 버전 | schema-06-v0.1 | AUDIT_METADATA |
| generator_version | string | YES | episode generator 버전 | gen-0.3.2 | AUDIT_METADATA |
| environment_version | string | YES | Web/GUI environment 버전 | env-0.2.0 | AUDIT_METADATA |
| license | string | YES | 배포 라이선스 | research-only | AUDIT_METADATA |
| created_at | datetime | YES | 생성 시각 | 2026-05-08T00:00:00+09:00 | AUDIT_METADATA |


### 5.2 Split-Level Metadata


| Field | Type | Required? | Description | Example | Visibility Bucket |
| --- | --- | --- | --- | --- | --- |
| split_id | string | YES | split ID | ood_control_grammar_shift | AUDIT_METADATA |
| split_name | string | YES | split 명칭 | OOD-Control Grammar Shift | AUDIT_METADATA |
| distribution_rule | string | YES | 분포 규칙 | same layout, changed grammar | AUDIT_METADATA |
| held_out_factor | string | YES | held-out 요소 | grammar family | AUDIT_METADATA |
| episode_count | int | YES | episode 수 | 500 | AUDIT_METADATA |
| split_seed | int | YES | split seed | 73211 | AUDIT_METADATA |


### 5.3 Episode-Level Metadata


| Field | Type | Required? | Description | Example | Visibility Bucket |
| --- | --- | --- | --- | --- | --- |
| episode_id | string | YES | episode 고유 ID | ep_000001 | AUDIT_METADATA |
| task_family | string | YES | task family | shopping_search_filter | AUDIT_METADATA/EVALUATION_ONLY |
| episode_seed | int | YES | episode seed | 10001 | AUDIT_METADATA |
| max_steps | int | YES | 최대 step | 30 | AUDIT_METADATA |
| initial_url_ref | string | NO | 초기 page ref | page/product_list | AUDIT_METADATA |
| success_condition_id | string | YES | 성공 판정 rule ID | succ_add_cart_filter | EVALUATION_ONLY |


### 5.4 Task-Level Metadata


| Field | Type | Required? | Description | Example | Visibility Bucket |
| --- | --- | --- | --- | --- | --- |
| public_instruction | string | YES | agent에게 제공되는 instruction | Find a wireless mouse under $30... | AGENT_OBSERVATION |
| task_intent_graph | json | YES | subgoal DAG | search→filter→select→cart | EVALUATION_ONLY |
| target_entities_public | json | NO | 공개 가능한 target 조건 | price<30, rating>=4 | AGENT_OBSERVATION |
| subgoal_list | list | YES | 평가용 subgoal 목록 | [open_filter, set_price, add_cart] | EVALUATION_ONLY |
| instruction_paraphrase_id | string | YES | paraphrase template ID | para_17 | AUDIT_METADATA |
| language | string | YES | instruction 언어 | en | AUDIT_METADATA |


### 5.5 UI Template Metadata


| Field | Type | Required? | Description | Example | Visibility Bucket |
| --- | --- | --- | --- | --- | --- |
| template_id | string | YES | UI template ID | tmpl_product_list_v3 | AUDIT_METADATA |
| template_family | string | YES | 템플릿군 | product_list | AUDIT_METADATA |
| ui_pages | list | YES | episode page/view 목록 | [list, detail, cart] | AUDIT_METADATA |
| css_theme_id | string | YES | 스타일 변형 ID | theme_08 | AUDIT_METADATA |
| layout_seed | int | YES | layout randomization seed | 492 | AUDIT_METADATA |
| perturbation_config | json | NO | layout/text/timing perturbation | {"layout_shift": true} | AUDIT_METADATA |


### 5.6 Step-Level Observation Schema


| Field | Type | Required? | Description | Example | Visibility Bucket |
| --- | --- | --- | --- | --- | --- |
| step_id | int | YES | step index | 7 | AUDIT_METADATA |
| timestamp_ms | int | YES | episode-relative time | 15233 | AUDIT_METADATA |
| dom_tree_sanitized | json | YES | agent-safe DOM tree | {"nodes": [...]} | AGENT_OBSERVATION |
| accessibility_tree_sanitized | json/yaml | YES | agent-safe AX tree | - button: Add to cart | AGENT_OBSERVATION |
| screenshot_ref_public | string | NO | opaque screenshot artifact ref | img_a13f.png | AGENT_OBSERVATION |
| viewport_size | tuple | YES | viewport width/height | [1280,720] | AGENT_OBSERVATION/AUDIT_METADATA |
| visible_elements_public | list | YES | visible element summary | [{role:button,name:Add}] | AGENT_OBSERVATION |
| enabled_clickable_public | list | YES | public affordance summary | [{id:e12, enabled:false}] | AGENT_OBSERVATION |
| scroll_state_public | json | YES | scroll position/scrollability | {"page_y":0,"container_scrollable":true} | AGENT_OBSERVATION |
| observed_effect_public | string/json | NO | 이전 action 후 공개 가능한 effect 요약 | modal still blocks target | AGENT_OBSERVATION |


### 5.7 Step-Level Action Schema


| Field | Type | Required? | Description | Example | Visibility Bucket |
| --- | --- | --- | --- | --- | --- |
| previous_action_public | json | NO | 이전 public action | {"type":"click","target_ref":"e12"} | AGENT_OBSERVATION |
| action_id | string | YES | action 고유 ID | act_0007 | AUDIT_METADATA |
| action_type | enum | YES | click/type/select/scroll/wait 등 | click | EVALUATION_ONLY |
| action_args_public | json | YES | agent가 선택한 공개 args | {"target_ref":"e12"} | EVALUATION_ONLY |
| target_element_public_ref | string | NO | public element ref | e12 | EVALUATION_ONLY |
| action_macro_id | string | NO | macro action ID | macro_select_then_add | EVALUATION_ONLY |
| action_source | enum | YES | base/rewrite/oracle/random 등 | rewrite | EVALUATION_ONLY |


### 5.8 Step-Level Action-Effect Schema


| Field | Type | Required? | Description | Example | Visibility Bucket |
| --- | --- | --- | --- | --- | --- |
| pre_state_hash_public | string | YES | public observable state hash | h_pre_abc | AUDIT_METADATA |
| post_state_hash_public | string | YES | public observable post hash | h_post_def | AUDIT_METADATA |
| dom_diff | json | YES | pre/post DOM diff | [{op:add,node:cart_badge}] | TRAINING_SUPERVISION/EVALUATION_ONLY |
| visual_diff_score | float | YES | screenshot diff magnitude | 0.12 | TRAINING_SUPERVISION/EVALUATION_ONLY |
| accessibility_diff | json | YES | AX tree diff | [{changed:button_enabled}] | TRAINING_SUPERVISION/EVALUATION_ONLY |
| observed_effect | enum/json | YES | actual effect summary | no_state_change | TRAINING_SUPERVISION/EVALUATION_ONLY |
| effect_match_score | float | YES | expected vs observed match | 0.05 | TRAINING_SUPERVISION/EVALUATION_ONLY |
| failure_reason | enum | NO | 실패 원인 | modal_overlay | TRAINING_SUPERVISION/EVALUATION_ONLY |


### 5.9 Hidden Label Schema


| Field | Type | Required? | Description | Example | Visibility Bucket |
| --- | --- | --- | --- | --- | --- |
| true_hidden_state | json | YES | hidden UI/task state | {"modal_active":true} | TRAINING_SUPERVISION/EVALUATION_ONLY |
| true_regime | enum | YES | hidden interaction mode | modal_blocked | TRAINING_SUPERVISION/EVALUATION_ONLY |
| true_control_grammar | enum | YES | true intent-to-action grammar | remove_blocker_before_target_action | TRAINING_SUPERVISION/EVALUATION_ONLY |
| true_change_point | bool | YES | change-point 여부 | true | TRAINING_SUPERVISION/EVALUATION_ONLY |
| true_event_type | enum | YES | event type | shift | TRAINING_SUPERVISION/EVALUATION_ONLY |
| true_reveal_vs_shift | enum | YES | none/reveal/shift/failed/noisy/delayed | shift | TRAINING_SUPERVISION/EVALUATION_ONLY |
| true_wrong_hypothesis | bool | YES | executed hypothesis가 틀렸는지 | true | TRAINING_SUPERVISION/EVALUATION_ONLY |


### 5.10 Counterfactual Record Schema


| Field | Type | Required? | Description | Example | Visibility Bucket |
| --- | --- | --- | --- | --- | --- |
| counterfactual_action_effects | json | YES | candidate actions의 synthetic effect | {"close_modal":{"progress":0.1}} | COUNTERFACTUAL_ONLY |
| counterfactual_progress_delta | json | YES | action별 progress delta | {"close_modal":0.1} | COUNTERFACTUAL_ONLY |
| counterfactual_failure_risk | json | YES | action별 failure risk | {"click_filter":0.95} | COUNTERFACTUAL_ONLY |
| counterfactual_best_alternative | string | YES | oracle best alternative | close_modal_then_click_filter | COUNTERFACTUAL_ONLY/EVALUATION_ONLY |
| oracle_regime_action | string | YES | oracle regime policy action | close_modal | COUNTERFACTUAL_ONLY/EVALUATION_ONLY |
| oracle_grammar_action | string | YES | oracle grammar action/macro | remove_blocker_then_open_filter | COUNTERFACTUAL_ONLY/EVALUATION_ONLY |


### 5.11 Reward/Progress Record Schema


| Field | Type | Required? | Description | Example | Visibility Bucket |
| --- | --- | --- | --- | --- | --- |
| progress_score | float | YES | cumulative progress | 0.4 | TRAINING_SUPERVISION/EVALUATION_ONLY |
| progress_delta | float | YES | per-step progress | 0.2 | TRAINING_SUPERVISION/EVALUATION_ONLY |
| subgoal_completion | json | YES | subgoal status | {"filter_open":true} | EVALUATION_ONLY |
| reward_components | json | YES | reward decomposition | {"progress":0.2,"fail":-0.2} | TRAINING_SUPERVISION/EVALUATION_ONLY |
| task_success | bool | YES | episode success | false | EVALUATION_ONLY |
| done | bool | YES | episode done | false | EVALUATION_ONLY |


### 5.12 Leakage Audit Record Schema


| Field | Type | Required? | Description | Example | Visibility Bucket |
| --- | --- | --- | --- | --- | --- |
| leakage_check_flags | json | YES | audit 결과 flags | {"dom_label_token":false} | AUDIT_METADATA |
| forbidden_token_scan | json | YES | hidden label token scan | {"modal_blocked":0} | AUDIT_METADATA |
| template_regime_mutual_info | float | NO | template-regime MI | 0.03 | AUDIT_METADATA |
| task_regime_mutual_info | float | NO | task-regime MI | 0.04 | AUDIT_METADATA |
| filename_leakage_check | bool | YES | artifact path leakage 여부 | false | AUDIT_METADATA |
| split_seed_overlap_check | bool | YES | split seed overlap 여부 | false | AUDIT_METADATA |


## 6. Canonical Episode JSON Example

아래 예시는 storage용 canonical episode record다. 이 JSON에는 hidden labels가 포함되지만, **agent observation은 반드시 Section 7의 extraction contract를 통해 별도로 추출해야 하며 hidden labels를 포함하면 안 된다.**

```json
{
  "dataset_metadata": {
    "dataset_id": "frcgwm_synth",
    "dataset_version": "0.1.0",
    "schema_version": "schema-06-v0.1",
    "generator_version": "gen-0.3.2",
    "environment_version": "env-0.2.0"
  },
  "episode_metadata": {
    "episode_id": "ep_000001",
    "split_id": "ood_control_grammar_shift",
    "task_family": "shopping_search_filter",
    "episode_seed": 10001,
    "template_id": "tmpl_product_list_v3",
    "max_steps": 30
  },
  "task_metadata": {
    "public_instruction": "Find a wireless mouse under $30 with rating >= 4 and add it to cart.",
    "subgoal_list": ["open_filter", "set_price", "select_product", "add_to_cart"],
    "success_condition_id": "succ_cart_contains_target_product"
  },
  "steps": [
    {
      "step_id": 0,
      "observation": {
        "dom_tree_sanitized": {"nodes": [{"ref": "e12", "role": "button", "name": "Filter", "visible": true, "enabled": true}]},
        "accessibility_tree_sanitized": "- button: Filter",
        "screenshot_ref_public": "screens/ep000001_step000_uuid.png",
        "viewport_size": [1280, 720],
        "observed_effect_public": null
      },
      "action": {
        "action_id": "act_000000",
        "action_type": "click",
        "action_args_public": {"target_ref": "e12"},
        "action_source": "base"
      },
      "action_effect": {
        "pre_state_hash_public": "h_pre_001",
        "post_state_hash_public": "h_pre_001",
        "dom_diff": [],
        "visual_diff_score": 0.01,
        "accessibility_diff": [],
        "observed_effect": "no_state_change",
        "effect_match_score": 0.02,
        "failure_reason": "modal_overlay"
      },
      "hidden_labels": {
        "true_hidden_state": {"modal_active": true, "filter_panel_open": false, "cart_count": 0},
        "true_regime": "modal_blocked",
        "true_control_grammar": "remove_blocker_before_target_action",
        "true_change_point": false,
        "true_event_type": "failed_action",
        "true_reveal_vs_shift": "failed_action",
        "true_wrong_hypothesis": true
      },
      "counterfactual_records": {
        "counterfactual_action_effects": {
          "close_modal": {"observed_effect": "modal_removed", "progress_delta": 0.1, "failure_risk": 0.05},
          "click_filter_button": {"observed_effect": "no_state_change", "progress_delta": 0.0, "failure_risk": 0.95}
        },
        "counterfactual_best_alternative": "close_modal",
        "oracle_grammar_action": "close_modal_then_click_filter"
      },
      "reward_progress": {
        "progress_score": 0.0,
        "progress_delta": 0.0,
        "reward_components": {"progress": 0.0, "failed_action_penalty": -0.2, "compute_cost": -0.01},
        "task_success": false,
        "done": false
      }
    }
  ],
  "audit_metadata": {
    "leakage_check_flags": {"hidden_label_in_dom": false, "hidden_label_in_filename": false},
    "generation_config_hash": "sha256:abc123",
    "browser_version": "chromium-124",
    "viewport_size": [1280, 720]
  }
}
```

## 7. Agent Observation Extraction Contract


| Agent Input Field | Source Field | Included? | Reason | Hidden Label Risk |
| --- | --- | --- | --- | --- |
| instruction | task_metadata.public_instruction | YES | task instruction은 agent가 실제로 받아야 함 | instruction에 regime token 포함 금지 |
| dom_tree | step.observation.dom_tree_sanitized | YES | 구조화된 public UI observation | class/id/token sanitizer 필요 |
| accessibility_tree | step.observation.accessibility_tree_sanitized | YES | semantic UI observation | aria label leakage scan 필요 |
| screenshot_ref | step.observation.screenshot_ref_public | OPTIONAL | visual observation 실험에서 사용 | filename UUID 필요 |
| viewport_size | step.observation.viewport_size | YES | responsive UI 판단에 필요 | viewport-regime shortcut balancing |
| visible_elements | step.observation.visible_elements_public | YES | public affordance 판단 | target-only list 금지 |
| enabled_clickable_public | step.observation.enabled_clickable_public | YES | public UI 상태 | hidden precondition directly exposing 금지 |
| previous_action | step.previous_action_public | YES_AFTER_STEP0 | history 기반 판단 | oracle action_source 금지 |
| observed_effect_summary | step.observation.observed_effect_public | YES_AFTER_STEP0 | action-effect evidence의 public form | true_failure_reason direct 노출 금지 |
| true_regime | step.hidden_labels.true_regime | NO | hidden label | 절대 포함 금지 |
| true_control_grammar | step.hidden_labels.true_control_grammar | NO | hidden label | 절대 포함 금지 |
| counterfactual_action_effects | step.counterfactual_records.counterfactual_action_effects | NO | oracle/counterfactual label | 절대 포함 금지 |


```python
def build_agent_observation(step_record):
    obs = {
        "instruction": step_record["task_metadata"]["public_instruction"],
        "dom_tree": sanitize_dom(step_record["observation"]["dom_tree_sanitized"]),
        "accessibility_tree": sanitize_a11y(step_record["observation"]["accessibility_tree_sanitized"]),
        "screenshot_ref": sanitize_artifact_path(step_record["observation"].get("screenshot_ref_public")),
        "viewport_size": step_record["observation"]["viewport_size"],
        "visible_elements": step_record["observation"].get("visible_elements_public", []),
        "enabled_clickable": step_record["observation"].get("enabled_clickable_public", []),
        "previous_action": step_record.get("previous_action_public"),
        "observed_effect_summary": step_record["observation"].get("observed_effect_public")
    }
    forbidden = {
        "true_hidden_state", "true_regime", "true_control_grammar",
        "true_change_point", "true_reveal_vs_shift", "true_wrong_hypothesis",
        "counterfactual_action_effects", "counterfactual_best_alternative",
        "oracle_regime_action", "oracle_grammar_action", "reward_components",
        "split_id", "ood_type", "template_id"
    }
    serialized = repr(obs)
    for key in forbidden:
        assert key not in obs
        assert key not in serialized
    return obs
```

## 8. Label Definition Ledger


| Label ID | Label Name | Type | Generated From | Used By | Must Not Be Used By | Leakage Risk | Validation Rule |
| --- | --- | --- | --- | --- | --- | --- | --- |
| LABEL-06-001 | true_hidden_state | json | hidden state engine | state supervision/eval | agent observation | state leakage | keys sanitized from public obs |
| LABEL-06-002 | true_regime | enum | hidden regime engine | L_regime/eval | agent observation | regime answer leakage | not in prompt/DOM/text |
| LABEL-06-003 | true_control_grammar | enum | control grammar engine | L_grammar/eval | agent observation | core answer leakage | not in prompt/DOM/text |
| LABEL-06-004 | true_change_point | bool | change scheduler/event engine | change-point F1 | agent observation | event future leakage | post-step label only |
| LABEL-06-005 | true_event_type | enum | event engine | effect/event loss | agent observation | event shortcut | label-only |
| LABEL-06-006 | true_reveal_vs_shift | enum | reveal/shift engine | L_reveal_shift/eval | agent observation | shift shortcut | label-only |
| LABEL-06-007 | true_action_precondition_satisfied | bool | precondition checker | precondition head/eval | agent observation | precondition answer leakage | derived after action |
| LABEL-06-008 | true_action_effect_type | enum | action effect executor | L_action_effect | agent observation | effect answer leakage | post-action only |
| LABEL-06-009 | true_failed_action | bool | effect executor | failed-action loss/metric | agent observation | failure answer leakage | not in obs |
| LABEL-06-010 | true_failure_reason | enum | precondition/effect validator | failure diagnosis eval | agent observation | grammar hint leakage | coarse public summary only |
| LABEL-06-011 | true_recovery_action | action/macro | oracle grammar executor | recovery ranking | agent observation | oracle action leakage | eval/training only |
| LABEL-06-012 | true_progress_delta | float | progress tracker | progress loss/reward | agent observation | reward leakage | post-step only |
| LABEL-06-013 | true_subgoal_state | json | subgoal tracker | progress metric | agent observation | task solution leakage | eval only unless safe |
| LABEL-06-014 | true_task_success | bool | success checker | success rate | agent observation | terminal answer leakage | episode terminal only |
| LABEL-06-015 | true_wrong_hypothesis | bool | compare executed_hypothesis vs true grammar | falsification loss/metric | agent observation | wrong answer leakage | post-hoc only |
| LABEL-06-016 | true_valid_hypothesis_switch | bool | switch validator | valid switch reward/eval | agent observation | switch answer leakage | post-switch only |
| LABEL-06-017 | true_invalid_hypothesis_switch | bool | switch validator | invalid switch penalty/eval | agent observation | switch answer leakage | post-switch only |
| LABEL-06-018 | counterfactual_action_effects | json | counterfactual generator | rollout fidelity target | agent observation | oracle effect leakage | separate counterfactual shard |
| LABEL-06-019 | counterfactual_progress_delta | json | counterfactual generator | rollout value target | agent observation | oracle value leakage | separate shard |
| LABEL-06-020 | counterfactual_failure_risk | json | counterfactual generator | risk prediction/eval | agent observation | oracle risk leakage | separate shard |
| LABEL-06-021 | counterfactual_best_alternative | string | oracle selector | alt rollout fidelity/eval | agent observation | best action leakage | counterfactual-only |
| LABEL-06-022 | oracle_regime_action | action | oracle regime policy | upper bound | agent observation | oracle leakage | eval-only |
| LABEL-06-023 | oracle_grammar_action | action/macro | oracle grammar policy | upper bound/recovery target | agent observation | oracle leakage | eval-only |
| LABEL-06-024 | template_id | string | UI template generator | audit/split | agent observation | template-regime shortcut | hidden metadata |
| LABEL-06-025 | seed | int | seed manager | reproducibility | agent observation | split shortcut | hidden metadata |
| LABEL-06-026 | split_id | string | split manager | eval grouping | agent observation | train/test leakage | hidden metadata |
| LABEL-06-027 | ood_type | enum | split manager | OOD eval | agent observation | OOD answer leakage | hidden metadata |
| LABEL-06-028 | regime_distribution_id | string | generator config | distribution audit | agent observation | label distribution leakage | hidden metadata |
| LABEL-06-029 | grammar_distribution_id | string | generator config | distribution audit | agent observation | label distribution leakage | hidden metadata |
| LABEL-06-030 | leakage_check_flags | json | audit runner | leakage report | agent observation | audit answer leakage | audit-only |
| LABEL-06-031 | generation_config_hash | string | config manager | reproducibility | agent observation | config shortcut | opaque hash |
| LABEL-06-032 | effect_match_score | float | expected-vs-observed comparator | falsification calibration | agent observation direct | score leakage | training/eval only |
| LABEL-06-033 | evidence_strength | float | evidence scorer/oracle | falsification supervision | agent observation direct | falsification answer leakage | label-only |
| LABEL-06-034 | noisy_observation_flag | bool | noise engine | noise vs falsification separation | agent observation | noise answer leakage | label-only |
| LABEL-06-035 | delayed_effect_flag | bool | timing engine | delay vs failure separation | agent observation | delay answer leakage | label-only |
| LABEL-06-036 | repeated_invalid_mapping_flag | bool | history analyzer | failed repetition metric | agent observation | metric answer leakage | eval-only |
| LABEL-06-037 | evidence_to_update_delay | int | trace analyzer | switch delay metric | agent observation | metric answer leakage | eval-only |


## 9. Action-Effect Evidence Schema


| Evidence Field ID | Field | Type | Meaning | Needed For | Leakage Risk | Validation |
| --- | --- | --- | --- | --- | --- | --- |
| EVID-06-001 | previous_action | json | 직전 action record | history/evidence extraction | action source leakage | remove action_source from public obs |
| EVID-06-002 | action_type | enum | click/type/select/scroll/wait 등 | action effect grouping | target semantics shortcut | normalize enum |
| EVID-06-003 | target_element_id | string | internal element ID | trace linking | oracle target leakage | public_ref와 internal_id 분리 |
| EVID-06-004 | target_bbox | tuple | target 위치 | visual grounding/effect analysis | target-only bbox shortcut | all element bboxes 제공 |
| EVID-06-005 | target_visible | bool | target visibility | action precondition eval | precondition answer leakage | public affordance만 제공 |
| EVID-06-006 | target_enabled | bool | enabled 상태 | disabled-button evidence | precondition shortcut | agent는 public enabled만 |
| EVID-06-007 | target_clickable | bool | clickable 상태 | action failure analysis | oracle clickable leakage | clickable computed from public DOM/a11y |
| EVID-06-008 | target_covered_by | string/null | overlay/blocker ID | modal/overlay evidence | blocker label leakage | public overlay ref only |
| EVID-06-009 | precondition_status | enum | satisfied/failed/unknown | precondition loss/eval | hidden precondition leakage | training/eval only |
| EVID-06-010 | pre_state_hash | string | pre hidden/public state hash | state transition check | hidden hash shortcut | public/hidden hash 분리 |
| EVID-06-011 | post_state_hash | string | post state hash | effect detection | hidden hash shortcut | public/hidden hash 분리 |
| EVID-06-012 | dom_diff | json | DOM 변화 | effect prediction | diff includes hidden class | sanitize diff |
| EVID-06-013 | visual_diff_score | float | screenshot 변화량 | visual effect metric | noise/flicker shortcut | threshold calibrated |
| EVID-06-014 | accessibility_diff | json | AX tree 변화 | semantic effect metric | aria leakage | sanitize diff |
| EVID-06-015 | expected_effect_under_current_hypothesis | json/string | current hypothesis가 기대한 effect | falsification | current hypothesis leakage | model-side record, not env obs |
| EVID-06-016 | observed_effect | enum/json | 실제 관측 effect | effect loss/eval | too explicit failure reason | public vs label split |
| EVID-06-017 | effect_match_score | float | expected/observed match | falsification calibration | answer leakage | training/eval only |
| EVID-06-018 | no_effect_flag | bool | 관측 변화 없음 | failed action metric | no-effect=wrong grammar shortcut | delay/noise/failure 분리 |
| EVID-06-019 | delayed_effect_flag | bool | effect 지연 여부 | timing failure separation | delay answer leakage | label-only |
| EVID-06-020 | noisy_observation_flag | bool | noise 여부 | false falsification 방지 | noise answer leakage | label-only |
| EVID-06-021 | failure_reason | enum | 실패 원인 | failure analysis | grammar leakage | coarse public, detailed hidden |
| EVID-06-022 | falsification_candidate | bool | 반증 후보 evidence 여부 | falsification precision/recall | answer leakage | eval/training only |
| EVID-06-023 | evidence_strength | float | evidence 강도 | likelihood ratio proxy | score leakage | not agent input |
| EVID-06-024 | event_type | enum | no-change/reveal/shift/failed/delayed | event loss/eval | event answer leakage | label-only |
| EVID-06-025 | progress_delta | float | task progress 변화 | progress/reward metric | reward leakage | post-step label |
| EVID-06-026 | post_action_latency_ms | int | action 후 안정화까지 시간 | timing/asynchrony eval | latency shortcut | balanced distributions |


## 10. Counterfactual Labeling Contract


| Counterfactual ID | Field | Generated From | Used For | Excluded From | Risk | Guardrail |
| --- | --- | --- | --- | --- | --- | --- |
| CF-06-001 | candidate_action_set | generator/action sampler | counterfactual coverage | agent observation | candidate set too oracle | candidate source logged separately |
| CF-06-002 | current_action_effect | action executor | observed vs predicted effect | agent observation direct label | actual effect leakage | public summary only |
| CF-06-003 | alternative_action_effect | counterfactual generator | alternative rollout fidelity | agent observation | oracle effect leakage | counterfactual-only shard |
| CF-06-004 | counterfactual_progress_delta | counterfactual generator | value target | agent observation | oracle progress leakage | training/eval only |
| CF-06-005 | counterfactual_failure_risk | counterfactual generator | risk prediction/eval | agent observation | oracle risk leakage | hidden shard |
| CF-06-006 | oracle_best_action | counterfactual argmax | oracle upper bound | agent observation | oracle policy leakage | eval-only |
| CF-06-007 | oracle_regime_action | true regime policy | oracle regime upper bound | agent observation | regime oracle leakage | eval-only |
| CF-06-008 | oracle_grammar_action | true grammar policy | oracle grammar upper bound | agent observation | grammar oracle leakage | eval-only |
| CF-06-009 | rollout_fidelity_target | counterfactual effects | train/evaluate rollout model | agent observation | target leakage | supervision only |
| CF-06-010 | topk_alternative_record | hypothesis proposer/oracle | alternative selection eval | agent observation | alt answer leakage | post-hoc only |
| CF-06-011 | counterfactual_generation_method | simulator config | audit/reproducibility | agent observation | generator shortcut | audit-only |
| CF-06-012 | counterfactual_validity_flag | validator | filter invalid actions | agent observation | validity leakage | eval-only |
| CF-06-013 | excluded_from_agent_input | visibility contract | leakage prevention | none | if false, experiment invalid | automated assert |
| CF-06-014 | synthetic_only_limitation | dataset card | claim boundary | none | overclaim real-world counterfactuals | documentation |
| CF-06-015 | counterfactual_shard_ref | storage manager | separate storage/access control | agent observation | path leakage | opaque shard ID |


## 11. Reward and Progress Label Contract


| Reward/Progress ID | Field | Formula/Rule | Generated From | Used By | Risk |
| --- | --- | --- | --- | --- | --- |
| RP-06-001 | progress_score | cumulative normalized subgoal progress | subgoal tracker | progress predictor/eval | dense progress artifact |
| RP-06-002 | progress_delta | progress_t - progress_{t-1} | progress tracker | L_progress/reward | ambiguous subgoal weight |
| RP-06-003 | subgoal_completion | boolean vector over subgoals | task verifier | success decomposition | subgoal leakage if public |
| RP-06-004 | task_success | terminal verifier | success rate | evaluation | success condition overfit |
| RP-06-005 | failed_action_penalty_target | -alpha if true_failed_action | action-effect labels | reward/loss | exploration suppression |
| RP-06-006 | repeated_failure_penalty_target | -alpha_repeat for same invalid mapping | history analyzer | repetition metric/reward | identity of same mapping ambiguous |
| RP-06-007 | recovery_reward_target | positive only if progress after failure | recovery validator | recovery ranking | reward hacking by inducing failure |
| RP-06-008 | valid_switch_reward_target | positive only if evidence-supported switch + progress | switch validator | switch reward | switch hacking |
| RP-06-009 | invalid_switch_penalty_target | negative if switch unsupported/no progress | switch validator | switch regularization | over-penalizes exploration |
| RP-06-010 | compute_cost_target | -beta * planning_units | planner logger | compute-matched eval | discourages useful planning |
| RP-06-011 | normalized_return | sum reward normalized by oracle/budget | reward record | evaluation | normalization can hide failures |


## 12. Metric Support Contract


| Metric ID | Metric | Required Fields | Computation Rule | Leakage Risk | Used In Step |
| --- | --- | --- | --- | --- | --- |
| METRIC-SUP-001 | success rate | task_success, done | mean(task_success) | success label not in agent obs | Step 10 |
| METRIC-SUP-002 | normalized return | reward_components, oracle_return | sum_reward / oracle_or_max_return | oracle denominator leakage | Step 10 |
| METRIC-SUP-003 | compute-matched return | reward_components, compute_cost, planning_units | compare return under same compute budget | compute logging mismatch | Step 10 |
| METRIC-SUP-004 | failed-action repetition rate | action_id, true_failed_action, failure_reason, mapping_id | repeated failed same action/mapping / failed actions | mapping identity ambiguity | Step 10 |
| METRIC-SUP-005 | wrong-control-grammar persistence time | executed_hypothesis, true_control_grammar, step_id | steps until hypothesis aligns after evidence | true grammar hidden label dependence | Step 10 |
| METRIC-SUP-006 | action-interface switch delay | evidence timestamp, rewritten_action timestamp | steps between falsifying evidence and action rewrite | rewrite detection ambiguity | Step 10 |
| METRIC-SUP-007 | recovery delay | failed_action step, progress_delta>0 step | steps to positive progress after failure | progress label weighting | Step 10 |
| METRIC-SUP-008 | alternative rollout fidelity | predicted alt effects, counterfactual_action_effects | accuracy/CE/MSE between predicted and oracle cf effect | synthetic-only oracle | Step 10 |
| METRIC-SUP-009 | falsification precision/recall | falsification_candidate, true_wrong_hypothesis | PR/F1 for current wrong detection | label ambiguity | Step 10 |
| METRIC-SUP-010 | change-point F1 | predicted change, true_change_point | F1 over event boundary | boundary tolerance needed | Step 10 |
| METRIC-SUP-011 | reveal-vs-shift accuracy | predicted event_type, true_reveal_vs_shift | classification accuracy/F1 | ambiguous reveal/state transition | Step 10 |
| METRIC-SUP-012 | progress per compute | progress_delta, planning_units | sum(progress_delta)/sum(planning_units) | compute units comparability | Step 10 |
| METRIC-SUP-013 | evidence-to-update delay | falsifying evidence step, hypothesis update step | delta steps | update definition depends on model | Step 09/10 |


## 13. Split / Versioning / Reproducibility Contract

### 13.1 Reproducibility Fields


| Repro ID | Field | Purpose | Required? | Example | Failure If Missing |
| --- | --- | --- | --- | --- | --- |
| REPRO-06-001 | dataset_version | dataset release ID | YES | 0.1.0 | results cannot be tied to data |
| REPRO-06-002 | schema_version | schema contract ID | YES | schema-06-v0.1 | field semantics drift |
| REPRO-06-003 | generator_version | generator code version | YES | gen-0.3.2 | episode regeneration mismatch |
| REPRO-06-004 | environment_version | browser env version | YES | env-0.2.0 | DOM/render changes |
| REPRO-06-005 | task_template_version | task template version | YES | tasktmpl-0.4 | task distribution drift |
| REPRO-06-006 | ui_template_version | UI template version | YES | uitmpl-0.5 | layout drift |
| REPRO-06-007 | rendering_version | renderer version | YES | chromium-124 | screenshot/layout mismatch |
| REPRO-06-008 | random_seed | global seed | YES | 42 | non-reproducible generation |
| REPRO-06-009 | split_seed | split assignment seed | YES | 73211 | split leakage/overlap |
| REPRO-06-010 | episode_seed | episode-specific seed | YES | 10001 | episode cannot be reproduced |
| REPRO-06-011 | train_valid_test_ood_ids | split IDs | YES | train,valid,test_id,ood_* | eval grouping impossible |
| REPRO-06-012 | config_hash | full generation config hash | YES | sha256:abc | silent config drift |
| REPRO-06-013 | generation_timestamp | generation time | YES | 2026-05-08T... | version tracking impossible |
| REPRO-06-014 | dependency_snapshot | library versions | YES | package-lock/requirements hash | runtime drift |
| REPRO-06-015 | browser_engine_version | browser version | YES | Chromium 124 | render/action drift |
| REPRO-06-016 | screenshot_resolution | image resolution | YES | 1280x720 | visual feature mismatch |
| REPRO-06-017 | viewport_size | viewport config | YES | 1280x720 | responsive regime mismatch |
| REPRO-06-018 | action_space_version | action schema version | YES | action-v0.2 | policy/eval mismatch |
| REPRO-06-019 | counterfactual_generator_version | cf generator version | YES | cfgen-0.1 | rollout target drift |
| REPRO-06-020 | audit_script_version | leakage audit version | YES | audit-0.1 | leakage checks not reproducible |
| REPRO-06-021 | artifact_manifest_hash | screenshots/traces manifest hash | YES | sha256:def | artifact mismatch |


### 13.2 Split Definition Table


| Split ID | Split Name | Included Episodes | Distribution Rule | Held-Out Factor | Leakage Risk | Guardrail |
| --- | --- | --- | --- | --- | --- | --- |
| SPLIT-06-001 | train | all train episodes | seen task/regime/grammar combos | none | template-regime shortcut | balanced sampling |
| SPLIT-06-002 | valid | validation episodes | same distribution as train, disjoint seeds | seeds/templates | seed leakage | seed disjointness check |
| SPLIT-06-003 | test_id | in-domain test | same factor support, disjoint episodes | episodes/seeds | memorization | template/seed disjoint |
| SPLIT-06-004 | ood_regime_recombination | OOD episodes | seen regimes in unseen order | regime sequence | sequence shortcut | held-out sequence list |
| SPLIT-06-005 | ood_control_grammar_shift | OOD episodes | same UI layout, different grammar | grammar mapping | layout shortcut | same-layout different-grammar pairing |
| SPLIT-06-006 | ood_visual_layout | OOD episodes | same grammar, changed visual/layout | layout/theme | visual shortcut | style/position randomization |
| SPLIT-06-007 | ood_dom_text | OOD episodes | same semantics, paraphrased DOM/text | DOM text/roles | text shortcut | paraphrase validation |
| SPLIT-06-008 | ood_task_composition | OOD episodes | seen subtasks in longer unseen composition | subgoal graph | task family leakage | held-out DAG |
| SPLIT-06-009 | ood_timing_async | OOD episodes | same task, timing/delayed effects changed | latency schedule | no-effect shortcut | delay/noisy labels balanced |
| SPLIT-06-010 | ood_reveal_shift_ambiguity | OOD episodes | ambiguous reveal vs shift cases | event semantics | event token leakage | paired examples |
| SPLIT-06-011 | ood_unseen_template | OOD episodes | new UI template family | template | template leakage | template ID hidden and held out |


## 14. Leakage and Shortcut Audit Ledger


| Audit ID | Leakage/Shortcut Risk | Detection Method | Guardrail | Severity | Must Test In |
| --- | --- | --- | --- | --- | --- |
| AUDIT-06-001 | hidden regime이 DOM class name에 새는가? | forbidden token scan over DOM/classes | remove regime/grammar tokens; random class names | CRITICAL | Step 06/05 |
| AUDIT-06-002 | hidden grammar가 text label에 새는가? | scan visible text/accessibility names | paraphrase and ban grammar labels | CRITICAL | Step 06/05 |
| AUDIT-06-003 | split id가 task id를 통해 새는가? | mutual information split-task | split ID hidden; task balanced | HIGH | Step 10 |
| AUDIT-06-004 | OOD type이 agent input에 들어가는가? | prompt serialization assert | ood_type audit-only | CRITICAL | Step 06 |
| AUDIT-06-005 | true labels가 prompt context에 들어가는가? | build_agent_observation unit test | forbidden key assert | CRITICAL | Step 06/07 |
| AUDIT-06-006 | target element id가 oracle처럼 작동하는가? | action success by target_ref baseline | opaque public refs, all elements listed | HIGH | Step 10 |
| AUDIT-06-007 | no-effect flag가 wrong grammar shortcut이 되는가? | correlation no_effect vs wrong_grammar | include delay/noise/valid no-effect cases | CRITICAL | Step 05/10 |
| AUDIT-06-008 | failed_action_evidence가 너무 노골적인가? | LLM zero-shot grammar from evidence only | coarse public evidence; detailed hidden label | HIGH | Step 04/10 |
| AUDIT-06-009 | counterfactual table이 training input으로 새는가? | data loader schema assertion | separate counterfactual shard | CRITICAL | Step 07/08 |
| AUDIT-06-010 | progress label이 observation에 새는가? | obs field scan | reward/progress post-step only | CRITICAL | Step 06 |
| AUDIT-06-011 | template_id가 regime shortcut이 되는가? | MI(template_id,true_regime) | balanced regime per template | HIGH | Step 05/10 |
| AUDIT-06-012 | task_family가 grammar shortcut이 되는가? | MI(task_family,true_grammar) | multi-grammar per task family | HIGH | Step 05 |
| AUDIT-06-013 | visual layout이 grammar shortcut이 되는가? | vision-only classifier test | layout randomization + paired controls | HIGH | Step 10 |
| AUDIT-06-014 | seed ordering이 split shortcut이 되는가? | seed range overlap/ordering check | randomized IDs; disjoint seed spaces | MEDIUM | Step 06 |
| AUDIT-06-015 | action id가 target semantics를 직접 노출하는가? | action token scan | normalize action args, opaque refs | HIGH | Step 06 |
| AUDIT-06-016 | hidden precondition status가 agent input으로 새는가? | obs extraction assert | public UI affordance only | CRITICAL | Step 06 |
| AUDIT-06-017 | accessibility label이 hidden grammar를 노출하는가? | AX forbidden token scan | sanitize_a11y; paraphrase | HIGH | Step 05/06 |
| AUDIT-06-018 | screenshot filename/path가 split/regime을 노출하는가? | path regex scan | UUID paths; manifest hidden | HIGH | Step 06 |
| AUDIT-06-019 | state hash가 hidden state shortcut이 되는가? | public obs field scan | public/hidden hash separation | MEDIUM | Step 06 |
| AUDIT-06-020 | reward field가 agent input으로 들어가는가? | obs extraction assert | reward after-action record only | CRITICAL | Step 06 |
| AUDIT-06-021 | generation_config_hash가 distribution shortcut이 되는가? | agent input scan | audit-only | MEDIUM | Step 06 |
| AUDIT-06-022 | counterfactual shard path가 oracle name을 담는가? | artifact path scan | opaque shard refs | HIGH | Step 06 |
| AUDIT-06-023 | success condition text가 answer를 노출하는가? | prompt scan | success condition eval-only | HIGH | Step 06 |
| AUDIT-06-024 | public observed_effect가 true_failure_reason을 그대로 말하는가? | public/hidden evidence diff audit | coarse summary only | HIGH | Step 06 |
| AUDIT-06-025 | DOM diff가 hidden class removal을 노출하는가? | diff sanitizer test | sanitize diff before public use | CRITICAL | Step 06/07 |
| AUDIT-06-026 | episode length가 split/OOD shortcut이 되는가? | length distribution test | length balancing | MEDIUM | Step 10 |


## 15. Schema Stress Test Ledger


| Stress ID | Stress Case | Schema Failure Mode | Required Revision | Affected Later Step |
| --- | --- | --- | --- | --- |
| STRESS-06-001 | delayed effect와 no effect가 혼동된다 | delayed action을 failed_action으로 잘못 label | delayed_effect_flag와 stabilization window 추가 | Step 06/10 |
| STRESS-06-002 | visual diff는 작지만 semantic effect는 크다 | progress가 있는데 visual_diff_score 낮음 | semantic DOM/a11y diff와 progress label 분리 | Step 08/10 |
| STRESS-06-003 | DOM diff는 크지만 task progress는 없다 | cosmetic update가 progress로 오인 | progress tracker는 subgoal graph 기반 | Step 10 |
| STRESS-06-004 | action은 실패했지만 current hypothesis는 맞았다 | execution/timing failure를 grammar failure로 오분류 | failure_reason과 wrong_hypothesis 분리 | Step 08/10 |
| STRESS-06-005 | action은 성공했지만 wrong grammar persistence가 있었다 | 우연히 성공한 wrong mapping 미포착 | executed_hypothesis record와 true grammar 비교 | Step 09/10 |
| STRESS-06-006 | recovery action이 여러 개 가능하다 | true_recovery_action 단일 label 과도 | set-valued recovery action label 허용 | Step 08 |
| STRESS-06-007 | alternative hypothesis가 여러 개 plausible하다 | counterfactual_best_alternative 단일화 위험 | ranked alternatives + ties 저장 | Step 09 |
| STRESS-06-008 | counterfactual best action이 action space에 없다 | oracle action이 agent 불가능 action | oracle action must be executable check | Step 07/10 |
| STRESS-06-009 | progress reward가 subgoal 설계에 과적합된다 | dense reward가 benchmark-specific | subgoal weight audit and ablation | Step 08/10 |
| STRESS-06-010 | hidden regime label이 human-interpretable하지 않다 | reviewer가 label arbitrary 공격 | taxonomy-derived label rules 저장 | Step 03/06 |
| STRESS-06-011 | action-effect evidence가 noisy해서 falsification이 잘못된다 | false falsification 증가 | noisy_observation_flag와 calibration label | Step 09 |
| STRESS-06-012 | accessibility tree와 DOM tree가 충돌한다 | agent observation inconsistent | cross-modal consistency flags | Step 07 |
| STRESS-06-013 | screenshot이 늦게 업데이트된다 | visual diff stale | post_action_latency_ms/stabilization window | Step 05/06 |
| STRESS-06-014 | action target이 사라진다 | detached DOM 오류 | stale_target flag and failure_reason | Step 05/06 |
| STRESS-06-015 | scroll action effect가 누적적이라 step label이 어렵다 | per-step effect 분해 실패 | scroll_delta and cumulative_visible_items fields | Step 06/10 |
| STRESS-06-016 | multi-step wizard에서 regime이 빠르게 바뀐다 | change-point label 폭증 | minimum event duration + schedule log | Step 05/10 |
| STRESS-06-017 | same UI template에서 grammar만 바뀌어 label ambiguity | visual clue 없이 label arbitrary | action-effect evidence required after action | Step 05/09 |
| STRESS-06-018 | UI text paraphrase가 task intent를 바꿔버린다 | instruction label mismatch | paraphrase semantic validation | Step 05/06 |
| STRESS-06-019 | trace length가 너무 길어 memory 문제가 생긴다 | training/eval pipeline overload | trace truncation and summary fields | Step 07/10 |
| STRESS-06-020 | OOD split이 너무 어렵거나 너무 쉽다 | result 해석 불가 | difficulty calibration metadata | Step 10 |
| STRESS-06-021 | template-regime balance가 깨진다 | shortcut baseline 급상승 | balance report required | Step 10 |


## 16. Dataset Card / Documentation Requirements


| Card Section | Required Content | Why Needed | Risk If Missing |
| --- | --- | --- | --- |
| motivation | 왜 synthetic Web/GUI dataset이 필요한지; real benchmark 한계 | mechanism 검증 목적 명확화 | toy benchmark 공격 |
| composition | task family, regime, grammar, OOD split 구성 | coverage와 balance 검증 | distribution 불명확 |
| generation process | procedural generation, seed, templates, hidden engines | 재현성 | hidden label arbitrary 공격 |
| labels | hidden/supervision/eval/counterfactual label 정의 | loss/metric 의미 명확화 | label misuse |
| hidden labels | agent input에서 제외되는 label 목록 | leakage 방지 | 실험 무효 |
| intended use | FRCG-WM mechanism 학습/평가 | 과장 방지 | real-world generalization 과장 |
| prohibited use | real-world deployment benchmark로 단독 사용 금지 | 오용 방지 | external validity 과장 |
| leakage guardrails | forbidden token scan, split balance, path sanitizer | 실험 신뢰성 | shortcut 미검출 |
| split definitions | train/valid/test/OOD split rule | 재현 가능한 비교 | split 혼동 |
| OOD definitions | held-out factors와 claim 연결 | generalization 해석 | OOD claim 약화 |
| limitations | counterfactual synthetic-only, real latency/website diversity 한계 | 정직한 scope | reviewer 신뢰 저하 |
| ethical/security considerations | real account/session 없음, automation safety, synthetic data | 안전성/배포 맥락 | 보안/개인정보 오해 |
| reproducibility | versions, seeds, hashes, artifact manifest | 재실험 가능성 | 결과 재현 불가 |
| versioning | schema/generator/env/action space version policy | 장기 유지보수 | version drift |


## 17. Required Design Revisions From Data Schema


| Revision ID | Schema Issue | Required Revision | Affected Later Step | Severity |
| --- | --- | --- | --- | --- |
| DATA-REV-001 | hidden labels and public observation mixed in one JSON | visibility extractor를 공식 API로 강제 | Step 07/08/10 | CRITICAL |
| DATA-REV-002 | counterfactual labels stored near public obs | counterfactual-only shard로 분리 | Step 07/09 | CRITICAL |
| DATA-REV-003 | no-effect와 wrong grammar가 shortcut으로 연결 | delayed/noisy/valid no-effect label 추가 | Step 08/10 | CRITICAL |
| DATA-REV-004 | progress label이 observation으로 leak될 위험 | reward/progress record는 post-step label only | Step 08 | CRITICAL |
| DATA-REV-005 | current hypothesis 정의가 불명확 | executed_hypothesis/model_record를 trace에 저장 | Step 09 | HIGH |
| DATA-REV-006 | multiple valid recovery actions | set-valued recovery labels 허용 | Step 08/10 | HIGH |
| DATA-REV-007 | event boundary ambiguity | event_start/end/tolerance field 추가 | Step 10 | HIGH |
| DATA-REV-008 | template-regime shortcut | MI audit와 balanced sampling 필요 | Step 05/10 | CRITICAL |
| DATA-REV-009 | screenshot/path leakage | opaque artifact naming + manifest hidden | Step 06 | HIGH |
| DATA-REV-010 | real-world counterfactual 없음 | synthetic-only supervision limitation 명시 | Step 09/10 | HIGH |
| DATA-REV-011 | DOM/AX/screenshot mismatch | cross-modal consistency audit field 추가 | Step 07 | MEDIUM |


## 18. Handoff to Later Steps


| Handoff ID | Target Step | What Must Be Used | What Must Be Verified | What Must Not Be Assumed |
| --- | --- | --- | --- | --- |
| HANDOFF-06-001 | 07_LATENT_ARCHITECTURE_DESIGN.md | true_hidden_state/true_regime/true_control_grammar/true_change_point, visibility contract | latent supervision이 leakage 없이 쓰이는지 | hidden labels가 inference input이라고 가정 금지 |
| HANDOFF-06-002 | 08_LOSS_REWARD_TRAINING_OBJECTIVE.md | label ledger, reward/progress contract, action-effect evidence schema | 각 loss가 어떤 label을 쓰는지와 reward hacking guardrail | reward field가 observation에 있다고 가정 금지 |
| HANDOFF-06-003 | 09_PLANNING_THEORY_ALGORITHM.md | counterfactual contract, current/alternative hypothesis records, evidence fields | falsification score와 rollout fidelity가 어떤 field로 계산되는지 | counterfactual table을 runtime input으로 사용한다고 가정 금지 |
| HANDOFF-06-004 | 10_EVALUATION_BASELINE_ABLATION.md | metric support contract, split definitions, leakage audit | metric 계산식과 OOD split 방어력 | success rate만으로 claim 증명 금지 |


## 19. Updated Risk / Unknown Ledger


| Risk ID | Risk / Unknown | Triggered By | Why It Matters | Resolution Path | Can Be Final Claim? |
| --- | --- | --- | --- | --- | --- |
| DATA-RISK-001 | hidden label leakage가 완전히 차단됐는지 | visibility contract | 실험 무효 가능 | unit test + adversarial classifier | NO |
| DATA-RISK-002 | counterfactual label이 training input으로 새는지 | counterfactual shard | oracle leakage | data loader assert | NO |
| DATA-RISK-003 | grammar label taxonomy가 arbitrary인지 | label definition | reviewer 공격 | taxonomy rule + ablation | NO |
| DATA-RISK-004 | event/reveal/shift boundary ambiguity | event labels | metric noise | tolerance window + human-readable rule | NO |
| DATA-RISK-005 | no-effect shortcut | action-effect schema | wrong grammar metric 오염 | delay/noise/no-effect balance | NO |
| DATA-RISK-006 | DOM/AX/screenshot 불일치 | observation schema | model confusion | cross-modal consistency flag | NO |
| DATA-RISK-007 | progress label 과적합 | reward/progress contract | reward hacking | subgoal ablation and normalization | NO |
| DATA-RISK-008 | OOD split leakage | split metadata | generalization claim 무효 | held-out factor audit | NO |
| DATA-RISK-009 | template/task-regime mutual information 높음 | audit ledger | shortcut learning | balanced generation | NO |
| DATA-RISK-010 | real-world counterfactual unavailable | counterfactual contract | external validity 한계 | synthetic-only limitation | NO |
| DATA-RISK-011 | trace size 너무 큼 | schema design | storage/training bottleneck | artifact manifest + compression | NO |
| DATA-RISK-012 | action target ID가 oracle처럼 작동 | action schema | action selection shortcut | opaque refs and all-element list | NO |
| DATA-RISK-013 | valid recovery action이 여러 개 | label definition | single-label loss 부적절 | set-valued labels | NO |
| DATA-RISK-014 | delayed effect를 failed action으로 오분류 | evidence schema | false falsification | stabilization window | NO |
| DATA-RISK-015 | dataset card 불충분 | documentation | reproducibility/ethics 부족 | dataset card checklist | NO |
| DATA-RISK-016 | seed/config hash가 shortcut | audit metadata | hidden metadata leakage | never in agent input | NO |


## 20. Quality Gate Result


| Gate ID | Gate | PASS/FAIL/PARTIAL | Evidence | If Not PASS, Blocker |
| --- | --- | --- | --- | --- |
| QG-06-01 | 00/01/02/03/04/05 refs imported | PASS | Imported References 70개 이상 |  |
| QG-06-02 | search expansion 25개 이상 수행 | PASS | Search Ledger 25개 |  |
| QG-06-03 | data visibility contract 40개 이상 작성 | PASS | Visibility 항목 45개 |  |
| QG-06-04 | hierarchical schema 70개 이상 field 정의 | PASS | 12개 schema level, 70개 이상 field |  |
| QG-06-05 | agent observation extraction contract 작성 | PASS | Section 7 table + pseudo-code |  |
| QG-06-06 | label definition 35개 이상 작성 | PASS | Label 37개 |  |
| QG-06-07 | action-effect evidence schema 25개 이상 작성 | PASS | Evidence field 26개 |  |
| QG-06-08 | counterfactual labeling contract 15개 이상 작성 | PASS | Counterfactual 15개 |  |
| QG-06-09 | metric support contract 작성 | PASS | Metric support 13개 |  |
| QG-06-10 | split/versioning/reproducibility contract 작성 | PASS | Repro 21개, split 11개 |  |
| QG-06-11 | leakage audit 25개 이상 작성 | PASS | Audit 26개 |  |
| QG-06-12 | schema stress test 20개 이상 작성 | PASS | Stress 21개 |  |
| QG-06-13 | dataset card requirements 작성 | PASS | Dataset card 14개 section |  |
| QG-06-14 | no hidden label included in agent observation | PASS | visibility contract + extraction assert |  |


## 21. Final Statement of This File

```text
06_DATA_SCHEMA_AND_LABELING.md is a data contract file, not a model architecture or final evaluation file.

The most critical schema decisions are:
- agent observation, training supervision, evaluation-only label, counterfactual-only label, audit metadata를 visibility bucket으로 분리한다.
- true_regime, true_control_grammar, true_change_point, true_reveal_vs_shift, counterfactual_action_effects는 agent observation에 절대 포함하지 않는다.
- action-effect evidence schema를 중심으로 falsification, recovery, persistence, rollout fidelity, progress metric이 모두 계산 가능해야 한다.

The strongest leakage guardrails are:
- build_agent_observation()에서 forbidden key와 forbidden serialized token을 assert한다.
- hidden label/counterfactual record는 agent-safe observation과 물리적으로 분리된 shard 또는 filtered view로 제공한다.
- DOM/AX/text/screenshot path/template/task/seed 기반 shortcut을 leakage audit으로 정기 검출한다.

The schema still leaves the following risks:
- synthetic counterfactual labels는 실제 Web/GUI에서 직접 관측할 수 없으므로 external validity가 제한된다.
- regime/control grammar label은 taxonomy와 generator rule에 의존하므로 arbitrary label 공격을 받을 수 있다.
- delayed/noisy/no-effect event를 잘못 분리하면 falsification metric이 오염된다.

The next required file is:
07_LATENT_ARCHITECTURE_DESIGN.md
```

---

## 22. Implementation-Ready Contract Addendum

이 섹션은 Claude Code가 실제 파일/코드를 작성할 때 바로 사용할 수 있는 구현 계약이다. 이 섹션은 Step 06의 schema contract를 실행 가능한 형태로 압축한다.

### 22.1 Strongly Typed Record Contract

아래 구조는 Pydantic/TypedDict/Dataclass 중 어떤 방식으로 구현해도 되지만, 의미는 유지해야 한다.

```python
from typing import Any, Literal, Optional, TypedDict

VisibilityBucket = Literal[
    "AGENT_OBSERVATION",
    "TRAINING_SUPERVISION",
    "EVALUATION_ONLY",
    "COUNTERFACTUAL_ONLY",
    "AUDIT_METADATA",
]

class AgentObservation(TypedDict, total=False):
    instruction: str
    dom_tree: dict[str, Any]
    accessibility_tree: Any
    screenshot_ref: Optional[str]
    viewport_size: tuple[int, int]
    visible_elements: list[dict[str, Any]]
    enabled_clickable: list[dict[str, Any]]
    previous_action: Optional[dict[str, Any]]
    observed_effect_summary: Optional[Any]

class HiddenLabels(TypedDict, total=False):
    true_hidden_state: dict[str, Any]
    true_regime: str
    true_control_grammar: str
    true_change_point: bool
    true_event_type: str
    true_reveal_vs_shift: str
    true_action_precondition_satisfied: bool
    true_action_effect_type: str
    true_failed_action: bool
    true_failure_reason: str
    true_progress_delta: float
    true_wrong_hypothesis: bool
    true_valid_hypothesis_switch: bool
    true_invalid_hypothesis_switch: bool

class CounterfactualRecord(TypedDict, total=False):
    counterfactual_action_effects: dict[str, Any]
    counterfactual_progress_delta: dict[str, float]
    counterfactual_failure_risk: dict[str, float]
    counterfactual_best_alternative: str
    oracle_regime_action: str
    oracle_grammar_action: str

class AuditMetadata(TypedDict, total=False):
    split_id: str
    ood_type: Optional[str]
    template_id: str
    seed: int
    generation_config_hash: str
    leakage_check_flags: dict[str, bool]
```

### 22.2 Non-Negotiable Runtime Assertions

```python
FORBIDDEN_AGENT_KEYS = {
    "true_hidden_state",
    "true_regime",
    "true_control_grammar",
    "true_change_point",
    "true_event_type",
    "true_reveal_vs_shift",
    "true_action_precondition_satisfied",
    "true_action_effect_type",
    "true_failed_action",
    "true_failure_reason",
    "true_recovery_action",
    "true_progress_delta",
    "true_wrong_hypothesis",
    "true_valid_hypothesis_switch",
    "true_invalid_hypothesis_switch",
    "counterfactual_action_effects",
    "counterfactual_progress_delta",
    "counterfactual_failure_risk",
    "counterfactual_best_alternative",
    "oracle_regime_action",
    "oracle_grammar_action",
    "reward_components",
    "split_id",
    "ood_type",
    "template_id",
    "seed",
    "generation_config_hash",
}

FORBIDDEN_AGENT_TOKENS = {
    "modal_blocked",
    "remove_blocker_before_target_action",
    "true_regime",
    "true_control_grammar",
    "counterfactual",
    "oracle_grammar_action",
    "ood_control_grammar_shift",
}


def assert_agent_observation_safe(obs: dict) -> None:
    serialized = repr(obs)
    for key in FORBIDDEN_AGENT_KEYS:
        assert key not in obs, f"Forbidden key leaked into agent observation: {key}"
        assert key not in serialized, f"Forbidden serialized key leaked: {key}"
    for token in FORBIDDEN_AGENT_TOKENS:
        assert token not in serialized, f"Forbidden token leaked into agent observation: {token}"
```

### 22.3 Data Loader View Contract

| Loader View | Contains | Excludes | Used By |
|---|---|---|---|
| `storage_view` | full episode record | nothing | offline audit/debug only |
| `agent_view` | sanitized instruction/DOM/AX/screenshot/previous action/effect | all `true_*`, `counterfactual_*`, `oracle_*`, split/template/seed | inference, base agent, planner |
| `supervision_view` | `true_*` labels and selected counterfactual targets | raw private generator internals | training losses |
| `evaluation_view` | hidden labels, metrics fields, oracle upper bound labels | agent prompt | metrics and ablation |
| `audit_view` | leakage flags, seed/version/config/template metadata | agent prompt | dataset validation |

Implementation rule:

```text
No training/evaluation script may call storage_view directly as agent input.
All agent-facing code must call build_agent_observation() or an equivalent sanitizer.
```

### 22.4 Metric Field Dependency Matrix

| Metric | Minimal Required Fields | If Missing |
|---|---|---|
| wrong-control-grammar persistence time | `executed_hypothesis`, `true_control_grammar`, `falsifying_evidence_step`, `step_id` | core metric cannot be computed |
| failed-action repetition rate | `action_type`, `target_element_id`, `true_failed_action`, `failure_reason`, history | failure loop metric invalid |
| recovery delay | `true_failed_action`, `progress_delta`, `step_id` | recovery claim invalid |
| action-interface switch delay | `base_action`, `rewritten_action`, `falsifying_evidence_step`, `step_id` | rewrite timing claim invalid |
| falsification precision/recall | predicted `falsification_score`, `true_wrong_hypothesis` | falsification claim invalid |
| alternative rollout fidelity | predicted alternative effects, `counterfactual_action_effects` | rollout claim invalid |
| compute-normalized return | `reward_components`, `planning_units`, `rollout_steps`, `compute_cost` | planning efficiency claim invalid |
| reveal-vs-shift accuracy | predicted event, `true_reveal_vs_shift` | taxonomy/event claim invalid |

### 22.5 Required Dataset Validation Commands

아래 명령은 예시이며, 실제 path는 프로젝트 구조에 맞게 조정한다.

```bash
python scripts/validate_schema.py \
  --input data/frcgwm_synth/train.jsonl \
  --schema configs/schema_v06.json

python scripts/audit_agent_observation_leakage.py \
  --input data/frcgwm_synth/train.jsonl \
  --fail-on-forbidden-token

python scripts/check_split_disjointness.py \
  --dataset-root data/frcgwm_synth \
  --keys episode_id,template_id,seed,subgoal_graph_hash

python scripts/check_metric_fields.py \
  --input data/frcgwm_synth/test_id.jsonl \
  --metrics wrong_grammar_persistence,recovery_delay,rollout_fidelity
```

### 22.6 MVE Implementation Gate

| Gate ID | Gate | Pass Condition | If Fail |
|---|---|---|---|
| MVE-06-01 | storage/agent/supervision/evaluation/audit view 분리 | five view functions exist | dataset loader blocked |
| MVE-06-02 | forbidden key assertion | all agent observations pass | experiment invalid |
| MVE-06-03 | hidden label availability | `true_regime`, `true_control_grammar`, `true_wrong_hypothesis` non-null | supervised objective blocked |
| MVE-06-04 | counterfactual shard separation | counterfactual fields absent from agent view | rollout fidelity invalid |
| MVE-06-05 | metric field completeness | core metric dependency matrix complete | Step 10 blocked |
| MVE-06-06 | split disjointness | no seed/template overlap where forbidden | OOD claim invalid |
| MVE-06-07 | audit flags | no critical leakage flags | dataset release blocked |

### 22.7 Claude Code Do/Don't Checklist

| Do | Don't |
|---|---|
| `build_agent_observation()`을 모든 agent call 앞에 사용하라. | full JSON episode를 prompt에 그대로 넣지 마라. |
| hidden/counterfactual/audit fields를 물리적으로 다른 view로 분리하라. | `true_*` 또는 `counterfactual_*`를 public dict에 섞지 마라. |
| metric별 required fields를 먼저 체크하라. | 실험 후 metric 계산이 안 되는 상태로 training을 시작하지 마라. |
| split/template/seed metadata는 audit-only로 둬라. | 파일명/path에 split/regime/grammar를 넣지 마라. |
| delayed/noisy/no-effect/failed action을 구분하라. | no-effect를 곧바로 wrong grammar로 label하지 마라. |
| counterfactual은 synthetic-only limitation으로 문서화하라. | real benchmark에도 counterfactual oracle이 있다고 쓰지 마라. |

---

## 23. Final Upgrade Statement

이 `06_DATA_SCHEMA_AND_LABELING.md`는 schema contract이며, model architecture나 final evaluation이 아니다.

이 파일의 10점급 핵심은 다음이다.

1. agent observation과 hidden/counterfactual/evaluation/audit record를 구조적으로 분리한다.
2. `wrong-control-grammar persistence`, `falsification`, `alternative rollout fidelity`, `recovery delay`, `compute-normalized return`이 실제 field chain으로 계산 가능하다.
3. Claude Code가 구현할 때 어떤 view를 사용해야 하는지 명확한 routing과 runtime assertion을 제공한다.
4. synthetic counterfactual label의 강점과 real-world extension limitation을 동시에 명시한다.
5. Step 07~10이 이 schema 위에서 architecture/loss/planning/evaluation을 구현할 수 있도록 MVE field subset과 validation commands를 제공한다.

다음 파일:

```text
07_LATENT_ARCHITECTURE_DESIGN.md
```

