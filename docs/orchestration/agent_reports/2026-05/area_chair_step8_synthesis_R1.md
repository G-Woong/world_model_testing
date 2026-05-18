# Area Chair Synthesis: STEP 8 Final Evidence

**report_id**: area_chair_step8_synthesis_R1
**date**: 2026-05-18
**trigger**: T4 deep (결과 해석 전)
**verdict**: AT_RISK
**confidence**: MEDIUM

---

## Conflicting Opinion Resolutions

### Dispute 1: Task Success Rate as Signal

**Resolution**: task_success_rate is NON_DISCRIMINATIVE in this evaluation setup (ceiling effect — all ablations including oracle probe ABL-040 score 0.994/0.998). C6 progress_per_compute (93% gap: FRCG-LR 0.221 vs ABL-036 0.015) is a distinct, legitimate discriminative metric. These are not in conflict. Paper must label task_success results as NON_DISCRIMINATIVE and route compute-gate evidence through C6/ppc.

### Dispute 2: C3 Falsification — Mechanism vs Metric

**Resolution**: BLOCKED verdict is premature. Training evidence confirms non-degenerate F_t (variance=0.191, l_falsification=0.635). Eval degeneration (falsification_precision=0.0, predicted_wrong true_count=0) has three candidate root causes:
1. ABL-040 injection may be inert in eval_runner.py — if so, positive control validation chain is suspect
2. Training-to-inference path divergence for predicted_wrong flag
3. math_critic: potential silent l_falsification=0 if F_t=None passed to compute_total_loss()

**C3 status = PRELIMINARY_PENDING_EVAL, not BLOCKED.** Root cause audit (Gate O4) is the decision point.

### Dispute 3: BASE-026/027 Adequacy

**Resolution**: Acceptable if forbidden wording enforced + comparison extends beyond task_success to persistence + recovery_delay + falsification + ppc. approximation_level=heuristic must be visible in all tables.

---

## Final Verdict: AT_RISK

**Positive evidence:**
- F_t training non-degenerate (variance=0.191)
- l_falsification non-zero in training (0.635)
- C6 ppc 93% gap (strongest positive signal)
- VOCAB fix mathematically validated
- ABL-015 training-time differentiation works (l_control_grammar 2.075 vs 0.055)

**Risk evidence:**
- C3 eval degenerate (falsification_precision=0.0, predicted_wrong true_count=0)
- task_success NON_DISCRIMINATIVE (ceiling effect, NOT a performance failure)
- n=5 seeds missing for statistical reliability
- ABL-040 injection may be inert (eval harness propagation unverified)
- FC-02 C2 = PRELIMINARY_PROXY only

**Why not ALIVE**: C3 READY_CANDIDATE and n=5 stats not met.
**Why not BLOCKED**: Training mechanism alive (F_t variance > 0), root cause unidentified, resolution paths exist.

---

## Paper Claim Wording Catalog

| Claim | Status | Permitted | Forbidden |
|---|---|---|---|
| C1 wrong-grammar persistence | PRELIMINARY (conditional on correct_hypothesis_id) | "preliminary persistence_v1 metric" | "resolved", "proven", "measured at N steps" |
| C2 OOD separation | PRELIMINARY_PROXY | "ood_shift_f1 proxy, STEP 7" | "confirmed", "demonstrated", PRELIMINARY label |
| C3 falsification | PRELIMINARY_PENDING_EVAL | "training F_t non-degenerate (variance=0.191), eval pending root cause" | "falsification demonstrated on eval", "precision=[any positive]" |
| C4 task success | NON_DISCRIMINATIVE | "ceiling effect — non-discriminative in current setup" | Citing tsr as positive evidence |
| C5 calibration | BLOCKED_PENDING_C3 | "blocked pending C3 non-degenerate eval" | Any ECE reporting |
| C6 compute gate | PRELIMINARY | "ppc 93% gap (n=1 seed), preliminary compute-gate evidence" | "proven", "defeats", "superior" |
| BASE-026/027 | PARTIAL | "approximation_level=heuristic" qualifier required | "defeats WAC", "outperforms CUWM", "superior to WebWorld" |

---

## Top 3 STEP 9 Priorities

1. **C3 root cause**: Assert F_t is not None in training. Verify ABL-040 injection propagates to metric output. Gate O4: falsification_precision > 0.
2. **v0_4 correct_hypothesis_id**: Add to evaluation_labels — without it all C1 episodes BLOCKED.
3. **ABL-001/003 + true regime_shift_f1**: R2 lock review for true_regime. Implement regime_shift_f1. Faithful retrains for CLAIM-EVAL-002.

---

## Escalation Note

ABL-040 injection inertness is the most dangerous operational risk. If eval_runner.py doesn't propagate `_last_selected_hypothesis_id` to metric computation, the entire eval harness validation chain is suspect. This must be verified FIRST in STEP 9.
