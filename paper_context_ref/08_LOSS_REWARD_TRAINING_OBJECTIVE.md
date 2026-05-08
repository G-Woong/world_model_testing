---
file_id: STEP-08
title: Loss, Reward, and Training Objective Design for FRCG-WM
version: v1.0
status: objective_contract_not_final_planner_or_evaluation
language: ko
upgraded_from:
  - user_uploaded_STEP_08_draft
  - prior_00_MASTER_REFERENCE_v1_10점
  - prior_01_to_07_context_contracts
purpose:
  - FRCG-WM의 loss, reward, training objective, staged training, reward hacking guardrail, objective ablation 계약을 최종 정리한다.
  - 모든 objective가 data label, architecture module, metric, ablation, paper claim에 실제로 연결되는지 검증한다.
  - reward가 단순 evaluation metric이 아니라 training 또는 planning decision에 작용하도록 강제한다.
  - hidden label과 counterfactual label의 inference leakage를 방지한다.
  - Claude Code가 이후 09/10/FINAL 파일을 작성하거나 objective 구현을 할 때 필요한 context만 확장적으로 읽을 수 있도록 routing layer를 제공한다.
depends_on:
  - 00_MASTER_REFERENCE.md
  - 01_RELATED_WORK_THREAT_MAP.md
  - 02_PROBLEM_NOVELTY_FALSIFICATION.md
  - 03_CORE_CONCEPT_TAXONOMY.md
  - 04_TEXT_ONLY_SMOKE_TESTBED.md
  - 05_SYNTHETIC_WEB_GUI_ENVIRONMENT.md
  - 06_DATA_SCHEMA_AND_LABELING.md
  - 07_LATENT_ARCHITECTURE_DESIGN.md
forbidden:
  - Do not finalize planning algorithm.
  - Do not finalize evaluation results.
  - Do not claim empirical success.
  - Do not use hidden labels as inference inputs.
  - Do not use counterfactual tables as agent observations.
  - Do not reward hypothesis switching unless progress-linked validity is satisfied.
  - Do not describe a reward as training objective if it is only used for evaluation.
  - Do not introduce new core claims that are absent from Step 00-07.
next_files:
  - 09_PLANNING_THEORY_ALGORITHM.md
  - 10_EVALUATION_BASELINE_ABLATION.md
  - FINAL_RESEARCH_BLUEPRINT.md
---

# 08_LOSS_REWARD_TRAINING_OBJECTIVE.md

## 1. File Purpose

이 파일은 최종 planner 문서도 아니고 최종 evaluation 문서도 아니다. 이 파일은 FRCG-WM 후보의 **objective contract**다.

목적은 다음이다.

1. `L_action_effect`, `L_progress`, `L_regime`, `L_control_grammar`, `L_falsification`, `L_intent_action_mapping`이 단순 이름이 아니라 실제 module·label·metric·ablation에 연결되는지 고정한다.
2. progress reward, failed-action penalty, recovery reward, valid hypothesis-switch reward, compute cost penalty가 실제 training 또는 planning에 작용하는 경로를 명확히 한다.
3. reward hacking, loss proliferation, hidden label leakage, counterfactual oracle leakage, objective collapse를 사전에 차단한다.
4. Step 09의 planning algorithm이 objective를 어떻게 사용해야 하는지 handoff한다.
5. Step 10의 evaluation이 어떤 ablation으로 objective 필요성을 검증해야 하는지 계약화한다.

핵심 규칙은 다음이다.

```text
loss는 반드시 어떤 module을 학습시키는지 명시해야 한다.
reward는 반드시 training 또는 planner decision에 작용해야 한다.
reward가 evaluation metric으로만 존재하면 objective에서 강등하거나 폐기한다.
hypothesis-switch reward는 반드시 progress-linked valid switch에만 허용한다.
hidden label과 counterfactual table은 inference input으로 절대 사용하지 않는다.
main objective와 auxiliary objective를 분리한다.
ablation에서 제거해도 metric 변화가 없으면 해당 objective 기반 claim은 약화된다.
```

---

## 2. Claude Code Context Routing

Claude Code는 objective 관련 작업에서 아래 routing을 따른다.

| User Intent / Task | Must Read First | Then Read | Do Not Assume |
|---|---|---|---|
| loss 수식 구현 | `08_LOSS_REWARD_TRAINING_OBJECTIVE.md` §5, §13, §20 | `06_DATA_SCHEMA_AND_LABELING.md`, `07_LATENT_ARCHITECTURE_DESIGN.md` | label field가 public observation에 있다고 가정 금지 |
| reward 함수 구현 | `08` §8, §9, §10, §21 | `06` reward/progress schema, `09` planner gate | reward가 metric으로만 존재해도 된다고 가정 금지 |
| valid hypothesis switch 정의 | `08` §8.2, §10, §20 | `03` concept taxonomy, `06` labels, `09` planning | switch 자체를 무조건 positive reward로 보상 금지 |
| staged training 설계 | `08` §11, §12, §22 | `07` module contract, `10` ablation | 모든 loss를 end-to-end로 한 번에 학습한다고 가정 금지 |
| objective ablation 설계 | `08` §15, §16, §23 | `10` evaluation plan | ablation 결과가 안 나와도 claim이 살아남는다고 가정 금지 |
| reward hacking 점검 | `08` §10, §16, §18 | `05` environment, `06` schema, `10` stress test | no-effect를 곧바로 wrong hypothesis로 처리 금지 |
| planning handoff | `08` §19, §24 | `09_PLANNING_THEORY_ALGORITHM.md` | 여기서 planning algorithm을 최종 확정 금지 |

---

## 3. Source Anchor Ledger

이 섹션은 논문 citation-ready related work의 최종본이 아니다. Step 01의 threat map 및 Step 10의 baseline 설계와 연결되는 objective 관련 anchor다.

| Anchor ID | Source / Concept | URL / Identifier | Why It Matters For Objective Design | Threat / Use |
|---|---|---|---|---|
| SRC-OBJ-001 | WebWorld: A Large-Scale World Model for Web Agent Training | https://arxiv.org/abs/2602.14721 | large-scale web world model, long-horizon simulation, inference-time search가 이미 존재하므로 generic web-world-model objective claim은 약하다 | DIRECT_THREAT |
| SRC-OBJ-002 | Computer-Using World Model | https://arxiv.org/abs/2602.17365 | frozen agent + world model + test-time action search 구조가 이미 존재하므로 FRCG objective는 grammar/falsification 특수성을 보여야 함 | DIRECT_THREAT |
| SRC-OBJ-003 | World-Model-Augmented Web Agents with Action Correction | https://arxiv.org/abs/2602.15384 | consequence simulation + action correction과 겹치므로 `L_intent_action_mapping`은 grammar-conditioned rewrite임을 증명해야 함 | DIRECT_THREAT |
| SRC-OBJ-004 | Don’t Act Blindly: Robust GUI Automation via Action-Effect Verification and Self-Correction | https://arxiv.org/abs/2604.05477 | action-effect verification baseline이 강하므로 `L_falsification`은 단순 verification을 넘어 current-vs-alt hypothesis를 학습해야 함 | DIRECT_THREAT |
| SRC-OBJ-005 | Web Agents with World Models | https://arxiv.org/abs/2410.13232 | web world model이 action outcome simulation을 사용하므로 rollout objective는 generic next-state prediction과 달라야 함 | HIGH_THREAT |
| SRC-OBJ-006 | DynaWeb: Model-Based Reinforcement Learning of Web Agents | https://arxiv.org/abs/2601.22149 | web world model을 synthetic environment로 활용해 policy training을 수행하므로 FRCG는 policy RL이 아니라 grammar-falsification mechanism을 강조해야 함 | HIGH_THREAT |
| SRC-OBJ-007 | GUI-Robust | https://arxiv.org/abs/2506.14477 | GUI anomaly/robustness 평가가 이미 있으므로 reward는 generic robustness가 아니라 wrong grammar persistence를 직접 줄여야 함 | MEDIUM_THREAT |
| SRC-OBJ-008 | Potential-Based Reward Shaping | Ng et al. 1999 | progress reward가 task objective를 왜곡하지 않도록 potential-like shaping 원칙 참고 | DESIGN_ANCHOR |
| SRC-OBJ-009 | Reward hacking / specification gaming | Concrete Problems in AI Safety; later reward hacking surveys | switch/recovery reward가 proxy hacking을 만들 수 있음을 경고 | DESIGN_GUARDRAIL |
| SRC-OBJ-010 | Calibration / Expected Calibration Error | Guo et al. 2017 and calibration literature | falsification threshold와 decision gate가 confidence calibration에 민감함 | DESIGN_ANCHOR |
| SRC-OBJ-011 | GradNorm / multi-task loss balancing | Chen et al. 2018 | multi-loss objective에서 gradient scale imbalance를 진단할 수 있음 | IMPLEMENTATION_ANCHOR |
| SRC-OBJ-012 | PCGrad / gradient conflict mitigation | gradient surgery family | main/aux losses의 conflict를 모니터링하거나 완화하는 후보 | OPTIONAL_ANCHOR |
| SRC-OBJ-013 | Advantage-Weighted Regression / AWAC family | offline RL / weighted imitation | optional Stage 8로만 사용하고 main contribution을 흐리지 않도록 제한 | APPENDIX_ONLY |
| SRC-OBJ-014 | Likelihood-ratio / sequential hypothesis testing | classical statistical testing | `L_falsification`을 evidence likelihood ratio 형태로 정식화하는 얇은 이론 spine | THEORY_ANCHOR |
| SRC-OBJ-015 | Value of Computation / Expected Value of Information | rational metareasoning literature | compute cost penalty와 decision-relevant gate의 objective grounding | THEORY_ANCHOR |

