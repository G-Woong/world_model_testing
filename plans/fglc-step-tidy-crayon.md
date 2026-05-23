# Step 10 PLAN — R3 base world model smoke (synthetic toy fixture 단계)

> Status: PLAN ONLY (코드 수정/파일 생성/실험 실행/sentinel 생성 금지)
> 작성일: 2026-05-23
> 선행: STEP9.5_PASS (commits `e243455`, `7218c6d`, `68888e5`)
> 사용자 결정 1: 데이터 경로 = 2단계 (synthetic toy → ManiSkill state-only 순차). Step 10은 synthetic만, R3.passed는 별도 phase에서 닫음.
> 사용자 결정 2: R1/R2 sentinel = Step 10 PLAN에 mini-closure 동반 명시.

---

## Context

Step 9.5에서 closed-loop repair harness(`src/fglc/repair/*`, `scripts/fglc/repair_loop.py`)는 production-ready 수준으로 완성됐고 ledger 구조도 `outputs/repair/{loop_id}/ledger.jsonl`로 안정화됐다(CD-1/CD-9 패치, dry-run 7 시나리오 PASS).

그러나 **R3 base world model 본체 코드는 0% 구현 상태**다. `src/fglc/__init__.py:7-17`이 R1~R8 컴포넌트를 docstring으로 약속만 했을 뿐 `src/fglc/models/`, `src/fglc/training/`, `src/fglc/evaluation/`, `src/fglc/data/`, `src/fglc/runners/` 디렉터리 전체가 미생성이다(Glob `src/fglc/**/*.py` 결과 = `schemas/visibility.py` + `repair/*` 8개 + `__init__.py` + `py.typed`만 존재).

따라서 Step 10의 목표는 **R3 과학적 통과(`R3.passed` 생성)가 아니라**, synthetic toy fixture로 다음 흐름이 끊김 없이 연결됨을 검증하는 것이다:

```
toy dataset → encoder/belief/dynamics → trainer → evaluator → metrics.json
→ R3Runner(RepairRunner Protocol) → run_repair_loop
→ diagnose → candidates → ranker → compare → ledger.jsonl
```

R3.passed sentinel은 Step 10 이후 ManiSkill state-only 데이터 파이프라인 단계에서 별도 phase-check로 닫는다.

---

## A. 현재 repo 상태 감사 요약

### A.1 코드 상태 (`src/fglc/`)
- **존재**: `schemas/visibility.py` (12 forbidden fields, SSoT), `repair/` 8 modules (`taxonomy.py`, `diagnose.py`, `candidates.py`, `ranker.py`, `compare.py`, `ledger.py`, `orchestrator.py`, `__init__.py`).
- **부재 (BLOCKED)**: `models/{encoder,dynamics,belief}.py`, `training/`, `evaluation/`, `data/`, `runners/`, `detectors/`, `attention/`, `correction/`, `planning/` 디렉터리 전체.
- 핵심 인터페이스: `RepairRunner` Protocol (`src/fglc/repair/orchestrator.py:74-85`) — `__call__(*, phase, config_path, split, seed, descriptor, patch, iter_index) -> RunnerOutput`이 metric dict를 받는 유일한 경로.

### A.2 config 상태 (`configs/fglc/`)
- `smoke_4060.yaml` 6 lines만 존재 (`phase: R3`, `seed: 0`, `K: 4`, `d: 32`, `h: 64`, `batch_size: 32`).
- **CD-8 미해결**: 권장 K=6, h=128, batch=16, +`train_horizon`, `n_episode`, `dataset`, `model`, `trainer`, `metric` 섹션이 모두 없음.
- R3 trainer가 yaml을 읽으려면 schema 보강 필수.

### A.3 scripts 상태 (`scripts/fglc/`)
- `repair_loop.py` 1개만 존재. argparse 옵션 12개 완비 (`--phase`, `--config`, `--split`, `--seed`, `--descriptor`, `--failed-metric`, `--max-iter`, `--max-wall-clock-minutes`, `--max-consecutive-inconclusive`, `--output-root`, `--dry-run`, `--mock-scenario`).
- L94–L136 `build_mock_runner`만 존재 — **실제 R3 학습 runner는 미구현**.
- 누락: `train_world_model.py`, `eval_world_model.py`, `collect_dataset.py`, `r3_smoke.py`.

### A.4 tests 상태 (`tests/`)
- 현재 `pytest tests/` = **159 passed** (사용자 인지값 65와 불일치 — Step 9.5 이후 lifecycle/repair/forbidden_field 테스트가 누적된 결과로 추정).
- repair 9개 (`test_fglc_repair_{taxonomy,compare,candidates,diagnose,ranker,loop_cli,ledger,orchestrator}.py` + `test_fglc_forbidden_field_sync.py`), lifecycle 5개.
- **R3 관련 unit test 0개**: `test_world_model*`, `test_dataset*`, `test_trainer*`, `test_encoder*`, `test_dynamics*` 모두 부재. `tests/fixtures/`, `tests/data/` 디렉터리 자체 부재.

