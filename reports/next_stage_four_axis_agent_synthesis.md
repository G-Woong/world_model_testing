# Next-Stage Four-Axis Dataset — Agent Synthesis Report

> **작성일**: 2026-05-24
> **Phase**: R2 완료 → EXECUTION PLAN 진입 전
> **Branch**: `memory-redesign-2026-05-16`
> **선행 DESIGN**: `docs/FOUR_AXIS_HIGH_QUALITY_DATASET_PLAN.md` (commit `6f48d67`)
> **선행 SYNTHESIS**: `reports/four_axis_dataset_design_synthesis.md` (Agent I CONDITIONAL_ACCEPT × 5조건)
> **본 문서 목적**: EXECUTION PLAN (`docs/NEXT_STAGE_FOUR_AXIS_DATA_COLLECTION_EXECUTION_PLAN.md`) 검토 — 각 Agent가 axis 구현 순서, STOP 조건, repair loop, R3 smoke 연결의 타당성을 심사
> **판정 요약**:
> - Agent I (synthesis chair): **CONDITIONAL_ACCEPT** (TASK_2050 verify + action_gain Pilot PASS + R3 smoke OK)
> - 즉시 PASS: friction (기존 gap 0.138/0.124), Stage 0 체크리스트
> - 구현 후 검증: action_gain (PRIMARY), latency (SECONDARY), noise (SPECIFICITY)
> - BLOCKED: mass (별도 contact-rich policy track)

---

## Agent A — axis-implementation-auditor

### Role / Input / Output

**역할**: 3 신규 axis 구현 격차 심사 + 구현 순서 타당성 + Codex 위임 feasibility

**Input**:
- `src/fglc/data/collector.py` (L66-89 `_apply_ood`, L147-199 episode loop)
- `src/fglc/data/maniskill_schema.py` (REGIME_ID, TASK_OOD_PARAMS)
- `configs/fglc/` (3개 yaml)
- `tests/test_fglc_*.py` (24개 목록)

**Output**: 구현 격차 표 + TASK 2050/2053/2054 타당성 + Gatekeeper 체크리스트

### Top 3 Findings

1. **action_gain (~50 LOC) 즉시 실행 가능**:
   - collector.py L89 직후, `_apply_ood()` 마지막 줄 이후에 분기 삽입 가능
   - maniskill_schema.py TASK_OOD_PARAMS dict에 literal key 추가만으로 충분
   - REGIME_ID는 int 값 추가 (~2 줄) — BACKBONE 등급 3 (사용자 승인 불필요)
   - 단, `env.step()` 내부 clip 위치 불명 [U-A1] → 1-step probe로 즉시 해결 가능

2. **latency FIFO buffer (~40 LOC)는 episode loop 수준 변경**:
   - `_apply_ood()`는 env.reset() 후 state 설정용 — latency buffer는 별도 구현 필요
   - `deque(maxlen=d)` + zero-fill reset: Python stdlib, 의존성 추가 없음
   - commanded/executed 이중 기록: eval_metas에 추가 key → FORBIDDEN 필드 12개와 충돌 없음 (`commanded_actions`는 eval-only, inference path 불접근)

3. **noise injection (~15 LOC)은 가장 단순**:
   - `_flat_obs(obs)` 반환값에 직접 덧셈 → 1~2 줄 코어 변경
   - per-episode `np.random.default_rng(seed)`: stdlib, 재현성 보장
   - σ upper bound guard (0.15/0.2): 1 if-else → test에서 검증 가능

### Top 2 Unresolved UNKNOWNs

- **[U-A1]** ManiSkill 3.0.1 `env.step(a)` 내부에서 action clip 발생 여부. gain=1.3 시 `[-1,1]` space에서 effective gain < 1.3이 될 수 있음. → 해결: 1-step probe `print(a_before, a_after_step)` 비교
- **[U-A2]** latency buffer가 `_apply_ood()` 내부에 있으면 reset 시마다 deque가 초기화됨 — episode loop 밖 구현 필요. TASK_2053 FILES_ALLOWED에 episode loop 수준 코드 포함 확인 필요.

### Recommendations

1. TASK_2050: Codex 위임 권장 (3파일 동시 수정 → codex_orchestration_rules.md 트리거 (a))
2. TASK_2050 전 ManiSkill action clipping 위치를 1-step probe로 확인 (Claude 직접, ~5분)
3. TASK_2053 FIFO: `collector.py` episode while loop 시작 직전 `buffer = deque([np.zeros(D_a)] * delay, maxlen=delay)` 패턴 사용

### Judgment: **PATCH_REQUIRED**

TASK_2050~2054 완료 후 → **PASS** 전환 기대.
U-A1 해결 전 action_gain Pilot 진입 금지.

