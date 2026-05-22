---
file_id: STEP-04
title: Text-Only Smoke Testbed for FRCG-WM
version: v1.0
status: smoke_test_design_not_main_experiment
language: ko
depends_on:
  - 00_MASTER_REFERENCE.md
  - 01_RELATED_WORK_THREAT_MAP.md
  - 02_PROBLEM_NOVELTY_FALSIFICATION.md
  - 03_CORE_CONCEPT_TAXONOMY.md
must_read_before_implementation:
  - 00_MASTER_REFERENCE.md
  - 03_CORE_CONCEPT_TAXONOMY.md
must_not_skip:
  - pass_fail_gate
  - ablation_suite
  - reward_hacking_audit
  - leakage_and_shortcut_audit
  - implementation_contract
purpose:
  - Web/GUI 환경 구현 전에 FRCG-WM 핵심 메커니즘이 최소 symbolic/text-only 조건에서 살아남는지 검증한다.
  - wrong-control-grammar hypothesis persistence, falsification, alternative grammar selection, action-interface rewrite, decision-relevant compute를 계산 가능한 실험 계약으로 만든다.
  - Step 05 Synthetic Web/GUI Environment로 넘어갈 수 있는지 판단하는 pass/fail gate를 제공한다.
forbidden:
  - Do not treat this as the final main experiment.
  - Do not finalize Web/GUI environment design.
  - Do not finalize architecture/loss/reward for the paper.
  - Do not claim empirical success without running experiments.
  - Do not use text-only success as evidence for visual grounding or real browser robustness.
  - Do not hide toy/shortcut/leakage risks.
next_files:
  - 05_SYNTHETIC_WEB_GUI_ENVIRONMENT.md
  - 06_DATA_SCHEMA_AND_LABELING.md
  - 07_LATENT_ARCHITECTURE_DESIGN.md
  - 08_LOSS_REWARD_TRAINING_OBJECTIVE.md
  - 09_PLANNING_THEORY_ALGORITHM.md
  - 10_EVALUATION_BASELINE_ABLATION.md
---

# 04_TEXT_ONLY_SMOKE_TESTBED.md

## 0. Claude Code Context Routing

Claude Code는 이 파일을 단독으로 읽고 구현을 시작하면 안 된다. 이 파일은 text-only smoke testbed 설계서이며, 개념 정의와 최종 평가 계약은 다른 파일에 분산되어 있다.

| 작업 의도 | 먼저 읽을 파일 | 이어서 읽을 파일 | 금지 가정 |
|---|---|---|---|
| text-only 환경 구현 | `04_TEXT_ONLY_SMOKE_TESTBED.md` §5~§13 | `03_CORE_CONCEPT_TAXONOMY.md`, `06_DATA_SCHEMA_AND_LABELING.md` | text-only schema가 final Web/GUI schema라고 가정 금지 |
| control grammar test case 추가 | `03_CORE_CONCEPT_TAXONOMY.md` §4~§7 | `04` §6~§8, `05_SYNTHETIC_WEB_GUI_ENVIRONMENT.md` | grammar를 precondition 하나로 축소 금지 |
| reward/recovery 실험 수정 | `04` §9~§14 | `08_LOSS_REWARD_TRAINING_OBJECTIVE.md`, `10_EVALUATION_BASELINE_ABLATION.md` | switch reward를 무조건 positive reward로 두지 말 것 |
| ablation runner 작성 | `04` §11~§13 | `07_LATENT_ARCHITECTURE_DESIGN.md`, `09_PLANNING_THEORY_ALGORITHM.md`, `10` | success rate만 출력하고 끝내지 말 것 |
| Step 05로 확장 | `04` §15~§18 | `05`, `06`, `10` | text-only 성공을 visual/DOM robustness로 일반화 금지 |

---

## 1. File Purpose

이 파일은 메인 실험 설계가 아니다. 이 파일은 Web/GUI 환경을 구현하기 전에, 핵심 아이디어가 최소 symbolic/text-only 조건에서도 살아남는지 죽여보는 **viability gate**다.

검증 대상은 다음 5개뿐이다.

1. `wrong-control-grammar hypothesis persistence`가 structured symbolic log에서 계량 가능한가.
2. action-effect evidence가 current hypothesis를 반증하는 신호로 작동하는가.
3. alternative grammar selection이 단순 action search보다 recovery에 도움을 주는가.
4. action-interface rewrite가 같은 intent를 다른 executable macro로 바꾸어 progress를 만드는가.
5. decision-relevant compute가 uncertainty-gated planning이나 always-plan보다 compute 효율이 좋은가.

이 파일의 성공은 최종 성공이 아니다. text-only는 DOM tree, screenshot, element localization, rendering delay, browser execution noise를 제거한다. 따라서 text-only 성공은 **Step 05로 갈 자격**일 뿐이고, Web/GUI claim의 증거가 아니다.

반대로 text-only에서조차 다음 ablation이 무너지지 않으면 Step 05로 넘어가면 안 된다.

- `ABL-NO-GRAMMAR`
- `ABL-NO-FALSIFICATION`
- `ABL-NO-ALT`
- `ABL-NO-REWRITE`
- `BASE-VERIFIER`
- `BASE-NEXTSTATE-WM`
- `BASE-UNCERTAINTY`

---

## 2. Design Constitution

| Constitution ID | 대원칙 | 이유 | 위반 시 결과 |
|---|---|---|---|
| CONST-04-001 | text-only는 final experiment가 아니라 falsification gate다 | Web/GUI complexity를 제거했기 때문 | 논문 claim 과대화 |
| CONST-04-002 | visual grounding은 성공했다고 가정한다 | grammar failure만 분리하기 위함 | visual failure와 grammar failure 혼동 |
| CONST-04-003 | base intent는 맞는 subset을 반드시 별도 둔다 | planning failure와 grammar failure 분리 | 문제정의 붕괴 |
| CONST-04-004 | current hypothesis는 직전 action 생성에 사용된 `h_exec`여야 한다 | persistence metric 기준 | posterior mode와 혼동 |
| CONST-04-005 | alternative는 action이 아니라 grammar/regime hypothesis다 | tree search와 구분 | generic search로 collapse |
| CONST-04-006 | falsification은 failed-action flag가 아니다 | VeriGUI-style verification과 구분 | novelty 약화 |
| CONST-04-007 | reward는 metric이 아니라 action selection 또는 training proxy에 작용해야 한다 | reward design validity | reward-only reporting |
| CONST-04-008 | 모든 pass/fail gate는 baseline/ablation과 연결되어야 한다 | 메인트랙 설득력 | “좋아 보이는 toy”로 끝남 |

---

## 3. Imported References

