# Falsification, Action Relevance, Compute Reallocation & Control Logic

Part 2의 핵심은 하나다. **이 알고리즘은 “규칙 변화를 감지했다”에서 멈추지 않는다.** 현재 규칙 가설이 틀렸을 가능성을 계산하고, 그 대안 가설이 실제 행동을 바꿀 만큼 중요한지 확인한 뒤, 그때만 current-regime rollout에서 alternative-regime rollout으로 계산을 옮긴다. 기존 STEP 3 원문도 단순 prediction error threshold가 아니라 current regime hypothesis와 alternative hypothesis 사이의 likelihood ratio 및 action relevance를 사용해야 한다고 정리했고, 추가 계산은 “낯설다”가 아니라 “다른 규칙이 더 맞으며 그 차이가 실제 행동을 바꾼다”는 조건에서만 투입되어야 한다고 잡고 있다.

감사 결과에서 확정된 수정 방향은 더 명확하다. 기존 표현인 “planning compute를 더 배분”은 부족하고, 최종 표현은 **대안 가설 하의 rollout으로 전환하고 그 가설 쪽에 계산을 선택적으로 집중한다**가 되어야 한다. 또한 control-drift는 연속 회전이 아니라 4방향 grid에 맞는 **이산 remap + 약한 miscontrol**로 정의되어야 하며, mobility는 latency/cooldown 축으로 분리되어야 한다.

---

# 3.7 Falsification Score

## 3.7.1 직관적 해설: falsification은 “이상하다”가 아니라 “현재 가설보다 대안 가설이 더 잘 설명한다”이다

falsification score는 단순히 “예측이 틀렸다”는 점수가 아니다. 이 차이가 매우 중요하다. 예측이 틀렸다는 사실만으로는 agent가 무엇을 해야 하는지 알 수 없다. 예측이 틀린 이유는 너무 많다.

예를 들어 agent가 `W`를 눌렀는데 예상보다 한 tick 늦게 위로 이동했다고 하자. 이 결과는 여러 방식으로 설명될 수 있다.

첫째, mobility가 낮아져서 이동 cooldown이 늘어났을 수 있다.
둘째, 무거운 조각을 들고 있어서 일시적으로 이동이 느려졌을 수 있다.
셋째, friction field에 들어가 mobility dynamics가 바뀌었을 수 있다.
넷째, control-drift 때문에 실제 입력 해석이 바뀌었을 수 있다.
다섯째, agent가 자기 위치를 잘못 belief update했을 수 있다.

raw prediction error는 이 모든 경우를 한 바구니에 넣고 “틀렸다”고 말한다. 하지만 논문에서 필요한 것은 “틀렸다”가 아니라 “어떤 설명이 더 맞는가”다. 그래서 falsification은 반드시 current hypothesis와 alternative hypothesis 사이의 비교여야 한다.

쉬운 비유로 말하면, 운전 중 차가 예상과 다르게 움직였다고 하자. 그냥 “차가 이상하다”고 말하는 것은 mismatch다. 하지만 “브레이크가 밀리는 문제인지, 핸들 입력이 반대로 먹는 문제인지, 길이 미끄러운 문제인지”를 비교하는 것은 hypothesis testing이다. 본 논문은 두 번째를 한다.

따라서 falsification score의 의미는 다음이다.

> 최근 observation-action evidence가 current dynamics hypothesis보다 alternative dynamics hypothesis를 더 잘 지지하는 정도.
> 

이때 중요한 것은 “최근 관측”만 보는 것이 아니라 “최근 행동과 그 결과”를 함께 본다는 점이다. regime는 단순 이미지 패턴이 아니라 action-to-transition rule이기 때문이다. agent가 어떤 행동을 했고, 그 행동이 어떤 결과를 냈는지를 봐야 현재 규칙이 맞는지 틀렸는지 판단할 수 있다.

---

## 3.7.2 학술적 서술: raw mismatch가 아니라 likelihood-ratio 기반 가설 반증

시점 `t`에서 agent는 현재 가장 가능성 높은 regime hypothesis를 가진다.

$\displaystyle r_t^{cur} = \arg\max_r q_t(r)$

동시에 current hypothesis를 제외한 대안 후보 중 최근 observation-action window를 가장 잘 설명하는 alternative hypothesis를 둔다.

$\displaystyle r_t^{alt}=\arg\max_{r\neq r_t^{cur}} p_\theta(o_{t-w+1:t},e_{t-w+1:t}\mid r,\hat{s}_{t-w:t})$

여기서 `w`는 최근 evidence window의 길이다. 이 window는 단일 관측 하나만 보지 않도록 만든다. 단일 관측은 우연한 noise나 일시적 collision 때문에 흔들릴 수 있다. 반면 짧은 window는 “이 오차가 일회성인지, 어떤 규칙 아래에서 반복적으로 더 잘 설명되는지”를 보게 한다.

falsification의 기본항은 likelihood ratio 또는 Bayes factor 스타일로 정의한다.

$B_t=\log p_\theta(o_{t-w+1:t},e_{t-w+1:t}\mid r_t^{alt},\hat{s}{t-w:t})-\log p_\theta(o_{t-w+1:t},e_{t-w+1:t}\mid r_t^{cur},\hat{s}_{t-w:t})$

이 식은 직관적으로 매우 단순하다.

- `B_t > 0`이면 최근 evidence는 current regime보다 alternative regime에서 더 잘 설명된다.
- `B_t < 0`이면 current regime를 유지해도 된다.
- `B_t`가 매우 크면 current hypothesis가 강하게 반증되고 있다는 뜻이다.

하지만 `B_t`만으로는 부족하다. 왜냐하면 likelihood ratio는 단기 window의 우연한 변화에도 민감할 수 있기 때문이다. 따라서 change-point posterior를 함께 넣는다.

$C_t=q_\phi(c_t=1\mid h_{t-1},o_t,e_t)$

최종 falsification signal은 다음과 같이 둔다.

$F_t^*=B_t+\lambda_{cp}\log\frac{C_t}{1-C_t+\epsilon}$

이 식에서 `B_t`는 “대안 가설이 현재 가설보다 최근 evidence를 더 잘 설명하는가”를 나타낸다. `C_t`는 “지금이 실제 규칙 전환 시점일 가능성이 있는가”를 나타낸다. 두 항을 결합하면 단순 예측오차보다 훨씬 강한 신호가 된다.

---

## 3.7.3 posterior shift만 보면 왜 순환논리가 되는가?

regime posterior가 바뀌었다는 사실만으로 falsification을 정의하면 위험하다. 예를 들어 모델이 어떤 이유로 `q_t(r)`를 바꿨다고 하자. 그 다음 “posterior가 바뀌었으니 regime shift가 있었다”고 말하면 순환논리가 된다.

즉 다음 논리는 위험하다.

> 모델이 regime posterior를 바꿨다.
그러므로 regime가 바뀌었다.
그러므로 모델이 잘 감지했다.
> 

이건 검증이 아니다. 모델 내부 belief 변화 자체를 근거로 다시 모델이 맞았다고 말하는 구조다.

그래서 falsification은 posterior shift 하나로 정의하면 안 된다. 반드시 외부 evidence likelihood와 연결되어야 한다. 즉 “posterior가 바뀌었다”가 아니라, “최근 observation-action sequence가 current hypothesis보다 alternative hypothesis에서 더 높은 likelihood를 갖는다”가 되어야 한다.

