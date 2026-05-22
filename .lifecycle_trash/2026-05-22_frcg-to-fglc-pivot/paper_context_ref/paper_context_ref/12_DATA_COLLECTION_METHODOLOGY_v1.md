---
file_id: STEP-12
title: Data Collection Methodology for FRCG-WM
version: v1.0
status: data_collection_contract_not_final_dataset
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
  - FINAL_RESEARCH_BLUEPRINT.md
purpose:
  - FRCG-WM 논문 설계에 맞는 데이터 수집 방법론을 정의한다.
  - text-only, synthetic Web/GUI, multimodal VLM-MVE, paper-main synthetic, optional real auxiliary trace 수집을 단계별로 분리한다.
  - agent observation, hidden label, training supervision, evaluation-only label, counterfactual-only label, audit metadata를 수집 시점부터 분리한다.
  - failure/recovery/reveal/shift/control-grammar coverage를 보장하는 수집 정책과 rejection policy를 정의한다.
  - Claude Code가 데이터 수집 코드를 구현할 때 따라야 할 collector, generator, logger, validator, exporter 계약을 제공한다.
forbidden:
  - Do not collect data without visibility-bucket separation.
  - Do not expose hidden regime/control-grammar/change-point/counterfactual labels to agent observations.
  - Do not use real websites as the main causal dataset.
  - Do not scrape user/private data.
  - Do not treat raw success-rate rollouts as sufficient training data.
  - Do not scale data collection before leakage audit passes.
  - Do not mix train/valid/test/OOD split generation without split seed isolation.
  - Do not claim real-world generalization from synthetic-only data.
next_files:
  - 13_CLAUDE_CODE_EXECUTION_ROADMAP.md
  - 14_TRD_TECHNICAL_REQUIREMENTS_DOCUMENT.md
  - 15_TDD_TECHNICAL_DESIGN_DOCUMENT.md
---

# 12_DATA_COLLECTION_METHODOLOGY.md

## 1. File Purpose

이 파일은 최종 데이터셋 설명 문서가 아니다.  
이 파일은 FRCG-WM 논문 설계에 맞는 **데이터 수집 방법론 계약서**다.

기존 파일들은 다음을 정의했다.

- `04_TEXT_ONLY_SMOKE_TESTBED.md`: text-only viability gate
- `05_SYNTHETIC_WEB_GUI_ENVIRONMENT.md`: synthetic Web/GUI controlled environment
- `06_DATA_SCHEMA_AND_LABELING.md`: visibility contract와 schema
- `10_EVALUATION_BASELINE_ABLATION.md`: metric/baseline/ablation/evaluation contract
- `11_MODEL_DATASET_SCALE_AND_TRAINING_BUDGET.md`: 모델·데이터 규모·GPU budget

그러나 아직 부족한 것은 다음이다.

1. 실제로 데이터를 어떤 순서로 수집할 것인가?
2. 어떤 agent policy로 rollout을 생성할 것인가?
3. failure/recovery/reveal/shift 샘플을 어떻게 충분히 확보할 것인가?
4. hidden label과 agent observation을 수집 시점부터 어떻게 분리할 것인가?
5. counterfactual action-effect table은 언제, 어떻게 생성할 것인가?
6. split leakage를 어떻게 막을 것인가?
7. 어떤 데이터는 reject하고 어떤 데이터는 keep할 것인가?
8. Claude Code가 구현할 collector/generator/logger/exporter 구조는 무엇인가?

이 문서의 핵심은 다음이다.

```text
FRCG-WM의 데이터 수집은 단순 웹 자동화 로그 수집이 아니다.

목표는:
current observation + action + observed effect + hidden regime/control grammar + counterfactual alternatives + progress/recovery/failure labels
를 leakage 없이 수집하는 것이다.
```

---

## 2. Claude Code Context Routing

| User Intent / Task | Must Read First | Then Read | Do Not Assume |
|---|---|---|---|
| 데이터 수집 코드 작성 | `12_DATA_COLLECTION_METHODOLOGY.md` | `05`, `06`, `11` | 수집 로그가 곧 학습 데이터라고 가정 금지 |
| text-only 데이터 생성 | `04_TEXT_ONLY_SMOKE_TESTBED.md` | `12` §8, §13 | text-only 성공을 GUI 성공으로 일반화 금지 |
| synthetic Web/GUI generator 구현 | `05_SYNTHETIC_WEB_GUI_ENVIRONMENT.md` | `12` §9~12 | real website scraping으로 대체 금지 |
| schema/exporter 구현 | `06_DATA_SCHEMA_AND_LABELING.md` | `12` §14~15 | hidden labels를 episode JSON public field에 섞지 말 것 |
| 데이터 규모 결정 | `11_MODEL_DATASET_SCALE_AND_TRAINING_BUDGET.md` | `12` §16~18 | success transition만 많이 만들면 충분하다고 가정 금지 |
| leakage audit 작성 | `06_DATA_SCHEMA_AND_LABELING.md` | `12` §19 | audit metadata를 agent input에 포함 금지 |
| counterfactual 수집 | `12` §11 | `05`, `06`, `09` | counterfactual table을 inference input으로 사용 금지 |
| OOD split 생성 | `05`, `10`, `11` | `12` §17 | split_id나 template_id가 model input에 새면 안 됨 |
| real benchmark auxiliary trace | `12` §23 | `10` | hidden grammar metric을 real benchmark에서 동일하게 측정 가능하다고 가정 금지 |

