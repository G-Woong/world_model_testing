# STEP 10 Next Phase Plan

date: 2026-05-18
source: 47_step9_final_evidence_card.md
verdict: AT_RISK_BUT_RECOVERING → ALIVE_READY path

---

## 1. Current Status

STEP 9 breakthrough: C3 f1=0.539/0.587 (test_id/test_ood), C6 14.9× advantage, ABL-040 active.
Remaining for ALIVE_READY: ABL-001/003 faithful retrain, n=5 stochastic eval, C2 dataset.

---

## 2. STEP 10 Priority Queue

### P0: ABL-001 faithful retrain (l_regime=0.0)
- Config: `configs/train_text_v0_4_abl001.yaml`
- Expected: `regime_shift_f1` collapse → confirms C2 claim
- Command: `python scripts/02_train_text_smoke.py --config configs/train_text_v0_4_abl001.yaml`
- Gate: checkpoint exists + C3/C6 non-collapse (l_regime doesn't affect C3)

### P0: ABL-003 faithful retrain (merged regime/grammar)
- Config: `configs/train_text_v0_4_abl003.yaml`
- Expected: C2 + C3 simultaneous collapse → confirms separability claim
- Gate: checkpoint exists + both C2/C3 collapse

### P1: C2 dataset (multi-regime episodes)
- v0_4는 per-episode single regime → C2=0.0
- OPTION A: v0_5 dataset with intra-episode regime shifts
- OPTION B: redefine C2 as "across-episode regime consistency" (simpler, requires different metric)
- Decision: OPTION A preferred for scientific integrity

### P2: n=5 stochastic eval
- Current: std=0.000 (deterministic model + fixed data)
- OPTION A: train 5 models with different seeds → true n=5
- OPTION B: subsample episodes per seed → pseudo-variance
- Decision: OPTION A for proper CI

### P3: STEP 10 → P4 gate decision
- After ABL-001/003 retrain: verdict upgrade AT_RISK → ALIVE_READY
- If ABL collapse confirmed: proceed to P4 (synthetic GUI MVE)
- If ABL doesn't collapse as expected: CLAIM_REDESIGN_READY path

---

## 3. P4 Readiness Check (pending ABL retrain)

| Gate | Condition | Status |
|---|---|---|
| C3 PRELIMINARY_PLUS | f1 > 0 in n=5 | ✓ 0.539/0.587 |
| C6 ppc advantage | 2× vs ABL-036 | ✓ 14.9× |
| ABL-040 discriminability | recall=1.0 | ✓ |
| ABL-001/003 collapse | retrain needed | PENDING |
| No hidden leakage | leakage=0 | ✓ |
| Tests green | 4 pre-existing fail (unchanged) | ✓ |

**P4 진입 권장**: ABL-001/003 retrain 후 collapse 확인 시 즉시 가능.

---

## 4. Paper Framing Update

Based on STEP 9 evidence:
- **C3 claim**: "FRCG-WM uniquely detects wrong control-grammar with F1=0.539/0.587" — allowed
- **C6 claim**: "Falsification gate achieves 14.9× progress-per-compute vs no-gate" — allowed
- **C2 claim**: DEFERRED pending v0_5 dataset
- **task_success claim**: FORBIDDEN (dataset-invariant in offline eval)

---

## 5. Phase Gate Sentinel

Target: `outputs/phase_gates/P3_STEP9_C3_RECOVERY.passed`
Condition: C3 f1 > 0 on test_id AND test_ood (n=5 any seed) + Gate O-DTB PASS + Gate O-39/40 PASS
Status: **READY TO CREATE**
