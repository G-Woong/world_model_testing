결론: **네 아이디어는 “기존 월드모델 하나를 그냥 쓰는 것”이 아니라, TD-MPC2/Dreamer류의 latent world model 위에 `falsification detector + causalized attention + sparse latent correction + action/value validation`을 얹는 구조로 설계해야 한다.**
가장 안전한 1차 구현은 **ManiSkill state-only 환경에서 TD-MPC2식 decoder-free latent dynamics를 기본 골격으로 차용하고, 그 위에 네 모듈을 붙이는 방식**이다. TD-MPC2는 learned implicit latent world model 위에서 latent-space local trajectory optimization을 수행하는 model-based RL 계열이고, 104개 continuous-control task에서 강한 기준선으로 보고된 바 있다. ([arXiv][1])

아래는 네가 지금 설계해야 하는 전체 지식 체계를 “논문용 아키텍처 설계서” 수준으로 풀어쓴 것이다.

---

# 0. 먼저 네 아이디어를 한 문장으로 고정해야 함

네 방법은 이렇게 정의하는 게 제일 좋다.

> **현재 world model의 예측분포가 실제 관측 전이와 통계적으로 불일치할 때, 이를 dynamics hypothesis의 falsification으로 보고, mismatch가 행동/value 예측에 영향을 주는 latent subspace를 causalized attention으로 선택한 뒤, 그 subspace에만 sparse residual correction을 적용한다.**
> 

이 문장을 풀면 네 시스템은 4개 문제를 푼다.

```
1. 현재 world model이 틀렸는가?
2. 틀렸다면 전체 latent 중 어디가 문제인가?
3. 그 부분을 얼마나 고쳐야 하는가?
4. 고친 결과가 실제 행동 선택과 보상 회복에 도움이 되는가?
```

즉 네 논문은 단순히 “attention을 쓴 world model”이 아니다.

```
기존 world model:
latent dynamics를 학습하고 planning한다.

네 world model:
latent dynamics가 틀렸을 때,
그 틀림을 통계적으로 감지하고,
어떤 latent subspace를 얼마나 교정해야 할지 학습한다.
```

---

# 1. 어떤 기존 월드모델을 차용해야 하나?

## 1.1 제일 추천: TD-MPC2 계열을 base로 삼아라

너는 지금 “현실 동역학 상태 latent vector 간 상호작용”을 다루고 있다.
이 경우 처음부터 이미지 기반 Dreamer 전체를 구현하면 복잡도가 터질 가능성이 높다.

그래서 1차 실험은 이쪽이 맞다.

```
환경: ManiSkill / robosuite
입력: state vector
기본 world model: TD-MPC2-style decoder-free latent dynamics
planning: latent space MPPI/CEM/local trajectory optimization
추가 모듈: falsification + causalized attention + correction
```

TD-MPC2류의 핵심은 **픽셀을 복원하는 decoder를 반드시 두지 않고**, control에 필요한 latent를 만들고 그 latent 위에서 planning한다는 점이다. 이게 네 목적과 잘 맞는다. 네가 원하는 것은 “이미지를 예쁘게 복원하는 latent”가 아니라 **행동 결과를 예측하고 교정할 수 있는 latent**이기 때문이다. TD-MPC2는 learned implicit decoder-free latent world model과 latent-space local trajectory optimization을 핵심으로 한다. ([arXiv][1])

## 1.2 대안: Dreamer/RSSM 계열

Dreamer/PlaNet 계열은 recurrent state-space model, 즉 RSSM 기반이다. PlaNet은 deterministic transition component와 stochastic transition component를 함께 쓰는 latent dynamics model로 planning from pixels를 수행했고, DreamerV3는 환경 모델을 학습한 뒤 imagined future를 통해 행동을 개선하는 일반 world model algorithm으로 소개된다. ([arXiv][2])

Dreamer/RSSM이 유리한 경우는 이거다.

```
1. 관측이 partial observable이다.
2. 이미지/RGB-D를 직접 쓴다.
3. 과거 history 없이는 현재 상태를 알기 어렵다.
4. hidden regime이 천천히 바뀐다.
```

하지만 네 첫 실험에서는 Dreamer 전체 구현보다 TD-MPC2식이 낫다.

```
처음부터 Dreamer:
이미지 encoder + RSSM + decoder + actor-critic + imagination training까지 필요
→ 복잡도 높음

처음은 TD-MPC2-style:
state encoder + latent dynamics + reward/value + planner
→ 핵심 아이디어 검증에 집중 가능
```

## 1.3 최종 추천 골격

내 추천은 **hybrid**다.

```
Base:
TD-MPC2-style decoder-free latent world model

Add:
RSSM-like belief memory h_t

Novel module:
Falsification-guided attention correction
```

즉 구조는 이렇게 간다.

```
observation/state x_t
      ↓
encoder E
      ↓
factorized latent z_t
      ↓
belief memory h_t
      ↓
base dynamics fθ
      ↓
predicted distribution p(z_{t+1}|z_t, a_t)
      ↓
standardized mismatch
      ↓
causalized attention α_t
      ↓
sparse correction δ_t
      ↓
corrected latent prediction
      ↓
reward/value/planning
```

---

# 2. 입력 데이터는 어떤 구조로 들어와야 하나?

ManiSkill을 기준으로 보면 observation mode는 `state_dict`, `sensor_data`, `state+sensor_data`, `rgb+depth`, `rgb+depth+segmentation`, `pointcloud` 등으로 구성할 수 있다. `state_dict`에는 robot proprioception, joint position `qpos`, joint velocity `qvel`, task-specific extra information 등이 들어가고, `rgb+depth+segmentation`에서는 RGB, depth, segmentation 같은 camera tensor도 받을 수 있다. ([ManiSkill][3])

