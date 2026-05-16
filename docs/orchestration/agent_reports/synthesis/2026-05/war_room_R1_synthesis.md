# War Room R1 — Area Chair Synthesis Report
**Agent**: area-chair-synthesis-agent (deep)
**Date**: 2026-05-16
**Session**: War Room R1
**Inputs**: 7 deep critic reports

---

## Verdict: C (AT RISK)
## Confidence: HIGH

---

## Consensus Items (모든 에이전트 동의)

1. **P4 GUI env 0% implemented** — PAPER_KILLER without P4. (reviewer2 Attack 4, exp_design, feasibility)
2. **BASE-005 VerifierOnlyAgent = string-length heuristic** (code confirmed: picks longest action_id)
3. **BASE-026/027/028 (WAC/CUWM/WebWorld) 0% implemented** (claim_align, exp_design, reviewer2)
4. **h_exec trace not populated → MET-PERSIST-001 uncomputable** (reviewer2 REF-PROBLEM-012)
5. **P3_EVAL.passed is INVALID** — planning_calls=0 for FRCG-FULL across all seeds; all mechanism metrics identical to all baselines (metrics.json direct evidence)
6. **C2 identifiability is CRITICAL risk** — Locatello impossibility, ABL-001 missing, 1:1 mapping risk (math_critic, claim_align, exp_design)

---

## Conflict Resolution

**CONFLICT 1: P3 gate 유효성**
→ RESOLUTION: feasibility_auditor WINS. metrics.json is definitive. planning_calls=0 all seeds. P3_EVAL.passed treated as INVALID until B2 merge confirmed + re-run.

**CONFLICT 2: TASK_1021_A 즉시 실행 가능성**
→ RESOLUTION: NOT a real conflict. impl_risk's FILES_FORBIDDEN fix is pre-execution fix. feasibility's "proceed immediately" is correct after fix. claim_align's baseline priority runs in parallel. TASK_1021_A proceeds with FILES_FORBIDDEN additions applied.

**CONFLICT 3: Novelty 생존 여부 (severity framing difference)**
→ RESOLUTION: CONVERGENT. 4 surviving novelty items identified (wrong-grammar persistence metric, LR falsification ≠ binary verification, grammar-conditioned alternative hypothesis rollout, grammar-conditioned intent-to-action rewrite). 3 new threats (CATTS/VLAA-GUI/WebUncertainty) unaddressed.

**CONFLICT 4: C2 identifiability**
→ RESOLUTION: CONVERGENT_CRITICAL from all 3 agents independently.

---

## Claim-by-Claim Survivability

| Claim | Math | Align | Exp | Rev2 | Nov | **Overall** |
|---|---|---|---|---|---|---|
| C1 | CONDITIONAL (oracle-dependent) | PARTIAL | INCOMPLETE (h_exec) | AT_RISK | SURVIVABLE | **AT_RISK** |
| C2 | CONDITIONAL_CRITICAL (Locatello) | CRITICAL (ABL-001) | CRITICAL (1:1 map) | FIXABLE | SURVIVABLE | **AT_RISK** |
| C3 | CONDITIONAL (LR vs BCE gap) | PARTIAL | INCOMPLETE | AT_RISK | SURVIVABLE | **CONDITIONAL** |
| C4 | CONDITIONAL (horizon) | CRITICAL (MET-WM-001) | INCOMPLETE | AT_RISK | SURVIVABLE | **AT_RISK** |
| C5 | CONDITIONAL (best claim) | PARTIAL (ABL-017) | INCOMPLETE | AT_RISK | SURVIVABLE | **CONDITIONAL** |
| C6 | CONDITIONAL (VOC overstated) | PARTIAL (BASE-015) | INCOMPLETE | AT_RISK | **AT_RISK** (CATTS) | **AT_RISK** |

**0 VIABLE, 2 CONDITIONAL (C3/C5), 4 AT_RISK (C1/C2/C4/C6)**

---

## FATAL_FLAW Items (blocking submission)

1. P4 GUI env = 14-line stub. "Web/GUI agent paper" framing unjustifiable.
2. P3_EVAL.passed is invalid (planning_calls=0, all metrics identical).
3. h_exec trace not populated → MET-PERSIST-001 uncomputable.
4. BASE-026/027/028 0% implemented → ATTACK-DEF-004 unanswerable.

---

## Critical Gap Items (blocking strong paper)

1. C2 identifiability: ABL-001 missing, MET-LATENT-001 missing, crossed split absent.
2. C3 theory-impl gap: LR theory vs BCE implementation. Resolution: claim reframe or add LR scorer.
3. 3 new unregistered threats: CATTS (2602.12276), VLAA-GUI (2604.21375), WebUncertainty (2604.17821).
4. ABL-017 + ABL-022 standalone: both MISSING (block training/inference separation arguments).
5. `test_ablation_runner.py` hardcodes `len(ABLATION_REGISTRY) == 12` — ESCALATION FLAG.
6. TASK_1021_A FILES_FORBIDDEN missing: visibility.py, step_schema.py, validation.py, episode_schema.py.

---

## Next 3 Decisions Required

1. **P3_EVAL.passed — invalidate or retest?** (Must decide before ANY P4 work) → Recommended: INVALIDATE, diagnose planning_calls=0, re-run after B2 merge confirmed.

2. **Paper framing — "Web/GUI agent paper" or "controlled study + GUI as future work"?** → 3 paths (reviewer2 Attack 4). Decides scope of all downstream Codex tasks.

3. **C3 theory-implementation gap resolution — claim reframe or change loss?** → Decides whether paper_context_ref edit (needs user approval) or narrative reframing only.

---

## Recommended Actions (Priority Order)

1. **IMMEDIATE**: Diagnose planning_calls=0 root cause in FRCG-FULL (B2 merge, model.forward() call path, gate condition threshold)
2. **IMMEDIATE**: Invalidate P3_EVAL.passed. Do not proceed to P4 under false gate.
3. **HIGH**: Apply impl_risk FILES_FORBIDDEN additions to TASK_1021_A, then execute.
4. **HIGH**: Add ABL-001 (no_regime) to ABLATION_REGISTRY + update test_ablation_runner.py count simultaneously.
5. **HIGH**: Add MET-WM-001 (rollout_fidelity) + MET-ALT-001 (alternative_adoption_rate) to metrics.py.
6. **HIGH**: Add BASE-026/027/028 stubs to baselines.py.
7. **HIGH**: Add CATTS/VLAA-GUI/WebUncertainty to related work threat map (requires user approval as paper_context_ref/ edit).
8. **MED**: Resolve C3 LR vs BCE gap (claim reframe).
9. **MED**: Add h_exec trace (selected_hypothesis_id) to step log + all agent.act() calls.
10. **MED**: Add ABL-011/015/017/022/040 in single Codex task (co-update test_ablation_runner.py count).

---

## Session Verdict Grade: C

C — 2 conditionally defensible claims (C3, C5), 4 AT_RISK (C1/C2/C4/C6). P3 gate invalid (planning_calls=0). P4 missing. 3 new unregistered threats. Major revision required on 4 independent blocking dimensions before ICLR submission is possible.
