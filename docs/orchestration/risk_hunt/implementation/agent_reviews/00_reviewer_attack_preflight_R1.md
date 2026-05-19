# Agent Report: reviewer-2-attack-agent — PHASE 0 Preflight

**Date**: 2026-05-19  
**Agent**: reviewer-2-attack-agent  
**Overall Verdict**: `HIGH_RISK`

---

## FATAL Attacks

### FATAL-1: CUSUM 충분성
text env에서 CUSUM이 이미 탁월하면 LFD complexity 정당화 불가.  
**방어 필요**: OOD grammar split(SPLIT-003), reveal-vs-shift(SPLIT-008)에서 LFD > CUSUM (detection_delay AND false_alarm_rate 양쪽).  
**필수 ablation**: stateless-LFD vs GRU-LFD — 차이 없으면 persistent h_t claim 붕괴.

### FATAL-3: 순환 평가
`wrong_prob_learned` → `true_wrong_hypothesis`로 훈련 → 동일 레이블 타입으로 평가 = memorization 측정.  
**방어 필요**: grammar-template-level train/test OOD split. MET-FALS를 SPLIT-003에서만 보고.

---

## MAJOR Attacks

### MAJOR-2: text-only 외적 타당성
GUI 실험 없이 detection_delay가 GUI에 적용 불가. 모든 정량적 claim을 text env + synthetic GUI로 명시 한정 필수.

### MAJOR-4: v0_5 인공성
v0_5 = 메커니즘 검증 testbed. main results table에 사용 금지 (SPLIT-002/003만 허용).

### MAJOR-5: detection_delay 무앵커
`detection_delay + rewrite_latency + replanning_latency = total_recovery_delay` 분해 보고 필수.  
Pearson r(detection_delay, recovery_delay) < 0.3이면 metric이 task-relevant 결과와 무관.

---

## 해결 불가 약점

1. P5 (frozen VLM MVE) 미완료 시 GUI claim 전부 제거 또는 강한 hedge 필수.
2. 순환 훈련/평가 문제 구조적 — OOD split으로 완화는 가능하나 완전 해결 불가.
   재프레이밍 권장: "sequential falsification signal calibration + gate reliability" (MET-CAL-001 ECE + MET-COMP-005).
