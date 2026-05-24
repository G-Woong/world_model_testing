# FGLC R4 FALSIFICATION GATE Plan — standardized residual + conformal calibration + β_t gate

> **Status**: PLAN (Phase 1 read-only audit + Phase 3 user clarification 완료, ExitPlanMode 승인 대기)
> **Branch**: `memory-redesign-2026-05-16`
> **Date**: 2026-05-24
> **Supersedes**: 직전 R3 SMOKE EXECUTION plan (closure commit `4b3b8c0` 완료)
> **Authority**: 사용자 메시지 "R4 FALSIFICATION GATE — standardized residual + conformal calibration + β_t gate"
> **Predecessor artifacts**: `reports/R3_SMOKE_CLOSURE_REPORT.md` (R3 finding), `docs/FUTURE_OOD_DATA_EXPANSION_INSIGHTS.md` (easy-looking OOD)

---

## Context — 왜 R4가 필요한가

### R3 closure에서 닫힌 사실 (reports/R3_SMOKE_CLOSURE_REPORT.md §E + §G)

- PickCube/PushCube R3 base WM 학습은 PASS (`id_nll = -0.16 / -1.20`).
- 그러나 `ood_friction_nll` 및 `ood_gain_nll`가 `id_nll`보다 **더 음수** (역전).
  - PickCube: gain Δ = −0.131, friction Δ = −0.084
  - PushCube: gain Δ = −0.050, friction Δ = −0.011
- 원인은 **transition magnitude 축소(physics)** 확증 — gain=0.7에서 ID 1.305 → OOD 0.924 (−29%), friction=5.0에서 ID → OOD −10%.
- wiring bug H1~H3 모두 기각 (4 split hash 상이, dataloader split→h5 매핑 직접 검증, mass axis는 magnitude 변화 없어 역전 약함).
- 결론: **raw Gaussian NLL은 transition magnitude 축소형 easy-looking OOD를 탐지하지 못한다**.

### R4의 핵심 질문 (사용자 명시)

> "raw NLL이 놓친 OOD를 standardized residual + conformal β_t gate가 탐지할 수 있는가?"

`02_FALSIFICATION_THEORY.md §B-C`의 수식:

```
ρ_t^k = (z_{t+1}^k − μ_t^k) / σ_t^k                  # group별 standardized residual
F_t^k = ||ρ_t^k||₂²                                  # χ²_d under H0
F_t   = Σ_k F_t^k                                    # χ²_{K·d} under H0
τ     = empirical (1−α)-quantile of F_t on ID        # conformal threshold (σ̂ 비의존)
β_t   = sigmoid(MLP([F_1,…,F_K, F_t, h_t]))         # gate output ∈ (0,1)
```

### Phase 1 audit 결과 — 구조적 호환성 (POSITIVE)

3 Explore agent 병렬 audit (Agent A: model μ/Σ, Agent B: repair/metrics/ledger, Agent C: 이론+R3 closure):

| # | 항목 | 실측 | 비고 |
|---|---|---|---|
| 1 | `src/fglc/models/dynamics.py:32,46-47` | `mu, log_sigma = self.head(...).chunk(2, dim=-1)` — **이미 diagonal Gaussian σ_t export** | 추가 covariance head 불필요 |
| 2 | latent shape | `K=6, d=32, h_dim=128` → `ρ_t ∈ R^{B×T×6×32}` | 메모리 부담 무시 가능 |
| 3 | `src/fglc/training/trainer_r3.py` `torch.save` | **0건** | R4 frozen weight 검증 위해 save/load 추가 필수 |
| 4 | `Evaluator.evaluate` (`src/fglc/evaluation/metrics.py:44-77`) | metric scalar dict만 반환, **per-step residual 미노출** | `evaluate_residuals` 메서드 추가 필요 |
| 5 | `src/fglc/repair/taxonomy.py:26-27` | `SIGMA_CALIBRATION_FAILURE` + `BETA_GATE_COLLAPSE` 이미 R4 cause로 정의 | 재사용 가능 |
| 6 | `src/fglc/repair/candidates.py:82-115` | `calibration_loss_weight`, `beta_reparameterize`, `beta_prior_scale` patch 이미 등록 | R4용 추가 patch 신설 시 같은 패턴 |
| 7 | `src/fglc/repair/diagnose.py:10-32` `CANONICAL_METRIC_KEYS` | 18 key, `beta_mean`, `ece`, `ood_auroc` 이미 포함 | R4 metric은 frozenset 확장만 필요 |
| 8 | `src/fglc/repair/ledger.py:17-37` REQUIRED_KEYS | 19개, `metrics_before/after`는 dict | R4 metric은 dict 내부 추가만으로 충분 |
| 9 | `scripts/fglc/r3_smoke.py:38` `choices=["R2..R7"]` | R4 분기 이미 허용 | 새 runner 주입 패턴 사용 |
| 10 | `src/fglc/data/dataloader.py:120-127` | `test_id` split이 이미 로딩되지만 `Evaluator.evaluate`(line 44)는 사용 안 함 | **calibration split으로 즉시 재사용** |
| 11 | `src/fglc/schemas/visibility.py:18-31` FORBIDDEN_AGENT_FIELDS | 12개 — R4 input은 `ρ_t`(model 파생) + `h_t`(belief) → **금지 필드 위반 위험 0** | |
| 12 | `outputs/repair/{pickcube,pushcube}_r3_2axis_2026-05-24/iter_0/` | `.pt`/`.ckpt` **0건** | R3 minimal rerun 필요 |
| 13 | `.gitignore:47` | `outputs/*` 차단 | R4 artifact는 force-add 또는 `outputs/eval_reports/` 사용 결정 |

### Phase 3 user clarification (이번 세션)

| 결정점 | 사용자 응답 |
|---|---|
| Conformal calibration split | **test_id 전체 사용** (PickCube 50ep / PushCube 100ep) |
| 양방향(gain=0.7+1.3) 평가 범위 | **단방향만**(gain=0.7 + friction=5.0); gain=1.3 readiness는 §L next step으로 분리 |
| R3 checkpoint 정책 | **(plan default)** trainer_r3.py에 `save_state()` 추가 + R4 entry 시 R3 minimal rerun 1회 (5 epoch, ~2초/task). R3 closure artifact 무손, R4용 별도 디렉토리에 model.pt 생성 |
| R4 PASS gate 기준 | **(plan default)** R3 closure §H.3 제안값 채택: AUROC≥0.85 (friction OR gain), FPR≤0.05, raw NLL 대비 AUROC gain ≥+0.20 |