---

## 4. Imported Reference Ledger

| Imported ID | Source File | Type | Meaning | Why It Matters | Priority |
|---|---|---|---|---|---|
| REF-CORE-001 | 00_MASTER_REFERENCE.md | core thesis | wrong-control-grammar hypothesis persistence | objective가 줄여야 하는 최종 failure mode | CRITICAL |
| REF-CORE-002 | 00_MASTER_REFERENCE.md | core thesis | latent regime/control-grammar world model | `L_regime`, `L_control_grammar` 필요성 | CRITICAL |
| REF-CORE-003 | 00_MASTER_REFERENCE.md | core thesis | action-effect evidence based falsification | `L_action_effect`, `L_falsification` 중심 근거 | CRITICAL |
| REF-CORE-004 | 00_MASTER_REFERENCE.md | core thesis | current-vs-alternative hypothesis rollout | `L_current_alt_ranking`, `L_counterfactual_rollout` 근거 | CRITICAL |
| REF-CORE-005 | 00_MASTER_REFERENCE.md | core thesis | intent-to-action rewrite | `L_intent_action_mapping`, recovery reward 근거 | CRITICAL |
| REF-CORE-006 | 00_MASTER_REFERENCE.md | core thesis | decision-relevant compute reallocation | compute cost penalty, VOC proxy 근거 | CRITICAL |
| REF-CORE-007 | 00_MASTER_REFERENCE.md | constraint | Frozen Base VLM/LLM + proposed module | objective가 base LLM fine-tuning으로 성능을 만들면 안 됨 | CRITICAL |
| REF-CORE-008 | 00_MASTER_REFERENCE.md | process | text-only smoke test | objective sanity를 cheap environment에서 먼저 확인 | HIGH |
| CLAIM-02-001 | 02_PROBLEM_NOVELTY_FALSIFICATION.md | survival claim | action failure와 분리 | failed-action penalty가 단순 action failure detector로 끝나면 안 됨 | CRITICAL |
| CLAIM-02-002 | 02_PROBLEM_NOVELTY_FALSIFICATION.md | survival claim | visual grounding failure와 분리 | affordance/visual loss가 core claim을 대체하면 안 됨 | CRITICAL |
| CLAIM-02-003 | 02_PROBLEM_NOVELTY_FALSIFICATION.md | survival claim | planning failure와 분리 | reward/planning gain이 generic search로 설명되면 안 됨 | CRITICAL |
| CLAIM-02-004 | 02_PROBLEM_NOVELTY_FALSIFICATION.md | survival claim | verification failure와 분리 | `L_falsification`은 verifier-only와 구분되어야 함 | CRITICAL |
| CLAIM-02-005 | 02_PROBLEM_NOVELTY_FALSIFICATION.md | survival claim | robustness failure와 분리 | OOD/reward objective가 generic robustness claim으로 흐르면 안 됨 | HIGH |
| CONCEPT-03-003 | 03_CORE_CONCEPT_TAXONOMY.md | concept | regime | `L_regime`의 target과 ablation 기준 | CRITICAL |
| CONCEPT-03-004 | 03_CORE_CONCEPT_TAXONOMY.md | concept | control grammar | `L_control_grammar`, rewrite loss의 핵심 | CRITICAL |
| CONCEPT-03-006 | 03_CORE_CONCEPT_TAXONOMY.md | concept | action effect schema | `L_action_effect`, `L_control_grammar`의 연결점 | CRITICAL |
| CONCEPT-03-009 | 03_CORE_CONCEPT_TAXONOMY.md | concept | current hypothesis | `L_falsification`과 persistence metric의 입력 | CRITICAL |
| CONCEPT-03-010 | 03_CORE_CONCEPT_TAXONOMY.md | concept | alternative hypothesis | ranking/rollout objective의 비교 대상 | CRITICAL |
| CONCEPT-03-011 | 03_CORE_CONCEPT_TAXONOMY.md | concept | action-effect evidence | evidence encoder와 falsification loss의 핵심 입력 | CRITICAL |
| CONCEPT-03-012 | 03_CORE_CONCEPT_TAXONOMY.md | concept | falsification | objective의 핵심 mechanism | CRITICAL |
| CONCEPT-03-016 | 03_CORE_CONCEPT_TAXONOMY.md | concept | wrong-control-grammar persistence | objective가 줄여야 하는 mechanism metric | CRITICAL |
| CONCEPT-03-017 | 03_CORE_CONCEPT_TAXONOMY.md | concept | action-interface rewrite | mapping/rewrite objective의 근거 | CRITICAL |
| CONCEPT-03-018 | 03_CORE_CONCEPT_TAXONOMY.md | concept | decision-relevant compute | compute penalty와 gate objective의 근거 | CRITICAL |
| TEXT-REWARD-001 | 04_TEXT_ONLY_SMOKE_TESTBED.md | reward seed | progress reward | smoke test에서 reward sanity 확인 | HIGH |
| TEXT-METRIC-001 | 04_TEXT_ONLY_SMOKE_TESTBED.md | metric seed | failed-action repetition | reward/loss 효과 초기 검증 | HIGH |
| ENV-COUNTERFACTUAL-001 | 05_SYNTHETIC_WEB_GUI_ENVIRONMENT.md | environment label | alternative action effect | rollout objective target | CRITICAL |
| ENV-OOD-001 | 05_SYNTHETIC_WEB_GUI_ENVIRONMENT.md | split | OOD-control grammar shift | objective 일반화 검증 | CRITICAL |
| DATA-LABEL-001 | 06_DATA_SCHEMA_AND_LABELING.md | label | true_hidden_state | state/effect/progress supervision | HIGH |
| DATA-LABEL-002 | 06_DATA_SCHEMA_AND_LABELING.md | label | true_regime | `L_regime` target | CRITICAL |
| DATA-LABEL-003 | 06_DATA_SCHEMA_AND_LABELING.md | label | true_control_grammar | `L_control_grammar` target | CRITICAL |
| DATA-LABEL-004 | 06_DATA_SCHEMA_AND_LABELING.md | label | true_change_point | `L_change_point` target | HIGH |
| DATA-LABEL-005 | 06_DATA_SCHEMA_AND_LABELING.md | label | true_event_type | reveal/shift/failure/noisy 구분 | HIGH |
| DATA-LABEL-006 | 06_DATA_SCHEMA_AND_LABELING.md | label | true_reveal_vs_shift | `L_reveal_shift` target | HIGH |
| DATA-LABEL-007 | 06_DATA_SCHEMA_AND_LABELING.md | label | true_action_precondition_satisfied | `L_precondition` target | MEDIUM |
| DATA-LABEL-008 | 06_DATA_SCHEMA_AND_LABELING.md | label | true_action_effect_type | `L_action_effect` target | CRITICAL |
| DATA-LABEL-009 | 06_DATA_SCHEMA_AND_LABELING.md | label | true_failed_action | failed-action loss/reward target | HIGH |
| DATA-LABEL-010 | 06_DATA_SCHEMA_AND_LABELING.md | label | true_failure_reason | failure taxonomy | HIGH |
| DATA-LABEL-011 | 06_DATA_SCHEMA_AND_LABELING.md | label | true_recovery_action | `L_recovery_ranking`, rewrite target | CRITICAL |
| DATA-LABEL-012 | 06_DATA_SCHEMA_AND_LABELING.md | label | true_progress_delta | `L_progress`, progress reward target | CRITICAL |
| DATA-LABEL-013 | 06_DATA_SCHEMA_AND_LABELING.md | label | true_subgoal_state | subgoal reward/progress target | HIGH |
| DATA-LABEL-014 | 06_DATA_SCHEMA_AND_LABELING.md | label | true_task_success | final success metric | HIGH |
| DATA-LABEL-015 | 06_DATA_SCHEMA_AND_LABELING.md | label | true_wrong_hypothesis | `L_falsification` target | CRITICAL |
| DATA-LABEL-016 | 06_DATA_SCHEMA_AND_LABELING.md | label | true_valid_hypothesis_switch | valid switch reward target | CRITICAL |
| DATA-LABEL-017 | 06_DATA_SCHEMA_AND_LABELING.md | label | true_invalid_hypothesis_switch | invalid switch penalty target | CRITICAL |
| DATA-LABEL-018 | 06_DATA_SCHEMA_AND_LABELING.md | counterfactual label | counterfactual_action_effects | rollout target, never inference input | CRITICAL |
| DATA-LABEL-019 | 06_DATA_SCHEMA_AND_LABELING.md | counterfactual label | counterfactual_progress_delta | rollout progress target | CRITICAL |
| DATA-LABEL-020 | 06_DATA_SCHEMA_AND_LABELING.md | counterfactual label | counterfactual_failure_risk | failure-risk-aware rollout | HIGH |
| DATA-LABEL-021 | 06_DATA_SCHEMA_AND_LABELING.md | counterfactual label | counterfactual_best_alternative | alternative ranking target | HIGH |
| ARCH-MODULE-006 | 07_LATENT_ARCHITECTURE_DESIGN.md | module | Structured Action-Effect Encoder | `L_action_effect`, `L_falsification`이 학습 | CRITICAL |
| ARCH-MODULE-012 | 07_LATENT_ARCHITECTURE_DESIGN.md | module | Regime Inference Head | `L_regime`이 학습 | CRITICAL |
| ARCH-MODULE-013 | 07_LATENT_ARCHITECTURE_DESIGN.md | module | Control-Grammar Inference Head | `L_control_grammar`이 학습 | CRITICAL |
| ARCH-MODULE-014 | 07_LATENT_ARCHITECTURE_DESIGN.md | module | Change-Point/Event Head | `L_change_point`, `L_reveal_shift`가 학습 | HIGH |
| ARCH-MODULE-015 | 07_LATENT_ARCHITECTURE_DESIGN.md | module | Auxiliary Progress Head | `L_progress`가 학습 | HIGH |
| ARCH-MODULE-018 | 07_LATENT_ARCHITECTURE_DESIGN.md | module | Current Hypothesis Scorer | `L_falsification`, ranking loss가 학습 | CRITICAL |
| ARCH-MODULE-019 | 07_LATENT_ARCHITECTURE_DESIGN.md | module | Falsification Scorer | `L_falsification`, calibration loss가 학습 | CRITICAL |
| ARCH-MODULE-020 | 07_LATENT_ARCHITECTURE_DESIGN.md | module | Alternative Hypothesis Proposer | ranking/counterfactual loss가 학습 | CRITICAL |
| ARCH-MODULE-021 | 07_LATENT_ARCHITECTURE_DESIGN.md | module | Short-Horizon Rollout Model | `L_counterfactual_rollout`, `L_progress`가 학습 | CRITICAL |
| ARCH-MODULE-024 | 07_LATENT_ARCHITECTURE_DESIGN.md | module | Decision-Relevance Gate | compute/VOC 관련 objective가 연결 | CRITICAL |
| ARCH-MODULE-025 | 07_LATENT_ARCHITECTURE_DESIGN.md | module | Intent-to-Action Rewrite Module | `L_intent_action_mapping`, recovery ranking이 학습 | CRITICAL |

