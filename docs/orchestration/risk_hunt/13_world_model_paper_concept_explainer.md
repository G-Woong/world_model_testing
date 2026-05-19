# FRCG-WM 논문 개념 지도 — 처음 읽는 사람을 위한 완전 해설

```
작성일: 2026-05-19
담당: Main Claude (Research Explainer)
목적: STEP8~STEP10, Risk-Hunt, LFD redesign, v0_5, CUSUM/LFD 비교 결과를
      처음 읽는 사람도 직관적으로 이해할 수 있도록 단일 문서로 정리
코드 변경 없음 / 새 실험 없음 / 순수 설명 문서
```

---

## §1. 한 문장으로 이 논문은 무엇을 하려는가

> **Web/GUI 에이전트가 "틀린 지도"를 믿고 반복 실패할 때, 그 지도가 틀렸다는 누적 증거를 감지하고, 올바른 지도로 갱신하고, 그에 맞춰 행동 방식을 다시 쓰는 계층을 설계한다.**

비유로 시작하자. 당신이 내비게이션을 믿고 운전하는데, 브레이크를 밟아도 차가 계속 가속한다. 한 번은 오작동이라고 넘길 수 있다. 두 번, 세 번? 그때는 "내 차(=행동 모델)의 기본 동작 원리 자체가 내가 이해하는 것과 다르다"는 사실을 의심해야 한다. 이것이 이 논문이 다루는 실패 패턴이다.

기존 Web/GUI 에이전트 연구들은 다음을 해결하려 했다.
- 클릭 위치를 잘못 잡는다 → visual grounding 개선
- 다음 화면을 예측 못한다 → next-state world model
- 나쁜 행동을 선택한다 → better planning
- 행동이 실패했다는 걸 감지 못한다 → action-effect verification

이 논문이 다루는 문제는 다르다. 위 모든 것이 제대로 작동해도 발생하는 실패다.

**에이전트가 어떤 행동 규칙(control grammar)을 쓰고 있는지에 대한 가설이 틀렸고, 그 틀린 가설이 falsifying evidence(반증 증거)가 나온 뒤에도 오래 지속되는 것.**

이를 `wrong-control-grammar hypothesis persistence`라고 부른다. 이 논문은 이 persistence를 줄이는 시스템을 만들려 한다.

---

## §2. 월드모델이란 무엇인가

### 내부 시뮬레이터로서의 월드모델

월드모델(world model)이란 에이전트가 머릿속에 갖고 있는 환경 시뮬레이터다. "내가 이 버튼을 클릭하면 어떤 일이 일어날까?"를 실제로 클릭하지 않고 예측하는 내부 모델이다.

```
model-free agent:  o_t → a_t  (환경을 직접 탐색하며 경험에서 배움)
model-based agent: o_t → WM → 가상 시뮬레이션 → a_t  (내부 모델로 미리 생각)
```

월드모델의 핵심 장점은 **compute 재배분**이다. 같은 계산 예산으로 실제 환경에서 시행착오를 반복하는 대신, 내부 모델로 미리 여러 선택지를 시뮬레이션할 수 있다.

### "다음 상태"만 잘 예측하는 것은 왜 충분하지 않은가

많은 월드모델 연구가 `o_t, a_t → o_{t+1}`을 잘 예측하는 것을 목표로 한다. 픽셀 단위로 다음 화면을 맞추거나, DOM 변화를 예측하는 것. 이것만으로는 충분하지 않다.

예를 들어보자. 쇼핑몰에서 "필터 검색"을 하려는 에이전트가 있다. 이 환경에는 두 가지 규칙이 있다.

- **검색창 문법**: 검색어를 타이핑하고 Enter
- **드롭다운 선택 문법**: 카테고리를 드롭다운 메뉴에서 선택

에이전트가 "검색창 문법"을 쓰고 있는데, 실제 환경은 "드롭다운 선택 문법"이 필요한 상황으로 바뀌었다. 에이전트가 계속 검색창에 타이핑한다. 화면이 바뀌긴 한다(next-state 예측 성공). 그런데 원하는 필터가 적용되지 않는다. 에이전트는 계속 같은 틀린 행동을 반복한다.

**next-state를 잘 예측해도, 어떤 문법 규칙이 현재 적용되는지를 모르면 planning이 소용없다.**

이 논문의 월드모델은 단순 next-state predictor가 아니다. **어떤 제어 문법(control grammar) 가설이 현재 유효한지, 그 가설이 반증되고 있는지**를 추적하는 task-relevant latent structure를 학습한다.

---

## §3. "세계관 가설"이란 무엇인가

### Control Grammar의 정의

이 논문에서 `control grammar`는 다음을 묶은 하나의 구조다.

```
control grammar = {
  intent → executable action 변환 방법,
  precondition: 이 문법이 적용되기 위한 환경 조건,
  expected effect: 이 문법대로 행동했을 때 기대되는 결과
}
```

단순히 "어떤 행동을 취한다"가 아니다. "이런 조건에서, 이렇게 행동하면, 이런 결과가 나온다"는 **규칙의 집합**이다.

`regime`은 이러한 control grammar들이 적용되는 환경 모드 전체다. "검색 폼 모드", "드롭다운 선택 모드", "로그인 모드" 등이 regime의 예다.

### Wrong Hypothesis란 무엇인가

에이전트는 매 step마다 어떤 가설을 기반으로 행동한다.

```
current hypothesis h_exec = (현재 믿고 있는 regime, control grammar, 상태, 이벤트 유형)
```

이 가설이 실제 환경의 규칙과 맞지 않으면, 에이전트는 아무리 노력해도 원하는 결과를 얻지 못한다. 이것이 `wrong hypothesis`다.