### A.5 outputs 상태
- `outputs/repair/`: Step 9.5 신구조 적용 확인. `loop_2026-05-23T09-29-55-3eef/ledger.jsonl` 등 7개 디렉터리 + 구버전 flat 6개 잔존.
- `outputs/phase_gates/`: **`R0.passed` 단 1개만 존재** (zero-byte, 2026-05-22 15:59). R1~R16 sentinel 전부 미생성.
- ledger 라인은 정상 스키마 (REQUIRED_KEYS 19개, `phase: "R3"` 기록 가능).

### A.6 dependencies 상태
- `requirements.txt`: `torch==2.6.0+cu124`, `numpy==2.1.3`, `gymnasium==1.2.3`, `mujoco==3.6.0`, `pytest==9.0.3` 등 154 핀.
- **누락 (pyproject.toml에는 있으나 미설치)**: `h5py`, `hydra-core`, `omegaconf`, optional `mani-skill`, `sapien`, `tensorflow-datasets`.
- 사용자 결정에 따라 **synthetic toy 경로는 torch + numpy만 사용** → 위 의존성 갭은 Step 10에서 차단 사유 아님.

### A.7 문서 계약 (핵심 추출)
- R3 정식 gate (`docs/ROADMAP/04_PHASE_R3_BASE_WORLD_MODEL.md` L35-42, `docs/idea/04_BASE_WORLD_MODEL.md` C5): ID 1-step NLL < 0.1 nat, OOD-mass gap > 0.2 nat, OOD-friction gap > 0.1 nat.
- 4060 smoke 완화 (`docs/ROADMAP/4060_SMOKE_REPAIR_PATH.md` L88-90): ID NLL ≤ 0.5 nat, OOD-ID gap ≥ 0.05 nat. 단 L96에서 "UNKNOWN — 실측 후 조정" 명시.
- Stage 1 loss (`docs/idea/10_LOSS_DESIGN.md` L18-32): `L_base_dynamics + λ1·L_reward + λ2·L_value + λ3·L_calibration`, λ1=1.0, λ2=1.0, λ3=0.1.
- forbidden fields 12개 (`docs/idea/18_DATA_BENCHMARKS.md` L25-34 + `src/fglc/schemas/visibility.py:18-31`): `regime_id, true_{mass,friction,latency,noise_sigma,action_gain}, oracle_action, counterfactual_reward, split_id, ood_type, seed, template_id`.
- R3 phase doc 권장 아키텍처: encoder MLP `D_x→256→256→K*d`, GRU h_dim=256 (A100) / 128 (4060), 2-layer group transformer, per-group MLP dynamics.

---

## B. Step 10 진입 가능 여부

**진입 가능**. 단 다음 조건 하에:

1. 사용자 결정대로 **synthetic toy fixture 단계**로 시작 — ManiSkill/h5py 의존성 회피.
2. `R3.passed` sentinel **절대 생성 금지** (Step 10 종료 시점 검증 대상이 "R3 smoke 연결성"이지 "R3 과학적 통과"가 아님).
3. R1/R2 mini-closure를 Step 10A/10B에 동반.
4. 159 tests passed 유지가 모든 sub-step의 precondition.

진입 차단 사유는 없다. CD-1/CD-9 패치 완료, ledger 신구조 정상, repair harness Protocol이 외부 runner 주입을 받도록 설계되어 있어 R3 본체 구현만 추가하면 즉시 연결 가능.

---

## C. R3 구현에 필요한 누락 요소

### C.1 코드 (BLOCKED 8건)
| 파일 | 책임 | 우선순위 |
|---|---|---|
| `src/fglc/models/__init__.py` + `encoder.py` | grouped latent encoder (MLP, K=6, d=32) | 필수 |
| `src/fglc/models/belief.py` | GRU belief memory (h_dim=128) | 필수 |
| `src/fglc/models/dynamics.py` | per-group MLP dynamics → μ, logσ | 필수 |
| `src/fglc/training/__init__.py` + `trainer_r3.py` | Stage 1 loss, epoch loop | 필수 |
| `src/fglc/evaluation/__init__.py` + `metrics.py` | `id_nll`, `train_nll`, `val_train_nll_gap`, `stagnant_epochs`, `kstep_nll_slope`, `ood_*_nll` | 필수 |
| `src/fglc/data/__init__.py` + `state_only_dataset.py` + `dataloader.py` | synthetic toy state-action episode | 필수 |
| `src/fglc/runners/__init__.py` + `r3_runner.py` | `RepairRunner` Protocol 구현 | 필수 |
| `scripts/fglc/r3_smoke.py` (또는 `repair_loop.py`의 runner 분기) | real-run entry point | 필수 |

