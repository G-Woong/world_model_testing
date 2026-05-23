---
file_id: STEP-13
title: Claude Code Execution Roadmap for FRCG-WM
version: v1.0
status: execution_roadmap_not_implementation_code
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
  - FINAL_RESEARCH_BLUEPRINT.md
purpose:
  - Claude Code가 FRCG-WM 연구 repo를 구조적으로 읽고, 필요한 context만 확장적으로 참조하면서, 단계별 구현·검증·실험 준비를 수행하도록 실행 로드맵을 정의한다.
  - 연구 설계 문서 00~12를 실제 파일 생성, 모듈 구현, 테스트, 데이터 생성, 학습, 평가 실행 순서로 변환한다.
  - 각 단계마다 Claude Code가 반드시 읽어야 할 MD, 생성해야 할 파일, 금지해야 할 가정, 통과해야 할 quality gate를 고정한다.
  - 무리한 대형 VLM 학습, hidden label leakage, weak baseline 누락, compute mismatch, 구현 전 설계 비약을 방지한다.
forbidden:
  - Do not let Claude Code implement from memory without reading the required MD context.
  - Do not skip schema/leakage tests before model training.
  - Do not start with 7B VLM or paper-main training before text-only and MVE gates pass.
  - Do not expose hidden labels or counterfactual labels to inference input.
  - Do not remove verifier-only, next-state-WM-only, uncertainty-gated, always-plan, no-control-grammar ablations.
  - Do not treat generated metrics as empirical claims before evaluation scripts run.
  - Do not modify scientific definitions without updating the relevant source MD and downstream references.
next_files:
  - 14_TRD_TECHNICAL_REQUIREMENTS_DOCUMENT.md
  - 15_TDD_TECHNICAL_DESIGN_DOCUMENT.md
  - 16_REPO_SCAFFOLD_AND_TEST_PLAN.md
---

# 13_CLAUDE_CODE_EXECUTION_ROADMAP.md

## 1. File Purpose

이 파일은 코드 구현물이 아니다.  
이 파일은 Claude Code가 FRCG-WM 연구 repo를 실제로 구축할 때 따라야 하는 **실행 로드맵 계약서**다.

기존 문서들은 연구 설계를 정의했다.

- `00_MASTER_REFERENCE.md`: 전체 REF 원장과 routing
- `01_RELATED_WORK_THREAT_MAP.md`: related work threat와 novelty 방어
- `02_PROBLEM_NOVELTY_FALSIFICATION.md`: 문제정의와 반증 가능성
- `03_CORE_CONCEPT_TAXONOMY.md`: regime/control grammar/current hypothesis 등 개념 계약
- `04_TEXT_ONLY_SMOKE_TESTBED.md`: text-only viability gate
- `05_SYNTHETIC_WEB_GUI_ENVIRONMENT.md`: synthetic Web/GUI 환경 설계
- `06_DATA_SCHEMA_AND_LABELING.md`: schema, label, visibility, leakage 계약
- `07_LATENT_ARCHITECTURE_DESIGN.md`: architecture/module/latent 계약
- `08_LOSS_REWARD_TRAINING_OBJECTIVE.md`: loss/reward/training objective 계약
- `09_PLANNING_THEORY_ALGORITHM.md`: planning/theory/pseudo-code 계약
- `10_EVALUATION_BASELINE_ABLATION.md`: metric/baseline/ablation/failure interpretation 계약
- `11_MODEL_DATASET_SCALE_AND_TRAINING_BUDGET.md`: 모델·데이터 규모·GPU budget 계약
- `12_DATA_COLLECTION_METHODOLOGY.md`: 데이터 수집 방법론 계약
- `FINAL_RESEARCH_BLUEPRINT.md`: 최종 연구 설계도

그러나 Claude Code는 위 문서들을 자동으로 올바른 순서로 읽지 않는다.  
따라서 이 파일은 Claude Code에게 다음을 강제한다.

1. 어떤 작업 전에 어떤 MD를 먼저 읽어야 하는가?
2. 어떤 파일/모듈/테스트를 어떤 순서로 생성해야 하는가?
3. 어떤 단계에서 멈추고 검증해야 하는가?
4. 어떤 결과가 나오면 다음 단계로 넘어가고, 어떤 결과면 claim을 약화해야 하는가?
5. 어떤 shortcut, hidden label leakage, weak baseline, compute mismatch를 절대 허용하지 않는가?

---

## 2. Operating Principle

Claude Code의 기본 실행 원칙은 다음이다.

```text
Read narrowly, implement minimally, test aggressively, scale only after gates pass.
```

즉:

