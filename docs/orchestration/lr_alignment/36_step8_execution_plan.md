# STEP 8 — Final Evidence Validation: Execution Plan

date: 2026-05-18
branch: memory-redesign-2026-05-16
phase_gate_target: P3_STEP8_FINAL_EVIDENCE_VALIDATION
verdict: IMPLEMENTABLE_CORE (사용자 결정)
prior_sentinel: P3_STEP7_FULL_EVIDENCE_VALIDATION.passed @ c2cd0a7

---

## 1. STEP 7 Completion Snapshot

| Item | Status | Path |
|---|---|---|
| P3_STEP7_FULL_EVIDENCE_VALIDATION sentinel | PASS | `outputs/phase_gates/P3_STEP7_FULL_EVIDENCE_VALIDATION.passed` |
| C3 mapping fix | MERGED | planner.py + losses.py + lr_scorer.py |
| falsification.py short-circuit | Option C (unchanged + comment) | `1bd36c6` |
| C2 ood_shift_f1 proxy | MERGED | metrics.py + eval_runner.py |
| C4 expanded harness | MERGED | `configs/lr_eval_real_v0_3_step7_full.yaml` |
| 11 inference ablation harness | MERGED | `scripts/run_step7_full_inference_ablations.py` |
| BASE-026/027 approximation_level | MERGED | baselines.py |
| **STEP 7 eval runs (F.3~F.6)** | **NEVER RAN** | — |
| **step8 audit artifacts** | **ALL MISSING** | — |

---

## 2. STEP 8 Scope (locked)

### In Scope
1. v0_4 dataset: 5000 episodes, OOD coverage (blocker_removed ≥ 30, delayed_effect ≥ 30)
2. Long-horizon training: Stage A (diagnostic, 500 steps) + Stage B (2000 steps, ≥10 epochs)
3. C3 final verification: F_t variance > 0, predicted_wrong diversity, ABL-016/022/023 comparison
4. C4 expanded: n=5 seeds × test_id + test_ood × FRCG-LR + ABL-024 + ABL-036
5. C1/C2/C5: full report (C2 proxy only, C5 gated on C3 non-degenerate)
6. 11 inference-time ablations + ABL-040 positive control isolation
7. ABL-015 faithful retrain (l_control_grammar=0.0)
8. BASE-026 faithful: WACFaithfulCandidate (grammar posterior + consequence correction)
9. BASE-027 faithful: CUWMFaithfulCandidate (K-candidate + model rollout)
10. Final evidence card + ALIVE/AT_RISK/BLOCKED/PIVOT_REQUIRED verdict
11. STEP 9 handoff

### Out of Scope (deferred to STEP 9)
- ABL-001/003 faithful retrain
- BASE-028 WebWorld faithful
- true regime_shift_f1 (visibility contract change → R2 lock review)
- schema_leakage_guard hook drift sync
- LR active path swap
- compute-matched BASE-015 vs FRCG-LR

---

## 3. Codex Task Summary

| Task | Scope | Key Output |
|---|---|---|
| 1 | C3 diagnostics + per_step trace hardening | `scripts/audit_step8_c3_root_cause.py`, `tests/test_step8_c3_trace_integrity.py` |
| 2 | v0_4 dataset generator + coverage audit | `scripts/generate_v0_4_dataset.py`, `scripts/audit_step8_dataset_coverage.py`, `configs/dataset_v0_4.yaml` |
| 3 | Long-horizon training configs | `configs/train_text_v0_4_long.yaml`, `configs/train_text_v0_4_long_stage2.yaml`, `configs/lr_eval_real_v0_4_long.yaml` |
| 4 | Full eval / n=5 report harness | `scripts/run_step8_full_eval_report.py` |
| 5 | Faithful ABL-015 retrain config | `configs/train_text_v0_4_abl015.yaml`, `scripts/run_step8_faithful_ablations.py` |
| 6 | BASE-026/027 faithful baselines | `src/frcgw/evaluation/baselines.py` (WACFaithfulCandidate + CUWMFaithfulCandidate) |
| 7 | C2/C5 metric integrity | `src/frcgw/evaluation/metrics.py` (ood_shift_f1 only), `src/frcgw/evaluation/calibration.py` (NEW) |
| 8 | Final evidence card scaffolding | `docs/orchestration/lr_alignment/37_step8_final_evidence_card.md`, `38_step9_handoff.md` |

---

## 4. Forbidden Paths

```
paper_context_ref/**
src/frcgw/schemas/visibility.py          (Fragile File — R2 lock)
src/frcgw/schemas/step_schema.py         (visibility contract — STEP 9)
.claude/settings*
scripts/run_codex_task.ps1
data/frcgw_text/v0_{1,2,3}/**           (immutable evidence)
outputs/checkpoints/pretrain_v0_3/**    (ABL-016 control)
outputs/runs/p3_lr_real_eval_step{5,6,7}_*/**
outputs/audits/step{3,4,5,6,7}_*.json
outputs/phase_gates/P*.passed
```

Codex also forbidden: `outputs/**` write, `data/**` write, `*.pt` checkpoint files.

---

## 5. Gate Criteria (O3~O14)

### O3 Data Gate
- `data/frcgw_text/v0_4/manifest.json` exists, total episodes = 5000 ±5%
- OOD: blocker_removed ≥ 30, delayed_effect ≥ 30
- leakage audit: 0 FORBIDDEN_AGENT_FIELDS
- v0_3 sha256 unchanged

### O4 C3 Gate
- `outputs/audits/step8_c3_root_cause_audit.json` exists
- F_t variance > 0 OR explicit BLOCKED reason
- Verdict: READY_CANDIDATE / PRELIMINARY+ / BLOCKED / PIVOT_REQUIRED