> default 2건은 사용자가 plan 검토 시 변경 가능. ExitPlanMode 전 명시.

### 이론적 강제 조건 (must-have)

| 코드 | 조건 | 출처 |
|---|---|---|
| M1 | group별 `ρ_t^k = (z_{t+1}^k−μ_t^k)/σ_t^k` | `02_FALSIFICATION §B` |
| M2 | ID empirical (1−α)-quantile conformal threshold | `02 §C5`, R3 closure §H.2-2 |
| M3 | signed residual + magnitude **양방향 feature** (구현, 평가는 단방향) | R3 closure §H.2-1 |
| M4 | sequential aggregation (CUSUM/SPRT-like window) | R3 closure §H.2-3 |
| M5 | R3 weights freeze | `12_TRAINING_STAGES §Stage 2` |
| M6 | regime_id/ood_type/seed/template_id model input 금지 | `18_DATA_BENCHMARKS`, `visibility.py:18-31` |
| M7 | σ floor (clamp) + ECE 측정 | `02 §C8` |
| M8 | ablation: no-conformal (hard threshold) | `02 §C7` |

### UNKNOWN (plan 진행 중 closing)

- conformal α 정확 값: `02 §78` "1000개 ID 궤적" 권고만 있음, 정량 α=0.05 default 채택 (사용자 reject 시 수정)
- R4 = Stage 2 전체인지 β-gate-only인지: `12_TRAINING_STAGES`에 R-번호 매핑 없음 → **R4 = β-gate-only** 해석 채택 (causal attention/correction은 R5/R6로 분리, R3 closure §L에서도 동일 분리)

### 본 plan의 의도된 결과

1. **Stage 2**: trainer_r3.py에 minimal `save_state/load_state` 추가, `Evaluator.evaluate_residuals` 신설 (R3 model API 호환 유지)
2. **Stage 3**: `src/fglc/falsification/` 새 패키지 — residuals.py + conformal.py + gate.py
3. **Stage 4**: tests 7종 추가 + 기존 4 tests regression PASS
4. **Stage 5**: R3 minimal rerun(checkpoint 생성) → R4 smoke 실행 (PickCube + PushCube 각 1회)
5. **Stage 6**: metric 분석 + R4 PASS/PATCH_REQUIRED/BLOCKED 판정
6. **Stage 7**: 실패 시 repair loop (max 3 iter)
7. **Stage 8**: 보고서 + commit (R4.passed sentinel은 사용자 명시 승인 시에만 생성)

---

## Stage 흐름

```
Stage 0: R4 entry audit (read-only, ~10 min)
   ↓ R3.passed 보존 / R4.passed 부재 / model μ/Σ 가용 확인
Stage 1: R4 algorithm design closure (~10 min, 본 plan §"R4 Algorithm"에서 확정)
   ↓
Stage 2: trainer_r3 save/load + Evaluator.evaluate_residuals (~45 min)
   ↓ R3 회귀 tests PASS
Stage 3: falsification 패키지 구현 (~90 min)
   ↓ residuals/conformal/gate 3 파일 + 단위 tests
Stage 4: R4 tests 작성 (~30 min)
   ↓ 7 신규 + 4 기존 PASS
Stage 5: R3 minimal rerun + R4 smoke 실행 (~30 min, 2 task × 2 run)
   ↓ metrics.json + ledger.jsonl 생성
Stage 6: metric 분석 + 1차 판정 (~20 min)
   ↓ PASS / PATCH_REQUIRED / BLOCKED
Stage 7: repair loop (조건부, 최대 3 iter, ~0~90 min)
   ↓ diagnose → candidate → patch → rerun → compare
Stage 8: 보고서 + commit (~30 min)
```

**총 wall-clock**: 약 4~6 hour (실패 없을 시 ~4 hour)
**GPU**: RTX 4060 Ti 8 GB (R3 inference만, ~수백 MiB)
**raw HDF5 변경**: 0 (절대 보존)
**R3.passed 변경**: 0 (이미 존재, 건드리지 않음)
**예상 commit**: 3개 (Stage 2+3 / Stage 4 / Stage 8)

---

## R4 Algorithm (확정)

### A. Residual (M1, M7)

```python
# src/fglc/falsification/residuals.py
def standardized_residual(z_next, mu, log_sigma, sigma_floor=1e-3):
    """
    z_next, mu, log_sigma: (B, T, K, d)
    returns rho: (B, T, K, d) — element-wise (z_next − μ) / σ
    """
    sigma = torch.exp(log_sigma).clamp_min(sigma_floor)
    return (z_next - mu) / sigma
```

### B. Group falsification scores

```python
def group_falsification_scores(rho):
    """rho: (B, T, K, d) → F_per_group: (B, T, K)  = ||rho_k||₂²"""
    return (rho ** 2).sum(dim=-1)

def total_falsification_score(F_per_group):
    """F_per_group: (B, T, K) → F_total: (B, T)"""
    return F_per_group.sum(dim=-1)
```

### C. Conformal threshold (M2)

```python
# src/fglc/falsification/conformal.py
def fit_threshold(scores_id, alpha=0.05):
    """scores_id: (N_ID,) flat → returns scalar tau = (1−α) quantile"""
    return torch.quantile(scores_id, 1.0 - alpha).item()

def fit_per_group_thresholds(F_per_group_id, alpha=0.05):
    """returns tau_per_k: (K,)"""
    flat = F_per_group_id.reshape(-1, F_per_group_id.shape[-1])  # (N*T, K)
    return torch.quantile(flat, 1.0 - alpha, dim=0)              # (K,)
```

### D. β_t gate (continuous score)

R4 단계에서는 **β_t를 MLP로 학습하지 않고 conformal-only**로 정의한다. 이유: (i) R3 closure의 PASS gate 기준이 AUROC 중심이라 continuous score만으로 충분, (ii) MLP 학습은 R5+ Stage 2 freeze 정책과 충돌, (iii) plan 단순화.

```python
# src/fglc/falsification/gate.py
def beta_t_continuous(F_total, tau):
    """β_t = sigmoid((F_total − τ) / s)  with adaptive scale s = τ / 4"""
    s = max(tau / 4.0, 1e-6)
    return torch.sigmoid((F_total - tau) / s)             # (B, T)

def beta_t_boolean(F_total, tau):
    """β_t boolean = (F_total > τ)"""
    return (F_total > tau).float()
```

