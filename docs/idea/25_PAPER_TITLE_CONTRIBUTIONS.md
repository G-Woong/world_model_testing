# 25_PAPER_TITLE_CONTRIBUTIONS — 논문 제목 및 기여사항

## 출처
- main.md §24 (제목 후보), §마지막 핵심 정리

## 제목 후보

**주요 (권장)**:
> Falsification-Guided Latent Correction for World Model Planning under Physical Distribution Shift
> (물리적 분포 이동 하에서 World Model Planning을 위한 Falsification 유도 잠재 보정)

**대안 A** (짧게):
> Action-Relevant Falsification in Latent World Models
> (잠재 World Model에서의 Action 관련 Falsification)

**대안 B** (알고리즘 강조):
> CIRCA: Causal Intervention Randomized Conformal Attention for World Model Correction
> (World Model 보정을 위한 인과 개입 무작위 Conformal Attention)

**결정**: 주요 제목을 제출에 사용. 기여가 CIRCA만으로 축소되면 대안 B.

## 5가지 기여 사항

1. **Falsification 유도 보정 프레임워크**: 잠재 world model의 예측 분포가 관측 전이와
   통계적으로 불일치(falsification 이벤트)할 때를 감지하고 표적 sparse residual correction을
   적용하는 원칙적 프레임워크.

2. **보정된 falsification gate**: 보류된 ID 궤적의 경험적 분위수 보정으로 유한 샘플
   오탐율 제어를 제공하며, 하드 임계값 이상 탐지와 수학적으로 구별 가능한 통계적으로
   보정된 gate β_t.

3. **개입 정책 attention**: Necessity/sufficiency 손실 + τ_g 무작위화된 개입으로
   개입 정책으로 검증된 그룹 수준 sparse attention 메커니즘 α_t.
   Attention-as-explanation 비판을 다루며 단순한 attention 시각화가 아닌.

4. **4가지 알고리즘 벤치마크**: 개입 유효성/보정/계산 효율성 공간에서 서로 다른 지점을
   커버하는 CIRCA, ASAP, I3G, IVI의 체계적 비교로, 실무자에게 알고리즘 선택 지침 제공.

5. **경험적 평가**: 4축 지표(예측/탐지/귀인/제어)를 사용하여 OOD return 및 회복 시간에서
   TD-MPC2/DreamerV3/HiP-RSSM을 능가하고 계산 효율성을 유지함을 보여주는 ManiSkill
   제어된 물리적 dynamics 이동 벤치마크 (OOD 축: mass/friction/latency/noise/action-gain).

## 초록 초안 (v0.1)

```
잠재 world model은 물리적 dynamics가 이동할 때 조용히 성능이 저하됩니다 —
우리는 이것을 잘못된 dynamics 가설의 지속이라고 부릅니다.
우리는 FGLC(Falsification-Guided Latent Correction)를 소개합니다.
이 프레임워크는 (1) 보정된 표준화된 예측 불일치를 통해 dynamics 가설 위반을 감지하고,
(2) 개입 검증된 sparse attention 메커니즘을 통해 어떤 그룹화된 잠재 하위공간이
planning 실패를 유발하는지 식별하며, (3) 해당 하위공간에 경계가 있는 residual correction을
적용합니다. 우리는 necessity, sufficiency, counterfactual rollout 손실을 통해 correction을
검증하여 sparse attention 마스크가 단순한 attention 시각화가 아닌 효과적인 개입 정책임을
보장합니다. 우리는 FGLC를 개입 유효성/보정/계산 트레이드오프가 다른 네 가지 알고리즘
(CIRCA, ASAP, I3G, IVI)으로 인스턴스화하고 ManiSkill 조작 태스크에서 제어된 질량, 마찰,
지연, 노이즈, 액션-게인 이동 하에서 평가합니다. FGLC는 OOD 조건에서 TD-MPC2 대비
[X]% 높은 return과 [Y]× 빠른 회복을 달성합니다.
[자리 표시자: X와 Y는 실제 실험 결과가 필요합니다]
```

## 직접 위협에 대한 포지셔닝

| 위협 | 우리의 포지셔닝 |
|---|---|
| TD-MPC2 | Falsification 탐지와 표적 보정으로 TD-MPC2 확장 |
| DreamerV3 | 동일한 OOD 문제지만 decoder-free, 보정 메커니즘 없음 |
| HiP-RSSM | 명시적 파라미터 추론 없이 감지하고 보정 |
| PLSM | PLSM은 학습 시 action 효과 개선; FGLC는 추론 시 실패 보정 |
| ReDRAW/AdaWM | FGLC는 causal attention + necessity/sufficiency 검증 추가 |

## 연결 맵
- 상위: 22_NOVELTY_AND_THREATS.md, 17_ALGORITHM_COMPARISON.md
- 하위: docs/ROADMAP/15_PHASE_R14_PAPER_FRAMING_AND_DRAFTING.md
