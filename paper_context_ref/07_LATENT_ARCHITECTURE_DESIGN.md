---
file_id: STEP-07
title: Latent Variable and Architecture Design for FRCG-WM
version: v1.0
status: architecture_candidate_contract_not_final_method
language: ko
source_input:
  - 붙여넣은 마크다운(1)(81).md
  - 00_MASTER_REFERENCE.md
  - 01_RELATED_WORK_THREAT_MAP.md
  - 02_PROBLEM_NOVELTY_FALSIFICATION.md
  - 03_CORE_CONCEPT_TAXONOMY.md
  - 04_TEXT_ONLY_SMOKE_TESTBED.md
  - 05_SYNTHETIC_WEB_GUI_ENVIRONMENT.md
  - 06_DATA_SCHEMA_AND_LABELING.md
purpose:
  - FRCG-WM의 latent factorization, module architecture, inference/training/evaluation dataflow를 Claude Code가 바로 읽고 구현 가능한 수준으로 고정한다.
  - architecture가 논문 claim, data schema, hidden label, objective, planning, metric, ablation과 직접 연결되는지 검증한다.
  - z_state, z_regime, z_control_grammar, z_change_point 4-latent 후보를 무비판적으로 확정하지 않고, merged/collapsed/hierarchical/auxiliary-head 대안을 비교한다.
  - hidden label leakage, concept collapse, over-complex architecture, weak baseline 공격을 사전에 차단한다.
forbidden:
  - Do not finalize loss/reward objective.
  - Do not finalize planning algorithm.
  - Do not finalize evaluation results.
  - Do not claim architecture is empirically validated.
  - Do not use hidden labels or counterfactual labels as inference-time input.
  - Do not treat 4-latent factorization as proven.
next_files:
  - 08_LOSS_REWARD_TRAINING_OBJECTIVE.md
  - 09_PLANNING_THEORY_ALGORITHM.md
  - 10_EVALUATION_BASELINE_ABLATION.md
---

# 07_LATENT_ARCHITECTURE_DESIGN.md

## 1. 파일 목적

이 파일은 최종 논문 method section이 아니다. 이 파일은 FRCG-WM의 **architecture candidate contract**다. 목적은 “그럴듯한 블록 다이어그램”을 만드는 것이 아니라, 각 latent/module이 실제 데이터 필드, hidden supervision, objective, planning component, metric, ablation과 연결되는지를 고정하는 것이다.

핵심 원칙은 다음이다.

1. `z_state`, `z_regime`, `z_control_grammar`, `z_change_point`는 현재 가장 강한 후보지만 최종 확정이 아니다.
2. `z_regime`과 `z_control_grammar`는 반드시 분리 가능한 데이터 조건과 ablation을 가져야 한다.
3. hidden labels는 training/evaluation supervision에는 쓰일 수 있으나 inference input으로는 절대 들어가면 안 된다.
4. counterfactual labels는 rollout target/evaluation에는 쓰일 수 있으나 agent observation에는 절대 포함하지 않는다.
5. collapsed latent, merged regime-control grammar, hierarchical latent, auxiliary-head 구조가 더 강할 가능성을 숨기지 않는다.
6. architecture는 minimal viable experiment로 구현 가능해야 하며, full multimodal architecture만 제시하면 안 된다.
7. no-control-grammar, no-falsification, no-alternative-rollout, no-compute-gate ablation이 성능을 떨어뜨리지 않으면 관련 claim은 약화 또는 폐기한다.

---

## 2. Claude Code Context Routing

| 작업 의도 | 먼저 읽을 파일 | 이어서 읽을 파일 | 절대 가정하지 말 것 |
|---|---|---|---|
| architecture 전체 수정 | `07_LATENT_ARCHITECTURE_DESIGN.md` | `03`, `06`, `08`, `09`, `10` | 4-latent가 최종 확정이라고 가정 금지 |
| latent 추가/삭제 | `07 §5~6`, `03 §8` | `06 §8`, `10 §8` | 새 latent가 primary로 필요한지 검증 없이 추가 금지 |
| `z_control_grammar` 구현 | `03_CORE_CONCEPT_TAXONOMY.md` | `06`, `07 §5/8/12`, `09`, `10` | grammar를 action precondition 하나로 축소 금지 |
| module I/O 구현 | `07 §8`, `06_DATA_SCHEMA_AND_LABELING.md` | `08`, `09` | 없는 schema field를 input으로 요구 금지 |
| inference path 구현 | `07 §9`, `09_PLANNING_THEORY_ALGORITHM.md` | `06` | hidden label/counterfactual label을 inference input으로 사용 금지 |
| objective 설계 | `08_LOSS_REWARD_TRAINING_OBJECTIVE.md` | `07 §13`, `06 §8~11` | loss 이름만 만들고 trained module을 비워두기 금지 |
| evaluation/ablation 설계 | `10_EVALUATION_BASELINE_ABLATION.md` | `07 §14~17`, `08`, `09` | success rate만으로 architecture claim 검증 금지 |
| minimal 구현 시작 | `07 §15`, `04`, `05`, `06` | `08`, `09` | full multimodal 구조부터 구현 금지 |

---

## 3. Citation-Grade Source Anchors

> 아래 anchor는 architecture 설계의 외부 위협/배경이다. 논문 본문에서는 Step 01/10에서 citation table로 재정리해야 한다.

| Source ID | Anchor | URL | Architecture Implication | Threat Level |
|---|---|---|---|---|
| SRC-ARCH-001 | PlaNet / latent dynamics planning | https://arxiv.org/abs/1811.04551 | latent world model + planning은 오래된 강한 baseline이다. FRCG-WM은 generic latent planning이 아니라 grammar falsification으로 좁혀야 한다. | HIGH |
| SRC-ARCH-002 | Dreamer / RSSM | https://arxiv.org/abs/1912.01603 | recurrent latent state-space model 설계의 대표 anchor. `history_encoder → latent posterior` 설계에 참고하되, GUI grammar claim과 혼동 금지. | MEDIUM |
| SRC-ARCH-003 | DreamerV3 | https://arxiv.org/abs/2301.04104 | general world model scaling threat. FRCG-WM은 stronger generic WM과 비교해야 한다. | MEDIUM |
| SRC-ARCH-004 | TD-MPC | https://arxiv.org/abs/2203.04955 | latent MPC와 compute-matched planning baseline 위협. | HIGH |
| SRC-ARCH-005 | Locatello et al. disentanglement impossibility | https://arxiv.org/abs/1811.12359 | unsupervised factorization은 보장되지 않는다. 4-latent는 supervision/inductive bias/ablation이 필요하다. | CRITICAL |
| SRC-ARCH-006 | WebWorld | https://arxiv.org/abs/2602.14721 | large-scale web world model + inference-time search가 직접 threat. generic web world model claim 금지. | CRITICAL |
| SRC-ARCH-007 | CUWM | https://arxiv.org/abs/2602.17365 | frozen agent + world model + candidate action search가 직접 threat. FRCG-WM은 control-grammar hypothesis와 persistence metric으로 차별화해야 한다. | CRITICAL |
| SRC-ARCH-008 | WAC | https://arxiv.org/abs/2602.15384 | consequence simulation + action correction이 직접 threat. rewrite module은 grammar-hypothesis 기반이어야 한다. | CRITICAL |
| SRC-ARCH-009 | VeriGUI | https://arxiv.org/abs/2604.05477 | action-effect verification/self-correction이 직접 threat. FRCG-WM은 verification이 아니라 falsification→alternative hypothesis→rewrite 경로를 보여야 한다. | CRITICAL |
| SRC-ARCH-010 | BrowserGym | https://arxiv.org/abs/2412.05467 | browser agent observation/action/evaluation ecosystem anchor. interface/schema 설계 참고. | MEDIUM |

---

## 4. Architecture Thesis and Design Constraints