1차 실험은 반드시 **state-only**로 가라.

예를 들어 한 timestep 데이터는 이렇게 생긴다.

```python
transition_t = {
    "state": x_t,          # shape: [D_x]
    "action": a_t,         # shape: [D_a]
    "next_state": x_tp1,   # shape: [D_x]
    "reward": r_t,         # scalar
    "done": d_t,           # scalar
    "success": s_t,        # optional scalar
    "regime_id": g_t       # optional, training에는 안 쓰고 eval에만 사용
}
```

ManiSkill state vector 예시는 대략 이렇게 분해된다.

```
x_t =
[
  robot_qpos,          # 관절 위치
  robot_qvel,          # 관절 속도
  tcp_pose,            # end-effector 위치/자세
  gripper_state,       # gripper open/close
  object_pose,         # object 위치/자세
  object_velocity,     # object 속도
  goal_pose,           # 목표 위치
  task_extra           # success condition 관련 값
]
```

action은 manipulation task에서 보통 이런 구조다.

```
a_t =
[
  Δx, Δy, Δz,
  Δroll, Δpitch, Δyaw,
  gripper_command
]
```

즉 shape 예시는:

```
x_t: [D_x] = [64] 또는 [80] 또는 [120]
a_t: [D_a] = [4] 또는 [7]
r_t: scalar
done_t: scalar
```

데이터셋 batch는 이렇게 만든다.

```
batch_x:      [B, T, D_x]
batch_a:      [B, T, D_a]
batch_r:      [B, T, 1]
batch_done:   [B, T, 1]
batch_success:[B, T, 1]
```

처음에는 `T=16~32` 정도가 좋다.
open-loop rollout mismatch를 보기 위해서는 `T=5, 10, 20` horizon 평가를 따로 둔다.

---

# 3. latent는 어떻게 분해해야 하나?

여기가 제일 중요하다.
네가 원하는 대로 학습되게 하려면 latent를 그냥 하나의 벡터로 만들면 안 된다.

나쁜 설계:

```
z_t ∈ R^256
```

이렇게 하나로 만들면 모델은 예측하기 편한 방향으로 모든 정보를 섞어버릴 수 있다.
비지도 disentanglement는 inductive bias 없이 일반적으로 보장되지 않는다는 결과가 있고, Locatello et al.은 unsupervised disentangled representation learning이 model/data bias 없이 근본적으로 어렵다고 지적했다. ([Proceedings of Machine Learning Research][4])

따라서 네 구조는 **grouped latent tokens**로 가야 한다.

## 3.1 추천 latent 구조

처음 구현은 이렇게 해라.

```
K = 6 latent groups
d = 16 or 32 per group

z_t = [z_t^1, z_t^2, z_t^3, z_t^4, z_t^5, z_t^6]

z_t^k ∈ R^d
total latent dim = K × d
```

예시:

```
z_agent        ∈ R^32  # robot proprioception / motion
z_object       ∈ R^32  # object pose / velocity
z_contact      ∈ R^16  # contact / interaction
z_action_gain  ∈ R^16  # action이 상태에 미치는 효과
z_context      ∈ R^16  # hidden regime / domain shift
z_task_value   ∈ R^16  # reward / goal / success 관련
```

단, 논문에서는 이 이름들을 “ground-truth semantic factor”라고 주장하면 안 된다.
이렇게 써야 한다.

```
우리는 latent를 인간이 해석 가능한 진짜 원인명으로 복원하지 않는다.
대신 control에 필요한 기능적 subspace로 factorize한다.
```

즉 이름은 개발 편의를 위한 기능적 역할이다.

## 3.2 왜 group latent가 필요한가?

네 attention은 “개별 scalar latent dim”에 주면 불안정해질 가능성이 높다.

나쁜 방식:

```
α ∈ R^256
각 latent dimension마다 attention
```

문제:

```
z_17 하나가 진짜 의미를 가진다는 보장이 없음
차원 permutation에 취약함
attention이 noise처럼 흔들릴 수 있음
```

좋은 방식:

```
α ∈ R^K
각 latent group마다 attention
```

예:

```
α = [0.05, 0.10, 0.42, 0.31, 0.08, 0.04]
```

이러면 모델이 말하는 것은:

```
이번 mismatch는 contact/action-effect group 쪽을 주로 교정해야 한다.
```

가 된다.

이 정도는 논문적으로 방어 가능하다.

---

# 4. 기본 world model은 어떤 레이어로 만들까?

## 4.1 Encoder

state-only 기준 encoder는 MLP면 충분하다.

```
x_t ∈ R^{D_x}
↓
LayerNorm
↓
MLP
↓
group token projection
↓
z_t = [z_t^1, ..., z_t^K]
```

구체 예시:

```
Encoder E:
Linear(D_x → 256)
SiLU
LayerNorm
Linear(256 → 256)
SiLU
Linear(256 → K*d)
Reshape → [K, d]
```

왜 LayerNorm을 쓰냐?

```
state feature들은 단위가 다르다.
qpos, qvel, object pose, velocity, goal distance 등이 스케일이 다르다.
정규화하지 않으면 특정 feature가 latent를 지배한다.
```

또 데이터 전처리에서 반드시 해야 한다.

```
x_norm = (x - mean_train) / std_train
a_norm = action scaling to [-1, 1]
reward = symlog or normalization optional
```

## 4.2 Belief memory h_t

현실 동역학에서는 현재 관측만으로 hidden regime을 알기 어렵다.

예:

```
컵이 무거운지 가벼운지는 보기만 해서는 모름.
밀어보고 나서야 알 수 있음.
```

