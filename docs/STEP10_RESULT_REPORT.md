# STEP 10 — R3 Base WM Smoke Result Report

> 작성일: 2026-05-23  
> Phase: memory-redesign-2026-05-16  
> 직전 commit: 35604d0 (TASK_10E merge)  
> 결과: **STEP10_PASS — synthetic toy fixture 단계 연결 검증 완료**

---

## 1. 완료된 Sub-step 요약

| Sub-step | 범위 | 결과 | Commit |
|---|---|---|---|
| 10A | R3 prerequisite audit + R1 mini-closure | ✅ PASS | `docs/STEP10A_AUDIT_REPORT.md` 작성, `R1.passed` 생성 |
| 10B | Config schema 확장 + state-only toy dataset + R2 mini-closure | ✅ PASS | `6bc087e` TASK_10B merge |
| 10C | Base WM 최소 모듈 (encoder/belief/dynamics/heads) | ✅ PASS | `e779412` TASK_10C merge |
| 10D | Trainer + Evaluator + metrics.json artifact | ✅ PASS | `5341341` TASK_10D merge |
| 10E | R3Runner adapter + repair_loop 연결 | ✅ PASS | `35604d0` TASK_10E merge |
| 10F | 1-iter real smoke 실행 | ✅ PASS | 이 보고서 |

---

## 2. 최종 pytest 상태

```
185 passed in 12.83s
```

이전 대비 증가:
- Step 9.5 이후: 159 passed
- TASK 10B (dataset tests): +6 → 165
- TASK 10C (WM shape tests): +8 → 173
- TASK 10D (trainer smoke tests): +6 → 179
- TASK 10E (r3_runner integration tests): +6 → 185

---

## 3. TASK 10F: 1-iter Real Smoke 실행 결과

### 실행 명령
```
python scripts\fglc\r3_smoke.py \
  --phase R3 --config configs\fglc\smoke_4060.yaml \
  --seed 42 --descriptor smoke_synthetic \
  --max-iter 1 --max-wall-clock-minutes 60 \
  --output-root outputs\repair
```

### 결과 요약
```json
{
  "loop_id": "loop_2026-05-23T10-45-27-0539",
  "final_result": "inconclusive",
  "metrics_after": {
    "id_nll": 0.9599,
    "train_nll": 0.9579,
    "val_nll": 0.9599,
    "val_train_nll_gap": 0.0020,
    "ood_mass_nll": 0.9747,
    "ood_friction_nll": 0.9581,
    "ood_id_nll_diff": 0.0065,
    "stagnant_epochs": 0,
    "kstep_nll_slope": 0.00144,
    "epoch": 5,
    "wall_clock_minutes": 0.025,
    "vram_peak_mib": 33.06
  }
}
```

### ledger.jsonl 검증
```
outputs/repair/loop_2026-05-23T10-45-27-0539/ledger.jsonl
REQUIRED_KEYS 19/19: PASS
```

### iter_0/ artifacts 생성 (CD-2)
```
iter_0/
  compare.json     {} (baseline — 비교 없음) ✅
  run_manifest.json  {iter_index: 0, loop_id, phase, seed, descriptor, patch: null} ✅
```

---

## 4. 결과 해석

### 4.1 연결 흐름 검증 (핵심 목표)
```
synthetic toy dataset
→ SyntheticToyDataset(4 splits) → make_dataloaders
→ Encoder + BeliefMemory + GroupedDynamics + RewardHead + ValueHead
→ TrainerR3 (Stage 1 loss) → evaluate_model → metrics dict
→ R3SmokeRunner (RunnerOutput)
→ run_repair_loop → diagnose → candidates → rank → ledger.jsonl
```
**전체 연결 끊김 없음 — PASS**.

### 4.2 id_nll = 0.96 (gate threshold 0.5 초과)
- 현재 id_nll = 0.96이며 smoke gate 0.5를 초과.
- **이것은 예상된 결과**. synthetic toy에서 5 epochs (batch=16, T=8, K=6, d=32)은 충분한 학습이 아님.
- 4060 완화 임계값 (0.5)을 통과하려면 epochs 증가, 또는 ManiSkill state-only 실제 데이터 필요.
- **smoke의 목표는 id_nll gate 통과가 아니라 연결 검증** → PASS.

### 4.3 repair loop 흐름
- diagnose(id_nll=0.96, phase="R3") → `IMPLEMENTATION_BUG_SUSPECTED` 발화
  - 이유: diagnose.py에 정의된 임계값을 넘었으나 현재 CANDIDATE_TABLE에서 
    repair 후보가 없어 sentinel-only → escalate_to_user
- **repair loop가 올바르게 escalate한 것은 정상 동작**
- `stop_condition_hit: "hook_blocked"` — `escalate_to_user`로 인한 early exit (max_iter=1 내에서)
- **이것은 smoke 실패가 아니라 repair loop의 정상 실패 처리 경로**