| Constraint ID | Constraint | 이유 | 위반 설계 | Guardrail |
|---|---|---|---|---|
| ARCH-CONSTRAINT-001 | Frozen Base VLM/LLM은 고정한다 | “LLM이 좋아서 된 것” 공격 방어 | base model을 fine-tune하고 proposed module도 변경 | base checkpoint, tokenizer, prompt, candidate budget 고정 |
| ARCH-CONSTRAINT-002 | hidden label은 inference input 금지 | label leakage 발생 시 모든 실험 무효 | `true_regime`, `true_control_grammar`를 prompt/context에 주입 | `build_agent_observation()` forbidden-key assert |
| ARCH-CONSTRAINT-003 | counterfactual label은 inference input 금지 | oracle alternative effect가 새면 rollout claim 무효 | `counterfactual_action_effects`를 model input에 포함 | counterfactual shard 분리, loader-level denylist |
| ARCH-CONSTRAINT-004 | 4-latent는 candidate일 뿐이다 | 식별성/중복 가능성 큼 | 4-latent를 empirical validation 없이 final로 선언 | collapsed/merged/hierarchical/aux-head variant 비교 |
| ARCH-CONSTRAINT-005 | regime과 control grammar는 crossed condition으로 분리 가능해야 한다 | 핵심 novelty가 factorization에 의존 | task family와 grammar가 1:1 대응 | same regime/different grammar, same grammar/different regime split 생성 |
| ARCH-CONSTRAINT-006 | current hypothesis는 executed hypothesis로 정의한다 | persistence metric 안정화 | posterior mode를 current로 대체 | `h_exec` logger 필수 |
| ARCH-CONSTRAINT-007 | falsification은 no-effect flag가 아니다 | VeriGUI와 차별화 | action failed → falsification으로 단순 처리 | evidence likelihood / likelihood-ratio / posterior drop candidate 비교 |
| ARCH-CONSTRAINT-008 | alternative는 action이 아니라 hypothesis다 | WAC/CUWM/action search와 차별화 | top-k actions만 비교 | top-k regime/control-grammar hypothesis record 사용 |
| ARCH-CONSTRAINT-009 | rollout은 short-horizon 중심이다 | long rollout compounding error/compute 폭발 | H=10+ full tree search | H=1/3/5 ablation, rollout-step logging |
| ARCH-CONSTRAINT-010 | decision gate는 uncertainty threshold가 아니다 | uncertainty-gated baseline과 구분 | confidence 낮으면 plan | falsification score + ΔV + action_switch_prob + compute_cost |
| ARCH-CONSTRAINT-011 | auxiliary head는 primary latent를 대체하면 안 된다 | grammar novelty가 precondition/blocker로 붕괴 가능 | aux-head-only가 full과 동일 | aux-only, no-grammar+aux ablation |
| ARCH-CONSTRAINT-012 | module I/O는 Step 06 schema에 존재해야 한다 | 구현 가능성 | 존재하지 않는 label/field 요구 | Module-to-data map에서 exact field name 사용 |
| ARCH-CONSTRAINT-013 | architecture는 compute-matched baseline과 비교 가능해야 한다 | planning gain fairness | ours만 더 많은 rollout 사용 | planning_calls, rollout_steps, wall-clock proxy logging |
| ARCH-CONSTRAINT-014 | minimal viable architecture가 있어야 한다 | full multimodal 구조는 구현 리스크 큼 | DOM+screenshot+log full만 제시 | text-only → DOM+log → DOM+screenshot+log 단계화 |
| ARCH-CONSTRAINT-015 | every module must have a collapse rule | module decoration 방지 | module 제거해도 claim 해석 없음 | “if ablation does not hurt” column 필수 |

---

## 5. Semantic Reference Repair: Placeholder REF 제거

원본 초안의 `DATA-LABEL-001 = architecture supervision/evaluation label 1` 같은 항목은 Claude Code context로 부적합하다. 이 파일에서는 모두 실제 semantic field로 치환한다.

| Old Placeholder | Correct Semantic REF | Exact Field / Meaning | Used By |
|---|---|---|---|
| DATA-LABEL-001 | DATA-LABEL-true_hidden_state | `true_hidden_state` | `z_state`, state head |
| DATA-LABEL-002 | DATA-LABEL-true_regime | `true_regime` | `z_regime`, `L_regime` |
| DATA-LABEL-003 | DATA-LABEL-true_control_grammar | `true_control_grammar` | `z_control_grammar`, `L_control_grammar` |
| DATA-LABEL-004 | DATA-LABEL-true_change_point | `true_change_point` | `z_change_point`, change-point head |
| DATA-LABEL-005 | DATA-LABEL-true_event_type | `true_event_type` | event/reveal-shift head |
| DATA-LABEL-006 | DATA-LABEL-true_reveal_vs_shift | `true_reveal_vs_shift` | reveal-vs-shift classifier |
| DATA-LABEL-007 | DATA-LABEL-true_action_precondition_satisfied | `true_action_precondition_satisfied` | precondition auxiliary head |
| DATA-LABEL-008 | DATA-LABEL-true_action_effect_type | `true_action_effect_type` | action-effect head |
| DATA-LABEL-009 | DATA-LABEL-true_failed_action | `true_failed_action` | failure-risk head |
| DATA-LABEL-010 | DATA-LABEL-true_failure_reason | `true_failure_reason` | failure-mode head, qualitative analysis |
| DATA-LABEL-011 | DATA-LABEL-true_recovery_action | `true_recovery_action` | recovery ranking/rewrite target |
| DATA-LABEL-012 | DATA-LABEL-true_progress_delta | `true_progress_delta` | progress head, reward predictor |
| DATA-LABEL-013 | DATA-LABEL-true_subgoal_state | `true_subgoal_state` | goal progress / task phase head |
| DATA-LABEL-014 | DATA-LABEL-true_task_success | `true_task_success` | final evaluation only |
| DATA-LABEL-015 | DATA-LABEL-true_wrong_hypothesis | `true_wrong_hypothesis` | falsification supervision |
| DATA-LABEL-016 | DATA-LABEL-true_valid_hypothesis_switch | `true_valid_hypothesis_switch` | switch reward / switch classifier |
| DATA-LABEL-017 | DATA-LABEL-true_invalid_hypothesis_switch | `true_invalid_hypothesis_switch` | invalid switch penalty |
| DATA-COUNTERFACTUAL-001 | DATA-CF-counterfactual_action_effects | `counterfactual_action_effects` | rollout fidelity target |
| DATA-COUNTERFACTUAL-002 | DATA-CF-counterfactual_progress_delta | `counterfactual_progress_delta` | value/progress rollout target |
| DATA-COUNTERFACTUAL-003 | DATA-CF-counterfactual_best_alternative | `counterfactual_best_alternative` | oracle alt evaluation only |

---

## 6. Latent Candidate Analysis

