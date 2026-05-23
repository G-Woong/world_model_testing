# EXPERIMENT_REPAIR_LOOP_PLAN — Closed-Loop 실험 Repair Harness 마스터 플랜

> **Branch**: memory-redesign-2026-05-16
> **Status**: v0 (2026-05-23) — 문서 4종 중 master plan (Step 4 산출물)
> **Scope**: state-only ManiSkill smoke. RGB-D / DROID / BridgeData / full baseline grid는 모두 DEFERRED.

---

## A. 왜 이 플랜이 필요한가

현재 FGLC repo는 **fail-stop 머신**이다:
- Phase gate FAIL → "stop and report blocker" 6+ 군데
- Closed-loop repair를 시사하는 코드/문서: 0건
- `R4`의 "ECE > 0.2이면 L_cal 페널티 추가 및 재학습" 1줄이 유일한 retry 힌트
- ROADMAP은 A100 ~55일을 가정 — RTX 4060 8GB smoke path: 0건 명시

**목표**: 기존 sentinel/gate/Codex 정책을 깨지 않고 그 위에 closed-loop repair harness를 얹는다.

### 현재 구조 핵심 감사 결과

| 항목 | 상태 |
|---|---|
| fail-stop 정책 | ROADMAP 8개 phase 전부 2분기(PASS/FAIL) 구조 |
| AGENTS.md:L156 | "stop completely. Do not start the next task in the queue" — Codex는 단일 TASK만 |
| retry-with-fix 유일 사례 | `R4`: ECE > 0.2이면 L_cal 재학습 1줄 |
| failure cause taxonomy (enum) | 부재 → `docs/idea/FGLC_FAILURE_TAXONOMY.md`에서 정형화 |
| experiment ledger | 부재 → `docs/EXPERIMENT_LEDGER_SCHEMA.md`에서 정의 |
| 4060/8GB smoke path | 부재 → `docs/ROADMAP/4060_SMOKE_REPAIR_PATH.md`에서 정의 |
| closed-loop orchestrator | 부재 → `src/fglc/repair/` (Step 5+ 이후 구현) |

---

## B. Fail-stop 구조 판정

**판정**: 현재 repo는 사실상 fail-stop 머신이다.

Closed-loop은 Codex가 아니라 **main Claude + repair-planner가 enqueue**하는 방식으로만 정당화 가능하다:
- Codex는 단일 TASK 수행 후 stop (AGENTS.md:156)
- Phase gate guard는 sentinel 부재 시 entrypoint를 exit 1로 BLOCK
- Main Claude가 진단 → patch 후보 생성 → Codex TASK enqueue 또는 manual config patch → 재실험 → 비교 → ledger update 루프를 구동

---

## C. 부족한 자동화 요소 (12개)

| # | 부재 요소 | 구현 위치 |
|---|---|---|
| C1 | enum-id 형식 failure taxonomy | `docs/idea/FGLC_FAILURE_TAXONOMY.md` + `src/fglc/repair/taxonomy.py` |
| C2 | metric → cause 점화 규칙 | `src/fglc/repair/diagnose.py` |
| C3 | cause → repair candidate 매핑 | `src/fglc/repair/candidates.py` |
| C4 | repair candidate ranking | `src/fglc/repair/ranker.py` |
| C5 | experiment ledger schema | `docs/EXPERIMENT_LEDGER_SCHEMA.md` + `src/fglc/repair/ledger.py` |
| C6 | config_hash + git_sha run_id 발급기 | `src/fglc/repair/ledger.py` |
| C7 | 4060 8GB smoke budget tier | `docs/ROADMAP/4060_SMOKE_REPAIR_PATH.md` + `configs/fglc/smoke_4060.yaml` |
| C8 | accept/reject/inconclusive 결정 규칙 | `src/fglc/repair/compare.py` |
| C9 | closed-loop stop condition | `src/fglc/repair/orchestrator.py` |
| C10 | repair TASK 자동 enqueue | `src/fglc/repair/orchestrator.py` (Codex TASK 생성 포함) |
| C11 | sentinel 규약 정합성 | repair-planner는 `R<N>.passed`만 신뢰 |
| C12 | DEFER 표시 | `docs/ROADMAP/4060_SMOKE_REPAIR_PATH.md` §DEFERRED |

