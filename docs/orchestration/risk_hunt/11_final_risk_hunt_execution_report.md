# Final Risk-Hunt Execution Report — STEP 10 Phase 2 Verdict

작성일: 2026-05-19
담당: Main Claude (STEP 10 Phase 2 Loop Execution Orchestrator)
branch: `memory-redesign-2026-05-16` @ `bab31db` (pre-execution) + 본 세션 minimal patches
관련 보고서:
- `loop_reports/00_execution_preflight.md`
- `loop_reports/09_loop_01_proxy_off_eval.md`
- `loop_reports/09_loop_02_seed_validity.md`
- `loop_reports/09_loop_03_faithful_ablation.md`
- `loop_reports/09_loop_06_fair_compute_matching.md`

---

## 1. Executive Summary

**최종 claim verdict: `CLAIM_SHRINK_REQUIRED`**

| 영역 | 결과 |
|---|---|
| **C3 falsification (학습된 신호 주장)** | **DEAD** — Loop-01 proxy OFF에서 F1=0.000, predicted_wrong_count=0. STEP 9 F1=0.539 회복은 전부 `no_state_change→effect_type=3` 휴리스틱 의존이었음. |
| **C2 regime separability (latent disentanglement 주장)** | **DEAD at current setup** — Loop-03 ABL-001/003 retrain 결과 reference도 C2=0. ablation으로 collapse를 만드는 contrast 자체가 불가능. |
| **C6 advantage (14.9× progress per compute)** | **SHRUNK** — Loop-06 fair compute(ABL-036b RealNoGate)에서 ratio = 2.00× (self-report 분모 기준). 14.9× 보고는 ABL-036 heuristic-bypass 분모 artifact. |
| **Statistical validity** | **KEEP** — Loop-02 5-seed에서 C3 F1 std = 0.075 (range 0.42–0.58). STEP 9의 std=0.000 deterministic 문제 해소. 단 분산 자체가 휴리스틱 boundary 변동에서 기인. |
| **Loop-04 foresight causal** | **NOT RUN** — 별도 Codex task 후보. |

가장 중요한 사실: **STEP 9의 핵심 회복 metric (C3 F1=0.539, C6 14.9×) 모두 학습된 model signal이 아닌 proxy/self-report artifact**였다. 이는 paper main claim의 본질적 재구성을 요구한다.

---

## 2. 실행한 명령어 목록

| # | 명령 | 결과 | 산출물 |
|---|---|---|---|
| A1 | `git status` 등 preflight 진단 | OK | `loop_reports/00_execution_preflight.md` |
| B1 | `.venv/Scripts/python.exe scripts/risk_hunt/run_proxy_ablation_eval.py --max-episodes 50` | OK | `outputs/risk_hunt/experiments/loop01_proxy_ablation/` |
| Patch-α | `scripts/10_run_lr_real_eval.py` import + dispatch table에 `RealNoGateAblation`, `NoComputeGateAblation` 등록 | applied | (in-tree edit) |
| B2a | `.venv/Scripts/python.exe scripts/10_run_lr_real_eval.py --config configs/lr_eval_step10_fair_compute.yaml --max-episodes 50` (out-dir default) | OK but path 잘못됨 | `outputs/runs/p3_lr_real_eval/metrics.json` (재실행으로 폐기) |
| B2b | 동일 + `--out-dir outputs/risk_hunt/experiments/loop06_fair_compute` | OK | `outputs/risk_hunt/experiments/loop06_fair_compute/` |
| Patch-β | `scripts/risk_hunt/run_abl001_retrain.py` / `run_abl003_retrain.py` launcher에 `--output-dir` + `checkpoint_best.pt` promote 단계 추가 | applied | (in-tree edit) |
| B3a | `.venv/Scripts/python.exe scripts/risk_hunt/run_abl001_retrain.py` | OK | `outputs/checkpoints/abl001_no_regime/checkpoint_best.pt`, `outputs/risk_hunt/experiments/loop03_abl001_retrain/` |
| B3b | `.venv/Scripts/python.exe scripts/risk_hunt/run_abl003_retrain.py` | OK | `outputs/checkpoints/abl003_merged_regime_grammar/checkpoint_best.pt`, `outputs/risk_hunt/experiments/loop03_abl003_retrain/` |
| Patch-γ | `scripts/02_train_text_smoke.py`에 `--seed`, `--checkpoint-dir` argparse 추가. `scripts/risk_hunt/run_multiseed_training.py`에 promote 단계 추가 | applied | (in-tree edit) |
| B4a | `.venv/Scripts/python.exe scripts/risk_hunt/run_multiseed_training.py` | OK | 5 × `outputs/checkpoints/pretrain_v0_4_seed{42,123,456,789,999}/checkpoint_best.pt` |
| B4b | `.venv/Scripts/python.exe scripts/10_run_lr_real_eval.py --config configs/lr_eval_step10_multiseed.yaml --out-dir outputs/risk_hunt/experiments/loop02_multiseed --max-episodes 50` | OK | `outputs/risk_hunt/experiments/loop02_multiseed/` |

