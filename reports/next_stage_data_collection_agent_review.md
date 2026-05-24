# Next-Stage Data Collection — Agent Team Review

> **Scope**: action_gain PRIMARY + friction 재사용 + latency/noise 조건부
> **Date**: 2026-05-24
> **Trigger**: T2 (실험설계 변경 전) + T4 (수집 결과 해석 전)
> **Input documents**:
> - `docs/NEXT_STAGE_DATA_COLLECTION_EXECUTION_READY_PLAN.md` (본 review 기준)
> - `docs/NEXT_STAGE_FOUR_AXIS_DATA_COLLECTION_EXECUTION_PLAN.md` (4-axis 종합, commit 4fc3565)
> - `reports/next_stage_four_axis_agent_synthesis.md` (이전 synthesis, Agent I CONDITIONAL_ACCEPT 8조건)
> - `reports/pushcube_ood_severity_agent_report_R1.md` (PushCube severity 실측)
> - Phase 1 Explore 2개 결과 (code audit: collector.py, maniskill_schema.py)
> **Phase gate 상태**: R0/R1/R2 PASS, R3 PENDING

---

## Agent A — Axis Implementation Auditor

**Role**: action_gain collector 구현 정합성 감시 (Stage 0 pre / Stage 1 post)

**Input**:
- `src/fglc/data/collector.py` 실측: `_apply_ood()` L66-89 (mass/friction만), episode loop L148-149
- `src/fglc/data/maniskill_schema.py` 실측: TASK_OOD_PARAMS L115-130, REGIME_ID L103-110
- `src/fglc/schemas/visibility.py::FORBIDDEN_AGENT_FIELDS` (SSoT, 12개)

**Top 3 findings**

1. **삽입 위치 확정**: collector.py L148-149 사이가 action_gain 적용의 유일한 올바른 위치. `_apply_ood()`는 env-side 파라미터 전용이므로 action_gain을 그곳에 넣으면 FORBIDDEN_AGENT_FIELDS 경계 위반 위험.

2. **eval_metas 슬롯 이미 존재**: L191 `config.ood_params.get("action_gain", 1.0)`가 이미 있어 schema 변경 없이 true_action_gain eval-only 기록 가능. → 구현 복잡도 감소.

3. **clipping 필요**: sapien_env.py L1042-1044 자동 clip이 존재하지만, 외부 pre-clip(`np.clip`) 없이 gain × action을 그대로 넘기면 실제 실행 action이 clip되어 정보 손실. gain=0.7은 low side 위험 낮음; gain=1.3 high side에서 saturation 위험.

**Top 2 UNKNOWNs**

- U-N7: `np.clip` 후 dtype float64 cast 여부 — test에서 `assert a.dtype == np.float32` 명시 필요
- U-N1: PickCube yaml seed_pool block 부재 — TASK_2050 포함 또는 별도 commit (D-8 결정 대기)

**Recommendations**

1. `gain != 1.0` 분기로 ID 분기 유지 (gain=1.0 시 기존 코드와 100% 동일 경로 보장)
2. `.astype(np.float32)` 명시적 캐스트 필수
3. test assertion: `np.abs(a_gain).mean() < np.abs(a_id).mean() * 0.85` (gain=0.7 시 action magnitude 감소 증명)

**Judgment**: **CONDITIONAL_PASS**
- 구현 명세(§E.1) 충족 시 PASS 가능
- D-8 결정 전까지 PickCube yaml 보강 PATCH_REQUIRED

**Trigger for re-invocation**: TASK_2050 Codex 결과 accept 직전 (T3 gatekeeper)

---

## Agent B — Data Quality Auditor

**Role**: 수집 데이터 품질 검증 (Stage 2 probe / Stage 3 pilot / Stage 4 scaled)

