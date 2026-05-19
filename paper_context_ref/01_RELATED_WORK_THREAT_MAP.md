---
file_id: STEP-01
title: FRCG-WM 논문 설계를 위한 Related Work Threat Map
version: v1.0
status: threat_analysis_not_final_novelty_claim
language: ko
created_from:
  - 00_MASTER_REFERENCE.md
  - uploaded_step01_v0.1
  - citation_grade_search_sanity_check
purpose:
  - 기존 Web/GUI agent, world model, verification, robustness, planning 연구가 FRCG-WM의 novelty를 어디까지 위협하는지 공격적으로 분석한다.
  - DIRECT_THREAT, PARTIAL_OVERLAP, BENCHMARK_ANCHOR, BACKGROUND_ONLY를 분리한다.
  - Step 02에서 문제정의와 novelty를 반증 가능하게 만들기 위한 reviewer-grade 공격 지도를 제공한다.
  - Claude Code가 후속 작업 시 필요한 관련연구 context만 확장적으로 읽을 수 있도록 routing과 handoff를 제공한다.
forbidden:
  - novelty를 최종 확정하지 않는다.
  - 최종 related work 문단을 쓰지 않는다.
  - 최종 architecture/loss/reward/experiment를 확정하지 않는다.
  - 검색하지 않은 연구를 확인된 연구처럼 취급하지 않는다.
  - DIRECT_THREAT를 약하게 축소하지 않는다.
  - SURVIVING_NOVELTY를 verified novelty처럼 쓰지 않는다.
next_files:
  - 02_PROBLEM_NOVELTY_FALSIFICATION.md
  - 03_CORE_CONCEPT_TAXONOMY.md
  - 10_EVALUATION_BASELINE_ABLATION.md
---

# 01_RELATED_WORK_THREAT_MAP.md

## 1. File Purpose

이 파일은 최종 related work 섹션이 아니다. 이 파일은 **novelty threat map**이다. 목적은 우리 아이디어를 지지하는 논문을 찾는 것이 아니라, 우리 아이디어를 죽일 수 있는 논문·벤치마크·방법론을 먼저 찾는 것이다.

FRCG-WM의 현재 후보 주장은 다음과 같다.

> Web/GUI agent의 반복 실패는 단순 action failure, visual grounding failure, planning failure, action-effect verification failure가 아니라, 현재 UI가 어떤 조작 문법으로 작동하는지에 대한 잘못된 control-grammar hypothesis를 오래 유지하는 wrong-control-grammar hypothesis persistence에서 발생한다. 이를 해결하기 위해 latent regime/control-grammar world model을 학습하고, action-effect evidence가 current hypothesis를 반증할 때 alternative hypothesis rollout을 수행하여 intent-to-action mapping과 planning compute를 재배치한다.

이 주장은 아직 검증된 novelty가 아니다. 특히 WebWorld, WMA, WAC, CUWM, ViMo, MobileDreamer, VeriGUI, AgentRx, StressWeb 계열은 직접적인 위협이다.

이 파일의 산출물은 다음 후속 파일에 강제로 전달된다.

- `02_PROBLEM_NOVELTY_FALSIFICATION.md`: problem claim이 기존 연구의 재포장인지 반증한다.
- `03_CORE_CONCEPT_TAXONOMY.md`: `regime`, `control grammar`, `falsification`, `alternative hypothesis`의 경계를 고정한다.
- `10_EVALUATION_BASELINE_ABLATION.md`: direct threat를 baseline/ablation으로 변환한다.

---

## 2. Claude Code Context Routing

Claude Code는 이 파일 전체를 매번 읽지 말고 작업 목적에 따라 아래 섹션을 우선 읽어야 한다.

| User Intent / Task | Must Read First | Then Read | Do Not Assume |
|---|---|---|---|
| WebWorld/CUWM/WAC와의 차별성 검토 | §6.1, §6.2, §7, §8 | §9, §10 | generic world model novelty가 살아있다고 가정 금지 |
| VeriGUI/action-effect verification과의 차별성 검토 | §6.3, §7, §8 | §9, §10 | action-effect evidence 자체가 novelty라고 가정 금지 |
| robustness/perturbation benchmark와의 차별성 검토 | §6.5, §8, §12 | §9, §13 | grammar shift가 benchmark perturbation과 자동으로 다르다고 가정 금지 |
| `control grammar` 개념 방어 | §7, §8, §9 | `03_CORE_CONCEPT_TAXONOMY.md` | control grammar가 verified concept이라고 가정 금지 |
| baseline/ablation 설계 | §5, §6, §8, §11 | `10_EVALUATION_BASELINE_ABLATION.md` | weak baseline으로 novelty 방어 금지 |
| final blueprint 통합 | §9, §10, §11, §12, §14 | `FINAL_RESEARCH_BLUEPRINT.md` | `SURVIVING_NOVELTY`를 final claim으로 승격 금지 |

---

## 3. Verification and Citation Policy

이 파일에서 사용하는 검증 상태는 다음과 같다.

| Status | 의미 | 최종 claim 사용 가능 여부 | 조치 |
|---|---|---:|---|
| `CONFIRMED_PRIMARY` | arXiv, OpenReview, 공식 사이트, GitHub 등 1차 출처로 확인됨 | 단독으로 novelty 증명 불가 | Step 02/10에서 overlap 분석 필요 |
| `CONFIRMED_SECONDARY` | Hugging Face paper page, 저자/기관 페이지, 논문 목록 등 2차 출처로 확인됨 | 불가 | 1차 출처 추가 확인 필요 |
| `PARTIALLY_CONFIRMED` | 제목/요약/논문 존재는 확인됐으나 세부 claim은 추가 검증 필요 | 불가 | Step 01/02/10에서 재확인 |
| `UNVERIFIED_ANCHOR` | 원문 초안에 등장했으나 현재 citation-grade 검증 부족 | 불가 | 검색 재수행 필요 |
| `SEARCH_FAILED` | 검색 실패 | 불가 | claim에서 제외 |
| `IRRELEVANT_AFTER_REVIEW` | 이름은 관련 있어 보이나 실제 threat 약함 | 불가 | background로만 사용 |

원칙:

```text
이 파일에서 CONFIRMED_PRIMARY라고 해도, 그것은 “논문/벤치마크의 존재와 대략적 기여가 확인됨”을 뜻할 뿐이다.
FRCG-WM의 novelty가 죽었는지/살아남았는지는 Step 02와 Step 10에서 metric, baseline, ablation으로 다시 검증해야 한다.
```

---

## 4. Imported Reference Map from Step 00

