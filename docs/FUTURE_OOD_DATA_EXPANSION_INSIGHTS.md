# Future OOD Data Expansion Insights

> **Date**: 2026-05-24
> **Branch**: `memory-redesign-2026-05-16`
> **Source finding**: R3 two-axis smoke (friction + action_gain) — `reports/R3_SMOKE_CLOSURE_REPORT.md`
> **Audience**: future-R3/R4/R5/R6 data design, paper Section §Methods, reviewer defense.
> **Status**: insight 기록용. **본 문서는 데이터 수집 명령이 아니다**. 새 데이터 수집은 별도 readiness audit + 사용자 승인 후 진행한다.

---

## A. 배경 — 왜 이 문서가 존재해야 하는가

R3 base world model의 friction + action_gain 2-axis smoke에서 다음 두 사실이 동시에 확인되었다.

1. base WM은 ID NLL gate를 통과한다 (PickCube −0.16, PushCube −1.20, gate `< 0.5`).
2. 그러나 두 OOD 축 모두에서 raw NLL이 ID NLL보다 더 낮아진다 ("NLL 역전"). 양 task 동일.

원인 분석 결과 이 역전은 wiring bug가 아니라 **action_gain=0.7 / friction=5.0이 state transition magnitude를 줄여 OOD를 likelihood 관점에서 "쉬워 보이게(easy-looking)"** 만들기 때문이다 (transition magnitude PickCube: train 1.305 vs gain 0.924, **−29%**).

이 결과는 **두 가지 future implication**을 동시에 갖는다:

- (i) R4 falsification gate는 "easy-looking OOD"도 탐지해야 한다는 강한 동기 → R3 데이터를 그대로 R4 evaluation에 재활용 가능.
- (ii) R4/R5/R6의 robust validation을 위해 "hard OOD"(transition magnitude가 줄지 않거나 늘어나서 raw NLL도 같이 상승하는 OOD)를 별도로 확보해야 함 → 본 문서가 그 데이터 확장 후보를 기록.

이 두 카테고리를 명확히 구분하지 않고 OOD 데이터를 추가하면 (1) R4 효과 측정이 흐려지고, (2) reviewer가 "특정 OOD에 맞춘 방법 아니냐"고 공격할 여지가 생긴다. 따라서 본 문서는 future data design의 **분류·우선순위·정당화 자료**로 보존된다.

---

## B. R3에서 얻은 핵심 insight (요약)

| # | insight | evidence | future 활용 |
|---|---|---|---|
| 1 | base WM의 raw NLL은 OOD에서 더 낮아질 수 있다 | PickCube ood_gain_nll−id_nll=−0.131, PushCube=−0.050 | R4 β_t gate가 raw NLL의 빈틈을 메우는지 직접 측정 |
| 2 | NLL 역전의 직접 원인은 transition magnitude 축소이다 | gain=0.7 → trans 1.305→0.924 (−29%), friction=5.0 → −10% | R4 evaluation에서 magnitude-controlled OOD subset 사용 |
| 3 | mass=1.5는 transition magnitude를 거의 변화시키지 않는다 | trans +1% / +2% | mass OOD axis는 R4에서 informational only, hard OOD 후보 아님 |
| 4 | base WM은 OOD label과 무관하게 학습된다 (regime_id 없음) | forbidden field test 32/32 PASS | R4가 추가하는 모든 OOD 신호는 model 입력 변경 없이 ρ_t 통계만으로 얻어야 함 |

---

## C. easy-looking OOD — 정의와 실세계 예시

### C.1. 정의
OOD 조건이 dynamics rule을 바꾸지만 **state transition magnitude를 축소**하거나 더 부드럽게 만들어, ID로 학습된 σ²에 대해 residual²/σ² 항이 줄어들고 결과적으로 raw NLL이 ID와 같거나 더 낮아지는 OOD.

