---
file_id: FINAL
title: Final Research Blueprint for FRCG-WM
version: v1.0_10score
status: final_research_blueprint_not_empirical_paper
language: ko
last_updated: 2026-05-08
source_input:
  - /mnt/data/붙여넣은 마크다운(1)(85).md
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
  - 10_EVALUATION_BASELINE_ABLATION.md
purpose:
  - Step 00~10의 모든 설계 산출물을 하나의 연구 설계도와 Claude Code 실행 context로 통합한다.
  - final claim, method, objective, planning, evaluation, ablation, failure interpretation을 1:1로 고정한다.
  - 연구 아이디어를 과장하지 않고, 실험 전 claim / 실험 후 claim / 폐기 조건을 분리한다.
  - Claude Code가 필요한 context를 확장적으로 읽고 구현·검증 작업을 시작할 수 있도록 routing, MVE, gate, file contract를 명시한다.
forbidden:
  - Do not fabricate empirical results.
  - Do not claim acceptance-level evidence.
  - Do not hide unresolved unknowns.
  - Do not introduce unsupported new core claims.
  - Do not treat this blueprint as a completed empirical paper.
  - Do not use hidden labels as inference inputs.
  - Do not evaluate planning claims without compute-matched baselines.
  - Do not promote SOURCE_ONLY or UNKNOWN items into final claims.
---

# FINAL_RESEARCH_BLUEPRINT.md

## 0. Claude Code Usage Contract

이 파일은 최종 논문 원고가 아니라 **Claude Code가 연구·구현·실험 설계를 이어가기 위한 최상위 context router**다. Claude Code는 이 파일을 먼저 읽고, 작업 목적에 따라 세부 MD를 확장적으로 읽어야 한다.

### 0.1 Read Policy

| 작업 의도 | 반드시 먼저 읽을 파일 | 이어서 읽을 파일 | 절대 가정하지 말 것 |
|---|---|---|---|
| 전체 연구 방향 파악 | `FINAL_RESEARCH_BLUEPRINT.md` | `00_MASTER_REFERENCE.md` | blueprint가 empirical result paper라고 가정 금지 |
| novelty 방어/관련연구 정리 | `01_RELATED_WORK_THREAT_MAP.md` | `02`, `10`, `FINAL` | WebWorld/CUWM/WAC/VeriGUI와 차별성이 자동으로 해결됐다고 가정 금지 |
| 문제정의 재작성 | `02_PROBLEM_NOVELTY_FALSIFICATION.md` | `03`, `10`, `FINAL` | wrong-control-grammar persistence가 이미 독립 failure로 증명됐다고 가정 금지 |
| 개념 정의 수정 | `03_CORE_CONCEPT_TAXONOMY.md` | `06`, `07`, `09`, `FINAL` | control grammar를 단순 action precondition으로 축소 금지 |
| text-only smoke 구현 | `04_TEXT_ONLY_SMOKE_TESTBED.md` | `08`, `09`, `10`, `FINAL` | text-only 성공을 Web/GUI 성공으로 일반화 금지 |
| synthetic Web/GUI 구현 | `05_SYNTHETIC_WEB_GUI_ENVIRONMENT.md` | `06`, `07`, `10`, `FINAL` | hidden labels를 observation으로 제공 금지 |
| schema/loader/assertion 구현 | `06_DATA_SCHEMA_AND_LABELING.md` | `05`, `08`, `10` | counterfactual table을 agent input에 넣지 말 것 |
| architecture 구현 | `07_LATENT_ARCHITECTURE_DESIGN.md` | `06`, `08`, `09`, `10` | 4-latent가 최종 정답이라고 가정 금지 |
| loss/reward 구현 | `08_LOSS_REWARD_TRAINING_OBJECTIVE.md` | `06`, `07`, `09`, `10` | reward가 metric으로만 존재해도 된다고 가정 금지 |
| planning 알고리즘 구현 | `09_PLANNING_THEORY_ALGORITHM.md` | `07`, `08`, `10` | uncertainty-gate와 falsification-gate를 동일시 금지 |
| evaluation runner 구현 | `10_EVALUATION_BASELINE_ABLATION.md` | `06`, `08`, `09`, `FINAL` | success rate만으로 claim 검증 금지 |

### 0.2 Claude Code Output Rule

Claude Code는 이 blueprint를 읽고 코드를 작성할 때 반드시 다음 순서를 따른다.

1. `context routing`으로 필요한 하위 MD를 선택한다.
2. 선택한 MD의 `forbidden`, `quality gate`, `unknown`, `handoff`를 먼저 읽는다.
3. 구현 전 `MVE Scope`를 확정한다.
4. 코드 작성 전 `schema visibility assertion`을 작성한다.
5. 실험 실행 전 `baseline/ablation runner contract`를 작성한다.
6. 결과를 해석할 때 `failure interpretation protocol`을 먼저 적용한다.

---

## 1. Executive Summary

본 연구의 임시 이름은 **FRCG-WM: Falsification-guided Regime-Control-Grammar World Model**이다. 핵심 아이디어는 Web/GUI agent의 실패를 단순 action failure나 visual grounding failure로만 보지 않고, **현재 UI에서 intent가 어떤 executable action 또는 action macro로 실현되는지에 대한 잘못된 control-grammar hypothesis를 agent가 오래 유지하는 현상**으로 정의하고, 이를 측정·완화하는 것이다.