> NOTE: M3 (signed feature) 구현은 `residuals.py`에 `signed_residual_mean(rho)` (per-group mean across d)와 `directional_bias_score(rho)` 함수로 별도 export. **이번 R4 평가에서는 evaluator metric에 포함만 하고 단방향 AUROC 비교에만 사용**. gain=1.3 데이터 readiness 후 R5/별도 phase에서 양방향 평가 정식 수행 (§L).

### E. Sequential aggregation (M4)

```python
# src/fglc/falsification/gate.py
def cusum_score(F_t_seq, tau, window=8):
    """CUSUM-like: S_t = max(0, S_{t-1} + (F_t − τ)). Returns full sequence."""
    excess = F_t_seq - tau                                # (B, T)
    S = torch.zeros_like(excess)
    S[:, 0] = excess[:, 0].clamp_min(0)
    for t in range(1, F_t_seq.shape[1]):
        S[:, t] = (S[:, t-1] + excess[:, t]).clamp_min(0)
    return S                                              # (B, T)
```

### F. R4 metric schema (Evaluator 확장)

`STAGE2_CANONICAL_METRIC_KEYS` 신설 (별도 frozenset, STAGE1 유지) (`src/fglc/evaluation/metrics.py`):

```
beta_t_auroc_friction     # AUROC over (ID test_id + ood_friction)
beta_t_auroc_gain         # AUROC over (ID test_id + ood_gain)
beta_t_fpr_id             # FPR on test_id at conformal threshold
beta_t_tpr_friction       # TPR on ood_friction
beta_t_tpr_gain           # TPR on ood_gain
conformal_threshold       # scalar τ
residual_ece              # σ calibration ECE on test_id
raw_nll_auroc_friction    # baseline: raw NLL score AUROC vs friction
raw_nll_auroc_gain        # baseline: raw NLL score AUROC vs gain
```

`CANONICAL_METRIC_KEYS` (`src/fglc/repair/diagnose.py:10-32`)에도 동일 9 key 추가 (failed_metric 가드 통과 위함).

### G. Comparison vs raw NLL baseline (사용자 명시: 같은 episode/split)

R4 smoke는 같은 forward pass에서:
- `raw_nll_id`, `raw_nll_friction`, `raw_nll_gain` (기존 metric)
- `beta_t_auroc_friction`, `beta_t_auroc_gain` (신규)
- baseline AUROC: raw NLL score를 OOD vs ID에 적용한 AUROC

같은 trajectory, 같은 model snapshot, 같은 split에서 두 score 모두 계산하여 공정 비교.

---

## Stage 0 — R4 entry audit (read-only)

### 체크리스트

1. `git status --short` clean (uncommitted noise 0)
2. branch = `memory-redesign-2026-05-16`
3. `outputs/phase_gates/R0~R3.passed` 4개 존재 (zero-byte)
4. `outputs/phase_gates/R4.passed` **부재** 확인
5. raw HDF5 12개 mtime 기록 (Stage 끝마다 비교)
6. `reports/R3_SMOKE_CLOSURE_REPORT.md` 존재
7. `docs/FUTURE_OOD_DATA_EXPANSION_INSIGHTS.md` 존재
8. `outputs/repair/{pickcube,pushcube}_r3_2axis_2026-05-24/iter_0/metrics.json` 존재 (R4 sanity 비교용)
9. `src/fglc/models/dynamics.py:46-47`에서 `(mu, log_sigma)` 둘 다 return 재확인

### Stage 0 PASS 조건
9개 항목 모두 expected. 격차 시 plan 갱신 후 재진입.

---

## Stage 1 — R4 algorithm design closure

본 plan §"R4 Algorithm"을 design SoT로 채택. 별도 design 문서 생성 없음 (사용자 명시: "필요 시 docs/R4_FALSIFICATION_GATE_DESIGN_NOTES.md" → R4 report 내부 §D-F에서 통합 기술).

---

## Stage 2 — R3 model API 호환 확장

### 2A. `src/fglc/training/trainer_r3.py` 수정 (~20 LOC)

```python
def save_state(self, path: Path) -> None:
    """Save encoder/belief/dynamics/heads state_dict for R4 frozen reuse."""
    torch.save({
        "encoder": self.encoder.state_dict(),
        "belief": self.belief.state_dict(),
        "dynamics": self.dynamics.state_dict(),
        "reward_head": self.reward_head.state_dict(),
        "value_head": self.value_head.state_dict(),
        "config_hash": self._config_hash,
    }, path)

def load_state(self, path: Path, freeze: bool = True) -> None:
    """Load checkpoint, freeze for R4."""
    ckpt = torch.load(path, map_location=self.device)
    self.encoder.load_state_dict(ckpt["encoder"])
    # ... (각 module load + .requires_grad_(False) for freeze)
```

### 2B. `src/fglc/evaluation/metrics.py::Evaluator` 확장 (~40 LOC)

기존 `evaluate` 시그니처 변경 없음. 새 메서드 추가:

```python
@torch.no_grad()
def evaluate_residuals(self, dataloader, model) -> dict[str, Tensor]:
    """
    Returns:
      rho_per_group: (N_total_steps, K, d)   standardized residuals
      F_per_group:   (N_total_steps, K)      group falsification scores
      F_total:       (N_total_steps,)        total falsification score
      raw_nll_step:  (N_total_steps,)        per-step Gaussian NLL for baseline
    """
    # 기존 _evaluate_nll와 동일한 forward 패턴, 단 residual 텐서 누적
```

### 2C. `STAGE2_CANONICAL_METRIC_KEYS` 신설

`tests/test_fglc_r3_runner_maniskill.py:177`의 `test_evaluate_model_produces_canonical_keys`는 STAGE1 검증만 — 변경 없음. R4 runner는 STAGE2 set으로 검증.

### 2D. Stage 2 검증

```powershell
& .venv\Scripts\python.exe -m pytest -q `
    tests/test_fglc_r3_runner_maniskill.py `
    tests/test_fglc_forbidden_field_sync.py `
    tests/test_fglc_split_integrity.py `
    tests/test_fglc_config_manifest_consistency.py
```

