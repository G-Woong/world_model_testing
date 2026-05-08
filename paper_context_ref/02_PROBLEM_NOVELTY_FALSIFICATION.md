---
file_id: STEP-02
title: Problem Definition and Novelty Falsification for FRCG-WM
version: v1.0
status: problem_falsification_contract_not_final_claim
language: ko
depends_on:
  - 00_MASTER_REFERENCE.md
  - 01_RELATED_WORK_THREAT_MAP.md
purpose:
  - wrong-control-grammar hypothesis persistence가 독립적인 Web/GUI agent failure mode인지 반증 중심으로 검증한다.
  - action failure, visual grounding failure, planning failure, action-effect verification failure, robustness failure, self-correction failure, next-state world-model failure, tree-search failure와 분리 가능한지 확인한다.
  - 후속 Step 03~10이 사용할 조건부 문제정의, minimal counterexample suite, metric contract, schema 요구사항, ablation 요구사항을 산출한다.
  - Claude Code가 후속 파일 작성 또는 구현 중 필요한 context를 확장적으로 읽을 수 있도록 routing과 handoff를 명시한다.
forbidden:
  - 최종 논문 thesis 확정 금지
  - novelty 최종 확정 금지
  - final introduction 작성 금지
  - 최종 architecture/loss/reward/planning/evaluation 설계 확정 금지
  - WebWorld, WMA, WAC, CUWM, VeriGUI, AgentRx, StressWeb 계열 threat를 약하게 축소 금지
  - synthetic counterexample를 empirical result처럼 작성 금지
  - `control grammar`를 정의 없이 사용 금지
  - `wrong hypothesis`를 측정 불가능한 심리적 표현으로 방치 금지
next_files:
  - 03_CORE_CONCEPT_TAXONOMY.md
  - 04_TEXT_ONLY_SMOKE_TESTBED.md
  - 05_SYNTHETIC_WEB_GUI_ENVIRONMENT.md
  - 06_DATA_SCHEMA_AND_LABELING.md
  - 07_LATENT_ARCHITECTURE_DESIGN.md
  - 08_LOSS_REWARD_TRAINING_OBJECTIVE.md
  - 09_PLANNING_THEORY_ALGORITHM.md
  - 10_EVALUATION_BASELINE_ABLATION.md
---

# 02_PROBLEM_NOVELTY_FALSIFICATION.md

## 1. File Purpose

이 파일은 introduction 초안이 아니다. 이 파일은 `wrong-control-grammar hypothesis persistence`라는 문제정의가 실제로 독립적인 failure mode인지 **먼저 죽여보는 반증 파일**이다.

이번 Step의 기본 태도는 다음이다.

```text
이 현상이 기존 action failure, visual grounding failure, planning failure,
action-effect verification failure, robustness failure, self-correction failure,
world-model prediction failure, tree-search failure의 재포장이라면 즉시 폐기한다.
```

따라서 이 파일에서 살아남는 claim도 최종 claim이 아니다. 살아남는 claim은 `CONDITIONAL_SURVIVAL` 또는 `UNKNOWN_NEEDS_EXPERIMENT` 상태로 후속 Step에 넘긴다.

최종 claim 승격 조건은 다음이다.

1. competing explanation과 분리되는 최소 반례가 있어야 한다.
2. metric으로 계량 가능해야 한다.
3. ablation 제거 시 해당 metric이 악화되어야 한다.
4. synthetic Web/GUI 환경에서 ground-truth label로 검증 가능해야 한다.
5. real benchmark에서는 weak measurement 또는 qualitative trace라도 가능해야 한다.
6. Step 10에서 compute-matched baseline과 비교되어야 한다.
7. direct threat paper 대비 “같은 문제를 이미 풀었다”는 공격을 방어해야 한다.

---

## 2. Claude Code Context Routing

Claude Code는 이 파일을 읽을 때 아래 routing을 따른다.

| User Intent / Task | Must Read First | Then Read | Do Not Assume |
|---|---|---|---|
| 문제정의 재작성 | `02_PROBLEM_NOVELTY_FALSIFICATION.md` §4~9 | `01`, `03`, `10` | wrong-control-grammar가 이미 독립 failure라고 가정 금지 |
| `control grammar` 정의 수정 | `03_CORE_CONCEPT_TAXONOMY.md` | `02` §5~8, `06`, `07` | grammar가 action precondition 하나라고 가정 금지 |
| minimal counterexample 구현 | `02` §6 | `04`, `05`, `06` | hand-crafted toy 예시만으로 충분하다고 가정 금지 |
| metric 구현 | `02` §8 | `06`, `10` | persistence metric을 failed action count로 축소 금지 |
| architecture 설계 | `07_LATENT_ARCHITECTURE_DESIGN.md` | `02` §5, §9, §13 | regime/grammar 분리가 학습 가능하다고 선결정 금지 |
| planning algorithm 설계 | `09_PLANNING_THEORY_ALGORITHM.md` | `02` §8~11 | falsification을 confidence threshold나 failed-action flag로 축소 금지 |
| evaluation/ablation 설계 | `10_EVALUATION_BASELINE_ABLATION.md` | `02` §9~14 | success rate만으로 문제정의 검증 금지 |
| final blueprint 통합 | `FINAL_RESEARCH_BLUEPRINT.md` | `02` 전체 + `00`~`10` | `CONDITIONAL_SURVIVAL`을 final claim으로 승격 금지 |

---

## 3. Verification Status Policy

| Status | 의미 | Final Claim 사용 여부 |
|---|---|---:|
| `COLLAPSE` | 기존 설명으로 충분히 설명됨 | 불가 |
| `WEAK_SURVIVAL` | 용어는 유용하나 novelty가 약함 | 불가. background/framing 가능 |
| `CONDITIONAL_SURVIVAL` | 특정 실험 조건에서만 살아남을 수 있음 | 실험 전에는 final claim 불가 |
| `STRONG_SURVIVAL` | 여러 competing explanation을 통과함 | Step 10 근거 후 가능 |
| `UNKNOWN_NEEDS_EXPERIMENT` | 실험 없이는 판정 불가 | 불가 |
| `BLOCKER` | 해결되지 않으면 claim 자체가 무효 | 불가 |

원칙:

```text
이 파일에서는 STRONG_SURVIVAL을 거의 부여하지 않는다.
대부분의 문제정의는 CONDITIONAL_SURVIVAL 또는 UNKNOWN_NEEDS_EXPERIMENT여야 한다.
```

---

## 4. Citation-Grade Source Anchor Table

> 이 표는 Step 01의 threat map을 문제정의 반증에 다시 연결하기 위한 anchor다.  
> 실제 논문 작성 시에는 DOI/arXiv/OpenReview/GitHub/official project page를 Step 01/10에서 다시 고정해야 한다.

| Anchor ID | Work / Benchmark | URL / Identifier | Why It Matters For Falsification | Threat Type |
|---|---|---|---|---|
| SRC-02-001 | WebArena | https://arxiv.org/abs/2307.13854 | realistic web benchmark. synthetic-only claim을 약화시키고 external validation 필요성을 만든다. | BENCHMARK_ANCHOR |
| SRC-02-002 | VisualWebArena | https://arxiv.org/abs/2401.13649 | visual grounding competing explanation의 핵심 anchor다. | VISUAL_GROUNDING_COMPETING_EXPLANATION |
| SRC-02-003 | OSWorld | https://arxiv.org/abs/2404.07972 | real computer-use task에서 GUI grounding/operational knowledge failure를 보여주는 anchor다. | COMPUTER_USE_BENCHMARK |
| SRC-02-004 | VeriGUI: Don't Act Blindly | https://arxiv.org/abs/2604.05477 | action-effect verification, failure loop reduction, recovery training을 직접 다루는 가장 강한 threat다. | VERIFICATION_DIRECT_THREAT |
| SRC-02-005 | VAGEN | https://arxiv.org/html/2602.00575v1 | proactive verification/probing agent. evidence collection과 falsification의 차이를 요구한다. | VERIFICATION_OVERLAP |
| SRC-02-006 | WebWorld | Step 01에서 확인된 web world model threat | generic web world model novelty를 약화시킨다. | WORLD_MODEL_DIRECT_THREAT |
| SRC-02-007 | WMA | Step 01에서 확인된 web-agent world model threat | action outcome simulation으로 policy selection을 이미 수행한다. | WORLD_MODEL_DIRECT_THREAT |
| SRC-02-008 | WAC | Step 01에서 확인된 action correction threat | consequence simulation/action correction과 rewrite claim이 겹친다. | ACTION_CORRECTION_DIRECT_THREAT |
| SRC-02-009 | CUWM | Step 01에서 확인된 computer-use world model threat | frozen agent + test-time world-model search claim을 위협한다. | WORLD_MODEL_DIRECT_THREAT |
| SRC-02-010 | StressWeb / web robustness benchmark family | Step 01에서 확인된 robustness benchmark threat | altered interaction semantics가 grammar shift와 겹칠 수 있다. | ROBUSTNESS_DIRECT_THREAT |
| SRC-02-011 | AgentRx | Step 01에서 확인된 failure diagnosis threat | failure taxonomy/critical failure step 분석이 problem novelty를 약화시킨다. | FAILURE_DIAGNOSIS_THREAT |
| SRC-02-012 | Agent Q / MCTS-style web agents | Step 01에서 확인된 tree-search threat | alternative rollout이 단순 search로 보일 위험을 만든다. | PLANNING_SEARCH_THREAT |

