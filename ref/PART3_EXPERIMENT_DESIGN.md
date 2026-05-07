# Experimental Design: RG-4F Environment, Tasks, OOD, Baselines, Ablations, Metrics

Part 3의 핵심은 하나다. **이 실험환경은 “복잡한 2D 게임”을 만들기 위한 장치가 아니라, wrong-hypothesis-aware world-model planning이 언제 baseline보다 강한지 분해해서 증명하기 위한 통제된 메커니즘 benchmark다.** 기존 STEP 3에서도 중앙홀-4방 구조는 geometry 다양성보다 각 방이 서로 다른 regime family를 유발하도록 설계하는 것이 목적이며, room-task permutation과 factor recombination으로 compositional OOD를 만들도록 정의되어 있다.

---

# 3.15 Environment: RegimeGrid-4Room Factorized Tasks, RG-4F

## 3.15.1 월드맵 구조의 최종 의미

최종 환경 이름은 다음으로 둔다.

**RegimeGrid-4Room Factorized Tasks, RG-4F**

RG-4F는 중앙홀 하나와 북/남/동/서 4개 방으로 구성된 부분관측 tick-based 2D world-model planning benchmark다. 공간 구조는 복잡하지 않다. 오히려 의도적으로 단순하다. 이유는 이 논문이 “geometry가 복잡한 환경에서 agent가 길을 잘 찾는다”를 주장하는 논문이 아니기 때문이다. 이 논문은 **부분관측 환경에서 hidden state와 hidden regime를 분리 추적하고, 잘못된 dynamics hypothesis를 오래 붙잡지 않도록 planning compute를 대안 가설 쪽으로 재배치하는 메커니즘 논문**이다.

따라서 이 환경에서 중요한 것은 벽이 얼마나 많고 미로가 얼마나 복잡한지가 아니다. 중요한 것은 다음이다.

1. 같은 관측 변화가 state reveal인지 regime shift인지 애매해야 한다.
2. 각 방이 서로 다른 regime factor를 자극해야 한다.
3. agent가 방 위치를 외우면 안 되고, task rule과 local cue를 통해 현재 규칙을 추론해야 한다.
4. 작은 drift와 큰 shift가 모두 있어야 한다.
5. current hypothesis와 alternative hypothesis에 따라 최적 행동이 달라져야 한다.
6. planning을 항상 많이 하는 방법이 compute-normalized 기준에서 손해를 봐야 한다.

즉 이 환경은 “복잡한 게임”이 아니라 “복잡한 규칙 가설 비교 문제”다.

공간 구조는 다음처럼 둔다.

- 중앙홀: `9 x 9`
- 북/남/동/서 방: 각각 `8 x 8`
- 중앙홀과 각 방 사이 연결 복도: 길이 3
- 시작 위치: 중앙홀 중심
- 방 하나 완료 시 중앙홀 복귀
- 전체 목표: A/B/C/D 네 임무 모두 완료

수식으로 episode-level goal은 다음처럼 둘 수 있다.

$G_{episode}=\mathbf{1}[\text{Task A completed}]\cdot \mathbf{1}[\text{Task B completed}]\cdot \mathbf{1}[\text{Task C completed}]\cdot \mathbf{1}[\text{Task D completed}]$

여기서 중요한 점은 각 방이 반드시 특정 task로 고정되지 않는다는 것이다. 훈련에서는 일부 room-task permutation만 보여주고, 테스트에서는 unseen permutation을 준다. 예를 들어 훈련에서는 북쪽 방에 Task A가 자주 있었지만, 테스트에서는 북쪽 방에 Task C가 등장할 수 있다. 이렇게 해야 agent가 “북쪽 방 = A”라고 외우는 것을 막을 수 있다.

---

## 3.15.2 왜 중앙홀 + 4방 구조로 충분한가?

### 직관적 해설

리뷰어가 “2D 4방 구조라 너무 장난감 아닌가?”라고 공격할 수 있다. 이 공격에 대한 답은 명확해야 한다.

이 논문은 3D simulator scale을 자랑하는 논문이 아니다. 이 논문은 **world model 내부에서 current hypothesis와 alternative hypothesis를 비교하고, 그 차이가 행동에 영향을 줄 때 planning 방향을 바꾸는 메커니즘**을 보여주는 논문이다. 이 경우 환경은 오히려 너무 복잡하면 안 된다. 환경이 지나치게 복잡하면 성능 차이가 어디서 발생했는지 해석하기 어렵다.

중앙홀 + 4방 구조는 다음 장점을 가진다.

첫째, 공통 시작점이 있다. 모든 episode가 중앙홀에서 시작하므로 초기조건이 통제된다.
둘째, 각 방을 서로 다른 regime family로 설계할 수 있다.
셋째, 방 완료 후 중앙홀로 돌아오게 하면 task 간 state carry-over와 post-task shift를 통제할 수 있다.
넷째, room-task permutation으로 위치 암기를 막을 수 있다.
다섯째, 4개의 task를 모두 완료해야 하므로 단일 skill이 아니라 multi-regime adaptation이 필요하다.

즉 geometry는 단순하지만 regime composition은 복잡하다. 이게 핵심이다.

### 학술적 서술

RG-4F는 geometric complexity를 최대화하기 위한 benchmark가 아니라, compositional regime complexity를 통제하기 위한 diagnostic environment다. 이 환경은 spatial layout을 고정함으로써 불필요한 confound를 줄이고, task permutation, factor recombination, parameter randomization, invisible field placement shift를 통해 dynamics-level generalization을 평가한다.

즉 평가 대상은 “넓은 미로를 외우는가”가 아니라 다음이다.

- 동일한 local cue를 다른 room 위치에서 해석할 수 있는가?
- task factor가 새롭게 조합되어도 regime posterior를 업데이트할 수 있는가?
- small drift가 누적될 때 current hypothesis persistence를 줄일 수 있는가?
- abrupt shift와 reveal을 구분할 수 있는가?
- 대안 hypothesis가 action flip을 만들 때만 planning을 재배치하는가?

이런 질문은 복잡한 3D visual environment보다 통제된 2D tick-based environment에서 더 선명하게 검증된다.

---

## 3.15.3 map number, map family, parameter randomization, task permutation

최종 실험에서는 하나의 고정 map만 쓰면 안 된다. 구조는 중앙홀 + 4방으로 유지하되, map family를 여러 개 둔다.

권장 구조는 다음이다.

- train map family: 50~200개
- validation map family: 20~50개
- test in-domain map family: 50개
- OOD map family: 각 OOD 조건별 50개 이상

여기서 map family는 단순 벽 배치만 뜻하지 않는다. 다음 요소의 조합이다.

1. 방 내부 object 배치
2. local cue 배치
3. invisible field source 배치 prior
4. task parameter range
5. target band 생성 규칙
6. field coupling family
7. drift/shift schedule prior

각 episode는 다음처럼 생성된다.

$M_e \sim p(M \mid \mathcal{F}_{map})$

$\pi_e \sim p(\pi_{task})$

$\theta_e^{task} \sim p(\theta \mid M_e,\pi_e)$

여기서 `M_e`는 episode map, `π_e`는 room-task permutation, `θ_e^{task}`는 task parameter다.

이 구조가 중요한 이유는 agent가 특정 map이나 특정 방 위치를 외우지 못하게 하기 위해서다. agent는 local cue, scalar state, event feedback, action outcome을 통해 현재 task와 regime를 추론해야 한다.

---

# 3.16 Partial Observability

## 3.16.1 왜 전체 맵을 다 보여주면 안 되는가?

전체 맵을 다 보여주면 이 논문의 핵심 문제가 약해진다. agent가 모든 object, hazard, target, field source, door condition을 처음부터 볼 수 있다면 hidden state tracking의 필요가 줄어든다. 더 나쁘게는 hidden regime tracking도 약해진다. 왜냐하면 많은 경우 agent가 local cue와 transition evidence를 통해 규칙을 추론하기보다, 전체 map annotation을 보고 바로 답을 낼 수 있기 때문이다.

이 논문은 world model이 필요한 환경을 다룬다. world model이 필요하려면 agent가 현재 보지 못하는 것을 기억하고, 최근 행동 결과를 통해 latent state와 latent regime를 갱신해야 한다. 따라서 부분관측은 선택이 아니라 필수다.

관측은 다음처럼 둔다.

$o_t=(o_t^{local},o_t^{scalar},e_t)$

local observation은 주변 `7 x 7` window다.

$o_t^{local}\in \mathbb{R}^{7\times 7\times C}$

scalar observation은 현재 측정 가능한 상태값과 진행 정보다.