| Imported ID | Source File | Type | Meaning | Why It Matters | Priority |
|---|---|---|---|---|---|
| REF-CORE-001 | 00_MASTER_REFERENCE.md | core thesis | wrong-control-grammar hypothesis persistence | text-only에서 직접 계량해야 하는 핵심 failure mode | CRITICAL |
| REF-CORE-002 | 00_MASTER_REFERENCE.md | core thesis | latent regime/control-grammar world model | text-only에서는 symbolic proxy로 검증 | CRITICAL |
| REF-CORE-003 | 00_MASTER_REFERENCE.md | core thesis | action-effect evidence 기반 falsification | expected/observed effect 불일치 생성 필요 | CRITICAL |
| REF-CORE-004 | 00_MASTER_REFERENCE.md | core thesis | current-vs-alternative hypothesis rollout | top-k grammar 비교 가능성 검증 | CRITICAL |
| REF-CORE-005 | 00_MASTER_REFERENCE.md | core thesis | intent-to-action rewrite | symbolic action macro로 검증 | CRITICAL |
| REF-CORE-006 | 00_MASTER_REFERENCE.md | core thesis | decision-relevant compute reallocation | progress-per-compute 측정 필요 | CRITICAL |
| REF-CONCEPT-003 | 03_CORE_CONCEPT_TAXONOMY.md | concept | regime | `hidden_regime` schema의 기반 | CRITICAL |
| REF-CONCEPT-004 | 03_CORE_CONCEPT_TAXONOMY.md | concept | control grammar | `hidden_control_grammar` schema의 기반 | CRITICAL |
| REF-CONCEPT-009 | 03_CORE_CONCEPT_TAXONOMY.md | concept | current hypothesis | `h_exec` logging 필요 | CRITICAL |
| REF-CONCEPT-010 | 03_CORE_CONCEPT_TAXONOMY.md | concept | alternative hypothesis | top-k grammar 후보 정의 | CRITICAL |
| REF-CONCEPT-012 | 03_CORE_CONCEPT_TAXONOMY.md | concept | falsification | failed-action flag와 분리 | CRITICAL |
| REF-CONCEPT-017 | 03_CORE_CONCEPT_TAXONOMY.md | concept | action-interface rewrite | macro action generation 필요 | CRITICAL |
| REF-CONCEPT-018 | 03_CORE_CONCEPT_TAXONOMY.md | concept | decision-relevant compute | uncertainty gate와 분리 | CRITICAL |
| MCX-001 | 02_PROBLEM_NOVELTY_FALSIFICATION.md | counterexample | pagination vs infinite scroll | 필수 text-only test로 변환 | CRITICAL |
| MCX-002 | 02_PROBLEM_NOVELTY_FALSIFICATION.md | counterexample | modal-blocked direct click | 필수 text-only test로 변환 | CRITICAL |
| MCX-003 | 02_PROBLEM_NOVELTY_FALSIFICATION.md | counterexample | form-invalid disabled submit | precondition/grammar 경계 검증 | CRITICAL |
| MCX-004 | 02_PROBLEM_NOVELTY_FALSIFICATION.md | counterexample | loading/stale DOM timing | delayed/noisy event 분리 | HIGH |
| ATTACK-VERIGUI | 01_RELATED_WORK_THREAT_MAP.md | threat | action-effect verification overlap | verifier-only baseline 필수 | CRITICAL |
| ATTACK-WORLD-MODEL | 01_RELATED_WORK_THREAT_MAP.md | threat | generic world model overlap | next-state-WM baseline 필수 | CRITICAL |
| ATTACK-TREE-SEARCH | 01_RELATED_WORK_THREAT_MAP.md | threat | “그냥 tree search” 공격 | alternative hypothesis와 action search 분리 필요 | CRITICAL |

---

## 4. Search Expansion Ledger

이 섹션은 Step 04 구현을 위한 외부 anchor다. 단, 이 파일은 관련연구 정리문이 아니므로 세부 citation-grade 검증은 `01_RELATED_WORK_THREAT_MAP.md`와 `10_EVALUATION_BASELINE_ABLATION.md`에서 관리한다.

| Search ID | Query / Anchor | Source/Paper/Concept | Key Finding | How It Informs Testbed | Risk/Threat | Follow-up |
|---|---|---|---|---|---|---|
| SEARCH-04-001 | MiniWoB++ web interaction environment | MiniWoB++ | controlled browser tasks and Gym-style API | text-only task family를 synthetic Web task로 확장하는 기준 | modern GUI complexity 부족 | Step 05에서 DOM/visual 확장 |
| SEARCH-04-002 | TextWorld reinforcement learning environment | TextWorld | generated text-based environment, state/reward tracking | structured text observation/state/reward schema 참고 | GUI interaction law와 직접 동일하지 않음 | text-only로만 제한 |
| SEARCH-04-003 | STRIPS/PDDL precondition effect schema | Classical planning | action schema = precondition + effect | `action_preconditions`, `action_effects` 설계 근거 | control grammar가 PDDL 재포장으로 보일 수 있음 | intent mapping 포함으로 구분 |
| SEARCH-04-004 | POMDP hidden state | POMDP literature | observation does not fully reveal state | `hidden_state`와 `state_text` 분리 근거 | regime/grammar가 hidden state로 흡수될 위험 | taxonomy separation 유지 |
| SEARCH-04-005 | Bayesian online change point detection | BOCPD / nonstationary RL | evidence 이후 transition detection delay 중요 | evidence-to-update delay metric 참고 | Step 04에 theory 과부하 위험 | Step 09로 이관 |
| SEARCH-04-006 | Value of computation planning | rational metareasoning / VOC | computation has value only if it can change decisions | decision-relevant compute gate 근거 | exact VOC 계산 과장 금지 | heuristic proxy로 사용 |
| SEARCH-04-007 | VeriGUI action-effect verification | VeriGUI | action outcome verification and recovery | `BASE-VERIFIER` 강 baseline 필요 | FRCG가 verification으로 흡수될 위험 | posterior/update/rewrite metric으로 분리 |
| SEARCH-04-008 | Recovery benchmark for failed agents | Recovery-Bench / PALADIN family | failed trajectories and recovery quality | recovery delay/failure pollution stress 참고 | GUI-specific grammar는 별도 설계 필요 | Step 10에서 baseline화 |
| SEARCH-04-009 | WebArena | realistic web benchmark | real web workflows but no hidden grammar labels | Step 05/10 external validity anchor | text-only 성공 과대화 방지 | auxiliary validation |
| SEARCH-04-010 | VisualWebArena | multimodal web benchmark | visual grounding required tasks | text-only limitation 명시 | visual grounding 검증 불가 | Step 05로 이관 |
| SEARCH-04-011 | action model learning with conditional effects | action model learning | conditional effects complicate action schemas | grammar/effect schema library 설계 | grammar library 과복잡화 | initial grammar 제한 |
| SEARCH-04-012 | GUI execution disturbance / latency | GUI robustness studies | delays, interrupts, stale targets matter | delayed/noisy event stress 설계 | text-only latency proxy 약함 | Step 05 async simulation |
| SEARCH-04-013 | agent failure trace taxonomy | failure diagnosis studies | structured trace helps failure classification | action-effect log fields 설계 | failure diagnosis로만 보일 위험 | closed-loop recovery 추가 |
| SEARCH-04-014 | RLDS / trajectory format | RL trajectory schemas | episode/step/action/reward logging precedent | later schema compatibility | too generic | Step 06 schema contract |
| SEARCH-04-015 | reward shaping | RL reward shaping | dense reward can help but may hack | reward hacking guardrail 필요 | progress reward shortcut | Step 08로 이관 |

---

## 5. Text-Only Testbed Scope

