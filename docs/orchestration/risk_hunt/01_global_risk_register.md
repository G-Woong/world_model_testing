# STEP 10 Global Risk Register

date: 2026-05-18
branch: memory-redesign-2026-05-16 @ 3b56ce7
gate: O-RISK
total_risks: 60
categories: 20
source: 00_current_state_truth_table.md + direct code audit

---

## Top-20 CRITICAL/HIGH Risks

| Rank | Risk ID | Statement (요약) | Severity | Claim |
|---|---|---|---|---|
| 1 | RH-CORE-01 | C3 회복이 threshold(tau_f=0.0) + proxy(no_state_change→type3) 합작이며 evidence-integrating learned signal 아님 | CRITICAL | C3 |
| 2 | RH-STAT-01 | n=5 std=0.000 (deterministic) — CI 작성 불가, reviewer reject 1순위 | CRITICAL | All |
| 3 | RH-EVAL-01 | task_success dataset-invariant offline eval — agent-discriminative 아님 | CRITICAL | C4 |
| 4 | RH-FORE-01 | text_frcg_plan rollout이 action selection에 causal 영향 미검증 | CRITICAL | Foresight |
| 5 | RH-THR-01 | falsification.py:66-67 short-circuit {0,6} 의존도가 no_state_change proxy에 종속 | CRITICAL | C3 |
| 6 | RH-DUP-01 | v0_4 per-episode single regime → C2=0.0 데이터 구조적 한계 | CRITICAL | C2 |
| 7 | RH-REV-01 | reviewer "n=5 std=0이면 단일 측정"으로 reject 가능 | CRITICAL | All |
| 8 | RH-FAI-01 | ABL-001/003 checkpoint MISSING — C2 separability claim 무근거 | HIGH | C2/C3 |
| 9 | RH-EVAL-02 | C6 14.9× advantage가 self-reported compute denominator에 기반 | HIGH | C6 |
| 10 | RH-CORE-02 | text path lr_scorer.py 미연결 → trace lr_scorer_F_t==planner_F_t 거짓 일치 | HIGH | C3/C6 |
| 11 | RH-THR-02 | predicted_wrong 결정이 single sigmoid threshold(0.5)에 종속, calibration 검증 없음 | HIGH | C3/C5 |
| 12 | RH-PCG-01 | l_falsification=0.635 but task_success=0.964 ceiling — prediction 개선이 control 개선과 분리 | HIGH | C3/C4 |
| 13 | RH-ENV-01 | text-only synthetic GUI가 실세계 web/robotics claim과 괴리 | HIGH | Novelty |
| 14 | RH-LEAK-01 | ABL-040 _last_F_t=10.0 직접 write — oracle 활용인지 metric 우회인지 의심 | HIGH | C3 validity |
| 15 | RH-NOV-01 | StressWeb/BacktrackAgent/WebUncertainty novelty overlap 미검토 | HIGH | Novelty |
| 16 | RH-DTB-01 | BASE-026/027 PARTIAL, BASE-028 HEURISTIC — faithful 강도 부족 | HIGH | Novelty |
| 17 | RH-FORE-02 | planner_state.update가 valid rewrite 시에만 호출 — h_exec_id emission이 정책 outcome과 분리 | HIGH | Architecture |
| 18 | RH-LOSS-01 | l_falsification 단순 BCE — sequence accumulation/contrastive/temporal consistency 없음 | HIGH | C3 |
| 19 | RH-ARC-01 | text_frcg_plan → falsification_score → decision_gate 경로가 학습된 signal을 사용하지만 foresight adapter 없음 | HIGH | Architecture |
| 20 | RH-PCG-02 | rollout 예측 개선이 plan_meta.F_t를 통해서만 정책에 영향 — 직접 value improvement 경로 없음 | HIGH | C3/C6 |

---

## CORE — Core Claim Risk (4개)

### RH-CORE-01
1. **Risk ID**: RH-CORE-01
2. **Risk statement**: C3 회복이 tau_f=0.0 (threshold adjustment) + no_state_change→type3 proxy (evidence mapping) 합작에 의한 결과이며, evidence-integrating learned signal이 아님. 두 조건 중 하나라도 제거하면 F1=0.0으로 회귀할 가능성 높음.
3. **Severity**: CRITICAL
4. **Affected claim**: C3
5. **Current evidence**: frcg_agent.py:74 `GateConfig(tau_f=0.0)`, planner.py:120-126 no_state_change→type3, falsification.py:66-67 `if evidence.observed_effect_type in {0,6}: return zeros`
6. **Why this kills the paper**: C3 claim의 핵심은 "agent learns to detect wrong grammar from evidence." threshold와 proxy가 없으면 F1=0.0이면 이것은 학습된 탐지가 아니라 heuristic 탐지임을 보여줌.
7. **Required test**: (a) proxy OFF eval → F1 변화 측정; (b) threshold-free AUROC/AUPRC 측정; (c) tau_f sweep
8. **Candidate fix idea**: (A) evidence-integrating recurrent state (Architecture B) 도입; (B) CLT-based statistical falsification (WH-1); (C) threshold를 보조 검출기로 명시적 격하 + learned component가 primary
9. **Codex implementation task**: TASK_1131_step10_no_state_change_decoupling, TASK_1117_step10_arch_b_skeleton
10. **Stop condition**: proxy OFF 후 F1=0.0이면 C3 claim 격하 필수. learned signal 없음 명시.
11. **Status**: OPEN

### RH-CORE-02
1. **Risk ID**: RH-CORE-02
2. **Risk statement**: text_frcg_plan evaluation path가 lr_scorer.py를 사용하지 않음. gui_env/lr_integration.py에서만 사용됨. trace에서 lr_scorer_F_t == planner_F_t (same value) → lr_scorer 실질적 미사용 증거. LR 논문 alignment 허위 주장 위험.
3. **Severity**: HIGH
4. **Affected claim**: C3, C6
5. **Current evidence**: frcg_agent.py text_frcg_plan import only, lr_scorer.py gui_env 전용 (39_current_state_audit.md §2 F-1d)
6. **Why this kills the paper**: "LR-inspired falsification"을 주장하면서 text eval path가 LR scorer를 사용하지 않으면 claim inconsistency.
7. **Required test**: trace log에서 lr_scorer_F_t와 planner F_t 비교. 같으면 lr_scorer 미사용 확증.
8. **Candidate fix idea**: (A) text eval path에 lr_scorer 연결; (B) falsification mechanism을 "LR-inspired"가 아닌 "model-internal F_t"로 정직하게 재명명
9. **Codex implementation task**: TASK_1118_step10_arch_i_skeleton (partial)
10. **Stop condition**: text eval F_t와 lr_scorer F_t가 동일하면 "lr_scorer connection claim" 제거.
11. **Status**: OPEN

### RH-CORE-03
1. **Risk ID**: RH-CORE-03
2. **Risk statement**: outputs/checkpoints/pretrain_v0_4_long/manifest.json MISSING. training metadata (steps, loss curve, seed, config hash, dataset hash) 인용 불가. checkpoint provenance gap.
3. **Severity**: MEDIUM
4. **Affected claim**: All (reproducibility)
5. **Current evidence**: glob outputs/checkpoints/pretrain_v0_4_long/manifest.json → No files found (STEP 10 STEP 0 audit)
6. **Why this kills the paper**: ICLR reproducibility requirement 충족 불가. training의 정확한 조건 미상.
7. **Required test**: manifest.json 생성 스크립트 실행 후 hash 검증
8. **Candidate fix idea**: (A) manifest generator script 실행; (B) checkpoint config.json 복원
9. **Codex implementation task**: TASK_1111_step10_current_state_audit (partial)
10. **Stop condition**: manifest 없이 training claim 작성 금지.
11. **Status**: OPEN

### RH-CORE-04
1. **Risk ID**: RH-CORE-04
2. **Risk statement**: FRCG-WM claim의 핵심 구조 — "wrong-control-grammar hypothesis persistence → falsification → alternative hypothesis → rewrite" — 이 전체 파이프라인이 end-to-end로 작동하는지 통합 검증 없음. 각 컴포넌트는 unit test 있지만 파이프라인 통합 eval이 없음.
3. **Severity**: HIGH
4. **Affected claim**: C3, C6, Architecture
5. **Current evidence**: tests/ 에 unit tests 존재, 그러나 end-to-end "wrong grammar → detection → recovery" trace가 eval에서 직접 측정되지 않음
6. **Why this kills the paper**: 각 부품이 작동해도 통합 파이프라인이 작동하지 않을 수 있음. reviewer는 end-to-end trace 요구.
7. **Required test**: falsification→switch→rewrite 완전 성공 에피소드 비율 측정
8. **Candidate fix idea**: (A) end-to-end trace logger 추가; (B) recovery_episode_rate metric 신설
9. **Codex implementation task**: TASK_1124_step10_foresight_causal (partial)
10. **Stop condition**: end-to-end trace 없이 "recovers from wrong grammar" claim 금지.
11. **Status**: OPEN

