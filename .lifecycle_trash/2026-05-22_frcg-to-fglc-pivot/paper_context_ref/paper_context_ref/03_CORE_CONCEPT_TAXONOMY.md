---
file_id: STEP-03
title: Core Concept Taxonomy for FRCG-WM Paper Design
version: v1.0
status: taxonomy_contract_not_final_architecture
language: ko
source_file:
  - 03_CORE_CONCEPT_TAXONOMY.md
depends_on:
  - 00_MASTER_REFERENCE.md
  - 01_RELATED_WORK_THREAT_MAP.md
  - 02_PROBLEM_NOVELTY_FALSIFICATION.md
next_files:
  - 04_TEXT_ONLY_SMOKE_TESTBED.md
  - 05_SYNTHETIC_WEB_GUI_ENVIRONMENT.md
  - 06_DATA_SCHEMA_AND_LABELING.md
  - 07_LATENT_ARCHITECTURE_DESIGN.md
  - 08_LOSS_REWARD_TRAINING_OBJECTIVE.md
  - 09_PLANNING_THEORY_ALGORITHM.md
  - 10_EVALUATION_BASELINE_ABLATION.md
purpose:
  - FRCG-WM 논문에서 쓰이는 핵심 개념을 정의·분리·운영화한다.
  - regime, control grammar, state, reveal, shift, falsification, alternative hypothesis가 서로 섞여 novelty-by-renaming으로 무너지는 것을 방지한다.
  - 후속 environment, data schema, architecture, loss, planning, evaluation 파일이 같은 의미 체계로 동작하도록 개념 계약서를 제공한다.
forbidden:
  - 최종 architecture 확정 금지
  - 최종 latent variable 확정 금지
  - 최종 loss/reward 확정 금지
  - 최종 method section 작성 금지
  - taxonomy가 실험적으로 검증되었다고 주장 금지
  - SOURCE_ONLY 또는 CONDITIONAL_SURVIVAL 개념을 final claim으로 승격 금지
---

# 03_CORE_CONCEPT_TAXONOMY.md

## 1. 파일 목적

이 파일은 단순 용어 사전이 아니다.  
이 파일은 `04_TEXT_ONLY_SMOKE_TESTBED.md`부터 `10_EVALUATION_BASELINE_ABLATION.md`까지 같은 개념을 같은 의미로 사용하도록 강제하는 **개념 계약서**다.

FRCG-WM의 가장 큰 위험은 새로운 algorithm을 제시하기 전에 용어가 먼저 무너지는 것이다. 특히 reviewer는 다음과 같이 공격할 가능성이 높다.

- `control grammar`는 그냥 action precondition 아닌가?
- `regime`과 `control grammar`는 같은 말 아닌가?
- `falsification`은 그냥 action-effect verification 아닌가?
- `alternative hypothesis`는 그냥 alternative action search 아닌가?
- `decision-relevant compute`는 그냥 uncertainty-gated planning 아닌가?
- `reveal`과 `shift`는 현실 Web/GUI에서 구분 불가능한 것 아닌가?
- synthetic label 없이는 이 taxonomy를 검증할 수 없는 것 아닌가?

따라서 이 파일의 목적은 멋진 용어를 만드는 것이 아니라, 각 개념에 대해 다음을 강제하는 것이다.

1. 정의 가능한가?
2. 서로 다른 개념과 경계가 있는가?
3. positive/negative example이 있는가?
4. synthetic label 또는 weak real-world proxy가 있는가?
5. 어떤 metric, loss, module, planning component, ablation에 연결되는가?
6. 개념이 너무 추상적이면 폐기하거나 auxiliary로 낮출 수 있는가?
7. reviewer 공격에 대비한 separability test가 있는가?

---

## 2. Claude Code Context Routing

Claude Code는 이 파일을 읽을 때 항상 아래 routing 규칙을 따른다.

| 작업 의도 | 먼저 읽을 섹션 | 추가로 읽을 파일 | 반드시 금지할 가정 |
|---|---|---|---|
| `control grammar` 정의/수정 | §5, §6, §7, §8 | `02`, `06`, `07`, `09`, `10` | grammar를 action precondition 하나로 축소 금지 |
| regime/grammar 분리 | §6, §9, §14, §15 | `05`, `06`, `07`, `10` | regime과 grammar가 자연히 분리된다고 가정 금지 |
| reveal/shift event 설계 | §9, §10, §15 | `05`, `06`, `10` | 모든 DOM 변화를 shift로 취급 금지 |
| falsification score 설계 | §5, §10, §12, §15 | `08`, `09`, `10` | failed-action flag를 falsification으로 취급 금지 |
| action rewrite 설계 | §11, §12, §15 | `07`, `09`, `10` | rewrite를 단순 retry/policy correction으로 취급 금지 |
| data schema 작성 | §7, §9, §10, §11 | `06` | hidden labels를 agent observation에 포함 금지 |
| latent architecture 작성 | §8, §13, §15 | `07` | 4-latent 구조가 이미 최종이라고 가정 금지 |
| evaluation/ablation 작성 | §6, §12, §17, §18 | `10` | success rate만으로 taxonomy 검증 금지 |

---

## 3. 핵심 개념 대헌법

아래 원칙은 이후 모든 파일에서 위반하면 안 된다.

```text
CONTROL GRAMMAR = intent-to-action mapping + action precondition + expected effect schema.
```

```text
REGIME = 현재 UI/환경이 어떤 interaction mode로 작동하는지에 대한 mode-level variable.
CONTROL GRAMMAR = 해당 mode에서 같은 intent를 어떤 executable action 또는 action macro로 번역해야 하는지에 대한 rule-level variable.
```

```text
CURRENT HYPOTHESIS = 현재 posterior mode가 아니라, 직전 action을 실제로 생성·선택할 때 사용된 executed hypothesis h_exec.
```

```text
FALSIFICATION = action이 실패했다는 사실이 아니라, h_exec가 observed action-effect evidence를 설명하지 못하고 alternative hypothesis가 더 잘 설명하는 상태.
```

```text
ALTERNATIVE HYPOTHESIS = alternative action이 아니라, evidence를 더 잘 설명하는 alternative state/regime/control-grammar hypothesis.
```

```text
REVEAL = hidden state의 관측 가능성이 증가하지만 action law는 변하지 않는 사건.
SHIFT = interaction mode 또는 intent-to-action/effect law가 변하는 사건.
```

```text
DECISION-RELEVANT COMPUTE = uncertainty가 높다는 이유만으로 planning하는 것이 아니라, alternative hypothesis가 action choice 또는 expected progress를 바꿀 가능성이 있을 때만 planning compute를 쓰는 원칙.
```

---

## 4. Imported Reference Ledger

