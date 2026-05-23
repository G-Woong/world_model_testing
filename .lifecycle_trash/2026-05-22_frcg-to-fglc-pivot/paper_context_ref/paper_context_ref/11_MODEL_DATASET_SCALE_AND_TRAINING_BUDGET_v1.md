---
file_id: STEP-11
title: Model, Dataset Scale, Coverage, and Training Budget Design for FRCG-WM
version: v1.0
status: scale_budget_contract_not_empirical_result
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
  - FINAL_RESEARCH_BLUEPRINT.md
purpose:
  - FRCG-WM 연구를 실제 구현 가능한 실험 단계로 낮추기 위해 모델 크기, 데이터셋 규모, 분포 커버리지, 학습 자원, 비용 산식, stop/go gate를 정량화한다.
  - 기존 00~10 파일의 qualitative design을 quantitative experiment budget contract로 연결한다.
  - text-only smoke, multimodal MVE, paper-main, optional large-model validation을 분리하여 무리한 실험 확장을 방지한다.
forbidden:
  - Do not treat the budgets as empirical results.
  - Do not start with 7B/72B VLM before text-only and 3B frozen-MVE gates pass.
  - Do not use hidden labels as inference inputs.
  - Do not scale dataset size before leakage audit and distribution coverage audit pass.
  - Do not claim main-track evidence from text-only or ID-only results.
  - Do not ignore compute-matched evaluation cost.
next_files:
  - 12_MVE_IMPLEMENTATION_ROADMAP.md
  - 13_TRAINING_RUNBOOK_AND_MONITORING.md
  - 14_EXPERIMENT_EXECUTION_PLAN.md
---

# 11_MODEL_DATASET_SCALE_AND_TRAINING_BUDGET.md

## 1. File Purpose

이 파일은 모델 방법론 파일이 아니다. 이 파일은 FRCG-WM 실험을 실제로 굴릴 때 필요한 **모델 크기, 데이터셋 규모, 분포 커버리지, GPU 자원, 예상 비용, stop/go gate**를 정량화하는 실행 예산 계약서다.

기존 `00~10` 파일은 문제정의, 개념, 환경, schema, architecture, objective, planning, evaluation을 설계했다. 그러나 구현자가 바로 실험을 돌리려면 다음 질문이 남는다.

1. 어떤 크기의 모델부터 시작할 것인가?
2. VLM backbone을 언제 freeze하고 언제 LoRA/QLoRA로 풀 것인가?
3. text-only, MVE, paper-main 단계에서 데이터 transition 수는 얼마나 필요한가?
4. failed-action, recovery, reveal, shift, delayed/noisy effect는 어떤 비율로 들어가야 하는가?
5. GPU는 T4/4090/A100/H100 중 무엇을 언제 쓰는가?
6. 비용은 어떤 산식으로 추정하는가?
7. 어떤 결과가 나오면 다음 단계로 넘어가고, 어떤 결과면 중단하는가?

이 파일은 위 질문을 정량화한다.

---

## 2. Claude Code Context Routing

| User Intent / Task | Must Read First | Then Read | Do Not Assume |
|---|---|---|---|
| 모델 크기 선택 | `11_MODEL_DATASET_SCALE_AND_TRAINING_BUDGET.md` §5~7 | `07_LATENT_ARCHITECTURE_DESIGN.md`, `08_LOSS_REWARD_TRAINING_OBJECTIVE.md` | 7B부터 시작해도 된다고 가정 금지 |
| 데이터셋 생성량 결정 | `11` §8~11 | `05_SYNTHETIC_WEB_GUI_ENVIRONMENT.md`, `06_DATA_SCHEMA_AND_LABELING.md` | success transition만 많이 만들면 충분하다고 가정 금지 |
| 실패/회복/shift 분포 설정 | `11` §9~10 | `03_CORE_CONCEPT_TAXONOMY.md`, `06`, `10` | failed-action과 wrong-control-grammar를 동일시 금지 |
| GPU 예산 계산 | `11` §12~14 | provider pricing page, local run logs | 가격표를 고정값으로 가정 금지 |
| MVE 구현 범위 결정 | `11` §15~16 | `04`, `05`, `06`, `09`, `10` | MVE가 main-track evidence라고 주장 금지 |
| Main experiment 확장 판단 | `11` §17~19 | `10_EVALUATION_BASELINE_ABLATION.md` | ID success만으로 확장 금지 |
| 중단/재설계 판단 | `11` §20~22 | `02`, `07`, `08`, `09`, `10` | 실패한 claim을 억지로 유지 금지 |

