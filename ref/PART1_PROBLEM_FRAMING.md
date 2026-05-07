# Problem Framing & Latent Ontology

## Wrong-Hypothesis-Aware World-Model Planning

기존 STEP 3의 중심 문장은 이미 좋은 방향을 갖고 있었다. 원문은 이 논문을 “더 많이 상상하는 월드모델”이 아니라, “잘못된 규칙 가설 위에 planning을 지속하는 실패를 줄이기 위해 hidden state와 hidden regime를 분리 추적하고, 가설 반증과 행동 관련성에 따라 compute를 선택적으로 배분하는 월드모델”로 정의했다. 또한 기존 Problem Statement도 실패 원인을 단순 prediction error accumulation이 아니라 wrong dynamics hypothesis 위에서 계산을 낭비하거나 잘못된 행동을 안정적으로 선택하는 실패로 잡고 있었다.

다만 최종 개정판에서는 이 표현을 한 단계 더 밀어붙여야 한다. 핵심은 **compute를 더 쓰는 것**이 아니라, **현재 가설 아래의 rollout을 계속할지, 대안 가설 아래의 rollout으로 계산을 옮길지 결정하는 것**이다. 감사 문서에서도 최종 변경 방향은 “어려우면 더 많이 계산”이 아니라 “틀린 세계관 위에서 계산 중이면, 세계관부터 바꾸고 그쪽에 계산을 쓴다”로 정리되어 있다.

---

# 3.1 Problem Statement

## 3.1.1 최종 문제정의

본 논문은 부분관측 환경에서 world-model planner가 실패하는 원인을 단순히 “미래 예측이 조금씩 틀려서 오차가 누적된다”는 문제로 보지 않는다. 물론 world model은 예측 오차를 가진다. 그러나 본 논문이 다루는 핵심 실패는 그보다 더 구조적이다. planner가 현재 세계를 설명하는 dynamics hypothesis, 즉 “지금 세상이 어떤 규칙으로 움직이고 있는가”에 대한 가설을 잘못 잡은 상태에서, 그 가설을 오래 유지하며 rollout을 계속 수행하는 것이 문제다.

즉 실패의 핵심은 다음 문장으로 정리된다.

> 기존 world-model planner는 부분관측과 잠재 규칙 변화가 함께 존재하는 환경에서, 최근 관측이 현재 dynamics hypothesis를 반증하고 있음에도 동일한 hypothesis 아래에서 rollout을 지속한다. 이때 실패는 단순한 prediction error accumulation이 아니라, wrong dynamics hypothesis persistence에서 발생한다.
> 

여기서 `wrong dynamics hypothesis persistence`는 단순히 모델이 틀렸다는 뜻이 아니다. 더 정확히는, agent가 현재 상태를 예측하는 데 필요한 “세계의 작동 규칙”을 잘못 선택했고, 그 잘못된 규칙을 기반으로 미래를 상상하고, 그 상상 결과를 기반으로 행동을 고른다는 뜻이다. 이렇게 되면 planner는 더 많이 계산할수록 더 좋아지는 것이 아니라, 오히려 틀린 세계관을 더 정교하게 굴리는 장치가 된다.

쉬운 비유로 말하면 이렇다. 일반적인 prediction error 문제는 “내비게이션 지도가 몇 미터 정도 부정확한 문제”에 가깝다. 지도는 대체로 맞고, 위치가 조금씩 틀리기 때문에 보정하면서 가면 된다. 그러나 본 논문의 문제는 더 심각하다. 차가 평소에는 핸들을 오른쪽으로 돌리면 오른쪽으로 갔는데, 어떤 구간부터는 오른쪽으로 돌리면 왼쪽으로 가는 규칙으로 바뀌었다고 하자. 그런데 내비게이션은 여전히 “오른쪽 핸들 → 오른쪽 이동”이라는 옛 규칙으로 경로를 계산한다. 이 경우 경로를 더 길게 계산해도 소용없다. 문제는 horizon이 짧은게 아니라, **계산에 쓰는 세계 규칙이 틀렸다는 것**이다.

본 논문의 planner 실패는 바로 이 상황과 같다. agent가 부분관측 환경에서 작은 단서만 보고 있고, invisible noise field나 control-drift 같은 잠재 교란이 상태와 행동 결과를 바꾸며, 어떤 순간에는 동일한 행동이 이전과 다른 결과를 만든다. 이때 planner가 과거 regime를 계속 믿으면, world model rollout은 겉보기에는 일관적이지만 실제 환경과는 점점 멀어진다. 그 결과 agent는 틀린 행동을 우연히 한 번 선택하는 것이 아니라, 틀린 규칙 아래에서 반복적으로 그럴듯한 잘못된 행동을 선택한다.

따라서 본 논문은 기존 실패를 다음처럼 재정의한다.

> planning failure under partial observability is not only an error accumulation problem, but a hypothesis persistence problem: the planner continues to evaluate future trajectories under a dynamics hypothesis that should have been falsified by recent observations.
> 

이 문제정의가 중요한 이유는 해결 방향을 완전히 바꾸기 때문이다. 실패 원인을 “예측이 덜 정확하다”로 보면 해결책은 더 큰 모델, 더 긴 horizon, 더 많은 rollout, 더 촘촘한 uncertainty estimation 쪽으로 간다. 반대로 실패 원인을 “현재 dynamics hypothesis가 틀렸는데도 유지된다”로 보면 해결책은 먼저 **현재 가설을 의심하고, 대안 가설과 비교하고, 행동적으로 의미 있는 경우에만 대안 가설 아래로 rollout을 옮기는 것**이 된다.

이 논문은 후자의 관점을 따른다.

---

## 3.1.2 기존 planner가 틀리는 3층 구조

### 직관적 해설

기존 planner가 실패하는 이유는 한 층짜리 문제가 아니다. 단순히 “관측이 애매해서”나 “예측이 조금 틀려서”라고 쓰면 논문 주장이 약해진다. 본 논문에서 다루는 실패는 최소 세 층으로 나눠야 한다.

첫 번째 층은 **hidden state uncertainty**다. agent는 전체 월드맵을 보지 못한다. 주변 5x5 local window와 일부 scalar만 본다. 따라서 agent는 보이지 않는 방 내부 객체 상태, invisible hazard source, 아직 보지 못한 문/비석/altar 상태를 추정해야 한다. 이건 일반적인 부분관측 문제다.