---

## 5. Imported References

| Imported ID | Source File | Type | Meaning | Why It Matters | Priority |
|---|---|---|---|---|---|
| REF-CORE-001 | 00_MASTER_REFERENCE.md | Core | wrong-control-grammar hypothesis persistence | 전체 문제정의의 중심이다 | CRITICAL |
| REF-CORE-002 | 00_MASTER_REFERENCE.md | Core | latent regime/control-grammar world model | 문제정의가 model 설계와 연결되는지 확인해야 한다 | CRITICAL |
| REF-CORE-003 | 00_MASTER_REFERENCE.md | Core | action-effect evidence based falsification | verification과 다른지 검증해야 한다 | CRITICAL |
| REF-CORE-004 | 00_MASTER_REFERENCE.md | Core | current-vs-alternative hypothesis rollout | tree search와 다른지 검증해야 한다 | CRITICAL |
| REF-CORE-005 | 00_MASTER_REFERENCE.md | Core | intent-to-action rewrite | 단순 recovery/action correction인지 검증해야 한다 | CRITICAL |
| REF-CORE-006 | 00_MASTER_REFERENCE.md | Core | decision-relevant compute reallocation | uncertainty gate와 구분되어야 한다 | HIGH |
| REF-CORE-007 | 00_MASTER_REFERENCE.md | Core | Frozen Base VLM/LLM + reliability module | base model 개선 효과와 분리해야 한다 | HIGH |
| REF-CORE-008 | 00_MASTER_REFERENCE.md | Core | text-only smoke test | minimal counterexample를 빠르게 검증할 수 있다 | HIGH |
| REF-CORE-009 | 00_MASTER_REFERENCE.md | Core | synthetic Web/GUI controlled environment | ground-truth grammar label을 만들 핵심 환경이다 | CRITICAL |
| REF-CORE-010 | 00_MASTER_REFERENCE.md | Core | real benchmark auxiliary validation | 외부 타당성 검증에 필요하다 | MEDIUM |
| REF-PROBLEM-001 | 00_MASTER_REFERENCE.md | Problem | wrong grammar persistence as failure | competing explanation과 직접 충돌한다 | CRITICAL |
| REF-PROBLEM-002 | 00_MASTER_REFERENCE.md | Problem | not merely click/type action failure | action failure로 collapse되는지 봐야 한다 | CRITICAL |
| REF-PROBLEM-003 | 00_MASTER_REFERENCE.md | Problem | not merely visual grounding failure | VisualWebArena류 공격 방어에 필요하다 | HIGH |
| REF-PROBLEM-004 | 00_MASTER_REFERENCE.md | Problem | not merely long-horizon planning | planning failure 재포장 공격 방어에 필요하다 | HIGH |
| REF-PROBLEM-005 | 00_MASTER_REFERENCE.md | Problem | verification alone insufficient | VeriGUI와 직접 비교되어야 한다 | CRITICAL |
| REF-PROBLEM-006 | 00_MASTER_REFERENCE.md | Problem | robustness failure decomposed into grammar shift/perception perturbation | robustness benchmark와 구분해야 한다 | CRITICAL |
| REF-PROBLEM-007 | 00_MASTER_REFERENCE.md | Problem | same layout but different grammar | 독립 failure mode를 보여주는 핵심 test다 | CRITICAL |
| REF-CONCEPT-001 | 00_MASTER_REFERENCE.md | Concept | regime | taxonomy에서 mode와 grammar를 분리해야 한다 | CRITICAL |
| REF-CONCEPT-002 | 00_MASTER_REFERENCE.md | Concept | control grammar | 단순 용어 변경인지 검증해야 한다 | CRITICAL |
| REF-CONCEPT-003 | 00_MASTER_REFERENCE.md | Concept | current hypothesis | persistence metric의 기준점이다 | CRITICAL |
| REF-CONCEPT-004 | 00_MASTER_REFERENCE.md | Concept | alternative hypothesis | alternative rollout과 연결된다 | HIGH |
| REF-CONCEPT-005 | 00_MASTER_REFERENCE.md | Concept | falsification evidence | verification과 구분해야 한다 | CRITICAL |
| REF-CONCEPT-006 | 00_MASTER_REFERENCE.md | Concept | action-interface rewrite | action correction과 구분해야 한다 | HIGH |
| REF-CONCEPT-007 | 00_MASTER_REFERENCE.md | Concept | decision-relevant compute | VOC와 연결되지만 단순 threshold가 아니어야 한다 | HIGH |
| REF-CONCEPT-008 | 00_MASTER_REFERENCE.md | Concept | reveal | state update와 grammar shift를 분리한다 | HIGH |
| REF-CONCEPT-009 | 00_MASTER_REFERENCE.md | Concept | shift | control grammar 변화의 core event다 | CRITICAL |
| REF-METRIC-001 | 00_MASTER_REFERENCE.md | Metric | task success rate | 최종 성능이지만 problem separability는 약하다 | MEDIUM |
| REF-METRIC-002 | 00_MASTER_REFERENCE.md | Metric | normalized return | dense progress와 연결된다 | MEDIUM |
| REF-METRIC-003 | 00_MASTER_REFERENCE.md | Metric | compute-matched return | planning/search 공격 방어에 필요하다 | HIGH |
| REF-METRIC-004 | 00_MASTER_REFERENCE.md | Metric | failed-action repetition rate | verification baseline과 비교해야 한다 | HIGH |
| REF-METRIC-005 | 00_MASTER_REFERENCE.md | Metric | wrong-control-grammar persistence time | 핵심 metric 후보다 | CRITICAL |
| REF-METRIC-006 | 00_MASTER_REFERENCE.md | Metric | action-interface switch delay | rewrite의 문제정의 연결 metric이다 | CRITICAL |
| REF-METRIC-007 | 00_MASTER_REFERENCE.md | Metric | recovery delay | VeriGUI/self-correction과 비교 가능하다 | HIGH |
| REF-METRIC-008 | 00_MASTER_REFERENCE.md | Metric | alternative rollout fidelity | world model 품질 검증에 필요하다 | MEDIUM |
| REF-METRIC-009 | 00_MASTER_REFERENCE.md | Metric | falsification precision/recall | evidence→hypothesis rejection 검증 metric이다 | CRITICAL |
| REF-METRIC-010 | 00_MASTER_REFERENCE.md | Metric | reveal-vs-shift accuracy | robustness/perturbation과 구분한다 | HIGH |
| REF-RISK-001 | 00_MASTER_REFERENCE.md | Risk | novelty risk from WebWorld/CUWM/WAC | generic world model claim은 붕괴 가능성이 높다 | CRITICAL |
| REF-RISK-002 | 00_MASTER_REFERENCE.md | Risk | verification overlap risk | VeriGUI가 가장 강한 공격이다 | CRITICAL |
| REF-RISK-003 | 00_MASTER_REFERENCE.md | Risk | synthetic toy risk | counterexample가 hand-crafted toy로 보일 수 있다 | HIGH |
| REF-RISK-004 | 00_MASTER_REFERENCE.md | Risk | latent identifiability risk | regime/control grammar 분리가 불가능할 수 있다 | CRITICAL |
| REF-RISK-005 | 00_MASTER_REFERENCE.md | Risk | metric independence risk | persistence metric이 success/recovery와 중복될 수 있다 | HIGH |
| PAPER-WEBWORLD | 01_RELATED_WORK_THREAT_MAP.md | Direct Threat | large-scale web world model | web world model novelty를 강하게 위협한다 | CRITICAL |
| PAPER-WMA | 01_RELATED_WORK_THREAT_MAP.md | Direct Threat | world-model-augmented web agent | action outcome simulation과 policy selection을 이미 수행한다 | CRITICAL |
| PAPER-WAC | 01_RELATED_WORK_THREAT_MAP.md | Direct Threat | world-model action correction | action correction과 consequence simulation 위협 | CRITICAL |
| PAPER-CUWM | 01_RELATED_WORK_THREAT_MAP.md | Direct Threat | computer-use world model | frozen agent + test-time search 위협 | CRITICAL |
| PAPER-VERIGUI | 01_RELATED_WORK_THREAT_MAP.md | Direct Threat | action-effect verification and self-correction | repeated failure/recovery claim을 직접 위협한다 | CRITICAL |
| PAPER-AGENTRX | 01_RELATED_WORK_THREAT_MAP.md | Direct Threat | agent failure diagnosis | failure taxonomy/diagnosis claim 위협 | HIGH |
| PAPER-STRESSWEB | 01_RELATED_WORK_THREAT_MAP.md | Direct Threat | robustness perturbation benchmark | robustness failure와 grammar shift가 겹칠 수 있다 | HIGH |
| ATTACK-001 | 01_RELATED_WORK_THREAT_MAP.md | Attack | 이미 WebWorld가 했다 | generic WM claim 붕괴 | CRITICAL |
| ATTACK-002 | 01_RELATED_WORK_THREAT_MAP.md | Attack | 이미 VeriGUI가 했다 | verification vs falsification 구분 필요 | CRITICAL |
| ATTACK-003 | 01_RELATED_WORK_THREAT_MAP.md | Attack | 그냥 tree search다 | planning novelty 약화 | HIGH |
| ATTACK-004 | 01_RELATED_WORK_THREAT_MAP.md | Attack | control grammar는 새 용어일 뿐 | 개념 novelty 붕괴 | CRITICAL |
| SURVIVING-NOVELTY-001 | 01_RELATED_WORK_THREAT_MAP.md | Candidate | measurable wrong grammar persistence | 문제정의의 생존 후보 | CRITICAL |
| SURVIVING-NOVELTY-002 | 01_RELATED_WORK_THREAT_MAP.md | Candidate | evidence as falsification not just verification | Step 02의 핵심 검증 대상 | CRITICAL |

