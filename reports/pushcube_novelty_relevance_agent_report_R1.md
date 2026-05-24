# Agent E — Novelty Relevance Critic Report (PushCube-v1)

**상태**: PENDING — Agent A~D 보고서 완료 후 populate  
**Phase**: R2 data pipeline → R3 진입 전  
**트리거**: Stage 4 Agent E (plans/fglc-step-vectorized-iverson.md §G.5)  
**담당**: novelty-threat-scout + reviewer-2-attack-agent  
**입력**: Agent A~D 보고서 + docs/idea/02_FALSIFICATION_THEORY.md + 22_NOVELTY_AND_THREATS.md  

---

## 검사 항목 (plans/fglc-step-vectorized-iverson.md §I)

| # | Question | 기준 | 결과 |
|---|---|---|---|
| I1 | domain randomization vs dynamics hypothesis shift? | per-dim Cohen's d ≥ 3 dims > 0.3 | PENDING |
| I2 | ID 학습 가능, OOD prediction error 누적 가능? | Agent F PASS + Agent C gap 충분 | PENDING |
| I3 | falsification gate 감지 가능성? | OOD ρ_t 분포 ID와 분리 가능 | PENDING (R4 의존) |
| I4 | correction 필요 구조? | Agent C gap × Agent F ID NLL | PENDING |
| I5 | planning/action-value 영향? | reward KS p 기록 | PENDING |
| I6 | friction/mass가 다른 물리 shift? | 두 task 다른 latent dims 활성화 | PENDING |
| I7 | 6개 직접 위협 차별점 유지? | Agent E 명시 답변 | PENDING |

## 6개 직접 위협 방어 (I7) — 사전 분석

| 위협 | 차별점 | PushCube mass 추가 시 유지? |
|---|---|---|
| TD-MPC2 | falsification gate + latent correction (단순 model rollout과 다름) | 유지 |
| DreamerV3 | calibrated β gate + per-group δ (RSSM residual과 다름) | 유지 |
| HiP-RSSM | 파라미터 추론 없음 → latent correction | 유지 |
| PLSM | action-effect 체계성 vs falsification-driven | 유지 |
| ReDRAW | sparse group-wise correction vs dense residual | 유지 |
| AdaWM | online adaptation 없음 → in-context correction | 유지 |

(교차검증: synthesis RC1 보고서 `docs/orchestration/agent_reports/2026-05/mass_ood_root_cause_synthesis_RC1.md` 참조)

## Dual-task 정당성 (Reviewer 2 예상 공격)

**공격**: "왜 single task 아닌가?"  
**방어 논리**: "task가 어느 OOD axis에 sensitive한지 사전에 알 수 없다는 것 자체가 FGLC의 falsification gate가 task-agnostic해야 함을 보여주는 evidence. PickCube+friction, PushCube+mass 조합이 이 agnosticism을 empirically demonstrate."

## 판정

**PENDING** — Agent A~D 결과 수신 후 채워질 것.

최종 판정 기준:
- PASS: I1~I7 모두 PASS 또는 CONDITIONAL (R4+ 의존 항목 제외)
- CONDITIONAL_PASS: mass secondary tier 유지 시 (현재 권장)
- NOVELTY_AT_RISK: I7에서 위협 차별 무효화 시 → MCP 교차검증 후 사용자 보고
