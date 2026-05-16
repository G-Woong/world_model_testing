# Novelty Threat Scout Report
**Agent**: novelty-threat-scout (deep, WebSearch + 2-source cross-check)
**Date**: 2026-05-16
**Session**: War Room R1
**Searches**: 20+ WebSearch + 4 WebFetch cross-verifications

## OVERALL_NOVELTY_VERDICT: B (REFRAME_NEEDED)

Generic WM / action correction / frozen search / verification 모두 2026년 상반기에 직접 선점됨.
생존 novelty = (a) wrong-grammar persistence as measurable failure mode, (b) likelihood ratio falsification (≠ verification), (c) grammar-conditioned alternative hypothesis rollout, (d) grammar-conditioned intent-to-action rewrite.

---

## Direct Threats (4개) — All CRITICAL, All 2-Source Confirmed

| Paper | arXiv | Threat | Verdict |
|---|---|---|---|
| WebWorld | 2602.14721 | Generic web WM 완전 선점 | OVERLAP_MANAGEABLE (grammar falsification으로 축소 가능) |
| WAC | 2602.15384 | Action correction + consequence simulation | OVERLAP_MANAGEABLE (grammar-conditioned vs generic) |
| CUWM | 2602.17365 | Frozen base + WM test-time search | OVERLAP_MANAGEABLE (control variable로 격하) |
| VeriGUI (Don't Act Blindly) | 2604.05477 | Action-effect verification + failure recovery | OVERLAP_MANAGEABLE (binary verify vs posterior LR) |

**VeriGUI (2604.05477) distinction:**
- VeriGUI: action → verify → [fail] → corrective reasoning → new action
- FRCG-WM: action → evidence → F_t = max_alt[ell(h_alt)-ell(h_exec)] → [grammar posterior falls] → alternative grammar selection → rollout → rewrite

VeriGUI는 verification layer에서 종료. FRCG-WM은 posterior update + alternative grammar adoption + grammar-conditioned rewrite까지 진행.

---

## New Threats (3+ 발견, not in existing threat map)

### CATTS (2602.12276) — **#2 most dangerous**
- Uncertainty-based compute gate (vote entropy + top-1/top-2 margin) → 동적 compute allocate
- +9.1% WebArena-Lite, 2.3x fewer tokens than uniform scaling
- **위협**: FRCG-WM C6 "decision-relevant compute gate" novelty를 직접 약화
- Defense: grammar hypothesis switch value ≠ prediction uncertainty (compute-matched experiment 필요)

### VLAA-GUI (2604.21375) — **#1 (compound with VeriGUI)**
- Loop Breaker: rule-based (repeat count + screen hash) → interaction mode switch + search
- Nearly halves wasted steps; 77.5% on OSWorld
- **위협**: FRCG-WM의 failure loop reduction + mode switch와 phenomenologically 유사
- Defense: heuristic rule-based vs posterior-based falsification (P/R comparison)

### WebUncertainty (2604.17821) — MED
- Dual-level uncertainty (aleatoric + epistemic) + MCTS reasoning
- **위협**: uncertainty vs falsification gate 구분 claim 약화
- Defense: high-confidence-wrong-grammar case에서 uncertainty gate ≠ falsification gate

### StressWeb (2604.16385) — HIGH (existing P-013, now CONFIRMED)
- Action semantic remap (RemapE/Remap): external perturbation
- **위협**: grammar shift as novel problem definition overlap
- Defense: external perturbation ≠ internal hypothesis persistence (명확)

---

## Top 3 Most Dangerous Threats

1. **VeriGUI (2604.05477) + VLAA-GUI (2604.21375) compound attack**
   - Detection (VeriGUI) + mode switch (VLAA-GUI) + search (WebWorld) = FRCG-WM?
   - Defense: verification success 후에도 wrong grammar hypothesis 유지하는 episode 실험 필요

2. **CATTS (2602.12276)**
   - Compute gate는 uncertainty gate로 설명 가능?
   - Defense: grammar-conditioned gate vs uncertainty gate, compute-matched comparison

3. **WebWorld + WAC + CUWM 3중 복합**
   - FRCG-WM = (WebWorld WM) + (WAC correction) + (CUWM frozen search)?
   - Defense: no-control-grammar ablation (ABL-002)이 반드시 이 모든 것을 무너뜨려야 함

---

## Action Items

1. `01_RELATED_WORK_THREAT_MAP.md`에 VLAA-GUI/CATTS/WebUncertainty 추가 필요 (Codex 금지 경로 — 별도 승인 필요)
2. `10_EVALUATION_BASELINE_ABLATION.md`에 CATTS-equivalent (BASE-uncertainty-entropy-gate), VLAA-GUI-equivalent (BASE-loop-heuristic) 추가 필요
3. VeriGUI baseline을 heuristic stub에서 real verifier로 교체 (ATTACK 3 방어)
4. CATTS compute-matched experiment 설계 (ATTACK 2 방어)

---

## Unknown Items

- POPPER (2502.09858): scientific falsification agent — mechanism overlap 확인 필요
- CI4A (2601.14790): component interface abstraction — action-interface schema overlap?
- CATTS vote margin vs grammar switch probability 상관 분석 필요
- VeriGUI 이름 충돌: 2604.05477 vs 2508.04026 (long-chain dataset)

## Citation Registry (All 2-source confirmed)

| Paper | arXiv | Source 1 | Source 2 |
|---|---|---|---|
| WebWorld | 2602.14721 | arxiv.org | huggingface.co/Qwen/WebWorld-8B |
| WAC | 2602.15384 | arxiv.org/abs | arxiv.org/html |
| CUWM | 2602.17365 | arxiv.org | huggingface.co/papers |
| VeriGUI | 2604.05477 | arxiv.org/abs | arxiv.org/html |
| VLAA-GUI | 2604.21375 | arxiv.org | huggingface.co/papers |
| CATTS | 2602.12276 | arxiv.org | alanhou.org blog |
| WebUncertainty | 2604.17821 | arxiv.org/html | arxiv.org/abs |
| StressWeb | 2604.16385 | arxiv.org/abs | arxiv.org/html |