**Input**:
- `data/fglc/PickCube-v1/{manifest,dataset_stats,quality_report}.json` (friction 기존)
- `data/fglc/PushCube-v1/{manifest,dataset_stats,quality_report}.json`
- validators.py EpisodeRejectReason (10개), 30 gate checklist (§I)

**Top 3 findings**

1. **friction 기존 데이터 품질 확인**: PickCube n_rejected=0, NaN=0; PushCube n_rejected=0, NaN=0. accept rate 100%. → friction 재사용 기준 (Gate 7, 8) 충족.

2. **action_gain probe 기준 적절**: probe-lenient (gap > 0.005, KS p < 0.1)은 `DATA_TOO_SMALL` 위험을 최소화하면서 axis 진입 가능성을 조기 판단하기에 충분. Pilot에서 0.01로 상향하는 구조가 올바름.

3. **PushCube 성공 기록**: 900ep accept, seeds 1042-1999 disjoint, FORBIDDEN_AGENT_FIELDS=0 — PushCube action_gain probe도 동일 품질 기대 가능.

**Top 2 UNKNOWNs**

- U-N8: PickCube/PushCube ID baseline action_std (gain=1.0) 미산출 — probe 시 비교 baseline 필요
- U-N6: PickCube/PushCube seed pool 끝값 manifest ↔ dataset_stats 정합성 미확인

**Recommendations**

1. probe 수집 직후 `action_norm_mean` ID vs OOD 비교 automated assertion 추가
2. manifest.json append 시 `ood_gain_low` 항목 schema 검증 (maniskill_schema.py TASK_OOD_PARAMS 확장 후)
3. gain=1.3 probe 시 clipping saturation rate (`|a|_clip / |a|_total` 비율) 기록 → TASK_CANDIDATE `OOD_AXIS_GAIN_CLIP_SATURATION` 증거

**Judgment**: **CONDITIONAL_PASS (Stage 0)**
- probe 완료 후 Gate 1~10, 14~17, 21 PASS → re-invocation 후 PASS로 전환
- U-N6 미해결 시 seed integrity PATCH_REQUIRED

**Trigger for re-invocation**: probe/pilot/scaled 각 수집 완료 직후

---

## Agent C — Split Leakage Auditor

**Role**: split간 누수 (seed/trajectory/forbidden field) 감시 (Stage 3 pilot / Stage 4 scaled)

**Input**:
- `src/fglc/schemas/visibility.py::FORBIDDEN_AGENT_FIELDS` (12개)
- `tests/test_fglc_forbidden_field_sync.py` (green 유지)
- `src/fglc/data/manifest.py` seed pool 정의

**Top 3 findings**

1. **FORBIDDEN_AGENT_FIELDS 12개 확인**: `regime_id, true_mass, true_friction, true_latency, true_noise_sigma, true_action_gain, oracle_action, counterfactual_reward, split_id, ood_type, seed, template_id`. `true_action_gain`이 이미 포함 — eval-only 처리 확인만 필요.

2. **seed 공간 설계 안전**: action_gain용 700s 영역 (PickCube: 700-709, PushCube: 700-709)은 기존 split들과 비겹침. train 42-91, val 200-209, test 300-309, ood_mass 500-509, ood_friction 600-609와 ∩=∅.

3. **trajectory hash collision 0 기대**: 기존 PickCube/PushCube 데이터에서 이미 hash collision=0 기록. seed 분리 설계가 올바를 경우 action_gain split도 동일 기대.

**Top 2 UNKNOWNs**

- U-N2: REGIME_ID `ood_latency:30` stub이 `ood_gain_low` split과 혼선 없는지 확인 필요 (D-9 결정 전)
- U-N5: ManiSkill 정확한 버전 핀 — requirements.txt에 `maniskill==3.0.1` 또는 유사 핀 존재 여부 Stage 0 확인

**Recommendations**