| Imported ID | Source File | Type | Meaning | Why It Matters | Priority |
|---|---|---|---|---|---|
| REF-CORE-001 | 00_MASTER_REFERENCE.md | Core | wrong-control-grammar hypothesis persistence | taxonomy 전체의 중심 failure mode | CRITICAL |
| REF-CORE-002 | 00_MASTER_REFERENCE.md | Core | latent regime/control-grammar world model | regime/grammar 분리 가능성 검증 | CRITICAL |
| REF-CORE-003 | 00_MASTER_REFERENCE.md | Core | action-effect evidence based falsification | verification과 falsification 분리 | CRITICAL |
| REF-CORE-004 | 00_MASTER_REFERENCE.md | Core | current-vs-alternative hypothesis rollout | alternative action search와 구분 | CRITICAL |
| REF-CORE-005 | 00_MASTER_REFERENCE.md | Core | intent-to-action rewrite | policy correction/retry와 구분 | HIGH |
| REF-CORE-006 | 00_MASTER_REFERENCE.md | Core | decision-relevant compute reallocation | uncertainty gate와 구분 | HIGH |
| REF-CORE-007 | 00_MASTER_REFERENCE.md | Core | Frozen Base VLM/LLM + reliability module | base agent와 proposed module 경계 | MEDIUM |
| REF-CORE-008 | 00_MASTER_REFERENCE.md | Core | text-only smoke test | concept이 GUI 없이도 operationalizable한지 검증 | HIGH |
| REF-CORE-009 | 00_MASTER_REFERENCE.md | Core | synthetic Web/GUI controlled environment | label/evidence 생성 환경 | HIGH |
| REF-CORE-015 | 00_MASTER_REFERENCE.md | Core | reveal-vs-shift split | event taxonomy 핵심 | CRITICAL |
| REF-CONCEPT-001 | 00_MASTER_REFERENCE.md | Concept | regime | mode와 grammar 분리 | CRITICAL |
| REF-CONCEPT-002 | 00_MASTER_REFERENCE.md | Concept | control grammar | novelty-by-renaming 방지 | CRITICAL |
| REF-CONCEPT-003 | 00_MASTER_REFERENCE.md | Concept | state | state/regime/grammar collapse 방지 | CRITICAL |
| REF-CONCEPT-004 | 00_MASTER_REFERENCE.md | Concept | change-point | event taxonomy 상위 개념 | HIGH |
| REF-CONCEPT-005 | 00_MASTER_REFERENCE.md | Concept | reveal | state belief update 사건 | HIGH |
| REF-CONCEPT-006 | 00_MASTER_REFERENCE.md | Concept | shift | grammar/regime update 사건 | HIGH |
| REF-CONCEPT-007 | 00_MASTER_REFERENCE.md | Concept | current hypothesis | persistence metric 기준 | CRITICAL |
| REF-CONCEPT-008 | 00_MASTER_REFERENCE.md | Concept | alternative hypothesis | top-k action과 혼동 금지 | CRITICAL |
| REF-CONCEPT-009 | 00_MASTER_REFERENCE.md | Concept | falsification evidence | verification evidence와 구분 | CRITICAL |
| REF-CONCEPT-010 | 00_MASTER_REFERENCE.md | Concept | action-interface rewrite | retry/self-correction과 구분 | HIGH |
| REF-CONCEPT-011 | 00_MASTER_REFERENCE.md | Concept | decision-relevant compute | uncertainty-only planning과 구분 | HIGH |
| REF-LATENT-001 | 00_MASTER_REFERENCE.md | Latent | z_state | hidden UI/task state 후보 | HIGH |
| REF-LATENT-002 | 00_MASTER_REFERENCE.md | Latent | z_regime | interaction mode latent 후보 | CRITICAL |
| REF-LATENT-003 | 00_MASTER_REFERENCE.md | Latent | z_control_grammar | 핵심 grammar latent 후보 | CRITICAL |
| REF-LATENT-004 | 00_MASTER_REFERENCE.md | Latent | z_change_point | event transition latent 후보 | HIGH |
| REF-LATENT-005 | 00_MASTER_REFERENCE.md | Latent | z_goal_progress | state/progress 중복 위험 | MEDIUM |
| REF-LATENT-006 | 00_MASTER_REFERENCE.md | Latent | z_action_precondition | grammar 내부 factor와 중복 위험 | HIGH |
| REF-LATENT-007 | 00_MASTER_REFERENCE.md | Latent | z_affordance | observation encoder와 중복 위험 | MEDIUM |
| REF-LATENT-008 | 00_MASTER_REFERENCE.md | Latent | z_blocker | regime/state와 중복 위험 | MEDIUM |
| REF-LATENT-009 | 00_MASTER_REFERENCE.md | Latent | z_uncertainty | planning gate와 연결되나 latent화 위험 | LOW |
| REF-LATENT-010 | 00_MASTER_REFERENCE.md | Latent | z_user_intent | base agent output과 중복 위험 | LOW |
| PAPER-WEBWORLD | 01_RELATED_WORK_THREAT_MAP.md | Threat | large-scale web world model | generic world model claim 위협 | CRITICAL |
| PAPER-WMA | 01_RELATED_WORK_THREAT_MAP.md | Threat | web agents with world models | next-observation WM overlap 위협 | CRITICAL |
| PAPER-WAC | 01_RELATED_WORK_THREAT_MAP.md | Threat | world-model-augmented web agents with action correction | action correction과 rewrite 구분 필요 | CRITICAL |
| PAPER-CUWM | 01_RELATED_WORK_THREAT_MAP.md | Threat | computer-using world model | frozen agent + WM search 위협 | CRITICAL |
| PAPER-VERIGUI | 01_RELATED_WORK_THREAT_MAP.md | Threat | verification-driven GUI agent | action-effect verification/recovery 위협 | CRITICAL |
| PAPER-AGENTRX | 01_RELATED_WORK_THREAT_MAP.md | Threat | agent failure diagnosis | failure diagnosis와 closed-loop planning 구분 | HIGH |
| ATTACK-004 | 01_RELATED_WORK_THREAT_MAP.md | Attack | control grammar는 새 용어일 뿐 | taxonomy에서 반드시 방어 | CRITICAL |
| ATTACK-009 | 01_RELATED_WORK_THREAT_MAP.md | Attack | uncertainty-gated planning과 같다 | decision-relevant compute 정의 필요 | HIGH |
| MCX-001 | 02_PROBLEM_NOVELTY_FALSIFICATION.md | Counterexample | pagination vs infinite scroll | grammar와 visual grounding 분리 | CRITICAL |
| MCX-002 | 02_PROBLEM_NOVELTY_FALSIFICATION.md | Counterexample | modal-blocked direct click | blocker/regime/grammar 경계 | CRITICAL |
| MCX-003 | 02_PROBLEM_NOVELTY_FALSIFICATION.md | Counterexample | form-invalid disabled submit | precondition과 grammar 경계 | CRITICAL |
| MCX-004 | 02_PROBLEM_NOVELTY_FALSIFICATION.md | Counterexample | loading/stale DOM timing | timing failure와 grammar 분리 | HIGH |
| MCX-005 | 02_PROBLEM_NOVELTY_FALSIFICATION.md | Counterexample | responsive menu hidden navigation | reveal/grammar 전환 경계 | HIGH |
| MCX-006 | 02_PROBLEM_NOVELTY_FALSIFICATION.md | Counterexample | hidden filter accordion | reveal과 action macro 구분 | HIGH |
| METRIC-02-001 | 02_PROBLEM_NOVELTY_FALSIFICATION.md | Metric | wrong-control-grammar persistence time | 핵심 metric | CRITICAL |
| METRIC-02-002 | 02_PROBLEM_NOVELTY_FALSIFICATION.md | Metric | failed-action repetition rate | verification baseline과 비교 | HIGH |
| METRIC-02-003 | 02_PROBLEM_NOVELTY_FALSIFICATION.md | Metric | action-interface switch delay | rewrite/grammar adoption 측정 | CRITICAL |
| CLAIM-02-001 | 02_PROBLEM_NOVELTY_FALSIFICATION.md | Claim | distinct failure may survive conditionally | taxonomy는 조건부 생존 기준 준수 | CRITICAL |
| REVISION-02-001 | 02_PROBLEM_NOVELTY_FALSIFICATION.md | Revision | control grammar를 schema로 정의 | 이 파일의 핵심 revision | CRITICAL |
| RISK-02-001 | 02_PROBLEM_NOVELTY_FALSIFICATION.md | Risk | synthetic label dependency | real proxy 필요 | HIGH |

---

## 5. Search Expansion Ledger

이 섹션은 related work 정리가 아니라, taxonomy 설계에 영향을 주는 개념적 anchor를 정리한다. URL/arXiv/OpenReview/DOI는 `01_RELATED_WORK_THREAT_MAP.md`에서 citation-grade로 보강되어야 한다.