---

## 5. Objective Design Constraints

| Constraint ID | Constraint | Reason | Violating Design | Guardrail |
|---|---|---|---|---|
| OBJ-CONSTRAINT-001 | main objective는 논문 claim과 직접 연결되어야 한다 | loss 이름만 많으면 contribution이 흐려진다 | 모든 auxiliary를 main으로 둔다 | main 6개 + auxiliary 분리 |
| OBJ-CONSTRAINT-002 | reward는 training 또는 planner에 실제 작용해야 한다 | metric-only reward는 objective가 아니다 | reward를 evaluation return에만 쓴다 | reward-to-learning pathway에서 거부 |
| OBJ-CONSTRAINT-003 | valid switch reward는 progress-linked 조건부여야 한다 | switch 자체 보상은 oscillation을 유발한다 | switch하면 무조건 +reward | 4조건 validity assertion |
| OBJ-CONSTRAINT-004 | hidden labels는 inference input으로 금지 | leakage 시 모든 실험 무효 | `true_regime`을 prompt에 넣음 | `build_agent_observation()` assert |
| OBJ-CONSTRAINT-005 | counterfactual labels는 agent observation 금지 | oracle rollout leakage | counterfactual table을 input으로 사용 | counterfactual shard 분리 |
| OBJ-CONSTRAINT-006 | failed-action penalty는 exploration을 죽이면 안 된다 | conservative policy로 collapse | 모든 failure를 동일 penalize | first failure weak, repeated failure strong |
| OBJ-CONSTRAINT-007 | compute penalty는 necessary planning을 막으면 안 된다 | underplanning collapse | planning call마다 큰 penalty | positive VOC일 때 cost 완화 |
| OBJ-CONSTRAINT-008 | no-effect는 항상 wrong grammar가 아니다 | loading/delay/noisy와 혼동 | no_effect ⇒ wrong_hypothesis | delayed/noisy/loading flags 분리 |
| OBJ-CONSTRAINT-009 | loss scale은 normalized 되어야 한다 | CE/MSE/ranking/reward scale 충돌 | raw sum of losses | normalized loss + gradient monitor |
| OBJ-CONSTRAINT-010 | objective ablation이 claim별로 해석 가능해야 한다 | 제거해도 변화 없으면 claim 약화 | whole objective bundle만 ablation | component-wise ablation |
| OBJ-CONSTRAINT-011 | real-world extension에서 hidden/counterfactual label 부재를 인정해야 한다 | synthetic-only 과장 방지 | real Web에도 true grammar/counterfactual 있다고 가정 | weak proxy / auxiliary validation 분리 |
| OBJ-CONSTRAINT-012 | auxiliary head가 primary latent를 대체하면 안 된다 | core latent claim 붕괴 | precondition/blocker만으로 성능 설명 | aux-only / no-primary comparison |
| OBJ-CONSTRAINT-013 | calibration은 downstream planning과 연결되어야 한다 | ECE만 좋아도 실용 gain이 없을 수 있음 | calibration score만 보고 claim | ECE + false planning + return 병행 |
| OBJ-CONSTRAINT-014 | offline RL은 main contribution을 흐릴 수 있다 | 성능이 RL 덕분인지 불명확 | AWR/AWAC를 main method로 섞음 | appendix/optional stage |
| OBJ-CONSTRAINT-015 | objective는 compute-matched baseline과 비교 가능해야 한다 | always-plan이 단순 compute로 이기는 착시 방지 | rollout budget 미기록 | planning_calls/rollout_steps logging |
| OBJ-CONSTRAINT-016 | reward component는 sign과 scale을 명확히 가져야 한다 | reward mixing 재현성 문제 | `+ reward` 식의 자연어 정의만 존재 | formula/rule + clip/scale range |
| OBJ-CONSTRAINT-017 | action-interface rewrite objective는 executable primitive/macro를 생성해야 한다 | rewrite가 natural language suggestion에 그치면 실행 불가 | “try closing modal first”만 출력 | action schema/macro schema target |
| OBJ-CONSTRAINT-018 | objective는 MVE 구현에서 먼저 작동해야 한다 | full pipeline 디버깅 전에 mechanism 검증 | full multimodal end-to-end만 설계 | DOM+log FRCG-lite objective 우선 |

---

## 6. Main Loss Candidate Table

| Loss ID | Loss | Formula / Pseudo-Formula | Trains Module | Required Label | Connected Claim | Connected Metric | Ablation | Risk |
|---|---|---|---|---|---|---|---|---|
| L-MAIN-001 | `L_action_effect` | `CE(ŷ_effect_type, y_effect_type) + BCE(ŷ_no_effect, y_no_effect) + BCE(ŷ_delayed, y_delayed)` | Structured Action-Effect Encoder, Effect Predictor | `true_action_effect_type`, `no_effect_flag`, `delayed_effect_flag` | action-effect evidence가 falsification에 쓰임 | action-effect accuracy, falsification P/R | no `L_action_effect` | DOM diff shortcut, delayed effect 오판 |
| L-MAIN-002 | `L_progress` | `MSE(Δp_hat, Δp_true) + CE(subgoal_hat, subgoal_true)` | Progress/Reward Predictor, Rollout Model | `true_progress_delta`, `true_subgoal_state` | rollout이 expected progress를 비교 | normalized return, progress per compute | no `L_progress` | immediate reward 과적합 |
| L-MAIN-003 | `L_regime` | `CE(q_φ(z^r_t|H_t), y_regime)` | Regime Inference Head, Latent Posterior | `true_regime` | regime/control grammar 분리 | wrong-regime persistence, OOD-regime | no `L_regime` | task/template shortcut |
| L-MAIN-004 | `L_control_grammar` | `CE(q_φ(z^g_t|H_t,i_t), y_grammar) + CE(ŝ_schema, y_schema)` | Control-Grammar Head, Rewrite Module | `true_control_grammar`, action precondition/effect schema | intent-to-action grammar 학습 | wrong-control-grammar persistence, switch delay | no `L_control_grammar` | precondition classifier로 축소 |
| L-MAIN-005 | `L_falsification` | `BCE(σ(F_t), y_wrong)`, where `F_t = log p_θ(e_t|h_alt*) - log p_θ(e_t|h_exec)` | Falsification Scorer, Current Hypothesis Scorer | `true_wrong_hypothesis`, evidence likelihood/ranking target | current hypothesis 반증 | falsification P/R, recovery delay, false planning call | no `L_falsification` | uncertainty threshold로 collapse |
| L-MAIN-006 | `L_intent_action_mapping` | `CE(a_rewrite_hat, a_oracle_grammar) + NLL(macro_hat, macro*)` | Intent-to-Action Rewrite Module, Final Selector | `oracle_grammar_action`, `true_recovery_action` | action-interface rewrite로 반복 실패 감소 | action-interface switch delay, failed repetition | no `L_intent_action_mapping` | oracle macro synthetic overfit |

### 6.1 Main Loss Survival Criteria

| Loss | Must Improve | Must Beat | If Not |
|---|---|---|---|
| `L_action_effect` | action-effect prediction, falsification P/R | verifier-only effect detector | evidence pathway claim 약화 |
| `L_progress` | rollout value, progress per compute | next-state-WM-only | reward/progress planning claim 약화 |
| `L_regime` | OOD-regime recombination | collapsed latent | regime factorization claim 약화 |
| `L_control_grammar` | persistence, OOD-control grammar shift | merged regime-grammar, no-grammar | core novelty collapse |
| `L_falsification` | false planning call↓, recovery delay↓ | uncertainty-gated planner, verifier-only | falsification-guided claim 약화 |
| `L_intent_action_mapping` | failed repetition↓, switch delay↓ | retry/self-correction baseline | rewrite claim 약화 |

---

## 7. Auxiliary Loss Candidate Table