두 번째 층은 **hidden regime uncertainty**다. agent가 모르는 것은 “무엇이 어디에 있는가”만이 아니다. 더 중요한 것은 “지금 어떤 규칙이 적용되고 있는가”다. 예를 들어 이동속도가 느려졌다면 단순히 무거운 조각을 들고 있어서 mobility가 떨어진 것일 수도 있고, friction field에 들어와 mobility dynamics 자체가 바뀐 것일 수도 있다. 또는 `A`를 눌렀는데 예상한 방향과 다르게 움직였다면, 단순히 collision 때문에 막힌 것일 수도 있고, control-drift regime가 바뀌어 입력 해석 규칙이 뒤틀린 것일 수도 있다.

세 번째 층은 **wrong hypothesis persistence**다. 이게 가장 중요하다. planner가 틀린 regime를 잠깐 의심하는 정도라면 큰 문제가 아닐 수 있다. 문제는 최근 관측이 이미 현재 regime 가설을 반증하고 있는데도, planner가 계속 기존 가설 아래에서 rollout한다는 점이다. 그러면 planning은 도움이 아니라 방해가 된다. planner는 더 멀리 보는 게 아니라, 잘못된 규칙으로 더 멀리 착각한다.

이 세 층을 실제 상황으로 풀면 다음과 같다.

agent가 C 방에 들어갔다. 원래는 `W`를 누르면 위로 이동한다. 그런데 어느 순간 invisible control interference field 때문에 입력 remap이 생겨 `W → D`처럼 오른쪽 이동으로 바뀌었다. agent는 local observation에서 자기 위치가 예상과 다르게 바뀐 것을 본다. 이 관측 변화는 여러 방식으로 설명될 수 있다.

1. 내가 벽에 걸려서 이동이 실패했나?
2. mobility가 낮아져서 아직 이동이 완료되지 않았나?
3. 내가 위치를 잘못 기억하고 있었나?
4. control-drift regime가 바뀌었나?
5. noise field 때문에 관측이 흔들렸나?

여기서 일반적인 prediction-error 기반 planner는 “예측이 틀렸다”는 신호만 본다. uncertainty gate는 “불확실성이 높다”고 판단할 수 있다. novelty detector는 “낯선 상황이다”라고 볼 수 있다. 그러나 이것만으로는 부족하다. 중요한 질문은 다음이다.

> 최근 관측은 현재 regime 가설을 반증하는가?
> 
> 
> 대안 regime 가설이 더 그럴듯한가?
> 
> 그 대안 regime가 맞다면 최적 행동이 달라지는가?
> 

이 세 질문을 묻지 않으면 agent는 단순히 놀라기만 한다. 반대로 이 세 질문을 묻기 시작하면, 문제는 anomaly detection이 아니라 hypothesis falsification이 된다.

### 학술적 서술

본 논문은 부분관측 sequential decision problem에서 world-model planning failure를 다음 세 요인의 결합으로 정의한다.

첫째, agent는 전체 상태를 직접 관측하지 못하므로 latent world state에 대한 posterior를 유지해야 한다. 둘째, 동일한 관측 변화가 state transition, observation noise, latent disturbance, 또는 dynamics regime shift에 의해 모두 설명될 수 있으므로, hidden regime에 대한 posterior도 함께 유지해야 한다. 셋째, planning module이 current regime hypothesis를 명시적으로 반증하지 못하면, 최근 evidence가 alternative regime를 지지하더라도 rollout은 current hypothesis 아래에서 지속된다.

따라서 본 논문의 핵심 failure mode는 다음과 같다.

> The planner persists with a current dynamics hypothesis even when recent observation-action evidence is better explained by an alternative regime, and this persistence leads to systematically wrong rollout evaluation and suboptimal closed-loop control.
> 

이 failure mode는 단순 open-loop prediction loss만으로 잘 드러나지 않는다. 예를 들어 한두 step의 observation prediction error는 작을 수 있다. 하지만 action-to-transition mapping이 틀린 경우, planning horizon이 길어질수록 agent는 잘못된 행동 결과를 일관되게 상상한다. 이 경우 모델은 “조금 부정확한 predictor”가 아니라 “틀린 causal rule을 가진 planner”가 된다.

따라서 본 논문은 world model을 다음과 같이 설계한다. agent는 hidden state posterior와 hidden regime posterior를 동시에 유지하고, change-point posterior를 통해 regime transition 가능성을 따로 추적한다. 그 다음 현재 regime hypothesis와 대안 regime hypothesis를 비교하고, 대안 hypothesis가 최근 관측을 더 잘 설명하며 그 차이가 실제 action choice를 바꿀 때만 compute를 해당 hypothesis 쪽으로 재배치한다.

---

# 3.2 Core Proposition

## 3.2.1 기존 문장의 문제

기존 Core Proposition은 다음 방향이었다.

> hidden world state와 hidden regime 및 change-point를 분리 추적하고, 최근 관측이 현재 regime hypothesis를 반증할수록 그리고 그 반증이 실제 최적 행동을 바꿀수록 planning compute를 더 배분하면, fixed planning, uncertainty gate, novelty-style mismatch gate, event-only gate보다 더 나은 closed-loop 성능-계산량 균형과 rule recombination/generalization 성능을 얻을 수 있다.
> 

이 문장은 핵심 요소를 거의 모두 포함한다. 그러나 “planning compute를 더 배분한다”는 표현은 아직 약간 위험하다. reviewer가 이 문장을 보면 “결국 불확실하거나 위험한 상황에서 더 많이 plan한다는 adaptive planning 아닌가?”라고 읽을 수 있다. 이 논문은 단순히 planning horizon을 늘리거나 rollout 수를 늘리는 논문으로 읽히면 안 된다.

최종판에서 강조해야 할 표현은 다음이다.

> 현재 가설 아래에서 계속 rollout할지, 대안 가설 아래로 rollout을 전환할지 결정한다.
> 

즉 compute의 양보다 먼저 compute의 **방향**이 중요하다. 이 논문은 “더 깊게 볼지”보다 “어떤 규칙으로 볼지”를 묻는다.

---

## 3.2.2 후보 문장 1: 보수적 버전

