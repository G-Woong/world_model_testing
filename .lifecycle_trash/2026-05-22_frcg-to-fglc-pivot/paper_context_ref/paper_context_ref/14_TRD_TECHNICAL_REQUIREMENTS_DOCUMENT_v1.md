---
file_id: STEP-14
title: Technical Requirements Document for FRCG-WM
version: v1.0
status: technical_requirements_contract_not_design_implementation
language: ko
depends_on:
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
  - 11_MODEL_DATASET_SCALE_AND_TRAINING_BUDGET.md
  - 12_DATA_COLLECTION_METHODOLOGY.md
  - 13_CLAUDE_CODE_EXECUTION_ROADMAP.md
  - FINAL_RESEARCH_BLUEPRINT.md
purpose:
  - FRCG-WM 연구 repo가 반드시 만족해야 하는 기술 요구사항을 기능/비기능/데이터/모델/학습/평가/운영/재현성/보안/검증 관점에서 정의한다.
  - Claude Code가 구현 단계에서 임의 해석하지 않도록 MUST/SHOULD/MAY 요구사항을 명확히 분리한다.
  - TRD 요구사항을 후속 TDD, repo scaffold, 테스트 계획, 구현 task로 추적 가능하게 만든다.
forbidden:
  - Do not include implementation-level class internals that belong in TDD.
  - Do not weaken hidden-label leakage constraints.
  - Do not remove required baselines or ablations.
  - Do not claim empirical results.
  - Do not treat optional real benchmark auxiliary validation as main evidence.
  - Do not start from paper-main VLM training before MVE gates pass.
next_files:
  - 15_TDD_TECHNICAL_DESIGN_DOCUMENT.md
  - 16_REPO_SCAFFOLD_AND_TEST_PLAN.md
  - 17_IMPLEMENTATION_TASK_BREAKDOWN.md
---

# 14_TRD_TECHNICAL_REQUIREMENTS_DOCUMENT.md

## 1. File Purpose

이 문서는 FRCG-WM 연구 시스템의 **Technical Requirements Document(TRD)**다.  
TRD의 목적은 “어떻게 구현할지”가 아니라, **무엇을 반드시 만족해야 하는지**를 요구사항 수준에서 고정하는 것이다.

이 문서는 다음 질문에 답한다.

1. 시스템은 어떤 기능을 반드시 제공해야 하는가?
2. 어떤 데이터와 label을 수집·저장·검증해야 하는가?
3. 어떤 모델/학습/평가 요구사항을 만족해야 하는가?
4. 어떤 보안·leakage·재현성·운영 요구사항을 만족해야 하는가?
5. 어떤 테스트와 acceptance criteria를 통과해야 다음 단계로 넘어갈 수 있는가?
6. Claude Code가 구현 과정에서 무엇을 절대 가정하면 안 되는가?

이 문서는 구현 설계서(TDD)가 아니다.  
구체적인 class 내부 구조, 함수 signature, 모듈별 알고리즘 상세는 `15_TDD_TECHNICAL_DESIGN_DOCUMENT.md`에서 정의한다.

---

## 2. Requirement Language

이 문서는 다음 용어를 사용한다.

| Term | Meaning |
|---|---|
| MUST | 반드시 구현·만족해야 한다. 만족하지 못하면 해당 phase는 실패다. |
| SHOULD | 강하게 권장된다. 예외가 있으면 이유와 대체 방안을 기록해야 한다. |
| MAY | 선택 사항이다. 구현하지 않아도 core gate를 막지 않는다. |
| MUST NOT | 절대 해서는 안 된다. 위반 시 해당 데이터/실험/run은 무효다. |
| BLOCKER | 해결 전 다음 단계로 진행하면 안 되는 요구사항이다. |
| ACCEPTANCE CRITERION | 해당 요구사항이 만족됐는지 판단하는 검증 기준이다. |

---

## 3. System Scope

### 3.1 In Scope