### Trigger for re-invocation

- post-TASK_2050 (action_gain 구현 후 diff review)
- post-TASK_2053 (latency 구현 후 diff review)
- post-TASK_2054 (noise 구현 후 diff review)

---

## Agent B — data-quality-gatekeeper

### Role / Input / Output

**역할**: 30개 quality gate 측정 계획 + reject reason 모니터링 + axis별 validator 확장 필요성

**Input**:
- `src/fglc/data/validators.py` (10개 EpisodeRejectReason)
- `src/fglc/data/manifest.py` (verify_ood_severity, delta_min=0.01)
- `data/fglc/PickCube-v1/quality_report.json` + `data/fglc/PushCube-v1/quality_report.json`

**Output**: 기존 데이터 gate 상태 + 신규 axis gate 확장 계획

### Top 3 Findings

1. **기존 friction 데이터 gate 상태 확인**:
   - PickCube 450ep / PushCube 900ep: n_rejected=0 (accept rate 100%), H1-H21 PASS
   - hash 중복 0건 (intra + inter)
   - Ckpt 4 FAIL은 mass에 의한 것 — friction 개별 H22는 gap=0.138 PASS (delta_min 기준 13.8×)
   - Ckpt 5/6/9=SKIP: learnability/repair_metric/novelty — R3 smoke 후 평가 예정

2. **신규 axis validator 추가 권장**:
   - action_gain: action_std 감소 validator (`a_std_ood < a_std_id × 0.95` for gain=0.7)
   - latency: executed ≠ commanded validator (첫 d step에서 executed = zero)
   - noise: state_std 증가 validator (`s_std_ood > s_std_id` for σ=0.1 기대)
   - 이 3개 validator는 기존 10개 reject reason과 별개 — `TASK_2050/2053/2054` 내 test에 포함

3. **noise axis gate 특수 처리**:
   - H22 (ood_severity: gap > 0.01) → noise에는 적용 불가 (gap ≈ 0이 올바른 결과)
   - 대체 gate: AUROC < 0.65 (Stage 3/R4 이후 측정 가능) + β-gate FPR < 0.05
   - 이 대체 gate는 `quality_report.json`의 `noise_specificity_check` key로 별도 기록 권장

### Top 2 Unresolved UNKNOWNs

- **[U-B1]** action_gain=1.3 clipping 발생 시 action_std가 오히려 증가할 수 있음 (clipping 전 gain × std 계산). validator 기준 방향 확인 필요.
- **[U-B2]** noise σ=0.2 시 constant_state reject reason 발생 가능성 (noise가 state 변화를 마스킹하지 않는다면 reject 없음, 그러나 edge case 확인 필요).

### Recommendations

1. `quality_report.json`을 axis별로 분리: `{"friction": {"Ckpt4": "PASS", ...}, "mass": {"Ckpt4": "FAIL", ...}}`
2. 신규 axis별 validator 3개 → `TASK_2050/2053/2054` 각 test 내 포함 (별도 TASK 불필요)
3. H22 noise 예외 처리를 manifest.py에 axis flag로 구현 권장 (`verify_ood_severity(skip_axes=["noise"])`)

### Judgment: **PASS (friction 기존)** / **PATCH_REQUIRED (신규 axis validator 추가 필요)**

### Trigger for re-invocation

- post-Stage 1 (probe 수집 후)
- post-Stage 2 (pilot 수집 후)
- post-Stage 3 (scaled 수집 후)
- post-Stage 4 (robust 수집 후)

---

## Agent C — split-leakage-auditor

### Role / Input / Output

**역할**: seed pool disjoint 확인 + 신규 axis seed 범위 할당 + forbidden field leakage 0건 보증

**Input**:
- `data/fglc/PickCube-v1/manifest.json` (seed_pool [42~650))
- `data/fglc/PushCube-v1/manifest.json` (seed_pool [1042~1999))
- `tests/test_fglc_split_integrity.py`
- `src/fglc/schemas/visibility.py` (FORBIDDEN_AGENT_FIELDS 12개)

**Output**: seed 충돌 위험 분석 + 신규 axis seed 범위 제안

### Top 3 Findings

1. **기존 seed pool 완전 disjoint 확인**:
   - PickCube: [42, 650) 범위 — train/val/test/ood_* 포함
   - PushCube: [1042, 1999) 범위 — 충돌 없음
   - 신규 axis 수집 시: [2000, 2999) 범위 할당 → PickCube/PushCube 모두 안전
   - trajectory hash 중복: 0건 (기존 데이터 기준)

