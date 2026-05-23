# 4060_SMOKE_REPAIR_PATH — RTX 4060 8GB Smoke 실험 경로

> **Source**: `docs/EXPERIMENT_REPAIR_LOOP_PLAN.md` §E + CLAUDE.md §머신 환경
> **Scope**: state-only ManiSkill PickCube 1태스크. RGB-D / DROID / BridgeData / full baseline grid는 모두 DEFERRED.
> **Status**: v0 (2026-05-23)

---

## 목적

전체 ROADMAP(A100 ~55일 기준)에서 RTX 4060 8GB 단일 GPU로 즉시 실행 가능한
**축소 smoke path**를 명시한다. Closed-loop repair harness(`docs/EXPERIMENT_REPAIR_LOOP_PLAN.md`)의
예산 체크에 사용된다.

---

## A100 기준 vs 4060 smoke 대비

| 항목 | A100 기준 (ROADMAP) | 4060 Smoke | 비고 |
|---|---|---|---|
| GPU | A100 40~80GB | RTX 4060 Ti 8GB | VRAM 8188 MiB |
| 전체 로드맵 기간 | ~55일 | 7일 이내/phase (smoke) | 단일 GPU |
| K (latent group) | 6 (기본) | 4, 6 | 8은 h_dim=256 시 OOM 위험 |
| d (per-group latent dim) | 32 | 16, 32 | 32 권장 (192차원 이상이면 재검토) |
| h_dim (GRU hidden) | 256 | 128, 256 | 128 권장 시작 |
| train horizon | 16 | 8, 16 | 8 권장 시작 |
| planning horizon | 5~10 | 3, 5 | 3 권장 시작 |
| batch size | 64~256 | 8, 16, 32 | 16 권장 시작 |
| episode 수 | 5000~50000 | 200, 500, 1000 | 200 smoke / 500 standard |
| seed 수 | 5 | 1 (smoke), 3 (standard) | smoke는 seed=42 단일 |
| MPPI n_rollout | 512 | 128, 256 | 4060에서 512는 planner가 느림 |
| RGB-D | 포함 | **DEFERRED** | ViT encoder OOM |
| DreamerV3 / HiP-RSSM | 포함 | **DEFERRED** | 동시 학습 불가 |
| DROID/BridgeData | 포함 | **DEFERRED** | ~100GB, 불가 |

---

## Hyperparam 후보 범위 (state-only ManiSkill PickCube)

### Grid

| param | 후보 | OOM 안전 추정 (8GB) |
|---|---|---|
| K | 4, 6, 8 | 6 권장 — 8은 h_dim=256 시 주의 |
| d | 16, 32 | 32 권장 |
| h_dim | 128, 256 | 128 권장 시작 |
| train_horizon | 8, 16 | 8 권장 시작 |
| planning_horizon | 3, 5 | 3 권장 시작 |
| batch_size | 8, 16, 32 | 16 권장 시작 |
| n_episode | 200, 500, 1000 | 200 smoke / 500 standard |
| seed | 42, 123, 456 | smoke 1개 / standard 3개 |

### VRAM 추정 (state-only, no RGB)

```
batch(16) × T(8) × K(6) × d(32) = 24,576 float32 ≈ 100 KB/sample
activations + grad ≈ 4× = 400 KB × 16 batch = 6.4 MB (매우 여유)
GRU h_dim=128 × layers=2 × batch(16): ~0.1 MB

총 추정 활성 메모리: < 50 MB (모델 파라미터 포함 시 < 200 MB)
→ 8GB VRAM 한계 기준 ≈ 40× 여유
```

OOM 위험 구간: `K=8 × d=32 × h_dim=256 × batch=32 × T=16` → 재측정 필요.

---

## Per-run Budget Cap

| 항목 | Smoke 모드 | Standard 모드 |
|---|---|---|
| per-iter wall-clock | ≤ 30분 | ≤ 60분 |
| total wall-clock (loop) | ≤ 4시간 | ≤ 8시간 |
| max-iter | 5 | 5 |
| max consecutive inconclusive | 3 | 3 |
| GPU memory cap | `torch.cuda.set_per_process_memory_fraction(0.85)` | 동일 |
| early stop | NLL 변동률 < 0.5% / 100 step 이하 | 동일 |
| OOM 발생 시 fallback 순서 | ① batch_size 절반 → ② K −1 → ③ T 절반 | 동일 |

---

## Phase별 Smoke Gate Threshold (4060 기준)