| Scope ID | In-Scope Item | Description |
|---|---|---|
| SCOPE-IN-001 | 연구 문서 기반 repo scaffold | 00~14 문서에 기반한 구조화된 repo 생성 |
| SCOPE-IN-002 | text-only smoke environment | symbolic text environment, grammar engine, failure/recovery trajectories |
| SCOPE-IN-003 | synthetic Web/GUI environment | controlled browser-like environment, DOM/screenshot/a11y/action-effect logging |
| SCOPE-IN-004 | data schema and visibility validation | agent observation / hidden label / counterfactual / audit metadata 분리 |
| SCOPE-IN-005 | data collection pipeline | policy mixture rollout, failure/recovery/OOD/counterfactual collection |
| SCOPE-IN-006 | leakage and coverage audit | hidden label leakage, split leakage, coverage ratio 검증 |
| SCOPE-IN-007 | text-only FRCG model | small mechanism model for viability |
| SCOPE-IN-008 | frozen VLM MVE adapter | frozen VLM embeddings + trainable FRCG heads |
| SCOPE-IN-009 | latent architecture heads | z_state, z_regime, z_control_grammar, z_change_point and auxiliary heads |
| SCOPE-IN-010 | objective implementation | action-effect, progress, grammar, falsification, rewrite, auxiliary losses |
| SCOPE-IN-011 | planning modules | falsification score, alternative hypothesis proposer, rollout, decision gate, rewrite |
| SCOPE-IN-012 | evaluation suite | metrics, baselines, ablations, compute-matched evaluation, failure interpretation |
| SCOPE-IN-013 | experiment reporting | real logs 기반 tables/figures/reports |
| SCOPE-IN-014 | reproducibility package | seeds, configs, manifests, hashes, versioning |

### 3.2 Out of Scope

| Scope ID | Out-of-Scope Item | Reason |
|---|---|---|
| SCOPE-OUT-001 | real production website scraping as main dataset | privacy/legal/reproducibility/counterfactual label 부재 |
| SCOPE-OUT-002 | pixel-level next screenshot generation as core objective | compute explosion, not necessary for latent world model |
| SCOPE-OUT-003 | full fine-tuning 7B/72B VLM at initial stage | cost and debugging risk |
| SCOPE-OUT-004 | final paper result fabrication | empirical result must come from runs |
| SCOPE-OUT-005 | hidden labels as inference inputs | invalidates the scientific claim |
| SCOPE-OUT-006 | success-rate-only evaluation | mechanism claim cannot be validated |
| SCOPE-OUT-007 | replacing all baselines with weak baselines | reviewer defense fails |
| SCOPE-OUT-008 | using optional real benchmark as main causal evidence | hidden labels/counterfactuals unavailable |

---

## 4. Stakeholders and Users

| Stakeholder | Need | TRD Impact |
|---|---|---|
| Research lead | claim이 metric/baseline/ablation으로 방어되는지 확인 | traceability and evaluation requirements |
| Claude Code | 필요한 context를 읽고 단계별 구현 | read policy, phase gates, module requirements |
| Model engineer | architecture/loss/training loop 구현 | model/training requirements |
| Data engineer | synthetic data collector/schema/exporter 구현 | data collection and validation requirements |
| Evaluation engineer | baselines/ablations/metrics 구현 | evaluation requirements |
| Reviewer | novelty, fairness, compute, ablation, limitations 확인 | scientific acceptance criteria |
| Future maintainer | run 재현 및 문서 추적 | reproducibility/versioning requirements |

---

## 5. High-Level System Requirements

| Req ID | Requirement | Priority | Acceptance Criteria |
|---|---|---|---|
| SYS-REQ-001 | 시스템은 text-only smoke test부터 시작해야 한다. | MUST | text-only data/model/eval phase가 repo에 존재 |
| SYS-REQ-002 | 시스템은 synthetic Web/GUI controlled data를 main causal dataset으로 지원해야 한다. | MUST | DOM/screenshot/a11y/action-effect/hidden label/counterfactual export 가능 |
| SYS-REQ-003 | 시스템은 hidden label을 inference input에서 완전히 배제해야 한다. | MUST | runtime assertion and tests pass |
| SYS-REQ-004 | 시스템은 failure/recovery/reveal/shift/control-grammar coverage를 수집·검증해야 한다. | MUST | coverage report generated and threshold checked |
| SYS-REQ-005 | 시스템은 Frozen Base VLM/LLM + proposed module 비교 구조를 지원해야 한다. | MUST | same base model with/without FRCG modules evaluable |
| SYS-REQ-006 | 시스템은 no-control-grammar/no-falsification/no-alternative/no-rewrite ablations를 지원해야 한다. | MUST | ablation configs and runners exist |
| SYS-REQ-007 | 시스템은 verifier-only, next-state-WM-only, uncertainty-gated, always-plan baselines를 지원해야 한다. | MUST | baseline suite runnable |
| SYS-REQ-008 | 시스템은 compute-matched evaluation을 기록해야 한다. | MUST | planning_calls, rollout_steps, wall-clock proxy logged |
| SYS-REQ-009 | 시스템은 fake empirical result를 생성하지 않아야 한다. | MUST NOT | report generator only reads run logs |
| SYS-REQ-010 | 시스템은 configs/seeds/manifests/hashes를 통해 재현성을 보장해야 한다. | MUST | manifest and config hash written for every run |
| SYS-REQ-011 | 시스템은 MVE gate 통과 전 paper-main training을 실행하지 않아야 한다. | MUST NOT | run guard blocks main config unless previous gate artifacts exist |
| SYS-REQ-012 | 시스템은 failure interpretation protocol을 결과 보고에 포함해야 한다. | MUST | evaluation report includes failure interpretation table |

