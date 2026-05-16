# Evidence Card C2: Regime / Control-Grammar Separation

## claim_id
C2

## current_status_before_run6
BLOCKED — no crossed-split eval, no latent probe, ABL-001 (no_regime) ablation exists but no full eval.

## run6_metric_evidence
Source: `outputs/runs/p3_lr_eval/metrics.json` → C2

| Metric | Value |
|---|---|
| C2 status | BLOCKED_no_regime_split_eval |

ABL-001 (no_regime) is in ABLATION_REGISTRY with expected_collapse: regime_shift_f1 decrease, recovery_delay increase. Pilot ablation run produced same proxy metrics as FRCG-FULL (smoke run, not meaningful for C2).

## baseline_evidence
No baseline comparison available for C2 at this scope.

## ablation_evidence
ABL-001 no_regime: wrong_grammar_persistence=1.909, recovery_delay=2.545 — identical to FRCG-FULL in smoke run. Expected differentiation requires crossed OOD splits (text_ood_grammar vs text_id) and latent probe.

## counter_evidence
- Locatello et al. impossibility: without inductive bias, latent disentanglement cannot be guaranteed. C2 claim requires explicit inductive bias argument or empirical proof.
- No regime_shift_f1 metric exists in current metrics.py.
- Smoke run results identical for no_regime vs FRCG-FULL — no differentiation.

## blocker
- No crossed-split evaluation (text_ood_grammar regime shift episodes)
- No latent probe metric (regime_shift_f1)
- Locatello impossibility not addressed

## decision
BLOCKED

## rationale
Cannot support C2 without crossed-split eval demonstrating regime separation. ABL-001 shows no differentiation in pilot smoke runs. Locatello impossibility risk unresolved.

## next_required_work
- Implement regime_shift_f1 metric
- Run crossed-split eval (text_ood_grammar vs text_id)
- Evaluate ABL-001 on split where regime changes
- Address Locatello impossibility with inductive bias argument

## allowed_claim_wording
"FRCG-WM includes a regime latent dimension. Empirical validation of regime/grammar separation is planned for Phase 5 crossed-split evaluation."

## forbidden_claim_wording
- "FRCG-WM disentangles regime from control grammar" — not empirically validated
- "ABL-001 confirms regime separation" — pilot shows no differentiation