또한 reveal-vs-shift 비교도 같이 필요하다.

$\Gamma_t=\log p_\theta(o_t\mid \mathcal{H}_{shift},h_{t-1})-\log p_\theta(o_t\mid \mathcal{H}_{reveal},h_{t-1})$

여기서 `Γ_t`는 현재 변화가 단순히 숨은 상태가 드러난 것인지, 아니면 규칙 자체가 바뀐 것인지 구분하는 진단 변수다. `B_t`가 alternative regime를 지지하더라도 `Γ_t`가 낮으면, 그 변화는 regime shift라기보다 state reveal일 수 있다. 따라서 최종 알고리즘에서는 `F_t^*`를 planning reallocation의 핵심 신호로 쓰되, `Γ_t`를 진단 및 auxiliary calibration metric으로 함께 보고한다.

---

## 3.7.4 “규칙이 다르다”와 “규칙을 바꿀 가치가 있다”는 다르다

falsification score가 높다는 것은 current hypothesis가 의심스럽다는 뜻이다. 그러나 그것만으로 planning을 많이 하거나 대안 가설로 전환하면 안 된다. 왜냐하면 어떤 규칙 차이는 행동에 거의 영향을 주지 않기 때문이다.

예를 들어 agent가 넓은 복도에서 목표 방향으로 직진만 하면 되는 상황이라고 하자. 이때 mobility가 조금 느려졌거나 noise가 약간 증가했더라도 최선 행동은 여전히 `W`일 수 있다. 이 경우 current hypothesis가 완벽하지 않더라도 대안 regime rollout을 많이 돌릴 필요가 없다. 그냥 직진하면 된다.

반대로 문 앞에서 상호작용해야 하는 상황을 보자. current hypothesis에서는 지금 바로 `E`를 누르면 문이 열린다고 예측하지만, alternative hypothesis에서는 interaction intensity가 target band에서 벗어나 있어 `i^-`를 두 번 조절한 뒤 `E`를 눌러야 한다고 예측한다. 이 경우 regime 차이는 행동을 바꾼다. 여기서는 planning reallocation이 중요하다.

따라서 본 논문의 핵심 조건은 두 개다.

1. current hypothesis가 반증되는가?
2. 그 반증이 실제 행동 선택을 바꾸는가?

첫 번째가 falsification이고, 두 번째가 action relevance다.

---

# 3.8 Action Relevance

## 3.8.1 직관적 해설: 행동이 안 바뀌면 깊게 생각할 이유가 없다

action relevance는 이 논문을 novelty detector나 uncertainty gate와 구분하는 핵심 장치다. 규칙이 달라 보인다고 해서 항상 planning을 켜면 안 된다. 낯선 상황이지만 최선 행동이 그대로라면 compute를 쓸 필요가 작다.

쉬운 예시를 들어보자.

agent가 긴 복도 중앙에 있고 목표는 북쪽 끝에 있다. current hypothesis에서는 `W`를 누르면 위로 이동한다. alternative hypothesis에서는 mobility가 조금 낮아서 `W`를 눌러도 한 tick 늦게 이동한다. 이 두 가설은 다르다. 그러나 최선 행동은 둘 다 `W`다. 이 경우 추가 rollout은 큰 이득이 없다. agent는 그냥 계속 `W`를 누르면 된다.

반대로 agent가 문 앞에 있다. 문을 열려면 mobility가 `[-0.02, 0.02]`에 있어야 하고, interaction intensity도 target band 안에 있어야 한다. current hypothesis에서는 조건을 만족한다고 믿는다. alternative hypothesis에서는 invisible field 때문에 mobility correction latency가 생겨 아직 target band에 들어오지 않았다고 예측한다. 이 경우 current hypothesis 아래 최선 행동은 `E`이고, alternative hypothesis 아래 최선 행동은 `m^-` 또는 wait일 수 있다. 이때는 행동이 갈린다. 이 순간이 바로 action relevance가 높은 순간이다.

즉 action relevance는 “규칙 차이가 행동 차이로 번역되는가”를 묻는다.

---

## 3.8.2 단순 policy distance가 약한 이유

action relevance를 policy distribution distance로 정의할 수도 있다. 예를 들어 current regime policy와 alternative regime policy의 KL divergence를 볼 수 있다. 하지만 이 방식은 약하다.

첫째, policy distribution은 temperature나 entropy regularization에 민감하다. 모델이 원래 여러 행동에 확률을 조금씩 나눠주는 정책이면, 실제 최선 행동은 같아도 policy distance가 커질 수 있다.

둘째, policy distance는 value magnitude를 반영하지 못한다. 두 regime에서 action distribution이 다르더라도 value 차이가 작으면 실제로는 중요하지 않을 수 있다.

셋째, policy distance는 “행동이 바뀌면 얼마나 중요한가”를 직접 말해주지 않는다. 예를 들어 current hypothesis에서 `W`가 0.51, `D`가 0.49이고 alternative에서 `D`가 0.51, `W`가 0.49라면 argmax는 바뀌지만 가치 차이는 거의 없을 수 있다. 반대로 policy는 비슷해 보여도 특정 critical action의 value가 크게 달라질 수 있다.

그래서 본 논문에서는 value gap 또는 action flip 기반 relevance가 더 적절하다.

---

## 3.8.3 value gap 기반 action relevance

가장 기본적인 action relevance는 current regime와 alternative regime 아래의 best value 차이로 정의한다.

$\displaystyle \Delta_t=\left[\max_a Q(\hat{s}_t,r_t^{alt},a)-\max_a Q(\hat{s}_t,r_t^{cur},a)\right]_+$

이 식은 alternative regime를 믿고 행동했을 때 얻을 수 있는 최고 가치가 current regime 아래 최고 가치보다 얼마나 큰지를 본다. `Δ_t`가 크면 alternative hypothesis가 단순히 그럴듯할 뿐 아니라 행동적으로도 유리하다는 뜻이다.

하지만 이 정의만으로는 부족할 수 있다. 왜냐하면 두 regime에서 최고 가치의 행동이 같을 수도 있기 때문이다. 따라서 action flip을 별도로 볼 수 있다.

$\displaystyle a_t^{cur}=\arg\max_a Q(\hat{s}_t,r_t^{cur},a)$

$\displaystyle a_t^{alt}=\arg\max_a Q(\hat{s}_t,r_t^{alt},a)$

$\Delta_t^{flip}=\mathbf{1}[a_t^{cur}\neq a_t^{alt}]\cdot\left|Q(\hat{s}_t,r_t^{alt},a_t^{alt})-Q(\hat{s}_t,r_t^{cur},a_t^{cur})\right|$

`Δ_t^{flip}`는 단순히 value 차이를 보는 것이 아니라, 실제 argmax action이 바뀌는지까지 반영한다. 이게 본 논문에 특히 중요하다. 왜냐하면 주장하고 싶은 것은 “regime를 잘 맞혔다”가 아니라 “regime 차이가 행동 선택을 바꿨고, 그 행동 변경이 성능을 개선했다”이기 때문이다.

---

## 3.8.4 직관적 예시: control-drift와 action relevance

