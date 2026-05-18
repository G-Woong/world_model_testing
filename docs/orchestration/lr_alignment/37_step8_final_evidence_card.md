# STEP 8 Final Evidence Card Template

date: [FILL AFTER EVAL]
branch: [FILL AFTER EVAL]
owner: Claude final evaluator
scope: Template scaffold only. Replace every `[FILL AFTER EVAL]` slot after STEP 8 evaluation runs complete.

## 1. Executive Summary - STATUS: [FILL AFTER EVAL]

5 lines max, non-expert readable.

1. [FILL AFTER EVAL]
2. [FILL AFTER EVAL]
3. [FILL AFTER EVAL]
4. [FILL AFTER EVAL]
5. [FILL AFTER EVAL]

## 2. Verdict: ALIVE / AT_RISK / BLOCKED / PIVOT_REQUIRED - STATUS: [FILL AFTER EVAL]

- Verdict: ALIVE / AT_RISK / BLOCKED / PIVOT_REQUIRED
- Confidence: HIGH / MEDIUM / LOW
- Reason: [FILL AFTER EVAL]
- Rubric applied:
  - ALIVE = C3 READY_CANDIDATE + C4 READY_FOR_REPORT + [FILL AFTER EVAL] faithful direct-threat baseline + ABL-040 pass
  - AT_RISK = C3 PRELIMINARY+ + C4 PRELIMINARY + partial gap
  - BLOCKED = C3 BLOCKED post-Stage-B
  - PIVOT_REQUIRED = C3 BLOCKED + C4 DOWNSHIFT

## 3. Repo State: before/after SHA, branch, scope - STATUS: [FILL AFTER EVAL]

| Field | Value |
|---|---|
| Before SHA | [FILL AFTER EVAL] |
| After SHA | [FILL AFTER EVAL] |
| Branch | [FILL AFTER EVAL] |
| Scope executed | [FILL AFTER EVAL] |
| Out-of-scope items confirmed deferred | [FILL AFTER EVAL] |
| Dirty tree before final commit | [FILL AFTER EVAL] |
| Dirty tree after final commit | [FILL AFTER EVAL] |

## 4. Data: v0_4 episodes, splits, coverage gate status, leakage audit result - STATUS: [FILL AFTER EVAL]

| Field | Value | Evidence path |
|---|---|---|
| v0_4 total episodes | [FILL AFTER EVAL] | [FILL AFTER EVAL] |
| Train split | [FILL AFTER EVAL] | [FILL AFTER EVAL] |
| Validation split | [FILL AFTER EVAL] | [FILL AFTER EVAL] |
| Test ID split | [FILL AFTER EVAL] | [FILL AFTER EVAL] |
| Test OOD split | [FILL AFTER EVAL] | [FILL AFTER EVAL] |
| blocker_removed OOD coverage | [FILL AFTER EVAL] | [FILL AFTER EVAL] |
| delayed_effect OOD coverage | [FILL AFTER EVAL] | [FILL AFTER EVAL] |
| Coverage gate status | [FILL AFTER EVAL] | [FILL AFTER EVAL] |
| Leakage audit result | [FILL AFTER EVAL] | [FILL AFTER EVAL] |

## 5. Training: config, steps, epochs, losses, l_falsification, F_t variance, checkpoint, valid_trained_eval - STATUS: [FILL AFTER EVAL]

| Field | Value | Evidence path |
|---|---|---|
| Training config | [FILL AFTER EVAL] | [FILL AFTER EVAL] |
| Steps | [FILL AFTER EVAL] | [FILL AFTER EVAL] |
| Epochs | [FILL AFTER EVAL] | [FILL AFTER EVAL] |
| Final total loss | [FILL AFTER EVAL] | [FILL AFTER EVAL] |
| Final l_falsification | [FILL AFTER EVAL] | [FILL AFTER EVAL] |
| F_t variance | [FILL AFTER EVAL] | [FILL AFTER EVAL] |
| Checkpoint | [FILL AFTER EVAL] | [FILL AFTER EVAL] |
| valid_trained_eval | [FILL AFTER EVAL] | [FILL AFTER EVAL] |

## 6. C3 Final Status table: condition | C3 F1 | F_t variance | wrong_prob diversity | status - STATUS: [FILL AFTER EVAL]

| Condition | C3 F1 | F_t variance | wrong_prob diversity | Status |
|---|---:|---:|---:|---|
| Main Stage-B checkpoint | [FILL AFTER EVAL] | [FILL AFTER EVAL] | [FILL AFTER EVAL] | [FILL AFTER EVAL] |
| ABL-016 control | [FILL AFTER EVAL] | [FILL AFTER EVAL] | [FILL AFTER EVAL] | [FILL AFTER EVAL] |
| ABL-022 comparison | [FILL AFTER EVAL] | [FILL AFTER EVAL] | [FILL AFTER EVAL] | [FILL AFTER EVAL] |
| ABL-023 comparison | [FILL AFTER EVAL] | [FILL AFTER EVAL] | [FILL AFTER EVAL] | [FILL AFTER EVAL] |
| Final C3 verdict | [FILL AFTER EVAL] | [FILL AFTER EVAL] | [FILL AFTER EVAL] | READY_CANDIDATE / PRELIMINARY+ / BLOCKED / PIVOT_REQUIRED |