| Scope ID | Question | Decision | Reason | Risk | Later Step |
|---|---|---|---|---|---|
| SCOPE-04-001 | 이 testbed는 최종 메인 실험인가? | 아니다. | DOM/screenshot/browser execution을 제거했기 때문이다. | toy benchmark로 과대해석 | 05/10 |
| SCOPE-04-002 | 무엇을 검증하는가? | grammar persistence, falsification, alt adoption, rewrite, compute gate | 핵심 mechanism만 분리 검증 | mechanism metric 부재 시 무의미 | 10 |
| SCOPE-04-003 | 무엇을 검증하지 못하는가? | visual grounding, DOM complexity, real latency, selector failure | text-only abstraction의 한계 | Web/GUI claim 과장 | 05 |
| SCOPE-04-004 | visual grounding은 어떻게 처리하는가? | 성공한 것으로 통제한다. | grammar failure만 분리하기 위함 | 실제 visual failure와 혼동 | 05/10 |
| SCOPE-04-005 | base intent는 어떻게 처리하는가? | intent-correct subset을 별도 둔다. | planning failure와 grammar failure 분리 | base LLM 실패를 FRCG 실패로 오분류 | 07/10 |
| SCOPE-04-006 | DOM 없이도 가능한 핵심은? | action-effect mismatch, current/alternative hypothesis, recovery delay | symbolic transition으로 재현 가능 | evidence가 너무 깨끗함 | 06 |
| SCOPE-04-007 | text-only 성공 후 GUI 실패 가능성은? | 높다. | DOM noise, async, screenshot ambiguity가 없다. | generalization overclaim | 05 |
| SCOPE-04-008 | text-only 실패 시 폐기 대상은? | grammar library, falsification gate, alternative proposer, rewrite module 중 원인을 분리 | 최소 환경에서 실패하면 Web/GUI로 갈 이유가 약함 | threshold 문제와 개념 문제 혼동 | 07/09/10 |
| SCOPE-04-009 | toy로 보이지 않기 위한 조건은? | 10+ family, 15+ grammar, OOD split, lexical cue removal | hand-crafted 몇 개로는 부족 | keyword benchmark화 | 05/06 |
| SCOPE-04-010 | 최종 논문에서 위치는? | sanity/ablation/appendix 또는 early viability result | 메인 claim은 Step 05/10에서 검증 | text-only main result로 과장 | FINAL |

---

## 6. Canonical Episode Schema

### 6.1 Canonical JSON Example

```json
{
  "episode_id": "ep_000001",
  "split": "text_id",
  "task_family": "shopping_search_filter",
  "instruction": "Find a wireless mouse under $30 with rating >= 4 and add it to cart.",
  "state_text": "A product list is visible. A filter panel is collapsed. A generic overlay message is present.",
  "hidden_state": {
    "progress_step": 0,
    "modal_active": true,
    "filter_panel_open": false,
    "cart_count": 0,
    "loading": false,
    "required_option_selected": false
  },
  "hidden_regime": "modal_blocked",
  "hidden_control_grammar": "remove_blocker_before_target_action",
  "agent_intent": "open_filter_panel",
  "available_actions": [
    "click_filter_button",
    "close_overlay_message",
    "scroll_down",
    "wait",
    "click_product_card"
  ],
  "action_preconditions": {
    "click_filter_button": "modal_active == false",
    "close_overlay_message": "modal_active == true"
  },
  "action_effects": {
    "close_overlay_message": {
      "modal_active": false,
      "progress_delta": 0.1,
      "effect_type": "blocker_removed"
    },
    "click_filter_button": {
      "filter_panel_open": true,
      "progress_delta": 0.2,
      "effect_type": "panel_opened"
    }
  },
  "h_exec": {
    "regime": "direct_click",
    "control_grammar": "click_target_directly"
  },
  "expected_effect_under_h_exec": {
    "filter_panel_open": true
  },
  "observed_effect": {
    "effect_type": "no_state_change",
    "filter_panel_open": false,
    "progress_delta": 0.0
  },
  "failed_action_evidence": {
    "evidence_type": "precondition_blocked",
    "message": "click_filter_button produced no state change because modal_active == true."
  },
  "event_type": "failed_action",
  "alternative_hypotheses": [
    {
      "regime": "modal_blocked",
      "control_grammar": "remove_blocker_before_target_action"
    },
    {
      "regime": "loading_stale",
      "control_grammar": "wait_until_stable_before_click"
    }
  ],
  "correct_alternative_hypothesis": {
    "regime": "modal_blocked",
    "control_grammar": "remove_blocker_before_target_action"
  },
  "rewrite_target": ["close_overlay_message", "click_filter_button"],
  "progress_state": {
    "subgoal_completed": false,
    "progress_score": 0.0
  },
  "reward_components": {
    "progress_reward": 0.0,
    "failed_action_penalty": -0.2,
    "repeated_failure_penalty": 0.0,
    "recovery_reward": 0.0,
    "valid_switch_reward": 0.0,
    "invalid_switch_penalty": 0.0,
    "compute_cost_penalty": -0.01
  },
  "done": false,
  "success": false
}
```

### 6.2 Field Definition Table

| Field ID | Field Name | Type | Meaning | Example | Required For | Risk If Missing |
|---|---|---|---|---|---|---|
| FIELD-04-001 | episode_id | string | episode unique id | ep_000001 | trace/debug | 재현 불가 |
| FIELD-04-002 | split | enum | text_id/text_ood_grammar/text_ood_task/text_noisy | text_ood_grammar | OOD 평가 | split 분석 불가 |
| FIELD-04-003 | task_family | enum | 상위 task 유형 | shopping_search_filter | family stratification | toy overfit 감지 불가 |
| FIELD-04-004 | instruction | string | 사용자 목표 | Find a mouse... | base intent | intent 분석 불가 |
| FIELD-04-005 | state_text | string | public text observation | product list visible | agent input | observation 없음 |
| FIELD-04-006 | hidden_state | object | simulator state | modal_active=true | ground truth transition | progress 계산 불가 |
| FIELD-04-007 | hidden_regime | enum | true interaction mode | modal_blocked | regime metric | regime ablation 불가 |
| FIELD-04-008 | hidden_control_grammar | enum | true grammar | remove_blocker_before_target_action | core metric | 핵심 claim 불가 |
| FIELD-04-009 | agent_intent | enum/string | 현재 subgoal | open_filter_panel | intent/action 분리 | base failure와 confound |
| FIELD-04-010 | available_actions | list | candidate primitive actions | click_filter_button | action selection | 정답 후보 부재 감지 불가 |
| FIELD-04-011 | action_preconditions | dict | action executability conditions | modal_active==false | precondition analysis | grammar/precondition 혼동 |
| FIELD-04-012 | action_effects | dict | true action effect schema | cart_count++ | rollout target | WM baseline 불가 |
| FIELD-04-013 | h_exec | object | executed hypothesis used to choose previous action | direct_click | persistence metric | posterior mode와 혼동 |
| FIELD-04-014 | expected_effect_under_h_exec | object | expected effect under h_exec | panel_opened | falsification | verification과 분리 불가 |
| FIELD-04-015 | observed_effect | object | actual effect after action | no_state_change | evidence | failed action 감지 불가 |
| FIELD-04-016 | failed_action_evidence | object | structured evidence of mismatch | precondition_blocked | falsification scorer | evidence update 불가 |
| FIELD-04-017 | event_type | enum | none/reveal/shift/failed/noisy/delayed | failed_action | event metric | delayed/noisy 오분류 |
| FIELD-04-018 | alternative_hypotheses | list | top-k alt regime/grammar hypotheses | modal_blocked | alt rollout | tree search와 구분 불가 |
| FIELD-04-019 | correct_alternative_hypothesis | object | oracle best alternative | modal_blocked | alt adoption metric | oracle eval 불가 |
| FIELD-04-020 | rewrite_target | list/action macro | correct executable rewrite | close_modal→click | rewrite training/eval | action-interface 검증 불가 |
| FIELD-04-021 | progress_state | object | progress/subgoal info | progress_score=0.4 | dense reward | sparse success만 남음 |
| FIELD-04-022 | progress_delta | float | step progress change | 0.2 | reward/return | progress per compute 불가 |
| FIELD-04-023 | reward_components | object | reward decomposition | failed=-0.2 | reward audit | reward hacking 원인 분석 불가 |
| FIELD-04-024 | compute_cost | float | planning/rollout cost | 0.03 | compute metric | always-plan 비교 불공정 |
| FIELD-04-025 | previous_action | string/object | previous executed action | click_filter_button | repetition | 반복 실패 계산 불가 |
| FIELD-04-026 | action_validity | enum | valid/blocked/noop/delayed | blocked | failure taxonomy | no-effect 오분류 |
| FIELD-04-027 | hypothesis_updated | bool | belief/h_exec update 여부 | true | update delay | persistence metric 불안정 |
| FIELD-04-028 | selected_alternative | object/null | selected alt hypothesis | modal_blocked | alt adoption rate | proposer 평가 불가 |
| FIELD-04-029 | rewritten_action | list/null | actual rewritten macro | close_modal→click_filter | rewrite metric | policy correction과 혼동 |
| FIELD-04-030 | done | bool | episode end | false | rollout loop | termination 불명확 |
| FIELD-04-031 | success | bool | task success | false | success rate | final outcome 없음 |
| FIELD-04-032 | audit_flags | list | shortcut/leakage flags | lexical_cue_removed | leakage audit | toy shortcut 탐지 불가 |