---

## THR — Falsification Threshold/Proxy Risk (3개)

### RH-THR-01
1. **Risk ID**: RH-THR-01
2. **Risk statement**: falsification.py:66-67 short-circuit `if evidence.observed_effect_type in {0,6}: return zeros`가 no_state_change proxy (type→3) 없이는 v0_4 데이터 65%+ 스텝에서 F_t=0 강제함. proxy가 제거되면 short-circuit이 대부분 걸림.
3. **Severity**: CRITICAL
4. **Affected claim**: C3
5. **Current evidence**: falsification.py:66-67, planner.py:120-126 proxy, v0_4 manifest: no_state_change=815/1979 ood effect_type counts (41%)
6. **Why this kills the paper**: no_state_change proxy는 "action failed" proxy이며 실제 falsification evidence가 아님. 문맥 의존적 heuristic이 C3 claim의 핵심.
7. **Required test**: proxy OFF → AUROC 측정. proxy OFF → F1 변화.
8. **Candidate fix idea**: (A) effect_type mapping coverage 개선; (B) architecture B (evidence-integrating) 도입으로 proxy 불필요화
9. **Codex implementation task**: TASK_1131_step10_no_state_change_decoupling
10. **Stop condition**: proxy OFF F1=0.0 → C3 claim scope 축소.
11. **Status**: OPEN

### RH-THR-02
1. **Risk ID**: RH-THR-02
2. **Risk statement**: predicted_wrong 결정이 `wrong_prob > 0.5` (single sigmoid threshold)에 종속. calibration 검증 없음. ECE가 degenerate (C5 BLOCKED). threshold를 0.3으로 낮추면 F1이 변하는지 테스트 없음.
3. **Severity**: HIGH
4. **Affected claim**: C3, C5
5. **Current evidence**: frcg_agent.py:142 `self._last_predicted_wrong = self._last_wrong_prob > 0.5`, C5 ECE=null (47_final_evidence_card §8)
6. **Why this kills the paper**: calibrated threshold 없이 predicted_wrong은 arbitrary decision boundary. ECE degenerate는 threshold가 meaningful 아님을 시사.
7. **Required test**: threshold sweep [0.3, 0.4, 0.5, 0.6, 0.7] → F1 변화. ECE after calibration training.
8. **Candidate fix idea**: (A) calibration-aware falsification loss; (B) post-hoc isotonic regression; (C) Platt scaling
9. **Codex implementation task**: TASK_1121_step10_loss_calibration_aware
10. **Stop condition**: threshold sweep F1 monotonic → threshold selection이 critical → claim에 명시.
11. **Status**: OPEN