---

## 6. Search Expansion Ledger

이 검색은 related work 확장이 아니라 failure taxonomy와 문제정의 반증을 위한 최소 검증이다. `Support Distinct Failure?`는 우리 문제정의를 지지한다는 뜻이 아니라, 독립 failure mode로 분리할 여지가 있는지를 뜻한다.

| Search ID | Query | Source/Paper | Key Finding | Support Distinct Failure? | Collapse Risk? | Follow-up |
|---|---|---|---|---|---|---|
| SEARCH-02-001 | web agent failure modes autonomous web agent failure taxonomy | A Closer Look at Why They Fail When Completing Tasks | agent 실패를 task execution/tool-use 등으로 분해한다 | PARTIAL | taxonomy가 더 넓어 우리 claim이 하위 항목으로 흡수될 수 있음 | Step 02/10에서 metric 차이 제시 |
| SEARCH-02-002 | GUI agent action-effect verification VeriGUI | VeriGUI | action outcome verification, recovery, failure loop 감소를 직접 다룸 | PARTIAL | verification failure로 collapse될 위험 큼 | evidence→posterior→rewrite 경로 필요 |
| SEARCH-02-003 | web agent robustness benchmark layout shift execution disruption | Diagnostic Benchmark for Web Agent Robustness | perception/action/execution perturbation을 stage-aligned로 평가 | PARTIAL | robustness failure로 collapse 가능 | grammar shift vs perturbation 분리 split 필요 |
| SEARCH-02-004 | agent failure diagnosis GUI agent AgentRx | AgentRx | plan adherence, invalid invocation, tool output misinterpretation 등 failure taxonomy 제공 | PARTIAL | failure diagnosis로 collapse 가능 | closed-loop action rewrite 차이 필요 |
| SEARCH-02-005 | visual grounding failure GUI agents | VisualWebArena | visually grounded task에서 text-only 한계 지적 | NO_DIRECT | visual grounding으로 설명 가능한 경우가 많음 | same visual observation/different grammar test 필요 |
| SEARCH-02-006 | OSWorld GUI grounding operational knowledge failure | OSWorld | GUI grounding과 operational knowledge가 주요 약점으로 분석됨 | PARTIAL | operational knowledge failure로 흡수될 수 있음 | operational knowledge vs grammar hypothesis 구분 필요 |
| SEARCH-02-007 | WebArena realistic web agents failure | WebArena | GPT-4 agent success가 human보다 크게 낮아 robust agent 필요성 제시 | BACKGROUND | task failure 원인은 넓게만 제시됨 | auxiliary validation anchor |
| SEARCH-02-008 | Web Agents with World Models WMA | WMA | action outcome simulation으로 policy selection 개선 | PARTIAL | world-model planning failure로 collapse 가능 | hypothesis persistence metric 필요 |
| SEARCH-02-009 | WebWorld web agent simulator | WebWorld | 1M+ open-web interactions, long-horizon simulation, inference-time search | PARTIAL | generic web WM novelty 붕괴 | grammar falsification으로 좁힐 것 |
| SEARCH-02-010 | CUWM computer use world model | CUWM | candidate action별 next UI state 예측, frozen agent test-time search | PARTIAL | frozen agent + WM search claim 붕괴 | current-vs-alt grammar posterior 필요 |
| SEARCH-02-011 | WAC world-model action correction | World-Model-Augmented Web Agents with Action Correction | consequence simulation/action correction을 수행 | PARTIAL | action rewrite가 action correction으로 collapse 가능 | intent-to-action grammar rewrite 명시 필요 |
| SEARCH-02-012 | GUI action outcome verification VSA | VSA | logic-based action verification으로 mobile GUI safety 강화 | PARTIAL | verification으로 collapse 가능 | posterior/hypothesis switch가 없음을 비교 필요 |
| SEARCH-02-013 | D-GARA GUI robustness benchmark anomalies | D-GARA | Android GUI anomaly/robustness 평가 | PARTIAL | anomaly robustness로 collapse 가능 | same anomaly but different grammar metric 필요 |
| SEARCH-02-014 | high dynamic GUI agent benchmark | High-Dynamic GUI benchmark | dynamic task state/partial observability 문제 제기 | PARTIAL | timing/partial observability로 collapse 가능 | grammar-vs-state ambiguity test 필요 |
| SEARCH-02-015 | MIRAGE web imperfect guidance agents | MIRAGE | imperfect guidance under web tasks에서 robustness 평가 | NO_DIRECT | wrong instruction/guidance failure와 혼동 가능 | user instruction vs UI grammar 분리 필요 |
| SEARCH-02-016 | sequential hypothesis testing planning agents | sequential hypothesis testing / Bayesian planning literature | hypothesis update와 belief selection의 일반 이론적 anchor | SUPPORTS_FORMALISM | 너무 일반적이라 novelty 직접 지원 아님 | Step 09에서 이론 framing 제한 |
| SEARCH-02-017 | value of computation planning | value-of-computation/metareasoning planning | compute를 value 기준으로 쓴다는 일반 framework 존재 | SUPPORTS_FORMALISM | decision gate novelty 약화 | application-specific gate로 제한 |
| SEARCH-02-018 | change point detection world model | change-point / regime switching models | dynamics shift 감지 문헌 존재 | PARTIAL | `z_change_point` novelty 약화 | GUI grammar-specific shift로 제한 |
| SEARCH-02-019 | failed action repetition GUI agent | VeriGUI / GUI robustness papers | failed action loops는 이미 명시적으로 다뤄짐 | PARTIAL | failed repetition metric만으로는 collapse | grammar-conditioned repetition 필요 |
| SEARCH-02-020 | action outcome prediction web agent | WMA / CUWM / WebWorld | action outcome prediction은 이미 강함 | NO_DIRECT | WM outcome novelty 붕괴 | falsification/persistence로 claim 축소 |
| SEARCH-02-021 | self-correcting GUI agents | VeriGUI / self-correction frameworks | verification 후 corrective reasoning 수행 | PARTIAL | self-correction failure로 collapse | alternative grammar adoption metric 필요 |
| SEARCH-02-022 | computer use agent failure analysis | OSWorld / AgentRx / OS-SPEAR | OS/agent failures는 safety, performance, robustness로 분해됨 | PARTIAL | broad taxonomy에 흡수 가능 | specific measurable submode로 남겨야 함 |
| SEARCH-02-023 | operational knowledge failure computer-use agents | OSWorld family | agents fail not only by perception but also by operational procedures | PARTIAL | control grammar가 operational knowledge로 흡수될 수 있음 | grammar를 UI-specific executable schema로 좁혀야 함 |
| SEARCH-02-024 | action correction web agent | WAC / WMA / Agent Q family | failed/outcome-based action refinement already exists | PARTIAL | rewrite claim이 약해짐 | grammar-conditioned rewrite + no-rewrite ablation |
| SEARCH-02-025 | GUI agent robustness anomalous dialogs | D-GARA / VeriGUI robustness benchmark | dialogs/loading/warnings already benchmarked | PARTIAL | blocker grammar가 robustness로 흡수됨 | blocker는 auxiliary, grammar shift는 core로 분리 |

