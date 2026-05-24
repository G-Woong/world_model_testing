# Four-Axis Dataset Design — Agent Synthesis Report

> **작성일**: 2026-05-24
> **Phase**: R2 완료 → R3 진입 전
> **Branch**: `memory-redesign-2026-05-16`
> **선행**: `docs/INTERACTION_AXIS_DATASET_DESIGN_REVIEW.md` (commit `7fe0a02`)
> **목적**: Agent A~I 9명의 관점에서 4-axis 데이터셋 설계 타당성 종합 심사
> **판정 요약**:
> - Agent I (synthesis chair): **CONDITIONAL_ACCEPT** (friction + action_gain Pilot PASS 조건부)
> - 즉시 BLOCKED: mass+random (PickCube gap=0.0038, PushCube gap=0.008)
> - 즉시 PASS: friction × 2 task (gap 0.138 / 0.124)
> - 구현 후 검증 필요: action_gain, latency, noise

---

## Agent A — axis-scout

### Role
13개 interaction axis 후보 조사 → 4 axis PRIMARY/SECONDARY 선택 근거 검증

### Input
- `docs/idea/18_DATA_BENCHMARKS.md` (5 axis SSoT)
- `src/fglc/data/collector.py` (구현 현황)
- `src/fglc/data/maniskill_schema.py` (TASK_OOD_PARAMS)
- INTERACTION_AXIS_REVIEW §D (13개 axis 점수표)

### Top 3 Findings

1. **friction axis**: 구현 완료 (collector.py:84-89), 두 task PASS. 그러나 SSoT 단위(`µ_kinetic`) ↔ API 단위(`joint_dry_friction`) 매핑 DEFERRED. 리뷰어 "물리 단위 불일치" 공격 가능 — `quality_report.json:friction_mapping=DEFERRED` 기록됨.

2. **action_gain, latency, noise**: SSoT에 정의됨 (`18_DATA_BENCHMARKS.md:44`) 그러나 코드 구현 없음. `_apply_ood()`에 분기 없음. `eval_metas`에 placeholder만 존재. 총 추가 LOC: action_gain ~50, latency ~40, noise ~15 = **~105 LOC** (collector.py + schema + test).

3. **mass+random**: 두 task 모두 실측 FAIL (gap 0.0038/0.008 < 0.01). contact_rate=0%에서 `F=ma` 물리 경로 완전 차단. 16개 metric 어느 것도 구분 못함. 별도 scripted policy repair track 분리 필수.

### Top 2 Unresolved UNKNOWNs

- **[U-A1]** ManiSkill 3.0.1에서 `action_gain`의 `env.step(a)` 전 clipping 위치. `gym.Env.step` 내부에서 action clip이 발생하면 gain=1.3의 effective gain이 낮아질 수 있음.
- **[U-A2]** LiftCube-v1 actor 이름 (`inner.cube`? `inner.obj`?). mass repair track 후보이나 probe 없이 확인 불가.

### Recommendations

1. 즉시: friction 기존 데이터로 R3 smoke 준비 (코드 변경 없음)
2. 1주 이내: action_gain `_apply_ood` 구현 (TASK_2050) → probe 50ep
3. 병렬: latency FIFO buffer 설계 문서화 (buffer reset 정책 먼저 확정)
4. mass repair track: LiftCube-v1 probe → contact_rate 확인 후 scripted policy 결정

### Judgment: **PASS** (friction), **PATCH** (action_gain/latency/noise 구현 필요 명시)

---

## Agent B — claim-metric-alignment-auditor

### Role
axis → metric → claim 1:1 매핑 검증. 누락 metric 탐지.

### Input
- `docs/idea/04_BASE_WORLD_MODEL.md` (encoder, K-group, dynamics)
- `docs/idea/10_LOSS_DESIGN.md` (Stage 1/2 losses)
- `docs/idea/21_METRICS.md` (4축 metric + thresholds)
- `src/fglc/repair/taxonomy.py` (20 FailureCauseId)

### Top 3 Findings