> 부분관측 tick-based 환경에서 hidden state, hidden regime, change-point를 분리 추적하고, 현재 regime hypothesis가 최근 관측에 의해 반증될 때 action relevance를 기준으로 planning compute를 선택적으로 사용하는 world-model planner를 제안한다.
> 

### reviewer reading

이 문장은 안전하다. 과장도 적고, 논문 범위도 좁다. 하지만 너무 보수적이다. “planning compute를 선택적으로 사용한다”는 표현 때문에 여전히 adaptive planning이나 uncertainty gating처럼 읽힐 수 있다. 핵심인 “대안 가설 아래로 rollout을 옮긴다”는 메시지가 약하다.

---

## 3.2.3 후보 문장 2: falsification 중심 버전

> 본 논문은 부분관측 환경에서 planner가 잘못된 dynamics hypothesis를 지속하는 실패를 regime falsification 문제로 재정의하고, hidden state와 hidden regime 및 change-point를 분리 추적하여 현재 hypothesis와 alternative hypothesis를 비교하는 world-model planning framework를 제안한다.
> 

### reviewer reading

이 문장은 문제정의는 강하다. `regime falsification`이 전면에 나오므로 novelty detector나 단순 uncertainty gate와 거리를 둘 수 있다. 그러나 아직 closed-loop action selection과 compute reallocation이 충분히 드러나지 않는다. 이 문장만 보면 “가설 비교를 잘하는 모델”이지 “그걸 planning compute와 행동 선택에 어떻게 연결하는지”가 약하게 보인다.

---

## 3.2.4 후보 문장 3: compute reallocation 중심 버전

> 부분관측과 잠재 regime 변화가 존재하는 환경에서, 본 논문은 최근 관측이 current dynamics hypothesis를 반증하고 alternative hypothesis가 실제 최적 행동을 바꿀 때, planning compute를 단순히 증가시키는 것이 아니라 alternative-regime rollout으로 재배치하는 world-model planner를 제안한다.
> 

### reviewer reading

이 문장이 가장 본 논문답다. “compute를 증가”가 아니라 “alternative-regime rollout으로 재배치”한다는 점이 분명하다. adaptive planning과의 차이도 선명하다. 다만 hidden state/regime/change-point 분리 구조가 문장 안에서 상대적으로 약하다. 따라서 최종 문장에서는 이 구조까지 함께 넣는 게 좋다.

---

## 3.2.5 후보 문장 4: 최종 논문형 버전

> 본 논문은 부분관측 tick-based 환경에서 hidden state, hidden regime, change-point를 분리 추적하고, 최근 observation-action evidence가 current dynamics hypothesis보다 alternative hypothesis를 더 강하게 지지하며 그 차이가 실제 action choice를 바꿀 때, planning compute를 더 많이 쓰는 것이 아니라 alternative-regime rollout으로 재배치하는 wrong-hypothesis-aware world-model planning framework를 제안한다.
> 

### reviewer reading

이 문장은 가장 강하다. 이 문장은 세 가지를 동시에 잡는다.

첫째, 다루는 환경이 부분관측 tick-based 환경임을 명확히 한다.

둘째, hidden state / hidden regime / change-point 분리를 전면에 둔다.

셋째, compute allocation이 아니라 compute reallocation임을 명확히 한다.

이 문장은 reviewer가 “adaptive planning 아닌가?”라고 읽는 위험을 줄인다. 왜냐하면 adaptive planning은 보통 “언제 더 길게 볼 것인가”에 집중하지만, 이 문장은 “어떤 dynamics hypothesis 아래에서 볼 것인가”를 중심에 두기 때문이다.

---

## 3.2.6 최종 채택 문장

최종 개정판 STEP 3 Part 1의 Core Proposition은 다음 문장으로 채택한다.

> 본 논문은 부분관측 tick-based 환경에서 hidden state, hidden regime, change-point를 분리 추적하고, 최근 observation-action evidence가 current dynamics hypothesis보다 alternative hypothesis를 더 강하게 지지하며 그 차이가 실제 action choice를 바꿀 때, planning compute를 단순히 증가시키는 것이 아니라 alternative-regime rollout으로 재배치하는 wrong-hypothesis-aware world-model planning framework를 제안한다.
> 

이를 조금 더 논문 abstract 문장처럼 쓰면 다음과 같다.

> We propose a wrong-hypothesis-aware world-model planner that separates hidden state, hidden regime, and change-points, and reallocates test-time planning from the current dynamics hypothesis to an alternative regime hypothesis only when recent evidence falsifies the current hypothesis and the alternative induces decision-relevant action changes.
> 

이 문장의 핵심은 `only when`이다. 아무 때나 대안 가설을 탐색하지 않는다. 낯설다고 무조건 planning하지 않는다. 위험하다고 무조건 horizon을 늘리지 않는다. 현재 가설이 반증되고, 대안 가설이 행동적으로 의미 있을 때만 계산 방향을 바꾼다.

---

# 3.3 Formal Setup: POMDP with Hidden State, Hidden Regime, and Change-point

## 3.3.1 POMDP 정의

본 논문이 다루는 환경은 일반적인 완전관측 MDP가 아니라 부분관측 POMDP다. agent는 실제 상태 전체를 보지 못한다. 관측 가능한 것은 local grid window, 일부 scalar state, event token뿐이다. 따라서 agent는 보이지 않는 상태와 보이지 않는 규칙을 동시에 추정해야 한다.

$\mathcal{M} = (\mathcal{S}, \mathcal{R}, \mathcal{A}, \mathcal{O}, T, \Omega, \rho, \gamma)$

여기서 각 구성요소는 다음 의미를 갖는다.

- `S`: hidden world state space
- `R`: hidden regime space
- `A`: action space
- `O`: observation space
- `T`: regime-conditioned transition function
- `Ω`: observation function
- `ρ`: reward function
- `γ`: discount factor

일반 POMDP와 다른 점은 `R`, 즉 hidden regime space를 명시적으로 둔다는 것이다. 일반적인 POMDP에서는 보이지 않는 모든 것을 hidden state 하나로 몰아넣을 수 있다. 그러나 본 논문에서는 그것을 의도적으로 나눈다. 왜냐하면 “지금 어디에 무엇이 있는가”와 “그것들이 어떤 규칙으로 변화하는가”는 planning 관점에서 다른 문제이기 때문이다.

