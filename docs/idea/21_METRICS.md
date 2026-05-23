# 21_METRICS — 4축 지표 체계

## 출처
- main.md §22 (실험 지표)
- deep-research-report.md §R-14 (4축 지표)

## 주장

FGLC 평가는 4개의 독립적인 지표 축이 필요합니다. NLL만 또는 return만 보고하는 것은
불충분합니다 — 논문은 4개 축 모두에서 기여를 주장하며, 각각을 측정해야 합니다.

## 축 1: 예측 정확도

| 지표 | 설명 | 필수 baseline |
|---|---|---|
| one-step NLL | -log pθ(z_{t+1}\|z_t,a_t,h_t) | 모든 baselines |
| MS-NLL | 다단계 rollout NLL (H=5,10,20) | 모든 baselines |
| Calibration ECE | σ 예측에 대한 기대 보정 오차 | β_t χ² 주장에 필수 |
| 신뢰도 다이어그램 | 신뢰도별 예측 빈화; 정확도 대비 도표 | 시각적 σ 보정 |

## 축 2: Falsification 탐지

| 지표 | 설명 | 오라클 레이블 필요 |
|---|---|---|
| OOD 탐지 AUROC | F_t 점수 사용; regime_id가 오라클 레이블 | 예 (평가만) |
| 탐지 지연 | 실제 regime 변화부터 β_t > 0.5까지 스텝 수 | 예 |
| 오탐율 | ID 데이터에서 β_t > 0.5 | 아니오 |
| 보정 커버리지 | β_t gate 발화율 ≤ ID에서 주장된 α | 아니오 |
| β_t 자기상관 | OOD 실제 이동 vs. ID 노이즈 하에서 AR(1) | 부분 (평가 regime 레이블) |

## 축 3: 귀인 / 인과 유효성

| 지표 | 설명 | 오라클 필요 |
|---|---|---|
| Necessity-Δ | L_without - L_with; > 0이어야 함 | 아니오 |
| Sufficiency-Δ | \|L_selected - L_full\|; < ε이어야 함 | 아니오 |
| Random-Δ | L_random - L_selected; > 0이어야 함 | 아니오 |
| Counterfactual-Δ | 반사실적 물리적 파라미터 하에서 NLL 변화 | 예 (시뮬레이션 오라클) |
| 마스크 정밀도/재현율 | α가 올바른 그룹 활성화 (변경된 팩터 대비) | 예 (시뮬레이션 오라클) |
| τ_g 유의성 | OOD 유형별 그룹 유틸리티 ATE에 대한 p-값 (CIRCA) | 아니오 |

## 축 4: 제어 성능

| 지표 | 설명 | 오라클 필요 |
|---|---|---|
| Return | 평균 에피소드 return (비할인 및 할인) | 아니오 |
| 성공률 | OOD 조건별 태스크 완료율 | 아니오 |
| 회복 시간 | Regime 변화부터 기준 return 회복까지 스텝 수 | 예 (regime 타임스탬프) |
| 에피소드당 planning 호출 수 | β_t > 0.5 발화 총 횟수 | 아니오 |
| 계산당 return | Return / 총 correction+planning rollouts | 아니오 |
| 최악의 경우 return | OOD-mixed 하에서 5백분위 return | 아니오 |
| 잘못된 가설 지속 시간 | 잘못된 dynamics 스텝 수 (오라클 비교) | 예 |

## 계산 매칭 실험 (핵심)

공격 5 방어에 따라: 모든 baselines에 FGLC와 동일한 계산 예산 제공 (에피소드당 동일 planning rollouts).
FGLC의 계산당 return 장점이 사라지면 → 추가 계산에서 이점, correction에서 아님.

## 지표 보고 요구사항

1. 모든 지표는 ≥3개 시드에 걸쳐 평균 ± 표준편차로 보고되어야 함
2. 통계적 유의성: 주요 주장에 대해 TD-MPC2 대비 p < 0.05 (짝지어진 t-검정) 필요
3. OOD 조건별 세분화 필요 (집계만이 아닌)
4. 오라클 지표는 "오라클 평가"로 명시적 레이블링 필요

## 연결 맵
- 상위: 19_BASELINES.md, 20_ABLATIONS.md
- 하위: 26_CROSSCHECK_SUMMARY.md
- 구현: src/fglc/evaluation/metrics.py (R4+ 단계)