---

## 3. Core Data Collection Thesis

FRCG-WM 데이터셋은 다음 6개 특성을 가져야 한다.

| Thesis ID | Data Collection Thesis | Why It Matters | If Violated |
|---|---|---|---|
| DATA-COLLECT-THESIS-01 | 데이터는 success trajectory가 아니라 failure→evidence→hypothesis update→recovery trajectory를 포함해야 한다. | wrong-control-grammar persistence 학습/평가에 필요 | 모델이 일반 success predictor로 축소됨 |
| DATA-COLLECT-THESIS-02 | hidden regime/control-grammar labels는 수집하되 agent observation에서 제외해야 한다. | supervised/evaluation은 가능하되 inference leakage 방지 | 실험 전체 무효 |
| DATA-COLLECT-THESIS-03 | counterfactual action-effect는 synthetic 환경에서만 생성하고 counterfactual-only bucket에 둔다. | alternative rollout fidelity 평가 | oracle leakage |
| DATA-COLLECT-THESIS-04 | same layout/different grammar와 different layout/same grammar pair를 모두 수집해야 한다. | visual shortcut과 grammar shortcut 분리 | control grammar claim 약화 |
| DATA-COLLECT-THESIS-05 | delayed/noisy/no-op-but-valid transition을 반드시 포함해야 한다. | no-effect를 wrong grammar로 오판하는 것 방지 | falsification false positive 증가 |
| DATA-COLLECT-THESIS-06 | 수집 단계부터 split seed와 template/regime/grammar distribution을 분리해야 한다. | OOD split integrity | generalization claim 무효 |

---

## 4. Data Source Taxonomy

| Source ID | Source | Role | Allowed For Main Evidence? | Hidden Labels Available? | Counterfactual Available? | Risk |
|---|---|---|---|---|---|---|
| SRC-DATA-001 | text-only symbolic generator | mechanism viability | NO, smoke only | YES | YES, symbolic | lexical shortcut |
| SRC-DATA-002 | synthetic Web/GUI controlled generator | main causal dataset | YES | YES | YES | toy/leakage risk |
| SRC-DATA-003 | generated browser traces from base agent rollouts | behavior distribution | YES, if schema-safe | YES from env | YES if synthetic | base policy bias |
| SRC-DATA-004 | scripted oracle/expert rollouts | recovery/oracle upper bound | training/eval support only | YES | YES | oracle overfit |
| SRC-DATA-005 | adversarial failure rollouts | failure/recovery coverage | YES | YES | YES | distribution artificiality |
| SRC-DATA-006 | random/exploratory rollouts | negative samples/diversity | support only | YES | YES | low-quality noise |
| SRC-DATA-007 | optional real benchmark traces | external auxiliary | AUXILIARY ONLY | NO or weak proxy | NO | cannot support core hidden-label metrics |
| SRC-DATA-008 | human annotations | optional validation | limited | partial | NO | cost/inconsistency |
| SRC-DATA-009 | LLM-generated task specs | generator seed only | not direct evidence | generated only | generated only | hallucinated task logic |
| SRC-DATA-010 | production/private websites | NOT allowed for main collection | NO | NO | NO | privacy/legal/reproducibility risk |

---

## 5. Data Collection Phase Overview

| Phase ID | Phase | Output | Primary Consumer | Pass Gate |
|---|---|---|---|---|
| DC-P0 | schema dry-run | tiny JSONL with visibility buckets | schema validator | no hidden label in agent obs |
| DC-P1 | text-only synthetic collection | symbolic trajectories | text-only smoke model | mechanism metrics computable |
| DC-P2 | synthetic Web/GUI generator dry-run | browser traces + screenshots + DOM/a11y/logs | environment validator | deterministic replay |
| DC-P3 | MVE multimodal collection | 50k~200k transitions | frozen 3B VLM MVE | coverage and leakage audit pass |
| DC-P4 | paper-main synthetic collection | 300k~1M transitions | main 7B frozen/QLoRA experiment | split integrity pass |
| DC-P5 | ablation/eval collection | matched eval episodes/OOD splits | evaluation suite | compute-matched logs complete |
| DC-P6 | optional real auxiliary trace | real benchmark traces/proxies | external validity appendix | no overclaim |

---

## 6. Required Data Unit Definitions

### 6.1 Episode

An episode is one task attempt from initial UI state to success/failure/timeout.

Required episode-level fields:

| Field | Bucket | Required | Meaning |
|---|---|---:|---|
| episode_id | AUDIT_METADATA | YES | unique episode ID |
| dataset_version | AUDIT_METADATA | YES | dataset version |
| split_id | AUDIT_METADATA | YES | train/valid/test/OOD split |
| task_family | AUDIT_METADATA / EVAL_ONLY | YES | task family; not agent input |
| template_id | AUDIT_METADATA | YES | UI template; not agent input |
| seed | AUDIT_METADATA | YES | generation seed |
| max_steps | AUDIT_METADATA | YES | episode limit |
| public_instruction | AGENT_OBSERVATION | YES | user/task instruction |
| success | EVALUATION_ONLY | YES | final task success |
| total_progress | EVALUATION_ONLY | YES | cumulative progress |
| failure_summary | EVALUATION_ONLY | OPTIONAL | failure reason summary |

### 6.2 Step

A step is one action decision and its observed effect.

Required step-level fields:

| Field | Bucket | Required | Meaning |
|---|---|---:|---|
| step_index | AUDIT_METADATA | YES | step number |
| public_observation | AGENT_OBSERVATION | YES | sanitized DOM/screenshot/a11y/history |
| action_text | AGENT_OBSERVATION | YES | action description or primitive |
| action_type | AGENT_OBSERVATION | YES | click/type/scroll/wait/etc |
| target_ref_public | AGENT_OBSERVATION | YES | sanitized target ref |
| observed_effect_public | AGENT_OBSERVATION | YES | public effect summary |
| true_regime | TRAINING_SUPERVISION / EVALUATION_ONLY | YES | hidden regime |
| true_control_grammar | TRAINING_SUPERVISION / EVALUATION_ONLY | YES | hidden grammar |
| true_change_point | TRAINING_SUPERVISION / EVALUATION_ONLY | YES | change event |
| true_reveal_vs_shift | TRAINING_SUPERVISION / EVALUATION_ONLY | YES | reveal/shift/none |
| true_action_effect_type | TRAINING_SUPERVISION | YES | effect class |
| true_failed_action | TRAINING_SUPERVISION / EVALUATION_ONLY | YES | failure label |
| failure_reason | TRAINING_SUPERVISION / EVALUATION_ONLY | OPTIONAL | blocker/precondition/stale/etc |
| progress_delta | TRAINING_SUPERVISION / EVALUATION_ONLY | YES | progress change |
| reward_components | TRAINING_SUPERVISION / EVALUATION_ONLY | YES | progress/failure/recovery/compute components |
| counterfactual_action_effects | COUNTERFACTUAL_ONLY | OPTIONAL | alt action effect table |
| leakage_check_flags | AUDIT_METADATA | YES | validator flags |

---

## 7. Collection Policy by Visibility Bucket

| Bucket | Collection Time | Stored? | Used For Training? | Used For Inference? | Notes |
|---|---|---:|---:|---:|---|
| AGENT_OBSERVATION | before action | YES | YES as input | YES | must be sanitized |
| TRAINING_SUPERVISION | from env oracle after step | YES | YES as target | NO | never prompt/input |
| EVALUATION_ONLY | after episode/step | YES | NO unless explicitly allowed | NO | metrics only |
| COUNTERFACTUAL_ONLY | after actual transition | YES | optional target/eval | NO | oracle leakage risk |
| AUDIT_METADATA | generation/export time | YES | NO | NO | seed/template/split/hash |

Hard rule:

```text
If any field in TRAINING_SUPERVISION, EVALUATION_ONLY, COUNTERFACTUAL_ONLY, or AUDIT_METADATA is present in agent observation input, discard the dataset shard.
```

---

## 8. Text-Only Data Collection Methodology

Text-only data collection is the first mechanism test.  
It does not attempt to validate real GUI perception.

### 8.1 Text State Template

Each text-only state must include:

```json
{
  "public_state_text": "User sees a search page with a disabled Search button and a required category dropdown.",
  "public_instruction": "Search for wireless mouse.",
  "available_public_actions": [
    "type query",
    "click search",
    "select category",
    "wait"
  ],
  "hidden_state": {
    "regime": "form_guarded",
    "control_grammar": "select_required_category_then_search",
    "required_precondition": "category_selected"
  }
}
```

Only `public_state_text`, `public_instruction`, and `available_public_actions` can be used as agent input.

### 8.2 Text Collection Task Families

| Task Family | Example Wrong Grammar | Correct Grammar | Required Failure Pattern |
|---|---|---|---|
| search | click search immediately | type query + select category + click | disabled/no-op |
| pagination | click next button | scroll container until next appears | wrong target/no effect |
| modal | click background target | close/confirm modal first | blocked |
| form | submit incomplete form | fill required fields then submit | validation error |
| filter | type query only | open filter then select | irrelevant results |
| permission | click action | accept permission then action | permission blocked |
| loading | repeat click | wait then click | stale/no-op |
| nested scroll | page scroll | container scroll | no visible progress |

### 8.3 Text Collection Ratios

