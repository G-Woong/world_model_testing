# Self-Evolution Log Template

근거: `docs/orchestration/08_AGENT_OUTPUT_CONTRACTS.md §6`

---

```markdown
---
evolution_id: SEV_YYYY-MM_NNN
date: <ISO 8601>
trigger: <RECURRING_FAILURE | USER_FEEDBACK | AGENT_REPORT | GATE_PATTERN | SCOPE_VIOLATION>
---

## OBSERVED_FAILURE
<무엇이 반복 실패했는가>

## EVIDENCE
| path | line | description |
|---|---|---|

## AFFECTED_COMPONENT
<03 | 04 | 05 | 06 | 07 | 08 | settings (requires human approval)>

## PROPOSED_IMPROVEMENT
<구체적 변경 내용 (what + where)>

## EXPECTED_BENEFIT
<기대 효과>

## RISK
<HIGH | MED | LOW>

## REQUIRED_APPROVAL
<HUMAN | AUTO>

## ADOPTION_STATUS
<ADOPTED | REJECTED | PENDING>

## ADOPTED_IN_BRANCH
<적용된 branch (없으면 none)>

## ROLLBACK_METHOD
<되돌리는 방법>

## NEXT_REVIEW_DATE
<YYYY-MM-DD>

## NOTES
<기타>
```
