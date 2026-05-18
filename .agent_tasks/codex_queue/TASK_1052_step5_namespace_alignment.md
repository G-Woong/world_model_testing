TASK_NAME: TASK_1052_step5_namespace_alignment
SANDBOX_MODE: bypass

BACKGROUND:
In STEP 4, C1 metric (compute_wrong_grammar_persistence_v1) was BLOCKED because
frcg_agent.py emits selected_hypothesis_id as "grammar_0", "grammar_1", etc.
(idx-based names), but compute_wrong_grammar_persistence_v1 expects grammar name
strings like "direct_search", "required_dropdown_then_search" (ControlGrammar enum values).

The 8 ControlGrammar enum values (in order from grammar.py):
  0: "direct_search"
  1: "required_dropdown_then_search"
  2: "modal_confirm_then_action"
  3: "container_scroll_then_select"
  4: "wait_until_enabled_then_click"
  5: "permission_accept_then_action"
  6: "filter_open_then_select"
  7: "pagination_or_infinite_scroll"

Current code in src/frcgw/evaluation/frcg_agent.py at line ~110:
  self._last_selected_hypothesis_id = f"grammar_{best_grammar_idx}"

GOAL:
Add a static mapping dict and use it to emit grammar name strings instead of grammar_{idx}.

FILES_ALLOWED:
- src/frcgw/evaluation/frcg_agent.py (mapping dict + act() change ONLY)
- tests/test_step5_namespace_alignment.py

FILES_FORBIDDEN:
- outputs/**
- data/**
- paper_context_ref/**
- src/frcgw/schemas/**
- .claude/**
- scripts/run_codex_task.ps1
- src/frcgw/text_env/grammar.py (read-only reference only)

REQUIRED_IMPLEMENTATION:
1. In src/frcgw/evaluation/frcg_agent.py, add before the class definition:

```python
_GRAMMAR_IDX_TO_NAME: list[str] = [
    "direct_search",
    "required_dropdown_then_search",
    "modal_confirm_then_action",
    "container_scroll_then_select",
    "wait_until_enabled_then_click",
    "permission_accept_then_action",
    "filter_open_then_select",
    "pagination_or_infinite_scroll",
]
```

2. In the act() method, change the line that sets _last_selected_hypothesis_id from:
   `self._last_selected_hypothesis_id = f"grammar_{best_grammar_idx}"`
   to:
   `self._last_selected_hypothesis_id = _GRAMMAR_IDX_TO_NAME[best_grammar_idx] if best_grammar_idx < len(_GRAMMAR_IDX_TO_NAME) else f"grammar_{best_grammar_idx}"`

SAFETY:
- Do NOT add correct_hypothesis_id or any FORBIDDEN_AGENT_KEYS to agent observation or act() parameters
- Do NOT change eval_labels usage (must stay as accepted-but-ignored)
- Only change the _last_selected_hypothesis_id assignment line

3. In tests/test_step5_namespace_alignment.py, write 6 tests:
   - test_mapping_covers_all_8_grammars(): _GRAMMAR_IDX_TO_NAME has len==8 and all 8 ControlGrammar values
   - test_emitted_id_in_grammar_enum(): create TextFRCGModelAgent (no ckpt), call act() with synthetic obs, verify _last_selected_hypothesis_id is a valid ControlGrammar value string (not "grammar_0" etc.)
   - test_persistence_v1_computable_after_fix(): build synthetic episodes using grammar name strings, verify compute_wrong_grammar_persistence_v1 returns status=="OK"
   - test_no_oracle_leakage(): act() does not accept or use correct_hypothesis_id, oracle_grammar_action, or true_control_grammar
   - test_fallback_for_unknown_idx(): idx=99 → "_last_selected_hypothesis_id" starts with "grammar_"
   - test_regression_no_grammar_idx_in_output(): after fix, normal obs → _last_selected_hypothesis_id does NOT match pattern "grammar_\d+" (for idx 0-7)

REQUIRED_TESTS:
pytest tests/test_step5_namespace_alignment.py -q
Expected: 6 passed

ACCEPTANCE_CRITERIA:
- 6 tests pass
- frcg_agent.py emits grammar name strings for idx 0-7
- Fallback to f"grammar_{idx}" for unknown idx
- No FORBIDDEN_AGENT_KEYS added to observation or act() signature
- compute_wrong_grammar_persistence_v1 can now work on emitted hypothesis IDs

COMMIT_MESSAGE:
feat(step5/task3): C1 namespace alignment grammar_idx→grammar_name

STOP_CONDITION:
Stop if: (1) TextFRCGModelAgent import fails, (2) grammar.py enum order differs from
expected — report as BLOCKED and do not guess the order