| Search ID | Query | Source/Paper/Concept | Key Finding | Concept Affected | Supports Distinction? | Follow-up |
|---|---|---|---|---|---|---|
| SEARCH-03-001 | latent regime model reinforcement learning hidden mode POMDP | Hidden Parameter MDPs / HiP-MDP 계열 | latent parameter/context가 transition dynamics를 바꿀 수 있음 | regime, hidden mode | YES | UI regime으로 한정하고 grammar와 분리 |
| SEARCH-03-002 | RL in latent MDPs online guarantees | latent MDP literature | partial observability와 latent mode가 policy를 좌우 | state, regime | PARTIAL | GUI grammar로 직접 확장 필요 |
| SEARCH-03-003 | change point detection reinforcement learning | nonstationary RL / change-point literature | dynamics/process change를 감지하는 문헌 존재 | change-point, shift | YES | visual diff가 아니라 action law change로 정의 |
| SEARCH-03-004 | reactive changepoint lifelong learning | prediction residual 기반 changepoint detection | expected outcome과 observed outcome 차이로 event 탐지 | falsification evidence | PARTIAL | residual만으로 falsification이라 부르지 말 것 |
| SEARCH-03-005 | action schema planning precondition effect | STRIPS/PDDL action schema | action은 precondition/effect로 모델링 가능 | control grammar, precondition | YES | grammar가 precondition/effect보다 넓은 mapping임을 명시 |
| SEARCH-03-006 | GUI affordance learning action precondition | GUI/mobile agent affordance literature | clickable/scrollable/actionability 판단은 기존 GUI agent 핵심 | affordance, executable action | PARTIAL | affordance는 grammar가 아니라 auxiliary head로 낮춤 |
| SEARCH-03-007 | VeriGUI action-effect verification | VeriGUI | action outcome verification/recovery 수행 | verification, falsification | YES_THREAT | posterior/hypothesis update가 있어야 구분 |
| SEARCH-03-008 | WebWorld web agent world model | WebWorld | long-horizon web simulation/search 방향 | world model, rollout | YES_THREAT | generic web WM claim 금지 |
| SEARCH-03-009 | CUWM computer use world model | CUWM | frozen agent + candidate action next UI prediction | alternative rollout | YES_THREAT | alternative hypothesis ≠ action candidate 명시 |
| SEARCH-03-010 | WMA web agents with world models | WMA | next observation/effect prediction 기반 web agent | action effect schema | YES_THREAT | effect prediction과 grammar falsification 분리 |
| SEARCH-03-011 | WAC action correction | WAC | consequence simulation + action correction | action-interface rewrite | YES_THREAT | rewrite를 same-intent interface remapping으로 제한 |
| SEARCH-03-012 | MiniWoB++ web interaction benchmark | MiniWoB++ | controlled web interaction benchmark precedent | smoke/synthetic bridge | YES | toy risk guardrail 필요 |
| SEARCH-03-013 | WebArena realistic web agents benchmark | WebArena | realistic web task benchmark | real proxy | PARTIAL | grammar label 부재 주의 |
| SEARCH-03-014 | VisualWebArena multimodal benchmark | VisualWebArena | visual grounding needed web tasks | visual grounding vs grammar | YES | same visual/different grammar test 필요 |
| SEARCH-03-015 | OSWorld computer use benchmark | OSWorld | real OS/computer-use tasks | real proxy | PARTIAL | weak labels만 가능 |
| SEARCH-03-016 | value of computation planning | VOC / rational metareasoning literature | compute를 expected value와 cost로 비교 | decision-relevant compute | YES | VOC-inspired로만 사용, exact theory 과장 금지 |
| SEARCH-03-017 | expected value of information planning | VOI/EVSI literature | information/computation gain과 cost 비교 | compute reallocation | PARTIAL | uncertainty 감소가 아니라 decision change 조건으로 둠 |
| SEARCH-03-018 | hypothesis testing planning likelihood ratio | Bayesian/sequential hypothesis testing | evidence likelihood ratio로 가설 비교 | falsification, posterior update | YES | learned likelihood-ratio proxy로 정의 |
| SEARCH-03-019 | instruction to action mapping GUI agent | GUI agent action abstraction literature | NL intent를 executable primitive/action sequence로 변환 | intent, executable action | PARTIAL | intent-to-action mapping을 grammar 내부로 명시 |
| SEARCH-03-020 | stale preconditions UI agent | context alignment / stale state literature | 실행 시점 상태 변화와 stale precondition 중요 | current hypothesis, timing | PARTIAL | loading/stale DOM은 timing event와 grammar precondition 모두로 취급 |
| SEARCH-03-021 | GUI agent hallucination taxonomy | GUI hallucination/failure taxonomy | action/history inconsistency 진단 | failure taxonomy | PARTIAL | reasoning hallucination과 grammar persistence 분리 |
| SEARCH-03-022 | browser agent robustness perturbation | web robustness benchmark family | layout/DOM/timing perturbation 평가 | reveal/shift, robustness | YES_THREAT | perturbation vs grammar shift factorial split 필요 |

---

## 6. Core Concept Definition Table

| Concept ID | Concept | Working Definition | Formal-ish Definition | Positive Example | Negative Example | Must Not Be Confused With |
|---|---|---|---|---|---|---|
| CONCEPT-03-001 | state | 현재 또는 숨은 UI/태스크 변수들의 값 | `s_t = {DOM-relevant variables, task progress variables, UI flags}`. intent-to-action law는 포함하지 않음 | `cart_count=0`, `modal_active=true`, `filter_panel_open=false` | pagination 방식 자체 | regime, control grammar |
| CONCEPT-03-002 | hidden UI/task state | 관측되지 않았거나 부분적으로만 관측되는 state subset | `s_hidden ⊂ s_t`, observation `o_t`로 완전히 식별되지 않는 변수 | size가 선택되지 않았지만 버튼 disabled만 보임 | 사용자의 semantic goal | user intent, regime |
| CONCEPT-03-003 | regime | 현재 UI/환경의 interaction mode | `r_t ∈ R`; 어떤 종류의 interaction context인지 나타냄 | `modal_blocked`, `loading`, `responsive_menu`, `form_invalid` | “size를 먼저 선택해야 한다”는 세부 규칙만 | control grammar, blocker |
| CONCEPT-03-004 | control grammar | intent를 executable action/macro로 번역하는 규칙 묶음 | `g_t = {intent→action/macro mapping, preconditions, expected effect schema}` | `add_to_cart → select_size → click_add`; `next_results → scroll_container` | `button.disabled=true`라는 단일 상태값 | regime, precondition, action label |
| CONCEPT-03-005 | action precondition | 특정 action/macro가 효과를 내기 위한 조건 | `pre(a|s,r,g) ∈ {true,false}` 또는 soft score | `click_submit`은 `required_fields_filled=true`일 때 유효 | submit intent 전체 수행법 | control grammar |
| CONCEPT-03-006 | action effect schema | action/macro 실행 후 기대되는 상태 변화 패턴 | `E[e_{t+1}|s_t,a_t,g_t]`; effect_type, DOM diff, progress delta | `click_next → result_cards replaced/appended` | reward scalar 하나 | progress, reward |
| CONCEPT-03-007 | intent | 사용자 instruction 또는 base agent가 현재 달성하려는 고수준 목적 | `i_t = semantic subgoal before grounding into actions` | `next_results`, `add_to_cart`, `open_filter` | `click(x,y)` 좌표 | executable action |
| CONCEPT-03-008 | executable action | 환경 API가 실제 실행할 수 있는 primitive 또는 macro | `a_t ∈ A_env` 또는 macro sequence | `click(node_id)`, `type(text)`, `scroll(container)`, `wait` | “상품을 장바구니에 넣기” | intent |
| CONCEPT-03-009 | current hypothesis | 직전 action/macro 생성에 실제 사용된 state/regime/grammar 가설 | `h_exec_t=(ŝ_t,r̂_t,ĝ_t)` used to choose `a_t`; posterior mode와 다를 수 있음 | 이전 step에서 `direct_click` grammar로 add button을 누름 | evidence 후 바뀐 현재 posterior | posterior mode, belief state |
| CONCEPT-03-010 | alternative hypothesis | 현재 evidence를 더 잘 설명할 수 있는 비현재 state/regime/grammar 후보 | `h_alt^k ∈ TopK p(h|history,evidence)`, `h_alt ≠ h_exec` | `form_invalid`, `modal_blocked` grammar 후보 | 후보 action `click A` vs `click B` | alternative action search |
| CONCEPT-03-011 | action-effect evidence | 실행 전후 차이와 기대 효과 불일치를 나타내는 관측 근거 | `e_t={pre_state, action, post_state, DOM diff, visual diff, event, progress_delta}` | click 후 cart_count 변화 없음, warning 표시 | 모델 confidence 낮음 | uncertainty, generic failure |
| CONCEPT-03-012 | falsification | h_exec가 evidence를 잘 설명하지 못하고 alternative가 더 잘 설명하는 상태 | `F_t=max_alt log p(e_t|h_alt)-log p(e_t|h_exec)` | direct click 기대와 달리 disabled warning이 뜨고 form_invalid가 더 잘 설명 | action failed=true만 기록 | verification |
| CONCEPT-03-013 | reveal | 기존 숨은 state가 관측 가능해지지만 action law는 그대로인 사건 | observation support increases while `r,g` unchanged | accordion을 열어 숨은 필터 옵션 표시 | size 선택 전후 submit grammar 변경 | shift, state transition |
| CONCEPT-03-014 | shift | interaction mode 또는 intent-to-action/effect law가 바뀌는 사건 | event where `r_t` or `g_t` changes | pagination → infinite_scroll grammar | 스크롤로 아래 상품 추가 표시 | reveal |
| CONCEPT-03-015 | change-point | state/regime/grammar/evidence process가 이전과 다른 구간으로 넘어가는 시점 | `c_t ∈ {none, reveal, state_transition, regime_shift, grammar_shift, failed_action, delayed_effect}` | modal이 활성화되어 click routing 변경 | 텍스트 한 글자 바뀜 | visual diff |
| CONCEPT-03-016 | wrong-control-grammar hypothesis persistence | 반증 evidence 이후에도 틀린 grammar로 action을 계속 생성하는 현상 | `Σ I[g_exec≠g_true ∧ evidence_falsifies(g_exec) ∧ no_switch]` | size warning 후에도 add button만 반복 클릭 | 한 번 실패 후 바로 size 선택 | failed-action count |
| CONCEPT-03-017 | action-interface rewrite | 같은 intent를 다른 grammar에 맞는 executable action/macro로 재작성 | `Rewrite(i_t,a_base,g*) → a_macro` | `click_add → select_size(M) → click_add` | 같은 버튼 재클릭 | policy correction, retry |
| CONCEPT-03-018 | decision-relevant compute | 계산이 action/value 결정을 바꿀 가능성이 있을 때 쓰는 planning compute | plan iff `ΔV - C_compute > τ` and action_switch_prob high | form_invalid 후보가 action을 select_size로 바꿀 때 rollout | uncertainty 높으니 무조건 rollout | uncertainty gate |
| CONCEPT-03-019 | short-horizon rollout | 1~3 step 내 action effect/progress/failure를 hypothesis 조건부로 예측 | `τ̂_{t:t+H}~WM(h,a)`, `H∈{1,3}` | close_modal 후 checkout 가능 여부 2-step 예측 | 30-step full web simulation | generic simulator |
| CONCEPT-03-020 | compute reallocation | planning budget을 모든 step/가설에 균등 배분하지 않고 반증/decision relevance가 큰 곳으로 이동 | allocate budget `B_t` to hypotheses/actions with expected decision impact | failed click 후 alt grammar에만 top-k rollout 사용 | always-plan으로 모든 후보 rollout | always-plan, MCTS |
| CONCEPT-03-021 | blocker | intended action을 막는 UI/state 요소 | `b_t ∈ {modal, overlay, permission, loading, disabled}` | cookie modal이 checkout click을 intercept | pagination mode 자체 | regime, state |
| CONCEPT-03-022 | effect mismatch | expected effect와 observed effect의 차이 | `m_t = d(e_expected, e_observed)` | click_add expected cart++, observed no cart change | OCR noise alone | falsification, noise |
| CONCEPT-03-023 | valid hypothesis switch | wrong current에서 better alternative로 바뀌고 progress가 뒤따르는 switch | switch if `F_t>τ`, action changes, progress improves within window | `direct_click → fill_required_then_submit` | random switch with no progress | reward hacking |
| CONCEPT-03-024 | invalid hypothesis switch | evidence/value 개선 없이 불필요하게 hypothesis를 바꿈 | switch without likelihood/progress gain | modal 아닌데 close_modal action으로 전환 | uncertain하지만 correct switch | exploration |

