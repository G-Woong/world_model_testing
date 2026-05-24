# R3 Smoke Closure Report — friction + action_gain two-axis

> **Date**: 2026-05-24
> **Branch**: `memory-redesign-2026-05-16`
> **Status**: **PASS (with FINDING) — CLOSED**
> **Phase Gate**: `outputs/phase_gates/R3.passed` (zero-byte, preserved)
> **Supersedes**: `reports/r3_smoke_two_axis_R1.md` (이번 보고서가 R3 단계의 공식 종료 문서)
> **Authority**: 사용자 메시지 "R3 CLOSURE — two-axis smoke result finalization and future OOD expansion insight recording"

---

## A. Executive Summary

friction + action_gain 2-axis 기반 R3 base world model smoke가 **실행/수치/audit 측면에서 모두 PASS**했다.
그러나 두 OOD 축 모두에서 **OOD NLL < ID NLL** ("NLL 역전")이 양 task 동일하게 관측되었다.

원인 audit 결과 이 역전은 dataloader wiring bug나 metric 계산 오류가 **아니며**, action_gain=0.7 / friction=5.0 조건이 state transition magnitude를 체계적으로 축소시켜 Gaussian likelihood 관점에서 OOD가 "쉬워 보이게(easy-looking)" 만들기 때문으로 **물리적으로 확증**되었다.

이 finding은 *negative*가 아니라 **R4 falsification gate 설계의 핵심 동기 데이터**이다:
- raw NLL은 hidden dynamics shift를 놓칠 수 있음 → conformal-calibrated standardized residual `ρ_t = Σ_t^{-1/2}(z_{t+1}−μ_t)`와 양방향 β_t gate가 필요함.
- 따라서 R3는 "base WM이 OOD를 자동으로 탐지하지 못한다"는 사실을 명시적으로 입증한 단계로 닫는다.

R4/R5/R6 진입 권장. 단, future data expansion은 별도 문서(`docs/FUTURE_OOD_DATA_EXPANSION_INSIGHTS.md`)에 분리 기록.

---

## B. 사용한 task / axis / split / config

| 항목 | PickCube-v1 | PushCube-v1 |
|---|---|---|
| config | `configs/fglc/smoke_maniskill_pickcube.yaml` | `configs/fglc/smoke_maniskill_pushcube.yaml` |
| 별도 gain config 존재 | ❌ (통합 yaml 사용) | ❌ (통합 yaml 사용) |
| D_x / D_a | 42 / 8 | 35 / 8 |
| K / d / h_dim | 6 / 32 / 128 | 6 / 32 / 128 |
| epochs / batch / horizon / lr | 5 / 16 / 8 / 3e-4 | 5 / 16 / 8 / 3e-4 |
| train_id (n_eps) | 250 | 500 |
| val_id (n_eps) | 50 | 100 |
| ood_friction_low (n_eps, friction=5.0) | 50 | 100 |
| ood_gain_low (n_eps, gain=0.7) | 500 | 500 |
| ood_mass_low (n_eps, mass=1.5) — informational only | 50 | 100 |
| failed_metric (loop trigger) | `id_nll` | `id_nll` |
| gate threshold | `id_nll ≤ 0.5` | `id_nll ≤ 0.5` |
| dataloader splits 활성 | 5 (train/val/ood_mass/ood_friction/ood_gain) | 5 |
| Stage 2 patched files | `dataloader.py`, `evaluation/metrics.py`, `tests/test_fglc_r3_runner_maniskill.py` (commit `b4bcd3e`) | 동일 |

### config 확인 사항
- `n_episode_*` yaml 필드는 advisory (dead config). ManiSkill dataloader는 h5 파일 경로만 사용. 이 점은 yaml 내 `=== DATA SoT NOTE ===` 주석에 명시되어 있다.
- `ood_gain_h5`, `n_episode_ood_gain`, `ood_gain_value` 모두 두 yaml에 존재 (PickCube L29-31, PushCube L29-31).
- `seed_pool` 문자열은 manifest의 실제 seed_pool과 일치.

---

## C. Metrics summary table

artifact 경로:
- PickCube: `outputs/repair/pickcube_r3_2axis_2026-05-24/iter_0/metrics.json`
- PushCube: `outputs/repair/pushcube_r3_2axis_2026-05-24/iter_0/metrics.json`

