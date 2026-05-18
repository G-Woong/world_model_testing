# STEP 8 Team Agents Round 1 Synthesis

date: 2026-05-18
trigger: PHASE B (pre-Codex)
agents: 6 (mathematical-validity-critic, experiment-design-expander, feasibility-and-cost-auditor, frcgw-data-leakage-auditor, claim-metric-alignment-auditor, novelty-threat-scout)
phase_gate_target: P3_STEP8_FINAL_EVIDENCE_VALIDATION

---

## 1. Overall Round 1 Verdict

| Agent | Verdict | Critical Issues |
|---|---|---|
| mathematical-validity-critic | NEEDS_REVISION | L_falsification silently zero if F_t not computed in training loop |
| experiment-design-expander | INCOMPLETE_CRITICAL | ABL-015 naming error; v0_4 OOD structural gap |
| feasibility-and-cost-auditor | FEASIBLE | Gradient clipping needed; Stage A extend to 1000 steps |
| frcgw-data-leakage-auditor | PASS (code) / WARN (planned) | WACFaithful/CUWMFaithful leakage guards required |
| claim-metric-alignment-auditor | PARTIALLY_ALIGNED | correct_hypothesis_id missing from v0_4; FC-02 is PRELIMINARY_PROXY |
| novelty-threat-scout | NOVELTY_AT_RISK | StressWeb HIGH threat; WebUncertainty MED threat (both new) |

---

## 2. Critical Issues That BLOCK Codex Task Submission

### BLOCK-R1-001: L_falsification Silent Zero Risk (math-critic)
**Location**: `src/frcgw/training/train_text.py` — training loop
**Issue**: `compute_total_loss(F_t=None)` returns `_zero()`. If training loop doesn't compute F_t per batch and pass non-None, L_falsification is silently zero regardless of l_falsification=1.0 config weight.
**Action**: Codex Task 3 (TASK_1080) must: (a) verify train_text.py computes F_t = falsification_score(...) per batch, (b) add assertion `assert F_t is not None` when l_falsification > 0.
**Resolved in**: TASK_1080 — train_text.py now in FILES_ALLOWED

### BLOCK-R1-002: v0_4 OOD Grammar Structural Gap (exp-design)
**Location**: generator.py — OOD_GRAMMAR_FAMILIES = [FILTER_ACCORDION, NESTED_SCROLL]
**Issue**: These families CANNOT produce blocker_removed or delayed_effect. Policy mixture alone cannot fix this.
**Action**: TASK_1079 updated — generator must implement explicit effect_type stratification for OOD split (20% forced episodes).
**Resolved in**: TASK_1079 updated BACKGROUND + REQUIRED_IMPLEMENTATION

### BLOCK-R1-003: ABL-015 Naming Error (exp-design)
**Location**: `docs/orchestration/lr_alignment/35_step8_handoff.md` line 43-46
**Issue**: Handoff says "no_falsification_training_hard (l_falsification=0.0)" — WRONG. SSoT §8: ABL-015 = no L_control_grammar (l_control_grammar=0.0).
**Action**: TASK_1082 already correctly specifies l_control_grammar=0.0. Codex Task 5 TASK file is correct. Handoff document has naming error but does NOT propagate to Codex task.
**Resolved in**: TASK_1082 correct as-written; handoff doc error noted but non-blocking

### BLOCK-R1-004: correct_hypothesis_id Missing from v0_4 Generator (claim-metric)
**Location**: dataset generator → evaluation_labels output
**Issue**: C1 metric requires eval_labels.correct_hypothesis_id. Without it, all C1 episodes blocked.
**Action**: TASK_1079 updated — generator must emit correct_hypothesis_id in evaluation_labels.
**Resolved in**: TASK_1079 updated

---

## 3. High-Priority Issues (Address Before First Codex Run)

### HIGH-R1-001: Gradient Clipping Required (feasibility)
Add `torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)` to train_one_epoch() in train_text.py. The lr × 0.5 retry is insufficient if NaN comes from forward pass.
**Action**: Added to TASK_1080 FILES_ALLOWED + REQUIRED_IMPLEMENTATION.

### HIGH-R1-002: Stage A Extend to 1000 Steps (feasibility)
Original 500 steps = 1.1 epochs at v0_4 (3500 episodes). Insufficient for F_t convergence diagnosis. 1000 steps = 2.28 epochs.
**Action**: TASK_1080 Stage A config updated to max_steps: 1000.

