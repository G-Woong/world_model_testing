---
file_id: STEP-10
title: Evaluation, Baseline, and Ablation Design for FRCG-WM
version: v1.0_10score
status: evaluation_contract_not_empirical_results
language: ko
derived_from:
  - 붙여넣은 마크다운(1)(84).md
  - 00_MASTER_REFERENCE.md
  - 01_RELATED_WORK_THREAT_MAP.md
  - 02_PROBLEM_NOVELTY_FALSIFICATION.md
  - 03_CORE_CONCEPT_TAXONOMY.md
  - 04_TEXT_ONLY_SMOKE_TESTBED.md
  - 05_SYNTHETIC_WEB_GUI_ENVIRONMENT.md
  - 06_DATA_SCHEMA_AND_LABELING.md
  - 07_LATENT_ARCHITECTURE_DESIGN.md
  - 08_LOSS_REWARD_TRAINING_OBJECTIVE.md
  - 09_PLANNING_THEORY_ALGORITHM.md
purpose:
  - FRCG-WM의 claim, metric, baseline, ablation, OOD split, compute-matched comparison, failure interpretation을 1:1로 고정한다.
  - success-rate-only evaluation, 약한 baseline, 불공정 compute 비교, unsupported novelty claim을 방지한다.
  - Claude Code가 FINAL_RESEARCH_BLUEPRINT.md 작성 시 필요한 evaluation context를 선택적으로 확장해 읽을 수 있도록 routing과 implementation contract를 제공한다.
forbidden:
  - Do not report empirical results.
  - Do not fabricate numbers.
  - Do not claim acceptance-level evidence.
  - Do not write the final paper evaluation section.
  - Do not ignore negative-result scenarios.
  - Do not make planning claims without compute-matched comparison.
  - Do not make control-grammar claims without no-control-grammar and merged/collapsed ablations.
next_files:
  - FINAL_RESEARCH_BLUEPRINT.md
---

# 10_EVALUATION_BASELINE_ABLATION.md

## 1. File Purpose

이 파일은 실험 결과 문서가 아니다. 이 파일은 **evaluation contract**다.
목적은 `claim → metric → baseline → ablation → split → pass/fail condition → failure interpretation → reviewer defense`를 1:1로 고정하는 것이다.

본 논문의 핵심은 단순 success rate 상승이 아니다. 핵심은 다음 mechanism metrics가 실제로 논문 claim과 맞물리는지 검증하는 것이다.

- `wrong-control-grammar hypothesis persistence`
- `repeated invalid mapping rate`
- `failed-action repetition rate`
- `recovery delay after falsifying evidence`
- `falsification precision/recall/calibration`
- `alternative rollout fidelity`
- `action-interface switch delay`
- `progress per compute`
- `false planning call rate`
- `OOD-control grammar shift performance`

따라서 본 파일은 숫자를 만들지 않는다. 모든 threshold는 후보 기준이며, 실제 실험 전까지 확정된 evidence가 아니다.

가장 중요한 원칙은 다음이다.

```text
성공률이 올라도 mechanism metric이 움직이지 않으면 core novelty claim은 살아남지 않는다.
compute-matched 비교 없이 planning claim은 살아남지 않는다.
no-control-grammar ablation이 무너지지 않으면 control grammar claim은 살아남지 않는다.
verifier-only baseline이 비슷하면 falsification novelty는 verification-plus-recovery 수준으로 약화된다.
next-state-WM-only 또는 WAC/CUWM/WebWorld-style baseline이 비슷하면 generic world-model과의 차별성은 약화된다.
```

---

## 2. Claude Code Context Routing

| User Intent / Task | Must Read First | Then Read | Do Not Assume |
|---|---|---|---|
| FINAL_RESEARCH_BLUEPRINT.md 작성 | 이 파일 전체 | 00~09 전체 | 이 파일이 empirical result라고 가정 금지 |
| metric 정의 확인 | §6 Metric Definition Table | 06_DATA_SCHEMA_AND_LABELING.md, 09_PLANNING_THEORY_ALGORITHM.md | success rate만으로 claim 검증 금지 |
| baseline 구현 | §7 Baseline Suite | 01_RELATED_WORK_THREAT_MAP.md, 09_PLANNING_THEORY_ALGORITHM.md | direct threat baseline을 생략 금지 |
| ablation runner 작성 | §8 Ablation Suite | 07, 08, 09 | ablation이 isolated된다고 자동 가정 금지 |
| OOD split 평가 | §10 OOD Split Evaluation Plan | 05_SYNTHETIC_WEB_GUI_ENVIRONMENT.md, 06_DATA_SCHEMA_AND_LABELING.md | OOD가 실제 held-out인지 반드시 audit |
| compute-matched 평가 | §11 Compute-Matched Evaluation Plan | 09_PLANNING_THEORY_ALGORITHM.md | planning calls/rollout steps/wall-clock proxy 중 하나만 보고 판단 금지 |
| reviewer defense 작성 | §13 Reviewer Attack Defense Table | 01, 02, 10 | WebWorld/CUWM/WAC/VeriGUI threat를 약하게 축소 금지 |
| negative result 해석 | §14 Failure Interpretation Protocol | FINAL_RESEARCH_BLUEPRINT.md | 실패 결과를 숨기거나 claim을 유지 금지 |
| qualitative trace 선정 | §16 Qualitative Failure Analysis Protocol | 06 trace schema, 09 planner trace | cherry-pick 금지 |

---

## 3. Citation-Grade Source Anchor Ledger

> 이 표는 final bibliography가 아니다. FINAL_RESEARCH_BLUEPRINT.md와 paper draft에서는 각 source를 citation 형식으로 다시 정리해야 한다.

| Source ID | Source / Benchmark | URL | Key Finding | How It Informs Evaluation |
|---|---|---|---|---|
| SRC-EVAL-001 | WebArena | https://arxiv.org/abs/2307.13854 | realistic self-hosted web environment; functional correctness 중심 web task evaluation anchor | 실제 웹 benchmark 보조 검증 및 success-rate reporting 기준 |
| SRC-EVAL-002 | VisualWebArena | https://arxiv.org/abs/2401.13649 | multimodal realistic visual web tasks; execution-based evaluation 계열 | visual/layout OOD 및 screenshot ablation 근거 |
| SRC-EVAL-003 | OSWorld | https://arxiv.org/abs/2404.07972 | real computer-use benchmark; open-ended OS task execution-based evaluation | real benchmark auxiliary validation의 상한과 한계 정의 |
| SRC-EVAL-004 | BrowserGym | https://arxiv.org/abs/2412.05467 | unified gym-like web-agent evaluation ecosystem with observation/action spaces | evaluation harness/reproducibility/standardized runner 참고 |
| SRC-EVAL-005 | MiniWoB++ | https://miniwob.farama.org/ | controlled synthetic web interaction tasks | text-only/synthetic smoke benchmark sanity anchor |
| SRC-EVAL-006 | WorkArena | https://arxiv.org/abs/2403.07718 | enterprise web tasks benchmark | workflow realism 보조 검증 후보 |
| SRC-EVAL-007 | ST-WebAgentBench | https://arxiv.org/abs/2410.06703 | safety/trustworthiness evaluation for web agents | invalid rewrite와 unintended action qualitative protocol 참고 |
| SRC-EVAL-008 | SafeArena | https://openreview.net/forum?id=7TrOBcxSvy | web agent safety benchmark | safety limitation 및 harmful/unintended behavior reporting 참고 |
| SRC-EVAL-009 | Rliable | https://arxiv.org/abs/2108.13264 | robust aggregate metrics and confidence intervals for RL | multi-seed/CI/aggregate reporting protocol 참고 |
| SRC-EVAL-010 | D4RL | https://arxiv.org/abs/2004.07219 | offline RL benchmark/dataset evaluation reporting | dataset/version/split reporting 참고 |
| SRC-EVAL-011 | Datasheets for Datasets | https://arxiv.org/abs/1803.09010 | dataset documentation framework | dataset card, intended/prohibited use, limitations reporting |
| SRC-EVAL-012 | Playwright Tracing | https://playwright.dev/docs/trace-viewer | browser execution trace artifact | trace logging/debug/qualitative replay format 참고 |

---

## 4. Evaluation Scope and Claim Contract

| Scope ID | Evaluation Question | Required Evidence | If Not Observed | Affected Claim |
|---|---|---|---|---|
| EVAL-SCOPE-001 | text-only smoke는 무엇을 증명하는가? | symbolic/text environment에서 persistence, recovery, falsification 개선 | GUI 확장 claim 불가 | text-to-Web/GUI transfer |
| EVAL-SCOPE-002 | synthetic Web/GUI는 무엇을 증명하는가? | hidden grammar/change-point/counterfactual label 기반 mechanism metrics | mechanism claim 검증 불가 | main method validity |
| EVAL-SCOPE-003 | real benchmark auxiliary는 무엇을 증명하는가? | WebArena/VisualWebArena/OSWorld/WorkArena-style success 또는 weak proxy | external validity 약함 | realism/generalization |
| EVAL-SCOPE-004 | success rate만 오르면 충분한가? | 아니오. persistence/recovery/falsification/rewrite metric 동반 필요 | performance-only paper로 약화 | core novelty |
| EVAL-SCOPE-005 | persistence 감소가 왜 중요한가? | wrong grammar 유지 step 감소가 core failure reduction을 직접 측정 | problem claim 약화 | failure-mode claim |
| EVAL-SCOPE-006 | compute-matched return이 왜 필요한가? | 더 많이 planning해서 좋아진 효과 제거 | planning claim 무효 | compute reallocation |
| EVAL-SCOPE-007 | OOD-control grammar shift가 왜 필요한가? | visual/task 같고 grammar만 바뀐 held-out split | control grammar claim 약화 | grammar novelty |
| EVAL-SCOPE-008 | no-control-grammar ablation이 안 무너지면? | grammar가 필요 없다는 뜻 | core claim 폐기/축소 | control grammar |
| EVAL-SCOPE-009 | verifier-only가 비슷하면? | verification/recovery만으로 충분 | falsification novelty 약화 | falsification |
| EVAL-SCOPE-010 | next-state-WM-only가 비슷하면? | grammar factor 없이도 충분 | WM novelty 약화 | grammar WM |
| EVAL-SCOPE-011 | uncertainty-gated planner가 비슷하면? | falsification gate가 불필요 | decision-relevant compute 약화 | planning gate |
| EVAL-SCOPE-012 | always-plan이 더 좋으면? | gate가 utility를 제한 | efficiency claim만 남김 | compute gate |
| EVAL-SCOPE-013 | merged/collapsed latent가 더 좋으면? | explicit factorization 불필요 | latent separation claim 약화 | architecture |
| EVAL-SCOPE-014 | no-reward가 비슷하면? | reward가 학습/planning에 작용하지 않음 | objective claim 약화 | reward/loss |
| EVAL-SCOPE-015 | OOD split이 train과 비슷하면? | generalization 주장 불가 | OOD claim 무효 | robustness |

