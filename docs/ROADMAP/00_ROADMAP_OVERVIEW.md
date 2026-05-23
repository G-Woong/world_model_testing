# ROADMAP 개요 — FGLC (R0..R16)

## 프로젝트 목표

FGLC (Falsification-Guided Latent Correction for World Model Planning) — ICLR 제출.
목표: falsification 유도 잠재 보정이 제어된 물리적 OOD 이동 하에서 ManiSkill 조작 태스크에서
TD-MPC2/DreamerV3/HiP-RSSM을 능가함을 보여줍니다.

## 마일스톤 요약

| 단계 | 목표 | 기간 (A100) | Gate sentinel |
|---|---|---|---|
| R0 | 계약 초기화 (완료) | 0 | R0.passed |
| R1 | 인프라: ManiSkill + src/fglc 스켈레톤 | 1일 | R1.passed |
| R2 | 데이터 파이프라인: state-only ID+OOD 데이터셋 | 2일 | R2.passed |
| R3 | 기본 world model: Stage 1 학습 수렴 | 3일 | R3.passed |
| R4 | Falsification gate: 보정된 β_t, OOD 탐지 AUROC > 0.75 | 2일 | R4.passed |
| R5 | CIRCA: 보정된 NLL < OOD에서 비보정 NLL | 3일 | R5.passed |
| R6 | Correction 모듈: necessity+sufficiency 테스트 통과 | 2일 | R6.passed |
| R7 | Planner: 폐쇄 루프 FGLC > 최소 1개 OOD 조건에서 TD-MPC2 | 4일 | R7.passed |
| R8 | 알고리즘 변형: ASAP, I3G, IVI 구현 + 비교 | 4일 | R8.passed |
| R9 | Ablation grid: 11가지 family + 결과 | 3일 | R9.passed |
| R10 | Baselines: TD-MPC2, DreamerV3, HiP-RSSM + 계산 매칭 | 5일 | R10.passed |
| R11 | RGB-D 확장: 동일한 ablation/baseline grid | 4일 | R11.passed |
| R12 | DROID/BridgeData 검증 | 5일 | R12.passed |
| R13 | Necessity/sufficiency 심층 평가: 시뮬레이션 오라클 | 2일 | R13.passed |
| R14 | 논문 구성 + 초안 작성 | 7일 | R14.passed |
| R15 | Reviewer 공격 방어 + 보충 자료 | 3일 | R15.passed |
| R16 | 최종 보고서 + 재현성 패키지 | 2일 | R16.passed |

**추정 총 A100 계산**: ~55일 (state-only Phase 1: ~25일)
**핵심 경로**: R3 → R4 → R5 → R7 → R10 (주요 주장 비교를 위해 baseline 필수)

## 커밋 주기 정책

완료된 phase gate당 하나의 커밋 (`docs/ROADMAP/18_COMMIT_AND_GIT_STRATEGY.md` 참조).
브랜치: R14 gate 통과까지 `memory-redesign-2026-05-16`; 그 후 PR to main.
Sentinel 규약: `outputs/phase_gates/R<N>.passed`.

## 성공 기준

**최소 실행 가능한 논문**:
1. R3 통과: 기본 WM이 ID에서 수렴 (NLL < 0.1 nat)
2. R4 통과: OOD 탐지 AUROC > 0.75 (대 0.5 무작위)
3. R7 통과: FGLC > TD-MPC2 return, ≥2 OOD 조건 (p < 0.05)
4. R9 통과: ABL-01 (no-correction) < OOD FGLC (문제 존재)
5. R10 통과: FGLC > HiP-RSSM OOD return (가장 가까운 경쟁자)
6. R14 통과: 논문 섹션 초안 완료

**전체 논문 (ICLR 목표)**:
17개 gate 모두 통과 + war-room synthesis PASS + reviewer-2 방어 완료.

## Phase Gate Sentinel 규약

```
outputs/phase_gates/R0.passed  ← 이 피벗으로 생성됨 (A.1..A.5 완료)
outputs/phase_gates/R1.passed  ← 인프라 검증 후
...
outputs/phase_gates/R16.passed ← 최종 보고서 완료
```

Phase gate는 `/fglc-phase-check --pass R<N>` 명령으로 생성되는 ZERO-BYTE 마커 파일입니다.
추측적으로 생성하지 마십시오.