| Imported Ref ID | Meaning | Why It Matters For This Step | Search Priority | Step 01 Handling |
|---|---|---|---|---|
| REF-CORE-001 | wrong-control-grammar hypothesis persistence | 기존 연구가 반복 실패/failed action loop를 이미 다루는지 검증해야 한다 | CRITICAL | VeriGUI, AgentRx, StressWeb와 비교 |
| REF-CORE-002 | latent regime/control-grammar world model | latent regime 또는 GUI world model 연구와 겹칠 수 있다 | CRITICAL | CUWM, ViMo, MobileDreamer, WebWorld와 비교 |
| REF-CORE-003 | action-effect evidence based falsification | VeriGUI/action-effect verification과 가장 크게 겹친다 | CRITICAL | verification과 falsification 분리 기준 도출 |
| REF-CORE-004 | current-vs-alternative hypothesis rollout | WAC/WMA/CUWM/Agent Q의 consequence simulation/search와 겹친다 | CRITICAL | alternative hypothesis가 action search와 다른지 검토 |
| REF-CORE-005 | intent-to-action rewrite | action correction, recovery, self-correction 연구와 비교 필요 | CRITICAL | WAC/VeriGUI와 비교 |
| REF-CORE-006 | decision-relevant compute reallocation | VOC, tree search, uncertainty-gated planning과 구분 필요 | HIGH | Agent Q, VOC, uncertainty planning과 비교 |
| REF-CORE-007 | Frozen Base VLM/LLM + reliability module | CUWM/WMA/WAC가 frozen agent 위에 WM을 붙이는지 검토 필요 | HIGH | novelty가 아니라 control variable로 격하 |
| REF-CORE-008 | text-only smoke test | MiniWoB/WebShop 등 synthetic web env와 toy risk 비교 필요 | MEDIUM | smoke-test precedent로만 사용 |
| REF-CORE-009 | synthetic Web/GUI controlled environment | StressWeb, WebArena-Infinity, BrowserGym과 비교 필요 | HIGH | causal label 목적 강조 |
| REF-CORE-010 | real benchmark auxiliary validation | WebArena/VisualWebArena/OSWorld/WorkArena anchor 검토 필요 | HIGH | external validity용 anchor로 분류 |
| REF-CORE-011 | 4-latent base design | latent factorization이 기존 MBRL/latent regime literature와 겹칠 수 있다 | HIGH | Step 03/07로 넘김 |
| REF-CORE-012 | main 6 loss candidates | verifier/world model training objective와 겹치는지 확인 필요 | MEDIUM | VeriGUI reward/training과 비교 |
| REF-CORE-013 | progress-linked reward design | VeriGUI의 asymmetric verification rewards, Agent Q의 self-critique reward와 비교 필요 | MEDIUM | reward novelty는 약하게 취급 |
| REF-CORE-014 | wrong-hypothesis persistence metric | 기존 robustness/failure loop metric과 겹치는지 확인 필요 | CRITICAL | surviving novelty 후보로 유지 |
| REF-CORE-015 | reveal-vs-shift split | robustness perturbation benchmark의 altered semantics와 비교 필요 | HIGH | StressWeb/D-GARA와 비교 |
| REF-CORE-016 | compute-matched evaluation | WMA/Agent Q가 cost/time/search를 다룬다 | HIGH | compute-matched baseline 필수화 |
| REF-CORE-017 | alternative rollout fidelity | world-model evaluation literature와 겹친다 | MEDIUM | WM fidelity metric으로 분리 |
| REF-CORE-018 | no-control-grammar ablation | 살아남는 novelty의 핵심 ablation 후보 | CRITICAL | Step 10 필수 ablation으로 전달 |
| REF-CORE-019 | real benchmark label limitation | grammar label 없는 benchmark에서 claim을 못 증명할 수 있다 | HIGH | synthetic main + real auxiliary로 분리 |
| REF-CORE-020 | 최종 claim은 generic GUI world model이 아님 | WebWorld/CUWM/WAC/ViMo가 generic claim을 이미 위협한다 | CRITICAL | 최종 framing 강제 수정 |
| REF-PROBLEM-001 | wrong grammar persistence as failure | 실패 원인 주장의 경쟁 설명을 관련 연구에서 찾는다 | CRITICAL | failure loop/recovery 연구와 비교 |
| REF-PROBLEM-002 | not merely click/type action failure | action-effect failure/recovery 연구와 비교 | HIGH | VeriGUI와 비교 |
| REF-PROBLEM-003 | not merely visual grounding failure | VisualWebArena/SeeAct/WebVoyager와 비교 | HIGH | visual grounding baseline 필요 |
| REF-PROBLEM-004 | not merely long-horizon planning | Agent Q/MCTS/WorkArena++와 비교 | HIGH | planning baseline 필요 |
| REF-PROBLEM-005 | verification alone insufficient | VeriGUI/VAGEN/VSA와 직접 비교 | CRITICAL | verifier-only baseline 필수 |
| REF-PROBLEM-006 | robustness failure decomposed into grammar shift/perception perturbation | StressWeb/D-GARA와 비교 | CRITICAL | OOD-control grammar split 필요 |
| REF-PROBLEM-007 | same layout but different grammar | controlled perturbation benchmark와 비교 | HIGH | synthetic same-UI/different-grammar split 필요 |
| REF-CONCEPT-001 | regime | latent regime literature와 taxonomy 차이를 정의해야 함 | HIGH | Step 03으로 넘김 |
| REF-CONCEPT-002 | control grammar | 단순 용어 변경인지 검증해야 함 | CRITICAL | 핵심 공격 대상으로 유지 |
| REF-CONCEPT-003 | current hypothesis | WMA/WAC의 candidate simulation과 다름을 보여야 함 | HIGH | `h_exec` 정의 필요 |
| REF-CONCEPT-004 | alternative hypothesis | tree search와 구분 필요 | HIGH | Agent Q와 비교 |
| REF-CONCEPT-005 | falsification evidence | verification과 hypothesis rejection의 차이를 검증 | CRITICAL | VeriGUI와 비교 |
| REF-CONCEPT-006 | action-interface rewrite | action correction과의 차이 검토 | CRITICAL | WAC와 비교 |
| REF-CONCEPT-007 | decision-relevant compute | uncertainty gate와 VOC의 차이 검토 | HIGH | Step 09/10으로 넘김 |
| REF-ARCH-003 | action-effect encoder | VeriGUI/VSA/VAGEN과 겹칠 수 있음 | CRITICAL | verification overlap |
| REF-ARCH-010 | falsification scorer | 독립 novelty 후보 | CRITICAL | likelihood-ratio formalization 필요 |
| REF-ARCH-011 | alternative hypothesis proposer | WAC/Agent Q와 겹칠 수 있음 | HIGH | random/top-k/oracle ablation 필요 |
| REF-ARCH-012 | short rollout model | 모든 WM 계열과 겹침 | CRITICAL | next-state-WM baseline 필요 |
| REF-ARCH-015 | intent-to-action rewrite module | WAC action correction과 비교 필요 | CRITICAL | grammar-conditioned rewrite로 한정 |
| REF-LOSS-005 | L_falsification | VeriGUI verification reward와 비교 필요 | HIGH | reward novelty로 쓰지 말 것 |
| REF-METRIC-005 | wrong-control-grammar persistence time | 기존 논문에 없는지 핵심 검증 대상 | CRITICAL | Step 02/10 핵심 metric |
| REF-RISK-001 | novelty risk from WebWorld/CUWM/WAC | Step 01의 가장 중요한 이유 | CRITICAL | direct threat로 처리 |
| REF-UNKNOWN-001 | grammar label real benchmark inference | real validation 가능성 검토 | HIGH | real benchmark auxiliary 제한 |

---

## 5. Search Protocol

| Search Group | Purpose | Example Queries | Expected Threat Type | Required Outcome |
|---|---|---|---|---|
| SG-01 Web Agent World Model | 웹 agent world model이 이미 action outcome/rollout/action correction을 했는지 확인 | `WebWorld`, `web agent world model`, `WMA`, `WAC`, `consequence simulation web agent` | WORLD_MODEL_OVERLAP | generic WM claim 폐기 여부 판단 |
| SG-02 GUI/Mobile/Computer-Use World Model | GUI/mobile/desktop world model이 이미 next UI prediction과 planning을 하는지 확인 | `CUWM`, `ViMo`, `MobileDreamer`, `Code2World`, `GUI world model` | WORLD_MODEL_OVERLAP | GUI WM threat 정리 |
| SG-03 Action-Effect Verification | failed action verification/recovery가 이미 반복 실패를 줄이는지 확인 | `VeriGUI`, `GUI action-effect verification`, `VAGEN`, `VSA` | VERIFICATION_OVERLAP | falsification vs verification 차이 도출 |
| SG-04 Failure Diagnosis | trajectory failure localization/taxonomy가 failure metric을 위협하는지 확인 | `AgentRx`, `agent failure diagnosis`, `trajectory failure diagnosis` | FAILURE_DIAGNOSIS_OVERLAP | online recovery와 post-hoc diagnosis 분리 |
| SG-05 Robustness Benchmark | layout shift, altered semantics, execution disruption benchmark가 grammar shift를 이미 다루는지 확인 | `StressWeb`, `D-GARA`, `WorkflowPerturb`, `web agent robustness benchmark` | ROBUSTNESS_BENCHMARK_OVERLAP | grammar shift를 benchmark perturbation과 분리 |
| SG-06 General Web/GUI Benchmarks | 실험 anchor 및 external validity 후보 확인 | `WebArena`, `VisualWebArena`, `MiniWoB++`, `OSWorld`, `WorkArena`, `BrowserGym`, `WebShop`, `Mind2Web` | BENCHMARK_ANCHOR | external benchmark role 분리 |
| SG-07 Planning / Search / VOC | alternative rollout이 일반 MCTS/VOC/planning과 다른지 확인 | `Agent Q`, `value of computation planning`, `Bayesian adaptive planning`, `latent regime switching RL` | PLANNING_SEARCH_OVERLAP | decision-relevant compute 정의 압박 |
| SG-08 Generalist Web/GUI Agents | base agent/grounding baseline 위협 확인 | `SeeAct`, `WebVoyager`, `AndroidControl`, `AitZ` | BENCHMARK_ANCHOR / BACKGROUND_ONLY | base-agent strength control 필요 |

---

## 6. Citation-Grade Anchor Ledger

이 표는 후속 `FINAL_RESEARCH_BLUEPRINT.md`에서 인용 후보로 사용할 수 있는 citation-grade seed다. 단, 최종 논문 작성 시에는 각 논문의 PDF/본문을 다시 확인해야 한다.

| Anchor ID | Work / Benchmark | Year | Primary URL | Confirmed Fact | Relation to FRCG-WM | Threat Level | Citation Status |
|---|---|---:|---|---|---|---|---|
| CITE-001 | WebArena | 2023 | https://arxiv.org/abs/2307.13854 | realistic self-hosted web environment; GPT-4 baseline 14.41%, human 78.24% reported in abstract | external web benchmark anchor | MEDIUM | CONFIRMED_PRIMARY |
| CITE-002 | VisualWebArena | 2024 | https://arxiv.org/abs/2401.13649 | realistic visually grounded web tasks for multimodal agents | visual grounding competing explanation | MEDIUM | CONFIRMED_PRIMARY |
| CITE-003 | MiniWoB++ / RL on Web Interfaces | 2018 | https://arxiv.org/pdf/1802.08802 | MiniWoB/MiniWoB++ web interaction tasks used for RL web interfaces | synthetic web task precedent | LOW | CONFIRMED_PRIMARY |
| CITE-004 | OSWorld | 2024 | https://arxiv.org/abs/2404.07972 | open-ended tasks in real computer environments | real computer-use auxiliary benchmark | MEDIUM | CONFIRMED_PRIMARY |
| CITE-005 | WorkArena | 2024 | https://arxiv.org/abs/2403.07718 | ServiceNow-based browser benchmark for knowledge-work tasks | enterprise web benchmark anchor | MEDIUM | CONFIRMED_PRIMARY |
| CITE-006 | WorkArena official site | 2024 | https://servicenow.github.io/WorkArena/ | browser-based ServiceNow tasks | benchmark implementation anchor | MEDIUM | CONFIRMED_PRIMARY |
| CITE-007 | WebShop | 2022 | https://arxiv.org/abs/2207.01206 | simulated e-commerce website with 1.18M products and 12,087 instructions | shopping task family precedent | LOW | CONFIRMED_PRIMARY |
| CITE-008 | Mind2Web | 2023 | https://arxiv.org/abs/2306.06070 | 2,000+ tasks, 137 websites, 31 domains | real web dataset anchor | LOW | CONFIRMED_PRIMARY |
| CITE-009 | SeeAct | 2024 | https://arxiv.org/abs/2401.01614 | GPT-4V-style generalist web agent; grounding remains major issue | visual grounding/base-agent threat | MEDIUM | CONFIRMED_PRIMARY |
| CITE-010 | WebWorld | 2026 | https://arxiv.org/abs/2602.14721 | large-scale web world model trained on 1M+ open-web interactions; inference-time search | generic web world model direct threat | CRITICAL | CONFIRMED_PRIMARY |
| CITE-011 | WAC | 2026 | https://arxiv.org/abs/2602.15384 | world-model-augmented web agents with consequence simulation and feedback-driven action refinement | action correction/direct rollout threat | CRITICAL | CONFIRMED_PRIMARY |
| CITE-012 | CUWM | 2026 | https://arxiv.org/abs/2602.17365 | computer-using world model predicts next UI state for candidate actions; frozen agent uses test-time search | frozen-base + WM search direct threat | CRITICAL | CONFIRMED_PRIMARY |
| CITE-013 | VeriGUI: Don’t Act Blindly | 2026 | https://arxiv.org/abs/2604.05477 | action-effect verification, TVAE, synthetic failure trajectories, GRPO asymmetric rewards | verification/recovery direct threat | CRITICAL | CONFIRMED_PRIMARY |
| CITE-014 | VAGEN | 2026 | https://arxiv.org/html/2602.00575v1 | verifier agent actively probes environment for completion evidence | verification/probing overlap | MEDIUM | CONFIRMED_PRIMARY |
| CITE-015 | OSWorld-MCP | 2025 | https://arxiv.org/abs/2510.24563 | benchmark for MCP tool invocation and GUI operation in computer-use agents | tool/GUIs evaluation fairness anchor | LOW | CONFIRMED_PRIMARY |
| CITE-016 | SeeAct GitHub | 2024 | https://github.com/OSU-NLP-Group/SeeAct | codebase for generalist web agents | implementation baseline reference | LOW | CONFIRMED_PRIMARY |
| CITE-017 | WebWorld GitHub | 2026 | https://github.com/QwenLM/WebWorld | open web-world model resources | implementation/reference anchor | MEDIUM | CONFIRMED_PRIMARY |
| CITE-018 | VeriGUI paper list summary | 2026 | https://github.com/OSU-NLP-Group/GUI-Agents-Paper-List | secondary listing summarizing VeriGUI | secondary confirmation only | MEDIUM | CONFIRMED_SECONDARY |

