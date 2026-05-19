# Learned Falsification Detector Redesign — Master Plan

**작성일**: 2026-05-19  
**작성자**: Main Claude (STEP 10 Risk-Hunt Synthesis)  
**상태**: DRAFT — 사용자 verdict confirm 대기  
**입력 근거**:
- `docs/orchestration/risk_hunt/loop_reports/09_loop_01_proxy_off_eval.md` (Loop-01)
- `docs/orchestration/risk_hunt/loop_reports/09_loop_03_faithful_ablation.md` (Loop-03)
- `docs/orchestration/risk_hunt/loop_reports/09_loop_06_fair_compute_matching.md` (Loop-06)
- `docs/orchestration/risk_hunt/11_final_risk_hunt_execution_report.md`
- `docs/orchestration/risk_hunt/00_current_state_truth_table.md`
- `docs/orchestration/lr_alignment/42_true_regime_shift_f1_report.md`
- MCP sweep log: `docs/orchestration/mcp_research/_call_log/semantic_scholar_2026-05-19.tsv`

---

> **읽는 법**: 이 문서 하나만 읽어도 14개 핵심 질문에 답할 수 있도록 설계됨.  
> 코드 편집 지시 없음. git 명령 없음. Codex task 직접 생성 없음. settings 변경 없음.  
> §12의 Codex task spec은 **사용자 confirm 후 별도 생성** 대기 상태임.

---

## §1. 왜 현재 falsification이 실패했는가

**핵심 진술**: "learned head 없음 + proxy ON 시에만 동작 + fair compute에서 effect size 7.5× 붕괴 + gate가 0회 열림"

### 1.1 proxy artifact 실증

`docs/orchestration/risk_hunt/loop_reports/09_loop_01_proxy_off_eval.md:55-67`에서 확인된 사실:

| Metric | proxy-ON | proxy-OFF |
|---|---|---|
| C3 F1 | 0.5806 | **0.000** |
| C3 Precision | 0.4932 | 0.000 |
| Steps with F_t > τ_f | 146/284 | **0/284** |
| Max planner F_t | 2.774 | **0.000** |

proxy를 끄면 학습된 신호는 단 한 step도 임계 위로 올라오지 않는다. Loop-01 verdict: **REJECT**.

### 1.2 proxy 구조 — 코드 위치

`src/frcgw/planning/planner.py:120-134` — `_effect_key == "no_state_change"` 조건이면 `_obs_effect_type_id = 3` (failed type)으로 강제 치환:

```python
# planner.py:125-126
if use_no_state_change_proxy:
    _obs_effect_type_id = 3 if _effect_key == "no_state_change" else _effect_type_id(effect_text)
```

이 치환 이전에 `src/frcgw/planning/falsification.py:66-67`의 short-circuit이 작동하기 때문에,
proxy가 없으면 type=0 (no_state_change 원래 값)에서 F_t=0을 반환한다:

```python
# falsification.py:66-67
if evidence.observed_effect_type in {0, 6}:
    return torch.zeros((), dtype=shared_h.dtype, device=shared_h.device)
```

v0_4 데이터에서 65%+ 스텝이 `no_state_change`이므로, proxy 없이는 falsification.py가 대부분 0을 반환한다.

### 1.3 fair compute에서의 advantage 붕괴

`docs/orchestration/risk_hunt/loop_reports/09_loop_06_fair_compute_matching.md:77-86`:

| Agent | C6 PPC | ratio vs FRCG-LR |
|---|---|---|
| FRCG-LR | 0.1926 | 1.00× |
| ABL-036b (RealNoGate) | 0.0963 | **2.00×** |
| ABL-036 (heuristic-bypass) | 0.0130 | **14.81×** |

14.9× 어드밴티지는 ABL-036 heuristic-bypass의 분모 inflation artifact였다.
fair compute(ABL-036b)에서는 ~2.0×로 7.4× 줄어든다.

### 1.4 Gate가 단 한 번도 열리지 않은 이유

`docs/orchestration/risk_hunt/loop_reports/09_loop_06_fair_compute_matching.md:78`: FRCG-LR `planning_calls_total = 0` (50 episodes, 284 steps). 즉 C3 F1=0.58은 gate가 한 번도 열리지 않은 상태에서 proxy label matching으로만 발생했다.

### 1.5 C2 separability 붕괴

`docs/orchestration/risk_hunt/loop_reports/09_loop_03_faithful_ablation.md:68-72`:

| Variant | C2 regime_split |
|---|---|
| FRCG-LR reference | **0.0** |
| ABL-001 no-regime | **0.0** |
| ABL-003 merged | **0.0** |

reference에서도 C2=0이므로 ablation으로 contrast를 만들 수 없다. 근본 원인:
`src/frcgw/text_env/generator.py:266` — `hidden_regime=family` 고정으로 에피소드당 단일 regime만 생성.
`docs/orchestration/lr_alignment/42_true_regime_shift_f1_report.md:44-46`: test_id 200 episodes 중 regime_shift_episodes=0.

---

> **Statistical Detection Team challenge**: proxy artifact와 data-design artifact가 혼재하는 상황에서 C3의 null-hypothesis를 정확히 정의하지 않으면, 새 detector의 baseline도 동일한 artifact에 오염될 위험이 있다. §2에서 null 명시 필수.

---

## §2. Falsification의 새 정의 — Sequential Evidence Accumulator

### 2.1 기존 정의의 실패 지점

현재 `falsification.py:49-85`의 `falsification_score()`는:
- 단일 step의 effect logit, progress, failed 신호를 즉각 비교
- 누적 증거 없음, 과거 예측 오차 없음, 행동-결과 불일치 이력 없음
- per-step likelihood ratio → 통계적으로 false alarm rate 통제 불가

### 2.2 새 정의

**Learned Falsification Detector (LFD)**: 현재 world hypothesis가 환경과 더 이상 맞지 않음을 통계적으로 감지하는 sequential learnable module.

**입력** (step t에서):
1. `predicted_effect_residual_t` = predicted effect logit − observed effect type (embedding 공간)
2. `progress_delta_t` = 예측 progress − 관측 progress delta
3. `failure_mismatch_t` = failed_score 예측 vs 실제 failed 발생
4. `action_outcome_mismatch_t` = 실행 action type 하에서 expected effect vs observed effect
5. `persistent_hidden_state h_t` = 전 step의 누적 belief state (GRU hidden)

**출력**:
- `falsified_t ∈ {0, 1}` — 현재 step에서 false signal 발생 여부
- `run_length_posterior P(R_t | data_0:t)` — BOCPD run-length 분포
- `cumulative_log_ratio S_t` — CUSUM/SPRT statistic for monitoring

### 2.3 6개 직관

1. **누적성**: 단일 step의 이상이 아니라 여러 step에 걸친 패턴이 threshold를 넘어야 alarm.
2. **노이즈 분리**: 우연한 1회 실패 vs. 지속적 misalignment 구분 (run-length posterior 활용).
3. **예측오차 통합**: effect 오차만이 아니라 progress + failure + action-outcome 오차를 weighted sum으로 통합.
4. **행동결과 불일치**: 같은 action이 다른 effect를 냈을 때만 falsifying (action-conditional prediction).
5. **persistent belief**: h_t가 episode 전체에 걸쳐 carry-over되어야 장기 drift를 감지 가능.
6. **통계적 false alarm rate 통제**: CUSUM/SPRT의 ARL(Average Run Length) 개념으로 임의 threshold 대신 통계 이론 기반 alarm.

### 2.4 기존 F_t와의 관계

기존 `F_t = max(ell_alts) - ell_exec` (`falsification.py:49-85`)는 단일 step likelihood ratio이며 LFD의 입력 성분 중 하나가 된다. 폐기하지 않고 `action_outcome_mismatch_t`의 구성요소로 통합.

---

> **Policy-Foresight Team challenge**: LFD가 출력하는 `falsified_t`가 planning gate 결정(§8)에 전달될 때, rollout이 falsification 이후에만 실행되는지, 아니면 동시에 실행되는지 명확히 해야 한다. §8에서 순서 명시.

---

## §3. 모델 입력/출력 specification

### 3.1 현재 HistoryEncoder의 stateless 문제

`src/frcgw/models/encoders.py:107`:
```python
self.gru = nn.GRU(input_size=64, hidden_size=hidden_dim, num_layers=1, batch_first=True)
```

`src/frcgw/models/encoders.py:142-145`:
```python
gru_out, _ = self.gru(step_features)  # h0=None → zero-initialized every call
for row, length in enumerate(lengths):
    if length > 0:
        out[row] = gru_out[row, length - 1]
```

`h0=None`으로 호출 → GRU가 에피소드/배치마다 zero-initialized. 이전 step의 evidence가 상위 모듈로 전달되지 않는다. 각 forward call이 독립 — sequential detector에서 필수적인 evidence accumulation이 구조적으로 불가능.

### 3.2 신규 Detector 입력 contract

| 입력 이름 | 타입 | 출처 | forbidden 여부 |
|---|---|---|---|
| `predicted_effect_logits` | Tensor[B, n_effect_types] | model forward (world_model_heads) | NO — model output |
| `observed_effect_type_id` | int (0-6) | public_obs.history[-1].effect_summary | NO — public field |
| `predicted_progress` | Tensor[B] | progress_pred (world_model_heads) | NO — model output |
| `observed_progress_delta` | float | public_obs에서 derived | NO — public field |
| `predicted_failed_score` | Tensor[B] | failed_score (world_model_heads) | NO — model output |
| `observed_failed_action` | bool | effect_summary에서 derived | NO — public field |
| `h_t_prev` | Tensor[hidden_dim] | carry-over from previous step | NO — internal state |

**절대 포함 금지** (visibility.py FORBIDDEN_AGENT_FIELDS에 의해 강제):
`true_regime`, `true_control_grammar`, `true_wrong_hypothesis`, `oracle_*`, `audit_metadata`

→ `src/frcgw/schemas/visibility.py`의 FORBIDDEN_AGENT_FIELDS는 **절대 변경 금지**. Detector output 노출 방식은 EvaluationLabels 확장 + forbidden mirror sync 패턴(§8.4 참조)을 통해서만.

### 3.3 신규 Detector 출력 contract