### C.2 config 보강 (CD-8 동반)
`configs/fglc/smoke_4060.yaml`을 다음 섹션 구조로 확장:
```yaml
phase: R3
seed: 42
device: cuda  # or cpu
dataset:
  type: synthetic_toy
  D_x: 8
  D_a: 4
  episode_len: 64
  n_episode_train: 32
  n_episode_val: 8
  n_episode_ood_mass: 16
  n_episode_ood_friction: 16
  ood_mass_scale: 2.0
  ood_friction_scale: 0.5
model:
  K: 6
  d: 32
  h_dim: 128
  encoder_hidden: 256
  dynamics_hidden: 64
trainer:
  batch_size: 16
  train_horizon: 8
  epochs: 5
  learning_rate: 3e-4
  optimizer: adam
  loss_weights:
    lambda_reward: 1.0
    lambda_value: 1.0
    lambda_calibration: 0.0  # smoke 단계 비활성
metric:
  primary: id_nll
  gate_threshold_id_nll: 0.5
  gate_threshold_ood_id_gap: 0.05
```

### C.3 문서 정렬 (CD-3, CD-4, CD-5)
- `docs/EXPERIMENT_LEDGER_SCHEMA.md` 예시 키 `id_nll_1step` ↔ `src/fglc/repair/diagnose.py:10` CANONICAL `id_nll` 명명 표준화 결정 필요. 권장: 코드 쪽 `id_nll`을 정식 키로 채택 후 ledger schema 예시 문서를 정렬.
- `scripts/fglc/repair_loop.py:84` default gate `id_nll: 0.4` → `0.5` (4060 path 정렬).
- `--dry-run` help text 1줄 보강.

### C.4 R1/R2 mini-closure
- R1.passed 조건: `src/fglc/` 스켈레톤 audit 보고 + 의존성 결정 (synthetic 경로 = h5py/mani-skill 불필요) + `import src.fglc` smoke.
- R2.passed 조건: synthetic toy state-only dataset 생성기 + forbidden field 0건 assert + 4 split shape 일관성 검증.

### C.5 tests (BLOCKED 4건)
- `tests/test_fglc_base_wm.py`
- `tests/test_fglc_dataset_state_only.py`
- `tests/test_fglc_trainer_r3_smoke.py`
- `tests/test_fglc_r3_runner_integration.py`
- `tests/fixtures/` 디렉터리 신규

---

## D. Step 10의 권장 하위 단계

| Sub-step | 범위 | Verify | Codex 위임 |
|---|---|---|---|
| **10A** | R3 prerequisite audit + R1 mini-closure | `docs/STEP10A_AUDIT_REPORT.md` 작성, `/fglc-phase-check --pass R1` | ✗ Claude 직접 |
| **10B** | Config schema 확장 + state-only toy dataset + R2 mini-closure | `pytest tests/test_fglc_dataset_state_only.py` PASS, forbidden field 0건, `/fglc-phase-check --pass R2` | ✓ TASK 10B |
| **10C** | Base WM 최소 모듈 (encoder/dynamics/belief) | `pytest tests/test_fglc_base_wm.py` PASS, shape 검증 | ✓ TASK 10C |
| **10D** | Trainer + Evaluator + metrics.json artifact | `pytest tests/test_fglc_trainer_r3_smoke.py` PASS, 1 epoch loss 감소, metrics.json 생성 | ✓ TASK 10D |
| **10E** | R3Runner adapter + `run_repair_loop` 연결 | `pytest tests/test_fglc_r3_runner_integration.py` PASS, ledger.jsonl 1줄 REQUIRED_KEYS 19개 | ✓ TASK 10E |
| **10F** | 1-iter real smoke 실행 + 결과 보고 | `outputs/repair/{loop_id}/ledger.jsonl` 1줄, `docs/STEP10_RESULT_REPORT.md` | ✗ Claude 직접 |

각 10B~10E TASK는 merge 직전 **T3 implementation-risk-critic** agent 호출 (Gatekeeper 6번째 조건, `CLAUDE.md` Codex Orchestration §Gatekeeper).

---

## E. 최소 R3 smoke contract

### E.1 입력 데이터 (synthetic toy)
- trajectory tuple: `(state[D_x=8], action[D_a=4], reward[float], done[bool])`
- episode_len = 64
- 4 split:
  - train ID: n=32, mass=1.0, friction=1.0
  - val ID: n=8, mass=1.0, friction=1.0
  - OOD-mass: n=16, mass=2.0
  - OOD-friction: n=16, friction=0.5
- 생성식: `x_{t+1} = mass · A·x_t + friction · B·a_t + N(0, σ²)`, `r_t = c1·||x_t||² + c2·||a_t||²`
- **인퍼런스 입력 허용 필드 4개**: `state, action, reward, done`. 12 forbidden 부재 검증 (`assert_no_forbidden_fields`).

### E.2 batch shape
- `state: [B=16, T=8, D_x=8]`
- `action: [B=16, T=8, D_a=4]`
- `reward: [B=16, T=8]`
- `done: [B=16, T=8]` bool

### E.3 모델 입출력
- `encoder(state[B,T,D_x]) → z[B,T,K=6,d=32]`
- `belief(z_flat[B,T,K*d], action[B,T,D_a], reward[B,T,1]) → h[B,T,h_dim=128]`
- `dynamics(z[B,T,K,d], action[B,T,D_a], h[B,T,h_dim]) → (μ[B,T,K,d], logσ[B,T,K,d])`
- `reward_head(z_flat + action + h) → r_hat[B,T]`
- `value_head(z_flat + h) → v_hat[B,T]`

