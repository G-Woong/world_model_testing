# Mass OOD Root Cause Analysis — Synthesis Report

**보고일**: 2026-05-24  
**트리거**: T4 — 결과 해석 전 (ood_severity FAIL RC1 분석)  
**입력 보고서**: Agent 1~4 (metric-validity, dynamics-forensics, novelty-relevance, repair-options)  
**담당**: area-chair-synthesis-agent (Agent 5)  
**소스**: G.1~G.5 forensic 분석, Scaled 450ep 데이터  

---

## 핵심 분석 요약

### 4개 Agent 수렴 결론

| 확정 사실 | 증거 | 신뢰도 |
|---|---|---|
| contact_rate = 0.0% (tcp_dist=0.999m, ALL splits) | G.3 직접 측정 | 고 |
| PickCube-v1 random policy: cube 미접촉 | G.3 | 고 |
| friction 작동: joint friction → qvel 직접 영향 (gap 0.071~0.128) | G.1 | 고 |
| mass 미작동: contact force 경로 차단됨 | G.1, G.3 | 고 |
| Pilot 90ep gap=0.0148 PASS: n=10 variance | Agent 1 + R1 보고서 | 고 |
| object_pose_delta_norm gap = 0.000136 (near-zero) | G.2 | 고 |
| dim24 Cohen's d=1.034: 수치적 artifact (abs=4e-6) | G.5 + Agent 1/2 | 고 |
| reward_max gap=0.24이나 KS p=0.107 (not significant) | G.4 | 중 |

**dominant cause: B1 (Data: zero contact) + B4 (Env: PickCube+random policy)**

FGLC novelty:  
- C1~C4: friction/latency/noise axis로 모두 방어 가능  
- C5 (5-axis benchmark)만 직접 위험  
- 6개 직접 위협 모두 friction-primary 전략으로 방어 가능 (교차검증 완료)

---

## Reviewer 2 공격 평가표

| 전략 | p-hacking | selective | neg.숨김 | Reviewer 2 반론 | 방어력 |
|---|---|---|---|---|---|
| threshold 완화 | 0.90 | 0.80 | 0.85 | "gap=0.00375를 임계값 이동으로 PASS 처리 = p-hacking" | WEAK |
| E.1 composite | 0.75 | 0.70 | 0.60 | "gap=0.000136 metric 추가 = zero to zero" | WEAK |
| E.7+E.2 (friction-only R3) | 0.10 | 0.30 | 0.25 | "5-axis 주장인데 mass가 missing" | MODERATE |
| E.4 PushCube probe | 0.35 | 0.45 | 0.30 | "task selection post-hoc, PickCube FAIL 충분히 보고 필요" | MODERATE |
| F.1 mass=3.0 | 0.65 | 0.60 | 0.55 | "FAIL까지 mass를 높이다가 PASS 지점 선택" | WEAK~MODERATE |

---

## 최종 Option 선정

### Option 1 (최우선 추천): E.7 + E.2 + E.4 순차

```
Option 1:
- 전략: friction-only R3 smoke (즉시) + mass secondary tier 기록 + PushCube-v1 probe (1~2시간)
- 리뷰어 공격: "5-axis benchmark에서 mass가 secondary/deferred이면 overclaiming"
- 방어 논리: "friction/latency/noise 3축이 FGLC C1~C4를 완전히 검증하며,
              mass axis는 contact-dependent 특성상 PushCube-v1에서 보완 검증;
              PickCube random policy에서의 contact 부재를 논문에 투명하게 명시"
- 단점 1: PushCube probe FAIL 시 C5 주장 완화 필요
- 단점 2: R4에서 mass axis 해결 약속 이행 부담
- ICLR accept 영향: neutral (friction-only R3 자체로 충분한 증거; mass는 honest limitation)
```

### Option 2 (대안): E.4 우선 + E.7 fallback

```
Option 2:
- 전략: PushCube-v1 probe 먼저 (1~2시간) → gap≥0.01이면 mass 구제, FAIL이면 E.7+E.2
- 방어 논리: "PushCube는 18_DATA_BENCHMARKS.md:54 허용, contact-mediated mass dynamics
              검증에 적합한 task; PickCube FAIL을 Section 4에 명시"
- 단점 1: PickCube FAIL 미명시 시 selective reporting 의심 급등
- 단점 2: PushCube probe FAIL 시 시간 소비 후 Option 3으로 전환
- ICLR accept 영향: positive (probe PASS) / neutral (FAIL 후 E.7 전환)
```

### Option 3 (즉시 실행 시): E.7 + E.2 단독

```
Option 3:
- 전략: friction-only R3 즉시, mass 완전 보류 (PushCube probe 없음)
- 방어 논리: "C1~C4가 friction/latency/noise로 완전 검증됨; mass는 R4+ deferred"
- 단점 1: C5 주장 문구 완화 동반 (5-axis → 4 primary axes)
- 단점 2: reviewer "why not fix mass OOD?" 답변 약해질 수 있음
- ICLR accept 영향: neutral → negative (C5 약화 수준에 따라)
```

---

## BACKBONE_CHANGE 판단

| 질문 | 판정 | 근거 |
|---|---|---|
| mass axis 즉시 폐기 필요? | **아니오** | oracle-mass baseline 무의미화, E.2 secondary tier가 안전 |
| 18_DATA_BENCHMARKS.md:44 수정 필요? | **현재 불필요** | Option 1~3 모두 SSoT 범위 내 |
| friction-only R3 = BACKBONE 변경? | **아니오** | R3 phase gate 세부 조건 조정, 핵심 claim 수식/metric 정의 불변 |

**BACKBONE_CHANGE 형식 불필요** — Option 1~3 모두 자체 수용 가능 영역.

F.1 (mass=3.0) 채택 필요 시: BACKBONE_CHANGE 형식 사용자 승인 필요 (18_DATA_BENCHMARKS.md fragile file).

---

## 사용자 결정 필요 사항

1. **R3 진행 경로**: Option 1 (추천) / Option 2 / Option 3 중 선택
2. **PushCube probe 경계 조건**: gap=0.01~0.02 (borderline) 시 어떻게 처리?
3. **F.1 대기선**: E.4 probe FAIL 시 mass=3.0 + 18_DATA_BENCHMARKS.md 수정 승인 여부

---

## ANALYSIS_PASS 판정

- Agent 1~4 보고서 5종 모두 작성됨 ✓
- dominant cause 확정: B1+B4 (Data/Env artifact) ✓  
- 후속 적용 후보 ≥1개 식별됨 (E.7+E.2+E.4) ✓
- negative result 숨김 없음 ✓
- 사용자 보고 §I 형식 준비됨 ✓

**final_acceptability: MAJOR_REVISION** (R3 friction-only 진행 가능, mass C5 주장 완화 필요)