## 7. C4 Final Status table: condition | C4 fidelity | ID | OOD | seeds | status - STATUS: [FILL AFTER EVAL]

| Condition | C4 fidelity | ID | OOD | Seeds | Status |
|---|---:|---:|---:|---:|---|
| FRCG-LR main | [FILL AFTER EVAL] | [FILL AFTER EVAL] | [FILL AFTER EVAL] | [FILL AFTER EVAL] | [FILL AFTER EVAL] |
| ABL-024 | [FILL AFTER EVAL] | [FILL AFTER EVAL] | [FILL AFTER EVAL] | [FILL AFTER EVAL] | [FILL AFTER EVAL] |
| ABL-036 | [FILL AFTER EVAL] | [FILL AFTER EVAL] | [FILL AFTER EVAL] | [FILL AFTER EVAL] | [FILL AFTER EVAL] |
| Final C4 verdict | [FILL AFTER EVAL] | [FILL AFTER EVAL] | [FILL AFTER EVAL] | [FILL AFTER EVAL] | READY_FOR_REPORT / PRELIMINARY / DOWNSHIFT |

## 8. C1/C2/C5 table: Claim | Status | Evidence | Blocker - STATUS: [FILL AFTER EVAL]

| Claim | Status | Evidence | Blocker |
|---|---|---|---|
| C1 wrong-control-grammar persistence | [FILL AFTER EVAL] | [FILL AFTER EVAL] | [FILL AFTER EVAL] |
| C2 OOD/regime separation proxy | PRELIMINARY_PROXY / [FILL AFTER EVAL] | [FILL AFTER EVAL] | true regime_shift_f1 pending unless STEP 9 completed |
| C5 calibration | [FILL AFTER EVAL] | [FILL AFTER EVAL] | [FILL AFTER EVAL] |

## 9. Ablation Results: 11 inference + ABL-015 faithful + ABL-025/ABL-026 + ABL-040 + collapsed/survived - STATUS: [FILL AFTER EVAL]

| Ablation set | Faithful/proxy level | Result | Collapsed/survived | Evidence path |
|---|---|---|---|---|
| 11 inference-time ablations | [FILL AFTER EVAL] | [FILL AFTER EVAL] | [FILL AFTER EVAL] | [FILL AFTER EVAL] |
| ABL-015 faithful | faithful retrain | [FILL AFTER EVAL] | [FILL AFTER EVAL] | [FILL AFTER EVAL] |
| ABL-025 | [FILL AFTER EVAL] | [FILL AFTER EVAL] | [FILL AFTER EVAL] | [FILL AFTER EVAL] |
| ABL-026 | [FILL AFTER EVAL] | [FILL AFTER EVAL] | [FILL AFTER EVAL] | [FILL AFTER EVAL] |
| ABL-040 positive control | positive_control isolation | [FILL AFTER EVAL] | [FILL AFTER EVAL] | [FILL AFTER EVAL] |
| Collapsed variants summary | [FILL AFTER EVAL] | [FILL AFTER EVAL] | collapsed | [FILL AFTER EVAL] |
| Survived variants summary | [FILL AFTER EVAL] | [FILL AFTER EVAL] | survived | [FILL AFTER EVAL] |

## 10. Direct-Threat Baselines: BASE-026/027/028 | faithful level | result | reviewer risk - STATUS: [FILL AFTER EVAL]

| Baseline | Faithful level | Result | Reviewer risk |
|---|---|---|---|
| BASE-026 WAC | [FILL AFTER EVAL] | [FILL AFTER EVAL] | [FILL AFTER EVAL] |
| BASE-027 CUWM | [FILL AFTER EVAL] | [FILL AFTER EVAL] | [FILL AFTER EVAL] |
| BASE-028 WebWorld | [FILL AFTER EVAL] | [FILL AFTER EVAL] | [FILL AFTER EVAL] |

## 11. Claim Readiness table: Claim | Readiness | Paper wording allowed | Forbidden wording - STATUS: [FILL AFTER EVAL]

| Claim | Readiness | Paper wording allowed | Forbidden wording |
|---|---|---|---|
| FC-01 / C1 wrong-control-grammar persistence | [FILL AFTER EVAL] | [FILL AFTER EVAL] | "resolved", "proven", "defeated", "outperforms" FORBIDDEN |
| FC-02 / C2 OOD-regime separation | PRELIMINARY_PROXY (not PRELIMINARY) | OOD shift F1 proxy only until true regime_shift_f1 exists | "resolved", "proven", "defeated", "outperforms" FORBIDDEN; "defeats WAC", "outperforms CUWM", "superior to WebWorld" FORBIDDEN |
| FC-03 / C3 falsification F1 | [FILL AFTER EVAL] | [FILL AFTER EVAL] | "resolved", "proven", "defeated", "outperforms" FORBIDDEN |
| FC-04 / C4 alternative-hypothesis world model | [FILL AFTER EVAL] | [FILL AFTER EVAL] | "resolved", "proven", "defeated", "outperforms" FORBIDDEN |
| FC-05 / C5 calibration | [FILL AFTER EVAL] | [FILL AFTER EVAL] | "resolved", "proven", "defeated", "outperforms" FORBIDDEN |

