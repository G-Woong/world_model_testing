# STEP 9 C3 Root Cause Report

date: 2026-05-18
source: 39_step9_current_state_audit.md
gate: O-40 (prerequisite for STEP 2 fix)
status: COMPLETE

---

## 1. Root Cause Classification (A~F)

### A. Threshold/Calibration Issue — CONFIRMED ★★★

**증거**:
- `frcg_agent.py:74` `GateConfig(tau_f=0.5)` hardcoded
- `decision_gate.py:14` default `tau_f=0.0`
- STEP 8 metrics: `mean_wrong_prob=0.0996`
- `sigmoid(F_t - 0.5) = 0.0996` → `F_t ≈ -1.7` → `F_t > 0.5` 불가
- 결과: `predicted_wrong=True` n=2645 중 0개. `false_planning_call_rate=0.0` 모든 13 agent

**Fix**:
- fix-1a: `frcg_agent.py:74` → `GateConfig(tau_f=0.0)` (1줄)
- fix-1b: `frcg_agent.py:141` predicted_wrong → `self._last_wrong_prob > 0.5` (1줄)

---

### B. Eval Harness Propagation Bug — CONFIRMED ★★★

**증거**:
- `eval_runner.py:111`: `action, compute_log = agent.act(obs)` — eval_labels 미전달
- `LeakageSanityProbeAblation.act()` (ablations.py:409): `eval_labels is not None and "true_control_grammar" in eval_labels` → 진입 자체 불가
- ABL-040 metric이 FRCG-LR과 bit-for-bit 동일 (0.215954631379962, 15자리 일치)
- `planner.py:116`: eval evidence 0/0/False 고정 (training과 비대칭)

**Fix**:
- fix-2a: `planner.py:116` evidence에서 effect_summary 파싱으로 `observed_failed_action` derive (5줄)
- fix-3a: `eval_runner.py:111` ABL-040에만 eval_labels+training_labels dict 전달 (10줄)
- fix-3b: `LeakageSanityProbeAblation.act` → F_t sentinel_high 강제 override (3줄)

---

### C. Label/Mapping Coverage Issue — PARTIAL ★

**증거**:
- STEP 8: `mapping_coverage=0.342` (effect_type mapping이 34.2%만 커버)
- `planner.py:55-75` `_effect_type_id()` mapping: "failed", "task_complete" 등 10개 key
- v0_4에서 effect_summary 값들 일부가 mapping table에 없어 default 0 반환 가능

**평가**: 이 자체로는 C3=0.0을 야기하지 않음. A+B가 해결되면 C는 F_t 정확도 문제에 그침.
**Action**: mapping table에 v0_4 실측 effect_summary 값 추가 (low priority, STEP 5 이후)

---

### D. Architecture Not Connected — CONFIRMED ★★★

**증거**:
- `src/` repo-wide grep: `planner_state.update` 호출 0개 (tests/TASK files에만 존재)
- `h_exec_id = planner_state.get_current(step_idx)` → 항상 0
- `planner.py:162` `P_switch = 1.0 if h_star is not None and h_star.combined_id != h_exec_id else 0.0`
- h_exec_id=0이고 alt_hypotheses[0].combined_id도 0 가능 → P_switch=0.0 빈번
- `decision_gate.py:66-67` `if gi.P_switch <= cfg.tau_a` (tau_a=0.5) → 차단
- lr_scorer는 text eval path에 미연결 (gui_env 전용)

**Fix**:
- fix-2b: `planner.py` gate_decision.proceed_with_plan=True일 때 `planner_state.update(step_idx+1, h_star.combined_id)` (3줄)

---

### E. Training Objective Failure — NOT failure ✓

**증거**:
- Stage B l_falsification=0.635 (non-degenerate)
- F_t variance=0.684 (test_id), 0.788 (test_ood) — training path alive
- gradient path 활성 확인 (loss 감소)

