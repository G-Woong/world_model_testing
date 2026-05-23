# FGLC_FAILURE_TAXONOMY — Failure Cause Taxonomy (Enum-ID 20종)

> **Source**: `docs/EXPERIMENT_REPAIR_LOOP_PLAN.md` §D.2 + 각 cause별 source MD 인용
> **Runtime consumer**: `src/fglc/repair/taxonomy.py` (Python Enum + threshold dict)
> **Status**: v0 (2026-05-23) — closed-loop repair harness Step 1 산출물

---

## 목적

4축 metric(ID NLL / OOD AUROC / nec-suf / return)이 gate threshold에 미달했을 때
자동 진단 모듈(`src/fglc/repair/diagnose.py`)이 cause-id 후보 집합을 산출하기 위한
**형식화된 실패 원인 분류 체계**다.

각 cause-id는:
1. SCREAMING_SNAKE_CASE 식별자
2. 의미 (1문장)
3. 1차 detection signal (수치 threshold)
4. source MD 인용

의 4-tuple로 정의된다.

---

## 전제

- 모든 detection signal은 동일 eval split(`PickCube/id`, `PickCube/ood_mass` 등)에서 측정된 metric artifact를 기반으로 한다.
- detection signal은 FAIL 의심이지 확진이 아니다 — 복수 cause가 동시 점화될 수 있다.
- 조기 단계(R3 이전)에서는 `ATTENTION_*` / `CORRECTION_*` / `PLANNER_*` cause는 관련 모듈이 없으므로 점화 대상에서 제외된다.

---

## Enum-ID 정의표

| # | ID | 의미 | 1차 detection signal | source MD |
|---|---|---|---|---|
| 1 | `DATA_TOO_SMALL` | episode 수 부족으로 NLL 분산이 큼 | `NLL_std / NLL_mean > 0.3` (epoch-end eval) | `docs/idea/18_DATA_BENCHMARKS.md` |
| 2 | `DATA_BAD_SPLIT` | ID/OOD overlap 또는 OOD가 ID와 동일 분포 | `|OOD_NLL − ID_NLL| < 0.05 nat` (1-step, 동일 task) | `docs/ROADMAP/03_PHASE_R2_DATA_PIPELINE.md:L42` |
| 3 | `OOD_TOO_HARD` | OOD shift가 너무 극단적 — 모델이 전혀 일반화 못 함 | `OOD_NLL − ID_NLL > 2.0 nat` | `docs/idea/18_DATA_BENCHMARKS.md` |
| 4 | `OOD_TOO_EASY` | OOD shift가 ID와 거의 같음 — 유의미한 shift 없음 | `OOD_NLL − ID_NLL < 0.05 nat` | `docs/idea/12_TRAINING_STAGES.md:L67-68` |
| 5 | `MODEL_UNDERCAPACITY` | 모델 용량 부족 — train loss가 정체 | `train_NLL ≥ val_NLL` 또는 `train_NLL > 0.5 nat` 정체 ≥ 10 epoch | `docs/idea/23_FAILURE_MODES.md` (실패 1 역) |
| 6 | `MODEL_OVERCAPACITY` | 과적합 — train↓ val↑ 발산 | `val_NLL − train_NLL > 0.3 nat` | `docs/idea/23_FAILURE_MODES.md` |
| 7 | `LATENT_GROUP_TOO_SMALL` | K 부족 — 다양한 이동 유형 표현 불가 | 그룹 간 cosine similarity 중앙값 > 0.85 (그룹 collapse 징후) | `docs/idea/03_LATENT_DECOMPOSITION.md:C8` |
| 8 | `LATENT_DIM_TOO_SMALL` | per-group d 부족 — 재구성 오차 상한선 초과 | `reconstruction_mse > baseline_reconstruction_mse × 1.5` | `docs/idea/03_LATENT_DECOMPOSITION.md` |
| 9 | `HORIZON_TOO_SHORT` | 학습 horizon으로 OOD 누적 오차 신호를 못 잡음 | k-step NLL이 k=1..T 전체에서 평탄 (기울기 < 0.01 nat/step) | `docs/idea/04_BASE_WORLD_MODEL.md` |
| 10 | `HORIZON_TOO_LONG` | 너무 긴 horizon으로 누적 오차 폭주 | k-step NLL이 exponential 증가 (k≥4에서 배증) | `docs/idea/04_BASE_WORLD_MODEL.md` |
| 11 | `LOSS_IMBALANCE` | objective_weights 한쪽이 폭주 — 다른 objective가 무시됨 | 특정 loss component가 전체 loss의 > 80% 점유 또는 log 발산 | `docs/idea/10_LOSS_DESIGN.md` |
| 12 | `SIGMA_CALIBRATION_FAILURE` | 예측 σ_t가 경험적 std 대비 2배 이상 과대/과소 추정 | `ECE > 0.2` (calibration error, 10-bin) | `docs/idea/23_FAILURE_MODES.md:L39` + `docs/ROADMAP/05_PHASE_R4_FALSIFICATION_GATE.md:L38-39` |
| 13 | `BETA_GATE_COLLAPSE` | β_t가 항상 0 또는 항상 1로 이분화 — gate 동작 불능 | `mean(β_t) < 0.05` 또는 `mean(β_t) > 0.95` | `docs/idea/23_FAILURE_MODES.md` (실패 5 변형) |
| 14 | `ATTENTION_COLLAPSE` | α가 한 group에 집중 또는 uniform — sparse correction 무력화 | `entropy(α_t) < 0.1` (과집중) 또는 `entropy(α_t) > 0.95 × log(K)` (uniform) | `docs/idea/23_FAILURE_MODES.md` (실패 2) + `docs/idea/06_CAUSAL_ATTENTION.md` |
| 15 | `CORRECTION_TOO_WEAK` | δ 크기 ≈ 0 — correction이 dynamics에 영향 없음 | `mean(||δ||) < 0.01` | `docs/idea/23_FAILURE_MODES.md` (실패 1 역) + `docs/idea/07_CORRECTION_MECHANISM.md` |
| 16 | `CORRECTION_TOO_LARGE` | δ가 δ_max bounding을 자주 hit — 보정이 과도함 | `||δ|| ≥ 0.9 × δ_max` 비율 > 30% of steps | `docs/idea/23_FAILURE_MODES.md` (실패 1) + `docs/idea/07_CORRECTION_MECHANISM.md` |
| 17 | `PLANNER_BUDGET_TOO_LOW` | rollout 개수 부족 — return 추정 분산이 큼 | return std > return mean × 0.5 (3 seed 단위) | `docs/idea/11_PLANNING_THEORY.md:C4` |
| 18 | `EVAL_NOISE_HIGH` | seed 간 분산이 effect 크기보다 큼 — 유의미한 비교 불가 | 95% CI 폭 > effect 크기 (Δ metric 절댓값) | `docs/idea/21_METRICS.md` |
| 19 | `BASELINE_MISMATCH` | baseline 코드가 spec(`19_BASELINES.md`)과 다름 | baseline NLL이 ID에서도 비정상적으로 낮거나 높음 (> 2σ from expected) | `docs/idea/19_BASELINES.md` |
| 20 | `IMPLEMENTATION_BUG_SUSPECTED` | 위 19개 cause 어디에도 해당하지 않는 이상 동작 | catch-all — 진단 불가 상태. blocker 보고 + 수동 점검 필요 | — |