모든 실행 sample size: test_id split 50 episodes (284 steps per agent).

---

## 3. 적용된 코드 수정 요약

모두 STEP C 분류 A/D/E (path/checkpoint/argparse 누락 launcher 결함) 범주에 해당. 연구 메소드 변경 없음. 학습/평가 알고리즘 변경 없음.

1. `scripts/10_run_lr_real_eval.py` — `_build_agent_dispatch_table`에 `RealNoGateAblation`, `NoComputeGateAblation` 등록. import 추가. 기존 agent 동작 보존.
2. `scripts/risk_hunt/run_abl001_retrain.py`, `run_abl003_retrain.py` — `--output-dir` 명시 + 학습 후 `checkpoint_ep*.pt` → `checkpoint_best.pt` promote 단계 추가. eval에도 `--out-dir` 명시.
3. `scripts/02_train_text_smoke.py` — `--seed`(train_cfg.seed override), `--checkpoint-dir`(--output-dir alias) argparse 추가. seed override 시 임시 yaml로 저장 후 `run_smoke_train`에 전달. `train_text.py` 핵심 변경 없음.
4. `scripts/risk_hunt/run_multiseed_training.py` — 학습 종료 후 `checkpoint_best.pt` promote 단계 추가.

---

## 4. Loop별 결과 표

### 4.1 Loop-01 proxy OFF eval

| Metric | proxy-ON | proxy-OFF |
|---|---|---|
| C3 F1 | **0.581** | **0.000** |
| C3 Precision | 0.493 | 0.000 |
| C3 Recall | 0.706 | 0.000 |
| C6 PPC | 0.193 | 0.193 |
| Mean planner F_t | +0.098 | **−0.464** |
| Steps with F_t > τ_f | 146/284 | **0/284** |
| Predicted-wrong count | 146 | 0 |

→ **Verdict: REJECT** (학습된 falsification signal 부재).

### 4.2 Loop-06 fair compute matching

| Agent | C3 F1 | C6 PPC | planning_calls | rollout_steps | ratio vs FRCG-LR |
|---|---|---|---|---|---|
| FRCG-LR | 0.581 | **0.1926** | 0 (gate never opens) | 0 | 1.00× |
| ABL-036b real-no-gate | 0.581 | **0.0963** | 284 | 0 | **2.00×** |
| ABL-036 heuristic | 0.000 | **0.0130** | 284 | 2840 | **14.81×** |

→ **Verdict: MODIFY** (advantage 살아있으나 14.9× → 2.0×로 축소). wall_clock denominator 회로는 P1 follow-up.

### 4.3 Loop-03 ABL-001/003 faithful retrain

| Variant | C3 F1 | C6 PPC | C2 regime_split |
|---|---|---|---|
| FRCG-LR reference (full loss) | 0.5391 | 0.2160 | **0.0** |
| ABL-001 no-regime (l_regime=0) | 0.5575 | 0.2160 | **0.0** |
| ABL-003 merged regime/grammar | 0.5391 | 0.2160 | **0.0** |

→ **Verdict: REJECT (with caveat)** — ABL이 reference를 무너뜨리지 못함. C2=0이 reference에서도 발생 → separability를 ablation으로 검증하는 게 현재 setup에서 불가능. 1 epoch 학습 길이 제약 caveat 존재.

### 4.4 Loop-02 5-seed multiseed