---

## 5. Claim-to-Evidence Master Table

| Claim ID | Claim | Required Metric | Required Baseline | Required Ablation | Required Split | Pass Condition | Fail Interpretation |
|---|---|---|---|---|---|---|---|
| CLAIM-EVAL-001 | wrong-control-grammar persistence는 독립적으로 측정 가능한 failure mode다 | MET-PERSIST-001, MET-FAIL-002, MET-BELIEF-001 | BASE-001, BASE-005, BASE-009 | ABL-002, ABL-003, ABL-022 | SPLIT-001, SPLIT-003, SPLIT-008 | persistence/repeated invalid mapping이 baseline보다 감소하고 no-control-grammar에서 악화 | 감소하지 않으면 문제정의는 action failure 또는 verification failure로 약화 |
| CLAIM-EVAL-002 | regime과 control grammar 분리는 recovery와 OOD generalization에 기여한다 | MET-REC-001, MET-OOD-003, MET-LATENT-001 | BASE-009, BASE-012, BASE-013 | ABL-001, ABL-002, ABL-003, ABL-006 | SPLIT-002, SPLIT-003, SPLIT-009 | factorized model이 merged/collapsed보다 OOD grammar/recovery에서 우위 | merged/collapsed가 비슷하거나 더 좋으면 latent factorization claim 약화 |
| CLAIM-EVAL-003 | action-effect evidence는 current hypothesis를 falsify할 수 있다 | MET-FALS-001, MET-FALS-002, MET-CAL-001 | BASE-005, BASE-006, BASE-012 | ABL-016, ABL-022, ABL-023 | SPLIT-001, SPLIT-007, SPLIT-008 | failed-action flag보다 falsification PR/calibration 우위 | 비슷하면 VeriGUI-style verification으로 축소 |
| CLAIM-EVAL-004 | alternative grammar rollout은 recovery action 선택을 개선한다 | MET-WM-001, MET-ALT-001, MET-REC-001 | BASE-009, BASE-013, BASE-014 | ABL-024, ABL-025, ABL-026, ABL-036 | SPLIT-002, SPLIT-003, SPLIT-006 | random/next-state-only보다 rollout fidelity와 recovery 개선 | 비슷하면 rollout/alternative novelty 약화 |
| CLAIM-EVAL-005 | action-interface rewrite는 repeated invalid mapping을 줄인다 | MET-FAIL-002, MET-REWRITE-001, MET-SWITCH-001 | BASE-003, BASE-004, BASE-006 | ABL-017, ABL-035 | SPLIT-003, SPLIT-007, SPLIT-010 | rewrite 제거 시 failed repetition/recovery delay 악화 | 악화 없으면 rewrite module을 appendix 또는 implementation detail로 하향 |
| CLAIM-EVAL-006 | decision-relevant compute gate는 always-plan/uncertainty-gate보다 progress per compute가 높다 | MET-COMP-003, MET-COMP-004, MET-COMP-007 | BASE-010, BASE-012, BASE-015 | ABL-020, ABL-023, ABL-033, ABL-034 | SPLIT-001~SPLIT-010 | 동일 compute budget에서 progress per compute/false planning 우위 | 비슷하면 compute reallocation claim 폐기 또는 약화 |
| CLAIM-EVAL-007 | reward/progress objective는 planning decision에 실제로 작용한다 | MET-PROG-001, MET-RETURN-002, MET-HACK-001 | BASE-021 vs reward-free | ABL-013, ABL-019, ABL-021 | SPLIT-001, SPLIT-003, SPLIT-006 | no-reward/no-progress에서 value/planning metric 악화 | 비슷하면 reward는 metric/reporting용으로 하향 |
| CLAIM-EVAL-008 | Frozen Base + module 구조는 base LLM 성능 confound를 통제한다 | MET-SUCCESS-001, MET-REC-001, MET-COMP-003 | BASE-001, BASE-004 | module off/on, same-base | all splits | 동일 base/candidate budget에서 module 추가 이득 | 차이 없으면 base LLM이 해결했거나 module 효과 미약 |
| CLAIM-EVAL-009 | text-only smoke mechanism은 synthetic Web/GUI에서 같은 방향으로 재현된다 | MET-TEXT-001, MET-PERSIST-001, MET-REC-001 | text baselines + DOM+log variant | text-to-synthetic bridge ablation | text + SPLIT-001/003 | text와 synthetic에서 persistence/recovery 개선 방향 일치 | 불일치하면 text-only artifact로 해석 |
| CLAIM-EVAL-010 | OOD-control grammar shift에서 verifier-only와 next-state-WM-only보다 강하다 | MET-OOD-003, MET-PERSIST-001, MET-REC-001 | BASE-005, BASE-009 | ABL-002, ABL-016, ABL-024 | SPLIT-003 | core OOD split에서 명확한 mechanism metric 우위 | 실패 시 main novelty 약화 |
| CLAIM-EVAL-011 | reveal-vs-shift 구분은 false switch와 invalid rewrite를 줄인다 | MET-EVENT-002, MET-SWITCH-002, MET-REWRITE-002 | change-detector-only | ABL-004, ABL-011, ABL-no-reveal-shift | SPLIT-008 | ambiguous event에서 invalid switch 감소 | taxonomy claim 약화 |
| CLAIM-EVAL-012 | counterfactual supervision은 alternative rollout fidelity와 recovery decision을 보조한다 | MET-WM-001, MET-ALT-002, MET-COMP-008 | no-counterfactual, random alt | ABL-036 | synthetic-only eval set | counterfactual target 제거 시 rollout fidelity/decision 악화 | 비슷하면 synthetic-only supervision 기여 약화 |

---

## 6. Metric Definition Table

