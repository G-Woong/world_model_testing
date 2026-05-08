"""frcgw.schemas — Data objects, visibility buckets, and validation.

Source docs:
- paper_context_ref/06_DATA_SCHEMA_AND_LABELING.md
- paper_context_ref/12_DATA_COLLECTION_METHODOLOGY_v1.md
- paper_context_ref/15_TDD_TECHNICAL_DESIGN_DOCUMENT_v1.md §5, §6

Hard constraints (placeholder; implementation deferred to P1):
- AGENT_OBSERVATION is the only VisibilityBucket allowed in inference input (TDD §5.1).
- FORBIDDEN_AGENT_FIELDS (TDD §5.4): true_regime, true_control_grammar,
  true_change_point, true_reveal_vs_shift, true_wrong_hypothesis,
  counterfactual_action_effects, oracle_regime_action, oracle_grammar_action,
  split_id, ood_type, template_id, seed, policy_id.
  None of these may appear in PublicObservation.
- schemas depends on nothing except utils (TDD §4 package layering).
"""
__all__: list[str] = []