control-drift가 있는 상황을 보자. current hypothesis는 identity control이다.

- `W → up`
- `A → left`
- `S → down`
- `D → right`

alternative hypothesis는 clockwise remap이다.

- `W → right`
- `D → down`
- `S → left`
- `A → up`

agent가 열린 공간 한가운데 있고 목표가 오른쪽에 있다면, current hypothesis에서는 `D`가 최선이다. alternative hypothesis에서는 `W`가 최선이다. 행동이 완전히 달라진다. 이 경우 action relevance는 높다.

반면 agent가 벽에 막힌 방 안에서 당장 interaction만 해야 하는 상황이라면, control remap이 조금 의심되어도 최선 행동은 `E`일 수 있다. 이 경우 control-drift falsification이 높아도 action relevance는 낮다. 지금 당장 이동하지 않기 때문이다.

이 차이가 중요하다. 본 논문은 “regime 변화 감지기”가 아니라 “regime 변화가 행동을 바꿀 때만 planning을 재배치하는 planner”다.

---

# 3.9 Compute Allocation vs Compute Reallocation

## 3.9.1 기존 표현 “더 배분한다”가 부족한 이유

“planning compute를 더 배분한다”는 표현은 반쯤 맞고 반쯤 부족하다. 맞는 이유는 실제로 horizon이나 rollout 수가 늘어날 수 있기 때문이다. 부족한 이유는 이 표현만으로는 논문 novelty가 adaptive planning으로 축소되기 때문이다.

adaptive planning은 보통 다음 질문을 묻는다.

> 지금 더 오래 볼까?
rollout 수를 늘릴까?
horizon을 키울까?
> 

본 논문은 다른 질문을 묻는다.

> 지금 current hypothesis 아래에서 계속 볼까?
아니면 alternative hypothesis 아래에서 다시 볼까?
current rollout에 쓰던 계산을 alternative rollout으로 옮길까?
> 

즉 핵심은 compute amount가 아니라 compute target이다. 그래서 최종 표현은 compute allocation보다 compute reallocation이 더 정확하다.

---

## 3.9.2 current-hypothesis rollout과 alternative-hypothesis rollout의 차이

world model rollout은 항상 어떤 dynamics hypothesis 아래에서 이루어진다. 겉으로는 같은 action sequence를 rollout하더라도, regime가 다르면 결과는 달라진다.

예를 들어 action sequence가 다음과 같다고 하자.

$(a_t,a_{t+1},a_{t+2})=(W,W,E)$

current regime가 identity control이면 rollout은 위로 두 칸 이동한 뒤 interaction하는 trajectory가 된다. 하지만 alternative regime가 `W → D` remap이면 같은 action sequence는 오른쪽으로 두 칸 이동한 뒤 interaction하는 trajectory가 된다. 겉으로는 같은 action sequence지만 미래 상태는 완전히 다르다.

따라서 planning reallocation은 “같은 미래를 더 많이 상상한다”가 아니다. 이것은 “다른 세계 규칙 아래에서 미래를 다시 상상한다”다.

이 차이가 논문 중심이다.

---

## 3.9.3 active hypothesis pool, horizon, rollout count의 구분

compute reallocation을 정확히 쓰려면 세 개념을 분리해야 한다.

첫째, **active hypothesis pool**이다. 이는 현재 비교할 regime 후보 집합이다.

$\mathcal{R}_t^{active}=\operatorname{TopK}(q_t(r),K=2)$

일반적으로 current hypothesis와 strongest alternative만 비교한다. 모든 regime 조합을 다 rollout하면 계산량이 폭발하기 때문이다. 이 active pool은 “어떤 가설들을 비교할 것인가”를 결정한다.

둘째, **horizon**이다. 이는 각 hypothesis 아래에서 얼마나 멀리 rollout할 것인지를 결정한다.

$h_t=h_{min}+\left\lfloor u_t(h_{max}-h_{min})\right\rfloor$

horizon은 “얼마나 멀리 볼 것인가”다.

셋째, **rollout count**다. 이는 각 hypothesis 아래에서 몇 개 trajectory 후보를 평가할 것인지를 결정한다.

$k_t=k_{min}+\left\lfloor u_t(k_{max}-k_{min})\right\rfloor$

rollout count는 “몇 개 선택지를 비교할 것인가”다.

이 세 개를 섞으면 안 된다. 본 논문의 핵심은 active hypothesis pool을 통해 current와 alternative를 비교하고, falsification과 action relevance에 따라 horizon과 rollout count를 조절하되, 특히 alternative hypothesis 쪽에 rollout weight를 재배치하는 것이다.

---

## 3.9.4 compute reallocation value

최종 compute value는 다음 형태로 둘 수 있다.

$V_t^{realloc}=\max(0,F_t^*-\tau_F)\cdot\max(0,\Delta_t-\tau_\Delta)-\lambda_C C_t^{plan}$

여기서 각 항의 의미는 다음과 같다.

- `F_t^*`: current hypothesis가 반증되는 정도
- `Δ_t`: alternative hypothesis가 행동적으로 중요한 정도
- `τ_F`: falsification threshold
- `τ_Δ`: action relevance threshold
- `C_t^{plan}`: 추가 planning cost
- `λ_C`: compute cost penalty weight

이 식의 구조가 중요한 이유는 곱셈 구조 때문이다. falsification만 높아도 planning하지 않는다. action relevance만 높아도 planning하지 않는다. 둘이 동시에 높아야 reallocation value가 커진다.

즉 다음 네 경우가 생긴다.

1. `F_t^*` 낮고 `Δ_t` 낮음
→ current hypothesis 유지, greedy 또는 shallow rollout
2. `F_t^*` 높고 `Δ_t` 낮음
→ 규칙은 의심되지만 행동은 안 바뀜, planning 억제
3. `F_t^*` 낮고 `Δ_t` 높음
→ 대안이 행동적으로는 중요할 수 있지만 evidence가 부족함, 제한적 탐색 또는 soft allocation
4. `F_t^*` 높고 `Δ_t` 높음
→ current hypothesis 반증 + 행동 변화 가능성 큼, alternative rollout으로 compute reallocation

이 구조 때문에 논문은 단순 risk gate가 아니다. risk gate는 위험하면 planning한다. 이 알고리즘은 위험해도 행동이 안 바뀌면 planning을 줄이고, 겉보기 위험이 작아도 행동이 갈리면 planning한다.

---

# 3.10 Control-Drift Final Definition

## 3.10.1 기존 연속 각도 drift 설명은 버려야 한다

초기 STEP 3에서는 control-drift가 연속적인 방향 회전처럼 설명될 수 있었다. 예를 들어 `d_t` 값에 따라 90도 회전, 좌우 반전, 상하 반전 같은 binning rule을 언급했다. 방향성은 맞지만, 최종 개정판에서는 “연속 각도 drift” 뉘앙스를 버려야 한다.

이유는 단순하다. 환경이 4방향 grid이기 때문이다. 4방향 grid에서 `13도 회전`, `27도 회전` 같은 연속 각도 개념은 실제 action semantics와 잘 맞지 않는다. agent의 이동 action은 `W/A/S/D` 네 개다. 따라서 control-drift는 연속적인 물리 회전이 아니라, discrete action remap 또는 stochastic miscontrol로 정의하는 것이 맞다.