---

## 7. Search Ledger

| Search ID | Query | Source/Paper | Year | Venue/Source | Core Finding | Relation to Our Idea | Verification Status | Citation Anchor |
|---|---|---:|---|---|---|---|---|---|
| SEARCH-001 | WebArena autonomous web agents | WebArena: A Realistic Web Environment for Building Autonomous Agents | 2023/2024 | arXiv / NeurIPS 2024 Oral | realistic self-hosted web benchmark; GPT-4 baseline much lower than human | 외부 web benchmark anchor | CONFIRMED_PRIMARY | CITE-001 |
| SEARCH-002 | VisualWebArena multimodal web agents | VisualWebArena | 2024 | arXiv / ACL 2024 | realistic visually grounded web task benchmark | visual grounding competing explanation | CONFIRMED_PRIMARY | CITE-002 |
| SEARCH-003 | MiniWoB++ web interaction benchmark | MiniWoB++ / RL on Web Interfaces | 2018 | ICLR / Farama docs | 100+ web interaction env | text-only/synthetic smoke test 비교 anchor | CONFIRMED_PRIMARY | CITE-003 |
| SEARCH-004 | OSWorld computer use benchmark | OSWorld | 2024 | arXiv / NeurIPS 2024 | real computer-use benchmark | real GUI/computer-use auxiliary benchmark | CONFIRMED_PRIMARY | CITE-004 |
| SEARCH-005 | WorkArena ServiceNow BrowserGym | WorkArena | 2024 | arXiv / official site | enterprise web task benchmark, ServiceNow/browser-based tasks | enterprise workflow benchmark anchor | CONFIRMED_PRIMARY | CITE-005, CITE-006 |
| SEARCH-006 | BrowserGym web agent ecosystem | BrowserGym ecosystem | 2024 | ecosystem/paper | unified web-agent research environment | synthetic env 설계에 압박 | PARTIALLY_CONFIRMED | VERIFY_STEP10 |
| SEARCH-007 | WebShop benchmark web agent | WebShop | 2022 | arXiv / NeurIPS | simulated e-commerce website, 1.18M products, 12,087 instructions | shopping task family 및 synthetic env 비교 | CONFIRMED_PRIMARY | CITE-007 |
| SEARCH-008 | Mind2Web generalist web agent | Mind2Web | 2023 | arXiv / OpenReview | 2,000+ tasks, 137 websites, 31 domains | real web diversity benchmark | CONFIRMED_PRIMARY | CITE-008 |
| SEARCH-009 | SeeAct generalist web agent | GPT-4V is a Generalist Web Agent, if Grounded | 2024 | arXiv / ICML | multimodal generalist web agent; grounding remains bottleneck | visual grounding competing explanation | CONFIRMED_PRIMARY | CITE-009 |
| SEARCH-010 | WebVoyager end-to-end web agent | WebVoyager | 2024 | arXiv / ACL | real-world LMM web agent | strong base-agent/benchmark context | PARTIALLY_CONFIRMED | VERIFY_STEP10 |
| SEARCH-011 | WebWorld web agent simulator | WebWorld | 2026 | arXiv | large-scale web simulator/world model trained on 1M+ open-web interactions; inference-time search | direct generic web world model threat | CONFIRMED_PRIMARY | CITE-010 |
| SEARCH-012 | Web Agents with World Models | WMA / DynaWeb family | 2024/2026 | arXiv / Semantic Scholar | web world model/action outcome simulation family | direct web WM + policy selection threat | PARTIALLY_CONFIRMED | VERIFY_STEP01 |
| SEARCH-013 | WAC world model action correction | WAC | 2026 | arXiv | consequence simulation + judge + feedback-driven action refinement | 가장 직접적인 action correction threat | CONFIRMED_PRIMARY | CITE-011 |
| SEARCH-014 | CUWM computer use world model | CUWM | 2026 | arXiv | current UI + candidate action → next UI state; frozen agent test-time search | frozen agent + WM search direct threat | CONFIRMED_PRIMARY | CITE-012 |
| SEARCH-015 | ViMo visual GUI world model | ViMo | 2025/2026 | arXiv/OpenReview candidate | future GUI observation image generation for action option evaluation | GUI world model threat | PARTIALLY_CONFIRMED | VERIFY_STEP01 |
| SEARCH-016 | MobileDreamer GUI world model | MobileDreamer | 2026 | arXiv candidate | textual sketch WM + rollout imagination for mobile GUI agent | lightweight GUI lookahead threat | PARTIALLY_CONFIRMED | VERIFY_STEP01 |
| SEARCH-017 | MobileWorldBench semantic world modeling | MobileWorldBench | 2025 | arXiv candidate | future state prediction benchmark/dataset for mobile GUI world models | semantic WM benchmark threat | PARTIALLY_CONFIRMED | VERIFY_STEP01 |
| SEARCH-018 | Code2World GUI world model | Code2World | 2026 | arXiv candidate | next GUI state via renderable code generation | structural GUI WM threat | PARTIALLY_CONFIRMED | VERIFY_STEP01 |
| SEARCH-019 | VeriGUI action-effect verification | Don’t Act Blindly / VeriGUI | 2026 | arXiv | TVAE, action-effect verification, synthetic failure trajectories, GRPO asymmetric rewards | 가장 직접적인 verification/recovery threat | CONFIRMED_PRIMARY | CITE-013 |
| SEARCH-020 | VAGEN GUI verification | VAGEN | 2026 | arXiv HTML | verifier agent proactively probes environment for task completion evidence | verification threat, but completion-verification 중심 | CONFIRMED_PRIMARY | CITE-014 |
| SEARCH-021 | VSA logic-based mobile GUI safeguard | VeriSafe Agent | 2025 | arXiv / MobiCom candidate | formal/logical action safeguard | pre-action safety/verification overlap | PARTIALLY_CONFIRMED | VERIFY_STEP01 |
| SEARCH-022 | AgentRx failure diagnosis | AgentRx | 2026 | arXiv / Microsoft candidate | failed trajectory diagnosis and critical failure step | failure diagnosis threat but post-hoc | PARTIALLY_CONFIRMED | VERIFY_STEP01 |
| SEARCH-023 | trace failure detection | AgentPex-like trace failure detection | 2026 | arXiv candidate | automatic agentic trace failure detection | failure diagnosis background | PARTIALLY_CONFIRMED | VERIFY_STEP01 |
| SEARCH-024 | web agent robustness benchmark | StressWeb / Diagnostic Benchmark for Web Agent Robustness | 2026 | arXiv candidate | shifting layouts, altered interaction semantics, execution disruptions | robustness/grammar-shift threat | PARTIALLY_CONFIRMED | VERIFY_STEP01 |
| SEARCH-025 | WorkflowPerturb | WorkflowPerturb | 2026 | arXiv candidate | controlled workflow perturbations, metric calibration | perturbation/evaluation calibration background | PARTIALLY_CONFIRMED | VERIFY_STEP10 |
| SEARCH-026 | D-GARA GUI robustness | D-GARA | 2026 | AAAI/PDF candidate | Android GUI robustness under anomalies | GUI robustness benchmark threat | PARTIALLY_CONFIRMED | VERIFY_STEP10 |
| SEARCH-027 | ST-WebAgentBench | ST-WebAgentBench | 2024 | arXiv candidate | safety/trustworthiness web agent benchmark | safety benchmark anchor | PARTIALLY_CONFIRMED | VERIFY_STEP10 |
| SEARCH-028 | Agent Q MCTS self-critique DPO | Agent Q | 2024/2025 | arXiv/ICLR candidate | guided MCTS + self-critique + DPO for web agents | tree-search/planning threat | PARTIALLY_CONFIRMED | VERIFY_STEP09 |
| SEARCH-029 | Agent-R reflection MCTS | Agent-R | 2025 | arXiv candidate | MCTS recovery trajectories from errors | recovery/search background | PARTIALLY_CONFIRMED | VERIFY_STEP09 |
| SEARCH-030 | value of computation planning | VOC/metareasoning literature | classic | broad literature | compute should be used when expected benefit exceeds cost | decision-relevant compute background | PARTIALLY_CONFIRMED | VERIFY_STEP09 |
| SEARCH-031 | Bayesian adaptive planning latent MDP | BAMDP / VariBAD family | classic/2020 | RL literature | belief over latent MDPs under uncertainty | latent hypothesis planning background | PARTIALLY_CONFIRMED | VERIFY_STEP09 |
| SEARCH-032 | change-point detection RL latent regime | BOCPD/RLCD/minimum-delay adaptation | 2007/2021+ | RL/CPD literature | context change-point detection for non-stationary RL | reveal/shift/change latent background | PARTIALLY_CONFIRMED | VERIFY_STEP09 |
| SEARCH-033 | AndroidControl benchmark | AndroidControl / AndroidControl-Curated | 2024/2025 | arXiv candidate | GUI-control benchmark; curated variants note benchmark flaws | VeriGUI robustness benchmark dependency | PARTIALLY_CONFIRMED | VERIFY_STEP10 |
| SEARCH-034 | AitZ GUI agent | Android in the Zoo | 2024 | arXiv / EMNLP candidate | chain-of-action-thought dataset, screen-action pairs | GUI dataset background | PARTIALLY_CONFIRMED | VERIFY_STEP10 |
| SEARCH-035 | GUI Odyssey benchmark | GUIOdyssey | 2025 | ICCV candidate | cross-app GUI navigation dataset | GUI benchmark anchor | PARTIALLY_CONFIRMED | VERIFY_STEP10 |
| SEARCH-036 | WebArena-Infinity | WebArena-Infinity | 2026? | site candidate | continuous/scalable evolving web agent evaluation | dynamic benchmark pressure | PARTIALLY_CONFIRMED | VERIFY_STEP10 |
| SEARCH-037 | Online-Mind2Web | Online-Mind2Web | 2025 | arXiv/HF candidate | 300 tasks on 136 live websites, benchmark optimism critique | real web external validity pressure | PARTIALLY_CONFIRMED | VERIFY_STEP10 |
| SEARCH-038 | RiskWebWorld | RiskWebWorld | 2026 | arXiv candidate | e-commerce risk-management GUI benchmark | domain-specific real benchmark anchor | PARTIALLY_CONFIRMED | VERIFY_STEP10 |
| SEARCH-039 | WebRSSBench | WebRSSBench | 2025/2026 | OpenReview candidate | web reasoning/robustness/safety for MLLMs | not direct action-loop threat | PARTIALLY_CONFIRMED | VERIFY_STEP10 |
| SEARCH-040 | C-World environment creator | C-World | 2026 | arXiv candidate | computer-use agent environment creation | synthetic environment generation pressure | PARTIALLY_CONFIRMED | VERIFY_STEP05 |