| Metric ID | Metric | Formal Definition | Required Fields | Connected Claim | Expected Direction | Failure Interpretation |
|---|---|---|---|---|---|---|
| MET-SUCCESS-001 | task success rate | #success / #episodes | task_success_label, done | utility | 상승 | success-only이면 mechanism claim 불충분 |
| MET-RETURN-001 | normalized return | (return - task_min)/(oracle_or_task_max-task_min) | reward_components, oracle_bound | partial progress | 상승 | reward shaping artifact 가능 |
| MET-RETURN-002 | subgoal completion rate | completed_subgoals / total_subgoals | subgoal_state | dense progress | 상승 | subgoal shortcut 위험 |
| MET-STEP-001 | episode length | steps until done | step_index, done | efficiency | 감소/적정 | premature stop 가능 |
| MET-PERSIST-001 | wrong-control-grammar persistence time | first_falsifying_evidence_t 이후 correct grammar switch까지 step 수 | true_control_grammar, selected_hypothesis, evidence_time | core mechanism | 감소 | 안 줄면 core problem claim 약화 |
| MET-FAIL-001 | failed-action rate | failed_actions / executed_actions | true_failed_action | execution robustness | 감소 | 단순 verifier로도 줄 수 있음 |
| MET-FAIL-002 | failed-action repetition rate | same intent+same invalid mapping repeated failures / failure opportunities | intent, action, grammar, failure_reason | persistence symptom | 감소 | 안 줄면 rewrite/falsification 약화 |
| MET-FAIL-003 | repeated invalid mapping rate | same intent에서 wrong grammar mapping 재사용 비율 | intent, selected_grammar, true_grammar | grammar persistence | 감소 | control grammar metric 핵심 |
| MET-SWITCH-001 | action-interface switch delay | falsifying evidence 후 executable action mapping 변경까지 step | evidence_time, action_mapping_log | rewrite timing | 감소 | invalid switch와 함께 봐야 함 |
| MET-REC-001 | recovery delay after falsifying evidence | falsifying evidence 후 progress_delta>0까지 step | evidence_time, progress_delta | recovery | 감소 | progress label 품질 의존 |
| MET-BELIEF-001 | evidence-to-hypothesis-update delay | evidence 후 h_exec/posterior mode 변화까지 step | posterior_log, h_exec_log | belief update | 감소 | h_exec 정의가 없으면 불가능 |
| MET-ALT-001 | alternative grammar adoption rate | needed alternative cases 중 correct/plausible alternative 선택 비율 | alt_set, selected_alt, oracle_alt | proposal | 상승 | oracle leakage 금지 |
| MET-ALT-002 | alternative proposal recall@k | true helpful grammar가 top-k에 포함된 비율 | oracle_alt, topk_alt | proposal quality | 상승 | top-k arbitrary 문제 |
| MET-WM-001 | alternative rollout fidelity | predicted effect/progress vs counterfactual effect/progress agreement | counterfactual_effects, predicted_rollout | WM quality | 상승 | synthetic-only supervision 한계 |
| MET-WM-002 | action-effect prediction accuracy | effect_type prediction accuracy/F1 | true_action_effect_type, pred_effect_type | effect model | 상승 | DOM diff shortcut 가능 |
| MET-PROG-001 | progress prediction error | MAE(predicted_progress_delta, true_progress_delta) | pred_progress, true_progress_delta | value model | 감소 | immediate progress bias |
| MET-FALS-001 | falsification precision | TP_wrong_current / predicted_wrong_current | true_wrong_hypothesis, F_t | falsification | 상승 | recall과 tradeoff |
| MET-FALS-002 | falsification recall | TP_wrong_current / all_wrong_current | true_wrong_hypothesis, F_t | falsification | 상승 | precision 낮아질 위험 |
| MET-CAL-001 | falsification calibration ECE | bin별 predicted wrong prob와 empirical wrong prob 차이 | F_t, true_wrong | gate reliability | 감소 | calibration만 좋고 task와 무관 가능 |
| MET-EVENT-001 | change-point F1 | event change-point detection F1 | true_change_point, pred_change | event handling | 상승 | visual diff detector로 축소 위험 |
| MET-EVENT-002 | reveal-vs-shift accuracy | reveal/shift/no-change classification accuracy or macro-F1 | true_reveal_vs_shift, pred_event | taxonomy | 상승 | ambiguous event 취약 |
| MET-SWITCH-002 | invalid switch rate | unnecessary/wrong hypothesis switches / all switches | switch_log, true_need_switch | switch safety | 감소 | valid switch reward hacking 탐지 |
| MET-REWRITE-001 | rewrite success rate | rewritten actions that become executable and progress-producing | rewrite_log, precondition, progress_delta | rewrite | 상승 | base-correct cases에서 regression 확인 필요 |
| MET-REWRITE-002 | unnecessary rewrite rate | base action correct였으나 rewrite로 악화된 비율 | base_action_outcome, rewritten_outcome | rewrite safety | 감소 | module이 base를 망치는지 탐지 |
| MET-COMP-001 | planning calls per episode | #decision_gate_on | planning_call_log | compute | 적정/감소 | underplanning 가능 |
| MET-COMP-002 | rollout steps per episode | sum simulated rollout transitions | rollout_trace | compute budget | matched | more compute confound |
| MET-COMP-003 | compute-normalized return | normalized_return / compute_budget | return, calls, rollout_steps | compute efficiency | 상승 | compute 정의 논쟁 |
| MET-COMP-004 | progress per compute | sum(progress_delta)/rollout_steps_or_calls | progress_delta, rollout_steps | VOC gate | 상승 | absolute return 낮을 수 있음 |
| MET-COMP-005 | false planning call rate | planning했지만 action/progress benefit 없는 비율 | planning_call, action_switch, progress_delta | overplanning | 감소 | benefit 정의 중요 |
| MET-COMP-006 | missed planning opportunity rate | planning 안 했지만 oracle alternative가 필요했던 비율 | gate, oracle_alt_needed | underplanning | 감소 | synthetic-only oracle 의존 |
| MET-COMP-007 | inference wall-clock proxy | agent decision elapsed time or estimated cost | timer, token_count, rollout_count | practicality | 감소/보고 | 환경별 노이즈 |
| MET-OOD-001 | ID-to-OOD performance drop | metric_ID - metric_OOD | split metrics | generalization | 감소 | aggregate가 split 실패 숨김 |
| MET-OOD-002 | OOD-regime recombination performance | target metrics on recombination split | split_id | regime generalization | 상승 | task difficulty confound |
| MET-OOD-003 | OOD-control grammar shift performance | target metrics on grammar shift split | split_id, grammar_id | core OOD | 상승 | 핵심 novelty split |
| MET-OOD-004 | OOD-timing/asynchrony robustness | false falsification/recovery under delayed/stale cases | delayed_effect_flag, split_id | timing robustness | 개선 | no-effect=falsification shortcut 탐지 |
| MET-HACK-001 | reward hacking indicator | invalid_switch + deliberate_failure + unnecessary_rewrite composite | switch/recovery/reward logs | objective safety | 감소 | reward claim 보호 |

---

## 7. Baseline Suite

| Baseline ID | Baseline | Inputs | Hidden Labels Used? | Planning Budget | What It Tests | Expected Strength | Expected Weakness |
|---|---|---|---|---|---|---|---|
| BASE-001 | Frozen Base VLM/LLM agent | public observation, same instruction | NO | 0 rollout | base confound 통제 | 실제 agent baseline | wrong grammar persistence 반복 |
| BASE-002 | Reactive DOM/text agent | current DOM/text only | NO | 0 | history/evidence 없는 reactive 비교 | 빠름/단순 | recovery 약함 |
| BASE-003 | Retry-after-failure agent | failure flag + previous action | NO | 0 | 단순 retry threat | transient failure 일부 해결 | wrong grammar 반복 가능 |
| BASE-004 | Base LLM self-correction | public obs + history + reflection prompt | NO | LLM call budget matched | self-correction threat | 강한 현실 baseline | structured posterior 없음 |
| BASE-005 | Verifier-only | obs + observed effect verification | NO | verification budget matched | VeriGUI-style threat | failed action 감지 강함 | alternative grammar/rewrite 없음 |
| BASE-006 | Verifier + heuristic recovery | verifier + hand rules | NO | matched | verification+recovery threat | modal/form에 강함 | OOD grammar 취약 |
| BASE-007 | Failure diagnosis only | trace + diagnosis | NO | offline/limited | AgentRx-style threat | 원인분석 가능 | closed-loop action 개선 약함 |
| BASE-008 | Rule-based blocker recovery | public obs + blocker rules | NO | 0 | blocker-specific baseline | modal/overlay에 강함 | taxonomy 확장 약함 |
| BASE-009 | Next-state-WM-only | obs + candidate action | NO | matched rollout | generic world model threat | future UI prediction 강함 | grammar posterior 없음 |
| BASE-010 | Always-plan world model | obs + WM + candidates | NO | reported or matched max | compute gate 필요성 | absolute return 높을 수 있음 | compute 비효율 |
| BASE-011 | Fixed-horizon planner | obs + WM | NO | fixed H=3 | MPC-style threat | 단순하고 강함 | decision relevance 없음 |
| BASE-012 | Uncertainty-gated planner | obs + uncertainty score | NO | matched | uncertainty vs falsification | 불확실성 높을 때 강함 | action choice 변화 고려 없음 |
| BASE-013 | Tree-search/MCTS-style planner | obs + action search tree | NO | matched nodes/rollouts | tree-search threat | 강한 search | hypothesis-level 비교 아님 |
| BASE-014 | Random alternative planner | obs + random grammar alternatives | NO | same top-k | alternative quality 검증 | 우연 탐색 control | 근거 없음 |
| BASE-015 | Compute-matched random reallocation | obs + random planning calls | NO | same calls/steps | compute만 쓴 효과 배제 | 공정 control | 무작위라 약함 |
| BASE-016 | Oracle regime | public obs + true regime | YES_ORACLE | matched | regime headroom | 상한 명확 | inference 불가 |
| BASE-017 | Oracle control grammar | public obs + true grammar | YES_ORACLE | matched | grammar headroom | core upper bound | inference 불가 |
| BASE-018 | Oracle alternative hypothesis | public obs + true helpful alternative | YES_ORACLE | matched | proposal upper bound | proposal gap 분해 | inference 불가 |
| BASE-019 | Oracle action precondition | public obs + true precondition | YES_ORACLE | matched | precondition error 상한 | executability error 제거 | grammar 전체는 아님 |
| BASE-020 | Oracle best action | public obs + oracle action | YES_ORACLE | minimal | environment upper bound | 최대 성능 | 비현실 |
| BASE-021 | Full FRCG-WM candidate | public obs + history + action-effect log | NO at inference | decision gate budget | proposed full | 핵심 mechanism | 복잡도 큼 |
| BASE-022 | Text-only FRCG prototype | symbolic text schema | NO at inference | small | smoke viability | 빠른 검증 | GUI realism 없음 |
| BASE-023 | DOM-only FRCG | DOM + history | NO | matched | modality ablation | 간단 | visual task 취약 |
| BASE-024 | DOM+log FRCG | DOM + structured action-effect log | NO | matched | evidence 중심 candidate | 핵심 mechanism에 적합 | visual ambiguity 취약 |
| BASE-025 | DOM+screenshot+log FRCG | DOM + screenshot + log | NO | matched | hybrid full candidate | 현실성 강화 | 복잡도/shortcut 위험 |
| BASE-026 | WAC-style consequence correction | obs + simulated consequence + correction | NO | matched | WAC direct threat | action correction 강함 | grammar persistence metric 약할 수 있음 |
| BASE-027 | CUWM-style candidate simulation | frozen base candidates + WM scoring | NO | matched | CUWM direct threat | frozen-agent WM search 강함 | grammar posterior 없음 |
| BASE-028 | WebWorld-style simulator search | obs + simulator + action search | NO | matched/reported | generic web WM threat | 강력한 WM baseline | 구현 난도/근사 필요 |

### 7.1 Baseline Implementation Fairness Rules