---

## 7. Boundary Case Decision Table

| Boundary ID | Ambiguous Case | Possible Classification A | Possible Classification B | Decision Rule | Example | Risk |
|---|---|---|---|---|---|---|
| BOUNDARY-03-001 | button disabled | state: `enabled=false` | control grammar: prerequisite-fill-before-submit | 단일 DOM property는 state; 해결 macro는 grammar | disabled submit button after empty field | state와 grammar 혼동 |
| BOUNDARY-03-002 | modal overlay | state/blocker: `overlay_active=true` | regime: `modal_blocked` | overlay 값은 state/blocker; 모든 target click을 intercept하는 mode는 regime | cookie modal covers checkout | blocker/regime collapse |
| BOUNDARY-03-003 | infinite scroll | regime: result navigation mode | grammar: `next_results→scroll_container` | UI 결과 표시 방식은 regime; intent translation은 grammar | results append on scroll | regime/grammar collapse |
| BOUNDARY-03-004 | required form field | precondition | grammar: `fill_required_then_submit` | 조건 하나는 precondition; 조건을 만족시키는 sequence는 grammar | size required before add | precondition=grammar 착각 |
| BOUNDARY-03-005 | loading/stale DOM | state/regime: loading/stale | timing failure | wait-stabilize macro가 필요하면 grammar component; 단순 지연이면 timing event | spinner active, element detached | latency vs grammar 혼동 |
| BOUNDARY-03-006 | hamburger menu | reveal | control grammar: open-menu-then-click | 메뉴 열림은 reveal; navigation intent 실행법은 grammar | small viewport settings menu | reveal을 shift로 오분류 |
| BOUNDARY-03-007 | accordion open | reveal/state transition | not grammar shift by default | hidden option 노출만이면 reveal | filter accordion expands | 모든 DOM 변화가 shift로 과장 |
| BOUNDARY-03-008 | click 후 no-effect | failed action evidence | falsification evidence | no-effect는 evidence; h_exec의 expected effect와 충돌할 때 falsification | cart_count unchanged | 실패 감지와 반증 혼동 |
| BOUNDARY-03-009 | action 변경 | policy correction | action-interface rewrite | 같은 intent의 grammar-conditioned macro로 바뀌면 rewrite | click_add→select_size→click_add | WAC/VeriGUI와 차이 흐림 |
| BOUNDARY-03-010 | top-k alternative | action search | hypothesis comparison | action 후보 탐색이면 search, evidence 설명 가설 비교면 hypothesis comparison | top-k grammar posterior | tree search 공격 |
| BOUNDARY-03-011 | high uncertainty | uncertainty signal | falsification only if evidence contradicts h_exec | falsification은 evidence likelihood ratio 필요 | ambiguous UI text | confidence threshold와 혼동 |
| BOUNDARY-03-012 | recovery action | retry | alternative grammar adoption | 같은 mapping 반복이면 retry; 다른 grammar로 intent 실행법이 바뀌면 adoption | close modal then checkout | recovery/switch metric 중복 |
| BOUNDARY-03-013 | search result replaced | effect schema mismatch | state transition | replacement law는 effect schema; 실제 카드 값 변화는 state | filter submit replaces list | state diff와 effect law 혼동 |
| BOUNDARY-03-014 | nested scroll target | action parameter error | control grammar target rule | page vs inner container target mapping이 intent-specific이면 grammar component | scroll inner panel not page | grounding 오류로 collapse |
| BOUNDARY-03-015 | confirmation dialog | state transition | grammar shift | dialog 출현은 state; destructive action macro law는 grammar | delete→confirm required | event/grammar 혼동 |
| BOUNDARY-03-016 | autocomplete required | precondition/effect schema | text input action | typed text 표시와 form acceptance는 다른 effect schema | city input requires suggestion select | typing 성공을 progress로 오판 |
| BOUNDARY-03-017 | delayed effect | delayed event | failed action | effect가 window 안에 도착하면 delayed; 영구 no-effect이면 failure | spinner then loaded results | falsification false positive |
| BOUNDARY-03-018 | overlay intercept | blocker | visual grounding failure | target bbox가 맞고 event target이 overlay면 blocker; target이 틀리면 grounding failure | click target covered by modal | visual failure로 collapse |

---

## 8. Concept Separation Matrix

| Pair ID | Concept A | Concept B | Why Similar | Key Difference | Separability Test | Risk If Confused |
|---|---|---|---|---|---|---|
| PAIR-03-001 | state | regime | 둘 다 UI 상황 설명 | state는 변수값, regime은 interaction mode | same state flags under different click routing | state encoder가 regime 흡수 |
| PAIR-03-002 | regime | control grammar | 둘 다 UI 조작 방식 설명 | regime은 mode, grammar는 intent→macro law | same regime/different grammar split | core novelty collapse |
| PAIR-03-003 | control grammar | action precondition | precondition이 grammar 내부 | precondition은 조건, grammar는 조건 해결 macro까지 포함 | disabled button vs fill-required macro | 말장난 공격 |
| PAIR-03-004 | control grammar | action effect schema | effect schema가 grammar 일부 | effect schema는 outcome law, grammar는 mapping+precondition+effect | pagination replaced vs appended | loss 연결이 흐려짐 |
| PAIR-03-005 | change-point | reveal | 둘 다 관측 변화 | change-point는 상위 event, reveal은 observability 변화 subtype | accordion expand | change detector 과검출 |
| PAIR-03-006 | change-point | shift | 둘 다 transition | shift는 regime/grammar change subtype | pagination to infinite scroll | event taxonomy 과확장 |
| PAIR-03-007 | reveal | shift | 둘 다 화면 변화 동반 가능 | reveal은 law 불변, shift는 action law 변경 | hidden filter reveal vs precondition change | OOD split 실패 |
| PAIR-03-008 | verification | falsification | 둘 다 action 결과 확인 | verification은 success/failure 확인, falsification은 hypothesis rejection | no cart change→form_invalid posterior | VeriGUI 차이 상실 |
| PAIR-03-009 | alternative action | alternative hypothesis | 둘 다 대안 | action은 실행 후보, hypothesis는 evidence 설명 모델 | click A/B vs modal/form_invalid grammar | tree search로 collapse |
| PAIR-03-010 | policy correction | action-interface rewrite | 둘 다 action 변경 | rewrite는 같은 intent를 새 grammar로 재번역 | click_add→select_size→click_add | WAC와 구분 약화 |
| PAIR-03-011 | uncertainty gate | decision-relevant compute | 둘 다 planning 여부 결정 | uncertainty는 epistemic signal, decision relevance는 action/value change 기준 | high uncertainty same action vs low uncertainty contradiction | compute novelty 약화 |
| PAIR-03-012 | planning/search | hypothesis rollout | 둘 다 미래 예측 | search는 action tree, hypothesis rollout은 grammar-conditioned law 비교 | current grammar vs alt grammar rollout | generic MCTS 공격 |
| PAIR-03-013 | blocker | regime | modal/permission이 mode처럼 보임 | blocker는 원인 요소, regime은 interaction mode | same blocker with different intent-specific grammar | blocker를 primary latent로 오해 |
| PAIR-03-014 | valid switch | exploration | 둘 다 action/hypothesis 변경 | valid switch는 evidence+progress-linked | random switch vs recovery switch | switch reward hacking |