| Aux Loss ID | Loss | Purpose | Required Label | Helps Which Module | Risk | Recommended Status |
|---|---|---|---|---|---|---|
| L-AUX-001 | `L_failed_action` | failed action 예측 보조 | `true_failed_action`, `true_failure_reason` | Failure Risk Predictor | verifier-only와 겹침 | `AUXILIARY_RECOMMENDED` |
| L-AUX-002 | `L_change_point` | 변화 발생 감지 | `true_change_point` | Change-Point/Event Head | visual diff detector로 붕괴 | `AUXILIARY_RECOMMENDED` |
| L-AUX-003 | `L_reveal_shift` | reveal/shift/failure/noisy 분리 | `true_reveal_vs_shift`, `true_event_type` | Event Head, Latent Posterior | ambiguous label noise | `AUXILIARY_RECOMMENDED` |
| L-AUX-004 | `L_recovery_ranking` | 실패 후 recovery action ranking | `true_recovery_action`, `progress_delta` | Rewrite/Selector | recovery 다양성 억제 | `AUXILIARY_RECOMMENDED` |
| L-AUX-005 | `L_temporal_consistency` | latent posterior 불필요 진동 억제 | adjacent latent labels/history | Latent Posterior | real shift 탐지 지연 | `AUXILIARY_RECOMMENDED_WITH_GUARDRAIL` |
| L-AUX-006 | `L_calibration` | falsification/confidence calibration | correctness labels, bins | Falsification/Regime Heads | downstream 무관 가능 | `AUXILIARY_RECOMMENDED` |
| L-AUX-007 | `L_uncertainty` | uncertainty proxy 학습 | entropy/correctness proxy | Decision Gate | uncertainty-gate와 혼동 | `ABLATION_ONLY` |
| L-AUX-008 | `L_precondition` | precondition satisfaction 예측 | `true_action_precondition_satisfied` | Precondition Head | control grammar와 중복 | `AUXILIARY_RECOMMENDED` |
| L-AUX-009 | `L_affordance` | clickable/scrollable affordance 예측 | visible/enabled/clickable fields | Affordance Head | visual grounding으로 흡수 | `APPENDIX_ONLY` |
| L-AUX-010 | `L_blocker` | modal/overlay/blocker 감지 | covered_by/blocker labels | Blocker Head | regime과 중복 | `APPENDIX_ONLY` |
| L-AUX-011 | `L_current_alt_ranking` | true alternative가 current보다 score 높게 | `counterfactual_best_alternative`, pair labels | Alternative Proposer | pair leakage 위험 | `AUXILIARY_RECOMMENDED` |
| L-AUX-012 | `L_counterfactual_rollout` | alternative effect/progress 예측 | `counterfactual_action_effects`, `counterfactual_progress_delta` | Rollout Model | synthetic-only overfit | `AUXILIARY_RECOMMENDED` |
| L-AUX-013 | `L_entropy_regularization` | posterior collapse/overconfidence 완화 | posterior entropy | Latent Posterior | 실제 확신도 약화 | `ABLATION_ONLY` |
| L-AUX-014 | `L_representation_contrastive` | evidence/history representation 강화 | positive/negative transitions | History Encoder | contribution 흐림 | `APPENDIX_ONLY` |
| L-AUX-015 | `L_value_of_computation_proxy` | compute 사용 가치 proxy | planning benefit proxy | Decision Gate | Step 09와 중복 | `UNKNOWN_NEEDS_EXPERIMENT` |
| L-AUX-016 | `L_invalid_switch` | unnecessary switch 억제 | `true_invalid_hypothesis_switch` | Decision Gate, Selector | OOD exploration 억제 | `AUXILIARY_RECOMMENDED_WITH_GUARDRAIL` |
| L-AUX-017 | `L_delayed_effect` | delayed/noisy effect와 failure 구분 | delayed/noisy flags | Event Head, Falsification Scorer | label ambiguity | `AUXILIARY_RECOMMENDED` |
| L-AUX-018 | `L_macro_validity` | generated action macro validity 학습 | executable macro label | Rewrite Module | hand-crafted macro dependence | `APPENDIX_OR_MVE_REQUIRED` |

---

## 8. Reward Component Table

| Reward ID | Reward Component | Formula / Rule | Acts On | Intended Effect | Hacking Risk | Guardrail | Ablation |
|---|---|---|---|---|---|---|---|
| R-001 | progress reward | `r_prog = clip(Δprogress, 0, 1)` | Progress Predictor, Planner | subgoal 진행 선호 | progress shortcut | subgoal labels hidden from observation | no progress reward |
| R-002 | subgoal completion reward | `r_sub = α_sub * 1[subgoal_newly_completed]` | Planner, value target | sparse success 보완 | subgoal gaming | final success consistency check | no subgoal reward |
| R-003 | failed-action penalty | `r_fail = -α_fail * 1[failed_action]` | Failure Risk Predictor, Planner | 무효 action 감소 | exploration 사망 | first failure weak, repeated failure strong | no failed penalty |
| R-004 | repeated-failure penalty | `r_rep = -α_rep * count_same_invalid_mapping` | Planner, Selector | 반복 실패 억제 | loading retry 억제 | delayed/loading/stale exception | no repeated penalty |
| R-005 | recovery reward | `r_rec = α_rec if evidence_seen ∧ k_step_progress>0 ∧ not deliberate_failure` | Recovery Ranking, Planner | 회복 action 선호 | 일부러 실패 유도 | agent-induced deliberate failure 제외 | no recovery reward |
| R-006 | valid hypothesis-switch reward | `r_sw = α_sw if valid_switch_4cond` | Falsification/Selector target | 진짜 hypothesis switch 유도 | switch oscillation | 4조건 모두 만족해야 부여 | no switch reward |
| R-007 | invalid switch penalty | `r_inv = -α_inv if switch ∧ no_falsifying_evidence ∧ no_progress` | Decision Gate | 쓸데없는 switch 억제 | OOD exploration 억제 | high-evidence uncertainty exception | no invalid switch penalty |
| R-008 | compute cost penalty | `r_comp = -β * rollout_steps` | Decision Gate, Planner | progress per compute 개선 | necessary planning 억제 | positive ΔV/VOC일 때 완화 | no compute penalty |
| R-009 | overplanning penalty | `r_over = -β_over * 1[plan_called ∧ action_unchanged ∧ ΔV≈0]` | Decision Gate | 불필요 planning 감소 | conservative gate | missed opportunity metric 병행 | no overplanning penalty |
| R-010 | unnecessary switch penalty | `r_unsw = -α_unsw if switch ∧ h_exec_correct` | Falsification/Selector | correct hypothesis 유지 | late correction 방해 | evidence likelihood condition | no unnecessary switch penalty |
| R-011 | delayed recovery penalty | `r_delay = -α_delay * steps_until_progress_after_evidence` | Planner, Ranking | 빠른 회복 | short-term 편향 | long horizon return 병행 | no delay penalty |
| R-012 | optional exploration bonus | `r_exp = ε if novel_valid_grammar ∧ uncertainty_high ∧ no_invalid_switch` | early training only | 대안 탐색 보조 | random switch 증가 | invalid switch penalty와 함께 제한 | exploration bonus off |

### 8.1 Valid Hypothesis-Switch Reward Contract

`R-006`은 가장 위험한 reward다. 다음 4조건을 모두 만족하지 않으면 reward를 주면 안 된다.

```python
def is_valid_hypothesis_switch(record):
    return (
        record["true_wrong_hypothesis_before_switch"] is True
        and record["alternative_explains_evidence_better"] is True
        and record["executed_action_changed"] is True
        and record["future_progress_delta_within_k"] > 0
    )
```

금지 규칙:

```text
switch 자체를 reward하지 마라.
posterior entropy 감소만 reward하지 마라.
current hypothesis가 틀렸다는 evidence 없이 switch reward를 주지 마라.
progress 또는 failure reduction 없이 switch reward를 주지 마라.
```

---

## 9. Reward-to-Learning Pathway

| Reward ID | Used For Training? | Used For Planner? | Used For Evaluation? | Pathway | If Only Metric, Reject? |
|---|---:|---:|---:|---|---:|
| R-001 | YES | YES | YES | progress predictor target + planner expected value + return | YES |
| R-002 | YES | YES | YES | subgoal value target + planner expected value | YES |
| R-003 | YES | YES | YES | failure risk target + planner penalty + repetition metric | YES |
| R-004 | YES | YES | YES | repeated invalid mapping penalty + selector shaping | YES |
| R-005 | YES | YES | YES | recovery action ranking + planner value | YES |
| R-006 | YES, but guarded | YES, but guarded | YES | switch validity target + planner switching value | YES |
| R-007 | YES | YES | YES | invalid switch classifier/penalty + gate calibration | YES |
| R-008 | YES | YES | YES | decision gate cost + compute-normalized return | YES |
| R-009 | YES | YES | YES | anti-overplanning gate target | YES |
| R-010 | YES | YES | YES | unnecessary switch suppression | YES |
| R-011 | YES | YES | YES | recovery delay minimization | YES |
| R-012 | OPTIONAL | OPTIONAL | DIAGNOSTIC | early exploration only | YES |

---

## 10. Objective Variants