$\displaystyle o_t^{scalar} = (x_t, \text{room\_id}_t, \text{completed\_count}_t, \text{fail\_count}_t, \text{step\_norm}_t)$

5차원 상태벡터는 다음이다.

$x_t=(v_t,m_t,i_t,n_t,d_t)\in[-1,1]^5$

event token은 최근 상호작용 성공/실패, checkpoint 통과, room entry, door open, forced reset 같은 신호다.

$e_t\in\mathcal{E}$

기존 STEP 3도 local observation window, scalar observation, event token으로 관측을 구성하고 전체 맵을 보이지 않게 해야 hidden state/regime 분리 필요성이 살아난다고 정의했다.

---

## 3.16.2 local observation + global scalar가 맞는 이유

local observation은 주변 구조를 본다. 예를 들어 벽, 문, 퍼즐 조각, 비석, 타일, altar, interaction cell, traversable mask를 본다. 하지만 전체 방 구조와 invisible field source는 직접 보이지 않는다.

global scalar는 agent의 내부 상태와 task 진행도를 본다. 예를 들어 현재 `v, m, i, n, d` 값, 현재 방 ID, 완료한 방 수, fail count, normalized step count를 제공한다.

이 조합이 좋은 이유는 다음이다.

- local observation만 있으면 agent가 자신의 내부 상태값 변화를 놓칠 수 있다.
- scalar만 있으면 local cue와 object layout을 해석할 수 없다.
- 둘을 결합하면 “내가 지금 어디에 있고, 주변에 무엇이 있으며, 내 상태값이 어떻게 바뀌고 있는가”를 함께 추론할 수 있다.
- 하지만 전체 map과 hidden source는 여전히 숨겨져 있으므로 belief tracking이 필요하다.

쉬운 말로 하면, agent는 “눈앞 풍경”과 “몸 상태 계기판”은 볼 수 있지만, “세계 전체 지도”와 “보이지 않는 물리 법칙 변화”는 모른다. 이 정도가 hidden state/regime world model 실험에 적절하다.

---

# 3.17 Five Controllable State Variables

상태값 5개는 이 환경의 핵심이다. 하지만 이 값들을 “항상 0으로 유지해야 하는 값”으로 설계하면 안 된다. 기존 감사 결과에서도 초기값 `(0,0,0,0,0)`은 episode 시작 baseline일 뿐이며, 상태값은 현재 임무와 규칙에 따라 최적 방향이 달라지는 값이어야 한다고 정리되어 있다. 또한 전역적으로는 시야/속도/상호작용이 커질수록 유리한 경향이 있지만, 특정 altar, 문, 비석, interaction cell 근처에서는 target band가 우선하는 local override 구조가 필요하다.

---

## 3.17.1 Vision, `v_t`

### 기본 의미

`vision`은 agent가 local map을 얼마나 넓고 선명하게 볼 수 있는지를 나타낸다. 수식적으로는 관측 반경 또는 관측 mask에 연결된다.

$\displaystyle \text{vision\_radius}(v_t) = r_0 + \lfloor \alpha_v v_t \rfloor$

$\displaystyle \text{vision\_mask}_t = \text{LocalFoV}(p_t, v_t, \chi_t)$

`v_t`가 높으면 더 넓은 local cue를 볼 수 있고, hidden object나 target hint를 더 빨리 발견할 수 있다. 하지만 이 값이 항상 클수록 좋은 것은 아니다. 어떤 task에서는 vision-positive cue만 골라야 하고, 어떤 순간에는 vision이 변하지 않고 안정되어야 문이 열릴 수 있다.

### 전역 기본 효용

전역적으로는 vision이 높으면 유리하다. 더 많은 정보를 빨리 보고, 잘못된 비석이나 hazard tile을 피할 수 있다. 예를 들어 vision이 낮으면 target band를 알려주는 local symbol을 너무 늦게 발견하고, 불필요한 탐색 step이 증가한다.

### local override

그러나 Task B처럼 “마지막 2 tick 동안 vision 변화 없음” 조건이 있는 경우에는 vision을 무작정 키우면 안 된다. local door condition이 “vision-positive stele만 켠 뒤, vision이 안정된 상태에서 interaction”을 요구한다면, agent는 vision을 키우는 것보다 안정화하는 것을 우선해야 한다.

### 잘못 추정될 때 생기는 비용

vision을 잘못 추정하면 다음 비용이 생긴다.

- local cue를 늦게 발견해 episode length 증가
- wrong stele 선택으로 failure count 증가
- observation shift를 regime shift로 오해
- hazard hint를 놓쳐 forced reset 위험 증가
- 필요한 시점에 vision 안정 조건을 만족하지 못함

따라서 vision은 단순 관측 품질 변수가 아니라 planning-relevant state다.

---

## 3.17.2 Mobility, `m_t`

### 기본 의미

`mobility`는 이동 효율이다. 핵심은 이동 방향이 바뀌는 것이 아니라, 같은 방향으로 이동하는 데 걸리는 tick 수가 달라진다는 점이다. mobility는 latency/cooldown 축이다.

$\displaystyle \text{move\_cd}(m_t) = \max \left( 1, \left\lceil \frac{\kappa_m}{1 + \alpha_m m_t} \right\rceil \right)$

`m_t`가 높으면 이동 cooldown이 줄고, 낮으면 이동 cooldown이 늘어난다.

### 전역 기본 효용

전역적으로 mobility가 높으면 유리하다. 같은 목표 위치에 더 빨리 도달하고, episode length와 step cost를 줄인다.

### local override

하지만 특정 door나 interaction cell에서는 `m_t`가 특정 band 안에 있어야 할 수 있다.

$m_t\in[\tau_m-\alpha_m^{gate},\tau_m+\alpha_m^{gate}]$

예를 들어 Task B에서는 interaction cell에서 `m_t`가 0 근처여야 문이 열린다. 이 경우 mobility를 높이는 전역 효용보다 local gate condition이 우선한다.

### control-drift와의 차이

mobility와 control-drift는 절대 섞이면 안 된다. mobility는 “느려지는 것”이고, control-drift는 “입력이 다른 방향으로 해석되는 것”이다. 감사 문서에서도 mobility는 latency/cooldown 축, control-drift는 이산 방향 remap과 약한 miscontrol로 분리해야 한다고 정리되어 있다.

### 잘못 추정될 때 생기는 비용

mobility를 잘못 추정하면 다음 비용이 생긴다.

- 도착 시간을 틀리게 예측
- interaction timing 실패
- door condition 미충족
- correction할지 adaptation할지 잘못 판단
- 이동 cooldown이 누적되어 compute frontier 악화

---

## 3.17.3 Interaction, `i_t`

### 기본 의미

`interaction`은 object, stele, altar, door와 상호작용할 때 필요한 강도 또는 calibration 상태다. 이 값은 성공확률 random variable로만 쓰면 약하다. 최종 설계에서는 latency와 target band에 연결한다.

$$
$\displaystyle \text{interaction\_ticks}(i_t, \tau) = \left\lceil T_0(1 + \alpha_i |i_t - \tau|) \right\rceil$
$$

여기서 `τ`는 local target이다. `i_t`가 target에 가까울수록 interaction latency가 줄고, 너무 벗어나면 실패할 수 있다.

### 전역 기본 효용

전역적으로는 interaction capability가 높거나 안정적이면 interaction 시간이 줄어드는 경향이 있다. 하지만 모든 task에서 interaction을 크게 만드는 게 정답은 아니다.

### local override

altar나 final door는 match-to-band 조건을 요구한다.

$$
$i_t\in[\tau_i-\alpha_i,\tau_i+\alpha_i]$
$$

특히 Task A와 Task D는 interaction target band를 맞추는 것이 핵심이다. 이때 agent는 local cue를 통해 `τ_i`를 추론해야 한다. 정답 band를 처음부터 알려주면 안 된다. 하지만 완전 blind trial-and-error도 안 된다. cue를 보고 합리적으로 추론할 수 있어야 한다.

### 잘못 추정될 때 생기는 비용

interaction을 잘못 추정하면 다음 비용이 생긴다.

- interaction latency 증가
- 실패 interaction 누적
- forced reset
- final altar 실패
- wrong hypothesis 아래에서 interaction timing rollout이 틀어짐

---

## 3.17.4 Noise, `n_t`

### 기본 의미

`noise`는 invisible field와 연결된 공통 latent disturbance 축이다. 단, noise가 모든 상태값을 동시에 흔들면 안 된다. 그렇게 하면 식별이 불가능해지고, agent는 어떤 field family인지 추론할 수 없다. 최종 설계에서는 noise는 공통 숨은 원인이지만, map family마다 1~2개 상태에만 sparse coupling된다.

