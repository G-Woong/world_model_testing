# 08_ACTION_VALUE_RELEVANCE — Action/Value 관련성

## 출처
- main.md §10 (action/value 관련성)
- deep-research-report.md §Robust control·DRO·value-aware loss (R-8)

## 주장

Correction attention은 **action/value 관련성**으로 안내되어야 하며, 단순히 예측 오류만이 아닙니다.
World model은 planning에 영향을 미치지 않는 무관한 잠재 차원에서 높은 예측 오류를
가질 수 있습니다. 반대로, action 관련 하위공간의 작은 불일치가 return을 붕괴시킬 수 있습니다.
L_value와 cause_score 정렬이 correction이 value-aware하도록 보장합니다.

## 수학적 형식화

```
Value/보상 헤드:
  r̂_t = Rθ(flatten(z_t), a_t, h_t)
  Q̂_t = Qθ(flatten(z_t), a_t, h_t)

그룹 k별 action 관련성:
  (a) Value 민감도:  A_k = |V(z̃_t^{(k)}) - V(z_t)|
  (b) 정책 KL 발산: P_k = D_KL(π(·|z̃_t^{(k)}) || π(·|z_t))

Cause score (attention의 의사 타겟):
  cause_score_k = standardized_mismatch_k × action_relevance_k × temporal_consistency_k

Attention 정렬 손실:
  L_attn_align = KL(stopgrad(normalize(cause_score)) || α_t)
  주의: cause_score는 의사 타겟이며, ground truth가 아님

Value 일관성 손실 (n-step TD):
  G_t = r_t + γ r_{t+1} + ... + γ^n V(z_{t+n})
  L_value = ||V(z̃_t) - G_t||²
```

**왜 value-aware인가?** L_value 없이는, correction이 planning 성능 희생으로
예측 정확도를 최대화합니다. 특정 태스크+상태 조합에서 실제 마찰 = 0.5일 때
"마찰 = 1.0"으로 예측하는 모델은 높은 예측 NLL을 보일 것입니다 —
하지만 이것이 최적 action을 변경하지 않을 수 있습니다.
L_value는 correction이 제어에 중요하도록 강제합니다.

## 연결 맵
- 상위: M-7 (불일치 점수), M-9 (α_t), M-10 (correction δ_t)
- 하위: M-13..M-15 (nec/suf/contrast), M-16 (전체 손실)
- 알고리즘: R-8 (robust control value-aware 손실), R-9 (CIRCA -ξ·ΔQ_robust 항)

## 체크포인트

- C1 수학적 유효성: CONDITIONAL — cause_score는 의사 타겟 (ground truth 아님).
  cause_score = mismatch × action_relevance × temporal_consistency라는 주장은
  경험적으로 동기화된 공식이며, 제1원리에서 도출 불가능합니다.
- C2 신규성: CONDITIONAL — Value-aware world model correction은 선례 있음 (TD-MPC2).
  새로운 조합: value 가이드 attention 선택 + 그룹 수준 correction.
- C3 Reviewer 공격: 중간 — "왜 WM 없이 직접 return을 최대화하지 않는가?"
  답변: WM은 이동 하에서 멀티 스텝 planning을 가능하게 함; 직접 정책 기울기는 OOD 일반화가 안 됨.
- C4 타당성: PASS — Q 민감도 계산은 순방향 패스; KL 발산은 표준.
- C5 Claim-지표: 필수: L_value ablation (no-value)이 NLL이 아닌 return을 저하시키는 것 보여야 함.
  이는 value-aware 선택이 순수 예측 correction 이상을 추가함을 보여줍니다.
- C6 구현 위험: 낮음 — 표준 TD 손실; Q-헤드는 작은 MLP.
- C7 실험 설계: 필수 ablation: no-value (L_value = 0).
  가설: L_value 없이, 예측 NLL이 개선되지만 return이 저하됩니다.
- C8 실패 해석: no-value ablation이 return에서 FGLC와 동등하면: value-aware correction이
  순수 예측 correction 이상을 추가하지 않습니다. 의미: 주장을 "예측 복구"로 축소.
- C9 관련 연구: TD-MPC2 (value-aware 잠재 planning), DRO 문헌 — 대기 중 ≥2 출처
- C10 컨텍스트 라우팅: 출처 = main.md §10. 하위: 09_NECESSITY_SUFFICIENCY.md, 10_LOSS_DESIGN.md