| Variant ID | Objective Variant | Included Losses | Included Rewards | Pros | Cons | Recommended Use |
|---|---|---|---|---|---|---|
| OBJ-MAIN6 | six main losses only | `L_action_effect`, `L_progress`, `L_regime`, `L_control_grammar`, `L_falsification`, `L_intent_action_mapping` | none | claim traceability 명확 | change/reveal/recovery 보조 약함 | initial main candidate |
| OBJ-MAIN6+AUX | main + selected auxiliary | main6 + failed/change/reveal/recovery/calibration/ranking | limited targets | 성능/안정성 보강 | contribution 흐림 | main expanded candidate |
| OBJ-NO-REWARD | supervised losses only | main/aux supervised | none | reward hacking 없음 | planner value 약함 | ablation baseline |
| OBJ-REWARD-AWARE | supervised + reward prediction | main6 + progress/reward heads | progress/recovery/penalty | planner expected value 연결 | reward scale 위험 | planner pretraining |
| OBJ-COUNTERFACTUAL | counterfactual target included | main6 + `L_counterfactual_rollout` + ranking | counterfactual progress/failure | alternative rollout fidelity 강화 | synthetic-only 의존 | synthetic main candidate |
| OBJ-PLANNER-AWARE | planning objective with compute cost | prediction losses + VOC proxy | compute cost / value | progress per compute 직접 연결 | Step 09와 경계 모호 | handoff to Step 09 |
| OBJ-END2END | all losses end-to-end | main + all auxiliary + planner proxy | all rewards | 성능 가능성 | 불안정/해석 어려움 | appendix only until proven |
| OBJ-STAGED | staged training | 단계별 main/aux | 단계별 reward | 안정성/해석성 | stage error propagation | recommended training protocol |
| OBJ-MVE-DOMLOG | minimal viable objective | effect + grammar + falsification + mapping + progress | progress/failure/compute only | 빠른 구현 가능 | visual claim 없음 | first implementation |

---

## 11. Training Stage Protocol

| Stage ID | Stage | Objective | Data Used | Trainable Modules | Frozen Modules | Stop Criterion | Failure Signal |
|---|---|---|---|---|---|---|---|
| STAGE-08-000 | data validation / leakage audit | hidden label leakage, split shortcut 검사 | schema + generated trace | none | all models | leakage flag 0 | hidden label in public obs |
| STAGE-08-001 | representation pretraining | observation/evidence/history encoding 안정화 | public obs + action-effect labels | encoders, history encoder | base agent | validation effect/regime stable | shortcut acc too high |
| STAGE-08-002 | action-effect/progress training | `L_action_effect + L_progress` | step trajectories | effect/progress heads | base agent | validation effect/progress stable | DOM diff overfit |
| STAGE-08-003 | latent head training | `L_regime + L_control_grammar + L_change_point` | hidden labels | latent heads | base agent | OOD head metrics pass | regime/grammar collapse |
| STAGE-08-004 | falsification/ranking training | `L_falsification + L_current_alt_ranking` | evidence + wrong hypothesis + alternatives | scorer/proposer | encoders optionally freeze | falsification P/R + calibration | false planning spikes |
| STAGE-08-005 | rewrite training | `L_intent_action_mapping + L_recovery_ranking` | oracle/recovery actions | rewrite module, selector | base agent | switch delay decreases | macro overfit |
| STAGE-08-006 | rollout validation | `L_counterfactual_rollout + L_progress` | counterfactual records | rollout model | base agent | rollout fidelity pass | synthetic-only overfit |
| STAGE-08-007 | planner-in-loop validation | expected value + compute penalty | closed-loop traces | gate/scorer/selector | base agent | progress per compute improves | over/underplanning |
| STAGE-08-008 | optional offline RL / AWR | advantage-weighted fine-tuning | offline trajectories | selector/rewrite only | encoders optional freeze | ablation-separated gain | contribution confusion |
| STAGE-08-009 | ablation retraining | remove each objective | all splits | variant-specific | baseline fixed | expected metric drop | no drop ⇒ claim weakened |

---

## 12. Loss Weighting and Optimization Stability

| Weighting ID | Strategy | Pros | Cons | When To Use | Risk |
|---|---|---|---|---|---|
| WEIGHT-08-001 | fixed weights | 재현성/해석성 좋음 | scale tuning 필요 | initial MVE/main6 | loss imbalance |
| WEIGHT-08-002 | staged weights | 안정성 좋음 | stage 간 error propagation | OBJ-STAGED | early error freeze |
| WEIGHT-08-003 | uncertainty-based weighting | automatic balancing | 해석성 약함 | auxiliary many | uncertainty head와 혼동 |
| WEIGHT-08-004 | GradNorm | training rate 균형 | 구현 복잡 | gradient conflict 심할 때 | method contribution 흐림 |
| WEIGHT-08-005 | manual claim-driven weighting | claim traceability 명확 | arbitrary attack | main paper candidate | hyperparameter sensitivity |
| WEIGHT-08-006 | main-loss first auxiliary later | main claim 보호 | aux late | main6 안정화 후 | aux underuse |
| WEIGHT-08-007 | representation pretrain then planner | encoders 안정 | target mismatch | DOM+log/hybrid | error propagation |
| WEIGHT-08-008 | freeze/unfreeze schedule | leakage/shortcut 제어 | 복잡 | staged training | underfit/overfit |
| WEIGHT-08-009 | loss scale normalization | CE/MSE/ranking 균형 | 기준 필요 | always | scale drift |
| WEIGHT-08-010 | gradient conflict monitoring | 진단 가능 | 직접 해결 아님 | all multi-loss runs | monitor만 하고 방치 |
| WEIGHT-08-011 | reward scale clipping | reward hacking 완화 | true value 왜곡 | reward-aware variants | clipped objective weak |
| WEIGHT-08-012 | group-wise ablation weights | objective group contribution 해석 | 많은 실험 필요 | Step 10 ablation | compute burden |

---

## 13. Minimal Viable Experiment Objective Contract

최초 구현은 full objective가 아니라 아래 MVE로 시작한다.

### 13.1 MVE-DOMLOG Objective

| Item | Decision |
|---|---|
| Observation | DOM + accessibility + structured action-effect log. screenshot optional. |
| Main losses | `L_action_effect`, `L_control_grammar`, `L_falsification`, `L_intent_action_mapping`, `L_progress` |
| Auxiliary losses | `L_failed_action`, `L_precondition`, `L_reveal_shift` only if labels stable |
| Rewards | progress, failed-action penalty, repeated-failure penalty, compute cost penalty |
| Excluded initially | full end-to-end planner-aware RL, optional exploration bonus, heavy contrastive loss |
| Required ablation | no grammar, no falsification, no mapping, no progress, no compute penalty |
| Go/No-Go metric | failed-action repetition↓, recovery delay↓, progress per compute↑ |

### 13.2 MVE Objective Builder Pseudo-Code

```python
def compute_mve_losses(batch, model_outputs, weights):
    losses = {}

    # Main supervised losses
    losses["L_action_effect"] = ce(model_outputs.effect_type, batch.true_action_effect_type)
    losses["L_control_grammar"] = ce(model_outputs.grammar_logits, batch.true_control_grammar)
    losses["L_falsification"] = bce(model_outputs.falsification_score, batch.true_wrong_hypothesis)
    losses["L_intent_action_mapping"] = ce(model_outputs.rewrite_action, batch.oracle_grammar_action)
    losses["L_progress"] = mse(model_outputs.progress_delta, batch.true_progress_delta)

    # Optional stable auxiliary losses
    if batch.has_field("true_action_precondition_satisfied"):
        losses["L_precondition"] = bce(
            model_outputs.precondition_score,
            batch.true_action_precondition_satisfied,
        )
    if batch.has_field("true_failed_action"):
        losses["L_failed_action"] = bce(model_outputs.failed_action_score, batch.true_failed_action)

    total = sum(weights[k] * normalize_loss(v, k) for k, v in losses.items())
    return total, losses
```

---

## 14. Objective-to-Data/Module Map

| Objective ID | Required Data Fields | Required Labels | Trained Module | Inference-Time Use | Leakage Risk |
|---|---|---|---|---|---|
| OBJ-DATA-001 | previous_action, observed_effect, DOM diff, visual/a11y diff | true_action_effect_type | Action-Effect Encoder | evidence feature | expected effect label leakage |
| OBJ-DATA-002 | history, progress_state, action | true_progress_delta, true_subgoal_state | Progress/Reward Predictor | value estimate | future progress leakage |
| OBJ-DATA-003 | public observation/history | true_regime | Regime Head | regime posterior | true_regime in input |
| OBJ-DATA-004 | intent, action history, effect schema | true_control_grammar | Grammar Head | grammar posterior | grammar text/class leakage |
| OBJ-DATA-005 | h_exec, evidence, alternative score | true_wrong_hypothesis | Falsification Scorer | replanning trigger | wrong-hypothesis label in input |
| OBJ-DATA-006 | intent, candidates, grammar | oracle_grammar_action, true_recovery_action | Rewrite Module | executable action/macro | oracle action as prompt |
| OBJ-DATA-007 | action target metadata | true_action_precondition_satisfied | Precondition Head | invalid action avoidance | precondition public leakage |
| OBJ-DATA-008 | blocker/overlay/loading fields | true_failure_reason | Blocker/Failure Head | recovery clue | blocker label naming leak |
| OBJ-DATA-009 | event trace | true_change_point, true_event_type | Event Head | belief update | event label leakage |
| OBJ-DATA-010 | reveal/shift annotation | true_reveal_vs_shift | Reveal/Shift Head | transition classification | ambiguous label |
| OBJ-DATA-011 | top-k alternatives, counterfactual effects | counterfactual_best_alternative | Alt Proposer | top-k hypotheses | counterfactual input leakage |
| OBJ-DATA-012 | alternative rollout traces | counterfactual_progress_delta | Rollout Model | expected progress | synthetic-only overfit |
| OBJ-DATA-013 | failed trace + recovery action | true_recovery_action | Recovery Ranking | action selection | hand-crafted recovery bias |
| OBJ-DATA-014 | prediction correctness bins | correctness/calibration labels | Calibration Head | threshold calibration | calibration target leakage |
| OBJ-DATA-015 | planning calls, rollout steps, return | planning benefit proxy | Decision Gate | plan/no-plan | post-hoc benefit leakage |
| OBJ-DATA-016 | same invalid mapping sequence | repeated failure counter | Selector/Planner penalty | avoid loops | legitimate retry penalty |
| OBJ-DATA-017 | action macro execution log | macro validity label | Rewrite Module | executable macro | macro oracle leakage |
| OBJ-DATA-018 | current/alt pair labels | pairwise preference | Current-Alt Ranker | alt ranking | pair construction shortcut |
| OBJ-DATA-019 | noisy/delayed flags | delayed/noisy labels | Event/Falsification Head | avoid false falsification | delayed flag in public obs |
| OBJ-DATA-020 | episode/split metadata | split/OOD type | no training input | audit only | split leakage |

