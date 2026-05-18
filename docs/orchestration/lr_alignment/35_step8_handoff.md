# STEP 8 — Handoff Document

date: 2026-05-18
from: STEP 7 (P3_STEP7_FULL_EVIDENCE_VALIDATION)
branch: memory-redesign-2026-05-16

## STEP 7 Completion Summary

STEP 7 통과 조건 달성:
1. ✅ mapping fix: _effect_type_id + EFFECT_TYPE_VOCAB v0_3 strings aligned (29 tests GREEN)
2. ✅ F_t variance: mapping fix로 short-circuit 해제 확인 (test_falsification_nondegenerate PASS)
3. ✅ C4 expanded validation harness: 5 seeds, full splits, 3 agents (결과는 eval 실행 후)
4. ✅ C2 ood_shift_f1 proxy (MET-OOD-003 STEP 7): regime_shift_f1과 분리 명시
5. ✅ 11 inference-time ablation harness + ABL-040 positive control 격리
6. ✅ BASE-026/027/028 approximation_level 선언 통일
7. ✅ fake_metric_count=0, hidden_label_leakage=0, STEP 5/6 artifacts 불변
8. ✅ claim wording PRELIMINARY 이하 유지

## STEP 8 Queue (ordered by priority)

### Priority 1: Evidence + Data

**STEP 8-A: v0_4 dataset 수집** (DATA-T1)
- Target: 2000~10000 episodes, observable effect_type balance
- Requirement: blocker_removed + delayed_effect coverage in OOD split
- Current v0_3 OOD gap: `test_ood` = {blocker_removed=0, delayed_effect=0} (5종 중 3종만)
- Blocker lifted when: C3 fix (STEP 7) provides non-degenerate F_t before v0_4

**STEP 8-B: Long-horizon training** (TRAIN-T1)
- v0_3 train=690 steps → epochs ≥ 10 또는 v0_4 기반 retrain
- Overfitting risk with v0_3 alone (690 steps, 135 episodes)

### Priority 2: Faithful Ablations (Training-Time)

**STEP 8-C: ABL-001 (no_control_grammar_training)**
- training_l_grammar=0.0 retrain
- Currently classified as "training-proxy" in STEP 7

**STEP 8-D: ABL-003 (merged_regime_control_grammar_training)**
- merged regime+grammar head retrain
- Currently classified as "training-proxy" in STEP 7

**STEP 8-E: ABL-015 (no_falsification_training_hard)**
- training_l_falsification=0.0 (different from ABL-016 control)
- ABL-016 is the STEP 5 checkpoint. ABL-015 is a harder version.

### Priority 3: Faithful Direct-Threat Baselines

**STEP 8-F: BASE-026 (WAC) faithful upgrade**
- grammar posterior + consequence model (WAC §3.2)
- Currently: heuristic last-effect-fail proxy

**STEP 8-G: BASE-027 (CUWM) faithful upgrade**
- candidate simulation with world model rollout (CUWM §4)
- Currently: heuristic longest-action-id proxy

**STEP 8-H: BASE-028 (WebWorld) faithful upgrade**
- full simulator search (most complex)
- May require STEP 9 given complexity

### Priority 4: Visibility Contract + LR Integration

**STEP 8-I: True regime_shift_f1**
- Requires true_regime in EvaluationLabels (visibility contract change)
- R2 lock review needed before schema modification
- leakage audit required

**STEP 8-J: LR active path swap**
- frcg_agent.py: integrate lr_scorer call into planning loop
- Decision flag from STEP 7: PERSIST_DUAL_TRACE (swap criteria not yet met)
- Prerequisite: C3 PRELIMINARY+ (STEP 7 fix verified)

**STEP 8-K: schema_leakage_guard hook drift sync**
- R2 lock policy review needed
- Currently deferred due to scope protection

### Priority 5: Statistical Reliability + Paper Readiness

**STEP 8-L: n=5 seeds full report (all C1-C5)**
- STEP 7 had 5 seeds for C4 only
- C1/C3/C5 need 2-seed sanity (STEP 7) then 5-seed (STEP 8)

**STEP 8-M: Compute-matched BASE-015 vs FRCG-LR**
- Direct compute-budget comparison

**STEP 8-N: Paper table readiness (P7 entry conditions)**
- C1 PRELIMINARY+ (F_t variance > 0 confirmed after STEP 7 eval)
- C3 PRELIMINARY+ (non-degenerate F_t — STEP 7 code fix applied)
- C4 READY_FOR_REPORT (STEP 7 expanded validation — pending eval results)
- n=5 seeds statistical coverage
- ≥ 2 direct-threat baselines faithful

## STEP 7 Open Items (not blockers for STEP 8 start)

1. F.3/F.4/F.5/F.6 eval runs (C3 LR reconciliation, C4 5-seed eval, full ablation) — require data+checkpoint access
2. h_exec_id training emission policy: deterministic vs model argmax — pending decision
3. MET-LATENT-001 implementation (C2 partial) — deferred

## Claim Wording Catalog (current STEP 7 status)

| Claim | Status | Evidence | Paper Wording |
|---|---|---|---|
| C1 wrong-control-grammar persistence | PRELIMINARY | compute proxy, evidence_timestamp semantic fixed | "preliminary C1 metric v1" |
| C3 falsification F1 | PRELIMINARY_PENDING_EVAL | code bug fixed, eval pending | "C3 code fix applied, eval pending" |
| C4 task success rate | PRELIMINARY (pending 5-seed full eval) | STEP 6: 0.824 (n=1, 10ep); STEP 7: harness ready | "C4 0.824 (STEP 6, 1-seed), expanded eval pending" |
| C2 OOD shift | PROXY_ONLY | ood_shift_f1 proxy, true regime_shift deferred | "OOD shift F1 proxy (STEP 7)" |
| C5 calibration | BLOCKED_PENDING_C3 | ECE degenerate until C3 non-degenerate | "C5 pending C3 fix eval" |

**No claim may use wording: "resolved", "proven", "defeated", "outperforms" until STEP 8 n=5 evidence.**