| Latent ID | Candidate | 의미 | Required Label | Connected Loss Candidate | Connected Metric | Possible Overlap | Identifiability Risk | Decision Candidate |
|---|---|---|---|---|---|---|---|---|
| LATENT-07-001 | `z_state` | hidden UI/task state belief. 예: modal_active, filter_panel_open, cart_count, current page | `true_hidden_state`, `true_subgoal_state` | `L_state`, `L_action_effect`, `L_progress` 후보 | state prediction, normalized return | `z_goal_progress`, `z_blocker`, `z_regime` | 높음. 모든 변수를 흡수하는 “garbage latent” 위험 | `PRIMARY_LATENT_CANDIDATE` |
| LATENT-07-002 | `z_regime` | 현재 interaction mode. 예: modal_blocked, loading_stale, responsive_menu, confirmation_required | `true_regime` | `L_regime` | wrong-regime persistence, OOD-regime recombination | `z_control_grammar`, `z_blocker` | 매우 높음. grammar와 1:1이면 무의미 | `PRIMARY_LATENT_CONTESTED` |
| LATENT-07-003 | `z_control_grammar` | intent를 executable action/macro/precondition/effect schema로 변환하는 latent rule | `true_control_grammar`, `true_action_precondition_satisfied`, `true_action_effect_type` | `L_control_grammar`, `L_intent_action_mapping` | wrong-control-grammar persistence, switch delay | precondition/effect schema, regime | 매우 높음. 단순 precondition classifier로 축소될 위험 | `PRIMARY_LATENT_CRITICAL` |
| LATENT-07-004 | `z_change_point` | no-change/reveal/shift/failed/delayed/noisy event belief | `true_change_point`, `true_event_type`, `true_reveal_vs_shift` | `L_change_point`, `L_reveal_shift` | change-point F1, reveal-vs-shift accuracy | visual diff detector, failure mode | 중간~높음. delayed/noisy effect와 혼동 | `PRIMARY_LATENT_CANDIDATE` |
| LATENT-07-005 | `z_goal_progress` | subgoal/task progress belief | `true_progress_delta`, `true_subgoal_state` | `L_progress` | progress per compute, normalized return | `z_state` | 높음. reward head로 충분할 수 있음 | `AUXILIARY_HEAD` |
| LATENT-07-006 | `z_action_precondition` | action precondition satisfaction belief | `true_action_precondition_satisfied` | `L_precondition` | failed-action prediction | `z_control_grammar` | 높음. grammar novelty를 잠식 | `AUXILIARY_HEAD_ONLY` |
| LATENT-07-007 | `z_affordance` | visible/enabled/clickable/scrollable affordance belief | public affordance labels, `target_visible`, `target_enabled` | `L_affordance` | failed-action repetition | observation encoder | 중간. DOM feature로 직접 계산 가능 | `AUXILIARY_HEAD_ONLY` |
| LATENT-07-008 | `z_blocker` | modal/overlay/permission/loading blocker belief | `true_failure_reason`, blocker flags | `L_blocker` | recovery delay | `z_regime` | 높음. modal_blocked regime과 중복 | `AUXILIARY_HEAD_OR_MERGE_WITH_REGIME` |
| LATENT-07-009 | `z_uncertainty` | posterior/rollout confidence uncertainty | calibration target, `effect_match_score` | `L_calibration`, `L_uncertainty` | false planning call rate, calibration ECE | decision gate scalar | 중간. latent보다 score가 적절할 수 있음 | `AUXILIARY_SCORE_ONLY` |
| LATENT-07-010 | `z_user_intent` | instruction/history에서 추론된 user intent | base intent trace, optional intent label | `L_intent` optional | intent-conditioned recovery | Frozen Base output | 높음. base LLM 역할 침범 | `INPUT_FEATURE_NOT_PRIMARY_LATENT` |
| LATENT-07-011 | `z_task_phase` | multi-step workflow phase. 예: search/filter/detail/checkout | `true_subgoal_state`, task phase labels | `L_phase` optional | long-horizon composition | `z_state`, `z_goal_progress` | 중간 | `AUXILIARY_HEAD` |
| LATENT-07-012 | `z_failure_mode` | failure type belief. 예: no_effect, delayed_effect, blocked, invalid_target | `true_failure_reason`, `true_failed_action` | `L_failed_action` | failure diagnosis accuracy | `z_change_point` | 중간 | `AUXILIARY_HEAD` |
| LATENT-07-013 | `z_interaction_protocol` | regime+grammar composite protocol | `true_regime` + `true_control_grammar` composite | `L_protocol` optional | OOD grammar recombination | merged regime-grammar | 높음. merged structure가 될 위험 | `ABLATION_ONLY` |
| LATENT-07-014 | `z_temporal_stability` | UI effect/state가 안정화됐는지 belief | `delayed_effect_flag`, `loading/stale` labels | `L_temporal_stability` | false falsification in async split | `z_change_point`, loading regime | 중간~높음 | `AUXILIARY_HEAD` |

### Latent survival rule

```text
If z_control_grammar does not improve wrong-control-grammar persistence, recovery delay, or OOD-control-grammar shift metrics over merged/collapsed variants, it must not be claimed as a necessary primary latent.
```

---

## 7. Latent Factorization Variant Comparison

| Variant ID | Latent Structure | Pros | Cons | Supports | Weakens | Trainability | Ablation Clarity | Final Recommendation |
|---|---|---|---|---|---|---|---|---|
| ARCH-07-001 | 4-latent: `z_state`, `z_regime`, `z_control_grammar`, `z_change_point` | taxonomy와 직접 정렬. ablation 명확. 논문 claim과 잘 연결 | supervision 많음. identifiability risk 큼 | factorization, persistence, reveal/shift | simplicity | 중간 | 높음 | `MAIN_CANDIDATE` |
| ARCH-07-002 | 4-latent + auxiliary heads | primary latents는 유지하고 precondition/progress/blocker/affordance는 보조 | aux heads가 primary latent를 대체할 위험 | main claim 대부분, trainability | 순수 factorization | 중간~높음 | 높음 | `BEST_MAIN_CANDIDATE` |
| ARCH-07-003 | 5-latent-progress | progress/value prediction 강화 | `z_state`와 중복, reward shaping 과적합 | progress per compute | clean latent story | 중간 | 중간 | `ABLATION_ONLY` |
| ARCH-07-004 | 5-latent-blocker | modal/permission/loading recovery 강화 | regime과 중복, toy shortcut 위험 | blocker recovery | regime/grammar separation | 중간 | 중간 | `ABLATION_ONLY` |
| ARCH-07-005 | collapsed latent `z_all` | 구현 단순, 강한 성능 가능 | novelty 해석 거의 불가 | practical performance baseline | factorization claim | 높음 | 낮음 | `STRONG_BASELINE_NOT_MAIN` |
| ARCH-07-006 | merged regime-control grammar | regime/grammar ambiguity 완화, 구현 쉬움 | 핵심 분리 claim 약화 | generic interaction protocol | control grammar novelty | 높음 | 중간 | `CRITICAL_ABLATION` |
| ARCH-07-007 | hierarchical: `z_state → z_regime → z_control_grammar → z_change_point` | causal story 강함 | 오류 전파, 학습 불안정 | belief hierarchy | robust training | 낮음~중간 | 중간 | `APPENDIX_OR_UNKNOWN` |
| ARCH-07-008 | no-explicit-latent direct predictor | 구현 쉬움, strong supervised baseline | problem novelty 설명 불가 | practical baseline | latent novelty | 높음 | 높음 | `BASELINE_ONLY` |

---

## 8. Main Architecture Candidate

현재 가장 강한 후보는 **`ARCH-07-002: 4-latent + auxiliary heads`**다.

```text
Frozen Base VLM/LLM Agent
  └─ input: public observation only
  └─ output: intent + candidate actions

Public Observation Builder
  └─ DOM / screenshot_ref or frozen visual feature / accessibility tree / previous action / public observed effect
  └─ forbidden: true_regime, true_control_grammar, true_change_point, counterfactual labels

FRCG-WM Candidate
  ├─ DOM Encoder
  ├─ Screenshot/Frozen VLM Feature Encoder
  ├─ Accessibility Tree Encoder
  ├─ Structured Action-Effect Encoder
  ├─ History Encoder
  ├─ Candidate Action Encoder
  ├─ Latent Posterior Module
  │    └─ q(z_state, z_regime, z_control_grammar, z_change_point | H_t, x_t)
  ├─ Primary Heads
  │    ├─ State Inference Head
  │    ├─ Regime Inference Head
  │    ├─ Control-Grammar Inference Head
  │    └─ Change-Point/Event Head
  ├─ Auxiliary Heads
  │    ├─ Progress Head
  │    ├─ Precondition Head
  │    ├─ Affordance/Blocker Head
  │    ├─ Failure-Risk Head
  │    └─ Calibration Head
  ├─ Current Hypothesis Scorer
  ├─ Falsification Scorer
  ├─ Alternative Hypothesis Proposer
  ├─ Short-Horizon Rollout Model
  ├─ Decision-Relevance Gate
  ├─ Intent-to-Action Rewrite Module
  ├─ Final Action Selector
  └─ Trace/Belief Logger
```