---

## 3. External Anchor Ledger

> 아래 anchor는 설계 기준점이다. 실제 실행 전에는 가격과 모델 card를 다시 확인해야 한다.

| Anchor ID | Source / URL | What It Supports | Current Use | Risk |
|---|---|---|---|---|
| EXT-11-001 | https://qwen.ai/blog?id=qwen2.5-vl | Qwen2.5-VL이 3B/7B/72B 크기로 공개됨 | VLM backbone tier 설계 | 모델 버전 업데이트 가능 |
| EXT-11-002 | https://huggingface.co/docs/transformers/model_doc/qwen2_5_vl | Qwen2.5-VL family, 3B/7B/72B, vision encoder/window attention/MRoPE 설명 | 3B→7B 단계화 근거 | 실제 VRAM은 구현 세팅 의존 |
| EXT-11-003 | https://huggingface.co/collections/Qwen/qwen25-vl | Qwen2.5-VL model collection | repo/checkpoint 선택 | collection 갱신 가능 |
| EXT-11-004 | https://www.runpod.io/pricing | GPU 시간당 가격 재확인 anchor | 비용 산식 예시 | region/secure/community/spot에 따라 변동 |
| EXT-11-005 | https://pytorch.org/blog/activation-checkpointing-techniques/ | activation checkpointing이 memory-compute trade-off 기법임 | VLM 실험 메모리 최적화 | 속도 저하 발생 |
| EXT-11-006 | QLoRA paper / HF ecosystem | 4-bit frozen base + low-rank adaptation 방향 | 7B LoRA/QLoRA 실험 | VLM-specific 구현 난도 |
| EXT-11-007 | DreamerV3 / latent world model line | pixel reconstruction보다 latent imagination/transition 중심 | latent transition 설계 방향 | Web/GUI grammar-specific novelty와 구분 필요 |

---

## 4. Core Scaling Principle

FRCG-WM은 처음부터 대형 VLM으로 가면 안 된다. 실험은 반드시 다음 순서를 따른다.

```text
Stage A: Text-only symbolic smoke test
→ Stage B: Multimodal MVE with frozen small VLM/features
→ Stage C: Paper-main synthetic Web/GUI with 7B frozen/LoRA VLM
→ Stage D: Optional large-model and real-benchmark auxiliary validation
```

핵심 원칙:

1. 아이디어 검증은 text-only에서 먼저 죽인다.
2. VLM은 feature extractor로 먼저 사용한다.
3. pixel prediction을 하지 않는다.
4. latent transition/effect/progress/falsification을 학습한다.
5. hidden labels는 training/evaluation에만 사용한다.
6. scaling은 leakage audit과 ablation gate 통과 후에만 진행한다.
7. 성공률보다 mechanism metric을 먼저 본다.
8. compute-matched evaluation cost를 처음부터 예산에 포함한다.

---

## 5. Model Tier Contract

| Tier ID | Stage | Backbone | Trainable Params | Main Trainable Parts | Target Purpose | Allowed Before |
|---|---|---|---:|---|---|---|
| MODEL-T0 | text-only smoke | MLP/GRU/Tiny Transformer | 5M~50M | text state encoder, grammar head, falsification head, rewrite policy | mechanism viability | 아무 조건 없음 |
| MODEL-T1 | multimodal MVE-light | frozen CLIP/SigLIP or frozen small VLM feature | 10M~80M heads | DOM/action-effect encoder, latent heads, progress/falsification heads | image+text+log pipeline sanity | T0 pass |
| MODEL-T2 | multimodal MVE-VLM | frozen Qwen2.5-VL-3B or equivalent | 10M~100M heads | structured encoders + FRCG heads | VLM context injection sanity | T0 pass + schema audit pass |
| MODEL-T3 | paper-main | frozen or QLoRA Qwen2.5-VL-7B or equivalent | 50M~200M heads/LoRA | FRCG full heads, rollout, rewrite, gate | main synthetic Web/GUI evidence | T2 pass |
| MODEL-T4 | upper-bound / auxiliary | 32B~72B VLM inference-only or LoRA if budget allows | 0~200M adapter optional | evaluator, teacher, strong base comparison | “base가 좋아서 된 것” 공격 점검 | T3 meaningful result |
| MODEL-T5 | rejected initial path | full fine-tuning 7B/72B VLM | billions | entire VLM | not recommended | 금지 |

