# FGLC Closed-Loop Experiment Repair Planner (PLAN ONLY, 2026-05-23)

> **Status**: PLAN ONLY. 이 문서는 다음 execute 단계의 입력이다. 코드/문서 수정/sentinel 생성 금지.
> **Branch**: memory-redesign-2026-05-16
> **Scope**: state-only ManiSkill smoke. RGB-D / DROID / BridgeData / full baseline grid는 모두 DEFERRED.

---

## Context — 왜 이 plan이 필요한가

현재 FGLC repo 구조는 **fail-stop 머신**이다. ROADMAP/idea/configs/scripts 전체에서 `repair / closed_loop / ledger / config_hash / 4060 / 8GB / fail_stop` 매치가 사실상 0건이다. phase gate가 FAIL이면 "stop and report blocker"로 종료되고, 다음 시도를 위한 자동 진단·수정 후보 생성·재실험·비교 회로가 없다. 또한 ROADMAP은 A100 ~55일 풀 로드맵을 가정하며, 사용자 머신(RTX 4060 8GB)에서 즉시 돌릴 수 있는 smoke 경로는 한 곳에도 명시되지 않았다 (`4060` / `8GB` / `VRAM` 키워드 0건).

목표는 다음을 추가하는 것이다:
1. **failure cause taxonomy**(20개 enum-id) — 비공식 prose(`23_FAILURE_MODES.md` + `19_RISKS_AND_BLOCKERS.md`)를 형식화.
2. **metric → diagnosis → repair candidate 매핑 테이블** — 4축 metric 각각의 gate 미달 시 자동 점화될 cause 후보 + fix candidate 정의.
3. **experiment ledger schema** — `outputs/repair/{loop_id}/iter_{N}/` 누적 ledger와 before/after metric diff, accept/reject 규칙.
4. **4060 8GB smoke budget** — K/d/h_dim/horizon/batch_size/episode 후보 범위 + per-iter ≤ N분, total ≤ M시간, max-try, OOM fallback.
5. **closed-loop orchestrator 설계** — main Claude가 read-only 진단 + Codex TASK enqueue 또는 manual config patch로 다음 try 실행 → 비교 → ledger update → 종료 조건 충족 시까지 반복.

산출물 자체는 다음 execute 단계에서 만든다 (`docs/EXPERIMENT_REPAIR_LOOP_PLAN.md` 등 4개). 이 plan은 **그 산출물 4개의 명세서 + 단계별 실행 계획**이다.

---

## A. 현재 구조 감사 요약

| 카테고리 | 상태 | 핵심 인용 |
|---|---|---|
| Phase gate 정의 | sentinel `outputs/phase_gates/R<N>.passed` + 자연어 체크리스트 | `docs/ROADMAP/00_ROADMAP_OVERVIEW.md:53-63` |
| 4축 metric 정의 | NLL / AUROC / nec-suf / return — 각각 R3/R4/R6/R7 gate에 1:1 | `docs/idea/21_METRICS.md` |
| FAIL 처리 정책 | "stop and report blocker" 6+ 군데, closed-loop은 0건 | `ROADMAP/03/L42`, `ROADMAP/07/L40`, `ROADMAP/10/L17-22`, `ROADMAP/19/L27`, `idea/23/L39`, `AGENTS.md:L156` |
| 유일한 retry-with-fix 규칙 | "ECE > 0.2이면 L_cal 페널티 추가 및 재학습" 1줄 | `ROADMAP/05_PHASE_R4/L38-39` |
| 유일한 backward jump | "Stage 1 OOD NLL ≈ ID NLL이면 데이터셋 설계로 되돌아가라" | `docs/idea/12_TRAINING_STAGES.md:67-68` |
| failure cause taxonomy (enum) | 부재 (SCREAMING_SNAKE_CASE 0건) | grep 결과 |
| failure mode prose | 8개 (`23_FAILURE_MODES.md` 5+Reviewer-2 3) + R-1~R-14 (`19_RISKS_AND_BLOCKERS.md`) | 동 파일들 |
| experiment ledger | 부재 — `outputs/README.md:11`에 manifest 작성 규약 1줄, `config_hash` 0건 | 동 |
| 4060/8GB 명시 | 0건 (`4060/8GB/VRAM/smoke_budget/OOM_fallback/wall_clock` 모두 0) | grep 결과 |
| `src/fglc/` 구현 상태 | `schemas/visibility.py` + `__init__.py` + `py.typed`만 — 11+ 모듈 부재 | `Glob src/fglc/**/*` |
| `configs/` 디렉터리 | **자체 부재** — frcgw 시절 configs는 `.lifecycle_trash/` 안 | 동 |
| `scripts/fglc/*` entrypoint | 부재 (단, `phase_gate_guard.ps1:24-35`에 11개 경로 예약) | 동 |
| `outputs/phase_gates/` | `R0.passed` 1개만 | 동 |
| Codex orchestration 골격 | 살아있음 (`run_codex_task.ps1` 6-mode + TASK template + RESULT.md 8-section) | `.agent_tasks/`, `scripts/run_codex_task.ps1` |
| `paper_context_ref/` | **부재 (lifecycle_trash 내부에만 존재)** — 사용자가 지정한 1번 파일 활성 경로 없음 | `.lifecycle_trash/2026-05-22_frcg-to-fglc-pivot/paper_context_ref/...` |
| sentinel 규약 정합성 | ROADMAP은 `R<N>.passed`, `lifecycle_audit_v2.py:183` + `frcgw-phase-gate/SKILL.md:50`은 여전히 `P<N>.passed` 잔재 | 동 |

