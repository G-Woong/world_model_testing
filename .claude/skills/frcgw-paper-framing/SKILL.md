---
description: >
  abstract/intro/related work/limitation/claim wording 작성 시 사용한다.
  generic Web/GUI world model claim으로 흐르는 것을 방지하고
  direct threats(WebWorld/CUWM/WAC/VeriGUI)에 대한 방어를 강제한다. P7/P8 핵심.
---

# frcgw-paper-framing

Source MDs: `paper_context_ref/00_MASTER_REFERENCE.md`;
`paper_context_ref/01_RELATED_WORK_THREAT_MAP.md` (WebWorld/CUWM/WAC/VeriGUI);
`paper_context_ref/02_PROBLEM_NOVELTY_FALSIFICATION.md`;
`paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md` §13 reviewer attack defense;
`paper_context_ref/FINAL_RESEARCH_BLUEPRINT.md`.

## Core Identity Preservation

이 논문은 **generic Web/GUI world model이 아니다**. 핵심:

```
wrong-control-grammar hypothesis persistence
→ action-effect evidence
→ current hypothesis falsification
→ alternative control-grammar hypothesis
→ short rollout
→ decision-relevant compute gate
→ action-interface rewrite
```

## Forbidden Claims

- "generic Web/GUI world model" novelty.
- success rate만으로 mechanism claim.
- WebWorld/CUWM/WAC/VeriGUI를 related work에서 무시.
- unresolved Unknown을 final claim으로 승격.
- synthetic counterfactual label이 real-world에도 있다고 주장.

## Claim Defense Template

```
Claim: <text>
Supporting metric: <metric ID>
Supporting baseline: <baseline ID>
Supporting ablation: <ablation ID>
Reviewer attack: <threat ID>
Defense: <1-2 sentences>
```

## Checklist

1. 모든 claim이 claim defense template으로 채워졌는가.
2. direct threats(WebWorld, CUWM, WAC, VeriGUI) 각각에 대한 defense가 존재하는가.
3. empirical evidence 없이 acceptance-level claim을 주장하고 있지 않은가.
4. text-only success를 Web/GUI evidence로 일반화하고 있지 않은가.

## Stop Condition

supporting metric/baseline/ablation 없는 claim 1개라도 있으면 `BLOCKED: unsupported claim`.