| 출력 이름 | 타입 | 용도 |
|---|---|---|
| `falsified_t` | bool | planner gate 입력 |
| `run_length_posterior` | Tensor[max_rl] | BOCPD run-length 분포, evaluation-only |
| `cusum_stat_t` | float | CUSUM/SPRT S_t, evaluation-only |
| `h_t_next` | Tensor[hidden_dim] | 다음 step carry-over |
| `wrong_prob_learned` | float (0-1) | P(current hypothesis wrong) — planner에 전달, proxy 대체 |

### 3.4 gradient flow 다이어그램 (텍스트)

```
observed_effect → [effect_residual] ─────┐
predicted_effect → [effect_residual] ────┘
                                         → [MismatchEncoder] → [BOCPD head] → run_length_posterior
predicted_progress → [prog_residual] ────┘        ↑                                    |
observed_progress → [prog_residual] ─────┘       h_t                          L_run_length_posterior
                                                  ↑                                    |
                                         [GRU carry-over] ←─────── h_t-1              |
                                                  ↑                                    ↓
                                         [seq_false_label] ──→ L_seq_falsification ←──┘
```

gradient flow target: MismatchEncoder weights + GRU weights + BOCPD head weights.  
detached inputs: `observed_effect_type_id` (integer, no gradient).  
weight schedule: L_seq_falsification weight 처음 5 epoch은 0.0 → ramp up (BOCPD head가 안정화된 후).

---

> **World Model Architecture Team challenge**: MismatchEncoder가 effect residual + progress residual + failure residual을 어떻게 통합하는지(concatenate vs. weighted attention vs. gating)에 따라 gradient vanishing 위험이 다르다. §9에서 각 loss별 detach 여부 명시 필수.

---

## §4. 통계 차용 — Top-5 선행 연구 + MCP sweep 보강

### 4.1 Adams & MacKay (2007) — BOCPD

**논문**: "Bayesian Online Changepoint Detection" (Adams & MacKay, 2007)  
**contribution**: run-length R_t의 posterior 분포를 sequential Bayesian update로 유지.  
**FRCG-WM 차용**: `FalsificationDetectorHead`의 run-length 출력 head. BOCPD prior로 regime switch 기대 빈도 설정.  
**차용하지 않는 것**: Gaussian predictive distribution 가정 — FRCG-WM은 categorical effect + continuous progress의 혼합 분포.  
**적용 위치**: `TASK_LFD_003` FalsificationDetectorHead.

*MCP sweep 보강*[^bocpd-rl]: Alami et al. (2023) "Restarted Bayesian Online Change-Point Detection for Non-Stationary MDPs"는 R-BOCPD를 MDP transition kernel 변화 감지에 적용하고 regret bound를 제공한다. FRCG-WM의 regime switch를 MDP mode shift로 해석하면 이론적 보장을 빌려올 수 있다.

### 4.2 Page (1954) CUSUM + Wald (1945) SPRT

**논문**: Page (1954) "Continuous Inspection Schemes"; Wald (1945) "Sequential Tests of Statistical Hypotheses"  
**contribution**: CUSUM: S_t = max(0, S_{t-1} + log p(x_t|H1) - log p(x_t|H0)); SPRT: stop at first time S_t > B or < A.  
**FRCG-WM 차용**: Mandatory baseline (TASK_LFD_001). `cusum_stat_t` 출력 필드. theory-backed ARL.  
**차용하지 않는 것**: exact likelihood 계산 — model 예측을 approximate likelihood로 사용.  
**적용 위치**: 후보 B 구현.

*MCP sweep 보강*[^cusum-rl]: Li et al. (2022) "Testing stationarity and change point detection in reinforcement learning" (CUSUM-RL, arXiv:2203.01707, 14 citations)은 offline RL 데이터에서 Q-function 비정상성을 CUSUM으로 탐지한다. FRCG-WM의 offline evaluation 설정과 구조적으로 유사하다. 2026 "Asymptotically optimal sequential change detection" (Ashwin Ram & Aaditya Ramdas)은 CUSUM의 sharp minimax lower bound를 확립하여 이론적 최적성 레퍼런스 역할.

### 4.3 Becker-Ehmck et al. (2019) — SLDS-VBF

**논문**: "Switching Linear Dynamical Systems for Noise Robust Speech" + 일반화: Switching Latent Dynamics with Variational Bayes Filtering  
**contribution**: 잠재 동역학이 이산 mode 간을 전환하는 구조를 VB inference로 학습.  
**FRCG-WM 차용**: z_regime_logits의 temporal prior 설계. regime이 에피소드 중에 전환 가능하다는 generative model 구조.  
**차용하지 않는 것**: 음성 도메인 특화 Gaussian emission — 텍스트/GUI action-effect에는 부적합.  
**적용 위치**: v0_5 generator의 intra-episode switch prior 설계 참조.

### 4.4 LeCun (2022) JEPA + Assran et al. (2023) I-JEPA

**논문**: LeCun (2022) "A Path Towards Autonomous Machine Intelligence"; Assran et al. (2023) "Self-Supervised Learning from Images with a Joint-Embedding Predictive Architecture" (NeurIPS 2023)  
**contribution**: 예측을 pixel space가 아닌 latent space에서 수행 → 노이즈 필터링 + representation 학습.  
**FRCG-WM 차용**: MismatchEncoder가 effect residual을 pixel-level이 아닌 latent 공간에서 측정하는 설계 철학.  
**차용하지 않는 것**: image self-supervised pretraining — FRCG-WM은 action-effect text 도메인.  
**적용 위치**: TASK_LFD_003 BOCPD head의 latent residual 입력 설계.

*MCP sweep 보강*[^jepa-control]: ACT-JEPA (Vujinović & Kovacevic, 2025) — IL과 SSL을 통합하여 latent observation 시퀀스 예측을 action 예측과 jointly 학습. FRCG-WM의 world_model_heads + FalsificationDetectorHead 결합과 유사한 목표를 공유하나, ACT-JEPA는 falsification/regime-switch 개념이 없음. JEPA-state-space (Ulmen et al., 2025) — neural ODE + JEPA로 구조화된 latent state-space를 학습하는 것은 FRCG-WM의 persistent h_t 설계에 직접 참조 가능.

### 4.5 Ebihara et al. (2020) — SPRT-TANDEM (DNN-SPRT)

**논문**: "Deep Neural Networks for the Sequential Probability Ratio Test on Non-i.i.d. Data Series" (arXiv:2006.05587)  
**contribution**: DNN으로 non-i.i.d. 시퀀스에서 SPRT log-likelihood ratio를 추정하는 Loss for Log-Likelihood Ratio estimation (LLLR).  
**FRCG-WM 차용**: `TASK_LFD_001` CUSUM/SPRT baseline 구현 시 정확히 이 접근을 참조. DNN이 F_t approximation을 학습하는 대신 LLR을 직접 학습.  
**차용하지 않는 것**: video domain 학습 — 텍스트/GUI adaptation 필요.  
**적용 위치**: 후보 B 구현.

*MCP sweep 보강*[^sprt-multi]: Novikov (2024) "A class of sequential multi-hypothesis tests" — 2개 이상 가설에 대한 SPRT 확장 이론. FRCG-WM의 k개 alternative hypothesis 시나리오에 이론적 지지를 제공.

---

> **Evaluation-Reviewer Attack Team challenge**: §4.5의 SPRT-TANDEM이 이미 DNN으로 non-i.i.d. SPRT를 구현했다면, FRCG-WM의 contribution이 무엇인지 명확히 해야 한다. 차이점: FRCG-WM은 control-grammar hypothesis mismatch라는 구조화된 problem에 specific하며, effect type + progress + action-outcome의 multi-dimensional residual을 통합하는 것이 novelty. SPRT-TANDEM은 단순 분류 문제임.

---

## §5. GUI 환경에서 Sequential Detector의 부적절성

### 5.1 VeriGUI / VeriSafe 직접 위협 확인

MCP sweep 결과[^verisafe]: VeriSafe Agent (Lee et al., 2025, arXiv:2503.18492, 17 citations) — 모바일 GUI agent에 logic-based action verification을 적용, 94.33–98.33% 정확도 달성. 이는 step-local verification(단일 step 검증)이며 sequential evidence accumulation이 아님. 따라서 FRCG-WM의 sequential falsification과는 보완적 관계.

MobileDreamer (Cao et al., 2026, arXiv:2601.04035) — **NEW DIRECT THREAT**: Generative Sketch World Model for GUI agents, Android World SOTA 달성 (+5.25% task success). GUI agent에 world model을 결합하는 접근이 이미 2026년에 발표됨. FRCG-WM의 GUI 환경 적용이 novelty를 유지하려면 sequential falsification + wrong-control-grammar detection이라는 specific contribution을 강조해야 함.

### 5.2 GUI episode의 구조적 문제

sequential detector를 GUI 환경에 적용하기 어려운 이유:

| 문제 | 상세 | 영향 |
|---|---|---|
| Episode 길이 | GUI episode 평균 5-15 step (WebArena/Android World 기준) | run-length accumulation에 불충분 — BOCPD posterior가 수렴 전에 episode 종료 |
| Discrete UI elements | click/type/scroll 3-5종류 → sparse action space | Simpson trap (§6.3) 또는 action inversion이 발생할 이벤트 다양성 부족 |
| Screenshot diff residual | screenshot pixel change = layout change + content change + rendering artifact | noisy observation → false positive alarm 높음 |
| Reward sparsity | 대부분 step에서 중간 progress reward 없음 | L_progress gradient 희박 → evidence accumulation signal 약함 |

### 5.3 GUI collector 부재

`src/frcgw/gui_env/` 디렉터리에 `collector.py`가 **존재하지 않음**. GUI 환경은 현재 단계에서 sequential detector 실험 불가 — text env로 먼저 검증 필수.

### 5.4 결론: GUI는 Phase 후속, 텍스트 환경 우선

sequential detector는 **text env (v0_5)에서 먼저 검증 후** GUI 환경으로 확장. GUI collector 작성은 TASK_LFD_008 이후 별도 phase. VeriGUI(P-009) §3에서 sequential evidence accumulator 부재 확인은 본 redesign이 해결하려는 gap과 일치.

---