```text
This is a main candidate architecture, not an empirically validated final method.
```

---

## 9. Module Contract Table

| Module ID | Module | Input | Output | Uses Hidden Label During Training? | Used At Inference? | Connected Loss Candidate | Connected Metric | Required Ablation |
|---|---|---|---|---|---|---|---|---|
| MOD-07-001 | Frozen Base VLM/LLM Agent | public observation, instruction, history | intent, candidate_actions | NO | YES | none | base success, candidate recall | base-only |
| MOD-07-002 | Public Observation Builder | raw step record | sanitized observation | NO | YES | none | leakage audit pass | sanitize off audit only |
| MOD-07-003 | DOM Encoder | `dom_tree_sanitized`, bbox, enabled/clickable | `dom_feature` | NO | YES | optional effect/target loss | DOM-only performance | no-DOM |
| MOD-07-004 | Screenshot/Frozen Visual Encoder | `screenshot_ref_public` or frozen visual embedding | `visual_feature` | NO | optional | optional modality loss | visual/layout OOD | no-screenshot |
| MOD-07-005 | Accessibility Encoder | `accessibility_tree_sanitized` | `a11y_feature` | NO | YES | optional semantic effect loss | AX robustness | no-a11y |
| MOD-07-006 | Structured Action-Effect Encoder | previous action, DOM diff, visual diff, public effect summary | `effect_feature` | NO | YES | `L_action_effect` | falsification P/R | no-effect-encoder |
| MOD-07-007 | History Encoder | previous obs/action/effect/features | `h_t` | NO | YES | temporal consistency optional | persistence/switch delay | no-history |
| MOD-07-008 | Intent Encoder | base intent, instruction, history | `intent_feature` | optional | YES | `L_intent` optional | intent-conditioned recovery | no-intent |
| MOD-07-009 | Candidate Action Encoder | candidate action list, target public attrs | action embeddings | NO | YES | `L_mapping` optional | action switch accuracy | no-action-encoder |
| MOD-07-010 | Latent Posterior Module | `h_t`, obs/effect/action features | posterior over 4 latents | YES | YES, posterior only | `L_state`, `L_regime`, `L_control_grammar`, `L_change_point` | latent probes | collapsed-latent |
| MOD-07-011 | State Inference Head | latent posterior, history | state belief | YES | YES | `L_state`, `L_action_effect` | state/progress prediction | no-state |
| MOD-07-012 | Regime Inference Head | latent posterior | regime distribution | YES | YES | `L_regime` | wrong-regime persistence | no-regime |
| MOD-07-013 | Control-Grammar Inference Head | latent posterior, intent feature | grammar distribution | YES | YES | `L_control_grammar`, `L_intent_action_mapping` | grammar persistence, switch delay | no-control-grammar |
| MOD-07-014 | Change-Point/Event Head | effect feature, history | event/change posterior | YES | YES | `L_change_point`, `L_reveal_shift` | change-point F1, reveal-vs-shift acc | no-change-point |
| MOD-07-015 | Progress Head | latent, action, hypothesis | predicted progress delta | YES | YES | `L_progress` | progress per compute | no-progress-head |
| MOD-07-016 | Precondition Head | latent, action target | precondition probability | YES | YES | `L_precondition` | failed-action prediction | no-precondition-head |
| MOD-07-017 | Affordance/Blocker Head | DOM/a11y/visual features | affordance/blocker scores | YES | YES | `L_affordance`, `L_blocker` | recovery delay | no-affordance-blocker |
| MOD-07-018 | Current Hypothesis Scorer | `h_exec`, evidence, posterior | likelihood/score of current | YES target | YES | `L_current_alt_ranking`, `L_falsification` | falsification P/R | no-current-scorer |
| MOD-07-019 | Falsification Scorer | current score, alternative scores, evidence | `F_t` | YES | YES | `L_falsification`, calibration | false/missed planning rate | no-falsification |
| MOD-07-020 | Alternative Hypothesis Proposer | posterior, evidence, history | top-k alternative hypotheses | optional | YES | `L_current_alt_ranking` | alt recall/adoption | no-alternative-hypothesis |
| MOD-07-021 | Short-Horizon Rollout Model | hypothesis, action, state belief | predicted effect/progress/failure | YES, incl. counterfactual targets | YES | `L_action_effect`, `L_progress`, `L_counterfactual_rollout` | rollout fidelity | no-rollout |
| MOD-07-022 | Progress/Reward Predictor | rollout outputs, latent | expected value proxy | YES | YES | `L_progress`, reward prediction | compute-matched return | no-reward-predictor |
| MOD-07-023 | Failure-Risk Predictor | latent, action, effect history | failure probability/reason | YES | YES | `L_failed_action` | failed repetition | no-failure-risk |
| MOD-07-024 | Decision-Relevance Gate | `F_t`, ΔV, action-switch prob, compute cost | plan/no-plan | NO direct hidden input | YES | gate calibration optional | progress per compute, false planning calls | no-compute-gate / always-plan |
| MOD-07-025 | Intent-to-Action Rewrite Module | intent, selected grammar, candidates, preconditions | rewritten action/macro | YES mapping/recovery label | YES | `L_intent_action_mapping`, `L_recovery_ranking` | action-interface switch delay | no-rewrite |
| MOD-07-026 | Final Action Selector | base action, rewritten action, scores | final executed action | NO | YES | ranking/policy optional | success, return | selector ablation |
| MOD-07-027 | Trace/Belief Logger | posterior, selected hypothesis, action, scores | `h_exec`, trace records | NO | YES logging | none | all mechanism metrics | no-logger is invalid |

---

## 10. Inference-Time Dataflow

| Flow ID | Stage | Input | Operation | Output | Possible Failure | Guardrail |
|---|---|---|---|---|---|---|
| INFLOW-07-001 | public observation extraction | raw step record | apply visibility contract | safe observation | hidden label leakage | forbidden-key assert |
| INFLOW-07-002 | base candidate generation | safe observation, instruction | frozen base model inference | intent, candidate actions | recovery action absent | candidate recall metric |
| INFLOW-07-003 | multimodal/structured encoding | DOM/a11y/screenshot/effect/history | encode features | feature bundle | shortcut feature | modality ablation |
| INFLOW-07-004 | latent posterior inference | feature bundle, history | infer posterior | q(z) | latent collapse | probes/ablation |
| INFLOW-07-005 | current hypothesis extraction | previous selected hypothesis/action | read `h_exec` | current hypothesis | posterior/current mismatch | trace logger |
| INFLOW-07-006 | evidence scoring | previous action/effect | compute evidence feature | evidence embedding | noisy/delayed effect | delayed/noisy heads |
| INFLOW-07-007 | falsification scoring | current hypothesis, evidence | estimate `F_t` | falsification score | no-effect shortcut | calibration + noise split |
| INFLOW-07-008 | alternative proposal | posterior, evidence | propose top-k hypothesis | alternative set | true alt missing | top-k recall metric |
| INFLOW-07-009 | short rollout | current/alternative hypotheses, actions | predict effect/progress/failure | rollout scores | compounding error | horizon sweep |
| INFLOW-07-010 | decision gate | `F_t`, ΔV, action-switch prob, compute cost | decide plan/rewrite | gate decision | over/under-planning | compute-matched metrics |
| INFLOW-07-011 | action rewrite | intent, selected grammar, candidates | rewrite action/macro | executable action | invalid macro | precondition check |
| INFLOW-07-012 | final selection/logging | base action, rewritten action, scores | select and log | final action + trace | selector confound | no-rewrite/no-gate ablation |