이 blueprint는 empirical paper가 아니다. 아직 실험 결과, acceptance-level evidence, final model claim은 존재하지 않는다. 이 문서는 `무엇을 주장할 수 있는지`, `무엇을 실험으로 검증해야 하는지`, `어떤 결과가 나오면 어떤 claim을 약화/폐기해야 하는지`를 연구 설계 차원에서 고정한다.

### 1.1 제목 후보

| Rank | Title Candidate | 장점 | 위험 | 현재 결정 |
|---:|---|---|---|---|
| 1 | **Wrong-Hypothesis-Aware Planning for Web/GUI Agents via Latent Control-Grammar World Models** | 문제·방법·도메인이 모두 드러난다 | 길다 | 1순위 |
| 2 | **Falsification-Guided Control-Grammar Planning for Web and GUI Agents** | falsification과 grammar를 전면화한다 | world model contribution이 약해 보일 수 있음 | 2순위 |
| 3 | **Reducing Wrong Control-Grammar Persistence in Web Agents** | problem metric 중심으로 날카롭다 | 방법 범위가 작아 보일 수 있음 | 대체 제목 |
| 4 | **Falsifiable Interaction Hypotheses for Reliable Web/GUI Agents** | 이론적 framing이 좋다 | control grammar 명시성 약함 | 보류 |
| 5 | **Regime-Control World Models for Robust GUI Agent Planning** | 짧고 직관적 | generic world model threat에 취약 | 비추천 |

### 1.2 한 문장 thesis

> Web/GUI agent의 반복 실패 중 일부는 current intent-to-action control-grammar hypothesis가 action-effect evidence에 의해 반증된 뒤에도 업데이트되지 않아 발생할 수 있으며, FRCG-WM은 hidden regime/control-grammar posterior, evidence-likelihood falsification, alternative grammar rollout, decision-relevant compute gate, action-interface rewrite를 결합해 이 persistence를 측정하고 줄일 수 있는지 검증한다.

### 1.3 핵심 설계 요약

| 축 | 최종 설계 후보 | 반드시 검증해야 할 것 |
|---|---|---|
| Problem | wrong-control-grammar hypothesis persistence | action failure, grounding failure, verification failure, generic planning failure와 분리되는가 |
| Data | synthetic Web/GUI causal laboratory + optional real benchmark auxiliary | hidden label leakage가 없는가, synthetic toy가 아닌가 |
| Architecture | Frozen Base VLM/LLM + FRCG-WM module | base LLM 효과와 proposed module 효과가 분리되는가 |
| Latent | `z_state`, `z_regime`, `z_control_grammar`, `z_change_point` + auxiliary heads | merged/collapsed latent보다 나은가 |
| Objective | `L_action_effect`, `L_progress`, `L_regime`, `L_control_grammar`, `L_falsification`, `L_intent_action_mapping` | 각 loss가 metric/ablation에 실제로 작동하는가 |
| Planning | likelihood-ratio falsification → top-k alternative hypothesis → short rollout → VOC gate → rewrite | uncertainty-gate/tree-search/next-state-WM과 구분되는가 |
| Evaluation | claim→metric→baseline→ablation→failure interpretation | success rate만이 아니라 mechanism metric이 개선되는가 |

---

## 2. Citation-Grade External Anchor Ledger

이 표는 final claim을 확정하는 근거가 아니라, related work와 evaluation framing의 anchor다. 각 논문/도구는 Step 01과 Step 10에서 더 깊게 비교되어야 한다.

| Anchor ID | Source | 확인된 역할 | FRCG-WM에 대한 의미 | Blueprint Usage |
|---|---|---|---|---|
| SRC-WEB-001 | WebArena, arXiv:2307.13854, https://arxiv.org/abs/2307.13854 | realistic, reproducible web benchmark; functional correctness 중심 | external benchmark anchor. hidden grammar label은 없음 | optional auxiliary validation |
| SRC-WEB-002 | VisualWebArena, arXiv:2401.13649, https://arxiv.org/abs/2401.13649 | multimodal/visually grounded realistic web tasks | visual grounding benchmark threat/anchor | optional auxiliary + modality discussion |
| SRC-WEB-003 | OSWorld, NeurIPS 2024, https://arxiv.org/abs/2404.07972 | 369 real computer tasks with execution-based evaluation | realistic computer-use benchmark anchor | optional auxiliary validation |
| SRC-WEB-004 | BrowserGym, arXiv:2412.05467, https://arxiv.org/abs/2412.05467 | unified Gym-like web agent environment including WebArena/WorkArena/MiniWoB++ | evaluation harness와 reproducibility anchor | future harness integration |
| SRC-WEB-005 | WebWorld, arXiv:2602.14721, https://arxiv.org/abs/2602.14721 | large-scale open-web world model, long-horizon simulation, inference-time search | generic web world model novelty를 직접 위협 | must beat/position against |
| SRC-WEB-006 | CUWM, arXiv:2602.17365, https://arxiv.org/abs/2602.17365 | frozen agent가 candidate action을 world model로 simulate/compare | frozen agent + WM test-time search threat | next-state-WM/CUWM-style baseline |
| SRC-WEB-007 | WAC, arXiv:2602.15384, https://arxiv.org/abs/2602.15384 | consequence simulation + feedback-driven action correction | action correction/WM augmentation direct threat | WAC-style baseline |
| SRC-WEB-008 | VeriGUI, arXiv:2604.05477, https://arxiv.org/abs/2604.05477 | action-effect verification and self-correction with robust SFT/GRPO | verification/recovery direct threat | verifier-only baseline |