2. **FORBIDDEN_AGENT_FIELDS 12개와 3 axis 추가 호환**:
   - `true_action_gain, true_latency, true_noise_sigma` 이미 12개 목록에 포함
   - 신규 axis 추가 후 `tests/test_fglc_forbidden_field_sync.py` green 유지 예상 (추가 변경 없음)
   - eval_metas 분리: `collect_episodes()` 반환 (episodes, eval_metas, stats) 패턴 유지

3. **신규 seed pool [2000+) 자동 no-overlap test 부재**:
   - `test_fglc_split_integrity.py`는 현재 PickCube/PushCube 기존 seed만 체크
   - action_gain seed [2000+) 추가 시 기존 [42,650) + [1042,1999)와 no-overlap 자동 검증 없음
   - TASK_2050~2054 각 test에 seed no-overlap assertion 포함 권장

### Top 2 Unresolved UNKNOWNs

- **[U-C1]** PickCube manifest.json의 split별 seed 범위 정확한 끝값 (manifest 직접 read 필요 — Stage 0 audit).
- **[U-C2]** 동일 random policy + 동일 seed → 동일 trajectory 가능성. action_gain axis의 gain=0.7과 gain=1.0(ID)이 같은 seed [42]로 수집 시 state 시작점 동일 → leakage 아니나 trajectory 상관성 존재 (통계 독립성 약화 가능).

### Recommendations

1. 신규 axis seed: `[2000, 2499]` (PickCube gain), `[2500, 2999]` (PushCube gain) 할당 제안
2. `test_fglc_split_integrity.py`에 전체 seed pool union의 disjoint 자동 검증 추가 (TASK_2050 내 포함)
3. trajectory hash 중복: 신규 axis × 기존 axis cross-hash 체크도 H8에 추가

### Judgment: **PASS (기존 leakage 0건)** / **PATCH_REQUIRED (신규 seed 범위 자동 체크 추가 필요)**

### Trigger for re-invocation

- post-Stage 2 (pilot seed pool 추가 후)
- post-Stage 3 (scaled seed pool 추가 후)

---

## Agent D — ood-severity-critic

### Role / Input / Output

**역할**: axis별 expected gap 예측 + delta_min 기준 적용 가능성 + noise 특수 처리

**Input**:
- `data/fglc/PickCube-v1/dataset_stats.json` (state_delta_norm stats)
- `data/fglc/PushCube-v1/dataset_stats.json`
- `src/fglc/data/manifest.py` (verify_ood_severity, delta_min=0.01)

**Output**: axis별 severity 예측 + 판정 기준 + 실패 시 repair 경로

### Top 3 Findings

1. **friction severity 실증 강력**:
   - PickCube: train_id=1.322009, ood_friction_low=1.183966, gap=0.138043 (PASS, 13.8×)
   - PushCube: gap=0.124 PASS
   - 기존 데이터 재사용 가능, 재수집 불필요, R3 smoke 첫 번째 axis 준비 완료

2. **action_gain severity 이론 예측 (probe 전)**:
   - gain=0.7: action_std = 0.577 × 0.7 ≈ 0.404 (random policy 가정)
   - qvel 응답 ≈ 70% → state_delta_norm gap 예상: **0.04~0.10** (friction보다 작지만 0.01 충분히 초과)
   - gain=1.3: ManiSkill clip 발생 시 effective gain < 1.3 → gap이 0.7보다 작을 수 있음 → gain=0.7 PRIMARY 확정 타당
   - 이론 예측: gap > 0.01 가능성 **높음** (70~80% 신뢰)

3. **noise severity는 delta_min 기준 적용 불가 (의도된 낮은 gap)**:
   - σ=0.1 주입 시 dynamics 변화 없음 → state_delta_norm gap ≈ 0 (noise가 |s_{t+1}-s_t|에 더해지나 dynamics path는 동일)
   - gap < 0.01이 FAIL이 아닌 **올바른 동작**
   - 대체 기준: AUROC(β_t 발화) < 0.65 + β-gate FPR < 0.05
   - `manifest.py::verify_ood_severity` 호출 시 `skip_axes=["noise"]` 옵션 필요

### Top 2 Unresolved UNKNOWNs

- **[U-D1]** latency axis expected gap (d=5 시): d-step delayed action → cumulative phase error → state_delta_norm gap 범위가 0.01~0.15 사이로 불명확. probe 후 실측 필요.
- **[U-D2]** noise axis에서 `verify_ood_severity(delta_min=0.01)` 호출 시 false FAIL 방지. manifest.py에 axis_skip 파라미터 없으면 noise는 항상 Ckpt4=FAIL 기록 → misleading.

### Recommendations