---

## 11. Training-Time Dataflow

| Flow ID | Stage | Input | Operation | Output | Failure Mode | Guardrail |
|---|---|---|---|---|---|---|
| TFLOW-07-001 | load trajectory | storage episode JSON | parse records | raw batch | schema drift | schema_version assert |
| TFLOW-07-002 | build safe input | raw step record | `build_agent_observation()` | public input batch | hidden label leakage | denylist assert |
| TFLOW-07-003 | build supervision targets | hidden label records | select targets | label tensors | target/input mixing | separate dataclass/shard |
| TFLOW-07-004 | encode features | public input | run encoders | feature tensors | shortcut learning | audit probes |
| TFLOW-07-005 | train latent heads | features + labels | supervised/multitask losses | posterior/head outputs | concept collapse | variant ablation |
| TFLOW-07-006 | train effect/progress heads | action-effect records | effect/progress losses | predictors | DOM diff overfit | semantic progress split |
| TFLOW-07-007 | train falsification/ranking | executed hypothesis + labels | ranking/calibration loss | `F_t` | circular target | held-out calibration |
| TFLOW-07-008 | train rollout model | counterfactual shard | effect/progress/failure targets | rollout predictor | synthetic-only overfit | no-counterfactual ablation |
| TFLOW-07-009 | train rewrite head | recovery/mapping labels | mapping/ranking loss | rewrite policy | oracle macro leakage | candidate-constrained labels |
| TFLOW-07-010 | calibration validation | validation split | reliability metrics | calibration report | overconfident gate | ECE/Brier |
| TFLOW-07-011 | leakage audit | trained model + metadata | shortcut probes | audit report | hidden shortcut | fail-fast gate |
| TFLOW-07-012 | checkpoint export | model + schema versions | save artifacts | checkpoint package | non-reproducible | hash/manifest |

---

## 12. Evaluation-Time Dataflow

| Flow ID | Stage | Input | Operation | Output | Failure Mode | Guardrail |
|---|---|---|---|---|---|---|
| EFLOW-07-001 | freeze checkpoints | base + module checkpoints | lock versions | eval config | unfair comparison | same base/same seed |
| EFLOW-07-002 | run public observation only | environment trace | execute agent | action trace | label leakage | runtime input audit |
| EFLOW-07-003 | record compute | planning calls, rollout steps | log budget | compute trace | unfair planning | compute-matched protocol |
| EFLOW-07-004 | compute hidden-label metrics offline | executed trace + labels | calculate metrics | persistence/recovery metrics | metric leakage into agent | offline-only computation |
| EFLOW-07-005 | compute rollout fidelity offline | predicted rollouts + counterfactuals | compare | fidelity metrics | counterfactual leakage | offline-only shard |
| EFLOW-07-006 | run ablations | variant configs | evaluate variants | ablation deltas | non-isolated ablation | one-change-at-a-time |
| EFLOW-07-007 | run baselines | baseline configs | evaluate | baseline table | weak baseline | threat baselines required |
| EFLOW-07-008 | failure analysis | traces + metrics | classify failures | qualitative cases | cherry-picking | predeclared case types |

---

## 13. Module-to-Data Schema Map

| Module | Required Public Input Fields | Required Training Labels | Counterfactual Fields | Output Fields | Leakage Risk |
|---|---|---|---|---|---|
| Public Observation Builder | raw record | none | none | sanitized observation | hidden key leak |
| DOM Encoder | `dom_tree_sanitized`, bbox, public attrs | none | none | `dom_feature` | class/id shortcut |
| Screenshot Encoder | `screenshot_ref_public` | none | none | `visual_feature` | filename/template shortcut |
| Accessibility Encoder | `accessibility_tree_sanitized` | none | none | `a11y_feature` | aria label leakage |
| Action-Effect Encoder | previous action, public observed effect, public diffs | `true_action_effect_type` for training | none | `effect_feature` | hidden failure reason leak |
| History Encoder | prior safe observations/actions/effects | none | none | `h_t` | hidden labels in history |
| Latent Posterior Module | `h_t`, features | `true_hidden_state`, `true_regime`, `true_control_grammar`, `true_change_point` | none | latent posterior | label leakage if target in input |
| Regime Head | latent posterior | `true_regime` | none | regime posterior | regime class leakage |
| Control-Grammar Head | latent posterior, intent | `true_control_grammar` | none | grammar posterior | grammar text shortcut |
| Change-Point/Event Head | effect/history feature | `true_change_point`, `true_event_type`, `true_reveal_vs_shift` | none | event posterior | delayed/noisy confusion |
| Progress Head | latent/action | `true_progress_delta`, `true_subgoal_state` | optional cf progress | predicted progress | reward leakage |
| Precondition Head | latent/action target | `true_action_precondition_satisfied` | none | precondition prob | precondition label leak |
| Falsification Scorer | evidence/current hypothesis | `true_wrong_hypothesis`, `effect_match_score` | optional alt evidence | `F_t` | circular scoring |
| Alternative Proposer | posterior/evidence/history | optional `true_valid_hypothesis_switch` | `counterfactual_best_alternative` for training only | top-k hypotheses | oracle alternative leak |
| Rollout Model | hypothesis/action/state belief | `true_action_effect_type`, `true_progress_delta` | `counterfactual_action_effects`, `counterfactual_progress_delta` | predicted effects/progress | counterfactual in obs |
| Decision Gate | `F_t`, ΔV, action-switch probability, compute cost | optional gate targets | none | plan/no-plan | hidden reward leak |
| Rewrite Module | intent, selected grammar, candidate actions | `true_recovery_action`, `true_valid_hypothesis_switch` | oracle grammar action eval-only | rewritten action | oracle action leak |
| Final Selector | base/rewrite action + scores | optional ranking target | none | executed action | selector hides module failures |
| Trace Logger | all inference outputs | none | none | `h_exec`, scores, decisions | logs accidentally used as next prompt labels |

---

## 14. Module-to-Loss/Metric/Ablation Map

| Module | Connected Loss Candidate | Connected Metric | Required Ablation | If Ablation Does Not Hurt, What Collapses? |
|---|---|---|---|---|
| DOM Encoder | optional effect/target loss | DOM-only return, OOD-DOM drop | no-DOM | DOM representation not needed |
| Screenshot Encoder | optional visual contrast/effect | OOD-visual/layout performance | no-screenshot | visual modality claim weakens |
| Action-Effect Encoder | `L_action_effect` | falsification P/R, effect accuracy | no-effect-encoder | evidence path weakens |
| History Encoder | temporal consistency optional | persistence/update delay | no-history | persistence is not history-dependent |
| Latent Posterior Module | main latent losses | latent probes, downstream return | collapsed-latent | factorization claim weakens |
| Regime Head | `L_regime` | regime accuracy, recovery delay | no-regime | regime claim weakens |
| Control-Grammar Head | `L_control_grammar`, `L_mapping` | grammar persistence, switch delay | no-control-grammar | core novelty collapses |
| Change-Point/Event Head | `L_change_point`, `L_reveal_shift` | change F1, reveal/shift accuracy | no-change-point | event transition claim weakens |
| Progress Head | `L_progress` | progress per compute | no-progress-head | value/planning claim weakens |
| Precondition Head | `L_precondition` | failed action prediction | no-precondition-head | aux head unnecessary |
| Affordance/Blocker Head | `L_affordance`, `L_blocker` | recovery delay | no-affordance-blocker | blocker aux unnecessary |
| Current Hypothesis Scorer | `L_current_alt_ranking` | current wrong detection | no-current-scorer | falsification path weakens |
| Falsification Scorer | `L_falsification`, calibration | falsification P/R, false planning rate | no-falsification | falsification claim collapses |
| Alternative Proposer | ranking/contrastive optional | alternative recall/adoption | no-alt-proposer | alternative hypothesis claim weakens |
| Rollout Model | `L_counterfactual_rollout`, `L_action_effect`, `L_progress` | rollout fidelity | no-rollout | rollout claim collapses |
| Decision Gate | gate calibration/VOC proxy optional | progress per compute, planning calls | no-compute-gate / always-plan | decision-relevant compute claim weakens |
| Rewrite Module | `L_intent_action_mapping`, `L_recovery_ranking` | failed repetition, switch delay | no-rewrite | action-interface rewrite claim collapses |
| Final Selector | ranking optional | return/success | selector ablation | gains may come from selector only |