---

## 15. Objective-to-Claim Traceability

| Claim ID | Claim | Required Loss | Required Reward | Required Module | Required Label | Required Metric | Required Ablation |
|---|---|---|---|---|---|---|---|
| OBJ-CLAIM-001 | wrong-control-grammar persistence is measurable and reducible | `L_control_grammar`, `L_falsification`, `L_intent_action_mapping` | repeated failure/recovery rewards | grammar head, falsification scorer, rewrite module | true_control_grammar, true_wrong_hypothesis | persistence time, failed repetition | no grammar / no falsification / no mapping |
| OBJ-CLAIM-002 | regime/control-grammar separation helps recovery | `L_regime`, `L_control_grammar`, `L_reveal_shift` | valid switch reward | regime/grammar heads | true_regime, true_control_grammar | recovery delay, OOD-control grammar | merged regime-control grammar |
| OBJ-CLAIM-003 | action-effect evidence can falsify current hypothesis | `L_action_effect`, `L_falsification` | false planning penalty optional | effect encoder, falsification scorer | true_action_effect_type, true_wrong_hypothesis | falsification P/R | no action-effect / no falsification |
| OBJ-CLAIM-004 | alternative grammar rollout improves recovery | `L_current_alt_ranking`, `L_counterfactual_rollout` | progress/recovery reward | alt proposer, rollout model | counterfactual_best_alternative | rollout fidelity, recovery delay | no alternative rollout |
| OBJ-CLAIM-005 | action-interface rewrite reduces failed repetition | `L_intent_action_mapping`, `L_recovery_ranking` | failed/repeated penalty | rewrite module, selector | oracle_grammar_action, true_recovery_action | failed repetition, switch delay | no rewrite |
| OBJ-CLAIM-006 | decision-relevant compute improves progress per compute | `L_value_of_computation_proxy` optional | compute/overplanning penalty | decision gate | planning benefit proxy | progress per compute | no compute penalty / always-plan |
| OBJ-CLAIM-007 | reward/progress shaping helps planning | `L_progress` | progress/subgoal/recovery rewards | progress predictor, planner | true_progress_delta | normalized return | no reward / no L_progress |
| OBJ-CLAIM-008 | frozen base agent + module isolates effect | all module losses, base frozen | same reward | all proposed modules | same base output/candidates | delta over frozen base | base-only |
| OBJ-CLAIM-009 | text-only objective scales to Web/GUI | same objective families | same reward contract | text+web modules | shared labels | text-to-web consistency | text-only only |
| OBJ-CLAIM-010 | OOD grammar shift beats verifier-only | `L_control_grammar`, `L_falsification`, `L_mapping` | valid switch/recovery rewards | grammar/scorer/rewrite | OOD labels | OOD-control grammar success | verifier-only baseline |
| OBJ-CLAIM-011 | reveal-vs-shift separation prevents false falsification | `L_reveal_shift`, `L_delayed_effect` | invalid switch penalty | event head, falsification scorer | true_reveal_vs_shift | false planning call rate | no reveal/shift loss |
| OBJ-CLAIM-012 | objective is not reward-only or loss-only artifact | main loss + reward ablation | all reward components | whole pipeline | all labels | component-wise metric delta | reward-free / supervised-free variants |

---

## 16. Objective Ablation Plan

| Ablation ID | Removed Objective | Expected Failure | Connected Claim | Required Metric Change | If No Change, Interpretation |
|---|---|---|---|---|---|
| ABL-08-001 | no `L_action_effect` | effect prediction/falsification 하락 | evidence-based falsification | falsification P/R↓, recovery delay↑ | effect loss 불필요 또는 shortcut 존재 |
| ABL-08-002 | no `L_progress` | rollout value 비교 약화 | progress-aware planning | normalized return↓, progress per compute↓ | progress predictor 불필요 또는 reward leakage |
| ABL-08-003 | no `L_regime` | OOD-regime 대응 하락 | regime factorization | OOD-regime success↓ | regime latent claim 약화 |
| ABL-08-004 | no `L_control_grammar` | persistence/rewrite 하락 | control grammar novelty | persistence↑, failed repetition↑ | 핵심 claim 붕괴 |
| ABL-08-005 | no `L_falsification` | false planning/late recovery 증가 | falsification novelty | falsification P/R↓, recovery delay↑ | verification/uncertainty로 충분 가능 |
| ABL-08-006 | no `L_intent_action_mapping` | rewrite 실패 | action-interface rewrite | switch delay↑, failed repetition↑ | policy correction claim 약화 |
| ABL-08-007 | no `L_failed_action` | failure risk 예측 하락 | failure loop 감소 | failed repetition↑ | verifier만으로 충분 가능 |
| ABL-08-008 | no `L_change_point` | transition 감지 하락 | change-point awareness | change-point F1↓ | change-point 필요성 약화 |
| ABL-08-009 | no `L_reveal_shift` | reveal/shift 혼동 | reveal-vs-shift | reveal-shift acc↓, false planning↑ | taxonomy claim 약화 |
| ABL-08-010 | no `L_recovery_ranking` | recovery action 선택 하락 | recovery improvement | recovery delay↑ | rewrite만으로 충분 가능 |
| ABL-08-011 | no progress reward | return 하락 | reward/progress shaping | normalized return↓ | reward contribution 약화 |
| ABL-08-012 | no failed-action penalty | 무효 행동 반복 | failure loop 감소 | failed repetition↑ | penalty 필요성 약화 |
| ABL-08-013 | no recovery reward | 회복 지연 | recovery mechanism | recovery delay↑ | ranking loss만 충분 가능 |
| ABL-08-014 | no valid switch reward | hypothesis switch 감소 | valid switch utility | adoption rate↓ | switch reward 불필요 가능 |
| ABL-08-015 | no compute penalty | overplanning 증가 | compute efficiency | planning calls↑, progress/compute↓ | gate claim 약화 |
| ABL-08-016 | no counterfactual rollout target | alt rollout fidelity 하락 | alternative rollout | rollout fidelity↓ | counterfactual target 불필요 가능 |
| ABL-08-017 | main losses only | auxiliary 제거 | main contribution clarity | aux-specific metrics 하락 여부 | auxiliary 불필요 또는 필수 |
| ABL-08-018 | auxiliary losses only | main 제거 | main objective necessity | core metrics 하락 | main6 과장 가능 |
| ABL-08-019 | reward-free supervised training | reward 제거 | reward pathway | progress per compute↓ | reward 없이도 충분하면 reward claim 약화 |
| ABL-08-020 | planner-objective-only | supervised heads 제거 | supervision necessity | head metrics↓, instability↑ | planner objective만으로 충분 가능 |
| ABL-08-021 | no invalid switch penalty | switch oscillation | safe switching | invalid switch rate↑ | penalty 불필요 가능 |
| ABL-08-022 | no delayed/noisy effect loss | false falsification | robust falsification | false planning call↑ | event taxonomy 약화 |
| ABL-08-023 | no calibration loss | threshold instability | calibrated falsification | ECE↑, false planning↑ | calibration 불필요 가능 |
| ABL-08-024 | no precondition loss | invalid action 증가 | action executability | invalid action rate↑ | grammar head가 충분 가능 |
| ABL-08-025 | no reward scale normalization | training instability | objective stability | variance↑ | normalization 불필요 가능 |

---

## 17. Reward Hacking Ledger