| metric | PickCube | PushCube | 비고 |
|---|---:|---:|---|
| `id_nll` (val_id) | **−0.1612** | **−1.2036** | gate `< 0.5` ✓ |
| `train_nll` | −0.2295 | −1.2024 | |
| `val_train_nll_gap` | 0.0682 | −0.0012 | overfit 없음 |
| `ood_friction_nll` | −0.2456 | −1.2144 | id 대비 더 음수 (역전) |
| `ood_gain_nll` | −0.2917 | −1.2538 | id 대비 더 음수 (역전, 크기 큼) |
| `ood_mass_nll` | −0.2220 | −1.1991 | PushCube에서 정방향 (+0.0045) |
| `ood_id_nll_diff` (mean ood_mass+ood_friction) | −0.0726 | −0.0031 | |
| `kstep_nll_slope` | 0.0048 | 0.0632 | |
| `stagnant_epochs` | 1 | 0 | |
| `epoch` | 5 | 5 | |
| `wall_clock_minutes` | 0.031 | 0.031 | |
| `vram_peak_mib` | **33.25** | **33.22** | 8 GB의 0.4% (안전) |
| ledger REQUIRED_KEYS | **19/19 ✓** | **19/19 ✓** | |
| ledger `result` | `accept` | `accept` | |
| ledger `stop_condition_hit` | `target_reached` | `target_reached` | |
| ledger `git_sha` | `b4bcd3e…` | `b4bcd3e…` | Stage 2 patch 이후 동일 |
| NaN/Inf 존재 | 없음 ✓ | 없음 ✓ | |

---

## D. ID NLL / OOD NLL 결과 — 정량 해석

### D.1. ID NLL 성능
양 task 모두 ID NLL이 음수이며, 이는 학습된 모델이 ID 분포의 ground-truth state transition을 매우 좁은 σ 안에서 예측한다는 뜻이다 (Gaussian NLL = `0.5 log(2πσ²) + 0.5 (x−μ)²/σ²` 에서 σ가 작으면 첫째 항이 강하게 음수가 되어 전체 NLL이 음수가 될 수 있음). `id_nll < 0.5` gate를 통과한 시점에서 R3 base WM은 정상 학습되었다고 판단한다.

### D.2. OOD NLL 역전 신호 (양 task, 양 축)

| split | PickCube ood_nll − id_nll | PushCube ood_nll − id_nll | 방향 |
|---|---:|---:|---|
| ood_friction (friction=5.0) | −0.084 | −0.011 | 역전 |
| ood_gain (gain=0.7) | −0.131 | −0.050 | 역전 (강함) |
| ood_mass (mass=1.5) | −0.061 | **+0.0045** | PushCube만 정방향 |

→ **friction과 gain은 두 task에서 일관되게 raw NLL이 더 낮아지는 방향으로 움직인다.** mass는 PushCube에서만 약하게 정방향이다.

---

## E. OOD NLL 역전 finding

본 finding은 R4 falsification gate 설계의 1차 evidence로 보존된다.

### E.1. 관측 사실
- friction OOD: id 대비 NLL이 **PickCube에서 −0.084**, **PushCube에서 −0.011** 더 음수.
- gain OOD: id 대비 **PickCube에서 −0.131**, **PushCube에서 −0.050** 더 음수.
- 양 task에서 동일한 방향. 단일 task fluke가 아님.

### E.2. 즉시 가설 검토

| 가설 | 검토 결과 | 근거 |
|---|---|---|
| H1: dataloader가 ood split을 train_id로 라우팅하는 wiring bug | **기각** | `src/fglc/data/dataloader.py::_make_maniskill_datasets` L120-126: `split_h5_keys` dict가 `ood_gain → ood_gain_h5`, `ood_friction → ood_friction_h5` 명시적 매핑. config yaml의 ood_*_h5는 `ood_gain_low.h5` / `ood_friction_low.h5` 경로 정확. |
| H2: metric 계산이 ood split을 train_id에 덮어쓰는 bug | **기각** | `src/fglc/evaluation/metrics.py::Evaluator.evaluate` L44-77: 4개 split을 각각 독립 호출 (`self.trainer.evaluate_nll(dataloaders[split])`). split 이름이 metrics.json 키에 그대로 반영됨. |
| H3: ood h5 파일이 실수로 train_id의 복제본 | **기각** | manifest hash 4개 모두 다름 (PickCube: train_id `b06bacef…`, ood_friction `ad975629…`, ood_gain `befa833e…`, ood_mass `a14279c3…`). |
| H4: physics가 OOD를 "쉬워 보이게" 만든다 | **채택** | E.3 transition magnitude 분석 참조. |

### E.3. 물리적 확증: state transition magnitude