---

## B. fail-stop 구조가 있는지 — 판정

**판정: 현재 repo는 사실상 fail-stop 머신이다.**

근거:
1. ROADMAP의 모든 phase gate가 "PASS면 sentinel 생성, FAIL이면 stop/abort"의 2분기 구조. closed-loop을 시사하는 표현 0건.
2. `AGENTS.md:156` (Codex 정책)이 **"After the single commit, stop completely. Do not start the next task in the queue."**를 명시 — closed-loop을 정책 수준에서 **금지**한다. closed-loop은 Codex가 아니라 **main Claude + repair-planner**가 enqueue하는 방식으로만 정당화 가능.
3. `.claude/hooks/phase_gate_guard.ps1`은 sentinel 부재 시 entrypoint를 `exit 1`로 BLOCK. 자동 fix candidate 생성·enqueue 로직 0건.
4. `.claude/commands/frcgw-phase-check.md:80-87`이 "fake metric으로 PASS 마크 불가" / "실패 pytest 상태에서 PASS 불가"를 hard rule로 두지만, FAIL을 다음 iteration의 입력으로 변환하는 규칙은 없음.
5. R4의 "ECE > 0.2이면 L_cal 페널티 추가 및 재학습" 한 줄이 closed-loop의 유일한 흔적. 8개 phase × 4축 metric 매트릭스 중 1칸만 채워져 있음.

→ closed-loop repair planner는 기존 sentinel/gate/Codex 정책을 **깨지 않고 그 위에 얹는 추가 레이어**로 설계한다.

---

## C. 부족한 자동화 요소

| # | 부재 요소 | 영향 |
|---|---|---|
| C1 | enum-id 형식 failure taxonomy | 진단을 코드로 표현 불가 — 모든 진단이 사람의 prose 해석에 의존 |
| C2 | metric → cause 점화 규칙 | "AUROC 0.6이면 어떤 cause id가 후보인가?" 자동 판정 불가 |
| C3 | cause → repair candidate 매핑 | "BETA_GATE_COLLAPSE면 어떤 hyperparam patch가 후보인가?" 매핑 부재 |
| C4 | repair candidate ranking (cost/risk/expected signal) | 4060 환경에서 어떤 후보가 가장 싸고 빠른지 결정 불가 |
| C5 | experiment ledger schema | 누적 비교 불가, before/after metric diff 없음 |
| C6 | config_hash + git_sha 같이 묶는 run_id 발급기 | 재현성/추적 깨짐 |
| C7 | 4060 8GB smoke budget tier | OOM 위험 회피 + max wall-clock/max-try cap 부재 |
| C8 | accept/reject/inconclusive 결정 규칙 | "이전보다 좋아졌나?"를 자동 판정 불가 |
| C9 | closed-loop stop condition | budget 초과/target 도달/max iter 미정 — 무한루프 위험 |
| C10 | repair TASK 자동 enqueue | `.agent_tasks/codex_queue/`에 manual 작성만 — 자동화 부재 |
| C11 | sentinel 규약 정합성(R*.passed vs P*.passed 잔재) | repair planner가 sentinel을 읽으면 잘못된 분기 |
| C12 | DEFER 표시 — RGB-D/DROID/Bridge/full baseline grid | 4060에서 무엇을 안 돌리는지 명문화 부재 |