---

## 15. Identifiability and Concept Collapse Ledger

| Risk ID | Risk | Why Dangerous | Detection Test | Required Guardrail | Later Step |
|---|---|---|---|---|---|
| COLLAPSE-07-001 | `z_regime` and `z_control_grammar` encode same information | core separation novelty collapses | crossed split: same regime/different grammar and same grammar/different regime | balanced generator + merged ablation | 10 |
| COLLAPSE-07-002 | `z_state` absorbs all factors | latent interpretability impossible | state-only probe predicts grammar/regime | orthogonal label probes | 07/10 |
| COLLAPSE-07-003 | `z_change_point` becomes visual diff detector | reveal/shift/failure distinction invalid | large visual diff/no shift and small visual diff/shift cases | delayed/noisy/no-change controls | 05/10 |
| COLLAPSE-07-004 | `z_control_grammar` reduces to precondition classifier | grammar becomes old planning concept | same precondition/different intent mapping cases | grammar includes intent mapping + expected effect schema | 03/10 |
| COLLAPSE-07-005 | blocker head replaces regime latent | primary regime unnecessary | no-regime + blocker-head ablation | blocker auxiliary only | 10 |
| COLLAPSE-07-006 | model memorizes template/seed labels | synthetic benchmark invalid | template-regime classifier/MI test | anti-leakage audit | 06/10 |
| COLLAPSE-07-007 | task family predicts grammar | toy shortcut | task-family-only classifier | multi-grammar per task family | 05/10 |
| COLLAPSE-07-008 | collapsed latent outperforms factorized | factorization claim weakens | collapsed baseline | downgrade claim if needed | 10 |
| COLLAPSE-07-009 | merged regime-grammar outperforms split | separation claim weakens | merged baseline | claim becomes composite protocol | 10 |
| COLLAPSE-07-010 | uncertainty replaces falsification | decision rule novelty weakens | uncertainty-gate baseline | keep likelihood/evidence term | 09/10 |
| COLLAPSE-07-011 | alternative proposer becomes action search | WAC/CUWM overlap | alt-hypothesis vs alt-action ablation | grammar-conditioned proposal | 09/10 |
| COLLAPSE-07-012 | progress head drives all gains | mechanism claim cosmetic | progress-only model | mechanism metrics required | 10 |
| COLLAPSE-07-013 | verifier-only matches full model | falsification/posterior/rewrite unnecessary | VeriGUI-style baseline | current-vs-alt evidence trace | 10 |
| COLLAPSE-07-014 | always-plan beats gated model | compute claim weakens | compute-matched always-plan | gate calibration | 10 |
| COLLAPSE-07-015 | next-state WM matches full model | grammar latent unnecessary | next-state-WM-only baseline | OOD-control-grammar split | 10 |

---

## 16. Complexity and Feasibility Ledger

| Feasibility ID | Question | Decision | Reason | Risk | Minimal Implementation |
|---|---|---|---|---|---|
| FEAS-07-001 | 첫 구현은 무엇인가? | DOM+structured log FRCG-lite | screenshot 없이 core mechanism 검증 가능 | visual claim 약함 | DOM encoder + action-effect encoder + GRU history + MLP heads |
| FEAS-07-002 | text-only prototype 재사용 가능? | 가능 | hypothesis/falsification/rewrite logic 검증 | symbolic shortcut | shared symbolic interfaces |
| FEAS-07-003 | screenshot은 필수인가? | core에는 optional | grammar/evidence 중심이면 DOM+log로 충분 | visual benchmark claim 약함 | frozen visual feature ablation |
| FEAS-07-004 | counterfactual rollout은 언제 도입? | Stage 2 이후 | 먼저 effect/progress predictor 안정화 | synthetic overfit | counterfactual training-only shard |
| FEAS-07-005 | top-k default? | `k=3` candidate, k=1/5 ablation | compute와 recall 균형 | arbitrary k | k sweep |
| FEAS-07-006 | rollout horizon default? | H=3 candidate, H=1/5 ablation | short recovery 비교에 적합 | long task 약함 | horizon sweep |
| FEAS-07-007 | staged vs end-to-end? | staged 먼저 | debugging/ablation 명확 | joint optimality 손실 | Stage 1 encoders/heads → Stage 2 rollout → Stage 3 planner-in-loop |
| FEAS-07-008 | model size? | small/medium two sizes | compute-matched eval 용이 | underfit | GRU/Transformer-small baseline |
| FEAS-07-009 | rewrite는 rule인가 learned인가? | rule baseline + learned head | 구현 가능성과 비교 명확 | hand-crafted 공격 | both reported |
| FEAS-07-010 | base candidate 부족 문제? | candidate recall metric + oracle candidate upper bound | module rescue 가능성 판단 | base too weak | candidate expansion optional |
| FEAS-07-011 | hidden label supervision 현실성? | synthetic main, real auxiliary | mechanism 검증 목적 | real transfer 제한 | limitation 명시 |
| FEAS-07-012 | full multimodal main? | main은 DOM+log, hybrid는 ablation/extension | complexity 제어 | reviewer가 visual insufficiency 공격 | VisualWebArena auxiliary |
| FEAS-07-013 | architecture가 너무 복잡한가? | main claim용 modules만 main table에 유지 | kitchen-sink 공격 방지 | contribution blurred | main/aux/appendix 구분 |
| FEAS-07-014 | implementation blocker? | `h_exec` logger와 visibility-safe loader가 최우선 | metric과 leakage validity의 핵심 | 없으면 전체 무효 | MVE gate |
| FEAS-07-015 | compute logging? | 필수 | progress-per-compute claim의 근거 | missing compute metric | per-step planning_calls/rollout_steps |

---

## 17. Minimal Viable Experiment Architecture

### 17.1 MVE-1: Text-only FRCG-lite

| Item | Decision |
|---|---|
| Input | symbolic state text + public action-effect history |
| Base | fixed rule/LLM candidate action generator |
| Latents | symbolic/posterior categories for regime/grammar/event |
| Heads | falsification scorer, alternative selector, rewrite rule |
| Metrics | failed repetition, recovery delay, wrong grammar persistence |
| Purpose | Web/GUI 이전 mechanism sanity |
| Must not claim | visual grounding, browser realism |

### 17.2 MVE-2: DOM+Log FRCG-lite

| Item | Decision |
|---|---|
| Input | sanitized DOM + accessibility tree + previous action-effect log |
| Encoder | small Transformer/GRU over serialized DOM/log features |
| Latents | 4-latent + auxiliary heads |
| Rollout | H=1/3 effect/progress prediction |
| Rewrite | rule-based macro first, learned rewrite second |
| Metrics | persistence, rollout fidelity, progress per compute |
| Purpose | main synthetic Web/GUI mechanism test |

### 17.3 MVE-3: DOM+Screenshot+Log Hybrid

| Item | Decision |
|---|---|
| Input | DOM+log plus frozen visual features |
| Purpose | visual/layout perturbation OOD 보강 |
| Required ablation | no-screenshot, DOM-only, screenshot-only |
| Risk | visual feature complexity without mechanism gain |

---

## 18. Architecture-to-Claim Traceability