**Positioning rule:** FRCG-WM은 “web world model”이나 “action-effect verification”만으로 주장하면 direct threat에 먹힌다. 최종 novelty는 반드시 `wrong-control-grammar persistence metric`, `current-vs-alternative grammar hypothesis falsification`, `decision-relevant compute`, `action-interface rewrite`의 결합으로 좁혀야 한다.

---

## 3. Final Claim Consolidation

최종 core claim은 3~5개로 제한한다. 아래 5개 외 claim은 supporting claim, experimental hypothesis, future work, 또는 limitation으로 처리한다.

| Claim ID | Final Claim | Status | Required Evidence | If Evidence Fails |
|---|---|---|---|---|
| FC-01 | wrong-control-grammar hypothesis persistence는 Web/GUI agent의 반복 실패를 설명하는 분리 가능한 측정 후보 failure mode다 | FINAL_CORE_CLAIM | persistence time, repeated invalid mapping, competing explanation falsification | problem claim을 “candidate mechanism”으로 약화 |
| FC-02 | regime/control grammar factorization은 recovery와 action-interface switch에 기여하는지 검증할 수 있는 architecture hypothesis다 | FINAL_CORE_CLAIM | no-control-grammar, merged, collapsed ablation | factorization claim 폐기 또는 merged 구조로 수정 |
| FC-03 | action-effect evidence는 단순 verification을 넘어 current hypothesis falsification과 alternative proposal에 사용할 수 있다 | FINAL_CORE_CLAIM | falsification P/R, calibration, verifier-only comparison | VeriGUI-style verification과 차별성 약화 |
| FC-04 | alternative control-grammar rollout과 action-interface rewrite는 failed-action repetition과 recovery delay를 줄일 수 있는지 검증한다 | FINAL_CORE_CLAIM | alternative rollout fidelity, no-alternative/no-rewrite ablation | rollout/rewrite claim 약화 |
| FC-05 | decision-relevant compute gate는 uncertainty-gated/always-plan baseline 대비 progress per compute를 개선할 수 있는지 검증한다 | FINAL_CORE_CLAIM | compute-matched return, progress per compute, false planning rate | “더 많이 생각한 효과”로 축소 |

### 3.1 Supporting Claims

| Claim ID | Supporting Claim | 왜 supporting인가 | Required Evidence |
|---|---|---|---|
| SC-01 | text-only smoke test는 mechanism viability gate다 | 메인 기여가 아니라 조기 검증 장치 | text gate 통과 |
| SC-02 | synthetic Web/GUI는 causal mechanism evaluation laboratory다 | hidden/counterfactual label을 제공하지만 real-world 한계 존재 | leakage audit + OOD suite |
| SC-03 | real WebArena/OSWorld류 benchmark는 auxiliary validation이다 | hidden grammar label이 없어 mechanism metric 불완전 | weak proxy + qualitative trace |
| SC-04 | base model 고정은 module effect isolation을 돕는다 | LLM 성능 confound 방지 장치 | same-base off/on comparison |
| SC-05 | reveal-vs-shift taxonomy는 invalid switch 방지에 도움이 될 수 있다 | auxiliary taxonomy claim | reveal-vs-shift ablation |

### 3.2 Drop / Unknown Claims

| Claim | Decision | Reason |
|---|---|---|
| FRCG-WM이 모든 Web/GUI agent failure를 해결한다 | DROP | 과장, 실험 불가능 |
| 4-latent 구조가 최종 정답이다 | UNKNOWN_DO_NOT_CLAIM | collapsed/merged/hierarchical 비교 전 확정 불가 |
| hidden labels 없이 real-world에서도 동일 metric이 측정된다 | DROP_OR_FUTURE | real benchmark에는 hidden grammar/counterfactual label 부재 |
| screenshot feature가 반드시 필요하다 | EXPERIMENTAL_ONLY | DOM-only vs hybrid ablation 필요 |
| valid switch reward가 항상 성능을 올린다 | EXPERIMENTAL_ONLY | reward hacking 위험 |

---

## 4. Problem Definition

### 4.1 Working Definition

`wrong-control-grammar hypothesis persistence`란 agent가 다음 조건을 만족하는 상태를 말한다.

1. agent의 high-level intent는 task와 크게 어긋나지 않는다.
2. agent는 UI element 또는 task-relevant state를 어느 정도 관측한다.
3. 하지만 해당 intent를 executable action 또는 action macro로 변환하는 control grammar를 잘못 가정한다.
4. 직전 action-effect evidence가 그 grammar를 반증했음에도 동일한 wrong mapping 또는 equivalent failed mapping을 반복한다.
5. posterior/action choice/rewrite가 충분히 빨리 전환되지 않는다.

### 4.2 Competing Explanation Separation

| Competing Explanation | 겉보기 유사성 | 분리 기준 | Required Metric/Baseline |
|---|---|---|---|
| low-level action failure | action이 실패한다 | 실패 자체가 아니라 실패 이후 wrong mapping persistence가 핵심 | failed-action repetition vs persistence |
| visual grounding failure | UI 요소를 잘못 찾는다 | 같은 observed element에서 precondition/effect grammar만 바뀌는 split 필요 | OOD-control grammar shift |
| verification failure | previous action success 여부를 모른다 | verification이 아니라 hypothesis update + alternative selection + rewrite가 필요 | verifier-only baseline |
| generic planning failure | sequence planning이 틀린다 | short-horizon grammar shift에서도 발생해야 함 | action-interface switch delay |
| robustness failure | perturbation에서 성능 저하 | 어떤 perturbation이 grammar shift를 유발했는지 계량 | OOD split table |
| search failure | 더 탐색하면 해결된다 | compute-matched tree-search/always-plan 비교 필요 | progress per compute |