| Seed | C3 F1 | C3 Recall | C6 PPC |
|---|---|---|---|
| 42 | 0.5806 | 0.7059 | 0.1926 |
| 123 | 0.4198 | 0.3333 | 0.1926 |
| 456 | 0.4762 | 0.4902 | 0.1926 |
| 789 | 0.5785 | 0.6863 | 0.1926 |
| 999 | 0.5806 | 0.7059 | 0.1926 |
| **mean ± std** | **0.527 ± 0.075** | 0.584 ± 0.167 | **0.193 ± 0.000** |

→ **Verdict: KEEP** (statistical validity 확보, std=0.075 > 0.01). 단 variance가 학습 신호의 variance가 아니라 휴리스틱 boundary 변동임을 보고해야 함.

---

## 5. STEP 9 결과와의 비교

| Metric | STEP 9 보고 | 본 실행 결과 | 변화 |
|---|---|---|---|
| C3 F1 (proxy-on) | 0.539 (n=5 deterministic) | 0.527 ± 0.075 (5 seeds) | mean 비슷, 분산 노출 |
| C3 F1 (proxy-off) | not measured | **0.000** | new evidence |
| C6 PPC ratio vs ABL-036 | **14.9×** | 14.81× (heuristic) / **2.00× (fair)** | 14.9×는 heuristic-bypass artifact |
| C2 regime_shift_f1 | not measured directly | 0.0 (reference and ablations) | learned regime 부재 확인 |
| std(C3 F1) | 0.000 (n=5 same seed) | 0.075 (n=5 independent seeds) | true variance 확보 |

---

## 6. Verdict 표

| Risk register entry | Verdict |
|---|---|
| RH-CORE-01 (proxy 의존) | **REJECT** (C3 = proxy artifact) |
| RH-FAI-01 (ABL-001/003 faithful retrain) | **REJECT with caveat** (no contrast) |
| RH-STAT-01 (multiseed validity) | **KEEP** (std=0.075) |
| RH-EVAL-02 (fair compute) | **MODIFY** (ratio 14.9×→2.0×) |
| RH-FORE-01 (foresight causal influence) | **NOT RUN** — Codex task 후보 |

---

## 7. BLOCKED / 미해결 항목

1. **`threshold_free_c3_auroc` metric output 누락** — config에 등록됐지만 metrics.json에 노출되지 않음. Loop-01/03/06/02 모두 동일. P1 follow-up: `_build_metrics_with_blocked_markers` 등 출력 직렬화 회로 보강 필요.
2. **`fair_ppc` metric output 누락** — config의 `fair_ppc` 항목이 metrics.json에 보이지 않음. wall_clock_seconds도 per_step JSONL에 미기록 → fair_ppc 함수가 fallback으로 self-report를 쓰는 듯. Loop-06의 2.00× ratio는 wall-clock 검증 미완.
3. **`regime_shift_f1`이 reference에서도 0.0** — model이 regime을 학습하지 못하는 근본 문제. v0.5 데이터/loss/learning rate 재설계 필요.
4. **`C5_calibration_status: DEGENERATE_PREDICTOR`** — Loop-01과 ABL-001 retrain에서 발생. C5 calibration claim 사용 불가 상태.
5. **Loop-04 (foresight causal divergence_rate) 미수행** — frcg_agent.py act()에 rollout_off_action 분기, eval_runner의 step_results에 `action_changed_by_rollout` 기록, `scripts/risk_hunt/compute_foresight_causal.py` 구현이 모두 필요. Codex task 후보.
6. **1 epoch 학습 한계** — Loop-02/03의 모든 retrain이 1 epoch (1000-2000 steps)로 끝남. full 10 epoch 학습에서 결과 변화 가능성 존재 (현재 evidence로는 proxy 의존성이 지배할 가능성이 높음).

---

## 8. 새로 발견된 risk

