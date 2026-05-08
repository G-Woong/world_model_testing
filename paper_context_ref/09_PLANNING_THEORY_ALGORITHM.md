---
file_id: STEP-09
title: Planning Theory and Algorithm Design for FRCG-WM
version: v1.0-10score
status: planning_algorithm_contract_not_final_evaluation
language: ko
source_file: 붙여넣은 마크다운(1)(83).md
upgraded_from: STEP-09 v0.1
purpose:
  - FRCG-WM의 planning/theory/algorithm을 구현 가능한 계약으로 고정한다.
  - falsification score, alternative hypothesis proposal, short rollout, decision-relevance gate, action-interface rewrite가 분리되지 않고 하나의 실행 경로로 이어지게 만든다.
  - Claude Code가 필요한 context만 확장적으로 읽어 algorithm, data schema, objective, evaluation을 안전하게 수정할 수 있도록 routing layer를 제공한다.
  - uncertainty-gated planning, verifier-only recovery, tree search, generic world model search와의 차이를 수식/알고리즘/ablation으로 방어한다.
forbidden:
  - Do not report empirical results.
  - Do not claim empirical success.
  - Do not write the final paper evaluation section.
  - Do not treat uncertainty-gated planning as equivalent to falsification-guided planning.
  - Do not treat alternative hypothesis as alternative action.
  - Do not use hidden labels or counterfactual tables as inference-time inputs.
  - Do not use exact Bayesian language unless explicitly marked as learned approximation.
depends_on:
  - 00_MASTER_REFERENCE.md
  - 01_RELATED_WORK_THREAT_MAP.md
  - 02_PROBLEM_NOVELTY_FALSIFICATION.md
  - 03_CORE_CONCEPT_TAXONOMY.md
  - 04_TEXT_ONLY_SMOKE_TESTBED.md
  - 05_SYNTHETIC_WEB_GUI_ENVIRONMENT.md
  - 06_DATA_SCHEMA_AND_LABELING.md
  - 07_LATENT_ARCHITECTURE_DESIGN.md
  - 08_LOSS_REWARD_TRAINING_OBJECTIVE.md
next_files:
  - 10_EVALUATION_BASELINE_ABLATION.md
---

# 09_PLANNING_THEORY_ALGORITHM.md

## 1. 이 파일의 역할

이 파일은 최종 실험 결과 문서가 아니다. 이 파일은 FRCG-WM의 planning/theory/algorithm을 **실제로 구현 가능한 계약**으로 고정하는 문서다.

핵심 목표는 다음 한 줄로 요약된다.

> FRCG-WM의 planner는 “불확실성이 높으니 더 생각한다”가 아니라, **직전 action을 만든 current control-grammar hypothesis가 action-effect evidence에 의해 반증되고, alternative regime/control-grammar hypothesis 아래에서 action choice가 바뀌며, 그 expected progress gain이 compute cost를 넘을 때만 planning compute를 쓰는 구조**여야 한다.

이 문서는 다음을 강제한다.

1. `current hypothesis`는 현재 posterior mode가 아니라 **직전 action/macro 생성에 실제 사용된 executed hypothesis `h_exec`**로 정의한다.
2. `alternative hypothesis`는 alternative action이 아니라 **alternative regime/control-grammar hypothesis**다.
3. `falsification score`는 단순 실패 flag가 아니라, current hypothesis가 observed action-effect evidence를 설명하지 못하는 정도다.
4. `short rollout`은 generic MCTS가 아니라, current vs alternative grammar hypothesis를 비교하는 1~3 step 가설 조건부 rollout이다.
5. `decision-relevance gate`는 falsification, expected value gain, action switch probability, compute cost를 모두 고려한다.
6. `action-interface rewrite`는 selected grammar에 따라 base intent/action을 executable primitive 또는 macro로 바꾼다.
7. 모든 component는 data field, architecture module, objective, metric, ablation과 연결되어야 한다.

---

## 2. Claude Code Context Routing

Claude Code는 이 파일을 단독으로 읽고 method를 구현하면 안 된다. 작업 목적별로 아래 routing을 따른다.

| 작업 의도 | 먼저 읽을 파일 | 이어서 읽을 파일 | 금지 가정 |
|---|---|---|---|
| planning algorithm 수정 | `09_PLANNING_THEORY_ALGORITHM.md` §6~§15 | `03`, `06`, `07`, `08`, `10` | uncertainty gate와 FRCG gate가 같다고 가정 금지 |
| falsification score 수정 | `09` §7, §16 | `03` §falsification, `06` action-effect schema, `08` L_falsification, `10` falsification metrics | failed_action flag만으로 falsification 정의 금지 |
| alternative hypothesis proposer 구현 | `09` §8, §15 | `03` alternative hypothesis, `07` proposer module, `06` counterfactual schema | alternative action과 alternative hypothesis 혼동 금지 |
| short rollout 구현 | `09` §9, §13 | `05` counterfactual generator, `06` counterfactual fields, `08` L_counterfactual_rollout | long-horizon simulator를 당연시 금지 |
| decision gate 수정 | `09` §10, §14 | `08` reward-to-planning pathway, `10` compute-matched evaluation | compute cost 없는 planning claim 금지 |
| action rewrite 구현 | `09` §11, §13 | `03` control grammar, `07` rewrite module, `06` executable action schema | rewrite를 단순 retry로 축소 금지 |
| evaluation 연결 | `09` §15~§18 | `10_EVALUATION_BASELINE_ABLATION.md` | success rate 하나로 planning claim 검증 금지 |

---

## 3. Citation-Grade External Anchor Ledger