---

## 5. Concept Taxonomy

| Concept | Definition | Boundary Rule | Used In |
|---|---|---|---|
| state | UI/task의 현재 값과 progress 상태 | regime/grammar가 아니라 task variable | z_state, progress label |
| regime | UI interaction mode | grammar와 1:1 대응한다고 가정 금지 | z_regime, OOD regime split |
| control grammar | intent→action/macro mapping + precondition + expected effect schema | 단일 precondition이나 action label로 축소 금지 | z_control_grammar, rewrite |
| change-point | state/regime/grammar/evidence structure가 바뀌는 시점 | 단순 visual diff와 동일시 금지 | z_change_point, event head |
| reveal | hidden state가 관측 가능해짐 | protocol 자체가 바뀌는 shift와 분리 | event taxonomy |
| shift | regime/control grammar가 바뀜 | 단순 content update와 분리 | OOD grammar shift |
| current hypothesis | 직전/current action selection에 사용된 hypothesis | posterior mode와 반드시 같다고 가정 금지 | falsification |
| alternative hypothesis | evidence를 더 잘 설명할 수 있는 alternative regime/control grammar | alternative action이 아님 | top-k proposal |
| falsification evidence | current hypothesis expected effect와 observed effect의 구조적 불일치 | failed flag와 동일시 금지 | F score |
| action-interface rewrite | selected grammar 아래 intent를 executable action/macro로 재작성 | LLM self-correction과 분리 | final action selector |
| decision-relevant compute | action choice 변화와 progress gain이 있을 때만 쓰는 compute | uncertainty threshold와 분리 | VOC gate |

---

## 6. Environment and Data Blueprint

### 6.1 Text-Only Smoke Testbed

Text-only testbed는 구현 리스크를 줄이기 위한 첫 번째 gate다. DOM/screenshot 없이 symbolic state와 control grammar만으로 core mechanism이 작동하는지 확인한다.

| Gate | Pass Condition | Fail Action |
|---|---|---|
| TEXT-GATE-01 | base/verifier 대비 failed repetition 감소 | problem framing 재검토 |
| TEXT-GATE-02 | no-control-grammar ablation에서 metric 하락 | grammar definition 보강 |
| TEXT-GATE-03 | no-falsification ablation에서 recovery delay 악화 | F score 재설계 |
| TEXT-GATE-04 | uncertainty-gate 대비 progress per compute 개선 | VOC gate 재설계 |
| TEXT-GATE-05 | 3개 이상 task family에서 방향성 일관 | synthetic Web/GUI 진행 |

### 6.2 Synthetic Web/GUI Environment

Synthetic environment는 단순 toy가 아니라 다음 ground truth를 생성하기 위한 causal lab이다.

| Component | Required Output | Critical Guardrail |
|---|---|---|
| task generator | task family, subgoal graph | template shortcut 방지 |
| UI template generator | DOM/screenshot/a11y | grammar label leak 금지 |
| hidden regime engine | true_regime | agent input 금지 |
| control grammar engine | true_control_grammar, precondition/effect schema | DOM class/name에 leak 금지 |
| change/reveal/shift scheduler | event labels | visual diff와 confound 방지 |
| action executor | actual effect, failure reason | delayed effect 분리 |
| counterfactual generator | alternative effect table | inference input 금지 |
| progress tracker | progress_delta, subgoal completion | synthetic reward shortcut 방지 |
| trace logger | episode step records | reproducibility |
| leakage auditor | flags/assertions | fail-fast |

### 6.3 Visibility Contract

| Field Class | Examples | Inference Input? | Training? | Evaluation? |
|---|---|---:|---:|---:|
| public observation | instruction, sanitized DOM, screenshot ref, a11y tree, previous public effect | YES | YES | YES |
| hidden labels | true_regime, true_control_grammar, true_change_point | NO | YES | YES |
| counterfactual labels | alternative effect table, oracle grammar action | NO | OPTIONAL | YES |
| audit metadata | seed, split, template id, leakage flags | NO | NO | YES |

---

## 7. Architecture Blueprint

### 7.1 Main Candidate Diagram

```text
Frozen Base VLM/LLM Agent
  -> intent + candidate actions

Public Observation Builder
  -> sanitized DOM / screenshot feature / accessibility tree / action-effect history

FRCG-WM Module
  -> DOM Encoder
  -> Screenshot Feature Encoder
  -> Accessibility Encoder
  -> Structured Action-Effect Encoder
  -> History Encoder
  -> Latent Posterior Module q(z_state, z_regime, z_control_grammar, z_change_point | H_t)
  -> Current Hypothesis Scorer
  -> Falsification Scorer
  -> Alternative Hypothesis Proposer
  -> Short-Horizon Rollout Model
  -> Progress/Failure Predictor
  -> Decision-Relevance Gate
  -> Intent-to-Action Rewrite Module
  -> Final Action Selector
```

This is a research blueprint candidate, not an empirically validated final method.

### 7.2 Module Contract