---

## 7. Candidate Problem Definition

### 7.1 Weak Version

Web/GUI agent는 UI 상호작용 중 실패한 action을 반복한다. 이 반복 실패를 줄이기 위해 action-effect evidence를 확인하고 더 나은 action을 선택해야 한다.

판정: 이 버전은 거의 죽는다. VeriGUI/action-effect verification, WAC/action correction, WMA/CUWM action outcome simulation으로 대부분 설명 가능하다.

### 7.2 Strong Version

Web/GUI agent의 반복 실패는 action failure, visual grounding failure, planning failure, verification failure와 독립적으로 발생하는 `wrong-control-grammar hypothesis persistence`이다. agent는 현재 UI regime에서 intent가 executable action으로 번역되는 규칙을 잘못 믿고, 반증 evidence가 있어도 해당 mapping을 유지한다.

판정: 메인트랙급으로 강하지만, 현재 상태에서는 증명되지 않았다. 특히 `control grammar`가 단순 action precondition인지, `hypothesis persistence`가 단순 recovery delay인지, `falsification`이 단순 verification인지 공격받는다.

### 7.3 Defensible Version

가장 방어 가능한 버전은 다음이다.

```text
일부 Web/GUI failure loop는 단순 action execution 실패나 visual grounding 실패만으로 설명되지 않는다.
특히 visual target과 task subgoal이 맞고 action-effect evidence도 관측되는데,
agent가 동일 intent를 계속 잘못된 executable action schema로 번역하는 경우가 있다.
이 파일에서는 이를 wrong-control-grammar hypothesis persistence라는 조건부 failure mode 후보로 정의한다.
이 후보는 synthetic Web/GUI 환경에서 같은 observation/task 아래 control grammar만 바꾸는 counterfactual split,
grammar-conditioned persistence metric, no-control-grammar ablation을 통해서만 독립 문제정의로 살아남을 수 있다.
```

| Version | Problem Definition | Strength | Weakness | Risk | Decision |
|---|---|---|---|---|---|
| Weak | failed action 반복을 action-effect verification으로 줄인다 | 이해가 쉽다 | VeriGUI/WAC와 거의 겹친다 | verification 재포장 | REJECT_AS_MAIN |
| Strong | wrong-control-grammar hypothesis persistence는 독립 failure mode다 | novelty가 강하다 | 식별성/metric/기존연구 공격이 큼 | 과장 가능성 | NOT_YET_VERIFIED |
| Defensible | 특정 조건에서 관측·실행·planning은 맞지만 intent-to-action grammar가 틀려 반복 실패하는 조건부 failure mode다 | competing explanation과 분리 가능 | synthetic label 의존 위험 | 실험 없이는 확정 불가 | KEEP_AS_CONDITIONAL |

---

## 8. Operational Definition Contract

`wrong-control-grammar hypothesis persistence`는 아래 조건을 모두 만족할 때만 기록한다.

| Condition ID | Required Condition | Why Required | If Missing |
|---|---|---|---|
| WCGP-C01 | agent의 high-level intent/subgoal이 task goal과 일치한다 | planning failure와 분리 | planning failure로 분류 |
| WCGP-C02 | target UI element 또는 relevant region은 관측 가능하다 | visual grounding failure와 분리 | grounding failure로 분류 |
| WCGP-C03 | 이전 action의 observed effect가 기록된다 | falsification evidence 필요 | unobservable failure로 분류 |
| WCGP-C04 | current executed grammar `g_exec`가 기록된다 | persistence 측정 기준 | metric 계산 불가 |
| WCGP-C05 | true/current-valid grammar `g_true` 또는 oracle grammar label이 있다 | wrong 여부 판정 | synthetic core metric 불가 |
| WCGP-C06 | `g_exec != g_true`이다 | wrong grammar 조건 | ordinary action failure 또는 success |
| WCGP-C07 | evidence가 `g_exec`의 expected effect와 불일치한다 | 단순 실패가 아니라 반증 | weak failure only |
| WCGP-C08 | agent가 evidence 이후에도 같은 invalid mapping을 반복하거나 switch를 지연한다 | persistence 조건 | one-shot wrong action |
| WCGP-C09 | alternative grammar가 존재한다 | rewrite/rollout 가능성 | impossible recovery |
| WCGP-C10 | alternative grammar 선택 시 progress가 증가하거나 failure가 감소한다 | 문제정의의 practical relevance | metric novelty만 있고 method relevance 약함 |

정의:

```text
WCGP episode = C01 ∧ C02 ∧ C03 ∧ C04 ∧ C05 ∧ C06 ∧ C07 ∧ C08 ∧ C09 ∧ C10
```

---

## 9. Competing Explanation Falsification Table

| CE ID | Competing Explanation | Can Fully Explain Our Failure? | What It Misses | Separability Test | Metric | Verdict |
|---|---|---|---|---|---|---|
| CE-ACTION | action failure | PARTIAL | 같은 action이 실패했다는 사실은 설명하지만 왜 같은 intent-to-action mapping을 유지하는지는 설명 부족 | target은 클릭 가능/불가능을 통제하고 grammar만 변경 | repeated invalid mapping rate | PARTIALLY_EXPLAINS |
| CE-GROUNDING | visual grounding failure | PARTIAL | target을 정확히 본 상태에서도 precondition/effect schema를 틀릴 수 있음 | 동일 screenshot/DOM에서 hidden grammar만 바꿈 | grammar-conditioned progress delta | DISTINCT_FAILURE_MAY_SURVIVE |
| CE-PLANNING | planning failure | PARTIAL | subgoal 순서는 맞지만 각 subgoal의 executable interface가 틀릴 수 있음 | short-horizon one-subgoal task에서 grammar만 바꿈 | action-interface switch delay | DISTINCT_FAILURE_MAY_SURVIVE |
| CE-VERIFICATION | action-effect verification failure | PARTIAL_HIGH | failure를 감지하지 못하는 경우는 설명하지만, 감지 후 hypothesis update가 안 되는 경우는 별도 | verifier-only vs hypothesis-update model 비교 | evidence-to-hypothesis-update delay | DISTINCT_FAILURE_MAY_SURVIVE |
| CE-ROBUSTNESS | robustness / perturbation failure | PARTIAL | perturbation이 어떤 hidden grammar shift를 유발했는지 설명하지 않음 | visual perturbation only vs grammar shift split | reveal-vs-shift accuracy | DISTINCT_FAILURE_MAY_SURVIVE |
| CE-SELF-CORRECTION | self-correction failure | PARTIAL_HIGH | correction 실패는 설명하지만 correction space가 grammar-conditioned인지 불명확 | recovery action 후보는 같고 grammar selection만 다르게 설정 | alternative grammar adoption rate | UNKNOWN_NEEDS_EXPERIMENT |
| CE-WORLD-MODEL | next-state/world-model prediction failure | PARTIAL | next-state 예측은 가능해도 current hypothesis falsification과 persistence metric은 별도 | next-state WM-only vs grammar-posterior WM 비교 | falsification precision/recall | DISTINCT_FAILURE_MAY_SURVIVE |
| CE-SEARCH | tree search / exploration failure | PARTIAL | 탐색 부족은 설명하지만 왜 특정 wrong mapping을 고집하는지 설명 부족 | same budget random/uncertainty/falsification gate 비교 | compute-to-recovery efficiency | UNKNOWN_NEEDS_EXPERIMENT |
| CE-LATENCY | loading/stale DOM/timing failure | PARTIAL | timing 자체는 원인이지만 wait-stabilize grammar로 전환하지 못하는 현상은 별도 | loading delay fixed, wait grammar available | stale-DOM grammar switch delay | DISTINCT_FAILURE_MAY_SURVIVE |
| CE-DATA | benchmark/data artifact | POSSIBLE | hand-crafted grammar taxonomy가 정답 유출일 수 있음 | lexical cue removal, held-out grammar composition | OOD grammar generalization | UNKNOWN_NEEDS_EXPERIMENT |
| CE-OPERATIONAL-KNOWLEDGE | operational knowledge failure | PARTIAL | “방법을 모른다”는 설명과 control grammar가 겹침 | same operational instruction, changed UI grammar | grammar-specific switch delay | UNKNOWN_NEEDS_EXPERIMENT |
| CE-AFFORDANCE | affordance perception failure | PARTIAL | visible/clickable affordance를 못 읽은 경우 설명 | oracle affordance given, grammar differs | affordance-controlled persistence | DISTINCT_FAILURE_MAY_SURVIVE |