---

## 8. Paper Threat Classification Table

| Paper ID | Paper / Benchmark | Category | Core Contribution | Overlap With Our Idea | Threat Level | Threat Type | Required Defense |
|---|---|---|---|---|---|---|---|
| P-001 | WebWorld | Web agent world model | large-scale open-web simulator/world model and inference-time search | generic web world model + search를 이미 수행 | CRITICAL | WORLD_MODEL_OVERLAP | generic WM claim 폐기, grammar falsification으로 축소 |
| P-002 | WMA / DynaWeb family | Web agent world model | action outcome simulation / transition abstraction | candidate action outcome simulation | CRITICAL | WORLD_MODEL_OVERLAP | outcome prediction이 아닌 wrong hypothesis persistence로 차별화 |
| P-003 | WAC | Web agent world model/action correction | consequence simulation + judge + feedback-driven correction | action correction/replanning 경로와 직접 겹침 | CRITICAL | WORLD_MODEL_OVERLAP | evidence→hypothesis rejection→alternative grammar→rewrite 경로 필요 |
| P-004 | CUWM | Computer-use world model | current UI+candidate action→next UI state; frozen agent search | frozen base + WM-guided search와 겹침 | CRITICAL | WORLD_MODEL_OVERLAP | frozen base는 control, grammar-falsification이 contribution |
| P-005 | ViMo | GUI visual world model | future GUI image generation for action options | GUI future prediction/action option evaluation | HIGH | WORLD_MODEL_OVERLAP | visual generation claim 금지 |
| P-006 | MobileDreamer | Mobile GUI WM | textual sketch WM + rollout imagination | mobile GUI lookahead와 겹침 | HIGH | WORLD_MODEL_OVERLAP | persistence/rewrite metric을 핵심화 |
| P-007 | MobileWorldBench | GUI WM benchmark | next-state-generation/QA for mobile GUI | WM evaluation metric threat | HIGH | WORLD_MODEL_OVERLAP | alternative rollout fidelity와 persistence metric 분리 |
| P-008 | Code2World | GUI renderable code WM | next UI via renderable code generation | structured GUI future prediction 위협 | HIGH | WORLD_MODEL_OVERLAP | renderable simulation을 contribution으로 삼지 않음 |
| P-009 | VeriGUI | Action-effect verification | TVAE, action-effect verification, failure recognition/correction | falsification/evidence/recovery와 직접 겹침 | CRITICAL | VERIFICATION_OVERLAP | verifier-only baseline과 mechanism metric으로 차별화 |
| P-010 | VAGEN | GUI verification | verifier agent probes environment for completion evidence | verification/probing overlap | MEDIUM | VERIFICATION_OVERLAP | completion verification과 hypothesis falsification 분리 |
| P-011 | VSA | Logic-based mobile GUI safeguard | logic-based action verification/safety | pre-action intent/action safety overlap | MEDIUM | VERIFICATION_OVERLAP | safety 검증과 failed mapping recovery 분리 |
| P-012 | AgentRx | Failure diagnosis | critical failure step + taxonomy from trajectories | failure attribution/metric threat | HIGH | FAILURE_DIAGNOSIS_OVERLAP | post-hoc diagnosis와 online rewrite 분리 |
| P-013 | StressWeb | Web robustness benchmark | layout shift, altered semantics, execution disruptions | grammar shift/perturbation claim 위협 | HIGH | ROBUSTNESS_BENCHMARK_OVERLAP | benchmark perturbation이 아니라 internal hypothesis persistence로 정의 |
| P-014 | D-GARA | GUI robustness benchmark | Android GUI anomalies/interruption benchmark | modal/blocker/permission regime와 겹침 | MEDIUM | ROBUSTNESS_BENCHMARK_OVERLAP | anomaly robustness와 grammar persistence metric 분리 |
| P-015 | WorkflowPerturb | Workflow metric robustness | controlled perturbation severity/calibration | metric calibration background | MEDIUM | ROBUSTNESS_BENCHMARK_OVERLAP | evaluation calibration 참조로 사용 |
| P-016 | Agent Q | Search/planning web agent | guided MCTS + self-critique + DPO | alternative rollout/tree search threat | HIGH | PLANNING_SEARCH_OVERLAP | decision-relevance gate + compute-matched comparison |
| P-017 | Agent-R | Reflection/search | MCTS-based recovery data from errors | recovery/search overlap | MEDIUM | PLANNING_SEARCH_OVERLAP | tree search와 grammar hypothesis comparison 분리 |
| P-018 | WebArena | Benchmark | realistic self-hosted web tasks | external benchmark anchor | MEDIUM | BENCHMARK_ANCHOR | auxiliary validation로만 사용 |
| P-019 | VisualWebArena | Benchmark | visually grounded web tasks | visual grounding competing explanation | MEDIUM | BENCHMARK_ANCHOR | same-visual/different-grammar split 필요 |
| P-020 | MiniWoB++ | Benchmark/env | simple web interaction envs | text-only/synthetic comparison | LOW | BENCHMARK_ANCHOR | smoke-test precedent |
| P-021 | OSWorld | Benchmark | real computer tasks | real computer-use auxiliary anchor | MEDIUM | BENCHMARK_ANCHOR | hidden labels 부재 명시 |
| P-022 | WorkArena/BrowserGym | Benchmark/ecosystem | enterprise web tasks, unified env | enterprise/BrowserGym env pressure | MEDIUM | BENCHMARK_ANCHOR | enterprise realism anchor |
| P-023 | WebShop | Benchmark | simulated shopping web env | task family overlap | LOW | BENCHMARK_ANCHOR | task novelty 주장 금지 |
| P-024 | Mind2Web | Dataset | real website tasks/action sequences | offline generalist web dataset | LOW | BENCHMARK_ANCHOR | auxiliary data only |
| P-025 | SeeAct | Generalist web agent | GPT-4V based web agent, grounding issue | visual grounding/base agent context | MEDIUM | BACKGROUND_ONLY | grounding baseline 필요 |
| P-026 | WebVoyager | Generalist web agent | real-world LMM web agent | strong base-agent context | MEDIUM | BACKGROUND_ONLY | stronger base stratification 필요 |
| P-027 | AndroidControl | GUI benchmark | mobile GUI-control dataset | VeriGUI/Android benchmarks context | LOW | BENCHMARK_ANCHOR | benchmark dependency audit |
| P-028 | AitZ | GUI dataset | chain-of-action-thought screen-action pairs | GUI action data background | LOW | BENCHMARK_ANCHOR | optional background |
| P-029 | ST-WebAgentBench | Safety benchmark | safety/trustworthiness for web agents | safety benchmark only | LOW | BENCHMARK_ANCHOR | safety claim 금지 |
| P-030 | C-World | Environment generator | computer-use environment creation | synthetic environment generation pressure | MEDIUM | BENCHMARK_ANCHOR | anti-toy generation 설계 압박 |

---

## 9. Direct Threat Deep Dive

### 9.1 Web Agent World Model Threats

