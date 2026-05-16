---
file_id: DEC-OPTION-B
title: Option B LR Alignment — Decision Record
phase: 0 (Decision Freeze)
run: 1
date: 2026-05-16
status: DECISION_RECORD
language: ko
type: not empirical result
---

# DEC_OPTION_B_LR_ALIGNMENT.md

**Phase**: 0 — Decision Freeze  
**Run**: 1  
**Date**: 2026-05-16  
**Status**: Option B selected  
**Type**: not empirical result — 이 파일은 연구 프로젝트의 공식 채택 결정을 기록하는 decision record다

---

## Section 1. Decision Summary

**Decision: Option B selected.**

Option B = 구현을 이론에 맞춘다.

| 항목 | 내용 |
|---|---|
| **Main path** | `LikelihoodRatioFalsificationScorer` |
| **Auxiliary / Ablation path** | `BCEBinaryFalsificationScorer` — ABL-022 / ABL-023 ablation으로 강등 |
| **Option A 처리** | Option A deferred. Phase 11 full eval에서 LR vs BCE mechanism delta 측정 후 재검토 가능 |
| **결정 유형** | not empirical result. 이 파일은 decision record다 |

**핵심 한 문장**: BCE를 LR approximation으로 약화해서 narrative만 수정하는 것이 아니라, `LikelihoodRatioFalsificationScorer`를 main path로 채택한다.

`BCEBinaryFalsificationScorer`는 이후 ABL-022 (no falsification score gate), ABL-023 (uncertainty instead of falsification) ablation으로 역할이 축소된다. 사라지는 것이 아니라 ablation 비교 대상으로 보존된다.

---

## Section 2. Why This Decision Exists

이 결정은 4개의 독립된 blocking evidence에 근거한다.

### 2.1 War Room R1 Verdict C / AT_RISK

출처: `docs/orchestration/agent_reports/synthesis/2026-05/war_room_R1_synthesis.md`

- Verdict: C (AT_RISK), Confidence: HIGH
- Claim survivability: 0 VIABLE / 2 CONDITIONAL (C3, C5) / 4 AT_RISK (C1, C2, C4, C6)
- FATAL_FLAW 4건 확인 (P4 GUI env 미구현, P3_EVAL invalid, h_exec trace 부재, BASE-026/027/028 미구현)

### 2.2 C3 LR Theory vs BCE Implementation Gap

출처: `docs/orchestration/agent_reports/2026-05/math_critic_20260516_R1.md` (C3 RISK HIGH)

- **이론**: `F_t = max_{h_alt ∈ A_t^H} [ell_t(h_alt) − ell_t(h_exec)]`  
  (근거: `paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md:172`)
- **구현**: `L_falsification = BCE(σ(F_t), y_wrong)`  
  (근거: `paper_context_ref/08_LOSS_REWARD_TRAINING_OBJECTIVE.md:208`)
- BCE-trained score가 true LR의 sufficient statistic인지 UNKNOWN
- 이론과 loss 형식의 불일치는 narrative 수정만으로 해결되지 않는다

### 2.3 P3_EVAL invalid: planning_calls=0

출처: `outputs/phase_gates/P3_EVAL.BLOCKED_planning_calls_zero.md`

- `planning_calls=0` across all 5 seeds
- FRCG-FULL metric = no_control_grammar metric (Δ=0): CC-P3-G1/G3/G4 FAIL
- Root cause: model weights at near-random-init level. `F_t`가 `tau_f`를 초과하지 못함
- `P3_EVAL.BLOCKED_planning_calls_zero.md`가 `P3_EVAL.passed`를 supersede한다
- **결론**: 현재 P3 결과는 논문 claim 근거로 사용 불가 (P3_EVAL invalid)

### 2.4 h_exec Trace Missing + Baseline-Only 전략 불충분

출처: `docs/orchestration/agent_reports/2026-05/reviewer2_20260516_R1.md` (Attack 2, REF-PROBLEM-012)  
출처: `docs/orchestration/agent_reports/2026-05/claim_align_20260516_R1.md`

- `selected_hypothesis_id` 필드가 step log에 populate되지 않음 → MET-PERSIST-001 계산 불가
- `h_exec` trace 없이 C1 persistence 주장 불가
- `LikelihoodRatioFalsificationScorer` 구현 없이 BASE-026/027/028만 추가해도 mechanism delta가 살아나지 않는다

---

## Section 3. Adopted Formal Direction

이 section은 design record다. 구현 상세는 `02_option_b_design_plan.md`에서 확장된다.

### 3.1 증거 가능도 (Evidence likelihood)

출처: `paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md §6.2 line 152`

