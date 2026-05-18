# STEP 7 C2 Metric Decision: ood_shift_f1 vs regime_shift_f1

date: 2026-05-18
status: DOCUMENTED

## Decision

C2's formal metric target for the claim that regime/control grammar separation
contributes to OOD generalization is MET-OOD-003: OOD control grammar shift
performance.

Computing a formal `regime_shift_f1` requires `true_regime` to be exposed in
`EvaluationLabels`. Today `true_regime` is part of the forbidden agent-field
contract, so surfacing it as an eval label requires a visibility contract change.
That change is deferred to STEP 8.

STEP 7 introduces `ood_shift_f1` as a MET-OOD-003 proxy:

- `ood_type` from `EvaluationLabels` is used only as an eval-time split label and
  is converted to binary shift/no-shift.
- The agent's `predicted_wrong` flag is used as the shift detection signal.
- This is a proxy and is not true regime shift detection.

## Paper Wording Rules

FORBIDDEN:

- `regime_shift_f1` as a STEP 7 metric name.
- "C2 resolved" or "C2 proven" before STEP 8.
- "defeats regime shift problem" without direct empirical evidence.

ALLOWED:

- "OOD shift detection F1 (proxy, STEP 7)".
- "C2 preliminary proxy: `ood_shift_f1`".
- "`regime_shift_f1` deferred to STEP 8 because a visibility contract change is
  required".

## C5 Calibration Retest Policy

`falsification_calibration` (ECE) is already implemented in `metrics.py`.
For STEP 7 trained eval, compute ECE only when `wrong_prob` has more than two
unique values. If `unique_count <= 2`, mark the result
`BLOCKED_DEGENERATE_PREDICTOR`.

## MET-LATENT-001 Status

MET-LATENT-001, the latent factorization quality metric, is not implementable in
STEP 7. It is deferred to STEP 8. C2 ablations ABL-001/002/003 also remain in
the STEP 8 faithful retrain queue.