---

## 3.3.2 hidden state란 무엇인가?

### 직관적 해설

hidden state는 “지금 실제 세상이 어떤 상태인가”를 뜻한다. agent가 못 보고 있을 뿐, 환경 안에는 실제로 존재하는 값들이다.

예를 들어 다음과 같은 것들이 hidden state다.

- 보이지 않는 방 안의 비석이 켜져 있는지
- 퍼즐 조각이 어디에 놓여 있는지
- invisible hazard source가 어디에 있는지
- 문이 열렸는지 닫혔는지
- agent가 전에 지나갔던 tile이 어떤 상태로 바뀌었는지
- noise field의 현재 영향권 안에 들어왔는지
- 현재 agent의 5차원 상태값이 실제로 얼마인지

이것들은 “세계의 현재 상태”다. 즉 사진 한 장을 찍는다면 그 안에 들어 있는 값들이다. 물론 agent는 그 사진 전체를 보지 못한다. 하지만 환경에는 존재한다.

쉬운 예시로, 어두운 방에 들어갔는데 책상 위에 열쇠가 있다고 하자. 내가 아직 손전등으로 책상을 비추지 않았기 때문에 열쇠를 못 봤다. 하지만 열쇠는 이미 거기에 있다. 이 경우 열쇠의 존재는 hidden state다. 내가 새로 본 것은 “새 정보의 reveal”이지, 세상 규칙이 바뀐 것은 아니다.

### 학술적 서술

hidden state는 시점 `t`에서 environment의 latent configuration을 나타낸다. 이는 agent의 observation에 직접 포함되지 않을 수 있지만, transition과 reward에 영향을 주는 모든 world variable을 포함한다. 본 논문에서 hidden state는 agent position, room object configuration, invisible hazard field state, controllable factor state, task progress, failure counters 등을 포함할 수 있다.

$s_t \in \mathcal{S}$

중요한 점은 hidden state가 dynamics rule 자체를 의미하지 않는다는 것이다. hidden state는 “현재 값”이다. 반면 regime는 “그 값들이 어떻게 변하는지”를 정의한다. 이 둘을 분리하지 않으면, agent는 새 정보를 본 것과 규칙이 바뀐 것을 구분하기 어렵다.

---

## 3.3.3 hidden regime란 무엇인가?

### 직관적 해설

hidden regime는 “지금 세상이 어떤 규칙으로 움직이고 있는가”를 뜻한다. state가 현재 장면이라면, regime는 장면이 다음 장면으로 바뀌는 법칙이다.

예를 들어 agent가 `W`를 눌렀을 때 위로 이동하는지, 오른쪽으로 이동하는지, 한 tick 늦게 이동하는지, 일정 확률로 미끄러지는지는 state 자체가 아니라 regime에 가깝다. `W`라는 행동과 다음 위치 사이의 관계가 달라졌기 때문이다.

마찬가지로 interaction intensity가 target band에서 벗어났을 때 interaction latency가 얼마나 늘어나는지, invisible noise field가 vision을 흔드는지 mobility를 흔드는지, noise mean이 천천히 drift하는지 이벤트 후 갑자기 shift하는지도 regime에 해당한다.

쉬운 비유를 들면, state는 체스판 위의 말 위치다. regime는 체스 규칙이다. 말 위치가 바뀐 것은 state update다. 그런데 어느 순간부터 나이트가 L자로 움직이지 않고 대각선으로 움직인다면 그것은 regime shift다. 두 문제는 완전히 다르다. 말 위치를 더 잘 기억하는 것만으로는 규칙 변화 문제를 해결할 수 없다.

### 학술적 서술

hidden regime는 transition law를 조건화하는 latent mode다. 본 논문에서 regime는 monolithic task label이 아니라 factorized dynamics code로 보는 것이 적절하다. 예를 들어 vision, mobility, interaction, noise, control-drift 각각에 대해 현재 어떤 dynamics mode가 적용되는지를 나타낼 수 있다.

$r_t \in \mathcal{R}$

current regime hypothesis는 다음과 같이 표기한다.

$r_t^{cur} = \arg\max_{r} q_t(r)$

alternative regime hypothesis는 current hypothesis를 제외한 후보 중 최근 관측을 더 잘 설명하는 후보로 둔다.

$r_t^{alt} = \arg\max_{r \neq r_t^{cur}} p_\theta(o_{t-w+1:t}, e_{t-w+1:t} \mid r, \hat{s}_{t-w:t})$

이 표기의 핵심은 planner가 단일 world hypothesis만 유지하지 않는다는 점이다. planner는 현재 가장 믿는 regime와, 그것을 대체할 수 있는 가장 강한 alternative regime를 비교한다. 이 비교가 있어야 “현재 가설을 계속 유지할지”와 “대안 가설로 rollout을 옮길지”를 결정할 수 있다.

---

## 3.3.4 change-point란 무엇인가?

### 직관적 해설

change-point는 “규칙이 바뀌는 순간인가?”를 나타내는 변수다. hidden state와 hidden regime를 분리하더라도, 언제 regime가 바뀌었는지를 따로 추적하지 않으면 모델은 모든 관측 변화를 애매하게 처리한다.

예를 들어 agent가 invisible noise field 근처에 들어가서 noise 값이 증가했다. 이 경우 두 가지 해석이 가능하다.

첫째, 원래 있던 field 영향권에 들어갔기 때문에 state가 바뀐 것이다. 이건 reveal 또는 state update다.

둘째, 어떤 checkpoint를 통과한 뒤 field mean 자체가 바뀌었다. 이건 regime shift다.

두 경우 모두 관측상으로는 noise가 증가한다. 하지만 의미는 완전히 다르다. 첫 번째 경우에는 “내 위치가 field 안으로 들어갔다”는 state belief를 업데이트하면 된다. 두 번째 경우에는 “이 field의 dynamics가 바뀌었다”는 regime belief를 업데이트해야 한다.

change-point는 바로 이 구분을 돕는다. change-point가 없다면 모델은 모든 변화를 state update로 밀어 넣거나, 반대로 모든 변화를 regime shift로 과잉해석할 수 있다.

### 학술적 서술

change-point variable은 시점 `t`에서 regime transition이 발생했는지를 나타내는 latent indicator다.

$c_t \in {0,1}$