### Noise vs Structural Mismatch

한 번 실패했다고 해서 가설이 틀린 것은 아니다. 클릭이 빗나갈 수 있고, 네트워크가 느릴 수 있고, 화면이 아직 로딩 중일 수 있다. 이것은 노이즈다.

그런데 **같은 패턴의 실패가 누적되면** 얘기가 달라진다. 비유하자면:

- 브레이크를 한 번 밟았는데 차가 멈추지 않았다 → 노이즈 (도로가 미끄러울 수 있음)
- 브레이크를 다섯 번 밟았는데 매번 차가 가속했다 → structural mismatch (내 차 모델이 틀림)

이 논문의 핵심은 **노이즈와 structural mismatch를 구분하는 것**이다. single-step 실패 flag가 아니라, **누적된 action-effect 증거의 패턴**을 보고 판단한다.

---

## §4. Learned Falsification Detector: 핵심 수식과 개념

### Falsification Score의 수식

```
F_t = max_{h_alt ∈ A_t^H} [ ℓ_t(h_alt) - ℓ_t(h_exec) ]
```

각 항의 의미:
- `ℓ_t(h)` = 가설 `h`가 직전 action-effect evidence `e_t`를 얼마나 잘 설명하는가 (log-likelihood)
- `h_exec` = 직전 action을 실제로 생성할 때 사용된 가설 (posterior mode가 아니라 **실제 사용된** 가설)
- `A_t^H` = 대안 가설들의 집합
- `F_t` = 대안 가설이 현재 가설보다 evidence를 더 잘 설명하는 정도

**F_t가 크다 = "내 현재 가설이 틀렸을 가능성이 높다"**

예시로 설명하면: 에이전트가 "검색창 문법"을 쓰고 있다(h_exec). 텍스트를 타이핑했는데 아무것도 일어나지 않았다(e_t). 이 evidence를 "검색창 문법"으로 설명하면 ℓ_t(h_exec)가 낮다. 반면 "드롭다운 선택 문법"으로 설명하면(h_alt) "검색창은 비활성 상태다"라는 설명이 되므로 ℓ_t(h_alt)가 높다. → F_t가 크다.

### Decision Gate: 언제 planning compute를 쓰는가

```
G_t = I[
  F_t > τ_f                                        (1. 현재 가설이 반증될 가능성)
  ∧ ΔV_t > τ_v                                     (2. 대안 가설이 더 나은 expected progress)
  ∧ P(action_switch | A_t^H, H_t) > τ_a            (3. 실제 행동이 바뀔 가능성)
  ∧ ΔV_t - C_plan > 0                              (4. 이득이 compute cost보다 큼)
]
```

네 조건이 **모두** 충족될 때만 planning compute를 추가로 쓴다. 이는 "불확실하면 더 생각한다"는 uncertainty-gated planning과 근본적으로 다르다.

uncertainty-gated planning은 모른다는 이유만으로 compute를 쓴다. 이 논문의 gate는 더 까다롭다.
1. 내 현재 가설이 반증되고 있어야 한다.
2. 대안 가설로 바꾸면 더 나은 행동을 할 수 있어야 한다.
3. 행동이 실제로 바뀌어야 한다.
4. 그 이득이 planning에 쓰는 compute 비용보다 커야 한다.

### CUSUM / BOCPD와의 관계

CUSUM(Cumulative Sum)은 신호의 누적 합을 보고 변화점을 감지하는 고전적 통계 방법이다. BOCPD(Bayesian Online Changepoint Detection)는 베이지안 방식으로 run length(마지막 변화점 이후 경과 step 수)의 posterior를 유지한다.

이 논문의 FalsificationDetectorHead는 세 가지 서브 신호를 계산한다.
- `effect_scalar`: 단계별 action-effect mismatch 신호
- `run_length_head`: BOCPD posterior (wrong이 얼마나 지속됐는지)
- `cusum_head`: 누적 통계
- `wrong_prob_head`: 학습된 P(wrong | history)

**CUSUM/BOCPD를 내 학습 가능한 아키텍처에 통합하되, grammar-conditioned signal로 확장하는 것이 핵심 주장이다.** 순수 통계적 changepoint detector와 다른 점은 (a) grammar-conditioned likelihood를 사용하고, (b) 탐지 결과가 planning과 action rewrite로 이어진다는 점이다.

---

## §5. 실험 흐름 시간순

### STEP 8: 첫 신호, 그리고 degenerate 문제

*질문*: v0_4 데이터로 기본 학습이 되는가?

*실험*: v0_4 5000 episodes, Stage A(기본 지식 학습) + Stage B(falsification 추가 학습)

*결과*:
- C4 (task success): test_id=0.994, test_ood=0.998 → **천장 효과 (ceiling effect)**. 0.99는 좋아 보이지만, 모든 에이전트가 0.99면 구분이 불가능하다.
- C3 (falsification F1): **predicted_wrong=0, F1=0.0** → degenerate. 학습이 아예 안 된 것.
- C6 (compute gate): FRCG-LR PPC=0.221 vs ABL-036=0.015 → 93% 격차 (예비 결과)

*판정*: AT_RISK / MEDIUM. C3이 완전히 무너졌다.

### STEP 9: Proxy로 "회복", 하지만 진짜인가?

*질문*: CUSUM 방식의 proxy를 써서 C3을 회복할 수 있나?

*해결책*: `planner.py:120-134`에 proxy 추가. `no_state_change` 관찰이 오면 `effect_type=3(failed)`로 강제 치환.