원래 ROADMAP gate threshold를 smoke 환경(소규모 데이터/짧은 학습)에 맞게 완화한 기준이다.
**실제 gate pass는 실측 metric artifact 기반이어야 한다** — 이 표는 "smoke라면 이 정도면 다음 단계 진행 가능" 기준이다.

| Phase | Metric | ROADMAP 기준 | 4060 Smoke 기준 |
|---|---|---|---|
| R3 (base WM) | ID NLL 1-step | TBD (idea/21) | ≤ 0.5 nat |
| R3 | OOD−ID NLL gap | ≥ 0.1 nat | ≥ 0.05 nat |
| R4 (falsification) | OOD AUROC | ≥ 0.75 | ≥ 0.65 |
| R4 | ECE | ≤ 0.10 | ≤ 0.20 |
| R6 (correction) | corrected NLL < uncorrected | Δ ≥ 0.05 nat | Δ ≥ 0.02 nat |
| R7 (planner) | return vs no-correction | Δ ≥ 0.1 return | Δ ≥ 0.05 return |

> 위 수치는 UNKNOWN — 실제 R3 첫 run 후 조정 예정 (U5 해소 후).

---

## DEFERRED 항목 명시 (4060 환경 한정)

다음 항목은 4060 smoke path에서 **명시적으로 실행하지 않는다**.
DEFER 해제는 사용자 명시 지시 또는 standard GPU 확보 시에만 가능하다.

| Phase/항목 | DEFER 이유 | 참조 |
|---|---|---|
| R8 ASAP/I3G | CIRCA+IVI 먼저 (ROADMAP/19/R-13). smoke에서는 CIRCA만 | `docs/ROADMAP/19_RISKS_BLOCKERS.md:R-13` |
| R10 DreamerV3 | 별도 학습 인프라 + ~8GB 상시 점유 — 동시 실험 불가 | `docs/idea/19_BASELINES.md` |
| R10 HiP-RSSM | 동일 이유 | 동 |
| R10 PLSM | 동일 이유 | 동 |
| R10 ReDRAW | 동일 이유 | 동 |
| R10 AdaWM | 동일 이유 | 동 |
| R10 smoke baseline | TD-MPC2 + oracle-mass + no-correction 3개만 | `docs/idea/19_BASELINES.md` §smoke 기준 |
| R11 RGB-D | ViT encoder OOM. state-only가 충분하면 연기 | `docs/ROADMAP/12_PHASE_R11.md:L24` |
| R12 DROID | ~100GB dataset, 4060에서 불가 | `docs/ROADMAP/19_RISKS_BLOCKERS.md:R-4` |
| R12 BridgeData | 동일 이유 | 동 |
| R13 5-seed nec/suf | R6의 basic nec/suf만 유지 (3-seed) | `docs/ROADMAP/14_PHASE_R13.md` |

---

## OOM Fallback 절차

```
1. OOM 발생 즉시 torch.cuda.empty_cache() 호출
2. batch_size 절반 (16→8, 8→4)
3. 여전히 OOM: K −1 (6→4)
4. 여전히 OOM: train_horizon 절반 (16→8, 8→4)
5. 3회 fallback 후에도 OOM: IMPLEMENTATION_BUG_SUSPECTED 또는 h_dim=64로 축소
   → 사용자에게 blocker 보고
```

OOM fallback 이력은 `ledger.jsonl`의 `oom_fallbacks_applied` 필드에 기록된다.

---

## Entry Point

```powershell
# dry-run (실제 학습 없음, mock metrics)
.venv\Scripts\python.exe scripts\fglc\repair_loop.py `
  --phase R3 `
  --config configs\fglc\smoke_4060.yaml `
  --dry-run

# smoke real run
.venv\Scripts\python.exe scripts\fglc\repair_loop.py `
  --phase R3 `
  --config configs\fglc\smoke_4060.yaml `
  --seed 42 `
  --max-iter 5 `
  --max-wall-clock-minutes 240
```

> **BLOCKER**: `src/fglc/` R3 모듈(encoder/dynamics/world model heads)이 아직 부재.
> dry-run은 가능하나 real run은 R3 모듈 구현 후에만 실행 가능.

---

## 참조

- master plan: `docs/EXPERIMENT_REPAIR_LOOP_PLAN.md`
- taxonomy: `docs/idea/FGLC_FAILURE_TAXONOMY.md`
- ledger schema: `docs/EXPERIMENT_LEDGER_SCHEMA.md`
- machine spec: `CLAUDE.md §머신 환경`
- config: `configs/fglc/smoke_4060.yaml` (신규, Step 5 이후)