---

## D. Closed-Loop Repair Harness 설계

### D.1 11단계 루프

```
1. Run experiment
   main Claude가 `python scripts/fglc/repair_loop.py --phase R<N> --config <path>`
   또는 Codex TASK를 `.agent_tasks/codex_queue/`에 enqueue

2. Collect metrics
   outputs/runs/{run_id}/metrics.json 작성
   4축 metric: ID NLL / OOD AUROC / nec-suf / return 누적

3. Detect failed metric
   metrics.json vs gate threshold (docs/ROADMAP/4060_SMOKE_REPAIR_PATH.md §gate) 비교

4. Diagnose failure
   taxonomy 점화 규칙 (D.2) → cause-id 후보 집합 산출
   (src/fglc/repair/diagnose.py)

5. Generate repair candidates
   cause → fix mapping (D.3) → patch 후보 N개 산출
   (src/fglc/repair/candidates.py)

6. Rank candidates
   (cost_minutes, risk, expected_signal) → composite score
   cheapest × lowest risk × highest signal 기준
   (src/fglc/repair/ranker.py)

7. Run cheapest smoke retest
   top-1 candidate를 4060 budget 안에서 실행
   (wall-clock ≤ 30분 smoke / ≤ 60분 standard)

8. Compare vs previous run
   outputs/repair/{loop_id}/iter_{N}/compare.json
   (src/fglc/repair/compare.py)

9. Accept/reject/inconclusive
   D.4 결정 규칙 → result 기록

10. Update experiment ledger
    outputs/repair/{loop_id}/ledger.jsonl append
    (src/fglc/repair/ledger.py)

11. Continue until stop rule
    D.5 stop 조건 확인 → 충족 시 loop 종료
```

### D.2 Failure Cause Taxonomy (요약)

20개 enum-id. 상세: `docs/idea/FGLC_FAILURE_TAXONOMY.md`

| 주요 ID | 의미 | 1차 detection signal |
|---|---|---|
| DATA_TOO_SMALL | episode 수 부족 | NLL_std/mean > 0.3 |
| DATA_BAD_SPLIT | ID/OOD overlap | `|OOD−ID NLL| < 0.05 nat` |
| OOD_TOO_HARD | OOD shift 극단 | `OOD−ID NLL > 2.0 nat` |
| OOD_TOO_EASY | OOD shift 무의미 | `OOD−ID NLL < 0.05 nat` |
| MODEL_UNDERCAPACITY | 용량 부족 | train_NLL ≥ val_NLL 정체 |
| MODEL_OVERCAPACITY | 과적합 | val−train gap > 0.3 nat |
| LATENT_GROUP_TOO_SMALL | K 부족, group collapse | inter-group cosine > 0.85 |
| LATENT_DIM_TOO_SMALL | d 부족 | reconstruction MSE > 1.5× baseline |
| HORIZON_TOO_SHORT | OOD 신호 못 잡음 | k-step NLL 기울기 < 0.01 |
| HORIZON_TOO_LONG | 누적 오차 폭주 | k-step NLL exponential |
| LOSS_IMBALANCE | objective 한쪽 폭주 | 1 component > 80% total loss |
| SIGMA_CALIBRATION_FAILURE | σ_t 과대추정 | ECE > 0.2 |
| BETA_GATE_COLLAPSE | β_t 이분화 | mean(β) < 0.05 or > 0.95 |
| ATTENTION_COLLAPSE | α uniform or 집중 | entropy < 0.1 or > 0.95×log(K) |
| CORRECTION_TOO_WEAK | δ ≈ 0 | mean(‖δ‖) < 0.01 |
| CORRECTION_TOO_LARGE | δ bounding 자주 hit | ‖δ‖ ≥ 0.9δ_max > 30% |
| PLANNER_BUDGET_TOO_LOW | rollout 부족 | return std > mean × 0.5 |
| EVAL_NOISE_HIGH | seed 분산 큼 | 95% CI > effect size |
| BASELINE_MISMATCH | baseline 코드 spec 불일치 | baseline NLL 비정상 |
| IMPLEMENTATION_BUG_SUSPECTED | 위 19개 해당 없음 | catch-all |