PASS 조건: 회귀 0건, 기존 R3 metric 정확히 동일 값 (deterministic seed 검증).

### T-trigger
- T3 fglc-code-reviewer (compact): trainer_r3.py + metrics.py 수정 후

### Stage 2 commit (Stage 3과 묶기 권장 — 단독으로는 fragment)
참조: Stage 3 commit message.

---

## Stage 3 — `src/fglc/falsification/` 패키지 구현

### 3A. `src/fglc/falsification/__init__.py`
```python
"""R4 falsification gate package.

References:
- docs/idea/02_FALSIFICATION_THEORY.md §B-C (standardized residual + conformal)
- reports/R3_SMOKE_CLOSURE_REPORT.md §H (R4 PASS gate proposal)
"""
from .residuals import standardized_residual, group_falsification_scores, total_falsification_score, signed_residual_mean, directional_bias_score
from .conformal import fit_threshold, fit_per_group_thresholds, ece
from .gate import beta_t_continuous, beta_t_boolean, cusum_score, auroc_from_scores
```

### 3B. `residuals.py` (~80 LOC)
- `standardized_residual(z_next, mu, log_sigma, sigma_floor=1e-3)` (M1, M7)
- `group_falsification_scores(rho)`
- `total_falsification_score(F_per_group)`
- `signed_residual_mean(rho)` → (B, T, K), per-group signed mean across d (M3 양방향 feature)
- `directional_bias_score(rho)` → (B, T), Σ_k |E[ρ_k]| / √(Var[ρ_k]+ε)

### 3C. `conformal.py` (~60 LOC)
- `fit_threshold(scores_id, alpha)` (M2)
- `fit_per_group_thresholds(F_per_group_id, alpha)`
- `ece(rho_id, n_bins=10)` — diagonal Gaussian calibration ECE (M7)
- `coverage(F_total, tau)` → fraction of (F_total ≤ τ)

### 3D. `gate.py` (~70 LOC)
- `beta_t_continuous(F_total, tau)` (D)
- `beta_t_boolean(F_total, tau)` (D)
- `cusum_score(F_t_seq, tau, window=8)` (M4 sequential aggregation)
- `auroc_from_scores(scores_id, scores_ood)` — sklearn 미사용, torch native ranking

### 3E. `src/fglc/evaluation/falsification_metrics.py` (~120 LOC)

R4-specific metric aggregator:

```python
def compute_r4_metrics(
    eval_data: dict[str, dict],  # split → {rho, F_per_group, F_total, raw_nll_step}
    calibration_split: str = "test_id",
    alpha: float = 0.05,
) -> dict[str, float]:
    """Returns R4 metric dict matching STAGE2_CANONICAL_METRIC_KEYS."""
    # 1. fit tau from calibration split
    # 2. compute beta_t boolean on all splits
    # 3. compute AUROC for each OOD axis vs calibration ID
    # 4. compute FPR on calibration split
    # 5. compute TPR per OOD
    # 6. compute residual ECE
    # 7. compute raw NLL baseline AUROC for comparison
```

### 3F. `scripts/fglc/r4_falsification.py` (~150 LOC)

`r3_smoke.py`의 패턴 차용:
- CLI: `--phase R4 --config configs/fglc/r4_falsification_{pickcube,pushcube}.yaml --r3-checkpoint <path> --calibration-split test_id --alpha 0.05 --output-root outputs/r4_falsification/<task>`
- 흐름: (i) R3 checkpoint load, (ii) freeze, (iii) `Evaluator.evaluate_residuals` on 4 splits (test_id calibration / val_id eval / ood_friction / ood_gain), (iv) `compute_r4_metrics` 호출, (v) metrics.json + ledger.jsonl 작성

### 3G. `configs/fglc/r4_falsification_pickcube.yaml` 신설 (~50 LOC)
기존 `smoke_maniskill_pickcube.yaml`을 base로 하되 새 section 추가:

```yaml
falsification:
  alpha: 0.05                  # conformal FPR target
  sigma_floor: 1.0e-3          # σ clamp
  sequence_window: 8           # CUSUM window
  calibration_split: test_id
```

`configs/fglc/r4_falsification_pushcube.yaml` 동일 구조.

### 3H. `scripts/fglc/r3_export_checkpoint.py` (~80 LOC)
R3 minimal rerun(5 epoch) → `trainer.save_state(<output>)` → R4용 ckpt 파일 생성. R3 closure metrics는 건드리지 않음.

### T-trigger
- T3 fglc-code-reviewer (compact): falsification 패키지 전체

### Stage 2+3 commit (단일 atomic commit 권장)
```
feat(r4): add standardized residual conformal falsification gate

- trainer_r3: state save/load + frozen reuse hook
- evaluation/metrics: evaluate_residuals method + STAGE2_CANONICAL keys
- falsification/{residuals,conformal,gate}: M1-M4,M7 implementation
- evaluation/falsification_metrics: R4 metric aggregator
- scripts/fglc/r4_falsification.py + scripts/fglc/r3_export_checkpoint.py
- configs/fglc/r4_falsification_{pickcube,pushcube}.yaml
```

---

## Stage 4 — R4 tests

### 4A. `tests/test_fglc_falsification_residual.py` (~80 LOC)
- `test_standardized_residual_shape`: rho.shape == (B, T, K, d)
- `test_standardized_residual_finite`: NaN/Inf 0
- `test_sigma_floor_applied`: σ < floor → clamped
- `test_group_score_sum_equals_total`: Σ_k F^k == F_total

### 4B. `tests/test_fglc_falsification_conformal.py` (~60 LOC)
- `test_fit_threshold_id_only`: τ가 ID 데이터만으로 fit됨 (OOD 입력 시 ValueError 또는 docstring contract)
- `test_threshold_quantile_property`: τ를 적용한 ID FPR ≈ α (±2σ tolerance)
- `test_ece_diagonal_gaussian`: 잘 calibrated 한 σ에서 ECE ≈ 0

### 4C. `tests/test_fglc_falsification_gate.py` (~70 LOC)
- `test_beta_t_in_unit_interval`: 0 ≤ β_t ≤ 1
- `test_beta_t_boolean_threshold`: F > τ ⟺ boolean = 1
- `test_cusum_monotonic_under_drift`: CUSUM score grows under sustained drift

