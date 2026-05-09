---
description: >
  `src/frcgw/schemas/`, `src/frcgw/data/`, `src/frcgw/text_env/collector.py`,
  `src/frcgw/gui_env/collector.py`, `src/frcgw/logging/` 변경 시 hidden label /
  counterfactual / audit metadata가 inference input에 들어가지 않도록 보장한다.
  데이터/스키마/수집기/배치 입력 작업 시 반드시 사용한다.
---

# frcgw-data-safety

Source MDs: `paper_context_ref/06_DATA_SCHEMA_AND_LABELING.md` §0.3, §0.4, §4, §14, §15;
`paper_context_ref/12_DATA_COLLECTION_METHODOLOGY_v1.md`.

## Forbidden Inference Fields (절대 agent observation/dataloader input/model input/prompt에 불가)

```
true_regime, true_control_grammar, true_change_point, true_reveal_vs_shift,
true_wrong_hypothesis, counterfactual_action_effects, counterfactual_progress_delta,
counterfactual_failure_risk, counterfactual_best_alternative,
oracle_regime_action, oracle_grammar_action, oracle_best_action,
split_id, ood_type, template_id, seed, policy_id, audit_metadata
```

## Visibility Buckets

| Bucket | Examples | Agent Input? |
|---|---|---|
| AGENT_OBSERVATION | `public_*`, `*_sanitized`, `dom_tree_sanitized`, `previous_action_public` | YES |
| TRAINING_SUPERVISION | `true_*` | NO (label only) |
| EVALUATION_ONLY | `oracle_*`, `true_task_success`, `executed_hypothesis` | NO (eval only) |
| COUNTERFACTUAL_ONLY | `counterfactual_*` | NO (separate shard) |
| AUDIT_METADATA | `audit_*`, `leakage_*`, `split_id`, `seed` | NO |

## Checklist

1. 변경 파일이 visibility bucket을 명시했는가.
2. `build_agent_observation()` 또는 동치 함수가 forbidden fields를 strip하는가.
3. counterfactual shard가 별도 file/struct에 격리됐는가.
4. `tests/test_visibility_contract.py` + `tests/test_counterfactual_exclusion.py` + `tests/test_leakage_auditor.py` 실행됐는가.
5. P1 통과 testcase가 그대로 통과하는가.

## Required Output

```
Visibility Audit:
  - changed: <file>
  - bucket declared: <YES/NO>
  - forbidden fields in obs path: <none / list>
  - counterfactual isolated: <YES/NO>
  - tests: <list> → <PASS/FAIL>
  - gate: <PASS/BLOCKED>
```

## Stop Condition

forbidden field가 agent observation / dataloader input / model input path에 1개라도 섞이면
즉시 `BLOCKED: leakage detected — dataset shard invalid`.