### D.3 Metric → Diagnosis → Repair Candidate 매핑

| 관측 | 점화 cause 후보 (우선순위) | repair candidate (cheapest first) |
|---|---|---|
| ID NLL 높음 | MODEL_UNDERCAPACITY, DATA_TOO_SMALL, HORIZON_TOO_SHORT, LOSS_IMBALANCE | h_dim 128→256, episode ×2, horizon 8→16, weights 재정렬 |
| OOD AUROC 낮음 | SIGMA_CALIBRATION_FAILURE, BETA_GATE_COLLAPSE, OOD_TOO_EASY, DATA_BAD_SPLIT | L_cal 추가, β reparam, OOD shift 강화, split 재생성 |
| corrected NLL > uncorrected NLL | CORRECTION_TOO_LARGE, ATTENTION_COLLAPSE, LOSS_IMBALANCE | δ_max 0.25→0.1, entmax/sparsemax 도입, corrected_loss_weight ↓, base WM freeze |
| attention entropy 과다 | ATTENTION_COLLAPSE(uniform) | entmax-alpha 1.5, top-k mask k=2, sparsity penalty 추가 |
| correction norm ≈ 0 | CORRECTION_TOO_WEAK, BETA_GATE_COLLAPSE | δ head init scale ↑, corrected loss weight ↑, β prior scale 재설정 |
| correction norm 과다 | CORRECTION_TOO_LARGE | δ_max ↓, L_corr_size ↑, base WM freeze |
| planner return 개선 없음 | PLANNER_BUDGET_TOO_LOW, HORIZON_TOO_LONG, IMPLEMENTATION_BUG_SUSPECTED | n_candidate ↑, horizon 5→3, reward/value head 재학습, rollout error 재측정 |

### D.4 Accept/Reject/Inconclusive 결정 규칙

```
primary_delta = metrics_after[failed_metric] − metrics_before[failed_metric]
  (NLL 계열: delta < 0 = 개선 / AUROC·return 계열: delta > 0 = 개선)

accept:
  |primary_delta| ≥ ε_accept(기본 0.05)
  AND 모든 secondary delta > −ε_secondary(기본 0.10)

reject:
  |primary_delta| ≤ ε_reject(기본 0.0)
  OR 어떤 secondary delta ≤ −ε_secondary

inconclusive:
  위 둘 다 아닌 경우
```

상세: `docs/EXPERIMENT_LEDGER_SCHEMA.md` §결정 규칙

### D.5 Stop 조건 (5개)

```
max_iter                   — iter 수 ≥ max_iter (기본 5)
wall_clock_total           — 누적 wall_clock ≥ 240분
target_metric_reached      — failed_metric이 gate threshold 충족
consecutive_inconclusive   — 연속 inconclusive ≥ 3
hook_blocked               — leakage hook 또는 phase_gate_guard가 BLOCK
```

---

## E. 4060 8GB Smoke 실험 예산

상세: `docs/ROADMAP/4060_SMOKE_REPAIR_PATH.md`

### 핵심 파라미터 (state-only PickCube)

- K: 4, 6 (권장 K=6)
- d: 16, 32 (권장 d=32)
- h_dim: 128, 256 (권장 128 시작)
- train_horizon: 8, 16 (권장 8 시작)
- batch_size: 8, 16, 32 (권장 16)
- n_episode: 200 (smoke), 500 (standard)

### Per-iter Budget

| 항목 | Smoke | Standard |
|---|---|---|
| wall-clock | ≤ 30분 | ≤ 60분 |
| total (loop) | ≤ 4시간 | ≤ 8시간 |
| max_iter | 5 | 5 |

---

## F. 산출물 목록

### F.1 문서 4종 (Step 1~4, 이번 commit)

| 파일 | 상태 |
|---|---|
| `docs/idea/FGLC_FAILURE_TAXONOMY.md` | ✅ 완료 |
| `docs/EXPERIMENT_LEDGER_SCHEMA.md` | ✅ 완료 |
| `docs/ROADMAP/4060_SMOKE_REPAIR_PATH.md` | ✅ 완료 |
| `docs/EXPERIMENT_REPAIR_LOOP_PLAN.md` | ✅ 완료 (본 파일) |

