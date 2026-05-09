---
description: >
  사용자가 "code review", "simplify", "리뷰", "PR", "pull request" 언급 시 또는 PR 생성 직전에
  built-in /review와 /simplify 결과를 FRCG-WM scientific contract 관점에서 검토한다.
  simplification이 baseline/ablation/visibility/term 계약을 망가뜨리지 않도록 감시한다.
---

# frcgw-code-review

Source MDs: `CLAUDE.md` (Implementation Policy, Response Policy);
`.claude/rules/research_context_rules.md` (terms must-preserve, baselines must-not-disappear).

## FRCG-WM Term Preservation List (절대 rename 불가)

```
control grammar | regime | current hypothesis | alternative hypothesis |
falsification evidence | decision-relevant compute | action-interface rewrite |
wrong-control-grammar persistence
```

## Workflow (built-in wrap)

1. built-in `/review` 또는 `/simplify` 호출 결과 캡처.
2. diff에서 위 term rename, baseline/ablation 이름 변경, visibility bucket 평탄화 검색.
3. 위반 없으면 accept + 간략 summary.
4. 위반 있으면 reject 사유 명시 + 대안 제시.

## Forbidden Actions

- `/simplify` auto-edit를 검토 없이 수용.
- baseline/ablation 이름을 "리팩토링" 명목으로 rename (MUST NOT — tracking ID가 깨진다).
- visibility bucket을 단순화 명목으로 평탄화 (`AGENT_OBSERVATION` + `TRAINING_SUPERVISION` 혼합 금지).
- source MD docstring 제거 (every major module must cite its source MD).

## Required Output

```
Review target: <file or diff>
Term drift: <none / list of changed terms>
Baseline/ablation drift: <none / list>
Visibility change: <none / details>
Verdict: ACCEPT / REJECT
Reason: <if REJECT>
```