| Type | Ratio |
|---|---:|
| normal progress | 30~40% |
| wrong grammar failure | 25~35% |
| repeated wrong mapping | 10~20% |
| recovery action | 10~20% |
| reveal event | 8~15% |
| shift event | 10~20% |
| delayed/no-op valid wait | 3~8% |

### 8.4 Text Collection Rejection Rules

Reject if:

- hidden grammar is mentioned in public text.
- task family uniquely identifies grammar.
- every failure can be solved by retry.
- no alternative action exists.
- progress label is trivial from wording.
- no-control-grammar ablation cannot be constructed.

---

## 9. Synthetic Web/GUI Data Collection Methodology

Synthetic Web/GUI collection is the main causal data source.

### 9.1 Required Instrumentation

| Instrument | Required Output | Purpose |
|---|---|---|
| Browser automation runner | action execution trace | step replay |
| DOM snapshotter | pre/post DOM tree | state/effect logging |
| Accessibility snapshotter | pre/post a11y tree | realistic agent observation |
| Screenshot renderer | pre/post screenshot | multimodal VLM input |
| Element mapper | element id, bbox, role, visibility | action target grounding |
| Hidden environment oracle | true regime/grammar/state/event | supervision/evaluation |
| Action-effect differ | DOM/a11y/screenshot/progress diff | falsification evidence |
| Counterfactual simulator | alt action effect table | rollout fidelity |
| Split manager | train/valid/test/OOD IDs | leakage control |
| Shard exporter | JSONL/parquet/webdataset | training pipeline |

### 9.2 Synthetic Web/GUI Collection Loop

```python
def collect_episode(env, policy, counterfactual_policy, logger):
    env.reset(seed=env.seed)
    episode = logger.start_episode(env.metadata())

    for t in range(env.max_steps):
        raw_state = env.get_raw_state()
        public_obs = env.build_public_observation(raw_state)
        assert_no_hidden_labels(public_obs)

        action = policy.act(public_obs)
        pre_state = env.snapshot()

        actual_result = env.step(action)
        post_state = env.snapshot()

        hidden_labels = env.get_hidden_labels()
        action_effect = env.compute_action_effect(pre_state, post_state, action)
        progress = env.compute_progress(pre_state, post_state)

        counterfactuals = counterfactual_policy.generate(
            env=env,
            pre_state=pre_state,
            candidate_actions=env.get_candidate_actions(public_only=True),
            exclude_actual_action=False
        )

        step_record = logger.make_step_record(
            public_obs=public_obs,
            action=action,
            pre_state=pre_state,
            post_state=post_state,
            hidden_labels=hidden_labels,
            action_effect=action_effect,
            progress=progress,
            counterfactuals=counterfactuals,
            audit=env.audit_flags()
        )

        assert_visibility_contract(step_record)
        episode.add(step_record)

        if actual_result.done:
            break

    return logger.finalize_episode(episode)
```

### 9.3 Policy Mix for Collection

Single-policy data is biased.  
Use a mixture of policies.

| Policy ID | Policy | Ratio | Purpose | Risk |
|---|---|---:|---|---|
| POL-001 | oracle/expert | 15~25% | successful progress/recovery examples | too clean |
| POL-002 | base agent / heuristic | 25~35% | realistic errors | base-specific bias |
| POL-003 | wrong-grammar scripted | 15~25% | persistence/falsification positives | artificial |
| POL-004 | random constrained | 5~10% | negative samples | low quality |
| POL-005 | recovery policy | 10~20% | failure→recovery transitions | oracle overfit |
| POL-006 | adversarial timing/noise policy | 5~10% | delayed/noisy effect | distribution shift |

Policy mixture must be logged in `AUDIT_METADATA`, not agent observation.

---

## 10. Failure and Recovery Data Collection

FRCG-WM needs explicit failure and recovery trajectories.

### 10.1 Failure Types

| Failure Type | Definition | Required Label | Example |
|---|---|---|---|
| wrong_control_grammar | intent correct, mapping wrong | true_wrong_hypothesis | click disabled submit before required field |
| precondition_missing | action requires unmet condition | true_action_precondition_satisfied=False | submit without category |
| blocker_modal | modal blocks target | failure_reason=modal_blocker | click background while modal open |
| stale_dom | DOM changed after observation | failure_reason=stale_state | click element that disappeared |
| wrong_scroll_context | page vs container scroll mismatch | failure_reason=scroll_context | page scroll but list inside container |
| delayed_effect | effect occurs after wait | delayed_effect_flag=True | click triggers loading then result |
| no_op_valid | wait/no-op is valid | no_op_valid=True | wait for async enable |
| visual_target_error | target visually confused | failure_reason=grounding_error | wrong icon button |
| permission_block | permission gate blocks progress | failure_reason=permission | must accept permission first |
| invalid_rewrite | rewrite worsens base action | invalid_switch=True | unnecessary macro |

### 10.2 Recovery Types