---

## 9. Concept-to-Data/Metric/Loss/Module Map

| Concept ID | Observable Evidence | Synthetic Label | Weak Real-World Proxy | Connected Metric | Connected Loss | Connected Module |
|---|---|---|---|---|---|---|
| CONCEPT-03-001 | DOM/state flags, task variables | state label, progress variables | DOM/accessibility diff | normalized return, progress delta | `L_progress`, optional state loss | observation encoder, state head |
| CONCEPT-03-002 | warning/disabled controls revealing hidden variables | hidden_state label | warning texts, disabled controls | hidden-state inference accuracy | state belief loss | history encoder |
| CONCEPT-03-003 | mode-specific event patterns | `true_regime` | modal/loading/responsive heuristics | wrong regime persistence | `L_regime` | regime head |
| CONCEPT-03-004 | intent/action/effect triplets | `true_control_grammar` | weak grammar tags from traces | grammar persistence, switch delay | `L_control_grammar`, `L_mapping` | grammar head, rewrite module |
| CONCEPT-03-005 | enabled/visible/required/covered flags | precondition table | DOM form validation | invalid precondition rate | `L_precondition_aux` | precondition head |
| CONCEPT-03-006 | effect type, DOM/visual diff | effect_schema label | state diff summary | rollout fidelity | `L_action_effect` | effect predictor, rollout model |
| CONCEPT-03-007 | base subgoal text | intent label | base LLM plan step | intent consistency | optional `L_intent_aux` | base interface |
| CONCEPT-03-008 | browser action trace | action/macro label | browser logs | action validity rate | `L_mapping` | final action selector |
| CONCEPT-03-009 | h_exec trace | executed hypothesis label | internal model log | persistence time | indirect via `L_falsification` | hypothesis scorer |
| CONCEPT-03-010 | posterior alternatives | alternative hypothesis label | top-k inferred modes | adoption rate | `L_current_alt_ranking` | alternative proposer |
| CONCEPT-03-011 | pre/post diff | evidence label | DOM/visual/action logs | falsification P/R | `L_action_effect` | evidence encoder |
| CONCEPT-03-012 | likelihood ratio/residual | current_wrong label | unexpected no-effect proxy | falsification P/R, calibration | `L_falsification` | falsification scorer |
| CONCEPT-03-013 | newly visible nodes | reveal label | newly visible nodes | reveal-vs-shift accuracy | `L_reveal_shift` | event head |
| CONCEPT-03-014 | grammar/regime transition | shift label | action law changed proxy | shift detection F1 | `L_change_point`, `L_reveal_shift` | change-point detector |
| CONCEPT-03-015 | event boundary | change-point label | diff/time boundary | change-point F1 | `L_change_point` | change-point detector |
| CONCEPT-03-016 | wrong h_exec kept over steps | true/executed grammar trace | repeated invalid mapping proxy | persistence time | evaluation metric only | evaluation harness |
| CONCEPT-03-017 | macro before/after rewrite | rewrite target label | successful recovery macro | rewrite accuracy, switch delay | `L_intent_action_mapping` | rewrite module |
| CONCEPT-03-018 | VOC/action switch estimates | compute trigger target optional | planning-call logs | progress per compute | planner objective | decision gate |
| CONCEPT-03-019 | predicted short traces | rollout effect/progress target | simulated/actual effect comparison | rollout fidelity | `L_action_effect`, `L_progress` | short rollout model |
| CONCEPT-03-020 | budget allocation trace | planning budget labels optional | rollout step logs | compute-matched return | compute regularization | planner/controller |
| CONCEPT-03-021 | overlay/loading/permission flags | blocker label | covered_by, modal role | blocker recovery success | `L_blocker_aux` | blocker head |
| CONCEPT-03-022 | expected/observed mismatch | mismatch/effect label | DOM diff residual | effect mismatch error | `L_action_effect`, `L_falsification` | evidence scorer |
| CONCEPT-03-023 | switch+progress trace | valid_switch label | recovery after switch | valid switch rate | `L_recovery_ranking` | rewrite/gate |
| CONCEPT-03-024 | switch without progress | invalid_switch label | oscillating action logs | invalid switch rate | switch penalty target | reward/gate monitor |

---

## 10. Latent Candidate Seed Table

이번 파일에서는 latent를 최종 확정하지 않는다. 이 표는 `07_LATENT_ARCHITECTURE_DESIGN.md`로 넘길 후보군이다.

| Latent Candidate ID | Candidate | Related Concept | Why Candidate | Possible Overlap | Identifiability Risk | Recommended Status |
|---|---|---|---|---|---|---|
| LATENT-CAND-03-001 | `z_state` | state, hidden UI/task state | partial observability를 belief로 처리 | `z_goal_progress`, `z_blocker` | 모든 정보를 흡수할 위험 | PRIMARY_CANDIDATE |
| LATENT-CAND-03-002 | `z_regime` | regime | interaction mode 변화 분리 | `z_control_grammar`, `z_blocker` | grammar와 collapse | PRIMARY_CANDIDATE |
| LATENT-CAND-03-003 | `z_control_grammar` | control grammar | 핵심 claim의 실행 law 표현 | `z_regime`, `z_action_precondition` | label artifact/용어 재포장 | PRIMARY_CANDIDATE |
| LATENT-CAND-03-004 | `z_change_point` | change-point, reveal, shift | event transition 감지 | reveal_shift head | 희소 이벤트 불안정 | PRIMARY_CANDIDATE |
| LATENT-CAND-03-005 | `z_goal_progress` | progress/state | value/progress prediction 보조 | `z_state`, progress head | state와 중복 | AUXILIARY_HEAD_ONLY |
| LATENT-CAND-03-006 | `z_action_precondition` | action precondition | precondition 오류 분석 | `z_control_grammar` | grammar를 쪼개 novelty 흐림 | AUXILIARY_HEAD_ONLY |
| LATENT-CAND-03-007 | `z_affordance` | affordance/executable action | clickable/scrollable 판단 보조 | observation encoder | 기존 GUI affordance와 겹침 | AUXILIARY_HEAD_ONLY |
| LATENT-CAND-03-008 | `z_blocker` | modal/blocker/loading | modal/permission/loading recovery 보조 | `z_regime`, `z_state` | blocker를 regime으로 착각 | AUXILIARY_HEAD_ONLY |
| LATENT-CAND-03-009 | `z_uncertainty` | uncertainty/compute gate | calibration과 planning trigger 보조 | falsification score | uncertainty gate로 claim 축소 | AUXILIARY_HEAD_ONLY |
| LATENT-CAND-03-010 | `z_user_intent` | intent | base intent 불안정 시 보조 | base LLM output | base/proposed 경계 붕괴 | REJECT_AS_PRIMARY |
| LATENT-CAND-03-011 | `z_effect_schema` | action effect schema | effect prediction을 명시적으로 분리 | `z_control_grammar` | grammar latent와 중복 | AUXILIARY_HEAD_ONLY |
| LATENT-CAND-03-012 | `z_failure_mode` | failed action, blocker, timing | failure diagnosis 분석 보조 | AgentRx-style diagnosis | contribution 흐림 | APPENDIX_ONLY |
| LATENT-CAND-03-013 | `z_temporal_stability` | change-point, delayed effect | persistence/shift risk 예측 | uncertainty/change point | 과도한 설계 | UNKNOWN |
| LATENT-CAND-03-014 | `z_task_phase` | state/progress | long-horizon task phase tracking | `z_state`, `z_goal_progress` | state와 중복 | AUXILIARY_HEAD_ONLY |

---

## 11. Reveal-vs-Shift Taxonomy

| Event Type | Definition | Updates Which Belief? | Example | Non-example | Label Rule |
|---|---|---|---|---|---|
| no-change | 관측/상태/action law 모두 유의미한 변화 없음 | belief 유지 | click no-op but no expected progress event | new panel visible | diff와 event label 모두 낮음 |
| reveal | 숨은 state가 보이지만 action law는 그대로 | `z_state` belief | accordion 열림으로 필터 옵션 표시 | required field 때문에 submit law 변경 | new visible nodes, same `r,g` |
| state transition | state variable 값이 실제로 바뀜 | `z_state` | cart_count 0→1 | pagination law 변경 | state diff with same `r,g` |
| regime shift | interaction mode 변경 | `z_regime` | normal→modal_blocked, normal→loading | 상품 카드 하나 추가 | mode label changes |
| control grammar shift | intent→action/precondition/effect law 변경 | `z_control_grammar` | next_results가 click_next에서 scroll_container로 바뀜 | 단순 버튼 위치 변경 | same/similar intent, different required macro/effect schema |
| failed action | action이 expected effect를 만들지 못함 | evidence/failure head | disabled button click no progress | success action with small visual diff | expected effect absent and failure evidence exists |
| noisy observation | 관측만 흔들리고 state/law는 유지 | observation confidence | OCR error, visual noise | modal appears | visual/text anomaly not supported by DOM/effect |
| delayed effect | effect가 즉시 나오지 않고 지연됨 | timing belief/state | spinner 후 DOM update | permanent no-effect | effect arrives within delay window |
| blocker removed | blocker state가 해소됨 | `z_state`, optional blocker head | close_modal 후 target clickable | click target itself | blocker flag changes, grammar may stay same |
| validation state changed | form validation condition이 바뀜 | state/precondition head | required field filled, submit enabled | visual style only | precondition status changes |