이 파일의 planning novelty는 직접 위협 연구와 구분되어야 한다. 아래 anchor는 Step 10에서 반드시 baseline/ablation으로 연결되어야 한다.

| Anchor ID | Work / Concept | URL | 핵심 요지 | FRCG-WM에 대한 위협 | 필요한 방어 |
|---|---|---|---|---|---|
| EXT-09-001 | WebWorld: A Large-Scale World Model for Web Agent Training | https://arxiv.org/abs/2602.14721 | open-web simulator/world model, 1M+ interactions, long-horizon simulation, inference-time search | generic web world model novelty를 강하게 위협 | FRCG는 generic simulation이 아니라 wrong-control-grammar persistence와 falsification-guided rewrite를 겨냥한다고 좁혀야 함 |
| EXT-09-002 | Computer-Using World Model, CUWM | https://arxiv.org/abs/2602.17365 | frozen agent가 candidate actions를 world model로 simulate/compare하는 test-time search | frozen base + world model action search가 이미 존재 | alternative action search가 아니라 regime/control-grammar hypothesis search임을 보이고 CUWM-style baseline 필요 |
| EXT-09-003 | World-Model-Augmented Web Agents with Action Correction, WAC | https://arxiv.org/abs/2602.15384 | consequence simulation과 action correction으로 web agent 행동 개선 | action correction/rewrite claim 위협 | grammar-conditioned rewrite와 falsification score, no-control-grammar ablation 필요 |
| EXT-09-004 | VeriGUI: Action-Effect Verification and Self-Correction | https://arxiv.org/abs/2604.05477 | action-effect verification, failure recognition, self-correction, robustness benchmark | action-effect evidence와 recovery claim 직접 위협 | verification-only가 아니라 current-vs-alt grammar hypothesis likelihood와 action-interface rewrite임을 실험으로 방어 |
| EXT-09-005 | MiniWoB++ / BrowserGym-style benchmark family | public benchmark family | controlled web interaction tasks | synthetic/testbed 설계가 toy처럼 보일 위험 | text-only → synthetic Web/GUI → optional real benchmark 계층화 필요 |
| EXT-09-006 | Value of Computation / Rational Metareasoning | classical theory anchor | computation has cost and value | theory 과장 위험 | exact optimal VOC가 아니라 learned proxy gate로 명시 |
| EXT-09-007 | Likelihood Ratio / Sequential Hypothesis Testing | classical theory anchor | evidence로 hypotheses 비교 | exact Bayesian/SPRT 주장 위험 | learned evidence-likelihood approximation으로만 사용 |

---

## 4. Algorithm Design Constitution

| Rule ID | 헌법 | 위반 설계 | 왜 위험한가 | 강제 guardrail |
|---|---|---|---|---|
| PLAN-CONST-001 | Falsification은 failed-action flag가 아니다 | `if failed: plan()` | verification-only와 구분 불가 | likelihood ratio 또는 calibrated wrong-current score 사용 |
| PLAN-CONST-002 | Alternative는 action이 아니라 hypothesis다 | `alt = other click action` | tree search/MCTS와 구분 불가 | `h_alt=(z_state,z_regime,z_control_grammar,z_change)` tuple로 제한 |
| PLAN-CONST-003 | Current hypothesis는 `h_exec`다 | posterior mode만 current로 사용 | persistence metric 오염 | 직전 action 생성 시 사용된 hypothesis를 trace에 저장 |
| PLAN-CONST-004 | Planning은 decision-relevant할 때만 한다 | always-plan | compute 효율 claim 붕괴 | `F_t`, `ΔV_t`, `P_switch`, `C_plan` 모두 gate에 포함 |
| PLAN-CONST-005 | Rewrite는 grammar-conditioned mapping이다 | retry 또는 random recovery | action-interface rewrite novelty 붕괴 | intent→macro/precondition/effect schema 참조 |
| PLAN-CONST-006 | Hidden labels는 inference input 금지 | `true_control_grammar`를 prompt에 넣음 | leakage로 실험 무효 | `build_agent_observation()` assertion |
| PLAN-CONST-007 | Counterfactual table은 inference input 금지 | alt effect table을 agent에게 제공 | oracle leakage | training/eval-only shard |
| PLAN-CONST-008 | No-effect는 곧 falsification이 아니다 | no-effect → wrong grammar | loading/delayed/noisy effect 오판 | delayed/noisy flags를 negative evidence로 분리 |
| PLAN-CONST-009 | Theory는 learned approximation이다 | exact Bayesian/POMDP optimality 주장 | reviewer 공격 | 모든 posterior/likelihood/value를 learned proxy로 명시 |
| PLAN-CONST-010 | Algorithm claim은 ablation과 연결되어야 한다 | pseudo-code만 제시 | 메인트랙 설득력 부족 | no-falsification/no-alt/no-rollout/no-gate/no-rewrite ablation 의무화 |

---

## 5. Symbol Table