| Recovery Type | Definition | Required Label |
|---|---|---|
| grammar_switch_recovery | switch grammar then progress | true_valid_hypothesis_switch |
| precondition_recovery | satisfy precondition then action | true_recovery_action |
| blocker_recovery | close/confirm blocker then proceed | recovery_action_type=blocker |
| wait_recovery | wait then retry after delayed effect | recovery_action_type=wait |
| scroll_context_recovery | change scroll target | recovery_action_type=scroll_context |
| alternative_action_recovery | choose different action under alt grammar | counterfactual_best_alternative |
| fallback_no_rewrite | base action kept because rewrite unnecessary | rewrite_fallback=True |

### 10.3 Required Trajectory Patterns

| Pattern ID | Pattern | Why Required |
|---|---|---|
| PAT-001 | success without failure | normal baseline |
| PAT-002 | single failure then recovery | basic recovery learning |
| PAT-003 | repeated wrong mapping then recovery | persistence metric |
| PAT-004 | wrong failure interpretation then invalid switch | switch penalty |
| PAT-005 | reveal mistaken as shift | reveal/shift guardrail |
| PAT-006 | shift mistaken as reveal | delayed recovery |
| PAT-007 | no-op valid wait mistaken as failure | false falsification |
| PAT-008 | base action correct but rewrite harmful | rewrite safety |
| PAT-009 | alternative hypothesis correct but rollout wrong | rollout fidelity |
| PAT-010 | top-k misses correct alternative | proposal recall |

---

## 11. Counterfactual Collection Methodology

Counterfactual labels are central but dangerous.  
They must never be included in agent input.

### 11.1 When to Generate Counterfactuals

Generate counterfactuals for:

- all failed-action steps,
- all change-point steps,
- all reveal/shift event steps,
- all recovery candidate steps,
- sampled normal progress steps,
- OOD-control grammar shift steps,
- steps where base action and oracle action differ.

### 11.2 Counterfactual Scope

| Scope | Description | Default |
|---|---|---|
| all actions | simulate all valid public candidate actions | use only in small MVE |
| top-k candidate actions | simulate top-k public candidates | default main |
| oracle candidates | include oracle best action for upper-bound | eval-only |
| grammar alternatives | simulate same intent under alt grammar | required |
| random negatives | random plausible actions | support contrastive learning |

### 11.3 Counterfactual Record

```json
{
  "counterfactual_id": "cf_ep001_step005_a03",
  "source_step_id": "ep001_step005",
  "candidate_action_public": "select category",
  "hypothesis_id": "grammar_form_guarded",
  "predicted_oracle_effect": "button_enabled",
  "counterfactual_progress_delta": 0.25,
  "counterfactual_failure_risk": 0.05,
  "is_oracle_best": true,
  "visibility_bucket": "COUNTERFACTUAL_ONLY"
}
```

### 11.4 Counterfactual Rejection Rules

Reject counterfactual record if:

- candidate action is not publicly available.
- it references true grammar in public text.
- it includes oracle label in `AGENT_OBSERVATION`.
- effect cannot be deterministically replayed.
- progress computation differs from actual transition logic.
- counterfactual best action is outside action space.

---

## 12. OOD Split Collection Methodology

OOD split must be generated, not merely filtered after collection.

| OOD ID | Split | Held-Out Factor | Collection Rule | Leakage Guardrail |
|---|---|---|---|---|
| OOD-001 | regime recombination | unseen regime sequences | hold out combinations | do not encode regime seq in task id |
| OOD-002 | control grammar shift | grammar mapping | same layout, different mapping | hide grammar from DOM text |
| OOD-003 | visual/layout | visual template | same grammar, changed layout | no template ID in input |
| OOD-004 | DOM/text perturbation | labels/text | paraphrase/rename | semantic cue audit |
| OOD-005 | timing/asynchrony | delay/noise | delayed effects, stale DOM | delayed labels hidden |
| OOD-006 | reveal-vs-shift ambiguity | event boundary | ambiguous cases held out | event type hidden |
| OOD-007 | unseen template | template family | new UI template | template_id audit-only |
| OOD-008 | long-horizon composition | workflow length | longer sequences | no length shortcut |
| OOD-009 | blocker composition | modal+permission+form | new blocker combinations | blocker type hidden |
| OOD-010 | action primitive composition | macro action patterns | unseen primitive order | action macro labels hidden |

---

## 13. Dataset Scale and Coverage Targets

| Stage | Episodes | Transitions | Counterfactuals | Screenshots | Purpose |
|---|---:|---:|---:|---:|---|
| DC-P1 text smoke | 2k~10k | 20k~100k | symbolic all-action | 0 | idea viability |
| DC-P2 GUI dry-run | 100~500 | 1k~5k | top-k | 1k~5k pairs | collector debug |
| DC-P3 MVE | 5k~20k | 50k~200k | 100k~500k | 50k~200k pairs | 3B frozen VLM MVE |
| DC-P4 paper-main | 30k~100k | 300k~1M | 1M~5M | 300k~1M pairs | main synthetic evidence |
| DC-P5 ablation/eval | fixed eval set | 50k~200k eval transitions | full top-k eval | eval-only | compute-matched evaluation |
| DC-P6 real auxiliary | benchmark dependent | trace dependent | none | benchmark dependent | external weak proxy |