1. `manifest.py::verify_ood_severity`에 `noise_axis_skip=True` 파라미터 추가 권장 (TASK_2054 내 포함)
2. action_gain probe: gain=0.7 우선, gain=1.3은 secondary (clipping 확인 후)
3. latency probe: d=3 / d=8 비교 → gap 크기 및 누적 효과 실측 후 Pilot 파라미터 결정

### Judgment: **PASS (friction)** / **CONDITIONAL_PASS (action_gain — probe 후 결정)** / **CONDITIONAL_PASS (latency — probe 필요)** / **SPECIFICITY_TEST (noise — delta_min 기준 미적용)**

### Trigger for re-invocation

- post-Stage 1/2/3/4 (axis별 probe/pilot/scaled/robust 후)
- R3 smoke 전 (axis별 severity 확인 최종)

---

## Agent E — dynamics-control-forensics-agent

### Role / Input / Output

**역할**: axis별 물리 경로 분해 + FGLC 핵심 수식 연결 + contact_rate 분석 + latency phase error 패턴

**Input**:
- `reports/mass_ood_dynamics_forensics_report.md` (mass contact_rate=0% 실측)
- `data/fglc/PickCube-v1/dataset_stats.json` (per-dim stats)
- DESIGN §F Agent F findings

**Output**: axis별 FGLC 수식 경로 + 신규 axis dynamics 가설 검증 계획

### Top 3 Findings

1. **friction/action_gain/latency: contact 무관 dynamics shift 확인**:
   ```
   friction:    τ_eff = τ_motor - 5.0 × sign(qvel)  → qvel 직접 영향 (접촉 불필요)
   action_gain: a_executed = gain × a → WM 입력 a_commanded와 실제 a_executed 불일치
   latency:     a_executed_t = a_commanded_{t-d} → temporal mismatch
   ```
   세 축 모두 random policy에서도 gap 발생 가능 (mass와 근본적으로 다름)

2. **latency phase error 패턴 이론**:
   - d=5 delay: step 5 이후부터 실제로 commanded_t-5 적용
   - episode 전반부: d step 동안 zero action (zero-fill) → 초기 gap 발생
   - episode 후반부: 누적 phase error → qvel / ee_pos 예측 오류 증가
   - 관측 가능 패턴: `per_step_gap[t>d] > per_step_gap[t<d]` → FGLC latent group 분리 증거

3. **noise axis: Σ_t ill-conditioning 위험**:
   - σ가 클수록 obs noise가 Σ_t의 diagonal에 추가됨 (WM이 noise를 model에 포함하려 할 수 있음)
   - σ=0.2에서 Σ_t^{-1/2} ill-conditioned 위험 → ρ_t 폭발 가능
   - σ_max=0.15 권장 이유: Σ calibration 안정 범위 내 유지

### Top 2 Unresolved UNKNOWNs

- **[U-E1]** PushCube-v1 contact_rate 직접 미측정. mass FAIL 원인이 contact=0%인지 obs_mode 이슈인지 간접 추론만 가능. → 해결: probe 시 contact 관련 info key 기록
- **[U-E2]** noise axis: WM이 훈련 중 σ를 추정하려 할 경우 Σ_t에 σ 성분이 흡수 → R4 falsification gate 학습 영향 불명확. → 해결: R4 이후 실측 필요

### Recommendations

1. action_gain probe 직후 per-dim Cohen's d 분석: action-induced velocity dims (qpos/qvel 9-17)
2. latency probe: episode 전반 vs 후반 step gap 비교 기록 → `dataset_stats.json`에 `gap_per_step` 추가 권장
3. noise: σ_max=0.15 guard 구현 (TASK_2054 acceptance criteria에 포함)

### Judgment: **PASS (friction/action_gain/latency 물리 경로 명확)** / **BLOCKED (mass contact_rate=0%)** / **CONDITIONAL (noise σ_max guard 후)**

### Trigger for re-invocation

- post-Stage 1 (probe 수집 후 per-dim 분석)
- Stage 2 Agent D FAIL 시 (forensics 심층 분석)

---

## Agent F — claim-metric-alignment-auditor

### Role / Input / Output

**역할**: axis → 4축 metric 1:1 매핑 검증 + 누락 metric 탐지 + noise specificity metric framework 설계

**Input**:
- `docs/idea/04_BASE_WORLD_MODEL.md` (encoder, K-group, dynamics μ/Σ)
- `docs/idea/10_LOSS_DESIGN.md` (Stage 1/2 losses)
- `docs/idea/21_METRICS.md` (4축 metric + thresholds)
- `src/fglc/repair/taxonomy.py` (20 FailureCauseId)

**Output**: axis × 4축 metric 매핑 표 + noise specificity framework

### Top 3 Findings