Recommended default:

```text
Start: MODEL-T0
First multimodal: MODEL-T2 with frozen Qwen2.5-VL-3B
Main candidate: MODEL-T3 with Qwen2.5-VL-7B frozen/QLoRA
Never start from: MODEL-T5
```

---

## 6. Architecture Scale by Stage

| Stage | Observation Input | Backbone Usage | FRCG Modules | Rollout | Rewrite | Primary Metrics |
|---|---|---|---|---|---|---|
| A. Text-only | symbolic state/action/effect text | none or tiny text encoder | grammar/falsification/progress/rewrite heads | 1~3 symbolic steps | rule-based or tiny learned | persistence, recovery, progress/compute |
| B. MVE-light | DOM + action-effect log + optional image embedding | frozen visual/text feature | same as FRCG minimal | 1-step, then 3-step | grammar-conditioned action ranking | leakage, effect prediction, falsification PR |
| C. MVE-VLM | DOM + screenshot + action text + history | frozen 3B VLM embeddings | latent posterior + all core heads | 1~3 | learned rewrite head | rollout fidelity, recovery delay |
| D. Main | DOM + screenshot + a11y + structured log | frozen/QLoRA 7B VLM | full architecture | 1/3/5 ablation | macro-capable rewrite | full metric suite |
| E. Auxiliary | real benchmark traces | frozen large VLM | limited heads/proxies | weak/no counterfactual | limited | success + weak proxy only |

---

## 7. Recommended Backbone Candidates

| Candidate | Role | Why Suitable | Risk | Use |
|---|---|---|---|---|
| Tiny Transformer 5M~50M | text-only smoke | cheap, fast, mechanism-only | multimodal 없음 | Stage A |
| CLIP/SigLIP frozen encoder | MVE-light | image embedding cheap | LLM/action reasoning 약함 | Stage B alternative |
| Qwen2.5-VL-3B | first VLM MVE | 3B/7B/72B family 중 가장 현실적 initial VLM | lower ceiling | Stage C first |
| Qwen2.5-VL-7B | paper-main candidate | VLM capability와 비용 균형 | A100급 필요 | Stage D |
| Qwen2.5-VL-72B | teacher/upper-bound | strong base check | training cost 과도 | Stage E inference-only |
| GPT-4o/Claude/Gemini API | evaluator/teacher only | strong external sanity | reproducibility/cost/API risk | optional analysis only |

---

## 8. Dataset Tier Contract

| Dataset Tier | Stage | Episodes | Transitions | Image Pairs | Task Families | UI Templates | Grammar Families | Purpose |
|---|---|---:|---:|---:|---:|---:|---:|---|
| DATA-T0 | text-only smoke small | 500~2,000 | 5k~20k | 0 | 4~6 | 0 | 6~10 | bug finding |
| DATA-T1 | text-only smoke full | 2k~10k | 20k~100k | 0 | 8~12 | 0 | 10~20 | mechanism gate |
| DATA-T2 | multimodal MVE small | 1k~5k | 10k~50k | 10k~50k | 5~8 | 10~20 | 8~15 | pipeline sanity |
| DATA-T3 | multimodal MVE full | 5k~20k | 50k~200k | 50k~200k | 10~15 | 20~50 | 15~25 | first VLM evidence |
| DATA-T4 | paper-main synthetic | 30k~100k | 300k~1M | 300k~1M | 15~25 | 50~150 | 20~40 | main evidence |
| DATA-T5 | large synthetic / appendix | 100k~300k | 1M~3M | 1M~3M | 25~40 | 150~300 | 40~80 | scaling/appendix |
| DATA-T6 | real auxiliary | benchmark dependent | trace dependent | trace dependent | external | external | weak/no labels | external validity only |

Default plan:

```text
A: DATA-T1
B/C: DATA-T3
D: DATA-T4
E: DATA-T6 optional
```

---

## 9. Dataset Distribution Coverage Contract

초기 MVE와 paper-main 데이터셋은 success-only 데이터가 아니어야 한다. FRCG-WM은 실패와 회복을 학습해야 하므로 failed/recovery/shift transition이 충분히 많아야 한다.

