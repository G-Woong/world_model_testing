확인했다. 앞으로 붙여넣는 MD는 **한국어 기준으로**, “평가”가 아니라 **Claude Code가 바로 context로 읽고 작업 가능한 10점급 MD**로 재작성하겠다.
이번 파일은 사용자가 제공한 `00_MASTER_REFERENCE.md`를 기준으로 고도화한다. 

````markdown
---
file_id: STEP-00
title: Master Reference Ledger for FRCG-WM Paper Design
version: v1.0
status: reference_ledger_not_final_design
language: ko
created_from:
  - user_original_context
  - user_short_generated_draft
  - assistant_atomic_gap_audit
  - external_search_sanity_check
  - user_revision_requirement_for_10_score_context
purpose:
  - FRCG-WM 논문 설계의 모든 핵심 주장, 개념, 위험, 미해결 사항을 추적 가능한 REF-ID로 정규화한다.
  - 후속 MD 파일들이 필요한 context만 확장적으로 읽을 수 있도록 master routing layer를 제공한다.
  - Claude Code가 초기 설계 제안을 최종 사실처럼 오인하지 않도록 claim status, unknown, blocker, handoff를 분리한다.
  - 논문 아이디어, 구현 가능성, 실험 명세, 평가 계약이 한 줄로 연결되도록 전체 reference backbone을 만든다.
forbidden:
  - Do not finalize the paper.
  - Do not write final architecture as accepted truth.
  - Do not claim novelty without later verification.
  - Do not resolve unknowns without evidence.
  - Do not promote SOURCE_ONLY items into final claims.
  - Do not use this file as a replacement for the later step files.
  - Do not implement code directly from this file without checking the target step file.
next_files:
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
  - FINAL_RESEARCH_BLUEPRINT.md
---

# 00_MASTER_REFERENCE.md

## 1. File Purpose

`00_MASTER_REFERENCE.md`는 최종 논문 설계도가 아니다.  
이 파일은 FRCG-WM 논문 설계 전체의 **master reference ledger**다.

이 파일의 역할은 다음 네 가지다.

1. 사용자 원문, 짧은 초안, gap audit, 검색 sanity 결과에서 나온 모든 핵심 항목을 추적 가능한 `REF-ID`로 정규화한다.
2. 각 항목이 최종 주장인지, 검증 대기 주장인지, 검색으로만 anchor가 확인된 주장인지, 아직 불명확한 unknown인지 명확히 분류한다.
3. Claude Code가 후속 작업 중 필요한 context만 읽을 수 있도록 `Context Routing`, `Handoff`, `Risk`, `Unknown`, `Claim-to-Module` 구조를 제공한다.
4. 후속 파일들이 `문제정의 → 개념분류 → text-only test → synthetic Web/GUI → schema → architecture → objective → planning → evaluation → final blueprint`로 유기적으로 연결되게 만든다.

이 파일에서 절대 하면 안 되는 일은 다음이다.

- FRCG-WM의 novelty를 최종 확정하지 않는다.
- 4-latent 구조를 최종 구조로 확정하지 않는다.
- loss/reward를 최종 objective로 확정하지 않는다.
- synthetic environment를 이미 검증된 benchmark처럼 취급하지 않는다.
- WebWorld, CUWM, WAC, VeriGUI, AgentRx 등과의 차별성을 검증 없이 주장하지 않는다.
- `SOURCE_ONLY`, `CONTESTED`, `UNKNOWN` 항목을 최종 논문 claim으로 승격하지 않는다.

---

## 2. Verification Status Policy

모든 항목은 다음 상태 중 하나를 가져야 한다.

| Status | 의미 | 최종 논문 claim 사용 가능 여부 | 후속 조치 |
|---|---|---:|---|
| `SOURCE_ONLY` | 사용자 제공 원문 또는 초안에서 나온 설계 아이디어 | 불가 | 관련 Step에서 검색/실험/반례 검증 필요 |
| `SEARCH_SUPPORTED` | 외부 연구/벤치마크/개념의 존재 또는 일반 범주가 검색으로 sanity-check됨 | 단독 사용 불가 | Step 01에서 세부 overlap/threat 검증 필요 |
| `CONTESTED` | 가능성은 있으나 기존 연구/개념 중복/구현위험/평가위험이 큼 | 불가 | 반례, baseline, ablation, metric으로 방어 필요 |
| `UNSUPPORTED` | 현재 근거가 부족하거나 주장의 기반이 약함 | 불가 | 주장 약화/폐기/재정의 필요 |
| `UNKNOWN` | 실험/구현/추가 검색 없이는 판단 불가 | 불가 | 명시적으로 Unknown Ledger에 등록 |
| `DESIGN_CANDIDATE` | 아직 최종은 아니지만 후속 설계 후보로 유지 | 조건부 | Step별 gate 통과 필요 |
| `BLOCKER` | 해결되지 않으면 후속 claim 또는 구현이 무효화됨 | 불가 | 지정 Step에서 반드시 해결 |

원칙:

```text
SOURCE_ONLY 또는 CONTESTED 상태의 항목은 FINAL_RESEARCH_BLUEPRINT.md에서 final claim으로 쓰면 안 된다.
단, “실험으로 검증할 hypothesis” 또는 “design candidate”로는 사용할 수 있다.
````

---

## 3. Claude Code Context Routing

Claude Code는 모든 파일을 매번 전부 읽지 말고, 작업 목적에 따라 아래 routing을 따른다.

| User Intent / Task        | Must Read First                        | Then Read                     | Do Not Assume                                                                        |
| ------------------------- | -------------------------------------- | ----------------------------- | ------------------------------------------------------------------------------------ |
| 전체 논문 방향 파악               | `00_MASTER_REFERENCE.md`               | `FINAL_RESEARCH_BLUEPRINT.md` | 00번 파일만으로 최종 설계가 확정됐다고 가정 금지                                                         |
| 관련연구/novelty threat 검토    | `01_RELATED_WORK_THREAT_MAP.md`        | `00`, `02`, `10`              | WebWorld/CUWM/WAC/VeriGUI와 차별성이 이미 해결됐다고 가정 금지                                       |
| 문제정의 수정                   | `02_PROBLEM_NOVELTY_FALSIFICATION.md`  | `00`, `01`, `03`, `10`        | wrong-control-grammar persistence가 독립 failure mode라고 선결정 금지                          |
| `control grammar` 정의/수정   | `03_CORE_CONCEPT_TAXONOMY.md`          | `02`, `06`, `07`, `09`, `10`  | control grammar를 단순 action precondition으로 축소 금지                                      |
| text-only 초기 실험 설계        | `04_TEXT_ONLY_SMOKE_TESTBED.md`        | `02`, `03`, `08`, `09`, `10`  | text-only 성공을 Web/GUI 성공으로 일반화 금지                                                    |
| synthetic Web/GUI 환경 구현   | `05_SYNTHETIC_WEB_GUI_ENVIRONMENT.md`  | `03`, `04`, `06`, `10`        | hidden label을 agent observation에 포함 금지                                               |
| dataset schema/logging 구현 | `06_DATA_SCHEMA_AND_LABELING.md`       | `05`, `07`, `08`, `10`        | `true_regime`, `true_control_grammar`, counterfactual table을 inference input으로 사용 금지 |
| architecture 설계/구현        | `07_LATENT_ARCHITECTURE_DESIGN.md`     | `03`, `06`, `08`, `09`, `10`  | 4-latent 구조가 최종 확정이라고 가정 금지                                                          |
| loss/reward 설계            | `08_LOSS_REWARD_TRAINING_OBJECTIVE.md` | `06`, `07`, `09`, `10`        | reward가 metric으로만 존재해도 된다고 가정 금지                                                     |
| planning algorithm 설계     | `09_PLANNING_THEORY_ALGORITHM.md`      | `07`, `08`, `10`              | uncertainty-gated planning과 falsification-guided planning을 동일시 금지                    |
| evaluation/ablation 설계    | `10_EVALUATION_BASELINE_ABLATION.md`   | `01`, `02`, `07`, `08`, `09`  | success rate만으로 claim 검증 금지                                                          |
| 최종 통합 설계도 작성              | `FINAL_RESEARCH_BLUEPRINT.md`          | `00`~`10` 전체                  | unresolved Unknown을 final claim으로 승격 금지                                              |

---

## 4. Source Ingestion Summary

| Source ID           | Source Type                                 | What It Contains                                                                                                                       | Reliability Level            | How It Will Be Used                                           |
| ------------------- | ------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------- | ------------------------------------------------------------- |
| SRC-USER-ORIGINAL   | user-provided research context              | FRCG-WM 아이디어, wrong-control-grammar persistence, architecture, loss, reward, metric, baseline, unknown                                 | intent 기준 높음, 외부 사실 검증 기준 낮음 | `SOURCE_ONLY` refs로 보존                                        |
| SRC-SHORT-DRAFT     | short generated draft / instruction context | 00 파일이 최종 설계도가 아니라 reference ledger여야 한다는 workflow constraint                                                                          | 높음                           | reference-only 상태와 handoff 구조 강제                              |
| SRC-ASSISTANT-AUDIT | previous atomic gap audit                   | regime/grammar ambiguity, current hypothesis 정의 문제, falsification circularity, toy risk, metric causality 문제                           | 중간                           | suspicion/blocker ledger로 변환                                  |
| SRC-SEARCH-SANITY   | external search sanity results              | WebArena, VisualWebArena, MiniWoB++, WebWorld, CUWM, WAC, VeriGUI, AgentRx, OSWorld, WorkArena++, Agent Q, VOC, change-point 관련 anchor | 중간. full related work 아님     | Step 01 threat map의 seed로 사용                                  |
| SRC-USER-REVISION   | user requirement for 10-score improvement   | 내용 고도화, Claude Code context 적합성, 구현 가능한 실험 명세를 모두 10점 수준으로 개선하라는 지시                                                                    | 높음                           | 모든 ref에 routing, implementation readiness, evaluation link 추가 |
| SRC-UNKNOWN         | unresolved unknowns                         | 구현 가능성, label leakage, metric validity, real benchmark transfer, base-model dependency                                                 | unknown                      | final claim 승격 방지                                             |

---

## 5. Master Core Thesis Ledger

| Ref ID       | Core Thesis Element                               | Source Summary                                                      | Verification Status | Why It Matters                             | Required Validation                                        | Later Step     |
| ------------ | ------------------------------------------------- | ------------------------------------------------------------------- | ------------------- | ------------------------------------------ | ---------------------------------------------------------- | -------------- |
| REF-CORE-001 | Wrong-control-grammar hypothesis persistence      | agent가 UI의 조작 문법을 잘못 가정한 채 반복 실패한다는 핵심 failure mode                 | `CONTESTED`         | 논문 전체의 중심 problem claim                    | action/grounding/planning/verification failure와 분리되는지 증명   | 02, 03, 10     |
| REF-CORE-002 | Latent regime/control-grammar world model         | `z_regime`과 `z_control_grammar`를 분리해 belief를 학습                     | `CONTESTED`         | novelty의 핵심 representation                 | merged/collapsed latent ablation에서 차별성 필요                  | 03, 07, 10     |
| REF-CORE-003 | Action-effect evidence based falsification        | observed effect가 current hypothesis를 반증하는 evidence로 쓰임              | `CONTESTED`         | VeriGUI식 verification과 구분되는 핵심             | evidence→posterior/falsification→alternative→rewrite 경로 필요 | 02, 08, 09     |
| REF-CORE-004 | Current-vs-alternative hypothesis rollout         | current grammar와 top-k alternative grammar를 짧은 rollout으로 비교         | `CONTESTED`         | next-state WM/tree search와 차별화되어야 함        | WebWorld/CUWM/WAC 대비 차별성 검증                                | 01, 09, 10     |
| REF-CORE-005 | Intent-to-action rewrite                          | 같은 intent라도 grammar에 따라 executable action/macro를 바꿈                 | `SOURCE_ONLY`       | 단순 retry/self-correction과 구분되는 행동 변화       | rewrite action이 실제 progress/recovery를 만드는지 실험 필요           | 03, 07, 09, 10 |
| REF-CORE-006 | Decision-relevant compute reallocation            | action choice가 바뀔 가능성이 있을 때만 planning compute 사용                    | `SEARCH_SUPPORTED`  | uncertainty-gated/always-plan baseline과 구분 | compute-matched evaluation 필요                              | 09, 10         |
| REF-CORE-007 | Frozen Base VLM/LLM + proposed reliability module | base agent를 고정하고 제안 모듈 효과만 측정                                       | `DESIGN_CANDIDATE`  | “LLM이 좋아서 된 것” 공격 방어                       | 같은 base, 같은 candidate budget 기준 비교                         | 07, 10         |
| REF-CORE-008 | Text-only smoke test                              | Web/GUI 이전에 symbolic/text 환경으로 핵심 mechanism 검증                      | `DESIGN_CANDIDATE`  | 구현 리스크를 조기 제거                              | text-only 성공이 GUI로 이어지는 bridge 필요                          | 04, 10         |
| REF-CORE-009 | Synthetic Web/GUI controlled environment          | hidden labels와 counterfactual action effect를 생성하는 메인 실험 환경          | `DESIGN_CANDIDATE`  | core metric 측정 가능성 확보                      | toy/label leakage 방지 및 OOD split 필요                        | 05, 06, 10     |
| REF-CORE-010 | Real benchmark auxiliary validation               | WebArena/VisualWebArena/OSWorld/WorkArena 등에서 보조 검증                 | `SEARCH_SUPPORTED`  | 외부 타당성 보강                                  | hidden grammar label 부재로 core metric 제한                    | 01, 06, 10     |
| REF-CORE-011 | 4-latent base design                              | `z_state`, `z_regime`, `z_control_grammar`, `z_change_point` 기본 후보  | `CONTESTED`         | 구조 단순성과 novelty 균형                         | 5-latent/merged/collapsed/hierarchical 비교 필요               | 07             |
| REF-CORE-012 | Main 6 loss candidates                            | effect/progress/regime/grammar/falsification/mapping loss           | `DESIGN_CANDIDATE`  | objective 복잡도 제어                           | 각 loss가 claim/metric/ablation과 연결되어야 함                     | 08, 10         |
| REF-CORE-013 | Progress-linked reward design                     | switch reward는 progress와 연결된 valid switch에만 부여                      | `DESIGN_CANDIDATE`  | reward hacking 방지                          | invalid switch, unnecessary switch, deliberate failure 방지  | 08             |
| REF-CORE-014 | Wrong-hypothesis persistence metric               | evidence 이후 wrong grammar 유지 시간을 측정                                 | `CONTESTED`         | core mechanism metric                      | `h_exec` trace 정의와 ground truth 필요                         | 02, 06, 10     |
| REF-CORE-015 | Reveal-vs-shift split                             | 관측 정보 공개와 조작 문법 변화 구분                                               | `SOURCE_ONLY`       | 모든 UI 변화를 하나로 뭉개지 않기 위함                    | event label과 boundary cases 필요                             | 03, 05, 06, 07 |
| REF-CORE-016 | Compute-matched evaluation                        | planning 계열 baseline과 동일 compute budget 비교                          | `SEARCH_SUPPORTED`  | planning contribution 공정성                  | planning calls, rollout steps, wall-clock proxy 기록         | 09, 10         |
| REF-CORE-017 | Alternative rollout fidelity                      | alternative hypothesis rollout이 실제 effect/progress를 맞추는지 평가         | `SOURCE_ONLY`       | world model quality와 policy gain 분리        | counterfactual effect labels 필요                            | 06, 09, 10     |
| REF-CORE-018 | No-control-grammar ablation                       | grammar latent 제거 시 core metric이 악화되어야 함                            | `SOURCE_ONLY`       | 가장 중요한 novelty ablation                    | no drop이면 grammar claim 약화/폐기                              | 07, 10         |
| REF-CORE-019 | Weak/real-label limitation                        | 실제 benchmark는 hidden grammar label을 제공하지 않음                         | `SOURCE_ONLY`       | real validation claim 제한                   | synthetic core + real auxiliary로 분리                        | 06, 10         |
| REF-CORE-020 | Final claim must not be generic “GUI world model” | generic WM novelty는 WebWorld/CUWM/WAC에 의해 위협받음                      | `SEARCH_SUPPORTED`  | 논문 framing을 좁혀야 함                          | grammar persistence/falsification/rewrite 중심으로 재정의         | 01, 02, FINAL  |
| REF-CORE-021 | Claim-to-evidence discipline                      | 모든 최종 claim은 metric/baseline/ablation/failure interpretation을 가져야 함 | `DESIGN_CANDIDATE`  | 메인트랙 설득력의 핵심                               | 10번 파일에서 평가 계약서화                                           | 10, FINAL      |
| REF-CORE-022 | Negative-result-aware design                      | 결과가 안 좋을 때 약화/폐기할 claim을 미리 지정                                      | `DESIGN_CANDIDATE`  | 과장 방지                                      | failure interpretation protocol 필요                         | 10, FINAL      |

---

## 6. Problem Claim Ledger

| Ref ID          | Problem Claim                                                          | Competing Explanation         | Required Falsification                                    | Metric Candidate                       | Status             | Later Step |
| --------------- | ---------------------------------------------------------------------- | ----------------------------- | --------------------------------------------------------- | -------------------------------------- | ------------------ | ---------- |
| REF-PROBLEM-001 | Agent가 contradictory evidence 이후에도 wrong control grammar를 유지한다         | action failure                | 동일 action failure가 반복 mapping persistence를 설명하지 못함을 보여야 함 | wrong-control-grammar persistence time | `CONTESTED`        | 02, 10     |
| REF-PROBLEM-002 | 실패는 단순 click/type 실행 실패가 아니다                                           | low-level execution failure   | verifier/retry baseline과 비교                               | failed-action repetition rate          | `CONTESTED`        | 02, 10     |
| REF-PROBLEM-003 | 실패는 단순 visual grounding 실패가 아니다                                        | visual grounding failure      | 같은 visible UI에서 precondition/effect grammar만 바꾸는 split 필요 | OOD-control-grammar shift success      | `CONTESTED`        | 02, 05, 10 |
| REF-PROBLEM-004 | 실패는 단순 long-horizon planning error가 아니다                                | planning failure              | short-horizon grammar shift에서도 발생해야 함                     | action-interface switch delay          | `CONTESTED`        | 02, 04, 10 |
| REF-PROBLEM-005 | verification alone은 hypothesis update/rewrite로 이어지지 않으면 불충분하다          | action-effect verification    | VeriGUI-style baseline과 비교                                | recovery delay, persistence time       | `CONTESTED`        | 01, 02, 10 |
| REF-PROBLEM-006 | UI robustness failure는 perception perturbation과 grammar shift로 분리 가능하다 | robustness failure            | visual/DOM perturbation과 semantic grammar shift split 필요  | reveal-vs-shift accuracy               | `DESIGN_CANDIDATE` | 05, 06, 10 |
| REF-PROBLEM-007 | UI perturbation은 appearance만이 아니라 action grammar를 바꿀 수 있다              | UI perturbation failure       | layout unchanged, precondition/effect changed scenario 필요 | OOD-grammar shift return               | `CONTESTED`        | 05, 10     |
| REF-PROBLEM-008 | repeated ineffective behavior는 retry noise보다 stale hypothesis에 가깝다     | retry/self-correction failure | evidence 이후 같은 wrong mapping 반복 추적                        | failed-action repetition rate          | `CONTESTED`        | 02, 10     |
| REF-PROBLEM-009 | Base agent는 intent는 맞추지만 executable action을 틀릴 수 있다                    | intent grounding failure      | base intent freeze + rewrite module comparison            | action rewrite accuracy                | `SOURCE_ONLY`      | 07, 09, 10 |
| REF-PROBLEM-010 | uncertainty만으로 planning하면 false planning이 증가할 수 있다                     | uncertainty-gated planning    | falsification/VOC gate vs uncertainty gate 비교             | false planning call rate               | `SEARCH_SUPPORTED` | 09, 10     |
| REF-PROBLEM-011 | same success rate라도 failure mechanism이 다를 수 있다                         | success-only evaluation       | success rate와 mechanism metric을 분리 보고                     | mechanism metric delta                 | `DESIGN_CANDIDATE` | 10         |
| REF-PROBLEM-012 | current hypothesis trace 없이는 persistence metric이 불가능하다                 | metric design flaw            | `h_exec`와 posterior mode 구분 필요                            | evidence-to-update delay               | `BLOCKER`          | 02, 06, 09 |

---

## 7. Concept and Taxonomy Seed Ledger

| Ref ID          | Concept                   | Working Definition                                                              | Must Not Be Confused With                  | Evidence Needed                                                 | Status                | Later Step |
| --------------- | ------------------------- | ------------------------------------------------------------------------------- | ------------------------------------------ | --------------------------------------------------------------- | --------------------- | ---------- |
| REF-CONCEPT-001 | Regime                    | UI/environment의 현재 interaction mode                                             | control grammar, visual layout, task state | hidden/weak regime label, transition event                      | `CONTESTED`           | 03         |
| REF-CONCEPT-002 | Control grammar           | intent를 executable action/macro, precondition, expected effect schema로 변환하는 규칙  | regime name, affordance, action label      | grammar label, precondition table, effect schema                | `CONTESTED`           | 03, 06     |
| REF-CONCEPT-003 | State                     | task/UI progress에 관련된 hidden variable                                           | regime, grammar                            | state variables, progress labels                                | `DESIGN_CANDIDATE`    | 03, 06     |
| REF-CONCEPT-004 | Change-point              | state/regime/grammar/evidence 구조가 바뀌는 시점                                        | any visual diff                            | event label: none/reveal/shift/failure                          | `DESIGN_CANDIDATE`    | 03, 06, 07 |
| REF-CONCEPT-005 | Reveal                    | action grammar는 그대로인데 hidden state가 관측 가능해지는 사건                                 | shift                                      | same grammar, expanded observation                              | `CONTESTED`           | 03, 06     |
| REF-CONCEPT-006 | Shift                     | interaction protocol/precondition/effect mapping이 바뀌는 사건                        | reveal, DOM update                         | grammar/regime transition label                                 | `CONTESTED`           | 03, 06     |
| REF-CONCEPT-007 | Current hypothesis        | 마지막 action을 생성/선택할 때 실제 사용된 hypothesis                                          | posterior mode                             | `h_exec` trace, action-generation log                           | `BLOCKER`             | 03, 09     |
| REF-CONCEPT-008 | Alternative hypothesis    | observed evidence를 current보다 더 잘 설명할 수 있는 non-current regime/grammar hypothesis | random alternative action                  | posterior/evidence likelihood ranking                           | `CONTESTED`           | 03, 09     |
| REF-CONCEPT-009 | Falsification evidence    | current hypothesis가 expected effect를 설명하지 못함을 보여주는 action-effect evidence       | generic uncertainty                        | expected-vs-observed effect discrepancy                         | `CONTESTED`           | 02, 06, 09 |
| REF-CONCEPT-010 | Action-interface rewrite  | selected grammar에 따라 intent/base action을 executable action/macro로 변환            | retry, natural-language self-correction    | macro/action trace, recovery label                              | `SOURCE_ONLY`         | 03, 07, 09 |
| REF-CONCEPT-011 | Decision-relevant compute | action choice 또는 expected progress가 바뀔 가능성이 있을 때 쓰는 planning compute            | uncertainty, always-plan                   | VOC estimate, action switch prob, compute logs                  | `SEARCH_SUPPORTED`    | 09         |
| REF-CONCEPT-012 | Expected effect schema    | 특정 grammar/action 아래 예상되는 상태 변화/effect type                                     | reward only                                | effect type, DOM diff, progress delta                           | `DESIGN_CANDIDATE`    | 06, 08     |
| REF-CONCEPT-013 | Persistence time          | evidence 이후 wrong executed hypothesis가 유지된 step 수                               | failure count                              | ground-truth grammar + executed hypothesis trace                | `CONTESTED`           | 02, 10     |
| REF-CONCEPT-014 | Recovery                  | failure evidence 이후 progress-producing state로 복귀                                | success alone                              | failure-to-progress delay                                       | `DESIGN_CANDIDATE`    | 08, 10     |
| REF-CONCEPT-015 | Blocker                   | intended action 실행을 막는 modal/loading/permission/form state                      | regime itself                              | overlay/permission/loading labels                               | `AUXILIARY_CANDIDATE` | 03, 06, 07 |
| REF-CONCEPT-016 | Action precondition       | action이 effect를 만들기 위해 만족해야 하는 조건                                               | whole control grammar                      | precondition status, failed reason                              | `AUXILIARY_CANDIDATE` | 03, 06     |
| REF-CONCEPT-017 | Action effect type        | action 이후 발생한 effect class                                                      | reward, progress                           | effect label, DOM/visual diff                                   | `DESIGN_CANDIDATE`    | 06, 08     |
| REF-CONCEPT-018 | Evidence-to-update delay  | falsifying evidence 이후 hypothesis update까지 걸린 delay                             | recovery delay                             | evidence timestamp, hypothesis trace                            | `DESIGN_CANDIDATE`    | 09, 10     |
| REF-CONCEPT-019 | Valid hypothesis switch   | wrong current에서 better alternative로 전환하고 progress가 뒤따른 switch                   | any switch                                 | true current wrong, alternative effect better, progress follows | `CONTESTED`           | 08, 10     |
| REF-CONCEPT-020 | Invalid hypothesis switch | evidence가 약하거나 progress 없는 unnecessary switch                                   | exploration                                | no progress, wrong alternative, oscillation                     | `DESIGN_CANDIDATE`    | 08, 10     |

---

## 8. Latent Variable Seed Ledger

| Ref ID         | Latent                  | Working Meaning                                    | Possible Overlap              | Needed Label             | Risk                            | Recommended Initial Status        | Later Step |
| -------------- | ----------------------- | -------------------------------------------------- | ----------------------------- | ------------------------ | ------------------------------- | --------------------------------- | ---------- |
| REF-LATENT-001 | `z_state`               | hidden UI/task state belief                        | progress, blocker, affordance | state/progress variables | 모든 정보를 흡수할 위험                   | `PRIMARY_CANDIDATE`               | 07         |
| REF-LATENT-002 | `z_regime`              | interaction mode belief                            | grammar, blocker              | regime label             | grammar와 collapse 가능            | `PRIMARY_CANDIDATE_BUT_CONTESTED` | 07         |
| REF-LATENT-003 | `z_control_grammar`     | intent-to-action/precondition/effect schema belief | regime, precondition          | grammar label            | core novelty지만 relabeling 공격 가능 | `PRIMARY_CANDIDATE_BUT_CRITICAL`  | 07         |
| REF-LATENT-004 | `z_change_point`        | none/reveal/shift/failure event belief             | reveal/shift head             | event label              | rare-event imbalance            | `PRIMARY_CANDIDATE`               | 07         |
| REF-LATENT-005 | `z_goal_progress`       | subgoal/progress status                            | `z_state`, progress head      | progress/subgoal label   | state와 중복 가능                    | `AUXILIARY_HEAD_CANDIDATE`        | 07         |
| REF-LATENT-006 | `z_action_precondition` | executability precondition belief                  | grammar                       | precondition table       | grammar를 쪼개 contribution 흐림     | `AUXILIARY_HEAD_CANDIDATE`        | 07         |
| REF-LATENT-007 | `z_affordance`          | UI element/action possibility                      | observation encoder           | affordance labels        | 기존 GUI grounding과 중복            | `AUXILIARY_HEAD_OR_REJECT`        | 07         |
| REF-LATENT-008 | `z_blocker`             | modal/loading/permission obstruction belief        | regime                        | blocker label            | regime과 중복                      | `AUXILIARY_HEAD_CANDIDATE`        | 07         |
| REF-LATENT-009 | `z_uncertainty`         | belief uncertainty/calibration                     | falsification score           | calibration target       | uncertainty baseline으로 collapse | `AUXILIARY_ONLY`                  | 07, 09     |
| REF-LATENT-010 | `z_user_intent`         | user/base-agent intended subgoal                   | frozen base output            | intent labels            | LLM 역할과 중복                      | `REJECT_AS_PRIMARY`               | 07         |
| REF-LATENT-011 | `z_effect_schema`       | expected action effect class                       | grammar                       | effect labels            | grammar head와 중복 가능             | `AUXILIARY_HEAD_CANDIDATE`        | 07         |
| REF-LATENT-012 | `z_recovery_mode`       | failure recovery strategy                          | grammar/rewrite policy        | recovery action labels   | model/policy 경계 흐림              | `APPENDIX_OR_REJECT`              | 07         |
| REF-LATENT-013 | `z_task_phase`          | multi-step task phase                              | state/progress                | subgoal/phase labels     | state와 중복                       | `AUXILIARY_HEAD_CANDIDATE`        | 07         |
| REF-LATENT-014 | `z_temporal_stability`  | current grammar/state가 유지될 가능성                     | uncertainty/change point      | stability label          | 과도한 설계                          | `UNKNOWN_NEEDS_EXPERIMENT`        | 07         |

---

## 9. Architecture Seed Ledger

| Ref ID       | Component                       | Input                                                   | Output                               | Role                              | Risk                                    | Required Implementation Detail      | Later Step |
| ------------ | ------------------------------- | ------------------------------------------------------- | ------------------------------------ | --------------------------------- | --------------------------------------- | ----------------------------------- | ---------- |
| REF-ARCH-001 | Frozen Base VLM/LLM agent       | instruction, public observation, history summary        | intent, candidate actions, rationale | module 효과 분리                      | candidate set에 recovery action이 없을 수 있음 | same base across all methods        | 07, 10     |
| REF-ARCH-002 | Public Observation Builder      | raw trace + visibility contract                         | agent-safe observation               | hidden label leakage 방지           | schema extraction 오류                    | enforce `build_agent_observation()` | 06, 07     |
| REF-ARCH-003 | Observation encoder             | DOM, accessibility tree, screenshot feature             | observation embedding                | UI state encoding                 | visual/DOM shortcut                     | modality ablation 필요                | 07         |
| REF-ARCH-004 | Action-effect encoder           | previous action, expected effect, observed effect, diff | evidence embedding                   | falsification evidence pathway    | expected effect leakage                 | public/label split 필요               | 06, 07     |
| REF-ARCH-005 | History encoder                 | obs/action/effect/intent sequence                       | temporal belief state                | persistence 추적                    | long history drift                      | window/summary policy 필요            | 07         |
| REF-ARCH-006 | Latent posterior module         | history state                                           | posterior over latents               | belief update                     | identifiability risk                    | probes + ablations                  | 07         |
| REF-ARCH-007 | Regime inference head           | posterior/history                                       | regime distribution                  | regime split                      | grammar 중복                              | no-regime/merged ablation           | 07         |
| REF-ARCH-008 | Control-grammar inference head  | posterior/history/intent                                | grammar distribution                 | core novelty                      | relabeled precondition 위험               | no-grammar ablation                 | 07         |
| REF-ARCH-009 | Change-point/event head         | action-effect history                                   | none/reveal/shift/failure            | transition detection              | visual diff classifier로 축소              | reveal-vs-shift split               | 07         |
| REF-ARCH-010 | Current hypothesis scorer       | executed hypothesis, evidence                           | likelihood/score                     | falsification target              | posterior mode와 혼동                      | `h_exec` trace 필수                   | 09         |
| REF-ARCH-011 | Falsification scorer            | current score, alternative score, evidence              | falsification score                  | replanning trigger                | circular scoring                        | held-out calibration                | 08, 09     |
| REF-ARCH-012 | Alternative hypothesis proposer | posterior, evidence likelihood                          | top-k alternative hypotheses         | grammar switch 후보                 | arbitrary top-k                         | k sweep                             | 09         |
| REF-ARCH-013 | Short rollout model             | hypothesis, action, obs                                 | predicted effect/progress/failure    | current vs alternative comparison | WebWorld/CUWM/WAC threat                | rollout fidelity metric             | 01, 09     |
| REF-ARCH-014 | Progress/reward predictor       | rollout features                                        | expected progress/reward             | action/value comparison           | synthetic reward overfit                | no-reward ablation                  | 08         |
| REF-ARCH-015 | Decision-relevance gate         | falsification, ΔV, action-switch prob, compute cost     | plan/no-plan                         | compute efficiency                | uncertainty gate로 collapse              | uncertainty baseline                | 09         |
| REF-ARCH-016 | Intent-to-action rewrite module | intent, candidate actions, grammar, preconditions       | executable action/macro              | recovery action 생성                | macro under-specification               | action macro schema                 | 07, 09     |
| REF-ARCH-017 | Final action selector           | base action, rewritten action, scores                   | executed action                      | loop closure                      | selector가 gains 주도 가능                   | selector ablation                   | 09         |
| REF-ARCH-018 | Evidence logger                 | action, pre/post state, diffs, labels                   | structured trace                     | training/evaluation source        | real benchmark mismatch                 | trace schema                        | 06         |
| REF-ARCH-019 | Calibration monitor             | predictions vs realized effects                         | calibration curves                   | gate reliability                  | OOD calibration failure                 | ECE/Brier metrics                   | 08, 10     |
| REF-ARCH-020 | Counterfactual label consumer   | alternative effect table                                | rollout targets/eval                 | synthetic supervision             | oracle leakage                          | excluded from inference             | 06, 08, 09 |

Collapse rule:

```text
If REF-ARCH-004, REF-ARCH-011, REF-ARCH-012, REF-ARCH-013, or REF-ARCH-016 is removed and performance does not degrade,
the paper likely collapses into ordinary verification, next-state prediction, or action search.
```

---

## 10. Loss Seed Ledger

| Ref ID       | Loss Candidate             | Trains What                                         | Connected Claim                   | Label Needed                                          | Risk                           | Initial Status                       | Later Step |
| ------------ | -------------------------- | --------------------------------------------------- | --------------------------------- | ----------------------------------------------------- | ------------------------------ | ------------------------------------ | ---------- |
| REF-LOSS-001 | `L_action_effect`          | effect type/effect embedding predictor              | action-effect evidence            | `true_action_effect_type`, DOM/visual diff            | effect label may leak grammar  | `MAIN_CANDIDATE`                     | 08         |
| REF-LOSS-002 | `L_progress`               | progress/reward predictor                           | decision-relevant rollout         | `true_progress_delta`                                 | dense progress synthetic-only  | `MAIN_CANDIDATE`                     | 08         |
| REF-LOSS-003 | `L_regime`                 | regime inference head                               | latent regime                     | `true_regime`                                         | collapses with grammar         | `MAIN_CANDIDATE_BUT_CONTESTED`       | 08         |
| REF-LOSS-004 | `L_control_grammar`        | grammar inference head                              | core grammar claim                | `true_control_grammar`                                | toy supervised classifier risk | `MAIN_CANDIDATE_CRITICAL`            | 08         |
| REF-LOSS-005 | `L_falsification`          | wrong-current detection or likelihood-ratio scoring | falsification claim               | `true_wrong_hypothesis` or pairwise likelihood target | circularity                    | `MAIN_CANDIDATE_CRITICAL`            | 08, 09     |
| REF-LOSS-006 | `L_intent_action_mapping`  | rewrite/mapping module                              | action-interface rewrite          | oracle executable action/macro                        | oracle macro availability      | `MAIN_CANDIDATE`                     | 08         |
| REF-LOSS-007 | `L_failed_action`          | failure predictor                                   | failure loop reduction            | `true_failed_action`                                  | duplicates verifier            | `AUXILIARY_CANDIDATE`                | 08         |
| REF-LOSS-008 | `L_change_point`           | event detector                                      | transition handling               | `true_change_point`                                   | rare event imbalance           | `AUXILIARY_CANDIDATE`                | 08         |
| REF-LOSS-009 | `L_reveal_shift`           | reveal vs shift classifier                          | taxonomy validity                 | `true_reveal_vs_shift`                                | ambiguous boundary             | `AUXILIARY_CANDIDATE`                | 08         |
| REF-LOSS-010 | `L_recovery_ranking`       | recovery action scorer                              | recovery delay reduction          | recovery action labels                                | policy confound                | `AUXILIARY_CANDIDATE`                | 08         |
| REF-LOSS-011 | `L_temporal_consistency`   | latent stability                                    | persistence tracking              | temporal transition target                            | suppresses valid switches      | `APPENDIX_OR_AUX`                    | 08         |
| REF-LOSS-012 | `L_calibration`            | prediction confidence                               | reliable falsification gate       | predicted vs realized effect                          | not directly tied to success   | `AUXILIARY_CANDIDATE`                | 08         |
| REF-LOSS-013 | `L_current_alt_ranking`    | alternative hypothesis ranking                      | alternative rollout/falsification | true/false hypothesis pairs                           | pair construction leakage      | `AUXILIARY_OR_MAIN_DEPENDING_STEP08` | 08         |
| REF-LOSS-014 | `L_affordance`             | clickable/scrollable/visible head                   | observation grounding             | affordance label                                      | not core novelty               | `AUXILIARY_ONLY`                     | 08         |
| REF-LOSS-015 | `L_blocker`                | blocker detection                                   | modal/loading/permission handling | blocker labels                                        | regime duplication             | `AUXILIARY_ONLY`                     | 08         |
| REF-LOSS-016 | `L_entropy_reg`            | posterior regularization                            | stable belief                     | none/direct                                           | hides uncertainty              | `EXPERIMENTAL_ONLY`                  | 08         |
| REF-LOSS-017 | `L_counterfactual_rollout` | rollout fidelity                                    | alternative hypothesis quality    | counterfactual effect/progress                        | synthetic-only                 | `AUXILIARY_HIGH_VALUE`               | 08         |
| REF-LOSS-018 | `L_value_of_compute_proxy` | compute gate                                        | decision-relevant compute         | compute/value targets                                 | heuristic                      | `UNKNOWN`                            | 08, 09     |

---

## 11. Reward Seed Ledger

| Ref ID         | Reward Component                | Intended Effect                         | Possible Reward Hacking           | Guardrail Needed                                                  | Initial Status        | Later Step |
| -------------- | ------------------------------- | --------------------------------------- | --------------------------------- | ----------------------------------------------------------------- | --------------------- | ---------- |
| REF-REWARD-001 | Progress reward                 | task progress 유도                        | synthetic progress marker exploit | env state 기반 progress, not model output                           | `MAIN_CANDIDATE`      | 08         |
| REF-REWARD-002 | Failed-action penalty           | ineffective action 감소                   | exploration suppression           | first failure weak, repeated failure strong                       | `MAIN_CANDIDATE`      | 08         |
| REF-REWARD-003 | Repeated-failure penalty        | same wrong mapping/action loop 감소       | legitimate retry까지 penalize       | state/hypothesis changed면 penalty 완화                              | `MAIN_CANDIDATE`      | 08         |
| REF-REWARD-004 | Recovery reward                 | failure 이후 progress recovery 유도         | deliberate failure exploit        | agent-induced repeated failure에는 bonus 금지                         | `CONTESTED`           | 08         |
| REF-REWARD-005 | Valid hypothesis-switch reward  | wrong current에서 better grammar로 전환 유도   | constant switching reward hacking | current false + alt better + action differs + progress follows 조건 | `HIGH_RISK_CONTESTED` | 08         |
| REF-REWARD-006 | Invalid switch penalty          | unnecessary/oscillatory switch 방지       | OOD exploration 억제                | high-falsification case 예외                                        | `AUXILIARY_CANDIDATE` | 08         |
| REF-REWARD-007 | Compute cost penalty            | overplanning 방지                         | necessary planning 억제             | decision relevance 조건과 jointly 적용                                 | `MAIN_CANDIDATE`      | 08, 09     |
| REF-REWARD-008 | Failure-risk penalty            | derail action 회피                        | over-conservative behavior        | progress reward와 균형                                               | `AUXILIARY_CANDIDATE` | 08         |
| REF-REWARD-009 | Switch cost                     | posterior/action oscillation 방지         | valid rapid recovery 억제           | high-falsification transition exempt                              | `AUXILIARY_CANDIDATE` | 08         |
| REF-REWARD-010 | Oracle upper-bound reward audit | learned reward와 true progress 비교        | oracle leakage                    | evaluation/audit only                                             | `EVAL_ONLY`           | 08, 10     |
| REF-REWARD-011 | Delayed recovery penalty        | evidence 이후 늦은 update/recovery penalize | overly aggressive switching       | only after stable falsifying evidence                             | `AUXILIARY_CANDIDATE` | 08         |
| REF-REWARD-012 | Optional exploration bonus      | alternative discovery 지원                | random exploration abuse          | limited to low-stakes early stage                                 | `UNKNOWN`             | 08         |

Critical rule:

```text
REF-REWARD-005 must never be a simple positive reward for switching.
It is valid only when all four conditions hold:
1. current hypothesis was wrong,
2. alternative explains evidence better,
3. selected action actually changes,
4. progress or reduced failure follows.
```

---

## 12. Environment and Data Seed Ledger

| Ref ID       | Environment/Data Item                    | Purpose                        | Needed Label                          | Leakage Risk                  | Critical Guardrail               | Later Step |
| ------------ | ---------------------------------------- | ------------------------------ | ------------------------------------- | ----------------------------- | -------------------------------- | ---------- |
| REF-DATA-001 | Text-only smoke test                     | GUI 이전에 mechanism viability 검증 | regime, grammar, effect, progress     | lexical cue로 label 노출         | paraphrase/decoy text            | 04         |
| REF-DATA-002 | Synthetic Web/GUI controlled environment | causal label 기반 메인 검증          | full hidden labels                    | toy classifier/label leakage  | anti-leakage audit               | 05         |
| REF-DATA-003 | DOM tree                                 | structured UI state            | node attrs, visibility, enabled, bbox | hidden flags 포함 위험            | sanitize DOM                     | 05, 06     |
| REF-DATA-004 | Screenshot feature                       | visual grounding auxiliary     | screenshot/VLM feature                | 불필요한 complexity               | modality ablation                | 05, 06     |
| REF-DATA-005 | Accessibility tree                       | GUI agent 현실성                  | role/name/state                       | semantic leakage              | sanitize labels                  | 05, 06     |
| REF-DATA-006 | Structured action-effect log             | falsification evidence         | pre/post state, action, diff, effect  | expected effect label leakage | public vs hidden split           | 06         |
| REF-DATA-007 | Hidden regime label                      | regime supervision/evaluation  | `true_regime`                         | inference input leakage       | training/eval only               | 06         |
| REF-DATA-008 | Hidden control grammar label             | grammar supervision/evaluation | `true_control_grammar`                | core leakage risk             | never public                     | 06         |
| REF-DATA-009 | Reveal-vs-shift label                    | event taxonomy 검증              | `true_reveal_vs_shift`                | boundary ambiguity            | label rules                      | 06         |
| REF-DATA-010 | Change-point label                       | transition timing              | `true_change_point`                   | rare imbalance                | class balancing                  | 06         |
| REF-DATA-011 | Progress label                           | dense progress/value learning  | `true_progress_delta`                 | synthetic reward overfit      | OOD task split                   | 06, 08     |
| REF-DATA-012 | Failed-action label                      | failure loop detection         | `true_failed_action`                  | verifier-only duplication     | reason taxonomy                  | 06         |
| REF-DATA-013 | Alternative action effect table          | rollout fidelity/evaluation    | counterfactual effects                | oracle leakage                | counterfactual-only bucket       | 06, 09     |
| REF-DATA-014 | Train/test/OOD split                     | generalization 측정              | split metadata                        | split shortcut                | seed/template separation         | 05, 06, 10 |
| REF-DATA-015 | OOD grammar shift split                  | grammar robustness 검증          | grammar shift label                   | 핵심 split 설계 실패 위험             | same UI, changed grammar         | 05, 10     |
| REF-DATA-016 | OOD visual/DOM perturbation split        | perception robustness 분리       | perturbation type                     | grammar shift와 confound       | independent perturbation factors | 05, 10     |
| REF-DATA-017 | OOD regime recombination split           | latent recombination 검증        | regime combination                    | train leakage                 | held-out combinations            | 05, 10     |
| REF-DATA-018 | Real benchmark auxiliary trace           | external validation            | weak logs                             | grammar labels 없음             | auxiliary only                   | 06, 10     |
| REF-DATA-019 | Leakage audit metadata                   | shortcut detection             | generation config, template id, flags | audit field가 input에 노출        | audit-only visibility            | 06         |
| REF-DATA-020 | Reproducibility metadata                 | deterministic generation       | seed/version/hash                     | seed leakage                  | file-path sanitization           | 06         |

---

## 13. Metric/Baseline/Ablation Seed Ledger

| Ref ID           | Item Type | Item                                   | Connected Claim               | Why Needed                 | Failure Interpretation                 | Later Step |
| ---------------- | --------- | -------------------------------------- | ----------------------------- | -------------------------- | -------------------------------------- | ---------- |
| REF-METRIC-001   | metric    | task success rate                      | final usefulness              | standard outcome           | success만 오르면 mechanism 미검증             | 10         |
| REF-METRIC-002   | metric    | normalized return                      | partial progress              | sparse success 보완          | reward shaping artifact 가능             | 10         |
| REF-METRIC-003   | metric    | compute-matched return                 | compute efficiency            | planning fairness          | 없으면 always-plan 비교 불공정                 | 10         |
| REF-METRIC-004   | metric    | failed-action repetition rate          | failure loop reduction        | direct symptom metric      | 안 줄면 core benefit 약화                   | 10         |
| REF-METRIC-005   | metric    | wrong-control-grammar persistence time | core failure mode             | 독립 failure 증명              | 안 줄면 problem claim 약화                  | 02, 10     |
| REF-METRIC-006   | metric    | action-interface switch delay          | rewrite timing                | action change 측정           | 느리면 rewrite claim 약화                   | 10         |
| REF-METRIC-007   | metric    | recovery delay                         | recovery after evidence       | practical recovery         | verifier-only와 같으면 novelty 약화          | 10         |
| REF-METRIC-008   | metric    | alternative rollout fidelity           | world model quality           | policy gain과 WM quality 분리 | 낮으면 rollout claim 약화                   | 10         |
| REF-METRIC-009   | metric    | falsification precision/recall         | wrong-current detection       | gate quality               | 낮으면 falsification claim 약화             | 10         |
| REF-METRIC-010   | metric    | change-point F1                        | transition detection          | `z_change_point` 검증        | 낮으면 change-point head 약화               | 10         |
| REF-METRIC-011   | metric    | reveal-vs-shift accuracy               | taxonomy validity             | event distinction 검증       | 낮으면 taxonomy 약화                        | 10         |
| REF-METRIC-012   | metric    | progress per compute                   | decision-relevant compute     | compute 효율                 | uncertainty/always-plan과 같으면 claim 약화  | 10         |
| REF-METRIC-013   | metric    | false planning call rate               | anti-overplanning             | gate precision             | 높으면 compute gate 약화                    | 10         |
| REF-METRIC-014   | metric    | action rewrite accuracy                | rewrite module                | executable mapping 검증      | 낮으면 rewrite claim 약화                   | 10         |
| REF-METRIC-015   | metric    | evidence-to-hypothesis-update delay    | belief update timing          | falsification→update 연결    | 높으면 persistence 해결 실패                  | 10         |
| REF-METRIC-016   | metric    | invalid switch rate                    | reward/gate safety            | switch hacking 검출          | 높으면 reward/gate 위험                     | 10         |
| REF-BASELINE-001 | baseline  | Frozen Base VLM/LLM agent              | module benefit                | 필수 기준                      | 이기지 못하면 module claim 붕괴                | 10         |
| REF-BASELINE-002 | baseline  | verifier-only                          | beyond verification           | VeriGUI threat 대응          | 비슷하면 falsification novelty 약화          | 10         |
| REF-BASELINE-003 | baseline  | next-state world model only            | beyond generic WM             | WebWorld/CUWM threat 대응    | 비슷하면 grammar novelty 약화                | 10         |
| REF-BASELINE-004 | baseline  | always-plan world model                | compute efficiency            | overplanning 비교            | always-plan이 이기면 gate claim 약화         | 10         |
| REF-BASELINE-005 | baseline  | uncertainty-gated planner              | falsification vs uncertainty  | 핵심 gate 비교                 | 비슷하면 falsification gate 약화             | 10         |
| REF-BASELINE-006 | baseline  | compute-matched random reallocation    | targeted compute              | compute fairness           | 비슷하면 targeted reallocation 약화          | 10         |
| REF-BASELINE-007 | baseline  | oracle regime upper bound              | headroom                      | upper bound                | gap이 너무 크면 method 약화                   | 10         |
| REF-BASELINE-008 | baseline  | WAC-style consequence simulation       | related work threat           | action correction threat   | 차별성 없으면 novelty 약화                     | 01, 10     |
| REF-BASELINE-009 | baseline  | VeriGUI-style verification/recovery    | related work threat           | verification threat        | 차별성 없으면 novelty 약화                     | 01, 10     |
| REF-BASELINE-010 | baseline  | oracle control grammar                 | grammar headroom              | grammar value upper bound  | full이 너무 멀면 learning 문제                | 10         |
| REF-ABLATION-001 | ablation  | no-regime                              | regime necessity              | latent factor 검증           | no drop이면 regime 약화                    | 07, 10     |
| REF-ABLATION-002 | ablation  | no-control-grammar                     | grammar necessity             | critical ablation          | no drop이면 core novelty 붕괴              | 07, 10     |
| REF-ABLATION-003 | ablation  | no-change-point                        | transition necessity          | event head 검증              | no drop이면 change-point 약화              | 07, 10     |
| REF-ABLATION-004 | ablation  | no-falsification                       | falsification necessity       | trigger mechanism          | no drop이면 verifier/uncertainty로 충분     | 09, 10     |
| REF-ABLATION-005 | ablation  | no-alternative-rollout                 | alternative rollout necessity | current-only 한계 검증         | no drop이면 rollout claim 약화             | 09, 10     |
| REF-ABLATION-006 | ablation  | no-compute-gate                        | compute gate necessity        | overplanning 검증            | no drop이면 gate 불필요                     | 09, 10     |
| REF-ABLATION-007 | ablation  | no-reward/progress loss                | value learning necessity      | progress predictor 검증      | no drop이면 reward contribution 약화       | 08, 10     |
| REF-ABLATION-008 | ablation  | merged regime-control grammar          | factorization necessity       | separability 검증            | merged가 낫다면 split claim 약화             | 07, 10     |
| REF-ABLATION-009 | ablation  | random alternative                     | alternative quality           | proposer 검증                | no drop이면 proposer 의미 약화               | 09, 10     |
| REF-ABLATION-010 | ablation  | text/DOM/screenshot/hybrid             | modality dependence           | input design 검증            | hybrid benefit 없으면 screenshot claim 약화 | 05, 07, 10 |
| REF-ABLATION-011 | ablation  | no-action-rewrite                      | rewrite necessity             | action-interface 검증        | no drop이면 rewrite claim 약화             | 09, 10     |
| REF-ABLATION-012 | ablation  | uncertainty instead of falsification   | gate specificity              | decision rule 검증           | 비슷하면 falsification claim 약화            | 09, 10     |

---

## 14. External Anchor Ledger

> 이 섹션은 full related work가 아니라 Step 01을 위한 sanity anchor다.
> URL/arXiv/OpenReview/DOI는 Step 01에서 반드시 citation-grade로 보강해야 한다.

| Search ID  | Query / Anchor                                       | Source/Paper/Benchmark                              |             Year | Current Finding                                                             | Relation to FRCG-WM                                            | Threat Level | Verification Needed In |
| ---------- | ---------------------------------------------------- | --------------------------------------------------- | ---------------: | --------------------------------------------------------------------------- | -------------------------------------------------------------- | ------------ | ---------------------- |
| SEARCH-001 | WebArena realistic web environment autonomous agents | WebArena                                            |             2023 | self-hosted realistic web benchmark; autonomous web agent evaluation anchor | external benchmark and baseline context                        | MEDIUM       | 01, 10                 |
| SEARCH-002 | VisualWebArena multimodal realistic visual web tasks | VisualWebArena                                      |             2024 | multimodal/visual web benchmark                                             | threatens visual grounding novelty; useful auxiliary benchmark | MEDIUM       | 01, 10                 |
| SEARCH-003 | MiniWoB++ web interaction benchmark                  | MiniWoB++                                           |        2017/2018 | synthetic web interaction tasks                                             | precedent for controlled web task generation                   | LOW          | 04, 05                 |
| SEARCH-004 | OSWorld real computer environment tasks              | OSWorld                                             |             2024 | real desktop/computer-use benchmark                                         | external validation anchor                                     | MEDIUM       | 01, 10                 |
| SEARCH-005 | WebWorld web agent world model                       | WebWorld                                            |             2026 | large-scale web world model / simulation / search direction                 | high threat to generic “web world model” claim                 | HIGH         | 01                     |
| SEARCH-006 | CUWM computer-using world model                      | CUWM                                                |             2026 | next UI-state prediction and frozen-agent test-time search                  | direct threat to frozen agent + world model search             | HIGH         | 01                     |
| SEARCH-007 | WAC action correction web agent                      | WAC                                                 |             2026 | consequence simulation and action correction                                | direct threat to action correction/rollout claim               | HIGH         | 01                     |
| SEARCH-008 | VeriGUI action-effect verification                   | VeriGUI                                             |             2026 | action-effect verification and self-correction                              | direct threat to verification/recovery framing                 | HIGH         | 01                     |
| SEARCH-009 | AgentRx failure diagnosis                            | AgentRx                                             |             2026 | failed trajectory diagnosis and critical failure step identification        | threatens failure diagnosis framing                            | MEDIUM       | 01                     |
| SEARCH-010 | WorkArena++ enterprise web tasks                     | WorkArena++                                         |             2024 | enterprise workflow benchmark                                               | task realism anchor                                            | MEDIUM       | 01, 10                 |
| SEARCH-011 | Agent Q MCTS self-critique DPO web agents            | Agent Q                                             |             2024 | search/self-critique/DPO for web agents                                     | threatens search/planning improvement claim                    | MEDIUM       | 01                     |
| SEARCH-012 | Web agent robustness perturbation benchmark          | StressWeb or diagnostic robustness benchmark family |             2026 | layout/DOM/semantic/execution perturbation style benchmark                  | threatens robustness novelty; supports OOD split design        | HIGH         | 01, 05, 10             |
| SEARCH-013 | value of computation planning                        | rational metareasoning / VOC literature             |        classical | computation as costly action                                                | supports decision-relevant compute framing                     | MEDIUM       | 09                     |
| SEARCH-014 | Bayesian model selection / likelihood ratio          | Bayesian model comparison literature                |        classical | evidence-based hypothesis comparison                                        | supports falsification score analogy                           | LOW          | 09                     |
| SEARCH-015 | change-point detection latent regime RL              | change-point/regime shift literature                |            mixed | adapts to nonstationary regimes                                             | supports but does not validate GUI grammar shift               | MEDIUM       | 09                     |
| SEARCH-016 | Web agents with world models                         | web agent world-model family                        |            2024+ | broad WM for action outcome/search exists                                   | broad world-model novelty is weak                              | HIGH         | 01                     |
| SEARCH-017 | RLDS / trajectory dataset schema                     | RL trajectory data format family                    |            2021+ | episode/step/action/reward logging precedent                                | informs data schema                                            | LOW          | 06                     |
| SEARCH-018 | Datasheets for Datasets / dataset cards              | dataset documentation standards                     |            2018+ | dataset transparency and intended-use reporting                             | informs dataset card                                           | LOW          | 06                     |
| SEARCH-019 | Reward shaping / potential-based shaping             | RL reward shaping literature                        |        classical | dense reward can preserve or distort objective                              | informs reward hacking guardrails                              | MEDIUM       | 08                     |
| SEARCH-020 | Calibration / ECE                                    | model calibration literature                        | classical/modern | reliability of predicted probabilities                                      | informs falsification calibration metric                       | LOW          | 08, 10                 |

---

## 15. Suspicion and Ambiguity Ledger

| Suspicion ID  | Item                      | Why Suspicious                                       | Failure Scenario                      | Required Next-Step Check                        | Severity | Status |
| ------------- | ------------------------- | ---------------------------------------------------- | ------------------------------------- | ----------------------------------------------- | -------- | ------ |
| SUSPICION-001 | Control grammar           | regime/action schema의 새 이름일 수 있음                     | reviewer says terminology is cosmetic | concept separation + no-grammar ablation        | CRITICAL | OPEN   |
| SUSPICION-002 | Regime vs grammar split   | examples may overlap heavily                         | latents collapse into one classifier  | merged-latent ablation and probes               | CRITICAL | OPEN   |
| SUSPICION-003 | Current hypothesis        | posterior mode와 executed hypothesis가 다를 수 있음         | persistence metric invalid            | define `h_exec` trace                           | CRITICAL | OPEN   |
| SUSPICION-004 | Falsification score       | model이 자기 score를 자기 검증할 수 있음                         | circular score                        | independent likelihood/held-out calibration     | CRITICAL | OPEN   |
| SUSPICION-005 | VeriGUI overlap           | action-effect verification + recovery already exists | novelty reduced to wording            | posterior/alternative/rewrite comparison        | CRITICAL | OPEN   |
| SUSPICION-006 | WebWorld overlap          | web world model + search already exists              | generic WM claim dead                 | reframe to grammar persistence                  | CRITICAL | OPEN   |
| SUSPICION-007 | CUWM overlap              | frozen agent + candidate action simulation           | test-time search not new              | grammar-specific alternative hypothesis benefit | CRITICAL | OPEN   |
| SUSPICION-008 | WAC overlap               | consequence simulation + action correction           | correction claim not enough           | grammar posterior + persistence metric          | CRITICAL | OPEN   |
| SUSPICION-009 | Synthetic environment     | toy/handcrafted criticism                            | reviewers reject realism              | anti-toy generator + real auxiliary             | HIGH     | OPEN   |
| SUSPICION-010 | Text-only smoke test      | may not transfer to GUI                              | early success misleading              | DOM-only bridge                                 | HIGH     | OPEN   |
| SUSPICION-011 | Reward effect             | reward may only be metric                            | objective disconnected                | reward-to-learning path                         | CRITICAL | OPEN   |
| SUSPICION-012 | Switch reward             | switching reward hacking                             | model oscillates                      | progress-linked valid switch only               | CRITICAL | OPEN   |
| SUSPICION-013 | Strong base LLM           | module effect may vanish                             | gains negligible with stronger base   | multi-base evaluation                           | HIGH     | OPEN   |
| SUSPICION-014 | Weak base LLM             | candidate set may miss recovery action               | rewrite cannot help                   | candidate expansion/macro composer              | HIGH     | OPEN   |
| SUSPICION-015 | 4-latent identifiability  | latents may not separate                             | ablations uninterpretable             | probes and MI/separability tests                | CRITICAL | OPEN   |
| SUSPICION-016 | 5-latent additions        | architecture bloat                                   | reviewer sees kitchen sink            | auxiliary heads unless proven                   | MEDIUM   | OPEN   |
| SUSPICION-017 | Screenshot feature        | necessity unclear                                    | hybrid complexity unjustified         | modality ablation                               | MEDIUM   | OPEN   |
| SUSPICION-018 | Top-k alternative         | k=3 arbitrary                                        | cherry-picked planning budget         | k sweep compute-matched                         | HIGH     | OPEN   |
| SUSPICION-019 | 1-3 step rollout          | may be too short                                     | long-horizon tasks fail               | horizon sweep                                   | HIGH     | OPEN   |
| SUSPICION-020 | Persistence metric        | may not explain success                              | cosmetic mechanism metric             | mediation/ablation analysis                     | CRITICAL | OPEN   |
| SUSPICION-021 | Compute gate              | may equal uncertainty gate                           | no novelty                            | uncertainty-only baseline                       | HIGH     | OPEN   |
| SUSPICION-022 | Alternative effect table  | counterfactual oracle leakage                        | model learns oracle                   | hidden counterfactual bucket only               | CRITICAL | OPEN   |
| SUSPICION-023 | Grammar labels            | too clean synthetic supervision                      | classifier solves benchmark           | noisy/weak/held-out grammar splits              | HIGH     | OPEN   |
| SUSPICION-024 | Real benchmark labels     | hidden grammar absent                                | core metrics impossible               | auxiliary only framing                          | HIGH     | OPEN   |
| SUSPICION-025 | Loss complexity           | too many objectives                                  | contribution unclear                  | main 6 + auxiliary appendix                     | HIGH     | OPEN   |
| SUSPICION-026 | Selector/rewrite confound | final selector may drive gains                       | WM contribution unclear               | disable rollout/rewrite separately              | HIGH     | OPEN   |
| SUSPICION-027 | Robustness novelty        | robustness benchmarks may cover perturbation         | OOD claim derivative                  | grammar-persistence mechanism focus             | HIGH     | OPEN   |
| SUSPICION-028 | Bayesian language         | exact inference not implemented                      | theory overclaim                      | learned approximation wording                   | MEDIUM   | OPEN   |
| SUSPICION-029 | Search citations          | current anchors lack citation-grade metadata         | weak related work                     | add URL/arXiv/OpenReview/DOI in Step 01         | HIGH     | OPEN   |
| SUSPICION-030 | Claude Code routing       | refs exist but reading policy may be underused       | Claude reads wrong context            | enforce Context Routing section in all files    | MEDIUM   | OPEN   |

---

## 16. Merge and Conflict Ledger

### 16.1 Merge Ledger

| Merge ID  | Items Merged                                                               | Reason                              | Resulting Ref ID | Residual Risk                                             |
| --------- | -------------------------------------------------------------------------- | ----------------------------------- | ---------------- | --------------------------------------------------------- |
| MERGE-001 | wrong hypothesis persistence, wrong control grammar persistence            | same intended core failure          | REF-CORE-001     | state-wrong vs grammar-wrong distinction may still matter |
| MERGE-002 | action-effect evidence, failure evidence, observed effect discrepancy      | all evidence used for falsification | REF-CONCEPT-009  | semantic vs visual evidence may be overmerged             |
| MERGE-003 | rewrite action, action-interface rewrite, intent-to-action mapping rewrite | same mechanism family               | REF-CONCEPT-010  | executable macro details unresolved                       |
| MERGE-004 | compute reallocation, decision relevance gate, VOC gate                    | same compute-control idea           | REF-CONCEPT-011  | heuristic vs theory distinction unresolved                |
| MERGE-005 | synthetic GUI env, controlled Web/GUI env, Playwright/React generator      | same main environment seed          | REF-DATA-002     | implementation stack not fixed                            |
| MERGE-006 | recovery delay, failure-to-progress delay                                  | same recovery timing metric         | REF-METRIC-007   | recovery definition must be exact                         |
| MERGE-007 | alternative rollout fidelity, counterfactual rollout accuracy              | same WM quality metric family       | REF-METRIC-008   | counterfactual supervision synthetic-only                 |
| MERGE-008 | valid switch reward, hypothesis-switch reward                              | same high-risk reward               | REF-REWARD-005   | must remain conditional                                   |

### 16.2 Conflict Ledger

| Conflict ID  | Item A                            | Item B                           | Conflict                                                  | Resolution Needed In | Severity |
| ------------ | --------------------------------- | -------------------------------- | --------------------------------------------------------- | -------------------- | -------- |
| CONFLICT-001 | `z_regime`                        | `z_control_grammar`              | definitions overlap                                       | 03, 07, 10           | CRITICAL |
| CONFLICT-002 | falsification as likelihood ratio | falsification as classifier      | different supervision/calibration                         | 08, 09               | HIGH     |
| CONFLICT-003 | synthetic labels                  | real benchmark validation        | core metrics need labels unavailable in real benchmarks   | 06, 10               | HIGH     |
| CONFLICT-004 | screenshot feature                | structured log-centered model    | visual modality may be unnecessary or confounding         | 05, 07, 10           | MEDIUM   |
| CONFLICT-005 | switch reward                     | temporal consistency/switch cost | one encourages switching, one suppresses it               | 08                   | HIGH     |
| CONFLICT-006 | frozen base candidates            | rewrite macro generation         | base may not propose recovery primitives                  | 07, 09               | HIGH     |
| CONFLICT-007 | main loss simplicity              | full mechanism complexity        | too few losses miss mechanism, too many blur contribution | 08                   | HIGH     |
| CONFLICT-008 | Bayesian framing                  | amortized learned posterior      | exactness overclaim risk                                  | 09                   | MEDIUM   |
| CONFLICT-009 | no-effect evidence                | loading/delayed effect           | no-effect may not mean wrong grammar                      | 05, 06, 09           | CRITICAL |
| CONFLICT-010 | progress reward                   | long-horizon correctness         | immediate progress can be misleading                      | 08, 10               | HIGH     |

---

## 17. Unknown Ledger

| Unknown ID      | Unknown                                        | Why It Matters                  | Possible Resolution                            | Can Be Used As Final Claim?            | Assigned Step |
| --------------- | ---------------------------------------------- | ------------------------------- | ---------------------------------------------- | -------------------------------------- | ------------- |
| REF-UNKNOWN-001 | grammar를 regime과 분리할 수 있는가?                    | core novelty depends on it      | taxonomy + merged/no-grammar ablation + probes | NO / EXPERIMENT_ONLY                   | 03, 07, 10    |
| REF-UNKNOWN-002 | persistence를 신뢰성 있게 측정할 수 있는가?                 | core metric depends on `h_exec` | define executed hypothesis trace               | NO / DESIGN_DECISION_REQUIRED          | 02, 06        |
| REF-UNKNOWN-003 | falsification score가 OOD에서 calibration되는가?     | gate reliability                | calibration curves, OOD tests                  | NO / EXPERIMENT_ONLY                   | 08, 10        |
| REF-UNKNOWN-004 | text-only 성공이 GUI로 전이되는가?                      | early gate validity             | DOM-only bridge test                           | NO / EXPERIMENT_ONLY                   | 04, 05        |
| REF-UNKNOWN-005 | synthetic env가 toy로 보이지 않을 만큼 충분한가?            | reviewer acceptance             | anti-toy task generator + real auxiliary       | NO / EXPERIMENT_ONLY                   | 05, 10        |
| REF-UNKNOWN-006 | WebWorld/CUWM/WAC가 너무 가까운가?                    | novelty risk                    | threat map                                     | NO / SEARCH_REQUIRED                   | 01            |
| REF-UNKNOWN-007 | VeriGUI가 이미 충분한가?                              | verification overlap            | verifier-only baseline                         | NO / SEARCH_REQUIRED + EXPERIMENT_ONLY | 01, 10        |
| REF-UNKNOWN-008 | 어떤 base model 조합이 적절한가?                        | generality/effect size          | multi-base plan                                | NO / DESIGN_DECISION_REQUIRED          | 10            |
| REF-UNKNOWN-009 | k=3 alternative가 적절한가?                         | planning quality/cost           | k sweep                                        | NO / EXPERIMENT_ONLY                   | 09, 10        |
| REF-UNKNOWN-010 | 1~3 step rollout이 충분한가?                        | long-horizon applicability      | horizon sweep                                  | NO / EXPERIMENT_ONLY                   | 09, 10        |
| REF-UNKNOWN-011 | real action-effect log를 어떻게 수집할 것인가?           | auxiliary validation            | browser instrumentation protocol               | NO / DESIGN_DECISION_REQUIRED          | 06            |
| REF-UNKNOWN-012 | macro rewrite가 안정적으로 실행 가능한가?                  | rewrite claim                   | Playwright primitive/macro schema              | NO / EXPERIMENT_ONLY                   | 07, 09        |
| REF-UNKNOWN-013 | progress reward가 reward hacking을 만드는가?         | objective validity              | anti-hacking tests                             | NO / EXPERIMENT_ONLY                   | 08            |
| REF-UNKNOWN-014 | persistence가 success를 설명하는가?                   | metric credibility              | mediation/regression analysis                  | NO / EXPERIMENT_ONLY                   | 10            |
| REF-UNKNOWN-015 | label leakage를 막을 수 있는가?                       | synthetic validity              | visibility contract + audit                    | NO / DESIGN_DECISION_REQUIRED          | 06            |
| REF-UNKNOWN-016 | 고위협 baseline 구현 가능성                            | practical feasibility           | full/approx/weak baseline tiering              | NO / DESIGN_DECISION_REQUIRED          | 10            |
| REF-UNKNOWN-017 | screenshot feature가 필요한가?                      | complexity                      | modality ablation                              | NO / EXPERIMENT_ONLY                   | 05, 07, 10    |
| REF-UNKNOWN-018 | Bayesian framing이 방어 가능한가?                     | theory credibility              | Bayesian-inspired learned approximation        | NO / DESIGN_DECISION_REQUIRED          | 09            |
| REF-UNKNOWN-019 | collapsed latent가 더 잘하면 어떻게 할 것인가?             | factorization claim risk        | collapsed baseline and failure interpretation  | NO / EXPERIMENT_ONLY                   | 07, 10        |
| REF-UNKNOWN-020 | no-reward model이 비슷하면 reward claim은 어떻게 할 것인가? | objective claim risk            | no-reward ablation                             | NO / EXPERIMENT_ONLY                   | 08, 10        |
| REF-UNKNOWN-021 | real benchmark에서 hidden labels 없이 무엇을 측정할 것인가? | external validity               | weak proxies, qualitative traces               | NO / DESIGN_DECISION_REQUIRED          | 10            |
| REF-UNKNOWN-022 | reviewer가 synthetic-only를 거부하면 어떻게 할 것인가?      | acceptance risk                 | optional real auxiliary + mechanism framing    | NO / STRATEGIC_RISK                    | FINAL         |

---

## 18. Step Handoff Map

| Handoff ID      | Next File                              | Required Input Refs                                                           | Required Output                                                       | Must Not Assume                                      |
| --------------- | -------------------------------------- | ----------------------------------------------------------------------------- | --------------------------------------------------------------------- | ---------------------------------------------------- |
| REF-HANDOFF-001 | `01_RELATED_WORK_THREAT_MAP.md`        | SEARCH-001..020, REF-CORE-020, REF-BASELINE-008..009, SUSPICION-005..008      | WebWorld/CUWM/WAC/VeriGUI/AgentRx/WebArena/OSWorld 등 threat map       | novelty survives라고 가정 금지                             |
| REF-HANDOFF-002 | `02_PROBLEM_NOVELTY_FALSIFICATION.md`  | REF-PROBLEM-001..012, REF-METRIC-005, REF-CONCEPT-007, SUSPICION-001..008     | falsifiable problem claims and minimal counterexamples                | wrong-control-grammar가 독립 failure라고 선결정 금지           |
| REF-HANDOFF-003 | `03_CORE_CONCEPT_TAXONOMY.md`          | REF-CONCEPT-001..020, REF-LATENT-001..014                                     | regime/grammar/state/reveal/shift/current/alt hypothesis taxonomy     | regime과 grammar를 조용히 중복시키지 말 것                       |
| REF-HANDOFF-004 | `04_TEXT_ONLY_SMOKE_TESTBED.md`        | REF-DATA-001, REF-PROBLEM-001..004, REF-CONCEPT-009..013, REF-REWARD-001..007 | text-only environment, tasks, labels, pass/fail gates                 | lexical cues로 label을 노출하지 말 것                        |
| REF-HANDOFF-005 | `05_SYNTHETIC_WEB_GUI_ENVIRONMENT.md`  | REF-DATA-002..020, SEARCH-003, SEARCH-012, REF-METRIC-003                     | controlled Web/GUI generator and OOD splits                           | toy-only claims 금지                                   |
| REF-HANDOFF-006 | `06_DATA_SCHEMA_AND_LABELING.md`       | REF-DATA-003..020, REF-CONCEPT-007..019, REF-UNKNOWN-015                      | schema, labels, visibility contract, leakage guardrails               | hidden labels를 agent input으로 주지 말 것                  |
| REF-HANDOFF-007 | `07_LATENT_ARCHITECTURE_DESIGN.md`     | REF-LATENT-001..014, REF-ARCH-001..020, REF-ABLATION-001..012                 | architecture candidates and ablation-ready module contracts           | 4-latent를 최종 확정하지 말 것                                |
| REF-HANDOFF-008 | `08_LOSS_REWARD_TRAINING_OBJECTIVE.md` | REF-LOSS-001..018, REF-REWARD-001..012, SUSPICION-011..012                    | staged objective, reward pathways, hacking tests                      | switch reward를 unconditional positive reward로 두지 말 것 |
| REF-HANDOFF-009 | `09_PLANNING_THEORY_ALGORITHM.md`      | REF-CONCEPT-007..011, REF-ARCH-010..017, SEARCH-013..015                      | falsification/VOC algorithm and pseudo-code                           | exact Bayesian inference라고 주장하지 말 것                  |
| REF-HANDOFF-010 | `10_EVALUATION_BASELINE_ABLATION.md`   | REF-METRIC-001..016, REF-BASELINE-001..010, REF-ABLATION-001..012             | evaluation matrix, compute matching, ablation, failure interpretation | high-threat baseline을 생략하지 말 것                       |
| REF-HANDOFF-011 | `FINAL_RESEARCH_BLUEPRINT.md`          | all previous finalized step outputs                                           | final coherent blueprint with claim-evidence contract                 | 00 파일만 보고 final blueprint 작성 금지                      |

---

## 19. Claude Code Implementation Readiness Ledger

이 파일은 구현 파일이 아니지만, 구현 가능성을 높이기 위해 다음 기준을 후속 파일들이 반드시 만족해야 한다.

| Implementation ID | Implementation Need                 | Why It Matters              | Required Later File | Blocking Risk                 |
| ----------------- | ----------------------------------- | --------------------------- | ------------------- | ----------------------------- |
| IMPL-001          | `h_exec` trace schema               | persistence metric 계산에 필수   | 06, 09              | 없으면 core metric 불가            |
| IMPL-002          | visibility-safe observation builder | hidden label leakage 방지     | 06                  | 없으면 실험 무효                     |
| IMPL-003          | text-only JSON schema               | smoke test 구현 시작점           | 04                  | 없으면 초기 viability test 불가      |
| IMPL-004          | synthetic browser action API        | Web/GUI 환경 구현               | 05, 06              | rewrite/macro 실행 불가           |
| IMPL-005          | action-effect diff logger           | falsification evidence 생성   | 05, 06              | evidence pathway 불가           |
| IMPL-006          | counterfactual effect generator     | rollout fidelity/evaluation | 05, 06, 09          | alternative rollout metric 불가 |
| IMPL-007          | latent head I/O contract            | architecture 구현             | 07                  | module 연결 불명확                 |
| IMPL-008          | objective-to-label map              | loss 구현                     | 08                  | loss가 이름만 존재                  |
| IMPL-009          | planning pseudo-code                | algorithm 구현                | 09                  | method 재현 불가                  |
| IMPL-010          | baseline/ablation runner spec       | 평가 구현                       | 10                  | claim 검증 불가                   |
| IMPL-011          | anti-leakage tests                  | dataset validity            | 06, 10              | shortcut 문제                   |
| IMPL-012          | compute budget logger               | compute-matched 평가          | 09, 10              | planning claim 불공정            |

---

## 20. Quality Gate Result

| Gate ID  | Gate                                       | PASS/FAIL/PARTIAL | Evidence                                                                              | If Not PASS, Blocker                           |
| -------- | ------------------------------------------ | ----------------- | ------------------------------------------------------------------------------------- | ---------------------------------------------- |
| QG-00-01 | 원본 핵심 주장 20개 이상 추출                         | PASS              | REF-CORE-001..022                                                                     | 없음                                             |
| QG-00-02 | architecture component 15개 이상 추출           | PASS              | REF-ARCH-001..020                                                                     | 없음                                             |
| QG-00-03 | loss/reward/metric seed 충분성                | PASS              | REF-LOSS-001..018, REF-REWARD-001..012, REF-METRIC-001..016                           | 없음                                             |
| QG-00-04 | search sanity check 12개 이상 수행              | PASS              | SEARCH-001..020                                                                       | Step 01에서 citation-grade 확인 필요                 |
| QG-00-05 | suspicion 20개 이상 기록                        | PASS              | SUSPICION-001..030                                                                    | 없음                                             |
| QG-00-06 | unknown 15개 이상 기록                          | PASS              | REF-UNKNOWN-001..022                                                                  | 없음                                             |
| QG-00-07 | all later steps have handoff refs          | PASS              | REF-HANDOFF-001..011                                                                  | 없음                                             |
| QG-00-08 | no final claim was prematurely accepted    | PASS_WITH_RISK    | core claims marked SOURCE_ONLY/CONTESTED/SEARCH_SUPPORTED/DESIGN_CANDIDATE, not final | later files must preserve status               |
| QG-00-09 | all refs have unique IDs                   | PASS              | category-level unique IDs used                                                        | manual audit recommended                       |
| QG-00-10 | no unsupported claim is marked as verified | PASS              | SEARCH_SUPPORTED only means sanity anchor, not novelty proof                          | Step 01 must verify details                    |
| QG-00-11 | high-threat related work surfaced          | PASS              | WebWorld, CUWM, WAC, VeriGUI, AgentRx, robustness benchmark anchors included          | threat depth unresolved                        |
| QG-00-12 | blocker logic exists                       | PASS              | Unknown/Suspicion/Handoff ledgers assign unresolved checks                            | must not skip later validation                 |
| QG-00-13 | Claude Code routing exists                 | PASS              | Section 3 provides routing table                                                      | later files should replicate routing           |
| QG-00-14 | implementation readiness seed exists       | PASS              | IMPL-001..012                                                                         | detailed implementation belongs to later steps |

---

## 21. Final Statement of This File

`00_MASTER_REFERENCE.md`는 reference ledger이며, 최종 연구 설계도가 아니다.

현재 가장 강한 thesis candidate는 다음이다.

```text
Web/GUI agents can fail by persistently executing actions under a wrong intent-to-action control-grammar hypothesis, and a falsification-guided planning layer may reduce this failure by using action-effect evidence to compare alternative grammar hypotheses and rewrite executable actions only when the decision would change.
```

그러나 다음 항목이 검증되기 전까지 final paper claim으로 승격하면 안 된다.

* `control grammar`가 단순 regime/action schema의 다른 이름이 아닌지 검증해야 한다.
* wrong-control-grammar persistence가 action failure, visual grounding failure, verification failure, planning failure와 분리되는지 증명해야 한다.
* WebWorld, CUWM, WAC, VeriGUI, AgentRx, robustness benchmark가 이미 핵심을 다룬 것은 아닌지 확인해야 한다.
* synthetic labels가 leakage 없이 제공되는지 검증해야 한다.
* falsification-guided compute reallocation이 verifier-only, next-state WM, always-plan, uncertainty-gated baseline보다 compute-matched 조건에서 강한지 검증해야 한다.
* action-interface rewrite가 실제 executable primitive/macro로 구현 가능한지 확인해야 한다.
* real benchmark auxiliary validation에서 hidden grammar label 없이 무엇을 측정할 수 있는지 명확히 해야 한다.
* no-control-grammar ablation, no-falsification ablation, no-alternative-rollout ablation이 무너지지 않으면 관련 claim을 약화하거나 폐기해야 한다.

다음 필수 파일:

```text
01_RELATED_WORK_THREAT_MAP.md
```

```
```
