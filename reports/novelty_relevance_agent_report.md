# novelty-relevance-critic 보고서 — Step 11-D7 Pilot (90ep)

**보고일**: 2026-05-23
**단계**: Pilot Stage 1 (실측, Post-Pilot)
**판정**: CONDITIONAL_PASS

---

## FGLC novelty 관련 6개 질문 답변

### Q1. mass/friction shift가 단순 noise가 아닌 physical dynamics hypothesis shift인가?

**답변: YES (PASS)**

- mass 1.5kg (default 1.0kg의 1.5배): 관성 증가 → 동일 force에서 가속도 감소 → trajectory 패턴 변화.
- friction=5.0 (joint dry friction 증가): 관절 운동 억제 → end-effector 궤적 감쇠.
- 두 shift 모두 observation-only(state vector)에서 감지 가능하며, random noise와 달리 **지속적(persistent)** 방향 편향을 유발함.
- dataset_stats 실측: friction 축에서 state_delta_norm 0.14 감소, 일부 state_std 차원 20% 이상 감소 → 신호 구조 변화 확인.

### Q2. base WM 1-step prediction이 ID에서 적합, OOD에서 mismatch가 누적되는가?

**답변: CONDITIONAL (더 많은 epoch 필요)**

- R3 smoke 5 epoch 결과: id_nll=0.8726, ood_mass_nll=0.8730, ood_friction_nll=0.8704.
- ood_id_nll_diff=-0.0009 — 아직 ID/OOD 구분 없음. 이는 5 epoch 초기 학습으로 NLL이 수렴 전임을 반영.
- 충분한 epoch(예: 50~100)에서 ID NLL이 낮아지고 OOD NLL이 높게 유지되어야 mismatch 누적 관찰 가능.
- 데이터 구조(friction gap 0.14, state distribution 변화)는 OOD mismatch 발생을 지지함.

### Q3. falsification gate(β_t)가 residual 차이를 감지할 가능성이 보이는가?

**답변: LIKELY (CONDITIONAL PASS)**

- ρ_t = Σ_t^{-1/2}(z_{t+1} − μ_t): friction 축에서 state_delta_norm이 0.14 감소 → standardized residual 패턴 변화 예상.
- mass 축(gap 0.0148)은 소폭이나 systematic bias로 β_t 감지 가능성 있음.
- probe(2026-05-23): L2 diff ~0.042/step (friction 축) 확인 기록.
- β_t 신뢰도는 R4 conformal calibration 단계에서 검증 필요.

### Q4. latent correction(δ_t^k)이 필요한 group-wise 구조 차이가 관찰되는가?

**답변: PARTIAL (CONDITIONAL PASS)**

- friction 축: state_std 감소가 특정 차원군(인덱스 12~15 관절 속도 차원)에 집중 → K-group 분해 가능성 지지.
- mass 축: 전반적 소폭 변화 → group-wise 구조 파악 위해 더 많은 데이터 필요.
- latent group K=6, d=32 설계로 관절-엔드이펙터-그립퍼 서브스페이스 분리 가능성 있음.

### Q5. mass/friction shift가 action/value에 영향을 주는가?

**답변: PARTIAL (실측)**

| Split | reward_mean | episode_length_mean |
|---|---|---|
| train_id | 0.0465 | 50.0 |
| ood_mass_low | 0.0606 | 50.0 |
| ood_friction_low | 0.0494 | 50.0 |

- success rate는 모든 split 0% (random policy 한계), episode_length는 50으로 고정 (max_steps 도달).
- reward_mean에서 ood_mass_low가 train_id보다 소폭 높음(0.061 vs 0.047) — mass 변화로 인한 contact pattern 차이 가능.
- Scaled 단계와 더 긴 학습으로 value 차이를 통계적으로 검증 필요.

### Q6. wrong-dynamics-hypothesis persistence 구간이 multi-step에 걸쳐 존재하는가?

**답변: UNVERIFIED (Pilot 5 epoch으로 관찰 불가)**

- wrong-dynamics-hypothesis persistence는 base WM이 잘못된 dynamics를 인지하지 못하고 여러 step에 걸쳐 틀린 예측을 지속하는 구간.
- R3 smoke 5 epoch 현재 NLL 차이 없음 → persistence 구간 측정 불가.
- 필요 조건: NLL이 ID에서 충분히 낮아지고 OOD에서 유의미하게 높아진 후, multi-step rollout에서 error 누적 관찰.
- friction shift(0.14 state_delta gap)는 persistence 발생 가능성을 지지함.

## 판정 근거

**CONDITIONAL_PASS**: Q1(YES), Q3(LIKELY), Q5(PARTIAL)로 FGLC 데이터 구조 적합성 확인됨.
Q2·Q6은 Scaled 데이터 + 더 많은 epoch(50~100) 학습 후 재검증 필요.
Q4는 K-group ablation에서 검증 필요.

## 다음 단계 권고

1. Scaled 450ep + 50~100 epoch 학습: ID/OOD NLL gap 관찰.
2. K-group latent 분해 후 friction 차원에서의 group-wise residual 패턴 분석.
3. R4 falsification gate 단계에서 β_t 발화율 측정.