| Transition Type | Target Ratio in Training | Minimum Ratio | Why Needed | If Missing |
|---|---:|---:|---|---|
| normal progress | 30~40% | 25% | task value/progress learning | model이 failure-heavy로 치우침 |
| failed action | 25~35% | 20% | falsification/retry failure 학습 | wrong hypothesis positive 부족 |
| repeated failed mapping | 10~20% | 8% | persistence metric 학습 | 핵심 failure mode 학습 불가 |
| recovery action | 10~20% | 8% | recovery ranking/rewrite 학습 | failure 이후 action 개선 불가 |
| reveal event | 8~15% | 5% | reveal-vs-shift 분리 | 모든 event를 shift로 오판 |
| control-grammar shift event | 10~20% | 8% | grammar posterior/falsification 학습 | core novelty 학습 부족 |
| delayed/noisy/stale effect | 8~15% | 5% | false falsification 방지 | no-effect를 wrong grammar로 오판 |
| blocker/modal/permission | 8~15% | 5% | precondition/rewrite 학습 | GUI 현실성 약화 |
| no-op but valid wait | 3~8% | 2% | no-effect≠failure 구분 | false positive 증가 |
| invalid switch / unnecessary switch | 5~10% | 3% | switch reward hacking 방지 | over-switching 탐지 불가 |

### 9.1 Batch Sampling Policy

| Batch Policy | Rule | Purpose |
|---|---|---|
| balanced falsification batch | wrong-current positive 30~50% 유지 | L_falsification class imbalance 방지 |
| mixed transition batch | progress/failure/recovery/shift를 한 batch에 섞음 | loss collapse 방지 |
| OOD holdout batch | train 중 OOD labels 사용 금지 | generalization 평가 유지 |
| delayed-effect batch | delayed/noisy cases를 별도 oversample | false falsification 방지 |
| no-leak batch assertion | hidden label fields가 input tensor에 없는지 assert | 실험 무효 방지 |

---

## 10. Coverage Matrix

| Coverage Axis | Required Values | Minimum Coverage Before Main | Connected Claim |
|---|---|---:|---|
| Task family | search, filter, form, modal, checkout, navigation, settings, permission, pagination, upload-like mock | 10+ | generality |
| Control grammar | direct-click, prerequisite-first, modal-confirm, infinite-scroll, container-scroll, accordion-open, delayed-enable, stale-retry, permission-accept, form-valid-then-submit | 15+ | grammar novelty |
| Regime | desktop, mobile-like, protected, async-loading, modal-heavy, nested-scroll, dynamic-form, multi-step | 8+ | regime latent |
| Event type | none, reveal, shift, failure, delayed, noisy, blocked | 7 | change-point/reveal-shift |
| UI template | list, grid, form, checkout, dashboard, settings, search-result, modal, nested panel | 20+ MVE / 50+ main | anti-toy |
| Visual layout | same grammar/different layout and same layout/different grammar | both required | shortcut defense |
| DOM text | exact, paraphrase, misleading label, icon-only | 4 | DOM shortcut defense |
| Action primitive | click, type, select, scroll page, scroll container, wait, hover, confirm, back | 8+ | action interface |
| Macro action | open+click, type+validate+submit, scroll+select, permission+confirm | 4+ MVE / 10+ main | rewrite claim |
| OOD split | regime recombination, control grammar shift, visual/layout, DOM/text, timing, reveal-shift, unseen template, long-horizon | 8+ | main evidence |

---

## 11. Recommended Experiment Phases

| Phase | Name | Model Tier | Dataset Tier | Primary Goal | Stop/Go Gate |
|---|---|---|---|---|---|
| P0 | schema/leakage dry-run | no model | DATA-T0 subset | data visibility and leakage audit | hidden labels never in agent input |
| P1 | text-only smoke | MODEL-T0 | DATA-T1 | mechanism viability | no-control-grammar/no-falsification ablations collapse |
| P2 | multimodal pipeline sanity | MODEL-T1/T2 | DATA-T2 | image+text+log injection works | effect prediction/falsification above trivial baseline |
| P3 | VLM frozen MVE | MODEL-T2 | DATA-T3 | frozen VLM + heads work | verifier-only and uncertainty-gate beaten on mechanism metrics |
| P4 | paper-main synthetic | MODEL-T3 | DATA-T4 | main evidence | compute-matched full evaluation passes |
| P5 | ablation/robustness expansion | MODEL-T3 | DATA-T4 | claim defense | core ablations collapse as expected |
| P6 | optional auxiliary real benchmark | MODEL-T3/T4 | DATA-T6 | external validity | weak external support without overclaim |
| P7 | appendix scaling | MODEL-T4/T5 | DATA-T5 | scale trend | only if P4/P5 strong |