---

## 7. Task Family Design

| Family ID | Task Family | Typical Intent | Possible Regimes | Wrong Grammar Cases | Recovery Grammar | Why Useful |
|---|---|---|---|---|---|---|
| FAM-04-001 | shopping_search_filter | filter/search/apply | modal_blocked, hidden_filter, loading, infinite_scroll | direct filter click 반복 | close_modal → open_filter → set_filter | e-commerce workflow와 연결 |
| FAM-04-002 | product_listing_navigation | next_results | pagination, infinite_scroll, scroll_container | Next click/scroll 오용 | scroll_container 또는 click_next | pagination/infinite scroll 반례 |
| FAM-04-003 | cart_add_to_cart | add_to_cart | form_invalid, prerequisite_option, disabled_button | add button 반복 | select_option → add | precondition/grammar 검증 |
| FAM-04-004 | checkout_form | submit_checkout | form_invalid, confirmation_flow, permission_required | submit 반복 | fill_required → confirm → submit | multi-step prerequisite |
| FAM-04-005 | account_settings | navigate/update_setting | responsive_menu, modal_blocked | top-nav 직접 클릭 | open_menu → settings | responsive menu shift |
| FAM-04-006 | dashboard_filtering | apply_filter | hidden_filter, accordion_reveal, loading | hidden filter 직접 select | expand → select → wait | reveal vs shift 분리 |
| FAM-04-007 | knowledge_base_search | search/open_result | search_result_replaced, stale_state | old result click | wait_replaced → click_new | stale/noisy evidence |
| FAM-04-008 | ticket_creation | create_ticket | form_invalid, attachment_required | submit_ticket 반복 | fill_missing → attach → submit | required field/macro |
| FAM-04-009 | permission_workflow | authorize_action | permission_required, confirmation_flow | target direct action | grant_permission → action | permission gate |
| FAM-04-010 | profile_update | save_profile | validation_error, disabled_button | save 반복 | fix_field → save | validation evidence |
| FAM-04-011 | calendar_creation | create_event | date_picker_hidden, confirmation_flow | submit direct | open_picker → select_date → submit | hidden widget macro |
| FAM-04-012 | document_management | upload/share/delete | async_upload, confirmation_flow | share/delete 반복 | wait_upload → share | delayed effect |

---

## 8. Regime and Control Grammar Library

| Grammar ID | Regime | Control Grammar | Intent Mapping | Preconditions | Expected Effect | Common Wrong Hypothesis | Evidence Against Wrong Hypothesis |
|---|---|---|---|---|---|---|---|
| GRAM-04-001 | pagination | click_next_button | next_results → click(next_button) | next_button visible/enabled | page_index += 1; results replaced | scroll_down | no new items after scroll |
| GRAM-04-002 | infinite_scroll | scroll_container_for_more | next_results → scroll(container) | container scrollable | result_cards appended | click_next_button | next button absent |
| GRAM-04-003 | modal_blocked | remove_blocker_before_target_action | target_action → close_modal → target_action | modal_active=true | blocker removed, target actionable | click_target_directly | click no-effect, modal active |
| GRAM-04-004 | form_invalid | fill_required_before_submit | submit → fill_required → submit | required_missing=true | validation clears, submit works | submit_directly | required warning appears |
| GRAM-04-005 | loading_stale | wait_until_stable_before_click | click_result → wait → click | loading=true/stale=true | stable result opens | click_immediately | stale/no-op |
| GRAM-04-006 | disabled_button | satisfy_prerequisite_to_enable | click_button → prerequisite → click_button | enabled=false | enabled then effect | click_disabled | no_state_change |
| GRAM-04-007 | hidden_filter | open_filter_panel_before_select | filter → open_filter → select_filter | panel_open=false | filter visible | select_directly | target absent |
| GRAM-04-008 | responsive_menu | expand_menu_before_navigation | navigate → open_menu → click_nav | nav_collapsed=true | nav item visible | click_top_nav | top nav absent |
| GRAM-04-009 | permission_required | grant_permission_before_action | action → grant_permission → action | prompt_active=true | permission granted | action_directly | permission prompt |
| GRAM-04-010 | confirmation_flow | confirm_after_action | finalize → click_action → confirm | confirmation_required=true | commit state | assume_final | pending confirmation |
| GRAM-04-011 | accordion_reveal | expand_section_before_target | access_hidden → expand → target | collapsed=true | target visible | click_hidden_target | target absent |
| GRAM-04-012 | scroll_container_vs_page | scroll_inner_container | view_more → scroll(inner) | inner_scrollable=true | inner list moves | scroll_page | page no effect |
| GRAM-04-013 | search_result_replaced | wait_for_replaced_results | search/open → wait → click_new | replacing=true | new results available | click_old | stale result |
| GRAM-04-014 | prerequisite_option | select_option_before_add | add → select_option → add | option_required=true | cart_count++ | add_directly | missing option error |
| GRAM-04-015 | overlay_intercept | dismiss_overlay_before_click | click_target → dismiss_overlay → click_target | overlay_intercepts=true | target receives click | click_target_directly | click swallowed |
| GRAM-04-016 | date_picker_hidden | open_picker_select_submit | set_date → open_picker → select → submit | picker_closed=true | date valid | submit_direct | missing date |
| GRAM-04-017 | async_upload | wait_upload_completion_before_share | share → wait_upload → share | upload_in_progress=true | share enabled | share_immediately | share disabled |

---

## 9. Minimal Text-Only Test Case Suite

