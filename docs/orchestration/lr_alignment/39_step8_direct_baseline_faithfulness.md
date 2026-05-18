# 39_step8_direct_baseline_faithfulness.md

## Scope

STEP 8 adds partial faithful candidates for the two direct-threat baselines that
previously used only heuristic proxies:

| Baseline | Class | Status |
| --- | --- | --- |
| BASE-026-faithful | `WACFaithfulCandidate` | partial faithful candidate |
| BASE-027-faithful | `CUWMFaithfulCandidate` | partial faithful candidate |
| BASE-028-heuristic | `WebWorldStyleSearchAgent` | unchanged heuristic proxy; STEP 9 scope |

## Faithfulness Criteria

`WACFaithfulCandidate` is faithful only to the public-observation side of the
WAC-style algorithm. It estimates a grammar-family posterior from public action
history by counting `no_state_change` effects per visible action family, then
selects the candidate with the highest posterior-weighted success estimate. It
is explicitly `approximation_level="partial"` because a full reconstruction
requires a trained discriminative model.

`CUWMFaithfulCandidate` is faithful only to the public candidate-simulation
interface. It scores up to five visible candidates with a one-step effect-type
rule table and gives a small bonus to candidates not tried in public history. It
is explicitly `approximation_level="partial"` because a full reconstruction
requires trained world-model rollout.

Both classes must keep the hidden-label assertion as the first executable line
of `act()`. They must not use true grammar labels, oracle actions, audit
metadata, counterfactual labels, or any other forbidden agent field as inference
input.

## Verification

Required tests:

```text
python -m pytest tests/test_step8_direct_threat_baselines.py -q
python -m pytest tests/test_forbidden_field_mirror_sync.py tests/test_leakage_auditor.py -q
```

Audit command:

```text
python scripts/audit_step8_direct_threat_baselines.py --eval-root <eval-runs-dir> --out <audit.json>
```

The audit records each direct-threat baseline's declared approximation level,
mean `task_success_rate`, mean `wrong_grammar_persistence`, source wording count,
and gate status.

## Reviewer Wording Guard

Reviewer-facing text must avoid categorical dominance claims over WAC, CUWM, or
WebWorld. The accepted phrasing is:

> BASE-026-faithful and BASE-027-faithful are partial faithful candidates built
> from public history and public candidate actions. They support a stronger
> direct-threat comparison than the prior heuristic proxies, but they are not
> complete paper reimplementations.

Use metric-specific language when reporting results, for example "lower
wrong-grammar persistence in this run" or "higher task success on this split."
Do not generalize beyond the audited metric, split, and implementation status.