---

## 12. GPU Resource Contract

| GPU Tier | Example | VRAM | Suitable Stage | Notes |
|---|---|---:|---|---|
| CPU only | local CPU | RAM dependent | tiny text debug | slow but possible |
| T4 / L4 | 16~24GB | 16~24GB | text-only, small frozen features | not ideal for VLM training |
| RTX 3090/4090 | 24GB | 24GB | MODEL-T0/T1/T2 with low batch/frozen | good local/MVE option |
| L40/L40S | 48GB | 48GB | 3B VLM frozen, some 7B QLoRA | cost-effective if available |
| A100 40GB | 40GB | 40GB | 3B VLM, 7B LoRA with care | batch/seq constrained |
| A100 80GB | 80GB | 80GB | 7B frozen/QLoRA main | recommended main |
| H100 80GB | 80GB | 80GB | faster 7B main, scaling | expensive but time-efficient |
| multi-GPU H100/A100 | 160GB+ | 160GB+ | 32B/72B optional | not initial path |

### 12.1 Memory-Saving Techniques

| Technique | Required Stage | Why |
|---|---|---|
| freeze VLM backbone | P2~P4 default | reduces trainable memory |
| LoRA/QLoRA | P4 optional | adapt 7B without full fine-tune |
| activation checkpointing | P3~P5 | reduce activation memory |
| gradient accumulation | P2~P5 | simulate larger batch |
| mixed precision bf16/fp16 | P2~P5 | reduce memory and speed up |
| image resolution cap 224~336 px | P2~P4 | prevent image token explosion |
| sequence length cap | all VLM stages | avoid context blow-up |
| cached image/VLM embeddings | P2/P3 | speed up head training |
| structured log first | all stages | reduce reliance on raw pixels |

---

## 13. Training Time and Cost Estimate

> 비용은 실험 전 반드시 provider pricing page에서 재확인해야 한다. 아래는 planning budget을 위한 rough estimate다.

### 13.1 Cost Formula

```text
total_gpu_hours = num_gpus × wall_clock_hours
estimated_cost_usd = total_gpu_hours × hourly_rate_usd
storage_cost = image_pairs × avg_image_pair_size + logs + checkpoints
total_cost ≈ training_cost + evaluation_cost + storage_cost + failed_run_margin
```

Recommended failed-run margin:

```text
research prototype: +30%
paper-main experiments: +50%
```

### 13.2 Stage-Level Estimate

| Phase | Model/Data | GPU | Wall-clock Estimate | GPU-hour Estimate | Budget Class | Notes |
|---|---|---|---:|---:|---|---|
| P0 | schema dry-run | CPU | 0.5~2h | 0 | free | must run often |
| P1 | text-only MODEL-T0/DATA-T1 | CPU/T4/4090 | 1~8h | 0~8 | negligible | idea killer |
| P2 | MVE small frozen features | 4090/A10/L40 | 4~24h | 4~24 | low | pipeline debug |
| P3 | Qwen2.5-VL-3B frozen + heads / DATA-T3 | 4090/A100 40/80 | 24~72h | 24~72 | medium | first serious multimodal |
| P4 | Qwen2.5-VL-7B frozen/QLoRA + heads / DATA-T4 | A100 80/H100 | 72~168h | 72~168 | high | main training |
| P5 | ablations 8~20 runs | A100/H100 | 3~10× P4 equivalent depending reuse | 300~1,500 | very high | must cache embeddings/checkpoints |
| P6 | real auxiliary eval | A100/H100 or API | 12~72h | 12~72 | medium | no full hidden labels |
| P7 | scale appendix | H100/multi-GPU | 1~3 weeks | 168~1,000+ | optional high | only after strong P4/P5 |

### 13.3 Example Budget Scenarios

| Scenario | What It Includes | Approx GPU Hours | Cost Sensitivity |
|---|---|---:|---|
| Minimal viability | P0+P1 only | 0~8 | almost free |
| Multimodal MVE | P0~P3 | 30~100 | single 4090/A100 class |
| Paper-main single run | P0~P4 | 100~250 | A100/H100 price sensitive |
| Paper-main with core ablations | P0~P5 with 8 core ablations | 500~1,500 | main budget driver |
| Full main-track attempt | P0~P6 + OOD + baselines + ablations | 1,000~3,000 | requires careful caching |
| Scaling appendix | P7 | 1,000+ additional | optional only |