| Module | Input | Output | Loss | Metric | Critical Ablation |
|---|---|---|---|---|---|
| Public Observation Builder | full step record | sanitized input | none | leakage audit | hidden labels included test |
| Frozen Base Agent | public observation | intent/candidates/base action | none | base success | module off |
| Action-Effect Encoder | previous action/effect/diff | evidence embedding | L_action_effect | effect accuracy | no-action-effect-log |
| History Encoder | sequence | H_t | temporal auxiliary | long-trace recovery | short-history only |
| Latent Posterior | H_t | q(z) | L_regime/L_control_grammar/L_change_point | latent probes | collapsed/merged |
| Current Hypothesis Scorer | posterior + trace | h_cur | L_falsification | wrong-current detection | posterior-mode-only |
| Falsification Scorer | h_cur + evidence | F_t | L_falsification | precision/recall/ECE | no F score |
| Alternative Proposer | posterior/evidence | top-k h_alt | ranking/counterfactual | alt recall | random alternative |
| Rollout Model | h, action | predicted effect/progress/failure | L_progress/L_counterfactual | rollout fidelity | no rollout |
| Decision Gate | F, ΔV, P_switch, cost | plan/no-plan | VOC proxy | progress per compute | always-plan/uncertainty |
| Rewrite Module | intent + selected grammar | executable action/macro | L_mapping | switch delay/recovery | no rewrite |
| Final Selector | base + rewritten action | final action | reward-aware | success/return | base-only |

---

## 8. Objective Blueprint

### 8.1 Main Losses

| Loss | Purpose | Required Labels | Failure If Removed |
|---|---|---|---|
| L_action_effect | action-effect prediction | true_action_effect_type, observed_effect | falsification evidence weakens |
| L_progress | progress/value prediction | progress_delta, subgoal | rollout cannot compare alternatives |
| L_regime | regime inference | true_regime | regime recombination weakens |
| L_control_grammar | grammar inference | true_control_grammar | core claim collapses if no drop |
| L_falsification | wrong-current detection / likelihood ratio | true_wrong_hypothesis, evidence targets | verifier-only becomes enough |
| L_intent_action_mapping | rewrite mapping | oracle/recovery action | action-interface rewrite weakens |

### 8.2 Auxiliary Losses

| Loss | Use | Status |
|---|---|---|
| L_failed_action | failure predictor | auxiliary |
| L_change_point | event detector | auxiliary |
| L_reveal_shift | reveal/shift distinction | auxiliary |
| L_recovery_ranking | recovery action ordering | auxiliary/high value |
| L_temporal_consistency | belief stability | appendix if needed |
| L_calibration | F score reliability | auxiliary |
| L_counterfactual_rollout | synthetic rollout target | auxiliary/high value but synthetic-only |

### 8.3 Reward Components

| Reward/Penalty | Acts On | Guardrail |
|---|---|---|
| progress reward | progress predictor/planner value | avoid immediate-progress shortcut |
| failed-action penalty | repeated invalid behavior | do not kill exploration |
| repeated-failure penalty | same wrong mapping loop | reset when state/hypothesis changes |
| recovery reward | post-failure progress | no deliberate failure exploitation |
| valid switch reward | correct hypothesis switch | only if current false + alt better + action changes + progress follows |
| invalid switch penalty | oscillation/needless switch | do not suppress OOD exploration |
| compute cost penalty | overplanning | do not block necessary planning |

---

## 9. Planning Blueprint

### 9.1 Minimal Theory Spine

All quantities below are learned approximations, not exact Bayesian inference.

```text
b_t(z^r, z^g) = q_phi(z^r, z^g | H_t)

ell_t(h) = log p_theta(e_t | H_{t-1}, a_{t-1}, h)

F_t = max_{h_alt in A_t^H} [ell_t(h_alt) - ell_t(h_cur)]

V(a, h) = E[progress - failure_cost - compute_cost]

G_t = I[F_t > tau_f and DeltaV_t > tau_v and P(action_switch) > tau_a]
```

### 9.2 Algorithm Summary

1. build public observation from sanitized schema.
2. frozen base agent proposes intent and candidate actions.
3. encode observation/history/action-effect evidence.
4. infer latent posterior.
5. define current hypothesis `h_cur`.
6. compute falsification score `F_t`.
7. if low falsification, use base action.
8. if high falsification, propose top-k alternative regime/control-grammar hypotheses.
9. short-rollout current and alternatives.
10. compute decision-relevance gate using `F_t`, `ΔV`, `P(action_switch)`, compute cost.
11. if gate passes, rewrite intent into executable action/macro under selected grammar.
12. execute, log, update trace.

### 9.3 What This Is Not

| Not This | Why Not |
|---|---|
| uncertainty-gated planning | gate requires falsification + value gain + action switch, not just uncertainty |
| generic tree search | alternatives are grammar hypotheses, not merely action branches |
| verifier-only recovery | verification does not imply posterior update/alternative rollout/rewrite |
| next-state world model only | predicted next state is not enough; grammar hypothesis matters |
| exact Bayesian planner | all posterior/likelihood/value terms are learned approximations |

---

## 10. Evaluation Blueprint

### 10.1 Claim-to-Evidence Table