---

## D. 새 closed-loop repair harness 설계

### D.1 11단계 루프 (사용자 요구 명세 그대로)

```
1. Run experiment           — main Claude가 `python -m fglc.scripts.<entry>` 또는 Codex TASK enqueue
2. Collect metrics          — outputs/runs/{run_id}/metrics.json 작성, 4축 metric 누적
3. Detect failed metric     — gate threshold(ROADMAP 각 phase 정의)와 비교
4. Diagnose failure         — taxonomy 점화 규칙 (D.2)에 따라 cause-id 후보 집합 산출
5. Generate repair candidates — cause→fix mapping (D.3)에서 patch 후보 N개 산출
6. Rank candidates          — cost(분) × risk(0..1) × expected_signal(0..1) ⇒ score
7. Run cheapest smoke retest — top-1 candidate를 4060 budget 안에서 실행
8. Compare vs previous run  — outputs/repair/{loop_id}/iter_{N}/compare.json
9. Accept/reject/inconclusive — D.4 결정 규칙
10. Update experiment ledger — outputs/repair/{loop_id}/ledger.jsonl append
11. Continue until stop rule — D.5 (max_iter / wall_clock / target reach)
```

### D.2 Failure cause taxonomy (enum-id 20개)

| ID | 의미 | 1차 detection signal | source MD |
|---|---|---|---|
| DATA_TOO_SMALL | episode 수 부족, NLL 분산 큼 | NLL std/mean > 0.3 | `idea/18_DATA_BENCHMARKS.md` |
| DATA_BAD_SPLIT | ID/OOD overlap 또는 OOD가 ID와 동일 분포 | `OOD_NLL ≈ ID_NLL ± 0.05 nat` | `ROADMAP/03_PHASE_R2/L42` |
| OOD_TOO_HARD | OOD가 너무 극단 → 모델이 전혀 일반화 못 함 | `OOD_NLL − ID_NLL > 2.0 nat` | `idea/18` |
| OOD_TOO_EASY | OOD shift가 ID와 거의 같음 | `OOD_NLL − ID_NLL < 0.05 nat` | `idea/12_TRAINING_STAGES.md:67-68` |
| MODEL_UNDERCAPACITY | train loss 안 떨어짐 | `train_NLL > val_NLL` 정체 | `idea/23/실패 1 역` |
| MODEL_OVERCAPACITY | train↓ val↑ 발산 | val gap > 0.3 nat | 동 |
| LATENT_GROUP_TOO_SMALL | K 부족 → 표현 못 함 | grouped variance < 5% | `idea/03_LATENT_DECOMPOSITION.md` (UNKNOWN — Explore 미확인) |
| LATENT_DIM_TOO_SMALL | d 부족 | reconstruction error 상한선 | 동 |
| HORIZON_TOO_SHORT | 학습 horizon으로 OOD 신호 못 잡음 | k-step NLL 평탄 | `idea/04_BASE_WORLD_MODEL.md` |
| HORIZON_TOO_LONG | 누적 오차 폭주 | k-step NLL exponential | 동 |
| LOSS_IMBALANCE | objective_weights 한쪽 폭주 | per-loss component log 발산 | `idea/10_LOSS_DESIGN.md` |
| SIGMA_CALIBRATION_FAILURE | σ_t > 2× empirical std | ECE > 0.2 | `idea/23/L39` + `ROADMAP/05_PHASE_R4/L38-39` |
| BETA_GATE_COLLAPSE | β_t가 항상 0 또는 항상 1 | `mean(β) < 0.05` or `> 0.95` | `idea/23/실패 5의 변형` |
| ATTENTION_COLLAPSE | α가 한 group에 집중 또는 uniform | entropy < 0.1 or > 0.95×log K | `idea/23/실패 2` |
| CORRECTION_TOO_WEAK | δ 크기 ≈ 0 | `mean(||δ||) < 0.01` | `idea/23/실패 1 역` |
| CORRECTION_TOO_LARGE | δ가 δ_max 자주 hit | `||δ|| ≥ 0.9 δ_max` 비율 > 30% | `idea/23/실패 1` |
| PLANNER_BUDGET_TOO_LOW | rollout 개수 부족 | return 분산 큼 | `idea/11_PLANNING_THEORY.md` |
| EVAL_NOISE_HIGH | seed 간 분산 큼 | seed-CI > effect 자체 | `idea/21_METRICS.md` |
| BASELINE_MISMATCH | baseline 코드가 spec과 다름 | baseline NLL이 ID에서도 비정상 | `idea/19_BASELINES.md` |
| IMPLEMENTATION_BUG_SUSPECTED | 위 어떤 카테고리에도 안 맞음 | catch-all | — |