그래서 hidden memory가 필요하다.

```
h_t = GRU(h_{t-1}, concat(flatten(z_t), a_{t-1}, r_{t-1}))
```

shape:

```
z_t: [K, d]
flatten(z_t): [K*d]
a_t: [D_a]
h_t: [D_h], 예: 128 or 256
```

이건 RSSM의 deterministic state 역할과 비슷하다. PlaNet류 RSSM도 deterministic component와 stochastic component를 함께 써서 latent dynamics를 구성한다. ([arXiv][2])

## 4.3 Base dynamics prior

기본 dynamics는 다음 latent 분포를 예측한다.

```
pθ(z_{t+1} | z_t, a_t, h_t)
= N(μ_t, diag(σ_t^2))
```

group별로 보면:

```
pθ(z_{t+1}^k | z_t, a_t, h_t)
= N(μ_t^k, diag((σ_t^k)^2))
```

레이어는 이렇게 잡을 수 있다.

```
Input per group:
[z_t^k, a_t_embed, h_t_embed]

GroupDynamicsMLP_k:
Linear(d + d_a + d_h → 128)
SiLU
Linear(128 → 128)
SiLU
Linear(128 → 2*d)

Output:
μ_t^k, logσ_t^k
```

그런데 group 간 상호작용도 필요하다.
현실 동역학에서는 object group과 contact group, action effect group이 서로 영향을 준다.

그래서 dynamics 전에 **group interaction block**을 넣는다.

```
Z_t = [z_t^1, ..., z_t^K]  # [K, d]

Z'_t = GroupTransformerBlock(Z_t, action_token, h_token)
```

여기서 Transformer는 NLP용 긴 sequence attention이 아니라, **latent group 간 상호작용을 학습하는 작은 attention block**이다.

```
tokens =
[
  z_agent,
  z_object,
  z_contact,
  z_action_gain,
  z_context,
  z_task_value,
  action_token,
  belief_token
]
```

Self-attention으로 각 group이 서로를 본다.

```
Q = tokens W_Q
K = tokens W_K
V = tokens W_V

Attention(Q,K,V) = softmax(QK^T / sqrt(d)) V
```

하지만 이 attention은 원인 attention이 아니다.
이건 그냥 **dynamics interaction layer**다.

원인 attention은 나중에 mismatch를 입력받아 따로 만든다.

---

# 5. 예측분포와 실제 관측 mismatch는 어떻게 계산하나?

기본 world model이 다음 latent 분포를 예측한다.

```
μ_t, σ_t = fθ(z_t, a_t, h_t)
```

실제 다음 관측을 encoder에 넣는다.

```
z_{t+1} = E(x_{t+1})
```

그럼 raw error는:

```
e_t = z_{t+1} - μ_t
```

하지만 raw error는 쓰면 안 된다.
왜냐하면 원래 불확실한 영역에서는 error가 커도 정상일 수 있기 때문이다.

그래서 standardization한다.

```
ρ_t = (z_{t+1} - μ_t) / σ_t
```

group별로는:

```
ρ_t^k = (z_{t+1}^k - μ_t^k) / σ_t^k
```

falsification score는:

```
F_t^k = ||ρ_t^k||_2^2
```

전체는:

```
F_t = Σ_k F_t^k
```

만약 Gaussian 예측분포가 잘 calibration되어 있다면, 이 값은 차원에 따라 χ² 형태의 기준과 비교할 수 있다. 중요한 건 네 말처럼 “error > 0.3” 같은 하드코딩 threshold가 아니라, **모델이 예측한 불확실성 대비 얼마나 비정상적인지**를 보는 것이다.

다만 주의해야 한다.

```
σ_t가 너무 커지면 모델이 모든 mismatch를 “불확실했다”고 도망갈 수 있음.
```

그래서 variance calibration loss가 필요하다.

---

# 6. falsification 판단은 어떻게 설계해야 하나?

너는 “하드코딩 threshold를 쓰고 싶지 않다”고 했다.
그 방향은 맞다.

하지만 완전히 threshold가 없는 것은 아니다.
정확히는 **고정 임계값이 아니라 학습분포 기반 통계 기준**을 쓴다.

## 6.1 falsification gate

```
β_t = sigmoid(MLP([F_t, F_t^1,...,F_t^K, h_t]))
```

해석:

```
β_t ≈ 0: 현재 mismatch는 정상 범위
β_t ≈ 1: 현재 H0 dynamics가 깨졌을 가능성 높음
```

또는 p-value 스타일로:

```
p_t = P(χ²_d > F_t)
β_t = 1 - p_t
```

하지만 실제 딥러닝 예측분포는 완벽한 Gaussian이 아니기 때문에, 실험적으로는 training ID distribution의 empirical quantile calibration을 같이 쓰는 것이 좋다.

예:

```
train ID에서 F_t 분포를 저장
현재 F_t가 상위 95%/99% 분위 이상이면 high falsification
```

논문에서는 “hard-coded scalar threshold”가 아니라:

```
calibrated standardized mismatch
```

라고 쓰면 된다.

## 6.2 calibration loss

world model이 σ를 제대로 내도록 NLL을 쓴다.

```
L_nll =
Σ_t Σ_k [
  0.5 * ((z_{t+1}^k - μ_t^k)^2 / (σ_t^k)^2)
  + log σ_t^k
]
```

이 loss는 두 가지를 동시에 한다.

```
예측 평균 μ를 맞춰라.
불확실성 σ도 정직하게 내라.
```

하지만 NLL만으로는 σ가 커질 수 있으니 추가 penalty를 둔다.

```
L_sigma = mean(log σ_t)^2 or clamp σ_min, σ_max
```

실전 구현:

```
σ_t = softplus(raw_sigma) + σ_min
σ_min = 1e-3 or 1e-2
σ_max는 clamp로 제한
```

---

# 7. 네 custom attention은 어떻게 설계해야 하나?

여기가 논문의 핵심이다.

일반 attention은 “어디를 참고했는가”를 말한다.
하지만 attention weight가 곧 설명이나 원인이라고 보장되지는 않는다. Jain & Wallace는 attention weight가 gradient-based feature importance와 잘 맞지 않을 수 있고, 다른 attention 분포로도 같은 예측이 가능하다는 점을 보였다. ([arXiv][5])
반대로 Wiegreffe & Pinter는 attention 설명 가능성 논의가 explanation 정의와 실험 설계에 의존하고, 더 엄격한 diagnostic test가 필요하다고 반론했다. ([arXiv][6])

따라서 네 attention은 이렇게 정의해야 한다.

```
일반 attention:
모델이 무엇을 참고했는가?

네 causalized attention:
현재 mismatch를 줄이고 행동/value 예측을 회복하기 위해
어떤 latent group을 교정해야 하는가?
```

## 7.1 attention 입력

원인 attention은 다음을 입력으로 받아야 한다.

```
1. standardized mismatch ρ_t^k
2. latent group z_t^k
3. predicted uncertainty σ_t^k
4. action embedding a_t
5. belief memory h_t
6. value gradient or Q sensitivity
7. recent mismatch history
```

즉:

```
context_t = [
  flatten(ρ_t),
  flatten(σ_t),
  a_embed,
  h_t,
  value_signal,
  history_embed
]
```

## 7.2 group-wise causal attention

각 group token에 대해 key/value를 만든다.

```
group_token_k = concat(z_t^k, ρ_t^k, σ_t^k)
K_k = W_K group_token_k
V_k = W_V group_token_k
```

query는 mismatch context에서 만든다.

```
q = W_Q context_t
```

attention weight:

```
α_k = softmax(q · K_k / sqrt(d))
```

하지만 softmax는 모든 group에 조금씩 weight를 준다.
네 목적은 “몇 개만 의심”하는 것이므로 sparse attention이 더 좋다.

추천:

```
softmax 초기 구현
→ entmax/sparsemax
→ top-k Gumbel mask
```

처음에는 softmax + L1/sparsity penalty로 충분하다.

```
L_sparse = Σ_k α_k
```

그런데 softmax에서는 Σα=1이라 의미가 약하다.
차라리 entropy penalty를 쓴다.

```
L_entropy = H(α)
```

목표:

```
attention entropy를 낮춰서 적은 group에 집중
```

혹은 top-k mask:

```
m_k = TopK(α, k=1~2)
```

초기에는 hard top-k보다 soft attention이 안정적이다.

---

# 8. correction은 어디에 적용해야 하나?

중요한 선택지가 있다.

## 8.1 현재 latent z_t를 고칠 것인가?

```
z̃_t = z_t + α_t ⊙ δ_t
```

이 방식은 현재 belief를 고친다.

장점:

```
현재 상태 추정이 틀렸을 때 좋음
observation encoder가 잘못됐을 때 좋음
```

단점:

```
실제 관측 z_t 자체를 임의로 바꾸는 셈이라 불안정할 수 있음
```

## 8.2 다음 예측 μ_t를 고칠 것인가?

```
μ̃_t = μ_t + α_t ⊙ δ_t
```

이 방식은 transition prediction을 고친다.

장점:

```
dynamics mismatch correction으로 해석이 명확함
```

단점:

```
현재 hidden state 자체는 그대로라 장기 regime belief 반영이 약할 수 있음
```

## 8.3 transition adapter parameter를 고칠 것인가?

```
f_corrected = fθ + gψ
```

즉:

```
μ̃_t = fθ(z_t, a_t, h_t) + α_t ⊙ gψ(z_t, a_t, h_t, ρ_t)
```

이게 제일 좋다.

해석:

```
기본 world model은 유지한다.
falsification이 발생했을 때만 residual adapter가 작동한다.
attention은 adapter가 어느 latent group에 얼마나 작동할지 조절한다.
```

최종 추천:

```
μ̃_t^k = μ_t^k + β_t * α_t^k * δ_t^k
```

여기서:

```
β_t: falsification gate
α_t^k: k번째 latent group 의심도
δ_t^k: k번째 group 교정량
```

이 수식이 네 아이디어의 핵심이다.

```
β_t가 낮으면 correction 거의 없음.
α_t^k가 낮으면 해당 group은 correction 없음.
δ_t^k가 correction 방향과 크기.
```

---

# 9. correction module 레이어 설계

각 group에 대해 correction vector를 만든다.

```
δ_t^k = Gψ^k(z_t^k, ρ_t^k, a_t, h_t)
```

레이어:

```
CorrectionMLP:
Linear(d_z + d_rho + d_a + d_h → 128)
SiLU
LayerNorm
Linear(128 → 128)
SiLU
Linear(128 → d)
tanh
```

왜 `tanh`를 쓰냐?

```
교정량이 무한정 커지는 것을 막기 위해.
```

최종 correction:

```
δ_t^k = δ_max * tanh(raw_delta_t^k)
```

초기값:

```
δ_max = 0.1 ~ 0.5 latent std 기준
```

또 correction size penalty를 둔다.

```
L_corr_size = Σ_k ||α_t^k δ_t^k||_2^2
```

이게 없으면 모델이 기본 dynamics를 제대로 학습하지 않고 correction module에 다 떠넘길 수 있다.

---

# 10. action/value relevance는 어떻게 넣어야 하나?