*결과*:
- C3 F1=0.539 (std=0.075, n=5 seeds) → 회복!
- C6 14.9× advantage 보고

*판정*: 회복으로 보였다. 하지만 뒤에서 밝혀지듯, 이것은 학습된 signal이 아니었다.

### Risk-Hunt Loop-01: Proxy OFF 실험 — 치명적 발견

*질문*: proxy를 제거하면 F1이 유지되는가?

*실험*: 같은 체크포인트로 proxy ON vs proxy OFF 비교 (50 episodes, 284 steps)

*결과*:

| 지표 | Proxy ON | Proxy OFF |
|---|---|---|
| C3 F1 | 0.5806 | **0.0000** |
| Mean F_t | +0.098 | **-0.464** |
| Steps with F_t > τ | 146 / 284 | **0 / 284** |

→ **proxy OFF 상태에서 학습된 falsification signal이 단 하나도 없다.**

모든 positive 예측 146건이 `observed_effect_type == "no_state_change"` 휴리스틱과 1:1 대응했다. 즉 에이전트는 "관찰된 화면 변화가 없으면 wrong"이라는 규칙을 학습한 게 아니라, proxy가 그냥 label을 그렇게 매겨줬을 뿐이다.

*결론*: **STEP 9의 C3 F1=0.539 회복은 학습된 signal이 아닌 `no_state_change` 휴리스틱 artifact였다.** **REJECT.**

### Risk-Hunt Loop-02: 5-seed 분산 검증

*질문*: 5개 독립 seed에서 일관된 결과가 나오는가?

*결과*:

| Seed | C3 F1 |
|---|---|
| 42 | 0.5806 |
| 123 | 0.4198 |
| 456 | 0.4762 |
| 789 | 0.5785 |
| 999 | 0.5806 |
| **mean ± std** | **0.527 ± 0.075** |

→ seed 42와 999가 동일 결과를 낸다 (1 epoch 내 같은 plateau에 수렴). Loop-01에서 proxy artifact임이 확인됐으므로 이 분산도 휴리스틱 boundary 근처의 noise다.

*결론*: 통계적 분산은 확보됐으나, 분산 자체가 학습된 signal이 아님을 재확인.

### Risk-Hunt Loop-06: C6 14.9× → 2.0× 수정

*질문*: C6 compute advantage가 fair 조건에서도 성립하는가?

*배경*: 기존 ABL-036(heuristic bypass)은 model forward를 건너뛰면서도 rollout_steps=10을 self-report로 신고했다. 분모가 부풀려진 artifact였다.

*실험*: ABL-036b(RealNoGateAblation) 추가 — full FRCG model forward + gate=always

*결과*:

| Agent | C6 PPC | planning_calls_total |
|---|---|---|
| FRCG-LR | 0.1926 | **0** (gate 한 번도 안 열림) |
| ABL-036b (fair) | 0.0963 | 284 |
| ABL-036 (heuristic) | 0.0130 | 284 |

→ FRCG-LR vs ABL-036b fair: **2.0×** (기존 14.9×에서 7.4배 축소)

*결론*: C6 advantage는 살아있으나 과장됐다. 14.9× 표현 금지. 또한 50 episodes 동안 gate가 **단 한 번도 열리지 않았다**는 사실이 더 심각하다 — gate가 작동하지 않는다면 planning 이점을 주장할 수 없다.

### Phase 9 Oracle-Probe: LFD vs CUSUM 첫 비교

*모드*: SYNTHETIC ORACLE PROBE (collect_episode()가 v0_5 switch를 처리하지 못해 oracle simulation으로 effect stream 생성)

*결과*:

| Metric | CUSUM (h=2.0) | SPRT | LFD mean±std |
|---|---|---|---|
| AUROC | 0.913 | 0.913 | **0.947 ± 0.004** |
| regime_shift_F1 | **0.635** | 0.000 | 0.632 ± 0.055 |
| FAR/step | **0.086** | 0.075 | 0.581 ± 0.060 |
| detection_delay | 2.356 | 5.872 | **0.288 ± 0.308** |

→ *F1은 동일, FAR에서 LFD가 6.8배 불리, AUROC에서 LFD 소폭 우위 (비유의).*

*판정*: **LFD_NOT_BETTER_THAN_CUSUM** — AUROC +0.034가 통계적으로 유의하지 않다(N=250, p≈0.41).

### Phase 9 Oracle-Free v0_5: 진짜 데이터로 재비교

*모드*: ORACLE-FREE, collect_episode() 사용, v0_5 grammar switch 처리 (TASK_COLLECTOR_V05_SWITCH 완료 후)

*결과*:

| Metric | CUSUM (h=2.0) | SPRT (A=3.0) | LFD mean±std |
|---|---|---|---|
| AUROC | 0.692 | 0.692 | **0.842 ± 0.003** |
| AUPRC | 0.479 | 0.479 | **0.707 ± 0.012** |
| regime_shift_F1 | **0.237** | **0.237** | 0.178 ± 0.000 |
| detection_delay | 0.231 | 0.192 | **0.000 ± 0.000** |
| FAR/step | **0.086** | **0.086** | 0.382 ± 0.127 |
| train_loss | N/A | N/A | 1.53 (비감소) |

→ AUROC에서 +0.150 우위가 있다. 하지만 F1에서 CUSUM이 이기고, FAR이 4.4배 불리하고, train_loss가 15 epochs 동안 감소하지 않았다.

*판정 (기록)*: `LFD_PARTIALLY_BEATS_CUSUM_NEEDS_CALIBRATION`
*권고 revised*: `LFD_AUROC_ADVANTAGE_UNCONFIRMED_ORIGIN_NOT_DEPLOYABLE_AS_GATE`