---

## 6. Functional Requirements

### 6.1 Documentation and Context Requirements

| Req ID | Requirement | Priority | Acceptance Criteria |
|---|---|---|---|
| DOC-REQ-001 | repo는 `docs/` 아래 00~14 문서를 보관해야 한다. | MUST | docs exist and are referenced in README |
| DOC-REQ-002 | 각 major module은 source-doc contract docstring을 가져야 한다. | MUST | grep/docstring test passes |
| DOC-REQ-003 | Claude Code 작업 전에 관련 MD를 읽어야 하는 read policy를 README 또는 roadmap에 포함해야 한다. | MUST | `13_CLAUDE_CODE_EXECUTION_ROADMAP.md` linked |
| DOC-REQ-004 | scientific definition 변경 시 source MD와 downstream docs를 업데이트해야 한다. | MUST | changelog or doc update required |
| DOC-REQ-005 | generated reports는 empirical/non-empirical 구분을 명시해야 한다. | MUST | report header includes status |

### 6.2 Schema and Visibility Requirements

| Req ID | Requirement | Priority | Acceptance Criteria |
|---|---|---|---|
| SCHEMA-REQ-001 | episode and step schema를 명시적으로 정의해야 한다. | MUST | schema tests pass |
| SCHEMA-REQ-002 | visibility bucket은 AGENT_OBSERVATION, TRAINING_SUPERVISION, EVALUATION_ONLY, COUNTERFACTUAL_ONLY, AUDIT_METADATA를 포함해야 한다. | MUST | enum and validation tests |
| SCHEMA-REQ-003 | agent observation builder는 forbidden hidden fields를 제거해야 한다. | MUST | hidden-field injection test fails as expected |
| SCHEMA-REQ-004 | counterfactual table은 COUNTERFACTUAL_ONLY bucket에 저장해야 한다. | MUST | counterfactual exclusion test |
| SCHEMA-REQ-005 | split_id, ood_type, template_id, seed는 model input에 포함되면 안 된다. | MUST NOT | leakage auditor detects and blocks |
| SCHEMA-REQ-006 | schema version, generator version, dataset version을 manifest에 기록해야 한다. | MUST | manifest fields exist |
| SCHEMA-REQ-007 | public observation과 hidden labels를 같은 nested object에 섞지 않아야 한다. | SHOULD | structure audit passes |
| SCHEMA-REQ-008 | schema validation은 data collection 전후 모두 실행되어야 한다. | MUST | pre/post validation logs exist |

### 6.3 Text-Only Environment Requirements

| Req ID | Requirement | Priority | Acceptance Criteria |
|---|---|---|---|
| TEXT-REQ-001 | text-only environment는 최소 8개 task family를 지원해야 한다. | MUST | generator coverage report |
| TEXT-REQ-002 | hidden control grammar와 public text를 분리해야 한다. | MUST | lexical leakage audit passes |
| TEXT-REQ-003 | wrong-grammar failure, recovery, reveal, shift, delayed/no-op cases를 생성해야 한다. | MUST | coverage thresholds pass |
| TEXT-REQ-004 | oracle, wrong-grammar, retry, random, recovery policy mixture를 지원해야 한다. | MUST | policy_id distribution report |
| TEXT-REQ-005 | text-only transition은 deterministic replay 가능해야 한다. | MUST | replay test passes |
| TEXT-REQ-006 | text-only data는 final paper main evidence로 단독 사용되면 안 된다. | MUST NOT | report labels as smoke only |

### 6.4 Synthetic Web/GUI Environment Requirements