1. **friction → 4축 metric 완전 매핑 (실증 가능)**:
   - Axis 1 (예측 NLL): OOD NLL > ID NLL ← gap=0.138 실증
   - Axis 2 (탐지 AUROC): β_t 발화 ↔ `regime_id` eval label → AUROC ≥ 0.75 기대
   - Axis 3 (attribution nec-suf): qvel dims necessity/sufficiency 검증 가능
   - Axis 4 (control return): friction shift → planner return 감소 → FGLC 회복

2. **action_gain → C2 (value-aware correction) 최강 검증**:
   - `∇_z V` 방향 = action-relevant latent group → α_t value-aware 특성 직접 검증
   - gain=0.7 vs ID: action → state transition 변화 → μ_t 예측 오류 → ρ_t 편차 → β_t → α_t
   - 4축 모두 signal 예상 (friction보다 Axis 4 control return signal 더 강할 수 있음)

3. **noise specificity metric framework 정의**:
   ```
   noise axis 검증 목적: β_t가 dynamics shift를 올바르게 탐지하면서 observation noise는 무시
   
   Metric 1: AUROC(β_t, noise_label)
     기대: < 0.65 (β_t가 noise를 dynamics shift로 오인하지 않음)
     실패: ≥ 0.70 → OBS_NOISE_SIGMA_MISMATCH → Σ recalibration
   
   Metric 2: β-gate false positive rate (ID + noise)
     기대: < 0.05 (σ=0.1 기준)
     실패: ≥ 0.10 → β_t oversensitive → conformal calibration 재조정
   
   Metric 3: Σ̂_t / Σ_true ratio
     기대: 0.8~1.2 (올바른 calibration)
     실패: < 0.5 or > 2.0 → SIGMA_CALIBRATION_FAILURE
   
   단, Metric 1/2는 R4 falsification gate 이후 측정 가능 (R3 smoke 단계는 framework 정의만)
   ```

### Top 2 Unresolved UNKNOWNs

- **[U-F1]** latency axis에서 Axis 2 탐지 AUROC 예측: d-step temporal shift가 β_t를 충분히 발화시키는지 불명확. FGLC가 temporal pattern을 dynamics shift로 탐지하면 AUROC ≥ 0.75 기대.
- **[U-F2]** R3 smoke 단계에서 noise specificity metric 실측 가능 범위: NLL 측정은 가능하나 AUROC/FPR은 R4 이후에야 측정 가능 (β_t가 R4에서 훈련됨).

### Recommendations

1. R3 smoke 단계: Axis 1 (NLL) 측정만 → noise axis NLL gap ≈ 0 확인 (의도된 결과)
2. R4 이후: noise specificity metric framework 전체 실측 → quality_report.json에 `noise_specificity` 섹션 추가
3. axis × 4축 metric 매핑표를 `docs/idea/21_METRICS.md`에 sub-section으로 추가 권장 (BACKBONE 등급 1 — 사용자 승인 후)

### Judgment: **PASS (friction 4축 완전 매핑)** / **CONDITIONAL (action_gain/latency — Pilot 후 재확인)** / **DEFERRED (noise specificity — R4 이후 측정)**

### Trigger for re-invocation

- post-Stage 2 (pilot 수집 후 claim-metric 재정렬)
- post-R3 smoke (Axis 1 NLL 실측 후)
- post-R4 (noise specificity 전체 실측)

---

## Agent G — novelty-relevance-critic

### Role / Input / Output

**역할**: 6 direct-threat 차별 + reviewer attack 방어 + action_gain novelty 강화 + noise specificity 논문 framing

**Input**:
- `docs/idea/22_NOVELTY_AND_THREATS.md`
- DESIGN §B Agent G findings
- 6 직접 위협: TD-MPC2, DreamerV3, HiP-RSSM, PLSM, ReDRAW, AdaWM

**Output**: axis별 novelty 방어 + reviewer attack 시뮬레이션 결과

### Top 3 Findings

1. **friction 단독은 reviewer "cherry-picking" 공격 위험**:
   - "friction axis만 작동하는 이유가 있는가?" → action_gain + latency 추가로 반박
   - 2 axis (friction + gain) 이상: "서로 다른 물리 메커니즘에서 일관된 성능" → strong rebuttal
   - CONDITIONAL_ACCEPT의 조건 1 (TASK_2050 + Pilot PASS)이 이 reviewer attack 방어에도 직결

2. **action_gain: FGLC 가장 강력한 novelty 증거**:
   ```
   TD-MPC2 vs FGLC: TD-MPC2는 gain shift를 dynamics mismatch로 처리하지 않음
   PLSM 차별: action-effect 체계성 generalization failure가 아닌 action-gain systematic shift
   AdaWM 차별: 불일치 탐지 후 모든 latent 갱신 vs FGLC value-aware grouped sparse correction
   ```
   action_gain은 "wrong-control-model" 시나리오로 FGLC의 grouped sparse correction 필요성을 가장 직접 정당화.