| Test ID | Scenario | Instruction | True Regime | True Grammar | Wrong Current Hypothesis | Failed Action Evidence | Correct Alternative | Expected Progress |
|---|---|---|---|---|---|---|---|---|
| TEST-04-001 | pagination vs infinite scroll | 더 많은 상품 결과를 보여줘 | infinite_scroll | scroll_container_for_more | pagination/click_next_button | next_button absent | scroll_container_for_more | new_results_visible |
| TEST-04-002 | modal-blocked direct click | 필터 패널을 열어줘 | modal_blocked | remove_blocker_before_target_action | direct_click | click no_state_change; modal_active=true | close_modal→click_filter | filter_panel_open |
| TEST-04-003 | form-invalid disabled submit | 양식을 제출해 | form_invalid | fill_required_before_submit | submit_directly | required_missing warning | fill_required→submit | submitted=true |
| TEST-04-004 | loading/stale DOM timing | 검색 결과 첫 번째를 열어 | loading_stale | wait_until_stable_before_click | click_immediately | stale result | wait→click | result_opened |
| TEST-04-005 | responsive menu hidden navigation | 설정으로 이동해 | responsive_menu | expand_menu_before_navigation | click_top_nav | top nav absent | open_menu→settings | settings_open |
| TEST-04-006 | hidden filter accordion | 가격 필터를 설정해 | hidden_filter | open_filter_panel_before_select | select_price_direct | price filter absent | open_filter→select_price | filter_applied |
| TEST-04-007 | permission flow | 문서 공유를 활성화해 | permission_required | grant_permission_before_action | share_directly | permission prompt | grant→share | shared=true |
| TEST-04-008 | required option before add | 신발을 장바구니에 넣어 | prerequisite_option | select_option_before_add | add_directly | size_missing | select_size→add | cart_count++ |
| TEST-04-009 | scroll container vs page | 댓글 더 보기 | scroll_container_vs_page | scroll_inner_container | scroll_page | page no list diff | scroll_inner | comments_appended |
| TEST-04-010 | overlay intercept | 체크아웃을 눌러 | overlay_intercept | dismiss_overlay_before_click | click_checkout | overlay swallowed click | dismiss→checkout | checkout_open |
| TEST-04-011 | result replaced | 새 검색 결과 열기 | search_result_replaced | wait_for_replaced_results | click_old_result | stale old result | wait→click_new | result_opened |
| TEST-04-012 | disabled save | 저장해 | disabled_button | satisfy_prerequisite_to_enable | click_disabled_save | save_enabled=false | fix_field→save | saved=true |
| TEST-04-013 | accordion reveal | FAQ 답변 열기 | accordion_reveal | expand_section_before_target | click_answer | answer hidden | expand_question | answer_visible |
| TEST-04-014 | confirmation | 계정을 삭제해 | confirmation_flow | confirm_after_action | delete_once_stop | pending confirm | delete→confirm | deleted=true |
| TEST-04-015 | date picker | 회의 날짜 설정 | date_picker_hidden | open_picker_select_submit | submit_direct | date_missing | open_picker→select→submit | date_set |
| TEST-04-016 | async upload | 파일 업로드 후 공유 | async_upload | wait_upload_completion_before_share | share_immediately | upload_in_progress | wait_upload→share | shared=true |
| TEST-04-017 | noisy no-effect | 필터 적용 | loading_stale | wait_until_stable_before_click | grammar_shift_to_hidden_filter | noisy observation | wait or verify | no false switch |
| TEST-04-018 | spurious alternative | 장바구니 추가 | prerequisite_option | select_option_before_add | modal_blocked | no modal evidence | select_option_before_add | avoid wrong alt |

---

## 10. Reward Instrumentation

| Reward ID | Component | Formula/Rule | Intended Effect | Reward Hacking Risk | Guardrail |
|---|---|---|---|---|---|
| REWARD-04-001 | progress reward | `r = progress_delta` | subgoal progress 유도 | easy progress shortcut | task-family normalized progress |
| REWARD-04-002 | failed-action penalty | `-α_fail` if failed_action | no-op/invalid action 감소 | exploration 억제 | first failure weak, repeated strong |
| REWARD-04-003 | repeated-failure penalty | `-α_repeat * n_same_wrong_mapping` | persistence 감소 | 다른 wrong action으로 회피 | same intent + same grammar 기준 |
| REWARD-04-004 | recovery reward | `+α_rec` if progress within H after failure | 회복 유도 | 일부러 실패 유도 | deliberate repeated failure 차단 |
| REWARD-04-005 | valid switch reward | `+α_switch` only if evidence + better alt + progress | 근거 있는 grammar switch 장려 | switch spam | 4조건 모두 만족해야 함 |
| REWARD-04-006 | invalid switch penalty | `-α_invalid` if switch without evidence/progress | oscillation 방지 | OOD exploration 억제 | high falsification exception |
| REWARD-04-007 | compute cost penalty | `-β * rollout_steps` | always-plan 방지 | planning off collapse | necessary planning allowance |
| REWARD-04-008 | terminal success bonus | `+α_success` if success | final completion 반영 | mechanism metric 가림 | auxiliary only |

---

## 11. Metric Instrumentation

| Metric ID | Metric | Computation Rule | Required Fields | What It Tests | Failure Interpretation |
|---|---|---|---|---|---|
| METRIC-04-001 | task success rate | success / episodes | success | 최종 완료 | mechanism 미검증 |
| METRIC-04-002 | normalized return | sum reward normalized by family | reward_components | dense performance | reward shaping 의존 |
| METRIC-04-003 | failed-action repetition rate | repeated failed mapping / failed steps | action_validity, h_exec | 반복 실패 | 줄지 않으면 core benefit 약함 |
| METRIC-04-004 | wrong-control-grammar persistence time | steps after falsifying evidence until correct grammar switch | h_exec, hidden_control_grammar, evidence | 핵심 failure | 줄지 않으면 problem claim 약함 |
| METRIC-04-005 | action-interface switch delay | t(rewrite) - t(evidence) | rewritten_action, evidence | rewrite timing | 느리면 rewrite 약함 |
| METRIC-04-006 | recovery delay | t(progress>0) - t(failure) | progress_delta, evidence | recovery speed | verifier와 같으면 novelty 약함 |
| METRIC-04-007 | evidence-to-hypothesis-update delay | t(hypothesis_updated) - t(evidence) | hypothesis_updated | belief update | update만 하고 action 안 바꿀 수 있음 |
| METRIC-04-008 | alternative grammar adoption rate | correct alt selected / needed alt | selected_alternative, correct_alt | proposer quality | alt rollout 약함 |
| METRIC-04-009 | falsification precision/recall | TP/FP/FN of wrong-current detection | score, h_exec, true grammar | falsification scorer | calibration 실패 |
| METRIC-04-010 | grammar-conditioned progress delta | E[Δprogress|correct grammar] - E[Δprogress|wrong grammar] | selected grammar, progress | grammar usefulness | progress와 grammar 무관 |
| METRIC-04-011 | compute-to-recovery efficiency | positive progress after failure / compute cost | progress, compute_cost | compute value | always-plan과 차이 약함 |
| METRIC-04-012 | false planning call rate | plan called but action/progress unchanged | planning_call, action_switch, progress | overplanning | gate가 uncertainty와 같음 |
| METRIC-04-013 | missed planning opportunity rate | no planning when alt would improve progress | oracle alt, plan flag | underplanning | compute penalty 과도 |
| METRIC-04-014 | invalid switch rate | invalid switches / total switches | switch validity | reward hacking | switch reward 위험 |