---

## 12. Hypothesis and Falsification Taxonomy

| Item | Definition | Evidence Type | Mathematical Proxy | Failure Risk | Used By |
|---|---|---|---|---|---|
| current hypothesis | 직전 action 선택에 사용된 `h_exec=(s,r,g)` | action-generation log, previous posterior | stored `h_exec_t` | posterior mode와 다를 수 있음 | persistence metric, falsification scorer |
| alternative hypothesis | evidence를 더 잘 설명하는 비현재 `h_alt` | posterior candidates, likelihood ranking | `TopK p(h|history,evidence)` | random action 후보와 혼동 | alternative proposer, rollout |
| evidence likelihood | 가설 `h`가 evidence `e_t`를 설명할 확률 | pre/post diff, expected effect | `log p(e_t|h,a)` | model miscalibration | falsification score |
| falsification score | current 대비 alternative evidence likelihood 우위 | expected vs observed contradiction | `max_alt logp(e|alt)-logp(e|current)` | 단순 uncertainty로 축소 | decision gate |
| likelihood ratio | 두 가설의 evidence 설명력 비율 | same evidence under current/alt | `Λ=p(e|alt)/p(e|current)` | numerical instability | hypothesis testing proxy |
| posterior update | evidence 후 belief가 h_alt 쪽으로 이동 | posterior before/after | `p(h|history,evidence)` | label leakage | latent posterior |
| hypothesis switch | h_exec가 다음 step에서 다른 grammar/regime으로 바뀜 | selector trace | `g_exec_t != g_exec_{t-1}` | invalid switch와 구분 필요 | switch delay metric |
| invalid switch | progress/evidence 개선 없이 가설만 바꿈 | switch trace + no progress | switch and `Δprogress≤0` | reward hacking | reward guardrail |
| valid switch | evidence를 더 잘 설명하고 이후 progress를 회복하는 switch | switch + recovery + likelihood improvement | switch and `Δprogress>0` within window | post-hoc correlation | reward/recovery metric |
| evidence-to-update delay | 반증 evidence 이후 posterior/action이 바뀔 때까지 지연 | event log and h_exec trace | min Δt until switch after `F_t>τ` | real label 어려움 | persistence/recovery analysis |

---

## 13. Action Interface Taxonomy

| Item | Definition | Example | Connected Failure | Connected Recovery | Risk |
|---|---|---|---|---|---|
| intent | 고수준 목적 | next_results | wrong grammar persistence | grammar-conditioned rewrite | intent extraction 오류와 혼동 |
| base action | base agent가 제안한 primitive/macro | click(add_button) | invalid mapping | rewrite 또는 reject | base quality 의존 |
| executable action | 환경이 실행 가능한 primitive | click(node), type(text), scroll(container) | execution failure | valid primitive sequence | semantic intent와 혼동 |
| action macro | 여러 primitive로 구성된 실행 sequence | select_size→click_add | missing prerequisite | macro rewrite | macro 길이 폭증 |
| precondition | action/macro 유효 조건 | required_field_filled | disabled/no-effect | fill prerequisite | grammar와 중복 |
| blocker | target action을 막는 UI/state 요소 | modal overlay, permission prompt | intercepted click | remove blocker | regime과 중복 |
| effect schema | action 후 기대되는 변화 패턴 | cart_count++, cards appended | unexpected no-effect | choose alternative grammar | next-state prediction과 혼동 |
| rewritten action | grammar에 맞게 재작성된 action/macro | click_add→select_size→click_add | wrong mapping | recover progress | policy correction과 혼동 |
| recovery action | failure evidence 후 progress를 회복시키는 action | close_modal, wait, fill_required | failure loop | valid switch/retry | retry와 adoption 구분 |
| repeated invalid mapping | 동일 intent를 계속 같은 틀린 mapping으로 실행 | click disabled add repeatedly | persistence | grammar switch | 단순 반복 action과 혼동 |

---

## 14. Operational Label Rules

후속 `06_DATA_SCHEMA_AND_LABELING.md`에서 반드시 이 규칙을 반영해야 한다.

| Label Rule ID | Label | Positive Condition | Negative Condition | Ambiguous Handling |
|---|---|---|---|---|
| LABELRULE-03-001 | `true_regime` | UI interaction mode가 modal/loading/responsive/form_invalid 등으로 결정됨 | 단순 state value 변화 | ambiguous regime이면 `mixed_or_unknown` 허용 |
| LABELRULE-03-002 | `true_control_grammar` | 같은 intent에 대해 required macro/precondition/effect law가 특정됨 | 단일 actionability flag만 있음 | grammar는 mapping+precondition+effect 셋이 모두 있어야 core label |
| LABELRULE-03-003 | `true_reveal` | hidden state가 관측 가능해지고 `r,g`는 유지 | action law가 변경 | reveal/shift 동시 발생 시 compound event로 저장 |
| LABELRULE-03-004 | `true_shift` | regime 또는 grammar가 변경 | DOM만 변경되고 law 유지 | state transition과 구분 |
| LABELRULE-03-005 | `h_exec` | 직전 action selector가 실제 사용한 hypothesis | current posterior after evidence | selector trace에서 저장 |
| LABELRULE-03-006 | `falsifying_evidence` | expected effect under h_exec와 observed effect가 충돌하고 alt가 더 잘 설명 | 단순 no-effect without expected effect | delayed/noisy/no-change class 먼저 배제 |
| LABELRULE-03-007 | `valid_switch` | falsification 이후 selected hypothesis/action이 바뀌고 progress 회복 | switch only, no progress | recovery window 내 progress 필요 |
| LABELRULE-03-008 | `invalid_switch` | likelihood/progress 개선 없이 switch | high-evidence valid exploration | threshold-sensitive로 audit |
| LABELRULE-03-009 | `repeated_invalid_mapping` | same intent가 same wrong grammar/macro로 반복 | same action repeated under changed correct grammar | intent normalization 필요 |
| LABELRULE-03-010 | `wrong_control_grammar_persistence` | falsifying evidence 후 `g_exec != g_true` 유지 | initial unknown before evidence | evidence timestamp 이후부터 계산 |

---

## 15. Taxonomy Stress Test Ledger

| Stress ID | Attack | Why Dangerous | Concept Affected | Required Guardrail | Later Step |
|---|---|---|---|---|---|
| STRESS-03-001 | taxonomy가 너무 많은 용어를 만든다 | 복잡성이 method contribution을 흐린다 | 전체 taxonomy | core/supporting/auxiliary status 분리 | 07,08 |
| STRESS-03-002 | control grammar는 precondition/effect schema로 충분하다 | 핵심 용어 재포장 | control grammar | intent mapping까지 포함 | 03,06 |
| STRESS-03-003 | regime과 grammar 분리가 label artifact다 | latent separation claim 붕괴 | regime/control grammar | same regime/different grammar split | 05,06,10 |
| STRESS-03-004 | reveal과 shift는 현실에서 애매하다 | event label 신뢰성 하락 | reveal/shift | label rule + ambiguous class | 06 |
| STRESS-03-005 | falsification은 likelihood 낮음일 뿐이다 | verification과 차별성 약화 | falsification | alternative likelihood ratio + posterior update | 09 |
| STRESS-03-006 | current hypothesis는 posterior mode일 뿐이다 | persistence metric 불안정 | current hypothesis | h_exec trace 저장 | 06,09 |
| STRESS-03-007 | alternative hypothesis는 top-k action이다 | tree search로 collapse | alternative hypothesis | hypothesis/action index 분리 | 09,10 |
| STRESS-03-008 | decision-relevant compute는 heuristic이다 | theory claim 과장 | decision compute | VOC-inspired로 낮추고 compute-matched baseline | 09,10 |
| STRESS-03-009 | persistence metric은 synthetic에 과적합된다 | real benchmark 전이 약화 | persistence | weak proxy + qualitative trace | 10 |
| STRESS-03-010 | WebArena/OSWorld에서 taxonomy 적용 어렵다 | 외부 타당성 약화 | all concepts | auxiliary validation은 weak label만 사용 | 10 |
| STRESS-03-011 | concept이 많아 architecture가 복잡해진다 | over-engineering 공격 | latent candidates | 4 primary + auxiliary heads | 07 |
| STRESS-03-012 | latent identifiability가 약하다 | regime/grammar 분리 실패 | z_regime/z_grammar | probe/ablation/controlled split | 07,10 |
| STRESS-03-013 | human grammar taxonomy가 임의적이다 | label construction 신뢰성 약화 | control grammar | formal label rule과 consistency audit | 06 |
| STRESS-03-014 | evidence가 noisy하면 taxonomy가 무너진다 | falsification false positive | evidence | noise/no-op/delayed class 분리 | 06,09 |
| STRESS-03-015 | DOM/screenshot/log가 충돌하면 무엇을 믿는가 | multi-modal conflict | state/evidence | source priority rule | 06 |
| STRESS-03-016 | button disabled는 state로 충분하다 | grammar 필요성 약화 | precondition/grammar | disabled 해결 macro law 분리 | 04,05 |
| STRESS-03-017 | recovery delay와 switch delay가 중복된다 | metric 독립성 공격 | metrics | correlation/mediation 분석 | 10 |
| STRESS-03-018 | action-interface rewrite는 WAC action correction이다 | method novelty 약화 | rewrite | same-intent remapping criterion | 09,10 |
| STRESS-03-019 | VeriGUI가 failure loop를 이미 줄였다 | verification overlap | falsification/recovery | verification-only baseline | 10 |
| STRESS-03-020 | WebWorld/CUWM이 rollout을 이미 한다 | world model overlap | short rollout | grammar-hypothesis-indexed rollout | 09,10 |
| STRESS-03-021 | state absorbs all latent structure | factorization 불필요 | state/regime/grammar | collapsed latent baseline | 07,10 |
| STRESS-03-022 | grammar label leaks through UI text | synthetic shortcut | control grammar | paraphrase/decoy/anti-leakage audit | 05,06 |
| STRESS-03-023 | delayed effect misclassified as failure | false falsification | evidence/falsification | delay window label | 06,09 |
| STRESS-03-024 | current hypothesis not logged | core metric 불가능 | current hypothesis | h_exec required field | 06 |