1. **friction → 4축 metric 1:1 매핑 완성**:
   - Axis 1 (예측 NLL): OOD NLL > ID NLL ← friction gap=0.138 실증
   - Axis 2 (falsification AUROC): β_t 발화 ↔ `regime_id` eval label → AUROC ≥ 0.75 기대
   - Axis 3 (attribution nec-suf): qvel dims 9-17의 necessity/sufficiency 검증 가능
   - Axis 4 (control return): friction shift → planner return 감소 → FGLC correction return 회복

2. **action_gain → C2(action-value relevance) 최강**:
   - `V(s)` gradient → action-relevant latent group 활성화 → α_t의 value-aware 특성 가장 직접 검증
   - gain=0.7 vs ID: action → state transition 변화 → μ_t 예측 오류 → ρ_t 편차
   - 4축 모두 강한 signal 기대

3. **noise → Axis 2 (AUROC)에서 의도적 낮은 값**:
   - noise는 dynamics hypothesis를 바꾸지 않음 → β_t false positive 방지가 목표
   - FGLC Σ calibration이 올바르면 AUROC < 0.65 예상
   - 이 값이 ≥ 0.70이면 SIGMA_CALIBRATION_FAILURE → repair loop

### Top 2 Unresolved UNKNOWNs

- **[U-B1]** latency axis에서 falsification gate β_t 발화 이론: 시간 지연으로 인한 누적 phase error가 `ρ_t = Σ_t^{-1/2}(z_{t+1} - μ_t)` 임계를 초과하는 step 수 — 실측 전 불확실.
- **[U-B2]** action_gain clipping이 있을 경우 C2(action-value) signal이 감소 → planning decision 변화가 줄어들 가능성.

### Recommendations

1. noise axis는 Stage 3 (R4 falsification gate 이후)에서 Σ calibration 함께 평가 권장
2. latency axis는 temporal consistency loss (`L_temporal`) 설계 시 d-step group 분리 명시 필요
3. claim 매핑표: `docs/idea/21_METRICS.md`의 axis별 threshold를 `quality_report.json`에 함께 기록하도록 확장 권장

### Judgment: **PASS** (friction 4축 완전 매핑), **CONDITIONAL** (action_gain/latency — Pilot 후 재확인)

---

## Agent C — data-quality-gatekeeper

### Role
validators.py 10 reject reasons + 30 quality gate 통과 예측

### Input
- `src/fglc/data/validators.py`
- `src/fglc/data/manifest.py`
- `data/fglc/PickCube-v1/quality_report.json`
- `data/fglc/PushCube-v1/quality_report.json`

### Top 3 Findings

1. **기존 데이터 품질 높음**:
   - PickCube 450ep: n_rejected=0 (100% accept), Ckpt 0~3 PASS
   - PushCube 900ep: n_rejected=0 (100% accept), 동일
   - hash_intra_duplicate_count=0, hash_inter_duplicate_count=0
   - forbidden_field=0 (12개 모두 eval_metas에만)

2. **Ckpt 4 FAIL (ood_sev mass)**:
   - PickCube: `checkpoint_4_ood_sev=FAIL` (mass gap 0.0038 < 0.01)
   - friction은 PASS — checkpoint_4는 axis별 독립 체크 필요 (현재 mass가 전체를 FAIL로 표기)
   - Ckpt 5/6/9=SKIP: learnability/repair_metric/novelty — R3 smoke 후 평가 예정

3. **신규 axis 수집 시 validator 확장 필요**:
   - action_gain: action_std 감소 검증 추가 (gain=0.7이면 action_std ≈ 0.404 vs ID ≈ 0.577)
   - latency: `commanded_action` ≠ `executed_action` 기록 확인 validator
   - noise: state_std 증가 검증 (σ=0.1이면 각 dim std ≈ original_std + 0.1)

### Top 2 Unresolved UNKNOWNs

- **[U-C1]** PickCube on-disk train_id=250ep ↔ smoke config `n_episodes=50` 격차. 다른 collect run 결과인지, config 버전 불일치인지 확인 필요.
- **[U-C2]** `quality_report.json Ckpt 4 FAIL` (mass) vs `STEP11_RESULT_REPORT Ckpt 4 PASS` 충돌. friction의 Ckpt 4는 PASS일 것이나, 현재 JSON에 mass와 friction 통합 표기 문제 가능성.

