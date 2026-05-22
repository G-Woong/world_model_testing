# 20_ABLATIONS — 사라져서는 안 되는 Ablation Family (취약 SSoT)

## 출처
- main.md §22.5 (ablation 목록), deep-research-report.md §실험 설계
- CLAUDE.md §필수 ablation family

## 이 파일이 규범적 ablation SSoT입니다. 다른 곳에 중복 열거를 유지하지 마십시오.

## 11개 필수 Ablation Family

| ID | Family | 제거된 구성 요소 | Ablation의 예상 효과 | 검증되는 주장 |
|---|---|---|---|---|
| ABL-01 | no-correction | 모든 δ_t^k 제거 (correction = 0) | OOD return 저하 → 기본 WM 불충분 | Correction이 필요함 |
| ABL-02 | no-attention | α_t를 균일 1/K로 대체 | Return 및 귀인 저하 | Attention 선택이 가치 있음 |
| ABL-03 | no-falsification-gate | β_t = 1 항상 (always-correct) | OOD 약간 개선되지만 계산 비효율 | Gate가 계산 절약 제공 |
| ABL-04 | random-mask | 무작위 k 그룹, attention 가이드 아님 | Return < FGLC → attention이 무작위 아님 | Attention이 비무작위적으로 선택적 |
| ABL-05 | no-value | λ2 = λ_value = 0 | NLL 개선, return 저하 | Value-aware 손실이 필요함 |
| ABL-06 | no-sparse | 희소성 페널티 없음 (softmax, λ5=0) | Attention 분산; 귀인 저하 | 희소성이 그룹 선택 가능하게 함 |
| ABL-07 | no-temporal-consistency | λ7 = 0 | Attention이 시간적으로 불안정 | 시간적 일관성이 귀인 안정화 |
| ABL-08 | collapsed-K=1-latent | K=1 (단일 그룹, 분해 없음) | Correction 국소화 불가; no-attention과 유사 | K>1 그룹화가 필요함 |
| ABL-09 | no-iVAE-prior | iVAE 목표 없는 I3G | 귀인 정밀도 저하 (I3G만) | iVAE 식별 가능성 필요 (I3G) |
| ABL-10 | no-conformal-calibration | 경험적 분위수 대신 하드 임계값 | 오탐율 제어 안 됨 | Conformal 보정이 필요함 |
| ABL-11 | no-robust-MPC | 표준 MPC (robust 아님) | 최악의 경우 성능 저하 | 불확실성 하에서 robust planning 필요 |

## Ablation 결과 규칙

ABL-02 (no-attention) ≈ FGLC이면: **중단.** "sparse attention이 균일 선택 이상을 추가" 주장 무효.
ABL-01 (no-correction) ≈ OOD에서 FGLC이면: **중단.** 문제 존재 실패 — 기본 WM이 OOD에서 충분.
ABL-08 (K=1) ≈ FGLC이면: **중단.** 그룹 분해 주장 무효; 게이팅된 residual 주장으로 축소.
ABL-10 (하드 임계값) ≈ FGLC이면: **CONDITIONAL.** Conformal 보정 주장 약화; 경험적으로 축소.

## Ablation 실행 계획

```
Phase R9 (docs/ROADMAP/10_PHASE_R9_ABLATION_GRID.md 참조):
  - ManiSkill PickCube (주요 태스크)에서 11가지 family 모두 실행
  - ABL-01, ABL-02, ABL-08도 PushCube에서 실행 (태스크 간 일반화)
  - 각 ablation: 3개 시드, 5가지 OOD 조건, 조건당 100개 평가 에피소드
  
실행 순서:
  1. ABL-01 (no-correction) — 문제 존재 검증
  2. ABL-08 (K=1) — 분해 필요성 검증
  3. ABL-02 (no-attention) — 선택 기여 검증
  4. ABL-10 (no-conformal) — 보정 기여 검증
  5. ABL-03 (no-gate) — β_t gate 계산 절약 검증
  6. ABL-05 (no-value) — value-aware 손실 검증
  7. ABL-04 (random-mask) — attention 비무작위성 검증
  8. ABL-06, ABL-07, ABL-09, ABL-11 — 2차 검증
```

## 연결 맵
- 이 파일을 참조하는 곳: CLAUDE.md, behavioral_coding_rules.md §5, baseline_ablation_guard.ps1
- 하위: 21_METRICS.md, docs/ROADMAP/10_PHASE_R9_ABLATION_GRID.md