Notes:
- FC-02 (C2) must be PRELIMINARY_PROXY, never PRELIMINARY, until true regime_shift_f1 is implemented.
- StressWeb (2604.16385) should be cited as motivation evidence for C1/C3 claims.
- Do not use comparative victory language unless the faithful direct-threat baseline evidence supports it and the forbidden wording list is updated by review.

## 12. Tests: targeted / regression / failures / unrelated - STATUS: [FILL AFTER EVAL]

| Test category | Command or scope | Result | Notes |
|---|---|---|---|
| Targeted | [FILL AFTER EVAL] | [FILL AFTER EVAL] | [FILL AFTER EVAL] |
| Regression | [FILL AFTER EVAL] | [FILL AFTER EVAL] | [FILL AFTER EVAL] |
| Failures | [FILL AFTER EVAL] | [FILL AFTER EVAL] | [FILL AFTER EVAL] |
| Unrelated failures | [FILL AFTER EVAL] | [FILL AFTER EVAL] | [FILL AFTER EVAL] |

## 13. Safety: leakage_count / fake_metric_count / forbidden_source / overwrite / Codex_outputs_write - STATUS: [FILL AFTER EVAL]

| Safety check | Value | Evidence |
|---|---|---|
| leakage_count | [FILL AFTER EVAL] | [FILL AFTER EVAL] |
| fake_metric_count | [FILL AFTER EVAL] | [FILL AFTER EVAL] |
| forbidden_source | [FILL AFTER EVAL] | [FILL AFTER EVAL] |
| overwrite | [FILL AFTER EVAL] | [FILL AFTER EVAL] |
| Codex_outputs_write | [FILL AFTER EVAL] | [FILL AFTER EVAL] |

## 14. Team Agents / Codex: used / tasks / accepted / rejected / red-team verdict - STATUS: [FILL AFTER EVAL]

| Agent or Codex task | Used | Task | Accepted | Rejected | Red-team verdict |
|---|---|---|---|---|---|
| exp_design_step8_v04_ablation_R1 | [FILL AFTER EVAL] | [FILL AFTER EVAL] | [FILL AFTER EVAL] | [FILL AFTER EVAL] | [FILL AFTER EVAL] |
| claim_metric_step8_alignment_R1 | [FILL AFTER EVAL] | [FILL AFTER EVAL] | [FILL AFTER EVAL] | [FILL AFTER EVAL] | [FILL AFTER EVAL] |
| novelty_step8_threat_R1 | [FILL AFTER EVAL] | [FILL AFTER EVAL] | [FILL AFTER EVAL] | [FILL AFTER EVAL] | [FILL AFTER EVAL] |
| Codex STEP 8 tasks | [FILL AFTER EVAL] | [FILL AFTER EVAL] | [FILL AFTER EVAL] | [FILL AFTER EVAL] | [FILL AFTER EVAL] |

## 15. User Feedback Events: decisions / impact - STATUS: [FILL AFTER EVAL]

| Event | Decision | Impact |
|---|---|---|
| [FILL AFTER EVAL] | [FILL AFTER EVAL] | [FILL AFTER EVAL] |
| [FILL AFTER EVAL] | [FILL AFTER EVAL] | [FILL AFTER EVAL] |

## 16. Commit: hash / message / files - STATUS: [FILL AFTER EVAL]

| Field | Value |
|---|---|
| Commit hash | [FILL AFTER EVAL] |
| Commit message | [FILL AFTER EVAL] |
| Files | [FILL AFTER EVAL] |

## 17. Final Human-readable Summary (5-10 lines) - STATUS: [FILL AFTER EVAL]

1. [FILL AFTER EVAL]
2. [FILL AFTER EVAL]
3. [FILL AFTER EVAL]
4. [FILL AFTER EVAL]
5. [FILL AFTER EVAL]
6. [FILL AFTER EVAL]
7. [FILL AFTER EVAL]
8. [FILL AFTER EVAL]
9. [FILL AFTER EVAL]
10. [FILL AFTER EVAL]

## 18. STEP 9 Handoff: remaining blockers / paper rewrite / training / baselines / ICLR readiness - STATUS: [FILL AFTER EVAL]

| Area | Remaining blocker | STEP 9 owner/action |
|---|---|---|
| Paper rewrite | [FILL AFTER EVAL] | [FILL AFTER EVAL] |
| Training | [FILL AFTER EVAL] | [FILL AFTER EVAL] |
| Baselines | [FILL AFTER EVAL] | [FILL AFTER EVAL] |
| Metrics | [FILL AFTER EVAL] | [FILL AFTER EVAL] |
| Architecture | [FILL AFTER EVAL] | [FILL AFTER EVAL] |
| ICLR readiness | [FILL AFTER EVAL] | [FILL AFTER EVAL] |
