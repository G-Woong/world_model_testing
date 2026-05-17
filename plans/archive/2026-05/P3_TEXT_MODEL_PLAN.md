# P3_TEXT_MODEL_PLAN.md

> 1차 저장: `C:\Users\computer\.claude\plans\venv-ps-generic-frog.md` (Plan Mode)
> Sonnet execution phase 복제: `plans/P3_TEXT_MODEL_PLAN.md` (본 파일)

## Context

P0 scaffold → P1 schema/visibility → P1.5 hardening → P2 text-only data generator(200 ep / 1002 step, P2 Gate PASS, leakage 0건)까지 완료. 다음 단계는 **P3 = tiny FRCG text model 구현**이다. 본 plan은 학습 가능한 최소 모델·loss·falsification·alternative proposer·decision gate·rewrite module 구현과 unit/integration test까지의 범위를 고정한다. Step 7(P3 evaluation/ablation, baseline 비교)은 분리된 후속 plan으로 다룬다.

핵심 헌법 2개:
- **Novelty**: `wrong-control-grammar persistence`를 직접 줄이는 mechanism이어야 한다. 차용은 LR/VOC/EVoI 원리만, 변형은 `h_exec` vs alt-grammar hypothesis 비교로 한다. 단순 next-state-WM/verifier-only/uncertainty-gate가 되면 안 된다.
- **Feasibility**: P2 dataset의 `TrainingLabels`/`EvaluationLabels`가 모든 main loss target을 제공하므로 학습 가능. tiny scale(<1M params)로 closed-loop dry-run까지 한 번에 검증한다.

---

## 1. Read Context

```text
필수 1차 read (plan 작성 단계에서 완독):
- CLAUDE.md
- .claude/rules/codex_orchestration_rules.md
- .claude/rules/research_context_rules.md
- paper_context_ref/00_CONTEXT_INDEX.md
- paper_context_ref/03_CORE_CONCEPT_TAXONOMY.md
- paper_context_ref/04_TEXT_ONLY_SMOKE_TESTBED.md
- paper_context_ref/06_DATA_SCHEMA_AND_LABELING.md
- paper_context_ref/07_LATENT_ARCHITECTURE_DESIGN.md
- paper_context_ref/08_LOSS_REWARD_TRAINING_OBJECTIVE.md
- paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md
- paper_context_ref/10_EVALUATION_BASELINE_ABLATION.md
- plans/P2_GATE_REPORT.md
- src/frcgw/schemas/{visibility.py, step_schema.py, episode_schema.py}
- src/frcgw/text_env/{state.py, grammar.py, generator.py, collector.py}
- data/frcgw_text/v0_1/manifest.json (200 ep, 1002 step, splits 132/35/33)
```

---

## 2. Current Repository State

| 항목 | 상태 |
|---|---|
| current branch | `feat/p1-schema-visibility` (HEAD `664eebc`) |
| `outputs/phase_gates/P2.passed` | EXISTS — P3 진입 가능 |
| `plans/P2_GATE_REPORT.md` | EXISTS |
| `data/frcgw_text/v0_1/manifest.json` | EXISTS, coverage_gate_pass=true, leakage_gate_pass=true |
| `src/frcgw/{models,objectives,planning,training}/` | greenfield (`__init__.py`만 존재) |
| `configs/model_text.yaml`, `configs/train_text.yaml` | P0 stub (`null` 값) — P3가 채움 |

---

## 3. P3 Scope

### 구현 대상 (P3 IN-SCOPE)

```text
src/frcgw/data/text_dataset.py
src/frcgw/models/encoders.py
src/frcgw/models/latent_heads.py
src/frcgw/models/world_model_heads.py
src/frcgw/models/text_frcg_model.py
src/frcgw/objectives/losses.py
src/frcgw/objectives/rewards.py
src/frcgw/planning/falsification.py
src/frcgw/planning/alternative_proposer.py
src/frcgw/planning/decision_gate.py
src/frcgw/planning/rewrite.py
src/frcgw/planning/planner.py
src/frcgw/training/train_text.py
src/frcgw/training/monitoring.py
configs/model_text.yaml
configs/train_text.yaml
scripts/02_train_text_smoke.py
tests/test_text_frcg_model.py
tests/test_losses.py
tests/test_falsification.py
tests/test_decision_gate.py
tests/test_rewrite.py
tests/test_train_text_smoke.py
```