### D.3 metric → diagnosis → repair candidate 매핑 (사용자 명세 그대로)

| 관측 | 점화될 cause 후보 (우선순위 순) | repair candidate (cheapest first) |
|---|---|---|
| ID NLL이 높다 | MODEL_UNDERCAPACITY, DATA_TOO_SMALL, HORIZON_TOO_SHORT, LOSS_IMBALANCE | `h_dim 128→256`, `episode ×2`, `train horizon 8→16`, `objective_weights 재정렬` |
| OOD AUROC가 낮다 | SIGMA_CALIBRATION_FAILURE, BETA_GATE_COLLAPSE, OOD_TOO_EASY, DATA_BAD_SPLIT | `L_cal 추가`, `β_t reparam`, `OOD shift 강화`, `split 재생성` |
| corrected NLL > uncorrected NLL | CORRECTION_TOO_LARGE, ATTENTION_COLLAPSE, LOSS_IMBALANCE | `δ_max 0.25→0.1`, `entmax/sparsemax 도입`, `corrected_loss_weight ↓`, `base WM freeze` |
| attention entropy 너무 높음 | ATTENTION_COLLAPSE(uniform) | `entmax-alpha 1.5`, `top-k mask k=2`, `sparsity penalty 추가` |
| correction norm ≈ 0 | CORRECTION_TOO_WEAK, BETA_GATE_COLLAPSE | `δ head init scale ↑`, `corrected loss weight ↑`, `β prior scale 재설정` |
| correction norm 너무 큼 | CORRECTION_TOO_LARGE | `δ_max ↓`, `L_corr_size ↑`, `base WM freeze` |
| planner return 개선 없음 | PLANNER_BUDGET_TOO_LOW, HORIZON_TOO_LONG, IMPLEMENTATION_BUG_SUSPECTED | `n_candidate ↑`, `planning horizon 5→3`, `reward/value head 재학습`, `rollout error 재측정` |

### D.4 accept/reject/inconclusive 결정 규칙

이전 run vs 새 run, 같은 split에서:
- **accept** — primary metric Δ ≥ ε_accept(기본 0.05 nat / 0.05 AUROC / 0.05 return) **그리고** secondary metric 어느 것도 Δ ≤ -ε_secondary(기본 0.10) 아님.
- **reject** — primary metric Δ ≤ ε_reject(기본 0) **또는** 어떤 secondary metric에서 Δ ≤ -ε_secondary.
- **inconclusive** — 그 외 (seed CI 안에 들어감) → ledger에 `inconclusive`로 기록하고 다음 후보로 진행.

### D.5 stop 조건

다음 중 하나가 충족되면 loop 종료:
- `max_iter` 도달 (기본 5)
- `wall_clock_total` 초과 (기본 4시간)
- `target_metric_reached` (해당 phase ROADMAP gate threshold)
- `consecutive_inconclusive ≥ 3` (signal 없음)
- 어떤 hook이 BLOCKED 반환 (data leakage / forbidden field / sentinel 위반)

---

## E. 4060 8GB smoke 실험 루프

### E.1 hyperparam 후보 범위 (state-only ManiSkill PickCube 1태스크)

| param | 후보 | OOM 안전 추정 (8GB) |
|---|---|---|
| K (latent group) | 4, 6, 8 | 6 권장 |
| d (latent dim) | 16, 32 | 32 권장 |
| h_dim | 128, 256 | 128 권장 시작 |
| train horizon | 8, 16 | 8 권장 시작 |
| planning horizon | 3, 5 | 3 권장 시작 |
| batch size | 8, 16, 32 | 16 권장 시작 |
| episode 수 | 200, 500, 1000 | 200 smoke / 500 standard |
| seed | 42, 123, 456 | smoke는 1 seed로 시작 |

곱 추정: `batch(16) × T(8) × K(6) × d(32) = 24576 float32 ≈ 100KB/sample` — 8GB 한계 안 들어옴(여유 ≈ 80×). RGB-D + ViT encoder는 명시적으로 **금지**.

