# STEP 7 Full Inference Ablation Execution Results

date: 2026-05-18
status: PLANNED (results pending eval execution)

## Executed Ablations (11 inference-time)

| ID | Description | Expected Collapse | Result |
|---|---|---|---|
| ABL-006 | collapsed latent | falsification_precision_recall_f1 down | PENDING |
| ABL-011 | no rollout | alternative_rollout_fidelity down | PENDING |
| ABL-017 | random alternative | task_success_rate down | PENDING |
| ABL-022 | classifier variant A | falsification_precision_recall_f1 change | PENDING |
| ABL-023 | uncertainty instead of falsification | false_planning_call_rate up | PENDING |
| ABL-024 | no alternative hypothesis | task_success_rate down | PENDING |
| ABL-033 | no rewrite | task_success_rate down | PENDING |
| ABL-034 | no progress/reward | progress_per_compute down | PENDING |
| ABL-035 | no compute gate (soft) | false_planning_call_rate up | PENDING |
| ABL-036 | no compute gate | false_planning_call_rate up | PENDING |

## Positive Control (isolated)

| ID | Description | Expected Result |
|---|---|---|
| ABL-040 | oracle leakage positive control | PASS (leakage detected) = F1 artificially high |

ABL-040 FAIL = leakage working correctly (intended).

## Deferred to STEP 8 (faithful retrain required)

| ID | Description | Reason |
|---|---|---|
| ABL-001 | no control grammar training | requires training-time l_grammar=0 |
| ABL-003 | merged regime control grammar training | requires re-training with merged head |
| ABL-015 | no falsification training hard | requires training-time l_falsification=0 (different from ABL-016) |

These are training-proxy ablations only in STEP 7. STEP 8 faithful retrain is required
for paper reporting. Do NOT report these as faithful ablation results.