이게 없으면 attention은 그냥 prediction error 줄이는 group만 본다.
하지만 네 목표는 “행동에 영향을 주는 mismatch”다.

따라서 reward/value head가 필요하다.

```
r̂_t = Rθ(z_t, a_t, h_t)
Q̂_t = Qθ(z_t, a_t, h_t)
V̂_t = Vθ(z_t, h_t)
πθ(a|z_t,h_t) optional
```

TD-MPC2처럼 latent planning을 쓰려면 reward/value model이 중요하다. TD-MPC2는 latent world model 위에서 local trajectory optimization을 하는 방식이라, reward/value 예측은 planning 품질과 직접 연결된다. ([arXiv][1])

## 10.1 action relevance score

각 group을 교정했을 때 value가 얼마나 바뀌는지 본다.

```
z̃_t^{(k)} = z_t with only group k corrected

A_k = |V(z̃_t^{(k)}) - V(z_t)|
```

또는 policy 변화:

```
P_k = D_KL(π(.|z̃_t^{(k)}) || π(.|z_t))
```

최종 의심 점수는 이렇게 학습시킨다.

```
cause_score_k =
standardized_mismatch_k
× action_relevance_k
× temporal_consistency_k
```

attention은 이 score와 맞도록 regularization할 수 있다.

```
L_attn_align = KL(stopgrad(normalize(cause_score)) || α)
```

단, 이것은 완전한 ground truth가 아니다.
pseudo-target이다.

## 10.2 value consistency loss

교정 후 value prediction이 실제 return과 맞아야 한다.

```
L_value =
|| V(z̃_t) - G_t ||^2
```

여기서 `G_t`는 n-step return 또는 TD target이다.

```
G_t = r_t + γ r_{t+1} + ... + γ^n V(z_{t+n})
```

이렇게 해야 correction이 단순히 다음 latent 예측만 맞추는 게 아니라, 실제 control objective에 맞게 학습된다.

---

# 11. necessity / sufficiency 검증을 학습에 넣는 방법

네가 “attention이 높다 = 원인”을 주장하려면 최소한 아래 검증을 넣어야 한다.

## 11.1 Necessity

선택된 group correction을 제거하면 성능이 나빠져야 한다.

```
L_with = prediction/value loss after selected correction
L_without = prediction/value loss when selected correction is removed

목표:
L_without > L_with
```

loss:

```
L_nec = max(0, margin - (L_without - L_with))
```

## 11.2 Sufficiency

선택된 group만 교정해도 full correction과 비슷해야 한다.

```
L_selected ≈ L_full
```

loss:

```
L_suf = |L_selected - L_full|
```

여기서 full correction은 모든 group correction을 허용한 경우다.

해석:

```
선택된 group이 충분히 핵심이면,
모든 group을 다 고치는 것과 비슷한 효과가 나야 한다.
```

## 11.3 Random mask 대비

무작위 group을 고친 것보다 좋아야 한다.

```
L_selected < L_random
```

loss:

```
L_rand = max(0, margin - (L_random - L_selected))
```

이 세 개를 넣으면 attention은 그냥 예쁜 heatmap이 아니라 **intervention-validated correction mask**가 된다.

---

# 12. 전체 loss 함수

최종 loss는 이렇게 간다.

```
L_total =
L_base_dynamics
+ λ1 L_reward
+ λ2 L_value
+ λ3 L_calibration
+ λ4 L_corrected_dynamics
+ λ5 L_sparse_attention
+ λ6 L_correction_size
+ λ7 L_temporal_consistency
+ λ8 L_necessity
+ λ9 L_sufficiency
+ λ10 L_random_contrast
```

각각 의미:

```
L_base_dynamics:
기본 world model이 정상 dynamics를 잘 예측

L_reward:
reward prediction

L_value:
value prediction

L_calibration:
예측분포 σ가 정직하게 calibration

L_corrected_dynamics:
correction 후 예측이 실제 관측과 가까워짐

L_sparse_attention:
적은 latent group만 교정

L_correction_size:
필요 이상으로 크게 교정하지 않음

L_temporal_consistency:
진짜 regime shift라면 연속 timestep에서 비슷한 group이 선택됨

L_necessity:
선택 group 제거 시 성능 악화

L_sufficiency:
선택 group만으로 full correction에 가까운 성능

L_random_contrast:
random correction보다 selected correction이 좋음
```

초기 구현에서는 전부 넣지 마라.
단계적으로 가야 한다.

---

# 13. 학습 단계는 반드시 분리해야 함

한 번에 end-to-end로 다 학습하면 망할 가능성이 높다.

## Stage 1. Base world model pretraining

먼저 correction 없이 기본 world model을 학습한다.

```
Input:
z_t, a_t, h_t

Output:
μ_t, σ_t, r̂_t, V̂_t

Loss:
L_base_dynamics + L_reward + L_value + L_calibration
```

이 단계에서 모델이 정상 dynamics를 배운다.

## Stage 2. Falsification/correction module training

base model을 freeze하거나 learning rate를 낮춘다.

```
freeze:
encoder E
base dynamics fθ 일부
reward/value head 일부

train:
falsification gate β
causal attention Aφ
correction adapter Gψ
```

왜 freeze하냐?

```
base dynamics와 correction module이 동시에 움직이면,
무엇이 틀렸고 무엇이 교정인지 경계가 사라짐.
```

즉 base가 H0 hypothesis 역할을 해야 한다.
그래야 falsification이 의미가 있다.

## Stage 3. Planner integration

교정된 dynamics로 planning한다.

```
for candidate action sequence:
  rollout under base dynamics
  if falsification expected or observed:
      use corrected dynamics
  evaluate reward + terminal value
choose best action
```