### E.2 per-run budget cap

| 항목 | 값 |
|---|---|
| per-iter wall-clock | ≤ 30분 (smoke), ≤ 60분 (standard) |
| total wall-clock | ≤ 4시간 |
| max-iter | 5 |
| OOM fallback | batch size 절반, K 한 단계 낮춤, T 한 단계 낮춤 (순서대로) |
| early stop | NLL 변동률 < 0.5% / 100 step 이하 |
| GPU memory cap | `torch.cuda.set_per_process_memory_fraction(0.85)` |

### E.3 DEFERRED 명시 (4060 환경 한정)

| Phase | 이유 |
|---|---|
| R8 (ASAP/I3G) | CIRCA+IVI 먼저 (`ROADMAP/19/R-13`) |
| R10 의 DreamerV3/HiP-RSSM/PLSM/ReDRAW/AdaWM | 핵심 비교는 TD-MPC2 + 오라클 + BASE-COMP-04만 (4060에서 5개 baseline 동시 학습 불가) |
| R11 (RGB-D) | `ROADMAP/12_PHASE_R11/L24` "state-only 충분하면 연기" |
| R12 (DROID/BridgeData) | `ROADMAP/19/R-4` "Phase 1 state-only가 주요 결과 충분" + DROID ~100GB 불가 |
| R13 (5-seed deep nec/suf) | R6의 basic nec/suf만 유지 |

---

## F. 수정/생성해야 할 파일 목록

### F.1 신규 문서 (산출물 4종)

| 경로 | 목적 | 핵심 내용 |
|---|---|---|
| `docs/EXPERIMENT_REPAIR_LOOP_PLAN.md` | closed-loop 마스터 plan | A~E + sample iteration walk-through |
| `docs/EXPERIMENT_LEDGER_SCHEMA.md` | ledger JSON schema 명세 | F.3 schema 정의 |
| `docs/ROADMAP/4060_SMOKE_REPAIR_PATH.md` | 축소 로드맵 | A100 표 vs 4060 표 대비 + phase gate "smoke" 변형 정의 |
| `docs/idea/FGLC_FAILURE_TAXONOMY.md` (신규) | enum-id 20개 taxonomy 정형화 | D.2 표 + 각 cause의 source MD 인용 |

### F.2 신규 코드/config (PLAN ONLY, 본 plan에서는 명세만)

| 경로 | 목적 |
|---|---|
| `configs/fglc/smoke_4060.yaml` | E.1 hyperparam 후보 grid + per-iter budget |
| `configs/fglc/base.yaml` | K/d/h_dim/horizon SSoT (이후 phase 공통) |
| `src/fglc/repair/__init__.py` | closed-loop 모듈 진입 |
| `src/fglc/repair/taxonomy.py` | D.2 enum-id (Python Enum) + detection signal threshold |
| `src/fglc/repair/diagnose.py` | metrics.json → 점화될 cause-id 집합 산출 |
| `src/fglc/repair/candidates.py` | cause-id → patch dict 후보 산출 |
| `src/fglc/repair/ranker.py` | (cost, risk, expected_signal) → score |
| `src/fglc/repair/compare.py` | before/after metric diff → accept/reject/inconclusive |
| `src/fglc/repair/ledger.py` | ledger.jsonl append + run_manifest 작성 |
| `src/fglc/repair/orchestrator.py` | 11단계 loop main; stop 조건 check |
| `scripts/fglc/repair_loop.py` | CLI entrypoint: `python scripts/fglc/repair_loop.py --phase R3 --config configs/fglc/smoke_4060.yaml` |
| `tests/test_fglc_repair_taxonomy.py` | enum-id 개수 = 20, 모든 source MD 존재, threshold sanity |
| `tests/test_fglc_repair_compare.py` | accept/reject/inconclusive 결정 단위 테스트 |
| `tests/test_fglc_repair_ledger.py` | ledger schema round-trip |

### F.3 ledger schema (`outputs/repair/{loop_id}/ledger.jsonl` 1 line = 1 iter)

