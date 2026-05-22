# 23_FAILURE_MODES — 실패 모드

## 출처
- main.md §23 (피해야 할 실패 패턴)
- docs/orchestration/agent_reports/synthesis/2026-05/reviewer2_attack_fglc_R1.md

## 5가지 핵심 실패 모드 (main.md 기반)

### 실패 1: Correction 모듈이 너무 강함
**패턴**: 기본 WM이 아무것도 학습 안 함; correction 모듈이 모든 dynamics를 흡수.

**탐지**: Stage 1 NLL이 correction 없이 감소 안 함; Stage 2 correction 크기 > δ_max;
β_t가 ID 데이터에서 타임스텝의 >20%에서 발화.

**완화**:
- 단계적 학습 (Stage 2에서 기반 동결)
- δ_max clamp (δ_max = 0.1 초기, Stage 1이 수렴할 때만 증가)
- L_corr_size 페널티
- β_t gate (falsification 탐지 시에만 correction)

### 실패 2: Attention = 지름길 (선택적이지 않음)
**패턴**: α_t가 항상 OOD 유형에 관계없이 동일한 1-2개 그룹을 선택.

**탐지**: 모든 OOD 조건에서 attention 엔트로피 매우 낮음; ABL-04 (random mask) ≈ FGLC.

**완화**:
- L_entropy 페널티 (항상 선택하는 것 방지)
- OOD 유형별 attention 분포가 다른지 검증
- Necessity 테스트: 동일한 그룹 제거가 *다른* OOD 조건에서도 성능 저하 유발해야 함

### 실패 3: σ 팽창 (분산 붕괴 탈출)
**패턴**: 모델이 큰 σ_t를 학습하여 모든 불일치를 "불확실성 범위 내"로 처리.

**탐지**: σ에 대한 ECE 도표에서 과과신; OOD AUROC → 0.5; σ_t >> 데이터 표준편차.

**완화**:
- L_cal = mean(log σ_t)² 페널티
- σ clamp: σ_min=1e-3, σ_max=3.0
- 학습 중 σ_t 모니터링; σ_t > 2× 데이터 표준편차이면 중단

### 실패 4: 잠재 그룹 붕괴 (그룹들이 동일한 표현 학습)
**패턴**: K 그룹 모두 유사한 특징 인코딩; 그룹 상호작용이 그룹 구분 안 함.

**탐지**: 그룹 표현 간 코사인 유사도 > 0.9; ABL-08 (K=1) ≈ FGLC.

**완화**:
- 그룹별 dynamics 헤드 (그룹이 다른 측면을 예측하도록 강제)
- 그룹 분리 정규화 (선택적: L_2,1 sparse group lasso)
- 올바른 K를 찾기 위한 K 민감도 ablation

### 실패 5: 예측은 개선됐는데 제어는 안 됨
**패턴**: World model 논문에서 흔한 문제.

**탐지**: Stage 2가 보정된 NLL < 비보정 NLL을 보이지만 폐쇄 루프 return ≈ TD-MPC2 baseline.

**완화**:
- L_value (value-aware correction)
- L_attn_align (cause_score 정렬)
- H_corr 증가 (단기 유지가 너무 짧을 수 있음)
- MPPI 샘플이 보정된 dynamics를 사용하는지 확인 (기본 dynamics가 아닌)

## Reviewer-2 추가 실패 모드

### 실패 6: Causal Attention 레이블이 지속적인 Reviewer 회의론 유발
**패턴**: 논문이 "causal attention"을 사용하지만 Jain-Wallace 조작 테스트를 통과 못함.

**완화**: "intervention-policy attention"으로 이름 변경 또는 τ_g 무작위화된 개입 실험 실행
(CIRCA 알고리즘이 이 방어에 필요).

### 실패 7: K=6 그룹이 시드 의존적
**패턴**: OOD attention 벡터에 대한 시드 간 Spearman < 0.7.

**완화**: 5개 시드 실험 실행; <0.7이면 K를 줄이거나 명시적 그룹 분리 손실 추가.

### 실패 8: 계산 매칭된 Baseline이 FGLC와 동등
**패턴**: BASE-COMP-04 (계산 매칭된 무작위 재할당) ≈ FGLC return.

**완화**: 이것은 **하드 축소**입니다. 주장을 "FGLC는 더 적은 correction 평가로 동일한 성능 달성"으로 축소 (효율성 주장). "correction이 planning을 개선한다" 주장 불가.

## 연결 맵
- 출처: main.md §23, reviewer2_attack_fglc_R1.md
- 하위: 24_OPEN_QUESTIONS.md, 26_CROSSCHECK_SUMMARY.md