### 4D. `tests/test_fglc_r4_runner_maniskill.py` (~120 LOC)
- `test_r4_runner_loads_r3_checkpoint`: stub R3 ckpt + R4 runner 1-iter
- `test_r4_metrics_contain_all_canonical_keys`: STAGE2 키 9개 모두 present
- `test_r4_no_forbidden_field_in_input`: regime_id/ood_type/seed forbidden 검증

### 4E. `tests/test_fglc_falsification_leakage.py` (~50 LOC)
- conformal threshold가 OOD 데이터에서 fit되지 않음 (assertion 또는 explicit raise)
- regime_id가 R4 evaluator forward path에 들어가지 않음 (mock dataloader로 검증)

### 4F. `tests/test_fglc_falsification_repro.py` (~50 LOC)
- 같은 seed + 같은 checkpoint → 같은 τ, 같은 AUROC

### 4G. 기존 회귀
```powershell
& .venv\Scripts\python.exe -m pytest -q `
    tests/test_fglc_forbidden_field_sync.py `
    tests/test_fglc_split_integrity.py `
    tests/test_fglc_ood_severity.py `
    tests/test_fglc_r3_runner_maniskill.py `
    tests/test_fglc_falsification_*.py `
    tests/test_fglc_r4_runner_maniskill.py
```

PASS 조건: 기존 PASS + 신규 7 파일 (~17 tests) PASS.

### Stage 4 commit
```
test(r4): add 7 falsification gate test files (residual / conformal / gate / runner / leakage / repro)
```

---

## Stage 5 — R3 minimal rerun + R4 smoke 실행

### 5A. R3 checkpoint 생성 (R3 closure 무손)

```powershell
$pickCkptRoot = "outputs/r4_falsification/pickcube"
New-Item -ItemType Directory -Force -Path $pickCkptRoot | Out-Null

& .venv\Scripts\python.exe scripts/fglc/r3_export_checkpoint.py `
    --config configs/fglc/smoke_maniskill_pickcube.yaml `
    --seed 42 `
    --output $pickCkptRoot/r3_model.pt 2>&1 | Tee-Object -FilePath "$pickCkptRoot/r3_export.log"
```

PushCube 동일 (`outputs/r4_falsification/pushcube/`).

**원칙**: R3 minimal rerun은 **R3 closure metrics.json/ledger.jsonl을 건드리지 않는다**. R4 디렉토리에 독립 artifact 생성.

### 5B. R4 smoke 실행

```powershell
& .venv\Scripts\python.exe scripts/fglc/r4_falsification.py `
    --phase R4 `
    --config configs/fglc/r4_falsification_pickcube.yaml `
    --r3-checkpoint outputs/r4_falsification/pickcube/r3_model.pt `
    --calibration-split test_id `
    --alpha 0.05 `
    --seed 42 `
    --descriptor pickcube_r4_falsification `
    --output-root outputs/r4_falsification/pickcube 2>&1 | Tee-Object -FilePath outputs/r4_falsification/pickcube/r4_stdout.log