| Claim ID | Claim | Required Module | Required Latent | Required Data Label | Required Metric | Required Ablation |
|---|---|---|---|---|---|---|
| CLAIM-ARCH-001 | wrong-control-grammar persistence is measurable | Grammar Head, Trace Logger | `z_control_grammar` | `true_control_grammar`, `h_exec` | persistence time | no-control-grammar |
| CLAIM-ARCH-002 | regime/control-grammar separation helps recovery | Regime Head, Grammar Head, Rewrite Module | `z_regime`, `z_control_grammar` | `true_regime`, `true_control_grammar` | recovery delay, switch delay | merged regime-grammar |
| CLAIM-ARCH-003 | action-effect evidence can falsify current hypothesis | Action-Effect Encoder, Falsification Scorer | `z_control_grammar`, `z_change_point` | `observed_effect`, `true_wrong_hypothesis` | falsification P/R | no-falsification |
| CLAIM-ARCH-004 | alternative grammar rollout improves recovery | Alternative Proposer, Rollout Model | `z_regime`, `z_control_grammar` | `counterfactual_action_effects` | rollout fidelity, recovery delay | no-alternative-rollout |
| CLAIM-ARCH-005 | action-interface rewrite reduces failed repetition | Rewrite Module, Final Selector | `z_control_grammar` | `true_recovery_action` | failed-action repetition | no-rewrite |
| CLAIM-ARCH-006 | decision-relevant compute improves progress per compute | Decision Gate, Progress Predictor | uncertainty/calibration auxiliary | `compute_cost`, `progress_delta` | progress per compute | no-compute-gate, always-plan |
| CLAIM-ARCH-007 | frozen base + module isolates effect | Frozen Base Agent, Public Obs Builder | none | base candidate trace | base vs module delta | base-only |
| CLAIM-ARCH-008 | text-only mechanism scales to synthetic Web/GUI | shared falsification/rewrite components | `z_regime`, `z_control_grammar` | text + DOM labels | transfer gap | text-only vs DOM+log |
| CLAIM-ARCH-009 | reveal-vs-shift handling matters | Event Head | `z_change_point` | `true_reveal_vs_shift` | reveal-vs-shift accuracy, recovery | no-change-point |
| CLAIM-ARCH-010 | grammar-conditioned rollout beats next-state-only | Rollout Model | `z_control_grammar` | counterfactual progress/effect | grammar-conditioned progress delta | next-state-WM-only |

---

## 19. Architecture Stress Test Ledger

| Stress ID | Attack | Architecture Failure Mode | Detection Method | Required Guardrail | Affected Claim |
|---|---|---|---|---|---|
| STRESS-07-001 | Base agent already correct | module gain disappears | stratify by base failure cases | report base-success/base-failure subsets | module value |
| STRESS-07-002 | Base agent too weak | module cannot rescue missing candidate | oracle-candidate upper bound | candidate recall metric | recovery claim |
| STRESS-07-003 | VeriGUI-style verifier matches full model | falsification not needed | verifier-only baseline | posterior/hypothesis update metric | falsification claim |
| STRESS-07-004 | CUWM-style next-state WM matches full model | grammar latent not needed | next-state-WM baseline | OOD-control-grammar split | grammar claim |
| STRESS-07-005 | WAC-style action correction matches full model | rewrite not novel | action correction baseline | grammar-conditioned alternative trace | rewrite claim |
| STRESS-07-006 | Falsification scorer overreacts to noisy observations | false planning calls | noisy/delayed split FPR | delayed/noisy labels | planning claim |
| STRESS-07-007 | Alternative proposer misses true alternative | no recovery | top-k recall | k sweep, oracle alternative upper bound | alternative claim |
| STRESS-07-008 | Rollout model inaccurate | wrong action selection | rollout fidelity | counterfactual eval | rollout claim |
| STRESS-07-009 | Decision gate overplans | high compute, low efficiency | planning_calls/return | compute penalty and always-plan baseline | compute claim |
| STRESS-07-010 | Decision gate underplans | missed recovery | missed planning opportunity rate | threshold calibration | recovery claim |
| STRESS-07-011 | Rewrite module creates invalid macro | task derailment | macro validity check | precondition validation | rewrite claim |
| STRESS-07-012 | `z_control_grammar` equals precondition head | novelty collapse | no-grammar+precondition ablation | intent mapping/effect schema tasks | grammar claim |
| STRESS-07-013 | collapsed latent better | factorization weak | collapsed baseline | downgrade claim | latent claim |
| STRESS-07-014 | merged regime-grammar better | separation weak | merged baseline | composite protocol fallback | separation claim |
| STRESS-07-015 | screenshot feature adds no value | multimodal claim weak | no-screenshot ablation | DOM+log main framing | visual claim |
| STRESS-07-016 | progress head overfits synthetic reward | OOD failure | no-reward/progress ablation | OOD progress calibration | objective claim |
| STRESS-07-017 | hidden label leakage | invalid results | forbidden-token/unit tests | fail-fast audit | all claims |
| STRESS-07-018 | counterfactual shard leakage | oracle shortcut | loader audit | shard isolation | rollout claim |
| STRESS-07-019 | history encoder memorizes templates | fake persistence reduction | history shuffle/template split | OOD template split | persistence claim |
| STRESS-07-020 | auxiliary heads dominate | primary latents decorative | aux-only model | main-vs-aux ablation | latent claim |
| STRESS-07-021 | calibration poor | wrong gate decisions | ECE/Brier | calibration loss/temperature scaling | compute claim |
| STRESS-07-022 | long-horizon tasks fail | short rollout insufficient | OOD-long-horizon split | horizon=1/3/5 | generality |
| STRESS-07-023 | real benchmark lacks labels | core metrics unavailable | real auxiliary evaluation | synthetic-core framing | external validity |
| STRESS-07-024 | same success, no mechanism gain | mechanism irrelevant | mechanism metric table | claim-to-evidence rule | paper thesis |
| STRESS-07-025 | high variance across seeds | unstable architecture | seed CI | reporting protocol | credibility |

---

## 20. Required Design Revisions

| Revision ID | Architecture Issue | Required Revision | Affected Later Step | Severity |
|---|---|---|---|---|
| ARCH-REV-07-001 | 4-latent가 확정처럼 보임 | `candidate not final` 문구와 variant comparison 유지 | 08, 10 | CRITICAL |
| ARCH-REV-07-002 | placeholder REF 존재 | semantic data labels로 전면 교체 | 06, 08 | CRITICAL |
| ARCH-REV-07-003 | control grammar가 precondition으로 축소 | grammar = intent mapping + precondition + effect schema로 고정 | 08, 09 | CRITICAL |
| ARCH-REV-07-004 | falsification/verification 혼동 | likelihood/evidence-based current-vs-alt scoring으로 설계 | 08, 09 | HIGH |
| ARCH-REV-07-005 | alternative rollout이 action search처럼 보임 | alternative hypothesis record를 regime/grammar pair로 정의 | 09 | HIGH |
| ARCH-REV-07-006 | decision gate가 uncertainty threshold처럼 보임 | ΔV/action-switch/compute-cost 조건 추가 | 09 | HIGH |
| ARCH-REV-07-007 | architecture 과복잡 | DOM+log FRCG-lite를 MVE로 지정 | 08, 09 | HIGH |
| ARCH-REV-07-008 | auxiliary vs primary 중복 | aux-only/no-primary ablation 추가 | 10 | HIGH |
| ARCH-REV-07-009 | screenshot claim 과장 | screenshot은 optional hybrid/ablation으로 처리 | 10 | MEDIUM |
| ARCH-REV-07-010 | base candidate dependency | candidate recall + oracle candidate upper bound 추가 | 10 | HIGH |
| ARCH-REV-07-011 | counterfactual supervision synthetic-only | limitation과 no-counterfactual ablation 추가 | 08, 10 | HIGH |
| ARCH-REV-07-012 | `h_exec` 없으면 persistence 불가 | Trace/Belief Logger를 required module로 승격 | 06, 09, 10 | CRITICAL |

