# Mass OOD Novelty Relevance 분석 보고서

**보고일**: 2026-05-24  
**역할**: novelty-relevance-critic (Agent 3)  
**트리거**: T1 (핵심 claim 변경 전) + T6 (novelty-risk 감지)  
**소스**: Agent 1/2 결과, 직접 위협 논문 분석  

---

## 핵심 판정: NOVELTY_AT_RISK (조건부)

mass axis가 현재 데이터에서 실질적인 dynamics shift를 생성하지 못함.  
"5개 axis multi-axis benchmark" (Contribution 5)가 reviewer 공격에 취약.  
단, Contribution 1~4는 friction/latency/noise axis로 완전히 방어 가능하므로  
NOVELTY_COMPROMISED는 아님.

---

## 1. FGLC 5개 Contribution별 mass axis 의존성

| Contribution | mass 의존성 | 대체 가능 축 | 판정 |
|---|---|---|---|
| C1: falsification gate β_t | LOW (contact=0%에서 발화 불가) | friction/latency/noise | mass 없이 방어 가능 |
| C2: causal attention α_t | LOW (mass gradient 신호 부재) | friction/latency/noise | mass 없이 방어 가능 |
| C3: sparse residual correction | NONE (β_t 미발화 → correction 없음) | friction/latency/noise | mass 없이 방어 가능 |
| C4: robust MPC planning | INDIRECT | friction/latency/noise | mass 없이 방어 가능 |
| C5: multi-axis OOD benchmark | **HIGH** (5개 축 직접 명시) | friction + 3개 추가 | mass 약화 시 위험 |

C1~C4는 mass axis에 의존하지 않아도 완전히 입증 가능.  
C5만이 mass axis에 직접 의존하는 contribution이다.

---

## 2. 시나리오 A/B/C 평가

### 시나리오 A: mass axis 유지 (현재 design)

**R3 blocker 유지**: ood_severity FAIL → R3 smoke 금지 상태 지속  
**Novelty 영향**: mass OOD 결과(gap=0.004)를 제시하면 reviewer 3이 "PickCube + random policy는 mass-insensitive"라고 정확히 지적할 것  
**Reviewer-defensibility**: WEAK  
**판정**: 시나리오 A 단독으로는 R3 진행 불가, 채택 불가

### 시나리오 B: mass axis "weak OOD secondary" tier 격하 ★추천★

**Novelty 영향**: C1~C4는 완전 유지. C5는 "4 primary axes + mass(contact-dependent, secondary)"로 서술 수정  
**물리적 근거**: "mass OOD는 contact-dependent physics를 요구하며, random exploration policy 하에서는 state-level에서 severity 측정이 어려움"  
**"negative result as feature"**: β_t가 mass=1.5 OOD에서 발화하지 않는다면, conformal gate의 특이도(specificity)가 보장됨 — false positive 방지의 올바른 동작  
**Reviewer-defensibility**: MODERATE-TO-STRONG  
**SSoT 영향**: 없음 (18_DATA_BENCHMARKS.md는 axis 열거만, 우선순위 미명시)  
**구현 비용**: 0시간 (코드 변경 없음)  
**판정**: 단기 채택 권고

### 시나리오 C: PushCube-v1 추가 (mass-sensitive task) ★중기 권고★

**Novelty 영향**: C5의 "5개 axis" 주장 완전 유지 + multi-task generalization 추가  
**물리적 근거**: PushCube는 cube pushing이 task 정의상 필수 → contact rate 구조적으로 높음  
**Reviewer-defensibility**: STRONG  
**SSoT 영향**: 없음 (18_DATA_BENCHMARKS.md:54 PushCube 허용)  
**구현 비용**: 중간 (1~2시간 probe + 필요 시 재수집)  
**판정**: 중기 채택 권고. 시나리오 B(단기)와 병행 전략이 적절

---

## 3. Friction-Primary 전략으로 직접 위협 방어 가능 여부