기본 noise update는 다음처럼 둔다.

$\displaystyle n_{t+1}=\operatorname{clip}\left(n_t+\sum_{j=1}^{M_t}\epsilon_{j,t},-1,1\right)$

$\epsilon_{j,t}\sim\mathcal{N}(\mu_{j,t},\sigma_j^2)$

### 전역 기본 효용

전역적으로는 noise가 낮거나 안정적인 것이 유리하다. 하지만 noise 자체를 reward target으로 삼으면 안 된다. noise는 task cost와 observation/transition disturbance의 원인으로 작동해야 한다.

### local override

어떤 task에서는 `n_t≈0`이어야 stele이 켜지거나 altar가 작동할 수 있다. 예를 들어 Task C는 noise-zero condition을 요구한다. 이 경우 agent는 noise를 무조건 낮추는 것이 아니라, 특정 local interaction 시점에 target band로 맞춰야 한다.

$n_t\in[\tau_n-\alpha_n,\tau_n+\alpha_n]$

보통 `τ_n=0`으로 둘 수 있다.

### 잘못 추정될 때 생기는 비용

noise를 잘못 추정하면 다음 비용이 생긴다.

- observation cue를 잘못 해석
- invisible field family를 잘못 추론
- interaction target drift를 놓침
- control-drift와 noise coupling을 혼동
- reveal을 shift로, shift를 reveal로 오판

---

## 3.17.5 Control-drift, `d_t`

### 기본 의미

`control-drift`는 이동속도가 아니라 입력 해석 규칙의 왜곡이다. 4방향 grid에서 연속 각도 drift로 설명하면 부정확하다. 최종 정의는 다음이다.

> control-drift는 `W/A/S/D` 입력이 실제 이동 결과로 매핑되는 규칙이 이산적으로 바뀌거나, 약한 확률적 miscontrol이 발생하는 action-semantics regime다.
> 

기본 remap은 다음처럼 둔다.

$\tilde{a}_t=\Pi_{r_t^{ctrl}}(a_t)$

예를 들어 clockwise remap은 다음과 같다.

$\Pi_{cw}(W)=D,\Pi_{cw}(D)=S,\Pi_{cw}(S)=A,\Pi_{cw}(A)=W$

좌우 반전은 다음과 같다.

$\Pi_{lr}(A)=D,\Pi_{lr}(D)=A,\Pi_{lr}(W)=W,\Pi_{lr}(S)=S$

약한 miscontrol은 다음처럼 둔다.

$\displaystyle \tilde{a}t = \begin{cases} \Pi{r_t^{ctrl}}(a_t), & \text{with probability } 1 - p_{slip} \\ a' \sim \text{NeighborActions}(a_t), & \text{with probability } p_{slip} \end{cases}$

### 전역 기본 효용

전역적으로는 identity control이 유리하다. 하지만 control-drift가 생겼다고 항상 correction해야 하는 것은 아니다. 짧은 구간이라면 remap을 감안해 adaptation하는 것이 더 싸다.

### local override

특정 interference field 안에서는 control-drift가 일시적으로 바뀔 수 있다. 문 앞이나 narrow corridor에서는 작은 remap도 치명적이다. 반대로 넓은 공간에서 짧은 이동만 필요하면 adaptation으로 충분할 수 있다.

### 잘못 추정될 때 생기는 비용

control-drift를 잘못 추정하면 다음 비용이 생긴다.

- wrong movement
- collision
- hazard tile 진입
- target cell 이탈
- unnecessary correction
- detour 증가
- forced reset

이 변수가 본 논문의 가장 강한 hard case를 만든다. 왜냐하면 control-drift는 state-only 모델이 “위치가 예상과 달라졌다”로만 볼 수 있지만, 제안모델은 “action semantics 자체가 바뀌었다”는 alternative regime를 세울 수 있기 때문이다.

---

# 3.18 Task A/B/C/D Final Design

각 task는 단순 puzzle이 아니다. 각 task는 서로 다른 regime ambiguity와 action relevance를 드러내기 위한 실험 장치다. 기존 STEP 3에서도 Task A는 mobility와 interaction, Task B는 vision과 mobility, Task C는 noise와 control-drift, Task D는 interaction과 noise를 중심 factor로 둔다.

---

## 3.18.1 Task A: Weight-Order + Interaction Calibration

### task 목적

Task A의 목적은 4개의 조각을 올바른 순서로 배치하고, 마지막 altar에서 interaction target band를 맞추는 것이다. 조각은 서로 다른 weight를 가지고, 무거운 조각을 들수록 mobility가 낮아진다.

weight set은 다음처럼 둔다.

$\mathcal{W}={0.20,0.40,0.60,0.80}$

조각 운반 중 mobility penalty는 다음과 같다.

$\Delta m_t^{carry}=-w_j$

각 조각을 처음 들 때 interaction과 noise에 persistent shift를 줄 수 있다.

$\Delta i_j\sim U_{0.01}[-0.10,0.10]$

$\Delta n_j\sim U_{0.01}[-0.03,0.03]$

최종 altar target은 다음처럼 episode마다 샘플링한다.

$\tau_i\sim U_{0.01}[-0.20,0.20]$

성공 조건은 다음이다.

$\text{Success}_A=\mathbf{1}[\text{heavy-to-light order correct}]\cdot\mathbf{1}[i_t\in[\tau_i-0.02,\tau_i+0.02]]$

### 주 상태값

- mobility `m`
- interaction `i`

### 보조 상태값

- noise `n`

### local cue

조각 주변에는 weight cue가 약하게 주어진다. 예를 들어 tile mark, 조각 크기, 주변 pressure plate pattern이 weight order를 암시한다. altar 주변에는 interaction target band를 추론할 수 있는 cue가 있다. 그러나 `τ_i` 값을 숫자로 직접 알려주면 안 된다.

### 잘못된 hypothesis

Task A에서 흔한 wrong hypothesis는 다음이다.

1. 조각 운반으로 인한 mobility penalty를 일시 state 변화로만 보고, burdened mobility regime를 놓침
2. interaction target band를 `i≈0`으로 잘못 믿음
3. noise shift로 인한 interaction drift를 단순 observation noise로 처리
4. heavy-to-light order를 local cue가 아니라 trial-and-error로 해결하려 함

### 왜 falsification-driven planning이 드러나는가?

Task A는 correction과 planning의 관계를 잘 보여준다. current hypothesis에서는 “지금 바로 altar interaction”이 최선일 수 있지만, alternative hypothesis에서는 `i_t`가 target band에서 벗어나 있으므로 `i^+` 또는 `i^-` correction 후 interaction이 최선일 수 있다. 즉 regime hypothesis 차이가 action flip을 만든다.

---

## 3.18.2 Task B: Vision-Positive Selection + Zero-Mobility Gate

### task 목적

Task B의 목적은 4개의 stele 중 vision-positive stele만 켜고, 최종 interaction cell에서 mobility를 0 근처로 맞춘 뒤 문을 여는 것이다. 기존 STEP 3도 Task B를 vision-positive stele 선택과 zero-mobility gate로 정의하고, 마지막 2 tick 동안 vision 변화가 없어야 하며, interaction cell에서 `m_t∈[-0.02,0.02]` 조건을 둔다.

각 stele ON 시 상태 변화는 다음처럼 둔다.

$\Delta v_k\sim U_{0.01}[-0.10,0.10]$

$\Delta m_k\sim U_{0.01}[-0.10,0.10]$

$\Delta d_k\sim U_{0.01}[-0.03,0.03]$

정확히 2개는 vision-positive이고 2개는 non-positive다.

$|{k:\Delta v_k>0}|=2$

성공 조건은 다음이다.

$\text{Success}B=\mathbf{1}[\text{only vision-positive steles are ON}]\cdot\mathbf{1}[m_t\in[-0.02,0.02]]\cdot\mathbf{1}[\Delta v{t-2:t}=0]\cdot\mathbf{1}[E\text{ at door}]$

### 주 상태값

- vision `v`
- mobility `m`

### 보조 상태값

- control-drift `d`

### local cue

stele 주변에는 vision-positive인지 추론할 수 있는 visual cue가 있다. 단, cue는 현재 vision level에 따라 보이거나 안 보일 수 있다. 따라서 vision을 높이면 정보를 더 잘 얻지만, 마지막 문 앞에서는 vision 변화가 없어야 한다.

### 잘못된 hypothesis

Task B에서 흔한 wrong hypothesis는 다음이다.