---

## §6. 살아남은 것 vs 죽은 것 vs 애매한 것

### 살아남은 것 (KEEP)

| 항목 | 근거 |
|---|---|
| **문제 정의 자체** | wrong-control-grammar persistence는 독립적 failure mode로 식별됨 |
| **Sequential evidence accumulation 방향** | h_t carry-over가 탐지에 필요하다는 방향 (Loop-01 간접 확인) |
| **CUSUM이 text-env에서 meaningful baseline임** | F1=0.237 (12-step, oracle-free) — 약하지만 작동함 |
| **Data leakage PASS** | oracle-free v0_5 eval에서 FORBIDDEN_AGENT_FIELDS 위반 없음 |
| **LFD AUROC 우위 가능성** | 0.842 vs 0.692 — origin 불명이지만 가능성은 있음 |

### 죽은 것 (DEAD / REJECT)

| 항목 | 근거 |
|---|---|
| **C3 proxy artifact** | proxy OFF → F1=0.000. 학습된 signal 없음 (Loop-01) |
| **C2 separability claim** | v0_4 single-regime episode 구조 → C2=0.0 구조적 불가능 (Loop-03) |
| **C6 14.9× advantage** | self-report 분모 artifact. fair compute 기준 2.0× (Loop-06) |
| **task_success as primary metric** | C4=0.994~0.998 ceiling. 모든 에이전트가 같음 — 비교 불가 |
| **"detection_delay=0 = 빠른 탐지"** | alarm bias. FAR=38%이기 때문에 delay=0 (alarm bias) |
| **"LFD 성공" 표현** | train_loss 비감소. AUROC 우위 origin 불명 |
| **fair_ppc claim** | mathematical-validity-critic 무효 판정 (progress proxy 자의적) |

### 애매한 것 (UNCERTAIN — 실험 필요)

| 항목 | 불확실성 이유 |
|---|---|
| **AUROC 우위 origin** | random-weight probe 없이는 학습 기여인지 feature artifact인지 불명 |
| **Calibration 후 F1** | threshold=0.5 고정 기준 F1 열세 → validation-derived threshold로 개선 가능한가 |
| **v0_6 일반화** | 2 grammar pair → real Web/GUI(수십 pair, noisy, long-horizon)로의 gap 미검증 |
| **Grammar-conditioned vs generic CPD** | NN-CUSUM baseline 없이 LFD가 정말 grammar 정보를 활용하는지 불명 |

---

## §7. 데이터셋과 환경의 문제

### v0_4의 구조적 한계

v0_4 환경은 episode당 regime이 고정이었다. 즉 한 episode 안에서 "검색창 모드"면 처음부터 끝까지 검색창 모드다.

이것이 왜 문제인가? 논문의 핵심 claim은 "에이전트가 regime이 바뀌었는데도 계속 틀린 가설을 사용한다"는 것이다. 그런데 regime이 바뀌지 않는 환경에서는 이 현상을 측정할 수 없다.

- `hidden_regime=family` 고정 → 단일 regime episodes
- regime_shift_f1=0 구조적 불가능 (변화가 없으니 탐지할 것도 없음)
- HistoryEncoder h0=None으로 매 episode 초기화 → sequential evidence 누적 불가
- gate가 열리지 않음 → planning signal 학습 불가

C2 (regime separability)=0은 데이터 자체의 문제였다.

### v0_5의 설계와 한계

v0_5는 이 문제를 해결하려 했다. 핵심 변경:
- episode 내 grammar switch 도입 (switch_step ∈ [2, max_steps-2])
- 공유 action-set vocabulary (두 grammar가 같은 action space 사용 → 진정한 "틀린 가설" 가능)
- `collect_episode()`가 switch 처리 가능하도록 수정 (TASK_COLLECTOR_V05_SWITCH)

그런데 현재 v0_5는 **2개의 grammar pair만** 사용한다.
- `search_form` ↔ `required_dropdown`

이것이 FATAL 공격의 원인이다. reviewer의 공격: "2개 grammar pair 장난감 환경에서 나온 결과가 실제 Web/GUI와 무슨 관계가 있나?"

추가 한계:
- max_steps=12 (매우 짧은 에피소드)
- n_stable_episodes=0 (FAR 계산의 negative class 오염)
- 250 episodes → 50 eval episodes (통계적 검증 불충분)
- train_loss 비감소 (15 epochs 동안 ~1.53 유지 — 학습 실패)
- post_switch_wrong_rate=14.73% (낮음 — switch 후에도 잘 맞춤)

### v0_6이 필요한 이유

v0_6은 다음을 목표로 해야 한다.
- k ≥ 4 grammar pair (실질적 diversity)
- 더 긴 episode (max_steps ≥ 30)
- stable episodes 포함 (FAR negative class 복원)
- noisy effects 추가 (delayed/partial observation)
- N ≥ 1000 episodes

v0_6 실험 없이는 "LFD shows promise"조차 paper에 쓸 수 없다.

### GUI 환경이 아직 primary가 아닌 이유

GUI screenshot은 픽셀 노이즈가 많고, 에피소드가 길고, action space가 넓다. 현재 실험은 text-only 환경에서 이루어지고 있다. GUI는 실험 로드맵의 P5(frozen VLM MVE) 단계에 해당하며, P3(text-only model)의 gate가 먼저 통과되어야 한다.

---

## §8. 모델 아키텍처 쉬운 설명

### 전체 정보 흐름