### HIGH-R1-003: ABL-025 (random-alternative) + ABL-026 (no-rollout) Missing Runners (exp-design)
CLAUDE.md requires these families to have ≥1 runner. Neither in STEP 7 or STEP 8 plans.
**Action**: TASK_1081 now includes ABL-025 + ABL-026 as inference-time ablations.

### HIGH-R1-004: ABL-040 Injection May Be Inert (claim-metric)
LeakageSanityProbeAblation sets `_last_selected_hypothesis_id` AFTER act(). If eval_runner doesn't use this field for metric computation, positive control is inert.
**Action**: TASK_1081 includes ABL-040 injection validation test.

### HIGH-R1-005: FC-02 (C2) Cannot Be PRELIMINARY in STEP 8 (claim-metric)
FC-02 requires true regime_shift_f1 (deferred) + ABL-001/003 retrain (deferred). Max level: PRELIMINARY_PROXY.
**Action**: TASK_1085 evidence card template pre-populates FC-02 wording as PRELIMINARY_PROXY.

---

## 4. WACFaithfulCandidate / CUWMFaithfulCandidate Leakage Guards (leakage-auditor)

For TASK_1083:
- Both classes: `eval_labels` must be entirely ignored. Assert `not (FORBIDDEN_AGENT_KEYS & set(eval_labels or {}))`
- WACFaithfulCandidate: grammar posterior from `history_public` ONLY (no true_control_grammar)
- CUWMFaithfulCandidate: must NOT call GrammarEngine(grammar=true_grammar); simulated rollout from public action_type heuristics
- Both: approximation_level="partial" (honest)
- oracle_best_action and audit_metadata must be in v0_4 config forbidden_fields

---

## 5. Novelty Threat Update for STEP 9 (novelty-scout)

New papers requiring action in STEP 9 paper framing:
- StressWeb (2604.16385, Mar 2026) — HIGH: cite as primary motivation evidence. Remap perturbation = 92 consecutive wrong actions.
- WebUncertainty (2604.17821, Apr 2026) — MED: add as uncertainty-gate baseline competitor in STEP 10 eval
- BacktrackAgent (2505.20660, EMNLP 2025) — MED: cite in verification-cluster related work
- AgentProg (2512.10371, Dec 2025) — MED: distinguish from grammar-level posterior
- gWorld (2602.01576) — LOW: add to §RWG-002

Upgrades: ViMo, MobileDreamer, Code2World, AgentRx → CONFIRMED_PRIMARY

Action: paper_context_ref/** is FORBIDDEN in STEP 8. All updates deferred to STEP 9. Captured in TASK_1085 (38_step9_handoff.md).

---

## 6. Codex Task Readiness Status

| Task | Readiness | Blocking Agent Reports Resolved |
|---|---|---|
| TASK_1078 (C3 diagnostics) | READY | math_critic_step8_c3_gradient_R1 ✓ |
| TASK_1079 (v0_4 dataset) | READY (updated) | exp_design + leakage + claim-metric ✓ |
| TASK_1080 (long-horizon configs) | READY (updated) | feasibility + math-critic ✓ |
| TASK_1081 (full eval harness) | READY (updated) | exp-design (ABL-025/026) + claim-metric (ABL-040) ✓ |
| TASK_1082 (ABL-015 faithful) | READY | exp-design naming clarification ✓ |
| TASK_1083 (BASE-026/027) | READY | leakage + claim-metric + novelty-scout ✓ |
| TASK_1084 (C2/C5) | READY | claim-metric ✓ |
| TASK_1085 (evidence card) | READY | all agents ✓ |

All critical blocking issues resolved in task files. Recommend proceeding with Codex Tasks in execution order:
1. TASK_1078 (independent — C3 diagnostics only)
2. TASK_1079 (independent — v0_4 generator only)
3. TASK_1080 (independent — configs + train_text.py gradient clipping)
4. TASK_1082 (depends on TASK_1080 Stage B config existing)
5. TASK_1081 (depends on TASK_1079 ablations.py check)
6. TASK_1083 (depends on TASK_1079 baselines.py structure known)
7. TASK_1084 (depends on TASK_1080 metrics.py check)
8. TASK_1085 (depends on all agent reports — can run now with templates)

Tasks 1, 2, 3 can run CONCURRENTLY (no dependencies between them).