| Paper ID | What It Already Does | What It Does Not Clearly Do | Threat To Us | Required Defense |
|---|---|---|---|---|
| P-001 WebWorld | open-web simulator/world model, long-horizon simulation, inference-time search, trajectory synthesis | wrong-control-grammar persistence metric, explicit control-grammar latent, evidence likelihood ratio는 확인 필요 | “웹 world model은 이미 했다” 공격의 최상위 위협 | FRCG-WM은 generic web simulator가 아니라 wrong grammar persistence를 측정하고 줄이는 planning layer라고 축소 |
| P-002 WMA | action outcome simulation으로 policy selection을 돕는 web world model 계열 | current hypothesis falsification, grammar posterior, persistence metric은 확인 필요 | action outcome simulation novelty를 거의 제거 | outcome simulation이 아니라 executed hypothesis persistence와 rewrite latency를 metric화 |
| P-003 WAC | consequence simulation, judge model, feedback-driven action refinement | control grammar latent, current-vs-alt grammar likelihood ratio는 확인 필요 | action correction/rewrite claim을 강하게 위협 | generic feedback correction과 grammar-conditioned intent-to-action rewrite를 분리 |
| P-023 WebShop | simulated shopping website and agent benchmark | world model/falsification은 아님 | shopping synthetic task가 새롭지 않다는 배경 위협 | task family가 아니라 mechanism/label/evaluation이 contribution이라고 명시 |
| P-036 WebArena-Infinity | evolving/scalable web evaluation을 지향하는 benchmark 계열 | grammar label/falsification은 확인 필요 | synthetic/evolving env 설계 압박 | controlled causal label 목적을 명확히 함 |

### 9.2 GUI / Mobile / Computer-Use World Model Threats

| Paper ID | What It Already Does | What It Does Not Clearly Do | Threat To Us | Required Defense |
|---|---|---|---|---|
| P-004 CUWM | desktop software에서 candidate action 이후 next UI state를 예측하고 frozen agent의 test-time search에 사용 | wrong grammar persistence, grammar latent 분리, falsification ratio는 확인 필요 | frozen base + WM-guided search 패턴 선점 | base freezing은 novelty가 아니라 fair control이고, contribution은 grammar falsification/rewrite라고 정의 |
| P-005 ViMo | future GUI observation image를 생성해 action option evaluation | control grammar hypothesis나 falsification은 중심이 아님 | GUI visual world model novelty 제거 | screenshot generation을 contribution에서 제외, structured action-effect log 중심 |
| P-006 MobileDreamer | textual sketch world model로 mobile GUI post-action state 예측/lookahead | grammar persistence metric 없음 | lightweight GUI lookahead threat | lookahead보다 wrong mapping switch delay 감소를 증명 |
| P-007 MobileWorldBench | mobile GUI future state prediction benchmark | failure mechanism/control grammar posterior 없음 | world-model evaluation metric overlap | rollout fidelity만으로 논문 claim을 만들지 말고 persistence/rewrite metric과 연결 |
| P-008 Code2World | renderable code로 next GUI state 예측 | intent-to-action grammar rewrite가 핵심은 아님 | structured GUI simulation novelty 위협 | structural GUI generation이 아니라 grammar-level abstraction으로 포지셔닝 |

### 9.3 Action-Effect Verification Threats

| Paper ID | What It Already Does | What It Does Not Clearly Do | Threat To Us | Required Defense |
|---|---|---|---|---|
| P-009 VeriGUI | action-effect verification, TVAE, failure recognition/correction, synthetic failure trajectories, asymmetric GRPO reward | control grammar를 latent hypothesis로 분리하고 current-vs-alt likelihood ratio로 falsification하는지는 확인 필요 | action-effect evidence/failure loop/recovery claim을 정면 위협 | `verifier-only`를 high-threat baseline으로 두고 persistence, switch delay, alternative grammar adoption에서 추가 이득 필요 |
| P-010 VAGEN | verifier agent가 환경을 능동적으로 probe하여 task completion evidence 수집 | action grammar persistence/rewrite는 중심 아님 | evidence collection/verification overlap | evidence collection과 hypothesis falsification의 차이를 Step 02에서 정의 |
| P-011 VSA | action이 user intent/safety에 맞는지 logic-based safeguard | post-action evidence 기반 grammar switching은 아님 | pre-action safety/verification overlap | action safety와 failed mapping recovery를 분리 |

### 9.4 Failure Diagnosis Threats

| Paper ID | What It Already Does | What It Does Not Clearly Do | Threat To Us | Required Defense |
|---|---|---|---|---|
| P-012 AgentRx | failed trajectory에서 critical failure step과 taxonomy를 찾는다 | closed-loop next-action rewrite/planning layer는 아님 | failure diagnosis/taxonomy novelty 위협 | 우리는 사후 진단이 아니라 online belief update/rewrite로 포지셔닝 |
| P-023 Trace failure detection | agentic trace failure detection | GUI grammar hypothesis는 아님 | failure detection claim 약화 | detection이 아니라 grammar-specific action rewrite metric 필요 |
| P-015 WorkflowPerturb | workflow perturbation severity/metric calibration | GUI/Web action grammar 자체는 아님 | metric calibration pressure | 우리 evaluation에서 perturbation severity와 mechanism metric을 함께 보고 |

### 9.5 Robustness Benchmark Threats

| Paper ID | What It Already Does | What It Does Not Clearly Do | Threat To Us | Required Defense |
|---|---|---|---|---|
| P-013 StressWeb | layout shift, altered interaction semantics, execution disruptions | latent control grammar posterior/rewrite는 아님 | altered interaction semantics가 grammar shift와 매우 가까움 | grammar shift를 benchmark perturbation이 아니라 model-internal wrong hypothesis persistence로 계량 |
| P-014 D-GARA | Android GUI anomalies/dialogs/warnings/interruption | grammar abstraction은 불명확 | modal/permission/blocker regime claim 위협 | anomaly robustness와 grammar-persistence metric을 분리 |
| P-015 WorkflowPerturb | workflow perturbation severity/calibration | agent internal belief update는 아님 | evaluation calibration overlap | perturbation severity vs persistence/recovery mediation 분석 추가 |
| P-029 ST-WebAgentBench | safety/trustworthiness benchmark | grammar hypothesis는 아님 | safety evaluation background | safety claim은 하지 않음 |

### 9.6 General Benchmark Anchors

| Paper ID | What It Already Does | What It Does Not Clearly Do | Threat To Us | Required Defense |
|---|---|---|---|---|
| P-018 WebArena | realistic self-hosted web tasks와 execution-based success | hidden grammar labels 없음 | synthetic toy criticism 완화용 | auxiliary validation에만 사용 |
| P-019 VisualWebArena | visually grounded web task benchmark | grammar label 없음 | visual grounding competing explanation | same visual / different grammar split으로 분리 |
| P-020 MiniWoB++ | simple web interaction tasks | modern robustness/grammar shift 제한 | smoke-test comparison | text-only smoke와 MiniWoB 차이 명시 |
| P-021 OSWorld | real computer-use tasks | grammar labels 없음 | external validity anchor | weak inferred metrics만 가능 |
| P-022 WorkArena/BrowserGym | enterprise browser tasks | grammar labels 없음 | enterprise realism pressure | BrowserGym compatibility optional |
| P-024 Mind2Web | real websites/action sequences | online causal state label 부족 | generalist dataset anchor | offline action sequence는 auxiliary only |
| P-025 SeeAct | LMM web agent, grounding challenge | world model/falsification 아님 | grounding explanation 경쟁 | grounding baseline과 grammar shift split 분리 |
| P-026 WebVoyager | real-world LMM web agent | grammar metric 없음 | strong base-agent context | stronger frozen-base variants에서 평가 필요 |

---

## 10. 12-Question Novelty Overlap Matrix

질문 정의:

- Q1: Web/GUI/Computer-use agent를 다루는가?
- Q2: world model을 쓰는가?
- Q3: action outcome을 예측하는가?
- Q4: failed action을 검증하는가?
- Q5: failure diagnosis를 하는가?
- Q6: alternative action/search를 수행하는가?
- Q7: latent regime을 학습하는가?
- Q8: control grammar를 명시적으로 다루는가?
- Q9: intent-to-action mapping rewrite를 명시적으로 다루는가?
- Q10: current vs alternative hypothesis를 비교하는가?
- Q11: action-effect evidence를 hypothesis falsification으로 쓰는가?
- Q12: wrong-hypothesis persistence를 metric으로 측정하는가?

| Paper ID | Q1 | Q2 | Q3 | Q4 | Q5 | Q6 | Q7 | Q8 | Q9 | Q10 | Q11 | Q12 | Summary |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| P-001 WebWorld | YES | YES | YES | PARTIAL | NO | YES | UNKNOWN | NO | NO | PARTIAL | NO | NO | generic web WM과 search는 강하지만 grammar falsification은 확인 안 됨 |
| P-002 WMA | YES | YES | YES | PARTIAL | NO | YES | NO | NO | NO | PARTIAL | NO | NO | action outcome simulation threat가 큼 |
| P-003 WAC | YES | YES | YES | PARTIAL | PARTIAL | YES | NO | NO | PARTIAL | PARTIAL | NO | NO | action correction은 강한 overlap, hypothesis falsification은 불명확 |
| P-004 CUWM | YES | YES | YES | PARTIAL | NO | YES | UNKNOWN | NO | NO | PARTIAL | NO | NO | frozen agent + WM search 직접 위협 |
| P-005 ViMo | YES | YES | YES | NO | NO | PARTIAL | NO | NO | NO | NO | NO | NO | visual GUI future prediction 위협 |
| P-006 MobileDreamer | YES | YES | YES | NO | NO | PARTIAL | NO | NO | NO | NO | NO | NO | GUI lookahead 위협 |
| P-007 MobileWorldBench | YES | YES | YES | NO | NO | NO | NO | NO | NO | NO | NO | NO | WM evaluation benchmark 위협 |
| P-008 Code2World | YES | YES | YES | NO | NO | PARTIAL | NO | NO | NO | NO | NO | NO | GUI next-state simulation 위협 |
| P-009 VeriGUI | YES | PARTIAL | YES | YES | PARTIAL | PARTIAL | NO | NO | PARTIAL | NO | PARTIAL | PARTIAL | action-effect verification/failure loop direct threat |
| P-010 VAGEN | YES | NO | NO | YES | PARTIAL | PARTIAL | NO | NO | NO | NO | NO | NO | verification/probing overlap |
| P-011 VSA | YES | NO | NO | YES | NO | NO | NO | NO | PARTIAL | NO | NO | NO | action safeguard overlap |
| P-012 AgentRx | PARTIAL | NO | NO | NO | YES | NO | NO | NO | NO | NO | NO | NO | post-hoc diagnosis threat |
| P-013 StressWeb | YES | NO | NO | NO | PARTIAL | NO | NO | PARTIAL | NO | NO | NO | PARTIAL | altered semantics/robustness threat |
| P-016 Agent Q | YES | NO | NO | NO | PARTIAL | YES | NO | NO | NO | NO | NO | NO | tree search/planning threat |
| P-018 WebArena | YES | NO | NO | NO | NO | NO | NO | NO | NO | NO | NO | NO | benchmark anchor |
| P-019 VisualWebArena | YES | NO | NO | NO | NO | NO | NO | NO | NO | NO | NO | NO | visual grounding benchmark anchor |
| P-020 MiniWoB++ | YES | NO | NO | NO | NO | NO | NO | NO | NO | NO | NO | NO | synthetic web benchmark anchor |
| P-021 OSWorld | YES | NO | NO | NO | NO | NO | NO | NO | NO | NO | NO | NO | computer-use benchmark anchor |
| P-022 WorkArena | YES | NO | NO | NO | NO | NO | NO | NO | NO | NO | NO | NO | enterprise benchmark anchor |
| P-024 Mind2Web | YES | NO | NO | NO | NO | NO | NO | NO | NO | NO | NO | NO | generalist web dataset |
| P-025 SeeAct | YES | NO | NO | NO | NO | NO | NO | NO | NO | NO | NO | NO | grounding/base-agent background |