1. vision-positive stele을 외형 cue가 아니라 방 위치로 외움
2. mobility를 높게 유지하는 전역 효용만 믿고 zero-mobility gate를 놓침
3. subtle control perturbation을 단순 이동 실수로 봄
4. 마지막 2 tick 안정 조건을 무시하고 door interaction 실패

### 왜 falsification-driven planning이 드러나는가?

Task B는 “전역 기본 효용 + local override”를 가장 잘 보여준다. 평소에는 vision과 mobility가 높을수록 좋다. 하지만 문 앞에서는 mobility를 0 근처로 맞춰야 하고, vision은 안정되어야 한다. 따라서 planner는 “항상 크게 만들기”가 아니라 “지금 local condition이 무엇인가”를 추론해야 한다.

---

## 3.18.3 Task C: Noise-Zero Multi-Stele + Control-Drift Tracking

### task 목적

Task C는 본 논문의 핵심 hard case다. 목적은 여러 stele을 활성화하되, 각 stele interaction 시점에서 noise를 0 근처로 맞추고, 동시에 control-drift를 추적하는 것이다. 기존 STEP 3에서도 Task C는 noise와 control-drift를 주 factor로 두고, action semantics 자체가 흔들리는 control regime 변화를 추적해야 하므로 state-only 모델이 취약해지는 방이라고 정의되어 있다.

활성 stele 수는 다음처럼 샘플링한다.

$N_{stele}\sim {2,3,4}$

방향별 noise increment는 다음처럼 둔다.

$\Delta n_W,\Delta n_A,\Delta n_S,\Delta n_D\sim U_{0.01}[-0.10,0.10]$

방 진입 시 initial control-drift bin은 다음 중 하나다.

$d_0\in{-0.70,-0.35,0.00,0.35,0.70}$

각 stele 성공 조건은 다음이다.

$n_t\in[-0.02,0.02]$

모든 활성 stele을 완료하면 성공이다.

$\text{Success}C=\prod{k=1}^{N_{stele}}\mathbf{1}[n_{t_k}\in[-0.02,0.02]]\cdot\mathbf{1}[\text{all active steles completed}]$

### 주 상태값

- noise `n`
- control-drift `d`

### 보조 상태값

- mobility `m`

### local cue

stele 주변에는 방향별 noise correction cue가 있다. 예를 들어 서쪽 stele 주변 pattern은 `A` 방향 이동이 noise를 낮추는지 높이는지 암시할 수 있다. 그러나 cue가 항상 완전하지는 않다. agent는 action outcome을 통해 현재 noise-control coupling을 갱신해야 한다.

### 잘못된 hypothesis

Task C에서 흔한 wrong hypothesis는 다음이다.

1. control-drift를 mobility latency로 오해
2. `W`를 눌렀을 때 예상과 다른 이동을 단순 collision으로 해석
3. noise-zero 실패를 interaction 실수로 오해
4. small drift를 무시하다가 cumulative control cost를 키움
5. current remap hypothesis를 오래 붙잡음

### 왜 falsification-driven planning이 드러나는가?

Task C는 current와 alternative hypothesis의 action이 가장 잘 갈린다. current hypothesis가 identity control이면 목표 방향으로 `W`를 누르지만, alternative hypothesis가 clockwise remap이면 같은 목표를 위해 `A`나 다른 입력을 눌러야 할 수 있다. 이 차이는 action flip으로 직접 나타난다.

따라서 Task C는 다음 metric에서 제안법의 강점을 보여야 한다.

- wrong-hypothesis persistence time 감소
- action flip precision 증가
- switch detection delay 감소
- compute-normalized return 증가
- control-drift OOD 성능 향상

---

## 3.18.4 Task D: Tile-Induced Interaction Drift + Final Zero-Interaction Altar

### task 목적

Task D의 목적은 tile을 지나며 interaction drift를 누적하고, 최종 altar에서 interaction을 0 근처로 맞추는 것이다. 기존 STEP 3에서도 Task D는 interaction과 noise를 주 factor로 두며, tile 최초 통과 시 interaction/noise/vision이 변하고, 최종 altar는 `i_t∈[-0.02,0.02]` 조건을 요구하며, 오답 interaction 3회 누적 시 중앙홀로 강제복귀하는 구조로 정의되어 있다.

각 tile 최초 통과 시 변화는 다음이다.

$\Delta i_t\sim U_{0.01}[-0.10,0.10]$

$\Delta n_t\sim U_{0.01}[-0.05,0.05]$

$\Delta v_t\sim U_{0.01}[-0.03,0.03]$

최종 성공 조건은 다음이다.

$\text{Success}_D=\mathbf{1}[i_t\in[-0.02,0.02]]\cdot\mathbf{1}[E\text{ at final altar}]$

오답 interaction 3회 누적 시 reset이다.

$\text{Reset}_D=\mathbf{1}[\text{wrong interaction count}\ge 3]$

### 주 상태값

- interaction `i`
- noise `n`

### 보조 상태값

- vision `v`

### local cue

tile pattern은 interaction drift 방향을 약하게 암시한다. 하지만 오차 크기를 직접 알려주지는 않는다. feedback은 success/fail count 중심이다. 따라서 agent는 tile을 지나며 누적된 drift를 기억하고, final altar 직전에 correction해야 한다.

### 잘못된 hypothesis

Task D에서 흔한 wrong hypothesis는 다음이다.

1. tile-induced interaction drift를 일회성 noise로 처리
2. final altar target을 항상 `i=0`이라고 믿지만 실제 drift 누적을 반영하지 못함
3. failure feedback만 보고 target band를 정확히 추정하지 못함
4. correction보다 immediate interaction을 선택해 reset 유발

### 왜 falsification-driven planning이 드러나는가?

Task D는 정밀 endpoint correction의 중요성을 보여준다. 이동 중에는 adaptation이 유리할 수 있지만, final altar 앞에서는 correction이 필요하다. current hypothesis에서는 즉시 `E`가 최선일 수 있지만, alternative hypothesis에서는 `i^-`, `i^+`, wait 후 `E`가 최선일 수 있다. 이게 action relevance와 compute reallocation을 드러낸다.

---

# 3.19 Target Band and Local Override

## 3.19.1 모든 상태를 항상 0으로 맞추면 안 되는 이유

초기 상태값을 다음처럼 둘 수 있다.

$x_0=(0,0,0,0,0)$

하지만 이것은 시작 baseline일 뿐이다. 목표가 아니다. 모든 상태를 0으로 유지하라는 reward를 주면 agent는 task를 해결하지 않고 상태 안정화만 하려 한다. 이는 논문 목적과 맞지 않는다.

상태값은 context-dependent하다.

- 어떤 상황에서는 vision을 키워야 한다.
- 어떤 상황에서는 vision 변화가 멈춰야 한다.
- 어떤 상황에서는 mobility를 높여 빨리 이동해야 한다.
- 어떤 상황에서는 mobility를 0 근처로 맞춰야 한다.
- 어떤 상황에서는 interaction을 빠르게 해야 한다.
- 어떤 상황에서는 interaction target band를 정확히 맞춰야 한다.
- 어떤 상황에서는 control-drift를 correction해야 한다.
- 어떤 상황에서는 remap에 adaptation하는 게 더 싸다.

따라서 상태값 최적화는 “좋은 값 하나 찾기”가 아니라 “현재 task phase와 local condition에 맞는 목표구간을 추론하는 문제”다.

---

## 3.19.2 default utility + local override

각 상태값에는 전역 기본 효용이 있다.

$U^{default}(x_t)=w_v v_t+w_m m_t+w_i i_t-w_n|n_t|-w_d|d_t|$

하지만 local override가 발생하면 이 기본 효용보다 target band condition이 우선한다.

$\text{TargetBand}_j=[\tau_j-\alpha_j,\tau_j+\alpha_j]$

local objective는 다음처럼 둘 수 있다.

$U^{local}_j(x_t)=-\mathbf{1}[x_t^{(j)}\notin \text{TargetBand}_j]\cdot C_j^{miss}$

최종 utility는 task phase에 따라 혼합된다.

$U_t=(1-\omega_t)U^{default}(x_t)+\omega_t U^{local}(x_t,\tau)$

여기서 `ω_t`는 local override strength다. 예를 들어 agent가 final altar 근처에 있으면 `ω_t`가 커지고, 일반 이동 중이면 `ω_t`가 작다.

이 구조가 핵심이다. agent는 평소에는 효율을 추구하지만, 특정 local condition 앞에서는 정확도를 추구해야 한다.

---

## 3.19.3 maximize / match-to-band / threshold task

task condition은 세 종류로 나누는 것이 좋다.

