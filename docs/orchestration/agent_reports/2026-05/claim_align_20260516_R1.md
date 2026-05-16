# Claim-Metric Alignment Audit Report
**Agent**: claim-metric-alignment-auditor (deep)
**Date**: 2026-05-16
**Session**: War Room R1
**Source**: TASK_1021_A pre-execution audit

---

## Executive Summary

- Claims fully aligned (metric+baseline+ablation): **NONE** (0/6)
- Claims with CRITICAL gaps (mechanism metric completely absent): **C2, C4**
- Total baselines implemented: 9/28 (32%)
- Total ablations implemented: 12/42 (29%)
- Total metrics implemented: 10/36 (28%)
- CRITICAL ablations implemented: 8/14 (57%)
- Direct-threat baselines (BASE-026/027/028): **0/3 (0%)** ← HIGHEST RISK

---

## Claim-by-Claim Results

### C1 — wrong-grammar persistence (PARTIAL)
```
CLAIM: C1
RISK: HIGH
EVIDENCE:
  MET-PERSIST-001: metrics.py:78 IMPLEMENTED
  MET-FAIL-002:    metrics.py:92 IMPLEMENTED
  MET-BELIEF-001:  MISSING (no posterior_log/h_exec_log tracking)
  BASE-001: baselines.py:83 IMPLEMENTED
  BASE-005: baselines.py:144 IMPLEMENTED
  BASE-009: baselines.py:159 IMPLEMENTED
  ABL-002:  ablations.py:82+248 IMPLEMENTED
  ABL-003:  ablations.py:95+260 IMPLEMENTED
  ABL-022:  MISSING (standalone — registry merges with ABL-016)
RECOMMENDATION:
  1. Add MET-BELIEF-001 (belief_update_delay using posterior_log/h_exec_log)
  2. Add ABL-022 as separate registry entry from ABL-016
ACTIONABLE_CODE_DIRECTION:
  - metrics.py: add belief_update_delay()
  - ablations.py ABLATION_REGISTRY: add "no_falsification_score_gate" tdd_ref=ABL-022
VERIFICATION_PLAN: test_metrics_compute_belief_update_delay, test_ablation_registry_includes_abl022
VERDICT: PARTIAL
UNKNOWN_ITEMS: ABL-022 intentionally merged with ABL-016?
```

### C2 — regime/grammar separation (CRITICAL GAPS)
```
CLAIM: C2
RISK: CRITICAL
EVIDENCE:
  MET-REC-001:    metrics.py:110 IMPLEMENTED
  MET-OOD-003:    MISSING (no ood_grammar_performance function)
  MET-LATENT-001: MISSING (no latent probe metric anywhere)
  BASE-009: baselines.py:159 IMPLEMENTED
  BASE-012: baselines.py:196 IMPLEMENTED
  BASE-013: MISSING (TreeSearchAgent)
  ABL-001:  MISSING (no_regime — cannot isolate regime factor)
  ABL-002:  ablations.py:82 IMPLEMENTED
  ABL-003:  ablations.py:95 IMPLEMENTED
  ABL-006:  ablations.py:108 IMPLEMENTED
RECOMMENDATION:
  Priority 1 CRITICAL: Add ABL-001 (no_regime) — blocks C2 factorization entirely
  Priority 2 HIGH: Add BASE-013 (TreeSearchAgent)
  Priority 3 HIGH: Add MET-OOD-003, MET-LATENT-001
ACTIONABLE_CODE_DIRECTION:
  - ablations.py ABLATION_REGISTRY: add "no_regime" tdd_ref=ABL-001
  - baselines.py: add TreeSearchAgent baseline_id=BASE-013
  - metrics.py: add ood_control_grammar_performance(), latent_factorization_probe()
VERIFICATION_PLAN: test_ablation_registry_includes_abl001, test_tree_search_baseline
VERDICT: PARTIAL (critical metric+ablation gaps)
UNKNOWN_ITEMS: MET-LATENT-001 formal definition not fully specified in §6
```

### C3 — action-effect falsification (PARTIAL)
```
CLAIM: C3
RISK: HIGH
EVIDENCE:
  MET-FALS-001: metrics.py:124 IMPLEMENTED
  MET-FALS-002: metrics.py:124 IMPLEMENTED
  MET-CAL-001:  metrics.py:151 IMPLEMENTED
  BASE-005: baselines.py:144 IMPLEMENTED
  BASE-006: MISSING (VerifierHeuristicRecoveryAgent)
  BASE-012: baselines.py:196 IMPLEMENTED
  ABL-016:  ablations.py:121 IMPLEMENTED
  ABL-022:  MISSING (see C1)
  ABL-023:  ablations.py:137 IMPLEMENTED
RECOMMENDATION:
  Priority 1 HIGH: Add BASE-006 (VerifierHeuristicRecoveryAgent)
  Priority 2 HIGH: Add ABL-022 (see C1)
ACTIONABLE_CODE_DIRECTION:
  - baselines.py: Add VerifierHeuristicRecoveryAgent baseline_id=BASE-006
VERDICT: PARTIAL
```

