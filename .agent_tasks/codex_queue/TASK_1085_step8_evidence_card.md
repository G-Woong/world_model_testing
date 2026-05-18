TASK_NAME: step8_evidence_card_scaffold
SANDBOX_MODE: bypass

BACKGROUND:
FRCG-WM STEP 8. Need evidence card template and STEP 9 handoff document. Claude fills real numbers after eval runs. Codex creates the template structure only.

GOAL:
Create two documentation scaffolds:
1. docs/orchestration/lr_alignment/37_step8_final_evidence_card.md (template)
2. docs/orchestration/lr_alignment/38_step9_handoff.md (STEP 9 queue)

FILES_ALLOWED:
- docs/orchestration/lr_alignment/37_step8_final_evidence_card.md (NEW)
- docs/orchestration/lr_alignment/38_step9_handoff.md (NEW)
- .agent_tasks/codex_done/TASK_1085_step8_evidence_card_RESULT.md

FILES_FORBIDDEN:
- everything else

REQUIRED_IMPLEMENTATION:

docs/orchestration/lr_alignment/37_step8_final_evidence_card.md:
Must include these 18 sections (template slots for Claude to fill):

1. Executive Summary (5 lines max, non-expert readable)
2. Verdict: ALIVE / AT_RISK / BLOCKED / PIVOT_REQUIRED
   - Confidence: HIGH / MEDIUM / LOW
   - Reason: [FILL AFTER EVAL]
   - Rubric applied: (ALIVE = C3 READY_CANDIDATE + C4 READY_FOR_REPORT + ≥1 faithful baseline + ABL-040 pass; AT_RISK = C3 PRELIMINARY+ + C4 PRELIMINARY + partial gap; BLOCKED = C3 BLOCKED post-Stage-B; PIVOT_REQUIRED = C3 BLOCKED + C4 DOWNSHIFT)
3. Repo State: before/after SHA, branch, scope
4. Data: v0_4 episodes, splits, coverage gate status, leakage audit result
5. Training: config, steps, epochs, losses, l_falsification, F_t variance, checkpoint, valid_trained_eval
6. C3 Final Status table: (condition | C3 F1 | F_t variance | wrong_prob diversity | status)
7. C4 Final Status table: (condition | C4 fidelity | ID | OOD | seeds | status)
8. C1/C2/C5 table: (Claim | Status | Evidence | Blocker)
9. Ablation Results: 11 inference + ABL-015 faithful + ABL-025/ABL-026 + ABL-040 + collapsed/survived
10. Direct-Threat Baselines: (BASE-026/027/028 | faithful level | result | reviewer risk)
11. Claim Readiness table: (Claim | Readiness | Paper wording allowed | Forbidden wording)
    - Note: FC-02 (C2) must be PRELIMINARY_PROXY, never PRELIMINARY
    - Note: StressWeb (2604.16385) should be cited as motivation evidence for C1/C3 claims
12. Tests: targeted / regression / failures / unrelated
13. Safety: leakage_count / fake_metric_count / forbidden_source / overwrite / Codex_outputs_write
14. Team Agents / Codex: used / tasks / accepted / rejected / red-team verdict
15. User Feedback Events: decisions / impact
16. Commit: hash / message / files
17. Final Human-readable Summary (5-10 lines)
18. STEP 9 Handoff: remaining blockers / paper rewrite / training / baselines / ICLR readiness

Each section header must include a "STATUS: [FILL AFTER EVAL]" placeholder.
The Claim Readiness table must pre-populate the "Forbidden wording" column:
  - ALL claims: "resolved", "proven", "defeated", "outperforms" → FORBIDDEN
  - C2 specifically: "defeats WAC", "outperforms CUWM", "superior to WebWorld" → FORBIDDEN
  - C2 wording: PRELIMINARY_PROXY (not PRELIMINARY)

docs/orchestration/lr_alignment/38_step9_handoff.md:
Must list the following STEP 9 queue items (from STEP 8 out-of-scope list + agent findings):

**Training-time retrain queue:**
- ABL-001 (no_regime) faithful retrain — CLAIM-EVAL-002 prerequisite
- ABL-003 (merged regime-control grammar) faithful retrain — CLAIM-EVAL-002 prerequisite

**Faithful baseline queue:**
- BASE-028 (WebWorld) faithful upgrade — simulator search complexity

**Visibility contract changes (R2 lock review required):**
- Add true_regime to EvaluationLabels EVALUATION_ONLY bucket → enables true regime_shift_f1
- schema_leakage_guard hook drift sync → update .claude/hooks after visibility.py if changed

**Metric queue:**
- true regime_shift_f1 (MET-OOD-003 faithful) implementation
- compute-matched BASE-015 vs FRCG-LR comparison

**Architecture queue:**
- LR active path swap: frcg_agent.py integrate lr_scorer into planning loop (condition: C3 PRELIMINARY+)
- h_exec_id training emission policy decision (deterministic vs model argmax)

**Paper framing queue (STEP 9 novelty):**
- Update 01_RELATED_WORK_THREAT_MAP.md: add StressWeb (CITE-019, HIGH), BacktrackAgent (CITE-020), WebUncertainty (CITE-021), gWorld (CITE-022), AgentProg (CITE-023)
- Upgrade PARTIALLY_CONFIRMED → CONFIRMED_PRIMARY: ViMo, MobileDreamer, Code2World, AgentRx
- Cite StressWeb as primary motivation in §RWG-005 (Remap perturbation = 92 consecutive wrong actions)
- Add WebUncertainty as uncertainty-gate baseline competitor in STEP 10 evaluation plan
- Add ATK-NEW-001 through ATK-NEW-006 to reviewer attack ledger

**ICLR readiness gate conditions:**
- C3 READY_CANDIDATE (F_t variance > 0.01 confirmed on n=5 seeds)
- C4 READY_FOR_REPORT (0.824 level maintained or higher)
- ABL-003 faithful retrain PASS (CLAIM-EVAL-002)
- True regime_shift_f1 implemented (C2 not PROXY)
- ≥2 faithful direct-threat baselines
- n=5 seed full report with all C1-C5

REQUIRED_TESTS:
None required (documentation only).

ACCEPTANCE_CRITERIA:
1. 37_step8_final_evidence_card.md exists with all 18 sections + placeholder slots
2. 38_step9_handoff.md exists with full STEP 9 queue
3. Forbidden wording column pre-populated in Claim Readiness table
4. FC-02 explicitly marked PRELIMINARY_PROXY in template

COMMIT_MESSAGE:
docs(step8/task8): final evidence card template + STEP 9 handoff scaffold

STOP_CONDITION:
None (documentation only task).

RELATED_AGENT_REPORT_IDS: exp_design_step8_v04_ablation_R1, claim_metric_step8_alignment_R1, novelty_step8_threat_R1