1. test_fglc_action_gain_collector.py에 `assert "true_action_gain" not in agent_obs_keys` assertion 필수 (eval_metas에만 있고 obs에 없음 검증)
2. manifest.json `split_id` 필드가 inference input 경로에 노출되지 않음을 dataloader 단계에서 audit
3. pilot 시 `split_id ∈ FORBIDDEN_AGENT_FIELDS` 이므로 split 정보는 metadata 분리 경로로만 접근

**Judgment**: **CONDITIONAL_PASS (Stage 0)**
- test_fglc_forbidden_field_sync.py green 유지 확인 후 PASS
- TASK_2050 수행 후 visibility.py 미수정 확인 필수

**Trigger for re-invocation**: TASK_2050 accept commit 후, pilot 완료 후

---

## Agent D — OOD Severity Critic

**Role**: OOD axis별 severity 판정 (gap, KS, Cohen's d) — probe lenient / pilot-scaled strict

**Input**:
- PickCube friction gap 0.1380 (PASS), PushCube 0.1236 (PASS)
- PickCube mass gap 0.0038 (FAIL), PushCube mass gap 0.0080 (FAIL)
- `src/fglc/data/manifest.py::verify_ood_severity` (delta_min=0.01, 변경 금지)

**Top 3 findings**

1. **friction 재사용 근거 확실**: 두 task 모두 gap > 0.01 (PickCube 0.138, PushCube 0.124), threshold 대비 10~13배 여유. Probe-level 재검증만으로 충분.

2. **action_gain 0.7 severity 예측**: action magnitude ~30% 감소 → joint velocity / end-effector position trajectory shift. 모든 episode에서 발생 (contact 독립). gap > 0.01 예상 근거 있음 — **그러나 단정 금지, probe에서 실증 필요**.

3. **mass FAIL 근본 원인 명확**: random policy에서 object와 접촉 없음 → mass shift가 dynamics에 전파되지 않음. gain=0.7은 매 step action을 통해 영향이 발생하므로 same random policy에서도 dynamics shift 발생.

**Top 2 UNKNOWNs**

- U-N8: action_gain OOD 시 어느 state 차원에서 Cohen's d > 0.3이 나오는가 — qvel 차원이 가장 유력, probe 실증 필요
- gain=0.7의 gap이 0.005~0.01 사이일 때 repair loop path 결정 (severity-up 0.5 vs episode 증가)

**Recommendations**

1. probe에서 per-dim Cohen's d를 먼저 확인 → pilot 기준 dims 선정에 활용
2. gain=1.3 secondary probe: clipping saturation rate (`|a_clipped| / |a_raw|` ratio per step) 기록 후 ≥50% → 폐기
3. `verify_ood_severity` threshold(0.01) 완화 제안 발생 시 즉시 BLOCKED — manifest.py 변경 금지 불변

**Judgment**: **CONDITIONAL_PASS (Stage 0)**
- probe 완료 후 gap > 0.005 확인 → PASS
- gap < 0.005 → PATCH_REQUIRED (severity-up, D-5 승인 필요)

**Trigger for re-invocation**: probe/pilot gap 측정 완료 직후

---

## Agent E — Dynamics Forensics

**Role**: dynamics shift 메커니즘 분석, action_gain axis 물리적 타당성 검증

**Input**:
- ManiSkill 3.x sapien_env.py L1042-1044 자동 clip 확인
- PickCube D_x=42 (joint_pos, joint_vel, tcp_pos, tcp_rot, obj_pos, obj_rot), D_a=8
- PushCube D_x=35 (joint_pos, joint_vel, tcp_pos, tcp_rot, obj_pos_z만), D_a=8

**Top 3 findings**

1. **action_gain은 contact-independent**: `a_executed = clip(a × gain, low, high)` → 모든 step에서 joint velocity 목표치 변경 → joint_vel 차원에서 shift 발생 보장. PickCube/PushCube 공통.

2. **shift 경로**: gain=0.7 → `a_executed = 0.7 × a_raw` (clip 이전) → 관절 속도 감소 → tcp_pos trajectory slower convergence → state_delta_norm 감소. 이 경로는 random policy에서도 동일.

3. **clipping saturation 위험 (gain=1.3)**: `a_raw ∈ [-1,1]` (normalized), gain=1.3 → `clip(1.3×a, -1, 1)` → `|a|>0.77`인 action이 clip → saturation. random policy에서 `|a| > 0.77` 비율은 `P(U(0,1)>0.77) = 0.23` 수준 → 대략 23% episode에서 partial saturation 발생. secondary probe에서 실증 필요.

**Top 2 UNKNOWNs**

- U-N8: tcp_pos vs joint_vel 중 어느 차원이 더 큰 per-dim shift를 보이는가 (probe 실측 필요)
- gain=0.7에서 state_delta_norm 감소량의 task별 차이 (PickCube object pick 여부, PushCube push distance)

**Recommendations**

1. probe 시 per-dim shift 히스토그램을 joint_vel(8 dims)과 tcp_pos(3 dims) 별도 분석
2. gain=0.7 time-averaged action magnitude를 ID baseline과 통계 비교 (t-test p < 0.05 목표)
3. contact rate 측정: PickCube `obj_pos_z` 변화 여부로 간접 추정 가능

**Judgment**: **PASS (Stage 0, 물리적 타당성)**
- contact-independent action_gain shift 경로 확인됨
- 실측 gap 검증은 probe(Stage 2)로 위임

**Trigger for re-invocation**: probe gap < 0.005 발생 시 (dynamics pathway 재분석)

---

## Agent F — Claim-Metric Alignment Auditor

**Role**: action_gain axis가 FGLC 4축 claim에 기여하는지 검증 (Stage 3 pilot / Stage 4 scaled / R3 smoke)

**Input**:
- FGLC 핵심 claim: prediction NLL / detection AUROC / attribution nec-suf / control return
- `docs/idea/21_METRICS.md` 4축 metric 정의
- `docs/idea/12_TRAINING_STAGES.md` Stage 3 gate (≥2 axis)

**Top 3 findings**

1. **prediction NLL axis 기여**: action_gain OOD에서 base world model의 `pθ(z_{t+1}|z_t,a_t,h_t)` NLL 상승 기대. FGLC β-gate가 이를 탐지하고 correction을 적용 → NLL 하강. 2축 데이터(friction + action_gain)로 검증 신뢰도 향상.

2. **control return 차별**: action_gain OOD 환경에서 FGLC corrected rollout이 비보정 WM 대비 reward 유지. 이는 action-relevance claim의 핵심 증거. `causal attention α_t`가 joint velocity latent group에 집중하는지 확인 필요 (R5 이후).

3. **Stage 3 gate 충족 경로**: friction(PASS) + action_gain(목표) = 2 axis → Stage 3 gate 충족 가능. 단, Stage 3은 R5/R6 구현 후이므로 현재는 **데이터 준비** 단계.

**Top 2 UNKNOWNs**

- noise axis의 claim 기여: dynamics shift ≈ 0 → NLL 기여 없음. specificity claim(β-gate 오탐 없음)은 별도 metric → noise를 동일 axis로 취급 시 claim 혼선 위험
- action_gain과 latency가 같은 latent group(joint velocity)에서 shift를 일으킬 경우 attribution 구별 가능 여부

**Recommendations**

1. pilot 시 `ood_nll_gain - id_nll` ≥ 일정 threshold 사전 설정 (R3 smoke 기준으로 사용)
2. noise axis claim 기여를 별도 섹션으로 분리: "falsification robustness to obs noise" vs "dynamics OOD correction"
3. R3 smoke 시 per-axis `ood_nll > id_nll` assertion 자동화

**Judgment**: **CONDITIONAL_PASS**
- R3 smoke에서 friction + action_gain 각각 `ood_nll > id_nll` 확인 후 PASS
- noise claim 분리 문서화 PATCH_REQUIRED

**Trigger for re-invocation**: R3 smoke metrics.json 생성 후

---

## Agent G — Novelty Relevance Critic

**Role**: action_gain axis가 FGLC novelty claim을 강화하는지, 직접 위협 논문과의 차별점 검증

**Input**:
- 직접 위협: TD-MPC2, DreamerV3, HiP-RSSM, PLSM, ReDRAW, AdaWM
- `docs/idea/22_NOVELTY_AND_THREATS.md`
- `docs/idea/25_PAPER_TITLE_CONTRIBUTIONS.md`

**Top 3 findings**

1. **action_gain은 직접 위협 미포함 axis**: HiP-RSSM은 mass/inertia 파라미터 추론에 집중. PLSM은 action-effect 구조를 가지지만 action scale OOD를 명시적으로 다루지 않음. action_gain OOD는 FGLC의 **control-relevance 차별점**을 노출하는 고유 axis.

2. **causal attention action-relevance 강화**: `CausalAttention(ρ_t, z_t, a_t, h_t, ∇_z V)`에서 `a_t` 입력이 action_gain OOD 시 α_t 분포를 변화시키는지 확인 가능 → intervention-validity 증거로 활용 (R5/R6 단계).

3. **friction+gain 2축이 friction 단독보다 novelty frame 강화**: "단일 joint friction 파라미터 OOD" → reviewer가 "narrow domain" 공격 가능. action_gain 추가로 "제어 파라미터 변화에도 robust한 WM planning"으로 확장.

**Top 2 UNKNOWNs**

- U-N9: 2025/2026 신규 논문 중 action_gain / action scale OOD를 명시적으로 다루는 WM 논문 존재 여부 (MCP arxiv + semantic-scholar 조회 Stage 4 / R14 예정)
- AdaWM의 "불일치 기반 적응"이 action_gain OOD에서 FGLC와 어떻게 다른지 방어 문장 준비 필요

**Recommendations**

1. paper framing에 "We are the first to evaluate WM correction under simultaneous friction and action-gain distribution shift" 문장 후보 준비 (MCP 교차검증 후 확정)
2. U-N9 해결 전까지 이 claim 확정 보류
3. R14 단계에서 `fglc-related-work-scout` agent로 action_gain OOD WM 논문 전수 조사

**Judgment**: **CONDITIONAL_PASS**
- U-N9 (2025/2026 신규 위협) 조회 후 최종 판정
- friction + action_gain 2축 novelty frame은 현재 문헌 기준 차별점 존재로 판단

**Trigger for re-invocation**: R14 논문 framing 시작 시 (T5 trigger)

---

## Agent H — Resource Budget Auditor

**Role**: GPU/VRAM/disk/wall-clock 자원 현실성 검증 (Stage 0 pre-S3 / Stage 4 pre-Robust)

**Input**:
- VRAM 8 GB (RTX 4060 Ti), 7일/단일 GPU 한계
- §G 자원 계산 매트릭스
- 현재 데이터: PickCube 250ep ID + 50ep friction + 50ep mass; PushCube 500ep ID + 100ep each

**Top 3 findings**

1. **action_gain Scaled 예산 적절**: 2 task × 650ep × ~10-11 KB/ep ≈ 16 MB / ~1 hour wall-clock. RTX 4060 8GB VRAM에서 7일 한계 대비 극히 여유.

2. **R3 smoke 1-epoch 예상**: batch=16, T=16, K=8, d=32, h=256 → ~1 GB VRAM (RTX 4060 8GB 여유). 1-epoch ≈ 5~10 min. 기존 SyntheticToyDataset 기반 R2 smoke와 동일 scale.

3. **Robust 단계 (4000ep+) 경고**: 4 axis × 2 task × Robust(2000ep) = ~200 MB / ~12 hour. 7일 한계 내이지만 단일 실행으로는 긴 편 → stage별 분할 수집 권장.

**Top 2 UNKNOWNs**

- R3 model forward pass VRAM: K=8, d=32 그룹 분해 + GRU h=256 + correction module 누적 → 실제 VRAM 측정 필요 (R3 smoke 직전)
- 4-axis full Robust 시 disk I/O bottleneck: HDF5 400개+ 파일 동시 열기 → RAM 제약 체크

**Recommendations**

1. R3 smoke 직전 `torch.cuda.memory_summary()` 출력 확인 → OOM 없음 보장
2. Robust 단계는 2 seed × 1 axis씩 순차 진행 (단일 72h run 방지)
3. disk 사용량 체크: `data/fglc/` 현재 크기 + 예상 증가분 확인 후 진행

**Judgment**: **PASS (Stage 0 예산 검증)**
- action_gain Probe/Pilot/Scaled 모두 7일 한계 대비 여유 ✅
- RTX 4060 8GB VRAM 내 처리 가능 ✅

**Trigger for re-invocation**: Robust 단계 진입 직전 (pre-Robust)

---

## Agent I — Experiment Design Chair (Synthesis)

**Role**: Agent A~H 8개 보고서 종합 + 최종 acceptability 판정

**Input**: Agent A~H 보고서 전체 (본 문서 §A~§H)

**종합 판정 매트릭스**

| Agent | 판정 | 핵심 근거 |
|---|---|---|
| A (impl-auditor) | CONDITIONAL_PASS | 구현 명세 충족 시 PASS, D-8 대기 |
| B (data-quality) | CONDITIONAL_PASS | probe 완료 후 Gate 1~16 PASS 기대 |
| C (split-leakage) | CONDITIONAL_PASS | visibility.py 미수정 확인 후 PASS |
| D (ood-severity) | CONDITIONAL_PASS | probe gap > 0.005 기대, friction 재사용 확실 |
| E (dynamics-forensics) | **PASS** | contact-independent shift 경로 확인됨 |
| F (claim-metric) | CONDITIONAL_PASS | R3 smoke `ood_nll > id_nll` 확인 후 PASS |
| G (novelty-relevance) | CONDITIONAL_PASS | U-N9 조회 후 최종 판정 |
| H (resource-budget) | **PASS** | 7일 한계 내 충분한 여유 확인 |

**Conflicts & Resolution**

| 충돌 | 해결 |
|---|---|
| Agent D의 "단정 금지"와 Agent E의 "shift 경로 확인" | 불충돌 — D는 측정값, E는 물리 메커니즘. probe 실측이 최종 근거 |
| Agent F의 "noise claim 분리"와 4-axis 계획 | noise는 specificity test로 분리 유지. 4-axis 계획 내 noise 섹션에 명시 |
| Agent G의 "U-N9 미해결"과 action_gain 우선 진행 | 데이터 수집은 MCP 조회 전 진행 가능. 논문 framing은 R14까지 보류 |

**이전 synthesis (4fc3565) CONDITIONAL_ACCEPT 8조건 현황**

| 조건 | 현재 상태 |
|---|---|
| 1. friction 2-task PASS 재확인 | ✅ PickCube 0.138, PushCube 0.124 |
| 2. mass FAIL negative result 공시 | ✅ §J.4에 명시 |
| 3. delta_min=0.01 불변 | ✅ manifest.py 변경 금지 재확인 |
| 4. friction_mapping DEFERRED Appendix 방어 | ✅ §D.2 문장 준비 |
| 5. action_gain axis 물리적 타당성 | ✅ Agent E PASS |
| 6. R3 smoke 사용자 승인 필수 | ✅ D-7 명시 |
| 7. repair loop 16단계 정의 | ✅ §J.1 |
| 8. BACKBONE 변경 사용자 피드백 | ✅ D-5 명시 |

**EXECUTION-READY 신규 조건 (본 plan 추가)**

| 조건 | 현재 상태 |
|---|---|
| N-1: U-N1 PickCube yaml seed_pool 보강 | D-8 결정 대기 (PATCH_REQUIRED) |
| N-2: U-N4 quality_report Ckpt 4 충돌 해소 | 사용자 확인 대기 (PATCH_REQUIRED) |

**Top 3 cross-cutting concerns**

1. **action_gain probe 실패 시 escape hatch**: gain=0.5로 severity-up (D-5 신규 cause). 단, `OOD_AXIS_GAIN_UNCOVERED` cause 추가는 BACKBONE 등급 1 → 사용자 승인 필수. 사전 승인(D-5=(a)) 시 repair loop 자동 진행 가능.

2. **mass FAIL 명시 의무**: PickCube+PushCube 두 task 모두 random policy에서 FAIL. 이 사실은 논문 Section 4에 반드시 명시. "contact-requiring OOD axis에 대한 random policy baseline의 한계"로 framing.

3. **noise specificity 독립 추적**: noise axis를 "dynamics OOD"와 혼용하면 claim confusion. §F의 specificity metric framework (AUROC, FPR, Σ ratio)를 별도 섹션으로 분리 유지.

**최종 판정: CONDITIONAL_ACCEPT**

조건:
1. D-1 = (a) action_gain 선택
2. D-8 결정 후 PickCube yaml seed_pool 보강 (TASK_2049 또는 TASK_2050)
3. U-N4 (Ckpt 4 FAIL/PASS 충돌) 사용자 확인 또는 deferred 명시
4. TASK_2050 Codex 결과 Gatekeeper 6조건 전체 통과
5. probe gap > 0.005 실증 후 pilot 진입
6. D-7 사용자 명령으로만 R3.passed 생성
7. negative result (mass FAIL, friction DEFERRED, noise specificity) 논문 명시 약속

미충족 시:
- D-8/U-N4 미해결 → PLAN_BLOCKED까지는 아님, PATCH_REQUIRED 상태로 진행
- probe gap < 0.005 → repair loop (D-5 승인 후) 또는 USER_ESCALATION
- Gatekeeper 6조건 실패 → git merge --abort → 재시도 또는 Claude 직접 처리

**Re-invocation schedule**

| 시점 | 트리거 | 모드 |
|---|---|---|
| Stage 0 완료 후 | TASK_2049 read-only audit 완료 | compact |
| Stage 1 (TASK_2050) accept 후 | T3 gatekeeper + 구현 검토 | compact |
| Stage 2 (probe) 완료 후 | gap 실측 + Agent D/E 재검토 | compact |
| Stage 3 (pilot) 완료 후 | 30 gate 중 25개 + Agent B/C/D/F | deep |
| Stage 4 (scaled) 완료 후 | 30 gate 전체 + war-room | deep + `/war-room` |
| R3 smoke 완료 후 | metrics.json + D-7 사용자 결정 | deep |

---

## Synthesis Summary

**Plan Judgment**: **CONDITIONAL_ACCEPT**

**PASS 요소**:
- friction 재사용 근거 확실 (2 task, gap 0.124~0.138, threshold 10× 여유)
- action_gain physics 타당성 확인 (contact-independent, Agent E PASS)
- 자원 예산 충분 (Agent H PASS)
- mass FAIL negative result 공시 의무 명시

**PATCH_REQUIRED 요소**:
- U-N1: PickCube yaml seed_pool block 보강 (D-8 결정 후)
- U-N4: Ckpt 4 FAIL/PASS 충돌 해소 (사용자 확인)
- noise claim 분리 문서화 (§F, TASK_2056)

**BLOCKED 위험 요소** (현재 없음, 발생 가능):
- probe gap < 0.005 × 3 iter inconclusive → USER_ESCALATION
- Gatekeeper 6조건 반복 실패 → 구현 전략 재검토

**다음 즉시 행동**: 사용자 D-1~D-9 응답 수령 → TASK_2049 PREFLIGHT_AUDIT 진입