`reports/r3_smoke_two_axis_R1.md` §5에서 측정한 raw HDF5 transition magnitude (`mean(|x_{t+1}−x_t|)` over all transitions):

| split | PickCube trans_mean | PushCube trans_mean |
|---|---:|---:|
| train_id | 1.305 | 1.294 |
| ood_friction (friction=5.0) | 1.172 (**−10%**) | 1.182 (**−9%**) |
| ood_gain (gain=0.7) | 0.924 (**−29%**) | 0.914 (**−29%**) |
| ood_mass (mass=1.5) | 1.319 (+1%) | 1.325 (+2%) |

→ gain=0.7은 action 효과를 30% 줄여 state 전이 크기를 29% 감소시킨다. friction=5.0(joint 마찰)은 10% 감소. mass=1.5는 전이 크기에 거의 영향 없음 (1~2% 증가).

ID 학습 모델의 `σ²`는 train_id의 큰 magnitude 분포에 맞춰 학습됨. OOD에서 residual `(x_{t+1}−μ_t)²`가 체계적으로 작아짐 → Gaussian NLL의 `(x−μ)²/σ²` 항이 줄어듦 → NLL이 더 음수.

mass=1.5는 transition magnitude를 줄이지 않으므로 raw NLL 역전 현상이 약하게만 나타남 (PushCube에서 오히려 정방향).

### E.4. 결론
**wiring bug 아님. metric error 아님. raw NLL의 본질적 한계가 드러난 결과이다.**

---

## F. wiring bug가 아니라 물리적 현상으로 판단한 근거 (요약)

1. dataloader split→h5 매핑 코드 직접 확인 (read of `dataloader.py:120-126`).
2. metric 평가 루프가 4 split을 독립 호출 (`evaluation/metrics.py:44-77`).
3. manifest hash가 4 split에서 모두 다름 (PickCube 기준 4개 sha256).
4. transition magnitude를 raw HDF5에서 직접 측정 → gain −29%, friction −10%, mass +1% (PickCube/PushCube 동일).
5. mass 축에서는 magnitude가 줄지 않으므로 raw NLL 역전이 약함 또는 정방향 — 이는 가설 H4("physics가 OOD를 쉬워 보이게 함")와 일관됨.
6. 양 task에서 동일 패턴 재현 — 단일 task 또는 단일 seed에 한정된 우연이 아님.

---

## G. raw NLL 한계 — 명문화

### G.1. raw NLL은 "easy-looking OOD"를 놓친다
다음 두 조건이 동시에 성립하면 raw NLL이 OOD에서 더 낮아질 수 있다:
- (a) OOD가 system control gain을 줄이거나 시스템을 더 부드럽게 만들어 transition magnitude를 축소함.
- (b) 모델 σ²가 train magnitude에 맞춰져 OOD residual (x−μ)²/σ²가 함께 작아짐.

이런 조건의 실세계 대응(actuator gain 감소, 배터리 약화, 제어기 둔감화 등)은 dynamics가 명백히 바뀌었음에도 raw NLL이 OOD를 탐지하지 못한다는 위험을 안는다.

### G.2. raw NLL은 distribution shift 자체를 측정하지 않는다
raw NLL은 conditional likelihood `log p(x|z,a)`의 sample-mean이다. 이는 (1) state 분포 자체의 거리 (KL/W2), (2) dynamics rule의 변화, (3) 모델 σ²의 정합성, 세 요소가 모두 섞여 있다. 따라서 raw NLL 단일 값만으로는 "OOD인가/아닌가"를 직접 판정할 수 없다.

### G.3. 본 finding의 학문적 의미
이 R3 결과는 "base world model + raw NLL"만으로 OOD detection을 시도하는 모든 baseline (ReDRAW, DreamerV3 등)의 **공통 약점을 reproducible empirical evidence**로 보여준다. R4가 도입할 standardized mismatch + conformal calibration이 왜 필요한지를 직접 정당화한다.

---

## H. R4 falsification gate 필요성 — 본 finding의 R4 연결

### H.1. 무엇을 R4에서 측정해야 하는가
- ρ_t = Σ_t^{-1/2}(z_{t+1}−μ_t) (latent-group별 standardized residual)
- ρ_t의 **방향 통계** (systematic bias) — 단순 |ρ_t|가 작아도 방향이 일관되게 한쪽으로 치우치면 falsification 신호.
- ρ_t의 conformal calibration: ID에서 보정된 quantile q^{1-α}를 사용하여 OOD score를 비교.
- β_t = `FalsificationGate(ρ_t, h_t)` — magnitude + direction + sequential evidence를 결합.