### F.2 코드 (Step 5~8, Codex TASK 예정)

| 경로 | 목적 |
|---|---|
| `configs/fglc/smoke_4060.yaml` | E 절 hyperparam grid + budget |
| `configs/fglc/base.yaml` | K/d/h_dim/horizon SSoT |
| `src/fglc/repair/taxonomy.py` | D.2 enum-id Python Enum |
| `src/fglc/repair/diagnose.py` | metrics.json → cause-id 집합 |
| `src/fglc/repair/candidates.py` | cause-id → patch dict |
| `src/fglc/repair/ranker.py` | (cost, risk, signal) → score |
| `src/fglc/repair/compare.py` | before/after diff → accept/reject |
| `src/fglc/repair/ledger.py` | ledger.jsonl append |
| `src/fglc/repair/orchestrator.py` | 11단계 loop main |
| `scripts/fglc/repair_loop.py` | CLI entrypoint |
| `tests/test_fglc_repair_taxonomy.py` | enum-id 20개, source MD 존재, threshold 타입 |
| `tests/test_fglc_repair_compare.py` | accept/reject/inconclusive 단위 테스트 |
| `tests/test_fglc_repair_ledger.py` | ledger schema round-trip |

---

## G. 단계별 실행 계획

```
Step 1. taxonomy 정형화
  - 완료: docs/idea/FGLC_FAILURE_TAXONOMY.md
  - verify: 20개 enum-id, 각 항목 detection threshold + source MD ≥1

Step 2. ledger schema 문서
  - 완료: docs/EXPERIMENT_LEDGER_SCHEMA.md
  - verify: REQUIRED_KEYS 17개 모두 포함

Step 3. 4060 smoke path 문서
  - 완료: docs/ROADMAP/4060_SMOKE_REPAIR_PATH.md
  - verify: A100 vs 4060 대비표, DEFERRED 명시

Step 4. master plan (본 파일)
  - 완료: docs/EXPERIMENT_REPAIR_LOOP_PLAN.md
  - verify: 11단계 loop, sample walk-through ledger와 1:1 대응

Step 5. taxonomy 모듈 + 테스트 [다음 Codex TASK]
  - FILES_ALLOWED: src/fglc/repair/taxonomy.py, tests/test_fglc_repair_taxonomy.py
  - REQUIRED_TESTS: pytest tests/test_fglc_repair_taxonomy.py -q

Step 6. compare/ledger 모듈 + 테스트 [다음 Codex TASK]
  - FILES_ALLOWED: src/fglc/repair/compare.py, ledger.py, tests/test_fglc_repair_*.py
  - REQUIRED_TESTS: pytest tests/test_fglc_repair_compare.py tests/test_fglc_repair_ledger.py -q

Step 7. diagnose/candidates/ranker 모듈 [다음 Codex TASK]

Step 8. orchestrator + smoke entrypoint [다음 Codex TASK]
  - dry-run mode 필수 (no actual training, mock metrics)

Step 9. R3 base WM smoke dry-run [사람 트리거]
  - 전제 조건: src/fglc/ R3 모듈 (encoder/dynamics/WM heads) 별도 구현 완료
  - BLOCKER: R3 모듈 미구현 상태 → dry-run만 가능

Step 10. R3 smoke real run [사람 트리거]
  - n_episode=200, K=6, d=32, h_dim=128, T=8, batch=16, seed=42
```

---

## H. Sample Iteration Walk-Through

(ledger schema `docs/EXPERIMENT_LEDGER_SCHEMA.md` §F.3과 1:1 대응)