최종적으로 버려야 하는 설명은 다음이다.

> control-drift는 연속적인 방향 회전 정도를 나타낸다.
> 

대체해야 하는 설명은 다음이다.

> control-drift는 4방향 grid에서 입력 action이 실제 movement outcome으로 해석되는 mapping이 이산적으로 바뀌거나, 일정 확률로 잘못된 방향으로 실행되는 action-semantics regime이다.
> 

---

## 3.10.2 mobility와 control-drift의 분리

이 분리는 반드시 명확해야 한다. 두 개가 겹치면 논문이 약해진다.

mobility는 이동 효율이다. 같은 방향으로 가긴 가는데 느려진다. 예를 들어 `W`를 누르면 여전히 위로 간다. 다만 이동 cooldown이 늘어나 한 칸 이동하는 데 2 tick이 걸릴 수 있다.

control-drift는 입력 해석 규칙이다. `W`를 눌렀는데 위로 가지 않고 오른쪽으로 갈 수 있다. 또는 `A`를 눌렀는데 위로 갈 수 있다. 또는 일정 확률로 의도와 다른 방향으로 미끄러질 수 있다.

비유하면 mobility는 “다리가 무거워져서 느리게 걷는 것”이다. control-drift는 “오른쪽으로 가려고 했는데 몸이 왼쪽으로 움직이는 것”이다. 전자는 속도 문제고, 후자는 조작 규칙 문제다.

수식적으로 mobility는 cooldown에 들어간다.

$\displaystyle \text{move\_cd}(m_t) = \max \left( 1, \left\lceil \frac{\kappa_m}{1 + \alpha_m m_t} \right\rceil \right)$

반면 control-drift는 action remapping function에 들어간다.

$\tilde{a}t=\Pi{r_t^{ctrl}}(a_t)$

여기서 `Π`는 현재 control regime가 정의하는 action remap이다. 예를 들어 identity regime에서는 다음과 같다.

$\Pi_{identity}(W)=W,\Pi_{identity}(A)=A,\Pi_{identity}(S)=S,\Pi_{identity}(D)=D$

clockwise regime에서는 다음처럼 둘 수 있다.

$\Pi_{cw}(W)=D,\Pi_{cw}(D)=S,\Pi_{cw}(S)=A,\Pi_{cw}(A)=W$

좌우 반전 regime는 다음처럼 둔다.

$\Pi_{lr}(A)=D,\Pi_{lr}(D)=A,\Pi_{lr}(W)=W,\Pi_{lr}(S)=S$

확률적 miscontrol은 다음처럼 정의할 수 있다.

$\displaystyle \tilde{a}_t = \begin{cases} \Pi_{r_t^{ctrl}}(a_t), & \text{with probability } 1 - p_{slip} \\ a' \sim \text{NeighborActions}(a_t), & \text{with probability } p_{slip} \end{cases}$

이렇게 하면 mobility와 control-drift가 완전히 분리된다.

- mobility: 원하는 방향으로 가되, 느려진다.
- control-drift: 원하는 방향 자체가 다르게 해석된다.

---

## 3.10.3 구현 방식 비교

control-drift는 세 가지 방식으로 구현할 수 있다.

첫째, **이산 remap**이다. 가장 명확하다. `W → D`, `A → W`처럼 action mapping이 바뀐다. 이 방식은 regime hypothesis comparison에 가장 적합하다. current hypothesis와 alternative hypothesis의 rollout 결과가 명확히 달라지기 때문이다.

둘째, **확률적 miscontrol**이다. 기본 mapping은 유지되지만 일정 확률로 옆 방향으로 미끄러진다. 이 방식은 subtle drift를 만들기 좋다. 변화가 너무 명확하지 않기 때문에 baseline detector가 바로 잡기 어렵다.

셋째, **주기적 slip**이다. 예를 들어 4칸마다 한 번씩 입력이 시계방향으로 틀어진다. 이 방식은 adaptation vs correction 문제를 만들기 좋다. 매번 원상복구하려고 correction하는 것보다, 패턴을 학습해서 적응하는 것이 더 이득일 수 있다.

최종 논문에서는 세 방식을 모두 메인 환경에 다 넣기보다, main setting에서는 이산 remap과 약한 miscontrol을 쓰고, periodic slip은 adaptation/correction hard case로 두는 것이 좋다.

---

# 3.11 Adaptation vs Correction

## 3.11.1 drift가 생겼다고 무조건 correction이 답은 아니다

drift가 생기면 직관적으로는 “원래 상태로 돌려야 한다”고 생각하기 쉽다. 하지만 sequential decision problem에서는 항상 그렇지 않다. correction에는 비용이 든다. 특히 이 환경은 tick-based이므로 상태 조절 action도 시간을 쓴다. 따라서 drift를 교정하는 데 쓰는 tick이 목표 달성에 쓰는 tick보다 더 비쌀 수 있다.

예를 들어 control-drift가 약간 생겼지만 앞으로 두 칸만 이동하면 방을 완료할 수 있다고 하자. 이때 drift를 완전히 0으로 되돌리기 위해 `d^-` action을 여러 번 쓰는 것은 낭비일 수 있다. 차라리 remap을 감안해 다른 입력을 누르는 것이 빠르다. 이것이 adaptation이다.

반대로 앞으로 긴 복도를 지나가야 하고, control-drift가 계속 누적되어 잘못된 이동을 만들 가능성이 크다면 correction이 낫다. 지금 몇 tick을 써서 drift를 안정화하면 이후 수십 tick의 이동 오류를 줄일 수 있다.

즉 핵심 질문은 다음이다.

> 지금 drift를 원래대로 돌리는 것이 더 싼가, 아니면 바뀐 drift를 감안해 행동하는 것이 더 싼가?
> 

이 질문이 바로 adaptation vs correction이다.

---

## 3.11.2 correction이 유리한 경우

correction은 다음 상황에서 유리하다.

첫째, drift가 크고 오래 지속된다.
한 번 크게 바뀐 뒤 계속 유지되는 control remap이나 field mean shift라면, 매 행동마다 적응하는 것보다 원인을 교정하는 것이 낫다.

둘째, 남은 horizon이 길다.
앞으로 해야 할 행동이 많을수록 현재 drift가 누적 비용을 만든다. 이때 correction cost는 초기 투자처럼 작동한다.

셋째, 최종 정밀 interaction 직전이다.
문, altar, stele 같은 interaction target은 target band를 요구할 수 있다. 이 순간에는 조금만 벗어나도 실패 interaction, latency 증가, reset으로 이어질 수 있다. 따라서 마지막 interaction 전에는 adaptation보다 correction이 유리할 수 있다.

넷째, drift가 다른 오차를 연쇄적으로 키운다.
예를 들어 control-drift 때문에 잘못된 tile을 밟고, 그 tile이 interaction intensity와 noise를 다시 흔든다면 drift는 단일 비용이 아니라 연쇄 비용을 만든다. 이 경우 correction이 더 중요해진다.

---

## 3.11.3 adaptation이 유리한 경우

adaptation은 다음 상황에서 유리하다.

첫째, drift가 짧은 구간에서만 발생한다.
예를 들어 특정 local hazard zone 안에서만 `W → D` remap이 발생하고, 두 칸만 지나면 정상으로 돌아온다면 굳이 correction할 필요가 없다.