---

## 12. Baseline and Light Model Suite

| Model ID | Model/Baseline | Inputs | Uses Grammar? | Uses Falsification? | Uses Alternative Rollout? | Expected Strength | Expected Weakness |
|---|---|---|---|---|---|---|---|
| BASE-RANDOM | random valid action | available_actions | NO | NO | NO | lower bound | 거의 모든 grammar shift 취약 |
| BASE-REACTIVE | reactive state-text agent | state_text, instruction | NO | NO | NO | explicit cue에 강함 | history/evidence 사용 약함 |
| BASE-RETRY | retry-after-failure agent | previous_action, state_text | NO | PARTIAL | NO | transient failure에 강함 | wrong grammar loop 악화 |
| BASE-VERIFIER | verifier-only | expected/observed effect | NO | PARTIAL | NO | VeriGUI-style 강 baseline | posterior/grammar rewrite 없음 |
| BASE-UNCERTAINTY | uncertainty-gated planner | uncertainty score | NO | NO/PARTIAL | PARTIAL | ambiguous case에 planning | decision relevance 아님 |
| BASE-NEXTSTATE-WM | next-state-WM-only | state, action | NO | NO | PARTIAL | effect prediction 가능 | grammar hypothesis 없음 |
| BASE-ORACLE-GRAMMAR | oracle grammar | true grammar | YES/ORACLE | ORACLE | ORACLE | upper bound | 비현실적 |
| OURS-TEXT-FRCG | proposed text prototype | state_text, history, evidence, alt hypotheses | YES | YES | YES | 핵심 메커니즘 검증 | symbolic label 의존 |
| ABL-NO-GRAMMAR | ours without grammar | state/effect | NO | YES | PARTIAL | grammar contribution 검증 | no drop이면 core collapse |
| ABL-NO-FALSIFICATION | ours without falsification | posterior only | YES | NO | YES | falsification contribution | no drop이면 verifier/uncertainty 충분 |
| ABL-NO-ALT | ours without alternative rollout | current only | YES | YES | NO | alt rollout contribution | no drop이면 rollout claim 약함 |
| ABL-NO-REWRITE | ours without rewrite | selected alt but base action | YES | YES | YES | rewrite contribution | no drop이면 rewrite 불필요 |

---

## 13. Text-Only Algorithm Sketch

아래 pseudo-code는 최종 algorithm이 아니다. Step 04에서만 쓰는 smoke-test prototype이다.

```python
def text_frcg_step(state_text, history, candidate_actions, model, budget):
    intent = model.infer_intent(state_text, history)

    # h_exec: 직전 action을 실제로 만든 hypothesis. posterior mode와 다를 수 있음.
    current_h = model.infer_current_hypothesis(state_text, history)
    evidence = model.extract_action_effect_evidence(history)

    falsification_score = model.score_falsification(
        current_hypothesis=current_h,
        evidence=evidence
    )

    if falsification_score < model.tau_f:
        return model.select_base_action(candidate_actions)

    alternatives = model.propose_alternative_grammars(
        state_text=state_text,
        history=history,
        evidence=evidence,
        k=model.k_alt
    )

    scored = []
    for h_alt in alternatives:
        rollout = model.short_rollout(
            hypothesis=h_alt,
            candidate_actions=candidate_actions,
            horizon=model.rollout_horizon
        )
        scored.append({
            "hypothesis": h_alt,
            "expected_progress": rollout.expected_progress,
            "failure_risk": rollout.failure_risk,
            "expected_action": rollout.best_action,
            "compute_cost": rollout.compute_cost
        })

    decision = model.decision_relevant(
        current_hypothesis=current_h,
        alternatives=scored,
        compute_budget=budget
    )

    if not decision.should_plan:
        return model.select_base_action(candidate_actions)

    return model.rewrite_action(
        intent=intent,
        grammar=decision.best_hypothesis.control_grammar,
        candidate_actions=candidate_actions
    )
```

### 13.1 Algorithm Contract

| Contract ID | Contract | Why Needed | Failure If Violated |
|---|---|---|---|
| ALG-04-001 | `h_exec`는 직전 action 생성에 사용된 hypothesis여야 함 | persistence metric 기준 | posterior mode와 혼동 |
| ALG-04-002 | falsification score는 expected/observed effect mismatch 또는 likelihood ratio proxy여야 함 | verification과 구분 | failed-action flag로 축소 |
| ALG-04-003 | alternative는 grammar/regime hypothesis여야 함 | tree search와 구분 | alternative action search로 붕괴 |
| ALG-04-004 | decision relevance는 action switch 또는 progress gain이 있을 때만 true | uncertainty gate와 구분 | overplanning |
| ALG-04-005 | rewrite는 executable primitive/macro를 반환해야 함 | 구현 가능성 | 설명만 바뀌고 action은 동일 |
| ALG-04-006 | compute_cost는 모든 planning call마다 기록되어야 함 | compute-matched evaluation | always-plan 비교 불공정 |

---

## 14. Pass/Fail Gate to Step 05

수치 threshold는 실험 전 후보값이다. 최종 주장이 아니다.

| Gate ID | Pass Criterion | Required Metric | Threshold Candidate | Why Needed | If Failed |
|---|---|---|---|---|---|
| GATE-04-001 | BASE-REACTIVE 대비 failed-action repetition 감소 | METRIC-04-003 | 후보 ≥25% | 반복 실패 감소 확인 | grammar/evidence 설계 재검토 |
| GATE-04-002 | BASE-VERIFIER 대비 recovery delay 감소 | METRIC-04-006 | 후보 ≥15% | VeriGUI류와 구분 | falsification/rewrite 경로 약함 |
| GATE-04-003 | BASE-UNCERTAINTY 대비 progress per compute 향상 | METRIC-04-011 | 후보 ≥10% | decision-relevant compute 확인 | gate 재설계 |
| GATE-04-004 | BASE-NEXTSTATE-WM 대비 grammar shift 성능 향상 | METRIC-04-010 | grammar OOD에서 우위 | generic WM과 구분 | grammar claim 약화 |
| GATE-04-005 | ABL-NO-GRAMMAR 성능 하락 | METRIC-04-004/010 | persistence 증가 | control grammar 필요성 | core claim 약화/폐기 |
| GATE-04-006 | ABL-NO-FALSIFICATION 성능 하락 | METRIC-04-006/009 | recovery 지연 | falsification 필요성 | verifier-only와 유사 |
| GATE-04-007 | ABL-NO-ALT 성능 하락 | METRIC-04-008/006 | alt adoption 하락 | alternative rollout 필요성 | rollout claim 약화 |
| GATE-04-008 | ABL-NO-REWRITE 성능 하락 | METRIC-04-005/006 | switch/recovery 지연 | rewrite 필요성 | action correction claim 약화 |
| GATE-04-009 | oracle grammar와 gap 분석 가능 | upper bound gap | gap 설명 가능 | learning headroom 확인 | architecture 개선 |
| GATE-04-010 | lexical cue removal에서도 유지 | METRIC-04-008/009 | 급락 없음 | keyword shortcut 방지 | generator 재설계 |
| GATE-04-011 | reward hacking 없음 | invalid switch rate | 증가 없음 | switch reward 안전성 | reward 재설계 |
| GATE-04-012 | 최소 3개 OOD split 유지 | OOD metrics | ID 대비 과도한 급락 없음 | toy overfit 방지 | Step 05 보류 |