| 논문 | threat_level | friction-primary 방어 | 근거 |
|---|---|---|---|
| TD-MPC2 (arXiv:2310.16828) | MED | **가능** | falsification gate + correction 없음. friction OOD에서 직접 구분 가능 |
| DreamerV3 (arXiv:2301.04104) | MED | **가능** | RSSM 기반, falsification/causal attention/nec-suf 없음 |
| HiP-RSSM (arXiv:2206.14697) | MED | **가능** | friction이 hidden param 핵심 경쟁 축. mass 없어도 방어 강화됨 |
| PLSM (arXiv:2401.17835) | LOW-MED | **가능** | training-time vs inference-time 구분. friction에서 입증 가능 |
| ReDRAW (arXiv:2504.02252) | MED | **가능** | no gate, no causal attention, no nec-suf. friction에서 방법론 차이 명확 |
| AdaWM (arXiv:2501.13072) | LOW-MED | **가능** | 자율주행 도메인, physical OOD benchmark 없음. friction-primary 전략 무관 |

**결론**: 6개 직접 위협 모두 friction-primary 전략으로 방어 가능.  
mass axis는 직접 위협 방어에서 결정적인 역할을 하지 않는다.

---

## 4. 2025/2026 신규 위협 목록

| 논문 | arXiv | threat_level | 메모 |
|---|---|---|---|
| ReDRAW (Blanier 2025) | 2504.02252 | MED | 방법론 친척. no gate, no causal attention으로 구분됨 |
| AdaWM (2025) | 2501.13072 | LOW-MED | 자율주행 도메인, 로봇 OOD 없음 |
| TD-M(PC)² (2025) | 2502.03550 | LOW | TD-MPC2 value 개선, dynamics correction 없음 |
| Learnable CP (2025) | 2509.21955 | LOW | conformal prediction 로봇 적용, correction 없음 |
| Bounding Shifts (2025) | 2508.06096 | LOW | novelty detection + planning, latent correction 없음 |

HIGH 중복 위협 없음. FGLC의 "falsification gate + causal attention + necessity/sufficiency + multi-axis physical OOD" 조합을 동시에 다루는 논문 발견되지 않음.

citation 교차검증:  
- ReDRAW: arXiv:2504.02252 + researchgate.net/publication/390468274 (2개 출처 ✓)  
- AdaWM: arXiv:2501.13072 + ICLR 2025 proceedings (2개 출처 ✓)  
- TD-M(PC)²: arXiv:2502.03550 + darthutopian.github.io (2개 출처 ✓)

---

## 5. "Negative Result as Feature" 전략

### 유리한 논거
- β_t가 mass=1.5 OOD에서 발화하지 않는다면 **conformal gate의 특이도(specificity)가 보장됨** — false positive 방지의 정확한 동작
- 투명한 보고: "contact-independent task에서 mass shift는 state dynamics에 weak effect (gap=0.004)"라는 서술은 데이터 정직성의 증거
- 숨겼다가 발각되는 것보다 먼저 인정하는 것이 reviewer 방어력 높음

### 위험한 논거
- "5개 axis" 주장이 "4개 axis + 1개 negative"로 약화되면 C5 스코프가 줄어듦
- mass negative result가 FGLC 메커니즘 문제로 오독될 위험 → framing 중요: "task 설계 문제, FGLC 메커니즘 문제 아님"

### 적용 조건
friction/latency/noise 3축에서 positive result가 충분히 확보될 때만 유효.  
현재 단계(R3 smoke도 진행 못한 상태)에서 확정하기는 이르다.

---

## 6. 권고사항

**단기**: 시나리오 B 채택  
- friction을 primary OOD axis로 명시, R3 smoke를 friction OOD로만 진행  
- ood_severity gate에서 mass axis를 "contact-dependent, BLOCKED"로 별도 처리  

**중기**: 시나리오 C 채택  
- PushCube-v1 probe 10~20 ep → gap ≥ 0.01 확인 후 재수집  
- mass axis를 primary로 복원하거나 "contact-intensive task"로 한정 서술  

**논문 서술 보호** (필요 시):
```
"Contribution 5: multi-axis OOD benchmark (friction/latency/noise/action_gain primary;
mass shift는 contact-dependent로 PushCube-v1에서 검증 예정)"
```