---

## 14. Data Storage and I/O Budget

| Item | Small MVE | Main Synthetic | Risk |
|---|---:|---:|---|
| JSONL structured logs | 1~5GB | 10~100GB | manageable |
| screenshots compressed | 5~50GB | 100GB~1TB | main storage driver |
| cached VLM embeddings | 5~30GB | 50~500GB | speeds training but storage-heavy |
| checkpoints | 1~20GB | 20~200GB | many ablations multiply storage |
| trace visualizations | <5GB | 10~100GB | qualitative analysis storage |
| tensorboard/wandb logs | <1GB | 1~20GB | long ablations accumulate |

Storage policy:

```text
raw screenshots: keep for audit and visual examples
cached embeddings: keep for speed, but version/hash them
failed run checkpoints: delete unless needed for debugging
structured logs: never delete until paper decision
```

---

## 15. Minimum Viable Experiment MVE-0

MVE-0은 VLM을 쓰지 않는다. 목적은 아이디어가 죽는지 확인하는 것이다.

| Component | Required |
|---|---|
| model | 5M~50M text transformer or GRU |
| data | 2k~10k episodes, 20k~100k transitions |
| labels | true_control_grammar, true_wrong_hypothesis, progress_delta, failed_action, recovery_action |
| metrics | persistence time, failed repetition, recovery delay, falsification PR, progress/compute |
| baselines | reactive, verifier-only, uncertainty-gated, no-grammar, no-falsification |
| pass gate | no-control-grammar and no-falsification ablations must degrade mechanism metrics |
| fail action | if no degradation, revise problem/taxonomy before VLM |

MVE-0 pass condition:

```text
FRCG-text beats verifier-only on recovery delay
FRCG-text beats uncertainty-gate on progress per compute
no-control-grammar ablation worsens persistence
no-falsification ablation worsens recovery/falsification PR
```

---

## 16. Minimum Multimodal Experiment MVE-1

MVE-1은 frozen VLM/visual encoder를 사용하되, VLM 자체를 크게 학습하지 않는다.

| Component | Required |
|---|---|
| model | frozen Qwen2.5-VL-3B or frozen visual/text encoders + FRCG heads |
| data | 5k~20k episodes, 50k~200k transitions |
| image | 224~336px, compressed, deterministic viewport |
| structured input | DOM + a11y + action-effect log mandatory |
| losses | L_action_effect, L_progress, L_control_grammar, L_falsification, L_mapping |
| rollout | horizon 1 and 3 |
| alternatives | top-k 1/3 sweep |
| baselines | Frozen Base, verifier-only, next-state-WM-only, uncertainty-gated |
| pass gate | mechanism metrics improve under compute-matched comparison |

MVE-1 fail conditions:

```text
If hidden label leakage detected: discard run.
If no-control-grammar ablation does not degrade: do not scale to 7B.
If verifier-only matches recovery delay: revise falsification/rewrite.
If uncertainty-gate matches progress per compute: revise VOC gate.
```

---

## 17. Paper-Main Experiment Scale

Paper-main은 처음부터 대규모가 아니라, MVE-1 통과 후 확장한다.

| Item | Recommended Main |
|---|---|
| model | Qwen2.5-VL-7B frozen/QLoRA + FRCG heads |
| trainable params | 50M~200M |
| episodes | 30k~100k |
| transitions | 300k~1M |
| OOD splits | 8~10 |
| templates | 50~150 |
| grammar variants | 20~40 |
| horizon | 1/3/5 ablation, default 3 only if validated |
| top-k | 1/3/5 ablation, default 3 only if validated |
| evaluation | compute-matched full baseline suite |
| ablations | no-control-grammar, no-falsification, no-alternative, no-rollout, no-rewrite, uncertainty instead, always-plan, merged/collapsed latent |

Main run is not valid unless:

```text
leakage audit passes
OOD split integrity audit passes
baseline implementations are non-trivial
compute budgets are logged
negative result protocol is active
```

---

## 18. Ablation Budget Planning

Ablations dominate compute. 따라서 ablation을 3 tiers로 나눈다.

### 18.1 Critical Ablations