| Req ID | Requirement | Priority | Acceptance Criteria |
|---|---|---|---|
| GUI-REQ-001 | environment는 DOM snapshot을 수집해야 한다. | MUST | pre/post DOM stored |
| GUI-REQ-002 | environment는 screenshot을 저장하거나 deterministic reference를 제공해야 한다. | MUST | screenshot paths or refs valid |
| GUI-REQ-003 | environment는 accessibility tree를 수집해야 한다. | SHOULD | a11y snapshot present |
| GUI-REQ-004 | environment는 hidden regime/control grammar oracle labels를 생성해야 한다. | MUST | labels present outside agent obs |
| GUI-REQ-005 | environment는 reveal/shift/delay/noisy/stale event를 생성해야 한다. | MUST | event labels and coverage report |
| GUI-REQ-006 | environment는 action precondition과 expected effect schema를 가져야 한다. | MUST | action-effect logger validates |
| GUI-REQ-007 | environment는 counterfactual alternative action effect를 생성해야 한다. | MUST for synthetic | CF table present and hidden |
| GUI-REQ-008 | environment는 deterministic replay를 지원해야 한다. | MUST | replay validator pass |
| GUI-REQ-009 | environment는 OOD split 생성 규칙을 지원해야 한다. | MUST | split integrity report |
| GUI-REQ-010 | environment는 production/private website scraping을 main data source로 사용하면 안 된다. | MUST NOT | source audit |

### 6.5 Data Collection Requirements

| Req ID | Requirement | Priority | Acceptance Criteria |
|---|---|---|---|
| DATA-REQ-001 | data collector는 policy mixture rollout을 지원해야 한다. | MUST | policy distribution logged |
| DATA-REQ-002 | failed-action ratio는 MVE/main training set에서 최소 20% 이상이어야 한다. | MUST | coverage auditor |
| DATA-REQ-003 | recovery ratio는 최소 8% 이상이어야 한다. | MUST | coverage auditor |
| DATA-REQ-004 | repeated wrong mapping ratio는 최소 8% 이상이어야 한다. | MUST | coverage auditor |
| DATA-REQ-005 | shift event ratio는 최소 8% 이상이어야 한다. | MUST | coverage auditor |
| DATA-REQ-006 | delayed/noisy/stale effect ratio는 최소 5% 이상이어야 한다. | MUST | coverage auditor |
| DATA-REQ-007 | same layout/different grammar와 different layout/same grammar examples를 포함해야 한다. | MUST | pair coverage report |
| DATA-REQ-008 | OOD-control grammar split은 반드시 존재해야 한다. | MUST | split files exist |
| DATA-REQ-009 | dataset shard는 leakage audit 통과 전 training loader에 사용되면 안 된다. | MUST NOT | dataloader guard |
| DATA-REQ-010 | data export는 JSONL/parquet/assets layout을 명시해야 한다. | SHOULD | manifest references outputs |
| DATA-REQ-011 | rejected episodes는 reason과 함께 보존해야 한다. | SHOULD | rejected log exists |
| DATA-REQ-012 | dataset generation은 seed/config hash를 기록해야 한다. | MUST | manifest hash exists |

### 6.6 Model Architecture Requirements

| Req ID | Requirement | Priority | Acceptance Criteria |
|---|---|---|---|
| MODEL-REQ-001 | system은 text-only tiny model을 지원해야 한다. | MUST | MODEL-T0 train/eval scripts |
| MODEL-REQ-002 | system은 frozen VLM adapter를 지원해야 한다. | MUST | frozen backbone params verified |
| MODEL-REQ-003 | VLM full fine-tuning은 MVE/main 초기 요구사항이 아니다. | MUST NOT initially | config guard |
| MODEL-REQ-004 | model은 z_state, z_regime, z_control_grammar, z_change_point heads를 지원해야 한다. | MUST | head outputs and losses |
| MODEL-REQ-005 | model은 collapsed/merged/hierarchical variants를 ablation으로 지원해야 한다. | MUST | ablation configs |
| MODEL-REQ-006 | model은 action-effect encoder와 history encoder를 포함해야 한다. | MUST | module tests |
| MODEL-REQ-007 | model은 falsification scorer를 포함해야 한다. | MUST | scoring function tests |
| MODEL-REQ-008 | model은 alternative hypothesis proposer를 포함해야 한다. | MUST | top-k proposer tests |
| MODEL-REQ-009 | model은 short rollout/progress predictor를 포함해야 한다. | MUST | rollout shape/metric tests |
| MODEL-REQ-010 | model은 intent-to-action rewrite module을 포함해야 한다. | MUST | rewrite validity tests |
| MODEL-REQ-011 | model input batch는 field names를 log해야 한다. | MUST | no hidden label in batch log |
| MODEL-REQ-012 | screenshot/VLM feature는 DOM/log-only ablation과 비교 가능해야 한다. | SHOULD | modality ablation configs |

### 6.7 Objective and Training Requirements