### E.4 loss (Stage 1, `docs/idea/10_LOSS_DESIGN.md`)
- `L_total = L_base_dynamics + λ1·L_reward + λ2·L_value + λ3·L_calibration`
- λ1=1.0, λ2=1.0, λ3=0.0 (smoke 단계 calibration 비활성)
- `L_base_dynamics = -log N(z_{t+1}; μ_t, exp(2·logσ_t))` (1-step Gaussian NLL)
- `L_reward = MSE(r_hat, r_true)`
- `L_value = MSE(v_hat, MC_return)`

### E.5 metrics.json 형식
```json
{
  "id_nll": 0.42,
  "train_nll": 0.40,
  "val_nll": 0.42,
  "val_train_nll_gap": 0.02,
  "stagnant_epochs": 0,
  "ood_mass_nll": 0.58,
  "ood_friction_nll": 0.51,
  "ood_id_nll_diff": 0.16,
  "kstep_nll_slope": 0.03,
  "epoch": 5,
  "wall_clock_minutes": 4.2,
  "vram_peak_mib": 850
}
```
키 명명은 `src/fglc/repair/diagnose.py:10` `CANONICAL_METRIC_KEYS`와 정합 (CD-3 결정).

### E.6 ledger 연결
- R3Runner는 `RunnerOutput(metrics=<위 dict>, wall_clock_minutes=4.2, vram_peak_mib=850, hook_blocked=False, hook_reason="")` 반환.
- `run_repair_loop`이 `outputs/repair/{loop_id}/ledger.jsonl` 1줄 + `iter_{N}/{config.yaml, metrics.json, compare.json, run_manifest.json}` 4종 생성 (CD-2 동반).

---

## F. 데이터 파이프라인 선택지와 권장 방향

사용자 결정: **2단계 (synthetic→ManiSkill 순차)**.

### F.1 Step 10 단계 — synthetic toy fixture (이 PLAN의 범위)
- 위치: `src/fglc/data/state_only_dataset.py`
- 의존성: torch + numpy만 사용 (h5py/hydra/mani-skill/sapien 불필요)
- 4 split (train ID / val ID / OOD-mass / OOD-friction) on-the-fly 생성
- forbidden field 12개 부재 강제 (`src/fglc/schemas/visibility.py::assert_no_forbidden_fields`)
- 산출: R1/R2 mini-closure → R3 smoke 연결 검증

### F.2 ManiSkill 단계 (Step 10 종료 후, R3.passed 별도 PR)
- 위치: `src/fglc/data/maniskill_collector.py` (`docs/ROADMAP/03_PHASE_R2_DATA_PIPELINE.md` 기반)
- `pyproject.toml [maniskill]` extras 설치 + Windows 호환성 검증
- 200 episode/split × 3 task × 7 split (4060 path L29 축소판)
- 정식 R3 gate (ID NLL < 0.1 nat 또는 ≤ 0.5 nat 4060 완화) 검증 후 `/fglc-phase-check --pass R3`
- **이 PLAN의 직접 범위 밖**, Step 10F 결과 보고에서 진입 여부 결정.

---

## G. Base WM 최소 아키텍처 방향

### G.1 Encoder (`src/fglc/models/encoder.py`)
- `nn.Sequential(Linear(D_x, 256), LayerNorm, SiLU, Linear(256, 256), LayerNorm, SiLU, Linear(256, K*d))`
- reshape `→ [B, T, K, d]`
- docstring: `docs/idea/04_BASE_WORLD_MODEL.md` L18-22, `docs/ROADMAP/04_PHASE_R3_BASE_WORLD_MODEL.md` L13-15

### G.2 Belief (`src/fglc/models/belief.py`)
- `nn.GRU(input_size=K*d + D_a + 1, hidden_size=128, num_layers=1, batch_first=True)`
- 입력 `[flatten(z_t), a_{t-1}, r_{t-1}]`
- docstring: `docs/idea/04_BASE_WORLD_MODEL.md` L24-28

### G.3 Dynamics (`src/fglc/models/dynamics.py`)
- Step 10 단순화: **group transformer 생략**, per-group MLP만.
- group k별 `nn.Sequential(Linear(d + h_dim + D_a, 64), SiLU, Linear(64, 2*d))` → split `(μ, logσ)`
- group transformer 2-layer는 ManiSkill 단계 (R3.passed gate용)에서 추가. PLAN에 명시적 DEFERRED.

### G.4 Reward / Value head
- `reward_head = Linear(K*d + D_a + h_dim, 1)`, `value_head = Linear(K*d + h_dim, 1)`, 둘 다 hidden=64 SiLU MLP

### G.5 4060 8GB VRAM 안전성
- 추정 활성 메모리: B=16 × T=8 × K=6 × d=32 × 4B ≈ 100 KB / layer activation. 5 epoch 기준 < 1 GB.
- `torch.cuda.set_per_process_memory_fraction(0.85)` 호출 의무 (4060 path L74).
- OOM fallback 순서 (4060 path L76-78): ① batch//2 → ② K-1 → ③ T//2.
- CPU fallback 지원 (`device: cpu` 옵션, pytest 환경 변수 `FGLC_DEVICE=cpu`).