둘째, drift가 주기적이고 예측 가능하다.
예를 들어 4칸마다 한 번씩 slip이 발생한다면, agent는 correction보다 타이밍을 맞춰 우회하거나 입력을 바꾸는 방식으로 적응할 수 있다.

셋째, correction action의 tick cost가 크다.
상태값을 조절하는 action이 tick을 많이 쓰면, correction 자체가 목표 달성을 늦춘다.

넷째, 현재 task가 drift에 민감하지 않다.
예를 들어 지금은 이동이 아니라 interaction만 하면 되는 상황이라면 control-drift를 당장 교정할 필요가 없을 수 있다.

---

## 3.11.4 정밀 상호작용 직전의 예외

정밀 interaction 직전은 특별하다. 일반적으로는 adaptation이 싼 경우가 많아도, 최종 interaction 직전에는 correction이 유리해질 수 있다.

예를 들어 D task에서 최종 altar 성공 조건이 다음과 같다고 하자.

$i_t\in[\tau_i-\alpha_i,\tau_i+\alpha_i]$

agent가 target band 근처에 있지만 invisible interaction interference 때문에 `i_t`가 조금씩 drift하고 있다. 이때 그냥 적응해서 `E`를 누르면 실패할 수 있다. 실패 interaction이 3회 누적되면 중앙홀로 강제복귀하는 구조라면, 한 번의 실패 비용이 매우 크다. 따라서 이 순간에는 `i^+` 또는 `i^-`로 정확히 band 안에 넣고 `E`를 누르는 correction이 더 유리하다.

이 구조는 논문에 중요하다. 왜냐하면 adaptation과 correction이 단순 선호 문제가 아니라, state, regime, task phase, remaining horizon, failure cost에 따라 달라지는 planning 문제임을 보여주기 때문이다.

---

## 3.11.5 세 가지 drift scenario

### 장기 drift형

장기 drift형에서는 correction이 유리해야 한다. 예를 들어 C 방에 들어간 뒤 control mapping이 `identity`에서 `cw`로 바뀌고 방을 완료할 때까지 유지된다. agent가 이 remap을 무시하면 모든 이동이 꼬인다. 이 경우 alternative hypothesis가 맞다면 correction 또는 remap-aware planning을 해야 한다.

### 주기 drift형

주기 drift형에서는 adaptation이 유리해야 한다. 예를 들어 4 tick마다 한 번씩 miscontrol이 발생한다. 이 경우 매번 `d`를 0으로 돌리는 것보다, slip timing을 고려해 한 tick 기다리거나 우회하는 것이 더 싸다.

### 최종 precision endpoint형

최종 precision endpoint에서는 마지막에만 correction이 유리하다. 이동 중에는 drift에 적응하다가, altar 앞에서는 interaction intensity나 mobility를 target band에 맞춰야 한다. 이 경우 planner는 “계속 적응”도 아니고 “항상 correction”도 아닌 phase-dependent strategy를 선택해야 한다.

이 세 가지 scenario가 있어야 본 논문의 핵심 메시지가 살아난다.

> 대안 규칙이 더 맞아 보이는 것만으로는 부족하고, 그 대안 규칙 아래에서 adaptation, correction, wait, detour 중 어떤 행동이 비용상 더 나은지를 비교해야 한다.
> 

---

# 3.12 Reward, Penalty, and Cost Linkage

## 3.12.1 상태값 자체에 벌점을 주면 안 된다

초기 설계에서 가장 조심해야 할 부분은 상태값 자체를 reward/punishment의 직접 대상으로 삼는 것이다. 예를 들어 다음과 같은 설계는 위험하다.

- `vision`이 낮으면 벌점
- `mobility`가 0에서 멀어지면 벌점
- `interaction`이 0에서 멀어지면 벌점
- `noise`가 증가하면 벌점
- `control-drift`가 0이 아니면 벌점

이렇게 하면 agent는 task를 해결하는 것이 아니라 상태값을 예쁘게 유지하는 데 집착할 수 있다. 특히 이 환경에서는 어떤 상태값 변화가 beneficial할 수도 있다. 어떤 task에서는 mobility가 높을수록 빨리 이동해서 유리하고, 어떤 task에서는 mobility를 0 근처에 맞춰야 문이 열린다. 어떤 interaction은 빠를수록 좋지만, 어떤 altar는 target band를 정확히 맞춰야 한다.

따라서 상태값 자체에 벌점을 주면 안 된다. 벌점은 상태값이 목표 달성에 만들어낸 실제 비용에 붙어야 한다.

---

## 3.12.2 각 상태값과 목표 달성 비용의 연결

### vision

vision은 정보 획득 비용과 연결된다. vision이 낮으면 local cue를 늦게 발견하고, 잘못된 room object를 선택할 수 있다. 하지만 vision이 낮다는 사실 자체가 벌점은 아니다. 벌점은 필요한 정보를 늦게 확인해서 step이 늘어나거나, wrong stele을 켜서 failure cost가 생길 때 발생한다.

### mobility

mobility는 latency와 연결된다. mobility가 낮으면 이동 cooldown이 늘어나고 episode length가 증가한다. 하지만 어떤 local gate에서는 mobility를 0 근처에 맞춰야 한다. 따라서 mobility가 높거나 낮다는 사실 자체가 reward/punishment가 아니라, 목표 셀 도달 시간, gate 통과 조건, interaction timing에 미치는 비용으로 반영되어야 한다.

### interaction

interaction은 success/failure 및 latency와 연결된다. target band와 mismatch가 크면 interaction_ticks가 늘거나 실패 interaction이 발생한다. 따라서 interaction penalty는 `|i_t - τ|` 자체가 아니라, 그 mismatch로 인해 발생한 latency, failure count, reset risk로 연결해야 한다.

### noise

noise는 직접 벌점이 아니라 uncertainty와 disturbance cost의 원인이다. noise가 높으면 관측이 흔들리거나 다른 상태값과 sparse coupling되어 vision, mobility, interaction, control-drift를 간접적으로 흔든다. 하지만 noise 자체를 무조건 줄이는 목표로 두면 agent가 task보다 noise minimization에 집착할 수 있다. noise는 auxiliary diagnostic과 transition difficulty로 쓰는 것이 좋다.

### control-drift

control-drift는 wrong movement cost와 연결된다. remap을 잘못 추정하면 의도와 다른 tile로 이동하고, hazard를 밟고, target cell을 지나치고, reset risk가 커진다. 따라서 control-drift penalty는 `d_t` 값 자체가 아니라 wrong movement, detour, collision, recovery step, failure interaction으로 계산되어야 한다.

---

## 3.12.3 reward/cost decomposition

최종 reward는 task reward와 cost 항으로 분해한다.

$R_t=R_t^{task}-\lambda_{step}C_t^{step}-\lambda_{fail}C_t^{fail}-\lambda_{reset}C_t^{reset}-\lambda_{plan}C_t^{plan}-\lambda_{latency}C_t^{latency}$

각 항의 의미는 다음과 같다.

