# novelty-threat-scout Report: STEP 8 WAC/CUWM/WebWorld 2025-2026 Threat Scan

**report_id**: novelty_step8_threat_R1
**date**: 2026-05-18
**trigger**: T1/T5/T6
**verdict**: NOVELTY_AT_RISK (not COMPROMISED)

---

## Summary

All four direct threats (WebWorld, WAC, CUWM, VeriGUI) remain CONFIRMED_PRIMARY with defensible distinguishing factors. No paper found that implements control-grammar falsification-guided planning with persistence metrics. However, two new threats require action.

## Direct Threat Status

| Threat | Status | Novelty Risk | Defense Strength |
|---|---|---|---|
| WebWorld (2602.14721) | CONFIRMED_PRIMARY | MEDIUM | STRONG |
| WAC (2602.15384) | CONFIRMED_PRIMARY | MEDIUM | MODERATE |
| CUWM (2602.17365) | CONFIRMED_PRIMARY | MEDIUM | STRONG |
| VeriGUI (2604.05477) | CONFIRMED_PRIMARY | HIGH (existing) | MODERATE |

## New 2025/2026 Threats

| Paper | arXiv | Threat Level | Key Risk |
|---|---|---|---|
| StressWeb | 2604.16385 (Mar 2026) | **HIGH** | Documents implicit grammar shift (Remap): agents repeat wrong action up to 92× |
| WebUncertainty | 2604.17821 (Apr 2026) | MED | Concrete uncertainty-MCTS web agent — "your gate is uncertainty thresholding" now has a citation |
| BacktrackAgent | 2505.20660 (EMNLP 2025) | MED | Venue-published verifier+judger+reflector; reinforces verification baseline cluster |
| AgentProg | 2512.10371 (Dec 2025) | MED | Belief-Reality Gap detection — similar conceptually to evidence-to-hypothesis-update |
| gWorld | 2602.01576 (Feb 2026) | LOW | New visual+code GUI WM; not in existing threat map |
| VeriWeb | 2508.04026 | LOW | NOT a VeriGUI extension — name confusion resolved |

Status upgrades (PARTIALLY_CONFIRMED → CONFIRMED_PRIMARY): ViMo, MobileDreamer, Code2World, AgentRx.

## Reviewer-2 Attack Scenarios (New)

| ATK | Source | Attack | Defense |
|---|---|---|---|
| ATK-NEW-001 | StressWeb | "Your phenomenon is already documented by StressWeb" | StressWeb measures symptom; FRCG-WM provides the mechanism (falsification posterior) |
| ATK-NEW-002 | StressWeb | "Action semantic remap = your grammar shift — it's just a benchmark perturbation" | Grammar shift is model-internal latent. FRCG-WM models persistence time as a first-class metric. StressWeb doesn't model agent hypothesis at all. |
| ATK-NEW-003 | AgentProg | "AgentProg Belief-Reality Gap detection already does hypothesis update" | AgentProg is program-state level. FRCG-WM is grammar-hypothesis level (intent-to-action schema). |
| ATK-NEW-004 | WebUncertainty | "Your compute gate is less principled than ConActU uncertainty-MCTS" | WebUncertainty: "how confident am I?". FRCG-WM: "does evidence force grammar hypothesis rejection?" Different signals. |
| ATK-NEW-005 | BacktrackAgent + VeriGUI | "Two venue papers (EMNLP + arXiv) already show error-recovery in GUI agents" | Both detect action-level failure. FRCG-WM targets grammar-level hypothesis replacement — not detectable by action verifiers alone. |

## Actions Required (STEP 9, paper_context_ref FORBIDDEN in STEP 8)

Defer to STEP 9:
1. Update `01_RELATED_WORK_THREAT_MAP.md`: add StressWeb (CITE-019), BacktrackAgent (CITE-020), WebUncertainty (CITE-021), gWorld (CITE-022), AgentProg (CITE-023); upgrade ViMo/MobileDreamer/Code2World/AgentRx to CONFIRMED_PRIMARY
2. Add StressWeb to `02_PROBLEM_NOVELTY_FALSIFICATION.md` as primary motivation evidence
3. STEP 10 eval plan must include WebUncertainty (2604.17821) as uncertainty-gate baseline
4. BASE-026/027 documentation must cite StressWeb as motivation for why WAC/CUWM-style correction is insufficient

## Citation Cross-Check (≥2 sources verified)
All papers above verified via arXiv primary + second source (HuggingFace papers / ACL Anthology / OpenReview). See full report for URL list.