### P3 OUT-OF-SCOPE
- P4 GUI/synthetic Web env, VLM, screenshot encoder
- Step 7 full evaluation/ablation runner
- paper-main claim 작성
- `paper_context_ref/` 수정
- 대규모 training run (smoke train 제한: ≤2 epoch, ≤32 batch×10 step)
- `git push`, hidden labels의 inference input 사용

---

## 4. Novelty Deep-Dive

P3 mechanism: **`F_t(LR over h_exec vs alt grammar) → 4-condition gate → grammar-conditioned rewrite`** 폐루프

| # | 질문 | 핵심 답변 |
|---|---|---|
| 1 | 단순 next-state model과 다른가? | F_t = ell(h_alt*) - ell(h_exec)로 hypothesis-level 비교. effect prediction은 ell 계산용 |
| 2 | verifier-only와 다른가? | LR 기반 비교 (current vs alternative). 단순 failure BCE가 아님 |
| 3 | uncertainty-gated와 다른가? | gate는 4조건 필수. F_t 없이 entropy만으로 gate 불가 |
| 4 | LR 차용 변형? | learned approximation q_phi. control grammar latent에 LR 적용 |
| 5 | regime/grammar 분리? | 두 latent head 분리, collapsed/merged ablation config 제공 |
| 6 | falsification 붕괴 방지? | alt score 차이가 BCE에 반드시 반영. alt를 batch에 포함 강제 |
| 7 | gate threshold 방지? | 4조건 모두 필수 (unit test로 uncertainty_alone 차단 검증) |
| 8 | rewrite imitation 방지? | grammar-conditioned ranking head. oracle_grammar_action은 training target만 |
| 9 | 결과 나쁘면? | claim 톤다운, Step 7으로 연기 |
| 10 | Step 7 ablation? | no-falsification, no-control-grammar, no-rewrite로 살림/죽임 판단 |

---

## 5. Feasibility Deep-Dive

| # | 질문 | 답변 |
|---|---|---|
| 1 | P2 dataset에 필요 label 다 있나? | YES — TrainingLabels + EvaluationLabels 완비 |
| 2 | 각 loss target 존재? | 6 main + 4 aux 모두 P2 schema 필드에 매핑 가능 |
| 3 | leakage 차단? | strip_to_agent_observation() + assert_agent_observation_safe() 기존 구현 |
| 4 | tiny model 학습 가능? | ~460k params, GRU+Transformer, 660 train sample이면 OK |
| 5 | smoke train 조건? | CPU ≤5분 (batch=8, step=80) |

---

## 6. Core Algorithm Design

### 6.1 Falsification score (FALS-02)

```
F_t = max_{h_alt ∈ A_t^H} [ ell_t(h_alt) - ell_t(h_exec) ]

ell_t(h) = log p_theta(e_t | H_{t-1}, a_{t-1}, h)
         = log Cat(true_action_effect_type | effect_logits(h, a, H))
           + λ_p * log p(progress_delta | progress_pred(h, a, H))
           + λ_f * log p(failed_action | failure_pred(h, a, H))
```

### 6.2 Alternative proposer (PROP-03 hybrid)

```
score(h_alt) = α_b * log b_t(h_alt) + α_l * ell_t(h_alt)
A_t^H = top_k(score, k=3)
```

### 6.3 Decision gate (G_hybrid)

```python
def should_plan(F_t, ΔV_t, P_switch, C_plan, τ_f, τ_v, τ_a) -> bool:
    return (F_t > τ_f and ΔV_t > τ_v and P_switch > τ_a and (ΔV_t - C_plan) > 0)
```

### 6.4 Rewrite (RW-02 + RW-06 fallback)

```
grammar_emb = grammar_embedding(h*.z_control_grammar)
scores = [head_rank(intent_emb, cand_emb, grammar_emb) for cand in candidates]
top = candidates[argmax(scores)]
```

---

## 7. Model Architecture Plan

### 7.1 Tiny model spec (~460k params)

| 컴포넌트 | 구현 | 크기 |
|---|---|---|
| TextStateEncoder | embedding → 2-layer Transformer(d=128, heads=4, ff=256) → CLS pool | ~250k |
| HistoryEncoder | GRU(hidden=128, 1 layer) | ~100k |
| LatentPosterior | MLP → 4 head linears (z_state/z_regime/z_control_grammar/z_change_point) | ~50k |
| AuxHeads | precondition(BCE), failure_risk(BCE) | ~5k |
| WorldModelHeads | [h_t||z||action_emb] → effect_type(7), progress_delta, failed_action | ~30k |
| RewriteHead | MLP [intent||cand||grammar_emb] → score | ~15k |
| AlternativeProposer | linear posterior→score | ~5k |
| **Total** | | **~460k** |

