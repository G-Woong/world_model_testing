---
file_id: CONTEXT-INDEX
title: FRCG-WM Paper Context Index
version: v1.0
status: context_router_not_research_content
language: ko
root_policy:
  - This file is the first file Claude Code must read before working on FRCG-WM.
  - This file routes Claude Code to the right context files.
  - This file does not replace the detailed MD files.
  - If uncertain, read the smallest relevant set first, then expand.
---

# 00_CONTEXT_INDEX.md

## 1. Purpose

이 파일은 `paper_context_ref/`의 전체 메모리 구조도다.

Claude Code는 작업을 시작할 때 이 파일을 먼저 읽고,  
요청 유형에 따라 필요한 MD만 추가로 읽어야 한다.

원칙:

```text
Do not read everything by default.
Read the router.
Read the minimum required context.
Expand only when the task requires it.
Never violate hidden-label, evaluation, baseline, or phase-gate rules.
```

---

## 2. Absolute Rules

- hidden labels are never inference inputs.
- counterfactual labels are never inference inputs.
- audit metadata is never model input.
- fake empirical results are forbidden.
- success rate alone is not sufficient evidence.
- text-only → GUI MVE → frozen VLM MVE → baselines/ablations → paper-main 순서를 건너뛰지 않는다.
- no-control-grammar, no-falsification, verifier-only, next-state-WM-only, uncertainty-gated, always-plan baseline은 절대 사라지면 안 된다.
- unresolved Unknown은 final claim으로 승격하면 안 된다.
- WebWorld/CUWM/WAC/VeriGUI threat를 무시하면 안 된다.

---

## 3. Memory Map

| File | Role | Read When |
|---|---|---|
| `00_MASTER_REFERENCE.md` | 전체 REF 원장, 핵심 claim/risk/unknown seed | 전체 방향이 헷갈리거나 REF 추적이 필요할 때 |
| `01_RELATED_WORK_THREAT_MAP.md` | WebWorld/CUWM/WAC/VeriGUI 등 direct threat map | related work, novelty, reviewer attack 검토 시 |
| `02_PROBLEM_NOVELTY_FALSIFICATION.md` | 문제정의, novelty, 반증 가능성 | “이 문제가 진짜 새로운가?” 검토 시 |
| `03_CORE_CONCEPT_TAXONOMY.md` | state/regime/control grammar/current hypothesis 등 개념 계약 | 용어·latent·schema·planning 수정 시 |
| `04_TEXT_ONLY_SMOKE_TESTBED.md` | text-only viability gate | GUI/VLM 전 작은 실험 설계·구현 시 |
| `05_SYNTHETIC_WEB_GUI_ENVIRONMENT.md` | synthetic Web/GUI 환경 설계 | browser-like env, task generator, OOD split 구현 시 |
| `06_DATA_SCHEMA_AND_LABELING.md` | schema, label, visibility, leakage 계약 | dataloader, schema, leakage audit 구현 시 |
| `07_LATENT_ARCHITECTURE_DESIGN.md` | latent/module architecture 계약 | 모델 구조, heads, module I/O 설계 시 |
| `08_LOSS_REWARD_TRAINING_OBJECTIVE.md` | loss/reward/training objective 계약 | 학습 objective, reward hacking, staged training 설계 시 |
| `09_PLANNING_THEORY_ALGORITHM.md` | falsification planning 알고리즘 | planner, gate, rollout, rewrite 구현 시 |
| `10_EVALUATION_BASELINE_ABLATION.md` | metric/baseline/ablation/failure interpretation 계약 | evaluation runner, baseline, ablation, paper evidence 설계 시 |
| `11_MODEL_DATASET_SCALE_AND_TRAINING_BUDGET.md` | 모델 크기, 데이터 규모, GPU budget | transition 수, 모델 tier, 비용, stop/go gate 결정 시 |
| `12_DATA_COLLECTION_METHODOLOGY.md` | 데이터 수집 방법론 | collector, policy mixture, counterfactual, OOD 수집 구현 시 |
| `13_CLAUDE_CODE_EXECUTION_ROADMAP.md` | Claude Code 실행 순서 | repo 구현 순서, phase gate, 작업 지시 시 |
| `14_TRD_TECHNICAL_REQUIREMENTS_DOCUMENT.md` | 기술 요구사항 | 무엇을 반드시 구현해야 하는지 확인 시 |
| `15_TDD_TECHNICAL_DESIGN_DOCUMENT.md` | 기술 설계 | class/function/config/test 구현 직전 |
| `FINAL_RESEARCH_BLUEPRINT.md` | 최종 연구 설계도 | 전체 논문 방향, final claim, method/eval 통합 확인 시 |
| `core_theory_ssot.md` | 8개 핵심 계약 압축 SSoT (concept taxonomy + loss anchor + BASE/ABL anchor + forbidden field + phase gate + term lock) | 빠른 cross-check, agent skill에서 짧은 reference. **원본이 우선; 충돌 시 03/10/FINAL 승.** |

