TASK_NAME: TASK_1054_step5_abl_registry
SANDBOX_MODE: bypass

BACKGROUND:
3 CRITICAL ablations are registered in configs/ablation_core.yaml but are NOT in
src/frcgw/evaluation/ablations.py ABLATION_REGISTRY or _WRAPPERS dict.

ABL-011 (no_action_effect_log): Remove action-effect log from agent observation.
  - The action-effect grounding in PublicObservation is in history_public[*].effect_summary
    (each PublicHistoryItem has an effect_summary str field, NOT a top-level action_effect_log field)
  - Implementation: zero/None out effect_summary on all PublicHistoryItem in a COPY of obs.history_public
  - Expected collapse: falsification_precision_recall_f1 decrease, wrong_control_grammar_persistence increase

ABL-015 (no_control_grammar_loss): Remove L_control_grammar training loss (C2).
  - This is a TRAINING-TIME ablation. At inference smoke test, proxy behavior = random candidate
    selection (like NoControlGrammarAblation) but with distinct ablation_id and tdd_ref=ABL-015
  - Document clearly that this is a proxy for the training-time intervention (training cannot be
    replayed in P3 text-only smoke mode)
  - Expected collapse: regime_shift_f1 decrease, rewrite_success_rate decrease

ABL-040 (leakage_sanity_probe): Oracle label leakage positive control.
  - Inject true_control_grammar from eval_labels dict (NOT from PublicObservation) to override
    selected_hypothesis_id output. This uses the eval_labels: dict | None parameter of act().
  - Implementation: in act(), if eval_labels is not None and "true_control_grammar" in eval_labels,
    override _last_selected_hypothesis_id with eval_labels["true_control_grammar"]
  - Expected: task_success_rate jumps → confirms metric discriminability
  - LEAKAGE NOTE: This is a POSITIVE CONTROL test, not a production path. The inject comes from
    eval_labels arg (not PublicObservation), which is structurally isolated from agent observation.
    Document this isolation explicitly in the class docstring.
  - The leakage_auditor checks PublicObservation only, so this probe path is structurally safe.

Read the existing ABLATION_REGISTRY pattern in ablations.py to follow the exact same style.
Read PublicHistoryItem in src/frcgw/schemas/step_schema.py to confirm the effect_summary field name.

GOAL:
1. Add 3 new AblationConfig entries to ABLATION_REGISTRY in ablations.py
2. Add 3 new wrapper classes (NoActionEffectLogAblation, NoControlGrammarLossAblation, LeakageSanityProbeAblation)
3. Add 3 entries to _WRAPPERS dict
4. Write tests/test_step5_critical_ablations.py (5 tests)

FILES_ALLOWED:
- src/frcgw/evaluation/ablations.py
- tests/test_step5_critical_ablations.py

FILES_FORBIDDEN:
- outputs/**
- data/**
- paper_context_ref/**
- src/frcgw/schemas/**
- .claude/**
- scripts/run_codex_task.ps1
- configs/ablation_core.yaml (already registered — do not modify)

REQUIRED_IMPLEMENTATION:

1. ABLATION_REGISTRY entries (add after the "no_counterfactual_target" entry):

```python
"no_action_effect_log": AblationConfig(
    ablation_id="no_action_effect_log",
    tdd_ref="ABL-011",
    severity="CRITICAL",
    description="Remove action-effect log (effect_summary) from history_public; falsification loses grounding evidence (C3).",
    expected_collapse={
        "falsification_precision_recall_f1": "decrease",
        "wrong_control_grammar_persistence": "increase",
    },
    masking={"zero_effect_summary": True},
),
"no_control_grammar_loss": AblationConfig(
    ablation_id="no_control_grammar_loss",
    tdd_ref="ABL-015",
    severity="CRITICAL",
    description="Proxy for L_control_grammar=0.0 training ablation (C2). At inference: random candidate. Training-time intervention proxied.",
    expected_collapse={
        "regime_shift_f1": "decrease",
        "rewrite_success_rate": "decrease",
    },
    masking={"disable_control_grammar_loss": True},
),
"leakage_sanity_probe": AblationConfig(
    ablation_id="leakage_sanity_probe",
    tdd_ref="ABL-040",
    severity="CRITICAL",
    description="Oracle label leakage positive control: inject true_control_grammar from eval_labels to confirm metric discriminability. NOT a production path.",
    expected_collapse={
        "task_success_rate": "increase",
    },
    masking={"inject_oracle_grammar": True},
),
```

2. Wrapper classes:

NoActionEffectLogAblation:
- In act(), create a modified copy of obs where each PublicHistoryItem has effect_summary=None
  (use dataclasses.replace for immutability; make a new PublicObservation with modified history_public)
- Pass the modified obs to self._agent.act()
- Do NOT mutate the original obs

NoControlGrammarLossAblation:
- Proxy: return _random_public_candidate(obs, salt=self.ablation_id) with appropriate budget
  (planning_calls=0, same as NoControlGrammarAblation pattern)

LeakageSanityProbeAblation:
- In act(obs, eval_labels=None), call self._agent.act(obs, eval_labels) to get base action and log
- If eval_labels is not None and "true_control_grammar" in eval_labels:
  override _agent._last_selected_hypothesis_id = eval_labels["true_control_grammar"]
- Return the base action and log unchanged
- Docstring must include: "POSITIVE CONTROL: oracle injection via eval_labels, NOT PublicObservation"

3. _WRAPPERS additions:
```python
"no_action_effect_log": NoActionEffectLogAblation,
"no_control_grammar_loss": NoControlGrammarLossAblation,
"leakage_sanity_probe": LeakageSanityProbeAblation,
```

4. tests/test_step5_critical_ablations.py (5 tests):
   - test_abl011_registered(): "no_action_effect_log" in ABLATION_REGISTRY and in _WRAPPERS
   - test_abl015_registered(): "no_control_grammar_loss" in ABLATION_REGISTRY and in _WRAPPERS
   - test_abl040_registered(): "leakage_sanity_probe" in ABLATION_REGISTRY and in _WRAPPERS
   - test_abl011_dispatch_zeros_effect_summary(): apply NoActionEffectLogAblation on mock agent,
     call act with obs that has non-empty history_public with effect_summary="some_effect",
     verify the modified obs passed to inner agent has effect_summary=None for all history items
     (needs to capture the obs the inner agent received)
   - test_abl040_leakage_probe_overrides_hypothesis(): apply LeakageSanityProbeAblation,
     call act with eval_labels={"true_control_grammar": "direct_search"},
     verify that after act(), agent._last_selected_hypothesis_id == "direct_search"

REQUIRED_TESTS:
pytest tests/test_step5_critical_ablations.py -q
Expected: 5 passed

ACCEPTANCE_CRITERIA:
- 5 tests pass
- 3 new ABLATION_REGISTRY entries present
- 3 new wrapper classes with correct behavior
- 3 new _WRAPPERS entries
- NoActionEffectLogAblation does NOT mutate original obs (creates copy)
- LeakageSanityProbeAblation uses eval_labels arg, NOT PublicObservation
- No FORBIDDEN_AGENT_KEYS in PublicObservation via ablation path

COMMIT_MESSAGE:
feat(step5/task6): ABL-011/015/040 ablations.py registry wiring

STOP_CONDITION:
Stop if: (1) PublicHistoryItem does not have effect_summary field (report field name and stop),
(2) TextFRCGModelAgent.act() does not accept eval_labels parameter (check and stop if missing),
(3) dataclasses.replace fails on PublicObservation (check if it's a dataclass or Pydantic model)