| Rule ID | Rule | Why Needed | Violation Consequence |
|---|---|---|---|
| BASE-RULE-001 | 모든 non-oracle baseline은 hidden label, counterfactual table, true grammar를 inference input으로 사용 금지 | leakage 방지 | 해당 결과 무효 |
| BASE-RULE-002 | Frozen Base VLM/LLM 모델, prompt, candidate action budget은 baseline 간 동일하게 고정 | base confound 제거 | “LLM이 좋아서 된 것” 공격 방어 실패 |
| BASE-RULE-003 | verifier-only baseline은 failed action detection과 heuristic recovery를 충분히 강하게 구현 | weak baseline 공격 방지 | novelty 과장 |
| BASE-RULE-004 | next-state-WM-only baseline은 가능한 동일 training data와 rollout budget 사용 | generic WM threat 공정 비교 | WM overlap 방어 실패 |
| BASE-RULE-005 | uncertainty-gated baseline은 FRCG와 동일 compute budget에서 비교 | decision gate claim 공정성 | compute confound |
| BASE-RULE-006 | oracle baselines는 upper bound로만 보고, proposed method와 동일 inference setting처럼 쓰지 않음 | oracle leakage 방지 | result misleading |
| BASE-RULE-007 | direct threat baseline 구현이 완전하지 않으면 `approximation_level`을 명시 | honesty | reviewer trust 하락 |

---

## 8. Ablation Suite

| Ablation ID | Removed/Changed Component | Connected Claim | Expected Metric Drop | If No Drop, What Collapses? | Severity |
|---|---|---|---|---|---|
| ABL-001 | no-regime | regime/control separation | regime shift F1, recovery delay | regime latent 필요성 약화 | HIGH |
| ABL-002 | no-control-grammar | core grammar claim | persistence, OOD grammar performance | 핵심 novelty 붕괴 | CRITICAL |
| ABL-003 | merged regime-control grammar | factorization claim | OOD recombination, interpretability, persistence | 분리 주장이 약화 | CRITICAL |
| ABL-004 | no-change-point | shift/reveal update | change-point F1, recovery delay | event handling 약화 | HIGH |
| ABL-005 | no-state latent | state belief necessity | progress prediction, return | state factor 불필요 가능 | MEDIUM |
| ABL-006 | collapsed latent | factorized latent claim | mechanism metrics and OOD | explicit factorization 폐기 가능 | CRITICAL |
| ABL-007 | no-auxiliary heads | auxiliary contribution | calibration/precondition/blocker metrics | aux head 필요성 약화 | MEDIUM |
| ABL-008 | hierarchical latent variant | architecture alternative | same metrics | main factorization 수정 가능 | MEDIUM |
| ABL-009 | no-screenshot | visual contribution | visual/layout OOD | screenshot claim 약화 | MEDIUM |
| ABL-010 | no-DOM | structured UI contribution | DOM/text OOD | DOM dependency 재검토 | MEDIUM |
| ABL-011 | no-action-effect-log | evidence claim | falsification PR, recovery delay | 핵심 evidence 경로 붕괴 | CRITICAL |
| ABL-012 | no L_action_effect | effect prediction | action-effect accuracy, rollout fidelity | WM effect 학습 필요성 약화 | HIGH |
| ABL-013 | no L_progress | planning value | progress error, return | progress value 약화 | HIGH |
| ABL-014 | no L_regime | regime inference | regime acc, OOD recombination | regime latent 약화 | HIGH |
| ABL-015 | no L_control_grammar | grammar inference | persistence, OOD grammar | core novelty 붕괴 | CRITICAL |
| ABL-016 | no L_falsification | falsification | falsification PR, false planning | verification과 차별 약화 | CRITICAL |
| ABL-017 | no L_intent_action_mapping | rewrite | rewrite success, failed repetition | action-interface rewrite 약화 | CRITICAL |
| ABL-018 | no recovery ranking | recovery | recovery delay | recovery path 약화 | MEDIUM |
| ABL-019 | no reward/progress training | reward path | return, progress per compute | reward가 metric일 뿐일 가능성 | HIGH |
| ABL-020 | no compute penalty | compute objective | planning calls, compute-normalized return | overplanning penalty 불필요 가능 | HIGH |
| ABL-021 | no valid switch reward | switch reward | adoption rate, invalid switch | switch reward 기여 약화 | MEDIUM |
| ABL-022 | no falsification score | planning trigger | falsification PR, recovery | 핵심 planning 붕괴 | CRITICAL |
| ABL-023 | uncertainty instead of falsification | falsification vs uncertainty | false planning, missed opportunity | uncertainty와 차별성 붕괴 | CRITICAL |
| ABL-024 | no alternative hypothesis | alternative planning | adoption/fidelity/recovery | alternative rollout claim 붕괴 | CRITICAL |
| ABL-025 | random alternative hypothesis | proposal quality | recovery, invalid switch | proposal이 무의미하면 claim 약화 | HIGH |
| ABL-026 | no short rollout | rollout | rollout-induced switch, recovery | rollout 불필요 가능 | HIGH |
| ABL-027 | horizon=1 | horizon sensitivity | recovery/progress/fidelity | 1-step 충분/부족 판단 | MEDIUM |
| ABL-028 | horizon=3 | main horizon | fidelity/return/compute | 3-step 과도하면 수정 | MEDIUM |
| ABL-029 | horizon=5 | compounding risk | fidelity, compute | long rollout instability 확인 | MEDIUM |
| ABL-030 | top-k=1 | alternative count | proposal recall | k=1 충분하면 k=3 약화 | MEDIUM |
| ABL-031 | top-k=3 | main candidate | recall/compute | main k 검증 | MEDIUM |
| ABL-032 | top-k=5 | compute/recall tradeoff | progress per compute | k=5가 좋으면 main 수정 | MEDIUM |
| ABL-033 | no decision-relevance gate | compute claim | false planning, compute-normalized return | gate 불필요 가능 | CRITICAL |
| ABL-034 | always-plan | compute gate | return vs compute | always-plan이 이기면 gate 약화 | CRITICAL |
| ABL-035 | no action rewrite | rewrite claim | failed repetition, switch delay | rewrite 핵심 붕괴 | CRITICAL |
| ABL-036 | no counterfactual target | rollout fidelity | alternative rollout fidelity | counterfactual supervision 약화 | HIGH |
| ABL-037 | no reveal-vs-shift head | event taxonomy | reveal/shift acc, invalid switch | taxonomy 약화 | HIGH |
| ABL-038 | no calibration loss | gate reliability | ECE, false planning | calibration 기여 약화 | MEDIUM |
| ABL-039 | base-action fallback disabled | rewrite safety | unnecessary rewrite rate | fallback 필요성 확인 | MEDIUM |
| ABL-040 | public evidence only vs hidden evidence leaked probe | leakage sanity | train/test gap, unrealistic jump | leakage 감지 | CRITICAL |
| ABL-041 | same success but no mechanism metric condition | mechanism necessity | persistence/recovery correlation | success-only claim 위험 | HIGH |
| ABL-042 | same compute but different candidate set | candidate budget | return/candidate eval | candidate confound 확인 | HIGH |

### 8.1 Ablation Interpretation Rules

```text
1. CRITICAL ablation이 expected collapse를 보이지 않으면 해당 claim은 FINAL_RESEARCH_BLUEPRINT.md에서 final core claim으로 쓰면 안 된다.
2. HIGH ablation이 무너지지 않으면 claim을 supporting claim 또는 appendix claim으로 낮춘다.
3. MEDIUM ablation이 무너지지 않으면 architecture simplification 후보로 기록한다.
4. ablation이 성능을 높이면 original component는 수정/폐기 후보로 재분류한다.
```

---

## 9. Experiment Suite

| Experiment ID | Purpose | Split/Data | Models Compared | Metrics | Claim Tested | Failure Interpretation |
|---|---|---|---|---|---|---|
| EXP-00 | Data/environment sanity and leakage audit | all generated data | schema auditor, leakage probes | leakage flags, class balance, split separation | valid evaluation foundation | leakage 있으면 전체 실험 무효 |
| EXP-01 | Text-only smoke test | text-only splits | text baselines + text-FRCG | persistence, failed repetition, recovery, progress/compute | mechanism viability | 실패 시 Web/GUI 진행 보류 |
| EXP-02 | Synthetic Web/GUI ID performance | SPLIT-001 | BASE-001..015 + FRCG variants | success, return, persistence | ID utility | ID 실패 시 method instability |
| EXP-03 | OOD-regime recombination | SPLIT-002 | baseline suite + latent variants | OOD return, recovery, regime error | regime generalization | regime claim 약화 |
| EXP-04 | OOD-control grammar shift | SPLIT-003 | verifier, next-state-WM, uncertainty, FRCG | persistence, recovery, OOD success | core grammar novelty | 핵심 novelty 약화 |
| EXP-05 | OOD-visual/layout perturbation | SPLIT-004 | DOM-only vs hybrid vs visual baselines | visual OOD drop, success | visual modality value | screenshot/hybrid claim 약화 |
| EXP-06 | OOD-DOM/text perturbation | SPLIT-005 | all public-input variants | OOD drop, falsification PR | shortcut 방지 | DOM/text shortcut 가능 |
| EXP-07 | OOD-timing/asynchrony | SPLIT-007 | verifier, uncertainty, FRCG | false falsification, recovery | delayed/no-effect robustness | no-effect shortcut 위험 |
| EXP-08 | OOD-reveal-vs-shift ambiguity | SPLIT-008 | no-reveal-shift vs full | event acc, invalid switch | event taxonomy | taxonomy 약화 |
| EXP-09 | OOD-long-horizon composition | SPLIT-010 | fixed horizon, always-plan, FRCG | return, recovery, length | short rollout scalability | long-horizon 한계 |
| EXP-10 | Compute-matched planning comparison | ID+all OOD | FRCG, always-plan, uncertainty, random gate | progress/compute, calls, rollouts | decision-relevant compute | more-compute attack 방어 실패 |
| EXP-11 | World model/rollout fidelity | counterfactual eval split | WM variants | effect acc, rollout fidelity | WM quality | fidelity 낮으면 rollout claim 약화 |
| EXP-12 | Falsification calibration | event/evidence eval | F score candidates | precision, recall, ECE | falsification claim | verification과 차별 약화 |
| EXP-13 | Latent factorization ablation | ID+OOD | 4-latent, merged, collapsed, hierarchical | persistence, OOD, probes | factorization | merged/collapsed가 이기면 수정 |
| EXP-14 | Objective/reward ablation | ID+OOD | objective variants | return, hack indicators | objective contribution | loss/reward 불필요 가능 |
| EXP-15 | Planning ablation | ID+OOD | planning variants | compute metrics, recovery | planning mechanism | gate/rollout/rewrite 약화 |
| EXP-16 | Qualitative failure analysis | predefined trace buckets | representative models | trace diagrams | mechanism explanation | cherry-pick 방지 필요 |
| EXP-17 | Optional real benchmark auxiliary validation | WebArena/VisualWebArena/OSWorld/WorkArena-like | best feasible baselines | success + weak proxies | external validity | synthetic-only limitation |
| EXP-18 | Reward hacking audit | stress cases | objective variants | invalid switch, deliberate failure, unnecessary rewrite | reward safety | reward claim 제한 |
| EXP-19 | Base model robustness | same splits, multiple frozen bases | weak/medium/strong base + module | module delta | LLM confound control | base-specific effect |

