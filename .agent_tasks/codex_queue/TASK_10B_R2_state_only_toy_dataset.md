TASK_NAME: TASK_10B_R2_state_only_toy_dataset
SANDBOX_MODE: bypass

BACKGROUND:
FGLC (Falsification-Guided Latent Correction) Step 10B.
R1.passed sentinel이 생성되었으며 (outputs/phase_gates/R1.passed 존재),
현재 pytest 159 passed (회귀 없음).

이 TASK는 두 가지를 처리한다:
(1) configs/fglc/smoke_4060.yaml 확장 (CD-8: 6-line stub → 전체 schema)
(2) synthetic toy state-only dataset 구현 + tests 작성 (R2 mini-closure)

synthetic toy 경로는 torch + numpy만 사용한다. h5py / hydra / mani-skill / sapien 불필요.

과학적 계약:
- FORBIDDEN_AGENT_FIELDS (src/fglc/schemas/visibility.py:18-31, 12 fields): 
  regime_id, true_mass, true_friction, true_latency, true_noise_sigma,
  true_action_gain, oracle_action, counterfactual_reward, split_id, ood_type, seed, template_id
- 위 필드는 inference/training input에 절대 포함되면 안 된다.
- assert_no_forbidden_fields(batch) 검증 통과 필수.

GOAL:
1. configs/fglc/smoke_4060.yaml을 dataset/model/trainer/metric 섹션 포함 전체 schema로 확장 (CD-8)
2. src/fglc/data/__init__.py 생성 (빈 패키지 init)
3. src/fglc/data/state_only_dataset.py 구현:
   - SyntheticToyDataset 클래스
   - 4 split 생성: train_id (n=32), val_id (n=8), ood_mass (n=16), ood_friction (n=16)
   - trajectory: x_{t+1} = mass * A@x_t + friction * B@a_t + N(0, sigma^2)
   - reward: r_t = -0.1 * ||x_t||^2 - 0.01 * ||a_t||^2
   - done: all False (episode_len 내에서 종료 없음)
   - 반환 batch dict: {"state": [B,T,D_x], "action": [B,T,D_a], "reward": [B,T], "done": [B,T]}
   - 허용 필드 4개만: state, action, reward, done
   - assert_no_forbidden_fields(batch) 내부 호출로 leakage 강제 방지
4. src/fglc/data/dataloader.py 구현:
   - make_dataloaders(config: dict) -> dict[str, DataLoader]
   - config의 dataset 섹션 파라미터 사용
   - torch DataLoader 반환 (train_id, val_id, ood_mass, ood_friction 4개 키)
5. tests/test_fglc_dataset_state_only.py 작성:
   - test_four_split_shapes: 4 split 각각 shape 검증
   - test_forbidden_field_absent: assert_no_forbidden_fields(batch) 통과
   - test_episode_len_consistent: episode_len=64 일관성
   - test_dx_da_consistent: D_x=8, D_a=4 일관성
   - test_reward_is_negative: reward <= 0 (MSE 기반 음수 보상)
   - test_dataloader_batch_shape: batch_size=16, T=8 DataLoader batch shape 검증
6. tests/fixtures/ 디렉터리 생성 (빈 __init__.py 포함)

FILES_ALLOWED:
configs/fglc/smoke_4060.yaml
src/fglc/data/__init__.py
src/fglc/data/state_only_dataset.py
src/fglc/data/dataloader.py
tests/test_fglc_dataset_state_only.py
tests/fixtures/__init__.py

FILES_FORBIDDEN:
src/fglc/schemas/
docs/idea/
docs/ROADMAP/
scripts/run_codex_task.ps1
.claude/
CLAUDE.md
.mcp.json
.env
src/fglc/repair/
src/fglc/__init__.py

REQUIRED_IMPLEMENTATION:
1. configs/fglc/smoke_4060.yaml — 전체 schema:

```yaml
phase: R3
seed: 42
device: cuda  # fallback to cpu if cuda unavailable

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
  sigma: 0.1

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
  learning_rate: 3.0e-4
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

2. SyntheticToyDataset:
- __init__(self, n_episodes, episode_len, D_x, D_a, mass=1.0, friction=1.0, sigma=0.1, seed=42)
- A, B matrix: 고정 seed로 생성 (np.random.default_rng(seed).normal(0, 0.1, size=(D_x, D_x)) 등)
- A를 stable dynamics로 만들기: A = A - np.eye(D_x) * 0.5 (eigenvalue < 1 보장)
- 생성: x0 = rng.normal(0, 1, (n_episodes, D_x))
- step: x_{t+1} = mass * A @ x_t + friction * B @ a_t + N(0, sigma^2)
- action: rng.uniform(-1, 1, (n_episodes, episode_len, D_a))
- reward: -0.1 * np.sum(x_t**2, axis=-1) - 0.01 * np.sum(a_t**2, axis=-1)
- done: np.zeros((n_episodes, episode_len), dtype=bool)
- __getitem__: episode i를 {"state": Tensor[T,D_x], "action": Tensor[T,D_a], "reward": Tensor[T], "done": Tensor[T]} 반환
- __len__: n_episodes
- 내부에서 assert_no_forbidden_fields 호출 (import from fglc.schemas.visibility)
- docstring: "Source: docs/ROADMAP/03_PHASE_R2_DATA_PIPELINE.md, docs/ROADMAP/4060_SMOKE_REPAIR_PATH.md §Step 10 synthetic"

3. make_dataloaders(config: dict) -> dict[str, DataLoader]:
- config["dataset"]에서 파라미터 읽기
- 4개 DataLoader 반환: train_id, val_id, ood_mass, ood_friction
- shuffle=True (train_id만), num_workers=0 (Windows 호환)
- batch_size = config["trainer"]["batch_size"]

REQUIRED_TESTS:
tests/test_fglc_dataset_state_only.py 6개 테스트 모두 PASS.
기존 159 tests 회귀 없음 (pytest tests/ -q 결과 159+신규 모두 PASS).

ACCEPTANCE_CRITERIA:
1. pytest tests/ 결과: 기존 159 + 신규 최소 6개 PASS (총 165+)
2. configs/fglc/smoke_4060.yaml에 dataset/model/trainer/metric 4개 섹션 존재
3. K=6, h_dim=128, batch_size=16 값 확인 (CD-8 반영)
4. SyntheticToyDataset.__getitem__ 반환 batch에 forbidden field 0건
5. 4 split shape: state [n,64,8], action [n,64,4], reward [n,64], done [n,64]
6. DataLoader batch shape: state [16,8,8] (batch=16, T=8, D_x=8)
7. FGLC 예약 용어 rename 없음 (falsification, standardized mismatch 등)
8. src/fglc/schemas/ 및 docs/idea/ 미수정

COMMIT_MESSAGE:
feat(data): add synthetic toy state-only dataset + config CD-8 (TASK_10B, R2 closure)

STOP_CONDITION:
- forbidden field가 dataset에서 감지되면 즉시 중단, 보고
- h5py / hydra / mani-skill import가 필요해지면 즉시 중단 (synthetic 경로는 torch + numpy만)
- 기존 159 tests 중 하나라도 깨지면 즉시 중단
- configs/fglc/smoke_4060.yaml의 K < 6 또는 h_dim < 128이면 즉시 중단 (4060 VRAM 경로 이탈)

RELATED_AGENT_REPORT_IDS: docs/STEP10A_AUDIT_REPORT.md