- `R_t^{task}`: room task 완료, 전체 task 완료, subgoal 진행도
- `C_t^{step}`: 매 tick마다 드는 기본 시간 비용
- `C_t^{fail}`: 실패 interaction, 잘못된 object 선택
- `C_t^{reset}`: 중앙홀 강제복귀, room progress 초기화
- `C_t^{plan}`: planning call, rollout step, wall-clock compute
- `C_t^{latency}`: 이동 cooldown, interaction latency
- `λ`: 각 비용의 가중치

여기서 중요한 것은 `C_t^{plan}`이 reward에 들어간다는 점이다. 이 논문은 compute frontier를 주장하기 때문에 planning을 무한정 많이 쓰면 안 된다. always-plan baseline이 성능은 높을 수 있지만 compute-normalized return에서 손해를 보게 만들어야 한다.

---

## 3.12.4 discomfort latent의 위치

discomfort latent 또는 공통 불편값 latent vector는 유용할 수 있다. 하지만 main reward가 되면 안 된다.

예를 들어 agent가 현재 상태를 “불편하다”고 느끼는 latent를 학습한다고 하자. 이 latent는 다음 진단에 좋다.

- 현재 상태가 목표 달성에 불리한가?
- 여러 상태값 변화가 누적 비용을 만들고 있는가?
- agent가 correction을 고려해야 하는가?
- hidden field가 어떤 불편 패턴을 만드는가?

하지만 이것을 main objective로 두면 agent는 task를 해결하는 대신 discomfort를 줄이는 행동만 할 수 있다. 예를 들어 방을 완료하려면 잠깐 noise field를 통과해야 하는데, discomfort penalty가 너무 크면 agent는 목표를 포기하고 안전한 곳에 머물 수 있다.

따라서 discomfort latent는 다음 위치가 적절하다.

$z_t^{disc}=f_\psi(\hat{s}_t,\hat{r}_t,o_t)$

$\mathcal{L}_{disc}=\ell(z_t^{disc},C_t^{future})$

여기서 `C_t^{future}`는 미래 누적 비용의 auxiliary target이다. 즉 discomfort latent는 미래 비용 예측용 보조 변수이지, 메인 보상 자체가 아니다.

---

# 3.13 Planning Collapse Prevention

## 3.13.1 왜 collapse 위험이 생기는가?

`falsification × action relevance` 구조는 매우 강력하지만, 너무 보수적으로 학습되면 planning을 거의 안 쓰는 방향으로 collapse할 수 있다. 이유는 세 가지다.

첫째, planning cost가 reward에 들어가면 agent는 planning을 아끼는 것이 당장 유리해 보일 수 있다.
둘째, 초기 학습 단계에서는 world model이 부정확해서 alternative rollout의 value가 불안정하다. 그러면 `Δ_t`가 낮게 추정되고 planning이 꺼진다.
셋째, planning을 덜 하면 alternative hypothesis를 검증할 기회도 줄어든다. 그러면 계속 current hypothesis에 갇힐 수 있다.

즉 다음 악순환이 가능하다.

> world model이 아직 약함
alternative value를 낮게 추정함
planning을 안 씀
alternative evidence를 덜 모음
current hypothesis가 계속 유지됨
planning이 더 줄어듦
> 

이것이 planning collapse다.

---

## 3.13.2 soft allocation에서 hard gating으로 가야 한다

초기부터 hard threshold로 planning 여부를 결정하면 collapse 위험이 크다. 따라서 학습 초반에는 soft allocation을 쓰고, 학습 후반에 hard gating으로 가는 것이 좋다.

soft allocation은 다음처럼 둘 수 있다.

$p_t^{plan}=\sigma(\beta_0+\beta_1F_t^*+\beta_2\Delta_t-\beta_3C_t^{plan})$

초기에는 `p_t^{plan}`에 따라 stochastic하게 planning을 수행한다. 이렇게 하면 falsification과 action relevance가 애매한 구간에서도 가끔 planning을 시도한다. 이후 threshold annealing을 통해 점점 hard gating으로 전환한다.

hard gating은 다음과 같다.

$b_t^{plan}=\mathbf{1}[V_t^{realloc}>0]$

논문에서는 이 과정을 정직하게 써야 한다. “우리 방법은 항상 깔끔하게 필요한 순간만 planning한다”고 쓰면 안 된다. 실제로는 학습 안정화를 위해 soft-to-hard schedule이 필요할 수 있다.

---

## 3.13.3 threshold annealing

threshold annealing은 `τ_F`, `τ_Δ`를 학습 단계에 따라 조절하는 것이다. 초기에는 threshold를 낮춰 planning 경험을 확보하고, 후반에는 threshold를 높여 정말 필요한 순간에만 planning하도록 만든다.

$\tau_F(e)=\tau_F^{start}+\frac{e}{E}(\tau_F^{end}-\tau_F^{start})$

$\tau_\Delta(e)=\tau_\Delta^{start}+\frac{e}{E}(\tau_\Delta^{end}-\tau_\Delta^{start})$

여기서 `e`는 training epoch 또는 environment interaction phase고, `E`는 annealing horizon이다.

이 장치는 논문에서 “engineering trick”처럼 보일 수 있으므로, 목적을 명확히 써야 한다.

> Threshold annealing is used to avoid premature under-planning while the world model and value estimates are still poorly calibrated.
> 

즉 초기 모델이 불안정해서 planning을 꺼버리는 문제를 막기 위한 안정화 장치다.

---

## 3.13.4 budget target regularization

planning을 너무 적게 쓰는 것도 문제지만, 너무 많이 쓰는 것도 문제다. 따라서 target planning rate를 둘 수 있다.
$\displaystyle \mathcal{L}_{budget-rate}=\left(\frac{1}{T}\sum_{t=1}^{T}b_t^{plan}-\bar{p}_{plan}\right)^2$

이 항은 planning call 비율이 목표 범위에서 너무 벗어나지 않게 한다. 물론 최종 test-time에서는 이 항을 직접 쓰지 않을 수 있다. 하지만 학습 중 allocator가 collapse하거나 always-plan으로 가는 것을 막는 regularizer로 유용하다.

또는 Lagrangian 형태로 compute budget을 둔다.

$\mathcal{L}_{budget}=-\mathbb{E}[R]+\lambda_C(\mathbb{E}[C^{plan}]-\bar{C})$

이 구조의 핵심은 compute cost를 무시하지 않되, planning을 지나치게 억제하지 않는 것이다.

---

# 3.14 Full Algorithm Loop

## 3.14.1 전체 루프 직관적 설명

이제 전체 알고리즘을 한 번에 연결한다. 이 알고리즘은 매 tick마다 다음 질문을 한다.

1. 지금 무엇을 봤는가?
2. 이 관측을 바탕으로 현재 world state와 regime belief를 어떻게 업데이트할 것인가?
3. 지금 가장 믿는 규칙은 무엇인가?
4. 그 규칙보다 최근 evidence를 더 잘 설명하는 대안 규칙이 있는가?
5. 그 대안 규칙이 맞으면 실제 행동이 달라지는가?
6. 달라진다면 current rollout을 계속할 것인가, alternative rollout으로 계산을 옮길 것인가?
7. alternative rollout 결과 adaptation, correction, wait, detour, interaction 중 무엇이 가장 싼가?
8. 그 행동을 실행하면 tick cost, latency cost, failure risk가 어떻게 발생하는가?
9. 다음 관측으로 다시 belief를 업데이트한다.

