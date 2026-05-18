# STEP 8 Final Evidence Card

date: 2026-05-18
branch: memory-redesign-2026-05-16
phase_gate_target: P3_STEP8_FINAL_EVIDENCE_VALIDATION

---

## 1. Executive Summary

STEP 8 generated the first real eval evidence for FRCG-WM on 5000-episode v0_4 data. The falsification training signal is non-degenerate (F_t variance=0.191, l_falsification=0.635). The compute gate shows a 93% progress_per_compute gap vs no-gate ablation. Task success is 0.994/0.998 but is non-discriminative due to task triviality (ceiling effect across all ablations). C3 eval is degenerate (falsification_precision=0.0) with unidentified root cause — root cause resolution is the STEP 9 critical path.

---

## 2. Verdict

**VERDICT: AT_RISK**
**Confidence: MEDIUM**
**Reason**: Training mechanism alive (F_t_variance=0.191) but eval metric degenerate (C3 fp=0.0). C6 compute gate strong (93% ppc gap). Task success non-discriminative. n=5 seeds incomplete. Root cause investigation required in STEP 9.

Rubric (from 36_step8_execution_plan.md §6):
- NOT ALIVE: C3 not READY_CANDIDATE, n=5 stats missing
- NOT BLOCKED: Training F_t non-degenerate, root cause unidentified
- AT_RISK: C3 PRELIMINARY_PENDING_EVAL + C4 NON_DISCRIMINATIVE + heuristic approx level + missing seeds

---

## 3. Repo State

Before SHA: c2cd0a7 (P3_STEP7_FULL_EVIDENCE_VALIDATION)
After SHA: 8316bd6
Branch: memory-redesign-2026-05-16

---

## 4. Data

| Item | Value | Gate |
|---|---|---|
| v0_4 total episodes | 5000 | O3 PASS |
| train/valid/test_id/test_ood | 3500/500/500/500 | PASS |
| blocker_removed (test_ood) | 50 >= 30 | PASS |
| delayed_effect (test_ood) | 50 >= 30 | PASS |
| leakage_count | 0 | PASS |
| correct_hypothesis_id | NOT EMITTED | STEP 9 required |
| v0_3 sha256 | unchanged | PASS |

---

## 5. Training

| Config | Steps | l_falsification | l_total | Status |
|---|---|---|---|---|
| Stage A | 1000 | 0.647 | 1.433 | complete |
| Stage B | 2000 | 0.635 | 1.141 | complete |
| ABL-015 (l_cg=0.0) | 2000 | 0.635 | 1.068 | complete |

ABL-015 training differentiation: l_control_grammar=2.075 vs Stage B 0.055 — training-time signal confirmed.

---

## 6. C3 Final Status

| Condition | F_t variance | predicted_wrong true_count | falsification_fp | Status |
|---|---|---|---|---|
| Post-Stage B training audit | 0.191 | 0 | 0.0 (eval) | PRELIMINARY_PENDING_EVAL |

Root cause candidates for eval degeneration:
1. ABL-040 injection inert → eval harness propagation suspect
2. Training-to-inference predicted_wrong flag divergence
3. F_t=None silent zero in training (unverified)

---

## 7. C4 Final Status

| Split | FRCG-LR tsr | ABL-036 tsr | ABL-040 tsr | Status |
|---|---|---|---|---|
| test_id | 0.994 | 0.994 | 0.994 | NON_DISCRIMINATIVE |
| test_ood | 0.998 | 0.998 | 0.998 | NON_DISCRIMINATIVE |

Ceiling effect confirmed. All agents identical. C4 is not a discriminative metric in current setup.

C6 progress_per_compute (discriminative):
- FRCG-LR: 0.221 (ID) / 0.290 (OOD)
- ABL-036 (no_compute_gate): 0.015 / 0.020 → 93% gap

---

## 8. C1/C2/C5

| Claim | Status | Evidence | Blocker |
|---|---|---|---|
| C1 persistence_v1 | BLOCKED | compute proxy | correct_hypothesis_id missing from v0_4 |
| C2 ood_shift_f1 proxy | PRELIMINARY_PROXY | proxy metric | true regime_shift_f1 → STEP 9 |
| C5 ECE calibration | BLOCKED_DEGENERATE | — | C3 eval degenerate |

---

## 9. Ablation Results

FRCG-LR ppc reference: 0.221 (ID), 0.290 (OOD)