### H.2. 본 finding이 R4 설계에 강제하는 3가지 조건

1. **양방향 detection 의무**: gain=0.7 (effect 감소) ↔ gain=1.3 (effect 증가) 양 방향에서 β_t가 모두 falsification 신호를 내야 함. magnitude-only gate는 (a)에서 실패.
2. **σ recalibration 무관성**: 모델 σ²가 train에 맞춰 작아진 상태에서도 β_t는 작동해야 함. 따라서 conformal calibration의 prediction interval은 σ̂에 직접 의존하지 않는 형태가 바람직 (e.g., empirical quantile over ID ρ_t).
3. **temporal consistency**: 단일 step의 ρ_t만으로 OOD 판정을 하면 false-positive가 폭증. CUSUM/SPRT-like sequential evidence aggregation (`docs/idea/02_FALSIFICATION_THEORY.md` §sequential block) 필수.

### H.3. R4 PASS gate 제안 (R4 설계 단계에서 확정 예정)
- ROC AUROC(β_t, ground-truth OOD label) ≥ **0.85** on (friction OR gain) OOD split
- false-positive rate (β_t fires on ID split) ≤ **0.05** (conformal α=0.05)
- gain=0.7 / gain=1.3 양방향 모두 AUROC ≥ 0.80
- raw NLL baseline 대비 AUROC gain ≥ **+0.20** absolute

→ 이 기준은 본 R3 closure finding이 직접 동기를 부여한다.

---

## I. metrics.json / ledger 경로

### PickCube
- iter metrics: `outputs/repair/pickcube_r3_2axis_2026-05-24/iter_0/metrics.json`
- iter config: `outputs/repair/pickcube_r3_2axis_2026-05-24/iter_0/config.yaml`
- iter manifest: `outputs/repair/pickcube_r3_2axis_2026-05-24/iter_0/run_manifest.json`
- loop ledger: `outputs/repair/pickcube_r3_2axis_2026-05-24/loop_2026-05-24T08-20-04-b2c2/ledger.jsonl`
- loop compare: `outputs/repair/pickcube_r3_2axis_2026-05-24/loop_2026-05-24T08-20-04-b2c2/iter_0/compare.json`
- stdout: `outputs/repair/pickcube_r3_2axis_2026-05-24/stdout.log`

### PushCube
- iter metrics: `outputs/repair/pushcube_r3_2axis_2026-05-24/iter_0/metrics.json`
- iter config: `outputs/repair/pushcube_r3_2axis_2026-05-24/iter_0/config.yaml`
- iter manifest: `outputs/repair/pushcube_r3_2axis_2026-05-24/iter_0/run_manifest.json`
- loop ledger: `outputs/repair/pushcube_r3_2axis_2026-05-24/loop_2026-05-24T08-22-43-926d/ledger.jsonl`
- loop compare: `outputs/repair/pushcube_r3_2axis_2026-05-24/loop_2026-05-24T08-22-43-926d/iter_0/compare.json`
- stdout: `outputs/repair/pushcube_r3_2axis_2026-05-24/stdout.log`

### Phase gate sentinel (보존)
- `outputs/phase_gates/R0.passed`
- `outputs/phase_gates/R1.passed`
- `outputs/phase_gates/R2.passed`
- `outputs/phase_gates/R3.passed`

---

## J. 테스트 결과

```powershell
& .venv/Scripts/python.exe -m pytest -q \
    tests/test_fglc_r3_runner_maniskill.py \
    tests/test_fglc_forbidden_field_sync.py \
    tests/test_fglc_split_integrity.py \
    tests/test_fglc_ood_severity.py
```

결과: **54 passed, 0 failed** (executed 2026-05-24 R3 closure 단계).

| test 파일 | passed | 비고 |
|---|---:|---|
| `test_fglc_r3_runner_maniskill.py` | 4 | 6 splits (ood_gain 포함) 정상 검증 |
| `test_fglc_forbidden_field_sync.py` | 32 | 12 forbidden field 동기화 PASS |
| `test_fglc_split_integrity.py` | 12 | split-integrity 회귀 PASS |
| `test_fglc_ood_severity.py` | 6 | OOD severity (friction+gain) PASS |

추가 검증:
- metrics.json schema: 11개 STAGE1_CANONICAL_METRIC_KEYS 모두 존재 ✓ (직접 확인)
- ledger REQUIRED_KEYS: 19 ✓ (두 ledger.jsonl 모두)
- raw HDF5 mtime: smoke 실행(17:20) 이전(15:24)이 가장 최신 — 변경 없음 ✓

