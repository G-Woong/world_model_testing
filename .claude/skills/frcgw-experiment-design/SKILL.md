---
description: >
  P3/P5/P6 실험 config 작성, eval runner 수정, ablation runner 수정, paper claim drafting 시
  claim → metric → baseline → ablation → split → pass/fail → failure interpretation을 1:1로 고정한다.
---

# frcgw-experiment-design

Source MDs: `paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md` §5 claim-to-evidence,
§6 metric, §7 baseline, §8 ablation, §11 compute-matched, §13 reviewer attack, §14 failure interpretation.

## Must-Not-Disappear Baselines

```
Frozen Base VLM/LLM | verifier-only | next-state-WM-only |
uncertainty-gated planner | always-plan world model | random alternative planner |
compute-matched random reallocation | oracle regime | oracle control grammar |
oracle alternative hypothesis
```

## Must-Not-Disappear Ablations

```
no-control-grammar | merged regime-control grammar | collapsed latent |
no-falsification | uncertainty instead of falsification | no-alternative-hypothesis |
random alternative | no-rollout | no-rewrite | no-progress/reward | no-compute-gate
```

## Claim-to-Evidence Template (실험마다 작성)

```
Claim ID: CLAIM-EVAL-<N>
Claim: <text>
Required Metric: <metric IDs>
Required Baseline: <baseline IDs>
Required Ablation: <ablation IDs>
Required Split: <split IDs>
Compute log active: <YES/NO>
Pass condition: <text>
Fail interpretation: <text>
```

## Checklist

1. 위 claim-to-evidence 표를 현재 phase에 대해 작성했는가.
2. must-not-disappear baseline/ablation 전부 config/runner에 존재하는가.
3. compute log (planning_calls, rollout_steps, wall-clock proxy) 활성화됐는가.
4. failure interpretation 섹션이 plan에 포함됐는가.
5. success rate 하나만 보고하는 것이 아닌가.

## Stop Condition

must-not-disappear baseline/ablation 1개라도 config/runner에서 누락 시
`BLOCKED: missing <name> — corresponding claim cannot be made`.
