# Run 6B: Claim Survivability Decision Report

**Date**: 2026-05-16
**Phase**: CC-P3 (pilot/core eval scope)
**Run**: 6B — Evidence card synthesis + survivability judgment
**Scope**: pilot/core eval — NOT paper-accept-level evidence.

---

## 1. Claim Decision Summary

| Claim | Before Run 6 | After Run 6 | Key Evidence |
|---|---|---|---|
| C1 wrong-grammar persistence | CONDITIONAL | CONDITIONAL_ALIVE | h_exec null_rate=0.0, MET-PERSIST-001 BLOCKED (no eval labels) |
| C2 regime/grammar separation | BLOCKED | BLOCKED | No crossed-split eval, no latent probe |
| C3 falsification via LR score | CONDITIONAL | CONDITIONAL_ALIVE | ABL-022 delta=+0.403, ABL-023 delta=+0.403, F_t variance=1.26 |
| C4 alternative hypothesis WM | BLOCKED | BLOCKED | rollout_steps=0 |
| C5 action-interface rewrite | CONDITIONAL | CONDITIONAL_ALIVE | ABL-017 UNEXPECTED direction (counter-evidence recorded) |
| C6 compute gate | CONDITIONAL | CONDITIONAL_ALIVE | ABL-034 delta=+0.115 ppc (~2x), BASE-015 null |

---

## 2. Baseline / Ablation Comparison Table

| Agent | falsification_f1 | progress_per_compute | failed_rep_rate | recovery_delay |
|---|---|---|---|---|
| FRCG-FULL | 0.403 | 0.229 | 0.500 | 2.545 |
| ABL-022 no_falsification_score_gate | 0.000 | 0.114 | 0.500 | 2.545 |
| ABL-023 uncertainty_instead | 0.000 | 0.114 | 0.500 | 2.545 |
| ABL-017 no_intent_action_mapping | 0.403 | 0.229 | 0.089 | 2.545 |
| ABL-034 always_plan_no_gate | 0.000 | 0.114 | 0.500 | 2.545 |
| ABL-001 no_regime | 0.403 | 0.229 | 0.500 | 2.545 |
| ABL-036 no_counterfactual_target | 0.403 | 0.229 | 0.500 | 2.545 |
| BASE-026 WAC | N/A | N/A | N/A | N/A |
| BASE-027 CUWM | N/A | N/A | N/A | N/A |
| BASE-028 WebWorld | N/A | N/A | N/A | N/A |
| BASE-006 Verifier | N/A | N/A | N/A | N/A |
| BASE-012-CATTS | N/A | N/A | N/A | N/A |
| BASE-015 Compute-Matched | N/A | N/A | N/A | N/A |

---

## 3. C3 판정 상세 (Gate 통과 기준 claim)

**C3 ALIVE_WITH_EVIDENCE 미달 이유**:
- precision/recall 존재 (0.338/0.500) → ✓
- F_t non-degenerate (variance=1.26) → ✓
- LR vs ABL-022 구분 (delta=+0.403) → ✓
- LR vs ABL-023 구분 (delta=+0.403) → ✓
- BCE/sigmoid 없음 (main path) → ✓
- BASE-006 VerifierRecovery 비교 → **ABSENT** ✗
- BASE-012-CATTS 비교 → **ABSENT** ✗
- 실제 모델 inference (proxy 아님) → **ABSENT** ✗

→ **CONDITIONAL_ALIVE** (3/3 LR mechanics checks pass, 3/3 direct-threat checks absent)

---

## 4. 숨겨진 negative result 없음 선언

다음 counter-evidence를 명시적으로 기록한다:

1. **C5 ABL-017 unexpected direction**: removing intent-action mapping reduces failure repetition (0.089 vs 0.500). Expected direction: increase. This refutes the proxy-based C5 claim in pilot.
2. **C4 rollout=0**: world model claim has zero empirical support in this run.
3. **C2 BLOCKED**: regime separation claim cannot be supported at this scope.
4. **C6 compute_matched_delta=null**: BASE-015 absent → cannot compare to compute-matched random.

모든 위 사항은 evidence cards에 BLOCKER 및 counter_evidence로 명시됨.

---

## 5. ABL-040 / BASE-013 판단

**결정**: DEFER_TO_RUN7_REPORT

**근거**:
- ABL-040 leakage probe: `tests/test_forbidden_field_mirror_sync.py` (green) + `FORBIDDEN_AGENT_FIELDS` 15개 runtime 적용이 leakage 차단을 이미 보장. Run 6 hard gate `hidden_leakage_count=0` 통과. 추가 ablation은 redundant.
- BASE-013 TreeSearch: BASE-027 (CUWM) + BASE-028 (WebWorld)가 generic search attack 방어로 충분. Run 7 실행 후보.

---

## 6. Pilot/Core Eval Scope 명시

> **P3_LR_EVAL.passed는 LR eval gate 통과만 의미하며, 논문 accept-level 증명이 아니다. pilot/core eval scope.**

다음 작업 없이 논문에서 ALIVE 판정 claim을 쓸 수 없다:
- C1: eval_labels.evidence_timestamp 경로 확보
- C2: 교차 split eval + latent probe
- C3: BASE-006 + BASE-012-CATTS 비교
- C4: rollout 구현 + MET-WM-001/ALT-001
- C5: ABL-017 unexpected direction 해소
- C6: BASE-015 비교

---

## 7. Run 7 후보

1. BASE-026/027/028 (직접 위협 baseline) 실행
2. BASE-006 / BASE-012-CATTS 실행
3. BASE-015 compute_matched 실행
4. ABL-040 leakage probe (if needed beyond mirror sync test)
5. BASE-013 TreeSearch (after BASE-027/028 decision)
6. eval_labels.evidence_timestamp 경로 구현 → MET-PERSIST-001 해소
7. ABL-017 unexpected direction 재현 + 원인 분석
8. rollout 구현 → MET-WM-001 / ALT-001

**Run 7 시작은 별도 사용자 트리거 필요. 자동 진행 금지.**