TD-MPC2식으로는 MPPI/CEM류 latent trajectory optimization을 붙일 수 있다.

## Stage 4. Optional online fine-tuning

시뮬레이터에서 실제로 action을 실행하고, 교정이 return/recovery time을 개선하는지 본다.

---

# 14. planning 구조는 어떻게 붙이나?

네 논문은 단순 prediction 논문이 아니라 planning 논문이어야 한다.
따라서 planner가 필요하다.

## 14.1 Planner 입력

```
current z_t, h_t
candidate action sequences A = [a_t, ..., a_{t+H-1}]
```

## 14.2 Uncorrected rollout

```
ẑ_{τ+1} = fθ(ẑ_τ, a_τ)
r̂_τ = Rθ(ẑ_τ, a_τ)
```

## 14.3 Corrected rollout

실제 관측이 있는 첫 step에서는 observed mismatch를 쓴다.
future rollout에서는 observed mismatch가 없으므로 predicted uncertainty와 learned regime belief를 쓴다.

```
z̃_{τ+1} = fθ(z̃_τ, a_τ) + β_τ α_τ ⊙ δ_τ
```

여기서 future β/α/δ는 history belief `h_t`와 simulated mismatch estimate로 예측한다.

처음 구현에서는 간단히:

```
현재 step에서 얻은 α_t, δ_t를 short horizon 동안 유지
```

로 해도 된다.

예:

```
for τ=t to t+H:
  use same correction mask α_t for H_corr=3~5 steps
```

이게 현실적으로 좋다.
왜냐하면 friction/mass/action gain 같은 regime은 한 step만 바뀌는 게 아니라 일정 구간 지속되기 때문이다.

---

# 15. 데이터 split은 어떻게 만들어야 하나?

ManiSkill controlled benchmark에서는 이렇게 만든다.

```
Train-ID:
normal mass, normal friction, no latency, normal noise

Valid-ID:
same distribution

Test-ID:
same distribution but unseen seeds

OOD-mass:
object mass changed

OOD-friction:
surface/object friction changed

OOD-latency:
action delay introduced

OOD-noise:
observation noise increased

OOD-mixed:
mass + friction + latency combined
```

중요한 건 regime label을 training loss에 직접 넣지 않는 것이다.

```
regime_id는 evaluation용으로만 사용
```

그래야 네 주장이 산다.

```
우리는 원인 label 없이 mismatch와 action relevance만으로 correction mask를 학습한다.
```

다만 ablation으로 weak supervision 버전을 둘 수는 있다.

```
oracle regime label 사용 버전
```

이건 upper bound로 좋다.

---

# 16. 이미지/RGB-D는 언제 넣어야 하나?

처음에는 넣지 마라.
네 핵심은 이미지가 아니라 dynamics correction이다.

단계는 이렇게 가야 한다.

```
Phase 1:
state-only

Phase 2:
state_dict + RGB

Phase 3:
RGB-D only or RGB-D + proprioception

Phase 4:
DROID/BridgeData real trajectory validation
```

ManiSkill은 state-only뿐 아니라 RGB, depth, segmentation, pointcloud 조합도 지원한다. 따라서 state-only로 방법론을 검증한 뒤, 같은 환경에서 observation modality를 확장할 수 있다. ([ManiSkill][3])

이미지를 넣는 경우 encoder는 이렇게 바뀐다.

```
RGB image
↓
CNN or ViT encoder
↓
visual token

proprio state
↓
MLP encoder
↓
proprio token

object/goal/state extra
↓
MLP encoder
↓
task token

tokens fusion
↓
latent groups
```

하지만 논문 1차 메인 결과는 state-only로 충분히 강할 수 있다.
오히려 state-only에서 이겨야 네 알고리즘 주장이 선명하다.

---

# 17. 네 모델이 “원하는 대로” 학습되게 만드는 핵심 inductive bias

이게 제일 중요하다.

네가 원하는 건:

```
latent가 기능별로 분해되고,
mismatch가 생겼을 때 관련 group만 선택되고,
그 group만 적절히 교정되는 것.
```

그냥 loss만 넣으면 안 된다.
다음 bias가 필요하다.

## 17.1 Grouped latent

```
z = [z^1, ..., z^K]
```

개별 차원보다 group 단위가 안정적이다.

## 17.2 Sparse attention

```
적은 group만 선택
```

그래야 원인 후보가 분해된다.

## 17.3 Bounded correction

```
δ_t 크기 제한
```

그래야 correction module이 모든 걸 해결하는 shortcut을 막는다.

## 17.4 Temporal consistency

```
α_t와 α_{t+1}가 지나치게 튀지 않게
```

진짜 regime shift와 일시적 noise를 구분한다.

## 17.5 Action relevance

```
prediction error만 줄이지 말고 value/action ranking 개선을 보게 함
```

이게 네 논문 정체성이다.

## 17.6 Necessity/sufficiency validation

```
선택된 group이 진짜 필요한지,
선택된 group만으로 충분한지 검증
```

attention을 원인 주장에 가깝게 만든다.

## 17.7 Controlled OOD regime

```
mass/friction/latency/noise/action gain shift
```

