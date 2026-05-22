# 22_NOVELTY_AND_THREATS — 신규성 및 위협

## 출처
- main.md §18 (HiP-RSSM/PLSM 차별화)
- deep-research-report.md §요약, §CIRCA 설명

## 직접 위협 표

모든 위협은 ≥2개 출처 교차 검증이 필요합니다 (C9 체크포인트). 인용 링크 MCP 검증 대기 중.

| 위협 | arXiv/DOI | 차별화 | 심각도 |
|---|---|---|---|
| TD-MPC2 (Hansen 2024) | 2310.16828 | FGLC는 falsification gate + correction 추가; TD-MPC2는 OOD 적응 메커니즘 없음 | 약함 (우리가 확장) |
| DreamerV3 (Hafner 2023) | 2301.04104 | Decoder 기반 RSSM; FGLC는 decoder-free; DreamerV3는 falsification/correction 없음 | 약함 |
| HiP-RSSM (Achterhold 2022) | 2206.14697 | HiP-RSSM: 어느 dynamics family인지 명시적 파라미터 추론; FGLC: 파라미터 추론 없이 falsification + sparse correction | 중간 (가장 가까운 경쟁자) |
| PLSM (Tomar 2024) | 2401.17835 | PLSM: 학습 시 action 효과를 더 체계적으로; FGLC: 추론 시 가설 위반 감지 및 보정 | 약함 |
| ReDRAW (잔차 WM) | 미정 | 잔차 잠재 correction; FGLC는 causal attention + necessity/sufficiency + value-aware 선택 추가 | 중간 |
| AdaWM (sim-to-real) | 미정 | 불일치 기반 적응; FGLC는 공식적 보정 + 그룹 수준 귀인 추가 | 중간 |
| CIRCA 인접 conformal RL | 최근 | FGLC의 conformal gate는 하나의 구성 요소; CIRCA는 conformal + 개입 + robust MPC 결합 | 약함 |
| iVAE (Khemakhem 2020) | arxiv 1907.04809 | iVAE는 I3G 알고리즘만의 구성 요소; 주요 FGLC 기여 아님 | 약함 |

## 핵심 신규성 주장

FGLC의 신규성은 world model correction 컨텍스트에서의 **조합**입니다:
1. 보정된 falsification 신호로서의 표준화된 불일치
2. 개입 정책으로 검증된 그룹 수준 correction attention (설명이 아닌)
3. Attention을 검증된 correction 정책으로 만드는 necessity/sufficiency 학습 손실
4. 개입 유효성/보정/효율성 트레이드오프의 다른 지점을 커버하는 4가지 알고리즘
   (CIRCA/ASAP/I3G/IVI)

이들 중 어느 것도 개별적으로는 새롭다고 주장하지 않습니다.
새로운 기여는 물리적 OOD 이동 하에서 잠재 world model correction을 위한 통합입니다.

## 2025/2026 신규성 위협 탐색

계획 §D.1에 따라 필수: 다음에 대한 arxiv 최근 12개월 탐색:
- "world model correction robotics" (world model correction 로봇공학)
- "latent correction world model" (잠재 correction world model)
- "falsification robotics planning" (falsification 로봇공학 planning)
- "causal attention world model" (causal attention world model)
- "sparse latent correction" (sparse latent correction)

상태: **MCP 검색 대기 중** (semantic-scholar + arxiv).
docs/orchestration/mcp_research/INDEX.md 참조.

## 연결 맵
- 상위: 17_ALGORITHM_COMPARISON.md (알고리즘 차별화)
- 하위: 25_PAPER_TITLE_CONTRIBUTIONS.md
- 검증: fglc-related-work-scout agent

## 체크포인트

- C2 신규성: **대기 중** — 위의 모든 위협 항목에 MCP 교차 검증 필요
- C9 관련 연구: **대기 중** — ≥2-출처 규칙은 항목당 arxiv + semantic-scholar 필요
- 기타 모든 체크포인트: C9 MCP 검증 완료까지 연기