| Req ID | Requirement | Priority | Acceptance Criteria |
|---|---|---|---|
| TRAIN-REQ-001 | training은 staged mode를 지원해야 한다. | MUST | config stages exist |
| TRAIN-REQ-002 | L_action_effect를 구현해야 한다. | MUST | unit test and non-zero loss |
| TRAIN-REQ-003 | L_progress를 구현해야 한다. | MUST | progress prediction eval |
| TRAIN-REQ-004 | L_control_grammar를 구현해야 한다. | MUST | grammar head train target |
| TRAIN-REQ-005 | L_falsification을 구현해야 한다. | MUST | falsification PR/calibration |
| TRAIN-REQ-006 | L_intent_action_mapping 또는 rewrite supervision을 구현해야 한다. | MUST | rewrite target/eval |
| TRAIN-REQ-007 | valid switch reward는 4조건을 모두 만족할 때만 적용되어야 한다. | MUST | reward unit tests |
| TRAIN-REQ-008 | reward는 metric-only가 아니라 training/planning path에 연결되어야 한다. | MUST | reward path report |
| TRAIN-REQ-009 | gradient clipping 또는 stability guard를 지원해야 한다. | SHOULD | training config |
| TRAIN-REQ-010 | hidden labels는 target으로만 사용되고 input으로 사용되면 안 된다. | MUST | batch audit |
| TRAIN-REQ-011 | failed run은 run status로 기록되어야 한다. | MUST | run manifest |

### 6.8 Planning Requirements

| Req ID | Requirement | Priority | Acceptance Criteria |
|---|---|---|---|
| PLAN-REQ-001 | planner는 current hypothesis와 alternative hypothesis를 분리해야 한다. | MUST | tests verify h_cur vs h_alt |
| PLAN-REQ-002 | planner는 falsification score를 계산해야 한다. | MUST | scoring test |
| PLAN-REQ-003 | falsification은 단순 failure flag와 동일하면 안 된다. | MUST NOT | test with delayed/no-op valid case |
| PLAN-REQ-004 | planner는 top-k alternative hypothesis proposal을 지원해야 한다. | MUST | k sweep config |
| PLAN-REQ-005 | planner는 short-horizon rollout을 지원해야 한다. | MUST | horizon 1/3/5 configs |
| PLAN-REQ-006 | planner는 decision-relevance/VOC gate를 지원해야 한다. | MUST | gate unit tests |
| PLAN-REQ-007 | planner는 uncertainty-gated baseline과 분리되어야 한다. | MUST | separate baseline config |
| PLAN-REQ-008 | planner는 action-interface rewrite를 지원해야 한다. | MUST | rewrite tests |
| PLAN-REQ-009 | planner는 compute cost를 기록해야 한다. | MUST | compute logs |
| PLAN-REQ-010 | always-plan과 no-gate variants를 지원해야 한다. | MUST | ablation configs |

### 6.9 Evaluation Requirements

| Req ID | Requirement | Priority | Acceptance Criteria |
|---|---|---|---|
| EVAL-REQ-001 | evaluation은 success rate 외 mechanism metrics를 계산해야 한다. | MUST | metrics report |
| EVAL-REQ-002 | wrong-control-grammar persistence time을 계산해야 한다. | MUST | metric implemented |
| EVAL-REQ-003 | failed-action repetition rate를 계산해야 한다. | MUST | metric implemented |
| EVAL-REQ-004 | recovery delay를 계산해야 한다. | MUST | metric implemented |
| EVAL-REQ-005 | falsification precision/recall/calibration을 계산해야 한다. | MUST | metric implemented |
| EVAL-REQ-006 | alternative rollout fidelity를 계산해야 한다. | MUST for synthetic | metric implemented |
| EVAL-REQ-007 | progress per compute를 계산해야 한다. | MUST | compute metric implemented |
| EVAL-REQ-008 | compute-matched evaluation을 지원해야 한다. | MUST | matched budgets logged |
| EVAL-REQ-009 | verifier-only baseline을 포함해야 한다. | MUST | baseline result artifact |
| EVAL-REQ-010 | next-state-WM-only baseline을 포함해야 한다. | MUST | baseline result artifact |
| EVAL-REQ-011 | uncertainty-gated baseline을 포함해야 한다. | MUST | baseline result artifact |
| EVAL-REQ-012 | always-plan baseline을 포함해야 한다. | MUST | baseline result artifact |
| EVAL-REQ-013 | no-control-grammar ablation을 포함해야 한다. | MUST | ablation artifact |
| EVAL-REQ-014 | no-falsification ablation을 포함해야 한다. | MUST | ablation artifact |
| EVAL-REQ-015 | failure interpretation protocol을 출력해야 한다. | MUST | report table |
| EVAL-REQ-016 | fake numbers를 출력하면 안 된다. | MUST NOT | report reads logs only |

### 6.10 Reporting Requirements