1. 모든 MD를 항상 전부 읽지 않는다.
2. 작업 목적에 따라 필요한 MD를 먼저 읽는다.
3. 구현은 항상 가장 작은 MVE부터 시작한다.
4. 테스트와 leakage audit 없이는 학습으로 넘어가지 않는다.
5. text-only가 실패하면 VLM으로 넘어가지 않는다.
6. MVE가 실패하면 paper-main으로 넘어가지 않는다.
7. metric이 안 무너지면 claim을 억지로 유지하지 않는다.

---

## 3. Global Claude Code Read Policy

| Task Type | Must Read | Optional Read | Forbidden Assumption |
|---|---|---|---|
| repo scaffold 생성 | `00`, `13`, `14`, `15` | `FINAL` | 연구 정의를 코드 안에서 임의 변경 금지 |
| text-only generator 구현 | `04`, `12`, `06` | `02`, `03`, `11` | text-only가 최종 evidence라고 가정 금지 |
| schema 구현 | `06`, `12` | `05`, `10`, `11` | hidden label을 public observation에 포함 금지 |
| leakage test 구현 | `06`, `12`, `13` | `05`, `10` | audit metadata를 model input으로 넣지 말 것 |
| synthetic GUI env 구현 | `05`, `12` | `03`, `06`, `11` | real website scraping으로 대체 금지 |
| data collector 구현 | `12`, `06`, `05` | `11` | success trajectory만 수집 금지 |
| text-only model 구현 | `04`, `07`, `08`, `09` | `10`, `11` | 4-latent를 최종 확정 금지 |
| VLM MVE 구현 | `07`, `08`, `11`, `12` | `05`, `06`, `09` | VLM full fine-tuning부터 시작 금지 |
| training loop 구현 | `08`, `11`, `13` | `07`, `06` | reward가 metric으로만 존재해도 된다고 가정 금지 |
| planning module 구현 | `09`, `07`, `08` | `03`, `10` | uncertainty gate와 falsification gate 동일시 금지 |
| evaluation runner 구현 | `10`, `11` | `02`, `07`, `08`, `09` | success rate만 출력 금지 |
| ablation runner 구현 | `10`, `07`, `08`, `09` | `11` | no-control-grammar/no-falsification 생략 금지 |
| final paper support 자료 생성 | `FINAL`, `10`, `01` | `00`~`12` | fake result 생성 금지 |

---

## 4. Required Repository Layout

Claude Code는 아래 repo 구조를 먼저 생성해야 한다.

```text
frcgw/
  README.md
  pyproject.toml
  configs/
    text_smoke.yaml
    data_collection_text.yaml
    data_collection_gui_mve.yaml
    data_collection_gui_main.yaml
    model_text.yaml
    model_vlm_mve.yaml
    train_text.yaml
    train_vlm_mve.yaml
    eval_text.yaml
    eval_gui_mve.yaml
    ablation_core.yaml
  docs/
    00_MASTER_REFERENCE.md
    01_RELATED_WORK_THREAT_MAP.md
    02_PROBLEM_NOVELTY_FALSIFICATION.md
    03_CORE_CONCEPT_TAXONOMY.md
    04_TEXT_ONLY_SMOKE_TESTBED.md
    05_SYNTHETIC_WEB_GUI_ENVIRONMENT.md
    06_DATA_SCHEMA_AND_LABELING.md
    07_LATENT_ARCHITECTURE_DESIGN.md
    08_LOSS_REWARD_TRAINING_OBJECTIVE.md
    09_PLANNING_THEORY_ALGORITHM.md
    10_EVALUATION_BASELINE_ABLATION.md
    11_MODEL_DATASET_SCALE_AND_TRAINING_BUDGET.md
    12_DATA_COLLECTION_METHODOLOGY.md
    13_CLAUDE_CODE_EXECUTION_ROADMAP.md
    FINAL_RESEARCH_BLUEPRINT.md
  src/
    frcgw/
      __init__.py
      schemas/
        visibility.py
        episode_schema.py
        step_schema.py
        validation.py
      text_env/
        generator.py
        state.py
        grammar.py
        policies.py
        collector.py
      gui_env/
        task_spec.py
        template_generator.py
        regime_grammar_engine.py
        event_scheduler.py
        browser_executor.py
        action_space.py
        collector.py
      logging/
        action_effect_logger.py
        counterfactual_logger.py
        replay_validator.py
        manifest.py
      data/
        split_manager.py
        shard_exporter.py
        leakage_auditor.py
        coverage_auditor.py
        dataset_loader.py
      models/
        encoders.py
        latent_heads.py
        world_model_heads.py
        text_frcg_model.py
        vlm_frcg_adapter.py
      objectives/
        losses.py
        rewards.py
        weighting.py
      planning/
        falsification.py
        alternative_proposer.py
        rollout.py
        decision_gate.py
        rewrite.py
        planner.py
      training/
        train_text.py
        train_vlm_mve.py
        checkpoints.py
        monitoring.py
      evaluation/
        metrics.py
        baselines.py
        ablations.py
        compute_budget.py
        eval_runner.py
      utils/
        seed.py
        hashing.py
        io.py
        config.py
  scripts/
    00_validate_docs.py
    01_generate_text_data.py
    02_train_text_smoke.py
    03_eval_text_smoke.py
    04_generate_gui_mve_data.py
    05_validate_dataset.py
    06_train_vlm_mve.py
    07_eval_vlm_mve.py
    08_run_core_ablations.py
    09_generate_reports.py
  tests/
    test_visibility_contract.py
    test_episode_schema.py
    test_text_env.py
    test_counterfactual_exclusion.py
    test_leakage_auditor.py
    test_coverage_auditor.py
    test_falsification.py
    test_decision_gate.py
    test_metrics.py
    test_eval_runner.py
  data/
    README.md
  outputs/
    README.md
```

