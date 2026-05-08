# read-paper-context

## Purpose

FRCG-WM 작업을 시작하기 전에 필요한 paper context만 정확히 읽는다.

이 커맨드는 전체 문서를 전부 읽기 위한 것이 아니다.  
`paper_context_ref/00_CONTEXT_INDEX.md`를 먼저 읽고, 작업 유형에 맞는 최소 context bundle만 확장한다.

---

## Usage

```text
/read-paper-context <task>
```

Examples:

```text
/read-paper-context schema
/read-paper-context data-collection
/read-paper-context text-smoke
/read-paper-context gui-env
/read-paper-context model
/read-paper-context loss
/read-paper-context planning
/read-paper-context evaluation
/read-paper-context roadmap
/read-paper-context trd
/read-paper-context tdd
/read-paper-context paper-framing
/read-paper-context all-index
```

---

## Always Read First

Before doing anything, read:

```text
paper_context_ref/00_CONTEXT_INDEX.md
```

Then select the smallest matching bundle below.

---

## Task Routing

### all-index

Read:

```text
paper_context_ref/00_CONTEXT_INDEX.md
paper_context_ref/00_MASTER_REFERENCE.md
paper_context_ref/FINAL_RESEARCH_BLUEPRINT.md
```

Use when:

- 전체 연구 방향을 빠르게 파악해야 할 때
- 어떤 문서를 읽어야 할지 애매할 때

---

### related-work

Read:

```text
paper_context_ref/01_RELATED_WORK_THREAT_MAP.md
paper_context_ref/02_PROBLEM_NOVELTY_FALSIFICATION.md
paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md
paper_context_ref/FINAL_RESEARCH_BLUEPRINT.md
```

Use when:

- novelty 검토
- reviewer attack 대응
- WebWorld/CUWM/WAC/VeriGUI 비교
- related work 작성

Do not assume direct threats are solved.

---

### problem

Read:

```text
paper_context_ref/02_PROBLEM_NOVELTY_FALSIFICATION.md
paper_context_ref/03_CORE_CONCEPT_TAXONOMY.md
paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md
```

Use when:

- problem definition 수정
- wrong-control-grammar persistence 검토
- falsifiability 확인

Do not assume the problem is independent from action failure, visual grounding failure, or verifier failure.

---

### concepts

Read:

```text
paper_context_ref/03_CORE_CONCEPT_TAXONOMY.md
paper_context_ref/02_PROBLEM_NOVELTY_FALSIFICATION.md
paper_context_ref/06_DATA_SCHEMA_AND_LABELING.md
paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md
```

Use when:

- control grammar, regime, current hypothesis, alternative hypothesis 정의를 확인할 때
- 용어가 흔들릴 때

Do not rename terms silently.

---

### text-smoke

Read:

```text
paper_context_ref/04_TEXT_ONLY_SMOKE_TESTBED.md
paper_context_ref/06_DATA_SCHEMA_AND_LABELING.md
paper_context_ref/08_LOSS_REWARD_TRAINING_OBJECTIVE.md
paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md
paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md
paper_context_ref/11_MODEL_DATASET_SCALE_AND_TRAINING_BUDGET.md
paper_context_ref/12_DATA_COLLECTION_METHODOLOGY.md
```

Use when:

- text-only generator 구현
- text-only model 구현
- text-only ablation/evaluation 구현

Do not claim text-only success as Web/GUI evidence.

---

### gui-env

Read:

```text
paper_context_ref/05_SYNTHETIC_WEB_GUI_ENVIRONMENT.md
paper_context_ref/06_DATA_SCHEMA_AND_LABELING.md
paper_context_ref/11_MODEL_DATASET_SCALE_AND_TRAINING_BUDGET.md
paper_context_ref/12_DATA_COLLECTION_METHODOLOGY.md
paper_context_ref/15_TDD_TECHNICAL_DESIGN_DOCUMENT.md
```

Use when:

- synthetic GUI environment 구현
- browser executor / template generator / event scheduler 구현
- OOD split 설계

Do not replace the main dataset with real website scraping.

---

### schema

Read:

```text
paper_context_ref/06_DATA_SCHEMA_AND_LABELING.md
paper_context_ref/12_DATA_COLLECTION_METHODOLOGY.md
paper_context_ref/14_TRD_TECHNICAL_REQUIREMENTS_DOCUMENT.md
paper_context_ref/15_TDD_TECHNICAL_DESIGN_DOCUMENT.md
```

Use when:

- schema
- dataloader
- collator
- visibility buckets
- leakage auditor
- counterfactual exclusion

Hard stop if hidden labels can enter inference input.

---

### data-collection

Read:

```text
paper_context_ref/12_DATA_COLLECTION_METHODOLOGY.md
paper_context_ref/05_SYNTHETIC_WEB_GUI_ENVIRONMENT.md
paper_context_ref/06_DATA_SCHEMA_AND_LABELING.md
paper_context_ref/11_MODEL_DATASET_SCALE_AND_TRAINING_BUDGET.md
paper_context_ref/15_TDD_TECHNICAL_DESIGN_DOCUMENT.md
```

Use when:

- collector 구현
- policy mixture
- failure/recovery collection
- counterfactual generation
- OOD split collection

Do not collect only success trajectories.

---

### model

Read:

```text
paper_context_ref/07_LATENT_ARCHITECTURE_DESIGN.md
paper_context_ref/03_CORE_CONCEPT_TAXONOMY.md
paper_context_ref/06_DATA_SCHEMA_AND_LABELING.md
paper_context_ref/08_LOSS_REWARD_TRAINING_OBJECTIVE.md
paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md
paper_context_ref/11_MODEL_DATASET_SCALE_AND_TRAINING_BUDGET.md
paper_context_ref/15_TDD_TECHNICAL_DESIGN_DOCUMENT.md
```

Use when:

- latent heads
- encoders
- frozen VLM adapter
- world model heads
- model I/O contract

Do not assume the 4-latent structure is final without ablation.

---

### loss

Read:

```text
paper_context_ref/08_LOSS_REWARD_TRAINING_OBJECTIVE.md
paper_context_ref/06_DATA_SCHEMA_AND_LABELING.md
paper_context_ref/07_LATENT_ARCHITECTURE_DESIGN.md
paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md
paper_context_ref/15_TDD_TECHNICAL_DESIGN_DOCUMENT.md
```

Use when:

- losses
- rewards
- valid switch reward
- staged training
- reward hacking guardrails

Do not make reward metric-only.

---

### planning

Read:

```text
paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md
paper_context_ref/03_CORE_CONCEPT_TAXONOMY.md
paper_context_ref/07_LATENT_ARCHITECTURE_DESIGN.md
paper_context_ref/08_LOSS_REWARD_TRAINING_OBJECTIVE.md
paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md
paper_context_ref/15_TDD_TECHNICAL_DESIGN_DOCUMENT.md
```

Use when:

- falsification score
- alternative hypothesis proposer
- short rollout
- decision-relevance gate
- action-interface rewrite

Do not collapse falsification-guided planning into uncertainty-gated planning.

---

### evaluation

Read:

```text
paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md
paper_context_ref/07_LATENT_ARCHITECTURE_DESIGN.md
paper_context_ref/08_LOSS_REWARD_TRAINING_OBJECTIVE.md
paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md
paper_context_ref/11_MODEL_DATASET_SCALE_AND_TRAINING_BUDGET.md
paper_context_ref/15_TDD_TECHNICAL_DESIGN_DOCUMENT.md
```

Use when:

- metrics
- baselines
- ablations
- compute-matched evaluation
- failure interpretation
- report artifacts

Do not output success-rate-only evaluation.

---

### scale-budget

Read:

```text
paper_context_ref/11_MODEL_DATASET_SCALE_AND_TRAINING_BUDGET.md
paper_context_ref/04_TEXT_ONLY_SMOKE_TESTBED.md
paper_context_ref/05_SYNTHETIC_WEB_GUI_ENVIRONMENT.md
paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md
paper_context_ref/12_DATA_COLLECTION_METHODOLOGY.md
```

Use when:

- model size
- dataset size
- transition count
- GPU budget
- stop/go gate
- scaling decision

Do not start with 7B/72B VLM.

---

### roadmap

Read:

```text
paper_context_ref/13_CLAUDE_CODE_EXECUTION_ROADMAP.md
paper_context_ref/14_TRD_TECHNICAL_REQUIREMENTS_DOCUMENT.md
paper_context_ref/15_TDD_TECHNICAL_DESIGN_DOCUMENT.md
```

Use when:

- repo implementation order
- phase planning
- task breakdown
- gate checking

Do not skip phase gates.

---

### trd

Read:

```text
paper_context_ref/14_TRD_TECHNICAL_REQUIREMENTS_DOCUMENT.md
paper_context_ref/13_CLAUDE_CODE_EXECUTION_ROADMAP.md
paper_context_ref/15_TDD_TECHNICAL_DESIGN_DOCUMENT.md
```

Use when:

- requirements checking
- MUST/SHOULD/MUST NOT interpretation
- acceptance criteria

Do not confuse requirements with implementation internals.

---

### tdd

Read:

```text
paper_context_ref/15_TDD_TECHNICAL_DESIGN_DOCUMENT.md
paper_context_ref/14_TRD_TECHNICAL_REQUIREMENTS_DOCUMENT.md
paper_context_ref/13_CLAUDE_CODE_EXECUTION_ROADMAP.md
```

Use when:

- class/function/config/test implementation
- repo module design
- script design

Do not treat TDD as empirical evidence.

---

### paper-framing

Read:

```text
paper_context_ref/FINAL_RESEARCH_BLUEPRINT.md
paper_context_ref/00_MASTER_REFERENCE.md
paper_context_ref/01_RELATED_WORK_THREAT_MAP.md
paper_context_ref/02_PROBLEM_NOVELTY_FALSIFICATION.md
paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md
```

Use when:

- title/abstract/intro
- related work framing
- claim wording
- limitations

Do not claim generic Web/GUI world-model novelty.

---

## Required Output After Running This Command

After reading the selected bundle, respond with:

```text
Read:
- ...

Task Type:
- ...

Relevant Constraints:
- ...

Next Safe Action:
- ...

Blockers:
- ...
```

If no blocker exists:

```text
Blockers:
- none
```

---

## Stop Conditions

Stop immediately if:

- requested task would expose hidden labels to inference input,
- requested task skips schema/leakage tests,
- requested task removes required baselines/ablations,
- requested task invents empirical numbers,
- requested task starts paper-main VLM before MVE gates,
- requested task treats optional real benchmark as main causal evidence.

---

## Final Reminder

This command is a router.

It does not replace the docs.
It routes to the right docs.

Correct flow:

```text
/read-paper-context <task>
→ read 00_CONTEXT_INDEX.md
→ read selected bundle
→ implement or answer only within that contract
```