수식 직관:
- ID: `NLL_id = 0.5 log(2πσ̂²) + E_id[(x−μ̂)²/σ̂²]/2`
- easy-looking OOD: `E_ood[(x−μ̂)²] < E_id[(x−μ̂)²]` (transition이 작아짐)
- → `NLL_ood < NLL_id` (raw NLL 역전)

### C.2. R3에서 관측된 사례

| axis | OOD value | transition mag. 변화 | NLL 변화 (PickCube/PushCube) |
|---|---|---:|---:|
| action_gain | 0.7 | **−29%** | id 대비 −0.131 / −0.050 |
| friction | 5.0 (joint) | **−10% / −9%** | id 대비 −0.084 / −0.011 |

### C.3. 실세계 대응 (왜 reviewer가 신경 써야 하는가)

| 시나리오 | dynamics 변화 | 안전/제어 위험 |
|---|---|---|
| Actuator gain 감소 (모터 power 저하) | action effect 축소 | control authority 감소 → tracking error 누적 → 그러나 transition은 더 "smooth"하게 보임 |
| 배터리 약화 (LiPo voltage sag) | gain 감소 + latency 미세 증가 | 명령은 작동하나 실제 effect 축소 |
| 제어기 둔감화 (low-pass filter 강화) | 고주파 dynamics 억제 | smoothing으로 NLL은 낮아질 수 있음 |
| Joint 마찰 증가 (마모) | 움직임 축소 | precise manipulation 실패하나 raw transition은 작아짐 |
| Soft contact / cushioned end-effector | impact dynamics 부드러움 | raw NLL이 OOD 신호를 놓침 |

→ **이 모든 시나리오에서 raw NLL은 OOD를 탐지하지 못할 수 있다.** β_t gate가 이런 case를 잡지 못하면 안전 critical 환경에서 falsification 실패.

### C.4. R4에서 easy-looking OOD가 갖는 역할
- "raw NLL이 실패하는 case"의 reproducible benchmark.
- R4 β_t gate가 magnitude-only가 아닌 direction + sequential evidence를 활용해야 함을 입증.
- conformal calibration이 σ̂에 직접 의존하지 않아야 함을 강제.

---

## D. hard OOD — 정의와 실세계 예시

### D.1. 정의
OOD 조건이 dynamics rule을 바꾸어 **predictability 자체를 악화**시키고, raw NLL이 ID 대비 상승하는 OOD. 전통적 OOD detection benchmark가 다루는 케이스.

수식 직관:
- hard OOD: `E_ood[(x−μ̂)²] > E_id[(x−μ̂)²]` (모델이 OOD에서 더 큰 prediction error 누적)
- → `NLL_ood > NLL_id` (정방향)

### D.2. 후보 axis (현재 미수집)

| axis | mechanism | 예상 transition 변화 | hard 정도 |
|---|---|---|---|
| **latency (action delay)** | 명령 효과가 k step 지연 → 모델이 t에서 예측한 μ̂_t와 실제 x_{t+1}이 시간축에서 어긋남 | residual 크기 증가, temporal mismatch | 매우 hard |
| **stronger friction** (e.g., friction=20.0) | 정지 마찰이 운동을 막다가 갑자기 break-away → 불연속 dynamics | residual 분산 증가 | hard |
| **high-gain saturation** (gain=2.0+) | actuator saturation 진입 → 비선형 clipping | residual 분포 왜곡 | hard |
| **multi-axis OOD** (friction + gain 동시) | 두 효과 상호작용 | 양 효과 누적, predictability 악화 | very hard |
| **severe latency + gain shift** | 시간축 + 크기축 동시 OOD | 양 효과 비선형 결합 | very hard |

### D.3. 실세계 대응

| 시나리오 | dynamics 변화 |
|---|---|
| 통신 지연 (network latency, ROS message lag) | k-step action delay |
| 제어 지연 (compute saturation, scheduler jitter) | variable latency |
| 강한 마찰/저항 (rusty joint, jam) | break-away dynamics |
| Actuator instability (PID gain mistune) | oscillation, saturation |
| 복합 장애 (gain 감소 + latency 증가) | 다중 axis OOD |