3. **noise specificity: "intentional negative" framing이 핵심**:
   - reviewer "왜 noise에서 AUROC < 0.65인가? 시스템이 작동 안 하는 것 아닌가?" → 의도된 결과임을 명시
   - ReDRAW 차별: "ReDRAW는 모든 mismatch에 correction 시도; FGLC는 noise를 dynamics로 오인하지 않음 (specificity)"
   - 논문 Sec. 4 또는 Appendix에 "Specificity Test" 섹션 추가 → AUROC < 0.65가 올바른 결과 서술

### Top 2 Unresolved UNKNOWNs

- **[U-G1]** 2025/2026 신규 논문 중 action-gain shift를 explicitly 다루는 논문 존재 여부 — MCP arxiv + semantic-scholar 교차검증 필요 (Scaled 단계 후 Agent G 재호출 시 수행).
- **[U-G2]** HiP-RSSM과 latency axis 차별: HiP-RSSM이 parameter inference로 latency도 다루는지 논문 §Methods 직접 확인 필요. 차별점 약화 가능성 있음.

### Recommendations

1. action_gain Scaled PASS 후 MCP 검색: "action gain OOD world model robotics 2025 2026" (arXiv + semantic-scholar)
2. HiP-RSSM 논문 §Methods 직접 읽기 → latency 처리 여부 확인 (R14 논문 작성 전 필수)
3. noise specificity: 논문에 "Robustness Test: Observation Noise Does Not Trigger Falsification Gate" 절로 명시

### Judgment: **PASS (friction/action_gain — 6 threat 방어 가능)** / **CONDITIONAL (latency — HiP-RSSM 비교 필요)** / **CONDITIONAL (noise — framing 주의, AUROC < 0.65 의도 명확 서술 필요)**

### Trigger for re-invocation

- post-Stage 3 (Scaled 후 MCP 교차검증)
- post-Stage 4 (robust 후 reviewer attack 시뮬레이션)
- R14/R15 논문 작성 전 (T5 트리거)

---

## Agent H — resource-budget-auditor

### Role / Input / Output

**역할**: 4 axis × 2 task × 4 stage 예산 정량화 + RTX 4060 8GB VRAM 안전성 + 수집 우선순위

**Input**:
- `§D 자원 계산 기반 수집량 계획` (본 EXECUTION PLAN)
- `data/fglc/PickCube-v1/dataset_stats.json`
- Phase 1 실측: 450ep ≈ 2 MB, ~7분 (5 splits 병렬 불가 → 순차)

**Output**: 수집 우선순위 + VRAM 위험 시점 + 수집 시간 예산

### Top 3 Findings

1. **현재 수집 예산 실측값 (friction 기준)**:
   - PickCube 450ep: 총 ~7분, ~2 MB (gzip4 압축)
   - 수집 속도: ~1.25 ep/s (train_id), ~0.82 ep/s (ood splits)
   - action_gain Pilot (350ep × 2 task): 예상 **~10분, ~8 MB** — 즉시 가능

2. **3 axis 전체 예산**:
   - 3 axis × 2 task × Scaled (1300ep) = 7800 ep
   - 예상: **~3~4 hour 수집, ~160 MB 디스크** — 1 day 내 완료 가능
   - 3 axis × 2 task × Robust (2600ep × 2 seed) = 31200 ep
   - 예상: **~24 hour, ~600 MB** — paper submission 전 2 days 필요

3. **VRAM 분석 (RTX 4060 8GB)**:
   - R3~R7 단계: 최대 ~2 GB (MPPI rollout n=512 포함) → **안전**
   - R9 ablation (11 family × 4 axis × 3 seed): 만약 동시 실행 시 ~6 GB → sequential 필수
   - batch=32로 R3 시작 권장: OOM 없음 확인 후 batch=64 시도

### Top 2 Unresolved UNKNOWNs

- **[U-H1]** action_gain probe 시 env.step() overhead: action 변환이 추가되면 ~5-10% 속도 감소 가능. probe 후 실측 필요.
- **[U-H2]** latency buffer deque 연산 overhead: 50-step episode에서 deque 연산 < 0.1ms — 무시 가능 수준이나 측정 필요.

### Recommendations

1. 수집 우선순위: action_gain Pilot → action_gain Scaled → latency Probe/Pilot → noise Probe/Pilot → (전체 Scaled)
2. R9 ablation grid: sequential seed (seed 0 → seed 1 → seed 2) + `torch.cuda.empty_cache()` 사이에 삽입
3. Robust stage: R5/R6 진입 후 결정 (본 PLAN 범위는 Scaled까지)