---

## H. metric artifact와 repair loop 연결 방식

### H.1 R3SmokeRunner 시그니처 (`src/fglc/runners/r3_runner.py`)
```python
class R3SmokeRunner:  # implements src/fglc/repair/orchestrator.py:74 RepairRunner Protocol
    def __init__(self, base_config_path: Path): ...

    def __call__(
        self,
        *,
        phase: str,            # "R3"
        config_path: Path,     # baseline config
        split: str,            # "val" or "train"
        seed: int,
        descriptor: str,
        patch: Mapping[str, Any] | None,   # candidates.py R3 patch keys
        iter_index: int,
    ) -> RunnerOutput:
        # 1) load config + apply patch
        # 2) build toy dataset (4 split)
        # 3) build model (encoder + belief + dynamics + heads)
        # 4) trainer_r3.train(...)  → train/val NLL
        # 5) evaluator.evaluate(...) → metrics dict
        # 6) save iter_{iter_index}/metrics.json (CD-2 동반)
        # 7) return RunnerOutput(metrics=..., wall_clock_minutes=..., vram_peak_mib=..., hook_blocked=False, hook_reason="")
```

`patch` dict는 `src/fglc/repair/candidates.py:24-80`의 R3 키를 수용: `hidden_dim`, `num_episodes`, `horizon`, `loss_weights`, `corrected_loss_weight` (Step 10에서는 마지막 항은 사용 안 함).

### H.2 ledger 흐름 (Step 10 1-iter 시나리오)
1. `run_repair_loop(cfg, runner=R3SmokeRunner(...))` 호출
2. baseline run (patch=None) → `metrics_before` (e.g., `id_nll=0.42`)
3. `diagnose(metrics_before, phase="R3")` → e.g., `[MODEL_UNDERCAPACITY]` (id_nll > 0.5 threshold 면 발화)
4. `candidates_for([MODEL_UNDERCAPACITY], "R3")` → e.g., `hidden_dim 128→256` 후보
5. `rank(...)` → cheapest
6. patched run (patch={"hidden_dim": 256}) → `metrics_after`
7. `compare_metrics(...)` → accept/reject/inconclusive
8. ledger.jsonl 1줄 append (`REQUIRED_KEYS` 19개 모두)

### H.3 실패 흐름의 repair loop 활용 (사용자 지시 "실패는 입력")
Step 10 smoke가 id_nll gate(0.5)를 못 넘으면:
- `diagnose` → `MODEL_UNDERCAPACITY / DATA_TOO_SMALL / HORIZON_TOO_SHORT / LOSS_IMBALANCE` 중 하나 발화 (`docs/EXPERIMENT_REPAIR_LOOP_PLAN.md` D.3 L141)
- `candidates` → `h_dim 128→256`, `num_episodes ×2 (32→64)`, `horizon 8→16`, `loss_weights` 재정렬
- `rank` → 가장 cheap & low-risk 후보
- patched run → compare → ledger append
- max_iter=3, max_wall_clock=240 min, max_consecutive_inconclusive=2

→ 단 한 번도 "smoke 실패 = Step 10 종료"로 처리하지 않는다. 항상 repair loop 입력으로 변환.

---

## I. 테스트/검증 계획

### I.1 기존 159 tests green 유지 (precondition)
모든 sub-step의 merge 전 `pytest tests/ -q` 통과 필수.

### I.2 R3 신규 unit/integration tests
| 파일 | 범위 |
|---|---|
| `tests/test_fglc_base_wm.py` | encoder/belief/dynamics shape, forward NaN-free, parameter count 상한 |
| `tests/test_fglc_dataset_state_only.py` | 4 split 생성, forbidden field 0건, episode_len/D_x/D_a 일관성 |
| `tests/test_fglc_trainer_r3_smoke.py` | 1 epoch 후 train loss 감소, metrics.json artifact 형식 |
| `tests/test_fglc_r3_runner_integration.py` | `RepairRunner` Protocol 시그니처, 1 iter end-to-end, ledger.jsonl REQUIRED_KEYS 19개 |

### I.3 CPU fallback
- synthetic toy는 충분히 작아 CUDA 미사용 가능.
- 환경 변수 `FGLC_DEVICE=cpu`로 pytest 분기.
- CI 환경(미정)에서도 동작 가능하도록 설계.

### I.4 4060 VRAM 안전성 검증
- 학습 시작 시 `torch.cuda.set_per_process_memory_fraction(0.85)` 강제.
- 학습 종료 시 `torch.cuda.max_memory_allocated() / 1024**2` → `vram_peak_mib` 기록.
- 6700 MiB(8GB × 0.85) 초과 시 fail-fast → repair loop의 `OOM_FALLBACK_APPLIED` 경로 (4060 path L76-78).

---

## J. Codex TASK 분해안