| Req ID | Requirement | Priority | Acceptance Criteria |
|---|---|---|---|
| REPORT-REQ-001 | reports는 run manifest와 config hash를 표시해야 한다. | MUST | report header |
| REPORT-REQ-002 | reports는 negative/non-effect ablation을 숨기면 안 된다. | MUST NOT | all ablations listed |
| REPORT-REQ-003 | reports는 minimum evidence와 main-track-level evidence를 구분해야 한다. | MUST | section exists |
| REPORT-REQ-004 | qualitative examples는 selection rule을 포함해야 한다. | MUST | case selection table |
| REPORT-REQ-005 | real auxiliary result는 auxiliary로 표시해야 한다. | MUST | report label |
| REPORT-REQ-006 | empirical result 없는 문서는 blueprint/spec로 표시해야 한다. | MUST | status field |

---

## 7. Non-Functional Requirements

### 7.1 Reproducibility

| Req ID | Requirement | Priority | Acceptance Criteria |
|---|---|---|---|
| NFR-REPRO-001 | 모든 generation/training/eval run은 seed를 기록해야 한다. | MUST | manifest seed |
| NFR-REPRO-002 | 모든 run은 config hash를 기록해야 한다. | MUST | hash in manifest |
| NFR-REPRO-003 | dataset/model/schema version을 기록해야 한다. | MUST | manifest fields |
| NFR-REPRO-004 | split assignment는 deterministic이어야 한다. | MUST | split replay test |
| NFR-REPRO-005 | replay validator는 deterministic transition을 확인해야 한다. | MUST | replay report |
| NFR-REPRO-006 | random seed only change도 minor version으로 기록해야 한다. | SHOULD | versioning log |

### 7.2 Reliability

| Req ID | Requirement | Priority | Acceptance Criteria |
|---|---|---|---|
| NFR-REL-001 | data validation failure should stop training. | MUST | dataloader guard |
| NFR-REL-002 | leakage audit failure should stop all downstream runs. | MUST | run guard |
| NFR-REL-003 | missing baseline should block claim report. | MUST | report guard |
| NFR-REL-004 | compute log missing should block planning claim. | MUST | eval guard |
| NFR-REL-005 | unit tests should run before data generation and training. | SHOULD | CI script |

### 7.3 Performance

| Req ID | Requirement | Priority | Acceptance Criteria |
|---|---|---|---|
| NFR-PERF-001 | text-only training should be runnable on CPU/T4/consumer GPU. | SHOULD | config profile |
| NFR-PERF-002 | MVE VLM should support frozen embedding/cache mode. | MUST | cache option |
| NFR-PERF-003 | image resolution should be configurable. | MUST | config field |
| NFR-PERF-004 | batch size and gradient accumulation should be configurable. | MUST | config field |
| NFR-PERF-005 | evaluation should support subset/smoke mode. | SHOULD | eval subset config |
| NFR-PERF-006 | ablation runner should reuse cached embeddings where possible. | SHOULD | cache reuse option |

### 7.4 Security and Privacy

| Req ID | Requirement | Priority | Acceptance Criteria |
|---|---|---|---|
| NFR-SEC-001 | no private/user data should be collected. | MUST | source audit |
| NFR-SEC-002 | real website scraping should not be main collection method. | MUST NOT | config guard |
| NFR-SEC-003 | API keys/secrets should not be stored in repo. | MUST | secret scan |
| NFR-SEC-004 | reports should not include private credentials/paths. | MUST | output sanitizer |
| NFR-SEC-005 | external API use should be optional and logged. | SHOULD | config and log |

### 7.5 Maintainability

| Req ID | Requirement | Priority | Acceptance Criteria |
|---|---|---|---|
| NFR-MAINT-001 | modules should map to source docs. | MUST | docstring pattern |
| NFR-MAINT-002 | configs should avoid hard-coded paths. | MUST | config loader |
| NFR-MAINT-003 | tests should cover schema, data, planner, metrics. | MUST | pytest coverage |
| NFR-MAINT-004 | scientific constants should be configured, not buried in code. | SHOULD | config fields |
| NFR-MAINT-005 | each experiment run should be inspectable by manifest. | MUST | manifest artifact |

---

## 8. Data Requirements Summary

