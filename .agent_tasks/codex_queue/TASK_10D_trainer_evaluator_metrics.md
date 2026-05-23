TASK_NAME: TASK_10D_trainer_evaluator_metrics
SANDBOX_MODE: bypass

BACKGROUND:
FGLC Step 10D. pytest 173 passed.
src/fglc/models/ (Encoder, BeliefMemory, GroupedDynamics, RewardHead, ValueHead) 완료.
src/fglc/data/ (SyntheticToyDataset, make_dataloaders) 완료.
configs/fglc/smoke_4060.yaml 완성 (K=6, h_dim=128, batch_size=16, dataset/model/trainer/metric).

이 TASK는 Stage 1 trainer와 evaluator + metrics.json artifact를 구현한다.
Stage 1 loss = L_base_dynamics + λ1·L_reward + λ2·L_value + λ3·L_calibration
smoke 단계에서 λ3=0.0 (calibration 비활성).
Source: docs/idea/10_LOSS_DESIGN.md Stage 1 (L18-32)

중요: CD-3 해결 — metric 키 명명은 diagnose.py::CANONICAL_METRIC_KEYS의 키를 따른다:
  id_nll, train_nll, val_nll (추가 명시), val_train_nll_gap, stagnant_epochs,
  kstep_nll_slope, ood_mass_nll, ood_friction_nll, ood_id_nll_diff

GOAL:
1. src/fglc/training/__init__.py 생성 (export: TrainerR3, TrainerConfig)
2. src/fglc/training/trainer_r3.py 구현:
   - TrainerConfig dataclass: batch_size, train_horizon, epochs, learning_rate, optimizer, loss_weights, device
   - TrainerR3(model_config: dict, trainer_config: TrainerConfig, device: str)
   - build 메서드: Encoder, BeliefMemory, GroupedDynamics, RewardHead, ValueHead 인스턴스 생성
   - train(train_loader, val_loader) -> dict (metrics dict, CANONICAL_METRIC_KEYS 서브셋)
   - 1-step Gaussian NLL loss: L_dyn = -log N(z_{t+1}; mu_t, exp(2*log_sigma_t))
     구현: 0.5 * (log(2π) + 2*log_sigma + (z_next - mu)^2 / exp(2*log_sigma))
   - L_reward = F.mse_loss(r_hat, r_true)
   - L_value = F.mse_loss(v_hat, mc_return)
     mc_return: 간단한 cumulative sum (no discount, smoke 단계)
   - L_total = L_dyn + λ1*L_reward + λ2*L_value
   - torch.cuda.set_per_process_memory_fraction(0.85) 호출 (CUDA 사용 시)
   - 매 epoch마다 train_nll, val_nll, train_loss 기록
   - stagnant_epochs: val_nll이 개선되지 않는 연속 epoch 수
3. src/fglc/evaluation/__init__.py 생성 (export: Evaluator, evaluate_model)
4. src/fglc/evaluation/metrics.py 구현:
   - evaluate_model(trainer: TrainerR3, dataloaders: dict, model_config: dict, trainer_config: TrainerConfig) -> dict
   - 반환 dict 키 (모두 CANONICAL_METRIC_KEYS 서브셋):
     - id_nll: float (val_id DataLoader 기준 1-step NLL)
     - train_nll: float (train_id DataLoader 기준)
     - val_nll: float (= id_nll, alias)
     - val_train_nll_gap: float (= val_nll - train_nll)
     - stagnant_epochs: int
     - kstep_nll_slope: float (k=1,2,4,8 multi-step NLL의 선형 회귀 기울기)
     - ood_mass_nll: float
     - ood_friction_nll: float
     - ood_id_nll_diff: float (= mean(ood_mass_nll, ood_friction_nll) - id_nll)
     - epoch: int (최종 epoch 수)
     - wall_clock_minutes: float
     - vram_peak_mib: float (CUDA 미사용 시 0.0)
   - metrics.json 저장 (output_dir / "metrics.json")
5. tests/test_fglc_trainer_r3_smoke.py 작성:
   - test_train_loss_decreases: 1 epoch 후 loss가 initial보다 낮거나 같음 (≤ init * 1.05 tolerance)
   - test_metrics_json_schema: evaluate_model 후 metrics.json 존재, 필수 키 모두 포함
   - test_canonical_keys_match: metrics dict 키가 CANONICAL_METRIC_KEYS의 서브셋인지 (초과 키 없음)
   - test_ood_nll_gap: ood_id_nll_diff는 float (sign 방향은 체크하지 않음, smoke 단계)
   - test_val_train_nll_gap_nonnegative: val_train_nll_gap >= -0.5 (overfitting 없음, smoke 단계 관대 허용)
   - test_cpu_device_works: device='cpu'로 TrainerR3 전체 실행 PASS (CUDA 없이도 동작)