| Ablation | Required Before Paper Claim? | Why |
|---|---|---|
| no-control-grammar | YES | core novelty |
| merged regime-control grammar | YES | factorization defense |
| collapsed latent | YES | latent factorization defense |
| no-falsification | YES | falsification novelty |
| uncertainty instead of falsification | YES | gate distinction |
| no alternative hypothesis | YES | alternative rollout claim |
| random alternative | YES | proposer quality |
| no rollout | YES | world model planning claim |
| no rewrite | YES | action-interface claim |
| always-plan | YES | compute gate claim |
| verifier-only | YES | verification threat |
| next-state-WM-only | YES | generic WM threat |

### 18.2 Important Ablations

| Ablation | Purpose |
|---|---|
| no L_progress | reward/progress contribution |
| no L_action_effect | effect prediction contribution |
| no valid switch reward | switch reward contribution |
| no compute penalty | overplanning control |
| horizon=1/3/5 | rollout sensitivity |
| top-k=1/3/5 | proposal sensitivity |
| DOM-only vs hybrid | modality contribution |

### 18.3 Optional / Appendix Ablations

| Ablation | Use |
|---|---|
| 72B inference-only base | strong base check |
| real benchmark auxiliary | external validity |
| large DATA-T5 scaling | scaling appendix |
| H100 vs A100 speed comparison | engineering appendix |
| alternative visual encoder | modality robustness |

---

## 19. Stop / Go / Kill Criteria

| Gate ID | Stage | Go Condition | Stop/Kill Condition | Action |
|---|---|---|---|---|
| GATE-11-001 | P0 schema | no hidden label leakage | any hidden/counterfactual in agent input | fix schema |
| GATE-11-002 | P1 text-only | core ablations collapse | no-grammar/no-falsification no effect | revise problem/taxonomy |
| GATE-11-003 | P2 multimodal sanity | effect/falsification above trivial baselines | model learns shortcuts only | fix data/sampling |
| GATE-11-004 | P3 3B MVE | beats verifier/uncertainty on mechanism metrics | verifier-only or uncertainty equal | revise method |
| GATE-11-005 | P4 7B main | ID+OOD gains under compute-matched eval | gains only from more compute | revise gate/baselines |
| GATE-11-006 | P5 ablation | critical ablations degrade expected metrics | no-control-grammar/no-falsification no effect | weaken/drop claim |
| GATE-11-007 | P6 real auxiliary | weak external support | real fails completely | keep synthetic-only limitation |
| GATE-11-008 | P7 scaling | trend improves with scale | no scale benefit | no scaling appendix |

---

## 20. Risk Ledger

| Risk ID | Risk | Trigger | Mitigation | If Unresolved |
|---|---|---|---|---|
| RISK-11-001 | data too success-heavy | low failed/recovery ratios | enforce transition ratio | falsification unreliably learned |
| RISK-11-002 | wrong-current rare event | low positive labels | balanced sampling | L_falsification collapses |
| RISK-11-003 | hidden label leakage | fields in agent observation | runtime assertion | experiment invalid |
| RISK-11-004 | VLM overkill | starting at 7B | text-only/3B gates | wasted budget |
| RISK-11-005 | pixel storage explosion | raw screenshots only | compressed images + cached embeddings | storage bottleneck |
| RISK-11-006 | compute budget explosion | too many ablations | tiered ablation plan | incomplete evaluation |
| RISK-11-007 | no-control-grammar no effect | ablation result | weaken/drop grammar claim | core novelty damaged |
| RISK-11-008 | verifier-only matches | baseline result | revise falsification/rewrite | novelty weak |
| RISK-11-009 | uncertainty gate matches | baseline result | revise VOC gate | compute claim weak |
| RISK-11-010 | next-state-WM matches | baseline result | strengthen grammar-specific OOD | WM novelty weak |
| RISK-11-011 | 3B works but 7B not better | scale result | report scale limitation | model scaling claim not made |
| RISK-11-012 | 7B too expensive | budget | freeze/cache/LoRA | reduce to 3B paper claim |
| RISK-11-013 | image modality unnecessary | DOM-only equals hybrid | drop screenshot claim | simplify architecture |
| RISK-11-014 | real benchmark weak | hidden labels absent | auxiliary only | no real-world core claim |
| RISK-11-015 | loss complexity | too many losses | main6-first staged training | reviewer confusion |

---