```json
{
  "loop_id": "loop_2026-05-23T15-00-00",
  "iter": 0,
  "run_id": "r3_smoke_seed42_K6_d32_h128",
  "git_sha": "<short>",
  "config_hash": "<sha256 of resolved config>",
  "config_path": "configs/fglc/smoke_4060.yaml",
  "split": "PickCube/id",
  "phase": "R3",
  "metrics_before": {"id_nll_1step": 0.42, "ood_mass_nll_1step": 0.51, ...},
  "metrics_after":  {"id_nll_1step": 0.28, "ood_mass_nll_1step": 0.55, ...},
  "deltas":        {"id_nll_1step": -0.14, ...},
  "failed_metric": "id_nll_1step",
  "diagnosed_cause": ["MODEL_UNDERCAPACITY", "HORIZON_TOO_SHORT"],
  "candidate_chosen": {"id": "C-014", "patch": {"h_dim": 256, "train_horizon": 16}},
  "candidate_cost_minutes": 22,
  "candidate_risk": 0.2,
  "candidate_expected_signal": 0.6,
  "result": "accept",
  "wall_clock_minutes": 24,
  "vram_peak_mib": 5230,
  "oom_fallbacks_applied": [],
  "stop_condition_hit": null,
  "next_action": "proceed to R4 smoke",
  "notes": "..."
}
```

### F.4 수정 대상 (PLAN ONLY)

| 경로 | 변경 사유 |
|---|---|
| `outputs/README.md` | run_manifest 1줄 규약을 ledger schema 명세로 확장 ref |
| `.claude/hooks/phase_gate_guard.ps1` | smoke variant entrypoint(`scripts/fglc/repair_loop.py`) 허용 — sentinel 부재 시에도 read-only 진단은 허용 |
| `docs/ROADMAP/00_ROADMAP_OVERVIEW.md` | 4060 smoke path link 추가 (한 줄) |
| `docs/idea/19_RISKS_AND_BLOCKERS.md` | R-15 추가: "closed-loop 무한루프 위험 → max_iter/wall_clock cap" |

**불변 파일은 건드리지 않음**: `src/fglc/schemas/visibility.py`, `docs/idea/18_DATA_BENCHMARKS.md`, `docs/idea/19_BASELINES.md`, `docs/idea/20_ABLATIONS.md`, `.claude/settings.json`, `scripts/run_codex_task.ps1`. 사용자 명시 승인 없이 절대 수정하지 않음.

---

## G. 단계별 실행 계획 (verify 조건 포함)

```
Step 1. taxonomy 정형화
  - 작성: docs/idea/FGLC_FAILURE_TAXONOMY.md (D.2 표 + source MD 인용)
  - verify: 20개 enum-id 전부 존재, 각 항목에 detection threshold + source MD 인용 1개 이상

Step 2. ledger schema 문서
  - 작성: docs/EXPERIMENT_LEDGER_SCHEMA.md (F.3 JSON schema)
  - verify: schema 키 = run_id/git_sha/config_hash/metrics_before/metrics_after/deltas/failed_metric/diagnosed_cause/candidate_chosen/result/stop_condition_hit/next_action 모두 포함

Step 3. 4060 smoke path 문서
  - 작성: docs/ROADMAP/4060_SMOKE_REPAIR_PATH.md (E.1+E.2+E.3 + DEFER 표)
  - verify: A100 표 vs 4060 표 직접 비교, RGB-D/DROID/Bridge/full baseline grid DEFERRED 명시

Step 4. master plan 문서
  - 작성: docs/EXPERIMENT_REPAIR_LOOP_PLAN.md (A~E 통합 + sample walk-through)
  - verify: 11단계 loop 명시, sample iteration이 ledger schema에 1:1 대응

Step 5. taxonomy 모듈 + 테스트 (코드)
  - Codex TASK (FILES_ALLOWED: src/fglc/repair/taxonomy.py, tests/test_fglc_repair_taxonomy.py)
  - REQUIRED_TESTS: pytest tests/test_fglc_repair_taxonomy.py -q
  - verify: 20개 Enum 존재, source MD 참조 docstring 존재, 모든 threshold int/float 타입

Step 6. compare/ledger 모듈 + 테스트 (코드)
  - Codex TASK (FILES_ALLOWED: src/fglc/repair/compare.py, ledger.py, tests/test_fglc_repair_*.py)
  - REQUIRED_TESTS: pytest tests/test_fglc_repair_compare.py tests/test_fglc_repair_ledger.py -q
  - verify: accept/reject/inconclusive 단위 테스트 통과, ledger.jsonl round-trip 통과

Step 7. diagnose/candidates/ranker 모듈 (코드)
  - Codex TASK
  - REQUIRED_TESTS: 각 모듈별 unit test
  - verify: D.3 매핑이 실제 dict로 표현, ranker 결정성 (동일 입력 → 동일 ordering)

Step 8. orchestrator 모듈 + smoke entrypoint (코드)
  - Codex TASK (FILES_ALLOWED: src/fglc/repair/orchestrator.py, scripts/fglc/repair_loop.py)
  - REQUIRED_TESTS: dry-run mode (no actual training, mock metrics)
  - verify: stop 조건 5개 전부 hit 가능, max_iter cap 동작

Step 9. R3 base WM smoke 1회 (사람 트리거)
  - 명령: python scripts/fglc/repair_loop.py --phase R3 --config configs/fglc/smoke_4060.yaml --dry-run
  - verify: ledger 1줄 생성, VRAM peak < 7000 MiB, wall-clock < 30분
  - 단, R3 모듈(encoder/dynamics/world model heads) 자체가 아직 부재 → Step 9는 R3 phase 모듈이 별도로 구현된 뒤에만 실행 가능 (BLOCKER 사전 공지)

Step 10. R3 smoke real run (사람 트리거)
  - --dry-run 제거. 실제 ManiSkill PickCube 200 episodes, K=6, d=32, h_dim=128, T=8, batch=16, seed=42
  - verify: ledger에 `accept` 또는 `inconclusive` 기록, 다음 iter candidate 자동 산출

각 step 종료 시 commit. sentinel R<N>.passed는 실제 gate threshold 충족이 metric artifact로 입증된 뒤에만 `/fglc-phase-check --pass R<N>`로 생성.
```

