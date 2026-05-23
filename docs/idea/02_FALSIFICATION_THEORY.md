# 02_FALSIFICATION_THEORY — Falsification 이론

## 출처
- main.md §5 (불일치), §6 (falsification gate)
- deep-research-report.md §Calibration·conformal·risk control, §CUSUM·SPRT·BOCPD

## 주장

예측 불일치를 모델 자체의 불확실성 대비 **표준화**하여 보정 유효한 falsification 점수를
생성할 수 있습니다. 이 점수가 ID 분포의 경험적 분위수 임계값을 초과하면 현재 dynamics
가설은 위반된 것입니다. Gate β_t는 보정된 sigmoid MLP로, 임계값이 보류된 ID 궤적의
경험적 α-분위수로 설정되어 수준 α에서 유한 샘플 커버리지를 제공하므로,
하드 임계값과 수학적으로 구별됩니다.

## 수학적 형식화

```
그룹별 표준화된 불일치:
  ρ_t^k = (z_{t+1}^k - μ_t^k) / σ_t^k  ∈ R^d

그룹 falsification 점수:
  F_t^k = ||ρ_t^k||₂²

H0 하에서 (올바른 모델, 보정된 σ): F_t^k ~ χ²_d
  [각 ρ_t^k_i ~ N(0,1)이므로]

전체 점수: F_t = Σ_k F_t^k ~ χ²_{K*d}  (H0 하에서)

Falsification gate (보정됨):
  β_t = sigmoid(MLP([F_1^k,...,F_K^k, F_t, h_t]))
  
  보정: 임계값을 보류된 ID 데이터의 (1-α)-분위수로 설정
  → 유한 샘플 오탐율 ≤ α

보정 손실 (σ 붕괴 탈출 방지):
  L_cal = E[log σ_t]²  또는 clamp: σ_min ≤ σ_t ≤ σ_max
  
  결합 NLL:
  L_nll = Σ_t Σ_k [0.5*(z_{t+1}^k - μ_t^k)²/(σ_t^k)² + log σ_t^k]
```

## 핵심 전제 부하 조건: σ 보정

σ_t가 잘못 보정되면 χ² 탐지 보증이 **붕괴**됩니다:
- σ 팽창 → 모든 불일치가 "불확실성 범위 내"로 보임 → 탐지 AUROC → 0.5
- NLL 손실만으로는 딥 네트워크에서 잘 보정된 σ를 보장하지 않습니다

**필수 증거**: ID 및 OOD에서 예측 분산에 대한 신뢰도 다이어그램 / ECE.

## Conformal vs CUSUM/SPRT/BOCPD 비교

| 방법 | 커버리지 보증 | Action 관련성 | 순차적 검정력 |
|---|---|---|---|
| FGLC conformal gate | 유한 샘플, 주변부 | Value-aware 손실을 통해 | β_t MLP를 통해 |
| CUSUM (Page 1954) | CUSUM 최적성 | 없음 | 강함 |
| SPRT (Wald 1945) | 확률비 | 없음 | 강함 |
| BOCPD (Adams & MacKay 2007) | 베이지안 | 없음 | 강함 |

FGLC의 CUSUM/SPRT/BOCPD 대비 장점: action/value 관련성을 직접 통합합니다.
FGLC의 gate가 잘못 보정되면 CUSUM/SPRT/BOCPD가 탐지 전용 지표에서
FGLC를 능가할 수 있습니다. 이는 예상된 정직한 결과로,
FGLC는 탐지 최적성을 action 관련성과 교환합니다.

## 연결 맵
- 상위: M-6 (dynamics 사전 분포), R-7 (CUSUM/SPRT/BOCPD baseline)
- 하위: M-9 (attention은 β_t 사용), M-10 (correction은 β_t로 gate됨), R-6 (conformal)
- 핵심: 탐지 성능 주장 전에 σ 보정 증거가 있어야 함

## 체크포인트

- C1 수학적 유효성: **CONDITIONAL** — χ² 주장은 명시된 가정 하에 유효.
  핵심 위험: σ 보정이 핵심 부하 조건입니다. 분산 보정 없이는 χ² 분포 논거가
  실패하고 gate는 학습 가능한 임계값과 구별 불가능해집니다.
  구별 가능성 수정: 임계값 = ID 점수의 경험적 (1-α)-분위수 (명시적 커버리지).
  에이전트 보고서: mathematical-validity-critic 결과 2026-05-22 참조
- C2 신규성: 대기 중
- C3 Reviewer 공격: 대기 중
- C4 타당성: PASS — 보정 세트는 1000개 ID 궤적에서 수집 가능.
  ECE 계산은 학습 후 O(n). R4 단계에서 실현 가능.
- C5 Claim-지표: CONDITIONAL — 탐지 AUROC + ECE + 오탐율을 보여야 함.
  σ가 잘못 보정되면 주장이 붕괴됩니다.
- C6 구현 위험: 대기 중
- C7 실험 설계: 필수 ablation: no-conformal-calibration (하드 임계값).
  이것 없이는 "보정된 gate" 주장이 검증되지 않습니다.
- C8 실패 해석: 주요 실패: σ 붕괴. σ가 팽창하면 gate가 아무것도 감지하지 못합니다.
  완화: L_cal + σ clamp + 없을 때 ECE가 저하됨을 보여주는 ablation.
- C9 관련 연구 (≥2 출처): 대기 중 — Adams & MacKay BOCPD, Angelopoulos CRC 필요.
- C10 컨텍스트 라우팅: 출처 = main.md §5-6.
  하위: 06_CAUSAL_ATTENTION.md, 13_ALGORITHM_CIRCA.md, 21_METRICS.md §탐지 축.

## 열린 질문
- 경험적 분위수 보정이 충분한가, 아니면 전체 conformal 커버리지(CRC)가 필요한가?
- 다른 이동 크기에서 CUSUM 대비 탐지 지연은 어떠한가?
- 잘 보정된 gate가 always-correct보다 엄격히 낮은 planning 비용을 갖는다는 것을 증명할 수 있는가?