---

## 11. Reviewer Attack Ledger

| Attack ID | Reviewer Attack | Existing Work That Enables This Attack | Why Dangerous | Defense Needed | Later Step |
|---|---|---|---|---|---|
| ATK-001 | “이미 WebWorld가 web world model을 했다.” | WebWorld | generic web world model claim은 즉시 사망 | claim을 control-grammar falsification layer로 좁힘 | 02 |
| ATK-002 | “이미 WMA가 action outcome simulation으로 web agent policy를 개선했다.” | WMA | outcome prediction novelty 제거 | outcome prediction이 아니라 wrong hypothesis persistence metric 전면화 | 02, 10 |
| ATK-003 | “이미 WAC가 consequence simulation/action correction을 했다.” | WAC | action correction/rewrite overlap | evidence→posterior→alternative grammar→rewrite 경로 입증 | 02, 09 |
| ATK-004 | “이미 CUWM이 frozen agent + world model test-time search를 했다.” | CUWM | architecture pattern overlap | frozen base는 novelty가 아니라 control variable로 격하 | 07, 10 |
| ATK-005 | “이미 ViMo/MobileDreamer가 GUI future prediction/lookahead를 했다.” | ViMo, MobileDreamer | GUI world model novelty 제거 | visual future prediction을 contribution에서 제외 | 02 |
| ATK-006 | “이미 Code2World가 더 강한 structured GUI simulator를 만들었다.” | Code2World | synthetic GUI simulation claim 약화 | renderable simulation이 아니라 hypothesis metric/label이 핵심 | 05, 06 |
| ATK-007 | “이미 VeriGUI가 action-effect verification/recovery/failure loop reduction을 했다.” | VeriGUI | action-effect evidence/failure loop/recovery claim을 정면 위협 | verifier-only baseline과 비교해 persistence/switch delay 추가 개선 필요 | 02, 10 |
| ATK-008 | “이미 AgentRx가 failure taxonomy와 diagnosis를 했다.” | AgentRx | failure definition/taxonomy novelty 약화 | online planning/rewrite와 post-hoc diagnosis 분리 | 02 |
| ATK-009 | “robustness benchmark가 이미 altered interaction semantics를 다룬다.” | StressWeb | grammar shift가 새롭지 않아 보임 | altered semantics를 model-internal wrong hypothesis persistence로 재정의 | 03, 10 |
| ATK-010 | “이건 그냥 tree search다.” | Agent Q, MCTS agents | alternative rollout novelty 약화 | action choice가 바뀔 때만 compute를 쓰는 decision-relevance gate 증명 | 09, 10 |
| ATK-011 | “이건 그냥 uncertainty-gated planning이다.” | generic uncertainty search | compute gate novelty 약화 | uncertainty가 아니라 expected action switch/value gap 기준임을 실험 | 09, 10 |
| ATK-012 | “control grammar는 새로운 용어일 뿐이다.” | GUI/action semantics/affordance literature | 핵심 개념이 말장난으로 보임 | taxonomy, label, metric, no-control-grammar ablation 필수 | 03, 07, 10 |
| ATK-013 | “synthetic benchmark는 toy다.” | WebArena, OSWorld, WorkArena | 메인트랙 방어력 약화 | synthetic은 causal label 목적, real benchmark는 auxiliary로 명시 | 05, 10 |
| ATK-014 | “hidden labels가 비현실적이다.” | real web benchmarks | supervised classifier로 보일 위험 | label-free/noisy-label/weak-label stress test 필요 | 06, 10 |
| ATK-015 | “Base LLM이 강하면 module gain이 사라진다.” | WebVoyager/SeeAct/strong base agents | empirical result 약화 | multi-base, weak/strong base stratified evaluation | 10 |
| ATK-016 | “metric이 success rate와 독립적이지 않다.” | benchmark metric criticism | 새 metric 의미 약화 | persistence↓ → recovery↓ → return↑ mediation/evidence chain | 10 |
| ATK-017 | “latent regime/control grammar가 identifiable하지 않다.” | latent variable criticism | architecture claim 붕괴 | probe, label intervention, merged-latent ablation 필요 | 07, 10 |
| ATK-018 | “VeriGUI의 asymmetric reward와 switch/recovery reward가 비슷하다.” | VeriGUI | reward novelty 약화 | reward를 novelty로 삼지 않고 support mechanism으로 격하 | 08 |
| ATK-019 | “WAC의 feedback-driven action refinement가 action rewrite와 같다.” | WAC | rewrite novelty 약화 | grammar-conditioned rewrite와 generic feedback correction 차이 입증 | 09, 10 |
| ATK-020 | “StressWeb의 altered interaction semantics가 control grammar shift와 같다.” | StressWeb | problem novelty 약화 | benchmark perturbation vs internal hypothesis persistence 분리 | 02, 03 |
| ATK-021 | “real benchmark에서 core metric을 못 재면 논문이 약하다.” | WebArena/OSWorld/WorkArena | hidden label limitation | synthetic core + real auxiliary를 명확히 분리 | 06, 10 |
| ATK-022 | “world model fidelity가 낮으면 planning claim이 성립하지 않는다.” | WM literature | rollout-based method 붕괴 | alternative rollout fidelity metric 필요 | 09, 10 |

---

## 12. Surviving Novelty Candidates

모든 항목은 `may survive`이다. 아직 verified novelty가 아니다.

| Surviving Novelty ID | Novelty Candidate | Direct Threats Considered | Why It May Survive | Required Evidence | Failure Trigger | Assigned Step |
|---|---|---|---|---|---|---|
| SN-001 | measurable wrong-control-grammar hypothesis persistence | VeriGUI, AgentRx, StressWeb | 기존 연구는 failure loop/diagnosis/perturbation을 다루지만 “틀린 intent-to-action grammar hypothesis 유지 시간”을 독립 metric으로 명시하는 증거는 약함 | metric definition, trace labeling, no-control-grammar ablation | persistence metric이 success/failure count와 중복되면 약화 | 02, 10 |
| SN-002 | latent separation of regime and control grammar | CUWM, MobileDreamer, ViMo, StressWeb | 기존 GUI WM은 future state/outcome 중심이며 regime과 grammar의 분리 supervision/ablation은 명시 약함 | taxonomy, identifiability probe, merged-latent ablation | merged latent가 더 좋으면 약화 | 03, 07, 10 |
| SN-003 | action-effect evidence as falsification, not just verification | VeriGUI, VAGEN, VSA | verification은 실패 감지에 머물 수 있으나, hypothesis likelihood ratio로 current grammar를 반증하는 구조는 생존 가능 | likelihood-ratio F_t, verifier-only baseline, falsification P/R | verifier-only와 비슷하면 약화 | 02, 09, 10 |
| SN-004 | current-vs-alternative control-grammar rollout | WAC, WMA, CUWM, Agent Q | 기존은 candidate action outcome/search 중심이고, grammar hypothesis posterior 비교는 명시 약함 | top-k alt fidelity, random-alt/oracle-alt baseline | random alternative와 비슷하면 약화 | 09, 10 |
| SN-005 | intent-to-action interface rewrite conditioned on grammar | WAC, VeriGUI | generic correction과 다르게 intent-to-action/precondition/effect schema를 바꾼다면 생존 가능 | macro action oracle, rewrite accuracy, action switch delay | no-rewrite ablation이 안 무너지면 약화 | 03, 07, 09, 10 |
| SN-006 | decision-relevant compute reallocation based on action-switch value | Agent Q, uncertainty-gated planning | 단순 uncertainty가 아니라 action choice/value gap이 바뀔 때만 compute를 쓰면 차별 가능 | uncertainty-gate, always-plan, random reallocation과 compute-matched 비교 | uncertainty-gated와 같으면 약화 | 09, 10 |
| SN-007 | reveal-vs-shift aware belief update | StressWeb, D-GARA | perturbation benchmark는 shift를 평가하지만 belief update factorization까지는 명시 약함 | reveal/shift label accuracy, shift-specific recovery gain | reveal/shift classifier가 낮으면 약화 | 03, 06, 07, 10 |

---

## 13. Design Revision Pressure Table