---

## 15. Stress Test Ledger

| Stress ID | Stress Case | What It Attacks | Expected Failure If Design Weak | Required Guardrail |
|---|---|---|---|---|
| STRESS-04-001 | lexical cue removal | keyword shortcut | 성능 급락 | paraphrase/neutral phrasing |
| STRESS-04-002 | noisy evidence | false falsification | invalid switch 증가 | threshold/calibration |
| STRESS-04-003 | delayed effect | no-effect 오판 | premature switch | delayed_effect event |
| STRESS-04-004 | spurious alternative | alt proposer robustness | wrong alt adoption | top-k ranking calibration |
| STRESS-04-005 | same symptom different cause | evidence specificity | modal/form/loading 혼동 | failure_reason taxonomy |
| STRESS-04-006 | high uncertainty same action | uncertainty gate 차별성 | overplanning | action_switch condition |
| STRESS-04-007 | low uncertainty wrong grammar | confidence failure | missed recovery | evidence likelihood ratio |
| STRESS-04-008 | large action set | scaling | random alt adoption | action family grouping |
| STRESS-04-009 | candidate missing correct macro | candidate coverage | false model failure | candidate_coverage flag |
| STRESS-04-010 | held-out grammar composition | compositional generalization | ID-only performance | OOD-composition split |
| STRESS-04-011 | switch reward hacking | reward exploit | switch spam | valid switch 4-condition rule |
| STRESS-04-012 | retry trap | BASE-RETRY threat | OURS와 retry 구분 실패 | persistent wrong-mapping cases |
| STRESS-04-013 | ambiguous intent | intent confound | grammar failure 오분류 | intent-correct subset |
| STRESS-04-014 | long prerequisite chain | horizon limit | rollout fails | horizon ablation |
| STRESS-04-015 | family imbalance | metric distortion | 특정 family만 개선 | family-balanced reporting |
| STRESS-04-016 | grammar label noise | label robustness | classifier collapse | noisy-label split |
| STRESS-04-017 | progress shortcut | reward hacking | easy progress만 반복 | terminal/subgoal consistency |
| STRESS-04-018 | no-effect shortcut | evidence overfit | no-effect=wrong always | delayed/noisy/nochange distinction |

---

## 16. What Text-Only Cannot Prove

| Limitation ID | Limitation | Why It Matters | Must Be Handled In | Risk If Ignored |
|---|---|---|---|---|
| LIMIT-04-001 | visual grounding | 위치/시각 affordance 없음 | 05/10 | VisualWebArena 공격 방어 불가 |
| LIMIT-04-002 | DOM complexity | hierarchy/dynamic node 없음 | 05/06 | schema 확장 실패 |
| LIMIT-04-003 | screenshot ambiguity | icon/color/layout 신호 없음 | 05 | visual claim 불가 |
| LIMIT-04-004 | noisy action effects | symbolic effect가 깨끗함 | 05/06 | falsification 과대평가 |
| LIMIT-04-005 | asynchronous UI | real rendering/network delay 없음 | 05 | stale/loading 일반화 실패 |
| LIMIT-04-006 | element localization | bbox/selector 문제 없음 | 05 | click failure 누락 |
| LIMIT-04-007 | real browser latency | execution API noise 없음 | 05 | action failure와 grammar failure 혼동 |
| LIMIT-04-008 | natural language ambiguity | intent를 구조화함 | 07/10 | base failure와 confound |
| LIMIT-04-009 | real-world distribution shift | synthetic symbolic space | 05/10 | toy criticism |
| LIMIT-04-010 | UI styling/layout perturbation | style/layout 없음 | 05 | robustness claim 불가 |
| LIMIT-04-011 | true VLM/LLM behavior | base agent proxy만 사용 가능 | 07/10 | 실제 candidate quality와 다름 |

---

## 17. Required Design Revisions From Text-Only Testbed

| Revision ID | Testbed Issue | Required Revision | Affected Later Step | Severity |
|---|---|---|---|---|
| REV-04-001 | grammar label shortcut 가능 | lexical cue removal/paraphrase split 추가 | 06 | HIGH |
| REV-04-002 | candidate action 부재 가능 | candidate_coverage 및 macro expansion 기록 | 07/09 | HIGH |
| REV-04-003 | verification과 차별 약함 | evidence→hypothesis→alt→rewrite trace 필드 추가 | 06/09 | CRITICAL |
| REV-04-004 | switch reward hacking | valid switch 조건 4개 고정 | 08 | CRITICAL |
| REV-04-005 | uncertainty gate와 혼동 | action_switch_prob와 ΔV 조건 추가 | 09 | HIGH |
| REV-04-006 | next-state WM과 겹침 | grammar-conditioned progress metric 필수화 | 10 | HIGH |
| REV-04-007 | delayed effect 오판 | delayed_effect/noisy/no-change event 구분 | 05/06 | HIGH |
| REV-04-008 | text-only toy risk | task family/grammar/OOD split 수량 유지 | 05 | MEDIUM |
| REV-04-009 | real proxy 부족 | weak real-world metric 설계 | 06/10 | MEDIUM |
| REV-04-010 | horizon arbitrary | horizon=1/3/5 ablation 전달 | 09/10 | MEDIUM |
| REV-04-011 | metric timestamp 모호 | evidence/update/rewrite/recovery timestamp 분리 | 06 | HIGH |
| REV-04-012 | base intent confound | intent-correct subset과 intent-error subset 분리 | 10 | HIGH |

---

## 18. Handoff to Later Steps

| Handoff ID | Target Step | What Must Be Used | What Must Be Verified | What Must Not Be Assumed |
|---|---|---|---|---|
| HANDOFF-04-001 | 05_SYNTHETIC_WEB_GUI_ENVIRONMENT.md | task family, grammar library, limitations, stress tests | symbolic schema가 DOM/action log로 확장되는지 | text-only success = Web/GUI success |
| HANDOFF-04-002 | 06_DATA_SCHEMA_AND_LABELING.md | FIELD-04-*, event_type, h_exec, reward_components | hidden label leakage 방지 | true grammar가 public observation에 있어도 된다는 가정 |
| HANDOFF-04-003 | 07_LATENT_ARCHITECTURE_DESIGN.md | current/alternative hypothesis, rewrite_target | symbolic proxy를 neural module로 전환 가능성 | latent가 이미 identifiable하다는 가정 |
| HANDOFF-04-004 | 08_LOSS_REWARD_TRAINING_OBJECTIVE.md | reward components, valid switch rule | reward hacking 방지 | recovery reward가 안전하다는 가정 |
| HANDOFF-04-005 | 09_PLANNING_THEORY_ALGORITHM.md | pseudo-code, gate, falsification score | decision-relevant compute 수식화 | uncertainty threshold와 같다는 가정 |
| HANDOFF-04-006 | 10_EVALUATION_BASELINE_ABLATION.md | baseline suite, gates, metrics | compute-matched baseline 구현 | success rate만으로 충분하다는 가정 |
| HANDOFF-04-007 | FINAL_RESEARCH_BLUEPRINT.md | pass/fail gate and limitations | text-only 결과의 논문 내 위치 | main result로 포장 금지 |

---

## 19. Implementation Readiness Contract

### 19.1 Minimal Package-Free Prototype