### Judgment: **PASS (Pilot/Scaled 예산)** / **EXPAND_AFTER_R3 (Robust는 R5/R6 진입 후 결정)**

### Trigger for re-invocation

- pre-Stage 3 (Scaled 진입 전 예산 재확인)
- pre-Stage 4 (Robust 진입 전)
- pre-R9 (ablation grid 예산 분석)

---

## Agent I — experiment-design-chair (synthesis)

### Role / Input / Output

**역할**: Agent A~H 종합 → EXECUTION PLAN 최종 판정 + CONDITIONAL_ACCEPT 조건 결정

**Input**: Agent A~H 전체 보고서 + `docs/NEXT_STAGE_FOUR_AXIS_DATA_COLLECTION_EXECUTION_PLAN.md`

**Output**: 최종 판정 + CONDITIONAL_ACCEPT 조건 목록 + 사용자 결정 우선순위

### Synthesis Matrix

| 판정 차원 | 결과 | 근거 |
|---|---|---|
| EXECUTION 순서 타당성 | **YES** | gain→latency→noise 조건부 확장 (Agent A/B 확인) |
| threshold 완화 여부 | **NO** | delta_min=0.01 유지 (Agent D 확인) |
| mass FAIL 공시 | **YES** | gap 0.0038/0.008, 별도 contact-rich track |
| friction cross-task PASS | **YES** | gap 0.138/0.124 양쪽 독립 PASS |
| R5/R6 2-axis 충족 경로 | **CONDITIONAL** | friction + action_gain Pilot PASS 시 |
| VRAM 한계 준수 | **YES** | R9 sequential seed 주의 포함 |
| forbidden field leakage | **0건 확인** | eval_metas 분리, FORBIDDEN_AGENT_FIELDS 12개 유지 |
| noise 특수 처리 | **YES** | AUROC < 0.65 의도 명확, delta_min 미적용 |
| TASK 위임 결정 | **CODEX 권장** | TASK_2050 3파일 동시 → Codex 트리거 조건 충족 |

### Top 3 Final Findings

1. **EXECUTION PLAN의 핵심 가치: action_gain이 FGLC "wrong-dynamics-hypothesis" 최직접 예시**:
   - friction: motor efficiency shift (motor τ → qvel)
   - action_gain: control model shift (WM 입력 a_commanded vs 실제 a_executed)
   - latency: temporal dynamics mismatch (d-step phase error)
   - noise: Σ calibration specificity (β_t false positive 방지)
   - 이 4축이 FGLC 4개 독립 시나리오를 커버 → R5/R6 "4-axis evaluation" claim 가능

2. **repair loop 구조적 개선 필요 (BACKBONE 등급 1, 사용자 승인 대기)**:
   - taxonomy.py 4 신규 cause 없으면: action_gain FAIL 시 `OOD_TOO_EASY` (기존)로 오진단 가능
   - `OOD_AXIS_GAIN_UNCOVERED` 분리 → 진단 정확도 향상 + repair candidate 정밀화
   - 단, 기존 20개 cause로도 repair loop 작동 가능 (오진단이지만 functional) — 사용자 D-5 결정 후 추가

3. **noise axis를 FAIL로 처리하는 오류를 명시적으로 방지**:
   - "noise gap ≈ 0 = FAIL" 해석은 FGLC specificity 검증 목적 불이해
   - Agent D/F 모두 noise를 별도 metric으로 분리 권장
   - EXECUTION PLAN §C.4, §F H22, §G.4에 명시 완료 → reviewer 선제 방어 가능

### Risk Matrix

| Risk | 수준 | 완화책 | 완화 가능성 |
|---|---|---|---|
| mass 완전 missing (R5/R6 2-axis 불충분?) | HIGH | friction + action_gain = 2 axes (최소 충족) | ✅ |
| friction µ_kinetic 단위 DEFERRED | MEDIUM | 논문 Appendix 명시 | ✅ |
| action_gain gain=1.3 clipping | MEDIUM | gain=0.7 PRIMARY | ✅ |
| noise AUROC < 0.65 reviewer 오해 | MEDIUM | specificity framing 논문 명시 | ✅ |
| R5/R6 2-axis gate (friction-only 불충분) | HIGH | action_gain Pilot PASS → 충족 | ✅ TASK_2050 우선 |
| taxonomy cause 부재 → 진단 오류 | LOW | 기존 cause로 functional (D-5 후 추가) | ✅ |
| U-A1 clipping 위치 불명 | MEDIUM | 1-step probe (Stage 0 + TASK_2050 전) | ✅ 즉시 해결 가능 |
| HiP-RSSM latency 차별 약화 가능 | MEDIUM | 직접 §Methods 읽기 (R14 전) | ✅ G agent 재호출 |