FILES_ALLOWED:
src/fglc/training/__init__.py
src/fglc/training/trainer_r3.py
src/fglc/evaluation/__init__.py
src/fglc/evaluation/metrics.py
tests/test_fglc_trainer_r3_smoke.py

FILES_FORBIDDEN:
src/fglc/schemas/
src/fglc/data/
src/fglc/repair/
src/fglc/models/
src/fglc/__init__.py
docs/idea/
docs/ROADMAP/
scripts/run_codex_task.ps1
.claude/
CLAUDE.md
.mcp.json
.env
configs/

REQUIRED_IMPLEMENTATION:
trainer_r3.py forward pass 구조:
  z = encoder(state)                        # [B,T,K,d]
  h = belief(z, action, reward)             # [B,T,h_dim]
  mu, log_sigma = dynamics(z, action, h)    # [B,T,K,d] each
  z_next_pred = mu[:, :-1]                  # 1-step prediction (shift by 1)
  z_next_target = z[:, 1:].detach()         # [B,T-1,K,d]
  L_dyn = gaussian_nll(z_next_target, mu[:, :-1], log_sigma[:, :-1])
  z_flat = z.flatten(-2, -1)                # [B,T,K*d]
  r_hat = reward_head(z_flat, action, h)    # [B,T]
  v_hat = value_head(z_flat, h)             # [B,T]
  mc_return = compute_mc_return(reward)     # [B,T] (no discount)
  L_reward = F.mse_loss(r_hat, reward)
  L_value = F.mse_loss(v_hat, mc_return)
  L_total = L_dyn + lambda_reward * L_reward + lambda_value * L_value

gaussian_nll 구현:
  var = torch.exp(2 * log_sigma)
  return 0.5 * (math.log(2 * math.pi) + 2 * log_sigma + (target - mu).pow(2) / var).mean()

compute_mc_return(reward: Tensor[B,T]) -> Tensor[B,T]:
  mc = torch.zeros_like(reward)
  cumsum = torch.zeros(reward.shape[0], device=reward.device)
  for t in range(reward.shape[1] - 1, -1, -1):
      cumsum = cumsum + reward[:, t]
      mc[:, t] = cumsum
  return mc

metrics.json 저장 경로:
  output_dir argument (default: Path("outputs") / "repair" / "metrics_tmp")
  또는 caller가 지정한 경로

REQUIRED_TESTS:
tests/test_fglc_trainer_r3_smoke.py 6개 PASS.
기존 173 tests 중 test_lifecycle_phase2_hooks.py 제외 회귀 없음.
(lifecycle hook 테스트는 worktree 구조상 .claude/ 부재로 실패하며 TASK 범위 외다.)

ACCEPTANCE_CRITERIA:
1. pytest tests/test_fglc_trainer_r3_smoke.py → 6 passed (device='cpu' 모든 테스트)
2. 1 epoch 후 train_nll <= epoch_0_nll (loss 감소 또는 유지)
3. metrics.json에 id_nll, train_nll, val_nll, val_train_nll_gap, stagnant_epochs,
   kstep_nll_slope, ood_mass_nll, ood_friction_nll, ood_id_nll_diff,
   epoch, wall_clock_minutes, vram_peak_mib 모두 존재
4. 과학적 metric 키 모두 CANONICAL_METRIC_KEYS 서브셋.
   operational artifact 키 (epoch, wall_clock_minutes, vram_peak_mib)는
   src/fglc/repair/diagnose.py::ARTIFACT_KEYS에 선언되어 있으며 metrics.json에 포함 허용.
5. src/fglc/schemas/ 미수정
6. docstring에 "docs/idea/10_LOSS_DESIGN" 문자열 포함

COMMIT_MESSAGE:
feat(training): add trainer_r3 + evaluator + metrics.json artifact (TASK_10D, CD-3)

STOP_CONDITION:
- src/fglc/schemas/, src/fglc/models/, src/fglc/data/, configs/ 수정 시 즉시 중단
- CANONICAL_METRIC_KEYS 또는 ARTIFACT_KEYS 에 없는 새 키를 metrics에 추가하지 마라 (id_nll_1step 등 비표준 키 금지)
- CANONICAL_METRIC_KEYS = id_nll, train_nll, val_nll, val_train_nll_gap, stagnant_epochs, kstep_nll_slope, ood_mass_nll, ood_friction_nll, ood_id_nll_diff (및 기타)
- ARTIFACT_KEYS = epoch, wall_clock_minutes, vram_peak_mib
- calibration loss 구현 금지 (λ3=0.0 smoke 단계 — 파일은 만들지 않는다)
- 기존 173 tests (lifecycle 제외) 추가 실패 시 즉시 중단

RELATED_AGENT_REPORT_IDS: docs/STEP10A_AUDIT_REPORT.md