| Symbol | 의미 | 구현 field/module | inference input 가능 여부 | 위험 |
|---|---|---|---:|---|
| `t` | step index | trace step id | YES | off-by-one |
| `o_t` | raw environment observation | raw DOM/screenshot/state | NO, raw hidden 포함 가능 | hidden leakage |
| `x_t` | sanitized public observation | `build_agent_observation()` output | YES | sanitization 실패 |
| `a_t` | executed primitive/macro action | action executor log | YES, previous action only | macro/primitive 혼동 |
| `i_t` | base agent intent | frozen base output | YES | intent 추론 오류 |
| `e_t` | action-effect evidence | observed effect + diff + flags | YES, sanitized summary | noisy/delayed effect |
| `H_t` | public history | sanitized observation/action/effect sequence | YES | long-history drift |
| `z^s_t` | latent state | state head | NO as true label | state가 모든 것을 흡수 |
| `z^r_t` | latent regime | regime head | NO as true label | grammar와 collapse |
| `z^g_t` | latent control grammar | grammar head | NO as true label | precondition classifier로 축소 |
| `z^c_t` | change/event latent | event head | NO as true label | visual diff detector화 |
| `h_t` | hypothesis tuple | `(z^s,z^r,z^g,z^c)` | predicted only | tuple 범위 모호 |
| `h_t^exec` | 직전 action 생성에 사용된 hypothesis | trace/belief logger | predicted trace only | posterior mode와 혼동 |
| `A_t^H` | alternative hypothesis set | proposer output | predicted only | alternative action과 혼동 |
| `b_t(z^r,z^g)` | regime/grammar belief | latent posterior | predicted only | calibration risk |
| `ell_t(h)` | evidence log-likelihood | current/alt scorer | predicted only | likelihood scale 문제 |
| `F_t` | falsification score | falsification scorer | predicted only | failure flag로 축소 위험 |
| `V(a,h)` | hypothesis-conditioned expected value | short rollout + progress predictor | predicted only | progress overfit |
| `ΔV_t` | best alternative gain | decision gate | predicted only | reward scale 의존 |
| `P_switch` | alternative 아래 action이 바뀔 확률 | selector/gate | predicted only | candidate set 의존 |
| `C_plan` | planning compute cost | compute logger | YES, runtime | cost 추정오차 |
| `G_t` | decision gate | VOC gate | predicted only | over/underplanning |
| `a_t^rewrite` | rewritten action/macro | rewrite module | YES, executed action | invalid macro |

---

## 6. Minimal Theory Spine

### 6.1 Learned belief over regime/control grammar

```text
b_t(z^r, z^g) = q_phi(z^r, z^g | H_t)
```

- 이는 exact Bayesian posterior가 아니다.
- `q_phi`는 history encoder와 latent posterior module이 만든 learned approximation이다.
- true labels는 training/evaluation에만 쓰이고 inference input으로는 쓰지 않는다.

### 6.2 Evidence likelihood

```text
ell_t(h) = log p_theta(e_t | H_{t-1}, a_{t-1}, h)
```

`ell_t(h)`는 hypothesis `h`가 직전 action-effect evidence `e_t`를 얼마나 잘 설명하는지 나타낸다. `e_t`는 단순 실패 flag가 아니라 다음을 포함한다.

- observed effect type
- DOM diff summary
- accessibility diff summary
- visual diff score
- precondition status
- no-effect flag
- delayed-effect flag
- noisy-observation flag
- progress delta
- failure reason

### 6.3 Main falsification score candidate

```text
F_t = max_{h_alt ∈ A_t^H} [ell_t(h_alt) - ell_t(h_exec)]
```

해석:

```text
F_t가 크다 = 직전 action을 생성한 current/executed hypothesis보다 alternative hypothesis가 evidence를 더 잘 설명한다.
```

반드시 지킬 것:

- `h_exec`는 posterior mode가 아니라 action 생성 시점에 사용된 hypothesis다.
- `A_t^H`는 alternative actions가 아니라 alternative state/regime/control-grammar/change hypotheses다.
- failed action 하나만으로 `F_t`를 정의하지 않는다.

### 6.4 Hypothesis-conditioned expected progress

```text
V(a, h) = E_{tau_hat ~ WM_theta(h,a)} [Σ_{i=1}^{H} γ^(i-1) progress_{t+i} - η failure_{t+i}] - β compute(a,h)
```

기본 horizon 후보:

- text-only smoke: `H ∈ {1,2,3}`
- synthetic Web/GUI main: default `H=3`, ablation `H=1,5`
- long rollout은 main claim이 아니라 appendix/stress candidate

### 6.5 Decision-relevance / VOC-style gate

```text
ΔV_t = max_{h_alt∈A_t^H, a∈A} V(a,h_alt) - max_{a∈A} V(a,h_exec)

G_t = I[
    F_t > τ_f
    ∧ ΔV_t > τ_v
    ∧ P(action_switch | A_t^H, H_t) > τ_a
    ∧ ΔV_t - C_plan > 0
]
```

이 gate는 `uncertainty > threshold`가 아니다. 네 조건이 모두 만족되어야 planning compute를 쓴다.

1. current hypothesis가 evidence로 반증될 가능성이 있다.
2. alternative hypothesis가 더 나은 expected progress를 만든다.
3. 실제 action choice가 바뀔 가능성이 있다.
4. 그 이득이 compute cost보다 크다.

### 6.6 Final action selection and rewrite

```text
h* = argmax_{h ∈ {h_exec} ∪ A_t^H} max_a V(a,h)

a* = argmax_a V(a,h*)

a_exec = Rewrite(intent=i_t, base_action=a_base, selected_hypothesis=h*)
```

fallback rule:

```text
if rewrite_confidence < τ_r or precondition_check(a_exec)==INVALID:
    use base_action or verifier-only safe fallback
```

---

## 7. Falsification Score Candidates

| ID | Score | Formula / Rule | 장점 | 약점 | 상태 |
|---|---|---|---|---|---|
| FALS-01 | Current NLL | `-log p(e_t | h_exec)` | 간단함 | alternative 비교 없음 | AUXILIARY |
| FALS-02 | Likelihood Ratio | `max_alt ell(h_alt)-ell(h_exec)` | hypothesis comparison 명확 | alt proposer quality 의존 | MAIN |
| FALS-03 | Calibrated wrong-current classifier | `σ(f(H,e,h_exec))` | supervised 학습 쉬움 | black-box classifier 위험 | ABLATION |
| FALS-04 | Effect mismatch score | `d(expected_effect, observed_effect)` | 직관적 | noisy/delayed effect 취약 | AUXILIARY |
| FALS-05 | Hybrid score | `w1*LR + w2*mismatch + w3*progress_gap` | robust 가능 | 가중치 arbitrary | ABLATION |
| FALS-06 | Posterior drop | `b_{t-1}(h_exec)-b_t(h_exec)` | belief update와 연결 | posterior calibration 민감 | UNKNOWN |
| FALS-07 | Counterfactual regret | `max_alt V_alt - V_cur` | planning value와 직접 연결 | synthetic-only | APPENDIX |