### maximize type

상태값이 클수록 유리한 조건이다. 예를 들어 vision을 높이면 더 넓게 보고, mobility를 높이면 더 빨리 이동한다.

$J_{max}(x^{(j)}_t)=x^{(j)}_t$

### match-to-band type

특정 target band에 맞춰야 하는 조건이다. interaction altar, zero-mobility gate, noise-zero stele이 여기에 해당한다.

$J_{band}(x_t^{(j)},\tau_j)=-|x_t^{(j)}-\tau_j|$

성공은 다음처럼 정의한다.

$\mathbf{1}[|x_t^{(j)}-\tau_j|\le \alpha_j]$

### threshold type

어떤 임계값을 넘거나 넘지 않아야 하는 조건이다. vision-positive stele selection, fail count threshold, door open condition 등이 여기에 해당한다.

$J_{thresh}(x_t^{(j)})=\mathbf{1}[x_t^{(j)}\ge \zeta_j]$

이 세 유형을 섞어야 agent가 단순히 상태값을 키우거나 줄이는 정책으로 해결할 수 없다. 이 구조가 있어야 world model planning이 필요해진다.

---

# 3.20 Invisible Noise Field Final Design

## 3.20.1 invisible field를 왜 넣는가?

invisible noise field는 단순 방해물이 아니다. 이 field의 목적은 agent가 보이지 않는 원인 때문에 상태값이 조금씩 변하는 상황을 만드는 것이다. 즉 hidden state tracking, reveal-vs-shift 구분, sparse coupling 추론, small drift 감지를 동시에 요구하게 만드는 장치다.

field source는 직접 보이지 않는다. agent는 특정 위치에 들어갔을 때 상태값이 변하거나, interaction latency가 바뀌거나, control outcome이 흔들리는 것을 보고 field 존재를 추론해야 한다.

---

## 3.20.2 모든 상태를 동시에 왜곡하면 안 되는 이유

invisible field가 vision, mobility, interaction, noise, control-drift를 모두 동시에 흔들면 너무 강한 교란이 된다. 그러면 agent가 어떤 원인이 어떤 결과를 만들었는지 식별할 수 없다. 또한 baseline도, 제안모델도 모두 어려워져서 논문 메시지가 흐려진다.

따라서 최종 설계는 sparse coupling이다.

$x_{t+1}^{(k)}=x_t^{(k)}+\sum_{j\in\mathcal{F}}g_{j,k}(p_t)\epsilon_{j,t}$

여기서 `g_{j,k}`는 field `j`가 state dimension `k`에 영향을 주는 coupling indicator 또는 strength다. sparse coupling 조건은 다음처럼 둔다.

$|{k:g_{j,k}\neq 0}|\le 2$

즉 하나의 field는 최대 1~2개 상태값만 흔든다.

---

## 3.20.3 map family-based coupling randomness

coupling은 완전 랜덤이면 안 된다. 완전 랜덤이면 agent가 family-level rule을 학습할 수 없다. 따라서 map family마다 제한된 coupling pattern을 둔다.

예시:

- visibility field: `noise + vision`
- friction field: `noise + mobility`
- interaction interference field: `noise + interaction`
- control interference field: `noise + control-drift`

이 구조는 기존 감사 결과에서 확정된 방향과 일치한다. noise는 공통 숨은 원인이지만 모든 상태를 동시에 흔들지 않고, map family별로 1~2개 상태에 제한적으로 coupling되어야 agent가 어떤 종류의 invisible field인지 추론할 수 있다.

---

## 3.20.4 field mean drift와 event-triggered shift

field의 평균은 두 방식으로 변한다.

첫째, small cumulative drift다.

$\mu_{j,t+1}=\mu_{j,t}+\eta_{j,t}$

$\eta_{j,t}\sim\mathcal{N}(0,\sigma_{\eta}^2)$

둘째, event-triggered shift다.

$\mu_{j,t+1}\leftarrow \mu_{j,t}+\delta_j$

기존 STEP 3도 invisible field mean이 평소에는 작은 drift를 만들고, checkpoint나 interaction 후에는 event-triggered shift를 만들도록 정의했다. 이 구조는 “정보 갱신 vs 규칙 전환”을 실제 동역학 수준에서 구현하기 위한 장치다.

---

# 3.21 Drift / Shift Scenarios

## 3.21.1 Abrupt event-triggered shift

abrupt shift는 checkpoint, room entry, 특정 stele activation, final altar 접근 같은 event 후 field mean이나 control mapping이 갑자기 바뀌는 경우다.

예시:

$r_t^{ctrl}=\text{identity}\rightarrow r_{t+1}^{ctrl}=\text{cw}$

또는

$\mu_{j,t+1}\leftarrow \mu_{j,t}+0.15$

이 경우 baseline도 어느 정도 감지할 수 있다. 변화가 크기 때문이다. 따라서 이 scenario는 “제안법만 풀 수 있다”보다 “제안법이 더 빠르게 감지하고 action flip timing을 더 정확히 맞춘다”를 보여주는 용도다.

## 3.21.2 Small cumulative drift

small drift는 변화량이 작지만 누적되면 행동 비용을 크게 만드는 경우다.

$$
$d_{t+1}=d_t+\epsilon_t,\quad \epsilon_t\sim U[-0.01,0.03]$
$$

이 경우 novelty detector나 event-only gate는 취약하다. 큰 이벤트가 없고, 단일 step mismatch도 작기 때문이다. 하지만 current hypothesis를 오래 유지하면 wrong movement가 누적된다. 이 scenario가 제안법의 핵심 hard case다. 감사 결과에서도 큰 변화뿐 아니라 작고 애매하지만 누적 오차를 만드는 drift를 반드시 포함해야 하며, detection delay, wrong-hypothesis persistence time, cumulative control cost, compute frontier가 중요하다고 정리되어 있다.

## 3.21.3 Periodic disturbance

periodic disturbance는 일정 주기로 miscontrol이나 noise spike가 발생하는 경우다.

$\displaystyle p_{slip}(t) = \begin{cases} p_{high}, & t \pmod K = 0 \\ p_{low}, & \text{otherwise} \end{cases}$

이 경우 항상 correction하는 것은 비효율적이다. agent는 wait하거나 timing을 맞추거나 remap에 adaptation해야 한다. 이 scenario는 adaptation vs correction 판단을 검증한다. 기존 감사 결과에서도 짧은 구간 반복 drift, 4칸마다 주기적으로 발생하는 drift, 패턴이 예측 가능한 경우에는 correction보다 adaptation이 유리하다고 정리되어 있다.

## 3.21.4 Hidden local hazard

hidden local hazard는 특정 위치 주변에서만 상태값을 흔드는 field다. agent는 field source를 직접 보지 못하고, 상태 변화와 local cue를 통해 추론해야 한다.

이 scenario는 reveal-vs-shift 구분에 중요하다. agent가 hazard 영향권에 처음 들어간 것은 reveal일 수 있다. 하지만 같은 field의 mean이 event 후 바뀌면 shift다. 제안법은 이 둘을 구분해야 한다.

---

# 3.22 Baselines

baseline 설계의 원칙은 명확하다. 쉬운 케이스에서는 baseline도 어느 정도 잘해야 한다. 그래야 제안법이 hard case에서 이기는 것이 의미 있다.

## 3.22.1 Reactive policy

world model 없이 현재 observation만 보고 행동한다. 이 baseline은 local cue가 충분하고 drift가 약한 쉬운 케이스에서는 작동할 수 있다. 하지만 hidden regime와 delayed effect가 있는 상황에서는 취약해야 한다.

## 3.22.2 Fixed-k planner

항상 고정 rollout 수와 고정 horizon으로 planning한다.

$h_t=h_{fixed},\quad k_t=k_{fixed}$

이 baseline은 compute를 일정하게 쓰므로 fair comparison에 중요하다. 그러나 current hypothesis가 틀렸을 때 alternative로 reallocation하지 못하면 wrong-hypothesis persistence가 길어져야 한다.

## 3.22.3 Always-plan

매 tick planning한다. 성능은 높을 수 있지만 compute cost가 크다. 이 baseline은 compute-normalized return에서 손해를 봐야 한다.

## 3.22.4 Uncertainty gate

state uncertainty나 value uncertainty가 높을 때 planning한다. 이 baseline은 “불확실하면 더 본다” 계열이다. 하지만 uncertainty가 높아도 action이 안 바뀌면 planning이 낭비되고, uncertainty가 낮아 보여도 current hypothesis가 틀린 경우를 놓칠 수 있다.

## 3.22.5 Novelty-style mismatch gate