이 흐름은 단순하다. agent는 매 순간 “내가 틀렸을 가능성”을 본다. 하지만 의심만 하지 않는다. 의심이 실제 행동을 바꾸는지 본다. 그리고 행동이 바뀔 때만 world model rollout의 계산 방향을 바꾼다.

---

## 3.14.2 단계 1: 관측 수집

agent는 전체 map을 보지 않는다. local observation, scalar state, event token만 본다.

$o_t=(o_t^{local},o_t^{scalar},e_t)$

여기서 local observation은 주변 grid window이고, scalar는 5개 상태값과 room progress, fail count 같은 값이다. event token은 interaction 성공/실패, checkpoint 통과, room entry 같은 신호다.

직관적으로 agent는 “눈앞의 일부 장면”과 “몸 상태 계기판”만 보는 것이다.

---

## 3.14.3 단계 2: latent belief 업데이트

관측을 받으면 recurrent latent state를 업데이트한다.

$z_t=f_\theta(z_{t-1},o_t,a_{t-1},e_t)$

그 다음 hidden state, change-point, regime posterior를 추정한다.

$\hat{s}_t=q_\phi^s(z_t,o_t,a_{t-1})$

$\hat{c}_t=q_\phi^c(z_t,o_t,e_t)$

$q_t(r)=q_\phi^r(z_t,o_t,e_t,\hat{c}_t)$

이 단계에서 중요한 것은 state와 regime를 동시에 업데이트한다는 점이다. agent는 “지금 어디에 있는가”와 “지금 어떤 규칙이 적용되는가”를 함께 추정한다.

---

## 3.14.4 단계 3: current/alternative hypothesis 선택

현재 가장 가능성 높은 regime를 current hypothesis로 둔다.

$\displaystyle r_t^{cur}=\arg\max_r q_t(r)$

그 다음 top-k 후보를 active hypothesis pool로 둔다.

$\mathcal{R}_t^{active}=\operatorname{TopK}(q_t(r),K=2)$

그리고 current를 제외한 후보 중 최근 observation-action window를 가장 잘 설명하는 것을 alternative로 둔다.

$\displaystyle r_t^{alt}=\arg\max_{r\in \mathcal{R}t^{active},r\neq r_t^{cur}}p_\theta(o_{t-w+1:t},e_{t-w+1:t}\mid r,\hat{s}_{t-w:t})$

이 단계는 계산량을 통제하기 위한 핵심이다. 모든 regime 조합을 다 비교하지 않는다. 현재 가장 유력한 가설과 가장 강한 대안 가설만 비교한다.

---

## 3.14.5 단계 4: falsification 계산

최근 evidence가 current보다 alternative를 더 잘 지지하는지 계산한다.

$B_t=\log p_\theta(o_{t-w+1:t},e_{t-w+1:t}\mid r_t^{alt},\hat{s}_{t-w:t})-\log p\theta(o_{t-w+1:t},e_{t-w+1:t}\mid r_t^{cur},\hat{s}_{t-w:t})$

change-point posterior를 결합한다.

$F_t^*=B_t+\lambda_{cp}\log\frac{C_t}{1-C_t+\epsilon}$

reveal-vs-shift 진단도 계산한다.

$\Gamma_t=\log p_\theta(o_t\mid \mathcal{H}_{shift},h_{t-1})-\log p_\theta(o_t\mid \mathcal{H}_{reveal},h_{t-1})$

이 단계의 질문은 다음이다.

> 지금 관측 변화는 단순히 새 정보를 본 것인가, 아니면 현재 규칙 가설이 틀렸다는 증거인가?
> 

---

## 3.14.6 단계 5: action relevance 계산

current와 alternative 아래에서 Q-value를 비교한다.

$\displaystyle \Delta_t=\left[\max_a Q(\hat{s}_t,r_t^{alt},a)-\max_a Q(\hat{s}_t,r_t^{cur},a)\right]_+$

action flip도 본다.

$\displaystyle a_t^{cur}=\arg\max_a Q(\hat{s}_t,r_t^{cur},a)$

$\displaystyle a_t^{alt}=\arg\max_a Q(\hat{s}_t,r_t^{alt},a)$

$I_t^{flip}=\mathbf{1}[a_t^{cur}\neq a_t^{alt}]$

이 단계의 질문은 다음이다.

> 대안 규칙이 맞다면 실제로 다른 행동을 해야 하는가?
> 

---

## 3.14.7 단계 6: compute reallocation 여부 결정

compute reallocation value를 계산한다.

$V_t^{realloc}=\max(0,F_t^*-\tau_F)\cdot\max(0,\Delta_t-\tau_\Delta)-\lambda_C C_t^{plan}$

계획 여부는 다음처럼 결정한다.

$b_t^{plan}=\mathbf{1}[V_t^{realloc}>0]$

하지만 학습 초기에는 soft planning probability를 사용할 수 있다.

$p_t^{plan}=\sigma(\beta_0+\beta_1F_t^*+\beta_2\Delta_t-\beta_3C_t^{plan})$

이 단계의 질문은 다음이다.

> 현재 가설 아래에서 즉시 행동할 것인가, 아니면 대안 가설 rollout으로 계산을 옮길 것인가?
> 

---

## 3.14.8 단계 7: current vs alternative rollout 비교

planning을 켜기로 했다면 current regime와 alternative regime 아래에서 각각 rollout을 수행한다.

$\tau_i^{cur}\sim \operatorname{Rollout}(W_\theta,\hat{s}_t,r_t^{cur},h_t)$

$\tau_i^{alt}\sim \operatorname{Rollout}(W_\theta,\hat{s}_t,r_t^{alt},h_t)$

각 rollout의 score는 task gain과 cost를 함께 반영한다.

$S(\tau)=w_1\operatorname{TaskGain}(\tau)-w_2\operatorname{FailureRisk}(\tau)-w_3\operatorname{LatencyCost}(\tau)-w_4\operatorname{ResetRisk}(\tau)-w_5\operatorname{PlanCost}(\tau)$

여기서 중요한 것은 alternative rollout이 단순 보조가 아니라 실제 행동 후보를 생성한다는 점이다. current rollout이 추천하는 행동과 alternative rollout이 추천하는 행동이 다르면, agent는 cost-normalized score를 기준으로 선택한다.

---

## 3.14.9 단계 8: adaptation / correction / detour / wait 중 선택

rollout 결과 agent는 여러 행동 전략 중 하나를 선택한다.

첫째, adaptation이다. 바뀐 규칙을 받아들이고 그 규칙에 맞춰 행동한다. 예를 들어 `W → D` remap을 감안해 목표 방향에 맞는 다른 키를 누른다.

둘째, correction이다. 상태값을 조절해 drift를 줄이거나 target band에 맞춘다. 예를 들어 final altar 앞에서 `i_t`를 band 안으로 넣는다.

셋째, detour다. invisible hazard field나 control interference zone을 우회한다.

넷째, wait다. periodic disturbance가 지나가기를 기다린다.

다섯째, immediate interaction이다. 현재 조건이 충분히 맞으면 바로 `E`를 누른다.

이 선택은 고정 규칙이 아니다. world model rollout이 각 선택의 future cost를 비교해서 결정한다. 그래서 이 논문은 단순 detector가 아니라 planner다.