Main candidate는 `FALS-02`다. 단, Step 10에서 `FALS-03`, `FALS-04`, uncertainty gate와 비교해야 한다.

---

## 8. Alternative Hypothesis Proposal Contract

| ID | Strategy | Input | Output | 사용 위치 | 위험 | 필수 ablation |
|---|---|---|---|---|---|---|
| PROP-01 | posterior top-k | `b_t(z^r,z^g)` | top-k hypotheses | 기본 proposer | posterior miss | top-k=1/3/5 |
| PROP-02 | evidence-likelihood top-k | `e_t`, `ell(h)` | evidence best hypotheses | falsification aligned | likelihood miscalibration | likelihood vs posterior |
| PROP-03 | posterior × likelihood hybrid | posterior + evidence likelihood | balanced alternatives | MAIN candidate | threshold 복잡 | hybrid vs posterior |
| PROP-04 | failure-type conditioned | failure reason | plausible grammar family | 효율적 | verifier-like shortcut | no failure reason |
| PROP-05 | grammar embedding neighbor | grammar embedding | nearby hypotheses | OOD recombination | embedding shortcut | OOD split |
| PROP-06 | retrieval from past traces | trace index | recovered hypotheses | data efficient | train/test leakage | retrieval baseline |
| PROP-07 | rule-based text-only | symbolic rules | grammar candidates | smoke test | GUI 확장 약함 | text-only only |
| PROP-08 | learned proposer | encoder output | hypothesis distribution | scalable | black-box | learned vs rule |
| PROP-09 | oracle proposer | true labels | true alt | upper bound | inference 불가 | oracle gap |
| PROP-10 | random proposer | random grammar | random alt | baseline | 약함 | random alt baseline |

명시 규칙:

```text
Alternative hypothesis proposal은 alternative action proposal이 아니다.
Action은 selected hypothesis 아래에서 다시 ranking/rewrite된다.
```

---

## 9. Short-Horizon Rollout Contract

| ID | Horizon | Predicts | 장점 | 약점 | 권장 사용 |
|---|---:|---|---|---|---|
| ROLL-01 | 1 | immediate effect/failure | 빠르고 안정 | recovery macro 부족 | smoke baseline |
| ROLL-02 | 2 | blocker removal + next progress | recovery에 적합 | 약간의 compounding | main candidate option |
| ROLL-03 | 3 | progress/failure/reward | grammar switch 효과 포착 | cost 증가 | main default |
| ROLL-04 | 5 | longer progress | long task 반영 | compounding error | ablation |
| ROLL-05 | adaptive | dynamic horizon | 유연 | gate 복잡 | appendix |
| ROLL-06 | no-rollout | scoring only | 빠름 | value comparison 약함 | baseline |
| ROLL-07 | next-state-only | next UI state | generic WM baseline | grammar 약함 | threat baseline |
| ROLL-08 | progress-only | progress delta | value 직접적 | failure risk 무시 | ablation |
| ROLL-09 | failure-risk-aware | progress + failure risk | 안전성 | 보수성 | main component |
| ROLL-10 | counterfactual-supervised | counterfactual effects | synthetic fidelity 높음 | real extension 제한 | training/eval only |

---

## 10. Decision Gate Contract

Main candidate:

```text
G_hybrid = I[F_t > τ_f ∧ ΔV_t > τ_v ∧ P_switch > τ_a ∧ ΔV_t - C_plan > 0]
```

| Gate | Rule | 장점 | 약점 | 역할 |
|---|---|---|---|---|
| falsification-only | `F_t>τ_f` | 간단 | action이 안 바뀌어도 planning | ablation |
| uncertainty-only | `U_t>τ_u` | 강한 baseline | wrong hypothesis 직접 반영 안 함 | threat baseline |
| progress-gain-only | `ΔV_t>τ_v` | value 중심 | falsification 없음 | ablation |
| switch-only | `P_switch>τ_a` | decision relevance | value 없음 | ablation |
| VOC-only | `ΔV-C>0` | compute cost 반영 | falsification 없음 | support |
| hybrid | all conditions | 논문 claim과 정렬 | threshold tuning | MAIN |
| oracle gate | true wrong/alt | upper bound | inference 불가 | upper bound |
| random gate | Bernoulli | compute baseline | 의미 약함 | baseline |
| always-plan | always true | upper-ish | compute 비효율 | baseline |

---

## 11. Action-Interface Rewrite Contract

Rewrite는 selected control grammar 아래에서 intent를 executable action/macro로 바꾸는 단계다.

| ID | Strategy | Input | Output | 장점 | 위험 | 상태 |
|---|---|---|---|---|---|---|
| RW-01 | rule-based rewrite | intent, grammar, symbolic actions | macro | 해석 쉬움 | coverage 낮음 | text-only |
| RW-02 | grammar-conditioned action ranking | intent, candidate actions, grammar | ranked action | 안정적 | candidate 밖 행동 생성 불가 | main early |
| RW-03 | learned rewrite head | encoded intent/hypothesis/actions | action/macro | 확장성 | invalid macro | main if stable |
| RW-04 | macro generation | grammar schema + primitives | multi-step macro | modal/form/permission에 강함 | safety/complexity | appendix/main |
| RW-05 | retrieval recovery | evidence + trace DB | recovery action | data efficient | leakage | baseline |
| RW-06 | base fallback | low confidence | base action | regression 방지 | 회복 실패 | guardrail |
| RW-07 | oracle rewrite | true grammar | oracle action | gap 분석 | inference 불가 | upper bound |