---

## 8. Loss / Reward Plan

### 8.1 Main 6 + Aux 4

| Loss | Source | Target field | Weight |
|---|---|---|---|
| L_action_effect | L-MAIN-001 | true_action_effect_type | 1.0 |
| L_progress | L-MAIN-002 | progress_delta | 0.5 |
| L_regime | L-MAIN-003 | true_regime | 1.0 |
| L_control_grammar | L-MAIN-004 | true_control_grammar | 1.0 |
| L_falsification | L-MAIN-005 | true_wrong_hypothesis | 1.0 |
| L_intent_action_mapping | L-MAIN-006 | recovery_action_id (mask if None) | 0.5 |
| L_change_point | L-AUX-002 | true_change_point | 0.3 |
| L_reveal_shift | L-AUX-003 | true_reveal_vs_shift | 0.3 |
| L_failed_action | L-AUX-001 | true_failed_action | 0.3 |
| L_temporal_consistency | L-AUX-005 | KL(posterior_t, sg(posterior_{t-1})) | 0.1 |

---

## 9. Codex Sub-task Decomposition (7 tasks)

| TASK | 파일 | 의존성 |
|---|---|---|
| C1_text_dataset_loader | data/text_dataset.py + test | P2 schema |
| C2_encoders | models/encoders.py + latent_heads.py + test | C1 |
| C3_world_model_and_model | models/world_model_heads.py + text_frcg_model.py + test | C2 |
| C4_objectives | objectives/losses.py + rewards.py + test | C3 |
| C5_falsification_alt_proposer | planning/falsification.py + alternative_proposer.py + test | C3 |
| C6_gate_rewrite_planner | planning/decision_gate.py + rewrite.py + planner.py + tests | C5 |
| C7_train_smoke | training/train_text.py + monitoring.py + configs + scripts + test | C1..C6 |

---

## 10. P3 Gate PASS 조건

```text
[ ] pytest -q 100% PASS (P0/P1/P2 regression 0건)
[ ] tests/test_text_dataset.py PASS
[ ] tests/test_text_frcg_model.py PASS
[ ] tests/test_losses.py PASS
[ ] tests/test_falsification.py PASS
[ ] tests/test_decision_gate.py PASS
[ ] tests/test_rewrite.py PASS
[ ] tests/test_train_text_smoke.py PASS
[ ] smoke train manifest + checkpoint 존재 (커밋 안 함)
[ ] hidden label inference input = 0건
[ ] paper_context_ref/ unchanged
[ ] forbidden path 수정 0건
[ ] frcgw-code-reviewer PASS or WARNING-only
[ ] frcgw-experiment-evaluator PASS or UNKNOWN-with-justification
[ ] outputs/phase_gates/P3.passed sentinel 생성
```

---

## 11. Risks

| ID | 항목 | 완화 |
|---|---|---|
| R-P3-01 | latent collapse (small data) | aux probe + Step 7 collapsed-latent 비교 |
| R-P3-02 | valid_hypothesis_switch label sparse | P3에서 switch reward 비활성화 |
| R-P3-03 | top-3 alt에 true alt 미포함 | oracle hook으로 Step 7 upper bound check |
| R-P3-04 | tiny model 8 grammars 학습 실패 | hidden=192/depth=3 확장 옵션 |
| R-P3-05 | Windows worktree sandbox lock | -BypassSandbox default |
| R-P3-06 | rewrite head training 불안정 | weight=0.5, Step 7 sweep |
| R-P3-07 | h_exec tracker 동기화 | unit test + EvaluationLabels.h_exec_id 비교 |
| R-P3-08 | GPU 가용성 | CPU로 batch=8, step=80 smoke train |

**Blockers (현재): none**

---

## 12. Commit Policy

```text
P3 진입 직후:
  git commit -m "plan(p3): finalize P3 text model implementation plan and Codex tasks"

각 TASK accept 후:
  git commit -m "feat(p3-c{N}): <subscope>"

P3 완료 통합:
  git commit -m "feat(p3): tiny text FRCG model + planning heads + smoke train"

금지: checkpoint commit, dataset/run log commit, paper_context_ref/ 수정,
      git push, --no-verify, amend
```