> **Dataset-Environment Team challenge**: text env v0_5에서 학습한 sequential detector가 GUI env에 어떤 조건에서 transfer되는지에 대한 사전 분석이 없다. §6에서 v0_5 spec이 GUI transfer를 고려해야 한다 — action type vocabulary 설계를 GUI와 compatible하게.

---

## §6. v0_5 Multi-Regime Dataset 필요성

### 6.1 v0_4의 한계

`src/frcgw/text_env/generator.py:253-270`:
```python
def _generate_spec(self, family: str, rng: random.Random) -> TextEpisodeSpec:
    ...
    return TextEpisodeSpec(
        ...
        hidden_regime=family,            # regime == family in P2 — 단일 고정
        hidden_control_grammar=template.grammar,
        event_schedule=list(template.event_schedules),
        ...
    )
```

에피소드 시작 시 regime이 결정되고 그 이후 변경 없음. 이로 인해:
- `42_true_regime_shift_f1_report.md:44-46`: test_id 200 episodes 중 regime_shift_episodes=0
- `09_loop_03_faithful_ablation.md:70-72`: reference C2=0.0 — ablation contrast 불가

### 6.2 v0_4 보존 정책

**사용자 결정**: v0_4는 **backward-compatible baseline reproduction**을 위해 그대로 유지.
v0_5는 active falsification primary dataset으로 병행 운영. `data/frcgw_text/v0_4/`는 write-protected 운영.

### 6.3 v0_5 필수 요소 7개

**요소 1: Intra-episode regime switch** (`generator.py:253` event_schedule 확장)
- 에피소드 도중 t_switch에서 hidden_regime이 family_A → family_B로 전환
- switch 발생 확률 p_switch ∈ {0.2, 0.5, 0.8} (train/val/test 분포 다르게)
- evaluation label `regime_switch_t` (전환 timestep) — inference 불가 필드

**요소 2: Same action / different effect by regime** (effect_map regime-conditional)
- grammar.py의 effect_map이 현재 fixed (`_FAMILY_GRAMMAR`). v0_5에서 같은 action type이 regime A에서는 `state_change`, regime B에서는 `no_state_change` 반환하도록 regime-conditional effect_map 추가
- 이것이 있어야 "같은 행동 → 다른 결과"라는 falsifying evidence가 생성됨

**요소 3: Cumulative noise drift** (`state.py`의 `_hidden_noise_level` 추가)
- episode 진행에 따라 점진적으로 effect type randomness가 증가
- t > t_noise_start이면 effect_type이 correct type ± 1 noise로 반환될 확률 ε(t) 증가
- evaluation label `noise_drift_max`, `t_noise_start`

**요소 4: Long-horizon trap** (max_steps 30+, prereq chain 5+)
- 현재 v0_4 max_steps=12. v0_5에서 30+ step 허용
- prerequisite action chain 5개 이상 요구하여 장기 evidence accumulation 테스트

**요소 5: Action-outcome inversion (Simpson trap)**
- 에피소드 전반부: action_A → effect_B (정상 grammar)
- 에피소드 후반부: regime switch 후 action_A → effect_C (다른 grammar)
- 단순 correlation을 따른 agent가 틀리도록 설계

**요소 6: Evaluation-only labels** (inference 입력 불가)
`src/frcgw/schemas/step_schema.py`의 EvaluationLabels 확장 제안 (§8.4 참조):
- `regime_switch_t: int | None` — 전환 timestep
- `noise_drift_max: float | None` — noise level 최대치
- `inversion_t: int | None` — action inversion 시작 timestep
- `detection_delay_gt: int | None` — ground-truth detection delay (oracle)

**요소 7: GUI collector 신규 작성** (별도 phase)
- v0_5 text env 검증 완료 후 GUI env로 확장
- `src/frcgw/gui_env/collector.py` 신규 (현재 부재 확인됨)

### 6.4 v0_5 scope 제한 (Risk Note §3 반영)

v0_5 spec 전체 구현은 TASK_LFD_004 (§12)에서 **minimal prototype scope**로 한정:
- 요소 1 (intra-episode switch) + 요소 2 (regime-conditional effect_map) 먼저
- 요소 3-6은 v0_5 alpha 이후 순차 추가

---

> **Dataset-Environment Team challenge**: regime switch 후 agent의 action history에서 switch 이전 evidence와 이후 evidence를 구분하지 않으면, BOCPD run-length posterior가 올바른 R_t를 학습할 수 없다. evaluation label `regime_switch_t`가 loss 계산에 사용되지 않더라도 test-time metric에서 detection delay를 정확히 계산하기 위해 필수.

---

## §7. Robotics Passive OOD Validation 역할 한정

### 7.1 FRCG-WM에 적합하지 않은 이유 3개

**이유 1: counterfactual 부재**
FRCG-WM의 핵심 evaluation은 "같은 action, 다른 grammar 하에서 다른 effect가 발생했을 때 detector가 반응하는가"이다. robotics dataset에는 grammar가 없고 counterfactual trajectory도 없다. FRCG-WM claim의 primary evidence를 robotics에서 얻을 수 없다.

**이유 2: wrong-control-grammar label 부재**
robotics dataset (Open X-Embodiment, DROID, LIBERO, CALVIN)에는 `true_wrong_hypothesis`에 해당하는 label이 없다. sequential detector의 supervised signal이 불가능하다.

**이유 3: failure mode 구분 불가**
"no-effect vs delayed-effect vs noisy-effect"가 robotics trajectory에서 관측만으로 구분되지 않는다. 물리적 제약(마찰, 중력)과 wrong-grammar-persistence를 분리할 방법이 없다.

### 7.2 적합한 용도 (역할 한정)

| 용도 | 데이터셋 | 사용 방식 |
|---|---|---|
| External auxiliary trace | Open X-Embodiment (`src/frcgw/data/` SRC-DATA-007 참조) | pretraining corpus (effect prediction head 사전학습) |
| Passive validation pretraining | DROID, LIBERO | action-effect 예측 능력 pretrain, falsification head는 별도 fine-tune |
| Appendix external validity | CALVIN | "text env에서 학습한 detector가 robotics trajectory에서도 anomaly를 탐지하는가" appendix 실험 |

*MCP sweep 보강*[^whale-oxe]: WHALE-X (Zhang et al., 2024, arXiv:2411.05619) — 414M parameter world model을 970K Open X-Embodiment trajectories에서 학습하여 uncertainty estimation + OOD 일반화. FRCG-WM의 robotics passive eval에서 WHALE-X를 외부 비교점으로 사용 가능. 단 WHALE-X도 wrong-control-grammar label은 없음.

*MCP sweep (topic 11, counterfactual limitation)*[^counterfactual-offline]: offline robotics dataset에서 counterfactual action-effect가 없는 근본적 한계. §7.3의 "main claim evidence로 robotics 금지" 정책의 이론적 근거.

### 7.3 robotics dataset 사용 조건

robotics trajectory를 어떤 형태로든 사용하기 전에:
1. `src/frcgw/schemas/visibility.py`의 FORBIDDEN_AGENT_FIELDS에 robotics-specific fields가 없는지 확인 (변경 금지)
2. robotics observation이 AGENT_OBSERVATION bucket의 정의와 일치하는지 `/frcgw-data-safety` 스킬로 확인
3. 결과는 appendix only — main claim evidence로 사용 금지

---

> **Evaluation-Reviewer Attack Team challenge**: robotics를 "passive OOD validation"으로만 사용할 경우, reviewer는 "text env에서 학습한 detector가 GUI/robotics에 얼마나 generalize하는가"를 core question으로 던질 것이다. 이 질문에 답하지 않으면 contribution이 text-only sandbox에 갇혀 있다는 비판을 피하기 어렵다. §14 claim 재구성에서 scope를 정직하게 한정해야 한다.

---

## §8. 아키텍처 변경 명세

### 8.1 HistoryEncoder — persistent h_t carry-over

*MCP sweep (topic 12, RNN-CPD)*[^rnn-cpd]: 신경과학에서 RNN이 latent context shift에 sequential Bayesian belief update를 구현함을 실험적으로 확인. GRU carry-over 설계의 신경과학적 motivation.

**현재 문제**: `src/frcgw/models/encoders.py:142` `gru_out, _ = self.gru(step_features)` — h0=None (zero 초기화).

**변경 방향** (구현은 TASK_LFD_002):
- evaluation loop에서 h_t를 외부 buffer로 관리하고 next step에 전달
- training: teacher-forcing으로 sequence 전체를 한 번에 process (h0=zeros는 episode 시작에만)
- inference: `TextFRCGModelAgent` 또는 새 `LFDAgent`가 `self._h_t: Tensor | None`을 state로 유지

**변경 범위**:
- `src/frcgw/models/encoders.py` — HistoryEncoder.forward()에 `h0` argument 추가 (optional)
- `src/frcgw/evaluation/frcg_agent.py` — episode-level h_t state 관리
- training loop에서 sequence-level GRU call

### 8.2 FalsificationDetectorHead 신규 (BOCPD run-length head)

**현재**: 없음 — `falsification.py:49-85`의 `falsification_score()` 함수가 deterministic LR 계산.

**신규 모듈** (TASK_LFD_003, `src/frcgw/models/` 아래 신규 파일):
```
FalsificationDetectorHead(
  input: [effect_residual, prog_residual, failure_residual, h_t]
  → cusum_stat_t: float
  → run_length_log_probs: Tensor[max_run_length]
  → wrong_prob_learned: float
  → h_t_next: Tensor
)
```

주의: 기존 `falsification.py`의 `falsification_score()` 함수는 **MODIFY** (§13.1) — 삭제하지 않고 MismatchEncoder의 입력 성분으로 통합.

### 8.3 PlannerState → BeliefState 확장

**현재**: `src/frcgw/planning/planner.py:28-38`의 PlannerState는 `dict[int, int]` (step_idx → hypothesis_id).

**확장 방향** (TASK_LFD_002의 일부):
- PlannerState에 `h_t: Tensor | None` 필드 추가
- episode 시작 시 `h_t = None`, 매 step 이후 `h_t = detector_output.h_t_next`로 갱신
- `BeliefState`로 rename은 §7 Terms Must Be Preserved 규칙에 의해 보류 — 기존 `PlannerState`를 확장

### 8.4 EvaluationLabels 확장 + forbidden mirror sync 패턴