### C4 — alternative grammar rollout (CRITICAL GAPS)
```
CLAIM: C4
RISK: CRITICAL
EVIDENCE:
  MET-WM-001:  MISSING (no rollout_fidelity function; predicted_rollout not tracked)
  MET-ALT-001: MISSING (no alternative_adoption_rate function; alt_set not tracked)
  MET-REC-001: metrics.py:110 IMPLEMENTED
  BASE-009: baselines.py:159 IMPLEMENTED
  BASE-013: MISSING (TreeSearchAgent)
  BASE-014: baselines.py:219 IMPLEMENTED
  ABL-024:  ablations.py:157 IMPLEMENTED
  ABL-025:  ablations.py:171 IMPLEMENTED
  ABL-026:  ablations.py:185 IMPLEMENTED
  ABL-036:  MISSING (no_counterfactual_target)
RECOMMENDATION:
  Priority 1 CRITICAL: Add MET-WM-001 (rollout_fidelity) — mechanism metric absent
  Priority 2 CRITICAL: Add MET-ALT-001 (alternative_adoption_rate) — mechanism metric absent
  Priority 3 HIGH: Add ABL-036 (no_counterfactual_target), BASE-013
ACTIONABLE_CODE_DIRECTION:
  - metrics.py: add rollout_fidelity(episodes), alternative_adoption_rate(episodes)
  - ablations.py: add "no_counterfactual_target" tdd_ref=ABL-036
  - eval_runner.py: track predicted_rollout and counterfactual_effects
VERDICT: PARTIAL (mechanism metrics completely absent — phase-dependency gap for P3)
UNKNOWN_ITEMS: MET-WM-001/ALT-001 may require P4+ data with counterfactual labels
```

### C5 — grammar-conditioned rewrite (PARTIAL)
```
CLAIM: C5
RISK: HIGH
EVIDENCE:
  MET-FAIL-002:    metrics.py:92 IMPLEMENTED
  MET-REWRITE-001: MISSING (no rewrite_success_rate)
  MET-SWITCH-001:  metrics.py:204 IMPLEMENTED
  BASE-003: baselines.py:113 IMPLEMENTED
  BASE-004: MISSING (BaseLLMSelfCorrectionAgent)
  BASE-006: MISSING (see C3)
  ABL-017:  MISSING (no_L_intent_action_mapping, loss-level)
  ABL-035:  ablations.py:198 IMPLEMENTED
RECOMMENDATION:
  Priority 1 CRITICAL: Add ABL-017 (loss-level ablation — cannot separate training from inference)
  Priority 2 HIGH: Add BASE-004, BASE-006, MET-REWRITE-001
VERDICT: PARTIAL
```

### C6 — decision-relevant compute gate (PARTIAL)
```
CLAIM: C6
RISK: HIGH
EVIDENCE:
  MET-COMP-003: MISSING (compute_normalized_return)
  MET-COMP-004: metrics.py:185 IMPLEMENTED
  MET-COMP-007: metrics.py:191 IMPLEMENTED
  BASE-010: baselines.py:181 IMPLEMENTED
  BASE-012: baselines.py:196 IMPLEMENTED
  BASE-015: MISSING (ComputeMatchedRandomReallocationAgent)
  ABL-020:  MISSING (no_compute_penalty, objective-level)
  ABL-023:  ablations.py:137 IMPLEMENTED
  ABL-033:  ablations.py:234 IMPLEMENTED
  ABL-034:  ablations.py:208 IMPLEMENTED
RECOMMENDATION:
  Priority 1 HIGH: Add BASE-015 (compute-matched baseline — C6 comparison not falsifiable without it)
  Priority 2 HIGH: Add ABL-020 (no_compute_penalty)
VERDICT: PARTIAL
```

---

## CRITICAL Ablations Status (14 items)

| ABL | Description | Status |
|---|---|---|
| ABL-002 | no-control-grammar | IMPLEMENTED |
| ABL-003 | merged regime-control grammar | IMPLEMENTED |
| ABL-006 | collapsed latent | IMPLEMENTED |
| ABL-011 | no-action-effect-log | **MISSING** |
| ABL-015 | no L_control_grammar | **MISSING** |
| ABL-016 | no L_falsification | IMPLEMENTED |
| ABL-017 | no L_intent_action_mapping | **MISSING** |
| ABL-022 | no falsification score gate | **MISSING** |
| ABL-023 | uncertainty instead of falsification | IMPLEMENTED |
| ABL-024 | no alternative hypothesis | IMPLEMENTED |
| ABL-033 | no decision-relevance gate | IMPLEMENTED |
| ABL-034 | always-plan | IMPLEMENTED |
| ABL-035 | no action rewrite | IMPLEMENTED |
| ABL-040 | public evidence only / leakage probe | **MISSING** |

**8/14 CRITICAL ablations implemented. 6 MISSING.**

---

## Direct-Threat Baselines (BASE-026/027/028) — 0/3

- BASE-026 (WAC-style): MISSING
- BASE-027 (CUWM-style): MISSING
- BASE-028 (WebWorld-style): MISSING

**HIGHEST reviewer attack risk.**

---

## Escalation Items (for Main Claude → Codex)

1. ABL-001 (no_regime) → blocks C2 completely
2. MET-WM-001 + MET-ALT-001 → blocks C4 mechanism evidence
3. BASE-006 (VerifierHeuristicRecovery) → blocks C3/C5 defense
4. BASE-015 (ComputeMatchedRandom) → blocks C6 falsifiability
5. ABL-017 + ABL-022 standalone → blocks C1/C5 training/inference separation
6. ABL-011 + ABL-015 + ABL-040 → CRITICAL severity, all missing
7. BASE-026/027/028 → prerequisite for ATTACK-DEF-004

**Target files**:
- `src/frcgw/evaluation/baselines.py` — add BASE-004, 006, 013, 015, 026, 027, 028
- `src/frcgw/evaluation/ablations.py` — add ABL-001, 011, 015, 017, 020, 022, 036, 040
- `src/frcgw/evaluation/metrics.py` — add MET-WM-001, ALT-001, BELIEF-001, OOD-003, REWRITE-001, COMP-003, LATENT-001