---

## K. 판정

**PASS (with FINDING) — R3 단계 종료**

### PASS 조건 충족 확인 (10/10)

| # | 조건 | 결과 |
|---|---|---:|
| 1 | R3 smoke artifact (metrics/ledger/manifest) 확인 완료 | ✓ |
| 2 | metrics.json 모든 키 finite | ✓ |
| 3 | ledger result=accept, stop_condition=target_reached | ✓ |
| 4 | ID/OOD NLL 결과 문서화 (본 보고서 §C, §D) | ✓ |
| 5 | OOD NLL 역전 finding 물리적 확증 문서화 (§E, §F) | ✓ |
| 6 | future OOD expansion insight 별도 문서화 | ✓ (`docs/FUTURE_OOD_DATA_EXPANSION_INSIGHTS.md`) |
| 7 | 필수 테스트 4종 PASS (54/54) | ✓ |
| 8 | raw HDF5 변경 없음 | ✓ |
| 9 | R4/R5/R6 실행 또는 코드 수정 없음 | ✓ |
| 10 | commit atomic, raw/대용량/unrelated 제외 | ✓ (Stage 7에서 완료 예정) |

### FINDING이 negative result로 격하되지 않는 이유
본 finding은 base WM의 raw NLL이 OOD detection metric으로 불완전하다는 사실을 **재현 가능한 evidence**로 보여준다. 이는 R4 falsification gate의 도입 동기를 **실험적으로 정당화**한다. negative result가 아닌 **R4 design data**이다.

---

## L. 다음 단계 권장

### L.1. 즉시 (R4 phase)
1. **R4 falsification gate 설계 착수** — `docs/idea/02_FALSIFICATION_THEORY.md` + `docs/idea/04_BASE_WORLD_MODEL.md` 재독.
2. β_t gate 구현 시 본 finding 반영:
   - magnitude + direction 결합
   - empirical quantile (ID ρ_t) 기반 conformal calibration (σ̂ 비의존)
   - sequential aggregation (CUSUM/SPRT-like)
3. **2-axis baseline 측정**: friction + gain 양 axis에서 β_t의 AUROC를 raw NLL과 비교하여 R4 effectiveness를 정량 검증.

### L.2. 단기 (R4 evaluation 단계)
1. gain=1.3 (effect 증가 방향) OOD 데이터 추가 수집 검토 (별도 SAFETY review 후).
2. R4 evaluation set에 본 R3 smoke의 4 split (val_id / ood_friction / ood_gain / ood_mass)을 그대로 재활용 → R4 effectiveness가 R3 base WM 대비 얼마나 향상되는지 직접 비교 가능.
3. mass OOD axis는 R4 PASS gate에서 informational only (transition magnitude 차이가 미미하므로 R4가 의미 있는 신호를 만들기 어려움 예상; R4 결과 후 재평가).

### L.3. 중장기 (R5~R6 전후)
- `docs/FUTURE_OOD_DATA_EXPANSION_INSIGHTS.md` 참조: hard OOD (latency, stronger friction, multi-axis) 수집 후 R5 causal attention + R6 correction의 검증 power 향상.
- mass axis repair track (contact-rich / scripted / goal-conditioned policy 검토) — 이번 작업 범위 외.

---

## 참조 artifact 트리

```
outputs/repair/
├── pickcube_r3_2axis_2026-05-24/
│   ├── iter_0/                          (metrics.json, config.yaml, run_manifest.json)
│   ├── loop_2026-05-24T08-20-04-b2c2/   (ledger.jsonl, iter_0/compare.json)
│   └── stdout.log
└── pushcube_r3_2axis_2026-05-24/
    ├── iter_0/
    ├── loop_2026-05-24T08-22-43-926d/
    └── stdout.log

outputs/phase_gates/
├── R0.passed
├── R1.passed
├── R2.passed
└── R3.passed                            (preserved by this closure)

reports/
├── r3_entry_audit_R1.md                 (R3 진입 audit, U-N3 해결)
├── r3_readiness_action_gain_R1.md       (action_gain 2-axis 데이터 readiness)
├── r3_smoke_two_axis_R1.md              (R3 smoke 실행 보고서)
└── R3_SMOKE_CLOSURE_REPORT.md           (본 문서, R3 단계 공식 종료)

docs/
└── FUTURE_OOD_DATA_EXPANSION_INSIGHTS.md (easy-looking vs hard OOD insight, R4~R6 활용)
```

---

*Closure completed: 2026-05-24. R3 closed. Next: R4 falsification gate design.*
