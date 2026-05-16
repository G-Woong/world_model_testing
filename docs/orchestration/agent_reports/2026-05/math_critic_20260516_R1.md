# Mathematical Validity Critic Report
**Agent**: mathematical-validity-critic (deep)
**Date**: 2026-05-16
**Session**: War Room R1

## Overall Verdict: NEEDS_REVISION

All 6 claims CONDITIONAL. No claim VALID.

### Critical Blocking Issues (3)

1. **CRITICAL — C2 identifiability**: regime/grammar 분리 불가 (Locatello impossibility). grammar.py:14-23에서 ControlGrammar Enum과 regime이 1:1 대응 위험. Crossed split 생성 코드 없음.
   - File evidence: `paper_context_ref/07_LATENT_ARCHITECTURE_DESIGN.md:370-371` (COLLAPSE-07-001), `:77` (Locatello 1811.12359)

2. **HIGH — C3 theory-implementation gap**: 이론은 likelihood ratio (`F_t = max_alt[ell(h_alt)-ell(h_exec)]`), 구현은 BCE binary classifier (`L_falsification = BCE(falsification_score, true_wrong_hypothesis)`). 이론과 loss 형식 불일치.
   - File evidence: `paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md:172`, `paper_context_ref/08_LOSS_REWARD_TRAINING_OBJECTIVE.md:208`

3. **HIGH — C6 threshold arbitrariness**: G_t 4개 threshold (τ_f, τ_v, τ_a + C_plan) calibration 방법 미명시. VOC theory와 formal 연결 없음.
   - File evidence: `paper_context_ref/09_PLANNING_THEORY_ALGORITHM.md:203`

---

## Claim-by-Claim Results

### C1 — CONDITIONAL (WCGP metric is oracle-dependent)
```
CLAIM: C1
RISK: HIGH
EVIDENCE:
  - 02:272 (WCGP Episode 10 conditions)
  - 02:369-370 (CLAIM-02-001: CONDITIONAL_SURVIVAL)
  - grammar.py:201-222 (is_wrong_grammar_failure — oracle hidden_state_flags 의존)
RECOMMENDATION:
  WCGP metric을 두 계층으로 분리:
  (a) oracle_wrong_grammar_label() — hidden-only, training/eval only
  (b) inferred_wrong_grammar_proxy() — inference-safe, h_exec_confidence + evidence_mismatch만 사용
ACTIONABLE_CODE_DIRECTION:
  grammar.py:201-222 분리. oracle version vs inference-safe proxy
VERDICT: CONDITIONAL
UNKNOWN_ITEMS: WCGP real benchmark proxy 미결정; C3 순환 의존
```

### C2 — CONDITIONAL (identifiability CRITICAL)
```
CLAIM: C2
RISK: CRITICAL
EVIDENCE:
  - 07:370-371 (COLLAPSE-07-001)
  - 07:77 (Locatello impossibility)
  - 07:142 (z_regime: PRIMARY_LATENT_CONTESTED)
  - grammar.py:14-23 (ControlGrammar → potential 1:1 regime-grammar mapping)
RECOMMENDATION:
  1. generate_same_regime_diff_grammar_episodes() 구현 필수
  2. generate_same_grammar_diff_regime_episodes() 구현 필수
  3. ABL-003 (merged regime-grammar) ablation에서 MI probe 측정
ACTIONABLE_CODE_DIRECTION:
  text_env generator에 crossed split 생성 함수 추가 (현재 없음)
VERDICT: CONDITIONAL
UNKNOWN_ITEMS: 8개 grammar Enum 중 same-regime/diff-grammar case 몇 개인지 미분석
```

### C3 — CONDITIONAL (theory-implementation gap)
```
CLAIM: C3
RISK: HIGH
EVIDENCE:
  - 09:170-184 (F_t = max_alt[ell(h_alt)-ell(h_exec)] definition)
  - 08:208 (L_falsification = BCE(falsification_score, true_wrong_hypothesis))
  - 08:384-387 (MVE pseudo-code: BCE on binary label)
RECOMMENDATION:
  방안 A (권장): "learned binary classifier as LR approximation"으로 claim 재서술
  방안 B: energy-based contrastive objective로 변경
  어떤 방안이든 FALS-01(threshold) vs FALS-02(LR) vs FALS-03(binary) 비교실험 필요
ACTIONABLE_CODE_DIRECTION:
  BinaryFalsificationScorer (BCE, 현재) + LikelihoodRatioFalsificationScorer 두 버전 구현
VERDICT: CONDITIONAL
UNKNOWN_ITEMS: BCE-trained score가 true LR의 sufficient statistic인지 UNKNOWN
```

### C4 — CONDITIONAL (rollout horizon + counterfactual supervision)
```
CLAIM: C4
RISK: HIGH
EVIDENCE:
  - 09:186-197 (V(a,h) definition)
  - 07:535 (ARCH-UNKNOWN-005: rollout horizon adequacy UNKNOWN)
  - 08:240 (L_counterfactual_rollout: synthetic-only label dependency)
  - grammar.py:160-177 (apply() — action effect is grammar-conditioned ✓)
RECOMMENDATION:
  H=3 rollout variance analysis 필요. Real benchmark limitation 명시.
ACTIONABLE_CODE_DIRECTION:
  WM_θ conditioning test: same action, different grammar → different predicted effect (smoke test)
VERDICT: CONDITIONAL
UNKNOWN_ITEMS: H=3 sufficiency UNKNOWN; estimation noise vs signal ratio UNKNOWN
```

### C5 — CONDITIONAL (best claim mathematically)
```
CLAIM: C5
RISK: MED
EVIDENCE:
  - 09:218-232 (Rewrite(i_t, a_base, h*) formula — mathematically clear)
  - 08:209 (L-MAIN-006)
  - grammar.py:185-199 (label_recovery_action — oracle version)
RECOMMENDATION:
  Oracle version vs learned version 분리 (already has clear separation point).
  L-AUX-018 (macro validity loss) 필수/보조 여부 확정 필요.
VERDICT: CONDITIONAL (best claim; practical issues, not mathematical)
UNKNOWN_ITEMS: oracle label → real benchmark proxy 미결정
```

### C6 — CONDITIONAL (VOC claim overstated)
```
CLAIM: C6
RISK: HIGH
EVIDENCE:
  - 09:199-211 (G_t = I[F_t>τ_f ∧ ΔV_t>τ_v ∧ P_switch>τ_a ∧ ΔV_t-C_plan>0])
  - 08:261 (C_plan = β * rollout_steps, informal)
RECOMMENDATION:
  1. 4개 threshold factorial ablation (G_falsification-only, G_uncertainty-only, etc.)
  2. C_plan formal definition (rollout_steps * cost_per_step_proxy)
  3. "VOC-inspired"로 tone down (not exact VOC)
VERDICT: CONDITIONAL
UNKNOWN_ITEMS: τ calibration UNKNOWN; G_t ↔ VOC formal connection UNKNOWN
```

---

## Worst/Best Claim

- **Worst: C2** — Locatello impossibility. architecture-level falsification risk.
- **Best: C5** — Rewrite formula is mathematically clearest. WAC distinction at formula level.
