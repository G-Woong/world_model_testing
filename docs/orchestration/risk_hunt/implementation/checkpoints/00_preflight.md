# PHASE 0 — Implementation Preflight Checkpoint

**Date**: 2026-05-19  
**Branch**: `memory-redesign-2026-05-16` @ `f271851`  
**Verdict**: `PASS_WITH_MODIFICATIONS`

---

## 1. 상태 검증 결과

| 항목 | 상태 | 위치 |
|---|---|---|
| Master plan 문서 | ✅ 존재 | `docs/orchestration/risk_hunt/12_learned_falsification_redesign_master_plan.md` |
| TASK_LFD_001-008 queue 파일 | ✅ 부재 (PHASE 1 생성 예정) | `.agent_tasks/codex_queue/` |
| `visibility.py::FORBIDDEN_AGENT_FIELDS` | ✅ 15개 필드, frozenset 확인 | `src/frcgw/schemas/visibility.py:25-41` |
| `test_forbidden_field_mirror_sync.py` | ✅ **3 passed** GREEN | pytest |
| `metrics.py` LFD 메트릭 | ✅ 부재 확인 (detection_delay, CUSUM, SPRT 없음) | `src/frcgw/evaluation/metrics.py` |
| `losses.py` placeholder 5개소 | ✅ 확인 | lines 120, 132, 150, 170-172 |
| `encoders.py:142` h0=None | ✅ `gru_out, _ = self.gru(step_features)` — hidden state 폐기 | `src/frcgw/models/encoders.py:142` |
| `generator.py:266` single regime | ✅ `hidden_regime=family` | `src/frcgw/text_env/generator.py:266` |
| `planner.py:120-134` proxy heuristic | ✅ `use_no_state_change_proxy` 존재 확인 | `src/frcgw/planning/planner.py:120-134` |
| `falsification.py:66-67` short-circuit | ✅ `{0,6}` effect type 단락 확인 | `src/frcgw/planning/falsification.py:66-67` |
| `step_schema.py:74-84` EvaluationLabels | ✅ `regime_switch_t` 없음 / `true_regime`, `ood_type` 이미 존재 | `src/frcgw/schemas/step_schema.py:74-84` |

---

## 2. Critic Agent 판정 요약

### 2.1 Implementation-Risk-Critic

**종합**: `NEEDS_FIX before Codex TASK authoring`

| 조건 | 상태 | 세부 |
|---|---|---|
| 1. Scope / FILES_ALLOWED | WARN | PHASE 4 h_t 변경 시 모든 caller 열거 미흡 |
| 2. 의존성 그래프 | PASS | 순서 논리적으로 올바름 (단, TextFRCGModel 링크 명시 필요) |
| 3. 테스트 커버리지 | FAIL | persistent h_t, BOCPD posterior, CUSUM/SPRT 테스트 없음 |
| 4. visibility.py 위험 | WARN | PHASE 6 변경 시 fragile-file 승인 게이트 TASK STOP_CONDITION에 필수 포함 |
| 5. Top 3 CRITICAL 리스크 | FAIL | 3개 CRITICAL 블로커 발견 |

**CRITICAL-1 (PHASE 4)**: `HistoryEncoder.forward` 반환 타입 `Tensor → (Tensor, Tensor)` 변경 시 모든 caller 연쇄 파괴. PHASE 4 TASK `FILES_ALLOWED`에 `TextFRCGModel`, training loop, rollout harness 전부 포함 필수.

**CRITICAL-2 (PHASE 5)**: `falsification.py:66-67` `{0,6}` short-circuit이 BOCPD head 입력의 65%+ 차단. PHASE 5 TASK에 short-circuit 처리 결정(bypass/condition/route)을 `BACKGROUND`에 명시 필수.

**CRITICAL-3 (PHASE 2)**: per-step regime switch → `BatchTargets` + `L_regime` cascade 미매핑. PHASE 2 TASK 작성 전 전체 cascade 매핑 필수.

---

### 2.2 Data-Leakage-Auditor

**종합**: `PASS with 2 CRITICAL pre-conditions`

| 항목 | 판정 | 근거 |
|---|---|---|
| 기존 `true_regime`/`ood_type` in EvaluationLabels | WARN (SAFE) | PublicObservation과 구조적으로 분리됨 |
| `regime_switch_t` (PHASE 2 신규) | **CRITICAL** | ground-truth switch timing = `true_change_point`급 레이블. PHASE 2 이전에 `FORBIDDEN_AGENT_FIELDS` 추가 + 사용자 승인 필수 |
| `detection_delay_gt` (PHASE 6 신규) | **CRITICAL** | `regime_switch_t` 직접 파생 → oracle timing 인코딩. PHASE 6 이전에 `FORBIDDEN_AGENT_FIELDS` 추가 + 사용자 승인 필수 |
| LFD 모델 출력 (`wrong_prob_learned`, `run_length_posterior`, `cusum_stat_t`) | SAFE | ground truth 아님, 모델 자체 불확실성 추정값 |
| EvaluationLabels 신규 detector 필드 | SAFE (EVALUATION_ONLY bucket) | 평가 전용, 추론 입력 아님 |

**사전 조건** (PHASE 2 전 사용자 승인 게이트 필요):
```
visibility.py::FORBIDDEN_AGENT_FIELDS에 추가:
  - "regime_switch_t"
  - "detection_delay_gt"

mirror 의무:
  .claude/hooks/schema_leakage_guard.ps1 $forbiddenTokens
  tests/test_forbidden_field_mirror_sync.py GREEN 유지
```