| Final Claim | Metric | Baseline | Ablation | Split | Pass Condition | Fail Interpretation |
|---|---|---|---|---|---|---|
| FC-01 persistence | persistence time, invalid mapping rate | Base, retry, verifier | no-control-grammar | ID + OOD grammar | persistence decreases | problem claim weakens |
| FC-02 factorization | recovery, switch delay, OOD grammar | merged, collapsed | no-regime/no-grammar | OOD grammar/recombination | factorized better | latent claim weakens |
| FC-03 falsification | F precision/recall, calibration | verifier-only, failed flag | no-falsification | noisy/timing/reveal-shift | calibrated detection | verification overlap |
| FC-04 alternative rollout/rewrite | rollout fidelity, recovery delay | next-state-WM, WAC-style | no-alt/no-rollout/no-rewrite | OOD regime/grammar | recovery improves | rollout/rewrite weakens |
| FC-05 compute gate | progress per compute, false planning | uncertainty, always-plan | no-gate/no-cost | all splits | compute-normalized win | more-compute attack |

### 10.2 Baseline Suite

| Family | Required Baselines |
|---|---|
| Base agents | Frozen Base VLM/LLM, reactive DOM/text, retry-after-failure, base self-correction |
| Verification/recovery | verifier-only, verification+heuristic recovery, failure diagnosis only, rule-based blocker recovery |
| World model/planning | next-state-WM-only, always-plan WM, fixed-horizon planner, uncertainty-gated planner, tree-search/MCTS-style, random alternative, compute-matched random reallocation |
| Oracle upper bounds | oracle regime, oracle control grammar, oracle alternative hypothesis, oracle precondition, oracle best action |
| Proposed variants | full FRCG-WM, text-only FRCG, DOM-only FRCG, DOM+log FRCG, DOM+screenshot+log FRCG |

### 10.3 Core Metrics

| Category | Metrics |
|---|---|
| Task | success rate, normalized return, subgoal completion, episode length |
| Mechanism | wrong-control-grammar persistence, failed repetition, repeated invalid mapping, switch delay, recovery delay, evidence-to-update delay |
| Falsification/WM | falsification precision/recall/calibration, action-effect accuracy, rollout fidelity, progress prediction error |
| Compute | planning calls, rollout steps, compute-normalized return, progress per compute, false planning call rate, missed opportunity rate |
| OOD | ID-to-OOD drop, OOD-control grammar performance, OOD-reveal/shift performance, long-horizon composition |

### 10.4 Minimum vs Main-Track Evidence

| Evidence Level | Required Evidence |
|---|---|
| Minimum publishable | text-only gate 통과, synthetic ID improvement, no-control-grammar drop, verifier-only보다 recovery delay 개선, leakage audit pass |
| Main-track-level | OOD-control grammar shift 개선, compute-matched progress per compute 우위, direct threat baselines 대비 mechanism metric 개선, critical ablations collapse, negative results reported, optional real auxiliary validation |

---

## 11. Implementation Roadmap

### 11.1 Minimal Viable Experiment 0: Text-Only

| Step | Deliverable | Pass Gate |
|---|---|---|
| MVE0-1 | symbolic episode schema | hidden/public fields separated |
| MVE0-2 | 3 task families × 3 grammar modes | no lexical leakage |
| MVE0-3 | base/verifier/uncertainty/ours planners | same candidate budget |
| MVE0-4 | persistence/recovery/compute metrics | all metrics computed from trace |
| MVE0-5 | no-grammar/no-falsification/no-alt ablations | expected metric drop |

### 11.2 Minimal Viable Experiment 1: Synthetic DOM+Log

| Step | Deliverable | Pass Gate |
|---|---|---|
| MVE1-1 | Playwright/DOM-like synthetic environment | deterministic seeds |
| MVE1-2 | action-effect logger | pre/post/effect/failure fields |
| MVE1-3 | hidden grammar/control labels | not in public observation |
| MVE1-4 | DOM+log FRCG architecture | inference runs without hidden labels |
| MVE1-5 | ID + OOD grammar split | baseline/ablation runner works |

### 11.3 Main Experiment Candidate

| Step | Deliverable | Pass Gate |
|---|---|---|
| MAIN-1 | DOM+screenshot+log hybrid | modality ablation included |
| MAIN-2 | full latent/objective/planning stack | module maps to labels/loss/metrics |
| MAIN-3 | direct threat baselines | verifier-only/next-state/uncertainty/always-plan implemented |
| MAIN-4 | OOD suite | at least 6 OOD splits |
| MAIN-5 | compute-matched reporting | calls/rollout/time/candidates logged |
| MAIN-6 | failure interpretation protocol | negative result table filled |

---

## 12. Reviewer Defense

| Reviewer Attack | Defense in Blueprint | Required Evidence | If Defense Fails |
|---|---|---|---|
| 그냥 Web/GUI world model이다 | grammar persistence + falsification + rewrite가 중심 | next-state-WM/WebWorld/CUWM-style baseline | generic WM으로 약화 |
| VeriGUI와 다르지 않다 | verification이 아니라 hypothesis falsification/alternative rollout | verifier-only baseline, no-falsification | falsification novelty 약화 |
| WAC와 겹친다 | consequence simulation이 아니라 grammar hypothesis comparison | WAC-style action correction baseline | action correction으로 축소 |
| 그냥 tree search다 | alternatives are hypotheses, not actions | MCTS-style baseline, hypothesis metric | planning novelty 약화 |
| uncertainty-gated planning이다 | F + ΔV + action switch + compute cost gate | uncertainty baseline | gate claim 약화 |
| control grammar는 말장난이다 | no-control-grammar/merged/collapsed ablations | factorization metric | core concept 폐기/축소 |
| synthetic toy다 | causal labels + OOD + leakage audit + optional real auxiliary | anti-toy suite | external validity 약화 |
| hidden labels 비현실적이다 | synthetic mechanism lab로 한정, inference input 금지 | visibility assertions | real-world claim 금지 |
| reward가 실제 작동하지 않는다 | reward-to-learning/planning path + no-reward ablation | objective ablations | reward claim appendix로 축소 |
| base LLM이 잘해서 된 것 | frozen base off/on, same base model | module isolation | module claim 약화 |
| compute 더 쓴 것뿐 | compute-matched frontier | progress per compute | planning claim 붕괴 |
| latent identifiable 아님 | merged/collapsed/hierarchical variants | latent probes/ablations | latent claim 약화 |
| negative result 숨김 | failure protocol | non-effect reports | trustworthiness 약화 |