핵심 판정:

```text
이 문제정의는 verification, robustness, planning으로 상당 부분 설명된다.
다만 관측 성공 + subgoal planning 성공 + action-effect evidence 관측 + wrong intent-to-action schema 유지 + alternative grammar 전환 시 회복 조건을 모두 만족하는 counterexample에서는 CONDITIONAL_SURVIVAL 가능성이 있다.
```

---

## 10. Minimal Counterexample Suite

각 counterexample은 text-only smoke test와 synthetic Web/GUI environment 모두에서 구현 가능해야 한다. 중요한 조건은 “grounding 실패가 아니다”, “action 실행 실패만도 아니다”, “계획 순서 실패만도 아니다”를 명시하는 것이다.

| MCX ID | Scenario | Grounding Success? | Action Technically Valid? | Wrong Grammar | Evidence Against It | Correct Alternative Grammar | Why Distinct |
|---|---|---|---|---|---|---|---|
| MCX-001 | pagination vs infinite scroll | YES: 결과 목록과 다음 영역을 봄 | PARTIAL: click next는 target absent로 무효 | `next_results → click(next_button)` | next button 없음, scrollable container 존재, scroll 후 cards append | `next_results → scroll(container_down)` | target을 못 본 게 아니라 같은 intent의 action grammar가 틀림 |
| MCX-002 | modal-blocked direct click | YES: checkout button과 modal 모두 봄 | YES: click action 자체는 실행됨 | `checkout → click(checkout)` | overlay가 click intercept, DOM state no progress | `checkout → close_modal → click(checkout)` | action failure지만 반복 원인은 blocker-removal grammar 미전환 |
| MCX-003 | form-invalid disabled submit | YES: submit button, required field 표시 관측 | YES: click submit 가능하지만 disabled/no effect | `submit → click(submit)` | disabled=true, required field red | `submit → fill_required → click(submit)` | visual grounding은 성공했지만 precondition grammar를 틀림 |
| MCX-004 | loading/stale DOM timing | YES: item card 관측 | YES: click 시도 가능하지만 element detached | `open_item → click_immediately` | stale element, DOM mutation, loading spinner | `open_item → wait_until_stable → click` | latency 자체가 아니라 wait-stabilize grammar 미전환 |
| MCX-005 | responsive menu hidden navigation | YES: viewport와 hamburger icon 관측 | YES: top-nav click은 target absent | `settings → click(top_nav_settings)` | small viewport, nav collapsed | `settings → open_hamburger → click(settings)` | visual target 부재가 아니라 responsive grammar 전환 실패 |
| MCX-006 | hidden filter accordion | YES: collapsed filter header 관측 | YES: filter option click은 hidden으로 실패 | `apply_filter → click(filter_option)` | option hidden, accordion collapsed | `apply_filter → expand_filter → click(option)` | subgoal은 맞지만 action interface 순서가 틀림 |
| MCX-007 | permission/confirmation flow | YES: delete/save action button 관측 | YES: primary click 후 confirmation required | `delete → click(delete)` | confirm dialog appears, state unchanged | `delete → click(delete) → confirm` | verification만으로는 confirm grammar 선택 필요 |
| MCX-008 | required option before add-to-cart | YES: add-to-cart와 size selector 관측 | YES: add click 가능하나 no cart change | `add_to_cart → click(add)` | missing size warning, cart_count unchanged | `add_to_cart → select_size → click(add)` | 상품 찾기는 성공, add grammar가 틀림 |
| MCX-009 | scroll container vs page scroll | YES: nested result panel 관측 | YES: page scroll 가능하지만 no result change | `more_results → scroll(page)` | page scroll no diff, container overflow true | `more_results → scroll(inner_container)` | action type은 맞지만 target grammar가 틀림 |
| MCX-010 | overlay intercepting click | YES: overlay bbox와 target bbox 관측 | YES: click lands on overlay | `target_click → click(target)` | event target overlay, z-index blocker | `target_click → dismiss_overlay → click(target)` | grounding 성공 후 event routing grammar 실패 |
| MCX-011 | search result replaced vs appended | YES: result list 관측 | YES: search submit 가능 | `refine_search → expect_append` | old cards replaced, selected item lost | `refine_search → preserve_query_state → submit → reselect` | outcome schema 예측 실패가 mapping 유지와 연결됨 |
| MCX-012 | disabled button becomes enabled after prerequisite | YES: disabled button과 prerequisite checkbox 관측 | YES: disabled button click no effect | `continue → click(continue)` | disabled until checkbox checked | `continue → check_required → click(continue)` | precondition을 grammar 일부로 모델링해야 회복 |
| MCX-013 | tabbed panel hidden content | YES: tabs 관측 | YES: content click target absent | `edit_field → click(field)` | field hidden under inactive tab | `edit_field → select_tab → click(field)` | hidden state reveal과 grammar step이 결합됨 |
| MCX-014 | autocomplete selection required | YES: input and suggestion list 관측 | YES: typing 가능 | `choose_city → type(city)` | form not accepted unless suggestion selected | `choose_city → type → select_suggestion` | text input 자체는 맞지만 acceptance grammar가 틀림 |
| MCX-015 | optimistic UI rollback | YES: save button and success toast 관측 | YES: click save 가능 | `save → click(save) and trust toast` | temporary success toast then rollback due validation | `save → verify_persisted_state → fix_field → save` | immediate effect와 persistent effect schema를 구분해야 함 |
| MCX-016 | multi-step wizard hidden next precondition | YES: next button visible | YES: click next produces warning | `next_step → click(next)` | wizard marks previous step incomplete | `next_step → complete_required_prev_panel → click(next)` | long-horizon planning이 아니라 local interface grammar 문제 |

---

## 11. Failure Mode Separability Matrix

| Failure Type | Observable Symptom | Hidden Cause | Our Failure Same/Different? | Required Test | Metric |
|---|---|---|---|---|---|
| action failure | action 후 상태 변화 없음 | target disabled, blocked, stale, invalid | PARTIALLY SAME | 동일 failed action에서 grammar switch 가능성 비교 | repeated invalid mapping rate |
| visual grounding failure | wrong element 클릭/탐색 실패 | 화면 요소 인식 실패 | DIFFERENT IF grounding controlled | target bbox/text/role을 oracle 제공한 상태에서 grammar만 변경 | grammar-conditioned progress delta |
| planning failure | subgoal 순서 오류 | high-level plan 자체가 틀림 | DIFFERENT IF subgoal controlled | one-subgoal 또는 oracle subgoal 환경 | action-interface switch delay |
| verification failure | 실패했는데 감지 못함 | observed effect checking 부재 | DIFFERENT IF verification success controlled | verifier가 failure를 감지했지만 mapping 유지하는 환경 | evidence-to-hypothesis-update delay |
| self-correction failure | 실패 후 recovery action 선택 실패 | correction policy 약함 | PARTIAL | same recovery candidates에서 grammar posterior 유무 비교 | alternative grammar adoption rate |
| robustness failure | perturbation에서 성능 하락 | layout/timing/semantics shift | PARTIAL | visual-only perturbation과 grammar-shift perturbation 분리 | reveal-vs-shift accuracy |
| world model prediction failure | predicted next state가 틀림 | dynamics/outcome model 오류 | PARTIAL | next-state accuracy matched 상태에서 grammar switching 비교 | falsification precision/recall |
| search/exploration failure | 더 좋은 action을 못 찾음 | insufficient rollout/search | PARTIAL | same budget random/uncertainty/falsification gate 비교 | compute-to-recovery efficiency |
| operational knowledge failure | UI 사용 절차를 모름 | domain/tool knowledge 부족 | PARTIAL | instruction/procedure oracle provided, grammar changed | grammar adoption rate |
| affordance failure | button/field 가능성을 잘못 판단 | visibility/clickability/scrollability 인식 오류 | DIFFERENT IF affordance controlled | affordance oracle labels given | affordance-controlled WCGP |