---

## 5. Execution Phase Overview

| Phase ID | Phase | Goal | Required Docs | Output | Gate |
|---|---|---|---|---|---|
| CC-P0 | docs and scaffold | repo/document structure 생성 | `00`, `13` | repo skeleton | docs present |
| CC-P1 | schema contract implementation | visibility/schema/validation 구현 | `06`, `12` | schema validators | no hidden label leakage |
| CC-P2 | text-only data generator | symbolic trajectories 생성 | `04`, `12` | DATA-T1 | coverage pass |
| CC-P3 | text-only model + planner | mechanism viability 확인 | `04`, `07`, `08`, `09` | MODEL-T0 results | core ablations collapse |
| CC-P4 | synthetic GUI MVE collector | browser/DOM/screenshot/action-effect log 수집 | `05`, `06`, `12` | DATA-T2/T3 | replay+leakage pass |
| CC-P5 | VLM MVE model | frozen VLM + FRCG heads | `07`, `08`, `11` | MODEL-T2 results | beats verifier/uncertainty on mechanism metrics |
| CC-P6 | core baselines/ablations | claim defense | `10`, `11` | eval tables | compute-matched pass |
| CC-P7 | paper-main planning | 7B/QLoRA main 준비 | `11`, `12`, `10` | run plan, not automatic training | previous gates pass |
| CC-P8 | report generation | figures/tables/logs 생성 | `10`, `FINAL` | report artifacts | no fake result |

---

## 6. Phase CC-P0: Documentation and Scaffold

### 6.1 Claude Code Prompt

```text
Read docs/00_MASTER_REFERENCE.md and docs/13_CLAUDE_CODE_EXECUTION_ROADMAP.md.
Create the repository scaffold exactly as specified in Section 4.
Do not implement model logic yet.
Create placeholder modules with docstrings that reference the correct source MD files.
Add README with project purpose, forbidden assumptions, and phase order.
```

### 6.2 Required Files

| File | Required Content |
|---|---|
| `README.md` | project purpose, phase order, no hidden label rule |
| `pyproject.toml` | package metadata, pytest, ruff/mypy optional |
| `configs/*.yaml` | empty but schema-valid configs |
| `src/frcgw/__init__.py` | package marker |
| `tests/` | placeholder tests |

### 6.3 Gate

| Gate | Pass Condition |
|---|---|
| CC-P0-G1 | all directories exist |
| CC-P0-G2 | docs copied into `docs/` |
| CC-P0-G3 | README includes no-fake-result/no-leakage rule |
| CC-P0-G4 | pytest runs with placeholder tests |

---

## 7. Phase CC-P1: Schema and Visibility Contract

### 7.1 Required Read

- `06_DATA_SCHEMA_AND_LABELING.md`
- `12_DATA_COLLECTION_METHODOLOGY.md`
- `13_CLAUDE_CODE_EXECUTION_ROADMAP.md`

### 7.2 Required Modules

| Module | Required Classes / Functions |
|---|---|
| `schemas/visibility.py` | `VisibilityBucket`, `AGENT_ALLOWED_FIELDS`, `assert_agent_observation_safe()` |
| `schemas/episode_schema.py` | `EpisodeRecord`, `EpisodeMetadata` |
| `schemas/step_schema.py` | `StepRecord`, `ActionRecord`, `ActionEffectRecord` |
| `schemas/validation.py` | `validate_episode()`, `validate_step()`, `validate_visibility_contract()` |
| `data/leakage_auditor.py` | `LeakageAuditor`, `LeakageReport` |