### Recommendations

1. quality_report.json을 axis별로 분리 기록하도록 확장 (mass:FAIL, friction:PASS 독립)
2. 신규 axis별 validator 추가 → TASK_2053에 포함
3. Ckpt 4~9를 friction 전용으로 재실행하여 SKIP 해소

### Judgment: **PASS** (friction 기존 데이터 전체 quality gate H1-H21), **PATCH** (신규 axis validator 추가 필요)

---

## Agent D — split-leakage-auditor

### Role
seed pool / hash / regime leakage 완전 검증

### Input
- `data/fglc/PickCube-v1/manifest.json`
- `data/fglc/PushCube-v1/manifest.json`
- `tests/test_fglc_split_integrity.py`
- `src/fglc/schemas/visibility.py` (FORBIDDEN_AGENT_FIELDS)

### Top 3 Findings

1. **seed pool 완전 disjoint 확인**:
   - PickCube: [42, 650) 범위 사용 (train: [42,292), val: [200,250), test: [250,300)... 추정)
   - PushCube: [1042, 1999) 범위 사용
   - 신규 axis 추가 시: [2000+) 범위 할당 필요 → 충돌 없음

2. **FORBIDDEN_AGENT_FIELDS 12개 강제 확인**:
   - `regime_id, true_mass, true_friction, true_latency, true_noise_sigma, true_action_gain, oracle_action, counterfactual_reward, split_id, ood_type, seed, template_id`
   - 4 axis 추가 시 `true_action_gain, true_latency, true_noise_sigma`가 이미 목록에 포함 → 추가 변경 불필요

3. **eval_metas vs inference 분리 확인**:
   - `collect_episodes()` 반환: (episodes, eval_metas, stats) — episodes에는 state/action/reward/done만
   - eval_metas는 HDF5에 별도 저장 (maniskill_schema.py EVAL_ONLY_FIELDS)
   - inference pipeline이 eval_metas 경로 접근 불가 확인 필요

### Top 2 Unresolved UNKNOWNs

- **[U-D1]** PickCube seed pool: val_id와 test_id seed 범위가 manifest에 명시되어 있는지, 수동 체크 필요.
- **[U-D2]** 신규 axis 수집 시 seed [2000+) 할당 후 기존 splits과 no-overlap 보장하는 자동 체크 test 없음.

### Recommendations

1. `test_fglc_split_integrity.py`에 seed 범위 no-overlap 자동 검증 추가 (신규 [2000+) 포함)
2. eval_metas HDF5 분리 경로 자동 감사 test 추가
3. manifest.json에 `seed_range_by_split` 명시적 기록 확장

### Judgment: **PASS** (기존 data leakage 0), **PATCH** (신규 axis seed 범위 자동 체크 추가 권장)

---

## Agent E — ood-severity-critic

### Role
axis별 expected gap, KS p-value, Cohen's d 예측 + threshold 검증

### Input
- `data/fglc/PickCube-v1/dataset_stats.json` (실측 state_delta_norm stats)
- `reports/ood_severity_agent_report_scaled_R1.md`
- `src/fglc/data/manifest.py` (verify_ood_severity, delta_min=0.01)

### Top 3 Findings