Coverage target must satisfy:

```text
normal progress: 30~40%
failed action: 25~35%
repeated wrong mapping: 10~20%
recovery action: 10~20%
reveal: 8~15%
shift: 10~20%
delayed/noisy/stale: 8~15%
blocker/modal/permission: 8~15%
no-op valid wait: 3~8%
```

---

## 14. Export Format Contract

### 14.1 Recommended Directory Layout

```text
data/
  frcgw/
    v0_1/
      manifest.json
      schema.json
      splits/
        train.jsonl
        valid.jsonl
        test_id.jsonl
        ood_control_grammar.jsonl
        ood_regime_recombination.jsonl
        ood_visual_layout.jsonl
        ood_dom_text.jsonl
        ood_timing_async.jsonl
        ood_reveal_shift.jsonl
        ood_long_horizon.jsonl
      screenshots/
        shard_000/
        shard_001/
      counterfactuals/
        cf_train.parquet
        cf_valid.parquet
        cf_eval.parquet
      audits/
        leakage_report.json
        coverage_report.json
        split_integrity_report.json
      metadata/
        generator_config.yaml
        version_hash.txt
        dataset_card.md
```

### 14.2 Manifest Fields

```json
{
  "dataset_name": "frcgw_synthetic_gui",
  "dataset_version": "v0.1",
  "schema_version": "v0.1",
  "generator_version": "v0.1",
  "created_at": "YYYY-MM-DD",
  "splits": {
    "train": "...",
    "valid": "...",
    "test_id": "...",
    "ood_control_grammar": "..."
  },
  "visibility_contract": "06_DATA_SCHEMA_AND_LABELING.md",
  "leakage_audit_passed": false,
  "coverage_audit_passed": false,
  "notes": "No empirical claims should be made from this manifest alone."
}
```

---

## 15. Leakage Audit Methodology

Leakage audit must run before training.

| Audit ID | Leakage Risk | Detection | Required Action |
|---|---|---|---|
| LA-001 | hidden regime in DOM class/name | regex and controlled probe | rename/sanitize |
| LA-002 | control grammar in public text | lexical scan | paraphrase/remove |
| LA-003 | split ID in filename/path | path parser | remap paths |
| LA-004 | template ID predicts grammar | classifier probe | rebalance templates |
| LA-005 | task family predicts grammar | mutual information/probe | decouple task/grammar |
| LA-006 | screenshot watermark/visual cue | visual probe | regenerate assets |
| LA-007 | counterfactual table in input | schema assertion | discard shard |
| LA-008 | progress label in observation | field audit | remove field |
| LA-009 | failure reason exposed too explicitly | prompt audit | public effect summary only |
| LA-010 | target ID reveals oracle action | randomize/sanitize IDs | re-export |
| LA-011 | seed ordering reveals split | shuffle/hash IDs | re-export |
| LA-012 | OOD type in metadata used by dataloader | dataloader audit | block from input |

A shard is valid only if all critical audits pass.

---

## 16. Coverage Audit Methodology

| Audit ID | Coverage Check | Required Threshold | If Failed |
|---|---|---:|---|
| CA-001 | failed-action ratio | >=20% | collect adversarial failure rollouts |
| CA-002 | recovery ratio | >=8% | collect recovery policy rollouts |
| CA-003 | shift ratio | >=8% | increase shift scheduler |
| CA-004 | reveal ratio | >=5% | increase reveal cases |
| CA-005 | delayed/noisy ratio | >=5% | increase timing perturbation |
| CA-006 | repeated wrong mapping ratio | >=8% | scripted wrong-grammar policy |
| CA-007 | OOD-control grammar size | >=10k transitions for MVE | regenerate split |
| CA-008 | template diversity | >=20 MVE / >=50 main | add templates |
| CA-009 | grammar diversity | >=15 MVE / >=20 main | add grammar variants |
| CA-010 | counterfactual coverage | >= failed+shift+recovery steps | generate CF table |

---

## 17. Data Quality Rejection Policy

Reject an episode if:

1. public observation contains hidden label.
2. no valid alternative action exists in failure state.
3. action effect cannot be replayed deterministically.
4. screenshot/DOM/a11y timestamps mismatch beyond tolerance.
5. progress label is inconsistent with state transition.
6. hidden regime/control grammar labels are missing.
7. counterfactual best action is outside candidate action space.
8. task is solved by one trivial lexical cue.
9. split/template/task IDs leak into public observation.
10. episode has only normal progress and no useful supervision for target split.
11. all failures are pure grounding errors, not grammar/precondition/effect issues.
12. same template uniquely maps to a single grammar in train and OOD.

---

## 18. Data Collection Implementation Modules

Claude Code must implement or stub the following modules.