---

## 16. Concept Decision Table

| Decision ID | Concept | Decision | Reason | Required Later Validation | Used By |
|---|---|---|---|---|---|
| DECISION-03-001 | state | CORE_CONCEPT | reveal/shift와 world model의 기본 축 | state labels/probes | 04,05,06,07 |
| DECISION-03-002 | hidden UI/task state | SUPPORTING_CONCEPT | state belief 설명에 필요 | hidden label feasibility | 06,07 |
| DECISION-03-003 | regime | CORE_CONCEPT | interaction mode 분리 | same grammar across regimes / same regime different grammar tests | 05,07,10 |
| DECISION-03-004 | control grammar | CORE_CONCEPT | 핵심 failure와 rewrite의 중심 | grammar label, no-grammar ablation | 06,07,10 |
| DECISION-03-005 | action precondition | SUPPORTING_CONCEPT | grammar 내부 요소 | precondition head utility | 06,08 |
| DECISION-03-006 | action effect schema | SUPPORTING_CONCEPT | falsification likelihood 입력 | effect prediction fidelity | 06,08,09 |
| DECISION-03-007 | intent | SUPPORTING_CONCEPT | base agent와 interface에 필요 | intent extraction stability | 07 |
| DECISION-03-008 | executable action | CORE_CONCEPT | rewrite가 실제 실행되는지 검증 | macro execution logs | 05,06 |
| DECISION-03-009 | current hypothesis | CORE_CONCEPT | persistence metric 기준 | h_exec logging | 06,09,10 |
| DECISION-03-010 | alternative hypothesis | CORE_CONCEPT | alternative rollout 대상 | top-k hypothesis quality | 09,10 |
| DECISION-03-011 | action-effect evidence | CORE_CONCEPT | falsification/verification 분리 | evidence reliability | 06,09 |
| DECISION-03-012 | falsification | CORE_CONCEPT | verification 이상 주장에 필요 | likelihood ratio calibration | 08,09,10 |
| DECISION-03-013 | reveal | CORE_CONCEPT | state update와 shift 분리 | reveal-vs-shift accuracy | 05,06,10 |
| DECISION-03-014 | shift | CORE_CONCEPT | grammar/regime update 핵심 event | OOD-shift split | 05,06,10 |
| DECISION-03-015 | change-point | SUPPORTING_CONCEPT | event boundary 상위 개념 | class imbalance control | 06,07 |
| DECISION-03-016 | wrong-control-grammar hypothesis persistence | CORE_CONCEPT | 논문 문제정의 핵심 metric | metric independence | 02,10 |
| DECISION-03-017 | action-interface rewrite | CORE_CONCEPT | policy correction과 구분 | rewrite macro accuracy | 07,09,10 |
| DECISION-03-018 | decision-relevant compute | CORE_CONCEPT | uncertainty gate와 차별화 | compute-matched return | 09,10 |
| DECISION-03-019 | short-horizon rollout | SUPPORTING_CONCEPT | alternative hypothesis 평가 수단 | horizon ablation | 09,10 |
| DECISION-03-020 | compute reallocation | SUPPORTING_CONCEPT | planning budget 정책 | progress per compute | 09,10 |
| DECISION-03-021 | blocker | AUXILIARY_HEAD_ONLY | modal/overlay/permission 회복 보조 | blocker ablation | 06,07 |
| DECISION-03-022 | effect mismatch | SUPPORTING_CONCEPT | falsification input | delayed/noisy disambiguation | 06,09 |
| DECISION-03-023 | valid hypothesis switch | SUPPORTING_CONCEPT | reward/gate guardrail | switch-progress audit | 08,10 |
| DECISION-03-024 | invalid hypothesis switch | SUPPORTING_CONCEPT | reward hacking 방지 | invalid switch metric | 08,10 |

---

## 17. Required Design Revisions From Taxonomy

| Revision ID | Taxonomy Issue | Required Revision | Affected Later Step | Severity |
|---|---|---|---|---|
| REVISION-03-001 | control grammar가 precondition과 혼동됨 | `intent-to-action mapping + precondition + expected effect schema`로 고정 | 06,07,08,09 | CRITICAL |
| REVISION-03-002 | regime/grammar 분리가 약함 | same regime/different grammar 및 different regime/same grammar split 설계 | 05,06,10 | CRITICAL |
| REVISION-03-003 | current hypothesis 기준 불안정 | posterior mode가 아니라 `h_exec` 로그 저장 | 06,09,10 | CRITICAL |
| REVISION-03-004 | falsification이 verification으로 축소됨 | likelihood-ratio + posterior update + action rewrite 경로 요구 | 08,09,10 | CRITICAL |
| REVISION-03-005 | reveal/shift 경계 모호 | label rule과 ambiguous/delayed/noisy event class 추가 | 05,06 | HIGH |
| REVISION-03-006 | action-interface rewrite가 policy correction과 겹침 | same intent의 grammar-conditioned macro remapping으로 제한 | 07,09 | HIGH |
| REVISION-03-007 | decision-relevant compute가 uncertainty gate와 겹침 | action_switch_prob와 ΔV 조건 필수 | 09,10 | HIGH |
| REVISION-03-008 | latent 후보 과다 | primary 4개 후보와 auxiliary heads 분리 | 07 | HIGH |
| REVISION-03-009 | real benchmark label 부재 | real validation은 weak proxy/qualitative trace로 제한 | 10 | MEDIUM |
| REVISION-03-010 | evidence source 충돌 가능 | DOM/log/screenshot priority와 conflict handling rule 필요 | 06 | HIGH |
| REVISION-03-011 | delayed/noisy/no-effect 구분 부족 | event class를 분리하고 falsification before-filter 적용 | 06,09 | CRITICAL |
| REVISION-03-012 | h_exec 없이는 persistence 불가능 | data schema에 executed hypothesis trace 필수 추가 | 06 | CRITICAL |
| REVISION-03-013 | grammar labels가 shortcut일 수 있음 | paraphrase, decoy, class/name sanitization 필요 | 05,06 | HIGH |
| REVISION-03-014 | rewrite macro 불명확 | executable macro schema와 max length budget 필요 | 06,09 | HIGH |

---

## 18. Handoff to Later Steps