### D.4. R4/R5/R6에서 hard OOD가 갖는 역할
- 전통적 OOD detection metric에서 base WM raw NLL도 정상 작동하는 환경 → β_t가 "추가로" 무엇을 잡는지 측정 가능.
- R5 causal attention의 sparse selection이 hard OOD에서 필수 group만 활성화하는지 검증.
- R6 correction module의 actually-helpful-correction이 hard OOD에서 control return 개선으로 이어지는지 검증 (raw NLL 개선만으로는 불충분).

---

## E. 왜 둘 다 필요한가 — 둘 중 하나만 쓰면 실패하는 시나리오

### E.1. easy-looking OOD만 쓰는 경우
- R4 evaluation이 raw NLL이 못 잡는 case만 본 다음 "β_t가 AUROC 0.9를 달성했다"고 결론.
- Reviewer: "이건 raw NLL이 실패하는 특수 case만 노린 거 아닌가? 일반 OOD에서는 어떻게 되나?"
- 답변 불가 → 논문 reject 위험.

### E.2. hard OOD만 쓰는 경우
- R4 evaluation이 raw NLL이 잡는 case에서 β_t의 "추가" 효과만 본다.
- Reviewer: "이게 raw NLL과 뭐가 다른가? 그냥 raw NLL 잘 calibrate한 것 아닌가?"
- 답변 불가 → novelty 약함.

### E.3. 둘 다 쓰는 경우
- easy-looking OOD: "raw NLL이 실패하는 경우에 β_t가 작동한다" → falsification gate의 added value 입증.
- hard OOD: "raw NLL이 작동하는 case에서 β_t는 raw NLL 이상으로 작동한다" → general capability 입증.
- Reviewer 공격에 모두 답변 가능.

### E.4. 본 R3 finding이 두 카테고리를 자연스럽게 강제
- 현재 우리는 (a) friction + gain 2개 axis로 easy-looking OOD를 이미 확보.
- (b) 같은 dynamics axis의 hard 변형(stronger friction, higher gain)과 (c) latency, (d) multi-axis를 추가 확보하면 contrast가 명확해짐.
- 같은 axis(friction)에서 magnitude를 바꾸기만 하면 되므로 collector 코드 변경 최소.

---

## F. R4 / R5 / R6에서 어떻게 활용할 것인가

### F.1. R4 falsification gate evaluation 설계 권장
| component | use easy-looking | use hard | rationale |
|---|---|---|---|
| primary AUROC | ✓ | ✓ | 양 카테고리 평균 AUROC + per-category breakdown |
| ablation: magnitude-only gate | ✓ | ✓ | direction component가 easy-looking에서 결정적임을 입증 |
| ablation: σ̂-dependent calibration | ✓ | (sanity) | σ̂-기반은 easy-looking에서 실패해야 함 |
| ablation: single-step gate | ✓ (latency 포함 후) | ✓ | sequential aggregation 필요성 입증 |
| baseline comparison | ✓ | ✓ | ReDRAW / AdaWM가 두 카테고리에서 어떻게 다른지 측정 |

### F.2. R5 causal attention 활용
- easy-looking OOD: ρ_t magnitude는 작지만 일부 latent group(action-effect-related)에 집중. attention sparsity 검증에 사용.
- hard OOD: ρ_t magnitude가 크고 다양한 group에 분산. attention의 group-selectivity가 다양한 OOD에 적응적인지 측정.

### F.3. R6 correction module 활용
- easy-looking OOD: NLL이 이미 낮으므로 correction이 NLL을 더 낮추기는 어려움 → return 기반 metric으로 actually-helpful-correction 검증.
- hard OOD: NLL이 높으므로 correction이 NLL 개선과 return 개선을 동시에 달성하는지 측정 (necessity/sufficiency).

### F.4. R13 necessity/sufficiency deep eval
- easy-looking OOD: correction 제거 시 control return 손상 여부 (necessity) — magnitude가 작으므로 baseline 차이가 미세할 가능성.
- hard OOD: correction 단독만으로 충분히 회복하는지 (sufficiency) — 큰 차이가 기대됨.