$c_t = 1 ;;\text{indicates a possible regime transition at time } t$

agent는 hidden state, hidden regime, change-point에 대한 joint latent belief를 유지한다.

$b_t(s,r,c)=p(s_t=s,r_t=r,c_t=c \mid o_{1:t},a_{<t})$

이 belief는 본 논문의 핵심 형식이다. planner는 “지금 세상이 어디쯤인가”만 추정하지 않는다. 동시에 “지금 어떤 규칙이 적용되는가”와 “방금 규칙이 바뀌었는가”를 추정한다.

change-point를 명시적으로 두는 이유는 regime posterior의 급격한 변화를 구조적으로 설명하기 위해서다. posterior가 바뀌었다는 사실만으로는 부족하다. posterior shift만 보고 regime shift를 선언하면 순환논리가 된다. “내 posterior가 바뀌었으므로 세상이 바뀌었다”는 식이 되기 때문이다. 따라서 change-point는 관측 likelihood, event token, action outcome mismatch, 최근 window evidence와 함께 추정되어야 한다.

---

# 3.4 Why Separate Hidden State and Hidden Regime?

## 3.4.1 직관적 해설

hidden state와 hidden regime를 굳이 나누는 이유는 단순하다.

> 같은 관측 변화가 “새 정보를 본 것”일 수도 있고, “세상 규칙이 바뀐 것”일 수도 있기 때문이다.
> 

예를 들어 agent가 어떤 방에서 이동하려고 했는데 예상보다 늦게 도착했다. 이 관측은 여러 방식으로 설명된다.

1. 무거운 조각을 들고 있어서 mobility state가 낮아졌다.
2. friction field 안에 들어와 mobility dynamics가 바뀌었다.
3. agent가 위치를 잘못 기억했다.
4. 실제로는 이동했지만 local observation이 noise 때문에 흔들렸다.
5. 특정 tile에 들어가면 이동 cooldown이 증가하는 hidden rule이 활성화됐다.

이 중 어떤 것은 state update고, 어떤 것은 regime shift다. 만약 모든 것을 하나의 latent state에 넣으면 모델은 이 차이를 내부적으로 섞어버릴 수 있다. 그러면 agent는 어느 정도 예측은 할 수 있지만, 왜 예측이 틀렸는지, 어떤 대안 규칙으로 rollout해야 하는지, 그 대안 규칙이 행동을 바꾸는지 설명하기 어렵다.

비유하면, 의사가 환자를 진단할 때 “체온이 39도다”는 state다. 하지만 “바이러스 감염 때문에 체온이 계속 오르는 중인지”, “운동 직후라 일시적으로 오른 것인지”, “약물 반응으로 체온 조절 메커니즘이 바뀐 것인지”는 regime에 가깝다. 체온 숫자만 맞히는 것과 병의 작동 원리를 구분하는 것은 다르다. 치료를 하려면 숫자보다 작동 원리를 알아야 한다.

planner도 마찬가지다. 다음 관측을 맞히는 것만으로는 부족하다. 어떤 action을 했을 때 어떤 transition이 생기는지, 그 transition law가 바뀌었는지를 알아야 한다.

---

## 3.4.2 학술적 서술

hidden state와 hidden regime의 분리는 단순한 모델링 취향이 아니라, decision-relevant latent factorization이다. partial observability 하에서 관측 변화는 latent state transition, observation noise, exogenous disturbance, regime transition 등 여러 원인으로 생성될 수 있다. 이들을 하나의 latent vector에 모두 흡수하면 representation은 예측에는 유리할 수 있지만, hypothesis comparison과 counterfactual rollout에는 불리해질 수 있다.

본 논문에서 state-regime separation은 다음 목적을 가진다.

첫째, state posterior update와 regime posterior update를 분리한다.

둘째, current hypothesis와 alternative hypothesis를 명시적으로 비교할 수 있게 한다.

셋째, reveal과 shift를 구분한다.

넷째, action relevance를 regime-conditioned value difference로 계산할 수 있게 한다.

다섯째, explanation faithfulness와 counterfactual rollout fidelity를 평가할 수 있게 한다.

다만 여기서 매우 중요한 점이 있다. 본 논문은 “state와 regime가 완벽히 자동 분리된다”고 주장해서는 안 된다. 그것은 과장이다. 특히 weak supervision과 self-supervised discovery가 섞이는 환경에서는 regime factor가 완벽하게 의미론적으로 정렬된다는 보장이 없다. 따라서 최종 논문에서는 다음처럼 써야 한다.

> We do not assume that state-regime separation is automatically identifiable in all environments. Instead, we treat it as an inductive bias whose usefulness is evaluated through ablations, reveal-vs-shift diagnostics, counterfactual rollout fidelity, and closed-loop performance under regime recombination and parameter shift.
> 

즉 이 논문은 “우리가 항상 진짜 regime를 완벽히 찾는다”가 아니다. 더 정확한 주장은 “이 환경군에서는 state와 regime를 분리해 추적하는 inductive bias가 wrong-hypothesis persistence를 줄이고, closed-loop planning을 개선하는지 검증한다”다.

이 표현이 중요하다. 그래야 reviewer가 “regime/state 분리 임의적인 것 아닌가?”라고 공격했을 때 방어할 수 있다. 방어는 “완벽한 ontological truth를 주장한다”가 아니라, “이 분리가 planning과 OOD generalization에 유용한지 실험적으로 보인다”가 되어야 한다.

---

# 3.5 Reveal vs Shift

## 3.5.1 핵심 정의

본 논문에서 reveal과 shift는 반드시 분리되어야 한다.

reveal은 새로운 정보를 본 것이다. 세계의 규칙은 그대로인데, agent가 이전에 몰랐던 hidden state를 관측하거나 추론하게 된 상황이다.

shift는 규칙이 실제로 바뀐 것이다. 같은 state와 같은 action이라도 이후 transition, observation, reward relation이 달라지는 상황이다.

이를 수식으로 쓰면 다음과 같다.

$\mathcal{H}_{reveal}: r_t = r{t-1},; s_t \neq s_{t-1}$

$\mathcal{H}_{shift}: r_t \neq r{t-1}$

reveal-vs-shift 비교 점수는 다음처럼 둘 수 있다.

$\Gamma_t = \log p(o_t \mid \mathcal{H}_{shift},h_{t-1})-\log p(o_t \mid \mathcal{H}_{reveal},h_{t-1})$