---

## 3.14.10 단계 9: 실제 tick 비용 반영

선택한 행동은 simulator에서 실행되고 tick cost가 반영된다.

$$
$o_{t+1},r_t^{env},done,info=\operatorname{EnvStep}(a_t)$
$$

이때 실제 reward는 task reward와 비용 항으로 계산된다.

$$
$R_t=R_t^{task}-\lambda_{step}C_t^{step}-\lambda_{fail}C_t^{fail}-\lambda_{reset}C_t^{reset}-\lambda_{plan}C_t^{plan}-\lambda_{latency}C_t^{latency}$
$$

여기서 planning cost도 실제 cost에 들어간다. 따라서 agent는 “항상 plan”을 하면 손해를 본다. 반대로 planning을 너무 안 하면 failure/reset/latency cost가 증가한다. 최적 전략은 필요한 순간에만 compute를 쓰는 것이다.

---

## 3.14.11 단계 10: 다음 관측으로 belief 재업데이트

행동을 실행한 뒤 다음 관측이 들어오면 belief를 다시 업데이트한다. 이때 중요한 것은 prediction이 맞았는지뿐 아니라, 어떤 hypothesis 아래의 prediction이 더 맞았는지를 기록하는 것이다.

예를 들어 alternative rollout을 믿고 action을 바꿨는데 실제 결과가 alternative와 일치했다면, regime posterior는 alternative 쪽으로 이동해야 한다. 반대로 alternative가 틀렸다면 current hypothesis를 유지하거나 새로운 후보를 열어야 한다.

이 과정이 반복되면서 agent는 단순히 상태를 추적하는 것이 아니라, “어떤 규칙으로 세상을 봐야 하는지”를 계속 갱신한다.

---

# 3.15 Algorithm Pseudo-code

```python
# FRC-WM: Falsification-driven Regime-Conditioned World Model
# Core idea: do not merely allocate more compute; reallocate rollout compute
# from current hypothesis to alternative hypothesis when falsification is decision-relevant.

initialize world model parameters theta
initialize inference model parameters phi
initialize value model parameters psi
initialize allocator parameters alpha
initialize recurrent latent state z_0
initialize planning budget tracker BUDGET

for each episode:
    o_t, e_t = env.reset()
    z_t = init_recurrent_state()

    for t in range(T_max):

        # 1. collect partial observation
        # o_t includes local grid window and scalar state
        # e_t includes event token such as interaction success/fail, room entry, checkpoint
        obs = (o_t, e_t)

        # 2. update latent belief
        z_t = recurrent_update(z_t, o_t, a_prev, e_t)
        s_hat_t = infer_hidden_state(z_t, o_t, a_prev)
        C_t = infer_change_point(z_t, o_t, e_t)
        q_r_t = infer_regime_posterior(z_t, o_t, e_t, C_t)

        # 3. select current and alternative hypotheses
        r_cur = argmax(q_r_t)
        R_active = topk(q_r_t, k=2)
        r_alt = best_alternative_by_recent_likelihood(
            R_active,
            r_cur,
            recent_observation_window,
            recent_event_window,
            recent_state_belief_window
        )

        # 4. compute falsification
        B_t = loglik_recent(r_alt) - loglik_recent(r_cur)
        F_t = B_t + lambda_cp * log(C_t / (1.0 - C_t + eps))

        # 5. compute reveal-vs-shift diagnostic
        Gamma_t = loglik_shift(o_t, z_t) - loglik_reveal(o_t, z_t)

        # 6. compute action relevance
        Q_cur = value_model(s_hat_t, r_cur)
        Q_alt = value_model(s_hat_t, r_alt)

        a_cur = argmax(Q_cur)
        a_alt = argmax(Q_alt)

        Delta_t = max(0.0, max(Q_alt) - max(Q_cur))
        flip_t = int(a_cur != a_alt)

        # 7. compute reallocation value
        V_realloc = max(0.0, F_t - tau_F) * max(0.0, Delta_t - tau_D)
        V_realloc -= lambda_cost * planning_cost_estimate(BUDGET)

        # 8. decide whether to plan
        if training_phase == "early":
            p_plan = sigmoid(beta0 + beta1 * F_t + beta2 * Delta_t - beta3 * cost(BUDGET))
            use_planning = sample_bernoulli(p_plan)
        else:
            use_planning = (V_realloc > 0)

        # 9. rollout under current and alternative hypotheses if needed
        if use_planning:
            h_t, k_t = allocate_horizon_and_rollouts(F_t, Delta_t, BUDGET)

            rollouts_cur = rollout_world_model(
                s_hat_t,
                r_cur,
                horizon=h_t,
                num_rollouts=k_t
            )

            rollouts_alt = rollout_world_model(
                s_hat_t,
                r_alt,
                horizon=h_t,
                num_rollouts=k_t
            )

            candidates = rollouts_cur + rollouts_alt
            best_tau = argmax_score(candidates)
            a_t = first_action(best_tau)

        else:
            a_t = a_cur

        # 10. execute action and receive tick-level cost
        o_next, reward_env, done, info = env.step(a_t)

        # 11. compute decomposed reward and costs
        reward = compute_task_reward(info)
        reward -= lambda_step * info.step_cost
        reward -= lambda_fail * info.failure_cost
        reward -= lambda_reset * info.reset_cost
        reward -= lambda_plan * info.planning_cost
        reward -= lambda_latency * info.latency_cost

        # 12. store transition and update models
        replay.add(
            o_t=o_t,
            e_t=e_t,
            a_t=a_t,
            reward=reward,
            o_next=o_next,
            info=info,
            s_hat=s_hat_t,
            q_r=q_r_t,
            r_cur=r_cur,
            r_alt=r_alt,
            F_t=F_t,
            Delta_t=Delta_t,
            flip=flip_t,
            planning_used=use_planning
        )

        train_world_model_value_and_allocator(replay)

        if done:
            break

        o_t = o_next
        e_t = info.event_token
        a_prev = a_t
```

---

# 3.16 Part 2의 최종 논문 메시지

Part 2에서 최종적으로 전달되어야 하는 메시지는 다음이다.

> 제안 알고리즘은 current regime가 의심스럽다는 이유만으로 planning하지 않는다. 먼저 최근 observation-action evidence가 current hypothesis를 반증하는지 likelihood ratio와 change-point posterior로 평가한다. 그다음 alternative hypothesis가 실제 action choice를 바꿀 만큼 decision-relevant한지 value gap과 action flip으로 평가한다. 두 조건이 동시에 만족될 때만 current-regime rollout에서 alternative-regime rollout으로 compute를 재배치한다. 이 과정에서 control-drift는 mobility와 분리된 discrete action remap/miscontrol로 정의되며, drift 대응은 항상 correction이 아니라 adaptation, correction, wait, detour의 cost-sensitive 선택 문제로 처리된다. reward는 상태값 자체가 아니라 task success, latency, failure, reset, planning cost에 연결된다.
> 

이 문장이 Part 2의 결론이다.
이제 Part 3에서는 이 알고리즘이 실제로 드러나도록 **RG-4F 환경, task A/B/C/D, invisible noise field, target band/local override, baseline, ablation, OOD, metric**을 실험 설계 수준으로 닫으면 된다.