# Phase R8 — 알고리즘 변형 (ASAP, I3G, IVI)

## 목표
ASAP, I3G, IVI 알고리즘 구현. 모두 Stage 1 기반 WM 공유. CIRCA와 비교.

## 단계

1. **ASAP**: top-k 그룹에 대한 개입적 ASV 계산 추가; α에 증류
2. **I3G**: iVAE 인수분해 사전 분포 + ICP 불변성 페널티 추가; SPCI 보정
3. **IVI**: 1차 순위 매기기로서 영향 함수(기울기 norm) 추가; 무작위화된 knockout 검증

## Gate 기준
- [ ] 3가지 알고리즘 모두 발산 없이 학습됨
- [ ] 공유 Stage 1 가중치 동일 확인 (SHA256 일치)
- [ ] PickCube ID+OOD에서 4가지 알고리즘 비교 결과 사용 가능

## Codex 위임
예 — 3가지 별도 알고리즘 학습 변형 → TASK_R8_ALGORITHM_VARIANTS.md