---

### 2.3 Reviewer-2-Attack-Agent

**종합**: `HIGH_RISK` — 2 FATAL, 3 MAJOR

**FATAL-1 (CUSUM 충분성)**: text env에서 CUSUM이 이미 탁월하면 LFD complexity가 정당화 불가. **방어**: OOD grammar split(SPLIT-003)과 reveal-vs-shift(SPLIT-008)에서 LFD가 CUSUM을 `detection_delay` AND `false_alarm_rate` 양쪽에서 엄격히 지배해야 함. stateless-LFD ablation 필수.

**FATAL-3 (순환 평가)**: `wrong_prob_learned`를 `true_wrong_hypothesis`로 훈련 후 동일 레이블 타입으로 평가 = memorization 측정. **방어**: grammar-template-level train/test OOD split 강제. SPLIT-003에서만 MET-FALS 보고. in-distribution 개선만으론 claim 불성립.

**MAJOR-2 (text-only 외적 타당성)**: GUI 실험 없이 detection_delay claim이 GUI에 적용 불가. 모든 정량적 claim을 text env + synthetic GUI로 명시 한정 필수.

**MAJOR-4 (v0_5 인공성)**: 동일-액션/다른-효과 트리거는 real GUI 실패 모드와 무관. CUSUM이 이미 해결 시 paper에 답이 없음. **방어**: v0_5는 메커니즘 검증 testbed로만 위치, main claim에 사용 금지.

**MAJOR-5 (detection_delay 무앵커)**: step 단위 수치 → recovery_delay와 인과 연결 없이는 무의미. `detection_delay + rewrite_latency + replanning_latency = total_recovery_delay` 분해 보고 필수.

---

## 3. Checkpoint-0 PASS 조건 평가

| 조건 | 상태 |
|---|---|
| 상태 명확 | ✅ |
| Dependency 그래프 확정 | ✅ (수정 사항 3개 반영 필요) |
| Critic CRITICAL FAIL 0 | ❌ (3 impl-risk CRITICAL + 2 leakage CRITICAL + 2 reviewer FATAL = 7개) |

---

## 4. 최종 판정: `PASS_WITH_MODIFICATIONS`

**이유**: CRITICAL/FATAL 발견들이 존재하지만, 이들은 모두 **TASK 파일 설계 수준에서 해결 가능**하며 구현 자체를 블록하지 않는다. 단, 아래 7개 수정사항이 TASK 파일 작성 전 반영되어야 한다.

### 4.1 PHASE 1 (TASK 파일 작성) 전 필수 수정사항

| # | 수정사항 | 대상 TASK | 우선도 |
|---|---|---|---|
| M1 | PHASE 4 TASK에 `HistoryEncoder` 모든 caller (TextFRCGModel, training loop, rollout harness) FILES_ALLOWED 포함 | TASK_LFD_002 | CRITICAL |
| M2 | PHASE 5 TASK BACKGROUND에 `{0,6}` short-circuit 처리 결정 명시 (bypass / condition / BOCPD separate routing) | TASK_LFD_003 | CRITICAL |
| M3 | PHASE 2 TASK에 BatchTargets + L_regime cascade 전체 매핑 포함 | TASK_LFD_004 | CRITICAL |
| M4 | PHASE 2 TASK STOP_CONDITION에 `regime_switch_t` FORBIDDEN_AGENT_FIELDS 추가(사용자 승인) 선행 조건 명시 | TASK_LFD_004 | CRITICAL (leakage) |
| M5 | PHASE 6 TASK STOP_CONDITION에 `detection_delay_gt` FORBIDDEN_AGENT_FIELDS 추가(사용자 승인) 선행 조건 명시 | TASK_LFD_006 | CRITICAL (leakage) |
| M6 | 모든 TASK REQUIRED_TESTS에 해당 컴포넌트 unit test 명시 (persistent h_t, BOCPD posterior, CUSUM/SPRT 각각) | LFD_001-003 | FAIL |
| M7 | PHASE 3 TASK에 grammar-template-level OOD split 설계 (SPLIT-003 등가물) 포함 — 순환 평가 방지 | TASK_LFD_007 | FATAL (reviewer) |

---

## 5. Agent Report 보존 경로

```
docs/orchestration/risk_hunt/implementation/agent_reviews/
  00_impl_risk_preflight_R1.md   (← implementation-risk-critic 결과)
  00_leakage_preflight_R1.md     (← frcgw-data-leakage-auditor 결과)
  00_reviewer_attack_preflight_R1.md  (← reviewer-2-attack-agent 결과)
```

---

## 6. 다음 단계

**PHASE 1 진입** — 위 M1-M7 수정사항을 반영한 8개 TASK 파일 작성.

실행 순서:
1. TASK_LFD_004 (v0_5 multi-regime dataset) — data first, M3/M4 반영
2. TASK_LFD_001 (CUSUM/SPRT baseline) — M7(OOD split) 반영
3. TASK_LFD_007 (sequential detection metrics)
4. TASK_LFD_002 (persistent h_t) — M1 반영
5. TASK_LFD_003 (BOCPD run-length head) — M2 반영
6. TASK_LFD_005 (temporal consistency + seq loss)
7. TASK_LFD_006 (EvaluationLabels contract) — M5 반영
8. TASK_LFD_008 (robotics passive OOD probe)
