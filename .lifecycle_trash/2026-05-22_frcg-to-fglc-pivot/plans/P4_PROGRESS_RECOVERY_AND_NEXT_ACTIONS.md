# P4 Progress Recovery and Next Actions

Generated: 2026-05-14  
Branch: `solo/p3-final-boss-cleared`  
HEAD commit: `ba204a8 feat(p3-eval): fix B1/B2 blockers → P3_EVAL.passed issued`  
Purpose: 이전 세션 삭제로 끊어진 P0~P4 진행상황 ledger를 레포 실물(코드/산출물/sentinel/commit) 근거로 복구한다. 추측·placeholder·가짜 수치를 포함하지 않는다.

---

## 0. Executive Summary

| 항목 | 내용 |
|---|---|
| 전체 진행 단계 | P3_EVAL **PASS w/ caveats** (sentinel `outputs/phase_gates/P3_EVAL.passed`, May 13 20:12); P4 **PENDING** (코드 0%) |
| 가장 강하게 확인된 완료 항목 | P0~P3 implementation + P3 evaluation infrastructure (TASK_999~TASK_1020, 22개 Codex 작업) |
| 가장 중요한 미완료 항목 | P4 GUI MVE data collector 전 파일 placeholder; CC-P3-G1(recovery_delay) 및 CC-P3-G3(no-control-grammar persistence) 논문 claim 미입증 |
| 다음 시작점 | `src/frcgw/gui_env/task_spec.py` (TaskSpec dataclass) — P4 §11.1 첫 번째 파일 |
| 주요 리스크 | G1/G3 FAIL이 P5 진입 전 미해결 시 논문 main claim 약화; `text_ood_grammar` shard 부재(B3 deferred); `outputs/runs/*` manifest에 `git_commit`/`config_hash`/top-level `timestamp` 누락 |

> **PHASE_PROGRESS.md drift 주의**: `plans/PHASE_PROGRESS.md` (May 9 18:11)는 P0~P3까지만 기록. `P3_EVAL.passed` sentinel(May 13)이 표에 미반영된 **stale ledger** 상태. 본 MD가 최신 ground truth.

---

## 1. Evidence Map

| 증거 파일 | 내용 요약 |
|---|---|
| `outputs/phase_gates/P1.passed` | May 8 18:24, 0 B |
| `outputs/phase_gates/P1.5.passed` | May 8 18:24 |
| `outputs/phase_gates/P2.passed` | May 8 18:51 |
| `outputs/phase_gates/P3.passed` | May 9 18:10 (implementation gate) |
| `outputs/phase_gates/P3_EVAL.passed` | May 13 20:12 (evaluation gate) |
| `plans/P3_EVAL_GATE_REPORT.md` | Generated 2026-05-13T11:11:04 UTC — G1 FAIL, G2 PASS, G3 FAIL, G4 PASS (§2.2 참조) |
| `outputs/runs/p3_eval/summary.txt` | 45 results (FRCG-FULL + BASE-001~014 × seed 0~4 × split=text_id, n=33 per run) |
| `outputs/runs/p3_ablations/ablation_results.json` | 65 결과 (13 ablation × 5 seed × split="text_ood_grammar" alias) |
| `outputs/runs/p3_smoke/manifest.json` | seed=42, max_steps=80, n_epochs=1, l_total_final=5.1518 |
| `outputs/runs/p3_smoke/checkpoint_ep0.pt` | 17.3 MB |
| `data/frcgw_text/v0_1/audits/leakage_report.json` | `{"passed": true, "forbidden_found": [], "counterfactual_found": []}` |
| `data/frcgw_text/v0_1/audits/coverage_report.json` | gate_pass=true; 6개 비율 모두 threshold 상회 (아래 §2 P2 참조) |
| `plans/PHASE_PROGRESS.md:15-19` | P0~P3 PASS 기록; P3_EVAL 행 없음 (stale) |
| `.agent_tasks/codex_done/TASK_1019_..._RESULT.md` | eval_runner.py B1 fix; 7+7 tests passed |
| `.agent_tasks/codex_done/TASK_1020_..._RESULT.md` | frcg_agent.py B2 fix; 11 tests passed |
| `src/frcgw/gui_env/__init__.py:14` | `__all__: list[str] = []` (P4 placeholder) |
| `src/frcgw/logging/__init__.py:13` | `__all__: list[str] = []` (P4 placeholder) |
| `scripts/04_generate_gui_mve_data.py:16` | `raise NotImplementedError("CC-P4: implementation deferred.")` |
| `scripts/05_validate_dataset.py:16` | `raise NotImplementedError("CC-P4: implementation deferred.")` |

