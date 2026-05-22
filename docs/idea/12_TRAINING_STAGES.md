# 12_TRAINING_STAGES — 학습 단계

## 출처
- main.md §13 (학습 단계), §20 (학습 루프 의사 코드)

## 주장

FGLC는 4개의 순차적 단계로 학습해야 합니다. 처음부터 end-to-end 학습하면 correction 모듈이
기본 WM 기울기를 모두 흡수하여 기본 WM이 의미 있는 예측을 생성하기 전에 학습 실패합니다.

## 단계

```
Stage 1: 기본 WM 사전 학습 (ID 데이터만)
  학습: encoder E, GRU h_t, dynamics fθ, 보상 Rθ, 가치 Vθ
  동결: 없음
  손실: L_base_dynamics + L_reward + L_value + L_calibration
  Gate 기준: ID NLL 수렴 + OOD NLL > ID NLL (문제 존재 확인)

Stage 2: Correction 모듈 학습 (ID + OOD 데이터)
  동결: encoder E (또는 매우 낮은 LR), base dynamics fθ (또는 낮은 LR)
  학습: β-gate MLP, causal attention Aφ, correction 어댑터 Gψ
  손실: + L_corrected_dynamics + L_sparse + L_size + L_temporal + L_nec + L_suf + L_rand
  Gate 기준: OOD 보정된 NLL < 비보정 NLL; correction 크기 < δ_max/2

Stage 3: Planner 통합
  동결: encoder, dynamics (Stage 1 가중치 안정)
  학습: 폐쇄 루프 시뮬레이션에서 planner (MPPI/CEM)
  손실: return 가중 rollout; 가치 TD 업데이트
  Gate 기준: 폐쇄 루프 return이 최소 2개 OOD 조건에서 TD-MPC2 baseline 초과

Stage 4: 선택적 온라인 미세 조정
  온라인: 새로운 regime 관측에 correction 모듈 적응
  손실: 최근 궤적 버퍼에 Stage 2 손실 적용
```

## 왜 Stage 2에서 기본 WM을 동결하는가

기본 dynamics와 correction 어댑터가 동시에 학습되면:
1. Correction 모듈이 correction 손실과 기본 dynamics 모두에서 기울기 신호 받음
2. Correction 모듈이 기본 dynamics residual을 캡처하도록 학습 → 기본 WM이 아무것도 학습 안 함
3. β_t gate가 "기본 WM이 OOD로 인해 틀림"과 "correction이 공백을 채움"을 구분 불가
4. "기본 WM = H0 가설, correction = H1" 이야기가 붕괴됨

Stage 2에서 기본 WM LR을 동결(또는 심각히 제한)하면 correction 모듈이 기본 WM이
생성하는 것만 개선할 수 있습니다.

## 연결 맵
- 상위: M-16 (손실 설계), M-6 (기본 dynamics 아키텍처)
- 하위: M-18 (Stage 3의 planner), M-24 (의사 코드)
- 모든 구현 단계: R2→R3→R4→R5→R6→R7 in ROADMAP

## 체크포인트

- C1 수학적 유효성: PASS — 단계적 학습은 설계 결정, 수학적 주장이 아님.
  동결의 논거는 경험적으로 동기화됨.
- C2 신규성: 해당 없음 — 단계적 학습은 어댑터 기반 방법에서 표준.
- C3 Reviewer 공격: 낮음 — "신중한 단계 설정이 필요하다"는 예상된 것. 완화:
  end-to-end 학습이 실패함을 보여주는 ablation (correction이 기본 WM을 흡수).
- C4 타당성: PASS — 태스크당 Stage 1 ~2시간 A100, Stage 2 ~4시간, Stage 3 ~6시간.
  태스크당 총 ~12시간; 3개 태스크 36시간. 8주 예산 내 실현 가능.
- C5 Claim-지표: Stage 1 gate: ID NLL 수렴 + OOD NLL > ID NLL (OOD 도전이 존재함).
  이것 없이는 보정할 것이 없음.
- C6 구현 위험: 낮음
- C7 실험 설계: 필수: Stage 1만으로 OOD 실패를 보여야 함 (문제 존재 검증).
  필수: end-to-end 학습이 staged 학습 대비 실패함을 보여야 함.
- C8 실패 해석: Stage 1 OOD NLL ≈ ID NLL이면: OOD 이동이 기본 WM에 도전하지 않음.
  이것은 근본적인 문제 존재 실패입니다. 데이터셋 설계로 되돌아가야 함.
- C9 관련 연구: 해당 없음 (표준 실습)
- C10 컨텍스트 라우팅: 출처 = main.md §13,20. 하위: 13_ALGORITHM_CIRCA.md, docs/ROADMAP/04_PHASE_R3...