사용자 지시: **"Step 10을 한 번에 Codex에게 맡기지 마라"**. 다음 5 TASK로 분해, 각 TASK 사이 Claude의 T3 implementation-risk-critic agent 호출.

### TASK 10A (Claude 직접, Codex 위임 ✗)
- 산출: `docs/STEP10A_AUDIT_REPORT.md` (이 PLAN을 토대로 한 정식 audit 문서)
- 산출: `/fglc-phase-check --pass R1` 호출 (사용자 승인 필요)
- 검증: `import src.fglc` smoke, dependencies 결정 (synthetic = h5py/mani-skill 불필요)

### TASK 10B — Config schema + state-only toy dataset (Codex 위임)
```
FILES_ALLOWED:
  configs/fglc/smoke_4060.yaml
  src/fglc/data/__init__.py
  src/fglc/data/state_only_dataset.py
  src/fglc/data/dataloader.py
  tests/test_fglc_dataset_state_only.py
  tests/fixtures/  (디렉터리만)
FILES_FORBIDDEN:
  src/fglc/schemas/   # CLAUDE.md Invariant
  docs/idea/          # 불변
  scripts/run_codex_task.ps1
  .claude/
  CLAUDE.md
ACCEPTANCE_CRITERIA:
  - configs CD-8 적용 (K=6, h=128, batch=16, +dataset/model/trainer/metric 섹션)
  - 4 split shape 검증 통과
  - forbidden field 0건 (assert_no_forbidden_fields)
  - tests 159 + 신규 dataset test PASS
```
검증 후 Claude가 `/fglc-phase-check --pass R2`.

### TASK 10C — Base WM 최소 모듈 (Codex 위임)
```
FILES_ALLOWED:
  src/fglc/models/__init__.py
  src/fglc/models/encoder.py
  src/fglc/models/belief.py
  src/fglc/models/dynamics.py
  src/fglc/models/heads.py  (reward_head + value_head)
  tests/test_fglc_base_wm.py
FILES_FORBIDDEN: (10B와 동일)
ACCEPTANCE_CRITERIA:
  - 3 모듈 shape unit test PASS
  - NaN/Inf 없음
  - docstring에 docs/idea/04 + ROADMAP/04 인용
```

### TASK 10D — Trainer + Evaluator + metrics artifact (Codex 위임)
```
FILES_ALLOWED:
  src/fglc/training/__init__.py
  src/fglc/training/trainer_r3.py
  src/fglc/evaluation/__init__.py
  src/fglc/evaluation/metrics.py
  tests/test_fglc_trainer_r3_smoke.py
FILES_FORBIDDEN: (동일)
ACCEPTANCE_CRITERIA:
  - 1 epoch 학습 후 train loss 감소
  - metrics.json artifact 형식 (E.5 contract)
  - CANONICAL_METRIC_KEYS 정합 (id_nll, train_nll, ...)
  - λ3=0.0 (calibration 비활성) 검증
```

### TASK 10E — R3Runner adapter + repair_loop 연결 (Codex 위임)
```
FILES_ALLOWED:
  src/fglc/runners/__init__.py
  src/fglc/runners/r3_runner.py
  scripts/fglc/r3_smoke.py
  scripts/fglc/repair_loop.py  (mock vs real runner 분기 추가)
  src/fglc/repair/orchestrator.py  (iter_{N}/ artifact 4종 생성 — CD-2 동반)
  tests/test_fglc_r3_runner_integration.py
FILES_FORBIDDEN: (동일)
ACCEPTANCE_CRITERIA:
  - RepairRunner Protocol 시그니처 충족
  - 1 iter end-to-end PASS
  - ledger.jsonl 1줄 REQUIRED_KEYS 19개
  - iter_{N}/ 4종 artifact 생성
  - 기존 65→159 tests + 신규 tests 모두 PASS
  - mock 시나리오 회귀 (--dry-run --mock-scenario improve) 영향 없음
```

### TASK 10F (Claude 직접, Codex 위임 ✗)
- 1-iter real smoke 실제 실행 (`scripts/fglc/r3_smoke.py --phase R3 --config configs/fglc/smoke_4060.yaml --seed 42 --descriptor smoke_synthetic --max-iter 1`)
- `outputs/repair/{loop_id}/ledger.jsonl` 라인 인스펙션
- `docs/STEP10_RESULT_REPORT.md` 작성 — repair loop 흐름 검증 결과, 다음 sub-phase(ManiSkill) 진입 여부 권고

---

## K. BLOCKED / UNKNOWN

### BLOCKED (해결 책임 = Step 10 TASK)
- `src/fglc/models/*` 미구현 → TASK 10C
- `src/fglc/training/*` 미구현 → TASK 10D
- `src/fglc/evaluation/*` 미구현 → TASK 10D
- `src/fglc/data/*` 미구현 → TASK 10B
- `src/fglc/runners/*` 미구현 → TASK 10E
- `configs/fglc/smoke_4060.yaml` 6키 stub → TASK 10B (CD-8 동반)
- `outputs/phase_gates/R1.passed`, `R2.passed` 미생성 → TASK 10A, 10B 종료 시
- `iter_{N}/` artifact 4종 미생성 (CD-2) → TASK 10E