### 7.3 Hard Assertions

Claude Code must implement runtime assertions.

```python
FORBIDDEN_AGENT_FIELDS = {
    "true_regime",
    "true_control_grammar",
    "true_change_point",
    "true_reveal_vs_shift",
    "true_wrong_hypothesis",
    "counterfactual_action_effects",
    "oracle_regime_action",
    "oracle_grammar_action",
    "split_id",
    "ood_type",
    "template_id",
    "seed",
}
```

If any forbidden field appears in agent observation, the code must raise an error.

### 7.4 Tests

| Test | Purpose |
|---|---|
| `test_visibility_contract.py` | hidden labels rejected from agent input |
| `test_episode_schema.py` | episode/step required fields enforced |
| `test_counterfactual_exclusion.py` | counterfactual-only fields excluded |
| `test_leakage_auditor.py` | template/split/grammar leakage detected |

### 7.5 Gate

| Gate | Pass Condition |
|---|---|
| CC-P1-G1 | forbidden hidden labels trigger failure |
| CC-P1-G2 | valid public observation passes |
| CC-P1-G3 | counterfactual table cannot be included in model input |
| CC-P1-G4 | tests pass before any data generation |

---

## 8. Phase CC-P2: Text-Only Data Generator

### 8.1 Required Read

- `04_TEXT_ONLY_SMOKE_TESTBED.md`
- `03_CORE_CONCEPT_TAXONOMY.md`
- `06_DATA_SCHEMA_AND_LABELING.md`
- `12_DATA_COLLECTION_METHODOLOGY.md`

### 8.2 Required Modules

| Module | Responsibility |
|---|---|
| `text_env/state.py` | symbolic state representation |
| `text_env/grammar.py` | hidden control grammar rules |
| `text_env/generator.py` | generate tasks/episodes |
| `text_env/policies.py` | oracle, wrong-grammar, retry, random, recovery policies |
| `text_env/collector.py` | collect DATA-T0/T1 text trajectories |

### 8.3 Required Task Families

At minimum implement:

1. search form
2. modal blocker
3. required dropdown
4. pagination vs infinite scroll
5. nested scroll
6. loading/delayed enable
7. permission gate
8. filter accordion

### 8.4 Required Policy Mix

| Policy | Ratio |
|---|---:|
| oracle/expert | 20% |
| wrong-grammar scripted | 25% |
| base/retry heuristic | 25% |
| recovery policy | 20% |
| random constrained | 10% |

### 8.5 Collection Command

```bash
python scripts/01_generate_text_data.py --config configs/data_collection_text.yaml
```

### 8.6 Tests

| Test | Purpose |
|---|---|
| `test_text_env.py` | state transition deterministic |
| `test_coverage_auditor.py` | failure/recovery/shift ratios pass |
| `test_visibility_contract.py` | public text excludes hidden grammar |
| `test_replay_text.py` | replay produces same transitions |

### 8.7 Gate

| Gate | Pass Condition |
|---|---|
| CC-P2-G1 | 20k~100k transitions generated |
| CC-P2-G2 | failed-action ratio >=20% |
| CC-P2-G3 | recovery ratio >=8% |
| CC-P2-G4 | repeated wrong mapping ratio >=8% |
| CC-P2-G5 | no hidden labels in public text |

---

## 9. Phase CC-P3: Text-Only Model and Planner

### 9.1 Required Read

- `07_LATENT_ARCHITECTURE_DESIGN.md`
- `08_LOSS_REWARD_TRAINING_OBJECTIVE.md`
- `09_PLANNING_THEORY_ALGORITHM.md`
- `10_EVALUATION_BASELINE_ABLATION.md`
- `11_MODEL_DATASET_SCALE_AND_TRAINING_BUDGET.md`

### 9.2 Required Modules

| Module | Required Components |
|---|---|
| `models/text_frcg_model.py` | tiny encoder, latent heads, effect/progress/falsification heads |
| `objectives/losses.py` | `L_action_effect`, `L_progress`, `L_control_grammar`, `L_falsification`, `L_mapping` |
| `planning/falsification.py` | likelihood-ratio or classifier-based falsification |
| `planning/alternative_proposer.py` | top-k alternative grammar proposer |
| `planning/decision_gate.py` | falsification + ΔV + action-switch gate |
| `planning/rewrite.py` | grammar-conditioned rewrite |
| `evaluation/metrics.py` | persistence, recovery delay, failed repetition, progress/compute |

### 9.3 Training Command

```bash
python scripts/02_train_text_smoke.py --config configs/train_text.yaml
```