## 21. Implementation Contract for Claude Code

Claude Code가 이 파일을 사용해 구현할 때는 아래 순서로 작업해야 한다.

```text
1. Build DATA-T0/T1 text-only generator.
2. Train MODEL-T0.
3. Run P1 metrics and critical ablations.
4. If P1 passes, build synthetic Web/GUI generator with schema assertions.
5. Generate DATA-T2.
6. Train frozen-feature MVE.
7. If leakage-free and above baseline, generate DATA-T3.
8. Train frozen Qwen2.5-VL-3B + FRCG heads.
9. Run core baselines and ablations.
10. Only then plan DATA-T4 + Qwen2.5-VL-7B run.
```

Claude Code must not:

```text
- jump directly to 7B training,
- remove no-control-grammar ablation,
- skip verifier-only baseline,
- skip compute logging,
- use hidden labels at inference,
- scale data before leakage audit,
- claim main-track evidence from MVE.
```

---

## 22. Handoff to Future Files

| Handoff ID | Target File | What Must Be Used | What Must Be Verified |
|---|---|---|---|
| H11-001 | `12_MVE_IMPLEMENTATION_ROADMAP.md` | MODEL-T0/T2, DATA-T1/T3, P0~P3 gates | class/API/file structure |
| H11-002 | `13_TRAINING_RUNBOOK_AND_MONITORING.md` | memory techniques, loss stages, risk gates | training logs/alerts/kill conditions |
| H11-003 | `14_EXPERIMENT_EXECUTION_PLAN.md` | P4/P5 main/ablation budget | run order, seeds, compute logs |
| H11-004 | `FINAL_RESEARCH_BLUEPRINT.md` revision | scale and budget constraints | final claims remain conditional |

---

## 23. Quality Gate Result

| Gate ID | Gate | PASS/FAIL/PARTIAL | Evidence | If Not PASS |
|---|---|---|---|---|
| QG-11-01 | model tiers defined | PASS | MODEL-T0~T5 | 없음 |
| QG-11-02 | dataset tiers defined | PASS | DATA-T0~T6 | 없음 |
| QG-11-03 | distribution coverage ratios defined | PASS | §9 | 없음 |
| QG-11-04 | OOD coverage matrix included | PASS | §10 | 없음 |
| QG-11-05 | GPU resource tiers included | PASS | §12 | 없음 |
| QG-11-06 | cost formula included | PASS | §13 | 없음 |
| QG-11-07 | MVE-0 and MVE-1 specified | PASS | §15~16 | 없음 |
| QG-11-08 | paper-main scale specified | PASS | §17 | 없음 |
| QG-11-09 | ablation budget tiered | PASS | §18 | 없음 |
| QG-11-10 | stop/go/kill gates included | PASS | §19 | 없음 |
| QG-11-11 | hidden label leakage prohibited | PASS | multiple sections | 없음 |
| QG-11-12 | no empirical results claimed | PASS | status + warnings | 없음 |
| QG-11-13 | external anchors included | PASS | §3 | 가격은 실행 전 재확인 필요 |
| QG-11-14 | Claude Code implementation contract included | PASS | §21 | 없음 |

---

## 24. Final Statement

`11_MODEL_DATASET_SCALE_AND_TRAINING_BUDGET.md`는 empirical result 파일이 아니다. 이 파일은 FRCG-WM의 모델 크기, 데이터셋 규모, 분포 커버리지, 학습 자원, 비용, 중단 조건을 정량화한 scale/budget contract다.

가장 중요한 결론은 다음이다.

```text
Do not start with a large VLM.

The correct order is:
text-only smoke
→ frozen 3B VLM MVE
→ 7B frozen/QLoRA paper-main
→ optional large-model/real-benchmark auxiliary validation.
```

실험 claim은 다음 조건을 통과해야만 강화된다.

- no-control-grammar ablation이 무너져야 한다.
- no-falsification ablation이 무너져야 한다.
- verifier-only보다 recovery delay가 좋아야 한다.
- uncertainty-gated보다 progress per compute가 좋아야 한다.
- next-state-WM-only보다 OOD-control grammar shift에서 좋아야 한다.
- hidden label leakage가 없어야 한다.
- compute-matched evaluation이 있어야 한다.
- MVE 결과만으로 main-track claim을 주장하면 안 된다.

Next required file:

```text
12_MVE_IMPLEMENTATION_ROADMAP.md
```
