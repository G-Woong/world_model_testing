# 10_LOSS_DESIGN — 손실 함수 설계

## 출처
- main.md §12 (전체 손실), §13 (학습 단계)

## 주장

전체 FGLC 학습 목표는 10개 항을 가집니다. 이것들은 **단계적으로** 도입되어야 합니다:
Stage 1은 L_base+L_reward+L_value+L_calibration만 사용하고; Stage 2는 correction 항을 추가합니다.
모든 10개 항으로 처음부터 end-to-end 학습하면 실패합니다.

## 수학적 형식화

```
L_total =
    L_base_dynamics          [기본 WM: 1단계 예측의 NLL]
  + λ1 L_reward              [보상 헤드 정확도]
  + λ2 L_value               [가치 헤드 TD 일관성]
  + λ3 L_calibration         [σ 정규화: 붕괴 방지]
  + λ4 L_corrected_dynamics  [보정된 rollout NLL 개선]
  + λ5 L_sparse_attention    [α_t에 대한 엔트로피 페널티]
  + λ6 L_correction_size     [α_t^k · δ_t^k에 대한 L2 페널티]
  + λ7 L_temporal_consistency [α_t ≈ α_{t+1} 지속적 regime 하에서]
  + λ8 L_necessity           [max(0, margin - (L_without - L_with))]
  + λ9 L_sufficiency         [|L_selected - L_full|]
  + λ10 L_random_contrast    [max(0, margin - (L_random - L_selected))]

초기 λ 값:
  λ1=1.0, λ2=1.0, λ3=0.1 (sigma 정규화)
  λ4=1.0 (Stage 2+)
  λ5=0.01 (희소성), λ6=0.1 (크기), λ7=0.05 (시간)
  λ8=0.1 (필요성), λ9=0.1 (충분성), λ10=0.1 (대비)

단계별 활성화:
  Stage 1: L_base + λ1 L_reward + λ2 L_value + λ3 L_calibration
  Stage 2: + λ4 L_corrected_dynamics + λ5..λ10 correction 항
  Stage 3: planner 통합 (MPPI/CEM)
```

**왜 단계적인가?**
- 기본 dynamics와 correction이 동시에 학습되면, correction 모듈이 기울기를 "훔침"
- 기본 WM은 먼저 안정적인 H0 가설을 확립해야 함; correction은 그 후 H1로 작동
- 유사: base = 동결된 사전 분포; correction = 사후 업데이트

## 연결 맵
- 상위: M-6 (기본 dynamics), M-8 (correction을 위한 β_t), M-9 (α_t), M-12..M-15
- 하위: M-17 (학습 단계), M-23 (하이퍼파라미터 스펙)
- 모든 이전 모듈이 L_total에 기여

## 체크포인트

- C1 수학적 유효성: PASS — 10개 손실 항 모두 잘 정의된 미분 가능 함수입니다.
  λ 값은 하이퍼파라미터; 단계별 활성화는 학습 스케줄 결정입니다.
- C2 신규성: 개별 항에 대해서는 해당 없음. 새로운 측면: 단일 목표에서
  보정 + correction + necessity/sufficiency + value-aware의 통합.
- C3 Reviewer 공격: 중간 — "10항 손실은 신중한 조정 필요; λ에 불안정."
  방어: 단계적 학습이 항을 분리; ablation 스위트가 각 λ_i → 0 테스트.
- C4 타당성: PASS — 모든 항은 표준 연산; 이상한 수치 문제 예상 안 됨.
- C5 Claim-지표: 필수: λ 민감도 스윕 (최소 λ6, λ7, λ8 중요).
- C6 구현 위험: 낮음 — 모든 항을 통한 기울기 흐름은 표준.
- C7 실험 설계: Stage 1만으로는 OOD에서 실패함을 보여야 합니다 (staged 학습 필요성 검증).
- C8 실패 해석: Stage 2가 OOD에서 Stage 1 이상 개선 안 되면: correction 모듈이 아무것도 추가 안 함.
  "보정된 탐지" 주장으로 축소되며 correction 개선은 없음.
- C9 관련 연구: 해당 없음 — 설계 결정, 신규성 주장 아님.
- C10 컨텍스트 라우팅: 출처 = main.md §12-13. 하위: 12_TRAINING_STAGES.md, 13_ALGORITHM_CIRCA.md