```

PushCube 동일.

### 5C. Artifact 확인 (per task)
- `outputs/r4_falsification/<task>/r3_model.pt`
- `outputs/r4_falsification/<task>/iter_0/metrics.json`
- `outputs/r4_falsification/<task>/iter_0/run_manifest.json`
- `outputs/r4_falsification/<task>/iter_0/config.yaml`
- `outputs/r4_falsification/<task>/loop_<id>/ledger.jsonl`
- `outputs/r4_falsification/<task>/r4_stdout.log`

### Stage 5 PASS 조건
- 두 task 모두 종료 코드 0
- artifact 6개 (per task) 모두 존재
- raw HDF5 mtime 변경 없음
- R3.passed sentinel 보존
- R3 closure metrics.json hash 변경 없음

### Stage 5 FAIL 분기
- OOM → batch_size 8 임시 yaml (R3 inference만이라 발생 가능성 낮음)
- import error → Stage 2-3 회귀
- R3 checkpoint 호환 실패 → trainer load_state 수정
- runner crash → stdout 분석 → Stage 7로

---

## Stage 6 — Metric 분석 + 1차 판정

### 6A. R4 metric 검증 표

| metric | 기대 | 점검 |
|---|---|---|
| `conformal_threshold` (τ) | finite, > 0 | json.load |
| `beta_t_fpr_id` | ≤ 0.05 + 2σ tolerance | conformal coverage |
| `beta_t_auroc_friction` | ≥ 0.85 (gate) | per task |
| `beta_t_auroc_gain` | ≥ 0.85 (gate) | per task |
| `beta_t_tpr_friction` | > 0.5 | informational |
| `beta_t_tpr_gain` | > 0.5 | informational |
| `residual_ece` | < 0.2 (M7) | σ calibration |
| `beta_t_auroc_*` − `raw_nll_auroc_*` | ≥ +0.20 | gate (R3 closure §H.3) |
| `vram_peak_mib` | < 6000 | ledger |
| forbidden field leak (stdout grep) | 0 | grep |

### 6B. 판정 매트릭스

| 결과 | 판정 |
|---|---|
| 양 task에서 β_t AUROC ≥ 0.85 (friction OR gain) AND FPR ≤ 0.05 + 2σ AND raw NLL 대비 +0.20 | **PASS** → Stage 8 |
| 한 task에서만 통과 또는 axis 한쪽만 통과 | **PARTIAL_PASS** → §L에 한계 명시 후 Stage 8 |
| β_t AUROC < raw NLL AUROC 또는 FPR > 0.10 | **PATCH_REQUIRED** → Stage 7 |
| residual NaN/Inf, 양 task 양 axis 모두 raw NLL과 동등 이하 | **BLOCKED** → Stage 8 보고만 |

### T-trigger
- T4 failure-interpretation-critic (deep): metric 분석 시
- T4 claim-metric-alignment-auditor (compact): PASS 판정 직전

---

## Stage 7 — Repair loop (조건부, max 3 iter)

### 7A. 진단 + 후보 적용

`src/fglc/repair/diagnose.py::diagnose(metrics, phase="R4")` 호출 시 R4 cause 자동 검출:
- `SIGMA_CALIBRATION_FAILURE` if `residual_ece > 0.2`
- `BETA_GATE_COLLAPSE` if `beta_t_fpr_id > 0.10` or `beta_t_auroc_* < 0.55`
- (신규 후보) `CONFORMAL_QUANTILE_MISMATCH` if `beta_t_fpr_id` ∉ [α/2, 2α]

### 7B. 실패 케이스별 대응

| # | 실패 | 진단 | 첫 candidate | 수정 범위 |
|---|---|---|---|---|
| 1 | residual NaN/Inf | sentinel IMPLEMENTATION_BUG | manual_blocker | sigma_floor 증가 또는 R3 ckpt log_sigma 분포 점검 |
| 2 | FPR >> α (false alarm 폭증) | SIGMA_CALIBRATION_FAILURE → CONFORMAL_QUANTILE_MISMATCH | sigma_floor 조정 (단 OOD 보지 않음) | falsification config |
| 3 | AUROC < raw NLL AUROC (β_t 열등) | (신규) BETA_GATE_DIRECTION_BLIND | signed_residual feature 가중치 증가, CUSUM window 변경 | falsification_metrics.py |
| 4 | gain AUROC만 낮음 (easy-looking 미탐) | (신규) EASY_LOOKING_OOD_MISSED | signed bias score 강화, magnitude-only → signed magnitude 조합 | gate.py |
| 5 | metrics.json 없음 | runner crash | n/a | stdout 분석 |
| 6 | forbidden field leak | n/a | immediate abort | input pipeline 수정 |

### 7C. Stop conditions
- max 3 iter 후 모든 metric 개선 없으면 USER_ESCALATION
- raw HDF5 mtime 변경 → immediate BLOCKED
- forbidden field leak → immediate BLOCKED
- R3 closure metrics.json hash 변경 감지 → immediate BLOCKED

### 7D. 사용자 명시 의무
"실패를 보고만 하고 끝내지 마라" — Stage 7은 진단→수정→재실행 루프 max 3회 시도하고, 모든 시도 실패해도 시도 기록을 보고서에 명시.

### T-trigger
- T3 implementation-risk-critic (compact): 패치 적용 후
- T4 failure-interpretation-critic (deep): 3회 시도 모두 실패 시

---

## Stage 8 — 보고서 + commit

### 8A. `reports/R4_FALSIFICATION_GATE_REPORT.md` (~250 LOC)

12 섹션:
A. Executive Summary (PASS / PARTIAL / PATCH / BLOCKED + 핵심 수치)
B. R3 finding recap (OOD NLL 역전)
C. raw NLL failure summary (per task per axis AUROC)
D. R4 algorithm (residual / conformal / β_t)
E. residual/conformal/β_t 구현 방식 (코드 발췌 + 파일 경로)
F. calibration split (test_id, N, α)
G. task/axis별 결과 (PickCube/PushCube × friction/gain × {AUROC, FPR, TPR, ECE})
H. raw NLL vs β_t 비교 표
I. easy-looking OOD 결과 (signed/CUSUM 효과)
J. failure/repair 기록 (Stage 7 iter별)
K. PASS/PARTIAL/PATCH/BLOCKED 판정 + 9 조건 표
L. 다음 단계: R4.passed sentinel 생성 승인 요청 / gain=1.3 데이터 readiness / R5 causal attention 진입 검토

### 8B. (선택) `docs/R4_FALSIFICATION_GATE_DESIGN_NOTES.md`
R4 보고서 §D-F에 통합 기술되므로 별도 생성 권장 안 함.

### 8C. `plans/PHASE_PROGRESS.md` 업데이트 — **R4 판정 후만**

PASS 시 Override History 1줄 append:
```
- 2026-05-XXTHH:MM:00Z | branch: memory-redesign-2026-05-16 | passed_gates: R0, R1, R2, R3 | SoT: reports/R4_FALSIFICATION_GATE_REPORT.md | NOTE: R4 falsification gate gate-ready (PASS). R4.passed sentinel은 사용자 명시 승인 후 생성.
```

R4.passed sentinel은 **사용자 명시 승인 없이 생성 금지** (사용자 명시).

### 8D. commit (총 3개)

**commit 1 (Stage 2+3 종료 시)**: `feat(r4): add standardized residual conformal falsification gate` (위 §"Stage 2+3 commit" 참조)

**commit 2 (Stage 4 종료 시)**: `test(r4): add 7 falsification gate test files`

**commit 3 (Stage 8 종료 시)**: `docs(r4): report falsification gate results and repair analysis`

commit 대상:
- src/fglc/falsification/*.py
- src/fglc/evaluation/falsification_metrics.py
- src/fglc/training/trainer_r3.py
- src/fglc/evaluation/metrics.py
- src/fglc/repair/{taxonomy,diagnose,candidates}.py (필요 시)
- scripts/fglc/r4_falsification.py
- scripts/fglc/r3_export_checkpoint.py
- configs/fglc/r4_falsification_*.yaml
- tests/test_fglc_falsification_*.py
- tests/test_fglc_r4_runner_maniskill.py
- reports/R4_FALSIFICATION_GATE_REPORT.md
- (R4 PASS 시) plans/PHASE_PROGRESS.md
- (R4 PASS 시 + 사용자 명시 승인 시) outputs/phase_gates/R4.passed

commit 금지:
- raw HDF5
- model checkpoint (.pt) — `.gitignore: outputs/*` 차단
- ledger.jsonl, metrics.json — 동일 차단
- hook log
- R3.passed sentinel
- **R4.passed sentinel (사용자 명시 승인 없이)**
- unrelated docs

### T-trigger
- T4 area-chair-synthesis-agent (deep): 최종 보고서 작성 시 (Agent A~G 7개 audit 종합)
- T5 reviewer-2-attack-agent (deep): R4 report 작성 후 reviewer 공격 시뮬

---

## Critical Files

### Read-only (전 stage)
- `data/fglc/PickCube-v1/raw/*.h5` (6 파일) — **mtime 보존 의무**
- `data/fglc/PushCube-v1/raw/*.h5` (6 파일) — **mtime 보존 의무**
- `docs/idea/02_FALSIFICATION_THEORY.md` (R4 이론 SoT)
- `docs/idea/04_BASE_WORLD_MODEL.md` (μ/σ shape SoT)
- `docs/idea/10_LOSS_DESIGN.md`, `12_TRAINING_STAGES.md`, `21_METRICS.md`, `18_DATA_BENCHMARKS.md`
- `docs/idea/22_NOVELTY_AND_THREATS.md` (AdaWM/CIRCA 차별화)
- `src/fglc/schemas/visibility.py::FORBIDDEN_AGENT_FIELDS` (12 forbidden)
- `outputs/phase_gates/R0~R3.passed` (보호)
- `outputs/repair/{pickcube,pushcube}_r3_2axis_2026-05-24/iter_0/metrics.json` (R3 closure SoT, hash 보존)
- `reports/R3_SMOKE_CLOSURE_REPORT.md`
- `docs/FUTURE_OOD_DATA_EXPANSION_INSIGHTS.md`

### Stage 2에서 수정
- `src/fglc/training/trainer_r3.py` (+save_state/load_state, ~20 LOC)
- `src/fglc/evaluation/metrics.py` (+evaluate_residuals, +STAGE2_CANONICAL_METRIC_KEYS, ~50 LOC)

### Stage 3에서 신규 생성
- `src/fglc/falsification/__init__.py`
- `src/fglc/falsification/residuals.py` (~80 LOC)
- `src/fglc/falsification/conformal.py` (~60 LOC)
- `src/fglc/falsification/gate.py` (~70 LOC)
- `src/fglc/evaluation/falsification_metrics.py` (~120 LOC)
- `scripts/fglc/r4_falsification.py` (~150 LOC)
- `scripts/fglc/r3_export_checkpoint.py` (~80 LOC)
- `configs/fglc/r4_falsification_pickcube.yaml`
- `configs/fglc/r4_falsification_pushcube.yaml`

### Stage 3에서 수정 (선택, repair loop 확장 시)
- `src/fglc/repair/taxonomy.py` (신규 R4 cause: CONFORMAL_QUANTILE_MISMATCH, BETA_GATE_DIRECTION_BLIND, EASY_LOOKING_OOD_MISSED)
- `src/fglc/repair/candidates.py` (대응 patch)
- `src/fglc/repair/diagnose.py::CANONICAL_METRIC_KEYS` 확장 (R4 9 key)

### Stage 4에서 신규
- `tests/test_fglc_falsification_residual.py`
- `tests/test_fglc_falsification_conformal.py`
- `tests/test_fglc_falsification_gate.py`
- `tests/test_fglc_r4_runner_maniskill.py`
- `tests/test_fglc_falsification_leakage.py`
- `tests/test_fglc_falsification_repro.py`

### Stage 5에서 생성 (자동, gitignored)
- `outputs/r4_falsification/{pickcube,pushcube}/r3_model.pt`
- `outputs/r4_falsification/{pickcube,pushcube}/iter_0/{config.yaml,metrics.json,run_manifest.json}`
- `outputs/r4_falsification/{pickcube,pushcube}/loop_*/ledger.jsonl`
- `outputs/r4_falsification/{pickcube,pushcube}/r4_stdout.log`

### Stage 8에서 생성/수정
- `reports/R4_FALSIFICATION_GATE_REPORT.md` (신규)
- (조건부 PASS 시) `plans/PHASE_PROGRESS.md` 1줄 append
- (조건부 사용자 승인 시) `outputs/phase_gates/R4.passed` zero-byte

---

## 기존 utility 재사용

- `scripts/fglc/r3_smoke.py` (R4 runner의 CLI 패턴 참조)
- `src/fglc/repair/{orchestrator,diagnose,candidates,ranker,compare,ledger}.py` (Stage 7 repair loop)
- `src/fglc/training/trainer_r3.py` (R3 inference 재사용)
- `src/fglc/models/{encoder,belief,dynamics,heads}.py` (μ/σ export 활용)
- `src/fglc/data/dataloader.py` (test_id 자동 로딩 활용)
- `src/fglc/evaluation/metrics.py::Evaluator` (베이스 확장)

---

## 자원 예산

| Stage | 파일 변경 | disk delta | wall-clock | GPU |
|---|---|---|---|---|
| 0 | 0 | 0 | 10 min | 0 |
| 1 | 0 | 0 | 10 min | 0 |
| 2 | 2 수정 | ~3 KB | 45 min | 0 |
| 3 | 9 신규 + 3 수정 | ~30 KB | 90 min | 0 |
| 4 | 6 신규 | ~25 KB | 30 min | 0 |
| 5 | artifacts 생성 | ~10 MB (2 ckpt + 4 metrics) | 30 min | RTX 4060 Ti 8 GB |
| 6 | 0 | 0 | 20 min | 0 |
| 7 | 조건부 | 변동 | 0~90 min | 변동 |
| 8 | 1 신규 + 1 수정 | ~25 KB | 30 min | 0 |
| **합계** | **~20 파일 + artifacts** | **~10 MB** | **4~6 hour** | **base inference만** |

---

## Team Agent 호출 매트릭스 (CLAUDE.md T-trigger)

| Stage | T-trigger | Agent | 모드 | 호출 시점 |
|---|---|---|---|---|
| 2 (post-edit) | T3 | fglc-code-reviewer | compact | trainer_r3.py + metrics.py 수정 후 |
| 3 (post-edit) | T3 | fglc-code-reviewer | compact | falsification 패키지 전체 후 |
| 5 (실패 시) | T2 | frcgw-test-runner | compact | smoke FAIL 시 pytest re-run |
| 6 (해석 전) | T4 | failure-interpretation-critic | deep | metric 분석 시 |
| 6 (acceptance 전) | T4 | claim-metric-alignment-auditor | compact | PASS 판정 직전 |
| 7 (repair iter) | T3 | implementation-risk-critic | compact | 각 patch 적용 후 |
| 8 (final) | T4 | area-chair-synthesis-agent | deep | R4 report 작성 시 |
| 8 (post-report) | T5 | reviewer-2-attack-agent | deep | R4 report 완료 후 reviewer 공격 시뮬 |

호출 명령: `/agent-team-review compact` 또는 `deep`

산출 경로:
- 개별: `docs/orchestration/agent_reports/2026-05/<agent>_r4_falsification_R1.md`
- synthesis: `docs/orchestration/agent_reports/synthesis/2026-05/r4_falsification_synthesis_R1.md`

---

## 절대 금지 (전 stage 공통)

- ❌ R5/R6/R7 진입 (causal attention / correction / planner)
- ❌ latency/noise/mass repair 새 데이터 수집
- ❌ raw HDF5 (`data/fglc/*/raw/*.h5`) 수정 또는 commit
- ❌ `outputs/phase_gates/R3.passed` 수정/삭제
- ❌ **`outputs/phase_gates/R4.passed` 사용자 명시 승인 없이 생성**
- ❌ R3 closure metrics.json/ledger.jsonl 수정 (R3 closure 무손)
- ❌ `docs/idea/` 무단 수정
- ❌ `src/fglc/schemas/visibility.py::FORBIDDEN_AGENT_FIELDS` 무단 수정
- ❌ regime_id / true_* / oracle_action / counterfactual_reward / split_id / ood_type / seed / template_id가 R4 model input에 들어가는 것
- ❌ conformal threshold τ를 OOD 데이터 보고 정하기
- ❌ β_t가 raw NLL보다 성공한다고 사전 단정
- ❌ raw NLL 역전 결과를 실패로 숨김
- ❌ 실패 보고만 하고 종료 (Stage 7 repair loop max 3 iter 시도 의무)
- ❌ Stage 3 외 부수 리팩터링 (예: encoder/belief 수정)
- ❌ baseline / ablation grid 진입 (R9/R10)
- ❌ threshold 완화로 test FAIL을 PASS로 위장
- ❌ 양방향(gain=1.3) 데이터를 이번 R4 작업에서 수집 (사용자 명시: 별도 작업으로 분리)
- ❌ Codex에 위 금지 경로 위임

---

## 검증 절차 (각 stage 종료 시)

```powershell
# 1. raw HDF5 무손
Get-Item data/fglc/PickCube-v1/raw/*.h5 | Select Name, Length, LastWriteTime
Get-Item data/fglc/PushCube-v1/raw/*.h5 | Select Name, Length, LastWriteTime

# 2. phase gate 보호
Test-Path C:\Users\computer\Desktop\ICLR_WM_claude-code\outputs\phase_gates\R3.passed  # True 유지
Test-Path C:\Users\computer\Desktop\ICLR_WM_claude-code\outputs\phase_gates\R4.passed  # False 유지 (사용자 승인 전)

# 3. R3 closure artifact 보호
Get-FileHash outputs/repair/pickcube_r3_2axis_2026-05-24/iter_0/metrics.json
Get-FileHash outputs/repair/pushcube_r3_2axis_2026-05-24/iter_0/metrics.json
# (Stage 0와 Stage 8에서 동일해야 함)

# 4. tests
& .venv\Scripts\python.exe -m pytest -q `
    tests/test_fglc_forbidden_field_sync.py `
    tests/test_fglc_split_integrity.py `
    tests/test_fglc_ood_severity.py `
    tests/test_fglc_r3_runner_maniskill.py `
    tests/test_fglc_falsification_*.py `
    tests/test_fglc_r4_runner_maniskill.py

# 5. R4 metrics.json 키 (Stage 5 후)
Get-ChildItem outputs/r4_falsification -Recurse -Filter metrics.json |
  ForEach-Object { & .venv\Scripts\python.exe -c "import json,sys; m=json.load(open(sys.argv[1])); print(sys.argv[1], sorted(m.keys()))" $_.FullName }
# 기대: beta_t_auroc_friction, beta_t_auroc_gain, beta_t_fpr_id, beta_t_tpr_friction, beta_t_tpr_gain, conformal_threshold, residual_ece, raw_nll_auroc_friction, raw_nll_auroc_gain + 기존 R3 키

# 6. ledger REQUIRED_KEYS
Get-ChildItem outputs/r4_falsification -Recurse -Filter ledger.jsonl |
  ForEach-Object { Get-Content $_.FullName | Select-Object -First 1 | & .venv\Scripts\python.exe -c "import json,sys; d=json.loads(sys.stdin.read()); print(len(d), sorted(d.keys()))" }
# 기대: 19개

# 7. forbidden field leak 검사
Select-String -Path outputs/r4_falsification/*/r4_stdout.log -Pattern "regime_id|true_mass|true_friction|true_latency|true_action_gain|oracle_action|counterfactual_reward|split_id|ood_type|template_id"
# 기대: 매치 0건