### 9.1 Minimum Viable Experiment Path

| MVE ID | Goal | Required Components | Required Outputs | Stop/Go Rule |
|---|---|---|---|---|
| MVE-10-A | text-only mechanism survival | text schema, base/verifier/ours-text, persistence metric | text metric CSV + failure traces | persistence/recovery 개선 없으면 Web/GUI 진행 보류 |
| MVE-10-B | synthetic DOM+log ID viability | DOM+log env, hidden labels, no leakage, base/verifier/ours | ID metric table + leakage audit | success/return 또는 mechanism metric 둘 다 실패하면 architecture/objective 재검토 |
| MVE-10-C | OOD-control grammar core test | held-out grammar split, no-control-grammar ablation | OOD grammar table | OOD grammar에서 no-control-grammar와 차이 없으면 core novelty 재정의 |
| MVE-10-D | compute gate sanity | always/uncertainty/random/FRCG gates | progress per compute table | FRCG가 compute frontier에 없으면 gate claim 보류 |
| MVE-10-E | direct threat mini-suite | verifier-only, next-state-WM-only, WAC/CUWM-style approximations | mechanism metric comparison | direct threat와 차이 없으면 novelty claim 축소 |

---

## 10. OOD Split Evaluation Plan

| Split ID | Split Name | What Changes | What Stays Fixed | Claim Tested | Required Metrics | Failure Interpretation |
|---|---|---|---|---|---|---|
| SPLIT-001 | ID test | held-out episodes only | task/regime/template distributions | base performance sanity | success, return, persistence | ID 실패 시 method 불안정 |
| SPLIT-002 | OOD-regime recombination | seen regimes in unseen compositions/order | individual regimes/templates | regime compositionality | OOD return, recovery | regime factor 약화 |
| SPLIT-003 | OOD-control grammar shift | same visual/layout/task but changed intent-action grammar | task/template/visual distribution | control grammar novelty | persistence, switch delay, OOD success | 핵심 novelty 약화 |
| SPLIT-004 | OOD-visual/layout perturbation | positions/styles/layout/viewport | grammar/task | visual robustness | visual OOD drop | visual encoder claim 약화 |
| SPLIT-005 | OOD-DOM/text perturbation | DOM names, labels, paraphrases | grammar/effect semantics | shortcut 방지 | OOD drop, falsification | DOM/text shortcut 가능 |
| SPLIT-006 | OOD-task composition | new subgoal combinations | primitive grammars | composition generalization | subgoal rate, return | long task 약화 |
| SPLIT-007 | OOD-timing/asynchrony | latency/stale/delayed effects | UI semantics | timing robustness | false falsification, recovery | delayed/no-effect 혼동 |
| SPLIT-008 | OOD-reveal-vs-shift ambiguity | ambiguous reveal/shift cases | task family | taxonomy robustness | event acc, invalid switch | taxonomy 약화 |
| SPLIT-009 | OOD-unseen UI template | new page templates/components | regime grammar | template generalization | OOD success, OOD drop | template memorization |
| SPLIT-010 | OOD-long-horizon composition | longer workflows/more pages | primitive grammars | planning scaling | return, recovery delay | short rollout 한계 |
| SPLIT-011 | OOD-distractor/decoy elements | additional plausible wrong targets | true grammar/task | shortcut resistance | invalid action rate | element shortcut 가능 |
| SPLIT-012 | OOD-base-agent-correct subset | base already correct cases isolated | episodes where base succeeds | rewrite safety | unnecessary rewrite rate | module regression 확인 |

---

## 11. Compute-Matched Evaluation Plan

| Compute Match ID | Matched Quantity | Why Needed | How To Enforce | Risk If Missing |
|---|---|---|---|---|
| CM-001 | planning calls | planning 빈도 증가 효과 제거 | per-episode call cap and logs | more calls attack |
| CM-002 | rollout step budget | world model rollout량 공정 비교 | same total simulated transitions | more rollout confound |
| CM-003 | wall-clock/inference proxy | 실사용 비용 비교 | timer/token/model-call/rollout-count logging | cost hidden |
| CM-004 | candidate action budget | action search 폭 통제 | same candidate count or report difference | candidate 수 차이 confound |
| CM-005 | top-k alternative budget | alternative exploration 폭 통제 | same k sweep | larger k effect |
| CM-006 | same frozen base model | LLM 성능 confound 제거 | identical model/version/prompt | LLM이 좋아서 된 것 |
| CM-007 | same observation input | modality confound 제거 | DOM-only/DOM+log/hybrid separately | 더 많은 정보 효과 |
| CM-008 | same training data | data scaling confound 제거 | same episodes and labels | 데이터 많아서 된 것 |
| CM-009 | same reward function | reward shaping confound 제거 | shared env return; learned objective separately reported | reward bias |
| CM-010 | same environment split | split difficulty confound 제거 | identical episode IDs | lucky split |
| CM-011 | same max action execution budget | retry-heavy methods와 planning methods 비교 공정성 | cap real actions per episode | longer acting wins |
| CM-012 | same external tool access | map/search/file access confound 제거 | tool access matrix | extra tool effect |

| Compute Metric ID | Metric | Definition | Used To Compare | Failure Interpretation |
|---|---|---|---|---|
| COMPUTE-MET-001 | planning calls per episode | number of gate-on calls | gate baselines | over/under-planning |
| COMPUTE-MET-002 | rollout steps per episode | total simulated transitions | WM planners | more rollout confound |
| COMPUTE-MET-003 | candidate evaluations | number of scored actions/hypotheses | search baselines | wider search confound |
| COMPUTE-MET-004 | compute-normalized return | return / compute budget | all planning methods | efficiency claim |
| COMPUTE-MET-005 | progress per compute | sum progress / rollout steps or calls | compute reallocation | efficiency vs absolute return conflict |
| COMPUTE-MET-006 | wall-clock proxy | elapsed decision time or proxy | practicality | implementation variability |
| COMPUTE-MET-007 | false planning call rate | planning with no action/progress benefit | gate quality | unnecessary compute |
| COMPUTE-MET-008 | missed planning opportunity rate | no planning when oracle alternative needed | underplanning | overly conservative gate |
| COMPUTE-MET-009 | token/model-call budget | LLM calls/tokens per episode | LLM-agent baselines | hidden API cost confound |

---

## 12. Statistical Reporting Protocol

| Reporting ID | Reporting Requirement | Why Needed | Suggested Method | Risk If Missing |
|---|---|---|---|---|
| REPORT-001 | number of seeds | variance와 reproducibility 확인 | 최소 3~5, main evidence는 가능하면 10 | single seed overclaim |
| REPORT-002 | mean/std | 기본 central tendency/variance | per split mean/std | variance 은폐 |
| REPORT-003 | median/IQR | skew/outlier robustness | episode return/recovery delay에 병행 | mean 왜곡 |
| REPORT-004 | confidence intervals | 차이 불확실성 보고 | bootstrap or t interval | 작은 차이 과장 |
| REPORT-005 | paired comparison | 동일 episode seed 기준 delta | paired bootstrap/delta table | unpaired noise 증가 |
| REPORT-006 | per-split reporting | OOD별 실패 확인 | ID/OOD table separate | aggregate가 실패 숨김 |
| REPORT-007 | effect size | statistical vs practical relevance | absolute/relative delta | p-value 과신 |
| REPORT-008 | compute budget report | planning cost 투명성 | calls/rollout/time/candidate logs | more-compute attack |
| REPORT-009 | negative result reporting | claim weakening discipline | failure interpretation table | cherry-pick 공격 |
| REPORT-010 | ablation non-effect reporting | component causality 정직성 | non-effect appendix/main table | claim 과장 |
| REPORT-011 | qualitative selection rule | trace cherry-pick 방지 | predefined buckets + random seeds | 선별 편향 |
| REPORT-012 | source/config versions | 재현성 | commit hash, env version, browser version | 재현 불가 |
| REPORT-013 | oracle gap decomposition | 상한과 method gap 해석 | oracle regime/grammar/alt/action rows | 실용성 판단 불가 |
| REPORT-014 | metric correlation matrix | success와 mechanism metric 관계 확인 | correlation/partial analysis | metric 독립성 공격 |

---

## 13. Reviewer Attack Defense Table