```
공개 관찰 (x_t) — 화면 텍스트, 이전 행동, 관찰된 효과 등
    │
    ▼
TextStateEncoder  →  현재 상태 임베딩
    │
    ▼
HistoryEncoder (h_t) ← 이전 step의 h_{t-1} carry-over
    │
    ▼
LatentPosterior  →  4개 latent 분포
    │    ├─ z_state    (UI 상태)
    │    ├─ z_regime   (interaction mode)
    │    ├─ z_control_grammar  (행동 패턴 규칙)
    │    └─ z_change_point    (이벤트 유형)
    │
    ▼
FalsificationDetectorHead  →  F_t 계산
    │    ├─ effect_scalar     (action-outcome mismatch)
    │    ├─ run_length_head   (BOCPD posterior)
    │    ├─ cusum_head        (누적 통계)
    │    └─ wrong_prob_head   (learned P(wrong | history))
    │
    ▼
DecisionGate  →  G_t 계산 (4-condition hybrid)
    │
    ├─ G_t = 0 → base action (compute 절약)
    │
    └─ G_t = 1 → planning 실행
         │
         ├─ AlternativeHypothesisProposer  →  대안 가설 목록
         ├─ ShortHorizonRollout (H=1~3 steps)
         └─ RewriteModule  →  intent → executable action (grammar-conditioned)
```

### HistoryEncoder의 h_t 왜 중요한가

h_0=None (매 episode 초기화)이면 어떤 일이 생기는가? 에이전트는 직전 step의 action-effect 기억을 갖고 있지 않다. "어제 브레이크를 밟았는데 차가 멈추지 않았다"는 기억 없이 오늘 또 브레이크를 밟는다.

sequential evidence accumulation은 **h_t carry-over 없이는 불가능**하다. v0_4의 핵심 결함 중 하나가 이것이었다. stateless GRU로는 5 step 동안 같은 패턴의 실패가 반복됐다는 사실을 기억할 수 없다.

### FalsificationDetectorHead: 세부 설명

```python
class FalsificationDetectorHead:
    # 입력: history encoding h_t, action-effect summary e_t
    # 출력: wrong_prob_head → P(wrong|h_t) [0,1]
    #        run_length_head → BOCPD posterior mass distribution
    #        cusum_head → cumulative sum statistic
    #        effect_scalar → per-step mismatch score
```

- `effect_scalar`: 이번 step의 행동 결과가 기대와 얼마나 다른지
- `cusum_head`: effect_scalar를 누적해 통계적 threshold 초과 감지
- `run_length_head`: 현재 상태가 "틀린 상태"로 얼마나 오래됐는지의 posterior
- `wrong_prob_head`: 4개 신호를 종합해 최종 P(wrong) 출력

---

## §9. Loss 설계 쉬운 설명

### 12개 Loss의 목적

| Loss | 무엇을 학습하는가 | 비고 |
|---|---|---|
| L_action_effect | action → effect type (7종) 예측 | 기본 환경 이해 |
| L_regime | 현재 어떤 task family (8종)인가 | 상황 파악 |
| L_control_grammar | 현재 어떤 grammar (8종)인가 | 행동 규칙 파악 |
| L_falsification | deterministic F_t가 true_wrong_hypothesis를 예측 | 구식 signal, proxy 연결 |
| **L_seq_falsification** | **LFD head의 wrong_prob_learned가 true_wrong_hypothesis 예측** | **신규 핵심** |
| **L_run_length_posterior** | **BOCPD posterior가 wrong/stable 상황에 mass 배분** | **신규 핵심** |
| L_temporal_consistency | posterior entropy가 이유 없이 급변하지 않도록 | 안정화 |
| L_progress | action → progress delta 회귀 | 목표 진행도 |
| L_change_point | change point 유형 (12종) 분류 | 이벤트 탐지 |
| L_reveal_shift | reveal/shift/none 3-way 분류 | 변화 유형 |
| L_failed_action | action이 실패했는지 BCE | 단순 실패 감지 |
| L_intent_action_mapping | intent → executable action 변환 | **현재 zero placeholder** |

### L_temporal_consistency: 실제로는 zero()

구현 코드에서 `L_temporal_consistency`는 `torch.tensor(0.0)`을 반환하는 placeholder였다. 설계 의도는 있었지만 아직 구현되지 않았다.

### L_falsification vs L_seq_falsification: gradient conflict 위험

두 loss가 `true_wrong_hypothesis`라는 같은 label을 supervision target으로 사용한다. 그런데 예측하는 신호가 다르다.

- `L_falsification`: 결정론적 F_t (proxy-based) → label
- `L_seq_falsification`: 학습된 wrong_prob → label

둘이 함께 학습되면 gradient 방향이 충돌할 수 있다. 설계 권고: LFD 학습 시에는 `L_falsification weight=0`, `L_seq_falsification`만 사용.

### Train Loss 비감소 문제

Phase 9 실험에서 train_loss가 15 epochs 동안 ~1.53에서 진동했다. log(2)=0.693보다 훨씬 높다. 이것이 "학습 실패"를 의미하는가?

단순 비교는 위험하다. train_loss는 `L_seq_falsification + L_run_length_posterior`의 합이므로 random baseline이 무엇인지 각 항 분리 측정이 필요하다. 하지만 분명한 것은 15 epochs 동안 **단조 감소 없이** 진동했다는 사실이다.

AUROC=0.842가 나오는 이유가 학습 때문인지, feature encoding의 grammar-switch signal이 implicit하게 포함됐기 때문인지 현재로선 알 수 없다 (FAIL-016).

---

## §10. CUSUM과 내 주장 사이의 관계

### CUSUM은 무엇인가

CUSUM(Cumulative Sum, Page 1954)은 다음과 같이 작동한다.

```
S_t = max(0, S_{t-1} + (x_t - k))
alarm if S_t > h
```