### 9.4 Evaluation Command

```bash
python scripts/03_eval_text_smoke.py --config configs/eval_text.yaml
```

### 9.5 Required Baselines

| Baseline | Required |
|---|---:|
| reactive policy | YES |
| retry-after-failure | YES |
| verifier-only | YES |
| uncertainty-gated | YES |
| random alternative | YES |
| no-control-grammar | YES |
| no-falsification | YES |
| no-alternative | YES |
| no-rewrite | YES |

### 9.6 Gate

| Gate | Pass Condition |
|---|---|
| CC-P3-G1 | FRCG-text beats verifier-only on recovery delay |
| CC-P3-G2 | FRCG-text beats uncertainty-gated on progress per compute |
| CC-P3-G3 | no-control-grammar ablation worsens persistence |
| CC-P3-G4 | no-falsification ablation worsens recovery/falsification |
| CC-P3-G5 | if gates fail, do not proceed to VLM |

---

## 10. Phase CC-P4: Synthetic Web/GUI MVE Collector

### 10.1 Required Read

- `05_SYNTHETIC_WEB_GUI_ENVIRONMENT.md`
- `06_DATA_SCHEMA_AND_LABELING.md`
- `12_DATA_COLLECTION_METHODOLOGY.md`
- `11_MODEL_DATASET_SCALE_AND_TRAINING_BUDGET.md`

### 10.2 Required Modules

| Module | Responsibility |
|---|---|
| `gui_env/task_spec.py` | task family and subgoal specs |
| `gui_env/template_generator.py` | UI template variants |
| `gui_env/regime_grammar_engine.py` | hidden regime/control grammar assignment |
| `gui_env/event_scheduler.py` | reveal/shift/delay/noisy event scheduling |
| `gui_env/browser_executor.py` | synthetic browser action execution |
| `gui_env/action_space.py` | public action candidates |
| `logging/action_effect_logger.py` | pre/post state and effect diff |
| `logging/counterfactual_logger.py` | top-k counterfactual action effects |
| `logging/replay_validator.py` | deterministic replay |
| `data/shard_exporter.py` | JSONL/parquet/screenshot export |

### 10.3 Required MVE Task Families

1. search form
2. product/list filtering
3. modal confirmation
4. nested scroll
5. pagination/infinite scroll
6. disabled submit / form validation
7. permission/consent gate
8. async loading/stale DOM
9. settings toggle
10. multi-step wizard

### 10.4 Collection Command

```bash
python scripts/04_generate_gui_mve_data.py --config configs/data_collection_gui_mve.yaml
```

### 10.5 Validation Command

```bash
python scripts/05_validate_dataset.py --config configs/data_collection_gui_mve.yaml
```

### 10.6 Gate

| Gate | Pass Condition |
|---|---|
| CC-P4-G1 | deterministic replay pass |
| CC-P4-G2 | visibility/leakage audit pass |
| CC-P4-G3 | coverage audit pass |
| CC-P4-G4 | screenshot/DOM/a11y timestamps aligned |
| CC-P4-G5 | counterfactual actions valid and excluded from agent input |
| CC-P4-G6 | 50k~200k valid transitions for DATA-T3 |

---

## 11. Phase CC-P5: Frozen VLM MVE Model

### 11.1 Required Read

- `07_LATENT_ARCHITECTURE_DESIGN.md`
- `08_LOSS_REWARD_TRAINING_OBJECTIVE.md`
- `09_PLANNING_THEORY_ALGORITHM.md`
- `11_MODEL_DATASET_SCALE_AND_TRAINING_BUDGET.md`
- `12_DATA_COLLECTION_METHODOLOGY.md`

### 11.2 Implementation Rule

Default MVE model:

```text
Frozen Qwen2.5-VL-3B or equivalent frozen VLM/vision-language encoder
+ structured DOM/action-effect encoder
+ latent posterior heads
+ effect/progress/falsification/rewrite heads
```

Do not full fine-tune the VLM in this phase.

### 11.3 Required Modules

| Module | Required |
|---|---|
| `models/vlm_frcg_adapter.py` | frozen VLM embedding extractor |
| `models/encoders.py` | DOM/a11y/action-effect/history encoders |
| `models/latent_heads.py` | z_state/z_regime/z_control_grammar/z_change_point heads |
| `models/world_model_heads.py` | effect/progress/failure/falsification/rollout heads |
| `training/train_vlm_mve.py` | staged training loop |
| `training/monitoring.py` | loss/metric/leakage alerts |

### 11.4 Training Command

```bash
python scripts/06_train_vlm_mve.py --config configs/train_vlm_mve.yaml
```