```
ell_t(h) = log p_theta(e_t | H_{t-1}, a_{t-1}, h)
```

- `e_t` = action-effect evidence (observed public evidence)
- `H_{t-1}` = step t-1까지의 history
- `h` = 평가 대상 hypothesis

### 3.2 Falsification Score — Main LR Form

출처: `paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md §6.3 line 171`

```
F_t = max_{h_alt ∈ A_t^H} [ ell_t(h_alt) − ell_t(h_exec) ]
```

- `h_exec` = 직전 action 생성에 실제로 사용된 hypothesis (predicted trace only, NOT oracle label)
- `A_t^H` = alternative regime/control-grammar hypothesis set (NOT alternative action set)
- `F_t > 0` = 어떤 alternative hypothesis가 h_exec보다 evidence를 더 잘 설명함 → falsification 발생

### 3.3 h_exec 정의

- `h_exec` = predicted trace only. oracle label이 아님
- `FORBIDDEN_AGENT_FIELDS`의 `true_control_grammar`, `true_regime`과 혼동 금지
- `selected_hypothesis_id` 필드를 step log에 populate해야 h_exec trace가 기록됨

### 3.4 Posterior (Learned Approximation)

출처: `paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md §6.1 line 142`

```
b_t(z^r, z^g) = q_phi(z^r, z^g | H_t)
```

- exact Bayesian posterior가 아님
- `q_phi` = history encoder + latent posterior module의 learned approximation

### 3.5 Decision-Relevance Gate

출처: `paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md §6.5 lines 200–209`

```
ΔV_t = max_{h_alt∈A_t^H, a∈A} V(a, h_alt) − max_{a∈A} V(a, h_exec)

G_t = I[
    F_t > τ_f
    ∧ ΔV_t > τ_v
    ∧ P(action_switch | A_t^H, H_t) > τ_a
    ∧ ΔV_t − C_plan > 0
]
```

- `uncertainty > threshold` 단일 조건이 아님. 4개 조건의 conjunction

### 3.6 Action-Interface Rewrite

출처: `paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md §6.6`

```
a_exec = Rewrite(intent=i_t, base_action=a_base, selected_hypothesis=h*)
```

- C5와 연결. grammar-conditioned rewrite

---

## Section 4. Deferred Work

Run 1에서는 아래 작업을 하지 않는다.

| 항목 | Defer 대상 | 이유 |
|---|---|---|
| P3 retraining | Run 4 / Phase 8 | LR alignment gate (`05_lr_implementation_contract.md`) 없이 재학습 금지 |
| BASE-026/027/028 구현 | Run 5 / Phase 10 | `LikelihoodRatioFalsificationScorer` 없이 추가해도 mechanism delta 부재 |
| ABL-001/017/022/023/024 구현 | Run 5 / Phase 10 | LR 설계 이후 (Run 3/4/5) |
| Evidence Card 작성 | Run 2 / Phase 3 | Phase 3로 defer |
| Code implementation | Run 4 / Phase 8 | Phase 5 계약 이후 |
| paper_context_ref 수정 | Run 2 / Phase 4 | Phase 4 계획 + 사용자 승인 후 |

---

## Section 5. Global Constraint Impact

- Phase 2/3/.../12는 이 decision을 상위 결정으로 따른다
- `paper_context_ref/02, 07, 08, 09, 10, FINAL_RESEARCH_BLUEPRINT.md`의 LR/BCE 관련 refactor는 이 decision 기반으로 진행되나, Run 1에서는 paper_context_ref를 수정하지 않는다
- `BCEBinaryFalsificationScorer`는 삭제되지 않는다. ABL-022/ABL-023 ablation 역할로 보존된다
- Option A deferred: Phase 11 LR vs BCE 비교 결과 전까지 채택 불가

---

## Section 6. Stop Condition

이 decision record는 다음 조건 전까지 유효하다.

- **유지 조건**: Phase 11 full eval 완료 전
- **재검토 트리거**:
  1. Phase 11에서 LR scorer가 BCE와 mechanism delta가 통계적으로 구별되지 않는 경우
  2. Phase 11에서 ablation delta = 0 확정 (DEAD_COLLAPSED)
- **재검토 후 후보**:
  - Option A (BCE reframe) 채택
  - Claim C3 weakening
  - `LikelihoodRatioFalsificationScorer` 유지
- Phase 11 evidence 없이 이 결정을 번복하지 않는다

---

*이 파일은 decision record다. not empirical result.*  
*생성일: 2026-05-16 / Run 1 / Phase 0 산출물*  
*근거: `docs/orchestration/lr_alignment/00_OPTION_B_PHASE_ROADMAP.md` Section 4 Phase 0, Section 5 Run 1*