**금지 사항**: `src/frcgw/schemas/visibility.py`의 FORBIDDEN_AGENT_FIELDS **수정 금지**.  
Detector output은 evaluation-only labels로만 노출 — inference input으로 절대 불가.

**확장 방향** (`src/frcgw/schemas/step_schema.py`의 EvaluationLabels, TASK_LFD_006):
```python
# 제안 (실제 수정은 TASK_LFD_006 Codex task가 수행)
class EvaluationLabels:
    ...  # 기존 필드 유지
    # 신규 detection output (inference-forbidden)
    detector_run_length_posterior: list[float] | None = None
    detector_cusum_stat: float | None = None
    detector_wrong_prob_learned: float | None = None
    regime_switch_t: int | None = None       # v0_5 only
    detection_delay_gt: int | None = None    # v0_5 only
```

`visibility.py`의 FORBIDDEN_AGENT_FIELDS에는 `detector_*` 계열 필드가 추가되어야 하나, 이는 **별도 사용자 승인 + frcgw-data-safety 스킬 실행 필수**. TASK_LFD_006 accept 전 T3 agent report PASS 필수 (§12.6).

---

> **Statistical Detection Team challenge**: `wrong_prob_learned`이 BOCPD run-length posterior에서 어떻게 derived되는지 정의되어야 한다. P(falsified | run_length > threshold)로 계산한다면 threshold는 어디서 결정되는가? 학습 중에 threshold를 학습해야 하는가, 아니면 post-hoc calibration인가?

---

## §9. Loss 변경 명세

### 9.1 신규 L_seq_falsification (cumulative BCE)

**목적**: sequential step에 걸쳐 누적된 mismatch가 `true_wrong_hypothesis` label을 예측하도록 학습.

**정의**:
```
L_seq_falsification = Σ_t BCE(wrong_prob_learned_t, true_wrong_hypothesis_t)
    weighted by: I(t ≥ t_switch - 2)  ← regime switch 직전 2 step 포함
```

**gradient flow**: FalsificationDetectorHead weights + GRU carry-over → HistoryEncoder weights.  
**detached inputs**: `true_wrong_hypothesis_t` (label, no gradient), `observed_effect_type_id` (integer).  
**weight**: 초기 0.0 → 5 epoch 후 0.5 → 10 epoch 후 1.0 (ramp schedule).

### 9.2 신규 L_run_length_posterior (BOCPD KL)

**목적**: run-length posterior가 ground-truth regime switch timing과 align되도록 학습.

**정의** (v0_5 데이터에서만 의미 있음):
```
L_run_length_posterior = KL(predicted_run_length_posterior || target_run_length)
    target_run_length: delta distribution at t - t_switch (episode 내 switch 위치)
```

**gradient flow**: BOCPD head weights.  
**detached**: `regime_switch_t` (v0_5 evaluation label, no gradient).  
**v0_4 호환**: v0_5 switch label이 없는 경우 L_run_length_posterior = 0 (skip).

### 9.3 L_temporal_consistency 실제 구현

*MCP sweep (topic 6, Dreamer WM uncertainty)*[^dreamer-wm]: DreamerV3 RSSM의 KL divergence가 uncertainty signal로 사용되는 방식. L_temporal_consistency와 병렬 설계 참조.

**현재**: `src/frcgw/objectives/losses.py:149-150`:
```python
def L_temporal_consistency(posterior_entropy: Tensor) -> Tensor:
    return _zero(posterior_entropy)  # PLACEHOLDER
```

**구현 방향** (TASK_LFD_005):
- z_regime_logits가 연속된 step 사이에서 크게 변하지 않도록 consistency 강제
- `L_temporal_consistency = MSE(z_regime_t, stop_gradient(z_regime_{t-1}))`
- v0_4에서도 의미 있음 (single-regime episode에서 regime logit이 안정적이어야 함)
- 기존 weight `l_temporal_consistency: 0.1` 유지

### 9.4 L_intent_action_mapping 결정

**현재**: `src/frcgw/objectives/losses.py:131-132`:
```python
def L_intent_action_mapping(rewrite_logits: Tensor | None, targets: list[BatchTargets]) -> Tensor:
    return _zero(rewrite_logits)  # PLACEHOLDER
```

**결정**: v0_5 phase에서 rewrite_action()에 학습 가능한 head를 추가한 뒤 구현. v0_4 phase에서는 placeholder 유지 (변경 없음). weight은 0.0으로 유지하여 gradient에 기여하지 않도록.

### 9.5 Loss weight schedule 요약

| Loss | v0_4 현재 | v0_5 초기 | v0_5 ramp-up | gradient target |
|---|---|---|---|---|
| L_action_effect | 1.0 | 1.0 | 1.0 | effect head |
| L_progress | 0.5 | 0.5 | 0.5 | progress head |
| L_regime | 1.0 | 1.0 | 1.0 | regime logit |
| L_control_grammar | 1.0 | 1.0 | 1.0 | grammar logit |
| L_falsification | 1.0 | → 0.0 | ramp 0→1.0 | falsification head (새 LFD) |
| L_intent_action_mapping | 0.0 | 0.0 | 0.0 | (placeholder) |
| L_change_point | 0.3 | 0.3 | 0.3 | change logit |
| L_reveal_shift | 0.3 | 0.3 | 0.3 | reveal/shift logit |
| L_failed_action | 0.3 | 0.3 | 0.3 | failed head |
| L_temporal_consistency | 0.0 (zero()) | 0.1 | 0.1 | regime logit stability |
| **L_seq_falsification** | (없음) | 0.0 | ramp 0→0.5 | **FalsificationDetectorHead** |
| **L_run_length_posterior** | (없음) | 0.0 | ramp 0→0.5 | **BOCPD head** |

---

> **Loss-Training Team challenge**: `L_seq_falsification`과 기존 `L_falsification`이 동시에 활성화되면 같은 `true_wrong_hypothesis` target에 두 개의 loss가 gradient를 전달한다. gradient conflict 위험이 있음. TASK_LFD_005에서는 `L_falsification` weight를 0으로 설정하고 `L_seq_falsification`으로 교체하는 전략을 명시해야 한다.

---

## §10. Metric 변경 — SSoT 업데이트 제안 (실제 수정은 별도 phase)

> **중요**: `paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md`의 실제 수정은 본 작업 scope 밖이다. 이 섹션은 **제안** 형태만 제공한다. BASE-029+/ABL-043+ 할당은 frcgw-phase-gate를 통한 별도 phase에서만 수행.

### 10.1 신규 제안 metric

| 제안 metric ID | 이름 | 정의 | SSoT 기재 위치 |
|---|---|---|---|
| MET-LFD-001 | sequential_detection_delay | E[t_detected - t_switch | detected] — alarm과 실제 switch 사이 delay | 제안 |
| MET-LFD-002 | false_alarm_rate_per_step | E[falsified_t = 1 | true_wrong_hypothesis_t = 0] | 제안 |
| MET-LFD-003 | run_length_posterior_ECE | Expected Calibration Error of run_length_posterior | 제안 |
| MET-LFD-004 | persistence_time | E[T_stop | H_wrong] — wrong hypothesis 유지 시간 | 제안 |

### 10.2 신규 baseline 카테고리 제안 (SEQUENTIAL-CHANGE-DETECTION)

| 제안 baseline ID | 이름 | 설명 |
|---|---|---|
| BASE-029 (제안) | CUSUM-detector | Page (1954) CUSUM on effect residual |
| BASE-030 (제안) | SPRT-TANDEM | Ebihara et al. (2020) DNN-SPRT |
| BASE-031 (제안) | Kalman-innovation-chi2 | Chi-squared test on innovation sequence |
| BASE-032 (제안) | BOCPD-point | Adams & MacKay (2007) with learned emission |
| BASE-033 (제안) | JEPA-residual-threshold | ACT-JEPA style latent residual + threshold |
| BASE-034 (제안) | Dreamer-KL | RSSM KL divergence as anomaly signal |
| BASE-035 (제안) | Ensemble-disagreement | K ensemble members' effect prediction variance |

### 10.3 C3 claim 재구성 제안

기존 C3 ("falsification F1 > 0.5"): 학습된 signal이 아닌 proxy artifact임이 확인됨.

제안 재구성:
- **C3-a**: "LFD detection delay < threshold" (MET-LFD-001, vs BASE-029/030 baselines)
- **C3-b**: "LFD false alarm rate < threshold" (MET-LFD-002, vs uncertainty-threshold baselines)
- **C3-c**: "LFD run_length_posterior ECE < 0.1" (MET-LFD-003)

---

> **Evaluation-Reviewer Attack Team challenge**: detection delay를 claim으로 사용할 경우, threshold는 task에 따라 달라진다. universal threshold를 주장하면 "task-specific engineering이지 scientific contribution이 아니다"는 비판을 받을 수 있다. calibration-based claim(ECE)이 더 principled할 수 있음.

---

## §11. 5개 구현 후보 설계 (A-E)

*MCP sweep (topic 7, value of computation)*[^value-compute]: adaptive planning "when to plan" 기준. FRCG-WM decision gate의 theoretical grounding.

*MCP sweep (topic 9, robot failure prediction)*[^robot-failure]: robotics trajectory failure prediction의 한계 — supervised label 없이 unsupervised anomaly only.

### 후보 A: Evidence-Accumulating Falsification State (BOCPD + persistent h_t)

**Hypothesis**: persistent GRU hidden state로 sequential mismatch를 누적하면, proxy 없이도 proxy-on 대비 동등하거나 더 높은 falsification F1을 달성한다.

**Test-first plan**:
1. `tests/test_lfd_persistent_state.py` — HistoryEncoder.forward(h0=h_prev) 호출 시 h_t가 carry-over되는지 단위 테스트
2. `tests/test_bocpd_head.py` — FalsificationDetectorHead가 run_length_posterior를 출력하고 합이 1인지 확인
3. `tests/test_seq_falsification_loss.py` — L_seq_falsification gradient가 BOCPD head까지 backprop되는지 확인

**Required changes**:
- Dataset: v0_5 (요소 1+2 최소, 요소 6 evaluation labels 포함)
- Loss: L_seq_falsification + L_run_length_posterior + L_temporal_consistency (실제 구현)
- Architecture: HistoryEncoder carry-over + FalsificationDetectorHead (BOCPD head)