### 11.5 Gate

| Gate | Pass Condition |
|---|---|
| CC-P5-G1 | effect prediction above trivial baseline |
| CC-P5-G2 | falsification P/R meaningful and calibrated |
| CC-P5-G3 | verifier-only beaten on recovery delay |
| CC-P5-G4 | uncertainty-gate beaten on progress per compute |
| CC-P5-G5 | no-control-grammar ablation degrades persistence |
| CC-P5-G6 | no hidden labels in inference batch logs |
| CC-P5-G7 | if fail, do not proceed to 7B main |

---

## 12. Phase CC-P6: Core Baselines and Ablations

### 12.1 Required Read

- `10_EVALUATION_BASELINE_ABLATION.md`
- `07_LATENT_ARCHITECTURE_DESIGN.md`
- `08_LOSS_REWARD_TRAINING_OBJECTIVE.md`
- `09_PLANNING_THEORY_ALGORITHM.md`
- `11_MODEL_DATASET_SCALE_AND_TRAINING_BUDGET.md`

### 12.2 Required Baselines

| Baseline | Must Implement Before Paper Claim? |
|---|---:|
| Frozen Base VLM/LLM | YES |
| reactive DOM/text | YES |
| retry-after-failure | YES |
| verifier-only | YES |
| failure diagnosis only | YES |
| next-state-WM-only | YES |
| always-plan world model | YES |
| fixed-horizon planner | YES |
| uncertainty-gated planner | YES |
| random alternative planner | YES |
| compute-matched random reallocation | YES |
| oracle regime | YES for upper bound |
| oracle control grammar | YES for upper bound |
| oracle alternative hypothesis | YES for upper bound |

### 12.3 Critical Ablations

| Ablation | If No Metric Drop |
|---|---|
| no-control-grammar | core grammar claim collapses |
| merged regime-control grammar | separation claim weakens |
| collapsed latent | factorization claim weakens |
| no-falsification | falsification novelty collapses |
| uncertainty instead of falsification | decision rule novelty weakens |
| no alternative hypothesis | alternative rollout claim weakens |
| random alternative | proposer quality weakens |
| no rollout | world model planning claim weakens |
| no rewrite | action-interface claim weakens |
| always-plan/no-gate | compute gate claim weakens |
| no reward/progress | objective contribution weakens |

### 12.4 Evaluation Command

```bash
python scripts/07_eval_vlm_mve.py --config configs/eval_gui_mve.yaml
python scripts/08_run_core_ablations.py --config configs/ablation_core.yaml
```

### 12.5 Gate

| Gate | Pass Condition |
|---|---|
| CC-P6-G1 | compute budgets logged for all methods |
| CC-P6-G2 | core baselines run on same split |
| CC-P6-G3 | critical ablations have expected metric drops |
| CC-P6-G4 | failure interpretation table generated |
| CC-P6-G5 | no fake result or manual cherry-pick |

---

## 13. Phase CC-P7: Paper-Main Planning

Claude Code must not automatically start paper-main training.  
It must generate a run plan and wait for human decision.

### 13.1 Required Read

- `11_MODEL_DATASET_SCALE_AND_TRAINING_BUDGET.md`
- `10_EVALUATION_BASELINE_ABLATION.md`
- `12_DATA_COLLECTION_METHODOLOGY.md`
- `FINAL_RESEARCH_BLUEPRINT.md`

### 13.2 Paper-Main Candidate

| Item | Recommended |
|---|---|
| model | frozen/QLoRA Qwen2.5-VL-7B or equivalent |
| data | 300k~1M transitions |
| templates | 50~150 |
| grammar variants | 20~40 |
| OOD splits | 8~10 |
| ablations | critical set first |
| hardware | A100 80GB or H100 80GB preferred |

### 13.3 Required Human Review Before Running

Claude Code must produce:

1. estimated GPU hours,
2. dataset storage estimate,
3. run order,
4. baseline/ablation list,
5. expected failure interpretation,
6. stop condition,
7. config diff from MVE,
8. risk register.

---

## 14. Phase CC-P8: Report and Artifact Generation

### 14.1 Required Read

- `10_EVALUATION_BASELINE_ABLATION.md`
- `FINAL_RESEARCH_BLUEPRINT.md`

### 14.2 Required Outputs

| Artifact | Description |
|---|---|
| `outputs/reports/metric_summary.md` | metric tables without fake numbers |
| `outputs/reports/ablation_summary.md` | ablation outcomes and interpretation |
| `outputs/reports/failure_cases.md` | qualitative selected cases |
| `outputs/reports/compute_budget.md` | compute-matched logs |
| `outputs/figures/` | plots generated only from real logs |
| `outputs/tables/` | CSV/markdown tables |