---

## 13. Failure Interpretation Protocol

| Observed Result | Interpretation | Claim To Weaken/Drop | Follow-up |
|---|---|---|---|
| success는 오르지만 persistence가 안 줄어듦 | mechanism이 아님 | FC-01 약화 | metric/separability 재검토 |
| persistence는 줄지만 success가 안 오름 | mechanism은 있으나 utility 부족 | task performance claim 약화 | rewrite/progress 개선 |
| verifier-only와 비슷 | verification만으로 충분 | FC-03 약화 | falsification score 재설계 |
| uncertainty-gate와 비슷 | F gate 차별 부족 | FC-05 약화 | gate 조건 수정 |
| next-state-WM과 비슷 | grammar hypothesis 불필요 | FC-02/04 약화 | OOD grammar split 강화 |
| always-plan이 더 좋음 | compute gate가 성능 제한 | FC-05 수정 | frontier로 재해석 |
| no-control-grammar가 안 무너짐 | grammar claim 붕괴 | FC-02 폐기/축소 | concept taxonomy 수정 |
| merged/collapsed가 더 좋음 | factorization 불필요 | latent claim 약화 | architecture 변경 |
| no-falsification이 안 무너짐 | verifier/uncertainty로 충분 | FC-03 약화 | F score 재정의 |
| no-reward가 비슷 | reward contribution 약함 | objective claim 축소 | reward appendix 이동 |
| OOD grammar 실패 | core generalization 실패 | FC-02/04 약화 | training/env 재설계 |
| real auxiliary 실패 | external validity 제한 | real-world claim 금지 | limitation 명시 |

---

## 14. Risk and Unknown Ledger

| Risk/Unknown | Status | Handling | Can Be Final Claim? |
|---|---|---|---|
| control grammar와 regime 분리 가능성 | REMAINS_UNKNOWN | merged/no-grammar/collapsed ablation | NO |
| current hypothesis trace 정의 | RESOLVED_BY_DESIGN_PARTIAL | `h_cur`/executed hypothesis logging 필요 | NO until implemented |
| hidden label leakage | CLAIM_BLOCKER | visibility assertions + leakage audit | NO |
| synthetic toy criticism | REMAINS_UNKNOWN | anti-toy OOD + optional real auxiliary | NO |
| WebWorld/CUWM/WAC overlap | RESOLVED_BY_EVAL_PLAN | direct threat baselines | NO until comparison |
| VeriGUI overlap | RESOLVED_BY_EVAL_PLAN | verifier-only baseline | NO until comparison |
| F score calibration | REMAINS_UNKNOWN | calibration metrics + loss | NO |
| alternative proposal recall | REMAINS_UNKNOWN | oracle/random/top-k comparisons | NO |
| rollout horizon selection | REMAINS_UNKNOWN | H=1/3/5 sweep | NO |
| top-k selection | REMAINS_UNKNOWN | k=1/3/5 sweep | NO |
| valid switch reward hacking | REMAINS_UNKNOWN | strict 4-condition reward + invalid switch metrics | NO |
| reward contribution | REMAINS_UNKNOWN | no-reward ablation | NO |
| screenshot necessity | REMAINS_UNKNOWN | DOM-only vs hybrid | NO |
| real-world hidden labels absent | FUTURE_WORK | real benchmark auxiliary only | NO |
| counterfactual unobservability | LIMITATION | synthetic-only counterfactual supervision | NO |
| base model dependency | REMAINS_UNKNOWN | multiple frozen bases | NO |
| implementation complexity | REMAINS_UNKNOWN | MVE0→MVE1→main staged roadmap | NO |
| compute fairness | RESOLVED_BY_EVAL_PLAN | compute-matched runner | NO until implemented |
| statistical variance | REMAINS_UNKNOWN | multiple seeds + CIs | NO |
| qualitative cherry-picking | RESOLVED_BY_PROTOCOL | predefined case selection | NO until applied |

---

## 15. Limitations

1. Synthetic environment는 causal label을 제공하지만 real web distribution을 완전히 대표하지 않는다.
2. Hidden regime/control grammar labels는 synthetic에서는 가능하지만 real benchmark에서는 직접 관측되지 않는다.
3. Counterfactual alternative effect table은 real-world interaction에서는 일반적으로 관측 불가능하다.
4. FRCG-WM은 frozen base agent의 candidate action quality에 의존한다.
5. Base agent가 너무 강하면 module gain이 작을 수 있고, 너무 약하면 candidate set에 recovery action이 없을 수 있다.
6. `z_regime`과 `z_control_grammar`의 identifiability는 실험 전 확정할 수 없다.
7. Reward shaping은 progress shortcut, switch hacking, deliberate failure를 만들 수 있다.
8. Decision gate는 necessary planning을 막거나 false planning을 만들 수 있다.
9. Short rollout은 compounding error를 줄이지만 long-horizon reasoning을 충분히 포착하지 못할 수 있다.
10. WebWorld/CUWM/WAC/VeriGUI 같은 direct threat와의 비교 없이는 main-track-level novelty를 주장할 수 없다.
11. Optional real benchmark auxiliary validation은 hidden grammar metric이 부재하므로 core mechanism 검증이 아니라 external sanity check다.
12. 이 blueprint는 empirical result를 포함하지 않으며, 실험 전 final paper claim을 확정하지 않는다.