**Expected failure mode**: v0_5 데이터 없이 v0_4에서 학습하면 regime_switch 없음 → L_run_length_posterior 의미 없음 → BOCPD head가 uninformative posterior를 학습. 이 경우 v0_5 data 우선 완료 필요.

**Reject condition**: v0_5 데이터에서도 proxy-off F1 < 0.1 and detection_delay > 5. → 기본 가설 falsified, architecture 재검토 필요.

### 후보 B: Sequential Statistical Detector Baseline (CUSUM/SPRT, mandatory)

**Hypothesis**: CUSUM/SPRT 기반 deterministic baseline이 learned BOCPD head보다 유사하거나 더 나은 detection delay를 보인다면, learned head의 필요성에 의문이 생긴다.

**Test-first plan**:
1. `tests/test_cusum_baseline.py` — CUSUM S_t가 regime switch 이후 B를 초과하는지 확인
2. `tests/test_sprt_tandem.py` — DNN-SPRT LLR 추정 loss가 수렴하는지 확인
3. `tests/test_baseline_vs_lfd.py` — detection delay 비교 (CUSUM vs LFD 후보 A)

**Required changes**:
- Dataset: v0_5 (요소 1+2)
- Loss: LLLR (Ebihara 2020 스타일)
- Architecture: `src/frcgw/evaluation/baselines.py`에 CUSUMDetectorBaseline 신규 클래스

**Expected failure mode**: v0_4의 no_state_change 단일 effect type에서는 CUSUM S_t가 언제나 임계 아래 → effect diversity가 없어서 baseline도 동작 안 함. v0_5 데이터가 먼저 필요.

**Reject condition**: v0_5에서 CUSUM detection_delay ≤ BOCPD detection_delay (5% 마진 이내) → learned BOCPD head가 statistical baseline 대비 유의한 이점 없음 → 후보 A claim 약화.

**[MANDATORY]**: 이 baseline은 후보 A 전에 반드시 구현되어야 한다. 학습된 detector와 통계 baseline을 비교하지 않으면 reviewer가 "deterministic CUSUM으로도 충분하다"는 공격을 막을 수 없다.

### 후보 C: Policy-Foresight Causal Link (rollout ON/OFF action divergence)

**Hypothesis**: planning을 허용할 때와 허용하지 않을 때 action 선택이 diverge하는 비율 (action_changed_by_rollout)이 C6 advantage의 causal mechanism을 설명한다.

**Test-first plan**:
1. `tests/test_foresight_causal.py` — `rollout_off_action`이 act()에서 계산되고 per_step JSONL에 기록되는지 확인
2. `tests/test_action_divergence_rate.py` — divergence_rate metric이 0과 1 사이인지 확인

**Required changes**:
- Dataset: v0_4 sufficient (기존 데이터)
- Loss: 변경 없음
- Architecture: `frcg_agent.py`에 rollout_off_action 분기 추가 (Loop-04 미수행 항목)

**Expected failure mode**: planning_calls_total=0이면 rollout이 한 번도 실행되지 않아 divergence_rate=0. gate를 강제로 열려면 tau_f override가 필요.

**Reject condition**: divergence_rate < 0.05 (5% 미만의 step에서 rollout이 action 변경) → rollout이 action 선택에 실질적 영향 없음 → C6 advantage의 mechanism 설명 불가.

### 후보 D: v0_5 Multi-Regime Dataset (intra-episode switch generator)

**Hypothesis**: intra-episode regime switch가 있는 데이터에서 학습하면, 후보 A (LFD)와 후보 B (CUSUM)의 detection performance가 의미있는 값을 가진다.

**Test-first plan**:
1. `tests/test_v0_5_generator.py` — episode 생성 시 hidden_regime이 episode 중간에 변경되는지 확인
2. `tests/test_v0_5_regime_switch_count.py` — test split에서 regime_switch_episodes > 0인지 확인
3. `tests/test_forbidden_field_mirror_sync.py` — **반드시 GREEN** 유지

**Required changes**:
- Dataset: `src/frcgw/text_env/generator.py` (event_schedule 확장, EpisodeSpecGenerator에 switch 로직)
- Loss: 변경 없음
- Architecture: `src/frcgw/schemas/step_schema.py` EvaluationLabels 확장 (§8.4)

**Expected failure mode**: regime switch timing이 너무 늦으면(max_steps-1) switch 전 evidence가 충분하지 않아 detection 불가. t_switch ≤ 0.7 × max_steps 조건 필요.

**Reject condition**: v0_5에서 학습해도 regime_switch_f1 = 0 (C2=0) — 데이터 생성 자체가 올바르지 않거나 model이 switch signal을 전혀 활용하지 못함. → 근본적 데이터 설계 재검토.

### 후보 E: Robotics Passive OOD Validation (eval-only)

**Hypothesis**: text env (v0_5)에서 학습한 FalsificationDetector가 robotics OOD trajectory에서도 anomaly를 탐지한다 (zero-shot transfer 가능성).

**Test-first plan**:
1. `tests/test_robotics_harness.py` — robotics JSONL을 frcgw schema로 변환하는 adapter가 FORBIDDEN_AGENT_FIELDS를 주입하지 않는지 확인
2. `tests/test_robotics_eval_only.py` — robotics eval이 훈련 데이터를 생성하지 않는지 (eval-only flag) 확인

**Required changes**:
- Dataset: 외부 robotics dataset adapter (Open X-Embodiment subset)
- Loss: 변경 없음 (eval-only, no training on robotics)
- Architecture: eval harness adapter만

**Expected failure mode**: robotics trajectory에 wrong-grammar label이 없어 supervised metric 계산 불가. detection_delay 등 ground-truth 필요 metric은 모두 N/A. unsupervised anomaly score(cusum_stat_t)만 의미 있음.

**Reject condition**: robotics에서 cusum_stat_t distribution이 text env OOD와 유사하지 않음 → transfer 없음, appendix 실험으로만 보고. (Main claim 영향 없음 — 후보 E는 항상 secondary.)

*MCP sweep 보강*[^oxe-eval]: WHALE-X (Zhang et al., 2024) — OXE 970K trajectories에서 학습한 WM은 uncertainty estimation 능력을 보유. FRCG-WM 후보 E는 WHALE-X의 uncertainty output을 CUSUM baseline과 비교하는 실험으로 설계 가능. Interleave-VLA (Fan et al., 2025, 47 citations)는 OXE 기반 210K episode 데이터셋을 공개하여 외부 eval 데이터로 활용 가능.

---

> **Policy-Foresight Team challenge**: 후보 C (foresight causal)가 Loop-04로 미수행 상태임. 후보 A-B-D-E보다 구현 난이도가 낮지만 claim에 critical한 causal mechanism을 제공한다. 실행 우선순위에서 후보 C가 후보 A보다 먼저 실행되어야 하는 근거가 있다. §12에서 ordering 명시.

---

## §12. 8개 Codex Task Spec — Draft Only

> **중요**: 이 section은 spec draft만 제공. **queue 파일 생성은 사용자 confirm 후 별도 요청으로만 진행**.  
> 4중 금지: 코드 직접 편집 지시 없음 / git 명령 없음 / settings 변경 없음 / queue 파일 직접 생성 없음.

### TASK_LFD_001 — CUSUM/SPRT Baseline (후보 B)

```
TASK_NAME: TASK_LFD_001_cusum_sprt_baseline
BACKGROUND: Loop-01 확인 결과 학습된 falsification signal이 부재. SPRT-TANDEM (Ebihara 2020)
  기반 DNN-SPRT를 mandatory baseline으로 먼저 구현해야 learned LFD와 비교 가능.
GOAL: CUSUMDetectorBaseline 클래스 구현 + DNN-SPRT LLR loss 구현.
  v0_5 데이터가 준비되면 detection_delay metric 산출 가능하도록 harness 준비.
FILES_ALLOWED:
  - src/frcgw/evaluation/baselines.py
  - src/frcgw/evaluation/metrics.py
  - tests/test_lfd_cusum_baseline.py
  - tests/test_sprt_tandem.py
FILES_FORBIDDEN:
  - .claude/
  - CLAUDE.md
  - src/frcgw/schemas/visibility.py
  - paper_context_ref/
  - data/
  - outputs/
  - secrets/
  - .env*
  - scripts/run_codex_task.ps1
REQUIRED_IMPLEMENTATION:
  1. CUSUMDetectorBaseline: step_features 입력 → S_t cumulative statistic 출력
  2. SPRTDetector: DNN-SPRT LLR 추정 head (선택적 loss LLLR)
  3. metrics.py에 detection_delay(), false_alarm_rate_per_step() 추가
REQUIRED_TESTS:
  - test_cusum_stat_increases_under_mismatch: mismatch 입력 시 S_t 단조 증가
  - test_cusum_resets_after_alarm: threshold 초과 후 S_t 리셋
  - test_false_alarm_rate_zero_for_stable: stable distribution에서 FAR < 0.05
  - tests/test_forbidden_field_mirror_sync.py: GREEN 유지
ACCEPTANCE_CRITERIA:
  - CUSUMDetectorBaseline.cusum_stat()가 [0, inf) range 출력
  - detection_delay() metric이 v0_4 single-regime에서 "no alarm" 반환
  - test_forbidden_field_mirror_sync 3 tests GREEN
COMMIT_MESSAGE: feat(lfd): CUSUM/SPRT mandatory baseline + detection metrics
STOP_CONDITION: test 4개 PASS + mirror sync GREEN
RELATED_AGENT_REPORT_IDS: [impl_risk_LFD001_R1] (T3 audit 완료 후 채움)
```

### TASK_LFD_002 — HistoryEncoder persistent h_t (후보 A precondition)