---

## 4. Task Router

| User Task | Read First | Then Read | Do Not Assume |
|---|---|---|---|
| 전체 연구 방향 파악 | `FINAL_RESEARCH_BLUEPRINT.md` | `00_MASTER_REFERENCE.md` | blueprint가 empirical result라고 가정 금지 |
| novelty 검토 | `01_RELATED_WORK_THREAT_MAP.md` | `02`, `10`, `FINAL` | direct threat가 해결됐다고 가정 금지 |
| 문제정의 수정 | `02_PROBLEM_NOVELTY_FALSIFICATION.md` | `03`, `10` | wrong-control-grammar가 자동으로 독립 failure라고 가정 금지 |
| 개념 정의 확인 | `03_CORE_CONCEPT_TAXONOMY.md` | `02`, `06`, `07`, `09` | control grammar를 단순 precondition으로 축소 금지 |
| text-only 실험 구현 | `04_TEXT_ONLY_SMOKE_TESTBED.md` | `06`, `08`, `09`, `10`, `11`, `12` | text-only 성공을 GUI 성공으로 일반화 금지 |
| synthetic GUI 환경 구현 | `05_SYNTHETIC_WEB_GUI_ENVIRONMENT.md` | `06`, `11`, `12`, `15` | real website scraping으로 대체 금지 |
| schema/dataloader 구현 | `06_DATA_SCHEMA_AND_LABELING.md` | `12`, `14`, `15` | hidden labels를 input으로 넣지 말 것 |
| 데이터 수집 구현 | `12_DATA_COLLECTION_METHODOLOGY.md` | `05`, `06`, `11`, `15` | success trajectory만 수집 금지 |
| 모델 구조 구현 | `07_LATENT_ARCHITECTURE_DESIGN.md` | `03`, `06`, `08`, `09`, `15` | 4-latent가 최종 확정이라고 가정 금지 |
| loss/reward 구현 | `08_LOSS_REWARD_TRAINING_OBJECTIVE.md` | `06`, `07`, `09`, `15` | reward가 metric-only여도 된다고 가정 금지 |
| planning 구현 | `09_PLANNING_THEORY_ALGORITHM.md` | `07`, `08`, `10`, `15` | uncertainty-gate와 falsification-gate 동일시 금지 |
| evaluation 구현 | `10_EVALUATION_BASELINE_ABLATION.md` | `07`, `08`, `09`, `11`, `15` | success rate만 출력 금지 |
| 실험 규모 결정 | `11_MODEL_DATASET_SCALE_AND_TRAINING_BUDGET.md` | `04`, `05`, `10`, `12` | 7B부터 시작 금지 |
| Claude Code 작업 순서 | `13_CLAUDE_CODE_EXECUTION_ROADMAP.md` | `14`, `15` | phase gate skip 금지 |
| 요구사항 확인 | `14_TRD_TECHNICAL_REQUIREMENTS_DOCUMENT.md` | `13`, `15` | SHOULD와 MUST를 혼동 금지 |
| 구현 설계 확인 | `15_TDD_TECHNICAL_DESIGN_DOCUMENT.md` | `13`, `14` | TDD를 empirical result로 취급 금지 |
| 최종 논문 설계 통합 | `FINAL_RESEARCH_BLUEPRINT.md` | `00`~`15` 필요한 범위 | fake result 작성 금지 |

---

## 5. Execution Phase Router

| Phase | Goal | Must Read | Required Gate |
|---|---|---|---|
| P0 | docs/scaffold | `13`, `14`, `15` | repo scaffold and docs present |
| P1 | schema/visibility | `06`, `12`, `14`, `15` | hidden label leakage tests pass |
| P2 | text-only data | `04`, `06`, `12`, `15` | coverage and leakage audit pass |
| P3 | text-only model/eval | `07`, `08`, `09`, `10`, `11`, `15` | no-control-grammar and no-falsification ablations degrade |
| P4 | synthetic GUI MVE data | `05`, `06`, `11`, `12`, `15` | replay/leakage/coverage pass |
| P5 | frozen VLM MVE | `07`, `08`, `09`, `11`, `15` | verifier-only and uncertainty-gated compared |
| P6 | baselines/ablations | `10`, `11`, `15` | compute-matched results and failure interpretation |
| P7 | paper-main planning | `10`, `11`, `12`, `FINAL` | human review of cost, risk, and run plan |
| P8 | report generation | `10`, `FINAL`, `15` | reports generated only from real logs |