---

## H. BLOCKED / UNKNOWN

### H.1 BLOCKED (사용자 결정 필요)

| # | 항목 | 옵션 | 권장 |
|---|---|---|---|
| H1 | `paper_context_ref/00_CONTEXT_INDEX.md`가 `.lifecycle_trash/2026-05-22_frcg-to-fglc-pivot/paper_context_ref/paper_context_ref/00_CONTEXT_INDEX.md`로 archived됨. closed-loop planner의 context router를 어떻게? | (A) `.lifecycle_trash/` 안의 것을 일회성 read-only 참고만 하고 신규 router는 `docs/idea/00_OVERVIEW.md` + `docs/ROADMAP/00_ROADMAP_OVERVIEW.md`로 갈음 (권장) / (B) `paper_context_ref/` 활성 복원 / (C) trash 무시, ROADMAP만 사용 | A |
| H2 | `AGENTS.md:156`의 "stop completely. Do not start the next task in the queue" 정책과 closed-loop의 충돌. | (A) Codex는 단일 TASK만 수행, main Claude(또는 사람)가 manual로 다음 iter TASK enqueue — Codex 정책 보존 (권장) / (B) AGENTS.md 개정해서 repair-loop 예외 추가 | A |
| H3 | sentinel 규약 정합성 — ROADMAP은 `R<N>.passed`인데 `lifecycle_audit_v2.py:183` + `frcgw-phase-gate/SKILL.md:50`은 `P<N>.passed` 잔재. | (A) repair-planner는 `R<N>.passed`만 신뢰 + `P*.passed` 잔재는 별 task로 정리 (권장) / (B) 양쪽 모두 인식하는 호환 layer | A |
| H4 | Step 9 BLOCKER — `src/fglc/` R3 모듈(encoder/dynamics/world model heads)이 아직 부재. closed-loop을 R3 phase 모듈 구현 전에 만들어도 dry-run만 가능. | (A) closed-loop harness 먼저 + R3 모듈은 그 다음 별도 task (권장) / (B) R3 모듈 먼저 + closed-loop은 R3 PASS 후 | A |
| H5 | repair-loop 진행 중 새 OOD axis가 필요해질 수 있음 (예: action_gain). 4060 환경에서 어디까지 OOD axis 추가? | (A) smoke는 mass+friction 2개만, 나머지(latency/noise/action_gain)는 standard run에서 (권장) / (B) mass 1개만 | A |

### H.2 UNKNOWN (조사 필요)