| Revision ID | Threat Source | Original Assumption | Why It Is Weak | Required Revision | Affected Ref IDs |
|---|---|---|---|---|---|
| REV-001 | WebWorld/WMA/CUWM/WAC | “우리는 Web/GUI world model을 만든다” | 이미 직접 선점된 claim | “falsification-guided control grammar planning layer”로 좁힘 | REF-CORE-020 |
| REV-002 | WAC | “action correction/rewrite가 novelty다” | WAC가 feedback-driven action correction 수행 | grammar-conditioned interface rewrite로 정의 | REF-CORE-005, REF-ARCH-015 |
| REV-003 | VeriGUI | “action-effect evidence가 novelty다” | VeriGUI가 action-effect verification을 정면으로 다룸 | verification이 아니라 hypothesis falsification likelihood ratio로 정의 | REF-CORE-003, REF-LOSS-005 |
| REV-004 | CUWM | “frozen base + WM search가 novelty다” | CUWM이 test-time action search를 수행 | frozen base는 control variable로 격하 | REF-CORE-007 |
| REV-005 | ViMo/MobileDreamer/Code2World | “future GUI prediction이 contribution이다” | 이미 강한 GUI future prediction 연구 존재 | screenshot/future-state generation을 contribution에서 제외하고 structured action-effect log 중심 | REF-DATA-004, REF-ARCH-012 |
| REV-006 | StressWeb | “grammar shift benchmark가 새롭다” | altered interaction semantics benchmark가 존재 | benchmark novelty가 아니라 persistence metric/model update novelty로 이동 | REF-PROBLEM-006 |
| REV-007 | Agent Q | “alternative rollout이 planning novelty다” | MCTS/search로 공격 가능 | decision-relevant gate + grammar-conditioned alternative만 남김 | REF-CORE-004, REF-CORE-006 |
| REV-008 | AgentRx | “failure taxonomy가 novelty다” | AgentRx가 failure taxonomy/critical step 제공 | taxonomy는 support, online rewrite가 novelty 후보 | REF-PROBLEM-001 |
| REV-009 | real benchmark literature | “real benchmark에서 core metric 검증 가능” | grammar labels 없음 | real benchmark는 auxiliary, core causal proof는 synthetic | REF-CORE-019 |
| REV-010 | latent identifiability criticism | “4-latent가 자연스럽다” | 자연스러움은 증거가 아님 | merged-latent/no-grammar/no-regime ablation + probes 추가 | REF-CORE-011 |
| REV-011 | reward hacking risk | “switch reward가 좋은 설계다” | switch 자체 보상은 hacking 위험 | valid switch reward는 progress-linked 조건부로만 유지 | REF-REWARD-005 |
| REV-012 | benchmark quality criticism | “benchmark 점수는 신뢰 가능” | benchmark flaws/curated variants 존재 | evaluation reliability audit 포함 | REF-METRIC-* |
| REV-013 | base agent strength | “한 base에서만 보이면 충분” | LLM이 좋아서 된 것 공격 | frozen base 2~3종, same candidate budget | REF-CORE-007 |
| REV-014 | rollout horizon | “horizon=3이면 충분” | arbitrary design 공격 | horizon=1/3/5 sweep | REF-CORE-004 |
| REV-015 | top-k alternatives | “k=3이면 충분” | arbitrary design 공격 | k=1/3/5/oracle-alt/random-alt 비교 | REF-ARCH-011 |

---

## 14. Related Work Grouping Proposal

| Group ID | Related Work Group | Papers Included | Why This Group Matters | Our Positioning |
|---|---|---|---|---|
| RWG-001 | Web and GUI Agent Benchmarks | WebArena, VisualWebArena, MiniWoB++, OSWorld, WorkArena, BrowserGym, WebShop, Mind2Web, WebVoyager | 실험 anchor와 competing explanation 제공 | core proof는 synthetic, external validity는 auxiliary |
| RWG-002 | World Models for Web/GUI Agents | WebWorld, WMA, WAC, CUWM, ViMo, MobileDreamer, MobileWorldBench, Code2World | generic world model novelty를 직접 위협 | next-state/outcome prediction이 아니라 grammar falsification으로 포지셔닝 |
| RWG-003 | Action-Effect Verification and Self-Correction | VeriGUI, VAGEN, VSA | action-effect evidence/recovery claim을 위협 | verification→posterior update→alternative grammar→rewrite로 구분 |
| RWG-004 | Failure Diagnosis for Agents | AgentRx, trace failure detection papers | failure taxonomy/critical step novelty를 위협 | post-hoc diagnosis가 아니라 online planning/rewrite로 구분 |
| RWG-005 | Robustness Evaluation for Web/GUI Agents | StressWeb, D-GARA, WorkflowPerturb, ST-WebAgentBench | perturbation/altered semantics가 grammar shift와 가까움 | robustness benchmark가 아니라 model-internal persistence metric으로 구분 |
| RWG-006 | Model-Based Planning, Hypothesis Testing, and Value of Computation | Agent Q, Agent-R, BAMDP/VariBAD, VOC, BOCPD/RLCD | tree search/VOC/latent regime background 제공 | 일반 planning이 아니라 decision-relevant grammar switching으로 구분 |

---

## 15. Risk / Unknown Ledger Updated From Step 01

| Risk ID | Risk / Unknown | Triggered By Which Paper? | Why It Matters | How Later Steps Must Resolve | Severity |
|---|---|---|---|---|---|
| RISK-01-001 | generic Web/GUI world model novelty is dead | WebWorld, WMA, CUWM, WAC, ViMo | broad claim 사용 시 reject 위험 | Step 02에서 claim 축소 | CRITICAL |
| RISK-01-002 | action correction novelty is weak | WAC, VeriGUI | rewrite claim이 generic correction으로 보일 수 있음 | Step 03/09에서 grammar-conditioned rewrite 정의 | CRITICAL |
| RISK-01-003 | verification vs falsification boundary unclear | VeriGUI, VAGEN, VSA | 핵심 차별점이 흐려짐 | Step 02에서 formal falsification 조건 정의 | CRITICAL |
| RISK-01-004 | control grammar may be relabeled affordance/precondition | VSA, GUI action semantics | 용어 장난 공격 | Step 03 taxonomy + Step 10 ablation 필요 | CRITICAL |
| RISK-01-005 | synthetic env may look toy | WebArena, OSWorld, WorkArena | 메인트랙 설득력 약화 | Step 05에서 causal label 목적과 real auxiliary 분리 | HIGH |
| RISK-01-006 | hidden grammar labels unrealistic | real web benchmarks | real transfer claim 불가 | Step 06 weak/noisy label protocol 필요 | HIGH |
| RISK-01-007 | alternative rollout indistinguishable from search | Agent Q, WAC | novelty collapse | Step 09 gate/value/action-switch formalization | CRITICAL |
| RISK-01-008 | compute gate indistinguishable from uncertainty threshold | generic planning | compute reallocation claim 약화 | Step 09/10 uncertainty-gate baseline 필수 | HIGH |
| RISK-01-009 | persistence metric duplicates failure-loop metric | VeriGUI | metric novelty 약화 | Step 10 correlation/mediation analysis | CRITICAL |
| RISK-01-010 | no-control-grammar ablation may not drop | latent factor risk | core claim 붕괴 | Step 07/10 ablation 설계 강화 | CRITICAL |
| RISK-01-011 | Strong base agent reduces gain | WebVoyager, SeeAct | empirical result 약화 | Step 10 base-strength stratification | HIGH |
| RISK-01-012 | world model fidelity may not matter | WMA/MobileWorldBench | alternative rollout quality 검증 필요 | Step 10 alternative rollout fidelity metric | HIGH |
| RISK-01-013 | altered semantics already covered | StressWeb | problem novelty 약화 | Step 02에서 internal hypothesis persistence로 재정의 | HIGH |
| RISK-01-014 | reward design not novel | VeriGUI, Agent Q | reward contribution으로 보이면 약함 | Step 08에서 reward는 support로 둠 | MEDIUM |
| RISK-01-015 | benchmark quality could mislead results | AndroidControl-Curated 등 | 결과 신뢰도 공격 | Step 10 benchmark audit/label audit 포함 | MEDIUM |
| RISK-01-016 | screenshot/DOM modality claim conflict | ViMo, Code2World | visual prediction 연구와 비교 필요 | Step 05/07에서 modality role 고정 | MEDIUM |
| RISK-01-017 | real benchmark cannot measure grammar persistence | WebArena/OSWorld | external validation 제한 | Step 10에서 auxiliary metric만 사용 | HIGH |
| RISK-01-018 | AgentRx-style taxonomy may already classify failure causes | AgentRx | failure category novelty 약화 | Step 02에서 category가 아니라 persistence dynamics로 정의 | MEDIUM |
| RISK-01-019 | paper anchors may drift because 2026 papers are recent | WebWorld/WAC/CUWM/VeriGUI | citation and venue details may change | final paper must re-check metadata before submission | HIGH |
| RISK-01-020 | using too many related works may diffuse the claim | all groups | contribution framing becomes unclear | final thesis limited to 3~5 claims | MEDIUM |

---

## 16. Handoff to Later Steps