| Attack ID | Reviewer Attack | Required Evidence | Required Baseline/Ablation | If Defense Fails |
|---|---|---|---|---|
| ATTACK-DEF-001 | LLM이 좋아서 된 것 아닌가? | same Frozen Base + module off/on delta | BASE-001, BASE-004, same-base module ablation | module isolation claim 약화 |
| ATTACK-DEF-002 | world model novelty가 약하다 | next-state-WM-only보다 grammar shift metric 우위 | BASE-009, BASE-026~028, ABL-002 | generic WM으로 축소 |
| ATTACK-DEF-003 | VeriGUI/action-effect verification과 다르지 않다 | verifier-only보다 persistence/recovery/alt adoption 우위 | BASE-005, BASE-006, ABL-016/022 | verification+recovery 수준으로 약화 |
| ATTACK-DEF-004 | WebWorld/CUWM/WAC와 겹친다 | frozen WM/search baselines 대비 grammar metric 우위 | BASE-026, BASE-027, BASE-028 | related-work threat 방어 실패 |
| ATTACK-DEF-005 | 그냥 tree search다 | hypothesis-level metric과 compute-matched MCTS 비교 | BASE-013, PABL variants | planning novelty 약화 |
| ATTACK-DEF-006 | 그냥 uncertainty-gated planning이다 | uncertainty 대신 falsification ablation 비교 | BASE-012, ABL-023 | decision relevance claim 약화 |
| ATTACK-DEF-007 | control grammar는 말장난이다 | no-control-grammar/merged/collapsed collapse | ABL-002, ABL-003, ABL-006 | 핵심 개념 붕괴 |
| ATTACK-DEF-008 | synthetic environment가 toy다 | anti-leakage audit + many OOD splits + real auxiliary | EXP-00, SPLIT-003~012, EXP-17 | mechanism lab 가치 약화 |
| ATTACK-DEF-009 | hidden label이 비현실적이다 | hidden label은 train/eval only, real benchmark는 auxiliary limitation | observation extraction audit | synthetic-only claim으로 제한 |
| ATTACK-DEF-010 | reward가 실제로 작동하지 않는다 | reward-to-learning pathway + no-reward ablation | ABL-019, EXP-14, MET-HACK-001 | objective claim 약화 |
| ATTACK-DEF-011 | loss가 너무 많다 | main6 vs aux variants, non-effect reporting | objective variants | contribution 흐림 |
| ATTACK-DEF-012 | ablation이 claim을 지지하지 못한다 | claim-to-evidence master table | ABL suite | 해당 claim 약화/폐기 |
| ATTACK-DEF-013 | OOD split이 진짜 OOD가 아니다 | held-out factor and leakage audit | EXP-00, OOD split probes | generalization claim 약화 |
| ATTACK-DEF-014 | metric이 success rate와 독립적이지 않다 | mechanism metrics correlation/mediation report | MET-PERSIST/REC/FALS vs success | metric novelty 약화 |
| ATTACK-DEF-015 | compute를 더 쓴 것뿐이다 | compute-matched return/progress per compute | BASE-010, BASE-015, CM-* | compute claim 붕괴 |
| ATTACK-DEF-016 | oracle upper bound와 gap이 너무 크다 | oracle gap decomposition | BASE-016~020 | method 실용성 약화 |
| ATTACK-DEF-017 | real benchmark에서 안 먹힐 수 있다 | optional auxiliary validation and honest limitation | EXP-17 | external validity 제한 |
| ATTACK-DEF-018 | latent variables가 identifiable하지 않다 | merged/collapsed/hierarchical ablation + probes | ABL-003/006/008 | latent claim 약화 |
| ATTACK-DEF-019 | failure examples가 hand-crafted다 | procedural generation + randomized qualitative case selection | EXP-16 selection protocol | toy/cherry-pick 공격 |
| ATTACK-DEF-020 | negative result를 숨긴다 | failure interpretation protocol and non-effect reporting | Section 14, REPORT-009/010 | trustworthiness 약화 |
| ATTACK-DEF-021 | DOM/screenshot/log 중 하나만으로 충분하다 | modality ablations | BASE-023/024/025, ABL-009/010/011 | hybrid claim 약화 |
| ATTACK-DEF-022 | rewrite가 base action을 망친다 | base-correct subset과 unnecessary rewrite rate | SPLIT-012, MET-REWRITE-002 | rewrite safety 약화 |

---

## 14. Failure Interpretation Protocol

| Failure ID | Observed Result | Interpretation | Claim To Weaken/Drop | Required Follow-up |
|---|---|---|---|---|
| FAIL-001 | success rate는 오르지만 persistence가 안 줄어든다 | 성능 원인이 grammar persistence가 아님 | core mechanism/problem claim | metric correlation/qualitative trace 재검토 |
| FAIL-002 | persistence는 줄지만 success rate가 안 오른다 | mechanism은 작동하지만 utility 부족 | main performance claim | rewrite/progress objective 수정 |
| FAIL-003 | verifier-only와 비슷하다 | verification만으로 충분할 수 있음 | falsification novelty | hypothesis update/alternative metric 재검토 |
| FAIL-004 | uncertainty-gated와 비슷하다 | decision gate 차별성 약함 | decision-relevant compute claim | F score vs uncertainty decoupling split 강화 |
| FAIL-005 | next-state-WM-only와 비슷하다 | control grammar 없이도 충분 | grammar novelty | OOD grammar split/labels 재검토 |
| FAIL-006 | always-plan이 더 좋다 | gate가 성능 제한 | compute gate claim | compute-return frontier로 claim 축소 |
| FAIL-007 | no-control-grammar ablation이 안 무너진다 | grammar factor 불필요 | core novelty | taxonomy/label/architecture 재설계 |
| FAIL-008 | merged regime-control grammar가 더 좋다 | 분리 factorization 부적절 | separation claim | merged variant를 main 후보로 검토 |
| FAIL-009 | collapsed latent가 더 좋다 | explicit factorization 약함 | latent novelty | method를 planning/evidence 중심으로 재정의 |
| FAIL-010 | no-falsification ablation이 안 무너진다 | F score 불필요 | falsification claim | score/label 품질 검토 |
| FAIL-011 | no-reward model이 비슷하다 | reward contribution 약함 | objective/reward claim | reward를 metric/appendix로 하향 |
| FAIL-012 | compute penalty 때문에 성능이 떨어진다 | necessary planning 억제 | compute objective | β schedule/threshold 수정 |
| FAIL-013 | OOD-control grammar shift에서 실패한다 | 핵심 generalization 실패 | main novelty | grammar generator/training split 재설계 |
| FAIL-014 | OOD-reveal-vs-shift에서 실패한다 | event taxonomy 불안정 | reveal/shift claim | event labels/guardrail 수정 |
| FAIL-015 | text-only는 되지만 synthetic Web/GUI에서 실패한다 | symbolic artifact | transfer claim | DOM/log observation bridge 재검토 |
| FAIL-016 | synthetic은 되지만 real auxiliary에서 실패한다 | external validity 제한 | real-world claim | limitation으로 명시 |
| FAIL-017 | rollout fidelity가 낮다 | alternative planning 신뢰 약함 | rollout claim | horizon/objective/proposer 수정 |
| FAIL-018 | falsification calibration이 낮다 | gate 불안정 | falsification/gate claim | calibration loss/threshold 조정 |
| FAIL-019 | alternative proposal recall이 낮다 | true alternative를 못 찾음 | alternative rollout claim | proposal strategy 개선 |
| FAIL-020 | action rewrite가 base action을 망친다 | over-correction | rewrite claim | fallback/confidence guardrail 추가 |
| FAIL-021 | invalid switch rate가 증가한다 | switch reward/gate hacking | switch reward claim | valid-switch 조건 강화 |
| FAIL-022 | DOM-only가 hybrid와 비슷하다 | screenshot contribution 약함 | hybrid/screenshot claim | screenshot을 appendix로 하향 |
| FAIL-023 | hidden-label probe가 높은 정확도 shortcut 발견 | label leakage 또는 template shortcut | synthetic validity | environment/schema 재생성 |
| FAIL-024 | variance가 너무 크다 | effect 불안정 | all performance claims | seeds/episodes 늘리고 CI 보고 |

---

## 15. Minimum Publishable Evidence vs Main-Track-Level Evidence

### 15.1 Minimum Publishable Evidence

| Evidence ID | Required Result | Why Minimum | If Missing |
|---|---|---|---|
| MIN-EVID-001 | text-only smoke에서 persistence/recovery/falsification 개선 | mechanism viability 최소 조건 | Step 05/architecture 진행 보류 |
| MIN-EVID-002 | synthetic ID에서 base 대비 task utility 개선 | method가 task에 유용해야 함 | method utility 약화 |
| MIN-EVID-003 | no-control-grammar ablation 악화 | core component 최소 증거 | grammar claim 폐기/약화 |
| MIN-EVID-004 | verifier-only보다 recovery delay 개선 | verification과 차별 최소 증거 | falsification claim 약화 |
| MIN-EVID-005 | uncertainty-gate보다 progress per compute 개선 | compute gate 최소 증거 | planning novelty 약화 |
| MIN-EVID-006 | rollout fidelity가 random alternative보다 우위 | alternative rollout 최소 증거 | rollout claim 약화 |
| MIN-EVID-007 | falsification PR이 failed-action flag보다 우위 | falsification score 최소 증거 | verification으로 축소 |
| MIN-EVID-008 | leakage audit 통과 | synthetic 실험 유효성 최소 조건 | 전체 실험 무효 |

### 15.2 Main-Track-Level Evidence