1. **`FRCG-LR.planning_calls_total = 0`** — 50 episodes 동안 gate가 단 한 번도 열리지 않음. 그런데 self-report PPC는 0.1926. PPC 분모 정의가 self-report planning_calls이라면, FRCG-LR의 분모는 ε이고 ABL-036b의 분모는 284 → 14× 차이는 사실상 `progress/ε` vs `progress/284`의 산물. 이건 metric 자체의 의미가 모호함을 시사. **새 risk: PPC denominator semantics 재정의 필요**.
2. **ABL-003 = FRCG-LR reference 정확히 일치** — 학습 시간이 짧아 두 model이 식별 불가능. v0.5에서 충분한 학습 후 재검증 필수.
3. **Codex Gatekeeper 우회 가능성** — 본 세션의 minimal patch는 Claude 직접 수정 (launcher script 4개). 작업이 5개 이상 파일 동시 수정에 근접 → 다음 단계에서 유사 작업은 Codex task로 분리하는 게 codex_orchestration_rules.md §Codex 호출 트리거에 부합.

---

## 9. 추가 Codex task 후보

| ID | 설명 | 우선순위 |
|---|---|---|
| TASK_proxy_metric_export | `eval_runner._build_metrics_with_blocked_markers` 보강 — `threshold_free_c3_auroc`, `fair_ppc`, `regime_shift_f1`을 metrics.json에 노출. per_step writer가 `wall_clock_seconds`를 dump하도록 수정. | **HIGH** |
| TASK_foresight_causal | `frcg_agent.py act()`에 rollout_off_action 분기 + `action_changed_by_rollout` 기록 + `compute_foresight_causal.py` 구현. Loop-04 실행. | HIGH |
| TASK_full_epoch_retrain | ABL-001/003/multiseed 모두 full 10 epoch (20000 steps) 학습 후 재측정. proxy 의존이 그대로일 가능성 검증. | MEDIUM |
| TASK_ppc_semantics_redesign | PPC denominator 정의를 wall_clock 기반으로 명확화. self-report 분모는 secondary로만 보고. C6 claim 재구성. | **HIGH** |
| TASK_falsification_head_redesign | F_t scorer가 no_state_change 이외 effect_type을 학습 신호로 사용하도록 재설계. proxy 제거 후에도 F1 > 0이 나오게. | **HIGH (paper-blocking)** |
| TASK_regime_separability_v0_5 | data v0.5 또는 loss 재가중으로 regime separability 학습이 가능하게 함. C2 claim 회복. | MEDIUM |

---

## 10. 최종 claim 판정

**`CLAIM_SHRINK_REQUIRED`**

근거:
- C3 falsification 학습 신호 주장은 dead (proxy artifact).
- C2 separability 주장은 현재 학습 setup에서 dead.
- C6 advantage는 살아있으나 14.9× → 2.0×로 축소되며 wall-clock 검증이 미완.
- Statistical validity는 회복됨.
- 데이터 leakage는 변동 없음 (`tests/test_forbidden_field_mirror_sync.py` 영향 없음).

`PIVOT_RECOMMENDED`까지 가지 않는 이유: C6의 ~2.0× fair advantage가 살아있고 statistical validity가 회복됐기 때문. 단 paper main claim의 narrative는 "C3 falsification works" → "proxy heuristic + model confidence가 결합된 systemic detector"로 재구성 필수.

---

## 11. 무엇이 살아났고 무엇이 죽었는가

**살아남은 것**:
- 5-seed statistical methodology (Loop-02)
- 코드 인프라 (eval runner, ablation registry, multiseed launcher 모두 패치 후 동작)
- C6 fair compute의 ~2.0× advantage (wall-clock 검증 전)
- `tests/test_forbidden_field_mirror_sync.py` GREEN — data contract 그대로

**죽은 것**:
- 학습된 C3 falsification signal (Loop-01 verdict)
- 14.9× C6 advantage 보고 (Loop-06 verdict — heuristic-bypass artifact)
- C2 regime separability claim (Loop-03 verdict — reference도 학습 못 함)
- "STEP 9에서 C3가 회복됐다"는 narrative

**아직 모호한 것**:
- Loop-04 foresight causal divergence_rate (미수행)
- 학습이 충분히 길어지면 (10 epochs) C3 학습 신호가 나타날지 (현재 1 epoch 결과로는 비관적)
- wall-clock 기준 fair PPC ratio가 self-report 2.0×와 어떻게 다른지 (per_step에 wall_clock 미기록)
- 데이터 자체에 sufficient signal이 있는지 (v0.4 dataset이 too easy 또는 too noisy인지 분석 필요)