---

## 6. Critical Context Bundles

### 6.1 Data Safety Bundle

Read when touching data, schema, loaders, collector, training batch, evaluation dataset.

```text
06_DATA_SCHEMA_AND_LABELING.md
12_DATA_COLLECTION_METHODOLOGY.md
14_TRD_TECHNICAL_REQUIREMENTS_DOCUMENT.md
15_TDD_TECHNICAL_DESIGN_DOCUMENT.md
```

Hard rule:

```text
If hidden label leakage is possible, stop.
```

### 6.2 Mechanism Bundle

Read when touching model, loss, planning, or claim mechanism.

```text
02_PROBLEM_NOVELTY_FALSIFICATION.md
03_CORE_CONCEPT_TAXONOMY.md
07_LATENT_ARCHITECTURE_DESIGN.md
08_LOSS_REWARD_TRAINING_OBJECTIVE.md
09_PLANNING_THEORY_ALGORITHM.md
```

Hard rule:

```text
Do not collapse falsification-guided planning into generic uncertainty planning.
```

### 6.3 Experiment Bundle

Read when touching baselines, ablations, metrics, or reports.

```text
10_EVALUATION_BASELINE_ABLATION.md
11_MODEL_DATASET_SCALE_AND_TRAINING_BUDGET.md
13_CLAUDE_CODE_EXECUTION_ROADMAP.md
15_TDD_TECHNICAL_DESIGN_DOCUMENT.md
```

Hard rule:

```text
No compute-matched evaluation, no planning claim.
```

### 6.4 Paper Framing Bundle

Read when touching abstract, intro, related work, claims, limitations.

```text
00_MASTER_REFERENCE.md
01_RELATED_WORK_THREAT_MAP.md
02_PROBLEM_NOVELTY_FALSIFICATION.md
10_EVALUATION_BASELINE_ABLATION.md
FINAL_RESEARCH_BLUEPRINT.md
```

Hard rule:

```text
Do not claim generic Web/GUI world-model novelty.
```

### 6.5 SSoT Quick-Check Bundle

Read when needing a fast cross-reference of core theory terms, loss IDs, baseline/ablation IDs, forbidden fields, or phase gate status without loading full source MDs.

```text
core_theory_ssot.md
00_CONTEXT_INDEX.md
```

Hard rule:

```text
This bundle gives compressed views only.
If any item here conflicts with 03/10/FINAL, the source file wins.
Never treat core_theory_ssot.md as a replacement for source MDs.
```

---

## 7. Must-Preserve Terms

Use these terms consistently.

| Term | Meaning |
|---|---|
| `control grammar` | intent-to-action mapping + precondition + expected effect schema |
| `regime` | interaction mode / environment mode |
| `current hypothesis` | hypothesis actually used to choose/execute action |
| `alternative hypothesis` | alternative regime/control-grammar belief, not merely alternative action |
| `falsification evidence` | action-effect evidence that current hypothesis fails to explain |
| `decision-relevant compute` | planning only when action/value changes justify compute cost |
| `action-interface rewrite` | rewrite base intent/action into executable action/macro under selected grammar |
| `wrong-control-grammar persistence` | time current wrong grammar remains after falsifying evidence |

---

## 8. Must-Not-Disappear Baselines and Ablations

Baselines:

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

Ablations:

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

If any critical baseline or ablation is missing, do not make the corresponding paper claim.

---

## 9. Stop Conditions

Stop and report blocker if:

- hidden labels appear in inference input,
- counterfactual labels appear in inference input,
- leakage audit fails,
- coverage audit fails,
- replay validation fails,
- required baseline is missing,
- compute logging is missing,
- no-control-grammar ablation has no effect,
- no-falsification ablation has no effect,
- verifier-only matches the proposed method on recovery,
- uncertainty-gated matches progress per compute,
- report generation requires manual/fake numbers.

---

## 10. Response Policy for Claude Code

When answering or implementing:

1. State which MD files were read.
2. State which phase the task belongs to.
3. State the intended output files.
4. State blockers before implementation.
5. Prefer smallest valid implementation.
6. Add or update tests with every module.
7. Never silently change scientific definitions.
8. Never silently remove baselines/ablations.
9. Never invent empirical results.
10. If uncertain, write `UNKNOWN` and route to the correct MD.

---

## 11. Final Reminder

This index is a router.

It is not the full research design.
It is not the implementation spec.
It is not empirical evidence.

The correct flow is:

```text
CLAUDE.md
→ paper_context_ref/00_CONTEXT_INDEX.md
→ task-specific MD bundle
→ implementation or research action
→ tests/gates
→ report only from real artifacts
```
