# 커밋 및 Git 전략

## 브랜치 정책
- 주요: `memory-redesign-2026-05-16` (현재)
- R14+ 이후: `paper-drafting-YYYY-MM-DD` 브랜치 생성
- main에 PR: R14 gate 통과 및 war-room synthesis PASS 후에만

## 관례적 커밋 어휘

| 접두사 | 의미 |
|---|---|
| `feat(fglc)` | src/fglc/의 새 기능 |
| `feat(data)` | 새 데이터 수집 또는 처리 |
| `feat(train)` | 학습 루프 또는 손실 구현 |
| `feat(detect)` | falsification gate / 불일치 탐지기 |
| `feat(attn)` | attention / CIRCA 개입 모듈 |
| `feat(correction)` | correction 어댑터 |
| `feat(plan)` | planner 통합 |
| `test(fglc)` | fglc를 위한 새 pytest |
| `results(R<N>)` | phase gate 결과 검증됨 |
| `docs(idea)` | docs/idea/ 업데이트 |
| `docs(roadmap)` | docs/ROADMAP/ 업데이트 |
| `chore(pivot)` | 피벗 관련 인프라 (Phase A에서 사용됨) |
| `chore(turn)` | 세션 종료 hook의 자동 커밋 |
| `fix(fglc)` | src/fglc/의 버그 수정 |

## 원자적 커밋 주기
- 논리적 단위당 하나의 커밋 (파일당이 아닌)
- 검증되지 않은 실험 결과 커밋 금지
- Phase gate sentinel은 gate 기준 검증 후에만 생성됨 (추측적으로 생성하지 않음)

## PR 경계
- R0..R7: 단일 브랜치, 순차적 커밋
- R8+: 각 알고리즘 (ASAP, I3G, IVI)에 대한 기능 브랜치 고려
- 논문 섹션: 코드 변경에서 별도 브랜치