---

## 12. Metric Separability Ledger

| Metric ID | Metric | Formal Definition | Required Label | Distinguishes From | Risk | Decision |
|---|---|---|---|---|---|---|
| METRIC-02-001 | wrong-control-grammar persistence time | `Σ_t I[g_exec_t != g_true_t and evidence_falsifies(g_exec_t)]` until switch | true grammar, executed grammar, falsification evidence | action failure, recovery delay | real benchmark에서 weak label 어려움 | KEEP_CORE |
| METRIC-02-002 | failed-action repetition rate | repeated failed primitive or macro actions / failed actions | failed action label, action signature | general verification failure | grammar 원인과 무관할 수 있음 | KEEP_AUXILIARY |
| METRIC-02-003 | action-interface switch delay | first falsifying evidence 이후 correct grammar macro 선택까지 step 수 | falsifying event, correct grammar | planning/recovery delay | recovery delay와 중복 가능 | KEEP_CORE |
| METRIC-02-004 | recovery delay after falsifying evidence | falsifying evidence 이후 positive progress까지 step 수 | progress label, evidence timestamp | self-correction | grammar-specific 아님 | KEEP_AUXILIARY |
| METRIC-02-005 | evidence-to-hypothesis-update delay | evidence 관측 이후 posterior mode 또는 executed grammar가 바뀌기까지 step 수 | posterior/log, evidence | verification failure | posterior 해석성 필요 | KEEP_CORE |
| METRIC-02-006 | alternative grammar adoption rate | falsified episode 중 correct alternative grammar 채택 비율 | alternative set, true grammar | search failure | alternative set leakage 가능 | KEEP_CORE |
| METRIC-02-007 | falsification precision/recall | current grammar wrong 탐지 precision/recall | current/true grammar, evidence | confidence threshold | calibration 필요 | KEEP_CORE |
| METRIC-02-008 | grammar-conditioned progress delta | correct grammar action의 progress - current grammar action의 progress | counterfactual action table | generic success rate | synthetic 전용 가능성 | KEEP_CORE |
| METRIC-02-009 | repeated invalid mapping rate | same intent가 same invalid grammar로 번역된 비율 | intent, grammar, action macro | repeated action rate | intent labeling 필요 | KEEP_CORE |
| METRIC-02-010 | compute-to-recovery efficiency | recovery progress / rollout steps or planning calls | compute trace, progress | always-plan/tree search | compute 정의에 민감 | KEEP_AUXILIARY |
| METRIC-02-011 | reveal-vs-shift error rate | true shift를 reveal/update로 잘못 처리한 비율 | reveal/shift label | robustness perturbation | label 설계 난도 높음 | KEEP_AUXILIARY |
| METRIC-02-012 | wrong-hypothesis causal mediation | persistence 감소가 recovery improvement를 매개하는 정도 | episode-level metric bundle | success-only explanation | 분석 복잡도 높음 | UNKNOWN |
| METRIC-02-013 | invalid grammar retry count | same `intent, grammar` pair가 invalid evidence 후 반복된 횟수 | intent, grammar, evidence | failed action count | grammar assignment 필요 | KEEP_CORE |
| METRIC-02-014 | no-effect disambiguation accuracy | no-effect를 loading/noise/failure/falsification으로 분류하는 정확도 | event type, effect label | simple failure detection | label 난도 높음 | KEEP_AUXILIARY |

---

## 13. Problem Claim Survival Table

| Claim ID | Claim | Threats Considered | Survival Decision | Required Conditions | Later Verification |
|---|---|---|---|---|---|
| CLAIM-02-001 | wrong-control-grammar persistence는 독립 failure mode일 수 있다 | action/grounding/planning/verification/robustness | CONDITIONAL_SURVIVAL | MCX 조건 10개를 모두 만족해야 함 | Step 04/05/10 |
| CLAIM-02-002 | verification alone은 충분하지 않다 | VeriGUI, VSA | CONDITIONAL_SURVIVAL | verifier가 실패를 감지해도 grammar update가 안 되는 case 필요 | Step 10 |
| CLAIM-02-003 | visual grounding failure와 분리 가능하다 | VisualWebArena, OSWorld | CONDITIONAL_SURVIVAL | oracle grounding 또는 동일 visual observation split 필요 | Step 04/05 |
| CLAIM-02-004 | planning failure와 분리 가능하다 | Agent Q, WMA, tree search | CONDITIONAL_SURVIVAL | oracle subgoal/one-step task에서도 발생해야 함 | Step 04/10 |
| CLAIM-02-005 | robustness perturbation과 구분된다 | StressWeb, D-GARA | CONDITIONAL_SURVIVAL | visual/layout shift와 grammar shift를 독립 조작해야 함 | Step 05/06 |
| CLAIM-02-006 | current-vs-alternative grammar rollout은 일반 action search와 다르다 | WMA/CUWM/WAC | WEAK_SURVIVAL | hypothesis-conditioned likelihood ratio와 metric 필요 | Step 09/10 |
| CLAIM-02-007 | control grammar는 단순 action precondition이 아니다 | reviewer attack | CONDITIONAL_SURVIVAL | intent mapping + precondition + effect schema 3요소 유지 | Step 03 |
| CLAIM-02-008 | wrong-control-grammar persistence metric은 success rate보다 설명력이 있다 | metric overlap risk | UNKNOWN_NEEDS_EXPERIMENT | mediation/correlation/ablation 분석 필요 | Step 10 |
| CLAIM-02-009 | synthetic labels로 문제정의 검증 가능하다 | toy benchmark attack | UNKNOWN_NEEDS_EXPERIMENT | lexical cue removal, held-out grammar composition 필요 | Step 04/05/06 |
| CLAIM-02-010 | real benchmark에서도 weak measurement 가능하다 | label limitation | UNKNOWN_NEEDS_EXPERIMENT | action-effect trace에서 weak grammar inference 가능해야 함 | Step 06/10 |
| CLAIM-02-011 | action-interface rewrite가 policy correction과 구분된다 | WAC, Agent Q | CONDITIONAL_SURVIVAL | same candidates에서 grammar-conditioned rewrite만 개선되어야 함 | Step 09/10 |
| CLAIM-02-012 | decision-relevant compute가 uncertainty gate보다 낫다 | uncertainty/planning baseline | UNKNOWN_NEEDS_EXPERIMENT | compute-matched progress per compute 개선 필요 | Step 09/10 |

---

## 14. Reviewer Attack Ledger