---

## 2. Phase-by-Phase Status

### P0 — Scaffold / Context / Rules

**Status: PASS** (sentinel 미발급이나 사실상 통과)

| 항목 | 상태 | 증거 |
|---|---|---|
| `paper_context_ref/` 18개 MD | PASS | `plans/PHASE_PROGRESS.md:15` "P0 PASS 2026-05-08" |
| `.claude/` (rules×2, skills×7, agents×7, hooks×11, commands×3) | PASS | P1.5 gate 체크리스트 |
| `CLAUDE.md`, `README.md`, `pyproject.toml`, `requirements.txt` | PASS | 동일 |
| `outputs/phase_gates/P0.passed` sentinel | **누락** | 디스크에 없음 — 선택적 보강 가능 |
| routing 이름 drift | **주의** | `CLAUDE.md`/README는 `_v1` suffix 없이 인용하나 디스크는 `_v1` suffix 존재 |

**Incomplete**: P0.passed sentinel 미발급; MD 라우팅 이름 drift.  
**Next Action (선택)**: P0.passed sentinel 발급. 이름 drift는 별도 task.

---

### P1 — Schema / Visibility / Dataset Contract

**Status: PASS** (`outputs/phase_gates/P1.passed`)

| 항목 | 상태 | 증거 |
|---|---|---|
| `src/frcgw/schemas/visibility.py` (15 forbidden fields, 5 visibility buckets, `assert_agent_observation_safe`) | PASS | `:25-41` |
| `src/frcgw/schemas/{step_schema,episode_schema,validation}.py` | PASS | P3 174 tests 포함 |
| `src/frcgw/data/leakage_auditor.py` | PASS | `tests/test_leakage_auditor.py` |
| `tests/test_visibility_contract.py`, `test_counterfactual_exclusion.py` | PASS | 53 tests baseline |
| forbidden fields 중복 정의 | **주의** | 4곳에 중복: `visibility.py` / `leakage_auditor.py` / 일부 baselines / configs/*.yaml — single-source 리팩터 미완 |

**Incomplete**: forbidden fields 중복 정의 4곳 — drift 위험.  
**Next Action (별도 task)**: forbidden fields를 `visibility.py` 단일 source로 통합.

---

### P1.5 — Harness Strengthening

**Status: PASS** (`outputs/phase_gates/P1.5.passed`)

| 항목 | 상태 | 증거 |
|---|---|---|
| 7 skills, 7 agents, 11 hooks, 3 commands | PASS | `plans/PHASE_PROGRESS.md:17` |
| `.claude/settings.json` hook 등록 | PASS | 동일 |
| `outputs/phase_gates/`, `outputs/test_reports/`, `outputs/eval_reports/` 디렉터리 | PASS | 동일 |
| `plans/PLUGIN_AUDIT_REPORT.md` initialized | PASS | 동일 |

**Incomplete**: 없음.

---

### P2 — Text-Only Data Generator

**Status: PASS** (`outputs/phase_gates/P2.passed`)

| 항목 | 상태 | 증거 |
|---|---|---|
| `src/frcgw/text_env/{state,grammar,generator,policies,collector,replay}.py` | PASS | `plans/PHASE_PROGRESS.md:18` |
| `data/frcgw_text/v0_1/` 200 ep (train 132/valid 35/test_id 33) | PASS | manifest.json |
| `audits/leakage_report.json` | PASS | `{"passed": true, "forbidden_found": [], "counterfactual_found": []}` |
| `audits/coverage_report.json` gate_pass | PASS | 아래 참조 |
| `text_ood_grammar`, `text_noisy` shard | **FAIL (deferred)** | 디스크에 없음 — eval-side proxy(`_ALIAS`) 운용 중 |

**Coverage 수치** (`data/frcgw_text/v0_1/audits/coverage_report.json`):

| Metric | Threshold | Actual | Pass |
|---|---|---|---|
| failed_action_ratio | ≥0.20 | 0.3892 | ✓ |
| recovery_ratio | ≥0.08 | 0.2385 | ✓ |
| repeated_wrong_mapping_ratio | ≥0.08 | 0.2206 | ✓ |
| shift_ratio | ≥0.08 | 0.0998 | ✓ |
| reveal_ratio | ≥0.05 | 0.0639 | ✓ |
| delayed_or_noisy_or_no_op_valid_ratio | ≥0.03 | 0.1008 | ✓ |

**Incomplete**: text_ood_grammar shard 부재 (G3 비교가 in-distribution proxy).  
**Next Action (B3)**: `src/frcgw/text_env/generator.py`에 grammar shift mid-episode 시나리오 추가 → 30+ episodes 생성. 우선순위: LOWER (debug plan §B3).

---

### P3 — World Model Training (Implementation Gate)

**Status: PASS** (`outputs/phase_gates/P3.passed`, May 9 18:10)

| 항목 | 상태 | 증거 |
|---|---|---|
| `src/frcgw/models/{encoders,latent_heads,world_model_heads,text_frcg_model}.py` | PASS | TransformerEncoder + GRU + MLP heads, ~460k params |
| `src/frcgw/objectives/{losses,rewards}.py` (6 main + 4 aux losses) | PASS | manifest `objective_weights` |
| `src/frcgw/planning/{falsification,alternative_proposer,decision_gate,rewrite,planner}.py` | PASS | FALS-02/PROP-03/G_hybrid/RW-02/RW-06 |
| `src/frcgw/training/train_text.py` smoke loop | PASS | 80 steps, l_total 7.43→3.14 (training_log.jsonl) |
| 174 pytest passed | PASS | `plans/PHASE_PROGRESS.md:19` |
| Smoke checkpoint | PASS | `outputs/runs/p3_smoke/checkpoint_ep0.pt` 17.3 MB |
| Multi-step latent transition (z_t→z_{t+1}) | **PARTIAL** | `world_model_heads.py:83-91` rollout_step은 H=1만 처리 — RSSM-style multi-step 없음 |
| 다중 seed / variance 측정 | **없음** | smoke는 seed=42 단일 run (manifest.json:127 `"seed": 42`) |
| outputs manifest에 `git_commit`/`config_hash`/top-level `timestamp` | **누락** | manifest.json에 해당 키 없음 |

**Smoke train 최종 손실** (`outputs/runs/p3_smoke/manifest.json`):

| Loss | Final value |
|---|---|
| l_action_effect | 0.7844 |
| l_change_point | 2.2820 |
| l_control_grammar | 1.6293 |
| l_failed_action | 0.6793 |
| l_regime | 1.6363 |
| l_reveal_shift | 0.5987 |
| **l_total** | **5.1518** |

Note: `l_falsification=0.0`, `l_intent_action_mapping=0.0`, `l_temporal_consistency=0.0` — objective_weight=0.0으로 비활성화 (smoke config).

**Incomplete**: RSSM-style multi-step rollout 부재; 재현성 metadata 누락.  
**Next Action**: P5 단계에서 본격 학습. P3에서 추가 작업 없음.

---

### P3_EVAL — Closed-loop Evaluation + Ablation (Evaluation Gate)

**Status: PASS w/ caveats** (`outputs/phase_gates/P3_EVAL.passed`, May 13 20:12)

#### PASS 근거

P4 entry criteria (`plans/P3_FINAL_EVAL_AND_P4_GUI_MVE_PLAN.md:273-275`):
- "G3 또는 G4 중 최소 하나 PASS" → **G4 PASS** ✓
- "G1 + G2 중 최소 하나 PASS" → **G2 PASS** ✓

따라서 sentinel 발급은 contract 적합.

#### Gate 결과 (`plans/P3_EVAL_GATE_REPORT.md:7-12`, Generated 2026-05-13T11:11:04 UTC)

| Gate | 정의 (roadmap §9.6) | Status | Evidence (직접 인용) |
|---|---|---|---|
| CC-P3-G1 | FRCG-text beats verifier-only on recovery_delay | **FAIL** | FRCG-FULL=2.5454545454545454; VerifierOnlyAgent=2.5454545454545454 |
| CC-P3-G2 | FRCG-text beats uncertainty-gated on progress_per_compute | **PASS** | FRCG-FULL=0.22848484848484846; UncertaintyGatedAgent=0.09062499999999998 |
| CC-P3-G3 | no-control-grammar ablation worsens persistence | **FAIL** | no_control_grammar persistence=1.9090909090909092; FRCG-FULL persistence=1.9090909090909092 |
| CC-P3-G4 | no-falsification ablation worsens recovery/falsification | **PASS** | no_falsification f1=0.0; FRCG-FULL f1=0.4032258064516129 |

#### Ablation 수치 직접 인용 (`outputs/runs/p3_ablations/ablation_results.json`, seed=0 기준)

**no_control_grammar** (seed=0, split="text_ood_grammar"):
```
wrong_control_grammar_persistence: 1.9090909090909092  ← FRCG-FULL과 동일
recovery_delay:                    2.5454545454545454  ← FRCG-FULL과 동일
failed_action_repetition_rate:     0.125               ← FRCG-FULL(0.5)과 다름
falsification f1:                  0.0                 ← FRCG-FULL(0.4032)과 다름
progress_per_compute:              0.05975             ← FRCG-FULL(0.2285)보다 낮음
```

**no_falsification** (seed=0, split="text_ood_grammar"):
```
wrong_control_grammar_persistence: 1.9090909090909092
recovery_delay:                    2.5454545454545454
falsification f1:                  0.0                 ← G4 PASS 근거
progress_per_compute:              0.22848484848484846 ← FRCG-FULL과 동일
```

**5 seed 모두 동일 수치** — variance = 0.

#### Caveats (논문 claim 측면 UNKNOWN)

**Caveat 1 (G1 FAIL — recovery_delay 차별화 없음)**:  
FRCG-FULL의 recovery_delay = VerifierOnly = 2.5454 across all 5 seeds. FRCG가 verifier-only 대비 더 빠른 hypothesis update를 보이지 못함. 논문 main claim "FRCG가 wrong-grammar persistence를 줄인다"의 핵심 evidence 부재.

**Caveat 2 (G3 FAIL — no-control-grammar ablation 효과 없음)**:  
no_control_grammar persistence = FRCG-FULL persistence = 1.9090 across all 5 seeds. control grammar 모듈 제거가 persistence를 악화시키지 못함 → ablation이 inference path에 영향 못 주거나 환경이 control grammar를 요구하지 않을 가능성.

**Caveat 3 (variance = 0)**:  
5 seed에서 동일 수치 → TextFRCGModel forward가 deterministic이거나 hypothesis selection이 seed에 의존하지 않음. act()가 seed-independent 결과를 산출하는지 추가 진단 필요.

**Caveat 4 (text_ood_grammar split은 alias)**:  
`ablation_results.json`의 split="text_ood_grammar"는 eval-runner측 `_ALIAS`로 `test_id`에 매핑 (debug plan §B3). 실제 OOD shard 부재 → G3 비교가 in-distribution proxy 기반.

#### B1/B2 fix 사실 (`TASK_1019`/`TASK_1020`)

- **B1 (TASK_1019, May 13 19:52)**: `src/frcgw/evaluation/eval_runner.py`에 `_compute_episode_timestamps` 도입 — step 시퀀스로부터 recovery/hypothesis_update timestamp 산출 (data 재생성 우회). 7+7 tests passed.
- **B2 (TASK_1020, May 13 19:56)**: `src/frcgw/evaluation/frcg_agent.py` 신규 (`TextFRCGModelAgent`). 11 tests passed.
- **B3 (text_ood_grammar shard)**: deferred — LOWER priority. eval runner `_ALIAS` proxy로 우회 중.

#### 완료된 인프라

- `src/frcgw/evaluation/{metrics,baselines(9),ablations(12),eval_runner,frcg_agent,reporter,compute_budget}.py`
- `outputs/runs/p3_eval/{metrics.json, summary.txt}` (45 baseline results)
- `outputs/runs/p3_ablations/ablation_results.json` (65 ablation results)
- `plans/P3_EVAL_GATE_REPORT.md`

**Next Action**:
- (a) G1/G3 root cause 진단 — FRCG-FULL과 baseline의 per-step act() 결과 동일성 확인 (trace mode 재실행, 사용자 승인 필요)
- (b) variance=0 원인 진단 — TextFRCGModel.forward 결정성 / hypothesis sampling 결정성 확인
- (c) B3: text_ood_grammar shard 생성 (Codex 위임, 별도 task)

---

### P4 — Synthetic GUI MVE Data Collection

**Status: PENDING (코드 0%)**

| 항목 | 상태 | 증거 |
|---|---|---|
| `src/frcgw/gui_env/__init__.py` | placeholder | `:14` `__all__: list[str] = []` |
| `src/frcgw/gui_env/{task_spec,template_generator,regime_grammar_engine,event_scheduler,action_space,browser_executor,collector}.py` | **미작성** | 파일 없음 |
| `src/frcgw/logging/__init__.py` | placeholder | `:13` `__all__: list[str] = []` |
| `src/frcgw/logging/{action_effect_logger,counterfactual_logger,replay_validator}.py` | **미작성** | 파일 없음 |
| `scripts/04_generate_gui_mve_data.py` | placeholder | `:16` NotImplementedError |
| `scripts/05_validate_dataset.py` | placeholder | `:16` NotImplementedError |
| `configs/data_collection_gui_mve.yaml` | **전 값 null** | 디스크 확인 |
| Design | DONE | `plans/P3_FINAL_EVAL_AND_P4_GUI_MVE_PLAN.md` §11~§12 |
| P4 gate 정의 (roadmap §10.6) | DONE | 아래 참조 |

**P4 Pass Gates** (`paper_context_ref/13_CLAUDE_CODE_EXECUTION_ROADMAP_v1.md:538-545`):

| Gate | Pass Condition |
|---|---|
| CC-P4-G1 | deterministic replay pass |
| CC-P4-G2 | visibility/leakage audit pass |
| CC-P4-G3 | coverage audit pass |
| CC-P4-G4 | screenshot/DOM/a11y timestamps aligned |
| CC-P4-G5 | counterfactual actions valid and excluded from agent input |
| CC-P4-G6 | 50k~200k valid transitions for DATA-T3 |

**Next Action**: §5 참조.

---

## 3. Current Repo Reality vs Intended Research Blueprint

| Blueprint Claim | 현재 구현 Evidence | Gap | Severity |
|---|---|---|---|
| FRCG가 verifier-only 대비 recovery 빠름 (G1) | recovery_delay 동일 (2.5454 / 2.5454) | FRCG의 act()가 baseline과 동일 결과 산출 가능성 — 진단 필요 | **HIGH** |
| no-control-grammar ablation이 persistence 악화 (G3) | persistence 동일 (1.9090 / 1.9090) | ablation masking이 inference path에 영향 못 줌 — control grammar 제거가 behavior를 바꾸지 않음 | **HIGH** |
| FRCG가 progress/compute 우월 (G2) | 0.2285 vs 0.0906 (UncertaintyGated) | 차별화 확인됨 | NONE |
| FRCG의 falsification PR > no_falsification (G4) | f1 0.4032 vs 0.0 | 차별화 확인됨 | NONE |
| RSSM-style multi-step latent rollout | world_model_heads.py H=1 one-step only | P5 backbone 교체 시 영향 가능 | MEDIUM |
| 5 seed variance | variance=0 across all seeds | forward/sampling이 seed-independent — 통계적 검증 불가 | **HIGH** |
| text_ood_grammar split 분리 | _ALIAS → test_id proxy | 실제 OOD 비교 불가 | MEDIUM |
| outputs/runs manifest 재현성 | git_commit/config_hash/timestamp 키 없음 | 실험 재현 metadata 부족 | MEDIUM |
| Compute-matched baselines (P6) | 미시작 | P6 영역 | N/A (현 단계) |

---

## 4. Critical Invariants Check

| Invariant | Status | Evidence |
|---|---|---|
| No oracle metadata leakage in inference input | **PASS** | `src/frcgw/schemas/visibility.py:25-41` 15 forbidden fields; `assert_agent_observation_safe` 5곳 호출 (collector, dataset, losses, planner, eval_runner) |
| `data/frcgw_text/v0_1/` jsonl hidden label 보유 | **TRUE (의도됨)** | jsonl 원본은 `training_labels.true_*`, `audit_metadata.policy_id/seed`, top-level `split_id` 보유. inference time drop 책임: `text_dataset.py:84` `collate_fn`. `audits/leakage_report.json`: passed |
| Leakage audit PASS | **PASS** | `{"passed": true, "forbidden_found": [], "counterfactual_found": []}` |
| Test/OOD HP selection 누수 | **UNKNOWN** | text_smoke 1 run만 존재 (epoch 1, 80 step). HP search 없으니 현재 leakage 없음. 향후 HP search 추가 시 contract 강화 필요 |
| Same backbone across baselines | **PARTIAL** | baselines 전부 heuristic (BASE-001~014) — backbone 공정성 비교 불가. FRCG-FULL만 TextFRCGModel 사용. 본격 비교는 P5 frozen VLM에서 |
| Train/valid/test split 분리 | **PARTIAL** | train/valid/test_id 디스크 분리 (132/35/33). text_ood_grammar split은 디스크에 없음 (eval-side proxy) |
| Checkpoint 미수정 | **PASS** | `outputs/runs/p3_smoke/checkpoint_ep0.pt` 17.3 MB, May 13 19:57 — meta만 확인 |

---

## 5. Immediate Continuation Plan

### Next 1 hour (선택적 정비 작업, 코드 미수정)

```
- (선택) plans/PHASE_PROGRESS.md에 P3_EVAL row 추가 (PASS w/ caveats, May 13 20:12)
- (선택) outputs/phase_gates/P0.passed sentinel 발급
- 본 MD git commit
```

### Next 1 day (G1/G3 진단 — 사용자 승인 필요)

G1/G3 root cause 진단 두 가지 경로:

**경로 A — act() 동일성 확인**:
`outputs/runs/p3_eval/metrics.json`의 per-step action_id 기록 없음 → eval_runner를 일회성 trace mode로 재실행 필요 (사용자 승인 후).
진단 포인트:
1. `TextFRCGModelAgent.act()` vs `VerifierOnlyAgent.act()` 반환값 동일 여부
2. `TextFRCGModel.forward()` — seed 변경 시 logit이 달라지는지
3. `AlternativeHypothesisProposer` — hypothesis sampling에 seed가 반영되는지

**경로 B — 모델 capacity 부족**:
1 epoch / 80 step smoke → control grammar head가 의미있는 분리를 학습 못했을 가능성.
확인: `l_control_grammar` final = 1.6293 (높은 편) → 추가 epoch 학습 후 재평가.

### Next 3 days (P4 구현 — Codex 위임, TASK_2001~2010)

P4 §11.1 구현 순서 (`plans/P3_FINAL_EVAL_AND_P4_GUI_MVE_PLAN.md` §11):

1. `src/frcgw/gui_env/task_spec.py` — TaskSpec dataclass ← **다음 시작점**
2. `src/frcgw/gui_env/template_generator.py` — UITemplateGenerator
3. `src/frcgw/gui_env/regime_grammar_engine.py` — GRAM-001~021
4. `src/frcgw/gui_env/event_scheduler.py` — EVT-001~010
5. `src/frcgw/gui_env/action_space.py` — ACT-001~015
6. `src/frcgw/gui_env/browser_executor.py` — synthetic backend
7. `src/frcgw/gui_env/collector.py` — episode collection
8. `src/frcgw/logging/action_effect_logger.py`
9. `src/frcgw/logging/counterfactual_logger.py` (eval-only; agent observation에 절대 미포함)
10. `src/frcgw/logging/replay_validator.py`

동시 진행:
- `configs/data_collection_gui_mve.yaml` null 값 채우기
- `scripts/04_generate_gui_mve_data.py`, `scripts/05_validate_dataset.py` 구현
- 100 episode dry-run → CC-P4-G1~G6 검증

**P3 G1/G3 caveat vs P4 병렬 진행 권장**: P4는 데이터 contract 검증 단계이므로 G1/G3 미해결 상태에서도 병렬 진행 가능. 단, P5/P6에서 G1/G3 재해결이 필요함을 인지한 상태로 진행.

### Before next full experiment run (재현성 보강)

- `outputs/runs/*` manifest에 `git_commit`, `config_hash`, top-level `timestamp` 추가
- forbidden fields single-source 리팩터 (4곳 중복 → `visibility.py` 단일 source)

---

## 6. Commands to Run Locally

### Read-only inspection (실행 가능, 파일 미수정)

```powershell
git rev-parse HEAD
git log --oneline -n 10
Get-ChildItem outputs\phase_gates | Select-Object Name, Length, LastWriteTime
Get-ChildItem outputs\runs -Recurse -File | Select-Object FullName, Length, LastWriteTime
Get-Content outputs\runs\p3_eval\summary.txt
Get-Content outputs\runs\p3_smoke\manifest.json | ConvertFrom-Json | Select-Object n_epochs, n_steps, seed, final_losses
```

### Optional validation (실행 가능)

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pytest -q tests/test_visibility_contract.py tests/test_leakage_auditor.py tests/test_counterfactual_exclusion.py
.\.venv\Scripts\python.exe -m pytest -q tests/test_frcg_agent.py tests/test_eval_runner_timestamps.py
```

### 금지 (사용자 승인 없이 실행 불가)

```powershell
# 금지 — P3 추가 학습은 사용자 승인 후
python -m frcgw.training.train_text ...

# 금지 — eval 재실행은 사용자 승인 후
python scripts/03_eval_text_smoke.py

# 금지 — 어떤 파일도 수정 불가
# outputs/, data/, paper_context_ref/, checkpoint 수정 모두 금지
```

---

## 7. Open Questions for User

1. **G1/G3 caveat 해결 우선순위**: P4 시작 전에 G1/G3 root cause 진단을 먼저 할지, P4 데이터 수집과 병렬로 진행할지? (병렬 권장 — P4는 데이터 contract 검증 단계이므로 독립적)

2. **B3 text_ood_grammar shard**: G3 재평가와 한 묶음으로 처리할지 (shard 생성 → eval 재실행)? 아니면 P4 이후로 deferred 유지?

3. **Ledger 정합성 작업**: `plans/PHASE_PROGRESS.md`에 P3_EVAL row 추가 및 `P0.passed` sentinel 발급을 지금 진행할지, 별도 follow-up으로 할지?

4. **Codex orchestration 다음 TASK 번호**: `TASK_2001`부터 시작할지, `TASK_1100`부터 시작할지?

---

## 8. 재현 절차 (Reproducibility Reference)

본 MD 작성 시 읽은 파일 목록 (모두 read-only, 수정 없음):

```
paper_context_ref/13_CLAUDE_CODE_EXECUTION_ROADMAP_v1.md      §9.6, §10.6 (gate definitions)
outputs/runs/p3_eval/summary.txt                               45-line result list
outputs/runs/p3_ablations/ablation_results.json                no_control_grammar / no_falsification seed=0 인용
outputs/runs/p3_smoke/manifest.json                            seed, n_steps, final_losses
data/frcgw_text/v0_1/audits/leakage_report.json               passed=true
data/frcgw_text/v0_1/audits/coverage_report.json               gate_pass=true, 6 ratios
plans/P3_EVAL_GATE_REPORT.md                                   L7-12 gate table
plans/P3_FINAL_EVAL_AND_P4_GUI_MVE_PLAN.md                    §10 P4 entry criteria (L273-275)
plans/PHASE_PROGRESS.md                                        L15-19 phase table
src/frcgw/gui_env/__init__.py                                  L14 empty __all__
src/frcgw/logging/__init__.py                                  L13 empty __all__
scripts/04_generate_gui_mve_data.py                            L16 NotImplementedError
scripts/05_validate_dataset.py                                 L16 NotImplementedError
.agent_tasks/codex_done/TASK_1019_..._RESULT.md               B1 fix fact
.agent_tasks/codex_done/TASK_1020_..._RESULT.md               B2 fix fact
```

---

## 9. Completion Criteria Checklist

- [x] `plans/P4_PROGRESS_RECOVERY_AND_NEXT_ACTIONS.md` 단일 파일 작성 (다른 파일 수정 없음)
- [x] P0~P3_EVAL 각각 PASS / PASS w/ caveats / PARTIAL / PENDING 분류됨
- [x] 각 분류에 파일경로 evidence 1개 이상 첨부됨
- [x] G1 FAIL: recovery_delay=2.5454545454545454 (FRCG=verifier) 인용
- [x] G3 FAIL: persistence=1.9090909090909092 (FRCG=no_control_grammar) 인용
- [x] P4 진입 첫 시작점: `src/frcgw/gui_env/task_spec.py` 수준으로 좁혀짐
- [x] Critical invariants 7개 행 PASS/PARTIAL/UNKNOWN 분류됨
- [x] PHASE_PROGRESS.md drift (stale ledger) 본문에 노출됨
- [x] forbidden field 중복 정의 4곳 사실 본문에 노출됨
- [x] `outputs/`/checkpoint 미수정 (§8 재현 절차에서 read-only 명시)
- [x] open questions 4개 이내 명시됨