Rewrite validity check:

```python
def validate_rewrite(action_macro, public_obs, predicted_grammar):
    assert "true_control_grammar" not in public_obs
    if not action_macro.is_executable():
        return False, "not_executable"
    if violates_public_precondition(action_macro, public_obs):
        return False, "precondition_violation"
    if predicted_grammar.confidence < TAU_REWRITE:
        return False, "low_confidence"
    return True, "ok"
```

---

## 12. Text-Only Algorithm Contract

```python
def text_frcg_plan(state_text, history, candidate_actions, model):
    """Smoke-test prototype. Not final deployed algorithm."""

    # public symbolic observation only
    intent = model.infer_intent(state_text, history)

    # h_exec = hypothesis used to generate previous/current mapping
    h_exec = model.infer_executed_hypothesis(state_text, history)

    # structured evidence, not just failed_action
    evidence = model.extract_action_effect_evidence(history)

    F = model.falsification_score(h_exec=h_exec, evidence=evidence)

    if F < model.tau_f:
        return model.select_base_action(candidate_actions), {
            "planned": False,
            "reason": "low_falsification",
        }

    alternatives = model.propose_alternative_hypotheses(
        state_text=state_text,
        history=history,
        evidence=evidence,
        k=model.k_alt,
    )

    current_value = model.short_rollout(
        hypothesis=h_exec,
        candidate_actions=candidate_actions,
        horizon=model.horizon,
    )

    alt_values = []
    for h_alt in alternatives:
        alt_values.append(model.short_rollout(
            hypothesis=h_alt,
            candidate_actions=candidate_actions,
            horizon=model.horizon,
        ))

    gate = model.decision_relevance_gate(
        falsification_score=F,
        current_value=current_value,
        alternative_values=alt_values,
        compute_cost=model.compute_cost,
    )

    if not gate.should_plan:
        return model.select_base_action(candidate_actions), {
            "planned": False,
            "reason": "not_decision_relevant",
        }

    rewritten_action = model.rewrite_action(
        intent=intent,
        selected_hypothesis=gate.best_hypothesis,
        candidate_actions=candidate_actions,
    )

    return rewritten_action, {
        "planned": True,
        "reason": "falsified_and_decision_relevant",
        "selected_hypothesis": gate.best_hypothesis.public_id,
    }
```

---

## 13. Synthetic Web/GUI Algorithm Contract

```python
def web_gui_frcg_step(raw_env_obs, trace_history, frozen_base_agent, frcgw):
    """Synthetic Web/GUI candidate algorithm.

    Inference-time inputs must be public only.
    Hidden labels/counterfactual tables are excluded.
    """

    public_obs = frcgw.build_agent_observation(raw_env_obs, trace_history)
    forbidden = {
        "true_regime",
        "true_control_grammar",
        "true_change_point",
        "true_reveal_vs_shift",
        "counterfactual_action_effects",
        "oracle_grammar_action",
    }
    assert forbidden.isdisjoint(set(public_obs.keys()))

    base = frozen_base_agent.propose(
        instruction=public_obs["instruction"],
        dom_tree=public_obs.get("dom_tree"),
        accessibility_tree=public_obs.get("accessibility_tree"),
        screenshot_ref=public_obs.get("screenshot_ref"),
        history=frcgw.public_history(trace_history),
    )

    x = frcgw.encode_public_observation(public_obs)
    e = frcgw.extract_public_evidence(trace_history)
    H = frcgw.history_encoder(x, e, trace_history)

    posterior = frcgw.latent_posterior(H)
    h_exec = frcgw.executed_hypothesis_tracker(trace_history, posterior)

    F = frcgw.falsification_scorer(h_exec=h_exec, evidence=e)

    if F < frcgw.tau_f:
        action = base.default_action
        decision = {"planned": False, "reason": "low_falsification"}
    else:
        alternatives = frcgw.propose_alternative_hypotheses(
            posterior=posterior,
            evidence=e,
            k=frcgw.k_alt,
        )

        cur_rollout = frcgw.rollout(
            hypothesis=h_exec,
            candidate_actions=base.candidate_actions,
            horizon=frcgw.horizon,
        )
        alt_rollouts = [
            frcgw.rollout(hypothesis=h, candidate_actions=base.candidate_actions, horizon=frcgw.horizon)
            for h in alternatives
        ]

        gate = frcgw.decision_gate(
            falsification_score=F,
            current_rollout=cur_rollout,
            alternative_rollouts=alt_rollouts,
            compute_cost=frcgw.estimate_compute_cost(alt_rollouts),
        )

        if not gate.should_plan:
            action = base.default_action
            decision = {"planned": False, "reason": "not_decision_relevant"}
        else:
            rewritten = frcgw.rewrite_action(
                intent=base.intent,
                base_action=base.default_action,
                selected_hypothesis=gate.best_hypothesis,
                candidate_actions=base.candidate_actions,
            )
            valid, invalid_reason = frcgw.validate_rewrite(rewritten, public_obs, gate.best_hypothesis)
            if valid:
                action = rewritten
                decision = {
                    "planned": True,
                    "reason": "falsified_decision_relevant_rewrite_valid",
                    "best_hypothesis_public_id": gate.best_hypothesis.public_id,
                }
            else:
                action = base.default_action
                decision = {
                    "planned": False,
                    "reason": f"rewrite_invalid:{invalid_reason}",
                }

    result = frcgw.action_executor.execute(action)
    frcgw.trace_logger.log_public_and_private_separately(
        public_obs=public_obs,
        base_output=base,
        posterior_summary=frcgw.public_posterior_summary(posterior),
        decision=decision,
        final_action=action,
        execution_result=result,
    )
    return action, result, decision
```

