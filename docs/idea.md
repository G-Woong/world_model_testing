# FGLC — 아이디어 문서 (목차)

이 파일은 목차 포인터입니다. 실제 아이디어 내용은 `docs/idea/`에 있습니다.

## 탐색 시작점

`docs/idea/00_OVERVIEW.md`

## 모든 아이디어 단위 (27개 파일)

| 파일 | 내용 |
|---|---|
| 00_OVERVIEW.md | 탐색 지도, 44개 단위 M↔R 매트릭스, 체크포인트 상태 |
| 01_PROBLEM_FORMULATION.md | 4개 하위 문제, 개입 정책 구성 |
| 02_FALSIFICATION_THEORY.md | 표준화된 불일치, β gate, conformal vs CUSUM |
| 03_LATENT_DECOMPOSITION.md | K=6 그룹 토큰, iVAE 식별 가능성 |
| 04_BASE_WORLD_MODEL.md | TD-MPC2 기반, encoder, GRU belief, dynamics transformer |
| 05_BELIEF_MEMORY.md | GRU h_t, HiP-RSSM 비교 |
| 06_CAUSAL_ATTENTION.md | 개입 정책 α_t, sparse softmax/entmax |
| 07_CORRECTION_MECHANISM.md | 전이 어댑터 μ̃=μ+βαδ, tanh bounding |
| 08_ACTION_VALUE_RELEVANCE.md | Q 민감도, value 일관성 손실 |
| 09_NECESSITY_SUFFICIENCY.md | L_nec, L_suf, L_rand 학습 손실 |
| 10_LOSS_DESIGN.md | 10항 전체 손실, staged λ 스케줄 |
| 11_PLANNING_THEORY.md | MPPI/CEM corrected rollout, robust MPC, H_corr=3~5 |
| 12_TRAINING_STAGES.md | Stage 1-4 학습 프로토콜, 동결(freeze) 전략 |
| 13_ALGORITHM_CIRCA.md | CIRCA: Bernoulli gate + conformal + τ_g distill + robust MPC |
| 14_ALGORITHM_ASAP.md | ASAP: top-k + MC 개입적 ASV + α-distill |
| 15_ALGORITHM_I3G.md | I3G: iVAE + ICP/anchor + SPCI + sparse group gates |
| 16_ALGORITHM_IVI.md | IVI: influence 순위 + 무작위 knockout + sparse α |
| 17_ALGORITHM_COMPARISON.md | 4알고리즘 교차표: 유효성/보정/비용/예상 우위 |
| 18_DATA_BENCHMARKS.md | ManiSkill OOD 분할, 데이터 규칙 (취약 파일) |
| 19_BASELINES.md | 사라져서는 안 되는 baselines (취약 SSoT) |
| 20_ABLATIONS.md | 11개 ablation family (취약 SSoT) |
| 21_METRICS.md | 4축 지표 체계 |
| 22_NOVELTY_AND_THREATS.md | 직접 위협 표, 2025/2026 탐색 (MCP 검색 대기) |
| 23_FAILURE_MODES.md | 8개 실패 모드 및 완화 전략 |
| 24_OPEN_QUESTIONS.md | 6개 미해결 질문 |
| 25_PAPER_TITLE_CONTRIBUTIONS.md | 제목, 기여 사항, 초록 초안 |
| 26_CROSSCHECK_SUMMARY.md | C1..C10 체크포인트 매트릭스 요약 |

**체크포인트 상태**: 클러스터 1+3 검토 완료 (2026-05-22). 클러스터 2,4,5,6,7 + MCP 문헌 검색 대기 중.