prediction error나 novelty score가 높을 때 planning한다. 이 baseline은 anomaly detector와 유사하다. reveal과 shift를 구분하지 못하면 새로운 object를 볼 때도 planning을 켜고, subtle drift는 놓칠 수 있다.

## 3.22.6 Event-only gate

checkpoint, room entry, stele activation 같은 event가 있을 때만 planning한다. abrupt shift에는 강하지만 small cumulative drift에는 취약하다.

## 3.22.7 Adaptive lookahead

위험도나 uncertainty에 따라 horizon만 조절한다. 이 baseline은 “더 멀리 볼지”를 조절하지만, 어떤 hypothesis 아래에서 볼지는 명시적으로 바꾸지 않는다. 따라서 제안법과 가장 중요한 비교 대상이다.

## 3.22.8 Sparse imagination류

일부 state/action 후보만 상상하는 sparse rollout 방법이다. compute를 아끼는 baseline으로 유용하다. 하지만 sparsity가 hypothesis-aware가 아니면, current hypothesis 아래에서만 sparse하게 상상할 수 있다.

## 3.22.9 제안모델 변형들

제안법 내부 변형도 baseline으로 둔다.

- FRC-WM full
- FRC-WM without alternative rollout
- FRC-WM with allocation only, no reallocation
- FRC-WM with uncertainty-only allocator
- FRC-WM with falsification only
- FRC-WM with action relevance only

이렇게 해야 “성능 향상이 그냥 모델 크기나 planning 양 때문이 아니라, falsification + action relevance + reallocation 결합에서 온다”를 보일 수 있다.

---

# 3.23 Ablations

## 3.23.1 no regime

hidden regime를 제거하고 hidden state만 유지한다. 이 ablation은 state-only world model이 action semantics shift를 얼마나 못 잡는지 보여준다.

예상 결과:

- next-observation NLL은 어느 정도 괜찮을 수 있음
- control-drift hard case에서 wrong-hypothesis persistence 증가
- action flip precision 감소
- Task C 성능 하락

## 3.23.2 no change-point

change-point posterior를 제거한다. 이 모델은 gradual state update와 regime transition을 구분하기 어렵다.

예상 결과:

- abrupt shift detection delay 증가
- reveal-vs-shift classification accuracy 감소
- event-triggered field shift에서 reset 증가

## 3.23.3 raw mismatch only

likelihood ratio 대신 raw prediction error만 사용한다. 이 ablation은 novelty detector 계열이다.

예상 결과:

- 새로운 object reveal에서 false positive planning 증가
- subtle drift에서 false negative 증가
- compute frontier 악화

## 3.23.4 no action relevance

falsification은 계산하지만 action relevance 없이 planning한다. 이 ablation은 “규칙이 달라 보이면 무조건 planning”하는 모델이다.

예상 결과:

- planning calls 증가
- planning-usefulness ratio 감소
- compute-normalized return 감소
- 쉬운 구간에서 불필요한 planning 증가

## 3.23.5 risk-only gate

risk score만 보고 planning한다. 이 모델은 위험한 상황에서는 planning하지만, 위험하지 않아 보여도 action flip이 중요한 상황을 놓칠 수 있다.

## 3.23.6 no memory

recurrent memory 또는 history belief를 제거한다. 이 ablation은 partial observability에서 과거 action outcome이 얼마나 중요한지 보여준다.

예상 결과:

- invisible field localization error 증가
- small drift 추적 실패
- Task D 누적 drift 처리 실패

## 3.23.7 monolithic regime

factorized regime 대신 단일 regime label을 사용한다. 이 ablation은 compositional generalization에서 약해야 한다.

예상 결과:

- in-domain은 어느 정도 가능
- factor recombination OOD에서 큰 성능 하락
- unseen joint factor pattern에서 regime posterior calibration 악화

기존 STEP 3도 regime를 monolithic label이 아니라 `vision, mobility, interaction, noise, control` factorized code로 두는 것이 hand-crafted semantic regime 위험을 줄이고 compositional generalization을 만들 수 있다고 설명한다.

## 3.23.8 no faithfulness

regime latent가 Q landscape와 행동 선택에 실제 영향을 주도록 하는 faithfulness constraint를 제거한다.

예상 결과:

- explanation은 그럴듯하지만 intervention 시 action flip이 줄어듦
- explanation faithfulness score 감소
- counterfactual rollout fidelity 감소

## 3.23.9 no adaptation/correction distinction

drift가 생기면 항상 correction하거나, 항상 adaptation하도록 고정한다.

예상 결과:

- 장기 drift에서는 always-adapt가 손해
- periodic drift에서는 always-correct가 손해
- final precision endpoint에서는 always-adapt가 실패
- 제안법은 phase-dependent로 우위

## 3.23.10 no sparse coupling

invisible field가 모든 상태를 동시에 흔들거나 coupling structure를 제거한다.

예상 결과:

- 식별성 악화
- field family inference 실패
- reveal-vs-shift ambiguity 증가
- 모델 간 차이가 흐려짐

---

# 3.24 OOD Protocol

기존 STEP 3은 room-task permutation, factor recombination, parameter shift, observation shift를 주요 OOD로 두고, 이후 invisible hazard placement OOD까지 확장하는 구조를 갖고 있다.

## 3.24.1 Room-task permutation OOD

훈련에서는 일부 room-task assignment만 사용한다. 테스트에서는 unseen assignment를 사용한다.

예시:

- train: north=A, east=B, south=C, west=D 중심
- test: north=C, east=A, south=D, west=B

검증 질문:

> agent가 방 위치를 외웠는가, 아니면 task rule과 local cue를 이해했는가?
> 

제안법은 위치가 바뀌어도 local evidence와 regime hypothesis를 바탕으로 task를 풀어야 한다.

## 3.24.2 Factor recombination OOD

훈련에서는 일부 factor 조합만 보여준다.

- train: `(vision + mobility)`, `(mobility + interaction)`, `(noise + control)`, `(interaction + noise)`
- test: `(vision + noise)`, `(mobility + control)`, `(interaction + control)`

검증 질문:

> agent가 regime factor를 조합적으로 일반화하는가?
> 

monolithic regime 모델은 여기서 약해야 한다. factorized regime 모델은 unseen 조합에서도 각 factor를 재조합해야 한다.

## 3.24.3 Parameter shift OOD

같은 규칙 종류지만 수치 범위가 달라진다.

예시:

$r_{hazard}^{train}\in[2,3],\quad r_{hazard}^{test}\in[4,5]$

$\alpha_i^{train}=1.0,\quad \alpha_i^{test}=1.5$

검증 질문:

> 같은 dynamics family 안에서 강도나 scale이 바뀌어도 robust한가?
> 

제안법은 current hypothesis가 parameter mismatch로 틀어질 때 alternative hypothesis 또는 recalibrated rollout으로 대응해야 한다.

## 3.24.4 Observation shift OOD

색, sprite, tile texture, icon만 바뀌고 underlying rule은 그대로다.

검증 질문:

> 겉모습 변화와 진짜 규칙 변화를 구분하는가?
> 

novelty detector는 observation shift에서 planning을 과도하게 켤 수 있다. 제안법은 action-outcome evidence가 regime shift를 지지하지 않으면 reallocation을 억제해야 한다.

## 3.24.5 Invisible field placement OOD

invisible field source count, placement prior, radius distribution이 바뀐다.

예시:

$N_{field}^{train}\in{1,2},\quad N_{field}^{test}\in{2,3}$

$p_{place}^{train}=\text{near-wall},\quad p_{place}^{test}=\text{near-door}$

검증 질문:

> hidden field 위치 prior가 바뀌어도 state/regime belief를 업데이트할 수 있는가?
> 

이 OOD는 hidden-state generalization과 reveal-vs-shift 구분을 동시에 본다.

---

# 3.25 Metrics

이 논문의 metric은 success rate 하나로 끝나면 안 된다. 기존 STEP 3도 task performance, compute, regime tracking, decision, world model quality, explanation, OOD robustness metric을 모두 포함해야 mechanism paper로 읽힌다고 정리했다.

---

## 3.25.1 Success Rate

### 무엇을 측정하는가?

episode 전체 성공률이다.

$\text{SuccessRate}=\frac{1}{N}\sum_{e=1}^{N}\mathbf{1}[G_{episode}^{(e)}=1]$

### 왜 중요한가?

최종적으로 agent가 task를 완료해야 한다. 아무리 regime tracking이 좋아도 task success가 낮으면 의미 없다.

### 차이가 드러나는 곳

제안법은 특히 Task C, Task D, parameter shift OOD, factor recombination OOD에서 success rate가 좋아야 한다.

