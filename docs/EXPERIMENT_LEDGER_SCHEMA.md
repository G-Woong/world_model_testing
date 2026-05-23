# EXPERIMENT_LEDGER_SCHEMA — 실험 Ledger JSON Schema 명세

> **Source**: `docs/EXPERIMENT_REPAIR_LOOP_PLAN.md` §F.3 + §D.4 (accept/reject 규칙)
> **Runtime consumer**: `src/fglc/repair/ledger.py`
> **Output path**: `outputs/repair/{loop_id}/ledger.jsonl` (1 line = 1 iteration)
> **Status**: v0 (2026-05-23)

---

## 목적

closed-loop repair harness가 각 iteration의 실험 결과, 진단 원인, 패치 후보, 결정을
**추적 가능하고 재현 가능한** 형태로 누적하기 위한 ledger schema다.

한 줄(`\n`으로 구분된 JSON)이 한 iteration을 나타낸다 (JSON Lines format).

---

## 경로 규약

```
outputs/repair/{loop_id}/
  ledger.jsonl          # 누적 ledger (JSON Lines)
  iter_{N}/
    config.yaml         # 해당 iter에서 사용한 resolved config snapshot
    metrics.json        # 4축 metric artifact (실제 숫자만)
    compare.json        # before/after diff + accept/reject/inconclusive
    run_manifest.json   # outputs/runs/{run_id}/run_manifest.json 복사본
```

`loop_id` 형식: `loop_YYYY-MM-DDTHH-MM-SS` (ISO 8601, 콜론 대신 하이픈)

---

## Ledger Line Schema (JSON)

```jsonc
{
  // ── 식별자 ──────────────────────────────────────────────
  "loop_id":         "loop_2026-05-23T15-00-00",    // loop 시작 타임스탬프
  "iter":            0,                              // 0-based iteration index
  "run_id":          "r3_smoke_seed42_K6_d32_h128", // "{phase}_{desc}_{seed}_{key_params}"
  "git_sha":         "6fcc09c",                      // 실험 시 HEAD의 short SHA
  "config_hash":     "sha256:abc123...",             // resolved config의 SHA-256
  "config_path":     "configs/fglc/smoke_4060.yaml", // 사용한 config 파일 경로
  "phase":           "R3",                           // 현재 phase (R2~R10)
  "split":           "PickCube/id",                  // 진단 기준 eval split

  // ── Metric snapshot ───────────────────────────────────
  "metrics_before": {                                // iter 시작 전 baseline metric
    "id_nll_1step":          0.42,
    "ood_mass_nll_1step":    0.51,
    "ood_friction_nll_1step": null,                  // 미측정 시 null
    "detection_auroc":       null,
    "nec_suf_score":         null,
    "eval_return_mean":      null
  },
  "metrics_after": {                                 // 이번 iter 종료 후 측정 metric
    "id_nll_1step":          0.28,
    "ood_mass_nll_1step":    0.55,
    "ood_friction_nll_1step": null,
    "detection_auroc":       null,
    "nec_suf_score":         null,
    "eval_return_mean":      null
  },
  "deltas": {                                        // metrics_after − metrics_before
    "id_nll_1step":          -0.14,
    "ood_mass_nll_1step":    0.04,
    "ood_friction_nll_1step": null,
    "detection_auroc":       null,
    "nec_suf_score":         null,
    "eval_return_mean":      null
  },

  // ── 진단 ─────────────────────────────────────────────
  "failed_metric":    "id_nll_1step",                // gate threshold 미달한 metric 키
  "gate_threshold":   0.35,                          // 해당 metric의 phase gate threshold
  "diagnosed_cause":  ["MODEL_UNDERCAPACITY", "HORIZON_TOO_SHORT"],  // taxonomy enum-id 복수

  // ── Repair candidate ──────────────────────────────────
  "candidate_chosen": {
    "id":          "C-014",                          // 후보 식별자 (candidates.py SSoT)
    "patch":       {"h_dim": 256, "train_horizon": 16},  // config 변경 dict
    "description": "h_dim 128→256, train_horizon 8→16"
  },
  "candidate_cost_minutes":    22,                   // 예상 wall-clock (분)
  "candidate_risk":            0.2,                  // 0.0~1.0 (회귀 위험)
  "candidate_expected_signal": 0.6,                  // 0.0~1.0 (primary metric 개선 기댓값)
  "candidate_rank_score":      0.68,                 // ranker.py 산출 composite score

  // ── 결정 ─────────────────────────────────────────────
  "result":          "accept",                       // "accept" | "reject" | "inconclusive"
  "result_reason":   "Δid_nll = -0.14 ≥ ε_accept(0.05), no regression",
  "epsilon_accept":  0.05,                           // primary metric 개선 최소 threshold
  "epsilon_reject":  0.0,                            // primary metric 비개선 threshold
  "epsilon_secondary": 0.10,                         // secondary metric 허용 최대 악화

  // ── 실행 자원 ─────────────────────────────────────────
  "wall_clock_minutes":     24,
  "vram_peak_mib":          5230,
  "oom_fallbacks_applied":  [],                      // e.g. ["batch_size: 16→8"]
  "early_stop_triggered":   false,
  "early_stop_reason":      null,

  // ── Stop 조건 ────────────────────────────────────────
  "stop_condition_hit":  null,                       // null | "max_iter" | "wall_clock" | "target_reached" | "consecutive_inconclusive" | "hook_blocked"
  "next_action":         "proceed to R4 smoke",

  // ── 메타 ─────────────────────────────────────────────
  "notes": ""
}
```