### UNKNOWN (Step 10 범위 밖 또는 실측 후 결정)
- 4060 smoke gate ID NLL ≤ 0.5 nat의 적정성 — `4060_SMOKE_REPAIR_PATH L96` "실측 후 조정". Step 10F 결과 보고에서 재조정 후보.
- R3 정식 ID NLL < 0.1 nat 통과 가능성 — ManiSkill 단계 (Step 10 범위 밖)에서 검증.
- `reward_mse`, `value_loss`를 ledger metric 키로 받는 표준 명명 — Step 10에서 metrics.json 내부 free-form으로 일단 기록, 표준 키 결정은 ManiSkill 단계.
- ledger schema 예시 `id_nll_1step` ↔ diagnose CANONICAL `id_nll` 명명 정합 — TASK 10D/10E에서 `id_nll`로 통일, `docs/EXPERIMENT_LEDGER_SCHEMA.md` 예시 패치 안건 (CD-3).
- pytest 159 vs 사용자 인지값 65 불일치 — Step 9.5 이후 lifecycle/repair tests 누적된 결과로 추정되나 origin 미확인. TASK 10A audit 단계에서 `git log --grep=test` 확인 권장.
- mani-skill / sapien Windows 호환성 — Step 10 범위 밖, ManiSkill 단계 별도 검증.
- R0.passed가 2026-05-22 15:59 생성됐고 R1~R16이 부재한 상태로 dry-run이 진행된 이력 — 본 PLAN은 R1/R2 mini-closure로 정합화하나, R0~R3 sentinel chain의 의미체계 (실제로 무엇이 닫혔다는 증거인지) 재정의가 필요한지 여부는 UNKNOWN.

---

## L. 다음 execute 단계에서 수행할 최소 작업

ExitPlanMode 후 사용자가 execute를 승인하면 다음 순서로 진행:

### Order 1 — TASK 10A (Claude 직접, Codex 위임 ✗)
1. 이 PLAN을 토대로 `docs/STEP10A_AUDIT_REPORT.md` 작성 (audit 결과 + 의존성 결정 + R1/R2 closure 조건 정의)
2. 사용자에게 "R1.passed 생성 승인" 명시적 요청
3. 승인 시 `/fglc-phase-check --pass R1` 호출

### Order 2 — TASK 10B (Codex 위임)
4. `.agent_tasks/codex_queue/TASK_10B_R2_state_only_toy_dataset.md` 작성 (10 헤더 + RELATED_AGENT_REPORT_IDS)
5. `scripts/run_codex_task.ps1 -Mode run -TaskName TASK_10B -TaskFile <path> -BypassSandbox` 실행
6. T3 implementation-risk-critic + fglc-code-reviewer agent 호출, PASS 확인
7. Gatekeeper 6 조건 충족 시 accept commit, `/fglc-phase-check --pass R2`

### Order 3 — TASK 10C (Codex 위임)
8. `.agent_tasks/codex_queue/TASK_10C_base_wm_modules.md` 작성
9. 실행 → T3 audit → accept

### Order 4 — TASK 10D (Codex 위임)
10. `.agent_tasks/codex_queue/TASK_10D_trainer_evaluator_metrics.md` 작성
11. 실행 → T3 audit → accept

### Order 5 — TASK 10E (Codex 위임)
12. `.agent_tasks/codex_queue/TASK_10E_r3_runner_repair_integration.md` 작성
13. 실행 → T3 audit → accept

### Order 6 — TASK 10F (Claude 직접)
14. `scripts/fglc/r3_smoke.py --phase R3 --config configs/fglc/smoke_4060.yaml --seed 42 --descriptor smoke_synthetic --max-iter 1` 실행 (사용자 승인 필요)
15. ledger.jsonl + iter_{0}/ artifact 인스펙션
16. `docs/STEP10_RESULT_REPORT.md` 작성 — synthetic 단계 PASS/FAIL + ManiSkill 단계 진입 권고

### 절대 하지 말 것 (사용자 지시)
- `outputs/phase_gates/R3.passed` 생성 금지 (synthetic만으로는 R3 gate 통과로 간주 불가)
- ManiSkill / DROID / BridgeData / RGB-D / baseline grid 시작 금지
- `docs/idea/`, `docs/ROADMAP/` 임의 수정 금지 (불변 파일)
- empirical result 추측 또는 fake number 기록 금지
- smoke 실패를 최종 결론으로 사용 금지 — 실패는 반드시 repair loop의 입력으로 변환
- FGLC 핵심 주장(falsification / standardized mismatch / latent group / causal attention 등) 성패 판단 금지 (R3 smoke는 base WM 단계, falsification은 R4 이후)

---

## 검증 (verification)

이 PLAN이 실제로 진행 가능한지 확인할 방법:

1. **현재 159 tests passed 재확인**:
   ```powershell
   .\.venv\Scripts\python.exe -m pytest tests/ -q
   ```
   기대: `159 passed`.