```
TASK_NAME: TASK_LFD_002_history_encoder_persistent_ht
BACKGROUND: src/frcgw/models/encoders.py:142의 GRU가 h0=None (zero-initialized)으로 호출됨.
  episode 전체에 걸친 evidence 누적이 구조적으로 불가능한 상태.
GOAL: HistoryEncoder.forward()에 h0 argument 추가. frcg_agent.py에서 episode-level
  h_t state 관리. training batch에서 sequence-level GRU call 지원.
FILES_ALLOWED:
  - src/frcgw/models/encoders.py
  - src/frcgw/evaluation/frcg_agent.py
  - src/frcgw/training/text_trainer.py (h0 sequence pass-through)
  - tests/test_lfd_persistent_state.py
FILES_FORBIDDEN: (공통 금지 목록과 동일 + src/frcgw/schemas/visibility.py)
REQUIRED_IMPLEMENTATION:
  1. HistoryEncoder.forward(history_list, h0=None) — h0 optional argument
  2. TextFRCGModelAgent에 self._h_t: Tensor | None = None 추가, episode 시작 시 reset
  3. act() 호출마다 h_t carry-over, episode 종료 시 reset
REQUIRED_TESTS:
  - test_h_t_carries_over: 2회 act() 호출 시 두 번째 h_t가 첫 번째와 다름
  - test_episode_reset: episode_reset() 후 h_t = None
  - test_training_batch_h0_zeros: 학습 배치에서 h0=zeros 사용됨
  - tests/test_forbidden_field_mirror_sync.py: GREEN
ACCEPTANCE_CRITERIA:
  - 기존 TextFRCGModelAgent 동작 backward-compatible (h0=None 시 기존과 동일)
  - 새 h0 argument로 episode carry-over 동작 확인
COMMIT_MESSAGE: feat(encoder): HistoryEncoder persistent h_t carry-over
STOP_CONDITION: test 4개 PASS
RELATED_AGENT_REPORT_IDS: [impl_risk_LFD002_R1]
```

### TASK_LFD_003 — BOCPD run-length head + L_run_length_posterior (후보 A)

```
TASK_NAME: TASK_LFD_003_bocpd_run_length_head
BACKGROUND: FalsificationDetectorHead가 부재. 결정론적 LR (falsification.py:49-85)만 존재.
  Adams & MacKay (2007) BOCPD 스타일의 run-length posterior head를 신규 구현.
GOAL: FalsificationDetectorHead 신규 모듈 구현. L_run_length_posterior KL loss 구현.
  GRU carry-over(TASK_LFD_002 완료 전제)를 입력으로 받아 wrong_prob_learned 출력.
FILES_ALLOWED:
  - src/frcgw/models/world_model_heads.py (또는 신규 src/frcgw/models/falsification_detector.py)
  - src/frcgw/objectives/losses.py (L_run_length_posterior, L_seq_falsification 추가)
  - tests/test_bocpd_head.py
  - tests/test_seq_falsification_loss.py
FILES_FORBIDDEN: (공통 금지 목록과 동일 + src/frcgw/schemas/visibility.py)
REQUIRED_IMPLEMENTATION:
  1. FalsificationDetectorHead(effect_residual, prog_residual, failure_residual, h_t)
     → (run_length_log_probs, cusum_stat_t, wrong_prob_learned, h_t_next)
  2. L_run_length_posterior: KL(predicted || target) — v0_5에서만 활성화, v0_4에서 0 반환
  3. L_seq_falsification: cumulative BCE over sequence (§9.1)
  4. losses.py의 L_temporal_consistency placeholder 제거 → MSE 구현 (§9.3)
REQUIRED_TESTS:
  - test_bocpd_posterior_sums_to_1: run_length_log_probs가 valid log-distribution
  - test_wrong_prob_in_range: wrong_prob_learned ∈ [0, 1]
  - test_seq_loss_gradient: L_seq_falsification gradient가 BOCPD head weights에 도달
  - tests/test_forbidden_field_mirror_sync.py: GREEN
ACCEPTANCE_CRITERIA:
  - 기존 falsification.py::falsification_score()는 삭제하지 않음 — MismatchEncoder 입력으로 통합
  - L_temporal_consistency가 0 이외의 gradient를 발생시킴
  - proxy-off 조건에서도 wrong_prob_learned가 0 이외 분포를 학습할 잠재력 확인 (unit test 수준)
COMMIT_MESSAGE: feat(lfd): BOCPD run-length head + sequential falsification losses
STOP_CONDITION: test 4개 PASS + mirror sync GREEN
RELATED_AGENT_REPORT_IDS: [impl_risk_LFD003_R1]
```

### TASK_LFD_004 — v0_5 Generator intra-episode regime switch (후보 D)

```
TASK_NAME: TASK_LFD_004_v0_5_intra_episode_switch
BACKGROUND: generator.py:266의 hidden_regime=family로 단일 regime만 생성.
  regime_shift_f1이 v0_4에서 0인 근본 원인. v0_5 prototype (요소 1+2만) 구현.
GOAL: EpisodeSpecGenerator에 intra-episode switch 옵션 추가. effect_map을 regime-conditional로.
  v0_5 데이터셋 생성 + 분포 검증. test split에서 regime_shift_episodes > 0 확인.
FILES_ALLOWED:
  - src/frcgw/text_env/generator.py
  - src/frcgw/text_env/grammar.py (regime-conditional effect_map)
  - src/frcgw/text_env/collector.py (regime_switch_t label emit)
  - src/frcgw/schemas/step_schema.py (EvaluationLabels 확장 — §8.4 방식)
  - tests/test_v0_5_generator.py
FILES_FORBIDDEN: (공통 금지 목록과 동일 + src/frcgw/schemas/visibility.py)
REQUIRED_IMPLEMENTATION:
  1. EpisodeSpecGenerator.generate(switch_prob=0.0) 기본값으로 v0_4 호환
  2. switch_prob > 0이면 episode 중 t_switch에서 hidden_regime 변경
  3. grammar.py effect_map이 (action, regime) tuple을 key로 사용
  4. collector.py에서 EvaluationLabels.regime_switch_t emit (None이면 v0_4)
  5. visibility.py는 절대 수정 금지 — regime_switch_t는 EvaluationLabels 필드만
REQUIRED_TESTS:
  - test_v0_5_generates_switch: switch_prob=1.0으로 생성 시 regime 변경 확인
  - test_v0_4_compat: switch_prob=0.0으로 생성 시 v0_4와 동일
  - test_regime_switch_t_not_in_public_obs: regime_switch_t가 public_observation에 없음
  - tests/test_forbidden_field_mirror_sync.py: GREEN (최우선)
ACCEPTANCE_CRITERIA:
  - v0_5 test split에서 regime_shift_episodes > 0
  - visibility.py 수정 0건
COMMIT_MESSAGE: feat(data-v0_5): intra-episode regime switch generator + evaluation labels
STOP_CONDITION: test 4개 PASS + mirror sync GREEN + visibility.py 미수정 확인
RELATED_AGENT_REPORT_IDS: [impl_risk_LFD004_R1]
```

### TASK_LFD_005 — L_temporal_consistency / L_seq_falsification 실제 구현

```
TASK_NAME: TASK_LFD_005_temporal_consistency_and_seq_loss
BACKGROUND: losses.py:149-150 L_temporal_consistency = _zero() placeholder.
  TASK_LFD_003에서 신규 loss를 추가하지만 temporal consistency 별도 구현 필요.
GOAL: L_temporal_consistency MSE 구현. L_seq_falsification과 기존 L_falsification
  weight 조정 (L_falsification weight=0.0, L_seq_falsification ramp schedule).
FILES_ALLOWED:
  - src/frcgw/objectives/losses.py
  - src/frcgw/training/ (training config schema)
  - tests/test_temporal_consistency_loss.py
FILES_FORBIDDEN: (공통 금지 목록과 동일)
REQUIRED_IMPLEMENTATION:
  1. L_temporal_consistency: MSE(z_regime_t, stop_gradient(z_regime_{t-1}))
  2. DEFAULT_WEIGHTS에서 l_temporal_consistency: 0.1로 실제 적용
  3. l_falsification weight ramp schedule config (epoch-based)
REQUIRED_TESTS:
  - test_temporal_consistency_not_zero: gradient가 0이 아님
  - test_seq_loss_weight_ramp: epoch 5 이전 weight=0, 이후 > 0
  - tests/test_forbidden_field_mirror_sync.py: GREEN
ACCEPTANCE_CRITERIA:
  - L_temporal_consistency가 더 이상 _zero() 반환하지 않음
COMMIT_MESSAGE: feat(loss): temporal consistency + seq_falsification weight schedule
STOP_CONDITION: test 3개 PASS + mirror sync GREEN
RELATED_AGENT_REPORT_IDS: [impl_risk_LFD005_R1]
```

### TASK_LFD_006 — EvaluationLabels detector output 추가 + forbidden mirror sync

```
TASK_NAME: TASK_LFD_006_evaluation_labels_detector_output
BACKGROUND: FalsificationDetectorHead 출력(wrong_prob_learned, cusum_stat_t 등)을
  evaluation metric에서 사용하려면 EvaluationLabels에 필드 추가 필요.
  visibility.py FORBIDDEN_AGENT_FIELDS와 동기화 필수 (사용자 승인 선결 조건).
GOAL: EvaluationLabels에 detector output 필드 추가. FORBIDDEN_AGENT_FIELDS에
  detector_* 계열 추가 (visibility.py 수정은 사용자 명시 승인 후만).
  test_forbidden_field_mirror_sync.py GREEN 유지.
FILES_ALLOWED:
  - src/frcgw/schemas/step_schema.py
  - tests/test_lfd_eval_labels.py
  (visibility.py 수정은 사용자 승인 후 별도 step)
FILES_FORBIDDEN: (공통 금지 목록과 동일 + src/frcgw/schemas/visibility.py [사용자 승인 없이])
REQUIRED_IMPLEMENTATION:
  1. EvaluationLabels에 detector 출력 필드 추가 (§8.4 spec 참조)
  2. collector가 agent의 detector output을 EvaluationLabels에 emit
  3. visibility.py의 FORBIDDEN_AGENT_FIELDS 수정은 별도 승인 단계 — task 내에서 직접 수정 금지
REQUIRED_TESTS:
  - test_detector_fields_not_in_public_obs
  - test_eval_labels_detector_fields_type
  - tests/test_forbidden_field_mirror_sync.py: GREEN (이 task의 핵심)
ACCEPTANCE_CRITERIA:
  - test_forbidden_field_mirror_sync.py GREEN
  - visibility.py 수정 0건 (사용자 승인 없이)
COMMIT_MESSAGE: feat(schema): EvaluationLabels detector output fields
STOP_CONDITION: mirror sync GREEN + visibility.py 미수정 확인
RELATED_AGENT_REPORT_IDS: [impl_risk_LFD006_R1]
```