**결론**: training은 정상. eval path 단절이 문제.

---

### F. Unknown / Architecture Output Distribution — NOT critical ✓

**증거**:
- `world_model_heads.py:66-80` standard nn.Linear init, no pathology
- effect_head output: raw logits, no constraint — 정상
- progress_head: ReLU sequence — dead neuron 가능하나 치명적 아님

**결론**: F_t variance가 이미 non-zero이므로 output distribution 문제 없음. Unknown 없음.

---

## 2. Fix Priority Order

| 순위 | Fix ID | 파일 | 예상 효과 | 우선순위 |
|---|---|---|---|---|
| 1 | fix-1a | frcg_agent.py:74 | tau_f 차단 제거 → predicted_wrong 발동 가능 | CRITICAL |
| 2 | fix-1b | frcg_agent.py:141 | wrong_prob > 0.5 기준 일관화 | HIGH |
| 3 | fix-2a | planner.py:116 | evidence quality 개선 → F_t 더 반응적 | HIGH |
| 4 | fix-2b | planner.py:~178 | h_exec_id 동적 갱신 → P_switch 정상화 | HIGH |
| 5 | fix-3a+3b | eval_runner.py:111 + ablations.py | ABL-040 positive control 활성화 | MEDIUM |
| 6 | success fix | eval_runner.py:130 | C4 ceiling 제거 | HIGH (C4) |

**1+2: frcg_agent.py 단독 (1 file, 2줄) → Claude 직접 구현**
**3+4: planner.py 단독 (1 file, 8줄) → Claude 직접 구현**
**5: eval_runner.py + ablations.py (2 files, ~13줄) → Claude 직접 구현**
**6: eval_runner.py (1 file, 1줄) → Claude 직접 구현 (fix-5와 합산)**

---

## 3. C3 READY_CANDIDATE 달성 조건

fix-1a~2b 구현 후 eval 재실행 시 5개 조건 예측:

| 조건 | 현재 | fix 후 예측 | 확신도 |
|---|---|---|---|
| F_t variance > 0.01 | 0.684 (이미 PASS) | 유지 | HIGH |
| predicted_wrong_diversity > 1 | 0/2645=0 | >0 (tau_f=0.0이면 F_t>0 episodes) | MEDIUM |
| C3 F1 trio 중 1+ > 0 | 0/0/0 | 불확실 (B+D fix 필요) | MEDIUM |
| n=5 seed variance < 0.5×mean | 미측정 | 구현 후 확인 필요 | UNKNOWN |
| ABL-040 inert 아님 | inert | fix-3a+3b 후 분리 | HIGH |

fix-1a만으로 predicted_wrong_diversity 회복 가능. C3 F1이 양수가 되려면 fix-2a+2b도 필요.

---

## 4. 연쇄 차단 구조

```
tau_f=0.5 (A) ──────────────────────────────→ predicted_wrong=False 100%
                                               C3 fp=0, ECE=null
evidence=0/0/False (B) ─────────────────────→ F_t suppressed
                                               C3 F1 추가 하락
h_exec_id=0 frozen (D) ──────────────────────→ P_switch=0 빈번
                                               planning gate 추가 차단
eval_labels 미전달 (B harness) ──────────────→ ABL-040 inert
                                               positive control 무력화
```

4개 원인이 **독립적으로** 각각 C3를 0으로 끌어내릴 수 있고, **동시에** 모두 활성화되어 있다.
fix-1a만으로는 C3 완전 회복 불가. fix-1a~2b 모두 필요.

---

## 5. Gate O-40 Status

**PASS** — C3 0.0의 원인이 A~F 카테고리 모두 직접 증거와 함께 분류되었고,
fix priority 순서가 확정되었으며, 각 fix의 file/line이 지정되었다.

**다음**: STEP 2 fix loop 진행 (fix-1a → fix-1b → fix-2a → fix-2b → fix-3a+3b → success fix)
