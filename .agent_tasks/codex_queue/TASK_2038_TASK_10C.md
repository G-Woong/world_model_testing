TASK_NAME: TASK_10C_base_wm_modules
SANDBOX_MODE: bypass

BACKGROUND:
FGLC (Falsification-Guided Latent Correction) Step 10C.
R2.passed sentinel 존재. 현재 pytest 165 passed.

이 TASK는 R3 base world model의 최소 모듈 3개를 구현한다:
- Encoder: grouped latent encoder (MLP, K=6, d=32)
- Belief: GRU belief memory (h_dim=128)
- Dynamics: per-group MLP dynamics (μ, logσ 예측)
- Heads: reward_head + value_head

smoke 단계이므로 group transformer (2-layer)는 구현하지 않는다. per-group MLP만.
Step 10 PLAN §G "group transformer는 DEFERRED" 명시.

GOAL:
1. src/fglc/models/__init__.py 생성 (export list: Encoder, BeliefMemory, GroupedDynamics, RewardHead, ValueHead)
2. src/fglc/models/encoder.py 구현:
   - Encoder(D_x: int, K: int = 6, d: int = 32, hidden: int = 256)
   - forward(state: Tensor[B,T,D_x]) -> Tensor[B,T,K,d]
   - MLP: D_x → 256 → 256 → K*d, with LayerNorm + SiLU
   - reshape to [B,T,K,d]
3. src/fglc/models/belief.py 구현:
   - BeliefMemory(K: int = 6, d: int = 32, D_a: int = 4, h_dim: int = 128)
   - forward(z: Tensor[B,T,K,d], action: Tensor[B,T,D_a], reward: Tensor[B,T]) -> Tensor[B,T,h_dim]
   - GRU input: flatten(z_t) + action_{t-1} + reward_{t-1}  (concat dim = K*d + D_a + 1)
   - 첫 타임스텝의 action_{t-1}/reward_{t-1}은 zeros
   - nn.GRU(input_size=K*d+D_a+1, hidden_size=h_dim, num_layers=1, batch_first=True)
4. src/fglc/models/dynamics.py 구현:
   - GroupedDynamics(K: int = 6, d: int = 32, D_a: int = 4, h_dim: int = 128, hidden: int = 64)
   - forward(z: Tensor[B,T,K,d], action: Tensor[B,T,D_a], h: Tensor[B,T,h_dim]) -> tuple[Tensor[B,T,K,d], Tensor[B,T,K,d]]
   - 반환: (mu, log_sigma) — both shape [B,T,K,d]
   - per-group MLP: Linear(d + h_dim + D_a, 64) → SiLU → Linear(64, 2*d) → split (mu, log_sigma)
   - K개의 group을 nn.ModuleList로 보관
5. src/fglc/models/heads.py 구현:
   - RewardHead(K: int = 6, d: int = 32, D_a: int = 4, h_dim: int = 128, hidden: int = 64)
     forward(z_flat: Tensor[B,T,K*d], action: Tensor[B,T,D_a], h: Tensor[B,T,h_dim]) -> Tensor[B,T]
     MLP: K*d + D_a + h_dim → 64 → SiLU → 1
   - ValueHead(K: int = 6, d: int = 32, h_dim: int = 128, hidden: int = 64)
     forward(z_flat: Tensor[B,T,K*d], h: Tensor[B,T,h_dim]) -> Tensor[B,T]
     MLP: K*d + h_dim → 64 → SiLU → 1
6. tests/test_fglc_base_wm.py 작성:
   - test_encoder_shape: Encoder forward shape [B,T,K,d]
   - test_belief_shape: BeliefMemory forward shape [B,T,h_dim]
   - test_dynamics_shape: GroupedDynamics forward shape (mu, log_sigma) 둘 다 [B,T,K,d]
   - test_reward_head_shape: RewardHead forward shape [B,T]
   - test_value_head_shape: ValueHead forward shape [B,T]
   - test_no_nan_forward: 정상 입력에서 NaN/Inf 없음 (all 5 modules)
   - test_parameter_count: 전체 파라미터 수 < 2M (toy 규모 상한)
   - test_docstring_source_present: 각 모듈 __doc__에 "docs/idea/04_BASE_WORLD_MODEL" 문자열 존재

FILES_ALLOWED:
src/fglc/models/__init__.py
src/fglc/models/encoder.py
src/fglc/models/belief.py
src/fglc/models/dynamics.py
src/fglc/models/heads.py
tests/test_fglc_base_wm.py

FILES_FORBIDDEN:
src/fglc/schemas/
src/fglc/data/
src/fglc/repair/
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
모든 모듈에 다음 docstring 형식 필수:
  """
  Source: docs/idea/04_BASE_WORLD_MODEL.md, docs/ROADMAP/04_PHASE_R3_BASE_WORLD_MODEL.md
  ...
  """

Encoder:
  - LayerNorm은 각 Linear 뒤 (Linear → LayerNorm → SiLU) 패턴 x2, 마지막은 Linear만
  - 최종 출력 reshape: view(B, T, K, d)

BeliefMemory:
  - 첫 타임스텝 shifted input: action_{t-1} = zeros, reward_{t-1} = 0
  - GRU 출력 h: [B,T,h_dim] (batch_first=True)

GroupedDynamics:
  - per-group Linear(d + h_dim + D_a, hidden) → SiLU → Linear(hidden, 2*d)
  - split: mu = out[..., :d], log_sigma = out[..., d:]
  - loop over K groups (또는 vmap, 어느 쪽이든 동일 output)

REQUIRED_TESTS:
tests/test_fglc_base_wm.py 8개 PASS.
기존 165 tests 중 test_lifecycle_phase2_hooks.py 제외 회귀 없음.
(lifecycle hook 테스트는 worktree 구조상 .claude/ 부재로 실패하며 TASK 범위 외다.)

ACCEPTANCE_CRITERIA:
1. pytest tests/test_fglc_base_wm.py → 8 passed
2. encoder output shape: [4, 8, 6, 32] (B=4, T=8, K=6, d=32)
3. belief output shape: [4, 8, 128]
4. dynamics (mu, log_sigma) shape: [4, 8, 6, 32] 각각
5. reward_head shape: [4, 8]
6. value_head shape: [4, 8]
7. NaN/Inf 없음 — 정상 rand 입력에 대해
8. 전체 파라미터 수 < 2M (encoder+belief+dynamics+heads 합산)
9. 각 모듈 __doc__에 "docs/idea/04_BASE_WORLD_MODEL" 포함
10. src/fglc/schemas/ 미수정
11. 기존 165 tests 중 lifecycle hook 제외 회귀 없음

COMMIT_MESSAGE:
feat(models): add encoder/belief/dynamics/heads base WM modules (TASK_10C, R3 smoke step)

STOP_CONDITION:
- src/fglc/schemas/ 또는 configs/ 수정 시 즉시 중단
- group transformer 구현 시도 시 중단 (DEFERRED — smoke 단계는 per-group MLP만)
- 기존 165 tests (lifecycle 제외) 중 하나라도 추가 실패 시 즉시 중단
- 모듈 파라미터 수 > 5M이면 즉시 중단 (8GB VRAM 경로 이탈)

RELATED_AGENT_REPORT_IDS: docs/STEP10A_AUDIT_REPORT.md