### TASK_LFD_007 — Sequential detection delay / FAR / ECE eval metric

```
TASK_NAME: TASK_LFD_007_sequential_detection_metrics
BACKGROUND: 현재 metrics.py에는 C3 F1/Precision/Recall (proxy 기반)만 있음.
  LFD 평가를 위해 detection_delay, false_alarm_rate, run_length_posterior_ECE 필요.
GOAL: MET-LFD-001~003 metric 구현. v0_5 evaluation labels (regime_switch_t) 활용.
FILES_ALLOWED:
  - src/frcgw/evaluation/metrics.py
  - tests/test_lfd_metrics.py
FILES_FORBIDDEN: (공통 금지 목록과 동일)
REQUIRED_IMPLEMENTATION:
  1. detection_delay(episodes): E[t_detected - t_switch | detected]
  2. false_alarm_rate_per_step(episodes): FAR per step
  3. run_length_posterior_ece(episodes): ECE of run_length posterior
  4. 기존 C3 metric 함수는 유지 (backward compat)
REQUIRED_TESTS:
  - test_detection_delay_correct: known t_switch에서 delay 계산 정확성
  - test_far_zero_for_stable: 안정 구간에서 FAR = 0
  - test_ece_perfect_calibration: perfect posterior에서 ECE = 0
  - tests/test_forbidden_field_mirror_sync.py: GREEN
ACCEPTANCE_CRITERIA:
  - 3개 신규 metric이 v0_4 (switch없음)에서 gracefully None 반환
  - v0_5 switch label이 있을 때 non-null 계산
COMMIT_MESSAGE: feat(metrics): LFD detection metrics (delay/FAR/ECE)
STOP_CONDITION: test 4개 PASS + mirror sync GREEN
RELATED_AGENT_REPORT_IDS: [impl_risk_LFD007_R1]
```

### TASK_LFD_008 — Robotics OOD passive eval harness (후보 E)

```
TASK_NAME: TASK_LFD_008_robotics_ood_eval_harness
BACKGROUND: 후보 E robotics passive OOD validation. WHALE-X (2024), OXE subset 활용.
  text env에서 학습한 detector가 robotics trajectory에서 anomaly를 탐지하는지 eval-only.
GOAL: robotics JSONL → frcgw schema 변환 adapter. eval-only harness (no training on robotics).
  cusum_stat_t distribution 비교.
FILES_ALLOWED:
  - src/frcgw/data/robotics_adapter.py (신규)
  - scripts/eval_robotics_ood.py (신규)
  - tests/test_robotics_harness.py
FILES_FORBIDDEN: (공통 금지 목록과 동일 + src/frcgw/schemas/visibility.py)
REQUIRED_IMPLEMENTATION:
  1. robotics_adapter.py: OXE JSONL → PublicObservation 변환 (hidden fields 제외)
  2. eval_robotics_ood.py: detector만 실행, training 없음
  3. 출력: cusum_stat_t distribution (histogram JSON)
REQUIRED_TESTS:
  - test_robotics_adapter_no_forbidden_fields: FORBIDDEN_AGENT_FIELDS 미포함
  - test_eval_only_no_training: backward pass 없음 확인
  - tests/test_forbidden_field_mirror_sync.py: GREEN
ACCEPTANCE_CRITERIA:
  - robotics adapter가 visibility.py contract를 준수
  - main claim에 영향 없음 (eval-only, appendix 전용)
COMMIT_MESSAGE: feat(eval): robotics OOD passive eval harness (appendix only)
STOP_CONDITION: test 3개 PASS + mirror sync GREEN
RELATED_AGENT_REPORT_IDS: [impl_risk_LFD008_R1]
```

---

## §13. KEEP / MODIFY / REJECT 조건

### 13.1 Component matrix

| Component | 파일 | 결정 | 근거 |
|---|---|---|---|
| `falsification.py::falsification_score()` | `src/frcgw/planning/falsification.py:49-85` | **MODIFY** | 삭제하지 않고 MismatchEncoder 입력(action_outcome_mismatch_t)으로 통합. deterministic LR은 BOCPD input feature |
| effect head (`world_model_heads.py`) | `src/frcgw/models/world_model_heads.py` | **KEEP + MODIFY** | 기능 유지, gradient를 FalsificationDetectorHead까지 흘려야 함 |
| progress head | `src/frcgw/models/world_model_heads.py` | **KEEP** | 변경 없음, L_progress는 그대로 |
| failure head | `src/frcgw/models/world_model_heads.py` | **KEEP + MODIFY** | gradient to detector 추가 |
| planner gate (`decision_gate.py`) | `src/frcgw/planning/decision_gate.py` | **MODIFY** | proxy 제거, `wrong_prob_learned` 입력으로 전환 |
| **proxy heuristic** (`planner.py:120-134`) | `src/frcgw/planning/planner.py:120-134` | **REJECT** | Loop-01에서 학습 신호가 전혀 없음이 확인. proxy 제거는 새 detector 가동 후 |
| HistoryEncoder GRU | `src/frcgw/models/encoders.py:107,142-145` | **MODIFY** | h0 argument 추가, carry-over 지원 (TASK_LFD_002) |
| PlannerState (dict) | `src/frcgw/planning/planner.py:28-38` | **MODIFY** | h_t 필드 추가 (BeliefState로 rename은 보류) |
| `L_temporal_consistency` (zero) | `src/frcgw/objectives/losses.py:149-150` | **MODIFY** | placeholder 제거, MSE 구현 (TASK_LFD_005) |
| `L_intent_action_mapping` (zero) | `src/frcgw/objectives/losses.py:131-132` | **KEEP** (보류) | v0_5 rewrite head 완료 후 결정 |
| regime label generator (v0_4) | `src/frcgw/text_env/generator.py:253-270` | **KEEP** (v0_4 보존) | backward-compat baseline reproduction용 |
| regime label generator (v0_5) | (신규) | **CREATE** | intra-episode switch (TASK_LFD_004) |
| `visibility.py` FORBIDDEN_AGENT_FIELDS | `src/frcgw/schemas/visibility.py` | **변경 금지** | invariant SSoT — 사용자 명시 승인 없이 수정 절대 금지 |

### 13.2 proxy heuristic REJECT의 조건부 성격

proxy heuristic (`planner.py:120-134`)는 **즉각 삭제하지 않는다**.
- TASK_LFD_003 (BOCPD head) 완료 + 학습 완료 후 `wrong_prob_learned`가 안정적 신호를 내기 시작하면
- Loop-01 재실행: proxy-off + LFD 조건에서 F1 > 0.1 확인
- 그 후에만 proxy 제거

이 순서를 지키지 않으면 LFD 미완성 상태에서 proxy를 제거해 regression이 발생한다.

---

> **Implementation-Risk Team challenge (T3)**: TASK_LFD_002 (persistent h_t)와 TASK_LFD_003 (BOCPD head)는 상호 의존적이다. TASK_LFD_002가 먼저 완료되어야 TASK_LFD_003이 h_t를 입력으로 받을 수 있다. 그러나 TASK_LFD_003이 없으면 TASK_LFD_002의 h_t가 의미 있는 loss gradient를 받지 못한다. → joint training loop 설계 필요. impl_risk T3 audit에서 순서 conflict 확인 필수.

---

## §14. 논문 Claim 재구성 + 최종 Verdict

### 14.1 verdict 후보 5개 검토

| Verdict | 조건 | §1-13 evidence |
|---|---|---|
| LFD_REDESIGN_FEASIBLE | A-E 모두 시행 가능 | **조건 미충족** — v0_4에서 A/B/D가 의미 있는 signal 불가 (§6.1), architecture carry-over 없음 (§3.1) |
| LFD_REQUIRES_ENVIRONMENT_PIVOT | GUI/v0_4 부족, v0_5 또는 robotics 필수 | **부분 충족** — v0_5 필수이나 GUI pivot이 주요 blocker는 아님 (§5.3) |
| LFD_REQUIRES_ARCHITECTURE_PIVOT | recurrent evidence state 변경 too invasive | **부분 충족** — architecture 변경 필요하나 데이터도 동등하게 limiting |
| **LFD_REQUIRES_DATA_AND_ARCH_PIVOT** | 데이터·모델 모두 변경 | **§1+§3+§6 동시 evidence** — 충족 |
| CLAIM_SHRINK_ONLY | heuristic detector paper로 축소 | **과도** — 2.0× fair compute advantage 생존, redesign 여지 있음 |

### 14.2 최종 verdict: **`LFD_REQUIRES_DATA_AND_ARCH_PIVOT`**

**근거 chain (§1, §3, §6 3개 섹션 인용)**:

**[증거 1 — §1]** 학습된 falsification signal 부재:  
`09_loop_01:55-67` → proxy OFF시 F1=0.000, steps_with_F_t_above_tau=0/284.  
deterministic LR (`falsification.py:49-85`)은 learn하지 않는다.  
→ **Architecture pivot 필요**: FalsificationDetectorHead + L_seq_falsification 신규 구현.

**[증거 2 — §3]** 통계적 evidence accumulation 불가:  
`encoders.py:142-145` → GRU h0=0 매 call 재시작.  
`losses.py:149-150` → L_temporal_consistency=_zero().  
두 조건이 동시에 충족되어야 sequential detector가 gradient를 받는다.  
→ **Architecture pivot 필요**: GRU carry-over + loss 실제 구현.

**[증거 3 — §6]** v0_4 데이터에서 regime switch 없음:  
`generator.py:266` → hidden_regime=family 고정.  
`42_true_regime_shift_f1:44-46` → test_id 0건 regime switch.  
sequential detector가 학습할 falsifying evidence sequence가 데이터에 존재하지 않는다.  
→ **Data pivot 필요**: v0_5 intra-episode switch.

세 증거 중 어느 하나만으로는 LFD_REQUIRES_ARCHITECTURE_PIVOT 또는 LFD_REQUIRES_ENVIRONMENT_PIVOT으로 오분류될 수 있다. 세 증거가 동시에 존재하므로 **DATA AND ARCH** pivot이 필요하다.

### 14.3 adversarial review 통과 확인

