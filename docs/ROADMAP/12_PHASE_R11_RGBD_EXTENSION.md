# Phase R11 — RGB-D 확장

## 목표
RGB + depth + 고유감각 입력을 처리하도록 기본 WM encoder 확장.
시각적 모달리티에서 핵심 FGLC 주장이 유지됨을 검증.

## 아키텍처 확장

```
RGB 이미지 → CNN/ViT encoder → visual_token
고유감각 상태 → MLP → proprio_token
태스크 추가 → MLP → task_token
토큰 융합 → cross-attention 또는 concat → 그룹화된 latent z_t
```

ManiSkill은 state+sensor_data 모드에서 기본적으로 RGB-D를 제공합니다.

## Gate 기준
- [ ] RGB-D가 있는 FGLC가 state-only와 비슷한 ID NLL 달성 (20% 이내)
- [ ] OOD 탐지 AUROC > 0.70 (state-only보다 약간 낮아도 허용)
- [ ] 동일한 ablation family가 1개 태스크 (PickCube)에서 RGB-D로 실행됨

## 위험 등록부
- R-11 (ROADMAP/19): RGB-D encoder가 상당한 계산을 추가; 단일 A100 배치에 안 맞을 수 있음
- 선택적: state-only 결과가 충분히 강하면 R11 연기 가능