### Recommendations (우선순위 순)

1. **즉시 (Stage 0)**: friction 기존 데이터 품질 재확인 + U-A1 clipping 위치 1-step probe
2. **D-1~D-7 사용자 결정 요청**: 특히 D-1(axis 순서), D-2(Codex 위임), D-3(latency reset)
3. **TASK_2050 착수 (D-1=(a) 결정 시)**: Codex 위임 + T3 audit + Gatekeeper 6조건
4. **action_gain Pilot PASS 후**: latency 진입 + Agent A/D/E 재호출
5. **Scaled 완료 후**: R3 smoke + Agent F/G 재호출 + 4축 metric 실측

### 최종 Judgment: **CONDITIONAL_ACCEPT**

**EXECUTION PLAN 자체 판정**: **PLAN_PASS**
- §A~§N 14 섹션 완성
- 4 axis 카드 + 25/30 gate 매핑 + 16 repair loop + TASK 2049~2056 + D-1~D-7 + Open UNKNOWNs 10개

**EXECUTION 진행 조건** (DESIGN CONDITIONAL_ACCEPT 5조건 + EXECUTION 신규 3조건):

```
[DESIGN 조건 1] TASK_2050 verify exit 0 + T3 implementation-risk-critic PASS
[DESIGN 조건 2] action_gain Pilot OOD severity PASS (gap > 0.01, KS p < 0.05, 2 task)
[DESIGN 조건 3] R3 smoke: friction + action_gain NLL finite + ood_nll > id_nll
[DESIGN 조건 4] mass FAIL × 2 task 투명 공시 (negative result 은폐 금지)
[DESIGN 조건 5] friction µ_kinetic DEFERRED 논문 Appendix 명시

[EXECUTION 신규 조건 1] U-A1 (clipping 위치) Stage 0 해결 완료
[EXECUTION 신규 조건 2] noise axis AUROC < 0.65 "의도된 결과" 논문 framing 준비
[EXECUTION 신규 조건 3] forbidden field guard test green 유지 (4 axis 추가 후에도)
```

미충족 시: **MAJOR_REVISION** (mass track 완성 또는 3rd axis 추가 필요)

### Trigger for re-invocation

- 매 stage post-collection (Agent I 재호출 /war-room)
- R3 smoke 직후 (T4 트리거 — failure-interpretation-critic 병행)
- R14/R15 논문 작성 전 (T5 트리거 — reviewer-2-attack-agent 병행)

---

## 종합 결론

### PLAN_PASS 판정 (본 EXECUTION PLAN 자체)

`docs/NEXT_STAGE_FOUR_AXIS_DATA_COLLECTION_EXECUTION_PLAN.md` + 본 합성 보고서는 다음 모두 충족:

- [x] §A~§N 14 섹션 완성 (현재 상태 + 목표 + axis 카드 + 자원 + 절차 + gate + 특수 CP + agent 매트릭스 + repair + TASK + 판정 + 사용자 결정 + checklist + 다음 단계)
- [x] Agent A~I 9명 sub-section (본 파일)
- [x] 4 axis 카드 (friction/action_gain/latency/noise) 각각 claim/LOC/criteria/failure 기술
- [x] 25개 quality gate + DESIGN §G 30개 매핑 완성
- [x] 16단계 repair loop + axis × cause × candidate 매핑
- [x] TASK 2049~2056 10헤더 명세 완성
- [x] atomic checklist + 절대 금지 항목
- [x] Open UNKNOWNs 10개 명시
- [x] verification plan 4 step
- [x] mass FAIL 투명 공시, friction-only 한계 명시
- [x] threshold 완화 명시적 거부
- [x] noise AUROC < 0.65 의도 명확 서술
- [x] D-1~D-7 사용자 결정 정리
- [x] 코드/데이터/phase gate 변경 없음 (본 PLAN 작성 단계)

**Agent I 최종 판정**: **CONDITIONAL_ACCEPT** → 8개 조건 충족 시 ACCEPT.

---

*보고서 경로: `reports/next_stage_four_axis_agent_synthesis.md`*
*참조 EXECUTION PLAN: `docs/NEXT_STAGE_FOUR_AXIS_DATA_COLLECTION_EXECUTION_PLAN.md`*
*참조 DESIGN PLAN: `docs/FOUR_AXIS_HIGH_QUALITY_DATASET_PLAN.md`*
*참조 DESIGN SYNTHESIS: `reports/four_axis_dataset_design_synthesis.md`*
*다음 단계: D-1~D-7 사용자 결정 → TASK_2049 Stage 0 audit → TASK_2050 Codex 위임*