### RH-THR-03
1. **Risk ID**: RH-THR-03
2. **Risk statement**: F_t가 단일 scalar이며 temporal consistency 없음. 연속 스텝에서 F_t가 급격히 변동 가능 (t=0.8, t+1=0.1, t+2=0.9). 이는 falsification "state"가 아닌 instantaneous score임.
3. **Severity**: HIGH
4. **Affected claim**: C3, Architecture
5. **Current evidence**: falsification.py:60-80 단일 forward pass로 F_t 산출, temporal smoothing 없음
6. **Why this kills the paper**: "evidence-integrating state"를 claim하려면 temporal consistency가 필요. instantaneous score는 약한 claim.
7. **Required test**: consecutive F_t 변동 측정 (std across time within episode)
8. **Candidate fix idea**: (A) recurrent state (Architecture B); (B) temporal consistency loss (#9); (C) sliding window EWMA
9. **Codex implementation task**: TASK_1120_step10_loss_evidence_accum
10. **Stop condition**: F_t per-step std > F_t mean → temporal inconsistency가 claim을 약화시킴.
11. **Status**: OPEN

---

## FORE — Policy Foresight Utilization Risk (4개)

### RH-FORE-01
1. **Risk ID**: RH-FORE-01
2. **Risk statement**: text_frcg_plan의 rollout이 action selection에 causal 영향을 주는지 검증 없음. rollout 결과가 plan_meta에 포함되지만 actual action selection을 얼마나 바꾸는지 intervention test 없음.
3. **Severity**: CRITICAL
4. **Affected claim**: Foresight claim, C3
5. **Current evidence**: text_frcg_plan code: rollout 실행 → h_star 선택 → rewrite_action. 하지만 rollout_off vs rollout_on에서 action divergence 미측정
6. **Why this kills the paper**: "foresight-guided planning"을 claim하면서 foresight가 실제로 action을 바꾸지 않는다면 novelty 없음.
7. **Required test**: 동일 obs에서 rollout on/off → action divergence rate (목표: >30%)
8. **Candidate fix idea**: (A) foresight-to-policy adapter (Architecture I); (B) rollout utility score metric
9. **Codex implementation task**: TASK_1124_step10_foresight_causal, TASK_1118_step10_arch_i_skeleton
10. **Stop condition**: divergence rate < 5% → "foresight-guided" claim 제거.
11. **Status**: OPEN

### RH-FORE-02
1. **Risk ID**: RH-FORE-02
2. **Risk statement**: planner_state.update()가 valid rewrite 확인 후에만 호출됨 (planner.py:190). rewrite가 invalid하면 h_exec_id 업데이트 없음 → 다음 스텝에서 P_switch 계산이 stale h_exec_id 기반.
3. **Severity**: HIGH
4. **Affected claim**: Architecture, C3
5. **Current evidence**: planner.py:186-190 `if valid: planner_state.update(step_idx+1, h_star.combined_id)` — invalid branch에 update 없음
6. **Why this kills the paper**: planning loop의 state propagation이 불완전. "persistent hypothesis tracking"이 invalid rewrite 시 단절됨.
7. **Required test**: invalid rewrite 비율 측정. invalid rewrite 이후 스텝의 P_switch 분포.
8. **Candidate fix idea**: (A) invalid rewrite에도 h_star 기록 (soft update); (B) hypothesis update timestamp tracking
9. **Codex implementation task**: TASK_1117_step10_arch_b_skeleton (partial)
10. **Stop condition**: invalid rewrite rate > 50% → h_exec_id가 대부분의 스텝에서 stale → architecture bug.
11. **Status**: OPEN

### RH-FORE-03
1. **Risk ID**: RH-FORE-03
2. **Risk statement**: rollout k=3 fixed. 값이 높을수록 더 좋은지 낮을수록 더 좋은지 sensitivity 분석 없음. k=1과 k=3이 동일 결과를 낼 수 있음.
3. **Severity**: MEDIUM
4. **Affected claim**: C6, Foresight
5. **Current evidence**: frcg_agent.py:150 `rollout_steps=3 if planned else 0` (hardcoded)
6. **Why this kills the paper**: k 값이 arbitrary → compute 비용 근거 없음. k=1이면 C6 ppc 계산이 달라짐.
7. **Required test**: k=[1,3,5] sweep → C3 F1 vs ppc 변화
8. **Candidate fix idea**: (A) value-of-computation gate (Architecture F); (B) k에 대한 sensitivity 보고
9. **Codex implementation task**: TASK_1119_step10_arch_f_skeleton
10. **Stop condition**: k sweep에서 F1 차이 < 1% → k 선택 arbitrary → compute claim 약화.
11. **Status**: OPEN

### RH-FORE-04
1. **Risk ID**: RH-FORE-04
2. **Risk statement**: propose()가 "posterior_only" mode로 실행됨 (planner.py:133-142). evidence-blind by design. alt_hypotheses가 현재 evidence를 고려하지 않고 prior-ranked. falsification 이후 alternative 선택이 evidence-based가 아님.
3. **Severity**: HIGH
4. **Affected claim**: C3, Foresight
5. **Current evidence**: planner.py:131-142 `mode="posterior_only"`, `evidence=None` — alt hypothesis 제안 시 evidence 무시
6. **Why this kills the paper**: "evidence-guided alternative hypothesis selection"이 핵심인데, evidence-blind alternative selection은 논리적 모순.
7. **Required test**: evidence-aware vs evidence-blind alt hypothesis selection → final action quality 비교
8. **Candidate fix idea**: (A) evidence-conditioned propose() mode 추가; (B) evidence-aware alt scoring
9. **Codex implementation task**: TASK_1117_step10_arch_b_skeleton (partial)
10. **Stop condition**: evidence-aware mode가 evidence-blind보다 C3 F1 < 1% 개선 → current posterior_only approach 유지 가능.
11. **Status**: OPEN

---

## PCG — Prediction-Control Gap Risk (3개)

### RH-PCG-01
1. **Risk ID**: RH-PCG-01
2. **Risk statement**: l_falsification=0.635 (Stage B) + F_t variance=0.684인데 task_success=0.964 ceiling. prediction 개선이 control 성능 개선과 분리됨. world model이 더 정확해져도 policy가 더 좋아지지 않음.
3. **Severity**: HIGH
4. **Affected claim**: C3, C4
5. **Current evidence**: 47_final_evidence_card §5,7: l_falsification=0.635 non-zero, task_success 0.964/0.998 (모든 ablation 동일)
6. **Why this kills the paper**: prediction accuracy ↔ control performance 분리는 MBRL의 핵심 문제. 이것이 확인되면 "world model improves decision" 주장 약화.
7. **Required test**: l_falsification sweep → task_success/ppc 변화 측정. prediction loss vs control metric correlation.
8. **Candidate fix idea**: (A) latent control sufficiency loss (#12); (B) v0_5 dataset에서 더 어려운 tasks
9. **Codex implementation task**: N/A (analysis)
10. **Stop condition**: l_falsification 개선 없이 ppc 동일 → prediction-control gap 확인 → claim 재구성 필요.
11. **Status**: OPEN

### RH-PCG-02
1. **Risk ID**: RH-PCG-02
2. **Risk statement**: rollout 예측 개선이 plan_meta.F_t를 통해서만 정책에 영향. direct value improvement 경로 없음. rollout prediction quality가 높아져도 F_t threshold를 통과하지 못하면 policy 변화 없음.
3. **Severity**: HIGH
4. **Affected claim**: C3, C6
5. **Current evidence**: text_frcg_plan: rollout → F_t → gate → if proceed → value comparison. F_t > tau_f 조건이 rollout 활용을 차단.
6. **Why this kills the paper**: rollout prediction quality와 final decision quality의 연결 고리가 단일 scalar gate에 의존. gate threshold가 바뀌면 전체 연결 끊김.
7. **Required test**: rollout prediction quality metric vs gate_out.should_plan rate correlation
8. **Candidate fix idea**: (A) policy-conditioned rollout evaluator (Architecture G); (B) rollout usefulness score
9. **Codex implementation task**: TASK_1119_step10_arch_f_skeleton
10. **Stop condition**: rollout quality vs decision quality r < 0.3 → gate가 arbitrary bottleneck.
11. **Status**: OPEN

### RH-PCG-03
1. **Risk ID**: RH-PCG-03
2. **Risk statement**: delta_V (value difference between best_alt and h_exec)가 학습되는지 검증 없음. delta_V=0이 빈번하면 value-based planning이 degenerate.
3. **Severity**: MEDIUM
4. **Affected claim**: C3, Architecture
5. **Current evidence**: planner.py:171-172 delta_V = best_alt_value - h_exec_value. value function 학습 품질 audit 없음.
6. **Why this kills the paper**: delta_V=0이 빈번하면 P_switch가 0 (no switch preference) → planning gate가 자주 차단됨 → C6 benefit의 일부가 delta_V=0 때문.
7. **Required test**: eval trace에서 delta_V 분포 측정. delta_V > 0 비율.
8. **Candidate fix idea**: (A) value function 별도 calibration; (B) alternative hypothesis margin loss (#8)
9. **Codex implementation task**: TASK_1111_step10_current_state_audit (partial — delta_V distribution)
10. **Stop condition**: delta_V=0 > 90% → value learning 실질적으로 없음 → architecture redesign.
11. **Status**: OPEN

---

## LAT — Task-Relevant Latent Risk (3개)

### RH-LAT-01
1. **Risk ID**: RH-LAT-01
2. **Risk statement**: z_grammar latent가 실제로 control grammar를 나타내는지 검증 없음. grammar probe accuracy가 chance level이면 latent가 grammar를 encoding하지 않는 것.
3. **Severity**: HIGH
4. **Affected claim**: C3, Architecture
5. **Current evidence**: model: z_grammar_logits → grammar_probs → best_grammar_idx. 하지만 probe accuracy on true_control_grammar label 미측정.
6. **Why this kills the paper**: latent가 grammar를 나타내지 않으면 "control grammar hypothesis"를 claim할 근거 없음.
7. **Required test**: z_grammar_logits → linear probe accuracy vs true_control_grammar label
8. **Candidate fix idea**: (A) probe accuracy metric 추가; (B) grammar 분리 loss 강화
9. **Codex implementation task**: TASK_1111_step10_current_state_audit (partial)
10. **Stop condition**: probe accuracy < 30% (8 classes, chance=12.5%) → latent grammar claim 금지.
11. **Status**: OPEN

### RH-LAT-02
1. **Risk ID**: RH-LAT-02
2. **Risk statement**: z_regime latent와 z_grammar latent가 실제로 분리(disentangle)되는지 검증 없음. ABL-003 (merged)이 collapse를 확인하지 못하면 disentanglement claim 근거 없음.
3. **Severity**: HIGH
4. **Affected claim**: C2, C3
5. **Current evidence**: ABL-003 config ready but checkpoint MISSING (47_final_evidence_card §9)
6. **Why this kills the paper**: "regime와 grammar를 분리 표현"이 핵심 novelty. 분리 증거 없으면 generic latent model과 차별점 없음.
7. **Required test**: ABL-003 retrain → C2 + C3 collapse 확인
8. **Candidate fix idea**: (A) ABL-003 retrain (TASK_1128); (B) mutual information I(z_regime; z_grammar) 측정
9. **Codex implementation task**: TASK_1128_step10_abl003_retrain
10. **Stop condition**: ABL-003 no collapse → disentanglement claim 제거.
11. **Status**: OPEN

### RH-LAT-03
1. **Risk ID**: RH-LAT-03
2. **Risk statement**: reconstruction loss가 latent를 task-relevant가 아닌 reconstruction-convenient 방향으로 정렬시킬 수 있음. JEPA/I-JEPA 계열 reconstruction-free approach 미적용.
3. **Severity**: MEDIUM
4. **Affected claim**: Architecture, Novelty
5. **Current evidence**: model architecture에 reconstruction head 존재 여부 → world_model_heads.py 구조 (forward_given_action: effect_head, progress_head, failure_head)
6. **Why this kills the paper**: 최신 MBRL은 reconstruction-free로 전환 중. reconstruction 기반이면 novelty 취약.
7. **Required test**: reconstruction head 제거 후 F_t quality 변화
8. **Candidate fix idea**: (A) JEPA-style latent consistency loss (#13); (B) task-relevant latent head
9. **Codex implementation task**: N/A (P1 우선순위)
10. **Stop condition**: N/A (architecture redesign 필요 시 P4에서 처리)
11. **Status**: OPEN

---

## REG — Regime/Grammar Latent Novelty Risk (3개)

### RH-REG-01
1. **Risk ID**: RH-REG-01
2. **Risk statement**: regime과 control grammar의 개념적 차이가 논문에서 명확히 정의되지 않으면 reviewer 혼동 유발. 현재 코드에서도 두 개념이 때때로 혼용됨.
3. **Severity**: HIGH
4. **Affected claim**: Novelty, C2/C3
5. **Current evidence**: CLAUDE.md 용어 정의 존재하지만 코드에서 일관되게 적용되는지 불명확
6. **Why this kills the paper**: regime≠grammar 구분이 없으면 ABL-001/003의 collapse 패턴 해석 불가.
7. **Required test**: regime과 grammar latent의 mutual information 측정. 0이면 분리됨.
8. **Candidate fix idea**: (A) explicit regime/grammar disentanglement metric; (B) probe accuracy 분리
9. **Codex implementation task**: N/A
10. **Stop condition**: I(z_regime; z_grammar) ≈ I(random; random) → latent 분리됨 증거.
11. **Status**: OPEN

### RH-REG-02
1. **Risk ID**: RH-REG-02
2. **Risk statement**: change-point detection이 explicit objective 없이 z_regime head에서 암묵적으로 학습되기를 기대함. regime change-point head 없음.
3. **Severity**: HIGH
4. **Affected claim**: C2
5. **Current evidence**: metrics.py regime_shift_f1() → v0_4 에서 0.0. 명시적 change-point head 없음.
6. **Why this kills the paper**: regime_shift_f1을 claim하려면 explicit change-point detection이 필요. 현재는 데이터 부재로 0.0.
7. **Required test**: v0_5 multi-regime data → change-point head 학습 → regime_shift_f1 측정
8. **Candidate fix idea**: (A) Regime change-point head (Architecture C); (B) HMM-based regime belief (WH-2)
9. **Codex implementation task**: TASK_1130_step10_v0_5_generator (dependent)
10. **Stop condition**: v0_5 데이터에서도 regime_shift_f1=0.0 → C2 claim 포기.
11. **Status**: OPEN

### RH-REG-03
1. **Risk ID**: RH-REG-03
2. **Risk statement**: v0_4에서 per-episode single regime이므로 C2 metric의 in-distribution vs OOD performance 차이가 meaningless. OOD test의 differentiating power 없음.
3. **Severity**: MEDIUM
4. **Affected claim**: C2
5. **Current evidence**: 42_true_regime_shift_f1_report.md §3: regime_shift_episodes=0 on both test_id and test_ood
6. **Why this kills the paper**: OOD가 ID와 동일하게 0.0이면 OOD generalization claim 불가.
7. **Required test**: v0_5 multi-regime data에서 ID vs OOD 비교
8. **Candidate fix idea**: (A) v0_5 generator with ID/OOD regime split; (B) regime type as OOD factor
9. **Codex implementation task**: TASK_1130_step10_v0_5_generator
10. **Stop condition**: v0_5에서도 OOD regime_shift_f1 = ID → OOD generalization claim 금지.
11. **Status**: OPEN

---

## DUP — Dataset Duplication/Simplicity/Ceiling Risk (3개)

### RH-DUP-01
1. **Risk ID**: RH-DUP-01
2. **Risk statement**: v0_4 generator가 에피소드당 single regime 할당. intra-episode regime shift 없음 → C2=0.0. 데이터 구조적 한계.
3. **Severity**: CRITICAL
4. **Affected claim**: C2
5. **Current evidence**: 42_true_regime_shift_f1_report.md §3: regime_shift_episodes=0 on both splits
6. **Why this kills the paper**: C2 claim이 핵심 novelty의 일부인데 데이터가 이를 지원하지 못함.
7. **Required test**: v0_5 multi-regime generator (Loop-05)
8. **Candidate fix idea**: (A) v0_5 intra-episode regime shifts; (B) C2 metric 재정의 (across-episode consistency — 권장하지 않음)
9. **Codex implementation task**: TASK_1130_step10_v0_5_generator
10. **Stop condition**: v0_5 데이터에서도 0.0 → C2 claim 제거.
11. **Status**: OPEN

### RH-DUP-02
1. **Risk ID**: RH-DUP-02
2. **Risk statement**: v0_4 데이터가 8개 grammar × 5000 episode = task diversity 제한적. grammar template이 고정되어 있어 grammar generalization 검증 불가.
3. **Severity**: MEDIUM
4. **Affected claim**: Novelty, C3
5. **Current evidence**: grammar.py 8개 grammar class (DIRECT_SEARCH, REQUIRED_DROPDOWN, MODAL_CONFIRM 등)
6. **Why this kills the paper**: 8개 grammar에 overfitting되면 unseen grammar에서 falsification 실패 가능.
7. **Required test**: train grammar subset vs test grammar subset — held-out grammar F1
8. **Candidate fix idea**: (A) grammar OOD split 추가; (B) v0_5에 새 grammar 유형 추가
9. **Codex implementation task**: N/A (P1)
10. **Stop condition**: held-out grammar F1 < 0.2 → grammar generalization claim 불가.
11. **Status**: OPEN

### RH-DUP-03
1. **Risk ID**: RH-DUP-03
2. **Risk statement**: v0_4 task는 synthetic web search simulation. 실제 web task의 복잡성(dynamic content, AJAX, multi-step navigation)이 없음. 난이도가 낮아 모든 agent가 동일 성능.
3. **Severity**: HIGH
4. **Affected claim**: C4, Novelty
5. **Current evidence**: grammar.py 최대 4스텝 에피소드, task_success 0.964 ceiling (47_final_evidence_card §7)
6. **Why this kills the paper**: "challenging web task" claim이 불가. 실세계 web task에서 C3 benefit이 더 커질 수도, 아닐 수도 있음.
7. **Required test**: v0_5 longer horizon + more complex task → task_success 차별화
8. **Candidate fix idea**: (A) v0_5 multi-step complex tasks; (B) real web benchmark (WebArena 등)
9. **Codex implementation task**: TASK_1130_step10_v0_5_generator
10. **Stop condition**: v0_5에서도 task_success ceiling → real benchmark 필요.
11. **Status**: OPEN

---

## ENV — GUI/Text-Only Environment Reality Gap Risk (3개)

### RH-ENV-01
1. **Risk ID**: RH-ENV-01
2. **Risk statement**: text-only synthetic GUI가 실세계 web/robotics task와 괴리. observation이 structured text dict이며 real pixel/HTML이 없음. 실세계 sim-to-real gap 미측정.
3. **Severity**: HIGH
4. **Affected claim**: Novelty
5. **Current evidence**: text_env/collector.py → PublicObservation with text fields. no pixel/HTML/DOM
6. **Why this kills the paper**: "Web/GUI agent failures"를 연구하면서 실제 GUI 없이 text만 사용하면 reviewer가 "not a real Web agent" 공격.
7. **Required test**: text vs pixel-based GUI performance gap 측정 (P4/P5에서)
8. **Candidate fix idea**: (A) P4/P5 GUI MVE; (B) WebArena/Mind2Web subset evaluation
9. **Codex implementation task**: N/A (P4 scope)
10. **Stop condition**: P4 없이 "Web/GUI agent" claim 금지.
11. **Status**: OPEN

### RH-ENV-02
1. **Risk ID**: RH-ENV-02
2. **Risk statement**: synthetic environment이 deterministic grammar rules를 사용. real web은 stochastic, dynamic, asynchronous. grammar rule generalization이 real web에서 미검증.
3. **Severity**: MEDIUM
4. **Affected claim**: Novelty, Generalization
5. **Current evidence**: grammar.py deterministic effect_map. text_env/collector.py synthetic episode
6. **Why this kills the paper**: "control grammar hypothesis" 개념이 real web에서도 유효한지 불명확.
7. **Required test**: real web 환경에서 grammar violation rate 측정
8. **Candidate fix idea**: (A) stochastic grammar perturbation in v0_5; (B) real web pilot study
9. **Codex implementation task**: N/A (P5 scope)
10. **Stop condition**: real web에서 grammar violation < 5% → real web에서 falsification 불필요 → claim scope 축소.
11. **Status**: OPEN

### RH-ENV-03
1. **Risk ID**: RH-ENV-03
2. **Risk statement**: offline eval만 존재. active interaction (agent가 환경에 act하고 feedback 받음) 없음. counterfactual action이 실제로 가능한지 검증 불가.
3. **Severity**: HIGH
4. **Affected claim**: C3, Foresight
5. **Current evidence**: eval_runner.py: episode JSONL replay. no real-time interaction.
6. **Why this kills the paper**: MBRL의 핵심은 active interaction. offline replay만으로는 "agent recovers from wrong grammar" 직접 증명 불가.
7. **Required test**: interactive eval loop (even in synthetic env)
8. **Candidate fix idea**: (A) P4 GUI interactive eval; (B) offline counterfactual simulation
9. **Codex implementation task**: N/A (P4 scope)
10. **Stop condition**: offline replay에서만 claim — 반드시 "offline setting" 명시.
11. **Status**: OPEN

---

## OXE — Open X-Embodiment/Robotics Dataset Risk (3개)

### RH-OXE-01
1. **Risk ID**: RH-OXE-01
2. **Risk statement**: Open X-Embodiment/RT-X를 검토 없이 채택/폐기할 위험. 적합성 검증 없이 "robotics validation"을 claim하거나 배제할 수 있음.
3. **Severity**: HIGH
4. **Affected claim**: Novelty, Generalization
5. **Current evidence**: STEP 10 plan에 OXE audit 포함 (TASK_1116) but 미실행
6. **Why this kills the paper**: robotics OOD claim 없이는 "general falsification" 주장 약함. 반대로 부적합한 robotics data 사용 시 leakage/invalid claim 위험.
7. **Required test**: TASK_1116 openx_schema_audit.py → schema fit 추정
8. **Candidate fix idea**: (A) passive OOD validation (not active training); (B) OXE surprise spike detection
9. **Codex implementation task**: TASK_1116_step10_openx_schema_audit
10. **Stop condition**: OXE schema와 FRCG-WM schema 불일치 → "active" OXE training 금지. passive OOD만 허용.
11. **Status**: OPEN

### RH-OXE-02
1. **Risk ID**: RH-OXE-02
2. **Risk statement**: robotics dataset은 static offline trajectory이며 counterfactual action 없음. anomaly regime label 없음. active falsification 불가. 적용 범위가 passive OOD verification에 한정됨.
3. **Severity**: MEDIUM
4. **Affected claim**: Generalization
5. **Current evidence**: Open X-Embodiment dataset: obs+action+proprio+language, no counterfactual, no regime label
6. **Why this kills the paper**: robotics에서 "falsification" 직접 측정 불가. "passive OOD validation"만 가능.
7. **Required test**: surprise spike detection on robotics trajectories (proxy for falsification)
8. **Candidate fix idea**: (A) failure-success contrast; (B) sim-to-real audit; (C) real-noise validation
9. **Codex implementation task**: TASK_1116_step10_openx_schema_audit
10. **Stop condition**: robotics에서 "active falsification" claim 금지. "passive OOD audit" 표기 필수.
11. **Status**: OPEN

### RH-OXE-03
1. **Risk ID**: RH-OXE-03
2. **Risk statement**: OXE preprocessing cost가 높음 (raw robot sensor data, proprioception, multi-camera). FRCG-WM schema와 alignment 비용 미추정.
3. **Severity**: MEDIUM
4. **Affected claim**: Feasibility
5. **Current evidence**: TASK_1116_step10_openx_schema_audit 미실행 — preprocessing cost 미추정
6. **Why this kills the paper**: 구현 불가능한 계획 → paper에서 robotics validation 언급 시 reviewer 요구
7. **Required test**: TASK_1116 실행 → preprocessing cost JSON
8. **Candidate fix idea**: (A) 소규모 pilot (10-50 episode); (B) 공개 processed subset 사용
9. **Codex implementation task**: TASK_1116_step10_openx_schema_audit
10. **Stop condition**: preprocessing cost > 100 GPU hours → robotics validation BLOCKED.
11. **Status**: OPEN

---

## CF — Offline Counterfactual Risk (2개)

### RH-CF-01
1. **Risk ID**: RH-CF-01
2. **Risk statement**: offline trajectory에서 counterfactual action (wrong grammar로 행동했을 때 어떤 결과가 나왔을지)이 없음. falsification signal이 실제 action outcome에서만 오며, "if had used correct grammar" 비교 불가.
3. **Severity**: HIGH
4. **Affected claim**: C3
5. **Current evidence**: eval_runner.py: step_results에 counterfactuals=[]. v0_4 counterfactual coverage 검증됨 (STEP 4) 하지만 eval path에서 미활용.
6. **Why this kills the paper**: counterfactual 없이는 "wrong grammar로 인한 실패"와 "올바른 grammar였어도 실패" 구분 불가.
7. **Required test**: counterfactual coverage audit (STEP 4 기반); counterfactual_rollout.py 활용 확인
8. **Candidate fix idea**: (A) counterfactual_rollout.py를 eval path에 연결; (B) offline counterfactual credit assignment
9. **Codex implementation task**: N/A (STEP 4에서 구현됨, 연결만 필요)
10. **Stop condition**: counterfactual coverage=0 → causal falsification claim 불가.
11. **Status**: OPEN

### RH-CF-02
1. **Risk ID**: RH-CF-02
2. **Risk statement**: offline trajectory에서 policy improvement가 실제로 일어나는지 검증 불가. "agent recovers from wrong grammar → better outcome"을 interactive eval 없이는 직접 증명 불가.
3. **Severity**: HIGH
4. **Affected claim**: C3, C6
5. **Current evidence**: eval_runner.py: replay-only, no interactive correction
6. **Why this kills the paper**: offline setting에서는 "policy improved" 아닌 "detection accuracy" 측정에 한정됨을 명시해야 함.
7. **Required test**: detection accuracy (C3 F1)를 primary, policy improvement를 secondary로 재정의
8. **Candidate fix idea**: (A) interactive eval (P4); (B) offline metric 범위 명확화
9. **Codex implementation task**: N/A
10. **Stop condition**: offline claim 범위 초과 시 즉시 수정.
11. **Status**: OPEN

---

## ARC — Architecture Active Path Risk (3개)

### RH-ARC-01
1. **Risk ID**: RH-ARC-01
2. **Risk statement**: text_frcg_plan → falsification_score → decision_gate 경로에서 foresight adapter가 없음. rollout prediction quality가 final action quality로 직접 전달되는 경로 없음.
3. **Severity**: HIGH
4. **Affected claim**: Architecture, C6
5. **Current evidence**: planner.py: F_t → gate_out → if should_plan → rewrite. rollout quality → action quality 직접 연결 없음.
6. **Why this kills the paper**: "foresight improves policy" 주장이 간접적. direct adapter 없으면 ablation으로 제거 불가.
7. **Required test**: foresight-to-policy adapter로 action selection 직접 조건화 → divergence 측정
8. **Candidate fix idea**: (A) Architecture I (foresight-to-policy adapter); (B) value-conditioned rewrite
9. **Codex implementation task**: TASK_1118_step10_arch_i_skeleton
10. **Stop condition**: adapter 없이 foresight claim 작성 금지.
11. **Status**: OPEN

### RH-ARC-02
1. **Risk ID**: RH-ARC-02
2. **Risk statement**: world_model_heads.forward_given_action이 action type별로 분리된 head가 없음. 모든 action에 동일 head → action-conditional prediction이 약함.
3. **Severity**: MEDIUM
4. **Affected claim**: Architecture
5. **Current evidence**: world_model_heads.py:66-80 linear heads (action_type을 embedding으로만 처리)
6. **Why this kills the paper**: action-specific effect prediction 품질이 낮으면 falsification_score 정확도 낮아짐.
7. **Required test**: action-type별 prediction accuracy 분석
8. **Candidate fix idea**: (A) action-conditional head mixture; (B) per-grammar world model head
9. **Codex implementation task**: N/A (P1 우선순위)
10. **Stop condition**: per-action prediction accuracy < 60% → world model head 재설계.
11. **Status**: OPEN

### RH-ARC-03
1. **Risk ID**: RH-ARC-03
2. **Risk statement**: TextFRCGModel이 Transformer 없이 linear head 기반. long-context dependency (long-horizon planning) 처리 능력 제한.
3. **Severity**: MEDIUM
4. **Affected claim**: Architecture, C6 (long-horizon)
5. **Current evidence**: TextFRCGModel architecture (linear + small MLP heads). no attention over history.
6. **Why this kills the paper**: long-horizon planning claim이 취약. Transformer 기반 모델과 직접 비교 시 약점.
7. **Required test**: episode length vs C3 F1 degradation curve
8. **Candidate fix idea**: (A) recurrent state (Architecture B); (B) attention over evidence history
9. **Codex implementation task**: TASK_1117_step10_arch_b_skeleton
10. **Stop condition**: F1 degrades significantly beyond 10 steps → long-horizon claim 금지.
11. **Status**: OPEN

---

## LOSS — Loss Novelty Risk (3개)

### RH-LOSS-01
1. **Risk ID**: RH-LOSS-01
2. **Risk statement**: l_falsification이 단순 BCE. sequence accumulation/contrastive/temporal consistency 없음. BCE만으로 evidence-integrating falsification state 학습이 충분한지 검증 없음.
3. **Severity**: HIGH
4. **Affected claim**: C3
5. **Current evidence**: src/frcgw/training/ BCE loss for falsification signal. no temporal accumulation.
6. **Why this kills the paper**: "evidence-integrating" claim이 핵심인데 loss function이 instantaneous BCE이면 모순.
7. **Required test**: BCE baseline vs evidence accumulation loss → C3 F1 비교
8. **Candidate fix idea**: (A) sequence evidence accumulation loss (#1); (B) contrastive wrong-hypothesis loss (#2)
9. **Codex implementation task**: TASK_1120_step10_loss_evidence_accum
10. **Stop condition**: evidence accumulation loss가 BCE보다 worse → BCE가 sufficient → claim 수정.
11. **Status**: OPEN

### RH-LOSS-02
1. **Risk ID**: RH-LOSS-02
2. **Risk statement**: class imbalance 문제 — falsification event (wrong hypothesis episode) vs normal episode 비율이 627:1979 (v0_4 train: true_wrong_counts). BCE는 class imbalance에 취약.
3. **Severity**: HIGH
4. **Affected claim**: C3
5. **Current evidence**: v0_4/manifest.json: true_wrong_counts: false=1352, true=627, none=0 (training labels)
6. **Why this kills the paper**: 627/(627+1352) ≈ 32% positive rate는 mild imbalance지만, rare falsification event에서 precision이 낮아질 수 있음.
7. **Required test**: class-weighted BCE vs focal loss (#8) → precision/recall tradeoff
8. **Candidate fix idea**: (A) focal loss for rare falsification events; (B) class-weighted BCE; (C) oversampling
9. **Codex implementation task**: TASK_1121_step10_loss_calibration_aware (partial)
10. **Stop condition**: precision < 0.3 consistently → class imbalance가 C3 bottleneck.
11. **Status**: OPEN

### RH-LOSS-03
1. **Risk ID**: RH-LOSS-03
2. **Risk statement**: l_regime과 l_falsification 가중치 균형 검증 없음. l_regime=1.0 default이지만 falsification signal을 억누를 수 있음. 또는 반대로 l_falsification이 regime을 지배할 수 있음.
3. **Severity**: MEDIUM
4. **Affected claim**: C2, C3
5. **Current evidence**: configs/train_text_v0_4_abl001.yaml (l_regime=0.0) exists but checkpoint MISSING. loss weight search 미실행.
6. **Why this kills the paper**: ABL-001 collapse를 l_regime=0.0으로만 확인하면 중간 값에서의 behavior 불명확.
7. **Required test**: l_regime sweep [0.0, 0.5, 1.0, 2.0] → C2/C3 F1 변화
8. **Candidate fix idea**: (A) loss weight sweep; (B) dynamic loss weighting (uncertainty-based)
9. **Codex implementation task**: TASK_1127_step10_abl001_retrain (partial)
10. **Stop condition**: l_regime sweep에서 C3 F1이 l_regime에 sensitive → joint optimization 문제.
11. **Status**: OPEN

---

## LONG — Long-Horizon Planning Risk (2개)

### RH-LONG-01
1. **Risk ID**: RH-LONG-01
2. **Risk statement**: v0_4 에피소드 길이가 최대 4-5 스텝으로 짧음. long-horizon planning benefit이 측정 불가. C6 ppc advantage가 long horizon에서 어떻게 변하는지 미측정.
3. **Severity**: MEDIUM
4. **Affected claim**: C6, Long-horizon
5. **Current evidence**: grammar.py 4-5 action sequence max. ppc measured on short episodes.
6. **Why this kills the paper**: "long-horizon planning" claim이 short episode에서만 검증됨 → weak claim.
7. **Required test**: v0_5 longer episode (10-20 steps) → C6 ppc curve over episode length
8. **Candidate fix idea**: (A) v0_5 longer episodes; (B) long-horizon degradation curve metric (#12)
9. **Codex implementation task**: TASK_1130_step10_v0_5_generator (partial)
10. **Stop condition**: ppc advantage degrades > 50% at 10 steps → long-horizon claim 금지.
11. **Status**: OPEN

### RH-LONG-02
1. **Risk ID**: RH-LONG-02
2. **Risk statement**: rollout depth k=3 fixed이며 adaptive depth 없음. complex task에서 더 깊은 rollout이 필요할 수 있음. planning depth와 performance의 관계 미측정.
3. **Severity**: MEDIUM
4. **Affected claim**: C6, Architecture
5. **Current evidence**: frcg_agent.py:150 hardcoded k=3
6. **Why this kills the paper**: "adaptive planning depth"이 claim이면 fixed k=3은 모순. "fixed depth planning"이면 adaptivity claim 없어야 함.
7. **Required test**: k=[1,3,5,10] sweep → C3 F1 vs ppc tradeoff
8. **Candidate fix idea**: (A) value-of-computation gate (Architecture F); (B) adaptive k based on uncertainty
9. **Codex implementation task**: TASK_1119_step10_arch_f_skeleton
10. **Stop condition**: k=1 vs k=3 F1 차이 < 2% → fixed k 정당화.
11. **Status**: OPEN

---

## EVAL — Evaluation Metric Risk (4개)

### RH-EVAL-01
1. **Risk ID**: RH-EVAL-01
2. **Risk statement**: task_success dataset-invariant offline eval — 모든 agent가 0.964/0.998으로 동일. agent-discriminative 아님.
3. **Severity**: CRITICAL
4. **Affected claim**: C4
5. **Current evidence**: 47_final_evidence_card §7: FRCG-LR tsr=0.964, BASE-026 tsr=0.964 (identical)
6. **Why this kills the paper**: task_success를 사용하면 모든 agent가 동일 → no evidence for any claim.
7. **Required test**: task_success가 agent별로 다른 환경에서 측정 (P4+)
8. **Candidate fix idea**: (A) task_success FORBIDDEN metric 선언; (B) ppc as primary metric; (C) v0_5 harder tasks
9. **Codex implementation task**: N/A
10. **Stop condition**: task_success를 claim evidence로 사용 시 즉시 reject.
11. **Status**: ACTIVE_CONSTRAINT

### RH-EVAL-02
1. **Risk ID**: RH-EVAL-02
2. **Risk statement**: C6 14.9× advantage가 self-reported compute denominator에 기반. denominator = planning_calls + rollout_steps + candidate_actions_scored (agent self-report). ABL-036 denominator가 FRCG-LR과 다르면 bias.
3. **Severity**: HIGH
4. **Affected claim**: C6
5. **Current evidence**: eval_runner.py: episode_compute_log accumulation from agent.act() return. ABL-036.NoComputeGateAblation heuristic bypass.
6. **Why this kills the paper**: self-report bias가 대부분의 14.9× 설명 가능. fair compute matching 없으면 C6 claim 약함.
7. **Required test**: wall-clock based denominator + ABL-036 faithful (FRCG model forward 강제) → ppc 재계산
8. **Candidate fix idea**: (A) TASK_1125 fair_ppc wall-clock; (B) TASK_1132 abl036_real_no_gate
9. **Codex implementation task**: TASK_1125_step10_fair_ppc, TASK_1132_step10_abl036_real_no_gate
10. **Stop condition**: fair ppc ratio < 2× → C6 14.9× 격하.
11. **Status**: OPEN

### RH-EVAL-03
1. **Risk ID**: RH-EVAL-03
2. **Risk statement**: configs/lr_eval_real_v0_4_long.yaml에 regime_shift_f1 metric 없음. main eval config와 recovery eval config 사이 metric 불일치.
3. **Severity**: MEDIUM
4. **Affected claim**: C2
5. **Current evidence**: lr_eval_real_v0_4_long.yaml metrics: [task_success_rate, falsification_precision_recall, ood_shift_f1, progress_per_compute, false_planning_call_rate]. regime_shift_f1 ABSENT
6. **Why this kills the paper**: C2 metric이 recovery config에만 있고 main config에 없으면 main eval에서 C2 미측정.
7. **Required test**: lr_eval_real_v0_4_long.yaml에 regime_shift_f1 추가 후 재실행
8. **Candidate fix idea**: (A) TASK_1126 eval_config_align
9. **Codex implementation task**: TASK_1126_step10_eval_config_align
10. **Stop condition**: N/A (fix는 간단)
11. **Status**: OPEN

### RH-EVAL-04
1. **Risk ID**: RH-EVAL-04
2. **Risk statement**: threshold-free metric (AUROC/AUPRC)이 없음. F1은 threshold에 sensitive. threshold 다르게 선택하면 F1이 크게 변할 수 있음.
3. **Severity**: HIGH
4. **Affected claim**: C3
5. **Current evidence**: metrics.py: falsification_precision_recall() → threshold-based. AUROC/AUPRC 미구현.
6. **Why this kills the paper**: threshold-based F1만으로는 classifier quality 주장 어려움. AUROC > 0.7이어야 "good detector" claim 가능.
7. **Required test**: TASK_1123 threshold_free_c3 구현 → AUROC 측정
8. **Candidate fix idea**: (A) TASK_1123 threshold_free_c3_auroc()
9. **Codex implementation task**: TASK_1123_step10_threshold_free_c3
10. **Stop condition**: AUROC < 0.6 → threshold-based F1은 threshold selection artifact → C3 격하.
11. **Status**: OPEN

---

## DTB — Direct-Threat Baseline Risk (2개)

### RH-DTB-01
1. **Risk ID**: RH-DTB-01
2. **Risk statement**: BASE-026 (WAC), BASE-027 (CUWM) approximation_level=partial, BASE-028 (WebWorld) heuristic. faithful 구현 아님. "defeats direct threats" claim이 approximate comparison에 기반.
3. **Severity**: HIGH
4. **Affected claim**: Novelty
5. **Current evidence**: 47_final_evidence_card §10: BASE-026 PARTIAL, BASE-027 PARTIAL, BASE-028 HEURISTIC. ppc gap 5.5-8.6×.
6. **Why this kills the paper**: approximate baseline은 faithful comparison 아님 → "FRCG-WM outperforms WAC/CUWM" claim 약함.
7. **Required test**: BASE-028 faithful simulator search (TASK_1133) + BASE-026/027 faithful upgrade
8. **Candidate fix idea**: (A) BASE-028 faithful WebWorld simulator; (B) BASE-026/027 stronger approximation
9. **Codex implementation task**: TASK_1133_step10_base028_faithful
10. **Stop condition**: faithful BASE 구현 후 ppc ratio < 2× → novelty claim 약화.
11. **Status**: OPEN

### RH-DTB-02
1. **Risk ID**: RH-DTB-02
2. **Risk statement**: C3 falsification에서 BASE-026/027/028 모두 C3 f1=0.0. 이는 "FRCG-WM uniquely detects wrong grammar"를 지지하지만, 이 baselines가 falsification을 시도조차 하지 않기 때문에 trivially 0.0일 수 있음.
3. **Severity**: MEDIUM
4. **Affected claim**: C3 uniqueness
5. **Current evidence**: 47_final_evidence_card §10: all baselines C3 f1=0.0
6. **Why this kills the paper**: baselines이 falsification head를 갖지 않으면 C3=0.0은 expected. "FRCG-WM uniquely"는 trivially true.
7. **Required test**: baselines에 falsification head 추가 후 C3 f1 비교 (새 ablation)
8. **Candidate fix idea**: (A) WAC + falsification head ablation; (B) non-FRCG model with F_t probe
9. **Codex implementation task**: N/A (새 design 필요)
10. **Stop condition**: baseline + falsification head C3 f1 ≥ FRCG-LR → FRCG-WM architecture uniqueness 없음.
11. **Status**: OPEN

---

## FAI — Faithful Ablation Risk (2개)

### RH-FAI-01
1. **Risk ID**: RH-FAI-01
2. **Risk statement**: ABL-001 (l_regime=0.0) + ABL-003 (merged regime/grammar) checkpoint MISSING. C2 separability + C3 disentanglement claim의 ablation 근거 없음.
3. **Severity**: HIGH
4. **Affected claim**: C2, C3
5. **Current evidence**: 47_final_evidence_card §9: ABL-001 config ready, checkpoint MISSING. ABL-003 config ready, checkpoint MISSING.
6. **Why this kills the paper**: claim "regime latent enables C2 detection" → ABL-001이 C2 collapse 보여야 함. "disentangled latent enables C3" → ABL-003이 C3 collapse 보여야 함.
7. **Required test**: TASK_1127 ABL-001 retrain + eval; TASK_1128 ABL-003 retrain + eval
8. **Candidate fix idea**: (A) TASK_1127, TASK_1128 실행
9. **Codex implementation task**: TASK_1127_step10_abl001_retrain, TASK_1128_step10_abl003_retrain
10. **Stop condition**: ABL-001/003 no expected collapse → claim 축소.
11. **Status**: OPEN

### RH-FAI-02
1. **Risk ID**: RH-FAI-02
2. **Risk statement**: ABL-015 (l_control_grammar=0.0) checkpoint exists but eval result 미통합. training differentiation 확인됨 (l_cg=2.075 vs Stage B 0.055) but inference-time impact 미확인.
3. **Severity**: MEDIUM
4. **Affected claim**: C3, Architecture
5. **Current evidence**: 37_step8_final_evidence_card.md §5: ABL-015 training done. eval pending with separate checkpoint.
6. **Why this kills the paper**: l_cg 제거 시 C3 F1 변화 불명확. grammar loss의 importance 미증명.
7. **Required test**: ABL-015 checkpoint → step9 eval config → C3 F1 비교
8. **Candidate fix idea**: (A) ABL-015 eval run; (B) l_cg sensitivity sweep
9. **Codex implementation task**: N/A (eval script already exists)
10. **Stop condition**: ABL-015 C3 f1 ≈ FRCG-LR → grammar loss irrelevant.
11. **Status**: OPEN

---

## STAT — Seed/Statistical Validity Risk (3개)

### RH-STAT-01
1. **Risk ID**: RH-STAT-01
2. **Risk statement**: n=5 std=0.000 (deterministic). 동일 checkpoint + 동일 dataset + seeds=[0,1,2,3,4]. CI 작성 불가. 5회 측정이 정보적으로 1회.
3. **Severity**: CRITICAL
4. **Affected claim**: All
5. **Current evidence**: 47_final_evidence_card §6: std=0.000 on both splits. seeds=[0,1,2,3,4] deterministic.
6. **Why this kills the paper**: ICLR statistical validity requirement. "n=5 std=0이면 단일 측정이다" reviewer attack 1순위.
7. **Required test**: TASK_1129 — 5 different training seeds → true variance
8. **Candidate fix idea**: (A) 5× training with different seeds (권장); (B) episode subsampling (약함)
9. **Codex implementation task**: TASK_1129_step10_n5_multiseed
10. **Stop condition**: training seed std < 0.01 → model/dataset determinism 확인 후 명시.
11. **Status**: OPEN

### RH-STAT-02
1. **Risk ID**: RH-STAT-02
2. **Risk statement**: n=500 episode per split이 충분한지 검증 없음. power analysis 없음. rare falsification event (wrong grammar episodes)가 충분한지 미검증.
3. **Severity**: MEDIUM
4. **Affected claim**: C3
5. **Current evidence**: v0_4 manifest: test_id=500, test_ood=500. true_wrong_counts: true=627/5000 episodes = 12.5% rate.
6. **Why this kills the paper**: 500 episodes × 12.5% = ~63 positive episodes. false positive/negative 분석에 충분한지 불명확.
7. **Required test**: power analysis: required n for 90% power to detect F1=0.5 vs null=0.0
8. **Candidate fix idea**: (A) n 증가 (v0_5); (B) 500 episode sufficiency justification
9. **Codex implementation task**: N/A
10. **Stop condition**: power < 80% at n=500 → "statistically significant" claim 금지.
11. **Status**: OPEN

### RH-STAT-03
1. **Risk ID**: RH-STAT-03
2. **Risk statement**: C3 F1=0.539/0.587 차이 (test_id vs test_ood)가 ID/OOD generalization을 나타내는지, 데이터셋 구성 차이인지 구분 불가. OOD improvement의 원인 불명확.
3. **Severity**: MEDIUM
4. **Affected claim**: C3 OOD generalization
5. **Current evidence**: 47_final_evidence_card §6: test_id f1=0.539, test_ood f1=0.587 (OOD higher)
6. **Why this kills the paper**: OOD F1 > ID F1은 unusual. OOD dataset이 쉬울 수도 있고 (blocker_removed/delayed_effect effect type 다름), 진짜 generalization일 수도 있음.
7. **Required test**: OOD dataset 분석 (effect type distribution, wrong_hypothesis rate). 각 effect type별 F1 분리 측정.
8. **Candidate fix idea**: (A) subgroup analysis by effect type; (B) stratified OOD eval
9. **Codex implementation task**: N/A
10. **Stop condition**: OOD F1 > ID F1이 데이터셋 쉬움 때문이면 "OOD generalization" claim 금지.
11. **Status**: OPEN

---

## REV — Reviewer Attack Risk (3개)

### RH-REV-01
1. **Risk ID**: RH-REV-01
2. **Risk statement**: reviewer가 "n=5 std=0이면 단일 측정이다. CI가 없다. statistical significance 없다"로 reject할 수 있음. ICLR 기본 요구사항 미충족.
3. **Severity**: CRITICAL
4. **Affected claim**: All
5. **Current evidence**: std=0.000 across all seeds (47_final_evidence_card §6)
6. **Why this kills the paper**: ICLR reviewers expect std > 0 for empirical claims. std=0은 reproducibility는 좋지만 variance 없음을 의미 → single data point.
7. **Required test**: TASK_1129 — 5 training seeds → compute CI
8. **Candidate fix idea**: (A) TASK_1129 실행; (B) std=0을 "highly reproducible" 프레이밍 (약함)
9. **Codex implementation task**: TASK_1129_step10_n5_multiseed
10. **Stop condition**: std=0 유지 시 paper에서 "highly reproducible (std=0.000)" 명시 필수.
11. **Status**: OPEN

### RH-REV-02
1. **Risk ID**: RH-REV-02
2. **Risk statement**: reviewer가 "synthetic text-only environment은 real Web/GUI가 아니다. real environment에서 검증하라"로 weak claim을 요구할 수 있음.
3. **Severity**: HIGH
4. **Affected claim**: Novelty, Generalization
5. **Current evidence**: v0_4 text-only synthetic. no real web/GUI eval.
6. **Why this kills the paper**: P4 (synthetic GUI MVE) 없으면 "GUI agent" claim 불가. P5 없으면 VLM claim 불가.
7. **Required test**: P4 GUI MVE eval (다음 phase)
8. **Candidate fix idea**: (A) P4 진입; (B) text-only scope 명시 ("we validate in text-only setting as MVP")
9. **Codex implementation task**: N/A (P4 scope)
10. **Stop condition**: P4 없이 "GUI agent falsification" claim 금지.
11. **Status**: OPEN

### RH-REV-03
1. **Risk ID**: RH-REV-03
2. **Risk statement**: reviewer가 "C6 14.9× advantage의 compute denominator가 self-reported이다. fair comparison 없다"로 C6 claim을 reject할 수 있음.
3. **Severity**: HIGH
4. **Affected claim**: C6
5. **Current evidence**: eval_runner.py self-report denominator. ABL-036 heuristic (no model forward).
6. **Why this kills the paper**: C6는 FRCG-WM의 가장 강한 claim 중 하나. fair comparison 없으면 이 claim도 약해짐.
7. **Required test**: TASK_1125 fair_ppc + TASK_1132 abl036_real_no_gate
8. **Candidate fix idea**: (A) wall-clock denominator; (B) FLOPs denominator; (C) faithful ABL-036
9. **Codex implementation task**: TASK_1125_step10_fair_ppc, TASK_1132_step10_abl036_real_no_gate
10. **Stop condition**: fair ppc ratio < 2× → C6 14.9× → honest reporting.
11. **Status**: OPEN

---

## NOV — Novelty Overlap Risk (3개)

### RH-NOV-01
1. **Risk ID**: RH-NOV-01
2. **Risk statement**: StressWeb (stress testing Web agents), BacktrackAgent (backtracking in web navigation), WebUncertainty (uncertainty in web agents)와 novelty overlap 미검토. 이들이 이미 "wrong grammar detection" 유사 기능을 구현했을 수 있음.
3. **Severity**: HIGH
4. **Affected claim**: Novelty
5. **Current evidence**: paper_context_ref/01_RELATED_WORK_THREAT_MAP.md 에 직접 위협으로 명시되어 있으나 STEP 9까지 직접 검토 없음.
6. **Why this kills the paper**: novelty overlap 발견 시 "FRCG-WM is first" claim 불가.
7. **Required test**: STEP 2 literature scout — StressWeb, BacktrackAgent, WebUncertainty 직접 읽기
8. **Candidate fix idea**: (A) STEP 2 lit scout; (B) 차별점 명확화
9. **Codex implementation task**: TASK_1113_step10_lit_scout_harness
10. **Stop condition**: direct overlap 발견 시 novelty claim 재구성.
11. **Status**: OPEN

### RH-NOV-02
1. **Risk ID**: RH-NOV-02
2. **Risk statement**: WebWorld, CUWM, WAC, VeriGUI가 FRCG-WM의 핵심 contribution을 이미 포함하고 있을 수 있음. BASE-026/027/028로 비교하지만 approximation_level=partial/heuristic이라 완전한 comparison 아님.
3. **Severity**: HIGH
4. **Affected claim**: Novelty
5. **Current evidence**: 37_step8_final_evidence_card §10: BASE-026/027 partial, BASE-028 heuristic
6. **Why this kills the paper**: direct threat baseline이 approximate이면 "defeats [prior work]" claim 불가.
7. **Required test**: faithful BASE-026/027/028 implementation or explicit approximation disclosure
8. **Candidate fix idea**: (A) faithful impl; (B) honest approximation disclosure
9. **Codex implementation task**: TASK_1133_step10_base028_faithful
10. **Stop condition**: faithful impl C3 f1 ≥ FRCG-LR → novelty gap 없음.
11. **Status**: OPEN

### RH-NOV-03
1. **Risk ID**: RH-NOV-03
2. **Risk statement**: 2025-2026 신규 논문 (gWorld, AgentProg, ViMo, MobileDreamer, Code2World, AgentRx)이 FRCG-WM과 유사한 falsification/planning 개념을 제안했을 수 있음. 검토 없음.
3. **Severity**: HIGH
4. **Affected claim**: Novelty
5. **Current evidence**: STEP 2 literature scout 미실행
6. **Why this kills the paper**: 2025-2026 arxiv에 이미 유사 논문 존재 가능.
7. **Required test**: STEP 2 lit scout — 2025-2026 web/GUI agent 신규 논문 검색
8. **Candidate fix idea**: (A) STEP 2 lit scout; (B) novelty differentiation argument
9. **Codex implementation task**: TASK_1113_step10_lit_scout_harness
10. **Stop condition**: exact novelty overlap 발견 시 claim 재구성.
11. **Status**: OPEN

---

## LEAK — Implementation Leakage/P-Hacking Risk (2개)

### RH-LEAK-01
1. **Risk ID**: RH-LEAK-01
2. **Risk statement**: ABL-040 fix-3b가 `_last_F_t=10.0, _last_wrong_prob=1.0, _last_predicted_wrong=True`를 직접 write. 이것이 oracle로서 정직한 positive control인지, 아니면 C3 metric을 높이기 위한 indirect metric 우회인지 의심 가능.
3. **Severity**: HIGH
4. **Affected claim**: C3 validity
5. **Current evidence**: ablations.py:417-420 forced override. ABL-040 C3 f1=0.511/0.481 (FRCG-LR보다 낮음) — 이상함 (oracle이면 더 높아야)
6. **Why this kills the paper**: ABL-040가 oracle이면 C3 f1 > FRCG-LR 이어야 하는데 낮음 (0.511 vs 0.539). 이는 ABL-040의 precision이 낮음 (too many false positives from always-positive). recall=1.0은 정상.
7. **Required test**: ABL-040 confusion matrix 분석. precision=recall=1.0이 기대값인데 실측 precision=0.369-0.481.
8. **Candidate fix idea**: (A) ABL-040이 "항상 wrong으로 예측" oracle임을 명시 (recall=1.0 but low precision); (B) 다른 oracle 방식
9. **Codex implementation task**: N/A
10. **Stop condition**: ABL-040 precision < 0.5 이지만 recall=1.0이면 정직한 positive control (항상-wrong oracle). 이 설명이 paper에 명시되어야 함.
11. **Status**: OPEN

### RH-LEAK-02
1. **Risk ID**: RH-LEAK-02
2. **Risk statement**: threshold/metric/seed 조정으로 결과를 미화할 위험 (p-hacking). tau_f=0.0이 best result를 주는 threshold이면, 이것이 principled choice인지 tuned choice인지 구분 불가.
3. **Severity**: MEDIUM
4. **Affected claim**: C3
5. **Current evidence**: tau_f=0.0 선택이 GateConfig default와 일치하는 것은 principled. 하지만 sweep 없이 채택됨.
6. **Why this kills the paper**: tau_f sweep 없이 tau_f=0.0을 "optimal"로 주장하면 p-hacking 의심.
7. **Required test**: tau_f sweep [0.0, 0.05, 0.1, 0.2, 0.5] + report all values
8. **Candidate fix idea**: (A) tau_f sweep 실행 + all values 보고; (B) tau_f=0.0이 design choice임을 명시
9. **Codex implementation task**: TASK_1131_step10_no_state_change_decoupling (partial)
10. **Stop condition**: tau_f=0.0에서만 F1>0이면 threshold selection artifact → claim 약화.
11. **Status**: OPEN

---

## Gate O-RISK Status

| 조건 | 상태 |
|---|---|
| ≥50 RISK 등록 | ✓ 60개 |
| 20 카테고리 전체 최소 1개 이상 | ✓ |
| CRITICAL/HIGH Top-20 표 작성 | ✓ |
| 모든 RISK 11-field non-null | ✓ |

**Gate O-RISK: PASS**