---

## G. 후보 axis ranking — 우선순위와 추천 사유

| rank | axis | category | 추천 사유 | risk / cost |
|---|---|---|---|---|
| 1 | **stronger friction** (e.g., friction=20.0) | hard | 기존 collector 그대로 재사용 (friction value만 변경) | 데이터 수집 1회 (~1h GPU), risk 낮음 |
| 2 | **action_gain reverse** (gain=1.3) | hard (자체 검증용) | β_t 양방향 detection 검증 (이 자체로 critical) | 동일 collector, risk 낮음 |
| 3 | **latency** (k=2~3 step delay) | hard | 시간축 OOD; temporal aggregation 필요성 입증 | collector에 delay buffer 추가 필요 (코드 변경 ~30 LOC) |
| 4 | **multi-axis: friction × gain** | very hard | reviewer가 가장 강하게 요구할 가능성 | OOD value 2개 동시 적용, sample 분산 큼 |
| 5 | **noise** (observation noise σ=0.05) | calibration test | dynamics OOD가 아니라 observation-level shift; specificity test 용 (β_t가 잘못 trigger되면 안 됨) | collector에 noise injection (작은 변경) |
| — | **mass repair track** | (separate) | random policy로는 mass effect 미미. contact-rich/scripted/goal-conditioned policy 검토 필요 | 본 작업 범위 외, 별도 plan 필요 |

### 우선순위 선정 원칙
1. 기존 collector 재사용 가능성이 높을수록 우선 (rank 1, 2).
2. R4 β_t 양방향 detection의 직접 evidence가 가능한 것이 critical (rank 2).
3. paper reviewer가 요구할 가능성이 높은 case 우선 (rank 4).
4. dynamics OOD와 observation OOD의 분리는 명확히 (rank 5는 specificity test).
5. mass repair는 별도 track으로 분리 — random policy로 의미 있는 변화를 만들기 어려움이 R3에서 입증됨.

---

## H. Future data collection checklist (실행 전 의무)

새 OOD 데이터를 수집하기 전에 다음을 모두 만족시켜야 한다.

### H.1. 사전 readiness audit
- [ ] axis 정의: 어떤 OOD parameter를 어떤 value로 설정하는가
- [ ] expected transition magnitude 예측 (easy-looking인지 hard인지)
- [ ] collector 코드 변경 범위 식별 (`scripts/fglc/collect_maniskill.py`)
- [ ] manifest seed_pool 계획 (cross-task disjoint 확인)
- [ ] HDF5 schema 동일성 확인 (existing 6 splits와 호환)
- [ ] forbidden field가 새 split에서 leak되지 않는지 검증 (test_fglc_forbidden_field_sync)
- [ ] OOD severity gate 정의 (`tests/test_fglc_ood_severity.py` 형식)

### H.2. 사전 비용 추정
- [ ] 1 split 수집 wall-clock 추정 (PickCube 50ep ≈ 5min @ random policy)
- [ ] disk size 추정 (현재 1 split ≈ 1~10 MB)
- [ ] GPU 사용량 추정 (data collection은 보통 CPU)
- [ ] R4 evaluation 시 추가 wall-clock (1 OOD split ≈ +1 evaluate_nll 호출)

### H.3. 사전 사용자 승인
- [ ] 본 문서 § G ranking과 새 axis가 일치하는지 확인
- [ ] 사용자에게 axis/value/예상 effect 보고
- [ ] 명시적 GO 사인 받은 후 수집 시작

### H.4. 수집 직후 검증
- [ ] `verify_split_integrity` (INVIOLABLE) PASS
- [ ] `verify_ood_severity` (delta_min 만족) PASS
- [ ] manifest hash 기록
- [ ] quality_report.json append
- [ ] transition magnitude 측정 (easy/hard 분류)

---

## I. Reviewer defense note