### 14.3 Forbidden

- Do not invent result numbers.
- Do not claim main-track evidence from partial runs.
- Do not hide negative ablations.
- Do not remove failure cases.

---

## 15. Claude Code Command Templates

### 15.1 Scaffold

```text
Read docs/13_CLAUDE_CODE_EXECUTION_ROADMAP.md.
Create only the repository scaffold and placeholder modules.
Do not implement model logic yet.
Run pytest.
Report created files and missing decisions.
```

### 15.2 Schema

```text
Read docs/06_DATA_SCHEMA_AND_LABELING.md and docs/12_DATA_COLLECTION_METHODOLOGY.md.
Implement visibility bucket schema and runtime assertions.
Write tests that fail if hidden labels appear in agent observation.
Run pytest.
Do not implement data generation until tests pass.
```

### 15.3 Text Data

```text
Read docs/04_TEXT_ONLY_SMOKE_TESTBED.md and docs/12_DATA_COLLECTION_METHODOLOGY.md.
Implement text-only task generator, grammar engine, policy mixture, and collector.
Generate a small DATA-T0 sample first.
Run coverage and leakage audits.
Do not train until audits pass.
```

### 15.4 Text Model

```text
Read docs/07, docs/08, docs/09, docs/10.
Implement minimal text FRCG model and baselines.
Train on DATA-T1.
Evaluate persistence, failed repetition, recovery delay, falsification PR, progress per compute.
Run no-control-grammar and no-falsification ablations.
Do not proceed to VLM if ablations do not degrade.
```

### 15.5 GUI MVE

```text
Read docs/05, docs/06, docs/11, docs/12.
Implement synthetic GUI MVE collector.
Generate 100-episode dry-run.
Validate replay, leakage, coverage, counterfactual exclusion.
Only then generate DATA-T3.
```

### 15.6 VLM MVE

```text
Read docs/07, docs/08, docs/09, docs/11.
Implement frozen VLM adapter and FRCG heads.
Train only heads/LoRA as configured.
Log all input field names per batch to prove hidden labels are excluded.
Evaluate against verifier-only, next-state-WM-only, uncertainty-gated, always-plan.
```

---

## 16. Quality Gates Across Entire Roadmap

| Gate ID | Gate | Blocks |
|---|---|---|
| ROAD-GATE-001 | docs present and readable | all implementation |
| ROAD-GATE-002 | visibility tests pass | all data generation |
| ROAD-GATE-003 | text-only data coverage pass | text model training |
| ROAD-GATE-004 | text model core ablations collapse | VLM MVE |
| ROAD-GATE-005 | GUI replay/leakage pass | VLM MVE training |
| ROAD-GATE-006 | frozen VLM MVE beats direct baselines | 7B main |
| ROAD-GATE-007 | compute-matched eval implemented | planning claims |
| ROAD-GATE-008 | critical ablations implemented | final claims |
| ROAD-GATE-009 | failure interpretation generated | report writing |
| ROAD-GATE-010 | no fake result assertion | all reporting |

---

## 17. Failure Handling Protocol

| Failure | Meaning | Action |
|---|---|---|
| hidden label leakage | experiment invalid | discard shard and fix schema |
| text-only no-control-grammar no effect | grammar claim weak | revise taxonomy/problem |
| text-only no-falsification no effect | falsification claim weak | revise evidence/loss |
| verifier-only matches recovery | novelty weak | revise alternative/rewrite path |
| uncertainty-gate matches progress/compute | VOC gate weak | revise decision rule |
| next-state-WM matches OOD grammar | grammar WM weak | revise grammar-specific data/architecture |
| no-rewrite no effect | rewrite not needed | weaken action-interface claim |
| always-plan wins under fair compute | gate not helpful | limit compute claim |
| OOD-control grammar fails | generalization weak | restrict claim to ID/synthetic |
| real auxiliary fails | external validity weak | keep as limitation |

---

## 18. Claude Code Self-Audit Checklist

Before each final response, Claude Code must answer internally:

| Check | Question |
|---|---|
| SELF-001 | Did I read the required MD files for this task? |
| SELF-002 | Did I preserve terminology from `03_CORE_CONCEPT_TAXONOMY.md`? |
| SELF-003 | Did I preserve visibility contract from `06`? |
| SELF-004 | Did I avoid hidden labels in inference path? |
| SELF-005 | Did I avoid claiming empirical results? |
| SELF-006 | Did I add or update tests? |
| SELF-007 | Did I run or specify the correct validation command? |
| SELF-008 | Did I keep baselines/ablations required by `10`? |
| SELF-009 | Did I report blockers instead of guessing? |
| SELF-010 | Did I avoid scaling before gates pass? |