**(Evaluation-Reviewer Attack Team 관점 적용)**:

Q: "proxy를 제거해도 2.0× advantage가 유지되는가?"  
A: `09_loop_06:78-83` → FRCG-LR planning_calls=0으로 gate가 열리지 않았다. 이 state에서 2.0×는 self-report 분모 artifact가 남아있을 가능성. wall-clock 검증 후 claim 확정.

Q: "MobileDreamer (2026)가 GUI WM으로 SOTA를 달성했는데 novelty가 있는가?"  
A: MobileDreamer는 step-local generative WM이며 sequential falsification / wrong-grammar detection 없음. FRCG-WM의 contribution은 "wrong control-grammar hypothesis persistence"라는 specific failure mode 진단 — 이는 MobileDreamer의 scope 밖. 단 §4에서 MobileDreamer를 direct threat로 기재하고 §5에서 차별점을 명시해야 한다.

Q: "v0_5 데이터에서 학습하지 않은 상태에서 어떻게 LFD_REQUIRES_DATA_AND_ARCH_PIVOT을 verdict로 낼 수 있는가?"  
A: 이 verdict는 *현재 상태*의 diagnosis이지 final paper verdict가 아니다. v0_5 + LFD redesign 후 results가 나오면 verdict가 LFD_REDESIGN_FEASIBLE로 upgrade될 수 있다. 현 verdict는 "무엇을 먼저 해야 하는가"를 결정하는 실행 가이드.

### 14.4 claim 재구성 제안

| 현재 claim | 문제 | 제안 재구성 |
|---|---|---|
| "C3 falsification F1 > 0.5" | proxy artifact | "LFD detection delay < K steps on v0_5 (N=X, threshold K from BOCPD theory)" |
| "C2 regime separability" | v0_4에 switch 없음 | "v0_5에서 regime_switch_f1 > 0 (먼저 데이터 제공 후 claim)" |
| "C6 14.9× advantage" | heuristic-bypass artifact | "fair compute 기준 ~2× advantage (n=50, self-report; wall-clock pending)" |
| "wrong-control-grammar persistence 감지" | 핵심 contribution 유지 | "sequential evidence accumulation으로 wrong-grammar persistence time E[T_stop|H_wrong] 단축 확인" |

---

> **Area-Chair Synthesis (최종)**: 본 master plan이 제시하는 redesign은 논문 claim을 약화시키는 것이 아니라 *정직한 기반 위에서 재건*하는 것이다. C3 proxy artifact를 숨기지 않고 명시한 점(§1), data limitation을 구조적으로 진단한 점(§6), learned detector의 required condition을 statistical theory로 정당화한 점(§4)은 ICLR reviewer 기준에서 "honest negative reporting"으로 긍정 평가될 수 있다. verdict `LFD_REQUIRES_DATA_AND_ARCH_PIVOT`은 현 시점의 correct diagnosis이며, 본 redesign이 완료되면 `LFD_REDESIGN_FEASIBLE`로 upgrade 가능하다.

---

## Wave 5 자가 Audit

### Completeness checklist

- [x] **14개 섹션 존재**: §1-§14 모두 작성
- [x] **5개 후보 A-E 모두**: hypothesis + test-first plan + reject condition 완비
- [x] **8개 Codex task 10-field spec 완비**: TASK_LFD_001-008 각각 10 필드
- [x] **6개 team 관점 각 섹션에 최소 1줄**: Statistical Detection / WM Architecture / Policy-Foresight / Dataset-Environment / Loss-Training / Evaluation-Reviewer Attack
- [x] **verdict 정확히 1개**: `LFD_REQUIRES_DATA_AND_ARCH_PIVOT` §14에서 정식 선택 (나머지 4개는 후보 목록)
- [x] **4중 금지 위반 0건**: 코드 편집 instruction 없음 / git 명령 없음 / settings 변경 없음 / Codex queue 직접 생성 없음
- [x] **visibility.py 변경 instruction 0건**: "변경 금지" 또는 "사용자 승인 선결" 문맥에서만 언급
- [x] **SSoT 업데이트는 "제안"형태만**: §10에서 "제안" 명시, 10_EVAL 직접 수정 instruction 없음
- [x] **MCP sweep footnote 존재**: §4/§5/§11 inline footnote 포함
- [x] **모든 file path absolute 또는 repo-relative 일관적**

### 4중 금지 0건 검증

본 문서는 다음 4가지 금지 원칙을 준수한다:
- 코드 직접 편집 지시: 0건 (모든 구현은 TASK spec으로만 기술)
- git 명령 지시: 0건
- codex_queue 파일 직접 생성 지시: 0건 (사용자 confirm 후 별도 요청)
- settings/hooks 변경 지시: 0건

---

## MCP Sweep 각주

[^bocpd-rl]: Alami, R., Mahfoud, M., & Moulines, É. (2023). "Restarted Bayesian Online Change-Point Detection for Non-Stationary MDPs." arXiv:2304.00232. 5 citations. RL MDP transition kernel 변화 감지에 R-BOCPD 적용. FRCG-WM의 regime switch = MDP mode shift 해석에 직접 적용 가능.

[^cusum-rl]: Li, M., Shi, C., Wu, Z., & Fryzlewicz, P. (2022). "Testing stationarity and change point detection in reinforcement learning." arXiv:2203.01707. 14 citations. Offline RL Q-function 비정상성을 CUSUM으로 탐지. CUSUM-RL code repository 공개. // Ram, A. & Ramdas, A. (2026). "Asymptotically optimal sequential change detection for bounded means." arXiv:2602.05272. 3 citations. CUSUM sharp minimax lower bound 이론.

[^jepa-control]: Vujinović, A. & Kovacevic, A. (2025). "ACT-JEPA: Novel Joint-Embedding Predictive Architecture for Efficient Policy Representation Learning." arXiv:2501.14622. // Ulmen, J., Sundaram, G., & Görges, D. (2025). "Learning State-Space Models of Dynamic Systems from Arbitrary Data using JEPA." arXiv:2508.10489. 4 citations.

[^verisafe]: Lee, J. et al. (2025). "VeriSafe Agent: Safeguarding Mobile GUI Agent via Logic-based Action Verification." arXiv:2503.18492. 17 citations. Step-local verification — sequential evidence accumulation 없음. // **NEW DIRECT THREAT**: Cao, Y. et al. (2026). "MobileDreamer: Generative Sketch World Model for GUI Agent." arXiv:2601.04035. 4 citations. GUI WM으로 Android World SOTA (+5.25%). FRCG-WM과 차별점: wrong-grammar persistence 진단 없음, sequential falsification 없음.

[^whale-oxe]: Zhang, Z. et al. (2024). "WHALE: Towards Generalizable and Scalable World Models for Embodied Decision-making." arXiv:2411.05619. 5 citations. WHALE-X: 414M param WM on 970K OXE trajectories + uncertainty estimation. Passive OOD eval 비교점으로 활용 가능.

[^sprt-multi]: Ebihara, A.F. et al. (2020). "Deep Neural Networks for the Sequential Probability Ratio Test on Non-i.i.d. Data Series." arXiv:2006.05587. DNN-SPRT (SPRT-TANDEM) with LLLR loss. TASK_LFD_001 구현의 직접 참조. // Novikov, A. (2024). "A class of sequential multi-hypothesis tests." arXiv:2406.00930. 2 citations. k개 가설 SPRT 이론.

[^sweep-partial]: MCP sweep topics 11 (Kalman innovation test) 및 12 (Bayesian surprise): no targeted results. 참조: Mehra, R.K. (1971) "On the identification of variances and adaptive Kalman filtering" — whiteness test classical reference. Itti, L. & Baldi, P. (2009) "Bayesian Surprise attracts Human Attention" — Bayesian surprise classical reference.

[^dreamer-wm]: Topic 6 (Learned WM uncertainty). Hafner, D. et al. (2023). "Mastering Diverse Domains through World Models (DreamerV3)." arXiv:2301.04104. KL divergence of RSSM posterior as anomaly/uncertainty signal. FRCG-WM 차용 불가 부분: pixel-level reconstruction target — text/action domain에 부적합. BOCPD head의 prior 설계 참조는 가능.

[^value-compute]: Topic 7 (Value of computation / adaptive planning). Ott, J. et al. (2020). "Sequential Neural Likelihood Test for Hypothesis Testing under Model Misspecification." NeurIPS 2020. MuZero (Schrittwieser et al., 2020, Nature): value of computation = plan only when Q-value estimate changes significantly. FRCG-WM decision gate(decision_gate.py)의 delta_V 조건이 이 원칙을 approximation하나, threshold가 heuristic. AdaWM (Wang et al., 2025) "mismatch identification" for selective finetuning이 같은 원칙의 최근 적용 예.

[^robot-failure]: Topic 9 (Failure prediction in robotics trajectories). MCP sweep: no highly relevant papers found (false alarm / anomaly detection in robotics returned sensor-level anomaly papers). Classical reference: Léziart, P.A. et al. (2021) "Experience-driven Predictive Control with Additional Objectives." — early failure signal in manipulation. FRCG-WM 후보 E (robotics passive eval)에서는 supervised failure label 없이 unsupervised cusum_stat_t만 의미 있음.

[^counterfactual-offline]: Topic 11 (Counterfactual limitation offline robot dataset). Counterfactual actions이 없는 offline dataset에서 wrong-grammar detection이 왜 불가능한지: de Haan et al. (2019) "Causal Confusion in Imitation Learning" — 관측만으로는 environment dynamics와 policy dynamics를 분리 불가. FRCG-WM의 falsification evidence는 counterfactual effect type 비교를 필요로 하므로 offline robotics에서 primary evidence 불가.

[^rnn-cpd]: Topic 12 (Recurrent evidence accumulation / RNN-CPD). Schwarcz, J. et al. (2025). "Neural mechanisms of flexible perceptual inference." PMC12680366. mice가 latent context shift에 대한 sequential Bayesian belief update를 학습함을 실험적으로 확인 + RNN이 near-optimal Bayesian inference를 구현. FRCG-WM의 GRU carry-over 설계(TASK_LFD_002)와 직접 유사한 신경과학적 motivation 제공.

---

*작성 완료: 2026-05-19 | 다음 단계: 사용자 confirm → §12 Codex task queue 파일 별도 생성*