- `x_t`: 매 step의 신호 (여기서는 action-effect log-likelihood ratio)
- `k`: slack parameter (0.3 사용) — 정상 범위 내 변동 흡수
- `h`: threshold (2.0이 optimal) — alarm 임계값

누적 합이 threshold를 넘으면 "변화점이 있었다"고 선언한다. 단순하지만 강력하다.

### 현재 실험에서 CUSUM이 이기는 이유

oracle-free v0_5 실험 (N=50 eval):
- CUSUM F1=0.237 vs LFD F1=0.178 → CUSUM 우위
- CUSUM FAR=0.086 vs LFD FAR=0.382 → CUSUM 압도적 우위

CUSUM이 F1에서 이기는 이유는 **12-step 짧은 에피소드에서의 threshold 최적화**다. h=2.0은 12 step 이내에 alarm을 내면서도 FAR을 낮게 유지하는 sweet spot이다. LFD는 threshold=0.5로 고정됐고, alarm bias 상태에서 FAR이 과도하게 높았다.

### LFD가 CUSUM을 이기려면

이론적 우위는 있다. grammar-conditioned signal은 "단순히 신호가 급변했다"가 아니라 "이 grammar 아래에서의 expected effect와 observed effect의 괴리"를 계산할 수 있다. 이는 generic changepoint detector가 갖지 못하는 구조적 이점이다.

이 이점을 **실제로 보이려면** 다음이 필요하다.
1. **Random-weight LFD probe**: 학습 전 랜덤 초기화 LFD의 AUROC와 비교 → 학습 기여 분리
2. **NN-CUSUM baseline** (2210.17312): 뉴럴넷 기반 CUSUM과 비교 → "뉴럴넷이면 다 좋아지는 것"이 아님을 보여야 함
3. **Grammar conditioning ablation**: grammar signal 없는 LFD vs grammar signal 있는 LFD
4. **N ≥ 1000 에피소드 + bootstrap CI**: 통계적 유의성

### CUSUM을 못 이길 때의 Pivot 옵션

만약 LFD가 CUSUM을 통계적으로 유의하게 능가하지 못한다면, 다음 3가지 pivot을 고려할 수 있다.

**Pivot A**: CUSUM 기반 게이트를 "falsification proxy"로 수용하고, 대신 **alternative hypothesis proposal + action rewrite**의 품질로 차별화.
→ "탐지는 CUSUM, 그 이후(대안 가설 생성, 행동 재작성)가 novelty"

**Pivot B**: grammar-conditioned CUSUM으로 재구성.
→ 일반 CUSUM이 아닌, effect likelihood가 grammar-conditioned인 CUSUM

**Pivot C**: 탐지 정확도가 아닌 **recovery quality(틀린 가설 이후 얼마나 빨리 올바른 행동으로 복구하는가)**로 claim 전환.
→ detection F1이 아닌 MET-PERSIST-001 (persistence time) 중심

---

## §11. Phase 9 결과 해석

### Oracle-Free v0_5 수치 재해석

| Metric | CUSUM (h=2.0) | LFD mean±std | 해석 |
|---|---|---|---|
| AUROC | 0.692 | **0.842 ± 0.003** | LFD ranking 능력 우위. 그러나 origin 불명 |
| AUPRC | 0.479 | **0.707 ± 0.012** | threshold 최적화 여지 있음. 단 negative class 오염 |
| F1 | **0.237** | 0.178 ± 0.000 | threshold 고정 기준 CUSUM 우위. 양쪽 낮음 |
| FAR/step | **0.086** | 0.382 ± 0.127 | LFD 4.4배 불리. 운영 불가 |
| detection_delay | 0.231 | 0.000 ± 0.000 | LFD의 delay=0은 빠른 탐지가 아니라 alarm bias |
| train_loss | N/A | 1.53 (비감소) | 학습 자체가 제대로 됐는지 의문 |

### Alarm Bias란 무엇인가

`detection_delay=0.000`을 보고 "LFD가 grammar switch를 즉각 감지한다!"라고 해석하면 안 된다. FAR=38.2%와 함께 보면 의미가 달라진다.

FAR=38%는 switch가 없는 step에서도 매 2.6 step마다 alarm을 낸다는 뜻이다. 이렇게 많은 alarm을 내면 switch 직후에도 alarm을 내게 되고, 그래서 detection_delay가 0으로 보이는 것이다. 이는 **alarm bias**이지 빠른 탐지가 아니다.

비유: 불이 날 때 즉각 경보를 울리는 화재 감지기가 있다. 그런데 이 감지기는 불이 없는 상황에서도 매 3초마다 경보를 울린다. 이 감지기가 "반응이 빠르다"고 할 수 없다.

### Train Loss 비감소: 의미와 한계

LFD train_loss가 3 seed 모두 ~1.53에서 진동했다. 이것은 세 가지를 의미할 수 있다.

1. 모델이 signal에서 유용한 패턴을 학습하지 못했다 (학습 실패)
2. loss 항의 scale이 맞지 않아 gradient가 서로 상쇄된다
3. 15 epoch이 수렴에 부족하다

세 번째 가능성도 배제하기 어렵지만, AUROC=0.842가 나왔다는 사실과 train_loss 비감소가 공존한다는 것이 이상하다. 이것이 FAIL-016 공격의 핵심: "학습이 안 됐는데 AUROC가 좋다 → 학습이 아닌 feature 자체가 signal을 갖고 있는 것 아닌가?"

### Critic들이 왜 보수적 판정을 했는가

세 가지 이유로 요약된다.