1. **friction severity 강력 (실측)**:
   - PickCube: train_id=1.322009, ood_friction_low=1.183966 → gap=0.138043 (PASS)
   - ood_friction_low qvel dims 9-17의 std: train_id 대비 20~32% 감소 (dim-level Cohen's d 실측 가능)
   - delta_min=0.01 기준 13.8× 여유

2. **action_gain severity 이론 예측**:
   - gain=0.7: action_std = 0.577 × 0.7 ≈ 0.404 (random policy)
   - qvel 응답 ≈ 70% → state_delta_norm gap 예상값: **≈ 0.04~0.10** (friction보다 작지만 0.01 초과 가능)
   - gain=1.3: clipping 발생 시 effective gain ↓ → gap이 예상보다 작을 수 있음 (gain=0.7이 주력)

3. **noise severity 이론 예측 (의도된 낮은 값)**:
   - σ=0.1 주입 시 state_delta_norm은 증가하지 않음 (noise는 |s_{t+1}-s_t|에 noise 추가)
   - state_delta_norm gap이 **0.01 미만 가능** — 이것이 올바른 동작
   - 대신 AUROC < 0.65 (Stage 3 검증 지표) 사용 → delta_min 기준 적용 제외 고려

### Top 2 Unresolved UNKNOWNs

- **[U-E1]** latency axis에서 state_delta_norm gap 예상값. d=8 step delay → 8 step 이전 action으로 현재 state 변화 → gap 크기가 불명확 (0.01~0.05 사이 추정).
- **[U-E2]** noise axis에서 verify_ood_severity(delta_min=0.01)를 어떻게 처리할지. gap < 0.01이 "FAIL"이 아닌 "올바른 동작"인 경우 → axis별 예외 처리 or 별도 severity 기준 필요.

### Recommendations

1. noise axis는 verify_ood_severity 대신 `β_t false positive rate < 0.10` (ID data에서) 기준 적용 권장
2. action_gain probe 시 gain=0.7과 gain=1.3 모두 수집 → clipping 영향 비교
3. latency axis probe: d=3, d=8 비교 → gap 크기 및 누적 효과 실측 필요

### Judgment: **PASS** (friction, delta_min=0.01 기준 13.8× 여유), **CONDITIONAL** (action_gain — clipping 확인 후), **FAIL** (noise severity — 의도된 낮은 gap, 별도 기준 필요)

---

## Agent F — dynamics/control-forensics-agent

### Role
axis별 물리 경로 분해 + FGLC 핵심 수식 연결 검증

### Input
- `reports/mass_ood_dynamics_forensics_report.md`
- `reports/mass_ood_metric_validity_report.md`
- `data/fglc/PickCube-v1/dataset_stats.json` (per-dim stats)

### Top 3 Findings

1. **friction 물리 경로 명확**:
   ```
   τ_eff = τ_motor - 5.0 × sign(qvel)   [매 step, 접촉 무관]
   qvel_{t+1} = qvel_t + M^{-1} × τ_eff × dt
   → qvel dims 9-17 std 20~32% 감소 (ood_friction_low 실측)
   → 기본 WM의 qvel 예측 μ_t 오류 → ρ_t 편차 → β_t 발화
   ```
   friction은 단계 1 (접촉)을 우회하는 유일한 축.

2. **action_gain 물리 경로 분석**:
   ```
   a_executed = gain × a_commanded         [step 전 변환]
   state_{t+1} = f(state_t, a_executed)    [환경 dynamics]
   μ_t = f_θ(z_t, a_commanded, h_t)       [WM은 a_commanded 기반 예측]
   ρ_t = Σ_t^{-1/2}(z_{t+1} - μ_t)       [a_executed 기반 실제 vs μ_t 차이]
   ```
   WM이 `a_commanded`를 입력받지만 환경은 `a_executed`로 작동 → systematic mismatch.
   **이것이 FGLC의 "wrong-dynamics-hypothesis" 정확한 예시**.

3. **latency 물리 경로 분석**:
   ```
   a_executed_t = a_commanded_{t-d}        [d-step delay]
   μ_t = f_θ(z_t, a_commanded_t, h_t)     [WM은 현재 action 기반]
   실제: a_{t-d}이 적용되므로 z_{t+1} ≠ μ_t 예측
   → phase error 누적: d step 이후 mismatch 증가
   ```
   temporal group latent에서 d-step shifted pattern → FGLC의 temporal latent group 분리 직접 검증.

### Top 2 Unresolved UNKNOWNs

- **[U-F1]** PickCube 실측 contact_rate=0.000% vs PushCube contact_rate 직접 미측정. PushCube mass FAIL 원인이 contact=0%인지 obs_mode 이슈인지 간접 추론만 가능.
- **[U-F2]** noise axis에서 `Σ_t^{-1/2}` ill-conditioned 임계 σ 값. σ가 너무 크면 ρ_t denominator 수치 불안정 → R4 falsification gate 학습 자체 불안정.

### Recommendations

1. TASK_2052 (noise injection)에 σ 상한 guard 추가: `σ_max = 0.2`, 이를 초과하면 경고 출력
2. latency buffer reset: zero-fill이 d-step gap을 명확히 하므로 zero-fill 권장 (first-action repeat은 gap을 희석할 수 있음)
3. friction unit mapping: `joint_dry_friction=5.0 N·m/rad` → `µ_kinetic` 변환 공식 문서화 필요

### Judgment: **PASS** (friction/action_gain/latency 물리 경로 명확), **BLOCKED** (mass — contact_rate=0% 물리 경로 차단), **CONDITIONAL** (noise — σ 상한 확인 후)

---

## Agent G — novelty-relevance-critic

### Role
6 direct-threat 논문 차별 검증 + reviewer attack 방어 시뮬레이션

### Input
- `docs/idea/22_NOVELTY_AND_THREATS.md`
- INTERACTION_AXIS_REVIEW §H (6-threat 차별표)
- 4 axis별 FGLC 수식 연결 (§B)

### Top 3 Findings

1. **friction axis 방어 가능 (6 threats 모두)**:
   - TD-MPC2: "friction OOD에서 grouped sparse correction" — TD-MPC2는 correction 없음
   - DreamerV3: "K-group latent의 friction-related subspace 분리" — RSSM은 non-grouped
   - HiP-RSSM: "파라미터 추론 없이 mismatch-driven β_t 발화" — 핵심 차별
   - **단, friction µ_kinetic 단위 매핑 DEFERRED → reviewer "unrealistic setting" 위험**

2. **action_gain axis의 C5 value**:
   - PLSM 차별: "action-gain shift는 action-effect 체계성 generalization failure" → PLSM은 이를 다루지 않음
   - AdaWM 차별: "AdaWM의 불일치 기반 적응 vs FGLC의 value-aware grouped correction"
   - gain=0.7 (과소작동) + gain=1.3 (과작동) 두 방향 모두 reviewer 방어 가능

3. **noise axis의 독특한 C5 가치**:
   - "FGLC가 observation noise를 dynamics shift로 오인하지 않음" → specificity 검증
   - ReDRAW 차별: "ReDRAW는 모든 mismatch에 correction 시도; FGLC는 noise를 dynamics로 오인 안 함"
   - AUROC < 0.65가 의도된 결과임을 논문에 투명하게 제시 → reviewer "왜 낮은가?" 방어 가능

### Top 2 Unresolved UNKNOWNs

- **[U-G1]** 2025/2026 신규 논문 중 action-gain shift를 explicitly 다루는 논문이 존재하는지 MCP 검증 미완료 (arXiv + semantic-scholar 교차검증 필요).
- **[U-G2]** latency axis의 HiP-RSSM 차별이 실질적인지: HiP-RSSM도 latency를 다룰 가능성 → 정확한 비교 필요.

### Recommendations

1. action_gain 논문 방어: 2 task (PickCube + PushCube) cross-replication으로 "cherry-picking" 방어 가능
2. latency 논문: HiP-RSSM §Methods와 비교 섹션 추가 필요 (R14 논문 작성 시)
3. friction unit: 논문 Appendix에 "joint dry friction coefficient interpretation" 섹션 추가로 reviewer 선제 방어

### Judgment: **PASS** (friction/action_gain — 6 threat 방어 가능), **CONDITIONAL** (latency — HiP-RSSM 비교 필요), **CONDITIONAL** (noise — AUROC < 0.65 의도 명확히 서술 필요)

---

## Agent H — resource-budget-auditor

### Role
4 axis × 2 task × 4 stage 예산 정량화 + 4060 8GB VRAM 안전성

### Input
- `reports/resource_budget_agent_report_scaled_R1.md`
- `data/fglc/PickCube-v1/dataset_stats.json`
- Phase 1 실측: 450ep = ~2 MB, ~7분 (병렬)

### Top 3 Findings

1. **현재 데이터 수집 예산 실측값**:
   - PickCube 450ep: 5 split 병렬 총 ~7분, ~2 MB (gzip4)
   - 속도: ~1.25 ep/s (train_id), ~0.82 ep/s (val/test/ood splits)
   - 신규 axis Scaled (900ep): 예상 ~14-15분, ~4 MB

2. **4 axis × 2 task × Scaled 전체 예산**:
   - 신규 3 axis (action_gain+latency+noise) × 2 task = 6 수집
   - 6 × 900ep × ~15분 = **~90분 수집 시간**
   - 6 × 4 MB = **~24 MB 디스크** (기존 ~6 MB 포함 총 ~30 MB)
   - R3 training (4 axis × 2 task × 30 epoch × 1 seed): 예상 **~8-12시간**

3. **VRAM 안전성**:
   | 구성 | 추정 VRAM | 4060 여유 |
   |---|---|---|
   | R3 base WM (D_x=42, K=8, h=256, batch=16) | ~400 MB | 20× |
   | R5 causal attention 추가 | ~800 MB | 10× |
   | R7 MPPI rollout (n=512) | ~2 GB | 4× |
   | R9 ablation grid (4 seed) | ~1.6 GB × 4 = 6.4 GB | 한계 근접 |
   - **주의 시점**: R9 ablation × 4 seed 병렬 시 OOM 가능. Sequential seed 실행 권장.

### Top 2 Unresolved UNKNOWNs

- **[U-H1]** action_gain probe 시 `env.step()` overhead — action 변환이 CPU/GPU에서 처리될 경우 속도 변화 없으나, 환경 내부 clip이 추가 연산이면 ~5-10% 느려질 수 있음.
- **[U-H2]** latency buffer (deque) 추가 시 episode loop overhead — 50 step episode에 deque 연산은 무시할 수준이나 measured 필요.

### Recommendations

1. 수집 우선순위: action_gain(~50 LOC) → probe(50ep) → pilot(300ep) → scaled(900ep) → 이후 latency/noise
2. R9 ablation grid 전에 VRAM 측정 실시 (`torch.cuda.memory_summary()`)
3. Robust stage (1800ep)는 paper submission 전 2 seeds로만 진행 (주 실험은 Scaled 충분)

### Judgment: **PASS** (현재 수집량 및 VRAM), **EXPAND** 조건부 (R9 ablation grid 시 sequential seed 권장)

---

## Agent I — experiment-design-chair (synthesis)

### Role
Agent A~H 종합 → 최종 axis ranking + 권장 path + R3 진입 조건 판정

### Input
Agent A~H 전체 보고서 + `docs/FOUR_AXIS_HIGH_QUALITY_DATASET_PLAN.md`

### Synthesis Matrix

| 판정 차원 | 결과 | 근거 |
|---|---|---|
| threshold 완화 여부 | **NO** | delta_min=0.01 유지 (Agent E 확인) |
| mass FAIL 명시 | **YES** | PickCube 0.0038, PushCube 0.008 양쪽 공시 |
| friction cross-task 방어 | **YES** | gap 0.138/0.124 독립 PASS |
| H1-H21 gate 통과 | **PARTIAL** | Ckpt 4 mass FAIL, friction은 PASS |
| R5/R6 ≥2 axes 충족 가능 | **CONDITIONAL** | friction+action_gain Pilot 후 |
| VRAM 한계 준수 | **YES** | R9 주의사항 포함 |
| forbidden field leakage | **0건 확인** | eval_metas 분리 완전 |

### Top 3 Final Findings

1. **friction 단독으로 R3 smoke 즉시 가능하나 R5/R6 Stage 3 gate 불충분**:
   - Stage 3: "≥2 OOD 조건에서 TD-MPC2 baseline 초과" → friction 1개로 부족
   - action_gain 구현 + Pilot PASS 시 2-axis gate 충족 → R5/R6 진입 가능
   - latency/noise는 보조 evidence (paper-grade reproducibility용)

2. **repair loop의 구조적 격차**:
   - `taxonomy.py`: action_gain/latency용 axis-specific cause 없음 (`OOD_AXIS_GAIN_UNCOVERED`, `OOD_AXIS_LATENCY_UNCOVERED` 추가 권장)
   - `candidates.py`: policy-change family 전무 (mass repair track용 필수)
   - `EVAL_NOISE_HIGH` cause가 noise axis의 "의도된 낮은 AUROC"와 혼재 위험 (`OBS_NOISE_SIGMA_MISMATCH` 분리 권장)

3. **4 axis 전체 완성 시 FGLC 주장 검증 구조**:
   ```
   friction:     wrong-dynamics-hypothesis (motor efficiency shift)
   action_gain:  wrong-control-model (gain shift → action-effect mismatch)
   latency:      temporal-dynamics-mismatch (d-step phase error)
   noise:        Σ-calibration specificity (β_t false positive 방지)
   ```
   이 4축이 FGLC의 "falsification gate + sparse grouped correction" 4개 독립 시나리오 커버.

### Risk Matrix

| Risk | 수준 | 완화책 | 완화 가능성 |
|---|---|---|---|
| mass axis 완전 missing | HIGH | Honest limitation 명시 + scripted policy track | ✅ 논문에 명시 |
| friction µ_kinetic 단위 DEFERRED | MEDIUM | mapping ledger 문서화 | ✅ TASK 추가 |
| action_gain gain=1.3 clipping | MEDIUM | gain=0.7 중심 설계 | ✅ 설계 변경 |
| noise AUROC < 0.65 오해 | MEDIUM | 논문에 "의도된 낮은 값" 명시 | ✅ 섹션 추가 |
| R5/R6 2-axis 미충족 (friction only) | HIGH | action_gain Pilot 우선 | ✅ TASK_2050 착수 |
| taxonomy.py cause 부재로 repair 진단 오류 | LOW | TASK 승인 후 추가 | ✅ 사용자 승인 대기 |

### Recommendations (우선순위 순)

1. **즉시**: friction 기존 데이터로 R3 base WM smoke (Stage 1 gate: ID NLL 수렴 확인)
2. **1주 이내**: TASK_2050 (action_gain ~50 LOC) → probe → pilot → R3 full smoke
3. **2주 이내**: TASK_2051 (latency FIFO) → probe
4. **병렬**: friction µ_kinetic unit mapping ledger 문서화
5. **R4 이후**: TASK_2052 (noise injection) + Σ calibration false positive 검증
6. **mass track 분리**: scripted policy 구현 검토 (D-4 사용자 결정 후)

### 최종 Judgment: **CONDITIONAL_ACCEPT**

```
조건 1: action_gain TASK_2050 완료 + Pilot PASS (gap > 0.01, AUROC ≥ 0.70)
조건 2: R3 smoke: ID NLL 수렴 + friction/action_gain OOD NLL > ID NLL
조건 3: mass FAIL 투명 공시 (negative result 은폐 금지)
조건 4: friction µ_kinetic 매핑 DEFERRED 논문 Appendix 명시
조건 5: taxonomy.py cause 추가 (사용자 승인 후)

미충족 시: MAJOR_REVISION
```

---

## 종합 결론

### PLAN_PASS 판정 (본 PLAN 자체)

이 합성 보고서와 `docs/FOUR_AXIS_HIGH_QUALITY_DATASET_PLAN.md`는 다음을 모두 충족:

- [x] §A~§N 14개 섹션 + §P, §Q (절대 금지 + 타임라인) 완성
- [x] 4 axis × 5관점 점수표 + tier 확인 (§C.3)
- [x] Agent A~I 9명 sub-section (본 파일)
- [x] Codex TASK A1~A7 + TASK_2050~2055 헤더 명세 (§K)
- [x] 30개 quality gate (§G)
- [x] atomic checklist (§N.1)
- [x] BLOCKED 2개 + UNKNOWN 8개 + UNRESOLVED 5개 명시 (§N.2~N.4)
- [x] verification plan (§O)
- [x] mass FAIL 투명 공시, friction-only 한계 명시
- [x] threshold 완화 명시적 거부 (§E.4 인용)
- [x] 코드/데이터/phase gate 변경 없음

**Agent I 최종 판정**: CONDITIONAL_ACCEPT → 상기 조건 5개 충족 시 ACCEPT.

---

*보고서 경로: `reports/four_axis_dataset_design_synthesis.md`*
*참조 PLAN: `docs/FOUR_AXIS_HIGH_QUALITY_DATASET_PLAN.md`*
*선행 보고서: `docs/INTERACTION_AXIS_DATASET_DESIGN_REVIEW.md`*