여기서 `Γ_t`가 크면 최근 관측이 단순 state update보다 regime shift로 더 잘 설명된다는 뜻이다. 반대로 `Γ_t`가 작거나 음수라면, 새로운 정보를 본 것이지 규칙이 바뀐 것은 아닐 가능성이 크다.

---

## 3.5.2 직관적 해설: reveal 사례

예를 들어 agent가 중앙홀에서 북쪽 방으로 들어갔다. 이전에는 방 내부를 보지 못했기 때문에, 북쪽 방 안에 어떤 비석이 켜져 있는지 몰랐다. local window에 비석이 들어오자 agent는 비석이 켜져 있다는 사실을 알게 된다.

이건 reveal이다. 세계가 바뀐 것이 아니다. 비석은 원래 켜져 있었고, agent가 이제 본 것이다. 이 경우 planner는 regime를 바꿀 필요가 없다. state belief만 업데이트하면 된다.

다른 예시를 보자. agent가 invisible hazard source 근처에 들어갔다. 이전에는 source가 보이지 않았기 때문에 noise가 안정적이라고 믿었다. 그런데 특정 위치에 들어가자 noise 값이 조금 증가하기 시작했다. 이 경우도 우선은 reveal로 설명할 수 있다. 원래 그 위치 주변에 field가 있었고, agent가 그 영향권에 들어가면서 hidden state가 드러난 것이다.

이때 바로 “noise regime가 바뀌었다”고 선언하면 안 된다. 그것은 과잉해석이다. 그냥 안 보이던 field에 접근했을 수 있다. 이 구분이 없으면 agent는 모든 새로운 관측을 regime shift로 착각한다.

---

## 3.5.3 직관적 해설: shift 사례

반대로 shift는 규칙 자체가 바뀐 상황이다.

예를 들어 agent가 특정 checkpoint를 통과한 뒤, 같은 invisible field 안에 있어도 noise mean이 이전과 다르게 움직이기 시작한다. 이전에는 noise가 평균 0 근처에서 작게 흔들렸는데, checkpoint 이후 평균이 지속적으로 양수 방향으로 drift한다. 이 경우 단순히 field를 새로 본 것이 아니다. field의 dynamics가 바뀐 것이다.

또 다른 예시는 control-drift다. 이전에는 `W → up`, `A → left`, `S → down`, `D → right`였다. 그런데 특정 room event 이후 `W → right`, `A → up`처럼 input remap이 생겼다. 이 경우 agent의 위치가 달라진 것은 단순 state change지만, 그 원인은 action-to-transition rule 자체가 바뀐 것이다. 이것은 regime shift다.

정밀 interaction 직전에도 shift가 발생할 수 있다. 예를 들어 altar와 상호작용할 때 interaction target band가 이전에는 `i≈0`이었는데, 특정 event 이후 `i≈0.25`로 바뀌었다. agent가 이를 모르고 계속 `i≈0`에 맞추면 interaction latency가 증가하거나 실패한다. 이 경우 중요한 것은 interaction 값 자체가 아니라, target band를 결정하는 local regime가 바뀌었다는 점이다.

---

## 3.5.4 이 구분이 없으면 왜 anomaly detector가 되는가?

reveal-vs-shift 구분이 없으면 모델은 모든 관측 변화를 “이상하다”로 처리한다. 그러면 논문은 world-model planning 논문이 아니라 novelty detector 또는 anomaly-triggered planning 논문처럼 보인다.

예를 들어 agent가 새로운 방에 들어가서 처음 보는 문양을 봤다. novelty detector는 이것을 낯선 상황으로 본다. uncertainty gate는 불확실성이 높다고 본다. raw mismatch gate는 예측과 다르다고 본다. 그러나 이것이 regime shift인지는 별개의 문제다. 처음 보는 문양이더라도 규칙은 그대로일 수 있다. 반대로 관측상 변화가 작더라도 action 결과가 조금씩 어긋나기 시작하면 regime shift일 수 있다.

따라서 이 논문에서 중요한 것은 “낯섦”이 아니다. 중요한 것은 “현재 hypothesis가 최근 observation-action evidence를 설명하지 못하고, alternative hypothesis가 더 잘 설명하며, 그 차이가 행동 선택을 바꾸는가”다.

이 구분이 들어가야 논문은 anomaly detector가 아니라 falsification-driven world model이 된다.

---

## 3.5.5 이 구분이 있으면 왜 falsification 논문으로 읽히는가?

falsification은 단순히 틀렸다는 느낌이 아니다. 현재 가설과 대안 가설을 놓고, 최근 evidence가 어느 쪽을 더 지지하는지 비교하는 과정이다.

현재 가설은 다음처럼 둘 수 있다.

$H_t^{cur}: r_t = r_t^{cur}$

대안 가설은 다음처럼 둔다.

$H_t^{alt}: r_t = r_t^{alt}$

이제 agent는 최근 관측 window와 action outcome이 current hypothesis 아래에서 더 잘 설명되는지, alternative hypothesis 아래에서 더 잘 설명되는지 비교한다. 이 비교가 들어가면 모델은 단순 mismatch detector가 아니다. 왜냐하면 mismatch가 크다는 사실만 보는 것이 아니라, “어떤 대안 설명이 더 나은가”를 묻기 때문이다.

즉 reveal-vs-shift는 “변화가 있었다”를 묻고, current-vs-alternative hypothesis comparison은 “그 변화를 어떤 규칙 가설이 더 잘 설명하는가”를 묻는다. 두 구조가 결합될 때 본 논문의 정체성이 생긴다.

> 이 논문은 관측 변화에 놀라는 모델이 아니라, 관측 변화가 현재 world hypothesis를 반증하는지 평가하는 모델이다.
> 

---

# 3.6 Scope and Claim Boundary

## 3.6.1 이 논문이 다루는 환경군

본 논문은 모든 일반 환경에서 항상 더 좋은 world model을 주장하지 않는다. 그렇게 쓰면 과장이다. 대신 이 논문은 특정 구조를 가진 sequential decision environment에서 강하게 작동하는 메커니즘을 제안한다.

본 논문이 다루는 환경군은 다음 조건을 가진다.