---

## 3.25.2 Return

### 무엇을 측정하는가?

task reward에서 step, failure, reset, planning, latency cost를 뺀 총합이다.

$\displaystyle R_{episode}=\sum_{t=1}^{T}R_t$

$$
$R_t=R_t^{task}-\lambda_{step}C_t^{step}-\lambda_{fail}C_t^{fail}-\lambda_{reset}C_t^{reset}-\lambda_{plan}C_t^{plan}-\lambda_{latency}C_t^{latency}$
$$

### 왜 중요한가?

success만 보면 always-plan이 유리할 수 있다. return은 비용까지 반영한다.

### 차이가 드러나는 곳

제안법은 always-plan과 비슷한 success를 더 낮은 planning cost로 달성하거나, fixed planner와 같은 compute에서 더 높은 return을 보여야 한다.

---

## 3.25.3 Average Episode Length

### 무엇을 측정하는가?

episode 완료 또는 실패까지 걸린 tick 수다.

$\displaystyle \text{EpisodeLength}=\frac{1}{N}\sum_{e=1}^{N}T_e$

### 왜 중요한가?

mobility latency, unnecessary correction, wrong movement, detour가 모두 episode length에 반영된다.

### 차이가 드러나는 곳

uncertainty gate나 novelty gate는 불필요한 planning/correction으로 episode length가 늘 수 있다. 제안법은 필요한 순간에만 reallocation하여 길이를 줄여야 한다.

---

## 3.25.4 Planning Calls

### 무엇을 측정하는가?

episode당 planning이 호출된 횟수다.

$\displaystyle \text{PlanningCalls}=\frac{1}{N}\sum_{e=1}^{N}\sum_{t=1}^{T_e}b_t^{plan}$

### 왜 중요한가?

이 논문은 더 많이 planning해서 이기는 논문이 아니다. 필요한 순간에 planning이 집중되는지를 보여야 한다.

### 차이가 드러나는 곳

always-plan은 높고, reactive는 0이다. 제안법은 planning calls가 중간 수준이어야 하며, hard case에서만 증가해야 한다.

---

## 3.25.5 Rollout Steps

### 무엇을 측정하는가?

총 rollout horizon × rollout count 비용이다.

$\displaystyle \text{RolloutSteps}=\sum_{t=1}^{T}b_t^{plan}h_tk_t|\mathcal{R}_t^{active}|$

### 왜 중요한가?

planning call 수가 같아도 horizon과 rollout 수가 다르면 compute cost가 다르다.

### 차이가 드러나는 곳

adaptive lookahead는 horizon을 늘려 rollout steps가 커질 수 있다. 제안법은 active hypothesis pool을 제한해 compute를 통제해야 한다.

---

## 3.25.6 Wall-clock / Compute-normalized Return

### 무엇을 측정하는가?

실제 실행 시간 또는 compute 단위당 return이다.

$\text{ComputeNormReturn}=\frac{R_{episode}}{1+\text{RolloutSteps}}$

또는 wall-clock 기준으로 다음처럼 둔다.

$\text{WallClockNormReturn}=\frac{R_{episode}}{1+\text{WallClockTime}}$

### 왜 중요한가?

논문의 핵심 claim은 performance-compute frontier다.

### 차이가 드러나는 곳

always-plan은 success가 높아도 compute-normalized return에서 손해를 봐야 한다. 제안법은 frontier에서 우상단에 있어야 한다.

---

## 3.25.7 Switch Detection F1

### 무엇을 측정하는가?

실제 regime switch를 얼마나 잘 감지했는지 본다.

$F1_{switch}=\frac{2\cdot Precision_{switch}\cdot Recall_{switch}}{Precision_{switch}+Recall_{switch}}$

### 왜 중요한가?

change-point posterior가 실제 regime transition과 맞는지 확인한다.

### 차이가 드러나는 곳

event-only gate는 abrupt shift에는 강하지만 small drift에는 약해야 한다. 제안법은 둘 모두에서 균형이 좋아야 한다.

---

## 3.25.8 Detection Delay

### 무엇을 측정하는가?

실제 shift 발생 후 모델이 감지하기까지 걸린 tick 수다.

$\text{Delay}=t_{detect}-t_{shift}$

### 왜 중요한가?

늦게 감지하면 이미 wrong-hypothesis rollout으로 비용을 낭비한다.

### 차이가 드러나는 곳

제안법은 small cumulative drift에서 delay를 줄여야 한다.

---

## 3.25.9 Falsification Calibration

### 무엇을 측정하는가?

`F_t^*`가 실제 current hypothesis error probability와 잘 맞는지 본다.

예를 들어 binning calibration error를 둔다.

$\displaystyle \text{FCE}=\sum_{b=1}^{B}\frac{|S_b|}{N}\left|\operatorname{acc}(S_b)-\operatorname{conf}(S_b)\right|$

### 왜 중요한가?

falsification score가 과신하면 planning을 과도하게 켜고, 과소신뢰하면 shift를 놓친다.

### 차이가 드러나는 곳

raw mismatch only는 observation shift에서 calibration이 깨질 수 있다. 제안법은 reveal-vs-shift를 구분해 calibration이 좋아야 한다.

---

## 3.25.10 Wrong-Hypothesis Persistence

### 무엇을 측정하는가?

current hypothesis가 실제 regime와 맞지 않는데도 유지되는 시간이다.

$\displaystyle \text{WHPT}=\sum_{t=1}^{T}\mathbf{1}[r_t^{cur}\neq r_t^{gt}]$

또는 shift 이후 persistence로 볼 수 있다.

$$
$\displaystyle \text{WHPT}_{post} = \sum_{t=t_{shift}}^{t_{recover}} \mathbb{1}[r_t^{cur} = r_{old}]$
$$

### 왜 중요한가?

이 논문의 핵심 failure mode가 wrong dynamics hypothesis persistence다. 따라서 이 metric은 central metric이어야 한다.

### 차이가 드러나는 곳

state-only, no-change-point, raw mismatch only는 WHPT가 길어야 한다. 제안법은 WHPT를 줄여야 한다.

---

## 3.25.11 Action Flip Precision

### 무엇을 측정하는가?

planning reallocation이 실제로 유용한 action change를 만들었는지 본다.