| ABL | Description | ppc (ID) | ppc (OOD) | Collapse |
|---|---|---|---|---|
| ABL-036 | no compute gate | 0.015 | 0.020 | COLLAPSE (93%) |
| ABL-034 | no progress/reward | 0.025 | 0.036 | COLLAPSE |
| ABL-023 | uncertainty instead | 0.086 | 0.118 | PARTIAL |
| ABL-022 | no falsif gate | 0.108 | 0.145 | PARTIAL |
| ABL-024 | no alt hypothesis | 0.108 | 0.145 | PARTIAL |
| ABL-011/025/026/035 | no rollout variants | 0.044 | 0.064 | COLLAPSE |
| ABL-006 | collapsed latent | 0.216 | 0.290 | NO COLLAPSE |
| ABL-033 | no rewrite | 0.216 | 0.290 | NO COLLAPSE |
| ABL-040 (positive ctrl) | oracle probe | tsr=0.994 | same as all | INERT (no discrimination) |

ABL-015 (faithful retrain, l_cg=0.0): eval pending with separate checkpoint.

Executed: 12 inference ablations (ABL-006,011,017,022,023,024,025,026,033,034,035,036)
Positive control isolated: ABL-040
Deferred: ABL-001, ABL-003 (STEP 9), ABL-015 (training done, eval pending)

---

## 10. Direct-Threat Baselines

| Baseline | approx_level | ppc (ID) | ppc (OOD) | Gate |
|---|---|---|---|---|
| BASE-026-faithful | partial | 0.037 | 0.053 | PASS |
| BASE-027-faithful | partial | 0.025 | 0.036 | PASS |
| BASE-026-heuristic | heuristic | 0.037 | 0.053 | PASS |
| BASE-027-heuristic | heuristic | 0.025 | 0.036 | PASS |
| BASE-028-heuristic | heuristic | — | — | STEP 9 |

forbidden_wording_count=0. FRCG-LR ppc vs BASE-026-faithful: 6× advantage (ID).

---

## 11. Claim Readiness

| Claim | Readiness | Paper wording allowed | Forbidden |
|---|---|---|---|
| C1 | BLOCKED | "blocked pending correct_hypothesis_id" | Any persistence values |
| C2 | PRELIMINARY_PROXY | "ood_shift_f1 proxy (STEP 7)" | "PRELIMINARY", "confirmed" |
| C3 | PRELIMINARY_PENDING_EVAL | "training F_t=0.191 non-degenerate; eval root cause unknown" | "falsification fp=[any positive]" |
| C4 | NON_DISCRIMINATIVE | "task success ceiling; C6 ppc 93% gap preliminary" | tsr as claim evidence |
| C5 | BLOCKED | "blocked pending C3" | Any ECE |
| C6 | PRELIMINARY | "93% ppc gap (preliminary)" | "proven", "defeats", "superior" |

---

## 12. Tests

STEP 8 targeted: 70/70 PASS
Full regression: 606 passed, 4 pre-existing failures, 2 skipped

---

## 13. Safety

hidden_label_leakage_count=0, fake_metric_count=0, forbidden_source=none_read, Codex outputs/** write=0, visibility.py unchanged=True

---

## 14. Team Agents / Codex

Agents used: 8 (Round 1: 6, Round 3: 2)
Codex tasks: 8 accepted (TASK_1087~1095)
Area-chair verdict: AT_RISK MEDIUM

---

## 15. User Feedback Events

Key user-decision events: ABL-015 naming corrected (l_control_grammar=0.0), Stage A extended to 1000 steps, gradient clipping added, v0_4 OOD stratified sampling required.

---

## 16. Commit

Hash: 8316bd6
Message: fix(step8): eval runner dataset_path + faithful baselines + ABL-025/026 ablation runner

---

## 17. Final Human-Readable Summary

FRCG-WM STEP 8 produced the first real eval on v0_4 (5000 episodes). The strongest finding is a 93% compute-efficiency advantage for FRCG-LR vs the always-plan ablation, providing preliminary C6 (compute gate) evidence. Training confirms the falsification mechanism is alive (F_t variance=0.191). Task success is non-discriminative (all agents score 0.994-0.998, task triviality ceiling). The C3 falsification eval metric shows 0.0 precision — the root cause is unknown but has candidate explanations to investigate in STEP 9. Verdict: AT_RISK. The project is not blocked — the mechanism trains — but ICLR readiness requires resolving C3 eval degeneration and completing n=5 seed statistics.

---

## 18. STEP 9 Handoff

See: docs/orchestration/lr_alignment/38_step9_handoff.md

Priority 1: C3 root cause — assert F_t is not None, verify ABL-040 injection propagates.
Priority 2: v0_4 correct_hypothesis_id in evaluation_labels.
Priority 3: ABL-001/003 faithful retrain + true regime_shift_f1 (R2 lock review).