---

## 21. Handoff to Later Steps

| Handoff ID | Target Step | What Must Be Used | What Must Be Verified | What Must Not Be Assumed |
|---|---|---|---|---|
| HANDOFF-07-001 | `08_LOSS_REWARD_TRAINING_OBJECTIVE.md` | module-loss map, semantic labels, main/aux head split | 각 loss가 실제로 어떤 module을 학습시키는지 | all losses가 필수라고 가정 금지 |
| HANDOFF-07-002 | `08_LOSS_REWARD_TRAINING_OBJECTIVE.md` | valid switch/rewrite/progress/recovery targets | reward hacking 방지 가능성 | switch reward를 unconditional positive reward로 두기 금지 |
| HANDOFF-07-003 | `09_PLANNING_THEORY_ALGORITHM.md` | current hypothesis scorer, falsification scorer, alternative proposer, rollout, gate, rewrite | uncertainty-gate/tree-search/verifier와 차별화 | architecture diagram만으로 algorithm 완성 가정 금지 |
| HANDOFF-07-004 | `09_PLANNING_THEORY_ALGORITHM.md` | `h_exec`, top-k hypothesis, rollout budget, compute cost fields | executed hypothesis가 제대로 기록되는지 | posterior mode = current hypothesis라고 가정 금지 |
| HANDOFF-07-005 | `10_EVALUATION_BASELINE_ABLATION.md` | all ablation-collapse rules | no-control-grammar/no-falsification/no-rollout/no-gate ablation 효과 | success rate만으로 claim 검증 금지 |
| HANDOFF-07-006 | `10_EVALUATION_BASELINE_ABLATION.md` | high-threat baselines: VeriGUI, WAC, CUWM, WebWorld-style WM, uncertainty-gate, always-plan | compute-matched fairness | weak baseline으로 성능 부풀리기 금지 |

---

## 22. Updated Risk / Unknown Ledger

| Risk ID | Risk / Unknown | Triggered By | Why It Matters | Resolution Path | Can Be Final Claim? |
|---|---|---|---|---|---|
| ARCH-UNKNOWN-001 | regime/grammar separability | 4-latent design | core novelty | crossed split + merged ablation | NO |
| ARCH-UNKNOWN-002 | `h_exec` trace feasibility | persistence metric | core metric dependency | trace logger implementation | NO |
| ARCH-UNKNOWN-003 | counterfactual supervision transfer | synthetic rollout labels | real-world generalization | no-counterfactual ablation, real auxiliary | NO |
| ARCH-UNKNOWN-004 | base candidate recall | frozen base design | rewrite can only choose available/action macro | candidate recall/oracle candidate | NO |
| ARCH-UNKNOWN-005 | rollout horizon adequacy | H=1/3 short rollout | long tasks may fail | horizon sweep | NO |
| ARCH-UNKNOWN-006 | top-k alternative adequacy | k=3 default | true alt may be missed | k sweep + oracle alt | NO |
| ARCH-UNKNOWN-007 | screenshot necessity | hybrid design | complexity vs benefit | modality ablation | NO |
| ARCH-UNKNOWN-008 | collapsed latent strength | factorization risk | latent novelty | collapsed baseline | NO |
| ARCH-UNKNOWN-009 | merged regime-control strength | separation risk | grammar novelty | merged baseline | NO |
| ARCH-UNKNOWN-010 | verifier-only strength | VeriGUI threat | falsification novelty | verifier baseline | NO |
| ARCH-UNKNOWN-011 | next-state WM strength | CUWM/WebWorld threat | grammar rollout novelty | next-state-WM baseline | NO |
| ARCH-UNKNOWN-012 | WAC-style correction overlap | action correction threat | rewrite novelty | action correction baseline | NO |
| ARCH-UNKNOWN-013 | calibration stability | decision gate | compute efficiency | calibration metrics | NO |
| ARCH-UNKNOWN-014 | reward/progress head overfit | synthetic reward | objective validity | OOD progress tests | NO |
| ARCH-UNKNOWN-015 | implementation complexity | full architecture | project feasibility | MVE stages | NO |

---

## 23. Quality Gate Result

| Gate ID | Gate | PASS/FAIL/PARTIAL | Evidence | If Not PASS, Blocker |
|---|---|---|---|---|
| QG-07-01 | prior refs imported and repaired | PASS | semantic label repair table included | 없음 |
| QG-07-02 | citation-grade anchors included | PASS | PlaNet, Dreamer, TD-MPC, WebWorld, CUWM, WAC, VeriGUI, BrowserGym | Step 01/10에서 full citation 보강 |
| QG-07-03 | placeholder REF 제거 | PASS | DATA-LABEL placeholders mapped to semantic labels | 없음 |
| QG-07-04 | latent candidates 14개 이상 분석 | PASS | LATENT-07-001..014 | 없음 |
| QG-07-05 | factorization variants 비교 | PASS | ARCH-07-001..008 | 없음 |
| QG-07-06 | main architecture candidate 명시 | PASS_WITH_RISK | 4-latent+aux heads candidate | empirical validation 필요 |
| QG-07-07 | module contract 25개 이상 작성 | PASS | MOD-07-001..027 | 없음 |
| QG-07-08 | inference/training/evaluation flow 작성 | PASS | Sections 10~12 | 없음 |
| QG-07-09 | module-to-data map 작성 | PASS | Section 13 | 없음 |
| QG-07-10 | module-to-loss/metric/ablation map 작성 | PASS | Section 14 | 없음 |
| QG-07-11 | identifiability/collapse risks 작성 | PASS | COLLAPSE-07-001..015 | 없음 |
| QG-07-12 | minimal implementation path 작성 | PASS | Section 17 | 없음 |
| QG-07-13 | stress tests 25개 작성 | PASS | STRESS-07-001..025 | 없음 |
| QG-07-14 | no final loss/planner/eval accepted | PASS | status and forbidden preserved | 없음 |
| QG-07-15 | hidden labels not used at inference | PASS | constraints + data map + quality gate | runtime audit still required |

---

## 24. Final Statement

`07_LATENT_ARCHITECTURE_DESIGN.md`는 architecture candidate file이며, 최종 method나 training objective가 아니다.

현재 가장 강한 architecture candidate는 다음이다.

```text
4-latent primary structure (`z_state`, `z_regime`, `z_control_grammar`, `z_change_point`) plus auxiliary heads for progress, precondition, affordance/blocker, failure risk, and calibration.
```

가장 위험한 architecture risks는 다음이다.

- `z_regime`과 `z_control_grammar`가 분리되지 않을 가능성.
- `z_control_grammar`가 단순 precondition classifier로 축소될 가능성.
- collapsed latent 또는 merged regime-control grammar가 더 강할 가능성.
- VeriGUI/WAC/CUWM/WebWorld 계열 baseline이 비슷한 결과를 낼 가능성.
- counterfactual label이나 hidden label이 inference input으로 새는 leakage risk.
- decision gate가 uncertainty threshold와 구분되지 않을 가능성.

이 architecture는 다음으로만 검증될 수 있다.

- no-control-grammar, merged-regime-grammar, collapsed-latent ablation.
- no-falsification, no-alternative-rollout, no-rewrite, no-compute-gate ablation.
- verifier-only, WAC-style correction, CUWM/WebWorld-style next-state WM, uncertainty-gated planner, always-plan baseline.
- OOD-control-grammar shift, OOD-regime recombination, OOD-timing/asynchrony split.
- rollout fidelity, persistence time, recovery delay, progress per compute, false planning call rate.

다음 필수 파일:

```text
08_LOSS_REWARD_TRAINING_OBJECTIVE.md
```