| Handoff ID | Target Step | What Must Be Used | What Must Be Verified | What Must Not Be Assumed |
|---|---|---|---|---|
| HANDOFF-03-001 | `04_TEXT_ONLY_SMOKE_TESTBED.md` | 24개 concept definition과 MCX mapping | text-only에서 grammar/reveal/shift label 생성 가능성 | taxonomy가 이미 실험 검증됐다고 가정 금지 |
| HANDOFF-03-002 | `05_SYNTHETIC_WEB_GUI_ENVIRONMENT.md` | boundary decision rules, reveal-vs-shift taxonomy | Playwright/React 환경에서 event label 구현 가능성 | real benchmark 수준 realism을 이미 확보했다고 가정 금지 |
| HANDOFF-03-003 | `06_DATA_SCHEMA_AND_LABELING.md` | concept-to-data map, h_exec/evidence label requirement | state/regime/grammar/evidence logging schema | posterior만으로 current hypothesis 정의 금지 |
| HANDOFF-03-004 | `07_LATENT_ARCHITECTURE_DESIGN.md` | latent candidate seed table | primary latent와 auxiliary head 분리 가능성 | z_control_grammar identifiability 검증 전 최종 확정 금지 |
| HANDOFF-03-005 | `08_LOSS_REWARD_TRAINING_OBJECTIVE.md` | concept-loss 연결, valid/invalid switch 정의 | loss가 taxonomy와 metric에 실제 연결되는지 | switch reward를 무조건 긍정 보상으로 가정 금지 |
| HANDOFF-03-006 | `09_PLANNING_THEORY_ALGORITHM.md` | hypothesis/falsification taxonomy, decision compute 정의 | likelihood ratio/VOC proxy의 algorithmic form | falsification을 confidence threshold로 축소 금지 |
| HANDOFF-03-007 | `10_EVALUATION_BASELINE_ABLATION.md` | concept separation tests, stress ledger | metrics/ablations가 개념 구분을 실제 검증하는지 | success rate 개선만으로 taxonomy 검증됐다고 가정 금지 |

---

## 19. Implementation Readiness Checklist

| Impl ID | Required Artifact | Why Needed | Target Step | Blocking If Missing |
|---|---|---|---|---|
| IMPL-03-001 | `h_exec` field in trace | current hypothesis/persistence metric 계산 | 06 | core metric 불가 |
| IMPL-03-002 | `true_control_grammar` field | no-grammar ablation/evaluation | 06 | grammar claim 불가 |
| IMPL-03-003 | `true_regime` field | regime/grammar separation | 06 | factorization 평가 불가 |
| IMPL-03-004 | `event_type` with reveal/shift/noisy/delayed | event taxonomy 평가 | 05,06 | false falsification 증가 |
| IMPL-03-005 | expected effect schema | falsification score 계산 | 06,08,09 | verification과 분리 불가 |
| IMPL-03-006 | observed effect record | action-effect evidence | 06 | evidence path 불가 |
| IMPL-03-007 | alternative hypothesis set | alt rollout/proposal 평가 | 09 | tree search와 구분 불가 |
| IMPL-03-008 | macro action schema | rewrite 실행 가능성 | 06,09 | action rewrite 불가 |
| IMPL-03-009 | valid/invalid switch label | reward hacking 방지 | 08,10 | switch reward 설계 불가 |
| IMPL-03-010 | modality conflict rule | DOM/screenshot/log 충돌 처리 | 06 | evidence instability |

---

## 20. Updated Risk / Unknown Ledger

| Risk ID | Risk / Unknown | Triggered By | Why It Matters | Resolution Path | Can Be Final Claim? |
|---|---|---|---|---|---|
| RISK-03-001 | control grammar가 용어 재포장으로 보일 위험 | ATTACK-004 | 핵심 novelty 붕괴 | formal schema + no-grammar ablation | NO |
| RISK-03-002 | regime/control grammar identifiability 실패 | REF-RISK-004 | 4-latent 구조 붕괴 | controlled split + probe + ablation | NO |
| RISK-03-003 | reveal/shift label ambiguity | boundary cases | event taxonomy 불안정 | label rules + ambiguous class | NO |
| RISK-03-004 | falsification이 VeriGUI verification과 겹침 | PAPER-VERIGUI | method 차별성 상실 | evidence→posterior→rewrite path | NO |
| RISK-03-005 | alternative hypothesis가 tree search로 보임 | PAPER-CUWM/WAC | planning novelty 약화 | hypothesis-indexed rollout | NO |
| RISK-03-006 | decision compute가 uncertainty gate와 겹침 | VOC search | compute contribution 약화 | action_switch_prob + ΔV gate | NO |
| RISK-03-007 | synthetic label에 과의존 | RISK-02-001 | real-world 타당성 약화 | weak proxy and auxiliary validation | NO |
| RISK-03-008 | evidence noise로 false falsification 증가 | stale/noisy event | planner instability | noisy/delayed/no-change event 분리 | NO |
| RISK-03-009 | action macro가 너무 길어짐 | rewrite taxonomy | 실행 복잡성 증가 | macro length budget | NO |
| RISK-03-010 | state가 regime/grammar를 흡수 | latent candidate analysis | ablation 해석 불가 | factorized labels and probes | NO |
| RISK-03-011 | real benchmark에서 h_exec 로그 없음 | current hypothesis definition | persistence metric 계산 어려움 | internal module logging only | NO |
| RISK-03-012 | intent extraction 오류가 grammar failure로 오분류 | intent concept | problem definition contamination | frozen base intent trace and intent-error filter | NO |
| RISK-03-013 | policy correction과 rewrite 구분 불명확 | WAC threat | related work 방어 실패 | same-intent remapping criterion | NO |
| RISK-03-014 | visual grounding failure와 grammar failure 혼동 | VisualWebArena threat | failure taxonomy collapse | same visual layout/different grammar test | NO |
| RISK-03-015 | concept 수가 너무 많음 | STRESS-03-001 | method readability 저하 | core/supporting/auxiliary pruning | NO |
| RISK-03-016 | grammar label leakage | synthetic env | shortcut classifier 위험 | DOM class/text sanitization | NO |
| RISK-03-017 | delayed effect를 failure로 오분류 | event taxonomy | false planning call 증가 | delayed event window | NO |
| RISK-03-018 | valid switch reward hacking | reward design | oscillation 유도 | progress-linked switch only | NO |

---

## 21. Quality Gate Result

| Gate ID | Gate | PASS/FAIL/PARTIAL | Evidence | If Not PASS, Blocker |
|---|---|---|---|---|
| QG-03-01 | 00/01/02 refs imported | PASS | Imported References 50개 이상 포함 | 없음 |
| QG-03-02 | search expansion 20개 이상 수행 | PASS | Search Expansion Ledger 22개 작성 | 없음 |
| QG-03-03 | core concept 20개 이상 정의 | PASS | Core Concept Definition Table 24개 작성 | 없음 |
| QG-03-04 | boundary case 15개 이상 검토 | PASS | Boundary Case Decision Table 18개 작성 | 없음 |
| QG-03-05 | concept separation matrix 12개 이상 작성 | PASS | Concept Separation Matrix 14개 작성 | 없음 |
| QG-03-06 | concept-to-data/metric/loss/module map 작성 | PASS | 24개 concept 모두 연결 | 없음 |
| QG-03-07 | latent candidate seed table 작성 | PASS | 14개 latent 후보 작성 | 없음 |
| QG-03-08 | reveal-vs-shift taxonomy 별도 작성 | PASS | 10개 event type 별도 정의 | 없음 |
| QG-03-09 | taxonomy stress test 20개 이상 작성 | PASS | 24개 stress attack 작성 | 없음 |
| QG-03-10 | no final architecture/loss/reward prematurely accepted | PASS | status를 candidate/contract로 제한 | 없음 |
| QG-03-11 | Claude Code routing 추가 | PASS | §2 routing table 포함 | 없음 |
| QG-03-12 | implementation readiness 추가 | PASS | §19 checklist 포함 | 없음 |
| QG-03-13 | hidden-label leakage 주의 명시 | PASS | §14, §17, §19 반영 | 없음 |

---

## 22. Final Statement

```text
03_CORE_CONCEPT_TAXONOMY.md is a taxonomy contract file, not a final method section.

The most important concept distinctions are:
- regime은 UI/environment의 interaction mode이고, control grammar는 같은 intent를 executable action/macro로 번역하는 규칙이다.
- reveal은 hidden state의 관측 가능성이 증가하는 사건이고, shift는 regime/control-grammar law가 바뀌는 사건이다.
- verification은 action outcome의 성공/실패 확인이고, falsification은 h_exec가 evidence를 설명하지 못해 alternative hypothesis로 posterior/update/rewrite를 유도하는 과정이다.
- alternative hypothesis는 alternative action이 아니라 evidence를 설명하는 대체 state/regime/grammar 가설이다.
- decision-relevant compute는 uncertainty threshold가 아니라 alternative hypothesis가 action/value decision을 바꿀 때 쓰는 compute allocation 원칙이다.

The concepts that remain risky or ambiguous are:
- control grammar: precondition/effect schema와의 중복 위험이 있으며 no-control-grammar ablation으로 검증해야 한다.
- regime vs control grammar: synthetic split에서 분리 가능성을 보여야 한다.
- reveal vs shift: real Web/GUI에서는 약한 proxy만 가능할 수 있다.
- falsification: likelihood-ratio calibration이 실패하면 verification과 구분되지 않는다.
- wrong-control-grammar persistence: real benchmark에서 ground-truth grammar label이 없어 weak measurement로 제한될 수 있다.

The next required file is:
04_TEXT_ONLY_SMOKE_TESTBED.md
```
