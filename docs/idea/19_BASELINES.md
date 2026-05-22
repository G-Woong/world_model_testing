# 19_BASELINES — 사라져서는 안 되는 Baseline 열거 (취약 SSoT)

## 출처
- main.md §22.5 (ablation 목록), deep-research-report.md §벤치마크
- CLAUDE.md §사라져서는 안 되는 Baselines

## 이 파일이 규범적 baseline SSoT입니다. 다른 곳에 중복 열거를 유지하지 마십시오.

## 필수 Baselines

모든 카테고리에 평가 세트에 최소 하나의 runner가 있어야 합니다.

### 카테고리 A: World Model Baselines

| ID | 이름 | 설명 | 예상 결과 |
|---|---|---|---|
| BASE-WM-01 | TD-MPC2 | 참조 decoder-free 잠재 WM (Hansen 2024) | ID에서 강함; OOD에서 저하 |
| BASE-WM-02 | DreamerV3 | RSSM 기반 WM (Hafner 2023) | 부분 관측 태스크에서 강함 |
| BASE-WM-03 | HiP-RSSM | 컨텍스트 조건부 RSSM (Achterhold 2022) | regime 컨텍스트와 함께 강함 |
| BASE-WM-04 | PLSM | 액션-효과 체계적 WM (Tomar 2024) | 액션 관련성 비교 |

### 카테고리 B: 적응 Baselines

| ID | 이름 | 설명 | 예상 결과 |
|---|---|---|---|
| BASE-ADAPT-01 | ReDRAW | 잔차 잠재 correction (sim-to-real) | 유사 메커니즘, causal attention 없음 |
| BASE-ADAPT-02 | AdaWM | 불일치 기반 적응 | FGLC의 가장 가까운 경쟁자 |

### 카테고리 C: Ablative Baselines

| ID | 이름 | 설명 | 예상 결과 |
|---|---|---|---|
| BASE-ABL-01 | Next-state-WM-only | FGLC 기본 WM, correction 모듈 없음 | FGLC Stage 1; 하한값 |
| BASE-ABL-02 | Always-correct WM | β_t = 1 항상 (falsification gate 없음) | Correction의 상한값; gate 필요성 테스트 |
| BASE-ABL-03 | Verifier-only (CUSUM) | CUSUM 탐지기, correction 없음 | 탐지, planning 이점 없음 |
| BASE-ABL-04 | Verifier-only (SPRT) | SPRT 탐지기, correction 없음 | 최적 탐지-지연 트레이드오프 |
| BASE-ABL-05 | Verifier-only (BOCPD) | BOCPD 변화점 탐지기, correction 없음 | 베이지안 탐지; planning 없음 |

### 카테고리 D: 계산/Planning Baselines

| ID | 이름 | 설명 | 예상 결과 |
|---|---|---|---|
| BASE-COMP-01 | Uncertainty-gated planner | σ_t 높을 때 더 많이 planning (falsification 없음) | 계산 효율성 비교 |
| BASE-COMP-02 | Random correction mask | 무작위 k 그룹 보정 (attention 가이드 아님) | Attention 기여 테스트 |
| BASE-COMP-03 | No-correction baseline | 기본 WM, correction 용량 없음 | 진정한 하한값 |
| BASE-COMP-04 | Compute-matched random realloc | FGLC와 동일 # planning rollout, 무작위 할당 | **핵심: 공격 5 방어** |

### 카테고리 E: 오라클 상한값

| ID | 이름 | 설명 | 예상 결과 |
|---|---|---|---|
| BASE-ORACLE-01 | Oracle-mass | Planner에 추론 시 실제 질량 제공 | 완벽한 OOD-mass correction |
| BASE-ORACLE-02 | Oracle-friction | Planner에 실제 마찰 제공 | 완벽한 OOD-friction correction |
| BASE-ORACLE-03 | Oracle-latency | Planner에 실제 액션 지연 제공 | 완벽한 OOD-latency correction |
| BASE-ORACLE-04 | Oracle-noise | Planner에 실제 노이즈 σ 제공 | 완벽한 OOD-noise correction |

## Baseline 제거 정책

Baseline이 제거되면 해당 주장을 할 수 없습니다:
- TD-MPC2 제거 → "TD-MPC2 능가" 주장 불가
- Compute-matched 제거 → "return-per-compute 개선" 주장 불가
- Oracle 제거 → "오라클 성능에 접근" 주장 불가
- Verifier-only 제거 → "correction이 탐지 이상을 추가" 주장 불가

## 연결 맵
- 이 파일을 참조하는 곳: CLAUDE.md, behavioral_coding_rules.md §5, baseline_ablation_guard.ps1
- 하위: 21_METRICS.md (각 baseline 평가), docs/ROADMAP/11_PHASE_R10_BASELINES.md