### O5 Training Gate
- pretrain_v0_4_long checkpoint exists
- abl015 checkpoint exists (or STEP 9 deferred reason)
- all losses finite, l_falsification non-zero post-training

### O6 C4 Gate
- n=5 seeds × 2 splits × 3 agents validation complete
- Status: READY_FOR_REPORT / PRELIMINARY / DOWNSHIFT

### O7 C1/C2/C5 Gate
- C1 persistence_v1 metric computed
- C2: ood_shift_f1 proxy ONLY (no true regime_shift_f1 introduced)
- C5: calibration if C3 non-degenerate, else BLOCKED_DEGENERATE_PREDICTOR

### O8 Ablation Gate
- 11 inference-time ablations on pretrain_v0_4_long
- ABL-040 isolated in positive_control bucket
- ABL-015 faithful retrain executed
- ABL-001/003 explicit STEP 9 deferred

### O9 Direct Baseline Gate
- BASE-026/027 faithful implementations + tests green
- approximation_level honestly recorded
- step8_direct_threat_baseline_audit.json exists
- forbidden wording: zero occurrences ("defeats WAC", "outperforms CUWM", "superior to WebWorld")

### O10 Safety Gate
- hidden_label_leakage_count=0, fake_metric_count=0
- STEP 5/6/7 artifacts unchanged
- Codex wrote zero files under `outputs/**`, `data/**`, `*.pt`

### O11 Test Gate
- All STEP 8 targeted tests green
- Full regression: ≥ 581 passed + new STEP 8 tests

### O12 Final Verdict Gate
- Evidence card filled with real numbers
- Verdict ∈ {ALIVE, AT_RISK, BLOCKED, PIVOT_REQUIRED}
- Paper table readiness yes/no

### O13 Commit Gate
- Commit message per verdict:
  - GREEN: `feat(step8): final evidence — v0_4 + long-horizon + n=5 + faithful baselines`
  - PARTIAL: `feat(step8): partial final evidence (C3/C4/ABL-015) + STEP 9 handoff`
  - BLOCKED: `docs(step8): final blocker diagnosis + PIVOT proposal`

### O14 Phase Gate Sentinel
- `outputs/phase_gates/P3_STEP8_FINAL_EVIDENCE_VALIDATION.passed` (zero-byte)

---

## 6. Final Verdict Rubric

| Verdict | Criteria |
|---|---|
| **ALIVE** | C3 READY_CANDIDATE + C4 READY_FOR_REPORT + ≥1 faithful direct baseline + ABL-040 isolation pass + n=5 stats + zero leakage |
| **AT_RISK** | C3 PRELIMINARY+ + C4 PRELIMINARY + at least one baseline approximation_level=partial + missing seeds OR one metric blocked |
| **BLOCKED** | C3 BLOCKED (F_t variance=0 post-Stage B + non-degenerate strategy exhausted) OR data generation fatal |
| **PIVOT_REQUIRED** | C3 BLOCKED + C4 DOWNSHIFT (mean < 0.5) → paper main axis must shift to C1/C2/C4-only |

---

## 7. Phase Execution Sequence

1. PHASE A: done (read-only audit)
2. PHASE B: Team Agents Round 1 (6 agents, read-only) → reports
3. PHASE C: this plan (locked)
4. PHASE D Task 1: C3 diagnostics → Round 2 → merge
5. PHASE D Task 2: v0_4 generator → Round 2 → merge
6. PHASE G: Claude direct [1][2] — generate v0_4 + coverage audit → O3 gate
7. PHASE D Task 3: long-horizon configs → merge
8. PHASE H: Claude direct [3][4][5] — pre-training audit + training Stage A + Stage B
9. PHASE D Task 5: ABL-015 config → merge
10. PHASE H: Claude direct [6] — ABL-015 faithful retrain
11. PHASE D Task 4: full eval report harness → merge
12. PHASE I: Claude direct [7][8][11] — full eval + LR reconciliation → O4 gate
13. PHASE J: Claude direct [9] — C4 expanded validation → O6 gate
14. PHASE D Task 7: C2/C5 → merge
15. PHASE K: C1/C2/C5 metric run
16. PHASE L: Claude direct [10] — 11 ablations + ABL-040 → O8 gate
17. PHASE D Task 6: faithful baselines → merge
18. PHASE M: Claude direct [12] — direct baseline eval → O9 gate
19. PHASE D Task 8: evidence card scaffold → merge
20. PHASE N: Claude direct [13][14] — targeted + full regression → O11 gate
21. Team Agents Round 3 (T4 deep): failure-interpretation + area-chair + reviewer-2
22. PHASE F: fill evidence card + STEP 9 handoff
23. PHASE O: verdict + commit + sentinel
24. PHASE P: final report

---

## 8. Team Agents Round 1 Reports (PHASE B)

Reports expected at: `docs/orchestration/agent_reports/2026-05/`

| Agent | Topic | Status |
|---|---|---|
| mathematical-validity-critic | C3 gradient path in long-horizon | pending |
| experiment-design-expander | v0_4 OOD coverage + ABL-015 budget | pending |
| feasibility-and-cost-auditor | full STEP 8 time budget | pending |
| frcgw-data-leakage-auditor | v0_4 generator + BASE-026/027 leakage | pending |
| claim-metric-alignment-auditor | C2 proxy + C5 gating + baseline metrics | pending |
| novelty-threat-scout | WAC/CUWM/WebWorld 2025/2026 threats | pending |