| Handoff ID | Target Step | What Must Be Used | What Must Be Verified | What Must Not Be Assumed |
|---|---|---|---|---|
| H-01-02 | 02_PROBLEM_NOVELTY_FALSIFICATION.md | P-001~P-013, ATK-001~022, SN-001~007 | problem claim이 action failure/verification/robustness와 분리되는지 | novelty가 이미 살아남았다고 가정 금지 |
| H-01-03 | 03_CORE_CONCEPT_TAXONOMY.md | REF-CONCEPT-001~007, RISK-01-004, REV-002/003/006 | regime/control grammar/reveal/shift/current hypothesis 정의 | control grammar가 자명하다고 가정 금지 |
| H-01-04 | 04_TEXT_ONLY_SMOKE_TESTBED.md | MiniWoB++, WebShop, StressWeb, synthetic toy risk | text-only가 lexical shortcut이 아닌지 | smoke test 성공이 GUI 성공을 의미한다고 가정 금지 |
| H-01-05 | 05_SYNTHETIC_WEB_GUI_ENVIRONMENT.md | WebArena, BrowserGym, StressWeb, D-GARA, C-World | synthetic env가 causal labels와 realism을 모두 갖는지 | benchmark novelty를 claim으로 쓰지 말 것 |
| H-01-06 | 06_DATA_SCHEMA_AND_LABELING.md | hidden label risk, VeriGUI failure trajectory, StressWeb perturbation | label leakage/expected-effect leakage 제거 | hidden labels가 real env에서 가능하다고 가정 금지 |
| H-01-07 | 07_LATENT_ARCHITECTURE_DESIGN.md | CUWM, MobileDreamer, ViMo, Code2World, latent identifiability risk | 4-latent 분리 가능성과 필요성 | latent가 자연스럽다는 이유만으로 채택 금지 |
| H-01-08 | 08_LOSS_REWARD_TRAINING_OBJECTIVE.md | VeriGUI reward, WAC correction, Agent Q search reward, REV-011 | switch/recovery reward hacking 방지 | reward를 novelty claim으로 격상 금지 |
| H-01-09 | 09_PLANNING_THEORY_ALGORITHM.md | Agent Q, WAC, CUWM, VOC/BAMDP background | alternative rollout이 tree search/uncertainty gate와 다른지 | 일반 MCTS보다 새롭다고 단정 금지 |
| H-01-10 | 10_EVALUATION_BASELINE_ABLATION.md | all DIRECT_THREAT papers, matrix, attacks, risks | verifier-only, WAC-style, CUWM-style, uncertainty-gate, no-grammar ablation | base success rate만으로 claim 증명 금지 |
| H-01-FINAL | FINAL_RESEARCH_BLUEPRINT.md | SN candidates, direct threats, revision pressure | final claims are conditional and evidence-bound | `may survive`를 verified novelty로 승격 금지 |

---

## 17. Claude Code Action Contract

Claude Code가 후속 파일을 생성하거나 수정할 때 아래 계약을 지켜야 한다.

| Contract ID | Rule | Why It Matters | Violation Consequence |
|---|---|---|---|
| CC-01 | Step 02에서 ATK-001~022를 모두 problem falsification에 반영한다 | direct threat를 숨기면 novelty가 약해짐 | problem claim overclaim |
| CC-02 | Step 03에서 `control grammar`를 반드시 precondition/effect/action-interface와 분리 정의한다 | 말장난 공격 방어 | taxonomy collapse |
| CC-03 | Step 05에서 synthetic env는 “benchmark novelty”가 아니라 “causal label lab”으로 설계한다 | toy criticism 방어 | environment contribution 과장 |
| CC-04 | Step 06에서 hidden labels와 counterfactual labels를 agent input에서 제외한다 | leakage 방지 | 실험 무효 |
| CC-05 | Step 07에서 4-latent를 확정하지 말고 merged/collapsed/hierarchical 비교를 포함한다 | identifiability risk 방어 | architecture claim 취약 |
| CC-06 | Step 08에서 reward를 novelty로 만들지 말고 learning/planning support로 둔다 | reward overlap 방어 | VeriGUI/Agent Q와 충돌 |
| CC-07 | Step 09에서 uncertainty-gate와 falsification/VOC gate를 엄격히 분리한다 | planning novelty 방어 | compute claim 붕괴 |
| CC-08 | Step 10에서 WAC/CUWM/VeriGUI/uncertainty/always-plan/no-grammar를 필수 baseline/ablation으로 넣는다 | reviewer attack 방어 | evaluation insufficiency |
| CC-09 | FINAL에서 direct threat를 약하게 축소하지 않는다 | 신뢰성 유지 | related work section 부실 |
| CC-10 | 모든 `PARTIALLY_CONFIRMED` anchor는 final submission 전에 primary source로 재검증한다 | citation quality 보장 | 잘못된 인용 위험 |

---

## 18. Quality Gate Result

| Gate ID | Gate | PASS/FAIL/PARTIAL | Evidence | If Not PASS, Blocker |
|---|---|---|---|---|
| QG-01-01 | 00_MASTER_REFERENCE.md refs imported | PASS | 40개 이상 REF 계열 import | 없음 |
| QG-01-02 | search groups 7개 이상 수행 | PASS | SG-01~SG-08 | 없음 |
| QG-01-03 | citation-grade anchors added | PASS_WITH_RISK | CITE-001~018 | 일부 2026 candidate는 final 전 재검증 필요 |
| QG-01-04 | search ledger 35개 이상 작성 | PASS | SEARCH-001~040 | 없음 |
| QG-01-05 | paper threat table 25개 이상 작성 | PASS | P-001~030 | 없음 |
| QG-01-06 | direct threat deep dive 수행 | PASS | §9.1~§9.6 | 없음 |
| QG-01-07 | 12-question matrix 15개 이상 작성 | PASS | 20개 paper row | 없음 |
| QG-01-08 | reviewer attack 15개 이상 작성 | PASS | ATK-001~022 | 없음 |
| QG-01-09 | surviving novelty candidates 5개 이상 작성 | PASS | SN-001~007 | 없음 |
| QG-01-10 | design revision pressure 10개 이상 작성 | PASS | REV-001~015 | 없음 |
| QG-01-11 | no novelty claim prematurely finalized | PASS | 모든 novelty는 `may survive`로 표기 | 없음 |
| QG-01-12 | direct threats were not hidden | PASS | WebWorld/WMA/WAC/CUWM/VeriGUI/StressWeb를 CRITICAL/HIGH로 표시 | 없음 |
| QG-01-13 | search uncertainty preserved | PASS | PARTIALLY_CONFIRMED / VERIFY_STEP 유지 | 없음 |
| QG-01-14 | Claude Code routing included | PASS | §2, §17 | 없음 |
| QG-01-15 | final handoff is actionable | PASS | H-01-02~H-01-FINAL | 없음 |

---

## 19.1 Phase 9 Update — Sequential Change-Point Detection Direct Threats

**Update source**: Phase 9 end-to-end evidence run (2026-05-19), novelty-threat-scout report.
**Cross-verification**: arXiv primary sources + Semantic Scholar.

These two papers were identified as CONFIRMED_PRIMARY direct threats to LFD novelty during Phase 9 evaluation. They were not in the original threat map and must be addressed before any falsification detector claim.

| Threat ID | Paper | Year | arXiv | Threat Level | What It Does | What It Does Not Do | Required Defense |
|---|---|---|---|---|---|---|---|
| CPD-001 | Neural Network-based CUSUM for Online Change-Point Detection (Gong & Lee, AAAI 2024) | 2024 | 2210.17312 | **CRITICAL** | Learned CPD that replaces the CUSUM statistic with a neural network, achieving theoretical guarantees (ARL/EDD) better than classical CUSUM without distributional assumptions. Semantic Scholar confirmed. | Web/GUI grammar-specific hypothesis falsification. Does not decompose regime × grammar latent. No alternative hypothesis rollout. | "LFD > CUSUM" claim must show advantage over NN-CUSUM, not just classical CUSUM. Until then, LFD AUROC advantage claim is relative to a weak baseline. |
| CPD-002 | Restarted Bayesian Online Change-Point Detection for Non-Stationary MDPs (Parker-Holder et al.) | 2023 | 2304.00232 | **CRITICAL** | R-BOCPD applied to non-stationary RL: detects regime changes online and restarts policy. Structurally isomorphic to LFD: BOCPD run-length posterior + policy switch + online update. MLG Cambridge confirmed. | Grammar-specific control hypothesis decomposition. No wrong-control-grammar persistence metric. No alternative rollout conditioned on grammar latent. | Differentiation requires: (a) grammar-conditioned specific hypothesis (not generic regime), (b) persistence metric, (c) falsification vs change-detection distinction. If these three distinctions cannot be demonstrated experimentally, LFD collapses into R-BOCPD variant. |

**Reviewer attack enabled by CPD-001 + CPD-002**:

| Attack ID | Attack | Defense Required |
|---|---|---|
| ATK-023 | "NN-CUSUM (AAAI 2024) already provides a learned CPD with better theoretical guarantees than LFD AUROC +0.034." | LFD vs NN-CUSUM comparison, not just classical CUSUM. Grammar-specific signal required. |
| ATK-024 | "R-BOCPD (2304.00232) already combines BOCPD with RL non-stationary regime detection. LFD is a web-specific re-implementation." | Distinguish grammar-conditioned control hypothesis (LFD) from generic regime change (R-BOCPD). Persistence metric + alternative rollout conditioned on grammar posterior are the only defensible distinguishing factors. |

**Risk added**:

| Risk ID | Risk | Severity |
|---|---|---|
| RISK-01-021 | NN-CUSUM and R-BOCPD pre-empt the LFD novelty at the CPD algorithm level. LFD must demonstrate grammar-specific signal beyond generic change-point detection. | CRITICAL |

---

## 19. Final Statement of This File

```text
01_RELATED_WORK_THREAT_MAP.md is a threat analysis file, not a final related work section.

The strongest direct threats are:
- WebWorld / WMA / WAC: generic web world model, consequence simulation, and action correction are already strong research directions.
- CUWM / ViMo / MobileDreamer / Code2World: GUI/computer-use world models and next-state prediction/lookahead already exist.
- VeriGUI / VAGEN / VSA: action-effect verification and recovery are already explicit GUI-agent directions.
- StressWeb / D-GARA / WorkflowPerturb: robustness perturbation and altered interaction semantics threaten grammar-shift novelty.
- Agent Q / MCTS-style agents: alternative rollout can be attacked as ordinary test-time search.

The novelty candidates that may survive are:
- wrong-control-grammar hypothesis persistence as a measurable failure mode,
- latent separation of regime and control grammar,
- action-effect evidence as hypothesis falsification rather than only verification,
- current-vs-alternative control-grammar rollout,
- grammar-conditioned intent-to-action interface rewrite,
- decision-relevant compute reallocation based on action-switch value,
- reveal-vs-shift aware belief update.

None of these are verified novelty claims yet. They must be defended in Step 02 and Step 10 with:
- explicit metric definitions,
- high-threat baselines,
- no-control-grammar / no-falsification / no-alternative-rollout ablations,
- compute-matched planning comparison,
- failure interpretation rules.

The next required file is:
02_PROBLEM_NOVELTY_FALSIFICATION.md
```
