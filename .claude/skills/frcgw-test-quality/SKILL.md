---
description: >
  코드/스크립트/스키마 변경 직후, phase gate 직전, 또는 사용자가 "tests", "pytest", "테스트" 언급 시
  targeted pytest 실행 권고, failure summary, fix loop, full gate test를 수행한다.
---

# frcgw-test-quality

Source MDs: `paper_context_ref/14_TRD_TECHNICAL_REQUIREMENTS_DOCUMENT_v1.md` §10;
`paper_context_ref/13_CLAUDE_CODE_EXECUTION_ROADMAP_v1.md` §16.

## File → Target Test Mapping

| Changed File Pattern | Target Tests |
|---|---|
| `src/frcgw/schemas/*.py` | `tests/test_visibility_contract.py tests/test_episode_schema.py tests/test_counterfactual_exclusion.py` |
| `src/frcgw/data/leakage_auditor.py` | `tests/test_leakage_auditor.py` |
| `src/frcgw/text_env/*.py` | `tests/test_text_env*.py` (P2+) |
| `src/frcgw/planning/*.py` | `tests/test_falsification.py tests/test_decision_gate.py` (P3+) |
| `src/frcgw/evaluation/*.py` | `tests/test_metrics.py tests/test_eval_runner.py` (P3+) |
| `configs/*.yaml` | `tests/test_config_validation.py` (if exists) |

## Checklist

1. 어떤 파일이 변경됐고 어떤 testcase가 영향받는가 (target mapping).
2. targeted pytest 결과.
3. 실패 시: 원인 1줄 + 수정 계획 + 다시 실행.
4. phase gate 직전이면 `pytest -q` (full) 실행.
5. 결과를 `outputs/test_reports/<UTC-timestamp>.txt`에 저장.

## Required Output

```
Changed files: <list>
Target tests: <list>
Result: <N passed, M failed>
Failed tests: <list + 1-line root cause>
Fix plan: <if any>
Gate ready: <YES/NO>
```

## Forbidden Actions

- 실패 testcase를 무시하고 다음 phase 작업 진행.
- `pytest --ignore` 광범위 사용.
- failure를 "intermittent"로 단정하고 재현 없이 pass 마크.

## Stop Condition

full pytest red 상태에서는 phase gate PASS 불가.
같은 testcase 2회 연속 fail이면 root-cause 명시 후 main agent에 fix 위임.