| Module | Responsibility | Required Output |
|---|---|---|
| `TaskSpecGenerator` | generate task family/instruction/subgoals | task spec |
| `UITemplateGenerator` | render UI template variants | DOM/screenshot/a11y |
| `RegimeGrammarEngine` | assign hidden regime/control grammar | hidden labels |
| `EventScheduler` | schedule reveal/shift/delay/noise | event labels |
| `ActionSpaceBuilder` | build public candidate actions | candidate action list |
| `PolicyMixtureRunner` | choose rollout policy | behavior trace |
| `BrowserExecutor` | execute action in synthetic browser | pre/post state |
| `ActionEffectLogger` | compute actual effect | effect record |
| `CounterfactualSimulator` | simulate alt actions | counterfactual table |
| `ProgressRewardComputer` | compute progress/reward components | reward/progress labels |
| `VisibilitySanitizer` | build agent observation | public observation |
| `LeakageAuditor` | detect leaked fields/shortcuts | leakage report |
| `CoverageAuditor` | check distribution coverage | coverage report |
| `SplitManager` | assign train/valid/test/OOD | split metadata |
| `ShardExporter` | export JSONL/parquet/assets | dataset shards |
| `ReplayValidator` | replay collected traces | replay pass/fail |

---

## 19. Minimal Implementation Pseudocode

```python
def generate_dataset(config):
    split_manager = SplitManager(config.splits)
    exporter = ShardExporter(config.output_dir)
    leakage_auditor = LeakageAuditor(config.visibility_contract)
    coverage_auditor = CoverageAuditor(config.coverage_targets)

    for episode_spec in TaskSpecGenerator(config).generate():
        split_id = split_manager.assign(episode_spec)
        env = SyntheticGUIEnvironment(
            task_spec=episode_spec,
            template=UITemplateGenerator(config).sample(split_id),
            grammar_engine=RegimeGrammarEngine(config),
            event_scheduler=EventScheduler(config),
        )

        policy = PolicyMixtureRunner(config.policy_mix).sample_policy(episode_spec)
        episode = collect_episode(
            env=env,
            policy=policy,
            counterfactual_policy=CounterfactualSimulator(config),
            logger=ActionEffectLogger(config),
        )

        if not ReplayValidator(config).validate(episode):
            exporter.write_rejected(episode, reason="replay_failed")
            continue

        if not leakage_auditor.validate(episode):
            exporter.write_rejected(episode, reason="leakage_failed")
            continue

        exporter.write(split_id, episode)

    coverage_report = coverage_auditor.run(exporter.output_dir)
    leakage_report = leakage_auditor.run_full(exporter.output_dir)

    if not coverage_report.passed:
        raise RuntimeError("Coverage audit failed. Collect more targeted episodes.")
    if not leakage_report.passed:
        raise RuntimeError("Leakage audit failed. Do not train.")

    exporter.write_manifest(coverage_report, leakage_report)
```

---

## 20. Dataset Versioning Policy

| Version Change | New Version Required? | Example |
|---|---:|---|
| schema field added/removed | YES | add `h_exec_trace` |
| visibility bucket changed | YES | move field from eval to train |
| generator logic changed | YES | new grammar scheduler |
| OOD split rule changed | YES | new held-out template assignment |
| random seed only changed | YES, minor version | v0.1.1 |
| screenshot resolution changed | YES | 224→336 |
| policy mixture changed | YES | more adversarial failures |
| only comments changed | NO | documentation typo |

Version rule:

```text
Never mix data from different generator/schema versions in a single training run unless explicitly recorded.
```

---

## 21. Connection to Losses and Metrics

| Data Field / Pattern | Required For Loss | Required For Metric |
|---|---|---|
| true_control_grammar | L_control_grammar | persistence time, no-grammar ablation |
| true_regime | L_regime | regime recombination |
| true_change_point | L_change_point | change-point F1 |
| true_reveal_vs_shift | L_reveal_shift | reveal-vs-shift accuracy |
| true_action_effect_type | L_action_effect | action-effect accuracy |
| progress_delta | L_progress | normalized return, progress per compute |
| true_failed_action | L_failed_action | failed-action repetition |
| recovery_action | L_recovery_ranking / L_mapping | recovery delay |
| counterfactual_action_effects | L_counterfactual_rollout | rollout fidelity |
| planning_calls / rollout_steps | compute penalty | compute-normalized return |
| policy_id | audit only | distribution analysis |
| split_id / ood_type | eval only | OOD metrics |

---

## 22. Real Benchmark Auxiliary Collection

Real benchmark traces can support external validity but cannot replace synthetic causal data.

| Real Source | Use | Not Allowed Claim |
|---|---|---|
| WebArena | task success / weak failure trace | hidden grammar persistence proven |
| VisualWebArena | visual grounding stress | control grammar metric proven |
| OSWorld | computer-use external validation | synthetic mechanism proven |
| WorkArena | enterprise task realism | causal hidden label analysis |
| BrowserGym | unified execution harness | main claim evidence alone |

Real auxiliary collection policy:

1. collect public observations/actions/effects only.
2. do not fabricate hidden labels.
3. use weak proxy labels such as repeated action, no progress, failure recovery.
4. report as auxiliary, not core evidence.
5. never use real traces to claim counterfactual rollout fidelity unless counterfactuals are actually available.