첫째, **부분관측**이다. agent는 전체 상태를 직접 보지 못하고, local observation과 일부 scalar만 본다. 따라서 hidden state belief가 필요하다.

둘째, **잠재 교란이 있다**. invisible noise field, hidden hazard source, local control interference, interaction target shift처럼 관측되지 않거나 약하게만 관측되는 요인이 transition과 cost에 영향을 준다.

셋째, **미세한 drift와 갑작스러운 shift가 모두 존재한다**. 너무 큰 shift만 있으면 단순 detector도 잘한다. 본 논문의 강점은 작고 애매하지만 누적되면 큰 비용을 만드는 drift에서 current hypothesis를 오래 붙잡지 않는 것이다.

넷째, **동일한 관측 변화가 state update와 regime shift 양쪽으로 설명될 수 있다**. 즉 reveal-vs-shift ambiguity가 존재해야 한다. 그래야 hidden state/regime 분리가 의미를 가진다.

다섯째, **regime 차이가 실제 action choice를 바꾼다**. 규칙이 달라도 최선 행동이 같으면 planning reallocation의 이득이 작다. 본 논문은 alternative regime가 맞을 때 adaptation, correction, wait, detour, interaction timing 같은 행동 선택이 달라지는 환경을 대상으로 한다.

여섯째, **compute cost가 의미 있다**. planning을 항상 많이 쓰면 해결되는 환경이 아니라, 같은 성능이면 계산을 줄이고, 같은 계산이면 성능을 높이는 compute frontier가 중요한 환경이다.

이를 한 문장으로 쓰면 다음과 같다.

> 본 논문은 부분관측, 잠재 교란, subtle drift/abrupt shift, reveal-vs-shift ambiguity, 그리고 regime-dependent optimal action이 공존하는 sequential decision environment에서, wrong dynamics hypothesis persistence를 줄이기 위한 world-model planning framework를 제안한다.
> 

---

## 3.6.2 이 논문이 주장하지 않는 범위

본 논문은 다음을 주장하지 않는다.

첫째, 모든 환경에서 hidden state와 hidden regime가 완벽히 식별된다고 주장하지 않는다.

둘째, 모든 world-model planning 문제에서 compute reallocation이 항상 이긴다고 주장하지 않는다.

셋째, visual realism이 높은 3D simulator에서 범용 성능을 주장하지 않는다.

넷째, 단순 deterministic grid world 전체를 해결하는 일반 알고리즘이라고 주장하지 않는다.

다섯째, 단순히 더 많은 rollout을 수행하면 좋은 결과가 나온다고 주장하지 않는다.

오히려 본 논문은 더 좁고 강한 주장을 한다.

> regime ambiguity가 decision-relevant하고, current hypothesis persistence가 실제 행동 비용을 만들며, alternative hypothesis가 최근 evidence로 비교 가능할 때, state-regime-change-point factorization과 falsification-driven rollout reallocation은 fixed planning, always planning, uncertainty gate, novelty gate보다 더 나은 closed-loop return-compute tradeoff를 만들 수 있다.
> 

이렇게 범위를 제한하면 논문이 약해지는 것이 아니다. 오히려 강해진다. 왜냐하면 reviewer는 넓고 과장된 주장보다, 좁지만 명확하게 검증되는 주장을 더 신뢰하기 때문이다. 특히 이 논문은 메커니즘 논문이다. 목적은 “모든 게임에서 이긴다”가 아니라, “wrong-hypothesis-aware planning이라는 실패 모드와 해결 메커니즘을 명확히 보인다”다.

---

## 3.6.3 왜 이 scope가 실험환경과 정합적인가?

중앙홀-4방 구조, 5차원 상태벡터, tick-based dynamics, partial observation, invisible noise field는 이 scope를 검증하기 위한 장치다. 이 환경은 geometry 복잡도를 높이기 위한 환경이 아니다. 벽과 방을 복잡하게 많이 만드는 것이 목적이 아니다. 목적은 regime ambiguity와 compositional dynamics shift를 통제된 방식으로 만드는 것이다.

중앙홀-4방 구조는 각 방을 서로 다른 regime family로 설계할 수 있게 한다. 예를 들어 한 방은 mobility와 interaction을 흔들고, 다른 방은 vision과 mobility를 흔들고, 또 다른 방은 noise와 control-drift를 흔든다. agent는 방 위치를 외우는 것이 아니라, local cue와 action outcome을 통해 현재 어떤 regime factor가 활성화되었는지 추론해야 한다.

부분관측은 필수다. 전체 맵과 모든 hidden variable을 보여주면 hidden state/regime 추론 문제가 약해진다. 반대로 local observation만 주면 agent는 과거 기억과 최근 action outcome을 이용해 belief를 업데이트해야 한다. 이때 reveal과 shift의 구분이 중요해진다.

invisible noise field는 단순 방해물이 아니다. 이것은 “관측 가능한 변화는 작지만 latent dynamics가 누적적으로 바뀌는 상황”을 만들기 위한 장치다. field mean이 조금씩 drift하거나 event 이후 shift하면, agent는 current hypothesis를 계속 유지할지, alternative hypothesis를 고려할지 결정해야 한다.

따라서 이 환경은 “장난감 2D 환경”이 아니라, wrong-hypothesis-aware planning 메커니즘을 검증하기 위해 의도적으로 단순화되고 통제된 benchmark다.

---

# 3.7 Reviewer Risk and Defense

## 3.7.1 공격 1: “그냥 adaptive planning 아닌가?”

### 위험

이 공격은 가장 먼저 들어올 가능성이 높다. reviewer가 “불확실하면 더 많이 plan하는 거 아닌가?”라고 읽으면 논문 novelty가 약해진다. 특히 기존 Core Proposition에서 “planning compute를 더 배분한다”는 표현은 이 오해를 부를 수 있다.

### 방어

Part 1에서는 반드시 다음 구분을 전면에 둬야 한다.

adaptive planning의 중심 질문은 다음이다.

> 언제 더 길게 볼 것인가?
> 

본 논문의 중심 질문은 다르다.

> 어떤 dynamics hypothesis 아래에서 볼 것인가?
> 

즉 본 논문은 horizon 조절만 하는 것이 아니다. current hypothesis 아래의 rollout과 alternative hypothesis 아래의 rollout을 비교한다. planning compute가 증가할 수도 있지만, 핵심은 증가가 아니라 재배치다. current regime rollout을 계속하는 것이 아니라, 대안 regime가 더 그럴듯하고 행동적으로 중요할 때 그쪽으로 계산을 옮긴다.