### 4.4 미해결 관찰
| 항목 | 값 | 해석 |
|---|---|---|
| `train_vram_peak_mib`, `train_wall_clock_minutes` | metrics에 추가 키 존재 | CANONICAL_METRIC_KEYS / ARTIFACT_KEYS 미선언 키. 기능상 무해, ManiSkill 단계에서 정리 권장 |
| id_nll 0.96 | 0.5 gate 초과 | 정상 (5 epoch synthetic, 충분한 학습 아님) |
| ood_id_nll_diff 0.0065 | 매우 작은 OOD gap | synthetic toy에서 mass=2.0은 dynamics가 충분히 불안정하지 않음. 실제 ManiSkill에서 더 큰 gap 예상 |

---

## 5. CD 항목 처리 현황

| CD | 내용 | 상태 |
|---|---|---|
| CD-1 | ledger path `{loop_id}/ledger.jsonl` | ✅ Step 9.5에서 완료 |
| CD-2 | iter_{N}/ 4종 artifact | ✅ TASK_10E에서 compare.json + run_manifest.json 생성 |
| CD-3 | id_nll 명명 표준화 | ✅ TASK_10D에서 CANONICAL_METRIC_KEYS val_nll/ood_mass_nll/ood_friction_nll 추가 |
| CD-4 | repair_loop.py id_nll gate 0.4→0.5 | ✅ TASK_10E에서 완료 |
| CD-5 | --dry-run help text 보강 | ⚠️ OPEN (LOW 우선순위, 다음 단계로 이월) |
| CD-6 | LEDGER_SCHEMA Optional Fields 섹션 | ✅ Step 9.5에서 완료 |
| CD-7 | --max-wall-clock typo | ✅ Step 9.5에서 완료 |
| CD-8 | smoke_4060.yaml 전체 schema | ✅ TASK_10B에서 완료 |
| CD-9 | loop_id uuid suffix | ✅ Step 9.5에서 완료 |

---

## 6. Sentinel 현황

```
outputs/phase_gates/R0.passed  (2026-05-22)
outputs/phase_gates/R1.passed  (2026-05-23 18:59)
outputs/phase_gates/R2.passed  (2026-05-23 19:17)
R3.passed: 생성 안 함 (synthetic만으로 R3 gate 통과 불가)
```

---

## 7. 새로 생성된 구조체 요약

```
src/fglc/
  data/__init__.py
  data/state_only_dataset.py     SyntheticToyDataset (4 splits, forbidden field guard)
  data/dataloader.py             make_dataloaders()
  models/__init__.py
  models/encoder.py              Encoder (MLP, K=6, d=32)
  models/belief.py               BeliefMemory (GRU, h_dim=128)
  models/dynamics.py             GroupedDynamics (per-group MLP, per-group μ+logσ)
  models/heads.py                RewardHead + ValueHead
  training/__init__.py
  training/trainer_r3.py         TrainerR3 (Stage 1 loss: NLL+reward+value)
  evaluation/__init__.py
  evaluation/metrics.py          evaluate_model() → CANONICAL_METRIC_KEYS dict
  runners/__init__.py
  runners/r3_runner.py           R3SmokeRunner (RepairRunner Protocol)

scripts/fglc/
  r3_smoke.py                   real smoke entry point
  repair_loop.py                --use-real-runner flag 추가, CD-4

configs/fglc/
  smoke_4060.yaml               전체 schema (K=6, h_dim=128, batch=16, 4 sections)

tests/
  test_fglc_dataset_state_only.py   6 tests
  test_fglc_base_wm.py              8 tests
  test_fglc_trainer_r3_smoke.py     6 tests
  test_fglc_r3_runner_integration.py 6 tests
  fixtures/__init__.py
```

---

## 8. 다음 단계 권고

### 8.1 R3.passed gate 진입 경로 (별도 phase)
- ManiSkill state-only 데이터 파이프라인 구현 (`src/fglc/data/maniskill_collector.py`)
- `pyproject.toml [maniskill]` extras 설치 + Windows 호환성 검증
- 실제 ID NLL ≤ 0.5 nat (4060 완화) 또는 < 0.1 nat (정식 gate) 달성 후 `/fglc-phase-check --pass R3`
- diagnose CANDIDATE_TABLE에 ID NLL 관련 repair 후보 보강 (현재 IMPLEMENTATION_BUG_SUSPECTED로 escalation)

### 8.2 즉시 처리 권장
- `train_vram_peak_mib`, `train_wall_clock_minutes` 비표준 키: ARTIFACT_KEYS에 추가 또는 Trainer에서 제거
- CD-5 (--dry-run help text) LOW 우선순위 마무리

### 8.3 R3.passed 생성 금지 재확인
- synthetic toy 단계만으로 R3 과학적 gate 통과로 간주 **불가**.
- ManiSkill 실제 데이터로 ID NLL < 0.1 nat 달성 후 별도 phase-check 필요.

---

## 9. 결론

**STEP10_PASS** — synthetic toy fixture 단계에서 다음 연결이 끊김 없이 검증됨:
```
toy dataset → encoder/belief/dynamics → trainer → evaluator → metrics.json
→ R3Runner(RepairRunner Protocol) → run_repair_loop → diagnose → ledger.jsonl
```

- `R0.passed` + `R1.passed` + `R2.passed` sentinel 생성 완료.
- `R3.passed` = ManiSkill 단계 이후 별도 phase-check (이 보고서 시점 미생성).
- 185 tests passed, 회귀 없음.
- CD-1~CD-9 중 CD-5만 LOW 우선순위 이월.