# 8. git status
git status --short
```

---

## Final Rule

본 plan의 목표는 **R3 closure에서 발견된 raw NLL OOD 탐지 실패를 standardized residual + conformal β_t gate가 보완할 수 있는지 friction + action_gain 단방향에서 검증하는 것**이다.

```
read correct context (3 Explore agent audit + 이론 + R3 closure)
preserve scientific contract (R3.passed/R3 closure artifact/raw HDF5/forbidden 12 보존)
implement smallest valid step (M1-M4,M7 + 단방향 평가 + 7 tests)
test before scaling (Stage 4 tests PASS → R3 ckpt → R4 smoke → metric 검증)
report blockers honestly (β_t 우월성을 사전 단정하지 않고 실측 보고; PARTIAL/BLOCKED 격하 금지)
```

### 판정 기준 (R3 closure §H.3 default)

- **PASS**: 양 task에서 β_t AUROC ≥ 0.85 (friction OR gain) AND β_t FPR ≤ 0.05 + 2σ AND raw NLL 대비 AUROC gain ≥ +0.20 + 모든 Stage 0~8 완주 + 모든 invariant 보존
- **PARTIAL_PASS**: 한 task 또는 한 axis만 통과 — §L에 한계 명시 후 commit
- **PATCH_REQUIRED**: Stage 7 repair loop max 3 iter 후에도 위 기준 미달
- **BLOCKED**: residual NaN/Inf 반복 해결 불가, R3 ckpt 호환 실패, forbidden field leak, raw HDF5 손상

### 사용자 plan 검토 시 변경 가능한 default

1. R3 checkpoint 저장 방식: trainer_r3.py 수정 + R3 minimal rerun (default) ↔ R3 trainer 변경 없이 R4 evaluator 안에서 매번 R3 학습 ↔ 다른 방식
2. R4 PASS gate 정량 기준: §H.3 제안값 (default) ↔ 더 보수적 (AUROC≥0.90) ↔ 더 공격적 (AUROC≥0.80)
3. conformal α 값: 0.05 (default) ↔ 다른 값
4. STAGE2_CANONICAL_METRIC_KEYS 분리 vs STAGE1 확장: 분리 권장 (default) ↔ STAGE1 확장
5. β_t MLP 학습 vs conformal-only: conformal-only (default, 더 단순) ↔ MLP 학습 (Stage 2 freeze 정책과 충돌, 비권장)

본 plan은 ExitPlanMode 승인 후 Stage 0부터 순차 진행한다.