따라서 최종 문장에는 `compute allocation`보다 `compute reallocation` 또는 `alternative-regime rollout reallocation`을 써야 한다.

---

## 3.7.2 공격 2: “heuristic threshold 아닌가?”

### 위험

falsification score, action relevance, threshold가 들어가면 reviewer는 “그냥 여러 score를 곱한 heuristic 아닌가?”라고 볼 수 있다.

### 방어

Part 1에서는 아직 세부 수식까지 깊게 들어가지는 않지만, 논리적 방어는 깔아야 한다. 핵심은 이 구조가 단순 heuristic이 아니라 value-of-computation의 근사라는 점이다.

즉 planning을 더 할지 말지는 다음 세 조건에 의해 정당화된다.

1. alternative hypothesis가 current hypothesis보다 최근 evidence를 더 잘 설명한다.
2. alternative hypothesis가 맞으면 최적 행동이 달라진다.
3. 그 행동 변화의 기대 이득이 추가 compute cost보다 크다.

이 세 조건은 Part 2에서 수식화된다. Part 1에서는 reviewer가 이 논문을 score engineering으로 읽지 않도록, 문제정의부터 “decision-relevant falsification”으로 잡아야 한다.

---

## 3.7.3 공격 3: “regime/state 분리가 임의적 아닌가?”

### 위험

hidden state와 hidden regime를 나누는 것은 강한 inductive bias다. reviewer는 “왜 이 변수가 state가 아니라 regime인가?”, “regime label을 사람이 넣어준 것 아닌가?”, “분리가 안 되면 어떻게 되는가?”라고 물을 수 있다.

### 방어

방어는 세 단계다.

첫째, 본 논문은 완벽한 식별을 주장하지 않는다.

둘째, 분리는 task success를 위한 inductive bias다.

셋째, 이 inductive bias의 유용성은 ablation으로 검증한다.

예를 들어 no-regime model, monolithic-regime model, no-change-point model, state-only memory model과 비교한다. 만약 full model이 wrong-hypothesis persistence time을 줄이고, action flip timing을 개선하고, OOD에서 더 낮은 성능 하락을 보인다면, state-regime separation은 단순 임의적 설계가 아니라 실험적으로 유용한 구조가 된다.

Part 1에서는 이 점을 정직하게 써야 한다.

> We do not claim universal identifiability of regimes. We evaluate whether this factorization reduces wrong-hypothesis persistence and improves closed-loop planning under controlled regime ambiguity.
> 

이 문장이 들어가야 공격을 줄일 수 있다.

---

## 3.7.4 공격 4: “world model이 아니라 detector game 아닌가?”

### 위험

regime shift, change-point, falsification 같은 표현이 많으면 reviewer가 “이건 그냥 hidden event detector를 잘 맞히는 게임 아닌가?”라고 볼 수 있다. 즉 실제 planning 논문이 아니라 detection benchmark처럼 읽힐 수 있다.

### 방어

방어는 metric과 claim을 연결해야 한다. Part 1에서는 다음을 분명히 한다.

본 논문의 목적은 change-point를 맞히는 것이 아니다. change-point detection은 중간 변수다. 최종 목적은 closed-loop action quality다.

따라서 다음 지표들이 중요하다.

- success rate
- return
- compute-normalized return
- wrong-hypothesis persistence
- action flip precision
- counterfactual rollout fidelity
- explanation faithfulness
- OOD performance drop

즉 detection이 좋아도 행동이 좋아지지 않으면 실패다. 반대로 본 논문이 성공하려면 “regime를 잘 맞혔다”가 아니라 “그 regime belief가 rollout과 행동 선택에 실제로 쓰였고, 그 결과 return-compute frontier가 좋아졌다”를 보여야 한다.

Part 1에서는 이 방향을 선언하고, Part 3에서 metric으로 닫아야 한다.

---

# 3.8 Part 1의 최종 논문형 요약 문단

아래 문단은 최종 개정판 STEP 3의 앞부분에 그대로 들어갈 수 있는 형태다.

> Existing world-model planners often treat planning failures under partial observability as prediction error accumulation: the model imagines the future, small errors compound, and the resulting trajectory becomes unreliable. We argue that this view misses a more structured failure mode. In environments where latent disturbances, subtle drift, and regime-dependent action semantics coexist, the planner may continue to roll out futures under a dynamics hypothesis that recent observation-action evidence should have falsified. In such cases, planning more is not necessarily useful; it may simply produce more internally consistent but externally wrong futures. We therefore formulate the problem as wrong dynamics hypothesis persistence. Our framework separates hidden world state, hidden regime, and change-points, compares current and alternative regime hypotheses, and reallocates planning from the current hypothesis to an alternative-regime rollout only when the alternative is both better supported by recent evidence and decision-relevant for action choice.
> 

한국어 논문 설명형으로 쓰면 다음과 같다.

> 기존 world-model planner의 실패는 단순히 미래 예측 오차가 horizon을 따라 누적되는 문제만으로 설명되지 않는다. 부분관측, 잠재 교란, 미세한 dynamics drift, 그리고 action semantics 변화가 공존하는 환경에서는 planner가 이미 반증되어야 할 current dynamics hypothesis를 계속 유지하며 rollout을 수행하는 실패가 발생한다. 이때 더 많은 planning은 해결책이 아니라, 틀린 규칙 가설 위의 계산 낭비가 될 수 있다. 본 논문은 이 실패를 wrong dynamics hypothesis persistence로 정의하고, hidden state, hidden regime, change-point를 분리 추적하는 latent world model을 제안한다. 핵심은 불확실하거나 낯선 상황에서 무조건 더 많이 planning하는 것이 아니라, 최근 observation-action evidence가 current hypothesis보다 alternative hypothesis를 더 강하게 지지하고 그 차이가 실제 action choice를 바꿀 때, planning compute를 alternative-regime rollout으로 재배치하는 것이다.
> 

이 Part 1의 결론은 하나다.

> 이 논문은 더 많이 보는 논문이 아니라, 틀린 규칙으로 보고 있을 때 어떤 규칙으로 다시 볼지 결정하는 논문이다.
>