| Data Req ID | Data Object | Required Fields | Validation |
|---|---|---|---|
| DATAOBJ-REQ-001 | EpisodeRecord | episode_id, split_id, task, public_instruction, steps, success | schema validation |
| DATAOBJ-REQ-002 | StepRecord | public_obs, action, observed_effect, labels, audit | schema validation |
| DATAOBJ-REQ-003 | PublicObservation | sanitized DOM, screenshot_ref, a11y, public history | forbidden field scan |
| DATAOBJ-REQ-004 | HiddenLabelRecord | true_regime, true_control_grammar, true_change_point, reveal_shift | not in agent obs |
| DATAOBJ-REQ-005 | ActionEffectRecord | pre/post hash, dom diff, visual diff, effect type | replay validation |
| DATAOBJ-REQ-006 | CounterfactualRecord | candidate action, hypothesis, effect, progress, failure risk | CF-only validation |
| DATAOBJ-REQ-007 | RewardRecord | progress, failure penalty, recovery, switch, compute | reward tests |
| DATAOBJ-REQ-008 | AuditRecord | seed, config hash, template, leakage flags | audit-only validation |
| DATAOBJ-REQ-009 | SplitManifest | train/valid/test/OOD assignments | split integrity audit |
| DATAOBJ-REQ-010 | RunManifest | config, dataset, model, metrics, status | report validation |

---

## 9. Requirement Traceability Matrix

| Claim / Need | Requirement IDs | Source Docs | Verification |
|---|---|---|---|
| hidden labels excluded from inference | SCHEMA-REQ-002~006, DATAOBJ-REQ-003~004 | 06, 12, 13 | tests + leakage audit |
| wrong-control-grammar persistence measurable | TEXT-REQ, GUI-REQ, DATA-REQ, EVAL-REQ-002 | 02, 03, 06, 10 | metric tests |
| falsification beyond verification | MODEL-REQ-007, PLAN-REQ-002~003, EVAL-REQ-005, baseline verifier-only | 08, 09, 10 | ablation + baseline |
| alternative hypothesis rollout | MODEL-REQ-008~009, PLAN-REQ-004~005, EVAL-REQ-006 | 07, 09, 10 | rollout fidelity |
| decision-relevant compute | PLAN-REQ-006~010, EVAL-REQ-007~008 | 09, 10, 11 | compute-matched eval |
| data coverage for failure/recovery | DATA-REQ-001~012 | 11, 12 | coverage report |
| text-only before VLM | SYS-REQ-001, TEXT-REQ, CC gates | 04, 11, 13 | phase gates |
| no fake result | REPORT-REQ-006, SYS-REQ-009 | 10, FINAL, 13 | report guard |
| baseline fairness | EVAL-REQ-009~014 | 10 | eval runner |
| reproducibility | NFR-REPRO-001~006 | 06, 11, 12 | manifest/hash tests |

---

## 10. Phase Acceptance Criteria

### 10.1 P0 Documentation and Scaffold Acceptance

| Criterion | Required |
|---|---|
| docs/00~14 present | MUST |
| repo scaffold created | MUST |
| README includes forbidden assumptions | MUST |
| pytest runs | MUST |
| no model logic required | MUST |

### 10.2 P1 Schema Acceptance

| Criterion | Required |
|---|---|
| forbidden hidden fields rejected | MUST |
| counterfactual excluded from inference | MUST |
| episode/step schema validated | MUST |
| leakage auditor exists | MUST |
| tests pass | MUST |

### 10.3 P2 Text Data Acceptance

| Criterion | Required |
|---|---|
| 20k~100k transitions generated | SHOULD for full smoke |
| failed-action ratio >=20% | MUST |
| recovery ratio >=8% | MUST |
| repeated wrong mapping ratio >=8% | MUST |
| no lexical grammar leakage | MUST |
| deterministic replay | MUST |

### 10.4 P3 Text Model Acceptance

| Criterion | Required |
|---|---|
| verifier-only beaten on recovery delay | SHOULD for go |
| uncertainty-gated beaten on progress per compute | SHOULD for go |
| no-control-grammar ablation degrades persistence | MUST for core claim |
| no-falsification ablation degrades recovery/falsification | MUST for core claim |
| if fail, do not proceed to VLM main | MUST |

### 10.5 P4 GUI MVE Data Acceptance

| Criterion | Required |
|---|---|
| deterministic replay | MUST |
| DOM/screenshot/a11y alignment | MUST |
| leakage audit pass | MUST |
| coverage audit pass | MUST |
| counterfactual validity pass | MUST |
| 50k~200k valid transitions | SHOULD for MVE full |

### 10.6 P5 VLM MVE Acceptance

| Criterion | Required |
|---|---|
| frozen VLM or adapter mode used | MUST |
| no hidden label in batch input logs | MUST |
| effect prediction above trivial baseline | SHOULD |
| falsification metrics meaningful | SHOULD |
| verifier/uncertainty baselines compared | MUST |
| critical ablations run | MUST |

### 10.7 P6 Evaluation Acceptance