| Evidence ID | Required Result | Why Main-Track-Level | If Missing |
|---|---|---|---|
| MAIN-EVID-001 | synthetic Web/GUI ID와 주요 OOD split 다수에서 일관 개선 | ID toy를 넘어선 설득력 | 메인트랙 주장 약화 |
| MAIN-EVID-002 | OOD-control grammar shift에서 verifier/WM/uncertainty 대비 명확한 우위 | 핵심 novelty split | core novelty 약화 |
| MAIN-EVID-003 | compute-matched progress per compute frontier 우위 | planning compute claim 방어 | 더 많이 생각한 효과 |
| MAIN-EVID-004 | no-control-grammar/no-falsification/no-alternative/no-rewrite 모두 expected collapse | component causality | method 구성 근거 약화 |
| MAIN-EVID-005 | merged/collapsed latent보다 factorized candidate가 mechanism metric 우위 | latent factorization 방어 | latent 분리 claim 약화 |
| MAIN-EVID-006 | falsification calibration과 rollout fidelity가 downstream recovery와 연결 | mechanism chain 검증 | metric만 좋고 task 무관 |
| MAIN-EVID-007 | reveal-vs-shift ambiguity split에서 invalid switch 억제 | taxonomy 방어 | event taxonomy 약화 |
| MAIN-EVID-008 | negative result와 failure cases를 사전 protocol대로 보고 | trustworthiness | reviewer 신뢰 하락 |
| MAIN-EVID-009 | optional real benchmark auxiliary에서 최소한 weak proxy 일관성 | synthetic-only 공격 완화 | external validity 제한 |
| MAIN-EVID-010 | strong direct threat baseline(WebWorld/CUWM/WAC/VeriGUI style) 대비 mechanism metric 우위 | related-work novelty 방어 | claim을 narrower workshop-level로 축소 |

---

## 16. Qualitative Failure Analysis Protocol

| Case Type ID | Case Type | Why Needed | Selection Rule | What To Show |
|---|---|---|---|---|
| CASE-001 | base agent repeated failure | core symptom 예시 | failure bucket에서 random seed로 선택 | same intent/action wrong repetition trace |
| CASE-002 | verifier-only recovery failure | verification 차별 | verifier succeeds/fails bucket | verification detects but wrong rewrite/no alt |
| CASE-003 | uncertainty-gate overplanning | compute gate 차별 | high uncertainty no action-switch cases | extra planning but no progress |
| CASE-004 | next-state-WM wrong action choice | grammar vs state prediction | state prediction correct but grammar action wrong cases | predicted state/effect mismatch |
| CASE-005 | FRCG correct grammar switch | positive mechanism | successful switch cases random | evidence→alt→rewrite→progress |
| CASE-006 | FRCG invalid switch failure | negative transparency | invalid switch bucket random | why gate/reward failed |
| CASE-007 | OOD-control grammar success | generalization evidence | OOD grammar successful cases | held-out grammar recovery |
| CASE-008 | OOD-control grammar failure | limitation | OOD grammar failed cases | proposal/rollout/rewrite failure point |
| CASE-009 | reveal-vs-shift ambiguity | taxonomy stress | ambiguous event split | delayed/noisy/reveal/shift distinction |
| CASE-010 | action rewrite regression | safety | base-correct but rewritten wrong | fallback need |
| CASE-011 | counterfactual oracle gap | proposal/rollout decomposition | oracle alt succeeds but ours fails | which component misses |
| CASE-012 | reward hacking trace | objective safety | invalid switch/repeated failure with reward | reward component analysis |

### 16.1 Qualitative Trace Display Contract

각 qualitative example은 다음 필드를 반드시 포함한다.

```yaml
case_id: string
split_id: string
task_family: string
base_agent_action_trace: list
frcg_action_trace: list
falsifying_evidence_step: int | null
current_hypothesis_before: string | redacted_if_hidden
alternative_hypothesis_selected: string | redacted_if_hidden_for_public_view
rewrite_action: string
observed_effect: string
progress_delta: float
failure_interpretation: string
why_this_case_was_selected: predefined_bucket_or_random_seed
```

주의:

- hidden labels는 paper figure용으로는 설명 목적에 한해 post-hoc annotation으로만 표시한다.
- agent observation에는 hidden labels가 들어가지 않았음을 caption 또는 appendix에서 명시한다.
- 성공 사례와 실패 사례를 모두 포함한다.

---

## 17. Evaluation Stress Test Ledger

| Stress ID | Attack | Evaluation Failure Mode | Detection Method | Required Revision | Affected Claim |
|---|---|---|---|---|---|
| ESTRESS-001 | metric이 hidden labels에 과의존 | real auxiliary와 연결 약함 | hidden-required vs public-proxy metric 분리 | public proxy table 추가 | external validity |
| ESTRESS-002 | OOD split이 train과 너무 비슷 | generalization 과장 | held-out factor audit | split generator 수정 | OOD claim |
| ESTRESS-003 | task family가 regime shortcut | grammar classifier shortcut | task↔grammar MI/probe | balance and decoy tasks | grammar claim |
| ESTRESS-004 | compute-matched baseline 불공정 | planning claim 무효 | budget logs audit | same budget runner | compute claim |
| ESTRESS-005 | oracle upper bound 비현실 | gap 해석 불가 | oracle levels separate | oracle regime/grammar/alt/action 분해 | utility |
| ESTRESS-006 | baseline 구현 약함 | ours 과대평가 | strong/weak baseline tier report | best-effort public baselines | novelty |
| ESTRESS-007 | ablation isolation 실패 | component causality 불명 | single-change ablation | factorial subset | component claim |
| ESTRESS-008 | multiple losses로 해석 어려움 | objective contribution 흐림 | main-only/aux-only/staged variants | objective simplification | objective claim |
| ESTRESS-009 | success와 mechanism metric 충돌 | claim 모순 | claim-to-metric priority rule | failure protocol 실행 | mechanism |
| ESTRESS-010 | falsification precision high recall low | missed recovery | PR curve/AUC | threshold tuning/report | falsification |
| ESTRESS-011 | recovery delay 줄지만 invalid switch 증가 | reward/gate hacking | invalid switch metric | valid-switch conditions 강화 | reward/gate |
| ESTRESS-012 | progress per compute 높지만 absolute return 낮음 | efficiency-only method | return-efficiency frontier | claim scope 제한 | compute |
| ESTRESS-013 | OOD 개선이 한 split에만 존재 | generalization 과장 | per-split reporting | claim을 해당 split으로 제한 | OOD |
| ESTRESS-014 | visual modality contribution 불명확 | hybrid complexity 정당화 실패 | modality ablation | screenshot claim 하향 | architecture |
| ESTRESS-015 | statistical variance 큼 | effect 불확실 | CI/paired/bootstrap | more seeds/episodes | all |
| ESTRESS-016 | qualitative examples cherry-picked | trust 하락 | predefined buckets/random seeds | case protocol | reporting |
| ESTRESS-017 | real benchmark 부재 공격 | external validity 약함 | aux benchmark or limitation | optional EXP-17 | external |
| ESTRESS-018 | hidden label metric real-world 확장 어려움 | deployment claim 제한 | synthetic-vs-real metric map | claim scope 명시 | external |
| ESTRESS-019 | always-plan이 unlimited compute에서 이김 | absolute performance 공격 | compute frontier | efficiency claim으로 제한 | planning |
| ESTRESS-020 | negative protocol 없음 | overclaim | failure interpretation table | claim drop rule | trust |
| ESTRESS-021 | WebWorld/CUWM/WAC baseline 근사 부정확 | direct threat 방어 약함 | faithfulness checklist | baseline caveat | related work |
| ESTRESS-022 | agent prompt differences | base confound | prompt/version lock | same prompt harness | base isolation |
| ESTRESS-023 | data leakage through screenshot/file path | split/regime shortcut | filename sanitization + probes | path randomization | data validity |
| ESTRESS-024 | counterfactual table leakage | oracle-like performance | visibility assertion | shard isolation | synthetic validity |
| ESTRESS-025 | reporting only best checkpoint | selection bias | predefined model selection metric | valid-only selection | reporting |

---

## 18. Implementation-Ready Evaluation Runner Contract

### 18.1 Required Output Folder Structure

```text
outputs/eval_runs/{run_id}/
  config.yaml
  source_versions.json
  metrics_summary.csv
  metrics_by_split.csv
  metrics_by_seed.csv
  compute_budget.csv
  ablation_summary.csv
  baseline_summary.csv
  failure_interpretation.md
  leakage_audit.json
  qualitative_cases/
    case_index.csv
    traces/*.jsonl
    figures/*.png
```

### 18.2 Required Evaluation Config Schema

```yaml
run_id: frcgw_eval_YYYYMMDD_HHMM
base_model:
  provider: string
  model_id: string
  frozen: true
  prompt_version: string
splits:
  - SPLIT-001
  - SPLIT-003
  - SPLIT-007
methods:
  - BASE-001
  - BASE-005
  - BASE-009
  - BASE-012
  - BASE-021
ablations:
  - ABL-002
  - ABL-016
  - ABL-024
  - ABL-033
compute_matching:
  match_planning_calls: true
  match_rollout_steps: true
  match_candidate_actions: true
metrics:
  core:
    - MET-PERSIST-001
    - MET-REC-001
    - MET-FALS-001
    - MET-COMP-004
seeds: [0, 1, 2, 3, 4]
reporting:
  confidence_interval: bootstrap
  paired_comparison: true
  negative_results: true
```

### 18.3 Required Runtime Assertions