### I.1. 예상 공격 1: "OOD인데 왜 NLL이 더 낮아졌나?"
**답변**: action_gain=0.7과 같은 OOD는 state transition magnitude를 −29% 줄인다 (raw HDF5 측정값, `reports/R3_SMOKE_CLOSURE_REPORT.md` §E.3). ID로 학습된 모델의 σ̂²에 대해 OOD residual (x−μ)²가 체계적으로 작아져 Gaussian NLL이 더 음수가 된다. 이는 raw NLL이 OOD detection metric으로 불완전하다는 우리 논문의 핵심 동기이며, 본 finding이 β_t falsification gate의 도입을 직접 정당화한다.

### I.2. 예상 공격 2: "Easy-looking OOD에 맞춘 cherry-pick 아닌가?"
**답변**: 우리는 (a) easy-looking OOD (friction=5.0, gain=0.7)와 (b) hard OOD (stronger friction, gain=1.3, latency, multi-axis)를 별도로 정의하고 양 카테고리에서 β_t의 AUROC를 보고한다 (R4 evaluation plan §F.1). 양 카테고리 모두에서 raw NLL baseline을 능가하지 않으면 R4 PASS gate를 통과시키지 않는다.

### I.3. 예상 공격 3: "Mass OOD에서는 잘 안 되는 것 아닌가?"
**답변**: mass=1.5는 random policy에서는 transition magnitude를 거의 변화시키지 않음 (+1% / +2%, R3 measurement). 이는 mass effect가 contact-rich behavior에서 나타나기 때문이며, random policy 데이터의 본질적 한계이다. 우리는 이 점을 honest하게 보고하며, mass repair는 별도의 contact-rich/scripted policy track으로 분리한다 (현재 논문 범위 외).

### I.4. 예상 공격 4: "왜 latency / noise는 R3에서 안 했나?"
**답변**: R3는 base world model의 OOD detection 한계를 입증하는 단계이다. latency / noise / multi-axis OOD는 R4 evaluation 단계에서 β_t의 general capability를 측정하기 위해 별도 track으로 수집할 예정이다 (본 문서 §G ranking). R3에서 모든 axis를 수집하면 base WM 학습 시간이 길어지고 finding이 흐려진다.

---

## J. Open questions / UNKNOWN

다음은 본 문서가 답변하지 않으며 R4 이후 단계에서 결정될 사항이다.

| # | question | 결정 시점 |
|---|---|---|
| 1 | gain=1.3 (reverse direction)에서 base WM raw NLL이 실제로 정방향(ood > id)이 되는가? | R4 evaluation 직전 (data 수집 후 즉시 측정) |
| 2 | latency OOD에서 raw NLL은 일관되게 증가하는가? action delay step k가 몇부터 detect되는가? | R4 evaluation |
| 3 | multi-axis OOD에서 axis별 ρ_t group attribution이 어떻게 나뉘는가? | R5 causal attention evaluation |
| 4 | conformal calibration의 α를 0.05로 고정할 때 false-positive가 ID에서 정말 ≤ 0.05인가? | R4 calibration 단계 |
| 5 | mass axis의 contact-rich policy 데이터를 수집해야 한다면 그 cost는? | mass repair track 별도 plan |
| 6 | DROID/BridgeData 실데이터에서 friction/gain shift가 본 simulation finding과 같은 방향으로 작동하는가? | R12 |
| 7 | RGB-D 확장 시 transition magnitude metric이 raw state 대신 latent space에서도 동일하게 작동하는가? | R11 |

---

## K. 본 문서의 갱신 정책

- 본 문서는 R3 finding의 future implication을 기록하는 **insight 보존 문서**이다.
- 새 OOD axis 수집 시 (§H checklist 통과 후) §G ranking과 결과를 본 문서에 append한다.
- §J open question에 답이 나오면 해당 row에 결과를 기록하고 timestamp 추가.
- 본 문서가 R4/R5/R6 보고서에 인용될 때 SoT로 사용한다.

---

*Document created: 2026-05-24. Source: R3 two-axis smoke closure. Next update: after first new OOD axis data collection.*