---

## 19. Risk Ledger

| Risk ID | Risk | Mitigation |
|---|---|---|
| ROAD-RISK-001 | Claude Code reads only FINAL and misses source contracts | required read policy |
| ROAD-RISK-002 | implementation starts from VLM main | phase gates |
| ROAD-RISK-003 | schema tests skipped | CC-P1 mandatory |
| ROAD-RISK-004 | hidden labels leak into batch | runtime batch field logging |
| ROAD-RISK-005 | weak baselines omitted | CC-P6 required baseline table |
| ROAD-RISK-006 | ablation results ignored | failure protocol |
| ROAD-RISK-007 | compute mismatch | compute_budget logger |
| ROAD-RISK-008 | text-only overclaimed | phase purpose warnings |
| ROAD-RISK-009 | real auxiliary overclaimed | auxiliary-only policy |
| ROAD-RISK-010 | Claude Code invents numbers | report artifact rule |
| ROAD-RISK-011 | concept drift across files | source MD references in docstrings |
| ROAD-RISK-012 | module bloat | MVE-first implementation |
| ROAD-RISK-013 | poor test coverage | tests required per phase |
| ROAD-RISK-014 | path/config mismatch | central config loader |
| ROAD-RISK-015 | failed run silently used | manifest and run status required |

---

## 20. Required Docstring Pattern

Every major module must include a source-doc contract.

Example:

```python
"""FRCG-WM visibility sanitizer.

Source docs:
- docs/06_DATA_SCHEMA_AND_LABELING.md
- docs/12_DATA_COLLECTION_METHODOLOGY.md
- docs/13_CLAUDE_CODE_EXECUTION_ROADMAP.md

Hard constraints:
- hidden labels must never appear in AGENT_OBSERVATION.
- counterfactual labels must never appear in inference input.
- audit metadata must not be used as model features.
"""
```

---

## 21. Required Configuration Principles

| Config Principle | Rule |
|---|---|
| explicit paths | no hidden default data path |
| explicit seed | every generation/training/eval config must include seed |
| explicit split | train/valid/test/OOD must be named |
| explicit visibility | dataloader must define input fields and target fields |
| explicit compute budget | planning calls and rollout budget configured |
| explicit ablation | ablation name encoded in run config |
| explicit version | dataset/model/schema version required |
| explicit forbidden fields | forbidden fields listed in config or code |

---

## 22. Final Quality Gate Result

| Gate ID | Gate | PASS/FAIL/PARTIAL | Evidence | If Not PASS |
|---|---|---|---|---|
| QG-13-01 | repo scaffold specified | PASS | §4 | 없음 |
| QG-13-02 | execution phases specified | PASS | §5~14 | 없음 |
| QG-13-03 | read policy specified | PASS | §3 | 없음 |
| QG-13-04 | schema/leakage phase specified | PASS | §7 | 없음 |
| QG-13-05 | text-only implementation path specified | PASS | §8~9 | 없음 |
| QG-13-06 | GUI MVE collector path specified | PASS | §10 | 없음 |
| QG-13-07 | VLM MVE path specified | PASS | §11 | 없음 |
| QG-13-08 | baseline/ablation path specified | PASS | §12 | 없음 |
| QG-13-09 | paper-main run requires human review | PASS | §13 | 없음 |
| QG-13-10 | command templates included | PASS | §15 | 없음 |
| QG-13-11 | failure handling included | PASS | §17 | 없음 |
| QG-13-12 | no empirical result fabricated | PASS | document status | 없음 |
| QG-13-13 | hidden label inference ban included | PASS | §7, §16, §18 | 없음 |
| QG-13-14 | Claude Code self-audit included | PASS | §18 | 없음 |

---

## 23. Final Statement

`13_CLAUDE_CODE_EXECUTION_ROADMAP.md`는 구현 코드가 아니다.  
이 파일은 Claude Code가 FRCG-WM repo를 안전하고 검증 가능하게 구축하도록 만드는 실행 로드맵이다.

가장 중요한 규칙은 다음이다.

```text
Do not let Claude Code jump to the impressive part.

The correct order is:
docs and scaffold
→ schema and visibility tests
→ text-only data
→ text-only model and ablations
→ synthetic GUI MVE data
→ frozen VLM MVE
→ compute-matched baselines and ablations
→ only then paper-main planning.
```

다음 필수 파일:

```text
14_TRD_TECHNICAL_REQUIREMENTS_DOCUMENT.md
```
