# Experiment Design Audit Report
**Agent**: experiment-design-expander (deep)
**Date**: 2026-05-16
**Session**: War Room R1

## Verdict: INCOMPLETE_CRITICAL

P4 GUI env 0% implemented. 4 CRITICAL ablations MISSING. 3 direct-threat baselines (BASE-026/027/028) MISSING.

---

## ESCALATION FLAG

`tests/test_ablation_runner.py:63` hardcodes `len(ABLATION_REGISTRY) == 12`. Any Codex task adding new ablations WITHOUT also updating this test will break the test suite. Must be done in same Codex task.

`tests/test_ablation_runner.py:30-39` `CRITICAL_ABLATION_IDS` only has 8 entries. Missing: ABL-011, ABL-015, ABL-017, ABL-022, ABL-040 (all CRITICAL in §8).

---

## CRITICAL Ablations Status (14 items)

| ABL | Description | Status |
|---|---|---|
| ABL-002 | no-control-grammar | IMPLEMENTED (ablations.py:248) |
| ABL-003 | merged regime-control grammar | IMPLEMENTED |
| ABL-006 | collapsed latent | IMPLEMENTED |
| ABL-011 | no-action-effect-log | **MISSING** |
| ABL-015 | no L_control_grammar (loss) | **MISSING** |
| ABL-016 | no L_falsification | IMPLEMENTED |
| ABL-017 | no L_intent_action_mapping (loss) | **MISSING** |
| ABL-022 | no falsification score gate (planning trigger) | **MISSING** (distinct from ABL-016) |
| ABL-023 | uncertainty instead of falsification | IMPLEMENTED |
| ABL-024 | no alternative hypothesis | IMPLEMENTED |
| ABL-033 | no decision-relevance gate | IMPLEMENTED |
| ABL-034 | always-plan | IMPLEMENTED |
| ABL-035 | no action rewrite | IMPLEMENTED |
| ABL-040 | public evidence only / leakage probe | **MISSING** |

**8/14 CRITICAL implemented. 6 MISSING (or 5+1 partial for ABL-022).**

---

## Direct Threat Baselines (BASE-026/027/028) — 0/3 MISSING

All three MISSING from baselines.py and tests/test_baselines.py.
Critical for ATTACK-DEF-004.

---

## TASK_1021_A Scope Assessment

SUFFICIENT for P4 entry precondition, with additions:
1. gui_env/env_schema.py (GuiEpisodeSpec + GuiObservation with hidden fields separated)
2. gui_env/observation_builder.py with assert_agent_observation_safe() + DOM value sanitizer
3. tests/test_gui_env_no_hidden_label_in_observation.py
4. tests/test_gui_env_replay.py
5. Grammar engine stub interface (class stubs only, no logic)

**IMPORTANT: Must NOT add full grammar engine, episode generator, or counterfactual generator.**

---

## Critical Design Risk: Text Env 1:1 Mapping

`text_env/generator.py:256`: `hidden_regime=family` — task_family=regime 1:1 mapping.
GUI env MUST break this. CONST-05-007 forbids task:grammar 1:1.
If inherited: OOD grammar shift (SPLIT-003) becomes trivial → invalid.

---

## P4 Entry Minimum Implementation (Ordered)

**TIER 0 (TASK_1021_A)**
1. `gui_env/env_schema.py` — GuiEpisodeSpec + GuiObservation
2. `gui_env/observation_builder.py` — agent observation builder + DOM value sanitizer
3. `tests/test_gui_env_no_hidden_label_in_observation.py`
4. `tests/test_gui_env_replay.py`
5. `gui_env/grammar_engine.py` — stub only (interface, GRAM-001..008)

**TIER 1 (after TASK_1021_A)**
6. `gui_env/episode_generator.py` — cross-product sampling (NOT 1:1)
7. `tests/test_gui_env_task_regime_balance.py`

**TIER 2 (parallel with TIER 1)**
8. ablations.py + ablation_core.yaml: add ABL-011/015/017/022/040 (same Codex task, include test update)
9. baselines.py: add BASE-026/027/028 stubs

**TIER 3**
10. `gui_env/counterfactual.py` — for MET-WM-001

---

## DOM String Value Leakage Risk (New Finding)

Existing `assert_agent_observation_safe()` checks FIELD NAMES only.
DOM class/data-*/aria values containing hidden label tokens (e.g., `"class": "regime_modal_blocked_grammar_003"`) are NOT scanned.

Two-layer sanitization required:
1. Field-name forbidden list (exists in visibility.py) ✓
2. DOM string value scan for forbidden token substrings (MISSING — needs design)