| # | 항목 | 다음 단계 |
|---|---|---|
| U1 | `docs/idea/03_LATENT_DECOMPOSITION.md`의 K-group variance 정의(D.2 LATENT_GROUP_TOO_SMALL detection signal) — 실제 파일 미확인 | Step 1 작성 전 read |
| U2 | `docs/idea/11_PLANNING_THEORY.md`의 planner budget 단위 (n_candidate? n_sample × horizon?) — D.3에 영향 | Step 1 작성 전 read |
| U3 | `outputs/runs/{run_id}/run_manifest.json`의 정확한 필드 enum (현재는 `outputs/README.md` 1줄 요약만) | F.3 ledger와 정합성 맞추기 위해 Step 2 작성 전 sample manifest 1개 read |
| U4 | `phase_gate_guard.ps1`이 `scripts/fglc/repair_loop.py`를 어떻게 다룰지 — phase 미지정 entrypoint를 허용하는 분기 있는지 | Step 8 전 hook source 확인 |
| U5 | RTX 4060 8GB에서 K=6/d=32/h_dim=128/T=8/batch=16의 실측 VRAM — 추정 100KB/sample이지만 PyTorch overhead 포함 시 실제 측정 필요 | Step 9 dry-run 시 `torch.cuda.memory_summary()` |

---

## I. 다음 execute 단계에서 수행할 최소 작업

이 plan이 ExitPlanMode로 승인되면 **즉시 수행할 최소 단위 작업**:

1. **Step 1+2+3+4 문서 4종 작성** (코드 변경 없음, 사람이 review 가능한 markdown만)
   - `docs/idea/FGLC_FAILURE_TAXONOMY.md`
   - `docs/EXPERIMENT_LEDGER_SCHEMA.md`
   - `docs/ROADMAP/4060_SMOKE_REPAIR_PATH.md`
   - `docs/EXPERIMENT_REPAIR_LOOP_PLAN.md`
   - 단, **새 파일은 4개 모두 PLAN ONLY 모드 종료 후 사용자가 "Step 1~4 진행" 또는 동등한 명령을 주었을 때만** 작성.
2. **commit 단위**: 문서 4개 한 commit (`docs(repair): add closed-loop experiment repair planner v0`).
3. **이 단계에서 절대 안 함**:
   - Step 5+ 의 코드 변경 (src/fglc/repair/, scripts/fglc/, configs/fglc/, tests/)
   - phase gate sentinel `R*.passed` 생성
   - `outputs/repair/*` 디렉터리 생성
   - 실제 학습/평가 실행
   - Codex TASK enqueue
   - paper_context_ref 복원/삭제
   - AGENTS.md / hook / settings.json 수정

다음 단계 진입 트리거: 사용자가 명시적으로 "Step 1~4 작성 진행" 또는 "Step 5 Codex 위임" 같은 명령을 줄 때만.

---

## Verification (이 plan 자체의 검증 방법)

이 plan이 사용자 의도와 정합한지 확인하는 방법:

1. **A 섹션의 인용이 실제 파일 라인과 일치** — `Read docs/ROADMAP/05_PHASE_R4_FALSIFICATION_GATE.md` L38-39를 직접 확인.
2. **D.2 taxonomy의 20개 enum-id가 사용자 명세와 1:1 일치** — 사용자 원문 prompt에 적힌 20개 SCREAMING_SNAKE_CASE와 대조.
3. **D.3 매핑이 사용자 명세 7개 예시를 전부 커버** — 사용자가 적은 7개 "관측 → 의심 항목" 모두 매핑됨을 확인.
4. **E.1 hyperparam 범위가 사용자 명세와 일치** — K{4,6,8}, d{16,32}, h_dim{128,256}, train horizon{8,16}, planning horizon{3,5}, batch{8,16,32} 모두 포함.
5. **F.4의 불변 파일 목록이 CLAUDE.md "불변 보존" 섹션과 일치** — visibility.py / 18_DATA_BENCHMARKS / 19_BASELINES / 20_ABLATIONS / settings.json / run_codex_task.ps1.
6. **H.1 BLOCKED 5개가 ExitPlanMode 검토 시 사용자가 명시적으로 옵션 A/B 중 선택할 수 있는 형태** — 모든 항목에 옵션 명시 및 권장.
7. **I 섹션이 "PLAN ONLY 종료 후 첫 작업은 마크다운 4종 작성만"임을 명확히 함** — 코드/sentinel/실행 0건.

검증 실패 항목이 발견되면 plan을 본 파일에서만 수정하고 ExitPlanMode를 호출하지 않는다.