---

## 14. Minimal Viable Experiment for Planning

이 파일이 구현 가능하려면 Step 10 이전에 최소 다음 실험이 가능해야 한다.

| MVE ID | 목적 | 최소 환경 | 필요한 모듈 | 성공 조건 | 실패 시 해석 |
|---|---|---|---|---|---|
| MVE-09-001 | text-only falsification gate sanity | 5 task × 5 grammar | evidence scorer, rule proposer | verifier-only보다 recovery delay 감소 | falsification novelty 약화 |
| MVE-09-002 | likelihood ratio vs failed flag | text-only delayed/noisy cases | likelihood scorer | no-effect shortcut 감소 | F_t 설계 수정 |
| MVE-09-003 | alternative hypothesis quality | text-only + synthetic labels | proposer | true alt top-k recall 상승 | proposer 약화 |
| MVE-09-004 | short rollout horizon sweep | H=1/3/5 | rollout model | H=3이 compute/return 균형 | horizon arbitrary |
| MVE-09-005 | hybrid gate vs uncertainty gate | same compute budget | gate variants | progress per compute 개선 | compute claim 약화 |
| MVE-09-006 | rewrite benefit | grammar-conditioned rewrite | rewrite module | failed repetition 감소 | rewrite claim 약화 |
| MVE-09-007 | no-hidden-label inference audit | schema/runtime assertion | observation builder | forbidden key 0 | 실험 무효 |
| MVE-09-008 | synthetic Web/GUI 1-page smoke | modal/form/scroll | full pipeline minimal | closed-loop trace 생성 | implementation blocker |

---

## 15. Planning Component Traceability

| Component | Architecture Module | Objective | Data Field | Metric | Ablation |
|---|---|---|---|---|---|
| Public observation sanitation | Public Observation Builder | leakage audit | agent observation fields | leakage count | hidden label injected |
| Base intent/candidates | Frozen Base Agent | none/frozen | base intent, candidate actions | delta over base | base-only |
| Evidence encoding | Action-Effect Encoder | `L_action_effect` | observed/expected effect, diff flags | effect acc, falsification P/R | no action-effect |
| Current hypothesis tracking | Belief Logger / Current Hypothesis Scorer | `L_regime`, `L_control_grammar` | `h_exec` trace | persistence time | no h_exec tracking |
| Falsification scoring | Falsification Scorer | `L_falsification` | evidence likelihood, wrong-current label | falsification P/R | no F score |
| Alternative proposal | Alternative Hypothesis Proposer | ranking/contrastive | alternative labels/top-k | top-k recall | random alt |
| Short rollout | Rollout Model | `L_progress`, `L_counterfactual_rollout` | counterfactual effects | rollout fidelity | no rollout |
| Decision gate | VOC/Decision Gate | compute/progress objective | compute logs, `ΔV` | progress per compute | always-plan/no-gate |
| Rewrite | Rewrite Module | `L_intent_action_mapping` | oracle/recovery action | switch delay, failed repetition | no rewrite |
| Final action selection | Final Selector | ranking/reward | action logs | success/return | selector ablation |
| Trace logging | Logger | none | full trace | all offline metrics | no logger impossible |

---

## 16. Competing Method Difference Table

| Competing Method | 겉보기 유사점 | 본질적 차이 | 필수 실험 |
|---|---|---|---|
| verifier-only recovery | action-effect를 본다 | verification은 실패 감지/교정, FRCG는 hypothesis likelihood와 grammar rewrite | VeriGUI-style baseline |
| uncertainty-gated planning | compute gate가 있다 | uncertainty가 아니라 falsification + ΔV + action switch + cost | uncertainty gate ablation |
| always-plan world model | rollout을 한다 | FRCG는 decision-relevant할 때만 rollout | compute-matched always-plan |
| next-state-WM action search | action consequence를 예측한다 | FRCG는 control grammar hypothesis를 바꾼다 | next-state-WM-only |
| tree search/MCTS | alternatives를 비교한다 | FRCG alternative는 action tree가 아니라 grammar hypothesis | MCTS-style baseline |
| base LLM self-correction | 실패 후 수정한다 | FRCG는 structured evidence likelihood와 learned grammar posterior 사용 | self-correction prompt baseline |
| failure diagnosis only | 실패 원인을 본다 | FRCG는 diagnosis 후 executable action rewrite | diagnosis-only baseline |
| oracle planner | grammar를 안다 | oracle은 upper bound, FRCG는 inferred belief만 사용 | oracle gap |

---

## 17. Ablation-Collapse Rules