| Hack ID | Reward Failure Scenario | Why Dangerous | Detection Test | Guardrail | If Not Solved |
|---|---|---|---|---|---|
| HACK-08-001 | switch reward 때문에 hypothesis를 매 step 바꾼다 | oscillation이 reward를 먹음 | invalid switch rate, switch count | 4조건 valid switch | switch reward 제거/강등 |
| HACK-08-002 | recovery reward 때문에 일부러 실패를 만든다 | deliberate failure exploit | failure-before-recovery audit | deliberate failure exclusion | recovery reward eval-only |
| HACK-08-003 | failed-action penalty가 탐색을 죽인다 | conservative/no-op policy | exploration coverage, missed opportunity | first failure weak | penalty annealing |
| HACK-08-004 | compute penalty가 necessary planning을 막는다 | underplanning | missed planning opportunity | positive ΔV exception | β reduction |
| HACK-08-005 | progress reward가 subgoal shortcut을 학습한다 | true task success와 분리 | progress-success correlation | held-out subgoal definitions | progress reward redesign |
| HACK-08-006 | no-effect를 무조건 failure로 해석한다 | loading/delay 오판 | delayed/noisy split | event flag separation | `L_delayed_effect` 추가 |
| HACK-08-007 | repeated penalty가 loading retry를 막는다 | legitimate wait/retry 실패 | loading cases audit | loading exception | penalty conditionalization |
| HACK-08-008 | valid switch 판단이 hidden label에 과의존한다 | real transfer 약함 | weak-label proxy eval | inference-safe proxy score | switch reward synthetic-only |
| HACK-08-009 | invalid switch penalty가 OOD exploration을 막는다 | new grammar 발견 방해 | OOD exploration metric | high-evidence exception | penalty soften |
| HACK-08-010 | progress reward가 UI template artifact를 학습한다 | generator shortcut | template-heldout split | template randomization | reward relabeling |
| HACK-08-011 | reward predictor가 future leakage를 학습한다 | impossible inference | causal timestamp audit | no future fields | schema fix |
| HACK-08-012 | counterfactual best action supervision이 synthetic에 과적합된다 | real benchmark 약함 | no-counterfactual ablation | synthetic-only claim | auxiliary only |
| HACK-08-013 | compute-to-recovery가 short-term progress만 선호한다 | long-horizon derail | long-horizon composition split | horizon-normalized value | reward horizon extension |
| HACK-08-014 | action macro rewrite가 reward를 과도하게 얻는다 | bloated macro | macro length/cost audit | macro cost | macro regularization |
| HACK-08-015 | oracle upper bound와 gap이 reward 설계 탓이다 | method가 아니라 reward problem | oracle gap decomposition | reward sensitivity | revise reward |
| HACK-08-016 | verifier-only baseline도 같은 reward로 따라온다 | novelty 약화 | verifier-only reward-aware baseline | hypothesis-specific loss | claim weaken |
| HACK-08-017 | always-plan baseline이 reward를 더 잘 활용한다 | gate claim 약화 | compute-matched comparison | compute budget match | gate redesign |
| HACK-08-018 | reward component scale imbalance | training collapse | per-loss gradient norm | normalization/clipping | stage split |
| HACK-08-019 | invalid switch penalty가 valid switch까지 억제 | no recovery switch | valid switch recall | threshold tuning | penalty redesign |
| HACK-08-020 | optional exploration bonus가 random switch 유도 | noisy policy | switch entropy, invalid rate | early-stage only | remove bonus |
| HACK-08-021 | progress reward가 DOM diff만 보상 | semantic progress 없음 | semantic-vs-DOM progress audit | progress from env state only | reward source fix |
| HACK-08-022 | recovery reward가 same failure loop 강화 | fail-recover-fail loop | cycle detection | no bonus after repeated induced failure | recovery reward off |

---

## 18. Objective Stress Test Ledger

| Stress ID | Attack | Objective Failure Mode | Detection Method | Required Revision | Affected Claim |
|---|---|---|---|---|---|
| STRESS-08-001 | `L_control_grammar`가 hidden label memorization | template shortcut | OOD template split, label leakage audit | sanitize + balanced templates | control grammar claim |
| STRESS-08-002 | `L_regime`과 `L_control_grammar`가 같은 정보 학습 | factorization collapse | merged ablation, MI/probe | crossed regime/grammar labels | separation claim |
| STRESS-08-003 | `L_falsification`이 noisy evidence 취약 | false planning | noisy/delayed split FPR | event-aware falsification | falsification claim |
| STRESS-08-004 | `L_progress`가 immediate reward만 학습 | long horizon failure | OOD-long-horizon split | multi-step progress target | planning claim |
| STRESS-08-005 | `L_action_effect`가 DOM diff 예측에 과적합 | semantic miss | semantic effect metric | effect type target 강화 | evidence claim |
| STRESS-08-006 | `L_mapping`이 base LLM shortcut | grammar 무시 | same intent/different grammar split | grammar-conditioned mapping | rewrite claim |
| STRESS-08-007 | `L_recovery_ranking`이 다양성 억제 | one-action overfit | multiple valid recovery cases | set/ranking target | recovery claim |
| STRESS-08-008 | `L_change_point`가 visual diff detector | shift 오판 | visual diff/no-shift cases | event taxonomy loss | change-point claim |
| STRESS-08-009 | `L_reveal_shift` label ambiguity | unstable training | inter-rule consistency audit | unknown/ambiguous bucket | taxonomy claim |
| STRESS-08-010 | calibration loss가 planning과 무관 | ECE-only gain | ECE + downstream metrics | gate-linked calibration | compute claim |
| STRESS-08-011 | counterfactual rollout target synthetic artifact | real transfer weak | no-counterfactual/real proxy | synthetic-only wording | rollout claim |
| STRESS-08-012 | reward scale imbalance | main loss 압도 | gradient norm logs | normalization/weight sweep | objective validity |
| STRESS-08-013 | compute penalty kills planning | underplanning | missed opportunity rate | VOC-conditioned penalty | compute claim |
| STRESS-08-014 | switch reward oscillation | hypothesis thrash | invalid switch rate | 4-condition reward | switch claim |
| STRESS-08-015 | failed penalty kills exploration | conservative policy | exploration coverage | weak first penalty | recovery claim |
| STRESS-08-016 | auxiliary heads dominate primary latent | primary decoration | aux-only ablation | aux as auxiliary only | latent claim |
| STRESS-08-017 | staged training error propagation | early error lock-in | stage diagnostics | retraining/joint finetune | training stability |
| STRESS-08-018 | end-to-end training unstable | gradient conflict | loss curves/variance | staged default | implementation |
| STRESS-08-019 | offline RL contribution confusion | method attribution unclear | no-RL ablation | appendix only | paper clarity |
| STRESS-08-020 | hidden labels absent in real setting | synthetic-only | real auxiliary proxy | claim limitation | external validity |
| STRESS-08-021 | no-loss ablation no drop | objective unnecessary | component ablation | weaken/drop claim | all claims |
| STRESS-08-022 | verifier-only same reward catches up | novelty weak | verifier-reward baseline | strengthen hypothesis loss | falsification |
| STRESS-08-023 | always-plan higher return | gate weak | compute-matched evaluation | gate redesign | compute claim |
| STRESS-08-024 | no-reward supervised model similar | reward contribution weak | no-reward comparison | reward claim weaken | reward claim |
| STRESS-08-025 | objective too complex | reviewer rejects kitchen sink | main/aux separation | MVE + appendix split | clarity |
| STRESS-08-026 | pairwise alt ranking uses hidden oracle too strongly | oracle leakage | training/inference field audit | ranking target hidden-only | rollout claim |
| STRESS-08-027 | progress and switch rewards conflict | unstable optimization | reward correlation audit | staged rewards | reward stability |
| STRESS-08-028 | delayed recovery penalty causes premature switching | invalid switches | delay vs invalid switch plot | evidence threshold | recovery claim |

---

## 19. Runtime Assertion and Leakage Guardrails

### 19.1 Inference Input Assertion

```python
FORBIDDEN_IN_AGENT_OBS = {
    "true_hidden_state",
    "true_regime",
    "true_control_grammar",
    "true_change_point",
    "true_event_type",
    "true_reveal_vs_shift",
    "true_wrong_hypothesis",
    "true_valid_hypothesis_switch",
    "true_invalid_hypothesis_switch",
    "counterfactual_action_effects",
    "counterfactual_progress_delta",
    "counterfactual_best_alternative",
    "oracle_regime_action",
    "oracle_grammar_action",
}


def assert_no_objective_leakage(agent_obs):
    flat_keys = flatten_keys(agent_obs)
    leaked = sorted(k for k in flat_keys if k in FORBIDDEN_IN_AGENT_OBS)
    assert not leaked, f"Forbidden objective labels leaked into agent observation: {leaked}"
```

### 19.2 Reward Validity Assertion

```python
def compute_valid_switch_reward(record, alpha_sw):
    valid = (
        record.true_wrong_hypothesis_before_switch
        and record.alternative_explains_evidence_better
        and record.executed_action_changed
        and record.future_progress_delta_within_k > 0
    )
    if valid:
        return alpha_sw
    return 0.0
```

### 19.3 Compute Cost Assertion

```python
def compute_planning_cost(record, beta):
    return -beta * record.rollout_steps


def assert_compute_logged(record):
    assert hasattr(record, "planning_calls")
    assert hasattr(record, "rollout_steps")
    assert hasattr(record, "candidate_action_count")
```

---

## 20. Loss Implementation Contract

| Implementation ID | Function | Input | Output | Must Assert |
|---|---|---|---|---|
| IMPL-LOSS-001 | `loss_action_effect(batch, outputs)` | action-effect record, effect labels | scalar loss | delayed/noisy labels separated |
| IMPL-LOSS-002 | `loss_progress(batch, outputs)` | progress labels | scalar loss | no future field in public obs |
| IMPL-LOSS-003 | `loss_regime(batch, outputs)` | hidden regime target | scalar loss | hidden target used only as label |
| IMPL-LOSS-004 | `loss_control_grammar(batch, outputs)` | grammar target, schema labels | scalar loss | grammar target not in observation |
| IMPL-LOSS-005 | `loss_falsification(batch, outputs)` | wrong hypothesis target, evidence scores | scalar loss | `h_exec` present |
| IMPL-LOSS-006 | `loss_intent_action_mapping(batch, outputs)` | oracle grammar action/recovery action | scalar loss | oracle action not public input |
| IMPL-LOSS-007 | `loss_counterfactual_rollout(batch, outputs)` | counterfactual shard | scalar loss | counterfactual excluded from inference |
| IMPL-LOSS-008 | `compute_reward_components(record)` | env step trace | reward dict | valid switch 4 conditions |
| IMPL-LOSS-009 | `aggregate_objective(losses, weights)` | normalized losses | scalar total | all loss keys logged |
| IMPL-LOSS-010 | `audit_objective_batch(batch)` | train batch | pass/fail report | no leakage, fields complete |

---

## 21. Reward Function Contract