1. **FAIL-016**: AUROC 우위의 origin이 불명확하다. random-weight probe 실험 없이는 학습 기여를 증명할 수 없다.
2. **FAIL-018**: 2 grammar pair, 12 steps, perfect discrete effects → real Web/GUI와 범주적 차이가 있다. "shows promise in oracle-free conditions"조차 caveat 없이는 쓸 수 없다.
3. **수치의 의미**: detection_delay=0은 alarm bias, fair_ppc는 계산 무효, F1은 CUSUM 열세. AUROC만 우위인 상황에서 "LFD가 낫다"고 말하기 어렵다.

---

## §12. Novelty 관점에서 무엇이 남았는가

### 직접 위협 논문들

이 연구의 핵심 기여를 공격할 수 있는 논문들을 솔직하게 정리한다.

| 논문 | 어디서 겹치는가 | 방어 방법 |
|---|---|---|
| **WebWorld** (2602.14721) | generic web world model, 1M+ interactions | FRCG는 generic simulation이 아니라 wrong-control-grammar persistence + falsification-guided rewrite |
| **CUWM** (2602.17365) | frozen agent + world model으로 action simulate/compare | FRCG는 action search가 아니라 **regime/control-grammar hypothesis search** |
| **WAC** (2602.15384) | consequence simulation + action correction | FRCG는 grammar-conditioned rewrite + falsification score |
| **VeriGUI** (2604.05477) | action-effect verification + self-correction | FRCG는 verification-only가 아니라 current vs alt grammar likelihood + rewrite |
| **R-BOCPD** (2304.00232) | run_length_head ≅ BOCPD posterior | grammar-conditioned + planning gate + rewrite까지 포함된 시스템 |
| **NN-CUSUM** (2210.17312) | cusum_head + CUSUM 비교 구조 | NN-CUSUM baseline 추가 없이는 "약한 baseline 비교" 공격 불가피 |
| **E-valuator** (2512.03109) | sequential hypothesis testing + agent failure | related work에 추가 + differentiation |

### 차별화 포인트: 무엇이 진짜 contribution인가

generic CPD(CUSUM, BOCPD, NN-CUSUM)와 이 논문의 차이는 네 가지다.

1. **Grammar-conditioned signal**: effect likelihood가 current grammar 아래의 expected effect와 비교됨 (generic CPD는 signal 자체의 변화만 봄)
2. **Persistence metric**: 탐지 정확도가 아니라 wrong-hypothesis가 지속되는 시간(MET-PERSIST-001)을 primary metric으로 사용
3. **Planning gate**: 탐지 이후 alternative hypothesis proposal + compute gate
4. **Action-interface rewrite**: grammar switch 결정 후 base action을 새 grammar에 맞게 다시 씀

이 네 가지 중 **1번(grammar-conditioned signal)**이 가장 중요하며, 이것이 실험으로 검증되지 않은 상태다. random-weight probe와 NN-CUSUM 비교가 이 contribution의 생사를 결정한다.

### 반드시 보여야 하는 실험

1. **CUSUM 능가 영역 탐색**: 어떤 조건(episode 길이, grammar 다양성, noise level)에서 LFD가 CUSUM을 이기는가
2. **Random-weight LFD probe**: 학습 전/후 AUROC 비교 → 학습 기여 정량화
3. **Grammar conditioning ablation**: grammar signal 없는 LFD와 비교
4. **NN-CUSUM baseline** (2210.17312): NN 자체의 효과 분리
5. **v0_6 데이터**: k ≥ 4 grammar, longer episodes → 일반화 가능성

---

## §13. 실세계 적용성 관점에서 무엇이 부족한가

### 현재 v0_5의 한계

솔직하게 나열하면:

- **2개 grammar pair**: `search_form` ↔ `required_dropdown`. 실제 웹 환경에는 수십 가지 interaction pattern이 있다.
- **12 step 에피소드**: 실제 웹 task는 수십~수백 step이다.
- **Perfect discrete effects**: v0_5는 grammar switch가 발생하면 effect_type이 명확하게 바뀐다. 실제 환경에서는 noisy DOM, partial loading, JavaScript 렌더링 지연 등으로 effect 신호가 불명확하다.
- **No partial observability**: 에이전트는 모든 텍스트 정보를 볼 수 있다. 실제 GUI에서는 스크롤 아래 요소나 hidden overlay를 볼 수 없다.
- **Synthetic data**: 실제 사용자 행동이 아닌 프로그래밍된 trajectory.

### GUI로 넘어가려면

P5(frozen VLM MVE) 단계에서 GUI를 다루게 된다. 이를 위해 필요한 것:

- VLM(Vision Language Model)이 screenshot에서 action-effect evidence를 추출하는 능력
- 스크린샷 노이즈에 robust한 effect_scalar 계산
- Longer-horizon episode에서 h_t carry-over의 메모리 관리
- 실제 웹 환경 collector (현재 collector가 GUI switch를 처리하지 못함)

### 실세계 적용의 최소 조건

어느 수준이 돼야 "real Web/GUI에서 의미 있다"고 말할 수 있는가?

1. k ≥ 10개 grammar pair (다양성)
2. noisy trajectory에서 탐지 성능 유지 (robust signal)
3. partial observability 환경에서 작동 (관찰 불완전성)
4. 100+ step long horizon에서 persistence metric 측정 가능
5. 계산 비용이 real-time에 가까운 수준 (gate가 너무 자주 열리면 안 됨)

현재 v0_5는 이 기준을 충족하지 못한다. 이것이 "실세계에 적용 가능하다"고 절대 쓰면 안 되는 이유다.

---

## §14. 지금 당장 다음 스텝 후보