---

## 23. Stop / Go Gates

| Gate ID | Gate | Pass Condition | If Failed |
|---|---|---|---|
| DC-GATE-001 | visibility gate | no hidden/counterfactual/audit field in agent input | discard shard |
| DC-GATE-002 | replay gate | collected transitions replay deterministically | fix executor |
| DC-GATE-003 | coverage gate | all required ratios above minimum | targeted collection |
| DC-GATE-004 | OOD integrity gate | held-out factors independent from train | regenerate split |
| DC-GATE-005 | counterfactual validity gate | CF actions valid and deterministic | restrict CF scope |
| DC-GATE-006 | text-only gate | mechanism metrics computable | revise schema |
| DC-GATE-007 | MVE collection gate | 50k~200k valid transitions | proceed to frozen VLM MVE |
| DC-GATE-008 | main collection gate | leakage+coverage+split pass | proceed to paper-main training |

---

## 24. Risk / Unknown Ledger

| Risk ID | Risk / Unknown | Why It Matters | Resolution |
|---|---|---|---|
| DATA-RISK-001 | synthetic data may be too artificial | reviewer toy attack | anti-toy templates + OOD + real auxiliary |
| DATA-RISK-002 | label leakage | invalid experiment | visibility sanitizer + audit |
| DATA-RISK-003 | grammar label too easy | classifier shortcut | decouple template/task/grammar |
| DATA-RISK-004 | failure distribution artificial | model overfits scripted mistakes | mix policies and random/adversarial rollouts |
| DATA-RISK-005 | recovery actions oracle-like | unrealistic recovery | include base/retry/self-correction rollouts |
| DATA-RISK-006 | counterfactuals leak oracle | invalid rollout training | CF-only bucket and input assertion |
| DATA-RISK-007 | delayed effect mislabeled as failure | false falsification | delayed/no-op valid labels |
| DATA-RISK-008 | OOD split not truly held out | generalization overclaim | split integrity audit |
| DATA-RISK-009 | real benchmark lacks labels | weak external evidence | auxiliary-only framing |
| DATA-RISK-010 | screenshots too expensive | storage bottleneck | compression/cache/resolution cap |
| DATA-RISK-011 | DOM/a11y/screenshot mismatch | inconsistent training | timestamp/replay validation |
| DATA-RISK-012 | base policy bias | method overfits base errors | policy mixture |
| DATA-RISK-013 | insufficient repeated failure | persistence not learnable | scripted wrong-grammar policy |
| DATA-RISK-014 | insufficient valid switches | switch reward unlearnable | recovery policy sampling |
| DATA-RISK-015 | too many trivial failures | verifier-only suffices | filter pure execution errors |

---

## 25. Quality Gate Result

| Gate ID | Gate | PASS/FAIL/PARTIAL | Evidence | If Not PASS |
|---|---|---|---|---|
| QG-12-01 | data source taxonomy defined | PASS | §4 | 없음 |
| QG-12-02 | collection phases defined | PASS | §5 | 없음 |
| QG-12-03 | episode/step data units defined | PASS | §6 | 없음 |
| QG-12-04 | visibility bucket policy defined | PASS | §7 | 없음 |
| QG-12-05 | text-only collection method defined | PASS | §8 | 없음 |
| QG-12-06 | synthetic Web/GUI loop defined | PASS | §9 | 없음 |
| QG-12-07 | failure/recovery taxonomy defined | PASS | §10 | 없음 |
| QG-12-08 | counterfactual methodology defined | PASS | §11 | 없음 |
| QG-12-09 | OOD split collection defined | PASS | §12 | 없음 |
| QG-12-10 | scale and coverage targets included | PASS | §13 | 없음 |
| QG-12-11 | export layout included | PASS | §14 | 없음 |
| QG-12-12 | leakage audit included | PASS | §15 | 없음 |
| QG-12-13 | implementation modules included | PASS | §18 | 없음 |
| QG-12-14 | pseudocode included | PASS | §19 | 없음 |
| QG-12-15 | real auxiliary policy included | PASS | §22 | 없음 |
| QG-12-16 | no empirical result fabricated | PASS | status and warnings | 없음 |

---

## 26. Final Statement

`12_DATA_COLLECTION_METHODOLOGY.md`는 dataset result 파일이 아니다.  
이 파일은 FRCG-WM 논문 설계에 맞는 데이터 수집 방법론 계약서다.

가장 중요한 원칙은 다음이다.

```text
Collect trajectories that expose:
wrong grammar,
falsifying evidence,
alternative hypothesis,
recovery action,
progress change,
and compute-relevant planning opportunities.

Do not collect only successful trajectories.
Do not leak hidden labels.
Do not use real websites as the main causal dataset.
Do not scale before leakage and coverage audits pass.
```

다음 필수 파일:

```text
13_CLAUDE_CODE_EXECUTION_ROADMAP.md
```