---

## 필수 키 목록

ledger.py의 schema validation은 다음 키가 반드시 존재하는지 검사한다:

```python
REQUIRED_KEYS = [
    "loop_id", "iter", "run_id", "git_sha", "config_hash",
    "config_path", "phase", "split",
    "metrics_before", "metrics_after", "deltas",
    "failed_metric", "diagnosed_cause",
    "candidate_chosen", "result",
    "stop_condition_hit", "next_action",
    "wall_clock_minutes", "vram_peak_mib",
]
```

---

## run_manifest.json 최소 필드

`outputs/runs/{run_id}/run_manifest.json`은 다음 최소 필드를 포함해야 한다
(ledger와의 정합성을 위해):

```json
{
  "run_id":      "r3_smoke_seed42_K6_d32_h128",
  "config":      {"path": "configs/fglc/smoke_4060.yaml", "hash": "sha256:abc123..."},
  "seed":        42,
  "status":      "completed",
  "git_sha":     "6fcc09c",
  "start_time":  "2026-05-23T15:00:00Z",
  "end_time":    "2026-05-23T15:24:00Z",
  "phase":       "R3"
}
```

---

## accept/reject/inconclusive 결정 규칙

(`src/fglc/repair/compare.py` 구현 기준, `docs/EXPERIMENT_REPAIR_LOOP_PLAN.md` §D.4에서 도출)

```
primary_delta = metrics_after[failed_metric] − metrics_before[failed_metric]
  (NLL 계열: 낮을수록 좋음 → delta < 0이 개선)
  (AUROC/return 계열: 높을수록 좋음 → delta > 0이 개선)

secondary_deltas = {k: v for k, v in deltas.items() if k != failed_metric}

accept:
  primary 개선 폭 ≥ ε_accept (기본 0.05)
  AND 어떤 secondary delta도 −ε_secondary(기본 0.10) 이하 미달 없음

reject:
  primary 개선 폭 ≤ ε_reject (기본 0.0)
  OR 어떤 secondary delta가 −ε_secondary 이하 악화

inconclusive:
  위 둘 다 아닌 경우 (개선했지만 ε_accept 미달 등)
```

---

## Stop 조건 enum

```
"max_iter"                 — loop_id 내 iter 수 ≥ max_iter (기본 5)
"wall_clock"               — loop 누적 wall_clock ≥ max_wall_clock_minutes (기본 240분)
"target_reached"           — failed_metric이 gate threshold 충족
"consecutive_inconclusive" — 연속 inconclusive ≥ 3
"hook_blocked"             — phase_gate_guard.ps1 또는 leakage hook이 BLOCK 반환
```

---

## 참조

- repair taxonomy: `docs/idea/FGLC_FAILURE_TAXONOMY.md`
- ledger 구현: `src/fglc/repair/ledger.py`
- compare 구현: `src/fglc/repair/compare.py`
- 4060 smoke budget: `docs/ROADMAP/4060_SMOKE_REPAIR_PATH.md`
- master plan: `docs/EXPERIMENT_REPAIR_LOOP_PLAN.md`