| 옵션 | 설명 | 장점 | 위험 | 필요 실험 |
|---|---|---|---|---|
| **A. LFD 계속 개선** | random-weight probe, CI, calibration, N=1000, v0_6 | AUROC 우위 가능성 확인 | 학습 실패가 구조적 문제일 수 있음. 오래 걸림 | random-weight probe 1개 실험이 먼저 필요 |
| **B. CUSUM-gate pivot** | LFD 포기, grammar-conditioned CUSUM으로 계획 | 즉시 작동하는 baseline 존재 | "novelty가 없다" 위험. NN-CUSUM 이미 존재 | grammar conditioning의 효과를 ablation으로 보여야 함 |
| **C. 데이터셋 우선** | v0_6 설계, k≥4 grammar, recovery trajectory 포함 | 실험 기반 강화 | 구현 시간 필요. v0_6 완성 전에는 아무것도 주장 불가 | v0_6 collector 구현 (현재 미완성) |
| **D. Claim 축소** | "heuristic gate + compute allocation paper"로 범위 축소 | 실현 가능성 높음 | 논문의 독특성 약화. FRCG-WM 고유 contribution 감소 | 기존 결과 재해석만 필요 |

### 가장 빠른 pivoting 경로

만약 시간이 부족하다면 **A의 random-weight probe 하나**가 가장 중요하다.

학습 전 랜덤 초기화 LFD로 AUROC를 측정한다. 만약 random-weight AUROC가 0.84에 가깝다면 → 학습 기여 없음 → B 또는 D로 즉시 pivot. 만약 random-weight AUROC가 낮다면 → 학습이 기여하고 있음 → A 계속.

이 하나의 실험이 전략을 결정한다.

### 반드시 함께 해야 하는 것

어떤 옵션을 선택하든:
1. **n_stable_episodes > 0** 데이터 추가 (FAR 계산 정상화)
2. **bootstrap CI** 계산 (통계적 유의성)
3. **NN-CUSUM baseline** (2210.17312) 구현
4. **alarm bias 표현** 수정 (detection_delay=0은 빠른 탐지가 아님)

---

## §15. 최종 요약

**현재 아이디어는 죽지 않았다.**

wrong-control-grammar hypothesis persistence는 독립적인 failure mode이고, sequential evidence accumulation이 탐지에 필요하다는 방향은 맞다. CUSUM이 12-step 텍스트 환경에서 meaningful baseline으로 작동한다는 것도 확인됐다.

**하지만 기존 구현은 잘못된 방향이었다.**

v0_4의 C3 회복은 proxy artifact였다. C2 separability는 데이터 구조의 문제로 측정 불가능했다. C6 14.9× advantage는 self-report 분모 artifact였다. 이 세 가지는 논문에 쓸 수 없다.

**CUSUM이 아직 이기고 있다, 하지만 AUROC 가능성은 있다.**

oracle-free v0_5에서 LFD AUROC=0.842 vs CUSUM=0.692 (+0.150). 그런데 이 우위가 학습 기여인지, feature 구조 artifact인지 현재로선 알 수 없다. F1에서는 CUSUM이 이기고, FAR은 4.4배 불리하다.

**다음에 해야 할 것은 "무엇을 주장할 것인가"부터 다시 정하는 것이다.**

random-weight probe 하나로 AUROC 우위의 origin을 확인한다. 그 결과에 따라 A(LFD 계속 개선), B(CUSUM-gate pivot), C(v0_6 데이터 우선), D(claim 축소) 중 하나를 선택한다. 데이터 없이 "LFD가 성공했다"거나 "실세계에 적용 가능하다"는 표현은 쓰지 않는다.

**현재 확인된 가장 중요한 사실들**:
- wrong-hypothesis persistence는 진짜 문제다
- sequential accumulation 방향은 맞다
- grammar-conditioned signal이 generic CPD보다 낫다는 것은 아직 미증명
- v0_6 없이는 ICLR 제출 불가

---

## 부록: 주요 수치 참조표

| 실험 | 지표 | 값 | 상태 |
|---|---|---|---|
| STEP 8 v0_4 | C3 F1 (degenerate) | 0.000 | DEAD |
| STEP 9 (proxy ON) | C3 F1 | 0.539 ± 0.075 | DEAD (proxy artifact) |
| Loop-01 | C3 F1 proxy OFF | **0.000** | DEAD (확인) |
| Loop-02 | C3 F1 5-seed mean | 0.527 ± 0.075 | DEAD (proxy artifact) |
| Loop-06 | C6 advantage (fair) | **2.0×** | ALIVE (boundary) |
| Loop-06 | C6 advantage (self-report) | 14.9× | DEAD (artifact) |
| Phase 9 oracle-probe | LFD AUROC | 0.947 ± 0.004 | UNCERTAIN (oracle) |
| Phase 9 oracle-probe | CUSUM F1 | 0.635 | REFERENCE |
| Phase 9 oracle-free | LFD AUROC | **0.842 ± 0.003** | UNCERTAIN (origin) |
| Phase 9 oracle-free | CUSUM AUROC | 0.692 | REFERENCE |
| Phase 9 oracle-free | LFD F1 | 0.178 | CUSUM 열세 |
| Phase 9 oracle-free | LFD FAR | 0.382 | NOT DEPLOYABLE |
| Phase 9 oracle-free | LFD train_loss | 1.53 (비감소) | LEARNING FAILURE |

---

*이 문서는 실험 결과 보고서가 아닌 개념 이해용 해설서입니다. 수치는 각 실험 report에서 확인된 값만 사용했으며, 과장이나 숨김 없이 있는 그대로를 기록했습니다.*