| Attack ID | Reviewer Attack | Why Dangerous | If True, What Collapses? | Required Defense | Assigned Later Step |
|---|---|---|---|---|---|
| ATTACK-02-001 | control grammar는 그냥 action precondition 아닌가? | 개념 novelty 붕괴 | REF-CONCEPT-002, CLAIM-02-007 | grammar를 mapping+precondition+effect schema로 정의 | 03 |
| ATTACK-02-002 | 이건 그냥 action-effect verification 아닌가? | VeriGUI와 겹침 | REF-CORE-003 | verification success 후 hypothesis update 실패 case 제시 | 02,10 |
| ATTACK-02-003 | 이건 그냥 planning failure 아닌가? | 문제정의 collapse | REF-PROBLEM-004 | oracle subgoal/one-subgoal counterexample | 04 |
| ATTACK-02-004 | UI robustness benchmark에서 이미 다룬다 | robustness novelty 약화 | REF-PROBLEM-006 | perturbation vs grammar shift factorial split | 05,10 |
| ATTACK-02-005 | wrong hypothesis는 측정 불가능한 인지적 표현이다 | metric 붕괴 | REF-METRIC-005 | executed grammar와 true grammar로 operationalize | 06,10 |
| ATTACK-02-006 | latent regime/control grammar는 identifiable하지 않다 | model claim 붕괴 | REF-CORE-002 | probe, ablation, factorized label | 07,10 |
| ATTACK-02-007 | metric이 synthetic label에만 의존한다 | external validity 약화 | REF-RISK-003 | weak-label real trace analysis | 06,10 |
| ATTACK-02-008 | alternative grammar로 해결된다는 보장이 없다 | rewrite claim 약화 | REF-CORE-005 | counterfactual action-effect table | 06,10 |
| ATTACK-02-009 | LLM base가 강하면 이런 failure가 별로 없다 | effect size 약화 | REF-CORE-007 | multiple base strengths and hard splits | 10 |
| ATTACK-02-010 | 반례가 전부 hand-crafted toy다 | benchmark credibility 약화 | REF-CORE-009 | procedurally generated task/regime combinations | 04,05 |
| ATTACK-02-011 | same failed action repetition은 verifier로 잡힌다 | core metric 약화 | REF-METRIC-004 | repeated action vs repeated invalid grammar 분리 | 10 |
| ATTACK-02-012 | switch delay는 recovery delay와 중복된다 | metric redundancy | REF-METRIC-006 | switch event와 progress event를 분리 기록 | 06,10 |
| ATTACK-02-013 | falsification은 그냥 confidence threshold다 | theory 약화 | REF-CORE-003 | likelihood ratio current-vs-alt 사용 | 09 |
| ATTACK-02-014 | intent-to-action rewrite는 그냥 policy correction이다 | WAC overlap | REF-CORE-005 | grammar-conditioned macro rewrite 제시 | 03,07,09 |
| ATTACK-02-015 | 이 문제는 benchmark artifact다 | problem definition collapse | REF-RISK-003 | held-out grammar composition, no lexical cue split | 04,05 |
| ATTACK-02-016 | WebWorld/CUWM/WAC가 already covers it | generic WM novelty 붕괴 | REF-RISK-001 | persistence metric과 no-grammar ablation | 01,10 |
| ATTACK-02-017 | VeriGUI already covers it | verification overlap | REF-RISK-002 | verification-only baseline과 posterior update 비교 | 10 |
| ATTACK-02-018 | AgentRx already diagnoses it | diagnosis novelty 약화 | PAPER-AGENTRX | closed-loop planning/rewrite 차이 | 10 |
| ATTACK-02-019 | semantic novelty는 있지만 algorithmic novelty가 약하다 | method rejection 가능 | REF-CORE-004 | falsification gate + alternative grammar rollout | 07,09 |
| ATTACK-02-020 | metric novelty는 있지만 method novelty가 약하다 | contribution 약화 | REF-METRIC-005 | metric-driven ablation and model gains | 10 |
| ATTACK-02-021 | control grammar taxonomy가 임의적이다 | reproducibility 약화 | REF-CONCEPT-002 | generation rules and annotation protocol | 03,06 |
| ATTACK-02-022 | current hypothesis가 무엇인지 모호하다 | persistence 측정 불가 | REF-CONCEPT-003 | `h_exec` 기준으로 정의 | 03,09 |
| ATTACK-02-023 | alternative top-k가 arbitrary하다 | rollout validity 약화 | REF-CORE-004 | posterior/evidence likelihood 기반 top-k | 09 |
| ATTACK-02-024 | real Web/GUI에서는 true grammar label이 없다 | validation 약화 | REF-CORE-019 | synthetic main + real auxiliary로 제한 | 06,10 |
| ATTACK-02-025 | operational knowledge failure와 구분되지 않는다 | OSWorld류 분석에 흡수 가능 | control grammar problem claim | operational instruction oracle + grammar shift split | 05,10 |
| ATTACK-02-026 | no-effect를 전부 falsification으로 잘못 처리한다 | loading/noisy observation confound | falsification metric | no-effect disambiguation labels | 06,09 |

---

## 15. Required Design Revisions From Falsification

| Revision ID | Original Assumption | Falsification Pressure | Required Revision | Affected Later Step |
|---|---|---|---|---|
| REV-02-001 | wrong-control-grammar는 독립 failure mode다 | 기존 failure taxonomy에 흡수 가능 | `may survive` 조건부 문제정의로 낮춘다 | 03,10 |
| REV-02-002 | control grammar는 latent 하나로 충분하다 | action precondition과 구분 불명확 | mapping+precondition+effect schema로 정의 | 03 |
| REV-02-003 | current hypothesis는 posterior mode다 | persistence metric 기준이 흔들림 | 직전 action 생성에 쓰인 `h_exec`로 정의 | 03,09 |
| REV-02-004 | verification과 다르다고 말하면 된다 | VeriGUI가 강한 threat | evidence→hypothesis update→alternative grammar→rewrite 경로를 강제 | 07,09,10 |
| REV-02-005 | robustness와 구분된다 | perturbation benchmark가 이미 강함 | visual/layout perturbation과 grammar shift factorial split 추가 | 05,06 |
| REV-02-006 | failed-action repetition만 보면 된다 | verifier baseline으로 설명 가능 | repeated invalid mapping rate를 core로 추가 | 06,10 |
| REV-02-007 | success rate 개선이면 충분하다 | 문제정의 독립성 증명 불가 | persistence/switch/falsification metric을 core로 승격 | 10 |
| REV-02-008 | synthetic text 사례로 충분하다 | toy attack | procedural generation + lexical cue removal + held-out grammar composition | 04,05 |
| REV-02-009 | alternative rollout은 search와 다르다 | tree-search 공격 | compute-matched random/uncertainty/always-plan baseline 필요 | 09,10 |
| REV-02-010 | reward switch bonus가 유용하다 | reward hacking | switch reward는 progress-linked valid switch 조건부로만 허용 | 08 |
| REV-02-011 | real benchmark에서 claim 검증 가능 | true grammar label 부재 | real은 auxiliary weak measurement로만 사용 | 06,10 |
| REV-02-012 | latent factorization은 자연스럽다 | identifiability 공격 | no-control-grammar, merged-regime-control ablation 필수 | 07,10 |
| REV-02-013 | no-effect는 falsification evidence다 | delayed/noisy/loading confound | no-effect는 loading/noisy/failure/falsification으로 분류 | 06,09 |
| REV-02-014 | operation procedure와 grammar는 다르다고 말하면 된다 | operational knowledge failure로 흡수 가능 | oracle instruction/procedure condition 추가 | 04,05,10 |

---

## 16. Handoff to Later Steps

| Handoff ID | Target Step | What Must Be Used | What Must Be Verified | What Must Not Be Assumed |
|---|---|---|---|---|
| HANDOFF-02-03 | 03_CORE_CONCEPT_TAXONOMY.md | defensible problem version, MCX suite, CE table | regime/control grammar/current hypothesis/falsification/reveal/shift 정의 | control grammar가 최종 novelty라고 가정 금지 |
| HANDOFF-02-04 | 04_TEXT_ONLY_SMOKE_TESTBED.md | MCX-001~016, metric separability | visual grounding/planning/action execution controlled counterexample 가능성 | text-only 성공이 GUI 성공으로 이어진다고 가정 금지 |
| HANDOFF-02-05 | 05_SYNTHETIC_WEB_GUI_ENVIRONMENT.md | same layout/different grammar, perturbation vs grammar shift split | procedural generation과 OOD split 설계 | hand-crafted toy만으로 충분하다고 가정 금지 |
| HANDOFF-02-06 | 06_DATA_SCHEMA_AND_LABELING.md | h_exec, true grammar, evidence, switch timestamp, progress label | metric 계산에 필요한 label/log schema | real benchmark에 true grammar label이 있다고 가정 금지 |
| HANDOFF-02-07 | 07_LATENT_ARCHITECTURE_DESIGN.md | CE/metric/attack 결과 | `z_regime`과 `z_control_grammar`의 identifiable 분리 | latent factorization이 자연스럽게 학습된다고 가정 금지 |
| HANDOFF-02-08 | 08_LOSS_REWARD_TRAINING_OBJECTIVE.md | reward hacking attacks, switch reward condition | L_falsification/L_mapping이 metric 개선과 연결되는지 | switch 자체를 보상해도 된다고 가정 금지 |
| HANDOFF-02-09 | 09_PLANNING_THEORY_ALGORITHM.md | falsification≠confidence threshold, h_exec definition, VOC pressure | likelihood ratio와 decision-relevant gate 정의 | alternative rollout이 tree search와 자동으로 구분된다고 가정 금지 |
| HANDOFF-02-10 | 10_EVALUATION_BASELINE_ABLATION.md | core metrics, CE separability, attacks | verifier-only, next-state WM, WAC-style, uncertainty-gate, no-grammar ablation | success rate만으로 문제정의가 증명된다고 가정 금지 |