초기 구현은 복잡한 LLM 없이 Python standard library + dataclass로 가능해야 한다.

| Component | Minimal Implementation | Later Neural Version |
|---|---|---|
| Environment | deterministic transition function | synthetic Web/GUI simulator |
| State | dict-based hidden_state | DOM/state encoder |
| Grammar | enum + rule table | grammar head |
| Falsification | expected vs observed mismatch rule | learned falsification scorer |
| Alternative proposer | rule-based top-k from evidence type | learned top-k proposer |
| Rollout | deterministic 1~3 step symbolic simulation | learned short rollout model |
| Rewrite | rule-based macro lookup | intent-to-action rewrite head |
| Metrics | offline trace computation | unified evaluator |

### 19.2 Minimal File Layout

```text
text_smoke/
  __init__.py
  schemas.py
  grammar_library.py
  task_generator.py
  env.py
  baselines.py
  text_frcg.py
  metrics.py
  run_smoke.py
  configs/
    text_smoke_default.yaml
  outputs/
    traces/
    metrics/
```

### 19.3 Minimal Run Commands

```bash
python -m text_smoke.run_smoke \
  --config text_smoke/configs/text_smoke_default.yaml \
  --num-episodes 500 \
  --splits text_id,text_ood_grammar,text_noisy \
  --models BASE_REACTIVE,BASE_VERIFIER,BASE_UNCERTAINTY,BASE_NEXTSTATE_WM,OURS_TEXT_FRCG,ABL_NO_GRAMMAR,ABL_NO_FALSIFICATION,ABL_NO_ALT \
  --out-dir outputs/text_smoke
```

### 19.4 Minimum Output Files

| Output File | Meaning |
|---|---|
| `traces.jsonl` | episode/step-level trace |
| `metrics_by_model.csv` | model-level aggregate metrics |
| `metrics_by_split.csv` | split-level metrics |
| `ablation_summary.csv` | ablation expected drop summary |
| `failure_cases.jsonl` | qualitative failure examples |
| `leakage_audit.json` | shortcut/leakage checks |

---

## 20. Updated Risk / Unknown Ledger

| Risk ID | Risk / Unknown | Triggered By | Why It Matters | Resolution Path | Can Be Final Claim? |
|---|---|---|---|---|---|
| RISK-04-001 | text keyword shortcut | state_text may expose regime | grammar reasoning이 아님 | lexical cue removal split | NO |
| RISK-04-002 | verifier-only와 차별 실패 | BASE-VERIFIER strong | novelty 약화 | recovery delay/persistence 비교 | NO |
| RISK-04-003 | next-state-WM과 차별 실패 | BASE-NEXTSTATE-WM | generic WM으로 collapse | grammar-conditioned metrics | NO |
| RISK-04-004 | reward hacking | valid switch reward | switch spam | invalid switch metric | NO |
| RISK-04-005 | candidate action 부재 | base action set too small | rewrite 불가능 | candidate coverage audit | NO |
| RISK-04-006 | synthetic label circularity | true grammar label too clean | classifier task화 | noisy/weak label split | NO |
| RISK-04-007 | delayed effect 오판 | no-effect ambiguity | false falsification | delayed/noisy/no-change class | NO |
| RISK-04-008 | base intent confound | intent wrong | grammar failure와 혼동 | intent-correct subset | NO |
| RISK-04-009 | horizon insufficiency | long prerequisite | rollout weak | horizon sweep | NO |
| RISK-04-010 | text-to-GUI gap | abstraction too clean | Step 05 실패 가능 | mandatory Web/GUI env | NO |
| RISK-04-011 | OOD split 부족 | ID-only success | toy overfit | held-out grammar/composition | NO |
| RISK-04-012 | metric over-oracle | true grammar label needed | real benchmark 한계 | weak proxy design | NO |
| RISK-04-013 | family imbalance | e-commerce dominates | metric distortion | stratified reporting | NO |
| RISK-04-014 | no-grammar ablation not dropping | grammar not useful | core claim 붕괴 | claim weaken/drop | NO |
| RISK-04-015 | no-falsification ablation not dropping | verification enough | falsification claim 붕괴 | claim weaken/drop | NO |
| RISK-04-016 | no-alt ablation not dropping | rollout unnecessary | alternative claim 약화 | claim weaken/drop | NO |

---

## 21. Quality Gate Result

| Gate ID | Gate | PASS/FAIL/PARTIAL | Evidence | If Not PASS, Blocker |
|---|---|---|---|---|
| QG-04-01 | 00/01/02/03 refs imported | PASS | §3 Imported References | - |
| QG-04-02 | search expansion 15개 이상 | PASS | §4 15개 anchor | - |
| QG-04-03 | environment schema 30개 이상 field | PASS | §6.2 FIELD-04-001~032 | - |
| QG-04-04 | task family 10개 이상 | PASS | §7 12개 | - |
| QG-04-05 | grammar library 15개 이상 | PASS | §8 17개 | - |
| QG-04-06 | minimal test case 15개 이상 | PASS | §9 18개 | - |
| QG-04-07 | reward instrumentation | PASS | §10 8개 | - |
| QG-04-08 | metric instrumentation | PASS | §11 14개 | - |
| QG-04-09 | baseline/light model suite | PASS | §12 12개 | - |
| QG-04-10 | pass/fail gate to Step 05 | PASS | §14 12개 | - |
| QG-04-11 | text-only limitation 10개 이상 | PASS | §16 11개 | - |
| QG-04-12 | implementation readiness included | PASS | §19 | - |
| QG-04-13 | no final Web/GUI experiment claimed | PASS | frontmatter + §1 + §22 | - |
| QG-04-14 | failure/negative interpretation exists | PASS | Gate failure rules and risk ledger | - |

---

## 22. Final Statement of This File

```text
04_TEXT_ONLY_SMOKE_TESTBED.md is a smoke-test design file, not the main Web/GUI experiment.

The text-only testbed can validate:
- wrong-control-grammar hypothesis persistence가 structured symbolic action-effect log에서 계량 가능한지.
- evidence가 current hypothesis를 반증하고 alternative grammar adoption으로 이어지는지.
- action-interface rewrite가 같은 intent를 다른 executable macro로 바꾸어 recovery를 만드는지.
- decision-relevant compute가 uncertainty gate와 always-plan보다 progress-per-compute 측면에서 유리한지.
- no-grammar, no-falsification, no-alternative-rollout, no-rewrite ablation이 핵심 metric을 무너뜨리는지.

The text-only testbed cannot validate:
- visual grounding, element localization, DOM hierarchy, screenshot ambiguity.
- browser latency, asynchronous rendering, click interception, selector failure.
- WebArena/VisualWebArena/OSWorld 수준의 external validity.

The idea may proceed to Step 05 only if:
- BASE-REACTIVE, BASE-VERIFIER, BASE-UNCERTAINTY, BASE-NEXTSTATE-WM 대비 mechanism metrics가 개선된다.
- ABL-NO-GRAMMAR, ABL-NO-FALSIFICATION, ABL-NO-ALT, ABL-NO-REWRITE에서 예상 하락이 관측된다.
- lexical cue removal, noisy evidence, delayed effect, spurious alternative stress test에서 치명적 shortcut이 발견되지 않는다.
- reward hacking과 invalid switch 증가가 통제된다.

The next required file is:
05_SYNTHETIC_WEB_GUI_ENVIRONMENT.md
```