$\displaystyle \text{ActionFlipPrecision} = \frac{\#\{ \text{useful action flips} \}}{\#\{ \text{all action flips} \}}$

useful action flip은 다음 조건으로 정의할 수 있다.

$\text{UsefulFlip}_t=\mathbf{1}[a_t^{cur}\neq a_t^{alt}]\cdot\mathbf{1}[Q^{gt}(a_t^{alt})>Q^{gt}(a_t^{cur})]$

### 왜 중요한가?

이 논문은 “regime를 감지했다”가 아니라 “행동을 더 좋게 바꿨다”를 보여야 한다.

### 차이가 드러나는 곳

no action relevance 모델은 action flip precision이 낮아야 한다. 제안법은 planning call 수는 적어도 flip precision이 높아야 한다.

---

## 3.25.12 Counterfactual Rollout Fidelity

### 무엇을 측정하는가?

world model이 “다른 행동을 했더라면” 결과를 얼마나 정확히 예측하는지 본다.

$$
$\text{CRF}=\mathbb{E}_{a'\neq a_t}\left[d(\hat{o}_{t+1:t+h}^{a'},o_{t+1:t+h}^{a'})\right]$
$$

distance가 낮을수록 fidelity가 좋다.

### 왜 중요한가?

alternative hypothesis rollout이 실제 행동 비교에 쓸 만해야 한다. counterfactual fidelity가 낮으면 planner는 그럴듯한 상상만 하는 것이다.

### 차이가 드러나는 곳

no regime 또는 monolithic regime 모델은 unseen factor recombination에서 counterfactual fidelity가 떨어져야 한다.

---

## 3.25.13 Explanation Faithfulness

### 무엇을 측정하는가?

모델이 “control-drift 때문에 행동을 바꿨다”고 설명한다면, 실제로 control-drift latent를 intervention했을 때 Q-value와 action이 바뀌는지 본다.

$$
$\displaystyle \text{Faithfulness}=\mathbb{E}\left[\mathbf{1}[\arg\max_a Q(\hat{s}_t,r_t,a)\neq \arg\max_a Q(\hat{s}_t,\tilde{r}_t,a)]\right]$
$$

또는 value shift로 본다.

$$
$\text{ValueShift}=\left|Q(\hat{s}_t,r_t,\cdot)-Q(\hat{s}_t,\tilde{r}_t,\cdot)\right|_1$
$$

### 왜 중요한가?

regime latent가 사후 설명용 장식이 아니라 실제 decision variable이어야 한다.

### 차이가 드러나는 곳

no faithfulness ablation은 explanation text나 label은 있어도 intervention action flip rate가 낮아야 한다. 제안법은 높아야 한다.

---

## 3.25.14 OOD별 성능

각 OOD에서 success, return, WHPT, compute-normalized return을 따로 보고한다.

$\text{RelativeDrop}_{OOD}=\frac{\text{Perf}_{ID}-\text{Perf}_{OOD}}{\text{Perf}_{ID}}$

### 왜 중요한가?

제안법은 단순 in-domain 성능보다 regime factor 일반화에서 강해야 한다.

### 차이가 드러나는 곳

- permutation OOD: 위치 암기 vs task rule 이해
- factor recombination OOD: factorized regime 일반화
- parameter shift OOD: dynamics scale robustness
- observation shift OOD: visual novelty와 true regime shift 분리
- invisible placement OOD: hidden field 추론 일반화

---

# 3.26 Easy Cases vs Hard Cases

## 3.26.1 baseline도 가능한 쉬운 케이스

좋은 실험은 baseline이 전부 실패하는 환경이 아니다. baseline도 풀 수 있는 쉬운 케이스가 있어야 한다.

쉬운 케이스는 다음이다.

1. abrupt shift가 event token과 강하게 동반됨
2. local cue가 명확함
3. target band가 넓음
4. control-drift가 identity 또는 단순 flip으로 고정됨
5. invisible field coupling이 약함
6. 한두 step correction만으로 해결됨
7. action relevance가 낮아도 task 성공 가능

이런 경우 reactive, fixed planner, event-only gate도 어느 정도 성공해야 한다.

## 3.26.2 제안법 우위가 드러나는 hard case

hard case는 다음 조건이 결합되어야 한다.

1. small cumulative drift
2. sparse invisible coupling
3. reveal-vs-shift ambiguity
4. current와 alternative가 서로 다른 action을 추천
5. correction과 adaptation 중 선택 필요
6. final precision endpoint 존재
7. wrong hypothesis를 오래 유지하면 reset 또는 큰 latency cost 발생
8. observation shift와 regime shift가 섞여 있음

이 경우 baseline은 다음처럼 실패해야 한다.

- reactive: hidden drift 누적을 못 봄
- fixed planner: current hypothesis 아래에서만 rollout
- always-plan: compute cost 과다
- uncertainty gate: action relevance 없는 구간에서도 planning 낭비
- novelty gate: reveal에 false positive, subtle drift에 false negative
- event-only: small drift 놓침
- adaptive lookahead: horizon은 늘리지만 hypothesis를 바꾸지 못함

제안법은 다음을 보여야 한다.

1. WHPT 감소
2. action flip precision 증가
3. planning-usefulness ratio 증가
4. compute-normalized return 증가
5. factor recombination OOD 성능 유지

기존 STEP 3도 최종적으로 state-only나 uncertainty gate는 hidden regime mismatch를 충분히 못 잡고, 제안법은 planning call을 더 많이 하는 게 아니라 필요한 순간에 집중시키며, wrong-hypothesis persistence와 action-flip timing 개선이 success/return/compute frontier 개선으로 이어져야 한다고 정리했다.

---

# 3.27 Statistical Protocol

최종 실험은 다음 기준으로 보고한다.

- seed: 최소 10개
- metric: mean ± 95% bootstrap CI
- iso-budget condition에서 paired comparison
- compute-performance frontier는 AUC로 비교
- switch metric은 macro-F1와 delay를 함께 보고
- OOD는 in-domain 대비 relative drop도 보고
- room-wise success를 A/B/C/D separately 보고
- hard/easy case를 분리 보고

compute frontier는 다음처럼 정의할 수 있다.

$$
\text{AUC-CF}=\int_{\bar{C}*{min}}^{\bar{C}*{max}}\text{Return}(\bar{C})d\bar{C}
$$

이 protocol이 필요한 이유는 명확하다. 제안법이 compute를 더 많이 써서 이긴 것인지, 아니면 같은 compute에서 더 잘하고 같은 성능에서 덜 계산한 것인지 분리해야 한다.

---

# 3.28 Reviewer Defense

## 3.28.1 “2D 장난감 환경 아닌가?”

방어는 다음이다.

> 이 환경은 geometry realism benchmark가 아니라 wrong-hypothesis-aware planning mechanism benchmark다. geometry를 단순화한 이유는 regime factor, hidden disturbance, reveal-vs-shift ambiguity, compute reallocation의 효과를 통제해서 분해하기 위해서다.
> 

또한 단일 map이 아니라 map family, parameter randomization, task permutation, factor recombination, invisible placement OOD를 사용하므로 단순 암기가 아니다.

## 3.28.2 “hand-crafted task 아닌가?”

방어는 다음이다.

> task는 hand-crafted label을 맞히기 위한 것이 아니라, 서로 다른 dynamics factor를 자극하는 controlled templates다. Task A/B/C/D는 각각 mobility-interaction, vision-mobility, noise-control, interaction-noise family를 자극하며, OOD에서는 factor recombination으로 훈련 조합 밖의 regime reasoning을 평가한다.
> 

## 3.28.3 “detector game 아닌가?”

방어는 metric으로 한다.

> 우리는 switch detection만 보고하지 않는다. Success, return, compute-normalized return, action flip precision, counterfactual rollout fidelity, explanation faithfulness를 함께 보고한다. 즉 regime를 맞히는 것이 목적이 아니라, regime belief가 rollout과 행동을 바꿔 실제 closed-loop 성능을 개선하는지를 본다.
> 

## 3.28.4 “adaptive planning 아닌가?”

방어는 baseline으로 한다.

> adaptive lookahead, uncertainty gate, novelty gate, event-only gate와 비교한다. 제안법은 horizon을 늘리는 것이 아니라 current hypothesis에서 alternative hypothesis로 rollout compute를 재배치한다. 차이는 WHPT, action flip precision, planning-usefulness ratio에서 드러나야 한다.
> 

---

# 3.29 Part 3 최종 결론

RG-4F는 단순한 2D 퍼즐이 아니다. 이 환경은 다음 질문을 검증하기 위해 설계된 통제된 world-model planning benchmark다.

> agent가 부분관측 환경에서 보이지 않는 상태 변화와 실제 규칙 변화를 구분하고, 현재 dynamics hypothesis가 틀렸다는 증거가 누적될 때, 그 차이가 실제 행동을 바꿀 만큼 중요한 경우에만 alternative-regime rollout으로 compute를 재배치할 수 있는가?
> 

최종 실험은 다음 메시지를 보여야 한다.

1. 중앙홀 + 4방 구조는 geometry가 아니라 regime composition을 통제하기 위한 장치다.
2. 부분관측은 hidden state/regime tracking을 만들기 위해 필수다.
3. 5개 상태값은 항상 0으로 유지하는 값이 아니라 task phase에 따라 최적 목표가 달라지는 planning-relevant variables다.
4. Task A/B/C/D는 각각 서로 다른 factor family를 자극한다.
5. invisible noise field는 만능 교란이 아니라 sparse coupling + family-limited randomness로 설계되어야 한다.
6. big shift뿐 아니라 small cumulative drift가 있어야 제안법의 강점이 드러난다.
7. baseline도 쉬운 케이스는 풀 수 있어야 하고, hard case에서 제안법의 우위가 드러나야 한다.
8. success rate만이 아니라 WHPT, action flip precision, compute frontier, counterfactual fidelity, explanation faithfulness까지 함께 봐야 mechanism paper가 된다.

최종적으로 이 Part 3은 Part 1과 Part 2를 실험적으로 닫는다.

- Part 1은 문제를 **wrong dynamics hypothesis persistence**로 정의했다.
- Part 2는 해결책을 **falsification + action relevance + compute reallocation**으로 설명했다.
- Part 3은 그 주장이 실제로 검증되도록 **RG-4F 환경, task, OOD, baseline, ablation, metric**을 설계했다.

따라서 최종 STEP 3의 전체 메시지는 다음 한 문장으로 닫힌다.

> 이 논문은 더 많이 planning하는 world model이 아니라, 부분관측과 잠재 regime 변화 속에서 현재 가설이 틀렸음을 감지하고, 그 차이가 행동을 바꿀 때만 대안 규칙 아래의 rollout로 계산을 재배치하는 world-model planning framework이며, RG-4F는 그 메커니즘을 성공률·계산량·가설 지속시간·행동 전환·반사실 rollout 충실도까지 분해해 검증하기 위한 환경이다.
>