| Criterion | Required |
|---|---|
| compute logs present | MUST |
| same split and same base used | MUST |
| verifier-only baseline included | MUST |
| next-state-WM-only baseline included | MUST |
| uncertainty-gated baseline included | MUST |
| always-plan baseline included | MUST |
| no-control-grammar/no-falsification ablations included | MUST |
| failure interpretation table generated | MUST |

---

## 11. Prohibited Shortcuts

| Shortcut | Why Forbidden |
|---|---|
| train directly on hidden regime/control grammar as input | invalidates central claim |
| skip text-only and start with 7B VLM | wastes compute and hides mechanism failure |
| collect only successful trajectories | cannot learn falsification/recovery |
| use real website traces as main dataset | lacks hidden labels/counterfactuals |
| use success rate as only metric | mechanism claim unvalidated |
| omit verifier-only baseline | VeriGUI threat unanswered |
| omit next-state-WM-only baseline | WebWorld/CUWM/WAC threat unanswered |
| omit uncertainty-gated baseline | decision gate novelty unanswered |
| omit no-control-grammar ablation | control grammar claim unsupported |
| omit compute logging | planning claim unfair |
| invent report numbers | scientific invalidity |
| hide negative ablations | reviewer trust loss |

---

## 12. Open Requirement Questions

| Question ID | Question | Blocking? | Assigned Future Doc |
|---|---|---:|---|
| OPEN-REQ-001 | exact class/function signatures? | YES for implementation | 15_TDD |
| OPEN-REQ-002 | exact config schema? | YES for implementation | 15_TDD |
| OPEN-REQ-003 | exact browser framework? Playwright default? | YES for GUI env | 15_TDD |
| OPEN-REQ-004 | exact VLM model checkpoint? | YES for training | 15_TDD / runbook |
| OPEN-REQ-005 | exact storage format JSONL vs parquet vs webdataset? | YES for scaling | 15_TDD |
| OPEN-REQ-006 | exact threshold values for τ_f, τ_v, τ_a? | NO initial, tune later | 15_TDD / training runbook |
| OPEN-REQ-007 | exact compute budget provider/cost? | NO, rerun before launch | runbook |
| OPEN-REQ-008 | exact real auxiliary benchmark? | NO for core | experiment plan |
| OPEN-REQ-009 | whether screenshot is necessary? | NO, ablation decides | evaluation |
| OPEN-REQ-010 | whether 4-latent survives? | NO, ablation decides | evaluation |

---

## 13. Quality Gate Result

| Gate ID | Gate | PASS/FAIL/PARTIAL | Evidence | If Not PASS |
|---|---|---|---|---|
| QG-14-01 | TRD scope defined | PASS | §3 | 없음 |
| QG-14-02 | functional requirements defined | PASS | §6 | 없음 |
| QG-14-03 | non-functional requirements defined | PASS | §7 | 없음 |
| QG-14-04 | schema/data requirements included | PASS | §6.2, §8 | 없음 |
| QG-14-05 | text-only requirements included | PASS | §6.3 | 없음 |
| QG-14-06 | synthetic GUI requirements included | PASS | §6.4 | 없음 |
| QG-14-07 | model/training requirements included | PASS | §6.6, §6.7 | 없음 |
| QG-14-08 | planning requirements included | PASS | §6.8 | 없음 |
| QG-14-09 | evaluation requirements included | PASS | §6.9 | 없음 |
| QG-14-10 | reproducibility/security included | PASS | §7 | 없음 |
| QG-14-11 | traceability matrix included | PASS | §9 | 없음 |
| QG-14-12 | phase acceptance criteria included | PASS | §10 | 없음 |
| QG-14-13 | prohibited shortcuts included | PASS | §11 | 없음 |
| QG-14-14 | no implementation internals over-specified | PASS | TDD deferred | 없음 |
| QG-14-15 | no empirical results fabricated | PASS | status and wording | 없음 |

---

## 14. Final Statement

`14_TRD_TECHNICAL_REQUIREMENTS_DOCUMENT.md`는 구현 설계서가 아니다.  
이 문서는 FRCG-WM 시스템이 반드시 만족해야 하는 기술 요구사항 계약서다.

가장 중요한 요구사항은 다음이다.

```text
The system must make hidden-label leakage impossible by design.
The system must collect failure/recovery/control-grammar evidence, not only success trajectories.
The system must validate text-only mechanism before VLM scaling.
The system must compare against verifier-only, next-state-WM-only, uncertainty-gated, and always-plan baselines.
The system must support no-control-grammar and no-falsification ablations.
The system must report negative and non-effect results instead of hiding them.
```

다음 필수 파일:

```text
15_TDD_TECHNICAL_DESIGN_DOCUMENT.md
```