| Ablation | 기대되는 metric 변화 | 변화가 없으면 무너지는 claim |
|---|---|---|
| no falsification score | persistence↑, recovery delay↑, falsification P/R↓ | evidence-based falsification claim |
| uncertainty instead of falsification | false planning call↑ 또는 OOD grammar shift 성능↓ | falsification이 uncertainty보다 낫다는 claim |
| no alternative hypothesis | recovery delay↑, alt adoption↓ | alternative hypothesis claim |
| random alternative | top-k recall↓, recovery↓ | proposer quality claim |
| no rollout | progress per compute↓ | current-vs-alt rollout claim |
| no decision gate | planning calls↑, progress/compute↓ | decision-relevant compute claim |
| always-plan | return은 유사 가능, compute 효율↓ | compute reallocation claim |
| no rewrite | failed repetition↑, switch delay↑ | action-interface rewrite claim |
| no compute cost | overplanning↑ | VOC-style gate claim |
| top-k=1 | true alt miss↑ | multi-hypothesis proposal claim |
| top-k=5 | compute↑, possibly return↑ | k=3 tradeoff claim |
| horizon=1 | recovery macro miss↑ | 1-step insufficient claim |
| horizon=5 | rollout error/compute↑ | short-horizon choice claim |
| oracle alternative | upper bound gap 측정 | proposer learning bottleneck |
| oracle grammar | upper bound gap 측정 | grammar inference bottleneck |

---

## 18. Planning Stress Test Ledger

| ID | 공격 | 실패 모드 | 검출 | 수정 |
|---|---|---|---|---|
| PST-01 | delayed effect | false falsification | delayed split | stabilization window |
| PST-02 | noisy observation | invalid switch | noisy split | evidence smoothing |
| PST-03 | no-effect valid case | wrong hypothesis 오판 | no-effect-valid subset | no-effect alone 금지 |
| PST-04 | low uncertainty wrong grammar | missed recovery | low-U wrong-G subset | F_t 우선 |
| PST-05 | high uncertainty no action change | overplanning | P_switch=0 subset | action switch threshold |
| PST-06 | true alt absent top-k | bad rollout | oracle proposer gap | proposer recall loss |
| PST-07 | plausible wrong alt | wrong rewrite | alt confusion matrix | likelihood calibration |
| PST-08 | H=1 too short | recovery 실패 | horizon sweep | H=3 default |
| PST-09 | H=5 unstable | rollout error | fidelity vs horizon | cap horizon |
| PST-10 | k arbitrary | sensitivity | k sweep | report frontier |
| PST-11 | rewrite invalid macro | execution failure | macro validation | fallback |
| PST-12 | base action already correct | module harms | base-correct subset | low-F fallback |
| PST-13 | always-plan wins | gate weak | compute frontier | weaken compute claim |
| PST-14 | verifier-only matches | novelty weak | verifier baseline | strengthen grammar path |
| PST-15 | tree search matches | planning novelty weak | MCTS baseline | hypothesis-specific metrics |
| PST-16 | next-state-WM matches | grammar weak | next-state baseline | no-grammar ablation |
| PST-17 | posterior miscalibrated | bad threshold | ECE/Brier | calibration loss |
| PST-18 | reward scale bad | gate wrong | sensitivity | normalize |
| PST-19 | history drift | stale belief | long trace split | memory reset/summarize |
| PST-20 | OOD grammar fail | no generalization | OOD-control split | proposer redesign |
| PST-21 | synthetic artifact | shortcut | template MI audit | randomization |
| PST-22 | real benchmark no labels | metric absent | auxiliary plan | limit claims |
| PST-23 | base candidate lacks recovery action | rewrite impossible | candidate recall | macro generator |
| PST-24 | h_exec not logged | metric impossible | trace audit | logger blocker |
| PST-25 | counterfactual leakage | oracle shortcut | forbidden key scan | shard separation |

---

## 19. Required Design Revisions

| Revision ID | 문제 | 필수 수정 | 영향 Step | Severity |
|---|---|---|---|---|
| REV-09-001 | falsification이 failed flag로 축소됨 | likelihood ratio main candidate 유지 | 08,10 | CRITICAL |
| REV-09-002 | alternative action/hypothesis 혼동 | proposer output은 hypothesis tuple로 제한 | 03,07,10 | CRITICAL |
| REV-09-003 | uncertainty gate와 차별 약함 | uncertainty baseline과 decoupled split 필수 | 10 | CRITICAL |
| REV-09-004 | tree search와 차별 약함 | hypothesis-level metrics 추가 | 10 | HIGH |
| REV-09-005 | horizon/k arbitrary | sensitivity sweep 필수 | 10 | HIGH |
| REV-09-006 | delayed/noisy effect 오판 | evidence flags와 stabilization window | 06,08,10 | HIGH |
| REV-09-007 | compute cost 불명확 | rollout steps, calls, latency proxy 기록 | 06,10 | HIGH |
| REV-09-008 | rewrite invalid macro | validate_rewrite + fallback | 07,09 | HIGH |
| REV-09-009 | exact Bayesian 과장 | learned approximation wording | FINAL | MEDIUM |
| REV-09-010 | real benchmark counterfactual 부재 | synthetic core + real auxiliary로 분리 | 10 | HIGH |

---

## 20. Handoff to 10_EVALUATION_BASELINE_ABLATION.md

| Handoff ID | 반드시 넘길 항목 | Step 10에서 검증할 것 | 주장 금지 사항 |
|---|---|---|---|
| HANDOFF-09-001 | `F_t` likelihood-ratio falsification | verifier-only/uncertainty와의 차이 | F_t가 이미 검증됐다고 단정 금지 |
| HANDOFF-09-002 | alternative hypothesis proposer | top-k recall, random/oracle alt baseline | alt action search와 혼동 금지 |
| HANDOFF-09-003 | short rollout design | H=1/3/5, rollout fidelity | long rollout 필요성 단정 금지 |
| HANDOFF-09-004 | hybrid VOC gate | compute-matched progress/compute | compute 많이 써서 좋아진 것 아님을 증명 전 주장 금지 |
| HANDOFF-09-005 | action-interface rewrite | no-rewrite, invalid rewrite, base-correct subset | rewrite가 항상 이득이라고 주장 금지 |
| HANDOFF-09-006 | stress tests | delayed/noisy/OOD splits | no-effect를 wrong grammar로 단순화 금지 |