```python
def assert_evaluation_integrity(batch):
    forbidden_in_agent_input = {
        "true_regime",
        "true_control_grammar",
        "true_change_point",
        "true_reveal_vs_shift",
        "counterfactual_action_effects",
        "oracle_best_action",
        "oracle_alternative_hypothesis",
    }
    for obs in batch["agent_observations"]:
        assert forbidden_in_agent_input.isdisjoint(obs.keys())

    assert batch["config"]["base_model"]["frozen"] is True
    assert "split_id" in batch["metadata"]
    assert "seed" in batch["metadata"]
    assert "method_id" in batch["metadata"]
```

### 18.4 Metric Computation Dependency Contract

| Metric | Required Trace Fields | If Missing |
|---|---|---|
| MET-PERSIST-001 | `selected_hypothesis`, `true_control_grammar`, `evidence_time`, `step_index` | cannot compute core metric |
| MET-REC-001 | `falsifying_evidence_step`, `progress_delta`, `step_index` | recovery claim blocked |
| MET-FALS-001/002 | `F_t`, `true_wrong_hypothesis` | falsification claim blocked |
| MET-WM-001 | `predicted_rollout`, `counterfactual_effects` | rollout fidelity blocked |
| MET-COMP-004 | `progress_delta`, `planning_calls`, `rollout_steps` | compute claim blocked |
| MET-REWRITE-002 | `base_action_outcome`, `rewritten_action_outcome` | rewrite safety blocked |

---

## 19. Required Design Revisions From Evaluation Analysis

| Revision ID | Evaluation Issue | Required Revision | Affected Final Blueprint Section | Severity |
|---|---|---|---|---|
| REV-10-001 | success-only evaluation risk | mechanism metrics를 final claim table의 first-class evidence로 승격 | Evaluation / Claims | CRITICAL |
| REV-10-002 | direct threat baselines 부족 | WebWorld/CUWM/WAC/VeriGUI-style approximations 명시 | Related Work / Experiments | CRITICAL |
| REV-10-003 | compute fairness risk | compute-matched runner schema 도입 | Experiments | CRITICAL |
| REV-10-004 | OOD split ambiguity | held-out factor와 leakage audit 필수 | Environment / Evaluation | HIGH |
| REV-10-005 | latent claim 위험 | merged/collapsed/no-control-grammar ablations 필수 | Architecture / Evaluation | CRITICAL |
| REV-10-006 | reward hacking 위험 | invalid switch/deliberate failure metric 추가 | Objective / Evaluation | HIGH |
| REV-10-007 | real benchmark label gap | real validation은 auxiliary로 제한 | Limitations | HIGH |
| REV-10-008 | qualitative cherry-pick 위험 | predefined case selection protocol 추가 | Failure Analysis | MEDIUM |
| REV-10-009 | baseline weakness risk | baseline implementation fairness rules 추가 | Experiments | HIGH |
| REV-10-010 | negative result handling 부족 | failure interpretation protocol을 final blueprint 필수 섹션으로 전달 | Final Blueprint | CRITICAL |

---

## 20. Handoff to FINAL_RESEARCH_BLUEPRINT.md

| Handoff ID | Target File | What Must Be Used | What Must Be Verified | What Must Not Be Claimed |
|---|---|---|---|---|
| HANDOFF-10-001 | FINAL_RESEARCH_BLUEPRINT.md | Claim-to-Evidence Master Table | every final claim has metric/baseline/ablation | claim without evidence |
| HANDOFF-10-002 | FINAL_RESEARCH_BLUEPRINT.md | Metric Definition Table | core mechanism metrics are prioritized over success-only | success-only novelty |
| HANDOFF-10-003 | FINAL_RESEARCH_BLUEPRINT.md | Baseline Suite | direct threats included | weak-baseline result |
| HANDOFF-10-004 | FINAL_RESEARCH_BLUEPRINT.md | Ablation Suite | CRITICAL ablations assigned to final claims | no-control-grammar claim without ablation |
| HANDOFF-10-005 | FINAL_RESEARCH_BLUEPRINT.md | Compute-Matched Plan | planning claims have compute budget | more-compute advantage |
| HANDOFF-10-006 | FINAL_RESEARCH_BLUEPRINT.md | Failure Protocol | negative outcomes weaken/drop claims | unconditional success claim |
| HANDOFF-10-007 | FINAL_RESEARCH_BLUEPRINT.md | Minimum/Main-Track Evidence | final blueprint separates minimum vs main-track evidence | acceptance-level evidence already exists |
| HANDOFF-10-008 | FINAL_RESEARCH_BLUEPRINT.md | Limitations from risks | synthetic/hidden-label/real-benchmark limitations | real deployment validation |

---

## 21. Updated Risk / Unknown Ledger

| Risk ID | Risk / Unknown | Handling | Can Be Final Claim? |
|---|---|---|---|
| RISK-10-001 | control grammar가 말장난으로 보일 위험 | no-control-grammar/merged ablation and OOD grammar split | NO until passed |
| RISK-10-002 | synthetic environment toy risk | anti-leakage + OOD + real auxiliary | NO |
| RISK-10-003 | compute-matched comparison 불공정 | budget logger and same runner | NO |
| RISK-10-004 | VeriGUI와 차별 실패 | verifier-only baseline | NO |
| RISK-10-005 | WebWorld/CUWM/WAC overlap | direct threat baselines or explicit limitation | NO |
| RISK-10-006 | latent identifiability failure | merged/collapsed/probes | NO |
| RISK-10-007 | reward hacking | hack indicators and invalid switch metrics | NO |
| RISK-10-008 | hidden label leakage | visibility assertions and probes | NO |
| RISK-10-009 | real benchmark hidden labels 부재 | auxiliary only framing | NO |
| RISK-10-010 | base LLM confound | same frozen base + module off/on | NO |
| RISK-10-011 | metric-success conflict | claim priority/failure protocol | NO |
| RISK-10-012 | falsification calibration low | calibration loss/threshold tuning | NO |
| RISK-10-013 | alternative proposal recall low | proposal strategy/k sweep | NO |
| RISK-10-014 | rewrite regression | base-correct subset and fallback | NO |
| RISK-10-015 | variance high | more seeds/CI | NO |
| RISK-10-016 | baseline implementation weak | strong/weak tiering and caveat | NO |
| RISK-10-017 | OOD split shortcut | MI/probe audits | NO |
| RISK-10-018 | loss complexity | objective ablation and main/aux separation | NO |
| RISK-10-019 | qualitative cherry-pick | predefined selection protocol | NO |
| RISK-10-020 | oracle gap too large | oracle decomposition | NO |

---

## 22. Quality Gate Result

| Gate ID | Gate | PASS/FAIL/PARTIAL | Evidence | If Not PASS |
|---|---|---|---|---|
| QG-10-01 | 00~09 refs imported | PASS | source file depends_on and imported references preserved/enhanced | none |
| QG-10-02 | citation-grade source anchor ledger added | PASS | SRC-EVAL-001..012 | Step FINAL may add bibliography |
| QG-10-03 | claim-to-evidence table 작성 | PASS | 12 final evidence claims | none |
| QG-10-04 | metric 30개 이상 정의 | PASS | 36 metrics | none |
| QG-10-05 | baseline 25개 이상 설계 | PASS | 28 baselines | none |
| QG-10-06 | ablation 35개 이상 설계 | PASS | 42 ablations | none |
| QG-10-07 | experiment suite 18개 이상 | PASS | 20 experiments | none |
| QG-10-08 | OOD split plan 10개 이상 | PASS | 12 OOD/ID splits | none |
| QG-10-09 | compute-matched plan 작성 | PASS | 12 matching quantities + compute metrics | none |
| QG-10-10 | statistical reporting protocol 작성 | PASS | 14 reporting requirements | none |
| QG-10-11 | reviewer attack defense 20개 이상 | PASS | 22 attacks | none |
| QG-10-12 | failure interpretation protocol 20개 이상 | PASS | 24 failure rules | none |
| QG-10-13 | minimum vs main-track evidence 분리 | PASS | 8 minimum + 10 main-track | none |
| QG-10-14 | qualitative failure analysis protocol 작성 | PASS | 12 case types | none |
| QG-10-15 | implementation-ready runner contract 포함 | PASS | Section 18 YAML/runner/schema contract | none |
| QG-10-16 | no empirical result fabricated | PASS | all entries are required evidence, no numbers reported | none |
| QG-10-17 | FINAL blueprint not prematurely written | PASS | handoff only | none |

---

## 23. Final Statement of This File

```text
10_EVALUATION_BASELINE_ABLATION.md is an evaluation contract file, not an empirical result section.

The strongest evaluation requirements are:
- Every final claim must have a metric, baseline, ablation, split, pass condition, and failure interpretation.
- The core mechanism must be evaluated with persistence, recovery, falsification, rollout fidelity, rewrite, and compute metrics, not success rate alone.
- Direct threat baselines must include verifier-only, next-state-WM-only, uncertainty-gated planning, always-plan world model, tree-search/MCTS-style planner, and WAC/CUWM/WebWorld-style approximations where feasible.

The most dangerous evaluation risks are:
- no-control-grammar ablation does not hurt,
- verifier-only or next-state-WM-only matches FRCG-WM,
- compute-matched comparison is unfair,
- synthetic leakage creates shortcut performance,
- mechanism metrics and success rate disagree.

The claims that must be weakened if evidence fails are:
- If no-control-grammar ablation does not collapse, weaken or drop the control grammar novelty claim.
- If verifier-only matches recovery and persistence metrics, reduce falsification novelty to verification-plus-recovery.
- If uncertainty-gated planning matches progress per compute, weaken the decision-relevant compute claim.
- If next-state-WM-only matches OOD-control grammar shift, weaken the grammar-world-model claim.
- If no-reward/progress training matches full objective, weaken the reward/objective contribution claim.

The next required file is:
FINAL_RESEARCH_BLUEPRINT.md
```