---

## 12. 다음에 정확히 무엇을 해야 하는가

**즉시 (Codex task로 분리 후 실행)**:

1. `TASK_proxy_metric_export` — eval output에 `threshold_free_c3_auroc`, `fair_ppc`, `wall_clock_seconds`, `regime_shift_f1`이 노출되도록 수정 + tests. 이게 모든 후속 분석의 전제조건.
2. `TASK_foresight_causal` — Loop-04 실행에 필요한 모든 계산. compute_foresight_causal.py 작성. Loop-04 verdict 산출.
3. `TASK_ppc_semantics_redesign` — PPC denominator semantics 재정의 + Loop-06 wall-clock 재측정.

**Paper claim 단계 (위 follow-up 완료 후)**:

4. C3 main claim 재구성: "falsification detector = (a) effect_type heuristic + (b) model confidence" 정직 보고. proxy 의존도 명시.
5. C6 claim 재보고: "FRCG-LR achieves ~2× advantage over fair-compute baseline (n=50, test_id, self-report denominator; wall-clock verification pending)". 14× 표현 금지.
6. C2 claim 격하 또는 v0.5 후속에 의존: "regime separability is an open question for v0.5 architecture/dataset".
7. STEP 9 이전의 모든 C3 회복 narrative 검토 → proxy artifact임을 명시하는 limitation 섹션 작성.

**Architecture/training 후속 (v0.5)**:

8. `TASK_falsification_head_redesign` — proxy 없이 F_t > 0이 나오는 falsification head 구조. data balance / aux loss 검토.
9. `TASK_regime_separability_v0_5` — regime separability를 실제로 학습할 수 있는 data + loss.
10. Full-epoch retrain pipeline 구축 — 1 epoch 한계가 결과 신뢰성에 미치는 영향 제거.

---

## 13. Paper claim 어떻게 고쳐야 하는가

### 13.1 Abstract / Intro

- "FRCG-WM은 wrong-control-grammar persistence를 falsification-guided rewrite로 줄인다" 큰 줄거리는 유지.
- 단 main results 섹션의 specific number (14× advantage, F1=0.539)는 모두 재기재.

### 13.2 Claims & Metrics

| 기존 | 재구성 후 |
|---|---|
| C3: "FRCG-WM learns falsification F1=0.539" | "FRCG-LR achieves F1≈0.53 ± 0.08 on test_id with a hybrid (heuristic + model-confidence) detector. The model-only component contributes 0 detected falsifications at τ_f=0 (proxy-OFF ablation)." |
| C6: "FRCG-LR is 14.9× more compute-efficient than no-gate baseline" | "FRCG-LR achieves ~2.0× progress-per-compute advantage over a fair-compute no-gate baseline (ABL-036b, model-forward equal). The previously reported 14.9× comparison used a heuristic-bypass baseline and overstates the advantage." |
| C2: "FRCG-WM disentangles regime and control grammar" | "Regime separability (regime_shift_f1) is 0.0 in both reference and l_regime=0 ablation under the current training setup (1 epoch v0.4). This claim is deferred to v0.5." |
| Statistical | "Reported with n=5 independent training seeds, std(F1)=0.075." |

### 13.3 Limitations

명시적으로 다음을 적는다:
- Falsification signal의 휴리스틱 의존
- regime separability 학습 미달성
- 1 epoch 학습 한계
- self-report denominator vs wall-clock 미결 issue
- v0.4 dataset의 task 다양성 한계

### 13.4 Related work

- STEP 9에서 "C3 회복"으로 보고한 모든 paragraph 재작성 — 회복이 학습이 아닌 heuristic enabling이었음을 명시.

---

## 14. 결론

STEP 10 risk-hunt는 STEP 9 main claims 중 **두 개를 무너뜨리고 한 개를 축소**시켰다.
이는 paper claim narrative의 본질적 재구성을 요구한다.
다만 데이터/코드 인프라/통계 방법론은 모두 살아있으며, 발견된 risk는 모두 v0.5 후속에서 실제로 fix 가능한 형태로 정리되었다.

**Final verdict**: `CLAIM_SHRINK_REQUIRED` + 6개 follow-up Codex task 후보 + paper narrative rewrite required before paper-main 진입.

end.