데이터 자체가 변동 요인을 제공해야 latent가 배울 수 있다.
데이터와 모델 inductive bias 없이 disentanglement가 저절로 생긴다고 기대하면 안 된다. ([Proceedings of Machine Learning Research](https://proceedings.mlr.press/v97/locatello19a))

---

# 18. 기존 changing dynamics 연구와 네 차별점

HiP-RSSM 같은 연구는 changing dynamics scenario에서 dynamics가 고정되어 있지 않고 latent parameter로 related dynamical systems를 모델링할 수 있다는 방향을 다룬다. 이 논문은 RSSM이 fixed dynamics를 가정하는 한계를 지적하고, 유사하지만 다른 dynamics를 low-dimensional latent factors로 parameterize하는 방식을 제안한다. ([arXiv](https://arxiv.org/abs/2206.14697))

네 방법은 여기와 가깝지만 다르게 가야 한다.

```
HiP-RSSM류:
hidden parameter로 dynamics family를 모델링

네 방법:
현재 H0 dynamics가 관측 전이와 통계적으로 불일치할 때,
action-relevant latent subspace를 찾아 sparse correction
```

즉 네 novelty는:

```
hidden parameter를 추정한다
```

가 아니라,

```
현재 hypothesis를 falsify하고,
어디를 얼마나 교정해야 planning이 회복되는지 학습한다
```

다.

또 PLSM류는 action effect가 더 systematic하게 표현되도록 latent dynamics를 regularize한다. PLSM은 action이 latent state에 만드는 변화가 state에 지나치게 의존하지 않도록 mutual information을 줄이는 방식으로 action effect를 더 예측 가능하게 만들려 한다. ([arXiv](https://arxiv.org/abs/2401.17835))

네 방법은 이것과도 연결된다.

```
PLSM:
action effect를 systematic하게 만들자.

네 방법:
action effect hypothesis가 깨졌을 때,
그 mismatch를 감지하고 관련 latent subspace만 교정하자.
```

---

# 19. 구체적인 아키텍처 스펙 초안

처음 구현은 이 정도가 적절하다.

```
Input:
D_x = environment state dimension
D_a = action dimension

Encoder:
MLP D_x → 256 → 256 → K*d
K = 6
d = 32
total latent = 192

Belief:
GRU input = K*d + D_a + 1 reward
hidden = 256

Group interaction:
2-layer Transformer block
num_tokens = K + action_token + belief_token
d_model = 32 or 64
heads = 4

Base dynamics:
per-group MLP
input = group_token + action_embed + belief_embed
output = μ_k, logσ_k

Reward head:
MLP flatten(z)+a+h → scalar

Value head:
MLP flatten(z)+h → scalar

Falsification:
standardized residual ρ
F_k = ||ρ_k||²
β = sigmoid(MLP([F_1...F_K, F_total, h]))

Causal attention:
query = MLP([ρ_all, F_all, h, a, value_signal])
keys = MLP([z_k, ρ_k, σ_k])
α = sparse softmax / entmax over K groups

Correction:
δ_k = tanh(MLP([z_k, ρ_k, a, h]))
μ̃_k = μ_k + β * α_k * δ_max * δ_k
```

초기 hyperparameter:

```
K = 6
d = 32
h_dim = 256
horizon train = 16
planning horizon = 5~15
δ_max = 0.25
λ_sparse = 0.01
λ_corr_size = 0.1
λ_temporal = 0.05
```

처음에는 너무 복잡하게 하지 마라.

최소 구현 버전:

```
Encoder
Base dynamics
Reward/value head
Standardized mismatch
Attention mask
Correction adapter
Corrected rollout loss
```

necessity/sufficiency는 2차로 넣어라.

---

# 20. 학습 루프는 어떻게 되나?

## 20.1 Base model 학습

```
for batch episodes:
    z_t = E(x_t)
    h_t = GRU(...)
    μ_t, σ_t = fθ(z_t, a_t, h_t)
    z_tp1 = E(x_tp1)

    L_dyn = NLL(z_tp1 | μ_t, σ_t)
    L_reward = MSE(r̂_t, r_t)
    L_value = TD loss
    update base model
```

## 20.2 Correction 학습

```
for batch episodes, especially OOD/mixed:
    base predicts μ_t, σ_t
    compute ρ_t = (z_tp1 - μ_t) / σ_t
    compute falsification β_t
    compute attention α_t
    compute correction δ_t
    μ̃_t = μ_t + β_t α_t δ_t

    L_corrected = NLL(z_tp1 | μ̃_t, σ_t)
    L_sparse
    L_corr_size
    L_value_corrected
    update correction modules
```

## 20.3 Open-loop rollout 학습

한 step만 맞추면 안 된다.
월드모델의 진짜 문제는 rollout error 누적이다.

```
ẑ_{t+1} = corrected_dynamics(z_t, a_t)
ẑ_{t+2} = corrected_dynamics(ẑ_{t+1}, a_{t+1})
...
```

loss:

```
L_rollout =
Σ_{k=1}^{H} w_k || z_{t+k} - ẑ_{t+k} ||²
```

이때 `H=5,10,20`으로 평가한다.

---

# 21. “mismatch가 어디에 영향을 받고 얼마만큼 변화시켜야 하는가”의 이론 정리

이론은 이렇게 쓰면 된다.

## 21.1 예측분포

```
pθ(z_{t+1}|z_t,a_t,h_t) = N(μ_t, Σ_t)
```

## 21.2 Falsification event

```
F_t = (z_{t+1}-μ_t)^T Σ_t^{-1} (z_{t+1}-μ_t)
```

이 값이 calibration된 ID distribution에서 비정상적으로 크면:

```
H0 dynamics is falsified.
```

## 21.3 원인 후보 attention

```
α_t = Aφ(ρ_t, z_t, a_t, h_t, ∇_z V)
```

## 21.4 교정

```
μ̃_t = μ_t + β_t Σ_k α_t^k δ_t^k
```

group-wise로는:

```
μ̃_t^k = μ_t^k + β_t α_t^k δ_t^k
```

## 21.5 최적 교정 목표

```
min_{α,δ}
E[
  prediction_error_after_correction
  + λ sparsity(α)
  + η ||δ||²
  - κ value_improvement
]
```

즉:

```
오차는 줄여라.
적은 group만 고쳐라.
조금만 고쳐라.
하지만 value/planning에는 도움이 되게 고쳐라.
```

이게 네 이론이다.

---

# 22. 실험에서 무엇을 보여줘야 하나?

## 22.1 Prediction metrics

```
one-step NLL
one-step latent MSE
multi-step rollout error
calibration error
```

## 22.2 Falsification metrics

```
OOD detection AUROC
standardized residual calibration
regime shift detection delay
false positive rate under ID noise
```

## 22.3 Correction metrics

```
corrected rollout error 감소
selected-only vs full correction 성능 차이
selected vs random mask 성능 차이
attention temporal stability
```

## 22.4 Control metrics

```
return
success rate
recovery time after shift
planning calls per success
return per compute
wrong-hypothesis duration
```

## 22.5 Ablation

반드시 넣어야 한다.

```
Base world model only
Base + uncertainty detector only
Base + full correction
Base + random correction mask
Base + standard attention
Base + causalized attention without value loss
Full model
Oracle regime correction upper bound
```

이 ablation이 없으면 reviewer가 이렇게 말한다.

```
그냥 residual adapter가 좋아진 거 아닌가?
attention은 필요 없는 거 아닌가?
falsification gate는 필요 없는 거 아닌가?
```

---

# 23. 네가 피해야 할 실패 패턴

## 실패 1. correction module이 너무 강함

문제:

```
base world model이 아무것도 안 배우고,
correction이 다 처리함.
```

해결:

```
base pretrain
correction capacity 제한
δ_max 제한
correction size penalty
β gate 없으면 correction 금지
```

## 실패 2. attention이 원인처럼 보이지만 실제로는 shortcut

문제:

```
attention이 항상 특정 group만 찍음.
```

해결:

```
random mask contrast
necessity/sufficiency test
OOD regime별 attention distribution 분석
```

## 실패 3. σ가 커져서 falsification 회피

문제:

```
모델이 불확실성을 크게 내서 모든 mismatch를 정상 처리.
```

해결:

```
variance regularization
calibration evaluation
ID coverage constraint
σ clamp
```

## 실패 4. latent group이 의미 없이 섞임

문제:

```
group attention을 해도 group 자체가 뒤섞여 있음.
```

해결:

```
group-specific dynamics head
sparse inter-group interaction
action-effect regularization
controlled regime variation
```

## 실패 5. prediction은 좋아졌는데 control은 안 좋아짐

문제:

```
world model 논문에서 흔한 문제.
```

해결:

```
value loss
action ranking loss
closed-loop return 평가
recovery time 평가
```

---

# 24. 네 아이디어를 논문 제목급으로 정리하면

가칭:

```
Falsification-Guided Latent Correction for World Model Planning
```

또는:

```
Action-Relevant Falsification in Latent World Models
```

핵심 contribution:

```
1. Standardized predictive mismatch를 이용한 dynamics hypothesis falsification
2. Falsification event에서 action-relevant latent subspace를 선택하는 causalized attention
3. Attention-gated sparse residual correction
4. Necessity/sufficiency/counterfactual rollout 기반 correction validation
5. Controlled physical dynamics shift benchmark에서 return/recovery/compute efficiency 개선
```

---

# 25. 최종 구현 순서

네가 지금 바로 프로젝트로 옮긴다면 이렇게 가라.

## Step 1. ManiSkill state-only dataset 생성

```
PickCube / PushCube / LiftCube 계열
ID + mass/friction/latency/noise OOD split 생성
transition 저장
```

## Step 2. base latent world model 구현

```
Encoder
GRU belief
Group latent
Base dynamics μ, σ
Reward/value head
```

## Step 3. base 성능 확인

```
ID one-step NLL
ID rollout error
OOD rollout error 증가 확인
```

여기서 OOD에서 error가 증가하지 않으면 네 실험 자체가 안 된다.

## Step 4. falsification score 구현

```
standardized residual
group score
global score
calibration plot
OOD AUROC
```

## Step 5. causalized attention + correction 구현

```
attention α
correction δ
μ̃ = μ + β α δ
corrected rollout loss
```

## Step 6. ablation

```
full correction
random mask
no value loss
no sparsity
no falsification gate
```

## Step 7. closed-loop planning

```
base planner vs corrected planner
return
success
recovery
compute
```

---

# 마지막 핵심 정리

네가 원하는 대로 학습시키려면 “아키텍처가 알아서 해주겠지”가 아니라 다음 5개를 강제해야 한다.

```
1. latent를 group token으로 나눈다.
2. 예측분포를 내고 standardized mismatch로 falsification을 판단한다.
3. mismatch/action/value/history를 입력으로 causalized attention을 만든다.
4. attention은 explanation이 아니라 sparse correction mask로 학습한다.
5. correction의 유효성은 rollout error와 return/recovery time으로 검증한다.
```

가장 중요한 수식은 이거다.

```
pθ(z_{t+1}|z_t,a_t,h_t) = N(μ_t, Σ_t)

ρ_t = Σ_t^{-1/2}(z_{t+1} - μ_t)

β_t = FalsificationGate(ρ_t)

α_t = CausalAttention(ρ_t, z_t, a_t, h_t, value_signal)

μ̃_t^k = μ_t^k + β_t α_t^k δ_t^k
```

이 구조가 네 아이디어의 뼈대다.

**base는 TD-MPC2-style latent world model, memory는 RSSM/GRU, novelty는 falsification-guided causal attention correction.**
이렇게 설계하면 네 주장은 단순 attention 실험이 아니라, **월드모델의 누적 mismatch와 wrong-hypothesis planning 문제를 직접 겨냥하는 구조**가 된다.