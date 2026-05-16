# Feasibility and Cost Audit Report
**Agent**: feasibility-and-cost-auditor (deep)
**Date**: 2026-05-16
**Session**: War Room R1

---

## CRITICAL FINDING: P3 Gate CC-P3-G3 FAIL

```
CLAIM: FEASIBILITY_CLAIM
RISK: CRITICAL
EVIDENCE:
  outputs/runs/p3_ablations/ablation_results.json:
    FRCG-FULL wrong_control_grammar_persistence = 1.9091 (all seeds)
    no_control_grammar persistence = 1.9091 (all seeds, DELTA=0)
    → CC-P3-G3 FAIL
  
  FRCG-FULL recovery_delay = 2.5455
  no_falsification recovery_delay = 2.5455 (DELTA=0)
    → CC-P3-G4 partial FAIL (falsification F1 collapses correctly, but recovery_delay identical)
  
  FRCG-FULL recovery_delay = 2.5455
  BASE-001 recovery_delay = 2.5455 (DELTA=0)
    → CC-P3-G1 FAIL (FRCG-FULL not beating verifier-only on recovery delay)
  
  manifest.json: n_steps=80, ~460k params, wall_clock_seconds=0.0 throughout
    → Model likely not doing real inference; random-init level losses
  
RECOMMENDATION:
  Investigate P3 gate sentinel discrepancy:
  - P3_EVAL.passed exists but CC-P3-G3/G1 data shows FAIL
  - Either: (1) gate was declared passed without checking ablation delta,
    or (2) a different eval run was used for gate pass decision
  
  Root cause hypotheses for delta=0:
  1. eval_labels.true_wrong_hypothesis field not populated → persistence = fixed value
  2. FRCG-FULL agent not calling model.forward() (B2 wrapper task not merged)
  3. 33 episodes all have same trajectory → no variance in metrics
  4. TextFRCGModelAgent has planning_calls=0 (still using heuristic)
  
ACTIONABLE_CODE_DIRECTION:
  Diagnostic: Check if planning_calls=0 in metrics.json for FRCG-FULL.
  If yes: B2 wrapper task (TASK_1020_TASK_1018_B2_frcg_agent_wrapper) needs merge.
  If metrics are all fixed: wrong_control_grammar_persistence implementation bug.
  
  Forward progress (independent of P3 gate issue): TASK_1021_A (GUI env data contract)
  can proceed in parallel since it doesn't require P3 gate pass.
  
VERIFICATION_PLAN:
  grep "planning_calls" outputs/runs/p3_eval/metrics.json
  Check TASK_1020_B2 status in codex_done/
  
VERDICT: CONDITIONAL
UNKNOWN_ITEMS:
  - Is P3_EVAL.passed based on the same run as ablation_results.json?
  - Is TASK_1020_B2 merged into codex-work?
  - wall_clock_seconds=0.0 — is this a logging bug or actual CPU-only 0s?
```

---

## Task A/B/C Recommendation

```
RECOMMENDED_CODEX_TASK: A

Reason 1: Task A (GUI env schema + leakage + replay) is independent of P3 gate issue
  and provides forward progress toward P4 CC-P4-G1~G5.

Reason 2: Task C (smoke evaluator) would always produce FAIL verdict given P3 gate
  status — implementing it now provides no actionable insight until P3 root cause fixed.

Reason 3: Task B depends on Task A schema layer existing first; without it,
  B's leakage/replay acceptance criteria have no basis.
```

---

## 3-Hour Viability Evidence: INFEASIBLE

3시간 안에 "decisive viability 증거" 생성은 불가능.
- P3 gate 미통과 원인 자체가 미진단
- GUI viability는 P4 gate 통과 후

현실적 3시간 목표:
- Task A: GUI env data contract 준비 (30-60분)
- P3 gate 미통과 원인 진단 (diagnostic, 30분)
- 종합 verdict 작성

## Key File References
- `outputs/runs/p3_ablations/ablation_results.json` (CC-P3-G3 FAIL evidence)
- `outputs/runs/p3_smoke/manifest.json` (wall_clock=0.0, 460k params, 33 episodes)
- `paper_context_ref/13_CLAUDE_CODE_EXECUTION_ROADMAP_v1.md §9.6` (CC-P3-G5: gate fail = no VLM)
- `.agent_tasks/codex_queue/TASK_1020_TASK_1018_B2_frcg_agent_wrapper.md` (B2: unmerged?)