```
loop_id: loop_2026-05-23T15-00-00
iter: 0
run_id: r3_smoke_seed42_K6_d32_h128
phase: R3
split: PickCube/id

metrics_before:
  id_nll_1step: null  (첫 iter — baseline 없음)

--- [Step 1: 실험 실행] ---
  python scripts/fglc/repair_loop.py --phase R3 --config configs/fglc/smoke_4060.yaml
  wall_clock: 24분, VRAM peak: 5230 MiB

metrics_after:
  id_nll_1step: 0.42

--- [Step 3: gate 비교] ---
  gate threshold: 0.35 nat (smoke 기준)
  FAIL: 0.42 > 0.35

--- [Step 4: 진단] ---
  diagnosed_cause: [MODEL_UNDERCAPACITY, HORIZON_TOO_SHORT]
  (train_NLL ≈ val_NLL 정체, k-step NLL 기울기 평탄)

--- [Step 5: 후보 생성] ---
  C-014: {h_dim: 256, train_horizon: 16} / cost=22분 / risk=0.2 / signal=0.6
  C-007: {n_episode: 500} / cost=45분 / risk=0.1 / signal=0.4

--- [Step 6: ranking] ---
  C-014 score=0.68, C-007 score=0.52 → top-1: C-014

--- [Step 7: 재실험] ---
  patch: h_dim 128→256, train_horizon 8→16, 나머지 동일
  wall_clock: 38분, VRAM peak: 6100 MiB

metrics_after (iter 1):
  id_nll_1step: 0.28

--- [Step 9: 결정] ---
  delta = -0.14 ≤ -ε_accept(-0.05) → accept
  no secondary regression → accept confirmed

--- [Step 10: ledger append] ---
  result: accept
  stop_condition_hit: null
  next_action: "proceed to iter 1 or R4 smoke if gate threshold met"

--- [gate check] ---
  0.28 ≤ 0.35 → gate PASS → next_action: "proceed to R4 smoke"
```

---

## I. BLOCKED / UNKNOWN 해소 현황

### H.1 BLOCKED (사용자 확인 — 권장 옵션 A 적용)

| # | 항목 | 선택 |
|---|---|---|
| H1 | paper_context_ref 경로 | A: `.lifecycle_trash/` read-only 참고, router = `docs/idea/00_OVERVIEW.md` |
| H2 | AGENTS.md:156 충돌 | A: Codex 단일 TASK, main Claude가 manual enqueue |
| H3 | sentinel 규약 정합성 | A: `R<N>.passed`만 신뢰, `P*.passed` 잔재는 별도 task |
| H4 | R3 모듈 미구현 | A: closed-loop harness 먼저, R3 모듈은 별도 task (Step 9 BLOCKER) |
| H5 | OOD axis 범위 | A: smoke는 mass+friction 2개, latency/noise/action_gain은 standard run |

### H.2 UNKNOWN 해소

| # | 항목 | 상태 |
|---|---|---|
| U1 | LATENT_GROUP_TOO_SMALL detection signal | ✅ inter-group cosine > 0.85 (03_LATENT_DECOMPOSITION.md:C8) |
| U2 | 플래너 budget 단위 | ✅ n_rollout × H, n_rollout=512 default (11_PLANNING_THEORY.md:C4) |
| U3 | run_manifest.json 필드 | ✅ config/seed/status (outputs/README.md) |
| U4 | repair_loop.py hook 처리 | ✅ phase_gate_guard.ps1 패턴 목록에 없음 → 자동 허용 |
| U5 | 4060 실측 VRAM | UNKNOWN — Step 9 dry-run 시 측정 필요 |

---

## 불변 파일 (수정 금지)

다음 파일은 이 플랜 및 하위 Step에서 **절대 수정하지 않는다**:

- `src/fglc/schemas/visibility.py`
- `docs/idea/18_DATA_BENCHMARKS.md`
- `docs/idea/19_BASELINES.md`
- `docs/idea/20_ABLATIONS.md`
- `.claude/settings.json`
- `scripts/run_codex_task.ps1`

---

## 참조 문서

| 문서 | 역할 |
|---|---|
| `docs/idea/FGLC_FAILURE_TAXONOMY.md` | enum-id 20개 taxonomy 정형화 |
| `docs/EXPERIMENT_LEDGER_SCHEMA.md` | ledger JSON schema 명세 |
| `docs/ROADMAP/4060_SMOKE_REPAIR_PATH.md` | 4060 예산·DEFER 표 |
| `docs/idea/00_OVERVIEW.md` | FGLC context router |
| `docs/ROADMAP/00_ROADMAP_OVERVIEW.md` | phase gate 정책 |
| `CLAUDE.md §머신 환경` | GPU/VRAM 한계 |
| `.claude/rules/codex_orchestration_rules.md` | Codex TASK 위임 정책 |