---

## 17. Implementation Readiness Contract

이 파일에서 후속 구현이 가능하려면 아래 항목을 반드시 Step 04~06에서 실제 schema로 내려야 한다.

| Impl ID | Required Artifact | Source Section | Must Be Implemented In | Why It Matters |
|---|---|---|---|---|
| IMPL-02-001 | `h_exec` field | §8, §12 | 06_DATA_SCHEMA_AND_LABELING.md | persistence metric의 기준 |
| IMPL-02-002 | `g_true` / oracle grammar label | §8, §12 | 05, 06 | wrong grammar 판정 |
| IMPL-02-003 | `evidence_falsifies(g_exec)` rule | §8, §12 | 06, 09 | falsification metric |
| IMPL-02-004 | same visual/different grammar split | §9, §10 | 04, 05 | grounding failure 분리 |
| IMPL-02-005 | oracle subgoal / one-subgoal tasks | §9, §10 | 04, 05 | planning failure 분리 |
| IMPL-02-006 | no-effect disambiguation labels | §14, §15 | 06 | loading/noisy/failure confound 제거 |
| IMPL-02-007 | repeated invalid mapping metric | §12 | 06, 10 | failed action count와 분리 |
| IMPL-02-008 | verifier-only baseline requirement | §14, §18 | 10 | VeriGUI threat 방어 |
| IMPL-02-009 | next-state WM-only baseline requirement | §13, §18 | 10 | WMA/CUWM/WebWorld threat 방어 |
| IMPL-02-010 | uncertainty-gate baseline requirement | §14 | 09, 10 | planning claim 방어 |

---

## 18. Updated Risk / Unknown Ledger

| Risk ID | Risk / Unknown | Triggered By | Why It Matters | Resolution Path | Can Be Final Claim? |
|---|---|---|---|---|---|
| RISK-02-001 | problem definition may collapse into verification failure | VeriGUI | repeated failure/recovery를 이미 다룸 | verifier-only vs hypothesis-update comparison | NO |
| RISK-02-002 | problem may collapse into action failure | CE-ACTION | no state change만 보면 기존 개념 | invalid mapping metric 추가 | NO |
| RISK-02-003 | problem may collapse into visual grounding failure | VisualWebArena/OSWorld | GUI failures often grounding-related | oracle grounding split | NO |
| RISK-02-004 | problem may collapse into planning failure | Agent Q/WMA | action sequence selection으로 해석 가능 | oracle subgoal/short task split | NO |
| RISK-02-005 | problem may collapse into robustness failure | StressWeb/D-GARA | perturbation failure와 겹침 | grammar shift vs visual perturbation 분리 | NO |
| RISK-02-006 | `control grammar` may be only precondition | reviewer attack | semantic novelty 약화 | 3-part schema definition | NO |
| RISK-02-007 | `wrong hypothesis` may be unobservable | metric attack | 측정 불가능하면 problem claim 붕괴 | h_exec/true grammar operationalization | NO |
| RISK-02-008 | metric may depend only on synthetic labels | toy attack | external validity 약함 | weak real trace metrics | NO |
| RISK-02-009 | counterexamples may be hand-crafted | benchmark attack | reviewer가 toy로 볼 수 있음 | procedural generation rules | NO |
| RISK-02-010 | alternative grammar may leak answer | data leakage | top-k가 oracle처럼 보일 수 있음 | posterior-only top-k construction | NO |
| RISK-02-011 | grammar taxonomy may be arbitrary | taxonomy attack | reproducibility 약화 | annotation/generation protocol | NO |
| RISK-02-012 | recovery delay overlaps switch delay | metric redundancy | metric novelty 약화 | event-level logging 분리 | NO |
| RISK-02-013 | decision gate may be confidence threshold | theory attack | algorithmic novelty 약화 | likelihood ratio + VOC gate | NO |
| RISK-02-014 | base model strength may erase effect | evaluation risk | gains 작으면 claim 약화 | multiple base models and hard splits | NO |
| RISK-02-015 | real benchmark label limitation | WebArena/OSWorld | main metric 직접 계산 어려움 | synthetic main, real auxiliary | NO |
| RISK-02-016 | next-state WM may already solve cases | WMA/CUWM/WebWorld | grammar latent 불필요 가능 | no-control-grammar and WM-only ablation | NO |
| RISK-02-017 | same visual/different grammar split may be artificial | synthetic design | real web에서 드문 현상일 수 있음 | real trace case study | NO |
| RISK-02-018 | falsification precision may not correlate with task success | metric validity | method가 metric만 개선할 수 있음 | mediation analysis | NO |
| RISK-02-019 | operational knowledge may explain grammar failures | OSWorld | grammar concept이 너무 넓어짐 | oracle procedure + grammar shift split | NO |
| RISK-02-020 | no-effect confound may inflate falsification | loading/noisy DOM | false positives 증가 | event type disambiguation | NO |

---

## 19. Quality Gate Result

| Gate ID | Gate | PASS/FAIL/PARTIAL | Evidence | If Not PASS, Blocker |
|---|---|---|---|---|
| QG-02-01 | 00/01 refs imported | PASS | Imported References 50개 이상 | 없음 |
| QG-02-02 | search expansion 20개 이상 수행 | PASS | SEARCH-02-001~025 | 없음 |
| QG-02-03 | competing explanations 10개 이상 검증 | PASS | CE-ACTION~CE-AFFORDANCE 12개 | 없음 |
| QG-02-04 | minimal counterexamples 12개 이상 작성 | PASS | MCX-001~016 | 없음 |
| QG-02-05 | failure mode separability matrix 작성 | PASS | 10개 failure type 비교 | 없음 |
| QG-02-06 | metric separability ledger 작성 | PASS | METRIC-02-001~014 | 없음 |
| QG-02-07 | reviewer attacks 20개 이상 작성 | PASS | ATTACK-02-001~026 | 없음 |
| QG-02-08 | survival decision을 조건부로 판정 | PASS | CLAIM-02 대부분 CONDITIONAL/UNKNOWN | 없음 |
| QG-02-09 | design revision 10개 이상 도출 | PASS | REV-02-001~014 | 없음 |
| QG-02-10 | no final novelty claim prematurely accepted | PASS | 모든 핵심 claim은 CONDITIONAL/UNKNOWN | 없음 |
| QG-02-11 | Claude Code routing included | PASS | §2 Context Routing | 없음 |
| QG-02-12 | implementation readiness included | PASS | §17 Implementation Readiness Contract | 없음 |
| QG-02-13 | direct threat anchors preserved | PASS | §4, §6, §14 | 없음 |
| QG-02-14 | no empirical result fabricated | PASS | all claims framed as conditional | 없음 |

---

## 20. Final Statement of This File

```text
02_PROBLEM_NOVELTY_FALSIFICATION.md is a falsification file, not a final problem statement.

The most defensible current problem definition is:
일부 Web/GUI failure loop는 단순 action execution 실패나 visual grounding 실패만으로 설명되지 않을 수 있다.
특히 visual target과 task subgoal이 맞고 action-effect evidence도 관측되는데,
agent가 동일 intent를 계속 잘못된 executable action schema로 번역하는 경우가 있다.
이 파일에서는 이를 wrong-control-grammar hypothesis persistence라는 조건부 failure mode 후보로 정의한다.
이 후보는 synthetic Web/GUI 환경에서 같은 observation/task 아래 control grammar만 바꾸는 counterfactual split,
grammar-conditioned persistence metric, no-control-grammar ablation을 통해서만 독립 문제정의로 살아남을 수 있다.

The problem definition may survive only if later steps verify:
- visual grounding, action execution, subgoal planning, verification success를 통제한 minimal counterexample가 실제로 생성 가능해야 한다.
- wrong-control-grammar persistence time, action-interface switch delay, repeated invalid mapping rate가 success/recovery metric과 구분되는 설명력을 가져야 한다.
- verifier-only, next-state world model only, WAC-style action correction, uncertainty-gated planning, no-control-grammar ablation을 모두 통과해야 한다.
- synthetic label leakage와 hand-crafted toy risk를 lexical cue removal, held-out grammar composition, procedural generation으로 줄여야 한다.
- real Web/GUI benchmark에서는 최종 claim이 아니라 auxiliary weak evidence로만 사용해야 한다.

The next required file is:
03_CORE_CONCEPT_TAXONOMY.md
```