2. **Step 9.5 ledger 신구조 재확인**:
   ```powershell
   Get-ChildItem outputs\repair -Recurse -Filter ledger.jsonl
   ```
   기대: 7개 이상의 `loop_*/ledger.jsonl`.

3. **phase_gates 상태 재확인**:
   ```powershell
   Get-ChildItem outputs\phase_gates
   ```
   기대: `R0.passed` 단 1개 (R1.passed부터 TASK 10A 종료 시 생성).

4. **forbidden field SSoT 재확인**:
   ```powershell
   .\.venv\Scripts\python.exe -m pytest tests/test_fglc_forbidden_field_sync.py -q
   ```
   기대: PASS.

5. **각 TASK 종료 후 회귀 검증**:
   - 159 + 신규 tests PASS
   - `pytest tests/test_fglc_repair_*.py -q` 9개 모두 green 유지
   - forbidden field 0건

6. **TASK 10F 종료 후 최종 검증**:
   ```powershell
   .\.venv\Scripts\python.exe scripts\fglc\r3_smoke.py --phase R3 --config configs\fglc\smoke_4060.yaml --seed 42 --descriptor smoke_synthetic --max-iter 1 --max-wall-clock-minutes 60 --output-root outputs\repair
   Get-Content outputs\repair\loop_*\ledger.jsonl | ConvertFrom-Json | Format-List
   ```
   기대: 1줄, `phase="R3"`, REQUIRED_KEYS 19개, `result ∈ {accept, reject, inconclusive}`, `failed_metric="id_nll"`, `metrics_before` / `metrics_after`에 `id_nll`/`train_nll`/`val_nll` 등 키.

---

## 핵심 파일 reference

### Plan 입력으로 직접 인용된 파일
- `CLAUDE.md` (Invariant Preservation, Codex Orchestration Precedence)
- `.claude/rules/behavioral_coding_rules.md` (§5 Fragile File Invariants)
- `.claude/rules/codex_orchestration_rules.md` (Gatekeeper 6 조건, 절대 수정 금지 경로)
- `docs/ROADMAP/00_ROADMAP_OVERVIEW.md` (R0~R16, R3 위치 L16)
- `docs/ROADMAP/04_PHASE_R3_BASE_WORLD_MODEL.md` (아키텍처 L13-24, gate L35-42)
- `docs/ROADMAP/03_PHASE_R2_DATA_PIPELINE.md` (data schema, OOD 축)
- `docs/ROADMAP/4060_SMOKE_REPAIR_PATH.md` (L22-33, L62-90, L96, L146-154)
- `docs/EXPERIMENT_REPAIR_LOOP_PLAN.md` (D.1, D.3 L141, D.5, §G H4 L268-270)
- `docs/EXPERIMENT_LEDGER_SCHEMA.md` (REQUIRED_KEYS L17-37, schema 예시 L50-56)
- `docs/STEP9_DRY_RUN_REPAIR_LOOP_REPORT.md` (CD-1~CD-9)
- `docs/STEP9_PATCH_PLAN.md` (CD-1 패치 명세, §9 Step 10 진입 직전 액션)
- `docs/STEP9_5_PATCH_RESULT_REPORT.md` (STEP9.5_PASS, §13, §14 미처리 CD)
- `docs/idea/04_BASE_WORLD_MODEL.md` (L18-38, C5 L73, C8 L76-77)
- `docs/idea/10_LOSS_DESIGN.md` (Stage 1 loss L18-32, C7 L61)
- `docs/idea/12_TRAINING_STAGES.md` (Stage 1 gate L19, C8 L67-68)
- `docs/idea/18_DATA_BENCHMARKS.md` (L15-35, forbidden L25-34)
- `docs/idea/21_METRICS.md` (4축, L13-19, 보고 요건 L60-65)
- `src/fglc/__init__.py:7-17` (R1~R8 모듈 약속만 존재)
- `src/fglc/schemas/visibility.py:18-31` (FORBIDDEN_AGENT_FIELDS 12개)
- `src/fglc/repair/orchestrator.py:74-85` (RepairRunner Protocol), `:220` (run_repair_loop), `:203-210` (_gate_passed)
- `src/fglc/repair/diagnose.py:10-27` (CANONICAL_METRIC_KEYS), `:111` (diagnose)
- `src/fglc/repair/candidates.py:24-80` (R3 patch keys)
- `src/fglc/repair/ledger.py:17-37` (REQUIRED_KEYS 19), `:39-48` (result, stop_condition)
- `scripts/fglc/repair_loop.py:37-62` (argparse), `:84` (id_nll default 0.4 CD-4), `:94-136` (build_mock_runner)
- `configs/fglc/smoke_4060.yaml` (6 lines, CD-8 미해결)
- `pyproject.toml` (L11-28 deps, [maniskill]/[rl]/[rlds] extras)
- `requirements.txt` (torch 2.6.0+cu124, numpy 2.1.3, 154 pins, h5py/hydra 미핀)
- `.gitignore` (L40 outputs/*, L98-102 phase_gates 예외, L140 repair/.gitkeep negate)
