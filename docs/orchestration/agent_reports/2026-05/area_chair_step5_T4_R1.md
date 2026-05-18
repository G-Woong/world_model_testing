# Area Chair Synthesis — STEP 5 Claim Wording (T4, deep mode)

**Date**: 2026-05-18
**Agent**: area-chair-synthesis-agent (T4)
**Input**: T2 agent reports (claim_metric, experiment_design, feasibility)
**Verdict**: MAJOR_REVISION

---

## Claim-Level Verdicts

| Claim | Permitted Wording | Forbidden |
|---|---|---|
| C1 (persistence) | "preliminary evidence" with scope: "smoke-only, not mechanism evidence" | Quoting numeric persistence values as mechanism evidence |
| C2 (regime) | N/A (out of scope) | N/A |
| C3 (falsification divergence) | "audit-only observation; F_t_planner=0.0 due to l_falsification=0; active path unchanged" | Any positive quantitative finding; "C3 resolved" |
| C4 (rollout fidelity) | "deferred; BLOCKED_no_model_rollout_prediction" | ANY computation or "preliminary evidence" |
| C5 (calibration) | "detector repaired; non-degenerate calibration claim deferred pending production training" | "C5 resolved", "model shows non-degenerate calibration" |

## ABL-011/015/040 Wording
Dispatch infrastructure in progress (TASK_1054 complete). Results cannot be reported until STEP 6 execution.
Paper must state: "11/14 critical ablations implemented; 3 pending execution (ABL-011/015/040)."

## valid_trained_eval: True
Legitimate disclosure improvement. Must NOT be conflated with mechanism validation.
Wording: "Checkpoint-based eval enabled (STEP 5); production-scale mechanism evidence deferred."

## Top 3 Priorities for Main Claude

1. **C4 claim containment**: Label BLOCKED_no_model_rollout_prediction in all reports; no C4 numeric results
2. **C5 wording firewall**: AND→OR fix = detector repair, NOT calibration proof; add comment to _compute_c5_status
3. **STEP 6 l_falsification**: CRITICAL — enable l_falsification > 0; relabel current checkpoint as ABL-010

## Overall STEP 5 Acceptability

MAJOR_REVISION — Infrastructure sound; claim wording requires enumerated qualifiers.
No escalation to REJECT: all gaps have STEP 6 resolutions.