---

## 21. Updated Risk / Unknown Ledger

| Risk ID | Risk / Unknown | 왜 중요한가 | 해결 경로 | Final Claim 가능? |
|---|---|---|---|---|
| RISK-09-001 | `h_exec` trace 정의 실패 | persistence metric 불가 | 06 logger 필수 | NO |
| RISK-09-002 | falsification likelihood miscalibration | gate 오작동 | calibration + PR curves | NO |
| RISK-09-003 | alternative proposer top-k recall 낮음 | recovery 불가 | oracle gap + proposer redesign | NO |
| RISK-09-004 | rollout fidelity 낮음 | alternative value 불신 | rollout metric + horizon sweep | NO |
| RISK-09-005 | uncertainty gate와 차이 없음 | novelty 약화 | decoupled split | NO |
| RISK-09-006 | verifier-only와 차이 없음 | falsification 약화 | grammar-specific ablation | NO |
| RISK-09-007 | tree search와 차이 없음 | planning novelty 약화 | hypothesis metric | NO |
| RISK-09-008 | rewrite가 base action을 망침 | practical failure | fallback + base-correct subset | NO |
| RISK-09-009 | compute penalty underplanning | recovery 실패 | budget sensitivity | NO |
| RISK-09-010 | always-plan이 더 좋음 | compute claim 약화 | frontier reporting | NO |
| RISK-09-011 | synthetic counterfactual only | real validity 제한 | auxiliary real benchmark | NO |
| RISK-09-012 | no-effect shortcut | false falsification | no-effect balanced split | NO |
| RISK-09-013 | control grammar relabeling | novelty-by-renaming | no-grammar/merged ablation | NO |
| RISK-09-014 | exact theory overclaim | reviewer attack | learned approximation wording | NO |
| RISK-09-015 | threshold arbitrary | reproducibility 약화 | validation protocol | NO |
| RISK-09-016 | candidate set misses recovery | rewrite 불가 | macro generator or candidate expansion | NO |
| RISK-09-017 | top-k/horizon tuning cherry-pick | evaluation unfair | pre-registered sweep | NO |
| RISK-09-018 | hidden label leakage | 실험 무효 | runtime assertion | NO |

---

## 22. Quality Gate Result

| Gate ID | Gate | Status | Evidence | If Not PASS |
|---|---|---|---|---|
| QG-09-01 | 00~08 refs imported | PASS | source and reference ledgers retained | - |
| QG-09-02 | direct threat anchors included | PASS | WebWorld/CUWM/WAC/VeriGUI anchors | Step10 baseline화 필요 |
| QG-09-03 | theory candidates separated | PASS | Bayesian/LR/VOC/MPC/tree/uncertainty 분리 | - |
| QG-09-04 | exact inference overclaim avoided | PASS | learned approximation 명시 | - |
| QG-09-05 | symbol table operationalized | PASS | h_exec, e_t, F_t, ΔV, G_t 정의 | - |
| QG-09-06 | falsification candidates compared | PASS | 7 candidates | - |
| QG-09-07 | alternative hypothesis != action | PASS | proposer contract | - |
| QG-09-08 | rollout horizon sweep specified | PASS | H=1/3/5 | - |
| QG-09-09 | decision gate includes compute | PASS | `ΔV-C_plan>0` | - |
| QG-09-10 | rewrite contract executable | PASS | validate_rewrite pseudo-code | - |
| QG-09-11 | text-only pseudo-code exists | PASS | §12 | - |
| QG-09-12 | Web/GUI pseudo-code exists | PASS | §13 | - |
| QG-09-13 | MVE path exists | PASS | §14 | - |
| QG-09-14 | competing methods distinguished | PASS | §16 | Step10 empirical defense 필요 |
| QG-09-15 | ablation-collapse rules included | PASS | §17 | - |
| QG-09-16 | hidden labels banned at inference | PASS | assertions and rules | - |

---

## 23. Final Statement

```text
09_PLANNING_THEORY_ALGORITHM.md is a planning/theory contract file, not a final evaluation or empirical result file.

The strongest current planning candidate is:
- likelihood-ratio falsification score over executed current hypothesis vs top-k alternative regime/control-grammar hypotheses,
- posterior/evidence hybrid alternative proposer,
- 1~3 step failure-risk-aware short rollout,
- hybrid decision-relevance/VOC gate using falsification, expected value gain, action-switch probability, and compute cost,
- grammar-conditioned action-interface rewrite with fallback.

The minimal theory spine is:
- learned belief over latent regime/control grammar,
- evidence likelihood and likelihood-ratio falsification,
- expected progress under current vs alternative hypothesis,
- value-of-computation-style decision gate with action-switch relevance.

The most dangerous planning risks are:
- falsification score가 noisy/delayed/no-effect evidence를 wrong hypothesis로 오판하는 위험,
- alternative proposer가 true grammar를 top-k에 포함하지 못하는 위험,
- uncertainty-gate, verifier-only recovery, tree search, generic world model search와 실험적으로 구분되지 않는 위험,
- rewrite module이 base agent의 좋은 action을 망치는 위험,
- hidden/counterfactual labels가 inference input으로 새는 위험.

The planning algorithm must still be validated by:
- compute-matched always-plan, uncertainty-gated, verifier-only, next-state-WM, tree-search baselines,
- no-falsification, no-alternative, random-alternative, no-rollout, no-gate, no-rewrite ablations,
- top-k/horizon/threshold sensitivity,
- OOD-control grammar shift and delayed/noisy effect stress tests.

The next required file is:
10_EVALUATION_BASELINE_ABLATION.md
```