---

## 16. Paper Skeleton

| Section | Purpose | Must Include |
|---|---|---|
| Title | problem+method+domain 압축 | wrong-hypothesis/control grammar/falsification |
| Abstract | claim을 과장 없이 요약 | no fake numbers, evaluation requirements |
| Introduction | problem framing | repeated failure beyond verification/action failure |
| Related Work | direct threat 정리 | WebWorld/CUWM/WAC/VeriGUI/WebArena/OSWorld |
| Problem Definition | formal failure mode | h_cur, grammar, persistence metric |
| Environment and Dataset | synthetic causal lab | hidden labels, counterfactuals, leakage guardrails |
| Method | architecture | frozen base + FRCG-WM modules |
| Training Objective | losses/rewards | main/aux separation, reward hacking guardrails |
| Planning Algorithm | theory spine | F score, alternatives, VOC gate, rewrite |
| Experiments | evaluation contract | metrics, baselines, ablations, OOD, compute-matched |
| Results To Report | future empirical section | no fabricated numbers |
| Failure Analysis | negative results | claim weakening rules |
| Limitations | honesty | synthetic/hidden label/real transfer limits |
| Conclusion | conditional contribution | claims only if evidence passes |
| Appendix | details | schema, task generator, ablations, prompts, stats |

---

## 17. Final Consistency Gate

| Gate ID | Gate | PASS/FAIL/PARTIAL | Evidence | If Not PASS |
|---|---|---|---|---|
| QG-FINAL-01 | Step 00~10 refs integrated | PASS | Sections 0~16 | none |
| QG-FINAL-02 | final core claims limited to 3~5 | PASS | FC-01~FC-05 | none |
| QG-FINAL-03 | every final claim has metric/baseline/ablation | PASS | Section 10 | none |
| QG-FINAL-04 | no empirical result fabricated | PASS | no numeric result claims | none |
| QG-FINAL-05 | unknowns not promoted to final claim | PASS | Section 14 | none |
| QG-FINAL-06 | related work threats addressed | PASS | Sections 2, 12 | must execute comparisons |
| QG-FINAL-07 | architecture connected to data/objective/planning/evaluation | PASS | Sections 6~10 | none |
| QG-FINAL-08 | reward/loss connected to learning/planning path | PASS | Section 8 | implementation still needed |
| QG-FINAL-09 | compute-matched evaluation included | PASS | Section 10 | runner required |
| QG-FINAL-10 | failure interpretation protocol included | PASS | Section 13 | must apply after experiments |
| QG-FINAL-11 | limitations explicit | PASS | Section 15 | none |
| QG-FINAL-12 | Claude Code routing exists | PASS | Section 0 | none |
| QG-FINAL-13 | MVE implementation roadmap included | PASS | Section 11 | execute MVE0 first |
| QG-FINAL-14 | no hidden label inference usage | PASS | Sections 6, 10 | assert in code |
| QG-FINAL-15 | final blueprint remains non-empirical | PASS | frontmatter + repeated warnings | none |

---

## 18. Final Statement

`FINAL_RESEARCH_BLUEPRINT.md`는 research blueprint이며 empirical result paper가 아니다.

최종 논문은 다음 조건을 만족하는 claim만 주장해야 한다.

- explicit metric이 있어야 한다.
- fair baseline이 있어야 한다.
- critical ablation이 있어야 한다.
- OOD split이 있어야 한다.
- compute-matched evaluation이 있어야 한다.
- negative result 해석 규칙이 있어야 한다.

가장 강한 현재 연구 방향은 다음 한 문장이다.

```text
FRCG-WM tests whether Web/GUI agents can reduce wrong-control-grammar hypothesis persistence by using action-effect evidence to falsify the current interaction hypothesis, compare alternative grammar hypotheses through short rollout, and rewrite executable actions only when the expected progress gain justifies additional compute.
```

실험 전까지 conditional로 유지해야 하는 claim:

- control grammar가 regime/action failure와 분리 가능한지.
- factorized 4-latent가 merged/collapsed보다 나은지.
- falsification score가 verifier-only보다 나은지.
- alternative rollout이 next-state-WM/tree-search보다 나은지.
- decision-relevant compute가 uncertainty/always-plan보다 효율적인지.
- synthetic mechanism이 real benchmark auxiliary에서 약하게라도 일관되는지.

다음 실제 작업 순서:

1. `04_TEXT_ONLY_SMOKE_TESTBED.md` 기반 MVE0 구현.
2. text-only gate 통과 여부 확인.
3. `05`+`06` 기반 synthetic DOM+log MVE1 구현.
4. leakage audit와 schema assertion 통과.
5. `07`+`08`+`09` 기반 minimal FRCG-WM 구현.
6. `10` 기반 baseline/ablation/compute-matched runner 구현.
7. 실패 결과가 나오면 Section 13의 failure interpretation protocol에 따라 claim을 약화/폐기한다.