| Component | Default Sign | Default Range | Source Field | Guardrail |
|---|---:|---|---|---|
| progress reward | positive | `[0, 1]` | `true_progress_delta` | clipped, env-state-based |
| subgoal reward | positive | `{0, α_sub}` | `true_subgoal_state` | only newly completed |
| failed-action penalty | negative | `[-α_fail, 0]` | `true_failed_action` | weaker for first failure |
| repeated-failure penalty | negative | `[-α_rep*k, 0]` | repeated invalid mapping trace | exempt loading/delayed states |
| recovery reward | positive | `{0, α_rec}` | failure→progress trace | no deliberate failure |
| valid switch reward | positive | `{0, α_sw}` | valid switch conditions | all 4 conditions required |
| invalid switch penalty | negative | `[-α_inv, 0]` | invalid switch label | high-evidence exception |
| compute cost penalty | negative | `[-β*steps, 0]` | rollout steps | compute-matched logging |
| overplanning penalty | negative | `[-β_over, 0]` | planning called/action unchanged | action-switch condition |
| delayed recovery penalty | negative | `[-α_delay*t, 0]` | evidence-to-progress delay | normalize by horizon |

---

## 22. Handoff to Planning Step

| Handoff ID | Target Step | What Must Be Used | What Must Be Verified | What Must Not Be Assumed |
|---|---|---|---|---|
| HANDOFF-08-001 | `09_PLANNING_THEORY_ALGORITHM.md` | `F_t` definition from `L_falsification` | likelihood-ratio form vs classifier form | falsification is not just failed-action flag |
| HANDOFF-08-002 | `09_PLANNING_THEORY_ALGORITHM.md` | reward-to-planner pathway | reward enters expected value and compute gate | reward is not only evaluation return |
| HANDOFF-08-003 | `09_PLANNING_THEORY_ALGORITHM.md` | valid switch reward contract | switch requires evidence and progress | switching itself is not good |
| HANDOFF-08-004 | `09_PLANNING_THEORY_ALGORITHM.md` | compute cost penalty | gate optimizes progress per compute | always-plan is not acceptable by default |
| HANDOFF-08-005 | `09_PLANNING_THEORY_ALGORITHM.md` | counterfactual rollout loss | counterfactual used for training/eval only | counterfactual table is not agent input |
| HANDOFF-08-006 | `09_PLANNING_THEORY_ALGORITHM.md` | delayed/noisy effect separation | prevent false falsification | no-effect does not always mean wrong grammar |

---

## 23. Handoff to Evaluation Step

| Handoff ID | Target Step | Required Ablation / Metric | Claim Risk If Missing |
|---|---|---|---|
| HANDOFF-08-EVAL-001 | `10_EVALUATION_BASELINE_ABLATION.md` | no `L_control_grammar` | core grammar novelty cannot be defended |
| HANDOFF-08-EVAL-002 | `10_EVALUATION_BASELINE_ABLATION.md` | no `L_falsification` + verifier-only baseline | falsification claim collapses into verification |
| HANDOFF-08-EVAL-003 | `10_EVALUATION_BASELINE_ABLATION.md` | no reward vs reward-aware | reward contribution cannot be claimed |
| HANDOFF-08-EVAL-004 | `10_EVALUATION_BASELINE_ABLATION.md` | no compute penalty / always-plan | compute efficiency claim invalid |
| HANDOFF-08-EVAL-005 | `10_EVALUATION_BASELINE_ABLATION.md` | no counterfactual rollout | alternative rollout claim weak |
| HANDOFF-08-EVAL-006 | `10_EVALUATION_BASELINE_ABLATION.md` | reward hacking stress metrics | reward safety unverified |
| HANDOFF-08-EVAL-007 | `10_EVALUATION_BASELINE_ABLATION.md` | OOD-control grammar shift | objective may be synthetic shortcut |

---

## 24. Updated Risk / Unknown Ledger

| Risk ID | Risk / Unknown | Triggered By | Why It Matters | Resolution Path | Can Be Final Claim? |
|---|---|---|---|---|---|
| RISK-08-001 | `L_control_grammar` may memorize labels | hidden grammar labels | core novelty could be shortcut | OOD split, leakage audit, no-grammar ablation | NO |
| RISK-08-002 | switch reward may cause oscillation | reward design | invalid behavior | 4-condition valid switch + invalid penalty | NO |
| RISK-08-003 | compute penalty may kill planning | compute cost | recovery failure | VOC-conditioned gate in Step 09 | NO |
| RISK-08-004 | progress reward may be synthetic artifact | dense progress | toy benchmark risk | OOD + subgoal consistency | NO |
| RISK-08-005 | counterfactual supervision synthetic-only | counterfactual labels | real transfer limit | synthetic main + real auxiliary framing | NO |
| RISK-08-006 | too many losses blur contribution | objective set | reviewer clarity risk | main/aux separation + ablation | NO |
| RISK-08-007 | verifier-only baseline may match | action-effect verification | falsification novelty weak | Step 10 direct baseline | NO |
| RISK-08-008 | no-reward supervised may match | reward-aware claim | reward not needed | no-reward ablation | NO |
| RISK-08-009 | auxiliary heads may dominate | aux losses | primary latent weak | aux-only and no-aux ablations | NO |
| RISK-08-010 | loss weighting arbitrary | multi-loss | reproducibility issue | fixed/staged weights, sensitivity | NO |
| RISK-08-011 | delayed/noisy effect mislabeling | event taxonomy | false falsification | `L_delayed_effect`, event split | NO |
| RISK-08-012 | oracle rewrite action unavailable | synthetic labels | rewrite training weak | macro schema and fallback | NO |
| RISK-08-013 | calibration improves but policy doesn't | `L_calibration` | metric mismatch | downstream gate metrics | NO |
| RISK-08-014 | offline RL contribution confound | optional Stage 8 | method clarity | appendix only, no-RL ablation | NO |
| RISK-08-015 | exact Bayesian language overclaim | likelihood-ratio loss | theory criticism | learned approximation wording | NO |
| RISK-08-016 | reward scale imbalance | all rewards | training instability | normalization/clip/gradient logs | NO |
| RISK-08-017 | action-effect loss learns visual diff only | DOM/visual diff | semantic evidence weak | effect type labels + semantic split | NO |
| RISK-08-018 | real benchmark lacks labels | hidden/counterfactual labels | external validation limited | weak proxy metrics | NO |

---

## 25. Quality Gate Result

| Gate ID | Gate | PASS/FAIL/PARTIAL | Evidence | If Not PASS, Blocker |
|---|---|---|---|---|
| QG-08-01 | prior refs imported | PASS | Step 00-07 references integrated | none |
| QG-08-02 | source anchor ledger included | PASS | WebWorld/CUWM/WAC/VeriGUI/DynaWeb anchors | Step 01 still citation-grade finalization |
| QG-08-03 | main losses defined with formulas | PASS | `L-MAIN-001`..`006` | none |
| QG-08-04 | auxiliary losses analyzed | PASS | 18 auxiliary candidates | none |
| QG-08-05 | objective variants compared | PASS | 9 variants | none |
| QG-08-06 | reward components formula/rule defined | PASS | 12 reward components | none |
| QG-08-07 | reward-to-learning pathway included | PASS | §9 | none |
| QG-08-08 | reward hacking ledger included | PASS | 22 hacking cases | none |
| QG-08-09 | staged training protocol included | PASS | 10 stages | none |
| QG-08-10 | loss weighting/stability strategies included | PASS | 12 strategies | none |
| QG-08-11 | objective-to-data/module map included | PASS | 20 mappings | none |
| QG-08-12 | objective-to-claim traceability included | PASS | 12 claim rows | none |
| QG-08-13 | objective ablation plan included | PASS | 25 ablations | none |
| QG-08-14 | objective stress tests included | PASS | 28 stress tests | none |
| QG-08-15 | runtime leakage assertions included | PASS | §19 | none |
| QG-08-16 | planning/evaluation not finalized | PASS | handoff only, no empirical result | none |
| QG-08-17 | reward acts on training/planning, not only metric | PASS | §9 and reward contract | none |

---

## 26. Final Statement of This File

`08_LOSS_REWARD_TRAINING_OBJECTIVE.md`는 objective design file이며, 최종 planner나 evaluation 결과 문서가 아니다.

현재 가장 강한 objective 후보는 다음이다.

```text
OBJ-STAGED + OBJ-MVE-DOMLOG:
초기에는 DOM+structured action-effect log 기반 FRCG-lite로
L_action_effect, L_control_grammar, L_falsification, L_intent_action_mapping, L_progress를 학습하고,
progress/failed-action/repeated-failure/compute-cost reward를 planner value와 gate에 연결한다.
이후 counterfactual rollout, reveal-vs-shift, calibration, recovery ranking을 auxiliary로 추가한다.
```

가장 위험한 objective risk는 다음이다.

- `valid hypothesis-switch reward`가 oscillation/reward hacking을 만들 수 있다.
- `L_control_grammar`가 hidden label/template shortcut으로 붕괴할 수 있다.
- `L_falsification`이 단순 no-effect/failure detector로 축소될 수 있다.
- progress reward가 synthetic subgoal artifact를 학습할 수 있다.
- counterfactual rollout target은 synthetic-only supervision이므로 real benchmark claim으로 과장하면 안 된다.
- too many losses는 contribution을 흐릴 수 있으므로 main/aux 분리가 필요하다.

다음 파일에서 반드시 검증해야 할 것:

- Step 09는 `F_t`, `ΔV`, compute cost, action switch probability를 하나의 planning gate로 연결해야 한다.
- Step 10은 no-grammar, no-falsification, no-rewrite, no-reward, no-compute-penalty, no-counterfactual-rollout ablation을 반드시 포함해야 한다.
- Step 10은 verifier-only, next-state-WM-only, always-plan, uncertainty-gated planner와 compute-matched 비교를 해야 한다.

다음 필수 파일:

```text
09_PLANNING_THEORY_ALGORITHM.md
```