---

## Detection Signal 상세 정의

### NLL 관련

```
NLL_1step  = E[-log p_θ(z_{t+1} | z_t, a_t, h_t)]           # 1-step prediction
NLL_kstep  = (1/k) Σ_{i=1}^{k} NLL_1step@i                  # k-step average
OOD_NLL    = NLL_1step on OOD eval split
ID_NLL     = NLL_1step on ID eval split
```

### AUROC 관련

```
AUROC      = roc_auc_score(regime_shifted_label, β_t)        # OOD detection
ECE        = Σ_b |mean_β_b - mean_conf_b| / n_bins           # calibration error (10 bins)
```

### Correction 관련

```
δ_norm     = mean over eval steps of ||δ_t||                 # correction magnitude
δ_max      = tanh bounding 상한 (config에서 설정)
α_entropy  = entropy(softmax(α_t))                           # attention entropy
β_mean     = mean(β_t over eval steps)                       # gate activation rate
```

### Planner 관련

```
return_std = std of episode return over eval seeds
return_mean = mean of episode return over eval seeds
n_rollout   = MPPI candidate count (default 512 per docs/idea/11_PLANNING_THEORY.md:C4)
```

---

## Cause → Phase 적용 가능성

| Phase | 적용 가능 cause-id |
|---|---|
| R2 (data pipeline) | DATA_TOO_SMALL, DATA_BAD_SPLIT, OOD_TOO_HARD, OOD_TOO_EASY |
| R3 (base world model) | MODEL_UNDERCAPACITY, MODEL_OVERCAPACITY, LATENT_GROUP_TOO_SMALL, LATENT_DIM_TOO_SMALL, HORIZON_TOO_SHORT, HORIZON_TOO_LONG, LOSS_IMBALANCE, EVAL_NOISE_HIGH, IMPLEMENTATION_BUG_SUSPECTED |
| R4 (falsification gate) | SIGMA_CALIBRATION_FAILURE, BETA_GATE_COLLAPSE, EVAL_NOISE_HIGH, IMPLEMENTATION_BUG_SUSPECTED |
| R5 (causal attention) | ATTENTION_COLLAPSE, EVAL_NOISE_HIGH, IMPLEMENTATION_BUG_SUSPECTED |
| R6 (correction) | CORRECTION_TOO_WEAK, CORRECTION_TOO_LARGE, IMPLEMENTATION_BUG_SUSPECTED |
| R7 (planner) | PLANNER_BUDGET_TOO_LOW, EVAL_NOISE_HIGH, IMPLEMENTATION_BUG_SUSPECTED |
| R9 (ablation) | BASELINE_MISMATCH, EVAL_NOISE_HIGH |
| R10 (baselines) | BASELINE_MISMATCH, EVAL_NOISE_HIGH |

---

## 참조

- runtime Enum 구현: `src/fglc/repair/taxonomy.py`
- 진단 점화 로직: `src/fglc/repair/diagnose.py`
- metric → cause 매핑 테이블: `docs/EXPERIMENT_REPAIR_LOOP_PLAN.md` §D.3
- 실험 ledger: `docs/EXPERIMENT_LEDGER_SCHEMA.md`
