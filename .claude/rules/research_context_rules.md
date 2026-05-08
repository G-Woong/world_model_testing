# research_context_rules.md

## Purpose

이 rule은 FRCG-WM 논문/구현 작업에서 Claude Code가 반드시 지켜야 하는 연구 context 규칙이다.

이 파일은 상세 지식 파일이 아니다.  
상세 context는 `paper_context_ref/00_CONTEXT_INDEX.md`에서 routing한다.

---

## Always Read First

FRCG-WM 관련 작업을 시작하면 반드시 먼저 읽는다.

```text
paper_context_ref/00_CONTEXT_INDEX.md
```

그 다음 작업 유형에 맞는 MD만 추가로 읽는다.

---

## Core Research Identity

이 프로젝트는 generic Web/GUI world model이 아니다.

핵심은 다음이다.

```text
wrong-control-grammar hypothesis persistence
→ action-effect evidence
→ current hypothesis falsification
→ alternative control-grammar hypothesis
→ short rollout
→ decision-relevant compute gate
→ action-interface rewrite
```

---

## Non-Negotiable Scientific Rules

- 실험 결과를 만들지 마라.
- empirical evidence 없이 acceptance-level claim을 쓰지 마라.
- success rate 하나로 claim을 검증하지 마라.
- unresolved Unknown을 final claim으로 승격하지 마라.
- negative result 또는 non-effect ablation을 숨기지 마라.
- WebWorld, CUWM, WAC, VeriGUI threat를 무시하지 마라.
- generic GUI world model novelty로 논문을 흐리지 마라.

---

## Non-Negotiable Data Rules

다음 필드는 inference input에 절대 들어가면 안 된다.

```text
true_regime
true_control_grammar
true_change_point
true_reveal_vs_shift
true_wrong_hypothesis
counterfactual_action_effects
oracle_regime_action
oracle_grammar_action
oracle_best_action
split_id
ood_type
template_id
seed
policy_id
audit_metadata
```

위 필드가 agent observation, dataloader input, model input, prompt input에 들어가면 즉시 중단한다.

---

## Required Execution Order

아래 순서를 건너뛰지 마라.

```text
1. docs/scaffold
2. schema and visibility tests
3. text-only data
4. text-only model and ablations
5. synthetic GUI MVE data
6. frozen VLM MVE
7. compute-matched baselines and ablations
8. paper-main planning only after gates pass
```

절대 7B/72B VLM 학습부터 시작하지 마라.

---

## Required Context Bundles

### Data / Schema / Leakage

```text
paper_context_ref/06_DATA_SCHEMA_AND_LABELING.md
paper_context_ref/12_DATA_COLLECTION_METHODOLOGY.md
paper_context_ref/14_TRD_TECHNICAL_REQUIREMENTS_DOCUMENT.md
paper_context_ref/15_TDD_TECHNICAL_DESIGN_DOCUMENT.md
```

### Model / Loss / Planning

```text
paper_context_ref/03_CORE_CONCEPT_TAXONOMY.md
paper_context_ref/07_LATENT_ARCHITECTURE_DESIGN.md
paper_context_ref/08_LOSS_REWARD_TRAINING_OBJECTIVE.md
paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md
```

### Evaluation / Baseline / Ablation

```text
paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md
paper_context_ref/11_MODEL_DATASET_SCALE_AND_TRAINING_BUDGET.md
paper_context_ref/13_CLAUDE_CODE_EXECUTION_ROADMAP.md
```

### Paper Framing / Novelty

```text
paper_context_ref/00_MASTER_REFERENCE.md
paper_context_ref/01_RELATED_WORK_THREAT_MAP.md
paper_context_ref/02_PROBLEM_NOVELTY_FALSIFICATION.md
paper_context_ref/FINAL_RESEARCH_BLUEPRINT.md
```

---

## Terms Must Be Preserved

| Term | Meaning |
|---|---|
| control grammar | intent-to-action mapping + precondition + expected effect schema |
| regime | interaction mode / environment mode |
| current hypothesis | hypothesis actually used to choose/execute action |
| alternative hypothesis | alternative regime/control-grammar belief, not merely alternative action |
| falsification evidence | action-effect evidence that current hypothesis fails to explain |
| decision-relevant compute | planning only when action/value changes justify compute cost |
| action-interface rewrite | rewrite base intent/action into executable action/macro under selected grammar |
| wrong-control-grammar persistence | time current wrong grammar remains after falsifying evidence |

용어를 임의로 바꾸지 마라.

---

## Baselines That Must Not Disappear

- Frozen Base VLM/LLM
- verifier-only
- next-state-WM-only
- uncertainty-gated planner
- always-plan world model
- random alternative planner
- compute-matched random reallocation
- oracle regime
- oracle control grammar
- oracle alternative hypothesis

---

## Ablations That Must Not Disappear

- no-control-grammar
- merged regime-control grammar
- collapsed latent
- no-falsification
- uncertainty instead of falsification
- no-alternative-hypothesis
- random alternative
- no-rollout
- no-rewrite
- no-progress/reward
- no-compute-gate

대응 claim을 쓰려면 관련 baseline/ablation이 반드시 있어야 한다.

---

## Implementation Rules

- 가장 작은 유효 구현부터 만든다.
- 각 major module docstring에 근거 MD를 적는다.
- 모든 script는 config, seed, manifest, status, log를 남긴다.
- 모든 dataloader/collator/model input은 forbidden field audit를 통과해야 한다.
- 모든 training/eval run은 run manifest를 남긴다.
- 모든 report는 실제 metric artifact에서만 숫자를 읽는다.
- fake number, placeholder metric, manually typed result를 report에 넣지 마라.

---

## Stop Conditions

다음 상황에서는 구현을 계속하지 말고 blocker를 보고한다.

- hidden label leakage detected
- counterfactual leakage detected
- leakage audit failed
- coverage audit failed
- replay validation failed
- required baseline missing
- compute log missing
- no-control-grammar ablation has no effect
- no-falsification ablation has no effect
- verifier-only matches proposed recovery behavior
- uncertainty-gated matches progress per compute
- report requires fake/manual numbers

---

## Response Format

작업 응답은 짧게 다음을 포함한다.

```text
Read:
- ...

Phase:
- ...

Changed/Created:
- ...

Tests/Gates:
- ...

Blockers:
- ...
```

Blocker가 없으면 `Blockers: none`이라고 쓴다.

---

## Final Rule

Claude Code의 목표는 똑똑해 보이는 답변이 아니다.

목표는 다음이다.

```text
read correct context
preserve scientific contract
implement smallest valid step
test before scaling
report blockers honestly
```
