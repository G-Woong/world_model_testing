# Phase R11 — RGB-D Extension

## Goal
Extend base WM encoder to handle RGB + depth + proprioception input.
Validate that core FGLC claims hold in visual modality.

## Architecture Extension

```
RGB image → CNN/ViT encoder → visual_token
proprio state → MLP → proprio_token
task extra → MLP → task_token
tokens fusion → cross-attention or concat → grouped latent z_t
```

ManiSkill provides RGB-D out of the box in state+sensor_data mode.

## Gate Criteria
- [ ] FGLC with RGB-D achieves comparable ID NLL to state-only (within 20%)
- [ ] OOD detection AUROC > 0.70 (slightly lower than state-only acceptable)
- [ ] Same ablation families run on 1 task (PickCube) with RGB-D

## Risk Register
- R-11 (ROADMAP/19): RGB-D encoder adds significant compute; may not fit in single A100 batch
- Optional: defer R11 if state-only results are strong enough for paper
